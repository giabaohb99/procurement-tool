"""duoc-CR-641 phase 04 — snapshot tuần: nhóm so sánh, chuỗi phiếu, thời gian duyệt, đường đi, chưa đo được, xu hướng,
khuôn dữ liệu cho pha 4 (chỉ số/mã, không văn bản tự do), idempotent, và SỐ TRUY VẤN cố định."""
import json
from datetime import date, datetime, timedelta

import pytest

from app.core.usage_codes import CohortKind, UiEventType, UnmeasuredReason
from app.modules.approval import instance_model as im
from app.modules.role.model import Role
from app.modules.usage_profile import snapshot_metrics_flow as flow
from app.modules.usage_profile.cohort import Cohort, assign_cohorts, cohort_stats
from app.modules.usage_profile.metric_catalog import METRIC_CATALOG
from app.modules.usage_profile.metric_stats import median, percentile
from app.modules.usage_profile.model import UsageDaily, UserUsageLabel, UserUsageSnapshot
from app.modules.usage_profile.snapshot_builder import build_snapshots, last_full_week_start
from app.modules.usage_profile.snapshot_paths import path_metrics
from app.modules.user.model import UserRole

from ho_so_lam_viec_factory import (add_audit, add_ui, make_company, make_dept, make_person, vn)
from lich_lam_viec_factory import count_queries

WEEK = date(2026, 1, 26)                    # thứ Hai; cửa sổ 4 tuần = 05/01 .. 01/02
FIRST = date(2026, 1, 5)


def add_daily(db, user, emp, day, **kw):
    base = dict(user_id=user.id, day=day, employee_id=emp.id, company_id=emp.company_id,
                department_id=emp.department_id, is_workday=day.weekday() < 6,
                work_capacity=1.0 if day.weekday() < 6 else 0.0, active=day.weekday() < 6,
                api_reads=10, api_writes=4, hourly=[0] * 8 + [3] * 8 + [0] * 8)
    base.update(kw)
    db.add(UsageDaily(**base))


def make_world(db, n, role=None, tag="U", days=28, **daily_kw):
    company = make_company(db, f"CW{tag}")
    dept = make_dept(db, company, f"DW{tag}")
    role = role or Role(code=f"R{tag}", name=f"Vai trò {tag}")
    if role.id is None:
        db.add(role)
        db.flush()
    people = []
    for i in range(n):
        user, emp = make_person(db, f"{tag}{i:02d}", company, dept, hire=date(2025, 1, 1))
        db.add(UserRole(user_id=user.id, role_id=role.id))
        for d in range(days):
            add_daily(db, user, emp, FIRST + timedelta(days=d), **daily_kw)
        people.append((user, emp))
    db.commit()
    return people, role


def snap(db, user, week=WEEK):
    return db.query(UserUsageSnapshot).filter_by(user_id=user.id, period_start=week).one()


# ── thống kê ────────────────────────────────────────────────────────────────

def test_percentile_noi_suy_tuyen_tinh():
    xs = [2, 4, 6, 8, 30]
    assert median(xs) == 6 and percentile(xs, 0.9) == pytest.approx(21.2)
    assert percentile([], 0.5) is None


def test_tuan_ket_thuc_gan_nhat():
    assert last_full_week_start(date(2026, 2, 2)) == date(2026, 1, 26)      # thứ Hai chạy job → tuần vừa qua
    assert last_full_week_start(date(2026, 2, 5)) == date(2026, 1, 26)


# ── nhóm so sánh ────────────────────────────────────────────────────────────

def _roles(spec):
    """spec: {role_id: (code, [user_id...])}"""
    roles = {rid: (code, code) for rid, (code, _) in spec.items()}
    ur = [(u, rid) for rid, (_, users) in spec.items() for u in users]
    return roles, ur


def test_cohort_chon_vai_tro_cu_the_nhat_du_5_nguoi():
    a, b = list(range(1, 7)), list(range(1, 31))          # A: 6 người (cũng thuộc B), B: 30 người
    roles, ur = _roles({1: ("A", a), 2: ("B", b)})
    out = assign_cohorts({u: 1 for u in b}, ur, roles)
    assert out[1] == Cohort(int(CohortKind.ROLE), 1, 6)     # có cả A và B → chọn A (ít người hơn nhưng ≥ 5)
    assert out[20] == Cohort(int(CohortKind.ROLE), 2, 30)


