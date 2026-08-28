"""Phân hệ Công việc — API nhóm · danh sách · cấu hình list. Prefix `/api/work`.

`/api/work` chứ không phải `/api/tasks`: đường đó đã bị tab «Việc cần làm»
chiếm (`/api/dashboard/tasks`, CR-215).

**Hai tầng quyền, cả hai đều bắt buộc:**
- `require("work_task", ...)` ở đây gác CỬA phân hệ (tầng 1 — RBAC hệ thống).
- Ai thấy/sửa được list nào là việc của `membership_service` (tầng 2). Có
  `work_task.read` toàn hệ vẫn KHÔNG đọc được list mình không phải thành viên.

Mọi endpoint đi qua service, không endpoint nào tự `db.query(...)`.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import group_service as groups
from . import list_config_service as cfg
from . import list_service as lists
from . import overview_service as overview
from . import schema
from .membership_service import require_employee, resolve_actor

router = APIRouter(prefix="/api/work", tags=["work"])


def _actor(db: Session, user):
    """Người thao tác, quy về trục nhân sự — chặn luôn tài khoản không có nhân sự."""
    actor = resolve_actor(db, user)
    require_employee(actor)
    return actor


# ── Nhóm ─────────────────────────────────────────────────────────────────────

@router.get("/groups")
def get_group_tree(include_archived: bool = False,
                   db: Session = Depends(get_db),
                   user=Depends(require("work_task", "read"))):
    """Cây điều hướng bên trái: nhóm → nhóm con → list, kèm list đứng lẻ (A-05)."""
    return success(groups.sidebar(db, _actor(db, user), include_archived))


@router.post("/groups")
def create_group(data: schema.GroupCreate, db: Session = Depends(get_db),
                 user=Depends(require("work_task", "create"))):
    return success(groups.create_group(db, _actor(db, user), data), "Đã tạo nhóm")


@router.patch("/groups/{group_id}")
def update_group(group_id: int, data: schema.GroupUpdate, db: Session = Depends(get_db),
                 user=Depends(require("work_task", "write"))):
    return success(groups.update_group(db, _actor(db, user), group_id, data), "Đã lưu")


@router.delete("/groups/{group_id}")
def archive_group(group_id: int, db: Session = Depends(get_db),
                  user=Depends(require("work_task", "delete"))):
    """LƯU TRỮ nhóm — không xóa cứng (A-01)."""
    return success(groups.archive_group(db, _actor(db, user), group_id), "Đã lưu trữ nhóm")


@router.get("/groups/{group_id}/members")
def get_group_members(group_id: int, db: Session = Depends(get_db),
                      user=Depends(require("work_task", "read"))):
    return success(groups.list_members(db, _actor(db, user), group_id))


@router.post("/groups/{group_id}/members")
def add_group_member(group_id: int, data: schema.MemberIn, db: Session = Depends(get_db),
                     user=Depends(require("work_task", "write"))):
    """Mời vào nhóm — vai trò kế thừa xuống mọi list bên trong (A-09)."""
    return success(groups.add_member(db, _actor(db, user), group_id, data), "Đã thêm")


@router.delete("/groups/{group_id}/members/{member_id}")
def remove_group_member(group_id: int, member_id: int, db: Session = Depends(get_db),
                        user=Depends(require("work_task", "write"))):
    groups.remove_member(db, _actor(db, user), group_id, member_id)
    return success(None, "Đã gỡ thành viên")


# ── Danh sách công việc ──────────────────────────────────────────────────────

@router.get("/overview")
def get_overview(db: Session = Depends(get_db),
                 user=Depends(require("work_task", "read"))):
    """Số liệu màn Tổng quan — chỉ đếm trong những dự án mình tham gia."""
    return success(overview.overview(db, _actor(db, user)))


@router.get("/lists")
def get_lists(include_archived: bool = False, with_people: bool = False,
              db: Session = Depends(get_db),
              user=Depends(require("work_task", "read"))):
    """Mọi dự án mình thấy. `with_people=1` nạp thêm chủ sở hữu + thành viên —
    chỉ màn liệt kê dự án cần, ô chọn thì đừng bật cho nhẹ."""
    return success(
        lists.get_lists(db, _actor(db, user), include_archived, with_people))


@router.post("/lists")
def create_list(data: schema.ListCreate, db: Session = Depends(get_db),
                user=Depends(require("work_task", "create"))):
    return success(lists.create_list(db, _actor(db, user), data), "Đã tạo danh sách")


@router.get("/lists/{list_id}")
def get_list(list_id: int, db: Session = Depends(get_db),
             user=Depends(require("work_task", "read"))):
    return success(lists.get_list(db, _actor(db, user), list_id))


@router.patch("/lists/{list_id}")
def update_list(list_id: int, data: schema.ListUpdate, db: Session = Depends(get_db),
                user=Depends(require("work_task", "write"))):
    return success(lists.update_list(db, _actor(db, user), list_id, data), "Đã lưu")


@router.delete("/lists/{list_id}")
def archive_list(list_id: int, db: Session = Depends(get_db),
                 user=Depends(require("work_task", "delete"))):
    return success(lists.archive_list(db, _actor(db, user), list_id), "Đã lưu trữ danh sách")


@router.get("/lists/{list_id}/members")
def get_list_members(list_id: int, db: Session = Depends(get_db),
                     user=Depends(require("work_task", "read"))):
    return success(lists.get_members(db, _actor(db, user), list_id))


@router.post("/lists/{list_id}/members")
def add_list_member(list_id: int, data: schema.MemberIn, db: Session = Depends(get_db),
                    user=Depends(require("work_task", "write"))):
    return success(lists.add_member(db, _actor(db, user), list_id, data), "Đã mời")


@router.delete("/lists/{list_id}/members/{member_id}")
def remove_list_member(list_id: int, member_id: int, db: Session = Depends(get_db),
                       user=Depends(require("work_task", "write"))):
    lists.remove_member(db, _actor(db, user), list_id, member_id)
    return success(None, "Đã gỡ thành viên")


@router.post("/lists/{list_id}/leave")
def leave_list(list_id: int, db: Session = Depends(get_db),
               user=Depends(require("work_task", "read"))):
    """Tự rời danh sách (A-03) — chỉ cần quyền đọc: rời khỏi chỗ của mình
    không phải hành động ghi lên dữ liệu người khác."""
    lists.leave_list(db, _actor(db, user), list_id)
    return success(None, "Đã rời danh sách")


@router.post("/lists/{list_id}/transfer")
def transfer_list(list_id: int, data: schema.TransferIn, db: Session = Depends(get_db),
                  user=Depends(require("work_task", "write"))):
    """Chuyển quyền sở hữu (A-04) — nguyên tử, giữ bất biến đúng một chủ."""
    return success(lists.transfer_ownership(db, _actor(db, user), list_id, data.employee_id),
                   "Đã chuyển quyền sở hữu")


# ── Cấu hình của list: cột · tag · nhãn tùy biến ─────────────────────────────

@router.get("/lists/{list_id}/sections")
def get_sections(list_id: int, db: Session = Depends(get_db),
                 user=Depends(require("work_task", "read"))):
    return success(cfg.get_sections(db, _actor(db, user), list_id))


@router.post("/lists/{list_id}/sections")
def create_section(list_id: int, data: schema.SectionIn, db: Session = Depends(get_db),
                   user=Depends(require("work_task", "write"))):
    return success(cfg.create_section(db, _actor(db, user), list_id, data), "Đã thêm cột")


@router.patch("/sections/{section_id}")
def update_section(section_id: int, data: schema.SectionIn, db: Session = Depends(get_db),
                   user=Depends(require("work_task", "write"))):
    return success(cfg.update_section(db, _actor(db, user), section_id, data), "Đã lưu")


@router.delete("/sections/{section_id}")
def delete_section(section_id: int, move_to: int | None = None,
                   db: Session = Depends(get_db),
                   user=Depends(require("work_task", "delete"))):
    """Xóa cột. Cột còn việc thì phải kèm `?move_to=` cột nhận."""
    cfg.delete_section(db, _actor(db, user), section_id, move_to)
    return success(None, "Đã xóa cột")


@router.get("/lists/{list_id}/tags")
def get_tags(list_id: int, db: Session = Depends(get_db),
             user=Depends(require("work_task", "read"))):
    return success(cfg.get_tags(db, _actor(db, user), list_id))


@router.post("/lists/{list_id}/tags")
def create_tag(list_id: int, data: schema.TagIn, db: Session = Depends(get_db),
               user=Depends(require("work_task", "write"))):
    return success(cfg.create_tag(db, _actor(db, user), list_id, data), "Đã thêm tag")


@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db),
               user=Depends(require("work_task", "delete"))):
    cfg.delete_tag(db, _actor(db, user), tag_id)
    return success(None, "Đã xóa tag")


@router.get("/lists/{list_id}/label-fields")
def get_label_fields(list_id: int, db: Session = Depends(get_db),
                     user=Depends(require("work_task", "read"))):
    return success(cfg.get_label_fields(db, _actor(db, user), list_id))


@router.post("/lists/{list_id}/label-fields")
def create_label_field(list_id: int, data: schema.LabelFieldIn,
                       db: Session = Depends(get_db),
                       user=Depends(require("work_task", "write"))):
    return success(cfg.create_label_field(db, _actor(db, user), list_id, data), "Đã thêm")


@router.delete("/label-fields/{field_id}")
def delete_label_field(field_id: int, db: Session = Depends(get_db),
                       user=Depends(require("work_task", "delete"))):
    cfg.delete_label_field(db, _actor(db, user), field_id)
    return success(None, "Đã xóa trường nhãn")


@router.post("/label-fields/{field_id}/options")
def create_label_option(field_id: int, data: schema.LabelOptionIn,
                        db: Session = Depends(get_db),
                        user=Depends(require("work_task", "write"))):
    return success(cfg.create_label_option(db, _actor(db, user), field_id, data), "Đã thêm")


@router.delete("/label-options/{option_id}")
def delete_label_option(option_id: int, db: Session = Depends(get_db),
                        user=Depends(require("work_task", "delete"))):
    cfg.delete_label_option(db, _actor(db, user), option_id)
    return success(None, "Đã xóa giá trị nhãn")
