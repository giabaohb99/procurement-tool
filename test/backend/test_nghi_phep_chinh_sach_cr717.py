"""duoc-CR-717 giai đoạn 01 — CHÍNH SÁCH NGHỈ PHÉP + PHÂN BỔ CHÍNH SÁCH (một người).

Ba nhóm: hàm thuần (bảng ví dụ luật D1/D2 + "không phân bổ == như cũ"), cấp / tính lại quỹ qua đường API thật
(TestClient + `world`), và chốt chặn schema. Hàng loạt / xem trước / phạm vi / đếm truy vấn ở
`test_nghi_phep_phan_bo_hang_loat_cr717.py`.

"Hôm nay" bị đóng băng ở 10/06/2026 để bài không trôi theo năm.
"""
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.modules.audit.model import AuditLog
from app.modules.employee.model import Employee
from app.modules.leave import accrual_service, balance_service, policy_assignment_controller
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LeaveAccrualMode, LeavePolicyAssignmentState
from app.modules.leave.policy_allocation_math import AssignmentSpan, compute_allocated, overlaps_year
from app.modules.leave.policy_model import LeavePolicy, LeavePolicyAssignment, LeavePolicyLine
from app.modules.leave.policy_schema import (AssignmentBulk, AssignmentCreate, AssignmentUpdate,
                                             PolicyCreate, PolicyLineItem, PolicyUpdate)

TODAY = date(2026, 6, 10)
YEAR = 2026
FULL, PRORATA, MONTHLY = (int(LeaveAccrualMode.FULL_YEAR), int(LeaveAccrualMode.PRORATA_HIRE),
                          int(LeaveAccrualMode.MONTHLY))


# ── Khung dùng chung (tệp hàng loạt cũng nhập từ đây) ────────────────────────────

def make_type(db, code="annual", **kw):
    kw.setdefault("name", f"Loại {code}")
    kw.setdefault("counts_balance", True)
    kw.setdefault("annual_quota_days", 12.0)
    obj = LeaveType(code=code, **kw)
    db.add(obj)
    db.flush()
    return obj


def make_policy(db, code, lines, active=True):
    """`lines` = {leave_type_id: số ngày/năm}."""
    policy = LeavePolicy(code=code, name=f"Gói {code}", is_active=active)
    db.add(policy)
    db.flush()
    for type_id, days in lines.items():
        db.add(LeavePolicyLine(policy_id=policy.id, leave_type_id=type_id, annual_days=days))
    db.flush()
    return policy


@pytest.fixture
def frozen_today(monkeypatch):
    monkeypatch.setattr(policy_assignment_controller, "vn_today", lambda: TODAY)
    return TODAY


@pytest.fixture
def http(db, frozen_today):
    def call(user, method, path, **kw):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            client = TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})
            return client.request(method, path, **kw)
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_current_user, None)
    return call


@pytest.fixture
def hr(db, world):
    """Nhân sự `a2`: ghi quỹ phép + ghi nhân sự toàn công ty (phạm vi `all`)."""
    actor = world.grant("a2", "leave_balance", scope="all", actions=("read", "write", "create"))
    world.grant("a2", "employee", scope="all", actions=("read", "write"))
    world.grant("a2", "leave_type", scope="all", actions=("read", "write", "create", "delete"))
    return actor


def assign_body(employee_id, policy_id, start="2026-07-01", end=None, **kw):
    body = {"employee_id": employee_id, "policy_id": policy_id, "effective_from": start,
            "effective_to": end, "recalc_current_year": True, "close_previous": False}
    body.update(kw)
    return body


# ── 1. Hàm thuần: bảng ví dụ luật D1 / D2 ────────────────────────────────────────

def _span(start, end, type_id, days):
    return AssignmentSpan(start, end, {type_id: days})


