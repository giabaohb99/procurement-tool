"""
helpers.py — Hàm tiện ích dùng chung cho các test E2E.
"""
import time
import re
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8080"


# ---------------------------------------------------------------------------
# react-select / SearchSelect helpers
# ---------------------------------------------------------------------------

def click_rs_control_by_label(page: Page, label_text: str,
                               container_selector: str = "body") -> None:
    """
    Click vào react-select control (SearchSelect) trong form-row có label chứa
    label_text.  Dùng JS evaluate để tránh bị 'div[data-value]' chặn pointer event.

    Sau khi gọi xong → có thể dùng page.keyboard.type() để lọc option.
    """
    page.evaluate(f"""
    (() => {{
        const container = document.querySelector('{container_selector}') || document.body;
        const rows = container.querySelectorAll('.form-row');
        for (const row of rows) {{
            const label = row.querySelector('label');
            if (!label) continue;
            if (!label.textContent.includes('{label_text}')) continue;
            // Tìm react-select control div
            const ctrl = row.querySelector('[class*="-control"]');
            if (ctrl) {{
                ctrl.dispatchEvent(new MouseEvent('mousedown', {{bubbles: true}}));
                ctrl.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
                const inp = row.querySelector('div[data-value]') || row.querySelector('input[type="text"]');
                if (inp) {{ inp.focus(); }}
                return;
            }}
        }}
    }})()
    """)
    page.wait_for_timeout(350)


def pick_rs_option(page: Page, option_text: str, exact: bool = False) -> None:
    """
    Click option trong react-select (options render trong document.body qua portal).
    Gọi sau khi dropdown đã mở và đã keyboard.type() để lọc.
    """
    page.wait_for_timeout(600)
    opt = page.get_by_role("option", name=option_text, exact=exact)
    count = opt.count()
    if count > 0:
        opt.first.click()
    else:
        # Thử không có gì → Enter chọn item đầu tiên
        page.keyboard.press("Enter")


def select_react_select_by_label(page: Page, label_text: str, search_text: str,
                                  option_text: str = "",
                                  container_selector: str = "body") -> None:
    """
    Kết hợp: mở dropdown SearchSelect theo label → gõ search_text → click option.
    """
    click_rs_control_by_label(page, label_text, container_selector)
    page.keyboard.type(search_text)
    pick_rs_option(page, option_text or search_text)


def select_react_select(page: Page, placeholder_text: str, search_text: str,
                        timeout: int = 7000) -> None:
    """
    Click control react-select nhận biết qua text placeholder,
    gõ search_text, click option đầu tiên.
    (Dùng cho trường hợp placeholder vẫn hiển thị — chưa có giá trị)
    """
    page.get_by_text(placeholder_text, exact=True).click()
    page.keyboard.type(search_text)
    page.wait_for_selector("[class*='-option']", timeout=timeout)
    page.get_by_role("option", name=search_text, exact=False).first.click()


# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------

def go_to_new_sr_form(page: Page) -> None:
    """Mở /survey-requests, bấm Thêm (nút tạo mới trong CrudList), chờ form."""
    page.goto(BASE_URL + "/survey-requests")
    page.wait_for_load_state("networkidle", timeout=15000)
    btn = page.get_by_role("button", name="Thêm").first
    btn.click()
    page.wait_for_url(f"{BASE_URL}/survey-requests/new", timeout=8000)
    expect(
        page.get_by_text("Tạo Phiếu Yêu cầu Khảo sát mới")
    ).to_be_visible(timeout=12000)


def go_to_new_survey_form(page: Page) -> None:
    """Mở /surveys, bấm Thêm, chờ form tạo mới."""
    page.goto(BASE_URL + "/surveys")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.get_by_role("button", name="Thêm").first.click()
    page.wait_for_url(f"{BASE_URL}/surveys/new", timeout=8000)
    expect(
        page.get_by_role("heading", name="Tạo Phiếu Khảo sát")
    ).to_be_visible(timeout=12000)


# ---------------------------------------------------------------------------
# Survey Request form helpers
# ---------------------------------------------------------------------------

def fill_sr_header(page: Page, company_search: str = "Dego", purpose: str = "") -> None:
    """Điền công ty + mục đích trong form tạo mới SR.
    Công ty có thể đã tự điền (auto-fill theo user profile) — chỉ chọn lại nếu cần.
    """
    page.wait_for_timeout(1200)
    try:
        company_placeholder = page.get_by_text("Chọn công ty", exact=True)
        if company_placeholder.is_visible(timeout=2000):
            company_placeholder.click()
            page.keyboard.type(company_search)
            page.wait_for_timeout(700)
            page.get_by_role("option").first.click()
    except Exception:
        pass

    if purpose:
        page.get_by_placeholder("Nhập mục đích khảo sát...").fill(purpose)


