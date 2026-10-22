---
name: he-agent-cai-tien
description: Chạy mỗi tuần (hoặc khi người chủ bảo) để hệ agent học: đọc sổ quyết định, đề xuất nâng / hạ mức tự quyết cho từng loại việc, gom bài học thành bài kiểm hoặc luật, rút gọn tệp hướng dẫn, và đo xem số lần phải hỏi người chủ có giảm không.
---

# Cải tiến hằng tuần

Đây là nơi hệ **khôn lên**: không phải thêm skill, mà là biến kinh nghiệm (sổ quyết định, lỗi lọt) thành quyền tự làm rộng hơn và luật chặt hơn.

## Các bước

1. **Đo tuần qua** (từ sổ quyết định, sổ task, git):
   - Số câu đã hỏi người chủ; so với tuần trước (mục tiêu: giảm).
   - Số việc xong; số việc phải làm lại; số lần hoàn tác.
   - Lỗi rà mã bắt được trước khi gộp; lỗi lọt lên prod.
2. **Đề xuất nâng mức:** mục C của sổ — loại việc có **≥ 5 lần `gật` liền**, không lần hoàn tác nào → đề xuất nâng một bậc (M1 → M2 → M3). Trình người chủ một danh sách, mỗi dòng: loại việc · mức hiện tại → mức mới · bằng chứng (các dòng sổ). **Không bao giờ đề xuất nâng việc ở sàn.**
3. **Hạ mức ngay** (không chờ tuần): loại việc nào trong tuần có một lần làm sai phải hoàn tác → hạ một bậc, đặt đếm về 0, báo người chủ.
4. **Áp sau khi người chủ gật:** sửa bảng hạn mức trong tệp cấu hình người chủ + mục C của sổ; ghi dòng quyết định vào mục B.
5. **Gom bài học:**
   - Lỗi lọt / lỗi rà mã lặp lại → **bài kiểm canh** hoặc luật ở `.claude/rules/` (luật quan trọng phải thành bài kiểm chạy tự động; lời dặn trong CLAUDE.md giúp nhanh hơn chứ không đúng hơn).
   - Tiền lệ trùng nhau trong sổ → gộp thành một dòng rõ phạm vi.
   - Bẫy mới → thêm vào mục *Bẫy đã gặp* của skill liên quan.
6. **Giữ gọn tệp hướng dẫn:** CLAUDE.md và luật dài thì rút ý trùng, chuyển chi tiết theo khu vào `.claude/rules/<khu>.md` (chỉ nạp khi đụng khu đó).
7. **Báo người chủ** theo mẫu báo cáo xong việc: số liệu tuần · đề xuất nâng mức (cần gật) · bài học đã áp.

## Kiểm đã làm đúng

- Tuần nào cũng có số *câu đã hỏi* để so; xu hướng giảm sau vài tuần.
- Không có thay đổi hạn mức nào được áp mà chưa có lời gật của người chủ.

## Bẫy

- **Đừng nâng mức vì *chắc là được*.** Chỉ nâng khi sổ có đủ lần `gật` không sửa cho đúng loại việc. Ngưỡng 5 là khởi đầu cho đội nhỏ có người chủ duyệt; nghiên cứu dùng ngưỡng thống kê chặt hơn (khoảng 35 lần liền).
- **Đổi model / đổi luật lớn** thì xem lại các mức đã nâng — hành vi agent có thể đổi theo.
