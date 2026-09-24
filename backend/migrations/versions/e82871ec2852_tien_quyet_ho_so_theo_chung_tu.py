"""tien_quyet_ho_so_tren_to_ho_so

Cột `depends` (JSON) của HỒ SƠ TIÊN QUYẾT nằm trên **`tab_dossier`** — tức trên
chính TỜ GIẤY, khai một lần cho cả kho (đại ca chốt 21/09/2026).

⚠️ Bản đầu của migration này đặt cột lên `tab_dossier_progress` (ràng buộc theo
từng phiếu). Đã đổi TRƯỚC KHI ra khỏi máy local nên không có dữ liệu nào để dời;
`drop_column` dưới đây chỉ để dọn máy nào đã lỡ chạy bản đầu.

Trình tự giấy tờ của công ty là MỘT: đơn mua hàng chỉ phát hành sau khi hợp đồng
ký xong, ở mọi thương vụ. Nhưng «xong» thì vẫn theo từng phiếu
(`tab_dossier_progress.status`), nên *«tờ này có đang khóa không»* vẫn là câu hỏi
của riêng từng phiếu — ràng buộc dùng chung, trạng thái riêng. Xem
`app/modules/dossier/depends_service.py`.

Revision ID: e82871ec2852
Revises: b92c74d55ee7
Create Date: 2026-09-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e82871ec2852'
down_revision: Union[str, None] = 'b92c74d55ee7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _co_cot(bang: str, cot: str) -> bool:
    """Máy nào đã chạy bản đầu thì có cột, máy mới thì không — hỏi rồi mới dọn."""
    bind = op.get_bind()
    return cot in {c["name"] for c in sa.inspect(bind).get_columns(bang)}


def upgrade() -> None:
    #  `nullable=True`: hồ sơ lập trước ngày này không có giá trị nào để điền, và
    #  `NULL` với `[]` được đọc như nhau ở `Dossier.depend_list` (`or []`). Ép
    #  NOT NULL thì phải UPDATE cả bảng trong cùng một migration.
    if not _co_cot('tab_dossier', 'depends'):
        op.add_column('tab_dossier', sa.Column('depends', sa.JSON(), nullable=True))

    if _co_cot('tab_dossier_progress', 'depends'):
        op.drop_column('tab_dossier_progress', 'depends')


def downgrade() -> None:
    #  ⚠️ Hỏi trước khi dọn. Máy nào đã chạy BẢN ĐẦU của chính migration này
    #  (cột nằm trên `tab_dossier_progress`) thì `tab_dossier` không có cột nào
    #  để bỏ, và `DROP COLUMN` trên một cột không tồn tại làm hỏng cả lượt
    #  downgrade — kẹt ở giữa, không tiến không lùi được.
    if _co_cot('tab_dossier', 'depends'):
        op.drop_column('tab_dossier', 'depends')
