"""MÁY CHẠY PHIÊN DUYỆT — mở chặng, đi tiếp, kết thúc (I04–I08, I15, I21).

Phần "người dùng bấm gì" nằm ở `action_service`. Ở đây chỉ có *phiếu đang ở đâu
và đi đâu tiếp*.
"""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import approver_resolver, entity_hooks, flow_service, task_notification
from .flow_model import (MULTI_ALL, MULTI_ANY, MULTI_QUORUM, MULTI_SEQUENTIAL,
                         NO_APPROVER_FALLBACK, NODE_CC, SKIP_ADJACENT,
                         SKIP_ANY_BEFORE, SKIP_NONE)
from .instance_model import (ACTION_APPROVE, ACTION_FINISH,
                             ACTION_SKIP_DUPLICATE, ACTION_START,
                             INSTANCE_APPROVED, INSTANCE_BLOCKED,
                             INSTANCE_OPEN_STATUSES, INSTANCE_RUNNING,
                             TASK_APPROVED, TASK_CANCELLED, TASK_PENDING,
                             TASK_SKIPPED_DUPLICATE, TASK_WAITING,
                             ApprovalAction, ApprovalInstance, ApprovalTask)


# ── Tra cứu ─────────────────────────────────────────────────────────────────

def running_instance(db: Session, entity: str, entity_id: int) -> ApprovalInstance | None:
    return (
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.entity == entity,
                ApprovalInstance.entity_id == entity_id,
                ApprovalInstance.status.in_(INSTANCE_OPEN_STATUSES))
        .order_by(ApprovalInstance.id.desc())
        .first()
    )


def tasks_of_instance(db: Session, instance_id: int) -> list[ApprovalTask]:
    return (
        db.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance_id)
        .order_by(ApprovalTask.node_seq.asc(), ApprovalTask.order_no.asc(),
                  ApprovalTask.id.asc())
        .all()
    )


def record_audit(db: Session, instance: ApprovalInstance, action: int, actor: int,
                node_seq: int = 0, node_name: str = "", comment: str = "",
                task_id: int | None = None, actor_employee_id: int | None = None,
                on_behalf_of_id: int | None = None,
                delegation_id: int | None = None) -> ApprovalAction:
    row = ApprovalAction(
        instance_id=instance.id, task_id=task_id, node_seq=node_seq, node_name=node_name,
        action=action, actor_employee_id=actor_employee_id,
        on_behalf_of_id=on_behalf_of_id, delegation_id=delegation_id,
        comment=comment, created_by=actor, updated_by=actor,
    )
    db.add(row)
    return row


# ── Bắt đầu ─────────────────────────────────────────────────────────────────

def start(db: Session, entity: str, entity_id: int, subject: dict,
            submitter_employee_id: int | None, actor: int,
            entity_code: str = "", entity_title: str = "", *,
            company_flow_only: bool = False) -> ApprovalInstance | None:
    """Trình một phiếu vào bộ máy. `None` = không có luồng nào áp, gọi đường cũ."""
    if running_instance(db, entity, entity_id):
        raise HTTPException(400, "Phiếu này đang có một phiên duyệt chưa kết thúc")

    flow = flow_service.pick_flow(
        db, entity, subject, company_only=company_flow_only,
    )
    if flow is None:
        return None

    raw_snapshot = flow_service.snapshot(db, flow)
    stage = flow_service.stages(raw_snapshot)
    if not stage:
        raise HTTPException(400, f"Luồng «{flow.name}» chưa khai bước nào")

    instance = ApprovalInstance(
        entity=entity, entity_id=entity_id,
        entity_code=entity_code, entity_title=entity_title,
        flow_id=flow.id, flow_version=flow.version_no, flow_snapshot=raw_snapshot,
        status=INSTANCE_RUNNING, current_seq=stage[0],
        started_by_employee_id=submitter_employee_id, started_at=datetime.now(),
        created_by=actor, updated_by=actor,
    )
    db.add(instance)

    try:
        db.flush()
    except IntegrityError:
        #  Chốt chặn THẬT là `running_slot` + UNIQUE ở tầng dữ liệu; câu kiểm
        #  `phien_dang_chay` bên trên chỉ để có câu báo đẹp cho ca thường.
        #  Rơi vào đây nghĩa là một lượt bấm khác vừa ghi xong giữa hai câu lệnh
        #  của ta — đúng ca NHẤP ĐÚP nút «Gửi duyệt» (dựng lại được 24/08/2026,
        #  trước khi có ràng buộc thì ra HAI phiếu duyệt cùng chạy).
        db.rollback()
        raise HTTPException(
            409, "Phiếu duyệt của chứng từ này vừa được mở bởi một lượt bấm khác. "
                 "Tải lại trang để xem phiếu đang chạy.")

    record_audit(db, instance, ACTION_START, actor,
                actor_employee_id=submitter_employee_id,
                comment=f"Trình duyệt theo luồng «{flow.name}» bản {flow.version_no}")
    open_stage(db, instance, subject, stage[0])
    db.commit()
    db.refresh(instance)
    return instance


