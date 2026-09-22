import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../../app/web/static/web/video.js", import.meta.url), "utf8");
const video = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
const CAMERA = "11111111-1111-4111-8111-111111111111";
const SESSION = "22222222-2222-4222-8222-222222222222";
const ENDPOINT = `/api/processing/cameras/${CAMERA}/whep/`;
const LOCATION = `${ENDPOINT}${SESSION}/`;
const ORIGIN = "https://dashboard.example.invalid";

test("only canonical camera IDs and same-origin session paths are accepted", () => {
  assert.equal(video.streamEndpoint(CAMERA), ENDPOINT);
  for (const id of ["../anything", "http://localhost/", "", "ABC"]) assert.throws(() => video.streamEndpoint(id));
  assert.equal(video.sessionPath(ENDPOINT, LOCATION, ORIGIN), LOCATION);
  for (const location of [null, `https://evil.invalid${LOCATION}`, `${LOCATION}?secret=x`, `${LOCATION}#x`, `${ENDPOINT}bad/`, `${ENDPOINT}${SESSION}`]) {
    assert.throws(() => video.sessionPath(ENDPOINT, location, ORIGIN));
  }
});

function reading(overrides = {}) {
  return { camera_id: CAMERA, configured: true, status: "online", people_count: 0,
    last_seen_at: new Date(100000).toISOString(), latency_ms: 30, inference_fps: 2,
    boxes: [{ x: 0.1, y: 0.2, width: 0.3, height: 0.4 }], ...overrides };
}

test("reading validation rejects malformed boxes/counts and duplicate cameras", () => {
  assert.equal(video.parseReadings({ cameras: [reading()] }).length, 1);
  for (const item of [reading({ people_count: -1 }), reading({ people_count: true }),
    reading({ inference_fps: Infinity }), reading({ boxes: [{ x: 0.9, y: 0, width: 0.5, height: 1 }] }),
    reading({ last_seen_at: "not a date" }), reading({ configured: "yes" })]) {
    assert.throws(() => video.parseReadings({ cameras: [item] }));
  }
  assert.throws(() => video.parseReadings({ cameras: [reading(), reading()] }));
});

test("absence, stale/future timestamps and waiting remain unknown, measured zero is allowed", () => {
  assert.equal(video.freshReading(reading(), 101999).people_count, 0);
  for (const item of [null, reading({ status: "waiting" }), reading({ configured: false }), reading({ last_seen_at: null })]) {
    assert.equal(video.freshReading(item, 100000), null);
  }
  assert.equal(video.freshReading(reading(), 102000), null);
  assert.equal(video.freshReading(reading(), 94999), null);
});

class Peer {
  iceGatheringState = "complete";
  listeners = new Map();
  closed = false;
  addEventListener(name, listener) { this.listeners.set(name, listener); }
  removeEventListener(name) { this.listeners.delete(name); }
  addTransceiver(kind, options) { assert.equal(kind, "video"); assert.equal(options.direction, "recvonly"); }
  async createOffer() { return { type: "offer", sdp: "v=0\r\n" }; }
  async setLocalDescription(value) { this.localDescription = value; }
  async setRemoteDescription(value) { this.remoteDescription = value; }
  async getStats() { return new Map(); }
  close() { this.closed = true; }
}

function receiver(request, peer = new Peer()) {
  return [new video.WhepReceiver({ request, peerFactory: () => peer, csrf: "test-csrf",
    origin: ORIGIN, onTrack: () => {}, onState: () => {} }), peer];
}

function answer(headers = {}) {
  return new Response("v=0\r\n", { status: 201, headers: { Location: LOCATION, "Content-Type": "application/sdp", ...headers } });
}

test("WHEP sends CSRF same-origin with no browser bearer; renew/delete cleanup", async () => {
  const calls = [];
  const [client, peer] = receiver(async (url, options) => { calls.push([url, options]); return options.method === "POST" && url === ENDPOINT ? answer() : new Response(null, { status: 204 }); });
  await client.start(CAMERA);
  assert.equal(peer.remoteDescription.type, "answer");
  await client.renew();
  client.close();
  assert.deepEqual(calls.map(([url, options]) => [url, options.method]), [
    [ENDPOINT, "POST"], [`${LOCATION}keepalive/`, "POST"], [LOCATION, "DELETE"],
  ]);
  for (const [, options] of calls) {
    assert.equal(options.headers["X-CSRFToken"], "test-csrf");
    assert.equal(options.headers.Authorization, undefined);
    assert.equal(options.credentials, "same-origin");
    assert.equal(options.redirect, "error");
  }
  assert.equal(peer.closed, true);
  await assert.rejects(client.start(CAMERA));
});

