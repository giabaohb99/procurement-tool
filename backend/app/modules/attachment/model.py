from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class StoredFile(Base, AuditMixin):
    """FILE THẬT — 1 dòng = 1 file trên storage (R2/local). Tách khỏi liên kết để 1 file
    có thể gắn vào nhiều record, và quản lý file rác (không có link) dễ dàng."""

    __tablename__ = "tab_file"

    filename: Mapped[str] = mapped_column(String(255))
    file_key: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000), default="")
    content_type: Mapped[str] = mapped_column(String(100), default="")
    size: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Mã băm toàn vẹn, tính lúc tải lên (`van-thu` C06). Để người cầm một tệp
    #  ngoài hệ thống đối chiếu được nó có đúng tệp đã đính kèm hay không —
    #  cùng dung lượng cùng tên file vẫn có thể là hai nội dung khác nhau.
    #
    #  Tệp tải lên TRƯỚC khi có cột này để rỗng: tính lại phải tải toàn bộ
    #  object từ storage về, tốn kém mà không ai đang cần đối chiếu tệp cũ.
    sha256: Mapped[str] = mapped_column(String(64), default="")
    #  Bản thumbnail sinh lúc upload (core/images.py) — chỗ hiển thị đọc bản nhẹ,
    #  bấm xem lớn/tải về mới đụng bản gốc. Rỗng = không có (tệp không phải ảnh,
    #  ảnh nhỏ sẵn không đáng nén, hoặc tệp tải lên trước khi có tính năng này)
    #  → bên đọc fallback về `url`.
    thumb_key: Mapped[str] = mapped_column(String(500), default="", server_default="")
    thumb_url: Mapped[str] = mapped_column(String(1000), default="", server_default="")
    #  NGUỒN của byte tệp. Rỗng = tệp của chính ERP, `file_key` trỏ vào kho R2 của
    #  ERP, đọc thẳng bằng `core/storage.download_bytes`. Khác rỗng = tệp còn nằm ở
    #  hệ thống khác và `file_key` là khóa của KHO ĐÓ — gọi `download_bytes` lên nó
    #  thì R2 của ERP trả 404, tức người dùng nhận "mã sự cố" cho một tệp vẫn còn
    #  sống. Mọi đường đọc byte phải rẽ theo cột này trước (`core/legacy_files.py`).
    #  Giá trị đang dùng: `"datxe"` — tệp đính kèm nhập từ app đặt xe / duyệt dấu cũ.
    source: Mapped[str] = mapped_column(String(20), default="", server_default="")
    #  Khóa của tệp BÊN NGUỒN KIA (với `datxe` là khóa nhánh `files` của Firebase).
    #  Cùng `source` làm nên cặp nhận dạng để nạp lại không sinh bản trùng.
    external_id: Mapped[str] = mapped_column(String(64), default="", server_default="", index=True)


class FileLink(Base, AuditMixin):
    """LIÊN KẾT file ↔ record. Xóa link không nhất thiết xóa file (file có thể dùng chỗ khác)."""

    __tablename__ = "tab_file_link"

    file_id: Mapped[int] = mapped_column(BigInteger, index=True)
    entity: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, index=True)
    purchase_order_id: Mapped[int] = mapped_column(BigInteger, default=0)   # gom bộ chứng từ theo đơn
    doc_type: Mapped[str] = mapped_column(String(50), default="", index=True)  # loại chứng từ (cố định trong code)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # thứ tự hiển thị (ảnh SP); nhỏ = trước
