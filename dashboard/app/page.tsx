"use client";

import { useEffect, useMemo, useState } from "react";
import { LoginScreen, ProfileModal, userInitials } from "./auth";
import { useBackendSession } from "./backend-session";
import type { CameraRecord, EnvironmentRecord, RuleRecord } from "./data-client";
import { BrandLogo } from "./brand-logo";
import { StreamPreview } from "./stream-preview";
import { processingConfigured, ProcessingContext, ServerCamera, useProcessingServer } from "./processing-server";
import { DashboardClock } from "./dashboard-clock";
import { CameraForm, EnvironmentForm, RulesDialog } from "./management-forms";
import { readingAge } from "./dashboard-model";
import { HistoryPanel, IndicatorsPanel, AlertsPanel } from "./history-panels";

type Section = "overview" | "cameras" | "environments" | "indicators" | "alerts" | "history";
type CameraStatus = "online" | "offline" | "waiting";

type CameraState = {
  camera_id: string;
  monitor_id?: string;
  environment_id?: string;
  name: string;
  environment: string;
  source: "webcam" | "mjpeg" | "rtsp";
  status: CameraStatus;
  people_count: number;
  detector: string;
  backend: string;
  latency_ms: number | null;
  last_seen_at: string | null;
  error_code: string | null;
};

type MonitorResponse = { cameras: CameraState[] };

const waitingCameras: CameraState[] = [
  { camera_id: "pc", name: "Câmera do computador", environment: "Escritório", source: "webcam", status: "waiting", people_count: 0, detector: "intel_yolo26", backend: "unknown", latency_ms: null, last_seen_at: null, error_code: null },
  { camera_id: "phone", name: "Câmera do celular", environment: "Escritório", source: "mjpeg", status: "waiting", people_count: 0, detector: "intel_yolo26", backend: "unknown", latency_ms: null, last_seen_at: null, error_code: null },
];

function environmentLabel(name: string) {
  return name;
}

const navigation: Array<{ key: Section; icon: string; label: string }> = [
  { key: "overview", icon: "⌂", label: "Visão geral" },
  { key: "cameras", icon: "▦", label: "Câmeras" },
  { key: "environments", icon: "◇", label: "Ambientes" },
  { key: "indicators", icon: "↗", label: "Indicadores" },
  { key: "alerts", icon: "!", label: "Alertas" },
  { key: "history", icon: "◷", label: "Histórico" },
];

const titles: Record<Section, { eyebrow: string; title: string }> = {
  overview: { eyebrow: "PAINEL DO AMBIENTE", title: "Visão geral" },
  cameras: { eyebrow: "MONITORAMENTO", title: "Câmeras" },
  environments: { eyebrow: "ORGANIZAÇÃO", title: "Ambientes" },
  indicators: { eyebrow: "ANÁLISE", title: "Indicadores" },
  alerts: { eyebrow: "ACOMPANHAMENTO", title: "Alertas" },
  history: { eyebrow: "REGISTROS", title: "Histórico" },
};

function statusLabel(status: CameraStatus) {
  if (status === "online") return "Online";
  if (status === "offline") return "Indisponível";
  return "Aguardando agente";
}

function lastReading(camera: CameraState) {
  return readingAge(camera.last_seen_at);
}

function CameraPreview({ camera, large = false }: { camera: CameraState; large?: boolean }) {
  const [frameVersion, setFrameVersion] = useState(0);
  const [frameLoaded, setFrameLoaded] = useState(false);

  useEffect(() => {
    if (processingConfigured() || camera.status !== "online") return;
    const timer = window.setInterval(() => setFrameVersion(Date.now()), 350);
    return () => window.clearInterval(timer);
  }, [camera.status]);

  if (processingConfigured()) return <ServerCamera cameraId={camera.camera_id} name={camera.name} />;

  const showLiveFrame = camera.status === "online";
  const frameUrl = `http://127.0.0.1:8765/api/cameras/${encodeURIComponent(camera.monitor_id ?? camera.camera_id)}/frame.jpg?v=${frameVersion}`;
  return (
    <div className={`camera-preview ${large ? "large" : ""}`}>
      {showLiveFrame && (
        // eslint-disable-next-line @next/next/no-img-element -- loopback JPEG is already resized and annotated
        <img
          className={`camera-feed ${frameLoaded ? "visible" : ""}`}
          src={frameUrl}
          alt={`Vídeo ao vivo com detecções — ${camera.name}`}
          crossOrigin="anonymous"
          onLoad={() => setFrameLoaded(true)}
          onError={() => setFrameLoaded(false)}
        />
      )}
      <span className={`online-badge status-${camera.status}`}><i /> {statusLabel(camera.status).toUpperCase()}</span>
      <div className="camera-frame aggregate-frame" aria-hidden="true">
        <span className="corner tl" /><span className="corner tr" />
        <span className="corner bl" /><span className="corner br" />
        <strong>{camera.status === "online" ? camera.people_count : "—"}</strong>
        <span className="detection-label">{camera.people_count === 1 ? "pessoa" : "pessoas"}</span>
      </div>
      <span className="preview-note">{showLiveFrame ? "Vídeo local com detecções — não gravado" : "Vídeo disponível apenas no dashboard local"}</span>
    </div>
  );
}

