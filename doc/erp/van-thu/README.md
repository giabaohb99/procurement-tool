# QUẢN LÝ VĂN THƯ — BỘ TÀI LIỆU

Hướng: **xây phân hệ quản lý văn bản ngay trong mã nguồn Thu mua đang chạy**, dùng lại tài khoản, nhân sự, phòng ban, pháp nhân, phân quyền, thông báo và kho tệp đã có.

Bộ tài liệu này **đảo hai quyết định cũ** của bộ thiết kế văn thư độc lập bên `quanlytailieu`:
- Trước: làm một hệ thống riêng, cơ sở dữ liệu riêng → **nay: làm trong Thu mua**.
- Trước: tuyệt đối không nhân bản văn bản xuống pháp nhân con → **nay: clone là một cơ chế hợp lệ, có kiểm soát**.

Lý do và cái giá của cả hai lần đảo nằm ở [`00` mục 2](./00-danh-gia-va-cau-hoi.md).

---

## Các tệp

| Tệp | Nội dung | Đọc khi nào |
|---|---|---|
| [`00` Đánh giá và câu hỏi](./00-danh-gia-va-cau-hoi.md) | Đánh giá cách làm, hai quyết định bị đảo, **ba lỗ hổng phải vá trước**, đề xuất chi tiết tính năng cha–con, sáu việc nặng chưa thấy nhắc tới, và **17 câu hỏi cần trả lời** | Đọc đầu tiên. Có chỗ không đồng ý và nói rõ vì sao |
| [`01` Danh sách tính năng](./01-danh-sach-tinh-nang.md) | **174 tính năng** chia 15 nhóm, 132 thuộc bản đầu. Mỗi tính năng có mã, nội dung, thuộc bản nào, dùng lại được của Thu mua hay phải làm mới | Khi cần biết phạm vi công việc |
| [`02` Lộ trình phát triển](./02-lo-trinh-phat-trien.md) | **10 phase**, sơ đồ phụ thuộc, điều kiện chuyển phase, rủi ro, chia việc cho nhiều người. **Không có mốc thời gian** — thứ tự và điều kiện mới là thứ quan trọng | Khi cần biết làm gì trước làm gì sau |
| [`03` Tính năng Lark Approver](./03-lark-approver.md) | Rà **82 tính năng** của Lark Approver, mỗi cái một kết luận lấy hay bỏ và vì sao. Kèm **ba chỗ cố ý làm khác Lark** và **bốn chỗ mình cần mà Lark không có** | Trước khi thiết kế bộ máy phê duyệt (phase 3) |
| [`04` Các bảng dữ liệu](./04-bang-du-lieu.md) | **25 bảng mới + 4 bảng sửa**, đủ cột và ý nghĩa từng cột, chỉ mục bắt buộc, ràng buộc phải đặt ở tầng dữ liệu, thứ tự chạy migration, **mười hai chỗ dễ sai nhất** | Khi bắt đầu viết mã |
| [Nhật ký thay đổi](./CHANGELOG.md) | Bộ tài liệu này sửa gì, lúc nào, vì sao | Khi quay lại sau một thời gian, hoặc khi thấy nội dung khác với lần đọc trước |
| [`05` Vòng đời phiên bản](./05-vong-doi-phien-ban.md) | **Đã ban hành rồi thì sửa bằng cách nào.** Hai cách khác nhau tùy loại văn bản: lên phiên bản 2.0 giữ nguyên mã, hay ra một văn bản mới sửa đổi văn bản cũ. Kèm sáu thứ bị kéo theo và bốn câu hỏi mới | Cùng lúc với `04`. Đây là chỗ dễ làm sai nhất mà không ai phát hiện |
| [`06` Kịch bản test](./06-kich-ban-test.md) | **Chạy tay một vòng đời văn bản** trên bản LOCAL: tài khoản nào để chuyển vai, ai thấy gì, ai duyệt chặng nào, năm ca phạm vi áp dụng (loại trừ phòng ban / chừa một người trong phòng đó), phiên bản, bản trích, danh mục mức mật | Khi cần nghiệm thu hoặc sau mỗi đợt sửa phân hệ Văn bản |

---

## Đọc theo vai

