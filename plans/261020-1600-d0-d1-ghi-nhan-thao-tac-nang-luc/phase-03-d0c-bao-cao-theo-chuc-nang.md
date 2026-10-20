# Phase 03 — D0c: Báo cáo theo chức năng (ReportKey 15 «Mức dùng chức năng»)

## Context links
- Lời đại ca: «chức năng nào nhiều người dùng, chức năng nào không ai dùng, chỗ nào hay bỏ dở hay lỗi … biết nhân sự vướng ở đâu mà sửa»
- `doc/erp/22-ai-ke-hoach-phan-viec.md` §5 (báo cáo theo chức năng đặt cạnh báo cáo theo người), §6 (chỉ quản trị)
- Lớp gác thứ ba: `backend/app/modules/report_access/guard.py`, `seed_defaults.ensure_report_access_defaults` (tự cấp admin cho khóa mới)
- Mẫu controller gác kép: `backend/app/modules/usage_profile/controller.py`
- Memory: «API báo cáo phải nhanh nhất», «Gác điều hướng mặc định MỞ»

## Overview
- P1 · **1,5 ngày** (BE 0,8 · FE 0,7) · **implemented (duoc-CR-655, 20/10/2026)** · cần phase 01–02 và **CR-651 đã gộp** (đụng `modules/report/**`).
- Bảng gom ngày theo chức năng + 3 đường API + 1 trang báo cáo, gác ReportKey **15** mới.

## Key insights
- Gom trực tiếp từ `tab_ui_event` thô lúc xem báo cáo thì chậm (~50k dòng/ngày, chỉ giữ 90 ngày) → cần **bảng gom ngày** riêng, giữ 3 năm như `tab_usage_daily`.
- Cần đếm **số người khác nhau trong cả kỳ** → bảng phải giữ mức `user × ngày × chức năng` (không gom mất user).
- Đặt ở **module mới `feature_usage/`** + task celery riêng 04:45 (sau `usage.aggregate_daily` 04:30) → không sửa builder của `usage_profile` (CR-651 đang làm).
- Lỗi API: `tab_request_log(route, http_status)` theo đường API, không ánh xạ được về màn → hiện riêng «đường API hay lỗi».
- «Không ai dùng»: mã `UiAction`/`UiForm` lấy từ enum (không truy vấn); màn chưa ai mở → FE so mục menu (module registry) với route đã thấy.

### Vì sao ReportKey 15 riêng (không dùng 14)
Số liệu ở đây là **gom theo chức năng**, không phải hồ sơ hành vi từng người. Khóa riêng cho phép đại ca sau này mở cho
BA/người phụ trách sản phẩm mà **không** mở hồ sơ cá nhân (khóa 14). Mặc định vẫn chỉ admin (`ensure_report_access_defaults`).

## Requirements
- Danh sách chức năng: số người dùng, % người dùng trên số người hoạt động, số lần, bỏ dở (form), lỗi; lọc kỳ, pháp nhân, phòng ban, loại.
- Tab «Không ai dùng» trong kỳ. Chi tiết một chức năng: theo màn + theo phòng ban (không theo từng người — Q7).
- Xuất Excel. Tốc độ: ≤ 3 truy vấn/đường, < 500 ms với kỳ 90 ngày trên dữ liệu 100 người.

