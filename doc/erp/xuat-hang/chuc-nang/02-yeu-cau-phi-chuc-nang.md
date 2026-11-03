# YÊU CẦU PHI CHỨC NĂNG — XUẤT KHO VÀ GIAO HÀNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-XH-NN`. Phân hệ chưa có mã nên hầu hết dòng ghi *Chưa có*; các dòng *đề xuất* lấy từ
[nghiên cứu](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md), chưa phải yêu cầu đã chốt.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-XH-01 | Hiệu năng | Chưa có | Chưa có | Chưa đo |
| PCN-XH-02 | Phân quyền | Chưa có entity. Đề xuất: thủ kho tách khỏi người mua, người dùng (câu X2); đề nghị lĩnh đi qua bộ máy duyệt chung | [nghiên cứu mục 7, 8](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) | Chưa làm |
| PCN-XH-03 | Dữ liệu nhạy cảm | Chưa có | Chưa có | Chưa đo |
| PCN-XH-04 | Giới hạn đầu vào | Đề xuất: chặn tồn âm khi xuất (hiện `service.adjust` không kiểm số tồn); chặn phát vượt số đề nghị | [nghiên cứu mục 5 B6, mục 7 XG1, XG2](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) | Chưa làm |
| PCN-XH-05 | Nhật ký và truy vết | Đề xuất: hủy phiếu bằng dòng đảo, không xóa | [nghiên cứu mục 7 XG1](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) | Chưa làm |
| PCN-XH-06 | Lưu trữ và dọn dữ liệu | Chưa có | Chưa có | Chưa đo |
| PCN-XH-07 | Sao lưu và khôi phục | Khi có bảng mới, nằm trong bản sao lưu CSDL chung (`backup.run`, `backend/app/core/celery_app.py`) | Chưa có | Chưa đo |
| PCN-XH-08 | Đồng thời | Đề xuất (XG7): hai đơn tranh một lô không lấy mất của nhau | [nghiên cứu mục 7](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) | Chưa làm |
| PCN-XH-09 | Tích hợp | Nối Đặt xe theo kiểu *nối chứ không gộp*; thêm cột vào phiếu đặt xe phải giữ ràng buộc đồng bộ app đặt xe cũ (`legacy_datxe/`). MISA: đẩy phiếu xuất, phiếu giao ở XG8; sổ kho chính thức ở đâu là câu X4 | [nghiên cứu mục 4, 6.2, 6.3](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) | Chưa làm |
| PCN-XH-10 | Khả dụng và thiết bị | Đề xuất: tài xế xác nhận từng điểm dừng kèm ảnh biên bản (màn *Chuyến của tôi* của Đặt xe đã có) | [nghiên cứu mục 7 XG4](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) | Chưa làm |
| PCN-XH-11 | Pháp lý | Chưa có yêu cầu viết. Hóa đơn bán, hóa đơn điện tử ngoài phạm vi (câu X12); hàng gửi đi bán tài khoản 157 là câu X11 | [nghiên cứu mục 2, 8](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) | Chưa đo |
| PCN-XH-12 | Vận hành | Chưa có | `/api/system/jobs` | Chưa đo |
