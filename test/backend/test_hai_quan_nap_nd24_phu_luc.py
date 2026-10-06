"""duoc-CR-598 mục 3 — nạp danh mục hóa chất NĐ 24/2026 phụ lục I–IV từ tệp «03. KHAI BÁO HOÁ CHẤT.xlsx».

Canh các bẫy của tệp thật (đọc tay 06/10/2026): Excel tự sửa số CAS (thêm số 0, đổi thành NGÀY,
`#VALUE!`), cột «Phụ lục» thiếu ở dòng có số thứ tự, «Bảng B» cuối phụ lục IV là NHÓM nguy hại chứ
không phải hóa chất, số CAS phụ nằm ở dòng kế tiếp. Và luật đồng bộ: cập nhật / thêm / NGỪNG DÙNG,
không đụng TT 75 + TT 01, chạy lại lần hai không đẻ thêm dòng.
"""
import json
from datetime import datetime
from pathlib import Path

import pytest

from app.modules.customs import nd24_regulation_loader as L
from app.modules.customs import regulation_browse_service as B
from app.modules.customs.constants import RegulationList
from app.modules.customs.model import CustomsRegulation
from app.modules.customs.service import lookup_regulations

PL1, PL2, PL3, PL4 = (int(RegulationList.ND24_PL1), int(RegulationList.ND24_PL2),
                      int(RegulationList.ND24_PL3), int(RegulationList.ND24_PL4))


# ── normalize_cas / split_cas ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw, expected", [
    ("106-99-0", "106-99-0"),
    ("0107-02-08", "107-02-8"),            # Excel thêm số 0 ở đầu và ở số kiểm
    ("0464-07-03", "464-07-3"),
    ("7719-09-07 00:00:00", "7719-09-7"),  # ô bị đọc thành ngày rồi in ra chuỗi
    (datetime(7719, 9, 7), "7719-09-7"),   # openpyxl trả thẳng `datetime`
    ("#VALUE!", ""),
    ("---", ""),
    ("--", ""),
    ("", ""),
    (None, ""),
    ("  7664-41-7  ", "7664-41-7"),
    (7664417, "7664-41-7"),                 # ô số: mất dấu gạch
    (12, ""),                               # số quá ngắn, không thể là CAS
])
def test_normalize_cas_repairs_what_excel_broke(raw, expected):
    assert L.normalize_cas(raw) == expected


def test_normalize_cas_reads_any_date_cell_as_year_month_day_parts():
    """Ô bị Excel coi là ngày: năm · tháng · ngày ghép lại đúng ba phần của số CAS, ngày một chữ số."""
    assert L.normalize_cas(datetime(2026, 9, 7)) == "2026-09-7"


def test_normalize_cas_keeps_well_formed_cas_with_wrong_check_digit_verbatim():
    #  Gõ nhầm ở nguồn thì giữ nguyên văn để người đọc thấy, không âm thầm xóa.
    assert L.normalize_cas("106-99-1") == "106-99-1"
    assert L.normalize_cas("abc") == "abc"


def test_split_cas_handles_several_numbers_in_one_cell():
    assert L.split_cas("107-01-7\n590-18-1\n624-64-6") == ["107-01-7", "590-18-1", "624-64-6"]
    assert L.split_cas("7664-41-7; #VALUE!") == ["7664-41-7"]
    assert L.split_cas(None) == []


# ── parse_sheet ────────────────────────────────────────────────────────────────────────────