## Architecture
**Mã** (`backend/app/core/usage_codes.py` hoặc `ui_action_codes.py`): `FeatureKind` IntEnum — 1 ACTION · 2 FORM · 3 SCREEN · 4 SEARCH · 5 CLIENT_ERROR · 6 API_ERROR; đăng ký code set `feature_kind`.
**Bảng `tab_feature_usage_daily`** (module `feature_usage/model.py`, không AuditMixin):
`id BIGINT PK · day DATE · user_id BIGINT · company_id BIGINT · department_id BIGINT · kind SMALLINT · code SMALLINT (UiAction / UiForm / HTTP 403·422·500 / 0) ·
route VARCHAR(200) · uses INT · completes INT · abandons INT · fails INT · duration_ms BIGINT`
UNIQUE `(day, user_id, kind, code, route)` · INDEX `ix_feature_daily_day_kind (day, kind)`.
Nghĩa cột theo loại: FORM uses=mở, completes=gửi, abandons=bỏ · SCREEN uses=lượt xem, duration=dwell · SEARCH uses=lượt, fails=0 kết quả ·
ACTION uses=lượt bấm · CLIENT_ERROR uses=số lỗi · API_ERROR uses=số lỗi, code=403/422/500 (5xx gộp 500).
**Builder** `feature_usage/daily_builder.py`: cho ngày VN `D` (dùng `vn_day_bounds`): 1 truy vấn GROUP BY trên `tab_ui_event`
(user, event_type, action_key, form_key, route_pattern) + 1 truy vấn GROUP BY trên `tab_request_log` (user_id>0, route, lớp status) + 1 truy vấn org từ
`tab_usage_daily` ngày D → xóa dòng ngày D rồi INSERT nhiều dòng (idempotent). Backfill: `scripts/backfill_feature_usage.py --days 90`.
**API** `feature_usage/controller.py`, `prefix=/api/feature-usage`, mọi đường `dependencies=[Depends(require_report(ReportKey.FEATURE_USAGE))]` + `require("setting","read"|"export")`:
- `GET /summary` — Q1: `SELECT kind, code, route, COUNT(DISTINCT user_id), SUM(uses), SUM(completes), SUM(abandons), SUM(fails) … WHERE day BETWEEN … [org] GROUP BY kind, code, route`;
  Q2: `COUNT(DISTINCT user_id) FROM tab_usage_daily WHERE active=1 AND day BETWEEN …` (mẫu số %); `unused` tính từ enum. Phân trang trong Python (vài trăm dòng).
- `GET /summary/export` — cùng service, xuất xlsx bằng `core/export_xlsx`.
- `GET /breakdown?kind&code&route` — Q1 theo `department_id`, Q2 theo `route` (cho ACTION dùng nhiều màn).
**FE** trang `modules/report/pages/feature-usage-report-page.tsx` 4 tab: Chức năng · Biểu mẫu (tỷ lệ bỏ dở) · Màn hình (kèm «chưa ai mở») · Lỗi (lỗi giao diện theo màn + API 403/422/5xx theo đường).

## Related code files
Tạo BE: `backend/app/modules/feature_usage/{__init__,model,daily_builder,service,export,controller,tasks}.py` (mỗi tệp < 200 dòng) ·
`backend/scripts/backfill_feature_usage.py` · migration `d0feat01_bang_gom_chuc_nang.py`.
Sửa BE: `core/report_keys.py` (`FEATURE_USAGE = 15`, nhãn «Mức dùng chức năng», nhóm «Quản trị») · `core/usage_codes.py` (`FeatureKind`) ·
`core/all_models.py` · `app/main.py` (router) · `core/celery_app.py` (include + beat `feature-usage-daily` 04:45, dọn 3 năm 04:25).
Sinh lại `statuses.ts`.
Tạo FE: `modules/report/pages/feature-usage-report-page.tsx` · `modules/report/components/feature-usage/{feature-usage-columns,feature-usage-tabs,feature-usage-breakdown-sheet}.tsx` ·
`modules/report/api/feature-usage-api.ts` · `modules/report/hooks/use-feature-usage.ts` · `modules/report/utils/feature-usage-unused-screens.ts` · `modules/report/types/feature-usage.ts`.
Sửa FE: `modules/report/config/report-catalog-system.ts` (key 15, entity `setting`, `sourcePath: appRoutes.system.logs`) · `modules/report/routes.tsx` + nav (`reportKeys: [15]`, mục Tổng quan thêm 15) ·
`shared/constants/app-routes.ts` (`report.featureUsage`) · `shared/constants/query-keys.ts`.
Sửa test cũ: `test/backend/test_ho_so_lam_viec_ma_so_cr641.py` (`max(ReportKey)` 14 → giá trị mới).

## Implementation steps
1. `FeatureKind` + `ReportKey.FEATURE_USAGE=15` + REPORT_META; sinh TS.
2. Model + migration viết tay (bảng + unique + index; nối head hiện hành).
3. Builder thuần (hàm nhận rows → dict) + hàm ghi; task celery + beat; task dọn 3 năm (dùng lại `purge_in_batches` — import từ `usage_profile.tasks_cleanup`, không sao chép).
4. Service + controller + export; khai `/summary`, `/summary/export` trước `/breakdown`.
5. Backfill 90 ngày trên dev; đo thời gian `/summary` kỳ 90 ngày.
6. FE: catalog + route + nav + trang 4 tab dùng `DataTable`; «chưa ai mở» so menu.
7. Gate FE: chạy typecheck, lint, vitest `src/modules/report`.

