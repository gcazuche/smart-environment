export const DASHBOARD_TIME_ZONE = "America/Sao_Paulo";
export type Period = "today" | "7d" | "30d";

export function formatDashboardClock(timestamp: number) {
  if (!Number.isFinite(timestamp)) return null;
  const date = new Date(timestamp);
  if (!Number.isFinite(date.getTime())) return null;
  return {
    iso: date.toISOString(),
    date: new Intl.DateTimeFormat("pt-BR", { timeZone: DASHBOARD_TIME_ZONE, weekday: "long", day: "2-digit", month: "long", year: "numeric" }).format(date),
    time: new Intl.DateTimeFormat("pt-BR", { timeZone: DASHBOARD_TIME_ZONE, hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" }).format(date),
  };
}

export function periodRange(period: Period, now: number) {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: DASHBOARD_TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(now);
  const part = (name: string) => Number(parts.find((item) => item.type === name)?.value);
  // Calendar labels, not durations: subtract calendar days in a UTC date container.
  const end = new Date(Date.UTC(part("year"), part("month") - 1, part("day")));
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - (period === "7d" ? 6 : period === "30d" ? 29 : 0));
  const formatter = new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", dateStyle: "short" });
  return `${formatter.format(start)} a ${formatter.format(end)}`;
}

export type CameraDraft = { name: string; environment: string; source: "webcam" | "mjpeg" | "rtsp"; address: string };

export function validateCameraDraft(draft: CameraDraft): string | null {
  if (!draft.name.trim() || draft.name.trim().length > 80) return "Informe um nome de até 80 caracteres para a câmera.";
  if (!draft.environment.trim()) return "Selecione o ambiente da câmera.";
  if (!["webcam", "mjpeg", "rtsp"].includes(draft.source)) return "Tipo de câmera inválido.";
  if (draft.source === "webcam") return /^\d{1,2}$/.test(draft.address.trim()) ? null : "Informe o índice da webcam, entre 0 e 99.";
  let url: URL;
  try { url = new URL(draft.address.trim()); } catch { return "Informe um endereço válido para a câmera."; }
  if (!url.hostname || !draft.address.trim().startsWith(`${url.protocol}//`)) return "Informe o endereço completo, com protocolo e nome ou IP da câmera.";
  if (url.username || url.password || url.search || url.hash) return "Não inclua senhas, tokens, parâmetros ou fragmentos no endereço. As credenciais serão configuradas no servidor.";
  if (draft.source === "rtsp" ? url.protocol !== "rtsp:" : !["http:", "https:"].includes(url.protocol)) return "O protocolo do endereço não corresponde ao tipo de câmera.";
  return null;
}

export function validateEnvironmentName(name: string, existing: string[]): string | null {
  const normalized = name.trim().replace(/\s+/g, " ");
  if (!normalized || normalized.length > 80) return "Informe um nome de até 80 caracteres para o ambiente.";
  if (existing.some((item) => item.trim().replace(/\s+/g, " ").toLocaleLowerCase("pt-BR") === normalized.toLocaleLowerCase("pt-BR"))) return "Já existe um ambiente com esse nome.";
  return null;
}

export function readingAge(value: string | null, now = Date.now()) {
  if (!value) return "Sem leitura";
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp) || timestamp > now + 5000) return "Horário da leitura inválido";
  const seconds = Math.max(0, Math.floor((now - timestamp) / 1000));
  if (seconds < 2) return "Agora";
  if (seconds < 60) return `Há ${seconds}s`;
  if (seconds < 3600) return `Há ${Math.floor(seconds / 60)} min`;
  return `Há ${Math.floor(seconds / 3600)} h`;
}
