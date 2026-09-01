"use client";

import { useEffect, useMemo, useState } from "react";
import { clearLocalSession, LoginScreen, ProfileModal, readLocalSession, userInitials, type AuthUser } from "./auth";

type Section = "overview" | "cameras" | "environments" | "indicators" | "alerts";
type CameraStatus = "online" | "offline" | "waiting";

type CameraState = {
  camera_id: string;
  name: string;
  environment: string;
  source: "webcam" | "mjpeg";
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

const environmentLabels: Record<string, string> = { Escritório: "Escritório principal" };

function environmentLabel(name: string) {
  return environmentLabels[name] ?? name;
}

const navigation: Array<{ key: Section; icon: string; label: string; count?: string }> = [
  { key: "overview", icon: "⌂", label: "Visão geral" },
  { key: "cameras", icon: "▦", label: "Câmeras", count: "2" },
  { key: "environments", icon: "◇", label: "Ambientes" },
  { key: "indicators", icon: "↗", label: "Indicadores" },
  { key: "alerts", icon: "!", label: "Alertas", count: "2" },
];

const titles: Record<Section, { eyebrow: string; title: string }> = {
  overview: { eyebrow: "QUINTA-FEIRA, 14 DE AGOSTO", title: "Visão geral" },
  cameras: { eyebrow: "MONITORAMENTO", title: "Câmeras" },
  environments: { eyebrow: "ORGANIZAÇÃO", title: "Ambientes" },
  indicators: { eyebrow: "ANÁLISE", title: "Indicadores" },
  alerts: { eyebrow: "ACOMPANHAMENTO", title: "Alertas" },
};

const occupancyBars = [38, 52, 45, 66, 81, 74, 68, 58, 43, 29];
const occupancyLabels = ["08h", "09h", "10h", "11h", "12h", "13h", "14h", "15h", "16h", "17h"];

function statusLabel(status: CameraStatus) {
  if (status === "online") return "Online";
  if (status === "offline") return "Indisponível";
  return "Aguardando agente";
}

function lastReading(camera: CameraState) {
  if (!camera.last_seen_at) return "Sem leitura";
  const elapsed = Math.max(0, Math.round((Date.now() - new Date(camera.last_seen_at).getTime()) / 1000));
  return elapsed < 2 ? "Agora" : `Há ${elapsed}s`;
}

function CameraPreview({ camera, large = false }: { camera: CameraState; large?: boolean }) {
  const [frameVersion, setFrameVersion] = useState(0);
  const [frameLoaded, setFrameLoaded] = useState(false);

  useEffect(() => {
    if (camera.status !== "online") return;
    const timer = window.setInterval(() => setFrameVersion(Date.now()), 350);
    return () => window.clearInterval(timer);
  }, [camera.status]);

  const showLiveFrame = camera.status === "online";
  const frameUrl = `http://127.0.0.1:8765/api/cameras/${camera.camera_id}/frame.jpg?v=${frameVersion}`;
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
        <strong>{camera.people_count}</strong>
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
        <div className="camera-title"><span className="device-icon">●</span><div><h3>{camera.name}</h3><p>{environmentLabel(camera.environment)} · {camera.source === "webcam" ? "Computador local" : "Rede local"}</p></div><span className={`small-online status-text-${camera.status}`}><i /> {statusLabel(camera.status)}</span></div>
        <div className="device-summary"><span><small>Pessoas agora</small><strong>{camera.people_count}</strong></span><span><small>Última leitura</small><strong>{lastReading(camera)}</strong></span><span><small>Origem</small><strong>{camera.source === "webcam" ? "Webcam" : "Celular"}</strong></span></div>
        <button className="primary-button" type="button" onClick={onOpen}>Abrir detalhes <span>→</span></button>
      </div>
    </article>
  );
}

