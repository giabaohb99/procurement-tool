"""bao-CR-319 P4 — chia chi phí lô hàng nhập khẩu về từng dòng hàng (chỉ để xem).

Điều phải giữ bằng mọi giá: tổng các phần chia của một khoản LUÔN bằng đúng số tiền khoản
đó (phần lệch làm tròn dồn vào dòng cuối), và khi cơ sở chia trống (chưa gõ kg, SL đặt 0,
mã chỉ định không có trên đơn) thì phải lùi về cách khác VÀ nói rõ, không im lặng đổi.
"""
from app.modules.purchase_order import service
from app.modules.purchase_order.model import AllocationMethod, ImportCostType, OrderType, PurchaseOrder
from app.modules.purchase_order.schema import POImportCostIn, POItemIn

RATE = 25_000.0


def _line(id_, code, order_total, qty=1, kg=0, rate=RATE, name=""):
    return {"id": id_, "product_code": code, "product_name": name or code, "unit": "cái",
            "qty_order": qty, "weight_kg": kg, "order_total": order_total, "exchange_rate": rate}


def _cost(id_, base_amount, method=AllocationMethod.BY_VALUE, target="", description="Cước biển"):
    return {"id": id_, "cost_type": int(ImportCostType.OCEAN_FREIGHT), "cost_type_label": "Cước biển",
            "description": description, "supplier_code": "HANGTAU", "supplier_name": "Hãng tàu",
            "base_amount": base_amount, "allocation_method": int(method), "allocation_target": target}


def _shares(result, cost_id):
    return [next((c["base_amount"] for c in line["costs"] if c["cost_id"] == cost_id), None)
            for line in result["lines"]]


# ── Theo giá trị (mặc định) ─────────────────────────────────────────────────────
def test_chia_theo_gia_tri_dung_ty_le_va_tong_khop():
    # 3 dòng 100 / 200 / 700 USD → 10% / 20% / 70%
    items = [_line(1, "A", 100), _line(2, "B", 200), _line(3, "C", 700)]
    result = service.allocate_import_costs(items, [_cost(9, 1_000_000)])
    assert _shares(result, 9) == [100_000.0, 200_000.0, 700_000.0]
    ratios = [line["costs"][0]["ratio"] for line in result["lines"]]
    assert ratios == [0.1, 0.2, 0.7]
    assert result["cost_total"] == 1_000_000.0
    assert result["goods_base_total"] == 1_000 * RATE
    assert result["landed_total"] == 1_000 * RATE + 1_000_000.0
    assert result["warnings"] == []


def test_phan_lech_lam_tron_don_vao_dong_cuoi():
    # 100 đồng chia đều 3 dòng: 33,33 + 33,33 + 33,34 — dòng cuối gánh phần lệch
    items = [_line(1, "A", 1), _line(2, "B", 1), _line(3, "C", 1)]
    result = service.allocate_import_costs(items, [_cost(9, 100)])
    assert _shares(result, 9) == [33.33, 33.33, 33.34]
    assert sum(_shares(result, 9)) == 100.0


def test_tien_hang_va_tong_moi_dong_bang_hang_cong_chi_phi():
    items = [_line(1, "A", 100), _line(2, "B", 300)]
    result = service.allocate_import_costs(items, [_cost(9, 400), _cost(10, 800)])
    first, second = result["lines"]
    assert first["goods_base"] == 100 * RATE and first["cost_base"] == 300.0
    assert first["landed_base"] == 100 * RATE + 300.0
    assert second["cost_base"] == 900.0
    assert [c["cost_id"] for c in second["costs"]] == [9, 10]


# ── Theo khối lượng / số lượng + lùi về khi cơ sở trống ─────────────────────────
def test_chia_theo_khoi_luong():
    items = [_line(1, "A", 900, kg=1), _line(2, "B", 100, kg=3)]
    result = service.allocate_import_costs(items, [_cost(9, 400, AllocationMethod.BY_WEIGHT)])
    assert _shares(result, 9) == [100.0, 300.0]
    assert result["lines"][0]["costs"][0]["effective_method"] == int(AllocationMethod.BY_WEIGHT)
    assert result["warnings"] == []


def test_khong_co_kg_thi_lui_ve_gia_tri_va_bao_ro():
    items = [_line(1, "A", 100), _line(2, "B", 300)]
    result = service.allocate_import_costs(items, [_cost(9, 400, AllocationMethod.BY_WEIGHT)])
    assert _shares(result, 9) == [100.0, 300.0]
    share = result["lines"][0]["costs"][0]
    assert share["allocation_method"] == int(AllocationMethod.BY_WEIGHT)      # cách ĐÃ CHỌN
    assert share["effective_method"] == int(AllocationMethod.BY_VALUE)        # cách THỰC DÙNG
    assert len(result["warnings"]) == 1 and "khối lượng" in result["warnings"][0]


