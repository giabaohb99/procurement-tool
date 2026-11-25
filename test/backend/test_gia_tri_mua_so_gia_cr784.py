"""duoc-CR-784 — GIÁ TRỊ MUA của Lịch sử mua hàng = thành tiền của sổ Misa (cột `amount` của sổ giá), không phải giá x số lượng:
nạp từ tệp HTML / JSON và từ Excel (nạp lại cùng tệp thì BỔ SUNG thành tiền cho dòng cũ, không tạo dòng trùng), nguồn 1 tính từ tiền
dòng lịch sử (bỏ VAT, quy VNĐ), nguồn 2 để trống, lịch sử hiện thành tiền khi có và giá x SL khi không; tổng giá trị + giá bình quân gia
quyền cộng đúng giá trị đó. Ví dụ bản mẫu: dòng Misa 2326 NHG3790 18/08/2025 = 7.121.169, không phải 7.121.134,8."""
from datetime import date
from decimal import Decimal

import openpyxl
import pytest

from app.core.packaging_price_codes import PriceSourceType
from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule, ImportStatus
from app.modules.packaging_cost import misa_xlsx_import
from app.modules.packaging_cost.history_service import build_history
from app.modules.product_price import ledger_sync_service as sync
from app.modules.product_price.misa_ledger_import import build_misa_rows, import_misa_rows
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.purchase_history.model import PurchaseHistory
from so_gia_factory_cr784 import add_ledger, add_products, make_item, make_po

MISA = int(PriceSourceType.MISA)
ROW_2326 = [2326, "2025-08-18", "CÔNG TY TNHH QUẢNG CÁO MỘC ẤN - VTBB", "NHG3790", 9204, 773.7, "NCC0186",
            "Kho DEGO Đồng Tháp - Thuê tại kho NTV", 7121169]
HEAD = ["Ngày hạch toán", "Mã nhà cung cấp", "Tên nhà cung cấp", "Tên kho", "Mã hàng", "Tên hàng", "ĐVT", "Số lượng", "Đơn giá", "Giá trị"]


def _src(*rows):
    return {"vtbb": {"NHG3790": ["Nhãn", "Nhãn", "Cái"]}, "mua": [list(r) for r in rows]}


def _amounts(db, code="NHG3790"):
    return [r.amount for r in db.query(L).filter(L.product_code == code).order_by(L.price_date, L.id)]


# ── Nạp tệp HTML / JSON ─────────────────────────────────────────────────────────
def test_doc_thanh_tien_tu_chi_so_8_dong_gia_0_hoac_thieu_thi_trong():
    rows, _ = build_misa_rows(_src(ROW_2326, [2327, "2025-08-19", "A", "NHG3790", 10, 0, "N", "K", 500],
                                   [2328, "2025-08-20", "A", "NHG3790", 10, 5, "N", "K", None],
                                   [2329, "2025-08-21", "A", "NHG3790", 10, 5, "N", "K"]), 1)
    assert [r["amount"] for r in rows] == [Decimal("7121169.00"), None, None, None]


def test_nap_lai_json_bo_sung_thanh_tien_cho_dong_da_nap_khong_tao_dong_trung(db):
    old, _ = build_misa_rows(_src(ROW_2326[:8]), 1)             # tệp cũ chưa có thành tiền
    import_misa_rows(db, old)
    db.commit()
    first_id = db.query(L.id).scalar()
    assert _amounts(db) == [None]
    new, _ = build_misa_rows(_src(ROW_2326), 1)
    stats = import_misa_rows(db, new)
    db.commit()
    assert (stats["updated"], stats["inserted"]) == (1, 0) and db.query(L.id).scalar() == first_id
    assert _amounts(db) == [Decimal("7121169.00")]


