# CR-686 phase 02 — sửa/bù A1, C1, C2

## A1 Biến động nhân sự (`employee/`)
- `department_id` lọc sau apply_scope (thread qua `scoped_employee_query`, hire/resign/as_of).
- notes: đếm hồ sơ đang làm thiếu `hire_date`; câu "chưa lưu lịch sử điều chuyển" viết lại (có ở Quá trình công tác, báo cáo chưa đọc).
- `meta.drilldown_metrics` = new_hires, departures, headcount_end; route `/summary/rows` (cùng guard), dùng lại hire_events/resign_events/employees_as_of + DimensionSpec của /summary; không cột nhạy cảm.
- Tệp mới: `report_headcount_spec.py` (spec tách khỏi service), `report_headcount_gaps.py` (missing_resign_count chuyển sang đây + missing_hire_count), `report_drill_rows.py`. `HeadcountEvent` thêm `employee_id` (cuối, mặc định 0).

## C1 Nghỉ phép (`leave/`)
- Chia ngày theo kỳ/mốc: `report_day_split.py` (nạp đơn vắt biên, trọng số ngày theo lịch + lễ + leave_mask, theo từng khoảng, chia dòng theo tỷ lệ, tổng trọng số 0 → chia đều ngày lịch, loại `exclude_holiday=False` đếm lịch dương) + `report_day_split_apply.py` (cộng CHÊNH LỆCH lên Tổng/nhóm/Top loại nghỉ/xu hướng). Đơn gọn trong một mốc giữ đường SQL. Đếm đơn/người/tỷ lệ/thời gian duyệt vẫn theo ngày bắt đầu.
- Chỉ số mới: `days_unpaid` (JOIN LeaveType.is_paid trong line_aggregate), `requests_pending_over_3d` (header_aggregate, 72h UTC), `avg_days_per_person` (DERIVED kind days scale 1).
- `department_id` theo `LeaveRequest.department_id`; `meta.drilldown_metrics`; `/summary/rows` (requests, days_approved, days_pending, requests_pending_over_3d; cột "Số ngày trong kỳ" cộng lại = con số trên bảng).
- Tách: `report_sql_merge.py` (totals_dict/merge_dim_rows/ZERO_METRICS, metrics tái xuất), `report_spec.py` (spec + load_type_info), `report_drill_rows.py`. `scoped_requests` thêm `scoped_base` + `department_id`.
- Truy vấn: 16 cố định (summary group_by=department, cả 5 và 50 đơn vắt biên); chia ngày thêm tối đa ~8 câu (đơn, dòng, khoảng(+1 nếu thiếu dòng khoảng), 3 lịch, ngày lễ) chỉ khi có đơn vắt biên.

## C2 Quỹ phép (`leave/balance_report_*`)
- `employee_status` working(mặc định)|resigned|all (working = status≠resigned và is_active; resigned = phần bù) — lọc bằng truy vấn con ngay trong câu quỹ; `department_id` theo phòng HIỆN TẠI; 422 giá trị lạ.
- Chỉ số: allocated, seniority, carried, adjusted, carried_expired (`carried_expired_days`), people_over_quota, people_unused (distinct employee), snapshot `people_missing_balance` (chỉ Tổng; phạm vi theo `apply_scope(Employee,"employee")`, loại `counts_balance=True`, bỏ người vào làm sau cuối năm).
- `/summary/rows`: remaining, people_over_quota, people_unused, carried_expired, people_missing_balance (cột riêng, bỏ qua group).
- Tệp mới: `balance_report_spec.py`, `balance_report_missing.py`, `balance_report_drill_rows.py`.

## Test
- Mới: `test_bao_cao_bien_dong_cr686.py` (10), `test_bao_cao_nghi_phep_chia_ngay_cr686.py` (22), `test_bao_cao_quy_phep_cr686.py` (14) — gồm 403/422/lọc nhóm/route không bị `/{id}` nuốt/đếm truy vấn.
- Sửa `test_bao_cao_nghi_phep_gom_sql.py` (đối chiếu bản đông cứng): gỡ khóa mới (days_unpaid, requests_pending_over_3d, avg_days_per_person, drilldown_metrics) + notes khỏi bản mới trước khi so; bỏ `days_approved/days_pending` khỏi XU HƯỚNG ngày (đơn 10–14/01 nay chia từng ngày, đổi có chủ đích). Mọi số khác khớp từng chữ.
- Chạy: `-k "cr686 or nghi_phep or quy_phep or bao_cao_nhan_su or pham_vi_luat_bat_bien or assistant_report_summary or phan_quyen_bao_cao_gac_duong or bao_cao_cache"`: 647 pass, 1 fail ngoài phạm vi (`test_assistant_report_summary_cr208::test_moi_khoa_bao_cao_deu_co_route_va_dung_khoa_gac` đỏ vì ReportKey 17/18 mới chưa có route — việc của agent phase 03/04). `import app.main` OK. Mọi tệp < 200 dòng.

## Cần lưu ý / câu hỏi mở
- `.claude/rules/hr-leave.md` còn câu "Báo cáo theo tháng neo ngày bắt đầu đơn (đã chốt)" — nay chỉ đúng cho SỐ ĐƠN; số NGÀY đã chia theo kỳ. Coordinator cập nhật rule + `doc/erp/hrm/02-nghi-phep.md`/05-bao-cao.
- Lịch/lễ của đơn lấy theo employee_id + phòng/công ty CHÉP trên đơn (không đọc lại hồ sơ hiện tại).
- `date_range` chặn 400 ngày: đơn dài hơn 400 ngày bị cắt khi tính trọng số/lễ (hiếm).
- `people_on_leave` chỉ đếm đơn bắt đầu trong kỳ nên `avg_days_per_person` là ước lượng khi có đơn vắt kỳ (đã ghi trong notes).
- Chưa cập nhật HDSD/help/change-log/nhật ký task (ngoài chủ tệp).

## Vòng sửa sau code review (6 mục)
1. Ngày lễ lặp: `report_day_split._holidays_chunked` nạp theo khúc ≤ 400 ngày (số truy vấn theo độ dài cửa sổ ≈ số năm, không theo số đơn). Bài `TestNgayLeLapKyDai` (đơn 31/08–02/09 + đơn dài từ 02/06/2025).
2. `people_unused` xét THEO NGƯỜI (`BalanceRow.person_unused`, cộng mọi dòng quỹ của người). Drilldown `people_over_quota`/`people_unused` = MỘT dòng mỗi người (cộng dồn, cột Loại nghỉ ghi các loại) → `total` khớp số trên bảng. Bài `TestChuaNghiTheoNguoi`.
3. Xóa `_SHARE_EPS`, `DAY_KEYS`.
4. `requests_pending_over_3d` (SQL + rows) so với `datetime.now()` (cùng đồng hồ `request_service` ghi `submitted_at`), có chú thích.
5. A1 drilldown «Ngày vào làm» trả `hire_date` thật (None = trống), bài kiểm mới.
6. `balance_report_drill_rows` quét Employee 1 lần (mã+tên+phòng).
Test: `-k "cr686 or nghi_phep or quy_phep or bao_cao_nhan_su"` + `test_bao_cao_nghi_phep_gom_sql.py`: xanh (538 + 26). Mọi tệp < 200 dòng.
