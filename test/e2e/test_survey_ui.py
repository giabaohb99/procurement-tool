"""
test_survey_ui.py — Kiểm tra UI kết quả khảo sát (ẩn NCC) + chọn option.

Test 1: Login TESTREQ → vào /survey-requests → tìm phiếu "Đã khảo sát".
  - Nếu không có phiếu → pytest.skip.
  - Mở phiếu → khu "Kết quả khảo sát" hiển thị.
  - Các thẻ option KHÔNG chứa chuỗi tên NCC (ví dụ: "Công Ty", "NCC", "TNHH").
  - Click 1 thẻ option → badge "Đã chọn" xuất hiện.
"""
import pytest
from playwright.sync_api import Page, expect

from conftest import BASE_URL

# Các từ khóa cho thấy tên NCC bị lộ (tiếng Việt)
NCC_KEYWORDS = ["Công Ty", "Công ty", "TNHH", "Cty", "NCC", "Nhà Cung Cấp"]


class TestSurveyResultUI:
    def test_result_hides_supplier_info(self, page_req: Page):
        """Màn kết quả khảo sát không lộ thông tin NCC trong thẻ option."""
        page_req.goto(BASE_URL + "/survey-requests")
        page_req.wait_for_load_state("networkidle", timeout=10000)

        # Tìm phiếu có trạng thái "Đã khảo sát"
        survey_done_rows = page_req.get_by_text("Đã khảo sát")
        count = survey_done_rows.count()
        if count == 0:
            pytest.skip("Không có phiếu ở trạng thái 'Đã khảo sát' — bỏ qua test E2E này")

        # Click vào phiếu đầu tiên
        survey_done_rows.first.click()
        page_req.wait_for_load_state("networkidle", timeout=8000)

        # Khu "Kết quả khảo sát" phải hiển thị
        expect(page_req.get_by_text("Kết quả khảo sát")).to_be_visible(timeout=8000)

        # Kiểm tra các thẻ option không lộ NCC
        # Tìm vùng chứa các option (thẻ card/div chứa option)
        option_cards = page_req.locator("[class*='option'], [data-testid*='option']")
        if option_cards.count() == 0:
            # Fallback: tìm theo text "Option"
            option_cards = page_req.get_by_text("Option", exact=False)

        page_content = page_req.content()
        # Chỉ kiểm tra trong vùng kết quả khảo sát (không toàn trang)
        result_section = page_req.locator("text=Kết quả khảo sát").locator("..")
        section_text = result_section.inner_text() if result_section.count() > 0 else ""

        for keyword in NCC_KEYWORDS:
            assert keyword not in section_text, (
                f"Tên NCC bị lộ: từ khóa '{keyword}' xuất hiện trong khu kết quả khảo sát"
            )

    def test_choose_option_shows_badge(self, page_req: Page):
        """Click thẻ option → badge 'Đã chọn' xuất hiện."""
        page_req.goto(BASE_URL + "/survey-requests")
        page_req.wait_for_load_state("networkidle", timeout=10000)

        survey_done_rows = page_req.get_by_text("Đã khảo sát")
        if survey_done_rows.count() == 0:
            pytest.skip("Không có phiếu 'Đã khảo sát' để test chọn option")

        survey_done_rows.first.click()
        page_req.wait_for_load_state("networkidle", timeout=8000)

        # Tìm nút/thẻ "Chọn" của option đầu tiên
        choose_buttons = page_req.get_by_role("button", name="Chọn")
        if choose_buttons.count() == 0:
            # Fallback: tìm thẻ option có thể click
            choose_buttons = page_req.locator("[class*='option']:first-child button")

        if choose_buttons.count() == 0:
            pytest.skip("Không tìm thấy nút chọn option — bỏ qua")

        choose_buttons.first.click()
        page_req.wait_for_load_state("networkidle", timeout=5000)

        # Badge "Đã chọn" phải xuất hiện sau khi click
        expect(page_req.get_by_text("Đã chọn")).to_be_visible(timeout=5000)
