# YÊU CẦU PHI CHỨC NĂNG — NHẬN HÀNG VÀ CHẤT LƯỢNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-NH-NN`. Phân hệ chưa có mã riêng; phần nhận hàng hiện chạy trong Đơn mua hàng, nên yêu cầu
hiện hành đi theo [thu mua 02](../../thu-mua/chuc-nang/02-yeu-cau-phi-chuc-nang.md). Các dòng *đề xuất* lấy từ
[nghiên cứu](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md), chưa phải yêu cầu đã chốt.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-NH-01 | Hiệu năng | Chưa có | Chưa có | Chưa đo |
| PCN-NH-02 | Phân quyền | Hiện tại: ghi số nhận cần `purchase_order.write`, phạm vi theo đơn. Đề xuất: entity mới `goods_receipt` (lập, ghi sổ, đảo) tách khỏi quyền đơn, khai đủ bảy sổ đăng ký theo skill `them-entity-moi` | [nghiên cứu mục 6.2](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Chưa làm |
| PCN-NH-03 | Dữ liệu nhạy cảm | Chưa có | Chưa có | Chưa đo |
| PCN-NH-04 | Giới hạn đầu vào | `qc_result` là `String(20)` chữ tự do; đề xuất chuyển sang bộ mã `SMALLINT`. Máy chủ chưa chặn số nhận vượt số đặt (dữ liệu thật có 128 mặt hàng từng nhận vượt 1 tới 25 %); đề xuất dung sai theo nhóm hàng | [nghiên cứu mục 1, 4.2, 6.6](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Chưa đạt theo nghiên cứu |
| PCN-NH-05 | Nhật ký và truy vết | Hiện xóa lần giao là xóa cứng phiếu nhập, dòng sổ kho, công nợ (`_cleanup_delivery`), không giữ dấu vết. Đề xuất: đảo phiếu thay xóa; nhật ký sửa số nhận, số chấp nhận (ai, lúc nào, từ bao nhiêu, lý do) | [nghiên cứu mục 4.1, 4.2, 7.1 N1.6](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Chưa đạt theo nghiên cứu |
| PCN-NH-06 | Lưu trữ và dọn dữ liệu | Như PCN-NH-05; thời hạn giữ chứng từ nhận hàng: Chưa có | Chưa có | Chưa đo |
| PCN-NH-07 | Sao lưu và khôi phục | Nằm trong bản sao lưu CSDL chung (`backup.run`, `backend/app/core/celery_app.py`); tệp phiếu giao, biên bản lưu qua phân hệ đính kèm chung (`attachment`) | Chưa có | Chưa đo |
| PCN-NH-08 | Đồng thời | Phiếu nhập ngầm có khóa duy nhất `delivery_id` (một lần giao một phiếu). Hai người cùng ghi một lần giao: Chưa có | [nghiên cứu mục 4.1](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Chưa đo |
| PCN-NH-09 | Tích hợp | Lưu ĐMH gọi `goods_receipt.service.upsert_for_delivery`, `inventory.service.apply_delivery`, `payable.service.upsert`. Xóa lần giao bị chặn nếu công nợ đã có tiền trả hoặc có dòng YCTT trỏ tới | [nghiên cứu mục 4.1](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Chưa đo |
| PCN-NH-10 | Khả dụng và thiết bị | Bảng lần giao v2 chưa có ô kết quả kiểm (nghiên cứu ghi là điểm hở); thiết bị di động cho thủ kho: Chưa có | [nghiên cứu mục 1](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Chưa đạt theo nghiên cứu |
| PCN-NH-11 | Pháp lý | Chưa có yêu cầu viết cho phân hệ. Câu R-Q8 (có hướng ISO 9001 không) còn mở | [nghiên cứu mục 6.11](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Chưa đo |
| PCN-NH-12 | Vận hành | Chưa có việc chạy ngầm. Trước khi bật nấc 2 phải kiểm kê chốt số dư đầu kỳ và tập huấn thủ kho, QC | [nghiên cứu mục 7.2](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Chưa làm |
