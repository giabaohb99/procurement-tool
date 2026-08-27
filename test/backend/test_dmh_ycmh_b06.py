"""B-06 — cụm Đơn mua hàng + Yêu cầu mua hàng chuyển sang MÃ tiếng Anh.

Đợt thứ sáu của kế hoạch đổ bê tông nền v2 (`doc/erp/15-do-be-tong-nen-v2.md` §3), và là đợt
nặng nhất: **sáu cột trong một đợt**, chia hai nhịp migration.

  nhịp 1 · `a3f7d2e51c94` — bốn cột "phẳng", không cột nào có thứ tự tiến trình:
      7  tab_purchase_request_item.line_status   (PR_LINE_STATUS)
      8  tab_purchase_order.document_status      (PO_DOCUMENT_STATUS)  — giá trị cũ VIẾT THƯỜNG
      9  tab_po_item.line_status                 (PO_ITEM_LINE_STATUS) — có dòng RỖNG hợp lệ
     12  tab_po_delivery.status                  (PO_DELIVERY_STATUS)

  nhịp 2 · `b6e9c4801fa2` — máy trạng thái:
     10  tab_po_item.progress_status             (PO_PROGRESS_STATUS)
     11  tab_po_item.status_before_pause         cùng bộ giá trị + chuỗi RỖNG

Bốn nhóm rủi ro riêng của đợt này, cũng là bốn nhóm bài kiểm dưới đây:

  1. **THỨ TỰ là logic, không phải nhãn.** `purchase_order.service.PROGRESS_ORDER` là một list
     và bước kế tiếp tính bằng `.index(...)`. Chèn/đổi chỗ một mã trong bộ mã là đổi nghĩa của
     mọi dòng đang nằm sau vị trí đó — mà không có gì báo lỗi.
  2. **Hai cột phải đổi CÙNG LÚC.** `status_before_pause` là bản chụp của `progress_status`;
     nút *Bỏ tạm ngưng* gán thẳng giá trị đó ngược trở lại. Lệch nhau là khôi phục một chuỗi
     tiếng Việt vào cột đã chuyển sang mã, im lặng.
  3. **`document_status` viết THƯỜNG trong CSDL** nhưng nhãn để hiện thì viết hoa chữ đầu.
     `downgrade()` phải trả lại đúng thứ CSDL đang có, không phải nhãn của bộ mã.
  4. **Chuỗi RỖNG là giá trị hợp lệ** ở `tab_po_item.line_status` và `status_before_pause`.
     Đổi nó thành một mức thật là bịa ra dữ liệu mà không ai kiểm lại được.
"""
import importlib.util
from pathlib import Path

import pytest

from app.core.status_codes import (PO_DELIVERY_STATUS, PO_DOCUMENT_STATUS, PO_ITEM_LINE_STATUS,
                                   PO_PROGRESS_STATUS, PR_LINE_STATUS)
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_order import service as po_svc
from app.modules.purchase_request.model import PurchaseRequestItem
from app.modules.purchase_request import service as pr_svc

_SAU_BO_MA = [PR_LINE_STATUS, PO_DOCUMENT_STATUS, PO_ITEM_LINE_STATUS,
              PO_DELIVERY_STATUS, PO_PROGRESS_STATUS]


# ── Bộ mã ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("bo", _SAU_BO_MA, ids=lambda b: b.name)
def test_ma_la_ascii_thuong_va_khong_trung(bo):
    """Cột lưu MÃ. Lọt tiếng Việt vào đây là quay lại đúng cái mớ vừa dọn."""
    for c in bo.codes:
        assert c.value.isascii() and c.value.islower(), c
        assert c.label, c
    assert len(set(bo.values)) == len(bo.values)


