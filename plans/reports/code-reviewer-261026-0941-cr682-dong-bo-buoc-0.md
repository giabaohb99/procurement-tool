# Review duoc-CR-682 — Bước 0 đồng bộ app đặt xe cũ

Luật chủ dự án: KHÔNG ghi gì sang app cũ (prod). Rà xác nhận: không đường mạng mới, `erp_action_at` không lọt payload chiều gửi / API.

| Mã | Phát hiện | Xử lý |
|---|---|---|
| H1 | Phiếu ERP làm chủ vẫn chép nội dung → lượt quét ép đêm trả mục đích người dùng sửa trên ERP về bản cũ (đã dò thật) | ERP đụng vào = làm chủ CẢ phiếu; bộ nghe đóng dấu khi BẤT KỲ cột nghiệp vụ đổi (kể cả lưu nháp) |
| H2 | Lượt nhận đọc dòng không khóa → cú bấm ERP giữa lượt bị đè | `db.refresh(..., with_for_update=True)` dấu + trạng thái trước khi phân xử |
| H3 | Làm chủ cả phiếu, không gỡ → tiến độ tiếp bên app cũ không sang | GIỮ — đánh đổi ghi ở sổ tay §8; hỏi anh Được / đại ca |
| M1 | `import_approval_history.py` chạy lại sẽ đóng dấu nhầm | Bọc `suppress_outbound()` |
| M2 | Phiếu ERP thao tác trước deploy vẫn bị lùi đêm đầu | Migration lấp dấu từ `tab_audit_log` `actor_kind = 1` (trừ xem / in / xuất); thử MySQL local bằng phiếu giả |
| M3 | Phiên duyệt soi gương dựng lại mỗi lượt, kể cả phiếu ERP làm chủ | Bỏ dựng lại khi đã có dấu |
| M4 | Docstring nói luật chốt không phụ thuộc dấu | Sửa docstring |
| L | Chiều gửi chưa bỏ qua cột dấu | Thêm `erp_action_at` vào `IGNORED_ATTRS` |
| L | Hủy từ app cũ trên phiếu đang điều phối giữ xe / tài xế | GIỮ — ghi chú |
| L | Trùng `legacy_id` (bao-CR-661) | Ngoài phạm vi |

Câu hỏi treo: «duyệt trên ERP rồi điều phối bên app cũ» có đang xảy ra thật không; bao nhiêu phiếu prod sẽ được lấp dấu.
