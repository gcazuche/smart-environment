"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { backend, type DataRepository } from "./data-client";
import { processingOrigin, serverStreamUrl, type ServerAuthorization } from "./stream-client";
import { StreamPreview } from "./stream-preview";

export type ServerReading = {
  camera_id: string; name: string; environment_id: string; configured: boolean;
  source: "webcam" | "mjpeg" | "rtsp"; status: "online" | "waiting";
  people_count: number | null; boxes: { x: number; y: number; width: number; height: number }[];
  last_seen_at: string | null; latency_ms: number | null; inference_fps: number | null;
  detector: string; backend: string;
};
export function processingConfigured(): boolean { return Boolean(import.meta.env.VITE_PROCESSING_SERVER_URL?.trim()); }
function authorization(): ServerAuthorization {
  return {
    baseUrl: processingOrigin(import.meta.env.VITE_PROCESSING_SERVER_URL ?? ""),
    token: async () => {
      const result = await backend()?.client.auth.getSession();
      const token = result?.data.session?.access_token;
      if (!token || result?.error) throw new Error("Entre com sua conta Supabase para acessar o servidor.");
      return token;
    },
  };
}

export function useProcessingServer(repository: DataRepository | null) {
  const [readings, setReadings] = useState<ServerReading[]>([]);
  const [error, setError] = useState("");
  const [connected, setConnected] = useState(false);
  useEffect(() => {
    if (!processingConfigured()) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    const refresh = async () => {
      try {
        if (!repository) throw new Error("Configure o Supabase para acessar o servidor.");
        const auth = authorization();
        const response = await fetch(`${auth.baseUrl}/v1/cameras`, {
          headers: { Authorization: `Bearer ${await auth.token()}` }, cache: "no-store",
          credentials: "omit", redirect: "error", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(6000)]),
        });
        if (!response.ok) throw new Error("Servidor indisponível ou acesso não autorizado. Confira a conexão e a configuração.");
        const result = await response.json();
        if (!Array.isArray(result.cameras) || result.cameras.length > 500) throw new Error("Resposta inválida do servidor.");
        if (active) { setReadings(result.cameras); setConnected(true); setError(""); }
      } catch (reason) {
        if (active) { setReadings([]); setConnected(false); setError(reason instanceof Error && reason.name === "Error" ? reason.message : "Não foi possível acessar o servidor de processamento."); }
      } finally { if (active) timer = setTimeout(() => void refresh(), 700); }
    };
    void refresh();
    return () => { active = false; controller.abort(); clearTimeout(timer); };
  }, [repository]);
  // Clear boxes/counts locally even when a request hangs after the last successful response.
  const [clock, setClock] = useState(() => Date.now());
  useEffect(() => { const timer = setInterval(() => setClock(Date.now()), 500); return () => clearInterval(timer); }, []);
  const fresh = useMemo(() => readings.map(item => {
    const age = clock - Date.parse(item.last_seen_at ?? "");
    return Number.isFinite(age) && age >= -5000 && age < 2000 ? item : {
      ...item, status: "waiting" as const, people_count: null, boxes: [], last_seen_at: null,
    };
  }), [readings, clock]);
  return { readings: fresh, error, connected };
}

export const ProcessingContext = createContext<ReturnType<typeof useProcessingServer>>({ readings: [], error: "", connected: false });

export function ServerCamera({ cameraId, name }: { cameraId: string; name: string }) {
  const state = useContext(ProcessingContext);
  const camera = state.readings.find(item => item.camera_id === cameraId);
  if (!camera?.configured) return <div className="empty-state"><h3>{name}</h3><p>{state.error || "Aguardando vínculo desta câmera no servidor. Use o UUID abaixo no arquivo de configuração da VM."}</p><code>{cameraId}</code></div>;
  let auth: ServerAuthorization;
  try { auth = authorization(); } catch { return <p role="alert">Configure o endereço do servidor.</p>; }
  return <StreamPreview remote={{ authorization: auth, endpoint: serverStreamUrl(auth.baseUrl, cameraId), camera }} />;
}
