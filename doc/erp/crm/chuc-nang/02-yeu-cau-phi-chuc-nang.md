# YÊU CẦU PHI CHỨC NĂNG — CRM

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-CRM-NN`, ghi **mức đo được** và **cách kiểm**. Phân hệ chưa có mã nên cột *Hiện trạng* đều là
*Chưa đo*; yêu cầu nào chưa có nguồn ghi *Chưa có*. Nguồn chính: mục 4 và 7 của [kế hoạch CRM](../plans/00-ke-hoach-crm.md).

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-CRM-01 | Hiệu năng | Chưa có. Lượng tin và cuộc gọi mỗi ngày chưa biết (câu hỏi 3 của kế hoạch) | Chưa có | Chưa đo |
| PCN-CRM-02 | Phân quyền | Nhân viên thấy hội thoại của mình; trưởng nhóm thấy cả nhóm; quản lý thấy theo thương hiệu (đề xuất, chờ câu hỏi 6). Dùng phân quyền hai trục có sẵn (`core/auth.py`, `core/scoping.py`); entity mới phải khai đủ phạm vi; báo cáo CSKH gác thêm `require_report` | [Kế hoạch CRM](../plans/00-ke-hoach-crm.md) CRM-3, CRM-6, §3; `test_pham_vi_khai_du_b07.py` | Chưa đo |
| PCN-CRM-03 | Dữ liệu nhạy cảm | Số điện thoại, tin nhắn, ghi âm của khách là dữ liệu cá nhân: có sự đồng ý của khách, giới hạn người xem, nhật ký truy cập, thời hạn lưu. Khóa / thông tin kết nối của tài khoản kênh lưu mã hóa, không hiện trên màn | [Kế hoạch CRM](../plans/00-ke-hoach-crm.md) CRM-3, §7 | Chưa đo |
| PCN-CRM-04 | Giới hạn đầu vào | Cột `String(n)` phải có `max_length` khớp ở schema; cỡ tệp / ảnh gửi qua hộp thư: chưa có | [`backend-input-limits.md`](../../../../.claude/rules/backend-input-limits.md) | Chưa đo |
| PCN-CRM-05 | Nhật ký và truy vết | Nhật ký truy cập dữ liệu khách (yêu cầu bảo vệ dữ liệu cá nhân); mỗi cuộc gọi ghi vào dòng thời gian khách (thời lượng, người nghe, ghi âm, gọi nhỡ) | [Kế hoạch CRM](../plans/00-ke-hoach-crm.md) CRM-4, §7 | Chưa đo |
| PCN-CRM-06 | Lưu trữ và dọn dữ liệu | Cần chính sách lưu trữ / dọn hội thoại và nhật ký cuộc gọi cũ (giống nhật ký nạp, CR-698); thời hạn giữ ghi âm chờ câu hỏi 5. Số ngày cụ thể: chưa có | [Kế hoạch CRM](../plans/00-ke-hoach-crm.md) §6, §7 | Chưa đo |
| PCN-CRM-07 | Sao lưu và khôi phục | Chưa có. Nơi lưu tệp ghi âm: chưa có | Chưa có | Chưa đo |
| PCN-CRM-08 | Đồng thời | Chưa có. Hai nhân viên nhận cùng một hội thoại: chưa có luật | Chưa có | Chưa đo |
| PCN-CRM-09 | Tích hợp | Zalo OA và bot Telegram cắm vào lớp kênh có sẵn của dịch vụ AI; tổng đài ảo qua webhook vào ERP và API của nhà cung cấp, bọc lớp trung gian để đổi nhà cung cấp không phải sửa ERP. Điều kiện gửi tin chủ động và biểu phí Zalo OA / ZNS phải kiểm lại lúc làm GĐ0. Xử lý khi bên kia lỗi: chưa có | [Kế hoạch CRM](../plans/00-ke-hoach-crm.md) CRM-2, CRM-4, §7 | Chưa đo |
| PCN-CRM-10 | Khả dụng và thiết bị | Gọi và nghe bằng app điện thoại hoặc trên trình duyệt (tổng đài ảo) | [Kế hoạch CRM](../plans/00-ke-hoach-crm.md) CRM-4 | Chưa đo |
| PCN-CRM-11 | Pháp lý | Bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP và luật mới về bảo vệ dữ liệu cá nhân (nhờ pháp chế kiểm điều khoản hiện hành); phải có lời thông báo ghi âm cho khách; tuân điều khoản Zalo khi nhắn khách số lượng lớn | [Kế hoạch CRM](../plans/00-ke-hoach-crm.md) CRM-2, §6 câu 5, §7 | Chưa đo |
| PCN-CRM-12 | Vận hành | Chưa có. Mỗi giai đoạn lên dev thử với một nhóm CSKH nhỏ trước khi lên prod | [Kế hoạch CRM](../plans/00-ke-hoach-crm.md) §5 | Chưa đo |
