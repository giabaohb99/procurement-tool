"""ai-CR-239 — đối chiếu HÓA ĐƠN NCC với lần giao / dòng ĐMH và công nợ khi soạn nháp `draft_po_receipt`.

- nhận số trên hóa đơn: tiền trước thuế, VAT % / tiền VAT, tổng tiền, tùy chọn các dòng hàng (tên, ĐVT, SL, đơn giá);
- so với các lần giao + dòng ĐMH của nháp (đơn giá × tỷ giá, % VAT của dòng) và công nợ hàng của lần giao;
- báo khớp / lệch bao nhiêu, nhận ra hóa đơn GỘP BỘ (một dòng ứng với chai + nắp), kèm công nợ còn phải trả để gợi ý
  draft_payment_request;
- CHỈ cảnh báo: nháp vẫn soạn, xác nhận vẫn ghi đúng như ai-CR-237, không đổi gì thêm.

Ca thật 12/11/2026: hóa đơn PHL số 6265 ký hiệu 1C26TAA ghi gộp 5.000 Bộ × 2.425 = 12.125.000, VAT 8% 970.000, tổng
13.095.000 — ứng với PO01017 gồm chai CHT0238 + nắp NAP0161.
"""
# ruff: noqa: F811  (fixture `kho` dùng chung từ bài bao-CR-740)
from types import SimpleNamespace

import pytest

from app.modules.agent_hub import draft_create
from app.modules.assistant import tools as T
from app.modules.payable.model import Payable
from app.modules.product.model import Product
from app.modules.purchase_order.model import PODelivery

from test_assistant_ghi_lan_nhan_hang_cr740 import SUP, _item, _po, _receive, kho  # noqa: F401

INV = {"invoice_no": "6265", "invoice_date": "12/11/2026"}
PHL_FIGURES = {"invoice_amount": 12125000, "invoice_vat_rate": 8, "invoice_vat_amount": 970000,
               "invoice_total": 13095000,
               "invoice_lines": [{"name": "Bộ chai nắp PET 100ml", "unit": "Bộ", "qty": 5000, "unit_price": 2425}]}


@pytest.fixture
def phl(kho, db, cap_quyen):
    """PO01017 (ĐMH02401): chai CHT0238 2.000 đ + nắp NAP0161 425 đ, mỗi dòng 5.000, đã nhận đủ (lần giao có sẵn)."""
    for code in ("CHT0238", "NAP0161"):
        db.add(Product(code=code, name=f"Hàng {code}", unit="Cái"))
    cap_quyen(kho.staff.id, "payable", scope="all", read=True)
    po = _po(db, "PO01017", "2026-11-01", [("CHT0238", 5000), ("NAP0161", 5000)])
    po.misa_code = "DMH02401"
    _item(db, po, "CHT0238").price = 2000
    _item(db, po, "NAP0161").price = 425
    db.commit()
    chai = _receive(db, po, "CHT0238", 5000, date="2026-11-12")
    nap = _receive(db, po, "NAP0161", 5000, date="2026-11-12")
    return SimpleNamespace(po=po, chai=chai, nap=nap)


def _draft(w, user=None, **args):
    return T.run_tool(w.db, user or w.staff, "draft_po_receipt", {"supplier": "Bao bì nhựa Phương Nam", **args})


def _invoice_mode(kho, phl, **figures):
    return _draft(kho, invoice_deliveries=[phl.chai.id, phl.nap.id], **INV, **figures)


def test_ca_phl_gop_bo_vat_8_khop_tong(kho, phl, db):
    out = _invoice_mode(kho, phl, **PHL_FIGURES)
    chk = out["invoice_check"]
    assert chk["status"] == "match" and chk["currency"] == "VND"
    assert chk["expected"] == {"amount": 12125000, "vat": 970000, "total": 13095000}
    assert chk["diffs"] == []
    (kit,) = chk["kits"]                                     # một dòng hóa đơn ↔ hai dòng ĐMH
    assert kit["qty"] == 5000 and kit["unit"] == "Bộ" and kit["unit_price"] == 2425
    assert kit["expected_unit_price"] == 2425
    assert {(c["product_code"], c["qty"], c["ratio"]) for c in kit["components"]} == {("CHT0238", 5000, 1),
                                                                                      ("NAP0161", 5000, 1)}
    assert "gộp" in chk["summary"].lower() and not any("LỆCH" in w for w in out["warnings"])
    #  Công nợ liên quan: hai khoản nợ hàng của hai lần giao, còn phải trả đủ 13.095.000 → gợi ý lập đề nghị thanh toán.
    pays = {p.ref_id: p for p in db.query(Payable).filter(Payable.source_type == "goods", Payable.po_id == phl.po.id)}
    assert {p["payable_id"] for p in chk["payables"]} == {pays[phl.chai.id].id, pays[phl.nap.id].id}
    assert chk["payables_remaining"] == 13095000
    assert "draft_payment_request" in chk["next_step"]
    assert set(chk["payable_ids"]) == {pays[phl.chai.id].id, pays[phl.nap.id].id}
    #  Chỉ cảnh báo: xác nhận ghi đúng như ai-CR-237 (số + ngày HĐ), không đổi số lượng / công nợ.
    draft_create.create(db, kho.staff, "po_receipt", out["draft"])
    for d in (db.get(PODelivery, phl.chai.id), db.get(PODelivery, phl.nap.id)):
        assert (d.invoice_no, d.invoice_date, float(d.received_qty)) == ("6265", "2026-11-12", 5000)
    assert sum(float(p.total) for p in db.query(Payable).filter(Payable.po_id == phl.po.id)) == 13095000


