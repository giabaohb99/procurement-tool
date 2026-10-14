"""Lõi hội thoại mới của bot (ai-CR-198, doc/agent-hub/20 — đại ca chốt 14/10/2026: «đập đi xây lại… ổn định và con
người hơn»).

Một tin chữ vào = MỘT vòng tác tử: model nhìn thấy ngày giờ, người đang nhắn, sổ nhớ, VIỆC ĐANG DỞ (nháp, kế hoạch đang
hỏi, hoàn tác chờ, vé sửa mã) và 30–40 lượt gần nhất; tự quyết hỏi lại, gợi ý, gọi công cụ nhiều vòng, hay ghi. Không
còn regex làm cổng chính, không còn bước đọc ý định, không cắt sau khi soạn nháp.

Chạy song song với đường cũ dưới cờ `AGENT_CORE_V2_ENABLED` (+ `AGENT_CORE_V2_CHATS` để bật theo từng chat thử).
Đường cũ không đụng: `service.py` chỉ rẽ ở hai chỗ gọi `_route_*_text`. Mọi thứ ghi xuống ERP vẫn đi qua các công cụ
và `erp.py` (cổng B) như cũ — lõi mới chỉ thay cách NÓI CHUYỆN và cách QUYẾT ĐỊNH.

Bước B1 (tệp này): vòng tác tử + ngữ cảnh đủ + prompt phong cách + ba công cụ nháp (`update_draft`, `commit_draft`,
`drop_draft`) + đo lượt. B2 dời kế hoạch việc / hoàn tác / sửa mã lên lõi; B3 phase 24 phía sếp (doc 20 §6).
"""
from __future__ import annotations

import json
import logging
import time
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.assistant.provider.base import ToolDef

from . import erp, manager, telegram, user_keys
from .constants import (ACT_ANSWER, ACT_ASKED, ACT_DRAFT_WAIT, ACT_PLAN_ASK_WAIT, ACT_UNDO_WAIT, DIR_IN, SRC_TELEGRAM,
                        ST_DONE, STAGE_ANSWER)
from .model import AgentMessage, AgentTask, AgentTaskItem
from .timeutil import fmt_local, now_local

log = logging.getLogger("app.agent_hub.core_v2")

HISTORY_WINDOW = timedelta(hours=24)
#  14/10 lượt #206: «hello em» nạp 39.211 token vì 17 lượt lịch sử chứa nguyên các bản tra giá dài (vàng, bitcoin)
#  → trạm không có prompt caching nên mỗi lượt đọc lại hết, chờ ~7 s. Nay mỗi tin cũ cắt ngắn, tổng trần 12k ký tự;
#  câu xã giao chỉ mang 6 lượt.
HISTORY_MAX_CHARS = 12_000
HISTORY_MSG_CHARS = 900
SMALLTALK_TURNS = 6
DRAFT_WINDOW = timedelta(minutes=15)
PLAN_WAIT_WINDOW = timedelta(hours=48)
MAX_ITERS = 6
MAX_TOKENS = 1500
TEMPERATURE = 0.4

