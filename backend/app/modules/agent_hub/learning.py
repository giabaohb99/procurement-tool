"""VÒNG TỰ HỌC của bot (ai-CR-078) — chạy ở worker của bot trên dev, mỗi 5 phút.

  1. Đề xuất thuật ngữ mới (từ `propose_glossary_term` của Trợ lý, ở web hay Telegram) → nhắn đại ca MỘT thẻ, «đúng» là
     ghi vào sổ, «thôi» là bỏ. Đề xuất cũ quá 15 phút thì duyệt bằng «duyệt thuật ngữ #n» / «bỏ thuật ngữ #n».
  2. Chỗ Trợ lý thiếu chức năng lặp từ `feedback.GAP_MIN` lần → mở VIỆC SỬA MÃ nguồn «Trợ lý thiếu chức năng» đi đường
     thường (rà soát → kế hoạch → đại ca duyệt), báo đại ca một câu. Việc đóng thì bỏ gắn để lần thiếu sau tính lại.
"""
from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings

from . import telegram
from .constants import ACT_GLOSS_WAIT, ACT_OPS, CLOSED_STATUSES, DIR_OUT, RISK_MEDIUM, SRC_GAP, ST_TRIAGE
from .model import AgentTask

log = logging.getLogger("app.agent_hub.learning")


def term_card(item: dict) -> str:
    esc = telegram.esc
    lines = [f"<b>ĐỀ XUẤT THUẬT NGỮ</b> · #{item['id']}", "",
             f"<b>Từ:</b> «{esc(item['term'])}»", f"<b>Nghĩa:</b> {esc(item['meaning'])}"]
    if item.get("evidence"):
        lines.append(f"<b>Bằng chứng:</b> {esc(item['evidence'])}")
    if item.get("source"):
        lines.append(f"<i>Nguồn: {esc(item['source'])}.</i>")
    lines += ["", "Nhắn <b>đúng</b> để ghi vào sổ · <b>thôi</b> để bỏ",
              f"<i>Quá 15 phút thì nhắn «duyệt thuật ngữ #{item['id']}».</i>"]
    return "\n".join(lines)


def notify_terms(db: Session) -> int:
    from app.modules.assistant import glossary

    from . import service

    chat = settings.AGENT_TELEGRAM_CHAT_ID
    if not chat:
        return 0
    sent = 0
    for item in glossary.load_pending(db):
        if item.get("notified"):
            continue
        service.reply(db, chat, term_card(item), action=ACT_OPS)
        service.log_message(db, DIR_OUT, chat, 0, json.dumps({"pid": item["id"]}), action=ACT_GLOSS_WAIT)
        db.commit()
        glossary.mark_notified(db, int(item["id"]))
        sent += 1
    return sent


def open_gap_tasks(db: Session) -> int:
    from app.modules.assistant import feedback

    from . import service

    #  Việc đã đóng → bỏ gắn, lần thiếu sau tính lại từ đầu.
    for gap in feedback.load(db):
        code = gap.get("task_code")
        if code:
            task = db.scalar(select(AgentTask).where(AgentTask.code == code))
            if task is None or task.status in CLOSED_STATUSES:
                feedback.clear_task(db, code)
    opened = 0
    for gap in feedback.due(db):
        if service._quota_left(db) <= 0:
            log.warning("agent_hub: chạm trần việc/ngày, chỗ thiếu «%s» chờ lượt sau", gap["missing"])
            break
        summary = "\n".join([
            f"Trợ lý AI không đáp được {gap['count']} lần vì công cụ thiếu tính năng: {gap['missing']}.",
            (f"Công cụ gần nhất: {gap['tool']}." if gap.get("tool") else ""),
            "Câu người dùng hỏi (ví dụ):",
            *[f"- {e}" for e in gap.get("examples") or []],
            "",
            "Việc: bổ sung tính năng còn thiếu cho công cụ của Trợ lý (backend/app/modules/assistant/tools/), kèm bài kiểm, "
            "giữ đúng phân quyền và phạm vi dữ liệu như các tool hiện có.",
        ])
        task = AgentTask(code=service.next_code(db), title=f"Trợ lý thiếu chức năng: {gap['missing']}"[:255],
                         source=SRC_GAP, status=ST_TRIAGE, summary=summary, risk_level=RISK_MEDIUM,
                         created_by=0, updated_by=0)
        db.add(task)
        db.flush()
        feedback.set_task(db, gap["sig"], task.code)
        db.commit()
        service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                      f"<b>TRỢ LÝ THIẾU CHỨC NĂNG</b> · {telegram.esc(task.code)}\n\n"
                      f"{telegram.esc(gap['missing'])}\n<i>Gặp {gap['count']} lần — em mở việc sửa mã, đi đường thường "
                      "(rà soát → kế hoạch → đại ca duyệt).</i>", task_id=task.id, action=ACT_OPS)
        db.commit()
        try:
            service.start_scan(db, task)
            db.commit()
        except Exception:  # noqa: BLE001 — mở việc được là đủ
            log.exception("agent_hub: giao rà soát việc thiếu chức năng hỏng")
        opened += 1
    return opened


def tick(db: Session) -> dict:
    return {"terms": notify_terms(db), "gap_tasks": open_gap_tasks(db)}
