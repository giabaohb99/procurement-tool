"""bao-CR-319 P5 — công nợ từng dòng chi phí lô hàng nhập khẩu + tạo Yêu cầu thanh toán.

Luật phải giữ:
1. Đơn NHÁP không sinh nợ; duyệt xong mỗi dòng chi phí (có NCC, tiền > 0) thành MỘT khoản
   nợ `source_type = ref_type = "import_cost"`, `ref_id` = id dòng chi phí. Tiền quy đổi,
   tách trước VAT / VAT; hạn trả ưu tiên ô "Hạn thanh toán" của dòng.
2. Sửa / xóa dòng sau khi duyệt thì nợ chạy theo (idempotent); dòng ĐÃ CHI thì cấm xóa.
3. Hủy đơn gỡ nợ CHƯA chi, giữ nợ đã chi (còn chỗ đối chiếu).
4. Tạo YCTT từ các khoản nợ chi phí: mỗi NCC một phiếu; chi tiền trừ đúng khoản của dòng.
"""
import pytest
from fastapi import HTTPException

from app.modules.payable.model import Payable
from app.modules.payment_request import service as pr_service
from app.modules.payment_request.schema import LineIn, PRequestCreate
from app.modules.purchase_order import service
from app.modules.purchase_order.controller import _out
from app.modules.purchase_order.model import ImportCostType, OrderType, PurchaseOrder
from app.modules.purchase_order.schema import POImportCostIn, POItemIn

RATE = 25_000.0
SRC = service.IMPORT_COST_SOURCE


def _make_po(db, seed, code="PO-NK-P5", **kw):
    kw.setdefault("status", "draft")
    po = PurchaseOrder(code=code, company_id=seed.company_id, supplier_code="NX",
                       supplier_name=seed.sup_name, order_date="2026-09-08",
                       order_type=int(OrderType.IMPORT), currency="USD", exchange_rate=RATE, **kw)
    db.add(po)
    db.flush()
    service._save_items(db, po, [POItemIn(
        product_code="SP01", product_name="Hàng nhập", item_group="Nhãn", unit="cái",
        qty_request=1, qty_order=4, price=100, vat=0, required_date="2026-09-20",
        warehouse_code="KHO01")], user_id=1)
    db.flush()
    return po


def _cost_in(**kw):
    base = dict(cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Cước biển",
                supplier_code="HANGTAU", supplier_name="Hãng tàu ABC",
                currency="VND", amount=1_000_000, vat=8)
    base.update(kw)
    return POImportCostIn(**base)


def _save_costs(db, po, costs):
    service._save_import_costs(db, po, costs, user_id=1)
    db.flush()


def _cost_payables(db, po):
    return (db.query(Payable).filter(Payable.po_id == po.id, Payable.ref_type == SRC)
            .order_by(Payable.ref_id).all())


# ── Sinh nợ theo trạng thái đơn ──────────────────────────────────────────────────
def test_don_nhap_khong_sinh_no(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in()])
    assert _cost_payables(db, po) == []
    out = _out(db, po)
    row = out["import_costs"][0]
    # Chưa thành nợ: payable_id = 0, còn lại = tổng dòng để màn hình vẫn cộng được
    assert row["payable_id"] == 0 and row["paid_amount"] == 0
    assert row["remaining"] == 1_080_000.0
    assert out["import_cost_summary"]["paid_total"] == 0
    assert out["import_cost_summary"]["remaining_total"] == 1_080_000.0


def test_duyet_don_moi_dong_chi_phi_thanh_mot_khoan_no(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [
        _cost_in(payment_due_date="2026-10-15", invoice_no="HD-001", invoice_date="2026-09-10"),
        _cost_in(cost_type=int(ImportCostType.IMPORT_DUTY), description="Thuế NK",
                 supplier_code="NSNN", supplier_name="Ngân sách nhà nước", amount=500_000, vat=0),
    ])
    service.set_status(db, po.id, "approved", user_id=1)

    pays = _cost_payables(db, po)
    rows = service.import_costs_of(db, po.id)
    assert [p.ref_id for p in pays] == [r.id for r in rows]
    freight, duty = pays
    assert freight.source_type == SRC and freight.ref_type == SRC
    assert freight.supplier_code == "HANGTAU" and freight.po_code == po.code
    # 1.000.000 trước VAT + 8% = 1.080.000; hạn trả lấy đúng ô của dòng, ngày phát sinh = ngày HĐ
    assert float(freight.amount) == 1_000_000.0 and float(freight.vat) == 80_000.0
    assert float(freight.total) == float(freight.remaining) == 1_080_000.0
    assert freight.invoice_no == "HD-001" and freight.incur_date == "2026-09-10"
    assert freight.due_date == "2026-10-15" and freight.status == "unpaid"
    # Thuế nhập khẩu = khoản nợ với NCC "Ngân sách nhà nước"; không có ngày HĐ thì lấy ngày đặt
    assert duty.supplier_code == "NSNN" and float(duty.total) == 500_000.0
    assert duty.incur_date == po.order_date

    out = _out(db, po)
    assert [r["payable_id"] for r in out["import_costs"]] == [freight.id, duty.id]
    summary = out["import_cost_summary"]
    assert summary["cost_total"] == 1_580_000.0 and summary["paid_total"] == 0
    assert summary["remaining_total"] == 1_580_000.0
    by_sup = {s["supplier_code"]: s for s in summary["by_supplier"]}
    assert by_sup["HANGTAU"]["unpaid_payable_ids"] == [freight.id]
    assert by_sup["NSNN"]["unpaid_payable_ids"] == [duty.id]
    assert out["unpaid_total"] == 1_580_000.0


