# Phase 03 — BE quá trình công tác, đổi pháp nhân, nhập Excel / hoàn tác

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 12/11/2026 | backend | Đã làm (12/11/2026) | duoc-CR-755 (nền duoc-CR-342, bao-CR-709, duoc-CR-585, duoc-CR-628) |

## Context links
- [plan.md](plan.md) Q4; [phase-01](phase-01-be-du-lieu-migration-api.md) (`concurrent_service`, L2 cặp).
- `employee/work_history_apply_service.py:80-115` (`_apply_concurrent`, `_other_concurrent_still_in_effect`),
  `employee/service.py:280-305` (`_sync_primary_department`), `:452-466` (đổi pháp nhân), `employee/schema.py:292`
  (`keep_old_department`), `department_service.py:40-60, 130-189, 286-324`, `import_tool/employee_import.py:179-183, 260-270`,
  `import_tool/employee_import_revert.py:60-80, 140-205`, `core/hr_work_history_codes.py:30, 66`.
- Luật: `.claude/rules/hr-employee-profile.md` mục QTCT (bẫy 1, 5, 6) và Nhập Excel (luật 8, 12).

## Overview
P1. Các đường ghi phụ đang đẩy phòng vào `tab_employee_department` chuyển sang bảng mới: nút **Áp** của QTCT loại Kiêm nhiệm,
**giữ phòng cũ làm kiêm nhiệm** (bao-CR-709), **đổi pháp nhân chính**, nhập Excel và hoàn tác. Dọn hẳn đường ghi phòng phụ cũ.

## Key insights
- Sau phase 01 bảng cũ chỉ còn dòng chính → `set_departments` thu về `set_primary_department` (một dòng + cột
  `Employee.department_id` + xóa cache). `set_extra_departments`, `extra_departments_of`, `detach_other_company_departments`
  hết lý do tồn tại: dòng kiêm nhiệm mang công ty riêng nên L3 cũ (*Phòng ban thuộc pháp nhân khác*) không còn vướng.
- Áp QTCT theo khóa `work_history_id` → chạy lại bao nhiêu lần cũng ra cùng một dòng (idempotent, như A5).
- Kết thúc dòng = đặt `to_date`, không xóa → giữ lịch sử, tệp QĐ, hoàn tác được.

## Requirements
1. **Áp QTCT loại 4** (`_apply_concurrent`): có dòng `work_history_id = row.id` → cập nhật công ty (`row.company_id` hoặc công
   ty chính nếu 0), phòng, chức vụ + nhãn chụp, từ/đến ngày, số/ngày QĐ, ghi chú; chưa có → tạo (`counts_scope` = bật). Không
   đổi `counts_scope` khi cập nhật. Liên kết tệp QĐ của dòng QTCT sang dòng kiêm nhiệm (thêm `FileLink` trỏ cùng `file_id`,
   bỏ qua tệp đã gắn). Qua L1 + L3 + L2 cặp. Dòng QTCT có `to_date` < hôm nay → chỉ cập nhật `to_date` (dòng tự thành Đã hết),
   không gỡ. Trùng phòng chính + công ty chính → bỏ qua (như cũ). Chiều ngược (sửa dòng kiêm nhiệm không sửa QTCT): một chiều,
   ghi rõ.
2. **Đổi phòng chính, giữ phòng cũ** (`keep_old_department = true`): tạo dòng kiêm nhiệm (phòng cũ, công ty TRƯỚC lần lưu, từ
   ngày = hôm nay, ghi chú *Giữ phòng cũ khi đổi phòng chính*). Không giữ: không làm gì thêm (phòng cũ vốn không còn là phòng
   phụ).
3. **Đổi pháp nhân chính A → B**: tham số mới `end_old_company_concurrent: bool | None` ở `EmployeeUpdate` (`None` = bật).
   Bật: dòng ở công ty A còn hiệu lực → `to_date = hôm qua`; dòng A **chưa bắt đầu** (`from_date >= hôm nay`) → xóa (kèm liên
   kết tệp, theo cùng chốt nhạy cảm của DELETE phase 01). Tắt: giữ nguyên. Dòng ở công ty khác A **không bao giờ** bị đụng.
   Trả câu cho nhật ký: *Đổi pháp nhân — kết thúc N dòng kiêm nhiệm ở công ty cũ: ...*.
4. **Nhập Excel**: snapshot `_depts` chỉ còn dòng chính; thêm `_concurrent_ended = [[id, to_date_cũ, to_date_mới], ...]` khi
   đổi pháp nhân kết thúc dòng. Dòng chưa bắt đầu ở công ty cũ → **lỗi dòng** *Còn kiêm nhiệm chưa bắt đầu ở công ty cũ — sửa
   ở tab Kiêm nhiệm trước* (không xóa được qua tệp vì không hoàn tác được).
5. **Hoàn tác**: khôi phục `to_date` cũ nếu giá trị hiện tại còn là `to_date` mới, lệch → từ chối cả lượt (luật 8); qua L1 + L2
   cặp. `_child_problem` đếm dòng `tab_employee_concurrent` thay cho phòng phụ cũ. Lô cũ (trước migration) có `_depts` chứa
   phòng phụ → so lệch → từ chối hồ sơ đó với câu rõ (an toàn, không khôi phục sai).

## Architecture
```
PATCH /employees/{id} ─ update_employee_core
   ├─ company đổi?  → concurrent_service.end_rows_at_company(emp, old_company, actor, mode)  (thay detach_*)
   └─ phòng đổi?    → _sync_primary_department → set_primary_department
                       └─ keep_old → concurrent_service.create_from_kept_department(...)
POST /work-history/{id}/apply (loại 4) → concurrent_service.upsert_from_work_history(row, actor, profile)
import_tool ─ update_employee_core(..., end_old_company_concurrent=True, import_mode=True) → snapshot _concurrent_ended
revert      ─ concurrent_service.restore_ended(snapshot) sau update_employee_core
```

