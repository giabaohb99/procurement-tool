"""Hai màn danh sách nặng nhất — Đơn mua hàng và Công nợ — phải hỏi gọn cả trang.

Cùng một kiểu lỗi ở hai chỗ: mỗi dòng danh sách cần một mẩu dữ liệu nằm ở bảng
khác, và cách viết tự nhiên nhất là hỏi ngay trong vòng lặp. Đo trên bản sao dữ
liệu thật dưới máy:

- **Đơn mua hàng**, cột *Tiền hàng* phải cộng các dòng hàng: 20 đơn hết 20 lượt
  (19 ms), 97 đơn hết 97 lượt (79 ms) — đúng một lượt cho mỗi dòng danh sách.
- **Công nợ**, cột *Ngày hóa đơn* phải dò dọc chuỗi chứng từ: 20 khoản hết 10
  lượt, 192 khoản hết 346 lượt (238 ms) — tới hai lượt cho mỗi dòng.

Bài kiểm ở đây canh hai điều, và phải canh cả hai mới đủ: **số lượt hỏi không
lớn lên theo số dòng**, và **con số ra vẫn y như bản hỏi từng dòng**. Chỉ đếm
truy vấn thì bỏ hẳn phần tính đi cũng xanh; chỉ so số thì đặt lại truy vấn vào
vòng lặp cũng xanh.
"""
from sqlalchemy import event

from app.modules.payable import service as pay_service
from app.modules.payable.model import Payable
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder


def _count_queries(db, fn, *, like: str = ""):
    """Chạy `fn` và đếm số câu lệnh xuống cơ sở dữ liệu; `like` để lọc theo tên bảng.

    Lọc bằng `FROM <bảng>` chứ đừng lọc bằng tên bảng trần: bí danh cột mà
    SQLAlchemy sinh ra có dạng `tab_po_item_po_id`, tức câu hỏi bảng CHA cũng
    chứa nguyên tên bảng CON.
    """
    counted: list[str] = []

    def _on_exec(conn, cursor, statement, *args):
        if not like or like in statement:
            counted.append(statement)

    event.listen(db.get_bind(), "before_cursor_execute", _on_exec)
    try:
        result = fn()
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", _on_exec)
    return result, counted


# ══════════════════════════════════════════════════════════════════════════════
#  Đơn mua hàng — tiền hàng của cả trang
# ══════════════════════════════════════════════════════════════════════════════

def _make_po(db, lines):
    """Một đơn kèm các dòng hàng; mỗi dòng khai (số lượng, đơn giá, VAT, tỷ giá)."""
    po = PurchaseOrder(code=f"PO-TEST-{len(db.query(PurchaseOrder).all()) + 1:03d}",
                       supplier_code="NCC01", supplier_name="Công ty Thử Nghiệm")
    db.add(po)
    db.flush()
    for qty, price, vat, rate in lines:
        db.add(POItem(po_id=po.id, product_code="SP01", product_name="Giấy A4",
                      qty_order=qty, price=price, vat=vat, exchange_rate=rate))
    db.flush()
    return po


def _amount_one_by_one(db, po) -> float:
    """Bản tính CŨ, hỏi riêng từng đơn — giữ ở đây làm mốc đối chiếu."""
    return round(sum(
        float(i.qty_order or 0) * float(i.price or 0) * (1 + float(i.vat or 0) / 100)
        * po_service.rate_of(i) for i in po_service.items_of(db, po.id)), 2)


def test_tien_hang_gom_ra_dung_y_nhu_ban_tinh_tung_don(db):
    """Bản gom là bản thay thế, nên nó phải ra ĐÚNG con số bản cũ ra — tới từng đồng."""
    pos = [_make_po(db, [(3, 150000, 8, 0), (2, 99999.5, 10, 0)]),
           _make_po(db, [(10, 25.5, 0, 25400)]),
           _make_po(db, [(1, 1000, 8, 1)])]
    db.commit()

    amounts = po_service.order_amount_map(db, [p.id for p in pos])

    assert amounts == {p.id: _amount_one_by_one(db, p) for p in pos}


