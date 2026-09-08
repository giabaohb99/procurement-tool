"""NGÀY VÀO LÀM + GIỚI TÍNH của hồ sơ nhân sự (vá 07/09/2026).

⚠️ Hai cột này có trong `tab_employee` từ 03/09/2026 (QĐ-NP3) nhưng **không nằm
trong schema nào**, nên API không nhận cũng không trả — và không màn hình nào
khai được. Hậu quả im lặng, cả hai luật nghỉ phép dựa vào chúng đều không chạy:

* `hire_date` rỗng ⇒ `balance_service` tính THÂM NIÊN bằng 0 năm cho **mọi**
  người, tức cả công ty mất phần ngày phép cộng thêm mà không ai báo;
* `gender` luôn `0` ⇒ `check_gender` coi là *"chưa khai"* và **không chặn loại
  nghỉ nào**, nên chốt "Thai sản chỉ áp cho nữ" coi như không tồn tại.

Bài ở đây chốt cả đường vào (nhận, kiểm) lẫn đường ra (trả), và chốt luôn cái
bẫy `NULL` — thứ làm đỏ hai bài B-03 ngay lần chạy đầu.
"""
from datetime import date

import pytest
from pydantic import ValidationError

from app.modules.employee.model import Employee
from app.modules.employee.schema import (EmployeeCreate, EmployeeOut,
                                         EmployeeUpdate)
from app.modules.leave import balance_service


# ── 1. Đường VÀO ───────────────────────────────────────────────────────────────

def test_nhan_ngay_vao_lam_khi_tao_moi():
    payload = EmployeeCreate(full_name="Nguyễn Văn A", hire_date=date(2018, 3, 1))
    assert payload.hire_date == date(2018, 3, 1)


def test_bo_trong_ngay_vao_lam_van_tao_duoc():
    """Hồ sơ cũ chưa ai nhập — bắt buộc thì cả công ty không sửa nổi hồ sơ cho
    tới khi tra ra ngày vào làm của từng người (D-018)."""
    assert EmployeeCreate(full_name="Nguyễn Văn A").hire_date is None


def test_sua_rieng_ngay_vao_lam_khong_dung_toi_o_khac():
    """PATCH chỉ gửi một ô — `exclude_unset` phải thấy đúng một khóa."""
    data = EmployeeUpdate(hire_date=date(2020, 1, 15))
    assert data.model_dump(exclude_unset=True) == {"hire_date": date(2020, 1, 15)}


def test_gui_null_TUONG_MINH_la_lenh_XOA_ngay_vao_lam():
    """Khác hẳn "không gửi": nhập nhầm năm rồi muốn xóa trắng thì phải làm được."""
    data = EmployeeUpdate(hire_date=None)
    assert data.model_dump(exclude_unset=True) == {"hire_date": None}


@pytest.mark.parametrize("value", [0, 1, 2])
def test_gioi_tinh_nhan_du_ba_gia_tri(value):
    assert EmployeeCreate(full_name="A", gender=value).gender == value


@pytest.mark.parametrize("value", [3, -1, 99])
def test_gioi_tinh_LA_bi_chan(value):
    """Giá trị lạ thì `check_gender` của nghỉ phép so `want != got` ra True và
    chặn nhầm loại nghỉ, mà không chỗ nào giải thích được vì sao."""
    with pytest.raises(ValidationError):
        EmployeeCreate(full_name="A", gender=value)
    with pytest.raises(ValidationError):
        EmployeeUpdate(gender=value)


# ── 2. Đường RA ────────────────────────────────────────────────────────────────

def test_tra_ve_ca_hai_o_de_man_hinh_hien_lai_duoc(db):
    emp = Employee(code="NV001", full_name="Nguyễn Văn A",
                   hire_date=date(2018, 3, 1), gender=2)
    db.add(emp)
    db.flush()

    out = EmployeeOut.model_validate(emp)
    assert out.hire_date == date(2018, 3, 1)
    assert out.gender == 2


def test_cot_gioi_tinh_NULL_doc_thanh_chua_khai_chu_khong_no(db):
    """⚠️ Bẫy đã làm đỏ hai bài B-03 ngay lần chạy đầu.

    Cột khai `default=0` nhưng đó là mặc định lúc INSERT: bản ghi dựng trong bộ
    nhớ mà chưa flush vẫn mang `None`, và dòng cũ có trước cột này cũng có thể
    `NULL`. Ném ở tầng đọc thì **cả màn danh sách nhân sự trả 500** vì một ô
    chưa ai nhập.
    """
    emp = Employee(code="NV002", full_name="Nguyễn Văn B")
    db.add(emp)
    db.flush()
    #  Dòng cũ có trước cột này: cột tồn tại nhưng ô rỗng.
    emp.gender = None

    assert EmployeeOut.model_validate(emp).gender == 0


# ── 3. Nối vào THÂM NIÊN — lý do tồn tại của ô ngày vào làm ────────────────────

def test_ngay_vao_lam_dieu_khien_so_nam_tham_nien():
    """Nhập được ngày vào làm thì thâm niên mới khác 0 — đó là cả điểm của đợt này."""
    assert balance_service.seniority_years(None, date(2026, 1, 1)) == 0
    assert balance_service.seniority_years(date(2018, 3, 1), date(2026, 1, 1)) == 7
    #  Chưa tới ngày kỷ niệm trong năm thì chưa đủ năm đó.
    assert balance_service.seniority_years(date(2018, 3, 1), date(2026, 3, 1)) == 8
    assert balance_service.seniority_years(date(2018, 3, 2), date(2026, 3, 1)) == 7
