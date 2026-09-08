import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { metadataOrigin } from "../app/metadata-origin.ts";

test("social metadata accepts only exact known origins, not attacker-controlled hostnames", () => {
  assert.equal(metadataOrigin("localhost:3000"), "http://localhost:3000");
  assert.equal(metadataOrigin("127.0.0.1:3000"), "http://127.0.0.1:3000");
  const published = "smart-environment-monitor.angel-of-the-night16.chatgpt.site";
  assert.equal(metadataOrigin(published.toUpperCase()), `https://${published}`);
  for (const host of [null, "", "localhost.evil.example", "localhost:3000@evil.example", "evil.example", "localhost:4000", `${published}.evil.example`, `${published}:443`, "https://localhost:3000", "[::]:3000"]) assert.equal(metadataOrigin(host), null);
});

test("dev server remains loopback and React/RSC versions remain aligned", async () => {
  const config = await readFile(new URL("../vite.config.ts", import.meta.url), "utf8");
  assert.match(config, /host: "localhost"/);
  const manifest = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
  assert.equal(manifest.dependencies.react, manifest.dependencies["react-dom"]);
  assert.equal(manifest.dependencies.react, manifest.devDependencies["react-server-dom-webpack"]);
  const [major, minor, patch] = manifest.dependencies.react.split(".").map(Number);
  assert.equal(major, 19); assert.equal(minor, 2); assert.ok(patch >= 8);
});
