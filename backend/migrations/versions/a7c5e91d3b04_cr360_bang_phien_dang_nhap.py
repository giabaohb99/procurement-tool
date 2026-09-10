"""bao-CR-360 (CR-312 P3a) — `tab_login_session` + `tab_user.token_version`

Phần lõi của phiên đăng nhập phía máy chủ, đóng **BM-002**. Chưa có màn hình nào
(đó là P3b), nhưng lược đồ phải lên trước để đăng xuất có hiệu lực thật.

Hai điều đáng ghi lại ngay ở đây, vì sửa sau là `ALTER` trên bảng đang chạy:

- **`token_id` là `CHAR(36)`, KHÔNG theo QĐ-B** (thứ bắt `request_id` phải là
  `BINARY(16)`). Cố ý lệch: giá trị này nằm trong claim `jti` của JWT, mà claim
  JWT buộc phải là chuỗi — lưu nhị phân là thêm một phép đổi qua đổi lại ở mọi
  lượt gọi. Chênh lệch dung lượng cũng không đáng: bảng này ~2.000 dòng/năm,
  còn `tab_request_log` là ~1 triệu.
- **`tab_user.token_version` để `NOT NULL` kèm `server_default '1'`.** Mọi tài
  khoản cũ vào "đời 1", và vé phát trước bản này không có claim `ver` nên đằng
  nào cũng bị chặn ở `core/auth._check_session`.

⚠️ **Deploy bản này là MỌI NGƯỜI bị đăng xuất một lần** — vé cũ không mang
`jti`. Đó là hệ quả biết trước, không phải lỗi; báo khách trước khi lên prod.

Tài liệu: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.4, §5, §11 (QĐ-D).

Revision ID: a7c5e91d3b04
Revises: e4b7c2a1d905
Create Date: 2026-09-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a7c5e91d3b04'
down_revision: Union[str, None] = 'e4b7c2a1d905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_login_session',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('token_id', sa.String(length=36), nullable=False, server_default=''),
        sa.Column('token_version', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('ip', sa.String(length=45), nullable=False, server_default=''),
        sa.Column('user_agent', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('device_type', sa.SmallInteger(), nullable=False, server_default='9'),
        sa.Column('os', sa.String(length=60), nullable=False, server_default=''),
        sa.Column('browser', sa.String(length=60), nullable=False, server_default=''),
        sa.Column('device_label', sa.String(length=120), nullable=False, server_default=''),
        sa.Column('login_method', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen_ip', sa.String(length=45), nullable=False, server_default=''),
        sa.Column('refreshed_at', sa.DateTime(), nullable=True),
        sa.Column('refresh_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('revoke_reason', sa.SmallInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        #  Duy nhất trên `token_id`: đây là đường tra ở MỌI lượt gọi đã đăng
        #  nhập, nên nó vừa là ràng buộc đúng đắn vừa là chỉ mục cần có.
        sa.UniqueConstraint('token_id'),
    )
    op.create_index(op.f('ix_tab_login_session_created_at'), 'tab_login_session', ['created_at'])
    op.create_index(op.f('ix_tab_login_session_user_id'), 'tab_login_session', ['user_id'])
    op.create_index(op.f('ix_tab_login_session_expires_at'), 'tab_login_session', ['expires_at'])
    op.create_index(op.f('ix_tab_login_session_revoked_at'), 'tab_login_session', ['revoked_at'])

    op.add_column('tab_user',
                  sa.Column('token_version', sa.SmallInteger(), nullable=False,
                            server_default='1'))


def downgrade() -> None:
    op.drop_column('tab_user', 'token_version')
    op.drop_index(op.f('ix_tab_login_session_revoked_at'), table_name='tab_login_session')
    op.drop_index(op.f('ix_tab_login_session_expires_at'), table_name='tab_login_session')
    op.drop_index(op.f('ix_tab_login_session_user_id'), table_name='tab_login_session')
    op.drop_index(op.f('ix_tab_login_session_created_at'), table_name='tab_login_session')
    op.drop_table('tab_login_session')
