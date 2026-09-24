"""Màn VIỆC CỦA BOT trong ERP v2 (ai-CR-036, AN-006) — `/system/agent-tasks`.

Chỉ ĐỌC. Mọi thao tác trên việc (duyệt, gộp, thu hồi, bỏ…) vẫn đi qua Telegram, nơi có
luật hỏi-trước và dấu vết hội thoại; màn này để tra: bot đã nhận gì, đi qua bước nào, mất
bao lâu, tốn bao nhiêu. Khóa quyền riêng `agent_task` (PUBLIC ở `SCOPE_FIELDS`: việc của bot
không thuộc người hay phòng nào).
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require
from app.core.config import settings
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import chat_link, coder, telegram
from .constants import (
    DIRECTION_LABELS,
    RISK_LABELS,
    RUN_STATUS_LABELS,
    SOURCE_LABELS,
    STAGE_LABELS,
    TASK_STATUS_LABELS,
)
from .model import AgentMessage, AgentRun, AgentTask, AgentTaskItem
from .timeutil import now_local, to_local

router = APIRouter(prefix="/api/agent-hub", tags=["agent-hub"])

ENTITY = "agent_task"
#  Thân tin nhắn trả về màn chi tiết: đủ đọc, không kéo cả thẻ kế hoạch dài vào mỗi dòng.
MESSAGE_BODY_LIMIT = 2000


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _run_totals(db: Session, task_ids: list[int]) -> dict[int, dict]:
    """Tổng chi phí + tổng thời gian bot chạy + số lượt, gom MỘT truy vấn cho cả trang."""
    if not task_ids:
        return {}
    rows = (db.query(AgentRun.task_id, func.coalesce(func.sum(AgentRun.cost_usd), 0.0),
                     func.coalesce(func.sum(AgentRun.duration_ms), 0), func.count(AgentRun.id))
            .filter(AgentRun.task_id.in_(task_ids)).group_by(AgentRun.task_id).all())
    return {tid: {"cost_usd": float(cost or 0), "bot_ms": int(ms or 0), "runs": int(n or 0)}
            for tid, cost, ms, n in rows}


def serialize_task(task: AgentTask, totals: dict | None = None) -> dict:
    totals = totals or {}
    return {
        "id": task.id,
        "code": task.code,
        "title": task.title,
        "status": task.status,
        "status_label": TASK_STATUS_LABELS.get(task.status, "?"),
        "risk_level": task.risk_level,
        "risk_label": RISK_LABELS.get(task.risk_level, "?"),
        "source": task.source,
        "source_label": SOURCE_LABELS.get(task.source, "?"),
        "branch_name": task.branch_name or "",
        "pr_url": task.pr_url or "",
        "created_at": _iso(task.created_at),
        "updated_at": _iso(task.updated_at),
        "closed_at": _iso(task.closed_at),
        "deployed_dev_at": _iso(task.deployed_dev_at),
        "cost_usd": round(totals.get("cost_usd", 0.0), 4),
        "bot_ms": totals.get("bot_ms", 0),
        "runs": totals.get("runs", 0),
    }


@router.get("/tasks")
def list_tasks(
    status: int = Query(0, ge=0),
    q: str = Query("", max_length=100),
    user=Depends(require(ENTITY, "read")),
    db: Session = Depends(get_db),
    pg: dict = Depends(pagination),
):
    """Việc của bot, mới nhất trước. Lọc theo trạng thái và chữ (mã hoặc tên việc)."""
    query = db.query(AgentTask)
    if status:
        query = query.filter(AgentTask.status == status)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(AgentTask.code.like(like), AgentTask.title.like(like)))
    total = query.count()
    rows = (query.order_by(AgentTask.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all())
    totals = _run_totals(db, [t.id for t in rows])
    return success({"items": [serialize_task(t, totals.get(t.id)) for t in rows], "total": total,
                    "page": pg["page"], "page_size": pg["page_size"],
                    "statuses": [{"value": k, "label": v} for k, v in TASK_STATUS_LABELS.items()]})


@router.get("/tasks/{task_id}")
def get_task(task_id: int, user=Depends(require(ENTITY, "read")), db: Session = Depends(get_db)):
    task = db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(404, "Không tìm thấy việc")
    runs = db.query(AgentRun).filter(AgentRun.task_id == task.id).order_by(AgentRun.id).all()
    msgs = db.query(AgentMessage).filter(AgentMessage.task_id == task.id).order_by(AgentMessage.id).all()
    items = db.query(AgentTaskItem).filter(AgentTaskItem.task_id == task.id).order_by(AgentTaskItem.id).all()
    scan = coder.latest_scan_run(db, task)
    data = serialize_task(task, _run_totals(db, [task.id]).get(task.id))
    data.update({
        "summary": task.summary or "",
        "plan": task.plan or "",
        "plan_files": list(task.plan_files or []),
        "test_plan": task.test_plan or "",
        "questions": list(task.questions or []),
        "note": task.note or "",
        "scan_message": (scan.artifact or {}).get("message", "") if scan is not None else "",
        "merged_sha": coder.merged_sha_for(db, task),
        "timing": coder.timing_line(db, task),
        "sources": [{"source": i.source, "source_label": SOURCE_LABELS.get(i.source, "?"),
                     "ref_id": i.ref_id} for i in items],
        "run_list": [{
            "id": r.id, "stage": r.stage, "stage_label": STAGE_LABELS.get(r.stage, str(r.stage)),
            "status": r.status, "status_label": RUN_STATUS_LABELS.get(r.status, "?"),
            "provider": r.provider, "model": r.model, "started_at": _iso(r.started_at),
            "duration_ms": r.duration_ms, "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens, "cost_usd": round(float(r.cost_usd or 0), 4),
            "error": (r.error or "")[:500],
        } for r in runs],
        "messages": [{
            "id": m.id, "direction": m.direction, "direction_label": DIRECTION_LABELS.get(m.direction, "?"),
            "action": m.action, "body": (m.body or "")[:MESSAGE_BODY_LIMIT],
            "files": len(m.files or []), "created_at": _iso(m.created_at),
        } for m in msgs],
    })
    return success(data)


# ---------------------------------------------------------------------------
# Liên kết Telegram của CHÍNH MÌNH (ai-CR-038) — chỉ đòi đăng nhập, không cần khóa `agent_task`:
# ai cũng tự nối được Telegram của mình, như tự đá thiết bị lạ ở «Thiết bị của tôi».
# ---------------------------------------------------------------------------
def _serialize_link(link) -> dict:
    return {"id": link.id, "chat": chat_link.mask_chat(link.chat_id), "tg_name": link.tg_name,
            "linked_at": _iso(link.linked_at), "expires_at": _iso(link.expires_at)}


@router.get("/links")
def list_my_links(user=Depends(get_current_user), db: Session = Depends(get_db)):
    bot = telegram.get_bot_username()
    return success({"enabled": bool(settings.AGENT_LINK_ENABLED), "bot_username": bot,
                    "items": [_serialize_link(x) for x in chat_link.list_user_links(db, user.id)]})


@router.post("/links/code")
def create_link_code(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Mã 6 số dùng một lần để nhắn `/dangnhap <mã>` cho bot. Mã cũ chưa dùng bị hủy."""
    if not settings.AGENT_LINK_ENABLED:
        raise HTTPException(400, "Liên kết Telegram đang tắt")
    code, expires = chat_link.issue_code(db, user.id)
    bot = telegram.get_bot_username()
    return success({"code": code, "expires_at": _iso(expires),
                    "deep_link": f"https://t.me/{bot}?start={code}" if bot else ""})


