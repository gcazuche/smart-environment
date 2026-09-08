import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

async function render(extraHeaders = {}) {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html", ...extraHeaders } }),
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
  assert.match(html, /src="\/brand\/smart-environment-horizontal\.png"/);
  assert.match(html, /src="\/brand\/smart-environment-symbol\.png"/);
  assert.doesNotMatch(html, /logo-slot|Espaço reservado para a logo/);
  assert.doesNotMatch(html, /protótipo|acadêmico|demonstração|simulad|TCC/i);
  assert.doesNotMatch(html, /Suas câmeras/);
  assert.doesNotMatch(html, /codex-preview|SkeletonPreview|react-loading-skeleton/);
});

test("rendered social metadata does not reflect an unknown Host or forwarded host", async () => {
  const response = await render({ host: "attacker.invalid", "x-forwarded-host": "forwarded.invalid" });
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.doesNotMatch(html, /https?:\/\/(?:attacker|forwarded)\.invalid\/og\.png/);
  assert.match(html, /Smart Environment/);
});

test("ships product metadata and removes starter assets", async () => {
  const [page, auth, layout, css, packageJson, forms, panels] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/auth.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
    readFile(new URL("../app/management-forms.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/history-panels.tsx", import.meta.url), "utf8"),
  ]);

  assert.match(page, /type Section = "overview" \| "cameras"/);
  assert.match(page, /LoginScreen/);
  assert.match(page, /ProfileModal/);
  assert.doesNotMatch(page, /Suas câmeras/);
  assert.doesNotMatch(page, /protótipo|acadêmico|demonstração|simulad|TCC/i);
  assert.match(page, /aria-haspopup="dialog"/);
  assert.match(page, /session.logout/);
  assert.match(page, /!session.ready \|\| !session.user/);
  assert.match(auth, /sessionStorage/);
  assert.match(auth, /readLocalSession/);
  assert.doesNotMatch(auth, /protótipo|acadêmico|demonstração|simulad|TCC/i);
  assert.match(auth, /Sair do painel/);
  assert.match(auth, /BrandLogo/);
  assert.match(page, /BrandLogo/);
  assert.match(page, /className="brand-compact"/);
  assert.match(page, /className="mobile-brand"/);
  assert.doesNotMatch(`${auth}\n${page}\n${css}`, /logo-slot|Espaço reservado para a logo/);
  assert.match(page, /Adicionar câmera/);
  assert.match(forms, /Câmera do celular/);
  assert.match(page, /selectedEnvironment/);
  assert.match(page, /onOpenEnvironment/);
  assert.match(page, /EnvironmentDetails/);
  assert.match(page, /environmentCameras/);
  assert.match(page, /Câmeras.*associados|dispositivos associados/i);
  assert.match(page, /Voltar para ambientes/);
  assert.match(page, /127\.0\.0\.1:8765\/api\/cameras/);
  assert.match(page, /frame\.jpg/);
  assert.match(page, /crossOrigin="anonymous"/);
  assert.match(forms, /Gateway ESP32/);
  assert.match(panels, /Decisão humana obrigatória/);
  assert.match(layout, /generateMetadata/);
  assert.match(layout, /\/og\.png/);
  assert.match(css, /@media \(max-width: 680px\)/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await access(new URL("../public/og.png", import.meta.url));
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
  await assert.rejects(access(new URL("public/favicon.svg", root)));
});

test("ships the supplied logo files unchanged and with their original proportions", async () => {
  const assets = [
    { name: "smart-environment-horizontal.png", width: 363, height: 154 },
    { name: "smart-environment-symbol.png", width: 167, height: 137 },
  ];
  for (const asset of assets) {
    const source = await readFile(new URL(`../public/brand/${asset.name}`, import.meta.url));
    const built = await readFile(new URL(`../dist/client/brand/${asset.name}`, import.meta.url));
    assert.equal(source.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
    assert.equal(source.readUInt32BE(16), asset.width);
    assert.equal(source.readUInt32BE(20), asset.height);
    assert.deepEqual(built, source);
  }
});
