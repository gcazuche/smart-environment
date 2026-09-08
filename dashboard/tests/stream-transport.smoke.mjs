// Explicit integration smoke; requires the local MediaMTX + a publisher already running.
// Checks signaling only. It does NOT establish ICE/DTLS or validate browser playback.
import assert from "node:assert/strict";
import { DEFAULT_STREAM_URL, sessionUrl } from "../app/stream-client.ts";

const origin = "http://localhost:3000";
const offer = [
  "v=0", "o=- 1 1 IN IP4 127.0.0.1", "s=-", "t=0 0", "a=group:BUNDLE 0",
  "m=video 9 UDP/TLS/RTP/SAVPF 96", "c=IN IP4 0.0.0.0", "a=mid:0", "a=recvonly",
  "a=rtcp-mux", "a=ice-ufrag:smoke123", "a=ice-pwd:smoketestpassword1234567890123456",
  "a=fingerprint:sha-256 " + Array(32).fill("AB").join(":"), "a=setup:actpass",
  "a=rtpmap:96 H264/90000", "a=fmtp:96 level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=42e01f",
  "a=candidate:1 1 UDP 2130706431 127.0.0.1 59999 typ host", "a=end-of-candidates", "",
].join("\r\n");
const options = await fetch(DEFAULT_STREAM_URL, {
  method: "OPTIONS", headers: { Origin: origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type" }, signal: AbortSignal.timeout(5000),
});
assert.ok(options.ok);
assert.equal(options.headers.get("access-control-allow-origin"), origin);
const response = await fetch(DEFAULT_STREAM_URL, {
  method: "POST", headers: { Origin: origin, "Content-Type": "application/sdp" }, body: offer,
  credentials: "omit", redirect: "error", signal: AbortSignal.timeout(5000),
});
assert.equal(response.status, 201, `WHEP ${response.status}: ${await response.clone().text()}`);
const resource = sessionUrl(DEFAULT_STREAM_URL, response.headers.get("location"));
try {
  assert.match(response.headers.get("content-type"), /application\/sdp/);
  assert.equal(response.headers.get("access-control-allow-origin"), origin);
  assert.match(response.headers.get("access-control-expose-headers")?.toLowerCase() ?? "", /location/);
  assert.match(await response.text(), /^v=0/);
  console.log("CORS + full-SDP WHEP POST 201 + same-origin session: OK (not a playback test)");
} finally {
  const removed = await fetch(resource, { method: "DELETE", headers: { Origin: origin }, signal: AbortSignal.timeout(5000) });
  assert.ok(removed.ok, `DELETE ${removed.status}`);
  console.log(`WHEP DELETE ${removed.status}: OK`);
}