def test_cohort_vai_tro_chi_4_nguoi_roi_ve_vai_tro_lon_hon_roi_phap_nhan_roi_toan_cty():
    roles, ur = _roles({1: ("A", [1, 2, 3, 4]), 2: ("B", list(range(1, 31)))})
    assert assign_cohorts({u: 1 for u in range(1, 31)}, ur, roles)[1].key == 2     # A 4 người → B
    roles, ur = _roles({1: ("A", [1, 2, 3, 4])})
    out = assign_cohorts({u: 7 for u in range(1, 7)}, ur, roles)                   # không vai trò nào ≥ 5 → pháp nhân
    assert out[1] == Cohort(int(CohortKind.COMPANY), 7, 6)
    out = assign_cohorts({1: 7, 2: 7, 3: 8, 4: 8}, ur, roles)                       # pháp nhân < 5 → toàn công ty
    assert out[1] == Cohort(int(CohortKind.ALL), 0, 4)


def test_cohort_khong_chon_vai_tro_quan_tri():
    users = list(range(1, 11))
    roles = {1: ("admin", "Quản trị"), 2: ("ADMINISTRATOR", "Quản trị cũ")}
    out = assign_cohorts({u: 0 for u in users}, [(u, 1) for u in users] + [(u, 2) for u in users], roles)
    assert all(c.kind == int(CohortKind.ALL) for c in out.values())


def test_trung_vi_nhom_bo_nguoi_khong_co_gia_tri():
    cohorts = {1: Cohort(1, 1, 3), 2: Cohort(1, 1, 3), 3: Cohort(1, 1, 3)}
    st = cohort_stats(cohorts, {1: {"x": 1.0}, 2: {"x": 3.0}, 3: {}})
    assert st[(1, 1)]["x"][0] == 2.0


# ── chuỗi phiếu ─────────────────────────────────────────────────────────────

def test_chuoi_phieu_tao_sua3_gui_sua_tra_ve(db):
    (u, emp), (other, _) = make_world(db, 1, tag="S1")[0][0], make_person(db, "BOSS")
    day = WEEK + timedelta(days=1)
    seq = [("create", u), ("update", u), ("update", u), ("update", u), ("submit", u), ("update", u),
           ("return", other)]
    for i, (action, who) in enumerate(seq):
        add_audit(db, who, vn(day, f"09:{i:02d}"), "purchase_order", 77, action, group=2)
    db.commit()
    build_snapshots(db, WEEK)
    m = snap(db, u).metrics["metrics"]
    assert m["drafts_before_submit_p50"]["v"] == 3
    assert m["edits_after_submit_share"]["v"] == 1.0
    assert m["returned_rate"]["v"] == 1.0
    assert snap(db, u).metrics["counts"]["submitted_chain"] == 1


def test_phieu_gui_lan_dau_truoc_cua_so_khong_tinh(db):
    people, _ = make_world(db, 1, tag="S2")
    u, _ = people[0]
    old = FIRST - timedelta(days=20)
    for i, a in enumerate(("create", "submit")):
        add_audit(db, u, vn(old, f"09:{i:02d}"), "purchase_order", 5, a)
    db.commit()
    build_snapshots(db, WEEK)
    assert "drafts_before_submit_p50" in snap(db, u).metrics["unmeasured"]


# ── thời gian duyệt ─────────────────────────────────────────────────────────

def _task(db, emp, hours, order=1, instance=1, node=1, status=im.TASK_APPROVED, decided=None):
    created = vn(WEEK + timedelta(days=1), "08:00")
    t = im.ApprovalTask(instance_id=instance, node_seq=node, order_no=order, assignee_employee_id=emp.id,
                        status=status, created_at=created,
                        decided_at=decided or created + timedelta(hours=hours) if status != im.TASK_PENDING else None)
    db.add(t)
    return t


def test_nam_viec_duyet_2_4_6_8_30_gio_p50_6_p90_noi_suy(db):
    people, _ = make_world(db, 1, tag="S3")
    u, emp = people[0]
    for i, h in enumerate((2, 4, 6, 8, 30)):
        _task(db, emp, h, instance=i + 1)
    for i in range(3):
        _task(db, emp, 0, instance=100 + i, status=im.TASK_PENDING)
    db.commit()
    build_snapshots(db, WEEK)
    m = snap(db, u).metrics
    assert m["metrics"]["approval_wait_p50_h"]["v"] == 6 and m["metrics"]["approval_wait_p90_h"]["v"] == pytest.approx(21.2)
    assert m["metrics"]["pending_now"]["v"] == 3 and m["counts"]["tasks_decided"] == 5


def test_duoi_5_viec_duyet_xong_la_duoi_nguong_khong_phai_0(db):
    people, _ = make_world(db, 1, tag="S4")
    u, emp = people[0]
    _task(db, emp, 3)
    db.commit()
    build_snapshots(db, WEEK)
    m = snap(db, u).metrics
    assert "approval_wait_p50_h" not in m["metrics"]
    assert m["unmeasured"]["approval_wait_p50_h"] == int(UnmeasuredReason.BELOW_THRESHOLD)


