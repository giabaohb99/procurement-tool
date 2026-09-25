"""Luồng của Agent Hub — nơi Telegram, sổ và bot quản lý gặp nhau.

Một tin nhắn đi qua đây theo hai đường, rẽ ở ngay dòng đầu:

  hỏi / nhờ làm nghiệp vụ / nói tiếp câu chuyện
               -> chuyển cho TRỢ LÝ AI sẵn có (có tool), trả lời tại chỗ, KHÔNG tạo task.
  nhờ sửa phần mềm
               -> ghi vào `tab_agent_message` với `task_id = 0` (đó là hàng đợi INBOX),
                  chờ lặng đủ `AGENT_TRIAGE_DELAY_SEC` rồi một vòng gom biến cả lô
                  thành các task, mỗi task một thẻ Telegram có nút.

Chỗ rẽ là `_route_plain_text`: bot vừa hỏi lại thì tin kế là câu trả lời (không cần
đoán); còn lại một lượt Gemini phân loại, có kèm mạch trước đó. Mặc định nghiêng về
Trợ lý AI — vào sổ việc là chuyện hiếm hơn và có người duyệt phía sau.

Vì sao hai đường trong một bot: trò chuyện và giao việc sửa mã là hai nhu cầu khác
nhau nhưng cùng đi qua một cái điện thoại. Tách làm hai bot thì đại ca phải nhớ mình
đang chat với con nào.

Bấm Duyệt: ghi `approved_at`, rồi nếu cờ `AGENT_CODER_ENABLED` bật thì giao cho bậc 2
(`coder.py`, chạy trong service `agent-runner`) sửa mã thật; cờ tắt thì dừng ở PLAN như bậc 1
(`TIER1_MAX_STATUS`) và nói rõ là đang tắt.
"""
import html as html_lib
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.assistant.provider.base import ChatResult

from . import chat_link, coder, draft_create, grants, manager, memory, playbook, research, runners, telegram, user_keys
from .timeutil import fmt_local, now_local, to_utc
from .constants import (
    ACT_ACK,
    ACT_ANSWER,
    ACT_HEARTBEAT,
    ACT_ASKED,
    ACT_COMMAND,
    ACT_DEPLOY_TIME,
    ACT_FILE,
    ACT_PATCH_ANSWER,
    ACT_PATCH_Q,
    ACT_PLAN_ANSWER,
    ACT_PROPOSAL,
    ACT_PROPOSAL_DONE,
    ACT_PROPOSAL_DROPPED,
    ACT_WAIT_CHOICE,
    ACT_WAIT_CONFIRM,
    ACT_PHOTO_ACK,
    ACT_PHOTO_USED,
    ACT_PHOTO_WAIT,
    ACT_WAIT_DEPLOY_TIME,
    ACT_WAIT_PATCH_Q,
    ACT_WAIT_PLAN_ANSWER,
    ACT_DRAFT_DONE,
    ACT_DENIED,
    ACT_DRAFT_DROPPED,
    ACT_DRAFT_WAIT,
    ACT_GRANT_DONE,
    ACT_GRANT_DROPPED,
    ACT_GRANT_WAIT,
    ACT_RUNNER_DONE,
    ACT_RUNNER_DROPPED,
    ACT_RUNNER_WAIT,
    BOT_DRAFT_FACTS,
    BOT_LOGIN_FACTS,
    BOT_NAME,
    BOT_PERSONA,
    CLOSED_STATUSES,
    DIR_IN,
    DIR_OUT,
    MERGED_BY_BOT,
    NOISE_ACTIONS,
    RISK_HIGH,
    RISK_LABELS,
    RISK_MEDIUM,
    RUN_ERROR,
    RUN_OK,
    RUN_RUNNING,
    SRC_ERP_TICKET,
    SRC_TELEGRAM,
    ST_CANCELLED,
    ST_CODE,
    ST_DEPLOYING,
    ST_DONE,
    ST_NEEDS_INPUT,
    ST_PLAN,
    ST_PROD,
    ST_REVIEW,
    ST_SCANNING,
    ST_TRIAGE,
    STAGE_DEPLOY,
    STAGE_INTENT,
    STAGE_PLAN,
    STAGE_REVERT,
    STAGE_RULE,
    STAGE_RESEARCH,
    STAGE_SCAN,
    STAGE_TRIAGE,
    TASK_STATUS_LABELS,
    estimate_cost_usd,
)
from .model import AgentCursor, AgentMessage, AgentRun, AgentRunner, AgentTask, AgentTaskItem

log = logging.getLogger("app.agent_hub")

CURSOR_NAME = "telegram_offset"


# ---------------------------------------------------------------------------
# Con trỏ Telegram
# ---------------------------------------------------------------------------
def get_cursor(db: Session) -> AgentCursor:
    row = db.scalar(select(AgentCursor).where(AgentCursor.name == CURSOR_NAME))
    if row is None:
        row = AgentCursor(name=CURSOR_NAME, value=0)
        db.add(row)
        db.flush()
    return row


# ---------------------------------------------------------------------------
# Kéo tin và phân đường
# ---------------------------------------------------------------------------
def poll_once(db: Session, *, timeout: int = telegram.POLL_TIMEOUT) -> int:
    """Kéo một lượt tin Telegram và xử hết. Trả số update đã đọc.

    `timeout` = số giây giữ kết nối chờ tin: vòng beat trong worker để 0 (về ngay),
    tiến trình `agent-poller` để `LONG_POLL_TIMEOUT` (ai-CR-008).
    """
    offset = get_cursor(db).value
    #  ĐÓNG giao dịch TRƯỚC khi chờ Telegram (ai-CR-025). MySQL mặc định REPEATABLE READ: giữ giao
    #  dịch mở suốt 25 giây long-poll thì lúc xử tin, mọi thứ runner/worker vừa ghi đều vô hình —
    #  đại ca bấm «Làm tiếp» AI-0007 mà bot thấy việc còn «Thất bại», lặng lẽ không làm gì.
    db.commit()
    updates = telegram.fetch_updates(offset, timeout=timeout)
    if not updates:
        return 0
    cursor = get_cursor(db)     # đọc lại trong giao dịch MỚI, sau khi chờ

    for upd in updates:
        #  Đẩy con trỏ TRƯỚC khi xử. Xử xong mới đẩy thì một tin làm nổ lỗi sẽ được kéo
        #  lại ở lượt sau, nổ lại, và bot kẹt vĩnh viễn ở đúng tin đó.
        cursor.value = max(cursor.value, int(upd.get("update_id", 0)) + 1)
        try:
            if upd.get("callback_query"):
                handle_callback(db, upd["callback_query"])
            elif upd.get("message"):
                handle_message(db, upd["message"])
        except Exception:
            log.exception("agent_hub: hỏng khi xử update %s", upd.get("update_id"))
        db.commit()
    return len(updates)


def handle_message(db: Session, msg: dict) -> None:
    """Mọi tin vào đi qua đây. ai-CR-053: mở ngữ cảnh KHÓA GEMINI của chat (khóa cá nhân của tài khoản đã
    liên kết; chat đại ca chưa có khóa cá nhân thì khóa `.env`) cho toàn bộ lượt xử lý bên trong."""
    chat_id = str((msg.get("chat") or {}).get("id") or "")
    with user_keys.for_chat(db, chat_id):
        _handle_message(db, msg, chat_id)


def _handle_message(db: Session, msg: dict, chat_id: str) -> None:
    #  ai-CR-035: ảnh gửi kèm chú thích thì chú thích là nội dung tin.
    text = (msg.get("text") or msg.get("caption") or "").strip()
    photo_id = _photo_file_id(msg)
    if not text and not photo_id:
        return
    if not telegram.is_allowed_chat(chat_id):
        #  ai-CR-038: chat khác chỉ có hai đường — đăng nhập bằng mã, hoặc đã liên kết thì hỏi Trợ lý.
        if not _handle_other_chat(db, msg, chat_id, text):
            #  Không trả lời gì cả. Trả lời "bạn không có quyền" là xác nhận cho người lạ
            #  rằng bot này sống và có chủ.
            log.warning("agent_hub: bỏ tin từ chat lạ %s", chat_id)
        return

    #  ai-CR-038: sổ không giữ mã đăng nhập một lần, kể cả khi đã dùng.
    logged = "/dangnhap ******" if _LOGIN_CMD.match(text) else (text or "(ảnh)")
    row = log_message(db, DIR_IN, chat_id, int(msg.get("message_id") or 0), logged)
    if photo_id:
        saved = _save_photo(chat_id, msg, photo_id)
        if saved is None:
            reply(db, chat_id, "Em không tải được ảnh này, đại ca gửi lại giúp em.", action=ACT_PHOTO_ACK)
            row.action = ACT_PHOTO_USED
            db.commit()
            return
        row.files = [saved]
        if not text:
            db.commit()
            _hold_photo(db, chat_id, row, saved)
            db.commit()
            return
    #  Chốt con trỏ + tin vào TRƯỚC khi gọi model. Mọi thứ phía dưới (phân loại ý định,
    #  Trợ lý AI, tool) đều có thể rollback session giữa chừng — bao-CR-463 là một ca
    #  như thế: một tin bị trả lời BỐN lần vì con trỏ trôi theo rollback của sổ audit.
    db.commit()
    #  Báo "đang soạn tin..." NGAY, trước khi đi hỏi model (ai-CR-008). Ở đây chứ không
    #  ở trong từng nhánh: đại ca cần biết bot đã nhận tin, chưa cần biết nó rẽ đường nào.
    telegram.send_chat_action(chat_id)

    if text.startswith("/"):
        #  Lệnh KHÔNG bao giờ là một đầu việc. Thiếu dấu này thì chính chữ `/start`
        #  nằm lại INBOX và vòng gom đẻ ra một task tên "Xử lý tin nhắn lệnh /start".
        row.action = ACT_COMMAND
        _run_command(db, chat_id, text)
        return

    _adopt_pending_photos(db, chat_id, row)
    _route_plain_text(db, chat_id, row, text)


# ---------------------------------------------------------------------------
# Ảnh chụp lỗi gửi kèm (ai-CR-035)
# ---------------------------------------------------------------------------
#  Album: các ảnh cùng `media_group_id` tới gần như cùng lúc, chú thích chỉ nằm ở MỘT ảnh. Ảnh
#  không chú thích thì chờ câu mô tả trong FOLLOW_UP_WINDOW rồi ghép vào câu đó.
ALBUM_WINDOW = timedelta(minutes=2)


def _photo_file_id(msg: dict) -> str:
    """file_id của ảnh lớn nhất; hoặc tệp ảnh gửi dạng tài liệu (giữ nguyên chất lượng)."""
    sizes = msg.get("photo") or []
    if sizes:
        return str(sizes[-1].get("file_id") or "")
    doc = msg.get("document") or {}
    if str(doc.get("mime_type") or "").startswith("image/"):
        return str(doc.get("file_id") or "")
    return ""


def _save_photo(chat_id: str, msg: dict, file_id: str) -> dict | None:
    try:
        data, remote = telegram.download_file(file_id, max_bytes=settings.AGENT_FILE_MAX_MB * 1024 * 1024)
    except telegram.TelegramError as e:
        log.warning("agent_hub: tải ảnh hỏng: %s", e)
        return None
    ext = (remote.rsplit(".", 1)[-1] if "." in remote else "jpg").lower()[:5]
    if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
        ext = "jpg"
    folder = Path(settings.AGENT_FILES_DIR) / "tg" / now_local().strftime("%Y%m")
    try:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{chat_id}_{int(msg.get('message_id') or 0)}.{ext}"
        path.write_bytes(data)
    except OSError as e:
        log.warning("agent_hub: ghi ảnh hỏng: %s", e)
        return None
    return {"path": str(path), "kind": "photo", "group": str(msg.get("media_group_id") or "")}


def _hold_photo(db: Session, chat_id: str, row: AgentMessage, saved: dict) -> None:
    """Ảnh không chữ: ghép vào tin cùng album nếu có; không thì chờ câu mô tả (báo nhận một lần)."""
    group = saved.get("group") or ""
    if group:
        since = (row.created_at or datetime.now()) - ALBUM_WINDOW
        recent = db.scalars(select(AgentMessage).where(
            AgentMessage.chat_id == chat_id, AgentMessage.direction == DIR_IN, AgentMessage.id < row.id,
            AgentMessage.created_at >= since).order_by(AgentMessage.id.desc()).limit(20)).all()
        for other in recent:
            if any((f or {}).get("group") == group for f in (other.files or [])):
                other.files = list(other.files or []) + [saved]
                row.files = []
                row.action = ACT_PHOTO_USED
                row.task_id = other.task_id
                return
    row.action = ACT_PHOTO_WAIT
    minutes = int(FOLLOW_UP_WINDOW.total_seconds() // 60)
    reply(db, chat_id, f"Em nhận ảnh rồi. Đại ca nhắn thêm mô tả lỗi (trong {minutes} phút), em ghép ảnh "
          "vào yêu cầu đó.", action=ACT_PHOTO_ACK)


def _adopt_pending_photos(db: Session, chat_id: str, row: AgentMessage) -> None:
    """Tin chữ vừa tới nhận luôn các ảnh đang chờ mô tả của cùng chat."""
    since = (row.created_at or datetime.now()) - FOLLOW_UP_WINDOW
    waiting = db.scalars(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.id < row.id, AgentMessage.action == ACT_PHOTO_WAIT,
        AgentMessage.created_at >= since).order_by(AgentMessage.id)).all()
    if not waiting:
        return
    files = list(row.files or [])
    for w in waiting:
        files += list(w.files or [])
        w.files = []
        w.action = ACT_PHOTO_USED
    row.files = files
    db.commit()


# ---------------------------------------------------------------------------
# Đăng nhập ERP trong Telegram (ai-CR-038)
# ---------------------------------------------------------------------------
_LOGIN_CMD = re.compile(r"^/(dangnhap|start)(?:@\w+)?\s+(\d{6})\s*$", re.IGNORECASE)
_LOGOUT_CMD = re.compile(r"^/(dangxuat|doitaikhoan)(?:@\w+)?\b", re.IGNORECASE)
_LINK_HELP = ("Lấy mã ở <b>Trang cá nhân → Telegram</b> trên ERP rồi nhắn <code>/dangnhap &lt;mã&gt;</code>. "
              "Đổi tài khoản: <code>/dangxuat</code> rồi đăng nhập lại bằng mã mới.")


def _get_tg_name(msg: dict) -> str:
    who = msg.get("from") or {}
    name = " ".join(p for p in (who.get("first_name"), who.get("last_name")) if p)
    return name or (f"@{who['username']}" if who.get("username") else "")


def _login_by_code(db: Session, msg: dict, chat_id: str, code: str, *, log_row: bool = True) -> None:
    """Đổi mã lấy liên kết. Sổ ghi lệnh đã che mã. Sai thì đếm để chặn dò mã."""
    ok = chat_link.redeem_code(db, chat_id, code, _get_tg_name(msg)) if settings.AGENT_LINK_ENABLED else None
    if log_row:
        log_message(db, DIR_IN, chat_id, int(msg.get("message_id") or 0), "/dangnhap ******",
                    action=ACT_COMMAND if ok else chat_link.ACT_LOGIN_FAIL)
    db.commit()
    if ok is None:
        reply(db, chat_id, "Mã không đúng hoặc đã hết hạn. " + _LINK_HELP)
        return
    from app.modules.user.model import User

    user = db.get(User, ok.user_id)
    name, detail = describe_user(db, user)
    reply(db, chat_id, f"Đã đăng nhập tài khoản ERP <b>{telegram.esc(name)}</b> cho chat này"
          + (f" ({telegram.esc(detail)})" if detail else "")
          + f". Hết hạn sau {settings.AGENT_LINK_DAYS} ngày. Cứ nhắn câu hỏi, em trả lời đúng quyền của tài khoản đó. "
          "Đăng xuất: <code>/dangxuat</code>.")


# ---------------------------------------------------------------------------
# Hỏi chi phí bằng chữ (ai-CR-043) — màn «Việc của bot» đã ẩn (ai-CR-039), đại ca hỏi bot thay
# ---------------------------------------------------------------------------
#  Chỉ bắt câu nói về tiền CỦA BOT: «chi phí» đứng một mình là từ nghiệp vụ ERP (chi phí thu mua).
_COST_Q = re.compile(
    r"(?<!\w)(chi phí|tốn|hết)(?!\w).{0,30}(?<!\w)(bot|token|gemini|claude|đậu đậu|ai[-\s]?\d+)(?!\w)"
    r"|(?<!\w)(bot|đậu đậu|ai[-\s]?\d+)(?!\w).{0,20}(?<!\w)(tốn|chi phí|hết bao nhiêu)(?!\w)")


# ---------------------------------------------------------------------------
# Nghiên cứu (ai-CR-044): tìm web · kiểm chứng · tài liệu nội bộ · xuất Word
# ---------------------------------------------------------------------------
_RESEARCH_CMDS = (("/kiemchung", research.MODE_VERIFY), ("/tailieu", research.MODE_DOCS),
                  ("/tim", research.MODE_WEB))
ACT_RESEARCH = "nghien_cuu"


def _research_command(db: Session, chat_id: str, text: str, *, allow_docs: bool) -> bool:
    """Các lệnh nghiên cứu. Trả True nếu tin là một lệnh trong số đó (đã xử)."""
    low = text.strip().lower()
    if re.match(r"^/word(?:@\w+)?\s*$", low):
        export_research_word(db, chat_id)
        return True
    for cmd, mode in _RESEARCH_CMDS:
        if re.match(rf"^{cmd}(?:@\w+)?(\s|$)", low):
            if mode == research.MODE_DOCS and not allow_docs:
                reply(db, chat_id, "Lệnh này chỉ dành cho quản trị.")
                return True
            question = re.sub(rf"^{cmd}(?:@\w+)?", "", text.strip(), flags=re.IGNORECASE).strip()
            run_research(db, chat_id, question, mode)
            return True
    return False


def run_research(db: Session, chat_id: str, question: str, mode: str) -> None:
    """Một lượt nghiên cứu: gọi `research.run`, ghi sổ chi phí, nhắn kết quả + nguồn."""
    if not question:
        reply(db, chat_id, "Đại ca nhắn luôn điều cần tra, ví dụ «tìm hiểu giúp anh thuế nhập khẩu thép "
              "2026» hoặc «có đúng là hóa đơn điện tử phải xuất trong ngày không».")
        return
    if not user_keys.active_key():
        reply(db, chat_id, user_keys.NO_KEY_HELP)
        return
    telegram.send_chat_action(chat_id)
    run = start_run(db, 0, STAGE_RESEARCH)
    db.commit()
    try:
        text, sources, result = research.run(question, mode)
    except Exception as e:  # noqa: BLE001 — lỗi nhà cung cấp phải thành câu trả lời
        log.exception("agent_hub: nghiên cứu hỏng")
        finish_run(db, run, error=str(e))
        db.commit()
        reply(db, chat_id, f"{BOT_NAME} chưa tra được: {telegram.esc(str(e)[:300])}")
        return
    if result is not None:
        finish_run(db, run, result=result)
    else:
        finish_run(db, run, result=ChatResult(text=text, provider="agent_gemini", model=run.model,
                                              input_tokens=0, output_tokens=0))
    run.artifact = {"chat_id": chat_id, "mode": mode, "question": question[:500], "text": text[:8000],
                    "sources": sources}
    db.commit()
    reply(db, chat_id, (text or "(không có câu trả lời)") + research.sources_markdown(sources)
          + "\n\n_Muốn bản Word thì nhắn «xuất Word»._", markdown=True, action=ACT_RESEARCH)


#  «xuất word giúp anh», «gửi bản word», «cho file word» — chỉ khi chat này VỪA tra xong (trong
#  RESEARCH_WORD_WINDOW) và câu ngắn: «xuất word báo cáo công nợ tháng 9» là việc của Trợ lý ERP.
_WORD_Q = re.compile(r"(?<!\w)word(?!\w)")
RESEARCH_WORD_WINDOW = timedelta(minutes=30)


def _word_by_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    low = text.strip().lower()
    if len(low.split()) > 8 or not _WORD_Q.search(low):
        return False
    runs = db.scalars(select(AgentRun).where(AgentRun.stage == STAGE_RESEARCH, AgentRun.status == RUN_OK,
                                             AgentRun.started_at >= datetime.now() - RESEARCH_WORD_WINDOW)
                      .order_by(AgentRun.id.desc()).limit(20)).all()
    if not any(isinstance(r.artifact, dict) and r.artifact.get("chat_id") == chat_id for r in runs):
        return False
    row.action = ACT_COMMAND
    db.commit()
    export_research_word(db, chat_id)
    return True


