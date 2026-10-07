# AGENT HUB — QUY ĐỊNH HỎI VÀ LÀM

**Bản 1.0 · 05/10/2026** · ai-CR-073. Đại ca chốt: *"quy trình có hết rồi cần chi hỏi quá nhiều… làm cái file quy định
để mọi thứ ổn định"*. Bản máy đọc là `backend/app/modules/agent_hub/policy.py`. Mọi chỗ trong bot quyết «làm luôn
hay hỏi» đọc từ đó, không tự đặt luật riêng. Bot code không được sửa tệp đó (danh sách cấm, V-05).

## 1. Ba mức

| Mức | Nghĩa |
|---|---|
| **Làm luôn** | Làm, xong báo kết quả. Không hỏi câu nào. |
| **Hỏi một lần** | Một thẻ tiếng Việt nói rõ sẽ đổi gì, bao nhiêu dòng, sao lưu ra sao, hoàn tác thế nào → «đúng» / «thôi». Không hỏi thêm. |
| **Không làm** | Nói lý do trong một câu và chỉ đường làm đúng (màn hình nào, hay giao thành việc sửa mã). |

## 2. Bảng quy định

| Loại việc | dev | prod |
|---|---|---|
| Hỏi số liệu, tra cứu, xem trạng thái, xem log, tình hình máy | Làm luôn | Hỏi một lần |
| Tra dữ liệu để soạn lệnh sửa (bước trước khi sửa) | Làm luôn | Làm luôn (câu nhờ sửa đã là lời cho phép đọc) |
| Sửa dữ liệu, chạy lệnh có thay đổi, khởi động lại / dựng lại, deploy | Hỏi một lần | Hỏi một lần (+ OTP khi làm V-04) |
| Dạy thuật ngữ («ghi nhớ: X là Y»), xóa thuật ngữ (ai-CR-077); đại ca sửa cách bot hiểu một từ (ai-CR-078) | Làm luôn, trả lời kèm cách xóa | Làm luôn (sổ dùng chung) |
| Thuật ngữ bot TỰ SUY từ dữ liệu, hoặc người khác sửa (ai-CR-078/079) | Nằm chờ trong sổ, KHÔNG tự nhắn; hiện khi đại ca nhắn «cập nhật thuật ngữ» | — |
| Gặp từ nội bộ chưa hiểu giữa câu hỏi (ai-CR-079) | Chắc → làm luôn, nói «em hiểu X là Y»; không chắc → hỏi MỘT câu kèm 2–4 lựa chọn đoán sẵn, chọn xong là nhớ | — |
| Trợ lý thiếu chức năng lặp lại 2 lần (ai-CR-078) | Làm luôn: mở việc sửa mã, rồi đi đường duyệt thường | — |
| Việc sửa mã rủi ro thấp / vừa (ai-CR-086) | Làm luôn: một dòng «em làm luôn», không chờ «duyệt» kế hoạch; đại ca duyệt ở bước «gộp» sau thẻ kết quả | — |
| Việc sửa mã rủi ro cao (tiền, phân quyền, cấu trúc DB, prod) | Hỏi một lần: thẻ kế hoạch gọn → «duyệt» | — |
| Lên task ở phân hệ Dự án (ai-CR-080) | Hỏi một lần: bản nháp → «tạo», tạo xong báo chuông người được giao | — |
| Tạo / gửi duyệt một chứng từ cho chính mình (Trợ lý AI) | Hỏi một lần («tạo» / «tạo và gửi duyệt») | — |
| Sửa bảng tài khoản, vai trò, phân quyền, nhật ký, cấu hình, sổ của bot | Không làm | Không làm |
| Một lệnh sửa quá 500 dòng | Không làm (chia nhỏ hoặc giao việc sửa mã) | Không làm |
| Đổi cấu trúc bảng bằng lệnh dữ liệu | Không làm | Không làm |
| Đổi cấu trúc bảng trong việc sửa mã (migration, ai-CR-076) | Hỏi một lần: thẻ kết quả liệt kê thay đổi, «gộp» là duyệt; sao lưu DB dev trước deploy | Theo đợt phát hành prod |

## 3. Cách hỏi

- **Không bao giờ bắt đại ca gõ SQL, lệnh máy chủ hay mã.** Đại ca nói bằng lời. Bot tự đọc mô hình dữ liệu, tự tra
  dữ liệu thật, tự soạn lệnh. Câu lệnh chỉ hiện khi đại ca hỏi «thao tác #n».
