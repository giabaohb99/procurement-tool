"""Bộ hội thoại mẫu tự chạy cho lõi hội thoại mới (doc/agent-hub/20 §7 + §10 việc 3, ai-CR-203).

Chạy THẬT qua `core_v2.handle` với model thật, khóa thật của chat chủ bot và dữ liệu ERP thật (đọc), nhưng trong một
LỒNG THỬ:
- mỗi mẫu một chat riêng `eval-<nhãn>-<mã mẫu>` (lịch sử sạch, không lẫn chat thật); xong thì xóa tin + lời nhắc của chat đó;
- không gửi Telegram (bắt lại chữ bot định gửi);
- KHÔNG ghi gì thật: ghi nháp (`_draft_by_text`), công cụ ERP có ghi (`WRITE_TOOLS`), hoàn tác, vé sửa mã đều chỉ GHI SỔ
  là «đã gọi» rồi trả như thành công; lối tắt chữ có thể đụng máy sửa mã / quyền / deploy bị tắt.

Chấm hai tầng: (1) luật cứng của từng lượt (`Turn`: phải / cấm gọi công cụ, có / cấm ghi nháp, ngày phải đúng…), (2) model
chấm theo ý mong đợi (so ý, không so nguyên văn). Mẫu đạt khi cả hai đạt.

Dùng: `python scripts/eval_core_v2.py` trong container agent-hub ở máy dev (xem tệp đó).
"""
from __future__ import annotations

import contextlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import date
from unittest import mock

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings

EVAL_PREFIX = "eval-"
#  Công cụ ERP có GHI — trong lồng thử chỉ ghi sổ rồi trả «coi như xong».
WRITE_TOOLS = frozenset({
    "ticket_create", "create_calendar_event", "update_calendar_event", "delete_calendar_event", "remember_fact",
    "forget_fact", "save_note", "add_personal_item", "mark_personal_item", "save_meeting_template",
    "rewrite_meeting_minutes", "report_missing_feature", "manage_briefs", "deep_research", "propose_glossary_term",
})


@dataclass(frozen=True)
class Turn:
    text: str
    expect: str                                      # ý mong đợi (cho model chấm)
    must_call: tuple[str, ...] = ()                  # phải gọi ĐỦ các công cụ này
    any_call: tuple[str, ...] = ()                   # phải gọi ÍT NHẤT một trong các công cụ này
    must_not_call: tuple[str, ...] = ()
    commit: bool | None = None                       # True: phải ghi nháp; False: cấm ghi
    drop: bool | None = None                         # True: phải bỏ nháp
    dates: tuple[str, ...] = ()                      # cụm «thứ sáu», «thứ sáu tuần sau» → ngày dd/mm/yyyy phải có trong tin
    contains: tuple[str, ...] = ()                   # chữ phải có (không phân biệt hoa thường, đã bỏ thẻ HTML)
    no_model: bool = False                           # lối tắt: không được gọi model
    must_write: tuple[str, ...] = ()                 # phải THẬT SỰ ghi (qua được chốt chặn) — tên trong TurnLog.blocked
    must_not_write: tuple[str, ...] = ()             # cấm ghi (gọi mà bị chốt chặn từ chối thì không tính)


@dataclass(frozen=True)
class Sample:
    id: str
    title: str
    turns: tuple[Turn, ...]
    unlinked: bool = False                           # chat chưa liên kết tài khoản


@dataclass
class TurnLog:
    text: str
    replies: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    commits: list[str] = field(default_factory=list)      # cụm đường cũ nhận: «tạo», «thôi»…
    blocked: list[str] = field(default_factory=list)       # công cụ ghi bị chặn (coi như xong)
    runs: int = 0
    input_tokens: int = 0
    seconds: float = 0.0
    error: str = ""


@dataclass
class SampleResult:
    sample: Sample
    turns: list[TurnLog]
    failures: list[str]
    judge: dict | None = None

    @property
    def passed(self) -> bool:
        return not self.failures and (self.judge is None or bool(self.judge.get("dat")))


