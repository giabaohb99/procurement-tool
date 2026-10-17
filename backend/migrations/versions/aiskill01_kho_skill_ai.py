"""kho skill AI - 5 bang tab_ai_skill* (bao-CR-621, K1 cua doc/erp/21)

Revision ID: aiskill01
Revises: grp14

Bo skill (tab_ai_skill_set) mang pham vi quan tri theo phap nhan + phong chu quan; skill + phien ban xuat ban (chi
them) + tep dinh kem dang chu; bang quyen DOC tab_ai_skill_access cung hinh dang tab_report_access (chu the, cam
thang, co han, thu hoi la danh dau) them target_kind / target_id / include_children. Model: app/modules/ai_skill.
Trang thai / muc bao mat luu SMALLINT (IntEnum o ai_skill/constants.py).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "aiskill01"
down_revision: Union[str, None] = "grp14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LONG_TEXT = sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql")


def _audit() -> list:
    return [
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def _soft_delete() -> list:
    return [
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    op.create_table(
        "tab_ai_skill_set",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(50), nullable=False, server_default=""),
        sa.Column("name", sa.String(150), nullable=False, server_default=""),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("owner_department_id", sa.BigInteger(), nullable=False, server_default="0"),
        # SkillSetStatus: 1 nhap · 2 dang dung · 3 luu tru
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        # SecurityLevel: 1 mo · 2 bao ve · 3 khoa
        sa.Column("security_level", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_audit(), *_soft_delete(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_ai_skill_set_code", "tab_ai_skill_set", ["code"])
    op.create_index("ix_tab_ai_skill_set_company_id", "tab_ai_skill_set", ["company_id"])
    op.create_index("ix_tab_ai_skill_set_owner_department_id", "tab_ai_skill_set", ["owner_department_id"])
    op.create_index("ix_tab_ai_skill_set_is_deleted", "tab_ai_skill_set", ["is_deleted"])

    op.create_table(
        "tab_ai_skill",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("skill_set_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("slug", sa.String(100), nullable=False, server_default=""),
        sa.Column("title", sa.String(200), nullable=False, server_default=""),
        sa.Column("summary", sa.String(500), nullable=False, server_default=""),
        # SkillStatus: 1 nhap · 2 dang dung · 3 luu tru
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("current_version_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("draft_body_md", LONG_TEXT, nullable=True),
        sa.Column("draft_updated_at", sa.DateTime(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_audit(), *_soft_delete(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_ai_skill_skill_set_id", "tab_ai_skill", ["skill_set_id"])
    op.create_index("ix_ai_skill_set_slug", "tab_ai_skill", ["skill_set_id", "slug"])
    op.create_index("ix_tab_ai_skill_is_deleted", "tab_ai_skill", ["is_deleted"])

    op.create_table(
        "tab_ai_skill_version",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("skill_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("title", sa.String(200), nullable=False, server_default=""),
        sa.Column("summary", sa.String(500), nullable=False, server_default=""),
        sa.Column("body_md", LONG_TEXT, nullable=True),
        sa.Column("change_note", sa.String(500), nullable=False, server_default=""),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("published_by", sa.BigInteger(), nullable=False, server_default="0"),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_skill_version_skill", "tab_ai_skill_version", ["skill_id", "version_no"])

    op.create_table(
        "tab_ai_skill_file",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("skill_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("path", sa.String(200), nullable=False, server_default=""),
        sa.Column("size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("content_text", LONG_TEXT, nullable=True),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_skill_file_skill", "tab_ai_skill_file", ["skill_id", "path"])

    op.create_table(
        "tab_ai_skill_access",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        # AccessTarget: 1 bo skill · 2 skill
        sa.Column("target_kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("target_id", sa.BigInteger(), nullable=False, server_default="0"),
        # chu the: 1 nguoi · 2 phong ban · 3 phap nhan · 4 vai tro · 5 chuc vu · 6 cap bac
        sa.Column("subject_kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("subject_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("include_children", sa.Boolean(), nullable=False, server_default="1"),
        # 1 cho phep · 2 cam (cam thang)
        sa.Column("effect", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("reason", sa.String(500), nullable=False, server_default=""),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("revoke_reason", sa.String(500), nullable=False, server_default=""),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_skill_access_target", "tab_ai_skill_access", ["target_kind", "target_id"])
    op.create_index("ix_ai_skill_access_subject", "tab_ai_skill_access", ["subject_kind", "subject_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_skill_access_subject", table_name="tab_ai_skill_access")
    op.drop_index("ix_ai_skill_access_target", table_name="tab_ai_skill_access")
    op.drop_table("tab_ai_skill_access")
    op.drop_index("ix_ai_skill_file_skill", table_name="tab_ai_skill_file")
    op.drop_table("tab_ai_skill_file")
    op.drop_index("ix_ai_skill_version_skill", table_name="tab_ai_skill_version")
    op.drop_table("tab_ai_skill_version")
    for name in ("ix_tab_ai_skill_is_deleted", "ix_ai_skill_set_slug", "ix_tab_ai_skill_skill_set_id"):
        op.drop_index(name, table_name="tab_ai_skill")
    op.drop_table("tab_ai_skill")
    for name in ("ix_tab_ai_skill_set_is_deleted", "ix_tab_ai_skill_set_owner_department_id",
                 "ix_tab_ai_skill_set_company_id", "ix_tab_ai_skill_set_code"):
        op.drop_index(name, table_name="tab_ai_skill_set")
    op.drop_table("tab_ai_skill_set")
