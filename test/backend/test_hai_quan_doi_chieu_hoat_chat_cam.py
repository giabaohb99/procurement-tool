"""Đối chiếu HAI CHIỀU danh mục thuốc BVTV ↔ hoạt chất CẤM TT 75/2025 (29/09/2026).

Canh mấy chỗ dễ lủng nhất:
  · dương tính giả Chlorpyrifos METHYL (không cấm) dính Chlorpyrifos ETHYL (cấm) — bản cào 28/09
    có đúng 10 thuốc methyl, khớp theo từ đầu là gắn cờ oan cả 10;
  · «2,4-D» không được bị bóc mất «2,4» như một con số hàm lượng;
  · danh mục thuốc CHƯA nạp thì màn Pháp lý không được nói «0 thuốc» (chưa đối chiếu gì cả);
  · chỉ danh sách TT 75 đang dùng mới được đem ra đối chiếu.
"""
import pytest

from app.modules.customs import banned_ingredient_match as M
from app.modules.customs import pesticide_service as S
from app.modules.customs import regulation_browse_service as B
from app.modules.customs.constants import PesticideStatus, RegulationList
from app.modules.customs.model import CustomsPesticide, CustomsRegulation

TT75 = int(RegulationList.BANNED_TT75)


def _reg(db, name, list_code=TT75, **kw):
    reg = CustomsRegulation(list_code=list_code, name=name, cas_no=kw.pop("cas_no", ""),
                            legal_basis=kw.pop("legal_basis", "TT 75/2025/TT-BNNMT"), **kw)
    db.add(reg)
    db.flush()
    return reg


def _drug(db, trade, active, status=PesticideStatus.ACTIVE):
    p = CustomsPesticide(trade_name=trade, trade_key=trade.upper(), active_ingredient=active,
                         status=int(status))
    db.add(p)
    db.flush()
    return p


@pytest.mark.parametrize("raw, expected", [
    ("Chlorpyrifos Methyl (min 96%) + Pymetrozine 120g/kg", ["CHLORPYRIFOS METHYL", "PYMETROZINE"]),
    ("Alpha-cypermethrin 20%w/w + Chlorpyrifos-methyl 30%w/w", ["ALPHA CYPERMETHRIN", "CHLORPYRIFOS METHYL"]),
    ("2,4-D 600g/l", ["2 4 D"]),
    ("Chất an toàn Fenclorim 50g/l + Pretilachlor 300g/l", ["FENCLORIM", "PRETILACHLOR"]),
    ("Dầu tỏi 10% + Matrine 0.5%", ["MATRINE"]),
    ("Paraquat 276 g/ l", ["PARAQUAT"]),
    ("Paraquat 20 SL + Carbofuran 3GR", ["PARAQUAT", "CARBOFURAN"]),
    ("Dinotefuran 250G/KG", ["DINOTEFURAN"]),
    ("Emamectin benzoate (Avermectin B1a 90 % + Avermectin B1b 10%)", ["EMAMECTIN BENZOATE"]),
    ("Paraquat\xa0dichloride 276g/l", ["PARAQUAT DICHLORIDE"]),
    ("\uf061 - Naphthalene Acetic Acid 30g/l", ["ALPHA NAPHTHALENE ACETIC ACID"]),
    ("", []),
    ("+ ; 10%", []),
])
def test_split_active_ingredients(raw, expected):
    assert M.split_active_ingredients(raw) == expected


def test_methyl_is_not_flagged_as_the_banned_ethyl(db):
    ethyl = _reg(db, "Chlorpyrifos ethyl")
    matcher = M.load_matcher(db)
    assert matcher.match("Chlorpyrifos Methyl 300g/kg + Pymetrozine 120g/kg") == []
    assert matcher.match("Chlorpyrifos-methyl 30%w/w") == []
    assert matcher.match("Chlorpyrifos Ethyl 480g/l") == [ethyl]


