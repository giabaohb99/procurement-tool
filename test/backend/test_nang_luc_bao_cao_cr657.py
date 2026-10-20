"""duoc-CR-657 (D1d) — thống kê năng lực: trung vị/p90/max đúng, ngưỡng ≥ 5 mẫu, loại dòng ước tính, phạm vi, số truy vấn cố định,
gác khóa báo cáo 16 (summary / export / load), hàm cho trợ lý (xếp hạng, bỏ số khi thiếu khóa), ĐMH `received` = xong."""
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.capability_codes import CycleKind, CycleOutcome, CycleRole
from app.core.database import get_db
from app.core.subject_match import SUBJECT_ROLE
from app.main import app
from app.modules.capability import ai_contract, cycle_builder, stats_math
from app.modules.capability.model import WorkCycle
from app.modules.capability.stats_service import StatsFilter, fetch_stats, task_type_stats
from app.modules.change_log.model import ChangeLog
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.work.task_type_model import WorkTaskType

from ho_so_lam_viec_factory import make_company, make_dept, make_person
from lich_lam_viec_factory import count_queries

NOW = datetime(2026, 10, 20, 3, 0)
D_FROM, D_TO = date(2026, 8, 1), date(2026, 10, 20)
PR, TASK, VEH = int(CycleKind.PURCHASE_REQUEST), int(CycleKind.WORK_TASK), int(CycleKind.VEHICLE_BOOKING)
_ids = iter(range(1, 10**6))


def f(**kw) -> StatsFilter:
    return StatsFilter(date_from=D_FROM, date_to=D_TO, **kw)


def cycle(db, emp, days, *, kind=PR, type_id=0, rework=0, est=False, role=CycleRole.HANDLER, dept=0, company=0,
          late=None, outcome=CycleOutcome.DONE, est_h=None, act_h=None):
    start = datetime(2026, 9, 1, 1, 0)
    db.add(WorkCycle(kind=kind, entity_id=next(_ids), role=int(role), employee_id=emp, company_id=company, department_id=dept,
                     task_type_id=type_id, started_at=start, done_at=start + timedelta(days=days) if outcome == CycleOutcome.DONE else None,
                     outcome=int(outcome), cycle_hours=days * 24.0, rework_count=rework, is_estimated=est, is_late=late,
                     estimate_hours=est_h, actual_hours=act_h, review_outcome=0, computed_at=NOW))


@pytest.fixture
def world(db):
    co = make_company(db, "C1")
    d1, d2 = make_dept(db, co, "D1"), make_dept(db, co, "D2")
    a_u, a = make_person(db, "A", co, d1)
    b_u, b = make_person(db, "B", co, d2)
    c_u, c = make_person(db, "C", co, d1)
    tt = WorkTaskType(company_id=co.id, code="T1", name="Thiết kế", is_active=True)
    db.add(tt)
    db.commit()
    return type("W", (), dict(co=co, d1=d1, d2=d2, a=a, b=b, c=c, tt=tt, a_u=a_u))


# ── phần tính thuần ──────────────────────────────────────────────────────────

def test_percentile_noi_suy_va_trung_vi_p90_max():
    assert stats_math.percentile([1, 2, 3, 4, 5], 0.5) == 3
    assert stats_math.percentile([1.0, 2.0], 0.5) == 1.5
    assert stats_math.percentile([7.0], 0.9) == 7.0
    samples = [stats_math.Sample(d * 24.0, r, late, None, None)
               for d, r, late in ((1, 0, False), (2, 0, False), (3, 1, True), (4, 0, None), (10, 1, True))]
    s = stats_math.summarize(samples, n_estimated=2)
    assert (s["n_done"], s["n_estimated"], s["below_threshold"]) == (5, 2, False)
    assert (s["mean_days"], s["p50_days"], s["max_days"]) == (4.0, 3.0, 10.0)
    assert s["p90_days"] == 7.6                          # 4 + (10-4)*0.6
    assert s["rework_rate"] == 0.4 and s["first_pass_rate"] == 0.6
    assert s["late_rate"] == 0.5                         # 2/4 phiếu có hạn


