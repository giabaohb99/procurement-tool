"""CR-068 - go quyen `export` (Xuat Excel) khoi vai tro `employee` (Nhan su)

Ban dau a7e3c9d15b62 bat `can_export` cho ca vai tro `employee`. Khach chot lai: nhan su yeu cau
thuong KHONG duoc xuat Excel; ai duoc xuat bao cao thi gan them mot VAI TRO RIENG do khach tu tao
va tick o "Xuat" trong man Phan quyen.

a7e3c9d15b62 da bo cap `employee` khoi danh sach cua no, nhung moi truong nao chay ban cu roi
(local + dev) thi DB da bat co -> phai go bang migration nay. Moi truong chua chay bao gio
(prod) thi day chi la no-op.

Chi dung toi vai tro chuan `employee` va dung 2 entity YCMH/YCBG; khong dung toi vai tro tu tao
tay (kho code khac 'employee'), khong doi scope, khong doi quyen khac.

Revision ID: b5c2f8a41d97
Revises: a7e3c9d15b62
Create Date: 2026-08-13 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b5c2f8a41d97'
down_revision: Union[str, None] = 'a7e3c9d15b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ENTITIES = ("purchase_request", "survey_request")


def _set(value: int) -> None:
    for entity in _ENTITIES:
        op.execute(f"""
            UPDATE tab_permission p
            JOIN tab_role r ON r.id = p.role_id
            SET p.can_export = {value}
            WHERE r.code = 'employee' AND p.entity = '{entity}'
        """)


def upgrade() -> None:
    _set(0)


def downgrade() -> None:
    # Tra ve trang thai cua a7e3c9d15b62 ban dau (co cap cho `employee`)
    _set(1)
