"""Chuông MỜI vào dự án / nhóm dự án và nút MỜI LẠI (duoc-CR-783, anh Được 19/11/2026).

Trước đây mời người vào dự án hay nhóm chỉ ghi một dòng thành viên, không có chuông nào kêu: người được mời không biết
mình vừa có thêm dự án, phải tự mò thấy trong cây bên trái. Nay:

- mời MỚI vào dự án / nhóm, hoặc được gán sẵn lúc tạo dự án trong nhóm → chuông "Bạn được mời vào …";
- đổi vai trò người đã có thì KHÔNG báo (không phải lời mời);
- nút *Mời lại* ở dòng thành viên gửi lại chuông cho đúng người đó — người được mời lỡ bỏ qua chuông lần đầu.

Theo luật chung của `notify_service`: không báo cho chính người thao tác, nhân sự chưa có tài khoản thì bỏ qua, chuông hỏng
không làm hỏng thao tác chính (lời mời đã lưu xong rồi mới báo).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.work import notify_service as notify
from app.modules.work.membership_service import CAN_MANAGE, Actor, get_list_or_403
from app.modules.work.model import WorkGroup, WorkGroupMember, WorkList, WorkListMember

#  Nhóm không có trang riêng — chuông mời vào nhóm mở màn danh sách dự án (có nút lọc theo nhóm).
GROUP_LINK = "/project/lists"
LIST_LINK = "/project/lists/{id}"


def notify_invited(db: Session, actor: Actor, employee_ids, *, kind: str, name: str, link: str,
                   again: bool = False, background_tasks=None) -> int:
    """Gửi chuông mời cho các NHÂN SỰ. `kind` là "dự án" / "nhóm dự án". Trả số người đã được báo."""
    try:
        from app.core.auth import user_has_permission
        from app.modules.user.model import User

        targets = notify._user_ids_of_employees(db, employee_ids)
        candidates = [u for u, e in targets.items() if u != actor.user_id and e != actor.employee_id]
        #  Cùng cổng với chuông giao việc (`notify.audience_user_ids`): thiếu `work_task.read` thì bấm vào là 403 —
        #  một lời mời không mở được còn tệ hơn không có lời mời.
        users = db.query(User).filter(User.id.in_(candidates)).all() if candidates else []
        user_ids = [u.id for u in users if user_has_permission(db, u, "work_task", "read")]
        who = notify._actor_name(db, actor)
    except Exception:
        db.rollback()
        notify.logger.warning("Không tra được người nhận chuông mời %s", link, exc_info=True)
        return 0
    title = f"Nhắc lời mời vào {kind}" if again else f"Bạn được mời vào {kind}"
    body = f"{who} {'nhắc bạn tham gia' if again else 'đã mời bạn vào'} {kind} {notify._clip(name)}"
    return notify.send_bell_users(db, user_ids, title, body, link, actor, background_tasks)


def notify_list_invited(db: Session, actor: Actor, lst: WorkList, employee_ids, again: bool = False,
                        background_tasks=None) -> int:
    return notify_invited(db, actor, employee_ids, kind="dự án", name=lst.name,
                          link=LIST_LINK.format(id=lst.id), again=again, background_tasks=background_tasks)


def notify_group_invited(db: Session, actor: Actor, grp: WorkGroup, employee_ids, again: bool = False,
                         background_tasks=None) -> int:
    return notify_invited(db, actor, employee_ids, kind="nhóm dự án", name=grp.name, link=GROUP_LINK,
                          again=again, background_tasks=background_tasks)


def reinvite_list_member(db: Session, actor: Actor, list_id: int, member_id: int, background_tasks=None) -> int:
    """Nút *Mời lại* ở hộp Quản lý dự án — cùng quyền với mời (quản trị dự án trở lên)."""
    lst = get_list_or_403(db, actor, list_id, CAN_MANAGE)
    m = db.get(WorkListMember, member_id)
    if not m or m.list_id != list_id:
        raise HTTPException(404, "Không thấy thành viên này")
    return notify_list_invited(db, actor, lst, [m.employee_id], again=True, background_tasks=background_tasks)


def reinvite_group_member(db: Session, actor: Actor, group_id: int, member_id: int, background_tasks=None) -> int:
    """Nút *Mời lại* ở hộp Quản lý nhóm dự án — cùng quyền với mời (quản trị nhóm trở lên)."""
    from app.modules.work.group_service import _get_group_or_403

    grp = _get_group_or_403(db, actor, group_id, CAN_MANAGE)
    m = db.get(WorkGroupMember, member_id)
    if not m or m.group_id != group_id:
        raise HTTPException(404, "Không thấy thành viên này")
    return notify_group_invited(db, actor, grp, [m.employee_id], again=True, background_tasks=background_tasks)
