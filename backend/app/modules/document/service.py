"""Nghiệp vụ VĂN BẢN: tạo, sửa, xóa, gửi duyệt, ban hành.

Duyệt ở bản này là **luồng một bước viết tay tạm thời** — một nút gửi duyệt, một
nút duyệt. P3 sẽ thay bằng bộ máy duyệt dùng chung (nhiều bước, rẽ nhánh, người
thay thế). Làm tạm để phase 2 cho người thật bấm thử được ngay, và cố ý gói gọn
trong ba hàm `submit` / `approve` / `reject` dưới đây để lúc thay không phải lần
mò khắp nơi.

Phần dựng bản ghi trả về nằm ở `serializer.py`.
"""
import logging
from datetime import date

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink
from app.modules.doc_catalog.model import DocType

from . import type_metadata
from app.modules.doc_catalog.security_level_model import (KIND_CONFIDENTIAL,
                                                          KIND_URGENCY)
from app.modules.doc_catalog.security_level_service import (ensure_valid,
                                                            value_of_code)

from . import numbering
from .model import (ALIVE_STATUSES, APPLY_MODE_LABELS, EDITABLE_STATUSES,
                    STATUS_APPROVED, STATUS_DRAFT, STATUS_EFFECTIVE,
                    STATUS_PENDING_ISSUE, STATUS_REJECTED, STATUS_RETURNED,
                    STATUS_REVOKED, STATUS_SUBMITTED, Document)
