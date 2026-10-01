"""Gom Ở SQL cho báo cáo Phê duyệt (01/10/2026) — bài kiểm TƯƠNG ĐƯƠNG giữa bản SQL mới
(`report_service.fetch_rows` + `report_step_metrics.py`) và bản THAM CHIẾU chép Y HỆT thuật
toán Python cũ (vòng lặp theo `node_seq` đã sắp, nạp toàn bộ `tab_approval_task` — xem
`frontend-v2/plans/reports/fullstack-developer-261001-1103-load-test-8-bao-cao-moi.md` §"approvals"
cho lý do đổi: 714k dòng/226MB/10-24s ở quy mô bench, endpoint nặng nhất trong 13 báo cáo).

Bản THAM CHIẾU giữ NGUYÊN tại đây làm "mỏ neo" hồi quy vĩnh viễn — KHÔNG xóa dù code chính đã
đổi, vì đây là bằng chứng duy nhất còn lại rằng hai thuật toán cho CÙNG một kết quả.

Fixture PHONG PHÚ: 3 loại chứng từ nguồn (document/seal_request/vehicle_booking), đủ 4 trạng
thái kết thúc (duyệt/từ chối/trả về/rút) + 1 đang chạy, bước TUẦN TỰ lẫn SONG SONG, task tự-
qua-vì-trùng/đã-hủy (phải bị loại khỏi cả giờ bước lẫn chiều người duyệt), hạn xử lý có/không/
quá hạn, trải 3 tháng + 1 mốc trong kỳ SO SÁNH (phủ `group_by` none/entity/approver/node_name
và `compare` previous/year).

Dung sai: `step_hours_sum`/`proc_hours_sum` (và `avg_*` dẫn xuất từ chúng) CỘNG bằng SQL
`SUM()` ở bản mới, bằng Python `sum()` tuần tự ở bản cũ — thứ tự cộng khác nhau nên CÓ THỂ lệch
bit cuối dấu phẩy động (không thuật toán nào đảm bảo trùng tuyệt đối, xem docstring
`report_step_metrics.py`). So khớp bằng dung sai nhỏ cho MỌI số thực; đếm nguyên/nhãn/cấu trúc
so khớp TUYỆT ĐỐI (một lệch số nguyên hay thiếu/thừa khóa là LỖI THẬT, không phải dung sai).
"""
from __future__ import annotations

from datetime import datetime, time, timedelta

import pytest

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_period import parse_period, range_filter, to_local_date
from app.modules.approval import report_service as svc
from app.modules.approval.instance_model import (ApprovalInstance, ApprovalTask, INSTANCE_APPROVED,
                                                  INSTANCE_REJECTED, INSTANCE_RETURNED,
                                                  INSTANCE_RUNNING, INSTANCE_WITHDRAWN,
                                                  TASK_CANCELLED, TASK_SKIPPED_DUPLICATE)
from app.modules.doc_catalog.model import DocType
from app.modules.document.model import Document
from app.modules.employee.model import Employee
from app.modules.seal_request.model import SEAL_APPROVED, SealRequest
from app.modules.vehicle_booking.model import VehicleBooking

from test_bao_cao_phe_duyet import _instance, _seal_request, _task, _viewer

_AF = dict(scope="all", read=True, export=True)


# ── Bản THAM CHIẾU — chép Y HỆT thuật toán Python trước 01/10/2026, KHÔNG được sửa theo bản mới ──
def _legacy_decorate(inst, tasks: list, names: dict) -> dict:
    proc_hours = None
    if inst.status in (INSTANCE_APPROVED, INSTANCE_REJECTED) and inst.started_at and inst.finished_at:
        proc_hours = max((inst.finished_at - inst.started_at).total_seconds(), 0) / 3600
    real = [t for t in tasks if t.status not in (TASK_SKIPPED_DUPLICATE, TASK_CANCELLED)]
    by_seq: dict[int, list] = {}
    for t in real:
        if t.decided_at:
            by_seq.setdefault(t.node_seq, []).append(t)
    step_hours: list[float] = []
    overdue = due_known = 0
    prev_close = inst.started_at
    for seq in sorted(by_seq):
        group = by_seq[seq]
        if prev_close is not None:
            step_hours.extend(max((t.decided_at - prev_close).total_seconds(), 0) / 3600 for t in group)
        for t in group:
            if t.due_at:
                due_known += 1
                overdue += t.decided_at > t.due_at
        prev_close = max(t.decided_at for t in group)
    approvers = {(t.assignee_employee_id, names.get(t.assignee_employee_id, str(t.assignee_employee_id)))
                for t in real if t.assignee_employee_id}
    node_names = {(t.node_name, t.node_name) for t in tasks if t.node_name}
    return {"started_at": inst.started_at, "status": inst.status, "entity": inst.entity,
           "proc_hours": proc_hours, "step_hours": step_hours,
           "overdue_count": overdue, "due_known": due_known,
           "approvers": list(approvers), "node_names": list(node_names)}


