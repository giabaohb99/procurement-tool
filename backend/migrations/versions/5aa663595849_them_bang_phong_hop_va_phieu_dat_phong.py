"""them bang phong hop va phieu dat phong (duoc-CR-279)

⚠️ Bản autogenerate ban đầu quét ra CẢ chục thay đổi của module khác (diễn đàn,
thanh toán, ticket, trợ lý) — đó là drift giữa model và DB local của người khác,
KHÔNG thuộc đợt này. Đã cắt bỏ, chỉ giữ ba bảng mới. Đừng chạy lại autogenerate
rồi commit nguyên bản: nó sẽ đổi kiểu cột của những bảng đang chạy thật.

Revision ID: 5aa663595849
Revises: a3b31686db49
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5aa663595849'
down_revision: Union[str, None] = 'a3b31686db49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_meeting_room',
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('location', sa.String(length=255), nullable=False),
    sa.Column('capacity', sa.Integer(), nullable=False),
    sa.Column('equipment', sa.String(length=500), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('note', sa.String(length=500), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_tab_meeting_room_company_id'), 'tab_meeting_room', ['company_id'], unique=False)
    op.create_table('tab_room_booking',
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('room_id', sa.BigInteger(), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('department_id', sa.BigInteger(), nullable=False),
    sa.Column('requester_employee_id', sa.BigInteger(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('purpose', sa.Text(), nullable=False),
    sa.Column('start_at', sa.DateTime(), nullable=False),
    sa.Column('end_at', sa.DateTime(), nullable=False),
    sa.Column('attendee_count', sa.Integer(), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=False),
    sa.Column('approval_instance_id', sa.BigInteger(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(), nullable=True),
    sa.Column('decided_at', sa.DateTime(), nullable=True),
    sa.Column('decision_note', sa.String(length=500), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index('ix_room_booking_requester', 'tab_room_booking', ['requester_employee_id'], unique=False)
    op.create_index('ix_room_booking_room_time', 'tab_room_booking', ['room_id', 'start_at', 'end_at'], unique=False)
    op.create_index('ix_room_booking_status', 'tab_room_booking', ['status'], unique=False)
    op.create_table('tab_room_booking_attendee',
    sa.Column('booking_id', sa.BigInteger(), nullable=False),
    sa.Column('employee_id', sa.BigInteger(), nullable=False),
    sa.Column('role', sa.String(length=100), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_room_attendee_booking', 'tab_room_booking_attendee', ['booking_id'], unique=False)
    op.create_index('ix_room_attendee_employee', 'tab_room_booking_attendee', ['employee_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_room_attendee_employee', table_name='tab_room_booking_attendee')
    op.drop_index('ix_room_attendee_booking', table_name='tab_room_booking_attendee')
    op.drop_table('tab_room_booking_attendee')
    op.drop_index('ix_room_booking_status', table_name='tab_room_booking')
    op.drop_index('ix_room_booking_room_time', table_name='tab_room_booking')
    op.drop_index('ix_room_booking_requester', table_name='tab_room_booking')
    op.drop_table('tab_room_booking')
    op.drop_index(op.f('ix_tab_meeting_room_company_id'), table_name='tab_meeting_room')
    op.drop_table('tab_meeting_room')
