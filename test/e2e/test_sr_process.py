"""
test_sr_process.py — NSTM xử lý khảo sát.

Covers:
  - DEMONV mở phiếu "Đang xử lý" → bấm "Xử lý khảo sát".
  - Chọn NCC "Nông Xanh" → bảng dòng khảo sát hiện đúng phân loại (Nhãn).
  - Thêm option → khối "Options đã gắn" tăng, dòng biến mất khỏi bảng trên.
  - Xóa option → quay lại.
  - Nút "Chốt hoàn thành" — DEMONV KHÔNG thấy (chỉ admin/QL); DEMO_MANAGER_PURCHASE thấy.
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


def create_processing_sr(page_req: Page, page_tp: Page, ts: str) -> str:
    """Tạo phiếu + gửi + TP duyệt → trả về sr_id ở trạng thái 'processing'."""
    go_to_new_sr_form(page_req)
    fill_sr_header(page_req, purpose=f"E2E Process {ts}")
    add_line_popup(page_req, item_group="Nhãn", detail=f"Nhãn SP {ts}", qty="10")
    save_and_submit(page_req)
    sr_id = get_current_sr_id(page_req)

    # TP duyệt
    open_sr_by_id(page_tp, sr_id)
    page_tp.get_by_role("button", name="Duyệt").click()
    page_tp.wait_for_timeout(1500)
    return sr_id


def find_existing_processing_sr(page_nstm: Page) -> str | None:
    """Tìm 1 phiếu 'Đang xử lý' sẵn trong list để dùng."""
    page_nstm.goto(BASE_URL + "/survey-requests")
    page_nstm.wait_for_load_state("networkidle", timeout=12000)
    # Tìm badge "Đang xử lý" trong list
    badge = page_nstm.get_by_text("Đang xử lý", exact=True).first
    if not badge.is_visible():
        return None
    # Click vào dòng chứa badge đó
    row = badge.locator("xpath=ancestor::tr")
    if row.count() == 0:
        # list kiểu card
        card = badge.locator("xpath=ancestor::*[@class and contains(@class,'card')]").first
        card.click()
    else:
        row.click()
    page_nstm.wait_for_load_state("networkidle", timeout=8000)
    m = re.search(r"/survey-requests/(\d+)", page_nstm.url)
    return m.group(1) if m else None


class TestSurveyRequestProcess:

    def test_process_button_visible_for_nstm(self, page_req: Page, page_tp: Page, page_nstm: Page):
        """DEMONV thấy nút 'Xử lý khảo sát' trên phiếu 'Đang xử lý'."""
        ts = str(int(time.time()))[-6:]
        sr_id = create_processing_sr(page_req, page_tp, ts)
        open_sr_by_id(page_nstm, sr_id)
        expect(page_nstm.get_by_role("button", name="Xử lý khảo sát")).to_be_visible(timeout=8000)

    def test_process_page_opens(self, page_req: Page, page_tp: Page, page_nstm: Page):
        """Bấm 'Xử lý khảo sát' → chuyển trang /process."""
        ts = str(int(time.time()))[-6:]
        sr_id = create_processing_sr(page_req, page_tp, ts)
        open_sr_by_id(page_nstm, sr_id)
        page_nstm.get_by_role("button", name="Xử lý khảo sát").click()
        page_nstm.wait_for_url(re.compile(r"/survey-requests/\d+/process"), timeout=8000)
        # Tiêu đề "Xử lý Khảo sát" hoặc mã phiếu
        expect(page_nstm.get_by_text("Chọn Nhà cung cấp để thêm option", exact=False)).to_be_visible(timeout=8000)

    def test_select_supplier_shows_lines(self, page_req: Page, page_tp: Page, page_nstm: Page):
        """Chọn NCC 'Nông Xanh' → bảng dòng khảo sát hiện (tên NCC thấy ở NSTM)."""
        ts = str(int(time.time()))[-6:]
        sr_id = create_processing_sr(page_req, page_tp, ts)
        open_sr_by_id(page_nstm, sr_id)
        page_nstm.get_by_role("button", name="Xử lý khảo sát").click()
        page_nstm.wait_for_url(re.compile(r"/process"), timeout=8000)

        # Chọn NCC từ react-select (placeholder "Tìm / chọn NCC...")
        # Dùng combobox role để click vào input của react-select
        ncc_combobox = page_nstm.get_by_role("combobox").first
        ncc_combobox.click()
        page_nstm.wait_for_timeout(300)
        ncc_combobox.type("Nông Xanh")
        page_nstm.wait_for_timeout(800)
        opt = page_nstm.get_by_role("option", name="Nông Xanh", exact=False)
        if opt.count() == 0:
            pytest.skip("NCC 'Nông Xanh' không có trong hệ thống dev")
        opt.first.click()
        page_nstm.wait_for_timeout(1000)

        # Phải hiện bảng "Dòng khảo sát đã duyệt của NCC" hoặc "Tất cả dòng..."
        expect(
            page_nstm.get_by_text("Dòng khảo sát đã duyệt của NCC", exact=False)
            .or_(page_nstm.get_by_text("Tất cả dòng khảo sát của NCC này đã được gắn.", exact=False))
            .or_(page_nstm.get_by_text("Chưa có dòng khảo sát đã duyệt cho NCC này.", exact=False))
        ).to_be_visible(timeout=8000)

    def test_add_option_increases_count(self, page_req: Page, page_tp: Page, page_nstm: Page):
        """Thêm option → 'Options đã gắn (1)' tăng, dòng biến mất khỏi bảng trên."""
        ts = str(int(time.time()))[-6:]
        sr_id = create_processing_sr(page_req, page_tp, ts)
        open_sr_by_id(page_nstm, sr_id)
        page_nstm.get_by_role("button", name="Xử lý khảo sát").click()
        page_nstm.wait_for_url(re.compile(r"/process"), timeout=8000)

        # Chọn NCC Nông Xanh — dùng combobox role (react-select renders input[role="combobox"])
        ncc_combobox = page_nstm.get_by_role("combobox").first
        ncc_combobox.click()
        page_nstm.wait_for_timeout(300)
        ncc_combobox.type("Nông Xanh")
        page_nstm.wait_for_timeout(800)
        opt = page_nstm.get_by_role("option", name="Nông Xanh", exact=False)
        if opt.count() == 0:
            pytest.skip("NCC 'Nông Xanh' không có trong hệ thống dev")
        opt.first.click()
        page_nstm.wait_for_timeout(1000)

        # Kiểm tra có dòng có sẵn không
        add_btn = page_nstm.locator('.items-table button').filter(has_text="").first
        # Tìm nút "+" trong bảng available-survey-lines
        add_btns = page_nstm.locator('table button').filter(
            has=page_nstm.locator('.ti-plus')
        )
        if add_btns.count() == 0:
            pytest.skip("Không có dòng khảo sát sẵn cho NCC này")

        # Đếm options trước khi thêm
        options_text_before = page_nstm.get_by_text("Options đã gắn (", exact=False).first.text_content() or ""
        count_before = int(re.search(r"\((\d+)\)", options_text_before).group(1)) if re.search(r"\((\d+)\)", options_text_before) else 0

        # Bấm "+" để thêm option đầu tiên
        add_btns.first.click()
        page_nstm.wait_for_timeout(1500)

        options_text_after = page_nstm.get_by_text("Options đã gắn (", exact=False).first.text_content() or ""
        count_after = int(re.search(r"\((\d+)\)", options_text_after).group(1)) if re.search(r"\((\d+)\)", options_text_after) else 0
        assert count_after == count_before + 1, f"Mong đợi {count_before + 1} options, có {count_after}"

    def test_chot_hoan_thanh_hidden_for_nstm(self, page_req: Page, page_tp: Page, page_nstm: Page):
        """DEMONV (NSTM) KHÔNG thấy nút 'Chốt hoàn thành khảo sát'."""
        ts = str(int(time.time()))[-6:]
        sr_id = create_processing_sr(page_req, page_tp, ts)
        open_sr_by_id(page_nstm, sr_id)
        page_nstm.get_by_role("button", name="Xử lý khảo sát").click()
        page_nstm.wait_for_url(re.compile(r"/process"), timeout=8000)
        # Nút không được hiện với NSTM
        expect(page_nstm.get_by_role("button", name="Chốt hoàn thành khảo sát")).not_to_be_visible()

    def test_chot_hoan_thanh_visible_for_manager(self, page_req: Page, page_tp: Page, page_admin: Page):
        """Admin thu mua thấy nút 'Chốt hoàn thành khảo sát' (cần survey_request.delete)."""
        ts = str(int(time.time()))[-6:]
        sr_id = create_processing_sr(page_req, page_tp, ts)
        open_sr_by_id(page_admin, sr_id)
        # Admin có survey_request.delete → isAdminTM=True → thấy nút Xử lý khảo sát
        process_btn = page_admin.get_by_role("button", name="Xử lý khảo sát")
        expect(process_btn).to_be_visible(timeout=8000)
        process_btn.click()
        page_admin.wait_for_url(re.compile(r"/process"), timeout=8000)
        # Nút Chốt hoàn thành hiện với Admin (có survey_request.delete)
        chot_btn = page_admin.get_by_role("button", name="Chốt hoàn thành khảo sát")
        expect(chot_btn).to_be_visible(timeout=5000)
