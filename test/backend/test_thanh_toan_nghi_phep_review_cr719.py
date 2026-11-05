"""duoc-CR-719 — sửa theo bản review code (H1, M1, M2, M3, L1..L4, L6).

Bám đúng kịch bản người review đã dò: người nhận tiền có quyền YCTT tự nhập / gửi / duyệt / chi YCTT của mình (H1);
nghỉ việc gồm phần mang sang rồi qua hạn bị thu hồi lần hai (M1); phiếu cuối năm đã duyệt chặn khoản nghỉ việc (M2);
nhật ký hệ thống lộ số tiền YCTT nghỉ phép (M3).
"""
import uuid
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.logging_policy import MASKED, mask_payload, sensitive_keys_for_path
from app.core.request_context import RequestContext, reset_context, set_context
from app.core.logging_codes import ACTOR_KIND_USER
from app.modules.employee.model import Employee
from app.modules.leave import balance_service, carryover_service
from app.modules.leave import encashment_approval_bridge as bridge, encashment_service as service
from app.modules.leave import encashment_transitions as tr
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.constants import LeaveEncashmentReason as R, LeaveEncashmentStatus as S
from app.modules.leave.encashment_schema import LeaveEncashmentCreate, LeaveEncashmentUpdate
from app.modules.payment_request import controller as C
from app.modules.payment_request import leave_encashment_payout as payout
from app.modules.payment_request import service as pay_service
from app.modules.payment_request.hr_payout_guard import PAYMENT_SOURCE_LEAVE_ENCASHMENT
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.payment_request.schema import LineIn, PRequestUpdate

# Fixture + helper dùng chung với bộ bài kiểm chính của CR-719 (import fixture để pytest thấy ở tệp này).
from test_nghi_phep_thanh_toan_cr719 import (  # noqa: F401  (fixture autouse + lt)
    ACTOR, YEAR, _balance, _create, _emp, _flow, _settings_from_test_db, _submit, _type, _user, lt)

APPROVED_HOOK = SimpleNamespace(updated_by=ACTOR, finish_reason="")


def _approve(db, obj):
    bridge._on_approved(db, obj.id, APPROVED_HOOK)
    db.commit()
    db.refresh(obj)


def _approved_form(db, lt, emp, *, reason=R.YEAR_END, days=None):
    obj = _create(db, emp, lt, days=days, reason_kind=int(reason))
    _submit(db, obj, emp)
    _approve(db, obj)
    return obj


# ── H1: người nhận không tự xử lý YCTT của mình ─────────────────────────────────

def _payee_world(db, world, lt):
    """a2 = người nhận (có quyền YCTT ghi + duyệt phạm vi công ty, và `self` của leave_encashment); a3 = kế toán."""
    emp = db.get(Employee, world.emp["a2"])
    _balance(db, emp, lt)
    obj = _approved_form(db, lt, emp, days=3)
    req = db.get(PaymentRequest, obj.payment_request_id)
    payee = world.grant("a2", "payment_request", "company", actions=("read", "write", "approve"))
    payee.grant("leave_encashment", "own")
    accountant = world.grant("a3", "payment_request", "company", actions=("read", "write", "approve"))
    accountant.grant("leave_encashment", "company")
    return req, payee, accountant


def test_h1_nguoi_nhan_khong_tu_nhap_tien_gui_duyet_duyet_chi(db, world, lt):
    req, payee, accountant = _payee_world(db, world, lt)
    data = PRequestUpdate(lines=[LineIn(amount=99_000_000)])
    with pytest.raises(HTTPException) as err:
        C.update_(req.id, data, db=db, user=payee.user)
    assert err.value.status_code == 403 and "chính mình" in err.value.detail
    assert float(db.get(PaymentRequest, req.id).total) == 0

    # kế toán nhập tiền hợp lệ; người nhận vẫn không gửi duyệt / duyệt / từ chối / chi được
    C.update_(req.id, PRequestUpdate(lines=[LineIn(amount=2_000_000)]), db=db, user=accountant.user)
    bg = BackgroundTasks()
    with pytest.raises(HTTPException) as e1:
        C.submit_(req.id, bg, db=db, user=payee.user)
    assert e1.value.status_code == 403
    C.submit_(req.id, bg, db=db, user=accountant.user)
    for call in (lambda: C.approve_(req.id, bg, db=db, user=payee.user),
                 lambda: C.reject_(req.id, {"reason": "x"}, bg, db=db, user=payee.user)):
        with pytest.raises(HTTPException) as e2:
            call()
        assert e2.value.status_code == 403
    C.approve_(req.id, bg, db=db, user=accountant.user)
    with pytest.raises(HTTPException) as e3:
        C.pay_(req.id, bg, db=db, user=payee.user)
    assert e3.value.status_code == 403
    assert db.get(PaymentRequest, req.id).status == "approved"
    C.pay_(req.id, bg, db=db, user=accountant.user)
    assert db.get(PaymentRequest, req.id).status == "paid"


