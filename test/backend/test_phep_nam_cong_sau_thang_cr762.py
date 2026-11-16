"""duoc-CR-762 — Phép năm: làm đủ một tháng được một ngày (chế độ MONTHLY_AFTER).

Chốt của người chủ 16/11/2026: Q1 cộng khi làm XONG tháng · Q2 mốc ngày 15 · Q4 thử việc không tích, mốc là HĐLĐ đầu
tiên đã ký không phải Thử việc · Q5 chưa có HĐ thì lấy ngày vào làm (trừ hồ sơ Thử việc) · Q6 hiệu lực ngay, âm thì chặn.
Các chế độ cũ (FULL_YEAR / PRORATA_HIRE / MONTHLY) phải ra đúng từng con số cũ.
"""
from datetime import date

import pytest
from fastapi import HTTPException

from app.core.labor_contract_codes import LaborContractStatus as CS, LaborContractType as CT
from app.core.report_period import parse_period
from app.modules.employee.constants import EMPLOYMENT_FULL_TIME, EMPLOYMENT_PROBATION
from app.modules.employee.model import Employee
from app.modules.labor_contract.model import LaborContract
from app.modules.leave import (accrual_service, accrual_start_service, balance_report_service,
                               balance_report_spec, balance_service)
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LeaveAccrualMode, label, LEAVE_ACCRUAL_MODE_LABELS

AFTER = int(LeaveAccrualMode.MONTHLY_AFTER)
YEAR = 2026


def _type(db, mode=AFTER, **kw):
    kw.setdefault("name", "Phép năm")
    kw.setdefault("counts_balance", True)
    kw.setdefault("annual_quota_days", 12.0)
    obj = LeaveType(code=kw.pop("code", "annual"), accrual_mode=mode, **kw)
    db.add(obj)
    db.flush()
    return obj


def _emp(db, code="NV001", **kw):
    kw.setdefault("company_id", 1)
    kw.setdefault("department_id", 7)
    kw.setdefault("employment_type", EMPLOYMENT_FULL_TIME)
    obj = Employee(code=code, full_name=f"Nhân sự {code}", **kw)
    db.add(obj)
    db.flush()
    return obj


def _contract(db, emp, start, ctype=CT.INDEFINITE, status=CS.SIGNED, deleted=False, end=None, n=[0]):
    n[0] += 1
    row = LaborContract(code=f"HDLD{n[0]:04d}", employee_id=emp.id, contract_type=int(ctype), status=int(status),
                        start_date=start, end_date=end, is_deleted=deleted, company_id=emp.company_id or 0)
    db.add(row)
    db.flush()
    return row


def _avail(db, row, today):
    return balance_service.available_days(db, row, today)


def _row(db, emp, lt, year=YEAR):
    return balance_service.ensure_balance(db, emp, year, lt)


# ── 1. Nhãn + mã ───────────────────────────────────────────────────────────────────────────────────────

def test_ma_va_nhan_che_do_moi():
    assert AFTER == 4
    assert LEAVE_ACCRUAL_MODE_LABELS[LeaveAccrualMode.MONTHLY_AFTER] == "Cộng dần sau mỗi tháng làm đủ"
    assert label(LEAVE_ACCRUAL_MODE_LABELS, AFTER) == "Cộng dần sau mỗi tháng làm đủ"
    #  Ba mã cũ không đổi số.
    assert [int(m) for m in (LeaveAccrualMode.FULL_YEAR, LeaveAccrualMode.PRORATA_HIRE, LeaveAccrualMode.MONTHLY)] == [1, 2, 3]


# ── 2. Q1: cộng khi làm XONG tháng (người làm đủ năm) ─────────────────────────────────────────────────

@pytest.mark.parametrize("today,expected", [
    (date(2026, 1, 1), 0.0), (date(2026, 1, 15), 0.0), (date(2026, 1, 31), 0.0),
    (date(2026, 2, 1), 1.0),     # hết tháng 1 -> từ 01/02 có 1 ngày
    (date(2026, 3, 1), 2.0), (date(2026, 6, 30), 5.0),
    (date(2026, 11, 16), 10.0),  # tháng 11 chưa xong
    (date(2026, 12, 31), 11.0),  # tháng 12 chưa xong
])
def test_q1_toi_hom_nay_co_bao_nhieu_ngay(db, today, expected):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2024, 5, 1))
    _contract(db, emp, date(2024, 5, 1))
    row = _row(db, emp, lt)
    assert row.allocated_days == 12.0
    assert _avail(db, row, today) == expected


def test_q1_nam_da_qua_du_va_nam_sau_chua_co(db):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2020, 1, 1))
    old, nxt = _row(db, emp, lt, 2025), _row(db, emp, lt, 2027)
    assert _avail(db, old, date(2026, 2, 1)) == 12.0
    assert _avail(db, nxt, date(2026, 11, 16)) == 0.0


def test_q1_khoan_khong_bi_cong_dan_van_dung_duoc(db):
    #  Thâm niên / mang sang / điều chỉnh / nghỉ bù không bị giữ lại, chỉ `allocated_days`.
    lt = _type(db)
    emp = _emp(db, hire_date=date(2020, 1, 1))
    row = _row(db, emp, lt)
    row.carried_days, row.adjusted_days, row.seniority_days = 2.0, 1.0, 1.0
    assert _avail(db, row, date(2026, 1, 10)) == 4.0
    assert _avail(db, row, date(2026, 3, 1)) == 6.0


# ── 3. Q2: vào làm giữa tháng, mốc ngày 15 ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("start,today,expected", [
    (date(2026, 3, 10), date(2026, 3, 31), 0.0),
    (date(2026, 3, 10), date(2026, 4, 1), 1.0),     # ngày <= 15 tính cả tháng 3: hết tháng 3 có 1
    (date(2026, 3, 15), date(2026, 4, 1), 1.0),     # biên 15
    (date(2026, 3, 16), date(2026, 4, 1), 0.0),     # từ ngày 16 tính từ tháng sau
    (date(2026, 3, 16), date(2026, 5, 1), 1.0),
    (date(2026, 3, 10), date(2026, 11, 16), 8.0),   # tháng 3..10 xong = 8
])
def test_q2_vao_lam_giua_thang(db, start, today, expected):
    lt = _type(db)
    emp = _emp(db, hire_date=start)
    _contract(db, emp, start)
    row = _row(db, emp, lt)
    #  Hạn mức tỷ lệ theo tháng (10 tháng -> 12 × 10 / 12) và số dùng được tăng 1 ngày/tháng.
    assert _avail(db, row, today) == expected


def test_q2_hang_muc_theo_thang_lam_tu_ngay_chinh_thuc(db):
    lt = _type(db)
    a, b = _emp(db, "A", hire_date=date(2026, 3, 10)), _emp(db, "B", hire_date=date(2026, 3, 16))
    _contract(db, a, date(2026, 3, 10))
    _contract(db, b, date(2026, 3, 16))
    assert _row(db, a, lt).allocated_days == 10.0     # tháng 3..12
    assert _row(db, b, lt).allocated_days == 9.0      # tháng 4..12


# ── 4. Q4: thử việc ────────────────────────────────────────────────────────────────────────────────────

def test_q4_hd_thu_viec_roi_hd_chinh_thuc_tu_thang_6(db):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2026, 4, 1))
    _contract(db, emp, date(2026, 4, 1), CT.PROBATION)
    _contract(db, emp, date(2026, 6, 1), CT.FIXED_TERM)
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing, start.missing_contract) == (date(2026, 6, 1), True, False)
    row = _row(db, emp, lt)
    assert row.allocated_days == 7.0                       # tháng 6..12
    assert _avail(db, row, date(2026, 6, 30)) == 0.0
    assert _avail(db, row, date(2026, 7, 1)) == 1.0        # xong tháng 6, không tính thời gian thử việc
    assert _avail(db, row, date(2026, 11, 16)) == 5.0