def _sheet():
    """Mô phỏng đúng hình các đoạn khó của sheet thật (cột A–G)."""
    return [
        ("DANH SÁCH HOẠT CHẤT THEO QUY ĐỊNH NHÀ NƯỚC", None, None, None, None, None, None),
        (None, None, "PHỤ LỤC I", None, None, None, None),
        ("STT", "Tên khoa học", "Tên chất", "Mã số CAS", "Công thức hóa học", None, None),
        (None, "(danh pháp IUPAC)", None, None, None, None, None),
        ("1.", "1,3-Butadiene", "1,3-Butadien", "106-99-0", "C4H6", "Phụ lục I", None),
        ("5.", "Argon", "Argon", "7440-37-1", "Ar", "Phụ lục I", "Barbasco powder"),   # rác cột G
        (None, None, "PHỤ LỤC II", None, None, None, None),
        ("1. Chất sản xuất, kinh doanh có điều kiện", None, None, None, None, None, None),
        ("59.", "Barium hypochlorite", "Bari hypoclorit", "#VALUE!", "Ba(ClHO)2", "Phụ lục II", None),
        ("381.", "Hexabromo cyclododecane", "Hexabrom xyclododecan", "134237-50-6", "C12H18Br6", "Phụ lục II", None),
        (None, None, None, "134237-51-7", None, None, None),                # số CAS phụ ở dòng sau
        (None, None, None, "#VALUE!", None, None, None),
        (None, None, "PHỤ LỤC III", None, None, None, None),
        ("A", "CÁC TIỀN CHẤT CÔNG NGHIỆP", None, None, None, None, None),
        (None, "Nhóm 1 (IVB): ghi chú dài…", None, None, None, None, None),   # ghi chú, không phải dòng
        ("Hóa chất khác", None, None, None, None, None, None),
        ("37.", "Arsenic and arsenic compounds", "Asen và các hợp chất của asen", "---", "---", None, None),  # thiếu cột F
        (None, "E.g", "Ví dụ", None, None, None, None),
        (None, None, "PHỤ LỤC IV", None, None, None, None),
        ("1. Bảng A", None, None, None, None, None, None),
        ("1.", "Acrolein (2-Propenal)", "Acrolein", "0107-02-08", "C3H4O", "Phụ lục IV", "5000"),
        ("135.", "Potassium nitrate", "Kali nitrat", "7757-79-1", "KNO3", "Phụ lục IV", None),
        (None, None, "Dạng hạt", None, None, "Phụ lục IV", 5000000),        # dòng con không số
        (271, "Carcinogens…", "Các chất gây ung thư…", None, None, "Phụ lục IV", 500),   # STT kiểu số
        ("2. Bảng B", None, None, None, None, None, None),
        ("1", "Độc cấp tính cấp 1, tất cả các đường phơi nhiễm", "5000", None, None, None, None),
        ("4", "Sol khí dễ cháy cấp 1", "150.000 (net)", None, None, None, None),
    ]


def test_parse_sheet_reads_each_appendix_by_its_heading_not_by_column_f():
    items = L.parse_sheet(_sheet())
    assert [(i["list_code"], i["seq_no"]) for i in items] == [
        (PL1, "1"), (PL1, "5"), (PL2, "59"), (PL2, "381"), (PL3, "37"),
        (PL4, "1"), (PL4, "135"), (PL4, "135"), (PL4, "271"),
    ]
    #  Thứ tự trong từng phụ lục bắt đầu lại từ 1.
    assert [i["sort_order"] for i in items if i["list_code"] == PL4] == [1, 2, 3, 4]


def test_parse_sheet_skips_table_b_hazard_groups_at_the_end_of_appendix_iv():
    names = [i["name"] for i in L.parse_sheet(_sheet())]
    assert not any("Độc cấp tính" in n or "Sol khí" in n for n in names)


def test_parse_sheet_fills_every_column_the_user_asked_for():
    first = L.parse_sheet(_sheet())[0]
    assert first == {
        "list_code": PL1, "seq_no": "1", "sort_order": 1, "name": "1,3-Butadiene", "name_vi": "1,3-Butadien",
        "cas_no": "106-99-0", "formula": "C4H6", "category": "", "threshold_kg": None, "mixture_pct": None,
        "legal_basis": "NĐ 24/2026/NĐ-CP Phụ lục I", "note": "",
    }


def test_parse_sheet_cleans_bad_cells_and_keeps_extra_cas_numbers_in_the_note():
    items = {i["name"]: i for i in L.parse_sheet(_sheet())}
    assert items["Barium hypochlorite"]["cas_no"] == ""
    assert items["Hexabromo cyclododecane"]["note"] == "Số CAS khác: 134237-51-7"
    assert items["Acrolein (2-Propenal)"]["cas_no"] == "107-02-8"
    arsenic = items["Arsenic and arsenic compounds"]
    assert (arsenic["cas_no"], arsenic["formula"]) == ("", "")
    #  Cột G rác ở phụ lục I («Barbasco powder») không thành ngưỡng.
    assert items["Argon"]["threshold_kg"] is None


