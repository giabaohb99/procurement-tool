"""Nghiệp vụ SỔ VĂN BẢN.

Viết tay chứ không dùng `make_crud_router` vì ba việc mà router chung không lo
được: bảng thành viên đi kèm, số kế tiếp phải tính lúc đọc, và ràng buộc "sổ đã
cấp số thì không xóa, không đổi mã".
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from .book_model import DocumentBook, DocumentBookMember, NumberSequence
from .book_schema import DocumentBookCreate, DocumentBookUpdate
from .number_service import book_scope_key, format_book_number, peek_book_number

#  Tiền tố mã sổ tự sinh theo loại.
_CODE_PREFIX = {1: "SD", 2: "SDI", 3: "SNB"}

ROLE_MANAGER = 1
ROLE_VIEWER = 2


def _generate_code(db: Session, kind: int) -> str:
    prefix = _CODE_PREFIX.get(kind, "SO")
    n = db.query(DocumentBook).filter(DocumentBook.code.like(f"{prefix}%")).count()
    #  Vòng lặp phòng trường hợp mã đã bị người dùng đặt tay trùng.
    while True:
        n += 1
        code = f"{prefix}{n:03d}"
        if not db.query(DocumentBook).filter(DocumentBook.code == code).first():
            return code


def _replace_members(db: Session, book_id: int, employee_ids: list[int], role: int, actor: int):
    """Ghi đè danh sách thành viên một vai trò.

    Xóa rồi thêm lại thay vì so sánh từng dòng: bảng này chỉ vài dòng mỗi sổ, mà
    so sánh thủ công là chỗ hay sót người khi bỏ tên khỏi danh sách.
    """
    db.query(DocumentBookMember).filter(
        DocumentBookMember.book_id == book_id, DocumentBookMember.role == role
    ).delete(synchronize_session=False)

    for employee_id in dict.fromkeys(employee_ids):  # bỏ trùng, giữ thứ tự
        db.add(DocumentBookMember(
            book_id=book_id, employee_id=employee_id, role=role,
            created_by=actor, updated_by=actor,
        ))


def members_of(db: Session, book_id: int, role: int) -> list[int]:
    rows = db.query(DocumentBookMember.employee_id).filter(
        DocumentBookMember.book_id == book_id, DocumentBookMember.role == role
    ).all()
    return [r[0] for r in rows]


def create_book(db: Session, data: DocumentBookCreate, actor: int) -> DocumentBook:
    code = data.code or _generate_code(db, data.kind)
    if db.query(DocumentBook).filter(DocumentBook.code == code).first():
        raise HTTPException(400, "Mã sổ đã tồn tại")

    payload = data.model_dump(exclude={"code", "manager_ids", "viewer_ids"})
    book = DocumentBook(**payload, code=code, created_by=actor, updated_by=actor)
    db.add(book)
    db.flush()

    _replace_members(db, book.id, data.manager_ids, ROLE_MANAGER, actor)
    _replace_members(db, book.id, data.viewer_ids, ROLE_VIEWER, actor)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: int, data: DocumentBookUpdate, actor: int) -> DocumentBook:
    book = db.get(DocumentBook, book_id)
    if not book:
        raise HTTPException(404, "Không tìm thấy sổ")

    values = data.model_dump(exclude_unset=True, exclude={"manager_ids", "viewer_ids"})

    #  Đổi `start_no` sau khi sổ đã cấp số là làm lệch cả sổ: số đã phát ra ngoài
    #  rồi thì không kéo về được nữa.
    if "start_no" in values and values["start_no"] != book.start_no and issued_count(db, book):
        raise HTTPException(400, "Sổ đã cấp số, không đổi được số bắt đầu")

    for key, value in values.items():
        setattr(book, key, value)
    book.updated_by = actor

    if data.manager_ids is not None:
        _replace_members(db, book.id, data.manager_ids, ROLE_MANAGER, actor)
    if data.viewer_ids is not None:
        _replace_members(db, book.id, data.viewer_ids, ROLE_VIEWER, actor)

    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int):
    """Xóa sổ — chỉ khi sổ CHƯA cấp số nào.

    Giống AMIS: sổ đã có văn bản thì không xóa. Ở đây chặt hơn một bậc, chặn
    ngay từ lúc bộ đếm khác 0: số đã cấp là số đã phát ra ngoài, xóa sổ đi thì
    không còn gì để đối chiếu khi có người cầm văn bản mang số đó đến hỏi.
    """
    book = db.get(DocumentBook, book_id)
    if not book:
        raise HTTPException(404, "Không tìm thấy sổ")
    if issued_count(db, book):
        raise HTTPException(400, "Sổ đã cấp số, không xóa được. Hãy chuyển sang Ngừng dùng.")

    db.query(DocumentBookMember).filter(DocumentBookMember.book_id == book_id).delete(
        synchronize_session=False
    )
    db.delete(book)
    db.commit()


def issued_count(db: Session, book: DocumentBook, year: int | None = None) -> int:
    """Đã cấp bao nhiêu số trong năm (sổ không reset thì tính từ đầu sổ)."""
    year = year or date.today().year
    key = book_scope_key(book.code, year, book.reset_yearly)
    row = db.query(NumberSequence).filter(NumberSequence.scope_key == key).one_or_none()
    if row is None or (book.reset_yearly and row.year != year):
        return 0
    return max(0, row.current_no - book.start_no + 1)


def serialize(db: Session, book: DocumentBook, year: int | None = None) -> dict:
    """Bản ghi kèm phần tính thêm cho màn hình: số kế tiếp, tên pháp nhân, người quản lý."""
    year = year or date.today().year
    manager_ids = members_of(db, book.id, ROLE_MANAGER)
    viewer_ids = members_of(db, book.id, ROLE_VIEWER)
    next_no = peek_book_number(db, book, year)

    company = db.get(Company, book.company_id) if book.company_id else None
    department = db.get(Department, book.department_id) if book.department_id else None
    managers = (
        db.query(Employee.full_name).filter(Employee.id.in_(manager_ids)).all()
        if manager_ids else []
    )

    return {
        "id": book.id,
        "code": book.code,
        "name": book.name,
        "kind": book.kind,
        "description": book.description,
        "company_id": book.company_id,
        "department_id": book.department_id,
        "number_prefix": book.number_prefix,
        "reset_yearly": book.reset_yearly,
        "start_no": book.start_no,
        "is_active": book.is_active,
        "manager_ids": manager_ids,
        "viewer_ids": viewer_ids,
        "next_no": next_no,
        "next_number_display": format_book_number(book, next_no, year),
        "issued_count": issued_count(db, book, year),
        "company_name": company.name if company else "",
        "department_name": department.name if department else "",
        "manager_names": [m[0] for m in managers],
    }