def test_h1_service_chan_ca_khi_la_quan_tri(db, world, lt):
    """Không có ngoại lệ cho quản trị nếu chính họ là người nhận (chốt ở service, không ở quyền)."""
    req, payee, _ = _payee_world(db, world, lt)
    uid = world.user_id("a2")
    with pytest.raises(HTTPException) as err:
        pay_service.update_request(db, req.id, PRequestUpdate(note="sửa"), uid)
    assert err.value.status_code == 403
    for status in ("submitted", "approved", "cancelled", "paid"):
        with pytest.raises(HTTPException) as e2:
            pay_service.set_status(db, req.id, status, uid)
        assert e2.value.status_code == 403
    # YCTT thường của cùng người không bị ảnh hưởng
    normal = PaymentRequest(code="YCTT-T", company_id=1, source_type="goods", status="draft", total=0)
    db.add(normal)
    db.commit()
    pay_service.update_request(db, normal.id, PRequestUpdate(note="ok"), uid)


def test_h1_tai_khoan_chua_gan_nhan_su_khong_bi_chan(db, world, lt):
    req, _, _ = _payee_world(db, world, lt)
    pay_service.update_request(db, req.id, PRequestUpdate(note="kế toán"), 9999)   # id không có hồ sơ -> không là người nhận


# ── M1: nghỉ việc gồm phần mang sang, qua hạn không thu hồi lần hai ──────────────

def _resign_emp(db, code="RS"):
    return _emp(db, code, resign_date=date(YEAR, 12, 31))


def test_m1_nghi_viec_12_cong_5_mang_sang_tra_17_qua_han_con_0(db):
    lt = _type(db, carry_over_expire_month=12)
    emp = _resign_emp(db)
    _balance(db, emp, lt, allocated_days=12.0, carried_days=5.0)
    obj = _approved_form(db, lt, emp, reason=R.RESIGNATION)
    assert obj.days == 17 and obj.carried_paid_days == 5
    row = balance_service.get_balance(db, emp.id, YEAR, lt.id)
    assert row.encashed_days == 17 and row.encashed_carried_days == 5 and row.remaining_days == 0
    lost = carryover_service.expire_carried(row, lt, today=date(YEAR + 1, 1, 5))
    assert lost == 0 and row.carried_days == 5 and row.remaining_days == 0       # trước bản vá: -5


def test_m1_cuoi_nam_khong_lay_phan_mang_sang_qua_han_van_thu_hoi_dung(db):
    lt = _type(db, carry_over_expire_month=12)
    emp = _emp(db, "YE")
    _balance(db, emp, lt, allocated_days=12.0, carried_days=5.0)
    obj = _approved_form(db, lt, emp)                      # D6a: 12 ngày, không đụng phần mang sang
    assert obj.days == 12 and obj.carried_paid_days == 0
    row = balance_service.get_balance(db, emp.id, YEAR, lt.id)
    assert row.encashed_carried_days == 0 and row.remaining_days == 5
    assert carryover_service.expire_carried(row, lt, today=date(YEAR + 1, 1, 5)) == 5
    assert row.remaining_days == 0


def test_m1_huy_phieu_nghi_viec_tra_dung_phan_mang_sang(db):
    lt = _type(db, carry_over_expire_month=12)
    emp = _resign_emp(db, "RC")
    _balance(db, emp, lt, allocated_days=12.0, carried_days=5.0)
    obj = _approved_form(db, lt, emp, reason=R.RESIGNATION)
    tr.cancel(db, obj, "nhầm", ACTOR)
    row = balance_service.get_balance(db, emp.id, YEAR, lt.id)
    assert row.encashed_days == 0 and row.encashed_carried_days == 0 and row.remaining_days == 17


# ── M2: khóa còn hiệu lực gồm lý do ─────────────────────────────────────────────

