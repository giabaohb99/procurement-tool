"""CR-034 - cap quyen duyet dieu phoi cho vai tro Admin thu mua (pur_admin)

Buoc duyet lan 2 (dieu phoi) doi hoi `approve` tren purchase_request voi pham vi proc/all.
Vai tro pur_admin truoc day chi co `read` nen KHONG thay nut duyet dieu phoi.

Khong sua bang seed.py duoc: theo D-018 seed o moi truong that chi THEM, khong DE
(phan quyen tren DB la nguon su that), nen doi STD_ROLES khong tu ap len dev/prod.
Migration chay dung 1 lan moi moi truong -> dung dung cho viec vá nay.

Chi BAT them co can_approve, KHONG dung toi cac co khac va KHONG doi scope.

Revision ID: d2e6f4b81a37
Revises: c5b1d0a7e934
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'd2e6f4b81a37'
down_revision: Union[str, None] = 'c5b1d0a7e934'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE tab_permission p
        JOIN tab_role r ON r.id = p.role_id
        SET p.can_approve = 1
        WHERE r.code = 'pur_admin' AND p.entity = 'purchase_request'
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE tab_permission p
        JOIN tab_role r ON r.id = p.role_id
        SET p.can_approve = 0
        WHERE r.code = 'pur_admin' AND p.entity = 'purchase_request'
    """)
