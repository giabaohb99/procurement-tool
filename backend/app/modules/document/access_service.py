"""Chia sẻ và kiểm quyền TRÊN TỪNG VĂN BẢN.

Quy tắc quyết định, đúng thứ tự này và không có ngoại lệ nào:

```
CẤM đích danh          →  KHÔNG được, dừng luôn (kể cả người tạo, kể cả admin)
CHO PHÉP đích danh     →  được
THÀNH VIÊN SỔ chứa nó  →  được (quản lý sổ: xem + sửa · người xem sổ: xem)
phạm vi vai trò        →  được
còn lại                →  không được
```

**Vì sao sổ là một nguồn quyền.** Sổ văn bản không chỉ là chỗ đánh số — nó là
cách văn thư phân việc: sổ Quyết định do phòng Hành chính giữ, sổ Nhân sự do
phòng Nhân sự giữ. Cấp quyền theo sổ thì khai một lần cho cả sổ, người vào sau
tự có, thay vì chia tay từng văn bản một. Danh sách thành viên nằm ở
`tab_document_book_member` (`role` 1 quản lý · 2 người xem), cấp cho **người đích
danh** chứ không theo phòng ban.

Hai chỗ dùng nó, phải dùng CẢ HAI kẻo lệch nhau:

* **Danh sách** — `visible_condition()` ghép vào câu truy vấn. Văn bản không được
  đọc thì không hiện, kể cả cái tiêu đề (K03: kết quả tìm kiếm không lộ tên văn
  bản mình không được xem).
* **Từng bản ghi** — `ensure_can()` gọi ở mọi endpoint đọc/sửa/xóa một văn bản.
  Danh sách lọc rồi mà chi tiết không kiểm thì gõ thẳng id lên URL là mở được.
"""
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.scoping import scope_condition

from .access_model import (EFFECT_ALLOW, EFFECT_DENY, SUBJECT_COMPANY,
                           SUBJECT_DEPARTMENT, SUBJECT_EMPLOYEE, SUBJECT_ROLE,
                           DocumentAccess)
from .model import Document

#  Vai trò trong sổ — khớp `tab_document_book_member.role`.
ROLE_BOOK_MANAGER = 1
ROLE_BOOK_VIEWER = 2

#  Hành động → cột trên bảng chia sẻ.
ACTION_COLUMN = {
    "read": DocumentAccess.can_read,
    "write": DocumentAccess.can_write,
    "delete": DocumentAccess.can_delete,
}


def subject_pairs(profile: dict) -> list[tuple[int, int]]:
    """Người đang đăng nhập ứng với những (loại đối tượng, id) nào.

    Một người khớp nhiều dòng cùng lúc: bản thân họ, phòng của họ, pháp nhân của
    họ, và từng vai trò họ mang.
    """
    pairs: list[tuple[int, int]] = []
    if profile.get("employee_id"):
        pairs.append((SUBJECT_EMPLOYEE, profile["employee_id"]))
    if profile.get("dept_id"):
        pairs.append((SUBJECT_DEPARTMENT, profile["dept_id"]))
    if profile.get("company_id"):
        pairs.append((SUBJECT_COMPANY, profile["company_id"]))
    for grant in profile.get("grants", []):
        if grant.get("role_id"):
            pairs.append((SUBJECT_ROLE, grant["role_id"]))
    return pairs


def _live(today: date):
    """Dòng còn hiệu lực: chưa thu hồi và đang trong hạn."""
    return and_(
        DocumentAccess.revoked_at.is_(None),
        or_(DocumentAccess.valid_from.is_(None), DocumentAccess.valid_from <= today),
        or_(DocumentAccess.valid_to.is_(None), DocumentAccess.valid_to >= today),
    )


def _subject_match(profile: dict):
    pairs = subject_pairs(profile)
    if not pairs:
        return None
    return or_(*[
        and_(DocumentAccess.subject_kind == kind, DocumentAccess.subject_id == sid)
        for kind, sid in pairs
    ])


def _document_ids(profile: dict, action: str, effect: int):
    """Truy vấn con: id các văn bản mà người này được (hoặc bị) đích danh."""
    match = _subject_match(profile)
    if match is None:
        return None
    column = ACTION_COLUMN[action]
    return (select(DocumentAccess.document_id)
            .where(and_(DocumentAccess.effect == effect, column.is_(True),
                        match, _live(date.today()))))


def _book_ids(profile: dict, action: str):
    """Sổ mà người này là thành viên. `None` = không phải thành viên sổ nào.

    Quản lý sổ (`role = 1`) xem và sửa được văn bản trong sổ; người xem
    (`role = 2`) chỉ xem. **Xóa thì không** — xóa văn bản là việc của người tạo
    ra nó hoặc của người được chia đích danh, giữ sổ không có nghĩa là được dọn
    sổ.
    """
    from app.modules.doc_catalog.book_model import DocumentBookMember

    employee_id = profile.get("employee_id") or 0
    if not employee_id or action == "delete":
        return None

    roles = [ROLE_BOOK_MANAGER] if action == "write" else [ROLE_BOOK_MANAGER, ROLE_BOOK_VIEWER]
    return (select(DocumentBookMember.book_id)
            .where(and_(DocumentBookMember.employee_id == employee_id,
                        DocumentBookMember.role.in_(roles))))


