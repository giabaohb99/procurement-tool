"""duoc-CR-744 — bấm tiêu đề cột ở "Tra cứu thị trường" phải XẾP THẬT, trên cả tập dữ liệu.

Bốn bảng chạy phân trang phía server và trước đây không đọc `sort_by`: Giá thị trường (dòng hàng hải quan),
Tra cứu hóa chất, Tra cứu Thuốc BVTV, Lịch sử nạp (lô · nhật ký lô · kết quả từng dòng). Bài này canh:

  · mỗi cột bên giao diện có một khóa xếp được (bản chép tay `*_UI_KEYS` phải khớp bài vitest cùng tên);
  · xếp theo ĐÚNG giá trị ô hiển thị (nhãn chữ, số suy ra, tên ở bảng khác…) cả hai chiều;
  · ô trống xuống cuối ở cả hai chiều (số 0 thật KHÔNG bị coi là trống);
  · lật trang không lặp / sót dòng khi nhiều dòng bằng nhau (khóa phụ id giảm dần);
  · khóa lạ không ném lỗi, về thứ tự mặc định; Excel "xuất ngay" ra cùng thứ tự;
  · mọi đường API nhận `sort_by` / `sort_dir` (soi OpenAPI, kẻo thêm khóa mà quên gắn vào controller).
"""
import io
import json
from datetime import date

import pytest
from openpyxl import load_workbook

from app.main import app
from app.modules.customs import batch_sort, line_sort, pesticide_sort, regulation_sort, service
from app.modules.customs.constants import COLUMNS
from app.modules.customs.model import (CustomsLine, CustomsParty, CustomsPesticide, CustomsPesticideUse,
                                       CustomsRegulation)
from app.modules.customs.pesticide_service import export_query, list_pesticides
from app.modules.customs.regulation_browse_service import list_regulations
from app.modules.import_tool.model import ImportBatch, ImportLog, ImportModule
from app.modules.customs import row_log

#  ── Bản chép tay khóa cột giao diện (canary: đổi cột bên TS thì sửa cả hai nơi) ──────────────────────────────
LINE_UI_KEYS = {"id", *[key for key, _ in COLUMNS], "active_ingredient", "formulation", "price_vnd_flat",
                "price_vnd_line_tax", "product_kind"}
REGULATION_UI_KEYS = {"seq_no", "list_label", "name", "name_vi", "cas_no", "formula", "limit", "obligation",
                      "pesticide_count"}
PESTICIDE_UI_KEYS = {"trade_name", "active_ingredient", "banned", "concentration", "pest_group", "registrant",
                     "registration_no", "expires_on", "status", "use_count", "sector"}
BATCH_UI_KEYS = {"id", "filename", "mode", "status", "created_count", "updated_count", "deleted_count", "range",
                 "date_fixed", "skipped_rows", "created_by_name", "finished_at"}


def _ids(items):
    return [x["id"] for x in items]


# ═══════════════════════════ 1. Canary khóa cột ═══════════════════════════════════════════════════════════
def test_moi_cot_bang_dong_hang_deu_xep_duoc():
    """38 cột của bảng dòng hàng (32 cột GTT02 + ID + 5 cột suy ra) đều có khóa xếp ở backend."""
    assert len(LINE_UI_KEYS) == 38
    assert LINE_UI_KEYS == set(line_sort.LINE_SORT_KEYS)


def test_moi_cot_bang_hoa_chat_thuoc_bvtv_va_lich_su_deu_xep_duoc():
    assert REGULATION_UI_KEYS == set(regulation_sort.REGULATION_SORT_KEYS)
    assert PESTICIDE_UI_KEYS == set(pesticide_sort.PESTICIDE_SORT_KEYS)
    assert BATCH_UI_KEYS == set(batch_sort.BATCH_SORT_KEYS)


