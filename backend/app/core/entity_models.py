"""Entity (khóa phân quyền) -> model SQLAlchemy, để soi phạm vi một bản ghi.

`apply_scope` nhận sẵn `model` từ nơi gọi, nên phần lớn mã không cần bảng này. Nó sinh
ra cho những chỗ chỉ cầm được TÊN entity dưới dạng chuỗi — các endpoint nói VỀ chứng từ
của module khác thay vì sở hữu chứng từ nào. Chỗ đầu tiên là nhật ký thao tác
(`/api/audit-logs`, bao-CR-313): tham số `entity=<chuỗi>` đến từ URL, không có model
nào để mà lọc.

Hai luật:

* Import bên trong hàm. Import ở đầu tệp là dựng vòng import với các module nghiệp vụ
  (chúng đều `from app.core...`).
* Chỉ khai entity CÓ trong `SCOPE_FIELDS` (`core/scoping.py`). Entity không có ở đó thì
  `apply_scope` cũng không sinh mệnh đề nào, tra ra model cũng không lọc được gì. Ai đọc
  `model_of(...) is None` phải hiểu là "entity này không lọc theo dòng", không phải
  "chưa khai".

Bản trên nhánh `erp-v2` dài hơn (văn thư, nghỉ phép, đặt phòng...); bản này chỉ có các
entity đang chạy ở prod.
"""

#  entity -> (đường dẫn module, tên lớp). Giữ đúng thứ tự của `SCOPE_FIELDS`.
ENTITY_MODEL_PATHS: dict[str, tuple[str, str]] = {
    "purchase_request": ("app.modules.purchase_request.model", "PurchaseRequest"),
    "survey_request": ("app.modules.survey_request.model", "SurveyRequest"),
    "purchase_order": ("app.modules.purchase_order.model", "PurchaseOrder"),
    "payable": ("app.modules.payable.model", "Payable"),
    "payment_request": ("app.modules.payment_request.model", "PaymentRequest"),
    "inventory": ("app.modules.inventory.model", "Inventory"),
    "survey": ("app.modules.survey.model", "Survey"),
    "employee": ("app.modules.employee.model", "Employee"),
    "ticket": ("app.modules.ticket.model", "Ticket"),
}


def model_of(entity: str):
    """Model của entity — `None` nếu entity không lọc theo dòng hoặc không tồn tại.

    `None` KHÔNG phải lỗi, và cũng không phải "cho qua": nơi gọi tự quyết định làm gì
    với nó. Nhật ký chọn cho qua (đã có lớp quyền vai trò chặn trước).
    """
    entry = ENTITY_MODEL_PATHS.get(entity)
    if not entry:
        return None
    from importlib import import_module

    module, name = entry
    return getattr(import_module(module), name)