_TAG = re.compile(r"<[^>]+>")


def plain(text: str) -> str:
    return _TAG.sub("", text or "").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


# ---------------------------------------------------------------------------
# Luật cứng
# ---------------------------------------------------------------------------
def check_turn(turn: Turn, log: TurnLog, today: date) -> list[str]:
    from .core_v2 import resolve_weekdays

    out: list[str] = []
    called = set(log.tools)
    said = " ".join(plain(r) for r in log.replies)
    if log.error:
        out.append(f"lỗi: {log.error}")
    if not log.replies:
        out.append("bot không trả lời gì")
    for name in turn.must_call:
        if name not in called:
            out.append(f"thiếu công cụ {name}")
    if turn.any_call and not called & set(turn.any_call):
        out.append(f"không gọi công cụ nào trong {', '.join(turn.any_call)}")
    for name in turn.must_not_call:
        if name in called:
            out.append(f"không được gọi {name}")
    for name in turn.must_write:
        if name not in log.blocked:
            out.append(f"phải ghi {name} mà không ghi")
    for name in turn.must_not_write:
        if name in log.blocked:
            out.append(f"GHI {name} khi chưa được phép")
    committed = any(p != "thôi" for p in log.commits)
    if turn.commit is True and not committed:
        out.append("phải ghi nháp mà không ghi")
    if turn.commit is False and committed:
        out.append("GHI NHÁP khi chưa được đồng ý")
    if turn.drop is True and "thôi" not in log.commits:
        out.append("phải bỏ nháp mà không bỏ")
    for phrase in turn.dates:
        for _label, d in resolve_weekdays(phrase, today)[:1]:
            if f"{d:%d/%m/%Y}" not in said and f"{d:%d/%m}" not in said:
                out.append(f"«{phrase}» phải là {d:%d/%m/%Y}")
    low = said.lower()
    for word in turn.contains:
        if word.lower() not in low:
            out.append(f"thiếu chữ «{word}»")
    if turn.no_model and log.runs:
        out.append("lẽ ra đi lối tắt, không gọi model")
    if "«" in said or "»" in said:
        out.append("dùng ngoặc « » trong tin (luật: in đậm / in nghiêng)")
    return out


