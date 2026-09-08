"""bao_cr319_p3_chi_phi_don_hang_nhap_khau

Bảng chi phí của lô hàng nhập khẩu + nhà cung cấp đại diện cho khoản nộp thuế.

Mọi cột đều khai `server_default`: bảng này còn được ghi bằng script nạp dữ liệu và
truy vấn tay, mà MySQL ở chế độ strict thì cột NOT NULL không mặc định sẽ chết ngay
lần INSERT thiếu cột đầu tiên.

Revision ID: ed610675320b
Revises: c5a81b3f6d24
Create Date: 2026-09-08 09:28:23.514644
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed610675320b'
down_revision: Union[str, None] = 'c5a81b3f6d24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# NCC đại diện cho tiền nộp ngân sách (thuế nhập khẩu, thuế GTGT hàng nhập...). Tạo ở
# migration chứ không ở seed vì đây là DANH MỤC BẮT BUỘC của tính năng: thiếu nó thì
# dòng chi phí thuế không gắn được vào đâu, mà `seed_prod.py` cố ý không nạp danh mục mẫu.
NSNN_CODE = "NSNN"
NSNN_NAME = "Ngân sách nhà nước"


def upgrade() -> None:
    op.create_table(
        'tab_po_import_cost',
        sa.Column('po_id', sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column('cost_type', sa.SmallInteger(), nullable=False, server_default="99"),
        sa.Column('description', sa.String(length=255), nullable=False, server_default=""),
        sa.Column('supplier_code', sa.String(length=50), nullable=False, server_default=""),
        sa.Column('supplier_name', sa.String(length=255), nullable=False, server_default=""),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default="VND"),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=6), nullable=False, server_default="1"),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column('vat', sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"),
        sa.Column('base_amount', sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column('allocation_method', sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column('allocation_target', sa.String(length=50), nullable=False, server_default=""),
        sa.Column('invoice_no', sa.String(length=50), nullable=False, server_default=""),
        sa.Column('invoice_date', sa.String(length=10), nullable=False, server_default=""),
        sa.Column('payment_due_date', sa.String(length=10), nullable=False, server_default=""),
        sa.Column('note', sa.String(length=255), nullable=False, server_default=""),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_po_import_cost_cost_type'), 'tab_po_import_cost', ['cost_type'], unique=False)
    op.create_index(op.f('ix_tab_po_import_cost_po_id'), 'tab_po_import_cost', ['po_id'], unique=False)
    op.create_index(op.f('ix_tab_po_import_cost_supplier_code'), 'tab_po_import_cost', ['supplier_code'], unique=False)

    _seed_state_budget_supplier()


def _seed_state_budget_supplier() -> None:
    """Thêm NCC "Ngân sách nhà nước" nếu chưa có.

    Cột của `tab_supplier` đọc từ CHÍNH database đang chạy chứ không gõ cứng danh sách:
    bảng này đã qua nhiều migration, mỗi môi trường một tập cột hơi khác nhau, gõ cứng
    là hoặc thiếu cột NOT NULL, hoặc gọi tên một cột không tồn tại. Cột NOT NULL nào
    không có mặc định thì lấp theo KIỂU (số về 0, chữ về rỗng).
    """
    conn = op.get_bind()
    already = conn.execute(sa.text("SELECT 1 FROM tab_supplier WHERE code = :c"),
                           {"c": NSNN_CODE}).first()
    if already:
        return

    columns = conn.execute(sa.text(
        "SELECT column_name, data_type, is_nullable, column_default "
        "FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = 'tab_supplier'")).fetchall()

    values = {"code": NSNN_CODE, "name": NSNN_NAME, "supplier_type": "goods",
              "vat": 0, "is_active": 1}
    for name, data_type, nullable, default in columns:
        if name in values or name == "id" or nullable == "YES" or default is not None:
            continue
        t = (data_type or "").lower()
        if t in ("datetime", "timestamp", "date", "time"):
            continue   # bịa ra một mốc thời gian còn tệ hơn là để MySQL báo lỗi
        values[name] = 0 if ("int" in t or t in ("decimal", "numeric", "float", "double", "bit")) else ""

    column_names = ", ".join(f"`{c}`" for c in values)
    params = ", ".join(f":{c}" for c in values)
    conn.execute(sa.text(f"INSERT INTO tab_supplier ({column_names}) VALUES ({params})"), values)


def downgrade() -> None:
    # NCC "Ngân sách nhà nước" CỐ Ý không xóa khi lùi migration: nó có thể đã được gắn
    # vào công nợ / yêu cầu thanh toán thật, xóa đi là bỏ lại chứng từ mồ côi.
    op.drop_index(op.f('ix_tab_po_import_cost_supplier_code'), table_name='tab_po_import_cost')
    op.drop_index(op.f('ix_tab_po_import_cost_po_id'), table_name='tab_po_import_cost')
    op.drop_index(op.f('ix_tab_po_import_cost_cost_type'), table_name='tab_po_import_cost')
    op.drop_table('tab_po_import_cost')
