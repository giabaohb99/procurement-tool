# Phase 03 + 04 — API Mẫu hợp đồng + API Hợp đồng lao động (backend)

Status: DONE (chưa commit). 266 test hdld xanh + 230 test hồ sơ/quá trình công tác/b07/bảo mật tệp + 64 test soi `app.routes` xanh. Không đụng `frontend-v2/`.

## Bắt buộc từ review 01/02 — đã làm
1. Upload mẫu: `guard_upload` rồi `inspect_template` (`template_service.read_and_inspect`); cả `PUT /{id}/file`.
2. Đóng DoS vòng lặp lồng: `docx_engine._SimpleVariableEnvironment._parse` chạy `_ensure_only_simple_variables` trên AST. Chỉ nhận chữ tĩnh + `{{ ten_bien }}`. Mọi `{% %}` (kể cả `{%p`/`{%tr`/`{%r`: docxtpl `patch_xml` đổi về `{% %}` trước khi tới Jinja), biểu thức khác tên biến (gọi hàm, `.thuộc_tính`, filter, phép tính, chuỗi hằng) → `ForbiddenTemplateSyntax` → `TemplateRejected` (422). Chặn ở bước phân tích, KHÔNG chạy vòng lặp (test < 3s). Hook ở `_parse` nên phủ cả header/footer/footnote/core properties lúc render. Chú thích `{# #}` lexer bỏ, vô hại. Sandbox giữ nguyên. `render` dùng cùng env nên tệp storage bị thay bằng bản có vòng lặp vẫn bị từ chối (422 «Mẫu không sinh được»).
   - Hệ quả: `{% if %}` trong mẫu KHÔNG còn dùng được (kể cả `{% if phu_cap_ghi_chu %}`). Đã sửa test cũ trong `test_hdld_bo_may_docx.py` (đổi thành bài từ chối + 13 payload tham số hóa + nested-for).
3. Không đổi đường dẫn / hình dạng phản hồi so với phase-03 doc. Chỗ plan chưa nói rõ, tôi chốt như dưới ("Quyết định mới").

## Đường API cuối cùng (envelope `{success,message,data}`; lỗi `{success:false,error:{code,message,details}}`)

### Mẫu — `/api/labor-contract-templates` (khóa `labor_contract_template`)
| Method | Path | Quyền | Vào | Ra (`data`) |
|---|---|---|---|---|
| GET | `/placeholders` | đăng nhập + (`labor_contract_template.read` HOẶC `labor_contract.create`) | — | `[{key,label,group,example}]` |
| GET | `` | read | query `company_id, contract_type, is_active, q, page, page_size` | `{total, items:[Template]}` |
| GET | `/{id}` | read, scope 404 | — | `Template` |
| POST | `` | create | multipart: `file`(.docx ≤10MB), `name`(1..200), `company_id`(≥1), `contract_type`(1,2,3,4,5,9), `note`(≤500) | 201 `Template` |
| PATCH | `/{id}` | write | JSON `{name?, note?, contract_type?, is_active?}` (extra forbid; không có `company_id`) | `Template` |
| PUT | `/{id}/file` | write | multipart `file` | `Template` |
| GET | `/{id}/file` | read | — | stream .docx (`Content-Disposition: attachment; filename*=UTF-8''…`) |
| DELETE | `/{id}` | delete | — | `null`; 409 nếu có HĐ tham chiếu (message gợi ý «Ngừng dùng») |

`Template` = `{id, company_id, company_name, contract_type, name, note, original_filename, file_size, placeholders:string[], is_active, created_at, created_by_name, contract_count}`. Không có `url`/`file_key`/`file_id`.
Mẫu bị từ chối (biến lạ / cú pháp / zip / macro / sai nội dung) → **422** với `error.message` tiếng Việt và `error.details = {"unknown": ["ten_bien_la", ...]}` (mảng rỗng nếu lý do khác biến lạ). FE nên đọc `error.details.unknown`.

