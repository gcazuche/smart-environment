import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import { Miniflare, convertV4MiniflareOptions } from "miniflare";

// Resolve from the consumer, not a potentially unrelated top-level sharp copy.
const consumerRequire = createRequire(import.meta.resolve("miniflare"));
const sharp = consumerRequire("sharp");
const semver = createRequire(consumerRequire.resolve("sharp"))("semver");
const fixture = { create: { width: 8, height: 6, channels: 3, background: "#46744e" } };

test("every locked sharp copy is patched and retains Windows/Linux binaries", async () => {
  const lock = JSON.parse(await readFile(new URL("../package-lock.json", import.meta.url), "utf8"));
  const copies = Object.entries(lock.packages).filter(([path]) => /(^|\/)node_modules\/sharp$/.test(path));
  assert.ok(copies.length > 0);
  for (const [path, pkg] of copies) {
    assert.ok(semver.gte(pkg.version, "0.35.4"), `${path} must include GHSA-rgj7-g3m4-5g8c fix`);
    for (const platform of ["win32-x64", "linux-x64", "linuxmusl-x64"]) {
      const name = `@img/sharp-${platform}`;
      const binary = Object.entries(lock.packages).find(([key, value]) =>
        key.endsWith(`node_modules/${name}`) && value.version === pkg.optionalDependencies[name]);
      assert.ok(binary, `lock must retain ${name} matching sharp ${pkg.version}`);
    }
  }
});

test("Miniflare resolves corrected sharp and the loaded libheif is patched", () => {
  assert.ok(semver.gte(sharp.versions.sharp, "0.35.4"));
  assert.ok(semver.gte(sharp.versions.heif, "1.23.2"));
});

test("native image decoding and resizing preserve PNG, JPEG, WebP and AVIF support", async () => {
  for (const format of ["png", "jpeg", "webp", "avif"]) {
    const source = await sharp(fixture).toFormat(format).toBuffer();
    const metadata = await sharp(source).metadata();
    assert.equal(metadata.width, 8);
    assert.equal(metadata.height, 6);
    const { info } = await sharp(source).resize(4, 3).png().toBuffer({ resolveWithObject: true });
    assert.equal(info.width, 4);
    assert.equal(info.height, 3);
    assert.equal(info.format, "png");
  }
});

test("unsupported bytes and a truncated AVIF fail without a successful decode", async () => {
  await assert.rejects(sharp(Buffer.from("not an image")).toBuffer());
  const avif = await sharp(fixture).avif().toBuffer();
  await assert.rejects(sharp(avif.subarray(0, 24)).toBuffer());
});

test("Miniflare Images binding still decodes AVIF and transforms to PNG", { timeout: 30_000 }, async (t) => {
  const runtime = new Miniflare({
    ...convertV4MiniflareOptions({
      modules: true,
      script: "export default { fetch() { return new Response('image-test'); } };",
      compatibilityDate: "2026-09-01",
      images: { binding: "IMAGES" },
      cf: false,
      host: "127.0.0.1",
      port: 0,
    }),
    telemetry: { enabled: false },
  });
  t.after(() => runtime.dispose());
  const binding = await runtime.getImagesBinding("IMAGES");
  const avif = await sharp(fixture).avif().toBuffer();
  const info = await binding.info(new Blob([avif]).stream());
  assert.equal(info.width, 8);
  assert.equal(info.height, 6);
  assert.equal(info.format, "image/avif");
  const output = await binding.input(new Blob([avif]).stream())
    .transform({ width: 4, height: 3 }).output({ format: "image/png" });
  const response = output.response();
  assert.equal(response.headers.get("content-type"), "image/png");
  const metadata = await sharp(await response.arrayBuffer()).metadata();
  assert.equal(metadata.width, 4);
  assert.equal(metadata.height, 3);
});
