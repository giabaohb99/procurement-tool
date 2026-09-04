"""P-03 (CR-259) — hai service nền của Nghỉ phép: đếm ngày công và sổ quỹ phép.

Hai thứ này là chỗ sai lặng lẽ nhất của cả phân hệ: đếm sai một nửa ngày thì
không ai kêu, nhưng cuối năm sổ phép lệch; quên nhịp GIỮ CHỖ thì nộp mười đơn
liền tay đều lọt và chỉ lộ ra khi đã có người nghỉ thừa hai tuần.
"""
from datetime import date

import pytest
from fastapi import HTTPException

from app.modules.leave import balance_service, workday_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import Holiday, LeaveType, LeaveTypeSeniority
from app.modules.leave.constants import (SESSION_AFTERNOON, SESSION_FULL,
                                         SESSION_MORNING)
from app.modules.employee.model import Employee


# ── Dựng dữ liệu ────────────────────────────────────────────────────────────────

def _leave_type(db, **kw):
    kw.setdefault("code", "annual")
    kw.setdefault("name", "Phép năm")
    kw.setdefault("counts_balance", True)
    kw.setdefault("annual_quota_days", 12.0)
    obj = LeaveType(**kw)
    db.add(obj)
    db.flush()
    return obj


def _employee(db, hire_date=None, company_id=1):
    obj = Employee(code="NV001", full_name="Nguyễn Văn A",
                   company_id=company_id, hire_date=hire_date)
    db.add(obj)
    db.flush()
    return obj


# ── 1. Đếm ngày công ────────────────────────────────────────────────────────────

def test_nghi_tron_mot_ngay_thuong_la_mot_ngay(db):
    #  Thứ Hai 05/01/2026.
    assert workday_service.count_leave_days(db, date(2026, 1, 5), date(2026, 1, 5)) == 1.0


def test_nghi_nua_ngay_la_nua_ngay(db):
    got = workday_service.count_leave_days(
        db, date(2026, 1, 5), date(2026, 1, 5), SESSION_MORNING, SESSION_MORNING)
    assert got == 0.5


def test_bo_qua_CHU_NHAT_nhung_van_tinh_THU_BAY(db):
    """DEGO Holding **làm cả ngày thứ Bảy** — chỉ Chủ nhật được miễn (04/09/2026).

    Thứ Sáu 02/01 → Thứ Hai 05/01 là 4 ngày lịch: T6, T7, CN, T2. Trừ mỗi Chủ
    nhật ra thì còn **3 ngày công**.

    ⚠️ Bài này từng khẳng định `2.0` theo mặc định "tuần làm 5 ngày", và con số
    đó sai với công ty này theo đúng hướng tốn tiền. Đừng sửa ngược lại cho
    "giống lệ thường" — xem `WEEKEND_DAYS` ở `workday_service`.
    """
    got = workday_service.count_leave_days(db, date(2026, 1, 2), date(2026, 1, 5))
    assert got == 3.0


def test_nghi_RIENG_mot_thu_bay_van_tru_mot_ngay_phep(db):
    """Ca lộ rõ nhất của luật cũ: nghỉ đúng một thứ Bảy thì trừ **0** ngày phép —
    tức nghỉ mà không mất gì. 03/01/2026 là thứ Bảy."""
    assert workday_service.count_leave_days(db, date(2026, 1, 3), date(2026, 1, 3)) == 1.0


def test_nghi_RIENG_mot_chu_nhat_khong_tru_phep(db):
    """Đối chứng cho bài trên — 04/01/2026 là Chủ nhật."""
    assert workday_service.count_leave_days(db, date(2026, 1, 4), date(2026, 1, 4)) == 0.0


def test_tron_mot_tuan_la_sau_ngay_cong(db):
    """T2 05/01 → CN 11/01: bảy ngày lịch, trừ mỗi Chủ nhật còn sáu."""
    assert workday_service.count_leave_days(db, date(2026, 1, 5), date(2026, 1, 11)) == 6.0


def test_bo_qua_ngay_le(db):
    """Thêm một ngày lễ giữa tuần thì số ngày phải rút đi đúng một."""
    truoc = workday_service.count_leave_days(db, date(2026, 1, 5), date(2026, 1, 9))
    assert truoc == 5.0

    db.add(Holiday(company_id=0, date=date(2026, 1, 7), name="Nghỉ thử"))
    db.flush()
    assert workday_service.count_leave_days(db, date(2026, 1, 5), date(2026, 1, 9)) == 4.0


