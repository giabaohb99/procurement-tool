"""Đối chiếu HAI CHIỀU giữa danh mục thuốc BVTV và danh sách hoạt chất CẤM (TT 75/2025) — 29/09/2026.

  · Mục «Thuốc BVTV»: thuốc nào có hoạt chất nằm trong danh sách cấm thì gắn cờ, lọc riêng được.
  · Mục «Pháp lý»: mỗi hoạt chất cấm đếm được bao nhiêu thuốc trong danh mục đang chứa nó.

Đo trên bản cào 28/09 thì nguồn đã BỎ HẲN thuốc chứa hoạt chất cấm (kể cả thuốc hết hiệu lực) —
nên kết quả bình thường là 0. Đây là bước KIỂM CHÉO: danh mục có lọt thuốc cấm thì màn hình báo.

⚠️ Khớp NGUYÊN TÊN hoạt chất, KHÔNG khớp chuỗi con / từ đầu như `ingredient.IngredientTagger`.
Danh mục có 10 thuốc chứa Chlorpyrifos **methyl** (không cấm) trong khi thứ bị cấm là Chlorpyrifos
**ethyl** — khớp theo từ đầu là gắn cờ «cấm» oan cho cả 10. Nới duy nhất: tên thuốc dài hơn tên cấm
ĐÚNG bằng một đuôi muối / dạng chế phẩm (`Paraquat dichloride`, `Glyphosate isopropylamine salt`)
— đó vẫn là chính hoạt chất ấy. `METHYL` / `ETHYL` cố ý KHÔNG nằm trong bộ đuôi đó.

Hai bảng không có khóa chung (danh mục thuốc không có số CAS), nên chỉ khớp được bằng tên — kết quả
là THAM KHẢO, không phải căn cứ pháp lý; màn hình phải nói điều đó.
"""
import re
import unicodedata
from collections import defaultdict

from sqlalchemy.orm import Session

from .constants import RegulationList
from .ingredient import normalize_for_match
from .model import CustomsPesticide, CustomsRegulation

_PAREN = re.compile(r"\(([^)]*)\)")
#  Hàm lượng CÓ đơn vị (`277g/l`, `10%`, `2.5 %w/w`, `276 g/ l`, `50G`) và dạng chế phẩm dính số
#  (`20 SL`, `800EC`, `3GR`). Đơn vị bắt buộc — khác `ingredient._AMOUNT`: số trần mà cũng bỏ thì
#  «2,4-D» mất «2,4» còn trơ «D».
_AMOUNT = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:%\s*(?:W\s*/\s*W|W\s*/\s*V)?"
    r"|(?:MG|ML|G|KG|L)\s*/\s*(?:KG|L|HA)\b"
    r"|(?:CFU|IU|SPORES?|PIB|OB)\s*/\s*\S+"
    r"|(?:EC|SC|WP|WG|WDG|SL|GR|SP|OD|CS|EW|ME|FS|DP|TC|SE|DF|ZC|GB|RB|AB|BR|DS|SG|TB|KG|G|L)\b)",
    re.IGNORECASE)
#  Ký tự mà bản cào / văn bản pháp lý hay lẫn vào: khoảng trắng không ngắt, gạch mềm, gạch dài,
#  α/β của font Symbol (vùng dùng riêng U+F061/F062). Không đổi thì cả tên rơi ở bước «chỉ ASCII».
_CHAR_MAP = str.maketrans({"\xa0": " ", "\xad": "-", "‐": "-", "‑": "-", "‒": "-",
                           "–": "-", "—": "-", "’": "'", "\uf061": "alpha",
                           "\uf062": "beta", "α": "alpha", "β": "beta", "ß": "beta"})
_SAFENER = re.compile(r"(?i)^\s*ch[aấ]t an to[aà]n\s*")
#  Tên cấm có nhiều cách gọi: «BHC, Lindane». Chỉ tách ở phẩy CÓ khoảng trắng — «2,4-D» giữ nguyên.
_ALTERNATES = re.compile(r";|,\s+|\s+/\s+")
_SALT_WORDS = frozenset({
    "DICHLORIDE", "CHLORIDE", "HYDROCHLORIDE", "BROMIDE", "SULFATE", "SULPHATE", "SALT", "SALTS",
    "SODIUM", "POTASSIUM", "AMMONIUM", "ISOPROPYLAMINE", "IPA", "DIMETHYLAMINE", "DMA", "AMINE",
    "TRIMESIUM", "ACID", "ESTER", "TECHNICAL", "TECH",
})
_MIN_KEY_LEN = 3


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", (text or "").translate(_CHAR_MAP))


