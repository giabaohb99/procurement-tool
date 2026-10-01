from pydantic import BaseModel, Field

from app.modules.employee.field_limits import Str10, Str20, Str25, Str30, Str50, Str100, Str255, Str355
from .model import AllocationMethod, DEFAULT_CURRENCY, ImportCostType, OrderType


class DeliveryIn(BaseModel):
    id: int | None = None
    delivery_no: int = 1
    warehouse_code: Str50 = ""
    carrier_code: Str50 = ""
    carrier_name: Str255 = ""
    ship_qty: float = 0
    ship_unit: Str25 = ""
    received_qty: float = 0
    promised_date: Str10 = ""
    expected_date: Str10 = ""
    received_date: Str10 = ""
    std_days: int = 0
    invoice_no: Str50 = ""
    invoice_date: Str10 = ""
    shipping_unit_price: float = 0
    shipping_amount: float = 0
    qc_result: Str20 = ""
    extra_request: str = ""
    progress_note: str = ""


class POItemIn(BaseModel):
    id: int | None = None
    product_code: Str50 = ""
    product_name: Str255 = ""
    invoice_name: Str255 = ""
    item_group: Str100 = ""
    spec: Str255 = ""
    fg_code: Str50 = ""
    fg_name: Str255 = ""
    invoice_no: Str50 = ""
    invoice_date: Str10 = ""             # Ngày hóa đơn (tự set hôm nay khi có số hóa đơn, sửa tay được)
    document_delivery_date: Str10 = ""   # Ngày giao chứng từ cho KT (Task 8)
    supplier_ready: bool = False
    required_date: Str10 = ""
    expected_date: Str10 = ""            # Dự kiến có hàng — rỗng thì backend copy từ dòng YCMH nguồn
    unit: Str25 = ""
    qty_request: float = 0
    qty_order: float = 0
    price: float = 0
    # % VAT theo dòng, nhập tay từ CR-058 → chặn 0 ≤ VAT < 100 (cột DB Numeric(5,2)).
    vat: float = Field(0, ge=0, lt=100)
    # bao-CR-319: đơn giá ghi theo đồng tiền của dòng. Để TRỐNG là cố ý — dòng không khai
    # thì `_save_items` chép loại tiền / tỷ giá từ đơn xuống. Nếu đặt sẵn "VND" ở đây, dòng
    # sinh tự động (tạo ĐMH từ YCMH, nhân bản đơn) sẽ mang cứng VNĐ vào đơn ngoại tệ.
    currency: Str10 = ""
    exchange_rate: float = Field(0, ge=0)
    weight_kg: float = Field(0, ge=0)
    dimension: Str100 = ""
    warehouse_code: Str50 = ""
    note: Str355 = ""
    deliveries: list[DeliveryIn] = []


class POImportCostIn(BaseModel):
    """Một khoản CHI PHÍ THU MUA của đơn (bao-CR-319 P3, ba giai đoạn bao-CR-453).

    `cost_type` là mã trong danh mục `tab_po_cost_type`; `_save_import_costs` kiểm tồn tại
    và còn dùng. Ba cặp `<giai đoạn>_amount / _rate`: số TRƯỚC thuế theo đồng tiền của dòng
    + tỷ giá riêng của giai đoạn đó; `None` = giai đoạn chưa có số (khác 0 đồng). Màn lưu
    đơn chỉ ghi được giai đoạn HIỆU LỰC của dòng, cột đã chốt gửi lên bị bỏ qua.
    Giai đoạn riêng dòng (`line_stage`) KHÔNG nhận qua đây — đi cửa `/costs/{id}/finalize`.
    """

    id: int | None = None
    cost_type: int = int(ImportCostType.OTHER)
    description: Str355 = ""
    supplier_code: Str50 = ""
    supplier_name: Str255 = ""
    # Để TRỐNG là cố ý, giống dòng hàng: backend chép loại tiền / tỷ giá từ đơn xuống.
    currency: Str10 = ""
    estimate_amount: float | None = Field(None, ge=0)
    estimate_rate: float = Field(0, ge=0)
    provisional_amount: float | None = Field(None, ge=0)
    provisional_rate: float = Field(0, ge=0)
    final_amount: float | None = Field(None, ge=0)
    final_rate: float = Field(0, ge=0)
    vat: float = Field(0, ge=0, lt=100)
    allocation_method: int = Field(int(AllocationMethod.BY_VALUE), ge=1, le=5)
    allocation_target: Str50 = ""                # mã hàng — chỉ dùng khi chia theo chỉ định
    # Cách 5 "Nhập tay": {"<id dòng hàng>": số tiền VNĐ}; tổng phải bằng số quy đổi của khoản
    manual_allocation: dict[str, float] = {}
    invoice_no: Str50 = ""
    invoice_date: Str10 = ""
    payment_due_date: Str10 = ""
    note: Str255 = ""