def test_q4_hd_chinh_thuc_dau_tien_la_cai_som_nhat_da_ky(db):
    emp = _emp(db, hire_date=date(2020, 1, 1))
    _contract(db, emp, date(2020, 1, 1), CT.PROBATION, end=date(2020, 3, 1))
    _contract(db, emp, date(2022, 9, 1), CT.FIXED_TERM, CS.TERMINATED)    # đã ký rồi chấm dứt: vẫn tính
    _contract(db, emp, date(2023, 9, 1), CT.INDEFINITE)
    _contract(db, emp, date(2021, 1, 1), CT.INDEFINITE, CS.DRAFT)         # nháp: bỏ
    _contract(db, emp, date(2021, 2, 1), CT.INDEFINITE, CS.CANCELLED)     # đã hủy: bỏ
    _contract(db, emp, date(2021, 3, 1), CT.INDEFINITE, deleted=True)     # xóa mềm: bỏ
    assert accrual_start_service.official_start(db, emp).start == date(2022, 9, 1)


def test_q4_hd_thu_viec_het_han_van_ghi_signed_khong_tinh_la_chinh_thuc(db):
    emp = _emp(db, hire_date=date(2026, 1, 5), employment_type=EMPLOYMENT_PROBATION)
    _contract(db, emp, date(2026, 1, 5), CT.PROBATION)
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing) == (None, False)


def test_q4_thu_viec_khong_hd_khong_tich_nua_ngay(db):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2025, 1, 1), employment_type=EMPLOYMENT_PROBATION)
    row = _row(db, emp, lt)
    assert row.allocated_days == 0.0
    assert _avail(db, row, date(2026, 11, 16)) == 0.0
    start = accrual_start_service.official_start(db, emp)
    assert (start.accruing, start.missing_contract) == (False, True)


def test_hd_chinh_thuc_tuong_lai_chua_tich_trang_thai_6(db):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2026, 10, 1))
    _contract(db, emp, date(2026, 10, 1), CT.PROBATION, end=date(2026, 12, 31))
    _contract(db, emp, date(2027, 1, 1))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing) == (date(2027, 1, 1), True)
    assert start.status_at(date(2026, 11, 16)) == 6
    assert start.status_at(date(2027, 1, 1)) == 1                     # tới ngày thì thành Đang tích
    row = _row(db, emp, lt)
    assert row.allocated_days == 0.0 and _avail(db, row, date(2026, 11, 16)) == 0.0
    nxt = _row(db, emp, lt, 2027)
    assert nxt.allocated_days == 12.0 and _avail(db, nxt, date(2026, 11, 16)) == 0.0


def test_not_started_giu_lai_ca_han_muc_neu_quy_da_co_so(db):
    #  Quỹ cũ allocated > 0 của người chưa chính thức: số dùng được vẫn 0 (không lọt ngày đã ghi).
    lt = _type(db)
    emp = _emp(db, hire_date=date(2025, 1, 1), employment_type=EMPLOYMENT_PROBATION)
    row = LeaveBalance(employee_id=emp.id, year=YEAR, leave_type_id=lt.id, allocated_days=12.0)
    db.add(row)
    db.flush()
    assert _avail(db, row, date(2026, 11, 16)) == 0.0


# ── 5. Q5: chưa có HĐ thì lấy ngày vào làm ─────────────────────────────────────────────────────────────

def test_q5_khong_hd_lay_ngay_vao_lam(db):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2026, 5, 10))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing, start.missing_contract) == (date(2026, 5, 10), True, True)
    row = _row(db, emp, lt)
    assert row.allocated_days == 8.0                       # tháng 5..12
    assert _avail(db, row, date(2026, 6, 1)) == 1.0


def test_q5_khong_hd_khong_ngay_vao_lam_tinh_tu_dau_nam_va_co_co(db):
    lt = _type(db)
    emp = _emp(db, hire_date=None)
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing, start.missing_contract) == (None, True, True)
    row = _row(db, emp, lt)
    assert row.allocated_days == 12.0
    assert _avail(db, row, date(2026, 11, 16)) == 10.0


def test_hd_chinh_thuc_thang_hd_khi_co_thu_viec_lech_ngay_vao_lam(db):
    emp = _emp(db, hire_date=date(2019, 1, 1))
    _contract(db, emp, date(2019, 1, 1), CT.PROBATION, end=date(2019, 3, 1))
    _contract(db, emp, date(2021, 7, 1))
    assert accrual_start_service.official_start(db, emp).start == date(2021, 7, 1)


# ── 5b. N3: lịch sử HĐ chưa đủ ───────────────────────────────────────────────────────────────────────

def test_n3_khong_thu_viec_hd_dau_tien_muon_hon_mot_thang_thi_tinh_tu_ngay_vao_lam(db):
    emp = _emp(db, hire_date=date(2019, 1, 15))
    _contract(db, emp, date(2021, 7, 1))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing, start.incomplete, start.missing_contract) == (date(2019, 1, 15), True, True, False)
    assert start.status_at(date(2026, 11, 16)) == 4


@pytest.mark.parametrize("hire,official,incomplete", [
    (date(2026, 1, 15), date(2026, 2, 15), False),    # đúng một tháng: chưa coi là thiếu
    (date(2026, 1, 15), date(2026, 2, 16), True),
    (date(2026, 1, 31), date(2026, 2, 28), False),    # tháng sau ngắn hơn: kẹp về ngày cuối tháng
    (date(2025, 12, 20), date(2026, 1, 20), False),   # qua năm
    (date(2026, 3, 10), date(2026, 3, 10), False),
])
def test_n3_bien_mot_thang(db, hire, official, incomplete):
    emp = _emp(db, hire_date=hire)
    _contract(db, emp, official)
    assert accrual_start_service.official_start(db, emp).incomplete is incomplete


def test_n3_co_hd_thu_viec_thi_khong_coi_la_thieu_lich_su(db):
    emp = _emp(db, hire_date=date(2019, 1, 1))
    _contract(db, emp, date(2019, 1, 1), CT.PROBATION, end=date(2019, 3, 1))
    _contract(db, emp, date(2019, 4, 1))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.incomplete, start.status_at(date(2026, 11, 16))) == (date(2019, 4, 1), False, 1)


# ── 5c. Q3: HĐ dịch vụ / cộng tác viên không phải HĐLĐ chính thức ──────────────────────────────────────

@pytest.mark.parametrize("ctype", [CT.SERVICE, CT.COLLABORATOR])
def test_q3_chi_co_hd_dich_vu_hoac_ctv_thi_khong_tich_trang_thai_5(db, ctype):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2025, 1, 1))
    _contract(db, emp, date(2025, 1, 1), ctype, end=date(2026, 12, 31))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing, start.service_only) == (None, False, True)
    assert start.status_at(date(2026, 11, 16)) == 5
    row = _row(db, emp, lt)
    assert row.allocated_days == 0.0 and _avail(db, row, date(2026, 11, 16)) == 0.0


def test_q3_hd_dich_vu_roi_hd_lao_dong_thi_tich_tu_hd_lao_dong(db):
    emp = _emp(db, hire_date=date(2025, 1, 1))
    _contract(db, emp, date(2025, 1, 1), CT.SERVICE, end=date(2025, 12, 31))
    _contract(db, emp, date(2026, 1, 1), CT.INDEFINITE)
    start = accrual_start_service.official_start(db, emp)
    #  Giai đoạn HĐ dịch vụ không tích phép năm: KHÔNG lùi về ngày vào làm (N3 không áp khi có HĐ dịch vụ / CTV).
    assert (start.start, start.incomplete, start.accruing) == (date(2026, 1, 1), False, True)
    assert start.status_at(date(2026, 11, 16)) == 1


# ── 5d. Nhận lại sau khi nghỉ (rehire) ────────────────────────────────────────────────────────────────

def test_rehire_bo_qua_hd_da_ket_thuc_truoc_ngay_vao_lam_hien_tai(db):
    emp = _emp(db, hire_date=date(2026, 6, 1))
    _contract(db, emp, date(2020, 1, 1), CT.INDEFINITE, CS.TERMINATED, end=date(2024, 12, 31))
    _contract(db, emp, date(2026, 6, 1), CT.FIXED_TERM, end=date(2027, 5, 31))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.incomplete) == (date(2026, 6, 1), False)