test("401/403 are explicit access failures and remove peer", async () => {
  for (const status of [401, 403]) {
    const [client, peer] = receiver(async () => new Response(null, { status }));
    await assert.rejects(client.start(CAMERA), video.AccessError);
    assert.equal(peer.closed, true);
  }
});

test("keepalive 401/403 closes peer and attempts bounded session deletion", async () => {
  for (const status of [401, 403]) {
    const methods = [];
    const [client, peer] = receiver(async (url, options) => {
      methods.push(options.method);
      if (url === ENDPOINT) return answer();
      return new Response(null, { status: options.method === "DELETE" ? 204 : status });
    });
    await client.start(CAMERA);
    await assert.rejects(client.renew(), video.AccessError);
    assert.equal(peer.closed, true);
    assert.deepEqual(methods, ["POST", "POST", "DELETE"]);
  }
});

test("late POST after cancellation revokes the newly created upstream session", async () => {
  let complete, started;
  const posted = new Promise(resolve => { started = resolve; });
  const calls = [];
  const [client] = receiver((url, options) => {
    calls.push(options.method);
    if (options.method === "POST") { started(); return new Promise(resolve => { complete = resolve; }); }
    return Promise.resolve(new Response(null, { status: 204 }));
  });
  const pending = client.start(CAMERA);
  await posted;
  client.close();
  complete(answer());
  await assert.rejects(pending);
  assert.deepEqual(calls, ["POST", "DELETE"]);
});

test("invalid answer deletes known session; malicious Location is never fetched", async () => {
  const calls = [];
  const [client] = receiver(async (url, options) => {
    calls.push([url, options.method]);
    return options.method === "DELETE" ? new Response(null, { status: 204 }) : answer({ "Content-Type": "text/html" });
  });
  await assert.rejects(client.start(CAMERA));
  assert.deepEqual(calls.map(item => item[1]), ["POST", "DELETE"]);
  const rogueCalls = [];
  const [rogue] = receiver(async (url) => { rogueCalls.push(url); return answer({ Location: "https://evil.invalid/session/" }); });
  await assert.rejects(rogue.start(CAMERA));
  assert.deepEqual(rogueCalls, [ENDPOINT]);
});

test("video FPS uses decoded frame deltas, resets remain unknown", () => {
  const previous = { id: "video", timestamp: 1000, framesDecoded: 0, bytesReceived: 100 };
  const current = { id: "video", timestamp: 2000, framesDecoded: 30, bytesReceived: 125100 };
  assert.deepEqual(video.sampleMetrics(current, previous), { decodedFps: 30, mbps: 1 });
  assert.equal(video.sampleMetrics(current, null).decodedFps, null);
  assert.equal(video.sampleMetrics({ ...current, timestamp: 1000 }, previous).decodedFps, null);
  assert.equal(video.sampleMetrics({ ...current, id: "other" }, previous).decodedFps, null);
});

test("serial polling does not overlap, aborts on hidden and backs off failures", async () => {
  const scheduled = [], cancelled = [];
  let resolveTask, count = 0, visible = true, signal;
  const poller = video.startPolling({ intervalMs: 10, canRun: () => visible,
    schedule: (callback, delay) => { scheduled.push([callback, delay]); return scheduled.length; },
    cancel: value => cancelled.push(value), onError: () => {},
    task: current => { count++; signal = current; return new Promise(resolve => { resolveTask = resolve; }); },
  });
  poller.wake(); poller.wake();
  assert.equal(count, 1);
  visible = false; poller.wake();
  assert.equal(signal.aborted, true);
  resolveTask(); await Promise.resolve(); await Promise.resolve();
  assert.equal(scheduled.length, 0);
  visible = true; poller.wake(); assert.equal(count, 2);
  resolveTask(); await Promise.resolve(); await Promise.resolve();
  assert.equal(scheduled.length, 1);
  poller.stop(); assert.equal(cancelled.length, 1);
  let errors = 0;
  const failing = video.startPolling({ intervalMs: 10, canRun: () => true,
    schedule: (_callback, delay) => { assert.equal(delay, 20); return 1; }, cancel: () => {},
    onError: () => errors++, task: async () => { throw new Error("offline"); },
  });
  await Promise.resolve(); await Promise.resolve();
  assert.equal(errors, 1); failing.stop();
});