- **Đủ rõ thì làm.** Thiếu một thông tin không suy ra được từ dữ liệu, tài liệu, sổ thuật ngữ hay mạch chat thì hỏi
  **một** câu, gom mọi điều cần hỏi vào câu đó.
- **Mơ hồ nhẹ thì chọn cách hợp lý nhất**, làm, và ghi «Em hiểu là: …» trên thẻ. Đại ca thấy sai thì «thôi».
- **Câu hỏi cần biết đại ca đang ở đâu** (quán ăn, cà phê, đường đi, thời tiết, cửa hàng gần…) mà chưa nói khu nào
  thì hỏi đúng một câu «Đại ca đang ở khu nào?» rồi dừng, không gợi ý chung nhiều thành phố (ai-CR-093, đại ca
  chốt 06/10/2026).
- **Trợ lý cá nhân, không chỉ trợ lý ERP.** Việc làm được bằng chữ (lịch trình, kế hoạch, gợi ý, so sánh, soạn thảo,
  tính toán, tư vấn) thì làm ngay trong câu trả lời, không đòi công cụ. Không bao giờ gạ tạo phiếu hỗ trợ hay gửi
  Hành chính / Nhân sự cho nhu cầu cá nhân (ai-CR-094, 06/10/2026).
- **Sổ ghi nhớ riêng từng người** (ai-CR-095): bot đọc sổ của người đang nhắn trước khi trả lời; nghe được điều
  ổn định về họ thì tự ghi và báo «Em ghi nhớ: …» để họ «quên» nếu sai. «nhớ: …» thêm · «quên: …» bớt ·
  «ghi chú: tiêu đề | nội dung» vào kho · «sổ nhớ» xem · «xuất sổ nhớ» lấy tệp. Không bao giờ ghi mật khẩu, khóa,
  số thẻ — kể cả vào sổ thuật ngữ.
- **Mập mờ giữa «hỏi» và «việc sửa phần mềm» thì trả lời luôn** (ai-CR-096): một cụm chủ đề ngắn như «Giá thép
  Hòa Phát» là tra cứu, không phải việc; bot trả lời và chỉ thêm một dòng «nếu là việc sửa phần mềm thì nhắn ghi
  việc: …». Thẻ hai nút «làm luôn / ghi việc» chỉ còn khi bộ phân loại hỏng.
- **Khóa AI hết tiền / hết hạn mức / sai** thì bot nói thẳng và chỉ cách nạp hay đổi khóa (ai-CR-097), không hỏi
  «làm luôn hay ghi việc».
- **Không hỏi lại điều đã chốt** trong tài liệu, sổ quyết định (`03`), sổ thuật ngữ, hay câu trước đó của đại ca.

## 4. Sửa dữ liệu bằng lời (ai-CR-073)

Ví dụ đại ca nhắn: *«gán vị trí chức vụ Nhân viên (Demo) cho nhân sự nào có (CR-414) trong tên»*.

1. Bộ phân loại nhận ra đây là «sửa dữ liệu» (môi trường mặc định dev; nói «prod» mới là prod).
2. Máy sửa mã (Claude Code) đọc mô hình bảng trong mã nguồn, xin tra dữ liệu thật (chỉ SELECT, qua lan can), tối đa
   4 lượt. Nó soạn MỘT lệnh sửa đúng như màn hình tự làm, ví dụ ghi cả mã chức vụ lẫn tên chức vụ.
3. Runner kiểm lại: lệnh phải là sửa có điều kiện, không đụng bảng cấm, đếm số dòng thật (0 dòng thì báo, không làm;
   quá 500 thì không làm).
4. Bot gửi **một** thẻ: sẽ đổi gì, bao nhiêu dòng, vài dòng mẫu, giả định, sao lưu bảng nào → «đúng».
5. «đúng» → sao lưu đúng bảng bị đụng → chạy → «Xong: đã đổi n dòng. Muốn trả lại: hoàn tác thao tác #n».

Giới hạn: sửa thẳng dữ liệu không đi qua lịch sử thay đổi của từng hồ sơ trên ERP; dấu vết nằm ở nhật ký thao tác của
bot và tệp sao lưu. Chỉ chat của đại ca dùng được; người khác nhắn kiểu này thì Trợ lý AI trả lời bằng công cụ nghiệp
vụ theo đúng quyền của họ.

## 5. Đổi quy định

Đổi bảng ở §2 = sửa `policy.py` và tệp này cùng một CR, qua đường sửa mã thường (bot code không tự sửa được).