def test_rehire_dung_ngay_cham_dut_thuc_te_khi_hd_khong_xac_dinh_thoi_han(db):
    emp = _emp(db, hire_date=date(2026, 6, 1))
    old = _contract(db, emp, date(2020, 1, 1), CT.INDEFINITE, CS.TERMINATED)       # không có end_date
    old.terminated_date = date(2025, 3, 31)
    _contract(db, emp, date(2026, 6, 1), CT.INDEFINITE)
    assert accrual_start_service.official_start(db, emp).start == date(2026, 6, 1)


def test_rehire_chi_co_hd_cu_da_ket_thuc_thi_coi_nhu_chua_co_hd(db):
    emp = _emp(db, hire_date=date(2026, 6, 1))
    _contract(db, emp, date(2020, 1, 1), CT.PROBATION, CS.TERMINATED, end=date(2020, 3, 1))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing, start.missing_contract) == (date(2026, 6, 1), True, True)


def test_rehire_hd_ket_thuc_sat_ngay_vao_lam_van_giu_va_khong_ngay_vao_lam_giu_het(db):
    emp = _emp(db, hire_date=date(2026, 6, 1))
    _contract(db, emp, date(2025, 1, 1), CT.FIXED_TERM, end=date(2026, 5, 31))      # kết thúc hôm trước: vẫn giữ (liền mạch)
    facts = accrual_start_service.contract_facts(db, [emp.id], {emp.id: date(2026, 6, 1)})
    assert facts[emp.id].official_start == date(2025, 1, 1)
    no_hire = accrual_start_service.contract_facts(db, [emp.id], {emp.id: None})
    assert no_hire[emp.id].official_start == date(2025, 1, 1)
    gone = accrual_start_service.contract_facts(db, [emp.id], {emp.id: date(2026, 6, 3)})
    assert emp.id not in gone


def test_loai_khac_van_la_chinh_thuc(db):
    emp = _emp(db, hire_date=date(2026, 2, 1))
    _contract(db, emp, date(2026, 2, 1), CT.OTHER)
    assert accrual_start_service.official_start(db, emp).start == date(2026, 2, 1)


# ── 6. Âm khi đã dùng quá số đã tích: chặn xin thêm ───────────────────────────────────────────────────

def test_q6_dung_qua_so_da_tich_thi_am_va_chan(db, monkeypatch):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2024, 1, 1))
    _contract(db, emp, date(2024, 1, 1))
    row = _row(db, emp, lt)
    row.used_days = 5.0
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 3, 1))     # đã tích 2 ngày
    assert balance_service.available_days(db, row) == -3.0
    with pytest.raises(HTTPException) as err:
        balance_service.check_enough(db, emp, YEAR, lt, 1.0)
    assert err.value.status_code == 400 and "-3" in err.value.detail
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 9, 1))     # tích tới 8 -> còn 3
    assert balance_service.available_days(db, row) == 3.0
    balance_service.check_enough(db, emp, YEAR, lt, 3.0)
    with pytest.raises(HTTPException):
        balance_service.check_enough(db, emp, YEAR, lt, 3.5)


# ── 7. Các chế độ cũ giữ nguyên từng con số ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("hire", [date(2020, 1, 1), date(2026, 3, 10), date(2026, 3, 16), date(2026, 12, 20), None])
@pytest.mark.parametrize("today", [date(2026, 1, 20), date(2026, 5, 10), date(2026, 12, 31), date(2027, 1, 2)])
def test_che_do_cu_khong_doi(hire, today):
    #  Mô phỏng công thức CŨ của MONTHLY (tháng hiện tại tính) so với hàm mới.
    def old(allocated, hire_date, year):
        period = accrual_service.months_in_period(hire_date, year)
        if period <= 0 or year < today.year:
            return 0.0
        reached = 0 if year > today.year else min(period, max(
            0, today.month - accrual_service.first_month_in_year(hire_date, year) + 1))
        return round(max(0.0, allocated - accrual_service.round_down_half(allocated * reached / period)), 2)

    for year in (2025, 2026, 2027):
        for allocated in (12.0, 10.0, 8.5):
            assert accrual_service.accrual_holdback(
                allocated, int(LeaveAccrualMode.MONTHLY), hire, year, today) == old(allocated, hire, year)
            for mode in (LeaveAccrualMode.FULL_YEAR, LeaveAccrualMode.PRORATA_HIRE):
                assert accrual_service.accrual_holdback(allocated, int(mode), hire, year, today) == 0.0


def test_che_do_cu_cap_quy_va_kha_dung_dung_nhu_truoc(db):
    emp = _emp(db, hire_date=date(2026, 3, 10))
    _contract(db, emp, date(2026, 8, 1))          # HĐ chính thức muộn: chế độ cũ KHÔNG nhìn vào
    for code, mode, expected in (("full", LeaveAccrualMode.FULL_YEAR, 12.0), ("pro", LeaveAccrualMode.PRORATA_HIRE, 10.0),
                                 ("mon", LeaveAccrualMode.MONTHLY, 10.0)):
        lt = _type(db, int(mode), code=code)
        assert _row(db, emp, lt).allocated_days == expected
    mon = db.query(LeaveBalance).filter_by(leave_type_id=db.query(LeaveType).filter_by(code="mon").one().id).one()
    assert _avail(db, mon, date(2026, 5, 10)) == 3.0      # tháng 3,4,5 -> 10 × 3/10 = 3 (tháng hiện tại tính)


# ── 8. Báo cáo / ma trận / trợ lý cùng một con số với available_days ─────────────────────────────────

def _after_world(db, world, today_year):
    world.grant("a1", "leave_balance", scope="all", actions=("read",))
    world.grant("a1", "employee", scope="all", actions=("read",))
    db.query(Employee).update({Employee.status: "resigned"})
    lt = _type(db, code="annual")
    rows = []
    #  (mã, ngày vào làm, hợp đồng chính thức, hình thức)
    specs = [("P1", date(2023, 1, 1), date(2023, 1, 1), EMPLOYMENT_FULL_TIME),     # đủ năm
             ("P2", date(2026, 4, 1), date(2026, 6, 1), EMPLOYMENT_FULL_TIME),      # chính thức từ 01/06 (có thử việc)
             ("P3", date(2025, 1, 1), None, EMPLOYMENT_PROBATION),                  # thử việc
             ("P4", date(2026, 5, 10), None, EMPLOYMENT_FULL_TIME)]                 # chưa có HĐ
    for code, hire, official, etype in specs:
        emp = Employee(code=code, full_name=f"NV {code}", company_id=world.co["A"], department_id=world.dept["A.kt"],
                       hire_date=hire, employment_type=etype)
        db.add(emp)
        db.flush()
        if code == "P2":
            _contract(db, emp, date(2026, 4, 1), CT.PROBATION, end=date(2026, 5, 31))
        if official:
            _contract(db, emp, official)
        row = balance_service.ensure_balance(db, emp, today_year, lt)
        row.company_id, row.used_days = world.co["A"], 1.0
        rows.append(row)
    db.commit()
    return rows


def _report(db, world, year):
    actor = world.actor("a1")
    period = parse_period({"preset": "custom", "date_from": f"{year}-01-01", "date_to": f"{year}-12-31",
                           "compare": "none"})
    return balance_report_service.build_summary(db, actor.user, actor.profile(), period, None)


def test_bao_cao_va_available_days_cung_so(db, world, monkeypatch):
    today = date(2026, 11, 16)
    monkeypatch.setattr(balance_service, "vn_today", lambda: today)
    monkeypatch.setattr(balance_report_spec, "vn_today", lambda: today)
    rows = _after_world(db, world, YEAR)
    expected = round(sum(balance_service.available_days(db, r, today) for r in rows), 2)
    #  P1: tích 10 - dùng 1 = 9; P2: 7 ngày tích, xong 5 tháng (6..10) -> 5 - 1 = 4; P3: 0 - 1 = -1; P4: 8 ngày, xong 6 (5..10) - 1 = 5
    assert expected == 9.0 + 4.0 - 1.0 + 5.0
    assert _report(db, world, YEAR)["totals"]["current"]["remaining"] == expected


