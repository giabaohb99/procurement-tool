"""bao-CR-437 — mọi cột TIỀN cộng gộp nhiều đơn đều phải nhân TỶ GIÁ.

Nền tiền tệ dựng ở bao-CR-319 mới chỉ phủ được đường ghi (công nợ, tồn kho, cột
*Tiền hàng* của màn danh sách). Bốn chỗ ĐỌC dưới đây bị sót, mỗi chỗ một bản chép
riêng của cùng một phép nhân, và bản chép nào cũng thiếu đúng một thừa số:

  1. tệp Excel Đơn mua hàng, cột *Tiền hàng* đầu đơn;
  2. `purchase_progress.export.row_values` — nuôi CẢ BA: bảng Tiến độ trên màn hình,
     tệp Excel Tiến độ, và cụm dòng của tệp Excel ĐMH;
  3. `report/controller.py` giữ hai hàm TRÙNG TÊN với `report/service.py` nhưng thiếu
     tỷ giá — hai tab của cùng một màn Báo cáo ra hai con số;
  4. biểu đồ chi tiêu 12 tháng của Trang chủ.

Sai số không phải vài phần trăm: một đơn CNY tỷ giá 3.620 hiện **42.850** dưới nhãn
"đ" trong khi khoản công nợ sinh từ đúng dòng đó ghi **155.117.000 đ**. Không dấu
hiệu nào trên giao diện báo rằng hai con số đó khác loại tiền.

Đơn giá thì NGƯỢC LẠI — giữ nguyên tệ, vì đó là số in trên hóa đơn nhà cung cấp.
Ranh giới đó cũng được chốt ở đây để lần sau không ai "sửa cho đồng bộ".
"""
import json
from types import SimpleNamespace

from starlette.datastructures import QueryParams

from app.core.export_xlsx import pick_columns
from app.core.filter_operators import apply_operator_filters_map
from app.modules.dashboard.controller import overview
from app.modules.payable.model import Payable
from app.modules.purchase_order import export as po_export
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import OrderType, PODelivery, POItem, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn
from app.modules.purchase_progress import controller as progress_ctl
from app.modules.purchase_progress import export as progress_ex
from app.modules.report import controller as report_ctl
from app.modules.report import service as report_svc
from app.modules.user.model import User

#  Tỷ giá CNY của đơn thật đang nằm dưới cơ sở dữ liệu (đơn 360) — lấy đúng số đó để khi
#  bài kiểm đỏ lên thì con số trong thông báo trùng với con số người dùng đang nhìn thấy.
RATE = 3620.0
RECV_DATE = "2026-09-10"


def _make_po(db, seed, **kw):
    po = PurchaseOrder(code=kw.pop("code", "PO-CNY-437"), company_id=seed.company_id,
                       supplier_code="NX", supplier_name=seed.sup_name,
                       order_date="2026-09-08", status="approved", **kw)
    db.add(po)
    db.flush()
    return po


def _item_in(**kw):
    base = dict(product_code="SP01", product_name="Hàng nhập", item_group="Nhãn",
                unit="cái", qty_request=5000, qty_order=5000, price=4.85, vat=0,
                required_date="2026-09-20", warehouse_code="KHO01")
    base.update(kw)
    return POItemIn(**base)


def _po_ngoai_te(db, seed, **kw):
    """Đơn CNY hai dòng, cả hai đều đã nhận đủ — bản sao thu nhỏ của đơn 360 ngoài đời."""
    po = _make_po(db, seed, order_type=int(OrderType.IMPORT), currency="CNY",
                  exchange_rate=RATE, **kw)
    po_service._save_items(db, po, [
        _item_in(deliveries=[DeliveryIn(received_qty=5000, received_date=RECV_DATE,
                                        warehouse_code="KHO01")]),
        _item_in(product_code="SP02", qty_request=3000, qty_order=3000, price=6.20,
                 deliveries=[DeliveryIn(received_qty=3000, received_date=RECV_DATE,
                                        warehouse_code="KHO01")]),
    ], user_id=1)
    db.flush()
    po_service.recompute_effects(db, po, user_id=1)
    db.flush()
    return po


#  5000 × 4,85 + 3000 × 6,20 = 42.850 CNY = 155.117.000 đ
TIEN_NGUYEN_TE = 5000 * 4.85 + 3000 * 6.20
TIEN_QUY_DOI = TIEN_NGUYEN_TE * RATE


