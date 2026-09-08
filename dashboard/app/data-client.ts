import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { parseBackendConfig, dataError, type BackendConfig } from "./backend-config.ts";
import { validateCameraDraft, validateEnvironmentName, type CameraDraft } from "./dashboard-model.ts";

export type EnvironmentRecord = { id: string; organization_id: string; name: string; version: number };
export type CameraRecord = { id: string; organization_id: string; environment_id: string; name: string; source: CameraDraft["source"]; address: string; monitor_id: string | null; enabled: boolean; version: number };
export type RuleRecord = { id: string; organization_id: string; environment_id: string; name: string; kind: "camera_offline" | "occupied_outside_hours"; enabled: boolean; start_time: string; end_time: string; delay_seconds: number; version: number };
export type AlertRecord = { id: string; environment_id: string; camera_id: string | null; title: string; detail: string; status: "open" | "reviewed" | "resolved"; occurred_at: string; reviewed_at: string | null; version: number };
export type SampleRecord = { id: string; environment_id: string; camera_id: string; bucket_start: string; state: "occupied" | "empty" | "unknown"; people_count: number | null; model_version: string };
export type ReportRow = { camera_id: string; environment_id: string; observed_minutes: number; occupied_minutes: number; empty_minutes: number; unknown_minutes: number; peak_people: number | null };
export type Catalog = { environments: EnvironmentRecord[]; cameras: CameraRecord[]; rules: RuleRecord[]; role: "admin" | "viewer" };
export type QueryPeriod = { start: string; end: string; environmentId?: string };
const environmentFields = "id,organization_id,name,version";
const cameraFields = "id,organization_id,environment_id,name,source,address,monitor_id,enabled,version";
const ruleFields = "id,organization_id,environment_id,name,kind,enabled,start_time,end_time,delay_seconds,version";

let singleton: { client: SupabaseClient; repository: DataRepository } | null = null;
export function backend() {
  if (typeof window === "undefined") return null;
  const config = parseBackendConfig(import.meta.env);
  if (!config) return null;
  if (!singleton) {
    const client = createClient(config.url, config.key, {
      auth: { detectSessionInUrl: false, persistSession: true, autoRefreshToken: true },
      global: { fetch: (input, init) => fetch(input, { ...init, signal: init?.signal ? AbortSignal.any([init.signal, AbortSignal.timeout(15000)]) : AbortSignal.timeout(15000) }) },
    });
    singleton = { client, repository: new DataRepository(client, config) };
  }
  return singleton;
}