def test_ngay_le_cua_phap_nhan_khac_khong_dinh_toi_minh(db):
    """`company_id` khác thì không phải lễ của mình — chỉ dòng `0` mới dùng chung."""
    db.add(Holiday(company_id=99, date=date(2026, 1, 7), name="Lễ riêng cty 99"))
    db.flush()
    assert workday_service.count_leave_days(
        db, date(2026, 1, 5), date(2026, 1, 9), company_id=1) == 5.0
    assert workday_service.count_leave_days(
        db, date(2026, 1, 5), date(2026, 1, 9), company_id=99) == 4.0


def test_ngay_le_lap_hang_nam_khop_theo_ngay_thang(db):
    """Nhập «01/01/2020» có cờ lặp thì năm 2026 vẫn phải nhận ra."""
    db.add(Holiday(company_id=0, date=date(2020, 1, 1), name="Tết Dương lịch",
                   is_recurring=True))
    db.flush()
    #  01/01/2026 là thứ Năm — không rơi vào cuối tuần, nên phần rút đi là do lễ.
    assert workday_service.count_leave_days(db, date(2026, 1, 1), date(2026, 1, 2)) == 1.0


def test_khong_tru_le_khi_loai_nghi_tat_co(db):
    """Thai sản nghỉ liên tục — `exclude_holiday=False` thì đếm cả cuối tuần."""
    got = workday_service.count_leave_days(
        db, date(2026, 1, 2), date(2026, 1, 5), exclude_holiday=False)
    assert got == 4.0


def test_khoang_nguoc_tra_khong(db):
    """Chặn khoảng ngược là việc của tầng schema; ở đây trả 0 chứ không nổ."""
    assert workday_service.count_leave_days(db, date(2026, 1, 9), date(2026, 1, 5)) == 0.0


def test_dau_cuoi_nua_buoi_cong_don_dung(db):
    """Chiều T2 → sáng T4 = 0.5 + 1 + 0.5 = 2 ngày."""
    got = workday_service.count_leave_days(
        db, date(2026, 1, 5), date(2026, 1, 7), SESSION_AFTERNOON, SESSION_MORNING)
    assert got == 2.0


# ── 2. Thâm niên ────────────────────────────────────────────────────────────────

def test_chua_khai_ngay_vao_lam_thi_coi_nhu_khong_nam(db):
    """Q4 — hồ sơ cũ chưa nhập `hire_date` KHÔNG được chặn, chỉ tính 0 năm."""
    assert balance_service.seniority_years(None) == 0


def test_thâm_nien_tron_nam(db):
    assert balance_service.seniority_years(date(2020, 1, 1), date(2026, 1, 1)) == 6
    #  Chưa tới ngày kỷ niệm trong năm thì chưa đủ năm đó.
    assert balance_service.seniority_years(date(2020, 6, 1), date(2026, 1, 1)) == 5


def test_lay_bac_cao_nhat_khop_duoc_khong_cong_don(db):
    """Khai «từ 5 năm +1» và «từ 10 năm +2» thì người 10 năm được +2, không phải +3."""
    lt = _leave_type(db)
    db.add_all([
        LeaveTypeSeniority(leave_type_id=lt.id, years_from=5, years_to=10, extra_days=1),
        LeaveTypeSeniority(leave_type_id=lt.id, years_from=10, years_to=0, extra_days=2),
    ])
    db.flush()
    assert balance_service.seniority_days(db, lt.id, 3) == 0.0
    assert balance_service.seniority_days(db, lt.id, 5) == 1.0
    assert balance_service.seniority_days(db, lt.id, 9) == 1.0
    assert balance_service.seniority_days(db, lt.id, 10) == 2.0
    assert balance_service.seniority_days(db, lt.id, 40) == 2.0


# ── 3. Sổ quỹ ───────────────────────────────────────────────────────────────────

def test_cap_phat_lan_dau_cong_ca_tham_nien(db):
    lt = _leave_type(db, annual_quota_days=12.0)
    db.add(LeaveTypeSeniority(leave_type_id=lt.id, years_from=5, years_to=0, extra_days=1))
    emp = _employee(db, hire_date=date(2018, 1, 1))
    db.flush()

    row = balance_service.ensure_balance(db, emp, 2026, lt)
    assert row.allocated_days == 12.0
    assert row.seniority_days == 1.0
    assert row.total_days == 13.0
    assert row.remaining_days == 13.0


