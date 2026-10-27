# CR-688 Phase 11 — A5 Quỹ lương + che nhóm nhỏ dùng chung

## Files
- NEW `backend/app/core/report_small_group.py` — `suppress_small_groups(data, counts_of, size_of, note, extra_note)`.
- `backend/app/modules/employee/report_headcount_privacy.py` — A2 chuyển sang hàm chung (vẫn chỉ che khi thiếu `employee_sensitive.read`). Không đụng `employee/report_service.py`, `core/report_export.py` (cờ `suppressed` + `_blank_suppressed` đã đủ cho money).
- `backend/app/modules/labor_contract/payroll_report_controller.py` (3 route, guard kép + `apply_scope`, export dùng scope `export`), NEW `payroll_report_data.py`, `payroll_report_extras.py`, `payroll_report_service.py`.
- NEW tests `test_bao_cao_quy_luong_cr688.py` (13), `test_che_nhom_nho_cr688.py` (8); thêm 1 bài vào `test_bao_cao_co_cau_cr687.py`.

## Luật che
- Sơ cấp: nhóm có BẤT KỲ số đếm người = 1–2 ở kỳ này HOẶC kỳ so sánh -> che cả nhóm cả hai kỳ (+ `suppressed`).
- Thứ cấp xét RIÊNG từng kỳ (vá lỗ hổng CR-687): trong nhóm bị che còn người ở kỳ đó cần >=2 nhóm, tổng >=3, nếu không che thêm nhóm hiện nhỏ nhất của kỳ đó; lặp tới ổn định. Kỳ mà không có nhóm nhỏ nào còn người thì bỏ qua (tránh che thừa — chính test CR-687 mới thêm đã bắt lỗi này).
- A5 che với MỌI người xem; `/rows` của nhóm bị che -> 403 (tính lại summary cùng tham số kỳ/so sánh).

## A5
- Một lần nạp HĐ (2 truy vấn: HĐ + nhân sự) cho kỳ này, kỳ so sánh, xu hướng. Test đếm truy vấn 5 vs 50 HĐ xanh.
- Mỗi người một HĐ tại mốc (HĐ bắt đầu muộn nhất khi chồng nhau); "còn làm" tại mốc t = đang làm hoặc `resign_date > t`.
- Chỉ số: people_paid(int), base_total, allowance_total, payroll_total, insurance_total, avg_payroll(derived), base_min/base_max (tính riêng từng nhóm/tổng, khai thêm vào `meta`).
- Xu hướng: cuối mỗi tháng (min(cuối tháng, cuối kỳ, hôm nay)); tháng bắt đầu sau hôm nay bị bỏ; `compare` dời theo khoảng lùi kỳ so sánh.
- Chiều: company (mặc định FE), department, position (nhãn chữ), job_category, contract_type.

## Test
`pytest -k "cr688 or quy_luong or che_nhom or co_cau or hdld_cr686 or bao_cao_nhan_su or bien_dong"` = 143 passed.
`test_phan_quyen_bao_cao_gac_duong.py` đang đỏ (2 bài) vì chưa phân loại khóa 21–24 — thuộc coordinator.

## Concerns / câu hỏi
- Tổng (totals) không bị che: nếu lọc `department_id` còn 1–2 người thì Tổng = lương của họ; `/rows` không lọc nhóm cũng trả lương từng người (theo spec: ai có `labor_contract.read` thấy như màn HĐLĐ). Cần chủ dự án xác nhận có muốn che cả trường hợp này.
- `position` gom theo nhãn chữ trên hồ sơ (không theo `position_id`).
- Xu hướng quá khứ dùng `resign_date` để biết người còn làm; hồ sơ nghỉ việc thiếu `resign_date` bị coi nghỉ từ trước.

**Status:** DONE_WITH_CONCERNS
**Summary:** Helper chung + A2 migrate + A5 đủ 3 route, test xanh (143). Không commit.
**Concerns/Blockers:** Totals/rows không lọc nhóm vẫn lộ lương khi bộ lọc thu hẹp còn 1–2 người (xem trên); test gác đường của coordinator cần thêm khóa 21–24.
