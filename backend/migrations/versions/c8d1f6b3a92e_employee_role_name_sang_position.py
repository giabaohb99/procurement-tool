"""CR-022: chuyen "Vai tro" cua ho so nhan su thanh "Vi tri / Chuc vu"

Ô "Vai trò" ở màn Nhân sự (`tab_employee.role_name`) trước đây vừa là nhãn hiển thị vừa TỰ CẤP
quyền cho tài khoản đăng nhập. Nay nó chỉ còn là chức danh hiển thị và được lưu vào cột
`position` (cột đang in trên phiếu YCMH/YCBG ở ô "Chức vụ"), còn quyền chỉ gán ở màn
"Phân quyền tài khoản".

Migration chỉ CHÉP dữ liệu: nhân sự nào chưa có `position` thì lấy `role_name` làm chức danh.
KHÔNG xóa cột `role_name` (giữ dữ liệu cũ để đối chiếu) và KHÔNG đụng `tab_user_role`
(vai trò đã cấp cho tài khoản giữ nguyên).

Revision ID: c8d1f6b3a92e
Revises: b7e4d2a9c561
Create Date: 2026-08-05 16:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d1f6b3a92e'
down_revision: Union[str, None] = 'b7e4d2a9c561'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        UPDATE tab_employee
           SET position = role_name
         WHERE COALESCE(position, '') = ''
           AND COALESCE(role_name, '') <> ''
    """))


def downgrade() -> None:
    # Không đảo ngược: `role_name` vẫn còn nguyên, chỉ có `position` được điền thêm.
    pass
