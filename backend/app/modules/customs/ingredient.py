"""Gắn HOẠT CHẤT và HÀM LƯỢNG / DẠNG BÀO CHẾ cho dòng hàng — HQ4 (bao-CR-470).

Tên hàng trên tờ khai là chữ tự do (83% tên chỉ xuất hiện một lần), nên "mặt hàng"
theo nghĩa của thu mua — hoạt chất — phải SUY RA từ chữ. Ba nguồn, dùng lần lượt:

1. **Từ khóa hoạt chất** (`tab_customs_ingredient_alias`): `EMAMECTIN` → `EMAMECTIN
   BENZOATE`. Tên hàng chứa từ khóa nào thì mang hoạt chất đó (hỗn hợp thì nối bằng
   " + ", tối đa 3).
2. **Tên hoạt chất trong danh mục thuốc BVTV** (`tab_customs_pesticide.active_ingredient`,
   ~6.900 thuốc): tách `Bifenazate 277g/l + Etoxazole 166g/l` thành từng tên, bỏ hàm
   lượng, rồi khớp NGUYÊN TỪ (`SULFUR` không được khớp vào `SULFURIC ACID`). Bước này
   bù cho bộ từ khóa tay chỉ có 99 hoạt chất — thiếu nó thì chính ATRAZINE, mặt hàng
   mẫu của tính năng, chỉ nhận ra 65/92 dòng.
3. **Tên thương mại** (cùng danh mục): tên hàng chứa `BIPYRHONE` thì hoạt chất là hoạt
   chất đăng ký của thuốc đó. Chỉ dùng khi hai bước trên không ra gì, và CHỈ cho dòng mã HS
   nhóm 3808 (thuốc BVTV) hoặc chưa có mã HS — bao-CR-733: danh mục có thuốc tên đúng bằng
   từ thường (`POWER`, `ELIXIR`, `JASMINE`, `ABSOLUTE`, `GAULOIS`), dò trên hương liệu / tinh
   dầu (3301 / 3302) là gắn nhầm hoạt chất BVTV cho hàng không phải thuốc.

Đo trên 18.243 dòng thật (trước khi có bước 2): bước 1 ra 31%, bước 3 ra 24%, gộp 41%. Phần còn lại phần lớn
là hóa chất khử trùng / tẩy rửa — không có hoạt chất BVTV để nối, không phải bộ gắn
kém. Màn hình phải NÓI độ phủ này, đừng để người đọc tưởng lọc theo hoạt chất là đủ.

Hàm lượng / dạng bào chế (`97%`, `80WP`, `20EC`, `250G/L`) tách được ~93% dòng — đây là
thứ tách thuốc kỹ thuật khỏi thành phẩm cùng hoạt chất (ATRAZINE 97% và 80WP giá lệch
nhau gấp đôi).
"""
import re
from collections import defaultdict

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .constants import ProductKind
from .model import CustomsIngredientAlias, CustomsKindKeyword, CustomsLine, CustomsPesticide

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


#  bao-CR-733: nhóm HS của thuốc BVTV (trừ sâu, trừ nấm, trừ cỏ, trừ chuột, điều hòa sinh trưởng…).
PESTICIDE_HS_PREFIX = "3808"


def allows_trade_names(hs_code: str | None) -> bool:
    """Dòng có được dò theo TÊN THƯƠNG MẠI thuốc BVTV không: mã HS nhóm 3808, hoặc chưa có mã HS (không đủ căn cứ để
    chặn). Bước theo tên hoạt chất không qua cổng này — thuốc kỹ thuật hay khai ở chương 29."""
    code = (hs_code or "").strip().lstrip("'")
    return not code or code.startswith(PESTICIDE_HS_PREFIX)


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

    def tag(self, product_name: str, hs_code: str | None = "") -> tuple[str, str]:
        """→ (hoạt chất, hàm lượng). `hs_code` rỗng = không biết mã HS (dò đủ ba bước như cũ)."""
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
        if not active and allows_trade_names(hs_code):
            #  bao-CR-728: duyệt từ theo THỨ TỰ trong tên hàng (bỏ trùng), không theo `set` — thứ tự của `set` chữ
            #  đổi theo từng tiến trình (băm ngẫu nhiên), nên tên chứa hai tên thương mại ra hoạt chất khác nhau giữa
            #  hai lần chạy: xuất rồi nạp lại tệp không sửa gì vẫn báo "Ghi đè" và đổi hoạt chất của dòng.
            for word in dict.fromkeys(_WORD.findall(up)):
                hit = next((a for k, a in self.trades.get(word, []) if k in up), None)
                if hit:
                    active = hit
                    break
        return active[:255], extract_formulation(product_name)


