# Phase 03 — BE: Báo cáo «Nhân viên làm việc vào ngày lễ» + khoảng hở nhỏ

## Context
- ERPNext `hr/report/employees_working_on_a_holiday/*.py` (lọc từ–đến, Holiday List, phòng, công ty; cột NV, ngày, trạng
  thái, tên ngày lễ), `employee_leave_balance_summary.py` (ma trận NV × loại = còn lại).
- Mẫu báo cáo DEGO: `work_schedule/attendance_report_controller.py` + `_service.py` (gác kép, `/summary`, `/export`,
  `/rows`, `build_report`, `rows_response`), `leave/balance_report_*.py`. Luật CLAUDE.md «Lớp gác thứ ba»: ReportKey →
  `gen_status_ts.py` → `report-catalog-*.ts` → `require_report` trên cả 3 đường. Memory: API báo cáo phải nhanh, số truy
  vấn cố định, có bài kiểm đếm truy vấn.
- Nguồn: `tab_leave_comp_request` (CR-715) — đã chốt «ngày lễ HOẶC ngày nghỉ theo lịch» lúc lập; ngày lễ qua
  `leave/holiday_calendar.holiday_names_many` (1 truy vấn cho nhiều pháp nhân).

## A. Báo cáo khóa 30 (D8a)
- `core/report_keys.py`: `HOLIDAY_WORK = 30` · `REPORT_META` = («Nhân viên làm việc vào ngày lễ», «Nhân sự»). Số chưa ai
  cấp — `dieu-phoi` xác nhận trước.
- Router riêng `leave/holiday_work_report_controller.py`, prefix **`/api/holiday-work-report`** (không đặt dưới
  `/api/leave-comp-requests` để khỏi bị `/{id}` nuốt): `/summary` (`require('leave_comp_request','read')`) · `/summary/export`
  (`…,'export'`) · `/summary/rows` (`read`) — cả ba `dependencies=[Depends(require_report(ReportKey.HOLIDAY_WORK))]`.
  Phạm vi: `apply_scope(db.query(LeaveCompRequest), LeaveCompRequest, "leave_comp_request", user, prof, action)`.
- Tham số: kỳ (`parse_period`, mặc định FE «Năm nay», trần 366 ngày → 422), `company_id`, `department_id`
  (`valid_*`), `include_pending` (mặc định false → chỉ `APPROVED`; true → thêm `PENDING`), `day_kind` (0 tất cả · 1 ngày lễ ·
  2 ngày nghỉ theo lịch). Lọc `is_deleted = False`, `work_date` trong kỳ.
- Dòng dữ liệu (`leave/holiday_work_report_data.py`): 1 câu phiếu (cột thô) + 1 câu ngày lễ (`holiday_names_many` cho các
  pháp nhân có trong kết quả + 0) + 1 câu tên/mã NV (IN danh sách) + tên pháp nhân/phòng chỉ khi `group_by` cần. Phân loại:
  có tên ngày lễ → `day_kind=1` kèm tên; không → `2` «Ngày nghỉ theo lịch». Phòng ban = `department_id` LƯU TRÊN PHIẾU
  (phòng lúc đi làm), ghi ở `notes`.
- Chỉ số (`MetricSpec`): `lines` «Lượt đi làm» (người-ngày) · `holiday_lines` «Trong đó ngày lễ» · `offday_lines` «Ngày
  nghỉ theo lịch» · `people` «Số người» (distinct) · `comp_days` «Ngày nghỉ bù được duyệt» (chỉ phiếu Đã duyệt) ·
  `pending_lines` «Đang chờ duyệt» (chỉ khi `include_pending`). Chiều: phòng ban · pháp nhân · nhân sự · loại ngày · tên
  ngày lễ. Xu hướng theo `work_date`. `drilldown_metrics = ["lines"]`.
- `/rows` cột: Mã NV · Họ tên · Phòng ban · Ngày · Thứ · Loại ngày · Tên ngày lễ · Số ngày bù · Trạng thái phiếu · Mã phiếu.
- `notes`: «Không có chấm công — chỉ thấy người đã lập phiếu nghỉ bù; dữ liệu có từ 02/11/2026», «Loại ngày tính theo lịch
  ngày lễ hiện hành», «Phòng ban là phòng ghi trên phiếu».
- Đăng ký: `main.py` (router), `core/report_cache.py` `REPORT_SUMMARY_PATHS` thêm `/api/holiday-work-report/summary`,
  `assistant/tools/report_summary_tool.py` `REPORTS["holiday_work"]` (bài kiểm CR-208 đòi mọi khóa mở cho trợ lý trừ 4 khóa
  đóng).

## B. Hở nhỏ (D9a)
1. **Báo cáo Quỹ phép năm (khóa 8)**: `balance_report_spec` thêm `BalanceRow.comp` + `MetricSpec("comp", "Nghỉ bù cộng
   thêm", kind="days")` — cột `comp_days` đã có trong `BAL_COLS`, không thêm truy vấn.
