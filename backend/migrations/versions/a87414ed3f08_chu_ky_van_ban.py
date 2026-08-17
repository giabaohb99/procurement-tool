"""chu ky van ban

J02/J03 — bản ghi chữ ký. Bảng **chỉ ghi thêm**, không sửa, không xóa: một chữ
ký gỡ được thì nó không còn là chữ ký.

`sign_kind` là cột quan trọng nhất — ba loại có giá trị pháp lý khác hẳn nhau,
và người dùng nhầm ký nội bộ với ký số là gửi ra ngoài một văn bản tưởng có giá
trị pháp lý mà thật ra không.

Đã gỡ phần drift `tab_comment_*` / `tab_ticket*` mà autogenerate bắt kèm.

Revision ID: a87414ed3f08
Create Date: 2026-08-17 04:12:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a87414ed3f08"
down_revision: Union[str, None] = 'bf27607f7549'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_signature",
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        #  Ký vào PHIÊN BẢN nào — văn bản lên bản 2.0 thì chữ ký của bản 1.0 nằm
        #  lại đúng chỗ của nó, không được hiểu là đã ký bản mới.
        sa.Column("version_id", sa.BigInteger(), nullable=False),
        sa.Column("signer_employee_id", sa.BigInteger(), nullable=False),
        # 1 ký điện tử nội bộ · 2 ký số có chứng thư · 3 ký giấy đã quét
        sa.Column("sign_kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("signed_at", sa.DateTime(), nullable=False),
        #  Ký vào nội dung nào. Chép lúc ký, không trỏ sang bảng phiên bản: nội
        #  dung đổi thì chữ ký phải LỘ RA là đang lệch, không lặng lẽ đổi theo.
        sa.Column("content_sha256", sa.String(length=64), nullable=False,
                  server_default=""),
        sa.Column("cert_serial", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("cert_issuer", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("signature_blob", sa.LargeBinary(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=False, server_default=""),
        sa.Column("user_agent", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signature_version", "tab_signature", ["version_id", "signed_at"])
    op.create_index("ix_signature_document", "tab_signature", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_signature_document", table_name="tab_signature")
    op.drop_index("ix_signature_version", table_name="tab_signature")
    op.drop_table("tab_signature")
