# Gói tri thức Trợ lý AI (AI-1)

Thư mục này chứa NỘI DUNG tri thức mà trợ lý nạp vào phần `system` mỗi lượt hỏi
(kèm prompt caching để lượt sau rẻ). Đây là cách làm của AI-1: không vector, chỉ
nhồi thẳng tài liệu đứng yên vào ngữ cảnh.

## Cách dùng

- Mỗi tệp `.md` trong thư mục này là một mảng tri thức. Bộ nạp đọc TẤT CẢ tệp `.md`
  theo thứ tự tên tệp rồi ghép lại (nên đánh số tiền tố: `10-...`, `20-...`).
- Tệp `README.md` này KHÔNG được nạp (bị loại theo tên).
- Sửa nội dung là có hiệu lực ngay lượt hỏi kế (bộ nạp không cache theo tiến trình —
  xem `knowledge.py`, đọc lại đĩa mỗi lần để dễ cập nhật khi vận hành).

## Giới hạn Phase 1

- Toàn bộ gói đi vào MỌI câu hỏi. Gói càng to, token nạp càng nhiều — nhờ prompt
  caching (Claude) / cache ngầm (Gemini 2.5+) nên lượt sau rẻ, nhưng vẫn nên giữ gói
  gọn, đúng trọng tâm.
- "Quyền theo gói" (mỗi nhóm người dùng thấy gói khác nhau) là việc của Phase sau —
  hiện mọi người có quyền `assistant.read` dùng chung một gói.
