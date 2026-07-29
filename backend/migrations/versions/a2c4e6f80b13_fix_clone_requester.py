"""fix_clone_requester — sửa người yêu cầu của các phiếu NHÂN BẢN cũ về đúng người tạo

Bug cũ: khi nhân bản YCKS/YCMH, requester/requester_id được COPY từ phiếu gốc trong khi
created_by = người bấm nhân bản -> phiếu hiển thị sai người yêu cầu và cả hai bên đều có
quyền phía yêu cầu. Code đã sửa cho lần clone sau; migration này dọn DATA CŨ.

Nhận diện phiếu clone qua nhật ký audit ("Nhân bản từ ..."), đặt lại:
  requester / requester_id / requester_position / department / head_of_dept = hồ sơ NV của
  người tạo (created_by). CHỈ sửa khi đang lệch (requester_id != NV người tạo) -> idempotent,
  không đụng phiếu đã đúng (kể cả phiếu đã chỉnh tay trước đó).

Revision ID: a2c4e6f80b13
Revises: f3a7c1e9b2d4
Create Date: 2026-07-29 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "a2c4e6f80b13"
down_revision: Union[str, None] = "f3a7c1e9b2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CLONE_PAT = "Nhân bản từ%"

# (entity trong audit, bảng phiếu)
_TARGETS = [
    ("survey_request", "tab_survey_request"),
    ("purchase_request", "tab_purchase_request"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for entity, table in _TARGETS:
        # Lấy phiếu là BẢN SAO (audit "Nhân bản từ") + hồ sơ NV của người tạo, chỉ ca đang LỆCH.
        rows = conn.execute(text(f"""
            SELECT sr.id AS pid, e.id AS emp_id, e.full_name AS emp_name,
                   e.position AS emp_pos, COALESCE(d.name, '') AS dept_name,
                   COALESCE(m.full_name, '') AS head_name
            FROM {table} sr
            JOIN tab_audit_log a
              ON a.entity = :ent AND a.action = 'create'
             AND a.entity_id = sr.id AND a.message LIKE :pat
            JOIN tab_user u ON u.id = sr.created_by
            JOIN tab_employee e ON e.id = u.employee_id
            LEFT JOIN tab_department d ON d.id = e.department_id
            LEFT JOIN tab_employee m ON m.id = d.manager_id
            WHERE sr.requester_id <> e.id
        """), {"ent": entity, "pat": _CLONE_PAT}).fetchall()

        seen = set()
        for r in rows:
            if r.pid in seen:      # audit có thể >1 dòng create -> tránh update lặp
                continue
            seen.add(r.pid)
            conn.execute(text(f"""
                UPDATE {table}
                   SET requester = :rq, requester_id = :rid, requester_position = :pos,
                       department = :dep, head_of_dept = :head
                 WHERE id = :pid
            """), {"rq": r.emp_name or "", "rid": r.emp_id, "pos": r.emp_pos or "",
                   "dep": r.dept_name or "", "head": r.head_name or "", "pid": r.pid})


def downgrade() -> None:
    # Không thể khôi phục người yêu cầu gốc (đã ghi đè) — không hạ cấp.
    pass
