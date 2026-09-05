"""tab_email_exclusion: thêm cột `event` (loại trừ theo từng mẫu email)

Revision ID: dxmail03
Revises: dxmail02
Create Date: 2026-09-04

`event` = "" nghĩa là áp cho MỌI mẫu; hoặc mã event của một mẫu cụ thể. Khóa
duy nhất đổi thành (scope, ref_id, event). Viết tay.
"""
from alembic import op
import sqlalchemy as sa

revision = "dxmail03"
down_revision = "dxmail02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tab_email_exclusion",
                  sa.Column("event", sa.String(length=50), nullable=False, server_default=""))
    op.create_index("ix_tab_email_exclusion_event", "tab_email_exclusion", ["event"])
    op.drop_constraint("uq_email_exclusion_scope_ref", "tab_email_exclusion", type_="unique")
    op.create_unique_constraint(
        "uq_email_exclusion_scope_ref_event", "tab_email_exclusion", ["scope", "ref_id", "event"])


def downgrade():
    op.drop_constraint("uq_email_exclusion_scope_ref_event", "tab_email_exclusion", type_="unique")
    op.create_unique_constraint(
        "uq_email_exclusion_scope_ref", "tab_email_exclusion", ["scope", "ref_id"])
    op.drop_index("ix_tab_email_exclusion_event", table_name="tab_email_exclusion")
    op.drop_column("tab_email_exclusion", "event")