def test_parse_sheet_takes_thresholds_only_in_appendix_iv_and_names_sub_rows_after_their_parent():
    items = [i for i in L.parse_sheet(_sheet()) if i["list_code"] == PL4]
    assert [i["threshold_kg"] for i in items] == [5000.0, None, 5000000.0, 500.0]
    sub = items[2]
    assert sub["name"] == "Potassium nitrate — Dạng hạt"
    assert sub["name_vi"] == "Kali nitrat — Dạng hạt"
    assert sub["seq_no"] == "135"


def test_parse_sheet_records_group_headings_as_category():
    items = {i["name"]: i for i in L.parse_sheet(_sheet())}
    assert items["Hexabromo cyclododecane"]["category"] == "1. Chất sản xuất, kinh doanh có điều kiện"
    assert items["Arsenic and arsenic compounds"]["category"] == "Hóa chất khác"
    assert items["Acrolein (2-Propenal)"]["category"] == "1. Bảng A"


def _appendix_iii():
    """Khung phụ lục III đúng như tệp thật: nhóm 1 / nhóm 2, mỗi nhóm có mục A (tiền chất CN), B, C."""
    return [
        (None, None, "PHỤ LỤC III", None, None, None, None),
        ("I. Chất cần kiểm soát đặc biệt", None, None, None, None, None, None),
        ("1.1. Nhóm 1", None, None, None, None, None, None),
        ("A", "CÁC TIỀN CHẤT CÔNG NGHIỆP", None, None, None, None, None),
        ("1.", "Phenylacetone", "Phenylaxeton", "103-79-7", "C9H10O", "Phụ lục III", None),
        ("B", "HÓA CHẤT THUỘC CÔNG ƯỚC CẤM …", None, None, None, None, None),
        ("2B", "Precursors", "Các tiền chất", None, None, None, None),
        ("26.", "Arsenic trichloride", "Arsenic trichloride", "7784-34-1", "AsCl3", "Phụ lục III", None),
        ("1.2. Nhóm 2", None, None, None, None, None, None),
        ("A", "CÁC TIỀN CHẤT CÔNG NGHIỆP", None, None, None, None, None),
        ("1.", "Acetone", "Axeton", "67-64-1", "C3H6O", "Phụ lục III", None),
        ("B", "HÓA CHẤT THUỘC CÔNG ƯỚC CẤM …", None, None, None, None, None),
        ("3A", "Toxic Chemicals", "Các hóa chất độc", None, None, None, None),
        ("24.", "Phosgene", "Phosgen", "75-44-5", "COCl2", "Phụ lục III", None),
        ("C", "HÓA CHẤT THUỘC CÁC CÔNG ƯỚC QUỐC TẾ VỀ HÓA CHẤT", None, None, None, None, None),
        ("36.", "Aldicarb", "Aldicarb", "116-06-3", "C7H14N2O2S", "Phụ lục III", None),
    ]


#  NĐ 24/2026 (câu ghi chú của văn bản, KHÔNG có trong tệp Excel): PL II > 5%; PL III nhóm 1 > 1%,
#  nhóm 2 tiền chất công nghiệp > 5%, nhóm 2 còn lại > 1%. Lệch một mức là cảnh báo sai cho thu mua.
def test_parse_sheet_sets_mixture_threshold_by_appendix_group_and_section():
    pct = {i["name"]: i["mixture_pct"] for i in L.parse_sheet(_sheet() + _appendix_iii())}
    assert pct["Barium hypochlorite"] == 5.0                 # PL II
    assert pct["Phenylacetone"] == 1.0                       # PL III nhóm 1, tiền chất CN
    assert pct["Arsenic trichloride"] == 1.0                 # PL III nhóm 1, công ước
    assert pct["Acetone"] == 5.0                             # PL III nhóm 2, tiền chất CN
    assert pct["Phosgene"] == 1.0                            # PL III nhóm 2, công ước vũ khí hóa học
    assert pct["Aldicarb"] == 1.0                            # PL III nhóm 2, Rotterdam / Stockholm
    assert pct["Argon"] is None and pct["Acrolein (2-Propenal)"] is None   # PL I, PL IV


