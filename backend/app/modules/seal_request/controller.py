"""API Duyệt dấu (Yêu cầu đóng dấu).

Gác hai trục như mọi module: `require("seal_request", action)` cho quyền hành động,
`apply_scope`/`get_scoped` bó phạm vi theo công ty/phòng ban/người tạo. Tệp chứng từ có
chữ ký sống đi qua module `attachment` dùng chung (entity="seal_request").
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped

from . import approval_bridge, service
from .model import SealRequest
from .schema import (
    CompleteSealIn,
    ReasonIn,
    SealRequestCreate,
    SealRequestUpdate,
)

router = APIRouter(prefix="/api/seal-requests", tags=["seal-request"])


def _with_reason(action: str, reason: str) -> str:
    reason = (reason or "").strip()
    return f"{action} — Lý do: {reason}" if reason else action


def _scoped_or_404(db: Session, rid: int, user, action: str) -> SealRequest:
    obj = get_scoped(db, SealRequest, "seal_request", rid,
                     user, get_perm_profile(db, user), action)
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy yêu cầu đóng dấu")
    return obj


@router.get("")
def list_seal_requests(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("seal_request", "read")),
):
    query = db.query(SealRequest).filter(SealRequest.is_deleted == False)  # noqa: E712
    query = apply_filters(query, SealRequest, request, service.FILTERABLE)
    query = service.apply_keyword_search(query, request.query_params.get("search"))
    query = apply_scope(query, SealRequest, "seal_request", user, get_perm_profile(db, user))
    query = apply_sort_from_request(query, SealRequest, request, default=SealRequest.id.desc())
    total = query.count()
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": service.serialize_seal_requests(db, items)})


@router.get("/approvers")
def list_approvers(db: Session = Depends(get_db),
                   user=Depends(require("seal_request", "create"))):
    """Trưởng bộ phận có quyền phê duyệt (để chọn), mặc định = TBP của người tạo."""
    return success(service.approver_options(db, user))


@router.get("/{rid}")
def get_seal_request(rid: int, db: Session = Depends(get_db),
                     user=Depends(require("seal_request", "read"))):
    obj = _scoped_or_404(db, rid, user, "read")
    return success(service.serialize_seal_request(db, obj))


@router.post("")
def create_seal_request(
    data: SealRequestCreate,
    background_tasks: BackgroundTasks,
    submit: bool = Query(False, description="true = gửi duyệt luôn; false = lưu nháp"),
    db: Session = Depends(get_db),
    user=Depends(require("seal_request", "create")),
):
    obj = service.create_seal_request(db, data, user, submit, background_tasks)
    audit_record(db, user.id, "seal_request", obj.id, "create",
                 f"Tạo yêu cầu đóng dấu {obj.code}")
    msg = "Đã gửi duyệt yêu cầu đóng dấu" if submit else "Đã lưu nháp yêu cầu đóng dấu"
    return success(service.serialize_seal_request(db, obj), msg, 201)


@router.patch("/{rid}")
def update_seal_request(
    rid: int,
    data: SealRequestUpdate,
    background_tasks: BackgroundTasks,
    submit: bool = Query(False, description="true = lưu rồi gửi duyệt"),
    db: Session = Depends(get_db),
    user=Depends(require("seal_request", "write")),
):
    obj = _scoped_or_404(db, rid, user, "write")
    obj = service.update_seal_request(db, obj, data, user, submit, background_tasks)
    audit_record(db, user.id, "seal_request", obj.id, "update",
                 f"Cập nhật yêu cầu đóng dấu {obj.code}")
    return success(service.serialize_seal_request(db, obj), "Đã cập nhật")


@router.post("/{rid}/submit")
def submit_seal_request(rid: int, background_tasks: BackgroundTasks,
                        db: Session = Depends(get_db),
                        user=Depends(require("seal_request", "write"))):
    """Gửi duyệt phiếu Nháp / bị Yêu cầu chỉnh sửa (kiểm dữ liệu + ≥1 chứng từ chữ ký sống)."""
    obj = _scoped_or_404(db, rid, user, "write")
    obj = service.submit_seal_request(db, obj, user, background_tasks)
    audit_record(db, user.id, "seal_request", obj.id, "update",
                 f"Gửi duyệt yêu cầu đóng dấu {obj.code}")
    return success(service.serialize_seal_request(db, obj), "Đã gửi duyệt")


# --- Cổng 1: Trưởng bộ phận (approve) --------------------------------------

@router.post("/{rid}/approve")
def approve_seal(rid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                 user=Depends(require("seal_request", "approve"))):
    obj = _scoped_or_404(db, rid, user, "approve")
    approval_bridge.block_legacy_path(db, obj)  # đang chạy luồng nhiều bước thì chặn đường tắt
    obj = service.approve_seal(db, obj, user, background_tasks)
    audit_record(db, user.id, "seal_request", obj.id, "approve",
                 f"Duyệt yêu cầu đóng dấu {obj.code}")
    return success(service.serialize_seal_request(db, obj), "Đã duyệt yêu cầu")


@router.post("/{rid}/return")
def return_seal(rid: int, data: ReasonIn, background_tasks: BackgroundTasks,
                db: Session = Depends(get_db),
                user=Depends(require("seal_request", "approve"))):
    obj = _scoped_or_404(db, rid, user, "approve")
    approval_bridge.block_legacy_path(db, obj)
    obj = service.return_seal(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "seal_request", obj.id, "update",
                 _with_reason("Yêu cầu chỉnh sửa", data.reason))
    return success(service.serialize_seal_request(db, obj), "Đã trả lại để chỉnh sửa")


@router.post("/{rid}/reject")
def reject_seal(rid: int, data: ReasonIn, background_tasks: BackgroundTasks,
                db: Session = Depends(get_db),
                user=Depends(require("seal_request", "approve"))):
    obj = _scoped_or_404(db, rid, user, "approve")
    approval_bridge.block_legacy_path(db, obj)
    obj = service.reject_seal(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "seal_request", obj.id, "cancel",
                 _with_reason("Từ chối yêu cầu", data.reason))
    return success(service.serialize_seal_request(db, obj), "Đã từ chối yêu cầu")


# --- Cổng 2: Văn thư (write) -----------------------------------------------

@router.post("/{rid}/complete")
def complete_seal(rid: int, data: CompleteSealIn, background_tasks: BackgroundTasks,
                  db: Session = Depends(get_db),
                  user=Depends(require("seal_request", "write"))):
    """Văn thư đóng dấu xong → Hoàn thành."""
    obj = _scoped_or_404(db, rid, user, "write")
    obj = service.complete_seal(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "seal_request", obj.id, "update",
                 f"Hoàn thành (đóng dấu) yêu cầu {obj.code}")
    return success(service.serialize_seal_request(db, obj), "Đã hoàn thành đóng dấu")


@router.post("/{rid}/return-clerk")
def return_seal_clerk(rid: int, data: ReasonIn, background_tasks: BackgroundTasks,
                      db: Session = Depends(get_db),
                      user=Depends(require("seal_request", "write"))):
    """Văn thư YÊU CẦU CHỈNH SỬA (phiếu Đã duyệt) — vd chụp lại chữ ký rõ hơn."""
    obj = _scoped_or_404(db, rid, user, "write")
    obj = service.return_seal(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "seal_request", obj.id, "update",
                 _with_reason("Yêu cầu chỉnh sửa (Văn thư)", data.reason))
    return success(service.serialize_seal_request(db, obj), "Đã trả lại để chỉnh sửa")


@router.post("/{rid}/reject-clerk")
def reject_seal_clerk(rid: int, data: ReasonIn, background_tasks: BackgroundTasks,
                      db: Session = Depends(get_db),
                      user=Depends(require("seal_request", "write"))):
    """Văn thư TỪ CHỐI (phiếu Đã duyệt)."""
    obj = _scoped_or_404(db, rid, user, "write")
    obj = service.reject_seal(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "seal_request", obj.id, "cancel",
                 _with_reason("Từ chối (Văn thư)", data.reason))
    return success(service.serialize_seal_request(db, obj), "Đã từ chối yêu cầu")


@router.delete("/{rid}")
def delete_seal_request(rid: int, db: Session = Depends(get_db),
                        user=Depends(require("seal_request", "delete"))):
    obj = _scoped_or_404(db, rid, user, "delete")
    obj.is_deleted = True
    obj.updated_by = user.id
    db.commit()
    audit_record(db, user.id, "seal_request", obj.id, "delete",
                 f"Xóa yêu cầu đóng dấu {obj.code}")
    return success(None, "Đã xóa")
