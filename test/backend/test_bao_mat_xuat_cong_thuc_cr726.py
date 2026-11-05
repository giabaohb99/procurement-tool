"""bao-CR-726 (BM-033 phần còn mở) — ô chữ mở đầu bằng = + - @ (tab / CR) không được thành CÔNG THỨC ở mọi tệp xuất.

- Sổ Excel tự đặt ô (báo cáo mua hàng, sổ tải về của sổ lao động / phúc lợi, tệp mẫu nhập, tệp Excel Trợ lý dựng):
  `guard_workbook` ép ô công thức openpyxl tự suy về chuỗi, giữ nguyên chữ.
- CSV danh mục (`csv_utils.export_csv_response`): thêm `'` trước ô nguy hiểm; bộ nạp CSV gỡ đúng dấu đó nên
  xuất -> nạp lại không đổi dữ liệu.
"""
import csv
import io

import pytest
from openpyxl import Workbook, load_workbook

from app.core.csv_utils import csv_escape, csv_unescape, export_csv_response, unescape_row
from app.core.export_xlsx import guard_workbook
from hdld_factory import client_as  # noqa: F401

DANGEROUS = ['=HYPERLINK("http://x","bam")', "+84901", "-2 kg", "@SUM(A1)", "\tabc", "\rabc"]
ROUND_TRIP = [*DANGEROUS, "'abc", "''x", "'=y", "binh thuong", "", "a'b", "'"]


def _reload(wb):
    buf = io.BytesIO()
    wb.save(buf)
    return load_workbook(io.BytesIO(buf.getvalue()))


# ---------- Excel ----------
def test_guard_workbook_ep_o_cong_thuc_ve_chu_giu_nguyen_noi_dung():
    wb = Workbook()
    ws = wb.active
    ws.cell(row=1, column=1, value="=1+1")
    ws.cell(row=1, column=2, value=5)
    ws.cell(row=1, column=3, value="binh thuong")
    wb.create_sheet("hai").cell(row=2, column=2, value="=HYPERLINK(\"http://x\")")
    assert ws["A1"].data_type == "f"      # openpyxl tự suy công thức — đúng lỗ cần chặn

    got = _reload(guard_workbook(wb))
    a1, b1, c1 = got.worksheets[0]["A1"], got.worksheets[0]["B1"], got.worksheets[0]["C1"]
    assert (a1.value, a1.data_type) == ("=1+1", "s")
    assert (b1.value, b1.data_type) == (5, "n")
    assert c1.value == "binh thuong"
    assert got["hai"]["B2"].data_type == "s"


def _no_formula(wb) -> None:
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                assert c.data_type != "f", f"{ws.title}!{c.coordinate} = {c.value!r} thành công thức"


def test_bao_cao_mua_hang_ten_ncc_mo_dau_bang_dau_bang_khong_thanh_cong_thuc():
    from app.modules.report.excel import build_report_workbook

    months = [{"key": "2026-06", "label": "06/2026"}]
    data = {"months": months,
            "supplier": [{"key": "=HYPERLINK(\"http://x\",\"bam\")", "trans": 1, "late": 0, "rate": 0.0,
                          "m": {"2026-06": {"trans": 1, "late": 0, "rate": 0.0}}}]}
    wb = load_workbook(build_report_workbook(data, "supplier"))
    _no_formula(wb)
    values = [c.value for row in wb.worksheets[0].iter_rows() for c in row]
    assert "=HYPERLINK(\"http://x\",\"bam\")" in values


def test_so_tai_ve_so_lao_dong_va_phuc_loi_qua_luoi_chung():
    from app.modules.labor_register.export_common import xlsx_download

    wb = Workbook()
    wb.active.cell(row=1, column=1, value="=cmd|' /C calc'!A0")   # ô ghi thẳng, không qua text_cell
    resp = xlsx_download(wb, "x")
    got = load_workbook(io.BytesIO(resp.body))
    assert (got.active["A1"].value, got.active["A1"].data_type) == ("=cmd|' /C calc'!A0", "s")


def test_tep_mau_nhap_ghi_chu_mo_dau_bang_dau_bang_khong_thanh_cong_thuc(monkeypatch):
    from app.modules.import_tool import catalog_import

    module = next(iter(catalog_import.ADAPTERS))
    monkeypatch.setitem(catalog_import.ADAPTERS, module, {
        "sheet": "Mau", "fields": [{"header": "=Ma"}], "template_notes": [("=Cot", "=1+1")]})
    wb = load_workbook(io.BytesIO(catalog_import.build_template(module)))
    _no_formula(wb)
    assert wb["Mau"]["A1"].value == "=Ma" and wb["Huong dan"]["B2"].value == "=1+1"