# ── 1. Excel Đơn mua hàng: cột "Tiền hàng" đầu đơn ───────────────────────────────
def test_excel_dmh_tien_hang_da_quy_doi(db, seed):
    po = _po_ngoai_te(db, seed)

    rows = po_export.build_rows(db, [po], show_supplier=True)

    assert rows, "đơn có dòng hàng thì phải ra hàng Excel"
    assert rows[0]["amount"] == round(TIEN_QUY_DOI, 2)
    #  Chốt luôn khoảng cách với bản cũ, để nếu ai đó bỏ tỷ giá ra thì thông báo lỗi nói
    #  thẳng con số 42.850 — thứ người dùng thực sự nhìn thấy trong tệp tải về.
    assert rows[0]["amount"] != round(TIEN_NGUYEN_TE, 2)


def test_excel_dmh_tien_hang_khop_cot_tren_man_hinh(db, seed):
    """Tệp tải về và bảng trên màn hình dùng chung một nhãn cột, buộc phải chung một số."""
    po = _po_ngoai_te(db, seed)

    tren_man_hinh = po_service.order_amount_map(db, [po.id])[po.id]
    trong_tep = po_export.build_rows(db, [po], show_supplier=True)[0]["amount"]

    assert round(trong_tep, 2) == round(tren_man_hinh, 2)


def test_excel_dmh_don_vnd_giu_nguyen_so_cu(db, seed):
    """Chốt chặn hồi quy: đơn trong nước (tỷ giá 1) không được đổi một đồng nào."""
    po = _make_po(db, seed, code="PO-VND-437")
    po_service._save_items(db, po, [_item_in(qty_request=2, qty_order=2, price=1000, vat=10)],
                           user_id=1)
    db.flush()

    rows = po_export.build_rows(db, [po], show_supplier=True)

    assert rows[0]["amount"] == 2200.0          # 2 × 1000 × 1,1


# ── 2. Màn + Excel Tiến độ mua hàng ──────────────────────────────────────────────
def _row_dau_tien(db, po):
    it = po_service.items_of(db, po.id)[0]
    dl = db.query(PODelivery).filter(PODelivery.po_item_id == it.id).first()
    return progress_ex.row_values(po, it, dl, True)


def test_tien_do_thanh_tien_dh_da_quy_doi(db, seed):
    po = _po_ngoai_te(db, seed)

    r = _row_dau_tien(db, po)

    assert r["order_amount"] == round(5000 * 4.85 * RATE, 2)


def test_tien_do_thanh_tien_nhan_bang_dung_so_ghi_cong_no(db, seed):
    """Chú thích trong mã nói "đây mới là số ghi công nợ" — nay câu đó mới thành đúng."""
    po = _po_ngoai_te(db, seed)
    it = po_service.items_of(db, po.id)[0]
    dl = db.query(PODelivery).filter(PODelivery.po_item_id == it.id).first()

    r = progress_ex.row_values(po, it, dl, True)
    #  Mỗi LẦN GIAO sinh một khoản nợ riêng (`ref_id` = id lần giao), đơn hai dòng ra hai khoản.
    no = db.query(Payable).filter(Payable.po_id == po.id, Payable.source_type == "goods",
                                  Payable.ref_id == dl.id).one()

    #  Công nợ tách tiền hàng và VAT thành hai cột, cột Tiến độ gộp cả hai -> so với `total`.
    assert round(r["amount"], 2) == round(float(no.total), 2)


def test_tien_do_don_gia_van_giu_nguyen_te(db, seed):
    """Ranh giới của bản vá: quy đổi THÀNH TIỀN, KHÔNG quy đổi ĐƠN GIÁ.

    Đơn giá là số in trên hóa đơn nhà cung cấp; nhân tỷ giá vào đó là mất luôn khả năng
    đối chiếu với chứng từ gốc, mà cột *Đồng tiền* ngay bên cạnh cũng hết nghĩa.
    """
    po = _po_ngoai_te(db, seed)

    r = _row_dau_tien(db, po)

    assert r["price"] == 4.85
    assert r["price_after_vat"] == 4.85


def test_tien_do_co_cot_dong_tien_va_ty_gia(db, seed):
    """Không có căn cứ quy đổi đi kèm thì người đọc không cách nào kiểm lại cột tiền."""
    po = _po_ngoai_te(db, seed)

    r = _row_dau_tien(db, po)

    assert r["currency"] == "CNY"
    assert r["exchange_rate"] == RATE
    assert {c.key for c in progress_ex.COLS} >= {"currency", "exchange_rate"}


