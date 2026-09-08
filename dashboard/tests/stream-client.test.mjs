import assert from "node:assert/strict";
import test from "node:test";
import { DEFAULT_STREAM_URL, WhepReceiver, validateStreamUrl, sessionUrl, sampleMetrics, videoSample } from "../app/stream-client.ts";

const origin = "http://localhost:3000";
const location = `${DEFAULT_STREAM_URL}/session-123`;
const answer = (overrides = {}) => new Response("v=0\r\n", {
  status: 201, headers: { "Content-Type": "application/sdp", Location: location, ...overrides },
});

class FakePeer extends EventTarget {
  iceGatheringState = "complete";
  connectionState = "new";
  ontrack = null;
  onconnectionstatechange = null;
  localDescription = null;
  remoteDescription = null;
  transceivers = [];
  closed = false;
  addTransceiver(kind, options) { this.transceivers.push([kind, options]); }
  async createOffer() { return { type: "offer", sdp: "v=0\r\na=candidate:local\r\n" }; }
  async setLocalDescription(value) { this.localDescription = value; }
  async setRemoteDescription(value) { this.remoteDescription = value; }
  async getStats() { return new Map(); }
  close() { this.closed = true; }
}

function receiver(request = async () => answer(), peer = new FakePeer()) {
  return { peer, client: new WhepReceiver({ peerFactory: () => peer, request, onTrack() {}, onState() {} }) };
}

test("accepts explicit loopback WHEP only", () => {
  assert.equal(validateStreamUrl(DEFAULT_STREAM_URL, origin), DEFAULT_STREAM_URL);
  assert.equal(validateStreamUrl("http://localhost:8889/camera1/whep", origin), "http://localhost:8889/camera1/whep");
});

for (const url of ["rtsp://127.0.0.1:8554/camera1", "http://192.168.1.36:8889/camera1/whep",
  "https://example.com/camera1/whep", "http://localhost:9000/camera1/whep",
  "http://user:secret@localhost:8889/camera1/whep", `${DEFAULT_STREAM_URL}?token=secret`,
  `${DEFAULT_STREAM_URL}#secret`, "http://localhost:8889/../whep", "not-a-url"]) {
  test(`rejects unsupported endpoint: ${url.replace(/secret/g, "redacted")}`, () => {
    assert.throws(() => validateStreamUrl(url, origin));
  });
}

test("rejects hosted or wrong-port dashboard before a network request", async () => {
  let requests = 0;
  const { client, peer } = receiver(async () => { requests++; return answer(); });
  await assert.rejects(client.start(DEFAULT_STREAM_URL, "https://smart.example.com"), /localhost/);
  assert.equal(requests, 0);
  assert.equal(peer.closed, true);
  assert.throws(() => validateStreamUrl(DEFAULT_STREAM_URL, "http://localhost:3001"));
});

test("session cleanup is restricted to the same endpoint and a single session ID", () => {
  assert.equal(sessionUrl(DEFAULT_STREAM_URL, "/camera1/whep/session-123"), location);
  for (const value of [null, "https://evil.example/session", "http://user@127.0.0.1:8889/camera1/whep/id", "/admin/delete", "/camera1/whep/a/b", "/camera1/whep/id?token=secret", "/camera1/whep/"]) {
    assert.throws(() => sessionUrl(DEFAULT_STREAM_URL, value));
  }
});

test("posts full SDP video-only, receives answer and deletes session without credentials", async () => {
  const calls = [];
  const { client, peer } = receiver(async (url, options) => {
    calls.push({ url, options });
    return options.method === "DELETE" ? new Response(null, { status: 204 }) : answer();
  });
  await client.start(DEFAULT_STREAM_URL, origin);
  assert.deepEqual(peer.transceivers, [["video", { direction: "recvonly" }]]);
  assert.equal(calls[0].options.body, peer.localDescription.sdp);
  assert.equal(calls[0].options.credentials, "omit");
  assert.equal(calls[0].options.redirect, "error");
  assert.equal(peer.remoteDescription.type, "answer");
  client.close();
  client.close();
  assert.equal(peer.closed, true);
  assert.equal(calls.filter((call) => call.options.method === "DELETE").length, 1);
  assert.equal(calls[1].url, location);
  assert.equal(calls[1].options.credentials, "omit");
  await assert.rejects(client.start(DEFAULT_STREAM_URL, origin), /nova conexão/);
});

test("waits for ICE gathering, not arbitrary delays", async () => {
  const peer = new FakePeer(); peer.iceGatheringState = "gathering";
  let requests = 0;
  const { client } = receiver(async (_url, opts) => { requests++; return opts.method === "DELETE" ? new Response(null, { status: 204 }) : answer(); }, peer);
  const starting = client.start(DEFAULT_STREAM_URL, origin);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(requests, 0);
  peer.iceGatheringState = "complete";
  peer.dispatchEvent(new Event("icegatheringstatechange"));
  await starting;
  assert.equal(requests, 1);
  client.close();
});

