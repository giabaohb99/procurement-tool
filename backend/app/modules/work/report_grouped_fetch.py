"""Báo cáo Công việc — bản GOM Ở SQL của `report_rows.fetch_rows` (review hiệu năng
"gói B", 01/10/2026). Load test đo 100k việc/100k PIC/kỳ 3 năm: 5-8s, 120-131 MB Python
(`plans/reports/fullstack-developer-261001-1103-load-test-8-bao-cao-moi.md` §2
`/api/work/summary`) — nguyên nhân là nạp MỖI việc khớp kỳ thành một dict Python
(`report_rows.fetch_rows`). Phần PIC (fan nhiều giá trị, không gộp chung được với
Tổng) nằm riêng ở `report_pic_groups.py` — xem docstring đầu tệp đó.

Ý tưởng cốt lõi GIỐNG HỆT `survey/report_grouped_fetch.py`: `report_aggregate.aggregate()`
chỉ CỘNG `MetricSpec.value_of(r)` qua mọi "hàng" — không quan tâm một hàng là 1 TASK
hay N TASK đã gộp sẵn. GROUP BY ở SQL theo (ngày hiệu lực giờ VN, CHIỀU đang "Xem
theo" — nếu dim đó không fan nhiều giá trị), trả COUNT(*)/SUM(...) làm các khóa
"cnt"/"on_time_cnt"/... — `report_service._build_spec()` đọc `r.get(...)` nên một
hàng gộp N task cộng đúng N; `key_of` của từng `DimensionSpec` không đổi gì, chỉ
CÁC CỘT KHÔNG PHẢI chiều đang active được để mặc định 0/"" (không ai đọc tới, xem
`_resolve`) — giống hệt cách `report_rows.fetch_rows` cũ chỉ tra PIC/ưu tiên khi
đúng `group_by` đó.

THỨ TỰ `groups` khi HÒA ĐIỂM: không cố tái tạo đúng thứ tự hòa điểm của bản cũ (bản
cũ cũng không có `ORDER BY` tường minh — thứ tự vốn đã phụ thuộc kế hoạch quét của
DB engine, chưa bao giờ là hợp đồng). Mỗi hàm GOM ở đây `ORDER BY` theo khóa chiều
tăng dần để ít nhất ổn định/tái lập được — bài kiểm equivalence
(`test_bao_cao_cong_viec_gom_sql.py`) chọn dữ liệu KHÔNG hòa điểm đúng ở cột xếp
hạng để so khớp JSON tuyệt đối, tránh phụ thuộc vào quy ước hòa điểm không có thật.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.core.report_period import range_filter

from . import report_rows as rows
from .label_model import WorkLabelField, WorkLabelOption, WorkTaskLabel
from .list_config_service import PRIORITY_KEY
from .model import ENUM_LABELS
from .report_sql_date import date_diff_days, vn_date_str
from .task_model import WorkTask


def _apply_dim(db: Session, q, group_by: str | None):
    """(cột CHIỀU cho GROUP BY/SELECT, query đã JOIN nếu cần) — cột `None` nếu
    `group_by` không cần cột riêng ở đây (none/pic — PIC xem `report_pic_groups.py`)."""
    if group_by in ("list", "group"):
        return WorkTask.list_id, q
    if group_by == "company":
        return WorkTask.company_id, q
    if group_by == "status":
        return WorkTask.status, q
    if group_by == "priority":
        field_ids = (db.query(WorkLabelField.id)
                    .filter(WorkLabelField.system_key == PRIORITY_KEY).scalar_subquery())
        q = (q.outerjoin(WorkTaskLabel, and_(WorkTaskLabel.task_id == WorkTask.id,
                                             WorkTaskLabel.field_id.in_(field_ids)))
              .outerjoin(WorkLabelOption, WorkLabelOption.id == WorkTaskLabel.option_id))
        return func.coalesce(WorkLabelOption.name, ""), q
    return None, q


def _row_dict(event: str, r, group_by: str | None) -> dict:
    d = {"event": event, "date": date.fromisoformat(r.date), "cnt": int(r.cnt),
        "list_id": 0, "list_name": "", "group_id": 0, "group_name": "",
        "company_id": 0, "company_name": "", "status": 0, "status_label": "",
        "priority_name": ""}
    if event == "completed":
        d["on_time_cnt"] = int(r.on_time_cnt or 0)
        d["due_completed_cnt"] = int(r.due_completed_cnt or 0)
        d["handling_days_sum"] = float(r.handling_days_sum or 0)
    if group_by in ("list", "group"):
        d["list_id"] = r.dim or 0
    elif group_by == "company":
        d["company_id"] = r.dim or 0
    elif group_by == "status":
        d["status"] = r.dim or 0
    elif group_by == "priority":
        d["priority_name"] = r.dim or ""
    return d


def _resolve(d: dict, group_by: str | None, metas: dict, companies: dict,
            status_labels: dict) -> None:
    """Điền TÊN hiển thị từ khóa thô — cùng lô tra `metas`/`companies` đã có sẵn ở
    `report_service.compute_work_summary` (điểm 4, review hiệu năng), không hỏi
    CSDL thêm lần nào ở đây."""
    if group_by in ("list", "group"):
        meta = metas.get(d["list_id"], rows.EMPTY_LIST_META)
        d["list_name"], d["group_id"], d["group_name"] = meta["name"], meta["group_id"], meta["group_name"]
    elif group_by == "company":
        d["company_name"] = companies.get(d["company_id"], "")
    elif group_by == "status":
        d["status_label"] = status_labels.get(d["status"], "")


def _grouped_created(db: Session, scope_ids, d_from: date, d_to: date, group_by: str | None) -> list:
    q = rows.base_query(db, scope_ids).filter(
        range_filter(WorkTask.created_at, "datetime_utc", d_from, d_to))
    date_expr = vn_date_str(db, WorkTask.created_at)
    dim_col, q = _apply_dim(db, q, group_by)
    cols, group_cols = [date_expr.label("date"), func.count().label("cnt")], [date_expr]
    if dim_col is not None:
        cols.append(dim_col.label("dim"))
        group_cols.append(dim_col)
    q = q.with_entities(*cols).group_by(*group_cols).order_by(*group_cols)
    return q.all()


def _grouped_completed(db: Session, scope_ids, d_from: date, d_to: date, group_by: str | None) -> list:
    completed_cond = and_(WorkTask.completed_at.isnot(None),
                          range_filter(WorkTask.completed_at, "datetime_utc", d_from, d_to))
    q = rows.base_query(db, scope_ids).filter(completed_cond)
    completed_date = vn_date_str(db, WorkTask.completed_at)
    created_date = vn_date_str(db, WorkTask.created_at)
    has_due = WorkTask.due_date != ""
    on_time = and_(has_due, completed_date <= WorkTask.due_date)
    dim_col, q = _apply_dim(db, q, group_by)
    #  Mọi hàng ở đây đã qua `completed_cond` (WHERE) nên `handling_days` CỘNG
    #  THẲNG không cần `CASE` — khác `on_time_cnt`/`due_completed_cnt` còn phải
    #  phân biệt "có hạn" hay không NGAY TRONG tập đã lọc completed.
    cols = [completed_date.label("date"), func.count().label("cnt"),
           func.sum(case((on_time, 1), else_=0)).label("on_time_cnt"),
           func.sum(case((has_due, 1), else_=0)).label("due_completed_cnt"),
           func.sum(date_diff_days(db, completed_date, created_date)).label("handling_days_sum")]
    group_cols = [completed_date]
    if dim_col is not None:
        cols.append(dim_col.label("dim"))
        group_cols.append(dim_col)
    q = q.with_entities(*cols).group_by(*group_cols).order_by(*group_cols)
    return q.all()


def grouped_fetch_rows(db: Session, scope_ids, d_from: date, d_to: date, metas: dict,
                       companies: dict, group_by: str | None) -> list[dict]:
    """Bản GOM Ở SQL của `report_rows.fetch_rows` — CÙNG HỢP ĐỒNG đầu ra (tên
    khóa, kiểu) để `report_service._build_spec()` không phải đổi `key_of`/
    `value_of` nào; chỉ khác MỘT "hàng" đại diện N task (có `cnt`) thay vì đúng 1.
    `group_by="pic"` KHÔNG được truyền vào đây — xem `report_pic_groups.pic_groups`."""
    if not scope_ids:
        return []
    status_labels = ENUM_LABELS["work_task_status"]
    out = [_row_dict("created", r, group_by) for r in _grouped_created(db, scope_ids, d_from, d_to, group_by)]
    out += [_row_dict("completed", r, group_by) for r in _grouped_completed(db, scope_ids, d_from, d_to, group_by)]
    for d in out:
        _resolve(d, group_by, metas, companies, status_labels)
    return out
