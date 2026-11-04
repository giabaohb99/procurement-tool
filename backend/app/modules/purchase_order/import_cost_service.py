"""ĐMH — chi phí thu mua (tên lịch sử import_cost): tra cứu, ba giai đoạn, chốt, công nợ chi phí (bao-CR-715 tách từ
service.py).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.payable import service as pay_service
from app.modules.payable.model import Payable

from .model import (COST_STAGE_LABELS, COST_STAGE_PREFIX, CostStage, IMPORT_COST_TYPE_LABELS, ImportCostType, OrderType,
                    POCost, POCostType, PurchaseOrder)
from .base_service import _supplier_map, normalize_rate


# ───────────────── Chi phí thu mua (bao-CR-319 P3 · ba giai đoạn bao-CR-453) ─────────────────
# Tên hàm / khóa API vẫn mang chữ `import_cost` vì đó là tên lịch sử đã nằm trong dữ liệu
# (`tab_payable.source_type`) và trong hai bản giao diện; chỉ NHÃN đổi thành "Chi phí thu mua".
def import_costs_of(db: Session, po_id: int):
    return (db.query(POCost).filter(POCost.po_id == po_id)
            .order_by(POCost.id.asc()).all())


def cost_type_map(db: Session) -> dict[int, POCostType]:
    """Danh mục loại chi phí, khóa theo mã số. Rỗng = DB chưa seed (bộ test cũ) → đọc bộ mã cứng."""
    return {int(t.code): t for t in db.query(POCostType).all()}


def cost_type_name(code: int, types: dict[int, POCostType] | None = None) -> str:
    """Tên loại chi phí: ưu tiên danh mục, không có thì lùi về bộ mã cứng, mã lạ thì "Chi phí khác"."""
    if types and int(code or 0) in types:
        return types[int(code)].name or ""
    try:
        return IMPORT_COST_TYPE_LABELS[ImportCostType(int(code or 0))]
    except ValueError:
        return IMPORT_COST_TYPE_LABELS[ImportCostType.OTHER]


def cost_type_creates_payable(code: int, types: dict[int, POCostType] | None = None) -> bool:
    """Loại chi phí này có sinh công nợ không. Không có danh mục hay mã lạ → CÓ (đúng nếp cũ)."""
    if types and int(code or 0) in types:
        return bool(types[int(code)].creates_payable)
    return True


def stage_of(value) -> CostStage:
    """Đọc một ô giai đoạn thành `CostStage`; rỗng / giá trị lạ đọc thành Dự toán."""
    try:
        return CostStage(int(value or 0))
    except ValueError:
        return CostStage.ESTIMATE


def cost_amount_of(row, stage: CostStage):
    """Số TRƯỚC thuế (nguyên tệ) của một giai đoạn; None = giai đoạn đó chưa có số."""
    value = getattr(row, f"{COST_STAGE_PREFIX[stage]}_amount", None)
    return None if value is None else float(value)


def cost_rate_of(row, stage: CostStage) -> float:
    """Tỷ giá riêng của giai đoạn; trống / 0 đọc thành 1 (cùng luật `normalize_rate`)."""
    return normalize_rate(getattr(row, f"{COST_STAGE_PREFIX[stage]}_rate", None))


def cost_base_of(row, stage: CostStage):
    """Tổng một giai đoạn ĐÃ gồm VAT, quy về VNĐ; None khi giai đoạn chưa có số.

    Tính từ amount × (1 + vat%) × tỷ giá của chính giai đoạn đó — không đọc cột `_base`
    để chỗ nào đổi VAT / tỷ giá mà chưa kịp lưu vẫn ra đúng số.
    """
    amount = cost_amount_of(row, stage)
    if amount is None:
        return None
    return round(amount * (1 + float(getattr(row, "vat", 0) or 0) / 100) * cost_rate_of(row, stage), 2)


def compute_cost_bases(row) -> None:
    """Ghi lại ba cột `_base` từ amount / vat / rate — gọi mỗi lần lưu dòng."""
    for stage, prefix in COST_STAGE_PREFIX.items():
        setattr(row, f"{prefix}_base", cost_base_of(row, stage))


def effective_stage_of(row, po) -> CostStage:
    """Giai đoạn HIỆU LỰC của một dòng = cao hơn giữa giai đoạn của đơn và của riêng dòng."""
    return max(stage_of(getattr(po, "cost_stage", None)), stage_of(getattr(row, "line_stage", None)))


def filled_stage_of(row, po):
    """Giai đoạn cao nhất KHÔNG vượt giai đoạn hiệu lực mà đã có số; None = dòng chưa có số nào."""
    top = effective_stage_of(row, po)
    for stage in sorted(CostStage, key=int, reverse=True):
        if stage <= top and cost_amount_of(row, stage) is not None:
            return stage
    return None


def effective_base_of(row, po) -> float:
    """Số quy đổi đang có hiệu lực của dòng — số của giai đoạn cao nhất đã điền, 0 nếu chưa có gì."""
    stage = filled_stage_of(row, po)
    return 0.0 if stage is None else float(cost_base_of(row, stage) or 0)


def is_final_cost(row, po) -> bool:
    """Dòng đang ở QUYẾT TOÁN (theo đơn hoặc riêng dòng) — chỉ dòng này mới sinh công nợ."""
    return effective_stage_of(row, po) == CostStage.FINAL


def final_costs(rows: list[dict]) -> list[dict]:
    """Lọc lấy dòng đã QUYẾT TOÁN từ danh sách đã tuần tự hóa (`_import_cost` của controller)."""
    return [r for r in rows if int(r.get("effective_stage") or 0) == int(CostStage.FINAL)]


# ───────────────────────── Công nợ chi phí lô hàng (bao-CR-319 P5) ─────────────────────────
# Mỗi dòng chi phí là MỘT khoản nợ riêng trên `tab_payable`: source_type = ref_type =
# "import_cost", ref_id = id dòng chi phí. Đi chung bảng với goods/shipping để Yêu cầu
# thanh toán, màn Công nợ và tuổi nợ dùng lại y nguyên, không phải dựng luồng thứ hai.
IMPORT_COST_SOURCE = "import_cost"
# Đơn ở các trạng thái này mới sinh nợ cho dòng chi phí. Nháp / chờ duyệt là số ước tính,
# hủy / từ chối thì không còn gì phải trả (khớp REAL_PO_STATUSES của báo cáo).
IMPORT_COST_PAYABLE_STATUSES = frozenset({"approved", "partial", "received", "completed"})


def import_cost_payables_of(db: Session, po_id: int) -> dict[int, Payable]:
    """Khoản nợ chi phí của một đơn, khóa theo id dòng chi phí."""
    rows = db.query(Payable).filter(Payable.po_id == po_id,
                                    Payable.ref_type == IMPORT_COST_SOURCE).all()
    return {int(p.ref_id or 0): p for p in rows}


def _wants_cost_payable(row, po, active: bool, base_total: float, types) -> bool:
    """Dòng chi phí có thành khoản nợ không: đơn đã duyệt, số Quyết toán > 0, có NCC (mã hoặc tên), dòng đang ở
    Quyết toán và loại chi phí có sinh công nợ."""
    has_supplier = bool((row.supplier_code or "").strip() or (row.supplier_name or "").strip())
    return not (not active or base_total <= 0 or not has_supplier or not is_final_cost(row, po)
                or not cost_type_creates_payable(row.cost_type, types))


def _drop_unpaid_cost_payable(db: Session, old: Payable | None) -> None:
    """Gỡ khoản nợ của dòng không còn sinh nợ — khoản đã chi một đồng nào thì GIỮ (mất dấu vết là mất đối chiếu)."""
    if old and float(old.paid_amount or 0) <= 0:
        db.delete(old)
        db.flush()


def _upsert_cost_payable(db: Session, po: PurchaseOrder, row, base_total: float, suppliers: dict,
                         user_id: int) -> None:
    """Có rồi thì cập nhật, chưa có thì tạo khoản nợ của một dòng chi phí đã quyết toán."""
    # Cùng quy ước với nợ hàng: `amount` là gốc trước VAT đã quy đổi, `vat` là tiền thuế.
    base_before_vat = round(float(row.final_amount or 0) * cost_rate_of(row, CostStage.FINAL), 2)
    sup = suppliers.get((row.supplier_code or "").strip())
    pay_service.upsert(
        db, source_type=IMPORT_COST_SOURCE, ref_type=IMPORT_COST_SOURCE, ref_id=row.id,
        company_id=po.company_id, department_id=pay_service.debt_dept_of(po, db),
        supplier_code=(row.supplier_code or "").strip(),
        supplier_name=(row.supplier_name or "").strip() or (sup.name if sup else ""),
        po_id=po.id, po_code=po.code, invoice_no=(row.invoice_no or "").strip(),
        incur_date=(row.invoice_date or "").strip() or po.order_date or "",
        amount=base_before_vat, vat=round(base_total - base_before_vat, 2),
        due_days=pay_service.debt_days(sup.payment_terms if sup else ""),
        due_date=(row.payment_due_date or "").strip(), user_id=user_id)


def sync_import_cost_payables(db: Session, po: PurchaseOrder, user_id: int,
                              suppliers: dict | None = None) -> None:
    """Đồng bộ công nợ cho TOÀN BỘ dòng chi phí của đơn — idempotent, gọi sau mỗi lần lưu
    bảng chi phí và mỗi lần đơn đổi trạng thái.

    Đơn chưa duyệt / đã hủy: gỡ khoản nợ chưa chi đồng nào; khoản đã chi một phần thì giữ
    lại (tiền đã ra khỏi két, xóa dấu vết là mất đối chiếu — cùng cách đối xử với nợ hàng
    khi hủy đơn). Dòng chi phí 0 đồng hoặc chưa khai NCC thì không thành nợ.

    bao-CR-453: chỉ số QUYẾT TOÁN mới thành nợ — Dự toán / Tạm tính là số để chốt giá bán,
    chưa có hóa đơn nên chưa nợ ai cả. Đơn (hoặc riêng dòng) lên Quyết toán là nợ hiện ra
    ngay; mở lại thì nợ chưa chi bị gỡ, y như lúc bỏ NCC. Loại chi phí khai "không sinh
    công nợ" trong danh mục thì bỏ qua dù đã quyết toán.

    bao-CR-719: tách bước kiểm (`_wants_cost_payable`) → ghi (`_upsert_cost_payable` / `_drop_unpaid_cost_payable`).
    """
    rows = import_costs_of(db, po.id)
    if not rows:
        return
    existing = import_cost_payables_of(db, po.id)
    active = po.status in IMPORT_COST_PAYABLE_STATUSES
    suppliers = suppliers if suppliers is not None else _supplier_map(db)
    types = cost_type_map(db)
    for row in rows:
        base_total = float(cost_base_of(row, CostStage.FINAL) or 0)
        if _wants_cost_payable(row, po, active, base_total, types):
            _upsert_cost_payable(db, po, row, base_total, suppliers, user_id)
        else:
            _drop_unpaid_cost_payable(db, existing.get(row.id))


def block_complete_unpaid_import_costs(db: Session, po: PurchaseOrder) -> None:
    """Đơn NHẬP KHẨU chỉ được Hoàn thành khi MỌI khoản chi phí lô hàng đã trả đủ (09/09/2026,
    khách chốt mức chặt, chỉ áp cho đơn nhập khẩu).

    Tiến độ dòng hàng chỉ xét nợ HÀNG (`is_line_paid`), nên không có chốt này thì đơn nhập khẩu
    vẫn "Hoàn thành" trong khi cước tàu, thuế nộp ngân sách, phí lưu bãi chưa trả đồng nào — mà
    Hoàn thành xong là khóa sửa đơn, muốn khai thêm chi phí phải Mở lại. Dòng chi phí có tiền
    nhưng chưa thành công nợ (chưa chọn NCC) cũng chặn: khoản đó không có đường nào để trả.
    Đơn trong nước không đổi luật.

    bao-CR-453: chỉ xét số QUYẾT TOÁN (chốt `block_complete_not_final_costs` chạy trước nên
    tới đây mọi dòng đã ở Quyết toán); loại chi phí "không sinh công nợ" đứng ngoài.
    """
    if int(po.order_type or OrderType.DOMESTIC) != int(OrderType.IMPORT):
        return
    rows = import_costs_of(db, po.id)
    if not rows:
        return
    pays = import_cost_payables_of(db, po.id)
    types = cost_type_map(db)
    problems: list[str] = []
    for row in rows:
        if (float(cost_base_of(row, CostStage.FINAL) or 0) <= 0 or not is_final_cost(row, po)
                or not cost_type_creates_payable(row.cost_type, types)):
            continue
        label = (row.description or "").strip() or cost_type_name(row.cost_type, types) or "Chi phí"
        pay = pays.get(row.id)
        if not pay:
            problems.append(f"{label}: chưa thành công nợ (chưa chọn NCC hoặc chưa Lưu đơn)")
            continue
        # Tính từ total - paid (như YCTT) thay vì đọc cột `remaining` tính sẵn, để không lệ thuộc
        # vào việc cột đó đã được cập nhật hay chưa.
        remaining = round(float(pay.total or 0) - float(pay.paid_amount or 0), 2)
        if remaining > 0.01:
            who = (pay.supplier_name or pay.supplier_code or "").strip()
            problems.append(f"{label} ({who}): còn {remaining:,.0f} đ")
    if problems:
        raise HTTPException(
            400, f"Đơn nhập khẩu chỉ Hoàn thành khi đã trả đủ chi phí lô hàng. Còn {len(problems)} khoản: "
                 + "; ".join(problems) + ". Tạo và chi Yêu cầu thanh toán cho các khoản này trước.")


def block_delete_paid_import_cost(db: Session, row: POCost) -> None:
    """Dòng chi phí đã có tiền chi thì không xóa được — xóa là mất chỗ để đối chiếu số đã trả."""
    pay = db.query(Payable).filter(Payable.ref_type == IMPORT_COST_SOURCE,
                                   Payable.ref_id == row.id).first()
    if pay and float(pay.paid_amount or 0) > 0:
        raise HTTPException(
            400, f"Dòng chi phí '{row.description or row.supplier_name or row.id}' đã chi "
                 f"{float(pay.paid_amount):,.0f} đ, không xóa được. Sửa số tiền hoặc ghi chú thay vì xóa.")
    if pay:
        db.delete(pay)
        db.flush()


def paid_cost_ids(db: Session, po_id: int) -> set[int]:
    """Id những dòng chi phí đã có tiền chi — không được lùi giai đoạn, không được xóa."""
    return {cid for cid, p in import_cost_payables_of(db, po_id).items() if float(p.paid_amount or 0) > 0}


# ───────────────────────── Giai đoạn chi phí thu mua (bao-CR-453 §6) ─────────────────────────
COST_STAGE_MIN_REASON = 10
# Mã dấu vết ≤ 20 ký tự (cột `tab_audit_log.action` là String(20)); khai ở `core/action_catalog.py`.
COST_STAGE_ADVANCE_ACTIONS = {CostStage.PROVISIONAL: "cost_stage_prov", CostStage.FINAL: "cost_stage_final"}


def _fill_stage_from_previous(row, target: CostStage, po) -> bool:
    """Giai đoạn `target` của dòng chưa có số thì CHÉP số + tỷ giá của giai đoạn đã điền cao nhất
    bên dưới sang (Dự toán → Tạm tính → Quyết toán). Trả True nếu có chép.

    bao-CR-478: số 0 cũng tính là "chưa có số" — bản cũ (v1) gửi ô bỏ trống thành 0
    (`Number(x) || 0`), nên chỉ xét `None` thì luật chép không bao giờ chạy với dữ liệu nhập
    từ v1. Cùng luật với `has_estimate`."""
    if cost_amount_of(row, target):
        return False
    source = None
    for stage in sorted(CostStage, key=int, reverse=True):
        if stage < target and cost_amount_of(row, stage):
            source = stage
            break
    if source is None:
        return False
    prefix = COST_STAGE_PREFIX[target]
    setattr(row, f"{prefix}_amount", cost_amount_of(row, source))
    setattr(row, f"{prefix}_rate", cost_rate_of(row, source))
    return True


def _cost_label(row, types: dict | None = None) -> str:
    return (row.description or "").strip() or cost_type_name(row.cost_type, types)


def _stage_label(stage) -> str:
    return COST_STAGE_LABELS.get(stage_of(stage), "")


def _require_reason(reason: str) -> str:
    reason = (reason or "").strip()
    if len(reason) < COST_STAGE_MIN_REASON:
        raise HTTPException(400, f"Lý do mở lại phải từ {COST_STAGE_MIN_REASON} ký tự trở lên")
    return reason


def advance_cost_stage(db: Session, po: PurchaseOrder, target: int, user_id: int) -> None:
    """Đưa bộ chi phí của đơn LÊN giai đoạn `target` (2 Tạm tính / 3 Quyết toán).

    Đi từng bậc: mỗi bậc chép số của giai đoạn dưới vào cột còn trống (người dùng đã gõ số
    riêng cho giai đoạn đó thì giữ nguyên), ghi một dòng dấu vết, rồi đồng bộ công nợ ở cuối —
    lên Quyết toán là nợ hiện ra ngay. Dòng đã quyết toán riêng (`line_stage` cao hơn) không
    bị đụng. Không lùi được bằng hàm này: lùi đi `reopen_cost_stage`.
    """
    target = stage_of(target)
    current = stage_of(po.cost_stage)
    if target <= current:
        raise HTTPException(400, f"Chi phí đơn đang ở giai đoạn {_stage_label(current)}, "
                                 f"không chuyển sang {_stage_label(target)} được. Muốn lùi thì dùng Mở lại.")
    rows = import_costs_of(db, po.id)
    while current < target:
        nxt = CostStage(int(current) + 1)
        copied = 0
        for row in rows:
            if stage_of(row.line_stage) >= nxt:
                continue
            if _fill_stage_from_previous(row, nxt, po):
                copied += 1
            compute_cost_bases(row)
            row.updated_by = user_id
        po.cost_stage = int(nxt)
        po.updated_by = user_id
        db.flush()
        record(db, user_id, "purchase_order", po.id, COST_STAGE_ADVANCE_ACTIONS[nxt],
               f"Chốt {_stage_label(nxt)} chi phí thu mua: {len(rows)} dòng, {copied} dòng lấy số từ "
               f"{_stage_label(current)}", doc_code=po.code or "")
        current = nxt
    sync_import_cost_payables(db, po, user_id)
    db.commit()


def reopen_cost_stage(db: Session, po: PurchaseOrder, target: int, reason: str, user_id: int) -> None:
    """Mở lại bộ chi phí của đơn về giai đoạn `target` (1 Dự toán / 2 Tạm tính), cần lý do.

    Dòng ĐÃ CHI tiền giữ nguyên Quyết toán riêng dòng (`line_stage = 3`) — tiền đã ra khỏi
    két, không có gì để dự toán lại; dòng còn lại theo đơn, nợ chưa chi của chúng bị gỡ.
    Số của các giai đoạn cao hơn KHÔNG bị xóa: lên lại là thấy số cũ, chỉ sửa chỗ cần sửa.
    """
    reason = _require_reason(reason)
    target = stage_of(target)
    current = stage_of(po.cost_stage)
    if target >= current:
        raise HTTPException(400, f"Chi phí đơn đang ở giai đoạn {_stage_label(current)}, "
                                 f"chỉ mở lại về giai đoạn thấp hơn được")
    paid = paid_cost_ids(db, po.id)
    kept = 0
    for row in import_costs_of(db, po.id):
        if row.id in paid:
            row.line_stage = int(CostStage.FINAL)
            kept += 1
        elif stage_of(row.line_stage) > target:
            row.line_stage = int(target)
        row.updated_by = user_id
    po.cost_stage = int(target)
    po.updated_by = user_id
    db.flush()
    note = f"Mở lại chi phí thu mua từ {_stage_label(current)} về {_stage_label(target)}: {reason}"
    if kept:
        note += f" ({kept} dòng đã chi giữ Quyết toán)"
    record(db, user_id, "purchase_order", po.id, "cost_stage_reopen", note, doc_code=po.code or "")
    sync_import_cost_payables(db, po, user_id)
    db.commit()


def _get_cost_row(db: Session, po: PurchaseOrder, cost_id: int) -> POCost:
    row = db.query(POCost).filter(POCost.id == cost_id, POCost.po_id == po.id).first()
    if not row:
        raise HTTPException(404, "Không tìm thấy dòng chi phí trên đơn này")
    return row


def finalize_cost_line(db: Session, po: PurchaseOrder, cost_id: int, user_id: int) -> POCost:
    """Quyết toán RIÊNG một dòng khi hóa đơn của khoản đó về trước các khoản khác.

    Giữ nguyên cửa một-dòng cho bản giao diện đang chạy thật; ruột đi chung với cửa nhiều
    dòng của bao-CR-469 để hai đường không trôi ra khác nhau.
    """
    row = _get_cost_row(db, po, cost_id)
    if is_final_cost(row, po):
        raise HTTPException(400, "Dòng chi phí này đã ở Quyết toán")
    return finalize_cost_lines(db, po, [cost_id], user_id)[0]


# Câu dấu vết chỉ kể tên tối đa chừng này khoản rồi ghi "và n khoản nữa" — cột `message`
# của nhật ký có hạn, mà chốt cả bảng hai chục dòng là chuyện thường.
COST_FINAL_NAMES_IN_LOG = 5


def has_estimate(row) -> bool:
    """bao-CR-478 — dòng đã có số Dự toán (khác rỗng, khác 0) — điều kiện để được quyết toán."""
    return bool(cost_amount_of(row, CostStage.ESTIMATE))


def count_costs_missing_estimate(db: Session, po: PurchaseOrder, cost_ids: list[int] | None = None) -> int:
    """Trong các dòng được yêu cầu chốt (rỗng = cả đơn), bao nhiêu dòng CHƯA quyết toán vì thiếu
    Dự toán — `finalize_cost_lines` bỏ qua chúng, controller nói ra cho người dùng biết."""
    want = {int(cid) for cid in cost_ids} if cost_ids else None
    return sum(1 for r in import_costs_of(db, po.id)
               if (want is None or r.id in want) and not is_final_cost(r, po) and not has_estimate(r))


def _pick_cost_rows(rows: list[POCost], cost_ids: list[int] | None) -> list[POCost]:
    """Dòng được yêu cầu chốt: `cost_ids` rỗng = cả đơn; có id không thuộc đơn thì 404."""
    if not cost_ids:
        return rows
    want = {int(cid) for cid in cost_ids}
    chosen = [r for r in rows if r.id in want]
    missing = want - {r.id for r in chosen}
    if missing:
        raise HTTPException(404, "Không tìm thấy dòng chi phí trên đơn này")
    return chosen


def _raise_nothing_to_finalize(db: Session, no_estimate: list[POCost]) -> None:
    """Không còn dòng nào chốt được: nói rõ vì thiếu Dự toán (kể tên) hay vì đã chốt hết."""
    if no_estimate:
        types = cost_type_map(db)
        names = ", ".join(f"\"{_cost_label(r, types)}\"" for r in no_estimate[:COST_FINAL_NAMES_IN_LOG])
        raise HTTPException(400, f"Dòng chưa có Dự toán thì không quyết toán được: {names}. "
                                 f"Nhập số Dự toán trước rồi mới chốt.")
    raise HTTPException(400, "Không còn dòng chi phí nào để quyết toán")


def _finalize_row(row: POCost, po: PurchaseOrder, user_id: int) -> None:
    """Đưa một dòng lên Quyết toán riêng dòng, chép số còn trống từ giai đoạn dưới rồi tính lại số quy đổi."""
    # bao-CR-478 — chưa có Tạm tính LẪN Quyết toán thì chép Dự toán sang CẢ HAI cột; đã có
    # Tạm tính thì Quyết toán chép từ Tạm tính (`_fill_stage_from_previous` lấy giai đoạn đã
    # điền cao nhất bên dưới). Không bịa Tạm tính khi Quyết toán đã có số thật.
    if not cost_amount_of(row, CostStage.FINAL):
        _fill_stage_from_previous(row, CostStage.PROVISIONAL, po)
    _fill_stage_from_previous(row, CostStage.FINAL, po)
    row.line_stage = int(CostStage.FINAL)
    compute_cost_bases(row)
    row.updated_by = user_id


def _finalize_log_note(todo: list[POCost], types: dict) -> str:
    """Câu dấu vết của cả lượt chốt — kể tên tối đa `COST_FINAL_NAMES_IN_LOG` khoản."""
    names = [f"\"{_cost_label(r, types)}\"" for r in todo[:COST_FINAL_NAMES_IN_LOG]]
    them = len(todo) - len(names)
    note = f"Quyết toán {len(todo)} dòng chi phí: {', '.join(names)}"
    if them > 0:
        note += f" và {them} khoản nữa"
    return note


def finalize_cost_lines(db: Session, po: PurchaseOrder, cost_ids: list[int] | None,
                        user_id: int) -> list[POCost]:
    """bao-CR-469 — Quyết toán NHIỀU dòng chi phí một lượt.

    `cost_ids` rỗng/None = chốt HẾT các dòng chưa quyết toán của đơn. Dòng đã quyết toán rồi
    thì bỏ qua chứ không báo lỗi: người dùng tick cả bảng rồi bấm, việc của hệ thống là làm
    nốt phần còn lại chứ không bắt họ đi bỏ tick từng dòng đã xong.

    Đồng bộ công nợ MỘT lần ở cuối và ghi MỘT dòng dấu vết cho cả lượt — chốt hai chục dòng
    mà đẻ hai chục dòng nhật ký thì sổ đọc không ra việc gì đã xảy ra.

    bao-CR-719: tách bước kiểm (`_pick_cost_rows`, `_raise_nothing_to_finalize`) → ghi từng dòng (`_finalize_row`)
    → dấu vết (`_finalize_log_note`) + đồng bộ công nợ.
    """
    rows = import_costs_of(db, po.id)
    chosen = _pick_cost_rows(rows, cost_ids)
    todo = [r for r in chosen if not is_final_cost(r, po)]
    # bao-CR-478 — dòng KHÔNG có Dự toán thì không được quyết toán (đại ca chốt 24/09/2026).
    # BỎ QUA dòng đó và chốt phần còn lại, KHÔNG ném lỗi cả lượt: nút "Quyết toán tất cả" của v2
    # gửi đích danh mọi id chưa chốt, ném 400 thì chỉ một dòng trống Dự toán là cả nút chết.
    # Controller nói ra số dòng bị bỏ qua; chỉ khi không còn dòng nào chốt được mới báo lỗi.
    no_estimate = [r for r in todo if not has_estimate(r)]
    todo = [r for r in todo if has_estimate(r)]
    if not todo:
        _raise_nothing_to_finalize(db, no_estimate)
    for row in todo:
        _finalize_row(row, po, user_id)
    db.flush()
    types = cost_type_map(db)
    record(db, user_id, "purchase_order", po.id, "cost_line_final", _finalize_log_note(todo, types),
           doc_code=po.code or "")
    sync_import_cost_payables(db, po, user_id)
    db.commit()
    return todo


def reopen_cost_line(db: Session, po: PurchaseOrder, cost_id: int, reason: str, user_id: int) -> POCost:
    """Mở lại một dòng đã quyết toán riêng — về theo giai đoạn của đơn. Dòng đã chi không lùi."""
    reason = _require_reason(reason)
    row = _get_cost_row(db, po, cost_id)
    if stage_of(row.line_stage) <= stage_of(po.cost_stage):
        raise HTTPException(400, "Dòng này đang theo giai đoạn của đơn; muốn lùi thì mở lại cả đơn")
    if row.id in paid_cost_ids(db, po.id):
        raise HTTPException(400, f"Dòng chi phí \"{_cost_label(row)}\" đã có tiền chi, không mở lại được")
    row.line_stage = int(stage_of(po.cost_stage))
    row.updated_by = user_id
    db.flush()
    record(db, user_id, "purchase_order", po.id, "cost_line_reopen",
           f"Mở lại dòng chi phí \"{_cost_label(row)}\" về {_stage_label(po.cost_stage)}: {reason}",
           doc_code=po.code or "")
    sync_import_cost_payables(db, po, user_id)
    db.commit()
    return row


def block_complete_not_final_costs(db: Session, po: PurchaseOrder) -> None:
    """Đơn có dòng chi phí thì phải ở QUYẾT TOÁN mới Hoàn thành được — Hoàn thành là khóa sửa
    đơn, mà chi phí chưa quyết toán nghĩa là còn hóa đơn chưa về. Đơn KHÔNG có dòng chi phí
    nào thì tự đặt giai đoạn = Quyết toán để báo cáo đọc đơn đó là đã chốt."""
    rows = import_costs_of(db, po.id)
    if not rows:
        if stage_of(po.cost_stage) != CostStage.FINAL:
            po.cost_stage = int(CostStage.FINAL)
            db.flush()
        return
    pending = [r for r in rows if not is_final_cost(r, po)]
    if pending:
        raise HTTPException(
            400, f"Chốt Quyết toán chi phí thu mua trước khi Hoàn thành đơn: còn {len(pending)} dòng "
                 f"đang ở {_stage_label(effective_stage_of(pending[0], po))}.")
