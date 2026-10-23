# Ép tải duoc-CR-660 + duoc-CR-674 (duoc-CR-675) — 23/10/2026

Phạm vi: mã sáng 23/10 — CR-660 (cổng xuất / nhập, che cột nhạy cảm, tải lại tệp xuất), CR-674 (sổ nhật ký task khai loại việc, hạn, giờ). CR-673 chỉ tài liệu, bỏ.

## Kết quả nhanh

| Hạng mục | Kết quả |
|---|---|
| Bài kiểm ép tải mới | 13 backend + 2 vitest, xanh sau khi sửa |
| Lỗi tìm ra | **4** (1 do CR-674 sáng nay, 3 có từ trước) — đã sửa cả 4 |
| Hồi quy | backend 728 + 221 + 23 bài, vitest đặt xe 105, typecheck 0, lint 0 lỗi |
| Tải HTTP 6 đường xuất | 1 / 10 / 50 / 150 người: **0 lỗi** (6 / 60 / 300 / 900 lượt đạt) |

## Lỗi tìm ra

| # | Lỗi | Gốc | Sửa |
|---|---|---|---|
| 1 | Sổ nhận giờ `999.01…999.99`, máy chủ chặn ở 999 → 422 giữa lượt đồng bộ | CR-674 sáng nay (bài dò ngẫu nhiên 3000 chuỗi) | `_parse_hours` chặn > 999 |
| 2 | Đọc sổ 18 000 mục mất ~2,8 s: kiểm trùng key bằng `list.count` trong vòng lặp (bậc hai) | Có từ trước | `Counter` → 0,3 s |
| 3 | Xuất CSV / Excel nhân sự N+1: 2000 dòng = 2008 / 2011 truy vấn (cột Phòng ban, Công ty đọc qua quan hệ) | Có từ trước | `selectinload(department, company)` → số truy vấn cố định |
| 4 | Xuất Excel **xe, tài xế, đặt xe** chỉ đòi quyền Xem; xuất đặt xe lọc phạm vi theo quyền Xem | Có từ trước (sót của NT1-1) | Gác `export`, phạm vi theo grant Xuất; nút v2 ẩn khi thiếu quyền; seed cấp Xuất cho điều phối viên (tất cả), tài xế (được giao), người đặt xe (của mình) |

Lỗi 4 do bài QUÉT `app.routes` tìm ra: người có mọi quyền trừ Xuất / Nhập gọi mọi đường `…/export/csv|xlsx` (33) và `…/import/csv` (18). Sau sửa: 0 đường lọt. Thêm danh mục mới mà quên gác thì bài này đỏ.

## Tải HTTP (local, 1 tiến trình uvicorn, 2 CPU)

| Người cùng lúc | Lượt | Đạt | p50 | p95 | Lâu nhất |
|---|---|---|---|---|---|
| 1 | 6 | 6 | 0,15 s | 0,68 s | 0,68 s |
| 10 | 60 | 60 | 1,5 s | 4,6 s | 4,8 s |
| 50 | 300 | 300 | 9,5 s | 19,5 s | 21,8 s |
| 150 | 900 | 900 | 20,7 s | 25,7 s | 26,9 s |

- Đường nặng nhất: xuất CSV sản phẩm (6 803 dòng) 0,68 s một mình.
- Chậm theo số người là XẾP HÀNG sau cổng 20 lượt / tiến trình (CR-671), không phải khóa: đường phòng ban 36 ms một mình vẫn chờ ~20 s ở 150 người. Prod chạy 2 tiến trình → ước nửa thời gian.
- 150 người bấm xuất cùng một giây là quá sức thực tế (20–100 người dùng); p95 ở đó 25,7 s, sát ngưỡng 503 `server_busy` 30 s.

Số liệu: `plans/261023-0935-stress-test-cr660-cr674/results/concurrent.json` · script `.../scripts/measure-export-concurrency.py`.

## Tệp

- Mới: `test/backend/test_ep_tai_quyen_xuat_nhap_cr675.py` (8), `test/backend/test_ep_tai_so_task_cr675.py` (5), `frontend-v2/src/modules/vehicle-booking/components/catalog-export-button.test.tsx` (2).
- Sửa: `backend/scripts/sync_task_journal.py`, `backend/app/modules/employee/controller.py`, `backend/app/modules/vehicle_booking/{controller,catalog_controller}.py`, `backend/app/seed.py`, `frontend-v2/src/modules/vehicle-booking/{components/catalog-export-button.tsx,config/{vehicle,driver}-crud.tsx,pages/{vehicle-booking-list,my-trips}-page.tsx}`.

## Deploy

Seed KHÔNG ghi đè quyền trên hệ đang chạy (D-018). Lên prod phải tick **Xuất** cho: *Điều phối viên (Đặt xe)* — đặt xe / xe / tài xế; *Tài xế (Đặt xe)* — đặt xe (phạm vi được giao), xe, tài xế; *Người đặt xe* — đặt xe (phạm vi của mình). Chưa tick thì nút Xuất Excel ẩn với họ (không còn bấm ra 403).

## Câu hỏi còn treo

- Không có.
