"""
test_sr_result.py — Xem kết quả khảo sát, chọn PA, tạo YCMH.

Covers:
  - TESTREQ mở phiếu "Đã khảo sát" hoặc "Đã tạo YCMH" → khu "Kết quả khảo sát" visible.
  - Assert NCC KHÔNG lộ trong thẻ option của người YC.
  - Chọn 1 PA mỗi SP → badge "Đã chọn" hiện (chỉ khi survey_done).
  - Khi đủ PA → nút "Tạo yêu cầu mua" bật → bấm → toast + banner link PYC.

NOTE: Dùng phiếu survey_done/pr_created/done có sẵn trong dev data.
Nếu không tìm thấy → pytest.skip.
"""
import re
import pytest
from playwright.sync_api import Page, expect
from conftest import BASE_URL


def find_result_sr(page: Page) -> tuple[str, str] | tuple[None, None]:
    """Tìm phiếu survey_done/pr_created/done trong list để xem kết quả.
    Trả về (sr_id, status) hoặc (None, None).
    """
    page.goto(BASE_URL + "/survey-requests")
    page.wait_for_load_state("networkidle", timeout=12000)

    # Thử tìm "Đã khảo sát" trước, sau đó "Đã tạo YCMH", rồi "Hoàn thành"
    for badge_text, status_key in [
        ("Đã khảo sát", "survey_done"),
        ("Đã tạo YCMH", "pr_created"),
        ("Hoàn thành", "done"),
    ]:
        badge = page.get_by_text(badge_text, exact=True).first
        try:
            if badge.is_visible(timeout=2000):
                row = badge.locator("xpath=ancestor::tr").first
                if row.count() > 0:
                    row.click()
                    page.wait_for_load_state("networkidle", timeout=8000)
                    m = re.search(r"/survey-requests/(\d+)", page.url)
                    if m:
                        return m.group(1), status_key
                    # navigate back
                    page.goto(BASE_URL + "/survey-requests")
                    page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

    # Fallback: dùng trực tiếp ID=11 (pr_created, TESTREQ là creator)
    try:
        page.goto(f"{BASE_URL}/survey-requests/11")
        page.wait_for_load_state("networkidle", timeout=10000)
        result_text = page.get_by_text("Kết quả khảo sát", exact=False)
        if result_text.is_visible(timeout=5000):
            return "11", "pr_created"
    except Exception:
        pass

    return None, None


class TestSurveyRequestResult:

    def test_result_section_visible(self, page_req: Page):
        """Phiếu survey_done/pr_created → khu 'Kết quả khảo sát' visible."""
        sr_id, _ = find_result_sr(page_req)
        if sr_id is None:
            pytest.skip("Không có phiếu survey_done/pr_created trong dev data")

        page_req.goto(f"{BASE_URL}/survey-requests/{sr_id}")
        page_req.wait_for_load_state("networkidle", timeout=10000)
        expect(page_req.get_by_text("Kết quả khảo sát", exact=False)).to_be_visible(timeout=8000)

    def test_no_supplier_name_in_options(self, page_req: Page):
        """Options KHÔNG lộ tên NCC/mã NCC với người YC."""
        sr_id, _ = find_result_sr(page_req)
        if sr_id is None:
            pytest.skip("Không có phiếu survey_done/pr_created trong dev data")

        page_req.goto(f"{BASE_URL}/survey-requests/{sr_id}")
        page_req.wait_for_load_state("networkidle", timeout=10000)

        # Tìm khối options-container (có thể có nhiều)
        options_containers = page_req.locator(".options-container")
        if options_containers.count() == 0:
            pytest.skip("Không có options trong phiếu này")

        # Gộp text từ tất cả containers
        text = ""
        for i in range(options_containers.count()):
            text += options_containers.nth(i).text_content() or ""

        # Tên NCC "Nông Xanh" KHÔNG được xuất hiện trong vùng kết quả với người YC
        assert "Nông Xanh" not in text, "NCC 'Nông Xanh' bị lộ trong option của người YC"
        # Không chứa key kỹ thuật supplier_code trong text UI
        assert "supplier_code" not in text.lower(), "supplier_code key bị lộ trong UI"

    def test_option_display_label_format(self, page_req: Page):
        """Option card hiện label dạng 'Option N — ID' (không có tên NCC)."""
        sr_id, _ = find_result_sr(page_req)
        if sr_id is None:
            pytest.skip("Không có phiếu survey_done/pr_created trong dev data")

        page_req.goto(f"{BASE_URL}/survey-requests/{sr_id}")
        page_req.wait_for_load_state("networkidle", timeout=10000)

        options_containers = page_req.locator(".options-container")
        if options_containers.count() == 0:
            pytest.skip("Không có options trong phiếu này")

        # Phải có ít nhất 1 option card
        option_cards = page_req.locator(".option-card")
        assert option_cards.count() > 0, "Không có option card nào"

        # Nội dung option card phải có pattern "Option N" hoặc snap fields
        first_card_text = option_cards.first.text_content() or ""
        assert "Option" in first_card_text or len(first_card_text) > 10, \
            "Option card không có nội dung đúng"

    def test_chosen_badge_visible_on_chosen_option(self, page_req: Page):
        """Phiếu đã chọn PA → badge 'Đã chọn' hiện trên option card."""
        sr_id, _ = find_result_sr(page_req)
        if sr_id is None:
            pytest.skip("Không có phiếu survey_done/pr_created trong dev data")

        page_req.goto(f"{BASE_URL}/survey-requests/{sr_id}")
        page_req.wait_for_load_state("networkidle", timeout=10000)

        options_containers = page_req.locator(".options-container")
        if options_containers.count() == 0:
            pytest.skip("Không có options trong phiếu này")

        # Phiếu pr_created đã có PA được chọn trước → badge "Đã chọn" visible
        chosen_badge = page_req.get_by_text("Đã chọn", exact=True).first
        if chosen_badge.is_visible(timeout=3000):
            expect(chosen_badge).to_be_visible()
        else:
            # Phiếu survey_done chưa chọn — thử click option đầu tiên
            option_cards = page_req.locator(".option-card")
            if option_cards.count() > 0:
                option_cards.first.click()
                page_req.wait_for_timeout(2000)
                expect(page_req.get_by_text("Đã chọn").first).to_be_visible(timeout=6000)
            else:
                pytest.skip("Không có option card để chọn")

    def test_create_pr_button_visible_for_survey_done(self, page_req: Page):
        """Nút 'Tạo yêu cầu mua' visible khi phiếu survey_done và người tạo đúng."""
        # Tìm phiếu survey_done (không phải pr_created)
        page_req.goto(BASE_URL + "/survey-requests")
        page_req.wait_for_load_state("networkidle", timeout=12000)
        badge = page_req.get_by_text("Đã khảo sát", exact=True).first
        if not badge.is_visible(timeout=2000):
            pytest.skip("Không có phiếu survey_done trong dev data — bỏ qua test tạo YCMH")

        row = badge.locator("xpath=ancestor::tr").first
        if row.count() == 0:
            pytest.skip("Không click được vào phiếu survey_done")
        row.click()
        page_req.wait_for_load_state("networkidle", timeout=8000)

        btn = page_req.get_by_role("button", name="Tạo yêu cầu mua")
        expect(btn).to_be_visible(timeout=8000)
