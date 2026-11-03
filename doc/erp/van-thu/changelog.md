# NHẬT KÝ THAY ĐỔI — BỘ TÀI LIỆU QUẢN LÝ VĂN THƯ

> Mọi lần sửa nội dung của bảy tệp trong thư mục này đều ghi một dòng ở đây.
> Mới nhất nằm trên cùng.

**Cách ghi:** mỗi mục có ngày, tệp bị sửa và số bản mới của tệp đó, sửa cái gì, **vì sao**. Phần "vì sao" quan trọng hơn phần "sửa gì" — sáu tháng sau người đọc cần biết lý do chứ không cần biết dòng nào đổi.

**Bản của từng tệp không đi cùng nhau.** `01` có thể ở bản 1.3 trong khi `00` còn ở bản 1.0. Ai muốn biết tệp mình đang đọc là bản nào thì xem dòng thứ hai ngay dưới tiêu đề của tệp đó.

---

## 13/08/2026 — `04` lên bản 1.1 · gom bảng

**Tệp sửa:** `04` (bản 1.0 → 1.1) · `05`, `README` sửa theo cho khớp.

**Gom 29 bảng mới xuống 25.** Bốn bảng bị bỏ, không bảng nào mất chức năng:

| Bảng bỏ | Đi đâu | Vì sao |
|---|---|---|
| `tab_document_clone` | Bảy cột trên `tab_document` | Bản ghi theo dõi clone và bản nháp được clone luôn là cùng một thứ, vì F06 quy định clone sinh bản nháp ngay. Giữ hai bảng nghĩa là **ba chỗ cùng ghi một sự thật** — cột `source_document_id`, bảng clone, và dòng `tab_document_link` hệ thống tự tạo |
| `tab_legal_reference` | `tab_document` với `origin = 2` | **Vá lỗi.** Bản 1.0 bảo nối văn bản pháp luật với văn bản nội bộ qua `tab_document_link` quan hệ *căn cứ theo*, nhưng cột `target_document_id` là khóa ngoại trỏ `tab_document` — một dòng ở bảng riêng không bao giờ làm đích của quan hệ được |
| `tab_outgoing_register` | Báo cáo đọc thẳng từ `tab_document`, thêm 3 cột | **Vá mâu thuẫn.** Ràng buộc `UNIQUE(company_id, year, seq_no)` của sổ đi chống lại chính cách cấp số ở mục 4.4: khóa `out:{pháp nhân}:{năm}:{mã loại}` đếm lại theo từng loại, nên Thông báo số 8 và Quyết định số 8 cùng năm là bình thường |
| `tab_read_receipt` | Gộp với `tab_distribution` thành `tab_document_recipient` | Hai bảng cùng một hạt: một người nhận, một phiên bản. Câu hỏi thường gặp nhất của văn thư — gửi bao nhiêu, đọc bao nhiêu, ai chưa — nay trả lời trong một truy vấn |

**Hai bảng cân nhắc gom nhưng cố ý giữ**, lý do ghi tại chỗ trong `04`: `tab_doc_template` (mục 4.3 — không đổi một bảng nóng lấy một bảng nguội) và `tab_incoming_register` (mục 9.2 — vòng đời khác hẳn, và thuộc phase 9).

**Bỏ thêm một cột thừa:** `tab_document_request.created_document_id`. Quan hệ đã có ở `tab_document.document_request_id`; con trỏ hai chiều thì luôn có ngày lệch nhau, và lệch im lặng.

**Cột mới quan trọng nhất: `tab_document.origin`** (1 nội bộ · 2 pháp luật ngoài · 3 văn bản đến). Đây là cái giá của việc gom — mọi truy vấn danh sách, tìm kiếm, báo cáo phải lọc `origin = 1`, và chỗ ép việc đó là tầng dịch vụ chứ không phải từng màn hình. Đã thêm thành chỗ dễ sai số 12 trong `04` mục 13, kèm bài kiểm tự động bắt buộc.

**Sửa theo cho khớp:** `04` mục 10 chỉ mục, mục 11 ràng buộc, mục 12 thứ tự migration (còn M1–M11 thay vì M1–M12), mục 14 bảng tổng hợp. `05` mục 5.1 và 5.2 đổi tên bảng được nhắc tới. `README` đổi con số và thêm dòng trỏ tới tệp này.

**Không đổi:** toàn bộ danh sách tính năng ở `01`, lộ trình ở `02`, và mọi quyết định nghiệp vụ. Việc gom bảng **không làm giảm khối lượng công việc** — cột vẫn từng ấy, màn hình vẫn từng ấy. Cái được là bớt bốn chỗ dữ liệu có thể lệch nhau, và vá hai lỗi thiết kế mà việc gom làm lộ ra.

---

## 13/08/2026 — bản đầu của cả bộ

Bảy tệp `README`, `00` tới `05` được viết trong cùng một ngày, rồi rà lại vài lượt ngay sau đó. Số bản lúc chốt: `00` bản 1.0 · `01` bản 1.3 · `02`, `03` không đánh số · `04` bản 1.0 · `05` bản 1.1.

Ba lần bổ sung của `01` (bản 1.1 đến 1.3), lý do đầy đủ ghi ngay đầu tệp đó:

| Bổ sung | Mã | Vì sao thiếu |
|---|---|---|
| Sửa văn bản **đã ban hành** | C13–C18, J10, J11 | Bốn tệp đầu có nói tới phiên bản nhưng không nói luồng. Hai loại văn bản sửa theo hai cách khác nhau — sinh ra hẳn tệp `05` |
| **Chia sẻ và thu hồi** | G14–G24, G09 lên bản 1 | Chỉ có luật "chia sẻ không vượt được mức mật" thì giám đốc bấm chia sẻ xong không ai thấy gì và không biết làm tiếp thế nào |
| **Bản trích** xếp lại cho đúng chỗ | C19, C20, E11 | Trước nằm trong nhóm quyền truy cập nên người đọc nhóm soạn thảo không bao giờ thấy. Kèm phát hiện: dùng quan hệ *thuộc về* cho bản trích là sai, cần quan hệ thứ mười *trích từ* |

Hai quyết định cũ bị đảo so với bộ thiết kế văn thư độc lập bên `quanlytailieu`: làm trong Thu mua thay vì hệ riêng, và clone là cơ chế hợp lệ có kiểm soát thay vì tuyệt đối cấm. Lý do và cái giá ở `00` mục 2.