class KindTagger:
    """Nhãn THÀNH PHẨM / NGUYÊN LIỆU theo bộ từ khóa admin — bao-CR-494 (F04).

    Luật: khớp từ khóa loại THÀNH PHẨM → Thành phẩm (ngoại lệ thắng ngược); khớp từ khóa loại
    NGUYÊN LIỆU → Nguyên liệu; không khớp gì → Thành phẩm (mặc định của chị Mi). Từ khóa ngắn
    (≤ 4 ký tự ASCII) khớp NGUYÊN TỪ để `TC` không dính `ATC`/`ETC`; từ dài khớp chuỗi con.
    So sánh sau khi viết hoa cả hai phía nên "Kỹ Thuật" và "KỸ THUẬT" như nhau.
    """

    def __init__(self, keywords: list[tuple[str, int]]):
        self.finished: list[re.Pattern] = []
        self.technical: list[re.Pattern] = []
        for keyword, kind in keywords:
            kw = " ".join((keyword or "").upper().split())
            if not kw:
                continue
            escaped = re.escape(kw)
            pattern = (re.compile(rf"(?<![A-Z0-9]){escaped}(?![A-Z0-9])")
                       if kw.isascii() and kw.isalnum() and len(kw) <= 4 else re.compile(escaped))
            (self.finished if int(kind) == int(ProductKind.FINISHED) else self.technical).append(pattern)

    def tag(self, product_name: str) -> int:
        up = (product_name or "").upper()
        if any(p.search(up) for p in self.finished):
            return int(ProductKind.FINISHED)
        if any(p.search(up) for p in self.technical):
            return int(ProductKind.TECHNICAL)
        return int(ProductKind.FINISHED)


def load_kind_tagger(db: Session) -> KindTagger:
    rows = (db.query(CustomsKindKeyword.keyword, CustomsKindKeyword.kind)
            .filter(CustomsKindKeyword.is_active == True).all())  # noqa: E712
    return KindTagger([(k, kind) for k, kind in rows])


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
    kinds = load_kind_tagger(db)
    cache: dict[tuple[str, bool], tuple[str, str]] = {}
    tagged = total = technical = 0
    batch: list[dict] = []
    #  Đọc hết trước rồi mới ghi: đọc kiểu luồng (`yield_per`) giữ con trỏ mở trên cùng
    #  kết nối, MySQL không cho chạy câu UPDATE xen giữa.
    #  bao-CR-603: dòng có hoạt chất / hàm lượng LẤY TỪ TỆP (cờ `_from_file`) thì giữ nguyên giá
    #  trị đó — gắn lại chỉ đụng phần suy ra.
    for line_id, name, hs_code, stored_active, stored_form, active_from_file, form_from_file in db.query(
            CustomsLine.id, CustomsLine.product_name, CustomsLine.hs_code, CustomsLine.active_ingredient,
            CustomsLine.formulation, CustomsLine.active_ingredient_from_file, CustomsLine.formulation_from_file).all():
        key = (name, allows_trade_names(hs_code))
        if key not in cache:
            cache[key] = tagger.tag(name, hs_code)
        active, form = cache[key]
        if active_from_file:
            active = stored_active
        if form_from_file:
            form = stored_form
        kind = kinds.tag(name)
        total += 1
        tagged += bool(active)
        technical += kind == int(ProductKind.TECHNICAL)
        batch.append({"line_id": line_id, "active_ingredient": active, "formulation": form,
                      "product_kind": kind})
        if len(batch) >= _RETAG_CHUNK:
            _flush(db, batch)
    _flush(db, batch)
    db.commit()
    return {"total": total, "tagged": tagged, "technical": technical}


def _flush(db: Session, batch: list[dict]) -> None:
    from sqlalchemy import bindparam
    if batch:
        stmt = (update(CustomsLine).where(CustomsLine.id == bindparam("line_id"))
                .values(active_ingredient=bindparam("active_ingredient"),
                        formulation=bindparam("formulation"),
                        product_kind=bindparam("product_kind")))
        db.connection().execute(stmt, batch)
        batch.clear()


