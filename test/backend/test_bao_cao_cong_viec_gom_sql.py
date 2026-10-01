"""Review hiệu năng "gói B" (01/10/2026) — chứng minh `report_grouped_fetch.py` +
`report_pic_groups.py` (GOM Ở SQL cho `/api/work/summary`) cho ĐÚNG Y HỆT kết quả
với tính TỪNG TASK một qua `report_aggregate.build_report` — cùng khung đã dùng
TRƯỚC khi gộp (xem `plans/reports/fullstack-developer-261001-1103-load-test-8-bao-cao-moi.md`
§2 `/api/work/summary`: 5-8s/120-131MB ở 100k task).

`report_rows.fetch_rows` (bản cũ, nạp 1 dict Python/task) đã bị XÓA khỏi mã nguồn
— khác `survey/report_grouped_fetch.py` còn giữ "đường cũ" sống song song cho
tham số `q`, ở đây không còn gì để so sánh trực tiếp. Nên bài kiểm này tự dựng
lại một ORACLE đơn giản (dễ thấy đúng bằng mắt, KHÔNG tối ưu — y hệt luật nghiệp
vụ của `fetch_rows` đã xóa) và so khớp với đường SẢN XUẤT thật
(`report_service.compute_work_summary`).

Vì `report_aggregate.compute_metrics` chỉ CỘNG `MetricSpec.value_of(r)` qua mọi
"hàng" — không quan tâm một hàng là 1 task (`cnt=1`, oracle) hay N task gộp sẵn
(`cnt=N`, đường SQL) — hai phía PHẢI cộng ra đúng một con số nếu luật nghiệp vụ
không đổi. Bài kiểm canh đúng ba chỗ dễ sai nhất khi gộp ở SQL:

  1. Biên UTC→VN 23:30 (hoàn thành TRƯỚC nửa đêm UTC nhưng SAU nửa đêm VN) —
     `report_sql_date.vn_date_str` NHÁNH THEO DIALECT, SQLite khác hẳn `to_local_date`
     Python ở công thức, sai một chỗ là đúng-hạn/trễ-hạn đảo ngược.
  2. PIC fan nhiều giá trị (2 PIC/task) — `groups` phải fan N, `totals` KHÔNG
     được đếm dôi (luật "totals cộng TRỰC TIẾP, không cộng lại từ groups").
  3. THỨ TỰ `groups` khi hòa điểm KHÔNG phải hợp đồng (bản cũ không có `ORDER BY`
     tường minh) — `_normalize` sắp lại theo `key` ở CẢ HAI phía trước khi so
     khớp, tránh bài kiểm đỏ vì một thứ tự chưa từng được cam kết.
"""
from datetime import datetime

from app.core.report_aggregate import aggregate
from app.core.report_compute import merge_groups_by_key
from app.core.report_period import parse_period, to_local_date
from app.modules.employee.model import Employee
from app.modules.work import label_value_service, report_rows as rows, report_service, schema, task_service
from app.modules.work.label_model import WorkLabelField, WorkLabelOption, WorkTaskLabel
from app.modules.work.list_config_service import PRIORITY_KEY, seed_system_label_fields
from app.modules.work.membership_service import Actor
from app.modules.work.model import ENUM_LABELS, WorkAssigneeKind, WorkGroup, WorkList, WorkListMember, WorkMemberRole
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

GROUP_BY_OPTIONS = (None, "list", "group", "company", "status", "priority", "pic")


# ── Dựng thế giới: 2 list (1 trong nhóm), PIC đơn/đôi/không, 4 độ ưu tiên ──────

def _emp(db, code: str) -> Employee:
    e = Employee(code=code, full_name=f"Người {code}", is_active=True)
    db.add(e)
    db.flush()
    return e


def _owner(db, code: str, company_id: int = 0) -> Actor:
    emp = _emp(db, code)
    return Actor(user_id=emp.id + 10_000, employee_id=emp.id, company_id=company_id)


def _list_direct(db, owner: Actor, name: str, company_id: int, group_id: int | None = None) -> int:
    """Dựng list THẲNG qua ORM (bỏ qua `list_service.create_list`'s kiểm quyền
    nhóm) — chỉ cần seed đủ trường "Độ ưu tiên" + một `WorkListMember` OWNER để
    `visible_list_ids` thấy được, không cần dựng cả bộ máy mời nhóm."""
    lst = WorkList(company_id=company_id, group_id=group_id, name=name)
    db.add(lst)
    db.flush()
    db.add(WorkListMember(company_id=company_id, list_id=lst.id, employee_id=owner.employee_id,
                          role=int(WorkMemberRole.OWNER)))
    seed_system_label_fields(db, lst.id, company_id, owner.user_id)
    db.commit()
    return lst.id


