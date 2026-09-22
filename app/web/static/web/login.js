"use strict";

(() => {
  const toggle = document.getElementById("migration-toggle");
  const details = document.getElementById("migration-content");
  if (!(toggle instanceof HTMLButtonElement) || !(details instanceof HTMLElement)) return;

  toggle.hidden = false;
  toggle.addEventListener("click", () => {
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    details.hidden = expanded;
    toggle.setAttribute("aria-expanded", String(!expanded));
    toggle.textContent = expanded ? "Ver detalhes de acesso" : "Ocultar detalhes de acesso";
  });
})();
