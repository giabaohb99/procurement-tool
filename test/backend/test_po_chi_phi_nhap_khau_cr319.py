"""bao-CR-319 P3 — chi phí lô hàng nhập khẩu + khóa VAT dòng hàng.

Hai thứ dễ hỏng âm thầm được canh ở đây:
1. VAT dòng hàng của đơn NHẬP KHẨU phải luôn bằng 0. Thuế GTGT hàng nhập nộp ngân sách
   nhà nước và đã khai thành một dòng chi phí; gõ thêm VAT ở dòng hàng là cộng thuế hai
   lần VÀ ghi nợ khoản thuế đó cho chính NCC nước ngoài — người không nhận đồng nào.
2. Chi phí phải được sửa SAU khi đơn đã duyệt. Hóa đơn cước, tờ khai thuế, phí lưu bãi
   đều về sau ngày duyệt; khóa chung với phần đã duyệt là không đơn nào ghi được chi phí.
"""
import pytest
from fastapi import HTTPException

from app.modules.purchase_order import service
from app.modules.purchase_order.model import (AllocationMethod, IMPORT_COST_TAX_TYPES,
                                              ImportCostType, OrderType, POImportCost,
                                              PurchaseOrder)
from app.modules.purchase_order.schema import DeliveryIn, POImportCostIn, POItemIn, POUpdate
from app.modules.payable.model import Payable

RATE = 25_000.0


def _make_po(db, seed, **kw):
    kw.setdefault("order_type", int(OrderType.IMPORT))
    kw.setdefault("currency", "USD")
    kw.setdefault("exchange_rate", RATE)
    kw.setdefault("status", "draft")
    po = PurchaseOrder(code=kw.pop("code", "PO-NK-001"), company_id=seed.company_id,
                       supplier_code="NX", supplier_name=seed.sup_name,
                       order_date="2026-09-08", **kw)
    db.add(po)
    db.flush()
    return po


def _item_in(**kw):
    base = dict(product_code="SP01", product_name="Hàng nhập", item_group="Nhãn",
                unit="cái", qty_request=2, qty_order=2, price=10, vat=0,
                required_date="2026-09-20", warehouse_code="KHO01")
    base.update(kw)
    return POItemIn(**base)


def _cost_in(**kw):
    base = dict(cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Cước biển",
                supplier_code="HANGTAU", supplier_name="Hãng tàu ABC", amount=1_000_000, vat=8)
    base.update(kw)
    return POImportCostIn(**base)


# ── Khóa VAT dòng hàng của đơn nhập khẩu ────────────────────────────────────────
def test_don_nhap_khau_ep_vat_dong_hang_ve_0(db, seed):
    po = _make_po(db, seed)
    service._save_items(db, po, [_item_in(vat=10, deliveries=[DeliveryIn(
        received_qty=2, received_date="2026-09-10", warehouse_code="KHO01")])], user_id=1)
    db.flush()
    service.recompute_effects(db, po, user_id=1)
    db.flush()

    it = service.items_of(db, po.id)[0]
    assert float(it.vat) == 0
    # Tiền hàng đúng 2 × 10 USD, KHÔNG có 10% cộng thêm ở bất kỳ đâu
    assert float(it.amount) == 20.0
    assert float(it.base_amount) == 20.0 * RATE
    pay = db.query(Payable).filter(Payable.po_id == po.id, Payable.source_type == "goods").one()
    assert float(pay.vat) == 0


def test_don_trong_nuoc_giu_nguyen_vat_nguoi_dung_nhap(db, seed):
    """Chốt chặn hồi quy: khóa VAT chỉ áp cho đơn nhập khẩu, đơn thường không đổi."""
    po = _make_po(db, seed, code="PO-TN-001", order_type=int(OrderType.DOMESTIC),
                  currency="VND", exchange_rate=1)
    service._save_items(db, po, [_item_in(vat=10)], user_id=1)
    db.flush()

    assert float(service.items_of(db, po.id)[0].vat) == 10


def test_doi_don_sang_nhap_khau_thi_lan_luu_sau_vat_ve_0(db, seed):
    """Đơn lập nhầm loại rồi sửa lại: lần lưu kế tiếp phải dọn VAT cũ, không để sót."""
    po = _make_po(db, seed, code="PO-TN-002", order_type=int(OrderType.DOMESTIC),
                  currency="VND", exchange_rate=1)
    service._save_items(db, po, [_item_in(vat=10)], user_id=1)
    db.flush()
    it_id = service.items_of(db, po.id)[0].id

    po.order_type = int(OrderType.IMPORT)
    service._save_items(db, po, [_item_in(id=it_id, vat=10)], user_id=1)
    db.flush()

    assert float(service.items_of(db, po.id)[0].vat) == 0


