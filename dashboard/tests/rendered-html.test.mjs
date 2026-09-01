import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the authentication gate before the dashboard", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /Smart Environment/);
  assert.match(html, /Entrar no painel/);
  assert.match(html, /Acesso ao sistema/);
  assert.doesNotMatch(html, /protótipo|acadêmico|demonstração|simulad|TCC/i);
  assert.doesNotMatch(html, /Suas câmeras/);
  assert.doesNotMatch(html, /codex-preview|SkeletonPreview|react-loading-skeleton/);
});

test("ships product metadata and removes starter assets", async () => {
  const [page, auth, layout, css, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/auth.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(page, /type Section = "overview" \| "cameras"/);
  assert.match(page, /LoginScreen/);
  assert.match(page, /ProfileModal/);
  assert.doesNotMatch(page, /Suas câmeras/);
  assert.doesNotMatch(page, /protótipo|acadêmico|demonstração|simulad|TCC/i);
  assert.match(page, /aria-haspopup="dialog"/);
  assert.match(page, /clearLocalSession/);
  assert.match(page, /if \(!authUser\) return/);
  assert.match(auth, /sessionStorage/);
  assert.match(auth, /readLocalSession/);
  assert.doesNotMatch(auth, /protótipo|acadêmico|demonstração|simulad|TCC/i);
  assert.match(auth, /Sair do painel/);
  assert.match(auth, /logo-slot/);
  assert.match(page, /Adicionar câmera/);
  assert.match(page, /Câmera do celular/);
  assert.match(page, /selectedEnvironment/);
  assert.match(page, /onOpenEnvironment/);
  assert.match(page, /EnvironmentDetails/);
  assert.match(page, /environmentCameras/);
  assert.match(page, /Câmeras.*associados|dispositivos associados/i);
  assert.match(page, /Voltar para ambientes/);
  assert.match(page, /127\.0\.0\.1:8765\/api\/cameras/);
  assert.match(page, /frame\.jpg/);
  assert.match(page, /crossOrigin="anonymous"/);
  assert.match(page, /Gateway ESP32/);
  assert.match(page, /Decisão humana obrigatória/);
  assert.match(layout, /generateMetadata/);
  assert.match(layout, /\/og\.png/);
  assert.match(css, /@media \(max-width: 680px\)/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await access(new URL("../public/og.png", import.meta.url));
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
  await assert.rejects(access(new URL("public/favicon.svg", root)));
});
