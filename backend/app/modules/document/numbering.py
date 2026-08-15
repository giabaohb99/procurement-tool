"""Cấp SỐ HIỆU cho văn bản — hai kiểu định danh, không thay thế nhau.

| `doc_type.id_scheme` | Ra cái gì | Đếm lại theo năm |
|---|---|---|
| 1 · mã tài liệu bất biến | `DEGO-QC-012` | **không** — mã theo văn bản suốt đời |
| 2 · số hiệu theo sổ | `08/2026/TB-NS-DEGO` | có |

Bộ đếm dùng chung `doc_catalog.number_service.next_number()` — khóa dòng, cùng
transaction với việc ghi bản ghi. Ở đây chỉ dựng **khóa bộ đếm** và **ghép
chuỗi**; tuyệt đối không tự đếm bằng `MAX + 1`.

`issue_code` của pháp nhân / phòng ban là mã đi vào số hiệu: chỉ chữ và số, khác
`code` (mã hiển thị, chứa được dấu và khoảng trắng). Dùng nhầm `code` thì ra
`Cty Dego-QC-012` (`van-thu` chỗ dễ sai số 1).
"""
import re
from datetime import date

from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.doc_catalog.number_service import next_number
from app.modules.doc_catalog.numbering_rule_model import DocumentNumberingRule
from app.modules.doc_catalog.numbering_rule_service import resolve_rule

ID_SCHEME_PERMANENT = 1  # mã tài liệu bất biến
ID_SCHEME_BY_BOOK = 2    # số hiệu theo sổ

#  Bỏ trống `issue_code` thì mã hiển thị vẫn phải đọc được, nên có phần thay thế
#  này. Không phải để dùng lâu dài — P1-T05 sẽ khóa mã lại sau khi đã cấp số,
#  nên đơn vị nào định cấp số thật thì phải khai `issue_code` trước.
_FALLBACK = "DEGO"


def _company_code(db: Session, company_id: int | None) -> str:
    company = db.get(Company, company_id) if company_id else None
    return (getattr(company, "issue_code", "") or "").strip() or _FALLBACK


def _department_code(db: Session, department_id: int | None,
                     company_id: int | None = None) -> str:
    dept = db.get(Department, department_id) if department_id else None
    # A05: đơn vị kinh doanh / ban dự án không xuất hiện trong số hiệu.
    if not dept or getattr(dept, "kind", 1) != 1:
        return ""

    if company_id:
        from app.modules.department.model import DepartmentCompany
        link = (
            db.query(DepartmentCompany)
            .filter(DepartmentCompany.department_id == department_id,
                    DepartmentCompany.company_id == company_id,
                    DepartmentCompany.is_active.is_(True))
            .one_or_none()
        )
        if link and (link.issue_code_override or "").strip():
            return link.issue_code_override.strip()
    return (getattr(dept, "issue_code", "") or "").strip()


def permanent_scope_key(company_code: str, type_code: str) -> str:
    """`doc:DEGO:QC` — một bộ đếm cho mỗi (pháp nhân × loại), **không kèm năm**."""
    return f"doc:{company_code}:{type_code}"


def yearly_scope_key(company_code: str, year: int, type_code: str) -> str:
    """`out:DEGO:2026:TB` — bộ đếm theo (pháp nhân × năm × loại)."""
    return f"out:{company_code}:{year}:{type_code}"


def format_permanent(company_code: str, type_code: str, seq: int) -> str:
    """`DEGO-QC-012`."""
    return f"{company_code}-{type_code}-{seq:03d}"


def format_yearly(seq: int, year: int, type_code: str, dept_code: str, company_code: str) -> str:
    """`08/2026/TB-NS-DEGO`; phòng ban chưa khai mã thì bỏ đoạn giữa."""
    tail = "-".join(part for part in (type_code, dept_code, company_code) if part)
    return f"{seq:02d}/{year}/{tail}"


def _book(db: Session, book_id: int | None):
    from app.modules.doc_catalog.book_model import DocumentBook

    return db.get(DocumentBook, book_id) if book_id else None


def _rule_scope_key(rule: DocumentNumberingRule, company_code: str, year: int) -> str:
    period = str(year) if rule.reset_yearly else "all"
    return f"rule:{rule.id}:{company_code}:{period}"


def _rule_counter_year(rule: DocumentNumberingRule, year: int) -> int:
    """Bộ đếm liên tục dùng năm 0 để `next_number` không tự đặt lại."""
    return year if rule.reset_yearly else 0


