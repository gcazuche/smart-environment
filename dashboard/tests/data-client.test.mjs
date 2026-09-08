import assert from "node:assert/strict";
import test from "node:test";
import { createClient } from "@supabase/supabase-js";
import { DataRepository } from "../app/data-client.ts";
import { parseBackendConfig, dataError } from "../app/backend-config.ts";
import { periodBounds, csvText } from "../app/report-model.ts";

const org = "00000000-0000-4000-8000-000000000001";
const config = { url: "https://fixture.supabase.co", key: "sb_publishable_fixture", organizationId: org };
function setup(responder) {
  const calls = [];
  const client = createClient(config.url, config.key, { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false }, global: { fetch: async (input, init) => {
    const call = { url: new URL(String(input)), init, body: init?.body ? JSON.parse(init.body) : undefined }; calls.push(call);
    const response = responder(call);
    return new Response(JSON.stringify(response.data), { status: response.status ?? 200, headers: { "Content-Type": "application/json" } });
  } } });
  return { repository: new DataRepository(client, config), calls };
}
test("configuration is optional but partial, insecure and privileged keys fail closed", () => {
  assert.equal(parseBackendConfig({}), null);
  const values = { VITE_SUPABASE_URL: config.url, VITE_SUPABASE_PUBLISHABLE_KEY: config.key, VITE_ORGANIZATION_ID: org };
  assert.deepEqual(parseBackendConfig(values), config);
  for (const patch of [{ VITE_SUPABASE_URL: "http://remote.test" }, { VITE_SUPABASE_URL: "https://user:password@remote.test" }, { VITE_SUPABASE_URL: "https://remote.test?token=secret" }, { VITE_SUPABASE_PUBLISHABLE_KEY: "sb_secret_no" }, { VITE_SUPABASE_PUBLISHABLE_KEY: "eyJlegacyServiceRole" }, { VITE_ORGANIZATION_ID: "" }]) assert.throws(() => parseBackendConfig({ ...values, ...patch }));
  assert.throws(() => parseBackendConfig({ VITE_SUPABASE_URL: config.url }));
});
test("environment writes use persistent API, tenant and optimistic version filters", async () => {
  const { repository, calls } = setup(() => ({ data: { id: "env", organization_id: org, name: "Sala 1", version: 2 } }));
  const first = await repository.saveEnvironment(" Sala   1 ");
  assert.equal(first.name, "Sala 1"); assert.equal(calls[0].init.method, "POST");
  assert.deepEqual(calls[0].body, { name: "Sala 1", organization_id: org });
  await repository.saveEnvironment("Sala nova", first);
  assert.equal(calls[1].init.method, "PATCH");
  assert.equal(calls[1].url.searchParams.get("organization_id"), `eq.${org}`);
  assert.equal(calls[1].url.searchParams.get("version"), "eq.2");
  assert.equal(calls[1].url.searchParams.get("id"), "eq.env");
  assert.equal(calls[1].body.organization_id, undefined);
});
test("camera and rule writes preserve IDs and never contact the camera source", async () => {
  const { repository, calls } = setup(call => ({ data: { ...call.body, id: "saved", version: 1 } }));
  await repository.saveCamera({ name: "Camera", environment: "env", source: "rtsp", address: "rtsp://192.168.1.4/live" }, "pc", true);
  assert.equal(calls[0].url.hostname, "fixture.supabase.co");
  assert.equal(calls[0].body.environment_id, "env"); assert.equal(calls[0].body.monitor_id, "pc");
  const rule = { name: "Fora do horário", environment_id: "env", kind: "occupied_outside_hours", enabled: true, start_time: "08:00", end_time: "18:00", delay_seconds: 60 };
  await repository.saveRule(rule);
  assert.deepEqual(calls[1].body, { ...rule, organization_id: org });
  await assert.rejects(repository.saveCamera({ name: "Camera", environment: "env", source: "rtsp", address: "rtsp://user:secret@192.168.1.4/live" }, "pc", true));
  assert.equal(calls.length, 2);
});
test("catalog requires membership and reads all independent collections", async () => {
  const { repository, calls } = setup(call => ({ data: call.url.pathname.endsWith("organization_members") ? { role: "viewer" } : [] }));
  assert.deepEqual(await repository.catalog("user"), { role: "viewer", environments: [], cameras: [], rules: [] });
  assert.equal(calls.length, 4);
  for (const call of calls) { assert.equal(call.url.searchParams.get("organization_id"), `eq.${org}`); assert.notEqual(call.url.searchParams.get("select"), "*"); }
  const missing = setup(() => ({ data: null }));
  await assert.rejects(missing.repository.catalog("nonmember"), /vinculada/);
  assert.equal(missing.calls.length, 1);
});
test("history pagination filters full minute boundaries and reports preserve requested scope", async () => {
  const { repository, calls } = setup(() => ({ data: Array.from({ length: 51 }, (_, id) => ({ id })) }));
  const period = { start: "2026-09-06T03:00:00.000Z", end: "2026-09-06T12:00:30.000Z", environmentId: "room" };
  const result = await repository.samples(period, 1);
  assert.equal(result.rows.length, 50); assert.equal(result.more, true);
  assert.equal(calls[0].url.searchParams.get("offset"), "50"); assert.equal(calls[0].url.searchParams.get("limit"), "51");
  assert.deepEqual(calls[0].url.searchParams.getAll("bucket_start"), [`gte.${period.start}`, "lte.2026-09-06T11:59:30.000Z"]);
  assert.equal(calls[0].url.searchParams.get("environment_id"), "eq.room");
  await repository.report(period);
  assert.deepEqual(calls[1].body, { org, starts_at: period.start, ends_at: period.end, env: "room" });
  await repository.alerts(period);
  assert.doesNotMatch(calls[2].url.searchParams.get("select"), /dedup_key|reviewed_by/);
});
test("API errors stay redacted and stale review uses expected version", async () => {
  const fail = setup(() => ({ status: 409, data: { code: "23505", message: "sensitive schema/address" } }));
  await assert.rejects(fail.repository.saveEnvironment("Sala"), /Já existe/);
  assert.doesNotMatch(dataError({ code: "unknown", message: "secret" }).message, /secret/);
  const { repository, calls } = setup(() => ({ data: { id: "alert", version: 4 } }));
  await repository.reviewAlert({ id: "alert", version: 3 }, "reviewed");
  assert.deepEqual(calls[0].body, { alert_id: "alert", expected_version: 3, next_status: "reviewed" });
});
test("period bounds use Brasilia calendar midnight and handle year change", () => {
  const now = Date.parse("2026-09-06T02:30:00Z");
  assert.deepEqual(periodBounds("today", now), { start: "2026-09-05T03:00:00.000Z", end: "2026-09-06T02:30:00.000Z" });
  assert.equal(periodBounds("7d", Date.parse("2026-01-01T12:00:00Z")).start, "2025-12-26T03:00:00.000Z");
  assert.equal(periodBounds("30d", Date.parse("2026-09-06T12:00:00Z")).start, "2026-08-08T03:00:00.000Z");
});
test("CSV escapes formulas, quotes, nulls and multiline fields", () => {
  assert.equal(csvText([["=1+1", "  @cmd", 'Sala "A"', null, 0, "linha\n2", "\t=cmd"]]), '\uFEFF"\'=1+1";"\'  @cmd";"Sala ""A""";"";"0";"linha\n2";"\'\t=cmd"');
});
