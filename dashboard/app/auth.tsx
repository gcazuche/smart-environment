"use client";

import type { FormEvent } from "react";
import { useState } from "react";

export type AuthUser = {
  email: string;
  name: string;
  role: "Administrador";
};

const LOCAL_SESSION_KEY = "smart-environment.local-session";
const SESSION_MAX_AGE_MS = 8 * 60 * 60 * 1000;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function nameFromEmail(email: string) {
  const localPart = email.split("@", 1)[0] ?? "administrador";
  const words = localPart.split(/[._-]+/u).filter(Boolean);
  return words.length > 0
    ? words.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")
    : "Administrador";
}

export function userInitials(name: string) {
  const words = name.trim().split(/\s+/u).filter(Boolean);
  if (words.length === 0) return "AD";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return `${words[0][0]}${words[words.length - 1][0]}`.toUpperCase();
}

export function readLocalSession(): AuthUser | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.sessionStorage.getItem(LOCAL_SESSION_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (!isRecord(parsed) || typeof parsed.email !== "string" || typeof parsed.issuedAt !== "number") return null;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/u.test(parsed.email) || Date.now() - parsed.issuedAt > SESSION_MAX_AGE_MS) {
      window.sessionStorage.removeItem(LOCAL_SESSION_KEY);
      return null;
    }
    const email = parsed.email.trim().toLowerCase();
    return { email, name: nameFromEmail(email), role: "Administrador" };
  } catch {
    window.sessionStorage.removeItem(LOCAL_SESSION_KEY);
    return null;
  }
}

function saveLocalSession(email: string): AuthUser {
  const normalizedEmail = email.trim().toLowerCase();
  const user: AuthUser = { email: normalizedEmail, name: nameFromEmail(normalizedEmail), role: "Administrador" };
  window.sessionStorage.setItem(LOCAL_SESSION_KEY, JSON.stringify({ ...user, issuedAt: Date.now() }));
  return user;
}

export function clearLocalSession() {
  if (typeof window !== "undefined") window.sessionStorage.removeItem(LOCAL_SESSION_KEY);
}

export function LoginScreen({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/u.test(normalizedEmail)) {
      setError("Digite um e-mail válido para entrar.");
      return;
    }
    if (password.length < 6) {
      setError("A senha precisa ter pelo menos 6 caracteres.");
      return;
    }
    setError("");
    onLogin(saveLocalSession(normalizedEmail));
  };

  return (
    <main className="auth-shell">
      <section className="auth-story" aria-label="Sobre o Smart Environment">
        <div className="auth-brand">
          <span className="brand-mark auth-brand-mark logo-slot" role="img" aria-label="Espaço reservado para a logo" />
          <span>Smart<br />Environment</span>
        </div>
        <div className="auth-story-copy">
          <span className="auth-kicker">AMBIENTE INTELIGENTE</span>
          <h1>Seu ambiente,<br />em equilíbrio.</h1>
          <p>Uma visão clara de ocupação, recursos e sustentabilidade para decisões melhores no dia a dia.</p>
          <ul className="auth-highlights">
            <li><span>↗</span><div><strong>Ocupação em contexto</strong><small>Indicadores por ambiente e horário.</small></div></li>
            <li><span>⌁</span><div><strong>Monitoramento responsável</strong><small>Privacidade e revisão humana no centro.</small></div></li>
          </ul>
        </div>
        <div className="auth-story-footer"><span><i /> Processamento local disponível</span></div>
        <div className="auth-orbit orbit-one" aria-hidden="true" />
        <div className="auth-orbit orbit-two" aria-hidden="true" />
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-card-meta"><span className="auth-mini-mark logo-slot" role="img" aria-label="Espaço reservado para a logo" /><span className="auth-secure-pill"><i /> Acesso ao sistema</span></div>
          <p className="eyebrow">BEM-VINDO DE VOLTA</p>
          <h2>Entrar no painel</h2>
          <p className="auth-lead">Acesse a visão geral do seu ambiente e acompanhe os dispositivos conectados.</p>

          <form className="auth-form" onSubmit={submit} noValidate>
            <label htmlFor="auth-email">E-mail</label>
            <input
              id="auth-email"
              name="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="voce@empresa.com"
              autoComplete="email"
              required
            />
            <div className="auth-label-row"><label htmlFor="auth-password">Senha</label><span>mínimo de 6 caracteres</span></div>
            <div className="password-field">
              <input
                id="auth-password"
                name="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
              <button type="button" onClick={() => setShowPassword((visible) => !visible)} aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}>
                {showPassword ? "Ocultar" : "Mostrar"}
              </button>
            </div>
            {error && <p className="auth-error" role="alert">{error}</p>}
            <button className="auth-submit" type="submit">Entrar no painel <span>→</span></button>
          </form>
        </div>
      </section>
    </main>
  );
}

export function ProfileModal({ user, onClose, onLogout }: { user: AuthUser; onClose: () => void; onLogout: () => void }) {
  return (
    <div className="modal-backdrop profile-backdrop">
      <section className="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-modal-title">
        <button className="modal-close" type="button" onClick={onClose} aria-label="Fechar perfil">×</button>
        <div className="profile-identity"><span className="avatar profile-avatar">{userInitials(user.name)}</span><div><p className="eyebrow">CONTA ATIVA</p><h2 id="profile-modal-title">{user.name}</h2><span>{user.role}</span></div></div>
        <div className="profile-details">
          <div><small>E-mail</small><strong>{user.email}</strong></div>
          <div><small>Sessão</small><strong>Ativa neste dispositivo</strong></div>
          <div><small>Permissão atual</small><strong>Administrador</strong></div>
        </div>
        <div className="profile-notice"><strong>Privacidade</strong><p>Os frames das câmeras permanecem locais e transitórios.</p></div>
        <div className="modal-actions"><button className="secondary-button" type="button" onClick={onClose}>Fechar</button><button className="danger-button" type="button" onClick={onLogout}>Sair do painel</button></div>
      </section>
    </div>
  );
}