# ---------------------------------------------------------------------------
# Lồng thử
# ---------------------------------------------------------------------------
class Sandbox:
    """Vá mọi đường ra ngoài trong lúc chạy một lượt; ghi lại thứ bot định làm vào `self.log`."""

    def __init__(self, db: Session, owner_chat: str, owner_user, *, unlinked: bool = False):
        self.db = db
        self.owner_chat = owner_chat
        self.owner_user = owner_user
        self.unlinked = unlinked
        self.log: TurnLog | None = None
        self.run_ids: list[int] = []                     # run do lồng thử mở (service.start_run)
        self._msg_id = 900_000

    # -- bắt lại ------------------------------------------------------------
    def _send(self, text, buttons=None, chat_id="", **kw):
        if self.log is not None:
            self.log.replies.append(str(text))
        self._msg_id += 1
        return self._msg_id

    def _send_document(self, chat_id, filename, data, *, caption="", **kw):
        if self.log is not None:
            self.log.replies.append(f"[tệp {filename}] {caption}")
        return {}

    def _draft_by_text(self, db, chat_id, row, phrase):
        from . import core_v2

        pending, _info = core_v2._pending_draft(db, chat_id, row.id, row.created_at)
        if pending is None:
            return False
        self.log.commits.append(str(phrase))
        #  Như đường cũ: báo kết quả + nháp không còn chờ (nhưng KHÔNG gọi ERP tạo thật).
        self.log.replies.append("Em bỏ nháp rồi, không tạo." if str(phrase) == "thôi"
                                else "Đã tạo theo nháp (mã phiếu do ERP cấp).")
        pending.action = "eval_da_xu_ly"
        db.flush()
        return True

    @contextlib.contextmanager
    def patched(self):
        from . import change_undo, core_v2, erp, ops, service, telegram  # noqa: F401  (change_undo: nạp sẵn)

        real_run_tool = erp.run_tool
        real_start_run = service.start_run

        def start_run(db, task_id, stage):
            run = real_start_run(db, task_id, stage)
            self.run_ids.append(run.id)
            return run
        real_run_local = core_v2._run_local
        real_more = core_v2._more_tools_result

        def run_tool(db, user, name, args):
            self.log.tools.append(name)
            if name in WRITE_TOOLS:
                self.log.blocked.append(name)
                return {"ok": True, "note": "(đã làm)"}
            return real_run_tool(db, user, name, args)

        def run_local(db, chat_id, row, user, name, args):
            self.log.tools.append(name)
            return real_run_local(db, chat_id, row, user, name, args)

        def more(args, offered):
            self.log.tools.append(core_v2.MORE_TOOLS)
            return real_more(args, offered)

        def undo_change(db, user, change_id, source=0):
            self.log.blocked.append(f"undo_change#{change_id}")
            return {"ok": True, "message": "Đã hoàn tác (thử)."}

        def code_task(db, chat_id, mo_ta):
            self.log.blocked.append("create_code_task")
            return {"ok": True, "note": "Đã ghi yêu cầu sửa phần mềm."}

        def allowed(chat_id) -> bool:
            chat_id = str(chat_id or "")
            if chat_id.startswith(EVAL_PREFIX):
                return not self.unlinked
            return chat_id == self.owner_chat

        user = None if self.unlinked else self.owner_user
        off = lambda *a, **k: False     # noqa: E731
        zero = lambda *a, **k: 0        # noqa: E731
        patches = [
            mock.patch.object(settings, "AGENT_ACK_ENABLED", False),
            mock.patch.object(service, "start_run", start_run),
            mock.patch.object(telegram, "send", self._send),
            mock.patch.object(telegram, "send_chat_action", lambda *a, **k: None),
            mock.patch.object(telegram, "send_document", self._send_document),
            mock.patch.object(telegram, "send_payload", lambda payload: {}),
            mock.patch.object(telegram, "delete_message", lambda *a, **k: True),
            mock.patch.object(telegram, "is_allowed_chat", allowed),
            mock.patch.object(service, "_assistant_user", lambda db, chat_id="": user),
            mock.patch.object(service, "_draft_by_text", self._draft_by_text),
            mock.patch.object(erp, "run_tool", run_tool),
            mock.patch.object(erp, "undo_change", undo_change),
            mock.patch.object(core_v2, "_run_local", run_local),
            mock.patch.object(core_v2, "_more_tools_result", more),
            mock.patch.object(core_v2, "_create_code_task", code_task),
            #  Lối tắt của chủ bot có thể đụng máy sửa mã / quyền / deploy / vé — tắt hẳn trong lồng thử.
            mock.patch.object(service, "_ok_by_text", off),
            mock.patch.object(service, "_grant_by_text", off),
            mock.patch.object(service, "_runner_by_text", off),
            mock.patch.object(service, "_ghi_viec_by_text", off),
            mock.patch.object(service, "_dev_request_by_text", off),
            mock.patch.object(service, "_keys_by_text", off),
            mock.patch.object(service, "route_task_command", off),
            mock.patch.object(service, "_deploy_time_target", zero),
            mock.patch.object(service, "_patch_question_target", zero),
            mock.patch.object(service, "_plan_answer_target", zero),
            mock.patch.object(ops, "handle_text", off),
        ]
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            yield self


