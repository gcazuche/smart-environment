"use client";

import { useEffect, useState } from "react";
import { DashboardDialog } from "./dashboard-dialog";
import { periodRange, type Period } from "./dashboard-model";
import { downloadCsv, periodBounds } from "./report-model";
import type { AlertRecord, CameraRecord, DataRepository, EnvironmentRecord, QueryPeriod, ReportRow, SampleRecord } from "./data-client";

type DataProps = { repository: DataRepository | null; environments: EnvironmentRecord[]; cameras: CameraRecord[] };
type Mode = "history" | "indicators" | "alerts";
type Result = { samples: SampleRecord[]; alerts: AlertRecord[]; report: ReportRow[]; more: boolean };
const emptyResult: Result = { samples: [], alerts: [], report: [], more: false };
const stateNames = { occupied: "Ocupado", empty: "Vazio", unknown: "Sem leitura válida", open: "Aberto", reviewed: "Revisado", resolved: "Resolvido" };
const formatTime = (value: string) => new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", dateStyle: "short", timeStyle: "medium" }).format(new Date(value));

export function HistoryPanel(props: DataProps) { return <RecordsPanel {...props} mode="history" />; }
export function IndicatorsPanel(props: DataProps) { return <RecordsPanel {...props} mode="indicators" />; }
export function AlertsPanel(props: DataProps & { canEdit: boolean; onConfigure: () => void }) { return <RecordsPanel {...props} mode="alerts" />; }

