# Phase 01 BE — Chính sách nghỉ phép + Phân bổ chính sách (duoc-CR-717)

Status: DONE. Không commit/push. Migration `lvpol717` đã áp local (lên/xuống/lên sạch, head = `lvpol717`).

## Tệp
Tạo (backend/app/modules/leave/): `policy_model.py` · `policy_schema.py` · `policy_allocation_math.py` (thuần) ·
`policy_allocation.py` (nạp DB, `allocated_days`) · `policy_assignment_plan.py` (`plan_change` dùng chung preview + ghi — tách khỏi
service để <200 dòng) · `policy_assignment_service.py` (tạo/sửa/xóa/bulk + `reconcile_balances`) · `policy_controller.py` ·
`policy_assignment_controller.py`. `backend/migrations/versions/lvpol717_chinh_sach_nghi_phep.py` (viết tay, idempotent).
Sửa: `balance_service.py` (import + `ensure_balance` gọi `policy_allocation.allocated_days`), `accrual_service.py` (tách
`pick_quota(rules, type, emp)` thuần, `resolve_quota` giữ chữ ký), `constants.py` (`LeavePolicyAssignmentState` 1 sắp tới · 2 hiệu
lực · 3 đã kết thúc + nhãn), `core/all_models.py`, `main.py` (3 dòng import + 3 include, đọc lại file trước khi sửa).
Test: `test_nghi_phep_chinh_sach_cr717.py` (109) · `test_nghi_phep_phan_bo_hang_loat_cr717.py` (13).
Ngoài danh sách nhưng đúng chỉ dẫn lead: `test_canh_do_dai_o_chu_cr538.py` (khai 9 schema mới ở TARGETS/NO_TARGET),
`test_pham_vi_luat_bat_bien.py` (BB4: `leave/policy_controller.py` vào danh sách miễn trừ kèm lý do — dùng make_crud_router, entity
PUBLIC).

## Luật đã xây (bám phase file)
- Hạn mức theo tháng: tháng m thuộc phân bổ ⇔ from ≤ ngày 15 tháng m ≤ to. Mọi q(m) bằng nhau / không tháng nào khớp → đúng
  `prorate_allocation` cũ (pin test 3 mode × 5 ngày vào làm × 4 hạn mức gồm 12.25). Ví dụ chốt: 12→15 từ 01/07 = 13.5; từ 16/07 = 13.5
  (13.25 làm tròn); PRORATA vào làm 10/03 gói 15 = 12.5; FULL_YEAR giữa năm = 15; kết thúc 14/09 → tháng 9 về luật loại (= 14.0).
- Không có phân bổ → `allocated_days` 1 truy vấn thêm (nạp phân bổ), không truy vấn dòng gói; kết quả y hệt cũ.
- Chốt tạo: nhân sự trong `apply_scope(Employee,"employee",…,"write")` (ngoài → 404) → gói tồn tại (404) → tự phân bổ 403 (trừ
  `is_system_admin`) → gói ngừng 422 → chồng ngày 409 (có tên gói + khoảng ngày) hoặc `close_previous` (chỉ khi đúng 1 lượt chồng
  bắt đầu TRƯỚC `from`; đặt `to = from − 1`). UNIQUE(employee, from) vỡ → 409. Khóa `tab_employee` FOR UPDATE (MySQL).
- Quỹ năm nay (`vn_today().year`): chỉ khi phân bổ (mới / cũ bị đóng) chạm năm; loại = hợp loại gói mới ∪ gói bị đóng, chỉ loại đang
  dùng + trừ quỹ. Thiếu dòng → `ensure_balance` (created); có dòng + recalc → chỉ `allocated_days`, audit `leave_balance`
  **… hạn mức X năm Y a → b ngày** (commit=False); không recalc / bằng nhau → kept. `negative_after` khi available < −max_negative.
- Năm đã qua / năm sau: không bao giờ đụng dòng quỹ (test). Dòng gói: loại phải `counts_balance`, không `is_compensatory`, 0–366 bước 0.5,
  ≤ 50 dòng, không trùng loại (422).
- Xóa gói còn phân bổ → 409 **Chính sách đang được phân bổ cho N nhân sự — …**. Xóa gói sạch luôn dòng. `code` không đổi (Update không có code).
- Bulk: ≤500 (422), dedupe id, mỗi người một savepoint, vướng chốt → `skipped`, lỗi CSDL → rollback cả lô + 500 chỉ nêu tên lớp lỗi.
- Preview và ghi dùng chung `plan_change`; số truy vấn cố định (test 1 / 7 / 30 người cùng số câu, và list 1 vs 30 dòng).
- Không thêm khóa quyền, không đụng SCOPE_FIELDS/seed/permissions.

## API as built (phong bì `{success, message, data}`; lỗi `{success:false, error:{code,message}}`)
Chính sách — gác `leave_type` (read/create/write/delete), `make_crud_router`:
- `GET /api/leave-policies` (lọc `code,name,is_active`, phân trang chuẩn) · `POST` (201) `{code≤30,name≤150,note≤500,is_active}` ·
  `GET/PATCH/DELETE /api/leave-policies/{id}` (PATCH `{name?,note?,is_active?}`) → item `{id,code,name,note,is_active,updated_at}`.
  (Không có `line_count`/`assignment_count` trong list — FE lấy riêng nếu cần.)
