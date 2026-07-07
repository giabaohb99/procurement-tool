"""
conftest.py — Playwright E2E fixtures cho procurement-tool.

BASE_URL: frontend dev server (web container, port 8080).
Fixtures login: trả về page đã đăng nhập với từng vai trò.
Tài khoản demo dev: email = code = password (ví dụ: TESTREQ/TESTREQ).

Mỗi role fixture tạo browser context riêng biệt → cho phép dùng nhiều role
trong cùng một test mà không xung đột session.
"""
import re
import pytest
from playwright.sync_api import Page, Browser, BrowserContext, expect

BASE_URL = "http://localhost:8080"


def login(page: Page, code: str, pw: str, max_retries: int = 3) -> None:
    """Đăng nhập vào app với mã nhân viên (code) và mật khẩu. Retry nếu thất bại."""
    for attempt in range(max_retries):
        page.goto(BASE_URL + "/login")
        page.wait_for_load_state("networkidle", timeout=12000)
        page.get_by_placeholder("Mã nhân viên").fill(code)
        page.get_by_placeholder("Mật khẩu").fill(pw)
        page.get_by_role("button", name="Đăng nhập").click()
        # Chờ URL rời khỏi /login (redirect về trang chủ)
        try:
            page.wait_for_url(
                lambda url: "/login" not in url,
                timeout=15000,
            )
            return  # Login thành công
        except Exception:
            if attempt < max_retries - 1:
                page.wait_for_timeout(1000)
                continue
            # Last attempt: chờ networkidle
            page.wait_for_load_state("networkidle", timeout=10000)


# ── Fixtures cho từng vai trò — mỗi role có browser context riêng ────────────────

@pytest.fixture(scope="function")
def page_req(browser: Browser):
    """Người yêu cầu (requester) — code TESTREQ."""
    context = browser.new_context()
    page = context.new_page()
    login(page, "TESTREQ", "TESTREQ")
    yield page
    context.close()


@pytest.fixture(scope="function")
def page_nstm(browser: Browser):
    """Nhân sự thu mua (NSTM/pur_staff) — code DEMONV."""
    context = browser.new_context()
    page = context.new_page()
    login(page, "DEMONV", "DEMONV")
    yield page
    context.close()


@pytest.fixture(scope="function")
def page_tp(browser: Browser):
    """Trưởng phòng (dept_head) — code DEMOTP."""
    context = browser.new_context()
    page = context.new_page()
    login(page, "DEMOTP", "DEMOTP")
    yield page
    context.close()


@pytest.fixture(scope="function")
def page_manager(browser: Browser):
    """Quản lý thu mua (pur_manager) — code DEMO_MANAGER_PURCHASE."""
    context = browser.new_context()
    page = context.new_page()
    login(page, "DEMO_MANAGER_PURCHASE", "DEMO_MANAGER_PURCHASE")
    yield page
    context.close()


@pytest.fixture(scope="function")
def page_admin(browser: Browser):
    """Quản trị hệ thống (admin full rights) — code admin."""
    context = browser.new_context()
    page = context.new_page()
    login(page, "admin", "admin")
    yield page
    context.close()
