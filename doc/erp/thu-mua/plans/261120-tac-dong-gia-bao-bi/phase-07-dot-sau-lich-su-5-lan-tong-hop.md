# Phase 07 — Đợt sau: lịch sử theo mã / SP, giá 5 lần gần nhất, tổng hợp

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 20/11/2026 | planner | Nháp | duoc-CR-784 (CR riêng khi làm) |

Hoãn · ~8 giờ (không tính vào effort) · cần 06 xong và người dùng chạy thật đợt đầu.

## Nội dung (bám bản mẫu)
| Tab | Đường đề xuất | Tái dùng |
|---|---|---|
| Tổng hợp (mọi SP: tăng / giảm / không đổi / chưa có giá) | `GET /api/packaging-cost/summary` (+ `/export`) | `compute_product_cost` không ghi đè + `get_price_states(None)` — gần như miễn phí |
| Giá 5 lần gần nhất (ma trận) | `GET /api/packaging-cost/last-prices` | truy vấn 1 của `get_price_states` với `rn <= 5`, thêm biến động lần 1/2, 1/5, giá TB |
| Lịch sử theo mã VTBB / theo SP (biểu đồ đơn giá) | `GET /api/packaging-cost/history` | đọc thẳng sổ giá, phân trang máy chủ, trần 2.000 dòng hiện |

## Điều kiện kích hoạt
Người dùng đã dùng Tác động + Bảng giá ít nhất một kỳ báo giá, và Q1 (nguồn MISA) đã chốt — nếu nạp MISA thì lịch sử ở
đây mới khớp bản mẫu.

## Không làm (YAGNI)
- Sửa đơn giá lịch sử ngay trên bảng như bản mẫu (ô vàng): lịch sử là bản chụp bất biến; sai thì sửa ở ĐMH / nguồn nạp.
