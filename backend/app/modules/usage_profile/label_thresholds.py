"""Ngưỡng nhận «kiểu làm việc» (duoc-CR-641, phase 04) — gom MỘT chỗ để chỉnh sau 2–4 tuần chạy thật.

Đây là ĐỀ XUẤT ĐẦU (plan §Luật nhận kiểu), chưa phải số đã hiệu chỉnh. Cửa sổ 4 tuần. «×med» = so với trung vị nhóm so sánh.
Nhóm `MIN_*` là dữ liệu tối thiểu: thiếu thì KHÔNG gắn nhãn (khác với «không phải kiểu này»).
"""
# 1 Làm dồn
BATCH_MONTH_END_SHARE = 0.4
BATCH_APPROVAL_SHARE = 0.5
BATCH_HEATMAP_TOP3 = 0.5
MIN_DOCS_MONTH_END = 10
MIN_DECISIONS = 10
MIN_API_CALLS = 200
# 2 Nút thắt duyệt (quyết định chủ sản phẩm: ≥ 2× trung vị nhóm VÀ ≥ 8 giờ)
BOTTLENECK_X_MEDIAN = 2.0
BOTTLENECK_MIN_HOURS = 8.0
BOTTLENECK_PENDING = 10
MIN_TASKS_DECIDED = 5
# 3 Excel song song
EXCEL_PER_WEEK = 3.0
EXCEL_PER_LIST_VIEW = 0.3
EXCEL_ENTITY_WEEKS = 3
MIN_EXPORTS = 3
# 4 Người mới vướng
NEWCOMER_TENURE_DAYS = 90
NEWCOMER_SIGNALS_NEEDED = 2
NEWCOMER_403 = 5
NEWCOMER_HELP_VIEWS = 3
NEWCOMER_ACTIVE_RATIO = 0.5
NEWCOMER_X_MEDIAN = 2.0
MIN_WORKDAYS_NEWCOMER = 5
# 5 Người thạo
MIN_ACTIVE_DAYS_POWER = 10
POWER_MIN_PREFS = 1
# 6 Hay đi lạc
WANDERER_403 = 5
WANDERER_X_MEDIAN = 2.0
WANDERER_LOOP_SHARE = 0.2
MIN_VIEWS_WANDERER = 50
# 7 Điện thoại
MOBILE_WRITE_SHARE = 0.6
MIN_WRITES_MOBILE = 20
# 8 Phiếu kém chất lượng
RETURNED_RATE = 0.2
RETURNED_X_MEDIAN = 2.0
EDITS_AFTER_SUBMIT = 0.3
MIN_SUBMITTED = 5
# 9 Nhờ làm hộ
PROXY_SHARE = 0.5
MIN_PROXY_DOCS = 5
# 10 Ít dùng
LOW_ACTIVE_RATIO = 0.4
COHORT_ACTIVE_RATIO = 0.7
MIN_WORKDAYS_LOW = 8