export default function Home() {
  const [authReady, setAuthReady] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [active, setActive] = useState<Section>("overview");
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);
  const [selectedEnvironment, setSelectedEnvironment] = useState<string | null>(null);
  const [addCameraOpen, setAddCameraOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("todas");
  const [cameras, setCameras] = useState<CameraState[]>(waitingCameras);
  const [agentConnected, setAgentConnected] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setAuthUser(readLocalSession());
      setAuthReady(true);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!(["localhost", "127.0.0.1"].includes(window.location.hostname))) return;
    if (!authUser) return;
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
        if (activeRequest && !(error instanceof DOMException && error.name === "AbortError")) setAgentConnected(false);
      }
    };

    void refresh();
    const timer = window.setInterval(() => void refresh(), 2000);
    return () => {
      activeRequest = false;
      controller?.abort();
      window.clearInterval(timer);
    };
  }, [authUser]);

  const visibleCameras = useMemo(
    () => cameras.filter((camera) => {
      const matchesSearch = `${camera.name} ${camera.environment} ${camera.source}`.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = statusFilter === "todas" || camera.status === statusFilter;
      return matchesSearch && matchesStatus;
    }),
    [cameras, search, statusFilter],
  );
  const selectedCamera = cameras.find((camera) => camera.camera_id === selectedCameraId) ?? null;
  const selectedEnvironmentCameras = selectedEnvironment
    ? cameras.filter((camera) => camera.environment === selectedEnvironment)
    : [];

  const navigate = (section: Section) => {
    setActive(section);
    setSelectedCameraId(null);
    setSelectedEnvironment(null);
  };

  const handleLogin = (user: AuthUser) => {
    setAuthUser(user);
    setAuthReady(true);
  };

  const handleLogout = () => {
    clearLocalSession();
    setProfileOpen(false);
    setAuthUser(null);
    setActive("overview");
    setSelectedCameraId(null);
    setSelectedEnvironment(null);
    setCameras(waitingCameras);
    setAgentConnected(false);
  };

  if (!authReady || !authUser) return <LoginScreen onLogin={handleLogin} />;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <button className="brand" type="button" onClick={() => navigate("overview")}>
          <span className="brand-mark logo-slot" role="img" aria-label="Espaço reservado para a logo" />
          <span>Smart<br />Environment</span>
        </button>

        <nav aria-label="Navegação principal">
          <p className="nav-label">PLATAFORMA</p>
          {navigation.map((item) => (
            <button
              className={`nav-item ${active === item.key ? "active" : ""}`}
              key={item.key}
              type="button"
              onClick={() => navigate(item.key)}
              aria-current={active === item.key ? "page" : undefined}
            >
              <span className="nav-icon" aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
              {item.count && <span className="nav-count">{item.count}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <div className="system-health"><span /> Sistema operacional</div>
          <button className="profile" type="button" aria-label="Abrir perfil do administrador" aria-haspopup="dialog" aria-expanded={profileOpen} onClick={() => setProfileOpen((open) => !open)}>
            <span className="avatar">{userInitials(authUser.name)}</span>
            <span><strong>{authUser.name}</strong><small>{authUser.role}</small></span>
            <b aria-hidden="true">•••</b>
          </button>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{titles[active].eyebrow}</p>
            <h1>{selectedCamera ? selectedCamera.name : selectedEnvironment ? environmentLabel(selectedEnvironment) : titles[active].title}</h1>
          </div>
          <div className="top-actions">
            <span className={`simulation-pill ${agentConnected ? "connected" : ""}`}>{agentConnected ? "Agente local conectado" : "Aguardando agente local"}</span>
            <button className="icon-button" type="button" aria-label="Notificações" onClick={() => navigate("alerts")}>♢<i /></button>
            <button className="account-button" type="button" aria-label="Abrir perfil" aria-haspopup="dialog" aria-expanded={profileOpen} onClick={() => setProfileOpen((open) => !open)}>
              <span className="avatar">{userInitials(authUser.name)}</span>
            </button>
          </div>
        </header>

        <div className="content">
          {active === "overview" && (
            <Overview cameras={cameras} agentConnected={agentConnected} />
          )}

          {active === "cameras" && !selectedCamera && (
            <section className="page-stack">
              <div className="page-intro">
                <div><p className="eyebrow">DISPOSITIVOS CADASTRADOS</p><h2>Todas as câmeras</h2><span>Gerencie cada ponto de monitoramento em um só lugar.</span></div>
                <button className="primary-action" type="button" onClick={() => setAddCameraOpen(true)}>＋ Adicionar câmera</button>
              </div>
              <div className="filter-bar">
                <label className="search-field"><span aria-hidden="true">⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar câmera ou ambiente" aria-label="Buscar câmera ou ambiente" /></label>
                <label className="select-field"><span>Status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="todas">Todas</option><option value="online">Online</option><option value="offline">Offline</option></select></label>
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

          {active === "cameras" && selectedCamera && (
            <CameraDetails camera={selectedCamera} onBack={() => setSelectedCameraId(null)} />
          )}

          {active === "environments" && !selectedEnvironment && <Environments cameras={cameras} onOpenEnvironment={setSelectedEnvironment} />}
          {active === "environments" && selectedEnvironment && <EnvironmentDetails name={environmentLabel(selectedEnvironment)} cameras={selectedEnvironmentCameras} onBack={() => setSelectedEnvironment(null)} onOpenCamera={(cameraId) => { setActive("cameras"); setSelectedEnvironment(null); setSelectedCameraId(cameraId); }} />}
          {active === "indicators" && <Indicators />}
          {active === "alerts" && <Alerts />}
        </div>
      </section>

      {addCameraOpen && <AddCameraModal onClose={() => setAddCameraOpen(false)} />}
      {profileOpen && <ProfileModal user={authUser} onClose={() => setProfileOpen(false)} onLogout={handleLogout} />}
    </main>
  );
}

function Overview({ cameras, agentConnected }: { cameras: CameraState[]; agentConnected: boolean }) {
  const onlineCameras = cameras.filter((camera) => camera.status === "online").length;
  const peopleNow = cameras.reduce((total, camera) => total + camera.people_count, 0);
  const metrics = [
    { label: "Pessoas agora", value: String(peopleNow), change: agentConnected ? "Leitura agregada em tempo real" : "Aguardando câmeras", tone: "teal" },
    { label: "Câmeras online", value: `${onlineCameras}/${cameras.length}`, change: agentConnected ? "Agente local conectado" : "Inicie o monitor local", tone: "blue" },
    { label: "Ocupação hoje", value: "68%", change: "Média do período", tone: "lime" },
    { label: "Alertas ativos", value: "2", change: "Acompanhamento atual", tone: "orange" },
  ];

  return (
    <>
      <section className="welcome-card">
        <div><span className={`live-label ${agentConnected ? "" : "waiting"}`}><i /> {agentConnected ? "MONITORAMENTO LOCAL ATIVO" : "PRONTO PARA DUAS CÂMERAS"}</span><h2>Seu ambiente, em equilíbrio.</h2><p>{agentConnected ? "A câmera do computador e a câmera do celular estão sendo acompanhadas pelo agente local." : "Inicie o agente local para acompanhar a câmera do computador e a câmera do celular neste dashboard."}</p></div>
        <div className="welcome-visual" aria-hidden="true"><span className="pulse one" /><span className="pulse two" /><div className="building"><i /><i /><i /><i /><i /><i /></div></div>
      </section>
      <section className="metrics-grid" aria-label="Indicadores principais">
        {metrics.map((metric) => <article className="metric-card" key={metric.label}><span className={`metric-symbol ${metric.tone}`} aria-hidden="true" /><p>{metric.label}</p><strong>{metric.value}</strong><small>{metric.change}</small></article>)}
      </section>
      <section className="dashboard-grid">
        <article className="chart-card">
          <div className="card-heading"><div><p className="eyebrow">MOVIMENTO HOJE</p><h2>Ocupação por horário</h2></div><span className="trend-up">↗ 8%</span></div>
          <div className="bar-chart" aria-label="Ocupação por horário">{occupancyBars.map((bar, index) => <div className="bar-column" key={occupancyLabels[index]}><i style={{ height: `${bar}%` }} /><small>{occupancyLabels[index]}</small></div>)}</div>
        </article>
        <article className="activity-card"><p className="eyebrow">ÚLTIMOS EVENTOS</p><h2>Atividade recente</h2><div className="timeline"><div><i className="green" /><span><strong>Pessoa detectada</strong><small>Webcam principal · agora</small></span></div><div><i className="blue" /><span><strong>Câmera conectada</strong><small>DirectShow · há 12 min</small></span></div><div><i className="orange" /><span><strong>Período vazio</strong><small>Escritório · há 1h</small></span></div></div><button className="text-button wide" type="button">Ver histórico completo <span>→</span></button></article>
      </section>
    </>
  );
}

function CameraDetails({ camera, onBack }: { camera: CameraState; onBack: () => void }) {
  const healthy = camera.status === "online";
  return (
    <section className="page-stack">
      <button className="back-button" type="button" onClick={onBack}>← Voltar para câmeras</button>
      <div className="detail-grid"><CameraPreview camera={camera} large /><aside className="health-card"><p className="eyebrow">SAÚDE DO DISPOSITIVO</p><h2>{healthy ? "Operação normal" : statusLabel(camera.status)}</h2><div className="health-score"><strong>{healthy ? "98" : "--"}</strong><span>/ 100<small>Saúde geral</small></span></div><dl><div><dt>Conexão</dt><dd className={healthy ? "good" : ""}>{statusLabel(camera.status)}</dd></div><div><dt>Backend</dt><dd>{camera.backend ?? "Aguardando"}</dd></div><div><dt>Processamento</dt><dd>Intel/OpenVINO local</dd></div><div><dt>Latência</dt><dd>{camera.latency_ms === null ? "--" : `${camera.latency_ms.toFixed(1)} ms`}</dd></div></dl></aside></div>
      <div className="detail-lower"><article className="info-panel"><p className="eyebrow">CONFIGURAÇÃO</p><h2>Informações da câmera</h2><dl className="info-list"><div><dt>Nome</dt><dd>{camera.name}</dd></div><div><dt>Ambiente</dt><dd>{environmentLabel(camera.environment)}</dd></div><div><dt>Origem</dt><dd>{camera.source === "webcam" ? "Câmera integrada/USB" : "Celular na rede local"}</dd></div><div><dt>Privacidade</dt><dd>Frames transitórios</dd></div></dl><button className="secondary-button" type="button">Editar configurações</button></article><article className="info-panel"><p className="eyebrow">CONTAGEM ATUAL</p><h2>Detecção de pessoas</h2><div className="current-count"><strong>{camera.people_count}</strong><span>{camera.people_count === 1 ? "pessoa detectada" : "pessoas detectadas"}</span></div><div className="mini-legend"><span>{lastReading(camera)}</span><small>Modelo Intel YOLO26</small></div></article></div>
    </section>
  );
}

function Environments({ cameras, onOpenEnvironment }: { cameras: CameraState[]; onOpenEnvironment: (environment: string) => void }) {
  const environmentNames = Array.from(new Set(cameras.map((camera) => camera.environment)));

  return (
    <section className="page-stack">
      <div className="page-intro">
        <div><p className="eyebrow">LOCAIS MONITORADOS</p><h2>Ambientes</h2><span>Organize câmeras, ocupação e recursos por espaço físico.</span></div>
        <button className="primary-action" type="button">＋ Novo ambiente</button>
      </div>
      <div className="environment-grid">
        {environmentNames.map((environment) => {
          const environmentCameras = cameras.filter((camera) => camera.environment === environment);
          const onlineCameras = environmentCameras.filter((camera) => camera.status === "online").length;
          const peopleNow = environmentCameras.reduce((total, camera) => total + camera.people_count, 0);
          const status = onlineCameras === 0 ? "Aguardando" : onlineCameras === environmentCameras.length ? "Ativo" : "Parcial";
          return (
            <article className="environment-card featured" key={environment}>
              <div className="room-art"><span /><span /><i /></div>
              <div>
                <span className={`small-online environment-status-${status.toLowerCase()}`}><i /> {status}</span>
                <h3>{environmentLabel(environment)}</h3>
                <p>{environmentCameras.length} {environmentCameras.length === 1 ? "câmera configurada" : "câmeras configuradas"}</p>
                <div className="room-stats"><span><small>Pessoas agora</small><strong>{peopleNow}</strong></span><span><small>Câmeras online</small><strong>{onlineCameras}/{environmentCameras.length}</strong></span></div>
                <button className="secondary-button" type="button" aria-label={`Ver ambiente ${environmentLabel(environment)}`} onClick={() => onOpenEnvironment(environment)}>Ver ambiente</button>
              </div>
            </article>
          );
        })}
        {environmentNames.length === 0 && <div className="empty-state"><b>⌂</b><h3>Nenhum ambiente configurado</h3><p>Adicione uma câmera para começar a organizar os locais.</p></div>}
        <button className="add-environment" type="button"><span>＋</span><strong>Criar outro ambiente</strong><small>Salas, laboratórios ou áreas comuns</small></button>
      </div>
    </section>
  );
}

function EnvironmentDetails({ name, cameras, onBack, onOpenCamera }: { name: string; cameras: CameraState[]; onBack: () => void; onOpenCamera: (cameraId: string) => void }) {
  const onlineCameras = cameras.filter((camera) => camera.status === "online").length;
  const peopleNow = cameras.reduce((total, camera) => total + camera.people_count, 0);

  return (
    <section className="page-stack environment-detail" aria-labelledby="environment-detail-title">
      <button className="back-button" type="button" onClick={onBack}>← Voltar para ambientes</button>
      <div className="page-intro environment-detail-header">
        <div><p className="eyebrow">AMBIENTE MONITORADO</p><h2 id="environment-detail-title">{name}</h2><span>Todos os dispositivos associados a este ambiente.</span></div>
      </div>
      <div className="alert-summary environment-detail-summary">
        <span><strong>{cameras.length}</strong><small>{cameras.length === 1 ? "Câmera" : "Câmeras"}</small></span>
        <span><strong>{onlineCameras}/{cameras.length}</strong><small>Online</small></span>
        <span><strong>{peopleNow}</strong><small>{peopleNow === 1 ? "Pessoa agora" : "Pessoas agora"}</small></span>
      </div>
      <div className="section-heading environment-camera-heading"><div><p className="eyebrow">DISPOSITIVOS DO AMBIENTE</p><h2>Câmeras</h2><span>Visualize e abra cada ponto de monitoramento.</span></div></div>
      <div className="camera-grid environment-camera-grid">
        {cameras.map((camera) => <CameraDeviceCard key={camera.camera_id} camera={camera} onOpen={() => onOpenCamera(camera.camera_id)} />)}
        {cameras.length === 0 && <div className="empty-state"><b>⌂</b><h3>Nenhuma câmera neste ambiente</h3><p>Associe um dispositivo para acompanhar este local.</p></div>}
      </div>
    </section>
  );
}

function Indicators() {
  return <section className="page-stack"><div className="page-intro"><div><p className="eyebrow">ANÁLISE DO AMBIENTE</p><h2>Indicadores do ambiente</h2><span>Tendências de ocupação e oportunidades de uso consciente.</span></div><label className="period-select"><span>Período</span><select><option>Hoje</option><option>Últimos 7 dias</option><option>Últimos 30 dias</option></select></label></div><section className="metrics-grid indicators"><article className="metric-card"><p>Horas ocupadas</p><strong>6h 12m</strong><small>68% do período monitorado</small></article><article className="metric-card"><p>Tempo vazio</p><strong>2h 14m</strong><small>Oportunidade estimada</small></article><article className="metric-card"><p>Pico de presença</p><strong>2</strong><small>Entre 12h e 13h</small></article><article className="metric-card"><p>Câmera disponível</p><strong>99,2%</strong><small>Últimas 24 horas</small></article></section><div className="dashboard-grid indicators-grid"><article className="chart-card"><div className="card-heading"><div><p className="eyebrow">OCUPAÇÃO</p><h2>Distribuição do dia</h2></div><span className="chart-legend"><i /> Presença estimada</span></div><div className="bar-chart tall">{occupancyBars.map((bar, index) => <div className="bar-column" key={occupancyLabels[index]}><i style={{ height: `${bar}%` }} /><small>{occupancyLabels[index]}</small></div>)}</div></article><article className="recommendation-card"><span className="recommendation-icon">↯</span><p className="eyebrow">SUSTENTABILIDADE</p><h2>Oportunidade observada</h2><p>O escritório ficou vazio por aproximadamente 2h14 hoje. Esse indicador pode apoiar recomendações de iluminação e ventilação.</p><div className="notice">Indicador sujeito a revisão humana. Nenhum equipamento é controlado.</div></article></div></section>;
}

function Alerts() {
  return <section className="page-stack"><div className="page-intro"><div><p className="eyebrow">CENTRAL DE ATENÇÃO</p><h2>Alertas e eventos</h2><span>Situações que podem exigir acompanhamento humano.</span></div><button className="secondary-button" type="button">Configurar regras</button></div><div className="alert-summary"><span><strong>2</strong><small>Ativos</small></span><span><strong>1</strong><small>Requer atenção</small></span><span><strong>4</strong><small>Resolvidos hoje</small></span></div><div className="alerts-list"><article className="alert-row high"><span className="alert-symbol">!</span><div><span className="alert-tag">ATENÇÃO</span><h3>Ambiente ocupado fora do horário configurado</h3><p>Escritório principal · detectado há 8 minutos</p></div><button type="button">Revisar</button></article><article className="alert-row medium"><span className="alert-symbol">↯</span><div><span className="alert-tag">OPORTUNIDADE</span><h3>Iluminação pode estar ativa em ambiente vazio</h3><p>Eficiência energética · detectado há 42 minutos</p></div><button type="button">Revisar</button></article><article className="alert-row resolved"><span className="alert-symbol">✓</span><div><span className="alert-tag">RESOLVIDO</span><h3>Câmera voltou a responder normalmente</h3><p>Webcam principal · resolvido há 1 hora</p></div><button type="button">Detalhes</button></article></div><div className="alert-disclaimer"><strong>Decisão humana obrigatória</strong><p>Alertas são indícios para revisão. O sistema não declara culpa, produtividade ou ação disciplinar automaticamente.</p></div></section>;
}

function AddCameraModal({ onClose }: { onClose: () => void }) {
  return <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><button className="modal-close" type="button" onClick={onClose} aria-label="Fechar">×</button><p className="eyebrow">NOVO DISPOSITIVO</p><h2 id="modal-title">Adicionar câmera</h2><p className="modal-lead">Conecte a webcam deste computador ou o celular como câmera IP na mesma rede.</p><div className="connection-options"><button type="button"><span>◉</span><div><strong>Webcam deste computador</strong><small>USB ou câmera integrada</small></div><b>Disponível</b></button><button type="button"><span>⌁</span><div><strong>Câmera do celular</strong><small>MJPEG ou RTSP pela rede privada</small></div><b>Disponível</b></button><button type="button" disabled><span>▣</span><div><strong>Gateway ESP32</strong><small>Dispositivo remoto autenticado</small></div><b>Em breve</b></button></div><div className="modal-actions"><button className="secondary-button" type="button" onClick={onClose}>Cancelar</button><button className="primary-action" type="button" onClick={onClose}>Continuar</button></div></section></div>;
}
