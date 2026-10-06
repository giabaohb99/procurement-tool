"""duoc-CR-598 mục 3 — nạp danh mục hóa chất NĐ 24/2026/NĐ-CP phụ lục I–IV từ tệp Excel của phòng
Thu mua (`03. KHAI BÁO HOÁ CHẤT.xlsx`, sheet «PHỤ LỤC NGHỊ ĐỊNH», đại ca gửi 06/10/2026).

Hai bước, tách để kiểm được từng bước:
  1. `parse_sheet(rows)` — dòng Excel → danh sách dict (hàm thuần). Bản đã đọc lưu thành JSON trong
     repo (`data/nd24_2026_regulations.json`) để prod nạp được mà không cần chép tệp Excel lên máy.
  2. `apply_rows(db, items)` — CẬP NHẬT dòng đã có, THÊM dòng mới, NGỪNG DÙNG (không xóa) dòng phụ lục
     I–IV không còn trong tệp. TT 75/2025 và TT 01/2026 không đụng tới.

Bẫy của tệp nguồn (đọc tay 06/10/2026):
  - Phụ lục xác định theo dòng tiêu đề «PHỤ LỤC …», KHÔNG theo cột F («Phụ lục I»…): cột đó thiếu ở
    ~45 dòng có số thứ tự đàng hoàng.
  - Cuối phụ lục IV là «Bảng B» — NHÓM nguy hại (độc cấp tính, chất nổ…) chứ không phải hóa chất,
    cột lệch hẳn: bỏ.
  - Excel tự «sửa» số CAS: `0107-02-08` (đúng: 107-02-8), ô thành NGÀY (7719-09-7 → 2026-…),
    `#VALUE!`, `---`. `normalize_cas` gỡ lại, kiểm số cuối (check digit) trước khi tin.
  - Một hóa chất nhiều số CAS: các số sau nằm ở dòng kế tiếp, chỉ có cột CAS → ghi vào ghi chú.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Iterable

from sqlalchemy.orm import Session

from .constants import RegulationList
from .model import CustomsRegulation

SHEET_NAME = "PHỤ LỤC NGHỊ ĐỊNH"
LEGAL_BASIS = "NĐ 24/2026/NĐ-CP"
APPENDIX_CODES = {
    "I": int(RegulationList.ND24_PL1),
    "II": int(RegulationList.ND24_PL2),
    "III": int(RegulationList.ND24_PL3),
    "IV": int(RegulationList.ND24_PL4),
}
_ROMAN = {code: roman for roman, code in APPENDIX_CODES.items()}
_STT_RE = re.compile(r"^\d+\.?$")
_CAS_RE = re.compile(r"^(\d{1,7})-(\d{1,2})-(\d{1,2})$")
_BANG_B_RE = re.compile(r"^\d+\.\s*Bảng\s*B", re.IGNORECASE)


def _text(value: Any) -> str:
    """Ô → chuỗi gọn; gạch ngang thay chỗ trống («---») coi như rỗng."""
    if value is None:
        return ""
    s = " ".join(str(value).split())
    return "" if not s.strip("-") else s


def _cas_check_ok(cas: str) -> bool:
    digits = cas.replace("-", "")
    body, check = digits[:-1], int(digits[-1])
    return sum(int(d) * w for w, d in enumerate(reversed(body), start=1)) % 10 == check


def normalize_cas(value: Any) -> str:
    """Số CAS chuẩn `NNNNNNN-NN-N`, gỡ các kiểu Excel làm hỏng; không đọc ra được thì trả rỗng.

    Chuỗi đúng dạng mà sai số kiểm thì GIỮ nguyên văn (có thể nguồn gõ nhầm — giấu đi còn tệ hơn).
    """
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):          # 7719-09-7 bị Excel đọc thành ngày
        value = f"{value.year}-{value.month:02d}-{value.day}"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        digits = str(int(value))
        if len(digits) < 5:
            return ""
        value = f"{digits[:-3]}-{digits[-3:-1]}-{digits[-1]}"
    s = str(value).strip().split(" ")[0]           # «7719-09-07 00:00:00»
    if not s or s.startswith("#") or not s.strip("-"):
        return ""
    m = _CAS_RE.match(s)
    if not m:
        return s[:40]
    cas = f"{int(m.group(1))}-{int(m.group(2)):02d}-{int(m.group(3))}"
    if int(m.group(3)) > 9:
        return s[:40]
    return cas if _cas_check_ok(cas) else s[:40]


def split_cas(value: Any) -> list[str]:
    """Một ô có thể chứa NHIỀU số CAS (xuống dòng / chấm phẩy / dấu phẩy) → danh sách đã chuẩn hóa."""
    if isinstance(value, str) and re.search(r"[\n;,]", value):
        parts = [normalize_cas(p) for p in re.split(r"[\n;,]+", value)]
    else:
        parts = [normalize_cas(value)]
    return [p for p in parts if p]


def _threshold(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(" ", "")
    return float(s) if re.fullmatch(r"\d+(\.\d+)?", s) else None


def _heading(a: str, b: str, c: str) -> str:
    """Dòng tiêu đề nhóm trong phụ lục → nhãn phân loại («A. CÁC TIỀN CHẤT CÔNG NGHIỆP»)."""
    tail = c or b
    if not tail:
        return a[:100]
    sep = " " if a.endswith(".") else ". "
    return f"{a}{sep}{tail}"[:100]


_GROUP_RE = re.compile(r"Nhóm\s*([12])(?!\d)")
#  Ngưỡng HÀM LƯỢNG trong hỗn hợp (% khối lượng) — câu ghi chú của chính NĐ 24/2026 (không có trong tệp
#  Excel, đối chiếu ngày 06/10/2026 với văn bản trên vanban.chinhphu.vn, luatvietnam, TVPL):
#    PL II : hỗn hợp chứa ≥ 1 chất của danh mục với hàm lượng > 5%.
#    PL III: nhóm 1 > 1%; nhóm 2 — tiền chất công nghiệp (mục A) > 5%, hóa chất công ước (B, C) > 1%.
#    PL I không có ngưỡng; PL IV dùng ngưỡng TỒN TRỮ kg (cột G), không dùng ngưỡng hỗn hợp.
MIXTURE_PCT_PL2 = 5.0
MIXTURE_PCT_STRICT = 1.0
MIXTURE_PCT_PRECURSOR_GROUP2 = 5.0


def _mixture_pct(list_code: int, group: int, section: str) -> float | None:
    if list_code == APPENDIX_CODES["II"]:
        return MIXTURE_PCT_PL2
    if list_code == APPENDIX_CODES["III"]:
        if group == 1:
            return MIXTURE_PCT_STRICT
        if group == 2:
            return MIXTURE_PCT_PRECURSOR_GROUP2 if section == "A" else MIXTURE_PCT_STRICT
    return None


def parse_sheet(rows: Iterable[tuple]) -> list[dict]:
    """Dòng sheet «PHỤ LỤC NGHỊ ĐỊNH» (cột A–G) → danh sách hóa chất theo đúng thứ tự văn bản."""
    items: list[dict] = []
    list_code = 0
    category = ""
    skip_rest = False
    order: dict[int, int] = {}
    last: dict | None = None      # dòng vừa đọc — nơi nhận các số CAS phụ ở dòng sau
    parent: dict | None = None    # dòng CÓ số thứ tự gần nhất — cha của các dòng con không số
    group, section = 0, ""        # phụ lục III: nhóm 1 / 2 và mục A (tiền chất CN) / B / C
    for raw in rows:
        a_raw, b_raw, c_raw, d_raw, e_raw, f_raw, g_raw = (list(raw) + [None] * 7)[:7]
        a, b, c, f = _text(a_raw), _text(b_raw), _text(c_raw), _text(f_raw)
        if c.upper().startswith("PHỤ LỤC "):
            roman = c.split()[-1].upper()
            list_code = APPENDIX_CODES.get(roman, 0)
            category, skip_rest, last, parent = "", False, None, None
            group, section = 0, ""
            continue
        if not list_code or skip_rest or a == "STT":
            continue
        if list_code == APPENDIX_CODES["IV"] and _BANG_B_RE.match(a):
            skip_rest = True
            continue
        is_stt = isinstance(a_raw, int) or bool(_STT_RE.match(a))
        tagged = f.lower().startswith("phụ lục")
        if (is_stt or tagged) and (b or c):
            order[list_code] = order.get(list_code, 0) + 1
            seq = a.rstrip(".") if is_stt else (parent["seq_no"] if parent else "")
            cas_list = split_cas(d_raw)
            name, name_vi = b or c, c
            #  Dòng con không số, không tên khoa học («Dạng hạt», «Dạng tinh thể» của mục 135 phụ
            #  lục IV) đứng một mình thì không biết là chất gì → ghép tên dòng cha phía trước.
            if not is_stt and not b and parent:
                name = f"{parent['name']} — {c}"
                name_vi = f"{parent['name_vi'] or parent['name']} — {c}"
            last = {
                "list_code": list_code,
                "seq_no": seq[:20],
                "sort_order": order[list_code],
                "name": name[:500],
                "name_vi": name_vi[:500],
                "cas_no": cas_list[0] if cas_list else "",
                "formula": _text(e_raw)[:100],
                "category": category,
                "threshold_kg": _threshold(g_raw) if list_code == APPENDIX_CODES["IV"] else None,
                "mixture_pct": _mixture_pct(list_code, group, section),
                "legal_basis": f"{LEGAL_BASIS} Phụ lục {_ROMAN[list_code]}",
                "extra_cas": cas_list[1:],
            }
            items.append(last)
            if is_stt:
                parent = last
        elif not (a or b or c) and d_raw is not None and last is not None:
            for extra in split_cas(d_raw):
                if extra != last["cas_no"] and extra not in last["extra_cas"]:
                    last["extra_cas"].append(extra)
        elif a and not is_stt and not _text(d_raw) and not _text(e_raw):
            heading = _heading(a, b, c)
            m = _GROUP_RE.search(a)
            if m:
                group, section = int(m.group(1)), ""
            elif a in ("A", "B", "C"):
                section = a
            #  Phụ lục III: ghi kèm nhóm vào phân loại — người đọc cần biết nhóm để hiểu ngưỡng %.
            category = (f"Nhóm {group} · {heading}" if group and not m else heading)[:100]
    for item in items:
        extra = item.pop("extra_cas")
        item["note"] = f"Số CAS khác: {'; '.join(extra)}"[:500] if extra else ""
    return items


def _name_key(name: str) -> str:
    return " ".join((name or "").lower().split())


def apply_rows(db: Session, items: list[dict]) -> dict[str, int]:
    """Đồng bộ bốn phụ lục NĐ 24 với `items`. Không commit — người gọi quyết định."""
    codes = sorted(APPENDIX_CODES.values())
    existing = db.query(CustomsRegulation).filter(CustomsRegulation.list_code.in_(codes)).all()

    def unique_index(pairs: Iterable[tuple[tuple, Any]]) -> dict:
        seen: dict = {}
        for key, value in pairs:
            seen.setdefault(key, []).append(value)
        return {k: v[0] for k, v in seen.items() if len(v) == 1}

    by_cas = unique_index(((r.list_code, r.cas_no), r) for r in existing if r.cas_no)
    by_name = unique_index(((r.list_code, _name_key(r.name)), r) for r in existing if r.name)
    new_cas_unique = unique_index(((i["list_code"], i["cas_no"]), True) for i in items if i["cas_no"])

    used: set[int] = set()
    inserted = updated = 0
    #  Nạp lại lần hai: khớp theo VỊ TRÍ dòng trong phụ lục + tên trước — trong tệp có cặp dòng trùng
    #  cả tên lẫn số CAS (cùng một chất ở hai mục), hai khóa kia không phân biệt được.
    by_position = unique_index(((r.list_code, r.sort_order, _name_key(r.name)), r)
                               for r in existing if r.sort_order)
    for item in items:
        row = by_position.get((item["list_code"], item["sort_order"], _name_key(item["name"])))
        cas_key = (item["list_code"], item["cas_no"])
        if row is None and item["cas_no"] and cas_key in new_cas_unique:
            row = by_cas.get(cas_key)
        if row is None or row.id in used:
            row = by_name.get((item["list_code"], _name_key(item["name"])))
        if row is not None and row.id in used:
            row = None
        fields = {k: item.get(k) for k in ("list_code", "seq_no", "sort_order", "name", "name_vi", "cas_no",
                                           "formula", "threshold_kg", "mixture_pct", "legal_basis", "note")}
        if row is None:
            db.add(CustomsRegulation(**fields, category=item["category"], banned_year=None, is_active=True))
            inserted += 1
            continue
        used.add(row.id)
        #  Ô CAS của tệp hỏng (`#VALUE!`) → rỗng: giữ số CAS đang có thay vì xóa mất.
        if not fields["cas_no"] and row.cas_no:
            fields["cas_no"] = row.cas_no
        for key, value in fields.items():
            setattr(row, key, value)
        if item["category"]:
            row.category = item["category"]
        row.is_active = True
        updated += 1

    deactivated = 0
    for row in existing:
        if row.id not in used and row.is_active:
            row.is_active = False
            deactivated += 1
    db.flush()
    return {"total": len(items), "inserted": inserted, "updated": updated, "deactivated": deactivated}