def test_thu_tu_tien_do_TRUNG_KHIT_list_cua_service():
    """Bài kiểm quan trọng nhất của cả đợt.

    `auto_advance_line` đi tới bước kế bằng `PROGRESS_ORDER.index(...)`. Nếu `ordered_values`
    lệch khỏi chuỗi sáu bước cũ — thừa một mã ngoại lệ, thiếu một bước, hoặc đảo chỗ — thì mọi
    dòng đang nằm sau vị trí lệch bị hiểu sai mức tiến độ mà KHÔNG có lỗi nào nổ ra.
    """
    assert po_svc.PROGRESS_ORDER == [
        "not_ordered", "ordered", "received", "doc_pending", "doc_sent", "completed",
    ]
    assert tuple(po_svc.PROGRESS_ORDER) == PO_PROGRESS_STATUS.ordered_values
    # Hai ngoại lệ nằm NGOÀI chuỗi, không được lẫn vào để `.index(...)` đếm nhầm số bước.
    assert set(po_svc.PROGRESS_EXCEPTIONS) == {"paused", "cancelled"}
    assert not set(po_svc.PROGRESS_ORDER) & set(po_svc.PROGRESS_EXCEPTIONS)


def test_ycmh_va_dmh_dung_chung_mot_nguon_thu_tu():
    """`purchase_request.service._PROGRESS_ORDER` trước B-06 là bản CHÉP TAY của list bên ĐMH.
    Hai bản chép trôi khỏi nhau thì `sync_from_purchase_orders` xếp dòng YCMH sai mức mà không
    ai biết — nên nay cả hai cùng đọc một bộ mã."""
    assert pr_svc._PROGRESS_ORDER == po_svc.PROGRESS_ORDER


def test_diem_cuoi_cua_dong_ycmh_dung_hang_chu_khong_go_chuoi():
    assert pr_svc.LINE_STATUS_DONE == ("completed", "cancelled")
    assert pr_svc.LINE_STATUS_IDLE == ("no_po", "not_ordered")
    # `.values` là frozenset (không thứ tự) nên phải so với `.codes` — danh sách này lên UI làm
    # ô chọn, thứ tự khai báo chính là thứ tự người dùng nhìn thấy.
    assert pr_svc.LINE_STATUS == [c.value for c in PR_LINE_STATUS.codes]


def test_bon_ma_ngoai_le_va_ket_dung_cho():
    """`cancelled` vừa là điểm cuối vừa là nhánh rẽ; `paused` chỉ là nhánh rẽ (bỏ tạm ngưng thì
    dòng quay lại chuỗi). Đánh nhầm `paused` là điểm cuối thì màn nào tin vào cờ đó sẽ khóa
    luôn dòng đang tạm ngưng, không ai mở lại được."""
    assert PO_PROGRESS_STATUS.is_terminal("completed")
    assert PO_PROGRESS_STATUS.is_terminal("cancelled")
    assert not PO_PROGRESS_STATUS.is_terminal("paused")
    assert PO_PROGRESS_STATUS.is_exception("paused")
    assert PO_PROGRESS_STATUS.is_exception("cancelled")
    assert PR_LINE_STATUS.is_terminal("completed") and PR_LINE_STATUS.is_terminal("cancelled")
    # Hàng LỖI của lần giao là nhánh rẽ, không phải một nấc tiến trình.
    assert PO_DELIVERY_STATUS.is_exception("defect")


def test_chuoi_rong_khong_nam_trong_bo_ma_nao():
    """Rỗng là giá trị hợp lệ của hai cột (chưa tính lần nào / chưa từng tạm ngưng) nhưng KHÔNG
    phải một mã. Đưa nó vào bộ mã là mời người sau vẽ badge cho một ô trống."""
    for bo in _SAU_BO_MA:
        assert "" not in bo.values, bo.name