def _legacy_fetch_rows(db, user, profile, allowed, d_from, d_to) -> list[dict]:
    cond = svc._visibility_cond(db, user, profile, allowed)
    instances = (db.query(ApprovalInstance.id, ApprovalInstance.entity, ApprovalInstance.status,
                          ApprovalInstance.started_at, ApprovalInstance.finished_at)
                .filter(cond)
                .filter(range_filter(ApprovalInstance.started_at, "datetime_utc", d_from, d_to))
                .all())
    if not instances:
        return []
    ids = [i.id for i in instances]
    tasks = (db.query(ApprovalTask.instance_id, ApprovalTask.node_seq, ApprovalTask.order_no,
                      ApprovalTask.id, ApprovalTask.assignee_employee_id, ApprovalTask.decided_at,
                      ApprovalTask.due_at, ApprovalTask.node_name, ApprovalTask.status)
            .filter(ApprovalTask.instance_id.in_(ids))
            .order_by(ApprovalTask.instance_id, ApprovalTask.node_seq, ApprovalTask.order_no,
                     ApprovalTask.id).all())
    by_instance: dict[int, list] = {}
    for t in tasks:
        by_instance.setdefault(t.instance_id, []).append(t)
    approver_ids = {t.assignee_employee_id for t in tasks if t.assignee_employee_id}
    names = ({e_id: name for e_id, name in db.query(Employee.id, Employee.full_name)
             .filter(Employee.id.in_(approver_ids)).all()} if approver_ids else {})
    return [_legacy_decorate(inst, by_instance.get(inst.id, []), names) for inst in instances]


def _legacy_build_spec() -> ReportSpec:
    def status_is(code):
        return lambda r: 1 if r["status"] == code else 0
    metrics = [
        MetricSpec("sessions", "Phiên duyệt", kind="int", value_of=lambda r: 1),
        MetricSpec("approved", "Đã duyệt", kind="int", value_of=status_is(INSTANCE_APPROVED)),
        MetricSpec("rejected", "Từ chối", kind="int", value_of=status_is(INSTANCE_REJECTED)),
        MetricSpec("returned", "Trả về", kind="int", value_of=status_is(INSTANCE_RETURNED)),
        MetricSpec("withdrawn", "Rút", kind="int", value_of=status_is(INSTANCE_WITHDRAWN)),
        MetricSpec("pending", "Đang chờ", kind="int", good="down", snapshot=True, value_of=lambda r: 0),
        MetricSpec("proc_hours_sum", "Tổng giờ xử lý phiên", kind="hours", helper=True,
                  value_of=lambda r: r["proc_hours"] if r.get("proc_hours") is not None else 0),
        MetricSpec("proc_hours_count", "Số phiên có thời gian xử lý", kind="int", helper=True,
                  value_of=lambda r: 1 if r.get("proc_hours") is not None else 0),
        MetricSpec("step_hours_sum", "Tổng giờ mỗi bước", kind="hours", helper=True,
                  value_of=lambda r: sum(r["step_hours"])),
        MetricSpec("step_hours_count", "Số bước có thời gian", kind="int", helper=True,
                  value_of=lambda r: len(r["step_hours"])),
        MetricSpec("step_overdue", "Số bước quá hạn", kind="int", helper=True,
                  value_of=lambda r: r["overdue_count"]),
        MetricSpec("step_due_known", "Số bước có hạn", kind="int", helper=True,
                  value_of=lambda r: r["due_known"]),
    ]
    derived = [
        DerivedSpec("avg_proc_hours", "Thời gian xử lý phiên TB", num="proc_hours_sum",
                   den="proc_hours_count", kind="hours", good="down", scale=1),
        DerivedSpec("avg_step_hours", "Thời gian mỗi bước TB", num="step_hours_sum",
                   den="step_hours_count", kind="hours", good="down", scale=1),
        DerivedSpec("step_overdue_rate", "Tỷ lệ bước quá hạn", num="step_overdue",
                   den="step_due_known", good="down"),
    ]
    dimensions = {
        "entity": DimensionSpec("entity", "Loại chứng từ", key_of=lambda r: (
            [(r["entity"], svc.ENTITY_LABELS.get(r["entity"], r["entity"]))] if r.get("entity") else [])),
        "approver": DimensionSpec("approver", "Người duyệt", key_of=lambda r: r["approvers"]),
        "node_name": DimensionSpec("node_name", "Bước", key_of=lambda r: r["node_names"]),
    }
    return ReportSpec(date_of=lambda r: to_local_date(r.get("started_at")), metrics=metrics,
                      derived=derived, dimensions=dimensions, breakdowns=dimensions)