def _priority_option(db, list_id: int, index: int) -> int:
    """`index`: 0=P1 Khẩn, 1=P2 Cao, ... — khớp thứ tự `PRIORITY_OPTIONS`."""
    field = (db.query(WorkLabelField)
            .filter(WorkLabelField.list_id == list_id, WorkLabelField.system_key == PRIORITY_KEY).one())
    opt = (db.query(WorkLabelOption).filter(WorkLabelOption.field_id == field.id)
          .order_by(WorkLabelOption.sort_order).all())[index]
    return field, opt.id


def _set_priority(db, owner: Actor, list_id: int, task_id: int, index: int) -> None:
    field, opt_id = _priority_option(db, list_id, index)
    label_value_service.write_value(db, field, task_id, opt_id, owner.user_id)
    db.commit()


def _task(db, owner: Actor, list_id: int, **kw) -> int:
    kw.setdefault("title", "Việc")
    return task_service.create_task(db, owner, schema.TaskCreate(list_id=list_id, **kw))["id"]


def _set_times(db, task_id: int, created_at=None, completed_at=None) -> None:
    t = db.get(WorkTask, task_id)
    if created_at is not None:
        t.created_at = created_at
    if completed_at is not None:
        t.completed_at = completed_at
    db.commit()


def _world(db):
    """Thế giới DÙNG CHUNG cho mọi tổ hợp group_by/compare của bài kiểm này —
    dựng MỘT LẦN, không lặp lại cho từng `group_by` để tiết kiệm thời gian chạy."""
    owner = _owner(db, "OWS", company_id=55)
    pic1, pic2, pic3 = _emp(db, "PS1"), _emp(db, "PS2"), _emp(db, "PS3")
    group = WorkGroup(company_id=55, name="Nhóm G")
    db.add(group)
    db.flush()
    lid_a = _list_direct(db, owner, "Dự án A", company_id=55, group_id=group.id)
    lid_b = _list_direct(db, owner, "Dự án B", company_id=77, group_id=None)

    #  T1 (list A) — hoàn thành 23:30 UTC ngày hạn-1 -> ngày VN = ngày hạn -> ĐÚNG HẠN.
    t1 = _task(db, owner, lid_a, due_date="2026-05-10")
    task_service.set_assignees(db, owner, t1, [pic1.id], [])
    _set_priority(db, owner, lid_a, t1, 0)   # P1 — Khẩn
    task_service.update_task(db, owner, t1, schema.TaskUpdate(status=2))   # DONE
    _set_times(db, t1, created_at=datetime(2026, 5, 1, 1, 0), completed_at=datetime(2026, 5, 9, 23, 30))

    #  T2 (list A) — 2 PIC, hoàn thành TRỄ hạn.
    t2 = _task(db, owner, lid_a, due_date="2026-05-10")
    task_service.set_assignees(db, owner, t2, [pic2.id, pic3.id], [])
    _set_priority(db, owner, lid_a, t2, 1)   # P2 — Cao
    task_service.update_task(db, owner, t2, schema.TaskUpdate(status=2))   # DONE
    _set_times(db, t2, created_at=datetime(2026, 5, 2, 1, 0), completed_at=datetime(2026, 5, 11, 10, 0))

    #  T3 (list B) — chưa xong, không hạn, không PIC, không ưu tiên.
    t3 = _task(db, owner, lid_b)
    _set_times(db, t3, created_at=datetime(2026, 5, 15, 1, 0))

    #  T4 (list B) — hủy, có PIC + ưu tiên (kiểm "status" dim gồm cả CANCELLED).
    t4 = _task(db, owner, lid_b, due_date="2026-05-01")
    task_service.set_assignees(db, owner, t4, [pic1.id], [])
    _set_priority(db, owner, lid_b, t4, 0)
    task_service.update_task(db, owner, t4, schema.TaskUpdate(status=3))   # CANCELLED
    _set_times(db, t4, created_at=datetime(2026, 5, 5, 0, 0))

    #  T5 (list A) — rơi vào kỳ SO SÁNH "previous" (tháng 4/2026), 2 PIC khác.
    t5 = _task(db, owner, lid_a, due_date="2026-04-28")
    task_service.set_assignees(db, owner, t5, [pic1.id, pic2.id], [])
    _set_priority(db, owner, lid_a, t5, 1)
    task_service.update_task(db, owner, t5, schema.TaskUpdate(status=2))
    _set_times(db, t5, created_at=datetime(2026, 4, 25, 1, 0), completed_at=datetime(2026, 4, 27, 5, 0))

    #  T6 (list B) — rơi vào kỳ SO SÁNH "year" (tháng 5/2025), hoàn thành TRỄ hạn.
    t6 = _task(db, owner, lid_b, due_date="2025-05-09")
    task_service.set_assignees(db, owner, t6, [pic3.id], [])
    task_service.update_task(db, owner, t6, schema.TaskUpdate(status=2))
    _set_times(db, t6, created_at=datetime(2025, 5, 10, 1, 0), completed_at=datetime(2025, 5, 12, 1, 0))

    return owner


