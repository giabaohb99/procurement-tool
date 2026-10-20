# Phase 02 — D0b: Mở rộng theo dõi form (6 → 13)

## Context links
- `frontend-v2/src/core/telemetry/use-form-telemetry.ts` (`useFormTelemetry(form, active)` → `{markSubmitted}`)
- 6 chỗ gọi hiện có: PR/SR/PO detail, leave detail, `labor-contract-form-dialog.tsx`, `employee-form-dialog.tsx`
- `backend/app/core/usage_codes.py` (`UiForm`), `usage_profile/snapshot_metrics_screens.py` (`docs_forms_metrics` cộng mọi form, không liệt kê cứng)

## Overview
- P1 · **1 ngày** (BE 0,1 · FE 0,9) · implemented (duoc-CR-654) · sau phase 01 (cùng `usage_codes.py` + `statuses.ts` sinh).
- Thêm 7 mã `UiForm` và gắn `useFormTelemetry` ở 7 màn đại ca nêu.

## Key insights
- Không có khung form dùng chung giữa 7 màn → gắn từng màn, mỗi chỗ ~5 dòng (hook + `markSubmitted()` sau khi lưu thành công).
- **Nhận hàng không có form riêng**: số lượng/ngày nhận sửa trong `purchase-order-line-dialog.tsx` (phần deliveries). Đề xuất đo
  dialog dòng ĐMH như form «Nhận hàng / dòng ĐMH» (câu hỏi mở Q4).
- **Việc dự án** sửa trực tiếp (tự lưu) trong `task-detail-sheet.tsx` → không có «gửi». Chỉ đo **tạo nhanh** (`task-draft-row.tsx`): mở dòng nháp → tạo = SUBMIT, hủy/rời = ABANDON.
- Gom ngày (`daily_ui`) và snapshot cộng `forms` theo khóa số bất kỳ → **không cần sửa backend gom**; nhãn mới tự có ở FE qua `UI_FORM` sinh.

## Requirements
- Mỗi form: FORM_OPEN khi mở chế độ tạo/sửa, FORM_SUBMIT khi lưu/gửi thành công, FORM_ABANDON khi đóng/rời chưa lưu.
- Không đọc giá trị ô nhập (hook hiện tại đã đảm bảo).

## Architecture
Mã mới (tiếp số, không chèn giữa): 7 PAYMENT_REQUEST «Yêu cầu thanh toán» · 8 GOODS_RECEIPT «Nhận hàng (dòng ĐMH)» · 9 DOCUMENT «Văn bản» ·
10 VEHICLE_BOOKING «Đặt xe» · 11 SEAL_REQUEST «Duyệt dấu» · 12 ROOM_BOOKING «Đặt phòng họp» · 13 WORK_TASK «Việc dự án (tạo nhanh)».

| Form | Tệp | `active` | `markSubmitted()` |
|---|---|---|---|
| YCTT | `finance/pages/payment-request-detail-page.tsx` | `PaymentRequestCreate` mount; `PaymentRequestView` khi đang sửa | sau `handleCreate` (l.~408) / `handleSave`, `handleSubmit` thành công |
| Nhận hàng | `procurement/components/purchase-order-line-dialog.tsx` | `open` | sau lưu dòng thành công |
| Văn bản | `document/pages/document-create-page.tsx` | mount | trong `handleSubmit` (l.~333) sau mutate thành công |
| Đặt xe | `vehicle-booking/components/booking-form.tsx` | mount | `submit` (l.~238) thành công |
| Duyệt dấu | `approval-seal/components/seal-request-form.tsx` | mount | `submit` (l.~146) thành công |
| Phòng họp | `hr/pages/room-booking-detail-page.tsx` | chế độ `/new` hoặc đang sửa | `submitSave` (l.~141) thành công |
| Việc dự án | `work/components/task-draft-row.tsx` (+ quick-add kanban nếu cùng component) | dòng nháp mở | tạo task thành công |

## Related code files
Sửa BE: `backend/app/core/usage_codes.py` (7 mã + nhãn). Sinh lại `frontend-v2/src/shared/constants/statuses.ts`.
Sửa FE: 7 tệp ở bảng trên. Không tạo tệp mới. `work/` là vùng Agent 3 (màn Dự án) — báo trước, chỉ thêm hook.

## Implementation steps
1. Thêm 7 mã vào `UiForm` + `UI_FORM_LABELS`; chạy `gen_status_ts.py`.
2. Gắn hook từng màn; `markSubmitted()` đặt TRONG nhánh thành công (không trong `finally`).
3. Form dạng dialog: `active = open`; trang: `active = true` khi ở chế độ tạo/sửa.
4. typecheck + lint; vitest các thư mục đã sửa (`finance`, `procurement`, `document`, `vehicle-booking`, `approval-seal`, `hr`, `work`, `core/telemetry`).

## Todo
- [x] 7 mã `UiForm` + sinh TS
- [x] YCTT · Nhận hàng · Văn bản · Đặt xe · Duyệt dấu · Phòng họp · Việc dự án
- [x] cập nhật test mã BE

## Tests
- Backend: mở rộng `test/backend/test_bam_chuc_nang_d0.py` (hoặc `test_form_mo_rong_d0.py`): `UiForm` 13 mã, số 1–6 không đổi, nhận FORM_OPEN form=7..13.
- Vitest `core/telemetry/ui-event-codes.test.ts` (đã tự khớp bộ BE). Mỗi màn 1 test nhẹ: render → FORM_OPEN; submit thành công → FORM_SUBMIT; lỗi API → không SUBMIT.
  Ví dụ `finance/pages/payment-request-detail-page.telemetry.test.tsx`, `approval-seal/components/seal-request-form.telemetry.test.tsx`.

## Success criteria
- 13 form xuất hiện trong `tab_usage_daily.forms` sau một ngày có thao tác; màn Hồ sơ cách làm việc hiện nhãn đúng.
- Lưu lỗi (422) → không có FORM_SUBMIT; đóng không lưu → FORM_ABANDON.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Đặt `markSubmitted` sai chỗ → tỷ lệ bỏ dở sai | TB × TB | Test thành công/thất bại mỗi màn |
| Màn có cả xem lẫn sửa (YCTT, phòng họp) bắn OPEN khi chỉ xem | TB × TB | `active` chỉ true khi ở chế độ sửa/tạo |
| Dialog dòng ĐMH không chỉ nhận hàng | Cao × Thấp | Nhãn ghi rõ «Nhận hàng (dòng ĐMH)»; Q4 |

## Security
Không đổi bề mặt API. Hook không đọc giá trị ô nhập.

## Rollback
Gỡ hook từng màn độc lập; mã `UiForm` đã cấp giữ nguyên (không tái dùng).

## Next steps
Phase 03 dùng `forms` (mở/gửi/bỏ) cho cột «bỏ dở».
