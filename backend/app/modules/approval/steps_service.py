"""LUỒNG DUYỆT DẠNG NGANG cho một DANH SÁCH chứng từ (CR-260).

Màn danh sách muốn vẽ trên mỗi dòng một dải chấm «chặng 1 → chặng 2 → …» với
chặng đang chờ sáng lên. Câu hỏi đó hỏi cho HAI MƯƠI dòng cùng lúc, nên nó
không dùng lại được `instance_out(..., with_details=True)` — cái đó dựng cho
MỘT phiếu và gọi `_name_of` từng phát.

⚠️ Cả tệp này tồn tại vì một lý do: **N+1**. Hai mươi dòng × (1 truy vấn phiên
+ 1 truy vấn việc + n truy vấn tên) là hơn sáu mươi lượt vào cơ sở dữ liệu cho
một lần mở trang. Ở đây gom lại còn **ba** truy vấn cho cả trang, bất kể bao
nhiêu dòng. Thêm dữ liệu gì vào đây thì giữ đúng luật đó: không truy vấn nào
được nằm trong vòng lặp.

Đọc từ **bảng việc** (`tab_approval_task`) chứ không từ định nghĩa luồng
(`tab_approval_node`): định nghĩa luồng cho biết luồng ĐỊNH đi qua đâu, còn
bảng việc cho biết phiếu THỰC SỰ đã đi qua đâu và ai đã cầm nó. Hai thứ đó lệch
nhau ngay khi có ủy quyền, chuyển người xử lý, hoặc luồng bị sửa giữa chừng —
và người xem cần thứ THỰC SỰ đã xảy ra.
"""
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from .flow_model import NODE_APPROVAL, NODE_CC
from .instance_model import (INSTANCE_APPROVED, INSTANCE_BLOCKED,
                             INSTANCE_OPEN_STATUSES, INSTANCE_REJECTED,
                             INSTANCE_RETURNED, INSTANCE_RUNNING,
                             INSTANCE_STATUS_LABELS, INSTANCE_WITHDRAWN,
                             TASK_APPROVED, TASK_CANCELLED, TASK_PENDING,
                             TASK_REJECTED, TASK_SKIPPED_DUPLICATE, TASK_WAITING,
                             ApprovalInstance, ApprovalTask)

_OPEN_STATUSES = INSTANCE_OPEN_STATUSES

#  Trạng thái MỘT CHẶNG khi vẽ ra dải chấm. Cố ý KHÁC bộ mã trạng thái việc:
#  một chặng có thể có nhiều việc (nhiều người duyệt cùng bước), nên trạng thái
#  chặng là kết luận rút ra từ cả nhóm chứ không phải chép lại của một việc.
STEP_DONE = "done"          # chặng này đã ký xong
STEP_CURRENT = "current"    # ĐANG chờ người ở chặng này — chấm sáng lên
STEP_TODO = "todo"          # chưa tới lượt
STEP_REJECTED = "rejected"  # phiếu dừng hẳn tại đây
STEP_RETURNED = "returned"  # bị trả về người nộp từ chặng này
STEP_CANCELLED = "cancelled"  # phiếu bị rút nên chặng không còn nghĩa


def steps_of_entities(db: Session, entity: str, entity_ids: list[int]) -> dict[int, dict]:
    """Luồng duyệt của nhiều chứng từ cùng loại. Khóa = `entity_id`.

    Chứng từ chưa vào bộ máy thì KHÔNG có khóa trong kết quả — chỗ gọi tự hiểu
    là "không có luồng" và không vẽ gì. Trả một bản ghi rỗng thay vì bỏ khóa sẽ
    khiến màn hình vẽ ra một dải chấm trống, đọc như luồng hỏng.
    """
    ids = [i for i in dict.fromkeys(entity_ids) if i]
    if not ids:
        return {}

    #  (1) Phiên duyệt. Một chứng từ có thể có NHIỀU phiên qua thời gian (bị trả
    #  về rồi nộp lại là một phiên mới) — lấy phiên MỚI NHẤT, vì đó là phiên
    #  đang có hiệu lực. Sắp xếp tăng dần rồi ghi đè để bản cuối cùng thắng.
    instances = (
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.entity == entity,
                ApprovalInstance.entity_id.in_(ids))
        .order_by(ApprovalInstance.id.asc())
        .all()
    )
    latest: dict[int, ApprovalInstance] = {}
    for row in instances:
        latest[row.entity_id] = row
    if not latest:
        return {}

    # (2) Toàn bộ việc của những phiên đó, một lượt.
    tasks = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.instance_id.in_([i.id for i in latest.values()]))
        .order_by(ApprovalTask.node_seq.asc(), ApprovalTask.order_no.asc(),
                  ApprovalTask.id.asc())
        .all()
    )
    by_instance: dict[int, list[ApprovalTask]] = {}
    for task in tasks:
        by_instance.setdefault(task.instance_id, []).append(task)

    # (3) Tên nhân sự — MỘT lượt cho cả trang, không phải mỗi việc một lượt.
    names = _names_of(db, {t.assignee_employee_id for t in tasks}
                      | {i.started_by_employee_id for i in latest.values()})

    return {
        entity_id: _instance_steps(instance, by_instance.get(instance.id, []), names)
        for entity_id, instance in latest.items()
    }


