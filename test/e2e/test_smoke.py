"""
test_smoke.py — Smoke test: login từng vai + kiểm tra menu.

Test 1: Mỗi vai đăng nhập → dashboard hiện "Chào mừng trở lại".
Test 2: TESTREQ, DEMONV thấy menu "Yêu cầu khảo sát".
Test 3: DEMOTP (trưởng phòng) cũng thấy menu "Yêu cầu khảo sát".
"""
import pytest
from playwright.sync_api import Page, expect

from conftest import BASE_URL


class TestLoginSmoke:
    def test_req_sees_welcome(self, page_req: Page):
        """Người YC đăng nhập → thấy 'Chào mừng trở lại'."""
        expect(page_req.get_by_text("Chào mừng trở lại")).to_be_visible(timeout=8000)

    def test_nstm_sees_welcome(self, page_nstm: Page):
        """NSTM đăng nhập → thấy 'Chào mừng trở lại'."""
        expect(page_nstm.get_by_text("Chào mừng trở lại")).to_be_visible(timeout=8000)

    def test_tp_sees_welcome(self, page_tp: Page):
        """Trưởng phòng đăng nhập → thấy 'Chào mừng trở lại'."""
        expect(page_tp.get_by_text("Chào mừng trở lại")).to_be_visible(timeout=8000)

    def test_manager_sees_welcome(self, page_manager: Page):
        """Quản lý TM đăng nhập → thấy 'Chào mừng trở lại'."""
        expect(page_manager.get_by_text("Chào mừng trở lại")).to_be_visible(timeout=8000)


class TestMenuVisibility:
    def test_req_sees_survey_request_menu(self, page_req: Page):
        """TESTREQ thấy menu 'Yêu cầu khảo sát' trong nav."""
        expect(page_req.get_by_role("link", name="Yêu cầu khảo sát")).to_be_visible(timeout=5000)

    def test_nstm_sees_survey_request_menu(self, page_nstm: Page):
        """DEMONV (NSTM) thấy menu 'Yêu cầu khảo sát'."""
        expect(page_nstm.get_by_role("link", name="Yêu cầu khảo sát")).to_be_visible(timeout=5000)

    def test_tp_sees_survey_request_menu(self, page_tp: Page):
        """DEMOTP (trưởng phòng) thấy menu 'Yêu cầu khảo sát'."""
        expect(page_tp.get_by_role("link", name="Yêu cầu khảo sát")).to_be_visible(timeout=5000)

    def test_manager_sees_survey_request_menu(self, page_manager: Page):
        """Quản lý TM thấy menu 'Yêu cầu khảo sát'."""
        expect(page_manager.get_by_role("link", name="Yêu cầu khảo sát")).to_be_visible(timeout=5000)
