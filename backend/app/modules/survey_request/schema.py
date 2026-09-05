from pydantic import BaseModel


class SurveyRequestLineIn(BaseModel):
    id: int = 0          # >0 = dòng đã có (giữ nguyên ID để không mất file đính kèm); 0 = dòng mới
    received_date: str = ""
    result_due_date: str = ""
    department_requester: str = ""
    item_group: str = ""
    requirement_detail: str = ""
    other_requirement: str = ""
    request_qty: float = 0
    uom: str = ""
    proposed_price: float = 0
    image_file: str = ""
    # P6-1 (bao-CR-277): trường của YCMH mang lên dòng phiếu gộp. `qty_ordered`/`qty_received`
    # CỐ Ý không có ở đây — hai cột đó do đồng bộ từ ĐMH ghi (P6-4), client không được gửi.
    product_code: str = ""
    warehouse: str = ""
    required_date: str = ""
    vat_pct: float = 0
    src_pr_item_id: int = 0   # CR-027: dòng YCMH nguồn — chỉ dùng lúc TẠO dòng mới để kéo ảnh sang


class _Header(BaseModel):
    company_id: int = 0
    requester: str = ""
    requester_id: int = 0
    requester_position: str = ""
    department_id: int = 0        # CR-086: phòng ban neo bằng id; bỏ trống thì tra từ `department`
    department: str = ""
    head_of_dept_id: int = 0      # CR-087: TBP neo bằng id nhân sự; bỏ trống thì lấy theo phòng
    head_of_dept: str = ""
    purpose: str = ""
    request_date: str = ""
    note: str = ""
    is_urgent: bool = False       # bao-CR-289: cờ Đơn gấp (mirror YCMH)
    # P6-9 (bao-CR-287): NCC người yêu cầu đề xuất (mirror cụm `req` của YCMH) — dùng cho bản in
    suggested_supplier: str = ""
    suggested_supplier_tax_code: str = ""
    suggested_supplier_contact: str = ""


class SurveyRequestCreate(_Header):
    code: str | None = None
    lines: list[SurveyRequestLineIn] = []


class SurveyRequestUpdate(BaseModel):
    company_id: int | None = None
    requester: str | None = None
    requester_id: int | None = None
    requester_position: str | None = None
    department_id: int | None = None      # CR-086
    department: str | None = None
    head_of_dept_id: int | None = None    # CR-087
    head_of_dept: str | None = None
    purpose: str | None = None
    request_date: str | None = None
    note: str | None = None
    is_urgent: bool | None = None                      # bao-CR-289
    suggested_supplier: str | None = None              # P6-9 (bao-CR-287)
    suggested_supplier_tax_code: str | None = None
    suggested_supplier_contact: str | None = None
    lines: list[SurveyRequestLineIn] | None = None


class RejectIn(BaseModel):
    reason: str = ""


class LineStatusIn(BaseModel):
    # "" chưa xác định · "resurvey" cần khảo sát lại · "completed" hoàn thành
    line_status: str = ""


class LineConfirmIn(BaseModel):
    # P6-3 (bao-CR-281): true = chốt phương án đang chọn của dòng · false = bỏ chốt
    confirmed: bool = True
