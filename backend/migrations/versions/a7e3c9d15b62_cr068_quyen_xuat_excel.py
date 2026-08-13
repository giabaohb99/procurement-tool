"""CR-068 - bat quyen `export` (Xuat) cho cac vai tro chuan tren YCMH/YCBG/DMH

Cac endpoint xuat Excel (`/export/xlsx`) doi hanh dong `export` tren tung entity. Ma tran
quyen tren dev/prod da co tu truoc va seed KHONG ghi de (D-018: DB la nguon su that), nen
doi STD_ROLES trong seed.py chi an voi cai moi -> phai vá bang migration, giong CR-034
(migration d2e6f4b81a37).

Chi BAT can_export tren dung 3 entity nghiep vu va dung cac vai tro chuan da CO quyen doc
entity do; khong dung toi co khac, khong doi scope, khong dung toi vai tro tu tao tay.
Pham vi du lieu van do apply_scope quyet dinh -> bat co nay khong mo rong pham vi.

Revision ID: a7e3c9d15b62
Revises: f4d1a6c92e08
Create Date: 2026-08-13 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7e3c9d15b62'
down_revision: Union[str, None] = 'f4d1a6c92e08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (ma vai tro, entity) — khop voi STD_ROLES trong app/seed.py
# KHONG co vai tro `employee` (Nhan su): khach chot nhan su yeu cau thuong khong duoc xuat Excel,
# ai duoc xuat thi gan them mot vai tro rieng tu tao. Ban dau co, da go bang migration b5c2f8a41d97
# cho moi truong da chay ban cu.
_GRANTS = [
    ("dept_head", "purchase_request"), ("dept_head", "survey_request"),
    ("company_head", "purchase_request"), ("company_head", "purchase_order"),
    ("pur_staff", "purchase_request"), ("pur_staff", "survey_request"),
    ("pur_staff", "purchase_order"),
    ("pur_admin", "purchase_request"), ("pur_admin", "survey_request"),
    ("pur_admin", "purchase_order"),
]


def _set(value: int) -> None:
    for role_code, entity in _GRANTS:
        op.execute(f"""
            UPDATE tab_permission p
            JOIN tab_role r ON r.id = p.role_id
            SET p.can_export = {value}
            WHERE r.code = '{role_code}' AND p.entity = '{entity}' AND p.can_read = 1
        """)


def upgrade() -> None:
    _set(1)


def downgrade() -> None:
    _set(0)