# ── Tầng ghi: chặn giá trị lạ tại cửa ────────────────────────────────────────────
def test_update_item_status_chan_chu_tieng_viet_kieu_cu(db, seed):
    """Giao diện cũ (`frontend/`, đóng băng) vẫn có thể gửi chữ tiếng Việt lên. Ghi lặng lẽ thì
    dòng đó rơi khỏi MỌI bộ lọc VÀ khỏi cả điều kiện hoàn thành phiếu — hỏng ở chỗ không ai
    nhìn. Chặn 400 ngay tại cửa."""
    from fastapi import HTTPException

    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.purchase_request.schema import ItemStatusIn, ItemStatusItem

    pr = PurchaseRequest(code="PYC-B06", status="approved", department="Phòng Test")
    db.add(pr)
    db.flush()
    it = PurchaseRequestItem(pr_id=pr.id, product_code="SP1", product_name="SP 1",
                                line_status="no_po")
    db.add(it)
    db.commit()

    def goi(value):
        # `is_manager=True` để bỏ qua vế lọc "NSTM chỉ sửa dòng được giao cho mình" — ở đây
        # đang kiểm cửa chặn giá trị, không kiểm phân quyền.
        return pr_svc.update_item_status(
            db, pr.id, ItemStatusIn(items=[ItemStatusItem(id=it.id, line_status=value)]),
            seed.u_req_id, seed.emp_req_code, True)

    with pytest.raises(HTTPException) as e:
        goi("Hủy đơn")
    assert e.value.status_code == 400

    goi("cancelled")
    db.refresh(it)
    assert it.line_status == "cancelled"


def test_import_misa_khong_ghi_thang_chu_la_vao_cot():
    """Trước B-06 chữ lạ trong file Misa được GHI THẲNG vào cột (`.get(..., d["progress"])`) —
    một ô gõ sai là một dòng mang trạng thái không tồn tại. Nay lùi về bước đầu chuỗi."""
    from app.modules.import_tool import po_import

    assert po_import.DEFAULT_PROGRESS == PO_PROGRESS_STATUS.ordered_values[0]
    assert set(po_import._PROGRESS.values()) <= set(PO_PROGRESS_STATUS.values)
    # "đang giao" từng được dịch thành "Đang giao hàng" — một chuỗi KHÔNG có trong máy trạng thái.
    assert po_import._PROGRESS["đang giao"] == "ordered"


# ── Tầng đọc: nhãn đi kèm mã ────────────────────────────────────────────────────
def test_api_ycmh_gan_san_nhan_tieng_viet(db):
    """Giao diện KHÔNG được tự dịch mã. Quên gắn nhãn là cột hiện `no_po` giữa màn tiếng Việt."""
    from app.modules.purchase_request import controller as pr_ctrl

    assert PR_LINE_STATUS.label_of("no_po") == "Chưa tạo đơn mua hàng"
    src = __import__("inspect").getsource(pr_ctrl)
    assert "line_status_label" in src


def test_file_xuat_ra_CHU_con_api_tra_MA():
    """Cùng một `row_values` nuôi cả API danh sách lẫn file Excel: API cần MÃ để tô badge và để
    gửi lại làm tham số lọc, file cần CHỮ cho người đọc. `dich_ma` là chỗ tách hai đường đó."""
    from app.modules.purchase_progress import export as pp_export

    r = pp_export.translate_codes({"progress_status": "doc_sent", "line_status": "full",
                           "delivery_status": "defect", "document_status": "none",
                           "po_code": "PO00001"})
    assert r["progress_status"] == "Đã gửi ĐMH cho KT"
    assert r["line_status"] == "Đủ"
    assert r["delivery_status"] == "Lỗi"
    assert r["document_status"] == "Chưa có chứng từ"
    assert r["po_code"] == "PO00001"          # cột không phải trạng thái thì không đụng vào


def test_ma_la_khong_bi_nuot_mat():
    """Dòng chưa chạy migration (hoặc do nơi khác ghi vào) vẫn phải đọc được: nuốt thành ô trống
    là người dùng tưởng dòng đó không có trạng thái nào."""
    from app.modules.purchase_progress import export as pp_export

    r = pp_export.translate_codes({"progress_status": "Trạng thái lạ", "line_status": ""})
    assert r["progress_status"] == "Trạng thái lạ"
    assert r["line_status"] == ""


# ── Migration ───────────────────────────────────────────────────────────────────
_TEN_N1 = "a3f7d2e51c94_b06n1_chuan_hoa_bon_cot_phang_dmh_ycmh.py"
_TEN_N2 = "b6e9c4801fa2_b06n2_chuan_hoa_may_trang_thai_tien_do_dong_dmh.py"


