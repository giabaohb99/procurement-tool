# Câu hỏi mở cho đại ca — D0 / D1 (plan đi theo MẶC ĐỀ XUẤT nếu chưa chốt)

| # | Câu hỏi | Mặc định đề xuất | Lý do | Phase |
|---|---|---|---|---|
| Q1 | Bật lại công tắc thu sự kiện giao diện trên prod (đang tắt từ 20/10) khi nào? | Bật sau khi thông báo nhân viên mục đích «cải tiến phần mềm, không chấm điểm» (doc 22 §6), ngay khi D0a+D0b lên prod | Tắt thì báo cáo theo chức năng rỗng | 01–03 |
| Q2 | Định nghĩa «xong» từng loại phiếu chốt ngay hay để sau? | Chốt ngay theo bảng ở phase 06; riêng YCBG lấy `done` (không phải `survey_done`) | Là cấu hình — đổi 1 dòng + chạy lại backfill | 06 |
| Q3 | Ai khai danh mục loại việc của Dự án? | Quản trị khai (gác `setting.write`); trưởng phòng đề xuất ngoài hệ thống. Mở cho trưởng phòng sau T1 | Ít quyền mới, ít entity mới | 05 |
| Q4 | «Nhận hàng» đo thế nào khi không có form/vòng đời riêng? | Form = dialog dòng ĐMH (nhãn «Nhận hàng (dòng ĐMH)»); KHÔNG tính thời gian trọn vòng cho nhận hàng | Nhận hàng là một bước của ĐMH | 02, 06 |
| Q5 | Tải đang ôm có tính việc được ủy quyền không? | Việc tính ở người ủy quyền; người được ủy quyền thấy thêm số riêng `delegated_in` | Không đếm trùng, AI vẫn thấy | 07 |
| Q6 | Duyệt Thu mua (YCMH/YCBG/ĐMH) không gán người duyệt — tính tải duyệt thế nào? | YCMH theo `head_of_dept_id` (đại diện); YCBG/ĐMH không tính theo người | Không có cột người duyệt; tính `apply_scope` từng người quá đắt | 07 |
| Q7 | Báo cáo theo chức năng (khóa 15): chỉ admin hay cả trưởng phòng? Có xem theo từng người không? | Chỉ admin; chỉ theo phòng ban, không theo từng người (muốn xem người → hồ sơ khóa 14) | Khớp chốt 20/10 «chỉ quản trị» | 03 |
| Q8 | Ai xem thời gian trọn vòng / tải theo từng người (khóa 16)? | Chỉ admin; người khác chỉ thấy đề xuất của AI (doc 22 §6). Số theo người chỉ khi ≥ 5 mẫu | Tránh dùng số để phạt | 08 |
| Q9 | «Phiếu do AI soạn» trước khi có A0? | Đếm tổng từ `tab_assistant_change` (CREATE/REUSE) ngay; tách kênh chờ A0 sửa `source` MCP + cờ `via_ai` | MCP đang bị ghi là Telegram | 04 |
| Q10 | Task nhiều PIC: giờ thực tế và thời gian trọn vòng chia thế nào? | Mỗi PIC một dòng cùng thời gian trọn vòng; giờ thực tế là của cả task (không chia), chỉ dùng ở mức loại việc | Không có chấm giờ theo người | 05, 06 |
| Q11 | «Tải» có quy ra một con số tổng có trọng số không? | Không — trả các số thành phần + tổng đếm thô; AI tự cân và giải thích | Máy tính số, AI viết chữ; tránh trọng số tùy tiện | 07 |
| Q12 | Thời gian trọn vòng tính theo ngày lịch hay ngày làm việc (trừ lễ, nghỉ)? | Ngày lịch ở bản đầu; ngày làm việc để sau (đã có lịch làm việc + lễ ở `usage_profile`) | Giữ D1 trong 1,5 tuần | 06, 08 |
| Q13 | Giờ thực tế của task có bắt buộc khi đánh dấu xong? | Không bắt buộc, nhắc nhẹ; số chính là thời gian trôi qua | Bắt buộc dễ bị nhập bừa | 05 |
| Q14 | Có cần nhóm 3.7 trong hồ sơ cách làm việc hay chỉ báo cáo khóa 16? | Chỉ báo cáo khóa 16; 3 khóa 3.7 trong hồ sơ là tùy chọn (+0,5 ngày) | YAGNI; AI đọc thẳng từ hàm năng lực | 08 |
