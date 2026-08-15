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
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.doc_catalog.number_service import next_number

ID_SCHEME_PERMANENT = 1  # mã tài liệu bất biến
ID_SCHEME_BY_BOOK = 2    # số hiệu theo sổ

#  Bỏ trống `issue_code` thì mã hiển thị vẫn phải đọc được, nên có phần thay thế
#  này. Không phải để dùng lâu dài — P1-T05 sẽ khóa mã lại sau khi đã cấp số,
#  nên đơn vị nào định cấp số thật thì phải khai `issue_code` trước.
_FALLBACK = "DEGO"


def _company_code(db: Session, company_id: int | None) -> str:
    company = db.get(Company, company_id) if company_id else None
    return (getattr(company, "issue_code", "") or "").strip() or _FALLBACK


def _department_code(db: Session, department_id: int | None) -> str:
    dept = db.get(Department, department_id) if department_id else None
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


def peek(db: Session, doc_type: DocType, company_id: int | None,
         department_id: int | None, year: int) -> str:
    """Số hiệu SẼ cấp — chỉ để xem trước trên màn hình, **không chiếm số**.

    Con số này lệch được nếu có người cấp số ngay sau khi màn hình đọc xong. Đó
    là chấp nhận được với một dòng xem trước (`van-thu` D08); tuyệt đối không ghi
    giá trị này xuống bản ghi.
    """
    from app.modules.doc_catalog.book_model import NumberSequence

    company_code = _company_code(db, company_id)
    type_code = (doc_type.code or "").strip()
    permanent = doc_type.id_scheme == ID_SCHEME_PERMANENT

    key = (permanent_scope_key(company_code, type_code) if permanent
           else yearly_scope_key(company_code, year, type_code))
    row = db.query(NumberSequence).filter(NumberSequence.scope_key == key).one_or_none()
    #  Bộ đếm theo năm mà dòng còn ở năm cũ thì sang năm mới bắt đầu lại từ 1.
    seq = 1 if row is None or (not permanent and row.year != year) else row.current_no + 1

    if permanent:
        return format_permanent(company_code, type_code, seq)
    return format_yearly(seq, year, type_code, _department_code(db, department_id), company_code)


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

    key = yearly_scope_key(company_code, year, type_code)
    seq = next_number(db, key, year)
    doc.seq_no, doc.issue_year = seq, year
    doc.issue_number = format_yearly(
        seq, year, type_code, _department_code(db, doc.department_id), company_code
    )