def test_available_days_map_khop_goi_le_va_so_truy_van_co_dinh(db, world, monkeypatch):
    from lich_lam_viec_factory import count_queries
    today = date(2026, 11, 16)
    rows = _after_world(db, world, YEAR)
    single = {r.id: balance_service.available_days(db, r, today) for r in rows}
    db.expire_all()
    result, few = count_queries(db, lambda: balance_service.available_days_map(
        db, db.query(LeaveBalance).all(), today))
    assert result == single
    lt = db.query(LeaveType).filter_by(code="annual").one()
    for i in range(10):
        emp = _emp(db, f"Z{i}", hire_date=date(2022, 1, 1))
        _contract(db, emp, date(2022, 1, 1))
        _row(db, emp, lt)
    db.commit()
    db.expire_all()
    result2, many = count_queries(db, lambda: balance_service.available_days_map(
        db, db.query(LeaveBalance).all(), today))
    #  Số câu SQL của riêng available_days_map không đổi: so hai lần chạy (cộng 1 câu đọc quỹ ở mỗi lần).
    assert len(many) == len(few) and len(few) <= 4 and len(result2) == 14


def test_bao_cao_so_truy_van_co_dinh(db, world, monkeypatch):
    from lich_lam_viec_factory import count_queries
    today = date(2026, 11, 16)
    monkeypatch.setattr(balance_service, "vn_today", lambda: today)
    monkeypatch.setattr(balance_report_spec, "vn_today", lambda: today)
    _after_world(db, world, YEAR)
    _report(db, world, YEAR)      # chạy nóng: nạp người dùng / hồ sơ quyền vào phiên
    _, few = count_queries(db, lambda: _report(db, world, YEAR))
    lt = db.query(LeaveType).filter_by(code="annual").one()
    for i in range(8):
        emp = Employee(code=f"Y{i}", full_name=f"NV Y{i}", company_id=world.co["A"], department_id=world.dept["A.kt"],
                       hire_date=date(2022, 1, 1))
        db.add(emp)
        db.flush()
        _contract(db, emp, date(2022, 1, 1))
        row = _row(db, emp, lt)
        row.company_id = world.co["A"]
    db.commit()
    _report(db, world, YEAR)
    _, many = count_queries(db, lambda: _report(db, world, YEAR))
    assert len(many) == len(few)


def test_ma_tran_cung_so_available_days(db, world, monkeypatch):
    from app.modules.leave import balance_matrix_service
    today = date(2026, 11, 16)
    monkeypatch.setattr(balance_service, "vn_today", lambda: today)
    rows = _after_world(db, world, YEAR)
    actor = world.actor("a1")
    out = balance_matrix_service.build_matrix(db, actor.user, actor.profile(), "read", YEAR, None, None, "all",
                                              None, 0, 50)
    lt = db.query(LeaveType).filter_by(code="annual").one()
    by_emp = {r.employee_id: balance_service.available_days(db, r, today) for r in rows}
    cells = {i["employee_id"]: i["cells"][str(lt.id)] for i in out["items"]}
    assert cells == by_emp and len(cells) == 4


def test_tro_ly_tra_phep_cung_so_available_days(db, seed, cap_quyen, monkeypatch):
    from app.modules.assistant import tools as T
    from app.modules.user.model import User
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "leave_request", scope="own", read=True)
    emp = db.get(Employee, seed.emp_req_id)
    emp.hire_date, emp.employment_type = date(2020, 2, 1), EMPLOYMENT_FULL_TIME
    _contract(db, emp, date(2020, 2, 1))
    lt = _type(db, code="annual")
    db.add(LeaveBalance(employee_id=emp.id, year=2026, leave_type_id=lt.id, allocated_days=12.0))
    db.commit()
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 5, 10))
    out = T.run_tool(db, user, "my_leave_summary", {"year": 2026})
    row = next(b for b in out["balances"] if b["leave_type_id"] == lt.id)
    #  Xong 4 tháng (1..4): dùng được 4, còn 8 chưa tới.
    assert row["remaining_days"] == 4.0 and row["not_yet_accrued_days"] == 8.0
    assert row["accrual_mode_label"] == "Cộng dần sau mỗi tháng làm đủ"


# ── 9. Chính sách phân bổ + xem trước dùng chung mốc chính thức ─────────────────────────────────────

def test_allocated_days_khong_phan_bo_khop_prorate_tu_ngay_chinh_thuc(db):
    from app.modules.leave import policy_allocation
    lt = _type(db)
    emp = _emp(db, hire_date=date(2025, 1, 1))
    _contract(db, emp, date(2025, 1, 1), CT.PROBATION, end=date(2025, 3, 1))
    _contract(db, emp, date(2026, 10, 1))
    assert policy_allocation.allocated_days(db, lt, emp, YEAR) == 3.0      # tháng 10..12
    assert policy_allocation.allocated_days(db, lt, emp, 2025) == 0.0      # chưa chính thức năm đó
    assert policy_allocation.allocated_days(db, lt, emp, 2027) == 12.0


# ── 10. Script áp dụng ───────────────────────────────────────────────────────────────────────────────

def _legacy_world(db):
    """Phép năm đang FULL_YEAR; ba quỹ năm nay đã cấp đủ 12 + một quỹ năm trước."""
    lt = _type(db, mode=int(LeaveAccrualMode.FULL_YEAR))
    a = _emp(db, "A", hire_date=date(2024, 1, 1))
    _contract(db, a, date(2024, 1, 1))
    b = _emp(db, "B", hire_date=date(2026, 4, 1))
    _contract(db, b, date(2026, 4, 1), CT.PROBATION)
    _contract(db, b, date(2026, 6, 1))
    c = _emp(db, "C", hire_date=date(2025, 1, 1), employment_type=EMPLOYMENT_PROBATION)
    rows = {}
    for emp in (a, b, c):
        rows[emp.code] = _row(db, emp, lt)
    rows["A"].used_days, rows["A"].seniority_days, rows["A"].carried_days, rows["A"].adjusted_days = 6.0, 1.0, 2.0, 0.5
    rows["A"].comp_days, rows["A"].encashed_days, rows["A"].pending_days = 0.5, 0.5, 1.0
    prev = _row(db, a, lt, 2025)
    db.flush()
    return lt, rows, prev


@pytest.fixture
def script(db, monkeypatch):
    from scripts import apply_monthly_after_annual_leave as mod
    monkeypatch.setattr(mod, "vn_today", lambda: date(2026, 11, 16))
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 11, 16))
    return mod


def test_script_dry_run_khong_ghi_gi(db, script):
    lt, rows, prev = _legacy_world(db)
    db.commit()
    lines, summary = script.run(db, "annual", dry_run=True)
    db.expire_all()
    assert db.get(LeaveType, lt.id).accrual_mode == int(LeaveAccrualMode.FULL_YEAR)
    assert [r.allocated_days for r in db.query(LeaveBalance).filter_by(year=YEAR).order_by(LeaveBalance.id)] == [12.0] * 3
    by_code = {ln.code: ln for ln in lines}
    assert (by_code["A"].old, by_code["A"].new) == (12.0, 12.0)
    assert (by_code["B"].old, by_code["B"].new) == (12.0, 7.0)
    assert (by_code["C"].old, by_code["C"].new) == (12.0, 0.0)
    assert summary["balances"] == 3 and summary["changed"] == 2 and summary["not_accruing"] == 1
    text = script.render(lines, summary, dry_run=True)
    assert "DRY-RUN" in text and "Tổng hợp" in text


