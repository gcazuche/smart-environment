export type BackendConfig = { url: string; key: string; organizationId: string };
export function parseBackendConfig(values: Record<string, string | undefined>): BackendConfig | null {
  const url = values.VITE_SUPABASE_URL?.trim() ?? "";
  const key = values.VITE_SUPABASE_PUBLISHABLE_KEY?.trim() ?? "";
  const organizationId = values.VITE_ORGANIZATION_ID?.trim() ?? "";
  if (!url && !key && !organizationId) return null;
  let endpoint: URL;
  try { endpoint = new URL(url); } catch { throw new Error("Configure a URL do Supabase."); }
  const local = ["127.0.0.1", "localhost"].includes(endpoint.hostname);
  if ((!local && endpoint.protocol !== "https:") || (local && !["http:","https:"].includes(endpoint.protocol)) || endpoint.username || endpoint.password || endpoint.search || endpoint.hash || endpoint.pathname !== "/") throw new Error("URL do Supabase inválida.");
  // New projects use public keys. Reject privileged keys before creating a client.
  if (!/^sb_publishable_[A-Za-z0-9_-]+$/.test(key)) throw new Error("Configure uma chave publicável sb_publishable_. Nunca use a chave secreta no dashboard.");
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(organizationId)) throw new Error("Configure o identificador da organização.");
  return { url: endpoint.origin, key, organizationId };
}

export function dataError(error: unknown): Error {
  const code = typeof error === "object" && error !== null && "code" in error ? String(error.code) : "";
  if (code === "23505") return new Error("Já existe um registro com esse nome ou identificador.");
  if (code === "23503") return new Error("O ambiente ou a câmera selecionada não está disponível.");
  if (code === "42501") return new Error("Sua conta não tem permissão para esta operação.");
  if (code === "40001" || code === "PGRST116") return new Error("O registro foi alterado ou não está disponível. Atualize a página e tente novamente.");
  if (code === "23514" || code === "22023") return new Error("Confira os campos e a operação selecionada.");
  return new Error("Não foi possível concluir a operação. Confira a conexão e a configuração do serviço.");
}
