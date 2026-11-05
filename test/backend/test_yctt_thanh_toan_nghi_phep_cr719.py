"""duoc-CR-719 phase 02 — YCTT nguồn "Thanh toán nghỉ phép".

Phủ: hợp đồng bốn hàm cho phase 03, luật sửa / gửi duyệt / chi / xóa của nguồn mới, bản in (D2a: số tài khoản theo
quyền), và việc YCTT này không lọt qua mọi đường đọc không phải danh sách (chi tiết, xuất Excel, tập dữ liệu AI, việc
chờ duyệt của trợ lý, chuông) cho người không có `leave_encashment.read` (D1a).
"""
import json

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.modules.assistant import tools as T
from app.modules.employee.model import Employee
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LeaveEncashmentStatus
from app.modules.leave.encashment_model import LeaveEncashment
from app.modules.notification.model import Notification
from app.modules.payable.model import Payable
from app.modules.payment_request import controller as C
from app.modules.payment_request import export as EX
from app.modules.payment_request import leave_encashment_payout as P
from app.modules.payment_request import service as S
from app.modules.payment_request.hr_payout_guard import PAYMENT_SOURCE_LEAVE_ENCASHMENT
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.payment_request.schema import LineIn, PRequestCreate, PRequestUpdate

STK = "0123456789"


def _make(db, world, *, code="TTP00001", payee="a2", actor="a3"):
    """Phiếu thanh toán nghỉ phép đã duyệt + YCTT nguồn nghỉ phép do máy sinh."""
    t = LeaveType(code=f"pn{code}", name="Phép năm", counts_balance=True, allow_encashment=True)
    db.add(t)
    db.flush()
    emp = db.get(Employee, world.emp[payee])
    emp.bank_account_no, emp.bank_name = STK, "Vietcombank"
    enc = LeaveEncashment(code=code, company_id=emp.company_id, department_id=emp.department_id,
                          employee_id=emp.id, leave_type_id=t.id, balance_year=2026, days=2.5,
                          status=int(LeaveEncashmentStatus.APPROVED))
    db.add(enc)
    db.flush()
    req = P.create_payout_request(db, enc, emp, world.user_id(actor))
    db.commit()
    return enc, emp, req


def _line_in(amount, **kw):
    return LineIn(amount=amount, **kw)


def _fill_money(db, req, amount, uid):
    S.update_request(db, req.id, PRequestUpdate(lines=[_line_in(amount)]), uid)


def _request():
    return Request({"type": "http", "query_string": b"", "headers": []})


# ── 1. hợp đồng bốn hàm ─────────────────────────────────────────────────────────

def test_create_payout_request_dung_hop_dong(db, world):
    enc, emp, req = _make(db, world)
    assert req.source_type == PAYMENT_SOURCE_LEAVE_ENCASHMENT == "leave_encashment"
    assert (req.supplier_code, req.status, req.payment_method, req.prepay) == ("", "draft", "transfer", 0)
    assert req.supplier_name == f"{emp.full_name} ({emp.code})"
    assert (req.payee_employee_id, req.source_ref_id) == (emp.id, enc.id)
    assert (req.company_id, req.department_id) == (emp.company_id, emp.department_id)
    assert req.created_by == 0 and req.updated_by == world.user_id("a3")
    assert float(req.total) == 0 and req.code == f"YCTT{req.id:05d}"
    assert req.note == f"Thanh toán 2.5 ngày Phép năm năm 2026 — phiếu {enc.code}"
    lines = S.lines_of(db, req.id)
    assert len(lines) == 1
    assert (lines[0].payable_id, lines[0].po_code, float(lines[0].amount)) == (0, enc.code, 0)


def test_create_payout_request_khong_commit(db, world):
    """Chỉ flush: rollback thì YCTT biến mất cùng giao dịch của phiếu nguồn."""
    t = LeaveType(code="pnrb", name="Phép", counts_balance=True)
    db.add(t)
    db.flush()
    emp = db.get(Employee, world.emp["a2"])
    enc = LeaveEncashment(code="TTP00077", employee_id=emp.id, leave_type_id=t.id, balance_year=2026, days=1)
    db.add(enc)
    db.flush()
    req = P.create_payout_request(db, enc, emp, 1)
    rid = req.id
    db.rollback()
    assert db.get(PaymentRequest, rid) is None


def test_khong_sinh_hai_yctt_cho_mot_phieu(db, world):
    enc, emp, _ = _make(db, world)
    with pytest.raises(HTTPException) as err:
        P.create_payout_request(db, enc, emp, 1)
    assert err.value.status_code == 400