def test_lech_don_gia_bao_so_lech_nhung_van_soan_nhap(kho, phl, db):
    figures = {**PHL_FIGURES, "invoice_amount": 12250000, "invoice_vat_amount": 980000, "invoice_total": 13230000,
               "invoice_lines": [{"name": "Bộ chai nắp", "unit": "Bộ", "qty": 5000, "unit_price": 2450}]}
    out = _invoice_mode(kho, phl, **figures)
    chk = out["invoice_check"]
    assert chk["status"] == "mismatch" and "draft" in out          # không chặn
    by = {d["field"]: d for d in chk["diffs"]}
    assert by["unit_price"]["invoice"] == 2450 and by["unit_price"]["expected"] == 2425
    assert by["unit_price"]["diff"] == 25
    assert by["amount"]["diff"] == 125000 and by["total"]["diff"] == 135000
    assert any("LỆCH" in w and "đơn giá" in w.lower() for w in out["warnings"])
    draft_create.create(db, kho.staff, "po_receipt", out["draft"])   # người dùng vẫn quyết ghi được
    assert db.get(PODelivery, phl.chai.id).invoice_no == "6265"


def test_lech_vat(kho, phl):
    figures = {"invoice_amount": 12125000, "invoice_vat_rate": 10, "invoice_vat_amount": 1212500,
               "invoice_total": 13337500}
    chk = _invoice_mode(kho, phl, **figures)["invoice_check"]
    by = {d["field"]: d for d in chk["diffs"]}
    assert chk["status"] == "mismatch"
    assert by["vat_rate"]["invoice"] == 10 and by["vat_rate"]["expected"] == 8
    assert by["vat"]["diff"] == 242500 and by["total"]["diff"] == 242500
    assert "amount" not in by                                         # tiền trước thuế vẫn khớp


def test_lam_tron_trong_nguong_van_khop(kho, phl):
    chk = _invoice_mode(kho, phl, invoice_amount="12.125.000", invoice_vat_amount="970.400",
                        invoice_total="13.095.400")["invoice_check"]
    assert chk["status"] == "match" and chk["diffs"] == []               # lệch 400 đ < ngưỡng 1.000 đ


def test_doi_chieu_khi_ghi_lan_nhan_moi(kho, db, cap_quyen):
    """Chế độ lần nhận mới: so với SL sẽ ghi; công nợ chưa có (sinh khi xác nhận) — nói rõ."""
    cap_quyen(kho.staff.id, "payable", scope="all", read=True)
    out = _draft(kho, slip_date="2026-11-12", lines=[{"product_code": "NAP0169", "qty": 100}], **INV,
                 invoice_amount=100000, invoice_vat_rate=8, invoice_total=108000)
    chk = out["invoice_check"]
    assert chk["status"] == "match" and chk["expected"]["total"] == 108000
    assert chk["payables"] == [] and chk["pending_payables"] == 1
    assert "confirm_draft" in chk["next_step"]


def test_khong_co_so_tien_thi_khong_doi_chieu(kho, phl):
    out = _invoice_mode(kho, phl)
    assert "invoice_check" not in out


def test_khong_quyen_cong_no_thi_khong_kem_cong_no(kho, db):
    d = _receive(db, kho.po712, "NAP0169", 500)
    out = _draft(kho, invoice_deliveries=[d.id], **INV, invoice_total=540000)
    chk = out["invoice_check"]
    assert chk["status"] == "match" and "payables" not in chk and "công nợ" in chk["payable_note"]


def test_so_sai_dang_chi_canh_bao(kho, phl):
    out = _invoice_mode(kho, phl, invoice_total="mười ba triệu", invoice_amount=12125000)
    assert "draft" in out and out["invoice_check"]["status"] == "match"
    assert any("mười ba triệu" in w for w in out["invoice_check"]["notes"])