def test_parse_sheet_prefixes_appendix_iii_category_with_its_group():
    items = {i["name"]: i for i in L.parse_sheet(_appendix_iii())}
    assert items["Phenylacetone"]["category"] == "Nhóm 1 · A. CÁC TIỀN CHẤT CÔNG NGHIỆP"
    assert items["Acetone"]["category"] == "Nhóm 2 · A. CÁC TIỀN CHẤT CÔNG NGHIỆP"
    assert items["Phosgene"]["category"] == "Nhóm 2 · 3A. Các hóa chất độc"


def test_obligation_mentions_the_mixture_threshold(db):
    L.apply_rows(db, [_item(PL2, "1", "Acetaldehyde", "75-07-0", mixture_pct=5.0),
                      _item(PL1, "1", "Argon", "7440-37-1")])
    db.commit()
    by_name = {i["name"]: i for i in B.list_regulations(db, "", None, 0, 50)[1]}
    assert by_name["Acetaldehyde"]["mixture_pct"] == 5.0
    assert "Hỗn hợp chứa chất này > 5% khối lượng" in by_name["Acetaldehyde"]["obligation"]
    assert by_name["Argon"]["mixture_pct"] is None
    assert "Hỗn hợp" not in by_name["Argon"]["obligation"]


def test_parse_sheet_on_empty_or_headless_input():
    assert L.parse_sheet([]) == []
    #  Chưa gặp tiêu đề «PHỤ LỤC …» thì không biết dòng thuộc phụ lục nào → bỏ, không đoán.
    assert L.parse_sheet([("1.", "Argon", "Argon", "7440-37-1", "Ar", "Phụ lục I", None)]) == []


# ── apply_rows ─────────────────────────────────────────────────────────────────────────────

def _item(list_code, seq, name, cas="", sort_order=1, **extra):
    return {"list_code": list_code, "seq_no": seq, "sort_order": sort_order, "name": name, "name_vi": "",
            "cas_no": cas, "formula": "", "category": "", "threshold_kg": None, "mixture_pct": None,
            "legal_basis": "NĐ 24/2026/NĐ-CP", "note": ""} | extra


def test_apply_rows_updates_legacy_rows_inserts_new_ones_and_deactivates_the_rest(db):
    db.add_all([
        CustomsRegulation(list_code=PL4, name="Acrolein", cas_no="107-02-8", threshold_kg=1),
        CustomsRegulation(list_code=PL2, name="Old chemical", cas_no="1-11-1"),
        CustomsRegulation(list_code=PL2, name="Barium hypochlorite", cas_no="13477-10-6"),
        CustomsRegulation(list_code=int(RegulationList.BANNED_TT75), name="Paraquat", cas_no="4685-14-7"),
        CustomsRegulation(list_code=int(RegulationList.PUBLISH_TT01), name="Toluene", cas_no="108-88-3"),
    ])
    db.commit()
    stats = L.apply_rows(db, [
        _item(PL4, "1", "Acrolein (2-Propenal)", "107-02-8", formula="C3H4O", threshold_kg=5000.0),
        _item(PL2, "59", "Barium hypochlorite", ""),        # ô CAS hỏng ở tệp → rỗng
        _item(PL1, "1", "1,3-Butadiene", "106-99-0"),
    ])
    db.commit()
    assert stats == {"total": 3, "inserted": 1, "updated": 2, "deactivated": 1}

    acrolein = db.query(CustomsRegulation).filter_by(cas_no="107-02-8").one()
    assert (acrolein.name, acrolein.formula, float(acrolein.threshold_kg), acrolein.seq_no) == \
        ("Acrolein (2-Propenal)", "C3H4O", 5000.0, "1")
    barium = db.query(CustomsRegulation).filter_by(name="Barium hypochlorite").one()
    assert barium.cas_no == "13477-10-6", "CAS hỏng ở tệp không được xóa mất CAS đang có"
    assert db.query(CustomsRegulation).filter_by(name="Old chemical").one().is_active is False
    #  TT 75 / TT 01 không thuộc phụ lục NĐ 24 → không đụng.
    assert db.query(CustomsRegulation).filter_by(name="Paraquat").one().is_active is True
    assert db.query(CustomsRegulation).filter_by(name="Toluene").one().is_active is True