# ── Lưu bảng chi phí ────────────────────────────────────────────────────────────
def test_dong_chi_phi_thua_huong_loai_tien_cua_don(db, seed):
    po = _make_po(db, seed)
    service._save_import_costs(db, po, [_cost_in()], user_id=1)
    db.flush()

    c = service.import_costs_of(db, po.id)[0]
    assert c.currency == "USD"
    assert float(c.exchange_rate) == RATE


def test_dong_chi_phi_tra_bang_tien_viet_khong_dinh_ty_gia_cua_don(db, seed):
    """Cước nội địa trả bằng VNĐ nằm trong đơn USD — nhân tỷ giá đơn vào là phồng 25.000 lần."""
    po = _make_po(db, seed)
    service._save_import_costs(db, po, [_cost_in(currency="VND", amount=2_000_000, vat=0)], user_id=1)
    db.flush()

    c = service.import_costs_of(db, po.id)[0]
    assert float(c.exchange_rate) == 1.0
    assert float(c.base_amount) == 2_000_000


def test_base_amount_gom_ca_vat_va_ty_gia(db, seed):
    po = _make_po(db, seed)
    service._save_import_costs(db, po, [_cost_in(currency="USD", amount=100, vat=8)], user_id=1)
    db.flush()

    c = service.import_costs_of(db, po.id)[0]
    assert float(c.amount) == 100                      # nguyên tệ, TRƯỚC thuế
    assert float(c.base_amount) == 100 * 1.08 * RATE   # đã gồm VAT, đã quy đổi


def test_loai_chi_phi_la_thue_van_luu_duoc_ncc_ngan_sach(db, seed):
    po = _make_po(db, seed)
    service._save_import_costs(db, po, [_cost_in(
        cost_type=int(ImportCostType.IMPORT_DUTY), description="Thuế nhập khẩu",
        supplier_code="NSNN", supplier_name="Ngân sách nhà nước",
        currency="VND", amount=5_000_000, vat=0)], user_id=1)
    db.flush()

    c = service.import_costs_of(db, po.id)[0]
    assert c.cost_type == int(ImportCostType.IMPORT_DUTY)
    assert c.supplier_code == "NSNN"
    assert ImportCostType(c.cost_type) in IMPORT_COST_TAX_TYPES


def test_ma_loai_chi_phi_la_thi_ve_chi_phi_khac(db, seed):
    """Mã lạ (payload cũ / gọi thẳng API) không được rơi vào cột theo kiểu im lặng."""
    po = _make_po(db, seed)
    service._save_import_costs(db, po, [_cost_in(cost_type=777)], user_id=1)
    db.flush()

    assert service.import_costs_of(db, po.id)[0].cost_type == int(ImportCostType.OTHER)


def test_chia_theo_chi_dinh_ma_khong_chon_ma_hang_thi_ve_theo_gia_tri(db, seed):
    po = _make_po(db, seed)
    service._save_import_costs(db, po, [_cost_in(
        allocation_method=int(AllocationMethod.BY_PRODUCT), allocation_target="")], user_id=1)
    db.flush()

    assert service.import_costs_of(db, po.id)[0].allocation_method == int(AllocationMethod.BY_VALUE)


# ── Nhập tay: tổng phải khớp số quy đổi, chỉ giữ khóa của dòng hàng còn tồn tại ──
def _po_hai_dong(db, seed, code="PO-NK-NT"):
    po = _make_po(db, seed, code=code)
    service._save_items(db, po, [_item_in(product_code="SP01"), _item_in(product_code="SP02")], user_id=1)
    db.flush()
    return po, [it.id for it in service.items_of(db, po.id)]


def test_nhap_tay_khop_tong_thi_luu_json_theo_id_dong_hang(db, seed):
    po, (id1, id2) = _po_hai_dong(db, seed)
    # 1.000.000 VNĐ + VAT 8% = 1.080.000 (chi phí trả bằng VNĐ nên tỷ giá 1)
    service._save_import_costs(db, po, [_cost_in(
        currency="VND", allocation_method=int(AllocationMethod.MANUAL),
        manual_allocation={str(id1): 1_000_000, str(id2): 80_000, "999999": 5})], user_id=1)
    db.flush()

    row = service.import_costs_of(db, po.id)[0]
    assert row.allocation_method == int(AllocationMethod.MANUAL)
    # Khóa của dòng hàng không tồn tại bị bỏ, số còn lại giữ nguyên
    assert service.parse_manual_allocation(row.manual_allocation) == {str(id1): 1_000_000.0, str(id2): 80_000.0}


