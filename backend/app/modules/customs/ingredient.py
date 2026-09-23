"""Gắn HOẠT CHẤT và HÀM LƯỢNG / DẠNG BÀO CHẾ cho dòng hàng — HQ4 (bao-CR-470).

Tên hàng trên tờ khai là chữ tự do (83% tên chỉ xuất hiện một lần), nên "mặt hàng"
theo nghĩa của thu mua — hoạt chất — phải SUY RA từ chữ. Ba nguồn, dùng lần lượt:

1. **Từ khóa hoạt chất** (`tab_customs_ingredient_alias`): `EMAMECTIN` → `EMAMECTIN
   BENZOATE`. Tên hàng chứa từ khóa nào thì mang hoạt chất đó (hỗn hợp thì nối bằng
   " + ", tối đa 3).
2. **Tên hoạt chất trong danh mục thuốc BVTV** (`tab_customs_pesticide.active_ingredient`,
   ~6.900 thuốc): tách `Bifenazate 277g/l + Etoxazole 166g/l` thành từng tên, bỏ hàm
   lượng, rồi khớp NGUYÊN TỪ (`SULFUR` không được khớp vào `SULFURIC ACID`). Bước này
   bù cho bộ từ khóa tay chỉ có 100 hoạt chất — thiếu nó thì chính ATRAZINE, mặt hàng
   mẫu của tính năng, chỉ nhận ra 65/92 dòng.
3. **Tên thương mại** (cùng danh mục): tên hàng chứa `BIPYRHONE` thì hoạt chất là hoạt
   chất đăng ký của thuốc đó. Chỉ dùng khi hai bước trên không ra gì.

Đo trên 18.243 dòng thật (trước khi có bước 2): bước 1 ra 31%, bước 3 ra 24%, gộp 41%. Phần còn lại phần lớn
là hóa chất khử trùng / tẩy rửa — không có hoạt chất BVTV để nối, không phải bộ gắn
kém. Màn hình phải NÓI độ phủ này, đừng để người đọc tưởng lọc theo hoạt chất là đủ.

Hàm lượng / dạng bào chế (`97%`, `80WP`, `20EC`, `250G/L`) tách được ~93% dòng — đây là
thứ tách thuốc kỹ thuật khỏi thành phẩm cùng hoạt chất (ATRAZINE 97% và 80WP giá lệch
nhau gấp đôi).
"""
import re
from collections import defaultdict

from sqlalchemy import update
from sqlalchemy.orm import Session

from .model import CustomsIngredientAlias, CustomsLine, CustomsPesticide

_FORMULATION = re.compile(
    r"(\d+(?:[.,]\d+)?\s?%"
    r"|\d+(?:[.,]\d+)?\s?(?:EC|SC|WP|WG|WDG|SL|GR|SP|OD|CS|EW|ME|FS|DP|TC|TECH)\b"
    r"|\d+(?:[.,]\d+)?\s?G/L)", re.IGNORECASE)
_WORD = re.compile(r"[A-Z0-9\-]+")
_MAX_ACTIVES = 3
_RETAG_CHUNK = 2000

