"""B-05 — `tab_payable.status` chuyển sang MÃ tiếng Anh.

Đợt thứ năm của kế hoạch đổ bê tông nền v2 (`doc/erp/15-do-be-tong-nen-v2.md` §3). Khác bốn
đợt trước ở một điểm: **cột này dính tiền**. Kế hoạch nói thẳng điều kiện đủ của đợt không
phải "màn hình chạy được" mà là *tổng công nợ theo từng nhà cung cấp trước và sau phải khớp
từng đồng* — đây chính là cột từng gây sự cố công nợ âm (fix `82ce6ad`).

Bốn nhóm rủi ro, cũng là bốn nhóm test dưới đây:

  1. **Không đồng nào được đổi.** Migration chỉ UPDATE một cột chữ. Có test đối chiếu tổng
     theo từng NCC trước/sau, cả chiều lên lẫn chiều xuống.
  2. **Trạng thái là HÀM của hai số tiền**, không phải người dùng chọn: `recalc_status` tính
     lại sau mỗi lần phân bổ thanh toán. Nghĩa là anh xạ sai một giá trị thì lần phân bổ kế
     tiếp TỰ GHI ĐÈ cho đúng — lỗi biến khỏi màn hình nhưng số liệu lịch sử đã lệch. Và vì
     nó lùi được (`paid` -> `partial`) nên không mã nào được đánh `is_terminal`.
  3. **Năm chỗ NGOÀI phân hệ so sánh với `paid`** để loại nợ đã tất toán. Sót một chỗ là chỗ
     đó im lặng trả ra số tiền sai chứ không nổ.
  4. **"Trả dư" không phải một giá trị của cột này.** Nó chỉ sống ở tầng hiển thị của
     `frontend/`, suy từ `remaining < 0`. Lọt vào bộ mã là mời người sau ghi nó xuống DB.
"""
import importlib.util
import inspect
from pathlib import Path

import pytest

from app.core.status_codes import PAYABLE_STATUS
from app.modules.payable import controller as pay_ctrl
from app.modules.payable import service as pay_svc
from app.modules.payable.model import Payable


# ── Bộ mã ───────────────────────────────────────────────────────────────────────
def test_ma_la_ascii_thuong_va_khong_trung():
    """Cột lưu MÃ. Lọt tiếng Việt vào đây là quay lại đúng cái mớ vừa dọn."""
    for c in PAYABLE_STATUS.codes:
        assert c.value.isascii() and c.value.islower(), c
        assert c.label, c
    assert len(set(PAYABLE_STATUS.values)) == len(PAYABLE_STATUS.values)


def test_khong_ma_nao_la_trang_thai_ket():
    """`paid` trông như đích đến nhưng không phải: thêm hóa đơn vào một khoản đã tất toán là
    `recalc_status` đưa nó về `partial`. Đánh `is_terminal` ở đây thì màn hình nào tin vào cờ
    đó (khóa dòng, ẩn khỏi danh sách cần xử lý) sẽ giấu mất khoản nợ vừa sống lại."""
    for v in PAYABLE_STATUS.values:
        assert not PAYABLE_STATUS.is_terminal(v), v


def test_thu_tu_la_chuoi_tien_trinh_that_theo_muc_da_tra():
    """Khác B-02/B-03/B-04 nơi `sort_order` chỉ là thứ tự hiển thị: ở đây nó có nghĩa thật
    (chưa trả -> trả một phần -> trả đủ) nên dùng được để sắp cột."""
    assert PAYABLE_STATUS.ordered_values == ("unpaid", "partial", "paid")


def test_tra_du_khong_nam_trong_bo_ma():
    """"Trả dư" là trạng thái CHỈ ĐỂ HIỆN của `frontend/supplier-payables-stats.ts`, tính tại
    chỗ từ `remaining < 0`, chưa bao giờ được ghi xuống cột này. Đưa vào bộ mã là sớm muộn có
    người gửi nó lên làm tham số lọc — backend không có dòng nào mang giá trị đó nên bảng rỗng
    mà không báo lỗi gì."""
    assert not any("dư" in c.label.lower() or "du" == c.value for c in PAYABLE_STATUS.codes)
    assert set(PAYABLE_STATUS.values) == {"unpaid", "partial", "paid"}


