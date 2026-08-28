"""bang tab_work_ phan he Cong viec W0 CR-217

Revision ID: 631070f1b801
Revises: e36bb121fce6
Create Date: 2026-08-28 05:06:56.932470
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '631070f1b801'
down_revision: Union[str, None] = 'e36bb121fce6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #  CHỈ tạo 12 bảng mới của phân hệ Công việc (CR-216 / W0). Bản autogenerate
    #  còn kèm một loạt `alter_column` NOT NULL và index của tab_assistant_* /
    #  tab_comment_* / tab_ticket_* / tab_employee_department — đó là ĐỘ LỆCH CŨ
    #  giữa model và DB, không phải việc của đợt này; gộp vào đây là sửa lén bảng
    #  người khác trong một migration mang tên "thêm bảng". Đã cắt bỏ.
    op.create_table('tab_work_group',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('sort_order', sa.BigInteger(), nullable=False),
    sa.Column('is_archived', sa.SmallInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['tab_work_group.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_work_group_company_id'), 'tab_work_group', ['company_id'], unique=False)
    op.create_table('tab_work_group_member',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('group_id', sa.BigInteger(), nullable=False),
    sa.Column('employee_id', sa.BigInteger(), nullable=False),
    sa.Column('department_id', sa.BigInteger(), nullable=True),
    sa.Column('role', sa.SmallInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['tab_work_group.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('group_id', 'employee_id', name='uq_work_group_member')
    )
    op.create_index(op.f('ix_tab_work_group_member_company_id'), 'tab_work_group_member', ['company_id'], unique=False)
    op.create_index(op.f('ix_tab_work_group_member_group_id'), 'tab_work_group_member', ['group_id'], unique=False)
    op.create_index('ix_work_group_member_emp', 'tab_work_group_member', ['employee_id'], unique=False)
    op.create_table('tab_work_list',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('group_id', sa.BigInteger(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=False),
    sa.Column('sort_order', sa.BigInteger(), nullable=False),
    sa.Column('is_archived', sa.SmallInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['tab_work_group.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_work_list_company_id'), 'tab_work_list', ['company_id'], unique=False)
    op.create_index(op.f('ix_tab_work_list_group_id'), 'tab_work_list', ['group_id'], unique=False)
    op.create_table('tab_work_label_field',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('list_id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('sort_order', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['list_id'], ['tab_work_list.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('list_id', 'name', name='uq_work_label_field')
    )
    op.create_index(op.f('ix_tab_work_label_field_company_id'), 'tab_work_label_field', ['company_id'], unique=False)
    op.create_index(op.f('ix_tab_work_label_field_list_id'), 'tab_work_label_field', ['list_id'], unique=False)
    op.create_table('tab_work_list_member',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('list_id', sa.BigInteger(), nullable=False),
    sa.Column('employee_id', sa.BigInteger(), nullable=False),
    sa.Column('department_id', sa.BigInteger(), nullable=True),
    sa.Column('role', sa.SmallInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['list_id'], ['tab_work_list.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('list_id', 'employee_id', name='uq_work_list_member')
    )
    op.create_index(op.f('ix_tab_work_list_member_company_id'), 'tab_work_list_member', ['company_id'], unique=False)
    op.create_index(op.f('ix_tab_work_list_member_list_id'), 'tab_work_list_member', ['list_id'], unique=False)
    op.create_index('ix_work_list_member_emp', 'tab_work_list_member', ['employee_id'], unique=False)
    op.create_table('tab_work_section',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('list_id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=False),
    sa.Column('sort_order', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['list_id'], ['tab_work_list.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_work_section_company_id'), 'tab_work_section', ['company_id'], unique=False)
    op.create_index(op.f('ix_tab_work_section_list_id'), 'tab_work_section', ['list_id'], unique=False)
    op.create_table('tab_work_tag',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('list_id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=False),
    sa.Column('sort_order', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['list_id'], ['tab_work_list.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('list_id', 'name', name='uq_work_tag_name')
    )
    op.create_index(op.f('ix_tab_work_tag_company_id'), 'tab_work_tag', ['company_id'], unique=False)
    op.create_index(op.f('ix_tab_work_tag_list_id'), 'tab_work_tag', ['list_id'], unique=False)
    op.create_table('tab_work_label_option',
    sa.Column('field_id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=False),
    sa.Column('sort_order', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['field_id'], ['tab_work_label_field.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('field_id', 'name', name='uq_work_label_option')
    )
    op.create_index(op.f('ix_tab_work_label_option_field_id'), 'tab_work_label_option', ['field_id'], unique=False)
    op.create_table('tab_work_task',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('list_id', sa.BigInteger(), nullable=False),
    sa.Column('section_id', sa.BigInteger(), nullable=True),
    sa.Column('parent_id', sa.BigInteger(), nullable=True),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=False),
    sa.Column('priority', sa.SmallInteger(), nullable=False),
    sa.Column('start_date', sa.String(length=10), nullable=False),
    sa.Column('due_date', sa.String(length=10), nullable=False),
    sa.Column('sort_order', sa.BigInteger(), nullable=False),
    sa.Column('creator_employee_id', sa.BigInteger(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('completed_by', sa.BigInteger(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['list_id'], ['tab_work_list.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_id'], ['tab_work_task.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['section_id'], ['tab_work_section.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_work_task_company_id'), 'tab_work_task', ['company_id'], unique=False)
    op.create_index(op.f('ix_tab_work_task_creator_employee_id'), 'tab_work_task', ['creator_employee_id'], unique=False)
    op.create_index(op.f('ix_tab_work_task_list_id'), 'tab_work_task', ['list_id'], unique=False)
    op.create_index('ix_work_task_due_status', 'tab_work_task', ['due_date', 'status'], unique=False)
    op.create_index('ix_work_task_list_parent', 'tab_work_task', ['list_id', 'parent_id', 'deleted_at'], unique=False)
    op.create_table('tab_work_task_assignee',
    sa.Column('task_id', sa.BigInteger(), nullable=False),
    sa.Column('employee_id', sa.BigInteger(), nullable=False),
    sa.Column('kind', sa.SmallInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['tab_work_task.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('task_id', 'employee_id', name='uq_work_task_assignee')
    )
    op.create_index(op.f('ix_tab_work_task_assignee_task_id'), 'tab_work_task_assignee', ['task_id'], unique=False)
    op.create_index('ix_work_task_assignee_emp', 'tab_work_task_assignee', ['employee_id'], unique=False)
    op.create_table('tab_work_task_label',
    sa.Column('task_id', sa.BigInteger(), nullable=False),
    sa.Column('field_id', sa.BigInteger(), nullable=False),
    sa.Column('option_id', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['field_id'], ['tab_work_label_field.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['option_id'], ['tab_work_label_option.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['task_id'], ['tab_work_task.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('task_id', 'field_id', name='uq_work_task_label')
    )
    op.create_index(op.f('ix_tab_work_task_label_field_id'), 'tab_work_task_label', ['field_id'], unique=False)
    op.create_index(op.f('ix_tab_work_task_label_task_id'), 'tab_work_task_label', ['task_id'], unique=False)
    op.create_table('tab_work_task_tag',
    sa.Column('task_id', sa.BigInteger(), nullable=False),
    sa.Column('tag_id', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['tag_id'], ['tab_work_tag.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['task_id'], ['tab_work_task.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('task_id', 'tag_id', name='uq_work_task_tag')
    )
    op.create_index(op.f('ix_tab_work_task_tag_tag_id'), 'tab_work_task_tag', ['tag_id'], unique=False)
    op.create_index(op.f('ix_tab_work_task_tag_task_id'), 'tab_work_task_tag', ['task_id'], unique=False)


def downgrade() -> None:
    #  CHỈ `drop_table`, theo thứ tự phụ thuộc ngược. KHÔNG `drop_index` trước:
    #  MySQL từ chối xóa index đang đỡ một khóa ngoại ("needed in a foreign key
    #  constraint") nên bản autogenerate chạy tới dòng đầu tiên là chết — thử
    #  `alembic downgrade -1` ngày 28/08/2026 đúng lỗi này. Xóa bảng là index
    #  của nó đi theo, không cần dọn tay.
    op.drop_table('tab_work_task_tag')
    op.drop_table('tab_work_task_label')
    op.drop_table('tab_work_task_assignee')
    op.drop_table('tab_work_task')
    op.drop_table('tab_work_label_option')
    op.drop_table('tab_work_label_field')
    op.drop_table('tab_work_tag')
    op.drop_table('tab_work_section')
    op.drop_table('tab_work_list_member')
    op.drop_table('tab_work_group_member')
    op.drop_table('tab_work_list')
    op.drop_table('tab_work_group')