#  Tách tên hoạt chất trong danh mục BVTV: bỏ phần trong ngoặc (`(min 98%)`), hàm lượng
#  (`277g/l`, `10%`, `2.5 %w/w`) và tiền tố `chất an toàn`.
_PAREN = re.compile(r"\([^)]*\)")
_AMOUNT = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%\s*(?:W/W|W/V)?|G/L|G/KG|MG/L|ML/L|CFU/\S+|IU/\S+|BT\S*|SPORES?/\S+)?", re.IGNORECASE)
_NON_WORD = re.compile(r"[^A-Z0-9 ]+")
_MIN_DERIVED_LEN = 6
#  Từ đầu của tên muối / chủng vi sinh / chất chung chung — không được đứng một mình
#  làm từ khóa (`POTASSIUM` khớp mọi loại phân kali).
_GENERIC_HEADS = frozenset({
    "POTASSIUM", "SODIUM", "CALCIUM", "COPPER", "MAGNESIUM", "AMMONIUM", "ZINC", "SULFUR",
    "MINERAL", "PETROLEUM", "PARAFFIN", "BACILLUS", "EXTRACT", "OIL", "ACID", "CHAT", "PROTEIN",
    "STREPTOMYCES", "TRICHODERMA", "BEAUVERIA", "METARHIZIUM", "PSEUDOMONAS", "VIRUS",
    "ACRYLIC", "CITRIC", "ACETIC", "BORIC", "SULFURIC", "HYDROGEN", "QUATERNARY", "ETHYL",
    "METHYL", "ALCOHOL", "SILICON", "SILICA", "PHOSPHORIC", "CHITOSAN", "SEAWEED", "HUMIC",
    "ALUMINIUM", "ALUMINUM", "NATURAL", "DIETHYL", "DIMETHYL", "SHANDONG", "JIANGSU", "ZHEJIANG",
    "VERTICILLIUM", "PAECILOMYCES", "NUCLEAR",
})
#  Cột hoạt chất của danh mục nguồn đôi chỗ chép nhầm TÊN CÔNG TY (`SHANDONG JOPHNE
#  BIOTECHNOLOGY CO LTD`) — tên nào mang dấu hiệu doanh nghiệp thì bỏ.
_COMPANY_MARK = re.compile(r"\b(?:CO|LTD|LIMITED|COMPANY|CORP|CORPORATION|INC|GROUP|BIOTECH\w*|INDUSTR\w*)\b")


def normalize_for_match(text: str) -> str:
    """Viết hoa, gạch nối và dấu câu thành khoảng trắng, gom khoảng trắng — để
    `CYHALOFOP-BUTYL` khớp `Cyhalofop butyl`."""
    return " " + " ".join(_NON_WORD.sub(" ", (text or "").upper()).split()) + " "


def derive_aliases(active_ingredients: list[str]) -> list[tuple[str, str]]:
    """Danh mục BVTV → cặp (từ khóa đã chuẩn hóa, hoạt chất). Thêm cả TỪ ĐẦU của tên
    nhiều chữ (`KANAMYCIN` → `KANAMYCIN SULFATE`) khi từ đó đủ dài và không chung chung."""
    names: dict[str, int] = defaultdict(int)
    for raw in active_ingredients:
        for part in (raw or "").split("+"):
            part = _AMOUNT.sub(" ", _PAREN.sub(" ", part))
            part = re.sub(r"(?i)^\s*ch[aấ]t an to[aà]n\s*", "", part).strip()
            #  Tên tiếng Việt (`Dầu tỏi`, `Dầu hạt bông`) bỏ qua: tờ khai hầu như không ghi
            #  hoạt chất bằng tiếng Việt, và chữ có dấu chỉ sinh từ khóa rác.
            if not part.isascii():
                continue
            name = normalize_for_match(part).strip()
            if _COMPANY_MARK.search(name):
                continue
            if len(name) >= _MIN_DERIVED_LEN and any(ch.isalpha() for ch in name):
                names[name] += 1
    out = {name: name for name in names}
    heads: dict[str, list[str]] = defaultdict(list)
    for name in names:
        head = name.split()[0]
        if head != name and len(head) >= 7 and head not in _GENERIC_HEADS:
            heads[head].append(name)
    for head, full in heads.items():
        if head not in out:
            out[head] = max(full, key=lambda n: names[n])   # tên hay gặp nhất
    return list(out.items())


def extract_formulation(product_name: str) -> str:
    m = _FORMULATION.search(product_name or "")
    return re.sub(r"\s+", "", m.group(1)).replace(",", ".").upper()[:40] if m else ""


