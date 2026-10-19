"""Luật đọc BẢN LƯU TRỮ Hợp đồng lao động ở phân hệ Văn bản (duoc-CR-629).

Văn bản D là bản lưu trữ HĐLĐ  ⇔  tồn tại dòng `tab_labor_contract` L (kể cả đã xóa mềm) với
`L.document_id = D.id`. Nhận diện bằng LIÊN KẾT chứ không bằng mã loại: đổi mã/tên loại `HDLD`
trên giao diện không mở khóa.

  * ĐỌC D  ⇔  người dùng có `labor_contract.read` VÀ L nằm trong phạm vi `labor_contract` của họ.
    Không tính phạm vi `document` (kể cả `all`), chia đích danh, CẤM, sổ, duyệt, phạm vi áp dụng,
    clone, chủ/người tạo — tức người lao động, văn thư và admin-không-có-`labor_contract` đều KHÔNG đọc.
  * GHI / XÓA D  ⇔  không bao giờ (bản lưu trữ chỉ đọc; mọi thay đổi đi từ Nhân sự).
  * Thao tác TẠO văn bản mới từ D (sao chép, clone, trích, ký) bị chặn 409.

⚠️ Import `LaborContract` CỤC BỘ trong hàm: `labor_contract` gọi ngược `document.service`
(vòng import).
"""
from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.scoping import scope_condition

from .model import Document
from .type_metadata import LABOR_CONTRACT_DOC_TYPE


def _labor_contract_model():
    from app.modules.labor_contract.model import LaborContract
    return LaborContract


def archive_ids():
    """Truy vấn con: id mọi văn bản là bản lưu trữ HĐLĐ (kể cả HĐ đã xóa mềm)."""
    lc = _labor_contract_model()
    return select(lc.document_id).where(lc.document_id > 0)


def _has_read(profile: dict) -> bool:
    from app.modules.labor_contract.access import has_perm
    return has_perm(profile, "labor_contract", "read")


def readable_archive_ids(user, profile: dict):
    """Truy vấn con: id bản lưu trữ người này ĐỌC được; `None` nếu thiếu `labor_contract.read`."""
    if not _has_read(profile):
        return None
    lc = _labor_contract_model()
    q = select(lc.document_id).where(lc.document_id > 0)
    scope = scope_condition(lc, "labor_contract", user, profile, "read")
    if scope is not None:
        q = q.where(scope)
    return q


def archive_type_ids():
    """Truy vấn con: id loại văn bản `HDLD` (theo MÃ). Văn bản thuộc loại này mà KHÔNG có HĐ trỏ tới
    (mồ côi do lỗi giữa hai commit, do downgrade…) không ai đọc được — kể cả quản trị (review M1)."""
    from app.modules.doc_catalog.model import DocType
    return select(DocType.id).where(DocType.code == LABOR_CONTRACT_DOC_TYPE)


def hdld_type_id(db: Session) -> int | None:
    """Id loại `HDLD` (theo mã) — nhớ trong `db.info` của phiên (một request) để `can()` gọi nhiều lần
    không hỏi lại. Chỉ nhớ khi TÌM THẤY (loại tạo sau đó không bị bỏ sót). Loại bị khóa sửa/xóa mã
    (`doc_catalog.guard`) nên id không đổi trong một phiên."""
    cached = db.info.get("hdld_type_id")
    if cached:
        return cached
    from app.modules.doc_catalog.model import DocType
    found = db.query(DocType.id).filter(DocType.code == LABOR_CONTRACT_DOC_TYPE).scalar()
    if found:
        db.info["hdld_type_id"] = found
    return found


def is_orphan_archive_type(db: Session, doc: Document) -> bool:
    """Văn bản loại `HDLD` (theo mã). Gọi SAU khi đã loại trường hợp có HĐ trỏ tới."""
    if not doc.doc_type_id:
        return False
    return doc.doc_type_id == hdld_type_id(db)


def archive_doc_set():
    """Truy vấn con: id MỌI văn bản thuộc diện bản lưu trữ — có HĐ trỏ tới HOẶC loại `HDLD` (kể cả đã
    xóa mềm / mồ côi / HĐ đã bị xóa cứng). Nhật ký dùng tập này để giấu VĨNH VIỄN (review N1)."""
    return select(Document.id).where(
        or_(Document.id.in_(archive_ids()), Document.doc_type_id.in_(archive_type_ids())))


def wrap_visible(direct, user, profile: dict, action: str):
    """Bọc điều kiện danh sách: văn thường (`direct`) trừ bản lưu trữ, rồi cộng bản lưu trữ đọc được.

    ⚠️ Không bao giờ trả `None` — luôn có vế `NOT IN archive`.
    Văn bản loại HDLD mà không có HĐ trỏ tới (mồ côi) bị loại ở vế thường ⇒ không ai thấy.
    """
    normal = ~Document.id.in_(archive_ids()) & or_(Document.doc_type_id.is_(None),
                                                   ~Document.doc_type_id.in_(archive_type_ids()))
    if direct is not None:
        normal = normal & direct
    if action != "read":
        return normal
    readable = readable_archive_ids(user, profile)
    if readable is None:
        return normal
    return or_(normal, Document.id.in_(readable))


