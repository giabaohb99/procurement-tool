"""Tách tên entity trong nhật ký của phân hệ Công việc (D-09).

Cả phân hệ từng ghi chung `entity = "work_task"` cho ba loại đối tượng đánh số
độc lập nhau (việc · dự án · nhóm), nên `(entity, entity_id)` không còn trỏ đúng
một thứ. Tab «Hoạt động» lọc theo đúng cặp đó nên phải dọn trước — không dọn thì
dòng "Tạo danh sách X" hiện lẫn vào nhật ký của việc trùng số id.

Nhận dạng dòng cũ bằng MẪU CÂU của `message`: các câu này do
`list_service` / `group_service` / `list_config_service` sinh ra nên cố định,
và mỗi loại một mở đầu riêng, không câu nào lẫn sang câu nào.

Không đảo lại được: sau khi đổi, dòng của việc và dòng của dự án không còn phân
biệt được bằng gì khác, nên `downgrade` gộp tất cả về `work_task` như cũ.

Revision ID: c3a91d47f2b8
Revises: 7e93b1977593
Create Date: 2026-08-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c3a91d47f2b8'
down_revision: Union[str, None] = '7e93b1977593'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  (entity mới, các mẫu LIKE của `message`). Thứ tự không quan trọng: mẫu nào
#  cũng chỉ khớp đúng một nhóm câu.
RULES = [
    ("work_group", ["Tạo nhóm %", "Sửa nhóm %", "Lưu trữ nhóm %"]),
    ("work_group_member", ["Thêm nhân sự #% vào nhóm", "Gỡ nhân sự #% khỏi nhóm"]),
    ("work_list", ["Tạo danh sách %", "Sửa danh sách %", "Lưu trữ danh sách %",
                   "Xếp lại cột: %"]),
    ("work_list_member", ["Mời nhân sự #% vào danh sách", "Gỡ nhân sự #% khỏi danh sách",
                          "Chuyển quyền sở hữu danh sách %"]),
]


def upgrade() -> None:
    conn = op.get_bind()
    for entity, patterns in RULES:
        for pattern in patterns:
            conn.execute(
                sa.text("UPDATE tab_audit_log SET entity = :entity "
                        "WHERE entity = 'work_task' AND message LIKE :pattern"),
                {"entity": entity, "pattern": pattern},
            )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE tab_audit_log SET entity = 'work_task' WHERE entity IN "
                "('work_list', 'work_list_member', 'work_group', 'work_group_member')")
    )
