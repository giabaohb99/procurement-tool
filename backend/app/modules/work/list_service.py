"""Phân hệ Công việc — danh sách công việc và thành viên của nó (A-01…A-05).

List là ĐƠN VỊ PHÂN QUYỀN CHÍNH: mọi kiểm tra "được đọc/ghi gì" ở các service
khác đều quy về `effective_role` trên một list. Bất biến quan trọng nhất của tệp
này: **mỗi list đúng MỘT chủ sở hữu** — chuyển quyền là thao tác nguyên tử, hạ
người cũ xuống ADMIN và nâng người mới lên OWNER trong cùng một commit.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.work import list_config_service
from app.modules.work import serializer as ser
from app.modules.work.group_service import _get_group_or_403, _with_names
from app.modules.work.membership_service import (CAN_MANAGE, CAN_OWN, Actor,
                                                 assert_can_grant,
                                                 block_if_archived,
                                                 effective_role,
                                                 get_list_or_403,
                                                 visible_list_ids)
from app.modules.work.model import (WorkList, WorkListMember, WorkMemberRole,
                                    WorkTaskStatus)
from app.modules.work.task_model import WorkSection, WorkTask

#  Ba cột seed sẵn lúc tạo list — sửa/xóa/đổi tên tự do sau đó. Có sẵn cột thì
#  người dùng kéo thả được ngay, không phải dựng bảng từ con số không.
DEFAULT_SECTIONS = ("Cần làm", "Đang làm", "Hoàn thành")


def create_list(db: Session, actor: Actor, data) -> dict:
    """Tạo list: người tạo thành OWNER, seed sẵn ba cột mặc định."""
    group_id = data.group_id or None
    if group_id:
        #  Bỏ list vào nhóm của người khác thì phải có quyền quản trị nhóm đó —
        #  không thì ai cũng nhét được list lạ vào nhóm của đội khác.
        _get_group_or_403(db, actor, group_id, CAN_MANAGE)

    lst = WorkList(company_id=actor.company_id, group_id=group_id,
                   name=data.name.strip(), description=data.description or "",
                   color=data.color or "", sort_order=data.sort_order or 0,
                   created_by=actor.user_id, updated_by=actor.user_id)
    db.add(lst)
    db.flush()
    db.add(WorkListMember(company_id=actor.company_id, list_id=lst.id,
                          employee_id=actor.employee_id,
                          role=int(WorkMemberRole.OWNER),
                          created_by=actor.user_id, updated_by=actor.user_id))
    for i, name in enumerate(DEFAULT_SECTIONS):
        db.add(WorkSection(company_id=actor.company_id, list_id=lst.id, name=name,
                           sort_order=i, created_by=actor.user_id,
                           updated_by=actor.user_id))
    #  Độ ưu tiên là một TRƯỜNG TÙY BIẾN nạp sẵn, không còn là cột cứng của task
    #  — xem đầu `label_model.py`.
    list_config_service.seed_system_label_fields(db, lst.id, actor.company_id, actor.user_id)
    db.commit()
    record(db, actor.user_id, "work_task", lst.id, "create", f"Tạo danh sách {lst.name}")
    return ser.list_out(lst, int(WorkMemberRole.OWNER))


def get_lists(db: Session, actor: Actor, include_archived: bool = False,
              with_people: bool = False) -> list[dict]:
    """Mọi list người này thấy, phẳng — ô chọn "chuyển sang list khác" và màn
    liệt kê DỰ ÁN.

    `with_people` mới nạp chủ sở hữu + thành viên: hai thứ đó tốn thêm hai query
    và chỉ màn liệt kê dùng, ô chọn thì không.
    """
    ids = visible_list_ids(db, actor.employee_id, actor.company_id)
    if not ids:
        return []
    q = db.query(WorkList).filter(WorkList.id.in_(ids))
    if not include_archived:
        q = q.filter(WorkList.is_archived == 0)
    rows = q.order_by(WorkList.sort_order, WorkList.id).all()
    counts = _task_counts(db, [r.id for r in rows])
    people = _people_by_list(db, [r.id for r in rows]) if with_people else {}
    return [ser.list_out(r, effective_role(db, actor.employee_id, r.id),
                         *counts.get(r.id, (0, 0)),
                         owner=people.get(r.id, {}).get("owner"),
                         members=people.get(r.id, {}).get("members", []))
            for r in rows]


def _people_by_list(db: Session, list_ids: list[int]) -> dict[int, dict]:
    """Chủ sở hữu + thành viên của từng list — HAI query cho cả bảng.

    Không gọi `get_members` trong vòng lặp: màn liệt kê hay có vài chục dự án,
    mỗi dự án một cặp query là bảng tải hàng giây.
    """
    if not list_ids:
        return {}
    rows = (db.query(WorkListMember)
            .filter(WorkListMember.list_id.in_(list_ids))
            .order_by(WorkListMember.role, WorkListMember.id).all())
    named = _with_names(db, rows)

    out: dict[int, dict] = {lid: {"owner": None, "members": []} for lid in list_ids}
    for member, row in zip(named, rows):
        bucket = out[row.list_id]
        bucket["members"].append(member)
        if bucket["owner"] is None and int(row.role) == int(WorkMemberRole.OWNER):
            bucket["owner"] = member
    return out


def _task_counts(db: Session, list_ids: list[int]) -> dict[int, tuple[int, int]]:
    """`(tổng, đã xong)` số task CHA còn sống của từng list — MỘT query.

    Chỉ đếm `parent_id IS NULL`: việc con không phải một đầu việc của list, nó
    chỉ là gạch đầu dòng bên trong thẻ cha (C-05).

    Đếm luôn vế "đã xong" ở đây thay vì thêm một query riêng: thanh tiến độ trên
    màn liệt kê dự án cần đúng hai con số này.
    """
    from sqlalchemy import case, func

    if not list_ids:
        return {}
    done = func.sum(case((WorkTask.status == int(WorkTaskStatus.DONE), 1), else_=0))
    rows = (db.query(WorkTask.list_id, func.count(WorkTask.id), done)
            .filter(WorkTask.list_id.in_(list_ids),
                    WorkTask.parent_id.is_(None),
                    WorkTask.deleted_at.is_(None))
            .group_by(WorkTask.list_id).all())
    return {lid: (int(total), int(finished or 0)) for lid, total, finished in rows}


def get_list(db: Session, actor: Actor, list_id: int) -> dict:
    lst = get_list_or_403(db, actor, list_id)
    return ser.list_out(lst, effective_role(db, actor.employee_id, list_id),
                        *_task_counts(db, [list_id]).get(list_id, (0, 0)))


def update_list(db: Session, actor: Actor, list_id: int, data) -> dict:
    """Đổi tên/mô tả/màu/lưu trữ/chuyển nhóm — CHỈ chủ list (04 §3)."""
    lst = get_list_or_403(db, actor, list_id, CAN_OWN)
    if data.group_id is not None:
        group_id = data.group_id or None
        if group_id:
            _get_group_or_403(db, actor, group_id, CAN_MANAGE)
        lst.group_id = group_id
    for field in ("name", "description", "color", "sort_order", "is_archived"):
        val = getattr(data, field, None)
        if val is not None:
            setattr(lst, field, val)
    lst.updated_by = actor.user_id
    db.commit()
    record(db, actor.user_id, "work_task", lst.id, "update", f"Sửa danh sách {lst.name}")
    return ser.list_out(lst, int(WorkMemberRole.OWNER))


def archive_list(db: Session, actor: Actor, list_id: int) -> dict:
    """"Xóa" list = lưu trữ (A-01). Việc bên trong còn nguyên, tra cứu được."""
    lst = get_list_or_403(db, actor, list_id, CAN_OWN)
    lst.is_archived = 1
    lst.updated_by = actor.user_id
    db.commit()
    record(db, actor.user_id, "work_task", lst.id, "delete", f"Lưu trữ danh sách {lst.name}")
    return ser.list_out(lst, int(WorkMemberRole.OWNER))


def get_members(db: Session, actor: Actor, list_id: int) -> list[dict]:
    """Ai cũng xem được danh sách thành viên của list mình ở trong — biết mình
    đang làm việc với ai không phải là quyền quản trị."""
    get_list_or_403(db, actor, list_id)
    rows = (db.query(WorkListMember).filter(WorkListMember.list_id == list_id)
            .order_by(WorkListMember.role, WorkListMember.id).all())
    return _with_names(db, rows)


def add_member(db: Session, actor: Actor, list_id: int, data) -> dict:
    lst = get_list_or_403(db, actor, list_id, CAN_MANAGE)
    block_if_archived(lst)
    assert_can_grant(effective_role(db, actor.employee_id, list_id), data.role)

    m = (db.query(WorkListMember)
         .filter(WorkListMember.list_id == list_id,
                 WorkListMember.employee_id == data.employee_id).first())
    if m:
        if int(m.role) == int(WorkMemberRole.OWNER):
            raise HTTPException(400, "Đây là chủ danh sách — dùng chuyển quyền sở hữu")
        m.role = data.role
        m.updated_by = actor.user_id
    else:
        m = WorkListMember(company_id=actor.company_id, list_id=list_id,
                           employee_id=data.employee_id, role=data.role,
                           created_by=actor.user_id, updated_by=actor.user_id)
        db.add(m)
    db.commit()
    record(db, actor.user_id, "work_task", list_id, "update",
           f"Mời nhân sự #{data.employee_id} vào danh sách")
    return _with_names(db, [m])[0]


def remove_member(db: Session, actor: Actor, list_id: int, member_id: int) -> None:
    get_list_or_403(db, actor, list_id, CAN_MANAGE)
    m = db.get(WorkListMember, member_id)
    if not m or m.list_id != list_id:
        raise HTTPException(404, "Không thấy thành viên này")
    if int(m.role) == int(WorkMemberRole.OWNER):
        raise HTTPException(400, "Không gỡ được chủ danh sách — chuyển quyền sở hữu trước")
    db.delete(m)
    db.commit()
    record(db, actor.user_id, "work_task", list_id, "update",
           f"Gỡ nhân sự #{m.employee_id} khỏi danh sách")


def leave_list(db: Session, actor: Actor, list_id: int) -> None:
    """Tự rời list (A-03). Chủ list phải chuyển quyền trước rồi mới rời được."""
    get_list_or_403(db, actor, list_id)
    m = (db.query(WorkListMember)
         .filter(WorkListMember.list_id == list_id,
                 WorkListMember.employee_id == actor.employee_id).first())
    if not m:
        raise HTTPException(400, "Bạn vào danh sách này bằng quyền kế thừa từ nhóm — "
                                 "rời thì rời ở nhóm")
    if int(m.role) == int(WorkMemberRole.OWNER):
        raise HTTPException(400, "Chủ danh sách phải chuyển quyền sở hữu trước khi rời")
    db.delete(m)
    db.commit()


def transfer_ownership(db: Session, actor: Actor, list_id: int, employee_id: int) -> dict:
    """Chuyển quyền sở hữu (A-04) — NGUYÊN TỬ, giữ bất biến "đúng một OWNER".

    Người tạo nghỉ việc mà list mồ côi là kịch bản tài liệu nêu đích danh, nên
    đây là thao tác bắt buộc có chứ không phải tiện ích.
    """
    get_list_or_403(db, actor, list_id, CAN_OWN)
    if employee_id == actor.employee_id:
        raise HTTPException(400, "Bạn đang là chủ danh sách này")

    old = (db.query(WorkListMember)
           .filter(WorkListMember.list_id == list_id,
                   WorkListMember.employee_id == actor.employee_id).first())
    new = (db.query(WorkListMember)
           .filter(WorkListMember.list_id == list_id,
                   WorkListMember.employee_id == employee_id).first())
    if not new:
        new = WorkListMember(company_id=actor.company_id, list_id=list_id,
                             employee_id=employee_id, role=int(WorkMemberRole.ADMIN),
                             created_by=actor.user_id, updated_by=actor.user_id)
        db.add(new)
    #  Hạ trước, nâng sau, một commit: chen commit vào giữa là có khoảnh khắc
    #  list có hai chủ (hoặc không chủ nào).
    if old:
        old.role = int(WorkMemberRole.ADMIN)
        old.updated_by = actor.user_id
    new.role = int(WorkMemberRole.OWNER)
    new.updated_by = actor.user_id
    db.commit()
    record(db, actor.user_id, "work_task", list_id, "update",
           f"Chuyển quyền sở hữu danh sách cho nhân sự #{employee_id}")
    return _with_names(db, [new])[0]
