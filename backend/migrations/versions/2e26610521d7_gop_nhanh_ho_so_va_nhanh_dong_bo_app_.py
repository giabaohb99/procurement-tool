"""Gộp hai nhánh migration — phân hệ Hồ sơ × đồng bộ app đặt xe

Hai nhóm việc làm song song cùng tách ra từ `a3e8c1f6d924` (17/09/2026):

    a3e8c1f6d924 ─┬─ e4b7bc674d61 ── c8a1d4f60b37   Hồ sơ (danh mục + bảng hồ sơ)
                  └─ b7c2e4a91f30 ── … ── e5a1b9c73d04   bao-CR-415/416 đồng bộ

⚠️ **Gộp chứ không nối lại chuỗi**, dù nối chuỗi nhìn gọn hơn: cả hai nhánh đều
ĐÃ ĐẨY LÊN `origin/erp-v2`, tức là đã chạy trên máy người khác và có thể đã lên
dev-UAT. Sửa `down_revision` của một migration đã phát hành thì máy nào lỡ chạy
nó rồi sẽ mang một `alembic_version` không còn tồn tại trong chuỗi — và `alembic
upgrade` ở đó **không chạy lại được nữa**. Khuôn này đã dùng vài lần ở repo,
xem `cc503d81a047_merge_heads.py`.

KHÔNG có thao tác DDL nào: hai nhánh đụng vào những bảng rời nhau (`tab_dossier`
+ `tab_dossier_type` bên này, `tab_sync_log` + `tab_file` + đặt xe bên kia), nên
không có gì phải hòa giải. Bản gộp chỉ để Alembic còn đúng MỘT head.

Revision ID: 2e26610521d7
Revises: e5a1b9c73d04, c8a1d4f60b37
Create Date: 2026-09-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e26610521d7'
down_revision: Union[str, None] = ('e5a1b9c73d04', 'c8a1d4f60b37')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