def test_khai_them_sua_va_xoa_dong_sau_duyet_no_chay_theo(db, seed):
    po = _make_po(db, seed)
    service.set_status(db, po.id, "approved", user_id=1)
    _save_costs(db, po, [_cost_in()])
    (pay,) = _cost_payables(db, po)
    row_id = service.import_costs_of(db, po.id)[0].id

    # Sửa số tiền → cùng khoản nợ (idempotent), tổng đổi theo
    _save_costs(db, po, [_cost_in(id=row_id, amount=2_000_000, vat=0)])
    (pay2,) = _cost_payables(db, po)
    assert pay2.id == pay.id and float(pay2.total) == 2_000_000.0

    # Bỏ NCC → không còn biết trả cho ai → gỡ nợ (chưa chi)
    _save_costs(db, po, [_cost_in(id=row_id, supplier_code="", supplier_name="")])
    assert _cost_payables(db, po) == []

    # Chọn lại NCC → nợ quay lại; xóa dòng → nợ mất
    _save_costs(db, po, [_cost_in(id=row_id)])
    assert len(_cost_payables(db, po)) == 1
    _save_costs(db, po, [])
    assert _cost_payables(db, po) == []
    assert service.import_costs_of(db, po.id) == []


def test_dong_da_chi_thi_khong_xoa_duoc(db, seed):
    po = _make_po(db, seed)
    service.set_status(db, po.id, "approved", user_id=1)
    _save_costs(db, po, [_cost_in()])
    (pay,) = _cost_payables(db, po)
    pay.paid_amount = 300_000
    db.flush()

    with pytest.raises(HTTPException) as e:
        _save_costs(db, po, [])
    assert e.value.status_code == 400 and "đã chi" in e.value.detail
    assert len(service.import_costs_of(db, po.id)) == 1


def test_huy_don_go_no_chua_chi_giu_no_da_chi(db, seed):
    po = _make_po(db, seed)
    service.set_status(db, po.id, "approved", user_id=1)
    _save_costs(db, po, [_cost_in(), _cost_in(description="Phí cảng", amount=200_000, vat=0)])
    unpaid, paid = _cost_payables(db, po)
    paid.paid_amount = 200_000
    db.flush()

    service.set_status(db, po.id, "cancelled", user_id=1)
    left = _cost_payables(db, po)
    assert [p.id for p in left] == [paid.id]


# ── Hoàn thành đơn nhập khẩu phải trả đủ chi phí (09/09, khách chốt mức chặt) ─────────
def test_don_nk_con_chi_phi_chua_tra_thi_khong_hoan_thanh_duoc(db, seed):
    po = _make_po(db, seed)
    service.set_status(db, po.id, "approved", user_id=1)
    _save_costs(db, po, [
        _cost_in(description="Cước biển chặng 1"),
        _cost_in(cost_type=int(ImportCostType.IMPORT_DUTY), description="",
                 supplier_code="NSNN", supplier_name="Ngân sách nhà nước", amount=500_000, vat=0),
    ])
    freight, duty = _cost_payables(db, po)
    freight.paid_amount = 1_080_000
    db.flush()

    with pytest.raises(HTTPException) as e:
        service.block_complete_unpaid_import_costs(db, po)
    assert e.value.status_code == 400
    # Khoản đã trả đủ không bị kể; khoản chưa trả nêu tên (không có diễn giải thì lấy tên loại) + NCC + số còn
    assert "Còn 1 khoản" in e.value.detail
    assert "Cước biển chặng 1" not in e.value.detail
    assert "Thuế nhập khẩu (Ngân sách nhà nước): còn 500,000 đ" in e.value.detail

    duty.paid_amount = 500_000
    db.flush()
    service.block_complete_unpaid_import_costs(db, po)   # trả đủ thì qua


