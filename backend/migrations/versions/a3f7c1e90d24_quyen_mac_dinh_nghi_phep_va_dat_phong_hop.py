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

CO = ("can_read", "can_create", "can_write", "can_delete",
      "can_approve", "can_cancel", "can_print", "can_export")

#  Bộ quyền TỐI THIỂU mọi vai trò phải có, khớp đúng hai vòng `setdefault` trong
#  `seed.py`. Dạng: entity -> (tập hành động, phạm vi).
MAC_DINH = {
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
QUAN_LY = {
    "dept_head": "dept",
    "manager": "dept",             # Trưởng bộ phận (bản demo)
    "manager_purchase": "dept",    # Trưởng phòng Thu mua (bản demo)
    "company_head": "company",
    "pur_manager": "company",      # Quản lý thu mua — quản cả pháp nhân
}
QUAN_LY_THEM = {
    "leave_request": {"read", "create", "write", "delete", "approve", "export"},
    "room_booking": {"read", "create", "write", "delete", "approve", "cancel"},
}

#  `tab_permission` mang `AuditMixin`: `created_by`/`updated_by` NOT NULL và
#  không có mặc định ở tầng CSDL. `0` = do hệ thống dựng, đúng với thực tế —
#  không có người nào bấm nút cấp bộ quyền này.
ACTOR = 0


def _co(actions: set) -> dict:
    return {ten: (ten[len("can_"):] in actions) for ten in CO}


def upgrade() -> None:
    conn = op.get_bind()
    roles = conn.execute(sa.text("SELECT id, code FROM tab_role")).mappings().all()
    if not roles:
        return

    dang_co = {
        (row["role_id"], row["entity"]): row
        for row in conn.execute(sa.text(
            "SELECT role_id, entity, scope, " + ", ".join(CO) +
            " FROM tab_permission WHERE entity IN :ds"
        ).bindparams(sa.bindparam("ds", expanding=True)), {"ds": list(MAC_DINH)}).mappings()
    }

    cot = ", ".join(CO)
    tham_so = ", ".join(f":{ten}" for ten in CO)
    for role in roles:
        for entity, (actions, scope) in MAC_DINH.items():
            #  Vai trò quản lý được cấp bộ rộng hơn ngay từ đầu, khỏi chèn rồi sửa.
            if role["code"] in QUAN_LY and entity in QUAN_LY_THEM:
                actions, scope = QUAN_LY_THEM[entity], QUAN_LY[role["code"]]

            hien_tai = dang_co.get((role["id"], entity))
            if hien_tai is None:
                conn.execute(
                    sa.text(
                        f"INSERT INTO tab_permission "
                        f"(role_id, entity, scope, {cot}, created_by, updated_by) "
                        f"VALUES (:role_id, :entity, :scope, {tham_so}, :actor, :actor)"
                    ),
                    {"role_id": role["id"], "entity": entity, "scope": scope,
                     "actor": ACTOR, **_co(actions)},
                )
                continue

            #  Khóa đã có nhưng THIẾU cờ: bổ sung bằng phép HỢP, không ghi đè.
            #  Chỉ bật thêm, không tắt của ai — quản trị có thể đã tick thêm tay
            #  và phần đó phải còn nguyên. Ví dụ thật: vai trò `employee` trên DB
            #  đang chạy có `leave_request` nhưng thiếu `delete`, nên nhân viên
            #  không xóa nổi đơn NHÁP của chính mình.
            co_moi = {ten: bool(hien_tai[ten]) or _co(actions)[ten] for ten in CO}
            #  Phạm vi chỉ NỚI cho vai trò quản lý — `approve` mà phạm vi `own`
            #  là quyền duyệt không dùng được (xem phần mở đầu).
            scope_moi = (scope if role["code"] in QUAN_LY and entity in QUAN_LY_THEM
                         else hien_tai["scope"])
            if co_moi == {ten: bool(hien_tai[ten]) for ten in CO} and scope_moi == hien_tai["scope"]:
                continue
            conn.execute(
                sa.text(
                    "UPDATE tab_permission SET scope = :scope, updated_by = :actor, "
                    + ", ".join(f"{ten} = :{ten}" for ten in CO)
                    + " WHERE role_id = :role_id AND entity = :entity"
                ),
                {"role_id": role["id"], "entity": entity, "scope": scope_moi,
                 "actor": ACTOR, **co_moi},
            )


def downgrade() -> None:
    #  Cố ý KHÔNG gỡ: bộ quyền này là mức tối thiểu để hai phân hệ dùng được, và
    #  sau khi chạy thì quản trị có thể đã tick thêm/bớt ngay trên màn Phân quyền
    #  — xóa sạch theo entity là xóa luôn phần họ vừa khai.
    pass