def test_tep_excel_tro_ly_dung_khong_co_cong_thuc():
    from app.modules.assistant.tools.export_tool import render_xlsx

    wb = load_workbook(io.BytesIO(render_xlsx([{"name": "S", "columns": ["Tên"], "rows": [["=1+1"], [3]]}])))
    _no_formula(wb)
    assert wb["S"]["A2"].value == "=1+1"


# ---------- CSV ----------
@pytest.mark.parametrize("value", ROUND_TRIP)
def test_csv_thoat_roi_go_ra_dung_chuoi_goc(value):
    assert csv_unescape(csv_escape(value)) == value


def test_csv_o_nguy_hiem_co_dau_nhay_o_so_giu_nguyen():
    assert all(csv_escape(v).startswith("'") for v in DANGEROUS)
    assert csv_escape("binh thuong") == "binh thuong"
    assert csv_unescape("'abc") == "'abc"            # tệp người gõ tay: `'` trước chữ thường giữ nguyên
    assert csv_unescape(None) is None                # dòng thiếu cột của DictReader

    class Item:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    items = [Item(code="=1+1", qty=-5, note=None, is_active=True)]
    resp = export_csv_response(items, {"code": "Mã", "qty": "SL", "note": "Ghi chú"}, "x")
    rows = list(csv.reader(io.StringIO(resp.body.decode("utf-8-sig"))))
    assert rows[1] == ["'=1+1", "-5", "", "Hoạt động"]   # số âm là SỐ, không thoát
    assert unescape_row(dict(zip(rows[0], rows[1])))["Mã"] == "=1+1"


def test_csv_danh_muc_xuat_roi_nap_lai_khong_doi_du_lieu(db, world, client_as):  # noqa: F811
    from app.modules.catalog.model import Unit

    actor = world.grant("a1", "unit", "all", actions=("read", "create", "write", "import", "export"))
    names = {"CR726A": '=HYPERLINK("http://x","bam")', "CR726B": "'giu dau nhay", "CR726C": "-5 kg",
             "CR726D": "@SUM(A1)"}
    units = [Unit(code=c, name=n, is_active=True) for c, n in names.items()]
    db.add_all(units)
    db.commit()
    client = client_as(actor)

    resp = client.get("/api/units/export/csv", params={"ids": ",".join(str(u.id) for u in units)})
    assert resp.status_code == 200, resp.text
    text = resp.content.decode("utf-8-sig")
    by_code = {r["Mã"]: r["Tên ĐVT"] for r in csv.DictReader(io.StringIO(text))}
    assert by_code["CR726A"] == "'" + names["CR726A"] and by_code["CR726B"] == "''giu dau nhay"

    for u in units:
        u.name = "doi ten"
    db.commit()
    files = {"file": ("dvt.csv", resp.content, "text/csv")}   # nạp lại NGUYÊN tệp vừa xuất (kể cả BOM)
    resp = client.post("/api/units/import/csv", files=files)
    assert resp.status_code == 200, resp.text

    db.expire_all()
    got = {u.code: u.name for u in db.query(Unit).filter(Unit.code.in_(names))}
    assert got == names


def test_csv_xuat_tap_trung_roi_nap_qua_quan_ly_import_khong_doi_du_lieu():
    """Xuất tập trung (`/api/exports/run?format=csv`) thoát ô chữ; Quản lý Import đọc CSV gỡ đúng dấu."""
    from app.core.export_xlsx import Col
    from app.modules.export_log.service import _build_csv
    from app.modules.import_tool.tasks import _csv_to_workbook

    cols = [Col("code", "Mã"), Col("name", "Tên"), Col("qty", "SL", "int")]
    rows = [{"code": "A1", "name": v, "qty": -3} for v in ROUND_TRIP if v not in ("\tabc", "\rabc")]
    raw = _build_csv(cols, rows)
    lines = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    assert lines[1][1] == "'" + ROUND_TRIP[0] and lines[1][2] == "-3"
    ws = _csv_to_workbook(raw).active
    got = [r[1] for r in ws.iter_rows(min_row=2, values_only=True)]
    assert got == [r["name"] for r in rows]
