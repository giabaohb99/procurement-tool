// zalo-listener — giữ phiên MỘT tài khoản Zalo của công ty cho bot Lạc Lạc (ai-CR-122, Zalo hướng B).
//
// Tài khoản Zalo thường (không phải bot chính thức) đăng nhập bằng QR qua thư viện zca-js (không chính thức — Zalo có
// thể khóa số nếu gửi dồn dập, nên tiến trình này GIÃN NHỊP mọi tin gửi). Tiến trình KHÔNG có logic nghiệp vụ: chỉ
//   - ghi mọi sự kiện vào một hàng đợi trong bộ nhớ, `agent-poller` kéo về bằng GET /updates (như getUpdates Telegram);
//   - gửi tin / tệp khi `agent-poller` / worker gọi POST /send;
//   - mở đăng nhập QR khi gọi POST /login (ảnh QR đi ra như một sự kiện `qr`, bot chuyển cho đại ca qua Telegram).
// Mọi lượt gọi phải ký HMAC giống core/agent_signature.py (khóa AGENT_SERVICE_SECRET). Chỉ nghe trong mạng nội bộ.
// Phiên đăng nhập (cookie + imei) lưu MÃ HÓA AES-256-GCM ở ZALO_SESSION_FILE.

import crypto from "node:crypto";
import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";

import { GroupEventType, LoginQRCallbackEventType, ThreadType, Zalo } from "zca-js";

const PORT = Number(process.env.PORT || 3100);
const SECRET = process.env.AGENT_SERVICE_SECRET || "";
const SESSION_FILE = process.env.ZALO_SESSION_FILE || "/data/session.enc";
const SEND_GAP_MS = Number(process.env.ZALO_SEND_GAP_MS || 1500);
const GROUP_SYNC_MIN = Number(process.env.ZALO_GROUP_SYNC_MIN || 360);
const BUFFER_MAX = Number(process.env.ZALO_EVENT_BUFFER_MAX || 5000);
const RELOGIN_MIN = Number(process.env.ZALO_RELOGIN_MIN || 10);
const MAX_SKEW_SEC = 300;
const MAX_BODY = 30 * 1024 * 1024;
const USER_AGENT = process.env.ZALO_USER_AGENT
  || "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36";

const log = (...a) => console.log(new Date().toISOString(), ...a);

// ---------------------------------------------------------------------------
// Chữ ký (khớp core/agent_signature.py: HMAC(secret, "ts.METHOD.path.user.sha256(body)"))
// ---------------------------------------------------------------------------
export function buildSignature(secret, ts, method, urlPath, userId, body) {
  const digest = crypto.createHash("sha256").update(body || Buffer.alloc(0)).digest("hex");
  const payload = `${ts}.${method.toUpperCase()}.${urlPath}.${Number(userId || 0)}.${digest}`;
  return crypto.createHmac("sha256", secret || "").update(payload).digest("hex");
}

function verify(req, urlPath, body) {
  if (!SECRET) return "chưa khai AGENT_SERVICE_SECRET";
  const ts = String(req.headers["x-agent-ts"] || "");
  const sign = String(req.headers["x-agent-sign"] || "");
  const user = String(req.headers["x-agent-user"] || "0");
  if (!/^\d+$/.test(ts) || !sign) return "thiếu chữ ký";
  if (Math.abs(Date.now() / 1000 - Number(ts)) > MAX_SKEW_SEC) return "chữ ký quá hạn";
  if (!/^-?\d+$/.test(user)) return "danh tính không hợp lệ";
  const expected = Buffer.from(buildSignature(SECRET, ts, req.method, urlPath, user, body));
  const got = Buffer.from(sign);
  if (expected.length !== got.length || !crypto.timingSafeEqual(expected, got)) return "chữ ký sai";
  return "";
}

// ---------------------------------------------------------------------------
// Phiên đăng nhập mã hóa
// ---------------------------------------------------------------------------
function sessionKey() {
  const base = process.env.ZALO_SESSION_KEY || SECRET;
  return crypto.createHash("sha256").update(`zalo-session:${base}`).digest();
}

async function saveSession(creds) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", sessionKey(), iv);
  const enc = Buffer.concat([cipher.update(JSON.stringify(creds), "utf8"), cipher.final()]);
  const blob = Buffer.concat([iv, cipher.getAuthTag(), enc]);
  await fs.mkdir(path.dirname(SESSION_FILE), { recursive: true });
  await fs.writeFile(SESSION_FILE, blob, { mode: 0o600 });
}

