"""CỔNG B — ERP mở cho DỊCH VỤ AI (ai-CR-119, phase S-2; hợp đồng ở doc/agent-hub/14-cong-erp-api.md).

Mọi đường ở đây:
  - KHÔNG có token người dùng — xác thực bằng chữ ký máy-nói-máy (`core/agent_signature.py`), header `X-Agent-User` là id
    tài khoản ERP mà lượt gọi chạy DƯỚI QUYỀN. ERP tra tài khoản đó (phải đang hoạt động), rồi mọi công cụ / nháp phiếu
    chạy y như người đó tự bấm trên web: `require` + `apply_scope` ở ngay trong công cụ.
  - Gói gọn `agent_hub.erp._Local` — cùng mã với chế độ embedded, không có nhánh nghiệp vụ riêng.
  - Chỉ gắn khi `AGENT_MODE=erp` (xem app/main.py). Ở chế độ embedded không ai cần cổng này.
"""
from __future__ import annotations

import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import agent_signature
from app.core.database import get_db
from app.core.response import success
from app.modules.agent_hub.erp import _Local as L
from app.modules.assistant.change_model import ChangeSource

log = logging.getLogger("app.agent_gateway")
#  ai-CR-182: kênh ghi vào sổ thay đổi cho mọi lượt ghi đi qua cổng B. Dịch vụ AI hiện chỉ nhận lệnh từ Telegram
#  (Zalo hướng B còn chờ — đại ca chốt 09/10 «Telegram trước, Zalo sau»); khi mở Zalo thì thêm header kênh ở
#  `agent_hub/erp._Remote._call` rồi đọc ở đây thay hằng số.
GATEWAY_SOURCE = int(ChangeSource.TELEGRAM)
router = APIRouter(prefix="/api/agent-gw", tags=["agent-gateway"])


async def _verified(request: Request) -> int:
    body = await request.body()
    ok, reason, user_id = agent_signature.verify(request.method, request.url.path, body, request.headers)
    if not ok:
        log.warning("agent_gateway: từ chối %s %s — %s", request.method, request.url.path, reason)
        raise HTTPException(401, f"Chữ ký dịch vụ AI không hợp lệ: {reason}")
    return user_id


async def gateway_user(request: Request, db: Session = Depends(get_db)):
    """Tài khoản ERP đứng sau lượt gọi — BẮT BUỘC có và đang hoạt động."""
    user_id = await _verified(request)
    user = L.user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, "Tài khoản không tồn tại hoặc đã bị khóa")
    return user


async def gateway_signed(request: Request) -> int:
    """Chỉ cần chữ ký đúng (đường không chạy dưới quyền ai: cấu hình, chuông, phiếu hỗ trợ theo lô)."""
    return await _verified(request)


# --- người dùng ---------------------------------------------------------------------------------------------------
@router.get("/ping")
async def ping(_: int = Depends(gateway_signed)):
    return success({"ok": True})


