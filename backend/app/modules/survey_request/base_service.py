"""Hằng và hàm đọc nền của YCBG — mọi tệp nghiệp vụ con dùng chung, KHÔNG import tệp anh em (bao-CR-715)."""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import SurveyRequest, SurveyRequestLine, SurveyRequestOption


ENTITY = "survey_request"
# request_date: cho bộ lọc điều kiện lọc theo ngày (apply_range_filters vẫn lo _from/_to)
FILTERABLE = ["code", "status", "requester", "department", "request_date",
              "department_id", "head_of_dept_id", "requester_id", "company_id", "purpose"]
MAX_OPTIONS_PER_LINE = 5   # mỗi sản phẩm (dòng YCKS) tối đa 5 phương án khảo sát
HEADER_FIELDS = ["company_id", "requester", "requester_id", "requester_position",
                 "department_id", "handler_dept_id", "department",
                 "head_of_dept_id", "head_of_dept", "purpose", "request_date", "note",
                 "approver_employee_id"]   # bao-CR-499


VN_OFFSET = timedelta(hours=7)   # container chạy giờ UTC — ngày phải quy về giờ Việt Nam


def _stamp_result_date(ln: SurveyRequestLine) -> None:
    """CR-075: ghi "ngày trả kết quả thực tế" cho dòng khảo sát, MỘT LẦN duy nhất.

    Đã có mốc rồi thì giữ nguyên — dòng bị trả về "cần khảo sát lại" rồi chốt lần hai không
    được phép xóa dấu trễ của lần đầu."""
    if not (ln.result_date or "").strip():
        ln.result_date = (datetime.utcnow() + VN_OFFSET).strftime("%Y-%m-%d")


def get_sr(db: Session, sid: int) -> SurveyRequest:
    """Nạp phiếu theo id. ai-CR-170: phiếu đã xóa mềm coi như không có (404)."""
    o = db.get(SurveyRequest, sid)
    if not o or o.is_deleted:
        raise HTTPException(404, "Không tìm thấy phiếu yêu cầu báo giá")
    return o


def lines_of(db: Session, sid: int):
    return (db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sid)
            .order_by(SurveyRequestLine.id).all())


def options_of(db: Session, line_id: int):
    return (db.query(SurveyRequestOption).filter(SurveyRequestOption.survey_request_line_id == line_id)
            .order_by(SurveyRequestOption.public_id).all())


def valid_options_of(db: Session, line_id: int):
    """Option hợp lệ để hiển thị/chọn. Option là SNAPSHOT tự đủ (đã copy thông số).
    Chỉ LOẠI option khi dòng khảo sát nguồn CÒN TỒN TẠI nhưng bị 'Không duyệt'
    (line_approve != 'Đã duyệt'). Nguồn đã BỊ XÓA (phiếu KS xóa) → GIỮ snapshot,
    vì snapshot vẫn đầy đủ và có thể đã được chọn/tạo YCMH. Option không gắn nguồn cũng giữ."""
    opts = options_of(db, line_id)
    if not opts:
        return opts
    from app.modules.survey.model import SurveyProductLine
    pids = [o.product_survey_line_id for o in opts if o.product_survey_line_id]
    existing: set[int] = set()
    approved: set[int] = set()
    if pids:
        for pid, appr in (db.query(SurveyProductLine.id, SurveyProductLine.line_approve)
                          .filter(SurveyProductLine.id.in_(pids)).all()):
            existing.add(pid)
            if appr == "Đã duyệt":
                approved.add(pid)
    return [o for o in opts
            if (not o.product_survey_line_id)              # option nhập tay, không gắn nguồn
            or (o.product_survey_line_id not in existing)  # nguồn đã bị xóa → giữ snapshot
            or (o.product_survey_line_id in approved)]     # nguồn còn & Đã duyệt


# ───────────────────────── Phase 5B: xử lý khảo sát (NSTM) ─────────────────────────

def get_line(db: Session, sid: int, line_id: int) -> SurveyRequestLine:
    ln = (db.query(SurveyRequestLine)
          .filter(SurveyRequestLine.id == line_id, SurveyRequestLine.survey_request_id == sid).first())
    if not ln:
        raise HTTPException(404, "Không tìm thấy dòng khảo sát")
    return ln
