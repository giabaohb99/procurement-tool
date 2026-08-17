"""CR-068 — xuất Excel màn Yêu cầu báo giá (YCBG/YCKS).

Mỗi DÒNG YÊU CẦU là một hàng Excel, kèm PHƯƠNG ÁN ĐÃ CHỐT của dòng đó (`is_chosen`).
Chỉ lấy phương án chốt — các option còn lại không xuất (quyết định của khách hàng).
Dòng chưa chốt phương án thì cụm phương án để trống.

ẨN NCC: mã/tên NCC, mã SP theo NCC, ghi chú NSTM và mã dòng nội bộ chỉ ra file khi người xuất
có quyền `supplier.read` — cùng luật với API kết quả khảo sát, kẻo file Excel thành đường rò.
"""
from sqlalchemy.orm import Session

from app.core.export_xlsx import Col
from . import service
from .model import (LS_COMPLETED, LS_RESURVEY, SurveyRequest, SurveyRequestLine,
                    SurveyRequestOption)

STATUS_LABEL = {
    "draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
    "processing": "Đang xử lý", "survey_done": "Đã khảo sát", "pr_created": "Đã tạo YCMH",
    "done": "Hoàn thành", "rejected": "Bị trả lại", "cancelled": "Đã từ chối",
}

LINE_STATUS_LABEL = {
    "": "", LS_RESURVEY: "Cần khảo sát lại", LS_COMPLETED: "Hoàn thành",
}

# Cụm đầu phiếu — key trùng cột trên bảng danh sách
HEADER_COLS = [
    Col("code", "Mã YCBG", width=18),
    Col("purpose", "Mục đích", width=28),
    Col("requester", "Người yêu cầu", width=22),
    Col("department", "Bộ phận", width=18),
    Col("created_at", "Ngày tạo", "datetime", 18),
    Col("status", "Trạng thái", width=16),
]

# Cụm dòng yêu cầu — luôn xuất
LINE_COLS = [
    Col("line_no", "STT dòng", "int", 9),
    Col("internal_line_code", "Mã dòng nội bộ", width=16),   # chỉ khi có supplier.read
    Col("item_group", "Phân loại", width=16),
    Col("requirement_detail", "Thông số kỹ thuật", width=34),
    Col("other_requirement", "Yêu cầu khác", width=26),
    Col("request_qty", "SL dự kiến", "qty", 12),
    Col("uom", "ĐVT", width=8),
    Col("proposed_price", "Giá đề xuất", "price", 14),
    Col("received_date", "Ngày tiếp nhận", "date", 14),
    Col("result_due_date", "Hạn trả kết quả", "date", 14),
    Col("assignee_name", "NSTM phụ trách", width=22),
    Col("line_status", "Trạng thái dòng", width=16),
    # CR-079: bỏ cột "Mã YCMH đã tạo" — cùng lý do với màn Tiến độ báo giá: `pr_code` trên dòng
    # chỉ giữ mã MỚI NHẤT, dòng tạo YCMH nhiều lần (mua lại) thì các mã trước biến mất. Danh
    # sách đủ nằm ở `tab_survey_request_pr`, xem qua popup phương án trong chi tiết YCBG.
]

# Cụm PHƯƠNG ÁN CHỐT
OPTION_COLS = [
    Col("opt_label", "Phương án chốt", width=18),
    Col("opt_supplier_code", "Mã NCC", width=14),          # chỉ khi có supplier.read
    Col("opt_supplier_name", "Tên NCC", width=28),         # chỉ khi có supplier.read
    Col("opt_internal_code", "Mã SP theo NCC", width=16),  # chỉ khi có supplier.read
    Col("opt_product_code", "Mã SP hệ thống", width=16),
    Col("opt_product_name", "Tên SP báo giá", width=32),
    Col("opt_spec", "Quy cách", width=30),
    Col("opt_origin", "Xuất xứ", width=14),
    Col("opt_quote_unit", "ĐVT báo giá", width=12),
    Col("opt_moq", "SL tối thiểu", "qty", 12),
    Col("opt_price", "Đơn giá báo", "price", 14),
    Col("opt_volume_range", "Khoảng SL áp giá", width=16),
    Col("opt_vat", "% VAT", "int", 8),
    Col("opt_delivery_time", "Thời gian giao", width=16),
    Col("opt_delivery_place", "Nơi giao", width=22),
    Col("opt_shipping_cost", "Phí vận chuyển", "money", 14),
    Col("opt_sample_ready", "Có mẫu", "bool", 9),
    Col("opt_lab_result", "Kết quả kiểm nghiệm", width=16),
    Col("opt_note", "Ghi chú NSTM", width=26),             # chỉ khi có supplier.read
]

# Cột lộ NCC — bỏ khỏi file khi người xuất không có quyền supplier.read
SUPPLIER_ONLY = {"internal_line_code", "opt_supplier_code", "opt_supplier_name",
                 "opt_internal_code", "opt_note"}

SHEET_TITLE = "Yeu cau bao gia"
FILE_NAME = "yeu-cau-bao-gia"


def columns_for(show_supplier: bool) -> list[Col]:
    """Cụm dòng + cụm phương án, đã bỏ cột lộ NCC nếu không đủ quyền."""
    cols = list(LINE_COLS) + list(OPTION_COLS)
    if show_supplier:
        return cols
    return [c for c in cols if c.key not in SUPPLIER_ONLY]


