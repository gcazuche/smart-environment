/* Local progressive enhancement. Data navigation and mutations remain Django forms. */
(() => {
  "use strict";
  const format = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo", dateStyle: "short", timeStyle: "short",
  });
  const clock = document.querySelector("[data-clock]");
  function updateClock() {
    if (!clock || document.hidden) return;
    const now = new Date();
    clock.textContent = `${format.format(now)} · Brasília`;
    clock.setAttribute("datetime", now.toISOString());
  }
  updateClock();
  const timer = window.setInterval(updateClock, 30000);
  document.addEventListener("visibilitychange", updateClock);
  window.addEventListener("pagehide", () => window.clearInterval(timer), { once: true });

  const toggle = document.querySelector("[data-menu-toggle]");
  const sidebar = document.getElementById("sidebar");
  function closeMenu() {
    sidebar?.classList.remove("is-open");
    toggle?.setAttribute("aria-expanded", "false");
  }
  toggle?.addEventListener("click", () => {
    const open = sidebar?.classList.toggle("is-open") ?? false;
    toggle.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && sidebar?.classList.contains("is-open")) {
      closeMenu();
      toggle?.focus();
    }
  });
  document.addEventListener("click", (event) => {
    if (sidebar && !sidebar.contains(event.target) && !toggle?.contains(event.target)) closeMenu();
  });

  for (const form of document.querySelectorAll("[data-save-form]")) {
    form.addEventListener("submit", () => {
      const button = form.querySelector("[data-save-button]");
      if (button) { button.disabled = true; button.textContent = "Salvando…"; }
      form.setAttribute("aria-busy", "true");
    });
  }
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) window.location.reload();
  });

  const source = document.getElementById("id_source");
  const address = document.getElementById("id_address");
  source?.addEventListener("change", () => {
    if (!address) return;
    const webcam = source.value === "webcam";
    if (webcam && !address.value) address.value = "0";
    if (!webcam && /^\d+$/.test(address.value)) address.value = "";
    address.placeholder = webcam ? "0" : source.value === "rtsp" ? "rtsp://192.168.1.10/stream" : "http://192.168.1.10:8080/video";
  });
})();
