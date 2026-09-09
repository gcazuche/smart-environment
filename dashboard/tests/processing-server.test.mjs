import assert from "node:assert/strict";
import test from "node:test";
import { processingOrigin, serverStreamUrl, WhepReceiver } from "../app/stream-client.ts";

const camera = "11111111-1111-4111-8111-111111111111";
const base = "https://192.168.1.50";
const endpoint = serverStreamUrl(base, camera);
const location = `${endpoint}/22222222-2222-4222-8222-222222222222`;
class Peer {
  iceGatheringState = "complete";
  localDescription = null;
  addTransceiver() {}
  addEventListener() {}
  removeEventListener() {}
  async createOffer() { return { type: "offer", sdp: "v=0\r\n" }; }
  async setLocalDescription(value) { this.localDescription = value; }
  async setRemoteDescription() {}
  close() {}
}
function receiver(request) {
  return new WhepReceiver({ request, peerFactory: () => new Peer(), onTrack() {}, onState() {},
    authorization: { baseUrl: base, token: async () => "session-token" } });
}
test("server address is explicit TLS, never a camera-supplied URL", () => {
  assert.equal(processingOrigin(base), base);
  assert.equal(processingOrigin("http://127.0.0.1:8766"), "http://127.0.0.1:8766");
  for (const value of ["http://192.168.1.50", "https://user:pass@server", "https://server/path", "https://server?token=x", "https://server/#x"]) assert.throws(() => processingOrigin(value));
  assert.throws(() => serverStreamUrl(base, "../../admin"));
});
test("authenticated video POST, renewal and DELETE use current session token without cookies", async () => {
  const calls = [];
  const client = receiver(async (url, options) => {
    calls.push([url, options]);
    return new Response(url === endpoint ? "v=0\r\n" : null, { status: url === endpoint ? 201 : 204,
      headers: { "Content-Type": "application/sdp", Location: location } });
  });
  await client.start(endpoint, "http://localhost:3000");
  await client.renew();
  client.close();
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(calls.map(([, options]) => options.method), ["POST", "POST", "DELETE"]);
  for (const [, options] of calls) {
    assert.equal(options.headers.Authorization, "Bearer session-token");
    assert.equal(options.credentials, "omit");
    assert.equal(options.redirect, "error");
  }
});
test("a different origin is rejected before sending a token", async () => {
  let calls = 0;
  const client = receiver(async () => { calls++; throw new Error("unexpected"); });
  await assert.rejects(client.start(endpoint.replace(base, "https://other.invalid"), base));
  assert.equal(calls, 0);
});
test("refused renewal closes the receiver", async () => {
  const client = receiver(async (url) => url === endpoint ? new Response("v=0", { status: 201,
    headers: { "Content-Type": "application/sdp", Location: location } }) : new Response(null, { status: 403 }));
  await client.start(endpoint, base);
  await assert.rejects(client.renew(), /autorização/);
  await assert.rejects(client.start(endpoint, base), /nova conexão/);
});
