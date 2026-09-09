/** WHEP video receiver. No camera permission, upload, recording or inference. */
export const DEFAULT_STREAM_URL = "http://127.0.0.1:8889/camera1/whep";

export function processingOrigin(value: string): string {
  const url = new URL(value);
  const local = ["localhost", "127.0.0.1"].includes(url.hostname);
  if ((url.protocol !== "https:" && !(local && url.protocol === "http:" && url.port === "8766")) ||
      url.username || url.password || url.search || url.hash || url.pathname !== "/") {
    throw new Error("Configure o endereço HTTPS do servidor, sem caminho ou credenciais.");
  }
  return url.origin;
}

export function serverStreamUrl(base: string, cameraId: string): string {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(cameraId)) throw new Error("Câmera inválida.");
  return `${processingOrigin(base)}/v1/cameras/${cameraId}/whep`;
}

export type ServerAuthorization = { baseUrl: string; token: () => Promise<string> };

export function validateStreamUrl(value: string, pageOrigin: string): string {
  const local = (host: string) => host === "localhost" || host === "127.0.0.1";
  let url: URL;
  let page: URL;
  try { url = new URL(value); page = new URL(pageOrigin); }
  catch { throw new Error("Informe um endereço WHEP válido."); }
  if (!local(page.hostname) || page.protocol !== "http:" || page.port !== "3000") {
    throw new Error("Abra o painel em http://localhost:3000 para usar a transmissão local.");
  }
  if (url.protocol !== "http:" || !local(url.hostname) || url.port !== "8889" ||
      url.username || url.password || url.search || url.hash ||
      !/^\/[a-zA-Z0-9_-]+\/whep$/.test(url.pathname)) {
    throw new Error("Use http://127.0.0.1:8889/nome-da-camera/whep, sem senha ou parâmetros. Acesso pela rede será configurado na próxima etapa.");
  }
  return url.href;
}

export function sessionUrl(endpoint: string, location: string | null): string {
  if (!location) throw new Error("O servidor não retornou a sessão WHEP.");
  const base = new URL(endpoint);
  const target = new URL(location, base);
  if (target.origin !== base.origin || target.username || target.password || target.search || target.hash ||
      !target.pathname.startsWith(`${base.pathname}/`) ||
      !/^[a-zA-Z0-9_-]+$/.test(target.pathname.slice(base.pathname.length + 1))) {
    throw new Error("O servidor retornou uma sessão inválida.");
  }
  return target.href;
}

function waitForIce(peer: RTCPeerConnection, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const finish = (error?: Error) => {
      peer.removeEventListener("icegatheringstatechange", check);
      signal.removeEventListener("abort", abort);
      if (error) reject(error); else resolve();
    };
    const check = () => { if (peer.iceGatheringState === "complete") finish(); };
    const abort = () => finish(new Error("A conexão foi cancelada ou excedeu o tempo limite."));
    peer.addEventListener("icegatheringstatechange", check);
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort(); else check();
  });
}

export class WhepReceiver {
  private peer: RTCPeerConnection;
  private request: typeof fetch;
  private controller = new AbortController();
  private location: string | null = null;
  private closed = false;
  private started = false;
  private authorization?: ServerAuthorization;

  constructor(options: {
    onTrack: (event: RTCTrackEvent) => void;
    onState: (state: RTCPeerConnectionState) => void;
    peerFactory?: () => RTCPeerConnection;
    request?: typeof fetch;
    authorization?: ServerAuthorization;
  }) {
    this.peer = options.peerFactory?.() ?? new RTCPeerConnection({ iceServers: [] });
    this.request = options.request ?? fetch;
    this.authorization = options.authorization;
    this.peer.ontrack = (event) => { if (!this.closed) options.onTrack(event); };
    this.peer.onconnectionstatechange = () => {
      if (!this.closed) options.onState(this.peer.connectionState);
    };
    this.peer.addTransceiver("video", { direction: "recvonly" });
  }