async function loadSession() {
  let blob;
  try {
    blob = await fs.readFile(SESSION_FILE);
  } catch {
    return null;
  }
  try {
    const decipher = crypto.createDecipheriv("aes-256-gcm", sessionKey(), blob.subarray(0, 12));
    decipher.setAuthTag(blob.subarray(12, 28));
    const raw = Buffer.concat([decipher.update(blob.subarray(28)), decipher.final()]).toString("utf8");
    return JSON.parse(raw);
  } catch {
    log("phiên lưu không giải mã được (đổi khóa?) — cần quét QR lại");
    return null;
  }
}

// ---------------------------------------------------------------------------
// Hàng đợi sự kiện (con trỏ kiểu Telegram). Id bắt đầu từ mốc giờ khởi động để khởi động lại vẫn TĂNG so với con trỏ
// bot đang giữ.
// ---------------------------------------------------------------------------
let nextId = Date.now();
const events = [];
const waiters = new Set();

function push(ev) {
  events.push({ id: nextId++, ...ev });
  if (events.length > BUFFER_MAX) events.splice(0, events.length - BUFFER_MAX);
  for (const w of waiters) w();
  waiters.clear();
}

function pending(offset) {
  return events.filter((e) => e.id >= offset);
}

function ack(offset) {
  while (events.length && events[0].id < offset) events.shift();
}

// ---------------------------------------------------------------------------
// Trạng thái phiên Zalo
// ---------------------------------------------------------------------------
const state = { value: "idle", name: "", uid: "", since: Date.now(), reason: "" };
let api = null;
let loggingIn = false;
let reloginTimer = null;
const groupNames = new Map();

function setState(value, extra = {}) {
  const changed = state.value !== value;
  Object.assign(state, { value, since: changed ? Date.now() : state.since, reason: "" }, extra);
  if (changed && (value === "connected" || value === "down")) {
    push({ kind: "status", state: value, name: state.name, reason: state.reason });
  }
}

const CLOSE_REASONS = {
  1000: "đóng chủ động",
  1006: "đứt mạng",
  3000: "tài khoản đang mở Zalo Web / Zalo PC ở nơi khác",
  3003: "Zalo đá phiên ra",
};

function text(content) {
  return typeof content === "string" ? content : null;
}

async function attach(newApi) {
  api = newApi;
  try {
    state.uid = String(api.getOwnId() || "");
  } catch {
    state.uid = "";
  }
  try {
    const info = await api.fetchAccountInfo();
    state.name = String(info?.profile?.displayName || info?.profile?.zaloName || state.name || "");
  } catch {
    /* tên chỉ để hiển thị */
  }
  const listener = api.listener;
  listener.on("connected", () => setState("connected"));
  listener.on("closed", (code, reason) => {
    setState("down", { reason: CLOSE_REASONS[code] || `mã ${code} ${reason || ""}`.trim() });
    scheduleRelogin();
  });
  listener.on("error", (e) => log("listener lỗi:", e?.message || e));
  listener.on("message", (m) => {
    try {
      onMessage(m);
    } catch (e) {
      log("xử tin hỏng:", e?.message || e);
    }
  });
  listener.on("group_event", (ev) => {
    onGroupEvent(ev).catch((e) => log("xử sự kiện nhóm hỏng:", e?.message || e));
  });
  listener.start({ retryOnClose: true });
  setTimeout(() => syncGroups().catch((e) => log("đồng bộ nhóm hỏng:", e?.message || e)), 5000);
}

function onMessage(m) {
  const d = m.data || {};
  const group = m.type === ThreadType.Group;
  push({
    kind: "message",
    thread_type: group ? "group" : "user",
    thread_id: String(m.threadId || ""),
    thread_name: group ? groupNames.get(String(m.threadId)) || "" : "",
    is_self: Boolean(m.isSelf),
    msg_id: String(d.msgId || ""),
    msg_type: String(d.msgType || ""),
    from_uid: String(d.uidFrom || ""),
    from_name: String(d.dName || ""),
    ts: Number(d.ts || 0),
    content: text(d.content) ?? (d.content && typeof d.content === "object" ? d.content : null),
  });
}

const refreshTimers = new Map();

function scheduleGroupRefresh(groupId, extra = {}) {
  clearTimeout(refreshTimers.get(groupId));
  refreshTimers.set(groupId, setTimeout(() => {
    refreshTimers.delete(groupId);
    pushGroup(groupId, extra).catch((e) => log("đọc nhóm hỏng:", e?.message || e));
  }, 3000));
}

