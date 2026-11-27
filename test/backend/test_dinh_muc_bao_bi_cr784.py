"""duoc-CR-784 phase 03 — định mức bao bì: CRUD (schema, chốt danh mục, quyền) + nhập `DATA_CHAI.xlsx` hai khuôn."""
from datetime import date
from io import BytesIO

import openpyxl
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.import_tool import controller as imp_ctl
from app.modules.import_tool import service as imp_service
from app.modules.import_tool.catalog_import import ImportValidationError
from app.modules.import_tool.model import ImportBatch, ImportLog, ImportMode, ImportModule, ImportStatus, LogLevel
from app.modules.packaging_cost import bom_import
from app.modules.packaging_cost.model import PackagingBom
from app.modules.packaging_cost.schema import BomCreate, BomUpdate
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_ledger, add_products, build_bom

BOMS = "/api/packaging-boms"


@pytest.fixture
def catalog(db):
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp", "Cái"), ("NHG0001", "Nhãn", "Cái"),
                 ("NDT0001", "Nhãn thùng", "Cái"), ("THU0001", "Thùng", "Cái"))


@pytest.fixture
def api(db, seed, cap_quyen, client_as, catalog):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_bom", scope="all", read=True, create=True, write=True, delete=True)
    return client_as(db.get(User, seed.u_req_id))


def _bom(db, **over) -> PackagingBom:
    base = dict(fg_code="HH0417.1", fg_name="Flower Top", bottle_code="CPT0105", cap_code="NAP0085", carton_qty=40,
                created_by=1, updated_by=1)
    base.update(over)
    row = build_bom(**base)
    db.add(row)
    db.commit()
    return row


# ── Schema ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("field,size", [("fg_code", 51), ("fg_name", 256), ("legal_name", 256), ("bottle_code", 51),
                                        ("cap_code", 51), ("label_code", 51), ("carton_label_code", 51),
                                        ("carton_code", 51)])
def test_schema_dinh_muc_chan_chuoi_dai_hon_cot(field, size):
    with pytest.raises(ValidationError) as exc:
        BomCreate(**{"fg_code": "H1", "bottle_code": "C1", field: "x" * size})
    assert any(e["type"] == "string_too_long" for e in exc.value.errors())


@pytest.mark.parametrize("bad", [{"carton_qty": -1}, {"carton_qty": 100001}, {"bottle_code": " "}, {"fg_code": ""}])
def test_schema_dinh_muc_chan_gia_tri_vo_ly(bad):
    with pytest.raises(ValidationError):
        BomCreate(**{"fg_code": "H1", "bottle_code": "C1", **bad})
    with pytest.raises(ValidationError):
        BomUpdate(**bad)


# ── CRUD ────────────────────────────────────────────────────────────────────────
def test_tao_dinh_muc_tra_ve_nam_thanh_phan_kem_ten_va_dvt(api):
    res = api.post(BOMS, json={"fg_code": "HH0417.1", "fg_name": "Flower Top", "bottle_code": "CPT0105",
                               "cap_code": "NAP0085", "label_code": "NHG0001", "carton_qty": 40})
    assert res.status_code == 201, res.text
    parts = res.json()["data"]["parts"]
    assert [p["role"] for p in parts] == [1, 2, 3, 4, 5]
    assert parts[0] == {"role": 1, "code": "CPT0105", "name": "Chai 450ml", "unit": "Cái", "in_catalog": True}
    assert parts[3]["code"] == "" and parts[3]["in_catalog"] is False


def test_trung_ma_hh_la_400_ma_thanh_phan_la_la_422_thieu_chai_422(api, db):
    _bom(db)
    assert api.post(BOMS, json={"fg_code": "HH0417.1", "bottle_code": "CPT0105"}).status_code == 400
    bad = api.post(BOMS, json={"fg_code": "HH9", "bottle_code": "CPT0105", "cap_code": "KHONG_CO"})
    assert bad.status_code == 422 and "KHONG_CO" in bad.text
    assert api.post(BOMS, json={"fg_code": "HH9"}).status_code == 422
    assert api.post(BOMS, json={"fg_code": "HH9", "bottle_code": "CPT0105", "carton_qty": 100001}).status_code == 422


