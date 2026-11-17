# Nhập giá sau VAT, tự tính giá trước thuế — YCMH và ĐMH (duoc-CR-776)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 17/11/2026 | Anh Được (NSU231) | Hiệu lực | duoc-CR-776 |

Trạng thái kế hoạch: xong

## Yêu cầu (anh Được chốt 17/11/2026)

- Phạm vi: dòng hàng **Yêu cầu mua hàng** và **Đơn mua hàng**, cả giao diện cũ (`frontend/`) và mới (`frontend-v2/`).
  KHÔNG làm: yêu cầu báo giá, phiếu khảo sát, công nợ, bản in.
- **Hai ô cùng sửa được** trên mỗi dòng: *Đơn giá (chưa VAT)* và *Đơn giá sau VAT*. Gõ ô nào thì ô kia tự tính.
- Đổi **VAT %** khi đã có giá: **giữ ô vừa gõ gần nhất**. Vừa gõ sau VAT thì giữ sau VAT, tính lại trước thuế; vừa
  gõ trước thuế (hoặc chưa gõ gì trong phiên — dòng mới nạp từ máy chủ) thì giữ trước thuế như hiện nay.
- Đơn giá trước thuế tính ngược giữ **4 số lẻ** (đúng độ chính xác cột `price` Numeric(18,4)).

## Thiết kế

- **Máy chủ không đổi.** Vẫn nhận / lưu `price` (trước thuế) và `vat` / `vat_pct` (phần trăm, 8 = 8%). Ô sau VAT chỉ là
  cách nhập ở giao diện; payload gửi đi KHÔNG kèm trường phụ nào.
- Công thức (một nơi mỗi giao diện, hàm thuần có bài kiểm):
  - sau VAT = làm tròn 2 số lẻ của `price × (1 + vat/100)` (khớp `delivery_service` CR-307);
  - trước thuế = làm tròn 4 số lẻ của `sau VAT / (1 + vat/100)`;
  - VAT rỗng / âm coi như 0; giá rỗng / âm / không phải số → để trống, không tính.
- Trạng thái "ô vừa gõ" và số sau VAT người dùng gõ giữ ở bản nháp dòng phía giao diện (không lưu), mất khi tải lại.
- Đơn nhập khẩu ép VAT dòng = 0 → hai ô bằng nhau, vẫn chạy đúng.

## Việc

| Phase | Nội dung | Tệp chính |
|---|---|---|
| v2 | Hàm thuần + bảng dòng + hộp chi tiết dòng của YCMH và ĐMH | `frontend-v2/src/modules/procurement/...` |
| v1 | Hàm thuần + bảng dòng + hộp chi tiết dòng của YCMH và ĐMH | `frontend/src/pages/PurchaseRequestDetail.tsx`, `PurchaseOrderDetail.tsx` |
| Tài liệu | HDSD Thu mua (bài lẻ, không dựng lại cây), cẩm nang thu mua, RAG | `backend/scripts/seed_help_thu_mua_*`, `seed_handbook/10-quy-trinh-thu-mua.md` |

## Kiểm

- Bài kiểm hàm thuần: 108.000 ↔ 100.000 ở 8%; 100.000 sau VAT ở 8% → 92.592,5926; VAT 0; rỗng / âm / chữ; đổi VAT
  giữ đúng ô vừa gõ.
- v2: typecheck, lint, vitest `src/modules/procurement`. v1: không thêm lỗi kiểu ở tệp đã sửa.
- Xem tận mắt trên local cả hai giao diện.
