"""Phân hệ Công việc — API công việc và việc con. Prefix `/api/work`.

Tách khỏi `controller.py` cho mỗi tệp giữ được một chủ đề: bên kia là tổ chức
(nhóm · list · cấu hình), bên này là chính công việc.

Nhắc lại luật sống còn: KHÔNG endpoint nào tự `db.query(WorkTask)`. Mọi đường
đi qua `task_service`, nơi đã kiểm tư cách thành viên của list chứa task.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import link_service as links
from . import schema
from . import task_outcome_service as outcome_svc
from . import task_comment_service as comments
from . import task_service as tasks
from . import task_trash_service as trash
from .membership_service import require_employee, resolve_actor

router = APIRouter(prefix="/api/work", tags=["work"])


def _actor(db: Session, user):
    actor = resolve_actor(db, user)
    require_employee(actor)
    return actor


@router.get("/lists/{list_id}/board")
def get_board(list_id: int, per_section: int = Query(0, ge=0, le=tasks.BOARD_PAGE_MAX),
              light: bool = False, db: Session = Depends(get_db),
              user=Depends(require("work_task", "read"))):
    """Cột + task cha + mọi thứ vẽ trên thẻ, trong MỘT lượt gọi (D-01).

    bao-CR-483: `per_section` > 0 = chế độ nhẹ, mỗi cột tối đa chừng ấy việc, phần
    dư tải qua `/sections/{id}/tasks`; `light` bỏ phần mô tả. Không truyền = như cũ.
    """
    return success(tasks.board(db, _actor(db, user), list_id, per_section=per_section, light=light))


@router.get("/lists/{list_id}/sections/{section_id}/tasks")
def get_section_tasks(list_id: int, section_id: int, offset: int = Query(0, ge=0),
                      limit: int = Query(tasks.BOARD_PAGE_SIZE, ge=1, le=tasks.BOARD_PAGE_MAX),
                      light: bool = True, db: Session = Depends(get_db),
                      user=Depends(require("work_task", "read"))):
    """Trang kế của một cột — bao-CR-483. `section_id = 0` = "Chưa phân cột"."""
    return success(tasks.section_tasks(db, _actor(db, user), list_id, section_id,
                                       offset=offset, limit=limit, light=light))


@router.post("/tasks")
def create_task(data: schema.TaskCreate, background_tasks: BackgroundTasks,
                db: Session = Depends(get_db), user=Depends(require("work_task", "create"))):
    return success(tasks.create_task(db, _actor(db, user), data, background_tasks), "Đã tạo công việc")


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db),
             user=Depends(require("work_task", "read"))):
    """Chi tiết + việc con. Không phải thành viên của list là 403, kể cả khi
    gõ thẳng id vào URL (bài khóa §5.1 của tài liệu phân quyền)."""
    return success(tasks.get_task(db, _actor(db, user), task_id))


@router.patch("/tasks/{task_id}")
def update_task(task_id: int, data: schema.TaskUpdate, background_tasks: BackgroundTasks,
                db: Session = Depends(get_db), user=Depends(require("work_task", "write"))):
    """Sửa, kéo cột (`section_id` + `sort_order`), tick hoàn thành (`status`)."""
    return success(tasks.update_task(db, _actor(db, user), task_id, data, background_tasks), "Đã lưu")


@router.post("/tasks/{task_id}/outcome")
def set_task_outcome(task_id: int, data: schema.TaskOutcomeIn, background_tasks: BackgroundTasks,
                     db: Session = Depends(get_db), user=Depends(require("work_task", "write"))):
    """Đánh giá kết quả task đã xong: 1 = Đạt · 2 = Phải làm lại (tự mở lại task). duoc-CR-656."""
    return success(outcome_svc.set_outcome(db, _actor(db, user), task_id, data.outcome, background_tasks), "Đã lưu đánh giá")


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
def create_subtask(task_id: int, data: schema.TaskCreate, background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db), user=Depends(require("work_task", "create"))):
    """Thêm việc con. `parent_id` lấy từ đường dẫn nên client không đặt nhầm cha."""
    data.parent_id = task_id
    return success(tasks.create_task(db, _actor(db, user), data, background_tasks), "Đã thêm việc con")


@router.post("/task-links")
def create_task_link(data: schema.TaskLinkIn, db: Session = Depends(get_db),
                     user=Depends(require("work_task", "write"))):
    """Nối việc trước → việc sau trên Gantt (B-15). Service chặn vòng lặp, chặn
    nối chính mình và chặn hai đầu khác dự án."""
    return success(links.create_link(db, _actor(db, user), data), "Đã thêm phụ thuộc")


@router.patch("/task-links/{link_id}")
def update_task_link(link_id: int, data: schema.TaskLinkUpdate, db: Session = Depends(get_db),
                     user=Depends(require("work_task", "write"))):
    """Đổi KIỂU (FS/SS/FF/SF) hoặc độ trễ. Đổi hai đầu thì xóa rồi nối lại."""
    return success(links.update_link(db, _actor(db, user), link_id, data), "Đã lưu")


@router.delete("/task-links/{link_id}")
def delete_task_link(link_id: int, db: Session = Depends(get_db),
                     user=Depends(require("work_task", "write"))):
    """Xóa CỨNG: mũi tên là quan hệ hiển thị, không có gì để tra lại về sau."""
    links.delete_link(db, _actor(db, user), link_id)
    return success(None, "Đã xóa phụ thuộc")


@router.put("/tasks/{task_id}/assignees")
def set_assignees(task_id: int, data: schema.AssigneesIn, background_tasks: BackgroundTasks,
                  db: Session = Depends(get_db), user=Depends(require("work_task", "write"))):
    """Đặt LẠI cả bộ người phụ trách + theo dõi (B-02). Nhiều PIC được."""
    return success(
        tasks.set_assignees(db, _actor(db, user), task_id, data.pic_ids, data.follower_ids,
                            background_tasks),
        "Đã cập nhật người phụ trách")


@router.put("/tasks/{task_id}/label")
def set_label(task_id: int, data: schema.LabelIn, db: Session = Depends(get_db),
              user=Depends(require("work_task", "write"))):
    """Đặt giá trị cho một trường tùy biến. Sáu kiểu, xem `LabelIn` (B-13)."""
    return success(
        tasks.set_label(db, _actor(db, user), task_id, data.field_id, data.value),
        "Đã lưu")


@router.patch("/tasks/{task_id}/comments/{comment_id}")
def edit_task_comment(task_id: int, comment_id: int, data: schema.CommentEdit,
                      background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                      user=Depends(require("work_task", "write"))):
    """Sửa bình luận CỦA CHÍNH MÌNH (E-05) — người khác sửa là 403. Tạo/xóa đi cửa chung `/api/comments`."""
    return success(comments.edit_comment(db, _actor(db, user), user, task_id, comment_id,
                                         data.body, background_tasks),
                   "Đã sửa bình luận")


@router.get("/lists/{list_id}/trash")
def get_trash(list_id: int, db: Session = Depends(get_db),
              user=Depends(require("work_task", "read"))):
    """Thùng rác của dự án (B-09): việc đã xóa mềm, kèm cờ `can_restore` theo quyền người xem."""
    return success(trash.list_trash(db, _actor(db, user), list_id))


@router.post("/tasks/{task_id}/restore")
def restore_task(task_id: int, db: Session = Depends(get_db),
                 user=Depends(require("work_task", "delete"))):
    """Khôi phục việc khỏi thùng rác — cùng luật với xóa (cả RBAC `work_task.delete` lẫn
    vai trò dự án): MEMBER chỉ khôi phục việc mình tạo."""
    return success(trash.restore_task(db, _actor(db, user), task_id), "Đã khôi phục công việc")