def test_duoi_nguong_mau_khong_co_so_nhung_van_co_n_done():
    s = stats_math.summarize([stats_math.Sample(24.0, 0, None, None, None)] * 4)
    assert s["n_done"] == 4 and s["below_threshold"] is True
    assert all(s[k] is None for k in ("mean_days", "p50_days", "p90_days", "max_days", "rework_rate", "first_pass_rate"))


def test_ti_le_thuc_te_tren_uoc_luong_chi_tinh_dong_co_ca_hai():
    samples = [stats_math.Sample(24.0, 0, None, 2.0, 3.0)] * 3 + [stats_math.Sample(24.0, 0, None, None, 5.0)] * 2
    assert stats_math.summarize(samples)["est_ratio_p50"] == 1.5


# ── truy vấn thật ────────────────────────────────────────────────────────────

def test_nhom_theo_loai_va_nguoi_dong_uoc_tinh_bi_loai_khoi_so_lieu(db, world):
    for d in (1, 2, 3, 4, 10):
        cycle(db, world.a.id, d, dept=world.d1.id, company=world.co.id)
    for d in (5, 5):
        cycle(db, world.b.id, d, dept=world.d2.id, company=world.co.id)           # B chỉ 2 mẫu
    for _ in range(30):
        cycle(db, world.a.id, 0.01, kind=VEH, est=True, dept=world.d1.id, company=world.co.id)   # đặt xe nhập từ hệ cũ
    cycle(db, world.a.id, 1, role=CycleRole.CREATOR)                                # vai khác
    cycle(db, world.a.id, 0, outcome=CycleOutcome.CANCELLED)                        # không xong
    db.commit()
    data = fetch_stats(db, f(unrestricted=True))
    people = {(p["kind"], p["employee_id"]): p for p in data["people"]}
    a = people[(PR, world.a.id)]
    assert a["n_done"] == 5 and a["p50_days"] == 3.0 and a["max_days"] == 10.0 and a["employee_code"] == "A"
    assert people[(PR, world.b.id)]["below_threshold"] is True and people[(PR, world.b.id)]["p50_days"] is None
    veh = people[(VEH, world.a.id)]
    assert veh["n_done"] == 0 and veh["n_estimated"] == 30 and veh["p50_days"] is None     # không lọt vào p50
    types = {t["kind"]: t for t in data["types"]}
    assert types[PR]["n_done"] == 7 and types[PR]["kind_label"] == "Yêu cầu mua hàng"
    assert data["n_estimated"] == 30 and data["min_samples"] == 5


def test_loc_phong_ban_cong_ty_loai_viec_va_ten_loai_viec(db, world):
    for d in range(1, 6):
        cycle(db, world.a.id, d, kind=TASK, type_id=world.tt.id, dept=world.d1.id, company=world.co.id)
        cycle(db, world.b.id, d, kind=TASK, type_id=0, dept=world.d2.id, company=world.co.id)
        cycle(db, world.c.id, d, kind=PR, dept=world.d1.id, company=999)
    db.commit()
    rows = task_type_stats(db, f(department_ids=(world.d1.id,), company_id=world.co.id))
    assert {(r["employee_id"], r["task_type_name"]) for r in rows} == {(world.a.id, "Thiết kế")}
    names = {t["task_type_name"] for t in task_type_stats(db, f(kinds=(TASK,), unrestricted=True), by_person=False)}
    assert names == {"Thiết kế", "Chưa chọn loại việc"}
    assert len(task_type_stats(db, f(task_type_ids=(world.tt.id,), unrestricted=True))) == 1


