# Review fixes BE — duoc-CR-717 (03/11/2026)

Tests: `test_nghi_phep_review_cr717.py` (mới, 35) + 2 tệp CR-717 cũ = 157 xanh. Hồi quy `-k "nghi_phep or cr715 or cr713 or cr717 or quy_phep"` = 777 xanh.
B07 / duong_vong / luat_bat_bien xanh; `test_canh_do_dai_o_chu_cr538` chỉ đỏ 3 schema customs/forum có sẵn. Không đụng `change_tracker`, frontend, doc.
Hình dạng phản hồi API không đổi, ngoại lệ duy nhất: xem **Ghi chú cho FE** cuối.

## Từng điểm
- **H1** — `policy_allocation.with_row_lock(db, query, exclusive=False)` (`FOR SHARE` / `FOR UPDATE` + `populate_existing`, chỉ MySQL/PG). `load_assignments`, `load_lines`, `allocated_days`, `plan_change` có tham số `lock`; mọi đường ghi (create, bulk, update, delete, reconcile) truyền `lock=True` sau `lock_employees`. `update`/`delete` nạp lại phân bổ bằng `lock_assignment` (FOR UPDATE; mất rồi → 404). Dòng quỹ khóa bằng MỘT câu `IN (...) FOR UPDATE`. Test: `test_h1_*` (bật khóa ở SQLite + soi SQL biên dịch MySQL qua `do_orm_execute`: phân bổ, dòng gói, dòng quỹ đều có FOR SHARE/UPDATE trên 4 đường; `with_row_lock` fake-mysql).
- **H2** — `policy_assignment_scope.writable_employee_query`: phạm vi XEM `employee` VÀ `scope_condition("leave_balance", "write")` dựng trên **bảng giả** `(company_id=Employee.company_id, employee_id=Employee.id)` — không tạo dòng nào, đúng điều kiện `get_scoped(...,"write")` sẽ áp về sau. Preview / create / bulk cùng dùng. Ngoài phạm vi: create 404, bulk `skipped` (lý do), preview theo bộ lọc không liệt kê. Admin không đổi. Test: `test_h2_*` (404, skipped, preview, admin, và `test_h2_dieu_kien_khop_get_scoped` tham số hóa 5 kiểu grant đối chiếu `get_scoped`).
- **M1** — `_writable` (PATCH + DELETE): hồ sơ của chính người bấm → 403 `SELF_MESSAGE`, trừ admin; ngoài phạm vi vẫn 404 trước. Test `test_m1_*`.
- **M2** — `policy_allocation_math.extend_to_year_start`: phân bổ bắt đầu trong `(01/01, hết tháng vào làm]` kéo lùi về 01/01 (không lấn qua phân bổ khác đã kết thúc trước nó). FULL_YEAR loại 12, gói 15, vào làm + gán 01/10 → 15 (gói 0 → 0); PRORATA/MONTHLY = `prorate_allocation(15…)` như thường; gán sau tháng vào làm không kéo lùi. Test `test_m2_*` (4 ngày bắt đầu × full-year, prorata, monthly, không kéo lùi, không lấn, qua API).
- **M3** — bỏ savepoint cho bulk (đường ngắn nhất, không đụng core): cả lô trong một giao dịch, chốt nghiệp vụ đã lọc ở `plan_change`; UNIQUE vỡ (chỉ khi race) → 409 cả lô. Controller bắt `IntegrityError`→409 trước `SQLAlchemyError`→500. Test `test_m3_*`: ngữ cảnh request + `create_bulk` lỗi + rollback → `ctx.changes == []`, `begin_nested` không gọi; test cũ lỗi-CSDL-cuộn-cả-lô viết lại (patch `reconcile_plan`).
- **M4** — `PlanItem.new_values` (plan_change đã tính) → `policy_assignment_balances.reconcile_plan` dùng thẳng: 1 câu khóa dòng quỹ, dòng mới dựng trực tiếp (cùng cột `ensure_balance`, bậc thâm niên tra 1 lần/(loại, số năm)), một flush. Test `test_m4_*`: SELECT = 2 / 9 / 25 người bằng nhau. ⚠️ Câu GHI vẫn tuyến tính (INSERT lấy PK tự tăng + UPDATE có `updated_at` biểu thức SQL — ORM không gộp); test chặn trần ≤ 5n+10. Trước: ≈5 câu ĐỌC/người.
- **L1** — create/bulk lọc `is_active` (404 / `skipped`). `test_l1_*`.
- **L2** — PUT dòng: khóa FOR UPDATE dòng gói + dòng cũ; audit (cùng giao dịch) ghi **trước [loại: ngày] → sau […]**; `IntegrityError` → 409. Test `test_l2_*` (audit, commit giả vỡ UNIQUE → 409 và dữ liệu cũ còn).
- **L3** — `PolicyUpdate` (name/note/is_active) và `AssignmentUpdate` (note/recalc) cấm `null` (422); `effective_to=null` vẫn hợp lệ. Test `test_l3_*`.
- **L4** — tạo phân bổ: `lock_policy` FOR SHARE (gói đã xóa → 404); xóa gói: FOR UPDATE dòng gói + đọc phân bổ có khóa; PUT dòng: FOR UPDATE. Test `test_l4_*`.
- **L5** — `update_one`: hồ sơ mất → 404 (không để kéo dài chồng ngày). `delete_one` vẫn xóa được phân bổ mồ côi. Test `test_l5_*`.
- **L6** — `search` `max_length=100` (422); lọc bằng `ILIKE` ngay trong SQL (subquery), `% _ \` được escape. Test `test_l6_*`.

## Tệp
Sửa: `policy_allocation.py`, `policy_allocation_math.py`, `policy_assignment_plan.py`, `policy_assignment_service.py` (viết lại), `policy_assignment_controller.py`, `policy_controller.py`, `policy_schema.py`.
Mới: `policy_assignment_balances.py` (cấp/tính lại quỹ), `policy_assignment_scope.py` (H2/M1), `policy_assignment_view.py` (dump/tra tên/tìm kiếm, tách cho controller < 230 dòng).
Test: mới `test_nghi_phep_review_cr717.py`; sửa 2 bài trong `test_nghi_phep_phan_bo_hang_loat_cr717.py` (lỗi-CSDL-cuộn-cả-lô; từ khóa tìm kiếm viết **NHân sự B1**).

## Ghi chú cho FE (thay đổi hành vi, không đổi khóa JSON)
- `POST /preview` với `employee_ids`: id không nằm trong phạm vi ghi / đã nghỉ việc / không tồn tại nay hiện thêm một dòng `{employee_id, code:"", name:"", department_name:"", hire_date:null, current:null, conflict:"scope", conflict_message:<lý do>, changes:[]}`. Giá trị `conflict` MỚI `"scope"` — FE nên coi như các conflict khác (hiện `conflict_message`).
- `/bulk` `skipped[].reason` cho người ngoài phạm vi / nghỉ việc: **Không tìm thấy nhân sự (đã nghỉ việc, hoặc ngoài phạm vi của bạn).**
- PATCH/DELETE phân bổ của chính mình → 403 (trước: qua). PATCH `null` cho name/note/is_active → 422.
- `search` danh sách: theo collation `_ci` của MySQL (khớp không phân biệt hoa thường/dấu); SQLite test chỉ khớp ASCII không phân biệt hoa thường.

## Chưa giải quyết / lưu ý
- Probe MySQL hai luồng thật (kiểu CR-628) chưa chạy — chỉ chứng minh SQL biên dịch có khóa; nên chạy một lần trên MySQL local trước khi gộp.
- `adjust_balance` vẫn chưa có chốt tự sửa quỹ của mình (lỗ cũ, ngoài CR này — đã ghi ở review).
- `_new_balance` lặp phần dựng dòng của `ensure_balance` (cột + bậc thâm niên); đổi `ensure_balance` thì phải đổi theo.

**Status:** DONE_WITH_CONCERNS
**Summary:** Sửa đủ H1, H2, M1–M4, L1–L6; 157 bài CR-717 + 777 bài hồi quy nghi_phep xanh (còn 3 đỏ customs/forum có sẵn).
**Concerns:** H1 chỉ kiểm bằng SQL biên dịch (SQLite không có RR); M4 chỉ cố định phần ĐỌC, phần GHI vẫn 1 câu/dòng; preview thêm `conflict:"scope"` (FE cần biết).
