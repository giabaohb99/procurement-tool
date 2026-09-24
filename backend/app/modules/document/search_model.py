"""Chỉ mục TÌM KIẾM TOÀN VĂN của văn bản — DỮ LIỆU DẪN XUẤT (phase 07, duoc-CR-477).

Một dòng ↔ một văn bản (`document_id` PK). Xóa cả bảng rồi chạy
`python -m app.scripts.reindex_documents --all` là dựng lại y hệt —
`tab_document`/`tab_document_version`/`tab_file` mới là nguồn sự thật, bảng
này KHÔNG BAO GIỜ được coi là nguồn (xem `plan.md` mục "Luật phải giữ").

Ba cột `meta_text`/`body_text`/`file_text` lưu chữ ĐÃ GẬP DẤU + HẠ CHỮ THƯỜNG
(`app.core.text_fold.fold`) — độc lập collation MySQL (`utf8mb4_*` không tự
gập dấu tiếng Việt), và là ba cột thật sự được đánh FULLTEXT `WITH PARSER
ngram` (viết tay trong migration — `alembic --autogenerate` không sinh được
cú pháp `WITH PARSER`).

`file_text_raw` là NGOẠI LỆ so với ba cột trên: giữ nguyên chữ GỐC (có dấu,
hoa/thường) trích từ tệp đính kèm, dùng riêng để dựng đoạn trích đẹp mắt lúc
trả kết quả tìm. Meta và nội dung soạn thảo KHÔNG cần bản gốc song song —
dựng lại đoạn trích từ `tab_document`/`tab_document_version` lúc trả kết quả
là đủ rẻ (đã là bảng SQL thường, không tệp không mạng). File thì khác: byte
tệp nằm trên R2, trích lại nghĩa là tải mạng + phân tích PDF/docx — chấp nhận
được cho MỘT trang kết quả, không chấp nhận được nếu phải làm lại ở MỌI lần
tìm. Đây là quyết định thay cho phần "lưu thêm cột gốc nếu đo thấy chậm — quyết
ở bước đo" mà đặc tả phase để ngỏ (không có dữ liệu quy mô thật để đo).

`file_text_raw` LUÔN cùng độ dài ký tự với `file_text` theo từng đoạn ghép
(một ký tự gập ↔ đúng một ký tự gốc, xem `text_fold.fold_char`) để offset tìm
thấy trên bản gập dùng thẳng được trên bản gốc khi cắt đoạn trích.
"""
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Index, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class DocumentSearch(Base):
    __tablename__ = "tab_document_search"
    __table_args__ = (
        #  Bốn chỉ mục FULLTEXT `WITH PARSER ngram` — khai LẠI Ở ĐÂY (dựng
        #  bằng SQL thô trong migration, `alembic --autogenerate` không sinh
        #  được cú pháp `WITH PARSER`) để `--autogenerate` KHÔNG coi chúng là
        #  "vừa bị xóa khỏi model" ở mọi lần chạy sau — không khai thì mỗi lần
        #  rà lệch đều đề nghị DROP rồi CREATE lại bốn chỉ mục này, dù DB đang
        #  đúng. Bản thân bốn Index này KHÔNG được autogenerate DDL — bảng đã
        #  có sẵn từ migration `747c71718181`.
        Index("ft_document_search_all", "meta_text", "body_text", "file_text",
              mysql_prefix="FULLTEXT", mysql_with_parser="ngram"),
        Index("ft_document_search_meta", "meta_text",
              mysql_prefix="FULLTEXT", mysql_with_parser="ngram"),
        Index("ft_document_search_body", "body_text",
              mysql_prefix="FULLTEXT", mysql_with_parser="ngram"),
        Index("ft_document_search_file", "file_text",
              mysql_prefix="FULLTEXT", mysql_with_parser="ngram"),
    )

    #  ⚠️ `autoincrement=False` bắt buộc: đây là KHÓA CHÍNH nhưng KHÔNG tự
    #  sinh — nó CHÍNH LÀ `tab_document.id` (một-một), ứng dụng luôn gán tay
    #  (`DocumentSearch(document_id=document_id)`). Thiếu cờ này, SQLAlchemy
    #  mặc định bật `AUTO_INCREMENT` cho khóa chính số nguyên MỘT CỘT — vô hại
    #  về chức năng (MySQL vẫn nhận giá trị gán tay) nhưng sai ý nghĩa cột.
    document_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)

    meta_text: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default="")
    body_text: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default="")
    file_text: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default="")
    file_text_raw: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default="")

    #  `[{attachment_id, name, start, end}]` — `start`/`end` là offset TRONG
    #  `file_text`/`file_text_raw` (cùng thang đo cả hai), để biết một đoạn
    #  trích trong `file_text` thuộc về tệp nào lúc dựng nhãn "trúng trong:
    #  Tệp ‹tên tệp›".
    file_names: Mapped[list] = mapped_column(JSON, default=list)

    #  Băm DANH TÍNH bộ tệp đính kèm (id·sha256·size từng tệp) — TÁCH RIÊNG
    #  khỏi `source_hash` để `reindex()` biết KHÔNG cần trích lại chữ từ tệp
    #  (mạng + phân tích PDF/docx, đắt) khi chỉ có nội dung soạn thảo đổi.
    #  Không có cột này thì tự động lưu chạy theo nhịp gõ (mỗi vài giây một
    #  lần, `body_text` đổi ở HẦU HẾT các lần gọi) sẽ kéo theo trích lại TOÀN
    #  BỘ tệp đính kèm ở MỌI lần gõ — đúng chi phí mà cột này tồn tại để né.
    file_fingerprint: Mapped[str] = mapped_column(String(64), default="")

    #  Băm nguồn (meta + nội dung + chữ tệp cuối cùng) — `reindex()` bỏ qua,
    #  không ghi lại, nếu hash này không đổi so với dòng đang có.
    source_hash: Mapped[str] = mapped_column(String(64), default="")
    indexed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
