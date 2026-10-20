"""gop hai nhanh migration d0feat01 (duoc-CR-655) + d1cap01 (duoc-CR-656) ve mot dau

Revises: d0feat01, d1cap01

Hai migration cùng mọc từ `d0merge01` (làm song song ngày 20/10/2026). Tệp này chỉ gộp đầu, không đổi bảng.
"""
from typing import Sequence, Union

revision: str = "d01merge01"
down_revision: Union[str, Sequence[str], None] = ("d0feat01", "d1cap01")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
