"""van ban va phien ban van ban (M6) + ma so hieu cho phap nhan/phong ban (M2)

Revision ID: 32f20b5057fc
Revises: 7c31d0a94ef5
Create Date: 2026-08-14 08:29:18.661067

Viết TAY chứ không dùng bản autogenerate. Lý do: một số máy dev còn sót ba bảng
`tab_document*` của bản dựng thử theo trục sổ đến/đi (migration đó đã bị revert,
tệp không còn trong git nhưng bảng vẫn nằm trong DB). Autogenerate nhìn thấy
chúng rồi sinh ra một chuỗi ALTER để nắn bảng cũ thành bảng mới — vừa không chạy
được trên máy sạch, vừa kéo theo cả đống thay đổi không liên quan.

Ở đây làm thẳng: xóa bảng cũ nếu có rồi tạo lại theo trục **loại văn bản × pháp
nhân ban hành × phiên bản**. An toàn trên cả hai loại máy vì dùng
`DROP TABLE IF EXISTS`, và ba bảng đó chưa từng lên dev/prod.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = '32f20b5057fc'
down_revision: Union[str, None] = '7c31d0a94ef5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit() -> list:
    """Bốn cột chuẩn + khóa chính. Là HÀM vì mỗi `create_table` phải nhận một bộ
    đối tượng Column RIÊNG — dùng lại cùng một danh sách cho hai bảng thì
    SQLAlchemy báo cột đã thuộc về bảng khác."""
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    # ── M2: mã đi vào số hiệu văn bản ────────────────────────────────────────
    # Khác `code` (mã hiển thị, chứa được dấu và khoảng trắng) — xem
    # `Company.issue_code`. KHÔNG đặt UNIQUE: 13 pháp nhân chưa khai mã thì 13
    # dòng cùng rỗng, UNIQUE chặn ngay lúc chạy migration.
    op.add_column("tab_company", sa.Column("issue_code", sa.String(20), nullable=False,
                                           server_default=""))
    op.add_column("tab_company", sa.Column("short_name", sa.String(100), nullable=False,
                                           server_default=""))
    op.add_column("tab_company", sa.Column("level", sa.SmallInteger(), nullable=False,
                                           server_default="2"))
    op.add_column("tab_department", sa.Column("issue_code", sa.String(20), nullable=False,
                                              server_default=""))
    op.add_column("tab_department", sa.Column("kind", sa.SmallInteger(), nullable=False,
                                              server_default="1"))
    op.create_index("ix_tab_company_issue_code", "tab_company", ["issue_code"])

    # ── Dọn ba bảng của bản dựng thử theo trục sổ (xem chú thích đầu tệp) ────
    for table in ("tab_document_assignee", "tab_document_version", "tab_document"):
        op.execute(f"DROP TABLE IF EXISTS {table}")

    # ── M6: văn bản ──────────────────────────────────────────────────────────
    op.create_table(
        "tab_document",
        sa.Column("origin", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("doc_code", sa.String(50), nullable=True),
        sa.Column("issue_number", sa.String(100), nullable=False, server_default=""),
        sa.Column("seq_no", sa.Integer(), nullable=True),
        sa.Column("issue_year", sa.SmallInteger(), nullable=True),
        sa.Column("legacy_code", sa.String(100), nullable=False, server_default=""),

        sa.Column("doc_type_id", sa.BigInteger(), nullable=True),
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        sa.Column("department_id", sa.BigInteger(), nullable=True),
        sa.Column("owner_employee_id", sa.BigInteger(), nullable=True),
        sa.Column("drafter_employee_id", sa.BigInteger(), nullable=True),
        sa.Column("signer_employee_id", sa.BigInteger(), nullable=True),

        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("keywords", sa.String(500), nullable=False, server_default=""),
        sa.Column("secrecy_level", sa.SmallInteger(), nullable=False, server_default="2"),
        sa.Column("urgency", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expire_date", sa.Date(), nullable=True),
        sa.Column("current_version_id", sa.BigInteger(), nullable=True),

        sa.Column("document_request_id", sa.BigInteger(), nullable=True),

        # Bảy cột clone của P4 — khai sẵn, bản 1 không màn hình nào chạm tới.
        sa.Column("source_document_id", sa.BigInteger(), nullable=True),
        sa.Column("clone_status", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("clone_source_version_id", sa.BigInteger(), nullable=True),
        sa.Column("apply_mode", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("cloned_at", sa.Date(), nullable=True),
        sa.Column("cloned_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("clone_note", sa.String(500), nullable=False, server_default=""),

        sa.Column("legal_issuer", sa.String(300), nullable=False, server_default=""),
        sa.Column("legal_url", sa.String(1000), nullable=False, server_default=""),

        # Sổ đến/đi (nhóm S) — chờ câu A1, bản 1 luôn rỗng.
        sa.Column("book_id", sa.BigInteger(), nullable=True),
        sa.Column("book_seq_no", sa.Integer(), nullable=True),
        sa.Column("book_year", sa.SmallInteger(), nullable=True),

        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        # Văn bản nội bộ bắt buộc có loại + pháp nhân + người chịu trách nhiệm.
        sa.CheckConstraint(
            "origin <> 1 OR (doc_type_id IS NOT NULL AND company_id IS NOT NULL"
            " AND owner_employee_id IS NOT NULL)",
            name="ck_document_internal_required"),
        sa.UniqueConstraint("doc_code", name="uq_document_doc_code"),
        # Lớp chặn trùng số THỨ HAI, sau khóa dòng ở `next_number()`.
        sa.UniqueConstraint("company_id", "issue_year", "doc_type_id", "seq_no",
                            name="uq_document_issue_seq"),
        sa.UniqueConstraint("source_document_id", "company_id", name="uq_document_clone"),
    )
    op.create_index("ix_document_list", "tab_document",
                    ["origin", "company_id", "doc_type_id", "status"])
    op.create_index("ix_document_effective", "tab_document",
                    ["origin", "status", "effective_date"])
    op.create_index("ix_document_issue_number", "tab_document", ["issue_number"])
    op.create_index("ix_document_legacy_code", "tab_document", ["legacy_code"])
    op.create_index("ix_document_clone", "tab_document", ["source_document_id", "clone_status"])

    # ── M6: phiên bản ────────────────────────────────────────────────────────
    op.create_table(
        "tab_document_version",
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("major", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("minor", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="0"),
        # Cột SINH: bằng `document_id` khi bản còn mở, NULL khi đã chốt. UNIQUE
        # trên cột này = mỗi văn bản nhiều nhất một bản đang mở. Đây là chốt
        # chặn THẬT cho việc hai người cùng bấm "mở phiên bản mới" — câu kiểm
        # trong mã thì cả hai đều thấy trống rồi cùng ghi.
        sa.Column("open_slot", sa.BigInteger(),
                  sa.Computed("CASE WHEN status IN (1, 2) THEN document_id ELSE NULL END",
                              persisted=False), nullable=True),
        sa.Column("content_html", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("change_kind", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("change_summary", sa.String(500), nullable=False, server_default=""),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("requires_reconfirm", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("prev_version_id", sa.BigInteger(), nullable=True),
        sa.Column("created_from_request_id", sa.BigInteger(), nullable=True),
        sa.Column("file_id", sa.BigInteger(), nullable=True),
        sa.Column("pdf_file_id", sa.BigInteger(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.BigInteger(), nullable=False, server_default="0"),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("open_slot", name="uq_one_open_version"),
        sa.UniqueConstraint("document_id", "major", "minor", name="uq_version_no"),
    )
    op.create_index("ix_version_document", "tab_document_version",
                    ["document_id", "major", "minor"])

    # ── M6: yêu cầu văn bản — TẠO RỖNG, không service, không router ──────────
    # Bước xin phép đã cắt khỏi bản 1 (quyết định 7 của plan). Tạo bảng bây giờ
    # để lúc bật lại không phải thêm bảng vào một hệ đang chạy.
    op.create_table(
        "tab_document_request",
        sa.Column("kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("target_document_id", sa.BigInteger(), nullable=True),
        sa.Column("doc_type_id", sa.BigInteger(), nullable=True),
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        sa.Column("department_id", sa.BigInteger(), nullable=True),
        sa.Column("requester_employee_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(500), nullable=False, server_default=""),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expected_date", sa.Date(), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("approved_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("approved_at", sa.Date(), nullable=True),
        sa.Column("reject_reason", sa.Text(), nullable=False),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("tab_document_request")
    op.drop_table("tab_document_version")
    op.drop_table("tab_document")
    op.drop_index("ix_tab_company_issue_code", table_name="tab_company")
    op.drop_column("tab_department", "kind")
    op.drop_column("tab_department", "issue_code")
    op.drop_column("tab_company", "level")
    op.drop_column("tab_company", "short_name")
    op.drop_column("tab_company", "issue_code")