def test_dong_chi_phi_co_tien_nhung_chua_chon_ncc_cung_chan_hoan_thanh(db, seed):
    """Không có NCC thì không có công nợ, tức không có đường nào để trả — đóng đơn là mất dấu khoản đó."""
    po = _make_po(db, seed)
    service.set_status(db, po.id, "approved", user_id=1)
    _save_costs(db, po, [_cost_in(supplier_code="", supplier_name="", description="Phí lưu bãi")])
    assert _cost_payables(db, po) == []

    with pytest.raises(HTTPException) as e:
        service.block_complete_unpaid_import_costs(db, po)
    assert "Phí lưu bãi: chưa thành công nợ" in e.value.detail


def test_don_trong_nuoc_va_don_khong_co_chi_phi_khong_bi_chan(db, seed):
    po_nk = _make_po(db, seed)
    service.set_status(db, po_nk.id, "approved", user_id=1)
    service.block_complete_unpaid_import_costs(db, po_nk)   # chưa khai chi phí → qua

    po_tn = _make_po(db, seed, code="PO-TN-P5")
    po_tn.order_type = int(OrderType.DOMESTIC)
    po_tn.currency, po_tn.exchange_rate = "VND", 1
    db.flush()
    service.set_status(db, po_tn.id, "approved", user_id=1)
    _save_costs(db, po_tn, [_cost_in()])
    service.block_complete_unpaid_import_costs(db, po_tn)   # đơn trong nước giữ luật cũ


# ── Tạo Yêu cầu thanh toán từ nợ chi phí ────────────────────────────────────────
def test_tao_yctt_tach_moi_ncc_mot_phieu_va_chi_tien_tru_dung_khoan(db, seed):
    po = _make_po(db, seed)
    service.set_status(db, po.id, "approved", user_id=1)
    _save_costs(db, po, [
        _cost_in(invoice_no="HD-001"),
        _cost_in(description="Phí cảng", amount=200_000, vat=0),                     # chưa có số HĐ
        _cost_in(cost_type=int(ImportCostType.IMPORT_DUTY), description="Thuế NK",
                 supplier_code="NSNN", supplier_name="Ngân sách nhà nước", amount=500_000, vat=0),
    ])
    freight, port, duty = _cost_payables(db, po)

    reqs = pr_service.create_requests(db, PRequestCreate(
        request_date="2026-09-09", lines=[LineIn(payable_id=p.id) for p in (freight, port, duty)]),
        user_id=1)
    by_sup = {r.supplier_code: r for r in reqs}
    assert set(by_sup) == {"HANGTAU", "NSNN"}
    assert all(r.source_type == SRC for r in reqs)
    assert float(by_sup["HANGTAU"].total) == 1_280_000.0
    assert float(by_sup["NSNN"].total) == 500_000.0

    # Gửi duyệt: dòng chưa có số HĐ bị chặn; gõ số HĐ ngay trên phiếu thì khớp theo payable_id
    hangtau = by_sup["HANGTAU"]
    with pytest.raises(HTTPException) as e:
        pr_service.check_submit(db, hangtau)
    assert "chưa có Số hóa đơn" in e.value.detail
    for ln in pr_service.lines_of(db, hangtau.id):
        if ln.payable_id == port.id:
            ln.invoice_no = "HD-002"
    db.flush()
    pr_service.check_submit(db, hangtau)

    pr_service.set_status(db, hangtau.id, "submitted", user_id=1)
    pr_service.set_status(db, hangtau.id, "approved", user_id=1)
    pr_service.set_status(db, hangtau.id, "paid", user_id=1)
    db.refresh(freight); db.refresh(port); db.refresh(duty)
    assert float(freight.paid_amount) == 1_080_000.0 and freight.status == "paid"
    assert float(port.paid_amount) == 200_000.0 and port.status == "paid"
    assert float(duty.paid_amount) == 0

    out = _out(db, po)
    summary = out["import_cost_summary"]
    assert summary["paid_total"] == 1_280_000.0 and summary["remaining_total"] == 500_000.0
    sup = {s["supplier_code"]: s for s in summary["by_supplier"]}
    assert sup["HANGTAU"]["remaining"] == 0 and sup["HANGTAU"]["unpaid_payable_ids"] == []
    assert sup["NSNN"]["unpaid_payable_ids"] == [duty.id]
    assert out["unpaid_total"] == 500_000.0


def test_yctt_go_tay_chap_nhan_loai_import_cost(db, seed):
    (req,) = pr_service.create_requests(db, PRequestCreate(
        supplier_code="NX", company_id=seed.company_id, source_type=SRC,
        lines=[LineIn(po_code="PO-X", invoice_no="HD-9", amount=100)]), user_id=1)
    assert req.source_type == SRC
