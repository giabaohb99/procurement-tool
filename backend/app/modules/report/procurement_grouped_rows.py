"""Hàng ĐẶT HÀNG (`kind="po"`) của Báo cáo mua hàng — bản GOM Ở SQL, thay
`procurement_summary_rows.po_rows` (P06, review hiệu năng 28/09/2026).

Giữ NGUYÊN độ hạt DÒNG (1 hàng = 1 POItem, y hệt bản cũ) cho hai chỉ số KHÔNG gộp an toàn được:

- `order_value`: `report_service.order_amount_of` cộng bằng PHÉP TOÁN FLOAT của Python (mỗi số
  hạng ép `float()` rồi nhân). Cộng ở SQL sẽ tính bằng DECIMAL CHÍNH XÁC rồi mới đổi sang float
  MỘT LẦN ở cuối — hai đường cho ra hai bit cuối khác nhau (không kết hợp/giao hoán tuyệt đối
  giữa cộng dồn theo thứ tự khác nhau), lộ ra thành JSON không khớp `report_bench.py` (so khớp
  `!=` tuyệt đối, không làm tròn). Vì vậy công thức vẫn tính Ở PYTHON, y hệt bản cũ.
- `po_count`: đếm PHÂN BIỆT `po_id` (`distinct_of` của `report_aggregate`) — khung tính đúng
  theo TỪNG NHÓM chỉ khi hàng còn giữ `po_id` thật (một ĐMH nhiều nhóm hàng vẫn phải đếm ở MỌI
  nhóm hàng đó, xem `MetricSpec.distinct_of` không cộng dồn được qua GROUP BY thô).

Phần GOM ĐƯỢC AN TOÀN Ở SQL (số nguyên, cộng không lệch bit): số LẦN GIAO đã nhận / đúng hạn
của từng POItem — trước đây nạp TOÀN BỘ `PODelivery` liên quan rồi đếm bằng 2 dict Python
(`done`/`ontime` trong `po_rows` cũ). Đây là phần NẶNG thật sự (một PO có thể có hàng chục lần
giao), nên gộp bằng SQL `GROUP BY po_item_id` (subquery `_delivery_agg`) cắt bỏ phần lớn chi phí
ORM-materialize + vòng lặp Python, mà KHÔNG đụng tới công thức tiền.

`ORDER BY POItem.id` giữ ĐÚNG thứ tự hàng của bản cũ (`db.query(POItem)...all()` không có
ORDER BY, nhưng MySQL/InnoDB quét theo khóa chính khi không ép sắp xếp khác) — cần giữ vì
`sum()` cộng float KHÔNG kết hợp được ((a+b)+c có thể khác a+(b+c) ở bit cuối), nên đổi thứ tự
hàng có thể đổi bit cuối của TỔNG dù tập giá trị y hệt.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_order.service import normalize_rate

from .controller import REAL_PO_STATUSES
from .procurement_summary_rows import Row, _ranges_cond


def _delivery_agg(db: Session):
    """Số LẦN GIAO đã nhận + số lần ĐÚNG HẠN của từng POItem — GROUP BY po_item_id.

    Số nguyên, cộng ở SQL hay Python cho kết quả giống hệt nhau (không có rủi ro sai số float).
    Đúng hạn = KHÔNG (`diff_promise` HOẶC `diff_regulated` âm) — cùng luật `po_rows` cũ."""
    on_time = and_(func.coalesce(PODelivery.diff_promise, 0) >= 0,
                   func.coalesce(PODelivery.diff_regulated, 0) >= 0)
    return (db.query(PODelivery.po_item_id.label("po_item_id"),
                     func.count().label("done"),
                     func.sum(case((on_time, 1), else_=0)).label("ontime"))
            .filter(PODelivery.received_qty > 0)
            .group_by(PODelivery.po_item_id)
            .subquery())


def grouped_po_rows(db: Session, company_id: int | None, ranges: list[tuple[date, date]]) -> list[Row]:
    """Bản GOM Ở SQL của `procurement_summary_rows.po_rows` — MỘT lượt JOIN (POItem × PO ×
    gộp giao hàng) thay 3 truy vấn ORM rời + 2 dict Python nối tay. Xem docstring đầu tệp về
    lý do GIỮ độ hạt dòng cho `order_value`/`po_count`."""
    if not ranges:
        return []
    dlv = _delivery_agg(db)
    q = (db.query(PurchaseOrder.order_date, PurchaseOrder.company_id, PurchaseOrder.department,
                 POItem.item_group, PurchaseOrder.supplier_name, PurchaseOrder.supplier_code,
                 PurchaseOrder.nspt, PurchaseOrder.id, POItem.qty_order, POItem.price, POItem.vat,
                 POItem.exchange_rate, dlv.c.done, dlv.c.ontime)
         .select_from(POItem)
         .join(PurchaseOrder, POItem.po_id == PurchaseOrder.id)
         .outerjoin(dlv, dlv.c.po_item_id == POItem.id)
         .filter(PurchaseOrder.status.in_(REAL_PO_STATUSES), _ranges_cond(PurchaseOrder.order_date, ranges)))
    if company_id:
        q = q.filter(PurchaseOrder.company_id == company_id)
    q = q.order_by(POItem.id)

    out: list[Row] = []
    for (order_date, comp_id, dept, item_group, sup_name, sup_code, nspt, po_id, qty, price, vat,
         rate, done, ontime) in q.all():
        #  Y HỆT `report_service.order_amount_of`: SL đặt × đơn giá × (1+VAT%) × tỷ giá quy đổi,
        #  cộng bằng float Python (xem docstring đầu tệp vì sao KHÔNG cộng ở SQL).
        order_value = (float(qty or 0) * float(price or 0) * (1 + float(vat or 0) / 100)
                      * normalize_rate(rate))
        out.append(Row(kind="po", date_str=order_date, company_id=comp_id, department=dept or "",
                       item_group=item_group or "", supplier=sup_name or sup_code or "",
                       nspt=nspt or "", order_value=order_value, po_id=po_id,
                       deliveries_done=done or 0, on_time_deliveries=ontime or 0))
    return out