def test_moi_duong_api_nhan_sort_by_va_sort_dir():
    """Thêm khóa xếp mà quên gắn tham số vào controller thì giao diện gửi mà backend không nghe."""
    paths = app.openapi()["paths"]
    for path in ("/api/customs/lines", "/api/customs/lines/export", "/api/customs/regulations",
                 "/api/customs/pesticides", "/api/customs/pesticides/export", "/api/customs/imports",
                 "/api/customs/imports/{bid}/logs", "/api/customs/imports/{bid}/rows"):
        names = {p["name"] for p in paths[path]["get"]["parameters"]}
        assert {"sort_by", "sort_dir"} <= names, path


# ═══════════════════════════ 2. Bảng dòng hàng ════════════════════════════════════════════════════════════
@pytest.fixture
def lines(db):
    """4 dòng hàng với đủ kiểu giá trị: trống, số 0 thật, đối tượng khác nhau, tên trùng để thử khóa phụ."""
    imp = [CustomsParty(party_type=1, dedupe_key=f"i{i}", tax_code=tax, name=name)
           for i, (tax, name) in enumerate([("0300", "Zeta"), ("0100", "Alpha"), ("0200", "Mu")])]
    par = [CustomsParty(party_type=2, dedupe_key=f"p{i}", name=name) for i, name in enumerate(["Foreign B", "Foreign A"])]
    db.add_all(imp + par)
    db.flush()
    base = dict(batch_id=1, importer_id=0, partner_id=0)
    rows = [
        dict(reg_date=date(2026, 3, 1), importer_id=imp[0].id, partner_id=par[0].id, hs_code="38089", line_no=2,
             product_name="Beta", price_usd=5, currency="USD", fx_rate=1, usd_rate=25000, quantity=100,
             transport_mode=1, rate_import=3, product_kind=2, office_code="HP"),
        dict(reg_date=date(2026, 1, 5), importer_id=imp[1].id, partner_id=par[1].id, hs_code="29", line_no=1,
             product_name="Alpha", price_usd=2, adj_price_usd=9, currency="EUR", fx_rate=1.1, usd_rate=24000,
             quantity=5, transport_mode=4, rate_import=None, product_kind=1, price_vnd_flat=77, office_code="HC"),
        dict(reg_date=date(2026, 2, 10), importer_id=imp[2].id, hs_code="30", line_no=3, product_name="Gamma",
             price_usd=None, quantity=None, transport_mode=None, rate_import=0, product_kind=0, office_code=""),
        dict(reg_date=date(2026, 2, 10), partner_id=par[0].id, hs_code="30", line_no=4, product_name="Delta",
             price_usd=7, currency="USD", fx_rate=2, usd_rate=None, quantity=50, transport_mode=2, rate_import=10,
             product_kind=1, office_code="HP"),
    ]
    objs = [CustomsLine(**{**base, **r}) for r in rows]
    db.add_all(objs)
    db.commit()
    return objs


def _line_names(db, sort_by, sort_dir="asc", **kw):
    _, items = service.list_lines(db, {}, 0, 100, sort_by, sort_dir, **kw)
    return [x["product_name"] for x in items]


def test_moi_khoa_xep_dong_hang_chay_duoc_ca_hai_chieu(db, lines):
    for key in sorted(line_sort.LINE_SORT_KEYS):
        for direction in ("asc", "desc"):
            total, items = service.list_lines(db, {}, 0, 100, key, direction)
            assert total == 4 and len(items) == 4, (key, direction)


def test_xep_theo_ten_doanh_nghiep_va_doi_tac_o_bang_khac(db, lines):
    """Tên / mã số thuế doanh nghiệp, tên đối tác nằm ở bảng đối tượng; dòng chưa gắn (id 0) xuống cuối."""
    assert _line_names(db, "importer_name", "asc") == ["Alpha", "Gamma", "Beta", "Delta"]     # Alpha · Mu · Zeta
    assert _line_names(db, "importer_name", "desc") == ["Beta", "Gamma", "Alpha", "Delta"]    # Zeta · Mu · Alpha
    assert _line_names(db, "importer_tax_code", "asc") == ["Alpha", "Gamma", "Beta", "Delta"]  # 0100 · 0200 · 0300
    assert _line_names(db, "importer_tax_code", "desc")[-1] == "Delta"
    partner = _line_names(db, "partner_name", "asc")
    assert partner[0] == "Alpha" and partner[-1] == "Gamma"      # Foreign A đứng đầu, chưa gắn xuống cuối
    assert _line_names(db, "partner_name", "desc")[-1] == "Gamma"