  async start(value: string, pageOrigin: string, timeoutMs = 12000): Promise<void> {
    if (this.started || this.closed) throw new Error("Crie uma nova conexão para tentar novamente.");
    this.started = true;
    const timer = setTimeout(() => this.controller.abort(), timeoutMs);
    try {
      let endpoint: string;
      if (this.authorization) {
        const match = new URL(value).pathname.match(/^\/v1\/cameras\/([0-9a-f-]{36})\/whep$/);
        if (!match || value !== serverStreamUrl(this.authorization.baseUrl, match[1])) throw new Error("Servidor de vídeo inválido.");
        endpoint = value;
      } else endpoint = validateStreamUrl(value, pageOrigin);
      const offer = await this.peer.createOffer();
      this.controller.signal.throwIfAborted();
      await this.peer.setLocalDescription(offer);
      await waitForIce(this.peer, this.controller.signal);
      const response = await this.request(endpoint, {
        method: "POST", headers: { "Content-Type": "application/sdp", ...await this.authHeaders() },
        body: this.peer.localDescription?.sdp,
        signal: this.controller.signal, credentials: "omit", redirect: "error", cache: "no-store",
      });
      if (response.status !== 201) {
        throw new Error(response.status === 404 ? "Nenhum transmissor ativo nesse endereço. Inicie a câmera e tente novamente." : "O servidor recusou a conexão de vídeo.");
      }
      this.location = sessionUrl(endpoint, response.headers.get("Location"));
      if (this.closed || this.controller.signal.aborted) throw new Error("Conexão cancelada.");
      if (!response.headers.get("Content-Type")?.toLowerCase().startsWith("application/sdp")) {
        throw new Error("O servidor não retornou uma resposta de vídeo válida.");
      }
      const answer = await response.text();
      this.controller.signal.throwIfAborted();
      if (answer.length > 128000 || !answer.startsWith("v=0")) throw new Error("Resposta de vídeo inválida.");
      await this.peer.setRemoteDescription({ type: "answer", sdp: answer });
    } catch (error) {
      this.close();
      throw error;
    } finally { clearTimeout(timer); }
  }

  getStats(): Promise<RTCStatsReport> { return this.peer.getStats(); }

  private async authHeaders(): Promise<Record<string, string>> {
    return this.authorization ? { Authorization: `Bearer ${await this.authorization.token()}` } : {};
  }

  async renew(): Promise<void> {
    if (!this.authorization || !this.location || this.closed) return;
    const response = await this.request(`${this.location}/keepalive`, {
      method: "POST", headers: await this.authHeaders(), credentials: "omit", redirect: "error",
      signal: AbortSignal.any([this.controller.signal, AbortSignal.timeout(8000)]), cache: "no-store",
    });
    if (!response.ok) { this.close(); throw new Error("A autorização de vídeo expirou. Entre novamente ou confira o servidor."); }
  }

  close(): void {
    this.closed = true;
    this.controller.abort();
    this.peer.ontrack = null;
    this.peer.onconnectionstatechange = null;
    this.peer.close();
    // Best effort, bounded cleanup, including a late POST response after cancellation.
    const location = this.location;
    this.location = null;
    if (location) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 2500);
      const remove = (headers: Record<string, string>) => this.request(location, {
        method: "DELETE", headers, signal: controller.signal, credentials: "omit", redirect: "error", keepalive: true,
      });
      const cleanup = this.authorization ? this.authHeaders().then(remove) : remove({});
      void cleanup.catch(() => undefined).finally(() => clearTimeout(timer));
    }
  }
}

export type VideoSample = {
  id: string; timestamp: number; framesDecoded?: number; bytesReceived?: number;
  frameWidth?: number; frameHeight?: number; jitterBufferDelay?: number; jitterBufferEmittedCount?: number;
};

export function videoSample(report: RTCStatsReport): VideoSample | null {
  let sample: VideoSample | null = null;
  report.forEach((entry) => {
    if (entry.type === "inbound-rtp" && (entry.kind === "video" || entry.mediaType === "video")) sample = entry;
  });
  return sample;
}

export function sampleMetrics(current: VideoSample, previous: VideoSample | null) {
  const valid = previous && current.id === previous.id && Number.isFinite(current.timestamp) && Number.isFinite(previous.timestamp) && current.timestamp > previous.timestamp;
  const seconds = valid ? (current.timestamp - previous.timestamp) / 1000 : 0;
  const delta = (key: keyof VideoSample): number | null => {
    const now = current[key]; const before = previous?.[key];
    return valid && typeof now === "number" && typeof before === "number" && Number.isFinite(now) && Number.isFinite(before) && now >= before ? now - before : null;
  };
  const frames = delta("framesDecoded");
  const bytes = delta("bytesReceived");
  const buffer = delta("jitterBufferDelay");
  const emitted = delta("jitterBufferEmittedCount");
  return {
    decodedFps: frames === null ? null : frames / seconds,
    mbps: bytes === null ? null : (bytes * 8) / seconds / 1_000_000,
    bufferMs: buffer === null || !emitted ? null : buffer * 1000 / emitted,
    resolution: current.frameWidth && current.frameHeight ? `${current.frameWidth} × ${current.frameHeight}` : null,
  };
}