# ── Oracle: nạp TỪNG task một (`cnt=1`), KHÔNG tối ưu — tái hiện luật của
#    `fetch_rows` đã xóa (git log trước 01/10/2026) để làm "đường cũ" so khớp ──

def _oracle_fetch(db, scope_ids, d_from, d_to) -> list[dict]:
    if not scope_ids:
        return []
    metas = rows.list_meta(db, scope_ids, need_group_names=True)
    companies = rows.company_names(db)
    status_labels = ENUM_LABELS["work_task_status"]

    tasks = rows.base_query(db, scope_ids).with_entities(
        WorkTask.id, WorkTask.list_id, WorkTask.company_id, WorkTask.status,
        WorkTask.due_date, WorkTask.created_at, WorkTask.completed_at).all()
    task_ids = [t.id for t in tasks]

    priority_by_task: dict[int, str] = {}
    pics_by_task: dict[int, list] = {}
    if task_ids:
        priority_by_task = dict(
            db.query(WorkTaskLabel.task_id, WorkLabelOption.name)
            .join(WorkLabelField, WorkLabelField.id == WorkTaskLabel.field_id)
            .join(WorkLabelOption, WorkLabelOption.id == WorkTaskLabel.option_id)
            .filter(WorkLabelField.system_key == PRIORITY_KEY, WorkTaskLabel.task_id.in_(task_ids)).all())
        pic_rows = (db.query(WorkTaskAssignee.task_id, WorkTaskAssignee.employee_id)
                   .filter(WorkTaskAssignee.task_id.in_(task_ids),
                           WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC)).all())
        names = rows.employee_names(db, {eid for _, eid in pic_rows})
        for tid, eid in pic_rows:
            pics_by_task.setdefault(tid, []).append((eid, names.get(eid, f"#{eid}")))

    out: list[dict] = []
    for t in tasks:
        meta = metas.get(t.list_id, rows.EMPTY_LIST_META)
        base = {"list_id": t.list_id, "list_name": meta["name"], "group_id": meta["group_id"],
               "group_name": meta["group_name"], "company_id": t.company_id,
               "company_name": companies.get(t.company_id, ""), "status": t.status,
               "status_label": status_labels.get(t.status, ""),
               "priority_name": priority_by_task.get(t.id, ""), "pics": pics_by_task.get(t.id, []), "cnt": 1}
        created_date = to_local_date(t.created_at)
        if created_date and d_from <= created_date <= d_to:
            out.append({**base, "event": "created", "date": created_date})
        if t.completed_at:
            completed_date = to_local_date(t.completed_at)
            if completed_date and d_from <= completed_date <= d_to:
                has_due = bool(t.due_date)
                on_time = has_due and completed_date.isoformat() <= t.due_date
                handling_days = (completed_date - created_date).days if created_date else 0
                out.append({**base, "event": "completed", "date": completed_date,
                           "on_time_cnt": 1 if on_time else 0, "due_completed_cnt": 1 if has_due else 0,
                           "handling_days_sum": handling_days})
    return out


def _oracle_summary(db, scope_ids, period, group_by) -> dict:
    """Y HỆT `report_service.compute_work_summary` nhưng `fetch()` đi qua
    `_oracle_fetch` (từng task) thay vì `report_grouped_fetch` (GOM Ở SQL)."""
    spec = report_service._build_spec()
    sql_group_by = None if group_by == "pic" else group_by

    def fetch(d_from, d_to):
        return _oracle_fetch(db, scope_ids, d_from, d_to)

    from app.core.report_aggregate import build_report
    data = build_report(fetch, spec, period, group_by=sql_group_by,
                        snapshot=report_service._snapshot_fn(db, scope_ids))
    if group_by == "pic":
        data["meta"]["group_by"] = "pic"
        cur = aggregate(_oracle_fetch(db, scope_ids, period.date_from, period.date_to), spec,
                        period.date_from, period.date_to, "day", "pic")["groups"]
        cmp = None
        if period.compare != "none" and period.compare_from and period.compare_to:
            cmp = aggregate(_oracle_fetch(db, scope_ids, period.compare_from, period.compare_to), spec,
                            period.compare_from, period.compare_to, "day", "pic")["groups"]
        data["groups"] = merge_groups_by_key(cur, cmp, spec, spec.rank_key())
    data["breakdowns"] = report_service._breakdowns(
        db, scope_ids, rows.list_meta(db, scope_ids), min(period.date_to, rows.today_vn()))
    data["notes"] = data.get("notes", []) + report_service.NOTES
    return data


