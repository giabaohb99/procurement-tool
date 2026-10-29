"""Bộ TÍNH chi phí nhân sự theo kỳ (duoc-CR-690) — hàm THUẦN, không DB, không biết ai là người xem.

Bên trong luôn tính theo TỪNG THÁNG rồi mới gộp lên kỳ con và tổng kỳ (`doc/erp/hrm/06-ke-hoach-nhan-su.md` §3):
chi phí Q2 là chi phí thật của Q2 chứ không phải 1/4 của năm. Mã nguồn KHÔNG nhớ khoản nào (không ghi cứng
17,5%): mọi tỷ lệ, trần, tháng rơi đều đến từ `CostItem` do người dùng khai.

Kiểm hợp lệ (`validate_plan`) ném `PlanCalcError` với câu tiếng Việt; tầng API đổi thành 422.
"""
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from .constants import ActualSource, CostAppliesTo, CostCalcMethod, PlanPeriodType

M = CostCalcMethod
ZERO = Decimal(0)
_HUNDRED = Decimal(100)


class PlanCalcError(ValueError):
    """Dữ liệu kế hoạch sai luật tính — thông điệp tiếng Việt, hiển thị thẳng cho người dùng."""


@dataclass(frozen=True)
class CostItem:
    code: str
    name: str = ""
    group_id: int = 0
    calc_method: int = M.PER_HEAD_MONTH
    rate: Decimal = ZERO                 # % cho PERCENT_OF
    factor: Decimal = ZERO               # số tháng cho MONTHS_OF
    cap_amount: int = 0                  # trần / người / tháng; 0 = không trần
    amount: int = 0                      # PER_HEAD_ONCE (đồng / người) · LUMP_SUM (tổng)
    base_codes: tuple = ()
    applies_to: int = CostAppliesTo.ALL_POSITIONS
    position_ids: tuple = ()
    months: tuple = ()                   # rỗng = mọi tháng của kỳ
    sort_order: int = 0
    actual_source: int = 0               # ActualSource; chỉ để kiểm hợp lệ (bộ tính không dùng)


@dataclass(frozen=True)
class PlanLine:
    position_id: int                     # 0 = «Không theo vị trí»
    headcounts: tuple                    # một số cho mỗi kỳ con
    amounts: dict = field(default_factory=dict)   # {mã khoản PER_HEAD_MONTH: đồng / người / tháng}


# ---- Kỳ và kỳ con ---------------------------------------------------------------------------------
def _quarter(q: int) -> dict:
    return {"key": f"Q{q}", "label": f"Quý {q}", "months": [3 * q - 2, 3 * q - 1, 3 * q]}


def _month(m: int) -> dict:
    return {"key": f"M{m:02d}", "label": f"Tháng {m}", "months": [m]}


def period_layout(period_type: int, period_no: int) -> list[dict]:
    """Các kỳ con (= cột định biên + cột bảng tự tính): Năm→Q1..Q4 · Bán niên→2 quý · Quý→3 tháng · Tháng→1 cột."""
    pt, no = int(period_type), int(period_no)
    if pt == PlanPeriodType.YEAR and no == 1:
        return [_quarter(q) for q in (1, 2, 3, 4)]
    if pt == PlanPeriodType.HALF and no in (1, 2):
        return [_quarter(q) for q in (2 * no - 1, 2 * no)]
    if pt == PlanPeriodType.QUARTER and 1 <= no <= 4:
        return [_month(m) for m in _quarter(no)["months"]]
    if pt == PlanPeriodType.MONTH and 1 <= no <= 12:
        return [_month(no)]
    raise PlanCalcError("Loại kỳ hoặc số thứ tự kỳ không hợp lệ")


