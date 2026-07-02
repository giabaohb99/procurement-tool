from pydantic import BaseModel


class PRItemIn(BaseModel):
    product_code: str = ""
    product_name: str
    item_group: str = ""
    group_desc: str = ""
    qty: float = 0
    unit: str = ""
    price: float = 0
    warehouse: str = ""
    required_date: str = ""
    assignee: str = ""
    line_status: str = "Chưa đặt hàng"
    progress_note: str = ""
    note: str = ""


class PRCreate(BaseModel):
    code: str | None = None  # bỏ trống -> tự sinh PYC#####
    company_id: int = 0
    requester: str = ""
    requester_position: str = ""
    department: str = ""
    head_of_dept: str = ""
    purpose: str = ""
    request_date: str = ""
    need_date: str = ""
    is_urgent: bool = False
    vat_rate: float = 0.08
    note: str = ""
    show_code_on_print: bool = True
    suggested_supplier: str = ""
    suggested_supplier_tax_code: str = ""
    suggested_supplier_contact: str = ""
    quote_filename: str = ""
    quote_file_url: str = ""
    items: list[PRItemIn] = []


class PRUpdate(BaseModel):
    company_id: int | None = None
    requester: str | None = None
    requester_position: str | None = None
    department: str | None = None
    head_of_dept: str | None = None
    purpose: str | None = None
    request_date: str | None = None
    need_date: str | None = None
    is_urgent: bool | None = None
    vat_rate: float | None = None
    assignee_id: int | None = None
    note: str | None = None
    show_code_on_print: bool | None = None
    suggested_supplier: str | None = None
    suggested_supplier_tax_code: str | None = None
    suggested_supplier_contact: str | None = None
    quote_filename: str | None = None
    quote_file_url: str | None = None
    items: list[PRItemIn] | None = None


class RejectIn(BaseModel):
    reason: str = ""


class ApproveIn(BaseModel):
    assignee_id: int = 0


class AssignItemIn(BaseModel):
    id: int
    assignee: str = ""


class AssignIn(BaseModel):
    """Phân bổ NSTM (do admin/quản lý/người duyệt) — chạy được cả khi phiếu đã gửi duyệt."""
    assignee_id: int = 0
    items: list[AssignItemIn] = []


class ItemStatusItem(BaseModel):
    id: int
    line_status: str | None = None
    progress_note: str | None = None
    note: str | None = None


class ItemStatusIn(BaseModel):
    """Cập nhật trạng thái/tiến độ từng dòng (NSTM phụ trách hoặc admin/quản lý)."""
    items: list[ItemStatusItem] = []


class ReasonIn(BaseModel):
    reason: str = ""
