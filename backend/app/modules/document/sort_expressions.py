"""Biểu thức SẮP XẾP tại server cho danh sách VĂN BẢN ĐI (duoc-CR-744).

Trước đây `GET /api/documents` chỉ nhận `?sort=-col` với 4 cột (`id`, `book_seq_no`, `issued_at`,
`created_at`) và bảng giao diện không có cột nào bấm được. Nay `sort_by`/`sort_dir` (cùng khuôn mọi màn
danh sách) xếp theo ĐÚNG thứ ô đang hiện, trên CẢ TẬP (đúng qua phân trang, và tệp Export ra cùng thứ tự):

- Cột chữ: ô trống (hiện trống / "—") luôn xuống CUỐI, cả chiều tăng lẫn giảm.
- Số hiệu: chữ ô hiện là `doc_code` rồi tới `issue_number` (giống `serializer.base_fields.display_code`).
- Loại / Pháp nhân / Phòng chủ trì / Sổ / Người chịu trách nhiệm / Người soạn: xếp theo TÊN, không theo `*_id`.
- Số vào sổ: xếp theo (tiền tố sổ, năm, số thứ tự) — xếp theo chuỗi "CVĐ 08/2026" sẽ đặt số 08 của năm
  2027 trước số 09 của năm 2026. Văn bản chưa vào sổ là ô trống.
- Bản: xếp theo (số lớn, số nhỏ) của bản đang dùng — chuỗi "2.10" sẽ đứng trước "2.9".
- Trạng thái: xếp theo HẠNG vòng đời (Nháp → … → Có hiệu lực → Hết hiệu lực → …), tính cả nhãn "Hết hiệu
  lực" / "Chưa hiệu lực" mà giao diện suy ra từ ngày (`effectiveLabel`), không theo mã số thô.
- Mức mật / Độ khẩn: mã thang đã tăng dần theo mức độ.
- Tệp: số tệp đính kèm của bản đang dùng; 0 hiện trống nên là ô trống.
- Khóa phụ luôn là `id` giảm dần để thứ tự ổn định giữa các trang.

Cột "Thư mục" KHÔNG xếp được: đường dẫn thư mục hiện trên ô đã lọc theo quyền xem thư mục của TỪNG người
xem, xếp ở SQL sẽ lộ thứ tự của thư mục họ không thấy.
"""
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import aliased

from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.core.vn_time import vn_today
from app.modules.attachment.model import FileLink
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.book_model import DocumentBook
from app.modules.doc_catalog.model import DocType
from app.modules.employee.model import Employee

from . import model as m
from .model import Document
from .serializer import ATTACH_ENTITY
from .version_model import DocumentVersion

_OWNER = aliased(Employee)
_DRAFTER = aliased(Employee)

#  Hạng vòng đời của trạng thái (nhỏ -> lớn). Hai nhãn suy ra từ ngày cũng có hạng riêng.
_RANK_NOT_YET_EFFECTIVE = 6
_RANK_EXPIRED = 8
_STATUS_RANK = {
    m.STATUS_DRAFT: 1,
    m.STATUS_RETURNED: 2,
    m.STATUS_SUBMITTED: 3,
    m.STATUS_PENDING_ISSUE: 4,
    m.STATUS_APPROVED: 5,
    m.STATUS_EFFECTIVE: 7,
    m.STATUS_EXPIRED: _RANK_EXPIRED,
    m.STATUS_REPLACED: 9,
    m.STATUS_REVOKED: 10,
    m.STATUS_ARCHIVED: 11,
    m.STATUS_REJECTED: 12,
}


def _name_of(id_column, name_column, fk_column):
    """Tên bản ghi mà `fk_column` trỏ tới; không có -> NULL (ô trống)."""
    return select(name_column).where(id_column == fk_column).limit(1).scalar_subquery()


def _status_rank(today):
    """Hạng trạng thái đúng như chữ giao diện hiện (xem `effectiveLabel` ở frontend)."""
    effective = Document.status == m.STATUS_EFFECTIVE
    expired = and_(effective, Document.expire_date.is_not(None), Document.expire_date < today)
    not_yet = and_(effective, Document.effective_date.is_not(None), Document.effective_date > today)
    return case(
        (expired, _RANK_EXPIRED),
        (not_yet, _RANK_NOT_YET_EFFECTIVE),
        *[(Document.status == code, rank) for code, rank in _STATUS_RANK.items()],
        else_=99,
    )


def _book_prefix():
    return select(DocumentBook.number_prefix).where(DocumentBook.id == Document.book_id).limit(1).scalar_subquery()


def _version_part(column):
    return (select(column).where(DocumentVersion.id == Document.current_version_id).limit(1).scalar_subquery())


def _attachment_count():
    count = (select(func.count(FileLink.id))
             .where(FileLink.entity == ATTACH_ENTITY, FileLink.entity_id == Document.current_version_id)
             .scalar_subquery())
    return func.nullif(count, 0)


def _spec(today) -> dict:
    """(biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống."""
    return {
        "id": (Document.id, False),
        "display_code": (func.coalesce(func.nullif(Document.doc_code, ""), func.nullif(Document.issue_number, "")), True),
        "title": (Document.title, True),
        "doc_type_name": (_name_of(DocType.id, DocType.name, Document.doc_type_id), True),
        "company_name": (_name_of(Company.id, Company.name, Document.company_id), True),
        "department_name": (_name_of(Department.id, Department.name, Document.department_id), True),
        "book_name": (_name_of(DocumentBook.id, DocumentBook.name, Document.book_id), True),
        "owner_name": (_name_of(_OWNER.id, _OWNER.full_name, Document.owner_employee_id), True),
        "drafter_name": (_name_of(_DRAFTER.id, _DRAFTER.full_name, Document.drafter_employee_id), True),
        #  Số trong sổ (tab "Văn bản trong sổ"): chưa vào sổ là NULL nên là ô trống.
        "book_seq_no": (Document.book_seq_no, False),
        "status": (_status_rank(today), False),
        "effective_date": (Document.effective_date, False),
        "expire_date": (Document.expire_date, False),
        "secrecy_level": (Document.secrecy_level, False),
        "urgency": (Document.urgency, False),
        "legacy_code": (Document.legacy_code, True),
        "storage_location": (Document.storage_location, True),
        "attachment_count": (_attachment_count(), False),
        "created_at": (Document.created_at, False),
    }


def _compound_order(blank_expr, parts, direction: str) -> list:
    """Xếp theo NHIỀU phần: ô trống (theo `blank_expr`) xuống cuối, rồi lần lượt từng phần theo `direction`."""
    blank_flag = case((blank_expr.is_(None), 1), else_=0).asc()
    return [blank_flag, *[(p.desc() if direction == "desc" else p.asc()) for p in parts]]


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách mệnh đề ORDER BY (đã gồm khóa phụ `id`); rỗng nếu khóa lạ -> nơi gọi dùng thứ tự mặc định."""
    key = (sort_by or "").strip()
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    if key == "book_number_display":
        #  Chưa vào sổ (`book_seq_no` rỗng hoặc 0) là ô trống.
        seq = func.nullif(Document.book_seq_no, 0)
        order = _compound_order(seq, [func.coalesce(_book_prefix(), ""), Document.book_year, seq], direction)
    elif key == "version_no":
        major, minor = _version_part(DocumentVersion.major), _version_part(DocumentVersion.minor)
        order = _compound_order(major, [major, minor], direction)
    else:
        spec = _spec(vn_today()).get(key)
        if spec is None:
            return []
        expr, is_text = spec
        order = build_blank_last_order(expr, direction, is_text)
    return with_stable_tiebreak(order, Document.id)