def test_payout_state_va_allows_cancel(db, world):
    _, _, req = _make(db, world)
    st = P.payout_state(db, req.id)
    assert st == {"id": req.id, "code": req.code, "status": "draft", "status_label": "Nháp", "total": 0.0}
    assert P.payout_state(db, 0) is None
    assert P.payout_state(db, 987654) is None
    assert P.payout_allows_cancel(None) is True
    assert P.payout_allows_cancel({"status": "draft"}) is True
    assert P.payout_allows_cancel({"status": "cancelled"}) is True
    for s in ("submitted", "approved", "paid"):
        assert P.payout_allows_cancel({"status": s}) is False


def test_void_draft_payout_xoa_mem_ban_nhap(db, world):
    _, _, req = _make(db, world)
    P.void_draft_payout(db, req.id, world.user_id("a3"))
    db.commit()
    assert db.get(PaymentRequest, req.id).is_deleted is True
    assert P.payout_state(db, req.id) is None            # xóa mềm = không còn
    P.void_draft_payout(db, req.id, 1)                   # gọi lại / id 0: không làm gì
    P.void_draft_payout(db, 0, 1)


def test_void_draft_payout_khac_nhap_bi_400(db, world):
    _, _, req = _make(db, world)
    _fill_money(db, req, 1_000_000, world.user_id("a3"))
    S.set_status(db, req.id, "submitted", world.user_id("a3"))
    with pytest.raises(HTTPException) as err:
        P.void_draft_payout(db, req.id, 1)
    assert err.value.status_code == 400
    assert db.get(PaymentRequest, req.id).is_deleted is False


def test_void_khong_xoa_duoc_yctt_thuong(db, world):
    normal = PaymentRequest(code="YCTT-N", source_type="goods", status="draft")
    db.add(normal)
    db.commit()
    with pytest.raises(HTTPException) as err:
        P.void_draft_payout(db, normal.id, 1)
    assert err.value.status_code == 400


# ── 2. tạo tay bị chặn ──────────────────────────────────────────────────────────

def test_khong_tao_tay_nguon_nghi_phep_qua_create_requests(db, world):
    data = PRequestCreate(source_type="leave_encashment", supplier_code="NCC1",
                          lines=[LineIn(amount=1_000)])
    with pytest.raises(HTTPException) as err:
        S.create_requests(db, data, 1)
    assert err.value.status_code == 400
    assert "hệ thống tự tạo" in err.value.detail
    assert "leave_encashment" not in S.SOURCE_TYPES


# ── 3. sửa: chỉ ô cho phép + số tiền ────────────────────────────────────────────

def test_sua_chi_duoc_tien_va_o_cho_phep(db, world):
    _, _, req = _make(db, world)
    uid = world.user_id("a3")
    out = S.update_request(db, req.id, PRequestUpdate(
        note="ghi chú mới", payment_method="cash", request_date="2026-11-04",
        lines=[_line_in(3_500_000)]), uid)
    assert float(out.total) == 3_500_000 and out.note == "ghi chú mới" and out.payment_method == "cash"
    ln = S.lines_of(db, req.id)
    assert len(ln) == 1 and float(ln[0].amount) == 3_500_000 and ln[0].po_code == "TTP00001"
    #  Gửi po_code rỗng (màn gửi lại nguyên form) vẫn giữ mã phiếu trên dòng.
    S.update_request(db, req.id, PRequestUpdate(lines=[_line_in(4_000_000, po_code="")]), uid)
    assert S.lines_of(db, req.id)[0].po_code == "TTP00001"


@pytest.mark.parametrize("lines", [
    [LineIn(amount=1), LineIn(amount=2)],                    # thêm dòng
    [],                                                      # bớt hết dòng
    [LineIn(amount=1, payable_id=5)],                        # gắn công nợ
    [LineIn(amount=1, po_code="PO-KHAC")],                   # đổi po_code
    [LineIn(amount=1, offset_amount=100)],                   # cấn trừ
    [LineIn(amount=-5)],                                     # tiền âm
    [LineIn(amount=10_000_000_000_000)],                     # quá trần
])
def test_sua_ngoai_pham_vi_bi_400(db, world, lines):
    _, _, req = _make(db, world)
    with pytest.raises(HTTPException) as err:
        S.update_request(db, req.id, PRequestUpdate(lines=lines), world.user_id("a3"))
    assert err.value.status_code == 400
    assert float(S.lines_of(db, req.id)[0].amount) == 0           # không ghi gì


