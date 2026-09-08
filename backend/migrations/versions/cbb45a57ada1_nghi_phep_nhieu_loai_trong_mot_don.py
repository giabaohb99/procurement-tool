"""nghi phep: nhieu loai nghi trong mot don

Bảng `tab_leave_request_line` — mỗi dòng là MỘT loại nghỉ trong tờ đơn, kèm số
ngày của loại đó. Cả đơn vẫn dùng chung một khoảng ngày ở đầu phiếu.

⚠️ **Phần backfill là bắt buộc, không phải tiện tay.** Sau đợt này mọi nhịp của
sổ quỹ phép (giữ chỗ · trừ thật · trả lại · hoàn) đọc bảng dòng chứ không đọc
`tab_leave_request.leave_type_id` nữa. Đơn cũ không có dòng nào thì hủy nó đi
KHÔNG hoàn lại ngày phép, và lỗi đó im lặng — đúng kiểu chỉ lộ ra khi ai đó cộng
tay lại sổ cuối năm.

Revision ID: cbb45a57ada1
Revises: 73f09d029675
Create Date: 2026-09-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'cbb45a57ada1'
down_revision: Union[str, None] = '73f09d029675'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_leave_request_line',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.BigInteger(), nullable=False),
        sa.Column('leave_type_id', sa.BigInteger(), nullable=False),
        sa.Column('days', sa.Float(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_leave_request_line_request', 'tab_leave_request_line',
                    ['request_id'], unique=False)
    op.create_index('ix_leave_request_line_type', 'tab_leave_request_line',
                    ['leave_type_id'], unique=False)

    #  Backfill: mỗi đơn cũ thành đúng một dòng. Lọc `total_days > 0` để không
    #  đẻ ra dòng 0 ngày — `check_lines` coi dòng như vậy là dữ liệu hỏng, và
    #  đơn nháp chưa nhập gì thì người dùng sẽ nhập lại khi mở ra sửa.
    op.execute(sa.text("""
        INSERT INTO tab_leave_request_line
            (request_id, leave_type_id, days, sort_order,
             created_at, created_by, updated_at, updated_by)
        SELECT r.id, r.leave_type_id, r.total_days, 0,
               NOW(), r.created_by, NOW(), r.updated_by
        FROM tab_leave_request r
        WHERE r.leave_type_id > 0 AND r.total_days > 0
    """))


def downgrade() -> None:
    op.drop_index('ix_leave_request_line_type', table_name='tab_leave_request_line')
    op.drop_index('ix_leave_request_line_request', table_name='tab_leave_request_line')
    op.drop_table('tab_leave_request_line')
