"""bao-CR-470 — HQ1 phân hệ Tra cứu giá hải quan: bộ đọc tệp GTT02 + đường nạp.

Thiết kế: `doc/erp/hai-quan/02-thiet-ke-ky-thuat.md` (§4 luật đọc, §8 danh sách
bài kiểm). Ba cái bẫy được canh ở đây đều IM LẶNG nếu vỡ — không lỗi, chỉ ra số sai:

```
cột Ngày đăng ký bị Excel đảo ngày/tháng  -> phải vá, nhưng CHỈ khi tệp có đúng dấu vân tay
cột Ngày hợp đồng là ngày THẬT            -> tuyệt đối không vá
nạp lại cùng khoảng ngày                  -> thay, không nhân đôi; lô đã thay thì không hoàn tác
```

Tệp mẫu thật nằm ngoài repo (dữ liệu của doanh nghiệp khác), nên ở đây dựng tệp
`.xlsx` giả bằng openpyxl — đi CÙNG đường luật đọc với `.xls`, vì cả hai định dạng
đều quy về một lưới ô chung trước khi áp luật.
"""
import io
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import openpyxl
import pytest

from app.modules.customs import importer, reader
from app.modules.customs.constants import COLUMNS, PartyType
from app.modules.customs.model import CustomsLine, CustomsParty
from app.modules.import_tool import service as import_service
from app.modules.import_tool.model import (ImportBatch, ImportMode, ImportModule,
                                           ImportStatus)

LABEL = dict(COLUMNS)


def _row(**over):
    """Một dòng hợp lệ theo khóa nội bộ; `over` ghi đè từng ô."""
    base = {
        "reg_date": "13-01-2026", "office_code": "HQHPKV3", "importer_tax_code": "'0500590269",
        "importer_name": "Công Ty TNHH Thú Y Toàn Cầu", "partner_name": "NOVADAN APS",
        "hs_code": "'38089990", "line_no": 1, "product_name": "ATRAZINE 97% TECH",
        "price_usd": 17.3897, "price_nt": 14.9, "adj_price_usd": None, "adj_price_nt": None,
        "currency": "EUR", "fx_rate": 30448.32, "usd_rate": 26089, "quantity": 880,
        "unit_code": "KGM", "origin_country": "DK", "contract_no": "770710",
        "contract_date": datetime(2025, 11, 20), "incoterm": "CIF",
        "transport_mode": "2-Đường biển (container)", "rate_import": 0, "rate_excise": 0,
        "rate_vat": 5, "rate_safeguard": 0, "tax_import": 0, "tax_excise": 0,
        "tax_vat": 19961918.592, "tax_environment": 0, "tax_safeguard": 0, "import_country": "VN",
    }
    base.update(over)
    return base


def _xlsx(rows, headers=None) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers or [label for _, label in COLUMNS])
    for r in rows:
        ws.append([r[key] for key, _ in COLUMNS])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── Luật đọc ngày ───────────────────────────────────────────────────────────
def test_o_chu_doc_thang_o_ngay_bi_dao_thi_va_lai():
    """Đúng dấu vân tay của tệp thật: ô chữ ngày > 12, ô ngày có "ngày" ≤ 12."""
    raw = _xlsx([_row(reg_date="13-01-2026"),
                 _row(reg_date=datetime(2026, 5, 3))])      # nguồn "05-03-2026" bị đọc thành 3/5
    res = reader.parse(raw, today=date(2026, 9, 23))

    assert res.date_swap is True
    assert res.rows[0]["reg_date"] == date(2026, 1, 13) and res.rows[0]["date_fixed"] == 0
    assert res.rows[1]["reg_date"] == date(2026, 3, 5) and res.rows[1]["date_fixed"] == 1


def test_ngay_hop_dong_khong_bao_gio_bi_va():
    """Cái bẫy đắt nhất: vá cả cột này là hỏng 39% số ngày hợp đồng đang đúng."""
    raw = _xlsx([_row(reg_date="13-01-2026", contract_date=datetime(2025, 3, 5)),
                 _row(reg_date=datetime(2026, 5, 3), contract_date=datetime(2025, 11, 20))])
    res = reader.parse(raw, today=date(2026, 9, 23))

    assert res.date_swap is True
    assert res.rows[0]["contract_date"] == date(2025, 3, 5)      # KHÔNG thành 3/5
    assert res.rows[1]["contract_date"] == date(2025, 11, 20)


def test_tep_co_ngay_that_thi_khong_va():
    """Nguồn mà sửa khuôn xuất (ô ngày đúng, có ngày > 12) thì bộ đọc tự thôi vá."""
    raw = _xlsx([_row(reg_date=datetime(2026, 1, 20)),
                 _row(reg_date=datetime(2026, 5, 3)),
                 _row(reg_date="14-02-2026")])
    res = reader.parse(raw, today=date(2026, 9, 23))

    assert res.date_swap is False
    assert res.rows[1]["reg_date"] == date(2026, 5, 3) and res.rows[1]["date_fixed"] == 0


