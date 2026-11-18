"""Phân hệ Dự án — số liệu cho màn TỔNG QUAN.

Tách khỏi `list_service` / `task_service` vì đây thuần là đếm: không sửa gì,
không có bất biến nào phải giữ, và mọi query đều gom theo tập dự án của
`overview_scope.overview_list_ids` (duoc-CR-782: người xem được báo cáo Công việc
& Dự án đếm trên mọi dự án, còn lại theo `visible_list_ids`).

Vì sao đếm ở MÁY CHỦ chứ không kéo hết về gom ở trình duyệt như màn Tổng quan
Nhân sự: bên đó chỉ có vài trăm nhân sự nằm trong MỘT endpoint danh sách, còn
việc ở đây nằm rải trong từng dự án và API bảng kanban lấy theo TỪNG dự án —
gom ở client là hàng chục lượt gọi rồi tải về vài nghìn thẻ chỉ để đếm.

⚠️ Mọi con số phải lọc qua tập dự án của `overview_list_ids`. Đếm thẳng trên
`tab_work_task` là lộ khối lượng việc của những đội mình không tham gia.

Các khối cho người quản lý (duoc-CR-782) nằm ở tệp riêng: `overview_people.py`
(bảng theo người), `overview_projects.py` (sức khỏe dự án), `overview_attention.py`
(cần xử lý ngay).
"""
from datetime import datetime, timedelta

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.modules.work.label_model import (WorkLabelField, WorkLabelOption,
                                          WorkTaskLabel)
from app.modules.work.list_config_service import PRIORITY_KEY
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkAssigneeKind, WorkList, WorkTaskStatus
from app.modules.work.overview_attention import attention
from app.modules.work.overview_people import DUE_SOON_DAYS, people_rows, person_tasks
from app.modules.work.overview_projects import project_rows
from app.modules.work.overview_trend import trend
from app.modules.work.overview_scope import SCOPE_MEMBER, openable_list_ids, overview_list_ids
from app.modules.work.report_sql_date import vn_date_str
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

#  Giờ Việt Nam. Máy chủ chạy UTC nên "hôm nay" lệch 7 tiếng nếu lấy thẳng —
#  việc đến hạn hôm nay sẽ bị đếm là quá hạn suốt buổi tối.
VN_OFFSET = timedelta(hours=7)

#  Số dự án vẽ trên biểu đồ cột. Nhiều hơn thì chữ chồng lên nhau, mà phần đuôi
#  toàn dự án một hai việc, không nói lên điều gì.
TOP_PROJECTS = 8

#  Số dòng của hai danh sách việc trên màn Tổng quan.
#
#  ⚠️ Đây là màn TỔNG QUAN, không phải màn danh sách — chốt 8 dòng để nó còn là
#  một lời mời đi tiếp, không thành một bảng thứ hai. Số đầy đủ vẫn nằm ở thẻ
#  đếm ngay trên đó, nên người đọc luôn biết mình đang thấy 8 trong bao nhiêu.
TOP_TASKS = 8


#  Kỳ mặc định của các chỉ số "trong kỳ" (xong trong kỳ, đúng hạn) — duoc-CR-782.
DEFAULT_PERIOD_DAYS = 30


def _today() -> str:
    return (datetime.utcnow() + VN_OFFSET).strftime("%Y-%m-%d")


def _period_start_utc(today: str, period_days: int) -> datetime:
    """0 giờ (giờ VN) của ngày đầu kỳ, đổi sang UTC để so với `completed_at` (lưu UTC). Kỳ N ngày tính cả hôm nay."""
    first_day = datetime.strptime(today, "%Y-%m-%d") - timedelta(days=period_days - 1)
    return first_day - VN_OFFSET


