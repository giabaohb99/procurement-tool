"""HẠN XEM TỆP ĐÍNH KÈM của văn bản.

Một văn bản đặt được ngày *"xem tệp tới ngày…"* (`Document.attachment_view_until`).
Quá ngày đó thì mọi tệp đính kèm của nó **không mở ra và không tải về được nữa**
— dùng cho tài liệu chỉ cho xem trong một khoảng: bảng lương kỳ này, hồ sơ thầu
tới ngày mở thầu, tài liệu họp chỉ sống tới hết cuộc họp.

⚠️ Kiểm ở BACKEND, không phải ở giao diện. Giấu nút xem trên màn hình chỉ ngăn
được người dùng bình thường; ai copy được đường dẫn `/api/attachments/{id}/view`
thì vẫn lấy về nguyên tệp. Hạn xem mà chỉ có ở giao diện là hạn xem giả.

Đính kèm của văn bản treo vào **phiên bản** (`entity = 'document_version'`), nên
phải đi hai chặng mới tới được cột hạn: link → phiên bản → văn bản.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import Document
from .version_model import DocumentVersion

#  Entity của đính kèm văn bản. Các entity khác (YCMH, ĐMH, bình luận…) không
#  có hạn xem nên đi qua đây là không đổi gì.
ENTITY_DINH_KEM_VAN_BAN = "document_version"


def van_ban_cua_dinh_kem(db: Session, entity: str, entity_id: int) -> Document | None:
    """Văn bản chủ của một tệp đính kèm. `None` = tệp không thuộc văn bản nào."""
    if entity != ENTITY_DINH_KEM_VAN_BAN:
        return None
    version = db.get(DocumentVersion, entity_id)
    if version is None:
        return None
    return db.get(Document, version.document_id)


def het_han_xem(doc: Document | None, hom_nay: date | None = None) -> bool:
    """Văn bản này đã quá hạn cho xem tệp chưa.

    So bằng `>` chứ không `>=`: đặt hạn 24/08 nghĩa là **hết ngày 24/08 vẫn
    xem được**, đúng cách người Việt đọc "xem tới ngày 24/08".
    """
    if doc is None or doc.attachment_view_until is None:
        return False
    return (hom_nay or date.today()) > doc.attachment_view_until


def chan_neu_het_han(db: Session, entity: str, entity_id: int) -> None:
    """Ném 403 nếu tệp thuộc một văn bản đã quá hạn cho xem.

    403 chứ không 404: tệp có thật và người này vốn có quyền, chỉ là **hết
    giờ**. Trả 404 là nói dối và người dùng sẽ đi báo mất tệp.
    """
    doc = van_ban_cua_dinh_kem(db, entity, entity_id)
    if not het_han_xem(doc):
        return
    raise HTTPException(
        403,
        f"Tệp đính kèm của văn bản này chỉ xem được tới ngày "
        f"{doc.attachment_view_until:%d/%m/%Y}.",
    )
