"""CR-068 - cap quyen `export` cho vai tro "Gia von nha may" (cost_factory)

Khach yeu cau vi tri Gia von nha may duoc xuat du lieu. Vai tro nay do khach TU TAO tren prod
(khong co trong STD_ROLES, khong co tren dev/local), hien doc duoc: report, supplier, survey.

Trong 3 entity do, chi `report` co cong xuat that (`GET /api/reports/... ` doi hanh dong
`report.export`, nut "Xuat" tren man Bao cao gate bang `can('report','export')`). `supplier` va
`survey` khong co cong xuat nao, bat co o day se la co suong -> khong bat.

4 man cua CR-068 (YCMH/YCBG/DMH/Tien do) thi vai tro nay KHONG doc duoc, nen khong cap `export`
o day: cap them se vo nghia neu khong dong thoi mo quyen XEM cac man do - viec do la mo rong
pham vi du lieu, phai do khach quyet dinh rieng.

Moi truong khong co vai tro `cost_factory` (dev/local) -> UPDATE khong khop dong nao, no-op.

Revision ID: c4a9b2e60f83
Revises: b5c2f8a41d97
Create Date: 2026-08-13 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4a9b2e60f83'
down_revision: Union[str, None] = 'b5c2f8a41d97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _set(value: int) -> None:
    op.execute(f"""
        UPDATE tab_permission p
        JOIN tab_role r ON r.id = p.role_id
        SET p.can_export = {value}
        WHERE r.code = 'cost_factory' AND p.entity = 'report' AND p.can_read = 1
    """)


def upgrade() -> None:
    _set(1)


def downgrade() -> None:
    _set(0)
