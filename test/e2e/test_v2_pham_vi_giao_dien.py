"""E1–E6 — đi một vòng `frontend-v2` bằng tài khoản PHẠM VI HẸP (cụm 09).

Viết 05/09/2026 trong đợt stress test phân quyền, **chạy lần đầu 19/09/2026**:
6 xanh · 1 bỏ qua (E4) trong 54s. Bốn chỗ phải sửa để chạy được, ghi lại vì cả
bốn đều là bẫy sẽ gặp lại khi viết bài E2E mới cho v2:
 · form đăng nhập v2 không có `<label>` -> `get_by_label` treo (xem `v2_login`);
 · vào route LẦN ĐẦU thì Vite dev mới dịch, quá 30s mặc định (xem `CHO_MS`);
 · `count()` không chờ như `expect` (xem `dem_the_phan_he`);
 · màn bị cổng quyền chặn thì không vẽ bảng nào (xem E6).

⚠️ Chạy cả 7 bài một lượt lúc máy đang gánh 11 container + route chưa ấm thì
driver Playwright chết giữa chừng ("Connection closed while reading from the
driver"). Ấm rồi thì cả tệp 54s. Kẹt thì chạy lẻ từng bài.

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

#  Vào một route LẦN ĐẦU thì Vite dev mới dịch cả nhánh module đó, đo được
#  >30s trên máy đang chạy 11 container — quá mức chờ mặc định của Playwright.
#  Lần thứ hai chỉ còn ~4s. Nên mọi chỗ chờ ở tệp này phải tự đặt mức chờ,
#  đừng để mặc định, kẻo bài kiểm đỏ vì máy chậm chứ không phải vì giao diện sai.
CHO_MS = 90000


def cho_man(page: Page, timeout: int = CHO_MS) -> None:
    page.wait_for_load_state("networkidle", timeout=timeout)


def dem_the_phan_he(page: Page) -> int:
    """Đếm thẻ phân hệ ở màn chọn phân hệ.

    `count()` chụp ngay lập tức, KHÔNG chờ như `expect`. Mạng rảnh rồi mà React
    chưa vẽ xong thì đếm ra 0 — đo được: cùng một bài, lần đỏ «0 thẻ» lần xanh
    «15 thẻ». Nên phải chờ thẻ đầu tiên hiện đã rồi mới đếm.
    """
    page.goto(f"{V2_URL}/")
    cho_man(page)
    page.get_by_role("link").first.wait_for(state="visible", timeout=CHO_MS)
    return page.get_by_role("link").count()


#  Mật khẩu = mã tài khoản (quy ước dữ liệu demo, xem CLAUDE.md § Tests).
TAI_KHOAN_HEP = "DEMONV"  # nhân sự thu mua — phạm vi «được giao»
TAI_KHOAN_QUAN_TRI = "admin"

#  Câu của màn chặn quyền cả trang (`core/auth` — trang 403 thay cho nội dung).
CHU_CHAN_QUYEN = "không có quyền truy cập"


def v2_login(page: Page, code: str) -> None:
    page.goto(f"{V2_URL}/login")
    cho_man(page)
    #  Form đăng nhập v2 KHÔNG có <label> — hai ô chỉ mang `placeholder`, nên
    #  `get_by_label` treo tới hết giờ chờ. Đây đúng là chỗ tệp này dự là sẽ
    #  lệch: xem ghi chú đầu tệp.
    page.get_by_placeholder("Mã nhân viên").fill(code)
    page.get_by_placeholder("Mật khẩu").fill(code)
    page.get_by_role("button", name="Đăng nhập").click()
    page.wait_for_url(lambda url: "/login" not in url, timeout=CHO_MS)


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
    the_hep = dem_the_phan_he(v2_hep)
    the_admin = dem_the_phan_he(v2_quan_tri)

    assert the_hep > 0, "tài khoản hẹp không mở được phân hệ nào — giấu nhầm"
    assert the_hep < the_admin, "tài khoản hẹp thấy y hệt quản trị — cổng quyền không ăn"


def test_e1b_menu_trai_khong_co_muc_ngoai_quyen(v2_hep: Page):
    """Vào một phân hệ mở được thì mọi mục menu trái phải bấm được."""
    v2_hep.goto(f"{V2_URL}/procurement")
    cho_man(v2_hep)

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
    cho_man(v2_hep)

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
    cho_man(v2_hep)

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
        cho_man(v2_hep)

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
        cho_man(v2_hep)

        than = v2_hep.locator("body").inner_text()
        if CHU_CHAN_QUYEN in than.lower():
            #  Cổng quyền chặn hẳn cả màn, không vẽ bảng nào — đã có câu giải
            #  thích riêng và E2 lo ca đó. Đo 19/09: `DEMONV` vào Đơn mua hàng
            #  rơi đúng nhánh này.
            continue

        bang = v2_hep.locator("table tbody").first
        bang.wait_for(state="visible", timeout=CHO_MS)
        chu = bang.inner_text().strip()
        assert chu, f"{duong}: bảng rỗng mà không một chữ nào"
