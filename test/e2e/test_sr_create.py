"""
test_sr_create.py — Tạo phiếu Yêu cầu khảo sát mới.

Covers:
  - Mở /survey-requests → "Thêm" → form rỗng với tiêu đề đúng.
  - Tạo phiếu hợp lệ: mục đích + thêm dòng qua popup → Lưu nháp → thấy mã YCKS.
  - Validation: thiếu mục đích / 0 dòng → hiện lỗi, không lưu.
  - Thêm/xóa nhiều dòng.
  - Định dạng tiền: gõ 3000 popup → blur → hiển thị 3.000.
"""
import re
import time
import pytest
from playwright.sync_api import Page, expect
from conftest import BASE_URL
from helpers import go_to_new_sr_form, fill_sr_header, add_line_popup, save_as_draft


class TestSurveyRequestCreate:

    def test_open_new_form(self, page_req: Page):
        """Mở form tạo mới → tiêu đề đúng."""
        go_to_new_sr_form(page_req)
        expect(page_req.get_by_text("Tạo Phiếu Yêu cầu Khảo sát mới")).to_be_visible()
        # Nút Lưu nháp visible
        expect(page_req.get_by_role("button", name="Lưu")).to_be_visible()

    def test_validation_no_purpose(self, page_req: Page):
        """Thiếu mục đích → hiện lỗi."""
        go_to_new_sr_form(page_req)
        # Đợi auto-fill xong
        page_req.wait_for_timeout(1500)
        # Thêm 1 dòng để pass validation lines
        add_line_popup(page_req, item_group="Nhãn", detail="Test detail")
        # Xóa mục đích
        purpose_ta = page_req.get_by_placeholder("Nhập mục đích khảo sát...")
        purpose_ta.fill("")
        page_req.get_by_role("button", name="Lưu").click()
        # Lỗi validation mục đích
        err = page_req.get_by_text("Vui lòng nhập Mục đích", exact=False)
        expect(err).to_be_visible(timeout=5000)

    def test_validation_no_lines(self, page_req: Page):
        """Không có dòng → lỗi 'Cần ít nhất 1 dòng'."""
        go_to_new_sr_form(page_req)
        fill_sr_header(page_req, purpose="Test không có dòng")
        # KHÔNG thêm dòng
        page_req.get_by_role("button", name="Lưu").click()
        expect(page_req.get_by_text("Cần ít nhất 1 dòng", exact=False)).to_be_visible(timeout=5000)

    def test_create_valid_draft(self, page_req: Page):
        """Tạo phiếu hợp lệ → Lưu nháp → thấy mã YCKS."""
        ts = str(int(time.time()))[-6:]
        go_to_new_sr_form(page_req)
        fill_sr_header(page_req, purpose=f"E2E Tạo nháp {ts}")
        add_line_popup(page_req, item_group="Nhãn", detail=f"SP test {ts}", qty="5")
        save_as_draft(page_req)
        # Thấy mã phiếu YCBG...
        expect(page_req.get_by_text("YCBG", exact=False)).to_be_visible(timeout=8000)

    def test_add_multiple_lines_then_delete(self, page_req: Page):
        """Thêm 2 dòng, xóa 1 → còn 1 dòng."""
        go_to_new_sr_form(page_req)
        # Thêm dòng 1
        page_req.get_by_role("button", name="Thêm dòng").click()
        page_req.wait_for_timeout(300)
        # Thêm dòng 2
        page_req.get_by_role("button", name="Thêm dòng").click()
        page_req.wait_for_timeout(300)

        # Đếm số dòng tbody tr (bỏ qua tr "Chưa có dòng nào")
        rows = page_req.locator(".items-table tbody tr")
        assert rows.count() == 2, f"Mong đợi 2 dòng, có {rows.count()}"

        # Xóa dòng đầu
        page_req.locator('.items-table tbody tr').nth(0).get_by_title("Xóa").click()
        page_req.wait_for_timeout(400)
        assert rows.count() == 1, f"Sau khi xóa mong đợi 1 dòng, có {rows.count()}"

    def test_price_format_3000(self, page_req: Page):
        """Gõ 3000 trong popup → blur → hiển thị 3.000."""
        go_to_new_sr_form(page_req)
        # Thêm 1 dòng
        page_req.get_by_role("button", name="Thêm dòng").click()
        page_req.wait_for_timeout(300)
        # Mở popup chi tiết
        page_req.locator('button[title="Chi tiết / hình ảnh"]').last.click()
        expect(page_req.get_by_text("Chi tiết dòng #")).to_be_visible(timeout=5000)

        # Ô Giá đề xuất VNĐ
        price_input = page_req.get_by_placeholder("Để trống nếu chưa có")
        price_input.click()
        price_input.fill("3000")
        # Blur để trigger format
        page_req.get_by_placeholder("Mô tả chi tiết yêu cầu kỹ thuật, chất lượng...").click()
        page_req.wait_for_timeout(500)
        # Giá trị hiển thị phải là "3.000"
        val = price_input.input_value()
        assert val == "3.000", f"Mong 3.000, có '{val}'"

    def test_line_popup_shows_and_closes(self, page_req: Page):
        """Popup dòng mở/đóng đúng."""
        go_to_new_sr_form(page_req)
        page_req.get_by_role("button", name="Thêm dòng").click()
        page_req.wait_for_timeout(300)

        # Mở popup
        page_req.locator('button[title="Chi tiết / hình ảnh"]').last.click()
        expect(page_req.get_by_text("Chi tiết dòng #1")).to_be_visible(timeout=5000)

        # Đóng bằng nút Xong
        page_req.get_by_role("button", name="Xong").click()
        expect(page_req.get_by_text("Chi tiết dòng #1")).not_to_be_visible(timeout=5000)

    def test_save_and_submit_shows_submitted_badge(self, page_req: Page):
        """Lưu & Gửi Duyệt → badge 'Chờ duyệt'."""
        ts = str(int(time.time()))[-6:]
        go_to_new_sr_form(page_req)
        fill_sr_header(page_req, purpose=f"E2E Submit {ts}")
        add_line_popup(page_req, item_group="Nhãn", detail=f"SP {ts}", qty="2")
        page_req.get_by_role("button", name="Gửi duyệt").click()
        page_req.wait_for_url(
            lambda url: "/survey-requests/" in url and url.split("/")[-1] != "new",
            timeout=12000,
        )
        expect(page_req.get_by_text("Chờ duyệt")).to_be_visible(timeout=8000)