def test_ngay_tuong_lai_thi_canh_bao():
    res = reader.parse(_xlsx([_row(reg_date="13-12-2026")]), today=date(2026, 9, 23))
    assert any("TƯƠNG LAI" in msg for _, _, msg in res.logs)


# ── Luật đọc mã, số, chữ ────────────────────────────────────────────────────
def test_boc_dau_nhay_va_giu_so_0_dau():
    raw = _xlsx([_row(importer_tax_code="'0500590269", hs_code="'01012100"),
                 _row(importer_tax_code=500590269, hs_code=1012100)])   # ô số đã mất số 0 đầu
    rows = reader.parse(raw, today=date(2026, 9, 23)).rows

    assert rows[0]["importer_tax_code"] == "0500590269" and rows[0]["hs_code"] == "01012100"
    assert rows[1]["importer_tax_code"] == "0500590269" and rows[1]["hs_code"] == "01012100"


def test_o_trong_ra_null_khong_ra_0():
    """Trống ≠ 0: rỗng là tờ khai không khai, 0 là thuế suất bằng không."""
    row = reader.parse(_xlsx([_row(adj_price_usd=None, rate_import=0)]),
                       today=date(2026, 9, 23)).rows[0]
    assert row["adj_price_usd"] is None
    assert row["rate_import"] == Decimal("0")


def test_tien_thue_giu_du_3_so_le():
    row = reader.parse(_xlsx([_row()]), today=date(2026, 9, 23)).rows[0]
    assert row["tax_vat"] == Decimal("19961918.592")
    assert row["price_usd"] == Decimal("17.3897")


def test_phuong_tien_van_chuyen_ra_ma_so():
    row = reader.parse(_xlsx([_row(transport_mode="1-Đường không")]), today=date(2026, 9, 23)).rows[0]
    assert row["transport_mode"] == 1


def test_ma_phuong_tien_la_tu_choi_ca_lo():
    """Mã lạ = nguồn đổi khuôn — không lưu bừa thành 9 «Khác»."""
    with pytest.raises(reader.CustomsFileError, match="lạ"):
        reader.parse(_xlsx([_row(transport_mode="7-Tàu vũ trụ")]), today=date(2026, 9, 23))


# ── Tiêu đề ─────────────────────────────────────────────────────────────────
def test_thieu_cot_thi_tu_choi_va_noi_ten_cot():
    headers = [label for _, label in COLUMNS]
    headers[headers.index("Thuế VAT")] = "Cột lạ"
    with pytest.raises(reader.CustomsFileError, match="«Thuế VAT»"):
        reader.check_headers(_xlsx([_row()], headers=headers))


def test_nguon_sua_chinh_ta_tieu_de_van_khop():
    """Nguồn ghi «Tên nuớc xuất xứ» (sai chính tả); sửa thành «nước» vẫn phải khớp."""
    headers = [label for _, label in COLUMNS]
    headers[headers.index("Tên nuớc xuất xứ")] = "Tên nước xuất xứ"
    reader.check_headers(_xlsx([_row()], headers=headers))


def test_tep_khong_phai_excel_thi_tu_choi():
    with pytest.raises(reader.CustomsFileError, match="không phải Excel"):
        reader.check_headers(b"ngay,ten\n1,2", "du-lieu.csv")


def test_doc_sheet_xls_quy_ve_cung_luoi_o():
    """Đường `.xls` (xlrd) phải ra đúng bốn loại ô như đường `.xlsx`."""
    import xlrd
    cells = {(0, 0): (xlrd.XL_CELL_TEXT, "13-01-2026"),
             (0, 1): (xlrd.XL_CELL_DATE, 46054.0),      # 01/02/2026
             (0, 2): (xlrd.XL_CELL_NUMBER, 17.5),
             (0, 3): (xlrd.XL_CELL_EMPTY, "")}
    sheet = SimpleNamespace(nrows=1, ncols=4,
                            cell=lambda r, c: SimpleNamespace(ctype=cells[(r, c)][0], value=cells[(r, c)][1]))
    row = reader.cells_from_xlrd_sheet(sheet, datemode=0)[0]

    assert [c.kind for c in row] == ["text", "date", "number", "empty"]
    assert row[1].value == date(2026, 2, 1)


# ── Ghi xuống DB ────────────────────────────────────────────────────────────
def _batch(db, mode=ImportMode.APPLY) -> ImportBatch:
    b = ImportBatch(module=ImportModule.CUSTOMS_DECLARATION, mode=mode, filename="gtt02.xlsx",
                    sheet_info="", error_summary="", status=ImportStatus.RUNNING, created_by=1)
    db.add(b)
    db.commit()
    return b


