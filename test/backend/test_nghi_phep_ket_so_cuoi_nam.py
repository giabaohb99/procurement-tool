"""KẾT SỔ CUỐI NĂM (07/09/2026) — số dư đi đâu, và bao giờ thì nó mất.

Ba ô «Cho chuyển phép sang năm sau · Chuyển tối đa · Hết hạn cuối tháng» trước
đợt này là **cột chết**: lưu được, hiện được, không chỗ nào đọc. Bộ bài này là
thứ chặn chúng chết lại lần nữa — bỏ một bài ở đây là ba ô kia lại thành lời hứa
suông trên giao diện.

Chỗ dễ sai nhất và vì sao có bài riêng cho từng chỗ:
  · chạy hai lần phải KHÔNG nhân đôi số ngày (dấu `carried_out_days`);
  · số dư năm cũ phải TỤT đúng phần đã mang đi, nếu không cộng hai năm lại là
    công ty thấy mình nợ gấp đôi số ngày phép thật;
  · quy đổi phải nhân tỷ lệ và rơi vào ĐÚNG loại đích;
  · phần mang sang quá hạn phải mất, và mất theo luật "tiêu phần mang sang
    trước" — chọn nhầm phía là người lao động mất oan ngày phép.
"""
from datetime import date

import pytest

from app.modules.employee.model import Employee
from app.modules.leave import balance_service, carryover_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (YEAR_END_CARRY, YEAR_END_CONVERT,
                                         YEAR_END_DROP)


# ── Dựng dữ liệu ────────────────────────────────────────────────────────────────

def _leave_type(db, code="annual", name="Phép năm", **kw):
    kw.setdefault("counts_balance", True)
    kw.setdefault("annual_quota_days", 12.0)
    kw.setdefault("year_end_mode", YEAR_END_DROP)
    obj = LeaveType(code=code, name=name, **kw)
    db.add(obj)
    db.flush()
    return obj


def _employee(db, code="NV001"):
    obj = Employee(code=code, full_name="Nguyễn Văn A", company_id=1,
                   hire_date=date(2020, 1, 1))
    db.add(obj)
    db.flush()
    return obj


def _balance(db, employee, leave_type, year=2026, **kw):
    kw.setdefault("allocated_days", 12.0)
    obj = LeaveBalance(employee_id=employee.id, year=year,
                       leave_type_id=leave_type.id, company_id=1, **kw)
    db.add(obj)
    db.flush()
    return obj


def _close(db, year=2026):
    rows = db.query(LeaveBalance).filter(LeaveBalance.year == year).all()
    return carryover_service.close_year(db, year, rows, actor=1)


def _next_year_row(db, employee, leave_type, year=2027):
    return balance_service.get_balance(db, employee.id, year, leave_type.id)


# ── 1. Mang sang năm sau ────────────────────────────────────────────────────────

def test_mang_so_du_sang_nam_sau(db):
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY)
    nv = _employee(db)
    _balance(db, nv, lt, used_days=4.0)  # còn 8

    result = _close(db)

    assert result["moved_days"] == 8.0
    assert _next_year_row(db, nv, lt).carried_days == 8.0


def test_so_du_nam_cu_TUT_dung_phan_da_mang_di(db):
    """Không trừ bên năm cũ thì cộng hai năm lại ra gấp đôi số ngày phép thật."""
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY)
    nv = _employee(db)
    row = _balance(db, nv, lt, used_days=4.0)

    _close(db)

    assert row.carried_out_days == 8.0
    assert row.remaining_days == 0.0


def test_khong_khai_luat_thi_KHONG_dung_toi(db):
    """Mặc định «Hết năm là mất» — kết sổ không được tự ý mang phép của loại đó."""
    lt = _leave_type(db)  # YEAR_END_DROP
    nv = _employee(db)
    row = _balance(db, nv, lt, used_days=4.0)

    result = _close(db)

    assert result["moved_rows"] == 0
    assert row.carried_out_days == 0.0
    assert _next_year_row(db, nv, lt) is None


def test_tran_mang_di_kep_so_ngay(db):
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY, carry_over_max_days=5.0)
    nv = _employee(db)
    row = _balance(db, nv, lt)  # còn nguyên 12

    _close(db)

    assert row.carried_out_days == 5.0
    #  Phần vượt trần thì MẤT, không treo lại: 12 − 5 = 7 vẫn nằm ở năm cũ và
    #  năm cũ thì không ai tiêu được nữa.
    assert _next_year_row(db, nv, lt).carried_days == 5.0


