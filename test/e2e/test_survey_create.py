"""
test_survey_create.py — Tạo phiếu khảo sát (Surveys module).

Covers:
  - DEMONV mở /surveys → bấm Thêm.
  - Chọn Phân loại (load động từ item-groups — kiểm 'Nhãn'/'Thùng' có trong dropdown).
  - Thêm dòng SP (product line) → lưu.
"""
import time
import pytest
from playwright.sync_api import Page, expect
from conftest import BASE_URL
from helpers import go_to_new_survey_form, click_rs_control_by_label, pick_rs_option


class TestSurveyCreate:

    def test_open_new_survey_form(self, page_nstm: Page):
        """Mở form tạo phiếu khảo sát mới."""
        go_to_new_survey_form(page_nstm)
        expect(page_nstm.get_by_role("heading", name="Tạo Phiếu Khảo sát")).to_be_visible()
        expect(page_nstm.get_by_role("heading", name="Thông tin tiếp nhận")).to_be_visible(timeout=5000)

    def test_item_group_dropdown_has_nhan_and_thung(self, page_nstm: Page):
        """Dropdown Phân loại có 'Nhãn' và 'Thùng'."""
        go_to_new_survey_form(page_nstm)

        # Kiểm 'Nhãn'
        click_rs_control_by_label(page_nstm, "Phân loại")
        page_nstm.keyboard.type("Nhãn")
        page_nstm.wait_for_timeout(600)
        nhan_opt = page_nstm.get_by_role("option", name="Nhãn", exact=False)
        assert nhan_opt.count() > 0, "'Nhãn' không có trong dropdown Phân loại"
        page_nstm.keyboard.press("Escape")
        page_nstm.wait_for_timeout(400)

        # Clear value nếu có bằng cách re-open và check 'Thùng'
        click_rs_control_by_label(page_nstm, "Phân loại")
        page_nstm.keyboard.type("Thùng")
        page_nstm.wait_for_timeout(600)
        thung_opt = page_nstm.get_by_role("option", name="Thùng", exact=False)
        assert thung_opt.count() > 0, "'Thùng' không có trong dropdown Phân loại"

    def test_create_survey_with_product_line(self, page_nstm: Page):
        """Tạo phiếu khảo sát hợp lệ với 1 dòng SP."""
        ts = str(int(time.time()))[-6:]
        go_to_new_survey_form(page_nstm)

        # Chọn Phân loại
        click_rs_control_by_label(page_nstm, "Phân loại")
        page_nstm.keyboard.type("Nhãn")
        page_nstm.wait_for_timeout(600)
        nhan_opt = page_nstm.get_by_role("option", name="Nhãn", exact=False)
        if nhan_opt.count() == 0:
            pytest.skip("'Nhãn' không tồn tại trong item-groups")
        nhan_opt.first.click()
        page_nstm.wait_for_timeout(300)

        # Điền Yêu cầu kỹ thuật
        page_nstm.get_by_placeholder("Mô tả thông số kỹ thuật, chất lượng, yêu cầu khác…").fill(
            f"Yêu cầu kỹ thuật test {ts}"
        )

        # Thêm dòng NCC (nút "Thêm dòng" đầu tiên trong bảng Khảo sát NCC)
        add_btns = page_nstm.get_by_role("button", name="Thêm dòng")
        if add_btns.count() > 0:
            add_btns.first.click()
            page_nstm.wait_for_timeout(400)

        # Bấm Tạo
        page_nstm.get_by_role("button", name="Tạo").click()
        page_nstm.wait_for_url(
            lambda url: "/surveys/" in url and url.split("/")[-1] != "new",
            timeout=12000,
        )
        # Thấy mã phiếu (heading "Phiếu Khảo sát KS...")
        expect(
            page_nstm.get_by_role("heading", name="Phiếu Khảo sát", exact=False)
        ).to_be_visible(timeout=8000)

    def test_survey_list_visible_for_nstm(self, page_nstm: Page):
        """DEMONV thấy list phiếu khảo sát và nút Thêm."""
        page_nstm.goto(BASE_URL + "/surveys")
        page_nstm.wait_for_load_state("networkidle", timeout=12000)
        expect(
            page_nstm.get_by_role("heading", name="Khảo sát (NCC", exact=False)
        ).to_be_visible(timeout=8000)
        # DEMONV có survey.create → thấy nút Thêm
        expect(page_nstm.get_by_role("button", name="Thêm")).to_be_visible(timeout=5000)
