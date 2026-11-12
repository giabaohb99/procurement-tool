"""ai-CR-236 — cổng MCP tạo được Đề nghị thanh toán (YCTT) ở trạng thái NHÁP.

Trước đây `confirm_draft(kind="payment")` chỉ trả link form web (ai-CR-063). Nay tạo phiếu Nháp bằng ĐÚNG service của form
web (`payment_request.service.create_requests` + kiểm phạm vi công nợ như `POST /api/payment-requests`), dưới danh tính chủ
khóa. Không bao giờ tự gửi duyệt; nhóm G7 "Công nợ và thanh toán" tắt thì chặn cả bước tạo.
"""
import json

import pytest

from app.modules.agent_hub import draft_create, mcp, mcp_keys, mcp_settings
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.user.model import User


@pytest.fixture
def no(db, seed):
    """Hai khoản nợ còn phải trả của NCC PHL + một khoản đã tất toán."""
    rows = [
        Payable(company_id=seed.company_id, supplier_code="PHL", supplier_name="NCC PHL", source_type="goods",
                po_code="PO-922", invoice_no="HD922", incur_date="2026-10-05", period="2026", due_date="2026-11-30",
                total=1000, paid_amount=0, remaining=1000, status="unpaid"),
        Payable(company_id=seed.company_id, supplier_code="PHL", supplier_name="NCC PHL", source_type="goods",
                po_code="PO-923", invoice_no="HD923", incur_date="2026-10-10", period="2026", due_date="2026-11-30",
                total=500, paid_amount=200, remaining=300, status="partial"),
        Payable(company_id=seed.company_id, supplier_code="PHL", supplier_name="NCC PHL", source_type="goods",
                po_code="PO-900", incur_date="2026-09-01", period="2026", due_date="2026-10-01",
                total=700, paid_amount=700, remaining=0, status="paid"),
    ]
    db.add_all(rows)
    db.commit()
    return rows


@pytest.fixture
def nguoi_lap(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "payment_request", scope="all", read=True, create=True)
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    return db.get(User, seed.u_req_id)


@pytest.fixture
def mo_nhom_finance(monkeypatch):
    """Nhóm G7 "Công nợ và thanh toán" mặc định TẮT — bật riêng cho bài kiểm cần tạo."""
    real = mcp_settings.tool_blocked
    monkeypatch.setattr(mcp_settings, "tool_blocked",
                        lambda db, name, args=None: None if name == "draft_payment_request" else real(db, name, args))


def _call(db, user, args, scope=mcp_keys.SCOPE_WRITE):
    class _Key:
        id = 1

    _Key.scope = scope
    res = mcp.handle(db, user, _Key(), {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                        "params": {"name": "confirm_draft", "arguments": args}}, {})
    return json.loads(res["result"]["content"][0]["text"])


def _draft(no, **over):
    d = {"kind": "payment_request", "payable_ids": [no[0].id, no[1].id]}
    d.update(over)
    return d


def test_tao_duoc_phieu_nhap_bang_service_web(db, no, nguoi_lap, mo_nhom_finance):
    out = _call(db, nguoi_lap, {"kind": "payment", "draft": _draft(no)})
    assert out["ok"] is True and out["submitted"] is False
    req = db.get(PaymentRequest, out["id"])
    assert req.status == "draft" and req.code == out["code"] and req.created_by == nguoi_lap.id
    assert req.supplier_code == "PHL" and req.company_id == no[0].company_id
    lines = db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == req.id).all()
    assert sorted(ln.amount for ln in lines) == [300, 1000]           # mặc định = số còn lại từng khoản, như form web
    assert out["link"].startswith("http") and out["link"].endswith(f"/finance/payment-requests/{req.id}")
    assert "Gửi duyệt" in out["note"]


def test_submit_true_van_nam_o_nhap(db, no, nguoi_lap, mo_nhom_finance):
    out = _call(db, nguoi_lap, {"kind": "payment", "draft": _draft(no), "submit": True})
    assert out["ok"] is True and out["submitted"] is False
    assert db.get(PaymentRequest, out["id"]).status == "draft"
    assert "Nháp" in out["note"]


def test_khoa_chi_doc_bi_chan(db, no, nguoi_lap, mo_nhom_finance):
    out = _call(db, nguoi_lap, {"kind": "payment", "draft": _draft(no)}, scope=mcp_keys.SCOPE_READ)
    assert out.get("denied") is True
    assert db.query(PaymentRequest).count() == 0


def test_thieu_quyen_tao_bi_chan(db, seed, no, cap_quyen, mo_nhom_finance):
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)          # xem được nợ nhưng không có quyền tạo YCTT
    out = _call(db, db.get(User, seed.u_req_id), {"kind": "payment", "draft": _draft(no)})
    assert "quyền" in out["error"]
    assert db.query(PaymentRequest).count() == 0