def _names_of(db: Session, employee_ids: set[int]) -> dict[int, str]:
    ids = {i for i in employee_ids if i}
    if not ids:
        return {}
    rows = db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(ids)).all()
    return {row.id: row.full_name for row in rows}


def _instance_steps(instance: ApprovalInstance, tasks: list[ApprovalTask],
                    names: dict[int, str]) -> dict:
    grouped: dict[int, list[ApprovalTask]] = {}
    for task in tasks:
        grouped.setdefault(task.node_seq, []).append(task)

    #  ⚠️ Bảng việc CHỈ có chặng đã mở. Bộ máy dựng việc cho chặng `n` đúng lúc
    #  chặng `n-1` ký xong, nên hỏi riêng bảng việc thì luồng hai chặng vừa gửi
    #  đi chỉ ra MỘT chấm — người xem tưởng ký một cái là xong, trong khi còn
    #  giám đốc chưa duyệt.
    #
    #  Tổng số chặng lấy từ BẢN CHỤP luồng nằm trong chính phiếu
    #  (`flow_snapshot`), không phải từ bảng `tab_approval_node` đang sống: phiếu
    #  chạy theo bản chụp của nó, và quản trị sửa luồng giữa chừng thì bảng sống
    #  đã khác. Bản chụp có sẵn trong bản ghi phiên nên không tốn truy vấn nào.
    planned = _planned_steps(instance)
    all_seqs = sorted(set(grouped) | set(planned))

    steps = [_one_step(seq, grouped.get(seq, []), planned.get(seq), instance, names)
             for seq in all_seqs]
    current = next((s for s in steps if s["state"] == STEP_CURRENT), None)

    return {
        "instance_id": instance.id,
        "status": instance.status,
        "status_label": INSTANCE_STATUS_LABELS.get(instance.status, ""),
        "current_seq": instance.current_seq,
        "started_by_name": names.get(instance.started_by_employee_id, ""),
        #  Câu rút gọn cho ô hẹp / bản đọc màn hình. Dựng ở BACKEND để mọi màn
        #  đọc cùng một câu — chép luật này sang TypeScript là sớm muộn hai chỗ
        #  nói khác nhau.
        "summary": _summary(instance, steps, current),
        "steps": steps,
    }


def _planned_steps(instance: ApprovalInstance) -> dict[int, str]:
    """Tên từng chặng theo bản chụp luồng. Khóa = `seq`.

    Bỏ **bước nhận bản sao** (`NODE_CC`): nó không chặn luồng và không sinh việc
    cho ai, nên vẽ nó thành một chấm là bịa ra một chặng phải chờ mà thực tế
    phiếu chạy thẳng qua.

    Nhiều bước cùng `seq` là các NHÁNH song song — chặng chưa mở thì chưa biết
    nhánh nào được chọn, lấy tên nhánh đầu làm nhãn tạm. Sai nhãn ở chặng chưa
    tới còn đỡ hơn giấu hẳn chặng đó đi.
    """
    from . import flow_service

    planned: dict[int, str] = {}
    for node in flow_service.steps(instance.flow_snapshot):
        if getattr(node, "node_kind", NODE_APPROVAL) == NODE_CC:
            continue
        planned.setdefault(node.seq, node.name or "")
    return planned