def contract_of(db: Session, doc: Document):
    """HĐLĐ đang trỏ tới văn bản này (1 truy vấn, KHÔNG lọc xóa mềm); `None` nếu là văn bản thường."""
    lc = _labor_contract_model()
    return (db.query(lc).filter(lc.document_id == doc.id).order_by(lc.id).first())


def can_read(db: Session, contract, user, profile: dict) -> bool:
    """Người này đọc được HĐ `contract` không — hỏi lại DB bằng đúng điều kiện phạm vi của danh sách."""
    if not _has_read(profile):
        return False
    lc = _labor_contract_model()
    scope = scope_condition(lc, "labor_contract", user, profile, "read")
    if scope is None:
        return True
    return db.query(lc.id).filter(lc.id == contract.id, scope).first() is not None


def can_write(db: Session, contract, user, profile: dict) -> bool:
    """duoc-CR-640: SỬA bản lưu trữ ⇔ đọc được HĐ VÀ có `labor_contract.write` phủ HĐ đó (cùng người sửa được HĐ ở
    Nhân sự). HĐ đã xóa mềm thì chỉ đọc. Không nguồn quyền nào của Văn bản được tính."""
    if getattr(contract, "is_deleted", False) or not can_read(db, contract, user, profile):
        return False
    from app.modules.labor_contract.access import has_perm
    #  Khớp đúng những gì ROUTE cho phép: lớp 1 của sửa / tải tệp đòi `document.write` (xem seed `hr_profile`).
    if not has_perm(profile, "labor_contract", "write") or not has_perm(profile, "document", "write"):
        return False
    lc = _labor_contract_model()
    scope = scope_condition(lc, "labor_contract", user, profile, "write")
    if scope is None:
        return True
    return db.query(lc.id).filter(lc.id == contract.id, scope).first() is not None


#  Trường do ĐỒNG BỘ từ hợp đồng sở hữu (duoc-CR-640): sửa tay sẽ bị đồng bộ ghi đè và `keywords` còn là dấu nhận
#  văn bản mồ côi nên cấm sửa. Các trường còn lại (ghi chú, nơi lưu bản giấy, thư mục, nội dung, tệp…) sửa được.
SYNC_OWNED_FIELDS = ("title", "summary", "keywords", "effective_date", "expire_date", "doc_type_id", "book_id",
                     "company_id", "department_id", "owner_employee_id")


def ensure_no_sync_owned_change(doc: Document, changes: dict) -> None:
    """409 nếu `changes` (PATCH) ĐỔI giá trị một trường do đồng bộ sở hữu; gửi lại đúng giá trị cũ thì bỏ qua."""
    touched = [f for f in SYNC_OWNED_FIELDS if f in changes and changes[f] != getattr(doc, f, None)]
    if touched:
        raise HTTPException(409, "Các trường này do hợp đồng lao động ở phân hệ Nhân sự quyết định, "
                                 "không sửa ở Văn bản: " + ", ".join(touched))


def is_archive_document(db: Session, doc: Document) -> bool:
    """Loại `HDLD` HOẶC có HĐ trỏ tới — hai điều kiện (phòng đổi mã loại / chạy đua lúc tạo)."""
    if contract_of(db, doc) is not None:
        return True
    from app.modules.doc_catalog.model import DocType
    code = db.query(DocType.code).filter(DocType.id == doc.doc_type_id).scalar()
    return (code or "").upper() == LABOR_CONTRACT_DOC_TYPE


def ensure_not_archive(db: Session, doc: Document) -> None:
    """Chặn thao tác dẫn xuất (sao chép, clone, trích, ký) từ bản lưu trữ HĐLĐ."""
    if contract_of(db, doc) is not None:
        raise HTTPException(409, "Bản lưu trữ hợp đồng lao động không dùng được thao tác này "
                                 "(chia sẻ, sao chép, quan hệ, gửi duyệt, ký, ban hành, xóa…); "
                                 "trạng thái do hợp đồng ở phân hệ Nhân sự quyết định")


def ensure_not_system_type(db: Session, doc_type_id: int | None) -> None:
    """Người dùng không được tạo / đổi văn bản sang loại `HDLD` — loại này chỉ do Nhân sự sinh."""
    if not doc_type_id:
        return
    from app.modules.doc_catalog.model import DocType
    code = db.query(DocType.code).filter(DocType.id == doc_type_id).scalar()
    if (code or "").upper() == LABOR_CONTRACT_DOC_TYPE:
        raise HTTPException(400, "Loại này chỉ sinh từ phân hệ Nhân sự")