export class DataRepository {
  readonly client: SupabaseClient;
  readonly org: string;
  constructor(client: SupabaseClient, config: BackendConfig) { this.client = client; this.org = config.organizationId; }
  async catalog(userId: string): Promise<Catalog> {
    const member = await this.client.from("organization_members").select("role").eq("organization_id", this.org).eq("user_id", userId).maybeSingle();
    if (member.error) throw dataError(member.error);
    if (!member.data || !["admin", "viewer"].includes(member.data.role)) throw new Error("Sua conta ainda não foi vinculada a esta organização.");
    const [environments, cameras, rules] = await Promise.all([
      this.client.from("environments").select(environmentFields).eq("organization_id", this.org).order("name").limit(500),
      this.client.from("cameras").select(cameraFields).eq("organization_id", this.org).order("name").limit(500),
      this.client.from("alert_rules").select(ruleFields).eq("organization_id", this.org).order("name").limit(500),
    ]);
    for (const response of [environments,cameras,rules]) if (response.error) throw dataError(response.error);
    if ([environments,cameras,rules].some((result) => (result.data?.length ?? 0) === 500)) throw new Error("O catálogo atingiu o limite desta versão. Contate o administrador.");
    return { environments: environments.data as EnvironmentRecord[], cameras: cameras.data as CameraRecord[], rules: rules.data as RuleRecord[], role: member.data.role };
  }
  async saveEnvironment(name: string, existing?: EnvironmentRecord): Promise<EnvironmentRecord> {
    const invalid = validateEnvironmentName(name, []); if (invalid) throw new Error(invalid);
    const values = { name: name.trim().replace(/\s+/g," ") };
    const query = existing ? this.client.from("environments").update(values).eq("id",existing.id).eq("organization_id",this.org).eq("version",existing.version) : this.client.from("environments").insert({ ...values, organization_id:this.org });
    const { data,error } = await query.select(environmentFields).single(); if (error) throw dataError(error); return data;
  }
  async saveCamera(draft: CameraDraft, monitorId: string, enabled: boolean, existing?: CameraRecord): Promise<CameraRecord> {
    const invalid = validateCameraDraft(draft); if (invalid) throw new Error(invalid);
    if (monitorId && !/^[a-zA-Z0-9_-]{1,64}$/.test(monitorId)) throw new Error("O identificador do monitor deve conter letras, números, hífen ou sublinhado.");
    const values = { name: draft.name.trim(), environment_id:draft.environment, source:draft.source, address:draft.address.trim(), monitor_id:monitorId || null, enabled };
    const query = existing ? this.client.from("cameras").update(values).eq("id",existing.id).eq("organization_id",this.org).eq("version",existing.version) : this.client.from("cameras").insert({ ...values, organization_id:this.org });
    const {data,error} = await query.select(cameraFields).single(); if(error) throw dataError(error); return data;
  }
  async saveRule(values: Pick<RuleRecord,"environment_id"|"name"|"kind"|"enabled"|"start_time"|"end_time"|"delay_seconds">, existing?: RuleRecord): Promise<RuleRecord> {
    const query = existing ? this.client.from("alert_rules").update(values).eq("organization_id",this.org).eq("id",existing.id).eq("version",existing.version) : this.client.from("alert_rules").insert({...values,organization_id:this.org});
    const {data,error} = await query.select(ruleFields).single(); if(error) throw dataError(error); return data;
  }
  async samples(period: QueryPeriod, page=0, signal?: AbortSignal): Promise<{ rows: SampleRecord[]; more: boolean }> {
    const lastCompleteStart = new Date(Date.parse(period.end) - 60000).toISOString();
    let query = this.client.from("occupancy_samples").select("id,environment_id,camera_id,bucket_start,state,people_count,model_version").eq("organization_id",this.org).gte("bucket_start",period.start).lte("bucket_start",lastCompleteStart).order("bucket_start",{ascending:false}).order("id").range(page*50,page*50+50);
    if(period.environmentId) query=query.eq("environment_id",period.environmentId);
    if(signal) query=query.abortSignal(signal);
    const {data,error}=await query; if(error) throw dataError(error);
    return {rows:(data??[]).slice(0,50) as SampleRecord[], more:(data?.length??0)>50};
  }
  async alerts(period:QueryPeriod,page=0,signal?:AbortSignal):Promise<{rows:AlertRecord[];more:boolean}> {
    let query=this.client.from("alerts").select("id,environment_id,camera_id,title,detail,status,occurred_at,reviewed_at,version").eq("organization_id",this.org).gte("occurred_at",period.start).lt("occurred_at",period.end).order("occurred_at",{ascending:false}).order("id").range(page*50,page*50+50);
    if(period.environmentId) query=query.eq("environment_id",period.environmentId);
    if(signal) query=query.abortSignal(signal);
    const {data,error}=await query;if(error)throw dataError(error);
    return {rows:(data??[]).slice(0,50) as AlertRecord[],more:(data?.length??0)>50};
  }
  async report(period:QueryPeriod,signal?:AbortSignal):Promise<ReportRow[]> {
    let query=this.client.rpc("occupancy_report",{org:this.org,starts_at:period.start,ends_at:period.end,env:period.environmentId||null}).limit(500);
    if(signal)query=query.abortSignal(signal);
    const {data,error}=await query;if(error)throw dataError(error);
    if((data?.length??0)>=500)throw new Error("O relatório atingiu o limite desta versão. Reduza o período ou selecione um ambiente.");
    return data??[];
  }
  async reviewAlert(alert:AlertRecord,status:"reviewed"|"resolved") {
    const {data,error}=await this.client.rpc("review_alert",{alert_id:alert.id,expected_version:alert.version,next_status:status});
    if(error)throw dataError(error);return data as AlertRecord;
  }
}
