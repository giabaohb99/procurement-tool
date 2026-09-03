"""API ĐƠN NGHỈ PHÉP — `/api/leave-requests`.

Gác hai trục như mọi module: `require("leave_request", action)` cho quyền hành
động, `apply_scope(...)` bó phạm vi. Lấy một đơn theo id đi qua `get_scoped` —
`db.get()` bỏ qua sạch bộ lọc, gõ id lên URL là đọc được đơn nghỉ của người
khác kèm lý do nghỉ, thứ riêng tư nhất trong cả hệ này.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record, resolve_actor
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped

from . import (approval_bridge, balance_service, request_serializer,
               request_service, workday_service)
from .catalog_model import LeaveType
from .constants import LR_APPROVED, LR_CANCELLED, LR_PENDING, LR_REJECTED
from .request_model import LeaveRequest
from .schema import LeaveRequestCreate, LeaveRequestUpdate

router = APIRouter(prefix="/api/leave-requests", tags=["leave"])

ENTITY = "leave_request"

#  Ba trạng thái KHÓA hẳn tờ đơn — xem ghi chú ở `get_request`.
DECIDED_FINAL_STATUSES = (LR_APPROVED, LR_REJECTED, LR_CANCELLED)


#  Ba hàm dựng dòng đơn nằm ở `request_serializer` — hộp việc duyệt
#  (`inbox_controller`) dùng chung, xem docstring tệp đó.
def _names(db: Session, employee_ids: set[int]) -> dict[int, str]:
    return request_serializer.names_of(db, employee_ids)


def _dump(db: Session, obj: LeaveRequest, names: dict[int, str],
          types: dict[int, str]) -> dict:
    return request_serializer.dump_request(obj, names, types)


def _type_names(db: Session) -> dict[int, str]:
    return request_serializer.type_names(db)


@router.get("")
def list_requests(
    request: Request,
    pg: dict = Depends(pagination),
    search: str | None = None,
    from_date: str | None = Query(None, description="Lọc theo khoảng: nghỉ TỪ ngày"),
    to_date: str | None = Query(None, description="Lọc theo khoảng: nghỉ ĐẾN ngày"),
    db: Session = Depends(get_db),
    user=Depends(require(ENTITY, "read")),
):
    """Danh sách đơn trong phạm vi người xem («Đơn của tôi» khi phạm vi = own).

    `from_date`/`to_date` lọc theo GIAO NHAU của khoảng, không phải theo cột
    `from_date` đơn lẻ — màn Lịch nghỉ hỏi "tuần này ai nghỉ", và một đơn nghỉ
    từ tuần trước sang tuần này phải lọt vào.
    """
    query = db.query(LeaveRequest).filter(LeaveRequest.is_deleted.is_(False))
    query = apply_filters(query, LeaveRequest, request, request_service.FILTERABLE)
    query = request_service.apply_keyword_search(query, search)
    if from_date:
        query = query.filter(LeaveRequest.to_date >= from_date)
    if to_date:
        query = query.filter(LeaveRequest.from_date <= to_date)
    query = apply_scope(query, LeaveRequest, ENTITY, user, get_perm_profile(db, user))
    query = apply_sort_from_request(query, LeaveRequest, request,
                                    default=LeaveRequest.id.desc())
    total = query.count()
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()

    names = _names(db, {i.employee_id for i in items})
    types = _type_names(db)
    return success({"total": total,
                    "items": [_dump(db, i, names, types) for i in items]})


def _get_or_404(db: Session, rid: int, user, action: str = "read") -> LeaveRequest:
    obj = get_scoped(db, LeaveRequest, ENTITY, rid, user, get_perm_profile(db, user),
                     action)

    #  Người ĐANG được giao ký tờ đơn này đọc được nó, dù phạm vi dữ liệu không
    #  với tới (CR-260). Chỉ mở cho `read`: được giao ký KHÔNG có nghĩa là được
    #  sửa hay xóa đơn của người khác — hai việc đó vẫn phải nằm trong phạm vi.
    if obj is None and action == "read":
        obj = _readable_by_approver(db, rid, user)

    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy đơn nghỉ phép")
    return obj


def _readable_by_approver(db: Session, rid: int, user) -> LeaveRequest | None:
    """Tờ đơn mà người này đang phải ký — `None` nếu họ không có việc treo trên nó."""
    if not approval_bridge.can_read_request(db, rid, user):
        return None
    return db.get(LeaveRequest, rid)


@router.get("/{rid}")
def get_request(rid: int, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "read"))):
    obj = _get_or_404(db, rid, user)
    names = _names(db, {obj.employee_id} | {h.employee_id for h in obj.handovers})
    data = _dump(db, obj, names, _type_names(db))
    #  AI đã chốt tờ đơn này. Lấy từ `updated_by` chứ không thêm cột `decided_by`:
    #  ba trạng thái dưới đây KHÓA hẳn tờ đơn (`check_editable` chặn mọi lượt sửa
    #  sau đó), nên lượt ghi cuối cùng CHÍNH là lượt ra quyết định.
    #
    #  ⚠️ Cố ý BỎ *Trả về chỉnh sửa*: trạng thái đó sửa được, người nộp lưu lại
    #  một cái là `updated_by` thành tên họ — màn hình sẽ khai người nộp tự trả
    #  đơn về cho chính mình.
    #
    #  Chỉ dựng ở đường lấy MỘT đơn — danh sách mà tra thêm mỗi dòng một tên là N+1.
    data["decided_by_name"] = (
        resolve_actor(db, obj.updated_by)
        if obj.decided_at and obj.status in DECIDED_FINAL_STATUSES else ""
    )
    data["handovers"] = request_serializer.dump_handovers(obj, names)
    return success(data)


@router.post("")
def create_request(data: LeaveRequestCreate, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "create"))):
    obj = request_service.create(db, data, user)
    audit_record(db, user.id, ENTITY, obj.id, "create", f"Lập đơn nghỉ phép {obj.code}")
    return success(_dump(db, obj, _names(db, {obj.employee_id}), _type_names(db)),
                   "Đã lưu đơn nghỉ phép")


@router.patch("/{rid}")
def update_request(rid: int, data: LeaveRequestUpdate, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "write"))):
    obj = _get_or_404(db, rid, user, "write")
    obj = request_service.update(db, obj, data, user)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Sửa đơn nghỉ phép {obj.code}")
    return success(_dump(db, obj, _names(db, {obj.employee_id}), _type_names(db)),
                   "Đã cập nhật")


@router.delete("/{rid}")
def delete_request(rid: int, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "delete"))):
    obj = _get_or_404(db, rid, user, "delete")
    code = obj.code
    request_service.soft_delete(db, obj, user)
    audit_record(db, user.id, ENTITY, rid, "delete", f"Xóa đơn nghỉ phép {code}")
    return success(None, "Đã xóa đơn")


@router.post("/{rid}/submit")
def submit_request(rid: int, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "write"))):
    """Gửi duyệt: kiểm đủ phép TRƯỚC, trình bộ máy SAU, rồi mới giữ chỗ quỹ.

    Thứ tự đó là có chủ ý — trình phiếu xong mới phát hiện hết phép thì phải đi
    rút phiếu, và người dùng đã kịp thấy một phiếu duyệt hiện ra rồi biến mất.
    """
    obj = _get_or_404(db, rid, user, "write")
    employee, leave_type = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    obj = request_service.mark_submitted(db, obj, employee, leave_type, user, instance_id)
    audit_record(db, user.id, ENTITY, obj.id, "update",
                 f"Gửi duyệt đơn nghỉ phép {obj.code}")
    return success(_dump(db, obj, _names(db, {obj.employee_id}), _type_names(db)),
                   "Đã gửi duyệt")


@router.post("/{rid}/approve")
def approve_request(rid: int, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "approve"))):
    """Duyệt THẲNG — chỉ dùng khi môi trường chưa khai luồng nhiều bước.

    Đơn đang chạy trong luồng thì chặn: không chặn là mở một đường tắt đi vòng
    qua cả luồng, đúng lỗ hổng đã phải vá cho phân hệ Văn thư.
    """
    obj = _get_or_404(db, rid, user, "approve")
    if obj.status != LR_PENDING:
        raise HTTPException(400, "Chỉ duyệt được đơn đang ở trạng thái Chờ duyệt")
    approval_bridge.block_legacy_path(db, obj)

    #  Dùng lại đúng hook của bộ máy duyệt, không chép luật trừ quỹ ra đây —
    #  chép là hai đường duyệt và một trong hai sẽ quên sinh giấy GNP.
    class _DirectApproval:
        updated_by = user.id
        finish_reason = ""

    approval_bridge._on_approved(db, obj.id, _DirectApproval())
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "approve", f"Duyệt đơn nghỉ phép {obj.code}")
    return success(_dump(db, obj, _names(db, {obj.employee_id}), _type_names(db)),
                   "Đã duyệt đơn")


@router.post("/{rid}/reject")
def reject_request(rid: int, reason: str = Query("", max_length=500),
                   db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "approve"))):
    """Từ chối THẲNG — cùng điều kiện với `/approve`."""
    obj = _get_or_404(db, rid, user, "approve")
    if obj.status != LR_PENDING:
        raise HTTPException(400, "Chỉ từ chối được đơn đang ở trạng thái Chờ duyệt")
    approval_bridge.block_legacy_path(db, obj)

    class _DirectRejection:
        updated_by = user.id
        finish_reason = reason

    approval_bridge._on_rejected(db, obj.id, _DirectRejection())
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Từ chối đơn {obj.code}")
    return success(_dump(db, obj, _names(db, {obj.employee_id}), _type_names(db)),
                   "Đã từ chối đơn")


@router.post("/{rid}/cancel")
def cancel_request(rid: int, reason: str = Query("", max_length=500),
                   db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "cancel"))):
    """Hủy đơn và TRẢ LẠI quỹ — cả đơn đang chờ lẫn đơn đã duyệt.

    Đơn còn nằm trong luồng thì RÚT phiên duyệt trước. Không rút thì hủy xong
    phiên vẫn chạy: người duyệt vẫn thấy việc chờ mình, ký xong là hook
    `on_approved` trừ quỹ cho một tờ đơn đã hủy.

    ⚠️ Cố ý KHÔNG gọi `block_legacy_path` ở đây — xem docstring của hàm đó.
    """
    obj = _get_or_404(db, rid, user, "cancel")
    obj = approval_bridge.cancel_request(db, obj, reason, user)
    audit_record(db, user.id, ENTITY, obj.id, "cancel", f"Hủy đơn nghỉ phép {obj.code}")
    return success(_dump(db, obj, _names(db, {obj.employee_id}), _type_names(db)),
                   "Đã hủy đơn")


# ── Hai endpoint phụ trợ cho FORM ──────────────────────────────────────────────

@router.get("/tools/estimate-days")
def estimate_days(from_date: str, to_date: str,
                  leave_type_id: int = 0,
                  from_session: int = 1, to_session: int = 1,
                  employee_id: int = 0,
                  db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "read"))):
    """Số ngày GỢI Ý cho khoảng đang chọn — form gọi mỗi lần đổi ngày.

    Đặt dưới `/tools/` chứ không để `/estimate-days` trần: đường trần chỉ có một
    đoạn nên nó rơi vào `/{rid}` (khai trước) và ăn lỗi ép kiểu số. Hai đoạn thì
    không đụng nhau, khỏi phải nhớ thứ tự khai route.
    """
    from datetime import date as _date

    employee = request_service.resolve_leave_taker(db, user, employee_id)
    leave_type = (db.get(LeaveType, leave_type_id) if leave_type_id else None)
    days = workday_service.count_leave_days(
        db, _date.fromisoformat(from_date), _date.fromisoformat(to_date),
        from_session, to_session,
        company_id=employee.company_id or 0,
        exclude_holiday=bool(leave_type.exclude_holiday) if leave_type else True)
    return success({"total_days": days})


@router.get("/tools/my-balance")
def my_balance(leave_type_id: int, year: int = 0, employee_id: int = 0,
               db: Session = Depends(get_db),
               user=Depends(require(ENTITY, "read"))):
    """Số phép còn lại — ràng buộc §6.1: form phải hiện con số này lúc nộp.

    Cố tình gác bằng `leave_request.read` chứ không `leave_balance.read`: đây là
    quỹ của CHÍNH người đang nộp (hoặc của người mình đang lập hộ), và ai nộp
    được đơn thì phải thấy được số còn lại — bắt cấp thêm một khóa nữa là chắc
    chắn có người quên cấp, rồi ô đó hiện 0 vĩnh viễn.
    """
    from datetime import date as _date

    employee = request_service.resolve_leave_taker(db, user, employee_id)
    leave_type = request_service.get_leave_type(db, leave_type_id)
    year = year or _date.today().year
    row = balance_service.ensure_balance(db, employee, year, leave_type)
    db.commit()
    return success({
        "employee_id": employee.id,
        "year": year,
        "leave_type_id": leave_type.id,
        "counts_balance": bool(leave_type.counts_balance),
        "total_days": row.total_days,
        "used_days": row.used_days,
        "pending_days": row.pending_days,
        "remaining_days": row.remaining_days,
        #  Q4 — hồ sơ chưa nhập ngày vào làm thì thâm niên tính bằng 0 và con số
        #  trên có thể thiếu. Trả cờ ra để màn hình nói thẳng, đừng để im lặng.
        "missing_hire_date": getattr(employee, "hire_date", None) is None,
    })