2. **Tổng hợp theo người** (ma trận ERPNext Leave Balance Summary) — router riêng `leave/balance_matrix_controller.py`
   (`/api/leave-balances/matrix` + `/matrix/export`), gác `leave_balance` read / export + `apply_scope(LeaveBalance)`;
   đăng ký `main.py` **TRƯỚC** `leave_balance_router` (nếu không `/{bid}` nuốt → 422). Tham số `year`, `company_id`,
   `department_id`, `employee_status` (dùng lại `balance_report_spec.valid_employee_status/employee_conds`), `search`,
   phân trang. Trả `{columns:[{leave_type_id, name}], items:[{employee_id, code, name, department_name, cells:{type_id:
   available}, total}], total}`; số = `available_days_map` (trừ phần chưa tới tháng). Cột = loại `counts_balance` có ít nhất
   một dòng quỹ trong kết quả. Service `leave/balance_matrix_service.py`; số truy vấn cố định (đếm + trang người + quỹ +
   loại + hire + tên phòng). Xuất Excel `xlsx_response` cột động.
3. **Cấp quỹ có lọc**: `schema.LeaveBalanceAllocate` thêm `company_id`, `department_id`, `employment_type`, `job_level`
   (int ≥ 0, 0 = bỏ qua); `balance_controller.allocate` lọc `Employee` theo các ô đó TRƯỚC `apply_scope` (chỉ thu hẹp). Không
   đổi luật «chỉ tạo dòng thiếu».

## Tệp
Tạo: `leave/holiday_work_report_controller.py` · `leave/holiday_work_report_service.py` ·
`leave/holiday_work_report_data.py` · `leave/balance_matrix_controller.py` · `leave/balance_matrix_service.py` ·
`test/backend/test_bao_cao_lam_ngay_le_cr717.py` · `test/backend/test_nghi_phep_quy_tong_hop_cr717.py`.
Sửa: `core/report_keys.py` · `core/report_cache.py` · `assistant/tools/report_summary_tool.py` · `main.py` ·
`leave/balance_report_spec.py` · `leave/balance_controller.py` (chỉ `allocate`) · `leave/schema.py` (chỉ
`LeaveBalanceAllocate`) · `test/backend/test_migration_bo_ke_hoach_nhan_su_cr692.py` (dòng 46: `len == 29`, `max == 30`) ·
`test/backend/test_phan_quyen_bao_cao_gac_duong.py` (3 đường mới → khóa 30).
KHÔNG đụng: tệp phase 01 (`policy_*`), `balance_service.py`, FE.

## Bài kiểm
- Báo cáo ngày lễ: phiếu đã duyệt ngày 02/09 (lễ) → `day_kind=1` + tên lễ; chủ nhật nghỉ theo lịch → `2`; phiếu chờ duyệt
  chỉ có khi `include_pending`; nháp / từ chối / hủy / xóa không bao giờ; ngày lễ riêng pháp nhân khác không áp; người
  phòng khác (phạm vi `dept`) không thấy; chưa gán khóa 30 → 403; xuất Excel có đủ cột; `/rows` lọc theo nhóm đúng;
  kỳ > 366 ngày → 422; **đếm truy vấn**: 1 phiếu vs 25 phiếu / 3 pháp nhân cùng số câu.
- Ma trận: cột theo loại có dữ liệu; ô = `available_days` (loại cộng dần giữ lại phần chưa tới tháng); phạm vi `own` chỉ 1
  dòng; đếm truy vấn cố định; `/api/leave-balances/matrix` không bị `/{bid}` nuốt.
- Quỹ phép năm: chỉ số `comp` = tổng `comp_days`; số truy vấn không đổi (bài kiểm CR-715 sẵn có).
- Cấp quỹ có lọc: `department_id` chỉ cấp người phòng đó; lọc không mở rộng ra ngoài phạm vi.
- Hồi quy: `-k "bao_cao or report_access or phan_quyen_bao_cao"` (chia nhóm), `test_assistant_report_summary_cr208.py`.

## Xong khi
Bài kiểm trên xanh; `curl` local `/api/holiday-work-report/summary?preset=this_year` trả đúng khung `build_report`; admin
tự có khóa 30 sau restart (`ensure_report_access_defaults`).

## Rủi ro
| Rủi ro | K×T | Giảm |
|---|---|---|
| Số 30 bị CR khác cấp song song | TB × Cao | `dieu-phoi` giữ số trước; test «khóa liên tục» bắt trùng |
| Ngày lễ bị xóa/sửa sau → phân loại đổi | Thấp × Thấp | ghi trong `notes`; phiếu vẫn hiện (loại 2) |
| Ma trận nhiều loại × nhiều người nặng | Thấp × TB | phân trang người, 1 câu quỹ cho trang |
| Quên thêm vào `REPORTS` trợ lý → test CR-208 đỏ | TB × Thấp | đã liệt kê ở mục Tệp |

## Bảo mật
Gác kép (khóa vai trò + khóa báo cáo); dữ liệu chỉ mã/tên/phòng/ngày — không trường nhạy cảm, nên vào bộ đệm Redis được.
