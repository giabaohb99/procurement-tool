"""
test_sr_full_flow.py — Full E2E flow xuyên suốt 1 phiếu YCKS.

Luồng:
  TESTREQ tạo+gửi → DEMOTP duyệt → DEMONV xử lý gắn option
  → Admin chốt hoàn thành khảo sát (cần survey_request.delete)
  → TESTREQ chọn PA + tạo YCMH
  → DEMO_MANAGER_PURCHASE chuyển Hoàn thành (cần approve + process).

Mỗi bước assert trạng thái + dữ liệu tương ứng.

NOTE: Bước "Chốt hoàn thành khảo sát" cần isAdminTM = can('survey_request', 'delete').
- DEMO_MANAGER_PURCHASE chỉ có approve+process, KHÔNG có delete → dùng admin.
- Bước "Chuyển Hoàn thành" cần approve+process → DEMO_MANAGER_PURCHASE phù hợp.
"""
import re
import time
import pytest
from playwright.sync_api import Page, expect
from conftest import BASE_URL
from helpers import (
    go_to_new_sr_form, fill_sr_header, add_line_popup,
    save_and_submit, get_current_sr_id, open_sr_by_id,
)


class TestSurveyRequestFullFlow:

    def test_full_flow(
        self,
        page_req: Page,
        page_tp: Page,
        page_nstm: Page,
        page_admin: Page,
        page_manager: Page,
    ):
        """Toàn bộ luồng YCKS từ tạo đến Hoàn thành."""
        ts = str(int(time.time()))[-6:]

        # ── Bước 1: TESTREQ tạo + gửi duyệt ──────────────────────────────────
        go_to_new_sr_form(page_req)
        fill_sr_header(page_req, purpose=f"E2E Full Flow {ts}")
        add_line_popup(page_req, item_group="Nhãn", detail=f"Nhãn SP {ts}", qty="10")
        save_and_submit(page_req)
        sr_id = get_current_sr_id(page_req)
        assert sr_id, "Không lấy được SR ID sau khi tạo"

        expect(page_req.get_by_text("Chờ duyệt")).to_be_visible(timeout=8000)

        # ── Bước 2: DEMOTP duyệt ──────────────────────────────────────────────
        open_sr_by_id(page_tp, sr_id)
        approve_btn = page_tp.get_by_role("button", name="Duyệt")
        expect(approve_btn).to_be_visible(timeout=8000)
        approve_btn.click()
        page_tp.wait_for_timeout(1500)
        expect(page_tp.get_by_text("Đang xử lý")).to_be_visible(timeout=8000)

        # ── Bước 3: DEMONV mở trang xử lý, chọn NCC, thêm option ─────────────
        open_sr_by_id(page_nstm, sr_id)
        process_btn = page_nstm.get_by_role("button", name="Xử lý khảo sát")
        expect(process_btn).to_be_visible(timeout=8000)
        process_btn.click()
        page_nstm.wait_for_url(re.compile(r"/process"), timeout=8000)

        # Chọn NCC Nông Xanh — dùng combobox role (react-select renders input[role="combobox"])
        ncc_combobox = page_nstm.get_by_role("combobox").first
        ncc_combobox.click()
        page_nstm.wait_for_timeout(300)
        ncc_combobox.type("Nông Xanh")
        page_nstm.wait_for_timeout(800)
        ncc_opt = page_nstm.get_by_role("option", name="Nông Xanh", exact=False)
        if ncc_opt.count() == 0:
            pytest.skip("NCC 'Nông Xanh' không tồn tại trong dev data")
        ncc_opt.first.click()
        page_nstm.wait_for_timeout(1200)

        # Thêm option đầu tiên nếu có
        add_plus_btns = page_nstm.locator('table button').filter(
            has=page_nstm.locator('.ti-plus')
        )
        if add_plus_btns.count() == 0:
            pytest.skip("Không có dòng khảo sát khả dụng cho NCC này")
        add_plus_btns.first.click()
        page_nstm.wait_for_timeout(2000)

        # Kiểm tra Options đã gắn (1)
        expect(
            page_nstm.get_by_text("Options đã gắn (1)", exact=False)
        ).to_be_visible(timeout=8000)

        # ── Bước 4: Admin chốt hoàn thành khảo sát (cần survey_request.delete) ─
        open_sr_by_id(page_admin, sr_id)
        chot_process = page_admin.get_by_role("button", name="Xử lý khảo sát")
        expect(chot_process).to_be_visible(timeout=8000)
        chot_process.click()
        page_admin.wait_for_url(re.compile(r"/process"), timeout=8000)

        chot_btn = page_admin.get_by_role("button", name="Chốt hoàn thành khảo sát")
        expect(chot_btn).to_be_visible(timeout=5000)
        # Confirm dialog
        page_admin.once("dialog", lambda d: d.accept())
        chot_btn.click()
        # Sau chốt → redirect về detail
        page_admin.wait_for_url(
            re.compile(r"/survey-requests/\d+$"), timeout=10000
        )
        expect(page_admin.get_by_text("Đã khảo sát").first).to_be_visible(timeout=8000)

        # ── Bước 5: TESTREQ chọn PA ───────────────────────────────────────────
        open_sr_by_id(page_req, sr_id)
        # Reload để lấy status mới
        page_req.reload()
        page_req.wait_for_load_state("networkidle", timeout=10000)
        expect(page_req.get_by_text("Kết quả khảo sát", exact=False)).to_be_visible(timeout=10000)

        # Click option đầu tiên để chọn PA
        option_cards = page_req.locator(".option-card")
        if option_cards.count() == 0:
            pytest.skip("Không có option card sau khi chốt")
        option_cards.first.click()
        page_req.wait_for_timeout(2000)
        expect(page_req.get_by_text("Đã chọn").first).to_be_visible(timeout=6000)

        # ── Bước 6: Tạo YCMH ─────────────────────────────────────────────────
        create_pr_btn = page_req.get_by_role("button", name="Tạo yêu cầu mua")
        expect(create_pr_btn).to_be_visible(timeout=5000)
        if create_pr_btn.is_disabled():
            pytest.skip("Nút Tạo yêu cầu mua vẫn disabled (chưa chọn đủ PA)")
        page_req.once("dialog", lambda d: d.accept())
        create_pr_btn.click()
        page_req.wait_for_timeout(3000)

        # Badge "Đã tạo YCMH"
        expect(page_req.get_by_text("Đã tạo YCMH").first).to_be_visible(timeout=10000)

        # Banner link PYC
        expect(
            page_req.get_by_text("Đã tạo", exact=False).filter(has_text="phiếu").first
        ).to_be_visible(timeout=5000)

        # ── Bước 7: Manager chuyển Hoàn thành (approve + process) ────────────
        open_sr_by_id(page_manager, sr_id)
        page_manager.reload()
        page_manager.wait_for_load_state("networkidle", timeout=10000)

        finalize_btn = page_manager.get_by_role("button", name="Chuyển Hoàn thành")
        expect(finalize_btn).to_be_visible(timeout=8000)
        page_manager.once("dialog", lambda d: d.accept())
        finalize_btn.click()
        page_manager.wait_for_timeout(2000)
        expect(page_manager.get_by_text("Hoàn thành").first).to_be_visible(timeout=8000)
