"""cr312_p4_change_log — bảng `tab_change_log`: giá trị TRƯỚC/SAU của từng
trường, do lớp sự kiện ORM ghi (bao-CR-402, phase 4 của bao-CR-312).

Đóng BM-005: hôm nay nhật ký chỉ nói "user 24 đã sửa purchase_order 129", không
nói sửa ô nào và từ bao nhiêu sang bao nhiêu — khoảng trống đó đã phải trả giá
bằng một lần mở thẳng cơ sở dữ liệu ra soi (sự cố 07/09/2026).

Một dòng = MỘT TRƯỜNG với thao tác sửa; thêm/xóa thì chụp cả bản ghi vào
`snapshot_json`. Thiết kế: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md`
mục 4.3.

⚠️ VIẾT TAY, không autogenerate.

Revision ID: d5f7a9c1b3e2
Revises: c3e5a7b9d1f2
Create Date: 2026-09-14 08:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd5f7a9c1b3e2'
down_revision: Union[str, None] = 'c3e5a7b9d1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_change_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        #  QĐ-B (mục 4.5): BINARY(16) chứ không CHAR(36) — cột này có chỉ mục ở
        #  cả ba bảng nhật ký nên mỗi byte nhân lên ba lần.
        sa.Column('request_id', sa.BINARY(16), nullable=True),
        sa.Column('session_id', sa.BigInteger(), nullable=True),
        sa.Column('table_name', sa.String(64), nullable=False, server_default=''),
        sa.Column('row_id', sa.BigInteger(), nullable=False, server_default='0'),
        #  1 thêm · 2 sửa · 3 xóa (`core/logging_codes.CHANGE_OP_*`).
        sa.Column('op', sa.SmallInteger(), nullable=False, server_default='2'),
        sa.Column('field', sa.String(64), nullable=False, server_default=''),
        sa.Column('before_value', sa.Text(), nullable=True),
        sa.Column('after_value', sa.Text(), nullable=True),
        sa.Column('snapshot_json', sa.JSON(), nullable=True),
        sa.Column('is_masked', sa.Boolean(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tab_change_log_created_at', 'tab_change_log', ['created_at'])
    op.create_index('ix_tab_change_log_created_by', 'tab_change_log', ['created_by'])
    #  Dựng lại MỘT lần bấm nút: nối sang tab_request_log + tab_audit_log.
    op.create_index('ix_tab_change_log_request_id', 'tab_change_log', ['request_id'])
    op.create_index('ix_tab_change_log_session_id', 'tab_change_log', ['session_id'])
    op.create_index('ix_tab_change_log_table_name', 'tab_change_log', ['table_name'])
    op.create_index('ix_tab_change_log_row_id', 'tab_change_log', ['row_id'])
    op.create_index('ix_tab_change_log_field', 'tab_change_log', ['field'])
    #  Dựng lịch sử một DÒNG dữ liệu: "đơn giá của dòng 4412 đã qua tay ai".
    op.create_index('ix_change_log_row', 'tab_change_log', ['table_name', 'row_id', 'id'])


def downgrade() -> None:
    op.drop_index('ix_change_log_row', table_name='tab_change_log')
    op.drop_index('ix_tab_change_log_field', table_name='tab_change_log')
    op.drop_index('ix_tab_change_log_row_id', table_name='tab_change_log')
    op.drop_index('ix_tab_change_log_table_name', table_name='tab_change_log')
    op.drop_index('ix_tab_change_log_session_id', table_name='tab_change_log')
    op.drop_index('ix_tab_change_log_request_id', table_name='tab_change_log')
    op.drop_index('ix_tab_change_log_created_by', table_name='tab_change_log')
    op.drop_index('ix_tab_change_log_created_at', table_name='tab_change_log')
    op.drop_table('tab_change_log')