- `GET /api/leave-policies/{id}/lines` → `{total, items:[{id,leave_type_id,annual_days}]}` · `PUT …/lines` body
  `{items:[{leave_type_id, annual_days}]}` thay cả danh sách, trả cùng dạng GET.

Phân bổ — gác `leave_balance` (read xem; write tạo/sửa/xóa):
- `GET /api/leave-policy-assignments?page&page_size&employee_id&policy_id&company_id&active_on=YYYY-MM-DD&search=` →
  `{total, items:[{id,employee_id,company_id,policy_id,effective_from,effective_to|null,note,employee_name,employee_code,policy_name,
  state(1|2|3),updated_at}]}`; sắp xếp from giảm dần; lọc phạm vi `leave_balance`.
- `GET /{id}` → cùng item (get_scoped, ngoài phạm vi 404).
- `POST` `{employee_id, policy_id, effective_from, effective_to?, note?≤500, recalc_current_year=true, close_previous=false}` →
  `{assignment:<item>, balances:{created:int, recalculated:[{leave_type_id,before,after}], kept:int, negative_after:[{leave_type_id,available_days}]}}`.
  Lỗi: 403 tự phân bổ · 404 ngoài phạm vi/không có · 409 chồng ngày (message dựng sẵn để hiện) · 422 gói ngừng / ngày sai.
- `POST /preview` `{policy_id, effective_from, effective_to?, close_previous=false, employee_ids? (≤500) | company_id?,department_id?,
  employment_type?,job_level?, only_without_active=true}` → `{items:[{employee_id,code,name,department_name,hire_date,
  current:{policy_name,from,to}|null, conflict:null|'overlap'|'self'|'inactive', conflict_message, changes:[{leave_type_id,before,after}]}],
  total, truncated}` (trần 500; chỉ nhân sự đang làm trong phạm vi ghi; `only_without_active` chỉ áp khi KHÔNG truyền `employee_ids`
  — bỏ người có phân bổ hiệu lực hôm nay). `changes.before` = `allocated_days` hiện có (hoặc số sẽ được cấp nếu chưa có dòng).
- `POST /bulk` `{policy_id, effective_from, effective_to?, employee_ids (1..500), recalc_current_year=true, close_previous=false}` →
  `{created, skipped:[{employee_id,name,reason}], balances:{created,recalculated:[{leave_type_id,before,after,employee_id}],kept,negative_after:[…,employee_id]}}`.
  Nhân sự ngoài phạm vi / không tồn tại vào `skipped` (name rỗng).
- `PATCH /{id}` `{effective_to? (null = không thời hạn), note?, recalc_current_year=true}` → `{assignment, balances}`; 409 nếu kéo dài
  chồng, 422 nếu `to < from`. Chỉ đổi `effective_to` mới tính lại quỹ.
- `DELETE /{id}?recalc_current_year=false` → `{balances}` (recalc=true → các loại của gói về luật loại).
Trạng thái `state` dẫn xuất theo `vn_today()`; nhãn: 1 **Sắp tới**, 2 **Đang hiệu lực**, 3 **Đã kết thúc** (`LEAVE_POLICY_ASSIGNMENT_STATE_LABELS`).

## Kiểm
- Mới: 122 xanh. Hồi quy `-k "nghi_phep or cr715 or cr713 or quy_phep"` = 729 xanh. `test_pham_vi_khai_du_b07`, `test_pham_vi_duong_vong`
  xanh (controller mới dùng `db.query`, không `db.get`). `test_canh_do_dai_o_chu_cr538`: chỉ còn 3 lỗi sẵn có customs/forum.
  Quét `-k "pham_vi or route or migration or status_catalog…"`: 1436 xanh, 1 đỏ BB4 do tôi gây → đã khai, nay xanh.
- Migration trên MySQL local: upgrade/downgrade/upgrade sạch, cột khớp model.
- API thật trên MySQL local (TestClient trên app thật, chỉ override auth, rồi dọn sạch dữ liệu thử): loại quota 12, cấp quỹ 12, phân bổ
  gói 15 từ 01/07 tính lại → `recalculated [{before:12.0, after:13.5}]` (đúng tiêu chí **xong khi**).

## Lưu ý cho FE / người sau
- **Kết thúc chính sách cũ** cắt đuôi: nếu lượt cũ kéo dài quá `effective_to` của lượt mới thì phần đuôi mất (đúng spec D6). 
- Quyền ghi phân bổ cần CẢ `leave_balance.write` lẫn `employee.write` (scope ghi nhân sự) theo spec — vai trò HR chỉ có `employee.read`
  sẽ thấy mọi nhân sự là 404. Nếu thực tế HR không có `employee.write`, đổi `_employee_query` sang action `read` (1 chỗ).
- SQLite (test) + savepoint: pysqlite COMMIT khi nhả savepoint ngoài cùng nếu chưa BEGIN — chỉ test; đã ghi chú trong bài kiểm rollback.
- Docs/HDSD/change-log/nhật ký chưa động (ngoài quyền sở hữu phase này).

Unresolved: không.

**Status:** DONE


## Sửa sau bàn giao (lead, 03/11/2026)
- Phạm vi nhân sự của phân bổ (đơn lẻ, xem trước, hàng loạt) đổi từ `employee.write` sang phạm vi XEM `employee` — cùng luật **Cấp quỹ**; quyền ghi chỉ còn `leave_balance.write`. 122 bài CR-717 vẫn xanh.
