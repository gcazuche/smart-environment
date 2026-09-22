/** Receive-only video; credentials stay in Django. No capture, recording or storage. */
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
export const READING_TTL_MS = 2000;

export function streamEndpoint(cameraId) {
  if (!UUID.test(cameraId)) throw new Error("Câmera inválida.");
  return `/api/processing/cameras/${cameraId}/whep/`;
}

export function sessionPath(endpoint, location, origin) {
  if (!location) throw new Error("Sessão de vídeo ausente.");
  const base = new URL(endpoint, origin);
  const target = new URL(location, base);
  const suffix = target.pathname.slice(base.pathname.length);
  if (target.origin !== base.origin || target.username || target.password || target.search ||
      target.hash || !target.pathname.startsWith(base.pathname) ||
      !UUID.test(suffix.replace(/\/$/, "")) || !suffix.endsWith("/")) {
    throw new Error("Sessão de vídeo inválida.");
  }
  return target.pathname;
}

export function parseReadings(value) {
  const fail = () => { throw new Error("Telemetria inválida."); };
  if (!value || !Array.isArray(value.cameras) || value.cameras.length > 500) return fail();
  const ids = new Set();
  for (const item of value.cameras) {
    if (!item || !UUID.test(item.camera_id) || ids.has(item.camera_id)) return fail();
    ids.add(item.camera_id);
    if (!["online", "waiting"].includes(item.status) || typeof item.configured !== "boolean") return fail();
    if (item.people_count !== null && (!Number.isSafeInteger(item.people_count) || item.people_count < 0)) return fail();
    for (const key of ["latency_ms", "inference_fps"]) {
      if (item[key] !== null && (typeof item[key] !== "number" || !Number.isFinite(item[key]) || item[key] < 0)) return fail();
    }
    if (item.last_seen_at !== null && (typeof item.last_seen_at !== "string" || !Number.isFinite(Date.parse(item.last_seen_at)))) return fail();
    if (!Array.isArray(item.boxes) || item.boxes.length > 1000) return fail();
    for (const box of item.boxes) {
      if (!box || !["x", "y", "width", "height"].every(key =>
        typeof box[key] === "number" && Number.isFinite(box[key]) && box[key] >= 0 && box[key] <= 1) ||
        box.x + box.width > 1.000001 || box.y + box.height > 1.000001) return fail();
    }
  }
  return value.cameras;
}

export function freshReading(item, now = Date.now()) {
  const age = now - Date.parse(item?.last_seen_at ?? "");
  return item?.configured && item.status === "online" && Number.isFinite(age) &&
    age >= -5000 && age < READING_TTL_MS ? item : null;
}

/** One outstanding operation. Pausing aborts it; failure retries use bounded backoff. */
export function startPolling(options) {
  const schedule = options.schedule ?? setTimeout;
  const cancel = options.cancel ?? clearTimeout;
  let timer, controller, stopped = false, pendingWake = false, failures = 0;
  const clear = () => { if (timer !== undefined) cancel(timer); timer = undefined; };
  const run = async () => {
    if (stopped || controller || !options.canRun()) return;
    const current = new AbortController();
    controller = current;
    try {
      await options.task(current.signal);
      if (!current.signal.aborted) failures = 0;
    } catch (error) {
      if (!stopped && !current.signal.aborted) {
        failures = Math.min(failures + 1, 8);
        options.onError(error);
      }
    } finally {
      controller = undefined;
      if (!stopped && options.canRun()) {
        const delay = pendingWake ? 0 : Math.min(options.intervalMs * 2 ** failures, options.maxBackoffMs ?? 10000);
        pendingWake = false;
        timer = schedule(() => { timer = undefined; void run(); }, delay);
      }
    }
  };
  const wake = () => {
    if (stopped) return;
    clear();
    if (!options.canRun()) { pendingWake = false; controller?.abort(); return; }
    if (controller) { pendingWake = true; return; }
    failures = 0;
    void run();
  };
  wake();
  return { wake, stop: () => { stopped = true; clear(); controller?.abort(); } };
}

