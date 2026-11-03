"""ĐMH — phân bổ chi phí thu mua vào dòng hàng, CHỈ ĐỂ XEM (bao-CR-715 tách từ service.py).

bao-CR-719: phần lưu bảng chi phí dời sang `cost_save_service`; tệp này chỉ còn phép TÍNH (dict vào, dict ra, không
đọc / ghi DB). `_allocation_basis` và `allocate_import_costs` tách theo từng cách chia / từng bước chia.
"""
import json

from .model import ALLOCATION_METHOD_LABELS, AllocationMethod, COST_STAGE_PREFIX
from .import_cost_service import stage_of


# ───────────────────────── Phân bổ chi phí về dòng hàng (bao-CR-319 P4) ─────────────────────────
# Kết quả chia CHỈ ĐỂ XEM: tính lúc xem / lúc in, không ghi xuống cột nào, không đẩy vào
# giá tồn kho. Vì vậy hàm nhận/trả dict thuần (đúng dạng `_item` / `_import_cost` của
# controller) để màn hình, bản in và P5 cùng đọc một con số — giao diện tự cộng là lệch.
EQUAL_SHARE_LABEL = "Chia đều"
# Cách 5 "Nhập tay": tổng số gõ được phép lệch tối đa chừng này so với số quy đổi của khoản
# (số quy đổi là số thập phân sau nhân tỷ giá, người gõ số tròn đồng).
MANUAL_ALLOCATION_TOLERANCE = 1.0


def parse_manual_allocation(raw) -> dict[str, float]:
    """Đọc cột / payload `manual_allocation` thành {"<id dòng hàng>": số tiền VNĐ}.

    Nhận cả chuỗi JSON (từ DB) lẫn dict (từ payload); giá trị hỏng, khóa rỗng, số âm hay
    không phải số đều bị bỏ chứ không làm đổ cả đơn — cột này chỉ là dữ liệu phụ của khoản.
    """
    if not raw:
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        key = str(key).strip()
        if not key:
            continue
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            continue
        if amount > 0:
            out[key] = round(amount, 2)
    return out


def _line_goods_base(line: dict) -> float:
    """Tiền hàng QUY ĐỔI của một dòng theo SL đặt (cùng cách tính `goods_base` ở controller)."""
    return float(line.get("order_total") or 0) * float(line.get("exchange_rate") or 1)


def _basis_goods_base(line: dict) -> float:
    """Tiền hàng của một DÒNG ĐÃ CHUẨN HÓA trong `allocate_import_costs` (khóa `goods_base`)."""
    return float(line.get("goods_base") or 0)


def allocation_method_of(value) -> AllocationMethod:
    """Đọc ô cách chia thành `AllocationMethod`; rỗng / số lạ đọc thành theo giá trị (dùng chung cho phép chia và
    serializer để hai nơi không hiểu một ô theo hai kiểu)."""
    try:
        return AllocationMethod(int(value or 0))
    except ValueError:
        return AllocationMethod.BY_VALUE


def _value_or_equal_basis(lines: list[dict], warning: str = ""):
    """Cơ sở theo GIÁ TRỊ; giá trị cũng cộng bằng 0 thì chia ĐỀU. `warning` là lý do phải lùi về đây (rỗng = người
    dùng chọn đúng theo giá trị) — có lý do thì nối thêm cách đã dùng thực tế."""
    basis = [_basis_goods_base(line) for line in lines]
    if sum(basis) > 0:
        return basis, AllocationMethod.BY_VALUE, (warning + " — đã chia theo giá trị") if warning else ""
    return [1.0] * len(lines), None, (warning + " — đã chia đều") if warning else ""


def _fallback_to_value(lines: list[dict], warning: str):
    """Lùi của cách Nhập tay / Chỉ định mã: cơ sở theo giá trị (giá trị bằng 0 thì là chia đều) nhưng cách và lời
    cảnh báo LUÔN ghi là theo giá trị — giữ đúng nếp cũ, đừng gộp với `_value_or_equal_basis`."""
    return _value_or_equal_basis(lines)[0], AllocationMethod.BY_VALUE, warning + " — đã chia theo giá trị"


def _manual_basis(lines: list[dict], manual: dict[str, float] | None, amount: float):
    """Cách "Nhập tay": cơ sở là số tiền đã gõ cho từng dòng (khóa = id dòng hàng); tổng lệch quá
    `MANUAL_ALLOCATION_TOLERANCE` so với số tiền khoản thì lùi về giá trị."""
    manual = manual or {}
    basis = [float(manual.get(str(line.get("item_id") or ""), 0) or 0) for line in lines]
    entered = round(sum(basis), 2)
    if entered > 0 and abs(entered - float(amount or 0)) <= MANUAL_ALLOCATION_TOLERANCE:
        return basis, AllocationMethod.MANUAL, ""
    warning = (f"chọn nhập tay nhưng tổng đã gõ {entered:,.0f} đ lệch số tiền khoản {float(amount or 0):,.0f} đ"
               if entered > 0 else "chọn nhập tay nhưng chưa gõ số tiền dòng nào")
    return _fallback_to_value(lines, warning)