def add_line_popup(page: Page, item_group: str = "Nhãn",
                   detail: str = "Chi tiết test", qty: str = "10") -> None:
    """
    Trong SurveyRequestDetail: bấm Thêm dòng, mở popup chi tiết,
    điền Phân loại (SearchSelect) + chi tiết + SL, bấm Xong.

    SearchSelect "Phân loại" trong popup SR dùng react-select với menuPortalTarget=body.
    Cách tương tác: dùng JS evaluate để click vào react-select control.
    """
    page.get_by_role("button", name="Thêm dòng").click()
    page.wait_for_timeout(500)

    # Mở popup chi tiết dòng cuối (icon bút title="Chi tiết")
    page.locator('button[title="Chi tiết"]').last.click()
    expect(page.get_by_text("Chi tiết dòng #")).to_be_visible(timeout=6000)

    # Phân loại — SearchSelect (react-select) trong popup
    # Popup có z-index cao và class="form-row" bên trong
    # Dùng evaluate để click vào control react-select
    page.evaluate("""
    (() => {
        // Tìm popup overlay (fixed position) và form-row trong đó
        const overlays = document.querySelectorAll('[style*="position: fixed"]');
        for (const overlay of overlays) {
            const rows = overlay.querySelectorAll('.form-row');
            for (const row of rows) {
                const label = row.querySelector('label');
                if (label && label.textContent.includes('Phân loại')) {
                    const ctrl = row.querySelector('[class*="-control"]');
                    if (ctrl) {
                        ctrl.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                        ctrl.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                        const inp = row.querySelector('div[data-value]') || row.querySelector('input');
                        if (inp) inp.focus();
                        return;
                    }
                }
            }
        }
        // Fallback: tìm trong toàn bộ document
        const rows = document.querySelectorAll('.form-row');
        for (const row of rows) {
            const label = row.querySelector('label');
            if (label && label.textContent.includes('Phân loại')) {
                const ctrl = row.querySelector('[class*="-control"]');
                if (ctrl) {
                    ctrl.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                    ctrl.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                    const inp = row.querySelector('div[data-value]') || row.querySelector('input');
                    if (inp) inp.focus();
                    return;
                }
            }
        }
    })()
    """)
    page.wait_for_timeout(500)
    page.keyboard.type(item_group)
    page.wait_for_timeout(700)

    # Thử exact match trước để tránh chọn nhầm (vd "Nhãn" vs "Nhãn dán thùng")
    opt_exact = page.get_by_role("option", name=item_group, exact=True)
    opt_fuzzy = page.get_by_role("option", name=item_group, exact=False)
    if opt_exact.count() > 0:
        opt_exact.first.click()
    elif opt_fuzzy.count() > 0:
        opt_fuzzy.first.click()
    else:
        page.keyboard.press("Enter")
    page.wait_for_timeout(400)

    # Chi tiết thông số kỹ thuật
    page.get_by_placeholder("Mô tả chi tiết yêu cầu kỹ thuật, chất lượng...").fill(detail)

    # Số lượng dự kiến (ô input placeholder="0")
    qty_inputs = page.locator('input[placeholder="0"]')
    if qty_inputs.count() > 0:
        qty_inputs.first.click()
        qty_inputs.first.fill(qty)

    # Đóng popup
    page.get_by_role("button", name="Xong").click()
    expect(page.get_by_text("Chi tiết dòng #")).not_to_be_visible(timeout=5000)


# ---------------------------------------------------------------------------
# SR save/submit helpers
# ---------------------------------------------------------------------------

def save_as_draft(page: Page) -> None:
    """Bấm Lưu nháp và chờ redirect ra khỏi /new."""
    page.get_by_role("button", name="Lưu nháp").click()
    page.wait_for_url(
        lambda url: "/survey-requests/" in url and url.split("/")[-1] != "new",
        timeout=12000,
    )


def save_and_submit(page: Page) -> None:
    """Bấm 'Lưu & Gửi Duyệt' và chờ redirect."""
    page.get_by_role("button", name="Lưu & Gửi Duyệt").click()
    page.wait_for_url(
        lambda url: "/survey-requests/" in url and url.split("/")[-1] != "new",
        timeout=12000,
    )


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def get_current_sr_id(page: Page) -> str:
    """Lấy ID phiếu từ URL hiện tại."""
    m = re.search(r"/survey-requests/(\d+)", page.url)
    return m.group(1) if m else ""


def get_sr_code(page: Page) -> str:
    """Lấy mã phiếu YCKS... từ tiêu đề trang."""
    el = page.get_by_text(re.compile(r"YCKS"), exact=False).first
    return el.text_content() or ""


def create_draft_sr(page: Page, ts: str = "") -> str:
    """Tạo 1 phiếu nháp hoàn chỉnh, trả về SR ID."""
    if not ts:
        ts = str(int(time.time()))[-6:]
    go_to_new_sr_form(page)
    fill_sr_header(page, purpose=f"E2E test {ts}")
    add_line_popup(page, item_group="Nhãn", detail=f"SP Nhãn {ts}", qty="5")
    save_as_draft(page)
    return get_current_sr_id(page)


def open_sr_by_id(page: Page, sr_id: str) -> None:
    """Điều hướng tới detail của 1 phiếu SR cụ thể."""
    page.goto(f"{BASE_URL}/survey-requests/{sr_id}")
    page.wait_for_load_state("networkidle", timeout=10000)


def wait_for_toast(page: Page, text: str = "", timeout: int = 6000) -> None:
    """Chờ toast notification (bất kỳ hoặc có text cụ thể)."""
    if text:
        expect(page.get_by_text(text, exact=False)).to_be_visible(timeout=timeout)
    else:
        page.wait_for_selector(".toast, [class*='toast'], [class*='Toastify']", timeout=timeout)