export class AccessError extends Error {}

const telemetryByDocument = new WeakMap();
/** All visible players share one telemetry request, not one request per camera. */
export function subscribeReadings(doc, request, local, onData, onError) {
  let services = telemetryByDocument.get(doc);
  if (!services) { services = new Map(); telemetryByDocument.set(doc, services); }
  const key = local ? "local" : "server";
  let service = services.get(key);
  if (!service) {
    service = { subscribers: new Set(), poller: null };
    services.set(key, service);
  }
  const subscriber = { onData, onError };
  service.subscribers.add(subscriber);
  if (!service.poller) {
    const active = service;
    active.poller = startPolling({ intervalMs: 1000,
      canRun: () => !doc.hidden && active.subscribers.size > 0,
      onError: error => { for (const item of [...active.subscribers]) item.onError(error); },
      task: async signal => {
        const response = await request(local ? "/api/processing/local-cameras/" : "/api/processing/cameras/", {
          credentials: "same-origin", redirect: "error", cache: "no-store",
          signal: AbortSignal.any([signal, AbortSignal.timeout(6000)]),
        });
        if ([401, 403].includes(response.status)) throw new AccessError("Acesso expirado. Entre novamente.");
        if (!response.ok) throw new Error("Telemetria indisponível.");
        const rows = parseReadings(await response.json());
        if (!signal.aborted) for (const item of [...active.subscribers]) item.onData(rows);
      },
    });
  }
  return { stop: () => {
    service.subscribers.delete(subscriber);
    if (!service.subscribers.size) { service.poller.stop(); services.delete(key); }
  } };
}

function waitForIce(peer, signal) {
  return new Promise((resolve, reject) => {
    const finish = error => {
      peer.removeEventListener("icegatheringstatechange", check);
      signal.removeEventListener("abort", abort);
      if (error) reject(error); else resolve();
    };
    const check = () => { if (peer.iceGatheringState === "complete") finish(); };
    const abort = () => finish(new Error("Conexão cancelada ou tempo limite excedido."));
    peer.addEventListener("icegatheringstatechange", check);
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort(); else check();
  });
}

export class WhepReceiver {
  constructor(options) {
    this.peer = options.peerFactory?.() ?? new RTCPeerConnection({ iceServers: [] });
    this.request = options.request ?? fetch;
    this.csrf = options.csrf;
    this.origin = options.origin;
    this.controller = new AbortController();
    this.location = null;
    this.started = false;
    this.closed = false;
    this.peer.ontrack = event => { if (!this.closed) options.onTrack(event); };
    this.peer.onconnectionstatechange = () => { if (!this.closed) options.onState(this.peer.connectionState); };
    this.peer.addTransceiver("video", { direction: "recvonly" });
  }
  async start(cameraId, timeoutMs = 12000) {
    if (this.started || this.closed) throw new Error("Crie uma nova conexão para tentar novamente.");
    if (!this.csrf) throw new Error("Recarregue a página para renovar a proteção de acesso.");
    this.started = true;
    const timer = setTimeout(() => this.controller.abort(), timeoutMs);
    try {
      const endpoint = streamEndpoint(cameraId);
      const offer = await this.peer.createOffer();
      this.controller.signal.throwIfAborted();
      await this.peer.setLocalDescription(offer);
      await waitForIce(this.peer, this.controller.signal);
      const response = await this.request(endpoint, {
        method: "POST", headers: { "Content-Type": "application/sdp", "X-CSRFToken": this.csrf },
        body: this.peer.localDescription?.sdp, signal: this.controller.signal,
        credentials: "same-origin", redirect: "error", cache: "no-store",
      });
      if ([401, 403].includes(response.status)) throw new AccessError("Acesso expirado. Entre novamente.");
      if (response.status !== 201) throw new Error(response.status === 404 ?
        "Câmera sem transmissão ativa. Confira o publicador e o vínculo na VM." :
        "Não foi possível conectar. Confira a configuração do servidor.");
      // Register Location even after cancellation so the late session is revoked.
      this.location = sessionPath(endpoint, response.headers.get("Location"), this.origin);
      this.controller.signal.throwIfAborted();
      if (!response.headers.get("Content-Type")?.toLowerCase().startsWith("application/sdp")) throw new Error("Resposta de vídeo inválida.");
      const answer = await response.text();
      if (answer.length > 131072 || !answer.startsWith("v=0")) throw new Error("Resposta de vídeo inválida.");
      this.controller.signal.throwIfAborted();
      await this.peer.setRemoteDescription({ type: "answer", sdp: answer });
    } catch (error) {
      this.close();
      throw error;
    } finally { clearTimeout(timer); }
  }
  async renew() {
    if (!this.location || this.closed) return;
    const response = await this.request(`${this.location}keepalive/`, {
      method: "POST", headers: { "X-CSRFToken": this.csrf }, credentials: "same-origin",
      redirect: "error", cache: "no-store",
      signal: AbortSignal.any([this.controller.signal, AbortSignal.timeout(8000)]),
    });
    if (!response.ok) {
      this.close();
      if ([401, 403].includes(response.status)) throw new AccessError("Acesso expirado. Entre novamente.");
      throw new Error("A autorização do vídeo expirou. Conecte novamente.");
    }
  }
  getStats() { return this.peer.getStats(); }
  close() {
    this.closed = true;
    this.controller.abort();
    this.peer.ontrack = null;
    this.peer.onconnectionstatechange = null;
    this.peer.close();
    const location = this.location;
    this.location = null;
    if (location) {
      void this.request(location, {
        method: "DELETE", headers: { "X-CSRFToken": this.csrf }, credentials: "same-origin",
        redirect: "error", cache: "no-store", keepalive: true, signal: AbortSignal.timeout(2500),
      }).catch(() => undefined);
    }
  }
}

