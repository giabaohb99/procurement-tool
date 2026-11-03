"""ĐMH — LƯU bảng chi phí thu mua từ màn hình (bao-CR-719 dời từ `cost_allocation_service`, tách theo bước).

`_save_import_costs` (F 45 trước khi tách) nay đi từng dòng payload qua các bước: kiểm loại chi phí
(`_check_cost_type`) → chuẩn hóa ô mặc định + bóc số ba giai đoạn (`_normalize_cost_data`) → dòng đã quyết toán thì
chỉ kiểm có sửa không (`_block_edit_final_cost`) → ghi dòng + tính số quy đổi (`_write_cost_row`) → kiểm và ghi số
nhập tay (`_write_manual_allocation`); cuối cùng xóa dòng bị bỏ (`_delete_dropped_costs`) rồi đồng bộ công nợ. Thứ tự
ghi, câu lỗi và số câu truy vấn giữ nguyên — bài kiểm chụp kết quả `test_chup_ket_qua_tien_dmh_cr719.py`.
"""
import json
from typing import NamedTuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import AllocationMethod, COST_STAGE_PREFIX, DEFAULT_CURRENCY, ImportCostType, POCost, PurchaseOrder
from .base_service import items_of, rate_of
from .import_cost_service import (_cost_label, block_delete_paid_import_cost, compute_cost_bases, cost_amount_of,
                                  cost_type_map, effective_base_of, import_costs_of, is_final_cost,
                                  sync_import_cost_payables)
from .cost_allocation_service import MANUAL_ALLOCATION_TOLERANCE, parse_manual_allocation


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


class _CostSaveContext(NamedTuple):
    """Những thứ nạp MỘT lần cho cả lượt lưu (không truy vấn lại trong vòng lặp từng dòng)."""
    existing: dict[int, POCost]     # dòng chi phí đang lưu, khóa theo id
    item_ids: set[str]              # id dòng hàng còn tồn tại (khóa hợp lệ của số nhập tay)
    types: dict                     # danh mục loại chi phí; rỗng = DB chưa seed → bộ mã cứng
    po_currency: str


def _check_cost_type(data: dict, row: POCost | None, types: dict) -> None:
    """Kiểm loại chi phí của một dòng payload rồi ghi lại mã đã chuẩn hóa vào `data`.

    Loại chi phí phải có trong danh mục và còn dùng; dòng cũ đang mang loại đã ngừng thì
    vẫn lưu được (không thì không sửa nổi ô nào khác). DB chưa seed danh mục → bộ mã cứng.
    """
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


def _normalize_cost_data(data: dict, po_currency: str) -> dict:
    """Điền ô mặc định của một dòng payload (sửa thẳng `data`) và bóc ba cặp số / tỷ giá của ba giai đoạn ra một
    dict riêng (trả về) — hai thứ đó ghi theo luật riêng ở `_write_cost_row`."""
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
    return stage_fields


def _block_edit_final_cost(row: POCost, data: dict, stage_fields: dict, manual: dict, types: dict) -> None:
    """bao-CR-467: chốt rồi là khóa. Dòng đã ở Quyết toán hiệu lực đã lên công nợ, sửa nó
    là lệch sổ — muốn sửa thì mở lại dòng (hoặc mở lại cả đơn) trước. Payload trùng khít
    giá trị cũ thì đi tiếp im lặng, vì màn hình gửi lại cả bảng mỗi lần lưu."""
    if is_cost_row_changed(row, data, stage_fields, manual):
        raise HTTPException(
            400, f"Dòng chi phí \"{_cost_label(row, types)}\" đã quyết toán, không sửa được. "
                 f"Mở lại dòng đó rồi hãy sửa.")


def _write_cost_row(db: Session, po: PurchaseOrder, row: POCost | None, data: dict, stage_fields: dict,
                    po_currency: str, user_id: int) -> POCost:
    """Ghi một dòng (sửa dòng cũ hoặc thêm dòng mới), số + tỷ giá ba giai đoạn, rồi tính lại ba cột quy đổi."""
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
    return row


def _write_manual_allocation(row: POCost, data: dict, manual: dict, po: PurchaseOrder) -> None:
    """Ghi số nhập tay của dòng (cách 5); cách khác thì xóa trắng cột."""
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


def _save_cost_row(db: Session, po: PurchaseOrder, raw, ctx: _CostSaveContext, user_id: int) -> int:
    """Lưu MỘT dòng payload theo bước kiểm → tính → ghi; trả id dòng phải giữ lại."""
    data = raw.model_dump()
    manual = {k: v for k, v in parse_manual_allocation(data.pop("manual_allocation", None)).items()
              if k in ctx.item_ids}
    cid = data.pop("id", None)
    row = ctx.existing.get(cid) if cid else None
    _check_cost_type(data, row, ctx.types)
    stage_fields = _normalize_cost_data(data, ctx.po_currency)
    if row is not None and is_final_cost(row, po):
        _block_edit_final_cost(row, data, stage_fields, manual, ctx.types)
        return row.id
    row = _write_cost_row(db, po, row, data, stage_fields, ctx.po_currency, user_id)
    _write_manual_allocation(row, data, manual, po)
    db.flush()
    return row.id


def _delete_dropped_costs(db: Session, po: PurchaseOrder, ctx: _CostSaveContext, keep: set[int]) -> None:
    """Xóa dòng không còn trong payload — dòng đã quyết toán / đã chi thì chặn."""
    for old_id, row in ctx.existing.items():
        if old_id not in keep:
            # bao-CR-467: khóa sau khi chốt phải khóa cả đường XÓA, không thì "không sửa được"
            # chỉ tốn một cú bấm để đi vòng — xóa dòng rồi gõ lại một dòng mới y hệt.
            if is_final_cost(row, po):
                raise HTTPException(
                    400, f"Dòng chi phí \"{_cost_label(row, ctx.types)}\" đã quyết toán, không xóa được. "
                         f"Mở lại dòng đó rồi hãy xóa.")
            block_delete_paid_import_cost(db, row)
            db.delete(row)


def _save_import_costs(db: Session, po: PurchaseOrder, costs, user_id: int):
    """Upsert bảng chi phí theo id, xóa dòng không còn trong payload.

    Không gửi khóa `import_costs` (costs is None) = màn hình không đụng tới bảng này,
    giữ nguyên. Gửi mảng rỗng = người dùng đã xóa hết dòng.
    """
    if costs is None:
        return
    ctx = _CostSaveContext(
        existing={c.id: c for c in import_costs_of(db, po.id)},
        # `_save_items` chạy trước nên id dòng hàng đã có; số nhập tay chỉ giữ khóa của dòng còn tồn tại.
        item_ids={str(it.id) for it in items_of(db, po.id)},
        types=cost_type_map(db),
        po_currency=(po.currency or "").strip() or DEFAULT_CURRENCY)
    keep = set()
    for raw in costs:
        keep.add(_save_cost_row(db, po, raw, ctx, user_id))
    _delete_dropped_costs(db, po, ctx, keep)
    db.flush()
    # bao-CR-319 P5 — bảng chi phí đổi là công nợ chi phí đổi theo, cùng một lần lưu.
    sync_import_cost_payables(db, po, user_id)