## Related code files
Sửa (phase sở hữu): `backend/app/modules/employee/department_service.py` (thu gọn), `employee/concurrent_service.py` (thêm
ba hàm ở trên — phase 01 đã tạo tệp, phase này nối thêm cuối tệp), `employee/service.py` (`_sync_primary_department`,
khối đổi pháp nhân), `employee/schema.py` (`end_old_company_concurrent`), `employee/work_history_apply_service.py`,
`employee/work_history_service.py` (chú thích dòng 8), `core/hr_work_history_codes.py` (chú thích 66),
`import_tool/employee_import.py`, `import_tool/employee_import_revert.py`.
Bài kiểm sửa: `test_doi_phap_nhan_nhan_su.py`, `test_qua_trinh_cong_tac_ap_ho_so.py`, `test_qua_trinh_cong_tac_gio_vn.py`,
`test_qua_trinh_cong_tac_sua_loi_review_low.py`, `test_nhap_excel_nhan_su_cr628.py`, `test_nhap_excel_nhan_su_review_cr628.py`
(+ các `test_qua_trinh_cong_tac_*` khác nếu đỏ).
Tạo: `test/backend/test_kiem_nhiem_khac_cong_ty_qua_trinh_doi_phap_nhan_cr755.py`.

## Implementation steps
1. `department_service`: `set_departments` → `set_primary_department(db, emp, dept_id, actor)`; xóa `set_extra_departments`,
   `extra_departments_of`, `detach_other_company_departments`; `departments_of` giữ (trả dòng chính) hoặc xóa nếu không còn
   ai gọi (grep cả `test/backend`). Giữ L1, L2 cũ (phòng chính).
2. `concurrent_service`: `end_rows_at_company`, `create_from_kept_department`, `upsert_from_work_history`, `restore_ended`.
3. `service.update_employee_core`: thay lời gọi `detach_*`; truyền `keep_old` + công ty cũ cho `_sync_primary_department`.
4. `work_history_apply_service._apply_concurrent` → `upsert_from_work_history`; xóa `_other_concurrent_still_in_effect`.
   `compute_can_apply` (nếu có nhánh loại 4) xét theo dòng kiêm nhiệm thay vì danh sách phòng.
5. Nhập Excel + hoàn tác theo Requirements 4–5.
6. Bài kiểm; chạy đúng tệp.

## Todo
- [x] Thu gọn `department_service` (còn `set_primary_department`, `check_primary_belongs`)
- [x] Bốn hàm kiêm nhiệm (nằm ở `concurrent_transition_service.py` mới, vì `concurrent_service.py` đã ~200 dòng)
- [x] Đổi pháp nhân + tham số `end_old_company_concurrent` + `keep_concurrent_ids`
- [x] Giữ phòng cũ → dòng kiêm nhiệm
- [x] Áp QTCT idempotent + liên kết tệp
- [x] Nhập Excel snapshot + lỗi dòng; hoàn tác
- [x] Sửa bài kiểm cũ + bài mới (`test_kiem_nhiem_luong_ghi_cr755.py`, thay tên so với kế hoạch)

## Success criteria
`docker compose exec -T api python -m pytest test/backend/test_kiem_nhiem_khac_cong_ty_qua_trinh_doi_phap_nhan_cr755.py
test/backend/test_doi_phap_nhan_nhan_su.py test/backend/test_nhap_excel_nhan_su_cr628.py
test/backend/test_nhap_excel_nhan_su_review_cr628.py -q --timeout=120` và `-k "qua_trinh_cong_tac"` trên thư mục bài kiểm xanh.
Phủ: đổi A → B kết thúc dòng A, KHÔNG đụng dòng C; tắt cờ thì giữ; dòng A chưa bắt đầu bị xóa (màn) / lỗi dòng (Excel);
giữ phòng cũ tạo đúng một dòng; Áp QTCT hai lần → một dòng, sửa ngày ở QTCT rồi Áp lại → dòng cập nhật; Áp dòng đã kết thúc
→ dòng thành Đã hết, không xóa; hoàn tác lô đổi pháp nhân trả lại `to_date`; lô cũ có phòng phụ → từ chối có câu rõ.

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Gỡ nhầm dòng ở công ty khác khi đổi pháp nhân | Thấp × Cao | Lọc cứng `company_id == công ty cũ`; bài kiểm có dòng công ty C |
| Đổi pháp nhân mà quên kết thúc → còn thấy dữ liệu A | Trung × Trung | Mặc định bật; giao diện hỏi (phase 04); nhật ký liệt kê |
| Hoàn tác lô cũ bị chặn hàng loạt | Thấp × Thấp | Chỉ lô có phòng phụ; câu lỗi chỉ cách sửa tay |
| Liên kết tệp QTCT sang dòng kiêm nhiệm làm tệp không bao giờ mồ côi | Thấp × Thấp | `_delete_file_if_orphan` đã đếm theo liên kết; xóa dòng là gỡ liên kết |

## Security
- Mọi đường mới vẫn qua L1 + L2 cặp; kết thúc / xóa dòng là thu hẹp nhưng vẫn kiểm `employee.write` hồ sơ.
- Không ghi giá trị nhạy cảm vào nhật ký nhập.

## Next steps
Phase 04 thêm hộp hỏi kết thúc khi đổi pháp nhân + thay câu xác nhận Áp QTCT.
