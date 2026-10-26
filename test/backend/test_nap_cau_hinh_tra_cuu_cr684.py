"""duoc-CR-684 — bộ nạp cấu hình Tra cứu thị trường (từ khóa nhãn, nhóm đồng nghĩa, mã dạng chế phẩm)."""
import json

from app.modules.customs.constants import ProductKind
from app.modules.customs.model import CustomsFormulationCode, CustomsKindKeyword, CustomsSearchSynonym
from scripts.load_customs_lookup_config_cr684 import DEFAULT_DATA, run


def _data():
    with open(DEFAULT_DATA, encoding="utf-8") as fh:
        return json.load(fh)


def _seed_default_keywords(db):
    for kw in ("TC", "TECH", "TG", "TECHNICAL", "KỸ THUẬT", "NGUYÊN LIỆU"):
        db.add(CustomsKindKeyword(keyword=kw, kind=int(ProductKind.TECHNICAL)))
    db.commit()


def test_du_lieu_nguon_hop_le():
    d = _data()
    assert len(d["kind_keywords"]) == 10 and len(d["synonym_groups"]) == 10
    codes = [c["code"] for c in d["formulation_codes"]]
    assert len(codes) == len(set(codes)) == 18 and "WDG" in codes and "WG / WDG" not in codes
    # Tệp dặn KHÔNG thêm EC/SC/WP làm từ khóa Thành phẩm.
    assert not any(k["keyword"] in {"EC", "SC", "WP"} for k in d["kind_keywords"])


def test_nap_hai_lan_khong_trung(db):
    _seed_default_keywords(db)
    first = run(db, _data(), retag=False)
    assert len(first["kind_keywords"]["new"]) == 4 and len(first["kind_keywords"]["present"]) == 6
    assert len(first["synonym_groups"]["new"]) == 10
    assert len(first["formulation_codes"]["new"]) == 18

    second = run(db, _data(), retag=False)
    for rep in second.values():
        assert rep is None or (not rep["new"] and not rep["merged"] and not rep["skipped"])
    assert db.query(CustomsKindKeyword).count() == 10
    assert db.query(CustomsSearchSynonym).count() == 10
    assert db.query(CustomsFormulationCode).count() == 18


def test_dry_run_khong_ghi(db):
    rep = run(db, _data(), dry_run=True)
    assert len(rep["formulation_codes"]["new"]) == 18
    assert db.query(CustomsFormulationCode).count() == 0
    assert db.query(CustomsSearchSynonym).count() == 0


def test_dong_nghia_gop_khong_trung_va_khong_de(db):
    db.add(CustomsSearchSynonym(term="wg", synonyms="WDG; Hạt mịn", note="người dùng sửa", is_active=False))
    db.commit()
    rep = run(db, _data(), retag=False)
    assert any(s.startswith("WG") for s in rep["synonym_groups"]["merged"])
    row = db.query(CustomsSearchSynonym).filter(CustomsSearchSynonym.term == "wg").one()
    parts = [p.strip() for p in row.synonyms.split(";")]
    assert parts[:2] == ["WDG", "Hạt mịn"]                       # giữ từ cũ, đúng thứ tự
    assert [p.casefold() for p in parts].count("wdg") == 1        # không lặp WDG từ tệp
    assert {"CỐM PHÂN TÁN", "DẠNG CỐM"} <= set(parts)
    assert row.note == "người dùng sửa" and row.is_active is False  # không đè
    assert db.query(CustomsSearchSynonym).filter(CustomsSearchSynonym.term.in_(["WG", "wg"])).count() == 1


def test_tu_khoa_da_co_khac_loai_hoac_tat_duoc_giu_nguyen(db):
    db.add(CustomsKindKeyword(keyword="TK", kind=int(ProductKind.FINISHED), is_active=True))
    db.add(CustomsKindKeyword(keyword="nlsx", kind=int(ProductKind.TECHNICAL), is_active=False))
    db.commit()
    rep = run(db, _data(), retag=False)["kind_keywords"]
    assert len(rep["skipped"]) == 2 and "TK" not in rep["new"] and "NLSX" not in rep["new"]
    assert db.query(CustomsKindKeyword).filter(CustomsKindKeyword.keyword == "TK").one().kind == 1


def test_ma_dang_che_pham_chi_dien_o_trong(db):
    db.add(CustomsFormulationCode(code="EC", name_en="", name_vi="Nhũ dầu (đã sửa)", description=""))
    db.commit()
    run(db, _data(), retag=False)
    ec = db.query(CustomsFormulationCode).filter(CustomsFormulationCode.code == "EC").one()
    assert ec.name_vi == "Nhũ dầu (đã sửa)" and ec.name_en == "Emulsifiable concentrate"


def test_nap_tu_khoa_moi_tu_gan_lai_nhan(db):
    _seed_default_keywords(db)
    rep = run(db, _data())
    assert rep["retag"] is not None and rep["retag"]["total"] == 0