@pytest.mark.parametrize("label,mode,hire,span,expected", [
    ("12→15 từ 01/07", FULL, None, _span(date(2026, 7, 1), None, 1, 15), 13.5),
    ("từ 16/07: tháng 7 còn luật cũ → 13.25 làm tròn 13.5", FULL, None, _span(date(2026, 7, 16), None, 1, 15), 13.5),
    ("từ 15/07 (biên): tháng 7 đã thuộc gói mới → (6×12+6×15)/12 = 13.5", FULL, None, _span(date(2026, 7, 15), None, 1, 15), 13.5),
    ("vào làm 10/03 PRORATA, gói 15 cả năm → 15×10/12", PRORATA, date(2026, 3, 10), _span(date(2026, 1, 1), None, 1, 15), 12.5),
    ("FULL_YEAR vào làm giữa năm, gói 15 cả năm → đủ 15", FULL, date(2026, 8, 20), _span(date(2026, 1, 1), None, 1, 15), 15.0),
    ("kết thúc 14/09 → tháng 9 về luật loại: (8×15+4×12)/12 = 14", FULL, None, _span(date(2026, 1, 1), date(2026, 9, 14), 1, 15), 14.0),
    ("kết thúc 15/09 → tháng 9 còn gói: (9×15+3×12)/12 = 14.25→14.5", FULL, None, _span(date(2026, 1, 1), date(2026, 9, 15), 1, 15), 14.5),
    ("gói không có dòng loại này → luật loại", FULL, None, _span(date(2026, 1, 1), None, 99, 30), 12.0),
    ("phân bổ năm sau → không đụng năm này", FULL, None, _span(date(2027, 1, 1), None, 1, 30), 12.0),
    ("phân bổ năm trước đã hết → không đụng năm này", FULL, None, _span(date(2025, 1, 1), date(2025, 12, 31), 1, 30), 12.0),
    ("MONTHLY vào làm 10/03, gói 24 cả năm → 24×10/12", MONTHLY, date(2026, 3, 10), _span(date(2026, 1, 1), None, 1, 24), 20.0),
    ("PRORATA, đổi gói giữa năm chỉ tính các tháng làm việc: tháng 3-6 @12, 7-12 @24 → (4×12+6×24)/12 = 16", PRORATA,
     date(2026, 3, 10), _span(date(2026, 7, 1), None, 1, 24), 16.0),
    ("vào làm năm sau → 0", PRORATA, date(2027, 2, 1), _span(date(2026, 1, 1), None, 1, 24), 0.0),
])
def test_bang_vi_du_luat(label, mode, hire, span, expected):
    assert compute_allocated(12.0, mode, hire, YEAR, [span], 1) == expected, label


def test_gan_phan_bo_ket_thuc_giua_hai_goi_lay_goi_moi_hon():
    spans = [_span(date(2026, 1, 1), None, 1, 12), _span(date(2026, 7, 1), None, 1, 18)]
    #  Dữ liệu lỡ chồng thì gói bắt đầu MUỘN hơn thắng: 6×12 + 6×18 = 180 / 12 = 15.
    assert compute_allocated(10.0, FULL, None, YEAR, spans, 1) == 15.0


@pytest.mark.parametrize("mode", [FULL, PRORATA, MONTHLY])
@pytest.mark.parametrize("hire", [date(2020, 5, 5), date(2026, 3, 10), date(2026, 3, 20), date(2027, 1, 5), None])
@pytest.mark.parametrize("quota", [12.0, 12.25, 0.0, 15.5])
def test_khong_phan_bo_giong_het_prorate_allocation_cu(mode, hire, quota):
    assert compute_allocated(quota, mode, hire, YEAR, [], 1) == accrual_service.prorate_allocation(
        quota, mode, hire, YEAR)
    #  Phân bổ có nhưng không chạm năm / không có loại này cũng phải ra đúng số cũ.
    other = [_span(date(2024, 1, 1), date(2024, 12, 31), 1, 30), _span(date(2026, 1, 1), None, 99, 30)]
    assert compute_allocated(quota, mode, hire, YEAR, other, 1) == accrual_service.prorate_allocation(
        quota, mode, hire, YEAR)


def test_goi_bang_han_muc_loai_giu_nguyen_lam_tron_le():
    """Gói có số đúng bằng quota lẻ của loại → ra đúng prorate (không bị làm tròn Σ/12 hai lần)."""
    span = _span(date(2026, 1, 1), None, 1, 12.25)
    assert compute_allocated(12.25, PRORATA, date(2026, 3, 10), YEAR, [span], 1) == accrual_service.prorate_allocation(
        12.25, PRORATA, date(2026, 3, 10), YEAR)


