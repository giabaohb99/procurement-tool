"""Phân hệ Dự án — số liệu cho màn TỔNG QUAN.

Tách khỏi `list_service` / `task_service` vì đây thuần là đếm: không sửa gì,
không có bất biến nào phải giữ, và mọi query đều gom theo `visible_list_ids`.

Vì sao đếm ở MÁY CHỦ chứ không kéo hết về gom ở trình duyệt như màn Tổng quan
Nhân sự: bên đó chỉ có vài trăm nhân sự nằm trong MỘT endpoint danh sách, còn
việc ở đây nằm rải trong từng dự án và API bảng kanban lấy theo TỪNG dự án —
gom ở client là hàng chục lượt gọi rồi tải về vài nghìn thẻ chỉ để đếm.

⚠️ Mọi con số phải lọc qua `visible_list_ids`. Đếm thẳng trên `tab_work_task`
là lộ khối lượng việc của những đội mình không tham gia.
"""
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.work.label_model import (WorkLabelField, WorkLabelOption,
                                          WorkTaskLabel)
from app.modules.work.list_config_service import PRIORITY_KEY
from app.modules.work.membership_service import Actor, visible_list_ids
from app.modules.work.model import WorkAssigneeKind, WorkList, WorkTaskStatus
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


def _today() -> str:
    return (datetime.utcnow() + VN_OFFSET).strftime("%Y-%m-%d")


def overview(db: Session, actor: Actor) -> dict:
    """Thẻ số liệu + dữ liệu hai biểu đồ của màn Tổng quan."""
    ids = visible_list_ids(db, actor.employee_id, actor.company_id)
    if not ids:
        return _empty()

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
    #  ⚠️ Hai danh sách này là ĐƯỜNG ĐI, không phải số liệu. Thẻ đếm nói "22 việc
    #  quá hạn" mà không có chỗ nào bấm vào thì người đọc biết mình đang có vấn
    #  đề nhưng không biết vấn đề nằm ở đâu — cảnh báo mà không có lối ra.
    #
    #  Quá hạn xếp theo hạn CŨ NHẤT trước: việc trễ lâu nhất là việc đáng hỏi
    #  nhất. Việc của tôi cũng theo hạn tăng dần, nhưng việc CHƯA đặt hạn
    #  (`due_date = ""`) phải xuống cuối chứ không lên đầu — chuỗi rỗng nhỏ hơn
    #  mọi chuỗi ngày nên sắp thẳng là chúng chiếm sạch tám dòng.
    overdue_rows = (open_only
                    .filter(WorkTask.due_date != "", WorkTask.due_date < _today())
                    .order_by(WorkTask.due_date.asc())
                    .limit(TOP_TASKS).all())

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

    return {
        "project_total": sum(1 for lst in lists if not lst.is_archived),
        "project_archived": sum(1 for lst in lists if lst.is_archived),
        "task_open": by_status.get(int(WorkTaskStatus.OPEN), 0),
        "task_done": by_status.get(int(WorkTaskStatus.DONE), 0),
        "task_cancelled": by_status.get(int(WorkTaskStatus.CANCELLED), 0),
        "task_overdue": overdue,
        "task_mine": mine,
        "by_project": by_project,
        "by_priority": by_priority,
        "overdue_tasks": [_task_row(t, names) for t in overdue_rows],
        "my_tasks": [_task_row(t, names) for t in mine_rows],
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


def _empty() -> dict:
    """Chưa tham gia dự án nào. Trả đủ KHÓA với số 0 chứ không trả `{}` —
    giao diện đọc `data.task_open` thẳng, thiếu khóa là `undefined` trên thẻ."""
    return {
        "project_total": 0, "project_archived": 0,
        "task_open": 0, "task_done": 0, "task_cancelled": 0,
        "task_overdue": 0, "task_mine": 0,
        "by_project": [], "by_priority": [],
        "overdue_tasks": [], "my_tasks": [],
    }