async function onGroupEvent(ev) {
  const groupId = String(ev.threadId || "");
  if (!groupId) return;
  const d = ev.data || {};
  const selfTouched = Array.isArray(d.updateMembers) && d.updateMembers.some((x) => String(x?.id) === state.uid);
  if ((ev.type === GroupEventType.LEAVE || ev.type === GroupEventType.REMOVE_MEMBER
       || ev.type === GroupEventType.BLOCK_MEMBER) && selfTouched) {
    push({ kind: "group", group_id: groupId, left: true });
    return;
  }
  if (ev.type === GroupEventType.JOIN && selfTouched) {
    scheduleGroupRefresh(groupId, { added_by: String(d.sourceId || "") });
    return;
  }
  if ([GroupEventType.JOIN, GroupEventType.LEAVE, GroupEventType.REMOVE_MEMBER, GroupEventType.BLOCK_MEMBER,
       GroupEventType.UPDATE].includes(ev.type)) {
    scheduleGroupRefresh(groupId);
  }
}

function memberIdsOf(info) {
  // memVerList đủ mọi thành viên («uid_phiênbản»); memberIds có thể bị cắt ở nhóm đông.
  if (Array.isArray(info.memVerList) && info.memVerList.length) {
    return info.memVerList.map((x) => String(x).split("_")[0]).filter(Boolean);
  }
  return Array.isArray(info.memberIds) ? info.memberIds.map(String) : [];
}

async function pushGroup(groupId, extra = {}) {
  if (!api) return;
  const res = await api.getGroupInfo(groupId);
  const info = res?.gridInfoMap?.[groupId];
  if (!info) return;
  groupNames.set(groupId, String(info.name || ""));
  push({ kind: "group", group_id: groupId, name: String(info.name || ""), member_ids: memberIdsOf(info), ...extra });
}

async function syncGroups() {
  if (!api) return 0;
  const all = await api.getAllGroups();
  const ids = Object.keys(all?.gridVerMap || {});
  for (let i = 0; i < ids.length; i += 20) {
    const chunk = ids.slice(i, i + 20);
    const res = await api.getGroupInfo(chunk);
    for (const id of chunk) {
      const info = res?.gridInfoMap?.[id];
      if (!info) continue;
      groupNames.set(id, String(info.name || ""));
      push({ kind: "group", group_id: id, name: String(info.name || ""), member_ids: memberIdsOf(info) });
    }
    await sleep(1000);
  }
  state.groups = ids.length;
  return ids.length;
}

function scheduleRelogin() {
  if (reloginTimer) return;
  reloginTimer = setTimeout(async () => {
    reloginTimer = null;
    if (state.value === "connected" || loggingIn) return;
    const ok = await loginFromSession();
    if (!ok) scheduleRelogin();
  }, RELOGIN_MIN * 60 * 1000);
}

async function loginFromSession() {
  const creds = await loadSession();
  if (!creds) return false;
  try {
    stopListener();
    const zalo = new Zalo({ selfListen: false, checkUpdate: false, logging: false });
    await attach(await zalo.login(creds));
    return true;
  } catch (e) {
    setState("down", { reason: `phiên cũ không dùng được (${e?.message || e})` });
    return false;
  }
}

function stopListener() {
  try {
    api?.listener?.stop();
  } catch {
    /* đã dừng */
  }
  api = null;
}

async function loginQR() {
  if (loggingIn) return;
  loggingIn = true;
  setState("qr");
  try {
    stopListener();
    const zalo = new Zalo({ selfListen: false, checkUpdate: false, logging: false });
    const newApi = await zalo.loginQR({ userAgent: USER_AGENT }, async (ev) => {
      if (ev.type === LoginQRCallbackEventType.QRCodeGenerated) {
        push({ kind: "qr", image: String(ev.data?.image || "") });
      } else if (ev.type === LoginQRCallbackEventType.QRCodeExpired) {
        push({ kind: "qr", expired: true });
        ev.actions?.abort?.();
      } else if (ev.type === LoginQRCallbackEventType.QRCodeScanned) {
        state.name = String(ev.data?.display_name || "");
      } else if (ev.type === LoginQRCallbackEventType.QRCodeDeclined) {
        push({ kind: "status", state: "down", reason: "người quét đã từ chối đăng nhập" });
        ev.actions?.abort?.();
      } else if (ev.type === LoginQRCallbackEventType.GotLoginInfo) {
        await saveSession({ cookie: ev.data.cookie, imei: ev.data.imei, userAgent: ev.data.userAgent });
      }
    });
    if (newApi) await attach(newApi);
    else setState("idle");
  } catch (e) {
    log("đăng nhập QR hỏng:", e?.message || e);
    state.value = "idle";
  } finally {
    loggingIn = false;
  }
}

// ---------------------------------------------------------------------------
// Gửi — một hàng, giãn nhịp
// ---------------------------------------------------------------------------
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let sendChain = Promise.resolve();
let queued = 0;
let lastSend = 0;

function enqueueSend(job) {
  queued += 1;
  const run = sendChain.then(async () => {
    const wait = lastSend + SEND_GAP_MS + Math.floor(Math.random() * 700) - Date.now();
    if (wait > 0) await sleep(wait);
    try {
      return await job();
    } finally {
      lastSend = Date.now();
      queued -= 1;
    }
  });
  sendChain = run.catch(() => {});
  return run;
}

