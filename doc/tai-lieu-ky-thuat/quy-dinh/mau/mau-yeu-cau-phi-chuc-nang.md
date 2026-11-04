# YÊU CẦU PHI CHỨC NĂNG — <TÊN PHÂN HỆ>

| | |
|---|---|
| Bản | 1.0 |
| Ngày | DD/MM/YYYY |
| Người phụ trách | <tên> |
| Trạng thái | Nháp / Hiệu lực |
| CR liên quan | <mã CR> |

Mỗi yêu cầu một mã `PCN-<PHÂN HỆ>-NN`, ghi **mức đo được** và **cách kiểm** (bài kiểm nào, đo thế nào). Mục nào không áp dụng thì ghi *Không áp dụng* kèm lý do, đừng xóa mục.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-XX-01 | Hiệu năng | Ví dụ: danh sách 20 dòng trả về dưới 1 giây với 10.000 bản ghi; số truy vấn mỗi trang cố định, không tăng theo số dòng | Bài kiểm đếm truy vấn `test_...` | Đạt / Chưa đo / Chưa đạt |
| PCN-XX-02 | Phân quyền | Khóa quyền dùng: `<entity>`; phạm vi theo `SCOPE_FIELDS`; lấy một bản ghi qua `get_scoped` | `test_pham_vi_...` | |
| PCN-XX-03 | Dữ liệu nhạy cảm | Trường nào bị che, ai được xem; không vào nhật ký / tệp xuất | | |
| PCN-XX-04 | Giới hạn đầu vào | Độ dài chuỗi (`max_length` khớp `String(n)`), số dòng con tối đa, cỡ tệp tải lên | Kiểm ở tầng schema | |
| PCN-XX-05 | Nhật ký và truy vết | Thao tác nào ghi `audit`, có hoàn tác không | | |
| PCN-XX-06 | Lưu trữ và dọn dữ liệu | Giữ bao lâu, việc chạy ngầm nào dọn, xóa mềm hay xóa cứng | | |
| PCN-XX-07 | Sao lưu và khôi phục | Nằm trong bản sao lưu DB nào, tệp đính kèm ở đâu | | |
| PCN-XX-08 | Đồng thời | Hai người sửa cùng lúc thì sao (khóa, kiểm phiên bản, UNIQUE) | | |
| PCN-XX-09 | Tích hợp | Hệ ngoài / phân hệ khác gọi vào hoặc được gọi; xử lý khi bên kia lỗi | | |
| PCN-XX-10 | Khả dụng và thiết bị | Dùng trên điện thoại được không, trình duyệt hỗ trợ | | |
| PCN-XX-11 | Pháp lý | Văn bản luật áp dụng (lao động, BHXH, hóa đơn, bảo vệ dữ liệu cá nhân…) | | |
| PCN-XX-12 | Vận hành | Việc chạy ngầm (Celery beat) liên quan, cảnh báo khi lỗi | `/api/system/jobs` | |
