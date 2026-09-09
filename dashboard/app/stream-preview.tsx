"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { DEFAULT_STREAM_URL, WhepReceiver, sampleMetrics, validateStreamUrl, videoSample, type VideoSample, type ServerAuthorization } from "./stream-client";
import type { ServerReading } from "./processing-server";

type Status = "idle" | "connecting" | "playing" | "stalled" | "error";
const labels: Record<Status, string> = {
  idle: "Desconectado", connecting: "Conectando", playing: "Ao vivo", stalled: "Sem quadros recentes", error: "Conexão indisponível",
};
type Metrics = ReturnType<typeof sampleMetrics> & { presentedFps: number | null };
const emptyMetrics: Metrics = { decodedFps: null, presentedFps: null, mbps: null, bufferMs: null, resolution: null };
const format = (value: number | null, digits = 1) => value === null ? "—" : value.toLocaleString("pt-BR", { maximumFractionDigits: digits });

export function StreamPreview({ remote }: { remote?: { authorization: ServerAuthorization; endpoint: string; camera: ServerReading } }) {
  const [url, setUrl] = useState(DEFAULT_STREAM_URL);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");
  const [metrics, setMetrics] = useState<Metrics>(emptyMetrics);
  const [needsPlay, setNeedsPlay] = useState(false);
  const video = useRef<HTMLVideoElement>(null);
  const dispose = useRef<(() => void) | null>(null);

  useEffect(() => () => { dispose.current?.(); }, []);

  const disconnect = () => {
    dispose.current?.(); dispose.current = null;
    setStatus("idle"); setError(""); setMetrics(emptyMetrics); setNeedsPlay(false);
  };

  const connect = async (event: FormEvent) => {
    event.preventDefault();
    disconnect();
    try { if (!remote) validateStreamUrl(url, window.location.origin); }
    catch (reason) { setError((reason as Error).message); setStatus("error"); return; }
    if (!window.RTCPeerConnection) { setError("Este navegador não oferece WebRTC."); setStatus("error"); return; }
    const element = video.current;
    if (!element) return;
    setStatus("connecting");
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let renewTimer: ReturnType<typeof setTimeout> | undefined;
    let frameCallback: number | undefined;
    let previous: VideoSample | null = null;
    let presented = 0;
    let previousPresented = 0;
    let presentationStarted = false;
    let receivedFrame = false;
    let previousTime = performance.now();
    let lastFrame = previousTime;
    const countFrames = (_now: number, metadata: VideoFrameCallbackMetadata) => {
      if (!active) return;
      if (!presentationStarted) { previousPresented = metadata.presentedFrames; presentationStarted = true; }
      presented = metadata.presentedFrames;
      lastFrame = performance.now();
      receivedFrame = true;
      clearTimeout(firstFrameTimeout);
      frameCallback = element.requestVideoFrameCallback(countFrames);
    };
    const finish = (message: string) => {
      if (!active) return;
      dispose.current?.(); dispose.current = null;
      setMetrics(emptyMetrics); setStatus("error"); setError(message); setNeedsPlay(false);
    };
    const receiver = new WhepReceiver({
      authorization: remote?.authorization,
      onTrack: (event) => {
        element.srcObject = event.streams[0] ?? new MediaStream([event.track]);
        void element.play().catch(() => { if (active) setNeedsPlay(true); });
      },
      onState: (state) => {
        if (state === "failed" || state === "closed") finish("A transmissão foi interrompida. Confira o transmissor e conecte novamente.");
        if (state === "disconnected") setStatus("stalled");
      },
    });
    const firstFrameTimeout = setTimeout(() => finish("Nenhum vídeo recebido. Confira se a câmera está transmitindo e se o formato é compatível."), 18000);
    dispose.current = () => {
      active = false; clearTimeout(timer); clearTimeout(renewTimer); clearTimeout(firstFrameTimeout);
      if (frameCallback !== undefined) element.cancelVideoFrameCallback(frameCallback);
      receiver.close();
      const stream = element.srcObject;
      if (stream instanceof MediaStream) stream.getTracks().forEach((track) => track.stop());
      element.pause(); element.srcObject = null;
    };
    const renew = async () => {
      try { await receiver.renew(); if (active) renewTimer = setTimeout(() => void renew(), 10000); }
      catch { finish("Acesso à transmissão interrompido. Confira a sessão e reconecte."); }
    };
    if (typeof element.requestVideoFrameCallback === "function") frameCallback = element.requestVideoFrameCallback(countFrames);
    const measure = async () => {
      try {
        const sample = videoSample(await receiver.getStats());
        if (!active) return;
        const now = performance.now();
        const seconds = (now - previousTime) / 1000;
        const supportsPresentation = typeof element.requestVideoFrameCallback === "function";
        if (sample) {
          const next = sampleMetrics(sample, previous);
          if ((sample.framesDecoded ?? 0) > (previous?.framesDecoded ?? 0)) {
            lastFrame = now; receivedFrame = true;
            clearTimeout(firstFrameTimeout);
          }
          setMetrics({ ...next, presentedFps: supportsPresentation && presentationStarted && !document.hidden ? Math.max(0, presented - previousPresented) / seconds : null });
          previous = sample;
        } else {
          setMetrics(emptyMetrics);
        }
        if (receivedFrame) setStatus(now - lastFrame > 4000 ? "stalled" : "playing");
        if (receivedFrame && now - lastFrame > 15000) { finish("A câmera deixou de enviar vídeo. Confira o transmissor e conecte novamente."); return; }
        previousTime = now; previousPresented = presented;
        timer = setTimeout(() => void measure(), 1000);
      } catch { finish("Não foi possível acompanhar a transmissão. Conecte novamente."); }
    };
    try {
      await receiver.start(remote?.endpoint ?? url, window.location.origin);
      if (active) timer = setTimeout(() => void measure(), 1000);
      if (active && remote) renewTimer = setTimeout(() => void renew(), 10000);
    } catch (reason) {
      finish(reason instanceof Error && reason.name !== "TypeError" && reason.name !== "AbortError" ? reason.message : "Não foi possível conectar. Inicie o servidor de vídeo local e a câmera; depois tente novamente.");
    }
  };

  const busy = status === "connecting" || status === "playing" || status === "stalled";
  return (
    <section className="stream-panel" aria-label={remote?.camera.name ?? "Transmissão da câmera"}>
      <div className="stream-heading"><div><p className="eyebrow">VÍDEO INDEPENDENTE</p><h2>{remote?.camera.name ?? "Transmissão da câmera"}</h2><p>Vídeo contínuo, sem aguardar a análise de pessoas.</p></div><span className="stream-target">Meta: 720p · 30 FPS</span></div>
      <form className="stream-form" onSubmit={(event) => void connect(event)}>
        {!remote && <label htmlFor="stream-address">Endereço do stream WHEP<input id="stream-address" value={url} onChange={(event) => setUrl(event.target.value)} disabled={busy} spellCheck={false} autoComplete="off" required aria-describedby="stream-help" /></label>}
        <button className="primary-action" type="submit" disabled={busy}>Conectar transmissão</button>
        <button className="secondary-button" type="button" disabled={!busy} onClick={disconnect}>Desconectar</button>
      </form>
      {!remote && <p id="stream-help" className="stream-help">Conexão local. Inicie o servidor de mídia e o transmissor no computador. Uma URL RTSP ou MJPEG não é um endereço WHEP.</p>}
      <div className={`stream-screen stream-${status}`}>
        <video ref={video} autoPlay muted playsInline aria-label={remote ? `Vídeo de ${remote.camera.name}` : "Transmissão da câmera sem análise de IA"} />
        {remote && status === "playing" && <svg className="server-detections" viewBox="0 0 1000 562.5" preserveAspectRatio="xMidYMid meet" aria-label="Localização aproximada das pessoas na análise recente">
          {remote.camera.boxes.map((box, index) => <rect key={index} x={box.x * 1000} y={box.y * 562.5} width={box.width * 1000} height={box.height * 562.5} fill="none" stroke="var(--accent, #c5f17b)" strokeWidth="3" />)}
        </svg>}
        <span className="stream-state" role="status">{labels[status]}</span>
        {(status === "idle" || status === "error") && <div className="stream-placeholder"><span aria-hidden="true">◉</span><p>{status === "idle" ? "Conecte uma transmissão para visualizar o vídeo." : "O vídeo não está disponível."}</p></div>}
        {needsPlay && <button className="primary-action stream-play" type="button" onClick={() => { void video.current?.play().then(() => setNeedsPlay(false)).catch(() => setError("O navegador não conseguiu reproduzir o vídeo.")); }}>Reproduzir vídeo</button>}
      </div>
      {error && <p className="stream-error" role="alert">{error}</p>}
      <dl className="stream-metrics">
        <div><dt>FPS decodificados</dt><dd>{format(metrics.decodedFps)}</dd></div>
        <div><dt>FPS apresentados</dt><dd>{format(metrics.presentedFps)}</dd></div>
        <div><dt>Resolução recebida</dt><dd>{metrics.resolution ?? "—"}</dd></div>
        <div><dt>Recepção (Mb/s)</dt><dd>{format(metrics.mbps, 2)}</dd></div>
        <div><dt>Buffer médio (ms)</dt><dd>{format(metrics.bufferMs)}</dd></div>
      </dl>
      <p className="stream-help">Métricas medidas no navegador, não valores garantidos. O buffer não representa o atraso total da câmera até a tela. Mantenha a aba visível para medir a apresentação.</p>
      <div className="stream-note">{remote ? `Pessoas: ${remote.camera.people_count ?? "—"} · Análise CPU: ${format(remote.camera.inference_fps)} FPS · ${format(remote.camera.latency_ms)} ms. Caixas da análise recente, não sincronizadas quadro a quadro. Sem gravação de vídeo.` : "IA não conectada a este vídeo. Nenhuma contagem ou caixa de detecção é estimada aqui; o fluxo não grava imagens."}</div>
    </section>
  );
}
