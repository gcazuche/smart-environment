"use client";

import { useEffect, useState } from "react";
import { formatDashboardClock } from "./dashboard-model";

export function DashboardClock() {
  const [clock, setClock] = useState<ReturnType<typeof formatDashboardClock>>(null);
  useEffect(() => {
    const update = () => setClock(formatDashboardClock(Date.now()));
    const initial = window.setTimeout(update, 0);
    const timer = window.setInterval(update, 1000);
    document.addEventListener("visibilitychange", update);
    return () => { window.clearTimeout(initial); window.clearInterval(timer); document.removeEventListener("visibilitychange", update); };
  }, []);
  return <time className="dashboard-clock" dateTime={clock?.iso} aria-label={clock ? `${clock.date}, ${clock.time}, horário de Brasília` : "Carregando data e hora"}>
    <span>{clock?.date ?? "Carregando data…"}</span><span>{clock?.time ?? "—"} <small>Brasília</small></span>
  </time>;
}