def test_o_trong_xuong_cuoi_ca_hai_chieu_va_so_khong_la_o_trong(db, lines):
    """`price_usd` trống ở Gamma; `rate_import = 0` của Gamma là số THẬT, đứng đầu khi xếp tăng."""
    assert _line_names(db, "price_usd", "asc")[-1] == "Gamma"
    assert _line_names(db, "price_usd", "desc")[-1] == "Gamma"
    asc = _line_names(db, "rate_import", "asc")
    assert asc[0] == "Gamma" and asc[-1] == "Alpha"             # 0 < 3 < 10 < trống
    assert _line_names(db, "rate_import", "desc")[-1] == "Alpha"
    assert _line_names(db, "office_code", "asc")[-1] == "Gamma"   # chuỗi rỗng cũng là ô trống
    assert _line_names(db, "office_code", "desc")[-1] == "Gamma"


def test_xep_theo_nhan_chu_dang_hien_thi_khong_theo_ma_so(db, lines):
    #  Kiểm bằng chính nhãn API trả về (ô đang hiển thị nhãn), không đoán mã số.
    _, items = service.list_lines(db, {}, 0, 100, "transport_mode", "asc")
    labels = [x["transport_label"] for x in items if x["transport_label"]]
    assert labels == sorted(labels)
    assert items[-1]["transport_label"] == ""                    # Gamma chưa có phương tiện
    _, items = service.list_lines(db, {}, 0, 100, "product_kind", "asc")
    kinds = [x["product_kind_label"] for x in items if x["product_kind_label"]]
    assert kinds == sorted(kinds)
    assert items[-1]["product_kind_label"] == ""                 # 0 = chưa gắn nhãn


def test_gia_vnd_xep_theo_gia_tri_dang_hien_ke_ca_khi_la_gia_tinh(db, lines):
    """Cột giá VND hiển thị giá của tệp nếu có, không thì giá tính — phải xếp theo chính con số đó."""
    for key in ("price_vnd_flat", "price_vnd_line_tax"):
        _, items = service.list_lines(db, {}, 0, 100, key, "asc")
        shown = [x[key] for x in items if x[key] is not None]
        assert shown == sorted(shown), key
        assert [x[key] is None for x in items] == sorted(x[key] is None for x in items), key
    _, items = service.list_lines(db, {}, 0, 100, "price_vnd_flat", "asc")
    # Alpha lấy 77 từ tệp; Delta tính từ 7 x fx 2 (tiền USD, thiếu usd_rate) x 1,07 = 15; Beta 5 x 25000 x 1,07.
    assert [(x["product_name"], x["price_vnd_flat"]) for x in items][:3] == [
        ("Delta", 15), ("Alpha", 77), ("Beta", 133750)]


def test_lat_trang_khong_lap_khong_sot_khi_nhieu_dong_bang_nhau(db):
    """Xếp theo cột nhiều giá trị trùng (hs_code chỉ có 3 giá trị / 30 dòng): ghép các trang phải ra đúng 30 dòng."""
    db.add_all([CustomsLine(batch_id=1, reg_date=date(2026, 1, 1 + i % 20), hs_code=f"3{i % 3}", product_name=f"P{i}")
                for i in range(30)])
    db.commit()
    for direction in ("asc", "desc"):
        seen = []
        for page in range(6):
            _, items = service.list_lines(db, {}, page * 5, 5, "hs_code", direction)
            seen += _ids(items)
        assert len(seen) == 30 and len(set(seen)) == 30, direction
    # Khóa phụ: cùng giá trị thì id GIẢM dần (bản ghi mới hơn đứng trước).
    _, items = service.list_lines(db, {}, 0, 100, "hs_code", "asc")
    groups = {}
    for it in items:
        groups.setdefault(it["hs_code"], []).append(it["id"])
    assert all(ids == sorted(ids, reverse=True) for ids in groups.values())


