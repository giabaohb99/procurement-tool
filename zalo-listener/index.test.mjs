// Bài kiểm zalo-listener (ai-CR-122): chữ ký khớp Python, đường HTTP từ chối lượt không ký, hàng đợi /updates.
// Chạy: docker run --rm -v <thư mục>:/w -w /w node:20-alpine sh -c "npm ci && node --test"
import assert from "node:assert/strict";
import test from "node:test";

process.env.ZALO_LISTENER_NO_START = "1";
process.env.AGENT_SERVICE_SECRET = "k-test";
process.env.PORT = "0";

const mod = await import("./index.mjs");

test("chữ ký khớp core/agent_signature.py", () => {
  // Hai vectơ tính bằng Python `agent_signature.build`.
  assert.equal(mod.buildSignature("k-test", "1700000000", "post", "/send", 0, Buffer.from('{"a":1}')),
    "91c8ad13395778a4d394d8b7fa85511792ac8da038420c2dcaaae474977e221e");
  assert.equal(mod.buildSignature("k-test", "1700000000", "GET", "/updates", 0, Buffer.alloc(0)),
    "48d0857600fe76289f4e233df84a48cdc7597e8c83e80508c281d525cd9c4e02");
});

async function call(port, method, urlPath, body, { sign = true } = {}) {
  const raw = body ? Buffer.from(JSON.stringify(body)) : Buffer.alloc(0);
  const ts = String(Math.floor(Date.now() / 1000));
  const headers = { "content-type": "application/json" };
  if (sign) {
    headers["x-agent-ts"] = ts;
    headers["x-agent-user"] = "0";
    headers["x-agent-sign"] = mod.buildSignature("k-test", ts, method, urlPath.split("?")[0], 0, raw);
  }
  const res = await fetch(`http://127.0.0.1:${port}${urlPath}`, { method, headers, body: raw.length ? raw : undefined });
  return { status: res.status, json: await res.json() };
}

test("HTTP: không ký bị từ chối, có ký thì đọc được trạng thái và hàng đợi", async () => {
  const server = mod.startServer();
  await new Promise((r) => server.once("listening", r));
  const { port } = server.address();
  try {
    const health = await fetch(`http://127.0.0.1:${port}/health`).then((r) => r.json());
    assert.equal(health.ok, true);

    const unsigned = await call(port, "GET", "/status", null, { sign: false });
    assert.equal(unsigned.status, 401);

    const st = await call(port, "GET", "/status");
    assert.equal(st.status, 200);
    assert.equal(st.json.state, "idle");

    const t0 = Date.now();
    const upd = await call(port, "GET", "/updates?offset=0&timeout=1");
    assert.equal(upd.status, 200);
    assert.deepEqual(upd.json.events, []);
    assert.ok(Date.now() - t0 >= 900, "giữ kết nối chờ đúng timeout");

    const send = await call(port, "POST", "/send", { thread_id: "123", thread_type: "user", text: "chào" });
    assert.equal(send.status, 409);
    assert.match(send.json.error, /chưa kết nối/);
  } finally {
    server.close();
  }
});