def retag_changed(db: Session, apply: bool = False, chunk: int = 5000, examples: int = 10) -> dict:
    """bao-CR-733 — gắn lại hoạt chất / hàm lượng / nhãn như `retag_all` nhưng ĐỌC THEO KHÚC (theo `id`) và CHỈ ghi
    dòng có giá trị khác; `apply=False` chỉ đếm. Chạy lại lần hai ra 0 dòng đổi (idempotent).

    Vì sao cần sau bao-CR-728: bộ gắn theo tên thương mại từng duyệt từ theo thứ tự `set` (đổi theo từng tiến trình),
    nên dòng đã lưu có tên hàng chứa từ hai tên thương mại trở lên mang hoạt chất ngẫu nhiên. Bản sửa chọn ổn định
    (tên đứng trước trong tên hàng thắng), nhưng dữ liệu cũ vẫn lệch: xuất rồi nạp lại tệp không sửa gì vẫn báo
    "Ghi đè" ở các dòng đó và đổi hoạt chất của chúng. Giá trị lấy từ tệp / sửa tay (cờ `_from_file`) giữ nguyên.

    Mỗi khúc commit riêng (gián đoạn giữa chừng thì chạy lại là tiếp phần còn lại). → số đếm + vài dòng mẫu.

    Sửa bộ dò (bao-CR-733): tên thương mại chỉ dò cho dòng mã HS 3808 (`allows_trade_names`), nên hàng ngoài nhóm đó đang
    mang hoạt chất suy ra từ tên thương mại (hương liệu GAULOIS ELIXIR → Brodifacoum) được ĐƯA VỀ RỖNG — đếm riêng ở
    `cleared`, theo mã HS 4 số ở `cleared_by_hs`. Không xóa thì nạp lại tệp xuất vẫn báo "Ghi đè" ở các dòng đó."""
    tagger = load_tagger(db)
    kinds = load_kind_tagger(db)
    cache: dict[tuple[str, bool], tuple[str, str, int]] = {}
    out = {"total": 0, "changed": 0, "active": 0, "formulation": 0, "kind": 0, "cleared": 0, "cleared_by_hs": {},
           "examples": [], "applied": apply}
    last_id = 0
    while True:
        rows = db.execute(
            select(CustomsLine.id, CustomsLine.product_name, CustomsLine.hs_code, CustomsLine.active_ingredient,
                   CustomsLine.formulation, CustomsLine.active_ingredient_from_file, CustomsLine.formulation_from_file,
                   CustomsLine.product_kind)
            .where(CustomsLine.id > last_id).order_by(CustomsLine.id).limit(chunk)).all()
        if not rows:
            return out
        batch: list[dict] = []
        for line_id, name, hs_code, active_now, form_now, active_from_file, form_from_file, kind_now in rows:
            key = (name, allows_trade_names(hs_code))
            if key not in cache:
                cache[key] = (*tagger.tag(name, hs_code), kinds.tag(name))
            active, form, kind = cache[key]
            active = active_now if active_from_file else active
            form = form_now if form_from_file else form
            diff = [active != (active_now or ""), form != (form_now or ""), kind != (kind_now or 0)]
            out["total"] += 1
            if not any(diff):
                continue
            out["changed"] += 1
            out["active"] += diff[0]
            out["formulation"] += diff[1]
            out["kind"] += diff[2]
            if active_now and not active:
                out["cleared"] += 1
                hs4 = (hs_code or "")[:4] or "?"
                out["cleared_by_hs"][hs4] = out["cleared_by_hs"].get(hs4, 0) + 1
            if len(out["examples"]) < examples:
                out["examples"].append({"id": line_id, "hs_code": hs_code, "product_name": name,
                                        "active_before": active_now,
                                        "active_after": active, "formulation_before": form_now,
                                        "formulation_after": form, "kind_before": kind_now, "kind_after": kind})
            batch.append({"line_id": line_id, "active_ingredient": active, "formulation": form,
                          "product_kind": kind})
        if apply and batch:
            _flush(db, batch)
            db.commit()
        last_id = rows[-1][0]