def _legacy_build_summary(db, user, profile, period, group_by) -> dict:
    allowed = svc.allowed_source_entities(db, user)

    def fetch(d_from, d_to):
        return _legacy_fetch_rows(db, user, profile, allowed, d_from, d_to)

    data = build_report(fetch, _legacy_build_spec(), period, group_by=group_by,
                        snapshot=svc.make_snapshot(db, user, profile, allowed, period))
    missing = [e for e in svc.APPROVAL_REPORT_SOURCES if e not in allowed]
    if missing:
        labels = ", ".join(svc.ENTITY_LABELS.get(e, e) for e in missing)
        data["notes"] = data.get("notes", []) + [f"Không có quyền đọc nên KHÔNG tính: {labels}."]
    return data


# ── So khớp có DUNG SAI cho số thực (xem docstring đầu tệp) ─────────────────────────────────
_FLOAT_TOL = 1e-6


def _assert_equivalent(old, new, path="$"):
    if isinstance(old, dict):
        assert isinstance(new, dict), f"{path}: {new!r} không phải dict"
        assert old.keys() == new.keys(), f"{path}: khóa khác nhau {old.keys()} vs {new.keys()}"
        for k in old:
            _assert_equivalent(old[k], new[k], f"{path}.{k}")
    elif isinstance(old, list):
        assert isinstance(new, list), f"{path}: {new!r} không phải list"
        assert len(old) == len(new), f"{path}: độ dài khác nhau {len(old)} vs {len(new)}"
        for i, (a, b) in enumerate(zip(old, new)):
            _assert_equivalent(a, b, f"{path}[{i}]")
    elif isinstance(old, float) or isinstance(new, float):
        if old is None or new is None:
            assert old == new, f"{path}: {old!r} != {new!r}"
        else:
            assert abs(old - new) < _FLOAT_TOL, f"{path}: {old} != {new}"
    else:
        assert old == new, f"{path}: {old!r} != {new!r}"