def test_overlaps_year_va_trang_thai_dan_xuat():
    assert overlaps_year(date(2026, 12, 31), None, 2026) and not overlaps_year(date(2027, 1, 1), None, 2026)
    assert overlaps_year(date(2020, 1, 1), date(2026, 1, 1), 2026) and not overlaps_year(
        date(2020, 1, 1), date(2025, 12, 31), 2026)
    from app.modules.leave.policy_assignment_plan import assignment_state
    mk = lambda a, b: LeavePolicyAssignment(effective_from=a, effective_to=b)  # noqa: E731
    assert assignment_state(mk(date(2026, 7, 1), None), TODAY) == LeavePolicyAssignmentState.UPCOMING
    assert assignment_state(mk(date(2026, 1, 1), None), TODAY) == LeavePolicyAssignmentState.ACTIVE
    assert assignment_state(mk(date(2026, 1, 1), TODAY), TODAY) == LeavePolicyAssignmentState.ACTIVE
    assert assignment_state(mk(date(2026, 1, 1), date(2026, 6, 9)), TODAY) == LeavePolicyAssignmentState.ENDED


# ── 2. Cấp quỹ qua ensure_balance ────────────────────────────────────────────────

def test_khong_co_phan_bo_nao_ensure_balance_nhu_cu(db, world):
    lt = make_type(db, accrual_mode=PRORATA)
    emp = db.get(Employee, world.emp["a1"])
    emp.hire_date = date(2026, 3, 10)
    db.add(LeavePolicy(code="X", name="Không ai dùng"))
    db.flush()
    row = balance_service.ensure_balance(db, emp, YEAR, lt)
    assert row.allocated_days == accrual_service.prorate_allocation(12.0, PRORATA, emp.hire_date, YEAR) == 10.0


def test_ensure_balance_theo_phan_bo_va_nam_sau(db, world):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emp = db.get(Employee, world.emp["a1"])
    db.add(LeavePolicyAssignment(employee_id=emp.id, company_id=emp.company_id, policy_id=policy.id,
                                 effective_from=date(2026, 7, 1)))
    db.flush()
    assert balance_service.ensure_balance(db, emp, 2026, lt).allocated_days == 13.5
    assert balance_service.ensure_balance(db, emp, 2027, lt).allocated_days == 15.0
    assert balance_service.ensure_balance(db, emp, 2025, lt).allocated_days == 12.0   # trước phân bổ


# ── 3. API chính sách + dòng ─────────────────────────────────────────────────────

def test_chinh_sach_crud_va_dong(db, world, hr, http):
    lt = make_type(db)
    kl = make_type(db, "unpaid", counts_balance=False)
    bu = make_type(db, "comp", is_compensatory=True)
    r = http(hr.user, "POST", "/api/leave-policies", json={"code": "HC", "name": "Hành chính"})
    assert r.status_code in (200, 201), r.text
    pid = r.json()["data"]["id"]
    #  Mã không đổi sau khi tạo: PATCH có `code` bị bỏ qua.
    r = http(hr.user, "PATCH", f"/api/leave-policies/{pid}", json={"code": "KHAC", "name": "Hành chính 2"})
    assert r.status_code == 200 and r.json()["data"]["code"] == "HC" and r.json()["data"]["name"] == "Hành chính 2"
    #  Thay dòng.
    r = http(hr.user, "PUT", f"/api/leave-policies/{pid}/lines", json={"items": [
        {"leave_type_id": lt.id, "annual_days": 15}]})
    assert r.status_code == 200 and r.json()["data"]["items"][0]["annual_days"] == 15
    assert http(hr.user, "GET", f"/api/leave-policies/{pid}/lines").json()["data"]["total"] == 1
    #  Loại không trừ quỹ / nghỉ bù / trùng / bước 0.5 / quá trần → 422.
    for items in ([{"leave_type_id": kl.id, "annual_days": 1}], [{"leave_type_id": bu.id, "annual_days": 1}],
                  [{"leave_type_id": lt.id, "annual_days": 1}, {"leave_type_id": lt.id, "annual_days": 2}],
                  [{"leave_type_id": lt.id, "annual_days": 1.3}], [{"leave_type_id": lt.id, "annual_days": 367}],
                  [{"leave_type_id": 9999, "annual_days": 1}]):
        assert http(hr.user, "PUT", f"/api/leave-policies/{pid}/lines", json={"items": items}).status_code == 422
    assert db.query(LeavePolicyLine).filter_by(policy_id=pid).count() == 1   # lượt lỗi không làm mất dòng cũ
    #  Trùng mã → lỗi; xóa gói sạch được cả dòng.
    assert http(hr.user, "POST", "/api/leave-policies", json={"code": "HC", "name": "Trùng"}).status_code >= 400
    assert http(hr.user, "DELETE", f"/api/leave-policies/{pid}").status_code == 200
    assert db.query(LeavePolicyLine).filter_by(policy_id=pid).count() == 0


