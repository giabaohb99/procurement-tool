"""Khóa AI của NGƯỜI ĐANG CHAT + chuỗi khóa dự phòng (ai-CR-053 D-01; ai-CR-098 C-04).

Đại ca chốt 24/09/2026: bot trên dev là trợ lý của TỪNG NGƯỜI, mỗi người dán khóa của mình ở Trang cá nhân → «Khóa AI»
(web, KHÔNG qua chat: Telegram giữ lịch sử vĩnh viễn). Đại ca chốt 07/10/2026 (ai-CR-098): nhiều khóa, nhiều hãng
(Gemini · Claude · OpenAI · OpenRouter) theo ƯU TIÊN; khóa hỏng vì hết tiền / hạn mức / khóa sai thì tự nhảy sang
khóa kế, hết khóa cá nhân thì về khóa CÔNG TY có trần lượt/ngày, KHÔNG nhắn gì khi đổi khóa — ai hỏi «còn khóa nào»
thì liệt kê. Sổ khóa chung cho cả công ty lẫn cá nhân nằm ở `ai_keys.py` (`tab_ai_key`).

Chuỗi khóa của lượt gọi hiện tại nằm trong ContextVar: `service` mở ngữ cảnh (`for_chat` / `for_admin`) quanh mỗi tin
nhắn hoặc việc nền; provider của bot (`manager.AgentGeminiProvider`) đọc `active_ref()` và gọi `advance()` khi khóa
đang dùng hỏng vì chuyện của khóa. Ngoài mọi ngữ cảnh (bài kiểm, script) thì lùi về `AGENT_GEMINI_API_KEY` như cũ.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings

from . import ai_keys, chat_link, telegram
from .ai_keys import OWNER_USER, PROVIDER_GEMINI, InvalidKey, KeyRef  # noqa: F401 — bí danh tương thích
from .model import AiKey

NO_KEY_HELP = ("Chat này chưa gắn khóa AI (công ty cũng chưa khai khóa chung) nên em chưa trả lời câu hỏi AI được. "
               "Vào ERP → <b>Trang cá nhân → Khóa AI</b>, dán khóa Gemini / Claude / OpenAI / OpenRouter của anh/chị rồi "
               "hỏi lại. Đăng nhập, xem tình trạng việc, ra lệnh trên việc vẫn dùng được, không cần khóa.")

_ctx_open: ContextVar[bool] = ContextVar("agent_key_ctx", default=False)
_ctx_chain: ContextVar[tuple] = ContextVar("agent_key_chain", default=())
_ctx_idx: ContextVar[int] = ContextVar("agent_key_idx", default=0)
_ctx_owner: ContextVar[int] = ContextVar("agent_key_owner", default=0)


# ---------------------------------------------------------------------------
# Ngữ cảnh lượt gọi
# ---------------------------------------------------------------------------
def env_ref() -> KeyRef | None:
    key = settings.AGENT_GEMINI_API_KEY
    return KeyRef(provider=PROVIDER_GEMINI, key=key, owner_type=ai_keys.OWNER_COMPANY, source="env") if key else None


def active_ref() -> KeyRef | None:
    """Khóa đang dùng cho lượt gọi hiện tại. Ngoài ngữ cảnh: khóa `.env` (hành vi cũ)."""
    if not _ctx_open.get():
        return env_ref()
    chain = _ctx_chain.get()
    idx = _ctx_idx.get()
    return chain[idx] if 0 <= idx < len(chain) else None


def active_key() -> str:
    ref = active_ref()
    return ref.key if ref is not None else ""


def active_provider() -> str:
    ref = active_ref()
    return ref.provider if ref is not None else PROVIDER_GEMINI


def active_owner() -> int:
    return _ctx_owner.get()


def in_context() -> bool:
    return _ctx_open.get()


def chain() -> list[KeyRef]:
    return list(_ctx_chain.get()) if _ctx_open.get() else [r for r in (env_ref(),) if r]


def advance() -> bool:
    """Khóa đang dùng hỏng vì chuyện của khóa → nhảy sang khóa kế. False = hết khóa."""
    if not _ctx_open.get():
        return False
    nxt = _ctx_idx.get() + 1
    if nxt >= len(_ctx_chain.get()):
        return False
    _ctx_idx.set(nxt)
    return True


def gemini_key() -> str:
    """Khóa GEMINI cho việc chỉ Gemini làm được (nhúng vector, tìm Google): khóa Gemini trong chuỗi từ vị trí hiện tại,
    rồi bất kỳ khóa Gemini nào trong chuỗi, rồi khóa Gemini công ty, rồi `.env`."""
    refs = chain()
    idx = _ctx_idx.get() if _ctx_open.get() else 0
    for ref in refs[idx:] + refs[:idx]:
        if ref.provider == PROVIDER_GEMINI and ref.key:
            return ref.key
    return ai_keys.company_key(PROVIDER_GEMINI) or settings.AGENT_GEMINI_API_KEY


@contextmanager
def use_chain(refs: list[KeyRef], owner: int = 0):
    tokens = (_ctx_open.set(True), _ctx_chain.set(tuple(refs)), _ctx_idx.set(0), _ctx_owner.set(int(owner or 0)))
    try:
        yield refs[0].key if refs else ""
    finally:
        _ctx_owner.reset(tokens[3])
        _ctx_idx.reset(tokens[2])
        _ctx_chain.reset(tokens[1])
        _ctx_open.reset(tokens[0])


def model_family(model: str) -> str:
    """'deepseek-v4-flash' → 'deepseek', 'claude-sonnet-4-5' → 'claude'."""
    return (model or "").lower().split("-", 1)[0]


@contextmanager
def prefer(providers: list[str] | tuple[str, ...], *, model: str = ""):
    """ai-CR-145: trong khối này, khóa của các hãng `providers` (theo thứ tự) đứng ĐẦU chuỗi; các khóa còn lại giữ thứ
    tự cũ làm dự phòng. Không có khóa nào của hãng đó thì chuỗi y nguyên. Dùng cho bước cần model mạnh (lập kế hoạch).
    ai-CR-146: `model` (vd `deepseek-v4-pro`) thay model của khóa trạm tùy chỉnh CÙNG HỌ model (deepseek-v4-flash →
    deepseek-v4-pro) trong khối này — chat hằng ngày vẫn dùng bản nhanh ghi ở ô Model, riêng lập kế hoạch dùng bản mạnh."""
    if not _ctx_open.get() or (not providers and not model):
        yield
        return
    refs = list(_ctx_chain.get())[_ctx_idx.get():]
    if model:
        from dataclasses import replace

        refs = [replace(r, model=model) if r.provider == "openai_compat" and r.model
                and model_family(r.model) == model_family(model) else r for r in refs]
    rank = {p: i for i, p in enumerate(providers)}

    def family(r: KeyRef) -> str:
        #  ai-CR-146: khóa trạm tùy chỉnh (openai_compat, vd modelapi.vn nhóm «claude») mang model Claude / GPT thì tính
        #  theo HÃNG CỦA MODEL — không thì khóa Claude mua qua trạm không bao giờ được ưu tiên.
        m = (r.model or "").lower()
        if r.provider == "openai_compat" and m.startswith("claude"):
            return "claude"
        if r.provider == "openai_compat" and m.startswith(("gpt", "codex", "o3", "o4")):
            return "openai"
        return r.provider

    first = sorted((r for r in refs if family(r) in rank), key=lambda r: rank[family(r)])
    rest = [r for r in refs if family(r) not in rank]
    tokens = (_ctx_chain.set(tuple(first + rest)), _ctx_idx.set(0))
    try:
        yield
    finally:
        _ctx_idx.reset(tokens[1])
        _ctx_chain.reset(tokens[0])


@contextmanager
def use(key: str, owner: int = 0):
    """Tương thích cũ: một khóa Gemini lẻ."""
    refs = [KeyRef(provider=PROVIDER_GEMINI, key=key, owner_id=int(owner or 0), source="manual")] if key else []
    with use_chain(refs, owner):
        yield key or ""


def chain_for_chat(db: Session, chat_id: str) -> tuple[list[KeyRef], int]:
    """(chuỗi khóa, chủ) cho một chat. Chat đã liên kết: khóa cá nhân theo ưu tiên → khóa công ty → `.env`.
    Chat đại ca chưa liên kết: khóa công ty → `.env`. Chat lạ: không khóa."""
    link = chat_link.get_active_link(db, chat_id) if chat_id else None
    company = ai_keys.company_chain_for_bot(db)
    #  Khóa `.env` là khóa của MÁY chạy bot (phase 0/1, khóa đại ca) — chỉ chat đại ca được lùi về nó; người khác chỉ
    #  lùi về khóa CÔNG TY khai trong sổ (có trần lượt/ngày P-02).
    if telegram.is_allowed_chat(chat_id):
        company = company + [r for r in (env_ref(),) if r]
    if link is not None:
        return ai_keys.chain_for_user(db, link.user_id) + company, link.user_id
    if telegram.is_allowed_chat(chat_id):
        return company, 0
    return [], 0


def key_for_chat(db: Session, chat_id: str) -> tuple[str, int]:
    """Tương thích cũ: (khóa đầu chuỗi, chủ)."""
    refs, owner = chain_for_chat(db, chat_id)
    return (refs[0].key if refs else ""), owner


@contextmanager
def for_chat(db: Session, chat_id: str):
    refs, owner = chain_for_chat(db, chat_id)
    with use_chain(refs, owner) as key:
        yield key


@contextmanager
def for_admin(db: Session):
    """Việc nền của mảng mã nguồn (gom việc, lập kế hoạch) chạy bằng khóa của đại ca."""
    with for_chat(db, settings.AGENT_TELEGRAM_CHAT_ID) as key:
        yield key


# ---------------------------------------------------------------------------
# Sổ khóa cá nhân (bọc `ai_keys`, giữ tên hàm cũ)
# ---------------------------------------------------------------------------
PROBE_URL = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1"


def _probe(raw: str) -> int:
    return ai_keys._probe(PROVIDER_GEMINI, raw)


def verify(raw: str, provider: str = PROVIDER_GEMINI) -> None:
    raw = (raw or "").strip()
    if provider not in ai_keys.PROVIDERS:
        raise InvalidKey(f"Chưa hỗ trợ hãng «{provider}».")
    if len(raw) < 20 or " " in raw:
        raise InvalidKey("Khóa không đúng dạng.")
    code = _probe(raw) if provider == PROVIDER_GEMINI else ai_keys._probe(provider, raw)
    label = ai_keys.PROVIDER_LABELS[provider]
    if code in (400, 401, 403):
        raise InvalidKey(f"{label} không nhận khóa này (sai, đã thu hồi, hoặc dự án chưa bật API).")
    if code != 200:
        raise InvalidKey(f"{label} trả lỗi {code} khi kiểm khóa, thử lại sau.")


def active_row(db: Session, user_id: int) -> AiKey | None:
    rows = ai_keys.active_rows(db, OWNER_USER, user_id)
    return rows[0] if rows else None


def key_for_user(db: Session, user_id: int) -> str:
    refs = ai_keys.chain_for_user(db, user_id)
    return refs[0].key if refs else ""


def set_key(db: Session, user_id: int, raw: str, provider: str = PROVIDER_GEMINI, *, model: str = "",
            priority: int = 0, daily_cap: int = 0, base_url: str = "") -> AiKey:
    """Kiểm khóa với hãng rồi lưu mã hóa; cùng hãng + cùng ưu tiên thì dòng cũ đóng. Không bao giờ ghi khóa thô."""
    if provider == ai_keys.PROVIDER_CUSTOM:
        return ai_keys.add_key(db, owner_type=OWNER_USER, owner_id=user_id, provider=provider, raw=raw, model=model,
                               priority=priority, daily_cap=daily_cap, by_user=user_id, base_url=base_url)
    verify(raw, provider)
    return ai_keys.add_key(db, owner_type=OWNER_USER, owner_id=user_id, provider=provider, raw=raw, model=model,
                           priority=priority, daily_cap=daily_cap, by_user=user_id, check=False)


def revoke(db: Session, user_id: int) -> int:
    return ai_keys.revoke_all(db, OWNER_USER, user_id)


def describe(db: Session, user_id: int) -> dict:
    rows = ai_keys.active_rows(db, OWNER_USER, user_id)
    first = rows[0] if rows else None
    return {"provider": first.provider if first else PROVIDER_GEMINI, "has_key": first is not None,
            "hint": f"…{first.key_hint}" if first else "",
            "verified_at": first.verified_at.isoformat(timespec="seconds") if first and first.verified_at else None,
            "items": ai_keys.describe_rows(rows, db), "company_keys": len(ai_keys.company_chain(db)),
            "providers": [{"name": p, "label": ai_keys.PROVIDER_LABELS[p], "site": ai_keys.PROVIDER_SITES[p]}
                          for p in ai_keys.PROVIDERS]}


def key_problem(error: str) -> str:
    return ai_keys.key_problem(error, active_provider())


def usage_today(db: Session, owner: int) -> dict[str, int]:
    """Số lượt model hôm nay của một chủ khóa, chia theo hãng (để trả lời «còn khóa nào, giới hạn bao nhiêu»)."""
    from sqlalchemy import func

    from .model import AgentRun
    from .timeutil import now_local, to_utc

    since = to_utc(now_local().replace(hour=0, minute=0, second=0, microsecond=0))
    rows = db.execute(select(AgentRun.provider, func.count(AgentRun.id)).where(
        AgentRun.owner_id == int(owner or 0), AgentRun.started_at >= since).group_by(AgentRun.provider)).all()
    return {str(p or ""): int(n) for p, n in rows}