def export_research_word(db: Session, chat_id: str) -> None:
    """«/word»: bản Word của lượt nghiên cứu GẦN NHẤT của chính chat này (R-04)."""
    runs = db.scalars(select(AgentRun).where(AgentRun.stage == STAGE_RESEARCH, AgentRun.status == RUN_OK)
                      .order_by(AgentRun.id.desc()).limit(50)).all()
    art = next((r.artifact for r in runs if isinstance(r.artifact, dict) and r.artifact.get("chat_id") == chat_id), None)
    if not art:
        reply(db, chat_id, "Chat này chưa có lần tìm hiểu nào để xuất Word. Đại ca nhắn điều cần tìm trước, "
              "ví dụ «tìm hiểu giúp anh …».")
        return
    data = research.build_docx(art.get("mode", research.MODE_WEB), art.get("question", ""),
                               art.get("text", ""), art.get("sources") or [])
    try:
        mid = telegram.send_document(chat_id, "nghien-cuu.docx", data, caption=telegram.esc(art.get("question", "")[:200]),
                                     content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except telegram.TelegramError as e:
        reply(db, chat_id, f"Gửi tệp Word hỏng: {telegram.esc(str(e)[:200])}")
        return
    log_message(db, DIR_OUT, chat_id, mid, "nghien-cuu.docx", action=ACT_FILE)
    db.commit()


def _cost_by_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    low = text.strip().lower()
    if len(low.split()) > 25 or not _COST_Q.search(low):
        return False
    code_m = _CODE_IN_TEXT.search(low)
    task = db.scalar(select(AgentTask).where(AgentTask.code == f"AI-{int(code_m.group(1)):04d}")) if code_m else None
    row.action = ACT_COMMAND
    db.commit()
    #  ai-CR-053: chat thường chỉ thấy tiền của KHÓA MÌNH; chat đại ca thấy cả bot.
    owner = 0 if telegram.is_allowed_chat(chat_id) else user_keys.active_owner()
    reply(db, chat_id, cost_report(db, task=task, owner_id=owner))
    return True


def _money(usd: float) -> str:
    vnd = round(usd * settings.AGENT_USD_VND / 1000) * 1000
    return f"${usd:.2f} (≈ {vnd:,.0f} đ)".replace(",", ".")


def cost_report(db: Session, *, task: AgentTask | None = None, now: datetime | None = None,
                owner_id: int = 0) -> str:
    """Báo chi phí ƯỚC của bot: một việc, hoặc hôm nay / 7 ngày / 30 ngày + ba việc tốn nhất.

    Tách hai loại tiền: Gemini là tiền THẬT trả theo lượt; Claude Code chạy gói thuê bao nên số của nó
    chỉ là ước để so, không phát sinh thêm. `owner_id` > 0: chỉ các lượt chạy bằng khóa của người đó (ai-CR-053).
    """
    esc = telegram.esc
    now = now or datetime.now()
    rate_note = f"Tỷ giá tạm {settings.AGENT_USD_VND:,} đ/USD.".replace(",", ".")
    if owner_id:
        runs = db.scalars(select(AgentRun).where(AgentRun.owner_id == owner_id, AgentRun.started_at >= now - timedelta(days=30))).all()
        today = to_utc(now_local().replace(hour=0, minute=0, second=0, microsecond=0))
        lines = ["<b>Chi phí Gemini bằng khóa của anh/chị</b> (tiền thật, ước theo bảng giá)"]
        for label, since in (("Hôm nay", today), ("7 ngày", now - timedelta(days=7)), ("30 ngày", now - timedelta(days=30))):
            lines.append(f"{label}: {_money(sum(float(r.cost_usd or 0) for r in runs if r.started_at and r.started_at >= since))}")
        lines.append(rate_note)
        return "\n".join(lines)
    if task is not None:
        runs = db.scalars(select(AgentRun).where(AgentRun.task_id == task.id)).all()
        gem = sum(float(r.cost_usd or 0) for r in runs if r.provider != coder.PROVIDER)
        cc = sum(float(r.cost_usd or 0) for r in runs if r.provider == coder.PROVIDER)
        return (f"<b>{esc(task.code)}</b> · {esc(task.title)}\n"
                f"Gemini (tiền thật): {_money(gem)}\n"
                f"Claude Code (gói thuê bao, ước để so): {_money(cc)}\n{rate_note}")
    today = to_utc(now_local().replace(hour=0, minute=0, second=0, microsecond=0))
    since30 = now - timedelta(days=30)
    runs = db.scalars(select(AgentRun).where(AgentRun.started_at >= since30)).all()

    def total(since, *, gemini: bool) -> float:
        return sum(float(r.cost_usd or 0) for r in runs
                   if r.started_at and r.started_at >= since and (r.provider != coder.PROVIDER) == gemini)

    lines = ["<b>Chi phí ước của bot</b>"]
    for label, since in (("Hôm nay", today), ("7 ngày", now - timedelta(days=7)), ("30 ngày", since30)):
        lines.append(f"{label}: Gemini {_money(total(since, gemini=True))} · Claude Code ước "
                     f"{_money(total(since, gemini=False))}")
    per_task: dict[int, float] = {}
    for r in runs:
        if r.task_id:
            per_task[r.task_id] = per_task.get(r.task_id, 0.0) + float(r.cost_usd or 0)
    top = sorted(per_task.items(), key=lambda x: -x[1])[:3]
    if top:
        tasks = {t.id: t for t in db.scalars(select(AgentTask).where(AgentTask.id.in_([t for t, _c in top])))}
        lines.append("Tốn nhất 30 ngày: " + " · ".join(
            f"<b>{esc(tasks[t].code)}</b> {_money(c)}" for t, c in top if t in tasks))
    lines.append("Gemini là tiền thật; Claude Code chạy gói thuê bao nên không trả thêm. " + rate_note)
    return "\n".join(lines)


def describe_user(db: Session, user) -> tuple[str, str]:
    """(nhãn, chi tiết) của một tài khoản ERP cho người đọc: «Họ tên (MÃ NV)», «Phòng … · Email …».

    ai-CR-042: bản đầu chỉ in email, tài khoản không có email thì ra «#238» — đại ca không biết là ai.
    """
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee

    if user is None:
        return "", ""
    emp = db.get(Employee, user.employee_id) if getattr(user, "employee_id", 0) else None
    login = (getattr(user, "email", "") or "").strip()
    if emp is not None:
        label = f"{emp.full_name} ({emp.code})" if emp.code else emp.full_name
        dept = db.get(Department, emp.department_id) if emp.department_id else None
        parts = [f"phòng {dept.name}" if dept is not None else "",
                 f"tên đăng nhập {login}" if login else ""]
        return label, " · ".join(p for p in parts if p)
    return (login or f"tài khoản #{getattr(user, 'id', 0)}"), ""


def _account_fact(db: Session, chat_id: str, user) -> str:
    """Câu cho model biết chat này đang chạy dưới tài khoản nào và vì sao (ai-CR-040, ai-CR-042)."""
    link = chat_link.get_active_link(db, chat_id)
    name, detail = describe_user(db, user)
    who = name + (f" ({detail})" if detail else "")
    how = ("đã đăng nhập bằng /dangnhap" if link is not None
           else "CHƯA đăng nhập bằng mã nên đang dùng tài khoản chung khai sẵn cho bot")
    return (f"Chat này đang dùng tài khoản ERP: {who}, {how}. Khi người dùng hỏi thông tin tài khoản / "
            "thông tin cá nhân của họ thì trả lời bằng chính thông tin tài khoản này (tra thêm bằng tool nếu "
            "cần), KHÔNG giảng lại cách đăng nhập — chỉ nói cách đăng nhập khi họ hỏi cách đổi tài khoản.")


def show_account(db: Session, chat_id: str) -> None:
    """«/taikhoan»: chat này hỏi Trợ lý dưới tài khoản nào, và cách đổi (ai-CR-040)."""
    from app.modules.user.model import User

    link = chat_link.get_active_link(db, chat_id)
    if link is not None:
        name, detail = describe_user(db, db.get(User, link.user_id))
        text = (f"Chat này đang dùng tài khoản ERP <b>{telegram.esc(name)}</b>"
                + (f" ({telegram.esc(detail)})" if detail else "")
                + f". Đăng nhập bằng mã lúc {fmt_local(link.linked_at)}, hết hạn {fmt_local(link.expires_at)}.")
    else:
        user = _assistant_user(db, chat_id)
        name, detail = describe_user(db, user)
        text = (f"Chat này CHƯA đăng nhập bằng mã nên đang dùng tài khoản chung của bot "
                f"<b>{telegram.esc(name)}</b>" + (f" ({telegram.esc(detail)})" if detail else "") + "."
                if user is not None else "Chat này chưa đăng nhập tài khoản ERP nào.")
    reply(db, chat_id, text + "\nĐăng nhập tài khoản trên web KHÔNG làm chat này đổi theo. " + _LINK_HELP)


def _logout(db: Session, chat_id: str) -> None:
    n = chat_link.revoke_chat(db, chat_id)
    reply(db, chat_id, ("Đã đăng xuất tài khoản ERP khỏi chat này. " if n else "Chat này chưa đăng nhập. ")
          + _LINK_HELP)


def _handle_other_chat(db: Session, msg: dict, chat_id: str, text: str) -> bool:
    """Chat KHÔNG phải của đại ca. Trả True nếu đã xử (đăng nhập / người đã liên kết), False = lờ đi.

    Người đã liên kết chỉ có một việc: hỏi Trợ lý AI. Tin của họ không bao giờ vào hàng việc sửa mã.
    """
    if not settings.AGENT_LINK_ENABLED or not chat_id:
        return False
    m = _LOGIN_CMD.match(text or "")
    if m:
        if str((msg.get("chat") or {}).get("type") or "private") != "private":
            return False                     # nhóm chat: không liên kết, kẻo cả nhóm dùng quyền một người
        if chat_link.has_too_many_failures(db, chat_id):
            return True                      # đang bị chặn dò mã: im lặng
        _login_by_code(db, msg, chat_id, m.group(2))
        return True
    link = chat_link.get_active_link(db, chat_id)
    if link is None:
        old = chat_link.get_expired_link(db, chat_id)
        if old is None:
            return False
        chat_link.revoke_chat(db, chat_id)
        reply(db, chat_id, "Phiên đăng nhập ERP của chat này đã hết hạn. " + _LINK_HELP)
        return True
    row = log_message(db, DIR_IN, chat_id, int(msg.get("message_id") or 0), text or "(ảnh)",
                      action=ACT_ASKED)
    db.commit()
    telegram.send_chat_action(chat_id)
    low = (text or "").strip().lower()
    if _LOGOUT_CMD.match(low):
        row.action = ACT_COMMAND
        _logout(db, chat_id)
        return True
    if not text:
        reply(db, chat_id, "Em chỉ đọc được chữ. Đại ca nhắn câu hỏi bằng chữ giúp em.")
        return True
    if low.startswith("/taikhoan"):
        row.action = ACT_COMMAND
        show_account(db, chat_id)
        return True
    if low.startswith("/"):
        row.action = ACT_COMMAND
        db.commit()
        #  Người đã liên kết dùng được tìm web + kiểm chứng + Word; tài liệu KỸ THUẬT dự án thì không.
        if _research_command(db, chat_id, text, allow_docs=False):
            return True
    if low.startswith("/") and not low.startswith("/hoi"):
        row.action = ACT_COMMAND
        reply(db, chat_id, f"Em là <b>{BOT_NAME}</b>. Anh/chị cứ nhắn bình thường: hỏi số liệu ERP (em trả lời "
              "theo quyền tài khoản của anh/chị), nhờ tìm hiểu một chủ đề trên mạng, hỏi một thông tin có đúng "
              "không, hay «xuất Word» bản vừa tìm. Đăng xuất: <code>/dangxuat</code>.")
        return True
    if low.startswith("/hoi"):
        answer_question(db, chat_id, text[4:].strip(), before_id=row.id)
        return True
    #  ai-CR-051 (K-04): người được đại ca cấp quyền ra lệnh trên việc bằng chữ như đại ca, nhưng PHẢI
    #  nêu mã việc («gộp AI-0007», «AI-0007 xong chưa»): họ trò chuyện với Trợ lý nhiều, một câu «xong
    #  rồi» trơn không được phép đóng việc nào. Đủ cấp hay không do `_grant_allows` xét.
    if grants.level_for(db, link.user_id) and _CODE_IN_TEXT.search(low) and route_task_command(db, chat_id, row, text):
        return True
    _route_linked_text(db, chat_id, row, text)
    return True


def _route_linked_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> None:
    """Tin chữ thường của người đã liên kết (ai-CR-045): hiểu bằng chữ, không bắt gõ lệnh.

    «Xuất Word» sau một lần tra → gửi Word; ý định `tra_cuu` → tìm web / kiểm chứng (tài liệu kỹ thuật
    dự án KHÔNG mở cho họ, hạ về tìm web); mọi ý định khác → Trợ lý ERP dưới quyền của chính họ. Họ
    không giao được việc sửa mã và không thao tác được việc của bot, nên «viec» / «thao_tac» cũng về Trợ lý.
    """
    if _draft_by_text(db, chat_id, row, text) or _word_by_text(db, chat_id, row, text):
        return
    if _cost_by_text(db, chat_id, row, text):
        return
    if not user_keys.active_key():
        #  ai-CR-053: không lùi về khóa công ty. Dấu lệnh để tin không rơi vào INBOX.
        row.action = ACT_COMMAND
        reply(db, chat_id, user_keys.NO_KEY_HELP)
        return
    run = start_run(db, 0, STAGE_INTENT)
    try:
        data, result = manager.run_intent(text, context=_intent_context(db, chat_id, row.id))
    except Exception as e:  # noqa: BLE001 — phân loại hỏng thì cứ để Trợ lý trả lời
        finish_run(db, run, error=str(e))
        db.commit()
        log.warning("agent_hub: phân loại tin người liên kết hỏng, chuyển Trợ lý")
        answer_question(db, chat_id, text, before_id=row.id)
        return
    finish_run(db, run, result=result)
    db.commit()
    if data["intent"] == manager.INTENT_RESEARCH:
        kind = data.get("kind") or research.MODE_WEB
        run_research(db, chat_id, data.get("query") or text,
                     research.MODE_WEB if kind == research.MODE_DOCS else kind)
        return
    answer_question(db, chat_id, text, before_id=row.id)


def _run_command(db: Session, chat_id: str, text: str) -> None:
    """Các lệnh `/` — nay chỉ là ĐƯỜNG TẮT cho ai quen gõ, không còn bắt buộc."""
    lower = text.lower()
    if m := _LOGIN_CMD.match(text):
        #  Chat của đại ca cũng liên kết được: /hoi khi đó chạy dưới tài khoản của chính đại ca.
        _login_by_code(db, {"chat": {"id": chat_id}}, chat_id, m.group(2), log_row=False)
    elif _LOGOUT_CMD.match(lower):
        _logout(db, chat_id)
    elif lower.startswith("/taikhoan"):
        show_account(db, chat_id)
    elif _research_command(db, chat_id, text, allow_docs=True):
        pass
    elif lower.startswith("/chiphi"):
        code_m = _CODE_IN_TEXT.search(lower)
        task = db.scalar(select(AgentTask).where(AgentTask.code == f"AI-{int(code_m.group(1)):04d}")) if code_m else None
        reply(db, chat_id, cost_report(db, task=task))
    elif lower.startswith("/hoi"):
        answer_question(db, chat_id, text[4:].strip())
    elif lower.startswith("/ds"):
        send_task_list(db, chat_id)
    elif lower.startswith("/xem"):
        show_task(db, chat_id, text[4:].strip())
    elif lower.startswith("/gom"):
        n = triage_inbox(db, force=True)
        if not n:
            reply(db, chat_id, "Không có tin nào đang chờ gom.")
    else:
        reply(db, chat_id,
              f"Em là <b>{BOT_NAME}</b>. Đại ca cứ nhắn bình thường, em tự hiểu, ví dụ:\n"
              "• «3 đơn mua hàng gần nhất» — em tra số liệu ERP\n"
              "• «màn công nợ lọc sai ngày» — em ghi thành việc sửa phần mềm\n"
              "• «tìm hiểu giúp anh thuế nhập khẩu thép» · «có đúng là … không» — em tìm trên mạng, kèm nguồn\n"
              "• «xuất Word giúp anh» — bản Word của lần tìm vừa rồi\n"
              "• «AI-0007 xong chưa» · «tháng này bot tốn bao nhiêu» · «tài khoản anh đang dùng là gì»\n"
              "Lệnh gõ tắt vẫn dùng được nếu muốn chắc (/ds · /xem · /chiphi · /tim · /word · /taikhoan), "
              "trừ đăng nhập phải nhắn <b>/dangnhap &lt;mã&gt;</b> (lấy mã ở Trang cá nhân → Telegram).")


#  Bot vừa hỏi lại mà đại ca nhắn tiếp trong khoảng này thì tin đó LÀ CÂU TRẢ LỜI, không
#  đem đi phân loại nữa. Quá khoảng này thì coi như chuyện mới. Cũng là ranh mà mạch
#  hỏi-đáp của Trợ lý AI đủ ngắn để câu trả lời còn dính vào câu hỏi.
FOLLOW_UP_WINDOW = timedelta(minutes=10)
#  Mạch đưa cho trạm phân loại: chỉ cần lượt hỏi-đáp gần nhất, cắt ngắn — đây là lượt
#  gọi rẻ, đưa cả 6000 ký tự lịch sử vào là biến nó thành lượt gọi đắt.
INTENT_CONTEXT_TURNS = 2
INTENT_CONTEXT_CHARS = 600


def _route_plain_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> None:
    """Tin chữ thường: đưa cho TRỢ LÝ AI hay ghi thành VIỆC SỬA MÃ (ai-CR-003, ai-CR-007).

    Trước đây phải gõ `/hoi` mới được trả lời — đại ca nói đúng là vô lý, vì Trợ lý AI
    trong ERP hỏi phát trả lời luôn chứ có lệnh nào đâu. Nay mỗi tin chữ thường đi qua
    một lượt Gemini rẻ tiền để phân loại trước khi rẽ.

    Hai chốt của ai-CR-007, sau ca AI-0004: Trợ lý hỏi *"nghỉ ngày nào, lý do gì?"*,
    đại ca đáp *"thứ 6, đi du lịch"*, và câu đáp đó bị phân loại rời thành một đầu
    việc sửa mã tên "Xử lý yêu cầu xin nghỉ phép".
      1. Bot vừa hỏi lại (tin ra gần nhất là câu trả lời của Trợ lý AI có dấu hỏi,
         trong `FOLLOW_UP_WINDOW`) thì tin kế là câu trả lời — nối thẳng, không tốn
         lượt phân loại, và không phụ thuộc hạn mức Gemini.
      2. Còn lại thì phân loại NHƯNG đưa kèm lượt hỏi-đáp gần nhất, để model đọc câu
         mới trong mạch chứ không trơ trọi.

    Ba nhánh, và nhánh nào cũng phải ĐÓNG DẤU vào `action` trừ nhánh giao việc — vòng
    gom nhặt đúng những tin còn dấu rỗng, nên để rỗng chính là cách xếp tin vào INBOX.

    Phân loại hỏng (mạng, hết hạn mức, model trả rác) thì HỎI LẠI kèm hai nút, y như
    nhánh mập mờ. Bản trước rơi về giao việc — tức một câu hỏi gặp lúc Gemini 429 là
    thành một thẻ việc 90 giây sau; tin vẫn không mất, nhưng nay đại ca là người chốt.
    """
    #  Bot vừa mời hẹn giờ gộp + deploy (ai-CR-014): tin kế là giờ hẹn, không đi phân loại.
    if task_id := _deploy_time_target(db, chat_id, row):
        _schedule_deploy(db, chat_id, row, text, task_id)
        return
    if task_id := _patch_question_target(db, chat_id, row):
        _ask_patch(db, chat_id, row, text, task_id)
        return
    #  Lệnh gõ bằng chữ trên một việc (ai-CR-027): «gộp AI-0007», «duyệt», «xong»… Đi TRƯỚC mạch trả
    #  lời kế hoạch: đang bị hỏi lại mà nhắn «bỏ việc này» là bỏ, không phải câu trả lời.
    if (_grant_by_text(db, chat_id, row, text) or _runner_by_text(db, chat_id, row, text)
            or _draft_by_text(db, chat_id, row, text)
            or _choice_by_text(db, chat_id, row, text) or _confirm_by_text(db, chat_id, row, text)
            or _word_by_text(db, chat_id, row, text)
            or _cost_by_text(db, chat_id, row, text) or route_task_command(db, chat_id, row, text)):
        return
    #  Trạm kế hoạch vừa hỏi lại (ai-CR-015): tin kế là câu trả lời CỦA VIỆC ĐÓ, không phải việc mới.
    if task_id := _plan_answer_target(db, chat_id, row):
        _answer_plan(db, chat_id, row, text, task_id)
        return

    if _is_follow_up(db, chat_id, row):
        row.action = ACT_ASKED
        answer_question(db, chat_id, text, before_id=row.id)
        return
    if not user_keys.active_key():
        #  ai-CR-053: trên dev đại ca cũng dùng khóa cá nhân; chưa dán thì bot nói thẳng, không đoán.
        row.action = ACT_COMMAND
        reply(db, chat_id, user_keys.NO_KEY_HELP)
        return

    run = start_run(db, 0, STAGE_INTENT)
    try:
        data, result = manager.run_intent(text, context=_intent_context(db, chat_id, row.id),
                                          tasks=_task_context(db, chat_id, row.id))
    except Exception as e:  # noqa: BLE001 - phân loại hỏng không được làm mất tin
        finish_run(db, run, error=str(e))
        log.warning("agent_hub: phân loại ý định hỏng (%s), hỏi lại đại ca", e)
        _ask_intent_choice(db, chat_id, row)
        return
    finish_run(db, run, result=result)

    if data["intent"] == manager.INTENT_ASK:
        row.action = ACT_ASKED
        answer_question(db, chat_id, text, before_id=row.id)
    elif data["intent"] == manager.INTENT_UNSURE:
        _ask_intent_choice(db, chat_id, row)
    elif data["intent"] == manager.INTENT_ACT:
        _act_by_intent(db, chat_id, row, text, data)
    elif data["intent"] == manager.INTENT_RESEARCH:
        row.action = ACT_COMMAND
        db.commit()
        run_research(db, chat_id, data.get("query") or text, data.get("kind") or research.MODE_WEB)
    #  GIAO VIỆC: để `action` rỗng, tin nằm lại INBOX và vòng gom lo tiếp.
    #  ai-CR-021: đại ca muốn biết ngay là bot đã nhận — nhắn MỘT câu báo nhận cho cả chùm tin
    #  liên tiếp (không phải mỗi câu một tiếng chuông, lý do bản cũ im lặng hẳn).
    else:
        ack_task_message(db, chat_id, row)


# ---------------------------------------------------------------------------
# Báo nhận + báo đang chạy (ai-CR-021)
# ---------------------------------------------------------------------------
HEARTBEAT_AFTER = timedelta(seconds=90)     # im quá chừng này thì nhắn «em vẫn đang làm»
HEARTBEAT_STOP = timedelta(minutes=60)      # quá chừng này thì thôi sửa tin (việc kẹt thì /xem)
_TRIAGE_ACTIVE = timedelta(minutes=15)      # việc ở TRIAGE lâu hơn = kẹt, vòng nhặt việc kẹt lo


def ack_task_message(db: Session, chat_id: str, row: AgentMessage) -> None:
    """Một câu «em nhận rồi» cho tin vừa được xếp là việc. Cả chùm tin liên tiếp chỉ một câu:
    đã báo nhận trong khoảng gom mà vẫn còn tin chờ gom thì thôi."""
    window = timedelta(seconds=settings.AGENT_TRIAGE_DELAY_SEC + 120)
    last_ack = db.scalar(
        select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.id < row.id,
                                   AgentMessage.action == ACT_ACK)
        .order_by(AgentMessage.id.desc()).limit(1)
    )
    if last_ack is not None and row.created_at and last_ack.created_at and \
            row.created_at - last_ack.created_at <= window:
        #  Còn tin nào khác đang chờ gom (tin đầu của chùm nằm TRƯỚC câu báo nhận) = cùng chùm.
        pending = db.scalar(select(func.count(AgentMessage.id)).where(
            AgentMessage.chat_id == chat_id, AgentMessage.direction == DIR_IN,
            AgentMessage.task_id == 0, AgentMessage.action == "",
            AgentMessage.id < row.id)) or 0
        if pending:
            return
    seconds = settings.AGENT_TRIAGE_DELAY_SEC
    reply(db, chat_id,
          f"Em nhận tin rồi, anh chờ em xíu. Em gom tin trong khoảng {seconds} giây (anh nhắn thêm "
          "thì em gom chung), rồi đọc mã, kiểm tra và phản hồi.", action=ACT_ACK)


def _active_stage(db: Session, task: AgentTask) -> tuple[str, datetime | None]:
    """(việc đang làm, mốc bắt đầu) của một việc đang chạy; ("", None) nếu không chạy gì."""
    def running(stage: int) -> AgentRun | None:
        return db.scalar(select(AgentRun).where(AgentRun.task_id == task.id, AgentRun.stage == stage,
                                                AgentRun.status == RUN_RUNNING)
                         .order_by(AgentRun.id.desc()).limit(1))

    if task.status == ST_SCANNING:
        run = running(STAGE_SCAN)
        if run is not None:
            return f"đọc mã trên <code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code> để rà soát", run.started_at
        return "chờ runner rảnh để rà soát (runner đang làm việc khác)", task.updated_at
    if task.status == ST_CODE:
        run = running(ST_CODE)
        return ("sửa mã và chạy cổng kiểm", run.started_at) if run is not None else \
            ("chờ runner rảnh để sửa mã", task.updated_at)
    if task.status == ST_DEPLOYING:
        run = running(STAGE_DEPLOY) or running(STAGE_REVERT)
        art = run.artifact if run is not None and isinstance(run.artifact, dict) else {}
        label = "gộp vào nhánh nền" if art.get("deploy") is False else "gộp vào nhánh nền và deploy dev"
        return label, (run.started_at if run is not None else task.updated_at)
    if task.status == ST_TRIAGE:
        #  Lượt lập kế hoạch chỉ commit dòng sổ khi xong nên từ ngoài không thấy nó: dựa vào mốc
        #  việc vào trạm này (updated_at), và chỉ trong 15 phút — lâu hơn là kẹt, không phải đang chạy.
        return "lập kế hoạch sửa", task.updated_at
    return "", None


def _heartbeat_text(task: AgentTask, doing: str, minutes: int) -> str:
    return (f"<b>{telegram.esc(task.code)}</b>: em vẫn đang {doing}, đã {max(minutes, 1)} phút, "
            "anh đợi em xíu. Xong em nhắn ngay.")