def test_khoa_la_hoac_rong_giu_thu_tu_mac_dinh_va_khong_loi(db, lines):
    default = _line_names(db, "")
    assert default == _line_names(db, "khong_co_cot_nay")
    assert default == _line_names(db, "id; DROP TABLE tab_customs_line")
    assert default == _line_names(db, "price_usd) desc --")
    assert default[0] == "Beta"                                  # ngày đăng ký giảm dần
    assert service.list_lines(db, {}, 0, 100, "price_usd", "ngang")[0] == 4   # chiều lạ coi như tăng


def test_loc_va_xep_di_cung_nhau_va_xep_tren_ca_tap_da_loc(db, lines):
    total, items = service.list_lines(db, {"hs_code": "30"}, 0, 100, "product_name", "desc")
    assert total == 2 and [x["product_name"] for x in items] == ["Gamma", "Delta"]
    _, page2 = service.list_lines(db, {}, 2, 2, "product_name", "asc")
    assert [x["product_name"] for x in page2] == ["Delta", "Gamma"]   # trang 2 của thứ tự toàn tập


def test_excel_xuat_ngay_ra_cung_thu_tu_voi_bang(db, lines):
    data = service.export_lines_xlsx(db, {}, "price_usd", "desc")
    sheet = load_workbook(io.BytesIO(data)).active
    ids = [row[0] for row in sheet.iter_rows(min_row=2, values_only=True)]
    _, items = service.list_lines(db, {}, 0, 100, "price_usd", "desc")
    assert ids == _ids(items)
    # Không truyền sort -> giữ thứ tự cũ (ngày giảm dần).
    default_ids = [r[0] for r in load_workbook(io.BytesIO(service.export_lines_xlsx(db, {}))).active.iter_rows(
        min_row=2, values_only=True)]
    assert default_ids == _ids(service.list_lines(db, {}, 0, 100)[1])


# ═══════════════════════════ 3. Tra cứu hóa chất ══════════════════════════════════════════════════════════
@pytest.fixture
def regulations(db):
    db.add_all([
        CustomsRegulation(list_code=1, seq_no="10", sort_order=10, name="Chem C", name_vi="Chat C", cas_no="3-3-3",
                          formula="C3", legal_basis="ND24"),
        CustomsRegulation(list_code=1, seq_no="2", sort_order=2, name="Chem A", name_vi="", cas_no="1-1-1",
                          formula="", legal_basis="ND24"),
        CustomsRegulation(list_code=1, seq_no="5.1", sort_order=5, name="Chem B", name_vi="Chat B", cas_no="",
                          formula="C2", legal_basis="ND24"),
        CustomsRegulation(list_code=4, seq_no="1", sort_order=1, name="Chem D", threshold_kg=500, legal_basis="PL4"),
        CustomsRegulation(list_code=2, seq_no="", sort_order=0, name="Chem E", mixture_pct=5, legal_basis="PL2"),
        CustomsRegulation(list_code=10, seq_no="1", sort_order=1, name="Paraquat", banned_year=2019,
                          legal_basis="TT75"),
        CustomsRegulation(list_code=10, seq_no="2", sort_order=2, name="Glyphosate", banned_year=2021,
                          legal_basis="TT75"),
        CustomsRegulation(list_code=1, seq_no="99", sort_order=99, name="Chem Off", is_active=False),
    ])
    db.commit()


def _reg_names(db, sort_by, sort_dir="asc"):
    return [x["name"] for x in list_regulations(db, "", None, 0, 100, sort_by, sort_dir)[1]]


def test_moi_khoa_xep_hoa_chat_chay_duoc(db, regulations):
    for key in sorted(regulation_sort.REGULATION_SORT_KEYS):
        for direction in ("asc", "desc"):
            total, items = list_regulations(db, "", None, 0, 100, key, direction)
            assert total == 7 and len(items) == 7, (key, direction)      # dòng ngừng dùng không vào bảng