def test_bare_banned_head_does_not_swallow_a_longer_name(db):
    _reg(db, "Chlorpyrifos")
    assert M.load_matcher(db).match("Chlorpyrifos methyl 250g/l") == []


def test_salt_and_formulation_suffixes_still_match(db):
    paraquat, glyphosate, d24 = _reg(db, "Paraquat"), _reg(db, "Glyphosate"), _reg(db, "2,4-D")
    matcher = M.load_matcher(db)
    assert matcher.match("Paraquat dichloride 276g/l") == [paraquat]
    assert matcher.match("Glyphosate isopropylamine salt 480g/l") == [glyphosate]
    assert matcher.match("2,4-D dimethylamine salt 600g/l") == [d24]
    assert matcher.match("2,4-D 600g/l + Glyphosate IPA salt 10%") == [d24, glyphosate]


def test_overlapping_banned_names_both_count_the_salt_form(db):
    """Review 29/09: bộ khớp dừng ở tầng trúng đầu tiên thì «Paraquat dichloride» chỉ đếm cho một
    dòng, và dòng nào thắng tùy bộ khớp dựng từ những dòng nào — số trên màn Pháp lý lệch danh
    sách nó mở ra."""
    salt, base = _reg(db, "Paraquat dichloride"), _reg(db, "Paraquat")
    drug = _drug(db, "Aaa 20SL", "Paraquat dichloride 276g/l")
    db.commit()
    assert M.load_matcher(db).match(drug.active_ingredient) == [salt, base]
    _, items = B.list_regulations(db, "Paraquat", TT75, 0, 50)
    for reg in items:
        assert reg["pesticide_count"] == 1
        assert S.list_pesticides(db, "", None, "", "", 0, 50, banned_regulation_id=reg["id"])[0] == 1
    #  Tìm chỉ ra MỘT dòng trên trang vẫn phải đếm như khi đủ trang.
    _, only = B.list_regulations(db, "dichloride", TT75, 0, 50)
    assert [(i["name"], i["pesticide_count"]) for i in only] == [("Paraquat dichloride", 1)]


def test_banned_name_without_any_key_is_not_reported_as_zero(db):
    _reg(db, "Hợp chất thủy ngân")
    _drug(db, "Aaa 480EC", "Chlorpyrifos Ethyl 480g/l")
    db.commit()
    item = B.list_regulations(db, "", TT75, 0, 50)[1][0]
    assert item["pesticide_matchable"] is False and item["pesticide_count"] is None


def test_alternate_names_after_comma_and_in_parentheses(db):
    bhc = _reg(db, "BHC, Lindane")
    mp = _reg(db, "Methyl Parathion (Parathion methyl)")
    matcher = M.load_matcher(db)
    assert matcher.match("Lindane 10%") == [bhc]
    assert matcher.match("BHC") == [bhc]
    assert matcher.match("Parathion-methyl 50%") == [mp]
    assert matcher.match("Parathion 50%") == [], "tên ngắn hơn tên cấm không được khớp"


def test_only_active_tt75_rows_are_used(db):
    _reg(db, "Toluene", list_code=int(RegulationList.ND24_PL4))
    _reg(db, "Endosulfan", is_active=False)
    matcher = M.load_matcher(db)
    assert matcher.match("Toluene 50%") == []
    assert matcher.match("Endosulfan 35%") == []
    assert M.build_index(db, matcher) == {}


def test_matcher_without_rules_matches_nothing():
    assert M.BannedIngredientMatcher([]).match("Paraquat 20%") == []


def _seed_catalog(db):
    ethyl, paraquat = _reg(db, "Chlorpyrifos ethyl"), _reg(db, "Paraquat")
    _reg(db, "Aldrin")
    a = _drug(db, "Aaa 480EC", "Chlorpyrifos Ethyl 480g/l")
    b = _drug(db, "Bbb 20SL", "Paraquat dichloride 276g/l + Chlorpyrifos ethyl 10%",
              status=PesticideStatus.EXPIRED)
    _drug(db, "Ccc 30EC", "Chlorpyrifos Methyl 300g/kg")
    _drug(db, "Ddd 5WG", "Emamectin benzoate 5%")
    db.commit()
    return ethyl, paraquat, a, b