def test_xoa_chinh_sach_con_phan_bo_409(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    r = http(hr.user, "POST", "/api/leave-policy-assignments", json=assign_body(world.emp["a1"], policy.id))
    assert r.status_code == 200, r.text
    r = http(hr.user, "DELETE", f"/api/leave-policies/{policy.id}")
    assert r.status_code == 409 and "1 nhân sự" in r.json()["error"]["message"]


# ── 4. Tạo phân bổ: cấp / giữ / tính lại ─────────────────────────────────────────

def test_tao_cap_dong_thieu_theo_chinh_sach(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(world.emp["a1"], policy.id, start="2026-01-01"))
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["balances"]["created"] == 1 and data["assignment"]["state"] == LeavePolicyAssignmentState.ACTIVE
    assert data["assignment"]["employee_code"] == "A1" and data["assignment"]["policy_name"] == "Gói P15"
    row = db.query(LeaveBalance).filter_by(employee_id=world.emp["a1"], year=YEAR).one()
    assert row.allocated_days == 15.0 and row.company_id == db.get(Employee, world.emp["a1"]).company_id


def test_giu_nguyen_khi_tat_tinh_lai_va_chi_doi_allocated_khi_bat(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emp = db.get(Employee, world.emp["a1"])
    row = balance_service.ensure_balance(db, emp, YEAR, lt)
    row.seniority_days, row.carried_days, row.adjusted_days = 1.0, 2.0, -0.5
    row.used_days, row.pending_days, row.comp_days = 3.0, 1.0, 0.5
    db.commit()
    before = {c: getattr(row, c) for c in ("seniority_days", "carried_days", "adjusted_days", "used_days",
                                           "pending_days", "comp_days", "carried_out_days", "carried_expired_days")}

    #  Tắt tính lại → giữ nguyên, đếm kept.
    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(world.emp["a1"], policy.id, start="2026-01-01", recalc_current_year=False))
    assert r.status_code == 200
    assert r.json()["data"]["balances"] == {"created": 0, "recalculated": [], "kept": 1, "negative_after": []}
    db.refresh(row)
    assert row.allocated_days == 12.0

    #  Xóa rồi tạo lại với tính lại BẬT → chỉ allocated_days đổi.
    aid = db.query(LeavePolicyAssignment).one().id
    assert http(hr.user, "DELETE", f"/api/leave-policy-assignments/{aid}").status_code == 200
    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(world.emp["a1"], policy.id, start="2026-07-01"))
    assert r.status_code == 200, r.text
    changed = r.json()["data"]["balances"]["recalculated"]
    assert changed == [{"leave_type_id": lt.id, "before": 12.0, "after": 13.5}]
    db.refresh(row)
    assert row.allocated_days == 13.5
    assert {c: getattr(row, c) for c in before} == before
    log = db.query(AuditLog).filter(AuditLog.entity == "leave_balance", AuditLog.entity_id == row.id).one()
    assert "12 → 13.5" in log.message and "Gói P15" in log.message