function CameraDeviceCard({ camera, onOpen }: { camera: CameraState; onOpen: () => void }) {
  return (
    <article className="device-card" key={camera.camera_id}>
      <CameraPreview camera={camera} />
      <div className="device-card-body">
        <div className="camera-title"><span className="device-icon">●</span><div><h3>{camera.name}</h3><p>{environmentLabel(camera.environment)} · {camera.source === "webcam" ? "Computador local" : "Fonte de rede"}</p></div><span className={`small-online status-text-${camera.status}`}><i /> {statusLabel(camera.status)}</span></div>
        <div className="device-summary"><span><small>Pessoas agora</small><strong>{camera.status === "online" ? camera.people_count : "—"}</strong></span><span><small>Última leitura</small><strong>{lastReading(camera)}</strong></span><span><small>Origem</small><strong>{camera.source === "webcam" ? "Webcam" : camera.source === "rtsp" ? "Câmera IP / RTSP" : "MJPEG / celular"}</strong></span></div>
        <button className="primary-button" type="button" onClick={onOpen}>Abrir detalhes <span>→</span></button>
      </div>
    </article>
  );
}

export default function Home() {
  const session = useBackendSession();
  if (!session.ready || !session.user) return <LoginScreen ready={session.ready} onLogin={session.localLogin} authenticate={session.configured ? session.login : undefined} configurationError={!session.repository ? session.error : ""} />;
  return <Dashboard key={session.user.id ?? session.user.email} session={session} />;
}