def test_script_ghi_that_chi_dung_allocated_nam_nay_va_chay_lai_khong_doi(db, script):
    from app.modules.audit.model import AuditLog   # nhật ký thao tác
    lt, rows, prev = _legacy_world(db)
    db.commit()
    lines, summary = script.run(db, "annual", dry_run=False)
    db.expire_all()
    assert db.get(LeaveType, lt.id).accrual_mode == AFTER and summary["mode_changed"] is True
    a, b, c = (db.query(LeaveBalance).filter_by(year=YEAR, employee_id=rows[k].employee_id).one() for k in "ABC")
    assert (a.allocated_days, b.allocated_days, c.allocated_days) == (12.0, 7.0, 0.0)
    #  Các cột khác của A không đụng.
    assert (a.used_days, a.seniority_days, a.carried_days, a.adjusted_days, a.comp_days, a.encashed_days,
            a.pending_days) == (6.0, 1.0, 2.0, 0.5, 0.5, 0.5, 1.0)
    #  Năm trước giữ nguyên.
    assert db.query(LeaveBalance).filter_by(year=2025).one().allocated_days == 12.0
    #  Nhật ký: một dòng đổi chế độ + hai dòng tính lại quỹ (B, C).
    logs = db.query(AuditLog).filter(AuditLog.entity.in_(["leave_type", "leave_balance"])).all()
    assert sorted(x.entity for x in logs) == ["leave_balance", "leave_balance", "leave_type"]
    #  A: xong 10 tháng -> 10 + 1 + 2 + 0.5 + 0.5 - 6 - 1 - 0.5 = 6.5
    assert balance_service.available_days(db, a, date(2026, 11, 16)) == 6.5
    again_lines, again = script.run(db, "annual", dry_run=False)
    assert again["changed"] == 0 and again["mode_changed"] is False
    assert db.query(AuditLog).filter(AuditLog.entity.in_(["leave_type", "leave_balance"])).count() == 3


def test_script_co_co_am_khi_da_dung_qua_so_tich(db, script):
    lt, rows, prev = _legacy_world(db)
    rows["A"].used_days = 20.0
    db.commit()
    lines, summary = script.run(db, "annual", dry_run=True)
    a = next(ln for ln in lines if ln.code == "A")
    assert a.negative and summary["negative"] >= 1
    assert "ÂM" in script.render(lines, summary, dry_run=True)


def test_script_khong_co_loai_thi_thoat(db, script):
    with pytest.raises(SystemExit):
        script.run(db, "annual", dry_run=True)


# ── 11. Quyết định 2: chỉ có HĐ Thử việc đã ký → chưa tích ──────────────────────────────────────────────

def test_chi_co_hd_thu_viec_con_han_thi_chua_tich_du_hinh_thuc_khac(db):
    emp = _emp(db, hire_date=date(2026, 1, 5), employment_type=EMPLOYMENT_FULL_TIME)
    _contract(db, emp, date(2026, 1, 5), CT.PROBATION, end=date(2026, 12, 31))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing, start.missing_contract) == (None, False, False)
    assert start.status_at(date(2026, 11, 16)) == 2


def test_hd_thu_viec_da_het_han_chua_co_chinh_thuc_van_chua_tich(db):
    lt = _type(db)
    emp = _emp(db, hire_date=date(2025, 1, 5))
    _contract(db, emp, date(2025, 1, 5), CT.PROBATION, end=date(2025, 3, 5))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing) == (None, False)
    row = _row(db, emp, lt)
    assert row.allocated_days == 0.0 and _avail(db, row, date(2026, 11, 16)) == 0.0


def test_thu_viec_het_han_roi_co_hd_chinh_thuc_thi_tich_tu_hd_chinh_thuc(db):
    emp = _emp(db, hire_date=date(2025, 1, 5))
    _contract(db, emp, date(2025, 1, 5), CT.PROBATION, end=date(2025, 3, 5))
    _contract(db, emp, date(2025, 3, 6), CT.FIXED_TERM, end=date(2026, 3, 5))
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing, start.status_at(date(2026, 11, 16))) == (date(2025, 3, 6), True, 1)


def test_hd_thu_viec_nhap_chua_ky_khong_tinh_la_co_hd(db):
    emp = _emp(db, hire_date=date(2026, 2, 3))
    _contract(db, emp, date(2026, 2, 3), CT.PROBATION, CS.DRAFT)
    start = accrual_start_service.official_start(db, emp)
    assert (start.start, start.accruing, start.missing_contract, start.status_at(date(2026, 11, 16))) == (date(2026, 2, 3), True, True, 3)


# ── 12. Quyết định 1: tự tính lại quỹ khi HĐ được ký / đổi hình thức ───────────────────────────────────

@pytest.fixture
def today_pin(monkeypatch):
    from app.modules.leave import accrual_refresh_service
    monkeypatch.setattr(accrual_refresh_service, "vn_today", lambda: date(2026, 11, 16))
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 11, 16))


def _audit_count(db, entity="leave_balance"):
    from app.modules.audit.model import AuditLog
    return db.query(AuditLog).filter(AuditLog.entity == entity).count()


def test_ky_hd_chinh_thuc_tu_tinh_lai_quy_nam_nay(db, today_pin):
    from types import SimpleNamespace

    from app.modules.labor_contract import service as contract_service
    from app.modules.labor_contract.schema import TransitionIn
    lt = _type(db)
    emp = _emp(db, hire_date=date(2026, 4, 1), employment_type=EMPLOYMENT_PROBATION)
    _contract(db, emp, date(2026, 4, 1), CT.PROBATION, end=date(2026, 5, 31))
    old_year = _row(db, emp, lt, 2025)
    row = _row(db, emp, lt)
    assert row.allocated_days == 0.0
    emp.employment_type = EMPLOYMENT_FULL_TIME       # đã chuyển chính thức nhưng chưa có HĐ ký
    draft = _contract(db, emp, date(2026, 6, 1), CT.FIXED_TERM, CS.DRAFT, end=date(2027, 5, 31))
    db.commit()

    contract_service.transition(db, SimpleNamespace(id=9), draft,
                                TransitionIn(to_status=int(CS.SIGNED), date=date(2026, 5, 30)))
    db.expire_all()
    assert db.query(LeaveBalance).filter_by(employee_id=emp.id, year=2026).one().allocated_days == 7.0   # tháng 6..12
    assert db.query(LeaveBalance).filter_by(employee_id=emp.id, year=2025).one().allocated_days == old_year.allocated_days
    assert _audit_count(db) == 1


def test_ky_hd_thu_viec_khong_doi_quy_va_khong_loi(db, today_pin):
    from types import SimpleNamespace

    from app.modules.labor_contract import service as contract_service
    from app.modules.labor_contract.schema import TransitionIn
    lt = _type(db)
    emp = _emp(db, hire_date=date(2026, 4, 1), employment_type=EMPLOYMENT_PROBATION)
    row = _row(db, emp, lt)
    draft = _contract(db, emp, date(2026, 4, 1), CT.PROBATION, CS.DRAFT, end=date(2026, 6, 1))
    db.commit()
    contract_service.transition(db, SimpleNamespace(id=9), draft,
                                TransitionIn(to_status=int(CS.SIGNED), date=date(2026, 4, 1)))
    assert db.get(LeaveBalance, row.id).allocated_days == 0.0 and _audit_count(db) == 0


def test_doi_hinh_thuc_vao_ra_thu_viec_tu_tinh_lai_quy(db, today_pin):
    from app.modules.employee.schema import EmployeeUpdate
    from app.modules.employee.service import update_employee_core
    lt = _type(db)
    emp = _emp(db, hire_date=date(2025, 1, 1))
    row = _row(db, emp, lt)
    old_year = _row(db, emp, lt, 2025)
    assert row.allocated_days == 12.0
    update_employee_core(db, emp, EmployeeUpdate(employment_type=EMPLOYMENT_PROBATION), 1)
    assert row.allocated_days == 0.0 and _audit_count(db) == 1
    update_employee_core(db, emp, EmployeeUpdate(employment_type=EMPLOYMENT_FULL_TIME), 1)
    assert row.allocated_days == 12.0 and _audit_count(db) == 2
    assert old_year.allocated_days == 12.0
    #  Sửa ô khác: không đụng tới quỹ, không thêm nhật ký.
    update_employee_core(db, emp, EmployeeUpdate(work_location="Kho 2"), 1)
    assert _audit_count(db) == 2


