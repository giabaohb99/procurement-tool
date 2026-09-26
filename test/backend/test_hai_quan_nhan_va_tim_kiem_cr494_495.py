"""bao-CR-494 (nhãn Thành phẩm / Nguyên liệu) + bao-CR-495 (tìm CÓ / KHÔNG CÓ, nồng độ, đồng nghĩa).

Hai yêu cầu F04 + F02 của chị Mi (22/09, ghi chú 25/09/2026). Tiêu chí nghiệm thu chị Mi ghi:
  · F02: tìm «Abamectin» AND «3.6» NOT «TC» ra đúng nhóm thành phẩm 3.6EC, không lẫn TC/TECH;
  · F04: gắn nhãn đúng ≥ 95% trên mẫu 50 dòng — ở đây canh các ca biên: từ ngắn phải khớp
    NGUYÊN TỪ (`TC` không dính `ATC`), từ tiếng Việt có dấu, từ khóa loại Thành phẩm thắng ngược.
"""
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.customs import search_service as SS
from app.modules.customs.constants import ProductKind
from app.modules.customs.ingredient import KindTagger, load_kind_tagger, retag_all
from app.modules.customs.model import (CustomsIngredientAlias, CustomsKindKeyword, CustomsLine,
                                       CustomsSearchSynonym)
from app.modules.customs.schema import KindKeywordCreate, SearchSynonymCreate

D = date(2026, 3, 1)


def _line(db, name, **kw):
    ln = CustomsLine(reg_date=D, product_name=name, unit_code="KGM", price_usd=Decimal("1"),
                     quantity=Decimal("1"), hs_code="38089319", **kw)
    db.add(ln)
    return ln


def _default_keywords(db):
    for kw in ("TC", "TECH", "TG", "TECHNICAL", "KỸ THUẬT", "NGUYÊN LIỆU"):
        db.add(CustomsKindKeyword(keyword=kw, kind=int(ProductKind.TECHNICAL)))
    db.commit()


# ── bao-CR-494: nhãn ───────────────────────────────────────────────────────────────────────

def test_kind_tagger_default_rules_from_chi_mi():
    t = KindTagger([(k, 2) for k in ("TC", "TECH", "TG", "KỸ THUẬT", "NGUYÊN LIỆU")])
    assert t.tag("Thuốc kỹ thuật ATRAZINE 97% TECH -Nguyên liệu dùng SX") == ProductKind.TECHNICAL
    assert t.tag("ATRAZINE 97%TC") == ProductKind.TECHNICAL, "«%TC» dính liền vẫn là nguyên từ"
    assert t.tag("Abamectin 3.6EC thuốc trừ sâu") == ProductKind.FINISHED, "không khớp gì → thành phẩm"
    assert t.tag("Hóa chất ATC-200 dùng cho sơn") == ProductKind.FINISHED, "TC nằm trong ATC không tính"
    assert t.tag("Thuốc Kỹ Thuật Mancozeb") == ProductKind.TECHNICAL, "không phân biệt hoa thường, giữ dấu"
    assert t.tag("") == ProductKind.FINISHED


def test_finished_keyword_is_an_override_and_inactive_keywords_are_ignored(db):
    _default_keywords(db)
    db.add(CustomsKindKeyword(keyword="TECHNOLOGY GRADE", kind=int(ProductKind.FINISHED)))
    db.add(CustomsKindKeyword(keyword="XYZ", kind=int(ProductKind.TECHNICAL), is_active=False))
    db.commit()
    t = load_kind_tagger(db)
    assert t.tag("ATRAZINE TECH TECHNOLOGY GRADE") == ProductKind.FINISHED, "từ loại Thành phẩm thắng"
    assert t.tag("Chất XYZ") == ProductKind.FINISHED, "từ khóa ngừng dùng không còn tác dụng"


def test_retag_all_writes_product_kind_for_every_line(db):
    _default_keywords(db)
    tech = _line(db, "Thuốc kỹ thuật ATRAZINE 97% TECH")
    fin = _line(db, "Abamectin 3.6EC")
    db.commit()
    assert tech.product_kind == 0 and fin.product_kind == 0, "dòng cũ chưa gắn = 0"
    out = retag_all(db)
    db.expire_all()
    assert out["total"] == 2 and out["technical"] == 1
    assert tech.product_kind == ProductKind.TECHNICAL and fin.product_kind == ProductKind.FINISHED


def test_keyword_schema_trims_and_rejects_bad_kind():
    assert KindKeywordCreate(keyword="  kỹ   thuật ").keyword == "kỹ thuật"
    with pytest.raises(ValidationError):
        KindKeywordCreate(keyword="   ")
    with pytest.raises(ValidationError):
        KindKeywordCreate(keyword="TC", kind=7)


# ── bao-CR-495: cú pháp ô tìm ─────────────────────────────────────────────────────────────

def test_parse_query_supports_and_not_quotes_and_dedupes():
    p = SS.parse_query('Abamectin 3.6 -TC !TECH NOT "nguyên liệu" and abamectin')
    assert p.include == ["Abamectin", "3.6"]
    assert p.exclude == ["TC", "TECH", "nguyên liệu"]
    assert SS.parse_query("   ").empty
    assert SS.parse_query("-").empty, "dấu trừ trơ không thành từ rỗng"
    assert len(SS.parse_query(" ".join(f"w{i}" for i in range(40))).include) == 10, "trần 10 từ"


