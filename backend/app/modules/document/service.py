"""Nghiệp vụ VĂN BẢN: tạo, sửa, xóa, gửi duyệt, ban hành.

Duyệt ở bản này là **luồng một bước viết tay tạm thời** — một nút gửi duyệt, một
nút duyệt. P3 sẽ thay bằng bộ máy duyệt dùng chung (nhiều bước, rẽ nhánh, người
thay thế). Làm tạm để phase 2 cho người thật bấm thử được ngay, và cố ý gói gọn
trong ba hàm `submit` / `approve` / `reject` dưới đây để lúc thay không phải lần
mò khắp nơi.

Phần dựng bản ghi trả về nằm ở `serializer.py`.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink
from app.modules.doc_catalog.model import DocType

from . import numbering
from .model import (ALIVE_STATUSES, APPLY_MODE_LABELS, STATUS_APPROVED, STATUS_DRAFT,
                    STATUS_EFFECTIVE, STATUS_REVOKED, STATUS_SUBMITTED,
                    Document)
from .query import documents_query
from .schema import DocumentCreate, DocumentUpdate
from .version_model import (VERSION_APPROVED, VERSION_DRAFT, VERSION_SUBMITTED,
                            VERSION_SUPERSEDED, DocumentVersion)

#  Cấp số lúc nào — `doc_type.number_when`.
NUMBER_ON_DRAFT = 1
NUMBER_ON_APPROVE = 2

#  Đính kèm treo vào PHIÊN BẢN chứ không vào văn bản: bản đã duyệt phải giữ đúng
#  bộ tệp lúc duyệt, mở bản mới thì tệp được chép sang bản mới (xem
#  `version_service.open_new_version`).
ATTACH_ENTITY = "document_version"


def doc_type_or_400(db: Session, doc_type_id: int) -> DocType:
    doc_type = db.get(DocType, doc_type_id)
    if not doc_type:
        raise HTTPException(400, "Loại văn bản không tồn tại")
    if not doc_type.is_active:
        raise HTTPException(400, f"Loại văn bản {doc_type.name} đã ngừng dùng")
    return doc_type


def get_or_404(db: Session, document_id: int) -> Document:
    doc = documents_query(db).filter(Document.id == document_id).one_or_none()
    if not doc:
        raise HTTPException(404, "Không tìm thấy văn bản")
    return doc


def open_version(db: Session, doc: Document) -> DocumentVersion | None:
    """Phiên bản đang mở (nháp hoặc đang duyệt). Nhiều nhất một — ép bởi `open_slot`."""
    return (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == doc.id,
                DocumentVersion.status.in_((VERSION_DRAFT, VERSION_SUBMITTED)))
        .order_by(DocumentVersion.major.desc(), DocumentVersion.minor.desc())
        .first()
    )


def issue_year(doc: Document) -> int:
    """Năm dùng để cấp số: theo NGÀY HIỆU LỰC nếu đã khai, không thì năm nay."""
    return (doc.effective_date or date.today()).year


def assign_book_number(db: Session, doc: Document) -> None:
    """Vào sổ: cấp số thứ tự từ bộ đếm RIÊNG của sổ. Gọi trong transaction đang ghi.

    Một văn bản vào sổ mang HAI số, và hai số đó khác nhau về bản chất:
      * `issue_number` / `doc_code` — số hiệu ĐI RA NGOÀI, in trên văn bản;
      * `book_seq_no` — số thứ tự TRONG SỔ, để văn thư dò lại theo quyển.

    Gọi lại trên văn bản đã có số vào sổ thì không làm gì — số đã ghi vào sổ.
    """
    from app.modules.doc_catalog.book_model import DocumentBook
    from app.modules.doc_catalog.number_service import next_book_number

    if not doc.book_id or doc.book_seq_no:
        return
    book = db.get(DocumentBook, doc.book_id)
    if not book:
        return

    year = issue_year(doc)
    doc.book_seq_no = next_book_number(db, book, year)
    doc.book_year = year


# ── Tạo / sửa / xóa ──────────────────────────────────────────────────────────
def create_document(db: Session, data: DocumentCreate, actor: int) -> Document:
    """Tạo văn bản + phiên bản 1.0 trong CÙNG một transaction.

    Cùng transaction là bắt buộc chứ không phải cho gọn: nếu cấp số xong mà ghi
    bản ghi hỏng thì số đó biến mất khỏi sổ, không ai giải thích được lỗ hổng.
    """
    doc_type = doc_type_or_400(db, data.doc_type_id)

    payload = data.model_dump(exclude={"content_html", "secrecy_level"})
    doc = Document(
        **payload,
        #  Bỏ trống thì theo mặc định của loại; loại đánh dấu "cả loại là loại
        #  bảo mật" thì kéo lên ít nhất mức Mật.
        secrecy_level=max(
            data.secrecy_level or doc_type.default_secrecy,
            3 if doc_type.is_confidential_type else 1,
        ),
        status=STATUS_DRAFT,
        created_by=actor, updated_by=actor,
    )
    db.add(doc)
    db.flush()

    if doc_type.number_when == NUMBER_ON_DRAFT:
        numbering.assign(db, doc, doc_type, issue_year(doc))

    version = DocumentVersion(
        document_id=doc.id, major=1, minor=0, status=VERSION_DRAFT,
        content_html=data.content_html or "",
        effective_from=data.effective_date,
        created_by=actor, updated_by=actor,
    )
    db.add(version)
    db.flush()

    doc.current_version_id = version.id
    db.commit()
    db.refresh(doc)
    return doc


def update_document(db: Session, doc: Document, data: DocumentUpdate, actor: int) -> Document:
    """Sửa bộ trường chung. Không đụng nội dung (ở phiên bản) và không đụng số hiệu."""
    values = data.model_dump(exclude_unset=True)
    numbered = bool(doc.doc_code or doc.issue_number)

    #  Đổi loại / pháp nhân sau khi đã cấp số là đổi luôn tiền tố của số đã phát
    #  hành — số trên giấy tờ đã gửi đi thành sai.
    if numbered and values.get("doc_type_id", doc.doc_type_id) != doc.doc_type_id:
        raise HTTPException(400, "Văn bản đã có số hiệu, không đổi được loại")
    if numbered and values.get("company_id", doc.company_id) != doc.company_id:
        raise HTTPException(400, "Văn bản đã có số hiệu, không đổi được pháp nhân ban hành")
    if "doc_type_id" in values and values["doc_type_id"] != doc.doc_type_id:
        doc_type_or_400(db, values["doc_type_id"])

    #  E11 (c) — kiểm LẠI ở đây chứ không chỉ lúc tạo bản trích: người dùng nâng
    #  mức mật sau đó thì bản trích thành ra mật hơn cả bản gốc, tức là phần nội
    #  dung ít hơn lại được canh chặt hơn phần đầy đủ.
    if "secrecy_level" in values:
        from .excerpt_service import ensure_secrecy_within_source, source_link_of

        link = source_link_of(db, doc.id)
        if link:
            source = db.get(Document, link.target_document_id)
            if source:
                ensure_secrecy_within_source(values["secrecy_level"], source.secrecy_level)

    for key, value in values.items():
        setattr(doc, key, value)
    doc.updated_by = actor
    db.commit()
    db.refresh(doc)
    return doc


def update_issue_number(
    db: Session,
    doc: Document,
    issue_number: str,
    actor: int,
) -> tuple[Document, str]:
    """Sửa số hiệu thủ công nhưng không quay lui bộ đếm đã cấp."""
    from app.modules.doc_catalog.numbering_rule_model import DocumentNumberingRule

    if not doc.issue_number:
        raise HTTPException(400, "Văn bản chưa có số hiệu để chỉnh sửa")
    rule = db.get(DocumentNumberingRule, doc.numbering_rule_id) if doc.numbering_rule_id else None
    if not rule or not rule.allow_manual:
        raise HTTPException(400, "Quy tắc đánh số không cho phép sửa số thủ công")

    value = issue_number.strip()
    duplicate = (
        db.query(Document.id)
        .filter(
            Document.id != doc.id,
            Document.company_id == doc.company_id,
            Document.issue_year == doc.issue_year,
            Document.issue_number == value,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(400, "Số hiệu này đã được dùng cho văn bản khác")

    previous = doc.issue_number
    doc.issue_number = value
    doc.updated_by = actor
    db.commit()
    db.refresh(doc)
    return doc, previous


def delete_document(db: Session, doc: Document):
    """Xóa — CHỈ khi còn là nháp chưa cấp số.

    Đã cấp số thì số đó đã nằm trong sổ; xóa bản ghi đi là sổ thủng một lỗ không
    giải thích được. Cách đúng là bãi bỏ, giữ nguyên dòng.
    """
    if doc.status != STATUS_DRAFT:
        raise HTTPException(400, "Chỉ xóa được văn bản đang ở trạng thái nháp")
    if doc.doc_code or doc.issue_number:
        raise HTTPException(400, "Văn bản đã cấp số, không xóa được. Hãy bãi bỏ văn bản.")

    version_ids = [
        row[0] for row in
        db.query(DocumentVersion.id).filter(DocumentVersion.document_id == doc.id).all()
    ]
    if version_ids:
        db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY,
                                  FileLink.entity_id.in_(version_ids)).delete(
                                      synchronize_session=False)
    db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).delete(
        synchronize_session=False)
    db.delete(doc)
    db.commit()


# ── Luồng duyệt một bước (TẠM — P3 thay) ─────────────────────────────────────
def submit(db: Session, doc: Document, actor: int) -> Document:
    version = open_version(db, doc)
    if not version:
        raise HTTPException(400, "Văn bản không có bản nháp nào để gửi duyệt")
    if version.status == VERSION_SUBMITTED:
        raise HTTPException(400, "Bản này đang chờ duyệt")
    if not (version.content_html or "").strip():
        raise HTTPException(400, "Nội dung văn bản còn trống, chưa gửi duyệt được")
    #  Từ phiên bản thứ hai trở đi phải nói rõ sửa gì (C05, C13).
    if (version.major, version.minor) != (1, 0) and not version.change_summary.strip():
        raise HTTPException(400, "Phiên bản từ bản thứ hai phải khai tóm tắt nội dung sửa")
    #  E04 — thiếu quan hệ bắt buộc thì không cho gửi. Chặn ở ĐÂY chứ không phải
    #  ẩn nút trên giao diện: Hướng dẫn công việc không trỏ vào Quy trình nào thì
    #  ban hành ra cũng không ai biết nó hướng dẫn cho cái gì.
    from .link_service import ensure_required_links
    ensure_required_links(db, doc)

    version.status, version.updated_by = VERSION_SUBMITTED, actor
    #  CHỈ bản đầu tiên mới kéo cả văn bản sang "đang duyệt". Từ bản thứ hai trở
    #  đi, văn bản vẫn đang có hiệu lực bằng bản cũ trong suốt lúc bản mới chờ
    #  duyệt — chỗ dễ sai số 7 của `van-thu/02`.
    if version.prev_version_id is None:
        doc.status = STATUS_SUBMITTED
    doc.updated_by = actor
    db.commit()
    db.refresh(doc)
    return doc


def approve(db: Session, doc: Document, actor: int,
            apply_mode: int | None = None) -> Document:
    """Duyệt bản đang chờ: khóa phiên bản, cấp số nếu tới lượt, chuyển hiệu lực.

    ⚠️ **Không kéo `tab_document.status` về nháp.** Quy chế lên bản 2.0 thì văn
    bản VẪN đang có hiệu lực trong suốt lúc bản mới chờ duyệt — xem chỗ dễ sai
    số 7 của `van-thu/02`.
    """
    from .version_service import lock_version

    version = open_version(db, doc)
    if not version or version.status != VERSION_SUBMITTED:
        raise HTTPException(400, "Không có bản nào đang chờ duyệt")

    #  F13 — cơ chế áp dụng chốt LÚC BAN HÀNH, không phải lúc soạn: tới lúc này
    #  người ban hành mới biết nội dung cuối cùng có dùng chung được cho mọi
    #  pháp nhân hay không.
    if apply_mode is not None:
        if apply_mode not in APPLY_MODE_LABELS:
            raise HTTPException(400, "Cơ chế áp dụng không hợp lệ")
        doc.apply_mode = apply_mode

    from .excerpt_service import is_excerpt
    from .parent_change_service import apply_new_version

    doc_type = doc_type_or_400(db, doc.doc_type_id)
    #  Bản trích KHÔNG cấp số hiệu riêng — nó gọi theo số của bản gốc (C19).
    #  Cấp số cho nó là đẻ ra một số hiệu thứ hai cho cùng một nội dung.
    if doc_type.number_when == NUMBER_ON_APPROVE and not is_excerpt(db, doc.id):
        numbering.assign(db, doc, doc_type, issue_year(doc))
    assign_book_number(db, doc)

    lock_version(version, actor)

    previous = db.get(DocumentVersion, version.prev_version_id) if version.prev_version_id else None
    effective = version.effective_from or doc.effective_date or date.today()

    if effective <= date.today():
        switch_current(db, doc, version, previous)
        #  E07 — cha lên phiên bản mới thì MỌI văn bản con bị xử lý theo cột
        #  `on_parent_new_version` của quy tắc quan hệ. Bản trích là trường hợp
        #  đặc biệt: cột đó bị khóa cứng ở mức "đánh dấu cần rà lại" (E11 a).
        if previous is not None:
            apply_new_version(
                db, doc,
                f"Văn bản cha đã lên phiên bản {version.version_no} ngày "
                f"{date.today():%d/%m/%Y}. Rà lại xem còn đúng không.",
            )
    elif previous is None:
        #  Bản đầu tiên duyệt trước ngày hiệu lực: đã duyệt nhưng chưa áp dụng.
        #  Bản thứ hai trở đi thì KHÔNG đụng gì — bản cũ còn đang chạy.
        doc.status = STATUS_APPROVED
        doc.effective_date = effective

    doc.updated_by = actor
    db.commit()
    db.refresh(doc)
    return doc


def reject(db: Session, doc: Document, reason: str, actor: int) -> Document:
    """Trả lại bản nháp kèm lý do. Bản nháp giữ nguyên nội dung để sửa tiếp."""
    version = open_version(db, doc)
    if not version or version.status != VERSION_SUBMITTED:
        raise HTTPException(400, "Không có bản nào đang chờ duyệt")

    #  F13 — cơ chế áp dụng chốt LÚC BAN HÀNH, không phải lúc soạn: tới lúc này
    #  người ban hành mới biết nội dung cuối cùng có dùng chung được cho mọi
    #  pháp nhân hay không.
    if apply_mode is not None:
        if apply_mode not in APPLY_MODE_LABELS:
            raise HTTPException(400, "Cơ chế áp dụng không hợp lệ")
        doc.apply_mode = apply_mode

    version.status, version.updated_by = VERSION_DRAFT, actor
    version.change_reason = (
        f"{version.change_reason}\n[Trả lại] {reason}".strip()
        if version.change_reason else f"[Trả lại] {reason}"
    )
    #  Bản đầu tiên bị trả về nháp; bản thứ hai trở đi thì VĂN BẢN giữ nguyên
    #  trạng thái vì bản trước đó vẫn đang có hiệu lực.
    if version.prev_version_id is None:
        doc.status = STATUS_DRAFT
    doc.updated_by = actor
    db.commit()
    db.refresh(doc)
    return doc


def revoke(db: Session, doc: Document, reason: str, actor: int) -> Document:
    """BÃI BỎ văn bản đã ban hành — cách đúng để gỡ bỏ thay cho xóa.

    Số hiệu đã cấp thì đã nằm trong sổ, xóa bản ghi đi là sổ thủng một lỗ không
    giải thích được (xem `delete_document`). Bãi bỏ giữ nguyên dòng và số, chỉ
    đổi trạng thái + đóng ngày hết hiệu lực, nên tra sổ vẫn ra "số này từng cấp
    cho văn bản gì, bỏ ngày nào".

    LÝ DO ghi vào nhật ký thao tác (`audit`) ở tầng controller, không thêm cột
    riêng: sổ nhật ký đã hiện ngay trên trang chi tiết, mà thêm cột là phải
    ALTER một bảng đang chạy.
    """
    if doc.status == STATUS_REVOKED:
        raise HTTPException(400, "Văn bản đã bãi bỏ rồi")
    #  Chưa ban hành thì không có gì để bãi bỏ: nháp thì xóa, đang duyệt thì
    #  trả lại bản nháp.
    if doc.status not in ALIVE_STATUSES:
        raise HTTPException(400, "Chỉ bãi bỏ được văn bản đã ban hành")

    from .parent_change_service import apply_obsolete

    doc.status = STATUS_REVOKED
    #  Ngày bãi bỏ chính là ngày hết hiệu lực — để bộ lọc "còn hiệu lực đến
    #  ngày…" khỏi phải biết thêm một cột nữa.
    doc.expire_date = date.today()
    #  E08 — văn bản con xử lý theo cột `on_parent_obsolete` của quy tắc: không
    #  làm gì · đánh dấu cần rà lại · hết hiệu lực theo cha. Bản trích bị khóa ở
    #  mức thứ ba (E11 b) — gốc bãi bỏ mà bản trích còn sống là phát tán nội
    #  dung đã bỏ.
    apply_obsolete(db, doc)
    doc.updated_by = actor
    db.commit()
    db.refresh(doc)
    return doc


def switch_current(db: Session, doc: Document, version: DocumentVersion,
                   previous: DocumentVersion | None):
    """Chuyển bản đang dùng sang `version`. Bản trước chuyển sang *đã thay thế*."""
    if previous is not None and previous.status != VERSION_SUPERSEDED:
        previous.status = VERSION_SUPERSEDED
    doc.current_version_id = version.id
    doc.status = STATUS_EFFECTIVE
    doc.effective_date = version.effective_from or doc.effective_date or date.today()


def activate_due_versions(db: Session, document_id: int | None = None) -> int:
    """Chuyển phiên bản đã duyệt sang hiệu lực khi tới ngày. Trả về số bản đã đổi.

    Vì sao không phải tác vụ chạy nền: hệ chưa có bộ chạy định kỳ, mà việc cần
    làm chỉ là một câu lọc theo ngày. Gọi ở đường đọc chi tiết văn bản (rẻ) và
    mở thêm một endpoint bảo trì để chạy cho toàn bảng. Đổi trong **một
    transaction** — không có khoảng trống nào mà văn bản không có bản hiệu lực
    (C16, C17).
    """
    today = date.today()
    q = (
        db.query(Document, DocumentVersion)
        .join(DocumentVersion, DocumentVersion.document_id == Document.id)
        .filter(DocumentVersion.status == VERSION_APPROVED,
                DocumentVersion.effective_from.isnot(None),
                DocumentVersion.effective_from <= today)
    )
    if document_id:
        q = q.filter(Document.id == document_id)

    changed = 0
    for doc, version in q.all():
        #  Văn bản đã trỏ đúng bản này rồi thì chỉ còn thiếu việc đổi trạng thái —
        #  trường hợp bản ĐẦU TIÊN duyệt trước ngày hiệu lực (`current_version_id`
        #  gán từ lúc tạo, nhưng văn bản mới chỉ ở "đã duyệt").
        if doc.current_version_id == version.id:
            if doc.status == STATUS_APPROVED:
                switch_current(db, doc, version, None)
                changed += 1
            continue
        current = db.get(DocumentVersion, doc.current_version_id) if doc.current_version_id else None
        #  Bản đang dùng đã mới hơn thì bỏ qua — tới ngày mà đã có bản 3.0 chạy
        #  rồi thì đừng kéo ngược về 2.0.
        if current and (current.major, current.minor) > (version.major, version.minor):
            continue
        switch_current(db, doc, version, current)
        changed += 1

    if changed:
        db.commit()
    return changed


# ── Gợi ý văn bản đã có (B05) ────────────────────────────────────────────────
def suggestions(db: Session, doc_type_id: int, department_id: int | None,
                company_id: int | None, exclude_id: int | None = None) -> list[dict]:
    """Văn bản CÙNG LOẠI, CÙNG PHÒNG đang còn hiệu lực.

    Đây là thứ rẻ nhất còn lại chống việc đẻ trùng quy trình sau khi bước xin
    phép bị cắt (quyết định 7): người soạn nhìn thấy ngay là đã có hay chưa,
    trước khi ngồi gõ một bản thứ hai cho cùng một việc.
    """
    q = documents_query(db).filter(Document.doc_type_id == doc_type_id,
                                   Document.status.in_(ALIVE_STATUSES))
    if department_id:
        q = q.filter(Document.department_id == department_id)
    if company_id:
        q = q.filter(Document.company_id == company_id)
    if exclude_id:
        q = q.filter(Document.id != exclude_id)

    rows = q.order_by(Document.effective_date.desc()).limit(10).all()
    return [{
        "id": row.id,
        "display_code": row.doc_code or row.issue_number,
        "title": row.title,
        "effective_date": row.effective_date.isoformat() if row.effective_date else "",
    } for row in rows]