def test_ty_gia_TRONG_phai_doc_thanh_mot(db):
    """Đơn trong nước để trống ô tỷ giá. Nhân với 0 thì cả đơn thành 0 đồng mà
    không có gì báo lỗi — đúng chỗ bao-CR-319 đã phải vá một lần."""
    po = _make_po(db, [(2, 500000, 0, 0)])
    db.commit()

    assert po_service.order_amount_map(db, [po.id])[po.id] == 1000000.0


def test_don_chua_co_dong_hang_van_co_KHOA_gia_tri_khong(db):
    """Thiếu khóa thì chỗ gọi phải tự đoán: "đơn rỗng" hay "quên hỏi đơn này"?"""
    po = _make_po(db, [])
    db.commit()

    assert po_service.order_amount_map(db, [po.id]) == {po.id: 0.0}


def test_danh_sach_don_rong_thi_KHONG_hoi_cau_nao(db):
    """Trang không có dòng nào vẫn đi qua hàm này. `IN ()` là câu hỏi vô nghĩa."""
    _, counted = _count_queries(db, lambda: po_service.order_amount_map(db, []),
                                like="FROM tab_po_item")

    assert counted == []


def test_hai_muoi_don_van_chi_MOT_luot_hoi_dong_hang(db):
    """Trần CỨNG, không phải số đo tham khảo: một trang bao nhiêu đơn cũng chỉ
    một câu hỏi vào bảng dòng hàng."""
    pos = [_make_po(db, [(1, 1000, 8, 0), (2, 2000, 10, 0)]) for _ in range(20)]
    db.commit()

    _, counted = _count_queries(db, lambda: po_service.order_amount_map(db, [p.id for p in pos]),
                                like="FROM tab_po_item")

    assert len(counted) == 1, f"Đã quay lại N+1: {len(counted)} truy vấn cho {len(pos)} đơn"


def test_them_don_thi_tong_so_luot_hoi_KHONG_tang(db):
    """Đếm theo một tên bảng bắt được lần lười quay lại ở đúng chỗ này, nhưng lần
    sau N+1 có thể mọc ở bảng khác. So hai kích cỡ trang thì bắt được cả chỗ đó."""
    pos = [_make_po(db, [(1, 1000, 8, 0)]) for _ in range(12)]
    db.commit()
    ids = [p.id for p in pos]

    _, it_counted = _count_queries(db, lambda: po_service.order_amount_map(db, ids[:3]))
    _, nhieu_counted = _count_queries(db, lambda: po_service.order_amount_map(db, ids))

    assert len(nhieu_counted) == len(it_counted), (
        f"3 đơn hết {len(it_counted)} truy vấn, 12 đơn hết {len(nhieu_counted)} — "
        "số lượt hỏi đang lớn lên theo số dòng")


# ══════════════════════════════════════════════════════════════════════════════
#  Công nợ — ngày hóa đơn của cả trang
# ══════════════════════════════════════════════════════════════════════════════

def _make_payable(db, *, delivery_invoice_date="", item_invoice_date="",
                  invoice_no="", incur_date="", linked=True):
    """Một khoản nợ kèm chuỗi chứng từ phía sau nó.

    `linked=False` dựng khoản nợ không sinh từ đợt giao (chi phí nhập khẩu chẳng
    hạn) — nhánh lùi sang số hóa đơn + ngày phát sinh.
    """
    ref_id = 0
    if linked:
        item = POItem(po_id=1, invoice_date=item_invoice_date)
        db.add(item)
        db.flush()
        deliv = PODelivery(po_id=1, po_item_id=item.id, invoice_date=delivery_invoice_date)
        db.add(deliv)
        db.flush()
        ref_id = deliv.id
    p = Payable(supplier_code="NCC01", source_type="goods",
                ref_type="delivery" if linked else "import_cost", ref_id=ref_id,
                invoice_no=invoice_no, incur_date=incur_date, total=1000, remaining=1000)
    db.add(p)
    db.flush()
    return p


