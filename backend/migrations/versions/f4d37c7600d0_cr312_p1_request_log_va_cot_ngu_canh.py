"""bao-CR-312 P1 — `tab_request_log` + cột ngữ cảnh cho `tab_audit_log`

Hai quyết định phải ĐÚNG NGAY Ở MIGRATION ĐẦU, vì sửa sau là `ALTER` trên bảng
đã vài trăm nghìn dòng:

- **QĐ-B**: `request_id` là `BINARY(16)`, không phải `CHAR(36)`. Đây là cột duy
  nhất có mặt và có chỉ mục ở cả ba bảng nhật ký, nên chênh lệch nhân lên ba
  lần: ~26 MB/năm nếu lưu chuỗi, ~14 MB nếu lưu nhị phân. Tra tay dưới DB phải
  dùng `UUID_TO_BIN()` / `BIN_TO_UUID()`.
- **QĐ-A**: gia hạn phiên thành công không đẻ dòng — luật nằm ở
  `core/logging_policy.py`, không phải ở lược đồ, nhưng ghi ra đây để ai đọc
  migration này hiểu vì sao bảng không phình như ước tính ban đầu.

Cột thêm vào `tab_audit_log` để `NOT NULL` kèm `server_default`: 4.201 dòng cũ
phải có giá trị, và `actor_kind = 0` ("không rõ") là đúng với chúng — chúng ra
đời trước khi hệ thống biết phân biệt người với máy, đừng đoán ngược lại.

Tài liệu: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.1, §4.2, §4.5.

Revision ID: f4d37c7600d0
Revises: d7f2a9c4e1b8
Create Date: 2026-09-09 10:18:04.644509
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f4d37c7600d0'
down_revision: Union[str, None] = 'd7f2a9c4e1b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_request_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.BINARY(length=16), nullable=False),
        sa.Column('source', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('session_id', sa.BigInteger(), nullable=True),
        sa.Column('ip', sa.String(length=45), nullable=False, server_default=''),
        sa.Column('method', sa.String(length=8), nullable=False, server_default=''),
        sa.Column('path', sa.String(length=300), nullable=False, server_default=''),
        sa.Column('route', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('query_string', sa.String(length=1000), nullable=False, server_default=''),
        sa.Column('request_body', sa.JSON(), nullable=True),
        sa.Column('http_status', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('response_body', sa.JSON(), nullable=True),
        sa.Column('error_code', sa.String(length=60), nullable=False, server_default=''),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('audit_count', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('change_count', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id'),
    )
    op.create_index(op.f('ix_tab_request_log_created_at'), 'tab_request_log', ['created_at'])
    op.create_index(op.f('ix_tab_request_log_http_status'), 'tab_request_log', ['http_status'])
    op.create_index(op.f('ix_tab_request_log_ip'), 'tab_request_log', ['ip'])
    op.create_index(op.f('ix_tab_request_log_route'), 'tab_request_log', ['route'])
    op.create_index(op.f('ix_tab_request_log_session_id'), 'tab_request_log', ['session_id'])
    op.create_index(op.f('ix_tab_request_log_user_id'), 'tab_request_log', ['user_id'])

    op.add_column('tab_audit_log',
                  sa.Column('actor_kind', sa.SmallInteger(), nullable=False, server_default='0'))
    op.add_column('tab_audit_log', sa.Column('session_id', sa.BigInteger(), nullable=True))
    op.add_column('tab_audit_log', sa.Column('request_id', sa.BINARY(length=16), nullable=True))
    op.add_column('tab_audit_log',
                  sa.Column('ip', sa.String(length=45), nullable=False, server_default=''))
    op.add_column('tab_audit_log',
                  sa.Column('on_behalf_of', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('tab_audit_log',
                  sa.Column('doc_code', sa.String(length=50), nullable=False, server_default=''))
    op.add_column('tab_audit_log',
                  sa.Column('parent_entity', sa.String(length=50), nullable=False,
                            server_default=''))
    op.add_column('tab_audit_log',
                  sa.Column('parent_id', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('tab_audit_log',
                  sa.Column('action_group', sa.SmallInteger(), nullable=False, server_default='0'))
    op.add_column('tab_audit_log',
                  sa.Column('changed_fields', sa.String(length=500), nullable=False,
                            server_default=''))
    op.add_column('tab_audit_log',
                  sa.Column('change_count', sa.SmallInteger(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_tab_audit_log_request_id'), 'tab_audit_log', ['request_id'])
    op.create_index(op.f('ix_tab_audit_log_session_id'), 'tab_audit_log', ['session_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_audit_log_session_id'), table_name='tab_audit_log')
    op.drop_index(op.f('ix_tab_audit_log_request_id'), table_name='tab_audit_log')
    for column in ('change_count', 'changed_fields', 'action_group', 'parent_id',
                   'parent_entity', 'doc_code', 'on_behalf_of', 'ip', 'request_id',
                   'session_id', 'actor_kind'):
        op.drop_column('tab_audit_log', column)

    op.drop_index(op.f('ix_tab_request_log_user_id'), table_name='tab_request_log')
    op.drop_index(op.f('ix_tab_request_log_session_id'), table_name='tab_request_log')
    op.drop_index(op.f('ix_tab_request_log_route'), table_name='tab_request_log')
    op.drop_index(op.f('ix_tab_request_log_ip'), table_name='tab_request_log')
    op.drop_index(op.f('ix_tab_request_log_http_status'), table_name='tab_request_log')
    op.drop_index(op.f('ix_tab_request_log_created_at'), table_name='tab_request_log')
    op.drop_table('tab_request_log')
