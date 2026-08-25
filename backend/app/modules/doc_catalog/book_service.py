"""Nghiệp vụ SỔ VĂN BẢN.

Viết tay chứ không dùng `make_crud_router` vì ba việc mà router chung không lo
được: bảng thành viên đi kèm, số kế tiếp phải tính lúc đọc, và ràng buộc "sổ đã
cấp số thì không xóa, không đổi mã".
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.company.model import Company
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


def _require_manager(manager_ids: list[int] | None):
    """Sổ phải có ít nhất một người quản lý.

    Không phải ràng buộc hình thức: người quản lý là người duy nhất sửa và xóa
    được sổ. Sổ không cử ai thì lúc cần đóng sổ hay sửa tiền tố, không ai có
    thẩm quyền làm ngoài quản trị hệ thống.
    """
    if manager_ids is not None and not manager_ids:
        raise HTTPException(400, "Sổ phải có ít nhất một người quản lý")


def create_book(db: Session, data: DocumentBookCreate, actor: int) -> DocumentBook:
    _require_manager(data.manager_ids)
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

    _require_manager(data.manager_ids)
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

    def names(ids: list[int]) -> list[str]:
        if not ids:
            return []
        rows = db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(ids)).all()
        by_id = {r[0]: r[1] for r in rows}
        # Giữ đúng thứ tự người dùng đã chọn, bỏ id trỏ tới nhân sự đã xóa.
        return [by_id[i] for i in ids if i in by_id]

    return {
        "id": book.id,
        "code": book.code,
        "name": book.name,
        "kind": book.kind,
        "description": book.description,
        "company_id": book.company_id,
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
        "manager_names": names(manager_ids),
        "viewer_names": names(viewer_ids),
    }


def so_minh_la_thanh_vien(employee_id: int | None):
    """Truy vấn con: id các sổ mà nhân sự này ĐƯỢC KHAI ĐÍCH DANH (quản lý hoặc xem).

    `None` khi tài khoản chưa gắn hồ sơ nhân sự — lúc đó không có gì để cộng thêm.
    """
    from sqlalchemy import select

    if not employee_id:
        return None
    return (select(DocumentBookMember.book_id)
            .where(DocumentBookMember.employee_id == employee_id))


def dieu_kien_xem_so(user, profile: dict):
    """Điều kiện lọc DANH SÁCH SỔ = phạm vi vai trò **HỢP** các sổ chia đích danh.

    ⚠️ Đây là lỗi khách báo 24/08/2026: thêm người vào ô *Người xem sổ*, lưu xong,
    người đó mở trang **Sổ văn bản** vẫn thấy «Chưa có sổ văn bản đến nào khớp».
    Bảng `tab_document_book_member` có dòng, nhưng câu truy vấn danh sách chỉ chạy
    `apply_scope` — mà phạm vi vai trò chỉ biết THU HẸP (pháp nhân, người tạo),
    không biết mở thêm. Nhân viên có phạm vi `own` thì chỉ thấy sổ do chính họ mở,
    tức là không thấy gì — đúng bằng việc ô *Người xem sổ* không có tác dụng nào.

    Cùng cách ghép với `document/access_service.visible_condition`: chia đích danh
    là một NGUỒN QUYỀN CỘNG THÊM, không phải một bộ lọc.

    Trả `None` = thấy tất cả (giữ đúng nghĩa của `scope_condition`).
    """
    from sqlalchemy import or_

    from app.core.scoping import scope_condition

    pham_vi = scope_condition(DocumentBook, "document_book", user, profile, "read")
    if pham_vi is None:
        return None

    cua_toi = so_minh_la_thanh_vien(profile.get("employee_id")
                                    or getattr(user, "employee_id", None))
    if cua_toi is None:
        return pham_vi
    return or_(pham_vi, DocumentBook.id.in_(cua_toi))


def dieu_kien_sua_so(user, profile: dict, action: str = "write"):
    """Điều kiện được SỬA / XÓA một quyển sổ.

    Khác `dieu_kien_xem_so` ở nguồn cộng thêm: chỉ **người quản lý sổ** (vai 1),
    không phải mọi thành viên. Đúng câu chú thích ngay dưới ô *Người quản lý*
    trên giao diện — *«Sửa, đóng và xóa được sổ»* — mà trước đây backend không
    hề đọc tới: sửa sổ chỉ xét quyền vai trò `document_book.write`, không xét
    phạm vi và cũng không xét ai quản lý sổ nào.

    Vẫn phải có quyền vai trò `write` mới vào tới đây (`require(...)` ở tầng
    controller). Hàm này chỉ trả lời câu thứ hai: **quyển nào**.
    """
    from sqlalchemy import or_

    from app.core.scoping import scope_condition

    pham_vi = scope_condition(DocumentBook, "document_book", user, profile, action)
    if pham_vi is None:
        return None

    employee_id = profile.get("employee_id") or getattr(user, "employee_id", None)
    if not employee_id:
        return pham_vi

    from sqlalchemy import select

    quan_ly = (select(DocumentBookMember.book_id)
               .where(DocumentBookMember.employee_id == employee_id,
                      DocumentBookMember.role == ROLE_MANAGER))
    return or_(pham_vi, DocumentBook.id.in_(quan_ly))


def so_sua_duoc_hoac_404(db: Session, book_id: int, user, profile: dict,
                         action: str = "write") -> DocumentBook:
    """Như `so_xem_duoc_hoac_404` nhưng cho SỬA / XÓA. Xem `dieu_kien_sua_so`."""
    return _so_hoac_404(db, book_id, dieu_kien_sua_so(user, profile, action))


def so_xem_duoc_hoac_404(db: Session, book_id: int, user, profile: dict) -> DocumentBook:
    """Lấy MỘT sổ, đã kiểm quyền xem trên chính nó.

    ⚠️ Trước 25/08/2026 ba endpoint đọc một sổ chỉ `db.get(...)`: lọc ở danh sách
    bao nhiêu cũng vô nghĩa vì gõ thẳng id lên URL là mở được sổ của pháp nhân
    khác — kèm tên người quản lý, người xem và cả bộ đếm. Đúng cái bẫy `get_scoped`
    đã ghi trong CLAUDE.md.
    """
    return _so_hoac_404(db, book_id, dieu_kien_xem_so(user, profile))


def _so_hoac_404(db: Session, book_id: int, dieu_kien) -> DocumentBook:
    book = db.get(DocumentBook, book_id)
    if not book:
        raise HTTPException(404, "Không tìm thấy sổ")
    if dieu_kien is None:
        return book

    thay = (db.query(DocumentBook.id)
            .filter(DocumentBook.id == book_id, dieu_kien)
            .first())
    if not thay:
        #  404 chứ không 403 — cùng lý lẽ với văn bản: nói "có sổ này nhưng anh
        #  không được xem" thì chính câu đó đã lộ thứ cần giấu.
        raise HTTPException(404, "Không tìm thấy sổ")
    return book
