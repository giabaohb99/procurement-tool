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
from . import revoke_access
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

    ⚠️ **KHÔNG kéo bản gốc theo bản clone** (bỏ ngày 22/08/2026).

    Trước đây quyền ĐỌC có cộng thêm một vế: thấy bản clone thì thấy luôn bản gốc
    của nó, với lý do "giao diện cần dòng gốc để gom bản clone vào nhánh bung".
    Nhưng ghép với `an_ban_rieng_co_goc_xem_duoc` — hàm giấu bản riêng khi bản
    gốc CŨNG xem được — thì kết quả lộn ngược đúng ở pháp nhân con:

      văn thư SAM mở danh sách, thấy dòng **02/2026/VBĐ-DEGO của DEGO** kèm mũi
      tên bung, còn văn bản của chính họ (**01/2026/TB-SAM**) bị giấu vào nhánh.

    Tức là người ở pháp nhân con nhận về một dòng của công ty khác như thể đó là
    văn bản của mình, và phải bung ra mới tìm thấy bản của mình. Vế kéo-theo này
    chỉ phục vụ đúng nhóm người đó, mà với họ nó lại sai — người ở pháp nhân mẹ
    vốn đã thấy bản gốc bằng phạm vi của chính mình.

    Bỏ vế đó thì mỗi bên thấy đúng phần của mình: mẹ vẫn có cây bung như cũ, con
    thấy thẳng bản riêng của con. Muốn đối chiếu thì trang chi tiết đã có sẵn nút
    **«Xem bản gốc»** (`document-needs-review-banner.tsx`).
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
        direct = base
        not_denied = None
    else:
        not_denied = ~Document.id.in_(deny)
        direct = not_denied if base is None else and_(base, not_denied)

    #  VĂN BẢN ĐÃ BÃI BỎ chỉ còn người tạo / người chịu trách nhiệm / người bãi
    #  bỏ / người giữ sổ nhìn thấy (xem `revoke_access.py`). Nhân với điều kiện
    #  chứ không thay thế: bãi bỏ **thu hẹp** tầm nhìn, không mở thêm cho ai.
    han_che = revoke_access.dieu_kien_loc(user, profile)
    if han_che is not None:
        direct = han_che if direct is None else and_(direct, han_che)

    #  `None` = đã thấy tất cả, không cần cộng nguồn quyền nào. Các hành động
    #  sửa / xóa tuyệt đối không được kéo theo từ bản clone sang bản gốc.
    return direct


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
    của mình rồi mới ban hành. Quyền này chỉ mở theo liên kết clone đã tồn tại;
    `visible_condition()` cũng đưa gốc vào danh sách để giao diện gom clone vào
    đúng nhánh cha–con.

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
    """Người này có được `action` trên ĐÚNG văn bản này không.

    ⚠️ **KHÔNG ĐỌC ĐƯỢC THÌ KHÔNG LÀM GÌ ĐƯỢC** (thêm 22/08/2026).

    Quyền đọc tới từ nhiều nguồn (phạm vi vai trò, chia đích danh, thành viên sổ,
    phạm vi áp dụng, đang duyệt), và dòng CẤM đích danh tick từng hành động
    riêng. Nên có tổ hợp đọc bị cấm mà ghi vẫn lọt: bắt được ở văn bản 352 —
    nhân viên thu mua bị cấm ĐỌC bằng một dòng chia sẻ, nhưng vẫn `write = True`
    nhờ là **người quản lý quyển sổ** chứa văn bản đó. Kết quả là họ sửa được số
    hiệu của một văn bản mà mở ra là 404.

    Sửa thứ mình không mở được là vô nghĩa ở mọi tình huống, nên chặn một lần ở
    đây thay vì vá từng nguồn quyền.
    """
    if action != "read" and not can(db, doc, user, profile, "read"):
        return False

    #  ĐÃ BÃI BỎ thì chặn TRƯỚC mọi khe cấp quyền bên dưới — người duyệt cũ,
    #  dòng chia đích danh, phạm vi áp dụng, thành viên sổ, bản clone: khe nào
    #  cũng phải đóng. Đặt sau chúng thì mỗi khe là một đường vòng.
    if not revoke_access.con_xem_duoc(doc, user, profile):
        return False

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

    #  Người nằm trong PHẠM VI ÁP DỤNG phải mở được chính văn bản đã ban hành
    #  từ chuông/email, kể cả vai trò của họ không có phạm vi đọc phân hệ Văn
    #  bản. Khe này CHỈ cấp đọc; dòng cấm đích danh ở trên vẫn thắng tuyệt đối.
    if action == "read" and getattr(user, "employee_id", None):
        from app.modules.employee.model import Employee
        from . import scope_service

        employee = db.get(Employee, user.employee_id)
        if employee and employee.is_active and scope_service.applies_to(db, doc.id, employee):
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