def _clean(name: str) -> str:
    """Một tên → chuỗi so khớp: viết hoa, dấu câu thành khoảng trắng. Tên có dấu tiếng Việt bỏ
    (`Dầu tỏi`) — chuẩn hóa ASCII sẽ biến nó thành rác trùng bừa."""
    name = _fold(name)
    if not name.isascii():
        return ""
    key = normalize_for_match(name).strip()
    return key if len(key) >= _MIN_KEY_LEN and any(ch.isalpha() for ch in key) else ""


def split_active_ingredients(active_ingredient: str) -> list[str]:
    """`Chlorpyrifos Methyl (min 96%) + Pymetrozine 120g/kg` → [`CHLORPYRIFOS METHYL`, `PYMETROZINE`]."""
    out: list[str] = []
    #  Bỏ ngoặc TRƯỚC rồi mới tách: `Emamectin benzoate (Avermectin B1a 90 % + B1b 10%)` tách trước
    #  thì ngoặc bị cắt đôi, nửa còn lại dính vào tên (123 dòng của bản cào 28/09).
    for part in re.split(r"[+;]", _PAREN.sub(" ", _fold(active_ingredient))):
        part = _SAFENER.sub("", _AMOUNT.sub(" ", part))
        key = _clean(part)
        if key and key not in out:
            out.append(key)
    return out


def regulation_keys(name: str) -> list[str]:
    """Mọi cách gọi của một hoạt chất cấm: tên chính, từng tên sau dấu phẩy, tên trong ngoặc."""
    name = _fold(name)
    raw = [_PAREN.sub(" ", name)] + _PAREN.findall(name)
    out: list[str] = []
    for chunk in raw:
        for alt in [chunk, *_ALTERNATES.split(chunk)]:
            key = _clean(alt)
            if key and key not in out:
                out.append(key)
    return out


class BannedIngredientMatcher:
    """Nạp danh sách cấm MỘT lần cho cả yêu cầu, rồi khớp bao nhiêu thuốc cũng được."""

    def __init__(self, regulations: list[CustomsRegulation]):
        self.by_key: dict[str, list[CustomsRegulation]] = defaultdict(list)
        for reg in regulations:
            for key in regulation_keys(reg.name):
                if reg not in self.by_key[key]:
                    self.by_key[key].append(reg)

    def _lookup(self, ingredient: str) -> list[CustomsRegulation]:
        """Khớp nguyên tên, rồi bóc dần đuôi muối từ phải sang (`GLYPHOSATE ISOPROPYLAMINE SALT` →
        `GLYPHOSATE`) và gom MỌI tầng trúng — không dừng ở tầng đầu: danh sách có cả «Paraquat» lẫn
        «Paraquat dichloride» thì thuốc Paraquat dichloride phải đếm cho CẢ HAI, bất kể bộ khớp
        được dựng từ những dòng nào (review 29/09: dừng sớm làm số đếm lệch danh sách nó mở ra)."""
        hits = list(self.by_key.get(ingredient, []))
        words = ingredient.split()
        while len(words) > 1 and words[-1] in _SALT_WORDS:
            words.pop()
            hits.extend(r for r in self.by_key.get(" ".join(words), []) if r not in hits)
        return hits

    def match(self, active_ingredient: str) -> list[CustomsRegulation]:
        found: list[CustomsRegulation] = []
        if not self.by_key:
            return found
        for ingredient in split_active_ingredients(active_ingredient):
            for reg in self._lookup(ingredient):
                if reg not in found:
                    found.append(reg)
        return found


def load_matcher(db: Session) -> BannedIngredientMatcher:
    rows = (db.query(CustomsRegulation)
            .filter(CustomsRegulation.is_active.is_(True),
                    CustomsRegulation.list_code == int(RegulationList.BANNED_TT75))
            .all())
    return BannedIngredientMatcher(rows)


def build_index(db: Session, matcher: BannedIngredientMatcher | None = None) -> dict[int, set[int]]:
    """id hoạt chất cấm → tập id thuốc chứa nó, quét CẢ danh mục (~7 nghìn dòng, hai cột, vài chục ms).

    Không lưu thành cột: danh sách cấm sửa được trên màn «Cấu hình», lưu sẵn là lệch ngay khi có
    người sửa một dòng mà không ai nhớ chạy lại.
    """
    matcher = matcher or load_matcher(db)
    index: dict[int, set[int]] = defaultdict(set)
    if not matcher.by_key:
        return index
    for pid, active in db.query(CustomsPesticide.id, CustomsPesticide.active_ingredient):
        for reg in matcher.match(active):
            index[reg.id].add(pid)
    return index


def banned_out(reg: CustomsRegulation) -> dict:
    return {"id": reg.id, "name": reg.name, "cas_no": reg.cas_no, "banned_year": reg.banned_year,
            "legal_basis": reg.legal_basis}
