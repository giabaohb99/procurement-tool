"""
test_print_filename.py — CR-057: tên file mặc định khi lưu phiếu in ra PDF.

Hộp thoại "Save As" do hệ điều hành vẽ nên Playwright không mở được; thứ DUY NHẤT trang web
điều khiển được là `document.title` — trình duyệt và máy in ảo (Foxit, Microsoft Print to PDF)
lấy đúng chuỗi đó làm tên file gợi ý. Vậy nên test kiểm `document.title`, không kiểm hộp thoại.

Phủ cả 4 phiếu in: 2 phiếu của ĐMH, phiếu YCMH và phiếu YCTT.

Cần: stack đang chạy + trong DB có chứng từ để in. Loại nào chưa có chứng từ thì skip chứ
không fail — môi trường sạch không phải là lỗi của tính năng này.
"""
import re

import pytest
from playwright.sync_api import Page

from conftest import BASE_URL

TIEU_DE_MAC_DINH = "Thu Mua Tool"

# (tên gọi, route trang in, endpoint danh sách, cột ngày dùng để đặt tên file)
PHIEU = [
    ("ĐMH — Đơn đặt hàng", "purchase-order", "/api/purchase-orders", "order_date"),
    ("ĐMH — Đơn mua hàng", "purchase-order-mh", "/api/purchase-orders", "order_date"),
    ("YCMH", "purchase-request", "/api/purchase-requests", "request_date"),
    ("YCTT", "payment-request", "/api/payment-requests", "request_date"),
]

DANG_TEN = re.compile(r"^[A-Za-z0-9]+-\d{8}$")


def _mot_chung_tu(page: Page, endpoint: str) -> dict:
    """Lấy 1 chứng từ bất kỳ qua API (dùng token đang có trong localStorage)."""
    r = page.evaluate(
        """async (ep) => {
            const t = localStorage.getItem('token')
            const res = await fetch(ep + '?page=1&page_size=1',
                                    { headers: { Authorization: 'Bearer ' + t } })
            return await res.json()
        }""",
        endpoint,
    )
    items = ((r or {}).get("data") or {}).get("items") or []
    if not items:
        pytest.skip(f"DB chưa có chứng từ nào ở {endpoint}")
    return items[0]


def _mo_trang_in(page: Page, route: str, doc_id) -> str:
    page.goto(f"{BASE_URL}/print/{route}/{doc_id}")
    page.wait_for_function(
        "() => document.title && document.title !== 'Thu Mua Tool'", timeout=15000)
    return page.title()


class TestTenFilePhieuIn:
    @pytest.mark.parametrize("name,route,endpoint,date_col", PHIEU,
                             ids=[p[1] for p in PHIEU])
    def test_tieu_de_la_ma_chung_tu_va_ngay(self, page_admin: Page, name, route,
                                            endpoint, date_col):
        """Mọi phiếu in đều đặt tiêu đề tab = <mã chứng từ>-DDMMYYYY."""
        ct = _mot_chung_tu(page_admin, endpoint)
        title = _mo_trang_in(page_admin, route, ct["id"])
        assert DANG_TEN.match(title), f"{name}: sai dạng <mã>-DDMMYYYY: {title!r}"
        assert title.startswith(ct["code"] + "-"), f"{name}: không bắt đầu bằng mã chứng từ"
        # Ngày trong tên file phải là NGÀY CHỨNG TỪ, không phải ngày in (bug dễ mắc nhất).
        y, m, d = ct[date_col].split("-")
        assert title.endswith(f"{d}{m}{y}"), f"{name}: ngày trong tên file không phải {date_col}"

    def test_ma_misa_khong_lam_ten_file(self, page_admin: Page):
        """Đơn nhập từ hệ thống cũ có mã MISA vẫn phải lấy Mã PO — mã MISA trùng nhau
        giữa các đơn nên đặt tên theo nó sẽ ghi đè file của nhau."""
        po = page_admin.evaluate("""async () => {
            const t = localStorage.getItem('token')
            const res = await fetch('/api/purchase-orders?page=1&page_size=200',
                                    { headers: { Authorization: 'Bearer ' + t } })
            const j = await res.json()
            return ((j.data || {}).items || []).find(x => x.misa_code) || null
        }""")
        if not po:
            pytest.skip("Không có đơn nào mang mã MISA")
        title = _mo_trang_in(page_admin, "purchase-order", po["id"])
        assert title.startswith(po["code"] + "-")
        assert po["misa_code"] not in title

    def test_roi_trang_in_thi_tra_lai_tieu_de(self, page_admin: Page):
        """Rời trang in -> tiêu đề về mặc định, không kẹt tên chứng từ ở tab chính."""
        po = _mot_chung_tu(page_admin, "/api/purchase-orders")
        _mo_trang_in(page_admin, "purchase-order", po["id"])
        page_admin.goto(f"{BASE_URL}/purchase-orders")
        page_admin.wait_for_function(
            f"() => document.title === '{TIEU_DE_MAC_DINH}'", timeout=15000)