def test_lich_su_hien_gia_tri_misa_khong_phai_gia_nhan_so_luong_va_tong_cong_dung_gia_tri_do(db):
    add_products(db, ("NHG3790", "Nhãn", "Cái"))
    import_misa_rows(db, build_misa_rows(_src(ROW_2326), 1)[0])
    add_ledger(db, "NHG3790", 100, "2025-09-01", qty=10, doc_id=7)      # sau mốc Misa, từ ĐMH thật, không có thành tiền: giá x SL
    add_ledger(db, "NHG3790", 0, "2025-09-02", qty=5, doc_id=8)                                             # giá 0: không có giá trị
    db.commit()
    res = build_history(db, codes=["NHG3790"])
    by_date = {r["date"]: r for r in res["items"]}
    assert by_date["2025-08-18"]["amount"] == 7121169 and by_date["2025-08-18"]["price"] == 773.7
    assert by_date["2025-09-01"]["amount"] == 1000 and by_date["2025-09-02"]["amount"] is None
    stats = res["stats"]
    assert stats["amount_total"] == 7121169 + 1000
    assert stats["weighted_avg"] == pytest.approx((7121169 + 1000) / (9204 + 10), abs=1e-3)        # BQ gia quyền = tổng giá trị / tổng SL có giá
    sort_desc = [r["date"] for r in build_history(db, codes=["NHG3790"], sort_by="amount", sort_dir="desc")["items"]]
    assert sort_desc == ["2025-08-18", "2025-09-01", "2025-09-02"]                                 # giá 0 (ô trống) xuống cuối


# ── Nạp Excel ───────────────────────────────────────────────────────────────────
def _wb(rows, head=HEAD):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sổ chi tiết mua hàng"
    ws.append(head)
    for r in rows:
        ws.append(r)
    return wb


