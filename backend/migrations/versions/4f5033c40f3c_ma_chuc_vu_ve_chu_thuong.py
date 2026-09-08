"""ma chuc vu ve chu thuong

Hạ toàn bộ `tab_job_position.code` về CHỮ THƯỜNG (khách chốt 08/09/2026).

Migration `c5e2a8b31d47` dựng mã gợi nhớ từ tên và viết HOA (`TRUONG-BO-PHAN`);
từ nay mã chức vụ luôn chữ thường. Luật ép ở tầng schema
(`position_schema._code_lowercase`) nên mã mới đã đúng — dòng này chỉ dọn những
dòng đã sinh ra trước đó.

⚠️ Đổi mã là việc **bình thường CHỈ vì tính năng chưa ra khỏi nhánh `erp-v2`**:
mã chức vụ vốn không sửa được sau khi tạo, vì tệp CSV nhập/xuất trỏ vào dòng
bằng mã. Chưa môi trường nào phát ra tệp như vậy nên chưa có gì để trỏ sai. Sau
này thì đừng lặp lại kiểu đổi hàng loạt này.

⚠️ Không đụng `tab_employee.position_id` / `position`: hồ sơ nối vào danh mục
bằng **khóa**, không bằng mã — nên đổi mã không làm hồ sơ nào mồ côi.

Revision ID: 4f5033c40f3c
Revises: 625411af912e
Create Date: 2026-09-08 08:57:10.236525
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f5033c40f3c'
down_revision: Union[str, None] = '625411af912e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    #  ⚠️ Kiểm TRÙNG trước khi ghi. Cột `code` có ràng buộc duy nhất, mà MySQL
    #  đối chiếu không phân biệt hoa thường nên hai dòng `TP` và `tp` vốn không
    #  cùng tồn tại được — nhưng đừng tin vào đó: một môi trường đặt collation
    #  phân biệt hoa thường thì `UPDATE` này đâm vào ràng buộc và migration chết
    #  giữa chừng, để lại nửa bảng đã đổi. Thà dừng trước với câu nói rõ lý do.
    rows = conn.execute(sa.text("SELECT id, code FROM tab_job_position")).fetchall()
    lowered = [(r[0], (r[1] or "").lower()) for r in rows]
    seen: dict[str, int] = {}
    clashes = []
    for pid, code in lowered:
        if code in seen:
            clashes.append(f"{code!r} (id {seen[code]} và {pid})")
        seen[code] = pid
    if clashes:
        raise RuntimeError(
            "Hạ chữ thường sẽ làm trùng mã chức vụ: " + ", ".join(clashes) +
            ". Sửa tay cho khác nhau rồi chạy lại.")

    for pid, code in lowered:
        conn.execute(
            sa.text("UPDATE tab_job_position SET code = :code WHERE id = :id"),
            {"code": code, "id": pid})


def downgrade() -> None:
    #  KHÔNG dựng lại được dạng hoa/thường cũ: `TRUONG-BO-PHAN` và
    #  `Truong-Bo-Phan` hạ xuống ra cùng một chuỗi, nên không có đường về. Viết
    #  hoa toàn bộ là bịa ra một trạng thái chưa từng tồn tại, còn tệ hơn.
    pass
