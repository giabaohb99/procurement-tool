"""ĐMH — lưu các lần giao, gỡ side-effect khi xóa lần giao, tính lại phiếu nhập kho / tồn kho / công nợ (bao-CR-715
tách từ service.py).
"""
from datetime import timedelta

from sqlalchemy.orm import Session

from app.modules.catalog import lead_time
from app.modules.goods_receipt import service as gr_service
from app.modules.inventory import service as inv_service
from app.modules.payable import service as pay_service

from .model import PODelivery, POItem, PurchaseOrder
from .base_service import (DELIV_DEFECT, DELIV_PENDING, DELIV_RECEIVED, DELIV_SHORT, LINE_FULL, LINE_NOT_DELIVERED,
                           LINE_PARTIAL, _days, _pdate, _supplier_map, deliveries_of, items_of, rate_of)


def _save_deliveries(db: Session, po: PurchaseOrder, item: POItem, delivs, user_id: int,
                     std_map: dict[str, int] | None = None):
    existing = {d.id: d for d in deliveries_of(db, item.id)}
    if std_map is None:
        std_map = lead_time.std_days_map(db)
    # Ngày QĐ có hàng của dòng = Ngày đặt hàng + số ngày QĐ của phân loại
    qd_date = lead_time.regulated_date(std_map, item.item_group, (po.order_date or "").strip())
    keep = set()
    for raw in delivs:
        data = raw.model_dump()
        inv_no = (data.get("invoice_no") or "").strip() or (item.invoice_no or "").strip()
        inv_date = (data.get("invoice_date") or "").strip() or (item.invoice_date or "").strip()
        # bao-CR-367: KHÔNG tự gán ngày hôm nay khi có số hóa đơn mà trống ngày. Câu đó biến
        # "thiếu dữ liệu" thành "dữ liệu sai" — trống thì người dùng còn nhìn ra mà điền, chứ
        # điền bừa ngày hôm nay thì không ai biết đó là ngày bịa. Ghép với lỗi giao diện quên
        # gửi `invoice_date` (PurchaseOrderDetail.tsx), nó đã dập ngày thật của 90/96 dòng
        # giao hàng trên hệ thật. Đừng khôi phục lại.
        if inv_no:
            data["invoice_no"] = inv_no
        if inv_date:
            data["invoice_date"] = inv_date
        did = data.pop("id", None)
        if did and did in existing:
            d = existing[did]
            for k, v in data.items():
                setattr(d, k, v)
            d.updated_by = user_id
        else:
            # Cam kết giao mặc định = NGÀY QĐ CÓ HÀNG theo phân loại (Ngày đặt hàng + số ngày QĐ).
            # CHỈ điền lúc TẠO lần giao (kể cả lần giao sinh từ nhập khẩu/copy đơn, không riêng nút
            # "Thêm lần giao"); lần giao đã có thì tôn trọng giá trị người dùng nhập, xóa trắng vẫn trắng.
            if not (data.get("promised_date") or "").strip():
                data["promised_date"] = qd_date
            d = PODelivery(po_id=po.id, po_item_id=item.id, created_by=user_id, updated_by=user_id, **data)
            db.add(d)
        db.flush()
        keep.add(d.id)
    for old_id, d in existing.items():
        if old_id not in keep:
            _cleanup_delivery(db, old_id)
            db.delete(d)
    db.flush()


def _cleanup_delivery(db: Session, delivery_id: int):
    """Gỡ side-effect của 1 lần giao (khi xóa dòng giao)."""
    gr_service.remove_for_delivery(db, delivery_id)
    inv_service.remove_delivery(db, delivery_id)
    pay_service.remove(db, "goods", delivery_id)
    pay_service.remove(db, "shipping", delivery_id)