### Hợp đồng — khóa `labor_contract`
| Method | Path | Quyền | Vào | Ra (`data`) |
|---|---|---|---|---|
| GET | `/api/employees/{eid}/labor-contracts` | read (scope) | — | `{items:[Contract], can_create}` (sắp `start_date` giảm dần) |
| GET | `/api/employees/{eid}/labor-contract-templates?contract_type=` | create HOẶC write | — | `[{id,name,contract_type}]` mẫu active của pháp nhân HIỆN TẠI của NV |
| POST | `/api/employees/{eid}/labor-contracts` | create | JSON `LaborContractCreate` | 201 `{item:Contract, warnings:string[]}` |
| GET | `/api/labor-contracts/{id}` | read, scope 404 | — | `Contract` |
| PATCH | `/api/labor-contracts/{id}` | write; chỉ DRAFT (409) | JSON mọi trường tùy chọn | `{item:Contract, warnings:string[]}` |
| DELETE | `/api/labor-contracts/{id}` | delete; chỉ DRAFT/CANCELLED (409) | — | `null` (xóa kèm 2 tệp) |
| POST | `/api/labor-contracts/{id}/generate` | write; chỉ DRAFT | `{template_id}` | `Contract` |
| GET | `/api/labor-contracts/{id}/document` | **print** + scope | — | stream .docx `HDLD-{số}-{họ tên}.docx`; 404 nếu chưa sinh |
| PUT | `/api/labor-contracts/{id}/signed-file` | write; DRAFT/SIGNED | multipart `file` (pdf/jpg/jpeg/png ≤50MB, sniff byte đầu) | `Contract` |
| GET | `/api/labor-contracts/{id}/signed-file` | read | — | stream; 404 nếu chưa có |
| POST | `/api/labor-contracts/{id}/transition` | write | `{to_status, date?, reason?}` | `Contract` |

`LaborContractCreate` (extra forbid): `contract_type`(1,2,3,4,5,9), `contract_no`(≤50, mặc định ""), `start_date`, `end_date?`, `job_title?`(≤100; null → lấy `employee.position`), `work_location?`(≤255; null → `employee.work_location`), `base_salary, insurance_salary, allowance`(int 0..10^12, mặc định 0), `allowance_note`(≤500), `note`(≤500). Ràng buộc: `end>=start`; loại 1,2,4,5 bắt buộc `end_date`; loại 3 cấm `end_date`; loại 9 tùy. Sai → 422 (POST) / 400 (PATCH, kiểm trên giá trị gộp). PATCH: truyền `end_date: null` để gỡ ngày kết thúc; các cột khác null bị bỏ qua.

`Contract` = `{id, code, contract_no, employee_id, company_id, company_name, department_id, department_name, template_id, template_name, contract_type, status, effective_status, sign_date, start_date, end_date, job_title, work_location, base_salary, insurance_salary, allowance, allowance_note, note, has_generated_file, generated_at, has_signed_file, terminated_date, terminate_reason, created_at, created_by_name, can_edit, can_delete, can_generate, can_print, can_upload_signed, transitions:int[]}`.
- `effective_status`: 3 (HẾT HẠN) khi `status==2` và `end_date < hôm nay VN`; còn lại = `status`.
- `transitions`: mã đích được phép (DRAFT → [2,5]; SIGNED → [4]); rỗng nếu không có `write` trong phạm vi.
- Cờ `can_*` do backend tính (1 truy vấn phạm vi / hành động / trang). `can_print` = có print trong phạm vi VÀ đã có tệp sinh.
- `transition`: `date` = ngày ký (→2, bắt buộc) hoặc ngày chấm dứt (→4, bắt buộc, ≥ start_date); `reason` bắt buộc cho →5 và →4. Cột ghi: `sign_date`; `terminated_date`+`terminate_reason`; hủy ghi lý do vào `terminate_reason`. Bảng 5x5 kiểm đủ; sai đường → 409; thiếu dữ liệu → 400.
- DRAFT → SIGNED không đòi tệp nào (đúng quyết định chốt).

## Quyết định mới (plan chưa nêu) — FE cần biết
- POST/PATCH hợp đồng trả `{item, warnings}` (không phải item trần); `warnings` có khi xác định thời hạn > 36 tháng (không chặn).
- List mẫu trả `{total, items}` (khuôn `document-templates`); không trả `page/page_size`.
- `GET /employees/{eid}/labor-contracts` 404 nếu nhân sự không tồn tại; ngoài phạm vi HĐLĐ thì `items:[]` (không lộ). `can_create` chỉ là gợi ý (có quyền create + NV có pháp nhân); chốt thật ở POST (403 «Nhân sự thuộc pháp nhân / phòng ngoài phạm vi của bạn»; 400 nếu NV chưa có pháp nhân).
- Tải `document`: `require(print)` + `get_scoped(..., "print")` (plan ghi «phạm vi read»; dùng print cho nhất quán với cờ `can_print`).
- Tên tệp: `safe_filename` bỏ ký tự điều khiển / `/ \ : * ? " < > |`, cắt 150 ký tự nhưng GIỮ đuôi; tên tệp scan dài không còn 422.
- Lỗi storage khi đọc → 502 (không 500).
- Audit: entity `labor_contract` / `labor_contract_template`, action `create|update|delete`, đổi trạng thái dùng `document_status` (message nêu nhãn trạng thái), sinh tệp dùng `update`. Không mở mã mới.

