"""ĐMH — phân bổ chi phí thu mua vào dòng hàng và lưu bảng chi phí (bao-CR-715 tách từ service.py)."""
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import (ALLOCATION_METHOD_LABELS, AllocationMethod, COST_STAGE_PREFIX, DEFAULT_CURRENCY, ImportCostType,
                    POCost, PurchaseOrder)
from .base_service import items_of, rate_of
from .import_cost_service import (_cost_label, block_delete_paid_import_cost, compute_cost_bases, cost_amount_of,
                                  cost_type_map, effective_base_of, import_costs_of, is_final_cost, stage_of,
                                  sync_import_cost_payables)


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
    """
    if method == AllocationMethod.MANUAL:
        manual = manual or {}
        basis = [float(manual.get(str(line.get("item_id") or ""), 0) or 0) for line in lines]
        entered = round(sum(basis), 2)
        if entered > 0 and abs(entered - float(amount or 0)) <= MANUAL_ALLOCATION_TOLERANCE:
            return basis, method, ""
        warning = (f"chọn nhập tay nhưng tổng đã gõ {entered:,.0f} đ lệch số tiền khoản {float(amount or 0):,.0f} đ"
                   if entered > 0 else "chọn nhập tay nhưng chưa gõ số tiền dòng nào")
        return _allocation_basis(AllocationMethod.BY_VALUE, "", lines)[0], AllocationMethod.BY_VALUE, \
            warning + " — đã chia theo giá trị"

    if method == AllocationMethod.BY_PRODUCT:
        code = (target or "").strip()
        matched = [(line.get("product_code") or "").strip() == code for line in lines]
        if code and any(matched):
            # Dòng ĐMH được phép trùng mã: mọi dòng cùng mã chia nhau khoản này theo giá trị,
            # giá trị trống thì theo SL đặt, cũng trống thì chia đều.
            for pick in (_basis_goods_base, lambda l: float(l.get("qty_order") or 0), lambda l: 1.0):
                basis = [pick(line) if hit else 0.0 for line, hit in zip(lines, matched)]
                if sum(basis) > 0:
                    return basis, method, ""
        warning = (f"Khoản chỉ định cho mã '{code}' nhưng đơn không có dòng hàng mã này"
                   if code else "Khoản chọn chỉ định mã hàng nhưng chưa ghi mã")
        return _allocation_basis(AllocationMethod.BY_VALUE, "", lines)[0], AllocationMethod.BY_VALUE, \
            warning + " — đã chia theo giá trị"

    if method == AllocationMethod.BY_WEIGHT:
        basis = [float(line.get("weight_kg") or 0) for line in lines]
        if sum(basis) > 0:
            return basis, method, ""
        warning = "chọn chia theo khối lượng nhưng chưa dòng nào có số kg"
    elif method == AllocationMethod.BY_QUANTITY:
        basis = [float(line.get("qty_order") or 0) for line in lines]
        if sum(basis) > 0:
            return basis, method, ""
        warning = "chọn chia theo số lượng nhưng SL đặt của mọi dòng đều bằng 0"
    else:
        warning = ""

    basis = [_basis_goods_base(line) for line in lines]
    if sum(basis) > 0:
        return basis, AllocationMethod.BY_VALUE, (warning + " — đã chia theo giá trị") if warning else ""
    return [1.0] * len(lines), None, (warning + " — đã chia đều") if warning else ""


def allocation_base_of(cost: dict, stage=None):
    """Số quy đổi của một khoản (dict đã tuần tự hóa) dùng để chia: theo giai đoạn chỉ định,
    hoặc số hiệu lực khi không chỉ định. None = giai đoạn đó chưa có số → khoản đứng ngoài."""
    if stage is None or stage == "effective":
        if "effective_base" in cost:
            return cost.get("effective_base")
        return cost.get("base_amount")     # dict cũ (bản in / test) chỉ có một số
    key = f"{COST_STAGE_PREFIX[stage_of(stage)]}_base"
    return cost.get(key) if key in cost else cost.get("base_amount")


def allocate_import_costs(items: list[dict], costs: list[dict], stage=None) -> dict:
    """Chia từng khoản chi phí về các dòng hàng theo `allocation_method` của khoản đó.

    Vào: `items` đúng dạng `_item()` và `costs` đúng dạng `_import_cost()` của controller
    (đã quy đổi VNĐ). Ra: mỗi dòng hàng là CHA, bên trong liệt kê từng khoản đã gánh kèm cách
    chia + tỷ lệ, cuối cùng là tổng toàn đơn — đúng chiều lồng đại ca chốt cho màn hình.

    bao-CR-453: `stage` = 1/2/3 chia theo số của giai đoạn đó (khoản chưa có số ở giai đoạn
    đó thì bỏ qua), None = theo số hiệu lực của từng dòng.

    Làm tròn: phần lệch DỒN VÀO DÒNG CUỐI (dòng cuối trong số các dòng có nhận khoản đó)
    để tổng các phần luôn bằng đúng số tiền khoản chi — kế toán đối chiếu là phải khớp.
    """
    lines = [{"item_id": it.get("id"), "product_code": it.get("product_code") or "",
              "product_name": it.get("product_name") or "", "unit": it.get("unit") or "",
              "qty_order": float(it.get("qty_order") or 0), "weight_kg": float(it.get("weight_kg") or 0),
              "goods_base": round(_line_goods_base(it), 2), "cost_base": 0.0, "landed_base": 0.0,
              "costs": []} for it in items]
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
        try:
            method = AllocationMethod(int(cost.get("allocation_method") or 0))
        except ValueError:
            method = AllocationMethod.BY_VALUE
        amount = float(allocation_base_of(cost, stage) or 0)
        basis, effective, warning = _allocation_basis(
            method, cost.get("allocation_target") or "", lines,
            manual=parse_manual_allocation(cost.get("manual_allocation")), amount=amount)
        if warning:
            warnings.append(f"Khoản '{cost.get('description') or cost.get('cost_type_label') or ''}': {warning}")
        total_basis = sum(basis)
        receivers = [i for i, b in enumerate(basis) if b > 0]
        last = receivers[-1]
        allocated = 0.0
        for i in receivers:
            ratio = basis[i] / total_basis
            share = round(amount - allocated, 2) if i == last else round(amount * ratio, 2)
            allocated = round(allocated + share, 2)
            lines[i]["costs"].append({
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
            })
            lines[i]["cost_base"] = round(lines[i]["cost_base"] + share, 2)

    for line in lines:
        line["landed_base"] = round(line["goods_base"] + line["cost_base"], 2)
    goods_total = round(sum(line["goods_base"] for line in lines), 2)
    cost_total = round(sum(line["cost_base"] for line in lines), 2)
    return {"lines": lines, "goods_base_total": goods_total, "cost_total": cost_total,
            "landed_total": round(goods_total + cost_total, 2), "warnings": warnings}


# bao-CR-467: những cột của một dòng chi phí mà người dùng gõ được trên bảng. Dùng để biết
# payload có SỬA gì thật không — màn hình gửi lại CẢ bảng mỗi lần bấm Lưu, nên dòng đã khóa
# vẫn đi kèm nguyên giá trị cũ; chặn theo "có mặt trong payload" thì không ai lưu nổi đơn nữa.
_COST_TEXT_FIELDS = ("description", "supplier_code", "supplier_name", "currency",
                     "allocation_target", "invoice_no", "invoice_date", "payment_due_date", "note")
_COST_NUMBER_FIELDS = ("cost_type", "vat", "allocation_method")


def is_cost_row_changed(row: POCost, data: dict, stage_fields: dict, manual: dict) -> bool:
    """Payload có sửa gì so với dòng đang lưu không (so chữ sau khi cắt khoảng trắng, so số
    bằng float vì cột tiền là Decimal còn giao diện gửi số thường).

    Tỷ giá đứng ngoài phép so: giao diện để trống là `0` rồi backend tự suy, nên so nó thì
    dòng nào cũng thành "đã sửa". Số tiền mới là thứ phải canh.
    """
    for field in _COST_TEXT_FIELDS:
        if field in data and (data.get(field) or "").strip() != (getattr(row, field, "") or "").strip():
            return True
    for field in _COST_NUMBER_FIELDS:
        if field in data and float(data.get(field) or 0) != float(getattr(row, field, 0) or 0):
            return True
    for stage, prefix in COST_STAGE_PREFIX.items():
        old = cost_amount_of(row, stage)
        new = stage_fields.get(f"{prefix}_amount")
        #  Trống (None) và 0 là MỘT với phép so này: bản v1 gửi 0 cho ô chưa gõ, còn dòng chuyển
        #  từ khuôn cũ (migration 05a62d38a47a) để trống cột Dự toán / Tạm tính — so khắt khe thì
        #  mọi lần lưu ĐMH trên v1 đều ăn 400 "đã quyết toán" (rà bản sao prod 28/09/2026, PO00122).
        if round(float(old or 0), 2) != round(float(new or 0), 2):
            return True
    old_manual = parse_manual_allocation(row.manual_allocation)
    return ({k: round(float(v), 2) for k, v in manual.items()}
            != {k: round(float(v), 2) for k, v in old_manual.items()})


def _save_import_costs(db: Session, po: PurchaseOrder, costs, user_id: int):
    """Upsert bảng chi phí theo id, xóa dòng không còn trong payload.

    Không gửi khóa `import_costs` (costs is None) = màn hình không đụng tới bảng này,
    giữ nguyên. Gửi mảng rỗng = người dùng đã xóa hết dòng.
    """
    if costs is None:
        return
    existing = {c.id: c for c in import_costs_of(db, po.id)}
    # `_save_items` chạy trước nên id dòng hàng đã có; số nhập tay chỉ giữ khóa của dòng còn tồn tại.
    item_ids = {str(it.id) for it in items_of(db, po.id)}
    types = cost_type_map(db)
    po_currency = (po.currency or "").strip() or DEFAULT_CURRENCY
    keep = set()
    for raw in costs:
        data = raw.model_dump()
        manual = {k: v for k, v in parse_manual_allocation(data.pop("manual_allocation", None)).items()
                  if k in item_ids}
        cid = data.pop("id", None)
        row = existing.get(cid) if cid else None
        # Loại chi phí phải có trong danh mục và còn dùng; dòng cũ đang mang loại đã ngừng thì
        # vẫn lưu được (không thì không sửa nổi ô nào khác). DB chưa seed danh mục → bộ mã cứng.
        code = int(data.get("cost_type") or 0)
        if types:
            ctype = types.get(code)
            if ctype is None:
                raise HTTPException(400, f"Loại chi phí mã {code} không có trong danh mục")
            if not ctype.is_active and not (row is not None and int(row.cost_type or 0) == code):
                raise HTTPException(400, f"Loại chi phí \"{ctype.name}\" đã ngừng dùng, chọn loại khác")
            data["cost_type"] = code
        else:
            try:
                data["cost_type"] = int(ImportCostType(code))
            except ValueError:
                data["cost_type"] = int(ImportCostType.OTHER)
        if not (data.get("currency") or "").strip():
            data["currency"] = po_currency
        # Chia theo chỉ định mà không chọn mã hàng thì không chia được — về mặc định theo giá trị.
        if int(data.get("allocation_method") or 0) == int(AllocationMethod.BY_PRODUCT) \
                and not (data.get("allocation_target") or "").strip():
            data["allocation_method"] = int(AllocationMethod.BY_VALUE)
        # bao-CR-467: bảng chi phí gõ tự do như Excel — CẢ BA cột Dự toán / Tạm tính / Quyết
        # toán đều ghi được bất kể đơn đang ở giai đoạn nào. Gõ sẵn số Quyết toán KHÔNG sinh
        # công nợ: nợ chỉ hiện ra khi dòng (hoặc cả đơn) được CHỐT sang Quyết toán.
        # (Luật cũ bao-CR-453 chỉ mở đúng cột của giai đoạn hiệu lực — đã bỏ.)
        stage_fields: dict[str, object] = {}
        for stage, prefix in COST_STAGE_PREFIX.items():
            stage_fields[f"{prefix}_amount"] = data.pop(f"{prefix}_amount", None)
            stage_fields[f"{prefix}_rate"] = data.pop(f"{prefix}_rate", None)
        # bao-CR-467: chốt rồi là khóa. Dòng đã ở Quyết toán hiệu lực đã lên công nợ, sửa nó
        # là lệch sổ — muốn sửa thì mở lại dòng (hoặc mở lại cả đơn) trước. Payload trùng khít
        # giá trị cũ thì đi tiếp im lặng, vì màn hình gửi lại cả bảng mỗi lần lưu.
        if row is not None and is_final_cost(row, po):
            if is_cost_row_changed(row, data, stage_fields, manual):
                raise HTTPException(
                    400, f"Dòng chi phí \"{_cost_label(row, types)}\" đã quyết toán, không sửa được. "
                         f"Mở lại dòng đó rồi hãy sửa.")
            keep.add(row.id)
            continue
        if row is not None:
            for k, v in data.items():
                setattr(row, k, v)
            row.updated_by = user_id
        else:
            row = POCost(po_id=po.id, created_by=user_id, updated_by=user_id, **data)
            db.add(row)
        for stage, prefix in COST_STAGE_PREFIX.items():
            amount = stage_fields.get(f"{prefix}_amount")
            rate = float(stage_fields.get(f"{prefix}_rate") or 0)
            if not rate:
                # Chi phí ghi bằng đúng đồng tiền của đơn thì theo tỷ giá đơn; khác đồng tiền
                # (cước nội địa trả bằng VNĐ trong đơn USD) thì để 1 chứ không mượn tỷ giá đơn.
                rate = rate_of(po) if (row.currency or "") == po_currency else 1
            setattr(row, f"{prefix}_amount", None if amount is None else float(amount))
            setattr(row, f"{prefix}_rate", rate)
        compute_cost_bases(row)
        # Nhập tay: tổng các dòng phải bằng đúng số quy đổi của khoản — chặn ngay lúc lưu chứ
        # không im lặng lùi về giá trị, vì thu mua gõ tay là để cân số với chứng từ.
        if int(data.get("allocation_method") or 0) == int(AllocationMethod.MANUAL):
            label = (data.get("description") or "").strip() or "chi phí"
            if not manual:
                raise HTTPException(400, f"Khoản '{label}' chọn nhập tay nhưng chưa nhập số tiền dòng nào")
            entered = round(sum(manual.values()), 2)
            target_amount = effective_base_of(row, po)
            if abs(entered - target_amount) > MANUAL_ALLOCATION_TOLERANCE:
                raise HTTPException(
                    400, f"Khoản '{label}' chọn nhập tay: tổng đã nhập {entered:,.0f} đ, "
                         f"phải bằng {target_amount:,.0f} đ (lệch {entered - target_amount:,.0f} đ)")
            row.manual_allocation = json.dumps(manual)
        else:
            row.manual_allocation = ""
        db.flush()
        keep.add(row.id)

    for old_id, row in existing.items():
        if old_id not in keep:
            # bao-CR-467: khóa sau khi chốt phải khóa cả đường XÓA, không thì "không sửa được"
            # chỉ tốn một cú bấm để đi vòng — xóa dòng rồi gõ lại một dòng mới y hệt.
            if is_final_cost(row, po):
                raise HTTPException(
                    400, f"Dòng chi phí \"{_cost_label(row, types)}\" đã quyết toán, không xóa được. "
                         f"Mở lại dòng đó rồi hãy xóa.")
            block_delete_paid_import_cost(db, row)
            db.delete(row)
    db.flush()
    # bao-CR-319 P5 — bảng chi phí đổi là công nợ chi phí đổi theo, cùng một lần lưu.
    sync_import_cost_payables(db, po, user_id)