def recompute_effects(db: Session, po: PurchaseOrder, user_id: int):
    """Tính lại tổng dòng + sinh/cập nhật phiếu nhập kho ngầm, tồn kho, công nợ 2 luồng."""
    suppliers = _supplier_map(db)
    goods_sup = suppliers.get(po.supplier_code)
    goods_days = pay_service.debt_days(po.payment_terms or (goods_sup.payment_terms if goods_sup else ""))

    std_map = lead_time.std_days_map(db)   # số ngày QĐ theo phân loại (mốc dài nhất, thiếu -> 15)

    total_order = total_received = 0.0
    for it in items_of(db, po.id):
        qty_order = float(it.qty_order or 0)
        vat = float(it.vat or 0)
        # bao-CR-319: đơn giá ghi theo đồng tiền của dòng. Công nợ, tồn kho và mọi báo cáo
        # đều không có khái niệm loại tiền nên phải nhận GIÁ ĐÃ QUY ĐỔI. Đơn VNĐ có tỷ giá 1
        # nên số liệu cũ không đổi một đồng nào.
        rate = rate_of(it)
        base_price = float(it.price or 0) * rate

        recv_sum = 0.0
        for d in deliveries_of(db, it.id):
            recv = float(d.received_qty or 0)
            recv_sum += recv
            wh = d.warehouse_code or it.warehouse_code
            if recv > 0:
                # Phiếu nhập kho ngầm + tồn kho
                gr_service.upsert_for_delivery(
                    db, po_id=po.id, po_code=po.code, delivery_id=d.id, company_id=po.company_id,
                    warehouse_code=wh, product_code=it.product_code, product_name=it.product_name,
                    unit=it.unit, qty_received=recv, received_date=d.received_date,
                    qc_result=d.qc_result, user_id=user_id)
                inv_service.apply_delivery(
                    db, delivery_id=d.id, company_id=po.company_id, warehouse_code=wh,
                    product_code=it.product_code, product_name=it.product_name, unit=it.unit,
                    qty=recv, price=base_price, user_id=user_id)
                # Công nợ hàng (NCC bán) — số HĐ lấy theo sản phẩm (po_item)
                amt = recv * base_price
                pay_service.upsert(
                    db, source_type="goods", ref_id=d.id, company_id=po.company_id,
                    department_id=pay_service.debt_dept_of(po, db),
                    supplier_code=po.supplier_code, supplier_name=po.supplier_name,
                    po_id=po.id, po_code=po.code, invoice_no=(d.invoice_no or it.invoice_no or "").strip(),
                    incur_date=d.received_date or po.order_date, amount=amt, vat=amt * vat / 100,
                    due_days=goods_days, user_id=user_id)
                # Công nợ vận chuyển (carrier riêng) — chỉ khi có carrier + cước > 0
                ship_amt = float(d.shipping_amount or 0)
                if d.carrier_code and ship_amt > 0:
                    carrier = suppliers.get(d.carrier_code)
                    c_days = pay_service.debt_days(carrier.payment_terms if carrier else "")
                    # Vận chuyển không có hóa đơn riêng → số HĐ tạm = Mã MISA + Mã SP
                    ship_inv = f"{po.misa_code}-{it.product_code}".strip("-")
                    pay_service.upsert(
                        db, source_type="shipping", ref_id=d.id, company_id=po.company_id,
                        department_id=pay_service.debt_dept_of(po, db),
                        supplier_code=d.carrier_code,
                        supplier_name=d.carrier_name or (carrier.name if carrier else ""),
                        po_id=po.id, po_code=po.code, invoice_no=ship_inv,
                        incur_date=d.received_date or po.order_date, amount=ship_amt, vat=0,
                        due_days=c_days, user_id=user_id)
                else:
                    pay_service.remove(db, "shipping", d.id)
            else:
                _cleanup_delivery(db, d.id)

            # Tiến độ giao: số ngày QĐ → ngày QĐ → chênh lệch.
            # Số ngày QĐ ĐƯỢC SỬA TAY: đã có số trên dòng giao thì giữ nguyên, chỉ dòng còn trống
            # mới lấy mặc định theo phân loại (mốc dài nhất — KHÔNG còn phụ thuộc "NCC có sẵn hàng").
            std = int(d.std_days or 0) or lead_time.std_days_of(std_map, it.item_group)
            d.std_days = std
            od = _pdate(po.order_date)
            d.regulated_date = (od + timedelta(days=std)).strftime("%Y-%m-%d") if (od and std) else ""
            d.diff_promise = _days(d.promised_date, d.received_date) if (d.promised_date and d.received_date) else 0
            d.diff_regulated = _days(d.regulated_date, d.received_date) if (d.regulated_date and d.received_date) else 0
            d.diff_required = _days(d.regulated_date, it.required_date) if (d.regulated_date and it.required_date) else 0
            ship_q = float(d.ship_qty or 0)
            # Mã B-06, xem PO_DELIVERY_STATUS. `qc_result` KHÔNG thuộc bộ mã nào — nó là ô chữ
            # tự do người dùng gõ, chỉ tình cờ cũng mang chữ "Lỗi"; đừng gộp hai thứ làm một.
            if recv <= 0:
                d.status = DELIV_PENDING
            elif d.qc_result == "Lỗi":
                d.status = DELIV_DEFECT
            elif ship_q > 0 and recv + 0.001 < ship_q:
                d.status = DELIV_SHORT
            else:
                d.status = DELIV_RECEIVED

        it.qty_received = round(recv_sum, 3)
        it.qty_remaining = round(qty_order - recv_sum, 3)
        # Thành tiền đơn hàng = SL THỰC NHẬN × đơn giá × (1+VAT) (đã chốt) — NGUYÊN TỆ
        it.amount = round(recv_sum * float(it.price or 0) * (1 + vat / 100), 2)
        it.base_amount = round(it.amount * rate, 2)   # bao-CR-319: bản quy đổi cho báo cáo
        # Mã B-06, xem PO_ITEM_LINE_STATUS. Là HÀM của hai con số nên `LINE_FULL` không phải
        # trạng thái kết: tăng SL đặt của một dòng đã đủ là nó tự lùi về `LINE_PARTIAL`.
        if recv_sum <= 0:
            it.line_status = LINE_NOT_DELIVERED
        elif recv_sum + 0.001 < qty_order:
            it.line_status = LINE_PARTIAL
        else:
            it.line_status = LINE_FULL
        total_order += qty_order
        total_received += recv_sum

    # CR-268 — nhận hàng sinh/cập nhật công nợ xong thì TỰ ĐỘNG đối trừ tiền treo
    # (phiếu THANH TOÁN TRƯỚC gắn đúng đơn này, đã chi). Phải chạy TRƯỚC
    # apply_auto_progress (gọi ngay sau recompute_effects) vì is_line_paid đọc
    # paid_amount của công nợ. Treo CẤP NCC (không gắn đơn) KHÔNG tự trừ — kế toán
    # bấm tay, xem payment_request.service.
    from app.modules.payment_request import service as prq_service   # LAZY: tránh circular
    prq_service.apply_prepay_offsets(db, po.code, po.supplier_code, user_id)

    # Trạng thái PO theo tiến độ nhận (không hạ cấp khi chưa duyệt)
    if po.status in ("approved", "partial", "received") and total_order > 0:
        if total_received <= 0:
            po.status = "approved"
        elif total_received + 0.001 < total_order:
            po.status = "partial"
        else:
            po.status = "received"
    db.flush()