def test_m2_cuoi_nam_da_duyet_roi_van_lap_duoc_phieu_nghi_viec(db, lt):
    emp = _resign_emp(db, "M2")
    _balance(db, emp, lt, allocated_days=10.0)
    year_end = _approved_form(db, lt, emp, days=4)
    assert year_end.active_key.endswith(f":{int(R.YEAR_END)}")
    # đánh dấu YCTT đã chi: phiếu không hủy được, nhưng khoản nghỉ việc bắt buộc theo luật vẫn lập được
    db.get(PaymentRequest, year_end.payment_request_id).status = "paid"
    db.commit()
    resign = _create(db, emp, lt, reason_kind=int(R.RESIGNATION))
    assert resign.active_key.endswith(f":{int(R.RESIGNATION)}") and resign.days == 6
    with pytest.raises(HTTPException) as dup_resign:
        _create(db, emp, lt, reason_kind=int(R.RESIGNATION))
    assert dup_resign.value.status_code == 409 and "nghỉ việc" in dup_resign.value.detail
    with pytest.raises(HTTPException) as dup_year:
        _create(db, emp, lt, days=1, reason_kind=int(R.YEAR_END))
    assert dup_year.value.status_code == 409 and "cuối năm" in dup_year.value.detail


def test_m2_doi_ly_do_cua_phieu_nhap_doi_khoa_va_chan_trung(db, lt):
    emp = _resign_emp(db, "M2U")
    _balance(db, emp, lt, allocated_days=10.0)
    year_end = _create(db, emp, lt, days=2)
    moved = service.update(db, year_end, LeaveEncashmentUpdate(reason_kind=int(R.RESIGNATION), days=2), _user(emp))
    assert moved.active_key.endswith(f":{int(R.RESIGNATION)}")
    other = _create(db, emp, lt, days=1)                       # cuối năm: khóa đã được nhả
    with pytest.raises(HTTPException) as err:
        service.update(db, other, LeaveEncashmentUpdate(reason_kind=int(R.RESIGNATION)), _user(emp))
    assert err.value.status_code == 409


def test_thong_bao_loai_nghi_khong_cho_thanh_toan_goi_dung_ten_o_cai_dat(db):
    off = _type(db, code="offx", name="Không cho", allow_encashment=False)
    emp = _emp(db, "MSG")
    with pytest.raises(HTTPException) as err:
        _create(db, emp, off)
    assert "Cho phép thanh toán nghỉ phép" in err.value.detail and "Cho thanh toán ngày phép" not in err.value.detail


# ── M3: nhật ký hệ thống không lộ số tiền YCTT nghỉ phép ─────────────────────────

@pytest.fixture
def ctx(db, monkeypatch):
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    context = RequestContext(request_id=uuid.uuid4().bytes, user_id=7, actor_kind=ACTOR_KIND_USER)
    token = set_context(context)
    try:
        yield context
    finally:
        reset_context(token)


def _yctt(db, source):
    req = PaymentRequest(code=f"Y-{source}", company_id=1, source_type=source, status="draft", total=0,
                         created_by=1, updated_by=1)
    db.add(req)
    db.flush()
    line = PaymentRequestLine(request_id=req.id, po_code="x", amount=0, created_by=1, updated_by=1)
    db.add(line)
    db.commit()
    return req, line


def _entry(ctx, table, field):
    return next(e for e in ctx.changes if e.table_name == table and e.field == field)


def test_m3_doi_so_tien_yctt_nghi_phep_bi_che_con_yctt_thuong_van_ghi(db, ctx):
    leave, leave_line = _yctt(db, PAYMENT_SOURCE_LEAVE_ENCASHMENT)
    goods, goods_line = _yctt(db, "goods")
    ctx.changes = []
    leave.total, leave_line.amount = 4_615_000, 4_615_000
    goods.total, goods_line.amount = 5_000_000, 5_000_000
    db.commit()
    for table, field, row in (("tab_payment_request", "total", leave), ("tab_payment_request_line", "amount", leave_line)):
        entry = next(e for e in ctx.changes if e.table_name == table and e.field == field and e.row_id == row.id)
        assert entry.is_masked is True and entry.before_value is None and entry.after_value is None
    for table, field, row in (("tab_payment_request", "total", goods), ("tab_payment_request_line", "amount", goods_line)):
        entry = next(e for e in ctx.changes if e.table_name == table and e.field == field and e.row_id == row.id)
        assert entry.is_masked is False and entry.after_value is not None and "5000000" in entry.after_value


def test_m3_anh_chup_them_moi_yctt_nghi_phep_che_so_tien(db, ctx):
    ctx.changes = []
    leave, _ = _yctt(db, PAYMENT_SOURCE_LEAVE_ENCASHMENT)
    snap = next(e for e in ctx.changes if e.table_name == "tab_payment_request" and e.snapshot).snapshot
    assert snap["total"] == "***" and snap["code"] == leave.code
    line_snap = next(e for e in ctx.changes if e.table_name == "tab_payment_request_line" and e.snapshot).snapshot
    assert line_snap["amount"] == "***"


