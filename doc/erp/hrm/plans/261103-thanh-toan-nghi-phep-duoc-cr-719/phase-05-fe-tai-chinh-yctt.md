# Phase 05 — FE Tài chính: YCTT thanh toán nghỉ phép + bản in

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | giao-dien-v2 | Nháp | duoc-CR-719 |

## Context
- API ở [phase-02](phase-02-be-yctt-nguon-nghi-phep.md) (`_out` thêm `payee_employee_id`, `source_ref_id`, khối `leave_encashment`;
  bản in thêm `bank_hidden`). Cần `appRoutes.hr.leaveEncashmentDetail` từ bước 1 của [phase-04](phase-04-fe-nghi-phep.md).
- `modules/finance/pages/payment-request-detail-page.tsx` (1447 dòng, xoay quanh NCC + công nợ),
  `pages/payment-request-print-page.tsx` (471), `pages/payment-request-list-page.tsx`, `types/payment-request.ts`,
  `types/payable.ts:85` `PAYABLE_SOURCE_LABELS`.

## Tổng quan
P2. Không chen nhánh vào trang 1447 dòng: rẽ SỚM sang một khung riêng khi `source_type === 'leave_encashment'`.

## Việc
1. **Kiểu + nhãn** `types/payment-request.ts`: thêm `payee_employee_id`, `source_ref_id`, `leave_encashment?` và
   `PAYMENT_SOURCE_LABELS = { ...PAYABLE_SOURCE_LABELS, leave_encashment: 'Thanh toán nghỉ phép' }` (không thêm vào
   `PAYABLE_SOURCE_LABELS` — màn Công nợ sẽ hiện ô lọc thừa). Ô lọc **Loại** ở danh sách tự có lựa chọn mới.
2. **Chi tiết**: tệp mới `components/payment-request-leave-encashment-view.tsx` — người nhận (tên + mã, không STK), liên kết phiếu
   `TTP…` (chỉ khi `can('leave_encashment','read')`), số ngày / loại / năm / lý do, ô **Số tiền** (chỉ Nháp + `payment_request.write`),
   ghi chú, hình thức thanh toán; dùng lại các nút trạng thái sẵn có (Gửi duyệt / Duyệt / Từ chối / Ghi nhận đã chi / In). Không nút
   Xóa, không nạp lại theo công nợ, không thêm dòng. `payment-request-detail-page.tsx`: một chỗ rẽ sau khi nạp xong phiếu.
3. **Bản in** `payment-request-print-page.tsx`: nguồn nghỉ phép thay khối NCC bằng **Người nhận**, nội dung tự động *Thanh toán tiền
   nghỉ phép năm {năm} — {số ngày} ngày*; `bank_hidden` → dòng **Số tài khoản: kế toán tự điền** thay vì để trống im lặng.
4. **Bài kiểm**: `payment-request-leave-encashment-view.test.tsx` (ô tiền khóa khi không phải Nháp; không có nút Xóa; link phiếu ẩn
   khi thiếu quyền); sửa `payment-request-list-page.test.tsx` nếu nó đếm lựa chọn ô lọc.

## Tệp sở hữu
Tạo: `frontend-v2/src/modules/finance/components/payment-request-leave-encashment-view.tsx`,
`frontend-v2/src/modules/finance/components/payment-request-leave-encashment-view.test.tsx`.
Sửa: `frontend-v2/src/modules/finance/{types/payment-request.ts,pages/payment-request-detail-page.tsx,
pages/payment-request-print-page.tsx,pages/payment-request-list-page.test.tsx}`. Không sửa `shared/constants/*` (phase 04 giữ).

## Xong khi
typecheck 0 lỗi; `npx eslint src/modules/finance` 0 lỗi; `npx vitest run src/modules/finance` xanh; YCTT NCC cũ mở, sửa, in y
như trước (soát một phiếu NCC trên `localhost:8083`).

## Rủi ro
| Rủi ro | K × T | Giảm |
|---|---|---|
| Rẽ nhánh muộn làm hook của trang NCC chạy với phiếu nhân sự | TB × TB | Rẽ ở cấp component (khung riêng), không rẽ trong JSX giữa các hook |
| Bản in lộ STK | Thấp × Cao | Chỉ in thứ backend gửi; backend quyết định (D2) |
