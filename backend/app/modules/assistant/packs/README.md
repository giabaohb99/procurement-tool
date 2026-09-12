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
| `40-nghi-phep.md` | Nghỉ phép (Nhân sự) | ~3 360 (12/09/2026: + mục tool `my_leave_summary` và `draft_leave_request`) |
| `50-dat-phong-hop.md` | Đặt phòng họp (Nhân sự) | ~1 900 |
| `60-nhan-su-ho-so.md` | Hồ sơ nhân sự + danh mục Chức vụ | ~1 670 (12/09/2026: + mục tool `employee_lookup`) |
| `nhamay-tri-thuc-co-dong.md` | Nhà máy DEGO Organic | ~11 000 |

⚠️ **`60-nhan-su-ho-so.md` cố ý chỉ giữ LUẬT, không giữ các bước bấm nút** — đúng
luật của thư mục này. Các bước nằm ở bài Help Center *«Chức vụ và hồ sơ nhân
sự»*, trợ lý tra bằng `search_docs`. Chia đôi như vậy vì gói đi vào **mọi** câu
hỏi (kể cả câu chẳng liên quan tới nhân sự), còn bài HDSD thì chỉ được nạp khi
đúng chủ đề. Thứ phải nằm trong gói là thứ **nói sai thì người dùng làm hỏng dữ
liệu thật** — ví dụ "đổi tên một chức vụ là đổi luôn chức danh của mọi người đang
giữ nó".

⚠️ **Hồ sơ nhân sự đi vào trợ lý bằng BA đường, đếm cho đủ** (cập nhật
12/09/2026 — bản trước ghi "chỉ 5 trường của chính người hỏi", nay đã hết hạn):

1. **Chân dung người hỏi** — 5 trường của **chính họ** (`service.py`
   `_caller_context`: họ tên · mã NV · chức vụ · phòng ban · công ty).
2. **`full_name` của người duyệt** (`document_tool`).
3. **Tool `employee_lookup`** (T45, bao-CR-386) — đường đầu tiên đọc hồ sơ
   **NGƯỜI KHÁC**: 12 trường danh bạ, gác bằng `employee.read` + `apply_scope`.

Cả ba đường **không** chạm trường nào thuộc nhóm nhạy cảm (CCCD · ngân hàng ·
địa chỉ nhà — xem `employee/sensitive.py`). Đường 3 giữ được điều đó bằng
**danh sách trắng** `_OUT_FIELDS` chứ không bằng may mắn, và vẫn chạy thêm một
lượt `sensitive.mask_many` làm chốt dự phòng. Thêm trường vào bất kỳ đường nào
thì phải kiểm lại đúng chỗ đó. Lưu ý `emp.position` là **nhãn đã chép**, không
phải khóa — đúng một trong những lý do cột nhãn còn tồn tại.

Tổng system prompt hiện ~**23,5k token/lượt** — 75 130 ký tự, đo lại 12/09/2026
bằng `knowledge.build_system()` (ước 3,2 ký tự/token cho tiếng Việt). Lần trước
ghi ~22,8k (72 928 ký tự), chênh là do hai mục hướng dẫn gọi tool thêm vào gói
Nghỉ phép và gói Nhân sự (bao-CR-386).

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