def test_doi_ngay_vao_lam_khi_chua_co_hd_tinh_lai(db, today_pin):
    from app.modules.employee.schema import EmployeeUpdate
    from app.modules.employee.service import update_employee_core
    lt = _type(db)
    emp = _emp(db, hire_date=date(2026, 3, 10))
    row = _row(db, emp, lt)
    assert row.allocated_days == 10.0
    update_employee_core(db, emp, EmployeeUpdate(hire_date=date(2026, 6, 10)), 1)
    assert row.allocated_days == 7.0


def test_tu_lam_moi_khong_dung_loai_khac_nam_cu_va_nguoi_khac(db, today_pin):
    from app.modules.leave.accrual_refresh_service import refresh_monthly_after_allocation
    after = _type(db)
    other = _type(db, int(LeaveAccrualMode.FULL_YEAR), code="sick", name="Ốm")
    a, b = _emp(db, "A", hire_date=date(2025, 1, 1)), _emp(db, "B", hire_date=date(2025, 1, 1))
    ra, rb, ro, rold = _row(db, a, after), _row(db, b, after), _row(db, a, other), _row(db, a, after, 2025)
    for emp in (a, b):
        emp.employment_type = EMPLOYMENT_PROBATION
    items = refresh_monthly_after_allocation(db, [a.id])
    assert [(i.employee.code, i.old, i.new) for i in items] == [("A", 12.0, 0.0)]
    assert (ra.allocated_days, rb.allocated_days, ro.allocated_days, rold.allocated_days) == (0.0, 12.0, 12.0, 12.0)
    assert refresh_monthly_after_allocation(db, []) == []


def test_tu_lam_moi_khong_co_loai_cong_dan_sau_thang_thi_khong_lam_gi(db, today_pin):
    from app.modules.leave.accrual_refresh_service import refresh_monthly_after_allocation
    lt = _type(db, int(LeaveAccrualMode.MONTHLY))
    emp = _emp(db, hire_date=date(2025, 1, 1), employment_type=EMPLOYMENT_PROBATION)
    _row(db, emp, lt)
    assert refresh_monthly_after_allocation(db, [emp.id]) == [] and _audit_count(db) == 0


# ── 13. Quyết định 3: ba trường tích phép ở các đường trả quỹ ───────────────────────────────────────────

def _fields_world(db, world):
    """Ba người: chính thức / thử việc / chưa có HĐ; thêm một quỹ loại khác (không MONTHLY_AFTER)."""
    world.grant("a1", "leave_balance", scope="all", actions=("read",))
    world.grant("a1", "employee", scope="all", actions=("read",))
    db.query(Employee).update({Employee.status: "resigned"})
    after = _type(db)
    sick = _type(db, int(LeaveAccrualMode.FULL_YEAR), code="sick", name="Ốm")
    out = {}
    for code, hire, official, etype in (("F1", date(2023, 1, 1), date(2023, 2, 1), EMPLOYMENT_FULL_TIME),
                                         ("F2", date(2025, 1, 1), None, EMPLOYMENT_PROBATION),
                                         ("F3", date(2025, 7, 7), None, EMPLOYMENT_FULL_TIME)):
        emp = Employee(code=code, full_name=f"NV {code}", company_id=world.co["A"], department_id=world.dept["A.kt"],
                       hire_date=hire, employment_type=etype)
        db.add(emp)
        db.flush()
        if official:
            _contract(db, emp, official)
        rows = [balance_service.ensure_balance(db, emp, YEAR, after), balance_service.ensure_balance(db, emp, YEAR, sick)]
        for r in rows:
            r.company_id = world.co["A"]
        out[code] = rows
    db.commit()
    return out


def test_truong_tich_phep_o_ham_dung_chung_va_dong_quy(db, world):
    from app.modules.leave.balance_accrual_info import NO_ACCRUAL_INFO, accrual_info_map
    rows = _fields_world(db, world)
    flat = [r for pair in rows.values() for r in pair]
    info = accrual_info_map(db, flat)
    assert info[rows["F1"][0].id] == {"accrual_start_date": "2023-02-01", "accrual_status": 1,
                                      "accrual_status_label": "Đang tích"}
    assert info[rows["F2"][0].id] == {"accrual_start_date": None, "accrual_status": 2,
                                      "accrual_status_label": "Đang thử việc — chưa tích"}
    assert info[rows["F3"][0].id] == {"accrual_start_date": "2025-07-07", "accrual_status": 3,
                                      "accrual_status_label": "Chưa có HĐLĐ trên hệ thống"}
    assert all(info[pair[1].id] == NO_ACCRUAL_INFO for pair in rows.values())     # loại khác → null


def test_truong_tich_phep_trong_dump_va_so_truy_van_co_dinh(db, world):
    from lich_lam_viec_factory import count_queries

    from app.modules.leave import balance_controller
    from app.modules.leave.balance_accrual_info import accrual_info_map
    rows = _fields_world(db, world)
    flat = [r for pair in rows.values() for r in pair]
    dumped = balance_controller._dump(db, flat[0], {}, {})            # đường một dòng tự tính
    assert dumped["accrual_status"] == 1 and dumped["accrual_start_date"] == "2023-02-01"
    flat = db.query(LeaveBalance).all()      # nạp sẵn: không tính lần nạp lười của ORM vào số đếm
    _, few = count_queries(db, lambda: accrual_info_map(db, flat))
    lt = db.query(LeaveType).filter_by(code="annual").one()
    for i in range(6):
        emp = _emp(db, f"Q{i}", hire_date=date(2022, 1, 1))
        _row(db, emp, lt)
    db.commit()
    more = db.query(LeaveBalance).all()
    _, many = count_queries(db, lambda: accrual_info_map(db, more))
    assert len(many) == len(few) == 3


def test_ma_tran_co_khoa_accrual_chi_o_loai_cong_dan_sau_thang(db, world):
    from app.modules.leave import balance_matrix_service
    rows = _fields_world(db, world)
    actor = world.actor("a1")
    out = balance_matrix_service.build_matrix(db, actor.user, actor.profile(), "read", YEAR, None, None, "all",
                                              None, 0, 50)
    after_id = rows["F1"][0].leave_type_id
    sick_id = rows["F1"][1].leave_type_id
    by_code = {i["code"]: i for i in out["items"]}
    assert set(by_code["F1"]["accrual"]) == {str(after_id)} and str(sick_id) not in by_code["F1"]["accrual"]
    assert by_code["F2"]["accrual"][str(after_id)]["accrual_status"] == 2
    assert by_code["F3"]["accrual"][str(after_id)]["accrual_status_label"] == "Chưa có HĐLĐ trên hệ thống"
    assert by_code["F1"]["cells"][str(after_id)] == balance_service.available_days(db, rows["F1"][0])


def test_tro_ly_tom_tat_phep_co_ba_truong(db, seed, cap_quyen):
    from app.modules.assistant import tools as T
    from app.modules.user.model import User
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "leave_request", scope="own", read=True)
    emp = db.get(Employee, seed.emp_req_id)
    emp.hire_date, emp.employment_type = date(2026, 3, 1), EMPLOYMENT_PROBATION
    lt = _type(db, code="annual")
    sick = _type(db, int(LeaveAccrualMode.FULL_YEAR), code="sick", name="Ốm")
    for t in (lt, sick):
        db.add(LeaveBalance(employee_id=emp.id, year=2026, leave_type_id=t.id, allocated_days=12.0))
    db.commit()
    out = T.run_tool(db, user, "my_leave_summary", {"year": 2026})
    by_id = {b["leave_type_id"]: b for b in out["balances"]}
    assert (by_id[lt.id]["accrual_start_date"], by_id[lt.id]["accrual_status"]) == (None, 2)
    assert by_id[lt.id]["accrual_status_label"] == "Đang thử việc — chưa tích"
    assert by_id[sick.id]["accrual_status"] is None and by_id[sick.id]["accrual_start_date"] is None
    assert {"accrual_start_date", "accrual_status_label"} <= set(out["glossary"])


