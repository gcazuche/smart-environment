import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { formatDashboardClock, periodRange, readingAge, validateCameraDraft, validateEnvironmentName } from "../app/dashboard-model.ts";

test("clock follows seconds and the midnight boundary in Brasilia, not UTC", () => {
  const before = formatDashboardClock(Date.parse("2026-09-04T02:59:59Z"));
  const after = formatDashboardClock(Date.parse("2026-09-04T03:00:00Z"));
  assert.match(before.date, /quinta-feira, 03 de setembro de 2026/);
  assert.equal(before.time, "23:59:59");
  assert.match(after.date, /sexta-feira, 04 de setembro de 2026/);
  assert.equal(after.time, "00:00:00");
  assert.equal(formatDashboardClock(Date.parse("2026-09-04T03:00:01Z")).time, "00:00:01");
  assert.equal(after.iso, "2026-09-04T03:00:00.000Z");
});

test("clock handles year changes and invalid timestamps", () => {
  assert.match(formatDashboardClock(Date.parse("2027-01-01T03:00:00Z")).date, /01 de janeiro de 2027/);
  for (const value of [NaN, Infinity, -Infinity, 1e20]) assert.equal(formatDashboardClock(value), null);
});

test("periods use inclusive calendar days in the displayed timezone", () => {
  const now = Date.parse("2026-09-04T15:00:00Z");
  assert.equal(periodRange("today", now), "04/09/2026 a 04/09/2026");
  assert.equal(periodRange("7d", now), "29/08/2026 a 04/09/2026");
  assert.equal(periodRange("30d", now), "06/08/2026 a 04/09/2026");
  assert.equal(periodRange("today", Date.parse("2026-09-04T02:00:00Z")), "03/09/2026 a 03/09/2026");
  assert.equal(periodRange("7d", Date.parse("2026-01-01T12:00:00Z")), "26/12/2025 a 01/01/2026");
});

test("environment validation rejects empty, long and normalized duplicate names", () => {
  assert.match(validateEnvironmentName(" ", []), /Informe/);
  assert.match(validateEnvironmentName("a".repeat(81), []), /80/);
  assert.match(validateEnvironmentName("  laboratório   1  ", ["Laboratório 1"]), /Já existe/);
  assert.equal(validateEnvironmentName("Laboratório 2", ["Laboratório 1"]), null);
});

const draft = { name: "Câmera 1", environment: "Escritório", source: "webcam", address: "0" };
test("camera validation checks name, environment, source and webcam index", () => {
  assert.equal(validateCameraDraft(draft), null);
  assert.match(validateCameraDraft({ ...draft, name: "" }), /nome/);
  assert.match(validateCameraDraft({ ...draft, environment: "" }), /ambiente/);
  assert.match(validateCameraDraft({ ...draft, source: "unknown" }), /inválido/);
  for (const address of ["-1", "100", "a", ""]) assert.match(validateCameraDraft({ ...draft, address }), /índice/);
});

test("source changes require matching protocols and never accept embedded credentials", () => {
  assert.equal(validateCameraDraft({ ...draft, source: "mjpeg", address: "http://192.168.1.36:8080/video" }), null);
  assert.equal(validateCameraDraft({ ...draft, source: "rtsp", address: "rtsp://192.168.1.36/live" }), null);
  for (const address of ["rtsp:stream", "rtsp:///stream"]) assert.match(validateCameraDraft({ ...draft, source: "rtsp", address }), /endereço completo/);
  for (const address of ["http://user:secret@192.168.1.36/video", "http://192.168.1.36/video?token=secret", "http://192.168.1.36/video#secret"]) {
    assert.match(validateCameraDraft({ ...draft, source: "mjpeg", address }), /senhas/);
  }
  assert.match(validateCameraDraft({ ...draft, source: "rtsp", address: "http://192.168.1.36/video" }), /protocolo/);
  assert.match(validateCameraDraft({ ...draft, source: "mjpeg", address: "file:///secret" }), /protocolo/);
});

test("reading ages do not emit NaN or falsely current timestamps", () => {
  const now = Date.parse("2026-09-04T12:00:00Z");
  assert.equal(readingAge(null, now), "Sem leitura");
  assert.equal(readingAge("invalid", now), "Horário da leitura inválido");
  assert.equal(readingAge("2026-09-04T12:05:00Z", now), "Horário da leitura inválido");
  assert.equal(readingAge("2026-09-04T12:00:00Z", now), "Agora");
  assert.equal(readingAge("2026-09-04T11:59:30Z", now), "Há 30s");
  assert.equal(readingAge("2026-09-04T11:58:00Z", now), "Há 2 min");
  assert.equal(readingAge("2026-09-04T09:00:00Z", now), "Há 3 h");
});

test("UI wiring preserves streams and connects forms to repository without local fake writes", async () => {
  const read = (name) => readFile(new URL(`../app/${name}`, import.meta.url), "utf8");
  const [page, clock, forms, panels, dialog] = await Promise.all([read("page.tsx"), read("dashboard-clock.tsx"), read("management-forms.tsx"), read("history-panels.tsx"), read("dashboard-dialog.tsx")]);
  assert.match(page, /<DashboardClock/);
  assert.match(page, /<StreamPreview/);
  assert.doesNotMatch(page + panels, /QUINTA-FEIRA, 14 DE AGOSTO|68%|99,2%|6h 12m|há 12 min|há 8 minutos/);
  assert.match(clock, /setInterval\(update, 1000\)/);
  assert.match(clock, /clearInterval\(timer\)/);
  assert.match(clock, /removeEventListener\("visibilitychange", update\)/);
  assert.match(page, /onOpenHistory=\{\(\) => navigate\("history"\)\}/);
  assert.match(page, /onClick=\{onEdit\}>Editar configurações/);
  assert.match(page, /onClick=\{onAdd\}>＋ Novo ambiente/);
  assert.match(page, /className="add-environment" type="button" onClick=\{onAdd\}/);
  assert.match(forms, /repository.saveCamera/);
  assert.match(forms, /repository.saveEnvironment/);
  assert.match(forms, /repository.saveRule/);
  assert.match(forms, /disabled=\{busy\|\|!canEdit\|\|!repository\}/);
  assert.doesNotMatch(forms, /localStorage|sessionStorage|fetch\(/);
  assert.match(panels, /value=\{period\} onChange=/);
  assert.match(panels, /value=\{environment\} onChange=/);
  assert.match(panels, /repository.samples/);
  assert.match(panels, /repository.report/);
  assert.match(panels, /repository.reviewAlert/);
  assert.match(dialog, /showModal\(/);
  assert.match(dialog, /onCancel=/);
  assert.match(dialog, /previous.focus\(/);
});