function RecordsPanel({ repository, environments, cameras, mode, canEdit = false, onConfigure }: DataProps & { mode: Mode; canEdit?: boolean; onConfigure?: () => void }) {
  const [period, setPeriod] = useState<Period>("today");
  const [environment, setEnvironment] = useState("");
  const [page, setPage] = useState(0);
  const [revision, setRevision] = useState(0);
  const [asOf, setAsOf] = useState(() => Date.now());
  const [snapshot, setSnapshot] = useState<{ key: string; result: Result; bounds: QueryPeriod; error: string } | null>(null);
  const [selected, setSelected] = useState<AlertRecord | null>(null);
  const key = `${mode}:${period}:${environment}:${page}:${revision}`;
  const loading = !!repository && snapshot?.key !== key;
  const result = snapshot?.key === key ? snapshot.result : emptyResult;
  const error = snapshot?.key === key ? snapshot.error : "";
  const cameraName = (id: string) => cameras.find(camera => camera.id === id)?.name ?? id;
  const environmentName = (id: string) => environments.find(item => item.id === id)?.name ?? id;

  useEffect(() => {
    if (!repository) return;
    const controller = new AbortController();
    const bounds = { ...periodBounds(period, asOf), environmentId: environment || undefined };
    const load = async () => {
      try {
        let response: Result;
        if (mode === "history") { const data = await repository.samples(bounds, page, controller.signal); response = { ...emptyResult, samples: data.rows, more: data.more }; }
        else if (mode === "alerts") { const data = await repository.alerts(bounds, page, controller.signal); response = { ...emptyResult, alerts: data.rows, more: data.more }; }
        else response = { ...emptyResult, report: await repository.report(bounds, controller.signal) };
        if (!controller.signal.aborted) setSnapshot({ key, result: response, bounds, error: "" });
      } catch (reason) {
        if (!controller.signal.aborted) setSnapshot({ key, result: emptyResult, bounds, error: reason instanceof Error ? reason.message : "Não foi possível consultar." });
      }
    };
    void load();
    return () => controller.abort();
  }, [repository, key, period, environment, page, mode, asOf]);

  const exportRows = () => {
    const scope = [["Início (UTC)", "Fim exclusivo (UTC)", "Ambiente", "Página"], [snapshot!.bounds.start, snapshot!.bounds.end, environment ? environmentName(environment) : "Todos", String(page + 1)]];
    if (mode === "history") downloadCsv(`historico-pagina-${page + 1}.csv`, [...scope, ["Minuto (UTC)", "Câmera", "Ambiente", "Estado", "Pessoas", "Modelo"], ...result.samples.map(row => [row.bucket_start, cameraName(row.camera_id), environmentName(row.environment_id), stateNames[row.state], row.people_count, row.model_version])]);
    if (mode === "indicators") downloadCsv("indicadores-por-camera.csv", [...scope, ["Câmera", "Ambiente", "Minutos registrados", "Ocupados", "Vazios", "Desconhecidos", "Pico de pessoas"], ...result.report.map(row => [cameraName(row.camera_id), environmentName(row.environment_id), row.observed_minutes, row.occupied_minutes, row.empty_minutes, row.unknown_minutes, row.peak_people])]);
  };
  const count = mode === "history" ? result.samples.length : mode === "alerts" ? result.alerts.length : result.report.length;
  return <section className="page-stack" aria-busy={loading}>
    <div className="page-intro"><div><p className="eyebrow">DADOS DO AMBIENTE</p><h2>{mode === "history" ? "Histórico de ocupação" : mode === "indicators" ? "Indicadores por câmera" : "Alertas e eventos"}</h2><span>Registros persistidos, separados por câmera e ambiente.</span></div>
      {onConfigure && <button className="secondary-button" type="button" onClick={onConfigure}>Configurar regras</button>}
    </div>
    <div className="filter-bar">
      <label className="select-field"><span>Período</span><select value={period} onChange={event => { setPeriod(event.target.value as Period); setPage(0); setSelected(null); setAsOf(Date.now()); }}><option value="today">Hoje</option><option value="7d">Últimos 7 dias</option><option value="30d">Últimos 30 dias</option></select></label>
      <label className="select-field"><span>Ambiente</span><select value={environment} onChange={event => { setEnvironment(event.target.value); setPage(0); setSelected(null); setAsOf(Date.now()); }}><option value="">Todos os ambientes</option>{environments.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <button className="secondary-button" type="button" disabled={!repository || loading} onClick={() => { setPage(0); setAsOf(Date.now()); setRevision(value => value + 1); }}>Atualizar</button>
      {mode !== "alerts" && <button className="secondary-button" type="button" disabled={!repository || loading || !!error || !count} onClick={exportRows}>{mode === "history" ? "Exportar página (CSV)" : "Exportar relatório (CSV)"}</button>}
    </div>
    {snapshot?.key === key && <p className="field-help">Período consultado: {periodRange(period, Date.parse(snapshot.bounds.end))} · até {formatTime(snapshot.bounds.end)} (Brasília). Use Atualizar para novas leituras.</p>}
    {!repository ? <div className="data-empty"><h3>Banco ainda não conectado</h3><p>As consultas estarão disponíveis após configurar o Supabase. Isso não significa ausência de eventos.</p></div> : loading ? <p role="status">Consultando registros…</p> : error ? <p className="form-feedback" role="alert">{error} Use Atualizar para tentar novamente.</p> : count === 0 ? <div className="data-empty"><h3>Nenhum registro neste recorte</h3><p>Não há dados retornados para este período e ambiente. Ausência de registro não é evidência de ambiente vazio.</p></div> :
      // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- enables keyboard scrolling of wide tables
      <div className="records-scroll" tabIndex={0} role="region" aria-label="Registros consultados"><table className="records-table">
        {mode === "history" && <><thead><tr>{["Horário (Brasília)", "Câmera", "Ambiente", "Estado", "Pessoas"].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead><tbody>{result.samples.map(row => <tr key={row.id}><td>{formatTime(row.bucket_start)}</td><td>{cameraName(row.camera_id)}</td><td>{environmentName(row.environment_id)}</td><td>{stateNames[row.state]}</td><td>{row.people_count ?? "—"}</td></tr>)}</tbody></>}
        {mode === "indicators" && <><thead><tr>{["Câmera / ambiente", "Registrados (min)", "Ocupados (min)", "Vazios (min)", "Desconhecidos (min)", "Pico de pessoas"].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead><tbody>{result.report.map(row => <tr key={`${row.camera_id}:${row.environment_id}`}><td>{cameraName(row.camera_id)} / {environmentName(row.environment_id)}</td><td>{row.observed_minutes}</td><td>{row.occupied_minutes}</td><td>{row.empty_minutes}</td><td>{row.unknown_minutes}</td><td>{row.peak_people ?? "—"}</td></tr>)}</tbody></>}
        {mode === "alerts" && <><thead><tr>{["Horário (Brasília)", "Ambiente", "Alerta", "Estado", "Ação"].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead><tbody>{result.alerts.map(row => <tr key={row.id}><td>{formatTime(row.occurred_at)}</td><td>{environmentName(row.environment_id)}</td><td>{row.title}</td><td>{stateNames[row.status]}</td><td><button className="text-button" type="button" onClick={() => setSelected(row)}>Detalhes / revisar</button></td></tr>)}</tbody></>}
      </table></div>}
    {repository && mode !== "indicators" && <div className="pagination"><button className="secondary-button" type="button" disabled={page === 0 || loading} onClick={() => setPage(value => value - 1)}>Anterior</button><span>Página {page + 1} · até 50 registros</span><button className="secondary-button" type="button" disabled={!result.more || loading || !!error} onClick={() => setPage(value => value + 1)}>Próxima</button></div>}
    {mode === "indicators" && <p className="field-help">Cada amostra representa um minuto completo. Desconhecido não conta como vazio. Não somamos pessoas de câmeras sobrepostas, nem inferimos consumo de energia ou produtividade.</p>}
    {mode === "alerts" && <div className="alert-disclaimer"><strong>Decisão humana obrigatória</strong><p>Alertas são indícios para revisão. O sistema não declara culpa, produtividade ou ação disciplinar automaticamente. A criação automática dos alertas depende do serviço de análise no servidor.</p></div>}
    {selected && repository && <AlertReview key={selected.id} alert={selected} repository={repository} canEdit={canEdit} onClose={() => setSelected(null)} onSaved={() => { setSelected(null); setRevision(value => value + 1); }} />}
  </section>;
}

function AlertReview({ alert, repository, canEdit, onClose, onSaved }: { alert: AlertRecord; repository: DataRepository; canEdit: boolean; onClose: () => void; onSaved: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const close = () => { if (!busy) onClose(); };
  const save = async () => {
    if (busy || !canEdit || alert.status === "resolved") return;
    setBusy(true); setError("");
    try { await repository.reviewAlert(alert, alert.status === "open" ? "reviewed" : "resolved"); onSaved(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível revisar."); }
    finally { setBusy(false); }
  };
  return <DashboardDialog title={alert.title} onClose={close}><p>{alert.detail || "Sem detalhes adicionais."}</p><p>{formatTime(alert.occurred_at)} · {stateNames[alert.status]}</p>
    {error && <p className="form-feedback" role="alert">{error} Feche e atualize a lista antes de tentar novamente.</p>}
    {!canEdit && <p>A sua conta permite somente consulta.</p>}
    <div className="modal-actions"><button className="secondary-button" type="button" disabled={busy} onClick={close}>Fechar</button>{alert.status !== "resolved" && <button className="primary-action" type="button" disabled={busy || !canEdit || !!error} onClick={() => void save()}>{busy ? "Salvando…" : alert.status === "open" ? "Marcar como revisado" : "Resolver alerta"}</button>}</div>
  </DashboardDialog>;
}