def _run(db, seed, wb, apply=True):
    batch = ImportBatch(module=int(ImportModule.PACKAGING_MISA), mode=int(ImportMode.APPLY if apply else ImportMode.DRY_RUN),
                        filename="x.xlsx", status=int(ImportStatus.RUNNING), created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(batch)
    db.commit()
    misa_xlsx_import.run(db, batch, wb, apply=apply)
    db.refresh(batch)
    return batch


X1 = ["18/08/2025", "NCC0186", "MỘC ẤN - VTBB", "Kho A", "NHG3790", "Nhãn", "Cái", 9204, 773.7, 7121169]
X2 = ["19/08/2025", "NCC0186", "MỘC ẤN - VTBB", "Kho A", "NHG3790", "Nhãn", "Cái", 100, 0, 5000]             # giá 0: bỏ thành tiền
X3 = ["20/08/2025", "NCC0186", "MỘC ẤN - VTBB", "Kho A", "NHG3790", "Nhãn", "Cái", 10, 5, None]                # thiếu thành tiền


def test_excel_doc_thanh_tien_va_nap_lai_cung_tep_bo_sung_cho_dong_cu_khong_nhan_doi(db, seed):
    no_amount = _wb([r[:9] for r in (X1, X2, X3)], head=HEAD[:9])                  # tệp cũ không có cột Giá trị
    _run(db, seed, no_amount)
    ids = [r.id for r in db.query(L).order_by(L.price_date)]
    assert _amounts(db) == [None, None, None]
    dry = _run(db, seed, _wb([X1, X2, X3]), apply=False)
    assert (dry.created_count, dry.updated_count, dry.deleted_count) == (0, 1, 0) and _amounts(db) == [None, None, None]     # chạy thử không ghi
    batch = _run(db, seed, _wb([X1, X2, X3]))
    assert (batch.created_count, batch.updated_count, batch.deleted_count) == (0, 1, 0)
    assert [r.id for r in db.query(L).order_by(L.price_date)] == ids and db.query(L).count() == 3
    assert _amounts(db) == [Decimal("7121169.00"), None, None]
    again = _run(db, seed, _wb([X1, X2, X3]))
    assert (again.created_count, again.updated_count, again.skipped_count) == (0, 0, 3)                 # lần ba: không đổi gì
    #  Tệp không có cột Giá trị không được xóa thành tiền đã có
    _run(db, seed, _wb([r[:9] for r in (X1, X2, X3)], head=HEAD[:9]))
    assert _amounts(db) == [Decimal("7121169.00"), None, None]
    #  Sửa thành tiền trong tệp thì dòng đó được sửa theo (cùng nội dung, cùng id)
    fixed = list(X1)
    fixed[9] = 7121200
    _run(db, seed, _wb([fixed, X2, X3]))
    assert _amounts(db)[0] == Decimal("7121200.00") and db.query(L).count() == 3


def test_excel_hai_dong_trung_noi_dung_giu_nguyen_so_dong_va_dien_thanh_tien_cho_tung_dong(db, seed):
    twin = [X1[:9], X1[:9]]
    _run(db, seed, _wb(twin, head=HEAD[:9]))
    assert db.query(L).count() == 2
    _run(db, seed, _wb([X1, X1]))
    assert db.query(L).count() == 2 and _amounts(db) == [Decimal("7121169.00")] * 2


# ── Nguồn 1 / 2 ─────────────────────────────────────────────────────────────────
def _history(db, **over):
    base = dict(po_item_id=None, po_id=0, source="system", product_code="NHG3790", supplier_code="NCC01", company_id=1,
                order_date="2026-10-01", price=1000, vat=8, qty_order=10, amount=10800, created_by=0, updated_by=0)
    base.update(over)
    ph = PurchaseHistory(**base)
    db.add(ph)
    db.commit()
    return ph


def test_thanh_tien_lich_su_bo_vat_quy_vnd_dong_tien_0_hoac_gia_0_la_none(db):
    ph = _history(db)
    assert sync.history_amount(ph, 1) == Decimal("10000.00")                                  # 10.800 gồm VAT 8% -> 10.000
    assert sync.history_amount(ph, 25000) == Decimal("250000000.00")
    assert sync.history_amount(_history(db, amount=0), 1) is None
    assert sync.history_amount(_history(db, vat=0, amount=5000), None) == Decimal("5000.00")        # tỉ giá trống đọc là 1
    assert sync.values_from_history(_history(db, price=0), 1)["amount"] is None                    # dòng giá 0 không có giá trị


def test_dong_so_gia_moi_chen_tu_lich_su_co_thanh_tien_con_dong_dmh_dang_mo_thi_trong(db):
    po = make_po(db, status="approved")
    make_item(db, po, product_code="NHG3790", qty_order=10, price=1000, amount=10800)
    sync.sync_po_price_ledger(db, po)
    assert db.query(L).one().amount is None and db.query(L).one().source_type == int(PriceSourceType.PO_LINE)
    _history(db, order_date="2026-09-01")
    sync.sync_history_ledger(db)
    db.commit()
    by_type = {r.source_type: r.amount for r in db.query(L)}
    assert by_type[int(PriceSourceType.PURCHASE_HISTORY)] == Decimal("10000.00") and by_type[int(PriceSourceType.PO_LINE)] is None


def test_backfill_dien_thanh_tien_cho_dong_lich_su_da_co_chay_lai_khong_doi_va_chay_thu_khong_ghi(db):
    ph = _history(db)
    sync.sync_history_ledger(db)
    db.commit()
    db.query(L).update({L.amount: None})                      # giả lập dòng chèn từ trước khi sổ có cột thành tiền
    db.commit()
    dry = sync.sync_history_ledger(db, dry_run=True)
    assert dry["updated_amount"] == 1 and db.query(L).one().amount is None
    stats = sync.sync_history_ledger(db)
    db.commit()
    assert stats["updated_amount"] == 1 and db.query(L).one().amount == Decimal("10000.00") and stats["inserted"] == 0
    assert sync.sync_history_ledger(db)["updated_amount"] == 0
    ph.amount = 0
    db.commit()
    db.query(L).update({L.amount: None})
    db.commit()
    assert sync.sync_history_ledger(db)["updated_amount"] == 0 and db.query(L).one().amount is None       # tiền 0: giữ trống, không quét lặp


def test_script_backfill_tinh_thanh_tien_vao_so_lech(db):
    from scripts.backfill_product_price_ledger import changes_of
    assert changes_of({"updated_amount": 3}) == 3