# ---------------------------------------------------------------------------
# Chạy
# ---------------------------------------------------------------------------
def run_turn(db: Session, box: Sandbox, chat_id: str, text: str) -> TurnLog:
    from . import core_v2, service, user_keys
    from .constants import DIR_IN
    from .model import AgentRun

    log = TurnLog(text=text)
    box.log = log
    start = len(box.run_ids)
    t0 = time.monotonic()
    row = service.log_message(db, DIR_IN, chat_id, 0, text, action="")
    db.commit()
    try:
        with user_keys.for_chat(db, box.owner_chat):
            core_v2.handle(db, chat_id, row, text)
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.error = f"{type(e).__name__}: {e}"[:300]
    log.seconds = round(time.monotonic() - t0, 1)
    #  Chỉ đếm / đóng run do CHÍNH lượt thử mở (bot thật vẫn chạy song song trên cùng DB).
    ids = box.run_ids[start:]
    runs = db.scalars(select(AgentRun).where(AgentRun.id.in_(ids))).all() if ids else []
    _close_dangling(db, runs, log)
    log.runs = len(runs)
    log.input_tokens = sum(int(r.input_tokens or 0) for r in runs)
    return log


def _close_dangling(db: Session, runs, log: TurnLog) -> None:
    """Agent 1 15/10: lần chạy thử bỏ dở để lại run #248 «đang chạy» → chặn deploy (deploy chờ hết việc dở). Lượt nào
    ném lỗi giữa chừng thì đóng run của nó ngay."""
    from .constants import RUN_ERROR, RUN_RUNNING

    open_runs = [r for r in runs if r.status == RUN_RUNNING]
    if not open_runs:
        return
    for r in open_runs:
        r.status = RUN_ERROR
        r.error = f"eval: lượt thử dừng giữa chừng ({log.error or 'không rõ'})"[:2000]
    db.commit()


def cleanup(db: Session, prefix: str) -> None:
    from .model import AgentMessage, AgentReminder

    db.execute(delete(AgentMessage).where(AgentMessage.chat_id.like(f"{prefix}%")).execution_options(synchronize_session=False))
    db.execute(delete(AgentReminder).where(AgentReminder.chat_id.like(f"{prefix}%"))
               .execution_options(synchronize_session=False))
    db.commit()


JUDGE_SYSTEM = (
    "Bạn chấm một trợ lý chat tiếng Việt của công ty (bot Telegram, gọi người dùng là «đại ca» khi đó là chủ bot). Với "
    "từng lượt có Ý MONG ĐỢI và câu trả lời THẬT của bot (kèm công cụ bot đã gọi). Chấm theo Ý, không cần nguyên văn. "
    "Trượt khi: không đạt ý chính; bịa số liệu / ngày; nói đã làm mà không có công cụ tương ứng; trả lời lạc đề; dài "
    "dòng vô ích; dùng emoji. Tin «Đã tạo theo nháp …» / «Em bỏ nháp rồi …» là hệ thống tự báo sau khi ghi / bỏ — coi là "
    "đúng. Dấu • là gạch đầu dòng, KHÔNG phải emoji. Chào lại ngắn kèm MỘT câu hỏi cần giúp gì (có thể nêu 2–3 việc "
    "hay làm) là đạt, không phải kể lể. Ngày giờ hiện tại ghi ở đầu bài chấm — dùng nó khi xét ngày. Chỉ trả JSON một dòng: {\"dat\": true|false, \"diem\": 0-10, \"ly_do\": \"tối đa 2 câu\"}."
)


def judge(sample: Sample, logs: list[TurnLog]) -> dict:
    """Model chấm theo ý (đường model thường của lõi — Claude qua trạm)."""
    from app.modules.assistant.provider.base import ChatMessage

    from . import core_v2, manager, user_keys

    from .timeutil import now_local

    now = now_local()
    parts = [f"BÂY GIỜ: {now:%H:%M} ngày {now:%d/%m/%Y} (giờ Việt Nam)", f"MẪU: {sample.title}"]
    for i, (turn, log) in enumerate(zip(sample.turns, logs), 1):
        said = "\n".join(plain(r) for r in log.replies) or "(không trả lời)"
        parts.append(f"--- Lượt {i}\nNGƯỜI DÙNG: {turn.text}\nÝ MONG ĐỢI: {turn.expect}\n"
                     f"CÔNG CỤ BOT GỌI: {', '.join(log.tools) or '(không)'}\nBOT TRẢ LỜI:\n{said[:2500]}")
    with user_keys.prefer(core_v2.route_providers(core_v2.LANE_NORMAL)):
        res = manager.get_provider().ask([ChatMessage(role="user", content="\n\n".join(parts))], system=JUDGE_SYSTEM,
                                         max_tokens=300, temperature=0.0)
    m = re.search(r"\{.*\}", res.text or "", re.S)
    try:
        out = json.loads(m.group(0)) if m else {}
    except ValueError:
        out = {}
    if not isinstance(out, dict) or "dat" not in out:
        return {"dat": False, "diem": 0, "ly_do": f"model chấm trả không đọc được: {(res.text or '')[:150]}"}
    return out


