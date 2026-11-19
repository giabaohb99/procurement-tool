"""Phân hệ Công việc — API nhóm · danh sách · cấu hình list. Prefix `/api/work`.

`/api/work` chứ không phải `/api/tasks`: đường đó đã bị tab "Việc cần làm"
chiếm (`/api/dashboard/tasks`, CR-215).

**Hai tầng quyền, cả hai đều bắt buộc:**
- `require("work_task", ...)` ở đây gác CỬA phân hệ (tầng 1 — RBAC hệ thống).
- Ai thấy/sửa được list nào là việc của `membership_service` (tầng 2). Có
  `work_task.read` toàn hệ vẫn KHÔNG đọc được list mình không phải thành viên.

Mọi endpoint đi qua service, không endpoint nào tự `db.query(...)`.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import activity_service as activities
from . import group_service as groups
from . import list_config_service as cfg
from . import list_purge_service as purge
from . import list_service as lists
from . import member_invite_service as invites
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
def add_group_member(group_id: int, data: schema.MemberIn, background_tasks: BackgroundTasks,
                     db: Session = Depends(get_db), user=Depends(require("work_task", "write"))):
    """Mời vào nhóm — vai trò kế thừa xuống mọi list bên trong (A-09).

    Người mới được mời nhận chuông (duoc-CR-783); đổi vai trò người đã có thì không báo.
    """
    return success(groups.add_member(db, _actor(db, user), group_id, data, background_tasks), "Đã thêm")


@router.post("/groups/{group_id}/members/{member_id}/reinvite")
def reinvite_group_member(group_id: int, member_id: int, background_tasks: BackgroundTasks,
                          db: Session = Depends(get_db), user=Depends(require("work_task", "write"))):
    """Gửi lại chuông mời vào nhóm dự án cho một thành viên (nút Mời lại).

    Quyền: quản trị nhóm trở lên. 404 khi dòng thành viên không thuộc nhóm này. Trả `notified` = số người đã được báo
    (0 khi người đó chưa có tài khoản hoặc chính là người bấm).
    """
    sent = invites.reinvite_group_member(db, _actor(db, user), group_id, member_id, background_tasks)
    return success({"notified": sent}, "Đã gửi lại lời mời")


@router.delete("/groups/{group_id}/members/{member_id}")
def remove_group_member(group_id: int, member_id: int, db: Session = Depends(get_db),
                        user=Depends(require("work_task", "write"))):
    groups.remove_member(db, _actor(db, user), group_id, member_id)
    return success(None, "Đã gỡ thành viên")


# ── Danh sách công việc ──────────────────────────────────────────────────────

@router.get("/overview")
def get_overview(period_days: int = Query(overview.DEFAULT_PERIOD_DAYS, ge=1, le=366),
                 list_id: int | None = Query(None, ge=1),
                 db: Session = Depends(get_db),
                 user=Depends(require("work_task", "read"))):
    """Số liệu màn Tổng quan phân hệ Dự án: thẻ số, bảng theo người, sức khỏe dự án, việc cần xử lý.

    Quyền: `work_task.read`. Phạm vi: người xem được báo cáo Công việc & Dự án (`ReportKey.WORK`, admin có sẵn) đếm trên
    mọi dự án; còn lại chỉ các dự án mình tham gia (trường `scope` trả `all` / `member`). `period_days` (1–366, mặc
    định 30) là kỳ của các chỉ số "trong kỳ": tạo mới, xong, tỉ lệ đúng hạn, giờ thực tế. `list_id` = chỉ tính riêng một
    dự án (tab Báo cáo trong chi tiết dự án); dự án ngoài phạm vi ra bộ số rỗng.
    """
    return success(overview.overview(db, _actor(db, user), user, period_days, list_id))


@router.get("/overview/trend")
def get_overview_trend(kind: str = Query(..., pattern="^(project|person)$"),
                       id: int = Query(..., ge=1),
                       period_days: int = Query(overview.DEFAULT_PERIOD_DAYS, ge=1, le=366),
                       db: Session = Depends(get_db),
                       user=Depends(require("work_task", "read"))):
    """Diễn biến theo ngày / tuần của một dự án hoặc một người: việc mới giao, việc xong (đúng hạn / trễ / không hạn).

    Quyền và phạm vi như `/overview`. `kind=project` với dự án ngoài phạm vi, hoặc `kind=person` chỉ đếm việc người đó
    phụ trách trong các dự án được đếm — ngoài phạm vi ra chuỗi rỗng. Kỳ ≤ 31 ngày chia theo ngày, dài hơn theo tuần.
    """
    return success(overview.overview_trend(db, _actor(db, user), user, kind, id, period_days))


@router.get("/overview/people/{employee_id}/tasks")
def get_overview_person_tasks(employee_id: int, db: Session = Depends(get_db),
                              user=Depends(require("work_task", "read"))):
    """Việc đang mở của một người phụ trách, trong phạm vi màn Tổng quan (bấm vào tên ở bảng theo người).

    Quyền và phạm vi như `/overview`: chỉ trả việc thuộc các dự án người xem được đếm; người ngoài phạm vi ra danh
    sách rỗng, không lộ việc ở dự án khác. Tối đa 50 việc, quá hạn trước.
    """
    return success(overview.person_overview_tasks(db, _actor(db, user), user, employee_id))


@router.get("/lists")
def get_lists(include_archived: bool = False, with_people: bool = False,
              db: Session = Depends(get_db),
              user=Depends(require("work_task", "read"))):
    """Mọi dự án mình thấy. `with_people=1` nạp thêm chủ sở hữu + thành viên —
    chỉ màn liệt kê dự án cần, ô chọn thì đừng bật cho nhẹ."""
    return success(
        lists.get_lists(db, _actor(db, user), include_archived, with_people))


@router.post("/lists")
def create_list(data: schema.ListCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                user=Depends(require("work_task", "create"))):
    """Tạo dự án; người tạo thành chủ dự án, kèm ba cột mặc định.

    Đặt vào nhóm (`group_id`) phải có quyền quản trị nhóm đó. `member_employee_ids` (duoc-CR-783) chép thành viên nhóm
    thành thành viên riêng của dự án, giữ vai trò ở nhóm (chủ nhóm thành Quản trị) và báo chuông cho họ; id không thuộc
    nhóm trả 400.
    """
    return success(lists.create_list(db, _actor(db, user), data, background_tasks), "Đã tạo danh sách")


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
    """Đưa dự án vào lưu trữ — việc bên trong giữ nguyên, khôi phục được (gửi `is_archived = 0` qua PATCH).

    Quyền: chủ dự án. Đường giữ tên `DELETE` vì các nơi gọi cũ (công cụ AI) đang dùng; xóa thật là `/permanent`.
    """
    return success(lists.archive_list(db, _actor(db, user), list_id), "Đã lưu trữ danh sách")


@router.delete("/lists/{list_id}/permanent")
def purge_list(list_id: int, db: Session = Depends(get_db),
               user=Depends(require("work_task", "delete"))):
    """Xóa vĩnh viễn dự án cùng mọi việc, bình luận, tệp đính kèm bên trong — không khôi phục được.

    Quyền: chủ dự án (duoc-CR-783). Nhật ký thao tác được giữ lại. Trả `tasks` = số việc đã xóa.
    """
    return success(purge.purge_list(db, _actor(db, user), list_id), "Đã xóa vĩnh viễn dự án")


@router.get("/lists/{list_id}/members")
def get_list_members(list_id: int, db: Session = Depends(get_db),
                     user=Depends(require("work_task", "read"))):
    return success(lists.get_members(db, _actor(db, user), list_id))


@router.post("/lists/{list_id}/members")
def add_list_member(list_id: int, data: schema.MemberIn, background_tasks: BackgroundTasks,
                    db: Session = Depends(get_db), user=Depends(require("work_task", "write"))):
    """Mời một người vào dự án, hoặc đổi vai trò nếu người đó đã có.

    Quyền: quản trị dự án trở lên, không cấp vai trò cao hơn của mình. Người mới được mời nhận chuông (duoc-CR-783).
    """
    return success(lists.add_member(db, _actor(db, user), list_id, data, background_tasks), "Đã mời")


@router.post("/lists/{list_id}/members/{member_id}/reinvite")
def reinvite_list_member(list_id: int, member_id: int, background_tasks: BackgroundTasks,
                         db: Session = Depends(get_db), user=Depends(require("work_task", "write"))):
    """Gửi lại chuông mời vào dự án cho một thành viên (nút Mời lại).

    Quyền: quản trị dự án trở lên. 404 khi dòng thành viên không thuộc dự án này. Trả `notified` = số người đã được báo
    (0 khi người đó chưa có tài khoản hoặc chính là người bấm).
    """
    sent = invites.reinvite_list_member(db, _actor(db, user), list_id, member_id, background_tasks)
    return success({"notified": sent}, "Đã gửi lại lời mời")


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


# ── Dòng hoạt động cấp dự án (D-09) ─────────────────────────────────────────

@router.get("/lists/{list_id}/activities")
def get_activities(list_id: int, kind: int | None = None, by: int | None = None,
                   offset: int = 0, limit: int = 30,
                   db: Session = Depends(get_db),
                   user=Depends(require("work_task", "read"))):
    """Nhật ký gộp của cả dự án — việc + thành viên + cột, mới nhất trước (§8).

    `kind` = `WorkActivityKind`, `by` = `user_id` người thao tác. Phân trang bằng
    `offset`/`limit` để giao diện cuộn lấy thêm.
    """
    return success(activities.list_activities(db, _actor(db, user), list_id,
                                              kind=kind, by=by,
                                              offset=offset, limit=limit))


@router.get("/lists/{list_id}/activity-actors")
def get_activity_actors(list_id: int, db: Session = Depends(get_db),
                        user=Depends(require("work_task", "read"))):
    """Những người từng thao tác trên dự án — nguồn cho ô lọc "theo người"."""
    return success(activities.list_actors(db, _actor(db, user), list_id))


# ── Cấu hình của list: cột kanban · nhãn tùy biến ────────────────────────────

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


@router.post("/sections/{section_id}/move")
def move_section(section_id: int, data: schema.SectionMove, db: Session = Depends(get_db),
                 user=Depends(require("work_task", "write"))):
    """Kéo cột sang chỗ khác — trả CẢ danh sách cột đã xếp lại."""
    return success(
        cfg.move_section(db, _actor(db, user), section_id, data.before_section_id),
        "Đã xếp lại cột")


@router.delete("/sections/{section_id}")
def delete_section(section_id: int, move_to: int | None = None,
                   db: Session = Depends(get_db),
                   user=Depends(require("work_task", "delete"))):
    """Xóa cột. Cột còn việc thì phải kèm `?move_to=` cột nhận."""
    cfg.delete_section(db, _actor(db, user), section_id, move_to)
    return success(None, "Đã xóa cột")


@router.get("/lists/{list_id}/label-fields")
def get_label_fields(list_id: int, db: Session = Depends(get_db),
                     user=Depends(require("work_task", "read"))):
    return success(cfg.get_label_fields(db, _actor(db, user), list_id))


@router.post("/lists/{list_id}/label-fields")
def create_label_field(list_id: int, data: schema.LabelFieldIn,
                       db: Session = Depends(get_db),
                       user=Depends(require("work_task", "write"))):
    return success(cfg.create_label_field(db, _actor(db, user), list_id, data), "Đã thêm")


@router.patch("/label-fields/{field_id}")
def update_label_field(field_id: int, data: schema.LabelFieldUpdate,
                       db: Session = Depends(get_db),
                       user=Depends(require("work_task", "write"))):
    return success(cfg.update_label_field(db, _actor(db, user), field_id, data), "Đã lưu")


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


@router.patch("/label-options/{option_id}")
def update_label_option(option_id: int, data: schema.LabelOptionUpdate,
                        db: Session = Depends(get_db),
                        user=Depends(require("work_task", "write"))):
    return success(cfg.update_label_option(db, _actor(db, user), option_id, data), "Đã lưu")


@router.delete("/label-options/{option_id}")
def delete_label_option(option_id: int, db: Session = Depends(get_db),
                        user=Depends(require("work_task", "delete"))):
    cfg.delete_label_option(db, _actor(db, user), option_id)
    return success(None, "Đã xóa giá trị nhãn")
