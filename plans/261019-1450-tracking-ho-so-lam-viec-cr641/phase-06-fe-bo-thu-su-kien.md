# Phase 06 — FE bộ thu sự kiện (`core/telemetry`) + móc form / tìm kiếm

**Ưu tiên:** P2 · **Effort:** 6h · **Phụ thuộc:** hợp đồng API của 03 (code song song được) · **Trạng thái:** pending

## Ngữ cảnh
- `src/core/telemetry/logger.ts` chỉ in console — đổi `error` để đẩy thêm sự kiện CLIENT_ERROR.
- Token: `src/core/api/token-storage.ts`; header `Authorization: Bearer` (`http-client.ts`). Không cookie → không dùng `sendBeacon`; dùng `fetch(url, {method: 'POST', keepalive: true, headers})`.
- Route gốc đã đăng nhập: `src/app/router/protected-route.tsx` (mọi màn sau đăng nhập, kể cả trang in).
- Ô tìm kiếm ghi `?q=` qua `shared/hooks/use-url-search-param.ts`; `shared/crud/crud-list-page.tsx` phủ các màn danh mục.
- Rules: `frontend-v2/.claude/rules/*` (không barrel, test cạnh tệp, tên `it` tiếng Anh, mock ở `@/core/api` / `fetch`, múi giờ test cố định).
- Mã sự kiện/form sinh từ backend vào `statuses.ts` (phase 01) — FE KHÔNG viết tay danh sách nhãn.

## Thiết kế
```
core/telemetry/
  ui-event-codes.ts          UI_EVENT / UI_FORM dạng `as const` (số) + test khớp từng giá trị với UI_EVENT_TYPE / UI_FORM sinh ở statuses.ts
  route-pattern.ts           toRoutePattern(pathname, params): thay giá trị param bằng `:tên`, rồi lưới an toàn số/uuid → `:id`; bỏ search/hash; ≤ 120
  telemetry-queue.ts         enqueue(event) → bộ đệm (trần 300, tràn bỏ cũ nhất) · flush mỗi 30 s nếu có · flush keepalive khi
                             visibilitychange=hidden / pagehide · chia lô ≤ 100 sự kiện & ≤ 60 KB (trần keepalive 64 KB) ·
                             401 → giữ lại gửi nhịp sau · lỗi khác → bỏ lô · tắt hẳn khi `usage_tracking` false, chưa đăng nhập, hoặc env test
                             · `age_ms` = now − lúc enqueue (server tự đổi ra giờ)
  dwell-timer.ts             cộng dồn thời gian CHỈ khi tab đang hiện (visibility), dừng khi ẩn
  use-route-telemetry.ts     đổi location: PAGE_LEAVE (màn cũ, duration = dwell) rồi PAGE_VIEW (màn mới); pagehide → PAGE_LEAVE
  route-telemetry.tsx        <RouteTelemetry/> không vẽ gì, gắn 1 lần trong protected-route.tsx
  use-form-telemetry.ts      useFormTelemetry(form: UiFormCode, active: boolean) → { markSubmitted() }
                             active=true lúc gắn → FORM_OPEN; markSubmitted → FORM_SUBMIT(duration); unmount/pagehide khi chưa submit → FORM_ABANDON(duration)
  use-search-telemetry.ts    useSearchTelemetry(query: string, total: number | undefined, isFetching: boolean)
                             query rỗng → im; khi kết quả của query mới về → SEARCH{result_count: total}; trùng query liền trước → bỏ.
                             TỪ KHÓA KHÔNG BAO GIỜ rời hook (không hash, không độ dài).
  install-global-error-capture.ts  window 'error' + 'unhandledrejection' → CLIENT_ERROR; tối đa 20/lần nạp trang; trùng thông điệp → bỏ;
                             thông điệp cắt 200, thay chuỗi số ≥ 6 chữ số bằng `#` (tránh số điện thoại/CCCD)