async function doSend(body) {
  if (!api || state.value !== "connected") throw new Error("Zalo chưa kết nối");
  const threadId = String(body.thread_id || "");
  if (!/^\d{1,40}$/.test(threadId)) throw new Error("thread_id không hợp lệ");
  const type = body.thread_type === "group" ? ThreadType.Group : ThreadType.User;
  const content = { msg: String(body.text || "").slice(0, 4000) };
  if (body.file && body.file.b64) {
    const data = Buffer.from(String(body.file.b64), "base64");
    let filename = String(body.file.name || "tep.bin").replace(/[\\/:*?"<>|]/g, "_").slice(0, 150);
    if (!/\.[A-Za-z0-9]{1,8}$/.test(filename)) filename += ".bin";
    content.attachments = [{ data, filename, metadata: { totalSize: data.length } }];
  }
  if (!content.msg && !content.attachments) throw new Error("tin rỗng");
  const res = await enqueueSend(() => api.sendMessage(content, threadId, type));
  const first = res?.message || res?.attachment?.[0] || {};
  return String(first.msgId || "");
}

// ---------------------------------------------------------------------------
// HTTP
// ---------------------------------------------------------------------------
function reply(res, code, obj) {
  const raw = Buffer.from(JSON.stringify(obj));
  res.writeHead(code, { "Content-Type": "application/json", "Content-Length": raw.length });
  res.end(raw);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (c) => {
      size += c.length;
      if (size > MAX_BODY) {
        reject(new Error("quá lớn"));
        req.destroy();
        return;
      }
      chunks.push(c);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

async function handle(req, res) {
  const url = new URL(req.url, "http://x");
  if (req.method === "GET" && url.pathname === "/health") {
    return reply(res, 200, { ok: true, state: state.value });
  }
  const body = await readBody(req);
  const bad = verify(req, url.pathname, body);
  if (bad) return reply(res, 401, { ok: false, error: bad });
  const json = body.length ? JSON.parse(body.toString("utf8")) : {};

  if (req.method === "GET" && url.pathname === "/updates") {
    const offset = Number(url.searchParams.get("offset") || 0);
    const timeout = Math.min(Math.max(Number(url.searchParams.get("timeout") || 0), 0), 50);
    ack(offset);
    if (!pending(offset).length && timeout > 0) {
      await new Promise((resolve) => {
        const t = setTimeout(() => {
          waiters.delete(resolve);
          resolve();
        }, timeout * 1000);
        waiters.add(() => {
          clearTimeout(t);
          resolve();
        });
      });
    }
    return reply(res, 200, { ok: true, events: pending(offset).slice(0, 100) });
  }
  if (req.method === "POST" && url.pathname === "/send") {
    try {
      return reply(res, 200, { ok: true, msg_id: await doSend(json) });
    } catch (e) {
      return reply(res, 409, { ok: false, error: String(e?.message || e) });
    }
  }
  if (req.method === "POST" && url.pathname === "/login") {
    if (state.value === "connected") return reply(res, 200, { ok: true, state: state.value });
    loginQR();
    return reply(res, 200, { ok: true, state: "qr" });
  }
  if (req.method === "POST" && url.pathname === "/groups/refresh") {
    syncGroups().catch((e) => log("đồng bộ nhóm hỏng:", e?.message || e));
    return reply(res, 200, { ok: true });
  }
  if (req.method === "GET" && url.pathname === "/status") {
    return reply(res, 200, { ok: true, state: state.value, name: state.name, uid: state.uid,
                             groups: state.groups ?? null, queued, since: state.since, reason: state.reason });
  }
  return reply(res, 404, { ok: false, error: "không có đường này" });
}

export function startServer() {
  const server = http.createServer((req, res) => {
    handle(req, res).catch((e) => reply(res, 500, { ok: false, error: String(e?.message || e) }));
  });
  server.requestTimeout = 120_000;
  server.listen(PORT, () => log(`zalo-listener nghe cổng ${PORT}`));
  return server;
}

if (process.env.ZALO_LISTENER_NO_START !== "1") {
  if (!SECRET) log("CẢNH BÁO: chưa khai AGENT_SERVICE_SECRET — mọi lượt gọi sẽ bị từ chối");
  startServer();
  loginFromSession().then((ok) => {
    if (!ok && state.value !== "down") log("chưa có phiên — chờ lệnh /zalo dangnhap để quét QR");
  });
  setInterval(() => {
    if (state.value === "connected") syncGroups().catch((e) => log("đồng bộ nhóm hỏng:", e?.message || e));
  }, GROUP_SYNC_MIN * 60 * 1000);
}
