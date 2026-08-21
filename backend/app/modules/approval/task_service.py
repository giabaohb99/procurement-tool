"""HỘP VIỆC CỦA MỘT NGƯỜI (I17) và nhắc hạn (I18).

Hai câu hỏi, hai hàm:

* `viec_cua_toi` — **đang chờ tôi** (màn «Chờ tôi duyệt»). Được mở nhiều nhất
  của cả hệ, nên truy vấn phải bám đúng chỉ mục
  `INDEX(assignee_employee_id, status)` của `tab_approval_task`.
* `viec_da_xu_ly` — **tôi đã quyết định gần đây**, đọc từ dấu vết.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from . import delegation_service, serializer
from .instance_model import (ACTION_APPROVE, ACTION_ESCALATE, ACTION_LABELS,
                             ACTION_REJECT, ACTION_RETURN,
                             INSTANCE_OPEN_STATUSES, INSTANCE_STATUS_LABELS,
                             TASK_PENDING, ApprovalAction, ApprovalInstance,
                             ApprovalTask)


def viec_cua_toi(db: Session, employee_id: int, entity: str = "") -> list[dict]:
    """Mọi thứ đang chờ một người — của cả văn thư lẫn thu mua, gom một chỗ.

    Gồm hai nguồn: việc của chính họ, và việc họ được **ủy quyền bấm thay**.
    Bỏ nguồn thứ hai thì người nhận ủy quyền không thấy việc mình phải làm, và
    ủy quyền thành ra vô dụng đúng lúc cần nhất (người kia đang đi vắng).
    """
    if not employee_id:
        return []

    nguoi_can_lam = {employee_id}
    uy_quyen_theo_nguoi: dict[int, int] = {}
    for row in delegation_service.nguoi_uy_quyen_cho(db, employee_id, entity or ""):
        nguoi_can_lam.add(row.from_employee_id)
        uy_quyen_theo_nguoi[row.from_employee_id] = row.id

    query = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.assignee_employee_id.in_(nguoi_can_lam),
                ApprovalTask.status == TASK_PENDING)
    )
    #  ⚠️ KHÔNG dùng `.nulls_last()`: MySQL 8 không hiểu cú pháp `NULLS LAST` và
    #  ném lỗi ngay ở câu truy vấn — mà bài kiểm chạy trên SQLite thì lại chấp
    #  nhận, nên lỗi này chỉ lộ ra khi gọi thật. `due_at IS NULL` xếp trước cho
    #  cùng kết quả và chạy trên cả hai.
    tasks = query.order_by(ApprovalTask.due_at.is_(None), ApprovalTask.due_at.asc(),
                           ApprovalTask.id.asc()).all()
    if not tasks:
        return []

    phien = {
        row.id: row for row in
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.id.in_({task.instance_id for task in tasks}))
        .all()
    }

    bay_gio = datetime.now()
    ket_qua = []
    for task in tasks:
        instance = phien.get(task.instance_id)
        #  Phiên đã đóng mà việc còn treo là dữ liệu lệch — đừng bày ra, người
        #  dùng bấm vào không làm được gì.
        if instance is None or instance.status not in INSTANCE_OPEN_STATUSES:
            continue
        if entity and instance.entity != entity:
            continue

        dong = serializer.task_out(db, task)
        dong.update({
            "entity": instance.entity,
            "entity_id": instance.entity_id,
            "entity_code": instance.entity_code,
            "entity_title": instance.entity_title,
            "started_by_name": serializer._ten(db, instance.started_by_employee_id),
            "instance_status": instance.status,
            #  Bấm thay ai — hiện thẳng trên dòng để người dùng biết mình đang
            #  làm việc của người khác trước khi bấm, không phải sau.
            "on_behalf_of_id": (task.assignee_employee_id
                                if task.assignee_employee_id != employee_id else None),
            "on_behalf_of_name": (serializer._ten(db, task.assignee_employee_id)
                                  if task.assignee_employee_id != employee_id else ""),
            "delegation_id": uy_quyen_theo_nguoi.get(task.assignee_employee_id),
            "is_overdue": bool(task.due_at and task.due_at < bay_gio),
        })
        ket_qua.append(dong)
    return ket_qua


#  Những việc coi là ĐÃ XỬ LÝ khi nhìn lại. Cố ý KHÔNG gồm «Ý kiến» (ghi ý kiến
#  không đổi trạng thái phiếu) và «Chuyển người xử lý» (đó là việc của quản trị,
#  không phải một quyết định trên phiếu).
HANH_DONG_DA_XU_LY = (ACTION_APPROVE, ACTION_REJECT, ACTION_RETURN)


def viec_da_xu_ly(db: Session, employee_id: int, entity: str = "",
                  ngay: int = 30, gioi_han: int = 50) -> list[dict]:
    """ĐÃ DUYỆT GẦN ĐÂY — nhìn lại những phiếu chính tôi vừa quyết định.

    Đọc từ **dấu vết** (`tab_approval_action`) chứ không từ bảng việc, vì hai lý
    do: dấu vết ghi rõ *đã làm gì* (duyệt / trả lại / từ chối) kèm ý kiến, còn
    bảng việc chỉ có trạng thái cuối; và người **bấm thay** theo ủy quyền phải
    thấy phiếu mình đã ký — dấu vết ghi đúng tên người bấm, bảng việc thì vẫn
    mang tên người được ủy quyền.

    Mặc định 30 ngày gần nhất: đây là màn "nhớ lại xem hôm qua mình ký cái gì",
    không phải sổ tra cứu — muốn tra đủ thì mở dấu vết của chính văn bản.
    """
    if not employee_id:
        return []

    tu_ngay = datetime.now() - timedelta(days=max(1, ngay))
    rows = (
        db.query(ApprovalAction)
        .filter(ApprovalAction.actor_employee_id == employee_id,
                ApprovalAction.action.in_(HANH_DONG_DA_XU_LY),
                ApprovalAction.created_at >= tu_ngay)
        .order_by(ApprovalAction.created_at.desc(), ApprovalAction.id.desc())
        .limit(gioi_han * 3)   # dư ra để còn lọc theo `entity` bên dưới
        .all()
    )
    if not rows:
        return []

    phien = {
        row.id: row for row in
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.id.in_({r.instance_id for r in rows})).all()
    }

    ket_qua = []
    for row in rows:
        instance = phien.get(row.instance_id)
        if instance is None:
            continue
        if entity and instance.entity != entity:
            continue
        ket_qua.append({
            "id": row.id,
            "instance_id": instance.id,
            "entity": instance.entity,
            "entity_id": instance.entity_id,
            "entity_code": instance.entity_code,
            "entity_title": instance.entity_title,
            "node_seq": row.node_seq,
            "node_name": row.node_name,
            "action": row.action,
            "action_label": ACTION_LABELS.get(row.action, str(row.action)),
            "comment": row.comment or "",
            "decided_at": row.created_at,
            #  Trạng thái CUỐI của phiếu — "tôi đã duyệt" khác "phiếu đã xong":
            #  ký xong bước của mình mà phiếu vẫn còn ba bước nữa là chuyện thường.
            "instance_status": instance.status,
            "instance_status_label": INSTANCE_STATUS_LABELS.get(instance.status, ""),
            #  Bấm THAY ai theo ủy quyền — nhật ký ghi cả hai tên, chỗ này cũng vậy.
            "on_behalf_of_name": serializer._ten(db, row.on_behalf_of_id),
        })
        if len(ket_qua) >= gioi_han:
            break
    return ket_qua


def dem_viec_cua_toi(db: Session, employee_id: int) -> int:
    """Con số cho chuông/huy hiệu — đếm bằng chính hàm trên để hai chỗ không lệch."""
    return len(viec_cua_toi(db, employee_id))


def viec_qua_han(db: Session, gio: int = 0) -> list[ApprovalTask]:
    """I18 — việc quá hạn, dùng cho tác vụ nền nhắc và leo cấp."""
    bay_gio = datetime.now()
    return (
        db.query(ApprovalTask)
        .filter(ApprovalTask.status == TASK_PENDING,
                ApprovalTask.due_at.isnot(None),
                ApprovalTask.due_at < bay_gio)
        .order_by(ApprovalTask.due_at.asc())
        .all()
    )


def danh_dau_da_nhac(db: Session, task: ApprovalTask) -> None:
    """Đã nhắc rồi thì thôi — nhắc lại mỗi lần chạy tác vụ nền là spam, và
    người ta tắt thông báo, rồi bỏ lỡ cả những cái quan trọng."""
    task.reminded_at = datetime.now()
    db.flush()


def leo_cap(db: Session, task: ApprovalTask, len_employee_id: int, actor: int) -> None:
    """I18 — quá lâu thì đẩy lên cấp trên, ghi rõ vào dấu vết."""
    from . import instance_service

    instance = db.get(ApprovalInstance, task.instance_id)
    nguoi_cu = task.assignee_employee_id
    task.assignee_employee_id = len_employee_id
    task.escalated_at = datetime.now()
    task.updated_by = actor

    instance_service.ghi_dau_vet(
        db, instance, ACTION_ESCALATE, actor, node_seq=task.node_seq,
        node_name=task.node_name, task_id=task.id,
        actor_employee_id=len_employee_id, on_behalf_of_id=nguoi_cu,
        comment="Quá hạn duyệt — chuyển lên cấp trên",
    )
    db.flush()