#  Mười hai hành vi «con người» của doc 20 §3b, viết thành lời dặn. Ngắn, không câu mẫu, không emoji.
STYLE_RULES = (
    "CÁCH NÓI CHUYỆN (bắt buộc):\n"
    "- Nói tiếng Việt tự nhiên như một trợ lý người thật đã biết việc; câu ngắn; 1–2 ý thì viết thành câu, không gạch "
    "đầu dòng; KHÔNG dùng emoji, KHÔNG lặp câu mẫu, KHÔNG mở đầu bằng «Chào anh/chị» ở mỗi câu.\n"
    "- Thiếu thông tin quan trọng (dự án nào, giao ai, hạn, số tiền, loại phiếu…) thì HỎI LẠI đúng cái thiếu, tối đa 2 "
    "câu hỏi, kèm 2–3 lựa chọn gợi ý lấy từ dữ liệu thật (tra công cụ trước nếu cần). Không đoán bừa, không ra nháp rỗng.\n"
    "- Người dùng sửa bằng lời («đổi hạn thứ năm», «giao Giang thay Được», «bỏ việc 2») thì gọi update_draft, đừng bắt "
    "họ gõ lại từ đầu.\n"
    "- Hiểu đồng ý / không đồng ý theo MỌI cách nói, kể cả sai chính tả, viết tắt, nói vòng («ok», «được đó», «tao task "
    "đó giúp anh», «chốt» = đồng ý; «khoan», «thôi», «để anh xem» = chưa). Đồng ý thì gọi commit_draft; chưa thì giữ nháp.\n"
    "- Trước khi ghi việc lớn (kế hoạch nhiều việc, xóa, gửi duyệt) nhắc lại ngắn cái sắp ghi: «Em hiểu là… đúng không?»\n"
    "- Xong một việc thì gợi ĐÚNG MỘT bước kế hợp lý («em báo anh Được luôn nhé?»); không hỏi han thừa.\n"
    "- Không biết hay công cụ lỗi thì nói thật nguyên nhân một câu và cách khác; không bịa số liệu, không bịa trạng thái.\n"
    "- Không bắt người dùng nhớ cú pháp lệnh; chỉ nhắc lệnh khi họ hỏi cách dùng.\n"
    "- Gọi người đang nhắn theo cách xưng hô ở mục NGƯỜI ĐANG NHẮN (tên, anh/chị), không dùng «anh/chị» chung chung khi "
    "đã biết tên.\n"
    "- Ngày tháng trong mọi nháp phải tính từ HÔM NAY ở mục THỜI ĐIỂM (năm hiện tại), viết dạng YYYY-MM-DD."
)

#  Bản gọn của policy.ASSISTANT_RULES (3,7k ký tự) cho lõi mới: giữ luật an toàn + phạm vi trợ lý cá nhân, bỏ phần dặn
#  dùng từng công cụ (đã nằm trong mô tả công cụ). Bản cũ còn mâu thuẫn với STYLE_RULES («làm luôn, hỏi tối đa MỘT câu»
#  so với «thiếu thì hỏi lại kèm gợi ý») — model nhận hai luật ngược nhau là lý do hay trả lời lúc thế này lúc thế khác.
CORE_RULES = (
    "PHẠM VI VÀ AN TOÀN:\n"
    "- Bạn là trợ lý CÁ NHÂN của người đang nhắn, không chỉ trợ lý ERP: việc làm được bằng chữ (lịch trình, kế hoạch, "
    "gợi ý, soạn thảo, tính toán) thì làm ngay trong câu trả lời; công cụ chỉ để đọc/ghi ERP, Google, tìm trên mạng. "
    "Không bao giờ gợi ý phiếu ERP cho nhu cầu cá nhân.\n"
    "- Đủ rõ thì làm luôn; mơ hồ nhẹ thì chọn cách hợp lý nhất và nói rõ giả định. Câu phụ thuộc nơi đang ở (quán, "
    "đường, thời tiết) mà chưa biết khu thì hỏi khu trước.\n"
    "- Chỉ nói «đã làm» khi công cụ trả thành công; không có công cụ đúng việc thì nói thẳng chưa làm được, không dùng "
    "công cụ khác làm thay. Công cụ báo thiếu quyền thì nói thiếu quyền gì và gợi ý nhắn «quyền của tôi».\n"
    "- Không bao giờ bảo người dùng gõ SQL, lệnh máy chủ hay mã nguồn. Không ghi mật khẩu, khóa, số thẻ vào sổ nhớ.\n"
    "- Sổ nhớ: theo đúng khối sổ ghi nhớ riêng (kể cả xưng hô); nghe điều ỔN ĐỊNH về họ thì remember_fact và thêm một "
    "dòng «Em ghi nhớ: …»; họ bảo quên thì forget_fact; nhắc chuyện cũ thì search_notes / search_chat_history trước."
)

