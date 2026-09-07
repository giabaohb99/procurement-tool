"""Nghỉ phép THEO GIỜ: hai cột khoảng giờ trên đơn nghỉ

Buổi nghỉ có thêm lựa chọn **Theo giờ** (`SESSION_HOURLY = 4`) — đi khám nửa
buổi, ra ngân hàng hai tiếng. Khoảng giờ lưu ở hai cột này; số ngày quy đổi
bằng `số giờ / constants.WORK_HOURS_PER_DAY`.

⚠️ `NULL` khi đơn KHÔNG khai theo giờ, không phải `00:00`. Một tờ đơn nghỉ cả
ngày mang giờ `00:00 → 00:00` thì mọi báo cáo về sau phải nhớ bỏ qua nó, và sớm
muộn có chỗ quên.

⚠️ Bản autogenerate ban đầu kéo theo cả trăm dòng KHÔNG liên quan (tạo lại bảng
diễn đàn, hàng loạt `NOT NULL` của các bảng khác) — đó là chênh lệch nền có sẵn
giữa model và CSDL, không phải việc của lần sửa này. Đã cắt bỏ hết, giữ đúng hai
cột. Đụng vào các chênh lệch kia thì làm ở một migration riêng, có chủ đích.

Revision ID: 73f09d029675
Revises: a3f7c1e90d24
"""
from alembic import op
import sqlalchemy as sa

revision = "73f09d029675"
down_revision = "a3f7c1e90d24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tab_leave_request", sa.Column("from_time", sa.Time(), nullable=True))
    op.add_column("tab_leave_request", sa.Column("to_time", sa.Time(), nullable=True))


def downgrade() -> None:
    op.drop_column("tab_leave_request", "to_time")
    op.drop_column("tab_leave_request", "from_time")