@router.get("/me")
def me(user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success(L.snapshot(db, user).to_dict())


class LookupIn(BaseModel):
    ids: list[int] = Field(default_factory=list, max_length=50)
    emails: list[str] = Field(default_factory=list, max_length=50)


@router.post("/users/lookup")
def users_lookup(body: LookupIn, _: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    out = []
    for uid in body.ids:
        u = L.user_by_id(db, uid)
        if u is not None:
            out.append(L.snapshot(db, u).to_dict())
    for email in body.emails:
        u = L.user_by_email(db, email)
        if u is not None:
            out.append(L.snapshot(db, u).to_dict())
    return success(out)


@router.get("/users/search")
def users_search(q: str = Query("", max_length=120), _: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    return success([L.snapshot(db, u).to_dict() for u in L.search_users(db, q)[:20]])


class CanIn(BaseModel):
    entity: str = Field(max_length=60)
    action: str = Field(max_length=20)


@router.post("/can")
def can(body: CanIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success({"ok": L.can(db, user, body.entity, body.action)})


@router.get("/settings")
def settings_snapshot(_: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    return success(L.settings_snapshot(db))


class SettingRawIn(BaseModel):
    key: str = Field(max_length=60)
    value: str = Field(max_length=512_000)


def _raw_key(key: str) -> str:
    from app.modules.agent_hub.erp import SETTING_RAW_KEYS

    if key not in SETTING_RAW_KEYS:
        raise HTTPException(403, "Khóa cấu hình này không mở qua cổng")
    return key


@router.get("/settings/raw")
def setting_raw_get(key: str = Query(max_length=60), _: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    """ai-CR-128: sổ JSON trong tab_setting mà bot đọc (thuật ngữ, đề xuất thuật ngữ, chỗ Trợ lý thiếu chức năng)."""
    return success({"value": L.setting_raw_get(db, _raw_key(key))})


@router.put("/settings/raw")
def setting_raw_put(body: SettingRawIn, user_id: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    L.setting_raw_put(db, _raw_key(body.key), body.value, user_id)
    return success(None)


class GlossaryIn(BaseModel):
    texts: list[str] = Field(default_factory=list, max_length=10)


@router.post("/glossary/block")
def glossary_block(body: GlossaryIn, _: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    return success({"block": L.glossary_block(db, [t[:4000] for t in body.texts]) or ""})


# --- công cụ của Trợ lý ---------------------------------------------------------------------------------------------
@router.get("/tools")
def tools(user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success([{"name": d.name, "description": d.description, "parameters": d.parameters} for d in L.tool_defs(db, user)])


class ToolRunIn(BaseModel):
    name: str = Field(max_length=80)
    args: dict = Field(default_factory=dict)


@router.post("/tools/run")
def tools_run(body: ToolRunIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    try:
        return success(L.run_tool(db, user, body.name, body.args))
    except Exception as e:  # noqa: BLE001 — lỗi công cụ phải thành dict để model tự sửa, không thành 500
        log.exception("agent_gateway: công cụ %s hỏng", body.name)
        return success({"error": f"Lỗi khi chạy công cụ: {str(e)[:300]}"})


# --- Kho skill AI (bao-CR-622, K2 doc/erp/21) — chỉ đọc, dưới quyền người cầm khóa MCP ---------------------------------
@router.get("/skills")
def skills_list(query: str = Query("", max_length=120), skill_set: str = Query("", max_length=150),
                user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success(L.skill_list(db, user, query, skill_set))


@router.get("/skills/read")
def skills_read(name: str = Query(..., max_length=160), user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success(L.skill_read(db, user, name))


@router.get("/skills/file")
def skills_file(name: str = Query(..., max_length=160), path: str = Query(..., max_length=200),
                user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success(L.skill_file(db, user, name, path))


# --- tạo phiếu từ nháp ------------------------------------------------------------------------------------------------
class DraftCreateIn(BaseModel):
    kind: str = Field(max_length=20)
    draft: dict


@router.post("/draft/create")
def draft_create_(body: DraftCreateIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    from app.modules.agent_hub.draft_create import DraftError

    try:
        code, oid = L.create_draft(db, user, body.kind, body.draft, source=GATEWAY_SOURCE)
    except DraftError as e:
        return success({"error": str(e)})
    return success({"code": code, "id": oid})


class DraftSubmitIn(BaseModel):
    kind: str = Field(max_length=20)
    id: int


@router.post("/draft/submit")
def draft_submit(body: DraftSubmitIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    from app.modules.agent_hub.draft_create import DraftError

    try:
        L.submit_draft(db, user, body.kind, body.id, source=GATEWAY_SOURCE)
    except DraftError as e:
        return success({"error": str(e)})
    return success({"ok": True})


#  ai-CR-143: đơn nháp của CHÍNH người gọi (chữ ký mang user_id) — xem / dùng lại đơn nghỉ cùng ngày / xóa bớt.
@router.get("/draft/mine")
def draft_mine(user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success(L.my_drafts(db, user))


class DraftUpdateIn(BaseModel):
    kind: str = Field(max_length=20)
    id: int
    draft: dict


@router.post("/draft/update")
def draft_update(body: DraftUpdateIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    from app.modules.agent_hub.draft_create import DraftError

    if body.kind != "leave":
        return success({"error": "chỉ đơn nghỉ phép dùng lại được bản nháp cũ"})
    try:
        return success({"code": L.update_leave_draft(db, user, body.id, body.draft, source=GATEWAY_SOURCE)})
    except DraftError as e:
        return success({"error": str(e)})


class DraftReuseIn(BaseModel):
    kind: str = Field(max_length=20)
    id: int
    draft: dict
    mode: str = Field(max_length=10)


#  ai-CR-156: dùng lại phiếu nháp YCMH / YCBG của chính người gọi (thêm dòng vào / ghi đè).
@router.post("/draft/reuse")
def draft_reuse(body: DraftReuseIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    from app.modules.agent_hub.draft_create import DraftError

    try:
        return success(L.update_doc_draft(db, user, body.kind, body.id, body.draft, body.mode, source=GATEWAY_SOURCE))
    except DraftError as e:
        return success({"error": str(e)})


class DraftRef(BaseModel):
    kind: str = Field(max_length=20)
    id: int


class DraftDeleteIn(BaseModel):
    items: list[DraftRef] = Field(default_factory=list, max_length=30)


@router.post("/draft/delete")
def draft_delete(body: DraftDeleteIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success(L.delete_my_drafts(db, user, [i.model_dump() for i in body.items], source=GATEWAY_SOURCE))


#  ai-CR-151: nút «Xác nhận sửa / xóa» trên Telegram. Token Fernet do ERP cấp lúc chạy tool đề xuất; ở đây ERP kiểm
#  lại TOÀN BỘ (token, hạn, đúng người, quyền, phạm vi, trạng thái) đúng như nút trên web.
class ProposalConfirmIn(BaseModel):
    token: str = Field(min_length=1, max_length=8000)


@router.post("/proposal/confirm")
def proposal_confirm(body: ProposalConfirmIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    try:
        return success(L.confirm_proposal(db, user, body.token, source=GATEWAY_SOURCE))
    except HTTPException as e:
        db.rollback()
        return success({"error": str(e.detail), "status": e.status_code})


# --- sổ thay đổi do bot ghi + hoàn tác (ai-CR-182) ------------------------------------------------------------------
#  Của CHÍNH người gọi (chữ ký mang user_id). Hợp đồng: doc/agent-hub/18-so-thay-doi-va-hoan-tac.md.
@router.get("/changes/mine")
def changes_mine(limit: int = Query(20, ge=1, le=100), user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success(L.my_changes(db, user, limit))


class ChangeUndoIn(BaseModel):
    id: int = Field(ge=1)


@router.post("/changes/undo")
def changes_undo(body: ChangeUndoIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    """ERP kiểm lại TOÀN BỘ (hạn 24 giờ, chủ, quyền, phạm vi, trạng thái, dấu phiếu); lỗi nghiệp vụ trả
    `{error, status}` như `/proposal/confirm` để dịch vụ AI ném lại HTTPException."""
    try:
        return success(L.undo_change(db, user, body.id, source=GATEWAY_SOURCE))
    except HTTPException as e:
        db.rollback()
        return success({"error": str(e.detail), "status": e.status_code})


@router.get("/draft/details")
def draft_details(kind: str = Query(max_length=20), id: int = Query(ge=1), _: int = Depends(gateway_signed),
                  db: Session = Depends(get_db)):
    return success(L.created_details(db, kind, id))


# --- phiếu hỗ trợ ----------------------------------------------------------------------------------------------------
class TicketsOpenIn(BaseModel):
    statuses: list[str] = Field(default_factory=list, max_length=10)
    exclude_ids: list[int] = Field(default_factory=list, max_length=5000)
    limit: int = Field(200, ge=1, le=500)


@router.post("/tickets/open")
def tickets_open(body: TicketsOpenIn, _: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    return success(L.tickets_open(db, body.statuses, body.exclude_ids, limit=body.limit))


@router.get("/tickets/max-id")
def tickets_max_id(_: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    return success({"max_id": L.tickets_max_id(db)})


class IdsIn(BaseModel):
    ids: list[int] = Field(default_factory=list, max_length=200)


@router.post("/tickets/by-ids")
def tickets_by_ids(body: IdsIn, _: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    return success(L.tickets_by_ids(db, body.ids))


class TicketNoteIn(BaseModel):
    body: str = Field(max_length=4000)
    status: str = Field(max_length=30)
    clear_assignee: bool = False


@router.post("/tickets/{ticket_id}/note")
def ticket_note(ticket_id: int, body: TicketNoteIn, user_id: int = Depends(gateway_signed),
                db: Session = Depends(get_db)):
    L.ticket_note(db, ticket_id, body.body, status=body.status, by_user_id=user_id, clear_assignee=body.clear_assignee)
    return success({"ok": True})


class TicketCreateIn(BaseModel):
    subject: str = Field(max_length=200)
    department: str = Field("", max_length=100)
    body: str = Field(max_length=4000)


@router.post("/tickets")
def ticket_create(body: TicketCreateIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success(L.create_ticket(db, user, subject=body.subject, department=body.department, body=body.body))


# --- phát khóa AI hộ (ai-CR-212, K4 doc/erp/21 §5.3) ---------------------------------------------------------------
class KeyAdminPeopleIn(BaseModel):
    action: str = Field(pattern="^(read|create|delete)$")
    user_ids: list[int] | None = Field(default=None, max_length=2000)
    department_id: int = Field(default=0, ge=0)
    limit: int = Field(default=2000, ge=1, le=2000)


@router.post("/key-admin/people")
def key_admin_people(body: KeyAdminPeopleIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    people = L.key_admin_people(db, user, body.action, user_ids=body.user_ids, department_id=body.department_id,
                                limit=body.limit)
    return success({"allowed": people is not None, "people": people or []})


class KeyAdminNotifyIn(BaseModel):
    user_ids: list[int] = Field(default_factory=list, max_length=50)
    title: str = Field(max_length=255)
    body: str = Field(default="", max_length=2000)
    link: str = Field(default="", max_length=500)


@router.post("/key-admin/notify")
def key_admin_notify(body: KeyAdminNotifyIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success({"sent": L.notify_users(db, body.user_ids, title=body.title, body=body.body, link=body.link,
                                           by_user_id=int(user.id))})


@router.get("/ai-skill/stats")
def ai_skill_stats(_: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    """ai-CR-213: số bộ / skill đang dùng cho màn Tổng quan (chỉ con số, không nội dung)."""
    return success(L.skill_stats(db))


# --- chuông ----------------------------------------------------------------------------------------------------------
@router.get("/notifications")
def notifications(after_id: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=500),
                  _: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    return success(L.notifications_after(db, after_id, limit))


@router.get("/notifications/max-id")
def notifications_max_id(_: int = Depends(gateway_signed), db: Session = Depends(get_db)):
    return success({"max_id": L.notifications_max_id(db)})


@router.post("/attachments/blocks")
def attachment_blocks(body: IdsIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    try:
        blocks, meta = L.attachment_blocks(db, user, body.ids)
    except (PermissionError, ValueError) as e:
        return success({"error": str(e) or "Không tìm thấy tệp đính kèm"})
    return success({"blocks": blocks, "meta": meta})


# --- tệp báo cáo -----------------------------------------------------------------------------------------------------
@router.get("/files/{file_id}")
def report_file(file_id: int, user=Depends(gateway_user), db: Session = Depends(get_db)):
    f = L.report_file(db, user, file_id)
    if f is None:
        raise HTTPException(404, "Không có tệp này của bạn")
    return Response(content=f["data"], media_type=f["content_type"] or "application/octet-stream",
                    headers={"X-Filename": quote(f["filename"] or "bao-cao.bin")})


# --- nhân sự, dự án --------------------------------------------------------------------------------------------------
@router.get("/employees/match")
def employees_match(name: str = Query("", max_length=120), _: int = Depends(gateway_signed),
                    db: Session = Depends(get_db)):
    return success(L.match_employee(db, name))


@router.get("/projects")
def projects(user=Depends(gateway_user), db: Session = Depends(get_db)):
    return success(L.projects_for(db, user))


# --- kế hoạch việc (bao-CR-616, phase 24.1) --------------------------------------------------------------------------
@router.get("/plan/overview")
def plan_overview(list_id: int = Query(ge=1), user=Depends(gateway_user), db: Session = Depends(get_db)):
    """Cây việc của một kế hoạch, chỉ thành viên bảng mới đọc được (kiểm trong `work/plan_service.overview`)."""
    return success(L.plan_overview(db, user, list_id))


class PlanReplyIn(BaseModel):
    task_id: int = Field(ge=1)
    action: str = Field(max_length=20)
    text: str = Field("", max_length=1000)
    pct: int | None = Field(None, ge=0, le=100)
    score: int | None = Field(None, ge=0, le=10)


@router.post("/plan/reply")
def plan_reply(body: PlanReplyIn, user=Depends(gateway_user), db: Session = Depends(get_db)):
    """Người làm trả lời (nhận / giờ khác / từ chối / xong / tiến độ) — ghi dưới quyền chính người đó."""
    return success(L.plan_reply(db, user, body.task_id, body.action, text=body.text, pct=body.pct, score=body.score))
