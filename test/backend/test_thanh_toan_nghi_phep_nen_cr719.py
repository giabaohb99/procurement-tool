"""duoc-CR-719 phase 01 — NỀN thanh toán nghỉ phép: công thức quỹ, chốt loại nghỉ, khóa quyền, chốt xem YCTT.

Không có đường API phiếu ở phase này; bài kiểm chạy thẳng hàm dùng chung (model, controller catalog, `apply_scope`,
`get_scoped`) như cách các endpoint đi.
"""
from datetime import date

import pytest
from fastapi import HTTPException

from app.core.permissions import ENTITIES
from app.core.scoping import SCOPE_FIELDS
from app.modules.employee.model import Employee
from app.modules.leave import balance_service
from app.modules.leave import catalog_controller as catalog
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (ENCASH_ACTIVE_STATUSES, ENCASH_EDITABLE_STATUSES,
                                         LEAVE_ENCASHMENT_REASON_LABELS, LEAVE_ENCASHMENT_STATUS_LABELS,
                                         LeaveAccrualMode, LeaveEncashmentReason, LeaveEncashmentStatus)
from app.modules.leave.encashment_model import LeaveEncashment
from app.modules.leave.schema import LeaveBalanceResponse, LeaveTypeCreate, LeaveTypeUpdate
from app.modules.payment_request.hr_payout_guard import PAYMENT_SOURCE_LEAVE_ENCASHMENT
from app.modules.payment_request.model import PaymentRequest

YEAR = 2026


# ── công thức quỹ ───────────────────────────────────────────────────────────────

def _balance(db, **kw):
    row = LeaveBalance(employee_id=1, year=YEAR, leave_type_id=1, company_id=1, **kw)
    db.add(row)
    db.flush()
    return row


def test_con_lai_tru_ngay_da_thanh_toan(db):
    row = _balance(db, allocated_days=12, seniority_days=1, used_days=3, pending_days=1,
                   carried_out_days=2, encashed_days=2.5)
    assert row.total_days == 13
    assert row.remaining_days == 13 - 3 - 1 - 2 - 2.5


def test_encashed_days_mac_dinh_0_va_none_khong_no(db):
    row = _balance(db, allocated_days=5)
    assert row.remaining_days == 5
    row.encashed_days = None          # dữ liệu cũ / chưa flush
    assert row.remaining_days == 5


def test_available_days_cong_don_van_dung_khi_co_thanh_toan(db):
    t = LeaveType(code="annual719", name="Phép năm", counts_balance=True, annual_quota_days=12,
                  accrual_mode=int(LeaveAccrualMode.MONTHLY), allow_encashment=True)
    db.add(t)
    db.add(Employee(code="E719", full_name="NV", company_id=1, department_id=1, is_active=True,
                    hire_date=date(2020, 1, 1)))
    db.flush()
    emp = db.query(Employee).filter(Employee.code == "E719").one()
    row = LeaveBalance(employee_id=emp.id, year=YEAR, leave_type_id=t.id, company_id=1, allocated_days=12)
    db.add(row)
    db.flush()
    today = date(2026, 6, 15)
    before = balance_service.available_days(db, row, today)
    assert 0 < before < 12            # mới tới tháng 6: phần chưa tới tháng bị giữ lại
    row.encashed_days = 2
    assert balance_service.available_days(db, row, today) == pytest.approx(before - 2)


def test_response_quy_tra_encashed_days(db):
    row = _balance(db, allocated_days=12, encashed_days=1.5)
    out = LeaveBalanceResponse.model_validate(row)
    assert out.encashed_days == 1.5


# ── bộ mã ───────────────────────────────────────────────────────────────────────

def test_bo_ma_phieu_cung_so_voi_phieu_nghi_bu():
    assert [int(s) for s in LeaveEncashmentStatus] == [1, 2, 3, 4, 5, 6]
    assert set(LEAVE_ENCASHMENT_STATUS_LABELS) == set(LeaveEncashmentStatus)
    assert set(LEAVE_ENCASHMENT_REASON_LABELS) == set(LeaveEncashmentReason)
    assert ENCASH_EDITABLE_STATUSES == (1, 5)
    assert ENCASH_ACTIVE_STATUSES == (1, 2, 3, 5)
    assert PAYMENT_SOURCE_LEAVE_ENCASHMENT == "leave_encashment"


