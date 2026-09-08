"""nghi phep: ket so cuoi nam (mang sang / quy doi) + thu hoi phep het han

Ba ô «Cho chuyển phép sang năm sau · Chuyển tối đa · Hết hạn cuối tháng» trước
đợt này là cột chết — lưu được nhưng không chỗ nào đọc. Đợt này chúng chạy thật,
và công tắc hai nước `carry_over` được thay bằng `year_end_mode` ba nước để nói
được nước thứ ba: quy đổi số dư sang một loại nghỉ KHÁC.

⚠️ Tệp autogenerate ra kèm cả drift của các module khác trên nhánh này
(tab_forum_*, tab_payment_request_line, một mớ NOT NULL) — đã CẮT HẾT. Migration
chỉ đụng đúng hai bảng của phân hệ Nghỉ phép.

Revision ID: 7b479d6dd387
Revises: cbb45a57ada1
Create Date: 2026-09-07 07:30:34.924719
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7b479d6dd387'
down_revision: Union[str, None] = 'cbb45a57ada1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  Khớp `app/modules/leave/constants.py`. Chép số vào đây chứ không import: một
#  migration đã chạy phải đọc được y nguyên kể cả khi hằng số kia đổi về sau.
YEAR_END_DROP = 0
YEAR_END_CARRY = 1


def upgrade() -> None:
    #  `server_default` để dòng CŨ có giá trị (cột NOT NULL), rồi bỏ ngay sau đó:
    #  giá trị mặc định thuộc về tầng ứng dụng, để lại dưới CSDL là hai nguồn.
    op.add_column('tab_leave_balance',
                  sa.Column('carried_out_days', sa.Float(), nullable=False,
                            server_default='0'))
    op.add_column('tab_leave_balance',
                  sa.Column('carried_expired_days', sa.Float(), nullable=False,
                            server_default='0'))
    op.add_column('tab_leave_type',
                  sa.Column('year_end_mode', sa.SmallInteger(), nullable=False,
                            server_default=str(YEAR_END_DROP)))
    op.add_column('tab_leave_type',
                  sa.Column('convert_to_type_id', sa.BigInteger(), nullable=False,
                            server_default='0'))
    op.add_column('tab_leave_type',
                  sa.Column('convert_ratio', sa.Float(), nullable=False,
                            server_default='1'))

    #  Đổ dữ liệu công tắc cũ sang cột mới. Ai đã bật «Cho chuyển phép sang năm
    #  sau» thì giữ nguyên ý định đó — bỏ qua bước này là lặng lẽ tắt cấu hình
    #  của người ta.
    op.execute(f"UPDATE tab_leave_type SET year_end_mode = {YEAR_END_CARRY} "
               "WHERE carry_over = 1")

    for table, column in (('tab_leave_balance', 'carried_out_days'),
                          ('tab_leave_balance', 'carried_expired_days'),
                          ('tab_leave_type', 'convert_to_type_id'),
                          ('tab_leave_type', 'convert_ratio')):
        op.alter_column(table, column, server_default=None)
    op.alter_column('tab_leave_type', 'year_end_mode', server_default=None,
                    existing_type=sa.SmallInteger(), existing_nullable=False)


def downgrade() -> None:
    #  Trả lại công tắc cũ trước khi bỏ cột — quay lui mà mất cấu hình thì lần
    #  tiến lên sau không dựng lại được.
    op.execute(f"UPDATE tab_leave_type SET carry_over = 1 "
               f"WHERE year_end_mode = {YEAR_END_CARRY}")
    op.drop_column('tab_leave_type', 'convert_ratio')
    op.drop_column('tab_leave_type', 'convert_to_type_id')
    op.drop_column('tab_leave_type', 'year_end_mode')
    op.drop_column('tab_leave_balance', 'carried_expired_days')
    op.drop_column('tab_leave_balance', 'carried_out_days')
