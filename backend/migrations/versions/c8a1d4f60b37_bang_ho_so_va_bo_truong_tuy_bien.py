"""Bảng HỒ SƠ (tab_dossier) + bộ trường tùy biến của loại hồ sơ

Phân hệ Hồ sơ, 16/09/2026. Hai việc:

1. `tab_dossier_type.field_schema` (JSON) — mỗi loại hồ sơ tự khai bộ ô nhập
   riêng, màn lập hồ sơ dựng biểu mẫu theo loại đang chọn.
2. `tab_dossier` — bảng hồ sơ, phần khung là cột thật, phần riêng của từng loại
   nằm trong `extra_fields` (JSON).

⚠️ **VIẾT TAY, cố ý không dùng `--autogenerate`.** Bản autogenerate trên nhánh
này lôi theo hơn năm mươi thay đổi KHÔNG liên quan (thêm/bớt chỉ mục, đổi NOT
NULL ở `tab_survey_request_*`, `tab_ticket`, `tab_vehicle`…) — chênh lệch có sẵn
giữa model và DB, tích lại từ các đợt trước. Chạy nguyên bản đó là sửa lặng lẽ
cấu trúc của bảy phân hệ khác trong một migration mang tên «hồ sơ». Ai cần dọn
mớ chênh lệch ấy thì làm thành một đợt riêng, có người rà từng dòng.

Revision ID: c8a1d4f60b37
Revises: e4b7bc674d61
Create Date: 2026-09-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8a1d4f60b37"
down_revision: Union[str, None] = "e4b7bc674d61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    cols_type = [c['name'] for c in inspector.get_columns("tab_dossier_type")]
    if "field_schema" not in cols_type:
        op.add_column("tab_dossier_type", sa.Column("field_schema", sa.JSON(), nullable=True))

    tables = inspector.get_table_names()
    if "tab_dossier" not in tables:
        op.create_table(
            "tab_dossier",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("code", sa.String(length=30), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("dossier_type_id", sa.BigInteger(), nullable=False),
            sa.Column("dossier_type_name", sa.String(length=100), nullable=False,
                      server_default=""),
            sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
            sa.Column("issued_date", sa.Date(), nullable=True),
            sa.Column("expiry_date", sa.Date(), nullable=True),
            sa.Column("owner_employee_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("storage_location", sa.String(length=200), nullable=False,
                      server_default=""),
            sa.Column("note", sa.String(length=1000), nullable=False, server_default=""),
            sa.Column("extra_fields", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code", name="uq_tab_dossier_code"),
        )
        op.create_index("ix_tab_dossier_dossier_type_id", "tab_dossier", ["dossier_type_id"])
        op.create_index("ix_tab_dossier_status", "tab_dossier", ["status"])
        op.create_index("ix_tab_dossier_expiry_date", "tab_dossier", ["expiry_date"])
        op.create_index("ix_tab_dossier_owner_employee_id", "tab_dossier", ["owner_employee_id"])
        op.create_index("ix_tab_dossier_department_id", "tab_dossier", ["department_id"])
        op.create_index("ix_tab_dossier_company_id", "tab_dossier", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_tab_dossier_company_id", table_name="tab_dossier")
    op.drop_index("ix_tab_dossier_department_id", table_name="tab_dossier")
    op.drop_index("ix_tab_dossier_owner_employee_id", table_name="tab_dossier")
    op.drop_index("ix_tab_dossier_expiry_date", table_name="tab_dossier")
    op.drop_index("ix_tab_dossier_status", table_name="tab_dossier")
    op.drop_index("ix_tab_dossier_dossier_type_id", table_name="tab_dossier")
    op.drop_table("tab_dossier")
    op.drop_column("tab_dossier_type", "field_schema")