class POCreate(BaseModel):
    code: Str50 | None = None
    misa_code: Str50 = ""
    pr_code: Str50 = ""
    survey_code: Str50 = ""
    company_id: int = 0
    supplier_code: Str50 = ""
    supplier_name: Str255 = ""
    department_id: int = 0        # CR-086: phòng ban neo bằng id; bỏ trống thì tra từ `department`
    handler_dept_id: int = 0      # bao-CR-414: phòng ĐƯỢC NHỜ xử lý; 0 = chép từ YCMH nếu có
    department: Str255 = ""
    nspt_id: int = 0              # CR-087: NSPT neo bằng id; bỏ trống thì tra từ `nspt`
    approver_employee_id: int = 0   # bao-CR-499: người được chọn duyệt; sau Duyệt = người thực duyệt
    nspt: Str100 = ""
    order_date: Str10 = ""
    vat_rate: float = 0.08
    payment_terms: Str255 = ""
    is_urgent: bool = False
    # bao-CR-319 — loại đơn + tờ khai hải quan (cụm tờ khai chỉ có nghĩa với đơn nhập khẩu)
    order_type: int = Field(int(OrderType.DOMESTIC), ge=1, le=2)
    currency: Str10 = DEFAULT_CURRENCY
    exchange_rate: float = Field(1, ge=0)
    customs_decl_no: Str50 = ""
    customs_decl_date: Str10 = ""
    etd_date: Str10 = ""                   # bao-CR-347 — ngày hàng rời cảng xuất
    # bao-CR-321 — điều khoản in theo NCC; 0 / rỗng = lùi về NCC rồi về mặc định
    inspection_days: int = Field(0, ge=0, le=365)
    return_days: int = Field(0, ge=0, le=365)
    invoice_deadline: str = Field("", max_length=255)
    note: str = ""
    items: list[POItemIn] = []
    import_costs: list[POImportCostIn] = []


class POUpdate(BaseModel):
    misa_code: Str50 | None = None
    pr_code: Str50 | None = None
    survey_code: Str50 | None = None
    company_id: int | None = None
    supplier_code: Str50 | None = None
    supplier_name: Str255 | None = None
    department_id: int | None = None      # CR-086
    handler_dept_id: int | None = None    # bao-CR-414
    department: Str255 | None = None
    nspt_id: int | None = None            # CR-087
    approver_employee_id: int | None = None   # bao-CR-499
    nspt: Str100 | None = None
    order_date: Str10 | None = None
    vat_rate: float | None = None
    payment_terms: Str255 | None = None
    is_urgent: bool | None = None
    order_type: int | None = Field(None, ge=1, le=2)
    currency: Str10 | None = None
    exchange_rate: float | None = Field(None, ge=0)
    customs_decl_no: Str50 | None = None
    customs_decl_date: Str10 | None = None
    etd_date: Str10 | None = None
    inspection_days: int | None = Field(None, ge=0, le=365)
    return_days: int | None = Field(None, ge=0, le=365)
    invoice_deadline: str | None = Field(None, max_length=255)
    document_status: Str30 | None = None   # Trạng thái hồ sơ chứng từ, cập nhật tay (Task 10b)
    note: str | None = None
    items: list[POItemIn] | None = None
    # Không gửi khóa này = không đụng tới bảng chi phí; gửi mảng rỗng = xóa hết.
    import_costs: list[POImportCostIn] | None = None


class RejectIn(BaseModel):
    reason: str = ""


class CostStageAdvanceIn(BaseModel):
    """Chốt Tạm tính (2) / Quyết toán (3) chi phí thu mua (bao-CR-453). Gửi kèm `import_costs`
    thì lưu bảng chi phí TRƯỚC rồi mới chốt — một nút bấm, không phải Lưu rồi Chốt."""
    target: int = Field(..., ge=2, le=3)
    import_costs: list[POImportCostIn] | None = None


class CostStageReopenIn(BaseModel):
    """Mở lại về Dự toán (1) / Tạm tính (2); lý do bắt buộc, tối thiểu 10 ký tự (kiểm ở service)."""
    target: int = Field(..., ge=1, le=2)
    reason: str = ""


class CostLinesFinalizeIn(BaseModel):
    """bao-CR-469 — Quyết toán nhiều dòng chi phí một lượt.

    Danh sách RỖNG là một lựa chọn có nghĩa chứ không phải thiếu dữ liệu: rỗng = chốt HẾT các
    dòng chưa quyết toán của đơn (nút «Chốt tất cả»). Trần 200 để một lời gọi hỏng không quét
    cả bảng chi phí của mọi đơn — một đơn không có tới bằng ấy khoản.
    """
    cost_ids: list[int] = Field(default_factory=list, max_length=200)
    # bao-CR-476: bảng chi phí ĐANG GÕ trên màn hình, gửi kèm để lưu TRƯỚC rồi mới chốt — cùng
    # khuôn `CostStageAdvanceIn.import_costs`. Thiếu nó thì đường chốt đọc số ĐÃ LƯU: người dùng
    # gõ số Quyết toán rồi bấm chốt ngay là chốt theo số cũ, sinh công nợ sai số, còn số vừa gõ
    # bị lượt tải lại đè mất. `None` = không đụng bảng chi phí (giữ hành vi cũ).
    import_costs: list[POImportCostIn] | None = None


class ItemProgressIn(BaseModel):
    status: str                    # MÃ tiến độ đích (hoặc "__resume__" để bỏ `paused`), xem PO_PROGRESS_STATUS
    reason: str = ""               # bắt buộc khi `paused` / `cancelled`


class DocumentStatusIn(BaseModel):
    document_status: Str30           # MÃ (B-06): none | partial | full — xem PO_DOCUMENT_STATUS