- **Người quyết:** đọc `00` mục 1 (tóm tắt một trang) và mục 8 (17 câu hỏi). Đây là tài liệu duy nhất cần câu trả lời từ ngoài đội phần mềm.
- **Người chủ trì:** đọc `00` rồi `02`. `02` mục 18 là danh sách việc bắt đầu được ngay mà không chờ ai.
- **Đội phần mềm:** đọc `01` để biết phạm vi, `04` để biết mô hình dữ liệu, `03` trước khi làm phase 3.
- **Hành chính và Pháp chế:** đọc `00` mục 8 nhóm B (8 câu về nghiệp vụ văn thư), và `02` mục 10 — phần số hóa văn bản giấy là việc của người, bắt đầu được ngay từ bây giờ.

---

## Năm điều quan trọng nhất trong cả bộ

1. **Phải vá nền trước khi đưa văn bản mật vào.** Hệ Thu mua đang chạy có tệp đính kèm tải được không cần quyền, nhật ký thao tác đọc tự do, và phạm vi phòng ban khớp bằng tên. Ba chỗ này vô hại với đơn mua hàng, nhưng chí mạng với văn bản mật. Đây là phase 0.

2. **Việc đầu tiên không phải viết tính năng, mà là viết kiểm thử cho 5 luồng duyệt hiện có của Thu mua.** Không có bộ kiểm thử này thì mọi thay đổi sau đó đều không biết có làm hỏng hệ đang chạy hay không. Việc này **bắt đầu được ngay, không chờ trả lời câu hỏi nào**.

3. **Cấp số văn bản phải khóa dòng bộ đếm, trong cùng một giao dịch với việc ghi bản ghi.** Lấy số lớn nhất cộng một, hoặc đếm bằng Redis, đều sinh ra hai văn bản trùng số. Bài kiểm bắt buộc: 100 kết nối cùng lúc phải ra đúng 100 số liên tiếp.

4. **Bộ máy duyệt không được có tùy chọn "không tìm thấy người duyệt thì tự động duyệt qua".** Lark có tùy chọn đó. Với văn bản, nó tạo ra văn bản có hiệu lực mà không ai chịu trách nhiệm, và trên giấy tờ không phân biệt được với văn bản duyệt đúng quy trình.

5. **Sửa văn bản đã ban hành có hai cách, không được dùng lẫn.** Quy chế thì lên phiên bản 2.0, mã giữ nguyên. Quyết định thì không có phiên bản 2 — phải ra một Quyết định mới sửa đổi Quyết định cũ. Cho lên phiên bản với văn bản hành chính là sửa giấy tờ đã ký. Chi tiết ở [`05`](./05-vong-doi-phien-ban.md).

---

## Liên quan tới đâu

| Nơi khác | Quan hệ |
|---|---|
| [`erp/README.md`](../README.md) | Bộ tài liệu nền ERP. Phân hệ văn thư được đẩy lên **trước HRM** |
| [`erp/06`](../06-lo-trinh-nen-tang-va-hrm.md), [`erp/08`](../08-danh-sach-task-cung-co.md) | Nhóm N trong `01` chính là các hạng mục củng cố nền đã liệt kê ở hai tệp đó, nay được làm sớm hơn |
| `D:\New folder\quanlytailieu\docs\` | Bộ thiết kế văn thư độc lập trước đây: danh mục 32 loại văn bản, 13 pháp nhân, logic đánh số, mô hình 42 bảng. **Nội dung nghiệp vụ vẫn dùng; phần kiến trúc thì bộ này thay thế** |

---

## Trạng thái

Toàn bộ bộ tài liệu là **bản đề xuất, chưa được duyệt**. Chưa có dòng mã nào được viết, chưa có bảng nào được tạo. Mọi lần sửa từ nay ghi vào [nhật ký thay đổi](./CHANGELOG.md) — đọc lại sau vài tuần mà không có nhật ký thì không biết chỗ nào đã đổi.

Việc chặn lớn nhất: **17 câu hỏi ở `00` mục 8** cộng **4 câu ở `05` mục 9** — trong đó nhóm A và nhóm B cần người ngoài đội phần mềm trả lời. Bốn câu ở `05` không chặn việc bắt đầu: có phương án mặc định, chốt khác thì đổi cấu hình chứ không sửa mã. Riêng B12 chặn đúng một tính năng là trích lục chính thức.
