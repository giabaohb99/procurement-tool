"""
test_sr_permissions.py — Visibility nút/menu theo vai trò.

Covers:
  - TESTREQ & DEMOTP KHÔNG thấy nút "Xử lý khảo sát".
  - DEMONV & DEMO_MANAGER_PURCHASE thấy nút "Xử lý khảo sát" (khi phiếu processing).
  - TESTREQ thấy menu "Yêu cầu khảo sát".
  - Tất cả vai đều thấy menu "Yêu cầu khảo sát".
  - DEMONV KHÔNG thấy nút "Tạo yêu cầu mua".
"""
import re
import time
import pytest
from playwright.sync_api import Page, expect
from conftest import BASE_URL, login
from helpers import (
    go_to_new_sr_form, fill_sr_header, add_line_popup,
    save_and_submit, get_current_sr_id, open_sr_by_id,
)


def create_processing_sr(page_req: Page, page_tp: Page) -> str:
    """Tạo phiếu processing và trả về ID."""
    ts = str(int(time.time()))[-6:]
    go_to_new_sr_form(page_req)
    fill_sr_header(page_req, purpose=f"E2E Perm {ts}")
    add_line_popup(page_req, item_group="Nhãn", detail=f"SP {ts}", qty="3")
    save_and_submit(page_req)
    sr_id = get_current_sr_id(page_req)
    open_sr_by_id(page_tp, sr_id)
    page_tp.get_by_role("button", name="Duyệt").click()
    page_tp.wait_for_timeout(1500)
    return sr_id


class TestSurveyRequestPermissions:

    def test_all_roles_see_menu(self, page_req: Page, page_tp: Page,
                                 page_nstm: Page, page_manager: Page):
        """Tất cả vai trò thấy menu 'Yêu cầu khảo sát'."""
        for p, name in [
            (page_req, "TESTREQ"),
            (page_tp, "DEMOTP"),
            (page_nstm, "DEMONV"),
            (page_manager, "DEMO_MANAGER_PURCHASE"),
        ]:
            p.goto(BASE_URL + "/")
            expect(
                p.get_by_role("link", name="Yêu cầu khảo sát")
            ).to_be_visible(timeout=8000), f"{name} không thấy menu Yêu cầu khảo sát"

    def test_req_no_process_button(self, page_req: Page, page_tp: Page):
        """TESTREQ KHÔNG thấy nút 'Xử lý khảo sát'."""
        sr_id = create_processing_sr(page_req, page_tp)
        open_sr_by_id(page_req, sr_id)
        # Phải đợi trang load xong
        page_req.wait_for_load_state("networkidle", timeout=8000)
        expect(
            page_req.get_by_role("button", name="Xử lý khảo sát")
        ).not_to_be_visible()

    def test_tp_no_process_button(self, page_req: Page, page_tp: Page):
        """DEMOTP KHÔNG thấy nút 'Xử lý khảo sát'."""
        sr_id = create_processing_sr(page_req, page_tp)
        open_sr_by_id(page_tp, sr_id)
        page_tp.wait_for_load_state("networkidle", timeout=8000)
        expect(
            page_tp.get_by_role("button", name="Xử lý khảo sát")
        ).not_to_be_visible()

    def test_nstm_sees_process_button(self, page_req: Page, page_tp: Page, page_nstm: Page):
        """DEMONV thấy nút 'Xử lý khảo sát'."""
        sr_id = create_processing_sr(page_req, page_tp)
        open_sr_by_id(page_nstm, sr_id)
        expect(
            page_nstm.get_by_role("button", name="Xử lý khảo sát")
        ).to_be_visible(timeout=8000)

    def test_manager_sees_process_button(self, page_req: Page, page_tp: Page, page_manager: Page):
        """DEMO_MANAGER_PURCHASE thấy nút 'Xử lý khảo sát'."""
        sr_id = create_processing_sr(page_req, page_tp)
        open_sr_by_id(page_manager, sr_id)
        expect(
            page_manager.get_by_role("button", name="Xử lý khảo sát")
        ).to_be_visible(timeout=8000)

    def test_nstm_no_create_pr_button(self, page_req: Page, page_tp: Page, page_nstm: Page):
        """DEMONV không thấy nút 'Tạo yêu cầu mua' (trên phiếu processing)."""
        sr_id = create_processing_sr(page_req, page_tp)
        open_sr_by_id(page_nstm, sr_id)
        page_nstm.wait_for_load_state("networkidle", timeout=8000)
        # Nút "Tạo yêu cầu mua" chỉ hiện khi status = survey_done + canCreatePr
        expect(
            page_nstm.get_by_role("button", name="Tạo yêu cầu mua")
        ).not_to_be_visible()

    def test_req_sees_approve_reject_buttons_absent(self, page_req: Page, page_tp: Page):
        """TESTREQ KHÔNG thấy nút Duyệt / Trả lại trên phiếu chờ duyệt."""
        ts = str(int(time.time()))[-6:]
        go_to_new_sr_form(page_req)
        fill_sr_header(page_req, purpose=f"E2E Perm2 {ts}")
        add_line_popup(page_req, item_group="Nhãn", detail=f"SP {ts}", qty="2")
        save_and_submit(page_req)
        sr_id = get_current_sr_id(page_req)
        open_sr_by_id(page_req, sr_id)
        page_req.wait_for_load_state("networkidle", timeout=8000)
        expect(page_req.get_by_role("button", name="Duyệt")).not_to_be_visible()
        expect(page_req.get_by_role("button", name="Trả lại")).not_to_be_visible()
