# Phase 06 — Nền đợt 2

**Trạng thái:** pending · **Chủ:** điều phối

- `core/report_keys.py`: `LABOR_BOOK = 19` («Sổ quản lý lao động», «Nhân sự»), `LABOR_USAGE_REPORT = 20` («Báo cáo sử dụng lao động (01/PLI)», «Nhân sự»); chạy `gen_status_ts.py`.
- `core/report_cache.py`: thêm 2 đường `/summary` mới.
- `employee/constants.py`: hàm thuần `job_category_of(job_level, education_level) -> int` + hằng số `JOB_CATEGORY_*` + `JOB_CATEGORY_LABELS` (1 Nhà quản lý · 2 bậc cao · 3 bậc trung · 9 Khác) — luật: cấp bậc ≥ Phó phòng → 1; còn lại Đại học / Sau đại học → 2; Trung cấp / Cao đẳng → 3; còn lại → 9. Không đăng ký bộ mã (nhãn đi qua `meta` của báo cáo).
- Đặt chỗ duoc-CR-687 ở change-log + nhật ký.