def test_buoc_lan_luot_moc_toi_luot_la_luc_nguoi_truoc_quyet_dinh(monkeypatch):
    monkeypatch.setattr(flow, "_sequential_nodes", lambda instances: {(1, 1)})
    t0 = datetime(2026, 1, 27, 1, 0)
    tasks = [(1, 1, 1, 1, 10, im.TASK_APPROVED, t0, t0 + timedelta(hours=2)),
             (2, 1, 1, 2, 11, im.TASK_APPROVED, t0, t0 + timedelta(hours=6))]
    siblings = [(1, 1, 1, t0 + timedelta(hours=2)), (1, 1, 2, t0 + timedelta(hours=6))]
    out = flow.approval_metrics(tasks, siblings, [], {10: 1, 11: 2}, t0 - timedelta(days=1), t0 + timedelta(days=1))
    # người 2 chỉ nhận việc lúc người 1 xong (02:00) → chờ 4h, không phải 6h
    assert out[2].counts["tasks_decided"] == 1
    monkeypatch.setattr(flow, "MIN_TASKS", 1)
    out = flow.approval_metrics(tasks, siblings, [], {10: 1, 11: 2}, t0 - timedelta(days=1), t0 + timedelta(days=1))
    assert out[1].values["approval_wait_p50_h"] == 2 and out[2].values["approval_wait_p50_h"] == 4


def test_duyet_theo_lo_cum_5_quyet_dinh_trong_10_phut():
    t0 = datetime(2026, 1, 27, 2, 0)
    cluster = [(1, t0 + timedelta(minutes=i)) for i in range(5)]
    lone = [(1, t0 + timedelta(hours=3 + i)) for i in range(5)]
    assert flow.batch_approval_share(cluster + lone)[1].values["batch_approval_share"] == 0.5


# ── đường đi ────────────────────────────────────────────────────────────────

def test_hai_tab_xen_ke_khong_tao_bo_ba_gia_va_vong_a_b_a_tinh_vao_loop_share():
    t0 = datetime(2026, 1, 27, 2, 0)
    ev = []
    for i in range(12):                  # tab 1: A,B,A,B,... → toàn bộ ba vòng A→B→A / B→A→B
        ev.append((1, 9, 1, t0 + timedelta(minutes=2 * i), "/a" if i % 2 == 0 else "/b"))
    for i in range(12):                  # tab 2 xen kẽ: C,D,E,... thẳng, KHÔNG nối với tab 1
        ev.append((1, 9, 2, t0 + timedelta(minutes=2 * i + 1), f"/c{i}"))
    out = path_metrics(sorted(ev, key=lambda e: e[3]))[1]
    assert out.lists["top_paths"][0][3] >= 5
    assert not any(p[0].startswith("/c") and p[2] == "/a" for p in out.lists["top_paths"])
    assert out.values["loop_share"] == pytest.approx(10 / 20)     # 10 vòng A↔B trên 20 bộ ba


# ── chưa đo được / xu hướng / khuôn ────────────────────────────────────────

def test_chua_bat_thu_thap_thi_chi_so_pha2_vao_unmeasured_ma_1_khong_ghi_0(db):
    people, _ = make_world(db, 1, tag="S5")
    build_snapshots(db, WEEK)
    m = snap(db, people[0][0]).metrics
    for key, meta in METRIC_CATALOG.items():
        if meta.phase == 2:
            assert key not in m["metrics"], key
            assert m["unmeasured"][key] == int(UnmeasuredReason.NOT_COLLECTED), key
    assert m["context"]["tracking_since"] is None


def test_xu_huong_lay_3_snapshot_truoc_cong_tuan_nay(db):
    people, _ = make_world(db, 1, tag="S6")
    u, _ = people[0]
    for i, weeks_ago in enumerate((3, 2, 1)):
        ps = WEEK - timedelta(weeks=weeks_ago)
        db.add(UserUsageSnapshot(user_id=u.id, period_start=ps, metrics={"metrics": {"active_ratio": {"v": (0.1, 0.2, 0.3)[i]}}}))
    db.commit()
    build_snapshots(db, WEEK)
    trend = snap(db, u).metrics["metrics"]["active_ratio"]["trend"]
    assert trend[:3] == [0.1, 0.2, 0.3] and trend[3] == snap(db, u).metrics["metrics"]["active_ratio"]["v"]


ALLOWED_STRING_PATHS = ("period.start", "period.end", "context.tracking_since", "lists.top_screens.*.0",
                        "lists.module_time.*.0", "lists.top_paths.*.0", "lists.top_paths.*.1", "lists.top_paths.*.2",
                        "lists.first_screen.0", "lists.top_403_routes.*.0")