```
`logger.error` gọi `enqueueClientError` (cờ chống đệ quy nếu chính hàng đợi lỗi).
`auth-types.ts` thêm `usage_tracking?: boolean`.

## Móc tối thiểu (opt-in, ~3 dòng mỗi chỗ)
| Form | Tệp | `active` |
|---|---|---|
| YCMH | `modules/procurement/pages/purchase-request-detail-page.tsx` | chế độ tạo mới |
| YCBG | `modules/procurement/pages/survey-request-detail-page.tsx` | tạo mới |
| ĐMH | `modules/procurement/pages/purchase-order-detail-page.tsx` | `isNew` |
| Đơn nghỉ phép | `modules/hr/pages/leave-request-detail-page.tsx` | `isNew` |
| HĐLĐ | `modules/hr/components/labor-contract-form-dialog.tsx` | dialog mở ở chế độ lập |
| Hồ sơ nhân sự | `modules/hr/components/employee-form-dialog.tsx` | dialog mở ở chế độ tạo |
`markSubmitted()` gọi trong `onSuccess` của mutation lưu.

Tìm kiếm: `shared/crud/crud-list-page.tsx` + `procurement/pages/{purchase-request,survey-request,purchase-order}-list-page.tsx`
+ `hr/pages/employee-list-page.tsx` + `document/hooks/use-document-search.ts`. Màn khác thêm dần sau (không chặn CR).

## Tệp
- Tạo: 9 tệp `core/telemetry/*` + test cạnh từng tệp có logic
- Sửa: `core/telemetry/logger.ts`, `core/auth/auth-types.ts`, `app/router/protected-route.tsx`, `app/bootstrap/app.tsx` (cài bắt lỗi toàn cục),
  6 tệp form + 6 tệp danh sách ở trên

## Todo
- [ ] ui-event-codes + test khớp statuses.ts
- [ ] route-pattern + test
- [ ] telemetry-queue + dwell-timer + test (fake timers, mock fetch)
- [ ] use-route-telemetry + RouteTelemetry gắn protected-route
- [ ] use-form-telemetry + 6 móc
- [ ] use-search-telemetry + 6 móc
- [ ] bắt lỗi toàn cục + logger.error

## Kiểm (vitest)
- `toRoutePattern('/procurement/purchase-orders/129', {id:'129'})` → `/procurement/purchase-orders/:id`; không params vẫn thay số/uuid; `?q=nguyen` không bao giờ có trong kết quả; chuỗi 500 ký tự → 120.
- Hàng đợi: tắt cờ → `fetch` không được gọi; 250 sự kiện → 3 lô ≤ 100; payload > 60 KB → chia; 401 → lô còn trong bộ đệm; 500 → bỏ; tràn 300 → giữ 300 mới nhất; pagehide → `keepalive: true` và header Authorization có mặt.
- Dwell: hiện 10 s, ẩn 60 s, hiện 5 s → 15 s.
- Form: mở → submit → không có ABANDON; mở → unmount → ABANDON với duration; `active=false` → không phát gì.
- Search: query rỗng → không phát; cùng query 2 lần → 1 sự kiện; kết quả 0 → `result_count: 0`; payload không chứa chuỗi query (khẳng định trên `JSON.stringify` của lô).
- Lỗi: 25 lỗi khác nhau → 20 sự kiện; `0912345678` trong thông điệp → bị thay.
Chạy: `docker compose exec -T erp npx vitest run src/core/telemetry src/modules/procurement src/modules/hr src/shared/crud src/modules/document`
+ `npm run typecheck` + `npm run lint` (0 lỗi).

## Rủi ro
| Rủi ro | K × T | Giảm thiểu |
|---|---|---|
| Bộ thu làm chậm giao diện | Thấp × Trung bình | chỉ đẩy vào mảng; gửi 30 s/lần; không re-render (không state React) |
| Firefox < 133 không hỗ trợ keepalive | Thấp × Thấp | mất lô cuối khi đóng tab; lô định kỳ vẫn đủ |
| Lọt từ khóa qua route (route có `/search/:term`) | Thấp × Cao | `toRoutePattern` thay mọi param; server chuẩn hóa lại; test |
| Sửa 12 tệp nghiệp vụ lớn (> 1000 dòng) | Trung bình × Thấp | chỉ thêm 2–3 dòng gọi hook, không đổi luồng |

## Bảo mật
Không gửi `user_id`, giờ máy, query string, giá trị ô nhập. Công tắc tắt → không có lời gọi mạng nào.
