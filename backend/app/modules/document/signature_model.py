"""CHỮ KÝ trên văn bản (J02, J03) — `04` mục 7.2.

**Ba loại chữ ký, giá trị pháp lý KHÁC HẲN nhau.** Đây là chỗ nguy hiểm nhất của
cả nhóm J, nên `sign_kind` phải hiện rõ trên giao diện chứ không giấu trong tài
liệu hướng dẫn:

  1. **Ký điện tử nội bộ** — hệ thống này tự làm. Đủ giá trị TRONG NỘI BỘ tập
     đoàn, **không có giá trị với bên ngoài**.
  2. **Ký số có chứng thư** — qua nhà cung cấp chứng thư số Việt Nam, cần thiết
     bị USB. Đây là J08, một dịch vụ riêng chưa làm; dòng loại 2 ở bảng này chỉ
     là bản GHI NHẬN việc ký đã làm ở nơi khác.
  3. **Ký giấy đã quét lên** — cũng là ghi nhận một việc làm ngoài hệ thống.

Người dùng nhầm hai loại đầu là gửi ra ngoài một văn bản tưởng có giá trị pháp
lý mà thật ra không.

Bảng **chỉ ghi thêm** — không sửa, không xóa. Một chữ ký đã đặt mà gỡ được thì
nó không còn là chữ ký.
"""
from datetime import datetime

from sqlalchemy import (BigInteger, DateTime, Index, LargeBinary, SmallInteger,
                        String)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

SIGN_INTERNAL = 1  # ký điện tử nội bộ — hệ thống này làm
SIGN_CERTIFIED = 2  # ký số có chứng thư — J08, làm ở dịch vụ riêng
SIGN_SCANNED = 3    # ký giấy đã quét lên

SIGN_KIND_LABELS = {
    SIGN_INTERNAL: "Ký điện tử nội bộ",
    SIGN_CERTIFIED: "Ký số có chứng thư",
    SIGN_SCANNED: "Ký giấy đã quét",
}

#  Câu nói rõ GIÁ TRỊ PHÁP LÝ, hiện ngay cạnh chữ ký. Tài liệu yêu cầu tường
#  minh chỗ này: "cách chắc chắn nhất để họ không nhầm là ghi rõ ngay cạnh chữ
#  ký chứ không giấu trong tài liệu hướng dẫn".
SIGN_KIND_NOTES = {
    SIGN_INTERNAL: "Có giá trị trong nội bộ tập đoàn. KHÔNG có giá trị với bên ngoài.",
    SIGN_CERTIFIED: "Có giá trị pháp lý với bên ngoài, dựa trên chứng thư số.",
    SIGN_SCANNED: "Bản ghi nhận chữ ký trên giấy. Giá trị theo bản giấy gốc.",
}


class DocumentSignature(Base, AuditMixin):
    __tablename__ = "tab_signature"
    __table_args__ = (
        #  Trang chi tiết đọc chữ ký theo PHIÊN BẢN: chữ ký gắn với nội dung cụ
        #  thể, không gắn với văn bản chung chung.
        Index("ix_signature_version", "version_id", "signed_at"),
        Index("ix_signature_document", "document_id"),
    )

    document_id: Mapped[int] = mapped_column(BigInteger)
    #  Ký vào PHIÊN BẢN nào. Văn bản lên bản 2.0 thì chữ ký của bản 1.0 vẫn nằm
    #  lại đúng chỗ của nó — không được hiểu là đã ký bản mới.
    version_id: Mapped[int] = mapped_column(BigInteger)
    signer_employee_id: Mapped[int] = mapped_column(BigInteger)

    sign_kind: Mapped[int] = mapped_column(SmallInteger, default=SIGN_INTERNAL)
    signed_at: Mapped[datetime] = mapped_column(DateTime)

    #  KÝ VÀO NỘI DUNG NÀO. Chép từ `tab_document_version.content_sha256` lúc ký;
    #  nội dung đổi thì mã băm đổi, và chữ ký cũ lộ ra là ký cho bản khác.
    content_sha256: Mapped[str] = mapped_column(String(64), default="")

    #  Ba cột dưới chỉ có nghĩa với `sign_kind = 2`.
    cert_serial: Mapped[str] = mapped_column(String(100), default="")
    cert_issuer: Mapped[str] = mapped_column(String(200), default="")
    signature_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    #  Dấu vết kỹ thuật của lần ký — phần "đủ giá trị nội bộ" của J02 nằm ở đây:
    #  có người, có thời điểm, có địa chỉ, có mã băm nội dung.
    ip: Mapped[str] = mapped_column(String(45), default="")
    user_agent: Mapped[str] = mapped_column(String(300), default="")
