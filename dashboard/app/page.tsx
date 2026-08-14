"use client";

import { useMemo, useState } from "react";

type Section = "overview" | "cameras" | "environments" | "indicators" | "alerts";

const navigation: Array<{ key: Section; icon: string; label: string; count?: string }> = [
  { key: "overview", icon: "⌂", label: "Visão geral" },
  { key: "cameras", icon: "▦", label: "Câmeras", count: "1" },
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

const metrics = [
  { label: "Pessoas agora", value: "1", change: "Escritório principal", tone: "teal" },
  { label: "Câmeras online", value: "1/1", change: "Todos os dispositivos ativos", tone: "blue" },
  { label: "Ocupação hoje", value: "68%", change: "+8% comparado à média", tone: "lime" },
  { label: "Alertas ativos", value: "2", change: "1 requer atenção", tone: "orange" },
];

const occupancyBars = [38, 52, 45, 66, 81, 74, 68, 58, 43, 29];
const occupancyLabels = ["08h", "09h", "10h", "11h", "12h", "13h", "14h", "15h", "16h", "17h"];

function SimulatedPreview({ large = false }: { large?: boolean }) {
  return (
    <div className={`camera-preview ${large ? "large" : ""}`}>
      <span className="online-badge"><i /> SIMULAÇÃO</span>
      <div className="camera-frame" aria-hidden="true">
        <span className="corner tl" /><span className="corner tr" />
        <span className="corner bl" /><span className="corner br" />
        <div className="person-shape"><i /><b /></div>
        <span className="detection-label">Pessoa · 72%</span>
      </div>
      <span className="preview-note">Prévia ilustrativa — nenhum frame armazenado</span>
    </div>
  );
}

export default function Home() {
  const [active, setActive] = useState<Section>("overview");
  const [cameraOpen, setCameraOpen] = useState(false);
  const [addCameraOpen, setAddCameraOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("todas");

  const cameraVisible = useMemo(
    () => "webcam principal escritório computador local".includes(search.toLowerCase()) && statusFilter !== "offline",
    [search, statusFilter],
  );

  const navigate = (section: Section) => {
    setActive(section);
    setCameraOpen(false);
  };

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <button className="brand" type="button" onClick={() => navigate("overview")}>
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
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
          <button className="profile" type="button" aria-label="Abrir perfil do administrador">
            <span className="avatar">AD</span>
            <span><strong>Administrador</strong><small>Conta de demonstração</small></span>
            <b aria-hidden="true">•••</b>
          </button>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{titles[active].eyebrow}</p>
            <h1>{cameraOpen ? "Webcam principal" : titles[active].title}</h1>
          </div>
          <div className="top-actions">
            <span className="simulation-pill">Dados simulados</span>
            <button className="icon-button" type="button" aria-label="Notificações" onClick={() => navigate("alerts")}>♢<i /></button>
          </div>
        </header>

        <div className="content">
          {active === "overview" && (
            <Overview onCameras={() => navigate("cameras")} onOpenCamera={() => { setActive("cameras"); setCameraOpen(true); }} />
          )}

          {active === "cameras" && !cameraOpen && (
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
                {cameraVisible ? (
                  <article className="device-card">
                    <SimulatedPreview />
                    <div className="device-card-body">
                      <div className="camera-title"><span className="device-icon">●</span><div><h3>Webcam principal</h3><p>Escritório · Computador local</p></div><span className="small-online"><i /> Online</span></div>
                      <div className="device-summary"><span><small>Pessoas agora</small><strong>1</strong></span><span><small>Última leitura</small><strong>Há 12s</strong></span><span><small>Origem</small><strong>Webcam</strong></span></div>
                      <button className="primary-button" type="button" onClick={() => setCameraOpen(true)}>Abrir detalhes <span>→</span></button>
                    </div>
                  </article>
                ) : (
                  <div className="empty-state"><b>⌕</b><h3>Nenhuma câmera encontrada</h3><p>Ajuste a busca ou o filtro selecionado.</p></div>
                )}
                <button className="add-device-card" type="button" onClick={() => setAddCameraOpen(true)}><span>＋</span><strong>Adicionar outra câmera</strong><small>Webcam, câmera IP ou gateway ESP32</small></button>
              </div>
            </section>
          )}

          {active === "cameras" && cameraOpen && (
            <CameraDetails onBack={() => setCameraOpen(false)} />
          )}

          {active === "environments" && <Environments />}
          {active === "indicators" && <Indicators />}
          {active === "alerts" && <Alerts />}
        </div>
      </section>

      {addCameraOpen && <AddCameraModal onClose={() => setAddCameraOpen(false)} />}
    </main>
  );
}

function Overview({ onCameras, onOpenCamera }: { onCameras: () => void; onOpenCamera: () => void }) {
  return (
    <>
      <section className="welcome-card">
        <div><span className="live-label"><i /> MONITORAMENTO ATIVO</span><h2>Seu ambiente, em equilíbrio.</h2><p>A webcam principal está online. Todos os valores desta primeira interface são demonstrações até a integração com dados reais.</p></div>
        <div className="welcome-visual" aria-hidden="true"><span className="pulse one" /><span className="pulse two" /><div className="building"><i /><i /><i /><i /><i /><i /></div></div>
      </section>
      <section className="metrics-grid" aria-label="Indicadores principais">
        {metrics.map((metric) => <article className="metric-card" key={metric.label}><span className={`metric-symbol ${metric.tone}`} aria-hidden="true" /><p>{metric.label}</p><strong>{metric.value}</strong><small>{metric.change}</small></article>)}
      </section>
      <section className="dashboard-grid">
        <article className="chart-card">
          <div className="card-heading"><div><p className="eyebrow">MOVIMENTO HOJE</p><h2>Ocupação por horário</h2></div><span className="trend-up">↗ 8%</span></div>
          <div className="bar-chart" aria-label="Gráfico simulado de ocupação por horário">{occupancyBars.map((bar, index) => <div className="bar-column" key={occupancyLabels[index]}><i style={{ height: `${bar}%` }} /><small>{occupancyLabels[index]}</small></div>)}</div>
        </article>
        <article className="activity-card"><p className="eyebrow">ÚLTIMOS EVENTOS</p><h2>Atividade recente</h2><div className="timeline"><div><i className="green" /><span><strong>Pessoa detectada</strong><small>Webcam principal · agora</small></span></div><div><i className="blue" /><span><strong>Câmera conectada</strong><small>DirectShow · há 12 min</small></span></div><div><i className="orange" /><span><strong>Período vazio</strong><small>Escritório · há 1h</small></span></div></div><button className="text-button wide" type="button">Ver histórico completo <span>→</span></button></article>
      </section>
      <section className="cameras-section">
        <div className="section-heading"><div><p className="eyebrow">DISPOSITIVOS</p><h2>Suas câmeras</h2><span>Todos os pontos de monitoramento em um só lugar.</span></div><button className="text-button" type="button" onClick={onCameras}>Ver todas <span>→</span></button></div>
        <article className="camera-card"><SimulatedPreview /><div className="camera-info"><div className="camera-title"><span className="device-icon">●</span><div><h3>Webcam principal</h3><p>Escritório · Computador local</p></div><button type="button" aria-label="Mais opções da câmera">•••</button></div><div className="camera-stats"><div><span>Status</span><strong className="status-online"><i /> Online</strong></div><div><span>Pessoas</span><strong>1 detectada</strong></div><div><span>Atualização</span><strong>Há 12 segundos</strong></div></div><button className="primary-button" type="button" onClick={onOpenCamera}>Abrir câmera <span>↗</span></button></div></article>
      </section>
    </>
  );
}

function CameraDetails({ onBack }: { onBack: () => void }) {
  return (
    <section className="page-stack">
      <button className="back-button" type="button" onClick={onBack}>← Voltar para câmeras</button>
      <div className="detail-grid"><SimulatedPreview large /><aside className="health-card"><p className="eyebrow">SAÚDE DO DISPOSITIVO</p><h2>Operação normal</h2><div className="health-score"><strong>98</strong><span>/ 100<small>Saúde geral</small></span></div><dl><div><dt>Conexão</dt><dd className="good">Estável</dd></div><div><dt>Backend</dt><dd>DirectShow</dd></div><div><dt>Processamento</dt><dd>Local</dd></div><div><dt>Última leitura</dt><dd>Há 12s</dd></div></dl></aside></div>
      <div className="detail-lower"><article className="info-panel"><p className="eyebrow">CONFIGURAÇÃO</p><h2>Informações da câmera</h2><dl className="info-list"><div><dt>Nome</dt><dd>Webcam principal</dd></div><div><dt>Ambiente</dt><dd>Escritório</dd></div><div><dt>Origem</dt><dd>Câmera integrada</dd></div><div><dt>Privacidade</dt><dd>Frames transitórios</dd></div></dl><button className="secondary-button" type="button">Editar configurações</button></article><article className="info-panel"><p className="eyebrow">CONTAGEM SIMULADA</p><h2>Últimos 60 minutos</h2><div className="mini-chart">{[24,36,48,42,68,62,75,58,70,46,55,64].map((value, index) => <i key={index} style={{ height: `${value}%` }} />)}</div><div className="mini-legend"><span>1 pessoa agora</span><small>Máximo: 2</small></div></article></div>
    </section>
  );
}

function Environments() {
  return <section className="page-stack"><div className="page-intro"><div><p className="eyebrow">LOCAIS MONITORADOS</p><h2>Ambientes</h2><span>Organize câmeras, ocupação e recursos por espaço físico.</span></div><button className="primary-action" type="button">＋ Novo ambiente</button></div><div className="environment-grid"><article className="environment-card featured"><div className="room-art"><span /><span /><i /></div><div><span className="small-online"><i /> Ocupado</span><h3>Escritório principal</h3><p>1 câmera · 1 pessoa agora</p><div className="room-stats"><span><small>Ocupação hoje</small><strong>68%</strong></span><span><small>Tempo vazio</small><strong>2h 14m</strong></span></div><button className="secondary-button" type="button">Ver ambiente</button></div></article><button className="add-environment" type="button"><span>＋</span><strong>Criar outro ambiente</strong><small>Salas, laboratórios ou áreas comuns</small></button></div></section>;
}

function Indicators() {
  return <section className="page-stack"><div className="page-intro"><div><p className="eyebrow">DADOS SIMULADOS</p><h2>Indicadores do ambiente</h2><span>Tendências de ocupação e oportunidades de uso consciente.</span></div><label className="period-select"><span>Período</span><select><option>Hoje</option><option>Últimos 7 dias</option><option>Últimos 30 dias</option></select></label></div><section className="metrics-grid indicators"><article className="metric-card"><p>Horas ocupadas</p><strong>6h 12m</strong><small>68% do período monitorado</small></article><article className="metric-card"><p>Tempo vazio</p><strong>2h 14m</strong><small>Oportunidade estimada</small></article><article className="metric-card"><p>Pico de presença</p><strong>2</strong><small>Entre 12h e 13h</small></article><article className="metric-card"><p>Câmera disponível</p><strong>99,2%</strong><small>Últimas 24 horas</small></article></section><div className="dashboard-grid indicators-grid"><article className="chart-card"><div className="card-heading"><div><p className="eyebrow">OCUPAÇÃO</p><h2>Distribuição do dia</h2></div><span className="chart-legend"><i /> Presença estimada</span></div><div className="bar-chart tall">{occupancyBars.map((bar, index) => <div className="bar-column" key={occupancyLabels[index]}><i style={{ height: `${bar}%` }} /><small>{occupancyLabels[index]}</small></div>)}</div></article><article className="recommendation-card"><span className="recommendation-icon">↯</span><p className="eyebrow">SUSTENTABILIDADE</p><h2>Oportunidade observada</h2><p>O escritório ficou vazio por aproximadamente 2h14 hoje. No futuro, esse indicador poderá apoiar recomendações de iluminação e ventilação.</p><div className="notice">Estimativa demonstrativa. Nenhum equipamento é controlado.</div></article></div></section>;
}

function Alerts() {
  return <section className="page-stack"><div className="page-intro"><div><p className="eyebrow">CENTRAL DE ATENÇÃO</p><h2>Alertas e eventos</h2><span>Situações simuladas que podem exigir acompanhamento humano.</span></div><button className="secondary-button" type="button">Configurar regras</button></div><div className="alert-summary"><span><strong>2</strong><small>Ativos</small></span><span><strong>1</strong><small>Requer atenção</small></span><span><strong>4</strong><small>Resolvidos hoje</small></span></div><div className="alerts-list"><article className="alert-row high"><span className="alert-symbol">!</span><div><span className="alert-tag">ATENÇÃO</span><h3>Ambiente ocupado fora do horário configurado</h3><p>Escritório principal · detectado há 8 minutos</p></div><button type="button">Revisar</button></article><article className="alert-row medium"><span className="alert-symbol">↯</span><div><span className="alert-tag">OPORTUNIDADE</span><h3>Iluminação pode estar ativa em ambiente vazio</h3><p>Recomendação simulada · detectado há 42 minutos</p></div><button type="button">Revisar</button></article><article className="alert-row resolved"><span className="alert-symbol">✓</span><div><span className="alert-tag">RESOLVIDO</span><h3>Câmera voltou a responder normalmente</h3><p>Webcam principal · resolvido há 1 hora</p></div><button type="button">Detalhes</button></article></div><div className="alert-disclaimer"><strong>Decisão humana obrigatória</strong><p>Alertas são indícios para revisão. O sistema não declara culpa, produtividade ou ação disciplinar automaticamente.</p></div></section>;
}

function AddCameraModal({ onClose }: { onClose: () => void }) {
  return <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><button className="modal-close" type="button" onClick={onClose} aria-label="Fechar">×</button><p className="eyebrow">NOVO DISPOSITIVO</p><h2 id="modal-title">Adicionar câmera</h2><p className="modal-lead">Escolha como esta câmera será conectada futuramente.</p><div className="connection-options"><button type="button"><span>◉</span><div><strong>Webcam deste computador</strong><small>USB ou câmera integrada</small></div><b>Disponível</b></button><button type="button" disabled><span>⌁</span><div><strong>Câmera IP</strong><small>RTSP ou integração pela rede</small></div><b>Em breve</b></button><button type="button" disabled><span>▣</span><div><strong>Gateway ESP32</strong><small>Dispositivo remoto autenticado</small></div><b>Em breve</b></button></div><div className="modal-actions"><button className="secondary-button" type="button" onClick={onClose}>Cancelar</button><button className="primary-action" type="button" onClick={onClose}>Continuar</button></div></section></div>;
}