DRAFT_FACTS = (
    "NHÁP CHỨNG TỪ / VIỆC: công cụ draft_* trả về bản nháp, bot tự gửi thẻ tóm tắt cho người dùng ngay sau câu trả lời "
    "của bạn — bạn chỉ nói ngắn là đã soạn và hỏi họ có muốn đổi gì không. Nháp đang chờ nằm ở mục ĐANG DỞ. Người dùng "
    "đồng ý → commit_draft (submit=true nếu họ bảo gửi duyệt luôn); muốn sửa → update_draft với đúng ô cần đổi; thôi → "
    "drop_draft. Mọi chữ tiếng Việt điền vào nháp phải CÓ DẤU đầy đủ."
)

LOCAL_TOOLS: tuple[ToolDef, ...] = (
    ToolDef(name="update_draft",
            description="Sửa bản nháp đang chờ của chat này (nháp mới nhất trong 15 phút) theo lời người dùng, rồi gửi "
                        "lại thẻ. Chỉ truyền các ô cần đổi; ô không nhắc thì giữ nguyên.",
            parameters={"type": "object",
                        "properties": {"changes": {"type": "object", "description": "Các ô của nháp cần đổi, "
                                                                                       "ví dụ {\"due_date\": \"2026-10-16\", \"assignee\": \"Nguyễn Văn A\"}"}},
                        "required": ["changes"]}),
    ToolDef(name="commit_draft",
            description="Người dùng đã đồng ý: tạo thật bản nháp đang chờ (lưu Nháp trên ERP). submit=true khi họ muốn "
                        "gửi duyệt luôn.",
            parameters={"type": "object", "properties": {"submit": {"type": "boolean"}}, "required": []}),
    ToolDef(name="drop_draft",
            description="Người dùng không muốn tạo nữa: bỏ bản nháp đang chờ.",
            parameters={"type": "object", "properties": {}, "required": []}),
)
LOCAL_TOOL_NAMES = frozenset(t.name for t in LOCAL_TOOLS)


# ---------------------------------------------------------------------------
# Cờ bật
# ---------------------------------------------------------------------------
def _is_smalltalk(text: str) -> bool:
    from app.modules.assistant import tool_router

    return tool_router.is_smalltalk(text)


def enabled_for(chat_id: str) -> bool:
    if not settings.AGENT_CORE_V2_ENABLED:
        return False
    chats = {c.strip() for c in str(settings.AGENT_CORE_V2_CHATS or "").split(",") if c.strip()}
    return not chats or str(chat_id).strip() in chats


# ---------------------------------------------------------------------------
# Ngữ cảnh
# ---------------------------------------------------------------------------
def _pending_draft(db: Session, chat_id: str, before_id: int, now) -> tuple[AgentMessage | None, dict]:
    row = db.scalar(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_DRAFT_WAIT,
                                               AgentMessage.id < before_id).order_by(AgentMessage.id.desc()).limit(1))
    if row is None or (now and row.created_at and now - row.created_at > DRAFT_WINDOW):
        return None, {}
    try:
        return row, json.loads(row.body or "{}")
    except ValueError:
        return row, {}


def _open_code_tasks(db: Session, chat_id: str) -> list[AgentTask]:
    """Vé sửa mã (AI-000x) do chính chat này gửi, còn mở."""
    q = (select(AgentTask).join(AgentTaskItem, AgentTaskItem.task_id == AgentTask.id)
         .join(AgentMessage, AgentMessage.id == AgentTaskItem.ref_id)
         .where(AgentMessage.chat_id == chat_id, AgentTaskItem.source == SRC_TELEGRAM, AgentTask.status < ST_DONE)
         .order_by(AgentTask.id.desc()).limit(5))
    seen, out = set(), []
    for t in db.scalars(q):
        if t.id not in seen:
            seen.add(t.id)
            out.append(t)
    return out


