begin;

create schema if not exists se_private;
revoke all on schema se_private from public, anon, authenticated;
grant usage on schema se_private to authenticated;

create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null check (length(btrim(name)) between 1 and 80),
  timezone text not null default 'America/Sao_Paulo' check (timezone = 'America/Sao_Paulo')
);
create table public.organization_members (
  organization_id uuid not null references public.organizations(id),
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('admin','viewer')),
  primary key (organization_id, user_id)
);
create function se_private.has_role(org uuid, admin_only boolean default false)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.organization_members m where m.organization_id = org
    and m.user_id = (select auth.uid()) and (not admin_only or m.role = 'admin'));
$$;
revoke all on function se_private.has_role(uuid, boolean) from public, anon;
grant execute on function se_private.has_role(uuid, boolean) to authenticated;

create table public.environments (
  id uuid primary key default gen_random_uuid(), organization_id uuid not null references public.organizations(id),
  name text not null check (length(btrim(name)) between 1 and 80),
  version integer not null default 1, created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  unique (organization_id,id)
);
create unique index environment_name_unique on public.environments (organization_id, lower(regexp_replace(btrim(name), '\s+', ' ', 'g')));
create table public.cameras (
  id uuid primary key default gen_random_uuid(), organization_id uuid not null references public.organizations(id),
  environment_id uuid not null, name text not null check (length(btrim(name)) between 1 and 80),
  source text not null check (source in ('webcam','mjpeg','rtsp')),
  address text not null check (length(address) between 1 and 500 and address !~ '[[:cntrl:]@?#]'),
  monitor_id text check (monitor_id ~ '^[a-zA-Z0-9_-]{1,64}$'),
  enabled boolean not null default true, version integer not null default 1,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  foreign key (organization_id,environment_id) references public.environments(organization_id,id),
  unique (organization_id,id), unique (organization_id,monitor_id),
  check ((source = 'webcam' and address ~ '^[0-9]{1,2}$') or
    (source = 'mjpeg' and address ~ '^https?://[^/[:space:]]+(/[^[:space:]]*)?$') or
    (source = 'rtsp' and address ~ '^rtsp://[^/[:space:]]+(/[^[:space:]]*)?$'))
);
create table public.alert_rules (
  id uuid primary key default gen_random_uuid(), organization_id uuid not null references public.organizations(id),
  environment_id uuid not null, name text not null check (length(btrim(name)) between 1 and 80),
  kind text not null check (kind in ('camera_offline','occupied_outside_hours')),
  enabled boolean not null default true,
  start_time time not null default '08:00', end_time time not null default '18:00',
  delay_seconds integer not null default 60 check (delay_seconds between 10 and 3600),
  version integer not null default 1, created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  foreign key (organization_id,environment_id) references public.environments(organization_id,id),
  unique (organization_id,id), check (start_time <> end_time)
);
-- Fixed UTC minute buckets: one record per camera/minute, no overlapping windows.
create table public.occupancy_samples (
  id uuid primary key default gen_random_uuid(), organization_id uuid not null references public.organizations(id),
  environment_id uuid not null, camera_id uuid not null, bucket_start timestamptz not null,
  state text not null check (state in ('occupied','empty','unknown')),
  people_count integer check (people_count between 0 and 10000),
  model_version text not null check (length(model_version) between 1 and 100),
  created_at timestamptz not null default now(),
  foreign key (organization_id,environment_id) references public.environments(organization_id,id),
  foreign key (organization_id,camera_id) references public.cameras(organization_id,id),
  unique (camera_id,bucket_start),
  check (extract(second from bucket_start) = 0),
  check ((state = 'unknown' and people_count is null) or (state = 'empty' and people_count is not null and people_count = 0) or (state = 'occupied' and people_count is not null and people_count > 0))
);
create index samples_period on public.occupancy_samples(organization_id,bucket_start,camera_id);
create table public.alerts (
  id uuid primary key default gen_random_uuid(), organization_id uuid not null references public.organizations(id),
  environment_id uuid not null, camera_id uuid, rule_id uuid,
  title text not null check (length(title) between 1 and 160),
  detail text not null default '' check (length(detail) <= 2000),
  occurred_at timestamptz not null, status text not null default 'open' check (status in ('open','reviewed','resolved')),
  dedup_key text not null check (length(dedup_key) between 1 and 160),
  reviewed_by uuid references auth.users(id), reviewed_at timestamptz,
  resolved_by uuid references auth.users(id), resolved_at timestamptz,
  version integer not null default 1, created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  foreign key (organization_id,environment_id) references public.environments(organization_id,id),
  foreign key (organization_id,camera_id) references public.cameras(organization_id,id),
  foreign key (organization_id,rule_id) references public.alert_rules(organization_id,id),
  unique (organization_id,dedup_key),
  check ((status = 'open' and reviewed_by is null and reviewed_at is null and resolved_by is null and resolved_at is null)
    or (status = 'reviewed' and reviewed_by is not null and reviewed_at is not null and resolved_by is null and resolved_at is null)
    or (status = 'resolved' and reviewed_by is not null and reviewed_at is not null and resolved_by is not null and resolved_at is not null))
);
create index alerts_period on public.alerts(organization_id,occurred_at desc,id);
create table public.audit_events (
  id bigint generated always as identity primary key,
  organization_id uuid not null references public.organizations(id), actor_id uuid,
  entity_type text not null, entity_id uuid not null, action text not null,
  occurred_at timestamptz not null default now()
);