def test_pesticide_list_flags_and_filters_banned(db):
    ethyl, paraquat, a, b = _seed_catalog(db)
    total, items = S.list_pesticides(db, "", None, "", "", 0, 50)
    flags = {i["trade_name"]: [x["name"] for x in i["banned"]] for i in items}
    assert total == 4
    assert flags == {"Aaa 480EC": ["Chlorpyrifos ethyl"],
                     "Bbb 20SL": ["Paraquat", "Chlorpyrifos ethyl"],
                     "Ccc 30EC": [], "Ddd 5WG": []}

    assert S.list_pesticides(db, "", None, "", "", 0, 50, banned_only=True)[0] == 2
    #  Lọc «có hoạt chất cấm» vẫn cộng dồn với lọc tình trạng — mặc định màn là «Còn hiệu lực».
    only_active = S.list_pesticides(db, "", int(PesticideStatus.ACTIVE), "", "", 0, 50, banned_only=True)
    assert [i["id"] for i in only_active[1]] == [a.id]
    by_reg = S.list_pesticides(db, "", None, "", "", 0, 50, banned_regulation_id=paraquat.id)
    assert [i["id"] for i in by_reg[1]] == [b.id]
    assert S.list_pesticides(db, "", None, "", "", 0, 50, banned_regulation_id=999999) == (0, [])


def test_banned_filter_without_rules_returns_nothing_not_everything(db):
    _drug(db, "Aaa 480EC", "Chlorpyrifos Ethyl 480g/l")
    db.commit()
    assert S.list_pesticides(db, "", None, "", "", 0, 50, banned_only=True) == (0, [])


def test_options_and_detail_report_banned(db):
    ethyl, paraquat, a, b = _seed_catalog(db)
    opt = S.options(db)
    assert opt["banned_rules"] == 3 and opt["banned_count"] == 2
    detail = S.get_pesticide(db, b.id)
    assert [x["id"] for x in detail["banned"]] == [paraquat.id, ethyl.id]
    assert detail["banned"][0]["legal_basis"] == "TT 75/2025/TT-BNNMT"


def test_options_tell_missing_rules_apart_from_zero_hits(db):
    _drug(db, "Ddd 5WG", "Emamectin benzoate 5%")
    db.commit()
    opt = S.options(db)
    assert opt["banned_rules"] == 0 and opt["banned_count"] == 0


def test_regulation_list_counts_pesticides_for_banned_rows_only(db):
    _seed_catalog(db)
    _reg(db, "Toluene", list_code=int(RegulationList.ND24_PL4), threshold_kg=1000)
    db.commit()
    _, items = B.list_regulations(db, "", None, 0, 50)
    counts = {i["name"]: i["pesticide_count"] for i in items}
    assert counts == {"Toluene": None, "Aldrin": 0, "Chlorpyrifos ethyl": 2, "Paraquat": 1}


def test_regulation_counts_are_empty_when_catalog_not_loaded(db):
    _reg(db, "Paraquat")
    db.commit()
    _, items = B.list_regulations(db, "", None, 0, 50)
    assert items[0]["pesticide_count"] is None, "chưa nạp danh mục thuốc thì không được nói «0 thuốc»"


def test_regulation_count_matches_the_list_it_opens(db):
    """Số trên màn Pháp lý và danh sách mở ra từ số đó phải bằng nhau — cùng một bộ khớp."""
    _seed_catalog(db)
    _, items = B.list_regulations(db, "", TT75, 0, 50)
    for reg in items:
        total, _ = S.list_pesticides(db, "", None, "", "", 0, 50, banned_regulation_id=reg["id"])
        assert total == reg["pesticide_count"], reg["name"]