def _normalize(data: dict) -> dict:
    """`groups` sắp theo `key` ở CẢ HAI phía trước khi so khớp — thứ tự hòa điểm
    CHƯA BAO GIỜ là hợp đồng (bản cũ không `ORDER BY`), chỉ GIÁ TRỊ mới cần khớp
    tuyệt đối. `trend`/`totals`/`breakdowns` không cần sắp lại: thứ tự của chúng
    đã xác định bởi trục ngày/đã gọi CHUNG một hàm `_breakdowns`."""
    out = dict(data)
    if out.get("groups") is not None:
        out["groups"] = sorted(out["groups"], key=lambda g: g["key"])
    return out


def _period(d_from: str, d_to: str, compare: str = "none"):
    return parse_period({"preset": "custom", "date_from": d_from, "date_to": d_to, "compare": compare})


# ── Bài kiểm chính: mọi `group_by` × hai kiểu so sánh đều khớp Oracle ──────────

class TestGomOSqlKhopOracle:
    def test_khop_moi_group_by_khong_so_sanh(self, db):
        owner = _world(db)
        scope_ids = {w.id for w in db.query(WorkList).all()}   # owner là OWNER của cả 2
        period = _period("2026-05-01", "2026-05-31", compare="none")

        for group_by in GROUP_BY_OPTIONS:
            params = {"group_by": group_by} if group_by else {}
            actual = report_service.compute_work_summary(db, owner.employee_id, period, params)
            expected = _oracle_summary(db, scope_ids, period, group_by)
            assert _normalize(actual) == _normalize(expected), f"lệch ở group_by={group_by}"

    def test_khop_moi_group_by_so_sanh_ky_truoc(self, db):
        owner = _world(db)
        scope_ids = {w.id for w in db.query(WorkList).all()}
        period = _period("2026-05-01", "2026-05-31", compare="previous")   # kéo theo T5 (tháng 4)

        for group_by in GROUP_BY_OPTIONS:
            params = {"group_by": group_by} if group_by else {}
            actual = report_service.compute_work_summary(db, owner.employee_id, period, params)
            expected = _oracle_summary(db, scope_ids, period, group_by)
            assert _normalize(actual) == _normalize(expected), f"lệch ở group_by={group_by} (previous)"

    def test_khop_moi_group_by_so_sanh_cung_ky_nam_truoc(self, db):
        owner = _world(db)
        scope_ids = {w.id for w in db.query(WorkList).all()}
        period = _period("2026-05-01", "2026-05-31", compare="year")   # kéo theo T6 (5/2025)

        for group_by in GROUP_BY_OPTIONS:
            params = {"group_by": group_by} if group_by else {}
            actual = report_service.compute_work_summary(db, owner.employee_id, period, params)
            expected = _oracle_summary(db, scope_ids, period, group_by)
            assert _normalize(actual) == _normalize(expected), f"lệch ở group_by={group_by} (year)"

    def test_so_lieu_nghiep_vu_dung_khong_chi_khop_oracle(self, db):
        """Oracle TỰ nó cũng có thể sai cùng một kiểu với bản gộp — chốt thêm vài
        con số tuyệt đối đọc tay được, không chỉ dựa vào so khớp hai bên."""
        owner = _world(db)
        period = _period("2026-05-01", "2026-05-31", compare="none")

        totals = report_service.compute_work_summary(db, owner.employee_id, period, {})["totals"]["current"]
        assert totals["created"] == 4          # T1,T2,T3,T4 tạo trong tháng 5
        assert totals["completed"] == 2         # T1,T2 hoàn thành trong tháng 5
        assert totals["due_completed_count"] == 2
        assert totals["on_time_count"] == 1     # chỉ T1 (biên 23:30 UTC) đúng hạn
        assert totals["on_time_rate"] == 50.0

        pic_data = report_service.compute_work_summary(db, owner.employee_id, period, {"group_by": "pic"})
        by_pic_created = {g["key"]: g["current"]["created"] for g in pic_data["groups"]}
        #  T1->pic1, T2->pic2+pic3, T4->pic1 (nhưng T4 bị HỦY vẫn tính "tạo mới" vì
        #  metric "created" không lọc theo trạng thái), T3 KHÔNG PIC -> "(Chưa gắn)".
        assert sorted(by_pic_created.values()) == [1, 1, 1, 2]
        assert by_pic_created[""] == 1          # T3 rơi vào nhóm "(Chưa gắn)"