def check_doc_type(db: Session) -> list[str]:
    """Điều kiện DỪNG triển khai (review H3): loại `HDLD` có sẵn mà không phải do seed CR-629 tạo.

    Seed chỉ chèn loại còn thiếu nên KHÔNG tự sửa loại người dùng đã tạo. Trả danh sách vấn đề (rỗng = ổn):
    loại không `is_personal` / đang bật duyệt-ký-cấp số-lưu khác mong đợi / đã tắt, và số văn bản loại này
    chưa có HĐ trỏ tới (mồ côi hoặc văn bản tay của văn thư — những văn bản ấy sẽ bị ẨN khỏi mọi người)."""
    from app.modules.doc_catalog.model import DocType

    row = db.query(DocType).filter(DocType.code == LABOR_CONTRACT_DOC_TYPE).first()
    if row is None:
        return []
    problems = []
    if not row.is_personal:
        problems.append("loại HDLD không bật is_personal")
    if row.needs_approval or row.needs_signature or row.number_when != 2:
        problems.append("loại HDLD đang bật duyệt/ký hoặc cấp số (bản lưu trữ phải không duyệt, không ký, không cấp số)")
    if not row.is_active:
        problems.append("loại HDLD đang tắt")
    unlinked = (db.query(Document.id).filter(Document.doc_type_id == row.id,
                                             Document.is_deleted == False,  # noqa: E712
                                             ~Document.id.in_(archive_ids())).count())
    if unlinked:
        problems.append(f"{unlinked} văn bản loại HDLD chưa gắn với hợp đồng lao động nào (sẽ bị ẩn với mọi người)")
    return problems


# ── Nhật ký (audit / system_log) — review H2 + lượt 2 ─────────────────────────────────────
def blocked_archive_doc_ids(db: Session, viewer, doc_ids) -> set[int]:
    """Trong `doc_ids`, những văn bản thuộc diện bản lưu trữ HĐLĐ mà `viewer` KHÔNG đọc được.

    «Thuộc diện» = có HĐ trỏ tới HOẶC loại HDLD (kể cả HĐ đã xóa cứng, văn bản xóa mềm / mồ côi) ⇒ dòng
    nhật ký không hiện lại khi HĐ biến mất. `viewer = (user, profile)`; `None` ⇒ đóng."""
    ids = {int(i) for i in doc_ids if i}
    if not ids:
        return set()
    lc = _labor_contract_model()
    linked = {d for (d,) in db.query(lc.document_id).filter(lc.document_id.in_(ids)).all()}
    typed = hdld_type_id(db)
    by_type = ({i for (i,) in db.query(Document.id).filter(Document.id.in_(ids), Document.doc_type_id == typed).all()}
               if typed else set())
    archived = linked | by_type
    if not archived:
        return set()
    readable = readable_archive_ids(*viewer) if viewer else None
    if readable is None:
        return archived
    ok = {d for (d,) in db.execute(readable.where(lc.document_id.in_(archived))).all()}
    return archived - ok


def blocked_contract_ids(db: Session, viewer, contract_ids) -> set[int]:
    """Trong `contract_ids`, những HĐLĐ mà `viewer` không đọc được.

    HĐ KHÔNG còn tồn tại (xóa cứng cùng hồ sơ nhân sự) coi là chặn, trừ người đọc HĐLĐ phạm vi không giới hạn."""
    ids = {int(i) for i in contract_ids if i}
    if not ids:
        return set()
    lc = _labor_contract_model()
    if not viewer or not _has_read(viewer[1]):
        return ids
    scope = scope_condition(lc, "labor_contract", viewer[0], viewer[1], "read")
    if scope is None:
        return set()
    ok = {i for (i,) in db.query(lc.id).filter(lc.id.in_(ids), scope).all()}
    return ids - ok


def audit_row_filter(db: Session, user):
    """Điều kiện lọc `tab_audit_log`: dòng của bản lưu trữ HĐLĐ (`entity=document`) và của chính HĐLĐ
    (`entity=labor_contract`) chỉ hiện cho người ĐỌC được chúng — kể cả quản trị có quyền `audit` mà không có
    `labor_contract`. Tập «bản lưu trữ» gồm cả văn bản loại HDLD / HĐ đã xóa cứng (giấu vĩnh viễn, N1)."""
    from app.core.auth import get_perm_profile
    from app.modules.audit.model import AuditLog

    profile = get_perm_profile(db, user)
    lc = _labor_contract_model()
    doc_hidden = (AuditLog.entity == "document") & AuditLog.entity_id.in_(archive_doc_set())
    contract_row = AuditLog.entity == "labor_contract"
    readable_docs = readable_archive_ids(user, profile)
    if not _has_read(profile):
        return ~(doc_hidden | contract_row)
    scope = scope_condition(lc, "labor_contract", user, profile, "read")
    if scope is None:
        contract_ok = contract_row
    else:
        contract_ok = contract_row & AuditLog.entity_id.in_(select(lc.id).where(scope))
    doc_ok = doc_hidden & AuditLog.entity_id.in_(readable_docs)
    # dòng KHÔNG thuộc diện ẩn  |  dòng thuộc diện ẩn mà đọc được
    return or_(~(doc_hidden | contract_row), doc_ok, contract_ok)
