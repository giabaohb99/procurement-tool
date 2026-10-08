"""Màn VIỆC CỦA BOT trong ERP v2 (ai-CR-036, AN-006) — `/system/agent-tasks`.

Chỉ ĐỌC. Mọi thao tác trên việc (duyệt, gộp, thu hồi, bỏ…) vẫn đi qua Telegram, nơi có
luật hỏi-trước và dấu vết hội thoại; màn này để tra: bot đã nhận gì, đi qua bước nào, mất
bao lâu, tốn bao nhiêu. Khóa quyền riêng `agent_task` (PUBLIC ở `SCOPE_FIELDS`: việc của bot
không thuộc người hay phòng nào).
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require
from app.core.config import settings
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from pydantic import BaseModel

from . import ai_keys, chat_link, coder, google_link, mcp_keys, telegram, user_keys
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
from app.modules.employee.field_limits import Str80, Str200

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
            "linked_at": _iso(link.linked_at), "expires_at": _iso(link.expires_at),
            "notify_mode": int(link.notify_mode or 0)}


class LinkNotifyIn(BaseModel):
    notify_mode: int


@router.patch("/links/{link_id}")
def set_link_notify(link_id: int, body: LinkNotifyIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """ai-CR-059: mức chuông ERP chuyển sang chat Telegram này — 0 tắt · 1 việc của tôi · 2 tất cả."""
    link = next((x for x in chat_link.list_user_links(db, user.id) if x.id == link_id), None)
    if link is None:
        raise HTTPException(404, "Không tìm thấy liên kết")
    if body.notify_mode not in (0, 1, 2):
        raise HTTPException(400, "Mức chuông không hợp lệ")
    link.notify_mode = body.notify_mode
    db.commit()
    return success(_serialize_link(link), "Đã đổi mức chuông")


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


# ---------------------------------------------------------------------------
# Khóa Gemini CÁ NHÂN (ai-CR-053, D-01) — cũng tự phục vụ, chỉ đòi đăng nhập. Khóa thô chỉ đi vào
# (PUT) rồi lưu mã hóa; không cửa nào trả khóa ra, kể cả cho chính chủ — chỉ 4 ký tự cuối.
# ---------------------------------------------------------------------------
class AiKeyIn(BaseModel):
    key: str
    provider: str = "gemini"
    model: Str80 = ""
    base_url: Str200 = ""     # ai-CR-108: chỉ hãng «tùy chỉnh»
    priority: int = 0
    daily_cap: int = 0


class AiKeyPatch(BaseModel):
    model: Str80 | None = None
    priority: int | None = None
    daily_cap: int | None = None


@router.get("/ai-key")
def get_my_ai_key(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return success(user_keys.describe(db, user.id))


@router.put("/ai-key")
def set_my_ai_key(body: AiKeyIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """ai-CR-098: nhiều khóa, nhiều hãng. Cùng hãng + cùng ưu tiên = thay khóa; ưu tiên 0 = tự xếp (cùng hãng thì giữ
    chỗ cũ, hãng mới thì xếp cuối)."""
    try:
        user_keys.set_key(db, user.id, body.key, body.provider, model=body.model, priority=body.priority,
                          daily_cap=body.daily_cap, base_url=body.base_url)
    except user_keys.InvalidKey as e:
        raise HTTPException(400, str(e)) from e
    label = ai_keys.PROVIDER_LABELS.get(body.provider, body.provider)
    return success(user_keys.describe(db, user.id), f"Đã lưu khóa {label}. Bot Telegram sẽ dùng khóa này cho anh/chị.")


@router.patch("/ai-key/{row_id}")
def patch_my_ai_key(row_id: int, body: AiKeyPatch, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if ai_keys.update_key(db, row_id, owner_type=ai_keys.OWNER_USER, owner_id=user.id, model=body.model,
                          priority=body.priority, daily_cap=body.daily_cap) is None:
        raise HTTPException(404, "Không tìm thấy khóa")
    return success(user_keys.describe(db, user.id), "Đã cập nhật khóa")


@router.delete("/ai-key/{row_id}")
def remove_one_ai_key(row_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not ai_keys.revoke_key(db, row_id, owner_type=ai_keys.OWNER_USER, owner_id=user.id):
        raise HTTPException(404, "Không tìm thấy khóa")
    return success(user_keys.describe(db, user.id), "Đã gỡ khóa")


@router.delete("/ai-key")
def remove_my_ai_key(user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_keys.revoke(db, user.id)
    return success(user_keys.describe(db, user.id), "Đã gỡ mọi khóa AI")


# Khóa CÔNG TY (ai-CR-098): một bảng với khóa cá nhân, owner_type = 1. Gác bằng quyền cấu hình hệ thống — cùng chỗ
# hai ô khóa cũ (Quản trị → Cấu hình hệ thống → Trợ lý AI). Dùng cho Trợ lý web + đường lùi của bot.
def _company_payload(db: Session) -> dict:
    return {"items": ai_keys.describe_rows(ai_keys.active_rows(db, ai_keys.OWNER_COMPANY, 0), db),
            "providers": [{"name": p, "label": ai_keys.PROVIDER_LABELS[p], "site": ai_keys.PROVIDER_SITES[p]}
                          for p in ai_keys.PROVIDERS]}


@router.get("/ai-key/company")
def get_company_ai_keys(user=Depends(require("setting", "read")), db: Session = Depends(get_db)):
    return success(_company_payload(db))


@router.put("/ai-key/company")
def set_company_ai_key(body: AiKeyIn, user=Depends(require("setting", "write")), db: Session = Depends(get_db)):
    try:
        ai_keys.add_key(db, owner_type=ai_keys.OWNER_COMPANY, owner_id=0, provider=body.provider, raw=body.key,
                        model=body.model, priority=body.priority, daily_cap=body.daily_cap, by_user=user.id,
                        base_url=body.base_url)
    except ai_keys.InvalidKey as e:
        raise HTTPException(400, str(e)) from e
    return success(_company_payload(db), f"Đã lưu khóa công ty {ai_keys.PROVIDER_LABELS.get(body.provider, body.provider)}")


@router.patch("/ai-key/company/{row_id}")
def patch_company_ai_key(row_id: int, body: AiKeyPatch, user=Depends(require("setting", "write")),
                         db: Session = Depends(get_db)):
    if ai_keys.update_key(db, row_id, owner_type=ai_keys.OWNER_COMPANY, owner_id=0, model=body.model,
                          priority=body.priority, daily_cap=body.daily_cap) is None:
        raise HTTPException(404, "Không tìm thấy khóa")
    return success(_company_payload(db), "Đã cập nhật khóa công ty")


@router.delete("/ai-key/company/{row_id}")
def remove_company_ai_key(row_id: int, user=Depends(require("setting", "write")), db: Session = Depends(get_db)):
    if not ai_keys.revoke_key(db, row_id, owner_type=ai_keys.OWNER_COMPANY, owner_id=0):
        raise HTTPException(404, "Không tìm thấy khóa")
    return success(_company_payload(db), "Đã gỡ khóa công ty")


# ---------------------------------------------------------------------------
# Khóa kết nối MCP cá nhân (ai-CR-063, M-02) — tự phục vụ; khóa thô chỉ trả đúng một lần lúc tạo.
# ---------------------------------------------------------------------------
class McpKeyIn(BaseModel):
    name: Str80 = ""
    scope: int = 0
    days: int = 90


@router.get("/mcp-keys")
def list_my_mcp_keys(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return success({"endpoint": f"{settings.AGENT_ERP_URL.rstrip('/') if settings.AGENT_ERP_URL else ''}/api/mcp",
                    "items": [mcp_keys.serialize(k) for k in mcp_keys.list_for_user(db, user.id)]})


@router.post("/mcp-keys")
def create_my_mcp_key(body: McpKeyIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        row, raw = mcp_keys.create(db, user.id, name=body.name, scope=body.scope, days=body.days)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return success({**mcp_keys.serialize(row), "key": raw}, "Đã tạo khóa MCP. Chép ngay: khóa chỉ hiện một lần.")


@router.delete("/mcp-keys/{key_id}")
def remove_my_mcp_key(key_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    row = next((k for k in mcp_keys.list_for_user(db, user.id) if k.id == key_id), None)
    if row is None:
        raise HTTPException(404, "Không tìm thấy khóa")
    mcp_keys.revoke(db, row)
    return success(None, "Đã gỡ khóa MCP")


# ---------------------------------------------------------------------------
# Google cá nhân (ai-CR-064, M-06) — tự phục vụ. Token chỉ nằm trong DB mã hóa, không cửa nào trả ra.
# ---------------------------------------------------------------------------
@router.get("/google")
def my_google(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return success(google_link.describe(db, user.id))


@router.post("/google/authorize")
def google_authorize(user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return success({"url": google_link.authorize_url(user.id)})
    except google_link.GoogleError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/google/callback")
def google_callback(code: str = "", state: str = "", error: str = "", db: Session = Depends(get_db)):
    """Google gọi về sau màn đồng ý (không có Bearer): danh tính lấy từ `state` đã ký."""
    back = (settings.AGENT_ERP_URL.rstrip("/") if settings.AGENT_ERP_URL else "") + "/me?tab=ai-key"
    uid = google_link.parse_state(state)
    if error or not code or not uid:
        return RedirectResponse(back + "&google=loi", status_code=302)
    try:
        google_link.exchange_code(db, uid, code)
    except google_link.GoogleError:
        return RedirectResponse(back + "&google=loi", status_code=302)
    return RedirectResponse(back + "&google=xong", status_code=302)


@router.delete("/google")
def google_disconnect(user=Depends(get_current_user), db: Session = Depends(get_db)):
    link = google_link.get_link(db, user.id)
    if link is not None:
        google_link.revoke(db, link)
    return success(google_link.describe(db, user.id), "Đã gỡ kết nối Google")


class RevokeIn(BaseModel):
    user_id: int


@router.post("/internal/revoke")
async def internal_revoke(request: Request, body: RevokeIn, db: Session = Depends(get_db)):
    """ai-CR-119: ERP (đã tách) báo nhân sự nghỉ — chỉ nhận chữ ký máy-nói-máy, không có người dùng."""
    from app.core import agent_signature

    ok, reason, _uid = agent_signature.verify(request.method, request.url.path, await request.body(), request.headers)
    if not ok:
        raise HTTPException(401, f"Chữ ký ERP không hợp lệ: {reason}")
    from .service import revoke_user_access

    n = revoke_user_access(db, body.user_id)
    db.commit()
    return success({"revoked": n})


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


# ---------------------------------------------------------------------------
# Màn «Nhóm chat» của Trợ lý AI trên ERP v2 (ai-CR-123)
#
# Hai lớp người xem (đại ca chốt 08/10):
#   - Ai cũng xem được nhóm MÌNH là thành viên (cùng luật bot: `groups.can_read`) — không cần khóa quyền.
#   - Người có `agent_group.read` (quản lý bot AI) thấy MỌI nhóm, kể cả nội dung; mở nội dung nhóm mình không phải
#     thành viên thì ghi nhật ký `tab_agent_group_view`. `agent_group.write` = phân loại mọi nhóm, ngừng ghi nhóm,
#     đăng nhập Zalo công ty. Chủ nhóm (người thêm bot) tự phân loại nhóm của mình.
# ---------------------------------------------------------------------------
GROUP_ENTITY = "agent_group"
GROUP_HOURS_MAX = 24 * 90


def _group_rights(db: Session, user) -> tuple[bool, bool]:
    from app.core.auth import user_has_permission

    return (user_has_permission(db, user, GROUP_ENTITY, "read"), user_has_permission(db, user, GROUP_ENTITY, "write"))


def _viewable_group(db: Session, user, group_id: int):
    """Nhóm người gọi được xem; không có / không được xem đều trả 404 (không lộ nhóm tồn tại)."""
    from . import groups

    manager, writer = _group_rights(db, user)
    g = groups.by_id(db, group_id)
    if g is None or not groups.is_viewer(db, user.id, g, manager=manager):
        raise HTTPException(404, "Không tìm thấy nhóm")
    return g, manager, writer


def _user_labels(db: Session, ids) -> dict[int, str]:
    from . import erp

    out: dict[int, str] = {}
    for uid in {int(i) for i in ids if i}:
        try:
            u = erp.user_by_id(db, uid)
            out[uid] = erp.describe(db, u)[0] if u is not None else f"#{uid}"
        except Exception:  # noqa: BLE001 — tên chỉ để hiển thị
            out[uid] = f"#{uid}"
    return out


@router.get("/groups/meta")
def group_meta(user=Depends(get_current_user), db: Session = Depends(get_db)):
    from . import groups
    from .constants import GROUP_CATEGORY_LABELS

    manager, writer = _group_rights(db, user)
    return success({
        "categories": [{"value": k, "label": v} for k, v in GROUP_CATEGORY_LABELS.items()],
        "channels": [{"value": k, "label": v} for k, v in groups.CHANNEL_LABELS.items()],
        "can_view_all": manager, "can_manage": writer,
        "retention_days": int(settings.AGENT_GROUP_RETENTION_DAYS),
        "zalo_enabled": bool(settings.AGENT_ZALO_LISTENER_URL),
    })


@router.get("/groups")
def list_groups(scope: str = Query("mine", pattern="^(mine|all)$"), channel: str = Query("", max_length=20),
                category: int | None = Query(None, ge=0, le=99), q: str = Query("", max_length=100),
                include_inactive: bool = False, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from . import groups

    manager, writer = _group_rights(db, user)
    items = groups.list_for_web(db, user.id, manager=manager, scope=scope, channel=channel, category=category, q=q,
                                include_inactive=include_inactive and manager)
    names = _user_labels(db, [i["owner_user_id"] for i in items])
    for i in items:
        i["owner_label"] = names.get(i["owner_user_id"], "")
        i["can_edit"] = writer or i["is_owner"]
    return success({"items": items, "total": len(items), "can_view_all": manager, "can_manage": writer})


@router.get("/groups/{group_id}")
def get_group(group_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from . import groups

    g, manager, writer = _viewable_group(db, user, group_id)
    item = next((i for i in groups.list_for_web(db, user.id, manager=manager, scope="all", include_inactive=True)
                 if i["id"] == g.id), None)
    if item is None:
        raise HTTPException(404, "Không tìm thấy nhóm")
    item["owner_label"] = _user_labels(db, [item["owner_user_id"]]).get(item["owner_user_id"], "")
    item["can_edit"] = writer or item["is_owner"]
    item["can_pause"] = writer
    return success(item)


@router.get("/groups/{group_id}/messages")
def group_messages(group_id: int, before_id: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
                   q: str = Query("", max_length=100), files_only: bool = False,
                   user=Depends(get_current_user), db: Session = Depends(get_db)):
    from . import groups

    g, manager, _ = _viewable_group(db, user, group_id)
    groups.record_view(db, g, user.id, "tệp" if files_only else "tin nhắn", manager=manager)
    data = groups.messages_page(db, g, before_id=before_id, limit=limit, q=q, files_only=files_only)
    db.commit()
    return success(data)


@router.get("/groups/{group_id}/files/{message_id}")
def group_file(group_id: int, message_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Tải tệp gửi trong nhóm (bot tải hộ từ Telegram / Zalo). Tệp chỉ lấy được khi còn trong hạn giữ của kênh."""
    from urllib.parse import quote

    from fastapi.responses import Response

    from . import groups

    g, manager, _ = _viewable_group(db, user, group_id)
    row = groups.file_by_ref(db, g, message_id)
    if row is None:
        raise HTTPException(404, "Không thấy tệp này trong nhóm (hoặc đã quá hạn giữ)")
    f = row.file or {}
    try:
        data, _ = telegram.download_file(str(f.get("file_id") or ""),
                                         max_bytes=int(settings.AGENT_FILE_MAX_MB) * 1024 * 1024)
    except telegram.TelegramError as e:
        raise HTTPException(409, f"Không tải được tệp: {e}") from None
    groups.record_view(db, g, user.id, "tải tệp", manager=manager)
    db.commit()
    name = str(f.get("name") or "tep")
    return Response(content=data, media_type=str(f.get("mime") or "application/octet-stream"),
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


@router.get("/groups/{group_id}/summaries")
def group_summaries(group_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from . import groups

    g, manager, _ = _viewable_group(db, user, group_id)
    items = groups.summaries(db, g)
    names = _user_labels(db, [i["user_id"] for i in items])
    for i in items:
        i["user_label"] = names.get(i["user_id"], "")
    groups.record_view(db, g, user.id, "bản tóm tắt", manager=manager)
    db.commit()
    return success({"items": items})


class GroupSummarizeIn(BaseModel):
    hours: int = 24


@router.post("/groups/{group_id}/summarize")
def summarize_group(group_id: int, body: GroupSummarizeIn, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    from app.modules.assistant import usage

    from . import groups

    g, manager, _ = _viewable_group(db, user, group_id)
    hours = max(1, min(int(body.hours or 24), GROUP_HOURS_MAX))
    try:
        usage.check_daily_limit(db, user)
    except usage.QuotaExceeded as e:
        raise HTTPException(429, str(e)) from None
    groups.record_view(db, g, user.id, "tóm tắt", manager=manager)
    out = groups.summarize_now(db, g, user, hours=hours)
    db.commit()
    if out["empty"]:
        return success(out, f"Nhóm không có tin nào trong {hours} giờ qua")
    return success(out, "Đã tóm tắt và lưu lại")


class GroupPatchIn(BaseModel):
    category: int | None = None
    paused: bool | None = None


@router.patch("/groups/{group_id}")
def update_group(group_id: int, body: GroupPatchIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from .constants import GROUP_CATEGORY_LABELS

    g, _manager, writer = _viewable_group(db, user, group_id)
    is_owner = bool(g.owner_user_id and int(g.owner_user_id) == int(user.id))
    if body.category is not None:
        if not (writer or is_owner):
            raise HTTPException(403, "Chỉ chủ nhóm hoặc người quản lý bot AI được phân loại nhóm")
        if body.category not in GROUP_CATEGORY_LABELS:
            raise HTTPException(422, "Loại nhóm không hợp lệ")
        g.category = int(body.category)
    if body.paused is not None:
        if not writer:
            raise HTTPException(403, "Chỉ người quản lý bot AI được ngừng / mở lại ghi nhóm")
        g.paused = bool(body.paused)
    g.updated_by = int(user.id)
    db.commit()
    return success({"id": g.id, "category": int(g.category or 0), "paused": bool(g.paused)}, "Đã lưu")


@router.get("/groups/{group_id}/views")
def group_views(group_id: int, user=Depends(require(GROUP_ENTITY, "read")), db: Session = Depends(get_db)):
    from . import groups

    g, _, _ = _viewable_group(db, user, group_id)
    items = groups.views(db, g)
    names = _user_labels(db, [i["user_id"] for i in items])
    for i in items:
        i["user_label"] = names.get(i["user_id"], "")
    return success({"items": items})


@router.get("/zalo/status")
def zalo_status(user=Depends(require(GROUP_ENTITY, "read")), db: Session = Depends(get_db)):
    """Tình trạng tài khoản Zalo công ty (ai-CR-122). Ảnh QR chỉ trả cho người có `agent_group.write`."""
    from app.core.auth import user_has_permission

    from . import zalo_account

    if not settings.AGENT_ZALO_LISTENER_URL:
        return success({"enabled": False, "state": "off"})
    try:
        st = zalo_account.status()
    except zalo_account.ZaloAccountError as e:
        return success({"enabled": True, "state": "unreachable", "reason": str(e)})
    out = {k: st.get(k) for k in ("state", "name", "groups", "queued", "reason")}
    out["enabled"] = True
    out["qr_image"] = st.get("qr_image") or "" if user_has_permission(db, user, GROUP_ENTITY, "write") else ""
    return success(out)


@router.post("/zalo/login")
def zalo_login(user=Depends(require(GROUP_ENTITY, "write"))):
    from . import zalo_account

    try:
        zalo_account.request_login()
    except zalo_account.ZaloAccountError as e:
        raise HTTPException(409, str(e)) from None
    return success(None, "Đang lấy mã QR — quét bằng điện thoại giữ số Zalo công ty")


@router.post("/zalo/refresh-groups")
def zalo_refresh_groups(user=Depends(require(GROUP_ENTITY, "write"))):
    from . import zalo_account

    try:
        zalo_account.refresh_groups()
    except zalo_account.ZaloAccountError as e:
        raise HTTPException(409, str(e)) from None
    return success(None, "Đang đồng bộ lại nhóm và thành viên Zalo")
