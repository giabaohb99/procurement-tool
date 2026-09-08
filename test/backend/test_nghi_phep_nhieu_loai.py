"""NHIỀU LOẠI NGHỈ TRONG MỘT ĐƠN (07/09/2026).

Một tờ đơn khai được *"nghỉ 05→08/01: 3 ngày phép năm + 1 ngày không lương"*.
Cả đơn dùng chung một khoảng ngày; dòng chỉ chia số ngày.

Bài nặng nhất ở đây là nhóm 3 — **sổ quỹ phải chạy theo TỪNG DÒNG**. Trừ tổng
vào loại chính là cộng ngày không lương vào quỹ phép năm, và lỗi đó không có
triệu chứng cho tới khi ai đó cộng tay lại sổ cuối năm.
"""
from datetime import date, time, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, balance_service, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (GENDER_FEMALE, LR_APPROVED, LR_PENDING,
                                         SESSION_HOURLY)
from app.modules.leave.request_model import LeaveRequestLine
from app.modules.leave.schema import (LeaveLineItem, LeaveRequestCreate,
                                      LeaveRequestUpdate)

#  Thứ Hai 05/01/2026 — tuần này không có ngày lễ nào, nên số ngày máy tính ra
#  không phụ thuộc bộ lịch (lịch lễ có bài riêng).
MONDAY = date(2026, 1, 5)


# ── Dựng dữ liệu ────────────────────────────────────────────────────────────────

def _leave_type(db, code="annual", name="Phép năm", **kw):
    kw.setdefault("counts_balance", True)
    kw.setdefault("annual_quota_days", 12.0)
    obj = LeaveType(code=code, name=name, **kw)
    db.add(obj)
    db.flush()
    return obj


def _employee(db, code="NV001", name="Nguyễn Văn A", **kw):
    kw.setdefault("company_id", 1)
    kw.setdefault("department_id", 7)
    obj = Employee(code=code, full_name=name, **kw)
    db.add(obj)
    db.flush()
    return obj


def _user(employee_id: int, uid: int = 1):
    return SimpleNamespace(id=uid, employee_id=employee_id)


def _create(db, user, lines, days_to=3, **kw):
    """Đơn nhiều dòng. `lines` là danh sách `(loại nghỉ, số ngày)`."""
    payload = {
        "lines": [LeaveLineItem(leave_type_id=lt.id, days=d) for lt, d in lines],
        "from_date": MONDAY,
        "to_date": MONDAY + timedelta(days=days_to),
        "reason": "Về quê",
    }
    payload.update(kw)
    return request_service.create(db, LeaveRequestCreate(**payload), user)


def _lines(db, request_id):
    return {line.leave_type_id: line.days
            for line in request_service.lines_of(db, request_id)}


class _Instance:
    def __init__(self, actor: int = 1, reason: str = ""):
        self.updated_by = actor
        self.finish_reason = reason


@pytest.fixture
def two_types(db):
    """Hai loại nghỉ có SỔ QUỸ RIÊNG — đó là cả lý do bảng dòng tồn tại."""
    return (_leave_type(db),
            _leave_type(db, code="unpaid", name="Nghỉ không lương",
                        annual_quota_days=30.0))


# ── 1. Lập đơn nhiều dòng ───────────────────────────────────────────────────────

def test_don_hai_loai_luu_du_hai_dong(db, two_types):
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])
    assert _lines(db, obj.id) == {annual.id: 3.0, unpaid.id: 1.0}


def test_tong_so_ngay_la_TONG_CUA_CAC_DONG(db, two_types):
    """`total_days` là cột dẫn xuất — người dùng gõ vào dòng, máy cộng lại."""
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])
    assert obj.total_days == 4.0


def test_loai_chinh_la_dong_NHIEU_NGAY_NHAT(db, two_types):
    """Cột `leave_type_id` đầu đơn nuôi bộ lọc và điều kiện rẽ nhánh luồng duyệt."""
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 1), (unpaid, 3)])
    assert obj.leave_type_id == unpaid.id


def test_hoa_so_ngay_thi_lay_dong_DAU(db, two_types):
    """Phải có một luật rõ ràng, không để nó phụ thuộc thứ tự sắp xếp của SQL."""
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 2), (unpaid, 2)])
    assert obj.leave_type_id == annual.id