def test_loai_khong_co_trong_chinh_sach_theo_luat_loai(db, world, hr, http):
    a, b = make_type(db, "a"), make_type(db, "b", annual_quota_days=5.0)
    policy = make_policy(db, "PA", {a.id: 20.0})
    emp = db.get(Employee, world.emp["a1"])
    db.commit()
    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(emp.id, policy.id, start="2026-01-01"))
    assert r.status_code == 200
    assert balance_service.ensure_balance(db, emp, YEAR, a).allocated_days == 20.0
    assert balance_service.ensure_balance(db, emp, YEAR, b).allocated_days == 5.0
    assert db.query(LeaveBalance).filter_by(leave_type_id=b.id).count() == 1   # `b` không bị cấp lúc phân bổ


def test_phan_bo_nam_sau_va_nam_da_qua_khong_dung_quy_nam_nay(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emp = db.get(Employee, world.emp["a1"])
    row25 = balance_service.ensure_balance(db, emp, 2025, lt)
    row26 = balance_service.ensure_balance(db, emp, 2026, lt)
    db.commit()
    #  Bắt đầu năm sau: không đụng, không cấp thêm dòng năm nay.
    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(emp.id, policy.id, start="2027-01-01"))
    assert r.status_code == 200 and r.json()["data"]["balances"]["recalculated"] == []
    db.refresh(row26)
    assert row26.allocated_days == 12.0
    assert balance_service.ensure_balance(db, emp, 2027, lt).allocated_days == 15.0
    #  Phân bổ phủ cả 2025 và 2026: dòng 2025 (năm đã qua) không bao giờ đổi.
    other = make_policy(db, "P20", {lt.id: 20.0})
    db.query(LeavePolicyAssignment).delete()
    db.commit()
    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(emp.id, other.id, start="2025-01-01"))
    assert r.status_code == 200
    db.refresh(row25)
    db.refresh(row26)
    assert (row25.allocated_days, row26.allocated_days) == (12.0, 20.0)


# ── 5. Chốt chặn ─────────────────────────────────────────────────────────────────

def test_chong_ngay_409_va_ket_thuc_chinh_sach_cu(db, world, hr, http):
    lt, lt2 = make_type(db), make_type(db, "sick", annual_quota_days=6.0)
    old = make_policy(db, "OLD", {lt.id: 15.0, lt2.id: 10.0})
    new = make_policy(db, "NEW", {lt.id: 18.0})
    emp = db.get(Employee, world.emp["a1"])
    db.commit()
    assert http(hr.user, "POST", "/api/leave-policy-assignments",
                json=assign_body(emp.id, old.id, start="2026-01-01")).status_code == 200
    assert balance_service.get_balance(db, emp.id, YEAR, lt2.id).allocated_days == 10.0

    r = http(hr.user, "POST", "/api/leave-policy-assignments", json=assign_body(emp.id, new.id, start="2026-07-01"))
    assert r.status_code == 409
    assert "Gói OLD" in r.json()["error"]["message"] and "01/01/2026" in r.json()["error"]["message"] \
        and "không thời hạn" in r.json()["error"]["message"]

    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(emp.id, new.id, start="2026-07-01", close_previous=True))
    assert r.status_code == 200, r.text
    old_row = db.query(LeavePolicyAssignment).filter_by(policy_id=old.id).one()
    assert old_row.effective_to == date(2026, 6, 30)
    #  Cả loại của gói mới (15→18 nửa năm = 16.5) lẫn loại của gói cũ (10 → 5.0... về luật loại 6 khi hết gói).
    assert balance_service.get_balance(db, emp.id, YEAR, lt.id).allocated_days == 16.5
    assert balance_service.get_balance(db, emp.id, YEAR, lt2.id).allocated_days == 8.0   # (6×10 + 6×6)/12


def test_close_previous_khong_dong_khi_nhieu_luot_chong(db, world, hr, http):
    lt = make_type(db)
    p1, p2, p3 = (make_policy(db, c, {lt.id: d}) for c, d in (("P1", 13.0), ("P2", 14.0), ("P3", 15.0)))
    emp = db.get(Employee, world.emp["a1"])
    db.commit()
    for policy, start, end in ((p1, "2026-01-01", "2026-06-30"), (p2, "2026-07-01", None)):
        assert http(hr.user, "POST", "/api/leave-policy-assignments",
                    json=assign_body(emp.id, policy.id, start=start, end=end)).status_code == 200
    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(emp.id, p3.id, start="2026-05-01", close_previous=True))
    assert r.status_code == 409
    #  Trùng đúng ngày bắt đầu cũng là chồng ngày (UNIQUE không phải đường duy nhất).
    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(emp.id, p3.id, start="2026-07-01", close_previous=True))
    assert r.status_code == 409