export function videoSample(report) {
  let sample = null;
  report.forEach(entry => {
    if (entry.type === "inbound-rtp" && (entry.kind === "video" || entry.mediaType === "video")) sample = entry;
  });
  return sample;
}

export function sampleMetrics(current, previous) {
  const valid = previous && current.id === previous.id && Number.isFinite(current.timestamp) &&
    Number.isFinite(previous.timestamp) && current.timestamp > previous.timestamp;
  const seconds = valid ? (current.timestamp - previous.timestamp) / 1000 : 0;
  const delta = key => valid && Number.isFinite(current[key]) && Number.isFinite(previous[key]) &&
    current[key] >= previous[key] ? current[key] - previous[key] : null;
  const frames = delta("framesDecoded"), bytes = delta("bytesReceived");
  return { decodedFps: frames === null ? null : frames / seconds,
    mbps: bytes === null ? null : bytes * 8 / seconds / 1000000 };
}

function renderBoxes(video, canvas, reading) {
  const context = canvas?.getContext("2d");
  if (!context) return;
  canvas.width = Math.max(1, Math.round(video.clientWidth));
  canvas.height = Math.max(1, Math.round(video.clientHeight));
  context.clearRect(0, 0, canvas.width, canvas.height);
  if (!reading || !video.videoWidth || !video.videoHeight) return;
  const scale = Math.min(canvas.width / video.videoWidth, canvas.height / video.videoHeight);
  const width = video.videoWidth * scale, height = video.videoHeight * scale;
  const left = (canvas.width - width) / 2, top = (canvas.height - height) / 2;
  context.strokeStyle = "#b8db75";
  context.lineWidth = 2;
  for (const box of reading.boxes) context.strokeRect(left + box.x * width, top + box.y * height, box.width * width, box.height * height);
}

