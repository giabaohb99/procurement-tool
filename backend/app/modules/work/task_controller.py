"""Phân hệ Công việc — API công việc và việc con. Prefix `/api/work`.

Tách khỏi `controller.py` cho mỗi tệp giữ được một chủ đề: bên kia là tổ chức
(nhóm · list · cấu hình), bên này là chính công việc.

Nhắc lại luật sống còn: KHÔNG endpoint nào tự `db.query(WorkTask)`. Mọi đường
đi qua `task_service`, nơi đã kiểm tư cách thành viên của list chứa task.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import schema
from . import task_service as tasks
from .membership_service import require_employee, resolve_actor

router = APIRouter(prefix="/api/work", tags=["work"])


def _actor(db: Session, user):
    actor = resolve_actor(db, user)
    require_employee(actor)
    return actor


@router.get("/lists/{list_id}/board")
def get_board(list_id: int, db: Session = Depends(get_db),
              user=Depends(require("work_task", "read"))):
    """Cột + task cha + mọi thứ vẽ trên thẻ, trong MỘT lượt gọi (D-01)."""
    return success(tasks.board(db, _actor(db, user), list_id))


@router.post("/tasks")
def create_task(data: schema.TaskCreate, db: Session = Depends(get_db),
                user=Depends(require("work_task", "create"))):
    return success(tasks.create_task(db, _actor(db, user), data), "Đã tạo công việc")


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db),
             user=Depends(require("work_task", "read"))):
    """Chi tiết + việc con. Không phải thành viên của list là 403, kể cả khi
    gõ thẳng id vào URL (bài khóa §5.1 của tài liệu phân quyền)."""
    return success(tasks.get_task(db, _actor(db, user), task_id))


@router.patch("/tasks/{task_id}")
def update_task(task_id: int, data: schema.TaskUpdate, db: Session = Depends(get_db),
                user=Depends(require("work_task", "write"))):
    """Sửa, kéo cột (`section_id` + `sort_order`), tick hoàn thành (`status`)."""
    return success(tasks.update_task(db, _actor(db, user), task_id, data), "Đã lưu")


@router.post("/tasks/{task_id}/move")
def move_task(task_id: int, data: schema.TaskMove, db: Session = Depends(get_db),
              user=Depends(require("work_task", "write"))):
    """Kéo thả kanban — đổi cột và/hoặc thứ tự trong cột, đánh số lại cả cột đích."""
    return success(
        tasks.move_task(db, _actor(db, user), task_id, data.section_id, data.before_task_id),
        "Đã lưu")


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db),
                user=Depends(require("work_task", "delete"))):
    """Xóa MỀM — vào thùng rác của list (B-09), khôi phục được."""
    tasks.delete_task(db, _actor(db, user), task_id)
    return success(None, "Đã xóa công việc")


@router.post("/tasks/{task_id}/subtasks")
def create_subtask(task_id: int, data: schema.TaskCreate, db: Session = Depends(get_db),
                   user=Depends(require("work_task", "create"))):
    """Thêm việc con. `parent_id` lấy từ đường dẫn nên client không đặt nhầm cha."""
    data.parent_id = task_id
    return success(tasks.create_task(db, _actor(db, user), data), "Đã thêm việc con")


@router.put("/tasks/{task_id}/assignees")
def set_assignees(task_id: int, data: schema.AssigneesIn, db: Session = Depends(get_db),
                  user=Depends(require("work_task", "write"))):
    """Đặt LẠI cả bộ người phụ trách + theo dõi (B-02). Nhiều PIC được."""
    return success(
        tasks.set_assignees(db, _actor(db, user), task_id, data.pic_ids, data.follower_ids),
        "Đã cập nhật người phụ trách")


@router.put("/tasks/{task_id}/tags")
def set_tags(task_id: int, data: schema.TagsIn, db: Session = Depends(get_db),
             user=Depends(require("work_task", "write"))):
    return success(tasks.set_tags(db, _actor(db, user), task_id, data.tag_ids), "Đã lưu")


@router.put("/tasks/{task_id}/label")
def set_label(task_id: int, data: schema.LabelIn, db: Session = Depends(get_db),
              user=Depends(require("work_task", "write"))):
    """Chọn một giá trị cho một trường nhãn tùy biến (B-08)."""
    return success(
        tasks.set_label(db, _actor(db, user), task_id, data.field_id, data.option_id),
        "Đã lưu")