def heartbeat(db: Session, now: datetime | None = None) -> int:
    """Vòng beat mỗi phút: việc đang chạy mà quá 90 giây chưa có tin nào thì nhắn «em vẫn đang
    làm»; đã nhắn rồi thì SỬA chính tin đó cho đúng số phút (không kêu chuông lần nữa).
    Trả số tin đã gửi hoặc sửa."""
    now = now or datetime.now()
    chat_id = settings.AGENT_TELEGRAM_CHAT_ID
    tasks = db.scalars(select(AgentTask).where(
        AgentTask.status.in_((ST_SCANNING, ST_CODE, ST_DEPLOYING, ST_TRIAGE)))).all()
    touched = 0
    for task in tasks:
        doing, start = _active_stage(db, task)
        if not doing or start is None:
            continue
        elapsed = now - start
        if elapsed > HEARTBEAT_STOP or (task.status == ST_TRIAGE and elapsed > _TRIAGE_ACTIVE):
            continue
        minutes = int(elapsed.total_seconds() // 60)
        hb = db.scalar(select(AgentMessage).where(
            AgentMessage.task_id == task.id, AgentMessage.action == ACT_HEARTBEAT,
            AgentMessage.created_at >= start).order_by(AgentMessage.id.desc()).limit(1))
        text = _heartbeat_text(task, doing, minutes)
        if hb is not None:
            if hb.body != text and telegram.edit_text(chat_id, hb.tg_message_id, text):
                hb.body = text
                db.commit()
                touched += 1
            continue
        last_out = db.scalar(select(func.max(AgentMessage.created_at)).where(
            AgentMessage.task_id == task.id, AgentMessage.direction == DIR_OUT))
        quiet_since = max(start, last_out) if last_out else start
        if now - quiet_since < HEARTBEAT_AFTER:
            continue
        reply(db, chat_id, text, task_id=task.id, action=ACT_HEARTBEAT)
        db.commit()
        touched += 1
    return touched


# ---------------------------------------------------------------------------
# Lệnh gõ bằng chữ trên một việc (ai-CR-027)
# ---------------------------------------------------------------------------
#  Đại ca 23/09: «anh không thích chọn option dưới dòng tin nhắn, anh thích nhắn vào». Chữ «gộp»,
#  «bỏ» còn nằm trong chính yêu cầu sửa phần mềm («bỏ ô Từ–Đến»), nên một tin chỉ là LỆNH khi:
#  nêu mã việc (AI-0007), HOẶC là câu ngắn chỉ vào việc vừa làm («này», «vừa sửa»…), HOẶC chỉ gồm
#  vài chữ («duyệt», «gộp đi», «xong rồi»). Câu dạng HỎI thì chỉ trả lời tình trạng, không làm gì.
_CODE_IN_TEXT = re.compile(r"(?i)\bai[-\s]?0*(\d{1,6})\b")
#  «Chỉ vào việc» phải là cụm CÓ DANH TỪ («việc này», «fix này», «code vừa sửa», «commit mới này»):
#  «mới», «này» đứng một mình thì «bỏ nút tạo mới này» — một yêu cầu MỚI — thành lệnh bỏ việc.
_TASK_DEICTIC = re.compile(
    r"(?<!\w)(việc|fix|bản sửa|bản vá|commit|code|mã)(?!\w).{0,25}(?<!\w)(này|nãy|đó|vừa|mới)(?!\w)")
#  Lệnh TRƠN (không mã việc, không cụm chỉ vào việc): chỉ gồm động từ + vài chữ đệm. «gộp hai cột
#  ngày» không khớp -> không phải lệnh, đi đường cũ thành việc mới.
_BARE = {
    "merge": r"^(tự\s+)?(gộp|merge)(\s+(đi|luôn|nhé|nha|code|vào|qua|lên|erp[-\s]?v2|dev|nhánh|nền|giúp|anh|em"
             r"|và|rồi|deploy|triển khai|đẩy))*[.! ]*$",
    "deploy": r"^(deploy|triển khai|đẩy lên dev|lên dev)(\s+(dev|đi|luôn|nhé|nha|lại|giúp|anh|em|lên))*[.! ]*$",
    "approve": r"^(ok[, ]+)?duyệt(\s+(đi|luôn|nhé|nha|kế hoạch))*[.! ]*$",
    "done": r"^(xong|đóng)(\s+(rồi|việc|nhé|đi|nha))*[.! ]*$",
    "cancel": r"^(bỏ|hủy)(\s+(việc|đi|luôn))+[.! ]*$",
    "continue": r"^làm tiếp(\s+(đi|nhé|nha))*[.! ]*$",
    "fixgate": r"^sửa cho (xanh|qua)(\s+(đi|nhé|nha))*[.! ]*$",
    "revert": r"^(thu hồi|revert)(\s+(đi|luôn|nhé))*[.! ]*$",
    "pr": r"^(mở pr|gửi link pr|link pr)[.! ]*$",
    "detail": r"^(chi tiết|xem)[.! ]*$",
}
_QUESTION = re.compile(r"\?|được không|(?<!\w)(chưa|nào|sao|đâu)(?!\w)")
_SCHEDULE_WORDS = re.compile(r"(?<!\w)(lúc|hẹn|nữa|sáng|chiều|tối|mai)(?!\w)|\d{1,2}\s*(h|:|giờ)")
_COMMANDS = (   # (tên, mẫu) — thứ tự là thứ tự ưu tiên
    ("rule_yes", r"^ghi (sổ|vào sổ)\b"),
    ("rule_no", r"^(không ghi|đừng ghi)\b"),
    ("fixgate", r"(?<!\w)sửa cho (xanh|qua)(?!\w)"),
    ("continue", r"(?<!\w)làm tiếp(?!\w)"),
    ("revert", r"(?<!\w)(thu hồi|revert)(?!\w)"),
    ("merge", r"(?<!\w)(gộp|merge)(?!\w)"),
    ("deploy", r"(?<!\w)(deploy|triển khai|lên dev)(?!\w)"),
    ("approve", r"^(ok[, ]+)?duyệt(?!\w)"),
    ("replan", r"^sửa( lại)?\s*[:：]"),
    ("pr", r"(?<!\w)(mở pr|link pr)(?!\w)"),
    ("detail", r"^(chi tiết|xem)(?!\w)"),
    ("done", r"^(xong|đóng)(\s+(rồi|việc|nhé|đi|nha))?(?!\w)"),
    ("cancel", r"^(bỏ|hủy)\s+(việc|đi|luôn|hẹn)(?!\w)|^(bỏ|hủy)\s+ai[-\s]?\d"),
)
_OPEN_FOR = {   # thao tác -> trạng thái việc hợp lệ khi đoán việc (không nêu mã)
    "merge": (ST_REVIEW, ST_PROD), "deploy": (ST_PROD,), "revert": (ST_PROD,), "approve": (ST_PLAN,),
    "replan": (ST_PLAN, ST_NEEDS_INPUT), "continue": (ST_NEEDS_INPUT,), "fixgate": (ST_REVIEW,),
    "done": (ST_REVIEW, ST_PROD), "pr": (ST_REVIEW,), "cancel": None, "detail": None, "status": None,
}


def _match_command(text: str) -> str:
    low = text.strip().lower()
    for name, pattern in _COMMANDS:
        if re.search(pattern, low):
            return name
    return ""


def _candidates(db: Session, action: str) -> list[AgentTask]:
    states = _OPEN_FOR.get(action)
    q = select(AgentTask).where(AgentTask.status.not_in(CLOSED_STATUSES))
    if states:
        q = q.where(AgentTask.status.in_(states))
    rows = list(db.scalars(q.order_by(AgentTask.updated_at.desc()).limit(10)))
    if action == "merge":
        rows = [t for t in rows if not (t.status == ST_PROD and t.deployed_dev_at)]
    if action == "deploy":
        rows = [t for t in rows if not t.deployed_dev_at and coder.merged_sha_for(db, t)]
    if action == "revert":
        rows = [t for t in rows if coder.merged_sha_for(db, t)]
    if action == "fixgate":
        rows = [t for t in rows if _red_gate(db, t)]
    if action == "continue":
        rows = [t for t in rows if coder.resumable_session(db, t)]
    return rows


def route_task_command(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """Tin này là lệnh trên một việc thì làm và trả True; không phải thì False (đi đường cũ)."""
    low = text.strip().lower()
    words = len(low.split())
    code_m = _CODE_IN_TEXT.search(low)
    pointed = bool(code_m) or (words <= 20 and bool(_TASK_DEICTIC.search(low)))
    action = _match_command(low)
    if action in ("rule_yes", "rule_no"):
        return _rule_by_text(db, chat_id, row, action)
    if _QUESTION.search(low) and pointed and action not in ("detail", "replan"):
        action = "status"
    elif not action:
        return False
    bare = bool(re.match(_BARE[action], low)) if action in _BARE else False
    if not (pointed or bare or action == "replan"):
        return False

    if code_m:
        task = db.scalar(select(AgentTask).where(AgentTask.code == f"AI-{int(code_m.group(1)):04d}"))
        if task is None:
            reply(db, chat_id, f"Không có việc <b>AI-{int(code_m.group(1)):04d}</b> trong sổ.")
            row.action = ACT_COMMAND
            return True
    else:
        found = _candidates(db, action)
        if not found:
            if bare:
                row.action = ACT_COMMAND
                reply(db, chat_id, "Không có việc nào đang ở bước đó. Nhắn kèm mã việc, ví dụ «gộp AI-0007».")
                return True
            return False
        if len(found) > 1:
            row.action = ACT_COMMAND
            listing = " · ".join(f"<b>{telegram.esc(t.code)}</b> ({telegram.esc(t.title[:40])})" for t in found[:4])
            reply(db, chat_id, f"Đại ca nói việc nào: {listing}? Nhắn kèm mã việc.")
            return True
        task = found[0]

    row.action = ACT_COMMAND
    row.task_id = task.id
    db.commit()
    #  K-04 (ai-CR-051): chat khác đại ca phải đủ cấp mới được chạm vào việc.
    if not _grant_allows(db, chat_id, row, task, action, text):
        return True
    _run_task_command(db, chat_id, row, task, action, text)
    _notify_admin_action(db, chat_id, task, action, text)
    return True


_DEPLOY_WORDS = re.compile(r"(?<!\w)(deploy|triển khai|lên dev|đẩy dev)(?!\w)")


def _deploy_what(deploy: bool, merged: bool) -> str:
    base = f"<code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code>"
    if not deploy:
        return f"gộp vào {base} (không deploy dev)"
    return "deploy dev" if merged else f"gộp vào {base} + deploy dev"


def _run_task_command(db: Session, chat_id: str, row: AgentMessage, task: AgentTask, action: str,
                      text: str) -> None:
    code = telegram.esc(task.code)
    if action == "status":
        reply(db, chat_id, task_status_line(db, task), task_id=task.id)
    elif action == "detail":
        show_task(db, chat_id, task.code)
    elif task.status in CLOSED_STATUSES:
        reply(db, chat_id, f"<b>{code}</b> đã đóng rồi. Xem lại: «chi tiết {code}».", task_id=task.id)
    elif action in ("merge", "deploy"):
        #  Đại ca GÕ lệnh gộp = đồng ý gộp (luật ai-CR-014: muốn gộp phải hỏi, anh đồng ý mới làm).
        #  «gộp» CHỈ gộp vào nhánh nền; lên dev phải nói ra (ai-CR-029).
        deploy = action == "deploy" or bool(_DEPLOY_WORDS.search(text.lower()))
        merged = bool(coder.merged_sha_for(db, task))
        if action == "deploy" and not merged:
            reply(db, chat_id, f"<b>{code}</b> chưa gộp vào <code>{telegram.esc(settings.AGENT_BASE_BRANCH)}"
                  f"</code> nên chưa lên dev được. Nhắn «gộp và deploy dev {code}» để làm cả hai.", task_id=task.id)
            db.commit()
            return
        if merged and not deploy:
            reply(db, chat_id, f"<b>{code}</b> đã gộp vào <code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code> "
                  + ("và đã lên dev rồi." if task.deployed_dev_at else f"rồi, dev chưa lên. Muốn lên dev thì nhắn "
                     f"«deploy dev {code}»."), task_id=task.id)
            db.commit()
            return
        what = _deploy_what(deploy, merged)
        when = parse_schedule_time(text, now_local()) if _SCHEDULE_WORDS.search(text.lower()) else None
        if when is not None and (blocked := _deploy_blocker(db, task)):
            reply(db, chat_id, f"<b>{code}</b>: {telegram.esc(blocked)}", task_id=task.id)
        elif when is not None and when > now_local():
            _new_deploy_run(db, task, STAGE_DEPLOY, "hen_gio", deploy=deploy,
                            scheduled_for=to_utc(when).isoformat(timespec="minutes"), approved_by=chat_id)
            reply(db, chat_id, f"Đã hẹn <b>{when:%H:%M %d/%m}</b>: {what} <b>{code}</b>. Đổi ý thì nhắn "
                  f"«hủy hẹn {code}».", task_id=task.id)
        else:
            _dispatch_deploy(db, chat_id, "", task, deploy=deploy)
    elif action == "revert":
        _dispatch_revert(db, chat_id, "", task)
    elif action == "approve":
        if task.status != ST_PLAN:
            reply(db, chat_id, f"<b>{code}</b> không ở bước chờ duyệt kế hoạch.", task_id=task.id)
        else:
            approve_task(db, chat_id, "", task)
    elif action == "replan":
        body = re.split(r"[:：]", text, maxsplit=1)[-1].strip()
        if not body:
            reply(db, chat_id, "Nhắn «sửa: <điều cần đổi>» để em lập lại kế hoạch.", task_id=task.id)
        else:
            _answer_plan(db, chat_id, row, body, task.id)
    elif action == "continue":
        start_continue(db, chat_id, "", task)
    elif action == "fixgate":
        start_fix_gate(db, chat_id, "", task)
    elif action == "pr":
        _dispatch_publish(db, chat_id, "", task)
    elif action == "done":
        close_done(db, chat_id, "", task)
    elif action == "cancel":
        run = coder.pending_deploy_run(db, task)
        if run is not None and _run_phase(run) == "hen_gio" and "hẹn" in text.lower():
            _cancel_deploy(db, chat_id, "", task)
        else:
            cancel_task(db, chat_id, "", task)
    db.commit()


def task_status_line(db: Session, task: AgentTask) -> str:
    """Trả lời GỌN câu hỏi về một việc: đang ở đâu, nhánh nào, gộp chưa, nhắn gì tiếp."""
    esc = telegram.esc
    code = esc(task.code)
    parts = [f"<b>{code}</b> · {esc(task.title)}: <b>{esc(TASK_STATUS_LABELS.get(task.status, '?'))}</b>."]
    if task.branch_name:
        parts.append(f"Nhánh <code>{esc(task.branch_name)}</code>.")
    if task.runner_id and (rn := db.get(AgentRunner, task.runner_id)) is not None:
        parts.append(f"Máy <b>{esc(rn.name)}</b> ({'đang bật' if runners.is_online(rn) else 'đang tắt'}).")
    merged = coder.merged_sha_for(db, task)
    if merged:
        parts.append(f"Đã gộp vào <code>{esc(settings.AGENT_BASE_BRANCH)}</code> (<code>{esc(merged[:10])}</code>)"
                     + (f", lên dev {fmt_local(task.deployed_dev_at)}." if task.deployed_dev_at else ", dev chưa lên."))
    last = coder.latest_code_run(db, task)
    gate = ((last.artifact or {}).get("gate") if last is not None and isinstance(last.artifact, dict) else None)
    if gate:
        parts.append(f"Cổng kiểm: {esc(coder._gate_brief(gate))}.")
    nxt = {
        ST_PLAN: f"Nhắn «duyệt» để em sửa mã hoặc «sửa: …».",
        ST_REVIEW: (f"Nhắn «sửa cho xanh {code}»." if _red_gate(db, task)
                    else f"Gộp được: nhắn «gộp {code}» (chỉ gộp, chưa lên dev) hoặc «gộp và deploy dev "
                         f"{code}»; thêm «lúc 20h» để hẹn giờ."),
        ST_PROD: (f"Nhắn «xong {code}» nếu ổn, «thu hồi {code}» nếu không." if task.deployed_dev_at
                  else f"Dev chưa lên: nhắn «deploy dev {code}», hoặc «thu hồi {code}» nếu gộp nhầm."),
        ST_NEEDS_INPUT: (f"Nhắn «làm tiếp {code}»." if coder.resumable_session(db, task)
                         else "Em đang chờ đại ca trả lời câu hỏi ở thẻ kế hoạch."),
    }.get(task.status, "")
    if nxt:
        parts.append(nxt)
    return " ".join(parts)


def _rule_by_text(db: Session, chat_id: str, row: AgentMessage, action: str) -> bool:
    """«ghi sổ» / «không ghi» cho thẻ đề xuất sổ quyết định gần nhất đang chờ (ai-CR-027)."""
    runs = db.scalars(select(AgentRun).where(AgentRun.stage == STAGE_RULE)
                      .order_by(AgentRun.id.desc()).limit(5)).all()
    run = next((r for r in runs if isinstance(r.artifact, dict) and r.artifact.get("state") == "cho_duyet"), None)
    if run is None:
        return False
    task = db.get(AgentTask, run.task_id)
    if task is None:
        return False
    row.action = ACT_COMMAND
    row.task_id = task.id
    _resolve_rule(db, chat_id, "", "qdok" if action == "rule_yes" else "qdno", task)
    if action == "rule_no":
        reply(db, chat_id, "Được, lần sau gặp tình huống đó em vẫn hỏi.", task_id=task.id)
    db.commit()
    return True


def _choice_by_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """Trả lời bằng chữ cho câu «làm luôn hay ghi việc» (thay hai nút, ai-CR-027)."""
    low = text.strip().lower()
    kind = "hoi" if re.fullmatch(r"(làm luôn|hỏi|trả lời|làm ngay)[.! ]*", low) else \
        "viec" if re.fullmatch(r"(ghi việc|việc|sửa mã|ghi thành việc)[.! ]*", low) else ""
    if not kind:
        return False
    pending = db.scalar(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.id < row.id,
                                                   AgentMessage.action == ACT_WAIT_CHOICE)
                        .order_by(AgentMessage.id.desc()).limit(1))
    if pending is None or (row.created_at and pending.created_at
                           and row.created_at - pending.created_at > FOLLOW_UP_WINDOW):
        return False
    row.action = ACT_COMMAND
    _resolve_intent(db, chat_id, "", kind, pending.id)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Hiểu ý thao tác theo ngữ cảnh (ai-CR-028)
# ---------------------------------------------------------------------------
#  Đại ca: «thay vì lệnh thì trợ lý phân tích ý định dựa trên văn bản mà làm, ví dụ anh nói đồng ý».
#  Lệnh gõ đúng mẫu vẫn đi đường nhanh ở `route_task_command` (không tốn lượt model). Câu tự do
#  thì lượt phân loại SẴN CÓ đọc thêm danh sách việc đang mở + tin bot vừa nhắn, và trả thêm một
#  loại «thao_tac». Chắc thì làm; chưa chắc thì hỏi lại một câu, và câu «đúng» sau đó chạy bằng
#  dấu đã ghi chứ không hỏi model lần nữa.
TASK_CONTEXT_LIMIT = 8
_YES = re.compile(r"^(đúng|đúng rồi|ừ|ừm|ờ|ok|oke|okay|được|đồng ý|phải|chuẩn|chính xác|làm đi|triển"
                  r"|có)(\s+(rồi|đó|luôn|đi|nhé|nha|em|vậy|á))*[.! ]*$")
_NO = re.compile(r"^(không|ko|khong|sai|thôi|đừng|chưa)(\s+(phải|đúng|làm|đâu|rồi|nhé|nha|em|đi))*[.! ]*$")
#  Nhãn nói lại cho đại ca nghe khi hỏi xác nhận.
_ACTION_LABELS = {
    "approve": "duyệt kế hoạch", "replan": "lập lại kế hoạch", "merge": "gộp vào nhánh nền",
    "deploy": "deploy dev",
    "revert": "thu hồi khỏi nhánh nền", "done": "đóng việc", "cancel": "bỏ việc", "continue": "làm tiếp",
    "fixgate": "sửa cho cổng kiểm xanh", "detail": "xem chi tiết", "pr": "mở PR",
    "status": "báo tình trạng", "rule_yes": "ghi vào sổ quyết định", "rule_no": "không ghi sổ",
}
#  Thao tác đổi mã/nhánh: model nói chắc vẫn phải khớp đúng bước của việc mới được làm ngay.
_RISKY_ACTIONS = ("merge", "deploy", "revert", "cancel")


def _task_context(db: Session, chat_id: str, before_id: int) -> str:
    """Việc đang mở + tin bot vừa nhắn, dạng chữ trơn cho trạm phân loại."""
    rows = db.scalars(select(AgentTask).where(AgentTask.status.not_in(CLOSED_STATUSES))
                      .order_by(AgentTask.updated_at.desc()).limit(TASK_CONTEXT_LIMIT)).all()
    parts = []
    if rows:
        lines = [_strip_tags(task_status_line(db, t)) for t in rows]
        parts.append("VIỆC ĐANG MỞ:\n" + "\n".join(f"- {line}" for line in lines))
    last = db.scalar(select(AgentMessage)
                     .where(AgentMessage.chat_id == chat_id, AgentMessage.id < before_id,
                            AgentMessage.direction == DIR_OUT, AgentMessage.action.not_in(NOISE_ACTIONS))
                     .order_by(AgentMessage.id.desc()).limit(1))
    if last is not None and last.body:
        parts.append("TIN BOT VỪA NHẮN:\n" + _strip_tags(last.body)[:INTENT_CONTEXT_CHARS])
    return "\n\n".join(parts)


def _strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", "", html or ""))).strip()


def _act_by_intent(db: Session, chat_id: str, row: AgentMessage, text: str, data: dict) -> None:
    """Model đọc ra một thao tác trên việc: chắc thì làm, chưa chắc thì hỏi lại một câu."""
    action = data["action"]
    if action in ("rule_yes", "rule_no"):
        if not _rule_by_text(db, chat_id, row, action):
            row.action = ACT_COMMAND
            reply(db, chat_id, "Không có đề xuất ghi sổ nào đang chờ.")
        return
    task = None
    if data.get("task"):
        task = db.scalar(select(AgentTask).where(AgentTask.code == data["task"]))
    if task is None:
        found = _candidates(db, action)
        if len(found) != 1:
            row.action = ACT_COMMAND
            if not found:
                reply(db, chat_id, f"Em hiểu là đại ca muốn {_ACTION_LABELS[action]}, nhưng không có việc nào "
                      "đang ở bước đó. Nhắn kèm mã việc giúp em.")
            else:
                listing = " · ".join(f"<b>{telegram.esc(t.code)}</b>" for t in found[:4])
                reply(db, chat_id, f"Đại ca muốn {_ACTION_LABELS[action]} việc nào: {listing}?")
            return
        task = found[0]
    sure = bool(data.get("confident"))
    if sure and action in _RISKY_ACTIONS:
        states = _OPEN_FOR.get(action)
        sure = task in _candidates(db, action) if states else task.status not in CLOSED_STATUSES
    cmd_text = text
    if action in ("merge", "deploy") and data.get("when"):
        #  Giữ chữ «deploy/lên dev» của câu gốc: nó quyết định có lên dev hay chỉ gộp (ai-CR-029).
        cmd_text = f"gộp {data['when']}" + (" deploy dev" if action == "deploy" or _DEPLOY_WORDS.search(text.lower())
                                             else "")
    row.action = ACT_COMMAND
    row.task_id = task.id
    if not sure:
        db.commit()
        reply(db, chat_id, f"Ý đại ca là <b>{_ACTION_LABELS[action]}</b> việc <b>{telegram.esc(task.code)}</b> "
              f"({telegram.esc(task.title[:50])}) phải không? Nhắn «đúng» để em làm.",
              task_id=task.id, action=ACT_WAIT_CONFIRM + action)
        return
    db.commit()
    _run_intent_action(db, chat_id, row, task, action, cmd_text, data.get("detail") or "")


def _run_intent_action(db: Session, chat_id: str, row: AgentMessage, task: AgentTask, action: str,
                       text: str, detail: str) -> None:
    if action == "replan":
        #  Câu tự do không có dấu «sửa:» — đưa thẳng ý cần đổi cho trạm kế hoạch.
        _answer_plan(db, chat_id, row, detail or text, task.id)
        db.commit()
        return
    _run_task_command(db, chat_id, row, task, action, text)


def _confirm_by_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """«đúng» / «không» cho câu bot vừa hỏi xác nhận thao tác (ai-CR-028)."""
    low = text.strip().lower()
    yes, no = bool(_YES.match(low)), bool(_NO.match(low))
    if not (yes or no):
        return False
    last = db.scalar(select(AgentMessage)
                     .where(AgentMessage.chat_id == chat_id, AgentMessage.id < row.id,
                            AgentMessage.action.not_in(NOISE_ACTIONS))
                     .order_by(AgentMessage.id.desc()).limit(1))
    if last is None or not (last.action or "").startswith(ACT_WAIT_CONFIRM) or not last.task_id:
        return False
    if row.created_at and last.created_at and row.created_at - last.created_at > FOLLOW_UP_WINDOW:
        return False
    task = db.get(AgentTask, last.task_id)
    action = last.action[len(ACT_WAIT_CONFIRM):]
    if task is None or action not in _ACTION_LABELS:
        return False
    row.action = ACT_COMMAND
    row.task_id = task.id
    last.action = ACT_COMMAND       # câu hỏi đã được trả lời, «đúng» lần hai không chạy lại
    db.commit()
    if no:
        reply(db, chat_id, "Dạ, em không làm. Đại ca nhắn lại ý khác giúp em.", task_id=task.id)
        db.commit()
        return True
    #  Lấy lại chính câu đại ca nhắn trước câu hỏi xác nhận: giờ hẹn gộp / ý sửa kế hoạch nằm trong đó.
    origin = db.scalar(select(AgentMessage)
                       .where(AgentMessage.chat_id == chat_id, AgentMessage.id < last.id,
                              AgentMessage.direction == DIR_IN)
                       .order_by(AgentMessage.id.desc()).limit(1))
    _run_intent_action(db, chat_id, row, task, action, origin.body if origin else "", "")
    return True


# ---------------------------------------------------------------------------
# Ai được ra lệnh sửa mã (ai-CR-051, K-01 «cách 3» + K-04)
# ---------------------------------------------------------------------------
GRANT_WINDOW = timedelta(minutes=15)


def _grant_level(db: Session, chat_id: str) -> int:
    """Cấp của chat này: chat đại ca = tối đa; chat khác = cấp của tài khoản ERP đã liên kết."""
    if telegram.is_allowed_chat(chat_id):
        return grants.LEVEL_ADMIN
    link = chat_link.get_active_link(db, chat_id)
    return grants.level_for(db, link.user_id) if link is not None else grants.LEVEL_NONE


def _grant_by_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """Chat đại ca: «cho anh Được quyền gộp dev» → hỏi lại → «đúng» ghi sổ; «gỡ quyền …»; «ai đang được
    sửa mã». Chỉ chat đại ca cấp được — chat khác nhắn câu này thì đi đường thường (Trợ lý trả lời)."""
    if not telegram.is_allowed_chat(chat_id):
        return False
    low = text.strip().lower()
    pending = db.scalar(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_GRANT_WAIT, AgentMessage.id < row.id)
        .order_by(AgentMessage.id.desc()).limit(1))
    live = pending is not None and not (row.created_at and pending.created_at
                                        and row.created_at - pending.created_at > GRANT_WINDOW)
    if live and (_YES.match(low) or _NO.match(low)):
        return _grant_confirm(db, chat_id, row, pending, yes=bool(_YES.match(low)))
    parsed = grants.parse(text)
    if parsed is None:
        return False
    row.action = ACT_COMMAND
    if pending is not None and pending.action == ACT_GRANT_WAIT:
        pending.action = ACT_GRANT_DROPPED      # câu mới thay câu hỏi cũ chưa trả lời
    if parsed["op"] == "list":
        reply(db, chat_id, _grant_listing(db))
        db.commit()
        return True
    users = grants.find_users(db, parsed["name"])
    esc = telegram.esc
    if not users:
        reply(db, chat_id, f"Em không tìm thấy tài khoản ERP nào tên «{esc(parsed['name'])}». Đại ca nhắn họ tên "
              "đầy đủ hoặc tên đăng nhập giúp em.")
        db.commit()
        return True
    if len(users) > 1:
        names = " · ".join(esc(describe_user(db, u)[0]) for u in users[:5])
        reply(db, chat_id, f"Có {len(users)} người khớp «{esc(parsed['name'])}»: {names}. Đại ca nhắn rõ tên hơn giúp em.")
        db.commit()
        return True
    user = users[0]
    label, _detail = describe_user(db, user)
    if parsed["op"] == "revoke":
        if not grants.active_grant(db, user.id):
            reply(db, chat_id, f"<b>{esc(label)}</b> hiện không có quyền sửa mã nào để gỡ.")
            db.commit()
            return True
        question = f"Gỡ quyền sửa mã của <b>{esc(label)}</b>? Nhắn «đúng» để gỡ, «thôi» để giữ."
        info = {"op": "revoke", "user_id": user.id}
    else:
        level = parsed["level"]
        current = grants.level_for(db, user.id)
        if current == level:
            reply(db, chat_id, f"<b>{esc(label)}</b> đã ở cấp <b>{grants.LEVEL_LABELS[level]}</b> rồi.")
            db.commit()
            return True
        note = "" if grants.is_linked(db, user.id) else (" Người này CHƯA đăng nhập bot; cấp trước được, có "
                                                          "hiệu lực khi họ nhắn /dangnhap.")
        question = (f"Cấp cho <b>{esc(label)}</b> cấp <b>{grants.LEVEL_LABELS[level]}</b> "
                    f"({esc(grants.LEVEL_SCOPE[level])})?{esc(note)} Nhắn «đúng» để cấp, «thôi» để bỏ.")
        info = {"op": "grant", "user_id": user.id, "level": level}
    reply(db, chat_id, question)
    log_message(db, DIR_OUT, chat_id, 0, json.dumps(info), action=ACT_GRANT_WAIT)
    db.commit()
    return True