# ── Mở một chặng ────────────────────────────────────────────────────────────

def open_stage(db: Session, instance: ApprovalInstance, subject: dict, seq: int) -> None:
    """Dựng việc cho chặng `seq`, xử lý trùng người và ca không tìm được ai."""
    node = flow_service.step_of_stage(instance.flow_snapshot, seq, subject)
    if node is None:
        #  ⚠️ Không nhánh nào nhận. Đây đúng là ca phiếu biến mất khỏi mọi danh
        #  sách nếu bỏ qua — nên đánh dấu KẸT để nó còn hiện ở đâu đó.
        _finish(db, instance, f"Chặng {seq}: không nhánh nào khớp và luồng không "
                           f"khai nhánh mặc định")
        return

    instance.current_seq = seq

    if node.node_kind == NODE_CC:
        #  I15 — bước nhận bản sao KHÔNG chặn luồng. Ghi dấu vết rồi đi tiếp
        #  ngay; người nhận biết qua thông báo.
        record_audit(db, instance, ACTION_APPROVE, instance.updated_by or 0,
                    node_seq=seq, node_name=node.name or "",
                    comment="Bước nhận bản sao — không chặn luồng")
        advance(db, instance, subject)
        return

    approvers = approver_resolver.resolve(db, node, subject, instance.started_by_employee_id)
    approvers = _exclude_submitter(instance, node, approvers)
    approvers, any_skipped = _split_duplicate_approvers(db, instance, node, approvers)

    if not approvers:
        if any_skipped:
            #  Cả chặng đều là người đã duyệt phía trước → coi như chặng xong.
            advance(db, instance, subject)
            return
        _handle_no_approver(db, instance, node, subject)
        return

    due = datetime.now() + timedelta(hours=node.sla_hours) if node.sla_hours else None
    sequential = node.multi_mode == MULTI_SEQUENTIAL

    new_tasks = []
    for order_index, employee_id in enumerate(approvers, start=1):
        task = ApprovalTask(
            instance_id=instance.id, node_seq=seq, node_name=node.name or "",
            order_no=order_index, assignee_employee_id=employee_id,
            #  Bước "lần lượt" chỉ mở việc cho người đầu; những người sau còn
            #  chờ. Mở hết cùng lúc thì "lần lượt" không còn nghĩa gì.
            status=TASK_WAITING if (sequential and order_index > 1) else TASK_PENDING,
            due_at=due, created_by=instance.updated_by or 0,
            updated_by=instance.updated_by or 0,
        )
        db.add(task)
        new_tasks.append(task)
    db.flush()
    #  Báo NGAY khi việc mở ra. Không báo thì việc nằm im trong hộp «Việc của
    #  tôi» tới lúc người duyệt tự nhớ ra mà mở hộp — phiếu chết giữa luồng.
    task_notification.notify_new_tasks(db, instance, new_tasks)


def _exclude_submitter(instance: ApprovalInstance, node, ids: list[int]) -> list[int]:
    """I08 — người nộp không duyệt phiếu của chính mình.

    Bỏ họ khỏi danh sách chứ không chặn cả bước: bước còn người khác thì vẫn
    chạy bình thường. Bỏ hết thì rơi vào `_khong_co_nguoi_duyet`, và ở đó luật
    thường là đẩy lên cấp trên — đúng câu tài liệu ghi.
    """
    submitter = instance.started_by_employee_id
    if not submitter:
        return ids
    return [employee_id for employee_id in ids if employee_id != submitter]


def _split_duplicate_approvers(db: Session, instance: ApprovalInstance, node,
                      ids: list[int]) -> tuple[list[int], bool]:
    """I06 — ai đã duyệt phía trước thì bước này tự qua.

    Việc tự qua được ghi thành **trạng thái riêng** (`TASK_SKIPPED_DUPLICATE`),
    KHÔNG ghi thành "đã duyệt": bản in dấu vết phải phân biệt *người này đã ký*
    với *bước này tự qua vì trùng người*. Gộp làm một là bản in nói dối rằng có
    thêm một người đã xem xét.
    """
    if node.skip_duplicate == SKIP_NONE or not ids:
        return ids, False

    already_approved = _previously_approved(db, instance, node)
    remaining, skipped = [], False

    for employee_id in ids:
        if employee_id in already_approved:
            db.add(ApprovalTask(
                instance_id=instance.id, node_seq=node.seq, node_name=node.name or "",
                order_no=0, assignee_employee_id=employee_id,
                status=TASK_SKIPPED_DUPLICATE, decided_at=datetime.now(),
                created_by=instance.updated_by or 0, updated_by=instance.updated_by or 0,
            ))
            record_audit(db, instance, ACTION_SKIP_DUPLICATE, instance.updated_by or 0,
                        node_seq=node.seq, node_name=node.name or "",
                        actor_employee_id=employee_id,
                        comment="Người này đã duyệt ở bước trước nên bước này tự qua")
            skipped = True
        else:
            remaining.append(employee_id)

    db.flush()
    return remaining, skipped


