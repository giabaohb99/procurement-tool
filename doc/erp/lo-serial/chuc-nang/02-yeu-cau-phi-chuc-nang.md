# YÊU CẦU PHI CHỨC NĂNG — LÔ, SERIAL VÀ HẠN DÙNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-LS-NN`. Phân hệ chưa có mã nên hầu hết dòng ghi *Chưa có*; các dòng *đề xuất* lấy từ
[nghiên cứu](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md), chưa phải yêu cầu đã chốt.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-LS-01 | Hiệu năng | Chưa có | Chưa có | Chưa đo |
| PCN-LS-02 | Phân quyền | Chưa có entity | Chưa có | Chưa làm |
| PCN-LS-03 | Dữ liệu nhạy cảm | Chưa có | Chưa có | Chưa đo |
| PCN-LS-04 | Giới hạn đầu vào | Đề xuất: ô lô chỉ hiện khi mã có `track_lot`; một dòng chứng từ một lô. Kiểu cột ngày của bảng lô (`Date` hay `String(10)`) là câu Q-L11, nghiên cứu nghiêng về `Date` | [nghiên cứu mục 7.4, 9](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) | Chưa làm |
| PCN-LS-05 | Nhật ký và truy vết | Đề xuất: dòng sổ kho chép cả `lot_id` lẫn `lot_no` (chứng từ là bản chụp); truy xuất ngược và xuôi theo lô là mục tiêu của L3, L4 | [nghiên cứu mục 7.4, 8](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) | Chưa làm |
| PCN-LS-06 | Lưu trữ và dọn dữ liệu | Chưa có. Tình trạng hết hạn suy ra từ ngày, không lưu cột | [nghiên cứu mục 7.4](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) | Chưa làm |
| PCN-LS-07 | Sao lưu và khôi phục | Khi có bảng mới, nằm trong bản sao lưu CSDL chung (`backup.run`, `backend/app/core/celery_app.py`) | Chưa có | Chưa đo |
| PCN-LS-08 | Đồng thời | Đề xuất: tổng tồn theo lô phải bằng `tab_inventory.qty`, có bài kiểm canh | [nghiên cứu mục 7.4](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) | Chưa làm |
| PCN-LS-09 | Tích hợp | Lô phải vào cùng lúc với phiếu nhập kho thật (nấc 2 doc 01); xuất theo lô cần phiếu xuất; truy xuôi tới khách cần bán hàng trên ERP hoặc nạp phiếu xuất bán có lô từ MISA (Q-L8) | [nghiên cứu mục 1, 8, 9](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) | Chưa làm |
| PCN-LS-10 | Khả dụng và thiết bị | Chưa có | Chưa có | Chưa đo |
| PCN-LS-11 | Pháp lý | Thành phẩm phân bón phải in ngày sản xuất, hạn sử dụng (Nghị định 43/2017/NĐ-CP sửa bởi Nghị định 111/2021/NĐ-CP); thuốc bảo vệ thực vật phải in thêm số lô sản xuất (Thông tư 21/2015/TT-BNNPTNT); khung truy xuất nguồn gốc theo Thông tư 02/2024/TT-BKHCN. Nghiên cứu ghi các văn bản có thể đã được sửa, cần pháp chế xác nhận (L0) | [nghiên cứu mục 5.3](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) | Chưa xác nhận văn bản hiện hành |
| PCN-LS-12 | Vận hành | Đề xuất: thẻ *lô sắp hết hạn* theo khuôn cảnh báo sẵn có ở `dashboard/controller.py`; ngưỡng 90/60/30 ngày là câu Q-L7 | [nghiên cứu mục 4.2, 9](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) | Chưa làm |
