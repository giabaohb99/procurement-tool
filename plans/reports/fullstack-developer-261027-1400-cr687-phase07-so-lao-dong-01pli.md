# Phase 07 — B2 Sổ quản lý lao động + B3 mẫu 01/PLI (duoc-CR-687)

Status: DONE_WITH_CONCERNS (code + test xanh; vài điểm cần đại ca/frontend chốt, xem cuối)

## Files
New `backend/app/modules/labor_register/` (11 tệp, mỗi tệp < 200 dòng):
- `people_data.py` — `PersonRow`, `load_people` (2 truy vấn cố định: nhân sự, HĐ), chọn HĐ, lịch sử lương, cờ thiếu thông tin
- `report_service.py` — `ReportKind` BOOK/USAGE, `build_summary`, `build_rows` (chung hai báo cáo)
- `report_inputs.py` — `build_inputs` + `ensure_hr_permissions` (403 nói rõ `employee_sensitive.read` / `labor_contract.read`)
- `register_controller.py` (`/api/labor-register`, hàm `labor_register_summary`), `usage_report_controller.py` (`/api/labor-usage-report`, hàm `labor_usage_summary`)
- `leave_days.py` — ngày nghỉ có/không lương trong kỳ (tái dùng `leave/report_day_split.py`, chỉ đơn đã duyệt, bỏ `is_deleted`)
- `export_common.py`, `labor_book_export.py` (B2, 25 cột = 24 theo spec + cột «Thiếu thông tin bắt buộc»), `form_01_pli_layout.py`, `form_01_pli_export.py` (B3)
Sửa: `backend/app/main.py` (2 import + 2 include, đặt cạnh router B1), `assistant/tools/report_summary_tool.py` (mở `labor_book`, `labor_usage_report`), `test/backend/test_phan_quyen_bao_cao_gac_duong.py` (6 đường vào GATED).
Test mới: `test_bao_cao_so_lao_dong_cr687.py` (20), `test_bao_cao_mau_01_pli_cr687.py` (14).

## Kết quả test
`-k "cr687 or gac_duong or assistant_report_summary"` -> 139 passed. `import app.main` sạch. Không chạy full suite, không commit.

## Quyết định
- Gác: route `require(employee, read|export)` + `require_report`; `build_inputs` đòi thêm 2 quyền, chạy ở cả 3 đường. `apply_scope` cho cả `Employee` và `LaborContract` (HĐ ngoài phạm vi coi như chưa có).
- Tập người: `hire_date <= cuối kỳ` (thiếu thì `created_at`), `status != resigned` hoặc `resign_date >= đầu kỳ`. Người «Đã nghỉ» mà không có `resign_date` bị loại (không biết nghỉ lúc nào) — ghi trong `notes`.
- HĐ: `as_of = min(cuối kỳ, hôm nay)`; ưu tiên HĐ đã ký còn hiệu lực (kể cả chấm dứt sau `as_of`), không có thì HĐ bắt đầu gần nhất trước đó; HĐ bắt đầu sau `as_of` bị bỏ.
- `/rows` không trả CCCD/BHXH/ngày sinh/địa chỉ/lương (có test); chỉ có tên nhãn các trường còn thiếu ở cột «Thiếu».
- B3 cột 12 = lương cơ bản HĐ, cột 16 = phụ cấp tổng của HĐ, cột 20–24 theo loại HĐ (không xác định -> 20; xác định -> 21–22; còn lại -> 23–24), cột 27 «Nghỉ việc ngày …» nếu nghỉ trong kỳ. Dòng Tổng: số người + đếm «x» cột 8–11.
- Sổ B2: «Nâng lương» = mọi mức lương khác nhau liền kề của các HĐ ≤ `as_of`: `dd/mm/yyyy: 8.000.000 → dd/mm/yyyy: 9.500.000`; chấm dứt = ngày chấm dứt HĐ (hoặc `resign_date`), lý do = `terminate_reason` của HĐ.

## Lưu ý / cần chốt
1. Nhãn tiêu đề 3 tầng của 01/PLI lấy từ `doc/erp/hrm/05-bao-cao-nhan-su.md`, KHÔNG có bản mẫu chính thức để đối chiếu từng chữ (nhất là nhóm cột 13–17 và 18–19). Nhân sự nên so với mẫu Phụ lục I NĐ 145/2020 trước khi nộp; sửa ở `form_01_pli_layout.HEADER_CELLS`.
2. `ROUTE_SPECS` của `test_phan_quyen_bao_cao_gac_duong.py` KHÔNG thêm 2 khóa mới: các bài trong đó chỉ cấp quyền `employee` nên sẽ ăn 403 thêm vì cổng nhạy cảm/HĐLĐ. Phần gác tương đương nằm ở test cr687 (cả 3 đường).
3. Đường giao diện cho trợ lý: `/report/labor-book`, `/report/labor-usage` (đặt trong `ReportRoute.path`) — frontend agent cần dùng đúng hai đường này hoặc báo để đổi.
4. Chưa làm theo phạm vi spec: HDSD/RAG, change-log, nhật ký task (ngoài phần sở hữu của phase).

## Unresolved questions
- Người «Đã nghỉ» không có ngày nghỉ: loại khỏi báo cáo có ổn không, hay muốn đưa vào kèm cảnh báo?
- Cột «Quốc tịch» để trống; có muốn mặc định «Việt Nam»?

**Status:** DONE_WITH_CONCERNS
**Summary:** B2 và B3 chạy đủ ba đường, hai tệp Excel dựng bằng openpyxl, test CR-687 + gác đường + trợ lý đều xanh (139).
**Concerns/Blockers:** nhãn tiêu đề mẫu 01/PLI chưa đối chiếu bản chính thức; ROUTE_SPECS không thêm 2 khóa mới (lý do ở mục 2).
