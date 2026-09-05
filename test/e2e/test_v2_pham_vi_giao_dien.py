"""E1–E6 — đi một vòng `frontend-v2` bằng tài khoản PHẠM VI HẸP (cụm 09).

⚠️ **CHƯA CHẠY LẦN NÀO.** Viết ra trong đợt stress test phân quyền
(05/09/2026) nhưng cố ý không chạy: cần stack đầy đủ + tài khoản demo, và chạy
tay trên dữ liệu local thì có nhịp bấm được vào chứng từ thật. Chạy lần đầu
phải có người ngồi xem, và phải sửa lại phần khẳng định nào bám vào câu chữ đã
đổi.

Vì sao cần dù đã có ~2400 bài Vitest: Vitest dựng từng component với dữ liệu
bịa. Nó **không** bắt được "đăng nhập bằng tài khoản hẹp rồi đi một vòng" —
đúng cái vòng mà người dùng thật đi, và là chỗ ba kiểu hỏng của giao diện phân
quyền (nút giả · giấu nhầm · rỗng mập mờ) mới lộ ra cùng lúc.

Khác `conftest.py` sẵn có ở hai điểm, nên tệp này tự dựng lấy phiên đăng nhập:
 · các fixture kia trỏ vào **`frontend/`** (cổng 8080), còn đây là **v2** (8083);
 · form đăng nhập của v2 không dùng cùng placeholder.

Chạy:
    pytest test/e2e/test_v2_pham_vi_giao_dien.py --headed -v
"""
import pytest
from playwright.sync_api import Browser, Page, expect

V2_URL = "http://localhost:8083"

#  Mật khẩu = mã tài khoản (quy ước dữ liệu demo, xem CLAUDE.md § Tests).
TAI_KHOAN_HEP = "DEMONV"  # nhân sự thu mua — phạm vi «được giao»
TAI_KHOAN_QUAN_TRI = "admin"


def v2_login(page: Page, code: str) -> None:
    page.goto(f"{V2_URL}/login")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.get_by_label("Mã nhân viên").fill(code)
    page.get_by_label("Mật khẩu").fill(code)
    page.get_by_role("button", name="Đăng nhập").click()
    page.wait_for_url(lambda url: "/login" not in url, timeout=15000)


@pytest.fixture()
def v2_hep(browser: Browser):
    context = browser.new_context()
    page = context.new_page()
    v2_login(page, TAI_KHOAN_HEP)
    yield page
    context.close()


@pytest.fixture()
def v2_quan_tri(browser: Browser):
    context = browser.new_context()
    page = context.new_page()
    v2_login(page, TAI_KHOAN_QUAN_TRI)
    yield page
    context.close()


# ───────────────────────────── E1 ─────────────────────────────

def test_e1_menu_chi_co_muc_duoc_cap(v2_hep: Page, v2_quan_tri: Page):
    """Người phạm vi hẹp thấy ÍT thẻ phân hệ hơn quản trị, và không thẻ nào khóa.

    Đo bằng SO SÁNH hai tài khoản chứ không chốt một con số: số phân hệ đổi mỗi
    lần thêm module, chốt cứng là bài kiểm chết yểu ngay tuần sau.
    """
    v2_hep.goto(f"{V2_URL}/")
    v2_hep.wait_for_load_state("networkidle")
    the_hep = v2_hep.get_by_role("link").count()

    v2_quan_tri.goto(f"{V2_URL}/")
    v2_quan_tri.wait_for_load_state("networkidle")
    the_admin = v2_quan_tri.get_by_role("link").count()

    assert the_hep > 0, "tài khoản hẹp không mở được phân hệ nào — giấu nhầm"
    assert the_hep < the_admin, "tài khoản hẹp thấy y hệt quản trị — cổng quyền không ăn"


def test_e1b_menu_trai_khong_co_muc_ngoai_quyen(v2_hep: Page):
    """Vào một phân hệ mở được thì mọi mục menu trái phải bấm được."""
    v2_hep.goto(f"{V2_URL}/procurement")
    v2_hep.wait_for_load_state("networkidle")

    muc = v2_hep.locator("nav a")
    for i in range(muc.count()):
        item = muc.nth(i)
        expect(item).to_be_enabled()


# ───────────────────────────── E2 ─────────────────────────────

def test_e2_go_thang_url_ngoai_quyen_bi_chan_tu_te(v2_hep: Page):
    """Gõ URL màn không có quyền -> trang 403 hoặc bị đá về màn chọn phân hệ.

    Sai kiểu nào cũng đáng chặn: trang TRẮNG (không biết chuyện gì), hoặc mở ra
    được rồi API bắn lỗi (nút giả cấp trang).
    """
    v2_hep.goto(f"{V2_URL}/system/settings")
    v2_hep.wait_for_load_state("networkidle")

    noi_dung = v2_hep.locator("body").inner_text()
    assert noi_dung.strip(), "trang trắng — không nói gì cả"
    bi_chan = "quyền" in noi_dung.lower() or v2_hep.url.rstrip("/").endswith(V2_URL)
    assert bi_chan, f"vào được /system/settings bằng tài khoản hẹp: {v2_hep.url}"