# ── 2. Bốn chốt trên danh sách dòng ─────────────────────────────────────────────

def test_khai_MOT_LOAI_HAI_LAN_bi_chan(db, two_types):
    """Hai dòng cùng loại là hai lượt trừ vào cùng một dòng quỹ — đọc sổ không hiểu."""
    annual, _ = two_types
    emp = _employee(db)
    with pytest.raises(HTTPException) as e:
        _create(db, _user(emp.id), [(annual, 2), (annual, 1)])
    assert "hai lần" in e.value.detail


def test_dong_KHONG_CO_SO_NGAY_bi_chan_khi_don_nhieu_dong(db, two_types):
    """Máy không đoán được chia 4 ngày thành 3+1 hay 2+2 — đoán sai là trừ nhầm quỹ."""
    annual, unpaid = two_types
    emp = _employee(db)
    with pytest.raises(HTTPException) as e:
        _create(db, _user(emp.id), [(annual, 3), (unpaid, 0)])
    assert "chưa có số ngày" in e.value.detail


def test_don_MOT_dong_de_trong_thi_may_van_tu_tinh(db, two_types):
    """Đơn một loại giữ nguyên hành vi cũ: để trống thì tính từ khoảng ngày."""
    annual, _ = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 0)], days_to=2)
    assert obj.total_days == 3.0
    assert _lines(db, obj.id) == {annual.id: 3.0}


def test_tong_ngay_VUOT_KHOANG_NGAY_bi_chan(db, two_types):
    """Trần đếm cả T7/CN/lễ nên không chặn nhầm ca hợp lệ, nhưng chặn được gõ nhầm.

    Trước đợt này `total_days` cho sửa đè tự do, nên gõ 30 ngày trên khoảng hai
    ngày là lọt thẳng vào sổ quỹ.
    """
    annual, unpaid = two_types
    emp = _employee(db)
    with pytest.raises(HTTPException) as e:
        _create(db, _user(emp.id), [(annual, 20), (unpaid, 10)], days_to=1)
    assert "nhiều hơn số ngày của khoảng" in e.value.detail


def test_qua_TRAN_SO_LOAI_bi_chan(db):
    """Quá `MAX_LINES` thì gần như chắc chắn là nhập nhầm."""
    emp = _employee(db)
    types = [_leave_type(db, code=f"lt{i}", name=f"Loại {i}")
             for i in range(request_service.MAX_LINES + 1)]
    with pytest.raises(HTTPException) as e:
        _create(db, _user(emp.id), [(lt, 1) for lt in types], days_to=30)
    assert "tối đa" in e.value.detail


def test_TRAN_MOI_LAN_xet_theo_TUNG_DONG(db, two_types):
    """Cưới hỏi trần 3 ngày thì dòng cưới hỏi 4 ngày bị chặn, dù tổng đơn hợp lệ."""
    annual, _ = two_types
    wedding = _leave_type(db, code="wedding", name="Cưới hỏi",
                          max_days_per_request=3.0, counts_balance=False)
    emp = _employee(db)
    with pytest.raises(HTTPException) as e:
        _create(db, _user(emp.id), [(annual, 1), (wedding, 4)], days_to=6)
    assert "Cưới hỏi" in e.value.detail


def test_GIOI_TINH_xet_theo_TUNG_DONG(db, two_types):
    """Thai sản nằm ở dòng phụ vẫn phải bị chặn với hồ sơ nam."""
    annual, _ = two_types
    maternity = _leave_type(db, code="maternity", name="Thai sản",
                            gender=GENDER_FEMALE, counts_balance=False)
    emp = _employee(db, gender=1)
    with pytest.raises(HTTPException) as e:
        _create(db, _user(emp.id), [(annual, 2), (maternity, 1)])
    assert "Thai sản" in e.value.detail


def test_theo_GIO_chi_khai_MOT_loai(db, two_types):
    """Nghỉ hai tiếng mà chia hai loại là ca chưa từng có, và nó phá phép quy đổi."""
    annual, unpaid = two_types
    emp = _employee(db)
    with pytest.raises(HTTPException) as e:
        _create(db, _user(emp.id), [(annual, 1), (unpaid, 1)], days_to=0,
                from_session=SESSION_HOURLY, to_session=SESSION_HOURLY,
                from_time=time(9, 0), to_time=time(11, 0))
    assert "một loại nghỉ" in e.value.detail