def _render_rule(
    pattern: str,
    seq: int,
    when: date,
    type_code: str,
    dept_code: str,
    company_code: str,
    book,
) -> str:
    values = {
        "STT": f"{seq:02d}",
        "Ngay": f"{when.day:02d}",
        "Thang": f"{when.month:02d}",
        "Nam": str(when.year),
        "LoaiVB": type_code,
        "PhongBan": dept_code,
        "PhapNhan": company_code,
        "SoVB": ((getattr(book, "number_prefix", "") or "").strip()
                 or (getattr(book, "code", "") or "").strip()),
    }
    result = pattern
    for token, value in values.items():
        result = result.replace(f"{{{token}}}", value)
    # Token tùy chọn trống không được để lại chuỗi kiểu `TB--DEGO`.
    result = re.sub(r"-{2,}", "-", result)
    result = re.sub(r"/{2,}", "/", result)
    result = re.sub(r"\s{2,}", " ", result)
    return result.strip(" /-")


def _matching_rule(db: Session, doc_type: DocType, book_id: int | None):
    book = _book(db, book_id)
    # Văn bản chưa vào sổ thuộc chiều nội bộ. Nếu có sổ thì chiều lấy từ chính
    # sổ, tránh lưu hai nguồn sự thật có thể mâu thuẫn nhau.
    direction = book.kind if book else 3
    return resolve_rule(db, direction, doc_type.id, book_id), book


def peek(db: Session, doc_type: DocType, company_id: int | None,
         department_id: int | None, when: date, book_id: int | None = None) -> str:
    """Số hiệu SẼ cấp — chỉ để xem trước trên màn hình, **không chiếm số**.

    Con số này lệch được nếu có người cấp số ngay sau khi màn hình đọc xong. Đó
    là chấp nhận được với một dòng xem trước (`van-thu` D08); tuyệt đối không ghi
    giá trị này xuống bản ghi.
    """
    from app.modules.doc_catalog.book_model import NumberSequence

    company_code = _company_code(db, company_id)
    type_code = (doc_type.code or "").strip()
    permanent = doc_type.id_scheme == ID_SCHEME_PERMANENT

    year = when.year
    rule, book = _matching_rule(db, doc_type, book_id) if not permanent else (None, None)
    key = (
        permanent_scope_key(company_code, type_code)
        if permanent
        else _rule_scope_key(rule, company_code, year)
        if rule
        else yearly_scope_key(company_code, year, type_code)
    )
    row = db.query(NumberSequence).filter(NumberSequence.scope_key == key).one_or_none()
    counter_year = _rule_counter_year(rule, year) if rule else year
    start_no = rule.start_no if rule else 1
    if permanent:
        seq = 1 if row is None else row.current_no + 1
    else:
        seq = start_no if row is None or row.year != counter_year else row.current_no + 1

    if permanent:
        return format_permanent(company_code, type_code, seq)
    if rule:
        return _render_rule(
            rule.pattern, seq, when, type_code,
            _department_code(db, department_id, company_id), company_code, book,
        )
    return format_yearly(
        seq, year, type_code,
        _department_code(db, department_id, company_id), company_code,
    )


def assign(db: Session, doc, doc_type: DocType, year: int) -> None:
    """Cấp số THẬT và ghi thẳng lên bản ghi. **Gọi trong transaction đang ghi `doc`.**

    Gọi lại trên một văn bản đã có số thì không làm gì — số đã phát ra ngoài,
    cấp lại là ra hai văn bản mang hai số khác nhau cho cùng một nội dung.
    """
    if doc.doc_code or doc.issue_number:
        return

    company_code = _company_code(db, doc.company_id)
    type_code = (doc_type.code or "").strip()

    if doc_type.id_scheme == ID_SCHEME_PERMANENT:
        key = permanent_scope_key(company_code, type_code)
        seq = next_number(db, key, year)
        doc.seq_no, doc.issue_year = seq, year
        doc.doc_code = format_permanent(company_code, type_code, seq)
        return

    rule, book = _matching_rule(db, doc_type, doc.book_id)
    if rule:
        key = _rule_scope_key(rule, company_code, year)
        seq = next_number(
            db, key, _rule_counter_year(rule, year), rule.start_no,
        )
        when = doc.effective_date or date.today()
        doc.seq_no, doc.issue_year = seq, year
        doc.numbering_rule_id = rule.id
        doc.issue_number = _render_rule(
            rule.pattern, seq, when, type_code,
            _department_code(db, doc.department_id, doc.company_id), company_code, book,
        )
        return

    key = yearly_scope_key(company_code, year, type_code)
    seq = next_number(db, key, year)
    doc.seq_no, doc.issue_year = seq, year
    doc.issue_number = format_yearly(
        seq, year, type_code,
        _department_code(db, doc.department_id, doc.company_id), company_code
    )