# ── Tầng ghi: recalc_status ─────────────────────────────────────────────────────
def _p(total, paid):
    return Payable(total=total, paid_amount=paid)


@pytest.mark.parametrize("total,paid,cho_ra", [
    (1_000_000, 0,          "unpaid"),
    (1_000_000, 400_000,    "partial"),
    (1_000_000, 1_000_000,  "paid"),
    (1_000_000, 1_200_000,  "paid"),    # trả dư vẫn là `paid` ở DB — "Trả dư" chỉ ở màn hình
    (1_000_000, -50_000,    "unpaid"),  # điều chỉnh giảm phần đã trả
])
def test_trang_thai_suy_tu_hai_so_tien(total, paid, cho_ra):
    p = _p(total, paid)
    pay_svc.recalc_status(p)
    assert p.status == cho_ra


def test_chi_ghi_ma_nam_trong_bo_ma():
    """Chốt chặn cuối: bất kỳ tổ hợp tiền nào cũng chỉ ra được mã hợp lệ."""
    for total, paid in [(0, 0), (-500, 0), (100, 99.995), (100, 100.5), (1e9, 1e9)]:
        p = _p(total, paid)
        pay_svc.recalc_status(p)
        assert p.status in PAYABLE_STATUS.values, (total, paid, p.status)


def test_tra_gan_du_van_la_da_tra_du_nguong_mot_xu():
    """Ngưỡng 0.01 có từ trước B-05 và phải giữ: lệch một xu do làm tròn VAT mà kẹt ở
    `partial` là khoản nợ đó nằm mãi trong danh sách quá hạn."""
    p = _p(1_000_000, 999_999.995)
    pay_svc.recalc_status(p)
    assert p.status == "paid"


def test_khoan_da_tat_toan_bi_them_hoa_don_thi_lui_lai():
    """Chính là lý do không mã nào là trạng thái kết."""
    p = _p(1_000_000, 1_000_000)
    pay_svc.recalc_status(p)
    assert p.status == "paid"
    p.total = 1_500_000            # thêm hóa đơn vào cùng khoản
    pay_svc.recalc_status(p)
    assert p.status == "partial"
    assert float(p.remaining) == 500_000


def test_mac_dinh_cua_cot_la_ma_chu_khong_phai_chu(db):
    """Mặc định của cột chỉ áp lúc INSERT, nên chỉ thấy được sau khi ghi xuống DB. Để sót chữ
    "Chờ TT" ở đây là mọi dòng công nợ sinh ngầm sau ngày cắt lại mang giá trị tiếng Việt."""
    db.add(Payable(supplier_code="NCC1", total=100, paid_amount=0))
    db.commit()
    assert db.query(Payable).one().status == "unpaid"


# ── Tầng đọc: nhãn đi kèm mã ────────────────────────────────────────────────────
def test_api_gan_san_nhan_tieng_viet(db):
    """Giao diện KHÔNG được tự dịch mã sang tiếng Việt. Quên gắn nhãn ở `_out()` là cột hiện
    `unpaid` giữa màn tiếng Việt mà không lỗi gì cả."""
    p = Payable(supplier_code="NCC1", total=1_000_000, paid_amount=400_000, due_date="")
    pay_svc.recalc_status(p)
    db.add(p)
    db.commit()

    ra = pay_ctrl._out(db, p)
    assert ra["status"] == "partial"
    assert ra["status_label"] == "Thanh toán một phần"


def test_ma_la_khong_bi_nuot_mat():
    """Dòng chưa chạy migration (hoặc do nơi khác ghi vào) vẫn phải đọc được: trả rỗng là
    người dùng tưởng khoản nợ không có trạng thái nào."""
    assert pay_svc.status_label("Đã TT") == "Đã TT"
    assert pay_svc.status_label("") == ""
    assert pay_svc.status_label("paid") == "Đã thanh toán"