def pending_block(db: Session, chat_id: str, before_id: int, now) -> str:
    """Khối ĐANG DỞ — thứ model phải nhìn thấy để không trả lời «không có dấu vết» như hôm 14/10."""
    from . import draft_create, service

    lines: list[str] = []
    pending, info = _pending_draft(db, chat_id, before_id, now)
    if pending is not None:
        label = draft_create.LABELS.get(str(info.get("kind") or ""), "phiếu")
        draft = info.get("draft") or {}
        age = int((now - pending.created_at).total_seconds() // 60) if now and pending.created_at else 0
        lines.append(f"- Nháp {label} đang chờ người dùng quyết (soạn {age} phút trước): "
                     f"{json.dumps(draft, ensure_ascii=False, default=str)[:900]}")
    waits = db.scalars(select(AgentMessage).where(AgentMessage.chat_id == chat_id,
                                                  AgentMessage.action == ACT_PLAN_ASK_WAIT, AgentMessage.id < before_id)
                       .order_by(AgentMessage.id.desc()).limit(3))
    for w in waits:
        if now and w.created_at and now - w.created_at > PLAN_WAIT_WINDOW:
            continue
        try:
            body = json.loads(w.body or "{}")
        except ValueError:
            body = {}
        lines.append(f"- Việc kế hoạch #{body.get('task_id')} đang chờ người dùng nhắn giờ làm / lý do "
                     f"({body.get('kind') or 'phản hồi'}).")
    undo = db.scalar(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_UNDO_WAIT,
                                                AgentMessage.id < before_id).order_by(AgentMessage.id.desc()).limit(1))
    if undo is not None and now and undo.created_at and now - undo.created_at <= DRAFT_WINDOW:
        lines.append("- Đang chờ người dùng xác nhận một lệnh hoàn tác («đúng» / «thôi»).")
    for t in _open_code_tasks(db, chat_id):
        try:
            lines.append(f"- Vé sửa phần mềm {t.code}: {service.task_status_line(db, t)[:300]}")
        except Exception:  # noqa: BLE001
            lines.append(f"- Vé sửa phần mềm {t.code}: {t.title[:120]}")
    return "ĐANG DỞ (việc chưa khép của cuộc này):\n" + ("\n".join(lines) if lines else "- (không có)")


def history(db: Session, chat_id: str, before_id: int, now, *, smalltalk: bool = False) -> list[dict]:
    """Tối đa 40 lượt trong 24 giờ, mỗi tin cắt còn HISTORY_MSG_CHARS, tổng trần HISTORY_MAX_CHARS (doc 20 §3.3).
    Chỉ lấy hỏi / trả lời / nghiên cứu."""
    from . import service

    turns_max = SMALLTALK_TURNS if smalltalk else max(4, int(settings.AGENT_CORE_V2_HISTORY_TURNS or 40))
    q = (select(AgentMessage)
         .where(AgentMessage.chat_id == chat_id,
                AgentMessage.action.in_((ACT_ASKED, ACT_ANSWER, service.ACT_RESEARCH)),
                AgentMessage.id < before_id)
         .order_by(AgentMessage.id.desc()).limit(turns_max * 2))
    turns: list[dict] = []
    total = 0
    for r in db.scalars(q):
        if now and r.created_at and now - r.created_at > HISTORY_WINDOW:
            break
        body = r.body or ""
        if len(body) > HISTORY_MSG_CHARS:
            body = body[:HISTORY_MSG_CHARS] + " …(đã rút gọn)"
        total += len(body)
        if total > HISTORY_MAX_CHARS:
            break
        turns.append({"role": "user" if r.direction == DIR_IN else "assistant", "content": body})
    turns.reverse()
    return turns