## Kết quả triển khai (duoc-CR-655)
Lệch so với bản kế hoạch (đều có lý do):
- Bỏ loại `API_ERROR` (lỗi 403/422/5xx theo đường API): `FeatureKind` chỉ còn 5 loại (ACTION·FORM·SCREEN·SEARCH·CLIENT_ERROR); lỗi API theo đường đã có ở nhật ký hệ thống, không ánh xạ được về màn. Builder chỉ đọc `tab_ui_event` (+ phòng ban từ `tab_usage_daily`) = 2 truy vấn nguồn.
- Task celery `feature_usage.aggregate_daily` 04:45 kiêm luôn dọn 3 năm (không tách beat riêng 04:25).
- Chi tiết một chức năng mở bằng Sheet (theo phòng ban + theo màn), không có đường theo từng người.
- Migration `d0feat01` (nối `d0merge01`). `/summary` = 3 truy vấn, `/breakdown` = 2 (test đếm truy vấn); đo trên DB dev 89 ngày: 10 ms.
- Tab «Lỗi» gộp cả «Tìm kiếm»; «Không ai dùng» = mã chưa thấy (BE) + mục menu chưa ai mở (FE, `feature-usage-unused-screens.ts`); kỳ rỗng thì ẩn các khẳng định «chưa ai dùng».

## Todo
- [x] mã + ReportKey 15 + sinh TS
- [x] bảng + migration
- [x] builder + task + beat + dọn
- [x] API 3 đường + xuất Excel
- [x] backfill script
- [x] trang FE + catalog + nav
- [x] sửa test cứng số 14

## Tests
Backend `test/backend/test_bao_cao_chuc_nang_d0.py`:
- builder: 1 ngày có PAGE_VIEW/UI_ACTION/FORM_*/SEARCH/CLIENT_ERROR + request_log 422/500 → đúng số dòng/cột; chạy 2 lần không nhân đôi.
- `/summary`: `COUNT(DISTINCT user)` qua nhiều ngày đúng; `unused` chứa mã chưa ai bấm; lọc phòng ban.
- **đếm truy vấn** (`sqlalchemy event before_cursor_execute`): `/summary` ≤ 3, `/breakdown` ≤ 2, bất kể số dòng.
- gác: thiếu ReportKey 15 → 403; có `setting.read` nhưng chưa gán khóa → 403; admin → 200; `/summary/export` gác `setting.export`.
- route soi `app.routes`: cả 2 đường mang `report_key=15` (test sẵn có sẽ bắt).
Vitest: `report-catalog.test.ts` (đã có — tự kiểm key 15 khớp backend, nav, Tổng quan); `feature-usage-unused-screens.test.ts`; `feature-usage-report-page.test.tsx` (render 4 tab, rỗng → thông báo «chưa bật thu thập»).

## Success criteria
- Đại ca mở «Mức dùng chức năng», thấy top chức năng, tab «Không ai dùng», tab «Biểu mẫu» có tỷ lệ bỏ dở 13 form, tab «Lỗi».
- `/summary` 90 ngày < 500 ms trên bản sao dữ liệu dev; test đếm truy vấn xanh.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Công tắc thu đang tắt trên prod → báo cáo rỗng | Cao × TB | Trang hiện banner «chưa bật thu thập từ …»; Q1 cho đại ca quyết bật |
| Phình bảng (user×ngày×route) | TB × Thấp | ~750k dòng/năm; index (day, kind); giữ 3 năm; dọn theo lô |
| Xung đột CR-651 ở `modules/report/**` | Cao × TB | Chỉ làm FE sau khi CR-651 gộp; BE làm trước được |
| Test cũ ghi cứng 14 khóa | Cao × Thấp | Sửa trong cùng phase |

## Security
Chỉ admin mặc định (khóa 15 + `setting`). Không có tên người ở `/summary`; `/breakdown` chỉ theo phòng ban. Mỗi lần xem để lại `tab_request_log`.
Excel: tiêu đề cột cố định, không đưa chuỗi người dùng vào ô (chống chèn công thức).

## Rollback
Gỡ beat + router; migration downgrade drop bảng. Khóa 15 đã cấp **không tái dùng**; dòng `tab_report_access` của nó thu hồi bằng `revoked_at`.

## Next steps
Phase 04 thêm nhóm AI vào hồ sơ. Sau T1: cân nhắc mở khóa 15 cho người phụ trách sản phẩm.
