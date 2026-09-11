"""gop head main (bao-CR-347/349) voi head erp-v2

Merge revision rong: nhanh main mang chuoi a1c6f80b2d47 -> d2f45a8c9e10
(gia von lo hang nhap khau + cot tab_user.notify_email) vao erp-v2
(head 94f0a2c4e43c - lop nhat ky P1b, 10/09/2026). Khong doi schema,
chi gop 2 head ve 1.

Revision ID: e4b7c2a1d905
Revises: 94f0a2c4e43c, d7f2a9c4e1b8
Create Date: 2026-09-10
"""
from typing import Sequence, Union

revision: str = "e4b7c2a1d905"
#  ⚠️ Cha thu hai doi tu `d2f45a8c9e10` sang `d7f2a9c4e1b8` (11/09/2026). Sau khi
#  `f4d37c7600d0` duoc tra ve dung cha cua no tren main (`d2f45a8c9e10`), chuoi
#  main tro thanh: c9d3e7a1f5b6 -> a1c6f80b2d47 -> d2f45a8c9e10 -> f4d37c7600d0
#  -> 94f0a2c4e43c, va nut gop `d7f2a9c4e1b8` (dau nhanh v2) thanh mot head roi.
#  Nut gop nay la cho hai nhanh nhap lai. Ly do day du: xem khoi chu thich tren
#  `down_revision` cua `f4d37c7600d0`.
down_revision: Union[str, Sequence[str], None] = ("94f0a2c4e43c", "d7f2a9c4e1b8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
