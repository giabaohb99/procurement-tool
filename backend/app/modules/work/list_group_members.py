"""Chép thành viên NHÓM dự án thành thành viên riêng của một dự án vừa tạo trong nhóm (duoc-CR-783).

Người trong nhóm vốn đã có quyền trên mọi dự án bên trong nhờ kế thừa (A-09, `effective_role`), nhưng KHÔNG có dòng ở
`tab_work_list_member`: hộp Quản lý dự án không liệt kê họ, các chỗ đọc thành viên dự án (ô chọn người phụ trách…) không
thấy họ. Anh Được muốn tạo dự án trong nhóm là thành viên nhóm vào luôn, có ô tick hỏi trước (bật sẵn) và chọn được người.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkGroup, WorkGroupMember, WorkListMember, WorkMemberRole


def get_group_chain_roles(db: Session, group_id: int) -> dict[int, int]:
    """Vai trò của từng người trong nhóm và nhóm cha (cây chỉ hai cấp) — lấy vai trò CAO nhất, tức số nhỏ nhất."""
    chain = [group_id]
    grp = db.get(WorkGroup, group_id)
    if grp and grp.parent_id:
        chain.append(grp.parent_id)
    roles: dict[int, int] = {}
    for m in db.query(WorkGroupMember).filter(WorkGroupMember.group_id.in_(chain)).all():
        roles[m.employee_id] = min(roles.get(m.employee_id, int(m.role)), int(m.role))
    return roles


def copy_group_members_to_list(db: Session, actor: Actor, list_id: int, group_id: int,
                               employee_ids: list[int]) -> int:
    """Thêm những người được chọn (phải là thành viên nhóm) vào dự án, giữ vai trò ở nhóm. Trả về số người đã thêm.

    - Chủ nhóm vào dự án làm QUẢN TRỊ: dự án giữ bất biến đúng một chủ là người tạo (`transfer_ownership`).
    - Người tạo đã là chủ dự án nên bỏ qua.
    - Không kiểm `assert_can_grant`: người đó vốn đã có đúng vai trò này trên dự án qua nhóm, chép ra không nâng quyền ai.
    - Id không thuộc nhóm thì CHẶN 400 — đường này không được thành lối mời người lạ vào dự án mà bỏ qua bước mời.
    Không tự commit: chạy trong cùng giao dịch tạo dự án.
    """
    roles = get_group_chain_roles(db, group_id)
    wanted = {i for i in employee_ids if i and i != actor.employee_id}
    outsiders = wanted - roles.keys()
    if outsiders:
        raise HTTPException(400, "Chỉ gán được người đang là thành viên của nhóm dự án")
    for employee_id in sorted(wanted):
        role = max(roles[employee_id], int(WorkMemberRole.ADMIN))
        db.add(WorkListMember(company_id=actor.company_id, list_id=list_id, employee_id=employee_id,
                              role=role, created_by=actor.user_id, updated_by=actor.user_id))
    return len(wanted)
