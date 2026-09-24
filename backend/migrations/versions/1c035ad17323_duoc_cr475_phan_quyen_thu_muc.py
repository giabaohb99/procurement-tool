"""duoc_cr475_phan_quyen_thu_muc

Quyền TRÊN TỪNG THƯ MỤC (phase 04, duoc-CR-475) — `tab_doc_folder_access`.
Thiết kế: `frontend-v2/plans/260923-1000-van-ban-thu-muc-nguoi-duyet/phase-04-phan-quyen-thu-muc.md`.

Cùng hình dạng với `tab_document_access` (migration `a41c7d5e9b02`) — bốn chủ
thể (người/phòng ban/pháp nhân/vai trò), cấm thắng cho phép, thu hồi là đánh
dấu, có hạn hiệu lực — khác đúng MỘT cột: `level` (`FolderAccessLevel`: 0 Riêng
tư · 1 Xem · 2 Đóng góp · 3 Quản lý) thay cho ba cờ `can_read/write/delete`,
vì quyền thư mục có BA MỨC chồng lên nhau chứ không phải ba hành động độc lập.

Không cột nào trên `tab_doc_folder` cần đổi ở migration này — `default_access`
đã có sẵn từ phase 03 (`e4a1c9d572b6`).

Revision ID: 1c035ad17323
Revises: e4a1c9d572b6
Create Date: 2026-09-23 09:46:18.696791
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c035ad17323'
down_revision: Union[str, None] = 'e4a1c9d572b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_doc_folder_access",
        sa.Column("folder_id", sa.BigInteger(), nullable=False),
        # 1 người (id NHÂN SỰ) · 2 phòng ban · 3 pháp nhân · 4 vai trò.
        sa.Column("subject_kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("subject_id", sa.BigInteger(), nullable=False),
        # 1 cho phép · 2 cấm. CẤM thắng CHO PHÉP và thắng cả mức nền theo pháp nhân.
        sa.Column("effect", sa.SmallInteger(), nullable=False, server_default="1"),
        # 0 Riêng tư · 1 Xem · 2 Đóng góp · 3 Quản lý — chỉ có nghĩa với dòng CHO PHÉP.
        sa.Column("level", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("valid_from", sa.Date(), nullable=True),
        # Trống = không hạn.
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("reason", sa.String(500), nullable=False, server_default=""),
        # Thu hồi = ĐÁNH DẤU, dòng ở lại bảng (G19, G20 — cùng luật với văn bản).
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("revoke_reason", sa.String(500), nullable=False, server_default=""),

        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Hai chiều tra: "thư mục này đang chia cho ai" (gộp cả kế thừa, quét theo
    # `path` ở tầng ứng dụng) và "người này được thấy thêm những thư mục nào"
    # — câu thứ hai chạy trên MỌI lần dựng cây (`folder_access_service.effective_levels`).
    op.create_index("ix_doc_folder_access_folder", "tab_doc_folder_access",
                    ["folder_id", "effect"])
    op.create_index("ix_doc_folder_access_subject", "tab_doc_folder_access",
                    ["subject_kind", "subject_id"])


def downgrade() -> None:
    op.drop_index("ix_doc_folder_access_subject", table_name="tab_doc_folder_access")
    op.drop_index("ix_doc_folder_access_folder", table_name="tab_doc_folder_access")
    op.drop_table("tab_doc_folder_access")