def _previously_approved(db: Session, instance: ApprovalInstance, node) -> set[int]:
    query = db.query(ApprovalTask.assignee_employee_id).filter(
        ApprovalTask.instance_id == instance.id,
        ApprovalTask.status == TASK_APPROVED,
        ApprovalTask.node_seq < node.seq,
    )
    if node.skip_duplicate == SKIP_ADJACENT:
        #  Chỉ nhìn chặng LIỀN TRƯỚC. `node.seq - 1` là đủ vì chặng đánh số liên
        #  tiếp; chặng đó có thể đã bị bỏ qua hết, khi ấy tập rỗng và không ai
        #  bị bỏ — đúng ý "chỉ bỏ khi vừa ký xong".
        query = query.filter(ApprovalTask.node_seq == node.seq - 1)
    elif node.skip_duplicate != SKIP_ANY_BEFORE:
        return set()
    return {row[0] for row in query.all()}


def _handle_no_approver(db: Session, instance: ApprovalInstance, node, subject: dict) -> None:
    """I07 — bước không tìm được ai.

    ⚠️ **Không có nhánh "tự động duyệt qua"**, và đó là chủ ý. Lark có tùy chọn
    đó; với văn bản nó tạo ra văn bản CÓ HIỆU LỰC mà không ai chịu trách nhiệm.
    Hai lối còn lại đều để lại một người cụ thể phải bấm.

    ⚠️ **Nhánh "đẩy lên cấp trên" ĐÃ BỎ** (21/08/2026, CR-114). Nó là chỗ duy
    nhất bộ máy TỰ CHỌN một người không có tên trong luồng — chủ đầu tư chốt
    phiếu phải đi đúng luồng đã khai, không ai thay ai. Luồng cũ còn khai giá
    trị đó thì nay rơi thẳng xuống *dừng phiếu*: hiện ra để người ta sửa luồng,
    chứ không lặng lẽ giao cho một người lạ.
    """
    if node.on_no_approver == NO_APPROVER_FALLBACK and node.fallback_employee_id:
        task = ApprovalTask(
            instance_id=instance.id, node_seq=node.seq, node_name=node.name or "",
            order_no=1, assignee_employee_id=node.fallback_employee_id,
            status=TASK_PENDING, created_by=instance.updated_by or 0,
            updated_by=instance.updated_by or 0,
        )
        db.add(task)
        record_audit(db, instance, ACTION_APPROVE, instance.updated_by or 0,
                    node_seq=node.seq, node_name=node.name or "",
                    comment="Không tìm được người duyệt — chuyển cho người dự phòng")
        db.flush()
        #  Người dự phòng lại càng phải được báo: họ không hề chờ phiếu này.
        task_notification.notify_new_tasks(db, instance, [task])
        return

    _finish(db, instance, f"Bước «{node.name or node.seq}» không tìm được người duyệt")


def _finish(db: Session, instance: ApprovalInstance, reason: str) -> None:
    """Phiếu kẹt — vẫn là phiên MỞ để nó còn hiện trên màn quản trị.

    Đóng luôn thì phiếu lặng lẽ biến mất và không ai biết là đang thiếu người.
    """
    instance.status = INSTANCE_BLOCKED
    instance.finish_reason = reason
    record_audit(db, instance, ACTION_FINISH, instance.updated_by or 0,
                node_seq=instance.current_seq, comment=reason)
    db.flush()


# ── Đi tiếp ─────────────────────────────────────────────────────────────────