def _nap_migration(name: str, ten_mod: str):
    duong_dan = Path(__file__).resolve().parents[2] / "migrations" / "versions" / name
    if not duong_dan.exists():   # chạy trong container: /app/test/backend + /app/migrations
        duong_dan = Path("/app/migrations/versions") / name
    spec = importlib.util.spec_from_file_location(ten_mod, duong_dan)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def n1():
    return _nap_migration(_TEN_N1, "mig_b06n1")


@pytest.fixture
def n2():
    return _nap_migration(_TEN_N2, "mig_b06n2")


def _dung_migration(db, mig, direction: str) -> None:
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    ctx = MigrationContext.configure(db.connection())
    with Operations.context(ctx):
        getattr(mig, direction)()
    db.expire_all()


# ── Nhịp 1 ──────────────────────────────────────────────────────────────────────
def test_n1_khop_theo_dang_chuan_hoa_chu_khong_khop_tuyet_doi(n1):
    """Khớp tuyệt đối thì một dấu cách thừa hay một chữ hoa lệch là lọt lưới, và dòng đó nằm im
    trong CSDL với giá trị tiếng Việt cho tới lúc có người lọc không ra."""
    pr = lambda s: n1._MAP_PR_LINE.get(n1._norm(s))      # noqa: E731
    doc = lambda s: n1._MAP_PO_DOC.get(n1._norm(s))      # noqa: E731

    assert pr("Chưa tạo đơn mua hàng") == "no_po"
    assert pr("  CHƯA TẠO ĐƠN MUA HÀNG ") == "no_po"
    assert pr("chua  tao   don mua hang") == "no_po"     # bản gõ không dấu
    assert pr("Hủy đơn") == "cancelled"
    assert pr("Đã duyệt") is None                        # không đoán bừa, giữ nguyên + in log

    # `document_status` viết thường trong CSDL — chuẩn hóa xong thì hai hệ chữ về cùng một khóa.
    assert doc("chưa có chứng từ") == "none"
    assert doc("Chưa có chứng từ") == "none"


def test_n1_bang_nhan_cua_document_status_CO_Y_VIET_THUONG(n1):
    """Bẫy riêng của đợt này. Giá trị cũ trong CSDL là "chưa có chứng từ" (thường), nhãn trong
    `status_codes.py` là "Chưa có chứng từ" (hoa chữ đầu) vì đó là chữ để HIỆN. `downgrade()`
    phải trả lại đúng thứ CSDL đang có, nên `_LABEL_PO_DOC` cố ý LỆCH với nhãn bộ mã."""
    assert set(n1._LABEL_PO_DOC) == set(PO_DOCUMENT_STATUS.values)
    for code, text in n1._LABEL_PO_DOC.items():
        assert text == text.lower(), code
        assert text != PO_DOCUMENT_STATUS.label_of(code), code


@pytest.mark.parametrize("ten_map,ten_label,bo", [
    ("_MAP_PR_LINE", "_LABEL_PR_LINE", PR_LINE_STATUS),
    ("_MAP_PO_ITEM_LINE", "_LABEL_PO_ITEM_LINE", PO_ITEM_LINE_STATUS),
    ("_MAP_PO_DELIVERY", "_LABEL_PO_DELIVERY", PO_DELIVERY_STATUS),
])
def test_n1_ba_bo_con_lai_TRUNG_KHIT_nhan_bo_ma(n1, ten_map, ten_label, bo):
    """Ba cột này thì giá trị cũ và nhãn trùng nhau từng ký tự — ngược với `document_status`.
    Migration không được import mã nguồn ứng dụng nên `_LABEL_*` là bản chép tay; bài kiểm này
    là thứ duy nhất giữ cho bản chép không trôi."""
    label = getattr(n1, ten_label)
    assert set(getattr(n1, ten_map).values()) == set(bo.values)
    assert set(label) == set(bo.values)
    for code, text in label.items():
        assert text == bo.label_of(code), code


