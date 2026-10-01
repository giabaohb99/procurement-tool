from app.modules.employee.field_limits import Str10, Str25, Str30, Str50, Str100, Str255, Str355, Str1000
from pydantic import BaseModel, Field


class SupplierClusterIn(BaseModel):
    """1 cụm NCC (Task 4). req = bộ phận đề xuất · pur = khảo sát/thu mua."""
    name: str = ""
    tax_code: str = ""
    contact: str = ""


class PRItemIn(BaseModel):
    id: int | None = None            # id dòng đã có -> cập nhật tại chỗ (GIỮ id để ảnh đối chiếu không mồ côi)
    product_code: Str50 = ""
    product_name: Str255
    item_group: Str100 = ""
    group_desc: Str255 = ""
    qty: float = Field(0, ge=0)      # SL không âm; cho số lẻ (BE Numeric(18,3))
    unit: Str25 = ""
    price: float = Field(0, ge=0)    # giá không âm; cho số lẻ (BE Numeric(18,4))
    # % VAT theo dòng (Task 4). Nhập tay từ CR-058 → phải chặn ở BE: 0 ≤ VAT < 100.
    # Cột DB là Numeric(5,2), trên 999,99 là MySQL báo lỗi tràn thay vì trả 422 tử tế.
    vat_pct: float = Field(0, ge=0, lt=100)
    warehouse: Str100 = ""
    required_date: Str10 = ""
    assignee: Str100 = ""
    # MÃ cố định, xem PR_LINE_STATUS trong app/core/status_codes.py (B-06). CR-074: dòng mới
    # chưa có ĐMH nào thì nằm ở `no_po`, khác với `not_ordered` (đã có ĐMH, chưa bấm đặt).
    line_status: Str30 = "no_po"
    progress_note: str = ""
    note: Str355 = ""


class PRCreate(BaseModel):
    code: Str50 | None = None  # bỏ trống -> tự sinh PYC#####
    company_id: int = 0
    requester: Str255 = ""
    requester_id: int = 0
    requester_position: Str100 = ""
    department_id: int = 0        # CR-086: phòng ban neo bằng id; bỏ trống thì tra từ `department`
    # bao-CR-414/480/488: phòng XỬ LÝ phiếu. `None` (không gửi) = để hệ thống chọn mặc định
    # (phòng tự mua → chính phòng lập, còn lại → phòng thu mua mặc định PBA017, bao-CR-524);
    # gửi số — kể cả 0 — là người lập ĐÃ CHỌN, giữ nguyên (0 = phòng thu mua mặc định, ghi id
    # thật). Trước CR-488 gửi 0 cũng bị tra đè, nhà máy không thể nhờ thu mua chung ngay lúc
    # lập phiếu.
    handler_dept_id: int | None = None
    department: Str255 = ""
    head_of_dept: Str255 = ""
    head_of_dept_id: int = 0      # CR-071: id nhân sự TBP đứng tên trên phiếu (0 = theo mặc định phòng)
    # bao-CR-499: người ĐƯỢC CHỌN sẽ duyệt (nhận chuông/mail lúc gửi duyệt); bấm Duyệt xong thì cột này
    # đổi thành người THỰC duyệt (bao-CR-490) — bản in luôn in tên đang nằm trong cột.
    approver_employee_id: int = 0
    purpose: Str355 = ""
    request_date: Str10 = ""
    need_date: Str10 = ""
    is_urgent: bool = False
    vat_rate: float = 0.08
    note: str = ""
    show_code_on_print: bool = True
    suggested_supplier: Str255 = ""
    suggested_supplier_tax_code: Str50 = ""
    suggested_supplier_contact: Str255 = ""
    quote_filename: Str255 = ""
    quote_file_url: Str1000 = ""
    supplier_req: SupplierClusterIn | None = None   # Task 4: NCC bộ phận đề xuất
    supplier_pur: SupplierClusterIn | None = None   # Task 4: NCC khảo sát/thu mua (cần supplier.write)
    items: list[PRItemIn] = []


class PRUpdate(BaseModel):
    company_id: int | None = None
    requester: Str255 | None = None
    requester_id: int | None = None
    requester_position: Str100 | None = None
    department_id: int | None = None      # CR-086
    handler_dept_id: int | None = None    # bao-CR-414
    department: Str255 | None = None
    head_of_dept: Str255 | None = None
    head_of_dept_id: int | None = None    # CR-071
    approver_employee_id: int | None = None   # bao-CR-499
    purpose: Str355 | None = None
    request_date: Str10 | None = None
    need_date: Str10 | None = None
    is_urgent: bool | None = None
    vat_rate: float | None = None
    assignee_id: int | None = None
    note: str | None = None
    show_code_on_print: bool | None = None
    suggested_supplier: Str255 | None = None
    suggested_supplier_tax_code: Str50 | None = None
    suggested_supplier_contact: Str255 | None = None
    quote_filename: Str255 | None = None
    quote_file_url: Str1000 | None = None
    supplier_req: SupplierClusterIn | None = None   # Task 4: NCC bộ phận đề xuất
    supplier_pur: SupplierClusterIn | None = None   # Task 4: NCC khảo sát/thu mua (cần supplier.write)
    items: list[PRItemIn] | None = None


class RejectIn(BaseModel):
    reason: str = ""


class ApproveIn(BaseModel):
    assignee_id: int = 0


