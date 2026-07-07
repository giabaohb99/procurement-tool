"""
test_sr_workflow.py — Luồng duyệt / trả lại phiếu Yêu cầu khảo sát.

Covers:
  - Tạo nháp → "Lưu & Gửi Duyệt" → trạng thái "Chờ duyệt".
  - DEMOTP Duyệt → trạng thái "Đang xử lý".
  - DEMOTP Trả lại + nhập lý do → "Từ chối" + banner lý do.
  - TESTREQ sửa phiếu bị trả lại + gửi lại.
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


def create_and_submit_sr(page: Page, ts: str) -> str:
    """TESTREQ: tạo phiếu + gửi duyệt, trả về sr_id."""
    go_to_new_sr_form(page)
    fill_sr_header(page, purpose=f"E2E WF Submit {ts}")
    add_line_popup(page, item_group="Nhãn", detail=f"SP {ts}", qty="5")
    save_and_submit(page)
    return get_current_sr_id(page)


class TestSurveyRequestWorkflow:

    def test_submit_changes_status_to_submitted(self, page_req: Page):
        """Lưu & Gửi Duyệt → badge 'Chờ duyệt' hiện trên detail page."""
        ts = str(int(time.time()))[-6:]
        create_and_submit_sr(page_req, ts)
        # Sau redirect, trang detail hiện badge "Chờ duyệt"
        expect(page_req.get_by_text("Chờ duyệt")).to_be_visible(timeout=8000)

    def test_tp_approve_changes_to_processing(self, page_req: Page, page_tp: Page):
        """DEMOTP duyệt → badge chuyển sang 'Đang xử lý'."""
        ts = str(int(time.time()))[-6:]
        # Bước 1: TESTREQ tạo + gửi
        sr_id = create_and_submit_sr(page_req, ts)

        # Bước 2: DEMOTP mở phiếu, bấm Duyệt
        open_sr_by_id(page_tp, sr_id)
        expect(page_tp.get_by_role("button", name="Duyệt")).to_be_visible(timeout=8000)
        page_tp.get_by_role("button", name="Duyệt").click()
        page_tp.wait_for_timeout(1500)

        # Badge chuyển "Đang xử lý"
        expect(page_tp.get_by_text("Đang xử lý")).to_be_visible(timeout=8000)

    def test_tp_reject_shows_reason(self, page_req: Page, page_tp: Page):
        """DEMOTP Trả lại + lý do → badge 'Từ chối' và banner lý do."""
        ts = str(int(time.time()))[-6:]
        reason = f"Lý do trả lại {ts}"
        sr_id = create_and_submit_sr(page_req, ts)

        # DEMOTP mở phiếu
        open_sr_by_id(page_tp, sr_id)
        expect(page_tp.get_by_role("button", name="Trả lại")).to_be_visible(timeout=8000)

        # Bấm Trả lại — prompt dialog
        page_tp.once("dialog", lambda d: d.accept(reason))
        page_tp.get_by_role("button", name="Trả lại").click()
        page_tp.wait_for_timeout(1500)

        # Badge "Từ chối"
        expect(page_tp.get_by_text("Từ chối", exact=True).first).to_be_visible(timeout=8000)
        # Banner lý do (xuất hiện trong div.err hoặc audit log)
        expect(page_tp.locator("*").filter(has_text=reason).first).to_be_visible(timeout=5000)

    def test_req_resubmit_after_reject(self, page_req: Page, page_tp: Page):
        """TESTREQ sửa phiếu bị trả lại → gửi lại → 'Chờ duyệt'."""
        ts = str(int(time.time()))[-6:]
        reason = f"Thiếu thông tin {ts}"
        sr_id = create_and_submit_sr(page_req, ts)

        # DEMOTP từ chối
        open_sr_by_id(page_tp, sr_id)
        page_tp.once("dialog", lambda d: d.accept(reason))
        page_tp.get_by_role("button", name="Trả lại").click()
        page_tp.wait_for_timeout(1500)

        # TESTREQ mở lại phiếu — sẽ thấy trạng thái "Từ chối" và form editable
        open_sr_by_id(page_req, sr_id)
        expect(page_req.get_by_text("Từ chối", exact=True).first).to_be_visible(timeout=8000)

        # Sửa mục đích
        purpose_ta = page_req.get_by_placeholder("Nhập mục đích khảo sát...")
        purpose_ta.fill(f"Đã cập nhật {ts}")

        # Gửi lại
        page_req.get_by_role("button", name="Lưu & Gửi Duyệt").click()
        page_req.wait_for_timeout(2000)
        expect(page_req.get_by_text("Chờ duyệt")).to_be_visible(timeout=8000)