def test_sua_dinh_muc_chan_null_va_ma_la(api, db):
    row = _bom(db)
    assert api.patch(f"{BOMS}/{row.id}", json={"carton_qty": 48}).status_code == 200
    assert db.get(PackagingBom, row.id).carton_qty == 48
    assert api.patch(f"{BOMS}/{row.id}", json={"bottle_code": None}).status_code == 422
    assert api.patch(f"{BOMS}/{row.id}", json={"cap_code": "KHONG_CO"}).status_code == 422


def test_danh_sach_dinh_muc_gom_mot_truy_van_ten_cho_ca_trang(api, db):
    from lich_lam_viec_factory import count_queries
    for i in range(30):
        _bom(db, fg_code=f"HH{i:04d}")
    res, sqls = count_queries(db, lambda: api.get(BOMS, params={"page_size": 100}))
    assert res.status_code == 200 and len(res.json()["data"]["items"]) == 30
    product_selects = [s for s in sqls if "FROM tab_product" in s and "tab_packaging_bom" not in s]
    assert len(product_selects) == 1


def test_khong_quyen_la_403(db, seed, client_as):  # noqa: F811
    assert client_as(db.get(User, seed.u_req_id)).get(BOMS).status_code == 403


# ── Nhập Excel ──────────────────────────────────────────────────────────────────
def _wb_map_sp(rows, sheet="MAP_SP"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(["Mã chai", "Mã nắp", "Mã HH", "Tên HH", "Tên pháp lý", "Quy cách", "x", "x", "Nhãn", "Nhãn thùng", "Thùng"])
    for _ in range(3):
        ws.append([None] * 11)
    for r in rows:
        ws.append(r)
    return wb


def _batch(db, seed, mode=ImportMode.APPLY):
    b = ImportBatch(module=int(ImportModule.PACKAGING_BOM), mode=int(mode), filename="DATA_CHAI.xlsx",
                    status=int(ImportStatus.RUNNING), created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(b)
    db.commit()
    return b


def _run(db, seed, wb, apply=True):
    b = _batch(db, seed, ImportMode.APPLY if apply else ImportMode.DRY_RUN)
    bom_import.run(db, b, wb, apply=apply)
    db.refresh(b)
    return b


def _logs(db, b, level=None):
    q = db.query(ImportLog).filter(ImportLog.batch_id == b.id)
    return [x for x in q.order_by(ImportLog.id) if level is None or x.level == int(level)]


ROW = ["CPT0105", "NAP0085", "HH0417.1", "Flower Top", "Vi lượng", 40.0, None, None, "NHG0001", "NDT0001", "THU0001"]


def test_nhap_map_sp_tao_moi_roi_nhap_lai_la_cap_nhat_khong_nhan_doi(db, seed, catalog):
    b = _run(db, seed, _wb_map_sp([ROW]))
    assert (b.status, b.created_count, b.updated_count, b.error_count) == (int(ImportStatus.DONE), 1, 0, 0)
    row = db.query(PackagingBom).one()
    assert (row.fg_code, row.bottle_code, row.cap_code, row.label_code, row.carton_label_code, row.carton_code,
            row.carton_qty) == ("HH0417.1", "CPT0105", "NAP0085", "NHG0001", "NDT0001", "THU0001", 40)

    changed = list(ROW)
    changed[5], changed[1] = 48, "NAP0099"
    b2 = _run(db, seed, _wb_map_sp([changed]))
    assert (b2.created_count, b2.updated_count) == (0, 1)
    row = db.query(PackagingBom).one()
    assert (row.cap_code, row.carton_qty) == ("NAP0099", 48)
    note = next(x.message for x in _logs(db, b2) if x.category == "bom_update")
    assert "Nắp: NAP0085 → NAP0099" in note and "Quy cách thùng: 40 → 48" in note
    assert _run(db, seed, _wb_map_sp([changed])).skipped_count == 1   # giống hệt → bỏ qua, không ghi


def test_chay_thu_khong_ghi_gi(db, seed, catalog):
    b = _run(db, seed, _wb_map_sp([ROW]), apply=False)
    assert b.created_count == 1 and db.query(PackagingBom).count() == 0


def test_o_loi_cong_thuc_la_rong_thieu_chai_hoac_ma_hh_la_loi_bo_dong(db, seed, catalog):
    rows = [["#N/A", "NAP0085", "HH1", "Không chai", None, 10, None, None, None, None, None],
            ["CPT0105", "#REF!", "HH2", "Nắp lỗi công thức", None, 10, None, None, "#N/A", None, None],
            ["CPT0105", None, "#N/A", "Mã HH lỗi", None, 10, None, None, None, None, None]]
    b = _run(db, seed, _wb_map_sp(rows))
    assert (b.created_count, b.error_count) == (1, 2)
    only = db.query(PackagingBom).one()
    assert (only.fg_code, only.cap_code, only.label_code) == ("HH2", "", "")
    cats = {x.category for x in _logs(db, b, LogLevel.ERROR)}
    assert cats == {"missing_bottle", "missing_fg"}


def test_ma_thanh_phan_chua_co_trong_danh_muc_la_canh_bao_van_nhan(db, seed, catalog):
    row = list(ROW)
    row[1] = "NAP9999"
    b = _run(db, seed, _wb_map_sp([row]))
    assert b.created_count == 1 and b.warning_count == 1
    assert "NAP9999" in next(x.message for x in _logs(db, b, LogLevel.WARNING))


def test_quy_cach_khong_phai_so_la_canh_bao_dat_0_trung_ma_lay_dong_sau(db, seed, catalog):
    first, second = list(ROW), list(ROW)
    first[5], second[5] = "abc", 24
    second[3] = "Tên dòng sau"
    b = _run(db, seed, _wb_map_sp([first, second]))
    assert b.warning_count == 2   # quy cách chữ + trùng mã
    row = db.query(PackagingBom).one()
    assert (row.carton_qty, row.fg_name) == (24, "Tên dòng sau")


def test_dong_tren_db_khong_co_trong_tep_giu_nguyen_va_bao_so_dem(db, seed, catalog):
    _bom(db, fg_code="HH-CU")
    b = _run(db, seed, _wb_map_sp([ROW]))
    assert db.query(PackagingBom).count() == 2
    assert any(x.category == "bom_kept" and x.message.startswith("1 ") for x in _logs(db, b))


def test_ma_hh_khop_khong_phan_biet_hoa_thuong(db, seed, catalog):
    _bom(db, fg_code="HH0417.1")
    lower = list(ROW)
    lower[2] = "hh0417.1"
    b = _run(db, seed, _wb_map_sp([lower]))
    assert (b.created_count, b.updated_count + b.skipped_count) == (0, 1) and db.query(PackagingBom).count() == 1


def _wb_data_chung(chung_rows, data_rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "data"
    ws.append(["Mã chai", "Mã nắp", "Mã HH", "Tên HH", "Tên pháp lý", "Quy cách"])
    for _ in range(3):
        ws.append([None] * 6)
    for r in data_rows:
        ws.append(r)
    dc = wb.create_sheet("DATA CHUNG")
    dc.append(["x"] * 6)
    dc.append(["Mã", "Tên", "Mã nhãn", "x", "x", "Mã HH"])
    for r in chung_rows:
        dc.append(r)
    return wb


def test_khuon_data_va_data_chung_chon_nhan_mua_gan_nhat_va_khop_hh_bo_so_0_dau(db, seed, catalog):
    add_products(db, ("NHG0002", "Nhãn B", "Cái"))
    add_ledger(db, "NHG0001", 100, "2026-01-10")
    add_ledger(db, "NHG0002", 100, "2026-09-10")          # NHG0002 được mua gần hơn → thắng
    wb = _wb_data_chung(
        [[None, None, "NHG0001", None, None, "HH417.1"], [None, None, "NHG0002", None, None, "HH0417.1"],
         [None, None, "NDT0001", None, None, "HH417.1"], [None, None, "ZZZ0001", None, None, "HH417.1"]],
        [["CPT0105", "NAP0085", "HH0417.1", "Flower Top", "Vi lượng", 40]])
    b = _run(db, seed, wb)
    assert b.created_count == 1
    row = db.query(PackagingBom).one()
    assert (row.label_code, row.carton_label_code, row.carton_code) == ("NHG0002", "NDT0001", "")


def test_khuon_data_giu_gia_tri_dang_co_khi_data_chung_khong_co(db, seed, catalog):
    _bom(db, label_code="NHG0001", carton_code="THU0001")
    wb = _wb_data_chung([], [["CPT0105", "NAP0085", "HH0417.1", "Flower Top", "Vi lượng", 40]])
    _run(db, seed, wb)
    row = db.query(PackagingBom).one()
    assert (row.label_code, row.carton_code) == ("NHG0001", "THU0001")


def test_tep_sai_dung_lo_bang_cau_ro_rang(db, seed, catalog):
    wb = openpyxl.Workbook()
    wb.active.title = "Sheet khac"
    with pytest.raises(ImportValidationError, match="MAP_SP"):
        bom_import.precheck(wb)
    wrong = openpyxl.Workbook()
    wrong.active.title = "MAP_SP"
    wrong.active.append(["Ngày", "Số chứng từ", "Diễn giải"])
    with pytest.raises(ImportValidationError, match="nhầm tệp"):
        bom_import.precheck(wrong)
    with pytest.raises(ImportValidationError, match="không có dòng dữ liệu"):
        _run(db, seed, _wb_map_sp([]))


def test_tran_so_dong(db, seed, catalog, monkeypatch):
    monkeypatch.setattr(bom_import, "MAX_ROWS", 2)
    with pytest.raises(ImportValidationError, match="vượt trần"):
        _run(db, seed, _wb_map_sp([ROW, ROW, ROW]))


# ── Gác quyền + hoàn tác ────────────────────────────────────────────────────────
def test_nguoi_khong_co_packaging_bom_create_tai_len_module_4_la_403(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    with pytest.raises(HTTPException) as exc:
        imp_ctl._guard_module(db, user, int(ImportModule.PACKAGING_BOM), "create")
    assert exc.value.status_code == 403
    cap_quyen(seed.u_req_id, "packaging_bom", scope="all", create=True)
    imp_ctl._guard_module(db, user, int(ImportModule.PACKAGING_BOM), "create")   # có quyền → qua


def test_hoan_tac_lo_dinh_muc_tra_loi_ro_rang_khong_roi_vao_nhanh_khao_sat(db, seed, catalog):
    b = _run(db, seed, _wb_map_sp([ROW]))
    res = imp_service.revert_batch(db, b, seed.u_req_id)
    assert res["ok"] is False and "chưa hỗ trợ hoàn tác" in res["message"]
    assert db.query(PackagingBom).count() == 1


def test_module_4_nam_trong_nhom_thu_mua_cua_man_import():
    assert ImportModule.PACKAGING_BOM in imp_service._SUBSYSTEM_MODULES["procurement"]


def test_tran_so_dong_kiem_truoc_khi_doc_ca_sheet_data_chung(db, seed, catalog, monkeypatch):
    monkeypatch.setattr(bom_import, "MAX_ROWS", 3)
    chung = [[None, None, f"NHG{i:04d}", None, None, "HH417.1"] for i in range(10)]
    wb = _wb_data_chung(chung, [["CPT0105", "NAP0085", "HH0417.1", "Flower Top", "Vi lượng", 40]])
    with pytest.raises(ImportValidationError, match="DATA CHUNG.*vượt trần"):
        _run(db, seed, wb)
    assert db.query(PackagingBom).count() == 0


def test_tran_chan_tu_max_row_khong_can_doc_het_dong(db, seed, catalog, monkeypatch):
    monkeypatch.setattr(bom_import, "MAX_ROWS", 2)
    wb = _wb_map_sp([ROW])
    wb["MAP_SP"].cell(row=50, column=1, value="rác")          # max_row = 50 > 2 + 4
    with pytest.raises(ImportValidationError, match="vượt trần"):
        _run(db, seed, wb)
