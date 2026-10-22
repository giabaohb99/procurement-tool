# Phase 01 — D0a: Sự kiện «Bấm chức năng» (`UI_ACTION`)

## Context links
- `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §5 (UI_ACTION, mã cố định, không chữ gõ)
- Nền: `backend/app/modules/usage_profile/telemetry_{schema,service,controller}.py`, `model.py` (`UiEvent`)
- FE: `frontend-v2/src/core/telemetry/telemetry-queue.ts`, `ui-event-codes.ts`
- Review cũ: `plans/reports/code-reviewer-261019-cr641-review.md` (scrub, 30 lô/phút, 64 KB)

## Overview
- Ưu tiên P1 · Ước **1,5 ngày** (BE 0,5 · FE 1) · Status: implemented (duoc-CR-654); gate xanh (vitest 418 tệp)
- Thêm loại sự kiện thứ 8 `UI_ACTION` + danh mục mã nút `UiAction`. Gắn ở **component dùng chung** để một chỗ sửa phủ nhiều màn.

## Key insights
- Wire hiện tại không có chỗ cho mã nút; `meta` JSON chỉ dành CLIENT_ERROR → thêm **trường số** `action` (không dùng meta: R2 + truy vấn được).
- `DataTable` không có sẵn xuất/in/sao chép; các nút đó nằm ở trang. Chỗ gắn chung được: menu cột, sắp xếp, phân trang,
  làm mới, nút xóa lọc (`data-table/`), áp/xóa bộ lọc (`conditional-filter/`), `ReportExportButton`, `BulkDeleteButton`, nút tạo mới `CrudListPage`.
- **Không có duyệt hàng loạt** trong code hiện nay → KHÔNG cấp mã trước (mã có trong danh mục mà không gắn sẽ hiện «không ai dùng» sai ở báo cáo D0c). Cấp khi tính năng ra đời.
- `daily_ui.ui_columns` bỏ qua loại lạ (chuỗi `elif`) → thêm loại 8 không làm hỏng gom ngày hiện tại.
- Công tắc `usage_tracking_enabled` đang TẮT trên prod từ 20/10 (doc 22 §6) → dữ liệu chỉ có khi đại ca bật sau khi thông báo nhân viên.

## Requirements
- Chức năng: ghi `(user, route mẫu, mã nút, thời điểm)`; mã cố định; không chữ người dùng gõ, không id bản ghi.
- Phi chức năng: không làm render lại (queue không phải state React); không vượt 30 lô/phút; không spam.

## Architecture
**Mã (BE, nguồn duy nhất)** — tệp mới `backend/app/core/ui_action_codes.py` (giữ `usage_codes.py` < 200 dòng), thuần stdlib,
`register(... keyed=True)` để sinh hằng TS `UI_ACTION_CODE`. Cấp số theo **khối** (số đã cấp không đổi/không tái dùng):

| Khối | Mã (tên IntEnum = nhãn) |
|---|---|
| 1–19 Bảng | 1 COLUMN_TOGGLE «Ẩn/hiện cột» · 2 COLUMN_PIN «Ghim cột» · 3 COLUMN_COLOR «Tô màu cột» · 4 LAYOUT_RESET «Khôi phục bố cục» · 5 SORT_CHANGE «Sắp xếp» · 6 PAGE_CHANGE «Chuyển trang» · 7 PAGE_SIZE_CHANGE «Đổi số dòng/trang» · 8 REFRESH «Làm mới» · 9 SELECT_ALL_PAGE «Chọn cả trang» |
| 20–39 Lọc | 20 FILTER_APPLY «Áp bộ lọc» · 21 FILTER_RESET «Xóa bộ lọc» · 22 FILTER_ROW_ADD «Thêm điều kiện lọc» · 23 QUICK_FILTER «Lọc nhanh» |
| 100–119 Xuất/In | 100 EXPORT_EXCEL «Xuất Excel» · 101 PRINT «In» · 102 REPORT_EXPORT «Xuất báo cáo» |
| 200–219 Phiếu/dòng | 200 COPY_DOCUMENT «Nhân bản phiếu» · 201 COPY_LINE «Sao chép dòng» · 202 BULK_DELETE_LINES «Xóa nhiều dòng» · 203 CREATE_NEW «Tạo mới từ danh sách» |
| 300–319 Duyệt | (để trống — cấp khi có duyệt hàng loạt) |
| 400–419 Dự án | 400 KANBAN_DRAG «Kéo thẻ kanban» (gắn ở phase 05 nếu Agent 3 đồng ý; không thì để trống) |

**Wire** — `UiEventIn.action: int = 0`; validator: `type == UI_ACTION` ⇔ `action ∈ UiAction`; loại khác buộc `action == 0`.
**DB** — `tab_ui_event.action_key SMALLINT NOT NULL DEFAULT 0` (không index: gom ngày quét theo `occurred_at`).
**Chống spam (FE)** — hàm `trackUiAction(code)` trong `core/telemetry/track-ui-action.ts`:
1. bỏ trùng: cùng `(code, route)` trong **2 giây** → bỏ (bấm đúp);
2. mã «lắm lời» (`SORT_CHANGE, PAGE_CHANGE, PAGE_SIZE_CHANGE, COLUMN_TOGGLE, COLUMN_COLOR`) gộp cửa sổ **10 giây** theo `(code, route)`;
3. trần **30 UI_ACTION/phút/tab** (cửa sổ trượt), vượt thì bỏ im lặng.
Với nhịp gửi 30 s, ≤ 100 sự kiện/lô → ~2 lô/phút, xa trần 30 lô/phút. **Chống spam (BE)** — trong `build_rows`, mỗi lô giữ tối đa
**60** sự kiện UI_ACTION, phần thừa bỏ (không từ chối cả lô, không 422).
**Luồng:** nút → `trackUiAction(UI_ACTION_CODE.X)` → `telemetry.enqueue({type: UI_EVENT.UI_ACTION, route: getCurrentRoute(), action})` → lô → `tab_ui_event`.

## Related code files
Sửa (BE): `backend/app/core/code_sets.py` (import module mã mới) · `backend/app/core/usage_codes.py` (thêm `UI_ACTION = 8` + nhãn) ·
`backend/app/modules/usage_profile/model.py` (cột `action_key`) · `telemetry_schema.py` (trường + validator) · `telemetry_service.py` (map cột + trần 60).
Tạo (BE): `backend/app/core/ui_action_codes.py` · `backend/migrations/versions/d0uiact01_su_kien_bam_chuc_nang.py` (tên gợi ý).
Sinh lại: `frontend-v2/src/shared/constants/statuses.ts` (`python backend/scripts/gen_status_ts.py`).
Sửa (FE): `core/telemetry/telemetry-queue.ts` (trường `action` trong `UiEventInput`/`toWire`) · `ui-event-codes.ts` (re-export `UI_ACTION_CODE`) ·
`shared/data-table/data-table.tsx` (toggleColumn/togglePin/setColumnColor/resetLayout/sort/refresh/pagination) · `shared/data-table/filter-reset-button.tsx` ·
`shared/conditional-filter/provider/filter-provider.tsx` (`apply`, `reset`) · `shared/conditional-filter/ui/filter-footer.tsx` (addRow) ·
`shared/crud/crud-list-page.tsx` (create, quick filter) · `modules/report/components/report-export-button.tsx` (**chờ CR-651 gộp**) ·
`shared/ui/bulk-delete-button.tsx` · 4 nút `exportExcel()` trang: `finance/pages/payment-request-list-page.tsx`, `document/components/outgoing-documents-tab.tsx`,
`procurement/pages/purchase-report-page.tsx`, `procurement/pages/customs-price-page.tsx` · nút In mở trang in (8 tệp liệt kê trong research: `*-detail-page.tsx` / `seal-request-more-menu.tsx`) ·
sao chép phiếu: `purchase-request-detail-page.tsx`, `purchase-request-list-page.tsx`, `purchase-order-detail-page.tsx`, `survey-list-page.tsx`, `survey-request-list-page.tsx`, `document/components/document-copy-action.tsx`, `seal-request-more-menu.tsx` ·
sao chép dòng: `survey-request-lines-table.tsx`, `survey-lines-table.tsx`, `purchase-order-items-table.tsx`.
Tạo (FE): `core/telemetry/track-ui-action.ts` (+ `.test.ts`).
⚠️ Gắn In ở **nút bấm** (không ở `useEffect` trang in) — mở lại trang in không tính lần in thứ hai.

## Implementation steps
1. BE: tạo `ui_action_codes.py` (IntEnum + `UI_ACTION_LABELS` + `register(... keyed=True)`); import ở `code_sets.py`; thêm `UI_ACTION=8` vào `UiEventType` + nhãn «Bấm chức năng».
2. BE: cột `action_key` ở model + migration viết tay (inspect-guard như `usgprof01`, nối head hiện hành; downgrade drop cột).
3. BE: schema `action` + validator chéo; service ghi `action_key`, cắt 60 UI_ACTION/lô.
4. Chạy `gen_status_ts.py`, kiểm `statuses.ts` có `UI_ACTION_CODE`, `UI_EVENT_TYPE_CODE.UI_ACTION`.
5. FE: `track-ui-action.ts` (dedupe 2 s, gộp 10 s, trần 30/phút; đồng hồ tiêm được để test); thêm `action` vào wire.
6. FE: gắn các chỗ dùng chung trước (data-table, conditional-filter, crud), rồi nút trang (xuất/in/sao chép).
7. Chạy `npm run typecheck`, `npm run lint`, vitest `src/core/telemetry`, `src/shared/data-table`, `src/shared/conditional-filter`, `src/shared/crud`.

## Todo
- [x] `ui_action_codes.py` + đăng ký + `UI_ACTION=8`
- [x] migration `action_key`
- [x] schema/service + trần 60/lô
- [x] sinh `statuses.ts`
- [x] `track-ui-action.ts` + test
- [x] gắn data-table / conditional-filter / crud
- [x] gắn xuất / in / sao chép / xóa nhiều dòng
- [x] cập nhật `test_ho_so_lam_viec_ma_so_cr641.py` (bộ `UiEventType` có 8)

## Tests
- Backend `test/backend/test_bam_chuc_nang_d0.py` (đổi hậu tố theo CR lead cấp): nhận UI_ACTION hợp lệ → `action_key` đúng; UI_ACTION thiếu/mã lạ → 422; loại khác có `action≠0` → 422;
  lô 100 UI_ACTION → ghi 60; mã trong `UiAction` duy nhất, nhãn đủ; công tắc tắt → 204 không ghi.
- Vitest `core/telemetry/track-ui-action.test.ts`: bỏ trùng 2 s; gộp 10 s cho mã lắm lời; trần 30/phút; tắt queue thì không enqueue; payload không có chuỗi tự do.
- Vitest `shared/data-table/data-table-ui-action.test.tsx`: ẩn cột / sắp xếp / chuyển trang gọi `trackUiAction` đúng mã; `conditional-filter` áp/xóa.

## Success criteria
- Bấm «Ẩn cột» trên 1 màn danh sách bất kỳ dùng `DataTable` → 1 dòng `tab_ui_event(event_type=8, action_key=1, route_pattern=/...)` sau ≤ 30 s.
- Bấm đúp nhanh → vẫn 1 dòng. Không có trường chuỗi tự do nào trong body (test khẳng định keys của `toWire`).
- typecheck + lint 0 lỗi; test BE/FE xanh.

## Risk assessment
| Rủi ro | Khả năng × Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Gắn sai chỗ → đếm cả thao tác tự động (vd đồng bộ URL gọi `apply`) | TB × TB | Gắn ở handler người bấm (`filter-footer`/nút), không ở hàm đồng bộ URL; test riêng |
| Spam lô vượt 30/phút → 429, mất sự kiện | Thấp × Thấp | Trần FE + gộp + trần BE 60/lô |
| Xung đột tệp với CR-651 (`report-export-button.tsx`) | TB × Thấp | Gắn tệp đó sau khi CR-651 gộp |
| Trang in gọi `window.print` ở nhiều nơi | TB × Thấp | Gắn ở nút mở trang in; ghi danh sách nút trong test |

## Security
- `user_id` từ token; route chuẩn hóa lại ở server (`normalize_route`) — id không lọt.
- Không thêm đường mới; giữ 64 KB, 30 lô/phút, công tắc.

## Rollback
Tắt `usage_tracking_enabled` → ngừng thu tức thì. Gỡ code FE độc lập; migration downgrade drop cột (dữ liệu thô 90 ngày, không phải chứng cứ).

## Next steps
Phase 02 (cùng tệp mã) → Phase 03 đọc `action_key`.