@router.delete("/links/{link_id}")
def remove_link(link_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    link = next((x for x in chat_link.list_user_links(db, user.id) if x.id == link_id), None)
    if link is None:
        raise HTTPException(404, "Không tìm thấy liên kết")
    chat_link.revoke_chat(db, link.chat_id)
    return success(None, "Đã gỡ liên kết Telegram")


@router.get("/stats")
def stats(days: int = Query(30, ge=1, le=365), user=Depends(require(ENTITY, "read")),
          db: Session = Depends(get_db)):
    """Tổng quan: số việc theo trạng thái, chi phí theo ngày và theo bước trong `days` ngày."""
    since = datetime.now() - timedelta(days=days)
    by_status = dict(db.query(AgentTask.status, func.count(AgentTask.id)).group_by(AgentTask.status).all())
    runs = db.query(AgentRun.stage, AgentRun.started_at, AgentRun.cost_usd).filter(
        AgentRun.started_at >= since).all()
    per_day: dict[str, float] = {}
    per_stage: dict[int, float] = {}
    for stage, started, cost in runs:
        #  Ngày theo giờ Việt Nam: sổ ghi giờ UTC của container (ai-CR-020).
        day = (to_local(started) or now_local()).date().isoformat()
        per_day[day] = per_day.get(day, 0.0) + float(cost or 0)
        per_stage[stage] = per_stage.get(stage, 0.0) + float(cost or 0)
    return success({
        "days": days,
        "total_cost_usd": round(sum(per_day.values()), 4),
        "run_count": len(runs),
        "by_status": [{"status": k, "label": TASK_STATUS_LABELS.get(k, "?"), "count": v}
                      for k, v in sorted(by_status.items())],
        "cost_by_day": [{"day": d, "cost_usd": round(c, 4)} for d, c in sorted(per_day.items())],
        "cost_by_stage": [{"stage": s, "label": STAGE_LABELS.get(s, str(s)), "cost_usd": round(c, 4)}
                          for s, c in sorted(per_stage.items(), key=lambda x: -x[1])],
    })