def test_apply_rows_twice_is_idempotent_even_with_duplicate_names_and_cas(db):
    items = [
        _item(PL3, "6", "Diethyl ether", "60-29-7", sort_order=1),
        _item(PL3, "6", "Diethyl ether", "60-29-7", sort_order=2),     # cùng chất ở hai mục
        _item(PL3, "7", "Ethyl ether", "", sort_order=3),
    ]
    assert L.apply_rows(db, items)["inserted"] == 3
    db.commit()
    assert L.apply_rows(db, items) == {"total": 3, "inserted": 0, "updated": 3, "deactivated": 0}
    db.commit()
    assert db.query(CustomsRegulation).count() == 3


def test_apply_rows_reactivates_a_row_that_comes_back(db):
    db.add(CustomsRegulation(list_code=PL1, name="Argon", cas_no="7440-37-1", is_active=False))
    db.commit()
    L.apply_rows(db, [_item(PL1, "5", "Argon", "7440-37-1")])
    db.commit()
    assert db.query(CustomsRegulation).one().is_active is True


def test_apply_rows_with_empty_input_deactivates_all_nd24_rows_but_nothing_else(db):
    db.add_all([CustomsRegulation(list_code=PL1, name="Argon"),
                CustomsRegulation(list_code=int(RegulationList.BANNED_TT75), name="Paraquat")])
    db.commit()
    assert L.apply_rows(db, [])["deactivated"] == 1
    assert db.query(CustomsRegulation).filter_by(name="Paraquat").one().is_active is True


# ── màn đọc sau khi nạp ────────────────────────────────────────────────────────────────────

def test_browse_returns_new_columns_in_document_order_and_manual_rows_last(db):
    L.apply_rows(db, [
        _item(PL2, "2", "Zinc", "7440-66-6", sort_order=2, formula="Zn"),
        _item(PL2, "1", "Acetone", "67-64-1", sort_order=1, formula="C3H6O"),
    ])
    db.add(CustomsRegulation(list_code=PL2, name="AAA thêm tay"))       # sort_order = 0
    db.commit()
    _, items = B.list_regulations(db, "", PL2, 0, 50)
    assert [i["name"] for i in items] == ["Acetone", "Zinc", "AAA thêm tay"]
    assert (items[0]["seq_no"], items[0]["formula"]) == ("1", "C3H6O")


def test_browse_and_quick_lookup_find_a_row_by_its_formula(db):
    L.apply_rows(db, [_item(PL2, "1", "Acetone", "67-64-1", formula="C3H6O")])
    db.commit()
    assert [i["name"] for i in B.list_regulations(db, "c3h6o", None, 0, 50)[1]] == ["Acetone"]
    assert [i["name"] for i in lookup_regulations(db, "C3H6O")["items"]] == ["Acetone"]


# ── bản JSON kèm repo ──────────────────────────────────────────────────────────────────────

def test_bundled_json_matches_the_loader_shape_and_has_all_four_appendices():
    path = Path(L.__file__).parent / "data" / "nd24_2026_regulations.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    assert {i["list_code"] for i in items} == {PL1, PL2, PL3, PL4}
    assert len(items) > 1300
    keys = set(_item(PL1, "1", "x"))
    assert all(set(i) == keys for i in items)
    #  Mọi số CAS đã qua chuẩn hóa: hoặc rỗng, hoặc đúng dạng.
    import re
    assert all(not i["cas_no"] or re.fullmatch(r"\d{2,7}-\d{2}-\d", i["cas_no"]) for i in items)
    #  Ngưỡng tồn trữ chỉ có ở phụ lục IV; ngưỡng hỗn hợp chỉ ở II (5%) và III (1% / 5%).
    assert all(i["threshold_kg"] is None for i in items if i["list_code"] != PL4)
    assert {i["mixture_pct"] for i in items if i["list_code"] == PL2} == {5.0}
    assert {i["mixture_pct"] for i in items if i["list_code"] == PL3} == {1.0, 5.0}
    assert {i["mixture_pct"] for i in items if i["list_code"] in (PL1, PL4)} == {None}
