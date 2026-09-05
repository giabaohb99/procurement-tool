"""CR-075 — màn "Tiến độ báo giá": bộ cột + cách dựng một hàng.

Một hàng = MỘT DÒNG Yêu cầu báo giá (kèm phương án đã chốt của dòng đó). Khác màn Tiến độ
mua hàng ở chỗ đó: bên kia nở theo LẦN GIAO, bên này KHÔNG nở theo phương án — dòng có 5
phương án vẫn là một hàng, vì thứ người ta theo dõi là "dòng này khảo sát tới đâu rồi".

Giá trị riêng của màn này so với danh sách YCBG là ba cột tính: **trễ hạn**, **số ngày xử lý**
và **tiến độ dòng**. Hai cột đầu dựa vào `result_date` (ngày trả kết quả thực tế) — cột do
CR-075 thêm; dữ liệu cũ đã backfill bằng `scripts/backfill_result_date_cr075.py`.

ẨN NCC: cùng luật với `survey_request/export.py` — cột NCC/mã SP theo NCC/ghi chú NSTM chỉ ra
với người có `supplier.read`. **Quyền phạm vi (`survey_request.read`) và quyền xem NCC
(`supplier.read`) là HAI cờ RỜI** — bài học CR-071, đừng gộp lại.
"""
from datetime import date, datetime

from app.core.export_xlsx import Col
from app.modules.survey_request.export import LINE_STATUS_LABEL, STATUS_LABEL, opt_cells
from app.modules.survey_request.line_state import (  # noqa: F401 — dùng lại nguyên bộ nhãn
    STATE_ANSWERED, STATE_CHOSEN, STATE_CONFIRMED, STATE_DONE, STATE_NOT_RECEIVED,
    STATE_NO_OPTION, STATE_PO_CREATED, STATE_PR_CREATED, STATE_RECEIVED, STATE_RESURVEY,
    STATE_SURVEYING, STATES, progress_state)
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)

# Key bị GỠ KHỎI DỮ LIỆU với người không có `supplier.read`
SUPPLIER_HIDDEN_KEYS = ("internal_line_code", "opt_supplier_code", "opt_supplier_name",
                        "opt_internal_code", "opt_note")

COLS = [
    Col("stt", "STT", "int", 7),
    # ----- Đầu phiếu -----
    Col("code", "Mã YCBG", width=18),
    Col("company", "Công ty", width=26),
    Col("department", "Bộ phận", width=18),
    Col("requester", "Người yêu cầu", width=22),
    Col("purpose", "Mục đích", width=26),
    Col("request_date", "Ngày yêu cầu", "date", 13),
    Col("status", "Trạng thái phiếu", width=16),
    # ----- Dòng yêu cầu -----
    Col("internal_line_code", "Mã dòng nội bộ", width=16),   # chỉ khi có supplier.read
    Col("item_group", "Phân loại", width=16),
    Col("requirement_detail", "Thông số kỹ thuật", width=34),
    Col("other_requirement", "Yêu cầu khác", width=24),
    Col("request_qty", "SL dự kiến", "qty", 12),
    Col("uom", "ĐVT", width=8),
    Col("proposed_price", "Giá đề xuất", "price", 14),
    Col("assignee_name", "NSTM phụ trách", width=22),
    # ----- Mốc tiến độ (phần cốt lõi của màn này) -----
    Col("received_date", "Ngày tiếp nhận", "date", 14),
    Col("result_due_date", "Hạn trả kết quả", "date", 14),
    Col("result_date", "Ngày trả kết quả", "date", 15),
    Col("days_late", "Trễ hạn (ngày)", "int", 13),
    Col("handling_days", "Số ngày xử lý", "int", 13),
    Col("progress_state", "Tiến độ dòng", width=18),
    Col("line_status", "Trạng thái dòng", width=16),
    Col("option_count", "Số phương án", "int", 12),
    # CR-079: bỏ cột "Mã YCMH đã tạo" — `pr_code` trên dòng chỉ giữ mã MỚI NHẤT, dòng tạo YCMH
    # nhiều lần (mua lại) thì các mã trước biến mất. Xuất ra Excel dễ bị đọc nhầm là đủ.
    # ----- Phương án đã chốt -----
    Col("opt_label", "Phương án chốt", width=16),
    Col("opt_supplier_code", "Mã NCC", width=14),          # chỉ khi có supplier.read
    Col("opt_supplier_name", "Tên NCC", width=28),         # chỉ khi có supplier.read
    Col("opt_internal_code", "Mã SP theo NCC", width=16),  # chỉ khi có supplier.read
    Col("opt_product_code", "Mã SP hệ thống", width=16),
    Col("opt_product_name", "Tên SP báo giá", width=32),
    Col("opt_spec", "Quy cách", width=28),
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
    Col("opt_note", "Ghi chú NSTM", width=24),             # chỉ khi có supplier.read
]