def test_stt_xep_theo_so_khong_theo_chu(db, regulations):
    """STT là chữ trong DB nhưng hiển thị như số: "2" phải đứng trước "10", "5.1" đi theo "5"."""
    _, items = list_regulations(db, "", 1, 0, 100, "seq_no", "asc")
    assert [x["seq_no"] for x in items] == ["2", "5.1", "10"]
    _, items = list_regulations(db, "", 1, 0, 100, "seq_no", "desc")
    assert [x["seq_no"] for x in items] == ["10", "5.1", "2"]
    assert _reg_names(db, "seq_no", "asc")[-1] == "Chem E"                 # STT trống xuống cuối
    assert _reg_names(db, "seq_no", "desc")[-1] == "Chem E"


def test_hoa_chat_o_trong_xuong_cuoi_va_nhan_phu_luc_xep_theo_ma(db, regulations):
    assert _reg_names(db, "cas_no", "asc")[-1] == "Chem B"       # CAS rỗng
    assert _reg_names(db, "cas_no", "desc")[-1] == "Chem B"
    names = _reg_names(db, "list_label", "asc")
    assert names[-2:] in (["Paraquat", "Glyphosate"], ["Glyphosate", "Paraquat"])   # list_code 10 sau cùng
    assert names[0] in ("Chem C", "Chem A", "Chem B")                              # phụ lục I đứng đầu


def test_cot_nguong_xep_theo_loai_roi_theo_gia_tri(db, regulations):
    """Cấm (theo năm) -> ngưỡng kg -> ngưỡng hỗn hợp % -> không có ngưỡng; cùng loại thì theo giá trị."""
    asc = _reg_names(db, "limit", "asc")
    assert asc[:2] == ["Paraquat", "Glyphosate"]                 # năm cấm 2019 < 2021
    assert asc[2] == "Chem D" and asc[3] == "Chem E"
    desc = _reg_names(db, "limit", "desc")
    assert desc[:2] == ["Glyphosate", "Paraquat"]
    assert set(asc[4:]) == {"Chem A", "Chem B", "Chem C"} == set(desc[4:])      # không ngưỡng luôn ở cuối


def test_cot_luu_y_xep_theo_loai_cau(db, regulations):
    asc = _reg_names(db, "obligation", "asc")
    assert set(asc[:2]) == {"Paraquat", "Glyphosate"} and asc[2] == "Chem D"     # cấm -> có ngưỡng kg -> còn lại


def test_so_thuoc_chua_hoat_chat_cam_xep_duoc_dong_khong_co_so_xuong_cuoi(db, regulations):
    db.add_all([
        CustomsPesticide(trade_name="T1", active_ingredient="Paraquat dichloride", status=1),
        CustomsPesticide(trade_name="T2", active_ingredient="Paraquat", status=1),
        CustomsPesticide(trade_name="T3", active_ingredient="Abamectin", status=1),
    ])
    db.commit()
    _, items = list_regulations(db, "", 10, 0, 100, "pesticide_count", "desc")
    assert [(x["name"], x["pesticide_count"]) for x in items] == [("Paraquat", 2), ("Glyphosate", 0)]
    _, items = list_regulations(db, "", 10, 0, 100, "pesticide_count", "asc")
    assert [x["name"] for x in items] == ["Glyphosate", "Paraquat"]
    # Dòng không phải TT 75 không có số -> xuống cuối ở cả hai chiều.
    assert _reg_names(db, "pesticide_count", "asc")[-1] not in ("Paraquat", "Glyphosate")
    assert _reg_names(db, "pesticide_count", "desc")[-1] not in ("Paraquat", "Glyphosate")


def test_hoa_chat_khoa_la_giu_thu_tu_phu_luc(db, regulations):
    default = list_regulations(db, "", None, 0, 100)[1]
    assert _ids(list_regulations(db, "", None, 0, 100, "khong_co", "asc")[1]) == _ids(default)
    assert [x["list_code"] for x in default] == sorted(x["list_code"] for x in default)


