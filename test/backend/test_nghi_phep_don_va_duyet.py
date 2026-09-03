"""P-04 + P-05 (CR-259) — vòng đời đơn nghỉ phép và bốn kết cục của bộ máy duyệt.

Bài quan trọng nhất ở đây là nhóm 3: **ba kết cục KHÔNG duyệt đều phải trả lại
phần giữ chỗ**. Quên một cái thì số ngày đó treo vĩnh viễn trong `pending_days`,
người ta mất phép, và lỗi không có triệu chứng nào cho tới khi ai đó cộng tay
lại sổ cuối năm.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, balance_service, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (GENDER_FEMALE, GENDER_MALE, LR_APPROVED,
                                         LR_CANCELLED, LR_DRAFT, LR_PENDING,
                                         LR_REJECTED, LR_RETURNED)
from app.modules.leave.request_model import LeaveHandover, LeaveRequest
from app.modules.leave.schema import (HandoverItem, LeaveRequestCreate,
                                      LeaveRequestUpdate)

#  Thứ Hai 05/01/2026 — mọi ngày dùng trong bộ này đều là ngày làm việc, để số
#  ngày tính ra không phụ thuộc vào lịch lễ (bộ lịch có bài riêng ở tệp kia).
MONDAY = date(2026, 1, 5)


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


def _employee(db, code="NV001", name="Nguyễn Văn A", **kw):
    kw.setdefault("company_id", 1)
    kw.setdefault("department_id", 7)
    obj = Employee(code=code, full_name=name, **kw)
    db.add(obj)
    db.flush()
    return obj


def _user(employee_id: int, uid: int = 1):
    """Người thao tác giả lập — service chỉ đọc `id` và `employee_id`."""
    return SimpleNamespace(id=uid, employee_id=employee_id)


def _create(db, user, leave_type, days_from=0, days_to=0, **kw):
    payload = {
        "leave_type_id": leave_type.id,
        "from_date": MONDAY + timedelta(days=days_from),
        "to_date": MONDAY + timedelta(days=days_to),
        "reason": "Về quê",
    }
    payload.update(kw)
    return request_service.create(db, LeaveRequestCreate(**payload), user)


class _Instance:
    """Phiên duyệt giả — hook chỉ đọc hai thuộc tính này."""

    def __init__(self, actor: int = 1, reason: str = ""):
        self.updated_by = actor
        self.finish_reason = reason


# ── 1. Lập đơn ──────────────────────────────────────────────────────────────────

def test_lap_don_luon_o_trang_thai_nhap(db):
    """Gửi duyệt là một bước RIÊNG. Lập xong tự vào luồng là mất đường lưu nháp."""
    emp = _employee(db)
    obj = _create(db, _user(emp.id), _leave_type(db))
    assert obj.status == LR_DRAFT
    assert obj.code.startswith("NP")


def test_tu_tinh_so_ngay_khi_khong_nhap(db):
    """T2 → T4 = 3 ngày công."""
    emp = _employee(db)
    obj = _create(db, _user(emp.id), _leave_type(db), days_to=2)
    assert obj.total_days == 3.0


def test_nguoi_dung_sua_de_so_ngay_thi_ton_trong(db):
    """Lịch làm việc thật luôn có ngoại lệ máy không biết — ô này sửa đè được."""
    emp = _employee(db)
    obj = _create(db, _user(emp.id), _leave_type(db), days_to=2, total_days=1.5)
    assert obj.total_days == 1.5


def test_chep_phap_nhan_va_phong_cua_NGUOI_NGHI(db):
    """Chép chứ không JOIN: người chuyển phòng giữa năm thì đơn cũ ở lại phòng cũ."""
    emp = _employee(db, company_id=3, department_id=9)
    obj = _create(db, _user(emp.id), _leave_type(db))
    assert (obj.company_id, obj.department_id) == (3, 9)


def test_lap_ho_nguoi_khac(db):
    """Hành chính lập hộ là việc có thật — người nghỉ khai tường minh."""
    hanh_chinh = _employee(db, code="NV009", name="Trần Hành Chính")
    nguoi_nghi = _employee(db, code="NV002", name="Lê Thị B")
    obj = _create(db, _user(hanh_chinh.id, uid=9), _leave_type(db),
                  employee_id=nguoi_nghi.id)
    assert obj.employee_id == nguoi_nghi.id
    assert obj.created_by == 9


def test_tai_khoan_khong_gan_ho_so_nhan_su_bi_chan(db):
    with pytest.raises(HTTPException) as e:
        _create(db, _user(0), _leave_type(db))
    assert "chưa gắn hồ sơ nhân sự" in e.value.detail


def test_khoang_ngay_nguoc_bi_chan(db):
    emp = _employee(db)
    with pytest.raises(HTTPException):
        _create(db, _user(emp.id), _leave_type(db), days_from=3, days_to=0)


def test_loai_nghi_gioi_han_gioi_tinh(db):
    """Thai sản không áp cho hồ sơ nam."""
    thai_san = _leave_type(db, code="maternity", name="Nghỉ thai sản",
                           counts_balance=False, gender=GENDER_FEMALE)
    nam = _employee(db, gender=GENDER_MALE)
    with pytest.raises(HTTPException) as e:
        _create(db, _user(nam.id), thai_san)
    assert "không áp dụng" in e.value.detail


def test_chua_khai_gioi_tinh_thi_khong_bi_chan(db):
    """Chặn người chưa khai là khóa cả công ty tới khi Nhân sự nhập bù."""
    thai_san = _leave_type(db, code="maternity", name="Nghỉ thai sản",
                           counts_balance=False, gender=GENDER_FEMALE)
    chua_khai = _employee(db)   # gender mặc định 0
    assert _create(db, _user(chua_khai.id), thai_san).id


def test_tran_so_ngay_moi_lan(db):
    """Cưới hỏi 3 ngày — luật cứng, không cần lập quỹ riêng."""
    cuoi = _leave_type(db, code="wedding", name="Nghỉ cưới hỏi",
                       counts_balance=False, max_days_per_request=3.0)
    emp = _employee(db)
    with pytest.raises(HTTPException) as e:
        _create(db, _user(emp.id), cuoi, days_to=6)
    assert "tối đa 3.0 ngày" in e.value.detail


def test_luu_danh_sach_ban_giao_nhieu_nguoi(db):
    """Nghỉ dài thì bàn giao cho nhiều người — giấy GNP cũ chỉ có MỘT ô."""
    emp = _employee(db)
    a, b = _employee(db, code="NV003"), _employee(db, code="NV004")
    obj = _create(db, _user(emp.id), _leave_type(db),
                  handovers=[HandoverItem(employee_id=a.id, content="Đơn hàng"),
                             HandoverItem(employee_id=b.id, content="Kho")])
    rows = db.query(LeaveHandover).filter(LeaveHandover.request_id == obj.id).all()
    assert {r.employee_id for r in rows} == {a.id, b.id}


# ── 2. Sửa đơn ──────────────────────────────────────────────────────────────────

def test_sua_ngay_thi_tinh_lai_so_ngay(db):
    """Giữ nguyên số ngày cũ sau khi đổi ngày là sai ngay lập tức."""
    emp = _employee(db)
    obj = _create(db, _user(emp.id), _leave_type(db))
    assert obj.total_days == 1.0

    obj = request_service.update(
        db, obj, LeaveRequestUpdate(to_date=MONDAY + timedelta(days=2)), _user(emp.id))
    assert obj.total_days == 3.0


def test_khong_sua_duoc_don_da_gui_duyet(db):
    emp = _employee(db)
    lt = _leave_type(db)
    obj = _create(db, _user(emp.id), lt)
    employee, leave_type = request_service.prepare_submit(db, obj, _user(emp.id))
    request_service.mark_submitted(db, obj, employee, leave_type, _user(emp.id))

    with pytest.raises(HTTPException) as e:
        request_service.update(db, obj, LeaveRequestUpdate(reason="Khác"), _user(emp.id))
    assert "không sửa được" in e.value.detail


def test_ghi_de_danh_sach_ban_giao(db):
    emp = _employee(db)
    a, b = _employee(db, code="NV003"), _employee(db, code="NV004")
    obj = _create(db, _user(emp.id), _leave_type(db),
                  handovers=[HandoverItem(employee_id=a.id)])

    request_service.update(db, obj,
                           LeaveRequestUpdate(handovers=[HandoverItem(employee_id=b.id)]),
                           _user(emp.id))
    rows = db.query(LeaveHandover).filter(LeaveHandover.request_id == obj.id).all()
    assert [r.employee_id for r in rows] == [b.id]


# ── 3. Gửi duyệt và bốn kết cục ────────────────────────────────────────────────

def _submit(db, obj, user):
    employee, leave_type = request_service.prepare_submit(db, obj, user)
    return request_service.mark_submitted(db, obj, employee, leave_type, user)


def test_gui_duyet_giu_cho_quy_ngay_lap_tuc(db):
    """Không giữ chỗ thì nộp mười đơn liền tay đều lọt — xem `HOLDING_STATUSES`."""
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt, days_to=2), _user(emp.id))

    assert obj.status == LR_PENDING
    assert obj.submitted_at is not None
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 9.0


def test_gui_duyet_thieu_ly_do_bi_chan(db):
    """Chốt «nhập đủ» đặt ở lúc GỬI, không phải lúc lưu nháp."""
    emp = _employee(db)
    obj = _create(db, _user(emp.id), _leave_type(db), reason="")
    assert obj.id   # lưu nháp vẫn được
    with pytest.raises(HTTPException) as e:
        request_service.prepare_submit(db, obj, _user(emp.id))
    assert "Lý do nghỉ" in e.value.detail


def test_gui_duyet_vuot_quy_bi_chan(db):
    emp, lt = _employee(db), _leave_type(db, annual_quota_days=1.0)
    obj = _create(db, _user(emp.id), lt, days_to=4)
    with pytest.raises(HTTPException) as e:
        request_service.prepare_submit(db, obj, _user(emp.id))
    assert "Không đủ phép" in e.value.detail


def test_hai_don_chong_ngay_bi_chan(db):
    """Chồng ngày = trừ phép hai lần cho cùng một ngày."""
    emp, lt = _employee(db), _leave_type(db)
    _submit(db, _create(db, _user(emp.id), lt, days_to=2), _user(emp.id))

    obj2 = _create(db, _user(emp.id), lt, days_from=1, days_to=3)
    with pytest.raises(HTTPException) as e:
        request_service.prepare_submit(db, obj2, _user(emp.id))
    assert "trùng khoảng ngày" in e.value.detail


def test_don_nhap_khong_tinh_la_chong_ngay(db):
    """Chỉ đơn còn GIỮ CHỖ mới chặn — nháp thì chưa ăn vào quỹ."""
    emp, lt = _employee(db), _leave_type(db)
    _create(db, _user(emp.id), lt, days_to=2)          # để nguyên nháp
    obj2 = _create(db, _user(emp.id), lt, days_from=1, days_to=3)
    request_service.prepare_submit(db, obj2, _user(emp.id))   # không ném


def test_phai_nop_truoc_n_ngay(db):
    """`min_notice_days` so với HÔM NAY, không với ngày lập đơn."""
    emp = _employee(db)
    lt = _leave_type(db, min_notice_days=30)
    obj = _create(db, _user(emp.id), lt)
    obj.from_date = date.today() + timedelta(days=1)
    obj.to_date = obj.from_date
    db.flush()

    with pytest.raises(HTTPException) as e:
        request_service.prepare_submit(db, obj, _user(emp.id))
    assert "trước ít nhất 30 ngày" in e.value.detail


def test_duyet_chuyen_giu_cho_sang_da_dung(db):
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt, days_to=2), _user(emp.id))

    approval_bridge._on_approved(db, obj.id, _Instance())
    db.commit()
    db.refresh(obj)

    assert obj.status == LR_APPROVED
    assert obj.decided_at is not None
    row = balance_service.get_balance(db, emp.id, 2026, lt.id)
    assert (row.pending_days, row.used_days) == (0.0, 3.0)


@pytest.mark.parametrize("hook,expect_status", [
    ("_on_rejected", LR_REJECTED),
    ("_on_returned", LR_RETURNED),
    ("_on_withdrawn", LR_DRAFT),
])
def test_ba_ket_cuc_khong_duyet_deu_tra_lai_giu_cho(db, hook, expect_status):
    """Bài quan trọng nhất của tệp này — xem docstring đầu tệp."""
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt, days_to=2), _user(emp.id))
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 9.0

    getattr(approval_bridge, hook)(db, obj.id, _Instance(reason="Không hợp lý"))
    db.commit()
    db.refresh(obj)

    assert obj.status == expect_status
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 12.0


def test_tra_ve_thi_sua_va_gui_lai_duoc(db):
    """Khác «từ chối» đúng ở chỗ này — và phải khác."""
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt), _user(emp.id))
    approval_bridge._on_returned(db, obj.id, _Instance())
    db.commit()
    db.refresh(obj)

    request_service.update(db, obj, LeaveRequestUpdate(reason="Đã bổ sung"),
                           _user(emp.id))
    assert _submit(db, obj, _user(emp.id)).status == LR_PENDING


def test_tu_choi_thi_khoa_khong_sua_duoc(db):
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt), _user(emp.id))
    approval_bridge._on_rejected(db, obj.id, _Instance())
    db.commit()
    db.refresh(obj)

    with pytest.raises(HTTPException):
        request_service.update(db, obj, LeaveRequestUpdate(reason="Khác"), _user(emp.id))


def test_hook_khong_chay_hai_lan(db):
    """Bộ máy gọi lại (bấm đúp, gọi lại sau lỗi) không được trừ quỹ lần thứ hai."""
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt, days_to=2), _user(emp.id))

    approval_bridge._on_approved(db, obj.id, _Instance())
    approval_bridge._on_approved(db, obj.id, _Instance())
    db.commit()

    row = balance_service.get_balance(db, emp.id, 2026, lt.id)
    assert row.used_days == 3.0


# ── 4. Hủy đơn ──────────────────────────────────────────────────────────────────

def test_huy_don_cho_duyet_tra_lai_giu_cho(db):
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt, days_to=2), _user(emp.id))

    obj = request_service.cancel(db, obj, "Đổi kế hoạch", 1)
    assert obj.status == LR_CANCELLED
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 12.0


def test_huy_don_da_duyet_hoan_lai_ngay_da_tru(db):
    """Xin nghỉ tuần sau, tuần này đổi ý — không hoàn thì họ mất phép."""
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt, days_to=2), _user(emp.id))
    approval_bridge._on_approved(db, obj.id, _Instance())
    db.commit()
    db.refresh(obj)

    request_service.cancel(db, obj, "Đổi kế hoạch", 1)
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 12.0


def test_huy_hai_lan_khong_hoan_hai_lan(db):
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt, days_to=2), _user(emp.id))
    request_service.cancel(db, obj, "", 1)
    request_service.cancel(db, obj, "", 1)
    assert balance_service.remaining(db, emp.id, 2026, lt.id) == 12.0


def test_xoa_mem_chi_ap_cho_don_chua_vao_luong(db):
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt), _user(emp.id))
    with pytest.raises(HTTPException):
        request_service.soft_delete(db, obj, _user(emp.id))


# ── 5. Sinh giấy GNP (QĐ-NP5) ──────────────────────────────────────────────────

def test_khong_co_loai_van_ban_GNP_thi_bo_qua_im_lang(db):
    """Văn thư là phân hệ tùy chọn — bắt phải có nó mới nộp được đơn là buộc hai
    phân hệ vào nhau không cần thiết."""
    emp, lt = _employee(db), _leave_type(db)
    obj = _submit(db, _create(db, _user(emp.id), lt), _user(emp.id))

    approval_bridge._on_approved(db, obj.id, _Instance())
    db.commit()
    db.refresh(obj)

    assert obj.status == LR_APPROVED       # đơn vẫn duyệt xong
    assert obj.document_id == 0            # chỉ là không sinh giấy