# ── chốt loại nghỉ ──────────────────────────────────────────────────────────────

def _type_payload(**kw):
    base = dict(code="enc719", name="Phép năm 719")
    base.update(kw)
    return LeaveTypeCreate(**base)


def test_loai_nghi_cho_thanh_toan_ma_khong_tru_quy_bi_422(db):
    with pytest.raises(HTTPException) as err:
        catalog._check_type_create(db, _type_payload(allow_encashment=True, counts_balance=False))
    assert err.value.status_code == 422
    assert "Trừ vào quỹ phép" in err.value.detail
    catalog._check_type_create(db, _type_payload(allow_encashment=True, counts_balance=True))
    catalog._check_type_create(db, _type_payload(allow_encashment=False, counts_balance=False))


def test_sua_loai_nghi_lay_gia_tri_dang_co_cho_o_khong_gui(db):
    t = LeaveType(code="enc719b", name="Loại B", counts_balance=True, allow_encashment=True)
    db.add(t)
    db.flush()
    #  Tắt "trừ quỹ" khi vẫn còn "cho thanh toán" → chặn.
    with pytest.raises(HTTPException) as err:
        catalog._block_code_change(db, t, LeaveTypeUpdate(counts_balance=False).model_dump(exclude_unset=True))
    assert err.value.status_code == 422
    #  Tắt cả hai cùng lúc → được.
    catalog._block_code_change(db, t, {"counts_balance": False, "allow_encashment": False})


def test_tran_nam_va_ngay_giu_lai_co_gioi_han():
    with pytest.raises(ValueError):
        _type_payload(max_encashable_days=-1)
    with pytest.raises(ValueError):
        _type_payload(non_encashable_days=367)
    ok = _type_payload(max_encashable_days=5, non_encashable_days=3)
    assert (ok.max_encashable_days, ok.non_encashable_days) == (5, 3)


def test_xoa_loai_nghi_da_co_phieu_thanh_toan_bi_chan(db):
    t = LeaveType(code="enc719c", name="Loại C", counts_balance=True, allow_encashment=True)
    db.add(t)
    db.flush()
    catalog._block_delete_used_type(db, t)      # chưa có phiếu: qua
    db.add(LeaveEncashment(code="TTP00001", employee_id=1, leave_type_id=t.id, balance_year=YEAR, days=1,
                           status=int(LeaveEncashmentStatus.CANCELLED)))
    db.flush()
    with pytest.raises(HTTPException) as err:
        catalog._block_delete_used_type(db, t)
    assert err.value.status_code == 400
    assert "thanh toán nghỉ phép" in err.value.detail


# ── khóa quyền ──────────────────────────────────────────────────────────────────

def test_khoa_leave_encashment_khai_du():
    assert "leave_encashment" in ENTITIES
    cfg = SCOPE_FIELDS["leave_encashment"]
    assert cfg == {"company": "company_id", "dept_id": "department_id",
                   "owner": "created_by", "self": "employee_id"}


def test_quan_ly_thu_mua_khong_tu_co_khoa_moi():
    from app.seed import STD_ROLES, _PUR_MANAGER_PERMS, _SYS_ENTITIES
    assert "leave_encashment" in _SYS_ENTITIES
    #  Vòng `setdefault` cấp `own` cho MỌI vai trò (kể cả pur_manager) nhưng KHÔNG phải `all` như các khóa ngoài _SYS_ENTITIES.
    assert _PUR_MANAGER_PERMS["leave_encashment"] == (["read", "create", "write", "delete"], "own")
    hr = STD_ROLES["hr_leave"]["perms"]["leave_encashment"]
    assert "approve" in hr[0] and hr[1] == "all"
    assert STD_ROLES["dept_head"]["perms"]["leave_encashment"] == (["read", "export"], "dept")
    assert STD_ROLES["company_head"]["perms"]["leave_encashment"] == (["read", "export"], "company")
    for code, info in STD_ROLES.items():
        perm = info["perms"].get("leave_encashment")
        if code in ("hr_leave", "dept_head", "company_head") or perm is None:
            continue
        assert perm == (["read", "create", "write", "delete"], "own"), code
        assert "approve" not in perm[0]