def visible_condition(user, profile: dict, action: str = "read"):
    """Điều kiện lọc danh sách văn bản cho người đang đăng nhập.

    Trả `None` nghĩa là **không lọc gì** — chỉ xảy ra khi vai trò cho thấy tất cả
    và không có dòng cấm nào áp lên người này.
    """
    scope = scope_condition(Document, "document", user, profile, action)
    allow = _document_ids(profile, action, EFFECT_ALLOW)
    deny = _document_ids(profile, action, EFFECT_DENY)
    books = _book_ids(profile, action)

    #  Hai nguồn CỘNG THÊM vào phạm vi vai trò: chia đích danh và thành viên sổ.
    extra = []
    if allow is not None:
        extra.append(Document.id.in_(allow))
    if books is not None:
        extra.append(and_(Document.book_id.isnot(None), Document.book_id.in_(books)))

    if extra:
        #  `scope is None` = vai trò đã thấy tất cả, không cần cộng thêm gì.
        base = None if scope is None else or_(scope, *extra)
    else:
        base = scope

    if deny is None:
        return base
    not_denied = ~Document.id.in_(deny)
    return not_denied if base is None else and_(base, not_denied)


def dang_duyet_van_ban_nay(db: Session, document_id: int, employee_id: int | None) -> bool:
    """Người này có chân trong một phiên duyệt của văn bản này không.

    Tính cả việc ĐÃ xử lý xong: người vừa ký phải mở lại được thứ mình đã ký,
    nếu không thì chữ ký của họ là chữ ký vào một tờ giấy họ không còn xem được.
    """
    if not employee_id:
        return False

    from app.modules.approval.instance_model import ApprovalInstance, ApprovalTask

    return (
        db.query(ApprovalTask.id)
        .join(ApprovalInstance, ApprovalInstance.id == ApprovalTask.instance_id)
        .filter(ApprovalInstance.entity == "document",
                ApprovalInstance.entity_id == document_id,
                ApprovalTask.assignee_employee_id == employee_id)
        .first()
        is not None
    )


def co_ban_clone_xem_duoc(db: Session, source_document_id: int, user,
                          profile: dict) -> bool:
    """Người dùng có đọc được ít nhất một bản clone của văn bản gốc hay không.

    Pháp nhân nhận phải mở lại được bản gốc để đặt hai bản cạnh nhau, chỉnh bản
    của mình rồi mới ban hành. Quyền này chỉ mở theo liên kết clone đã tồn tại,
    không cộng bản gốc vào danh sách chung của pháp nhân nhận.

    Dùng chính ``visible_condition`` của bản clone để giữ nguyên mọi luật phạm
    vi, chia sẻ, quyền theo sổ và dòng cấm. Không suy rộng thành "cùng pháp nhân
    là được xem", vì người có phạm vi phòng ban hẹp không mặc nhiên được đọc
    mọi bản clone của công ty.
    """
    visible = visible_condition(user, profile, "read")
    query = db.query(Document.id).filter(
        Document.source_document_id == source_document_id,
    )
    if visible is not None:
        query = query.filter(visible)
    return query.first() is not None


