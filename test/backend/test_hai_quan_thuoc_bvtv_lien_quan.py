"""Hai khối «Sản phẩm khác cùng công ty» / «Thuốc cùng hoạt chất» của trang chi tiết thuốc BVTV
(01/10/2026, bê theo danhmuc.thuocbvtv.com). Canh luật khớp hoạt chất — thứ dễ lệch nhất: phải
bỏ hàm lượng + ngoặc, không phụ thuộc thứ tự, và KHÔNG khớp tập con (một hoạt chất ≠ hỗn hợp).
"""
import pytest
from fastapi import HTTPException

from app.modules.customs import pesticide_related_service as R
from app.modules.customs.model import CustomsPesticide
from app.modules.customs.pesticide_controller import router


def _add(db, name, ingredient, registrant="Công ty TNHH Ngân Anh", group="Thuốc trừ bệnh"):
    p = CustomsPesticide(trade_name=name, trade_key=name.upper(), active_ingredient=ingredient,
                         registrant=registrant, pest_group=group)
    db.add(p)
    db.flush()
    return p


@pytest.mark.parametrize("raw, names", [
    ("Chitosan 2% + Oligo-Alginate 10%", ["Chitosan", "Oligo-Alginate"]),
    ("Buprofezin 400g/l + Deltamethrin 50g/l", ["Buprofezin", "Deltamethrin"]),
    ("Nitenpyram 200 g/kg + Pymetrozine 600 g/kg", ["Nitenpyram", "Pymetrozine"]),
    ("Fenpropathrin (min 90 %)", ["Fenpropathrin"]),
    #  Tên mở đầu bằng số và tên có dấu phẩy bên trong — không được cắt nhầm.
    ("28-epihomobrassinolide 0.002% + Gibberellic acid A4, A7 0.398%",
     ["28-epihomobrassinolide", "Gibberellic acid A4, A7"]),
    ("Bacillus thuringiensis var. kurstaki", ["Bacillus thuringiensis var. kurstaki"]),
    ("", []),
    ("  +  ", []),
])
def test_ingredient_names_drop_amounts_and_brackets(raw, names):
    assert R.ingredient_names(raw) == names


def test_key_ignores_order_case_and_amounts():
    assert R.ingredient_key("Chitosan 2% + Oligo-Alginate 10%") == \
        R.ingredient_key("OLIGO-ALGINATE 5% + chitosan 3%")


def test_same_ingredient_matches_the_set_not_a_subset(db):
    me = _add(db, "2S Sea & See 12WP", "Chitosan 2% + Oligo-Alginate 10%")
    twin = _add(db, "2S Sea & See 12SL", "Oligo-Alginate 8% + Chitosan 4%", registrant="Công ty B")
    _add(db, "Chỉ Chitosan", "Chitosan 5%")                                   # tập con
    _add(db, "Ba hoạt chất", "Chitosan 2% + Oligo-Alginate 10% + Kasugamycin 2%")  # tập cha
    out = R.related_pesticides(db, me.id)["same_ingredient"]
    assert out["label"] == "Chitosan + Oligo-Alginate"
    assert out["total"] == 1
    assert [i["id"] for i in out["items"]] == [twin.id]


def test_same_registrant_excludes_itself_and_caps_at_limit(db):
    me = _add(db, "A gốc", "Mancozeb 80%")
    for i in range(R.RELATED_LIMIT + 3):
        _add(db, f"Sp {i:02d}", "Abamectin 1.8%")
    _add(db, "Công ty khác", "Mancozeb 80%", registrant="Công ty Khác")
    out = R.related_pesticides(db, me.id)["same_registrant"]
    assert out["total"] == R.RELATED_LIMIT + 3
    assert len(out["items"]) == R.RELATED_LIMIT
    assert me.id not in [i["id"] for i in out["items"]]
    assert out["items"][0]["trade_name"] == "Sp 00"   # xếp theo tên


def test_expanded_limit_returns_everything_up_to_the_cap(db):
    me = _add(db, "A gốc", "Mancozeb 80%")
    for i in range(R.RELATED_LIMIT + 3):
        _add(db, f"Sp {i:02d}", "Mancozeb 64%")
    out = R.related_pesticides(db, me.id, limit=R.MAX_RELATED_LIMIT)
    assert len(out["same_registrant"]["items"]) == R.RELATED_LIMIT + 3
    assert len(out["same_ingredient"]["items"]) == R.RELATED_LIMIT + 3
    #  Gọi thẳng service với số rác vẫn bị kẹp về [1, trần] — không trả rỗng, không bung vô hạn.
    assert len(R.related_pesticides(db, me.id, limit=0)["same_registrant"]["items"]) == 1


def test_blank_registrant_and_ingredient_match_nothing(db):
    #  Thuốc tự thêm còn trống hai ô: không được gom mọi thuốc trống khác về "cùng công ty".
    me = _add(db, "Trống", "", registrant="")
    _add(db, "Trống 2", "", registrant="")
    out = R.related_pesticides(db, me.id)
    assert out["same_registrant"] == {"total": 0, "items": []}
    assert out["same_ingredient"]["total"] == 0


def test_missing_pesticide_is_404(db):
    with pytest.raises(HTTPException) as err:
        R.related_pesticides(db, 999999)
    assert err.value.status_code == 404


def test_route_is_registered():
    #  Quyền của đường này canh chung ở `test_hai_quan_thuoc_bvtv.test_every_route_is_guarded`.
    assert "/api/customs/pesticides/{pesticide_id}/related" in [r.path for r in router.routes]
