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
import json
import logging
import re
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings

from . import coder, manager, memory, playbook, telegram
from .timeutil import fmt_local, now_local, to_utc
from .constants import (
    ACT_ANSWER,
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
    ACT_WAIT_DEPLOY_TIME,
    ACT_WAIT_PATCH_Q,
    ACT_WAIT_PLAN_ANSWER,
    BOT_NAME,
    BOT_PERSONA,
    CLOSED_STATUSES,
    DIR_IN,
    DIR_OUT,
    MERGED_BY_BOT,
    RISK_HIGH,
    RISK_LABELS,
    RUN_ERROR,
    RUN_OK,
    RUN_RUNNING,
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
    STAGE_SCAN,
    STAGE_TRIAGE,
    TASK_STATUS_LABELS,
    estimate_cost_usd,
)
from .model import AgentCursor, AgentMessage, AgentRun, AgentTask, AgentTaskItem

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
    cursor = get_cursor(db)
    updates = telegram.fetch_updates(cursor.value, timeout=timeout)
    if not updates:
        return 0

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
    chat_id = str((msg.get("chat") or {}).get("id") or "")
    text = (msg.get("text") or "").strip()
    if not text:
        return
    if not telegram.is_allowed_chat(chat_id):
        #  Không trả lời gì cả. Trả lời "bạn không có quyền" là xác nhận cho người lạ
        #  rằng bot này sống và có chủ.
        log.warning("agent_hub: bỏ tin từ chat lạ %s", chat_id)
        return

    row = log_message(db, DIR_IN, chat_id, int(msg.get("message_id") or 0), text)
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

    _route_plain_text(db, chat_id, row, text)


def _run_command(db: Session, chat_id: str, text: str) -> None:
    """Các lệnh `/` — nay chỉ là ĐƯỜNG TẮT cho ai quen gõ, không còn bắt buộc."""
    lower = text.lower()
    if lower.startswith("/hoi"):
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
              f"Em là <b>{BOT_NAME}</b>. "
              "Cứ nhắn bình thường, em tự hiểu: <b>hỏi</b> hay <b>nhờ làm việc gì</b> "
              "trên hệ thống thì em làm ngay, <b>nhờ sửa phần mềm</b> thì em ghi thành việc.\n"
              "Đường tắt nếu muốn chắc: <b>/hoi</b> ép trả lời · <b>/ds</b> việc đang mở · "
              "<b>/xem AI-0006</b> lịch sử một việc, kể cả việc đã đóng · <b>/gom</b> gom ngay.")


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
    #  Trạm kế hoạch vừa hỏi lại (ai-CR-015): tin kế là câu trả lời CỦA VIỆC ĐÓ, không phải việc mới.
    if task_id := _plan_answer_target(db, chat_id, row):
        _answer_plan(db, chat_id, row, text, task_id)
        return

    if _is_follow_up(db, chat_id, row):
        row.action = ACT_ASKED
        answer_question(db, chat_id, text, before_id=row.id)
        return

    run = start_run(db, 0, STAGE_INTENT)
    try:
        data, result = manager.run_intent(text, context=_intent_context(db, chat_id, row.id))
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
    #  GIAO VIỆC: để `action` rỗng, tin nằm lại INBOX và vòng gom lo tiếp. Cố ý KHÔNG
    #  trả lời "đã nhận": gõ ba câu liền là ba tiếng chuông vô nghĩa, trong khi thẻ
    #  task vài phút nữa mới là thứ đáng đọc.