export function mountVideo(root, options = {}) {
  const doc = root.ownerDocument;
  const win = doc.defaultView;
  const video = root.querySelector("[data-video]");
  const localImage = root.querySelector("[data-local-frame]");
  const canvas = root.querySelector("[data-video-overlay]");
  const startButton = root.querySelector("[data-video-start]");
  const stopButton = root.querySelector("[data-video-stop]");
  if (!video || !startButton || !stopButton) return null;
  const enabled = !startButton.disabled;
  const request = options.request ?? win.fetch.bind(win);
  const set = (selector, text) => { const element = root.querySelector(selector); if (element) element.textContent = text; };
  let receiver = null, poller = null, renewer = null, stats = null, expiry, reading = null, previous = null, generation = 0, localUrl = null;
  const clearLocal = () => {
    if (localImage) { localImage.hidden = true; localImage.removeAttribute("src"); }
    if (localUrl) { win.URL.revokeObjectURL(localUrl); localUrl = null; }
    if (root.dataset.videoMode === "local") root.dataset.state = "stopped";
  };
  const unknown = () => {
    clearTimeout(expiry); reading = null;
    if (root.dataset.videoMode === "local") clearLocal();
    set("[data-people-count]", "Desconhecido"); set("[data-analysis-fps]", "—");
    renderBoxes(video, canvas, null);
  };
  const stop = (message = "Transmissão parada.") => {
    generation += 1;
    receiver?.close(); receiver = null;
    poller?.stop(); renewer?.stop(); stats?.stop(); poller = renewer = stats = null;
    video.srcObject?.getTracks().forEach(track => track.stop());
    video.srcObject = null; previous = null; unknown();
    clearLocal(); video.hidden = false;
    set("[data-video-status]", message); set("[data-video-fps]", "—");
    set("[data-analysis-status]", "Sem análise recente.");
    root.dataset.state = "stopped";
    startButton.disabled = !enabled; stopButton.disabled = true;
  };
  const onError = error => {
    unknown();
    if (error instanceof AccessError) stop(error.message);
    else set("[data-analysis-status]", "Análise indisponível; o vídeo usa uma conexão independente.");
  };
  const start = async () => {
    if (!enabled) return;
    stop("Conectando…");
    const current = generation;
    startButton.disabled = true; stopButton.disabled = false;
    if (root.dataset.videoMode === "local") {
      if (!localImage) { stop("Prévia local indisponível nesta página."); return; }
      video.hidden = true;
      set("[data-video-status]", "Conectando ao monitor local…");
      poller = startPolling({ intervalMs: 500, canRun: () => !doc.hidden && generation === current,
        onError: error => { clearLocal(); onError(error); set("[data-video-status]", "Monitor local indisponível."); },
        task: async signal => {
          const id = root.dataset.cameraId;
          if (!UUID.test(id)) throw new Error("Câmera inválida.");
          const response = await request(`/api/processing/cameras/${id}/local-frame/`, {
            credentials: "same-origin", redirect: "error", cache: "no-store",
            signal: AbortSignal.any([signal, AbortSignal.timeout(6000)]),
          });
          if ([401, 403].includes(response.status)) throw new AccessError("Acesso expirado. Entre novamente.");
          if (!response.ok) throw new Error("Prévia local indisponível.");
          const blob = await response.blob();
          if (blob.size > 2000000 || blob.type !== "image/jpeg") throw new Error("Prévia local inválida.");
          const url = win.URL.createObjectURL(blob);
          let transferred = false;
          try {
            const decoded = new win.Image(); decoded.src = url; await decoded.decode();
            if (signal.aborted || current !== generation) return;
            clearLocal(); localUrl = url; localImage.src = url; localImage.hidden = false;
            root.dataset.state = "playing";
            transferred = true;
            set("[data-video-status]", "Prévia JPEG local; frequência limitada, não é vídeo de 30 FPS.");
          } finally { if (!transferred) win.URL.revokeObjectURL(url); }
        } });
      stats = subscribeReadings(doc, request, true, rows => {
          const camera = rows.find(item => item.camera_id === root.dataset.cameraId);
          if (current !== generation) return;
          reading = freshReading(camera);
          clearTimeout(expiry);
          if (!reading) { unknown(); return; }
          set("[data-people-count]", String(reading.people_count ?? "Desconhecido"));
          set("[data-analysis-status]", "Caixas incorporadas à prévia pelo monitor local; presença não comprova trabalho.");
          expiry = setTimeout(unknown, Math.max(1, Date.parse(reading.last_seen_at) + READING_TTL_MS - Date.now()));
        }, onError);
      return;
    }
    const csrf = doc.querySelector("input[name=csrfmiddlewaretoken]")?.value ?? doc.querySelector("meta[name=csrf-token]")?.content;
    try {
      const active = new WhepReceiver({ request, csrf, origin: win.location.origin,
        peerFactory: options.peerFactory,
        onTrack: event => {
          if (current !== generation) return;
          video.srcObject = event.streams[0] ?? new win.MediaStream([event.track]);
          root.dataset.state = "playing";
          void video.play().catch(() => set("[data-video-status]", "Use os controles do vídeo para iniciar."));
        },
        onState: state => {
          if (current !== generation) return;
          if (["failed", "closed"].includes(state)) stop("Conexão encerrada. Conecte novamente.");
          else set("[data-video-status]", state === "connected" ? "Vídeo conectado." : "Conectando…");
        },
      });
      receiver = active;
      await active.start(root.dataset.cameraId);
      if (current !== generation) { active.close(); return; }
      poller = subscribeReadings(doc, request, false, incoming => {
          if (receiver !== active) return;
          const camera = incoming.find(item => item.camera_id === root.dataset.cameraId);
          reading = freshReading(camera);
          clearTimeout(expiry);
          if (!reading) { unknown(); set("[data-analysis-status]", "Sem análise recente; situação desconhecida."); return; }
          set("[data-people-count]", String(reading.people_count ?? "Desconhecido"));
          set("[data-analysis-fps]", reading.inference_fps?.toFixed(1) ?? "—");
          set("[data-analysis-status]", "Caixas aproximadas recentes, sem sincronização exata com o vídeo.");
          renderBoxes(video, canvas, reading);
          expiry = setTimeout(() => { unknown(); set("[data-analysis-status]", "Leitura expirada; situação desconhecida."); },
            Math.max(1, Date.parse(reading.last_seen_at) + READING_TTL_MS - Date.now()));
        }, onError);
      renewer = startPolling({ intervalMs: 15000, canRun: () => !doc.hidden && receiver === active,
        onError: () => stop("Autorização do vídeo indisponível. Conecte novamente."), task: () => active.renew() });
      stats = startPolling({ intervalMs: 1500, canRun: () => !doc.hidden && receiver === active,
        onError: () => set("[data-video-fps]", "—"), task: async () => {
          const sample = videoSample(await active.getStats());
          if (receiver !== active || !sample) return;
          const metrics = sampleMetrics(sample, previous); previous = sample;
          set("[data-video-fps]", metrics.decodedFps?.toFixed(1) ?? "—");
        } });
    } catch (error) {
      if (current === generation) stop(error instanceof Error ? error.message : "Falha ao conectar.");
    }
  };
  const visibility = () => {
    // Stop explicitly: no unattended playback or keepalive while hidden.
    if (doc.hidden) stop("Transmissão pausada com a aba oculta. Conecte para retomar.");
  };
  const resize = () => renderBoxes(video, canvas, freshReading(reading));
  const manualStop = () => stop();
  startButton.addEventListener("click", start); stopButton.addEventListener("click", manualStop);
  doc.addEventListener("visibilitychange", visibility); win.addEventListener("pagehide", manualStop);
  win.addEventListener("resize", resize); video.addEventListener("loadedmetadata", resize);
  stop(enabled ? "Pronto para conectar. Nenhuma câmera é aberta automaticamente." : "Câmera desabilitada no cadastro.");
  return { start, stop, destroy: () => {
    stop(); startButton.removeEventListener("click", start); stopButton.removeEventListener("click", manualStop);
    doc.removeEventListener("visibilitychange", visibility); win.removeEventListener("pagehide", manualStop);
    win.removeEventListener("resize", resize); video.removeEventListener("loadedmetadata", resize);
  } };
}

if (typeof document !== "undefined") {
  document.querySelectorAll(".camera-viewer[data-camera-id]").forEach(root => mountVideo(root));
}