def _grant_confirm(db: Session, chat_id: str, row: AgentMessage, pending: AgentMessage, *, yes: bool) -> bool:
    from app.modules.user.model import User

    row.action = ACT_COMMAND
    try:
        info = json.loads(pending.body or "{}")
    except ValueError:
        info = {}
    user = db.get(User, int(info.get("user_id") or 0))
    if not yes or user is None:
        pending.action = ACT_GRANT_DROPPED
        db.commit()
        reply(db, chat_id, "Dạ, em không đổi quyền gì.")
        return True
    pending.action = ACT_GRANT_DONE
    db.commit()
    label, _detail = describe_user(db, user)
    esc = telegram.esc
    if info.get("op") == "revoke":
        grants.revoke(db, user.id)
        reply(db, chat_id, f"Đã gỡ quyền sửa mã của <b>{esc(label)}</b>. Từ giờ người này chỉ hỏi Trợ lý được.")
        log.info("agent_hub: gỡ quyền sửa mã user=%s bởi chat %s", user.id, chat_id)
        return True
    level = int(info.get("level") or grants.LEVEL_PLAN)
    grants.grant(db, user.id, level, by_chat=chat_id)
    reply(db, chat_id, f"Đã cấp cho <b>{esc(label)}</b> cấp <b>{grants.LEVEL_LABELS.get(level, '?')}</b>. Ghi sổ "
          f"{fmt_local(datetime.now())}. Hỏi «ai đang được sửa mã» để xem lại; «gỡ quyền của {esc(label.split(' (')[0])}» để gỡ.")
    log.info("agent_hub: cấp quyền sửa mã user=%s cấp %s bởi chat %s", user.id, level, chat_id)
    return True


def _grant_listing(db: Session) -> str:
    from app.modules.user.model import User

    rows = grants.list_active(db)
    if not rows:
        return "Chưa cấp quyền sửa mã cho ai ngoài chat của đại ca."
    esc = telegram.esc
    lines = ["<b>Đang được ra lệnh sửa mã qua bot:</b>"]
    for g in rows:
        label, _detail = describe_user(db, db.get(User, g.user_id))
        linked = "" if grants.is_linked(db, g.user_id) else " · chưa đăng nhập bot"
        lines.append(f"• {esc(label or f'tài khoản #{g.user_id}')} — cấp <b>{grants.LEVEL_LABELS.get(int(g.level), '?')}</b>"
                     f", từ {fmt_local(g.created_at)}{linked}")
    lines.append("Chat của đại ca luôn đủ mọi cấp. Prod không cấp cho ai.")
    return "\n".join(lines)


def _grant_allows(db: Session, chat_id: str, row: AgentMessage, task: AgentTask, action: str, text: str) -> bool:
    """K-04: lệnh trên việc từ chat KHÔNG phải đại ca phải đủ cấp; thiếu thì từ chối và báo đại ca."""
    level = _grant_level(db, chat_id)
    need = grants.required_level(action)
    if level >= need:
        return True
    from app.modules.user.model import User

    link = chat_link.get_active_link(db, chat_id)
    label = describe_user(db, db.get(User, link.user_id))[0] if link is not None else f"chat {chat_link.mask_chat(chat_id)}"
    esc = telegram.esc
    row.action = ACT_DENIED
    have = grants.LEVEL_LABELS.get(level, "chưa có quyền")
    reply(db, chat_id, f"Lệnh «{esc(_ACTION_LABELS.get(action, action))}» cần cấp <b>{grants.LEVEL_LABELS.get(need, 'đại ca')}"
          f"</b>; anh/chị đang ở cấp <b>{have}</b>. Em đã báo đại ca.", task_id=task.id)
    reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
          f"<b>{esc(label)}</b> vừa nhắn «{esc(text[:80])}» trên <b>{esc(task.code)}</b> nhưng chỉ ở cấp {have}. "
          f"Muốn cho thì nhắn «cho {esc(label.split(' (')[0])} quyền {grants.LEVEL_LABELS.get(need, 'gộp dev')}».",
          task_id=task.id)
    db.commit()
    return False


# ---------------------------------------------------------------------------
# Máy sửa mã (ai-CR-054, D-03 + D-05): đăng ký / gỡ / liệt kê / chỉ định bằng câu nhắn của đại ca
# ---------------------------------------------------------------------------
def _runner_wait_note(db: Session, task: AgentTask, chat_id: str = "") -> None:
    """Việc vừa được đẩy vào hàng đợi của một máy đang TẮT: nói rõ đang chờ máy nào (vé nằm chờ, không mất)."""
    if not task.runner_id:
        return
    rn = db.get(AgentRunner, task.runner_id)
    if rn is None or runners.is_online(rn):
        return
    seen = f" (liên lạc lần cuối {fmt_local(rn.last_seen_at)})" if rn.last_seen_at else " (chưa liên lạc lần nào)"
    reply(db, chat_id or settings.AGENT_TELEGRAM_CHAT_ID,
          f"<b>{telegram.esc(task.code)}</b> đang chờ máy <b>{telegram.esc(rn.name)}</b> bật{telegram.esc(seen)}. "
          "Bật máy là em làm ngay; muốn máy khác làm thì nhắn «" + telegram.esc(task.code) + " cho máy ‹tên› làm».",
          task_id=task.id)


def _runner_listing(db: Session) -> str:
    rows = runners.active(db)
    if not rows:
        return ("Chưa đăng ký máy sửa mã nào: bot và runner đang chạy chung một máy (hàng đợi cũ). Thêm máy: "
                "«thêm máy của anh Được».")
    esc = telegram.esc
    lines = ["<b>Máy sửa mã:</b>"]
    for r in rows:
        state = "đang bật" if runners.is_online(r) else ("tắt từ " + fmt_local(r.last_seen_at) if r.last_seen_at else "chưa liên lạc")
        busy = runners.running_count(db, r.id)
        lines.append(f"• <b>{esc(runners.describe(db, r))}</b> — {state}, {busy} việc đang chạy, deploy dev: "
                     f"{'có' if r.can_deploy else 'không'}")
    return "\n".join(lines)


def _runner_by_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """Chat đại ca: «thêm máy của anh Được» → hỏi lại → «đúng» tạo mã máy (hiện MỘT lần); «tắt máy …»;
    «máy nào đang bật»; «AI-0012 cho máy anh Được làm»; «cho máy … được deploy»."""
    if not telegram.is_allowed_chat(chat_id):
        return False
    low = text.strip().lower()
    pending = db.scalar(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_RUNNER_WAIT, AgentMessage.id < row.id)
        .order_by(AgentMessage.id.desc()).limit(1))
    live = pending is not None and not (row.created_at and pending.created_at
                                        and row.created_at - pending.created_at > GRANT_WINDOW)
    if live and (_YES.match(low) or _NO.match(low)):
        return _runner_confirm(db, chat_id, row, pending, yes=bool(_YES.match(low)))
    parsed = runners.parse(text)
    if parsed is None:
        return False
    row.action = ACT_COMMAND
    if pending is not None and pending.action == ACT_RUNNER_WAIT:
        pending.action = ACT_RUNNER_DROPPED
    esc = telegram.esc
    op = parsed["op"]
    if op == "list":
        reply(db, chat_id, _runner_listing(db))
        db.commit()
        return True
    if op == "add":
        owner_id, owner_label = 0, ""
        users = grants.find_users(db, grants.clean_name(parsed["name"]))
        if len(users) == 1:
            owner_id, owner_label = users[0].id, describe_user(db, users[0])[0]
        raw_name = owner_label.split(" (")[0].split()[-1] if owner_label else parsed["name"]
        #  «thêm máy may-dai-ca» giữ nguyên tên đã có tiền tố; «thêm máy của anh Được» → may-duoc.
        name = runners.slug(raw_name) if runners.slug(raw_name).startswith("may-") else runners.slug("may " + raw_name)
        if runners.by_name(db, name) is not None:
            reply(db, chat_id, f"Đã có máy tên <b>{esc(name)}</b> rồi. Xem «máy nào đang bật».")
            db.commit()
            return True
        who = f", chủ máy <b>{esc(owner_label)}</b>" if owner_label else " (không gắn chủ máy: em không tìm thấy tài khoản ERP tên đó)"
        reply(db, chat_id, f"Thêm máy sửa mã <b>{esc(name)}</b>{who}? Máy mới mặc định KHÔNG được deploy dev. "
              "Nhắn «đúng» để em phát mã máy, «thôi» để bỏ.")
        log_message(db, DIR_OUT, chat_id, 0, json.dumps({"op": "add", "name": name, "owner_user_id": owner_id,
                                                         "note": parsed["name"]}), action=ACT_RUNNER_WAIT)
        db.commit()
        return True
    found = runners.find(db, parsed["name"])
    if not found:
        reply(db, chat_id, f"Không có máy nào khớp «{esc(parsed['name'])}». Xem «máy nào đang bật».")
        db.commit()
        return True
    if len(found) > 1:
        reply(db, chat_id, "Có nhiều máy khớp: " + " · ".join(esc(r.name) for r in found) + ". Nhắn đúng tên máy giúp em.")
        db.commit()
        return True
    rn = found[0]
    if op == "remove":
        reply(db, chat_id, f"Gỡ máy <b>{esc(rn.name)}</b>? Máy đó bị từ chối ngay ở lượt kế, việc đang dính máy sẽ chờ "
              "cho tới khi đại ca giao máy khác. Nhắn «đúng» để gỡ, «thôi» để giữ.")
        log_message(db, DIR_OUT, chat_id, 0, json.dumps({"op": "remove", "runner_id": rn.id}), action=ACT_RUNNER_WAIT)
        db.commit()
        return True
    if op in ("deploy_on", "deploy_off"):
        rn.can_deploy = op == "deploy_on"
        db.commit()
        reply(db, chat_id, f"Máy <b>{esc(rn.name)}</b> {'ĐƯỢC' if rn.can_deploy else 'KHÔNG được'} deploy dev từ giờ.")
        return True
    if op == "assign":
        code_m = _CODE_IN_TEXT.search(parsed["code"])
        task = db.scalar(select(AgentTask).where(AgentTask.code == f"AI-{int(code_m.group(1)):04d}")) if code_m else None
        if task is None:
            reply(db, chat_id, f"Không có việc <b>{esc(parsed['code'].upper())}</b> trong sổ.")
            db.commit()
            return True
        if task.runner_id and task.runner_id != rn.id and runners.running_count(db, task.runner_id):
            old = db.get(AgentRunner, task.runner_id)
            reply(db, chat_id, f"<b>{esc(task.code)}</b> đang chạy dở trên máy <b>{esc(old.name if old else '?')}</b>; "
                  "chờ xong lượt đó rồi giao lại.", task_id=task.id)
            db.commit()
            return True
        moved = bool(task.runner_id and task.runner_id != rn.id)
        task.runner_id = rn.id
        db.commit()
        reply(db, chat_id, f"Từ giờ <b>{esc(task.code)}</b> giao máy <b>{esc(rn.name)}</b>"
              + (" (bản vá dở trên máy cũ không mang theo, máy mới làm lại từ kế hoạch)." if moved else ".")
              + ("" if runners.is_online(rn) else " Máy đang tắt, việc sẽ chờ."), task_id=task.id)
        return True
    return False


def _runner_confirm(db: Session, chat_id: str, row: AgentMessage, pending: AgentMessage, *, yes: bool) -> bool:
    row.action = ACT_COMMAND
    try:
        info = json.loads(pending.body or "{}")
    except ValueError:
        info = {}
    esc = telegram.esc
    if not yes:
        pending.action = ACT_RUNNER_DROPPED
        db.commit()
        reply(db, chat_id, "Dạ, em không đổi gì ở sổ máy.")
        return True
    pending.action = ACT_RUNNER_DONE
    db.commit()
    if info.get("op") == "remove":
        rn = db.get(AgentRunner, int(info.get("runner_id") or 0))
        if rn is None or rn.revoked_at is not None:
            reply(db, chat_id, "Máy đó không còn trong sổ.")
            return True
        runners.revoke(db, rn)
        reply(db, chat_id, f"Đã gỡ máy <b>{esc(rn.name)}</b>.")
        log.info("agent_hub: gỡ máy sửa mã %s bởi chat %s", rn.name, chat_id)
        return True
    try:
        rn, raw = runners.register(db, info.get("name", ""), owner_user_id=int(info.get("owner_user_id") or 0),
                                   note=str(info.get("note") or ""), by_chat=chat_id)
    except ValueError as e:
        reply(db, chat_id, esc(str(e)))
        return True
    reply(db, chat_id,
          f"Đã thêm máy <b>{esc(rn.name)}</b>. Mã máy (hiện MỘT lần, chép xong đại ca XÓA tin này):\n"
          f"<code>AGENT_RUNNER_NAME={esc(rn.name)}</code>\n<code>AGENT_RUNNER_TOKEN={esc(raw)}</code>\n"
          "Dán hai dòng vào <code>.env</code> của runner trên máy đó rồi bật. Máy tự báo «còn sống» mỗi 30 giây; "
          "hỏi «máy nào đang bật» để kiểm. Muốn máy này deploy dev: «cho máy " + esc(rn.name) + " được deploy».")
    log.info("agent_hub: thêm máy sửa mã %s bởi chat %s", rn.name, chat_id)
    return True


def _notify_admin_action(db: Session, chat_id: str, task: AgentTask, action: str, text: str) -> None:
    """Người khác vừa ra lệnh đổi trạng thái việc: một dòng về chat đại ca (sổ đã có tin gốc)."""
    if telegram.is_allowed_chat(chat_id) or action not in grants.NOTIFY_ACTIONS:
        return
    from app.modules.user.model import User

    link = chat_link.get_active_link(db, chat_id)
    label = describe_user(db, db.get(User, link.user_id))[0] if link is not None else f"chat {chat_link.mask_chat(chat_id)}"
    esc = telegram.esc
    reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
          f"<b>{esc(label)}</b> vừa nhắn «{esc(text[:80])}» → {esc(_ACTION_LABELS.get(action, action))} "
          f"<b>{esc(task.code)}</b>.", task_id=task.id)


def _ask_intent_choice(db: Session, chat_id: str, row: AgentMessage) -> None:
    """Không đoán được thì đóng dấu chờ và đưa đại ca hai nút."""
    row.action = ACT_WAIT_CHOICE
    reply(db, chat_id,
          "Em chưa chắc đại ca đang nhờ em làm ngay hay nhờ sửa phần mềm. "
          + ("Nhắn «làm luôn» hoặc «ghi việc»." if settings.AGENT_TG_COMPACT else "Đại ca chọn giúp:"),
          buttons=[("Làm luôn", f"hoi:{row.id}"),
                   ("Ghi thành việc sửa mã", f"viec:{row.id}")])


def _is_follow_up(db: Session, chat_id: str, row: AgentMessage) -> bool:
    """Tin này có phải câu trả lời cho câu bot vừa hỏi không.

    Ba điều kiện, thiếu một là không: tin hội thoại gần nhất của chat là câu TRẢ LỜI
    của Trợ lý AI (dấu `tra_loi`), câu đó có dấu hỏi, và cách tin này chưa quá
    `FOLLOW_UP_WINDOW`. Dấu hỏi là chốt hẹp cố ý: bot trả lời xuôi một câu rồi đại ca
    nhắn *"màn đơn hàng lỗi lọc ngày"* thì đó là việc mới, phải đi phân loại; chỉ khi
    bot đang CHỜ một câu trả lời thì tin kế mới được nối thẳng.

    So thời gian bằng chính cột `created_at` của hai tin (đồng hồ DB), không so với
    đồng hồ Python: container chạy UTC, máy đại ca UTC+7.
    """
    last = db.scalar(
        select(AgentMessage)
        .where(AgentMessage.chat_id == chat_id, AgentMessage.id < row.id,
               AgentMessage.action.in_((ACT_ASKED, ACT_ANSWER)))
        .order_by(AgentMessage.id.desc())
        .limit(1)
    )
    if last is None or last.direction != DIR_OUT or "?" not in last.body:
        return False
    if row.created_at and last.created_at and row.created_at - last.created_at > FOLLOW_UP_WINDOW:
        return False
    return True


