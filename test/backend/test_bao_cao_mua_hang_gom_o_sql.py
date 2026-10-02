"""P06 (review hiệu năng 28/09/2026) — `report.procurement_grouped_rows.grouped_po_rows`: bản
GOM Ở SQL của `procurement_summary_rows.po_rows` (đã xóa) cho hàng ĐẶT HÀNG (`kind="po"`). Canh:

  - `order_value`/`deliveries_done`/`on_time_deliveries`/`po_count` khớp CÔNG THỨC cũ
    (`report_service.order_amount_of`, luật đúng-hạn `diff_promise`/`diff_regulated` >= 0);
  - Một ĐMH NHIỀU nhóm hàng vẫn đếm `po_count` = 1 Ở MỖI nhóm hàng (distinct_of theo bucket,
    không phải theo toàn cục) — đây là lý do hàng vẫn giữ độ hạt DÒNG, không collapse theo PO;
  - Trạng thái ĐMH không THẬT (nháp/chờ duyệt/hủy/từ chối) bị loại, cùng luật `REAL_PO_STATUSES`;
  - Lọc công ty + HỢP nhiều khoảng ngày (`ranges`, phục vụ kỳ này + kỳ so sánh trong 1 lượt);
  - So khớp TOÀN BỘ với `compute_procurement_summary` qua endpoint (đã canh ở
    `test_bao_cao_thu_mua_theo_ky.py`) — tệp này canh riêng hàm `grouped_po_rows`.
"""
import itertools
from datetime import date

from app.core.report_aggregate import aggregate
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.report.procurement_grouped_rows import grouped_po_rows

_seq = itertools.count(1)


def _po(db, company_id, order_date, status="approved", supplier="NCC A", nspt="NV A", dept="Kho"):
    #  `code` unique -> hậu tố số tăng dần, khỏi va nhau khi một test dựng NHIỀU ĐMH giống hệt
    #  tham số (vd cùng ngày/NCC/trạng thái nhưng khác công ty).
    po = PurchaseOrder(code=f"PO-{next(_seq):04d}-{order_date}-{supplier}-{status}-{dept}",
                       company_id=company_id,
                       order_date=order_date, status=status, supplier_code=supplier,
                       supplier_name=supplier, nspt=nspt, department=dept)
    db.add(po)
    db.flush()
    return po


def _item(db, po, qty=1, price=100, vat=0, item_group="Nhãn", rate=1):
    it = POItem(po_id=po.id, product_code="SP1", item_group=item_group, qty_order=qty,
               price=price, vat=vat, exchange_rate=rate)
    db.add(it)
    db.flush()
    return it


def _deliv(db, po, it, received_qty=1, diff_promise=0, diff_regulated=0):
    d = PODelivery(po_id=po.id, po_item_id=it.id, received_qty=received_qty,
                   diff_promise=diff_promise, diff_regulated=diff_regulated)
    db.add(d)
    db.flush()
    return d


R = [(date(2026, 9, 1), date(2026, 9, 30))]


def test_order_value_khop_cong_thuc_cu_qty_gia_vat_ty_gia(db, seed):
    cid = seed.company_id
    po = _po(db, cid, "2026-09-10")
    _item(db, po, qty=10, price=1000, vat=8, rate=1)   # 10*1000*1.08 = 10800
    db.commit()

    rows = grouped_po_rows(db, cid, R)
    assert len(rows) == 1
    assert rows[0].order_value == 10800.0


def test_ty_gia_0_hoac_rong_doc_thanh_1(db, seed):
    """`normalize_rate`: tỷ giá 0/None -> 1 (nhân 0 sẽ triệt tiêu cả đơn mà không báo lỗi)."""
    cid = seed.company_id
    po = _po(db, cid, "2026-09-10")
    _item(db, po, qty=1, price=100, vat=0, rate=0)
    db.commit()

    rows = grouped_po_rows(db, cid, R)
    assert rows[0].order_value == 100.0


def test_trang_thai_khong_that_bi_loai(db, seed):
    cid = seed.company_id
    for st in ("draft", "submitted", "cancelled", "rejected"):
        po = _po(db, cid, "2026-09-10", status=st, supplier=f"NCC-{st}")
        _item(db, po, qty=1, price=100)
    db.commit()

    assert grouped_po_rows(db, cid, R) == []


def test_lan_giao_dung_han_theo_ca_hai_dieu_kien(db, seed):
    """Đúng hạn = KHÔNG (diff_promise HOẶC diff_regulated âm) — âm MỘT trong hai là TRỄ."""
    cid = seed.company_id
    po = _po(db, cid, "2026-09-10")
    it = _item(db, po, qty=1, price=100)
    _deliv(db, po, it, diff_promise=0, diff_regulated=0)     # đúng hạn
    _deliv(db, po, it, diff_promise=-1, diff_regulated=0)    # trễ cam kết
    _deliv(db, po, it, diff_promise=0, diff_regulated=-2)    # trễ quy định
    _deliv(db, po, it, received_qty=0, diff_promise=0)       # chưa nhận -> KHÔNG tính
    db.commit()

    rows = grouped_po_rows(db, cid, R)
    assert rows[0].deliveries_done == 3
    assert rows[0].on_time_deliveries == 1


def test_mot_dmh_nhieu_nhom_hang_dem_po_count_o_moi_nhom(db, seed):
    """`po_count` (distinct_of po_id) đúng ở TỪNG bucket group_by=item_group — vẫn giữ 1 dòng
    cho mỗi nhóm hàng của CÙNG một ĐMH thì mới đếm đúng khi gom theo `report_aggregate`."""
    from app.modules.report.procurement_summary_service import _build_spec

    cid = seed.company_id
    po = _po(db, cid, "2026-09-10")
    _item(db, po, qty=1, price=300, item_group="Nhãn")
    _item(db, po, qty=1, price=100, item_group="Thùng")
    db.commit()

    rows = grouped_po_rows(db, cid, R)
    assert len(rows) == 2   # KHÔNG collapse về 1 dòng/PO — po_id vẫn phân biệt được

    spec = _build_spec(db, show_ncc=True)
    got = aggregate(rows, spec, date(2026, 9, 1), date(2026, 9, 30), "day", "item_group")
    by_group = {g["key"]: g["values"] for g in got["groups"]}
    assert by_group["Nhãn"]["po_count"] == 1 and by_group["Nhãn"]["order_value"] == 300.0
    assert by_group["Thùng"]["po_count"] == 1 and by_group["Thùng"]["order_value"] == 100.0
    assert got["totals"]["po_count"] == 1   # tổng KHÔNG cộng đôi — vẫn cùng 1 ĐMH


def test_loc_cong_ty_va_hop_nhieu_khoang_ngay(db, seed):
    cid = seed.company_id
    other_cid = cid + 1
    po_mine = _po(db, cid, "2026-09-10")
    _item(db, po_mine, qty=1, price=100)
    po_other = _po(db, other_cid, "2026-09-10")
    _item(db, po_other, qty=1, price=999)
    po_prev_period = _po(db, cid, "2026-08-15")
    _item(db, po_prev_period, qty=1, price=50)
    db.commit()

    ranges = [(date(2026, 9, 1), date(2026, 9, 30)), (date(2026, 8, 1), date(2026, 8, 31))]
    rows = grouped_po_rows(db, cid, ranges)
    assert {r.order_value for r in rows} == {100.0, 50.0}   # công ty khác bị loại