def test_khong_truyen_pham_vi_thi_rong_va_khong_truy_van(db, world):
    cycle(db, world.a.id, 1)
    db.commit()
    data, queries = count_queries(db, lambda: fetch_stats(db, f()))
    assert data["types"] == [] and data["people"] == [] and queries == []


def test_so_truy_van_co_dinh_voi_5_va_200_nguoi(db, world):
    for d in range(1, 8):
        cycle(db, world.a.id, d, kind=TASK, type_id=world.tt.id)
    db.commit()
    _, few = count_queries(db, lambda: fetch_stats(db, f(unrestricted=True)))
    for i in range(200):
        _u, e = make_person(db, f"X{i}", world.co, world.d1)
        for d in range(1, 7):
            cycle(db, e.id, d, kind=TASK, type_id=world.tt.id)
    db.commit()
    data, many = count_queries(db, lambda: fetch_stats(db, f(unrestricted=True)))
    assert len(data["people"]) == 201 and len(many) == len(few) <= 4


# ── đơn mua hàng «Đã nhận đủ» = xong ─────────────────────────────────────────

def test_don_mua_hang_received_la_xong_va_lay_moc_nhan_du(db, world):
    po = PurchaseOrder(code="DMH9", status="received", company_id=world.co.id, nspt_id=world.a.id,
                       created_at=datetime(2026, 10, 1, 1, 0), updated_at=datetime(2026, 10, 9, 1, 0))
    db.add(po)
    db.flush()
    db.add(ChangeLog(table_name="tab_purchase_order", row_id=po.id, op=2, field="status", before_value="partial",
                     after_value="received", created_at=datetime(2026, 10, 6, 1, 0)))
    db.commit()
    cycle_builder.build_all(db, None, datetime(2026, 10, 30), {int(CycleKind.PURCHASE_ORDER)})
    row = db.query(WorkCycle).filter_by(kind=int(CycleKind.PURCHASE_ORDER), role=int(CycleRole.HANDLER)).one()
    assert row.outcome == int(CycleOutcome.DONE) and row.done_at == datetime(2026, 10, 6, 1, 0) and row.is_estimated is False


# ── API: gác khóa 16 ─────────────────────────────────────────────────────────

@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_api_thieu_khoa_16_la_403_ca_ba_duong_con_co_khoa_la_200(db, world, cap_quyen, gan_bao_cao, client_as):
    user, _ = make_person(db, "VIEWER", world.co, world.d1)
    role = cap_quyen(user.id, "setting", scope="all", read=True, export=True)
    db.commit()
    client = client_as(user)
    paths = ["/api/work-capability/summary", "/api/work-capability/summary/export",
             f"/api/work-capability/load?company_id={world.co.id}"]
    assert [client.get(p).status_code for p in paths] == [403, 403, 403]
    gan_bao_cao(SUBJECT_ROLE, role.id, 16)
    db.commit()
    assert [client.get(p).status_code for p in paths] == [200, 200, 200]


def test_api_co_khoa_16_nhung_thieu_setting_export_van_403_o_export(db, world, cap_quyen, gan_bao_cao, client_as):
    user, _ = make_person(db, "RDONLY", world.co, world.d1)
    role = cap_quyen(user.id, "setting", scope="all", read=True, export=False)
    gan_bao_cao(SUBJECT_ROLE, role.id, 16)
    db.commit()
    client = client_as(user)
    assert client.get("/api/work-capability/summary").status_code == 200
    assert client.get("/api/work-capability/summary/export").status_code == 403