from .content_sanitize import sanitize_document_html
from .query import documents_query
from .schema import DocumentCreate, DocumentUpdate
from .version_model import (OPEN_STATUSES, VERSION_APPROVED, VERSION_DRAFT,
                            VERSION_REJECTED, VERSION_RETURNED,
                            VERSION_SUBMITTED, VERSION_SUPERSEDED,
                            DocumentVersion)

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
    """Phiên bản đang mở (nháp · đang duyệt · bị trả về). Nhiều nhất một — ép bởi `open_slot`.

    Dùng thẳng `OPEN_STATUSES` chứ không liệt kê lại: danh sách này còn là biểu
    thức của cột sinh `open_slot`, hai chỗ lệch nhau là câu truy vấn bỏ sót đúng
    cái phiên bản mà UNIQUE vẫn đang giữ chỗ.
    """
    return (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == doc.id,
                DocumentVersion.status.in_(OPEN_STATUSES))
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
    #  Dải hợp lệ là DANH MỤC, không phải một hằng số trong mã — xem
    #  `doc_catalog/security_level_service.ensure_valid`.
    ensure_valid(db, KIND_CONFIDENTIAL, data.secrecy_level)
    ensure_valid(db, KIND_URGENCY, data.urgency)

    #  ⚠️ `metadata` PHẢI tách khỏi payload. Thuộc tính Python của cột đó tên là
    #  `meta` (SQLAlchemy giữ riêng tên `metadata` cho `Base.metadata`), nên để
    #  nguyên trong payload là `Document(metadata=...)` nổ ngay.
    payload = data.model_dump(exclude={"content_html", "secrecy_level", "metadata"})
    doc = Document(
        **payload,
        #  Người nghỉ mặc định là NGƯỜI CHỊU TRÁCH NHIỆM của văn bản — với đơn
        #  nghỉ phép hai thứ đó là một. Khai tường minh trong metadata thì thắng.
        meta=type_metadata.sanitize(doc_type.code, data.metadata,
                                    data.owner_employee_id),
        #  Bỏ trống thì theo mặc định của loại; loại đánh dấu "cả loại là loại
        #  bảo mật" thì kéo lên ít nhất mức Mật. Tra mức Mật theo MÃ chứ không
        #  viết số 3 vào mã — xem `value_of_code`.
        secrecy_level=max(
            data.secrecy_level or doc_type.default_secrecy,
            value_of_code(db, "MAT") if doc_type.is_confidential_type else 1,
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
        #  Lọc XSS ngay tại cửa ghi — xem `content_sanitize`.
        content_html=sanitize_document_html(data.content_html),
        effective_from=data.effective_date,
        created_by=actor, updated_by=actor,
    )
    db.add(version)
    db.flush()

    doc.current_version_id = version.id
    db.commit()
    db.refresh(doc)
    return doc


def block_edit_while_approving(doc: Document) -> None:
    """Văn bản ĐANG TRÌNH DUYỆT thì đóng băng cả bộ trường chung (19/08/2026).

    Không chỉ thân văn bản: đổi **mức mật** hay **tiêu đề** dưới tay người duyệt
    cũng là đưa họ ký một thứ khác với thứ họ đọc. Đã dựng lại được — gửi duyệt
    xong `PATCH /documents/{id}` vẫn trả 200 và nâng được mức mật lên "Mật".

    Cùng luật với nội dung, xem `version_service.chan_khi_dang_duyet`: muốn sửa
    thì rút phiếu → văn bản về Nháp.

    Văn bản **ĐÃ TỪ CHỐI** cũng khóa ở đây, vì lý do khác: nó không còn đường đi
    tiếp nào cả. Cho sửa thì người soạn gõ cả buổi rồi mới phát hiện không có nút
    nào gửi lại được — đường đúng là *Sao chép* ra một bản nháp mới.
    Còn **TRẢ VỀ** thì mở, đó chính là chỗ để sửa rồi gửi duyệt lại.
    """
    if doc.status == STATUS_SUBMITTED:
        raise HTTPException(409, "Văn bản đang trình duyệt nên khóa thông tin. "
                                 "Muốn sửa thì rút phiếu duyệt (hoặc chờ người duyệt trả lại).")
    #  ĐÃ KÝ ĐỦ, CHỜ BAN HÀNH — khóa CHẶT như lúc đang duyệt, và vì đúng một lý
    #  do: chữ ký đã đặt lên nội dung này rồi. Mở ra thì người soạn sửa tiêu đề
    #  hay nâng mức mật xong mới bấm Ban hành, và thứ phát hành ra không còn là
    #  thứ người ký đã đọc — đúng cái lỗ mà cả `chan_sua_khi_dang_duyet` sinh ra
    #  để bịt, chỉ dịch sang muộn hơn một nhịp.
    if doc.status == STATUS_PENDING_ISSUE:
        raise HTTPException(409, "Văn bản đã ký đủ và đang chờ ban hành nên khóa "
                                 "thông tin. Muốn sửa thì nhờ người duyệt trả lại.")
    if doc.status == STATUS_REJECTED:
        raise HTTPException(409, "Văn bản đã bị từ chối nên khóa. "
                                 "Muốn làm lại thì bấm «Sao chép» để có bản nháp mới.")


def update_document(db: Session, doc: Document, data: DocumentUpdate, actor: int) -> Document:
    """Sửa bộ trường chung. Không đụng nội dung (ở phiên bản) và không đụng số hiệu."""
    block_edit_while_approving(doc)

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
    ensure_valid(db, KIND_CONFIDENTIAL, values.get("secrecy_level"))
    ensure_valid(db, KIND_URGENCY, values.get("urgency"))

    if "secrecy_level" in values:
        from .excerpt_service import ensure_secrecy_within_source, source_link_of

        link = source_link_of(db, doc.id)
        if link:
            source = db.get(Document, link.target_document_id)
            if source:
                ensure_secrecy_within_source(values["secrecy_level"], source.secrecy_level)

    #  ⚠️ `metadata` KHÔNG đi qua vòng `setattr` bên dưới. Thuộc tính đó trên lớp
    #  khai báo là `Base.metadata` (đối tượng MetaData của SQLAlchemy); gán đè lên
    #  bản ghi thì nó nằm trong `__dict__` của instance và **không bao giờ xuống
    #  CSDL** — mất dữ liệu im lặng, API vẫn trả 200.
    if "metadata" in values:
        kind = db.get(DocType, values.get("doc_type_id", doc.doc_type_id))
        doc.meta = type_metadata.sanitize(
            kind.code if kind else "", values.pop("metadata"),
            values.get("owner_employee_id", doc.owner_employee_id))

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
    #  Cả «Trả về»: bản đó chưa từng được ban hành nên chưa có gì trong sổ để mà
    #  thủng. Bắt người soạn giữ lại một bản nháp bị trả mà họ đã quyết định bỏ
    #  thì danh sách chỉ dài thêm.
    if doc.status not in EDITABLE_STATUSES:
        raise HTTPException(400, "Chỉ xóa được văn bản đang ở trạng thái nháp hoặc bị trả về")
    if doc.doc_code or doc.issue_number:
        raise HTTPException(400, "Văn bản đã cấp số, không xóa được. Hãy bãi bỏ văn bản.")

    #  Dọn PHIẾU DUYỆT trước khi xóa văn bản, trong cùng giao dịch. Văn bản ở
    #  «Trả về» thì gần như luôn CÓ một phiếu duyệt đã đóng — không dọn thì nó
    #  nằm lại trỏ vào một văn bản không còn tồn tại (lỗi dựng lại được
    #  24/08/2026 trên đúng đường hợp lệ: tạo → gửi duyệt → bị trả về → Xóa).
    from app.modules.approval import instance_service

    instance_service.delete_by_entity(db, "document", doc.id)

    #  Và dọn QUAN HỆ — cả hai chiều. Cùng một loại lỗi, tìm ra ngay sau đó khi
    #  soi dữ liệu dev: hai dòng quan hệ mồ côi có từ 19/08 và 21/08. Văn bản
    #  còn sống mở tab «Quan hệ» ra thì thấy một dòng *Có kèm theo* trỏ vào chỗ
    #  trống (`document: null`) — người đọc không biết nó từng là cái gì, mà cũng
    #  không bấm vào đâu được.
    from .link_model import DocumentLink

    db.query(DocumentLink).filter(
        or_(DocumentLink.source_document_id == doc.id,
            DocumentLink.target_document_id == doc.id)
    ).delete(synchronize_session=False)

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


def discard_own_draft(db: Session, doc: Document, actor: int) -> None:
    """Bỏ BẢN NHÁP DO CHÍNH MÌNH vừa mở ra — không đòi quyền `delete`.

    Từ 24/08/2026 màn *Tạo văn bản* bấm «Tiếp tục» là đã ghi một bản nháp thật
    xuống CSDL (để quay lại không mất dữ liệu đã gõ), nên nút «Hủy» buộc phải dọn
    được cái nháp đó. Nhưng vai trò soạn thảo tiêu chuẩn (`vanban_sua`) **cố ý
    không có `delete`** — không cho xóa văn bản của người khác. Kết quả dựng lại
    được: bấm Tiếp tục rồi bấm Hủy → **403**, và bản nháp nằm lại vĩnh viễn vì
    chính người tạo cũng không có quyền xóa nó.

    Nên tách một cửa hẹp riêng: **tự bỏ nháp của mình** đi cùng quyền `create`,
    vì đúng là mặt sau của thao tác vừa tạo ra nó. Hẹp ở ba chốt:
    - chỉ trạng thái **Nháp** (còn «Trả về» đã đi qua tay người duyệt, bỏ nó là
      xóa thật, vẫn phải có `delete`);
    - chỉ **tài khoản đã tạo** ra nó;
    - chưa cấp số — chốt này `delete_document` bên dưới giữ.
    """
    if doc.status != STATUS_DRAFT:
        raise HTTPException(400, "Chỉ bỏ được văn bản đang ở trạng thái nháp")
    if doc.created_by != actor:
        raise HTTPException(403, "Chỉ người tạo mới bỏ được bản nháp này")
    delete_document(db, doc)


# ── Luồng duyệt một bước (TẠM — P3 thay) ─────────────────────────────────────
def submit(db: Session, doc: Document, actor: int) -> Document:
    """Trình bản đang mở đi duyệt. Nhận cả bản **bị trả về** — đó là cả mục đích
    của trạng thái đó: sửa xong thì gửi lại trên chính văn bản này, không phải
    dựng bản mới."""
    #  Nói thẳng ở đây thay vì để rơi xuống câu "không có bản nháp nào": văn bản
    #  bị từ chối thì `open_version` không thấy gì cả, mà câu đó không gợi được
    #  đường ra nào cho người đọc.
    if doc.status == STATUS_REJECTED:
        raise HTTPException(400, "Văn bản đã bị từ chối, không gửi duyệt lại được. "
                                 "Bấm «Sao chép» để có bản nháp mới.")
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

    #  Phần RIÊNG CỦA LOẠI phải khai đủ trước khi gửi. Người duyệt mở đơn nghỉ
    #  phép ra mà không có ngày nghỉ lẫn lý do thì họ duyệt cái gì.
    #
    #  Chặn ở lúc GỬI, không phải lúc lưu nháp — cùng luật với `required-fields.ts`
    #  của Thu mua: lưu dở dang là quyền của người soạn, gửi đi mới là cam kết.
    kind = db.get(DocType, doc.doc_type_id)
    type_metadata.require_on_submit(kind.code if kind else "", doc.meta)

    #  Kiểm TRA LUỒNG trước khi chuyển bản nháp sang «Đang duyệt». Bản clone
    #  bắt buộc có luồng riêng của pháp nhân nhận; chặn sau `db.commit()` sẽ để
    #  lại một văn bản đang duyệt nhưng không có phiên duyệt nào nhặt nó lên.
    from .approval_bridge import (ensure_dedicated_flow, is_enabled,
                                  submit_for_approval)
    approval_engine_enabled = is_enabled(db)
    if approval_engine_enabled:
        ensure_dedicated_flow(db, doc)

    version.status, version.updated_by = VERSION_SUBMITTED, actor
    #  CHỈ bản đầu tiên mới kéo cả văn bản sang "đang duyệt". Từ bản thứ hai trở
    #  đi, văn bản vẫn đang có hiệu lực bằng bản cũ trong suốt lúc bản mới chờ
    #  duyệt — chỗ dễ sai số 7 của `van-thu/02`.
    if version.prev_version_id is None:
        doc.status = STATUS_SUBMITTED
    doc.updated_by = actor

    #  Văn bản này là bản clone thì bảng theo dõi ở bản gốc phải thấy ngay —
    #  không thì pháp nhân mẹ tưởng nơi đó còn chưa đụng tới.
    from .clone_lifecycle_service import sync_status
    sync_status(doc, actor)

    db.commit()

    #  Phase 3 — nếu bộ máy duyệt dùng chung đang BẬT cho văn bản thì mở luôn
    #  một phiên nhiều bước. Cờ tắt, hoặc bật mà chưa khai luồng nào, thì
    #  `trinh_duyet` trả `None` và mọi thứ chạy y như trước: ba nút cứng
    #  submit → approve/reject trên trang chi tiết.
    if approval_engine_enabled:
        submit_for_approval(db, doc, actor)

    db.refresh(doc)
    return doc


def mark_pending_issue(db: Session, doc: Document, actor: int) -> Document:
    """Ký đủ chữ ký rồi, nhưng DỪNG LẠI chờ người soạn bấm *Ban hành*.

    Chỉ chạy với loại khai `auto_issue_after_approval = False` (26/08/2026).

    ⚠️ **Phiên bản giữ nguyên `VERSION_SUBMITTED`, không khóa, không cấp số.**
    Đó là cả cơ chế của trạng thái này: `approve()` chạy được lần sau vì bản
    vẫn đang ở đúng tư thế "chờ duyệt", trong khi `submit()` thì không nhận
    (nó chặn thẳng bản đang chờ duyệt) nên không ai gửi duyệt chồng lên được.

    Không đụng bản thứ hai trở đi: y như mọi nhịp khác, văn bản đang có hiệu lực
    bằng bản cũ thì giữ nguyên trạng thái trong suốt lúc bản mới chờ — chỗ dễ
    sai số 7 của `van-thu/02`.
    """
    version = open_version(db, doc)
    if not version or version.status != VERSION_SUBMITTED:
        raise HTTPException(400, "Không có bản nào đang chờ duyệt")

    if version.prev_version_id is None:
        doc.status = STATUS_PENDING_ISSUE
    doc.updated_by = actor

    from .clone_lifecycle_service import sync_status
    sync_status(doc, actor)

    db.commit()
    db.refresh(doc)
    return doc


def can_issue(db: Session, doc: Document, user) -> bool:
    """Tài khoản này có phải NGƯỜI SOẠN THẢO của văn bản không.

    Chốt của bước ban hành thủ công: *"user chịu trách nhiệm soạn thảo cái văn
    bản đó bấm ban hành"*. Quyền `document.approve` KHÔNG thay được — người ký
    đã ký xong phần của họ ở bộ máy duyệt rồi; ai phát hành là một trách nhiệm
    khác, và nó phải chỉ đúng một người.

    So theo hồ sơ nhân sự chứ không theo `created_by`: văn thư lập hộ thì người
    soạn thảo ghi trên phiếu mới là người chịu trách nhiệm.
    """
    employee_id = getattr(user, "employee_id", None)
    if not employee_id:
        return False
    return employee_id in (doc.drafter_employee_id, doc.owner_employee_id)


def ensure_can_issue(db: Session, doc: Document, user) -> None:
    if can_issue(db, doc, user):
        return
    raise HTTPException(
        403,
        "Văn bản này đã ký đủ và đang chờ NGƯỜI SOẠN THẢO bấm Ban hành. "
        "Bạn không phải người soạn thảo nên không ban hành thay được.",
    )


def approve(db: Session, doc: Document, actor: int,
            apply_mode: int | None = None,
            mailbox_id: int | None = None) -> Document:
    """Duyệt bản đang chờ: khóa phiên bản, cấp số nếu tới lượt, chuyển hiệu lực.

    ⚠️ **Không kéo `tab_document.status` về nháp.** Quy chế lên bản 2.0 thì văn
    bản VẪN đang có hiệu lực trong suốt lúc bản mới chờ duyệt — xem chỗ dễ sai
    số 7 của `van-thu/02`.

    `mailbox_id` = hộp thư gửi thông báo ban hành danh nghĩa địa chỉ khác
    (26/08/2026). Người gọi phải kiểm quyền dùng hộp thư TRƯỚC — xem
    `mailbox_service.ensure_duoc_dung`; ở đây chỉ ghi lại.
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

    #  Ghi TRƯỚC commit: `notify_document_issued` chạy sau đó và đọc thẳng ô này
    #  để biết gửi bằng hộp thư nào.
    if mailbox_id is not None:
        doc.issue_mailbox_id = mailbox_id or None

    from .clone_notification import notify_clones_stale
    from .clone_service import clones_of, mark_clones_for_review
    from .excerpt_service import is_excerpt
    from .issue_service import ensure_can_issue
    from .parent_change_service import apply_new_version
    from .supersede_service import apply_supersede

    #  J11 — loại khai "ban hành phải kèm Quyết định" thì thiếu là không cho ban
    #  hành. Chặn ở đây chứ không chỉ trên màn xem trước: màn đó là tiện ích.
    ensure_can_issue(db, doc)

    doc_type = doc_type_or_400(db, doc.doc_type_id)
    #  Bản trích KHÔNG cấp số hiệu riêng — nó gọi theo số của bản gốc (C19).
    #  Cấp số cho nó là đẻ ra một số hiệu thứ hai cho cùng một nội dung.
    if doc_type.number_when == NUMBER_ON_APPROVE and not is_excerpt(db, doc.id):
        numbering.assign(db, doc, doc_type, issue_year(doc))
    assign_book_number(db, doc)

    lock_version(version, actor)

    previous = db.get(DocumentVersion, version.prev_version_id) if version.prev_version_id else None
    effective = version.effective_from or doc.effective_date or date.today()

    #  Văn bản bị chính lượt ban hành này BÃI BỎ (quan hệ *bãi bỏ*). Khai ngoài
    #  nhánh `if` để phần gửi thông báo sau commit lúc nào cũng có biến để đọc.
    revoked_docs: list[Document] = []

    if effective <= date.today():
        switch_current(db, doc, version, previous)
        #  J10 — ba tác động tự động: văn bản này *thay thế* cái nào thì cái đó
        #  chuyển sang "bị thay thế", *bãi bỏ* cái nào thì cái đó sang "bãi bỏ".
        #  Quan hệ *sửa đổi* KHÔNG đụng trạng thái — phần không bị sửa vẫn có
        #  hiệu lực, và chính vì thế mà cái nhãn cảnh báo là bắt buộc.
        #
        #  ⚠️ Chỉ chạy khi văn bản mới THẬT SỰ có hiệu lực. Ban hành hôm nay mà
        #  áp dụng từ tháng sau thì văn bản cũ còn hiệu lực nguyên tháng đó —
        #  đổi trạng thái sớm là khai tử một văn bản đang còn giá trị.
        #  Giữ lại danh sách văn bản bị BÃI BỎ để báo cho pháp nhân con SAU
        #  commit — xem `bao_bai_bo_theo_quan_he`.
        revoked_docs.extend(apply_supersede(db, doc, actor))
        #  E07 — cha lên phiên bản mới thì MỌI văn bản con bị xử lý theo cột
        #  `on_parent_new_version` của quy tắc quan hệ. Bản trích là trường hợp
        #  đặc biệt: cột đó bị khóa cứng ở mức "đánh dấu cần rà lại" (E11 a).
        if previous is not None:
            apply_new_version(
                db, doc,
                f"Văn bản cha đã lên phiên bản {version.version_no} ngày "
                f"{date.today():%d/%m/%Y}. Rà lại xem còn đúng không.",
            )
            #  Điều kiện 3 của clone (F11): mọi bản clone bị đánh dấu cần rà lại
            #  VÀ người phụ trách phải được báo. Đánh dấu mà không báo thì cái
            #  dấu nằm im tới lúc có người tình cờ mở văn bản ra xem.
            if mark_clones_for_review(db, doc):
                notify_clones_stale(db, doc, clones_of(db, doc.id))
    elif previous is None:
        #  Bản đầu tiên duyệt trước ngày hiệu lực: đã duyệt nhưng chưa áp dụng.
        #  Bản thứ hai trở đi thì KHÔNG đụng gì — bản cũ còn đang chạy.
        doc.status = STATUS_APPROVED
        doc.effective_date = effective

    #  Bản clone vừa được pháp nhân con ban hành → cột theo dõi ở bản gốc sang
    #  "Đã ban hành". Đặt TRƯỚC commit để đi chung một transaction với việc cấp
    #  số: có số hiệu mà bảng vẫn ghi "Đã gửi" là hai nguồn nói khác nhau.
    from .clone_lifecycle_service import sync_status
    sync_status(doc, actor)

    doc.updated_by = actor
    db.commit()
    db.refresh(doc)

    #  Ban hành xuống thì mỗi pháp nhân trong phạm vi có ngay một bản nháp
    #  (20/08/2026). Chạy SAU commit và tự nuốt lỗi — bản gốc đã ban hành xong
    #  và đúng, không được để việc clone kéo đổ nó.
    from .clone_lifecycle_service import auto_clone_after_issue
    from .clone_notification import notify_clone_created

    clones = auto_clone_after_issue(db, doc, actor)
    if clones:
        for clone in clones:
            notify_clone_created(db, doc, clone)
        db.commit()

    #  Văn bản CŨ vừa bị bãi bỏ bởi chính văn bản này: pháp nhân con giữ bản
    #  riêng của nó phải được báo, y như khi bấm nút «Bãi bỏ».
    notify_revocation_by_relation(db, revoked_docs, doc, actor)

    #  Thành viên thuộc phạm vi nhận cả chuông lẫn email có link chỉ đọc. Làm
    #  sau transaction ban hành và nuốt lỗi: SMTP/Redis hỏng không được biến
    #  một văn bản đã cấp số thành thao tác thất bại trên màn hình.
    try:
        from .issue_notification import notify_document_issued
        notify_document_issued(db, doc, version, actor)
    except Exception:  # noqa: BLE001 — kênh thông báo là best-effort
        import logging
        logging.getLogger(__name__).exception(
            "Không tạo được thông báo ban hành cho văn bản #%s", doc.id)

    return doc


def _close_approval_instance(db: Session, doc: Document, reason: str, actor: int, *,
                      label: str, version_status: int,
                      document_status: int) -> Document:
    """Nền chung của BA nhịp kết thúc phiên duyệt: trả về · từ chối · rút phiếu.

    Ba nhịp khác nhau đúng hai con số (trạng thái phiên bản, trạng thái văn bản)
    và cái nhãn ghi vào lý do sửa. Mọi thứ còn lại — chốt "có bản nào đang chờ
    duyệt không", luật *bản thứ hai trở đi giữ nguyên trạng thái văn bản*, đồng
    bộ cột theo dõi bản clone — phải giống nhau tuyệt đối, nên nằm một chỗ. Chép
    ra ba bản là sớm muộn có một bản quên luật bản 2.0 và kéo văn bản đang có
    hiệu lực về nháp.

    ⚠️ Ở đây từng có một khối F13 (chốt cơ chế áp dụng) bị chép nhầm từ
    `approve()` sang. Hàm cũ không có tham số `apply_mode` nên MỌI lần trả lại
    văn bản đều nổ `NameError` — im lặng cho tới 17/08 vì chưa bài kiểm nào gọi
    tới. Đã bỏ: chốt cơ chế áp dụng là việc của lúc BAN HÀNH.
    """
    version = open_version(db, doc)
    if not version or version.status != VERSION_SUBMITTED:
        raise HTTPException(400, "Không có bản nào đang chờ duyệt")

    version.status, version.updated_by = version_status, actor
    version.change_reason = (
        f"{version.change_reason}\n[{label}] {reason}".strip()
        if version.change_reason else f"[{label}] {reason}"
    )
    #  Bản đầu tiên kéo cả văn bản theo; bản thứ hai trở đi thì VĂN BẢN GIỮ
    #  NGUYÊN trạng thái vì bản trước đó vẫn đang có hiệu lực — chỗ dễ sai số 7
    #  của `van-thu/02`. Lúc đó chỗ duy nhất nói được "bản này vừa bị trả" là
    #  dòng phiên bản, nên nó phải có thang trạng thái riêng.
    if version.prev_version_id is None:
        doc.status = document_status
    doc.updated_by = actor

    #  Bản clone bị trả lại thì quay về "Đang soạn" ở bảng theo dõi — để nguyên
    #  "Đang duyệt" là pháp nhân mẹ chờ một cái duyệt không bao giờ tới.
    from .clone_lifecycle_service import sync_status
    sync_status(doc, actor)

    db.commit()
    db.refresh(doc)
    return doc


def send_back(db: Session, doc: Document, reason: str, actor: int) -> Document:
    """TRẢ VỀ kèm lý do — còn đường đi tiếp: sửa rồi **gửi duyệt lại**.

    Nội dung giữ nguyên để sửa tiếp, và phiên bản vẫn giữ `open_slot` nên không
    ai mở được một bản nháp thứ hai chen vào giữa.
    """
    return _close_approval_instance(db, doc, reason, actor, label="Trả về",
                             version_status=VERSION_RETURNED,
                             document_status=STATUS_RETURNED)


def reject(db: Session, doc: Document, reason: str, actor: int) -> Document:
    """TỪ CHỐI kèm lý do — hết đường: khóa sửa, muốn làm lại thì *Sao chép*.

    Phiên bản **nhả `open_slot`** (xem `OPEN_STATUSES`): bản đó chết hẳn, giữ chỗ
    thì văn bản bị nó chặn vĩnh viễn, không mở nổi bản mới.
    """
    return _close_approval_instance(db, doc, reason, actor, label="Từ chối",
                             version_status=VERSION_REJECTED,
                             document_status=STATUS_REJECTED)


def withdraw_document(db: Session, doc: Document, reason: str, actor: int) -> Document:
    """NGƯỜI NỘP TỰ RÚT — về Nháp, không phải "bị trả".

    Cố ý khác hai nhịp trên: không ai trả gì cho ai, nên đừng treo lên phiếu một
    trạng thái đọc như bị người khác đánh giá.
    """
    return _close_approval_instance(db, doc, reason, actor, label="Rút phiếu",
                             version_status=VERSION_DRAFT,
                             document_status=STATUS_DRAFT)


def confirm_reviewed(db: Session, doc: Document, conclusion: str, actor: int) -> Document:
    """TẮT cờ «cần rà lại» sau khi người phụ trách đã đối chiếu xong.

    Cờ này có **năm chỗ bật** (bản gốc lên bản mới, cha bị bãi bỏ, cha lên bản
    mới, hai luật của bản trích) mà trước đây **không có chỗ nào tắt** — rà xong,
    sửa xong, ban hành xong thì băng cảnh báo vẫn treo vĩnh viễn. Vài tháng là
    văn bản nào cũng đeo băng vàng, và đúng lúc cảnh báo cần được chú ý thì
    không ai còn nhìn nữa.

    Bắt ghi KẾT LUẬN chứ không cho bấm một cái cho xong: người sau mở nhật ký ra
    phải đọc được «đã đối chiếu, vẫn đúng, không phải sửa» hay «đã sửa theo
    Chương II» — hai câu đó dẫn tới hai hành động khác hẳn nhau nếu về sau có
    tranh chấp. Kết luận đi vào `audit` ở tầng controller, không thêm cột.

    Không kiểm trạng thái văn bản: rà soát là việc đọc, làm được ở mọi trạng
    thái. Quyền thì gác bằng `write` như mọi thao tác sửa khác.
    """
    if not doc.needs_review:
        raise HTTPException(400, "Văn bản này không có dấu cần rà lại")

    doc.needs_review = False
    doc.needs_review_note = ""

    #  Bản clone: dời con trỏ phiên bản lên bản hiện hành của gốc, nếu không thì
    #  bảng theo dõi vẫn kêu "lệch bản" vĩnh viễn dù đã rà xong. Tắt băng vàng mà
    #  quên chỗ này là chữa đúng một nửa — người rà thấy sạch, người ở tập đoàn
    #  mở bảng theo dõi vẫn thấy đỏ (bắt được 20/08/2026).
    if doc.source_document_id:
        from .clone_lifecycle_service import sync_status

        origin = db.get(Document, doc.source_document_id)
        if origin and origin.current_version_id:
            doc.clone_source_version_id = origin.current_version_id
        #  Gỡ luôn nhãn "Cần rà lại" khỏi cột theo dõi, trả về đúng chỗ bản clone
        #  đang đứng — đã ban hành thì là "Đã ban hành", còn nháp thì "Đang soạn".
        doc.clone_status = 0
        sync_status(doc, actor)

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

    ⚠️ **Bãi bỏ CŨNG là một thay đổi về quyền xem** (24/08/2026): từ đây văn bản
    chỉ còn người tạo · người chịu trách nhiệm · người bãi bỏ · người giữ sổ mở
    được — xem `revoke_access.py`. Câu "tra sổ vẫn ra" ở trên vẫn đúng, nhưng chỉ
    còn đúng với người giữ sổ, không còn đúng với cả phòng.
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

    #  BÁO CHO PHÁP NHÂN CON đang giữ bản riêng — chuông + thư. Chạy SAU commit
    #  và tự nuốt lỗi, cùng lý lẽ với thư ban hành: văn bản đã bãi bỏ rồi, không
    #  được để SMTP hay broker kéo đổ nó.
    try:
        from .revoke_notification import notify_clones_revoked

        notify_clones_revoked(db, doc, reason, actor)
    except Exception:  # noqa: BLE001
        logging.getLogger(__name__).exception(
            "Không gửi được thông báo bãi bỏ văn bản #%s", doc.id)

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
    #  Văn bản bị bãi bỏ theo quan hệ trong cả lượt quét này — gom lại, báo một
    #  lần sau commit (xem `bao_bai_bo_theo_quan_he`).
    revoked_docs: list[tuple[Document, Document]] = []
    for doc, version in q.all():
        #  Văn bản đã trỏ đúng bản này rồi thì chỉ còn thiếu việc đổi trạng thái —
        #  trường hợp bản ĐẦU TIÊN duyệt trước ngày hiệu lực (`current_version_id`
        #  gán từ lúc tạo, nhưng văn bản mới chỉ ở "đã duyệt").
        if doc.current_version_id == version.id:
            if doc.status == STATUS_APPROVED:
                switch_current(db, doc, version, None)
                revoked_docs += [(old, doc) for old in _apply_effective_side_effects(db, doc)]
                changed += 1
            continue
        current = db.get(DocumentVersion, doc.current_version_id) if doc.current_version_id else None
        #  Bản đang dùng đã mới hơn thì bỏ qua — tới ngày mà đã có bản 3.0 chạy
        #  rồi thì đừng kéo ngược về 2.0.
        if current and (current.major, current.minor) > (version.major, version.minor):
            continue
        switch_current(db, doc, version, current)
        revoked_docs += [(old, doc) for old in _apply_effective_side_effects(db, doc)]
        changed += 1

    if changed:
        db.commit()

    #  Actor 0 = hệ thống: tới ngày hiệu lực thì chính hệ đẩy văn bản cũ sang
    #  bãi bỏ, không phải ai bấm.
    for old, new in revoked_docs:
        notify_revocation_by_relation(db, [old], new, 0)

    return changed


def notify_revocation_by_relation(db: Session, revoked_docs: list[Document],
                            by_document: Document, actor: int) -> None:
    """Báo cho pháp nhân con của những văn bản vừa bị bãi bỏ BỞI MỘT VĂN BẢN KHÁC.

    Có HAI đường đưa một văn bản sang trạng thái bãi bỏ: bấm nút «Bãi bỏ»
    (`revoke`) và ban hành một văn bản mang quan hệ *bãi bỏ* (`apply_supersede`).
    Đường thứ hai trước đây **không báo cho ai** — cùng một chuyện với người nhận
    mà chỉ vì người ban hành thao tác kiểu khác.

    ⚠️ Gọi **sau commit**: hàm gửi thư tự commit để `EmailLog` tồn tại trước khi
    tác vụ nền đọc tới. Nuốt lỗi vì văn bản mới đã ban hành xong rồi.
    """
    if not revoked_docs:
        return

    reason = (
        f"Bị bãi bỏ bởi {by_document.doc_code or by_document.issue_number or by_document.title}"
    )
    for old in revoked_docs:
        try:
            from .revoke_notification import notify_clones_revoked

            notify_clones_revoked(db, old, reason, actor)
        except Exception:  # noqa: BLE001 — kênh thông báo là best-effort
            logging.getLogger(__name__).exception(
                "Không gửi được thông báo bãi bỏ (theo quan hệ) cho văn bản #%s", old.id)


def _apply_effective_side_effects(db: Session, doc: Document) -> list[Document]:
    """Việc phải làm khi một văn bản THẬT SỰ có hiệu lực, dù tới đường nào.

    `approve()` chạy phần này khi ban hành mà hiệu lực ngay. Văn bản hẹn hiệu lực
    tháng sau thì lúc ban hành CHƯA được chạy — văn bản cũ còn hiệu lực nguyên
    tháng đó. Tới ngày, `activate_due_versions()` mới gọi vào đây.

    Không có hàm này thì «Quyết định 47 hiệu lực từ 01/09» sẽ không bao giờ đẩy
    «Quyết định 15» sang *bị thay thế* — nó nằm im mãi ở trạng thái có hiệu lực.
    """
    from .clone_notification import notify_clones_stale
    from .clone_service import clones_of, mark_clones_for_review
    from .parent_change_service import apply_new_version
    from .supersede_service import apply_supersede

    #  Actor 0 = hệ thống. Đây đúng là hệ thống làm, không phải người nào bấm.
    revoked_docs = apply_supersede(db, doc, 0)
    apply_new_version(
        db, doc,
        f"Văn bản cha đã có hiệu lực từ {date.today():%d/%m/%Y}. "
        "Rà lại xem còn đúng không.",
    )
    if mark_clones_for_review(db, doc):
        notify_clones_stale(db, doc, clones_of(db, doc.id))

    #  Chưa gửi được thông báo bãi bỏ ở đây — `activate_due_versions` mới là chỗ
    #  commit. Đẩy danh sách lên cho nó.
    return revoked_docs


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