test("browser implementation has no capture/recording/storage or token plumbing", () => {
  for (const prohibited of ["getUserMedia", "MediaRecorder", "localStorage", "sessionStorage", "Authorization:", "access_token", "refresh_token"]) assert.equal(source.includes(prohibited), false);
  assert.match(source, /visibilitychange/);
  assert.match(source, /requestVideoFrameCallback|framesDecoded/);
  assert.match(source, /Conecte para retomar/);
});

test("multiple camera viewers share one telemetry request and last unsubscribe aborts it", async () => {
  const doc = { hidden: false };
  let calls = 0, complete, firstSignal;
  const received = [];
  const request = (_path, options) => {
    calls++; firstSignal = options.signal;
    return new Promise(resolve => { complete = resolve; });
  };
  const first = video.subscribeReadings(doc, request, false, rows => received.push([1, rows]), assert.fail);
  const second = video.subscribeReadings(doc, request, false, rows => received.push([2, rows]), assert.fail);
  assert.equal(calls, 1);
  complete(new Response(JSON.stringify({ cameras: [reading()] }), { headers: { "Content-Type": "application/json" } }));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(received.length, 2);
  first.stop(); second.stop();
  const third = video.subscribeReadings(doc, request, false, assert.fail, assert.fail);
  assert.equal(calls, 2);
  third.stop(); assert.equal(firstSignal.aborted, true);
  complete(new Response(JSON.stringify({ cameras: [] }), { headers: { "Content-Type": "application/json" } }));
  await new Promise(resolve => setImmediate(resolve));
});

function mounted(request, enabled = true) {
  const peer = new Peer(), listeners = new Map();
  const element = () => ({ textContent: "", disabled: false, hidden: false,
    addEventListener() {}, removeEventListener() {}, removeAttribute() {} });
  const elements = new Map(["[data-video]", "[data-local-frame]", "[data-video-start]", "[data-video-stop]",
    "[data-video-status]", "[data-analysis-status]", "[data-people-count]", "[data-analysis-fps]", "[data-video-fps]"]
    .map(key => [key, element()]));
  elements.get("[data-video]").srcObject = null;
  elements.get("[data-video]").play = async () => {};
  elements.get("[data-video-start]").disabled = !enabled;
  const doc = { hidden: false, querySelector: () => ({ value: "test-csrf" }),
    addEventListener: (name, listener) => listeners.set(name, listener), removeEventListener: name => listeners.delete(name),
    defaultView: { location: { origin: ORIGIN }, fetch: request,
      URL: { revokeObjectURL() {} }, addEventListener() {}, removeEventListener() {} } };
  const root = { ownerDocument: doc, dataset: { cameraId: CAMERA, videoMode: "server" }, querySelector: key => elements.get(key) ?? null };
  return { client: video.mountVideo(root, { request, peerFactory: () => peer }), peer, elements, root, doc, listeners };
}

test("viewer never auto-connects and keeps disabled catalog cameras disabled", async () => {
  let calls = 0;
  const viewer = mounted(() => { calls++; throw new Error("must not call"); }, false);
  assert.equal(calls, 0);
  assert.equal(viewer.elements.get("[data-video-start]").disabled, true);
  assert.equal(viewer.elements.get("[data-people-count]").textContent, "Desconhecido");
  await viewer.client.start();
  assert.equal(calls, 0);
  viewer.client.destroy();
});

test("transient telemetry failure preserves video; access denial closes and deletes", async () => {
  for (const status of [503, 401, 403]) {
    const calls = [];
    const viewer = mounted(async (url, options) => {
      calls.push([url, options.method ?? "GET"]);
      if (url === ENDPOINT) return answer();
      return new Response(null, { status: url.endsWith("/cameras/") ? status : 204 });
    });
    await viewer.client.start();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(viewer.peer.closed, status !== 503);
    assert.equal(viewer.elements.get("[data-people-count]").textContent, "Desconhecido");
    if (status !== 503) assert.ok(calls.some(([, method]) => method === "DELETE"));
    viewer.client.destroy();
  }
});

test("hiding the page closes an active viewer and does not reconnect on visibility return", async () => {
  let posts = 0;
  const viewer = mounted(async (url, options) => {
    if (url === ENDPOINT) { posts++; return answer(); }
    if (url.endsWith("/cameras/")) return new Response(JSON.stringify({ cameras: [] }));
    return new Response(null, { status: 204 });
  });
  await viewer.client.start();
  viewer.doc.hidden = true; viewer.listeners.get("visibilitychange")();
  assert.equal(viewer.peer.closed, true);
  viewer.doc.hidden = false; viewer.listeners.get("visibilitychange")();
  assert.equal(posts, 1);
  viewer.client.destroy();
});