def test_tro_ly_tra_phep_nguoi_khac_co_ba_truong(db, seed, cap_quyen):
    from app.modules.assistant import tools as T
    from app.modules.user.model import User
    emp = db.get(Employee, seed.emp_req_id)
    emp.hire_date = date(2024, 2, 5)
    lt = _type(db, code="annual")
    db.add(LeaveBalance(employee_id=emp.id, year=2026, leave_type_id=lt.id, company_id=emp.company_id,
                        allocated_days=12.0))
    db.commit()
    for ent in ("leave_balance", "employee", "leave_request"):
        cap_quyen(seed.u_nstm_id, ent, scope="all", read=True)
    out = T.run_tool(db, db.get(User, seed.u_nstm_id), "employee_leave_summary", {"employee": "TESTREQ", "year": 2026})
    bal = out["employees"][0]["balances"][0]
    assert (bal["accrual_start_date"], bal["accrual_status"]) == ("2024-02-05", 3)
    assert bal["accrual_status_label"] == "Chưa có HĐLĐ trên hệ thống"


# ── 14. Review: C1 làm mới cả năm sau ─────────────────────────────────────────────────────────────────

@pytest.fixture
def dec_20(monkeypatch):
    from app.modules.leave import accrual_refresh_service
    day = date(2026, 12, 20)
    for module in (accrual_refresh_service, balance_service, accrual_start_service):
        monkeypatch.setattr(module, "vn_today", lambda: day)
    return day


def test_c1_ky_hd_chinh_thuc_tu_01_01_nam_sau_tinh_lai_ca_quy_nam_sau(db, dec_20):
    from types import SimpleNamespace

    from app.modules.labor_contract import service as contract_service
    from app.modules.labor_contract.schema import TransitionIn
    lt = _type(db)
    emp = _emp(db, hire_date=date(2026, 10, 1), employment_type=EMPLOYMENT_PROBATION)
    _contract(db, emp, date(2026, 10, 1), CT.PROBATION, end=date(2026, 12, 31))
    past, this_year, nxt = _row(db, emp, lt, 2025), _row(db, emp, lt, 2026), _row(db, emp, lt, 2027)
    assert (this_year.allocated_days, nxt.allocated_days) == (0.0, 0.0)
    draft = _contract(db, emp, date(2027, 1, 1), CT.INDEFINITE, CS.DRAFT)
    db.commit()
    contract_service.transition(db, SimpleNamespace(id=9), draft,
                                TransitionIn(to_status=int(CS.SIGNED), date=date(2026, 12, 20)))
    db.expire_all()
    got = {b.year: b.allocated_days for b in db.query(LeaveBalance).filter_by(employee_id=emp.id)}
    assert got == {2025: 0.0, 2026: 0.0, 2027: 12.0}      # 2026 vẫn 0 (chính thức từ 2027), 2025 không đụng
    assert _audit_count(db) == 1


def test_c1_ham_lam_moi_cham_nam_nay_va_nam_sau_khong_cham_nam_qua(db, dec_20):
    from app.modules.leave.accrual_refresh_service import refresh_monthly_after_allocation
    lt = _type(db)
    emp = _emp(db, hire_date=date(2024, 1, 1))
    rows = {y: _row(db, emp, lt, y) for y in (2025, 2026, 2027, 2028)}
    emp.employment_type = EMPLOYMENT_PROBATION
    items = refresh_monthly_after_allocation(db, [emp.id])
    assert sorted(i.balance.year for i in items) == [2026, 2027, 2028]
    assert [rows[y].allocated_days for y in (2025, 2026, 2027, 2028)] == [12.0, 0.0, 0.0, 0.0]


# ── 15. Review: N1 đổi loại nghỉ sang chế độ mới ──────────────────────────────────────────────────────

def _patch_leave_type(db, actor, lt, **values):
    from app.modules.leave.catalog_controller import leave_type_router
    from app.modules.leave.schema import LeaveTypeUpdate
    route = next(r for r in leave_type_router.routes if getattr(r, "name", "") == "update_item"
                 and "PATCH" in r.methods)
    return route.endpoint(lt.id, LeaveTypeUpdate(**values), db, actor.user)


def test_n1_doi_sang_che_do_moi_qua_api_tinh_lai_quy_cung_giao_dich(db, world, today_pin):
    world.grant("a1", "leave_type", scope="all", actions=("read", "write"))
    lt = _type(db, int(LeaveAccrualMode.FULL_YEAR))
    emp = Employee(code="N1", full_name="NV N1", company_id=world.co["A"], department_id=world.dept["A.kt"],
                   hire_date=date(2025, 1, 1), employment_type=EMPLOYMENT_PROBATION)
    db.add(emp)
    db.flush()
    cur, nxt, past = _row(db, emp, lt), _row(db, emp, lt, 2027), _row(db, emp, lt, 2025)
    assert (cur.allocated_days, nxt.allocated_days) == (12.0, 12.0)
    db.commit()
    _patch_leave_type(db, world.actor("a1"), lt, name="Phép năm mới tên")        # sửa ô khác: không đụng quỹ
    assert (cur.allocated_days, nxt.allocated_days) == (12.0, 12.0)
    _patch_leave_type(db, world.actor("a1"), lt, accrual_mode=AFTER)
    db.expire_all()
    got = {b.year: b.allocated_days for b in db.query(LeaveBalance).filter_by(employee_id=emp.id)}
    assert got == {2025: 12.0, 2026: 0.0, 2027: 0.0}          # thử việc → 0; năm đã qua giữ nguyên
    assert db.get(LeaveType, lt.id).accrual_mode == AFTER


def test_n1_doi_roi_che_do_moi_giu_nguyen_allocated(db, world, today_pin):
    world.grant("a1", "leave_type", scope="all", actions=("read", "write"))
    lt = _type(db)
    emp = _emp(db, hire_date=date(2026, 3, 10))
    row = _row(db, emp, lt)
    assert row.allocated_days == 10.0
    db.commit()
    _patch_leave_type(db, world.actor("a1"), lt, accrual_mode=int(LeaveAccrualMode.FULL_YEAR))
    assert db.query(LeaveBalance).filter_by(id=row.id).one().allocated_days == 10.0


# ── 16. Review: N2 chỉ làm lại khi mốc tích đổi ───────────────────────────────────────────────────────

def test_n2_sua_ho_so_khong_doi_moc_thi_khong_dung_quy(db, today_pin):
    from app.modules.employee.schema import EmployeeUpdate
    from app.modules.employee.service import update_employee_core
    lt = _type(db)
    emp = _emp(db, hire_date=date(2024, 1, 1))
    _contract(db, emp, date(2024, 1, 1))
    row = _row(db, emp, lt)
    row.allocated_days = 99.0                                   # quỹ cấp từ hạn mức cũ
    update_employee_core(db, emp, EmployeeUpdate(employment_type=EMPLOYMENT_PROBATION), 1)   # có HĐ chính thức → mốc không đổi
    update_employee_core(db, emp, EmployeeUpdate(hire_date=date(2024, 1, 10)), 1)             # idem (vẫn trong một tháng)
    assert row.allocated_days == 99.0 and _audit_count(db) == 0


def test_n2_ky_them_hd_khong_doi_moc_thi_khong_dung_quy(db, today_pin):
    from types import SimpleNamespace

    from app.modules.labor_contract import service as contract_service
    from app.modules.labor_contract.schema import TransitionIn
    lt = _type(db)
    emp = _emp(db, hire_date=date(2024, 1, 1))
    _contract(db, emp, date(2024, 1, 1))
    row = _row(db, emp, lt)
    row.allocated_days = 99.0
    renewal = _contract(db, emp, date(2025, 1, 1), CT.FIXED_TERM, CS.DRAFT, end=date(2026, 12, 31))
    db.commit()
    contract_service.transition(db, SimpleNamespace(id=9), renewal,
                                TransitionIn(to_status=int(CS.SIGNED), date=date(2024, 12, 20)))
    assert db.query(LeaveBalance).filter_by(id=row.id).one().allocated_days == 99.0


def test_n2_previous_starts_khop_thi_bo_qua_va_khong_truyen_thi_tinh_lai_het(db, today_pin):
    from app.modules.leave.accrual_refresh_service import refresh_monthly_after_allocation
    lt = _type(db)
    emp = _emp(db, hire_date=date(2024, 1, 1))
    row = _row(db, emp, lt)
    row.allocated_days = 99.0
    same = {emp.id: accrual_start_service.official_start(db, emp)}
    assert refresh_monthly_after_allocation(db, [emp.id], previous_starts=same) == []
    assert row.allocated_days == 99.0
    assert [i.new for i in refresh_monthly_after_allocation(db, [emp.id])] == [12.0] and row.allocated_days == 12.0


