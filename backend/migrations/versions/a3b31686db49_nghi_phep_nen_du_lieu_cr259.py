"""nghi_phep_nen_du_lieu_cr259

Nền dữ liệu của phân hệ Nghỉ phép (CR-259, đợt P-01):
  · 6 bảng mới — loại nghỉ + bậc thâm niên + quỹ phép + đơn + bàn giao + lịch lễ;
  · 2 cột thêm vào `tab_employee` — `hire_date` (mốc tính thâm niên) và `gender`
    (lọc loại nghỉ theo giới tính).

⚠️ **Tệp này đã được CẮT TAY.** `--autogenerate` kéo theo ~30 thay đổi KHÔNG
liên quan: hàng loạt `alter_column ... nullable=False` trên `tab_assistant_*`,
`tab_comment_*`, `tab_mailbox`, `tab_payment_request`, `tab_ticket*`, cộng vài
index của `tab_employee_department`. Chúng là chênh lệch tồn đọng giữa model và
CSDL thật, có từ trước đợt này — cho chúng đi ké một migration về nghỉ phép thì
lúc có sự cố không ai lần ra được vì sao cột của Trợ lý AI đổi trong lần deploy
đó. Muốn dọn thì dọn thành một migration riêng, đặt tên đúng việc.

⚠️ **`down_revision` đã ĐỔI khi rebase 03/09/2026.** Bản đầu nối vào
`c3a91d47f2b8`, nhưng nhánh `erp-v2` trong lúc đó cũng nối `e7b3c9d41f28`
(forum_board) vào đúng điểm ấy — hai nhánh migration cùng lúc, và alembic dừng
với *"Multiple head revisions"* ngay ở bước `upgrade head` của `start.sh`.
Nghĩa là ai `git pull` về cũng không khởi động nổi `api`. Việc này rebase xong
đứng sau, nên nối tiếp vào head lúc đó là `f8b3d6a2c714`.

Revision ID: a3b31686db49
Revises: f8b3d6a2c714
Create Date: 2026-09-03 04:23:44.898129
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3b31686db49'
down_revision: Union[str, None] = 'f8b3d6a2c714'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_holiday',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('is_recurring', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('company_id', 'date', name='uq_holiday_company_date')
    )
    op.create_index('ix_holiday_date', 'tab_holiday', ['date'], unique=False)
    op.create_table('tab_leave_balance',
    sa.Column('employee_id', sa.BigInteger(), nullable=False),
    sa.Column('year', sa.SmallInteger(), nullable=False),
    sa.Column('leave_type_id', sa.BigInteger(), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('allocated_days', sa.Float(), nullable=False),
    sa.Column('seniority_days', sa.Float(), nullable=False),
    sa.Column('carried_days', sa.Float(), nullable=False),
    sa.Column('adjusted_days', sa.Float(), nullable=False),
    sa.Column('used_days', sa.Float(), nullable=False),
    sa.Column('pending_days', sa.Float(), nullable=False),
    sa.Column('note', sa.String(length=500), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('employee_id', 'year', 'leave_type_id', name='uq_leave_balance_emp_year_type')
    )
    op.create_index('ix_leave_balance_emp_year', 'tab_leave_balance', ['employee_id', 'year'], unique=False)
    op.create_table('tab_leave_handover',
    sa.Column('request_id', sa.BigInteger(), nullable=False),
    sa.Column('employee_id', sa.BigInteger(), nullable=False),
    sa.Column('content', sa.String(length=500), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_leave_handover_request', 'tab_leave_handover', ['request_id'], unique=False)
    op.create_table('tab_leave_request',
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('department_id', sa.BigInteger(), nullable=False),
    sa.Column('employee_id', sa.BigInteger(), nullable=False),
    sa.Column('leave_type_id', sa.BigInteger(), nullable=False),
    sa.Column('from_date', sa.Date(), nullable=False),
    sa.Column('to_date', sa.Date(), nullable=False),
    sa.Column('from_session', sa.SmallInteger(), nullable=False),
    sa.Column('to_session', sa.SmallInteger(), nullable=False),
    sa.Column('unit', sa.SmallInteger(), nullable=False),
    sa.Column('total_days', sa.Float(), nullable=False),
    sa.Column('reason', sa.String(length=1000), nullable=False),
    sa.Column('contact_phone', sa.String(length=30), nullable=False),
    sa.Column('contact_address', sa.String(length=255), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=False),
    sa.Column('approval_instance_id', sa.BigInteger(), nullable=False),
    sa.Column('document_id', sa.BigInteger(), nullable=False),
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
    op.create_index('ix_leave_request_emp_date', 'tab_leave_request', ['employee_id', 'from_date'], unique=False)
    op.create_index('ix_leave_request_range', 'tab_leave_request', ['from_date', 'to_date'], unique=False)
    op.create_index('ix_leave_request_status', 'tab_leave_request', ['status'], unique=False)
    op.create_table('tab_leave_type',
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('is_paid', sa.Boolean(), nullable=False),
    sa.Column('counts_balance', sa.Boolean(), nullable=False),
    sa.Column('annual_quota_days', sa.Float(), nullable=False),
    sa.Column('max_days_per_request', sa.Float(), nullable=False),
    sa.Column('carry_over', sa.Boolean(), nullable=False),
    sa.Column('carry_over_max_days', sa.Float(), nullable=False),
    sa.Column('carry_over_expire_month', sa.SmallInteger(), nullable=False),
    sa.Column('gender', sa.SmallInteger(), nullable=False),
    sa.Column('min_notice_days', sa.SmallInteger(), nullable=False),
    sa.Column('require_attachment', sa.Boolean(), nullable=False),
    sa.Column('exclude_holiday', sa.Boolean(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('note', sa.String(length=500), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('tab_leave_type_seniority',
    sa.Column('leave_type_id', sa.BigInteger(), nullable=False),
    sa.Column('years_from', sa.SmallInteger(), nullable=False),
    sa.Column('years_to', sa.SmallInteger(), nullable=False),
    sa.Column('extra_days', sa.Float(), nullable=False),
    sa.Column('note', sa.String(length=255), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_leave_seniority_type', 'tab_leave_type_seniority', ['leave_type_id', 'years_from'], unique=False)

    #  `hire_date` để NULL được: hồ sơ cũ chưa ai nhập ngày vào làm, và bắt buộc
    #  ở đây thì migration phải bịa một ngày cho mọi người — thâm niên sai còn
    #  tệ hơn thâm niên trống. `balance_service` coi NULL là 0 năm và màn Quỹ
    #  phép trưng cảnh báo ra (Q4 của kế hoạch).
    op.add_column('tab_employee', sa.Column('hire_date', sa.Date(), nullable=True))
    #  `gender` NOT NULL nên PHẢI có `server_default` — bảng đang có dữ liệu,
    #  thiếu nó là MySQL từ chối thêm cột. `0` = chưa khai, và chưa khai thì
    #  không bị chặn loại nghỉ nào (xem `leave/constants.GENDER_UNKNOWN`).
    op.add_column('tab_employee',
                  sa.Column('gender', sa.SmallInteger(), nullable=False,
                            server_default='0'))


def downgrade() -> None:
    op.drop_column('tab_employee', 'gender')
    op.drop_column('tab_employee', 'hire_date')
    op.drop_index('ix_leave_seniority_type', table_name='tab_leave_type_seniority')
    op.drop_table('tab_leave_type_seniority')
    op.drop_table('tab_leave_type')
    op.drop_index('ix_leave_request_status', table_name='tab_leave_request')
    op.drop_index('ix_leave_request_range', table_name='tab_leave_request')
    op.drop_index('ix_leave_request_emp_date', table_name='tab_leave_request')
    op.drop_table('tab_leave_request')
    op.drop_index('ix_leave_handover_request', table_name='tab_leave_handover')
    op.drop_table('tab_leave_handover')
    op.drop_index('ix_leave_balance_emp_year', table_name='tab_leave_balance')
    op.drop_table('tab_leave_balance')
    op.drop_index('ix_holiday_date', table_name='tab_holiday')
    op.drop_table('tab_holiday')