def test_concentration_variants_percent_and_grams_per_litre_are_equivalent():
    assert SS.concentration_variants("3,6%") == ["3.6", "3,6", "36G/L", "36 G/L"]
    assert SS.concentration_variants("36 g/l") == ["3.6", "3,6", "36G/L", "36 G/L"]
    assert SS.concentration_variants("3.6EC") == ["3.6", "3,6", "36G/L", "36 G/L"]
    assert SS.concentration_variants("3.6% W/W") == ["3.6", "3,6", "36G/L", "36 G/L"]
    assert SS.concentration_variants("97%")[:2] == ["97", "97"] or SS.concentration_variants("97%")[0] == "97"
    assert SS.concentration_variants("Abamectin") == []
    assert SS.concentration_variants("3.6.5%") == []


def test_expand_term_uses_user_synonyms_and_ingredient_aliases(db):
    db.add(CustomsSearchSynonym(term="Abamectin", synonyms="Abamectine; Aba"))
    db.add(CustomsIngredientAlias(keyword="EMAMECTIN", canonical="EMAMECTIN BENZOATE"))
    db.commit()
    groups = SS.load_synonym_groups(db)
    assert SS.expand_term("aba", groups) == ["aba", "Abamectin", "Abamectine"]
    assert SS.expand_term("emamectin benzoate", groups) == ["emamectin benzoate", "EMAMECTIN"]
    assert SS.expand_term("Kasugamycin", groups) == ["Kasugamycin"]


def test_acceptance_case_f02_abamectin_and_36_not_tc(db):
    """Nghiệm thu F02 của chị Mi: «Abamectin» AND «3.6» NOT «TC» → chỉ nhóm thành phẩm 3.6EC."""
    ec = _line(db, "Thuốc trừ sâu ABAMECTIN 3.6EC")
    gl = _line(db, "Abamectin 36 g/l SC — hàng mới")
    comma = _line(db, "ABAMECTIN 3,6% W/W")
    tc = _line(db, "ABAMECTIN 95% TC nguyên liệu 3.6")
    other = _line(db, "EMAMECTIN 3.6EC")
    db.commit()
    cond = SS.build_keyword_condition(db, "Abamectin 3.6 -TC")
    ids = {r.id for r in db.query(CustomsLine).filter(cond)}
    assert ids == {ec.id, gl.id, comma.id}
    assert tc.id not in ids and other.id not in ids


def test_keyword_condition_matches_tagged_ingredient_and_synonym(db):
    db.add(CustomsSearchSynonym(term="Kasu", synonyms="Kasugamycin"))
    db.commit()
    by_ingredient = _line(db, "Thuốc trừ bệnh SUPER 2SL", active_ingredient="KASUGAMYCIN")
    by_name = _line(db, "KASUGAMYCIN 3SL")
    db.commit()
    ids = {r.id for r in db.query(CustomsLine).filter(SS.build_keyword_condition(db, "kasu"))}
    assert ids == {by_ingredient.id, by_name.id}
    assert SS.build_keyword_condition(db, "") is None


def test_explain_query_lists_what_each_term_will_match(db):
    out = SS.explain_query(db, 'Abamectin "3,6%" -TC')
    assert out["include"][1]["matches"] == ["3,6%", "3.6", "3,6", "36G/L", "36 G/L"]
    assert out["exclude"] == [{"term": "TC", "matches": ["TC"]}]


def test_synonym_schema_normalizes_separator_and_dedupes():
    s = SearchSynonymCreate(term="Abamectin", synonyms="Aba;  aba ;Abamectine\nABA")
    assert s.synonyms == "Aba; Abamectine"


# ── Cắm vào bộ lọc chung của trang tra cứu (sau bao-CR-493) ─────────────────────────────────

def test_page_filter_uses_and_not_search_and_kind_filter(db):
    from app.modules.customs import service as S
    _line(db, "Abamectin 3.6EC thuốc trừ sâu", product_kind=int(ProductKind.FINISHED))
    _line(db, "ABAMECTIN 36 G/L EC", product_kind=int(ProductKind.FINISHED))
    _line(db, "Abamectin 95% TC nguyên liệu", product_kind=int(ProductKind.TECHNICAL))
    _line(db, "Emamectin 3.6EC", product_kind=int(ProductKind.FINISHED))
    db.commit()
    pg = (0, 50)
    total, items = S.list_lines(db, {"q": "abamectin 3.6 -TC"}, *pg)
    assert total == 2 and all("TC" not in i["product_name"] for i in items), \
        "nghiệm thu F02: Abamectin VÀ 3.6 (≡ 36 G/L), KHÔNG CÓ TC"
    total, _ = S.list_lines(db, {"q": "abamectin", "product_kind": ["2"]}, *pg)
    assert total == 1, "lọc Nguyên liệu"
    total, _ = S.list_lines(db, {"q": "", "product_kind": "1,2"}, *pg)
    assert total == 4
    total, _ = S.list_lines(db, {"q": "   "}, *pg)
    assert total == 4, "ô tìm toàn khoảng trắng = không lọc"
