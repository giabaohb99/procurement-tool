# PHA 4–5 — Đồng bộ UI/UX & đưa Thêm/Sửa lên TRANG ✅

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **ĐÃ XONG** (hồi cứu).
> Gộp 2 phase (như bộ ke-hoach-celery gộp "Phase 4–5") vì cùng là lớp **hoàn thiện giao diện**.

## Mục tiêu
Đưa 3 màn của phân hệ về đúng chuẩn thiết kế DEGO ERP v2: **badge "pill"** thống nhất, **hộp xác nhận
có style** (bỏ `window.confirm`), **sắp xếp theo cột**, **icon tự vẽ**; và **quyết định lớn** — chuyển
toàn bộ **Thêm/Sửa** của 3 màn từ popup sang **TRANG riêng** (case UI C-01 → **C-02**), kèm **Lịch sử
thao tác** + nút **Xóa** trên trang sửa.

## Phạm vi & việc đã làm
**PHA 4 — Đồng bộ UI/UX**
- [x] Badge "pill" theo `po_badges_design.md` (ok/warn/err/info/gray) — `status-pill.tsx`.
- [x] Hộp xác nhận style toàn cục thay `window.confirm` — `shared/ui/confirm-dialog.tsx`.
- [x] Sắp xếp theo cột cho 3 bảng (server-side, whitelist cột thật) — `sortable` + `apply_sort`.
- [x] Icon sedan tự vẽ cho menu Quản lý xe + thẻ phân hệ — `booking-type-icons.tsx`.
- [x] Bảng Phân quyền `/hr/permissions` dạng cây + 3 vai trò Đặt xe + màu — `role-permission-matrix.tsx`.
- [x] Chọn vai trò khi giao duyệt "theo vai trò" ở form node — `approval-node-form.tsx`.

**PHA 5 — Thêm/Sửa lên TRANG**
- [x] Khung CRUD thêm `createRoute` (nút Thêm điều hướng), bỏ popup danh mục — `shared/crud`.
- [x] Trang Thêm/Sửa Xe (`/vehicles/new`, `/vehicles/:id`) — `vehicle-catalog-form-page.tsx` + `VehicleForm`.
- [x] Trang Thêm/Sửa Tài xế (`/drivers/new`, `/drivers/:id`) — `driver-catalog-form-page.tsx` + `DriverForm`.
- [x] Trang Thêm/Sửa Yêu cầu (`/vehicle-booking/new`, `/:id/edit`, nhân bản `?from=`) — `vehicle-booking-form-page.tsx` + `BookingForm`.
- [x] Khối **Lịch sử thao tác** (`AuditTimeline`) + nút **Xóa** trên trang sửa.
- [x] Ghi case **C-02** vào skill `/ui` (đảo C-01).

## Thiết kế kỹ thuật
| Việc | Vị trí |
|---|---|
| Badge pill | `components/status-pill.tsx` — `StatusPill`, `BookingStatusBadge`, `DriverStatusBadge`, `SourceBadge`, `AvailabilityBadge` |
| Confirm toàn cục | `shared/ui/confirm-dialog.tsx` (zustand store + `confirm()` promise + `<ConfirmDialogHost/>` mount ở `app-providers.tsx`) |
| Sort | FE: cột `sortable: true` + `sortBy/sortDir/onSortChange`; BE: `apply_sort` whitelist **cột vật lý** |
| Icon | `components/booking-type-icons.tsx` (`CarTileIcon` forwardRef, viewBox 39×28, stroke `currentColor` — không ép màu, kế thừa màu menu) |
| Khung CRUD | `shared/crud/types.ts` (`createRoute`), `crud-list-page.tsx` (nút Thêm điều hướng nếu có `createRoute`) |
| Form trang | `components/{vehicle,driver,booking}-form.tsx` — nhúng vào page, `mx-auto max-w-2xl`, có `onDone` |

## Cấu hình / migration
- Không có migration/ENV. Route mới khai ở `modules/vehicle-booking/routes.tsx` (static `/new` xếp
  trước dynamic `/:id` theo luật xếp hạng react-router v6).

## Chống trùng / Idempotent
- Không áp dụng (lớp giao diện). Các file `*-form-dialog.tsx`, `*-detail-dialog.tsx`,
  `*-detail-page.tsx` cũ **đã xóa** để không còn 2 đường Thêm/Sửa song song.

## Đã kiểm (cổng + tiêu chí hoàn thành)
```bash
docker compose exec erp npm run check   # typecheck 0 lỗi · lint 0 lỗi · vitest xanh
```
- Xác minh trực tiếp trên `http://localhost:8083`: Thêm/Sửa 3 màn mở TRANG; nhân bản chép nội dung;
  sort cột chạy; confirm styled bật khi Xóa; badge + icon đúng.

## Rủi ro & lưu ý
- **Ô chỉ xem cấm `<Input disabled>`** — dùng `read-only-value.tsx`; giá trị trong ô CHỌN gắn `copy-button.tsx`.
- **Icon tự vẽ** phải khai đúng `viewBox` theo hệ toạ độ path + `strokeWidth` dày bằng lucide cạnh nó.
- Case C-01 (popup chống mất dữ liệu) **đã đảo** cho phân hệ này thành C-02 (trang); dialog **thao tác
  nhanh** (điều phối/lý do/hoàn tất) vẫn giữ popup — xem [phase-6 §6.6](phase-6-con-lai.md).