def chan_tu_cam_chinh_minh(db: Session, data, actor: int) -> None:
    """KHÔNG ai được tự đưa mình vào dòng CẤM — kể cả bằng cách gọi thẳng API.

    Nhìn bảng luật ở đầu tệp: *cấm đích danh* thắng tất cả, **kể cả người tạo,
    kể cả admin**. Nên tự cấm mình là tự khóa mình ra ngoài một văn bản mà chỉ
    mình có quyền sửa — và vì không mở được nữa nên cũng không còn đường vào để
    gỡ dòng cấm đó. Chỉ người khác cứu được.

    Lỗi người dùng đã dính thật (24/08/2026): tự chặn xong, danh sách hiện «Tổng
    0 văn bản» kèm ba toast đỏ liên tiếp. Giao diện nay đã bỏ tên mình khỏi ô
    chọn, nhưng ẩn nút không phải là chốt chặn — gọi thẳng API vẫn tự chặn được
    (dựng lại được trước khi có hàm này).

    Chặn cả PHÒNG BAN và PHÁP NHÂN của mình: chặn phòng mình thì mình nằm trong
    phòng đó, kết cục y hệt. **Vai trò thì không chặn** — người ta có thể giữ
    nhiều vai trò và bỏ một vai trò không đồng nghĩa mất quyền xem.
    """
    if data.effect != EFFECT_DENY:
        return

    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    emp_id = db.query(User.employee_id).filter(User.id == actor).scalar()
    if not emp_id:
        return
    emp = db.get(Employee, emp_id)
    if emp is None:
        return

    cua_minh = {
        SUBJECT_EMPLOYEE: emp.id,
        SUBJECT_DEPARTMENT: emp.department_id or 0,
        SUBJECT_COMPANY: emp.company_id or 0,
    }
    if cua_minh.get(data.subject_kind) and cua_minh[data.subject_kind] == data.subject_id:
        ten = {SUBJECT_EMPLOYEE: "chính mình",
               SUBJECT_DEPARTMENT: "phòng ban của mình",
               SUBJECT_COMPANY: "pháp nhân của mình"}[data.subject_kind]
        raise HTTPException(
            400, f"Không chặn được {ten}: dòng cấm thắng cả quyền của người tạo, "
                 "nên bạn sẽ không mở lại được văn bản này và cũng không còn đường "
                 "vào để gỡ. Nhờ người khác chặn hộ nếu thật sự cần.")


def grant(db: Session, doc: Document, data, actor: int) -> DocumentAccess:
    """Chia quyền cho một đối tượng. Đã có dòng còn sống thì SỬA dòng đó.

    Sửa chứ không thêm: hai dòng cho phép cùng một người, thu hồi một dòng mà
    người đó vẫn đọc được là chuyện không ai giải thích nổi.
    """
    if data.valid_from and data.valid_to and data.valid_from > data.valid_to:
        raise HTTPException(400, "Ngày hết hạn phải sau ngày bắt đầu")

    chan_tu_cam_chinh_minh(db, data, actor)

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
