# Sổ quyết định của đại ca cho bot

> Bản 1.0 · 23/09/2026 · ai-CR-015. Đi cùng [`02-bo-quy-tac-bot.md`](02-bo-quy-tac-bot.md).

Sổ này ghi những quyết định **quen thuộc** của đại ca, để bot tra trước khi hỏi. Gặp chỗ chưa
rõ, bot (cả bot quản lý lập kế hoạch lẫn Claude Code sửa mã) tìm mục khớp ở đây: có thì làm
theo và ghi rõ trong kế hoạch hoặc tổng kết **"Theo QĐ-xx: …"**; không có mà có một cách làm
hợp lý, an toàn, dễ đảo lại thì chọn nó và ghi **"Em giả định: …"**. Chỉ khi không có đường
nào như vậy bot mới hỏi.

## Ba luật của chính cuốn sổ (đại ca chốt 23/09/2026)

1. **Bot chỉ đề xuất ghi, đại ca bấm đồng ý mới thành luật.** Sau khi đại ca trả lời một câu
   bot hỏi lại, bot gửi thẻ «Lần sau gặp tương tự em tự làm vậy nhé?» kèm bản nháp mục mới.
   Bấm «Ghi vào sổ» thì mục đó được nối vào cuối tệp này; bấm «Không, lần nào cũng hỏi» thì thôi.
2. **Sổ nằm trong kho mã**, sửa tay được, có commit và lịch sử. Muốn gỡ hay sửa một mục: sửa
   thẳng tệp này. Không ghi bí mật nào vào đây.
3. **Việc dính tiền, công nợ, thanh toán, phân quyền, cấu trúc cơ sở dữ liệu, prod, nhánh
   `main`, hay gộp mã vào nhánh nền thì LUÔN hỏi**, dù sổ ghi gì. Luật này thi hành trong mã,
   không nhờ lời dặn: việc rủi ro cao không được nạp sổ, mọi giả định của nó thành câu hỏi, và
   bot không đề xuất ghi mục nào chạm các chủ đề đó.

## Cách viết một mục

Mỗi mục mở đầu bằng dòng `## QĐ-<số> | <tiêu đề>` rồi bốn dòng: **Tình huống**, **Bot làm**,
**Không áp khi**, **Nguồn**. Số tăng dần, không dùng lại số đã gỡ. Bot đọc từ mục `QĐ-01` trở
xuống, phần trên đây chỉ để người đọc.

---

## QĐ-01 | Lỗi không tái hiện được hoặc thiếu dữ liệu mẫu
- Tình huống: đại ca báo lỗi nhưng không kèm mã phiếu, ảnh hay bước bấm; bot không tái hiện được.
- Bot làm: sửa theo mô tả bằng cách an toàn nhất, viết bài kiểm dựng lại đúng ca mô tả, ghi rõ giả định trong tổng kết.
- Không áp khi: lỗi dính tiền, công nợ, phân quyền; hoặc mô tả hiểu được theo hai cách dẫn tới hai bản sửa khác hẳn nhau.
- Nguồn: đại ca duyệt đề xuất ai-CR-015 ngày 23/09/2026.

## QĐ-02 | Cần sửa thêm tệp tài liệu cho khớp thay đổi
- Tình huống: sửa mã xong thấy tài liệu trong `doc/` hoặc tệp `.md` cạnh mã đang nói sai.
- Bot làm: sửa luôn tài liệu đó trong cùng việc; tệp `.md` không tính là lệch kế hoạch.
- Không áp khi: `CLAUDE.md`, thư mục `.claude/` (cấm sửa, luật C4).
- Nguồn: đại ca duyệt đề xuất ai-CR-015 ngày 23/09/2026.

## QĐ-03 | Chạy bài kiểm tới đâu
- Tình huống: sửa xong cần chạy bài kiểm.
- Bot làm: chỉ chạy tệp bài kiểm của phần vừa sửa; không quét cả `test/backend`, không chạy cả bộ vitest.
- Không áp khi: đại ca bảo rõ chạy hết.
- Nguồn: đại ca nhắc nhiều lần 18/08, 03/09, 17/09/2026.