def period_label(year: int, period_type: int, period_no: int) -> str:
    """2026 · H2-2026 · Q3-2026 · 07/2026."""
    pt = int(period_type)
    if pt == PlanPeriodType.HALF:
        return f"H{period_no}-{year}"
    if pt == PlanPeriodType.QUARTER:
        return f"Q{period_no}-{year}"
    if pt == PlanPeriodType.MONTH:
        return f"{int(period_no):02d}/{year}"
    return str(year)


def period_months(period_type: int, period_no: int) -> list[int]:
    return [m for p in period_layout(period_type, period_no) for m in p["months"]]


# ---- Kiểm hợp lệ ----------------------------------------------------------------------------------
def validate_plan(period_type: int, period_no: int, items: list[CostItem], lines: list[PlanLine]) -> None:
    layout = period_layout(period_type, period_no)
    months_in_period = {m for p in layout for m in p["months"]}
    by_code: dict[str, CostItem] = {}
    for it in items:
        if not it.code:
            raise PlanCalcError("Khoản chi phí thiếu mã")
        if it.code in by_code:
            raise PlanCalcError(f"Mã khoản «{it.code}» bị trùng")
        by_code[it.code] = it
    for it in items:
        _validate_item(it, by_code, months_in_period)
    per_head_codes = {c for c, it in by_code.items() if it.calc_method == M.PER_HEAD_MONTH}
    seen_pos: set[int] = set()
    for ln in lines:
        if ln.position_id in seen_pos:
            raise PlanCalcError("Một vị trí chỉ được có một dòng số người")
        seen_pos.add(ln.position_id)
        if len(ln.headcounts) != len(layout):
            raise PlanCalcError(f"Dòng số người phải có đúng {len(layout)} số (mỗi kỳ con một số)")
        if any(h < 0 for h in ln.headcounts):
            raise PlanCalcError("Số người kế hoạch không được âm")
        for code, val in ln.amounts.items():
            if code not in per_head_codes:
                raise PlanCalcError(f"Cột «{code}» không phải khoản nhập theo vị trí của kế hoạch này")
            if val < 0:
                raise PlanCalcError("Số tiền không được âm")


def _validate_item(it: CostItem, by_code: dict, months_in_period: set) -> None:
    label = f"Khoản «{it.name or it.code}»"
    if it.calc_method not in {int(m) for m in M}:
        raise PlanCalcError(f"{label}: cách tính không hợp lệ")
    if it.applies_to not in {int(a) for a in CostAppliesTo}:
        raise PlanCalcError(f"{label}: phạm vi áp dụng không hợp lệ")
    if min(it.rate, it.factor) < 0 or it.cap_amount < 0 or it.amount < 0:
        raise PlanCalcError(f"{label}: tỷ lệ, số tháng, mức tính tối đa và số tiền không được âm")
    if it.applies_to == CostAppliesTo.WHOLE_DEPARTMENT and it.calc_method != M.LUMP_SUM:
        raise PlanCalcError(f"{label}: «cả phòng» chỉ dùng với cách tính «Số tiền cả phòng»")
    if it.applies_to == CostAppliesTo.SELECTED_POSITIONS and not it.position_ids:
        raise PlanCalcError(f"{label}: chọn «chỉ các vị trí» thì phải chọn ít nhất một vị trí")
    outside = sorted(set(it.months) - months_in_period)
    if outside:
        raise PlanCalcError(f"{label}: tháng {', '.join(map(str, outside))} nằm ngoài kỳ của kế hoạch")
    if it.calc_method == M.PERCENT_OF:
        if not it.base_codes:
            raise PlanCalcError(f"{label}: chưa chọn «Tính trên khoản» để tính phần trăm")
        for b in it.base_codes:
            _check_base(label, b, by_code, allowed=(M.PER_HEAD_MONTH, M.MONTHS_OF))
    if it.calc_method == M.PER_HEAD_ONCE and not it.months:
        raise PlanCalcError(f"{label}: chưa chọn tháng chi")
    _check_actual_source(label, it)
    if it.calc_method == M.MONTHS_OF:
        if len(it.base_codes) != 1:
            raise PlanCalcError(f"{label}: «Tính bằng số tháng lương» phải chọn đúng một khoản ở «Tính trên khoản»")
        _check_base(label, it.base_codes[0], by_code, allowed=(M.PER_HEAD_MONTH,))
        if not it.months:
            raise PlanCalcError(f"{label}: chưa chọn tháng chi")


