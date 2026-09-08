import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { PGlite } from "@electric-sql/pglite";

const uuid = n => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const [orgA, orgB, adminA, viewerA, adminB, outsider, envA, envB, envOther, camA, camB, alertA, ruleA] = Array.from({ length: 13 }, (_, i) => uuid(i + 1));

test("real PostgreSQL migration, RLS, grants and report contracts (offline)", async t => {
  const db = new PGlite();
  try {
    await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
      create schema auth; create table auth.users(id uuid primary key);
      create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true),'')::uuid $$;
      grant usage on schema public,auth to anon,authenticated,service_role;
      grant execute on function auth.uid() to anon,authenticated,service_role;`);
    await db.exec(await readFile(new URL("../../supabase/migrations/202609060001_smart_environment.sql", import.meta.url), "utf8"));
    await db.exec(`insert into auth.users values ('${adminA}'),('${viewerA}'),('${adminB}'),('${outsider}');
      insert into organizations(id,name) values('${orgA}','Empresa A'),('${orgB}','Empresa B');
      insert into organization_members values('${orgA}','${adminA}','admin'),('${orgA}','${viewerA}','viewer'),('${orgB}','${adminB}','admin');
      insert into environments(id,organization_id,name) values('${envA}','${orgA}','Sala A'),('${envB}','${orgB}','Sala B'),('${envOther}','${orgA}','Sala secundária');
      insert into cameras(id,organization_id,environment_id,name,source,address) values('${camA}','${orgA}','${envA}','Cam A','webcam','0'),('${camB}','${orgB}','${envB}','Cam B','rtsp','rtsp://192.168.1.10/live');
      insert into alert_rules(id,organization_id,environment_id,name,kind) values('${ruleA}','${orgA}','${envA}','Offline','camera_offline');
      insert into alerts(id,organization_id,environment_id,camera_id,rule_id,title,occurred_at,dedup_key) values('${alertA}','${orgA}','${envA}','${camA}','${ruleA}','Offline','2026-09-06T10:00:00Z','offline-a');`);
    const as = async (user, fn, role = "authenticated") => {
      await db.exec(`set role ${role}`);
      await db.query("select set_config('request.jwt.claim.sub',$1,false)", [user ?? ""]);
      try { return await fn(); } finally { await db.exec("reset role"); await db.query("select set_config('request.jwt.claim.sub','',false)"); }
    };
    const denied = async (fn, code = "42501") => assert.rejects(fn, error => error.code === code);
    const sample = (env, camera, minute, state = "occupied", count = 2, org = orgA) => db.query("insert into occupancy_samples(organization_id,environment_id,camera_id,bucket_start,state,people_count,model_version) values($1,$2,$3,$4,$5,$6,'fixture')", [org, env, camera, minute, state, count]);
    const report = (org = orgA, start = "2026-09-06T10:00:00Z", end = "2026-09-06T10:03:00Z", env = null) => db.query("select * from occupancy_report($1,$2,$3,$4)", [org, start, end, env]);

    await t.test("anonymous has no tables; nonmember gets no rows; admin/viewer see only their tenant", async () => {
      await as(null, () => denied(() => db.query("select * from cameras")), "anon");
      await as(outsider, async () => assert.equal((await db.query("select * from cameras")).rows.length, 0));
      for (const user of [adminA, viewerA]) await as(user, async () => {
        assert.equal((await db.query("select current_user")).rows[0].current_user, "authenticated");
        assert.deepEqual((await db.query("select id from cameras")).rows.map(row => row.id), [camA]);
        assert.equal((await db.query("select * from cameras where id=$1", [camB])).rows.length, 0);
        assert.equal((await db.query("select * from organization_members")).rows.length, 1);
      });
      await as(adminB, async () => assert.deepEqual((await db.query("select id from cameras")).rows.map(row => row.id), [camB]));
    });
    await t.test("admin can create/edit; viewer cannot; stale update changes no row", async () => {
      await as(adminA, async () => {
        const inserted = await db.query("insert into environments(organization_id,name) values($1,'Novo') returning *", [orgA]);
        const id = inserted.rows[0].id;
        const update = await db.query("update environments set name='Renomeado' where id=$1 and version=1 returning version", [id]);
        assert.equal(update.rows[0].version, 2);
        assert.equal((await db.query("update environments set name='Antigo' where id=$1 and version=1 returning *", [id])).rows.length, 0);
        await denied(() => db.query("insert into environments(organization_id,name) values($1,'Invasão')", [orgB]));
        await denied(() => db.query("update environments set organization_id=$1 where id=$2", [orgB, id]));
        await denied(() => db.query("insert into environments(organization_id,name) values($1,'  renomeado  ')", [orgA]), "23505");
      });
      await as(viewerA, async () => {
        await denied(() => db.query("insert into environments(organization_id,name) values($1,'Viewer')", [orgA]));
        assert.equal((await db.query("update environments set name='Viewer' where id=$1 returning *", [envA])).rows.length, 0);
        assert.equal((await db.query("select * from audit_events")).rows.length, 0);
      });
    });
    await t.test("membership elevation, fabricated telemetry and audit writes are denied", async () => {
      await as(adminA, async () => {
        await denied(() => db.query("insert into organization_members values($1,$2,'admin')", [orgA, outsider]));
        await denied(() => db.query("update organization_members set role='admin'"));
        await denied(() => sample(envA, camA, "2026-09-06T10:00:00Z"));
        await denied(() => db.query("update alerts set status='resolved' where id=$1", [alertA]));
        await denied(() => db.query("delete from cameras where id=$1", [camA]));
        await denied(() => db.query("delete from audit_events"));
      });
    });
    await t.test("foreign keys and ingestion reject cross-tenant and wrong-room assignments", async () => {
      await as(adminA, () => denied(() => db.query("insert into cameras(organization_id,environment_id,name,source,address) values($1,$2,'Cross','webcam','0')", [orgA, envB]), "23503"));
      await as(null, async () => {
        await denied(() => sample(envA, camB, "2026-09-06T10:00:00Z"), "23503");
        await denied(() => sample(envOther, camA, "2026-09-06T10:00:00Z"), "23503");
        await denied(() => db.query("insert into alerts(organization_id,environment_id,rule_id,title,occurred_at,dedup_key) values($1,$2,$3,'Wrong',now(),'wrong-rule')", [orgA, envOther, ruleA]), "23503");
        await denied(() => sample(envA, camA, "2026-09-06T10:00:00Z", "occupied", null), "23514");
        await denied(() => sample(envA, camA, "2026-09-06T10:00:00Z", "empty", null), "23514");
        await denied(() => sample(envA, camA, "2026-09-06T10:00:01Z"), "23514");
      }, "service_role");
    });
    await t.test("reports use unique full minutes, exclude unknown from empty, and enforce RLS", async () => {
      await as(null, async () => {
        await sample(envA, camA, "2026-09-06T10:00:00Z");
        await sample(envA, camA, "2026-09-06T10:01:00Z", "empty", 0);
        await sample(envA, camA, "2026-09-06T10:02:00Z", "unknown", null);
        await sample(envB, camB, "2026-09-06T10:00:00Z", "occupied", 9, orgB);
        await denied(() => sample(envA, camA, "2026-09-06T10:00:00Z"), "23505");
      }, "service_role");
      await as(viewerA, async () => {
        const row = (await report()).rows[0];
        assert.equal(Number(row.observed_minutes), 3); assert.equal(Number(row.occupied_minutes), 1);
        assert.equal(Number(row.empty_minutes), 1); assert.equal(Number(row.unknown_minutes), 1); assert.equal(row.peak_people, 2);
        assert.equal((await report(orgB)).rows.length, 0);
        assert.equal((await report(orgA, "2026-09-06T10:00:00Z", "2026-09-06T10:00:30Z")).rows.length, 0);
        assert.equal((await report(orgA, "2026-09-06T10:00:00Z", "2026-09-06T10:03:00Z", envOther)).rows.length, 0);
        await denied(() => report(orgA, null), "22023");
        await denied(() => report(orgA, "2026-07-01T00:00:00Z"), "22023");
      });
    });
    await t.test("alert review requires admin and non-null current version; resolution retains review", async () => {
      const review = (version, state) => db.query("select * from review_alert($1,$2,$3)", [alertA, version, state]);
      for (const user of [viewerA, adminB, outsider]) await as(user, () => denied(() => review(1, "reviewed")));
      await as(adminA, async () => {
        await denied(() => review(null, "reviewed"), "40001");
        await denied(() => review(1, null), "22023");
        await denied(() => review(1, "resolved"), "22023");
        const reviewed = (await review(1, "reviewed")).rows[0];
        assert.equal(reviewed.reviewed_by, adminA); assert.equal(reviewed.version, 2);
        await denied(() => review(1, "resolved"), "40001");
        const resolved = (await review(2, "resolved")).rows[0];
        assert.equal(resolved.reviewed_by, reviewed.reviewed_by);
        assert.equal(String(resolved.reviewed_at), String(reviewed.reviewed_at));
        assert.equal(resolved.resolved_by, adminA); assert.equal(resolved.version, 3);
        await denied(() => review(3, "reviewed"), "22023");
        assert.deepEqual((await db.query("select action from audit_events where entity_id=$1 order by id", [alertA])).rows.map(row => row.action), ["insert", "alert_reviewed", "alert_resolved"]);
      });
    });
    await t.test("moving a camera preserves historical assignment and revocation blocks next read", async () => {
      await as(adminA, () => db.query("update cameras set environment_id=$1 where id=$2", [envOther, camA]));
      await as(viewerA, async () => assert.equal((await report()).rows[0].environment_id, envA));
      await db.query("delete from organization_members where user_id=$1", [viewerA]);
      await as(viewerA, async () => { assert.equal((await report()).rows.length, 0); assert.equal((await db.query("select * from cameras")).rows.length, 0); });
    });
  } finally { await db.close(); }
});