def overview(db: Session, actor: Actor, user=None, period_days: int = DEFAULT_PERIOD_DAYS,
             list_id: int | None = None) -> dict:
    """Thẻ số liệu + biểu đồ + khối dành cho người quản lý (duoc-CR-782) của màn Tổng quan.

    Phạm vi theo `overview_scope.overview_list_ids`: xem được báo cáo Công việc & Dự án thì mọi dự án, còn lại các dự
    án mình tham gia. `user = None` giữ luật thành viên cho lời gọi nội bộ.

    `list_id` = báo cáo của RIÊNG một dự án (tab "Báo cáo" trong chi tiết dự án): đếm trong đúng dự án đó, và chỉ khi
    nó nằm trong phạm vi trên — dự án ngoài phạm vi ra bộ số rỗng, không lộ gì.
    """
    ids, scope = overview_list_ids(db, actor, user)
    if list_id is not None:
        ids = ids & {list_id}
    if not ids:
        return _empty(scope, period_days)

    lists = db.query(WorkList).filter(WorkList.id.in_(ids)).all()

    #  Nền chung của mọi phép đếm việc: chỉ task CHA còn sống, trong dự án mình
    #  thấy. Việc con là gạch đầu dòng bên trong thẻ, không phải một đầu việc.
    def tasks():
        return db.query(WorkTask).filter(
            WorkTask.list_id.in_(ids),
            WorkTask.parent_id.is_(None),
            WorkTask.deleted_at.is_(None),
        )

    by_status = dict(
        tasks().with_entities(WorkTask.status, func.count(WorkTask.id))
        .group_by(WorkTask.status).all())

    open_only = tasks().filter(WorkTask.status == int(WorkTaskStatus.OPEN))

    overdue = open_only.filter(
        WorkTask.due_date != "", WorkTask.due_date < _today()).count()
    #  duoc-CR-782: đến hạn trong 7 ngày tới (tính cả hôm nay), chưa quá hạn — một phần của vòng "tình trạng việc
    #  đang mở" (quá hạn / sắp tới hạn / còn hạn / chưa đặt hạn).
    soon_end = (datetime.strptime(_today(), "%Y-%m-%d") + timedelta(days=DUE_SOON_DAYS - 1)).strftime("%Y-%m-%d")
    due_soon = open_only.filter(WorkTask.due_date >= _today(), WorkTask.due_date <= soon_end).count()

    #  "Việc của tôi" = tôi là NGƯỜI PHỤ TRÁCH, không tính người theo dõi: theo
    #  dõi là để biết, không phải để làm.
    mine = (open_only.join(WorkTaskAssignee, WorkTaskAssignee.task_id == WorkTask.id)
            .filter(WorkTaskAssignee.employee_id == actor.employee_id,
                    WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC))
            .distinct().count())

    open_by_list = dict(
        open_only.with_entities(WorkTask.list_id, func.count(WorkTask.id))
        .group_by(WorkTask.list_id).all())

    by_priority = _count_by_priority(db, ids)

    names = {lst.id: lst.name for lst in lists}
    today = _today()
    since_utc = _period_start_utc(today, period_days)
    mine_rows = (open_only
                 .join(WorkTaskAssignee, WorkTaskAssignee.task_id == WorkTask.id)
                 .filter(WorkTaskAssignee.employee_id == actor.employee_id,
                         WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC))
                 .order_by((WorkTask.due_date == "").asc(), WorkTask.due_date.asc())
                 .distinct().limit(TOP_TASKS).all())

    by_project = sorted(
        ({"list_id": lst.id, "name": lst.name, "open": open_by_list.get(lst.id, 0)}
         for lst in lists if not lst.is_archived),
        key=lambda row: row["open"], reverse=True)[:TOP_PROJECTS]

    #  ⚠️ Danh sách quá hạn là ĐƯỜNG ĐI, không phải số liệu: thẻ "22 việc quá hạn" mà không có chỗ bấm thì người đọc
    #  biết có vấn đề nhưng không biết nó nằm đâu. Từ duoc-CR-782 nó nằm trong khối Cần xử lý ngay, kèm người
    #  phụ trách và số ngày trễ.
    openable = openable_list_ids(db, actor, scope, ids)
    attn = attention(db, ids, today, names, openable)
    period = _period_counts(db, tasks(), since_utc)

    return {
        "scope": scope,
        "period_days": period_days,
        "project_total": sum(1 for lst in lists if not lst.is_archived),
        "project_archived": sum(1 for lst in lists if lst.is_archived),
        "task_open": by_status.get(int(WorkTaskStatus.OPEN), 0),
        "task_done": by_status.get(int(WorkTaskStatus.DONE), 0),
        "task_cancelled": by_status.get(int(WorkTaskStatus.CANCELLED), 0),
        "task_overdue": overdue,
        "task_due_soon": due_soon,
        "task_mine": mine,
        **period,
        "task_unassigned": attn["unassigned_count"],
        "task_no_due": attn["no_due_count"],
        "by_project": by_project,
        "by_priority": by_priority,
        "overdue_tasks": attn["overdue_tasks"],
        "my_tasks": [_task_row(t, names) for t in mine_rows],
        "unassigned_tasks": attn["unassigned_tasks"],
        "no_due_tasks": attn["no_due_tasks"],
        "people": people_rows(db, ids, today, since_utc),
        "projects": project_rows(db, ids, today, openable, since_utc),
    }


def person_overview_tasks(db: Session, actor: Actor, user, employee_id: int) -> list[dict]:
    """Việc đang mở của một người phụ trách, trong ĐÚNG phạm vi màn Tổng quan (bấm vào tên ở bảng theo người)."""
    ids, scope = overview_list_ids(db, actor, user)
    if not ids:
        return []
    names = dict(db.query(WorkList.id, WorkList.name).filter(WorkList.id.in_(ids)).all())
    return person_tasks(db, ids, employee_id, _today(), names, openable_list_ids(db, actor, scope, ids))