def test_nam_cho_ngoai_phan_he_dung_hang_chu_khong_go_chuoi():
    """Năm chỗ này so sánh với `paid` để loại nợ đã tất toán. Gõ thẳng chuỗi ở từng chỗ là lần
    sau đổi mã sẽ sót đúng một chỗ, mà chỗ sót đó trả ra SỐ TIỀN sai chứ không nổ."""
    from app.modules.alert import controller as alert_ctrl
    from app.modules.dashboard import controller as dash_ctrl
    from app.modules.report import controller as report_ctrl

    assert pay_svc.ST_PAID == "paid"
    for mod, ten in [(alert_ctrl, "alert"), (dash_ctrl, "dashboard"),
                     (report_ctrl, "report"), (pay_ctrl, "payable")]:
        src = inspect.getsource(mod)
        assert "Đã TT" not in src, f"{ten}/controller.py còn so sánh với chữ tiếng Việt"
        assert "ST_PAID" in src, f"{ten}/controller.py không dùng hằng ST_PAID"


# ── Migration ───────────────────────────────────────────────────────────────────
_TEN_MIG = "f8c4a02b6d39_b05_chuan_hoa_payable_status.py"


def _nap_migration():
    duong_dan = Path(__file__).resolve().parents[2] / "migrations" / "versions" / _TEN_MIG
    if not duong_dan.exists():   # chạy trong container: /app/test/backend + /app/migrations
        duong_dan = Path("/app/migrations/versions") / _TEN_MIG
    spec = importlib.util.spec_from_file_location("mig_b05", duong_dan)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _dung_migration(db, mig, chieu: str) -> None:
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    ctx = MigrationContext.configure(db.connection())
    with Operations.context(ctx):
        getattr(mig, chieu)()
    db.expire_all()


def _doc(db) -> dict:
    return {p.invoice_no: p.status for p in db.query(Payable).order_by(Payable.invoice_no).all()}


def _tong_theo_ncc(db) -> dict:
    """Tổng công nợ theo từng NCC — chính là số kế hoạch bắt phải khớp từng đồng."""
    ra: dict[str, tuple] = {}
    for p in db.query(Payable).all():
        t, pa, r = ra.get(p.supplier_code, (0.0, 0.0, 0.0))
        ra[p.supplier_code] = (t + float(p.total or 0), pa + float(p.paid_amount or 0),
                               r + float(p.remaining or 0))
    return ra


def _nap_du_lieu_cu(db, cap):
    """cap = [(số hóa đơn, mã NCC, chữ tiếng Việt cũ, total, paid)]"""
    for inv, ncc, st, total, paid in cap:
        db.add(Payable(invoice_no=inv, supplier_code=ncc, supplier_name=ncc,
                       total=total, paid_amount=paid, remaining=round(total - paid, 2),
                       status=st))
    db.commit()


_MAU = [
    ("HD01", "NCC-A", "Chờ TT",        1_000_000, 0),
    ("HD02", "NCC-A", "Trả một phần",  2_000_000, 800_000),
    ("HD03", "NCC-A", "Đã TT",         3_000_000, 3_000_000),
    ("HD04", "NCC-B", "Đã TT",           500_000, 600_000),   # trả dư: remaining âm
    ("HD05", "NCC-B", "Chờ TT",         -250_000, 0),          # điều chỉnh giảm: total âm
]


def test_khop_theo_dang_chuan_hoa_chu_khong_khop_tuyet_doi():
    """Khớp tuyệt đối thì một dấu cách thừa hay một chữ hoa lệch là lọt lưới, và dòng đó nằm
    im trong CSDL với giá trị tiếng Việt cho tới lúc có người lọc không ra."""
    mig = _nap_migration()
    doi = lambda s: mig._MAP.get(mig._norm(s))   # noqa: E731

    assert doi("Chờ TT") == "unpaid"
    assert doi("  CHỜ TT ") == "unpaid"
    assert doi("cho tt") == "unpaid"                  # bản gõ không dấu
    assert doi("Trả một phần") == "partial"
    assert doi("tra  mot   phan") == "partial"
    assert doi("Đã TT") == "paid"
    # Chữ đầy đủ chưa bao giờ nằm trong DB, nhưng bản v2 hiện nó trên màn hình nên chỉ cần một
    # lần ai đó copy từ giao diện vào script sửa tay là có. Nhận thêm cho chắc.
    assert doi("Đã thanh toán") == "paid"
    assert doi("Chờ duyệt") is None                   # không đoán bừa, giữ nguyên + in log


