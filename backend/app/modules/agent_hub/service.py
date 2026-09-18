"""Luồng của Agent Hub — nơi Telegram, sổ và bot quản lý gặp nhau.

Một tin nhắn đi qua đây theo hai đường, rẽ ở ngay dòng đầu:

  /hoi <câu>   -> chuyển thẳng cho TRỢ LÝ AI sẵn có, trả lời tại chỗ, KHÔNG tạo task.
  chữ thường   -> ghi vào `tab_agent_message` với `task_id = 0` (đó là hàng đợi INBOX),
                  chờ lặng đủ `AGENT_TRIAGE_DELAY_SEC` rồi một vòng gom biến cả lô
                  thành các task, mỗi task một thẻ Telegram có nút.

Vì sao hai đường trong một bot: hỏi đáp và giao việc là hai nhu cầu khác nhau nhưng
cùng đi qua một cái điện thoại. Tách làm hai bot thì đại ca phải nhớ mình đang chat
với con nào.

BẬC 1 DỪNG Ở PLAN (`TIER1_MAX_STATUS`). Bấm Duyệt là ghi `approved_at` rồi đứng lại —
chưa có bot code nào để gọi.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings

from . import manager, memory, telegram
from .constants import (
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
    ST_NEEDS_INPUT,
    ST_PLAN,
    ST_TRIAGE,
    STAGE_PLAN,
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
def poll_once(db: Session) -> int:
    """Kéo một lượt tin Telegram và xử hết. Trả số update đã đọc."""
    cursor = get_cursor(db)
    updates = telegram.fetch_updates(cursor.value)
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

    log_message(db, DIR_IN, chat_id, int(msg.get("message_id") or 0), text)

    lower = text.lower()
    if lower.startswith("/hoi"):
        answer_question(db, chat_id, text[4:].strip())
    elif lower.startswith("/ds"):
        send_task_list(db, chat_id)
    elif lower.startswith("/gom"):
        n = triage_inbox(db, force=True)
        if not n:
            reply(db, chat_id, "Không có tin nào đang chờ gom.")
    elif lower.startswith("/"):
        reply(db, chat_id,
              "Lệnh: <b>/hoi</b> câu hỏi cho Trợ lý AI · <b>/ds</b> việc đang mở · "
              "<b>/gom</b> gom ngay.\nNhắn chữ thường = giao một việc mới.")
    #  Không phải lệnh thì tin đã nằm ở INBOX với `task_id = 0` rồi — vòng gom lo tiếp.
    #  Cố ý KHÔNG trả lời "đã nhận": mỗi lần đại ca gõ ba câu liền là ba tiếng chuông
    #  vô nghĩa, trong khi thẻ task vài phút nữa mới là thứ đáng đọc.


def handle_callback(db: Session, cb: dict) -> None:
    """Đại ca bấm một nút. `callback_data` dạng `<hành động>:<id task>`."""
    chat_id = str(((cb.get("message") or {}).get("chat") or {}).get("id") or "")
    data = str(cb.get("data") or "")
    cb_id = str(cb.get("id") or "")
    if not telegram.is_allowed_chat(chat_id):
        return

    action, _, raw_id = data.partition(":")
    task = db.get(AgentTask, int(raw_id)) if raw_id.isdigit() else None
    if task is None:
        telegram.answer_callback(cb_id, "Không tìm thấy việc này trong sổ")
        return

    #  Gỡ nút NGAY, trước khi làm gì — đây là chốt chống bấm hai lần, mà lượt PLAN thì
    #  mất vài giây và đại ca rất dễ bấm lại lần nữa trong lúc chờ.
    telegram.clear_buttons(chat_id, int((cb.get("message") or {}).get("message_id") or 0))
    log_message(db, DIR_IN, chat_id, 0, data, action=action, task_id=task.id)

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
        #  Bậc 1 dừng ở đây, và phải NÓI RA. Im lặng thì đại ca ngồi chờ một con bot
        #  code chưa tồn tại.
        reply(db, chat_id,
              f"Đã duyệt <b>{telegram.esc(task.code)}</b> và ghi vào sổ.\n"
              "Bậc 1 dừng ở đây — chưa có bot sửa mã, phần viết mã vẫn là việc tay.",
              task_id=task.id)
    elif action == "fix":
        task.status = ST_NEEDS_INPUT
        telegram.answer_callback(cb_id, "Chờ đại ca nói rõ thêm")
        reply(db, chat_id,
              f"<b>{telegram.esc(task.code)}</b> đang chờ đại ca nói rõ thêm. "
              "Nhắn bổ sung rồi bấm /gom để lập lại kế hoạch.", task_id=task.id)
    elif action == "no":
        task.status = ST_CANCELLED
        task.closed_at = datetime.now()
        task.note = "Đại ca bỏ từ Telegram"
        telegram.answer_callback(cb_id, "Đã bỏ")
    else:
        telegram.answer_callback(cb_id, "Không hiểu nút này")


# ---------------------------------------------------------------------------
# Nhánh /hoi — mượn nguyên Trợ lý AI của ERP
# ---------------------------------------------------------------------------
def answer_question(db: Session, chat_id: str, question: str) -> None:
    """Chuyển câu hỏi cho Trợ lý AI và nhắn lại câu trả lời.

    ⚠️ Trợ lý AI lọc dữ liệu theo NGƯỜI ĐĂNG NHẬP (`apply_scope`), mà Telegram thì
    không đăng nhập. Nên nó chạy dưới đúng một tài khoản ERP khai cứng ở
    `AGENT_ASSISTANT_USER`. Chưa khai thì KHÔNG chạy — chạy mà không có người dùng là
    chạy không phạm vi, tức mở sổ sách cả công ty cho bất kỳ ai tìm ra tên bot.
    """
    if not question:
        reply(db, chat_id, "Cú pháp: <b>/hoi</b> rồi tới câu hỏi.")
        return

    from app.modules.assistant import service as assistant_service
    from app.modules.user.model import User

    email = (settings.AGENT_ASSISTANT_USER or "").strip()
    user = db.scalar(select(User).where(User.email == email)) if email else None
    if user is None or not user.is_active:
        reply(db, chat_id,
              "Chưa khai <code>AGENT_ASSISTANT_USER</code> (email một tài khoản ERP còn "
              "hoạt động) nên em không chạy Trợ lý AI được — nó cần biết hỏi dưới quyền ai.")
        return

    try:
        result = assistant_service.ask(question, db=db, user=user)
    except Exception as e:  # noqa: BLE001 - lỗi nhà cung cấp phải thành câu trả lời
        log.exception("agent_hub: Trợ lý AI hỏng")
        reply(db, chat_id, f"Trợ lý AI lỗi: {telegram.esc(str(e)[:300])}")
        return
    reply(db, chat_id, telegram.esc(result.get("text") or "(không có câu trả lời)"))


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
        send_task_card(db, task)
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
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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
    run = start_run(db, task.id, STAGE_PLAN)
    try:
        data, result = manager.run_plan(task.title, task.summary, docs)
    except Exception as e:  # noqa: BLE001
        finish_run(db, run, error=str(e))
        db.commit()
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
              f"Lập kế hoạch cho <b>{telegram.esc(task.code)}</b> lỗi: "
              f"{telegram.esc(str(e)[:300])}", task_id=task.id)
        return
    finish_run(db, run, result=result)

    task.plan = data["plan"]
    task.plan_files = data["plan_files"]
    task.test_plan = data["test_plan"]
    task.related_docs = data["related_docs"]
    task.questions = data["questions"]
    task.risk_level = data["risk_level"]
    #  `plan_files` rỗng = bot không viết nổi phạm vi cụ thể = CẤM đi tiếp (luật B2).
    #  Đây là chỗ thi hành luật đó, không phải câu nhắc gửi cho model.
    task.status = ST_NEEDS_INPUT if data["needs_clarification"] else ST_PLAN
    db.commit()
    send_plan_card(db, task)
    db.commit()


# ---------------------------------------------------------------------------
# Thẻ Telegram
# ---------------------------------------------------------------------------
def send_task_card(db: Session, task: AgentTask) -> None:
    lines = [
        f"<b>{telegram.esc(task.code)}</b> · {telegram.esc(task.title)}",
        "",
        telegram.esc(task.summary),
    ]
    if task.risk_level == RISK_HIGH:
        lines += ["", "<b>Rủi ro CAO</b> — đụng tiền, phân quyền, cấu trúc DB hoặc nhánh main."]
    n_items = db.scalar(
        select(func.count(AgentTaskItem.id)).where(AgentTaskItem.task_id == task.id)
    ) or 0
    if n_items > 1:
        lines += ["", f"Gom từ {n_items} tin nhắn."]
    reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join(lines), task_id=task.id,
          buttons=[("Lập kế hoạch", f"plan:{task.id}"), ("Bỏ việc này", f"no:{task.id}")])


def send_plan_card(db: Session, task: AgentTask) -> None:
    lines = [f"<b>{telegram.esc(task.code)}</b> · {telegram.esc(task.title)}", ""]
    if task.questions:
        lines += ["<b>Bot chưa đủ thông tin, đang hỏi lại:</b>"]
        lines += [f"• {telegram.esc(q)}" for q in task.questions]
        lines += ["", "Nhắn trả lời rồi bấm /gom để lập lại kế hoạch."]
        reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join(lines), task_id=task.id)
        return

    lines += [telegram.esc(task.plan), ""]
    lines += ["<b>Tệp sẽ đụng:</b>"] + [f"• <code>{telegram.esc(f)}</code>" for f in task.plan_files]
    if task.test_plan:
        lines += ["", "<b>Kiểm thử:</b>", telegram.esc(task.test_plan)]
    if task.related_docs:
        lines += ["", "<b>Tài liệu đã tra:</b>"]
        lines += [f"• <code>{telegram.esc(d['path'])}</code>" for d in task.related_docs]
    lines += ["", f"Rủi ro: <b>{RISK_LABELS.get(task.risk_level, '?')}</b>"]
    reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join(lines), task_id=task.id,
          buttons=[("Duyệt", f"ok:{task.id}"), ("Sửa lại", f"fix:{task.id}"),
                   ("Bỏ việc này", f"no:{task.id}")])


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
          buttons: list[tuple[str, str]] | None = None) -> None:
    """Gửi Telegram VÀ ghi vào sổ (luật F3). Gửi hỏng thì vẫn ghi, kèm lý do."""
    try:
        mid = telegram.send(text, buttons=buttons, chat_id=chat_id)
    except telegram.TelegramError as e:
        log.exception("agent_hub: gửi Telegram hỏng")
        mid, text = 0, f"[KHÔNG GỬI ĐƯỢC: {e}] {text}"
    log_message(db, DIR_OUT, chat_id, mid, text, task_id=task_id)


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
