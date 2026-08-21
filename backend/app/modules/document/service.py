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


def chan_sua_khi_dang_duyet(doc: Document) -> None:
    """Văn bản ĐANG TRÌNH DUYỆT thì đóng băng cả bộ trường chung (19/08/2026).

    Không chỉ thân văn bản: đổi **mức mật** hay **tiêu đề** dưới tay người duyệt
    cũng là đưa họ ký một thứ khác với thứ họ đọc. Đã dựng lại được — gửi duyệt
    xong `PATCH /documents/{id}` vẫn trả 200 và nâng được mức mật lên "Mật".

    Cùng luật với nội dung, xem `version_service.chan_khi_dang_duyet`: muốn sửa
    thì rút phiếu → văn bản về Nháp.
    """
    if doc.status == STATUS_SUBMITTED:
        raise HTTPException(409, "Văn bản đang trình duyệt nên khóa thông tin. "
                                 "Muốn sửa thì rút phiếu duyệt (hoặc chờ người duyệt trả lại).")


def update_document(db: Session, doc: Document, data: DocumentUpdate, actor: int) -> Document:
    """Sửa bộ trường chung. Không đụng nội dung (ở phiên bản) và không đụng số hiệu."""
    chan_sua_khi_dang_duyet(doc)

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

    #  Kiểm TRA LUỒNG trước khi chuyển bản nháp sang «Đang duyệt». Bản clone
    #  bắt buộc có luồng riêng của pháp nhân nhận; chặn sau `db.commit()` sẽ để
    #  lại một văn bản đang duyệt nhưng không có phiên duyệt nào nhặt nó lên.
    from .approval_bridge import (dam_bao_co_luong_rieng, dang_bat,
                                  trinh_duyet)
    bo_may_duyet_bat = dang_bat(db)
    if bo_may_duyet_bat:
        dam_bao_co_luong_rieng(db, doc)

    version.status, version.updated_by = VERSION_SUBMITTED, actor
    #  CHỈ bản đầu tiên mới kéo cả văn bản sang "đang duyệt". Từ bản thứ hai trở
    #  đi, văn bản vẫn đang có hiệu lực bằng bản cũ trong suốt lúc bản mới chờ
    #  duyệt — chỗ dễ sai số 7 của `van-thu/02`.
    if version.prev_version_id is None:
        doc.status = STATUS_SUBMITTED
    doc.updated_by = actor

    #  Văn bản này là bản clone thì bảng theo dõi ở bản gốc phải thấy ngay —
    #  không thì pháp nhân mẹ tưởng nơi đó còn chưa đụng tới.
    from .clone_lifecycle_service import dong_bo_trang_thai
    dong_bo_trang_thai(doc, actor)

    db.commit()

    #  Phase 3 — nếu bộ máy duyệt dùng chung đang BẬT cho văn bản thì mở luôn
    #  một phiên nhiều bước. Cờ tắt, hoặc bật mà chưa khai luồng nào, thì
    #  `trinh_duyet` trả `None` và mọi thứ chạy y như trước: ba nút cứng
    #  submit → approve/reject trên trang chi tiết.
    if bo_may_duyet_bat:
        trinh_duyet(db, doc, actor)

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
        apply_supersede(db, doc, actor)
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
    from .clone_lifecycle_service import dong_bo_trang_thai
    dong_bo_trang_thai(doc, actor)

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


def reject(db: Session, doc: Document, reason: str, actor: int) -> Document:
    """Trả lại bản nháp kèm lý do. Bản nháp giữ nguyên nội dung để sửa tiếp."""
    version = open_version(db, doc)
    if not version or version.status != VERSION_SUBMITTED:
        raise HTTPException(400, "Không có bản nào đang chờ duyệt")

    #  ⚠️ Ở đây từng có một khối F13 (chốt cơ chế áp dụng) bị chép nhầm từ
    #  `approve()` sang. Hàm này không có tham số `apply_mode` nên MỌI lần trả
    #  lại văn bản đều nổ `NameError` — im lặng cho tới 17/08 vì chưa bài kiểm
    #  nào gọi `reject()`. Đã bỏ: chốt cơ chế áp dụng là việc của lúc BAN HÀNH,
    #  trả lại thì chưa ban hành gì cả.
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

    #  Bản clone bị trả lại thì quay về "Đang soạn" ở bảng theo dõi — để nguyên
    #  "Đang duyệt" là pháp nhân mẹ chờ một cái duyệt không bao giờ tới.
    from .clone_lifecycle_service import dong_bo_trang_thai
    dong_bo_trang_thai(doc, actor)

    db.commit()
    db.refresh(doc)
    return doc


def xac_nhan_da_ra_soat(db: Session, doc: Document, ket_luan: str, actor: int) -> Document:
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
        from .clone_lifecycle_service import dong_bo_trang_thai

        goc = db.get(Document, doc.source_document_id)
        if goc and goc.current_version_id:
            doc.clone_source_version_id = goc.current_version_id
        #  Gỡ luôn nhãn "Cần rà lại" khỏi cột theo dõi, trả về đúng chỗ bản clone
        #  đang đứng — đã ban hành thì là "Đã ban hành", còn nháp thì "Đang soạn".
        doc.clone_status = 0
        dong_bo_trang_thai(doc, actor)

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
                _apply_effective_side_effects(db, doc)
                changed += 1
            continue
        current = db.get(DocumentVersion, doc.current_version_id) if doc.current_version_id else None
        #  Bản đang dùng đã mới hơn thì bỏ qua — tới ngày mà đã có bản 3.0 chạy
        #  rồi thì đừng kéo ngược về 2.0.
        if current and (current.major, current.minor) > (version.major, version.minor):
            continue
        switch_current(db, doc, version, current)
        _apply_effective_side_effects(db, doc)
        changed += 1

    if changed:
        db.commit()
    return changed


def _apply_effective_side_effects(db: Session, doc: Document):
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
    apply_supersede(db, doc, 0)
    apply_new_version(
        db, doc,
        f"Văn bản cha đã có hiệu lực từ {date.today():%d/%m/%Y}. "
        "Rà lại xem còn đúng không.",
    )
    if mark_clones_for_review(db, doc):
        notify_clones_stale(db, doc, clones_of(db, doc.id))


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