class AssignItemIn(BaseModel):
    id: int
    assignee: Str100 = ""


class AssignIn(BaseModel):
    """Phân bổ NSTM (do admin/quản lý/người duyệt) — chạy được cả khi phiếu đã gửi duyệt."""
    assignee_id: int = 0
    items: list[AssignItemIn] = []


class UrgentIn(BaseModel):
    """Bật/tắt cờ Đơn gấp trực tiếp (chạy được cả khi phiếu đã duyệt) + đồng bộ xuống ĐMH."""
    is_urgent: bool


class ItemStatusItem(BaseModel):
    id: int
    # MÃ cố định (B-06) — service kiểm lại theo PR_LINE_STATUS trước khi ghi, gửi chữ tiếng Việt
    # kiểu cũ sẽ bị chặn 400 chứ không lặng lẽ ghi rác vào cột.
    line_status: Str30 | None = None
    progress_note: str | None = None
    note: Str355 | None = None
    expected_date: Str10 | None = None          # thời gian dự kiến có hàng (NSTM cập nhật)
    expected_date_reason: str | None = None    # lý do — BẮT BUỘC khi đổi giá trị đã có


class ItemStatusIn(BaseModel):
    """Cập nhật trạng thái/tiến độ từng dòng (NSTM phụ trách hoặc admin/quản lý)."""
    items: list[ItemStatusItem] = []


class ReasonIn(BaseModel):
    reason: str = ""


class TransferDeptIn(BaseModel):
    """bao-CR-414 GĐ5 — chuyển phiếu sang phòng xử lý khác / trả về thu mua.
    `handler_dept_id` = 0 nghĩa là trả về PHÒNG THU MUA MẶC ĐỊNH (bao-CR-524, ghi id thật của
    PBA017); lý do BẮT BUỘC (ghi vào nhật ký)."""
    handler_dept_id: int = 0
    reason: str = ""


# ───────────────── PHƯƠNG ÁN trên dòng YCMH (bao-CR-310) ─────────────────

class PROptionSurveyIn(BaseModel):
    """Gắn phương án bằng cách chọn một dòng khảo sát sản phẩm đã duyệt."""
    product_survey_line_id: int


class PROptionManualIn(BaseModel):
    """NSTM gõ thẳng NCC + giá. Chỉ NCC là bắt buộc (service kiểm), phần còn lại
    bỏ trống được — tên SP / ĐVT / VAT trống thì lấy theo dòng YCMH."""
    supplier_code: Str50 = ""
    supplier_name: Str255 = ""
    snap_product_name: Str255 = ""
    snap_internal_code: Str50 = ""
    snap_spec: str = ""
    snap_origin: Str100 = ""
    snap_quote_unit: Str25 = ""
    snap_moq: float = Field(0, ge=0)
    snap_price_by_volume: float = Field(0, ge=0)
    snap_volume_range: Str100 = ""
    # Cột DB là Numeric(5,2) — thả cửa thì trên 999,99 là MySQL báo lỗi tràn thay vì 422.
    snap_vat: float | None = Field(None, ge=0, lt=100)
    snap_delivery_time: Str100 = ""
    snap_delivery_place: Str255 = ""
    snap_shipping_cost: float = Field(0, ge=0)
    nstm_note: str = ""


class PROptionUpdateIn(BaseModel):
    """Sửa phương án đã gắn. Bộ trường phải khớp `option_service.EDITABLE_FIELDS`;
    `supplier_code` cố ý KHÔNG có ở đây — đổi NCC là một phương án khác."""
    nstm_note: str | None = None
    snap_price_by_volume: float | None = Field(None, ge=0)
    snap_vat: float | None = Field(None, ge=0, lt=100)
    snap_moq: float | None = Field(None, ge=0)
    snap_quote_unit: Str25 | None = None
    snap_volume_range: Str100 | None = None
    snap_delivery_time: Str100 | None = None
    snap_delivery_place: Str255 | None = None
    snap_shipping_cost: float | None = Field(None, ge=0)


class PROptionSupplierIn(BaseModel):
    """H.10.4 — điền/sửa NCC trên PHƯƠNG ÁN 0 / phương án nhập tay, kèm sửa giá nếu
    cần. Tách khỏi `PROptionUpdateIn` vì NCC cố ý không nằm trong bộ trường sửa thường."""
    supplier_code: Str50 = ""
    supplier_name: Str255 = ""
    snap_price_by_volume: float | None = Field(None, ge=0)


class PRAssignSupplierLineIn(BaseModel):
    """Một dòng trong lệnh "áp 1 NCC cho nhiều dòng" — giá sửa kèm là TÙY CHỌN theo dòng."""
    item_id: int
    snap_price_by_volume: float | None = Field(None, ge=0)


class PRAssignSupplierIn(BaseModel):
    """H.10.5 — "Áp 1 NCC cho nhiều dòng" ngay trên màn chọn: NCC áp vào PHƯƠNG ÁN
    ĐANG CHỌN của từng dòng tick."""
    supplier_code: str = ""
    supplier_name: str = ""
    items: list[PRAssignSupplierLineIn] = []


class PROptionCompleteIn(BaseModel):
    """Chốt hoàn thành xử lý phương án (bao-CR-310 đợt 3b, khuôn YCBG `complete_sr`):
    `empty_item_ids` là các dòng NSTM tick "chốt rỗng" — không có NCC phù hợp."""
    empty_item_ids: list[int] = []
