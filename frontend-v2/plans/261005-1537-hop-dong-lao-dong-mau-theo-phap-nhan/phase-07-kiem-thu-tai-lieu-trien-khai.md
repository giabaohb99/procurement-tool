# Phase 07 — Kiểm thử chéo, tài liệu, triển khai

## Context Links
- `CLAUDE.md` (cổng FE theo thư mục, nhật ký task, seed prod D-018), `doc/erp/hrm/01-ho-so-nhan-su.md`, `doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md` (V1-5), `doc/tai-lieu-ky-thuat/nhat-ky-task.md`

## Overview
Priority P2. Status pending. Ma trận kiểm thử, rà bảo mật, tài liệu, ghi chú deploy.

## Ma trận kiểm thử
| Lớp | Nội dung | Tệp |
|---|---|---|
| Unit BE | số→chữ; catalog ↔ context_builder đủ khóa; docx_engine (SSTI, escape, run tách, zip bomb, macro, biến lạ, cú pháp hỏng); luật trạng thái/ngày | `test_hdld_doc_so_thanh_chu.py`, `test_hdld_bo_may_docx.py`, `test_hdld_luat_trang_thai.py` |
| Tích hợp BE | phạm vi company/dept/self/owner trên 2 khóa; tạo ngoài phạm vi 403; `{id}` ngoài phạm vi 404; mẫu khác pháp nhân 400; print gác tải; delete_employee 409; `_SYS_ENTITIES` chứa 2 khóa; ENTITIES = 74 | `test_hdld_mau_hop_dong_api.py`, `test_hdld_hop_dong_api.py`, `test_hdld_sinh_tai_tep.py`, `test_pham_vi_khai_du_b07.py` |
| Unit FE | zod schema, payload, badge EXPIRED, hộp tải mẫu hiện biến lạ, stopPropagation, ẩn theo quyền | `src/modules/hr/**/*labor-contract*.test.ts(x)` |
| E2E tay | 2 pháp nhân × 2 mẫu; HR phạm vi `company` A: không thấy mẫu/HĐ B; lập → sinh → mở .docx bằng Word/LibreOffice kiểm dấu tiếng Việt, ngày, tiền, chữ → ký → chấm dứt | ghi kết quả vào báo cáo |

Lệnh (chỉ phần vừa sửa): `docker compose exec -T api python -m pytest test/backend/test_hdld_*.py test/backend/test_pham_vi_khai_du_b07.py test/backend/test_dong_bo_giao_dien_v2.py test/backend/test_ho_so_nhan_su_dot1.py "test/backend/test_qua_trinh*" -q` (glob qua shell); FE: `npm run typecheck`, `npm run lint`, `npx vitest run src/modules/hr src/modules/system`.

## Tài liệu
- `doc/erp/hrm/02-hop-dong-lao-dong.md` (mới): mô hình, luật trạng thái, danh mục biến, hướng dẫn soạn mẫu Word (gõ biến liền một lần; `{%p if %}` cho đoạn tùy chọn).
- `.claude/rules/hr-employee-profile.md`: thêm mục HĐLĐ (bẫy: sandbox, snapshot pháp nhân, tải tệp chỉ qua endpoint, `_SYS_ENTITIES`, ENTITIES 74); thêm `backend/app/modules/labor_contract/**`, `test/backend/*hdld*` vào `paths:`.
- `CLAUDE.md`: bảng luật trỏ tới mục mới (1 dòng).
- `10-de-xuat-ap-dung.md`: V1-5 → «Đang làm / Xong phần lập HĐ; còn cảnh báo hết hạn».
- Nhật ký task (câu tiếng Việt trọn vẹn, mã nguồn dòng cuối).

## Triển khai
1. `requirements.txt` đổi ⇒ prod phải **build lại** image api (`-f docker-compose.production.yml`).
2. Migration `lbrct01` chạy tự động ở `start.prod.sh`.
3. Vai trò trên DB thật KHÔNG tự có 2 khóa (D-018): tick ở màn Phân quyền, hoặc `SEED_FORCE_SYNC=true` một lần rồi trả `false`. Người đang đăng nhập phải đăng nhập lại.
4. Trước deploy: chạy full `npm run check` (luật: chỉ trước deploy).

## Rollback
Revert FE → revert BE → `alembic downgrade wsched01`. Không dữ liệu cũ nào bị sửa (chỉ thêm bảng).

## Todo
- [ ] chạy ma trận · [ ] E2E tay · [ ] code-reviewer · [ ] docs + rules · [ ] nhật ký task · [ ] ghi chú deploy

## Success Criteria
Mọi test trong ma trận xanh; code-reviewer không còn High; tài liệu cập nhật; tệp .docx sinh ra mở được bằng Word không cảnh báo «nội dung không đọc được».

## Risk Assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Quên tick quyền trên prod → «không thấy tính năng» | Cao×Thấp | Ghi chú deploy bước 3 |
| Build prod thiếu dep | Thấp×Cao | Build image local bằng Dockerfile.api trước |