def test_sua_bat_tra_truoc_bi_400_con_prepay_0_thi_qua(db, world):
    _, _, req = _make(db, world)
    uid = world.user_id("a3")
    S.update_request(db, req.id, PRequestUpdate(prepay=0, note="x"), uid)
    with pytest.raises(HTTPException) as err:
        S.update_request(db, req.id, PRequestUpdate(prepay=1), uid)
    assert err.value.status_code == 400


def test_chi_nhap_tien_o_ban_nhap(db, world):
    _, _, req = _make(db, world)
    uid = world.user_id("a3")
    _fill_money(db, req, 2_000_000, uid)
    S.set_status(db, req.id, "submitted", uid)
    with pytest.raises(HTTPException) as err:
        _fill_money(db, req, 9_000_000, uid)                       # đã gửi duyệt: khóa như mọi YCTT
    assert err.value.status_code == 400
    assert float(S.lines_of(db, req.id)[0].amount) == 2_000_000


# ── 4. gửi duyệt / duyệt / chi ──────────────────────────────────────────────────

def test_gui_duyet_tien_0_bi_400(db, world):
    _, _, req = _make(db, world)
    with pytest.raises(HTTPException) as err:
        S.set_status(db, req.id, "submitted", world.user_id("a3"))
    assert err.value.status_code == 400
    assert "Nhập số tiền thanh toán nghỉ phép" in err.value.detail
    assert db.get(PaymentRequest, req.id).status == "draft"


def test_gui_duyet_khong_doi_so_hoa_don_hay_khop_cong_no(db, world):
    """Dòng không có số hóa đơn, không công nợ — vẫn gửi duyệt được khi có tiền."""
    _, _, req = _make(db, world)
    _fill_money(db, req, 1_500_000, world.user_id("a3"))
    assert S.set_status(db, req.id, "submitted", world.user_id("a3")).status == "submitted"


def test_gui_duyet_chan_offset_va_prepay_du_du_lieu_ban(db, world):
    _, _, req = _make(db, world)
    _fill_money(db, req, 1_000, world.user_id("a3"))
    ln = S.lines_of(db, req.id)[0]
    ln.offset_amount = 50                                         # dữ liệu bẩn (không đi qua API)
    db.commit()
    with pytest.raises(HTTPException):
        S.set_status(db, req.id, "submitted", 1)
    ln.offset_amount = 0
    req.prepay = 1
    db.commit()
    with pytest.raises(HTTPException):
        S.set_status(db, req.id, "submitted", 1)


def test_chi_khong_dung_cong_no(db, world):
    """Có một khoản nợ cùng mã PO = mã phiếu: chi YCTT nghỉ phép không được trừ vào nó."""
    enc, _, req = _make(db, world)
    pay = Payable(company_id=req.company_id, supplier_code="", supplier_name="", source_type="goods",
                  po_code=enc.code, invoice_no="", total=999, paid_amount=0, remaining=999, status="open")
    db.add(pay)
    db.commit()
    uid = world.user_id("a3")
    _fill_money(db, req, 2_000_000, uid)
    for st in ("submitted", "approved", "paid"):
        S.set_status(db, req.id, st, uid)
    db.refresh(pay)
    assert float(pay.paid_amount) == 0
    done = db.get(PaymentRequest, req.id)
    assert done.status == "paid"
    ln = S.lines_of(db, req.id)[0]
    assert float(ln.allocated_amount) == 2_000_000 and S.line_hanging(ln) == 0


def test_tu_choi_cho_phep_hanh_dong_nhu_yctt_thuong(db, world):
    _, _, req = _make(db, world)
    _fill_money(db, req, 1_000, world.user_id("a3"))
    S.set_status(db, req.id, "submitted", 1)
    out = S.set_status(db, req.id, "cancelled", 1, "sai số")
    assert out.status == "cancelled" and out.reject_reason == "sai số"
    assert P.payout_allows_cancel(P.payout_state(db, req.id)) is True


def test_ghi_nhan_hoan_tien_bi_chan(db, world):
    _, _, req = _make(db, world)
    with pytest.raises(HTTPException) as err:
        S.record_refund(db, req.id, 0, "", 1)
    assert err.value.status_code == 400


# ── 5. chặn xóa / cập nhật theo công nợ ─────────────────────────────────────────

def test_xoa_tung_phieu_bi_chan(db, world):
    _, _, req = _make(db, world)
    with pytest.raises(HTTPException) as err:
        S.delete_request(db, req.id, 1)
    assert err.value.status_code == 400
    assert "hủy phiếu thanh toán nghỉ phép bên Nghỉ phép" in err.value.detail
    assert db.get(PaymentRequest, req.id).is_deleted is False