def _nap_n1(db):
    """Dữ liệu cũ đủ bốn bảng, kèm đúng các ca hiểm: dòng RỖNG, chữ lạ, id thưa."""
    db.add_all([
        PurchaseRequestItem(id=1, pr_id=1, product_code="SP1",
                            product_name="Ten SP1", line_status="Chưa tạo đơn mua hàng"),
        PurchaseRequestItem(id=2, pr_id=1, product_code="SP2",
                            product_name="Ten SP2", line_status="Đã nhận hàng"),
        PurchaseRequestItem(id=3, pr_id=1, product_code="SP3",
                            product_name="Ten SP3", line_status="Hủy đơn"),
        PurchaseOrder(id=1, code="PO00001", document_status="chưa có chứng từ"),
        PurchaseOrder(id=2, code="PO00002", document_status="đã có thông tin chứng từ"),
        PurchaseOrder(id=3, code="PO00003", document_status="đã đủ chứng từ"),
        POItem(id=1, po_id=1, product_code="SP1", line_status="Chưa giao"),
        POItem(id=2, po_id=1, product_code="SP2", line_status="Đủ"),
        POItem(id=3, po_id=1, product_code="SP3", line_status=""),          # dòng cũ chưa tính
        PODelivery(id=1, po_id=1, po_item_id=1, status="Chờ giao"),
        PODelivery(id=2, po_id=1, po_item_id=2, status="Đã nhận"),
        PODelivery(id=3, po_id=1, po_item_id=3, status="Giao thiếu"),
    ])
    db.commit()


def _doc_n1(db) -> dict:
    return {
        "pr": [r.line_status for r in db.query(PurchaseRequestItem).order_by(PurchaseRequestItem.id)],
        "doc": [r.document_status for r in db.query(PurchaseOrder).order_by(PurchaseOrder.id)],
        "item": [r.line_status for r in db.query(POItem).order_by(POItem.id)],
        "del": [r.status for r in db.query(PODelivery).order_by(PODelivery.id)],
    }


def test_n1_doi_het_bon_cot(db, n1):
    _nap_n1(db)
    _dung_migration(db, n1, "upgrade")
    assert _doc_n1(db) == {
        "pr": ["no_po", "received", "cancelled"],
        "doc": ["none", "partial", "full"],
        "item": ["not_delivered", "full", ""],       # ô rỗng giữ nguyên
        "del": ["pending", "received", "short"],
    }


def test_n1_chay_xuoi_roi_nguoc_tra_ve_dung_tung_ky_tu(db, n1):
    """Điều kiện thứ ba của QĐ-12: `downgrade()` khôi phục byte-exact."""
    _nap_n1(db)
    before = _doc_n1(db)

    _dung_migration(db, n1, "upgrade")
    assert _doc_n1(db) != before
    _dung_migration(db, n1, "downgrade")
    assert _doc_n1(db) == before


def test_n1_o_rong_khong_bi_bia_thanh_mot_muc_that(db, n1):
    """`tab_po_item.line_status` rỗng nghĩa là "chưa từng được tính lại", khác hẳn "Chưa giao".
    Đổi rỗng thành `not_delivered` là bịa ra dữ liệu mà không ai kiểm lại được."""
    db.add(POItem(id=9, po_id=1, product_code="SPX", line_status=""))
    db.commit()
    _dung_migration(db, n1, "upgrade")
    assert db.get(POItem, 9).line_status == ""


def test_n1_gia_tri_la_giu_nguyen_chu_khong_doan_bua(db, n1):
    _nap_n1(db)
    db.add(PurchaseRequestItem(id=99, pr_id=1, product_code="SPZ",
                            product_name="Ten SPZ", line_status="Trạng thái lạ"))
    db.commit()
    _dung_migration(db, n1, "upgrade")
    assert db.get(PurchaseRequestItem, 99).line_status == "Trạng thái lạ"


def test_n1_chay_theo_lo_khong_bo_sot_dong_nao(db, n1, monkeypatch):
    """Lô cắt theo KHOẢNG ID nên id thưa (dòng đã xóa) là chỗ dễ sai cận nhất. Sai cận thì dòng
    bị bỏ sót im lặng — không lỗi, chỉ là vài dòng còn chữ tiếng Việt."""
    monkeypatch.setattr(n1, "CO_LO", 2)
    for i in (1, 2, 3, 50, 51, 90, 91):
        db.add(POItem(id=i, po_id=1, product_code=f"SP{i}", line_status="Chưa giao"))
    db.commit()

    _dung_migration(db, n1, "upgrade")
    remaining = [r.line_status for r in db.query(POItem).all()]
    assert remaining == ["not_delivered"] * 7


