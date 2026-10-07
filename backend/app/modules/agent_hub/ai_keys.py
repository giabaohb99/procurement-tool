"""Sổ khóa AI MỘT BẢNG cho cả công ty lẫn từng người (ai-CR-098, nhóm C-04 — đại ca chốt 07/10/2026).

`tab_ai_key`: `owner_type` 1 công ty · 2 cá nhân; `owner_id` 0 với công ty, `user_id` với cá nhân; `provider`
gemini · claude · openai · openrouter; `model` mặc định cho khóa đó (trống = mặc định của hãng); `priority` 1 = chính,
2, 3… dự phòng (hỏng vì hết tiền / hạn mức / khóa sai thì nhảy sang); `daily_cap` trần lượt/ngày riêng cho khóa
(0 = theo trần chung). Khóa mã hóa Fernet, chỉ giữ 4 ký tự cuối; gỡ = `revoked_at`, giữ lịch sử.

Nguồn khóa theo thứ tự: dòng cá nhân (theo priority) → dòng công ty (theo priority) → `.env` (đường lùi cũ của bot).
Khóa công ty của Trợ lý web vẫn đọc thêm ở cấu hình hệ thống (`tab_setting`) khi bảng này chưa có dòng công ty — xem
`assistant/provider/*._api_key()`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import app_settings

from .model import AiKey

OWNER_COMPANY = 1
OWNER_USER = 2

PROVIDER_GEMINI = "gemini"
PROVIDER_CLAUDE = "claude"
PROVIDER_OPENAI = "openai"
PROVIDER_OPENROUTER = "openrouter"
PROVIDER_DEEPSEEK = "deepseek"      # ai-CR-107
PROVIDER_XAI = "xai"                # ai-CR-107: Grok
#  ai-CR-108: trạm trung gian / máy chủ tự dựng nói API kiểu OpenAI (vd modelapi.vn) — địa chỉ trạm nhập theo từng khóa.
PROVIDER_CUSTOM = "openai_compat"
PROVIDERS = (PROVIDER_GEMINI, PROVIDER_CLAUDE, PROVIDER_OPENAI, PROVIDER_OPENROUTER, PROVIDER_DEEPSEEK, PROVIDER_XAI,
             PROVIDER_CUSTOM)
PROVIDER_LABELS = {PROVIDER_GEMINI: "Gemini", PROVIDER_CLAUDE: "Claude", PROVIDER_OPENAI: "OpenAI",
                   PROVIDER_OPENROUTER: "OpenRouter", PROVIDER_DEEPSEEK: "DeepSeek", PROVIDER_XAI: "Grok (xAI)",
                   PROVIDER_CUSTOM: "Tương thích OpenAI (tùy chỉnh)"}
#  Trang lấy khóa — bot chỉ cách, không bao giờ nhận khóa qua chat.
PROVIDER_SITES = {PROVIDER_GEMINI: "https://aistudio.google.com/apikey", PROVIDER_CLAUDE: "https://console.anthropic.com/",
                  PROVIDER_OPENAI: "https://platform.openai.com/api-keys", PROVIDER_OPENROUTER: "https://openrouter.ai/keys",
                  PROVIDER_DEEPSEEK: "https://platform.deepseek.com/api_keys", PROVIDER_XAI: "https://console.x.ai",
                  PROVIDER_CUSTOM: ""}

PROBE_TIMEOUT = 15
_COMPANY_TTL = 60.0
_company_cache: tuple[float, list["KeyRef"]] | None = None


class InvalidKey(ValueError):
    """Khóa không được hãng chấp nhận (sai, bị thu hồi, hoặc dự án chưa bật API)."""


@dataclass(frozen=True)
class KeyRef:
    """Một khóa đã giải mã, sẵn sàng dùng cho lượt gọi. KHÔNG BAO GIỜ in `key` ra log / chat / sổ."""

    provider: str
    key: str
    model: str = ""
    owner_type: int = OWNER_USER
    owner_id: int = 0
    row_id: int = 0
    hint: str = ""
    priority: int = 1
    daily_cap: int = 0
    source: str = "db"      # db · env
    base_url: str = ""      # ai-CR-108: chỉ hãng tùy chỉnh


# ---------------------------------------------------------------------------
# Địa chỉ trạm tùy chỉnh (ai-CR-108)
# ---------------------------------------------------------------------------
def normalize_base_url(url: str) -> str:
    """Chỉ nhận `https://<tên miền công khai>[/đường dẫn]`. Chặn localhost / IP nội bộ / http — máy chủ gửi KHÓA tới địa
    chỉ này, để mở là lỗ dò mạng nội bộ (SSRF) và lộ khóa."""
    import ipaddress
    from urllib.parse import urlparse

    url = (url or "").strip().rstrip("/")
    u = urlparse(url)
    host = (u.hostname or "").lower()
    if u.scheme != "https" or not host or u.username or u.password:
        raise InvalidKey("Địa chỉ trạm phải dạng https://ten-mien/v1.")
    if host in ("localhost",) or host.endswith((".local", ".internal", ".localhost")) or "." not in host:
        raise InvalidKey("Địa chỉ trạm phải là tên miền công khai.")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved):
        raise InvalidKey("Địa chỉ trạm phải là tên miền công khai.")
    return url[:200]


def custom_models(base_url: str, raw: str) -> list[str]:
    """Danh sách model của trạm tùy chỉnh (GET /models, không tốn token)."""
    try:
        r = requests.get(f"{base_url}/models", headers={"authorization": f"Bearer {raw}"}, timeout=PROBE_TIMEOUT)
    except requests.RequestException as e:
        raise InvalidKey(f"Không gọi được trạm {base_url}: {type(e).__name__}") from e
    if r.status_code in (400, 401, 403):
        raise InvalidKey("Trạm không nhận khóa này (sai hoặc đã thu hồi).")
    if r.status_code != 200:
        raise InvalidKey(f"Trạm trả lỗi {r.status_code} khi kiểm khóa.")
    try:
        return [str(m.get("id")) for m in (r.json() or {}).get("data", []) if m.get("id")]
    except ValueError:
        return []


# ---------------------------------------------------------------------------
# Kiểm khóa với từng hãng — một lượt GET không tốn token
# ---------------------------------------------------------------------------
def _probe(provider: str, raw: str) -> int:
    try:
        if provider == PROVIDER_GEMINI:
            r = requests.get("https://generativelanguage.googleapis.com/v1beta/models?pageSize=1",
                             headers={"x-goog-api-key": raw}, timeout=PROBE_TIMEOUT)
        elif provider == PROVIDER_CLAUDE:
            r = requests.get("https://api.anthropic.com/v1/models?limit=1",
                             headers={"x-api-key": raw, "anthropic-version": "2023-06-01"}, timeout=PROBE_TIMEOUT)
        elif provider == PROVIDER_OPENAI:
            r = requests.get("https://api.openai.com/v1/models", headers={"authorization": f"Bearer {raw}"},
                             timeout=PROBE_TIMEOUT)
        elif provider == PROVIDER_DEEPSEEK:
            r = requests.get("https://api.deepseek.com/models", headers={"authorization": f"Bearer {raw}"},
                             timeout=PROBE_TIMEOUT)
        elif provider == PROVIDER_XAI:
            r = requests.get("https://api.x.ai/v1/models", headers={"authorization": f"Bearer {raw}"},
                             timeout=PROBE_TIMEOUT)
        elif provider == PROVIDER_OPENROUTER:
            r = requests.get("https://openrouter.ai/api/v1/key", headers={"authorization": f"Bearer {raw}"},
                             timeout=PROBE_TIMEOUT)
        else:
            raise InvalidKey(f"Chưa hỗ trợ hãng «{provider}».")
    except requests.RequestException as e:
        raise InvalidKey(f"Không gọi được {PROVIDER_LABELS.get(provider, provider)} để kiểm khóa: {e}") from e
    return r.status_code


def verify(provider: str, raw: str) -> None:
    raw = (raw or "").strip()
    if provider not in PROVIDERS or provider == PROVIDER_CUSTOM:
        raise InvalidKey(f"Chưa hỗ trợ hãng «{provider}».")
    if len(raw) < 20 or " " in raw:
        raise InvalidKey("Khóa không đúng dạng.")
    code = _probe(provider, raw)
    label = PROVIDER_LABELS[provider]
    if code in (400, 401, 403):
        raise InvalidKey(f"{label} không nhận khóa này (sai, đã thu hồi, hoặc dự án chưa bật API).")
    if code != 200:
        raise InvalidKey(f"{label} trả lỗi {code} khi kiểm khóa, thử lại sau.")


# ---------------------------------------------------------------------------
# Sổ khóa
# ---------------------------------------------------------------------------
def _ref(row: AiKey) -> KeyRef:
    return KeyRef(provider=row.provider, key=app_settings._decrypt(row.key_enc), model=row.model or "",
                  owner_type=int(row.owner_type), owner_id=int(row.owner_id), row_id=int(row.id),
                  hint=row.key_hint, priority=int(row.priority or 1), daily_cap=int(row.daily_cap or 0),
                  base_url=row.base_url or "")


def active_rows(db: Session, owner_type: int, owner_id: int) -> list[AiKey]:
    return list(db.scalars(select(AiKey).where(AiKey.owner_type == owner_type, AiKey.owner_id == int(owner_id),
                                               AiKey.revoked_at.is_(None))
                           .order_by(AiKey.priority.asc(), AiKey.id.desc())))


def used_today(db: Session, key_ids: list[int]) -> dict[int, int]:
    """Số lượt model hôm nay theo từng dòng khóa (cột `tab_agent_run.key_id`)."""
    ids = [int(i) for i in key_ids if int(i or 0) > 0]
    if not ids:
        return {}
    from sqlalchemy import func

    from .model import AgentRun
    from .timeutil import now_local, to_utc

    since = to_utc(now_local().replace(hour=0, minute=0, second=0, microsecond=0))
    rows = db.execute(select(AgentRun.key_id, func.count(AgentRun.id)).where(
        AgentRun.key_id.in_(ids), AgentRun.started_at >= since).group_by(AgentRun.key_id)).all()
    return {int(k): int(n) for k, n in rows}


def _under_cap(db: Session, refs: list[KeyRef]) -> list[KeyRef]:
    """Bỏ khóa đã chạm trần riêng hôm nay (`daily_cap` > 0). Khóa không khai trần thì giữ."""
    capped = [r for r in refs if r.daily_cap > 0]
    if not capped:
        return refs
    used = used_today(db, [r.row_id for r in capped])
    return [r for r in refs if r.daily_cap <= 0 or used.get(r.row_id, 0) < r.daily_cap]


def chain_for_user(db: Session, user_id: int) -> list[KeyRef]:
    if int(user_id or 0) <= 0:
        return []
    return _under_cap(db, [_ref(r) for r in active_rows(db, OWNER_USER, user_id)])


def company_chain(db: Session | None = None) -> list[KeyRef]:
    """Dòng công ty theo ưu tiên. Có bộ đệm 60 giây vì provider của Trợ lý web gọi mỗi lượt."""
    global _company_cache
    now = time.monotonic()
    if _company_cache is not None and _company_cache[0] > now:
        return list(_company_cache[1])
    own = db is None
    if own:
        from app.core.database import SessionLocal

        db = SessionLocal()
    try:
        refs = [_ref(r) for r in active_rows(db, OWNER_COMPANY, 0)]
    except Exception:  # noqa: BLE001 — bảng chưa có (migration chưa chạy) thì coi như rỗng
        refs = []
    finally:
        if own:
            db.close()
    _company_cache = (now + _COMPANY_TTL, refs)
    return list(refs)


def company_chain_for_bot(db: Session) -> list[KeyRef]:
    """Chuỗi khóa công ty cho bot — đọc thẳng (không đệm) để áp trần riêng từng khóa theo số lượt hôm nay."""
    return _under_cap(db, [_ref(r) for r in active_rows(db, OWNER_COMPANY, 0)])


def company_key(provider: str) -> str:
    """Khóa công ty ưu tiên cao nhất của một hãng, hoặc rỗng."""
    for ref in company_chain():
        if ref.provider == provider:
            return ref.key
    return ""


def clear_cache() -> None:
    global _company_cache
    _company_cache = None


def add_key(db: Session, *, owner_type: int, owner_id: int, provider: str, raw: str, model: str = "",
            priority: int = 0, daily_cap: int = 0, by_user: int = 0, check: bool = True, base_url: str = "") -> AiKey:
    """Kiểm với hãng rồi lưu mã hóa. Cùng chủ + cùng hãng + cùng ưu tiên thì đóng dòng cũ (thay khóa).
    Hãng tùy chỉnh (ai-CR-108): bắt buộc `base_url`; chưa chọn model thì lấy model đầu tiên trạm liệt kê."""
    raw = (raw or "").strip()
    if provider == PROVIDER_CUSTOM:
        base_url = normalize_base_url(base_url)
        if len(raw) < 20 or " " in raw:
            raise InvalidKey("Khóa không đúng dạng.")
        models = custom_models(base_url, raw) if check else []
        if not model:
            if not models:
                raise InvalidKey("Trạm không liệt kê model nào — nhập tên model ở «Tùy chọn».")
            model = models[0]
    else:
        base_url = ""
        if check:
            verify(provider, raw)
        elif provider not in PROVIDERS:
            raise InvalidKey(f"Chưa hỗ trợ hãng «{provider}».")
    rows = active_rows(db, owner_type, owner_id)
    if priority <= 0:
        same = [r for r in rows if r.provider == provider]
        priority = int(same[0].priority) if same else (max((int(r.priority) for r in rows), default=0) + 1)
    now = datetime.now()
    for old in rows:
        if old.provider == provider and int(old.priority) == priority:
            old.revoked_at = now
    row = AiKey(owner_type=owner_type, owner_id=int(owner_id), provider=provider, model=(model or "")[:80],
                base_url=base_url,
                priority=priority, daily_cap=max(0, int(daily_cap or 0)), key_enc=app_settings.encrypt(raw),
                key_hint=raw[-4:], verified_at=now, created_by=by_user, updated_by=by_user)
    db.add(row)
    db.commit()
    clear_cache()
    return row


def update_key(db: Session, row_id: int, *, owner_type: int, owner_id: int, model: str | None = None,
               priority: int | None = None, daily_cap: int | None = None) -> AiKey | None:
    row = db.get(AiKey, int(row_id))
    if row is None or int(row.owner_type) != owner_type or int(row.owner_id) != int(owner_id) or row.revoked_at:
        return None
    if model is not None:
        row.model = model[:80]
    if priority is not None and priority > 0:
        row.priority = priority
    if daily_cap is not None:
        row.daily_cap = max(0, int(daily_cap))
    db.commit()
    clear_cache()
    return row


def revoke_key(db: Session, row_id: int, *, owner_type: int, owner_id: int) -> bool:
    row = db.get(AiKey, int(row_id))
    if row is None or int(row.owner_type) != owner_type or int(row.owner_id) != int(owner_id) or row.revoked_at:
        return False
    row.revoked_at = datetime.now()
    db.commit()
    clear_cache()
    return True


def revoke_all(db: Session, owner_type: int, owner_id: int) -> int:
    now = datetime.now()
    n = 0
    for row in active_rows(db, owner_type, owner_id):
        row.revoked_at = now
        n += 1
    if n:
        db.commit()
        clear_cache()
    return n


def describe_rows(rows: list[AiKey], db: Session | None = None) -> list[dict]:
    used = used_today(db, [int(r.id) for r in rows]) if db is not None else {}
    return [{
        "id": r.id, "provider": r.provider, "provider_label": PROVIDER_LABELS.get(r.provider, r.provider),
        "model": r.model or "", "priority": int(r.priority or 1), "daily_cap": int(r.daily_cap or 0),
        "hint": f"…{r.key_hint}", "verified_at": r.verified_at.isoformat(timespec="seconds") if r.verified_at else None,
        "used_today": used.get(int(r.id), 0),
        "base_url": r.base_url or "",
    } for r in rows]


def key_problem(error: str, provider: str = "") -> str:
    """ai-CR-097: lỗi nào là CHUYỆN CỦA KHÓA (hết tiền, hết hạn mức, khóa sai) → câu nói thẳng. Khác → rỗng.

    Chuỗi khóa (ai-CR-098) dựa vào đúng hàm này để biết khi nào nhảy sang khóa kế.
    """
    e = (error or "").lower()
    label = PROVIDER_LABELS.get(provider, "AI") if provider else "Gemini"
    site = PROVIDER_SITES.get(provider or PROVIDER_GEMINI, "")
    if "402" in e or "depleted" in e or "prepayment" in e or "billing" in e or "insufficient" in e:
        return (f"Khóa {label} của đại ca <b>hết tiền</b> (hãng báo 402). Nạp thêm ở {site} rồi nhắn lại câu vừa rồi; "
                "hoặc thêm khóa khác ở ERP → Trang cá nhân → Khóa AI.")
    if "429" in e or "resource_exhausted" in e or "quota" in e or "rate limit" in e:
        return (f"Khóa {label} của đại ca <b>hết hạn mức</b> tạm thời (429). Chờ một phút rồi nhắn lại; "
                "lặp lại nhiều thì nâng hạn mức hoặc thêm khóa dự phòng ở Trang cá nhân → Khóa AI.")
    if ("api key not valid" in e or "api_key_invalid" in e or "permission_denied" in e or " 403" in e or "401" in e
            or "invalid_api_key" in e or "authentication_error" in e):
        return (f"Khóa {label} của đại ca <b>không còn hợp lệ</b> (hãng từ chối). Lấy khóa mới ở {site} rồi dán lại "
                "ở ERP → Trang cá nhân → Khóa AI.")
    return ""


def is_key_problem(error: str) -> bool:
    return bool(key_problem(error))


def is_transient(error: str) -> bool:
    """ai-CR-099: hãng quá tải tạm thời (503 «high demand», 500, 504) — thử lại một lần là thường qua."""
    e = (error or "").lower()
    return any(k in e for k in (" 503", "lỗi 503", "unavailable", "high demand", "overloaded", " 500:", " 504",
                                "deadline", "timed out", "timeout"))


def short_error(error: str) -> str:
    """Một câu ngắn thay cho cục JSON của hãng (ai-CR-099: đại ca thấy trả lời «không mượt»)."""
    if problem := key_problem(error):
        return problem
    if is_transient(error):
        return "Gemini đang quá tải tạm thời, em đã thử lại mà chưa được. Đại ca nhắn lại sau ít phút giúp em."
    return "Em gặp lỗi khi gọi AI, đại ca nhắn lại giúp em. Lặp lại nhiều thì báo em xem sổ chạy."