def test_xoa_nhieu_bi_chan_o_controller(db, world):
    _, _, req = _make(db, world)
    actor = world.grant("a3", "payment_request", "all", actions=("read", "delete"))
    actor.grant("leave_encashment", "all")
    with pytest.raises(HTTPException) as err:
        C.bulk_delete_requests(ids=str(req.id), db=db, user=actor.user)
    assert err.value.status_code == 400
    assert "hủy phiếu thanh toán nghỉ phép bên Nghỉ phép" in err.value.detail
    assert db.get(PaymentRequest, req.id).is_deleted is False


def test_refresh_block_reason_va_apply_refresh(db, world):
    _, _, req = _make(db, world)
    assert "không có công nợ" in S.refresh_block_reason(req)
    with pytest.raises(HTTPException):
        S.apply_refresh(db, req.id, 1)
    out = C._out(db, req)
    assert out["out_of_sync"] is False


# ── 6. đọc ra (_out) ────────────────────────────────────────────────────────────

def test_out_co_hai_truong_va_khoi_phieu_nguon(db, world):
    enc, emp, req = _make(db, world)
    out = C._out(db, req)
    assert out["payee_employee_id"] == emp.id and out["source_ref_id"] == enc.id
    assert out["leave_encashment"] == {"id": enc.id, "code": enc.code, "days": 2.5,
                                       "leave_type_name": "Phép năm", "balance_year": 2026, "reason_kind": 1}
    assert STK not in json.dumps(out, default=str)                # không có số tài khoản ở _out
    assert "salary" not in json.dumps(out, default=str)
    normal = PaymentRequest(code="YCTT-N2", source_type="goods", status="draft")
    db.add(normal)
    db.commit()
    plain = C._out(db, normal)
    assert plain["payee_employee_id"] == 0 and "leave_encashment" not in plain


# ── 7. bản in (D2a) ─────────────────────────────────────────────────────────────

def _print(db, req, actor):
    return json.loads(C.print_(req.id, db=db, user=actor.user).body)["data"]


def test_in_an_stk_khi_khong_co_quyen_nhay_cam(db, world):
    _, emp, req = _make(db, world)
    kt = world.grant("a3", "payment_request", "company", actions=("read", "print"))
    kt.grant("leave_encashment", "company")
    data = _print(db, req, kt)
    assert data["bank_account"] == "" and data["bank_name"] == "" and data["bank_hidden"] is True
    assert data["payee"] == {"employee_id": emp.id, "code": emp.code, "full_name": emp.full_name}
    assert STK not in json.dumps(data, default=str)


def test_in_hien_stk_khi_co_employee_sensitive_read(db, world):
    _, _, req = _make(db, world)
    kt = world.grant("a3", "payment_request", "company", actions=("read", "print"))
    kt.grant("leave_encashment", "company").grant("employee_sensitive", "company")
    data = _print(db, req, kt)
    assert (data["bank_account"], data["bank_name"], data["bank_hidden"]) == (STK, "Vietcombank", False)


def test_in_hien_stk_cho_chinh_chu(db, world):
    _, _, req = _make(db, world)
    me = world.grant("a2", "payment_request", "own", actions=("read", "print"))
    me.grant("leave_encashment", "own")
    # phiếu do a3 lập (created_by = 0) — chính chủ thấy nhờ phạm vi company của YCTT
    me = world.grant("a2", "payment_request", "company", actions=("read", "print"))
    data = _print(db, req, me)
    assert data["bank_account"] == STK and data["bank_hidden"] is False


def test_in_tien_mat_khong_in_stk_va_khong_co_co_an(db, world):
    _, _, req = _make(db, world)
    uid = world.user_id("a3")
    S.update_request(db, req.id, PRequestUpdate(payment_method="cash"), uid)
    kt = world.grant("a3", "payment_request", "company", actions=("read", "print"))
    kt.grant("leave_encashment", "company").grant("employee_sensitive", "company")
    data = _print(db, req, kt)
    assert data["bank_account"] == "" and data["bank_hidden"] is False


# ── 8. D1a: không lọt qua đường đọc nào ─────────────────────────────────────────