def _one_step(seq: int, group: list[ApprovalTask], planned_name: str | None,
              instance: ApprovalInstance, names: dict[int, str]) -> dict:
    statuses = {t.status for t in group}

    #  Thứ tự xét CÓ Ý NGHĨA: một chặng bị từ chối vẫn còn những việc khác ở
    #  trạng thái «đã hủy» (bộ máy dọn việc thừa khi phiếu dừng). Xét «đã hủy»
    #  trước thì chặng bị từ chối lại đọc thành chặng bị hủy, và dải chấm mất
    #  đúng thông tin quan trọng nhất — phiếu chết ở đâu.
    if not group:
        #  Chặng chưa mở. Phiếu còn chạy thì nó là việc SẮP tới; phiếu đã dừng
        #  thì nó là chặng KHÔNG BAO GIỜ tới — vẽ nó "đang chờ" là sai hẳn.
        state = STEP_TODO if instance.status in _OPEN_STATUSES else STEP_CANCELLED
    elif TASK_REJECTED in statuses:
        state = STEP_REJECTED
    elif TASK_PENDING in statuses:
        state = STEP_CURRENT
    elif statuses <= {TASK_APPROVED, TASK_SKIPPED_DUPLICATE}:
        state = STEP_DONE
    elif TASK_WAITING in statuses:
        state = STEP_TODO
    elif TASK_CANCELLED in statuses:
        #  Việc bị hủy vì phiếu bị TRẢ VỀ hay bị RÚT — hai chuyện khác nhau, và
        #  chỉ trạng thái phiên mới phân biệt được.
        state = STEP_RETURNED if instance.status == INSTANCE_RETURNED else STEP_CANCELLED
    else:
        state = STEP_TODO

    return {
        "seq": seq,
        #  Tên từ VIỆC trước, tên từ bản chụp sau: việc mang tên chặng lúc phiếu
        #  thật sự chạy qua, còn bản chụp chỉ là dự định.
        "name": (group[0].node_name if group else "") or planned_name or "",
        "state": state,
        #  Danh sách người, không phải một người: một chặng khai nhiều người
        #  duyệt là chuyện thường (bất kỳ ai trong nhóm, hoặc đủ số phiếu).
        #  Chặng chưa mở thì RỖNG — chưa ai được giao, và đoán trước tên người
        #  duyệt là nói sai ngay khi có ủy quyền hoặc chuyển người xử lý.
        "assignees": [
            {"employee_id": t.assignee_employee_id,
             "name": names.get(t.assignee_employee_id, ""),
             "status": t.status,
             "decided_at": t.decided_at}
            for t in group
        ],
    }


def _summary(instance: ApprovalInstance, steps: list[dict], current: dict | None) -> str:
    total = len(steps)
    if instance.status == INSTANCE_APPROVED:
        return f"Đã duyệt đủ {total}/{total} chặng" if total else "Đã duyệt"
    if instance.status == INSTANCE_REJECTED:
        stopped = next((s for s in steps if s["state"] == STEP_REJECTED), None)
        return f"Dừng ở chặng {stopped['seq']}/{total} · bị từ chối" if stopped else "Bị từ chối"
    if instance.status == INSTANCE_RETURNED:
        return "Đã trả về người nộp để chỉnh sửa"
    if instance.status == INSTANCE_WITHDRAWN:
        return "Người nộp đã rút phiếu"
    if instance.status == INSTANCE_BLOCKED:
        #  Kẹt KHÔNG được đọc thành "đang chờ": không có ai để chờ cả, phải có
        #  người vào khai lại luồng thì phiếu mới nhúc nhích.
        return "Kẹt — chưa tìm được người duyệt"
    if instance.status == INSTANCE_RUNNING and current:
        who = ", ".join(a["name"] for a in current["assignees"] if a["name"])
        vitri = f"Đang ở chặng {current['seq']}/{total}"
        return f"{vitri} · {who}" if who else vitri
    return INSTANCE_STATUS_LABELS.get(instance.status, "")


def pending_assignees(db: Session, entity: str, entity_ids: list[int]) -> dict[int, set[int]]:
    """Ai ĐANG có việc treo trên từng chứng từ. Khóa = `entity_id`.

    Dùng cho luật quyền đọc: người đang được giao ký thì mở được tờ chứng từ dù
    phạm vi dữ liệu của họ không với tới. Xem `leave/approval_bridge._can_read`.
    """
    ids = [i for i in dict.fromkeys(entity_ids) if i]
    if not ids:
        return {}

    rows = (
        db.query(ApprovalInstance.entity_id, ApprovalTask.assignee_employee_id)
        .join(ApprovalTask, ApprovalTask.instance_id == ApprovalInstance.id)
        .filter(ApprovalInstance.entity == entity,
                ApprovalInstance.entity_id.in_(ids),
                ApprovalTask.status == TASK_PENDING)
        .all()
    )
    result: dict[int, set[int]] = {}
    for entity_id, employee_id in rows:
        result.setdefault(entity_id, set()).add(employee_id)
    return result


def has_pending_task(db: Session, entity: str, entity_id: int, employee_id: int) -> bool:
    """Người này có đang được giao ký chứng từ này không?

    ⚠️ Chỉ xét việc **đang treo** (`TASK_PENDING`), không xét việc đã xử lý.
    Ký xong là quyền đọc mở thêm đó đóng lại — người duyệt vẫn xem lại được
    phiếu mình đã ký ở khối «Tôi đã duyệt gần đây», nơi dữ liệu đã lọc sẵn theo
    chính họ. Nới rộng hơn thì mỗi lượt ký lại nới thêm một tờ vào tầm nhìn của
    một người, và phạm vi dữ liệu cứ phình ra theo thời gian mà không ai rà.
    """
    if not employee_id:
        return False
    return db.query(
        db.query(ApprovalTask.id)
        .join(ApprovalInstance, ApprovalInstance.id == ApprovalTask.instance_id)
        .filter(ApprovalInstance.entity == entity,
                ApprovalInstance.entity_id == entity_id,
                ApprovalTask.assignee_employee_id == employee_id,
                ApprovalTask.status == TASK_PENDING)
        .exists()
    ).scalar()
