"""Cấp mặc định Nghỉ phép + Đặt phòng họp cho MỌI vai trò; cấp quản lý duyệt được

Hai phân hệ này là CÔNG CỤ TOÀN DÂN — ai đi làm cũng phải nộp được đơn nghỉ và
đặt được phòng họp. `seed.py` đã khai đúng như vậy trong `STD_ROLES`, nhưng seed
**không ghi đè vai trò đã có trên DB** (D-018), nên trên hệ đang chạy:

  * `room_booking` / `meeting_room` chỉ có ở đúng vai trò `admin` — mọi người
    khác mở menu *Đặt phòng họp* ra là ăn 403 ngay lúc nạp danh sách phòng;
  * quá nửa số vai trò (thu mua, văn thư, hỗ trợ, diễn đàn…) không có khóa
    `leave_*` nào, tức là không thấy cả màn Nghỉ phép;
  * vai trò có khóa thì thiếu `leave_balance` / `holiday`, nên ô «phép còn lại»
    trên form nộp đơn 403 và người dùng nộp đơn trong lúc không biết mình còn
    mấy ngày.

⚠️ **Và một lỗi cặp đôi hành động–phạm vi:** `dept_head` (cùng hai vai trò
Trưởng phòng bản demo) có `leave_request.approve` nhưng phạm vi `own`. Duyệt mà
phạm vi «của mình» thì người duyệt chỉ với tới đơn của CHÍNH HỌ — đúng những đơn
luật I08 không cho họ tự ký. Kết quả: tab «Cần tôi duyệt» rỗng và trưởng phòng
tưởng hệ thống hỏng. Migration này nâng phạm vi lên `dept` cho đúng ý nghĩa.

Chạy lại được: chỉ CHÈN khóa vai trò chưa có, và chỉ NÂNG phạm vi/hành động của
đúng những vai trò quản lý liệt kê dưới đây. Không đụng tới khóa nào khác, không
hạ quyền của ai.

Revision ID: a3f7c1e90d24
Revises: 62d3b3a81136
"""
from alembic import op
import sqlalchemy as sa

revision = "a3f7c1e90d24"
down_revision = "62d3b3a81136"
branch_labels = None
depends_on = None

FLAGS = ("can_read", "can_create", "can_write", "can_delete",
         "can_approve", "can_cancel", "can_print", "can_export")

#  Bộ quyền TỐI THIỂU mọi vai trò phải có, khớp đúng hai vòng `setdefault` trong
#  `seed.py`. Dạng: entity -> (tập hành động, phạm vi).
DEFAULT_PERMS = {
    "leave_request": ({"read", "create", "write", "delete"}, "own"),
    "leave_balance": ({"read"}, "own"),
    #  Danh mục: thiếu là form nộp đơn không dựng nổi ô «Loại nghỉ» và không tính
    #  được số ngày (phải trừ ngày lễ).
    "leave_type": ({"read"}, "all"),
    "holiday": ({"read"}, "all"),
    "room_booking": ({"read", "create", "write", "delete", "cancel"}, "own"),
    "meeting_room": ({"read"}, "all"),
}

#  Vai trò CẤP QUẢN LÝ → duyệt đơn nghỉ phép và phiếu đặt phòng của phạm vi mình.
#  Liệt kê theo MÃ vai trò chứ không đoán theo tên: tên vai trò người dùng sửa
#  được trên màn Phân quyền, mã thì không.
MANAGER_SCOPES = {
    "dept_head": "dept",
    "manager": "dept",             # Trưởng bộ phận (bản demo)
    "manager_purchase": "dept",    # Trưởng phòng Thu mua (bản demo)
    "company_head": "company",
    "pur_manager": "company",      # Quản lý thu mua — quản cả pháp nhân
}
MANAGER_ACTIONS = {
    "leave_request": {"read", "create", "write", "delete", "approve", "export"},
    "room_booking": {"read", "create", "write", "delete", "approve", "cancel"},
}

#  `tab_permission` mang `AuditMixin`: `created_by`/`updated_by` NOT NULL và
#  không có mặc định ở tầng CSDL. `0` = do hệ thống dựng, đúng với thực tế —
#  không có người nào bấm nút cấp bộ quyền này.
ACTOR = 0


def _flags(actions: set) -> dict:
    return {flag: (flag[len("can_"):] in actions) for flag in FLAGS}


def upgrade() -> None:
    conn = op.get_bind()
    roles = conn.execute(sa.text("SELECT id, code FROM tab_role")).mappings().all()
    if not roles:
        return

    existing = {
        (row["role_id"], row["entity"]): row
        for row in conn.execute(sa.text(
            "SELECT role_id, entity, scope, " + ", ".join(FLAGS) +
            " FROM tab_permission WHERE entity IN :ds"
        ).bindparams(sa.bindparam("ds", expanding=True)), {"ds": list(DEFAULT_PERMS)}).mappings()
    }

    columns = ", ".join(FLAGS)
    placeholders = ", ".join(f":{flag}" for flag in FLAGS)
    for role in roles:
        for entity, (actions, scope) in DEFAULT_PERMS.items():
            #  Vai trò quản lý được cấp bộ rộng hơn ngay từ đầu, khỏi chèn rồi sửa.
            if role["code"] in MANAGER_SCOPES and entity in MANAGER_ACTIONS:
                actions, scope = MANAGER_ACTIONS[entity], MANAGER_SCOPES[role["code"]]

            current = existing.get((role["id"], entity))
            if current is None:
                conn.execute(
                    sa.text(
                        f"INSERT INTO tab_permission "
                        f"(role_id, entity, scope, {columns}, created_by, updated_by) "
                        f"VALUES (:role_id, :entity, :scope, {placeholders}, :actor, :actor)"
                    ),
                    {"role_id": role["id"], "entity": entity, "scope": scope,
                     "actor": ACTOR, **_flags(actions)},
                )
                continue

            #  Khóa đã có nhưng THIẾU cờ: bổ sung bằng phép HỢP, không ghi đè.
            #  Chỉ bật thêm, không tắt của ai — quản trị có thể đã tick thêm tay
            #  và phần đó phải còn nguyên. Ví dụ thật: vai trò `employee` trên DB
            #  đang chạy có `leave_request` nhưng thiếu `delete`, nên nhân viên
            #  không xóa nổi đơn NHÁP của chính mình.
            merged = {flag: bool(current[flag]) or _flags(actions)[flag] for flag in FLAGS}
            #  Phạm vi chỉ NỚI cho vai trò quản lý — `approve` mà phạm vi `own`
            #  là quyền duyệt không dùng được (xem phần mở đầu).
            next_scope = (scope if role["code"] in MANAGER_SCOPES and entity in MANAGER_ACTIONS
                         else current["scope"])
            if merged == {flag: bool(current[flag]) for flag in FLAGS} and next_scope == current["scope"]:
                continue
            conn.execute(
                sa.text(
                    "UPDATE tab_permission SET scope = :scope, updated_by = :actor, "
                    + ", ".join(f"{flag} = :{flag}" for flag in FLAGS)
                    + " WHERE role_id = :role_id AND entity = :entity"
                ),
                {"role_id": role["id"], "entity": entity, "scope": next_scope,
                 "actor": ACTOR, **merged},
            )


def downgrade() -> None:
    #  Cố ý KHÔNG gỡ: bộ quyền này là mức tối thiểu để hai phân hệ dùng được, và
    #  sau khi chạy thì quản trị có thể đã tick thêm/bớt ngay trên màn Phân quyền
    #  — xóa sạch theo entity là xóa luôn phần họ vừa khai.
    pass