def test_tu_phan_bo_403_admin_qua(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    r = http(hr.user, "POST", "/api/leave-policy-assignments", json=assign_body(world.emp["a2"], policy.id))
    assert r.status_code == 403
    world.grant("a2", "leave_balance", scope="all", actions=("write",), role_code="admin")
    r = http(hr.user, "POST", "/api/leave-policy-assignments", json=assign_body(world.emp["a2"], policy.id))
    assert r.status_code == 200, r.text


def test_ngoai_pham_vi_404_va_nhan_su_la_404(db, world, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    actor = world.grant("a3", "leave_balance", scope="all", actions=("read", "write"))
    world.grant("a3", "employee", scope="dept", actions=("read", "write"))
    db.commit()
    #  a3 ở Phòng Thu mua: nhân sự phòng Kế toán nằm ngoài phạm vi `employee`.
    r = http(actor.user, "POST", "/api/leave-policy-assignments", json=assign_body(world.emp["a1"], policy.id))
    assert r.status_code == 404
    assert http(actor.user, "POST", "/api/leave-policy-assignments", json=assign_body(99999, policy.id)).status_code == 404
    assert http(actor.user, "POST", "/api/leave-policy-assignments", json=assign_body(world.emp["a1"], 99999)).status_code in (404,)


def test_chinh_sach_ngung_dung_422_nhung_phan_bo_cu_van_ap(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emp = db.get(Employee, world.emp["a1"])
    db.commit()
    assert http(hr.user, "POST", "/api/leave-policy-assignments",
                json=assign_body(emp.id, policy.id, start="2026-01-01")).status_code == 200
    policy.is_active = False
    db.commit()
    r = http(hr.user, "POST", "/api/leave-policy-assignments", json=assign_body(world.emp["a3"], policy.id))
    assert r.status_code == 422
    assert balance_service.ensure_balance(db, emp, 2027, lt).allocated_days == 15.0   # phân bổ cũ vẫn áp


# ── 6. Sửa / xóa phân bổ ─────────────────────────────────────────────────────────

def test_sua_ket_thuc_tinh_lai_va_chi_sua_ghi_chu_khong_dung_quy(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emp = db.get(Employee, world.emp["a1"])
    other = make_policy(db, "P20", {lt.id: 20.0})
    db.commit()
    aid = http(hr.user, "POST", "/api/leave-policy-assignments",
               json=assign_body(emp.id, policy.id, start="2026-01-01")).json()["data"]["assignment"]["id"]
    row = balance_service.get_balance(db, emp.id, YEAR, lt.id)
    assert row.allocated_days == 15.0
    #  Chỉ ghi chú → không tính lại gì.
    r = http(hr.user, "PATCH", f"/api/leave-policy-assignments/{aid}", json={"note": "ghi chú"})
    assert r.status_code == 200 and r.json()["data"]["balances"]["recalculated"] == []
    #  Rút ngắn: kết thúc 30/06 → (6×15 + 6×12)/12 = 13.5.
    r = http(hr.user, "PATCH", f"/api/leave-policy-assignments/{aid}", json={"effective_to": "2026-06-30"})
    assert r.status_code == 200, r.text
    db.refresh(row)
    assert row.allocated_days == 13.5
    #  Trước ngày bắt đầu → 422; chồng với lượt khác → 409.
    assert http(hr.user, "PATCH", f"/api/leave-policy-assignments/{aid}",
                json={"effective_to": "2025-12-31"}).status_code == 422
    assert http(hr.user, "POST", "/api/leave-policy-assignments",
                json=assign_body(emp.id, other.id, start="2026-09-01")).status_code == 200
    assert http(hr.user, "PATCH", f"/api/leave-policy-assignments/{aid}",
                json={"effective_to": "2026-10-01"}).status_code == 409
    #  Đưa về không thời hạn bằng null khi không còn chồng: xóa lượt kia trước.
    other_id = db.query(LeavePolicyAssignment).filter_by(policy_id=other.id).one().id
    assert http(hr.user, "DELETE", f"/api/leave-policy-assignments/{other_id}").status_code == 200
    r = http(hr.user, "PATCH", f"/api/leave-policy-assignments/{aid}", json={"effective_to": None})
    assert r.status_code == 200 and r.json()["data"]["assignment"]["effective_to"] is None
    db.refresh(row)
    assert row.allocated_days == 15.0


def test_xoa_phan_bo_kem_tinh_lai_ve_luat_loai(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emp = db.get(Employee, world.emp["a1"])
    db.commit()
    aid = http(hr.user, "POST", "/api/leave-policy-assignments",
               json=assign_body(emp.id, policy.id, start="2026-01-01")).json()["data"]["assignment"]["id"]
    row = balance_service.get_balance(db, emp.id, YEAR, lt.id)
    assert row.allocated_days == 15.0
    r = http(hr.user, "DELETE", f"/api/leave-policy-assignments/{aid}", params={"recalc_current_year": "true"})
    assert r.status_code == 200
    assert r.json()["data"]["balances"]["recalculated"] == [{"leave_type_id": lt.id, "before": 15.0, "after": 12.0}]
    db.refresh(row)
    assert row.allocated_days == 12.0
    assert http(hr.user, "GET", f"/api/leave-policy-assignments/{aid}").status_code == 404


def test_tinh_lai_bao_quy_am(db, world, hr, http):
    lt = make_type(db, annual_quota_days=15.0)
    policy = make_policy(db, "P5", {lt.id: 5.0})
    emp = db.get(Employee, world.emp["a1"])
    row = balance_service.ensure_balance(db, emp, YEAR, lt)
    row.used_days = 10.0
    db.commit()
    r = http(hr.user, "POST", "/api/leave-policy-assignments",
             json=assign_body(emp.id, policy.id, start="2026-01-01"))
    neg = r.json()["data"]["balances"]["negative_after"]
    assert neg and neg[0]["leave_type_id"] == lt.id and neg[0]["available_days"] == -5.0


# ── 7. Schema ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("make", [
    lambda: PolicyCreate(code="x" * 31, name="a"),
    lambda: PolicyCreate(code="x", name="a" * 151),
    lambda: PolicyCreate(code="x", name="a", note="n" * 501),
    lambda: PolicyCreate(code="", name="a"),
    lambda: PolicyUpdate(name="a" * 151),
    lambda: PolicyUpdate(note="n" * 501),
    lambda: PolicyLineItem(leave_type_id=1, annual_days=0.3),
    lambda: PolicyLineItem(leave_type_id=1, annual_days=-1),
    lambda: AssignmentCreate(employee_id=1, policy_id=1, effective_from=date(2026, 1, 1), note="n" * 501),
    lambda: AssignmentCreate(employee_id=1, policy_id=1, effective_from=date(1999, 12, 31)),
    lambda: AssignmentCreate(employee_id=1, policy_id=1, effective_from=date(2101, 1, 1)),
    lambda: AssignmentCreate(employee_id=1, policy_id=1, effective_from=date(2026, 5, 1), effective_to=date(2026, 4, 30)),
    lambda: AssignmentUpdate(note="n" * 501),
    lambda: AssignmentUpdate(effective_to=date(2101, 1, 1)),
    lambda: AssignmentBulk(policy_id=1, effective_from=date(2026, 1, 1), employee_ids=list(range(1, 502))),
    lambda: AssignmentBulk(policy_id=1, effective_from=date(2026, 1, 1), employee_ids=[]),
])
def test_schema_chan_dau_vao(make):
    with pytest.raises(ValidationError):
        make()


def test_schema_chap_nhan_bien_hop_le():
    AssignmentCreate(employee_id=1, policy_id=1, effective_from=date(2026, 1, 1), effective_to=date(2026, 1, 1),
                     note="n" * 500)
    PolicyCreate(code="x" * 30, name="a" * 150, note="n" * 500)
    assert AssignmentCreate(employee_id=1, policy_id=1, effective_from=date(2026, 1, 1)).recalc_current_year is True
