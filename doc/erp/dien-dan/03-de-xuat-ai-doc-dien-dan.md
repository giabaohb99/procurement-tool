# ĐỀ XUẤT — TRỢ LÝ AI ĐỌC DIỄN ĐÀN (GHI NỢ, CHƯA LÀM)

Ngày ghi: 03/09/2026. Trạng thái: **đề xuất đã chốt hướng, chưa xếp lịch làm** — ghi nợ ở đây
để khỏi quên, khi nào làm thì cấp số CR (re-grep change-log ngay trước khi cấp).

## 1. Ý tưởng gốc và ranh giới

Sếp hỏi: biến diễn đàn thành nơi tìm kiếm / tổng hợp tri thức cho bot học. Đánh giá đã chốt
qua trao đổi 03/09/2026 — tách làm hai tầng, chỉ làm tầng 1:

- **LÀM: cho bot ĐỌC diễn đàn lúc trả lời** (retrieval qua tool, có phân quyền). Bot không
  "học" theo nghĩa huấn luyện — chỉ tìm rồi đọc tại thời điểm trả lời.
- **KHÔNG LÀM: coi bài diễn đàn là nguồn tri thức ngang tài liệu.** Diễn đàn ai cũng đăng,
  không duyệt trước (QĐ-D1), có câu trả lời sai chưa ai đính chính — bài học search_docs
  từng phải tắt vì 66 bài HDSD (nội dung ĐÃ biên tập) còn ra 20 lỗi. Tri thức muốn vào gói
  AI-1 phải đi đường **chưng cất**: thread hay → người duyệt thăng cấp thành bài HDSD /
  văn bản Văn thư (mục 3).

## 2. Tầng 1 — hai tool đọc cho trợ lý (việc chính của đề xuất)

Theo khuôn tool trợ lý sẵn có (T25–T34, xem CR-218):

| Tool | Làm gì | Ghi chú |
|---|---|---|
| `forum_search` | Bọc hàm search CR-263 (`forum/service`), **ép quyền theo người đang hỏi** qua `_visible_cond` ngay trong SQL | Trả danh sách GỌN: tiêu đề, trích đoạn, tác giả, ngày, box, số bình luận, link — KHÔNG trả nguyên bài (phí token). Chỉ bài PUBLISHED |
| `forum_post_read` | Đọc nguyên văn MỘT bài + **cây bình luận** (bộ `/api/comments` entity `forum_post` sẵn có) | Bài hỏi-đáp thì câu trả lời nằm ở BÌNH LUẬN chứ không ở bài gốc — thiếu comment là bot recap ra toàn thắc mắc |

Việc kèm theo:

1. **Mở rộng search sang nội dung bình luận** — CR-263 hiện chỉ quét title+body của bài.
   Phần backend mới duy nhất có tí thịt.
2. **Hint dạy bot rào nguồn**: mọi câu trả lời lấy từ diễn đàn phải kèm link bài + câu
   "theo thảo luận trên diễn đàn, chưa phải tài liệu chính thức". Cấp độ tin: tài liệu
   đã duyệt (HDSD/Văn thư) > bài diễn đàn.
3. Bài rich text (`body_format=1`) phải bóc HTML trước khi đưa vào context
   (`strip_html_text` phía backend có sẵn).

Vì sao tách 2 tool thay vì 1 tool "search kiêm recap": recap là việc của model, API chỉ đưa
dữ liệu thô — cùng cặp tool phục vụ đủ kiểu câu hỏi (recap thread, "tuần rồi có gì mới",
"ai từng hỏi X chưa") mà không phải đẻ endpoint cho từng kiểu.

Khối lượng ước lượng: nhỏ hơn CR-263 — 2 hàm tool + mở rộng search comment + hint;
không migration, không quyền mới (tool chạy dưới quyền người hỏi).

## 3. Tầng 2 — chưng cất tri thức (để sau, chỉ ghi hướng)

Thread giá trị (prefix «kiến thức», hỏi-đáp có câu trả lời được xác nhận) → forum_admin /
người phụ trách HDSD thăng cấp thành bài HDSD hoặc văn bản Văn thư — đó mới là nguồn vào
gói tri thức AI-1 [[ai-rag-tro-ly-tai-lieu]]. Có thể thêm nút «Đề xuất đưa vào HDSD» trên
thread về sau, nhưng khâu duyệt luôn là người. Không làm gì ở đợt này.

## 4. Điều kiện đủ khi làm tầng 1

- Người thường hỏi bot về bài `dept` phòng khác → bot KHÔNG thấy (kiểm bằng 2 tài khoản).
- Bot recap thread hỏi-đáp lấy được nội dung từ bình luận, kèm link + câu rào nguồn.
- Bài ẩn/gỡ không lọt vào kết quả tool.