def can(db: Session, doc: Document, user, profile: dict, action: str = "read") -> bool:
    """Người này có được `action` trên ĐÚNG văn bản này không."""
    #  ĐỌC ĐƯỢC THỨ MÌNH PHẢI KÝ. Người duyệt trong luồng thường không có vai
    #  trò nào trên phân hệ Văn bản — bộ máy duyệt chỉ hỏi "anh có việc ở phiếu
    #  này không", không hỏi phân quyền. Thiếu ngoại lệ này thì họ bấm từ «Việc
    #  của tôi» sang văn bản là gặp 404 và phải ký mù, chỉ nhìn được mỗi cái
    #  tiêu đề trên dòng việc.
    #
    #  CHỈ mở quyền ĐỌC. Sửa, xóa, ban hành vẫn đi theo phân quyền như cũ — việc
    #  của người duyệt là xem xét rồi ký, không phải sửa bài người khác.
    if action == "read" and dang_duyet_van_ban_nay(
            db, doc.id, getattr(user, "employee_id", None)):
        return True

    match = _subject_match(profile)
    if match is not None:
        column = ACTION_COLUMN[action]
        rows = (db.query(DocumentAccess.effect)
                .filter(DocumentAccess.document_id == doc.id, column.is_(True),
                        match, _live(date.today())).all())
        effects = {row[0] for row in rows}
        #  Cấm thắng cho phép, và thắng luôn cả phạm vi vai trò.
        if EFFECT_DENY in effects:
            return False
        if EFFECT_ALLOW in effects:
            return True

    #  Thành viên sổ chứa văn bản này.
    books = _book_ids(profile, action)
    if books is not None and doc.book_id:
        if db.query(Document.id).filter(Document.id == doc.id,
                                        Document.book_id.in_(books)).first():
            return True

    #  Bản clone luôn dẫn ngược về bản gốc để pháp nhân nhận đối chiếu trước
    #  khi chỉnh và ban hành. Nếu người này đọc được ít nhất một bản clone của
    #  gốc thì mở thêm quyền ĐỌC gốc, nhưng tuyệt đối không kéo theo sửa / xóa.
    #  Dòng CẤM đích danh trên bản gốc đã được xét ở trên nên vẫn thắng.
    if action == "read" and co_ban_clone_xem_duoc(db, doc.id, user, profile):
        return True

    scope = scope_condition(Document, "document", user, profile, action)
    if scope is None:
        return True
    #  Hỏi lại cơ sở dữ liệu thay vì diễn giải điều kiện bằng Python: điều kiện
    #  phạm vi có cả truy vấn con, dựng lại bằng tay là hai đường kiểm khác nhau
    #  rồi lệch nhau lúc nào không biết.
    return db.query(Document.id).filter(Document.id == doc.id, scope).first() is not None


def ensure_can(db: Session, doc: Document, user, profile: dict, action: str = "read"):
    """Như `can()` nhưng ném lỗi. **Không được đọc → 404, không phải 403.**

    Cố ý: 403 là đã xác nhận "có văn bản này, anh không được xem" — chỉ riêng
    việc đó đã lộ thông tin (K03). Không được đọc thì với người đó văn bản không
    tồn tại. Còn sửa / xóa thì 403, vì lúc đó họ đã đọc được rồi.
    """
    if can(db, doc, user, profile, action):
        return
    if action == "read":
        raise HTTPException(404, "Không tìm thấy văn bản")
    raise HTTPException(403, "Bạn không có quyền thao tác trên văn bản này")


# ── Chia sẻ và thu hồi ───────────────────────────────────────────────────────
def list_access(db: Session, doc: Document, include_revoked: bool = True) -> list[DocumentAccess]:
    q = db.query(DocumentAccess).filter(DocumentAccess.document_id == doc.id)
    if not include_revoked:
        q = q.filter(DocumentAccess.revoked_at.is_(None))
    #  Dòng còn sống lên trước, trong đó dòng CẤM lên đầu — người đọc bảng cần
    #  thấy ngay ai đang bị chặn.
    return q.order_by(DocumentAccess.revoked_at.isnot(None),
                      DocumentAccess.effect.desc(), DocumentAccess.id.desc()).all()


def grant(db: Session, doc: Document, data, actor: int) -> DocumentAccess:
    """Chia quyền cho một đối tượng. Đã có dòng còn sống thì SỬA dòng đó.

    Sửa chứ không thêm: hai dòng cho phép cùng một người, thu hồi một dòng mà
    người đó vẫn đọc được là chuyện không ai giải thích nổi.
    """
    if data.valid_from and data.valid_to and data.valid_from > data.valid_to:
        raise HTTPException(400, "Ngày hết hạn phải sau ngày bắt đầu")

    existing = (db.query(DocumentAccess)
                .filter(DocumentAccess.document_id == doc.id,
                        DocumentAccess.subject_kind == data.subject_kind,
                        DocumentAccess.subject_id == data.subject_id,
                        DocumentAccess.effect == data.effect,
                        DocumentAccess.revoked_at.is_(None))
                .first())

    values = data.model_dump()
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
        existing.updated_by = actor
        row = existing
    else:
        row = DocumentAccess(document_id=doc.id, **values,
                             created_by=actor, updated_by=actor)
        db.add(row)

    db.commit()
    db.refresh(row)
    return row


def revoke(db: Session, doc: Document, access_id: int, reason: str, actor: int) -> DocumentAccess:
    """Thu hồi = ĐÁNH DẤU. Dòng ở lại bảng (G19, G20).

    Xóa dòng đi thì mất luôn câu trả lời cho "hồi tháng 7 ai đọc được văn bản
    này" — mà đó chính là câu người ta hỏi khi có chuyện.
    """
    row = db.get(DocumentAccess, access_id)
    if not row or row.document_id != doc.id:
        raise HTTPException(404, "Không tìm thấy dòng chia sẻ")
    if row.revoked_at is not None:
        raise HTTPException(400, "Dòng này đã thu hồi rồi")

    row.revoked_at = datetime.now()
    row.revoked_by = actor
    row.revoke_reason = reason
    row.updated_by = actor
    db.commit()
    db.refresh(row)
    return row