# ── chốt xem YCTT nguồn nghỉ phép (D1a) ─────────────────────────────────────────

def _payout_world(db, world):
    """Hai YCTT: một thường, một thanh toán nghỉ phép của a2 (công ty A)."""
    enc = LeaveEncashment(code="TTP00001", company_id=world.co["A"], department_id=world.dept["A.kt"],
                          employee_id=world.emp["a2"], leave_type_id=1, balance_year=YEAR, days=2,
                          status=int(LeaveEncashmentStatus.APPROVED))
    db.add(enc)
    db.flush()
    normal = PaymentRequest(code="YCTT1", company_id=world.co["A"], source_type="goods")
    payout = PaymentRequest(code="YCTT2", company_id=world.co["A"], source_type=PAYMENT_SOURCE_LEAVE_ENCASHMENT,
                            source_ref_id=enc.id, payee_employee_id=world.emp["a2"])
    db.add_all([normal, payout])
    db.flush()
    return normal, payout


def test_nhan_vien_thu_mua_khong_thay_yctt_nghi_phep(db, world):
    normal, payout = _payout_world(db, world)
    staff = world.grant("a1", "payment_request", "company")      # có YCTT, không có leave_encashment
    assert staff.sees(PaymentRequest) == {normal.id}
    assert staff.can_get(PaymentRequest, normal.id) is True
    assert staff.can_get(PaymentRequest, payout.id) is False     # gõ id vào URL cũng 404


def test_vai_tro_co_ca_hai_khoa_thay_yctt_nghi_phep(db, world):
    normal, payout = _payout_world(db, world)
    acc = world.grant("a3", "payment_request", "company")
    acc.grant("leave_encashment", "company")
    assert acc.sees(PaymentRequest, "payment_request") == {normal.id, payout.id}
    assert acc.can_get(PaymentRequest, payout.id, "payment_request") is True


def test_pham_vi_cua_phieu_nguon_thu_hep_yctt(db, world):
    """Có `leave_encashment` nhưng phạm vi `own` (phiếu của a3, không phải của a2) → vẫn không thấy YCTT của a2."""
    normal, payout = _payout_world(db, world)
    other = world.grant("a3", "payment_request", "company")
    other.grant("leave_encashment", "own")
    assert other.sees(PaymentRequest, "payment_request") == {normal.id}
    #  Chính chủ (a2) có phạm vi own thì thấy YCTT của chính mình.
    owner = world.grant("a2", "payment_request", "company")
    owner.grant("leave_encashment", "own")
    assert owner.sees(PaymentRequest, "payment_request") == {normal.id, payout.id}


def test_quan_tri_pham_vi_tat_ca_thay_het(db, world):
    normal, payout = _payout_world(db, world)
    admin = world.grant("b1", "payment_request", "all")
    admin.grant("leave_encashment", "all")
    assert admin.sees(PaymentRequest, "payment_request") == {normal.id, payout.id}


def test_yctt_thuong_khong_doi_voi_vai_tro_khong_dinh_toi_nghi_phep(db, world):
    """Không có phiếu thanh toán nào → hành vi YCTT y như trước chốt."""
    a = PaymentRequest(code="YCTT9", company_id=world.co["A"], source_type="goods")
    b = PaymentRequest(code="YCTT10", company_id=world.co["B"], source_type="shipping")
    db.add_all([a, b])
    db.flush()
    actor = world.grant("a1", "payment_request", "company")
    assert actor.sees(PaymentRequest) == {a.id}