def build_system(db: Session, chat_id: str, row: AgentMessage, user, text: str) -> str:
    from . import intent_ledger, personal_memory, service
    from .constants import BOT_LOGIN_FACTS

    now = now_local()
    name, role = "", ""
    try:
        name, role = erp.describe(db, user)
    except Exception:  # noqa: BLE001
        pass
    who = f"NGƯỜI ĐANG NHẮN: {name or 'người dùng ERP'}" + (f" — {role}" if role else "")
    who += ("; đây là chat CHỦ BOT (đại ca)." if telegram.is_allowed_chat(chat_id) else
            "; gọi theo tên hoặc anh/chị, KHÔNG gọi «đại ca».")
    parts = [
        service._persona(chat_id),
        STYLE_RULES,
        f"THỜI ĐIỂM: bây giờ là {fmt_local(now, '%H:%M, %A %d/%m/%Y')} (giờ Việt Nam). Năm hiện tại là {now.year}.",
        who,
        CORE_RULES,
        DRAFT_FACTS,
        BOT_LOGIN_FACTS,
        pending_block(db, chat_id, row.id, row.created_at),
    ]
    for fn in (lambda: erp.caller_context(db, user), lambda: erp.glossary_block(db, [text]),
               #  Tìm ghi chú theo câu hỏi tốn ~1,8 s (gọi nhúng véc-tơ) — câu xã giao chỉ cần phần lõi sổ nhớ.
               (lambda: personal_memory.load_core(db, user.id)) if _is_smalltalk(text)
               else (lambda: personal_memory.prompt_block(db, user.id, text)),
               lambda: intent_ledger.habit_block(db, user.id)):
        try:
            block = fn()
        except Exception:  # noqa: BLE001
            block = ""
        if block:
            parts.append(str(block))
    return "\n\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Công cụ
# ---------------------------------------------------------------------------
def select_tools(db: Session, user, text: str) -> list[ToolDef]:
    """Công cụ ERP theo nhóm của câu (tool_router, ai-CR-183/192) + công cụ nháp của lõi."""
    from app.modules.assistant import tool_router

    #  Câu xã giao («hello em», «cảm ơn») không cần 70+ công cụ ERP — hôm 14/10 «hello em» nạp 76 công cụ.
    if tool_router.is_smalltalk(text):
        return list(LOCAL_TOOLS)
    try:
        defs = list(erp.tool_defs(db, user) or [])
    except Exception:  # noqa: BLE001
        log.exception("core_v2: không lấy được bộ công cụ ERP")
        defs = []
    try:
        picked = tool_router.select(text, tool_router.recent_tools(db, getattr(user, "id", 0)))
    except Exception:  # noqa: BLE001
        picked = None
    if picked is not None:
        keep = set(picked) | set(tool_router.CORE)
        defs = [d for d in defs if d.name in keep]
    names = {d.name for d in defs}
    return defs + [t for t in LOCAL_TOOLS if t.name not in names]


def _run_local(db: Session, chat_id: str, row: AgentMessage, user, name: str, args: dict) -> dict:
    """Ba công cụ nháp của lõi: dùng lại nguyên đường «tạo» / «thôi» của service để không lệch luật (quyền, gửi duyệt,
    hỏi nhận việc sau kế hoạch…)."""
    from . import service

    now = row.created_at
    if name == "update_draft":
        pending, info = _pending_draft(db, chat_id, row.id, now)
        if pending is None:
            return {"error": "Không còn bản nháp nào đang chờ (quá 15 phút hoặc chưa soạn). Soạn lại bằng công cụ draft_*."}
        changes = args.get("changes") if isinstance(args.get("changes"), dict) else {}
        if not changes:
            return {"error": "Chưa có ô nào cần đổi."}
        draft = dict(info.get("draft") or {})
        draft.update(changes)
        service._offer_draft(db, chat_id, user, {"name": info.get("tool") or "", "draft": draft})
        return {"ok": True, "draft": draft, "note": "Đã gửi lại thẻ nháp mới cho người dùng; không cần lặp lại nội dung."}
    if name in ("commit_draft", "drop_draft"):
        pending, info = _pending_draft(db, chat_id, row.id, now)
        if pending is None:
            return {"error": "Không còn bản nháp nào đang chờ."}
        phrase = "thôi" if name == "drop_draft" else ("tạo và gửi duyệt" if args.get("submit") else "tạo")
        ok = bool(service._draft_by_text(db, chat_id, row, phrase))
        row.action = ACT_ASKED                       # _draft_by_text đổi thành lệnh; giữ mạch hội thoại
        db.commit()
        if not ok:
            return {"error": "Không ghi được nháp (có thể đã hết hạn)."}
        done = {"ok": True}
        if name == "commit_draft":
            try:
                created = (json.loads(db.get(AgentMessage, pending.id).body or "{}") or {}).get("created") or {}
            except Exception:  # noqa: BLE001
                created = {}
            done.update({"created": created, "note": "Bot đã tự báo kết quả tạo cho người dùng; bạn chỉ cần một câu ngắn, "
                                                     "không lặp lại mã phiếu."})
        else:
            done["note"] = "Bot đã báo «không tạo»; bạn chỉ cần một câu ngắn."
        return done
    return {"error": f"Công cụ lạ {name}"}