create function se_private.touch_record() returns trigger language plpgsql set search_path = '' as $$
begin
  if new.id <> old.id or new.organization_id <> old.organization_id then raise exception 'immutable identity'; end if;
  new.version := old.version + 1; new.created_at := old.created_at; new.updated_at := now();
  return new;
end $$;
create function se_private.audit_change() returns trigger language plpgsql security definer set search_path = '' as $$
declare action_name text := lower(tg_op);
begin
  if tg_table_name = 'alerts' and tg_op = 'UPDATE' then
    action_name := 'alert_' || new.status;
  end if;
  insert into public.audit_events(organization_id,actor_id,entity_type,entity_id,action)
  values (new.organization_id,auth.uid(),tg_table_name,new.id,action_name);
  return new;
end $$;
revoke all on function se_private.touch_record(), se_private.audit_change() from public, anon, authenticated;

-- Validate the current assignment at ingestion, while retaining historical environments
-- if a camera is subsequently moved. Row locks serialize moves against ingestion.
create function se_private.check_assignment() returns trigger language plpgsql set search_path = '' as $$
declare assigned uuid;
begin
  if new.camera_id is not null then
    select environment_id into assigned from public.cameras
      where id = new.camera_id and organization_id = new.organization_id for share;
    if assigned is distinct from new.environment_id then raise exception 'invalid camera assignment' using errcode='23503'; end if;
  end if;
  if tg_table_name = 'alerts' then
    if new.rule_id is not null then
      select environment_id into assigned from public.alert_rules
        where id = new.rule_id and organization_id = new.organization_id for share;
      if assigned is distinct from new.environment_id then raise exception 'invalid rule assignment' using errcode='23503'; end if;
    end if;
  end if;
  return new;
end $$;
revoke all on function se_private.check_assignment() from public, anon, authenticated;
create trigger assignment before insert on public.occupancy_samples for each row execute function se_private.check_assignment();
create trigger assignment before insert on public.alerts for each row execute function se_private.check_assignment();

alter table public.organizations enable row level security;
alter table public.organization_members enable row level security;
create policy organization_read on public.organizations for select to authenticated using (se_private.has_role(id));
create policy membership_read on public.organization_members for select to authenticated using (user_id = (select auth.uid()));

do $$ declare t text; begin
  foreach t in array array['environments','cameras','alert_rules','occupancy_samples','alerts'] loop
    execute format('alter table public.%I enable row level security',t);
    execute format('create policy scoped_read on public.%I for select to authenticated using (se_private.has_role(organization_id))',t);
  end loop;
  foreach t in array array['environments','cameras','alert_rules'] loop
    execute format('create policy admin_insert on public.%I for insert to authenticated with check (se_private.has_role(organization_id,true))',t);
    execute format('create policy admin_update on public.%I for update to authenticated using (se_private.has_role(organization_id,true)) with check (se_private.has_role(organization_id,true))',t);
  end loop;
  foreach t in array array['environments','cameras','alert_rules','alerts'] loop
    execute format('create trigger touch before update on public.%I for each row execute function se_private.touch_record()',t);
    execute format('create trigger audit after insert or update on public.%I for each row execute function se_private.audit_change()',t);
  end loop;