# ───────────────────────────── E3 ─────────────────────────────

def test_e3_chi_tiet_chung_tu_ngoai_pham_vi(v2_hep: Page):
    """Id không thuộc phạm vi -> "Không tìm thấy", không phải khung trắng.

    Backend trả 404 cho cả "không tồn tại" lẫn "ngoài phạm vi" (cố ý — trả 403
    là xác nhận bản ghi có thật).
    """
    v2_hep.goto(f"{V2_URL}/procurement/purchase-orders/999999")
    v2_hep.wait_for_load_state("networkidle")

    noi_dung = v2_hep.locator("body").inner_text().lower()
    assert "không tìm thấy" in noi_dung or "không có quyền" in noi_dung, noi_dung[:400]


# ───────────────────────────── E4 ─────────────────────────────

def test_e4_doi_pham_vi_co_hieu_luc_sau_khi_dang_nhap_lai(v2_quan_tri: Page, browser: Browser):
    """Sửa phạm vi ở màn Phân quyền -> đăng nhập lại thấy đổi.

    ⚠️ Nối C1 cụm 08: hồ sơ quyền có bộ nhớ đệm 60 giây trong tiến trình
    (`_PERM_CACHE` ở `core/auth.py`) và mọi lần đổi vai trò/phân quyền PHẢI gọi
    `perm_cache_clear(user_id)`. Quên gọi thì đổi xong tới một phút sau mới ăn —
    đúng quãng người khai quyền đang ngồi thử lại và kết luận "sửa không được".

    TODO khi chạy lần đầu: thao tác thật trên `/hr/users/<id>` (mở hộp Phạm vi,
    bỏ tick một phòng, Lưu) rồi mở context mới đăng nhập bằng tài khoản đó.
    Chưa viết sẵn vì nó GHI vào dữ liệu, phải chọn đúng tài khoản demo dùng một
    lần chứ không đụng vào tài khoản các bài khác đang dùng.
    """
    pytest.skip("cần chọn tài khoản demo dùng một lần — xem docstring")


# ───────────────────────────── E5 ─────────────────────────────

VONG_DI = [
    "/",
    "/procurement",
    "/procurement/purchase-requests",
    "/procurement/purchase-orders",
    "/hr/leave-requests",
]


def test_e5_khong_man_nao_co_403_khong_duoc_xu(v2_hep: Page):
    """Đi một vòng: không lỗi console, và không lời gọi 403 nào bị nuốt.

    403 trên GET **không bật toast** (`core/api/http-client.ts` — chỉ toast cho
    POST/PATCH/PUT/DELETE). Nên một màn bắn 403 rồi hiện bảng rỗng là hoàn toàn
    im lặng với người dùng; chỗ duy nhất nhìn thấy nó là tab Network.
    """
    loi_console: list[str] = []
    ba_khong_ba: list[str] = []

    v2_hep.on("console", lambda m: loi_console.append(m.text) if m.type == "error" else None)
    v2_hep.on(
        "response",
        lambda r: ba_khong_ba.append(f"{r.request.method} {r.url}") if r.status == 403 else None,
    )

    for duong in VONG_DI:
        v2_hep.goto(f"{V2_URL}{duong}")
        v2_hep.wait_for_load_state("networkidle", timeout=15000)

    assert ba_khong_ba == [], f"màn hình gọi API ngoài quyền: {ba_khong_ba}"
    assert loi_console == [], f"lỗi console: {loi_console}"


# ───────────────────────────── E6 ─────────────────────────────

def test_e6_bang_rong_luon_kem_cau_giai_thich(v2_hep: Page):
    """Bảng không có dòng nào thì phải có chữ, không được để ô trống.

    Chống 09-C: "không có dữ liệu" · "ngoài phạm vi" · "không có quyền" là ba
    tình huống khác hẳn nhau mà hôm nay nhìn giống hệt nhau.
    """
    for duong in ("/procurement/purchase-requests", "/procurement/purchase-orders"):
        v2_hep.goto(f"{V2_URL}{duong}")
        v2_hep.wait_for_load_state("networkidle", timeout=15000)

        so_dong = v2_hep.locator("tbody tr").count()
        if so_dong > 1:
            continue  # có dữ liệu, không phải ca cần kiểm

        chu = v2_hep.locator("tbody").inner_text().strip()
        assert chu, f"{duong}: bảng rỗng mà không một chữ nào"
