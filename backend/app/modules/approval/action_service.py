"""NGƯỜI DÙNG BẤM GÌ — duyệt, từ chối, trả lại, rút, góp ý (I09–I11, I16, I23).

Ba hành động **bắt buộc nhập lý do**: từ chối, trả lại, rút lại. Không có lý do
thì người nộp không biết phải sửa gì và lần gửi sau y hệt lần trước — đó là cách
một quy trình duyệt biến thành vòng lặp.
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import delegation_service, entity_hooks, flow_service, instance_service
from .instance_model import (ACTION_APPROVE, ACTION_COMMENT, ACTION_REASSIGN,
                             ACTION_REJECT, ACTION_RETURN, ACTION_WITHDRAW,
                             INSTANCE_OPEN_STATUSES, INSTANCE_REJECTED,
                             INSTANCE_RETURNED, INSTANCE_RUNNING,
                             INSTANCE_WITHDRAWN, TASK_APPROVED, TASK_CANCELLED,
                             TASK_PENDING, TASK_REJECTED, TASK_WAITING,
                             ApprovalInstance, ApprovalTask)


def _ensure_open(instance: ApprovalInstance) -> None:
    if instance.status not in INSTANCE_OPEN_STATUSES:
        raise HTTPException(400, "Phiên duyệt này đã kết thúc")


def _require_reason(reason: str, action: str) -> str:
    reason = (reason or "").strip()
    if not reason:
        raise HTTPException(400, f"Phải nêu lý do khi {action} — người nộp cần biết sửa gì")
    return reason


def pending_task_of(db: Session, instance: ApprovalInstance,
                      actor_employee_id: int) -> tuple[ApprovalTask, int | None]:
    """Việc mà người này được phép bấm, kèm id ủy quyền nếu bấm thay.

    Tìm việc của chính mình TRƯỚC: đang có ủy quyền không có nghĩa là mất quyền
    xử lý việc của bản thân.
    """
    waiting = [row for row in instance_service.tasks_of_instance(db, instance.id)
                if row.status == TASK_PENDING]

    mine = next((row for row in waiting
                     if row.assignee_employee_id == actor_employee_id), None)
    if mine:
        return mine, None

    #  ⚠️ I08 vẫn phải đứng ở đây. Luật «người nộp không duyệt phiếu của chính
    #  mình» đang cắt ở chỗ DỰNG VIỆC (`_bo_nguoi_nop`), mà ủy quyền thì không
    #  đi qua chỗ đó: nó xét lúc BẤM và chỉ hỏi «tờ ủy quyền còn hạn không».
    #  Ghép hai cái lại là người trình ký được chính phiếu mình vừa trình —
    #  trưởng phòng đi công tác ủy quyền cho cấp dưới là việc thường ngày, mà
    #  cấp dưới đúng là người hay trình phiếu. Dấu vết khi đó ghi «B duyệt thay
    #  A», nhìn qua không thấy gì bất thường (25/08/2026).
    if instance.started_by_employee_id == actor_employee_id:
        raise HTTPException(
            403, "Bạn là người trình phiếu này nên không duyệt thay người khác được, "
                 "kể cả khi đang giữ ủy quyền")

    for row in waiting:
        delegation = delegation_service.find_delegation(
            db, actor_employee_id, row.assignee_employee_id, instance.entity)
        if delegation:
            return row, delegation.id

    raise HTTPException(403, "Bạn không có việc nào đang chờ ở phiếu này")


def claim_task(db: Session, task: ApprovalTask, new_status: int, actor: int) -> None:
    """CHIẾM một việc bằng MỘT câu UPDATE có điều kiện — để CSDL phân xử.

    ⚠️ Gán thẳng `task.status = …` là **đọc rồi mới ghi**, và hai lượt chạy sát
    nhau đều đọc thấy «Đang chờ» rồi cùng ghi. Lỗi dựng lại được 24/08/2026:
    **nhấp đúp nút «Duyệt» ở bước cuối thì CẢ HAI cú đều thành công** — dấu vết
    ghi hai dòng *Duyệt* và hai dòng *Kết thúc* cho một người bấm một lần.
    Văn bản không hỏng (hàm ban hành thấy phiên bản đã khóa nên lần hai ném lỗi
    và bị nuốt), nhưng **bản in dấu vết nói người ta ký hai lần** — mà cả lý do
    tồn tại của dấu vết là để trả lời "ai duyệt cái này", nên nó nói sai là hỏng
    đúng thứ đáng giá nhất.
    """
    line_count = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.id == task.id, ApprovalTask.status == TASK_PENDING)
        .update({"status": new_status, "decided_at": datetime.now(),
                 "updated_by": actor}, synchronize_session=False)
    )
    if line_count != 1:
        #  Không phải lỗi hệ: đúng nghĩa "người khác (hoặc chính bạn, lượt bấm
        #  trước) vừa xử lý xong việc này". Cùng câu với `concurrency.py`.
        db.rollback()
        raise HTTPException(
            409, "Việc này vừa được xử lý cùng lúc. "
                 "Tải lại trang để xem phiếu đang ở đâu rồi thao tác tiếp.")
    #  ⚠️ FLUSH/REFRESH BẮT BUỘC, không phải cho gọn. Phiên làm việc của hệ chạy
    #  `autoflush=False`, nên nếu không đồng bộ lại thì mọi truy vấn phía sau
    #  vẫn đọc trạng thái CŨ. Đúng lỗi đã bắt được: bước lẽ ra tự qua vì trùng
    #  người lại hỏi người ta ký lần nữa, vì lúc xét trùng nó chưa thấy chữ ký
    #  vừa đặt.
    db.flush()
    db.refresh(task)


def approve(db: Session, instance: ApprovalInstance, actor_employee_id: int,
          actor: int, subject: dict, comment: str = "") -> ApprovalInstance:
    _ensure_open(instance)
    task, delegation_id = pending_task_of(db, instance, actor_employee_id)

    claim_task(db, task, TASK_APPROVED, actor)
    #  ⚠️ Đặt TRƯỚC khi đi tiếp, không phải sau. Duyệt nốt bước cuối thì
    #  `di_tiep` gọi thẳng hook của chứng từ, mà hook đọc `instance.updated_by`
    #  để biết AI vừa quyết — đọc lúc chưa gán là ra người ghi trước đó (thường
    #  là người gửi duyệt). Hậu quả: văn bản ban hành mang tên người soạn ở cột
    #  người sửa cuối, và dòng nhật ký ghi sai người duyệt.
    instance.updated_by = actor

    instance_service.record_audit(
        db, instance, ACTION_APPROVE, actor, node_seq=task.node_seq,
        node_name=task.node_name, comment=comment, task_id=task.id,
        actor_employee_id=actor_employee_id,
        #  Bấm thay thì ghi CẢ HAI danh tính — bản in cần câu "ông B duyệt thay
        #  ông A theo ủy quyền số 12". Ghi một người là mất dấu trách nhiệm.
        on_behalf_of_id=task.assignee_employee_id if delegation_id else None,
        delegation_id=delegation_id,
    )

    node = flow_service.step_of_stage(instance.flow_snapshot, task.node_seq, subject)
    if node is not None and instance_service.stage_done(db, instance, node):
        _cancel_pending_tasks(db, instance, task.node_seq, actor)
        instance_service.advance(db, instance, subject)
    elif node is not None:
        instance_service.open_next_task_in_step(db, instance, node)

    db.commit()
    db.refresh(instance)
    return instance


def reject(db: Session, instance: ApprovalInstance, actor_employee_id: int,
            actor: int, reason: str) -> ApprovalInstance:
    """I10 — từ chối: phiếu dừng hẳn, phải làm phiếu mới."""
    _ensure_open(instance)
    reason = _require_reason(reason, "từ chối")
    task, delegation_id = pending_task_of(db, instance, actor_employee_id)

    claim_task(db, task, TASK_REJECTED, actor)

    instance_service.record_audit(
        db, instance, ACTION_REJECT, actor, node_seq=task.node_seq,
        node_name=task.node_name, comment=reason, task_id=task.id,
        actor_employee_id=actor_employee_id,
        on_behalf_of_id=task.assignee_employee_id if delegation_id else None,
        delegation_id=delegation_id,
    )

    _cancel_pending_tasks(db, instance, None, actor)
    instance.status = INSTANCE_REJECTED
    instance.finished_at = datetime.now()
    instance.finish_reason = reason
    instance.updated_by = actor
    db.flush()
    entity_hooks.fire(db, instance, "rejected")
    db.commit()
    db.refresh(instance)
    return instance


def send_back(db: Session, instance: ApprovalInstance, actor_employee_id: int,
            actor: int, reason: str, subject: dict,
            to_step: int | None = None) -> ApprovalInstance:
    """I09 — trả lại: về người nộp, hoặc về đúng một bước phía trước.

    Khác từ chối ở chỗ phiếu **còn sống**: sửa xong gửi lại được. Trả về một
    bước cụ thể thì những bước sau nó phải duyệt lại từ đầu — người ký sau đã ký
    trên một nội dung khác với nội dung sắp sửa.
    """
    _ensure_open(instance)
    reason = _require_reason(reason, "trả lại")
    task, delegation_id = pending_task_of(db, instance, actor_employee_id)

    #  KIỂM TRƯỚC KHI SỬA. Bản cũ chiếm việc, ghi dấu vết, hủy việc còn treo rồi
    #  mới xét `ve_buoc` — hỏng ở đó thì việc của người bấm đã mang trạng thái
    #  «đã hủy», và thứ duy nhất cứu là `get_db` cuộn phiên làm việc lại. Dựa
    #  vào một tầng khác để giữ đúng dữ liệu của tầng này là để ngỏ: chỉ cần
    #  chỗ nào phía trên lỡ `commit` là việc biến mất thật, phiếu kẹt không ai
    #  bấm được nữa.
    if to_step is not None:
        stage = flow_service.stages(instance.flow_snapshot)
        if to_step not in stage or to_step >= task.node_seq:
            raise HTTPException(400, "Chỉ trả về được một bước phía trước bước đang đứng")

    claim_task(db, task, TASK_CANCELLED, actor)
    #  Gán TRƯỚC hook, cùng lý do như ở `duyet` — nếu không thì văn bản bị trả
    #  về lại mang tên người GỬI DUYỆT trong nhật ký, đúng người không làm việc đó.
    instance.updated_by = actor

    instance_service.record_audit(
        db, instance, ACTION_RETURN, actor, node_seq=task.node_seq,
        node_name=task.node_name, comment=reason, task_id=task.id,
        actor_employee_id=actor_employee_id,
        on_behalf_of_id=task.assignee_employee_id if delegation_id else None,
        delegation_id=delegation_id,
    )
    _cancel_pending_tasks(db, instance, None, actor)

    if to_step is None:
        instance.status = INSTANCE_RETURNED
        instance.finished_at = datetime.now()
        instance.finish_reason = reason
        db.flush()
        entity_hooks.fire(db, instance, "returned")
    else:
        _clear_results_from_step(db, instance, to_step, actor)
        instance.status = INSTANCE_RUNNING
        instance_service.open_stage(db, instance, subject, to_step)

    db.commit()
    db.refresh(instance)
    return instance


def withdraw(db: Session, instance: ApprovalInstance, actor_employee_id: int,
            actor: int, reason: str) -> ApprovalInstance:
    """I11 — người nộp tự rút. **Chỉ khi chưa ai duyệt.**

    Có người đã ký rồi mà vẫn rút được thì chữ ký đó thành vô nghĩa: người ký
    không biết thứ mình vừa ký đã bị rút khỏi quy trình.
    """
    _ensure_open(instance)
    reason = _require_reason(reason, "rút lại")

    #  ⚠️ Phiếu KHÔNG ghi người trình thì cấm luôn, đừng bỏ qua câu kiểm. Câu cũ
    #  là `if instance.started_by_employee_id and … != actor`, nên cột để trống
    #  là cả câu kiểm biến mất và AI cũng rút được phiếu của người khác — rút
    #  xong chứng từ quay về nháp. Ba đường duyệt / trả lại / từ chối tự gác
    #  bằng «có việc đang chờ mình không», riêng đường này chỉ có mỗi câu đó.
    #  Cột để trống khi tài khoản trình phiếu chưa gắn hồ sơ nhân sự.
    if instance.started_by_employee_id != actor_employee_id:
        raise HTTPException(403, "Chỉ người trình duyệt mới rút lại được")

    someone_approved = any(
        row.status == TASK_APPROVED for row in instance_service.tasks_of_instance(db, instance.id))
    if someone_approved:
        raise HTTPException(
            400, "Đã có người duyệt nên không rút lại được — dùng Trả lại hoặc Từ chối")

    _cancel_pending_tasks(db, instance, None, actor)
    instance_service.record_audit(db, instance, ACTION_WITHDRAW, actor,
                                 node_seq=instance.current_seq, comment=reason,
                                 actor_employee_id=actor_employee_id)
    instance.status = INSTANCE_WITHDRAWN
    instance.finished_at = datetime.now()
    instance.finish_reason = reason
    instance.updated_by = actor
    #  Trả chứng từ về chỗ SỬA ĐƯỢC. Không có nhịp này thì phiếu rút xong nằm
    #  lại ở *đang duyệt*: gửi duyệt lại không được, mà nút duyệt một bước lại
    #  mở ra — thành đường tắt đi vòng qua cả luồng. Xem `entity_hooks.register`.
    entity_hooks.fire(db, instance, "withdrawn")
    db.commit()
    db.refresh(instance)
    return instance


def give_comment(db: Session, instance: ApprovalInstance, actor_employee_id: int,
          actor: int, content: str) -> None:
    """I16 — ý kiến trao đổi ngay trên phiếu, không qua chat riêng.

    Không đổi trạng thái gì. Nằm chung bảng dấu vết để bản in đọc được theo đúng
    thứ tự thời gian: ý kiến tách khỏi quyết định thì đọc lại không hiểu vì sao
    người ta duyệt.

    ⚠️ **Phiếu đã kết thúc thì thôi.** Chính vì ý kiến nằm chung bảng với quyết
    định và đi thẳng lên bản in dấu vết, cho ghi tiếp sau khi phiếu đóng nghĩa
    là tờ giấy đã ký vẫn dài thêm được. Hộp thoại trên giao diện chỉ mở khi còn
    việc đang chờ nên không ai gặp; nhưng cửa API thì trước đây vẫn nhận
    (25/08/2026).
    """
    _ensure_open(instance)
    content = (content or "").strip()
    if not content:
        raise HTTPException(400, "Chưa nhập ý kiến")
    instance_service.record_audit(db, instance, ACTION_COMMENT, actor,
                                 node_seq=instance.current_seq, comment=content,
                                 actor_employee_id=actor_employee_id)
    db.commit()


def reassign(db: Session, task: ApprovalTask, to_employee_id: int,
                       actor: int, reason: str = "",
                       actor_employee_id: int | None = None) -> ApprovalTask:
    """I07/I23 — đổi người xử lý một việc đang treo (nghỉ việc, bàn giao).

    `actor_employee_id` = người đang bấm. Bỏ trống nghĩa là chỗ gọi đã tự kiểm.
    """
    if task.status not in (TASK_WAITING, TASK_PENDING):
        raise HTTPException(400, "Việc này đã xử lý xong, không chuyển được")
    if task.assignee_employee_id == to_employee_id:
        raise HTTPException(400, "Người nhận trùng người đang giữ việc")

    #  ⚠️ KHÔNG TỰ BỐC VIỆC CỦA NGƯỜI KHÁC VỀ TAY MÌNH.
    #
    #  Bàn giao là thao tác dành cho người NGHỈ — có người thứ ba đứng ra sắp
    #  xếp, hoặc chính người giữ việc nhường lại. Còn tự chuyển việc của giám đốc
    #  sang tên mình rồi ký thì không phải bàn giao, đó là chiếm chữ ký; và nó
    #  chỉ cần đúng `approval_flow.write`.
    #
    #  Nặng hơn ủy quyền một bậc: ủy quyền còn để lại chữ «ký thay A», còn ở đây
    #  việc ĐỔI HẲN CHỦ nên bản in dấu vết không còn chỗ nào nói người ký không
    #  phải người được giao ban đầu.
    if (actor_employee_id is not None
            and to_employee_id == actor_employee_id
            and task.assignee_employee_id != actor_employee_id):
        raise HTTPException(
            403, "Không tự chuyển việc của người khác sang chính mình. "
                 "Bàn giao phải do người đang giữ việc hoặc người quản trị làm.")

    instance = db.get(ApprovalInstance, task.instance_id)
    #  Cửa sau thứ hai đi vòng qua I08, và tiện hơn ủy quyền vì chỉ cần quyền
    #  `approval_flow.write`: giao thẳng việc duyệt vào tay người vừa trình
    #  phiếu. Bàn giao khi nghỉ việc là thao tác quét hàng loạt, nên chuyện này
    #  xảy ra được mà không ai cố ý.
    if instance is not None and instance.started_by_employee_id == to_employee_id:
        raise HTTPException(
            400, "Người nhận chính là người trình phiếu này — họ không duyệt phiếu "
                 "của chính mình được")

    old_assignee = task.assignee_employee_id
    task.assignee_employee_id = to_employee_id
    task.updated_by = actor

    instance_service.record_audit(
        db, instance, ACTION_REASSIGN, actor, node_seq=task.node_seq,
        node_name=task.node_name, task_id=task.id,
        actor_employee_id=to_employee_id, on_behalf_of_id=old_assignee,
        comment=reason or "Chuyển người xử lý",
    )
    db.commit()
    db.refresh(task)
    return task


def bulk_handover(db: Session, from_employee_id: int, to_employee_id: int,
                       actor: int, reason: str = "",
                       actor_employee_id: int | None = None) -> int:
    """I23 — nghỉ việc: 30 phiếu đang chờ chuyển hết sang người khác một lần.

    Làm từng phiếu thì người bàn giao bỏ sót, và phiếu bỏ sót nằm im cho tới khi
    có người đi hỏi.

    `actor_employee_id` = người đang bấm. Bỏ trống nghĩa là chỗ gọi đã tự kiểm.
    """
    if from_employee_id == to_employee_id:
        raise HTTPException(400, "Người nhận trùng người bàn giao")

    #  ⚠️ Cùng luật với `chuyen_nguoi_xu_ly`, nhưng ở đây hậu quả nhân lên theo
    #  số phiếu: MỘT cú gọi quét sạch hộp việc của giám đốc sang tên kẻ gọi, mà
    #  nhật ký chỉ ghi «Bàn giao 30 việc duyệt» — nhìn y như một thao tác nghỉ
    #  việc bình thường.
    if (actor_employee_id is not None
            and to_employee_id == actor_employee_id
            and from_employee_id != actor_employee_id):
        raise HTTPException(
            403, "Không tự bàn giao việc của người khác về tay mình. "
                 "Việc này phải do chính người đang giữ việc hoặc người quản trị làm.")

    pending = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.assignee_employee_id == from_employee_id,
                ApprovalTask.status.in_((TASK_WAITING, TASK_PENDING)))
        .all()
    )
    transferred = 0
    for task in pending:
        try:
            reassign(db, task, to_employee_id, actor,
                               reason or "Bàn giao hàng loạt khi nghỉ việc")
        except HTTPException:
            #  Trong 30 phiếu có phiếu do CHÍNH người nhận trình — phiếu đó
            #  không chuyển được (I08). Đổ cả mẻ vì nó thì người bàn giao phải
            #  ngồi dò từng phiếu, đúng cái mà thao tác quét này sinh ra để
            #  tránh. Bỏ qua và đếm đúng số đã chuyển; số còn lại vẫn hiện
            #  trong hộp việc của người cũ nên không mất dấu.
            continue
        transferred += 1
    return transferred


# ── Dọn việc ────────────────────────────────────────────────────────────────

def _cancel_pending_tasks(db: Session, instance: ApprovalInstance,
                       node_seq: int | None, actor: int) -> None:
    """Việc còn treo mà phiếu đã đi tiếp thì phải hủy, không để nằm lại.

    Bỏ sót là màn "Việc của tôi" hiện việc của một phiếu đã xong — người dùng
    bấm vào không làm được gì, và lần sau họ thôi tin cái danh sách đó.
    """
    query = db.query(ApprovalTask).filter(
        ApprovalTask.instance_id == instance.id,
        ApprovalTask.status.in_((TASK_WAITING, TASK_PENDING)),
    )
    if node_seq is not None:
        query = query.filter(ApprovalTask.node_seq == node_seq)
    for row in query.all():
        row.status = TASK_CANCELLED
        row.updated_by = actor
    db.flush()


def _clear_results_from_step(db: Session, instance: ApprovalInstance, from_step: int,
                         actor: int) -> None:
    """Trả về bước N thì kết quả duyệt từ bước N trở đi không còn giá trị.

    KHÔNG xóa dòng dấu vết — bảng đó chỉ ghi thêm. Chỉ hủy các việc, để lượt
    duyệt mới dựng việc mới.
    """
    for row in instance_service.tasks_of_instance(db, instance.id):
        if row.node_seq >= from_step and row.status != TASK_CANCELLED:
            row.status = TASK_CANCELLED
            row.updated_by = actor
    db.flush()