def _product_basis(target: str, lines: list[dict]):
    """Cách "Chỉ định mã": chỉ các dòng mang đúng mã nhận khoản; mã trống / đơn không có mã đó thì lùi về giá trị."""
    code = (target or "").strip()
    matched = [(line.get("product_code") or "").strip() == code for line in lines]
    if code and any(matched):
        # Dòng ĐMH được phép trùng mã: mọi dòng cùng mã chia nhau khoản này theo giá trị,
        # giá trị trống thì theo SL đặt, cũng trống thì chia đều.
        for pick in (_basis_goods_base, lambda l: float(l.get("qty_order") or 0), lambda l: 1.0):
            basis = [pick(line) if hit else 0.0 for line, hit in zip(lines, matched)]
            if sum(basis) > 0:
                return basis, AllocationMethod.BY_PRODUCT, ""
    warning = (f"Khoản chỉ định cho mã '{code}' nhưng đơn không có dòng hàng mã này"
               if code else "Khoản chọn chỉ định mã hàng nhưng chưa ghi mã")
    return _fallback_to_value(lines, warning)


# Cách chia theo một con số đo trên dòng: (cách lấy số của một dòng, câu báo khi mọi dòng đều bằng 0).
_MEASURED_BASES = {
    AllocationMethod.BY_WEIGHT: (lambda line: float(line.get("weight_kg") or 0),
                                 "chọn chia theo khối lượng nhưng chưa dòng nào có số kg"),
    AllocationMethod.BY_QUANTITY: (lambda line: float(line.get("qty_order") or 0),
                                   "chọn chia theo số lượng nhưng SL đặt của mọi dòng đều bằng 0"),
}


def _measured_basis(method: AllocationMethod, lines: list[dict]):
    """Theo khối lượng / số lượng; tổng bằng 0 thì lùi về giá trị (rồi chia đều) và nói rõ. Cách khác (theo giá trị)
    đi thẳng phép theo giá trị, không cảnh báo."""
    measured = _MEASURED_BASES.get(method)
    if measured is None:
        return _value_or_equal_basis(lines)
    pick, warning = measured
    basis = [pick(line) for line in lines]
    if sum(basis) > 0:
        return basis, method, ""
    return _value_or_equal_basis(lines, warning)


def _allocation_basis(method: AllocationMethod, target: str, lines: list[dict],
                      manual: dict[str, float] | None = None, amount: float = 0.0):
    """Trả (cơ sở chia từng dòng, cách chia THỰC TẾ, lời cảnh báo nếu phải đổi cách).

    Cơ sở nào cộng lại bằng 0 (chưa ai gõ kg, SL đặt toàn 0...) thì không chia được;
    lùi về theo giá trị, giá trị cũng 0 thì chia đều — và NÓI RÕ ra chứ không im lặng
    đổi cách, vì người xem sẽ tưởng số kg của họ đã được dùng.

    Cách "Nhập tay": cơ sở chính là số tiền đã gõ cho từng dòng (`manual`, khóa = id dòng
    hàng). Lúc lưu đã chặn tổng lệch, nhưng dòng hàng có thể bị xóa / số tiền khoản đổi sau
    đó nên lúc xem vẫn kiểm lại: lệch quá `MANUAL_ALLOCATION_TOLERANCE` thì lùi về giá trị
    và nói rõ.

    bao-CR-719: mỗi cách một hàm (`_manual_basis`, `_product_basis`, `_measured_basis`); có bài kiểm chụp kết quả
    `test_chup_ket_qua_tien_dmh_cr719.py`.
    """
    if method == AllocationMethod.MANUAL:
        return _manual_basis(lines, manual, amount)
    if method == AllocationMethod.BY_PRODUCT:
        return _product_basis(target, lines)
    return _measured_basis(method, lines)


def allocation_base_of(cost: dict, stage=None):
    """Số quy đổi của một khoản (dict đã tuần tự hóa) dùng để chia: theo giai đoạn chỉ định,
    hoặc số hiệu lực khi không chỉ định. None = giai đoạn đó chưa có số → khoản đứng ngoài."""
    if stage is None or stage == "effective":
        if "effective_base" in cost:
            return cost.get("effective_base")
        return cost.get("base_amount")     # dict cũ (bản in / test) chỉ có một số
    key = f"{COST_STAGE_PREFIX[stage_of(stage)]}_base"
    return cost.get(key) if key in cost else cost.get("base_amount")


def _allocation_lines(items: list[dict]) -> list[dict]:
    """Chuẩn hóa dòng hàng (dạng `_item()`) thành dòng để chia: tiền hàng quy đổi, chỗ cộng chi phí."""
    return [{"item_id": it.get("id"), "product_code": it.get("product_code") or "",
             "product_name": it.get("product_name") or "", "unit": it.get("unit") or "",
             "qty_order": float(it.get("qty_order") or 0), "weight_kg": float(it.get("weight_kg") or 0),
             "goods_base": round(_line_goods_base(it), 2), "cost_base": 0.0, "landed_base": 0.0,
             "costs": []} for it in items]