def line_visible_fn(db: Session, user, profile: dict):
    """Trả về hàm (phiếu, dòng) -> có được xuất dòng này không.

    Giữ đúng luật của màn chi tiết (`service.visible_lines_for`): người tạo/người YC/quản lý thấy
    hết dòng, còn NSTM chỉ thấy dòng mình được giao hoặc thuộc phân loại mình phụ trách.
    Khác `can_process_line` ở chỗ nạp sẵn danh sách phân loại một lần thay vì truy vấn từng dòng —
    xuất file có thể lên hàng nghìn dòng.
    """
    from sqlalchemy import or_
    from app.modules.catalog.model import ItemGroup
    from app.modules.category_assignee.model import CategoryAssignee

    if service._has_scope_all(profile):
        return lambda s, ln: True
    emp_code = profile.get("emp_code") or ""
    emp_id = profile.get("employee_id") or 0
    groups: set[str] = set()
    if emp_id:
        groups = {name for (name,) in db.query(ItemGroup.name)
                  .join(CategoryAssignee, CategoryAssignee.item_group_id == ItemGroup.id)
                  .filter(or_(CategoryAssignee.primary_employee_id == emp_id,
                              CategoryAssignee.backup_employee_id == emp_id)).all()}

    def visible(s, ln) -> bool:
        if service._see_all_lines(profile, s, user):
            return True
        if emp_code and ln.assignee == emp_code:
            return True
        return bool(emp_id) and ln.item_group in groups

    return visible


def _employee_names(db: Session, codes: set[str]) -> dict[str, str]:
    codes = {c for c in codes if c}
    if not codes:
        return {}
    from app.modules.employee.model import Employee
    rows = db.query(Employee.code, Employee.full_name).filter(Employee.code.in_(codes)).all()
    return {c: (f"{c} — {n}" if n else c) for c, n in rows}


def opt_cells(o: SurveyRequestOption | None) -> dict:
    if o is None:
        return {}
    return {
        "opt_label": o.display_label or (f"Option {o.public_id}" if o.public_id else ""),
        "opt_supplier_code": o.supplier_code,
        "opt_supplier_name": o.supplier_name,
        "opt_internal_code": o.snap_internal_code,
        "opt_product_code": o.system_product_code,
        "opt_product_name": o.snap_product_name,
        "opt_spec": o.snap_spec,
        "opt_origin": o.snap_origin,
        "opt_quote_unit": o.snap_quote_unit,
        "opt_moq": float(o.snap_moq or 0),
        "opt_price": float(o.snap_price_by_volume or 0),
        "opt_volume_range": o.snap_volume_range,
        "opt_vat": float(o.snap_vat or 0),
        "opt_delivery_time": o.snap_delivery_time,
        "opt_delivery_place": o.snap_delivery_place,
        "opt_shipping_cost": float(o.snap_shipping_cost or 0),
        "opt_sample_ready": bool(o.snap_sample_ready),
        "opt_lab_result": o.snap_lab_result,
        "opt_note": o.nstm_note,
    }


def build_rows(db: Session, srs: list[SurveyRequest], visible=None) -> list[dict]:
    """Bung mỗi phiếu thành các hàng theo dòng yêu cầu, ghép phương án đã chốt của dòng.

    `visible` = hàm (phiếu, dòng) -> bool từ `line_visible_fn`; bỏ trống nghĩa là xuất mọi dòng.
    """
    if not srs:
        return []
    sr_ids = [s.id for s in srs]
    lines = (db.query(SurveyRequestLine)
             .filter(SurveyRequestLine.survey_request_id.in_(sr_ids))
             .order_by(SurveyRequestLine.survey_request_id, SurveyRequestLine.id).all())
    by_sr: dict[int, list[SurveyRequestLine]] = {}
    for ln in lines:
        by_sr.setdefault(ln.survey_request_id, []).append(ln)

    chosen: dict[int, SurveyRequestOption] = {}
    if lines:
        opts = (db.query(SurveyRequestOption)
                .filter(SurveyRequestOption.survey_request_line_id.in_([ln.id for ln in lines]),
                        SurveyRequestOption.is_chosen == True).all())
        for o in opts:   # dòng chỉ chốt 1 phương án; có nhiều thì lấy bản chốt sau cùng
            chosen[o.survey_request_line_id] = o
    names = _employee_names(db, {ln.assignee for ln in lines})

    rows: list[dict] = []
    for s in srs:
        head = {
            "code": s.code,
            "purpose": s.purpose,
            "requester": s.requester,
            "department": s.department,
            "created_at": s.created_at,
            "status": STATUS_LABEL.get(s.status, s.status or ""),
        }
        sr_lines = by_sr.get(s.id, [])
        if visible is not None:
            sr_lines = [ln for ln in sr_lines if visible(s, ln)]
        if not sr_lines:
            rows.append(dict(head))
            continue
        for i, ln in enumerate(sr_lines, start=1):
            rows.append(head | {
                "line_no": i,
                "internal_line_code": ln.internal_line_code,
                "item_group": ln.item_group,
                "requirement_detail": ln.requirement_detail,
                "other_requirement": ln.other_requirement,
                "request_qty": float(ln.request_qty or 0),
                "uom": ln.uom,
                "proposed_price": float(ln.proposed_price or 0),
                "received_date": ln.received_date,
                "result_due_date": ln.result_due_date,
                "assignee_name": names.get(ln.assignee, ln.assignee or ""),
                "line_status": LINE_STATUS_LABEL.get(ln.line_status, ln.line_status or ""),
                "pr_code": ln.pr_code,
            } | opt_cells(chosen.get(ln.id)))
    return rows
