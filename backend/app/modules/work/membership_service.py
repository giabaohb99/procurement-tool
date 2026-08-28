"""Phân hệ Công việc — TẦNG 2: thành viên. Đây là chỗ giữ bảo mật của cả phân hệ.

`work_task` khai `PUBLIC` ở `core/scoping.SCOPE_FIELDS` vì phạm vi thật của nó là
"theo tư cách THÀNH VIÊN của list", không diễn đạt được bằng cột phòng ban/pháp
nhân của khuôn `apply_scope`. Đổi lại, **mọi đường đọc/ghi phải đi qua tệp này**
(`doc/erp/cong-viec/04-phan-quyen.md` §2). Gọi `db.query(WorkTask)` thẳng ở
controller là mở toang việc của cả công ty — đúng lỗ B-07 từng phải vá.

Hai hàm phải nhớ:

- `visible_list_ids(...)` — tập list người này thấy (mời riêng ∪ kế thừa từ nhóm).
- `effective_role(...)` — vai trò hiệu lực = `min()` của mọi nguồn (Q9: số nhỏ =
  quyền to). Không lưu vào bảng nào; tính mỗi lần cho khỏi lệch.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.work.model import (WorkGroup, WorkGroupMember, WorkList,
                                    WorkListMember, WorkMemberRole)


class Actor:
    """Người đang thao tác, quy về trục NHÂN SỰ của phân hệ.

    `employee_id = 0` (tài khoản kỹ thuật không gắn nhân sự) KHÔNG tham gia list
    được — hệ quả đã chấp nhận ở `02-bang-du-lieu.md` §0.1; họ đi cửa quản trị.
    """

    def __init__(self, user_id: int, employee_id: int, company_id: int):
        self.user_id = user_id
        self.employee_id = employee_id
        self.company_id = company_id


def resolve_actor(db: Session, user) -> Actor:
    from app.modules.employee.model import Employee

    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    return Actor(user.id, emp.id if emp else 0, emp.company_id if emp else 0)


def require_employee(actor: Actor) -> int:
    """Chặn sớm tài khoản không gắn nhân sự, kèm câu nói rõ phải làm gì."""
    if not actor.employee_id:
        raise HTTPException(
            400,
            "Tài khoản này chưa gắn với hồ sơ nhân sự nên không tham gia được "
            "danh sách công việc. Nhờ quản trị gắn nhân sự cho tài khoản.",
        )
    return actor.employee_id


def _covered_group_ids(db: Session, employee_id: int) -> set[int]:
    """Nhóm mà người này là thành viên, CỘNG các nhóm con của chúng (A-09).

    Nhóm chỉ sâu 2 cấp nên một lượt lấy con là đủ — không cần đệ quy.
    """
    direct = {g for (g,) in db.query(WorkGroupMember.group_id)
              .filter(WorkGroupMember.employee_id == employee_id).all()}
    if not direct:
        return set()
    children = {g for (g,) in db.query(WorkGroup.id)
                .filter(WorkGroup.parent_id.in_(direct)).all()}
    return direct | children


def visible_list_ids(db: Session, employee_id: int, company_id: int) -> set[int]:
    """Tập `list_id` người này được thấy.

        mời riêng ở list  ∪  list nằm trong nhóm (hoặc nhóm con) mình là thành viên

    Lọc luôn theo pháp nhân: người của công ty A không thấy list của công ty B,
    kể cả khi có ai đó lỡ mời chéo.
    """
    if not employee_id:
        return set()

    direct = {i for (i,) in db.query(WorkListMember.list_id)
              .filter(WorkListMember.employee_id == employee_id).all()}
    gids = _covered_group_ids(db, employee_id)
    from_groups: set[int] = set()
    if gids:
        from_groups = {i for (i,) in db.query(WorkList.id)
                       .filter(WorkList.group_id.in_(gids)).all()}

    ids = direct | from_groups
    if not ids:
        return set()
    return {i for (i,) in db.query(WorkList.id)
            .filter(WorkList.id.in_(ids), WorkList.company_id == company_id).all()}


def effective_role(db: Session, employee_id: int, list_id: int) -> int | None:
    """Vai trò hiệu lực trên MỘT list. `None` = không phải thành viên.

    Lấy `min()` của: vai trò mời riêng ở list · vai trò ở nhóm chứa list · vai
    trò ở nhóm ÔNG (nhóm cha của nhóm chứa list). Q9 chốt "lấy vai trò cao hơn",
    mà số nhỏ = quyền to nên phép lấy cao nhất chính là `min()`.
    """
    if not employee_id:
        return None
    roles: list[int] = []

    m = (db.query(WorkListMember)
         .filter(WorkListMember.list_id == list_id,
                 WorkListMember.employee_id == employee_id).first())
    if m:
        roles.append(int(m.role))

    lst = db.get(WorkList, list_id)
    if lst and lst.group_id:
        chain = [lst.group_id]
        grp = db.get(WorkGroup, lst.group_id)
        if grp and grp.parent_id:
            chain.append(grp.parent_id)
        rows = (db.query(WorkGroupMember)
                .filter(WorkGroupMember.group_id.in_(chain),
                        WorkGroupMember.employee_id == employee_id).all())
        roles += [int(r.role) for r in rows]

    return min(roles) if roles else None


def group_role(db: Session, employee_id: int, group_id: int) -> int | None:
    """Vai trò hiệu lực trên một NHÓM — của chính nhóm đó hoặc kế thừa từ nhóm cha."""
    if not employee_id or not group_id:
        return None
    chain = [group_id]
    grp = db.get(WorkGroup, group_id)
    if grp and grp.parent_id:
        chain.append(grp.parent_id)
    rows = (db.query(WorkGroupMember)
            .filter(WorkGroupMember.group_id.in_(chain),
                    WorkGroupMember.employee_id == employee_id).all())
    return min((int(r.role) for r in rows), default=None)


#  Ngưỡng vai trò của từng nhóm việc — bảng ở `04-phan-quyen.md` §3.
#  Đọc: "role hiệu lực phải <= ngưỡng" (số nhỏ = quyền to).
CAN_VIEW = int(WorkMemberRole.VIEWER)     # ai là thành viên cũng xem được
CAN_EDIT = int(WorkMemberRole.MEMBER)     # tạo/sửa task, kéo thả, bình luận
CAN_MANAGE = int(WorkMemberRole.ADMIN)    # cột, tag, nhãn, mời/gỡ thành viên
CAN_OWN = int(WorkMemberRole.OWNER)       # đổi tên, lưu trữ, chuyển sở hữu


def get_list_or_403(db: Session, actor: Actor, list_id: int, need: int = CAN_VIEW) -> WorkList:
    """Lấy list theo id kèm kiểm quyền — đường DUY NHẤT để chạm vào một list.

    Trả 403 (không phải 404) cho cả trường hợp không tồn tại lẫn không phải
    thành viên: phân biệt hai cái đó là để lộ "có tồn tại list id này". Đây
    chính là lỗ `get_scoped` kinh điển mà §5.1 của tài liệu phân quyền bắt khóa.
    """
    lst = db.get(WorkList, list_id)
    if not lst or lst.company_id != actor.company_id:
        raise HTTPException(403, "Không có quyền trên danh sách công việc này")
    role = effective_role(db, actor.employee_id, list_id)
    if role is None or role > need:
        raise HTTPException(403, "Không có quyền trên danh sách công việc này")
    return lst


def block_if_archived(lst: WorkList) -> None:
    """List đã lưu trữ: tra cứu thì được, ghi thì không (04 §2)."""
    if lst.is_archived:
        raise HTTPException(400, "Danh sách đã lưu trữ — mở lại trước khi sửa")


def assert_can_grant(actor_role: int, target_role: int) -> None:
    """Không ai cấp được vai trò CAO HƠN vai trò của chính mình (04 §3).

    Thiếu chốt này thì một ADMIN tự nâng người khác lên OWNER rồi nhờ người đó
    nâng lại — vòng lách quyền kinh điển.
    """
    if target_role < actor_role:
        raise HTTPException(403, "Không cấp được vai trò cao hơn vai trò của mình")
    if target_role == int(WorkMemberRole.OWNER):
        raise HTTPException(
            400, "Chỉ chuyển quyền sở hữu bằng thao tác riêng, không gán trực tiếp"
        )