def test_chay_hai_lan_KHONG_nhan_doi(db):
    """Nút bấm tay thì kiểu gì cũng có người bấm hai lần."""
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY)
    nv = _employee(db)
    _balance(db, nv, lt, used_days=4.0)

    _close(db)
    second = _close(db)

    assert second["moved_rows"] == 0
    assert _next_year_row(db, nv, lt).carried_days == 8.0


def test_ngay_QUAY_LAI_sau_khi_ket_so_thi_luot_sau_vet_not(db):
    """Đơn năm cũ bị từ chối / bị hủy SAU khi đã kết sổ — chuyện thường.

    Bản đầu bỏ qua hẳn dòng đã kết sổ, nên mấy ngày quay lại kẹt vĩnh viễn ở
    năm cũ: năm cũ không ai tiêu được nữa, năm mới thì không thấy chúng. Người
    lao động mất ngày phép vì một thao tác hành chính họ không hề biết.
    """
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY)
    nv = _employee(db)
    row = _balance(db, nv, lt, pending_days=2.0)   # 2 ngày đang chờ duyệt

    first = _close(db)
    assert first["moved_days"] == 10.0
    assert _next_year_row(db, nv, lt).carried_days == 10.0

    #  Đơn bị từ chối → trả lại phần giữ chỗ.
    row.pending_days = 0.0
    db.flush()
    second = _close(db)

    assert second["moved_days"] == 2.0
    assert _next_year_row(db, nv, lt).carried_days == 12.0
    assert (row.carried_out_days, row.remaining_days) == (12.0, 0.0)


def test_TRAN_tinh_tren_TONG_da_mang_di_chu_khong_tung_luot(db):
    """Không thì chạy lại đủ số lần là vượt trần — mỗi lượt lại được thêm 5 ngày."""
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY, carry_over_max_days=5.0)
    nv = _employee(db)
    row = _balance(db, nv, lt, pending_days=4.0)   # còn 8, trần 5

    assert _close(db)["moved_days"] == 5.0
    row.pending_days = 0.0                          # 4 ngày quay lại
    db.flush()

    assert _close(db)["moved_days"] == 0.0
    assert row.carried_out_days == 5.0
    assert _next_year_row(db, nv, lt).carried_days == 5.0


def test_het_phep_thi_khong_co_gi_de_mang(db):
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY)
    nv = _employee(db)
    row = _balance(db, nv, lt, used_days=12.0)

    result = _close(db)

    assert result["moved_rows"] == 0
    assert row.carried_out_days == 0.0


def test_phan_dang_CHO_DUYET_khong_duoc_mang_di(db):
    """Ngày đang giữ chỗ có thể sắp thành ngày đã nghỉ — mang đi là cấp hai lần."""
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY)
    nv = _employee(db)
    _balance(db, nv, lt, used_days=4.0, pending_days=3.0)  # còn 5

    result = _close(db)

    assert result["moved_days"] == 5.0


# ── 2. Quy đổi sang loại khác ───────────────────────────────────────────────────

def test_quy_doi_sang_loai_khac_theo_ty_le(db):
    bu = _leave_type(db, code="comp_off", name="Nghỉ bù", annual_quota_days=0.0)
    lt = _leave_type(db, year_end_mode=YEAR_END_CONVERT,
                     convert_to_type_id=bu.id, convert_ratio=0.5)
    nv = _employee(db)
    row = _balance(db, nv, lt, used_days=4.0)  # còn 8

    result = _close(db)

    #  Mang đi 8 ngày phép năm, nhận 4 ngày nghỉ bù — hai con số KHÁC nhau và
    #  cả hai đều phải trả ra, nếu không màn hình chỉ nói được một nửa câu.
    assert (result["moved_days"], result["credited_days"]) == (8.0, 4.0)
    assert row.carried_out_days == 8.0
    assert _next_year_row(db, nv, bu).carried_days == 4.0
    assert _next_year_row(db, nv, lt) is None


def test_loai_dich_KHONG_tru_quy_thi_bo_qua_chu_khong_doan(db):
    """Quy đổi vào loại không trừ quỹ = số ngày rơi vào chỗ không ai đọc."""
    khong_luong = _leave_type(db, code="unpaid", name="Nghỉ không lương",
                              counts_balance=False, annual_quota_days=0.0)
    lt = _leave_type(db, year_end_mode=YEAR_END_CONVERT,
                     convert_to_type_id=khong_luong.id)
    nv = _employee(db)
    row = _balance(db, nv, lt, used_days=4.0)

    result = _close(db)

    assert result["skipped_config"] == 1
    #  Không đụng gì tới sổ: bỏ qua phải là KHÔNG LÀM GÌ, không phải "trừ bên
    #  này rồi quên cộng bên kia".
    assert row.carried_out_days == 0.0


