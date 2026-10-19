# Frontend duoc-CR-641 (ex CR-635) — phase 06 bộ thu sự kiện + phase 07 màn admin hồ sơ

Status: DONE_WITH_CONCERNS. Chưa commit. Không đụng backend, change-log, nhat-ky-task, modules/document.

## Files

Tạo (`frontend-v2/src/`):
- `core/telemetry/`: `ui-event-codes.ts`, `route-pattern.ts`, `dwell-timer.ts`, `telemetry-queue.ts`, `use-route-telemetry.ts`, `route-telemetry.tsx`, `use-form-telemetry.ts`, `use-search-telemetry.ts`, `install-global-error-capture.ts` + 7 test cạnh tệp (44 bài).
- `modules/report/`: `config/report-catalog-system.ts`, `config/usage-metric-labels.ts`, `config/usage-style-hints.ts`, `types/usage-profile.ts`, `api/usage-profile-api.ts`, `hooks/use-usage-profile-list.ts`, `hooks/use-usage-profile.ts`, `utils/usage-format.ts`, `utils/usage-route-label.ts`, `utils/usage-profile-helpers.ts`, `pages/usage-profile-list-page.tsx`, `pages/usage-profile-detail-page.tsx`, `components/usage-profile/*` (14 tệp: notice-banner, header-card, metric-with-cohort, metric-grid, section-card, rhythm, hour-weekday-heatmap, day-strip, screens, task, response, proficiency, security, style-labels, filters, columns) + test.

Sửa: `core/telemetry/logger.ts` (error -> CLIENT_ERROR, try/catch), `core/auth/auth-types.ts` (`usage_tracking?`), `core/config/env.ts` (`isTest`), `app/router/protected-route.tsx` (gắn `<RouteTelemetry/>`), `modules/report/config/report-catalog.ts`, `modules/report/routes.tsx` (route chi tiết), `shared/constants/app-routes.ts`, `shared/constants/query-keys.ts`, `modules/system/components/report-access-tab.tsx` (bỏ số cứng 13, chỉ comment), `modules/report/components/report-export-button.tsx` + `api/report-analytics-api.ts` (nới kiểu params cho phép mảng, tương thích ngược).

Móc 6 form (`useFormTelemetry` + `markSubmitted()` sau khi lưu): purchase-request / survey-request / purchase-order detail, leave-request detail, labor-contract-form-dialog, employee-form-dialog.
Móc 5/6 tìm kiếm (`useSearchTelemetry`): purchase-request / survey-request / purchase-order list, employee-list, `shared/crud/crud-list-page`.
BỎ QUA: `document/hooks/use-document-search.ts` (thuộc modules/document, CR-634).

## Xác nhận 3 điểm user lo (lag / rò bộ nhớ)
1. Không có listener theo sự kiện/theo render. `visibilitychange` + `pagehide` toàn cục cài MỘT lần (`installTelemetryLifecycle`, cờ `lifecycleInstalled`); `error`/`unhandledrejection` cài một lần. Hook: `useRouteTelemetry` effect `[]` gỡ `visibilitychange` + hook pagehide khi unmount; `useFormTelemetry` đăng ký hook pagehide trong effect và gỡ ở cleanup. Interval 30 s chỉ có khi bật, `clearInterval` khi tắt. Bộ đệm trần 300, tắt thu thập thì xóa sạch. Set dedup lỗi tối đa 20 phần tử.
2. `enqueue` là O(1): chỉ `push` + `slice` khi vượt trần, KHÔNG `JSON.stringify`. JSON dựng đúng một lần/sự kiện lúc gửi (30 s/lần hoặc rời trang), tái dùng chuỗi đó cho thân yêu cầu. Không state React trong bộ thu.
3. Không có sự kiện theo phím hay theo click. Chỉ 7 loại: đổi route (PAGE_VIEW/LEAVE), mở/gửi/bỏ form (6 form), SEARCH khi kết quả của từ khóa mới về (đã debounce sẵn, 1 sự kiện/từ khóa, từ khóa không rời hook), CLIENT_ERROR (<= 20/lần nạp).

## Sửa theo yêu cầu điều phối: trần keepalive 64 KB
`flush(true)` chỉ bắn các lô cộng dồn <= 60 KB (`MAX_KEEPALIVE_TOTAL_BYTES`; lô đầu luôn bắn vì đã <= 60 KB). Phần còn lại GIỮ trong bộ đệm (tab chỉ ẩn thì gửi nhịp sau; trang đóng thì mất — cố ý, ghi trong comment). Test: 200 sự kiện lỗi dài -> 1 lần fetch, thân <= 60 KB, còn dư trong bộ đệm. Sự kiện 401 vẫn trả về bộ đệm; 204/413/5xx/mạng nuốt im.

