"""Them cot legacy_id cho 7 bang dong bo voi app dat xe cu

Revision ID: b7c2e4a91f30
Revises: a3e8c1f6d924
Create Date: 2026-09-16

Cot `legacy_id` giu khoa day Firebase cua ban ghi doi ung ben app dat xe cu.
Rong = ban ghi do ERP tu sinh. Chi danh index, KHONG dat UNIQUE — xem giai
thich o `LegacyIdMixin` trong app/core/base_model.py.
"""

from alembic import op
import sqlalchemy as sa

revision = "b7c2e4a91f30"
down_revision = "a3e8c1f6d924"
branch_labels = None
depends_on = None


#  (ten bang, ten index) — dat ten index ngan de khong cham gioi han 64 ky tu.
TABLES = [
    ("tab_company", "ix_company_legacy_id"),
    ("tab_department", "ix_department_legacy_id"),
    ("tab_employee", "ix_employee_legacy_id"),
    ("tab_vehicle", "ix_vehicle_legacy_id"),
    ("tab_driver", "ix_driver_legacy_id"),
    ("tab_vehicle_booking", "ix_vbooking_legacy_id"),
    ("tab_seal_request", "ix_seal_request_legacy_id"),
]


def upgrade() -> None:
    for table, index_name in TABLES:
        op.add_column(
            table,
            sa.Column(
                "legacy_id",
                sa.String(length=64),
                nullable=False,
                server_default="",
            ),
        )
        op.create_index(index_name, table, ["legacy_id"])


def downgrade() -> None:
    for table, index_name in reversed(TABLES):
        op.drop_index(index_name, table_name=table)
        op.drop_column(table, "legacy_id")
