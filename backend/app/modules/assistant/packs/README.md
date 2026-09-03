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

## Gói tri thức theo PHÂN HỆ

Ngoài gói của nhà máy, mỗi phân hệ nghiệp vụ có thể có một gói riêng — chỗ ghi **luật
mà trợ lý không được nói sai**. Các bước bấm nút chi tiết KHÔNG để ở đây: chúng nằm ở
Help Center và trợ lý tra bằng `search_docs` (RAG index `help_article` + FAQ).

| Tệp | Phân hệ | Token đo được |
|---|---|---|
| `10-quy-trinh-thu-mua.md` | Thu mua | ~830 |
| `20-van-thu-van-ban.md` | Văn thư | ~3 100 |
| `30-du-an-cong-viec.md` | Dự án (quản lý công việc) | ~2 300 |
| `nhamay-tri-thuc-co-dong.md` | Nhà máy DEGO Organic | ~11 000 |

Tổng system prompt hiện ~**17,7k token/lượt** (đo 03/09/2026 bằng
`knowledge.build_system()`, ước 3,2 ký tự/token cho tiếng Việt).

Viết gói phân hệ thì bám ba nguyên tắc:

1. **Chỉ ghi thứ trợ lý dễ nói sai** — trạng thái nào khoá sửa, ai được bấm nút nào,
   từ nào dùng đúng như trên màn hình. Thứ tra được ở HDSD thì đừng chép lại.
2. **Ghi cả điều CẤM nói.** Ví dụ Văn thư: hệ trả 404 thay vì 403 khi không đủ quyền
   đọc, nên trợ lý **không được nói "văn bản không tồn tại"**; và tuyệt đối không tiết
   lộ đơn nghỉ phép của người khác.
3. **Bảng từ dùng đúng** — dùng sai từ là người dùng tìm không ra nút.

⚠️ Không có bài kiểm tự động nào ràng buộc nội dung gói. Sửa xong nên hỏi thử trợ lý
vài câu thật để đối chiếu.

## Gói tri thức Nhà máy DEGO Organic

- `nhamay-tri-thuc-co-dong.md` là bản CHƯNG CẤT từ bộ 11 tài liệu gốc của nhà máy
  (quy định hệ thống công việc QĐ.HT.01, hướng dẫn vận hành trợ lý HD.HT.01, gói hợp
  nhất...). Giữ nguyên văn mọi quyết định / quy tắc / định nghĩa / bộ câu hỏi / mã tài
  liệu; bỏ phần lặp, biểu mẫu trống, ví dụ. Đo thật: ~12k input token/lượt, giảm ~81%
  so với nạp cả 11 file (~65k).
- 11 file gốc KHÔNG để trong thư mục này (kẻo bị nạp chồng cả 65k + 12k token). Chúng
  nằm ở `../knowledge-source/` — không bị bộ nạp đọc, giữ lại để làm RAG/tra chi tiết
  sau. Chưng cất thì mất chi tiết: câu hỏi sâu ngoài phần đã giữ, bot sẽ nói "không có
  trong tài liệu" thay vì bịa — đây là đánh đổi có chủ đích.