## Giả định về hợp đồng API (phase 05/03 chưa chốt hình dạng JSON)
- `POST /api/telemetry/ui-events` đúng phase 03: `{events:[{type,route,form,duration_ms,result_count,age_ms,tab_key,error}]}`; 204 hoặc `data.accepted===0` -> dừng gửi tới khi nạp lại trang.
- Gate bật: `user && user.usage_tracking !== false && !env.isTest` (thiếu trường = BẬT, theo "mặc định bật").
- List `GET /api/usage-profiles/summary`: tham số `preset` (mặc định `last_30_days`), custom gửi CẢ `date_from/date_to` và `from/to` (phase 05 viết `from&to`, các /summary khác dùng date_*); `company_id`, `department_id`, `role_id`, `q`, `page`, `page_size`; `label` là MẢNG lặp khóa (`label=2&label=5`). Response `{items[], total, period{date_from,date_to}, data_since}`; dòng: user_id, full_name, emp_code, department_name, cohort_name, active_days, workdays_net, active_ratio, api_writes, docs_created, approvals, exports, http_422_per_100_writes, labels[] (mã số), last_active_day.
- Chi tiết `GET /api/usage-profiles/{id}?weeks=`: `subject`, `latest` (= `{period, context, cohort{kind,size,name}, metrics{key:{v,med,trend[]}}, lists{top_paths,first_screen_mode,docs{entity:{c,s,a,r,ret}}}, unmeasured{key:code}, labels[{code,score,evidence[]}]}` theo khuôn snapshot phase 04), `weekly[]` (chưa dùng), `daily[{day,active,is_workday,is_holiday?,leave_days,...}]`, `heatmap` 7x24 (thứ Hai đầu), `screens[{route,views,dwell_ms,api_calls,source?}]`, `metric_meta{key:{label?}}` (nhãn backend ghi đè nhãn FE). Mọi trường ngoài định danh coi là tùy chọn.
- Xuất: `/api/usage-profiles/summary/export` cùng tham số; nút dùng `ReportExportButton` nên cần `can('setting','export')` ở FE (backend chỉ gác setting.read).

## Lệch plan (có chủ ý)
- Cài bắt lỗi toàn cục không sửa `app/bootstrap/app.tsx`: cài trong `RouteTelemetry` (chỉ sau đăng nhập, mới có gì để gửi) — ít chạm tệp hơn.
- Nhãn kiểu làm việc và lý do "chưa đo được" lấy từ `USAGE_STYLE` / `USAGE_UNMEASURED_REASON` trong `statuses.ts` (backend đã sinh); chỉ bảng gợi ý §4 chép tay (tầng hiển thị) và có test canh khớp mã. Mã sự kiện/form viết tay trong `ui-event-codes.ts` (gửi số) + test so với `UI_EVENT_TYPE`/`UI_FORM` sinh.
- `weekly[]` chưa vẽ biểu đồ xu hướng riêng (xu hướng 4 tuần đã hiện bằng mũi tên cạnh từng chỉ số); "cột nhóm" cạnh từng số làm ở thẻ chỉ số, bảng theo loại phiếu không có cột nhóm (không có trung vị theo loại).
- Kỳ mặc định: 30 ngày qua (không có preset "4 tuần"). Thanh chọn kỳ vẫn hiện nút so sánh (không dùng).

## Kiểm
- Gác route (`usage-profile-gating.test.ts`): chi tiết `/report/usage-profiles/5` bị chặn khi chỉ có khóa 1..13 hoặc thiếu `setting.read`; mở khi có khóa 14.
- vitest xanh: `src/core` + `src/modules/report` + `src/modules/system` + `src/modules/hr` + `src/shared/crud` (139 file/1452 bài lần chạy đầu, chạy lại telemetry+report/utils sau sửa keepalive: 132 bài xanh). `report-catalog.test.ts` xanh với khóa 14 (backend đã sinh `statuses.ts`).
- `src/modules/procurement` + `src/app`: 108/110 file xanh; lỗi duy nhất `purchase-request-items-table.test.tsx` timeout 5 s (bài "xóa nhiều dòng", tệp không đụng tới — nghi chậm do máy tải, chưa chạy lại riêng).
- Lint toàn cây: 0 lỗi, 29 cảnh báo (cũ, không có cảnh báo ở tệp mới/sửa).
- Typecheck: sạch khi tôi chạy trước đó; lần chạy cuối có 1 lỗi TS2345 ở `modules/document/pages/document-detail-page.tsx` (agent CR-634 đang sửa dở, ngoài quyền sở hữu của tôi).
- Chưa thử trên trình duyệt thật (giao diện hồ sơ chỉ kiểm bằng test, vì backend phase 05 chưa chạy).

## Mở
1. Hình dạng JSON chi tiết hồ sơ ở trên là suy từ phase 04/05 — cần đối chiếu với `usage_profile/schema.py` khi backend xong (đặc biệt `heatmap`, `screens[].source`, `lists.first_screen_mode`, `cohort.name`).
2. Tên tham số kỳ (`date_from` vs `from`) — đã gửi cả hai, nên chốt một.
3. Nút xuất cần `setting.export` ở FE; nếu muốn admin tùy chỉnh chỉ cần `setting.read` thì đổi sang nút riêng.
4. Móc tìm kiếm ở `document/hooks/use-document-search.ts` chờ CR-634 xong.

**Status:** DONE_WITH_CONCERNS
**Summary:** Bộ thu `core/telemetry` + 6 móc form + 5 móc tìm kiếm + 2 màn Báo cáo (danh sách, hồ sơ 9 khối) hoàn tất, test/lint xanh.
**Concerns:** hợp đồng JSON chi tiết hồ sơ là giả định; typecheck hiện đỏ 1 lỗi do CR-634 (modules/document); 1 bài procurement timeout (không liên quan).