def test_nhom_finance_tat_thi_chan(db, no, nguoi_lap):
    assert mcp_settings.GROUP_OF["draft_payment_request"].key == "finance"
    out = _call(db, nguoi_lap, {"kind": "payment", "draft": _draft(no)})
    assert out.get("denied") is True and "Công nợ và thanh toán" in out["error"]
    assert db.query(PaymentRequest).count() == 0


def test_cong_no_da_co_de_nghi_khac_xu_ly_nhu_web(db, no, nguoi_lap, mo_nhom_finance):
    """Form web không chặn lúc TẠO khi khoản nợ đã nằm ở phiếu khác (luật khớp công nợ bắt lúc gửi duyệt / duyệt) —
    cổng MCP đi đúng service đó nên cũng tạo được phiếu Nháp thứ hai."""
    first = _call(db, nguoi_lap, {"kind": "payment", "draft": _draft(no)})
    second = _call(db, nguoi_lap, {"kind": "payment", "draft": _draft(no)})
    assert first["ok"] is True and second["ok"] is True and first["id"] != second["id"]
    assert db.query(PaymentRequest).filter(PaymentRequest.status == "draft").count() == 2


def test_can_tru_tien_treo_di_theo_ban_nhap_va_kep_khong_vuot_no(db, no, nguoi_lap, mo_nhom_finance):
    d = _draft(no, offsets={str(no[0].id): 400, str(no[1].id): 999})
    out = _call(db, nguoi_lap, {"kind": "payment", "draft": d})
    by_po = {ln.po_code: ln for ln in db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == out["id"])}
    assert (by_po["PO-922"].amount, by_po["PO-922"].offset_amount) == (600, 400)
    assert (by_po["PO-923"].amount, by_po["PO-923"].offset_amount) == (0, 300)    # kẹp bằng nợ còn lại như form web


def test_khoan_da_tat_toan_hoac_rong_tra_loi_doc_duoc(db, no, nguoi_lap, mo_nhom_finance):
    out = _call(db, nguoi_lap, {"kind": "payment", "draft": {"payable_ids": [no[2].id]}})
    assert "còn phải trả" in out["error"]
    out = _call(db, nguoi_lap, {"kind": "payment", "draft": {"payable_ids": []}})
    assert "draft_payment_request" in out["error"]
    assert db.query(PaymentRequest).count() == 0


def test_khoan_no_chua_gan_cong_ty_tra_loi_doc_duoc(db, no, nguoi_lap, mo_nhom_finance):
    no[0].company_id = 0
    db.commit()
    out = _call(db, nguoi_lap, {"kind": "payment", "draft": _draft(no)})
    assert "công ty" in out["error"]
    assert db.query(PaymentRequest).count() == 0


def test_khoan_no_ngoai_pham_vi_bi_chan_nhu_web(db, seed, no, nguoi_lap):
    other = Payable(company_id=seed.company_id + 999, supplier_code="PHL", supplier_name="NCC PHL", source_type="goods",
                    po_code="PO-X", period="2026", total=50, paid_amount=0, remaining=50, status="unpaid")
    db.add(other)
    db.commit()

    def chi_thay_hai_khoan(q, model, entity, user, profile):
        return q.filter(model.id.in_([no[0].id, no[1].id]))

    from app.modules.payment_request import service

    real = service.apply_scope
    service.apply_scope = chi_thay_hai_khoan
    try:
        with pytest.raises(draft_create.DraftError, match="ngoài phạm vi"):
            draft_create.create(db, nguoi_lap, "payment", {"payable_ids": [no[0].id, other.id]})
    finally:
        service.apply_scope = real
    assert db.query(PaymentRequest).count() == 0


def test_loi_dan_soan_nhap_qua_mcp_chi_sang_confirm_draft(db, no, nguoi_lap, mo_nhom_finance):
    """Lời dặn của tool soạn nháp viết cho nút trên Trợ lý web — qua cổng phải chỉ sang confirm_draft(kind=payment)."""
    class _Key:
        scope, id = mcp_keys.SCOPE_WRITE, 1

    res = mcp.handle(db, nguoi_lap, _Key(), {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
        "name": "draft_payment_request", "arguments": {"payable_ids": [no[0].id, no[1].id]}}}, {})
    out = json.loads(res["result"]["content"][0]["text"])
    assert set(out["draft"]["payable_ids"]) == {no[0].id, no[1].id}
    assert 'kind="payment"' in out["reminder"] and "bấm nút" not in out["reminder"]
    made = _call(db, nguoi_lap, {"kind": "payment", "draft": out["draft"]})
    assert made["ok"] is True and db.get(PaymentRequest, made["id"]).status == "draft"
