"""gop hai nhanh migration aiusage01 (ai-CR-230) + d0uiact01 (duoc-CR-654) ve mot dau

Revises: aiusage01, d0uiact01

Hai migration cùng mọc từ `jobposrole01` (đẩy song song cùng ngày 20/10/2026). Tệp này chỉ gộp đầu, không đổi bảng.
"""
from typing import Sequence, Union

revision: str = "d0merge01"
down_revision: Union[str, Sequence[str], None] = ("aiusage01", "d0uiact01")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
