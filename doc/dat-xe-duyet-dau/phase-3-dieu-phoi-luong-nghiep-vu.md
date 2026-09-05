# PHA 3 — Điều phối & luồng nghiệp vụ theo vai trò ✅

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **ĐÃ XONG** (hồi cứu).
> ⚠️ Đây là luồng **chuyển trạng thái trực tiếp theo quyền** — bản nối engine đa-bước ở
> [phase-6-con-lai.md](phase-6-con-lai.md) §6.1.

## Mục tiêu
Cho phiếu chạy hết vòng đời qua tay từng vai trò: **người duyệt** (Duyệt / Yêu cầu chỉnh sửa / Từ chối)
→ **điều phối viên** (gán 1 xe + 1 tài xế) → **tài xế được phân** (Chấp nhận / Từ chối / Bắt đầu /
Hoàn tất). Chốt chặn thật ở backend, không chỉ ẩn nút.

## Phạm vi & việc đã làm
- [x] **Điều phối**: gán 1 xe + 1 tài xế → phiếu *Điều phối*, tài xế *Chờ nhận*.
- [x] **Người duyệt**: Duyệt · Yêu cầu chỉnh sửa · Từ chối (kèm **lý do**, ghi vào `note`).
- [x] **Tài xế**: Chấp nhận · Từ chối chuyến (lý do, quay về điều phối) · Bắt đầu (chấm giờ) · Hoàn tất (km + chi phí).
- [x] Chốt chặn `_ensure_can_drive` (đúng tài xế được phân; người không phải tài xế được thao tác thay) + `require`.
- [x] Cụm nút chuyển trạng thái **bày theo vai trò** trên trang chi tiết.
- [x] Tạo **luồng duyệt cấu hình** "Duyệt yêu cầu đặt xe" (2 bước) + full test data.

## Thiết kế kỹ thuật
| Chuyển | Endpoint | Hàm service |
|---|---|---|
| Duyệt | `POST /api/vehicle-bookings/{id}/approve` | `approve_booking` |
| Yêu cầu chỉnh sửa | `.../{id}/return` (+ `ReasonIn`) | `return_booking` |
| Từ chối | `.../{id}/reject` (+ `ReasonIn`) | `reject_booking` |
| Điều phối | `.../{id}/dispatch` (+ `DispatchIn`) | `dispatch_booking` |
| Tài xế nhận / từ chối | `.../{id}/driver/accept` · `/driver/reject` | `driver_accept` · `driver_reject` |
| Tài xế bắt đầu / hoàn tất | `.../{id}/driver/start` · `/driver/complete` (+ `CompleteIn`) | `driver_start` · `driver_complete` |

- Chốt chặn: `_ensure_can_drive`, `_is_assigned_driver`, `_append_note` (ghi lý do có nhãn) — `service.py`.
- Lấy 1 phiếu qua `_scoped_or_404` (dùng `get_scoped`, không `db.get`).
- FE: `components/booking-workflow-actions.tsx` (bày nút theo vai trò) + dialog điều phối / lý do / hoàn tất (popup C-01) + `booking-reason-dialog.tsx`, `booking-complete-dialog.tsx`.
- Seed test: `backend/scripts/seed_datxe_demo.py` (phiếu đủ mọi trạng thái + luồng "Duyệt yêu cầu đặt xe" 2 bước).

## Cấu hình / migration
- Không thêm cột/ENV — dùng cột điều phối/chạy thực tế đã có từ PHA 0.
```bash
docker compose exec -T api python -m scripts.seed_datxe_demo
```

## Chống trùng / Idempotent
- Mỗi chuyển kiểm **trạng thái nguồn** hợp lệ (vd chỉ Duyệt được phiếu *Chờ duyệt*) → bấm lại không nhảy sai.
- Tài xế Hoàn tất: chấm `actual_end_time`, phiếu sang *Hoàn thành* — không lặp.

## Đã kiểm (tiêu chí hoàn thành)
- Chạy end-to-end 6 bước trên phiếu dựng riêng (mã unique) qua các tài khoản vai trò khác nhau.
- Tài xế A **không** thao tác được chuyến của B; admin/điều phối thao tác thay được.
- Lý do Trả/Từ chối/Tài xế từ chối hiện đúng trong `note`.

## Rủi ro & lưu ý
- **Chưa chống trùng giờ** khi điều phối (1 xe/tài xế có thể nhận 2 chuyến trùng khung) → [phase-6 §6.3](phase-6-con-lai.md).
- Duyệt hiện theo **quyền `approve`**, chưa qua engine — khi bật engine phải **ẩn** cụm nút trực tiếp
  để tránh 2 đường đổi trạng thái ([phase-6 §6.1](phase-6-con-lai.md)).
