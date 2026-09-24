"""duoc_cr477_tim_kiem_toan_van

Chỉ mục TÌM KIẾM TOÀN VĂN văn bản (phase 07, duoc-CR-477) — `tab_document_search`.
Thiết kế: `frontend-v2/plans/260923-1000-van-ban-thu-muc-nguoi-duyet/phase-07-tim-kiem-toan-van.md`.

Viết TAY, không autogenerate: `alembic --autogenerate` không sinh được cú pháp
`FULLTEXT ... WITH PARSER ngram` (SQLAlchemy/Alembic không có API cho parser
FULLTEXT), nên bốn chỉ mục FULLTEXT phải thêm bằng `op.execute()` sau khi tạo
bảng bằng DDL thô.

Bốn chỉ mục FULLTEXT: một GỘP cả ba cột (dùng cho câu "trúng ở đâu cũng được"),
ba RIÊNG từng cột (dùng để tính điểm theo trọng số 3×meta + 2×body + 1×file —
xem `document/search_service.py`). `WITH PARSER ngram` (n=2, có sẵn trong MySQL
8, không cần cài plugin) để không rơi mất từ khóa 2 chữ cái tiếng Việt viết tắt
("hd", "qd", "le"...) — parser mặc định của MySQL bỏ mọi từ dưới 4 ký tự (hoặc
3 tùy cấu hình `innodb_ft_min_token_size`).

Revision ID: 747c71718181
Revises: 1c035ad17323
Create Date: 2026-09-23 17:40:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '747c71718181'
down_revision: Union[str, None] = '1c035ad17323'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FULLTEXT_INDEXES = (
    ("ft_document_search_all", "meta_text, body_text, file_text"),
    ("ft_document_search_meta", "meta_text"),
    ("ft_document_search_body", "body_text"),
    ("ft_document_search_file", "file_text"),
)


def upgrade() -> None:
    from sqlalchemy.dialects import mysql

    op.create_table(
        "tab_document_search",
        #  KHÓA CHÍNH nhưng KHÔNG tự sinh — chính là `tab_document.id` (một-một).
        sa.Column("document_id", sa.BigInteger(), autoincrement=False, nullable=False),
        #  Ba cột GẬP DẤU + HẠ CHỮ THƯỜNG (`core/text_fold.fold`) — nội dung
        #  thật sự được đánh FULLTEXT bên dưới, độc lập collation.
        sa.Column("meta_text", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("body_text", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("file_text", mysql.MEDIUMTEXT(), nullable=False),
        #  Bản GỐC (có dấu) của `file_text`, dùng riêng để dựng đoạn trích —
        #  xem docstring đầu `document/search_model.py`.
        sa.Column("file_text_raw", mysql.MEDIUMTEXT(), nullable=False),
        #  `[{attachment_id, name, start, end}]` — ứng dụng LUÔN gán `[]` tối
        #  thiểu (`DocumentSearch.file_names` mặc định `list`, không bao giờ
        #  `None`), nên khai NOT NULL khớp đúng model, tránh drift giả khi
        #  chạy `alembic --autogenerate` (kiểu Mapped[list] không Optional).
        sa.Column("file_names", sa.JSON(), nullable=False),
        #  Băm danh tính bộ tệp đính kèm — tách khỏi `source_hash` để tự động
        #  lưu (đổi `body_text` ở mọi lần gọi) không kéo theo trích lại tệp.
        sa.Column("file_fingerprint", sa.String(64), nullable=False, server_default=""),
        sa.Column("source_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("indexed_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.PrimaryKeyConstraint("document_id"),
    )
    for name, cols in _FULLTEXT_INDEXES:
        op.execute(
            f"ALTER TABLE tab_document_search "
            f"ADD FULLTEXT INDEX {name} ({cols}) WITH PARSER ngram"
        )


def downgrade() -> None:
    op.drop_table("tab_document_search")