# ═══════════════════════════ 4. Tra cứu Thuốc BVTV ════════════════════════════════════════════════════════
@pytest.fixture
def pesticides(db):
    objs = [
        CustomsPesticide(trade_name="Bravo", active_ingredient="Paraquat", concentration="20SL", pest_group="Cỏ",
                         registrant="Cty B", registration_no="B-2", expires_on=date(2027, 1, 1), status=2,
                         sector="Lúa"),
        CustomsPesticide(trade_name="Alpha", active_ingredient="Abamectin", concentration="", pest_group="Sâu",
                         registrant="Cty A", registration_no="A-1", expires_on=date(2026, 6, 1), status=1,
                         sector=""),
        CustomsPesticide(trade_name="Charlie", active_ingredient="Glyphosate", concentration="48SL", pest_group="",
                         registrant="", registration_no="C-3", expires_on=None, status=0, sector="Cà phê"),
        CustomsPesticide(trade_name="Delta", active_ingredient="Abamectin", concentration="1.8EC", pest_group="Sâu",
                         registrant="Cty A", registration_no="D-4", expires_on=date(2026, 6, 1), status=3,
                         sector="Lúa"),
    ]
    db.add_all(objs)
    db.add(CustomsRegulation(list_code=10, seq_no="1", sort_order=1, name="Paraquat", banned_year=2019))
    db.add(CustomsRegulation(list_code=10, seq_no="2", sort_order=2, name="Glyphosate", banned_year=2021))
    db.flush()
    db.add_all([CustomsPesticideUse(pesticide_id=objs[0].id, crop="Lúa"),
                CustomsPesticideUse(pesticide_id=objs[0].id, crop="Ngô"),
                CustomsPesticideUse(pesticide_id=objs[3].id, crop="Lúa")])
    db.commit()
    return objs


def _pest_names(db, sort_by, sort_dir="asc"):
    return [x["trade_name"] for x in list_pesticides(db, "", None, "", "", 0, 100, False, None, sort_by,
                                                     sort_dir)[1]]


def test_moi_khoa_xep_thuoc_bvtv_chay_duoc(db, pesticides):
    for key in sorted(pesticide_sort.PESTICIDE_SORT_KEYS):
        for direction in ("asc", "desc"):
            total, items = list_pesticides(db, "", None, "", "", 0, 100, False, None, key, direction)
            assert total == 4 and len(items) == 4, (key, direction)


def test_thuoc_o_trong_xuong_cuoi_ca_hai_chieu(db, pesticides):
    assert _pest_names(db, "concentration", "asc")[-1] == "Alpha"      # rỗng
    assert _pest_names(db, "concentration", "desc")[-1] == "Alpha"
    assert _pest_names(db, "expires_on", "asc")[-1] == "Charlie"       # NULL
    assert _pest_names(db, "expires_on", "desc")[-1] == "Charlie"
    assert _pest_names(db, "registrant", "asc")[-1] == "Charlie"
    assert _pest_names(db, "sector", "desc")[-1] == "Alpha"


def test_tinh_trang_xep_theo_vong_doi_ma_so_va_chua_ro_xuong_cuoi(db, pesticides):
    asc = _pest_names(db, "status", "asc")
    assert asc[:3] == ["Alpha", "Bravo", "Delta"] and asc[-1] == "Charlie"   # 1 Còn hiệu lực, 2 Hết, 3 Đang dùng
    desc = _pest_names(db, "status", "desc")
    assert desc[:3] == ["Delta", "Bravo", "Alpha"] and desc[-1] == "Charlie"


def test_pham_vi_su_dung_dem_dong_va_thuoc_khong_co_xuong_cuoi(db, pesticides):
    assert _pest_names(db, "use_count", "desc")[:2] == ["Bravo", "Delta"]
    assert _pest_names(db, "use_count", "asc")[:2] == ["Delta", "Bravo"]
    assert set(_pest_names(db, "use_count", "asc")[2:]) == {"Alpha", "Charlie"}


