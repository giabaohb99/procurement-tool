"""Entity (khóa phân quyền) → model SQLAlchemy, để soi phạm vi một bản ghi.

`apply_scope`/`get_scoped` đều nhận sẵn `model` từ nơi gọi, nên phần lớn mã
không cần bảng này. Nó sinh ra cho những chỗ chỉ cầm được **TÊN entity** dưới
dạng chuỗi — tức là các endpoint nói VỀ chứng từ của module khác thay vì sở hữu
chứng từ nào. Chỗ đầu tiên là nhật ký thao tác (`/api/audit-logs`): tham số
`entity=<chuỗi>` đến từ URL, không có model nào để mà lọc.

Cùng khuôn hai bảng đã có — `core/file_registry.FILE_POLICY` (đính kèm) và
`core/comment_registry.doc_model` (bình luận) — nhưng ở đây phủ **mọi** entity
có lọc phạm vi thật, không riêng một phân hệ.

Hai luật:

* **Import bên trong hàm.** Import ở đầu tệp là dựng vòng import với các module
  nghiệp vụ (chúng đều `from app.core...`).
* **Entity khai `PUBLIC` ở `SCOPE_FIELDS` KHÔNG có mặt ở đây.** Không phải bỏ
  sót: `apply_scope` không sinh mệnh đề nào cho chúng, nên tra ra model cũng
  không lọc được gì. Ai đọc `model_of(...) is None` phải hiểu là "entity này
  không lọc theo dòng", chứ không phải "chưa khai".
"""

#  entity → (đường dẫn module, tên lớp). Giữ đúng thứ tự của `SCOPE_FIELDS`
#  trong `core/scoping.py` để hai bảng đọc song song được.
ENTITY_MODEL_PATHS: dict[str, tuple[str, str]] = {
    "purchase_request": ("app.modules.purchase_request.model", "PurchaseRequest"),
    "survey_request": ("app.modules.survey_request.model", "SurveyRequest"),
    "purchase_order": ("app.modules.purchase_order.model", "PurchaseOrder"),
    "goods_receipt": ("app.modules.goods_receipt.model", "GoodsReceipt"),
    "payable": ("app.modules.payable.model", "Payable"),
    "payment_request": ("app.modules.payment_request.model", "PaymentRequest"),
    "contract": ("app.modules.contract.model", "Contract"),
    "inventory": ("app.modules.inventory.model", "Inventory"),
    "survey": ("app.modules.survey.model", "Survey"),
    "employee": ("app.modules.employee.model", "Employee"),
    "user": ("app.modules.user.model", "User"),
    "company": ("app.modules.company.model", "Company"),
    "department": ("app.modules.department.model", "Department"),
    "ticket": ("app.modules.ticket.model", "Ticket"),
    "document": ("app.modules.document.model", "Document"),
    "document_book": ("app.modules.doc_catalog.book_model", "DocumentBook"),
    "approval_flow": ("app.modules.approval.flow_model", "ApprovalFlow"),
    "seal_request": ("app.modules.seal_request.model", "SealRequest"),
    "vehicle_booking": ("app.modules.vehicle_booking.model", "VehicleBooking"),
    "leave_request": ("app.modules.leave.request_model", "LeaveRequest"),
    "leave_balance": ("app.modules.leave.balance_model", "LeaveBalance"),
    "room_booking": ("app.modules.meeting_room.model", "RoomBooking"),
}


def model_of(entity: str):
    """Model của entity — `None` nếu entity khai `PUBLIC` hoặc không tồn tại.

    `None` KHÔNG phải lỗi, và cũng không phải "cho qua": nơi gọi tự quyết định
    làm gì với nó. Nhật ký chọn cho qua (đã có lớp quyền vai trò chặn trước);
    chỗ khác có thể chọn chặn.
    """
    entry = ENTITY_MODEL_PATHS.get(entity)
    if not entry:
        return None
    from importlib import import_module

    module, name = entry
    return getattr(import_module(module), name)