def test_khong_khai_loai_nao_bi_chan(db):
    emp = _employee(db)
    with pytest.raises(HTTPException) as e:
        request_service.create(db, LeaveRequestCreate(
            from_date=MONDAY, to_date=MONDAY, reason="x"), _user(emp.id))
    assert "Chưa chọn loại nghỉ" in e.value.detail


# ── 3. Sổ quỹ chạy THEO DÒNG ───────────────────────────────────────────────────

def _submit(db, obj, emp):
    user = _user(emp.id)
    employee = request_service.prepare_submit(db, obj, user)
    return request_service.mark_submitted(db, obj, employee, user)


def _pending(db, emp, leave_type):
    row = balance_service.get_balance(db, emp.id, MONDAY.year, leave_type.id)
    return row.pending_days if row else 0.0


def _used(db, emp, leave_type):
    row = balance_service.get_balance(db, emp.id, MONDAY.year, leave_type.id)
    return row.used_days if row else 0.0


def test_gui_duyet_giu_cho_DUNG_PHAN_cua_tung_loai(db, two_types):
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])
    _submit(db, obj, emp)
    assert (_pending(db, emp, annual), _pending(db, emp, unpaid)) == (3.0, 1.0)


def test_duyet_xong_tru_that_DUNG_PHAN_cua_tung_loai(db, two_types):
    """Trừ tổng vào loại chính là cộng ngày không lương vào quỹ phép năm."""
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])
    _submit(db, obj, emp)

    approval_bridge._on_approved(db, obj.id, _Instance())
    db.commit()

    assert (_used(db, emp, annual), _used(db, emp, unpaid)) == (3.0, 1.0)
    assert (_pending(db, emp, annual), _pending(db, emp, unpaid)) == (0.0, 0.0)
    assert obj.status == LR_APPROVED


@pytest.mark.parametrize("hook", ["_on_rejected", "_on_returned", "_on_withdrawn"])
def test_ba_ket_cuc_khong_duyet_tra_lai_CA_HAI_dong(db, two_types, hook):
    """Quên một dòng thì số ngày đó treo vĩnh viễn trong `pending_days`."""
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])
    _submit(db, obj, emp)

    getattr(approval_bridge, hook)(db, obj.id, _Instance())
    db.commit()

    assert (_pending(db, emp, annual), _pending(db, emp, unpaid)) == (0.0, 0.0)


def test_huy_don_DANG_CHO_tra_lai_ca_hai_dong(db, two_types):
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])
    _submit(db, obj, emp)

    request_service.cancel(db, obj, "Đổi ý", emp.id)

    assert (_pending(db, emp, annual), _pending(db, emp, unpaid)) == (0.0, 0.0)


def test_huy_don_DA_DUYET_hoan_lai_ca_hai_dong(db, two_types):
    """Người xin nghỉ tuần sau, tuần này đổi ý — không hoàn thì họ mất phép."""
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])
    _submit(db, obj, emp)
    approval_bridge._on_approved(db, obj.id, _Instance())
    db.commit()

    request_service.cancel(db, obj, "Đổi ý", emp.id)

    assert (_used(db, emp, annual), _used(db, emp, unpaid)) == (0.0, 0.0)


def test_HET_PHEP_o_MOT_dong_thi_ca_don_khong_gui_duoc(db, two_types):
    """Đủ phép kiểm theo từng loại: 3 ngày phép năm khi quỹ còn 2 là chặn."""
    annual, unpaid = two_types
    annual.annual_quota_days = 2.0
    db.flush()
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])
    with pytest.raises(HTTPException) as e:
        _submit(db, obj, emp)
    assert "Không đủ phép" in e.value.detail


def test_het_quy_LOAI_KHAC_khong_chan_don(db, two_types):
    """Quỹ phép năm cạn không cản đơn xin toàn ngày không lương."""
    annual, unpaid = two_types
    annual.annual_quota_days = 0.0
    db.flush()
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(unpaid, 2)], days_to=1)
    _submit(db, obj, emp)
    assert obj.status == LR_PENDING