def test_cap_phat_khong_tao_dong_thu_hai(db):
    """Gọi lại phải trả ĐÚNG dòng cũ — hai dòng là quỹ nhân đôi."""
    lt, emp = _leave_type(db), _employee(db)
    a = balance_service.ensure_balance(db, emp, 2026, lt)
    b = balance_service.ensure_balance(db, emp, 2026, lt)
    assert a.id == b.id
    assert db.query(LeaveBalance).count() == 1


def test_giu_cho_tru_ngay_vao_so_con_lai(db):
    """Nhịp thiếu là hỏng cả sổ: đơn CHỜ DUYỆT phải ăn ngay vào số còn lại."""
    lt, emp = _leave_type(db), _employee(db)
    balance_service.reserve(db, emp, 2026, lt, 3.0)
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 9.0


def test_duyet_chuyen_giu_cho_sang_da_dung(db):
    lt, emp = _leave_type(db), _employee(db)
    balance_service.reserve(db, emp, 2026, lt, 3.0)
    balance_service.consume(db, emp.id, 2026, lt.id, 3.0)

    row = balance_service.get_balance(db, emp.id, 2026, lt.id)
    assert (row.pending_days, row.used_days) == (0.0, 3.0)
    assert row.remaining_days == 9.0


def test_tu_choi_tra_lai_giu_cho(db):
    lt, emp = _leave_type(db), _employee(db)
    balance_service.reserve(db, emp, 2026, lt, 3.0)
    balance_service.release(db, emp.id, 2026, lt.id, 3.0)
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 12.0


def test_huy_don_da_duyet_hoan_lai_ngay_da_tru(db):
    lt, emp = _leave_type(db), _employee(db)
    balance_service.reserve(db, emp, 2026, lt, 2.0)
    balance_service.consume(db, emp.id, 2026, lt.id, 2.0)
    balance_service.refund_used(db, emp.id, 2026, lt.id, 2.0)
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 12.0


def test_tra_lai_khong_bao_gio_lam_quy_phinh_ra(db):
    """`pending` âm nghĩa là quỹ tự phình — kẹp ở 0, xem docstring `release`."""
    lt, emp = _leave_type(db), _employee(db)
    balance_service.reserve(db, emp, 2026, lt, 1.0)
    balance_service.release(db, emp.id, 2026, lt.id, 5.0)

    row = balance_service.get_balance(db, emp.id, 2026, lt.id)
    assert row.pending_days == 0.0
    assert row.remaining_days == 12.0


# ── 4. QĐ-NP2 — vượt quỹ thì CHẶN, không ghi nợ ─────────────────────────────────

def test_vuot_quy_bi_chan(db):
    lt, emp = _leave_type(db, annual_quota_days=12.0), _employee(db)
    with pytest.raises(HTTPException) as e:
        balance_service.check_enough(db, emp, 2026, lt, 13.0)
    assert e.value.status_code == 400
    #  Câu báo phải chỉ đường sang «Nghỉ không lương», không chỉ nói "hết phép".
    assert "Nghỉ không lương" in e.value.detail


def test_dung_bang_quy_thi_qua(db):
    lt, emp = _leave_type(db, annual_quota_days=12.0), _employee(db)
    balance_service.check_enough(db, emp, 2026, lt, 12.0)   # không ném


def test_loai_khong_tru_quy_thi_bao_nhieu_cung_qua(db):
    """Nghỉ không lương — không hạn mức, và không cần có dòng quỹ nào."""
    lt = _leave_type(db, code="unpaid", name="Nghỉ không lương",
                     counts_balance=False, annual_quota_days=0.0)
    emp = _employee(db)
    balance_service.check_enough(db, emp, 2026, lt, 90.0)
    assert db.query(LeaveBalance).count() == 0


def test_sua_don_dang_cho_duyet_khong_bi_tinh_hai_lan(db):
    """Sửa đơn 3 ngày xuống 2 ngày mà báo hết phép là lỗi `exclude_days`."""
    lt, emp = _leave_type(db, annual_quota_days=3.0), _employee(db)
    balance_service.reserve(db, emp, 2026, lt, 3.0)

    with pytest.raises(HTTPException):
        balance_service.check_enough(db, emp, 2026, lt, 2.0)
    #  Bỏ phần giữ chỗ của CHÍNH tờ đơn đang sửa ra thì phải qua.
    balance_service.check_enough(db, emp, 2026, lt, 2.0, exclude_days=3.0)