SUPPLIER_ONLY = set(SUPPLIER_HIDDEN_KEYS)

SHEET_TITLE = "Tien do bao gia"
FILE_NAME = "tien-do-bao-gia"


def columns_for(show_supplier: bool) -> list[Col]:
    return list(COLS) if show_supplier else [c for c in COLS if c.key not in SUPPLIER_ONLY]


def _parse(d: str):
    """Chuỗi 'YYYY-MM-DD' -> date; rỗng/hỏng -> None (dữ liệu cũ có ô trống)."""
    try:
        return datetime.strptime((d or "").strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _days_late(due: str, result: str, today: date) -> int | None:
    """Trễ mấy ngày. Đã trả kết quả -> so ngày trả với hạn. CHƯA trả mà quá hạn -> so hôm nay
    với hạn (đang trễ, số này còn tăng). Chưa tới hạn hoặc không có hạn -> None (ô trống).

    Số âm (trả sớm) KHÔNG hiện — cột này để soi việc trễ, trả sớm mấy ngày không phải thứ
    người dùng đang tìm; muốn biết thì đã có sẵn hai cột ngày ngay cạnh."""
    d_due = _parse(due)
    if not d_due:
        return None
    d_res = _parse(result)
    mark = d_res or today
    late = (mark - d_due).days
    return late if late > 0 else None


def _handling_days(received: str, result: str) -> int | None:
    """Số ngày từ lúc NSTM tiếp nhận tới lúc trả kết quả. Thiếu một trong hai mốc -> ô trống."""
    a, b = _parse(received), _parse(result)
    return (b - a).days if a and b else None


def row_values(s: SurveyRequest, ln: SurveyRequestLine, opt: SurveyRequestOption | None,
               option_count: int, assignee_name: str, company_name: str,
               show_supplier: bool, today: date) -> dict:
    r = {
        # ----- Đầu phiếu -----
        "sr_id": s.id, "code": s.code, "company_id": s.company_id, "company": company_name,
        "department": s.department, "requester": s.requester, "purpose": s.purpose,
        "request_date": s.request_date, "sr_status": s.status,
        "status": STATUS_LABEL.get(s.status, s.status or ""),
        # ----- Dòng yêu cầu -----
        "line_id": ln.id, "internal_line_code": ln.internal_line_code,
        "item_group": ln.item_group, "requirement_detail": ln.requirement_detail,
        "other_requirement": ln.other_requirement,
        "request_qty": float(ln.request_qty or 0), "uom": ln.uom,
        "proposed_price": float(ln.proposed_price or 0),
        "assignee": ln.assignee, "assignee_name": assignee_name,
        # ----- Mốc tiến độ -----
        "received_date": ln.received_date, "result_due_date": ln.result_due_date,
        "result_date": ln.result_date or "",
        "days_late": _days_late(ln.result_due_date, ln.result_date, today),
        "handling_days": _handling_days(ln.received_date, ln.result_date),
        "progress_state": progress_state(ln, opt is not None, option_count),
        "line_status": LINE_STATUS_LABEL.get(ln.line_status, ln.line_status or ""),
        "option_count": option_count,
        "pr_id": ln.pr_id, "pr_code": ln.pr_code,
    }
    r.update(opt_cells(opt))
    if not show_supplier:
        for k in SUPPLIER_HIDDEN_KEYS:
            r.pop(k, None)
    return r
