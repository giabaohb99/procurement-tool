"""tab_seal_request: status String->SMALLINT (R2) + them cot copies

Revision ID: seal1status01
Revises: dx3self01
Create Date: 2026-09-05

Duyet dau (PHA 0): dua `status` ve SMALLINT + hang so SEAL_* cho khop khuon Dat xe.
Bang `tab_seal_request` chua tung co controller nen chua co du lieu; van map phong khi
co ban ghi le. Viet tay de khoi cuon theo drift autogenerate.
"""
from alembic import op
import sqlalchemy as sa

revision = "seal1status01"
down_revision = "dx3self01"
branch_labels = None
depends_on = None


def upgrade():
    #  Map cac gia tri chuoi cu -> so (neu lo co ban ghi); con lai ve 1 (Nhap).
    op.execute("UPDATE tab_seal_request SET status='1' WHERE status IN ('draft','')")
    op.execute("UPDATE tab_seal_request SET status='2' WHERE status IN ('submitted','pending')")
    op.execute("UPDATE tab_seal_request SET status='3' WHERE status='approved'")
    op.execute("UPDATE tab_seal_request SET status='4' WHERE status IN ('completed','done')")
    op.execute("UPDATE tab_seal_request SET status='5' WHERE status='rejected'")
    op.execute("UPDATE tab_seal_request SET status='6' WHERE status='cancelled'")
    op.execute("UPDATE tab_seal_request SET status='7' WHERE status='returned'")
    op.execute("UPDATE tab_seal_request SET status='1' WHERE status NOT REGEXP '^[0-9]+$'")
    op.alter_column("tab_seal_request", "status",
                    existing_type=sa.String(length=30),
                    type_=sa.SmallInteger(),
                    existing_nullable=False,
                    server_default="1")
    op.add_column("tab_seal_request",
                  sa.Column("copies", sa.SmallInteger(), nullable=False, server_default="1"))


def downgrade():
    op.drop_column("tab_seal_request", "copies")
    op.alter_column("tab_seal_request", "status",
                    existing_type=sa.SmallInteger(),
                    type_=sa.String(length=30),
                    existing_nullable=False,
                    server_default="draft")
