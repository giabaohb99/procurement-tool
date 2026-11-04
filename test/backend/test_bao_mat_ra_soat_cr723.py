"""Rà soát bảo mật bao-CR-723 (04/11/2026) — các chốt sửa ngay trong mã.

BM-033: ô chữ mở đầu bằng = + - @ trong tệp Excel xuất ra không được thành CÔNG THỨC. Dữ liệu tra cứu thị trường đến từ tệp
tờ khai bên ngoài, nên tên hàng kiểu `=HYPERLINK(...)` mở tệp ra là chạy. `guard_formula_row` giữ nguyên chữ, chỉ ép kiểu ô.
"""
import io

import pytest
from openpyxl import Workbook, load_workbook

from app.core.export_xlsx import guard_formula_row

DANGEROUS = ["=HYPERLINK(\"http://x\",\"bam\")", "+1+1", "-2", "@SUM(A1)", "\tabc", "binh thuong", 12, None]


@pytest.mark.parametrize("write_only", [False, True])
def test_o_chu_mo_dau_bang_dau_cong_thuc_giu_nguyen_chu_khong_thanh_cong_thuc(write_only):
    wb = Workbook(write_only=write_only)
    ws = wb.create_sheet("x") if write_only else wb.active
    ws.append(guard_formula_row(ws, DANGEROUS))
    buf = io.BytesIO()
    wb.save(buf)
    got = load_workbook(io.BytesIO(buf.getvalue())).worksheets[0]
    cells = [c for c in next(got.iter_rows(min_row=1, max_row=1))]
    assert [c.value for c in cells[:7]] == DANGEROUS[:7]
    assert all(c.data_type == "s" for c in cells[:6])          # chữ — kể cả các ô mở đầu bằng = + - @ tab
    assert cells[6].data_type == "n"                            # số vẫn là số


def test_bot_mac_dinh_khong_tu_tinh_cong_thuc_excel():
    """BM-032: pycel 1.0b30 thực thi được mã từ công thức tệp lạ (PYSEC-2025-177) — cờ mặc định TẮT."""
    from app.core.config import Settings

    assert Settings.model_fields["AGENT_XLSX_EVAL_FORMULAS"].default is False