def run_sample(db: Session, sample: Sample, *, owner_chat: str, owner_user, tag: str, today: date,
               use_judge: bool = True) -> SampleResult:
    from . import user_keys

    chat_id = f"{EVAL_PREFIX}{tag}-{sample.id}"
    box = Sandbox(db, owner_chat, owner_user, unlinked=sample.unlinked)
    logs: list[TurnLog] = []
    failures: list[str] = []
    try:
        with box.patched():
            for i, turn in enumerate(sample.turns, 1):
                log = run_turn(db, box, chat_id, turn.text)
                logs.append(log)
                failures += [f"lượt {i}: {f}" for f in check_turn(turn, log, today)]
            verdict = None
            if use_judge:
                try:
                    with user_keys.for_chat(db, owner_chat):
                        verdict = judge(sample, logs)
                except Exception as e:  # noqa: BLE001
                    verdict = {"dat": False, "diem": 0, "ly_do": f"model chấm lỗi: {type(e).__name__}: {e}"[:200]}
    finally:
        from .model import AgentRun

        db.rollback()
        if box.run_ids:
            _close_dangling(db, db.scalars(select(AgentRun).where(AgentRun.id.in_(box.run_ids))).all(),
                            TurnLog(text="", error="mẫu dừng giữa chừng"))
        cleanup(db, chat_id)
    return SampleResult(sample=sample, turns=logs, failures=failures, judge=verdict)


def report(results: list[SampleResult]) -> str:
    ok = sum(r.passed for r in results)
    lines = [f"# Bộ hội thoại mẫu lõi v2 — đạt {ok}/{len(results)}", "",
             "| Mẫu | Kết quả | Lượt gọi | Token vào | Giây | Ghi chú |", "|---|---|---|---|---|---|"]
    for r in results:
        note = "; ".join(r.failures)
        if r.judge is not None and not r.judge.get("dat"):
            note = (note + "; " if note else "") + f"chấm: {r.judge.get('ly_do', '')}"
        lines.append(f"| {r.sample.id} {r.sample.title} | {'đạt' if r.passed else 'TRƯỢT'} | "
                     f"{sum(t.runs for t in r.turns)} | {sum(t.input_tokens for t in r.turns):,} | "
                     f"{sum(t.seconds for t in r.turns):.1f} | {note.replace('|', '/')[:300]} |")
    total_in = sum(t.input_tokens for r in results for t in r.turns)
    lines += ["", f"Tổng token vào: {total_in:,} · tổng thời gian: {sum(t.seconds for r in results for t in r.turns):.0f} s"]
    return "\n".join(lines)


def owner_context(db: Session):
    """(chat chủ bot, tài khoản ERP của chat đó)."""
    from . import service

    chat = (settings.AGENT_TELEGRAM_CHAT_ID or "").split(",")[0].strip()
    if not chat:
        raise RuntimeError("Chưa khai AGENT_TELEGRAM_CHAT_ID.")
    user = service._assistant_user(db, chat)
    if user is None:
        raise RuntimeError("Chat chủ bot chưa có tài khoản ERP.")
    return chat, user


def as_dict(r: SampleResult) -> dict:
    return {"id": r.sample.id, "title": r.sample.title, "passed": r.passed, "failures": r.failures, "judge": r.judge,
            "turns": [vars(t) for t in r.turns]}


__all__ = ["Sample", "Turn", "WRITE_TOOLS", "run_sample", "report", "owner_context", "check_turn", "as_dict"]
