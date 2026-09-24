"""Điều kiện áp dụng của hồ sơ — hai cột JSON trên `tab_dossier`.

Revision ID: 2ef5534e5ace
Revises: 9f8e7d6c5b4a
Create Date: 2026-09-21 02:32:07.353714

⚠️ **Bản autogenerate đã bị CẮT về đúng hai cột này.** Nó quét ra thêm ~650 dòng
trôi dạt không liên quan — `NOT NULL` trên `created_at`/`updated_at` của hai chục
bảng, và một loạt đổi tên chỉ mục (`ix_vbooking_legacy_id` →
`ix_tab_vehicle_booking_legacy_id`). Đó là khoảng lệch có sẵn giữa model và DB
thật, tích từ trước; gom nó vào một migration mang tên «điều kiện áp dụng hồ sơ»
là giấu một đợt sửa lược đồ diện rộng dưới một cái tên không nói gì, và lúc phải
quay đầu thì không tách ra được. Muốn dọn thì dọn thành migration riêng, có tên
riêng, chạy lúc có người canh.

`nullable=True` cho cả hai: `NULL` = **chưa khai**, đọc ra danh sách rỗng qua
`apply_doc_kind_list` / `apply_condition_list`, và rỗng ở `apply_doc_kinds`
nghĩa là hồ sơ KHÔNG hiện ra ở chứng từ nào — đúng hành vi cũ của mọi hồ sơ đã
có. Xem `app/modules/dossier/applicability.py`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2ef5534e5ace'
down_revision: Union[str, None] = '9f8e7d6c5b4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_dossier', sa.Column('apply_doc_kinds', sa.JSON(), nullable=True))
    op.add_column('tab_dossier', sa.Column('apply_conditions', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_dossier', 'apply_conditions')
    op.drop_column('tab_dossier', 'apply_doc_kinds')
