// Bài kiểm zalo-listener (ai-CR-122): chữ ký khớp Python, đường HTTP từ chối lượt không ký, hàng đợi /updates.
// Chạy: docker run --rm -v <thư mục>:/w -w /w node:20-alpine sh -c "npm ci && node --test"
import assert from "node:assert/strict";
import test from "node:test";

process.env.ZALO_LISTENER_NO_START = "1";
process.env.AGENT_SERVICE_SECRET = "k-test";
process.env.PORT = "0";

const mod = await import("./index.mjs");

test("chữ ký khớp core/agent_signature.py", () => {
  // Vectơ tính bằng Python `agent_signature.build` (khuôn duoc-CR-757: thêm ".<kênh AI>|<chat riêng>", vắng = ".|").
  assert.equal(mod.buildSignature("k-test", "1700000000", "post", "/send", 0, Buffer.from('{"a":1}')),
    "bafc037a8c2ac5a5a2ddc2089ee980e537979eb0f5cbc74bd0424f176d9ee2d5");
  assert.equal(mod.buildSignature("k-test", "1700000000", "GET", "/updates", 0, Buffer.alloc(0)),
    "21fbaf8bcc575e4a49fdd7dd51a372739ed1413ec300ecb14512c4555414828b");
  assert.equal(mod.buildSignature("k-test", "1700000000", "POST", "/send", 7, Buffer.from('{"a":1}'), "zalo|1"),
    "4cfb2ce8732ba61b47f63cd0a796f48916e8f52150fceb07129e3784e34b5301");
  assert.equal(mod.contextMaterial({ "x-agent-ai-channel": " zalo ", "x-agent-private-chat": "1" }), "zalo|1");
  assert.equal(mod.contextMaterial({}), "|");
});

async function call(port, method, urlPath, body, { sign = true, context = {}, signedContext = context } = {}) {
  const raw = body ? Buffer.from(JSON.stringify(body)) : Buffer.alloc(0);
  const ts = String(Math.floor(Date.now() / 1000));
  const headers = { "content-type": "application/json", ...context };
  if (sign) {
    headers["x-agent-ts"] = ts;
    headers["x-agent-user"] = "0";
    headers["x-agent-sign"] = mod.buildSignature("k-test", ts, method, urlPath.split("?")[0], 0, raw,
      mod.contextMaterial(signedContext));
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

    // ai-CR-129: đăng xuất khi chưa có phiên vẫn trả gọn, máy về «idle»; không ký thì bị chặn.
    const out = await call(port, "POST", "/logout", {});
    assert.equal(out.status, 200);
    assert.equal(out.json.state, "idle");
    assert.equal((await call(port, "POST", "/logout", {}, { sign: false })).status, 401);

    // duoc-CR-757: hai header ngữ cảnh nằm trong chuỗi ký — ký đúng thì qua, thêm / đổi sau khi ký thì 401.
    const ctx = { "x-agent-ai-channel": "zalo", "x-agent-private-chat": "1" };
    assert.equal((await call(port, "GET", "/status", null, { context: ctx })).status, 200);
    assert.equal((await call(port, "GET", "/status", null, { context: ctx, signedContext: {} })).status, 401);
    assert.equal((await call(port, "GET", "/status", null,
      { context: { ...ctx, "x-agent-private-chat": "0" }, signedContext: ctx })).status, 401);
  } finally {
    server.close();
  }
});
