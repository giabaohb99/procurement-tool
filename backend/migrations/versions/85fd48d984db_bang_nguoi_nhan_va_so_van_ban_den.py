"""bang nguoi nhan va so van ban den

Dựng trước hai bảng của phase sau theo `02` mục 5 (Phase 1 · Danh mục và số
hiệu): `tab_document_recipient` (J06 xác nhận đã đọc) và `tab_incoming_register`
(S02 sổ văn bản đến). **Chỉ bảng, chưa màn hình** — không service, không router.

Kèm các cột mà `04` mục 9.1 và 9.3 gom về `tab_document` khi bỏ hai bảng
`tab_outgoing_register` và `tab_legal_reference`.

Bản autogenerate còn bắt kèm vài `alter_column` của `tab_comment_*` và
`tab_ticket*` — đó là chênh lệch có sẵn giữa model và DB, không phải do thay đổi
này sinh ra, nên đã gỡ khỏi đây. Muốn vá thì làm một migration riêng.

Revision ID: 85fd48d984db
Revises: e7c4a18f2d60
Create Date: 2026-08-17 01:57:51.319492
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "85fd48d984db"
down_revision: Union[str, Sequence[str], None] = "e7c4a18f2d60"
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
    # ── J06 · nơi nhận và xác nhận đã đọc ────────────────────────────────────
    op.create_table(
        "tab_document_recipient",
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        #  Gắn vào PHIÊN BẢN: quy chế lên 2.0 thì mọi người phải xác nhận lại.
        sa.Column("version_id", sa.BigInteger(), nullable=False),
        sa.Column("recipient_kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("recipient_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("external_party_id", sa.BigInteger(), nullable=True),
        #  Tập hợp kênh cộng dồn: 1 chuông · 2 thư · 4 bản giấy · 8 gửi ra ngoài.
        sa.Column("channels", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("send_status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("required", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=False, server_default=""),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("id"),
        #  Một người nhận một dòng trên mỗi phiên bản — điều kiện để việc đếm
        #  "bao nhiêu người đã đọc" không đếm trùng.
        sa.UniqueConstraint(
            "version_id", "recipient_kind", "recipient_id", name="uq_document_recipient",
        ),
    )
    op.create_index(
        "ix_document_recipient_doc", "tab_document_recipient",
        ["document_id", "version_id"],
    )
    op.create_index(
        "ix_document_recipient_person", "tab_document_recipient",
        ["recipient_kind", "recipient_id", "confirmed_at"],
    )

    # ── S02 · sổ văn bản đến ─────────────────────────────────────────────────
    op.create_table(
        "tab_incoming_register",
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("seq_no", sa.Integer(), nullable=False),
        sa.Column("received_date", sa.Date(), nullable=True),
        sa.Column("sender_party_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_doc_number", sa.String(length=100), nullable=False,
                  server_default=""),
        sa.Column("sender_doc_date", sa.Date(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("file_id", sa.BigInteger(), nullable=True),
        sa.Column("assigned_employee_id", sa.BigInteger(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("handled_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("note", sa.Text(), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("id"),
        #  Số đến dùng khóa `in:{mã pháp nhân}:{năm}` — một sổ cho cả pháp nhân,
        #  nên bộ ba này duy nhất thật (khác sổ đi, xem `04` mục 9.1).
        sa.UniqueConstraint("company_id", "year", "seq_no", name="uq_incoming_seq"),
    )
    op.create_index(
        "ix_incoming_assignee", "tab_incoming_register",
        ["assigned_employee_id", "status", "due_date"],
    )

    # ── Cột gom về tab_document ──────────────────────────────────────────────
    op.add_column("tab_document", sa.Column("issued_at", sa.DateTime(), nullable=True))
    op.add_column("tab_document", sa.Column("next_review_date", sa.Date(), nullable=True))
    #  Giao việc cho pháp nhân nhận bản clone (P4).
    op.add_column(
        "tab_document",
        sa.Column("clone_assignee_employee_id", sa.BigInteger(), nullable=True),
    )
    op.add_column("tab_document", sa.Column("clone_due_date", sa.Date(), nullable=True))
    op.add_column("tab_document", sa.Column("clone_handled_at", sa.DateTime(), nullable=True))
    #  Ba cột của sổ văn bản đi (`04` mục 9.1) — sổ đi là truy vấn, không phải bảng.
    op.add_column(
        "tab_document",
        sa.Column("recipient_summary", sa.String(length=500), nullable=False,
                  server_default=""),
    )
    op.add_column("tab_document", sa.Column("copies", sa.SmallInteger(), nullable=True))
    op.add_column(
        "tab_document",
        sa.Column("register_note", sa.String(length=500), nullable=False,
                  server_default=""),
    )


def downgrade() -> None:
    op.drop_column("tab_document", "register_note")
    op.drop_column("tab_document", "copies")
    op.drop_column("tab_document", "recipient_summary")
    op.drop_column("tab_document", "clone_handled_at")
    op.drop_column("tab_document", "clone_due_date")
    op.drop_column("tab_document", "clone_assignee_employee_id")
    op.drop_column("tab_document", "next_review_date")
    op.drop_column("tab_document", "issued_at")
    op.drop_index("ix_incoming_assignee", table_name="tab_incoming_register")
    op.drop_table("tab_incoming_register")
    op.drop_index("ix_document_recipient_person", table_name="tab_document_recipient")
    op.drop_index("ix_document_recipient_doc", table_name="tab_document_recipient")
    op.drop_table("tab_document_recipient")
