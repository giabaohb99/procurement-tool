"""Tìm tên hàng bằng từ khóa CÓ / KHÔNG CÓ + quy đổi nồng độ + từ đồng nghĩa — bao-CR-495.

Yêu cầu F02 của chị Mi (22/09 + ghi chú 25/09/2026): ô tìm «Tên hàng» phải
  · kết hợp nhiều từ khóa bắt buộc có (AND) và loại trừ từ khóa (NOT), không phân biệt hoa/thường;
  · nhận diện các cách viết nồng độ tương đương: `3,6%` ≡ `3.6%` ≡ `3.6EC` ≡ `36 G/L` ≡ `3.6% W/W`
    (phần trăm và g/l hơn kém nhau 10 lần — luật mặc định, ngoại lệ chị Mi bổ sung sau);
  · từ đồng nghĩa người dùng tự khai (`tab_customs_search_synonym`), cộng bộ từ khóa → hoạt
    chất có sẵn (`tab_customs_ingredient_alias`): gõ từ nào trong nhóm cũng ra cả nhóm.

Cú pháp ô tìm: các từ cách nhau bằng khoảng trắng đều là BẮT BUỘC CÓ; `-từ`, `!từ` hay
`NOT từ` = KHÔNG CÓ; `"cụm nhiều chữ"` giữ nguyên cụm; chữ `AND` bị bỏ qua. Ví dụ nghiệm thu:
`Abamectin 3.6 -TC` → dòng có ABAMECTIN và 3.6 (hoặc 3,6 / 36 G/L) nhưng không có TC.

Hàm `build_keyword_condition` trả một biểu thức SQLAlchemy để `apply_line_filters` cắm vào
truy vấn — cố ý tách khỏi `service.py` (bao-CR-493 đang sửa tệp đó).
"""
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import Session

from .model import CustomsIngredientAlias, CustomsLine, CustomsSearchSynonym

_TOKEN = re.compile(r'"([^"]*)"|(\S+)')
_NOT_PREFIX = ("-", "!")
_CONCENTRATION = re.compile(
    r"^(\d+(?:[.,]\d+)?)\s*(%|G/L|GL|EC|SC|SL|WP|WG|WDG|OD|CS|EW|ME|FS|DP|SP|GR|TC|TECH)?"
    r"(?:\s*W/[WV])?$", re.IGNORECASE)
_MAX_TERMS = 10


@dataclass
class ParsedQuery:
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not self.include and not self.exclude


def parse_query(raw: str) -> ParsedQuery:
    """Tách chuỗi gõ thành từ CÓ / KHÔNG CÓ. Trần 10 từ mỗi phía — ô tìm không phải chỗ dán cả
    danh sách, và mỗi từ là một cụm LIKE trên bảng vài chục nghìn dòng."""
    out = ParsedQuery()
    pending_not = False
    for quoted, bare in _TOKEN.findall(raw or ""):
        token = quoted if quoted else bare
        negate = pending_not
        pending_not = False
        if not quoted:
            if token.upper() == "AND":
                continue
            if token.upper() == "NOT":
                pending_not = True
                continue
            if token[:1] in _NOT_PREFIX:
                negate, token = True, token[1:]
        token = token.strip()
        if not token:
            continue
        bucket = out.exclude if negate else out.include
        if len(bucket) < _MAX_TERMS and token.casefold() not in {t.casefold() for t in bucket}:
            bucket.append(token)
    return out


