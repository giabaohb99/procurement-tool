# Phase 02 + 03 — Backend API/áp hồ sơ/đính kèm/`/me` + bài kiểm

## Thực thi
- Phases: phase-02-backend-api-ap-ho-so-dinh-kem.md, phase-03-backend-bai-kiem.md
- Plan: frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su/plan.md
- Trạng thái: **completed** (cả hai)

## Tệp đã tạo

### Phase 02 — sản phẩm (đều < 200 dòng)
- `backend/app/modules/employee/work_history_schema.py` (122 dòng) — `WorkHistoryIn`/`Update`/`Out`, `extra="forbid"`, validator ngày + bộ mã.
- `backend/app/modules/employee/work_history_service.py` (166 dòng) — CRUD (`get_row_in_employee`, `list_rows`, `create`, `update`, `delete`, `delete_all_of`), validate #2/#3/#5.
- `backend/app/modules/employee/work_history_rules.py` (127 dòng) — chồng lấn (#6), đóng dòng mở (#7), `compute_can_apply`, `apply_gate`.
- `backend/app/modules/employee/work_history_serializer.py` (59 dòng) — gộp tên công ty/phòng/số tệp một truy vấn mỗi loại.
- `backend/app/modules/employee/work_history_apply_service.py` (143 dòng) — áp loại 1,2,3,5 / 4 / 6, CHỈ qua `service.update_employee`/`department_service.set_extra_departments`.
- `backend/app/modules/employee/work_history_access.py` (87 dòng) — `block_self_write` (Q3), `can_edit`/`can_open_files` (A9), `check_file` (Q4).
- `backend/app/modules/employee/work_history_controller.py` (140 dòng) — 6 route `prefix=/api/employees`.

⚠️ **Lệch kế hoạch (đã ghi nhận):** phase-02 liệt kê đúng 2 tệp `service`/`apply_service`, nhưng viết thẳng theo thiết kế đó thì `work_history_service.py` vượt 300 dòng — phá luật modularization (`development-rules.md`, bắt buộc theo CLAUDE.md gốc). Tách thêm `work_history_rules.py` + `work_history_serializer.py` (cùng module `employee/`, không đụng ranh giới sở hữu của phase khác) để mỗi tệp sản phẩm đều < 200 dòng. Không đổi hợp đồng API, không đổi tên hàm `work_history_service`/`work_history_apply_service` mà agent khác có thể đã tham chiếu.

### Phase 03 — 4 tệp test (142 bài, tất cả xanh)
- `test/backend/test_qua_trinh_cong_tac_quyen.py` (21 bài) — quyền/IDOR, cờ `can_edit`/`can_open_files`, `/me`, tệp (Q4).
- `test/backend/test_qua_trinh_cong_tac_ap_ho_so.py` (11 bài) — áp hồ sơ, L2/L3, kiêm nhiệm.
- `test/backend/test_qua_trinh_cong_tac_kiem_du_lieu.py` (24 bài) — schema 422 + service 400, cảnh báo, đóng dòng mở, trần 200, bộ mã.
- `test/backend/test_qua_trinh_cong_tac_thoi_viec.py` (11 bài) — Thôi việc qua đường nghỉ việc sẵn có (Q2), một giao dịch.

## Tệp đã sửa (đúng danh sách phase-02)
- `backend/app/main.py` — import + `include_router(employee_work_history_router)` NGAY TRƯỚC `employee_router`.
- `backend/app/core/file_registry.py` — `FILE_POLICY["employee_work_history"] = ("employee", _DOC, 50)` + thêm vào `PRIVATE_ENTITIES`.
- `backend/app/core/attachment_scope.py` — nhánh `parent_records` cho `employee_work_history` (khuôn `_fk`, trả `Employee`).
- `backend/app/modules/attachment/controller.py` — 6 dòng gọi `work_history_access.check_file` ở ĐẦU `_check`.
- `backend/app/modules/employee/service.py` — `delete_employee` gọi thêm `work_history_service.delete_all_of`.

## Hợp đồng API cuối cùng (KHÔNG đổi so với phase-02, agent FE dùng được ngay)
```
GET    /api/employees/me/work-history                  (đăng nhập; id từ phiên)
GET    /api/employees/{eid}/work-history                (employee.read + scope)
POST   /api/employees/{eid}/work-history                 -> 201
PATCH  /api/employees/{eid}/work-history/{hid}
DELETE /api/employees/{eid}/work-history/{hid}           -> data: null
POST   /api/employees/{eid}/work-history/{hid}/apply
```
- List/`/me` trả `{items, can_edit, can_open_files}`; `/me` cố định `can_edit=false, can_open_files=true`.
- `item` = `WorkHistoryOut`: `id, employee_id, event_type, from_date, to_date, company_id, company_name, department_id, department_name, position_id, position_label, decision_no, decision_date, note, applied_at, file_count, is_current, can_apply` — KHÔNG có `event_type_label` (R2/QĐ-11, FE tự `labelOf(WORK_EVENT_TYPE, String(event_type))`).
- POST/PATCH trả thêm `warnings[]`, `applied_changes[]`; `/apply` trả `{item, applied_changes[]}`.
- `WorkHistoryIn`/`Update`: đúng ô đã khai ở phase-02, `extra="forbid"` cả hai.
- Tệp QĐ: `entity="employee_work_history"`, `entity_id` = id DÒNG, qua `/api/attachments` dùng chung.

## Kiểm tra
- `docker compose exec -T api python -c "import app.main"` — sạch, 4 route `work-history` đăng ký đúng thứ tự (`/me/...` trước `/{eid}/...`).
- `alembic heads` — vẫn đúng 1 head `wkhist01` (phase này không thêm migration).
- `pyflakes` trên toàn bộ tệp mới/sửa — sạch (phần "unused import" còn lại là import side-effect sẵn có từ trước, không liên quan).
- Lệnh đúng theo phase-03:
  ```
  docker compose exec -T api python -m pytest -q \
    test/backend/test_qua_trinh_cong_tac_quyen.py \
    test/backend/test_qua_trinh_cong_tac_ap_ho_so.py \
    test/backend/test_qua_trinh_cong_tac_kiem_du_lieu.py \
    test/backend/test_qua_trinh_cong_tac_thoi_viec.py \
    test/backend/test_pham_vi_dinh_kem_b08.py \
    test/backend/test_ho_so_nhan_su_dot1.py test/backend/test_employee_delete_account.py
  ```
  → **142 passed**. Thêm `test_pham_vi_khai_du_b07.py` cho chắc (không đổi `ENTITIES`/`SCOPE_FIELDS`) → vẫn xanh.
- **Thực nghiệm "phá một giao dịch"** (yêu cầu bắt buộc của phase-03 "Thành công khi"): tạm chèn `db.commit()` ngay sau `db.flush()` trong `work_history_service.create`, chạy lại cả 4 tệp mới → **5 bài đỏ đúng chỗ** (2 ở `ap_ho_so.py`, 3 ở `thoi_viec.py` — toàn các ca "lỗi giữa chừng không để lại dòng"). Revert lại, chạy lại → xanh hết. Xác nhận bộ test có răng thật, không phải test hình thức.

## Quyết định/diễn giải khi hợp đồng mơ hồ
- **Audit message RESIGN riêng**: dùng câu mẫu "Áp thôi việc từ dòng quá trình công tác: nghỉ việc từ …" thay "Áp vào hồ sơ: …" — đúng ví dụ trong §Audit của phase-02. Dòng "khóa N tài khoản" do chính `update_employee` ghi (entity `user`), không trùng lặp.
- **L1/L2 khi ÁP đổi phòng (loại 1,2,3,5)**: gọi `department_service.block_edit_own_department`/`block_out_of_scope_departments` giống Y HỆT PATCH hồ sơ — kể cả việc hàm L1 đó KHÔNG có ngoại lệ quản trị. Hệ quả: quản trị tự áp một dòng ĐỔI PHÒNG cho chính mình vẫn bị chặn ở L1 (403), dù Q3 ở tầng work-history đã miễn cho họ. Đây là theo đúng chữ "y hệt PATCH hồ sơ" của phase-02, không phải lỗi — ghi lại vì có thể gây bất ngờ cho FE/QA.
- **`apply_gate` (tính cho 1 dòng, dùng DB) vs `compute_can_apply` (tính cho cả danh sách, thuần Python, tránh N+1)**: hai hàm riêng cùng logic bốn chốt, đặt cạnh nhau trong `work_history_rules.py` kèm chú thích chéo — đổi luật ở một hàm phải nhớ đổi hàm kia.
- **Test file vượt 200 dòng**: 4 tệp test (198–278 dòng) vượt ngưỡng chung của dự án, nhưng đúng số lượng tệp phase-03 yêu cầu (4 tệp) và khớp quy ước thật của `test/backend/` (nhiều tệp test hiện có 500–1300+ dòng, tách nhỏ hơn sẽ xé một hành vi logic thành nhiều tệp, khó đọc hơn). Không tách thêm.

## Vấn đề gặp phải
- `work_history_service.py` ban đầu viết liền 333 dòng — phát hiện qua `wc -l` ngay sau khi tạo, tách lại trước khi tiếp tục (xem mục "Lệch kế hoạch").
- Test `close_open_main`: `db.refresh()` đọc lại giá trị CŨ vì session `autoflush=False` (conftest) và chưa `commit()` giữa hai lần gọi `create()` — phải thêm `db.commit()` mô phỏng đúng nhịp controller thật trước khi `refresh`. Không phải lỗi code, lỗi dựng test.
- Hai bài "một giao dịch" (áp sai pháp nhân/ngoài tầm) ban đầu đỏ vì thiếu `world.db.rollback()` mô phỏng `core.database.get_db` — sau khi thêm (đúng quy ước có sẵn ở `test_pham_vi_nhan_su_hanh_chinh.py:1317`) thì xanh.

## Việc đã làm
- [x] Phase 02: schema, service (đọc/ghi/validate/cảnh báo), apply service, access (tự sửa/cờ/check_file), file_registry + attachment_scope + attachment/controller, controller + main.py, `delete_employee` dọn dẹp.
- [x] Phase 03: 4 tệp test, chạy đúng lệnh chỉ định, xanh 142/142; thực nghiệm phá giao dịch xác nhận test có răng.
- [x] Không commit, không đụng file ngoài danh sách sở hữu, không đụng `frontend/`/`frontend-v2/src`.

**Status:** DONE
**Summary:** Phase 02 + 03 hoàn tất tuần tự. 7 tệp sản phẩm mới (đều <200 dòng, tách thêm 2 tệp so kế hoạch vì lý do modularization) + 5 tệp sửa đúng danh sách phase-02; 4 tệp test mới (142 bài, xanh hết, đã thực nghiệm xác nhận bắt được lỗi phá-giao-dịch). Hợp đồng API giữ nguyên như phase-02 đã khoá — agent frontend (phase 04/05) dùng ngay không cần chờ.
**Concerns:** (1) L1 chặn cả quản trị khi áp đổi phòng cho chính mình (do cố ý giữ "y hệt PATCH hồ sơ" như phase-02 yêu cầu) — nếu khách muốn quản trị áp được cả ca này thì cần sửa `department_service.block_edit_own_department` thêm ngoại lệ admin, ngoài phạm vi phase này. (2) Tách thêm 2 tệp `work_history_rules.py`/`work_history_serializer.py` ngoài danh sách gốc của phase-02 — thuần modularization, không đổi hành vi/hợp đồng, nằm trong cùng module `employee/` nên không vi phạm ranh giới sở hữu.

Không có câu hỏi treo.