# ── 4. Sửa đơn ─────────────────────────────────────────────────────────────────

def test_gui_lines_thi_GHI_DE_ca_danh_sach(db, two_types):
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])

    request_service.update(db, obj, LeaveRequestUpdate(
        lines=[LeaveLineItem(leave_type_id=unpaid.id, days=2)]), _user(emp.id))

    assert _lines(db, obj.id) == {unpaid.id: 2.0}
    assert (obj.total_days, obj.leave_type_id) == (2.0, unpaid.id)


def test_KHONG_gui_lines_thi_giu_nguyen_phan_bo(db, two_types):
    """Máy không có cách nào chia lại hộ — im lặng chia lại là sửa vào quỹ người ta."""
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])

    request_service.update(db, obj, LeaveRequestUpdate(reason="Lý do khác"),
                           _user(emp.id))

    assert _lines(db, obj.id) == {annual.id: 3.0, unpaid.id: 1.0}
    assert obj.total_days == 4.0


def test_doi_ngay_tren_don_MOT_dong_thi_tinh_lai_so_ngay(db, two_types):
    """Hành vi cũ phải còn nguyên: sửa ngày mà giữ số ngày cũ là sai ngay lập tức."""
    annual, _ = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 0)], days_to=1)
    assert obj.total_days == 2.0

    request_service.update(db, obj, LeaveRequestUpdate(
        to_date=MONDAY + timedelta(days=3)), _user(emp.id))

    assert obj.total_days == 4.0
    assert _lines(db, obj.id) == {annual.id: 4.0}


def test_sua_bang_leave_type_id_cu_van_chay(db, two_types):
    """Đường gọi cũ (một loại, không biết tới `lines`) không được gãy."""
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 0)], days_to=1)

    request_service.update(db, obj, LeaveRequestUpdate(leave_type_id=unpaid.id),
                           _user(emp.id))

    assert _lines(db, obj.id) == {unpaid.id: 2.0}


def test_xoa_het_dong_cu_khong_de_lai_rac(db, two_types):
    """Ghi đè là XÓA rồi thêm — sót dòng cũ thì quỹ bị trừ cho một loại đã bỏ."""
    annual, unpaid = two_types
    emp = _employee(db)
    obj = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])

    request_service.update(db, obj, LeaveRequestUpdate(
        lines=[LeaveLineItem(leave_type_id=annual.id, days=1)]), _user(emp.id))

    assert db.query(LeaveRequestLine).filter(
        LeaveRequestLine.request_id == obj.id).count() == 1


# ── 5. Đường tương thích ngược ─────────────────────────────────────────────────

def test_khong_gui_lines_thi_dung_cap_cot_cu(db, two_types):
    """Gói tri thức Trợ lý AI và kịch bản seed vẫn gửi `leave_type_id` + `total_days`."""
    annual, _ = two_types
    emp = _employee(db)
    obj = request_service.create(db, LeaveRequestCreate(
        leave_type_id=annual.id, from_date=MONDAY,
        to_date=MONDAY + timedelta(days=2), total_days=2.5,
        reason="Về quê"), _user(emp.id))

    assert obj.total_days == 2.5
    assert _lines(db, obj.id) == {annual.id: 2.5}


def test_giay_GNP_chi_mang_ban_ke_khi_don_NHIEU_loai(db, two_types):
    """Đơn một loại thì ô `leave_type` đã nói đủ — thêm danh sách một phần tử là
    bắt mọi chỗ đọc giấy xử lý hai hình dạng cho cùng một thứ."""
    annual, unpaid = two_types
    emp = _employee(db)

    mot_loai = _create(db, _user(emp.id), [(annual, 2)], days_to=1)
    assert approval_bridge._document_lines(db, mot_loai) == [
        {"leave_type": "annual", "name": "Phép năm", "days": 2.0}]

    nhieu_loai = _create(db, _user(emp.id), [(annual, 3), (unpaid, 1)])
    assert [line["leave_type"] for line in
            approval_bridge._document_lines(db, nhieu_loai)] == ["annual", "unpaid"]
