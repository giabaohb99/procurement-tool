"""Khóa BÁO CÁO (phân hệ Báo cáo) — số đã cấp KHÔNG ĐỔI, KHÔNG TÁI DÙNG.

R2/QĐ-11: cột MỚI mang nghĩa loại/kiểu phải là `SMALLINT` + `IntEnum`, không phải
mã chuỗi (ngoại lệ QĐ-9 chỉ dành cho 12 cột Thu mua đã liệt kê ở
`status_codes.py` — không phải giấy phép cho cột mới). `tab_report_access.report_key`
dùng bộ số này.

Luật bất biến — đọc trước khi sửa:
  - Số đã cấp cho một báo cáo thì GIỮ NGUYÊN mãi mãi, không gán lại cho báo cáo
    khác (một dòng `tab_report_access` cũ sẽ áp NHẦM báo cáo nếu số bị tái dùng).
  - Báo cáo bị bỏ thì để TRỐNG số đó (không dồn số xuống) — cùng luật với
    `product_code` (xem `doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md`).
  - Báo cáo mới → cấp số TIẾP THEO sau số lớn nhất đang có, không chèn vào giữa.

Thuần stdlib (không import SQLAlchemy) vì `code_sets.py` phải nạp được ở máy
không cài SQLAlchemy (chạy `scripts/gen_status_ts.py`) — cùng lý do tách
`forum_codes.py` khỏi `forum/model.py`. Khác forum: `report_access/model.py`
không cần chính `ReportKey` để khai cột (chỉ `SmallInteger` trần), nên IntEnum +
nhãn + đăng ký bộ mã gộp một tệp duy nhất.

Nhãn ở `REPORT_META` PHẢI KHỚP `label` trong danh mục FE
(`frontend-v2/src/modules/report/config/report-catalog-*.ts`) — test FE giữ
khớp 1-1 (xem phase 05 của plan `261002-0836-phan-quyen-tung-bao-cao`).
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class ReportKey(IntEnum):
    """28 báo cáo đang chạy (số 25 đã bỏ, để trống) của phân hệ Báo cáo — bảng khóa ↔ tệp controller nằm ở
    phase-02 của plan `261002-0836-phan-quyen-tung-bao-cao`."""

    PURCHASE_REPORT = 1      # Báo cáo mua hàng (Thu mua)
    PR_LINES = 2              # Chi tiết YC mua hàng (Thu mua)
    SURVEY_PROGRESS = 3       # Tiến độ báo giá (Thu mua)
    PURCHASE_PROGRESS = 4     # Tiến độ đơn mua hàng (Thu mua) — đổi nhãn bao-CR-691, giữ khóa
    SURVEY_REPORT = 5         # Báo cáo khảo sát (Thu mua)
    HR_HEADCOUNT = 6          # Biến động nhân sự (Nhân sự)
    LEAVE_USAGE = 7           # Tình hình nghỉ phép (Nhân sự)
    LEAVE_BALANCE = 8         # Quỹ phép năm (Nhân sự)
    VEHICLE_BOOKING = 9       # Báo cáo đặt xe (Hành chính)
    SEAL_REQUEST = 10         # Báo cáo đóng dấu (Hành chính)
    DOCUMENT = 11             # Báo cáo văn bản (Hành chính)
    APPROVAL = 12             # Báo cáo phê duyệt (Hành chính)
    WORK = 13                 # Công việc & Dự án (Dự án)
    USAGE_PROFILE = 14        # Hồ sơ cách làm việc (Quản trị) — duoc-CR-641
    FEATURE_USAGE = 15        # Mức dùng chức năng (Quản trị) — duoc-CR-655; gom theo phòng ban, không theo người
    WORK_CAPABILITY = 16      # Năng lực theo loại việc (Quản trị) — duoc-CR-657; số theo TỪNG NGƯỜI, mặc định chỉ admin
    LABOR_CONTRACT = 17       # Hợp đồng lao động (Nhân sự) — duoc-CR-686; danh sách có lương
    HR_PROFILE_GAPS = 18      # Hồ sơ & tài khoản còn thiếu (Nhân sự) — duoc-CR-686
    LABOR_BOOK = 19           # Sổ quản lý lao động (Nhân sự) — duoc-CR-687; có CCCD, BHXH, lương
    LABOR_USAGE_REPORT = 20   # Báo cáo sử dụng lao động mẫu 01/PLI (Nhân sự) — duoc-CR-687
    PAYROLL_FUND = 21         # Quỹ lương theo pháp nhân (Nhân sự) — duoc-CR-688; số lương, mặc định chỉ admin
    BENEFIT_AUDIENCE = 22     # Phúc lợi & sự kiện (Nhân sự) — duoc-CR-688
    MANAGEMENT_SPAN = 23      # Cơ cấu quản lý (Nhân sự) — duoc-CR-688
    WORK_MOVES = 24           # Điều chuyển & bổ nhiệm (Nhân sự) — duoc-CR-688
    #  25 = «Định biên kế hoạch so với thực tế» — ĐÃ BỎ duoc-CR-692, KHÔNG tái cấp số này (xóa cả dòng `tab_report_access` khóa 25).
    ATTENDANCE_DAILY = 26     # Có mặt theo ngày (Nhân sự) — duoc-CR-689
    PROFILE_CHANGES = 27      # Yêu cầu sửa hồ sơ (Nhân sự) — duoc-CR-689
    ROOM_USAGE = 28           # Sử dụng phòng họp (Nhân sự) — duoc-CR-689
    LEGAL_WATCH = 29          # Đối tượng cần chú ý theo luật (Nhân sự) — duoc-CR-689; có ngày sinh, con nhỏ


#  Số đã cấp rồi BỎ (để trống, không tái cấp) — test «khóa liên tục» cho phép đúng các khoảng trống này.
RETIRED_REPORT_KEYS: frozenset[int] = frozenset({25})   # «Định biên kế hoạch so với thực tế», bỏ duoc-CR-692


#  {khóa: (nhãn, nhóm phân hệ)} — nhãn KHỚP `label`, nhóm KHỚP `group` ở danh
#  mục FE (`report-catalog-*.ts`).
REPORT_META: dict[ReportKey, tuple[str, str]] = {
    ReportKey.PURCHASE_REPORT: ("Báo cáo mua hàng", "Thu mua"),
    ReportKey.PR_LINES: ("Chi tiết YC mua hàng", "Thu mua"),
    ReportKey.SURVEY_PROGRESS: ("Tiến độ báo giá", "Thu mua"),
    ReportKey.PURCHASE_PROGRESS: ("Tiến độ đơn mua hàng", "Thu mua"),
    ReportKey.SURVEY_REPORT: ("Báo cáo khảo sát", "Thu mua"),
    ReportKey.HR_HEADCOUNT: ("Biến động nhân sự", "Nhân sự"),
    ReportKey.LEAVE_USAGE: ("Tình hình nghỉ phép", "Nhân sự"),
    ReportKey.LEAVE_BALANCE: ("Quỹ phép năm", "Nhân sự"),
    ReportKey.VEHICLE_BOOKING: ("Báo cáo đặt xe", "Hành chính"),
    ReportKey.SEAL_REQUEST: ("Báo cáo đóng dấu", "Hành chính"),
    ReportKey.DOCUMENT: ("Báo cáo văn bản", "Hành chính"),
    ReportKey.APPROVAL: ("Báo cáo phê duyệt", "Hành chính"),
    ReportKey.WORK: ("Công việc & Dự án", "Dự án"),
    ReportKey.USAGE_PROFILE: ("Hồ sơ cách làm việc", "Quản trị"),
    ReportKey.FEATURE_USAGE: ("Mức dùng chức năng", "Quản trị"),
    ReportKey.WORK_CAPABILITY: ("Năng lực theo loại việc", "Quản trị"),
    ReportKey.LABOR_CONTRACT: ("Hợp đồng lao động", "Nhân sự"),
    ReportKey.HR_PROFILE_GAPS: ("Hồ sơ & tài khoản còn thiếu", "Nhân sự"),
    ReportKey.LABOR_BOOK: ("Sổ quản lý lao động", "Nhân sự"),
    ReportKey.LABOR_USAGE_REPORT: ("Báo cáo sử dụng lao động (01/PLI)", "Nhân sự"),
    ReportKey.PAYROLL_FUND: ("Quỹ lương theo pháp nhân", "Nhân sự"),
    ReportKey.BENEFIT_AUDIENCE: ("Phúc lợi & sự kiện", "Nhân sự"),
    ReportKey.MANAGEMENT_SPAN: ("Cơ cấu quản lý", "Nhân sự"),
    ReportKey.WORK_MOVES: ("Điều chuyển & bổ nhiệm", "Nhân sự"),
    ReportKey.ATTENDANCE_DAILY: ("Có mặt theo ngày", "Nhân sự"),
    ReportKey.PROFILE_CHANGES: ("Yêu cầu sửa hồ sơ", "Nhân sự"),
    ReportKey.ROOM_USAGE: ("Sử dụng phòng họp", "Nhân sự"),
    ReportKey.LEGAL_WATCH: ("Đối tượng cần chú ý theo luật", "Nhân sự"),
}

#  `value` là SỐ VIẾT DƯỚI DẠNG CHUỖI — khung `status_catalog` dùng mã chuỗi,
#  cùng lối `forum_codes.py`. `sort_order` = chính con số khóa, để FE/BE liệt
#  kê cùng một thứ tự (khóa nhỏ lên trước — không phải thứ tự theo nhóm).
REPORT_KEY_SET = register(CodeSet("report_key", "Báo cáo", [
    Code(str(int(key)), label, sort_order=int(key))
    for key, (label, _group) in REPORT_META.items()
]))