def _intent_context(db: Session, chat_id: str, before_id: int) -> str:
    """Lượt hỏi-đáp gần nhất, dạng chữ thường, cho trạm phân loại đọc kèm tin mới."""
    turns = _recent_turns(db, chat_id, before_id)[-INTENT_CONTEXT_TURNS:]
    lines = []
    for t in turns:
        who = "Người dùng" if t["role"] == "user" else "Bot"
        lines.append(f"{who}: {t['content'][:INTENT_CONTEXT_CHARS]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Hỏi thêm về bản vá (GĐ2b phần 1, ai-CR-013)
# ---------------------------------------------------------------------------
#  Mạch riêng, ba dấu: bot mời hỏi (`cho_hoi_va`) -> đại ca hỏi (`hoi_va`) -> Claude Code trả
#  lời (`tra_loi_va`). Tin kế tiếp trong FOLLOW_UP_WINDOW sau bất kỳ dấu nào là hỏi tiếp về
#  cùng bản vá. Cố ý nối cả sau dấu `hoi_va`: runner trả lời mất cả phút, đại ca nhắn bổ sung
#  trong lúc chờ thì đó là phần tiếp của câu hỏi, không phải việc mới. Đổi lại, trong 10 phút
#  sau khi hỏi, muốn giao việc mới thì phải chờ hết cửa sổ hoặc gõ /gom. Câu trả lời nói rõ.
_PATCH_THREAD_ACTIONS = (ACT_WAIT_PATCH_Q, ACT_PATCH_Q, ACT_PATCH_ANSWER)


def _patch_question_target(db: Session, chat_id: str, row: AgentMessage) -> int:
    """Tin này có đang nằm trong mạch hỏi về bản vá không. Trả id việc, hoặc 0."""
    last = db.scalar(
        select(AgentMessage)
        .where(AgentMessage.chat_id == chat_id, AgentMessage.id < row.id,
               AgentMessage.action.not_in(NOISE_ACTIONS))
        .order_by(AgentMessage.id.desc())
        .limit(1)
    )
    if last is None or last.action not in _PATCH_THREAD_ACTIONS or not last.task_id:
        return 0
    if row.created_at and last.created_at and row.created_at - last.created_at > FOLLOW_UP_WINDOW:
        return 0
    return last.task_id


def _ask_patch(db: Session, chat_id: str, row: AgentMessage, text: str, task_id: int) -> None:
    """Đóng dấu câu hỏi, gắn vào việc, giao cho runner (chỗ có worktree + phiên)."""
    row.action = ACT_PATCH_Q
    row.task_id = task_id
    db.commit()
    task = db.get(AgentTask, task_id)
    code = telegram.esc(task.code if task else str(task_id))
    if not settings.AGENT_CODER_ENABLED:
        reply(db, chat_id, f"Bot sửa mã đang TẮT (AGENT_CODER_ENABLED=false) nên không hỏi "
              f"phiên của <b>{code}</b> được.", task_id=task_id)
        return
    try:
        coder.dispatch_question(task_id, row.id)
    except Exception as e:  # noqa: BLE001 - hàng đợi hỏng thì nói, đừng để câu hỏi rơi im
        log.exception("agent_hub: giao câu hỏi về bản vá hỏng")
        reply(db, chat_id, f"Không giao được câu hỏi cho runner: {telegram.esc(str(e)[:300])}. "
              "Nhắn lại sau nhé.", task_id=task_id)


def _invite_patch_question(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    """Nút «Hỏi thêm về bản vá»: mở mạch hỏi, tin chữ kế tiếp của đại ca là câu hỏi."""
    code = telegram.esc(task.code)
    if not coder.session_id_for(db, task):
        telegram.answer_callback(cb_id, "Việc này chưa có phiên sửa mã để hỏi")
        return
    if not settings.AGENT_CODER_ENABLED:
        telegram.answer_callback(cb_id, "Bot sửa mã đang tắt")
        reply(db, chat_id, "Bot sửa mã đang TẮT (AGENT_CODER_ENABLED=false) nên chưa hỏi "
              f"phiên của <b>{code}</b> được.", task_id=task.id)
        return
    telegram.answer_callback(cb_id, "Nhắn câu hỏi ngay bên dưới")
    minutes = int(FOLLOW_UP_WINDOW.total_seconds() // 60)
    reply(db, chat_id,
          f"Đại ca muốn hỏi gì về bản vá <b>{code}</b>? Nhắn câu hỏi ngay bên dưới "
          f"(trong {minutes} phút), em đưa cho đúng phiên Claude Code đã sửa việc này trả lời. "
          "Lượt hỏi chỉ đọc, không sửa gì.",
          task_id=task.id, action=ACT_WAIT_PATCH_Q)


# ---------------------------------------------------------------------------
# Gộp erp-v2 + deploy dev có hỏi trước (GĐ2b·2, ai-CR-014)
# ---------------------------------------------------------------------------
#  Đường đi: thẻ kết quả «Gộp erp-v2 + deploy dev» (mg) -> THẺ HỎI kể rõ ba bước sẽ làm ->
#  «Đồng ý» (mgok) chạy ngay · «Hẹn giờ» (mgat) rồi nhắn giờ · «Thôi» (mgno). Mỗi lượt là một
#  dòng sổ STAGE_DEPLOY tạo NGAY lúc bấm/hẹn: hẹn giờ nằm trong sổ chứ không trong bộ nhớ
#  worker, vòng beat `agent.deploy_due` nhặt tới giờ. Đã lên dev mà đổi ý: «Thu hồi» (rv ->
#  rvok) revert bản gộp + deploy lại.
_DEAD_RUN_AFTER = timedelta(seconds=coder.DEPLOY_TIMEOUT_SEC + 900)
_REL_UNIT_MIN = {"phút": 1, "phut": 1, "p": 1, "tiếng": 60, "tieng": 60, "giờ": 60, "gio": 60, "h": 60}


def parse_schedule_time(text: str, now: datetime) -> datetime | None:
    """Đọc giờ hẹn kiểu đại ca nhắn: `14:30` · `20h` · `20h30` · `8 giờ sáng mai` · `45 phút nữa` ·
    `2 tiếng nữa` · `sau 30 phút`. Không đọc được -> None (bot hỏi lại, không đoán).
    Giờ tuyệt đối đã qua trong hôm nay thì hiểu là ngày mai; «chiều»/«tối» cộng 12 cho giờ < 12."""
    t = text.strip().lower()
    if not t:
        return None
    if t in ("ngay", "bây giờ", "bay gio", "luôn", "luon", "ngay bây giờ", "ngay bay gio"):
        return now
    rel = re.search(r"(\d{1,3})\s*(phút|phut|tiếng|tieng|giờ|gio|h|p)\b", t)
    if rel and re.search(r"(^|\s)(nữa|nua|sau)(\s|$)", t):
        minutes = int(rel.group(1)) * _REL_UNIT_MIN[rel.group(2)]
        if minutes <= 0 or minutes > 7 * 24 * 60:
            return None
        return (now + timedelta(minutes=minutes)).replace(second=0, microsecond=0)
    ab = re.search(r"(?<!\d)(\d{1,2})\s*(?::|h|g|giờ|gio)\s*(\d{1,2})?(?!\d)", t)
    if not ab:
        return None
    hour, minute = int(ab.group(1)), int(ab.group(2) or 0)
    if hour < 12 and re.search(r"chiều|chieu|tối|toi\b", t):
        hour += 12
    if hour > 23 or minute > 59:
        return None
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    words = t.split()
    if "mai" in words:
        target += timedelta(days=1)
    elif target <= now:
        target += timedelta(days=1)
    return target


def _run_phase(run: AgentRun) -> str:
    art = run.artifact if isinstance(run.artifact, dict) else {}
    return str(art.get("phase") or "")


def _scheduled_for(run: AgentRun) -> datetime | None:
    art = run.artifact if isinstance(run.artifact, dict) else {}
    raw = art.get("scheduled_for")
    try:
        return datetime.fromisoformat(raw) if raw else None
    except ValueError:
        return None


def _deploy_blocker(db: Session, task: AgentTask, *, for_revert: bool = False) -> str:
    """Vì sao CHƯA gộp/thu hồi được lúc này; rỗng = được. Một chỗ cho cả nút lẫn giờ hẹn.
    Lượt «đang chạy» quá lâu (worker chết giữa chừng) thì đóng luôn ở đây để không kẹt việc mãi."""
    if not settings.AGENT_DEPLOY_ENABLED:
        return "Gộp + deploy dev đang TẮT (AGENT_DEPLOY_ENABLED=false)."
    if not settings.AGENT_CODER_ENABLED:
        return "Runner đang TẮT (AGENT_CODER_ENABLED=false) nên không có ai gộp."
    if task.status == ST_DEPLOYING:
        return "Đang gộp/deploy dở, chờ thẻ kết quả đã."
    run = coder.pending_deploy_run(db, task)
    if run is not None:
        phase = _run_phase(run)
        if phase == "hen_gio":
            when = _scheduled_for(run)
            return (f"Đã có lịch hẹn lúc {fmt_local(when)}. " if when else "Đã có lịch hẹn. ") + \
                "Bấm «Hủy hẹn» trước nếu muốn đổi."
        if run.started_at and datetime.now() - run.started_at > _DEAD_RUN_AFTER:
            coder._close_run(run, status=RUN_ERROR, error="mất dấu: runner không đóng lượt này")
            db.commit()
        else:
            return "Đang có một lượt gộp/deploy chạy, chờ nó xong đã."
    if for_revert:
        if not coder.merged_sha_for(db, task):
            return "Việc này chưa gộp vào nhánh nền, không có gì để thu hồi."
        return ""
    if task.status == ST_PROD and task.deployed_dev_at:
        return "Đã gộp và lên dev rồi. Đổi ý thì bấm «Thu hồi»."
    if task.status not in (ST_REVIEW, ST_PROD):
        return "Chưa có bản vá đã commit để gộp."
    return ""


def _new_deploy_run(db: Session, task: AgentTask, stage: int, phase: str, **extra) -> AgentRun:
    run = AgentRun(task_id=task.id, stage=stage, provider=coder.PROVIDER, model="git+ssh",
                   status=RUN_RUNNING, started_at=datetime.now(),
                   artifact={"phase": phase, **extra})
    db.add(run)
    db.commit()
    return run


def _confirm_deploy(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    """Nút «Gộp erp-v2 + deploy dev»: KHÔNG gộp gì, chỉ kể rõ ba bước và hỏi. Đây là chỗ thực
    hiện điều đại ca chốt: muốn gộp là phải hỏi, đồng ý mới làm."""
    esc = telegram.esc
    code, base = esc(task.code), esc(settings.AGENT_BASE_BRANCH)
    if blocked := _deploy_blocker(db, task):
        telegram.answer_callback(cb_id, "Chưa gộp được, xem lý do")
        buttons = [("Hủy hẹn", f"mgno:{task.id}")] if "lịch hẹn" in blocked else None
        reply(db, chat_id, f"<b>{code}</b>: {esc(blocked)}", task_id=task.id, buttons=buttons)
        return
    art = coder._code_artifact(db, task)
    files = art.get("files") or []
    gate = art.get("gate") or {}
    services = coder.deploy_services_for([f.get("path", "") for f in files])
    svc = ", ".join(f"<code>{esc(s)}</code>" for s in services) or "không có (chỉ doc/test)"
    merged = coder.merged_sha_for(db, task)
    head = [f"<b>{code}</b> · {esc(task.title)}", ""]
    if merged:
        head += [f"Bản gộp <code>{esc(merged[:10])}</code> ĐÃ ở trên <code>{base}</code>, lượt trước "
                 "deploy dev hỏng. Lần này em chỉ làm lại bước deploy:", ""]
        steps = [f"1. SSH lên VPS: reset về <code>origin/{base}</code>, build lại {svc}.",
                 "2. Chờ health dev trả 200 rồi báo."]
    else:
        head += ["Em sẽ làm ba bước:"]
        steps = [f"1. Gộp <code>{esc(task.branch_name or '')}</code> vào <code>{base}</code> "
                 "(merge --no-ff, không --force) rồi đẩy GitHub.",
                 f"2. SSH lên VPS: reset về <code>origin/{base}</code>, build lại {svc}.",
                 "3. Chờ health dev trả 200 rồi báo."]
    added = sum(int(f.get("added") or 0) for f in files)
    deleted = sum(int(f.get("deleted") or 0) for f in files)
    gate_line = {"pass": "XANH", "fail": "ĐỎ — gộp là gộp cả lỗi vào nhánh nền"}.get(
        gate.get("status"), "không có bài kiểm backend bị đụng")
    tail = ["", f"{len(files)} tệp · +{added}/−{deleted} dòng · Cổng kiểm: <b>{gate_line}</b>", "",
            "Đại ca có muốn em gộp + deploy dev không? «Đồng ý» là chạy ngay; «Hẹn giờ» rồi nhắn "
            "giờ; «Thôi» thì không gì chạy cả."]
    telegram.answer_callback(cb_id, "Đọc thẻ rồi bấm đồng ý")
    reply(db, chat_id, "\n".join(head + steps + tail), task_id=task.id, buttons=[
        ("Đồng ý: gộp + deploy ngay", f"mgok:{task.id}"), ("Hẹn giờ", f"mgat:{task.id}"),
        ("Hỏi thêm về bản vá", f"ask:{task.id}"), ("Thôi, chưa gộp", f"mgno:{task.id}"),
    ])


def _dispatch_deploy(db: Session, chat_id: str, cb_id: str, task: AgentTask, *, deploy: bool = True) -> None:
    """Nút «Đồng ý» / lệnh chữ: ghi dòng sổ rồi giao runner. Đây là lần DUY NHẤT lệnh gộp được phát.
    `deploy=False` = chỉ gộp vào nhánh nền (ai-CR-029); nút bấm cũ ghi «Gộp + deploy dev» nên mặc định True."""
    code = telegram.esc(task.code)
    if blocked := _deploy_blocker(db, task):
        telegram.answer_callback(cb_id, "Chưa gộp được, xem lý do")
        reply(db, chat_id, f"<b>{code}</b>: {telegram.esc(blocked)}", task_id=task.id)
        return
    merged = bool(coder.merged_sha_for(db, task))
    run = _new_deploy_run(db, task, STAGE_DEPLOY, "ngay", approved_by=chat_id, deploy=deploy)
    try:
        coder.dispatch_deploy(task.id, run.id)
        _runner_wait_note(db, task)
    except Exception as e:  # noqa: BLE001 — broker chết thì đóng lượt, nút bấm lại được
        log.exception("agent_hub: giao việc gộp + deploy hỏng")
        coder._close_run(run, status=RUN_ERROR, error=str(e)[:500])
        db.commit()
        reply(db, chat_id, f"<b>{code}</b>: không giao được cho runner: {telegram.esc(str(e)[:300])}",
              task_id=task.id, buttons=[("Gộp erp-v2 + deploy dev", f"mg:{task.id}")])
        return
    telegram.answer_callback(cb_id, "Đang chạy…")
    what = _deploy_what(deploy, merged)
    eta = "thường 5-12 phút" if deploy else "khoảng 1 phút"
    reply(db, chat_id, f"<b>{code}</b>: đang {what}, {eta}. Xong em báo.", task_id=task.id)


def _invite_deploy_time(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    code = telegram.esc(task.code)
    if blocked := _deploy_blocker(db, task):
        telegram.answer_callback(cb_id, "Chưa hẹn được, xem lý do")
        reply(db, chat_id, f"<b>{code}</b>: {telegram.esc(blocked)}", task_id=task.id)
        return
    telegram.answer_callback(cb_id, "Nhắn giờ ngay bên dưới")
    minutes = int(FOLLOW_UP_WINDOW.total_seconds() // 60)
    reply(db, chat_id,
          f"Đại ca muốn em gộp + deploy dev <b>{code}</b> lúc mấy giờ? Nhắn ngay bên dưới (trong "
          f"{minutes} phút), ví dụ: <code>14:30</code> · <code>20h</code> · <code>45 phút nữa</code> · "
          "<code>2 tiếng nữa</code> · <code>8h sáng mai</code>.",
          task_id=task.id, action=ACT_WAIT_DEPLOY_TIME)


def _cancel_deploy(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    """«Thôi, chưa gộp» / «Hủy hẹn»: gỡ lịch hẹn nếu có; lượt đang chạy thì không hủy được nữa."""
    code = telegram.esc(task.code)
    run = coder.pending_deploy_run(db, task)
    if run is not None and _run_phase(run) == "hen_gio":
        coder._close_run(run, status=RUN_ERROR, error="Đại ca hủy hẹn")
        db.commit()
        telegram.answer_callback(cb_id, "Đã hủy hẹn")
        reply(db, chat_id, f"<b>{code}</b>: đã hủy lịch hẹn, không gộp gì. Muốn gộp sau thì bấm lại.",
              task_id=task.id, buttons=[("Gộp erp-v2 + deploy dev", f"mg:{task.id}")])
        return
    if run is not None:
        telegram.answer_callback(cb_id, "Lượt này đang chạy rồi, không hủy được nữa")
        return
    telegram.answer_callback(cb_id, "Chưa gộp gì")
    reply(db, chat_id, f"<b>{code}</b>: không gộp. Nhánh nền không đổi. Muốn gộp sau thì bấm lại.",
          task_id=task.id, buttons=[("Gộp erp-v2 + deploy dev", f"mg:{task.id}")])


def _deploy_time_target(db: Session, chat_id: str, row: AgentMessage) -> int:
    """Tin này có phải giờ hẹn trả lời lời mời «Hẹn giờ» không. Trả id việc, hoặc 0."""
    last = db.scalar(
        select(AgentMessage)
        .where(AgentMessage.chat_id == chat_id, AgentMessage.id < row.id,
               AgentMessage.action.not_in(NOISE_ACTIONS))
        .order_by(AgentMessage.id.desc())
        .limit(1)
    )
    if last is None or last.action != ACT_WAIT_DEPLOY_TIME or not last.task_id:
        return 0
    if row.created_at and last.created_at and row.created_at - last.created_at > FOLLOW_UP_WINDOW:
        return 0
    return last.task_id


def _schedule_deploy(db: Session, chat_id: str, row: AgentMessage, text: str, task_id: int) -> None:
    """Giờ hẹn của đại ca -> dòng sổ STAGE_DEPLOY pha `hen_gio`; vòng beat nhặt khi tới giờ."""
    row.action = ACT_DEPLOY_TIME
    row.task_id = task_id
    db.commit()
    task = db.get(AgentTask, task_id)
    code = telegram.esc(task.code if task else str(task_id))
    if task is None or task.status in CLOSED_STATUSES:
        reply(db, chat_id, f"<b>{code}</b> đã đóng rồi, không hẹn nữa.", task_id=task_id)
        return
    if blocked := _deploy_blocker(db, task):
        reply(db, chat_id, f"<b>{code}</b>: {telegram.esc(blocked)}", task_id=task.id)
        return
    #  Đại ca nhắn giờ VIỆT NAM; sổ và vòng beat chạy giờ UTC của container (ai-CR-020).
    when = parse_schedule_time(text, now_local())
    if when is None:
        reply(db, chat_id,
              f"Em chưa hiểu giờ «{telegram.esc(text[:60])}». Nhắn lại dạng <code>14:30</code> · "
              "<code>20h</code> · <code>45 phút nữa</code> · <code>2 tiếng nữa</code> · "
              "<code>8h sáng mai</code>.", task_id=task.id, action=ACT_WAIT_DEPLOY_TIME)
        return
    _new_deploy_run(db, task, STAGE_DEPLOY, "hen_gio",
                    scheduled_for=to_utc(when).isoformat(timespec="minutes"), approved_by=chat_id)
    reply(db, chat_id,
          f"Đã hẹn <b>{when:%H:%M %d/%m}</b>: gộp <b>{code}</b> vào "
          f"<code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code> + deploy dev. Tới giờ em tự "
          "chạy và gửi thẻ; đổi ý thì bấm «Hủy hẹn».",
          task_id=task.id, buttons=[("Hủy hẹn", f"mgno:{task.id}")])


def _confirm_revert(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    esc = telegram.esc
    code, base = esc(task.code), esc(settings.AGENT_BASE_BRANCH)
    if blocked := _deploy_blocker(db, task, for_revert=True):
        telegram.answer_callback(cb_id, "Chưa thu hồi được, xem lý do")
        reply(db, chat_id, f"<b>{code}</b>: {esc(blocked)}", task_id=task.id)
        return
    sha = coder.merged_sha_for(db, task)
    telegram.answer_callback(cb_id, "Đọc thẻ rồi bấm đồng ý")
    reply(db, chat_id, "\n".join([
        f"<b>{code}</b> · {esc(task.title)}", "",
        "Thu hồi nghĩa là:",
        f"1. <code>git revert -m 1 {esc(sha[:10])}</code> trên <code>{base}</code> (thêm một bản đảo "
        "ngược, KHÔNG xóa lịch sử) rồi đẩy GitHub.",
        f"2. SSH lên VPS: reset về <code>origin/{base}</code>, build lại đúng service.",
        "3. Việc về «Đang hỏi lại» — nhắn cần sửa gì rồi /gom để bot làm lại từ đầu.", "",
        "Đại ca có chắc muốn thu hồi không?",
    ]), task_id=task.id, buttons=[("Đồng ý thu hồi", f"rvok:{task.id}"),
                                 ("Thôi, giữ nguyên", f"rvno:{task.id}")])


def _dispatch_revert(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    code = telegram.esc(task.code)
    if blocked := _deploy_blocker(db, task, for_revert=True):
        telegram.answer_callback(cb_id, "Chưa thu hồi được, xem lý do")
        reply(db, chat_id, f"<b>{code}</b>: {telegram.esc(blocked)}", task_id=task.id)
        return
    run = _new_deploy_run(db, task, STAGE_REVERT, "ngay", approved_by=chat_id)
    try:
        coder.dispatch_revert(task.id, run.id)
        _runner_wait_note(db, task)
    except Exception as e:  # noqa: BLE001
        log.exception("agent_hub: giao việc thu hồi hỏng")
        coder._close_run(run, status=RUN_ERROR, error=str(e)[:500])
        db.commit()
        reply(db, chat_id, f"<b>{code}</b>: không giao được cho runner: {telegram.esc(str(e)[:300])}",
              task_id=task.id, buttons=[("Thu hồi khỏi erp-v2 + dev", f"rv:{task.id}")])
        return
    telegram.answer_callback(cb_id, "Đang thu hồi…")
    reply(db, chat_id, f"<b>{code}</b>: đang revert bản gộp trên "
          f"<code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code> và deploy lại dev, chờ chút.",
          task_id=task.id)


def dispatch_due_deploys(db: Session, now: datetime | None = None) -> int:
    """Vòng beat mỗi phút: lịch hẹn tới giờ -> giao runner. Trả số lượt đã giao."""
    now = now or datetime.now()
    runs = db.scalars(
        select(AgentRun).where(AgentRun.stage == STAGE_DEPLOY, AgentRun.status == RUN_RUNNING)
        .order_by(AgentRun.id)
    ).all()
    count = 0
    for run in runs:
        when = _scheduled_for(run)
        if _run_phase(run) != "hen_gio" or when is None or when > now:
            continue
        task = db.get(AgentTask, run.task_id)
        if task is None or task.status not in (ST_REVIEW, ST_PROD) or \
                (task.status == ST_PROD and task.deployed_dev_at):
            coder._close_run(run, status=RUN_ERROR, error="tới giờ hẹn nhưng việc không còn chờ gộp")
            db.commit()
            continue
        art = dict(run.artifact) if isinstance(run.artifact, dict) else {}
        run.artifact = {**art, "phase": "dispatched", "dispatched_at": now.isoformat(timespec="minutes")}
        db.commit()
        coder.dispatch_deploy(task.id, run.id)
        _runner_wait_note(db, task)
        what = _deploy_what(art.get("deploy", True), bool(coder.merged_sha_for(db, task)))
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
              f"Tới giờ hẹn {fmt_local(when, '%H:%M')}: em bắt đầu {what} <b>{telegram.esc(task.code)}</b>.",
              task_id=task.id)
        count += 1
    return count


# ---------------------------------------------------------------------------
# Trả lời câu hỏi lại + sổ quyết định (ai-CR-015)
# ---------------------------------------------------------------------------
#  Cửa sổ dài hơn FOLLOW_UP_WINDOW: câu hỏi của trạm kế hoạch cần nghĩ, không phải câu đáp nhanh.
PLAN_ANSWER_WINDOW = timedelta(minutes=30)
_FIX_QUESTION = "Đại ca muốn sửa kế hoạch thế nào?"


def _invite_plan_answer(db: Session, chat_id: str, task: AgentTask, *, again: bool = False) -> None:
    minutes = int(PLAN_ANSWER_WINDOW.total_seconds() // 60)
    code = telegram.esc(task.code)
    if again or task.questions:
        text = (f"Đại ca nhắn trả lời cho <b>{code}</b> ngay bên dưới (trong {minutes} phút), "
                "em gắn vào việc này và lập lại kế hoạch luôn.")
    else:
        text = (f"<b>{code}</b>: đại ca nhắn cần sửa kế hoạch thế nào ngay bên dưới (trong "
                f"{minutes} phút), em lập lại kế hoạch luôn, không cần /gom.")
    reply(db, chat_id, text, task_id=task.id, action=ACT_WAIT_PLAN_ANSWER)


def _plan_answer_target(db: Session, chat_id: str, row: AgentMessage) -> int:
    """Tin này có phải câu trả lời cho lần hỏi lại gần nhất của trạm kế hoạch không. Trả id việc, hoặc 0.

    Ba chốt: dấu chờ gần nhất còn trong cửa sổ; từ dấu đó tới giờ đại ca CHƯA nhắn hay bấm gì
    khác (có tin/bấm nút xen giữa là đã sang chuyện khác); và việc vẫn đang «Đang hỏi lại».
    """
    wait = db.scalar(
        select(AgentMessage)
        .where(AgentMessage.chat_id == chat_id, AgentMessage.id < row.id,
               AgentMessage.action == ACT_WAIT_PLAN_ANSWER)
        .order_by(AgentMessage.id.desc())
        .limit(1)
    )
    if wait is None or not wait.task_id:
        return 0
    if row.created_at and wait.created_at and row.created_at - wait.created_at > PLAN_ANSWER_WINDOW:
        return 0
    between = db.scalar(
        select(func.count(AgentMessage.id))
        .where(AgentMessage.chat_id == chat_id, AgentMessage.direction == DIR_IN,
               AgentMessage.id > wait.id, AgentMessage.id < row.id,
               AgentMessage.action.not_in(NOISE_ACTIONS))
    ) or 0
    if between:
        return 0
    task = db.get(AgentTask, wait.task_id)
    if task is None or task.status != ST_NEEDS_INPUT:
        return 0
    return task.id


def _answer_plan(db: Session, chat_id: str, row: AgentMessage, text: str, task_id: int) -> None:
    """Gắn câu trả lời vào việc (tin + mô tả), lập lại kế hoạch, rồi đề xuất ghi sổ nếu dùng lại được."""
    task = db.get(AgentTask, task_id)
    row.action = ACT_PLAN_ANSWER
    row.task_id = task_id
    asked = [str(q) for q in (task.questions or []) if str(q).strip()] or [_FIX_QUESTION]
    db.add(AgentTaskItem(task_id=task.id, source=SRC_TELEGRAM, ref_id=row.id,
                         merged_by=MERGED_BY_BOT))
    #  Câu rà soát nêu coi như đã trả lời: lập lại kế hoạch không được hỏi lại chúng (AI-0007 bị
    #  hỏi lại đúng hai câu đại ca vừa đáp «oke theo ý của em» — ai-CR-022).
    scan = coder.latest_scan_run(db, task)
    if scan is not None and isinstance(scan.artifact, dict):
        scan.artifact = {**scan.artifact, "answered": True}
    task.summary = (task.summary or "").rstrip() + (
        f"\n\n--- Bổ sung {now_local():%d/%m %H:%M} ---\n"
        + "\n".join(f"Bot hỏi: {q}" for q in asked)
        + f"\nĐại ca trả lời: {text}")
    task.questions = []
    db.commit()
    reply(db, chat_id, f"Đã gắn câu trả lời vào <b>{telegram.esc(task.code)}</b>, em lập lại kế hoạch.",
          task_id=task.id)
    plan_task(db, task)
    try:
        propose_rule(db, chat_id, task, asked, text)
    except Exception:  # noqa: BLE001 — đề xuất ghi sổ là phần phụ, hỏng không được làm hỏng việc
        log.exception("agent_hub: nháp mục sổ quyết định hỏng")


def _pending_rule_run(db: Session, task: AgentTask) -> AgentRun | None:
    run = db.scalar(
        select(AgentRun).where(AgentRun.task_id == task.id, AgentRun.stage == STAGE_RULE)
        .order_by(AgentRun.id.desc()).limit(1)
    )
    art = run.artifact if run is not None and isinstance(run.artifact, dict) else {}
    return run if art.get("state") == "cho_duyet" else None


def propose_rule(db: Session, chat_id: str, task: AgentTask, asked: list[str], answer: str) -> None:
    """Thẻ «Lần sau gặp tương tự em tự làm vậy nhé?». Luật 1 của sổ: bot CHỈ đề xuất."""
    esc = telegram.esc
    topic = playbook.protected_topic("\n".join([task.title or "", *asked, answer]))
    if int(task.risk_level or 0) >= RISK_HIGH or topic:
        #  Im lặng (ai-CR-021): việc công nợ thì câu trả lời nào cũng rơi vào đây, nhắn mỗi lần một
        #  câu «dính tiền nên em vẫn hỏi» chỉ làm khung chat dài thêm.
        log.info("agent_hub: %s chạm chủ đề luôn hỏi (%s), không đề xuất ghi sổ", task.code,
                 topic or "rủi ro cao")
        return
    run = start_run(db, task.id, STAGE_RULE)
    try:
        draft, result = manager.run_rule_draft(task.title, asked, answer, playbook.titles())
    except Exception as e:  # noqa: BLE001
        finish_run(db, run, error=str(e))
        db.commit()
        log.warning("agent_hub: nháp mục sổ hỏng (%s)", e)
        return
    finish_run(db, run, result=result)
    entry = {k: draft[k] for k in ("title", "situation", "action", "not_when")}
    topic = playbook.protected_topic(" ".join(entry.values()))
    if not draft["generalizable"] or topic:
        run.artifact = {"state": "khong_ap", "entry": entry, "topic": topic}
        db.commit()
        return
    run.artifact = {"state": "cho_duyet", "entry": entry, "questions": asked, "answer": answer[:1000]}
    db.commit()
    reply(db, chat_id, "\n".join([
        f"<b>{esc(task.code)}</b>: lần sau gặp tình huống tương tự em tự làm vậy, khỏi hỏi nhé?", "",
        f"<b>{esc(entry['title'])}</b>",
        f"Tình huống: {esc(entry['situation'])}",
        f"Em sẽ làm: {esc(entry['action'])}",
        f"Không áp khi: {esc(entry['not_when'] or 'chưa ghi')}", "",
        "Việc dính tiền, công nợ, phân quyền, cấu trúc DB, prod hay gộp mã thì em vẫn luôn hỏi.",
        *(["Nhắn «ghi sổ» để em ghi, «không ghi» thì thôi."] if settings.AGENT_TG_COMPACT else []),
    ]), task_id=task.id, buttons=[("Ghi vào sổ", f"qdok:{task.id}"),
                                  ("Không, lần nào cũng hỏi", f"qdno:{task.id}")])


def _resolve_rule(db: Session, chat_id: str, cb_id: str, action: str, task: AgentTask) -> None:
    run = _pending_rule_run(db, task)
    if run is None:
        telegram.answer_callback(cb_id, "Đề xuất này đã xử rồi")
        return
    art = dict(run.artifact)
    if action == "qdno":
        run.artifact = {**art, "state": "bo"}
        db.commit()
        telegram.answer_callback(cb_id, "Được, lần sau em vẫn hỏi")
        return
    source = f"đại ca bấm «Ghi vào sổ» trên Telegram {now_local():%d/%m/%Y}, từ việc {task.code}"
    try:
        qd_id = playbook.append_entry(art.get("entry") or {}, source=source)
    except playbook.PlaybookError as e:
        run.artifact = {**art, "state": "loi", "error": str(e)[:500]}
        db.commit()
        telegram.answer_callback(cb_id, "Chưa ghi được")
        reply(db, chat_id, f"Chưa ghi được vào sổ: {telegram.esc(str(e))}", task_id=task.id)
        return
    run.artifact = {**art, "state": "da_ghi", "qd_id": qd_id}
    db.commit()
    telegram.answer_callback(cb_id, f"Đã ghi {qd_id}")
    title = telegram.esc((art.get("entry") or {}).get("title") or "")
    reply(db, chat_id,
          f"Đã ghi <b>{qd_id} · {title}</b> vào sổ quyết định. Từ lần sau gặp tình huống này em "
          f"tự làm và ghi rõ «Theo {qd_id}». Muốn sửa hay gỡ thì sửa tay tệp "
          "<code>doc/agent-hub/03-so-quyet-dinh.md</code>.", task_id=task.id)


def handle_callback(db: Session, cb: dict) -> None:
    """Đại ca bấm một nút. `callback_data` dạng `<hành động>:<id task>`."""
    chat_id = str(((cb.get("message") or {}).get("chat") or {}).get("id") or "")
    with user_keys.for_chat(db, chat_id):
        _handle_callback(db, cb, chat_id)


def _handle_callback(db: Session, cb: dict, chat_id: str) -> None:
    data = str(cb.get("data") or "")
    cb_id = str(cb.get("id") or "")
    if not telegram.is_allowed_chat(chat_id):
        return

    action, _, raw_id = data.partition(":")

    #  Hai nút của nhánh mập mờ trỏ vào một TIN NHẮN, không phải một task — phải rẽ
    #  trước khi đi tra sổ việc, không thì nó tra id tin trong bảng task và báo
    #  "không tìm thấy việc này".
    if action in ("hoi", "viec"):
        telegram.clear_buttons(chat_id, int((cb.get("message") or {}).get("message_id") or 0))
        _resolve_intent(db, chat_id, cb_id, action, int(raw_id) if raw_id.isdigit() else 0)
        return
    #  Hai nút của thẻ đề xuất sửa phiếu (ai-CR-009) cũng trỏ vào một TIN NHẮN (thẻ đó).
    if action in ("sua", "khong_sua"):
        telegram.clear_buttons(chat_id, int((cb.get("message") or {}).get("message_id") or 0))
        _resolve_proposal(db, chat_id, cb_id, action, int(raw_id) if raw_id.isdigit() else 0)
        return

    task = db.get(AgentTask, int(raw_id)) if raw_id.isdigit() else None
    if task is None:
        telegram.answer_callback(cb_id, "Không tìm thấy việc này trong sổ")
        return

    if action == "ask":
        #  KHÔNG gỡ nút của thẻ kết quả: «Mở PR» / «Bỏ việc này» còn phải dùng sau khi hỏi xong,
        #  và bấm hỏi hai lần cũng chỉ là hai lời mời, không tốn gì.
        log_message(db, DIR_IN, chat_id, 0, data, action=action, task_id=task.id)
        if task.status in CLOSED_STATUSES:
            telegram.answer_callback(cb_id, "Việc này đã đóng rồi")
            return
        _invite_patch_question(db, chat_id, cb_id, task)
        return
    if action == "ans":
        #  Mở lại cửa trả lời khi đại ca trả lời trễ quá cửa sổ, hoặc sau khi đã nhắn chuyện khác.
        #  Không gỡ nút: «Bỏ việc này» trên cùng thẻ còn dùng.
        log_message(db, DIR_IN, chat_id, 0, data, action=action, task_id=task.id)
        if task.status != ST_NEEDS_INPUT:
            telegram.answer_callback(cb_id, "Việc này không còn chờ trả lời")
            return
        telegram.answer_callback(cb_id, "Nhắn trả lời ngay bên dưới")
        _invite_plan_answer(db, chat_id, task, again=True)
        return
    if action in ("mg", "rv"):
        #  Hai nút MỞ THẺ HỎI của ai-CR-014, cũng không gỡ nút thẻ cũ: thẻ hỏi có nút «Thôi»,
        #  thôi xong đại ca còn cần «Đẩy GitHub» / «Hỏi thêm» trên thẻ kết quả; mở thẻ hỏi hai
        #  lần chẳng chạy gì. Gộp thật chỉ xảy ra ở `mgok`/`rvok` — có gỡ nút.
        log_message(db, DIR_IN, chat_id, 0, data, action=action, task_id=task.id)
        if task.status in CLOSED_STATUSES:
            telegram.answer_callback(cb_id, "Việc này đã đóng rồi")
            return
        if action == "mg":
            _confirm_deploy(db, chat_id, cb_id, task)
        else:
            _confirm_revert(db, chat_id, cb_id, task)
        return

    #  Gỡ nút NGAY, trước khi làm gì — đây là chốt chống bấm hai lần, mà lượt PLAN thì
    #  mất vài giây và đại ca rất dễ bấm lại lần nữa trong lúc chờ.
    telegram.clear_buttons(chat_id, int((cb.get("message") or {}).get("message_id") or 0))
    log_message(db, DIR_IN, chat_id, 0, data, action=action, task_id=task.id)

    #  Duyệt mục sổ không phụ thuộc việc còn mở hay không: luật là của đại ca, không của việc.
    if action in ("qdok", "qdno"):
        _resolve_rule(db, chat_id, cb_id, action, task)
        return

    if task.status in CLOSED_STATUSES:
        telegram.answer_callback(cb_id, "Việc này đã đóng rồi")
        return

    if action == "plan":
        telegram.answer_callback(cb_id, "Đang lập kế hoạch…")
        plan_task(db, task)
    elif action == "ok":
        approve_task(db, chat_id, cb_id, task)
    elif action == "fix":
        task.status = ST_NEEDS_INPUT
        task.questions = []
        telegram.answer_callback(cb_id, "Chờ đại ca nói rõ thêm")
        _invite_plan_answer(db, chat_id, task)
    elif action == "no":
        cancel_task(db, chat_id, cb_id, task)
    elif action == "fixg":
        start_fix_gate(db, chat_id, cb_id, task)
    elif action == "cont":
        start_continue(db, chat_id, cb_id, task)
    elif action == "pr":
        _dispatch_publish(db, chat_id, cb_id, task)
    elif action == "mgok":
        _dispatch_deploy(db, chat_id, cb_id, task)
    elif action == "mgat":
        _invite_deploy_time(db, chat_id, cb_id, task)
    elif action == "mgno":
        _cancel_deploy(db, chat_id, cb_id, task)
    elif action == "rvok":
        _dispatch_revert(db, chat_id, cb_id, task)
    elif action == "rvno":
        telegram.answer_callback(cb_id, "Giữ nguyên, không thu hồi")
    elif action == "done":
        close_done(db, chat_id, cb_id, task)
    else:
        telegram.answer_callback(cb_id, "Không hiểu nút này")


# ---------------------------------------------------------------------------
# Thao tác trên một việc — dùng chung cho NÚT (thẻ cũ) và LỆNH GÕ BẰNG CHỮ (ai-CR-027)
# ---------------------------------------------------------------------------
def approve_task(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    task.approved_by_chat = chat_id
    task.approved_at = datetime.now()
    telegram.answer_callback(cb_id, "Đã duyệt")
    _dispatch_coder(db, chat_id, task)


def cancel_task(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    task.status = ST_CANCELLED
    task.closed_at = datetime.now()
    task.note = "Đại ca bỏ từ Telegram"
    telegram.answer_callback(cb_id, "Đã bỏ")
    #  Chỉ có toast thì khung chat không còn dấu vết gì (đại ca hỏi 23/09 về AI-0006).
    reply(db, chat_id, f"Đã bỏ <b>{telegram.esc(task.code)}</b> · {telegram.esc(task.title)}. "
          f"Lịch sử vẫn còn trong sổ: /xem {telegram.esc(task.code)}", task_id=task.id)
    report_to_tickets(db, task, done=False)
    _schedule_cleanup(db, task)


def _schedule_cleanup(db: Session, task: AgentTask) -> None:
    """Việc vừa đóng: giao runner dọn worktree + nhánh `bot/*` (ai-CR-033). Hỏng thì thôi."""
    if not settings.AGENT_CODER_ENABLED or not (task.branch_name or "").startswith("bot/"):
        return
    db.commit()
    try:
        coder.dispatch_cleanup(task.id)
    except Exception:  # noqa: BLE001 — broker chết thì nhánh còn đó, không hỏng việc
        log.exception("agent_hub: giao dọn nhánh hỏng")


def _red_gate(db: Session, task: AgentTask) -> bool:
    last = coder.latest_code_run(db, task)
    art = (last.artifact if last is not None and isinstance(last.artifact, dict) else {}) or {}
    return task.status == ST_REVIEW and (art.get("gate") or {}).get("status") == "fail" \
        and not coder.merged_sha_for(db, task)


def start_fix_gate(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    """«Sửa cho xanh» (ai-CR-026): cổng kiểm đỏ -> bot sửa tiếp đúng phiên, chạy lại cổng."""
    if not _red_gate(db, task):
        telegram.answer_callback(cb_id, "Việc này không còn ở trạng thái cổng kiểm đỏ")
        if not cb_id:
            reply(db, chat_id, f"<b>{telegram.esc(task.code)}</b> không ở trạng thái cổng kiểm đỏ.",
                  task_id=task.id)
        return
    task.status = ST_CODE
    db.commit()
    coder.dispatch_fix_gate(task.id)
    _runner_wait_note(db, task)
    telegram.answer_callback(cb_id, "Em sửa cho xanh")
    reply(db, chat_id, f"Em sửa <b>{telegram.esc(task.code)}</b> cho xanh trong đúng phiên cũ "
          f"(tối đa {coder.FIX_GATE_MAX_TURNS} lượt), xong chạy lại cổng kiểm và gửi thẻ.",
          task_id=task.id)


def start_continue(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    """«Làm tiếp» sau khi hết lượt (ai-CR-023): nối đúng phiên, đúng worktree đang dở."""
    if task.status != ST_NEEDS_INPUT or not coder.resumable_session(db, task):
        telegram.answer_callback(cb_id, "Việc này không còn phiên dở để làm tiếp")
        if not cb_id:
            reply(db, chat_id, f"<b>{telegram.esc(task.code)}</b> không có phiên dở nào để làm tiếp.",
                  task_id=task.id)
        return
    task.status = ST_CODE
    db.commit()
    coder.dispatch_continue(task.id)
    _runner_wait_note(db, task)
    telegram.answer_callback(cb_id, "Em làm tiếp")
    reply(db, chat_id, f"Em làm tiếp <b>{telegram.esc(task.code)}</b> đúng phiên cũ (thêm tối đa "
          f"{coder.CONTINUE_MAX_TURNS} lượt). Xong em gửi thẻ kết quả.", task_id=task.id)


def close_done(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    #  Đại ca thử trên dev thấy ổn. Prod đang tạm dừng deploy (chốt 19/09/2026) nên «xong»
    #  ở đây là xong việc của bot; lên prod là chuyện của người, ghi ở sổ khác.
    task.status = ST_DONE
    task.closed_at = datetime.now()
    task.note = (task.note + "\n" if task.note else "") + "Đại ca xác nhận xong trên dev (Telegram)"
    telegram.answer_callback(cb_id, "Đã đóng việc")
    reply(db, chat_id, f"<b>{telegram.esc(task.code)}</b>: đã đóng. Bản gộp ở trên "
          f"<code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code>, lên prod là đợt riêng.",
          task_id=task.id)
    report_to_tickets(db, task, done=True)
    _schedule_cleanup(db, task)


def _dispatch_publish(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    """Nút «Gửi link PR để anh tự merge» (ai-CR-012): giao cho runner đẩy nhánh đã commit của việc."""
    code = telegram.esc(task.code)
    if task.status != ST_REVIEW:
        telegram.answer_callback(cb_id, "Việc này chưa có bản vá để đẩy")
        return
    if task.pr_url:
        telegram.answer_callback(cb_id, "Đã có PR rồi")
        reply(db, chat_id, f"<b>{code}</b> đã có PR: {telegram.esc(task.pr_url)}", task_id=task.id,
              buttons=[("Mở PR trên GitHub", task.pr_url)])
        return
    if not settings.AGENT_CODER_ENABLED:
        telegram.answer_callback(cb_id, "Bot sửa mã đang tắt")
        reply(db, chat_id, f"<b>{code}</b>: runner đang TẮT (AGENT_CODER_ENABLED=false), "
              "không đẩy được.", task_id=task.id)
        return
    try:
        coder.dispatch_publish(task.id)
        _runner_wait_note(db, task)
    except Exception as e:  # noqa: BLE001 — broker chết thì nói ra, nút vẫn bấm lại được
        log.exception("agent_hub: giao việc đẩy GitHub hỏng")
        reply(db, chat_id, f"<b>{code}</b>: không giao được cho runner: {telegram.esc(str(e)[:300])}",
              task_id=task.id, buttons=[("Đẩy GitHub lại", f"pr:{task.id}")])
        return
    telegram.answer_callback(cb_id, "Đang đẩy lên GitHub…")
    reply(db, chat_id, f"<b>{code}</b>: đang đẩy nhánh lên GitHub và mở PR vào "
          f"<code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code>, chờ chút.", task_id=task.id)


def _dispatch_coder(db: Session, chat_id: str, task: AgentTask) -> None:
    """Sau khi Duyệt: giao bậc 2 sửa mã, hoặc NÓI RA vì sao không giao.

    Im lặng ở đây là lỗi nặng nhất của cả luồng — đại ca ngồi chờ một lượt sửa mã không
    bao giờ tới. Nên mọi nhánh đều kết thúc bằng một câu trả lời.
    """
    code = telegram.esc(task.code)
    if not settings.AGENT_CODER_ENABLED:
        reply(db, chat_id,
              f"Đã duyệt <b>{code}</b> và ghi vào sổ.\n"
              "Bot sửa mã đang TẮT (AGENT_CODER_ENABLED=false) — phần viết mã vẫn là việc tay.",
              task_id=task.id)
        return
    blocked = coder.approve_gate(task)
    if blocked:
        task.status = ST_NEEDS_INPUT
        reply(db, chat_id, f"Đã duyệt <b>{code}</b> nhưng chưa giao được: {telegram.esc(blocked)}.",
              task_id=task.id)
        return
    task.status = ST_CODE
    db.commit()
    try:
        coder.dispatch(task.id)
        _runner_wait_note(db, task)
    except Exception as e:  # noqa: BLE001 — broker chết thì trả việc về PLAN, không treo ở CODE
        log.exception("agent_hub: giao việc cho runner hỏng")
        task.status = ST_PLAN
        reply(db, chat_id,
              f"Đã duyệt <b>{code}</b> nhưng không giao được cho runner: "
              f"{telegram.esc(str(e)[:300])}. Việc vẫn ở trạm kế hoạch, bấm /gom để thử lại.",
              task_id=task.id)
        return
    reply(db, chat_id,
          f"Đã duyệt <b>{code}</b>, giao bot sửa mã (tối đa "
          f"{settings.AGENT_RUN_TIMEOUT_SEC // 60} phút). Xong em gửi thẻ kết quả kèm tệp .diff.",
          task_id=task.id)


# ---------------------------------------------------------------------------
# Nhánh /hoi — mượn nguyên Trợ lý AI của ERP
# ---------------------------------------------------------------------------
def _resolve_intent(db: Session, chat_id: str, cb_id: str, action: str, msg_id: int) -> None:
    """Đại ca tự chốt giúp một tin mập mờ: trả lời luôn, hay ghi thành việc.

    Nhánh "viec" chỉ cần XÓA dấu chờ — tin trở lại INBOX với `action` rỗng và vòng gom
    nhặt nó ở lượt sau, không phải dựng task tại chỗ.
    """
    row = db.get(AgentMessage, msg_id) if msg_id else None
    if row is None:
        telegram.answer_callback(cb_id, "Không tìm thấy tin này trong sổ")
        return
    if row.action != ACT_WAIT_CHOICE:
        telegram.answer_callback(cb_id, "Tin này đã xử rồi")
        return

    log_message(db, DIR_IN, chat_id, 0, f"{action}:{msg_id}", action=ACT_COMMAND)
    if action == "hoi":
        row.action = ACT_ASKED
        telegram.answer_callback(cb_id, f"{BOT_NAME} đang nghĩ…")
        answer_question(db, chat_id, row.body, before_id=row.id)
    else:
        row.action = ""
        telegram.answer_callback(cb_id, "Đã xếp vào hàng chờ gom")
        reply(db, chat_id, "Rồi, em nhận việc này, anh chờ em xíu. Gom xong em đọc mã, kiểm tra và "
              "phản hồi.", action=ACT_ACK)


#  Mạch hội thoại đưa cho Trợ lý AI: tối đa bấy nhiêu lượt hỏi-đáp, chỉ lấy tin trong
#  khoảng này tính từ tin gần nhất, và tổng chữ không quá trần. Web giữ cả cuộc trò
#  chuyện trong một hội thoại; Telegram không có khái niệm đó nên lấy "gần đây" làm ranh.
HISTORY_TURNS = 8
HISTORY_WINDOW = timedelta(hours=2)
HISTORY_MAX_CHARS = 6000


def _recent_turns(db: Session, chat_id: str, before_id: int) -> list[dict]:
    """Các lượt hỏi-đáp gần đây của chat này, dạng `[{role, content}]` cho `ask()`.

    Chỉ lấy tin HỎI (`hoi`) và tin TRẢ LỜI (`tra_loi`) — lệnh, nút bấm, thẻ việc không
    phải hội thoại. Ranh thời gian so bằng chính cột `created_at` của các tin (đồng hồ
    DB), không so với đồng hồ Python: container chạy UTC, máy đại ca UTC+7.
    """
    q = (
        select(AgentMessage)
        .where(AgentMessage.chat_id == chat_id,
               AgentMessage.action.in_((ACT_ASKED, ACT_ANSWER)))
        .order_by(AgentMessage.id.desc())
        .limit(HISTORY_TURNS * 2)
    )
    if before_id:
        q = q.where(AgentMessage.id < before_id)
    rows = list(db.scalars(q))
    if not rows:
        return []
    newest = max((r.created_at for r in rows if r.created_at), default=None)
    turns: list[dict] = []
    total = 0
    for r in rows:  # mới -> cũ, dừng ở tin quá cũ hoặc quá trần chữ
        if newest and r.created_at and newest - r.created_at > HISTORY_WINDOW:
            break
        total += len(r.body)
        if total > HISTORY_MAX_CHARS:
            break
        role = "user" if r.direction == DIR_IN else "assistant"
        turns.append({"role": role, "content": r.body})
    turns.reverse()
    return turns


def answer_question(db: Session, chat_id: str, question: str, *, before_id: int = 0) -> None:
    """Chuyển câu hỏi cho Trợ lý AI và nhắn lại câu trả lời.

    `before_id` = id tin đang hỏi, để mạch hội thoại lấy các tin TRƯỚC nó (không thì
    câu hỏi hiện tại đi vào history rồi lại đi vào message, model thấy hỏi hai lần).

    ⚠️ Trợ lý AI lọc dữ liệu theo NGƯỜI ĐĂNG NHẬP (`apply_scope`), mà Telegram thì
    không đăng nhập. Nên nó chạy dưới đúng một tài khoản ERP khai cứng ở
    `AGENT_ASSISTANT_USER`. Chưa khai thì KHÔNG chạy — chạy mà không có người dùng là
    chạy không phạm vi, tức mở sổ sách cả công ty cho bất kỳ ai tìm ra tên bot.
    """
    if not question:
        reply(db, chat_id, "Cú pháp: <b>/hoi</b> rồi tới câu hỏi.")
        return

    from app.modules.assistant import service as assistant_service

    user = _assistant_user(db, chat_id)
    if user is None:
        reply(db, chat_id, _NO_ASSISTANT_USER if telegram.is_allowed_chat(chat_id) else
              "Tài khoản ERP của chat này không còn hoạt động. " + _LINK_HELP)
        return
    if not user_keys.active_key():
        reply(db, chat_id, user_keys.NO_KEY_HELP)
        return

    history = _recent_turns(db, chat_id, before_id)
    #  Chốt dấu `hoi` trên tin trước khi giao cho Trợ lý AI: tool bên trong có thể
    #  rollback session (bao-CR-463), và dấu chưa chốt thì tin quay lại INBOX.
    db.commit()
    #  Bật lại "đang soạn tin...": dấu bật lúc nhận tin chỉ sống ~5 giây, mà trạm phân
    #  loại đã ăn mất 2-3 giây, còn Trợ lý AI chạy tool mất thêm 4-10 giây nữa.
    telegram.send_chat_action(chat_id)
    try:
        #  `system` của người gọi chỉ CHÈN THÊM vào cuối, không đè định nghĩa và rào an toàn của
        #  Trợ lý AI; nên web vẫn là «Trợ lý AI», chỉ kênh Telegram mới là Đậu Đậu (ai-CR-016).
        #  ai-CR-053: `provider="agent_gemini"` = khóa của NGƯỜI đang chat, không phải khóa công ty của web.
        result = assistant_service.ask(question, db=db, user=user, history=history, provider=manager.AgentGeminiProvider.name,
                                       system=f"{BOT_PERSONA} {BOT_DRAFT_FACTS} {BOT_LOGIN_FACTS} "
                                              f"{_account_fact(db, chat_id, user)}")
    except Exception as e:  # noqa: BLE001 - lỗi nhà cung cấp phải thành câu trả lời
        log.exception("agent_hub: Trợ lý AI hỏng")
        reply(db, chat_id, f"{BOT_NAME} chưa trả lời được: {telegram.esc(str(e)[:300])}")
        return
    #  Trợ lý AI trả Markdown (web render bằng react-markdown). Gửi qua bộ đổi sang HTML
    #  Telegram, còn sổ giữ nguyên Markdown để lượt sau đưa lại cho model đúng như web.
    tool_calls = result.get("tool_calls") or []
    has_draft = any(isinstance(c, dict) and isinstance(c.get("draft"), dict)
                    and draft_create.kind_of(str(c.get("name") or "")) for c in tool_calls)
    if has_draft:
        #  ai-CR-048: tool soạn nháp dặn model «mời người dùng bấm nút mở form» (đúng cho web), nên câu chữ
        #  của Trợ lý nói ngược thẻ tóm tắt của bot. Chỉ GHI SỔ câu đó (giữ mạch hội thoại), không gửi.
        log_message(db, DIR_OUT, chat_id, 0, result.get("text") or "", action=ACT_ANSWER)
        db.commit()
    else:
        reply(db, chat_id, result.get("text") or "(không có câu trả lời)",
              markdown=True, action=ACT_ANSWER)
    deliver_tool_results(db, chat_id, user, tool_calls)


_NO_ASSISTANT_USER = (
    "Chat này chưa đăng nhập ERP nên em chưa biết hỏi dưới quyền ai. " + _LINK_HELP
    + " (Máy chạy bot vẫn khai được <code>AGENT_ASSISTANT_USER</code> làm tài khoản chung cho chat đại ca; "
    "trên dev để trống — ai-CR-053.)"
)


def _assistant_user(db: Session, chat_id: str = ""):
    """Tài khoản ERP chạy Trợ lý AI cho chat này. None = không có / đã khóa.

    ai-CR-038: chat đã liên kết (`/dangnhap`) chạy dưới CHÍNH tài khoản đã liên kết. Chat của đại ca
    chưa liên kết thì lùi về tài khoản khai cứng `AGENT_ASSISTANT_USER` (`QĐ-AI-10`); chat khác
    không bao giờ được lùi về tài khoản đó.
    """
    from app.modules.user.model import User

    if chat_id:
        link = chat_link.get_active_link(db, chat_id)
        if link is not None:
            linked = db.get(User, link.user_id)
            return linked if linked is not None and linked.is_active else None
        if not telegram.is_allowed_chat(chat_id):
            return None
    email = (settings.AGENT_ASSISTANT_USER or "").strip()
    user = db.scalar(select(User).where(User.email == email)) if email else None
    if user is None or not user.is_active:
        return None
    return user


# ---------------------------------------------------------------------------
# Kết quả tool của Trợ lý AI đưa ra Telegram (ai-CR-009)
# ---------------------------------------------------------------------------
#  Trên web, mỗi khối trong `tool_calls` thành một "lời mời" dưới câu trả lời: nút «Tải
#  báo cáo» cho `file`, thẻ so sánh cũ/mới + nút «Xác nhận sửa» cho `proposal`, nút mở
#  form cho `draft`. Telegram không có màn hình ERP nên ba khối đó phải đi ba đường khác:
#  tệp đẩy thẳng bằng `sendDocument`, đề xuất thành thẻ có hai nút, nháp phiếu chỉ báo
#  là phải mở web (form soạn nháp không dựng được trong khung chat).
def deliver_tool_results(db: Session, chat_id: str, user, tool_calls: list) -> None:
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        if isinstance(call.get("file"), dict):
            _send_report_file(db, chat_id, user, call["file"])
        if isinstance(call.get("proposal"), dict):
            _send_proposal_card(db, chat_id, call["proposal"])
        if isinstance(call.get("draft"), dict):
            _offer_draft(db, chat_id, user, call)


# ---------------------------------------------------------------------------
# Bản nháp chứng từ -> tạo thật khi người dùng nhắn «tạo» (ai-CR-046)
# ---------------------------------------------------------------------------
DRAFT_WINDOW = timedelta(minutes=15)
#  ai-CR-047: một câu vừa tạo vừa gửi duyệt — «tạo và gửi duyệt», «gửi duyệt luôn», «tạo rồi gửi duyệt đi».
_CREATE_SUBMIT = re.compile(r"^((tạo|lưu)\s+(và|rồi|xong)\s+)?gửi duyệt(\s+(luôn|đi|nhé|nha|em|giúp|anh|giùm|lên|"
                            r"đơn|phiếu|này|đó))*[.! ]*$")
_CREATE_YES = re.compile(r"^(tạo|lưu|ok|oke|okay|đồng ý|đúng|ừ|được|làm đi|chuẩn)(\s+(đi|luôn|nhé|nha|em|giúp|"
                         r"anh|giùm|rồi|lại|đơn|phiếu|đó|này))*[.! ]*$")


_LOOSE_YES = re.compile(r"(?<!\w)(tạo|lưu|ok|oke|okay|đồng ý|được|làm đi|link|gửi|nháp|xác nhận)(?!\w)")
_LOOSE_BLOCK = re.compile(r"\d|(?<!\w)(khác|thêm|sửa|đổi|thành|không|thôi|đừng|hủy|bỏ|chưa)(?!\w)")


def _loose_confirm(low: str) -> bool:
    """ai-CR-048: đang có nháp chờ thì «oke tạo đơn nháp đi», «gửi cho anh cái link» cũng là xác nhận.
    Câu dài, có số, hoặc có ý đổi («khác», «sửa», «thêm»…) thì KHÔNG — đó là nhờ soạn lại."""
    return len(low.split()) <= 8 and bool(_LOOSE_YES.search(low)) and not _LOOSE_BLOCK.search(low)


def _offer_draft(db: Session, chat_id: str, user, call: dict) -> None:
    """Tool vừa soạn nháp: tóm tắt + chờ «tạo». Đề nghị thanh toán thì gửi link form web điền sẵn."""
    esc = telegram.esc
    kind = draft_create.kind_of(str(call.get("name") or ""))
    draft = call["draft"]
    if not kind:
        reply(db, chat_id, "Trợ lý đã soạn nháp một loại phiếu mà bot chưa tạo được từ chat; đại ca tạo trên web giúp em.")
        return
    if kind == "payment":
        link = telegram.absolute_url(draft_create.payment_link(draft))
        reply(db, chat_id, "Đề nghị thanh toán dính tiền nên em không tạo từ chat. Em đã điền sẵn form, đại ca mở "
              f'<a href="{esc(link)}">ở đây</a>, xem lại rồi bấm Lưu.')
        return
    replaced = 0
    for old in db.scalars(select(AgentMessage).where(AgentMessage.chat_id == chat_id,
                                                     AgentMessage.action == ACT_DRAFT_WAIT)):
        old.action = ACT_DRAFT_DROPPED
        replaced += 1
    lines = [f"<b>Bản nháp {esc(draft_create.LABELS[kind])}</b>" + (" (thay bản nháp trước)" if replaced else "")]
    lines += [esc(x) for x in draft_create.summarize(kind, draft)]
    if kind in draft_create.SUBMITTABLE:
        lines += ["", "Nhắn «tạo» để lưu Nháp, «tạo và gửi duyệt» để gửi duyệt luôn, «thôi» để bỏ."]
    else:
        lines += ["", "Nhắn «tạo» để em gửi phiếu cho nhóm hỗ trợ, «thôi» để bỏ."]
    reply(db, chat_id, "\n".join(lines))
    log_message(db, DIR_OUT, chat_id, 0, json.dumps({"tool": call.get("name"), "kind": kind,
                                                     "user_id": getattr(user, "id", 0), "draft": draft},
                                                    ensure_ascii=False, default=str),
                action=ACT_DRAFT_WAIT)
    db.commit()


def _draft_by_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """«tạo» / «thôi» cho bản nháp đang chờ của chat này (trong DRAFT_WINDOW)."""
    low = text.strip().lower()
    pending = db.scalar(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_DRAFT_WAIT, AgentMessage.id < row.id)
        .order_by(AgentMessage.id.desc()).limit(1))
    live = pending is not None and not (row.created_at and pending.created_at
                                        and row.created_at - pending.created_at > DRAFT_WINDOW)
    want_submit = bool(_CREATE_SUBMIT.match(low)) or (live and _loose_confirm(low) and "gửi duyệt" in low)
    yes = want_submit or bool(_CREATE_YES.match(low)) or (live and _loose_confirm(low))
    no = bool(_NO.match(low))
    if not (yes or no):
        return (not live) and _detail_recent(db, chat_id, row, low)
    if not live:
        #  Không còn nháp chờ: «gửi duyệt luôn» ngay sau một lần «tạo» thì gửi duyệt phiếu vừa tạo.
        return want_submit and _submit_recent(db, chat_id, row)
    row.action = ACT_COMMAND
    try:
        info = json.loads(pending.body or "{}")
    except ValueError:
        info = {}
    kind, label = info.get("kind", ""), draft_create.LABELS.get(info.get("kind", ""), "phiếu")
    if no:
        pending.action = ACT_DRAFT_DROPPED
        db.commit()
        reply(db, chat_id, f"Dạ, em không tạo {label}.")
        return True
    user = _assistant_user(db, chat_id)
    if user is None or user.id != int(info.get("user_id") or 0):
        pending.action = ACT_DRAFT_DROPPED
        db.commit()
        reply(db, chat_id, "Tài khoản của chat này đã đổi so với lúc soạn nháp, em không tạo. Đại ca nhờ soạn lại giúp em.")
        return True
    if want_submit and kind in draft_create.SUBMITTABLE:
        #  Luật bắt buộc lúc gửi duyệt (web chỉ kiểm ở giao diện): thiếu thì CHƯA tạo gì, nháp vẫn chờ.
        if missing := draft_create.missing_for_submit(kind, info.get("draft") or {}):
            db.commit()
            reply(db, chat_id, f"Chưa gửi duyệt được: {telegram.esc(missing)} Em chưa tạo gì — đại ca bổ sung "
                  "rồi nhờ soạn lại, hoặc nhắn «tạo» để lưu Nháp trước.")
            return True
    #  Chốt dấu TRƯỚC khi ghi phiếu: service có thể rollback, và dấu chưa chốt thì «tạo» lần hai tạo lần hai.
    pending.action = ACT_DRAFT_DONE
    db.commit()
    try:
        code, oid = draft_create.create(db, user, kind, info.get("draft") or {})
    except draft_create.DraftError as e:
        pending.action = ACT_DRAFT_DROPPED
        db.commit()
        reply(db, chat_id, f"Chưa tạo được {label}: {telegram.esc(str(e)[:400])}")
        return True
    #  Nhớ phiếu vừa tạo trên chính dòng sổ nháp, để «gửi duyệt luôn» nhắn sau vẫn biết phiếu nào.
    pending.body = json.dumps({**info, "created": {"id": oid, "code": code}}, ensure_ascii=False, default=str)
    db.commit()
    if want_submit and kind in draft_create.SUBMITTABLE:
        _submit_and_report(db, chat_id, user, kind, oid, code, pending)
        return True
    tail = "Nhắn «gửi duyệt» để gửi duyệt luôn." if kind in draft_create.SUBMITTABLE else ""
    _reply_created(db, chat_id, kind, oid, f"Đã tạo {label}.", tail)
    return True


def _doc_link_html(kind: str, oid: int) -> str:
    """Link mở phiếu. Gốc là AGENT_ERP_URL (hoặc FRONTEND_URL). Địa chỉ nội bộ (localhost, không tên miền)
    Telegram không cho bấm — in nguyên đường dẫn để chép sang trình duyệt trên máy chạy bot."""
    from urllib.parse import urlparse

    base = (settings.AGENT_ERP_URL or settings.FRONTEND_URL or "").rstrip("/")
    url = base + draft_create.DETAIL_PATHS[kind].format(id=oid)
    host = urlparse(url).hostname or ""
    if host and "." in host and not host.startswith("127."):
        return f'<a href="{telegram.esc(url)}">Mở phiếu</a>'
    return f"Mở trên máy chạy bot: <code>{telegram.esc(url)}</code>"


def _reply_created(db: Session, chat_id: str, kind: str, oid: int, head: str, tail: str = "") -> None:
    """Báo phiếu vừa tạo / gửi duyệt KÈM thông tin đọc lại từ DB + link (ai-CR-049). Ghi dấu câu trả lời
    để lượt hỏi sau Trợ lý biết phiếu ĐÃ tạo — không thì «cho chi tiết phiếu» lại bị soạn nháp lần nữa."""
    lines = [f"<b>{telegram.esc(head)}</b>"]
    lines += [telegram.esc(x) for x in draft_create.created_details(db, kind, oid)]
    lines.append(_doc_link_html(kind, oid))
    if tail:
        lines.append(telegram.esc(tail))
    reply(db, chat_id, "\n".join(lines), action=ACT_ANSWER)


def _submit_and_report(db: Session, chat_id: str, user, kind: str, oid: int, code: str,
                       pending: AgentMessage) -> None:
    label = draft_create.LABELS[kind]
    try:
        draft_create.submit(db, user, kind, oid)
    except draft_create.DraftError as e:
        _reply_created(db, chat_id, kind, oid, f"Đã tạo {label} {code} (Nháp) nhưng chưa gửi duyệt được: "
                       f"{str(e)[:400]}")
        return
    info = json.loads(pending.body or "{}")
    info["submitted"] = True
    pending.body = json.dumps(info, ensure_ascii=False, default=str)
    db.commit()
    _reply_created(db, chat_id, kind, oid, f"Đã tạo và gửi duyệt {label}.")


def _submit_recent(db: Session, chat_id: str, row: AgentMessage) -> bool:
    """«gửi duyệt (luôn)» trong DRAFT_WINDOW sau khi vừa «tạo»: gửi duyệt đúng phiếu đó, một lần."""
    done = db.scalar(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_DRAFT_DONE, AgentMessage.id < row.id)
        .order_by(AgentMessage.id.desc()).limit(1))
    if done is None or (row.created_at and done.created_at and row.created_at - done.created_at > DRAFT_WINDOW):
        return False
    try:
        info = json.loads(done.body or "{}")
    except ValueError:
        return False
    created, kind = info.get("created") or {}, info.get("kind", "")
    if not created or kind not in draft_create.SUBMITTABLE or info.get("submitted"):
        return False
    row.action = ACT_COMMAND
    user = _assistant_user(db, chat_id)
    if user is None or user.id != int(info.get("user_id") or 0):
        db.commit()
        reply(db, chat_id, "Tài khoản của chat này đã đổi so với lúc tạo phiếu, em không gửi duyệt.")
        return True
    if missing := draft_create.missing_for_submit(kind, info.get("draft") or {}):
        db.commit()
        reply(db, chat_id, f"Chưa gửi duyệt được: {telegram.esc(missing)} Đại ca bổ sung trên phiếu rồi gửi duyệt.")
        return True
    _submit_and_report(db, chat_id, user, kind, int(created["id"]), str(created.get("code", "")), done)
    return True


#  ai-CR-049: vừa tạo xong mà hỏi «chi tiết / thông tin / link» thì trả phiếu vừa tạo, không đi Trợ lý.
_DETAIL_Q = re.compile(r"(?<!\w)(chi tiết|thông tin|link|xem|mở)(?!\w)")


def _detail_recent(db: Session, chat_id: str, row: AgentMessage, low: str) -> bool:
    if len(low.split()) > 8 or re.search(r"\d", low) or not _DETAIL_Q.search(low):
        return False
    done = db.scalar(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_DRAFT_DONE, AgentMessage.id < row.id)
        .order_by(AgentMessage.id.desc()).limit(1))
    if done is None or (row.created_at and done.created_at and row.created_at - done.created_at > DRAFT_WINDOW):
        return False
    try:
        info = json.loads(done.body or "{}")
    except ValueError:
        return False
    created, kind = info.get("created") or {}, info.get("kind", "")
    if not created or kind not in draft_create.DETAIL_PATHS:
        return False
    row.action = ACT_COMMAND
    db.commit()
    _reply_created(db, chat_id, kind, int(created["id"]), f"{draft_create.LABELS[kind].capitalize()} vừa tạo:")
    return True


def _send_report_file(db: Session, chat_id: str, user, meta: dict) -> None:
    """Tệp do tool `export_report_file` xuất: đọc byte từ kho, gửi làm tệp đính kèm.

    Chốt sở hữu chép đúng endpoint tải trên web (`assistant/controller.download_report_file`):
    tệp phải của CHÍNH tài khoản bot đang mượn và nằm trong thư mục `assistant-report/`.
    Không có chốt này thì một khối `file` bịa id là lối tải mọi tệp đính kèm trong kho.
    """
    from app.core.storage import download_bytes
    from app.modules.attachment.model import StoredFile

    f = db.get(StoredFile, int(meta.get("id") or 0)) if str(meta.get("id") or "").isdigit() else None
    if f is None or f.created_by != user.id or "/assistant-report/" not in (f.file_key or ""):
        reply(db, chat_id, "Trợ lý báo có tệp báo cáo nhưng em không tìm thấy nó trong kho.")
        return
    telegram.send_chat_action(chat_id, "upload_document")
    try:
        data = download_bytes(f.file_key)
        mid = telegram.send_document(chat_id, f.filename, data,
                                     caption=f"<b>{telegram.esc(f.filename)}</b>",
                                     content_type=f.content_type or "")
    except Exception as e:  # noqa: BLE001 - kho hay Telegram hỏng đều phải thành câu trả lời
        log.exception("agent_hub: gửi tệp %s hỏng", f.id)
        reply(db, chat_id,
              f"Không gửi được tệp <b>{telegram.esc(f.filename)}</b> "
              f"({telegram.esc(str(e)[:200])}). Đại ca tải trên web: "
              f"{telegram.esc(telegram.absolute_url(str(meta.get('download_url') or '')))}")
        return
    log_message(db, DIR_OUT, chat_id, mid, f"[tệp] {f.filename} ({f.size} byte)",
                action=ACT_FILE)


def _send_proposal_card(db: Session, chat_id: str, proposal: dict) -> None:
    """Đề xuất sửa phiếu (tool `propose_document_update`) thành thẻ so sánh cũ/mới + hai nút.

    Token xác nhận dài vài trăm byte, mà `callback_data` của Telegram chỉ chứa 64 — nên
    ghi cả khối đề xuất vào sổ (`body` = JSON, dấu `de_xuat`) và nút chỉ mang id dòng sổ.
    Token là Fernet buộc vào tài khoản bot + hạn 15 phút, `confirm_update` kiểm lại toàn bộ
    lúc bấm; nằm trong sổ cũng như nằm trong trang web đang mở.
    """
    row = log_message(db, DIR_OUT, chat_id, 0, json.dumps(proposal, ensure_ascii=False),
                      action=ACT_PROPOSAL)
    lines = [
        f"<b>Đề xuất sửa {telegram.esc(proposal.get('entity_label') or 'phiếu')} "
        f"{telegram.esc(proposal.get('code') or '')}</b>"
        + (f" · {telegram.esc(proposal.get('doc_status_label'))}"
           if proposal.get("doc_status_label") else ""),
    ]
    for ch in proposal.get("changes") or []:
        if not isinstance(ch, dict):
            continue
        old = telegram.esc(ch.get("old") or "") or "(trống)"
        new = telegram.esc(ch.get("new") or "") or "(trống)"
        lines.append(f"• {telegram.esc(ch.get('label') or ch.get('field') or '')}: "
                     f"<s>{old}</s> → <b>{new}</b>")
    lines += [
        "",
        "Phiếu <b>CHƯA</b> sửa. Bấm <b>Xác nhận sửa</b> trong 15 phút, quá hạn phải nhờ "
        "trợ lý soạn lại.",
    ]
    if proposal.get("url"):
        lines.append(f"Xem phiếu: {telegram.esc(telegram.absolute_url(str(proposal['url'])))}")
    try:
        row.tg_message_id = telegram.send(
            "\n".join(lines), chat_id=chat_id,
            buttons=[("Xác nhận sửa", f"sua:{row.id}"), ("Không sửa", f"khong_sua:{row.id}")],
        )
    except telegram.TelegramError as e:
        #  Thẻ không tới tay thì không ai bấm được — đóng luôn, đừng để một đề xuất treo
        #  trong sổ mà Telegram không có nút nào trỏ tới.
        log.exception("agent_hub: gửi thẻ đề xuất hỏng")
        row.action = ACT_PROPOSAL_DROPPED
        reply(db, chat_id, f"Không gửi được thẻ đề xuất sửa: {telegram.esc(str(e)[:200])}")


def _resolve_proposal(db: Session, chat_id: str, cb_id: str, action: str, msg_id: int) -> None:
    """Đại ca bấm một trong hai nút của thẻ đề xuất sửa phiếu.

    Ghi phiếu đi qua ĐÚNG `confirm_update` của Trợ lý AI web: kiểm token, hạn, quyền, phạm
    vi, trạng thái rồi ghi bằng service của form — bot không có đường ghi riêng nào.
    """
    from fastapi import HTTPException

    from app.modules.assistant.tools.update_tool import confirm_update

    row = db.get(AgentMessage, msg_id) if msg_id else None
    if row is None or row.direction != DIR_OUT:
        telegram.answer_callback(cb_id, "Không tìm thấy đề xuất này trong sổ")
        return
    if row.action != ACT_PROPOSAL:
        telegram.answer_callback(cb_id, "Đề xuất này đã xử rồi")
        return
    try:
        proposal = json.loads(row.body or "{}")
    except ValueError:
        proposal = {}
    code = telegram.esc(proposal.get("code") or "")
    log_message(db, DIR_IN, chat_id, 0, f"{action}:{msg_id}", action=ACT_COMMAND)

    if action == "khong_sua":
        row.action = ACT_PROPOSAL_DROPPED
        telegram.answer_callback(cb_id, "Đã bỏ")
        reply(db, chat_id, f"Rồi, không sửa <b>{code}</b>. Phiếu giữ nguyên.")
        return

    user = _assistant_user(db, chat_id)
    if user is None:
        telegram.answer_callback(cb_id, "Chưa khai tài khoản")
        reply(db, chat_id, _NO_ASSISTANT_USER)
        return
    #  Chốt dấu + tin bấm nút TRƯỚC khi ghi phiếu: service của form có thể rollback
    #  (bao-CR-463), và dấu chưa chốt thì nút bấm lại lần nữa vẫn ghi lần nữa.
    db.commit()
    try:
        done = confirm_update(db, user, str(proposal.get("confirm_token") or ""))
    except HTTPException as e:
        db.rollback()
        row = db.get(AgentMessage, msg_id)
        row.action = ACT_PROPOSAL_DROPPED
        telegram.answer_callback(cb_id, "Không sửa được")
        reply(db, chat_id, f"Không sửa được <b>{code}</b>: {telegram.esc(str(e.detail))}")
        return
    except Exception as e:  # noqa: BLE001 - lỗi lạ cũng phải thành câu trả lời, không nuốt
        log.exception("agent_hub: xác nhận sửa phiếu hỏng")
        db.rollback()
        row = db.get(AgentMessage, msg_id)
        row.action = ACT_PROPOSAL_DROPPED
        telegram.answer_callback(cb_id, "Lỗi")
        reply(db, chat_id, f"Sửa <b>{code}</b> gặp lỗi: {telegram.esc(str(e)[:300])}")
        return
    row.action = ACT_PROPOSAL_DONE
    telegram.answer_callback(cb_id, "Đã sửa")
    fields = ", ".join(telegram.esc(x) for x in (done.get("updated_fields") or []))
    text = (f"Đã sửa <b>{telegram.esc(done.get('entity_label') or '')} "
            f"{telegram.esc(done.get('code') or code)}</b>"
            + (f": {fields}." if fields else "."))
    if done.get("url"):
        text += f"\nXem phiếu: {telegram.esc(telegram.absolute_url(str(done['url'])))}"
    reply(db, chat_id, text)


# ---------------------------------------------------------------------------
# Vòng gom — INBOX thành task
# ---------------------------------------------------------------------------
def triage_inbox(db: Session, *, force: bool = False) -> int:
    """Gom tin đang chờ thành task (chạy bằng khóa Gemini của đại ca, ai-CR-053). Trả số task vừa tạo."""
    if user_keys.in_context():
        return _triage_inbox(db, force=force)
    with user_keys.for_admin(db) as key:
        if not key:
            log.warning("agent_hub: chưa có khóa Gemini của đại ca, chưa gom tin (tin vẫn chờ ở INBOX)")
            return 0
        return _triage_inbox(db, force=force)


def _triage_inbox(db: Session, *, force: bool = False) -> int:
    """Gom tin đang chờ thành task. Trả số task vừa tạo.

    `force=False` (vòng theo lịch) chỉ nhận tin đã nằm yên đủ `AGENT_TRIAGE_DELAY_SEC`.
    Cửa sổ lặng đó là thứ làm chức năng gom có nghĩa: không có nó thì mỗi câu đại ca gõ
    ra thành một task riêng, và bot không bao giờ có hai tin cùng lúc để mà gom.
    """
    q = (
        select(AgentMessage)
        .where(AgentMessage.direction == DIR_IN, AgentMessage.task_id == 0,
               AgentMessage.action == "")
        .order_by(AgentMessage.id)
        .limit(settings.AGENT_TRIAGE_BATCH)
    )
    if not force:
        q = q.where(
            AgentMessage.created_at
            <= datetime.now() - timedelta(seconds=settings.AGENT_TRIAGE_DELAY_SEC)
        )
    rows = list(db.scalars(q))
    if not rows:
        return 0

    left = _quota_left(db)
    if left <= 0:
        log.warning("agent_hub: chạm trần %d việc/ngày, hoãn gom", settings.AGENT_DAILY_TASK_CAP)
        return 0

    run = start_run(db, 0, STAGE_TRIAGE)
    try:
        data, result = manager.run_triage([{"id": r.id, "text": r.body} for r in rows])
    except Exception as e:  # noqa: BLE001
        finish_run(db, run, error=str(e))
        db.commit()
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
              f"Gom việc lỗi, tin vẫn nằm trong sổ chờ lượt sau: {telegram.esc(str(e)[:300])}")
        return 0
    finish_run(db, run, result=result)

    by_id = {r.id: r for r in rows}
    created = []
    for group in data["groups"][:left]:
        created.append(_create_task(db, group, by_id))
    db.commit()

    for task in created:
        #  Chạy thẳng sang PLAN. Tấm thẻ "đã ghi nhận việc, bấm Lập kế hoạch" chỉ nhai
        #  lại lời đại ca vừa nhắn rồi bắt bấm thêm một nút — đại ca cần PHƯƠNG ÁN để
        #  duyệt. QĐ-AI-5 chỉ bắt dừng ở PLAN -> CODE nên tự đi tới PLAN là đúng luật.
        #  Từ ai-CR-017: đi qua bước rà soát mã thật trước (runner), runner lập kế hoạch sau.
        start_scan(db, task)
    db.commit()
    return len(created)


def _create_task(db: Session, group: dict, by_id: dict) -> AgentTask:
    task = AgentTask(
        code=next_code(db),
        title=group["title"],
        source=SRC_TELEGRAM,
        status=ST_TRIAGE,
        summary=group["summary"],
        risk_level=group["risk_level"],
    )
    db.add(task)
    db.flush()
    photos = 0
    for mid in group["message_ids"]:
        db.add(AgentTaskItem(task_id=task.id, source=SRC_TELEGRAM, ref_id=mid,
                             merged_by=MERGED_BY_BOT))
        #  Gắn tin vào task = rút nó khỏi INBOX. Quên bước này thì lượt gom sau lại
        #  nhặt đúng mấy tin đó và đẻ ra task trùng.
        by_id[mid].task_id = task.id
        photos += len(by_id[mid].files or [])
    if photos:
        #  ai-CR-035: trạm kế hoạch (Gemini) chỉ đọc chữ; ghi lại để nó biết rà soát đã có ảnh.
        task.summary = (task.summary or "").rstrip() + f"\n\n(Kèm {photos} ảnh chụp màn hình, bước rà soát mã đã xem ảnh.)"
    return task


# ---------------------------------------------------------------------------
# Phiếu hỗ trợ ERP làm nguồn việc (ai-CR-037, AN-005)
# ---------------------------------------------------------------------------
#  Một phiếu = một việc, KHÔNG qua trạm gom (phiếu đã là một yêu cầu trọn vẹn do người dùng viết).
#  Con trỏ `erp_ticket_since` = id phiếu lớn nhất lúc bật tính năng: cửa theo nhãn bộ phận chỉ nhận
#  phiếu MỚI hơn nó (bật lên không kéo cả lịch sử phiếu cũ vào hàng việc); cửa giao cho tài khoản
#  bot thì nhận cả phiếu cũ vì đó là người chủ động giao.
TICKET_CURSOR = "erp_ticket_since"
TICKET_BATCH = 5
_TICKET_OPEN = ("open", "in_progress")


def _named_cursor(db: Session, name: str) -> AgentCursor | None:
    return db.scalar(select(AgentCursor).where(AgentCursor.name == name))


def _ticket_bot_user(db: Session):
    from app.modules.user.model import User

    email = (settings.AGENT_TICKET_ASSIGNEE or "").strip()
    return db.scalar(select(User).where(User.email == email)) if email else None


def _ticket_departments() -> set[str]:
    return {d.strip().casefold() for d in (settings.AGENT_TICKET_DEPARTMENTS or "").split(",") if d.strip()}


def pull_tickets(db: Session) -> int:
    """Phiếu hỗ trợ đủ điều kiện mà chưa thành việc -> việc mới, đi thẳng bước rà soát. Trả số việc."""
    from app.modules.ticket.model import Ticket

    bot_user = _ticket_bot_user(db)
    departments = _ticket_departments()
    if bot_user is None and not departments:
        return 0
    cursor = _named_cursor(db, TICKET_CURSOR)
    if cursor is None:
        #  Lần đầu bật: mốc = phiếu mới nhất hiện có, phiếu cũ không tự tràn vào theo nhãn bộ phận.
        cursor = AgentCursor(name=TICKET_CURSOR, value=int(db.scalar(select(func.max(Ticket.id))) or 0))
        db.add(cursor)
        db.commit()
    linked = select(AgentTaskItem.ref_id).where(AgentTaskItem.source == SRC_ERP_TICKET)
    rows = list(db.scalars(select(Ticket).where(Ticket.status.in_(_TICKET_OPEN), Ticket.id.not_in(linked))
                           .order_by(Ticket.id).limit(200)))
    picked = [t for t in rows
              if (bot_user is not None and t.assignee_id == bot_user.id)
              or (t.id > cursor.value and (t.department or "").strip().casefold() in departments)]
    created = 0
    for ticket in picked[:TICKET_BATCH]:
        if _quota_left(db) <= 0:
            log.warning("agent_hub: chạm trần việc/ngày, phiếu %s chờ lượt sau", ticket.code)
            break
        task = _task_from_ticket(db, ticket, bot_user)
        created += 1
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
              f"Phiếu hỗ trợ <b>{telegram.esc(ticket.code)}</b> thành việc <b>{telegram.esc(task.code)}</b>: "
              f"{telegram.esc(ticket.subject[:120])}", task_id=task.id)
        db.commit()
        start_scan(db, task)
        db.commit()
    return created


def _task_from_ticket(db: Session, ticket, bot_user) -> AgentTask:
    from app.modules.employee.model import Employee
    from app.modules.ticket.model import TicketMessage

    first = db.scalar(select(TicketMessage).where(TicketMessage.ticket_id == ticket.id,
                                                  TicketMessage.is_staff.is_(False))
                      .order_by(TicketMessage.id).limit(1))
    requester = db.get(Employee, ticket.requester_id) if ticket.requester_id else None
    who = (requester.full_name if requester is not None else "") or "người dùng"
    lines = [f"Phiếu hỗ trợ {ticket.code} của {who} (bộ phận: {ticket.department or 'không ghi'}, "
             f"ưu tiên: {ticket.priority}).", "", ticket.subject or ""]
    if first is not None and (first.body or "").strip():
        lines += ["", first.body.strip()]
    if ticket.origin_url:
        lines += ["", f"Trang người gửi đang đứng lúc tạo phiếu: {ticket.origin_url}"]
    task = AgentTask(code=next_code(db), title=(ticket.subject or ticket.code)[:255], source=SRC_ERP_TICKET,
                     status=ST_TRIAGE, summary="\n".join(lines), risk_level=RISK_MEDIUM)
    db.add(task)
    db.flush()
    db.add(AgentTaskItem(task_id=task.id, source=SRC_ERP_TICKET, ref_id=ticket.id, merged_by=MERGED_BY_BOT))
    _ticket_note(db, ticket, bot_user,
                 f"Phiếu đã chuyển cho bot sửa mã {BOT_NAME} (mã việc {task.code}). Kết quả sẽ báo lại ở đây.",
                 status="in_progress")
    db.commit()
    return task


def _ticket_note(db: Session, ticket, bot_user, body: str, *, status: str) -> None:
    """Một dòng trả lời của nhóm hỗ trợ trên phiếu + đặt trạng thái (không qua service để khỏi tự
    đổi trạng thái sang «Đã trả lời» lúc bot mới NHẬN việc)."""
    from app.modules.ticket.model import TicketMessage

    uid = bot_user.id if bot_user is not None else 0
    db.add(TicketMessage(ticket_id=ticket.id, body=body, is_staff=True, created_by=uid, updated_by=uid))
    ticket.status = status
    ticket.closed_at = None
    ticket.updated_by = uid


def _tickets_of(db: Session, task: AgentTask) -> list:
    from app.modules.ticket.model import Ticket

    ids = db.scalars(select(AgentTaskItem.ref_id).where(AgentTaskItem.task_id == task.id,
                                                        AgentTaskItem.source == SRC_ERP_TICKET)).all()
    return list(db.scalars(select(Ticket).where(Ticket.id.in_(ids)))) if ids else []


def report_to_tickets(db: Session, task: AgentTask, *, done: bool) -> None:
    """Việc đóng -> báo lại trên phiếu gốc. Xong: «Đã trả lời». Bỏ: trả phiếu về hàng chờ người."""
    tickets = _tickets_of(db, task)
    if not tickets:
        return
    bot_user = _ticket_bot_user(db)
    for t in tickets:
        if done:
            _ticket_note(db, t, bot_user, f"{BOT_NAME} đã sửa xong việc {task.code}, bản sửa đã lên môi trường "
                         "thử (dev). Anh/chị kiểm tra lại giúp, còn lỗi thì trả lời ngay trên phiếu này.",
                         status="answered")
        else:
            _ticket_note(db, t, bot_user, f"Bot không xử lý việc {task.code}; nhóm hỗ trợ sẽ xử lý phiếu này.",
                         status="open")
            if bot_user is not None and t.assignee_id == bot_user.id:
                t.assignee_id = 0
    db.commit()


def _quota_left(db: Session) -> int:
    """Còn được tạo bao nhiêu task hôm nay.

    Trần này canh CHI PHÍ lẫn sự tỉnh táo: một vòng gom hỏng có thể đẻ ra hàng chục
    task, mỗi task một lượt gọi model và một tiếng chuông.
    """
    #  «Hôm nay» theo giờ Việt Nam: tính theo UTC thì trần reset lúc 7 giờ sáng (ai-CR-020).
    today = to_utc(now_local().replace(hour=0, minute=0, second=0, microsecond=0))
    used = db.scalar(select(func.count(AgentTask.id)).where(AgentTask.created_at >= today)) or 0
    return max(0, settings.AGENT_DAILY_TASK_CAP - used)


def next_code(db: Session) -> str:
    """Mã việc dạng `AI-0007`, đánh tiếp số lớn nhất đang có."""
    last = db.scalar(select(func.max(AgentTask.id))) or 0
    return f"AI-{last + 1:04d}"


# ---------------------------------------------------------------------------
# Trạm PLAN
# ---------------------------------------------------------------------------
def plan_task(db: Session, task: AgentTask) -> None:
    """Lập kế hoạch. Gọi từ worker (ngoài ngữ cảnh) thì chạy bằng khóa của đại ca (ai-CR-053)."""
    if user_keys.in_context():
        _plan_task(db, task)
        return
    with user_keys.for_admin(db):
        _plan_task(db, task)


def _plan_task(db: Session, task: AgentTask) -> None:
    docs = memory.recall(f"{task.title}\n{task.summary}")
    #  Luật 3 của sổ quyết định (ai-CR-015): việc rủi ro cao không được nạp sổ, cấm giả định.
    strict = int(task.risk_level or 0) >= RISK_HIGH
    run = start_run(db, task.id, STAGE_PLAN)
    try:
        data, result = manager.run_plan(task.title, task.summary, docs,
                                        playbook="" if strict else playbook.prompt_block(task.risk_level),
                                        strict=strict, review=coder.scan_message_for(task))
    except Exception as e:  # noqa: BLE001
        finish_run(db, run, error=str(e))
        db.commit()
        #  Kèm nút lập lại: không có nó thì việc vừa nhận câu trả lời nằm ở «Đang hỏi lại» mà không
        #  còn câu hỏi, không nút, không lối ra (AI-0007, 23/09/2026).
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
              f"Lập kế hoạch cho <b>{telegram.esc(task.code)}</b> lỗi: "
              f"{telegram.esc(str(e)[:300])}", task_id=task.id,
              buttons=[("Lập lại kế hoạch", f"plan:{task.id}"), ("Bỏ việc này", f"no:{task.id}")])
        return
    finish_run(db, run, result=result)

    task.plan = data["plan"]
    task.plan_files = resolve_plan_files(data["plan_files"], _scan_files(db, task))
    task.test_plan = data["test_plan"]
    task.related_docs = data["related_docs"]
    task.questions = data["questions"]
    task.risk_level = data["risk_level"]
    needs = data["needs_clarification"]
    assumptions = data.get("assumptions") or []
    open_scan_qs = _scan_questions(db, task)
    if assumptions and (strict or task.risk_level >= RISK_HIGH):
        #  Model tự giả định trên một việc rủi ro cao (kể cả khi chính lượt này mới nâng mức):
        #  luật 3 nói việc đó luôn hỏi, nên mọi giả định thành câu hỏi. Thi hành ở mã, không nhờ lời nhắc.
        #  ai-CR-021: gọn lại — «Chưa làm: … chờ đại ca quyết: Q» chỉ giữ Q, câu trùng bỏ bớt.
        task.questions = merge_questions(
            list(task.questions or []) + [assumption_question(a) for a in assumptions] + open_scan_qs)
        needs = True
    else:
        if assumptions:
            #  Ghi vào chính bản kế hoạch: thẻ duyệt hiện ra, và runner đọc lại y nguyên trong đề bài.
            task.plan = (task.plan or "").rstrip() + "\n\n**Em tự quyết, không hỏi lại:**\n" + \
                "\n".join(f"- {a}" for a in assumptions)
        #  Câu rà soát nêu mà kế hoạch không nhắc tới: tự thêm, để thẻ này là chỗ duy nhất hỏi và
        #  không câu nào bị rơi (đoạn phân tích không liệt kê câu hỏi nữa).
        seen = _norm_q((task.plan or "") + " " + " ".join(task.questions or []))
        missing = [q for q in open_scan_qs if _norm_q(q) not in seen]
        if missing and needs:
            task.questions = merge_questions(list(task.questions or []) + missing)
        elif missing:
            task.plan = (task.plan or "").rstrip() + "\n\n**Còn chờ đại ca quyết:**\n" + \
                "\n".join(f"- {q}" for q in missing)
    #  `plan_files` rỗng = bot không viết nổi phạm vi cụ thể = CẤM đi tiếp (luật B2).
    #  Đây là chỗ thi hành luật đó, không phải câu nhắc gửi cho model.
    task.status = ST_NEEDS_INPUT if needs else ST_PLAN
    db.commit()
    send_plan_card(db, task)
    db.commit()


# ---------------------------------------------------------------------------
# Rà soát mã trước kế hoạch (ai-CR-017)
# ---------------------------------------------------------------------------
#  Runner chạy `-c 1`: lượt rà soát có thể xếp hàng sau một lượt sửa mã (tối đa 30 phút). Quá
#  khoảng này mà lượt rà soát chưa BẮT ĐẦU thì coi như mất, lập kế hoạch theo tài liệu.
SCAN_QUEUE_GRACE = timedelta(minutes=45)


def start_scan(db: Session, task: AgentTask) -> None:
    """Giao runner rà soát mã, báo đại ca đã nhận việc. Runner tắt / broker chết thì lập kế
    hoạch theo tài liệu ngay, như trước ai-CR-017."""
    if not settings.AGENT_CODER_ENABLED:
        plan_task(db, task)
        return
    task.status = ST_SCANNING
    db.commit()
    try:
        coder.dispatch_scan(task.id)
        _runner_wait_note(db, task)
    except Exception:  # noqa: BLE001
        log.exception("agent_hub: giao rà soát mã hỏng, lập kế hoạch theo tài liệu")
        task.status = ST_TRIAGE
        db.commit()
        plan_task(db, task)
        return
    reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
          f"{BOT_NAME} nhận việc <b>{telegram.esc(task.code)}</b> · {telegram.esc(task.title)}.\n"
          f"Em đang đọc mã trên <code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code> để rà soát "
          "trước, xong em nhắn đại ca phân tích rồi gửi kế hoạch (thường 2-5 phút; runner đang "
          "sửa việc khác thì lâu hơn).", task_id=task.id)


_PENDING_Q = re.compile(r"(?is)^\s*chưa làm:.*?chờ đại ca quyết:\s*(.+)$")


def _norm_q(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", (text or "").lower()).split())


def assumption_question(assumption: str) -> str:
    """Giả định -> câu hỏi NGẮN cho việc rủi ro cao (ai-CR-021)."""
    m = _PENDING_Q.match(assumption or "")
    if m:
        return m.group(1).strip()
    text = re.sub(r"(?i)^\s*em giả định:\s*", "", (assumption or "").strip()).rstrip(" .")
    return f"{text} — đại ca đồng ý không?"


def merge_questions(questions: list[str]) -> list[str]:
    """Bỏ câu trùng (so sau khi bỏ dấu câu, hoặc câu này nằm trọn trong câu kia)."""
    out: list[str] = []
    for q in (str(x).strip() for x in questions):
        if not q:
            continue
        n = _norm_q(q)
        if any(n == _norm_q(o) or n in _norm_q(o) or _norm_q(o) in n for o in out):
            continue
        out.append(q)
    return out


def _scan_questions(db: Session, task: AgentTask) -> list[str]:
    run = coder.latest_scan_run(db, task)
    art = run.artifact if run is not None and isinstance(run.artifact, dict) else {}
    if art.get("answered"):
        return []
    return [str(q) for q in (art.get("info") or {}).get("questions") or [] if str(q).strip()]


def _scan_files(db: Session, task: AgentTask) -> list[str]:
    run = coder.latest_scan_run(db, task)
    art = run.artifact if run is not None and isinstance(run.artifact, dict) else {}
    return [str(f) for f in (art.get("info") or {}).get("files") or []]


def resolve_plan_files(files: list[str], scan_files: list[str]) -> list[str]:
    """Tên tệp trơn (thiếu thư mục, ca AI-0006: `PurchaseRequestDetail.tsx`) -> đường dẫn đầy
    đủ lấy từ kết quả rà soát, khi khớp đúng MỘT tệp. Không khớp hay khớp nhiều thì giữ nguyên."""
    out = []
    for f in files:
        if "/" not in f:
            hits = [s for s in scan_files if s.rsplit("/", 1)[-1] == f]
            if len(hits) == 1:
                f = hits[0]
        if f not in out:
            out.append(f)
    return out


def _resume_stuck_scans(db: Session, now: datetime) -> int:
    rows = db.scalars(select(AgentTask).where(AgentTask.status == ST_SCANNING)
                      .order_by(AgentTask.id)).all()
    count = 0
    for task in rows:
        run = db.scalar(select(AgentRun).where(AgentRun.task_id == task.id,
                                               AgentRun.stage == STAGE_SCAN)
                        .order_by(AgentRun.id.desc()).limit(1))
        if run is None:
            if task.updated_at and task.updated_at > now - SCAN_QUEUE_GRACE:
                continue          # còn xếp hàng sau một lượt sửa mã
            why = "lượt rà soát không bắt đầu được"
        elif run.status == RUN_RUNNING:
            limit = timedelta(seconds=coder.SCAN_TIMEOUT_SEC) + STUCK_TRIAGE_AFTER
            if run.started_at and run.started_at > now - limit:
                continue          # đang đọc mã
            coder._close_run(run, status=RUN_ERROR, error="mất dấu: runner không đóng lượt rà soát")
            why = "lượt rà soát mất dấu giữa chừng"
        else:
            why = "lượt rà soát đã đóng nhưng chưa lập kế hoạch"
        log.warning("agent_hub: %s kẹt ở rà soát (%s), lập kế hoạch theo tài liệu", task.code, why)
        task.status = ST_TRIAGE
        db.commit()
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
              f"<b>{telegram.esc(task.code)}</b>: {why}, em lập kế hoạch theo tài liệu.", task_id=task.id)
        plan_task(db, task)
        db.commit()
        count += 1
    return count


#  Việc đã gom mà quá khoảng này vẫn chưa có kế hoạch = lượt PLAN chết giữa chừng (worker bị
#  khởi động lại khi Gemini đang nghĩ — ca AI-0006 ngày 23/09/2026: đại ca nhắn, bot im mãi).
#  Lượt PLAN bị giết không để lại dòng sổ nào (chưa commit), nên phải dò theo trạng thái việc.
STUCK_TRIAGE_AFTER = timedelta(minutes=3)
#  Lượt PLAN hỏng THẬT (Gemini lỗi) có ghi sổ và đã nhắn lỗi; quá chừng này lần thì thôi thử lại,
#  không thì mỗi phút một tin báo lỗi.
MAX_PLAN_ATTEMPTS = 2


def resume_stuck_plans(db: Session, now: datetime | None = None) -> int:
    """Lập lại kế hoạch cho việc kẹt ở trạm gom. Trả số việc đã lập lại. Vòng beat mỗi phút gọi."""
    now = now or datetime.now()
    count = _resume_stuck_scans(db, now)
    rows = db.scalars(
        select(AgentTask).where(AgentTask.status == ST_TRIAGE,
                                #  updated_at, không created_at: việc rà soát xong mới về TRIAGE
                                #  (ai-CR-017), tính từ lúc tạo thì lập kế hoạch trùng.
                                AgentTask.updated_at <= now - STUCK_TRIAGE_AFTER)
        .order_by(AgentTask.id)
    ).all()
    for task in rows:
        tries = db.scalar(select(func.count(AgentRun.id)).where(
            AgentRun.task_id == task.id, AgentRun.stage == STAGE_PLAN)) or 0
        if tries >= MAX_PLAN_ATTEMPTS:
            continue
        log.warning("agent_hub: %s kẹt ở trạm gom, lập lại kế hoạch", task.code)
        plan_task(db, task)
        db.commit()
        count += 1
    return count


# ---------------------------------------------------------------------------
# Thẻ Telegram
# ---------------------------------------------------------------------------
def _card_md(text: str, limit: int = 3000) -> str:
    """Markdown -> HTML Telegram cho thân thẻ; dài quá trần thì lùi về chữ thường đã thoát,
    vì cắt ngang một chuỗi HTML là Telegram từ chối cả tin."""
    rendered = telegram.md_to_html(text or "")
    return rendered if len(rendered) <= limit else telegram.esc(text or "")


def send_plan_card(db: Session, task: AgentTask) -> None:
    lines = [f"<b>{telegram.esc(task.code)}</b> · {telegram.esc(task.title)}", ""]
    if task.questions:
        lines += ["<b>Bot chưa đủ thông tin, đang hỏi lại:</b>"]
        lines += [f"• {telegram.esc(q)}" for q in task.questions]
        minutes = int(PLAN_ANSWER_WINDOW.total_seconds() // 60)
        lines += ["", f"Đại ca nhắn trả lời ngay bên dưới (trong {minutes} phút), em lập lại kế "
                      "hoạch luôn. " + (f"Trả lời trễ hơn thì nhắn «sửa: …»." if settings.AGENT_TG_COMPACT
                                        else "Trả lời trễ hơn thì bấm «Trả lời câu hỏi» trước.")]
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join(lines), task_id=task.id,
              action=ACT_WAIT_PLAN_ANSWER,
              buttons=[("Trả lời câu hỏi", f"ans:{task.id}"), ("Bỏ việc này", f"no:{task.id}")])
        return

    #  Kế hoạch do model viết là Markdown (`tệp`, **đậm**, 1. 2.): đổi sang HTML Telegram như
    #  câu trả lời của Trợ lý AI, không in thô dấu nháy và dấu sao (đại ca báo 23/09/2026).
    lines += [_card_md(task.plan), ""]
    lines += ["<b>Tệp sẽ đụng:</b>"] + [f"• <code>{telegram.esc(f)}</code>" for f in task.plan_files]
    if task.test_plan:
        lines += ["", "<b>Kiểm thử:</b>", _card_md(task.test_plan[:500])]
    #  ai-CR-022: bỏ mục «Tài liệu đã tra» (AI-0007 lặp change-log.md bốn lần) và câu giải thích
    #  rủi ro cố định — thẻ dài mà không giúp bấm Duyệt hay không. Danh sách tài liệu vẫn nằm
    #  trong sổ và trong đề bài của runner.
    lines += ["", f"Rủi ro: <b>{RISK_LABELS.get(task.risk_level, '?')}</b>"]
    #  Thẻ kế hoạch nay là thẻ DUY NHẤT của một việc, nên phải nói rõ nó gom từ mấy tin,
    #  không thì đại ca tưởng bot bỏ sót mấy tin kia.
    n_items = db.scalar(
        select(func.count(AgentTaskItem.id)).where(AgentTaskItem.task_id == task.id)
    ) or 0
    if n_items > 1:
        lines += [f"Gom từ {n_items} tin nhắn."]
    if settings.AGENT_TG_COMPACT:
        lines += ["", "Nhắn «duyệt» để em sửa mã, «sửa: <điều cần đổi>» để em lập lại kế hoạch, "
                      "hoặc «bỏ việc này»."]
    reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join(lines), task_id=task.id,
          buttons=[("Duyệt", f"ok:{task.id}"), ("Sửa lại", f"fix:{task.id}"),
                   ("Bỏ việc này", f"no:{task.id}")])


#  Nhãn bước cho bảng lịch sử của /xem (ai-CR-020). Ngắn cho vừa màn hình điện thoại.
_STAGE_SHORT = {
    STAGE_TRIAGE: "Gom", STAGE_PLAN: "Kế hoạch", ST_CODE: "Sửa mã", STAGE_INTENT: "Phân loại",
    STAGE_DEPLOY: "Gộp+dev", STAGE_REVERT: "Thu hồi", STAGE_RULE: "Nháp sổ", STAGE_SCAN: "Rà soát",
}
_RUN_SHORT = {RUN_RUNNING: "đang", RUN_OK: "xong", RUN_ERROR: "lỗi"}
XEM_BUDGET = 3700   # chừa chỗ dưới telegram.MAX_TEXT
_CODE_ARG = re.compile(r"(?i)^(?:ai)?[-\s]*0*(\d{1,6})$")


def _task_code(arg: str) -> str:
    """`AI-0006` · `ai-6` · `AI6` · `6` -> `AI-0006`; không đọc được thì rỗng."""
    m = _CODE_ARG.match((arg or "").strip())
    return f"AI-{int(m.group(1)):04d}" if m else ""


def _dur(ms: int | None) -> str:
    sec = int((ms or 0) // 1000)
    return f"{sec}s" if sec < 60 else f"{sec // 60}p{sec % 60:02d}"


def _runs_table(runs: list[AgentRun]) -> str:
    """Bảng chữ đều khổ trong <pre>: Telegram không có thẻ bảng, đây là cách duy nhất để cột thẳng
    hàng. Giữ dưới ~32 ký tự một dòng cho khỏi xuống dòng trên điện thoại."""
    rows = [f"{'Giờ':<6}{'Bước':<10}{'KQ':<6}Lâu"]
    for r in runs:
        rows.append(f"{fmt_local(r.started_at, '%H:%M'):<6}{_STAGE_SHORT.get(r.stage, str(r.stage)):<10}"
                    f"{_RUN_SHORT.get(r.status, '?'):<6}{_dur(r.duration_ms)}")
    return "<pre>" + telegram.esc("\n".join(rows)) + "</pre>"


def show_task(db: Session, chat_id: str, arg: str) -> None:
    """/xem <mã>: toàn bộ lịch sử một việc, KỂ CẢ việc đã đóng (/ds chỉ liệt kê việc đang mở)."""
    esc = telegram.esc
    code = _task_code(arg)
    if not code:
        reply(db, chat_id, "Cú pháp: <b>/xem AI-0006</b> (hoặc <b>/xem 6</b>). Việc đang mở thì gõ <b>/ds</b>.")
        return
    task = db.scalar(select(AgentTask).where(AgentTask.code == code))
    if task is None:
        reply(db, chat_id, f"Không có việc <b>{esc(code)}</b> trong sổ.")
        return
    runs = list(db.scalars(select(AgentRun).where(AgentRun.task_id == task.id).order_by(AgentRun.id)))
    msgs = list(db.scalars(select(AgentMessage).where(AgentMessage.task_id == task.id)
                           .order_by(AgentMessage.id)))
    head = [f"<b>{esc(task.code)}</b> · {esc(task.title)}",
            f"Trạng thái: <b>{esc(TASK_STATUS_LABELS.get(task.status, '?'))}</b> · rủi ro "
            f"{esc(RISK_LABELS.get(task.risk_level, '?'))}",
            f"Tạo {fmt_local(task.created_at)}" + (f" · đóng {fmt_local(task.closed_at)}" if task.closed_at else "")]
    if task.note:
        head.append(f"Ghi chú: {esc(task.note[:300])}")
    links = []
    if task.branch_name:
        links.append(f"nhánh <code>{esc(task.branch_name)}</code>")
    if task.pr_url:
        links.append(f'<a href="{esc(task.pr_url)}">PR</a>')
    if merged := coder.merged_sha_for(db, task):
        links.append(f"đã gộp <code>{esc(merged[:10])}</code>")
    if task.deployed_dev_at:
        links.append(f"lên dev {fmt_local(task.deployed_dev_at)}")
    if links:
        head.append(" · ".join(links))
    n_in = sum(1 for m in msgs if m.direction == DIR_IN)
    head.append(f"Tin nhắn: {len(msgs)} ({n_in} của đại ca, {len(msgs) - n_in} của bot)")
    if timing := coder.timing_line(db, task):
        head.append(esc(timing))
    gem = sum(float(r.cost_usd or 0) for r in runs if r.provider != coder.PROVIDER)
    if gem or runs:
        head.append(f"Chi phí Gemini (tiền thật): {_money(gem)} · chi tiết: /chiphi {esc(task.code)}")
    parts = ["\n".join(head)]
    if runs:
        parts.append("<b>Các bước đã chạy</b>\n" + _runs_table(runs))
    #  Phần chữ dài chia nhau chỗ còn lại, theo thứ tự đáng đọc: yêu cầu -> rà soát -> kế hoạch.
    scan = coder.latest_scan_run(db, task)
    scan_text = (scan.artifact or {}).get("message", "") if scan is not None else ""
    blocks = [("Yêu cầu", task.summary or "", False), ("Rà soát mã", scan_text, True),
              ("Kế hoạch cuối", task.plan or "", True)]
    used = sum(len(p) for p in parts) + 40
    for title, body, is_md in blocks:
        if not body.strip():
            continue
        room = min(900, XEM_BUDGET - used - 60)
        if room < 150:
            break
        clipped = body.strip() if len(body.strip()) <= room else body.strip()[:room].rstrip() + "…"
        rendered = _card_md(clipped, limit=room + 400) if is_md else esc(clipped)
        parts.append(f"<b>{title}</b>\n{rendered}")
        used += len(parts[-1]) + 2
    reply(db, chat_id, "\n\n".join(parts), task_id=task.id)


def send_task_list(db: Session, chat_id: str) -> None:
    rows = list(db.scalars(
        select(AgentTask)
        .where(AgentTask.status.not_in(CLOSED_STATUSES))
        .order_by(AgentTask.id.desc())
        .limit(20)
    ))
    if not rows:
        reply(db, chat_id, "Không còn việc nào đang mở.")
        return
    lines = [f"<b>{len(rows)} việc đang mở</b>", ""]
    lines += [
        f"<b>{telegram.esc(t.code)}</b> · {TASK_STATUS_LABELS.get(t.status, '?')} · "
        f"{telegram.esc(t.title)}"
        for t in rows
    ]
    reply(db, chat_id, "\n".join(lines))


# ---------------------------------------------------------------------------
# Ghi sổ
# ---------------------------------------------------------------------------
def reply(db: Session, chat_id: str, text: str, *, task_id: int = 0,
          buttons: list[tuple[str, str]] | None = None,
          markdown: bool = False, action: str = "") -> None:
    """Gửi Telegram VÀ ghi vào sổ (luật F3). Gửi hỏng thì vẫn ghi, kèm lý do.

    `text` mặc định là HTML đã thoát sẵn (các câu của chính bot). `markdown=True` cho
    câu trả lời của Trợ lý AI: gửi bản đã đổi sang HTML, sổ ghi bản Markdown gốc.
    """
    wire = telegram.md_to_html(text) if markdown else text
    if settings.AGENT_TG_COMPACT:
        buttons = None      # ai-CR-027: đại ca ra lệnh bằng chữ, không nút dưới tin nhắn
    try:
        mid = telegram.send(wire, buttons=buttons, chat_id=chat_id)
    except telegram.TelegramError as e:
        log.exception("agent_hub: gửi Telegram hỏng")
        mid, text = 0, f"[KHÔNG GỬI ĐƯỢC: {e}] {text}"
    log_message(db, DIR_OUT, chat_id, mid, text, task_id=task_id, action=action)


def log_message(db: Session, direction: int, chat_id: str, tg_message_id: int,
                body: str, *, action: str = "", task_id: int = 0) -> AgentMessage:
    row = AgentMessage(task_id=task_id, direction=direction, chat_id=chat_id,
                       tg_message_id=tg_message_id, body=body, action=action)
    db.add(row)
    db.flush()
    return row


def start_run(db: Session, task_id: int, stage: int) -> AgentRun:
    run = AgentRun(task_id=task_id, stage=stage, provider="agent_gemini",
                   model=settings.AGENT_MANAGER_MODEL, status=RUN_RUNNING,
                   started_at=datetime.now(), owner_id=user_keys.active_owner())
    db.add(run)
    db.flush()
    return run


def finish_run(db: Session, run: AgentRun, *, result=None, error: str = "") -> None:
    """Đóng một dòng sổ gọi model (luật F4). Không đo thì không biết bot đốt bao nhiêu."""
    run.finished_at = datetime.now()
    run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
    if error:
        run.status = RUN_ERROR
        run.error = error[:2000]
        return
    run.status = RUN_OK
    run.input_tokens = result.input_tokens
    #  Token "suy nghĩ" gộp vào output — Gemini tính giá chúng như output.
    run.output_tokens = result.output_tokens + result.thinking_tokens
    run.model = result.model or run.model
    run.cost_usd = estimate_cost_usd(run.model, run.input_tokens, run.output_tokens)
    run.artifact = {"text": (result.text or "")[:8000]}