class IngredientTagger:
    """Nạp danh mục một lần rồi gắn cho cả lô — không truy vấn theo từng dòng."""

    def __init__(self, aliases: list[tuple[str, str]], trades: list[tuple[str, str]],
                 derived: list[tuple[str, str]] | None = None):
        self.aliases = sorted(((k.upper(), c) for k, c in aliases if k), key=lambda x: -len(x[0]))
        #  Từ khóa suy ra từ danh mục BVTV khớp NGUYÊN TỪ trên chuỗi đã chuẩn hóa (có
        #  khoảng trắng hai đầu) — tên dài xét trước để `CYHALOFOP BUTYL` thắng `CYHALOFOP`.
        self.derived = sorted(((f" {k} ", c) for k, c in (derived or []) if k), key=lambda x: -len(x[0]))
        #  Đánh chỉ mục tên thương mại theo TỪ ĐẦU TIÊN: dò ~6.900 tên cho mỗi dòng là
        #  quá chậm; đa số tên hàng chỉ có vài chục từ để tra.
        self.trades: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for key, active in sorted(trades, key=lambda x: -len(x[0])):
            if key:
                self.trades[key.split()[0]].append((key, active))

    def tag(self, product_name: str) -> tuple[str, str]:
        up = (product_name or "").upper()
        found: list[str] = []
        for keyword, canonical in self.aliases:
            if keyword in up and canonical not in found:
                found.append(canonical)
                if len(found) == _MAX_ACTIVES:
                    break
        if not found and self.derived:
            norm = normalize_for_match(up)
            for keyword, canonical in self.derived:
                if keyword in norm and canonical not in found                         and not any(canonical in f or f in canonical for f in found):
                    found.append(canonical)
                    if len(found) == _MAX_ACTIVES:
                        break
        active = " + ".join(found)
        if not active:
            for word in set(_WORD.findall(up)):
                hit = next((a for k, a in self.trades.get(word, []) if k in up), None)
                if hit:
                    active = hit
                    break
        return active[:255], extract_formulation(product_name)


def load_tagger(db: Session) -> IngredientTagger:
    aliases = [(a.keyword, a.canonical) for a in db.query(CustomsIngredientAlias)]
    pesticides = db.query(CustomsPesticide.trade_key, CustomsPesticide.active_ingredient).all()
    trades = [(p.trade_key, p.active_ingredient) for p in pesticides]
    derived = derive_aliases([p.active_ingredient for p in pesticides])
    return IngredientTagger(aliases, trades, derived)


def retag_all(db: Session) -> dict:
    """Gắn lại MỌI dòng — chạy sau khi danh mục hoạt chất / thuốc BVTV đổi.

    Cập nhật theo KHÓA CHÍNH, không theo tên hàng: cột tên hàng không có chỉ mục, và
    tên gần như không trùng nhau nên gom theo tên cũng chẳng bớt được bao nhiêu câu.
    """
    tagger = load_tagger(db)
    cache: dict[str, tuple[str, str]] = {}
    tagged = total = 0
    batch: list[dict] = []
    #  Đọc hết trước rồi mới ghi: đọc kiểu luồng (`yield_per`) giữ con trỏ mở trên cùng
    #  kết nối, MySQL không cho chạy câu UPDATE xen giữa.
    for line_id, name in db.query(CustomsLine.id, CustomsLine.product_name).all():
        if name not in cache:
            cache[name] = tagger.tag(name)
        active, form = cache[name]
        total += 1
        tagged += bool(active)
        batch.append({"line_id": line_id, "active_ingredient": active, "formulation": form})
        if len(batch) >= _RETAG_CHUNK:
            _flush(db, batch)
    _flush(db, batch)
    db.commit()
    return {"total": total, "tagged": tagged}


def _flush(db: Session, batch: list[dict]) -> None:
    from sqlalchemy import bindparam
    if batch:
        stmt = (update(CustomsLine).where(CustomsLine.id == bindparam("line_id"))
                .values(active_ingredient=bindparam("active_ingredient"),
                        formulation=bindparam("formulation")))
        db.connection().execute(stmt, batch)
        batch.clear()