def _staff_world(db, world):
    """a1 = nhân viên thu mua: có mọi quyền YCTT (kể cả duyệt / xuất) nhưng KHÔNG có leave_encashment."""
    normal = PaymentRequest(code="YCTT-THUONG", company_id=world.co["A"], source_type="goods",
                            status="submitted", total=5_000_000)
    db.add(normal)
    db.flush()
    db.add(PaymentRequestLine(request_id=normal.id, po_code="PO-X", invoice_no="HD-1", amount=5_000_000))
    enc, emp, payout = _make(db, world)
    payout.company_id = world.co["A"]
    _fill_money(db, payout, 7_777_000, world.user_id("a3"))
    S.set_status(db, payout.id, "submitted", world.user_id("a3"))
    db.commit()
    staff = world.grant("a1", "payment_request", "company",
                        actions=("read", "write", "delete", "approve", "export", "print"))
    return staff, normal, payout


def test_pur_staff_khong_thay_qua_danh_sach_chi_tiet_in_xuat(db, world):
    staff, normal, payout = _staff_world(db, world)
    #  danh sách
    ids = {r.id for r in C._list_query(db, _request(), staff.user).all()}
    assert ids == {normal.id}
    #  chi tiết (gõ id vào URL)
    with pytest.raises(HTTPException) as err:
        C.get_(payout.id, db=db, user=staff.user)
    assert err.value.status_code == 403
    #  bản in + ghi (đường dùng `_scoped`)
    for action_call in (lambda: C.print_(payout.id, db=db, user=staff.user),
                        lambda: C.pay_(payout.id, background_tasks=None, db=db, user=staff.user),
                        lambda: C.delete_(payout.id, db=db, user=staff.user)):
        with pytest.raises(HTTPException) as e2:
            action_call()
        assert e2.value.status_code == 404
    #  xuất Excel (cùng `_list_query`, action export): không có dòng của YCTT nghỉ phép
    q = C._list_query(db, _request(), staff.user, "export")
    rows = EX.build_rows(db, EX.load_lines(db, q.all()))
    assert {r["code"] for r in rows} == {"YCTT-THUONG"}
    assert all("7777000" not in str(v) for r in rows for v in r.values())


def test_pur_staff_khong_thay_qua_tap_du_lieu_ai(db, world):
    staff, normal, payout = _staff_world(db, world)
    out = T.run_tool(db, staff.user, "dataset_query", {"dataset": "payment_request",
                                                       "measures": ["total", "count"]})
    assert out["totals"]["count"] == 1
    assert out["totals"]["total"] == 5_000_000
    #  người có cả hai khóa thấy cả hai phiếu
    acc = world.grant("a3", "payment_request", "company", actions=("read", "approve"))
    acc.grant("leave_encashment", "company")
    out2 = T.run_tool(db, acc.user, "dataset_query", {"dataset": "payment_request",
                                                      "measures": ["total", "count"]})
    assert out2["totals"]["count"] == 2


def test_pur_staff_khong_thay_trong_viec_cho_duyet_cua_tro_ly(db, world):
    staff, normal, payout = _staff_world(db, world)
    out = T.run_tool(db, staff.user, "pending_procurement_approvals", {"entity": "payment_request"})
    codes = [it["code"] for g in out["groups"] for it in g["items"]]
    assert codes == ["YCTT-THUONG"] and out["total"] == 1
    acc = world.grant("a3", "payment_request", "company", actions=("read", "approve"))
    acc.grant("leave_encashment", "company")
    out2 = T.run_tool(db, acc.user, "pending_procurement_approvals", {"entity": "payment_request"})
    assert out2["total"] == 2


def test_chuong_tao_yctt_chi_den_nguoi_thay_duoc_phieu(db, world):
    _, _, payout = _make(db, world)
    staff = world.grant("a1", "payment_request", "company", actions=("read", "approve"))
    acc = world.grant("a3", "payment_request", "company", actions=("read", "approve"))
    acc.grant("leave_encashment", "company")
    P.notify_payout_created(db, payout)
    got = db.query(Notification).all()
    assert {n.user_id for n in got} == {acc.user.id}
    assert staff.user.id not in {n.user_id for n in got}
    assert payout.code in got[0].title and "thanh toán nghỉ phép cần nhập số tiền" in got[0].body
    assert not any(ch.isdigit() for ch in got[0].body.replace(payout.code, ""))     # chữ trơn, không số tiền / ngày


def test_chuong_cu_pay_approved_khong_di_dau(db, world):
    """Phiếu máy tạo (created_by = 0): các chuông gửi cho người lập không có ai nhận, không rò sang ai."""
    _, _, payout = _make(db, world)
    world.grant("a1", "payment_request", "company", actions=("read", "approve"))
    before = db.query(Notification).count()
    C._notify_pay(db, None, payout, "pay_approved")
    assert db.query(Notification).count() == before
