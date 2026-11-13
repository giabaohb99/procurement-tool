"""Phần THANH TOÁN NGHỈ PHÉP của `my_leave_summary` (duoc-CR-719, D8a): phiếu của CHÍNH người hỏi, chỉ số NGÀY + trạng thái.

KHÔNG có số tiền: tiền ÷ ngày = lương ngày, mà chỉ chính chủ / kế toán được xem. Trạng thái chi lấy từ YCTT (mã + nhãn).
Không có công cụ soạn nháp: muốn thanh toán thì mở màn Nghỉ phép ▸ Thanh toán nghỉ phép.
"""
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (LEAVE_ENCASHMENT_REASON_LABELS, LEAVE_ENCASHMENT_STATUS_LABELS, label)
from app.modules.leave.encashment_model import LeaveEncashment

DETAIL_URL = "/hr/leave-encashments/{id}"


def my_encashments(db, employee_id: int, year: int, limit: int) -> list[dict]:
    """Phiếu thanh toán nghỉ phép của CHÍNH một nhân sự trong năm quỹ `year` (mới nhất trước). Lọc cứng theo `employee_id`."""
    from app.modules.payment_request import service as pay_service
    from app.modules.payment_request.model import PaymentRequest

    rows = (db.query(LeaveEncashment)
            .filter(LeaveEncashment.employee_id == employee_id, LeaveEncashment.is_deleted.is_(False),
                    LeaveEncashment.balance_year == year)
            .order_by(LeaveEncashment.id.desc()).limit(limit).all())
    pay_ids = {r.payment_request_id for r in rows if r.payment_request_id}
    pay = dict(db.query(PaymentRequest.id, PaymentRequest.status).filter(
        PaymentRequest.id.in_(pay_ids), PaymentRequest.is_deleted.is_(False)).all()) if pay_ids else {}
    names = dict(db.query(LeaveType.id, LeaveType.name).filter(
        LeaveType.id.in_({r.leave_type_id for r in rows})).all()) if rows else {}
    return [{
        "code": r.code, "leave_type": names.get(r.leave_type_id, ""), "balance_year": r.balance_year,
        "days": r.days, "reason_kind": r.reason_kind,
        "reason_kind_label": label(LEAVE_ENCASHMENT_REASON_LABELS, r.reason_kind),
        "status": r.status, "status_label": label(LEAVE_ENCASHMENT_STATUS_LABELS, r.status),
        #  Trạng thái chi đọc từ YCTT (không lưu hai nơi); rỗng = chưa có YCTT. Tuyệt đối không trả `total`.
        "payment_status": pay.get(r.payment_request_id, ""),
        "payment_status_label": str(pay_service.STATUS_LABELS.get(pay.get(r.payment_request_id, ""), "")),
        #  duoc-CR-757: bỏ `decision_note` — chữ tự do của người duyệt, có thể ghi đơn giá / số tiền (lộ lương ngày).
        "url": DETAIL_URL.format(id=r.id),
    } for r in rows]
