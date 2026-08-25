# Tài liệu gốc Nhà máy DEGO Organic (KHÔNG nạp vào bot)

Thư mục này giữ 11 file tri thức GỐC của nhà máy, đã chuyển từ bộ tài liệu khách
đóng gói (`.docx` 01/02/03 → text, `.md` 04-11 copy thẳng).

## Vì sao để ở đây, không để trong `../packs/`

Bộ nạp `knowledge.py` (`load_pack`) đọc TẤT CẢ `packs/*.md` mỗi lượt hỏi. Nếu để 11
file này trong `packs/`, bot nạp ~65k token/lượt — quá tốn. Bản dùng thật là bản
CHƯNG CẤT `../packs/nhamay-tri-thuc-co-dong.md` (~12k token, giảm ~81%), giữ nguyên
văn mọi quyết định/quy tắc/định nghĩa/bộ câu hỏi/mã tài liệu.

`glob("*.md")` KHÔNG đệ quy, nên thư mục sibling này không bị nạp — an toàn.

## Dùng để làm gì

- Nguồn tra chi tiết khi bản cô đọng thiếu (bot nói "không có trong tài liệu").
- Nguồn để index sang RAG/vector (loại B) ở Phase sau — xem kế hoạch trợ lý AI.

Đừng move mấy file này lên `../packs/` trừ khi cố ý muốn nạp lại toàn bộ.
