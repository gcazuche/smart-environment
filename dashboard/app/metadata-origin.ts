// Do not reflect an arbitrary Host / forwarded host into social-preview URLs.
const publicHost = "smart-environment-monitor.angel-of-the-night16.chatgpt.site";
export function metadataOrigin(host: string | null): string | null {
  const normalized = host?.toLowerCase();
  if (normalized === publicHost) return `https://${publicHost}`;
  if (["localhost", "localhost:3000", "127.0.0.1:3000"].includes(normalized ?? "")) return `http://${normalized}`;
  return null;
}
