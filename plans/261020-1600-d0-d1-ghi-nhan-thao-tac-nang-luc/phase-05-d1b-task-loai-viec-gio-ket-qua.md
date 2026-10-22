# Phase 05 — D1b: Task Dự án có loại việc, giờ ước lượng, giờ thực tế, kết quả

## Context links
- Lời đại ca: «Task Dự án có thêm loại việc, giờ ước lượng, giờ thực tế, kết quả đạt hay làm lại»
- `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §5 «Phần Dự án», §8 câu 3 (ai khai danh mục loại việc)
- BE: `backend/app/modules/work/task_model.py` (`tab_work_task`), `model.py` (`WorkTaskStatus` OPEN 1/DONE 2/CANCELLED 3), `task_service.py` (`_apply_status` l.~367: mở lại XÓA `completed_at`), `schema.py` (`TaskCreate`/`TaskUpdate`)
- FE: `frontend-v2/src/modules/work/types/work.ts`, `components/task-detail-sheet.tsx`, `task-draft-row.tsx`, `utils/list-columns.ts`, `config/task-filter-fields.ts`
- `backend/scripts/sync_task_journal.py` (chỉ đi qua API, không cần đổi)

## Overview
- P1 · **2 ngày** (BE 1 · FE 1) · **implemented — duoc-CR-656 (20/10/2026)** · chạy song song với luồng D0.
- Thực hiện thật: migration `d1cap01` (gộp D1b+D1a+D1c, một migration như chốt); FE do cùng phiên làm (không thấy ai khác sửa `modules/work` trên origin).
- Danh mục loại việc + 4 cột mới trên `tab_work_task`. Đây là phase D1 đầu tiên vì D1a đọc `task_type_id`.

## Key insights
- Hiện chỉ có `kind` TASK/MILESTONE — không phải loại nghiệp vụ. Trường tùy biến (`tab_work_label_field`) theo **từng dự án** → không đồng nhất toàn công ty, AI không gom được → cần **cột thật**.
- Không có bảng giờ công/timesheet. YAGNI: giờ thực tế **nhập tay một số** khi xong (không làm chấm giờ — khớp memory «Không làm chấm công»).
- «Làm lại» suy được từ lịch sử: `tab_change_log` ghi `status` 2→1 (mở lại sau xong). Không cần cột đếm riêng (D1a đếm). Cột `outcome` là **đánh giá của người giao**.
- Một task có thể nhiều PIC → giờ thực tế là **tổng của task**; D1a chia theo PIC khi tính năng lực (Q10).

## Requirements
- Danh mục loại việc theo pháp nhân, tùy chọn gắn phòng ban; quản trị khai (Q3).
- Task: chọn loại việc, nhập giờ ước lượng (lúc giao), giờ thực tế (lúc xong, không bắt buộc), kết quả.
- Kết quả: người giao (người tạo task) hoặc quản trị dự án chọn «Đạt» / «Phải làm lại» sau khi task DONE; «Phải làm lại» tự mở lại task.
- Bot/AI (`plan_service`, A2) đặt được `task_type_id`, `estimate_hours` qua cùng schema.

## Architecture
**Mã** `backend/app/modules/work/model.py` (cạnh `WorkTaskStatus`): `WorkTaskOutcome(IntEnum)` 1 PASSED «Đạt» · 2 REWORK «Phải làm lại»; đăng ký code set `work_task_outcome`.
**Bảng mới `tab_work_task_type`** (`work/task_type_model.py`, AuditMixin): `id · company_id BIGINT · department_id BIGINT DEFAULT 0 (0 = cả pháp nhân) · code VARCHAR(30) · name VARCHAR(120) ·
default_estimate_hours DECIMAL(6,2) NULL · is_active BOOL · sort_order INT` UNIQUE `(company_id, code)`.
**Cột mới `tab_work_task`**: `task_type_id BIGINT DEFAULT 0` · `estimate_hours DECIMAL(6,2) NULL` · `actual_hours DECIMAL(6,2) NULL` · `outcome SMALLINT DEFAULT 0` (0 = chưa đánh giá) ·
INDEX `ix_work_task_type_status (task_type_id, status)` · INDEX `ix_work_task_completed_at (completed_at)` (cho D1a).
Ràng: `0 < hours ≤ 999` (schema `Field(ge=0, le=999)`); `actual_hours`, `outcome` chỉ đặt khi DONE; đặt `outcome=REWORK` → `_apply_status(OPEN)` + audit «Đánh giá phải làm lại».
**API**
- `GET /api/work/task-types?company_id` — `require("work_task","read")` (ai dùng Dự án cũng chọn được).
- `POST/PATCH/DELETE /api/work/task-types[/{id}]` — `require("setting","write")` (mặc định quản trị; Q3). Xóa = `is_active=false` nếu đã có task dùng.
- `PATCH /api/work/tasks/{id}` nhận thêm `task_type_id, estimate_hours, actual_hours`; `POST /api/work/tasks/{id}/outcome {outcome}` (quyền: người tạo task hoặc CAN_MANAGE của list).
**FE**: ô «Loại việc» (select), «Ước lượng (giờ)», «Thực tế (giờ)» trong `task-detail-sheet.tsx`; hộp «Đánh giá kết quả» hiện khi DONE; cột tùy chọn trong list view + bộ lọc theo loại việc;
màn quản trị danh mục: `CrudListPage` trong `modules/system` hoặc `modules/work/pages/task-type-catalog-page.tsx`.

## Related code files
Tạo BE: `backend/app/modules/work/task_type_model.py` · `task_type_service.py` · `task_type_controller.py` · `task_outcome_service.py` (giữ `task_service.py` đang 479 dòng không phình thêm) ·
migration `d1task01_loai_viec_gio_ket_qua_task.py`.
Sửa BE: `work/model.py` (`WorkTaskOutcome` + đăng ký) · `task_model.py` (4 cột + 2 index) · `schema.py` (trường mới, `max_length`/giới hạn số theo `backend-input-limits`) ·
`task_service.py` (`update_task` gán 3 trường; gọi `task_outcome_service`) · `serializer.py` / `task_enrich.py` (trả `task_type_id`, `task_type_name`, giờ, `outcome`) ·
`core/all_models.py` · `app/main.py` (router task-types) · `core/code_sets.py` nếu cần import.
Sửa FE (vùng Agent 3 — phối hợp): `modules/work/types/work.ts` · `components/task-detail-sheet.tsx` (tách ô mới ra `components/task-effort-fields.tsx` + `task-outcome-box.tsx` vì sheet đã 300 dòng) ·
`utils/list-columns.ts` · `config/task-filter-fields.ts` · `hooks/use-work-board.ts` · `api/*` · tạo `hooks/use-task-types.ts`, `pages/task-type-catalog-page.tsx`.

## Implementation steps
1. Enum + bảng + cột + migration viết tay (nối head hiện hành; tất cả nullable/default → không khóa bảng lâu).
2. CRUD danh mục + API outcome + mở rộng `update_task`; audit mọi thay đổi.
3. Trả trường mới ở serializer; `plan_service` chấp nhận `task_type_id`/`estimate_hours` (hợp đồng cho A2 Agent 4).
4. FE: ô nhập + hộp đánh giá + cột/bộ lọc + màn danh mục.
5. Seed local vài loại việc mẫu (chỉ `seed.py`, không `seed_prod.py`).

## Todo
- [x] enum + model + migration (`core/capability_codes.py` · `task_type_model.py` · `d1cap01`)
- [x] CRUD loại việc (`task_type_service/controller`; list trả `{total, items}` để dùng `CrudListPage`)
- [x] cập nhật task + outcome (`task_outcome_service`; mở lại khi REWORK)
- [x] serializer + plan_service (`_effort_kwargs`: rác thì bỏ qua)
- [x] FE sheet (`task-effort-fields`, `task-outcome-box`) + danh mục (`task-type-crud`, route `/project/task-types`) + bộ lọc theo loại việc
- [ ] **Hoãn:** cột «Loại việc» trong khung nhìn Danh sách — cần thêm khóa dựng sẵn vào `BUILTIN_CARD_FIELDS` và 3 nơi vẽ (thẻ, dòng danh sách, Gantt), đổi bố cục đã nhớ của mọi người dùng; để dành khi đại ca duyệt
- [x] seed local (`seed.py::seed_work_task_types`, 4 loại; không có trong `seed_prod.py`)

**Lệch so với kế hoạch (có chủ ý):** tên migration/tệp test; `GET /task-types` trả `{total, items}` có phân trang (thay vì mảng) cho khớp `CrudListPage`;
hộp đánh giá hiện cả khi việc đang làm lại (chỉ nhãn); `0` giờ = xóa giờ; ba migration D1 gộp một (`d1cap01`).

## Tests
Backend `test/backend/test_loai_viec_task_cr656.py` (21 bài): tạo/sửa loại việc (quyền `setting.write`, 403 khi không có); `(company_id, code)` trùng → 409/422;
cập nhật task giờ âm/ > 999 → 422; `actual_hours` khi OPEN → 422; outcome REWORK → task về OPEN, `completed_at` NULL, audit ghi; outcome PASSED khi chưa DONE → 422;
người không phải người tạo/quản lý list đặt outcome → 403; danh mục `work_task_outcome` đăng ký đúng.
Vitest `src/modules/work`: `task-effort-fields.test.tsx` (9 bài), `task-outcome-box.test.tsx` (6 bài), thêm 1 bài lọc loại việc ở `task-conditions.test.ts`.

## Success criteria
- Tạo task chọn loại «Báo giá NCC», ước 4 giờ → xong nhập thực tế 6 giờ → đánh giá «Đạt»; dữ liệu đọc được ở D1a.
- Task cũ không đổi hành vi (cột mới mặc định 0/NULL); `sync_task_journal.py` chạy như cũ.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Không ai nhập giờ thực tế → dữ liệu thưa | Cao × TB | D1a dùng thời gian trôi qua làm chỉ số chính; giờ thực tế là phụ; nhắc nhẹ ở hộp xong |
| Xung đột với Agent 3 trên `modules/work/**` FE | TB × TB | Lead giao FE cho Agent 3 hoặc khóa tệp; BE làm độc lập |
| `task_service.py` phình | Cao × Thấp | Logic mới vào tệp mới |

## Security
Danh mục: ghi chỉ `setting.write`. Outcome: người tạo task hoặc quản lý list (dùng lại `get_task_or_403`/`CAN_EDIT`). Giờ/outcome không phải dữ liệu nhạy cảm nhưng thống kê theo người ở D1d gác khóa 16.

## Rollback
Downgrade drop cột + bảng (dữ liệu nhập tay mất — chỉ làm nếu chưa ai nhập). FE ẩn ô là đủ để tạm dừng.

## Next steps
D1a đọc `task_type_id`, `estimate_hours`, `actual_hours`, `outcome`; A2 (Agent 4) đặt các trường này khi tạo task từ kế hoạch.
