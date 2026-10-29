# Phase 17 — Bảng kế hoạch nhân sự + A4 + cột kế hoạch của A5

**Chủ:** BE-7 · **Khóa báo cáo:** 25 `HEADCOUNT_PLAN` (router khung `employee/headcount_plan_report_controller.py`, `/api/headcount-plan-report`) · **Có migration.**

## Bảng kế hoạch `tab_headcount_plan`
- Cột: `id`, `year` (SMALLINT), `company_id`, `department_id` (0 = toàn pháp nhân), `planned_headcount` (int ≥ 0), `planned_payroll_monthly` (BIGINT ≥ 0, VND, lương + phụ cấp / tháng), `note` (String 500) + AuditMixin. UNIQUE (`year`, `company_id`, `department_id`).
- Khóa quyền MỚI `headcount_plan` (read · create · write · delete · export) — theo skill `them-entity-moi` (bảy sổ đăng ký: ENTITIES, SCOPE_FIELDS (company_id / department_id), seed `_SYS_ENTITIES` hay không — KHÔNG cho Quản lý thu mua tự có; vai trò `hr_profile` / admin có đủ), test canh 7 sổ phải xanh.
- API: `make_crud_router` (`core/crud.py`) ở `/api/headcount-plans` có lọc `year`, `company_id`, `department_id`, nhập / xuất CSV theo khuôn sẵn có (cột `year, company_code, department_code, planned_headcount, planned_payroll_monthly, note`). `max_length` cho chuỗi; số âm / năm ngoài 2000–2100 → 422 (luật `backend-input-limits.md`). Ghi nhật ký `audit.record`.
- `planned_payroll_monthly` là số lương → chỉ trả ra cho người có `labor_contract.read` (che ở serializer, giống `employee_sensitive`); người chỉ có `headcount_plan` thấy định biên, không thấy tiền.
- Migration autogenerate PHẢI gọt về đúng bảng mới (repo quét ra ~650 dòng trôi dạt).

## A4 — `/api/headcount-plan-report/summary` (+ export, rows) · `require('headcount_plan', read|export)` + `require_report(25)` + `apply_scope`
- Năm = năm của cuối kỳ; thực tế = định biên cuối kỳ (dùng lại `employees_as_of` / luật A1).
- Chỉ số: `planned` «Định biên kế hoạch» · `actual` «Đang có» · `gap` «Chênh (thực tế − kế hoạch)» · `vacancies` «Còn thiếu» (Σ max(0, kế hoạch − thực tế) theo dòng kế hoạch) · `over` «Vượt» · dẫn xuất `fill_rate` «Tỷ lệ lấp đầy».
- Dòng kế hoạch `department_id = 0` = cả pháp nhân (so với tổng pháp nhân, không cộng dồn với các dòng phòng). Phòng có người mà không có kế hoạch → hiện «chưa có kế hoạch».
- Xem theo `company` · `department`. `/rows`: người đang làm của nhóm (Mã, Họ tên, Phòng, Chức vụ, Ngày vào làm).
## A5 — thêm cột kế hoạch
- Chỉ số mới ở `/api/payroll-fund/summary`: `planned_payroll` «Quỹ lương kế hoạch / tháng» · `payroll_remaining` «Còn dư so với kế hoạch» · dẫn xuất `payroll_use_rate` «% dùng». Theo pháp nhân / phòng như dòng kế hoạch. Giữ luật che nhóm nhỏ.
- Test: CRUD + quyền (không lộ tiền khi thiếu `labor_contract.read`), CSV nhập / xuất, A4 định nghĩa chỉ số, A5 cột mới, số truy vấn cố định.
