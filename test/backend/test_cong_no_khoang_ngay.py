"""Lọc công nợ theo KHOẢNG NGÀY (`due_from`/`due_to`, `incur_from`/`incur_to`).

Khách nêu 31/08/2026: "cần thanh toán từ ngày tới ngày trên một nhà cung cấp". Trước đó
màn Công nợ chỉ lọc được theo NĂM và theo nhóm tuổi nợ, nên câu hỏi kỳ chi tiền không
trả lời được.

Bốn chỗ dễ hỏng, cũng là bốn nhóm test dưới đây:

  1. **`due_date` rỗng.** Cột lưu chuỗi, mà `"" <= "2026-08-31"` là ĐÚNG trong SQL. Không
     chặn thì mọi khoản chưa có hạn trả đều lọt vào mọi khoảng ngày — kế toán tưởng kỳ
     này phải trả thêm mấy chục khoản.
  2. **Nửa khoảng.** "Từ 01/08 tới nay" là câu hỏi có thật, không được ép phải đủ cặp.
  3. **Hai mốc lệch nhau thật.** Hàng nhận tháng 7 mà công nợ 30 ngày thì hạn trả rơi
     sang tháng 8; lọc nhầm mốc là ra tập khác hẳn chứ không phải lệch vài dòng.
  4. **Bẫy `year`.** `_filtered` mặc định kẹp theo NĂM HIỆN TẠI khi không nhận `year`,
     nên khoảng vắt qua giao thừa trả về RỖNG mà không báo gì. Giao diện phải tự ép
     `year=all`; test cuối cùng canh đúng cái bẫy đó.
"""
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.modules.payable import controller as pay_ctrl
from app.modules.payable.model import Payable
from app.modules.user.model import User


def _request(qs: str = ""):
    """`_filtered` chỉ đọc `query_params`, không cần dựng Request thật."""
    return SimpleNamespace(query_params=QueryParams(qs))


@pytest.fixture
def khoan_no(db, seed):
    """Sáu khoản: hạn trả rải tháng 8-9/2026, một khoản CHƯA có hạn, một khoản năm 2025."""
    rows = [
        # (mã ĐMH, ngày phát sinh, hạn trả, năm)
        ("PO-01", "2026-07-05", "2026-08-05", "2026"),
        ("PO-02", "2026-07-20", "2026-08-20", "2026"),
        ("PO-03", "2026-08-01", "2026-08-31", "2026"),
        ("PO-04", "2026-08-10", "2026-09-10", "2026"),
        ("PO-05", "2026-08-15", "", "2026"),          # chưa có hạn trả
        ("PO-06", "2025-12-01", "2025-12-31", "2025"),
    ]
    objs = [
        Payable(company_id=seed.company_id, supplier_code="NCCA", supplier_name="NCC Anpha",
                source_type="goods", po_code=po, incur_date=incur, due_date=due, period=period,
                total=1000, paid_amount=0, remaining=1000, status="unpaid")
        for po, incur, due, period in rows
    ]
    db.add_all(objs)
    db.commit()
    return objs


@pytest.fixture
def loc(db, seed, grant_role, khoan_no):
    """Trả về hàm lọc, đứng ở tư thế người dùng có `payable.read` phạm vi toàn hệ."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)

    def _loc(qs: str) -> set[str]:
        q = pay_ctrl._filtered(db, _request(qs), user)
        return {p.po_code for p in q.all()}

    return _loc


# ── Khoảng hạn trả ──────────────────────────────────────────────────────────────
def test_khoang_han_tra_lay_dung_hai_dau_mut(loc):
    """Bao gồm cả hai đầu: kế toán gõ 01/08 - 31/08 là muốn CẢ khoản đến hạn đúng 31/08."""
    assert loc("year=all&due_from=2026-08-01&due_to=2026-08-31") == {"PO-01", "PO-02", "PO-03"}


def test_chua_co_han_tra_khong_lot_vao_khoang(loc):
    """`due_date` rỗng so chuỗi thì bé hơn mọi ngày, không chặn là nó lọt vào MỌI khoảng."""
    assert "PO-05" not in loc("year=all&due_to=2026-12-31")
    assert "PO-05" not in loc("year=all&due_from=2020-01-01&due_to=2030-12-31")


def test_nua_khoang_van_chay(loc):
    """"Từ 01/09 tới nay" và "tới hết 20/08" đều là câu hỏi có thật."""
    assert loc("year=all&due_from=2026-09-01") == {"PO-04"}
    assert loc("year=all&due_to=2026-08-20") == {"PO-01", "PO-02", "PO-06"}


def test_khoang_lon_nguoc_thi_ra_rong_chu_khong_no(loc):
    """Người dùng chọn ngược đầu (từ 31/08 tới 01/08) — phải rỗng, không được ném lỗi."""
    assert loc("year=all&due_from=2026-08-31&due_to=2026-08-01") == set()


def test_hai_dau_trung_nhau_la_dung_mot_ngay(loc):
    assert loc("year=all&due_from=2026-08-20&due_to=2026-08-20") == {"PO-02"}


# ── Khoảng ngày phát sinh ───────────────────────────────────────────────────────
def test_moc_phat_sinh_ra_tap_khac_han_moc_han_tra(loc):
    """Nhận hàng tháng 7, công nợ 30 ngày -> hạn trả sang tháng 8. Chọn nhầm mốc là ra tập
    khác hẳn chứ không lệch vài dòng, nên giao diện phải cho chọn mốc rõ ràng."""
    theo_phat_sinh = loc("year=all&incur_from=2026-07-01&incur_to=2026-07-31")
    theo_han_tra = loc("year=all&due_from=2026-07-01&due_to=2026-07-31")

    assert theo_phat_sinh == {"PO-01", "PO-02"}
    assert theo_han_tra == set()


def test_hai_moc_gui_cung_luc_thi_giao_nhau(loc):
    """Không phải hợp: gửi cả hai là siết thêm điều kiện, không nới ra."""
    assert loc("year=all&incur_from=2026-08-01&due_from=2026-09-01") == {"PO-04"}


# ── Bẫy `year` ──────────────────────────────────────────────────────────────────
def test_khoang_vat_qua_giao_thua_bi_nam_hien_tai_nuot_mat(loc):
    """LÝ DO giao diện ép `year=all` khi có khoảng ngày (`payable-list-page.tsx`).

    Không gửi `year` thì backend kẹp theo NĂM HIỆN TẠI. Khoảng 12/2025 - 01/2026 vì thế
    trả về rỗng mà không báo gì — người dùng tưởng kỳ đó không nợ ai đồng nào."""
    qs = "due_from=2025-12-01&due_to=2026-01-31"
    assert loc(qs) == set()                      # bẫy: năm hiện tại nuốt mất khoản 2025
    assert loc(f"year=all&{qs}") == {"PO-06"}    # ép `year=all` mới ra đúng


def test_khong_gui_khoang_thi_khong_loc_ngay(loc):
    """Chuỗi rỗng phải bị bỏ qua như không gửi, kẻo bảng rỗng ngay lúc mở màn."""
    assert loc("year=all&due_from=&due_to=") == {
        "PO-01", "PO-02", "PO-03", "PO-04", "PO-05", "PO-06",
    }