def _fmt(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text if "." in text else text   # normalize() bỏ số 0 thừa: 3.60 → 3.6, 36.0 → 36


def concentration_variants(term: str) -> list[str]:
    """`3,6%` / `3.6EC` / `36 G/L` → các cách viết tương đương của CÙNG nồng độ.

    Trả rỗng khi từ không phải nồng độ. Số phần trăm và số g/l lệch nhau 10 lần (luật mặc định
    của chị Mi). Cách viết trả về: số thập phân bằng chấm và phẩy (bắt `3.6%`, `3.6EC`, `3,6 SL`…),
    dạng g/l có và không có khoảng trắng.
    """
    m = _CONCENTRATION.match((term or "").strip())
    if not m:
        return []
    try:
        number = Decimal(m.group(1).replace(",", "."))
    except InvalidOperation:
        return []
    unit = (m.group(2) or "").upper()
    percent = number / 10 if unit in ("G/L", "GL") else number
    grams = percent * 10
    p, g = _fmt(percent), _fmt(grams)
    variants = [p, p.replace(".", ","), f"{g}G/L", f"{g} G/L"]
    if "." in g:
        variants += [f"{g.replace('.', ',')}G/L", f"{g.replace('.', ',')} G/L"]
    seen: list[str] = []
    for v in variants:
        if v.casefold() not in {s.casefold() for s in seen}:
            seen.append(v)
    return seen


def load_synonym_groups(db: Session) -> list[list[str]]:
    """Mỗi nhóm = từ gốc + các từ đồng nghĩa (bảng người dùng) hoặc từ khóa + hoạt chất chuẩn
    (bảng hoạt chất có sẵn). Từ gốc trùng nhau giữa hai bảng thì giữ cả hai nhóm."""
    groups: list[list[str]] = []
    for row in db.query(CustomsSearchSynonym).filter(CustomsSearchSynonym.is_active == True):  # noqa: E712
        words = [row.term] + [w.strip() for w in (row.synonyms or "").split(";") if w.strip()]
        if len(words) > 1:
            groups.append(words)
    for a in db.query(CustomsIngredientAlias):
        if a.keyword and a.canonical and a.keyword.casefold() != a.canonical.casefold():
            groups.append([a.keyword, a.canonical])
    return groups


def expand_term(term: str, groups: list[list[str]]) -> list[str]:
    """Một từ → bản thân nó + đồng nghĩa + các cách viết nồng độ tương đương (khử trùng, giữ thứ tự)."""
    out: list[str] = [term]
    key = term.casefold()
    for group in groups:
        if any(w.casefold() == key for w in group):
            out += group
    out += concentration_variants(term)
    seen: list[str] = []
    for v in out:
        v = v.strip()
        if v and v.casefold() not in {s.casefold() for s in seen}:
            seen.append(v)
    return seen


def _like_any(variants: list[str], include_ingredient: bool):
    conds = []
    for v in variants:
        like = f"%{v}%"
        conds.append(CustomsLine.product_name.ilike(like))
        if include_ingredient:
            conds.append(CustomsLine.active_ingredient.ilike(like))
    return or_(*conds)


def build_keyword_condition(db: Session, raw: str):
    """Biểu thức lọc cho ô tìm tên hàng; `None` khi ô trống.

    Từ CÓ khớp tên hàng HOẶC hoạt chất đã gắn (giữ hành vi cũ của `apply_line_filters`); từ KHÔNG
    CÓ chỉ soi tên hàng — loại trừ theo hoạt chất suy ra thì người dùng không đoán được.
    """
    parsed = parse_query(raw)
    if parsed.empty:
        return None
    groups = load_synonym_groups(db) if parsed.include or parsed.exclude else []
    conds = [_like_any(expand_term(t, groups), include_ingredient=True) for t in parsed.include]
    conds += [not_(_like_any(expand_term(t, groups), include_ingredient=False)) for t in parsed.exclude]
    return and_(*conds)


def explain_query(db: Session, raw: str) -> dict:
    """Cho giao diện bày «đang tìm gì»: từng từ và các cách viết nó sẽ khớp."""
    parsed = parse_query(raw)
    groups = load_synonym_groups(db) if not parsed.empty else []
    return {
        "include": [{"term": t, "matches": expand_term(t, groups)} for t in parsed.include],
        "exclude": [{"term": t, "matches": expand_term(t, groups)} for t in parsed.exclude],
    }