@pytest.mark.parametrize("direction", ["upgrade", "downgrade"])
def test_n1_bang_rong_khong_no(db, n1, direction):
    """Môi trường mới dựng chưa có đơn nào."""
    _dung_migration(db, n1, direction)
    assert _doc_n1(db) == {"pr": [], "doc": [], "item": [], "del": []}


# ── Nhịp 2 ──────────────────────────────────────────────────────────────────────
def test_n2_bang_nhan_TRUNG_KHIT_nhan_bo_ma(n2):
    """Khác `document_status` ở nhịp 1: ở bộ này giá trị cũ và nhãn trùng nhau cả tám dòng."""
    assert set(n2._MAP.values()) == set(PO_PROGRESS_STATUS.values)
    assert set(n2._LABEL) == set(PO_PROGRESS_STATUS.values)
    for code, text in n2._LABEL.items():
        assert text == PO_PROGRESS_STATUS.label_of(code), code


def test_n2_khop_ca_ban_go_khong_dau_va_chu_DMH(n2):
    doi = lambda s: n2._MAP.get(n2._norm(s))      # noqa: E731
    assert doi("Đã gửi ĐMH cho KT") == "doc_sent"
    assert doi("da gui dmh cho kt") == "doc_sent"
    assert doi("  ĐÃ GỬI ĐMH  CHO KT ") == "doc_sent"
    assert doi("Tạm ngưng") == "paused"
    assert doi("Đang giao hàng") is None       # chuỗi rác cũ của import Misa — không đoán bừa


def _nap_n2(db):
    db.add_all([
        POItem(id=1, po_id=1, product_code="SP1", progress_status="Chưa đặt hàng",
               status_before_pause=""),
        POItem(id=2, po_id=1, product_code="SP2", progress_status="Đã gửi ĐMH cho KT",
               status_before_pause=""),
        POItem(id=3, po_id=1, product_code="SP3", progress_status="Hoàn thành",
               status_before_pause=""),
        # Dòng đang tạm ngưng: cột 11 giữ mức trước khi ngưng.
        POItem(id=4, po_id=1, product_code="SP4", progress_status="Tạm ngưng",
               status_before_pause="Đã đặt hàng"),
        POItem(id=5, po_id=1, product_code="SP5", progress_status="Hủy đơn",
               status_before_pause=""),
    ])
    db.commit()


def _doc_n2(db) -> list:
    return [(r.id, r.progress_status, r.status_before_pause)
            for r in db.query(POItem).order_by(POItem.id).all()]


def test_n2_doi_ca_hai_cot(db, n2):
    _nap_n2(db)
    _dung_migration(db, n2, "upgrade")
    assert _doc_n2(db) == [
        (1, "not_ordered", ""),
        (2, "doc_sent", ""),
        (3, "completed", ""),
        (4, "paused", "ordered"),
        (5, "cancelled", ""),
    ]


def test_n2_bo_tam_ngung_van_tra_dung_muc_truoc_do(db, n2):
    """Đây là lý do hai cột phải đổi cùng lúc. Chỉ đổi `progress_status` thì nút *Bỏ tạm ngưng*
    gán "Đã đặt hàng" (tiếng Việt) vào cột đã chuyển sang mã — dòng rơi khỏi mọi bộ lọc và
    `PROGRESS_ORDER.index(...)` coi nó là bước 0, tức là tự lùi về đầu chuỗi."""
    _nap_n2(db)
    _dung_migration(db, n2, "upgrade")

    it = db.get(POItem, 4)
    assert it.progress_status == "paused"
    khoi_phuc = it.status_before_pause
    assert khoi_phuc in PO_PROGRESS_STATUS.values
    assert khoi_phuc in po_svc.PROGRESS_ORDER
    assert po_svc.PROGRESS_ORDER.index(khoi_phuc) == 1      # không tụt về bước 0