def _walk(node, path, bad):
    """Mọi lá phải là số/bool/None; chuỗi chỉ ở vị trí trong ALLOWED_STRING_PATHS (`*` = chỉ số hàng)."""
    if isinstance(node, dict):
        for k, v in node.items():
            _walk(v, f"{path}.{k}" if path else str(k), bad)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, f"{path}.{'*' if isinstance(v, list) else i}", bad)
    elif isinstance(node, str):
        if path not in ALLOWED_STRING_PATHS:
            bad.append((path, node))
    elif not (node is None or isinstance(node, (int, float, bool))):
        bad.append((path, node))


def test_khuon_pha_4_chi_so_va_ma_khong_co_van_ban_tu_do(db):
    people, _ = make_world(db, 6, tag="S7")
    u, emp = people[0]
    for i in range(30):
        add_ui(db, u, vn(WEEK + timedelta(days=1), "09:00") + timedelta(minutes=i), UiEventType.PAGE_VIEW, f"/s{i % 4}", tab=1)
    db.query(UsageDaily).filter_by(user_id=u.id, day=FIRST).update(
        {"page_views": 5, "screens": {"/a": [5, 1000, 2]}, "first_route": "/a", "docs": {"purchase_order": {"c": 2}},
         "reports": {"13": 2}, "forbidden_routes": {"/api/x": 5}})
    db.commit()
    build_snapshots(db, WEEK)
    metrics = snap(db, u).metrics
    bad: list = []
    _walk(metrics, "", bad)
    assert bad == []
    assert metrics["period"] == {"start": "2026-01-05", "end": "2026-02-01", "window_weeks": 4}
    assert snap(db, u).schema_version == 1
    assert set(metrics) >= {"period", "subject", "context", "metrics", "lists", "unmeasured", "labels"}
    json.dumps(metrics)                     # tuần tự hóa được


def test_ghi_idempotent_chay_lai_khong_nhan_doi(db):
    make_world(db, 6, tag="S8", http_403=2)
    build_snapshots(db, WEEK)
    n1, l1 = db.query(UserUsageSnapshot).count(), db.query(UserUsageLabel).count()
    build_snapshots(db, WEEK)
    assert (db.query(UserUsageSnapshot).count(), db.query(UserUsageLabel).count()) == (n1, l1) and n1 == 6


def test_cohort_ghi_vao_snapshot_va_trung_vi_nhom(db):
    people, role = make_world(db, 6, tag="S9")
    # người đầu vào ít ngày hơn cả nhóm
    u0, _ = people[0]
    db.query(UsageDaily).filter(UsageDaily.user_id == u0.id, UsageDaily.day > FIRST + timedelta(days=10)).update({"active": False})
    db.commit()
    build_snapshots(db, WEEK)
    s = snap(db, u0)
    assert (s.cohort_kind, s.cohort_key, s.cohort_size) == (int(CohortKind.ROLE), role.id, 6)
    am = s.metrics["metrics"]["active_ratio"]
    assert am["v"] < am["med"] == 1.0


# ── số truy vấn cố định ─────────────────────────────────────────────────────

def _selects(sql):
    return len([s for s in sql if s.lstrip().upper().startswith("SELECT")])


def test_so_truy_van_khong_doi_theo_so_nguoi(db):
    make_world(db, 3, tag="Q1")
    _, few = count_queries(db, lambda: build_snapshots(db, WEEK))
    make_world(db, 12, tag="Q2")
    _, many = count_queries(db, lambda: build_snapshots(db, WEEK))
    assert _selects(few) == _selects(many) and _selects(many) <= 30
    assert db.query(UserUsageSnapshot).count() == 15


def test_xuat_cung_entity_nhieu_tuan_va_bien_dong_xuat_bat_thuong(db):
    from app.modules.export_log.model import ExportLog
    people, _ = make_world(db, 1, tag="X1")
    u, _ = people[0]
    for week_offset in (0, 8, 15):                      # 3 tuần khác nhau của cửa sổ, cùng entity
        db.add(ExportLog(entity="purchase_order", fmt="xlsx", row_count=10, created_by=u.id,
                         created_at=vn(FIRST + timedelta(days=week_offset), "10:00")))
    db.add(ExportLog(entity="supplier", fmt="xlsx", row_count=10, created_by=u.id,
                     created_at=vn(FIRST + timedelta(days=1), "10:00")))
    db.commit()
    build_snapshots(db, WEEK)
    m = snap(db, u).metrics
    assert m["metrics"]["export_entity_weeks_max"]["v"] == 3
    # không có lịch sử 12 tuần trước → không kết luận (None), không phải 0
    assert m["unmeasured"]["export_rows_spike"] == int(UnmeasuredReason.BELOW_THRESHOLD)
