"""Cảnh báo khóa AI hết tiền / hết hạn mức / hỏng (ai-CR-200).

Đại ca 14/10/2026: ví trạm modelapi.vn âm tiền → cả 3 khóa trạm (dùng chung một ví) hỏng cùng lúc, bot lặng lẽ rơi xuống
Gemini lite và trả lời «như con nít»; em chỉ biết khi đại ca chê bài viết. Nay mỗi lần chuỗi khóa nhảy vì CHUYỆN CỦA KHÓA,
bot nhắn riêng chủ khóa một tin (khóa cá nhân → chat của chính người đó; khóa công ty / `.env` → chat chủ bot), gom theo
trạm + loại lỗi và chỉ nhắn lại sau ALERT_EVERY — 3 khóa cùng một ví không thành 3 tin.

Không đọc được số dư: trạm kiểu new-api trả «hard_limit_usd» của khóa (khóa không giới hạn = 100 triệu USD), không phải
ví — nên tin chỉ báo hiện tượng, không bịa số dư.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.config import settings

log = logging.getLogger("app.agent_hub.key_alerts")

ACT_KEY_ALERT = "canh_bao_khoa"
ALERT_EVERY = timedelta(hours=3)

KIND_MONEY, KIND_QUOTA, KIND_INVALID, KIND_CHANNEL = "het_tien", "het_han_muc", "khoa_hong", "goi_khong_chay"
KIND_LABELS = {KIND_MONEY: "HẾT TIỀN", KIND_QUOTA: "hết hạn mức tạm thời", KIND_INVALID: "bị từ chối (khóa sai / hết hạn)",
               KIND_CHANNEL: "gói không chạy (trạm báo không có kênh cho model)"}


def kind_of(error: str) -> str:
    e = (error or "").lower()
    if any(k in e for k in ("402", "depleted", "prepayment", "billing", "insufficient", "额度不足", "余额不足", "balance")):
        return KIND_MONEY
    if any(k in e for k in ("429", "resource_exhausted", "quota", "rate limit")):
        return KIND_QUOTA
    if any(k in e for k in ("unknown provider", "no available channel", "model not supported")):
        return KIND_CHANNEL
    return KIND_INVALID


def _where(ref) -> str:
    """Tên chỗ mua khóa cho tin nhắn — trạm tùy chỉnh thì tên miền trạm."""
    base = str(getattr(ref, "base_url", "") or "")
    if base:
        return base.split("//", 1)[-1].split("/", 1)[0]
    return str(getattr(ref, "provider", "") or "hãng AI")


def _target_chat(db, ref) -> str:
    """Khóa cá nhân → chat riêng của chủ khóa (nếu đang liên kết); còn lại → chat chủ bot."""
    from . import ai_keys
    from .model import AgentChatLink

    owner = int(getattr(ref, "owner_id", 0) or 0)
    if int(getattr(ref, "owner_type", 0) or 0) == ai_keys.OWNER_USER and owner:
        now = datetime.now()
        link = db.scalar(select(AgentChatLink).where(
            AgentChatLink.user_id == owner, AgentChatLink.chat_id != "", AgentChatLink.revoked_at.is_(None),
            AgentChatLink.expires_at > now).order_by(AgentChatLink.id.desc()).limit(1))
        if link is not None:
            return str(link.chat_id)
    return str(settings.AGENT_TELEGRAM_CHAT_ID or "").strip()


def _recently_sent(db, chat_id: str, group: str, now: datetime) -> bool:
    from .model import AgentMessage

    rows = db.scalars(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_KEY_ALERT,
                                                 AgentMessage.created_at >= now - ALERT_EVERY))
    for r in rows:
        try:
            if json.loads(r.body or "{}").get("group") == group:
                return True
        except ValueError:
            continue
    return False


def message(ref, kind: str, has_next: bool) -> str:
    from . import telegram

    esc = telegram.esc
    name = f"…{esc(getattr(ref, 'hint', '') or '')}"
    model = esc(getattr(ref, "model", "") or "mặc định")
    where = esc(_where(ref))
    head = f"<b>Khóa AI {KIND_LABELS.get(kind, 'hỏng')}</b>: khóa {name} ({model}, {where})."
    tail = ("Bot đã tự chuyển sang khóa kế tiếp trong danh sách, nhưng model dự phòng có thể yếu hoặc chậm hơn."
            if has_next else "Không còn khóa dự phòng nào chạy được — bot tạm không trả lời được câu hỏi AI.")
    fix = {KIND_MONEY: f"Nạp thêm tiền ở {where}. Nếu nhiều khóa cùng một trạm thì thường là chung một ví.",
           KIND_QUOTA: "Chờ ít phút; lặp lại nhiều thì nâng hạn mức hoặc thêm khóa dự phòng.",
           KIND_CHANNEL: f"Kiểm nhóm / gói của khóa trên trang {where}.",
           KIND_INVALID: "Lấy khóa mới rồi dán lại ở ERP → Trang cá nhân → Khóa AI."}.get(kind, "")
    return f"{head}\n{tail}\n{fix}"


def notify(ref, error: str, *, has_next: bool) -> None:
    """Gọi từ chuỗi khóa khi nhảy khóa vì chuyện của khóa. Không bao giờ ném lỗi ra ngoài."""
    if ref is None or getattr(ref, "source", "") == "manual":
        return
    try:
        from app.core.database import SessionLocal

        from . import telegram
        from .constants import DIR_OUT
        from .model import AgentMessage

        kind = kind_of(error)
        group = f"{_where(ref)}|{kind}"
        db = SessionLocal()
        try:
            chat_id = _target_chat(db, ref)
            now = datetime.now()
            if not chat_id or _recently_sent(db, chat_id, group, now):
                return
            text = message(ref, kind, has_next)
            try:
                telegram.send(text, chat_id=chat_id)
            except Exception:  # noqa: BLE001 — gửi hỏng vẫn ghi sổ để không thử lại liên tục
                log.warning("key_alerts: gửi cảnh báo khóa hỏng")
            db.add(AgentMessage(task_id=0, direction=DIR_OUT, chat_id=chat_id, tg_message_id=0, action=ACT_KEY_ALERT,
                                body=json.dumps({"group": group, "hint": getattr(ref, "hint", ""), "kind": kind,
                                                 "text": text}, ensure_ascii=False)))
            db.commit()
        finally:
            db.close()
    except Exception:  # noqa: BLE001
        log.exception("key_alerts: không gửi được cảnh báo khóa")