def test_loai_dich_khong_ton_tai_thi_bo_qua(db):
    lt = _leave_type(db, year_end_mode=YEAR_END_CONVERT, convert_to_type_id=999)
    nv = _employee(db)
    row = _balance(db, nv, lt, used_days=4.0)

    result = _close(db)

    assert result["skipped_config"] == 1
    assert row.carried_out_days == 0.0


def test_ty_le_bang_khong_thi_bo_qua_chu_khong_TRU_TRANG(db):
    """Tỷ lệ 0 nghĩa là đổi ra 0 ngày — trừ bên nguồn là xóa trắng phép của người ta."""
    bu = _leave_type(db, code="comp_off", name="Nghỉ bù", annual_quota_days=0.0)
    lt = _leave_type(db, year_end_mode=YEAR_END_CONVERT,
                     convert_to_type_id=bu.id, convert_ratio=0.0)
    nv = _employee(db)
    row = _balance(db, nv, lt, used_days=4.0)

    result = _close(db)

    assert result["skipped_config"] == 1
    assert row.carried_out_days == 0.0


# ── 3. Hết hạn phần mang sang ───────────────────────────────────────────────────

def test_phan_mang_sang_chua_dung_thi_MAT_sau_han(db):
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY, carry_over_expire_month=3)
    nv = _employee(db)
    row = _balance(db, nv, lt, year=2027, carried_days=5.0)

    lost = carryover_service.expire_carried(row, lt, date(2027, 4, 1))

    assert lost == 5.0
    assert (row.carried_days, row.carried_expired_days) == (0.0, 5.0)


def test_truoc_han_thi_KHONG_dung_toi(db):
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY, carry_over_expire_month=3)
    nv = _employee(db)
    row = _balance(db, nv, lt, year=2027, carried_days=5.0)

    #  Đúng NGÀY CUỐI vẫn còn dùng được — lệch một ngày ở đây là mọi người dùng
    #  nốt ngày phép chuyển vào 31/03 đều mất trắng.
    assert carryover_service.expire_carried(row, lt, date(2027, 3, 31)) == 0.0
    assert row.carried_days == 5.0


def test_phan_MANG_SANG_duoc_coi_la_tieu_truoc(db):
    """Sổ chỉ có một cục `used_days`; chọn phía có lợi cho người lao động."""
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY, carry_over_expire_month=3)
    nv = _employee(db)
    row = _balance(db, nv, lt, year=2027, carried_days=5.0, used_days=3.0)

    lost = carryover_service.expire_carried(row, lt, date(2027, 4, 1))

    assert lost == 2.0
    assert row.carried_days == 3.0


def test_khai_khong_het_han_thi_giu_mai(db):
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY, carry_over_expire_month=0)
    nv = _employee(db)
    row = _balance(db, nv, lt, year=2027, carried_days=5.0)

    assert carryover_service.expire_carried(row, lt, date(2030, 1, 1)) == 0.0
    assert row.carried_days == 5.0


def test_thu_hoi_chay_lai_KHONG_mat_them_lan_hai(db):
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY, carry_over_expire_month=3)
    nv = _employee(db)
    row = _balance(db, nv, lt, year=2027, carried_days=5.0, used_days=3.0)

    carryover_service.expire_carried(row, lt, date(2027, 4, 1))
    lost_again = carryover_service.expire_carried(row, lt, date(2027, 5, 1))

    assert lost_again == 0.0
    assert (row.carried_days, row.carried_expired_days) == (3.0, 2.0)


def test_duong_CHAN_don_khong_tieu_duoc_phep_da_het_han(db):
    """`ensure_balance` là chỗ hẹp mọi đường chặn đi qua — thu hồi phải nằm ở đó.

    Không có nhịp này thì đơn nộp tháng Tư vẫn tiêu được phép đã hết hạn 31/03,
    và nó lọt ở dạng "cho nghỉ dư" nên không ai báo lỗi.
    """
    lt = _leave_type(db, year_end_mode=YEAR_END_CARRY, carry_over_expire_month=3,
                     annual_quota_days=0.0)
    nv = _employee(db)
    _balance(db, nv, lt, year=date.today().year, allocated_days=0.0, carried_days=5.0)

    #  `ensure_balance` gọi `expire_carried` với ngày HÔM NAY. Bài chạy sau
    #  tháng 3 nên phép mang sang đã quá hạn.
    row = balance_service.ensure_balance(db, nv, date.today().year, lt)

    if date.today() > date(date.today().year, 3, 31):
        assert row.remaining_days == 0.0
        with pytest.raises(Exception):
            balance_service.check_enough(db, nv, date.today().year, lt, 1.0)
    else:
        assert row.remaining_days == 5.0