def stage_done(db: Session, instance: ApprovalInstance, node) -> bool:
    """Chặng hiện tại đã đủ điều kiện đi tiếp chưa — phần `multi_mode` của I05.

    ⚠️ **Bỏ việc ĐÃ HỦY ra khỏi phép đếm.** Chúng là dấu vết của một lượt duyệt
    trước, không phải người đang giữ việc. Với ba chế độ kia không khác gì, nhưng
    biểu quyết theo tỷ lệ lấy `len(viec)` làm MẪU SỐ nên đếm cả việc hủy là mẫu
    số phình lên sau mỗi lần trả về một bước: chặng 3 người bị trả về rồi mở lại
    có 3 việc hủy + 3 việc mới, tỷ lệ 100% đòi 6 phiếu thuận trong khi nhiều
    nhất chỉ có 3 — cả hội đồng đã bấm Duyệt mà phiếu treo vĩnh viễn ở đó. Tỷ lệ
    50% thì không treo nhưng lặng lẽ đòi 3 người thay vì 2 (25/08/2026).
    """
    task = [row for row in tasks_of_instance(db, instance.id)
            if row.node_seq == node.seq and row.status != TASK_CANCELLED]
    if not task:
        return True

    in_favor = [row for row in task
             if row.status in (TASK_APPROVED, TASK_SKIPPED_DUPLICATE)]
    still_pending = [row for row in task if row.status in (TASK_WAITING, TASK_PENDING)]

    if node.multi_mode == MULTI_ANY:
        return bool(in_favor)
    if node.multi_mode in (MULTI_ALL, MULTI_SEQUENTIAL):
        return not still_pending
    if node.multi_mode == MULTI_QUORUM:
        can = len(task) * max(1, min(node.quorum_percent, 100)) / 100
        return len(in_favor) >= can
    return not still_pending


def advance(db: Session, instance: ApprovalInstance, subject: dict) -> None:
    """Sang chặng kế; hết chặng thì phiếu coi như đã duyệt xong."""
    stage = flow_service.stages(instance.flow_snapshot)
    next_no = next((seq for seq in stage if seq > instance.current_seq), None)

    if next_no is None:
        instance.status = INSTANCE_APPROVED
        instance.finished_at = datetime.now()
        record_audit(db, instance, ACTION_FINISH, instance.updated_by or 0,
                    node_seq=instance.current_seq, comment="Đã duyệt hết các bước")
        db.flush()
        #  Báo cho module chứng từ để nó tự đổi trạng thái theo luật của mình.
        entity_hooks.fire(db, instance, "approved")
        return

    open_stage(db, instance, subject, next_no)


def open_next_task_in_step(db: Session, instance: ApprovalInstance, node) -> None:
    """Bước «lần lượt»: người vừa duyệt xong thì mở việc cho người kế."""
    if node.multi_mode != MULTI_SEQUENTIAL:
        return
    waiting = [row for row in tasks_of_instance(db, instance.id)
           if row.node_seq == node.seq and row.status == TASK_WAITING]
    if waiting:
        waiting[0].status = TASK_PENDING
        db.flush()
        #  Tới lượt ai thì báo người đó — việc của họ vừa từ "chờ" sang "phải làm".
        task_notification.notify_new_tasks(db, instance, [waiting[0]])


def delete_by_entity(db: Session, entity: str, entity_id: int) -> int:
    """Chứng từ bị XÓA thì dọn luôn phiếu duyệt của nó. Trả về số phiếu đã dọn.

    Không dọn thì phiếu duyệt nằm lại trỏ vào một chứng từ không còn tồn tại —
    lỗi dựng lại được 24/08/2026 trên đường đi hoàn toàn hợp lệ: tạo văn bản →
    gửi duyệt → bị **trả về** → bấm **Xóa** (luật cho phép xóa ở trạng thái đó,
    nút có sẵn trên màn hình) → phiếu duyệt vẫn còn. Rác cứ thế tích lại, và mọi
    thống kê đếm theo phiếu duyệt đều đếm cả những phiếu không còn chứng từ.

    Xóa CẢ dấu vết chứ không giữ lại: dấu vết duyệt là để trả lời *"ai duyệt cái
    này"* — cái đó không còn thì dấu vết cũng hết chỗ bám. Chứng từ nào cần giữ
    vết thì luật đã không cho xóa (đã cấp số → bãi bỏ; đã từ chối → khóa lại).

    **Gọi TRƯỚC khi xóa hàng của chứng từ**, trong cùng một giao dịch — gọi sau
    thì lỡ vỡ ở giữa là mất chứng từ mà phiếu vẫn còn, đúng cái ta đang chữa.
    """
    ids = [row[0] for row in db.query(ApprovalInstance.id)
           .filter(ApprovalInstance.entity == entity,
                   ApprovalInstance.entity_id == entity_id).all()]
    if not ids:
        return 0

    db.query(ApprovalAction).filter(
        ApprovalAction.instance_id.in_(ids)).delete(synchronize_session=False)
    db.query(ApprovalTask).filter(
        ApprovalTask.instance_id.in_(ids)).delete(synchronize_session=False)
    db.query(ApprovalInstance).filter(
        ApprovalInstance.id.in_(ids)).delete(synchronize_session=False)
    db.flush()
    return len(ids)
