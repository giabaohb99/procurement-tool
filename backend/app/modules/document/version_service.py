"""Nghiệp vụ PHIÊN BẢN: mở bản mới, ghi nội dung, khóa bản đã duyệt.

Hai ràng buộc của tệp này đều là chốt chặn thật ở **tầng dịch vụ**, không phải
ẩn nút trên giao diện — bài kiểm gọi thẳng API để canh việc đó:

1. Phiên bản đã duyệt (`is_locked`) không sửa được bằng bất cứ đường nào → 409.
2. Mỗi văn bản chỉ một bản đang mở, ép bằng `open_slot` ở tầng dữ liệu. Hai
   người bấm "mở phiên bản mới" cùng lúc thì **một người thắng**, người kia nhận
   câu nói rõ ai đang giữ bản nháp.
"""
import hashlib
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink

from .model import Document
from .schema import VersionContentUpdate, VersionCreate
from .serializer import holder_name
from .service import ATTACH_ENTITY, open_version
from .version_model import (CHANGE_MAJOR, VERSION_APPROVED, VERSION_DRAFT,
                            VERSION_SUBMITTED, DocumentVersion)


def list_versions(db: Session, doc: Document) -> list[DocumentVersion]:
    """Mới nhất lên đầu — người mở tab phiên bản gần như luôn tìm bản đang chạy."""
    return (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == doc.id)
        .order_by(DocumentVersion.major.desc(), DocumentVersion.minor.desc())
        .all()
    )


def get_or_404(db: Session, doc: Document, version_id: int) -> DocumentVersion:
    version = db.get(DocumentVersion, version_id)
    if not version or version.document_id != doc.id:
        raise HTTPException(404, "Không tìm thấy phiên bản")
    return version


def save_content(db: Session, version: DocumentVersion, data: VersionContentUpdate,
                 actor: int) -> DocumentVersion:
    """Ghi nội dung bản nháp. Đường mà tự động lưu gọi liên tục theo nhịp gõ."""
    _require_open(db, version)

    #  Kéo thước lề chỉ gửi hai số lề, không gửi thân văn bản — đừng xóa trắng
    #  nội dung chỉ vì trường vắng mặt.
    if data.content_html is not None:
        version.content_html = data.content_html
    if data.margin_left_mm is not None:
        version.margin_left_mm = data.margin_left_mm
    if data.margin_right_mm is not None:
        version.margin_right_mm = data.margin_right_mm
    if data.auto_heading_number is not None:
        version.auto_heading_number = data.auto_heading_number
    for o in ("header_left", "header_right", "footer_left", "footer_right"):
        if getattr(data, o) is not None:
            setattr(version, o, getattr(data, o))
    if data.change_summary is not None:
        version.change_summary = data.change_summary
    if data.change_reason is not None:
        version.change_reason = data.change_reason
    if data.effective_from is not None:
        version.effective_from = data.effective_from
    version.updated_by = actor
    db.commit()
    db.refresh(version)
    return version


def open_new_version(db: Session, doc: Document, data: VersionCreate,
                     actor: int) -> DocumentVersion:
    """Mở phiên bản mới từ bản đang dùng: chép nội dung, chép đính kèm, bắt lý do.

    **Không đụng `tab_document.status`.** Trong suốt lúc bản mới còn nháp / còn
    duyệt, văn bản vẫn là bản cũ và vẫn ghi "có hiệu lực" (C16, C17).
    """
    existing = open_version(db, doc)
    if existing:
        holder = holder_name(db, existing.created_by) or "người khác"
        raise HTTPException(
            409, f"Bản nháp {existing.version_no} đang do {holder} giữ. "
                 "Mỗi văn bản chỉ mở được một bản nháp cùng lúc."
        )

    base = db.get(DocumentVersion, doc.current_version_id) if doc.current_version_id else None
    if base is None:
        raise HTTPException(400, "Văn bản chưa có phiên bản nào đang dùng")
    if base.status != VERSION_APPROVED:
        raise HTTPException(400, "Chỉ mở phiên bản mới từ bản đã được duyệt")

    #  Sửa lớn lên 2.0, sửa nhỏ lên 1.1 — chính chỗ này là lý do bắt người dùng
    #  chọn `change_kind` thay vì tự đoán.
    if data.change_kind == CHANGE_MAJOR:
        major, minor = base.major + 1, 0
    else:
        major, minor = base.major, base.minor + 1

    version = DocumentVersion(
        document_id=doc.id, major=major, minor=minor, status=VERSION_DRAFT,
        content_html=base.content_html,
        #  Bản mới thừa hưởng THỂ THỨC của bản nó sinh ra từ đó: mở bản 2.0 mà
        #  lề nhảy về mặc định thì cả văn bản lệch so với bản đã ký.
        margin_left_mm=base.margin_left_mm,
        margin_right_mm=base.margin_right_mm,
        auto_heading_number=base.auto_heading_number,
        header_left=base.header_left, header_right=base.header_right,
        footer_left=base.footer_left, footer_right=base.footer_right,
        change_kind=data.change_kind,
        change_summary=data.change_summary,
        change_reason=data.change_reason,
        #  Bỏ trống thì theo mức sửa: sửa lớn buộc người đã đọc bản cũ xác nhận
        #  đã đọc lại, sửa nhỏ thì không.
        requires_reconfirm=(data.requires_reconfirm
                            if data.requires_reconfirm is not None
                            else data.change_kind == CHANGE_MAJOR),
        effective_from=data.effective_from,
        prev_version_id=base.id,
        created_by=actor, updated_by=actor,
    )
    db.add(version)

    try:
        db.flush()
    except IntegrityError:
        #  `open_slot` chặn ở tầng dữ liệu: người thứ hai đi tới đây nghĩa là
        #  người thứ nhất vừa ghi xong giữa hai câu lệnh của ta.
        db.rollback()
        raise HTTPException(409, "Một bản nháp khác vừa được mở cho văn bản này")

    _copy_attachments(db, base.id, version.id, actor)
    db.commit()
    db.refresh(version)
    return version