# ── Fixture phong phú — 3 loại chứng từ, đủ trạng thái, bước tuần tự + song song, hạn xử lý ──
def _document(db, seed) -> Document:
    dt = DocType(code=f"QX{db.query(DocType).count()}", name="Loại test", id_scheme=2, number_when=2)
    db.add(dt)
    db.flush()
    doc = Document(origin=1, doc_type_id=dt.id, company_id=seed.company_id,
                   owner_employee_id=seed.emp_req_id, title="VB gom SQL",
                   created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(doc)
    db.flush()
    return doc


def _vehicle_booking(db, seed) -> VehicleBooking:
    vb = VehicleBooking(company_id=seed.company_id, department_id=seed.dept_id,
                        requester_id=seed.emp_req_id)
    db.add(vb)
    db.flush()
    return vb


def _rich_fixture(db, seed, cmp_anchor: datetime):
    """Dựng phiên trải 3 loại chứng từ + 1 phiên nằm TRONG kỳ so sánh (`cmp_anchor`)."""
    sr = _seal_request(db, company_id=seed.company_id, department_id=seed.dept_id,
                       requester_id=seed.emp_req_id)
    doc = _document(db, seed)
    vb = _vehicle_booking(db, seed)
    db.flush()

    #  seal_request: 2 BƯỚC TUẦN TỰ (bước 2 đo từ lúc bước 1 quyết, không từ start) — APPROVED.
    s1 = datetime(2026, 1, 10, 5, 0, 0)     # +2h từ start 03:00
    s2 = datetime(2026, 1, 10, 8, 0, 0)     # +3h từ bước 1
    i1 = _instance(db, entity="seal_request", entity_id=sr.id, started_at=datetime(2026, 1, 10, 3, 0, 0),
                  finished_at=s2, status=INSTANCE_APPROVED)
    _task(db, instance_id=i1.id, node_seq=1, assignee_employee_id=seed.emp_tp_id, decided_at=s1,
         due_at=datetime(2026, 1, 10, 6, 0, 0), node_name="Trưởng phòng duyệt")   # ĐÚNG hạn
    #  node_name TRÙNG với i6/i7 (dưới) CÓ CHỦ Ý — chiều "Bước" gom theo TÊN, không theo phiên
    #  gốc, nên nhiều phiên khác entity vẫn cộng chung một khóa "Điều phối xe" là ĐÚNG (không
    #  phải lỗi chọn tên trùng tình cờ) — xem tổng ở `_grant_viewer`/bài kiểm không hòa điểm.
    _task(db, instance_id=i1.id, node_seq=2, assignee_employee_id=seed.emp_nstm_id, decided_at=s2,
         due_at=datetime(2026, 1, 10, 7, 0, 0), node_name="Điều phối xe")     # QUÁ hạn

    #  seal_request: REJECTED, không bước nào có hạn.
    r_start, r_end = datetime(2026, 1, 15, 2, 0, 0), datetime(2026, 1, 15, 4, 0, 0)
    i2 = _instance(db, entity="seal_request", entity_id=sr.id, started_at=r_start, finished_at=r_end,
                  status=INSTANCE_REJECTED)
    _task(db, instance_id=i2.id, node_seq=1, assignee_employee_id=seed.emp_tp_id, decided_at=r_end,
         node_name="Trưởng phòng duyệt")

    #  seal_request: ĐANG CHẠY (không `finished_at`) — không góp `proc_hours`, vẫn góp `sessions`.
    i3 = _instance(db, entity="seal_request", entity_id=sr.id, started_at=datetime(2026, 1, 20, 1, 0, 0),
                  finished_at=None, status=INSTANCE_RUNNING)
    _task(db, instance_id=i3.id, node_seq=1, assignee_employee_id=seed.emp_tp_id, decided_at=None,
         node_name="Trưởng phòng duyệt")

    #  document: RETURNED, BƯỚC SONG SONG (node_seq=1, 2 task thật + 1 tự-qua-vì-trùng bị loại).
    a, b, dup = (datetime(2026, 2, 5, 5, 0, 0), datetime(2026, 2, 5, 7, 0, 0),
                datetime(2026, 2, 5, 4, 0, 0))
    i4 = _instance(db, entity="document", entity_id=doc.id, started_at=datetime(2026, 2, 5, 3, 0, 0),
                  finished_at=b, status=INSTANCE_RETURNED)
    #  Hai task THẬT dùng CÙNG tên bước "Song song" có chủ ý (chiều "Bước" chỉ cần PHÂN BIỆT
    #  theo (phiên, tên) — DISTINCT đã gộp về 1 khóa cho phiên này; không ảnh hưởng luật M6 vì
    #  M6 đo theo `node_seq`/`decided_at`, không theo tên bước).
    _task(db, instance_id=i4.id, node_seq=1, assignee_employee_id=seed.emp_tp_id, decided_at=a,
         node_name="Song song")
    _task(db, instance_id=i4.id, node_seq=1, assignee_employee_id=seed.emp_nstm_id, decided_at=b,
         node_name="Song song")
    _task(db, instance_id=i4.id, node_seq=1, assignee_employee_id=seed.emp_backup_id, decided_at=dup,
         node_name="Song song", status=TASK_SKIPPED_DUPLICATE)

    #  document: WITHDRAWN, 1 bước, KHÔNG approver (assignee=0 — bị loại khỏi chiều người duyệt,
    #  PHẢI vẫn góp khóa "(Chưa gắn)" ở chiều Người duyệt — canh ở bài kiểm).
    i5 = _instance(db, entity="document", entity_id=doc.id, started_at=datetime(2026, 2, 10, 1, 0, 0),
                  finished_at=datetime(2026, 2, 10, 2, 0, 0), status=INSTANCE_WITHDRAWN)
    _task(db, instance_id=i5.id, node_seq=1, assignee_employee_id=0, decided_at=datetime(2026, 2, 10, 2, 0, 0),
         node_name="Trưởng phòng duyệt")

    #  vehicle_booking: 2 phiên APPROVED trong tháng 3 — tách bước có CẢ có-hạn lẫn vô-hạn.
    i6 = _instance(db, entity="vehicle_booking", entity_id=vb.id, started_at=datetime(2026, 3, 1, 1, 0, 0),
                  finished_at=datetime(2026, 3, 2, 1, 0, 0), status=INSTANCE_APPROVED)
    _task(db, instance_id=i6.id, node_seq=1, assignee_employee_id=seed.emp_tp_id,
         decided_at=datetime(2026, 3, 2, 1, 0, 0), node_name="Điều phối xe")   # không hạn
    i7 = _instance(db, entity="vehicle_booking", entity_id=vb.id, started_at=datetime(2026, 3, 25, 1, 0, 0),
                  finished_at=datetime(2026, 3, 25, 3, 0, 0), status=INSTANCE_APPROVED)
    _task(db, instance_id=i7.id, node_seq=1, assignee_employee_id=seed.emp_nstm_id,
         decided_at=datetime(2026, 3, 25, 3, 0, 0), node_name="Điều phối xe")

    #  2 phiên "lấp đầy" (filler) — KHÔNG kiểm tra hành vi mới, CHỈ để tổng theo entity/approver/
    #  node_name không HÒA ĐIỂM ở chỉ số xếp hạng ("sessions"): thứ tự hòa điểm của `groups`/
    #  `breakdowns` CHƯA BAO GIỜ là hợp đồng (không `ORDER BY` tường minh ở cả bản cũ lẫn bản
    #  SQL mới — xem docstring `report_fan_groups.py`), nên bài kiểm tương đương PHẢI tránh dữ
    #  liệu hòa điểm thay vì cố tái tạo một thứ tự không có thật.
    for i in range(2):
        f = _instance(db, entity="vehicle_booking", entity_id=vb.id,
                     started_at=datetime(2026, 3, 10, 1, 0, 0) + timedelta(hours=i),
                     finished_at=datetime(2026, 3, 10, 2, 0, 0) + timedelta(hours=i),
                     status=INSTANCE_APPROVED)
        _task(db, instance_id=f.id, node_seq=1, assignee_employee_id=seed.emp_req_id,
             decided_at=datetime(2026, 3, 10, 2, 0, 0) + timedelta(hours=i), node_name="Filler")

    #  một phiên NẰM TRONG kỳ so sánh — bắt buộc để `compare` không rỗng (L1 hợp khóa).
    i8 = _instance(db, entity="seal_request", entity_id=sr.id, started_at=cmp_anchor,
                  finished_at=cmp_anchor + timedelta(hours=4), status=INSTANCE_APPROVED)
    _task(db, instance_id=i8.id, node_seq=1, assignee_employee_id=seed.emp_backup_id,
         decided_at=cmp_anchor + timedelta(hours=4), node_name="Trưởng phòng duyệt")

    db.commit()


def _grant_viewer(db, seed, cap_quyen):
    return _viewer(db, seed, cap_quyen, approval_flow=_AF,
                  seal_request=dict(scope="all", read=True),
                  document=dict(scope="all", read=True),
                  vehicle_booking=dict(scope="all", read=True))


@pytest.mark.parametrize("group_by", [None, "entity", "approver", "node_name"])
def test_gom_sql_khop_ban_cu_previous(db, seed, cap_quyen, group_by):
    """So khớp TOÀN BỘ dict trả về (`totals`/`trend`/`groups`/`breakdowns`/`notes`) giữa bản SQL
    mới và bản Python cũ, `compare=previous` — kỳ so sánh CÓ dữ liệu thật (không rỗng)."""
    from app.core.auth import get_perm_profile
    period = parse_period({"preset": "custom", "date_from": "2026-01-01", "date_to": "2026-03-31",
                           "compare": "previous"}, today=datetime(2026, 4, 1).date())
    cmp_anchor = datetime.combine(period.compare_from, time(3, 0, 0)) + timedelta(days=3)
    _rich_fixture(db, seed, cmp_anchor=cmp_anchor)
    viewer = _grant_viewer(db, seed, cap_quyen)
    profile = get_perm_profile(db, viewer)
    old = _legacy_build_summary(db, viewer, profile, period, group_by)
    new = svc.build_summary(db, viewer, profile, period, group_by)
    _assert_equivalent(old, new)
    #  Canh KHÔNG rỗng — nếu fixture lỗi (phiên rơi ra ngoài kỳ so sánh) thì test này vô nghĩa.
    assert old["totals"]["current"]["sessions"] >= 7
    assert old["totals"]["compare"]["sessions"] >= 1


def test_gom_sql_khop_ban_cu_compare_year(db, seed, cap_quyen):
    """`compare=year` — nhánh dời trục theo NĂM (khác `previous`, dời theo số ngày)."""
    from app.core.auth import get_perm_profile
    period = parse_period({"preset": "custom", "date_from": "2026-01-01", "date_to": "2026-03-31",
                           "compare": "year"}, today=datetime(2026, 4, 1).date())
    _rich_fixture(db, seed, cmp_anchor=datetime(2025, 2, 14, 3, 0, 0))
    viewer = _grant_viewer(db, seed, cap_quyen)
    profile = get_perm_profile(db, viewer)
    old = None
    for group_by in (None, "entity", "approver", "node_name"):
        old = _legacy_build_summary(db, viewer, profile, period, group_by)
        new = svc.build_summary(db, viewer, profile, period, group_by)
        _assert_equivalent(old, new)
    assert old["totals"]["compare"]["sessions"] >= 1
