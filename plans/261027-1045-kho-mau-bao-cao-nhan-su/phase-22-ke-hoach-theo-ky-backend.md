# Phase 22 — Kế hoạch nhân sự theo kỳ: backend (duoc-CR-690)

Thiết kế nghiệp vụ (NGUỒN CHÍNH, đọc trước): `doc/erp/hrm/06-ke-hoach-nhan-su.md`.
Ưu tiên P1 · Chủ: BE-10 · Trạng thái: pending

## Phạm vi
Thay bảng một-dòng của đợt 4 bằng: nhóm chi phí + mẫu khoản chi phí (người dùng tự định nghĩa) + kế hoạch theo kỳ
(header + khoản đã chép + dòng vị trí + văn bản liên kết + tệp) + bộ tính theo tháng + API. KHÔNG sửa A4/A5 (phase 24).

## Mã số (SMALLINT + IntEnum, luật R2) — `modules/headcount_plan/constants.py`, đăng ký `core/code_sets.py` để `gen_status_ts.py` sinh TS
- `PlanPeriodType`: YEAR=1, HALF=2, QUARTER=3, MONTH=4. `period_no`: YEAR→1; HALF 1–2; QUARTER 1–4; MONTH 1–12.
- `CostCalcMethod`: PER_HEAD_MONTH=1 (nhập theo vị trí), PERCENT_OF=2, MONTHS_OF=3, PER_HEAD_ONCE=4, LUMP_SUM=5.
- `CostAppliesTo`: ALL_POSITIONS=1, SELECTED_POSITIONS=2, WHOLE_DEPARTMENT=3 (chỉ hợp lệ với LUMP_SUM).
- `ActualSource`: NONE=0, BASE_SALARY=1, ALLOWANCE=2, PERCENT_OF_INSURANCE_SALARY=3.

## Bảng (FK mềm như module hiện tại; mọi `String(n)` có `max_length` ở schema — `.claude/rules/backend-input-limits.md`)
- `tab_hr_cost_group`: name String(100) unique, sort_order, is_active.
- `tab_hr_cost_template`: name String(150) unique, note String(500), is_active.
- `tab_hr_cost_template_item` và `tab_headcount_plan_cost_item` (cùng cột; bản plan có `plan_id`, bản mẫu có `template_id`):
  `code` String(30) (duy nhất trong mẫu / trong kế hoạch, khóa tham chiếu giữa các khoản và cột số tiền của dòng), `name` String(150),
  `group_id`, `calc_method`, `rate` Numeric(7,4) (% cho PERCENT_OF), `factor` Numeric(6,2) (cho MONTHS_OF), `cap_amount` BigInt (0 = không trần),
  `amount` BigInt (cho PER_HEAD_ONCE / LUMP_SUM), `base_codes` JSON list[str] (PERCENT_OF: các khoản gốc; MONTHS_OF: đúng 1 khoản),
  `applies_to`, `position_ids` JSON list[int], `months` JSON list[int 1..12] (rỗng = mỗi tháng), `actual_source`, `sort_order`.
- `tab_headcount_plan` (mở rộng bảng cũ): + `period_type`, `period_no`, `basis_no` String(100), `basis_date` Date null, `approver_employee_id`,
  `template_id` (chỉ ghi nguồn chép). Unique mới: (year, period_type, period_no, company_id, department_id). BỎ `planned_headcount`,
  `planned_payroll_monthly` SAU khi dời dữ liệu (downgrade dựng lại).
- `tab_headcount_plan_line`: plan_id, position_id (0 = «Không theo vị trí»), `headcounts` JSON list[int] (độ dài = số kỳ con), `amounts` JSON
  {code: int} cho khoản PER_HEAD_MONTH, note String(500). Unique (plan_id, position_id).
- `tab_headcount_plan_document`: plan_id, document_id; unique cặp.
- Tệp đính kèm: dùng `modules/attachment` (`FileLink`) như các module khác, entity = `headcount_plan`.

Migration MỘT tệp (`hcplan02_...`), cắt tay phần autogenerate trôi dạt. Dời dữ liệu cũ: mỗi dòng → YEAR, 1 dòng position 0 có headcounts
[n,n,n,n], 1 khoản «Quỹ lương (nhập tổng)» LUMP_SUM amount = 12 × số cũ, months rỗng (chia đều 12). Gieo bằng migration (Alembic, KHÔNG `mysql -e`)
nhóm gợi ý «Quỹ lương · Bắt buộc theo luật · Phúc lợi · Khác» + mẫu «Mẫu gợi ý» (LUONG, PC_BH, PC_KHONG_BH [PER_HEAD_MONTH, actual BASE/ALLOWANCE/NONE],
BHXH 17.5 / BHYT 3 / BHTN 1 / KPCD 2 [PERCENT_OF base LUONG+PC_BH, cap 46.800.000, actual PERCENT_OF_INSURANCE_SALARY], THUONG_13 [MONTHS_OF LUONG ×1, T12]).
Chỉ gieo khi bảng còn rỗng. Thêm model vào `core/all_models.py`.