def overview_trend(db: Session, actor: Actor, user, kind: str, entity_id: int,
                   period_days: int = DEFAULT_PERIOD_DAYS) -> dict:
    """Diễn biến theo ngày / tuần của MỘT dự án hoặc MỘT người, trong ĐÚNG phạm vi màn Tổng quan (`overview_trend.py`)."""
    ids, _scope = overview_list_ids(db, actor, user)
    today = _today()
    return trend(db, ids, kind, entity_id, today, period_days, _period_start_utc(today, period_days))


def _period_counts(db: Session, base, since_utc: datetime) -> dict:
    """Việc tạo mới / xong trong kỳ và tỉ lệ xong ĐÚNG HẠN — MỘT câu truy vấn.

    Đúng hạn = ngày xong (giờ VN) không sau hạn. Chỉ đo trên việc xong trong kỳ CÓ đặt hạn; chưa có việc nào để đo
    thì trả `None` (giao diện hiện "—"), không trả 0% — 0% là "trễ hết", nói sai sự thật.
    """
    def count(cond):
        return func.coalesce(func.sum(case((cond, 1), else_=0)), 0)

    done = and_(WorkTask.status == int(WorkTaskStatus.DONE), WorkTask.completed_at.isnot(None),
                WorkTask.completed_at >= since_utc)
    with_due = and_(done, WorkTask.due_date != "")
    on_time = and_(with_due, vn_date_str(db, WorkTask.completed_at) <= WorkTask.due_date)
    created, n_done, n_due, n_on_time = base.with_entities(
        count(WorkTask.created_at >= since_utc), count(done), count(with_due), count(on_time)).one()
    return {
        "task_created_in_period": int(created),
        "task_done_in_period": int(n_done),
        "on_time_rate": round(int(n_on_time) * 100 / int(n_due)) if n_due else None,
    }


def _task_row(task: WorkTask, names: dict[int, str]) -> dict:
    """Một dòng việc rút gọn cho màn Tổng quan.

    Chỉ đủ để NHẬN RA và BẤM VÀO: tên việc, dự án chứa nó, hạn. Không kèm mô
    tả, nhãn hay người phụ trách — đó là việc của thẻ chi tiết, mà kéo thêm
    chúng về đây là thêm hai lượt join cho một màn vốn thuần đếm.
    """
    return {
        "id": task.id,
        "list_id": task.list_id,
        "list_name": names.get(task.list_id, ""),
        "title": task.title,
        "due_date": task.due_date,
    }


def _count_by_priority(db: Session, list_ids) -> list[dict]:
    """Đếm việc CHƯA XONG theo bậc ưu tiên, gộp CHUNG mọi dự án.

    Độ ưu tiên nay là một trường tùy biến của TỪNG dự án (`system_key =
    "priority"`), nên mỗi dự án có bộ giá trị riêng và id riêng. Gộp theo **tên
    bậc**: hai dự án cùng để "P1 — Khẩn" thì trên biểu đồ là một cột, còn dự án
    nào đổi tên bậc của mình thì đứng thành cột riêng — đúng như nó vốn là.

    Việc KHÔNG đặt ưu tiên không có dòng nào ở đây; trước kia nó là bậc `0`.
    """
    rows = (db.query(WorkLabelOption.name, WorkLabelOption.color,
                     func.min(WorkLabelOption.sort_order), func.count(WorkTask.id))
            .select_from(WorkTaskLabel)
            .join(WorkLabelField, WorkLabelField.id == WorkTaskLabel.field_id)
            .join(WorkLabelOption, WorkLabelOption.id == WorkTaskLabel.option_id)
            .join(WorkTask, WorkTask.id == WorkTaskLabel.task_id)
            .filter(WorkLabelField.system_key == PRIORITY_KEY,
                    WorkTask.list_id.in_(list_ids),
                    WorkTask.parent_id.is_(None),
                    WorkTask.deleted_at.is_(None),
                    WorkTask.status == int(WorkTaskStatus.OPEN))
            .group_by(WorkLabelOption.name, WorkLabelOption.color)
            .all())
    return [{"name": name, "color": color, "open": int(count)}
            for name, color, _, count in sorted(rows, key=lambda r: (r[2], r[0]))]


def _empty(scope: str = SCOPE_MEMBER, period_days: int = DEFAULT_PERIOD_DAYS) -> dict:
    """Chưa thấy dự án nào. Trả đủ KHÓA với số 0 chứ không trả `{}` —
    giao diện đọc `data.task_open` thẳng, thiếu khóa là `undefined` trên thẻ."""
    return {
        "scope": scope, "period_days": period_days,
        "project_total": 0, "project_archived": 0,
        "task_open": 0, "task_done": 0, "task_cancelled": 0,
        "task_overdue": 0, "task_due_soon": 0, "task_mine": 0,
        "task_created_in_period": 0, "task_done_in_period": 0, "on_time_rate": None,
        "task_unassigned": 0, "task_no_due": 0,
        "by_project": [], "by_priority": [],
        "overdue_tasks": [], "my_tasks": [], "unassigned_tasks": [], "no_due_tasks": [],
        "people": [], "projects": [],
    }