def _cost_share(cost: dict, method: AllocationMethod, effective, ratio: float, share: float) -> dict:
    """Phần một khoản chi phí mà một dòng hàng gánh (một phần tử trong `costs` của dòng)."""
    return {
        "cost_id": cost.get("id"), "cost_type": cost.get("cost_type"),
        "cost_type_label": cost.get("cost_type_label") or "",
        "description": cost.get("description") or "",
        "supplier_code": cost.get("supplier_code") or "", "supplier_name": cost.get("supplier_name") or "",
        "allocation_method": int(method),
        "allocation_method_label": ALLOCATION_METHOD_LABELS.get(method, ""),
        # Cách chia THỰC TẾ đã dùng (khác cách chọn khi phải lùi về giá trị / chia đều)
        "effective_method": int(effective) if effective else 0,
        "effective_method_label": ALLOCATION_METHOD_LABELS.get(effective, "") if effective else EQUAL_SHARE_LABEL,
        "ratio": round(ratio, 6), "base_amount": share,
    }


def _spread_cost(lines: list[dict], cost: dict, method: AllocationMethod, effective, basis: list[float],
                 amount: float) -> None:
    """Chia `amount` của một khoản về các dòng có cơ sở > 0 (ghi thẳng vào `lines`).

    Làm tròn: phần lệch DỒN VÀO DÒNG CUỐI (dòng cuối trong số các dòng có nhận khoản đó)
    để tổng các phần luôn bằng đúng số tiền khoản chi — kế toán đối chiếu là phải khớp.
    """
    total_basis = sum(basis)
    receivers = [i for i, b in enumerate(basis) if b > 0]
    last = receivers[-1]
    allocated = 0.0
    for i in receivers:
        ratio = basis[i] / total_basis
        share = round(amount - allocated, 2) if i == last else round(amount * ratio, 2)
        allocated = round(allocated + share, 2)
        lines[i]["costs"].append(_cost_share(cost, method, effective, ratio, share))
        lines[i]["cost_base"] = round(lines[i]["cost_base"] + share, 2)


def _allocation_result(lines: list[dict], warnings: list[str]) -> dict:
    """Cộng giá vốn từng dòng và tổng toàn đơn sau khi đã chia hết các khoản."""
    for line in lines:
        line["landed_base"] = round(line["goods_base"] + line["cost_base"], 2)
    goods_total = round(sum(line["goods_base"] for line in lines), 2)
    cost_total = round(sum(line["cost_base"] for line in lines), 2)
    return {"lines": lines, "goods_base_total": goods_total, "cost_total": cost_total,
            "landed_total": round(goods_total + cost_total, 2), "warnings": warnings}


def allocate_import_costs(items: list[dict], costs: list[dict], stage=None) -> dict:
    """Chia từng khoản chi phí về các dòng hàng theo `allocation_method` của khoản đó.

    Vào: `items` đúng dạng `_item()` và `costs` đúng dạng `_import_cost()` của controller
    (đã quy đổi VNĐ). Ra: mỗi dòng hàng là CHA, bên trong liệt kê từng khoản đã gánh kèm cách
    chia + tỷ lệ, cuối cùng là tổng toàn đơn — đúng chiều lồng đại ca chốt cho màn hình.

    bao-CR-453: `stage` = 1/2/3 chia theo số của giai đoạn đó (khoản chưa có số ở giai đoạn
    đó thì bỏ qua), None = theo số hiệu lực của từng dòng.

    Làm tròn: phần lệch DỒN VÀO DÒNG CUỐI (dòng cuối trong số các dòng có nhận khoản đó)
    để tổng các phần luôn bằng đúng số tiền khoản chi — kế toán đối chiếu là phải khớp.

    bao-CR-719: tách bước chuẩn hóa dòng (`_allocation_lines`) → chia từng khoản (`_spread_cost`) → cộng tổng
    (`_allocation_result`).
    """
    lines = _allocation_lines(items)
    warnings: list[str] = []
    costs = [c for c in costs if allocation_base_of(c, stage) is not None]
    if not lines:
        if costs:
            warnings.append("Đơn chưa có dòng hàng nên chưa chia được chi phí")
        goods_total = 0.0
        cost_total = round(sum(float(allocation_base_of(c, stage) or 0) for c in costs), 2)
        return {"lines": [], "goods_base_total": goods_total, "cost_total": cost_total,
                "landed_total": cost_total, "warnings": warnings}

    for cost in costs:
        method = allocation_method_of(cost.get("allocation_method"))
        amount = float(allocation_base_of(cost, stage) or 0)
        basis, effective, warning = _allocation_basis(
            method, cost.get("allocation_target") or "", lines,
            manual=parse_manual_allocation(cost.get("manual_allocation")), amount=amount)
        if warning:
            warnings.append(f"Khoản '{cost.get('description') or cost.get('cost_type_label') or ''}': {warning}")
        _spread_cost(lines, cost, method, effective, basis, amount)
    return _allocation_result(lines, warnings)