def _ask_intent_choice(db: Session, chat_id: str, row: AgentMessage) -> None:
    """Không đoán được thì đóng dấu chờ và đưa đại ca hai nút."""
    row.action = ACT_WAIT_CHOICE
    reply(db, chat_id,
          "Em chưa chắc đại ca đang nhờ em làm ngay hay nhờ sửa phần mềm. Đại ca chọn giúp:",
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
        .where(AgentMessage.chat_id == chat_id, AgentMessage.id < row.id)
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


def _dispatch_deploy(db: Session, chat_id: str, cb_id: str, task: AgentTask) -> None:
    """Nút «Đồng ý»: ghi dòng sổ rồi giao runner. Đây là lần DUY NHẤT lệnh gộp được phát."""
    code = telegram.esc(task.code)
    if blocked := _deploy_blocker(db, task):
        telegram.answer_callback(cb_id, "Chưa gộp được, xem lý do")
        reply(db, chat_id, f"<b>{code}</b>: {telegram.esc(blocked)}", task_id=task.id)
        return
    run = _new_deploy_run(db, task, STAGE_DEPLOY, "ngay", approved_by=chat_id)
    try:
        coder.dispatch_deploy(task.id, run.id)
    except Exception as e:  # noqa: BLE001 — broker chết thì đóng lượt, nút bấm lại được
        log.exception("agent_hub: giao việc gộp + deploy hỏng")
        coder._close_run(run, status=RUN_ERROR, error=str(e)[:500])
        db.commit()
        reply(db, chat_id, f"<b>{code}</b>: không giao được cho runner: {telegram.esc(str(e)[:300])}",
              task_id=task.id, buttons=[("Gộp erp-v2 + deploy dev", f"mg:{task.id}")])
        return
    telegram.answer_callback(cb_id, "Đang gộp + deploy dev…")
    reply(db, chat_id, f"<b>{code}</b>: đang gộp vào <code>{telegram.esc(settings.AGENT_BASE_BRANCH)}"
          "</code> và deploy dev, thường 5-12 phút. Xong em gửi thẻ.", task_id=task.id)


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
        .where(AgentMessage.chat_id == chat_id, AgentMessage.id < row.id)
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
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
              f"Tới giờ hẹn {fmt_local(when, '%H:%M')}: em bắt đầu gộp <b>{telegram.esc(task.code)}</b> vào "
              f"<code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code> + deploy dev.", task_id=task.id)
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
               AgentMessage.id > wait.id, AgentMessage.id < row.id)
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
        reply(db, chat_id, f"Câu này dính {esc(topic or 'việc rủi ro cao')} nên lần sau gặp em vẫn "
              "hỏi, không đề xuất ghi vào sổ quyết định.", task_id=task.id)
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
        task.approved_by_chat = chat_id
        task.approved_at = datetime.now()
        telegram.answer_callback(cb_id, "Đã duyệt")
        _dispatch_coder(db, chat_id, task)
    elif action == "fix":
        task.status = ST_NEEDS_INPUT
        task.questions = []
        telegram.answer_callback(cb_id, "Chờ đại ca nói rõ thêm")
        _invite_plan_answer(db, chat_id, task)
    elif action == "no":
        task.status = ST_CANCELLED
        task.closed_at = datetime.now()
        task.note = "Đại ca bỏ từ Telegram"
        telegram.answer_callback(cb_id, "Đã bỏ")
        #  Chỉ có toast thì khung chat không còn dấu vết gì (đại ca hỏi 23/09 về AI-0006).
        reply(db, chat_id, f"Đã bỏ <b>{telegram.esc(task.code)}</b> · {telegram.esc(task.title)}. "
              f"Lịch sử vẫn còn trong sổ: /xem {telegram.esc(task.code)}", task_id=task.id)
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
        #  Đại ca thử trên dev thấy ổn. Prod đang tạm dừng deploy (chốt 19/09/2026) nên «xong»
        #  ở đây là xong việc của bot; lên prod là chuyện của người, ghi ở sổ khác.
        task.status = ST_DONE
        task.closed_at = datetime.now()
        task.note = (task.note + "\n" if task.note else "") + "Đại ca xác nhận xong trên dev (Telegram)"
        telegram.answer_callback(cb_id, "Đã đóng việc")
        reply(db, chat_id, f"<b>{telegram.esc(task.code)}</b>: đã đóng. Bản gộp ở trên "
              f"<code>{telegram.esc(settings.AGENT_BASE_BRANCH)}</code>, lên prod là đợt riêng.",
              task_id=task.id)
    else:
        telegram.answer_callback(cb_id, "Không hiểu nút này")


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
        reply(db, chat_id, "Rồi, em ghi vào sổ chờ. Lát nữa gom xong em gửi thẻ việc.")


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

    user = _assistant_user(db)
    if user is None:
        reply(db, chat_id, _NO_ASSISTANT_USER)
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
        result = assistant_service.ask(question, db=db, user=user, history=history,
                                       system=BOT_PERSONA)
    except Exception as e:  # noqa: BLE001 - lỗi nhà cung cấp phải thành câu trả lời
        log.exception("agent_hub: Trợ lý AI hỏng")
        reply(db, chat_id, f"{BOT_NAME} chưa trả lời được: {telegram.esc(str(e)[:300])}")
        return
    #  Trợ lý AI trả Markdown (web render bằng react-markdown). Gửi qua bộ đổi sang HTML
    #  Telegram, còn sổ giữ nguyên Markdown để lượt sau đưa lại cho model đúng như web.
    reply(db, chat_id, result.get("text") or "(không có câu trả lời)",
          markdown=True, action=ACT_ANSWER)
    deliver_tool_results(db, chat_id, user, result.get("tool_calls") or [])


