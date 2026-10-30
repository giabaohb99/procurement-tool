"""Bố cục MẪU SỐ 01/PLI (Phụ lục I Nghị định 145/2020): tiêu đề bảng 3 tầng và cách đặt một người vào 27 cột.

Tiêu đề khai dạng `(tầng đầu, cột đầu, tầng cuối, cột cuối, chữ)` — tầng 0..2 tính từ dòng tiêu đề đầu;
ô nào trải nhiều tầng / cột thì được gộp. Nhãn các nhóm lấy theo `doc/erp/hrm/05-bao-cao-nhan-su.md` (B3);
Nhân sự nên đối chiếu lại với bản mẫu chính thức trước khi nộp.
"""
from __future__ import annotations

from app.core.labor_contract_codes import LaborContractType as T
from app.modules.employee.constants import (GENDER_LABELS, JOB_CATEGORY_HIGH_SKILL, JOB_CATEGORY_MANAGER,
                                            JOB_CATEGORY_MID_SKILL, JOB_CATEGORY_OTHER)

from .people_data import PersonRow

NUM_COLS = 27
HEADER_CELLS: list[tuple[int, int, int, int, str]] = [
    #  Đối chiếu bản PDF Mẫu số 01/PLI Phụ lục I Nghị định 145/2020 (27/10/2026): nhãn và cách gộp ô
    #  giữ ĐÚNG câu chữ của mẫu — Sở Nội vụ soi theo mẫu, đừng "viết lại cho dễ đọc".
    (0, 1, 2, 1, "STT"), (0, 2, 2, 2, "Họ tên"), (0, 3, 2, 3, "Mã số BHXH"),
    (0, 4, 2, 4, "Ngày tháng năm sinh"), (0, 5, 2, 5, "Giới tính"),
    (0, 6, 2, 6, "Số CCCD/CMND/Hộ chiếu"), (0, 7, 2, 7, "Cấp bậc, chức vụ, chức danh nghề, nơi làm việc"),
    (0, 8, 0, 11, "Vị trí việc làm (2)"),
    (1, 8, 2, 8, "Nhà quản lý"), (1, 9, 2, 9, "Chuyên môn kỹ thuật bậc cao"),
    (1, 10, 2, 10, "Chuyên môn kỹ thuật bậc trung"), (1, 11, 2, 11, "Khác"),
    (0, 12, 0, 17, "Tiền lương"),
    (1, 12, 2, 12, "Hệ số/ Mức lương"), (1, 13, 1, 17, "Phụ cấp"),
    (2, 13, 2, 13, "Chức vụ"), (2, 14, 2, 14, "Thâm niên VK (%)"), (2, 15, 2, 15, "Thâm niên nghề (%)"),
    (2, 16, 2, 16, "Phụ cấp lương"), (2, 17, 2, 17, "Các khoản bổ sung"),
    (0, 18, 0, 19, "Ngành/nghề nặng nhọc, độc hại"),
    (1, 18, 2, 18, "Ngày bắt đầu"), (1, 19, 2, 19, "Ngày kết thúc"),
    (0, 20, 0, 24, "Loại và hiệu lực hợp đồng lao động"),
    (1, 20, 2, 20, "Ngày bắt đầu HĐLĐ không xác định thời hạn"),
    (1, 21, 1, 22, "Hiệu lực HĐLĐ xác định thời hạn"), (2, 21, 2, 21, "Ngày bắt đầu"), (2, 22, 2, 22, "Ngày kết thúc"),
    (1, 23, 1, 24, "Hiệu lực HĐLĐ khác (dưới 1 tháng, thử việc)"), (2, 23, 2, 23, "Ngày bắt đầu"),
    (2, 24, 2, 24, "Ngày kết thúc"),
    (0, 25, 2, 25, "Thời điểm đơn vị bắt đầu đóng BHXH"), (0, 26, 2, 26, "Thời điểm đơn vị kết thúc BHXH"),
    (0, 27, 2, 27, "Ghi chú"),
]
COLUMN_WIDTHS = {1: 5, 2: 22, 3: 15, 4: 12, 5: 8, 6: 15, 7: 30, 12: 14, 27: 24}
JOB_CATEGORY_COLUMN = {JOB_CATEGORY_MANAGER: 8, JOB_CATEGORY_HIGH_SKILL: 9, JOB_CATEGORY_MID_SKILL: 10,
                       JOB_CATEGORY_OTHER: 11}
NOTE_JOB_CATEGORY = ("(2) Vị trí việc làm: Nhà quản lý là người giữ chức vụ quản lý, điều hành; Chuyên môn kỹ thuật "
                     "bậc cao là nghề đòi hỏi trình độ đại học trở lên; Chuyên môn kỹ thuật bậc trung là nghề đòi hỏi "
                     "trình độ cao đẳng, trung cấp; còn lại ghi vào cột \"Khác\". Đánh dấu \"x\" vào một cột tương ứng.")
BLANK_NOTE = ("Các cột 13–15, 17, 18–19, 25–26 chưa có dữ liệu trong hệ thống: Nhân sự điền tay trước khi nộp.")


def contract_columns(r: PersonRow) -> dict[int, object]:
    """Cột 20–24 theo loại HĐ: không xác định thời hạn → 20; xác định thời hạn → 21–22; loại khác → 23–24."""
    if not r.contract_type:
        return {}
    if r.contract_type == int(T.INDEFINITE):
        return {20: r.contract_start}
    if r.contract_type == int(T.FIXED_TERM):
        return {21: r.contract_start, 22: r.contract_end}
    return {23: r.contract_start, 24: r.contract_end}


def row_values(n: int, r: PersonRow, department: str) -> dict[int, object]:
    """Giá trị các cột của một người (cột vắng = để trống). Ngày là `date`, số tiền là `int`."""
    note = f"Nghỉ việc ngày {r.resign_date:%d/%m/%Y}" if r.left_in_period and r.resign_date else ""
    values: dict[int, object] = {
        1: n, 2: r.employee_name, 3: r.social_insurance_no, 4: r.date_of_birth, 5: GENDER_LABELS.get(r.gender, ""),
        6: r.id_number, 7: ", ".join(p for p in (r.position, department) if p),
        JOB_CATEGORY_COLUMN[r.job_category]: "x", 12: r.base_salary or None, 16: r.allowance or None, 27: note}
    values.update(contract_columns(r))
    return values