## Files
Tạo (`backend/app/modules/labor_contract/`): `access.py`, `lookup.py`, `file_response.py`, `template_schema.py`, `template_serializer.py`, `template_service.py`, `template_controller.py`, `rules.py`, `schema.py`, `serializer.py`, `service.py`, `generate_service.py`, `controller.py`. (tất cả < 160 dòng)
Sửa: `backend/app/modules/labor_contract/docx_engine.py` (chặn cú pháp), `backend/app/main.py` (2 router, include TRƯỚC `employee_router`), `backend/app/modules/employee/service.py::delete_employee` (chặn 409 trước `detach_users` + dọn HĐ nháp/hủy kèm tệp), `plan.md`, `phase-03/04` (done).
Test tạo: `test/backend/hdld_factory.py` (fixture dùng chung: kho tệp giả, client nhiều người), `test_hdld_mau_hop_dong_api.py` (32), `test_hdld_luat_trang_thai.py` (41), `test_hdld_hop_dong_api.py` (48), `test_hdld_sinh_tai_tep.py` (39). Sửa: `test_hdld_bo_may_docx.py` (67).

## Bug thật tìm thấy nhờ test
- `rules.duration_warnings` tính thiếu ngày kết thúc (36 tháng + 1 ngày không cảnh báo) → tính cả ngày cuối.
- `safe_filename` cắt mất đuôi tệp khi tên dài → báo «Định dạng .?» khó hiểu → cắt phần tên, giữ đuôi.
- Harness: `dependency_overrides` là toàn cục nên 2 client «đăng nhập» 2 người bị đè nhau → `client_as` tra người theo token từng request (bài phạm vi chéo pháp nhân mới đúng).

## Tests
- `test_hdld_*` (7 tệp): 266 pass (30s). Hồ sơ nhân sự / quá trình công tác / b07 / bảo mật tệp: 230 pass. Test soi `app.routes`: 64 pass. `import app.main` OK.
- Phủ: scope 404 mọi đường `{id}` + 403 tạo ngoài phạm vi (không để lại dòng/tệp), mẫu sai pháp nhân/loại/ngừng → 400, sinh khi SIGNED/CANCELLED → 409, print 403 (read-only) + 404 (ngoài phạm vi), `delete_employee` có SIGNED/TERMINATED → 409 và chỉ nháp/hủy → dọn sạch tệp, EXPIRED theo ngày, upload từ chối (đuôi, rỗng, giả zip, macro, >10MB, vòng lặp lồng, biến lạ), scan giả (pdf/png/svg/exe), thay tệp hỏng giữ tệp cũ, lỗi giữa chừng không mồ côi, header injection, số truy vấn danh sách cố định.
- Chưa chạy typecheck FE (không đụng FE).

## Lưu ý / chưa giải
- Mẫu `GET /employees/{eid}/labor-contract-templates` chỉ gác bằng quyền create/write của `labor_contract` + NV tồn tại (không có hàng để `get_scoped`); lộ tối đa tên mẫu của pháp nhân của NV đó. Chấp nhận được, nếu muốn chặt hơn cần thêm hàm kiểm phạm vi theo (company, dept, employee) giả định.
- Footnote/core properties: cú pháp bị chặn ở `_parse` khi docxtpl render chúng; biến trong đó vẫn không được kiểm «biến lạ» lúc upload (render ra rỗng/lỗi StrictUndefined → 422 ở dry-run).
- Cần quyền cho môi trường đang chạy: tick tay `labor_contract*` hoặc `SEED_FORCE_SYNC` (đã ghi từ phase 01).
- `docxtpl` đã cài tay trong container api; máy khác cần `docker compose up --build -d api`.
- Không gọi `code-reviewer`/`tester` agent (agent con không có Task). Docs impact: minor (API mới, chưa cập nhật `docs/`; phase 07).

**Status:** DONE
**Summary:** Phase 03 + 04 backend xong, 266 test HĐLĐ + regression xanh; đã đóng lỗ DoS vòng lặp lồng (mẫu chỉ nhận `{{ biến }}`).
**Concerns/Blockers:** Mẫu `.docx` không dùng được `{% if %}`/`{% for %}` nữa (theo yêu cầu) — báo người soạn mẫu; endpoint chọn mẫu theo NV chưa chặn theo phạm vi từng hàng.