def test_hai_cot_can_cu_luon_xuat_du_khong_bay_tren_bang():
    """Bảng Tiến độ có hai cột này từ bao-CR-439, nhưng ẩn/hiện được như mọi cột khác.

    `pick_columns` vốn bỏ mọi key không nằm trong danh sách cột đang hiện — ai tắt hai cột
    đó đi mà không ép qua `always` thì tệp ra toàn cột tiền đã quy đổi, không kèm căn cứ.
    """
    cols_tren_man_hinh = "po_code,product_code,qty_order,price,order_amount"

    chon = pick_columns(progress_ex.columns_for(True), cols_tren_man_hinh,
                        progress_ex.ALWAYS_COLS)

    assert {c.key for c in chon} >= {"currency", "exchange_rate"}
    #  Hai cột căn cứ xếp CUỐI, không chen vào giữa bộ cột người dùng tự sắp
    assert [c.key for c in chon][:5] == cols_tren_man_hinh.split(",")


# ── 3. Báo cáo mua hàng: một luật, một bản ───────────────────────────────────────
def test_bao_cao_chi_con_mot_ban_tinh_tien():
    """`controller.py` từng giữ bản chép TRÙNG TÊN mà thiếu tỷ giá — nay phải là cùng một hàm."""
    assert report_ctl._amt is report_svc.order_amount_of
    assert report_ctl._recv_amt is report_svc.received_amount_of


def test_bao_cao_gia_tri_dat_va_nhan_deu_quy_doi():
    it = POItem(qty_order=5000, qty_received=3000, price=4.85, vat=0, exchange_rate=RATE)

    assert report_ctl._amt(it) == 5000 * 4.85 * RATE
    assert report_ctl._recv_amt(it) == 3000 * 4.85 * RATE


def test_bao_cao_dong_khong_co_ty_gia_doc_thanh_mot():
    """Dòng cũ (trước migration tiền tệ) để trống tỷ giá — đọc thành 0 là cả báo cáo về 0."""
    it = POItem(qty_order=2, qty_received=2, price=1000, vat=10, exchange_rate=None)

    assert report_ctl._amt(it) == 2200.0
    assert report_ctl._recv_amt(it) == 2200.0


# ── 4. Trang chủ: biểu đồ chi tiêu 12 tháng ──────────────────────────────────────
def test_trang_chu_chi_tieu_12_thang_da_quy_doi(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_order", scope="all", read=True)
    _po_ngoai_te(db, seed)
    db.commit()

    data = json.loads(overview(db=db, user=user).body)["data"]

    thang = {c["label"]: c["value"] for c in data["cost_12m"]}
    assert data["year"] == RECV_DATE[:4]
    #  Cả hai dòng nhận đủ trong cùng một tháng -> cột tháng đó bằng trọn giá trị đơn
    assert thang["T9"] == round(TIEN_QUY_DOI, 0)


# ── 5. bao-CR-439: hai cột căn cứ lên BẢNG, không chỉ nằm trong tệp xuất ─────────
def test_hai_cot_can_cu_sap_xep_va_loc_duoc_nhu_cot_hang_xom():
    """Cột có nút sắp xếp mà backend không biết key đó thì bấm vào KHÔNG XẢY RA GÌ — im lặng.

    `_cond_map` dẫn xuất từ `_sort_map` nên một dòng khai ở đó mở luôn bộ lọc điều kiện. Kiểm
    cả bản `show_supplier=False`: hai cột này không phải cụm NCC, không được rơi theo.
    """
    assert {"currency", "exchange_rate"} <= set(progress_ctl._sort_map())
    assert {"currency", "exchange_rate"} <= set(progress_ctl._cond_map(False))


def test_loc_theo_dong_tien_ra_dung_cum_ngoai_te(db, seed):
    """Cột thành tiền nay quy đổi hết, nên KHÔNG còn cách nào nhìn ra dòng ngoại tệ giữa bảng."""
    _po_ngoai_te(db, seed)
    po_vnd = _make_po(db, seed, code="PO-VND-438")
    po_service._save_items(db, po_vnd, [_item_in(qty_request=2, qty_order=2, price=1000)],
                           user_id=1)
    db.commit()

    def _codes(qs: str) -> set[str]:
        q = (db.query(PurchaseOrder, POItem)
             .join(POItem, POItem.po_id == PurchaseOrder.id))
        req = SimpleNamespace(query_params=QueryParams(qs))
        return {po.code for po, _it in
                apply_operator_filters_map(q, progress_ctl._cond_map(True), req).all()}

    assert _codes("currency__eq=CNY") == {"PO-CNY-437"}
    assert _codes("currency__ne=CNY") == {"PO-VND-438"}
    #  Đơn trong nước để tỷ giá 1; "lớn hơn 1" là cách lọc ra mọi dòng có quy đổi
    assert _codes("exchange_rate__gt=1") == {"PO-CNY-437"}
