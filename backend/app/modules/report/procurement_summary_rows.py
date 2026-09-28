"""Hàng dữ liệu GỘP cho Báo cáo mua hàng kiểu Haravan (P03) — tách khỏi
`procurement_summary_service.py` để mỗi tệp giữ dưới 200 dòng.

`_Row.kind` phân biệt hàng đến từ ĐMH (`"po"`, lọc theo `PurchaseOrder.order_date`) hay từ
công nợ (`"payable"`, lọc theo `Payable.incur_date`) — xem docstring của
`procurement_summary_service.py` để hiểu vì sao phải gộp hai nguồn có hai cột ngày khác nhau.

Review 28/09/2026 (Finding #3): trước đây hàng "payable" KHÔNG mang phòng ban/nhóm hàng/NSPT
nào cả (`department=""` mặc định) nên "Xem theo" luôn gộp hết chi phí vào "(Chưa gắn)". Nay
`payable_rows` tra `Payable.department_id` (Phòng XỬ LÝ, bao-CR-484) qua bảng Phòng ban, lùi về
phòng của ĐMH liên quan nếu rỗng; NSPT/nhóm hàng cũng suy từ ĐMH đó — ĐMH có NHIỀU nhóm hàng
thì CHIA chi phí theo TỶ TRỌNG giá trị đặt của từng nhóm (không chọn đại một nhóm).

Review hiệu năng (28/09/2026, P05): `payable_rows` nhận LIST khoảng ngày thay vì một cặp —
`build_report` gọi `fetch()` tối đa 2 lần (kỳ này + kỳ so sánh) nên trước đây mỗi lần gọi lại
truy vấn Payable/POItem từ đầu; nay gộp WHERE bằng `OR` các khoảng, truy vấn MỘT LƯỢT rồi
`compute_procurement_summary` tự chia lại theo từng kỳ bằng `row_in_range` (thuần Python, không
hỏi DB lại). Các truy vấn cũng chỉ nạp CỘT CẦN DÙNG (`load_only`) thay vì cả entity.

P06 (review hiệu năng 28/09/2026): hàng "po" (trước ở hàm `po_rows` của chính tệp này) đã dời
sang `procurement_grouped_rows.grouped_po_rows` (GOM số lần giao ở SQL GROUP BY) — xem docstring
của tệp đó. `Row`/`row_in_range`/`_ranges_cond` ở đây vẫn dùng chung cho cả hai nguồn."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, load_only

from app.core.report_period import range_filter
from app.modules.payable.model import Payable
from app.modules.payable.service import ST_PAID
from app.modules.purchase_order.model import POItem, PurchaseOrder

from . import service as report_service
from .controller import REAL_PO_STATUSES


@dataclass(frozen=True)
class Row:
    """Một hàng GỘP cho `build_report`. `kind` quyết định `MetricSpec`/`DimensionSpec` nào
    đọc nó — hàng "payable" luôn có `order_value`/`po_id`/`deliveries_done`... = 0, hàng "po"
    luôn có `spend` = 0."""

    kind: str  # "po" (1 dòng ĐMH — POItem) | "payable" (1 phần công nợ, có thể CHIA từ 1 khoản)
    date_str: str
    company_id: int = 0
    department: str = ""
    item_group: str = ""
    supplier: str = ""
    nspt: str = ""
    order_value: float = 0.0
    po_id: int = 0
    deliveries_done: int = 0
    on_time_deliveries: int = 0
    spend: float = 0.0


def valid_company_id(raw) -> int | None:
    """`company_id` từ query string — rỗng -> None (không lọc); không phải số nguyên -> 422
    (L3: trước đây `int("abc")` ném `ValueError` thô, lộ 500 thay vì báo lỗi đầu vào)."""
    if raw in (None, ""):
        return None
    s = str(raw).strip()
    if not s.isdigit():
        raise HTTPException(422, "company_id phải là số nguyên")
    return int(s)


def row_in_range(date_str: str, d_from: date, d_to: date) -> bool:
    """Cùng luật đóng-mở với `report_period.range_filter(kind='str')` — dùng để CHIA LẠI một
    tập hàng đã gộp NHIỀU khoảng ngày (xem `po_rows`/`payable_rows`) theo TỪNG kỳ trong Python,
    thay vì hỏi DB lại lần hai với khoảng ngày khác."""
    upper = (d_to + timedelta(days=1)).isoformat()
    return d_from.isoformat() <= (date_str or "") < upper


def _ranges_cond(col, ranges: list[tuple[date, date]]):
    conds = [range_filter(col, "str", d_from, d_to) for d_from, d_to in ranges]
    return conds[0] if len(conds) == 1 else or_(*conds)


def real_po_ids(db: Session, po_ids: set[int]) -> set[int]:
    """Lọc còn lại các id ĐMH THẬT (đã duyệt trở đi) trong tập id truyền vào."""
    if not po_ids:
        return set()
    return {pid for pid, st in db.query(PurchaseOrder.id, PurchaseOrder.status)
            .filter(PurchaseOrder.id.in_(po_ids)).all() if st in REAL_PO_STATUSES}


#  Cột PurchaseOrder/POItem THẬT SỰ cần cho `_resolve_po_context` — `load_only` khỏi kéo cả
#  ~35 cột (giá trần nhập khẩu, ghi chú, tỷ giá gốc…) mỗi lần build_report gọi fetch().
_PO_CONTEXT_COLS = (PurchaseOrder.id, PurchaseOrder.nspt, PurchaseOrder.department)
_POITEM_COLS = (POItem.id, POItem.po_id, POItem.item_group, POItem.qty_order, POItem.price,
                POItem.vat, POItem.exchange_rate)


def _resolve_po_context(db: Session, po_ids: set[int]):
    """PO liên quan (id -> đối tượng) + tỷ trọng giá trị đặt theo nhóm hàng của từng PO
    (`{po_id: {item_group: order_value}}`) — dùng để suy NSPT/nhóm hàng cho khoản công nợ
    và chia chi phí theo tỷ trọng khi một ĐMH có NHIỀU nhóm hàng (Finding #3)."""
    if not po_ids:
        return {}, {}
    po_by = {po.id: po for po in db.query(PurchaseOrder).options(load_only(*_PO_CONTEXT_COLS))
             .filter(PurchaseOrder.id.in_(po_ids)).all()}
    weight_by_po: dict[int, dict[str, float]] = {}
    for it in db.query(POItem).options(load_only(*_POITEM_COLS)).filter(POItem.po_id.in_(po_ids)).all():
        g = weight_by_po.setdefault(it.po_id, {})
        grp = it.item_group or ""
        g[grp] = g.get(grp, 0.0) + report_service.order_amount_of(it)
    return po_by, weight_by_po


def _split_by_weight(total: float, weights: dict[str, float]) -> list[tuple[str, float]]:
    """Chia `total` theo tỷ trọng `weights` (nhóm hàng -> giá trị đặt) — dòng CUỐI nhận phần dư
    để tổng các phần luôn khớp CHÍNH XÁC `total` (tránh lệch vài đồng do làm tròn từng phần)."""
    share_sum = sum(weights.values())
    if share_sum <= 0:
        return [("", total)]
    items = list(weights.items())
    out, allocated = [], 0.0
    for i, (grp, amt) in enumerate(items):
        if i == len(items) - 1:
            out.append((grp, round(total - allocated, 2)))
        else:
            share = round(total * amt / share_sum, 2)
            allocated += share
            out.append((grp, share))
    return out


def payable_rows(db: Session, company_id: int | None, ranges: list[tuple[date, date]],
                 dept_name: dict[int, str]) -> list[Row]:
    """Hàng CHI PHÍ: lọc theo `incur_date` — HỢP của mọi khoảng trong `ranges` (xem `po_rows`).
    Loại khoản nợ gắn với ĐMH KHÔNG THẬT (nháp/chờ duyệt/hủy/từ chối) — cùng luật
    `/api/reports/procurement`. Một khoản nợ có thể sinh NHIỀU hàng (một hàng mỗi nhóm hàng của
    ĐMH liên quan) khi ĐMH có nhiều nhóm hàng."""
    if not ranges:
        return []
    payq = (db.query(Payable)
            .options(load_only(Payable.id, Payable.incur_date, Payable.company_id, Payable.po_id,
                               Payable.department_id, Payable.supplier_name, Payable.supplier_code,
                               Payable.total))
            .filter(_ranges_cond(Payable.incur_date, ranges)))
    if company_id:
        payq = payq.filter(Payable.company_id == company_id)
    pays = payq.all()
    linked = {p.po_id for p in pays if p.po_id}
    ok = real_po_ids(db, linked)
    pays = [p for p in pays if not p.po_id or p.po_id in ok]
    po_by, weight_by_po = _resolve_po_context(db, ok)

    out = []
    for p in pays:
        po = po_by.get(p.po_id)
        #  Phòng: ưu tiên Phòng XỬ LÝ của khoản nợ (`department_id`, bao-CR-484), lùi về phòng
        #  của ĐMH liên quan (bản chụp tên) khi rỗng — "0 = thu mua chung/không có đơn" không
        #  tự suy ra được tên, còn ĐMH thì luôn có phòng yêu cầu.
        dept = dept_name.get(p.department_id or 0, "") or (po.department if po else "") or ""
        nspt = (po.nspt or "") if po else ""
        supplier = p.supplier_name or p.supplier_code or ""
        total = float(p.total or 0)
        weights = weight_by_po.get(p.po_id) if po else None
        for item_group, share in (_split_by_weight(total, weights) if weights else [("", total)]):
            out.append(Row(kind="payable", date_str=p.incur_date, company_id=p.company_id,
                           department=dept, item_group=item_group, supplier=supplier,
                           nspt=nspt, spend=share))
    return out


def debt_snapshot(db: Session, company_id: int | None):
    """`snapshot(as_of)` của `build_report` — công nợ còn lại/quá hạn TÍNH TỚI `as_of`."""

    def snap(as_of: date) -> dict:
        cutoff = as_of.isoformat()
        q = (db.query(Payable)
             .options(load_only(Payable.id, Payable.incur_date, Payable.company_id, Payable.po_id,
                                Payable.remaining, Payable.status, Payable.due_date))
             .filter(Payable.incur_date != "", Payable.incur_date <= cutoff))
        if company_id:
            q = q.filter(Payable.company_id == company_id)
        pays = q.all()
        linked = {p.po_id for p in pays if p.po_id}
        ok = real_po_ids(db, linked)
        pays = [p for p in pays if not p.po_id or p.po_id in ok]
        remaining = sum(float(p.remaining or 0) for p in pays if p.status != ST_PAID)
        overdue = sum(float(p.remaining or 0) for p in pays
                     if p.status != ST_PAID and p.due_date and p.due_date < cutoff)
        return {"debt_remaining": round(remaining, 2), "debt_overdue": round(overdue, 2)}

    return snap