def test_chia_theo_so_luong():
    items = [_line(1, "A", 500, qty=1), _line(2, "B", 500, qty=4)]
    result = service.allocate_import_costs(items, [_cost(9, 500, AllocationMethod.BY_QUANTITY)])
    assert _shares(result, 9) == [100.0, 400.0]


def test_moi_co_so_deu_trong_thi_chia_deu():
    items = [_line(1, "A", 0, qty=0), _line(2, "B", 0, qty=0)]
    result = service.allocate_import_costs(items, [_cost(9, 100, AllocationMethod.BY_QUANTITY)])
    assert _shares(result, 9) == [50.0, 50.0]
    share = result["lines"][0]["costs"][0]
    assert share["effective_method"] == 0 and share["effective_method_label"] == service.EQUAL_SHARE_LABEL
    assert "chia đều" in result["warnings"][0]


# ── Chỉ định một mã hàng ────────────────────────────────────────────────────────
def test_chi_dinh_ma_thi_chi_dong_do_ganh_dong_trung_ma_chia_nhau():
    # Dòng ĐMH được phép trùng mã: 2 dòng mã B cùng gánh, chia theo giá trị 1:3; dòng A không dính
    items = [_line(1, "A", 1000), _line(2, "B", 100), _line(3, "B", 300)]
    result = service.allocate_import_costs(items, [_cost(9, 400, AllocationMethod.BY_PRODUCT, target="B")])
    assert _shares(result, 9) == [None, 100.0, 300.0]
    assert result["lines"][0]["costs"] == []
    assert result["lines"][0]["landed_base"] == 1000 * RATE
    assert result["warnings"] == []


def test_chi_dinh_ma_khong_co_tren_don_thi_lui_ve_gia_tri_va_bao():
    items = [_line(1, "A", 100), _line(2, "B", 300)]
    result = service.allocate_import_costs(items, [_cost(9, 400, AllocationMethod.BY_PRODUCT, target="ZZZ")])
    assert _shares(result, 9) == [100.0, 300.0]
    assert "ZZZ" in result["warnings"][0]


# ── Biên ─────────────────────────────────────────────────────────────────────────
def test_don_khong_co_dong_hang_thi_khong_do_vo():
    result = service.allocate_import_costs([], [_cost(9, 400)])
    assert result["lines"] == [] and result["cost_total"] == 400.0
    assert result["warnings"]


def test_ma_cach_chia_la_thi_coi_nhu_theo_gia_tri():
    items = [_line(1, "A", 100), _line(2, "B", 300)]
    cost = _cost(9, 400)
    cost["allocation_method"] = 77
    result = service.allocate_import_costs(items, [cost])
    assert _shares(result, 9) == [100.0, 300.0]


# ── Đi qua controller: khóa `import_cost_allocation` có trong payload chi tiết/in ──
def test_out_tra_phan_bo_tinh_tu_du_lieu_da_luu(db, seed):
    from app.modules.purchase_order.controller import _out

    po = PurchaseOrder(code="PO-NK-P4", company_id=seed.company_id, supplier_code="NX",
                       supplier_name=seed.sup_name, order_date="2026-09-08", status="draft",
                       order_type=int(OrderType.IMPORT), currency="USD", exchange_rate=RATE)
    db.add(po)
    db.flush()
    service._save_items(db, po, [
        POItemIn(product_code="SP01", product_name="Hàng 1", item_group="Nhãn", unit="cái",
                 qty_request=1, qty_order=1, price=100, vat=0, required_date="2026-09-20",
                 warehouse_code="KHO01"),
        POItemIn(product_code="SP02", product_name="Hàng 2", item_group="Nhãn", unit="cái",
                 qty_request=1, qty_order=3, price=100, vat=0, required_date="2026-09-20",
                 warehouse_code="KHO01"),
    ], user_id=1)
    service._save_import_costs(db, po, [POImportCostIn(
        cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Cước biển", supplier_code="HANGTAU",
        supplier_name="Hãng tàu", currency="VND", amount=1_000_000, vat=0)], user_id=1)
    db.flush()

    out = _out(db, po)
    alloc = out["import_cost_allocation"]
    assert [line["cost_base"] for line in alloc["lines"]] == [250_000.0, 750_000.0]
    assert alloc["cost_total"] == out["import_cost_summary"]["cost_total"] == 1_000_000.0
    assert alloc["goods_base_total"] == out["import_cost_summary"]["goods_base_total"] == 400 * RATE
    assert alloc["landed_total"] == out["import_cost_summary"]["landed_total"]