_NO_ASSISTANT_USER = (
    "Chưa khai <code>AGENT_ASSISTANT_USER</code> (email một tài khoản ERP còn hoạt động) "
    "nên em không chạy Trợ lý AI được — nó cần biết hỏi dưới quyền ai."
)


def _assistant_user(db: Session):
    """Tài khoản ERP mà bot mượn để chạy Trợ lý AI (`QĐ-AI-10`). None = chưa khai / đã khóa."""
    from app.modules.user.model import User

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
            reply(db, chat_id,
                  "Trợ lý đã soạn nháp phiếu, nhưng form soạn nháp chỉ mở được trên web. "
                  f"Đại ca mở Trợ lý AI ở <a href=\"{telegram.esc(telegram.absolute_url('/assistant'))}\">"
                  "ERP</a> và hỏi lại câu này để nhận nút mở form.")


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

    user = _assistant_user(db)
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
    for mid in group["message_ids"]:
        db.add(AgentTaskItem(task_id=task.id, source=SRC_TELEGRAM, ref_id=mid,
                             merged_by=MERGED_BY_BOT))
        #  Gắn tin vào task = rút nó khỏi INBOX. Quên bước này thì lượt gom sau lại
        #  nhặt đúng mấy tin đó và đẻ ra task trùng.
        by_id[mid].task_id = task.id
    return task


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
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
              f"Lập kế hoạch cho <b>{telegram.esc(task.code)}</b> lỗi: "
              f"{telegram.esc(str(e)[:300])}", task_id=task.id)
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
    if assumptions and (strict or task.risk_level >= RISK_HIGH):
        #  Model tự giả định trên một việc rủi ro cao (kể cả khi chính lượt này mới nâng mức):
        #  luật 3 nói việc đó luôn hỏi, nên mọi giả định thành câu hỏi. Thi hành ở mã, không nhờ lời nhắc.
        task.questions = list(task.questions or []) + [
            f"Em định làm thế này, đại ca xác nhận giúp: {a}" for a in assumptions]
        needs = True
    elif assumptions:
        #  Ghi vào chính bản kế hoạch: thẻ duyệt hiện ra, và runner đọc lại y nguyên trong đề bài.
        task.plan = (task.plan or "").rstrip() + "\n\n**Em tự quyết, không hỏi lại:**\n" + \
            "\n".join(f"- {a}" for a in assumptions)
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
                      "hoạch luôn. Trả lời trễ hơn thì bấm «Trả lời câu hỏi» trước."]
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join(lines), task_id=task.id,
              action=ACT_WAIT_PLAN_ANSWER,
              buttons=[("Trả lời câu hỏi", f"ans:{task.id}"), ("Bỏ việc này", f"no:{task.id}")])
        return

    #  Kế hoạch do model viết là Markdown (`tệp`, **đậm**, 1. 2.): đổi sang HTML Telegram như
    #  câu trả lời của Trợ lý AI, không in thô dấu nháy và dấu sao (đại ca báo 23/09/2026).
    lines += [_card_md(task.plan), ""]
    lines += ["<b>Tệp sẽ đụng:</b>"] + [f"• <code>{telegram.esc(f)}</code>" for f in task.plan_files]
    if task.test_plan:
        lines += ["", "<b>Kiểm thử:</b>", _card_md(task.test_plan)]
    if task.related_docs:
        lines += ["", "<b>Tài liệu đã tra:</b>"]
        lines += [f"• <code>{telegram.esc(d['path'])}</code>" for d in task.related_docs]
    lines += ["", f"Rủi ro: <b>{RISK_LABELS.get(task.risk_level, '?')}</b>"]
    if task.risk_level == RISK_HIGH:
        lines += ["Đụng tiền, phân quyền, cấu trúc DB hoặc nhánh main — đọc kỹ trước khi duyệt."]
    #  Thẻ kế hoạch nay là thẻ DUY NHẤT của một việc, nên phải nói rõ nó gom từ mấy tin,
    #  không thì đại ca tưởng bot bỏ sót mấy tin kia.
    n_items = db.scalar(
        select(func.count(AgentTaskItem.id)).where(AgentTaskItem.task_id == task.id)
    ) or 0
    if n_items > 1:
        lines += [f"Gom từ {n_items} tin nhắn."]
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
                   started_at=datetime.now())
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
