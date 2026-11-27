"""duoc-CR-784 (23/11/2026) — nhập Excel báo giá VTBB (module 5), nạp Sổ chi tiết mua hàng Misa .xlsx (module 6) và tệp mẫu
của cả ba loại nhập trong cụm Giá NVL sản xuất."""
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

import openpyxl
import pytest
from fastapi import HTTPException

from app.core.packaging_price_codes import LedgerLineStage, PriceSourceType
from app.modules.import_tool import controller as imp_ctl
from app.modules.import_tool import service as imp_service
from app.modules.import_tool.catalog_import import ImportValidationError
from app.modules.import_tool.model import ImportBatch, ImportLog, ImportMode, ImportModule, ImportStatus, LogLevel
from app.modules.import_tool.tasks import precheck_headers
from app.modules.packaging_cost import bom_import, misa_xlsx_import, quote_import
from app.modules.packaging_cost.import_templates import TEMPLATES
from app.modules.product_price.misa_cutoff import get_misa_cutoff, set_misa_cutoff
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.product_price.model import ProductPriceQuote
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_ledger, add_products

MISA = int(PriceSourceType.MISA)
MISA_HEAD = ["Ngày hạch toán", "Mã nhà cung cấp", "Tên nhà cung cấp", "Tên kho", "Mã hàng", "Tên hàng", "ĐVT", "Số lượng",
             "Đơn giá", "Giá trị"]


@pytest.fixture
def catalog(db):
    add_products(db, ("CPT0075", "Chai 480ml", "Cái"), ("NAP0056", "Nắp", "Cái"), ("CET0028", "Chai PAPE", "Cái"))


