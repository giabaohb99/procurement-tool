# PHA 4 — Đồng bộ UI/UX + Bản in + Nhân bản + Ghi chú đính kèm ảnh

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **CHƯA LÀM**.
> Khuôn 1-1: các component dùng chung của `vehicle-booking` (`booking-page-header`, `status-pill`, `confirm-dialog`, print page).

## Mục tiêu
Hoàn thiện giao diện cho khớp phong cách Đặt xe: header có nút back + badge, ghi chú đính kèm ảnh,
**bản in** phiếu (kèm ảnh chứng từ chữ ký sống), **nhân bản** phiếu, badge "pill" + confirm dialog + sort cột.

## Phạm vi & việc cụ thể
- [ ] **Header** (`SealPageHeader` — mẫu `booking-page-header.tsx`): nút **back** trái + tiêu đề = **Mục đích sử dụng** + tiêu đề phụ "Yêu cầu đóng dấu {code}" + badge trạng thái bên phải + cụm nút thao tác trên đầu.
- [ ] **Ghi chú đính kèm ảnh** (`doc_type="note"`): ô ghi chú có nút thêm ảnh; ảnh hiển thị **inline** ở khối Ghi chú trên chi tiết. Tách khỏi khối **chứng từ chữ ký sống**.
- [ ] **Bản in** (`/print/approval-seal/:id`, `seal-request-print-page.tsx`): thông tin phiếu + người tạo + lịch sử duyệt + **ảnh chứng từ chữ ký sống** (nhúng); nút "In phiếu" ở chi tiết.
- [ ] **Nhân bản** (`/new?from=<id>`): chép nội dung phiếu, **KHÔNG** chép tệp đính kèm; biểu tượng nhân bản mỗi dòng danh sách.
- [ ] **Dùng chung**: badge "pill" (`status-pill.tsx`), hộp xác nhận toàn cục (`shared/ui/confirm-dialog.tsx`), **sắp xếp theo cột** (server-side, whitelist) cho 2 bảng, icon `Stamp` (lucide) cho menu + thẻ phân hệ.
- [ ] Ô **chỉ xem** dùng `read-only-value.tsx`; giá trị trong ô CHỌN kèm `copy-button.tsx` (không `<Input disabled>`).

## Thiết kế kỹ thuật
- **Bản in** tái dùng khuôn `vehicle-booking-print-page.tsx`: layout A4, `@media print`, ẩn nav. Ảnh chứng từ nhúng theo URL `preview` của attachment (ảnh) / liệt kê PDF (không nhúng, ghi tên + trang).
- **Nhân bản**: FE đọc `?from=`, prefill form từ chi tiết phiếu nguồn (trừ `code`, `status`, tệp).
- Màu qua **token semantic**; gộp class bằng `cn()`; icon chỉ `lucide-react`.
- Badge trạng thái map `SEAL_STATUS_LABELS` → tông pill: Hoàn thành ok(xanh) · Chờ duyệt warn(vàng) · Đã duyệt info(xanh dương) · Từ chối err(đỏ) · Đã hủy gray · Nháp/YCCS gray/warn.

## Cấu hình / migration
- Không thêm cột/ENV. Route in đăng ở `app/router/app-router.tsx` (`/print/approval-seal/:id`, ngoài layout chính).
```bash
docker compose exec erp npm run check
```

## Chống trùng / Idempotent
- Nhân bản không chép tệp → không nhân đôi chứng từ gốc.
- Bản in chỉ đọc; không đổi trạng thái.

## Kiểm thử & tiêu chí
- Header hiện đúng: back về danh sách, tiêu đề = mục đích, badge đúng màu theo trạng thái.
- Ghi chú kèm 2 ảnh → hiển thị inline; chứng từ chữ ký sống vẫn ở khối riêng.
- Bản in mở tab in, có ảnh chứng từ; nhân bản mở form đã prefill, **không** có tệp.
- `npm run check` xanh; không thêm cảnh báo lint mới.

## Rủi ro & lưu ý
- **Bản in ảnh nặng**: giới hạn kích thước hiển thị, dùng URL `preview` (thumbnail) khi có để in nhanh.
- Đừng để nút "In phiếu"/nhân bản lộ ở trạng thái không hợp lệ (in khi chưa có gì thì rỗng).
- Ảnh ghi chú và chứng từ **cùng entity** — phân biệt bằng `doc_type`, chớ trộn khi liệt kê.
