"""Phân hệ Công việc — việc ĐƯỢC GIAO cho tôi, đổ vào tab "Việc cần làm" (F-02).

`dashboard/controller.build_my_tasks` gọi `build_job_tasks` để thêm loại `job`
vào cùng danh sách với YCMH/ĐMH/công nợ… Khóa việc là `job:{task_id}` — không kèm
mức vì việc không "leo thang" thành khóa khác như công nợ (danger/warn).

**Bất biến CR-215 vẫn giữ nguyên**: tab Việc cần làm là TẬP CHA của chuông cảnh
báo `/api/alerts`. Việc Dự án chỉ được THÊM vào tập cha (chuông cảnh báo không có
`job:*`; giao việc báo qua `tab_notification`, xem `notify_service`), nên mọi key
của chuông vẫn nằm trong tab. `test_cong_viec_chuong_cr666.py` khóa điều này.

Điều kiện lấy việc (mọi vế đều bắt buộc, thiếu một là lộ việc của dự án người ta
không còn tham gia):

- tôi là PIC của việc (người theo dõi KHÔNG tính — họ nhận chuông, không phải làm);
- việc đang mở (`OPEN`) và chưa xóa; dự án chưa lưu trữ;
- tôi VẪN là thành viên của dự án chứa việc (`visible_list_ids`);
- tôi có quyền đọc `work_task` theo vai trò.
"""
from sqlalchemy.orm import Session

from app.core.vn_time import vn_today
from app.modules.work.membership_service import resolve_actor, visible_list_ids
from app.modules.work.model import WorkAssigneeKind, WorkList, WorkTaskStatus
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

JOB_LIMIT = 300


def build_job_tasks(db: Session, user, prof) -> list[dict]:
    """Các việc Dự án đang chờ tôi làm, đã ở dạng dòng của `build_my_tasks`."""
    if not prof["perms_union"].get("work_task", {}).get("read"):
        return []
    actor = resolve_actor(db, user)
    if not actor.employee_id:
        return []
    list_ids = visible_list_ids(db, actor.employee_id)
    if not list_ids:
        return []

    rows = (db.query(WorkTask, WorkList.name)
            .join(WorkTaskAssignee, WorkTaskAssignee.task_id == WorkTask.id)
            .join(WorkList, WorkList.id == WorkTask.list_id)
            .filter(WorkTaskAssignee.employee_id == actor.employee_id,
                    WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC),
                    WorkTask.status == int(WorkTaskStatus.OPEN),
                    WorkTask.deleted_at.is_(None),
                    WorkTask.list_id.in_(list_ids),
                    WorkList.is_archived == 0)
            .order_by(WorkTask.id.desc()).limit(JOB_LIMIT).all())

    today = vn_today().isoformat()
    out = []
    for t, list_name in rows:
        overdue = bool(t.due_date) and t.due_date < today
        out.append({
            "key": f"job:{t.id}", "type": "job",
            "label": "Việc quá hạn" if overdue else "Việc được giao",
            "code": "", "title": t.title,
            "subtitle": f"{list_name}" + (f" · hạn {t.due_date}" if t.due_date else ""),
            "date": t.due_date or "", "link": f"/project/tasks/{t.id}",
        })
    return out
