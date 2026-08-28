"""b13_truong_tuy_bien_6_kieu

Trường tùy biến của phân hệ Dự án mở từ MỘT kiểu (chọn một giá trị) sang SÁU
kiểu như Lark: chọn một · chọn nhiều · người · số · ngày · chữ (B-13).

⚠️ Bản autogenerate lôi vào cả một đống `alter_column` NOT NULL / index của
`tab_assistant_*`, `tab_comment_*`, `tab_ticket_*`, `tab_employee_department` —
đó là ĐỘ LỆCH CŨ giữa model và CSDL, không phải việc của đợt này, và migration
`631070f1b801` trước đó cũng đã phải cắt đúng những dòng ấy. Tệp này chỉ giữ
phần thuộc cụm nhãn.

Dữ liệu cũ KHÔNG cần vá: `field_type` mặc định `1 = SINGLE` nên mọi trường đã
khai giữ nguyên hành vi, và các cột `value_*` mới đều rỗng.

Revision ID: 9e357b249200
Revises: 631070f1b801
Create Date: 2026-08-28 10:25:22.566314
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9e357b249200'
down_revision: Union[str, None] = '631070f1b801'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tab_work_label_field',
        sa.Column('field_type', sa.SmallInteger(), nullable=False, server_default='1'),
    )

    op.add_column(
        'tab_work_task_label',
        sa.Column('value_text', sa.String(length=500), nullable=False, server_default=''),
    )
    op.add_column(
        'tab_work_task_label',
        sa.Column('value_number', sa.Numeric(precision=18, scale=4), nullable=True),
    )
    op.add_column(
        'tab_work_task_label',
        sa.Column('value_date', sa.String(length=10), nullable=False, server_default=''),
    )
    op.add_column(
        'tab_work_task_label',
        sa.Column('value_employee_id', sa.BigInteger(), nullable=True),
    )

    #  Bốn kiểu không có bộ giá trị (chữ · số · ngày · người) để `option_id` rỗng.
    op.alter_column(
        'tab_work_task_label', 'option_id',
        existing_type=sa.BigInteger(), nullable=True,
    )

    #  GỠ unique `(task_id, field_id)`: trước đây chính nó là ràng buộc "chọn
    #  một", nhưng kiểu CHỌN NHIỀU cần nhiều dòng cùng cặp khóa đó. Luật
    #  "kiểu này chỉ một giá trị" chuyển hẳn xuống `set_label` bên service.
    op.drop_index('uq_work_task_label', table_name='tab_work_task_label')
    op.create_index(
        'ix_work_task_label_task_field', 'tab_work_task_label',
        ['task_id', 'field_id'], unique=False,
    )


def downgrade() -> None:
    #  ⚠️ Lùi được CHỈ KHI chưa có trường chọn-nhiều nào được dùng: dựng lại
    #  unique `(task_id, field_id)` sẽ vỡ nếu đã tồn tại task mang hai giá trị
    #  cho cùng một trường. Dọn tay trước khi lùi.
    op.drop_index('ix_work_task_label_task_field', table_name='tab_work_task_label')
    op.create_index(
        'uq_work_task_label', 'tab_work_task_label', ['task_id', 'field_id'], unique=True,
    )
    op.alter_column(
        'tab_work_task_label', 'option_id',
        existing_type=sa.BigInteger(), nullable=False,
    )
    op.drop_column('tab_work_task_label', 'value_employee_id')
    op.drop_column('tab_work_task_label', 'value_date')
    op.drop_column('tab_work_task_label', 'value_number')
    op.drop_column('tab_work_task_label', 'value_text')
    op.drop_column('tab_work_label_field', 'field_type')