def _check_actual_source(label: str, it: CostItem) -> None:
    """Nguồn thực tế phải khớp cách tính: lương cơ bản / phụ cấp chỉ cho khoản «số tiền / người / tháng»; % × lương đóng
    BHXH chỉ cho khoản «%»; các cách tính còn lại không có nguồn nào để so."""
    src = int(it.actual_source or 0)
    if src == ActualSource.NONE:
        return
    allowed = {ActualSource.BASE_SALARY: M.PER_HEAD_MONTH, ActualSource.ALLOWANCE: M.PER_HEAD_MONTH,
               ActualSource.PERCENT_OF_INSURANCE_SALARY: M.PERCENT_OF}.get(src)
    if allowed is None:
        raise PlanCalcError(f"{label}: nguồn thực tế không hợp lệ")
    if it.calc_method != allowed:
        raise PlanCalcError(f"{label}: nguồn thực tế này không dùng được với cách tính đã chọn")


def _check_base(label: str, code: str, by_code: dict, allowed: tuple) -> None:
    base = by_code.get(code)
    if base is None:
        raise PlanCalcError(f"{label}: khoản «{code}» ở «Tính trên khoản» không còn trong kế hoạch")
    if base.calc_method not in allowed:
        raise PlanCalcError(f"{label}: khoản «{code}» không dùng được ở «Tính trên khoản» "
                            "(chỉ chọn được khoản «Hằng tháng theo người» hoặc khoản tính bằng số tháng lương)")