def test_n2_chay_xuoi_roi_nguoc_tra_ve_dung_tung_ky_tu(db, n2):
    _nap_n2(db)
    before = _doc_n2(db)

    _dung_migration(db, n2, "upgrade")
    assert _doc_n2(db) != before
    _dung_migration(db, n2, "downgrade")
    assert _doc_n2(db) == before


def test_n2_o_rong_cua_status_before_pause_giu_nguyen(db, n2):
    """Rỗng = dòng chưa từng tạm ngưng, là MẶC ĐỊNH của cột. Nó không nằm trong `_MAP` nên rơi
    vào nhánh "không nhận ra" và được giữ nguyên — đúng ý muốn."""
    _nap_n2(db)
    _dung_migration(db, n2, "upgrade")
    assert [v for _, _, v in _doc_n2(db) if v == ""] == [""] * 4


def test_n2_gia_tri_la_giu_nguyen_chu_khong_doan_bua(db, n2):
    db.add(POItem(id=9, po_id=1, product_code="SPZ", progress_status="Đang giao hàng",
                  status_before_pause=""))
    db.commit()
    _dung_migration(db, n2, "upgrade")
    assert db.get(POItem, 9).progress_status == "Đang giao hàng"


def test_n2_chay_theo_lo_khong_bo_sot_dong_nao(db, n2, monkeypatch):
    monkeypatch.setattr(n2, "CO_LO", 2)
    for i in (1, 2, 3, 50, 51, 90, 91):
        db.add(POItem(id=i, po_id=1, product_code=f"SP{i}",
                      progress_status="Chưa đặt hàng", status_before_pause=""))
    db.commit()

    _dung_migration(db, n2, "upgrade")
    assert [r.progress_status for r in db.query(POItem).all()] == ["not_ordered"] * 7


@pytest.mark.parametrize("direction", ["upgrade", "downgrade"])
def test_n2_bang_rong_khong_no(db, n2, direction):
    _dung_migration(db, n2, direction)
    assert _doc_n2(db) == []


# ── Hai nhịp nối nhau ───────────────────────────────────────────────────────────
def test_hai_nhip_chay_noi_tiep_roi_lui_ve_dung_trang_thai_ban_dau(db, n1, n2):
    """Nhịp 2 nối sau nhịp 1 (`down_revision = "a3f7d2e51c94"`) nên phải kiểm cả cặp: cùng động
    vào `tab_po_item` nhưng hai cột khác nhau, chạy chồng lên nhau không được lệch."""
    assert n2.down_revision == n1.revision

    _nap_n1(db)
    # `_nap_n1` chỉ đặt `line_status` cho POItem; ở đây cần dòng mang CẢ BA cột nên thay hẳn.
    db.query(POItem).delete()
    db.commit()
    db.add_all([
        POItem(id=1, po_id=1, product_code="SP1", line_status="Chưa giao",
               progress_status="Chưa đặt hàng", status_before_pause=""),
        POItem(id=2, po_id=1, product_code="SP2", line_status="Đủ",
               progress_status="Tạm ngưng", status_before_pause="Đã gửi ĐMH cho KT"),
        POItem(id=3, po_id=1, product_code="SP3", line_status="",
               progress_status="Hoàn thành", status_before_pause=""),
    ])
    db.commit()
    before = _doc_n1(db) | {"n2": _doc_n2(db)}

    _dung_migration(db, n1, "upgrade")
    _dung_migration(db, n2, "upgrade")
    after = _doc_n1(db) | {"n2": _doc_n2(db)}
    assert after["item"] == ["not_delivered", "full", ""]
    assert after["n2"] == [(1, "not_ordered", ""), (2, "paused", "doc_sent"),
                         (3, "completed", "")]

    # Lùi phải theo thứ tự ngược lại, đúng như alembic downgrade.
    _dung_migration(db, n2, "downgrade")
    _dung_migration(db, n1, "downgrade")
    assert (_doc_n1(db) | {"n2": _doc_n2(db)}) == before