## QĐ-04 | Tính năng mới hay sửa lỗi thì làm ở giao diện nào
- Tình huống: đại ca không nói làm ở `frontend/` hay `frontend-v2/`.
- Bot làm: tính năng mới làm ở `frontend-v2/`; sửa lỗi màn đang chạy thật thì sửa `frontend/` trước, phần port sang `frontend-v2/` ghi thành việc còn nợ trong tổng kết.
- Không áp khi: màn đó chỉ có ở một bản; hoặc đại ca nói rõ bản nào.
- Nguồn: D-026 ngày 13/08/2026; quy trình "v1 trước rồi mới port v2" ngày 08/09/2026.

## QĐ-05 | Cột trạng thái, loại, mức mới
- Tình huống: việc cần thêm một giá trị trạng thái, loại hay mức.
- Bot làm: dùng bộ mã số `IntEnum`, nhãn tiếng Việt chỉ ở tầng hiển thị; không lưu chữ.
- Không áp khi: cần cột mới dưới cơ sở dữ liệu (đó là migration, luôn hỏi).
- Nguồn: luật R2 / QĐ-11 ngày 22/08/2026.

## QĐ-06 | Đặt tên và câu chữ
- Tình huống: đặt tên hàm, biến, hằng, hoặc viết câu hiện cho người dùng mà đại ca không cho chữ cụ thể.
- Bot làm: tên tiếng Anh; câu hiện ra và chú thích bằng tiếng Việt trọn câu, giọng như các màn quanh đó; không emoji. Ghi câu đã chọn trong tổng kết để đại ca đọc.
- Không áp khi: đại ca đã cho sẵn câu chữ.
- Nguồn: luật đặt tên `backend/.claude/rules/naming.md`; luật không emoji.

## QĐ-07 | Câu báo lỗi cho người dùng
- Tình huống: một lỗi đang lộ nguyên văn lỗi thư viện, mã lỗi hay dấu vết mã nguồn ra màn hình.
- Bot làm: đổi thành câu tiếng Việt nói người dùng làm gì tiếp; chi tiết kỹ thuật chỉ ghi vào log.
- Không áp khi: màn quản trị cố ý hiện chi tiết cho người kỹ thuật.
- Nguồn: nợ N-009 (việc chạy thử AI-0005, 22/09/2026).

## QĐ-08 | Ô chỉ xem trên biểu mẫu
- Tình huống: cần hiện một giá trị không cho sửa.
- Bot làm: dùng `shared/ui/read-only-value.tsx`; giá trị trong ô chọn thì gắn `copy-button`. Không dùng `<Input disabled>`.
- Không áp khi: màn ở `frontend/` cũ chưa có thành phần tương đương.
- Nguồn: CR-105, ghi trong `CLAUDE.md`.

## QĐ-09 | Bộ lọc có mốc «tất cả»
- Tình huống: thêm ô lọc theo một cột tham chiếu (phòng ban, công ty, người…).
- Bot làm: dùng `-1` làm mốc «tất cả», vì `0` là nhóm «chưa gắn» thật; khai tham số mới vào danh sách cho phép của `apply_filters`; đổi bộ lọc thì kéo về trang 1.
- Không áp khi: cột đó không bao giờ bỏ trống.
- Nguồn: duoc-CR-322; bao-CR-447 (tham số ngoài danh sách cho phép bị bỏ im lặng).

## QĐ-10 | Trường chuỗi trong schema
- Tình huống: thêm hoặc sửa trường chữ ở schema Pydantic.
- Bot làm: khai `max_length` khớp đúng `String(n)` của model, để chuỗi quá dài ra lỗi 422 có câu rõ ràng thay vì lỗi 500.
- Không áp khi: cột kiểu `Text`.
- Nguồn: duoc-CR-316, ghi trong `CLAUDE.md`.

## QĐ-11 | Ghi nhận yêu cầu mới vào tài liệu
- Tình huống: việc sinh ra một tính năng hay câu trả lời thiết kế cần ghi lại.
- Bot làm: thêm dòng vào danh sách tính năng có sẵn của phân hệ đó, không đẻ tệp tài liệu mới dài.
- Không áp khi: đại ca bảo rõ muốn một tệp riêng.
- Nguồn: đại ca 13/08/2026 ("cập nhật đó vào danh sách tính năng là được rồi").