function Dashboard({ session }: { session: ReturnType<typeof useBackendSession> }) {
  const { repository, catalog } = session;
  const processing = useProcessingServer(repository);
  const authUser = session.user!;
  const canEdit = catalog?.role === "admin" && !session.loading;
  const [notice, setNotice] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [active, setActive] = useState<Section>("overview");
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);
  const [selectedEnvironment, setSelectedEnvironment] = useState<string | null>(null);
  const [addCameraOpen, setAddCameraOpen] = useState(false);
  const [editCamera, setEditCamera] = useState<CameraRecord | null>(null);
  const [editEnvironment, setEditEnvironment] = useState<EnvironmentRecord | null>(null);
  const [addEnvironmentOpen, setAddEnvironmentOpen] = useState(false);
  const [rulesOpen, setRulesOpen] = useState(false);
  const [cameraView, setCameraView] = useState<"stream" | "detection">("stream");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("todas");
  const [telemetry, setCameras] = useState<CameraState[]>(waitingCameras);
  const [localAgentConnected, setAgentConnected] = useState(false);
  const agentConnected = processingConfigured() ? processing.connected : localAgentConnected;

  const environments: EnvironmentRecord[] = catalog?.environments ?? (session.configured ? [] : Array.from(new Set(telemetry.map(camera => camera.environment))).map(name => ({ id: name, name, organization_id: "", version: 1 })));
  const cameras: CameraState[] = useMemo(() => session.configured ? (catalog?.cameras ?? []).map(record => {
    const live = record.enabled ? (processingConfigured() ? processing.readings.find(camera => camera.camera_id === record.id) : telemetry.find(camera => camera.camera_id === record.monitor_id)) : undefined;
    return { ...(live ?? waitingCameras[0]), camera_id: record.id, monitor_id: record.monitor_id ?? undefined,
      name: record.name, source: record.source, environment_id: record.environment_id,
      environment: catalog?.environments.find(item => item.id === record.environment_id)?.name ?? "Ambiente indisponível",
      status: live?.status ?? "waiting", people_count: live?.people_count ?? 0, last_seen_at: live?.last_seen_at ?? null, error_code: null };
  }) : telemetry, [session.configured, catalog, telemetry, processing.readings]);

  useEffect(() => {
    if (processingConfigured()) return;
    if (!(["localhost", "127.0.0.1"].includes(window.location.hostname))) return;
    let activeRequest = true;
    let controller: AbortController | undefined;

    const refresh = async () => {
      controller?.abort();
      controller = new AbortController();
      try {
        const response = await fetch("http://127.0.0.1:8765/api/cameras", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("monitor unavailable");
        const payload = await response.json() as MonitorResponse;
        if (activeRequest && Array.isArray(payload.cameras)) {
          setCameras(payload.cameras);
          setAgentConnected(true);
        }
      } catch (error) {
        if (activeRequest && !(error instanceof DOMException && error.name === "AbortError")) {
          setAgentConnected(false);
          setCameras((previous) => previous.map((camera) => ({ ...camera, status: camera.status === "waiting" ? "waiting" : "offline" })));
        }
      }
    };

    void refresh();
    const timer = window.setInterval(() => void refresh(), 2000);
    return () => {
      activeRequest = false;
      controller?.abort();
      window.clearInterval(timer);
    };
  }, []);

  const visibleCameras = useMemo(
    () => cameras.filter((camera) => {
      const matchesSearch = `${camera.name} ${camera.environment} ${camera.source}`.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = statusFilter === "todas" || camera.status === statusFilter;
      return matchesSearch && matchesStatus;
    }),
    [cameras, search, statusFilter],
  );
  const selectedCamera = cameras.find((camera) => camera.camera_id === selectedCameraId) ?? null;
  const selectedEnvironmentRecord = environments.find(item => item.id === selectedEnvironment);
  const selectedEnvironmentCameras = selectedEnvironment
    ? cameras.filter((camera) => (camera.environment_id ?? camera.environment) === selectedEnvironment)
    : [];

  const navigate = (section: Section) => {
    setActive(section);
    setSelectedCameraId(null);
    setSelectedEnvironment(null);
  };

  const handleLogout = async () => {
    await session.logout();
    setProfileOpen(false);
    setAddCameraOpen(false);
    setEditCamera(null);
    setEditEnvironment(null);
    setAddEnvironmentOpen(false);
    setRulesOpen(false);
    setActive("overview");
    setSelectedCameraId(null);
    setSelectedEnvironment(null);
    setCameras(waitingCameras);
    setAgentConnected(false);
    setNotice("");
  };

  const savedCamera = (record: CameraRecord) => { session.commitCatalog(authUser.id ?? "", previous => previous ? ({ ...previous, cameras: [...previous.cameras.filter(item => item.id !== record.id), record] }) : null); setNotice("Câmera salva no cadastro. Configure a origem no servidor para iniciar a transmissão."); };
  const savedEnvironment = (record: EnvironmentRecord) => { session.commitCatalog(authUser.id ?? "", previous => previous ? ({ ...previous, environments: [...previous.environments.filter(item => item.id !== record.id), record] }) : null); setNotice("Ambiente salvo."); };
  const savedRule = (record: RuleRecord) => { session.commitCatalog(authUser.id ?? "", previous => previous ? ({ ...previous, rules: [...previous.rules.filter(item => item.id !== record.id), record] }) : null); setNotice("Regra salva. Sua aplicação depende do serviço de análise no servidor."); };
  const dataProps = { repository: catalog ? repository : null, environments, cameras: catalog?.cameras ?? [] };

  return (
    <ProcessingContext.Provider value={processing}><main className="app-shell">
      <aside className="sidebar">
        <button className="brand" type="button" aria-label="Smart Environment — ir para visão geral" onClick={() => navigate("overview")}>
          <BrandLogo className="brand-full" />
          <BrandLogo variant="symbol" className="brand-compact" />
        </button>

        <nav aria-label="Navegação principal">
          <p className="nav-label">PLATAFORMA</p>
          {navigation.map((item) => (
            <button
              className={`nav-item ${active === item.key ? "active" : ""}`}
              key={item.key}
              type="button"
              onClick={() => navigate(item.key)}
              aria-label={item.label}
              title={item.label}
              aria-current={active === item.key ? "page" : undefined}
            >
              <span className="nav-icon" aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
              {item.key === "cameras" && <span className="nav-count">{cameras.length}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <div className={`system-health ${agentConnected ? "" : "health-waiting"}`}><span /> {agentConnected ? "Monitor conectado" : "Monitor desconectado"}</div>
          <button className="profile" type="button" aria-label="Abrir perfil da conta" aria-haspopup="dialog" aria-expanded={profileOpen} onClick={() => setProfileOpen((open) => !open)}>
            <span className="avatar">{userInitials(authUser.name)}</span>
            <span><strong>{authUser.name}</strong><small>{authUser.role}</small></span>
            <b aria-hidden="true">•••</b>
          </button>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbar-heading">
            <button className="mobile-brand" type="button" aria-label="Smart Environment — ir para visão geral" onClick={() => navigate("overview")}>
              <BrandLogo variant="symbol" />
            </button>
            <div className="topbar-titles">
              <p className="eyebrow">{titles[active].eyebrow}</p>
              <h1>{selectedCamera ? selectedCamera.name : selectedEnvironmentRecord ? selectedEnvironmentRecord.name : titles[active].title}</h1>
              <DashboardClock />
            </div>
          </div>
          <div className="top-actions">
            <span className={`simulation-pill ${agentConnected ? "connected" : ""}`}>{processingConfigured() ? (agentConnected ? "Servidor conectado" : "Aguardando servidor") : active === "cameras" && cameraView === "stream" ? "Transmissão independente da IA" : agentConnected ? "Agente local conectado" : "Aguardando agente local"}</span>
            <button className="icon-button" type="button" aria-label="Notificações" onClick={() => navigate("alerts")}>♢</button>
            <button className="account-button" type="button" aria-label="Abrir perfil" aria-haspopup="dialog" aria-expanded={profileOpen} onClick={() => setProfileOpen((open) => !open)}>
              <span className="avatar">{userInitials(authUser.name)}</span>
            </button>
          </div>
        </header>

        <div className="content">
          {!session.configured && <p className="connection-notice" role="status">Acesso local: banco ainda não configurado. Os cadastros e relatórios usarão o Supabase quando você conectar o projeto.</p>}
          {session.loading && <p role="status">Carregando cadastros e permissões…</p>}
          {session.error && <div className="form-feedback" role="alert">{session.error} <button type="button" className="text-button" onClick={session.refresh}>Tentar novamente</button></div>}
          {processingConfigured() && processing.error && <p className="connection-notice" role="status">{processing.error}</p>}
          {notice && <p className="connection-notice" role="status">{notice} <button type="button" className="text-button" onClick={() => setNotice("")}>Dispensar</button></p>}
          {active === "overview" && (
            <Overview cameras={cameras} agentConnected={agentConnected} connected={!!catalog} onOpenHistory={() => navigate("history")} />
          )}

          {active === "cameras" && <div className="camera-view-switch" role="group" aria-label="Modo de visualização das câmeras">
            <button type="button" aria-pressed={cameraView === "stream"} onClick={() => { setCameraView("stream"); setSelectedCameraId(null); }}>Transmissão</button>
            <button type="button" aria-pressed={cameraView === "detection"} onClick={() => setCameraView("detection")}>{processingConfigured() ? "Dispositivos e detecções" : "Detecção local"}</button>
          </div>}
          {active === "cameras" && cameraView === "stream" && <><div className="stream-management"><button className="secondary-button" type="button" onClick={() => setAddCameraOpen(true)}>Adicionar câmera</button></div>{processingConfigured() ? <div className="server-stream-grid">{cameras.map(camera => <ServerCamera key={camera.camera_id} cameraId={camera.camera_id} name={camera.name} />)}{cameras.length === 0 && <p>Cadastre uma câmera e vincule seu UUID ao stream no servidor.</p>}</div> : <StreamPreview />}</>}

          {active === "cameras" && cameraView === "detection" && !selectedCamera && (
            <section className="page-stack">
              <div className="page-intro">
                <div><p className="eyebrow">DISPOSITIVOS CADASTRADOS</p><h2>Todas as câmeras</h2><span>Gerencie cada ponto de monitoramento em um só lugar.</span></div>
                <button className="primary-action" type="button" onClick={() => setAddCameraOpen(true)}>＋ Adicionar câmera</button>
              </div>
              <div className="filter-bar">
                <label className="search-field"><span aria-hidden="true">⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar câmera ou ambiente" aria-label="Buscar câmera ou ambiente" /></label>
                <label className="select-field"><span>Status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="todas">Todas</option><option value="online">Online</option><option value="offline">Offline</option><option value="waiting">Aguardando agente</option></select></label>
              </div>
              <div className="camera-grid">
                {visibleCameras.map((camera) => (
                  <CameraDeviceCard key={camera.camera_id} camera={camera} onOpen={() => setSelectedCameraId(camera.camera_id)} />
                ))}
                {visibleCameras.length === 0 && (
                  <div className="empty-state"><b>⌕</b><h3>Nenhuma câmera encontrada</h3><p>Ajuste a busca ou o filtro selecionado.</p></div>
                )}
                <button className="add-device-card" type="button" onClick={() => setAddCameraOpen(true)}><span>＋</span><strong>Adicionar outra câmera</strong><small>Webcam, câmera IP ou gateway ESP32</small></button>
              </div>
            </section>
          )}

          {active === "cameras" && cameraView === "detection" && selectedCamera && (
            <CameraDetails camera={selectedCamera} onBack={() => setSelectedCameraId(null)} onEdit={() => { const record = catalog?.cameras.find(item => item.id === selectedCamera.camera_id); if (record) setEditCamera(record); else setNotice("Conecte o banco e cadastre esta câmera para editar sua configuração."); }} />
          )}

          {active === "environments" && !selectedEnvironment && <Environments environments={environments} cameras={cameras} onOpenEnvironment={setSelectedEnvironment} onAdd={() => setAddEnvironmentOpen(true)} />}
          {active === "environments" && selectedEnvironmentRecord && <EnvironmentDetails name={selectedEnvironmentRecord.name} cameras={selectedEnvironmentCameras} onEdit={() => { if (catalog) setEditEnvironment(selectedEnvironmentRecord); else setNotice("Conecte o banco para editar ambientes."); }} onBack={() => setSelectedEnvironment(null)} onOpenCamera={(cameraId) => { setActive("cameras"); setCameraView("detection"); setSelectedEnvironment(null); setSelectedCameraId(cameraId); }} />}
          {active === "indicators" && <IndicatorsPanel {...dataProps} />}
          {active === "alerts" && <AlertsPanel {...dataProps} canEdit={canEdit} onConfigure={() => setRulesOpen(true)} />}
          {active === "history" && <HistoryPanel {...dataProps} />}
        </div>
      </section>

      {addCameraOpen && <CameraForm repository={repository} canEdit={canEdit} environments={environments} onSaved={savedCamera} onClose={() => setAddCameraOpen(false)} />}
      {editCamera && <CameraForm repository={repository} canEdit={canEdit} initial={editCamera} environments={environments} onSaved={savedCamera} onClose={() => setEditCamera(null)} />}
      {addEnvironmentOpen && <EnvironmentForm repository={repository} canEdit={canEdit} environments={environments} onSaved={savedEnvironment} onClose={() => setAddEnvironmentOpen(false)} />}
      {editEnvironment && <EnvironmentForm repository={repository} canEdit={canEdit} initial={editEnvironment} environments={environments} onSaved={savedEnvironment} onClose={() => setEditEnvironment(null)} />}
      {rulesOpen && <RulesDialog repository={repository} canEdit={canEdit} rules={catalog?.rules ?? []} environments={environments} onSaved={savedRule} onClose={() => setRulesOpen(false)} />}
      {profileOpen && <ProfileModal user={authUser} onClose={() => setProfileOpen(false)} onLogout={handleLogout} />}
    </main></ProcessingContext.Provider>
  );
}

function Overview({ cameras, agentConnected, connected, onOpenHistory }: { cameras: CameraState[]; agentConnected: boolean; connected: boolean; onOpenHistory: () => void }) {
  const onlineCameras = cameras.filter((camera) => camera.status === "online").length;
  const metrics = [
    { label: "Contagem de pessoas", value: "Por câmera", change: "Consulte cada câmera; áreas podem se sobrepor", tone: "teal" },
    { label: "Câmeras online", value: `${onlineCameras}/${cameras.length}`, change: agentConnected ? "Monitor conectado" : "Aguardando leituras", tone: "blue" },
    { label: "Ocupação hoje", value: "—", change: connected ? "Consulte a página Indicadores" : "Histórico ainda não conectado", tone: "lime" },
    { label: "Alertas ativos", value: "—", change: connected ? "Consulte a central de Alertas" : "Serviço de alertas ainda não conectado", tone: "orange" },
  ];

  return (
    <>
      <section className="welcome-card">
        <div><span className={`live-label ${agentConnected ? "" : "waiting"}`}><i /> {agentConnected ? "MONITORAMENTO LOCAL ATIVO" : "AGUARDANDO MONITORAMENTO"}</span><h2>Seu ambiente, em equilíbrio.</h2><p>{agentConnected ? "Consulte os dispositivos para acompanhar as leituras disponíveis." : "A transmissão e a análise de pessoas ficam na página Câmeras. Cada modo informa seu próprio estado de conexão."}</p></div>
        <div className="welcome-visual" aria-hidden="true"><span className="pulse one" /><span className="pulse two" /><div className="building"><i /><i /><i /><i /><i /><i /></div></div>
      </section>
      <section className="metrics-grid" aria-label="Indicadores principais">
        {metrics.map((metric) => <article className="metric-card" key={metric.label}><span className={`metric-symbol ${metric.tone}`} aria-hidden="true" /><p>{metric.label}</p><strong>{metric.value}</strong><small>{metric.change}</small></article>)}
      </section>
      <section className="dashboard-grid">
        <article className="chart-card">
          <div className="card-heading"><div><p className="eyebrow">MOVIMENTO HOJE</p><h2>Ocupação por horário</h2></div></div>
          <div className="data-empty"><h3>{connected ? "Consulte os registros de ocupação" : "Histórico indisponível"}</h3><p>Indicadores e Histórico consultam as observações persistidas por câmera. A leitura ao vivo não cria um histórico por si só.</p></div>
        </article>
        <article className="activity-card"><p className="eyebrow">REGISTROS</p><h2>Histórico do ambiente</h2><div className="data-empty"><p>{connected ? "Filtre as observações por ambiente e período, ou exporte a página consultada em CSV." : "Conecte o banco para consultar os registros. Nenhum evento pode ser confirmado nesta tela."}</p></div><button className="text-button wide" type="button" onClick={onOpenHistory}>Ver histórico completo <span>→</span></button></article>
      </section>
    </>
  );
}

function CameraDetails({ camera, onBack, onEdit }: { camera: CameraState; onBack: () => void; onEdit: () => void }) {
  const healthy = camera.status === "online";
  return (
    <section className="page-stack">
      <button className="back-button" type="button" onClick={onBack}>← Voltar para câmeras</button>
      <div className="detail-grid"><CameraPreview camera={camera} large /><aside className="health-card"><p className="eyebrow">SAÚDE DO DISPOSITIVO</p><h2>{healthy ? "Recebendo leituras" : statusLabel(camera.status)}</h2><dl><div><dt>Conexão</dt><dd className={healthy ? "good" : ""}>{statusLabel(camera.status)}</dd></div><div><dt>Backend</dt><dd>{healthy ? camera.backend : "Sem leitura atual"}</dd></div><div><dt>Processamento</dt><dd>Intel/OpenVINO local</dd></div><div><dt>Latência</dt><dd>{!healthy || camera.latency_ms === null ? "—" : `${camera.latency_ms.toFixed(1)} ms`}</dd></div></dl></aside></div>
      <div className="detail-lower"><article className="info-panel"><p className="eyebrow">CONFIGURAÇÃO</p><h2>Informações da câmera</h2><dl className="info-list"><div><dt>Nome</dt><dd>{camera.name}</dd></div><div><dt>Ambiente</dt><dd>{environmentLabel(camera.environment)}</dd></div><div><dt>Origem</dt><dd>{camera.source === "webcam" ? "Câmera integrada/USB" : camera.source === "rtsp" ? "Câmera IP / RTSP" : "MJPEG / celular"}</dd></div><div><dt>Privacidade</dt><dd>Frames transitórios</dd></div></dl><button className="secondary-button" type="button" onClick={onEdit}>Editar configurações</button></article><article className="info-panel"><p className="eyebrow">CONTAGEM ATUAL</p><h2>Detecção de pessoas</h2><div className="current-count"><strong>{healthy ? camera.people_count : "—"}</strong><span>{healthy ? "pessoas detectadas" : "Sem leitura atual"}</span></div><div className="mini-legend"><span>{lastReading(camera)}</span><small>Modelo Intel YOLO26</small></div></article></div>
    </section>
  );
}

function Environments({ cameras, environments, onOpenEnvironment, onAdd }: { cameras: CameraState[]; environments: EnvironmentRecord[]; onOpenEnvironment: (environment: string) => void; onAdd: () => void }) {

  return (
    <section className="page-stack">
      <div className="page-intro">
        <div><p className="eyebrow">LOCAIS MONITORADOS</p><h2>Ambientes</h2><span>Organize câmeras, ocupação e recursos por espaço físico.</span></div>
        <button className="primary-action" type="button" onClick={onAdd}>＋ Novo ambiente</button>
      </div>
      <div className="environment-grid">
        {environments.map((environment) => {
          const environmentCameras = cameras.filter((camera) => (camera.environment_id ?? camera.environment) === environment.id);
          const onlineCameras = environmentCameras.filter((camera) => camera.status === "online").length;
          const onlyCamera = environmentCameras.length === 1 && environmentCameras[0].status === "online" ? environmentCameras[0] : null;
          const status = onlineCameras === 0 ? "Aguardando" : onlineCameras === environmentCameras.length ? "Ativo" : "Parcial";
          return (
            <article className="environment-card featured" key={environment.id}>
              <div className="room-art"><span /><span /><i /></div>
              <div>
                <span className={`small-online environment-status-${status.toLowerCase()}`}><i /> {status}</span>
                <h3>{environment.name}</h3>
                <p>{environmentCameras.length} {environmentCameras.length === 1 ? "câmera configurada" : "câmeras configuradas"}</p>
                <div className="room-stats"><span><small>Pessoas agora</small><strong>{onlyCamera ? onlyCamera.people_count : "—"}</strong></span><span><small>Câmeras online</small><strong>{onlineCameras}/{environmentCameras.length}</strong></span></div>
                {!onlyCamera && <p className="field-help">Consulte as leituras por câmera; sem contagem unificada.</p>}
                <button className="secondary-button" type="button" aria-label={`Ver ambiente ${environment.name}`} onClick={() => onOpenEnvironment(environment.id)}>Ver ambiente</button>
              </div>
            </article>
          );
        })}
        {environments.length === 0 && <div className="empty-state"><b>⌂</b><h3>Nenhum ambiente configurado</h3><p>Cadastre um ambiente e depois associe suas câmeras.</p></div>}
        <button className="add-environment" type="button" onClick={onAdd}><span>＋</span><strong>Criar outro ambiente</strong><small>Salas, laboratórios ou áreas comuns</small></button>
      </div>
    </section>
  );
}

function EnvironmentDetails({ name, cameras, onBack, onOpenCamera, onEdit }: { name: string; cameras: CameraState[]; onBack: () => void; onEdit: () => void; onOpenCamera: (cameraId: string) => void }) {
  const onlineCameras = cameras.filter((camera) => camera.status === "online").length;
  const onlyCamera = cameras.length === 1 && cameras[0].status === "online" ? cameras[0] : null;

  return (
    <section className="page-stack environment-detail" aria-labelledby="environment-detail-title">
      <button className="back-button" type="button" onClick={onBack}>← Voltar para ambientes</button>
      <div className="page-intro environment-detail-header">
        <div><p className="eyebrow">AMBIENTE MONITORADO</p><h2 id="environment-detail-title">{name}</h2><span>Todos os dispositivos associados a este ambiente.</span></div>
        <button className="secondary-button" type="button" onClick={onEdit}>Editar ambiente</button>
      </div>
      <div className="alert-summary environment-detail-summary">
        <span><strong>{cameras.length}</strong><small>{cameras.length === 1 ? "Câmera" : "Câmeras"}</small></span>
        <span><strong>{onlineCameras}/{cameras.length}</strong><small>Online</small></span>
        <span><strong>{onlyCamera ? onlyCamera.people_count : "—"}</strong><small>{onlyCamera ? "Pessoas agora" : "Consulte por câmera"}</small></span>
      </div>
      <div className="section-heading environment-camera-heading"><div><p className="eyebrow">DISPOSITIVOS DO AMBIENTE</p><h2>Câmeras</h2><span>Visualize e abra cada ponto de monitoramento.</span></div></div>
      <div className="camera-grid environment-camera-grid">
        {cameras.map((camera) => <CameraDeviceCard key={camera.camera_id} camera={camera} onOpen={() => onOpenCamera(camera.camera_id)} />)}
        {cameras.length === 0 && <div className="empty-state"><b>⌂</b><h3>Nenhuma câmera neste ambiente</h3><p>Associe um dispositivo para acompanhar este local.</p></div>}
      </div>
    </section>
  );
}