def _batch(db, seed, module, apply=True):
    b = ImportBatch(module=int(module), mode=int(ImportMode.APPLY if apply else ImportMode.DRY_RUN), filename="x.xlsx",
                    status=int(ImportStatus.RUNNING), created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(b)
    db.commit()
    return b


def _run(db, seed, runner, module, wb, apply=True):
    b = _batch(db, seed, module, apply)
    runner.run(db, b, wb, apply=apply)
    db.refresh(b)
    return b


def _messages(db, b, level=None):
    q = db.query(ImportLog).filter(ImportLog.batch_id == b.id)
    if level is not None:
        q = q.filter(ImportLog.level == int(level))
    return [lg.message for lg in q.order_by(ImportLog.id).all()]


def _sheet(head, rows, title="Sheet1", lead=0):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    for _ in range(lead):
        ws.append(["Sổ chi tiết mua hàng"])
    ws.append(head)
    for r in rows:
        ws.append(r)
    return wb


# ── Tệp mẫu ─────────────────────────────────────────────────────────────────────
def test_ba_tep_mau_doc_lai_duoc_va_bo_doc_nhan_dung_dong_tieu_de_khong_nhan_nham_vi_du():
    for module, (name, build) in TEMPLATES.items():
        wb = openpyxl.load_workbook(BytesIO(build()))
        assert wb.sheetnames[-1] == "Hướng dẫn" and name.startswith("mau-")
        if module == ImportModule.PACKAGING_BOM:
            bom_import.precheck(wb)
        elif module == ImportModule.PACKAGING_QUOTE:
            quote_import.precheck(wb)
            assert quote_import.find_header(wb.worksheets[0], quote_import.COLUMNS, quote_import.REQUIRED)[0] == 1
        else:
            misa_xlsx_import.precheck(wb)
            #  Sheet Hướng dẫn có bảng ví dụ nhưng đặt dưới dòng 6 — bộ đọc Misa (quét mọi sheet) không được nhận nó.
            assert [ws.title for _, ws, _, _ in misa_xlsx_import._sheets_with_header(wb)] == ["Sổ chi tiết mua hàng"]


def test_duong_tai_tep_mau_tra_dung_tep_cho_module_5_6_va_4(db, seed, cap_quyen, client_as):  # noqa: F811
    cap_quyen(seed.u_req_id, "import", scope="all", read=True)
    api = client_as(db.get(User, seed.u_req_id))
    for module in (4, 5, 6):
        res = api.get("/api/imports/template", params={"module": module})
        assert res.status_code == 200, res.text
        assert openpyxl.load_workbook(BytesIO(res.content)).sheetnames[-1] == "Hướng dẫn"


# ── Báo giá VTBB ────────────────────────────────────────────────────────────────
QUOTE_HEAD = ["Mã VTBB", "Đơn giá", "Ngày hiệu lực", "Mã NCC", "VAT (%)", "Ghi chú"]


def test_bao_gia_chay_thu_khong_ghi_ghi_that_thi_them_va_lan_hai_thi_sua(db, seed, catalog):
    wb = _sheet(QUOTE_HEAD, [["cpt0075", 2650, "01/12/2026", "NCC0185", 8, "Zalo"],
                             ["NAP0056", "1.250,5", datetime(2026, 12, 1), "", "0,08", ""]])
    dry = _run(db, seed, quote_import, ImportModule.PACKAGING_QUOTE, wb, apply=False)
    assert dry.created_count == 2 and db.query(ProductPriceQuote).count() == 0
    done = _run(db, seed, quote_import, ImportModule.PACKAGING_QUOTE, wb)
    assert done.created_count == 2
    nap = db.query(ProductPriceQuote).filter_by(product_code="NAP0056").one()
    assert nap.price == Decimal("1250.5000") and nap.vat == Decimal("8.00") and nap.valid_from == date(2026, 12, 1)
    #  Cùng mã + NCC + ngày hiệu lực → sửa, không thêm dòng thứ hai.
    again = _run(db, seed, quote_import, ImportModule.PACKAGING_QUOTE,
                 _sheet(QUOTE_HEAD, [["CPT0075", 2700, "01/12/2026", "NCC0185", 8, "Zalo"]]))
    assert (again.created_count, again.updated_count) == (0, 1)
    assert db.query(ProductPriceQuote).filter_by(product_code="CPT0075").one().price == Decimal("2700.0000")
    assert any("2.650 → 2.700" in m for m in _messages(db, again))


def test_bao_gia_dong_loi_bi_bo_khong_lam_hong_ca_lo(db, seed, catalog):
    wb = _sheet(QUOTE_HEAD, [["KHONGCO01", 100, "01/12/2026"], ["CPT0075", 0, "01/12/2026"], ["CPT0075", 100, "32/13/2026"],
                             ["CPT0075", 100, "01/01/1990"], ["CPT0075", 100, "02/12/2026", "", "abc"], [None, None, None]])
    b = _run(db, seed, quote_import, ImportModule.PACKAGING_QUOTE, wb)
    assert b.created_count == 1 and b.error_count == 4 and b.warning_count == 1
    errors = " | ".join(_messages(db, b, LogLevel.ERROR))
    assert "chưa có trong danh mục" in errors and "Đơn giá" in errors and "Ngày hiệu lực" in errors


def test_bao_gia_sai_tep_bi_chan_ngay_luc_tai_len():
    with pytest.raises(ImportValidationError, match="Mã VTBB, Đơn giá, Ngày hiệu lực"):
        precheck_headers(int(ImportModule.PACKAGING_QUOTE), _sheet(["Mã", "Giá"], []))


def test_doc_so_kieu_viet_va_kieu_anh():
    p = quote_import.parse_decimal
    assert p("1.234.567,5", "0.0001") == Decimal("1234567.5000") and p("1,234.5", "0.0001") == Decimal("1234.5000")
    assert p("85,5", "0.0001") == Decimal("85.5000") and p("2.5", "0.0001") == Decimal("2.5000")
    assert p("1.250", "0.0001") == Decimal("1250.0000") and p("", "0.0001") is None and p("abc", "0.0001") is None


# ── Sổ Misa ─────────────────────────────────────────────────────────────────────
def _misa(rows, lead=2):
    return _sheet(MISA_HEAD, rows, title="Sổ chi tiết mua hàng", lead=lead)


R1 = ["17/01/2025", "NCC38", "CÔNG TY PHL - VTBB", "KHO NCC_HÀ LONG", "CET0028", "Chai", "Cái", 12000, 4724, 56688000]
R2 = ["24/12/2025", "NCC0185", "CÔNG TY PHL", "KHO NCC YAMATO", "CET0028", "Chai", "Cái", 5000, 4300, 21500000]
R3 = [46203, "NCC0002", "IDA GLOBAL", "Kho VTBB DEGO Cần Thơ", "CET0028", "Chai", "Cái", 401, 3170, 1271170]   # 30/06/2026


def test_misa_lan_dau_them_du_dat_moc_va_nap_lai_cung_tep_la_khong_doi(db, seed, catalog):
    wb = _misa([R1, R2, R3, ["15/03/2025", "N1", "X", "K", "PPA0001", "", "", 5, 10, 50],
                ["16/03/2025", "N1", "X", "K", "CPT0075", "", "", 0, 10, 0], [None] * 10])
    dry = _run(db, seed, misa_xlsx_import, ImportModule.PACKAGING_MISA, wb, apply=False)
    assert dry.created_count == 3 and db.query(L).filter(L.source_type == MISA).count() == 0 and get_misa_cutoff(db) is None
    b = _run(db, seed, misa_xlsx_import, ImportModule.PACKAGING_MISA, wb)
    rows = db.query(L).filter(L.source_type == MISA).order_by(L.price_date).all()
    assert [(r.price_date, r.price, r.warehouse_name) for r in rows] == [
        (date(2025, 1, 17), Decimal("4724.0000"), "KHO NCC_HÀ LONG"), (date(2025, 12, 24), Decimal("4300.0000"), "KHO NCC YAMATO"),
        (date(2026, 6, 30), Decimal("3170.0000"), "Kho VTBB DEGO Cần Thơ")]
    assert rows[0].supplier_name == "CÔNG TY PHL" and get_misa_cutoff(db) == date(2026, 6, 30)
    summary = _messages(db, b)[0]
    assert "giữ 0, thêm 3, bỏ 0" in summary and "mã PPA / CKC / CPM / CPN 1" in summary and "số lượng 0 1" in summary
    ids = [r.id for r in rows]
    again = _run(db, seed, misa_xlsx_import, ImportModule.PACKAGING_MISA, wb)
    assert (again.created_count, again.deleted_count, again.skipped_count) == (0, 0, 3)
    assert [r.id for r in db.query(L).filter(L.source_type == MISA).order_by(L.price_date)] == ids


def test_misa_nap_mot_thang_khong_dung_toi_dong_ngoai_khoang_va_moc_khong_lui(db, seed, catalog):
    _run(db, seed, misa_xlsx_import, ImportModule.PACKAGING_MISA, _misa([R1, R2, R3]))
    #  Tệp chỉ có tháng 12/2025: lần mua 24/12 đổi giá 4300 → 4350; hai dòng ngoài khoảng giữ nguyên, mốc vẫn 30/06/2026.
    fix = list(R2)
    fix[8] = 4350
    b = _run(db, seed, misa_xlsx_import, ImportModule.PACKAGING_MISA, _misa([fix]))
    assert (b.created_count, b.deleted_count) == (1, 1)
    prices = sorted(float(r.price) for r in db.query(L).filter(L.source_type == MISA))
    assert prices == [3170.0, 4350.0, 4724.0] and get_misa_cutoff(db) == date(2026, 6, 30)


def test_misa_khong_dung_toi_nguon_khac_va_moc_doi_theo_tep(db, seed, catalog):
    add_ledger(db, "CET0028", 3000, "2026-08-01", source_type=PriceSourceType.PO_LINE, line_stage=LedgerLineStage.FINAL, doc_id=9)
    set_misa_cutoff(db, date(2025, 12, 31))
    db.commit()
    later = list(R3)
    _run(db, seed, misa_xlsx_import, ImportModule.PACKAGING_MISA, _misa([later]))
    assert get_misa_cutoff(db) == date(2026, 6, 30)
    assert db.query(L).filter(L.source_type == int(PriceSourceType.PO_LINE)).count() == 1


def test_misa_tieu_de_khong_o_dong_dau_va_sai_tep_bi_chan(db, seed):
    misa_xlsx_import.precheck(_misa([R1], lead=4))
    with pytest.raises(ImportValidationError, match="Ngày, Mã hàng, Số lượng, Đơn giá"):
        misa_xlsx_import.precheck(_misa([R1], lead=7))      # tiêu đề ở dòng 8: ngoài 6 dòng đầu
    with pytest.raises(ImportValidationError, match="không có dòng mua hàng"):
        _run(db, seed, misa_xlsx_import, ImportModule.PACKAGING_MISA,
             _misa([[None, None, None, None, "CPT0075", "", "", 0, 1, 0]]), apply=False)


# ── Quyền, nhóm màn Import, hoàn tác ───────────────────────────────────────────
def test_nap_so_misa_doi_quyen_sua_con_bao_gia_doi_quyen_tao(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    for key in ("packaging_price_list", "packaging_history"):       # bao-CR-792: báo giá theo khóa Bảng giá, Sổ Misa theo khóa Lịch sử
        cap_quyen(seed.u_req_id, key, scope="all", read=True, create=True)
    imp_ctl._guard_module(db, user, int(ImportModule.PACKAGING_QUOTE), "create")
    with pytest.raises(HTTPException) as exc:
        imp_ctl._guard_module(db, user, int(ImportModule.PACKAGING_MISA), "create")
    assert exc.value.status_code == 403 and "quyền sửa" in exc.value.detail


def test_hai_loai_moi_nam_trong_nhom_thu_mua_va_chua_hoan_tac(db, seed, catalog):
    assert {ImportModule.PACKAGING_QUOTE, ImportModule.PACKAGING_MISA} <= set(imp_service._SUBSYSTEM_MODULES["procurement"])
    b = _run(db, seed, quote_import, ImportModule.PACKAGING_QUOTE, _sheet(QUOTE_HEAD, [["CPT0075", 100, "01/12/2026"]]))
    res = imp_service.revert_batch(db, b, seed.u_req_id)
    assert res["ok"] is False and "chưa hỗ trợ hoàn tác" in res["message"]
    assert db.query(ProductPriceQuote).count() == 1