def test_bang_nhan_chieu_xuong_tra_lai_chu_VIET_TAT_chu_khong_phai_nhan_bo_ma():
    """CẢ BA mã đều lệch giữa `_LABEL` và nhãn bộ mã — khác B-04 nơi chỉ lệch một dòng.

    `downgrade()` phải trả về ĐÚNG THỨ CSDL đang có trước khi chạy, mà thứ đó là chữ viết tắt
    ("Chờ TT"). Nhãn trong `status_codes.py` là chữ đầy đủ ("Chờ thanh toán") — chưa từng nằm
    trong CSDL bao giờ. Lấy nhãn từ catalogue mà trả về là hỏng cả ba."""
    mig = _nap_migration()
    assert mig._LABEL == {"unpaid": "Chờ TT", "partial": "Trả một phần", "paid": "Đã TT"}
    assert set(mig._LABEL) == set(PAYABLE_STATUS.values)
    for ma, chu in mig._LABEL.items():
        assert chu != PAYABLE_STATUS.label_of(ma), ma


def test_doi_het_ba_gia_tri(db):
    mig = _nap_migration()
    _nap_du_lieu_cu(db, _MAU)
    _dung_migration(db, mig, "upgrade")
    assert _doc(db) == {"HD01": "unpaid", "HD02": "partial", "HD03": "paid",
                        "HD04": "paid", "HD05": "unpaid"}


def test_khong_dong_nao_doi_so_tien(db):
    """ĐIỀU KIỆN ĐỦ của đợt (doc/erp/15 §3, B-05): tổng công nợ theo TỪNG NCC trước và sau
    phải khớp từng đồng — cả chiều lên lẫn chiều xuống. Đây là cột từng gây sự cố công nợ âm
    (fix 82ce6ad), nên "màn hình chạy được" không phải bằng chứng."""
    mig = _nap_migration()
    _nap_du_lieu_cu(db, _MAU)
    truoc = _tong_theo_ncc(db)

    _dung_migration(db, mig, "upgrade")
    assert _tong_theo_ncc(db) == truoc

    _dung_migration(db, mig, "downgrade")
    assert _tong_theo_ncc(db) == truoc


def test_chay_xuoi_roi_nguoc_tra_ve_dung_tung_ky_tu(db):
    """Điều kiện thứ ba của QĐ-12: `downgrade()` khôi phục byte-exact."""
    mig = _nap_migration()
    _nap_du_lieu_cu(db, _MAU)
    truoc = _doc(db)

    _dung_migration(db, mig, "upgrade")
    assert truoc != _doc(db)
    _dung_migration(db, mig, "downgrade")
    assert _doc(db) == truoc


def test_gia_tri_la_giu_nguyen_chu_khong_doan_bua(db):
    """Giá trị không nhận ra phải nằm im + in log. Đoán bừa trên cột này là ghi sai một khoản
    tiền có thật; giữ nguyên thì nó lộ ra ngay lần lọc đầu tiên."""
    mig = _nap_migration()
    _nap_du_lieu_cu(db, [("HD09", "NCC-X", "Trạng thái lạ", 1000, 0)])
    _dung_migration(db, mig, "upgrade")
    assert _doc(db) == {"HD09": "Trạng thái lạ"}


def test_chay_theo_lo_khong_bo_sot_dong_nao(db, monkeypatch):
    """Lô cắt theo KHOẢNG ID nên id thưa (dòng đã xóa) là chỗ dễ sai cận nhất. Sai cận thì
    dòng bị bỏ sót một cách im lặng — không lỗi, chỉ là vài khoản nợ còn chữ tiếng Việt."""
    mig = _nap_migration()
    monkeypatch.setattr(mig, "CO_LO", 2)
    for i in (1, 2, 3, 50, 51, 90, 91):
        db.add(Payable(id=i, invoice_no=f"HD{i:03d}", supplier_code="NCC-A",
                       total=1000, paid_amount=0, remaining=1000, status="Chờ TT"))
    db.commit()

    _dung_migration(db, mig, "upgrade")
    assert set(_doc(db).values()) == {"unpaid"}
    assert len(_doc(db)) == 7


@pytest.mark.parametrize("chieu", ["upgrade", "downgrade"])
def test_bang_rong_khong_no(db, chieu):
    """Môi trường mới dựng chưa có công nợ nào."""
    mig = _nap_migration()
    _dung_migration(db, mig, chieu)
    assert _doc(db) == {}
