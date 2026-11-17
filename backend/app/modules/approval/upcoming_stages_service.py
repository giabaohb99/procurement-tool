"""CÁC CHẶNG CHƯA MỞ của một phiên duyệt đang chạy — "ai sẽ duyệt tiếp".

Bảng việc (`tab_approval_task`) chỉ có chặng ĐÃ MỞ, nên dòng thời gian của phiếu
chỉ kể được người đang giữ việc. Người nộp đơn nghỉ hỏi tiếp "duyệt xong chặng
này thì tới tay ai" — câu đó trước đây phải đi hỏi quản trị luồng.

Chỉ ĐỌC: không mở việc, không ghi dấu vết, không commit. Tính bằng ĐÚNG vòng
lặp của màn xem trước (`preview_service.walk_stages`) trên bản chụp luồng của
chính phiếu, nên luật chọn người, luật I08 (người nộp không tự duyệt) và luật
bỏ qua khi trùng người khớp với lúc chặng mở thật.

Vẫn là DỰ KIẾN: chặng chưa mở thì người duyệt còn có thể đổi (đổi trưởng bộ phận,
gán lại vai trò, người duyệt hiện tại bị chuyển việc). Giao diện phải nói chữ
"dự kiến".
"""
from sqlalchemy.orm import Session

from . import entity_hooks, flow_service
from .flow_model import MULTI_ALL, MULTI_SEQUENTIAL
from .instance_model import (INSTANCE_RUNNING, TASK_APPROVED, TASK_OPEN_STATUSES,
                             ApprovalInstance, ApprovalTask)
from .preview_service import walk_stages


def list_upcoming_stages(db: Session, instance: ApprovalInstance) -> list[dict]:
    """Các chặng sau `current_seq` kèm người duyệt dự kiến. Rỗng khi phiên không còn chạy.

    Hai tập "coi như đã duyệt" nạp từ việc ĐÃ GIAO: người đã ký thật ở mọi chặng,
    cộng người đang giữ việc ở chặng hiện tại NẾU chặng đó bắt mọi người cùng ký
    (tất cả / lần lượt). Chặng "một người là đủ" hay "đủ tỷ lệ" thì chưa biết ai sẽ
    ký, việc của người còn lại bị hủy — coi cả nhóm là đã duyệt thì màn hình báo
    "tự động qua" cho một chặng sau mà lúc chạy thật lại mở việc.
    """
    if instance.status != INSTANCE_RUNNING or not instance.flow_snapshot:
        return []

    seqs = [seq for seq in flow_service.stages(instance.flow_snapshot)
            if seq > (instance.current_seq or 0)]
    if not seqs:
        return []

    tasks = (db.query(ApprovalTask.node_seq, ApprovalTask.assignee_employee_id,
                      ApprovalTask.status)
             .filter(ApprovalTask.instance_id == instance.id)
             .all())
    subject = entity_hooks.entity_context(db, instance.entity, instance.entity_id)
    current_node = flow_service.step_of_stage(instance.flow_snapshot, instance.current_seq, subject)
    current_open = {emp for seq, emp, status in tasks
                    if seq == instance.current_seq and status in TASK_OPEN_STATUSES}
    #  Chỉ một người đang giữ việc thì chính người đó sẽ ký, chế độ nào cũng vậy.
    open_will_sign = len(current_open) == 1 or (
        current_node is not None and current_node.multi_mode in (MULTI_ALL, MULTI_SEQUENTIAL))

    approved_any = {emp for _, emp, status in tasks if status == TASK_APPROVED}
    current_stage = {emp for seq, emp, status in tasks
                     if seq == instance.current_seq and status == TASK_APPROVED}
    if open_will_sign:
        current_stage |= current_open
    approved_any |= current_stage

    steps, _cc = walk_stages(db, instance.entity, instance.flow_snapshot, seqs, subject,
                             instance.started_by_employee_id, current_stage, approved_any)
    return steps
