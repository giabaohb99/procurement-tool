# Phase 01 + 02 — nền dữ liệu, quyền, bộ máy docx (backend)

Status: DONE_WITH_CONCERNS. Chưa commit.

## Kết quả
- Migration `lbrct01` (down `wsched01`) áp OK; upgrade/downgrade/upgrade sạch; autogenerate lại không còn drift ở 2 bảng.
- Test xanh: 3 tệp hdld mới (92 bài) + b07 + dong_bo_giao_dien_v2 + ho_so_nhan_su_dot1 + bao_mat_tai_tep + cr523 + status_catalog = 184 + 10 pass.
- `gen_status_ts` đã chạy, `--check` OK (+21 dòng, chỉ 2 bộ mã mới). FE typecheck 0 lỗi, vitest authorization + system/config xanh.
- ENTITIES/SCOPE_FIELDS 72 -> 74; cả hai khóa vào `_SYS_ENTITIES`; chỉ `hr_profile` được seed quyền.

## Bẫy/phát hiện
1. Bản TS đọc «... đồng chẵn», plan ghi «... đồng». Chép đúng TS (có «chẵn»); test chung số liệu với bản TS.
2. Sandbox Jinja biến `x.__class__` thành Undefined IM LẶNG (in ra rỗng, không ném) -> payload SSTI "lọt" im. Đã dùng `StrictUndefined` + `ImmutableSandboxedEnvironment` nên in ra là bị từ chối.
3. `range(10**11)` ném `OverflowError` (không phải TemplateError); XML hỏng ném lỗi lxml -> đã bọc, mọi lỗi thành `TemplateRejected` (không 500).
4. `read_amount_vi` số > 10^15-1: Decimal.quantize nổ InvalidOperation (nuốt thành «Không đồng» là sai) -> chặn bằng ValueError trước quantize.
5. `describe_duration` (thời hạn) ban đầu ra «-1 ngày» với start 31/01; viết lại theo mốc cộng tháng kẹp cuối tháng.
6. Cột JSON `placeholders` để nullable (khớp migration; MySQL JSON không có default cố định).

## Concerns
- `guard_upload` KHÔNG sniff .docx (chỉ jpeg/png/pdf...). Phase 03 phải gọi `inspect_template` (đã kiểm zip/document.xml/macro) sau guard_upload — đừng bỏ.
- Vòng lặp lồng nhau trong mẫu (vd. 100000x100000 qua 2 for) vẫn có thể ngốn CPU lúc dry-run; sandbox chỉ chặn một `range` > 100000. Phase 03 nên chạy tải mẫu đồng bộ nhưng giới hạn (hoặc cân nhắc timeout/subprocess). Chưa xử lý (YAGNI cho tới khi chốt mô hình mối đe dọa: chỉ HR tải mẫu).
- Biến trong footnotes / core properties không nằm trong kiểm biến lạ của docxtpl (render ra rỗng, vẫn qua sandbox).
- Cần `docker compose up --build -d api` một lần ở máy khác; local đã `pip install docxtpl==0.20.2` thủ công trong container (mất khi recreate container nếu chưa build).
- Không thêm khóa `labor_contract` vào `hr_leave`/vai trò khác; môi trường đang chạy cần tick tay hoặc SEED_FORCE_SYNC.
- Chưa dùng được `fmt_date` kiểu `str` cho giá trị date từ DB dạng datetime (chỉ date).

## Files
Tạo: backend/app/core/labor_contract_codes.py, backend/app/core/vn_number_words.py, backend/app/modules/labor_contract/{__init__,model,template_model,placeholder_catalog,context_builder,docx_engine}.py, backend/migrations/versions/lbrct01_hop_dong_lao_dong.py, test/backend/test_hdld_{nen_du_lieu,doc_so_thanh_chu,bo_may_docx}.py
Sửa: backend/app/core/{code_sets,all_models,permissions,scoping,file_registry}.py, backend/app/seed.py, backend/requirements.txt (docxtpl==0.20.2, Jinja2==3.1.6), test/backend/test_pham_vi_khai_du_b07.py (72->74), frontend-v2/src/core/authorization/permission-types.ts, frontend-v2/src/modules/system/config/permission-groups.ts, frontend-v2/src/shared/constants/statuses.ts (sinh), plan.md (status 01/02)

## Chưa giải
- `seed_prod.py` có cùng nguồn STD_ROLES? Chưa kiểm sâu (không đổi gì ở đó).
