"""quy tac danh so van ban

Revision ID: e7c4a18f2d60
Revises: c4e8a1d7b2f9
Create Date: 2026-08-15 18:20:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7c4a18f2d60"
down_revision: Union[str, Sequence[str], None] = "c4e8a1d7b2f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    op.drop_constraint("uq_document_issue_seq", "tab_document", type_="unique")
    op.add_column(
        "tab_document",
        sa.Column("numbering_rule_id", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_unique_constraint(
        "uq_document_issue_seq",
        "tab_document",
        ["company_id", "issue_year", "doc_type_id", "numbering_rule_id", "seq_no"],
    )

    op.create_table(
        "tab_document_numbering_rule",
        sa.Column("direction", sa.SmallInteger(), nullable=False),
        sa.Column("pattern", sa.String(length=200), nullable=False),
        sa.Column("start_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("reset_yearly", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("allow_manual", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("doc_type_mode", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("book_mode", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_numbering_rule_direction",
        "tab_document_numbering_rule",
        ["direction", "is_active", "priority"],
    )

    op.create_table(
        "tab_document_numbering_rule_doc_type",
        sa.Column("rule_id", sa.BigInteger(), nullable=False),
        sa.Column("doc_type_id", sa.BigInteger(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["rule_id"], ["tab_document_numbering_rule.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["doc_type_id"], ["tab_doc_type.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_id", "doc_type_id", name="uq_numbering_rule_doc_type"),
    )
    op.create_index(
        "ix_tab_document_numbering_rule_doc_type_rule_id",
        "tab_document_numbering_rule_doc_type", ["rule_id"],
    )
    op.create_index(
        "ix_tab_document_numbering_rule_doc_type_doc_type_id",
        "tab_document_numbering_rule_doc_type", ["doc_type_id"],
    )

    op.create_table(
        "tab_document_numbering_rule_book",
        sa.Column("rule_id", sa.BigInteger(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["rule_id"], ["tab_document_numbering_rule.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["book_id"], ["tab_document_book.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_id", "book_id", name="uq_numbering_rule_book"),
    )
    op.create_index(
        "ix_tab_document_numbering_rule_book_rule_id",
        "tab_document_numbering_rule_book", ["rule_id"],
    )
    op.create_index(
        "ix_tab_document_numbering_rule_book_book_id",
        "tab_document_numbering_rule_book", ["book_id"],
    )


def downgrade() -> None:
    op.drop_table("tab_document_numbering_rule_book")
    op.drop_table("tab_document_numbering_rule_doc_type")
    op.drop_table("tab_document_numbering_rule")
    op.drop_constraint("uq_document_issue_seq", "tab_document", type_="unique")
    op.drop_column("tab_document", "numbering_rule_id")
    op.create_unique_constraint(
        "uq_document_issue_seq",
        "tab_document",
        ["company_id", "issue_year", "doc_type_id", "seq_no"],
    )
