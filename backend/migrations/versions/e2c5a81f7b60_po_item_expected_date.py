"""Them cot tab_po_item.expected_date (du kien co hang o muc DONG hang cua DMH)

Màn "Tiến độ mua hàng" có cột **Dự kiến nhận** đọc từ `tab_po_delivery.expected_date`,
nhưng KHÔNG chỗ nào trong ứng dụng ghi cột đó — không có ô nhập ở giao diện, không có
phép gán nào ở backend. Cột chỉ có dữ liệu ở 10 dòng nạp tay ngày 13/07/2026, tất cả
cùng một giá trị, nên cột hiển thị số rác.

Nguyên nhân: cùng một cột Excel bị ánh xạ hai lần trong tài liệu yêu cầu — chỗ thì về
`promised_date` ("NCC cam kết giao"), chỗ thì về `expected_date`. Bản được cài đặt thật
là `promised_date`.

Bản này thêm `expected_date` ở mức **DÒNG HÀNG của ĐMH** (`tab_po_item`), là mức đúng
theo nghiệp vụ: dòng YCMH đã có `expected_date` (thời gian dự kiến có hàng), nay dòng
ĐMH có cột đối ứng để chép xuống và cuộn ngược lên.

Cột cũ `tab_po_delivery.expected_date` KHÔNG bị xóa (luật "cơ sở dữ liệu cũ: chỉ thêm,
không sửa") — chỉ dọn 10 giá trị rác về rỗng và đánh dấu bỏ dùng trong model.

Revision ID: e2c5a81f7b60
Revises: c1f7b9d34e02
Create Date: 2026-08-12 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2c5a81f7b60'
down_revision: Union[str, None] = 'c1f7b9d34e02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_col(table: str, col: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in set(insp.get_table_names()):
        return False
    return any(c["name"] == col for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_col("tab_po_item", "expected_date"):
        op.add_column("tab_po_item",
                      sa.Column("expected_date", sa.String(10),
                                nullable=False, server_default=""))
    # Dọn giá trị rác của cột đã bỏ dùng — về rỗng, không xóa cột.
    if _has_col("tab_po_delivery", "expected_date"):
        op.execute("UPDATE tab_po_delivery SET expected_date = '' "
                   "WHERE expected_date IS NOT NULL AND expected_date <> ''")


def downgrade() -> None:
    # Chiều lùi chỉ bỏ cột mới. Giá trị rác đã dọn ở chiều tiến không khôi phục
    # (là dữ liệu rác, khôi phục lại còn hại hơn).
    if _has_col("tab_po_item", "expected_date"):
        op.drop_column("tab_po_item", "expected_date")