def test_hoat_chat_cam_xep_theo_ten_nhan_dau_tien_thuoc_khong_dinh_cam_xuong_cuoi(db, pesticides):
    asc = _pest_names(db, "banned", "asc")
    assert asc[:2] == ["Charlie", "Bravo"]          # Glyphosate < Paraquat
    assert set(asc[2:]) == {"Alpha", "Delta"}
    desc = _pest_names(db, "banned", "desc")
    assert desc[:2] == ["Bravo", "Charlie"] and set(desc[2:]) == {"Alpha", "Delta"}


def test_thuoc_xuat_excel_trang_hien_tai_ra_cung_thu_tu_voi_bang(db, pesticides):
    q = export_query(db, "", None, "", "", False, None, "registration_no", "desc")
    shown = [x["registration_no"] for x in list_pesticides(db, "", None, "", "", 0, 100, False, None,
                                                           "registration_no", "desc")[1]]
    assert [p.registration_no for p in q.all()] == shown == ["D-4", "C-3", "B-2", "A-1"]
    default = export_query(db, "", None, "", "").all()
    assert [p.trade_name for p in default] == ["Alpha", "Bravo", "Charlie", "Delta"]


def test_thuoc_khoa_la_ve_thu_tu_theo_ten(db, pesticides):
    assert _pest_names(db, "zzz") == ["Alpha", "Bravo", "Charlie", "Delta"]
    assert _pest_names(db, "") == ["Alpha", "Bravo", "Charlie", "Delta"]


# ═══════════════════════════ 5. Lịch sử nạp ═══════════════════════════════════════════════════════════════
@pytest.fixture
def batches(db, seed):
    def batch(name, mode, status, created, info, created_by):
        b = ImportBatch(module=ImportModule.CUSTOMS_DECLARATION, mode=mode, filename=name, status=status,
                        created_count=created, sheet_info=info, created_by=created_by)
        db.add(b)
        return b
    objs = [
        batch("b.xlsx", 1, 2, 10, json.dumps({"date_from": "2026-02-01", "date_to": "2026-02-28", "date_fixed": 3,
                                              "existing_rows": 5, "duplicate_rows": 1}), seed.u_req_id),
        batch("a.xlsx", 0, 2, 7, json.dumps({"date_from": "2026-01-01", "date_to": "2026-01-31", "date_fixed": 0,
                                             "existing_rows": 0, "duplicate_rows": 0}), 0),
        batch("c.xlsx", 1, 3, 4, "not json at all", seed.u_nstm_id),       # JSON hỏng không được làm sập cả danh sách
        batch("d.xlsx", 1, 4, 1, "", 0),                                   # sheet_info rỗng
        batch("e.xlsx", 1, 1, 0, json.dumps({"date_from": "2026-03-01", "date_to": "2026-03-05", "date_fixed": 12,
                                             "existing_rows": 20, "duplicate_rows": 0}), seed.u_req_id),
    ]
    db.commit()
    return objs


def _batch_names(db, sort_by, sort_dir="asc"):
    order = batch_sort.batch_order(db, sort_by, sort_dir)
    q = db.query(ImportBatch).filter(ImportBatch.module == ImportModule.CUSTOMS_DECLARATION)
    return [b.filename for b in q.order_by(*order).all()]


def test_moi_khoa_xep_lo_nap_chay_duoc_ke_ca_json_hong(db, batches):
    for key in sorted(batch_sort.BATCH_SORT_KEYS):
        for direction in ("asc", "desc"):
            assert len(_batch_names(db, key, direction)) == 5, (key, direction)


def test_lo_xep_theo_nhan_trang_thai_dang_hien_thi(db, batches):
    """Nhãn ghép từ trạng thái + chế độ: Chạy thử xong · Đã ghi · Đang chạy · Lỗi · Đã hoàn tác."""
    asc = _batch_names(db, "status", "asc")
    labels = {"a.xlsx": "Chạy thử xong", "b.xlsx": "Đã ghi", "c.xlsx": "Lỗi", "d.xlsx": "Đã hoàn tác",
              "e.xlsx": "Đang chạy"}
    assert [labels[n] for n in asc] == sorted(labels.values())
    assert [labels[n] for n in _batch_names(db, "status", "desc")] == sorted(labels.values(), reverse=True)


