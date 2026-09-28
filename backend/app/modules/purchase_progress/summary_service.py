"""Bản THEO KỲ của màn Tiến độ mua hàng (P03, `GET /api/purchase-progress/summary` khi có
`preset`) — hợp đồng chuẩn `report_aggregate.build_report`. Tách khỏi `controller.py` để giữ
tệp đó dưới 200 dòng; dùng lại `_build_query` của `controller.py` nên số liệu luôn khớp bảng.

M3 (review 28/09/2026, đảo quyết định Q3.1 cũ): chỉ số GIAO (lần giao/trễ/đúng hạn/tỷ lệ đúng
hạn) lọc/gộp theo NGÀY NHẬN của từng lần giao (`PODelivery.received_date`); chỉ số DÒNG (số
dòng, tình trạng nhận) lọc/gộp theo NGÀY ĐẶT của đơn (`PurchaseOrder.order_date`) — hai cách
đếm khác cột ngày nên GỘP hai nguồn vào MỘT danh sách hàng có kiểu (`Row.kind`), cùng khuôn
`procurement_summary_rows.py`. `fetch_rows` chạy HAI truy vấn trên CÙNG một câu truy vấn nền đã
lọc phạm vi/điều kiện (CHƯA lọc theo kỳ) — route chỉ cần truyền `base_query` + khoảng ngày.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec
from app.core.report_period import range_filter, to_local_date
from app.core.status_codes import PO_PROGRESS_STATUS
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder

#  Cột THẬT SỰ cần cho báo cáo tiến độ — `_build_query` (controller.py) trả full entity vì màn
#  danh sách/xuất Excel cần đủ cột, nhưng `/summary` (P05, review hiệu năng 28/09/2026) chỉ đọc
#  từng này; `with_entities` ngay trước khi gọi `.all()` khỏi phải nạp/hydrate ~80 cột của 3
#  bảng (PurchaseOrder/POItem/PODelivery) mỗi lần `build_report` gọi `fetch_rows` (2 lần/lượt xem).
_ROW_COLUMNS = (
    PurchaseOrder.order_date.label("order_date"), PurchaseOrder.department.label("department"),
    PurchaseOrder.supplier_name.label("supplier_name"), PurchaseOrder.supplier_code.label("supplier_code"),
    POItem.id.label("item_id"), POItem.progress_status.label("progress_status"),
    POItem.qty_order.label("qty_order"), PODelivery.received_qty.label("received_qty"),
    PODelivery.received_date.label("received_date"), PODelivery.diff_promise.label("diff_promise"),
    PODelivery.diff_regulated.label("diff_regulated"),
)

NOTE = ("Chỉ số giao (lần giao/trễ/đúng hạn) tính theo NGÀY NHẬN của từng lần giao; số dòng "
       "(và tình trạng nhận) tính theo NGÀY ĐẶT của đơn — hai cách đếm khác cột ngày nên tổng "
       "'Lần giao' của một kỳ có thể gồm cả lần giao của đơn đặt ở kỳ khác.")


@dataclass(frozen=True)
class Row:
    """Một hàng GỘP cho `build_report`. `kind="line"`: 1 hàng/DÒNG ĐMH, lọc theo NGÀY ĐẶT —
    `late` không dùng tới (luôn `False`). `kind="delivery"`: 1 hàng/LẦN GIAO đã nhận
    (`received_qty>0`), lọc theo NGÀY NHẬN — `item_id`/`recv_state` không dùng tới."""

    kind: str
    date_str: str
    department: str = ""
    supplier: str = ""
    progress_status: str = ""
    item_id: int = 0
    recv_state: str = ""    # chỉ "line": "" | "unreceived" | "under" | "full"
    late: bool = False      # chỉ "delivery"


def _recv_states(line_raw) -> dict[int, str]:
    """`line_raw`: list[hàng cột phẳng — xem `_ROW_COLUMNS`] lọc theo NGÀY ĐẶT (CHƯA lọc theo
    ngày nhận) -> {item_id: recv_state} — tổng đã nhận của MỌI lần giao (trạng thái HIỆN TẠI,
    không phải "trong kỳ"), cùng luật cũ trước M3."""
    received: dict[int, float] = {}
    for r in line_raw:
        received[r.item_id] = received.get(r.item_id, 0.0) + float(r.received_qty or 0)
    out: dict[int, str] = {}
    for r in line_raw:
        if r.item_id in out:
            continue
        qty = float(r.qty_order or 0)
        if qty <= 0:
            out[r.item_id] = ""
            continue
        got = received.get(r.item_id, 0.0)
        out[r.item_id] = "unreceived" if got <= 0 else ("under" if got < qty else "full")
    return out


def build_rows(line_raw, delivery_raw) -> list[Row]:
    """`line_raw`: hàng cột phẳng lọc theo NGÀY ĐẶT — khử trùng theo `item_id` (outer join có
    thể nhân bản item theo số lần giao). `delivery_raw`: hàng cột phẳng lọc theo NGÀY NHẬN +
    `received_qty>0` — 1 hàng/lần giao. Cả hai đọc CÙNG cột phẳng của `_ROW_COLUMNS`."""
    states = _recv_states(line_raw)
    seen: set[int] = set()
    out: list[Row] = []
    for r in line_raw:
        if r.item_id in seen:
            continue
        seen.add(r.item_id)
        out.append(Row(kind="line", date_str=r.order_date, department=r.department or "",
                       supplier=r.supplier_name or r.supplier_code or "",
                       progress_status=r.progress_status or "not_ordered",
                       item_id=r.item_id, recv_state=states.get(r.item_id, "")))
    for r in delivery_raw:
        late = (r.diff_promise or 0) < 0 or (r.diff_regulated or 0) < 0
        out.append(Row(kind="delivery", date_str=r.received_date, department=r.department or "",
                       supplier=r.supplier_name or r.supplier_code or "",
                       progress_status=r.progress_status or "not_ordered", late=late))
    return out


def fetch_rows(base_query, d_from, d_to) -> list[Row]:
    """Chạy HAI truy vấn trên CÙNG `base_query` (đã lọc phạm vi/điều kiện, CHƯA lọc theo kỳ):
    dòng hàng lọc theo NGÀY ĐẶT, lần giao lọc theo NGÀY NHẬN (M3) — rồi gộp thành `Row`.

    P05 (review hiệu năng 28/09/2026): `with_entities(*_ROW_COLUMNS)` TRƯỚC khi lọc/`.all()` —
    `base_query` gốc trả full `(PurchaseOrder, POItem, PODelivery)` (cần cho danh sách/Excel),
    còn ở đây chỉ đọc 11 cột nên khỏi hydrate cả ba entity đầy đủ 2 lần mỗi lượt xem báo cáo."""
    q = base_query.with_entities(*_ROW_COLUMNS)
    line_raw = q.filter(range_filter(PurchaseOrder.order_date, "str", d_from, d_to)).all()
    delivery_raw = q.filter(PODelivery.received_qty > 0,
                            range_filter(PODelivery.received_date, "str", d_from, d_to)).all()
    return build_rows(line_raw, delivery_raw)


def build_spec(show_supplier: bool) -> ReportSpec:
    metrics = [
        MetricSpec("lines", "Số dòng", kind="int",
                  distinct_of=lambda r: r.item_id if r.kind == "line" else None),
        MetricSpec("deliveries", "Lần giao", kind="int",
                  value_of=lambda r: 1 if r.kind == "delivery" else 0),
        MetricSpec("late_deliveries", "Lần giao trễ", kind="int", good="down",
                  value_of=lambda r: 1 if r.kind == "delivery" and r.late else 0),
        MetricSpec("on_time_deliveries", "Lần giao đúng hạn", kind="int",
                  value_of=lambda r: 1 if r.kind == "delivery" and not r.late else 0),
        MetricSpec("unreceived_items", "Dòng chưa nhận", kind="int",
                  distinct_of=lambda r: r.item_id if r.kind == "line" and r.recv_state == "unreceived" else None),
        MetricSpec("under_items", "Dòng nhận thiếu", kind="int",
                  distinct_of=lambda r: r.item_id if r.kind == "line" and r.recv_state == "under" else None),
        MetricSpec("full_items", "Dòng nhận đủ", kind="int",
                  distinct_of=lambda r: r.item_id if r.kind == "line" and r.recv_state == "full" else None),
    ]
    derived = [DerivedSpec("on_time_rate", "Giao đúng hạn", num="on_time_deliveries",
                          den="deliveries", good="up")]
    dimensions = {
        "department": DimensionSpec("department", "Bộ phận",
                                    key_of=lambda r: [(r.department, r.department)] if r.department else []),
        "progress_status": DimensionSpec(
            "progress_status", "Tiến độ dòng",
            key_of=lambda r: [(r.progress_status, PO_PROGRESS_STATUS.label_of(r.progress_status, r.progress_status))]
            if r.progress_status else []),
    }
    if show_supplier:
        dimensions["supplier"] = DimensionSpec(
            "supplier", "Nhà cung cấp",
            key_of=lambda r: [(r.supplier, r.supplier)] if r.supplier else [])
    #  `date_of` đọc `date_str` chung — "line" mang ngày ĐẶT, "delivery" mang ngày NHẬN (M3),
    #  mỗi `MetricSpec` ở trên đã tự lọc đúng `kind` của mình nên dùng chung một cột ngày ảo
    #  không lẫn ý nghĩa.
    return ReportSpec(date_of=lambda r: to_local_date(r.date_str), metrics=metrics, derived=derived,
                      dimensions=dimensions, breakdowns=dimensions)
