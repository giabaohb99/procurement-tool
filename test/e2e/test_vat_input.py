"""CR-058 — ô VAT theo dòng: nhập số tự do, chặn ở dưới 100%.

Trước đây VAT là <select> chỉ có 0/5/8/10 (YCMH) nên thuế suất khác (vd 3,5%) không
nhập được. Test mở màn hình TẠO YCMH — không cần dữ liệu sẵn, không ghi gì vào DB —
rồi kiểm tra ô VAT: là ô nhập số, nhận giá trị ngoài danh sách cũ, và bị kẹp lại khi
gõ quá 99,99.
"""
import re

BASE_URL = "http://localhost:8080"
O_VAT = 'input[placeholder="% VAT"]'


def _mo_ycmh_moi(page):
    """Mở màn hình tạo YCMH và thêm 1 dòng hàng trống (YCMH mới không có dòng nào)."""
    page.goto(BASE_URL + "/purchase-requests/new")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.get_by_role("button", name="Thêm SP").click()
    page.wait_for_selector(O_VAT, timeout=15000)
    return page.locator(O_VAT).first


def test_vat_la_o_nhap_khong_con_select(page_req):
    """Ô VAT phải là <input> — nếu ai đó trả lại <select> thì selector này biến mất."""
    o = _mo_ycmh_moi(page_req)
    assert o.evaluate("e => e.tagName") == "INPUT"
    # Mặc định vẫn là 8%
    assert o.input_value() == "8"


def test_vat_nhan_muc_ngoai_danh_sach_cu(page_req):
    """3,5% không có trong <select> cũ (0/5/8/10) — giờ phải nhập được."""
    o = _mo_ycmh_moi(page_req)
    o.fill("3,5")
    o.blur()
    assert o.input_value() == "3,5"


def test_vat_bi_kep_duoi_100(page_req):
    """Gõ 150 → kẹp ngay về 99,99, không đợi server trả 422."""
    o = _mo_ycmh_moi(page_req)
    o.fill("150")
    o.blur()
    assert o.input_value() == "99,99"


def test_vat_khong_nhan_so_am(page_req):
    """Dấu trừ bị lọc khỏi chuỗi gõ vào → -8 thành 8, không bao giờ ra số âm."""
    o = _mo_ycmh_moi(page_req)
    o.fill("-8")
    o.blur()
    assert not re.match(r"^-", o.input_value())
