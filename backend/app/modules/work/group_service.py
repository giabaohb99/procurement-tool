"""Phân hệ Công việc — nhóm (A-08, A-09) và cây điều hướng bên trái (A-05).

Nhóm chỉ sâu **2 cấp**: cha đã có `parent_id` thì không nhận con. Ràng buộc này
không diễn đạt được bằng khóa ngoại nên chặn ở đây; DB không giữ hộ.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.work import serializer as ser
from app.modules.work.membership_service import (CAN_MANAGE, CAN_OWN, Actor,
                                                 assert_can_grant, group_role,
                                                 visible_list_ids)
from app.modules.work.model import (WorkGroup, WorkGroupMember, WorkList,
                                    WorkMemberRole)


def _get_group_or_403(db: Session, actor: Actor, group_id: int, need: int) -> WorkGroup:
    """Lấy nhóm theo id kèm kiểm quyền. 403 cả khi không tồn tại — xem ghi chú
    ở `membership_service.get_list_or_403` về việc không để lộ id có thật."""
    grp = db.get(WorkGroup, group_id)
    if not grp or grp.company_id != actor.company_id:
        raise HTTPException(403, "Không có quyền trên nhóm này")
    role = group_role(db, actor.employee_id, group_id)
    if role is None or role > need:
        raise HTTPException(403, "Không có quyền trên nhóm này")
    return grp


def create_group(db: Session, actor: Actor, data) -> dict:
    """Tạo nhóm — người tạo thành OWNER (A-04: nhóm không bao giờ mồ côi)."""
    parent_id = data.parent_id or None
    if parent_id:
        parent = _get_group_or_403(db, actor, parent_id, CAN_MANAGE)
        if parent.parent_id:
            raise HTTPException(400, "Nhóm chỉ lồng tối đa 2 cấp")

    grp = WorkGroup(company_id=actor.company_id, parent_id=parent_id,
                    name=data.name.strip(), description=data.description or "",
                    sort_order=data.sort_order or 0,
                    created_by=actor.user_id, updated_by=actor.user_id)
    db.add(grp)
    db.flush()
    db.add(WorkGroupMember(company_id=actor.company_id, group_id=grp.id,
                           employee_id=actor.employee_id,
                           role=int(WorkMemberRole.OWNER),
                           created_by=actor.user_id, updated_by=actor.user_id))
    db.commit()
    record(db, actor.user_id, "work_task", grp.id, "create", f"Tạo nhóm {grp.name}")
    return ser.group_out(grp, int(WorkMemberRole.OWNER))


def update_group(db: Session, actor: Actor, group_id: int, data) -> dict:
    """Đổi tên/mô tả/thứ tự/lưu trữ — CHỈ chủ nhóm (04 §3)."""
    grp = _get_group_or_403(db, actor, group_id, CAN_OWN)
    for field in ("name", "description", "sort_order", "is_archived"):
        val = getattr(data, field, None)
        if val is not None:
            setattr(grp, field, val)
    grp.updated_by = actor.user_id
    db.commit()
    record(db, actor.user_id, "work_task", grp.id, "update", f"Sửa nhóm {grp.name}")
    return ser.group_out(grp, group_role(db, actor.employee_id, group_id))


def archive_group(db: Session, actor: Actor, group_id: int) -> dict:
    """"Xóa" một nhóm = LƯU TRỮ nó (A-01: không xóa cứng, việc cũ còn phải tra).

    Không đụng tới list bên trong: list vẫn sống, vẫn vào được qua đường của nó.
    """
    grp = _get_group_or_403(db, actor, group_id, CAN_OWN)
    grp.is_archived = 1
    grp.updated_by = actor.user_id
    db.commit()
    record(db, actor.user_id, "work_task", grp.id, "delete", f"Lưu trữ nhóm {grp.name}")
    return ser.group_out(grp, int(WorkMemberRole.OWNER))


def list_members(db: Session, actor: Actor, group_id: int) -> list[dict]:
    _get_group_or_403(db, actor, group_id, CAN_MANAGE)
    rows = (db.query(WorkGroupMember)
            .filter(WorkGroupMember.group_id == group_id)
            .order_by(WorkGroupMember.role, WorkGroupMember.id).all())
    return _with_names(db, rows)


def _with_names(db: Session, rows: list) -> list[dict]:
    """Gắn tên + mã nhân sự vào dòng thành viên — MỘT query cho cả danh sách."""
    from app.modules.employee.model import Employee

    ids = [r.employee_id for r in rows if r.employee_id]
    emps = {e.id: e for e in db.query(Employee).filter(Employee.id.in_(ids)).all()} if ids else {}
    out = []
    for r in rows:
        e = emps.get(r.employee_id)
        out.append(ser.member_out(r, e.full_name if e else "", e.code if e else ""))
    return out


def add_member(db: Session, actor: Actor, group_id: int, data) -> dict:
    """Mời một người vào nhóm — vai trò kế thừa xuống mọi list bên trong (A-09)."""
    _get_group_or_403(db, actor, group_id, CAN_MANAGE)
    my_role = group_role(db, actor.employee_id, group_id)
    assert_can_grant(my_role, data.role)

    exists = (db.query(WorkGroupMember)
              .filter(WorkGroupMember.group_id == group_id,
                      WorkGroupMember.employee_id == data.employee_id).first())
    if exists:
        exists.role = data.role
        exists.updated_by = actor.user_id
        db.commit()
        return _with_names(db, [exists])[0]

    m = WorkGroupMember(company_id=actor.company_id, group_id=group_id,
                        employee_id=data.employee_id, role=data.role,
                        created_by=actor.user_id, updated_by=actor.user_id)
    db.add(m)
    db.commit()
    record(db, actor.user_id, "work_task", group_id, "update",
           f"Thêm nhân sự #{data.employee_id} vào nhóm")
    return _with_names(db, [m])[0]


def remove_member(db: Session, actor: Actor, group_id: int, member_id: int) -> None:
    """Gỡ thành viên. Chủ nhóm KHÔNG gỡ được — chuyển quyền sở hữu trước."""
    _get_group_or_403(db, actor, group_id, CAN_MANAGE)
    m = db.get(WorkGroupMember, member_id)
    if not m or m.group_id != group_id:
        raise HTTPException(404, "Không thấy thành viên này")
    if int(m.role) == int(WorkMemberRole.OWNER):
        raise HTTPException(400, "Không gỡ được chủ nhóm — chuyển quyền sở hữu trước")
    db.delete(m)
    db.commit()
    record(db, actor.user_id, "work_task", group_id, "update",
           f"Gỡ nhân sự #{m.employee_id} khỏi nhóm")


def sidebar(db: Session, actor: Actor, include_archived: bool = False) -> dict:
    """Cây điều hướng bên trái (A-05): nhóm → nhóm con → list, kèm list đứng lẻ.

    Chỉ trả những gì người này THẤY: list lấy từ `visible_list_ids`, còn nhóm chỉ
    hiện khi bản thân là thành viên hoặc có ít nhất một list thấy được bên trong
    — nhóm rỗng của người khác không việc gì phải lộ tên ra.
    """
    ids = visible_list_ids(db, actor.employee_id, actor.company_id)
    q = db.query(WorkList).filter(WorkList.id.in_(ids)) if ids else None
    lists = q.order_by(WorkList.sort_order, WorkList.id).all() if q is not None else []
    if not include_archived:
        lists = [x for x in lists if not x.is_archived]

    my_groups = {g for (g,) in db.query(WorkGroupMember.group_id)
                 .filter(WorkGroupMember.employee_id == actor.employee_id).all()}
    group_ids = my_groups | {x.group_id for x in lists if x.group_id}
    groups = (db.query(WorkGroup).filter(WorkGroup.id.in_(group_ids))
              .order_by(WorkGroup.sort_order, WorkGroup.id).all()) if group_ids else []
    if not include_archived:
        groups = [g for g in groups if not g.is_archived]
    #  Nhóm cha của một nhóm thấy được cũng phải có mặt, không thì nhánh con
    #  treo lơ lửng không có chỗ móc vào trên giao diện.
    parent_ids = {g.parent_id for g in groups if g.parent_id} - {g.id for g in groups}
    if parent_ids:
        groups += db.query(WorkGroup).filter(WorkGroup.id.in_(parent_ids)).all()

    by_group: dict[int, list] = {}
    loose = []
    for x in lists:
        (by_group.setdefault(x.group_id, []) if x.group_id else loose).append(x)

    def node(g: WorkGroup) -> dict:
        out = ser.group_out(g, group_role(db, actor.employee_id, g.id))
        out["lists"] = [ser.list_out(x, None) for x in by_group.get(g.id, [])]
        out["children"] = [node(c) for c in groups if c.parent_id == g.id]
        return out

    roots = [node(g) for g in groups if not g.parent_id]
    return {"groups": roots, "lists": [ser.list_out(x, None) for x in loose]}
