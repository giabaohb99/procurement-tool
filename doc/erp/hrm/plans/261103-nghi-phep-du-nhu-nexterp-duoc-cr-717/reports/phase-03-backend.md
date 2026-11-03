# Phase 03 BE — báo cáo "Làm việc vào ngày lễ, ngày nghỉ" + hở nhỏ (duoc-CR-717)

Status: DONE. Không migration, không index mới (câu phiếu lọc `work_date` + `status` trên bảng nhỏ; có `ix_leave_comp_emp_date`).

## API as built (cho FE)

### 1. Báo cáo khóa 30 — `/api/holiday-work-report`
`ReportKey.HOLIDAY_WORK = 30`, REPORT_META **Làm việc vào ngày lễ, ngày nghỉ** / **Nhân sự**. TS đã sinh lại (`statuses.ts` +1 dòng). Admin tự có khóa 30 (`ensure_report_access_defaults`).
- `GET /summary` (`leave_comp_request.read`) · `GET /summary/export` (`...export`) · `GET /summary/rows` (`...read`); cả 3 gác `require_report(30)`; phạm vi `apply_scope(LeaveCompRequest)`.
- Query: chung của khung (`preset|date_from|date_to|compare|group_by`), `company_id`, `department_id` (phòng GHI TRÊN PHIẾU), `include_pending` (1/true/yes/on; mặc định false = chỉ Đã duyệt; true = thêm Chờ duyệt), `day_kind` (0 tất cả · 1 ngày lễ · 2 ngày nghỉ theo lịch; ngoài 0-2 → 422). Kỳ > 366 ngày → 422 (cả 3 đường).
- `group_by` hợp lệ: `department | company | employee | day_kind | holiday_name` (khác → 422). `day_kind` nhóm có nhãn **Ngày lễ** / **Ngày nghỉ theo lịch**; `holiday_name` nhóm ngày nghỉ theo lịch rơi vào **(Chưa gắn)**.
- Khung `build_report` chuẩn (`period·meta·totals·trend·groups?·breakdowns·notes`); trend theo `work_date`. `meta.drilldown_metrics = ["lines"]`.
- Chỉ số (`meta.metrics`): `lines` **Lượt đi làm** · `holiday_lines` **Trong đó ngày lễ** · `offday_lines` **Ngày nghỉ theo lịch** · `people` **Số người** (distinct) · `comp_days` **Ngày nghỉ bù được duyệt** (kind days, chỉ phiếu Đã duyệt) · `pending_lines` **Đang chờ duyệt** (CHỈ có khi `include_pending` bật; vắng khỏi meta khi tắt).
- `/rows?metric=lines[&group_by=&group_key=]`: cột `employee_code, employee_name, department, work_date(date), weekday, day_kind, holiday_name, days(days), status, code`; mỗi dòng có `link` `/hr/employees/{id}`. `weekday` = **Thứ 2…Thứ 7/Chủ nhật**; `status` = nhãn phiếu (**Đã duyệt**/**Chờ duyệt**). Sắp ngày → mã NV → mã phiếu. Trần 500, `total`/`truncated` theo hợp đồng chung. `metric` khác `lines` → 422; `group_key=__other__` → 422.
- Export: `report_xlsx("lam-viec-ngay-le")`, cột theo `meta.metrics`.
- `notes`: 3 câu theo spec (+1 câu khi `include_pending`).
- Assistant: `REPORTS["holiday_work"]`, path `/report/holiday-work`, extra `include_pending, day_kind, department_id`. Redis: `/api/holiday-work-report/summary` đã vào `REPORT_SUMMARY_PATHS`.
- Bộ lọc giao diện cần thêm: ô **Gồm phiếu chờ duyệt** (include_pending), **Loại ngày** (day_kind), phòng ban, pháp nhân.

### 2. Quỹ phép năm (khóa 8): chỉ số mới `comp` "Nghỉ bù cộng thêm" (kind days) — `meta.metrics`, `totals`, `groups`. Xuất Excel tự có cột. Không thêm truy vấn.

### 3. Ma trận "Tổng hợp theo người" — `GET /api/leave-balances/matrix` (+ `/matrix/export`)
- Gác `leave_balance.read` / `export` + `apply_scope(LeaveBalance)`; không có khóa báo cáo. Router đăng ký TRƯỚC `leave_balance_router` (test xác nhận không bị `/{bid}` nuốt).
- Query: `year` (0/bỏ = năm nay), `company_id`, `department_id` (phòng HIỆN TẠI), `employee_status` (`working` mặc định | `resigned` | `all`; khác → 422), `search` (mã/tên, ký tự `%` `_` được escape), `page`, `page_size`.
- Trả `data = {year, columns:[{leave_type_id, name}], items:[{employee_id, code, name, department_name, cells:{"<leave_type_id>": số còn lại}, total}], total}`. Khóa `cells` là CHUỖI. Người thiếu dòng quỹ của một loại → không có khóa đó (hiển thị **—**). Cột = loại `counts_balance` có dòng quỹ trong CẢ kết quả (không đổi theo trang), thứ tự `sort_order, id`. Ô = `available_days` (loại cộng dần trừ phần chưa tới tháng); `total` = tổng các ô của người. Sắp theo mã NV.
- Export: tối đa 5000 người, cột `Mã NV | Họ tên | Phòng ban | <mỗi loại> | Tổng còn lại`; ô thiếu = 0.
- Số truy vấn cố định (đếm người, trang người, loại, quỹ trang, loại+hire của available_days_map, tên phòng; +1 khi có phép mang sang cần thu hồi quá hạn) — có bài kiểm 2 vs 42 người.

### 4. Cấp quỹ có lọc — `POST /api/leave-balances/allocate`
Body thêm `company_id`, `department_id`, `employment_type`, `job_level` (int ≥ 0, 0 = bỏ qua; âm → 422). Lọc `Employee` TRƯỚC `apply_scope`, chỉ thu hẹp. Luật **chỉ tạo dòng thiếu** giữ nguyên. Response không đổi.

## Tệp
Tạo: `leave/holiday_work_report_{controller,service,data}.py`, `leave/balance_matrix_{controller,service}.py`, `test/backend/test_bao_cao_lam_ngay_le_cr717.py` (13 bài), `test/backend/test_nghi_phep_quy_tong_hop_cr717.py` (8 bài).
Sửa: `core/report_keys.py`, `core/report_cache.py`, `assistant/tools/report_summary_tool.py`, `main.py` (2 import + 2 include, ngay sau `leave_balance_report_router`), `leave/balance_report_spec.py`, `leave/balance_controller.py` (chỉ `allocate`), `leave/schema.py` (chỉ `LeaveBalanceAllocate`), `test_migration_bo_ke_hoach_nhan_su_cr692.py` (29 / max 30), `test_phan_quyen_bao_cao_gac_duong.py`, `frontend-v2/src/shared/constants/statuses.ts` (sinh tự động).

## Kiểm
- Mới 21 bài xanh. Hồi quy `-k bao_cao|report_access|phan_quyen_bao_cao` (51 tệp, chia 3 nhóm): 297 + 244 + 370 xanh. cr208, pham_vi_duong_vong, migration cr692, gac_duong, cap_quy/review cr715: 164 xanh.
- `test_canh_do_dai_o_chu_cr538.py::test_every_write_schema_is_mapped_to_its_table` ĐỎ — do schema phase 01 (`leave.Assignment*`, `leave.Policy*`) chưa khai vào TARGETS/NO_TARGET + 3 ca customs/forum cũ. Không do phase 03 (`LeaveBalanceAllocate` mới chỉ thêm int). Phase 01 cần khai (hoặc chủ test).
- Chưa curl local (cần token); route đã được test qua TestClient + soi `app.routes`.

## Câu hỏi còn mở
- Bài HDSD/cẩm nang AI cho báo cáo mới + `report-catalog-*.ts` (FE) + change-log/nhật ký thuộc phase khác.
