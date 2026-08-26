"""Hộp thư gửi danh nghĩa + trạng thái Chờ ban hành (26/08/2026)

Bốn thay đổi, một mục đích: cho phép **chọn địa chỉ gửi thông báo lúc ban hành**,
và tách nhịp *ký xong* khỏi nhịp *phát hành*.

  1. `tab_mailbox` + `tab_mailbox_member` — địa chỉ gửi đi kèm bộ SMTP riêng, và
     danh sách nhân sự được gửi danh nghĩa địa chỉ đó;
  2. `tab_doc_type.auto_issue_after_approval` — loại nào duyệt xong ban hành
     luôn, loại nào dừng chờ người soạn bấm;
  3. `tab_document.issue_mailbox_id` — hộp thư đã dùng để phát hành văn bản đó;
  4. `tab_email_log.mailbox_id` + `from_email` — thư đó đi bằng hộp thư nào và
     người nhận thấy địa chỉ gì.

⚠️ `auto_issue_after_approval` phải có **`server_default = 1`**. Cột thêm mới mà
để `NULL` thì mọi loại văn bản đang chạy bỗng rơi vào nhánh "dừng chờ người bấm"
— tức là mọi phiếu đang duyệt dở của cả hệ đứng lại chờ một cú bấm mà chưa ai
được báo là phải bấm.

⚠️ Bản tự sinh của Alembic kéo theo hơn 150 dòng `alter_column ... nullable` và
vài `drop_index` **không liên quan** — đó là chênh lệch tích tụ từ trước giữa
model và DB thật. Đã cắt bỏ hết: một lần di trú chỉ làm đúng việc của nó, dọn
chênh lệch cũ là một lần di trú riêng có chủ ý.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'fbfb0f748739'
down_revision: Union[str, None] = 'c5bf3dae51db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_mailbox',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False,
                  server_default=''),
        sa.Column('smtp_host', sa.String(length=200), nullable=False,
                  server_default=''),
        sa.Column('smtp_port', sa.Integer(), nullable=False, server_default='587'),
        sa.Column('smtp_user', sa.String(length=255), nullable=False,
                  server_default=''),
        sa.Column('smtp_password_enc', sa.Text(), nullable=True),
        sa.Column('use_tls', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_mailbox_active', 'tab_mailbox', ['is_active', 'company_id'])
    op.create_index('ix_tab_mailbox_company_id', 'tab_mailbox', ['company_id'])

    op.create_table(
        'tab_mailbox_member',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('mailbox_id', sa.BigInteger(), nullable=False),
        sa.Column('employee_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mailbox_id', 'employee_id', name='uq_mailbox_member'),
    )
    op.create_index('ix_tab_mailbox_member_mailbox_id', 'tab_mailbox_member', ['mailbox_id'])
    op.create_index('ix_tab_mailbox_member_employee_id', 'tab_mailbox_member', ['employee_id'])

    #  server_default='1' — xem cảnh báo ở đầu tệp.
    op.add_column('tab_doc_type', sa.Column(
        'auto_issue_after_approval', sa.Boolean(), nullable=False,
        server_default=sa.text('1')))

    op.add_column('tab_document', sa.Column(
        'issue_mailbox_id', sa.BigInteger(), nullable=True))

    op.add_column('tab_email_log', sa.Column(
        'mailbox_id', sa.BigInteger(), nullable=True))
    op.add_column('tab_email_log', sa.Column(
        'from_email', sa.String(length=255), nullable=False, server_default=''))
    op.create_index('ix_tab_email_log_mailbox_id', 'tab_email_log', ['mailbox_id'])


def downgrade() -> None:
    op.drop_index('ix_tab_email_log_mailbox_id', table_name='tab_email_log')
    op.drop_column('tab_email_log', 'from_email')
    op.drop_column('tab_email_log', 'mailbox_id')
    op.drop_column('tab_document', 'issue_mailbox_id')
    op.drop_column('tab_doc_type', 'auto_issue_after_approval')
    op.drop_index('ix_tab_mailbox_member_employee_id', table_name='tab_mailbox_member')
    op.drop_index('ix_tab_mailbox_member_mailbox_id', table_name='tab_mailbox_member')
    op.drop_table('tab_mailbox_member')
    op.drop_index('ix_tab_mailbox_company_id', table_name='tab_mailbox')
    op.drop_index('ix_mailbox_active', table_name='tab_mailbox')
    op.drop_table('tab_mailbox')