# ---- Tính -----------------------------------------------------------------------------------------
def _round(v: Decimal) -> int:
    return int(v.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _in_months(it: CostItem, m: int) -> bool:
    return not it.months or m in it.months


def _applies(it: CostItem, ln: PlanLine) -> bool:
    if it.applies_to == CostAppliesTo.ALL_POSITIONS:
        return True
    return it.applies_to == CostAppliesTo.SELECTED_POSITIONS and ln.position_id in it.position_ids


def _nominal(it: CostItem, ln: PlanLine) -> Decimal:
    """Số tiền / người / tháng của khoản cách tính 1 cho một vị trí (không xét tháng chi).

    Ô của vị trí có số (> 0) thì dùng số đó; trống / 0 thì lấy MỨC CHUNG `it.amount` khai ở hộp thoại khoản (vd ăn trưa
    730k cho mọi người) — người dùng chỉ nhập riêng vị trí nào khác mức chung."""
    if not _applies(it, ln):
        return ZERO
    own = ln.amounts.get(it.code) or 0
    return Decimal(own if own > 0 else it.amount)


def _per_head(it: CostItem, ln: PlanLine, m: int, by_code: dict) -> Decimal:
    """Số tiền / người của khoản cách tính 1 hoặc 3 ở tháng m — cũng là «khoản gốc» của khoản %."""
    if not _in_months(it, m) or not _applies(it, ln):
        return ZERO
    if it.calc_method == M.MONTHS_OF:
        return it.factor * _nominal(by_code[it.base_codes[0]], ln)
    return _nominal(it, ln)


def _item_month(it: CostItem, m: int, lines: list, sub_of: dict, by_code: dict) -> Decimal:
    """Chi phí của MỘT khoản (cách tính 1–4) ở tháng m, cộng mọi dòng vị trí."""
    total = ZERO
    for ln in lines:
        hc = ln.headcounts[sub_of[m]]
        if not hc or not _applies(it, ln) or not _in_months(it, m):
            continue
        if it.calc_method == M.PER_HEAD_ONCE:
            total += hc * it.amount
        elif it.calc_method == M.PERCENT_OF:
            base = sum((_per_head(by_code[b], ln, m, by_code) for b in it.base_codes), ZERO)
            if it.cap_amount:
                base = min(base, Decimal(it.cap_amount))
            total += hc * base * it.rate / _HUNDRED
        else:   # PER_HEAD_MONTH · MONTHS_OF
            total += hc * _per_head(it, ln, m, by_code)
    return total


def _lump_by_month(it: CostItem, months_all: list[int]) -> dict[int, int]:
    """Chia đều `amount` cho các tháng rơi vào; dư (đồng lẻ) dồn cho các tháng đầu để tổng khớp tuyệt đối."""
    ms = [m for m in months_all if _in_months(it, m)]
    if not ms:
        return {}
    base, extra = divmod(it.amount, len(ms))
    return {m: base + (1 if i < extra else 0) for i, m in enumerate(ms)}


def compute_plan(period_type: int, period_no: int, year: int, items: list[CostItem], lines: list[PlanLine],
                 group_names: dict | None = None, group_sort: dict | None = None) -> dict:
    """Kết quả đầy đủ cho form «Hệ thống tự tính» và cho báo cáo (`monthly`)."""
    validate_plan(period_type, period_no, items, lines)
    layout = period_layout(period_type, period_no)
    months_all = [m for p in layout for m in p["months"]]
    sub_of = {m: i for i, p in enumerate(layout) for m in p["months"]}
    ordered = sorted(enumerate(items), key=lambda t: (t[1].sort_order, t[0]))
    ordered = [it for _, it in ordered]
    by_code = {it.code: it for it in items}

    monthly: dict[int, dict] = {m: {"headcount": sum(ln.headcounts[sub_of[m]] for ln in lines), "items": {}}
                                for m in months_all}
    for it in ordered:
        lump = _lump_by_month(it, months_all) if it.calc_method == M.LUMP_SUM else None
        for m in months_all:
            value = lump.get(m, 0) if lump is not None else _round(_item_month(it, m, lines, sub_of, by_code))
            monthly[m]["items"][it.code] = value

    def fold(per_month: dict) -> dict:
        values = [sum(per_month.get(m, 0) for m in p["months"]) for p in layout]
        return {"values": values, "total": sum(values)}

    out_items = [{"code": it.code, "name": it.name, "group_id": it.group_id,
                  **fold({m: monthly[m]["items"][it.code] for m in months_all})} for it in ordered]
    names = group_names or {}
    group_order: list[int] = []
    for row in out_items:
        if row["group_id"] not in group_order:
            group_order.append(row["group_id"])
    #  Nhóm xếp theo «Thứ tự» người dùng khai ở danh mục Nhóm chi phí; cùng thứ tự (hoặc không có) thì theo khoản đầu tiên.
    sort_of = group_sort or {}
    first_seen = {gid: i for i, gid in enumerate(group_order)}
    group_order.sort(key=lambda gid: (sort_of.get(gid, 1 << 30), first_seen[gid]))
    groups = []
    for gid in group_order:
        rows = [r for r in out_items if r["group_id"] == gid]
        values = [sum(r["values"][i] for r in rows) for i in range(len(layout))]
        groups.append({"group_id": gid, "name": names.get(gid, ""), "values": values, "total": sum(values)})
    total_values = [sum(g["values"][i] for g in groups) for i in range(len(layout))]
    total = sum(total_values)
    avg_heads = Decimal(sum(monthly[m]["headcount"] for m in months_all)) / len(months_all)
    return {
        "periods": layout,
        "headcount": [sum(ln.headcounts[i] for ln in lines) for i in range(len(layout))],
        "items": out_items, "groups": groups,
        "total": {"values": total_values, "total": total},
        "avg_per_head": _round(Decimal(total) / avg_heads) if avg_heads > 0 else None,
        "monthly": monthly,
    }