def _reload_payables(db, ps):
    """Nạp lại khoản nợ bằng MỘT câu, y như màn danh sách thật.

    `db.commit()` làm hết hạn mọi bản ghi đang giữ, nên đọc thuộc tính đầu tiên là
    mỗi bản ghi một lượt `SELECT ... WHERE id = ?`. Đó là chuyện của bài kiểm chứ
    không phải của màn hình — không nạp lại thì bộ đếm dưới đây đếm nhầm lượt hết
    hạn thành N+1 của mã nguồn.
    """
    ids = [p.id for p in ps]
    rows = db.query(Payable).filter(Payable.id.in_(ids)).all()
    return sorted(rows, key=lambda p: ids.index(p.id))


def _invoice_date_one_by_one(db, p) -> str:
    """Bản dò CŨ, hỏi riêng từng khoản — `get_invoice_date` nay chỉ là lối vào lẻ."""
    return pay_service.get_invoice_date(db, p)


def test_ngay_hoa_don_gom_ra_dung_y_nhu_ban_do_tung_khoan(db):
    """Ba nhánh dò phải ra y hệt nhau ở cả hai bản: đợt giao tự khai ngày · đợt
    giao câm thì lấy của dòng hàng · không sinh từ đợt giao thì lùi về ngày phát sinh."""
    ps = [_make_payable(db, delivery_invoice_date="2026-03-01", item_invoice_date="2026-02-02"),
          _make_payable(db, delivery_invoice_date="", item_invoice_date="2026-02-02"),
          _make_payable(db, delivery_invoice_date="", item_invoice_date="",
                        invoice_no="HD001", incur_date="2026-01-15"),
          _make_payable(db, linked=False, invoice_no="HD002", incur_date="2026-01-20"),
          _make_payable(db, linked=False)]
    db.commit()

    dates = pay_service.invoice_date_map(db, ps)

    assert dates == {p.id: _invoice_date_one_by_one(db, p) for p in ps}


def test_dot_giao_TU_KHAI_ngay_thi_khong_do_tiep_xuong_dong_hang(db):
    """Thứ tự ưu tiên là một phần của luật, không phải chuyện ngẫu nhiên: ngày trên
    đợt giao thắng ngày trên dòng hàng."""
    p = _make_payable(db, delivery_invoice_date="2026-03-01", item_invoice_date="2026-02-02")
    db.commit()

    assert pay_service.invoice_date_map(db, [p])[p.id] == "2026-03-01"


def test_khoan_khong_do_ra_ngay_van_co_KHOA_chuoi_rong(db):
    """Thiếu khóa thì chỗ gọi phải tự đoán: "không có ngày" hay "quên hỏi khoản này"?"""
    p = _make_payable(db, linked=False)
    db.commit()

    assert pay_service.invoice_date_map(db, [p]) == {p.id: ""}


def test_danh_sach_no_rong_thi_KHONG_hoi_cau_nao(db):
    """Trang không có dòng nào vẫn đi qua hàm này."""
    _, counted = _count_queries(db, lambda: pay_service.invoice_date_map(db, []))

    assert counted == []


def test_hai_muoi_khoan_no_van_chi_HAI_luot_hoi(db):
    """Trần CỨNG: một lượt hỏi đợt giao, một lượt hỏi dòng hàng, hết. Số dòng danh
    sách không được chạm vào con số này."""
    ps = [_make_payable(db, delivery_invoice_date="", item_invoice_date="2026-02-02")
          for _ in range(20)]
    db.commit()
    ps = _reload_payables(db, ps)

    _, counted = _count_queries(db, lambda: pay_service.invoice_date_map(db, ps))

    assert len(counted) == 2, f"Đã quay lại N+1: {len(counted)} truy vấn cho {len(ps)} khoản"


def test_them_khoan_no_thi_tong_so_luot_hoi_KHONG_tang(db):
    ps = [_make_payable(db, delivery_invoice_date="2026-03-01") for _ in range(12)]
    db.commit()
    ps = _reload_payables(db, ps)

    _, it_counted = _count_queries(db, lambda: pay_service.invoice_date_map(db, ps[:3]))
    _, nhieu_counted = _count_queries(db, lambda: pay_service.invoice_date_map(db, ps))

    assert len(nhieu_counted) == len(it_counted), (
        f"3 khoản hết {len(it_counted)} truy vấn, 12 khoản hết {len(nhieu_counted)} — "
        "số lượt hỏi đang lớn lên theo số dòng")