# ---------------------------------------------------------------------------
# Vòng tác tử
# ---------------------------------------------------------------------------
def handle(db: Session, chat_id: str, row: AgentMessage, text: str) -> None:
    from app.modules.assistant.provider.base import ChatMessage

    from . import service

    #  Đường cũ ghi tin chủ bot với action="" (để gom việc). Lõi mới KHÔNG gom việc từ tin thường → đóng dấu «hỏi» ngay,
    #  kẻo _triage_inbox biến mỗi câu chào thành một vé sửa mã.
    row.action = ACT_ASKED
    db.commit()
    user = service._assistant_user(db, chat_id)
    if user is None:
        service.reply(db, chat_id, "Chat này chưa liên kết tài khoản ERP. Nhắn <code>/dangnhap &lt;mã&gt;</code> "
                                   "(mã lấy ở Trang cá nhân → Telegram) rồi hỏi lại giúp em.")
        return
    if not user_keys.active_key():
        service.reply(db, chat_id, user_keys.NO_KEY_HELP)
        return
    run = service.start_run(db, 0, STAGE_ANSWER)
    db.commit()                                  # giữ dòng sổ kể cả khi lượt hỏng phải rollback
    try:
        from app.modules.assistant import tool_router

        t0 = time.monotonic()
        system = build_system(db, chat_id, row, user, text)
        turns = history(db, chat_id, row.id, row.created_at, smalltalk=tool_router.is_smalltalk(text))
        tools = select_tools(db, user, text)
        log.info("core_v2: dựng ngữ cảnh %.1f s", time.monotonic() - t0)
        msgs = [ChatMessage(role=t["role"], content=t["content"]) for t in turns] + [ChatMessage(role="user", content=text)]
        log.info("core_v2: system=%d ký tự · công cụ=%d · lịch sử=%d lượt", len(system), len(tools), len(turns))

        def execute(name: str, args: dict) -> dict:
            try:
                if name in LOCAL_TOOL_NAMES:
                    return _run_local(db, chat_id, row, user, name, args or {})
                return erp.run_tool(db, user, name, args or {})
            except Exception as e:  # noqa: BLE001
                log.exception("core_v2: công cụ %s hỏng", name)
                return {"error": f"Công cụ {name} lỗi: {type(e).__name__}: {str(e)[:200]}"}

        result = manager.get_provider().run_tools(
            msgs, tools=tools, execute=execute, system=system, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
            max_iters=MAX_ITERS, cache_system=True)
        answer = (result.text or "").strip() or "Em đã làm xong phần đó."
        service.reply(db, chat_id, answer, markdown=True, action=ACT_ANSWER)
        calls = [c for c in (result.tool_calls or []) if isinstance(c, dict) and c.get("name") not in LOCAL_TOOL_NAMES]
        service.deliver_tool_results(db, chat_id, user, calls)
        service.finish_run(db, run, result=result)
        run.artifact = {"core": "v2", "tools": [str(c.get("name") or "") for c in (result.tool_calls or [])
                                                if isinstance(c, dict)][:20], "tools_offered": len(tools)}
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.exception("core_v2: lượt hỏng")
        try:
            run = db.get(service.AgentRun, run.id) or run
            service.finish_run(db, run, error=f"{type(e).__name__}: {e}")
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        service.reply(db, chat_id, f"Em gọi AI bị lỗi (mã lượt #{run.id} · {telegram.esc(type(e).__name__)}). "
                                   "Anh/chị nhắn lại sau một phút giúp em; lặp lại thì báo em xem sổ chạy.")
