# Phase 11 — A5 Quỹ lương theo pháp nhân + che nhóm nhỏ dùng chung

**Chủ:** BE-4 · **Khóa:** 21 `PAYROLL_FUND` · **Đường:** `/api/payroll-fund/summary` (+ `/export`, `/rows`) — router khung `labor_contract/payroll_report_controller.py` đã đăng ký.

## Che nhóm nhỏ dùng chung (`core/report_small_group.py`)
- Rút luật đã làm ở `employee/report_headcount_privacy.py` (CR-687) thành hàm chung: che cả nhóm khi bất kỳ chỉ số đếm/tiền nào của nhóm (kỳ này HOẶC kỳ so sánh) dựa trên < 3 người; che phụ tới khi ≥ 2 nhóm bị che và tổng người bị che ≥ 3 — **xét RIÊNG cho kỳ này và kỳ so sánh** (vá chỗ hở CR-687: Tổng kỳ so sánh trừ các nhóm).
- A2 (nhóm tuổi) chuyển sang dùng hàm chung, giữ nguyên hành vi + test cũ, thêm test kỳ so sánh.

## A5
- Gác: `require('labor_contract', read|export)` + `require_report(21)` + `apply_scope(LaborContract)`; lọc `company_id`, `department_id` (của HĐ).
- Hàng = HĐ đã ký có hiệu lực tại mốc (`as_of = min(cuối kỳ, hôm nay)`), người còn làm.
- Chỉ số (thời điểm): `people_paid` «Số người hưởng lương» · `base_total` «Tổng lương cơ bản» · `allowance_total` «Tổng phụ cấp» · `payroll_total` «Quỹ lương (lương + phụ cấp)» · `insurance_total` «Tổng lương đóng BHXH» · `avg_payroll` «Bình quân / người» · `base_min` / `base_max` «Lương cơ bản thấp nhất / cao nhất». kind `money`.
- Xu hướng: `payroll_total` và `people_paid` tại cuối mỗi mốc (tháng) trong kỳ — tính từ một lần nạp HĐ, không truy vấn theo mốc.
- Xem theo: `company` (mặc định) · `department` · `position` · `job_category` · `contract_type`.
- **Che nhóm < 3 người** (mọi người xem, kể cả admin — lương từng người chỉ xem qua danh sách): dùng hàm chung.
- `/rows`: `people_paid` (mỗi người: mã, họ tên, pháp nhân, phòng, chức vụ, loại HĐ, lương cơ bản, phụ cấp, lương BHXH). Danh sách theo nhóm bị che → 403.
- `notes`: lương thỏa thuận trên HĐ, không phải lương thực trả; chưa có quỹ lương kế hoạch / BHXH công ty đóng.
- Test: chọn HĐ tại mốc, phạm vi, che nhóm + che phụ hai kỳ, xu hướng theo tháng, số truy vấn cố định.