@pytest.mark.parametrize("path", ["/api/payment-requests/5", "/api/payment-requests/5/approve", "/api/payment-requests/12/pay"])
def test_m3_than_request_yctt_che_so_tien(path):
    body = {"note": "n", "lines": [{"amount": 4615000, "po_code": "TTP1"}], "total": 4615000}
    masked = mask_payload(body, sensitive_keys_for_path(path))
    assert masked["total"] == MASKED and masked["lines"][0]["amount"] == MASKED and masked["note"] == "n"


@pytest.mark.parametrize("path", ["/api/payment-requests", "/api/payment-requests/summary", "/api/purchase-orders/5"])
def test_m3_duong_khac_khong_bi_che_them(path):
    assert sensitive_keys_for_path(path) == frozenset()


# ── L1: thứ tự khóa phiếu rồi tới quỹ ───────────────────────────────────────────

def test_l1_duyet_chiem_phieu_truoc_roi_moi_khoa_dong_quy(db, lt, monkeypatch):
    emp = _emp(db, "L1")
    _balance(db, emp, lt)
    obj = _create(db, emp, lt, days=2)
    _submit(db, obj, emp)
    order: list[str] = []
    real_claim, real_get = service.try_claim, balance_service.get_balance

    monkeypatch.setattr(service, "try_claim", lambda *a, **k: (order.append("form"), real_claim(*a, **k))[1])

    def spy_get(*args, **kwargs):
        if kwargs.get("for_update"):
            order.append("balance")
        return real_get(*args, **kwargs)

    monkeypatch.setattr(balance_service, "get_balance", spy_get)
    tr.approve_now(db, obj, ACTOR)
    assert order[:2] == ["form", "balance"]


# ── L2: khóa dòng + chặn dòng đã xóa mềm khi đổi trạng thái YCTT ─────────────────

def test_l2_set_status_doc_lai_dong_va_tu_choi_yctt_da_xoa_mem(db, world, lt):
    emp = db.get(Employee, world.emp["a2"])
    _balance(db, emp, lt)
    obj = _approved_form(db, lt, emp, days=2)
    req = db.get(PaymentRequest, obj.payment_request_id)
    pay_service.update_request(db, req.id, PRequestUpdate(lines=[LineIn(amount=1000)]), 9999)
    assert req.is_deleted is False              # bản trong bộ nhớ phiên: còn sống
    # lượt hủy phiếu (phiên khác) xóa mềm YCTT đúng lúc kế toán bấm Gửi duyệt
    db.execute(text("UPDATE tab_payment_request SET is_deleted = 1 WHERE id = :i"), {"i": req.id})
    with pytest.raises(HTTPException) as err:
        pay_service.set_status(db, req.id, "submitted", 9999)
    assert err.value.status_code == 404
    db.rollback()
    assert db.get(PaymentRequest, req.id).status == "draft"


# ── L3: Nhân sự hủy được phiếu Chờ duyệt đang chạy trong luồng ───────────────────

def test_l3_nhan_su_huy_phieu_dang_cho_duyet_trong_luong(db, lt):
    emp, approver, hr = _emp(db, "L3E"), _emp(db, "L3P"), _emp(db, "L3H")
    _balance(db, emp, lt)
    _flow(db, approver)
    obj = _create(db, emp, lt, days=4)
    _submit(db, obj, emp)
    assert obj.approval_instance_id and balance_service.get_balance(db, emp.id, YEAR, lt.id).pending_days == 4
    hr_user = SimpleNamespace(id=61, employee_id=hr.id)
    out = bridge.cancel_request(db, obj, "Nhập nhầm", hr_user)
    assert out.status == int(S.CANCELLED) and out.active_key is None
    assert balance_service.get_balance(db, emp.id, YEAR, lt.id).pending_days == 0
    assert bridge.running_instance(db, obj.id) is None


# ── L4: chuông chỉ chạy khi commit thật, không chạy lúc nhả savepoint ────────────

def test_l4_chuong_bo_qua_savepoint_va_chay_dung_mot_lan_khi_commit_that(db, monkeypatch):
    req = PaymentRequest(code="Y-L4", company_id=1, source_type=PAYMENT_SOURCE_LEAVE_ENCASHMENT, status="draft",
                         total=0, created_by=0, updated_by=1)
    db.add(req)
    db.commit()
    calls: list[str] = []
    monkeypatch.setattr(payout, "notify_payout_created", lambda session, r, *a, **k: calls.append(r.code))
    tr._notify_after_commit(db, req.id)
    nested = db.begin_nested()
    nested.commit()                               # nhả savepoint: giao dịch ngoài chưa commit thật
    assert calls == []
    db.commit()
    assert calls == ["Y-L4"]
    db.add(PaymentRequest(code="Y-L4b", company_id=1, source_type="goods", status="draft"))
    db.commit()
    assert calls == ["Y-L4"]                       # không chạy lần hai
