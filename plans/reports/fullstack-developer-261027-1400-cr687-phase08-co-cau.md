# duoc-CR-687 phase 08 — A2 Cơ cấu nhân sự
Status: DONE

## Files
- NEW backend/app/modules/employee/report_headcount_dims.py (55) — age_band/normalise_location/row_dims; DOB chỉ chọn nhóm, không lưu.
- NEW backend/app/modules/employee/report_headcount_privacy.py (35) — che nhóm tuổi <3 + chặn rows 403.
- EDIT report_headcount_events.py (196): _DIM_COLS +3 cột (date_of_birth, education_level, work_location); HeadcountEvent +7 trường mặc định; _row_common(row, on) — tuổi tại ngày hire/resign/as_of.
- EDIT report_headcount_spec.py: 4 chiều age_band/education/work_location/job_category.
- EDIT report_service.py: gọi suppress sau khi gán notes. EDIT report_drill_rows.py: gọi guard 403.
- NEW test/backend/test_bao_cao_co_cau_cr687.py (25 bài). EDIT test_bao_cao_nhan_su.py: 1 assert cũ "không có chiều tuổi" nới cho phép `age_band` (vẫn cấm birth/tuoi thô).

## Hành vi
- Nhóm tuổi: lt25 · 25-34 · 35-44 · 45-54 · 55+ · "" (Chưa gắn; cả khi DOB sau mốc). Tuổi tại event_date (hire_date / resign_date / as_of).
- work_location: khóa = casefold + gộp khoảng trắng; nhãn = bản trim của hàng đầu.
- Che: thiếu employee_sensitive.read (chỉ xét khóa quyền, không ngoại lệ self) → nhóm headcount_end<3 mọi giá trị current+compare = None, thêm 1 note; totals giữ. Áp luôn cho /summary/export (test xlsx xanh).
- rows: group_by=age_band + group_key (kể cả "") thiếu quyền → 403; không group_key/chiều khác không đổi.
- Số truy vấn: không thêm truy vấn (mở rộng with_entities); test đếm 5 vs 50 người cho cả 4 chiều xanh.

## Tests
`-k "bao_cao_nhan_su or bien_dong or co_cau or cr687_co_cau"`: 50 passed; file mới riêng: 25 passed. Không chạy full.

## Lưu ý / chưa giải quyết
- Docstring/ghi chú notes cũ về "cơ cấu hiện tại" không đổi. Không cập nhật doc/ (ngoài sở hữu).
- Nhãn work_location "first seen" phụ thuộc thứ tự DB (không xác định), key ổn định.
- Chưa commit.

**Status:** DONE
**Summary:** 4 chiều cơ cấu + che nhóm tuổi nhỏ + 403 rows theo nhóm tuổi, số truy vấn cố định, test xanh.
