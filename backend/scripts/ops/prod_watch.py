#!/usr/bin/env python3
"""bao-CR-735 — CANH PROD TỪ NGOÀI. Chạy trên VPS 2 (dev), systemd timer dego-prod-watch.timer mỗi phút.

Gọi WATCH_URL (mặc định https://thumua.degoholding.vn/api/health — đi qua Cloudflare như người dùng thật). Hỏng
FAIL_THRESHOLD lượt liền (mặc định 2) thì báo Telegram MỘT lần; còn hỏng thì nhắc lại mỗi REMIND_MINUTES phút
(mặc định 60, 0 = không nhắc); trả lời lại thì báo đã hồi kèm thời gian đứng. Không gửi lặp mỗi phút.

Chỉ thư viện chuẩn. Biến lấy từ môi trường (systemd EnvironmentFile=/etc/dego/alert.env, chmod 600):
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID; tùy chọn WATCH_URL, WATCH_NAME, FAIL_THRESHOLD, REMIND_MINUTES, WATCH_TIMEOUT,
WATCH_STATE. Khóa không bao giờ in ra log.

    python3 prod_watch.py            # một lượt kiểm (timer gọi)
    python3 prod_watch.py --test     # gửi thử một tin, không đụng trạng thái
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_URL = "https://thumua.degoholding.vn/api/health"
DEFAULT_STATE = "/var/lib/dego-prod-watch/state.json"
USER_AGENT = "dego-prod-watch/1 (bao-CR-735)"

EMPTY = {"fails": 0, "down_since": None, "alerted": False, "last_alert": None, "last_detail": ""}


def probe(url: str, timeout: float) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(512)
            if resp.status == 200 and b'"success":true' in body.replace(b" ", b""):
                return True, "ok"
            return False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 — hết giờ, DNS, TLS... đều là hỏng
        return False, f"{type(exc).__name__}: {exc}"[:200]


def hhmm(epoch: float) -> str:
    return time.strftime("%H:%M %d/%m", time.localtime(epoch))


def minutes(seconds: float) -> int:
    return max(1, round(seconds / 60))


def step(state: dict, ok: bool, detail: str, now: float, *, name: str, url: str,
         threshold: int = 2, remind_minutes: int = 60) -> tuple[dict, str | None]:
    """Một lượt kiểm → (trạng thái mới, tin cần gửi hoặc None). Hàm thuần, không I/O."""
    state = {**EMPTY, **(state or {})}
    if ok:
        if state["alerted"]:
            since = state["down_since"] or now
            msg = (f"[ĐÃ HỒI] {name} trả lời lại lúc {hhmm(now)}. Đứng khoảng {minutes(now - since)} phút "
                   f"(từ {hhmm(since)}).")
            return dict(EMPTY), msg
        return dict(EMPTY), None

    state["fails"] += 1
    state["down_since"] = state["down_since"] or now
    state["last_detail"] = detail
    if not state["alerted"]:
        if state["fails"] >= threshold:
            state["alerted"], state["last_alert"] = True, now
            return state, (f"[CẢNH BÁO] {name} KHÔNG trả lời {state['fails']} lượt liền (từ {hhmm(state['down_since'])})."
                           f" Lỗi: {detail}. Địa chỉ kiểm: {url}")
        return state, None
    if remind_minutes > 0 and now - (state["last_alert"] or now) >= remind_minutes * 60:
        state["last_alert"] = now
        return state, (f"[VẪN HỎNG] {name} đã đứng khoảng {minutes(now - state['down_since'])} phút "
                       f"(từ {hhmm(state['down_since'])}). Lỗi gần nhất: {detail}")
    return state, None


def keep_unsent(old: dict, new: dict, ok: bool) -> dict:
    """Gửi tin hỏng thì lượt sau phải thử gửi lại, không nuốt mất tin."""
    old = {**EMPTY, **(old or {})}
    if ok:
        return old  # tin "đã hồi" chưa đi — giữ nguyên để lượt sau tính lại từ mốc đứng cũ
    return {**new, "alerted": old["alerted"], "last_alert": old["last_alert"]}


def send_telegram(token: str, chat_id: str, text: str, timeout: float = 15) -> bool:
    if not token or not chat_id:
        print("chưa khai TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID — không gửi được tin")
        return False
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data,
                                 headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        print(f"Telegram từ chối: HTTP {exc.code}")  # KHÔNG in exc.url — có khóa
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"Telegram lỗi: {type(exc).__name__}")
        return False


def load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return dict(EMPTY)


def save(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, path)


def main(argv: list[str]) -> int:
    env = os.environ
    url = env.get("WATCH_URL", DEFAULT_URL)
    name = env.get("WATCH_NAME", "Prod thumua")
    token, chat = env.get("TELEGRAM_BOT_TOKEN", ""), env.get("TELEGRAM_CHAT_ID", "")
    if "--test" in argv:
        sent = send_telegram(token, chat, f"[THỬ] Bộ canh {name} ({url}) gửi được tin. Không cần làm gì.")
        print("đã gửi tin thử" if sent else "gửi thử thất bại")
        return 0 if sent else 1

    path = env.get("WATCH_STATE", DEFAULT_STATE)
    old = load(path)
    ok, detail = probe(url, float(env.get("WATCH_TIMEOUT", "10")))
    new, msg = step(old, ok, detail, time.time(), name=name, url=url,
                    threshold=int(env.get("FAIL_THRESHOLD", "2")),
                    remind_minutes=int(env.get("REMIND_MINUTES", "60")))
    if not ok:
        print(f"hỏng lượt {new['fails']}: {detail}")
    if msg:
        sent = send_telegram(token, chat, msg)
        print(("đã báo: " if sent else "CHƯA báo được: ") + msg.split(".")[0])
        if not sent:
            new = keep_unsent(old, new, ok)
    save(path, new)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