def lock_version(version: DocumentVersion, actor: int):
    """Khóa phiên bản khi được duyệt. **Một chiều — không có hàm mở khóa.**

    `sha256` tính đúng lúc này: sau đó nội dung không đổi được nữa, nên con số
    này là dấu vân tay dùng được để đối chiếu bản in với bản đã duyệt (C06).
    """
    version.status = VERSION_APPROVED
    version.is_locked = True
    version.content_sha256 = hashlib.sha256(
        (version.content_html or "").encode("utf-8")
    ).hexdigest()
    version.approved_at = datetime.now()
    version.approved_by = actor
    version.updated_by = actor


def _require_open(db: Session, version: DocumentVersion):
    if version.is_locked or version.status == VERSION_APPROVED:
        raise HTTPException(409, f"Phiên bản {version.version_no} đã duyệt, không sửa được. "
                                 "Muốn sửa thì mở phiên bản mới.")
    chan_khi_dang_duyet(version)


def chan_khi_dang_duyet(version: DocumentVersion) -> None:
    """ĐANG TRÌNH DUYỆT thì đóng băng — 409 (19/08/2026).

    Trước đây bản «đang duyệt» vẫn ghi được, với lý do "trả lại thì gõ tiếp".
    Lý do đó chết từ D-029: bị trả lại hay rút phiếu là văn bản **về Nháp** rồi
    mới gõ tiếp, nên không cần mở cửa trong lúc đang duyệt nữa.

    Mở cửa lúc đó là một lỗ hổng thật, đã dựng lại được: người duyệt đọc bản A,
    người soạn sửa thành bản B, người duyệt bấm Duyệt → **ban hành bản B mà
    không ai đọc**. Luồng nhiều bước còn tệ hơn — bước 1 ký trên bản A, bước 2
    ký trên bản B, dấu vết ghi "đã duyệt" cho cả hai. `content_sha256` chỉ tính
    lúc khóa nên sau đó không còn gì để đối chiếu ngược.

    Đường ra cho người soạn: **Rút phiếu** (hoặc người duyệt trả lại) → văn bản
    về Nháp → sửa tiếp. Không ai bị kẹt.
    """
    if version.status == VERSION_SUBMITTED:
        raise HTTPException(409,
                            f"Phiên bản {version.version_no} đang trình duyệt nên khóa nội dung. "
                            "Muốn sửa thì rút phiếu duyệt (hoặc chờ người duyệt trả lại) — "
                            "văn bản về Nháp rồi sửa tiếp.")


def _copy_attachments(db: Session, from_version_id: int, to_version_id: int, actor: int):
    """Chép LIÊN KẾT tệp sang bản mới — không chép tệp.

    Một tệp gắn được vào nhiều bản ghi (`tab_file_link`), nên bản mới dùng chung
    đúng tệp đó. Bản cũ vẫn giữ liên kết của nó: bản đã duyệt phải luôn tra ra
    đúng bộ tệp lúc duyệt, kể cả khi bản mới đã gỡ bớt.
    """
    links = db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY,
                                      FileLink.entity_id == from_version_id).all()
    for link in links:
        db.add(FileLink(file_id=link.file_id, entity=ATTACH_ENTITY,
                        entity_id=to_version_id, doc_type=link.doc_type,
                        sort_order=link.sort_order, created_by=actor, updated_by=actor))
