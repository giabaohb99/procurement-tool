"""them danh muc muc mat do khan

Bảng `tab_security_level` — bảy dòng Mức mật / Độ khẩn trước đây khai cứng trong
mã (`security-level.ts` bên giao diện và `SECRECY_LABELS` trong
`document/export.py`), nay là danh mục thêm sửa xóa được.

**Không đụng vào `tab_document.secrecy_level` / `.urgency`.** Hai cột đó vẫn là
số trần, không chuyển sang khóa ngoại: chúng đang mang số của HAI thang khác nhau
nên không trỏ nổi vào một bảng, và quan trọng hơn — mọi điều kiện luồng duyệt đã
cấu hình đang lưu chính con số ấy dạng chuỗi JSON. Đổi số là chúng lặng lẽ thôi
khớp. Chống dữ liệu mồ côi bằng chốt chặn lúc xóa
(`doc_catalog/security_level_guard.py`), không bằng ràng buộc của MySQL.

Bảy dòng dữ liệu do `seed_document_phase1` nạp (insert-only), không nạp ở đây:
seed chạy mỗi lần khởi động nên đó là chỗ duy nhất, khỏi hai nơi cùng ghi.

Revision ID: ebcfc25db193
Revises: 08d4f35a52a5
Create Date: 2026-08-22 04:45:12.302020
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ebcfc25db193'
down_revision: Union[str, None] = '08d4f35a52a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #  ⚠️ Bản autogenerate còn kèm ~50 dòng `alter_column ... nullable=False` cho
    #  `tab_comment_*`, `tab_ticket*`… Đó là ĐỘ LỆCH CÓ SẴN giữa model và DB
    #  thật, không liên quan gì tới việc này — đã bỏ hết. Gộp vào đây thì một
    #  migration mang tên "thêm danh mục mức mật" lại đi sửa ràng buộc của phân
    #  hệ khác, và lúc có sự cố không ai lần ra.
    op.create_table(
        'tab_security_level',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        # 1 mức mật · 2 độ khẩn
        sa.Column('kind', sa.SmallInteger(), nullable=False),
        # Con số nằm trên `tab_document.secrecy_level` / `.urgency`, và cũng
        # chính là thứ bậc — càng lớn càng nghiêm / càng gấp.
        sa.Column('value', sa.SmallInteger(), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        # Mặc định ghi rõ ở migration, không để mã ứng dụng tự đoán
        # (quy ước `van-thu/04` mục 12).
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        # Khóa nghiệp vụ. Không đặt `unique` lên riêng `value`: hai thang dùng
        # chung dải số nhỏ (Công khai = 1 và Thường = 1).
        sa.UniqueConstraint('kind', 'value', name='uq_security_level_kind_value'),
    )


def downgrade() -> None:
    op.drop_table('tab_security_level')