def test_nhap_excel_chay_thu_khong_lam_moi_quy(db, today_pin):
    from app.modules.employee.schema import EmployeeUpdate
    from app.modules.employee.service import update_employee_core
    lt = _type(db)
    emp = _emp(db, hire_date=date(2025, 1, 1))
    row = _row(db, emp, lt)
    update_employee_core(db, emp, EmployeeUpdate(employment_type=EMPLOYMENT_PROBATION), 1, refresh_quota=False)
    assert row.allocated_days == 12.0 and _audit_count(db) == 0


# ── 17. Review: trạng thái nhãn, năm đã qua, hiệu năng ────────────────────────────────────────────────

def test_ma_va_nhan_trang_thai_do_backend_gui():
    from app.modules.leave.constants import LEAVE_ACCRUAL_STATUS_LABELS, LeaveAccrualStatus
    assert {int(k): v for k, v in LEAVE_ACCRUAL_STATUS_LABELS.items()} == {
        1: "Đang tích", 2: "Đang thử việc — chưa tích", 3: "Chưa có HĐLĐ trên hệ thống",
        4: "Lịch sử HĐLĐ chưa đủ — đang tính từ ngày vào làm",
        5: "Hợp đồng dịch vụ / cộng tác viên — không tích phép năm", 6: "Chưa tới ngày làm chính thức"}
    assert [int(x) for x in LeaveAccrualStatus] == [1, 2, 3, 4, 5, 6]


def test_nam_da_qua_khong_co_truong_tich_phep(db):
    from app.modules.leave.balance_accrual_info import NO_ACCRUAL_INFO, accrual_info_map
    lt = _type(db)
    emp = _emp(db, hire_date=date(2024, 1, 1))
    past, now = _row(db, emp, lt, 2020), _row(db, emp, lt, vn_today_year())
    info = accrual_info_map(db, [past, now])
    assert info[past.id] == NO_ACCRUAL_INFO and info[now.id]["accrual_status"] == 3


def vn_today_year() -> int:
    from app.core.vn_time import vn_today
    return vn_today().year


def test_trang_thai_dang_dich_vu_va_chua_toi_ngay_o_truong_api(db):
    from app.modules.leave.balance_accrual_info import fields_of
    svc = accrual_start_service.AccrualStart(None, False, False, service_only=True)
    fut = accrual_start_service.AccrualStart(date(2027, 1, 1), True, False)
    inc = accrual_start_service.AccrualStart(date(2020, 1, 1), True, False, incomplete=True)
    today = date(2026, 11, 16)
    assert fields_of(svc, today)["accrual_status_label"] == "Hợp đồng dịch vụ / cộng tác viên — không tích phép năm"
    assert fields_of(fut, today) == {"accrual_start_date": "2027-01-01", "accrual_status": 6,
                                     "accrual_status_label": "Chưa tới ngày làm chính thức"}
    assert fields_of(inc, today)["accrual_status"] == 4


def _contract_queries(queries) -> int:
    return sum(1 for q in queries if "FROM tab_labor_contract" in q)


def test_lam_moi_chi_truy_van_hd_mot_lan_cho_ca_lo(db, today_pin):
    from lich_lam_viec_factory import count_queries

    from app.modules.leave.accrual_refresh_service import refresh_monthly_after_allocation
    lt = _type(db)
    for i in range(8):
        emp = _emp(db, f"R{i}", hire_date=date(2024, 1, 1))
        _contract(db, emp, date(2024, 1, 1))
        _row(db, emp, lt).allocated_days = 1.0
    db.commit()
    items, queries = count_queries(db, lambda: refresh_monthly_after_allocation(db, None))
    assert len(items) == 8 and all(i.new == 12.0 for i in items)
    assert _contract_queries(queries) == 1


def test_cap_quy_hang_loat_nap_gom_mot_lan_hd(db, world, today_pin):
    from lich_lam_viec_factory import count_queries

    from app.modules.leave import balance_controller
    from app.modules.leave.schema import LeaveBalanceAllocate
    world.grant("a1", "leave_balance", scope="all", actions=("read", "create"))
    world.grant("a1", "employee", scope="all", actions=("read",))
    db.query(Employee).update({Employee.is_active: False})
    _type(db)
    for i in range(6):
        emp = Employee(code=f"AL{i}", full_name=f"NV AL{i}", company_id=world.co["A"],
                       department_id=world.dept["A.kt"], hire_date=date(2024, 1, 1), is_active=True)
        db.add(emp)
        db.flush()
        _contract(db, emp, date(2024, 1, 1))
    db.commit()
    actor = world.actor("a1")
    out, queries = count_queries(db, lambda: balance_controller.allocate(LeaveBalanceAllocate(year=2026), db, actor.user))
    import json
    assert json.loads(out.body)["data"]["created"] == 6
    assert _contract_queries(queries) == 1


# ── 18. Script: cờ lịch sử HĐ chưa đủ + đổi do hạn mức hiện hành ───────────────────────────────────

def test_script_co_lich_su_chua_du_va_doi_do_han_muc_hien_hanh(db, script):
    lt = _type(db, mode=int(LeaveAccrualMode.FULL_YEAR))
    drift = _emp(db, "D", hire_date=date(2024, 1, 1))                       # không HĐ, quỹ cũ 10 ≠ hạn mức hiện hành 12
    inc = _emp(db, "I", hire_date=date(2019, 1, 1))
    _contract(db, inc, date(2023, 1, 1))                                    # HĐ đầu tiên muộn hơn 1 tháng, không thử việc
    off = _emp(db, "O", hire_date=date(2026, 3, 1))
    _contract(db, off, date(2026, 3, 1), CT.PROBATION, end=date(2026, 5, 31))
    _contract(db, off, date(2026, 6, 1))
    for emp in (drift, inc, off):
        _row(db, emp, lt)
    db.query(LeaveBalance).filter_by(employee_id=drift.id).one().allocated_days = 10.0
    db.commit()
    lines, summary = script.run(db, "annual", dry_run=True)
    by = {ln.code: ln for ln in lines}
    assert by["D"].quota_drift is True and (by["D"].old, by["D"].new) == (10.0, 12.0)
    assert by["I"].incomplete is True and by["I"].quota_drift is False
    assert by["O"].quota_drift is False and by["O"].new == 7.0              # đổi do mốc chính thức, không do hạn mức
    assert summary["incomplete"] == 1 and summary["quota_drift"] == 1
    text = script.render(lines, summary, dry_run=True)
    assert "hạn mức hiện hành khác số đã cấp" in text and "Lịch sử HĐLĐ chưa đủ" in text


# ── 19. Hook after_update của CRUD: vi phạm duy nhất khi flush → 400 như lúc commit ─────────────────

def test_crud_after_update_integrity_error_thanh_400(db, world):
    from fastapi import HTTPException
    from sqlalchemy.exc import IntegrityError

    from app.core.crud import make_crud_router
    from app.modules.leave.schema import LeaveTypeCreate, LeaveTypeResponse, LeaveTypeUpdate
    world.grant("a1", "leave_type", scope="all", actions=("read", "write"))
    lt = _type(db)
    db.commit()

    def boom(db_, obj, before, user):
        raise IntegrityError("flush", {}, Exception("duplicate"))

    router = make_crud_router("/api/x-leave-types", "leave_type", LeaveType, LeaveTypeCreate, LeaveTypeUpdate,
                              LeaveTypeResponse, filterable=["code"], unique_field="code", after_update=boom)
    route = next(r for r in router.routes if getattr(r, "name", "") == "update_item" and "PATCH" in r.methods)
    with pytest.raises(HTTPException) as err:
        route.endpoint(lt.id, LeaveTypeUpdate(name="Tên mới"), db, world.actor("a1").user)
    assert err.value.status_code == 400 and "code đã tồn tại" in err.value.detail