def test_lo_xep_theo_truong_trong_json_sheet_info_json_hong_xuong_cuoi(db, batches):
    assert _batch_names(db, "date_fixed", "desc")[:2] == ["e.xlsx", "b.xlsx"]
    asc = _batch_names(db, "range", "asc")
    assert asc[:3] == ["a.xlsx", "b.xlsx", "e.xlsx"] and set(asc[3:]) == {"c.xlsx", "d.xlsx"}
    assert set(_batch_names(db, "range", "desc")[3:]) == {"c.xlsx", "d.xlsx"}      # trống cuối cả hai chiều
    assert _batch_names(db, "skipped_rows", "desc")[:2] == ["e.xlsx", "b.xlsx"]       # 20 · 6
    assert _batch_names(db, "skipped_rows", "asc")[-1] == "e.xlsx"


def test_lo_xep_theo_nguoi_nap_he_thong_la_ten_that(db, batches):
    asc = _batch_names(db, "created_by_name", "asc")
    # "Hệ thống" (id 0) · "Người YC" · "NSTM Chính" — xếp theo chữ.
    names = {"a.xlsx": "Hệ thống", "d.xlsx": "Hệ thống", "b.xlsx": "Người YC", "e.xlsx": "Người YC",
             "c.xlsx": "NSTM Chính"}
    assert [names[n] for n in asc] == sorted(names.values())


def test_lo_mac_dinh_la_moi_nhat_len_dau_va_khoa_la_bi_bo_qua(db, batches):
    assert batch_sort.batch_order(db, "", "asc") is None
    assert batch_sort.batch_order(db, "abc", "asc") is None
    assert _batch_names(db, "id", "desc")[0] == "e.xlsx"


def test_nhat_ky_lo_va_ket_qua_tung_dong_xep_duoc(db, batches):
    b = batches[0]
    db.add_all([
        ImportLog(batch_id=b.id, row_no=3, level=1, message="b", row_status=0),
        ImportLog(batch_id=b.id, row_no=0, level=3, message="", row_status=0),
        ImportLog(batch_id=b.id, row_no=1, level=0, message="a", row_status=0),
        ImportLog(batch_id=b.id, row_no=5, level=0, message="x", ref_key="Zeta", row_status=1),
        ImportLog(batch_id=b.id, row_no=2, level=0, message="y", ref_key="Alpha", row_status=2),
        ImportLog(batch_id=b.id, row_no=4, level=0, message="z", ref_key="", row_status=4),
    ])
    db.commit()
    pg = {"offset": 0, "limit": 100}
    _, logs = batch_sort.list_logs(db, b.id, None, pg, "row_no", "asc")
    assert [x.row_no for x in logs] == [1, 3, 0]                 # số dòng 0 = không có -> xuống cuối
    _, logs = batch_sort.list_logs(db, b.id, None, pg, "row_no", "desc")
    assert [x.row_no for x in logs] == [3, 1, 0]
    _, logs = batch_sort.list_logs(db, b.id, None, pg, "message", "asc")
    assert [x.message for x in logs] == ["a", "b", ""]
    _, logs = batch_sort.list_logs(db, b.id, None, pg, "", "asc")           # mặc định: mức giảm dần
    assert [x.level for x in logs] == [3, 1, 0]

    _, rows = row_log.list_rows(db, b.id, None, pg, "product_name", "asc")
    assert [x["product_name"] for x in rows] == ["Alpha", "Zeta", ""]
    _, rows = row_log.list_rows(db, b.id, None, pg, "row_no", "desc")
    assert [x["row_no"] for x in rows] == [5, 4, 2]
    _, rows = row_log.list_rows(db, b.id, None, pg)
    assert [x["row_no"] for x in rows] == [2, 4, 5]               # mặc định theo số dòng trong tệp
    _, rows = row_log.list_rows(db, b.id, None, pg, "row_status", "asc")
    assert len(rows) == 3
