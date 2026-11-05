"""gop hai nhanh migration: thanh toan nghi phep (duoc-CR-719) va gui lai thu / sao luu hai phan (bao-CR-727, 732)

Revision ID: mrg719x732
Revises: lvenc719, bkpart732

lvenc719 viet tren may local khi head con la hqx718b; trong luc do erp-v2 da them emresend727 -> bkpart732 cung
noi vao hqx718b, thanh hai head. Migration nay chi noi hai nhanh lai, khong doi bang nao: DB nao da chay
nhanh nao thi chi chay not nhanh con lai.
"""
from typing import Sequence, Union

revision: str = "mrg719x732"
down_revision: Union[str, Sequence[str], None] = ("lvenc719", "bkpart732")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