## Bộ tính — `modules/headcount_plan/costing.py` (hàm thuần, không DB, bài kiểm đơn vị đầy đủ)
`compute_plan(period_type, period_no, year, items, lines) -> dict`
- Kỳ con: YEAR→Q1..Q4; HALF→2 quý; QUARTER→3 tháng; MONTH→1 cột. Tháng của kỳ suy từ loại kỳ.
- Người của vị trí ở tháng m = headcounts[chỉ số kỳ con chứa m].
- PER_HEAD_MONTH: người × amount[code] mỗi tháng (lọc theo applies_to/position_ids, months).
- PERCENT_OF: Σ vị trí: người × min(Σ khoản gốc / người, cap or ∞) × rate/100.
- MONTHS_OF: người × factor × (khoản gốc / người) ở các tháng `months` (bắt buộc ≥1 tháng).
- PER_HEAD_ONCE: người × amount ở tháng `months`. LUMP_SUM: amount chia đều cho `months` (rỗng = mọi tháng của kỳ).
- Kiểm hợp lệ (422 tiếng Việt): code trùng, base_codes trỏ khoản không tồn tại / trỏ PERCENT_OF / tự trỏ, months ngoài kỳ, WHOLE_DEPARTMENT
  với method khác 5, số âm, độ dài headcounts sai.
- Trả: `periods` [{key, label, months}], `headcount` [cuối mỗi kỳ con], `items` [{code, name, group_id, values[], total}],
  `groups` [{group_id, name, values[], total}], `total` {values[], total}, `avg_per_head` (total / người bình quân, None nếu 0), `monthly`
  {m: {"headcount": n, "items": {code: amount}}} (để phase 24 dùng).

## API (giữ tiền tố, envelope `success()`, gác `require("headcount_plan", ...)` + `apply_scope`/`get_scoped`)
- `/api/hr-cost-groups` — `make_crud_router` (read theo `headcount_plan.read`, ghi theo `headcount_plan.write`). Xóa nhóm đang dùng → 400.
- `/api/hr-cost-templates` — list/get/create/patch/delete; body có `items` (thay nguyên danh sách). Sao chép mẫu: `POST /{id}/duplicate`.
- `/api/headcount-plans`:
  - `GET` list (lọc year, period_type, company_id, department_id): header + `headcount_end`, `total_cost` (None nếu không xem được tiền), tên.
  - `GET /{id}`: header + `cost_items` + `lines` (kèm position_name) + `documents` [{document_id, code, title, status, can_read}] + `files` + `computed`.
  - `POST` {header…, template_id}: chép khoản từ mẫu, `lines` rỗng (hoặc lấy kèm `lines` nếu gửi). `PUT /{id}`: thay header + cost_items + lines + document_ids.
  - `POST /compute` (body = bản nháp đầy đủ, không lưu) → `computed` — giao diện gọi để xem trước khi đang nhập. Gác `headcount_plan.read`.
  - `GET /position-stats?company_id&department_id[&as_of]` → [{position_id, position_name, current_count, avg_base_salary, avg_allowance}];
    hai cột tiền None nếu không `can_see_payroll`. Đếm người đang làm đúng pháp nhân × phòng × `position_id`.
  - `DELETE /{id}`. Xuất: `GET /{id}/export` (xlsx: dòng vị trí + bảng tính) và `GET /export/csv` (danh sách header). Nhập CSV dòng vị trí vào
    MỘT kế hoạch: `POST /{id}/import/csv` cột `position_code, hc_1..hc_n, <code khoản PER_HEAD_MONTH>...`; lỗi tiếng Việt theo dòng
    (`describe_validation_errors`), mã chức vụ lạ = lỗi dòng.
- Văn bản liên kết: chỉ gắn được văn bản người lưu đọc được (`document.access_service.can(...,"read")`) → khác thì 403; khi trả về,
  văn bản người xem không đọc được chỉ có `{document_id, can_read:false}` (KHÔNG code/title); văn bản đã xóa `{deleted:true}`.
- Tiền: mọi `amount`, `cap_amount`, `amounts`, `computed` tiền, `avg_*` chỉ trả khi `can_see_payroll(profile, company_id)`; ngược lại None
  (định biên vẫn trả). Ghi số tiền khác 0/None khi không xem được → 403; số 0/None từ người không xem được = giữ nguyên (đúng luật CR-689).
- Giữ luật cũ: `check_refs` (pháp nhân phải có, phòng có thật), phạm vi ghi qua `get_scoped(..., "write")`, `commit_or_conflict`, audit `record`.

## Bài kiểm (`test/backend/test_ke_hoach_nhan_su_theo_ky_cr690.py` + `test_bo_tinh_ke_hoach_cr690.py`)
Bộ tính: từng cách tính, trần, tháng rơi, kỳ con của 4 loại kỳ, kiểm hợp lệ. API: tạo từ mẫu (chép, sửa mẫu không đổi kế hoạch), PUT, compute,
che tiền theo pháp nhân, văn bản không đọc được, CSV, dời dữ liệu cũ (gọi hàm dời trên SQLite). Sửa/xóa các bài `test_ke_hoach_nhan_su_cr689.py`
phụ thuộc cột bỏ đi cho khớp khuôn mới. `test_pham_vi_khai_du_b07.py`, `test_canh_do_dai_o_chu_cr538.py` phải xanh (khai entity/schema mới nếu thêm).

## Rủi ro
- A4/A5 đang đọc `planned_headcount` / `planned_payroll_monthly`: phase 24 sửa; phase 22 KHÔNG xóa cột trước khi phase 24 xong → làm migration
  dời dữ liệu ở 22 nhưng bước DROP cột để ở migration riêng của phase 24.