test("ICE timeout releases the peer and sends no offer", async () => {
  const peer = new FakePeer(); peer.iceGatheringState = "gathering";
  let requests = 0;
  const { client } = receiver(async () => { requests++; return answer(); }, peer);
  await assert.rejects(client.start(DEFAULT_STREAM_URL, origin, 15), /tempo limite/);
  assert.equal(peer.closed, true);
  assert.equal(requests, 0);
});

test("HTTP timeout cancels the fetch and releases the peer", async () => {
  const { client, peer } = receiver(async (_url, opts) => new Promise((_resolve, reject) => {
    opts.signal.addEventListener("abort", () => reject(new Error("timeout")), { once: true });
  }));
  await assert.rejects(client.start(DEFAULT_STREAM_URL, origin, 15), /timeout/);
  assert.equal(peer.closed, true);
});

test("late POST after cancellation is deleted and never attached to the peer", async () => {
  let resolvePost;
  const deleted = [];
  const { client, peer } = receiver((url, opts) => opts.method === "DELETE"
    ? (deleted.push(url), Promise.resolve(new Response(null, { status: 204 })))
    : new Promise((resolve) => { resolvePost = resolve; }));
  const starting = client.start(DEFAULT_STREAM_URL, origin);
  await new Promise((resolve) => setImmediate(resolve));
  client.close();
  resolvePost(answer());
  await assert.rejects(starting, /cancelada/);
  assert.equal(peer.remoteDescription, null);
  assert.deepEqual(deleted, [location]);
});

test("offline source gives actionable error, not successful connection", async () => {
  const { client, peer } = receiver(async () => new Response("not found", { status: 404 }));
  await assert.rejects(client.start(DEFAULT_STREAM_URL, origin), /transmissor ativo/);
  assert.equal(peer.closed, true);
});

test("invalid answer is cleaned up, invalid session never triggers a cross-origin request", async () => {
  const calls = [];
  const { client } = receiver(async (url, options) => {
    calls.push(url);
    return options.method === "DELETE" ? new Response(null, { status: 204 }) : answer({ "Content-Type": "text/html" });
  });
  await assert.rejects(client.start(DEFAULT_STREAM_URL, origin), /resposta de vídeo/);
  assert.deepEqual(calls, [DEFAULT_STREAM_URL, location]);
  const other = receiver(async () => answer({ Location: "http://evil.example/session" }));
  await assert.rejects(other.client.start(DEFAULT_STREAM_URL, origin), /sessão inválida/);
});

test("measures counter deltas, not a constant target or total-call duration", () => {
  const previous = { id: "v1", timestamp: 1000, framesDecoded: 10, bytesReceived: 1000, jitterBufferDelay: .1, jitterBufferEmittedCount: 10 };
  const current = { id: "v1", timestamp: 2000, framesDecoded: 40, bytesReceived: 126000, frameWidth: 1280, frameHeight: 720, jitterBufferDelay: .7, jitterBufferEmittedCount: 40 };
  const result = sampleMetrics(current, previous);
  assert.equal(result.decodedFps, 30);
  assert.equal(result.mbps, 1);
  assert.equal(result.bufferMs, 20);
  assert.equal(result.resolution, "1280 × 720");
  assert.equal(sampleMetrics(current, null).decodedFps, null);
  assert.equal(sampleMetrics(current, { ...previous, id: "old" }).decodedFps, null);
  assert.equal(sampleMetrics(current, { ...previous, timestamp: 2000 }).decodedFps, null);
  assert.equal(sampleMetrics({ ...current, framesDecoded: 2 }, previous).decodedFps, null);
  assert.equal(sampleMetrics({ ...current, framesDecoded: NaN }, previous).decodedFps, null);
  assert.equal(sampleMetrics({ ...current, timestamp: Infinity }, previous).decodedFps, null);
  assert.equal(sampleMetrics({ id: "v1", timestamp: 2000 }, previous).decodedFps, null);
  assert.equal(sampleMetrics({ ...current, framesDecoded: 10 }, previous).decodedFps, 0);
});

test("selects only incoming video, never audio/outgoing stats", () => {
  const sample = { id: "v", type: "inbound-rtp", kind: "video", framesDecoded: 20, timestamp: 3 };
  assert.equal(videoSample(new Map([["a", { type: "inbound-rtp", kind: "audio" }], ["v", sample]])), sample);
  assert.equal(videoSample(new Map([["a", { type: "outbound-rtp", kind: "video" }]])), null);
});