def test_api_summary_tra_ve_so_lieu_va_loc_sai_la_422(db, world, cap_quyen, gan_bao_cao, client_as):
    for d in (1, 2, 3, 4, 5):
        cycle(db, world.a.id, d, company=world.co.id, dept=world.d1.id)
    user, _ = make_person(db, "ADM", world.co, world.d1)
    role = cap_quyen(user.id, "setting", scope="all", read=True, export=True)
    gan_bao_cao(SUBJECT_ROLE, role.id, 16)
    db.commit()
    client = client_as(user)
    qs = {"preset": "custom", "date_from": "2026-08-01", "date_to": "2026-10-20"}
    data = client.get("/api/work-capability/summary", params=qs).json()["data"]
    assert data["period"]["date_from"] == "2026-08-01" and data["people"][0]["p50_days"] == 3.0
    assert client.get("/api/work-capability/summary", params={**qs, "kind": 99}).status_code == 422
    assert client.get("/api/work-capability/summary", params={**qs, "role": 9}).status_code == 422
    res = client.get("/api/work-capability/summary/export", params=qs)
    assert res.status_code == 200 and res.headers["content-type"].startswith("application/vnd.openxmlformats")


# ── hàm cho trợ lý ───────────────────────────────────────────────────────────

def test_goi_y_xep_hang_co_so_khi_co_khoa_va_chi_thu_tu_khi_khong_co(db, world, cap_quyen, gan_bao_cao):
    for d in (2, 3, 4, 5, 6):
        cycle(db, world.a.id, d, company=world.co.id, dept=world.d1.id)            # A: đủ mẫu, p50 = 4
        cycle(db, world.c.id, d - 1, company=world.co.id, dept=world.d1.id)        # C: đủ mẫu, p50 = 3, nhanh hơn
    cycle(db, world.b.id, 1, company=world.co.id, dept=world.d2.id)                # B: thiếu mẫu
    admin, _ = make_person(db, "ADM", world.co, world.d1)
    plain, _ = make_person(db, "PLAIN", world.co, world.d1)
    role = cap_quyen(admin.id, "setting", scope="all", read=True)
    gan_bao_cao(SUBJECT_ROLE, role.id, 16)
    db.commit()

    out = ai_contract.suggest_assignees(db, admin, kind=PR, company_id=world.co.id, now=NOW, limit=10)
    top = [r["employee_code"] for r in out]
    assert top[:2] == ["C", "A"] and top.index("B") > top.index("A")               # đủ mẫu + nhanh trước; thiếu mẫu sau
    assert out[0]["stats"]["p50_days"] == 3.0 and "load" in out[0] and "BELOW_THRESHOLD" in next(r for r in out if r["employee_code"] == "B")["reasons"]

    blind = ai_contract.suggest_assignees(db, plain, kind=PR, company_id=world.co.id, now=NOW, limit=10)
    assert [r["employee_code"] for r in blind] == top and all("stats" not in r and "load" not in r for r in blind)


def test_goi_y_khong_pham_vi_la_rong_va_lay_toi_da_limit(db, world):
    user, _ = make_person(db, "U", world.co, world.d1)
    db.commit()
    assert ai_contract.suggest_assignees(db, user, kind=PR, now=NOW) == []
    assert len(ai_contract.suggest_assignees(db, user, kind=PR, company_id=world.co.id, now=NOW, limit=1)) == 1
    with pytest.raises(ValueError):
        ai_contract.suggest_assignees(db, user, kind=999, company_id=world.co.id)


def test_get_capability_can_khoa_16(db, world, cap_quyen, gan_bao_cao):
    for d in range(1, 6):
        cycle(db, world.a.id, d)
    admin, _ = make_person(db, "ADM", world.co, world.d1)
    plain, _ = make_person(db, "PLAIN", world.co, world.d1)
    role = cap_quyen(admin.id, "setting", scope="all", read=True)
    gan_bao_cao(SUBJECT_ROLE, role.id, 16)
    db.commit()
    with pytest.raises(ai_contract.CapabilityForbidden):
        ai_contract.get_capability(db, plain, world.a.id, now=NOW)
    cap = ai_contract.get_capability(db, admin, world.a.id, now=NOW)
    assert cap["by_type"][0]["p50_days"] == 3.0 and cap["load"]["employee_code"] == "A"