def _lines(db):
    return db.query(CustomsLine).all()


def test_chay_thu_khong_ghi_gi_nhung_bao_du_so(db):
    b = _batch(db, ImportMode.DRY_RUN)
    importer.run(db, b, _xlsx([_row(), _row(reg_date="20-01-2026")]), apply=False)

    assert _lines(db) == []
    assert b.status == ImportStatus.DONE and b.created_count == 2 and b.deleted_count == 0
    assert '"date_from": "2026-01-13"' in b.sheet_info and '"date_to": "2026-01-20"' in b.sheet_info


def test_ap_dung_ghi_dong_va_doi_tuong(db):
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(), _row(line_no=2)]), apply=True)

    lines = _lines(db)
    assert len(lines) == 2 and all(ln.batch_id == b.id for ln in lines)
    imp = db.get(CustomsParty, lines[0].importer_id)
    par = db.get(CustomsParty, lines[0].partner_id)
    assert imp.party_type == PartyType.DOMESTIC and imp.tax_code == "0500590269"
    assert par.party_type == PartyType.FOREIGN and par.name == "NOVADAN APS"


def test_doanh_nghiep_chong_trung_theo_ma_so_thue_ten_lay_ban_moi_nhat(db):
    """Cùng mã số thuế, hai cách viết hoa → MỘT doanh nghiệp."""
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(importer_name="CôNG TY TNHH BAYER VIệT NAM"),
                               _row(importer_name="Công ty TNHH Bayer Việt Nam")]), apply=True)

    domestic = db.query(CustomsParty).filter(CustomsParty.party_type == PartyType.DOMESTIC).all()
    assert len(domestic) == 1
    assert domestic[0].name == "Công ty TNHH Bayer Việt Nam"


def test_cung_ten_khac_loai_thi_hai_doi_tuong(db):
    """Đối tác nước ngoài trùng tên doanh nghiệp trong nước → KHÔNG gộp nhầm."""
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(importer_name="ABC", partner_name="ABC")]), apply=True)
    assert db.query(CustomsParty).count() == 2


def test_nap_lai_cung_khoang_ngay_thi_thay_khong_nhan_doi(db):
    first = _batch(db)
    importer.run(db, first, _xlsx([_row(), _row(line_no=2), _row(line_no=3)]), apply=True)
    second = _batch(db)
    importer.run(db, second, _xlsx([_row(), _row(line_no=2)]), apply=True)

    lines = _lines(db)
    assert len(lines) == 2 and all(ln.batch_id == second.id for ln in lines)
    assert second.deleted_count == 3


def test_khoang_ngay_khac_nhau_thi_khong_dung_nhau(db):
    jan = _batch(db)
    importer.run(db, jan, _xlsx([_row(reg_date="13-01-2026")]), apply=True)
    mar = _batch(db)
    importer.run(db, mar, _xlsx([_row(reg_date="13-03-2026")]), apply=True)

    assert len(_lines(db)) == 2 and mar.deleted_count == 0


def test_hoan_tac_lo_khong_thay_gi(db):
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(), _row(line_no=2)]), apply=True)
    res = import_service.revert_batch(db, b, user_id=1)

    assert res["ok"] and _lines(db) == []
    assert b.status == ImportStatus.REVERTED


def test_lo_da_thay_du_lieu_cu_thi_khong_hoan_tac(db):
    """Hoàn tác lúc này là để trống cả khoảng ngày — dòng cũ đã xóa, không có bản chụp."""
    first = _batch(db)
    importer.run(db, first, _xlsx([_row()]), apply=True)
    second = _batch(db)
    importer.run(db, second, _xlsx([_row()]), apply=True)
    res = import_service.revert_batch(db, second, user_id=1)

    assert res["ok"] is False and "nạp lại tệp đúng" in res["message"]
    assert len(_lines(db)) == 1 and second.status == ImportStatus.DONE


# ── Khai báo hệ thống ───────────────────────────────────────────────────────
def test_khoa_quyen_khai_du_va_khong_tu_cap():
    from app.core.permissions import ENTITIES, ENTITY_LABELS
    from app.core.scoping import PUBLIC, SCOPE_FIELDS
    from app.seed import _PUR_MANAGER_PERMS, _SYS_ENTITIES

    assert "customs_price" in ENTITIES and "customs_price" in ENTITY_LABELS
    assert SCOPE_FIELDS["customs_price"] is PUBLIC
    #  Không vai trò nào tự có — quyền ghi là quyền thay cả khoảng dữ liệu (đại ca tick tay).
    assert "customs_price" in _SYS_ENTITIES and "customs_price" not in _PUR_MANAGER_PERMS


def test_hai_bang_hai_quan_khong_ghi_nhat_ky_truoc_sau():
    from app.core.logging_policy import NO_LOG_TABLES
    assert {"tab_customs_line", "tab_customs_party"} <= NO_LOG_TABLES
