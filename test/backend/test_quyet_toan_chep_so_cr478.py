"""bao-CR-478 — QUYẾT TOÁN DÒNG CHI PHÍ: CHÉP SỐ TỪ GIAI ĐOẠN TRƯỚC, KHÔNG CÓ DỰ TOÁN THÌ KHÔNG CHỐT.

Luật đại ca chốt 24/09/2026 khi bỏ dải giai đoạn + nút «Chốt Tạm tính» ở bản cũ:

- Dòng chưa có Tạm tính LẪN Quyết toán mà tick quyết toán → chép Dự toán sang CẢ HAI cột.
- Dòng có Tạm tính, chưa có Quyết toán → chép Tạm tính sang Quyết toán.
- Dòng KHÔNG có Dự toán → không cho quyết toán: lượt chốt BỎ QUA dòng đó, chốt phần còn lại
  và nói ra số dòng bị bỏ qua; không còn dòng nào chốt được thì chặn và kể tên. Không ném lỗi
  cả lượt vì nút «Quyết toán tất cả» của v2 gửi đích danh mọi id chưa chốt.

Trước CR này quyết toán chỉ điền cột Quyết toán, cột Tạm tính để trống — bảng ba cột
nhìn như một khoản chưa từng qua bước tạm tính.
"""
import pytest
from fastapi import HTTPException

from app.modules.purchase_order import service
from app.modules.purchase_order.model import ImportCostType, OrderType, POCost, PurchaseOrder
from app.modules.purchase_order.schema import POImportCostIn, POItemIn


def _make_po(db, seed, code="PO-CP-478"):
    po = PurchaseOrder(code=code, company_id=seed.company_id, supplier_code="NX", supplier_name=seed.sup_name,
                       order_date="2026-09-24", status="approved", order_type=int(OrderType.IMPORT),
                       currency="USD", exchange_rate=25_000.0)
    db.add(po)
    db.flush()
    service._save_items(db, po, [POItemIn(
        product_code="SP01", product_name="Hàng nhập", item_group="Nhãn", unit="cái", qty_request=1,
        qty_order=4, price=100, vat=0, required_date="2026-09-30", warehouse_code="KHO01")], user_id=1)
    db.flush()
    return po


def _cost(**kw):
    base = dict(cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Cước biển",
                supplier_code="HANGTAU", supplier_name="Hãng tàu ABC", currency="VND", vat=0)
    base.update(kw)
    return POImportCostIn(**base)


def _rows(db, po, costs):
    service._save_import_costs(db, po, costs, user_id=1)
    db.flush()
    return db.query(POCost).filter(POCost.po_id == po.id).order_by(POCost.id).all()


def _num(value):
    return None if value is None else float(value)


def test_chi_co_du_toan_thi_chep_sang_ca_tam_tinh_lan_quyet_toan(db, seed):
    po = _make_po(db, seed)
    row = _rows(db, po, [_cost(estimate_amount=1_000_000)])[0]
    service.finalize_cost_lines(db, po, [row.id], user_id=1)
    assert _num(row.provisional_amount) == 1_000_000
    assert _num(row.final_amount) == 1_000_000


def test_co_tam_tinh_thi_quyet_toan_chep_tu_tam_tinh(db, seed):
    po = _make_po(db, seed)
    row = _rows(db, po, [_cost(estimate_amount=1_000_000, provisional_amount=1_200_000)])[0]
    service.finalize_cost_lines(db, po, [row.id], user_id=1)
    assert _num(row.provisional_amount) == 1_200_000          # giữ nguyên số đã gõ
    assert _num(row.final_amount) == 1_200_000


def test_du_lieu_tu_v1_o_trong_luu_thanh_0_van_duoc_chep(db, seed):
    # Bản cũ gửi ô bỏ trống thành 0 (`Number(x) || 0`), không phải null. Chỉ xét None thì luật
    # chép không bao giờ chạy với dữ liệu nhập từ v1.
    po = _make_po(db, seed)
    row = _rows(db, po, [_cost(estimate_amount=1_000_000, provisional_amount=0, final_amount=0)])[0]
    service.finalize_cost_lines(db, po, [row.id], user_id=1)
    assert _num(row.provisional_amount) == 1_000_000
    assert _num(row.final_amount) == 1_000_000


def test_da_go_quyet_toan_thi_giu_nguyen_khong_bia_tam_tinh(db, seed):
    po = _make_po(db, seed)
    row = _rows(db, po, [_cost(estimate_amount=1_000_000, final_amount=950_000)])[0]
    service.finalize_cost_lines(db, po, [row.id], user_id=1)
    assert _num(row.final_amount) == 950_000
    assert row.provisional_amount is None


def test_tick_ca_dong_khong_co_du_toan_thi_bo_qua_dong_do_chot_phan_con_lai(db, seed):
    # Nút «Quyết toán tất cả» của v2 gửi ĐÍCH DANH mọi id chưa chốt — ném lỗi cả lượt thì chỉ một
    # dòng trống Dự toán là cả nút chết. Nên bỏ qua dòng đó và nói ra số dòng bị bỏ qua.
    po = _make_po(db, seed)
    rows = _rows(db, po, [_cost(estimate_amount=1_000_000),
                          _cost(description="Phí lưu bãi", provisional_amount=300_000)])
    ids = [r.id for r in rows]
    done = service.finalize_cost_lines(db, po, ids, user_id=1)
    assert [r.id for r in done] == [rows[0].id]
    assert rows[1].final_amount is None
    assert service.count_costs_missing_estimate(db, po, ids) == 1


def test_chi_con_dong_khong_co_du_toan_thi_chan_va_ke_ten(db, seed):
    po = _make_po(db, seed)
    row = _rows(db, po, [_cost(description="Phí lưu bãi", provisional_amount=300_000)])[0]
    with pytest.raises(HTTPException) as e:
        service.finalize_cost_line(db, po, row.id, user_id=1)
    assert e.value.status_code == 400 and "Phí lưu bãi" in e.value.detail
    assert row.final_amount is None


def test_chot_het_bo_qua_dong_khong_co_du_toan(db, seed):
    po = _make_po(db, seed)
    rows = _rows(db, po, [_cost(estimate_amount=1_000_000),
                          _cost(description="Phí lưu bãi", provisional_amount=300_000)])
    done = service.finalize_cost_lines(db, po, [], user_id=1)
    assert [r.id for r in done] == [rows[0].id]
    assert service.count_costs_missing_estimate(db, po) == 1


def test_du_toan_bang_0_tinh_la_chua_co(db, seed):
    po = _make_po(db, seed)
    row = _rows(db, po, [_cost(estimate_amount=0)])[0]
    with pytest.raises(HTTPException) as e:
        service.finalize_cost_lines(db, po, [], user_id=1)
    assert e.value.status_code == 400 and "chưa có Dự toán" in e.value.detail
    assert row.final_amount is None