end $$;
alter table public.audit_events enable row level security;
create policy admin_read on public.audit_events for select to authenticated using (se_private.has_role(organization_id,true));

-- Revoke Supabase default grants explicitly; membership/admin are provisioned outside the browser.
revoke all on public.organizations, public.organization_members, public.environments, public.cameras,
 public.alert_rules, public.occupancy_samples, public.alerts, public.audit_events from anon, authenticated;
grant select on public.organizations, public.organization_members, public.environments, public.cameras,
 public.alert_rules, public.occupancy_samples, public.alerts, public.audit_events to authenticated;
grant insert(organization_id,name) on public.environments to authenticated;
grant insert(organization_id,environment_id,name,source,address,monitor_id,enabled) on public.cameras to authenticated;
grant insert(organization_id,environment_id,name,kind,enabled,start_time,end_time,delay_seconds) on public.alert_rules to authenticated;
grant update(name) on public.environments to authenticated;
grant update(name,environment_id,source,address,monitor_id,enabled) on public.cameras to authenticated;
grant update(name,environment_id,kind,enabled,start_time,end_time,delay_seconds) on public.alert_rules to authenticated;
grant all on public.organizations, public.organization_members, public.environments, public.cameras,
 public.alert_rules, public.occupancy_samples, public.alerts, public.audit_events to service_role;
grant usage, select on sequence public.audit_events_id_seq to service_role;

create function public.review_alert(alert_id uuid, expected_version integer, next_status text)
returns public.alerts language plpgsql security definer set search_path = '' as $$
declare a public.alerts;
begin
  select * into a from public.alerts where id = alert_id and se_private.has_role(organization_id,true) for update;
  if not found or not se_private.has_role(a.organization_id,true) then raise exception 'access denied' using errcode='42501'; end if;
  if expected_version is null or a.version is distinct from expected_version then raise exception 'record changed' using errcode='40001'; end if;
  if next_status is null or not ((a.status='open' and next_status='reviewed') or (a.status='reviewed' and next_status='resolved')) then raise exception 'invalid transition' using errcode='22023'; end if;
  if next_status = 'reviewed' then
    update public.alerts set status=next_status, reviewed_by=auth.uid(), reviewed_at=now() where id=a.id returning * into a;
  else
    update public.alerts set status=next_status, resolved_by=auth.uid(), resolved_at=now() where id=a.id returning * into a;
  end if;
  return a;
end $$;
revoke all on function public.review_alert(uuid,integer,text) from public, anon;
grant execute on function public.review_alert(uuid,integer,text) to authenticated;

-- SECURITY INVOKER: underlying RLS also filters reports. Group by camera, never sum overlapping cameras.
create function public.occupancy_report(org uuid, starts_at timestamptz, ends_at timestamptz, env uuid default null)
returns table(camera_id uuid, environment_id uuid, observed_minutes bigint, occupied_minutes bigint, empty_minutes bigint, unknown_minutes bigint, peak_people integer)
language plpgsql stable security invoker set search_path = '' as $$
begin
  if org is null or starts_at is null or ends_at is null or ends_at <= starts_at or ends_at-starts_at > interval '31 days' then raise exception 'invalid period' using errcode='22023'; end if;
  return query select s.camera_id,s.environment_id,count(*),count(*) filter(where s.state='occupied'),
    count(*) filter(where s.state='empty'),count(*) filter(where s.state='unknown'),max(s.people_count)
    from public.occupancy_samples s where s.organization_id=org and s.bucket_start >= starts_at
    and s.bucket_start + interval '1 minute' <= ends_at and (env is null or s.environment_id=env)
    group by s.camera_id,s.environment_id;
end $$;
revoke all on function public.occupancy_report(uuid,timestamptz,timestamptz,uuid) from public,anon;
grant execute on function public.occupancy_report(uuid,timestamptz,timestamptz,uuid) to authenticated;
commit;