def test_nhap_tay_lech_tong_thi_chan_400(db, seed):
    po, (id1, id2) = _po_hai_dong(db, seed, code="PO-NK-NT2")
    with pytest.raises(HTTPException) as exc:
        service._save_import_costs(db, po, [_cost_in(
            currency="VND", allocation_method=int(AllocationMethod.MANUAL),
            manual_allocation={str(id1): 500_000, str(id2): 500_000})], user_id=1)
    assert exc.value.status_code == 400
    assert "1,080,000" in exc.value.detail


def test_nhap_tay_chua_go_dong_nao_thi_chan_400(db, seed):
    po, _ids = _po_hai_dong(db, seed, code="PO-NK-NT3")
    with pytest.raises(HTTPException) as exc:
        service._save_import_costs(db, po, [_cost_in(
            currency="VND", allocation_method=int(AllocationMethod.MANUAL))], user_id=1)
    assert exc.value.status_code == 400
    assert "chưa nhập" in exc.value.detail


def test_doi_sang_cach_khac_thi_xoa_so_nhap_tay(db, seed):
    po, (id1, id2) = _po_hai_dong(db, seed, code="PO-NK-NT4")
    service._save_import_costs(db, po, [_cost_in(
        currency="VND", allocation_method=int(AllocationMethod.MANUAL),
        manual_allocation={str(id1): 1_000_000, str(id2): 80_000})], user_id=1)
    db.flush()
    cid = service.import_costs_of(db, po.id)[0].id

    service._save_import_costs(db, po, [_cost_in(
        id=cid, currency="VND", allocation_method=int(AllocationMethod.BY_VALUE),
        manual_allocation={str(id1): 1_000_000, str(id2): 80_000})], user_id=1)
    db.flush()
    row = service.import_costs_of(db, po.id)[0]
    assert row.allocation_method == int(AllocationMethod.BY_VALUE)
    assert (row.manual_allocation or "") == ""


def test_luu_lai_thi_upsert_theo_id_va_xoa_dong_khong_con_gui_len(db, seed):
    po = _make_po(db, seed)
    service._save_import_costs(db, po, [_cost_in(), _cost_in(
        cost_type=int(ImportCostType.STORAGE), description="Lưu bãi", amount=200)], user_id=1)
    db.flush()
    rows = service.import_costs_of(db, po.id)
    assert len(rows) == 2
    giu_id = rows[0].id

    service._save_import_costs(db, po, [_cost_in(id=giu_id, amount=1_500_000)], user_id=1)
    db.flush()
    rows = service.import_costs_of(db, po.id)
    assert [r.id for r in rows] == [giu_id]
    assert float(rows[0].amount) == 1_500_000


def test_khong_gui_khoa_import_costs_thi_giu_nguyen_bang(db, seed):
    """Màn hình không đụng tới bảng chi phí (None) khác hẳn với xóa hết (mảng rỗng)."""
    po = _make_po(db, seed)
    service._save_import_costs(db, po, [_cost_in()], user_id=1)
    db.flush()

    service._save_import_costs(db, po, None, user_id=1)
    db.flush()
    assert len(service.import_costs_of(db, po.id)) == 1

    service._save_import_costs(db, po, [], user_id=1)
    db.flush()
    assert service.import_costs_of(db, po.id) == []


# ── Đơn đã duyệt: chi phí vẫn sửa được ──────────────────────────────────────────
def test_don_da_duyet_van_them_duoc_chi_phi(db, seed):
    po = _make_po(db, seed, code="PO-NK-002", status="approved")
    service.block_edit_approved_order(db, po, POUpdate(import_costs=[_cost_in()]))   # không được ném


def test_don_da_duyet_van_chan_sua_o_khac(db, seed):
    po = _make_po(db, seed, code="PO-NK-003", status="approved")
    with pytest.raises(HTTPException):
        service.block_edit_approved_order(db, po, POUpdate(supplier_code="KHAC"))


# ── Xóa đơn thì dọn luôn bảng chi phí ───────────────────────────────────────────
def test_xoa_don_thi_xoa_ca_dong_chi_phi(db, seed):
    po = _make_po(db, seed, code="PO-NK-004")
    service._save_import_costs(db, po, [_cost_in()], user_id=1)
    db.commit()
    pid = po.id

    service.delete_po(db, pid, user_id=1)
    assert db.query(POImportCost).filter(POImportCost.po_id == pid).count() == 0
