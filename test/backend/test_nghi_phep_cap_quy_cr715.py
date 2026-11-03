"""duoc-CR-715 giai đoạn A — luật loại nghỉ kiểu ERPNext: tỷ lệ tháng, cộng dần, hạn mức theo nhóm,
«dùng được sau N ngày», ứng phép. Mặc định của ba cột mới phải giữ NGUYÊN hành vi cũ.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.employee.constants import (EMPLOYMENT_PART_TIME, JOB_LEVEL_MANAGER,
                                            JOB_LEVEL_STAFF)
from app.modules.employee.model import Employee
from app.modules.leave import accrual_service, balance_service, request_service
from app.modules.leave.catalog_controller import _block_delete_used_type, replace_quotas
from app.modules.leave.catalog_model import LeaveType, LeaveTypeQuota
from app.modules.leave.constants import (QUOTA_BASIS_EMPLOYMENT_TYPE, QUOTA_BASIS_JOB_LEVEL,
                                         LeaveAccrualMode)
from app.modules.leave.schema import (LeaveLineItem, LeaveRequestCreate, LeaveTypeCreate,
                                      QuotaRuleItem, QuotaRuleReplace)

MONDAY = date(2026, 1, 5)


def _type(db, code="annual", **kw):
    kw.setdefault("name", "Phép năm")
    kw.setdefault("counts_balance", True)
    kw.setdefault("annual_quota_days", 12.0)
    obj = LeaveType(code=code, **kw)
    db.add(obj)
    db.flush()
    return obj


def _emp(db, code="NV001", **kw):
    kw.setdefault("company_id", 1)
    kw.setdefault("department_id", 7)
    obj = Employee(code=code, full_name="Nguyễn Văn A", **kw)
    db.add(obj)
    db.flush()
    return obj


def _alloc(db, emp, lt, year=2026):
    return balance_service.ensure_balance(db, emp, year, lt)


# ── 1. Mặc định = hành vi cũ ────────────────────────────────────────────────────

def test_mac_dinh_ba_cot_moi_giu_hanh_vi_cu(db):
    lt = _type(db)
    assert (int(lt.accrual_mode), lt.applicable_after_days, lt.max_negative_days) == (1, 0, 0.0)
    #  Người vào làm giữa năm vẫn được ĐỦ quota khi chế độ FULL_YEAR.
    row = _alloc(db, _emp(db, hire_date=date(2026, 11, 20)), lt)
    assert row.allocated_days == 12.0
    assert balance_service.remaining(db, row.employee_id, 2026, lt.id) == 12.0


def test_schema_mac_dinh_va_bien(db):
    base = dict(code="x", name="X")
    got = LeaveTypeCreate(**base)
    assert (got.accrual_mode, got.applicable_after_days, got.max_negative_days) == (1, 0, 0.0)
    for bad in ({"accrual_mode": 0}, {"accrual_mode": 4}, {"applicable_after_days": 3651},
                {"applicable_after_days": -1}, {"max_negative_days": 30.5}, {"max_negative_days": -1}):
        with pytest.raises(ValidationError):
            LeaveTypeCreate(**base, **bad)


# ── 2. Tỷ lệ theo tháng làm việc ────────────────────────────────────────────────

@pytest.mark.parametrize("hire,expected", [
    (date(2026, 3, 10), 10.0),    # ngày 10 → tính cả tháng 3: 10 tháng
    (date(2026, 3, 15), 10.0),    # biên: ngày 15 vẫn tính cả tháng
    (date(2026, 3, 16), 9.0),     # biên: ngày 16 → từ tháng 4: 9 tháng
    (date(2026, 3, 20), 9.0),
    (date(2026, 1, 1), 12.0),
    (date(2025, 6, 1), 12.0),     # vào trước năm → đủ
    (date(2026, 12, 20), 0.0),    # vào cuối tháng 12 → chưa có tháng nào
    (None, 12.0),                 # chưa khai ngày vào làm → đủ
])
def test_prorata_hire(db, hire, expected):
    lt = _type(db, accrual_mode=int(LeaveAccrualMode.PRORATA_HIRE))
    assert _alloc(db, _emp(db, hire_date=hire), lt).allocated_days == expected


def test_lam_tron_nua_len_toi_nua_ngay(db):
    #  14 ngày × 7 tháng / 12 = 8.1667 → 8.0; 15 × 7 / 12 = 8.75 → 9.0 (nửa lên); 13 × 7 / 12 = 7.58 → 7.5
    assert accrual_service.round_half_up(8.75) == 9.0
    assert accrual_service.round_half_up(8.1667) == 8.0
    assert accrual_service.round_half_up(7.5833) == 7.5
    assert accrual_service.round_down_half(7.99) == 7.5


def test_tham_nien_khong_bi_ty_le(db):
    from app.modules.leave.catalog_model import LeaveTypeSeniority
    lt = _type(db, accrual_mode=int(LeaveAccrualMode.PRORATA_HIRE))
    db.add(LeaveTypeSeniority(leave_type_id=lt.id, years_from=0, years_to=0, extra_days=2.0))
    db.flush()
    row = _alloc(db, _emp(db, hire_date=date(2026, 3, 10)), lt)
    assert (row.allocated_days, row.seniority_days) == (10.0, 2.0)


# ── 3. Cộng dần theo tháng ──────────────────────────────────────────────────────

def test_cong_dan_thang_nam_la_nam_phan_muoi_hai(db, monkeypatch):
    lt = _type(db, accrual_mode=int(LeaveAccrualMode.MONTHLY))
    emp = _emp(db, hire_date=date(2020, 2, 1))
    row = _alloc(db, emp, lt)
    assert row.allocated_days == 12.0                 # lưu CẢ NĂM
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 5, 10))
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 5.0
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 12, 31))
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 12.0
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2027, 1, 2))   # năm đã qua → đủ
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 12.0


def test_cong_dan_lam_tron_xuong_nua_ngay(db, monkeypatch):
    lt = _type(db, accrual_mode=int(LeaveAccrualMode.MONTHLY), annual_quota_days=14.0)
    emp = _emp(db, hire_date=date(2020, 2, 1))
    _alloc(db, emp, lt)
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 3, 1))   # 14×3/12 = 3.5
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 3.5
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 4, 1))   # 14×4/12 = 4.67 → 4.5
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 4.5


def test_cong_dan_nguoi_vao_lam_trong_nam_ky_tinh_tu_thang_vao(db, monkeypatch):
    lt = _type(db, accrual_mode=int(LeaveAccrualMode.MONTHLY))
    emp = _emp(db, hire_date=date(2026, 3, 10))      # kỳ 10 tháng, allocated 10
    row = _alloc(db, emp, lt)
    assert row.allocated_days == 10.0
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 5, 20))  # tháng 3,4,5 = 3/10
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 3.0


def test_cong_dan_thuc_hien_o_check_enough_va_giu_nguyen_dieu_chinh(db, monkeypatch):
    lt = _type(db, accrual_mode=int(LeaveAccrualMode.MONTHLY))
    emp = _emp(db, hire_date=date(2020, 2, 1))
    row = _alloc(db, emp, lt)
    row.adjusted_days = 3.0        # điều chỉnh tay KHÔNG bị cộng dần
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 5, 10))
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 8.0   # 5 + 3
    balance_service.check_enough(db, emp, 2026, lt, 8.0)
    with pytest.raises(HTTPException):
        balance_service.check_enough(db, emp, 2026, lt, 8.5)


# ── 4. Hạn mức theo nhóm ────────────────────────────────────────────────────────

def test_quota_hinh_thuc_thang_cap_bac_thang_mac_dinh(db):
    lt = _type(db)
    db.add_all([
        LeaveTypeQuota(leave_type_id=lt.id, basis=QUOTA_BASIS_EMPLOYMENT_TYPE,
                       basis_value=EMPLOYMENT_PART_TIME, quota_days=6.0),
        LeaveTypeQuota(leave_type_id=lt.id, basis=QUOTA_BASIS_JOB_LEVEL,
                       basis_value=JOB_LEVEL_MANAGER, quota_days=15.0),
    ])
    db.flush()
    both = _emp(db, "A1", employment_type=EMPLOYMENT_PART_TIME, job_level=JOB_LEVEL_MANAGER)
    level_only = _emp(db, "A2", employment_type=1, job_level=JOB_LEVEL_MANAGER)
    neither = _emp(db, "A3", employment_type=1, job_level=JOB_LEVEL_STAFF)
    unknown = _emp(db, "A4")
    assert _alloc(db, both, lt).allocated_days == 6.0
    assert _alloc(db, level_only, lt).allocated_days == 15.0
    assert _alloc(db, neither, lt).allocated_days == 12.0
    assert _alloc(db, unknown, lt).allocated_days == 12.0


def test_quota_nhom_roi_tiep_toi_ty_le_thang(db):
    lt = _type(db, accrual_mode=int(LeaveAccrualMode.PRORATA_HIRE))
    db.add(LeaveTypeQuota(leave_type_id=lt.id, basis=QUOTA_BASIS_JOB_LEVEL,
                          basis_value=JOB_LEVEL_MANAGER, quota_days=24.0))
    db.flush()
    emp = _emp(db, job_level=JOB_LEVEL_MANAGER, hire_date=date(2026, 7, 1))   # 6 tháng
    assert _alloc(db, emp, lt).allocated_days == 12.0


def test_api_quota_thay_ca_danh_sach_chan_trung_va_tran(db):
    lt = _type(db)
    user = SimpleNamespace(id=1)
    items = [QuotaRuleItem(basis=1, basis_value=2, quota_days=6),
             QuotaRuleItem(basis=2, basis_value=4, quota_days=15)]
    replace_quotas(lt.id, QuotaRuleReplace(items=items), db, user)
    assert db.query(LeaveTypeQuota).filter_by(leave_type_id=lt.id).count() == 2
    #  Thay lại bằng 1 dòng → còn đúng 1.
    replace_quotas(lt.id, QuotaRuleReplace(items=items[:1]), db, user)
    assert db.query(LeaveTypeQuota).filter_by(leave_type_id=lt.id).count() == 1
    #  Trùng nhóm → 422, danh sách cũ giữ nguyên.
    with pytest.raises(HTTPException) as exc:
        replace_quotas(lt.id, QuotaRuleReplace(items=[items[0], items[0]]), db, user)
    assert exc.value.status_code == 422
    assert db.query(LeaveTypeQuota).filter_by(leave_type_id=lt.id).count() == 1
    with pytest.raises(HTTPException) as exc:
        replace_quotas(9999, QuotaRuleReplace(items=[]), db, user)
    assert exc.value.status_code == 404
    #  Trần 50 dòng + cơ sở lạ.
    with pytest.raises(ValidationError):
        QuotaRuleReplace(items=[QuotaRuleItem(basis=1, basis_value=1, quota_days=1)] * 51)
    with pytest.raises(ValidationError):
        QuotaRuleItem(basis=3, basis_value=1, quota_days=1)


def test_xoa_loai_nghi_don_dep_quota(db):
    lt = _type(db)
    db.add(LeaveTypeQuota(leave_type_id=lt.id, basis=1, basis_value=2, quota_days=6.0))
    db.flush()
    _block_delete_used_type(db, lt)
    assert db.query(LeaveTypeQuota).filter_by(leave_type_id=lt.id).count() == 0


# ── 5. «Dùng được sau N ngày» ───────────────────────────────────────────────────

def test_ap_dung_sau_n_ngay_dung_bien(db):
    lt = _type(db, name="Phép năm", applicable_after_days=30)
    hire = date(2025, 12, 6)                       # + 30 ngày = 05/01/2026
    accrual_service.ensure_applicable(lt, hire, date(2026, 1, 5))        # đúng ngày mở → qua
    with pytest.raises(HTTPException) as exc:
        accrual_service.ensure_applicable(lt, hire, date(2026, 1, 4))    # trước 1 ngày → chặn
    assert exc.value.status_code == 422
    assert "sau 30 ngày vào làm (từ 05/01/2026)" in exc.value.detail
    accrual_service.ensure_applicable(lt, None, date(2020, 1, 1))        # không có hire_date → không chặn
    accrual_service.ensure_applicable(_type(db, "other"), hire, date(2020, 1, 1))   # N = 0 → không chặn


def _payload(lt, **kw):
    return LeaveRequestCreate(lines=[LeaveLineItem(leave_type_id=lt.id, days=1)],
                              from_date=MONDAY, to_date=MONDAY, reason="Việc riêng", **kw)


def test_lap_don_va_gui_duyet_chan_theo_n_ngay(db):
    lt = _type(db, applicable_after_days=60)
    emp = _emp(db, hire_date=date(2025, 12, 20))   # mở từ 18/02/2026
    user = SimpleNamespace(id=1, employee_id=emp.id)
    with pytest.raises(HTTPException) as exc:
        request_service.create(db, _payload(lt), user)
    assert exc.value.status_code == 422
    #  Dời ngày hợp lệ → lập được; rồi đổi ngày sửa về trước mốc → update chặn.
    ok = LeaveRequestCreate(lines=[LeaveLineItem(leave_type_id=lt.id, days=1)],
                            from_date=date(2026, 2, 23), to_date=date(2026, 2, 23), reason="ok")
    obj = request_service.create(db, ok, user)
    from app.modules.leave.schema import LeaveRequestUpdate
    with pytest.raises(HTTPException):
        request_service.update(db, obj, LeaveRequestUpdate(from_date=MONDAY, to_date=MONDAY), user)
    #  Đổi ngày hợp lệ khác (vẫn sau mốc) thì qua; gửi duyệt cũng kiểm lại (mốc dời sau khi lưu nháp).
    lt.applicable_after_days = 400
    with pytest.raises(HTTPException):
        request_service.prepare_submit(db, obj, user)


def test_sua_ly_do_khong_kiem_lai_n_ngay(db):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2025, 12, 20))
    user = SimpleNamespace(id=1, employee_id=emp.id)
    obj = request_service.create(db, _payload(lt), user)
    lt.applicable_after_days = 400                  # luật siết SAU khi đơn đã lập
    from app.modules.leave.schema import LeaveRequestUpdate
    request_service.update(db, obj, LeaveRequestUpdate(reason="Đổi lý do"), user)   # không chặn


# ── 6. Ứng phép ────────────────────────────────────────────────────────────────

def test_ung_phep_xuong_toi_tru_n_khong_hon(db):
    lt = _type(db, annual_quota_days=2.0, max_negative_days=3.0)
    emp = _emp(db)
    balance_service.check_enough(db, emp, 2026, lt, 5.0)     # còn 2 → xuống -3: đúng sàn
    with pytest.raises(HTTPException) as exc:
        balance_service.check_enough(db, emp, 2026, lt, 5.5)
    assert exc.value.status_code == 400
    #  Đang giữ chỗ vẫn tính: đã giữ 4 → còn -2, xin thêm 1 được, thêm 1.5 không.
    balance_service.reserve(db, emp, 2026, lt, 4.0)
    balance_service.check_enough(db, emp, 2026, lt, 1.0)
    with pytest.raises(HTTPException):
        balance_service.check_enough(db, emp, 2026, lt, 1.5)


def test_mac_dinh_khong_ung_phep(db):
    lt = _type(db, annual_quota_days=2.0)
    emp = _emp(db)
    balance_service.check_enough(db, emp, 2026, lt, 2.0)
    with pytest.raises(HTTPException):
        balance_service.check_enough(db, emp, 2026, lt, 2.5)


def test_loai_khong_tinh_quy_khong_bi_anh_huong(db):
    lt = _type(db, code="unpaid", counts_balance=False, annual_quota_days=0.0)
    balance_service.check_enough(db, _emp(db), 2026, lt, 99.0)


def test_hire_date_in_a_later_year_gets_no_prorated_quota_for_this_year():
    """Rà của lead: hồ sơ tạo trước ngày vào làm (vào 05/01/2027) không được cấp đủ quỹ năm 2026."""
    from datetime import date as _date

    from app.modules.leave import accrual_service
    from app.modules.leave.constants import LeaveAccrualMode

    hire = _date(2027, 1, 5)
    assert accrual_service.months_in_period(hire, 2026) == 0
    assert accrual_service.prorate_allocation(12, LeaveAccrualMode.PRORATA_HIRE, hire, 2026) == 0
    assert accrual_service.prorate_allocation(12, LeaveAccrualMode.MONTHLY, hire, 2026) == 0
    #  Chế độ «đủ đầu năm» giữ đúng hành vi cũ (không xét ngày vào làm).
    assert accrual_service.prorate_allocation(12, LeaveAccrualMode.FULL_YEAR, hire, 2026) == 12
    #  Năm vào làm thì tính bình thường (05/01 → đủ 12 tháng).
    assert accrual_service.prorate_allocation(12, LeaveAccrualMode.PRORATA_HIRE, hire, 2027) == 12
