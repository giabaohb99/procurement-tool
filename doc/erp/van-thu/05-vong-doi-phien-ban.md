# VÒNG ĐỜI PHIÊN BẢN — SỬA MỘT VĂN BẢN ĐÃ BAN HÀNH

Bản 1.1 — 13/08/2026 · bản 1.1 chỉ thêm câu hỏi B12 ở mục 9

> Tệp này trả lời một câu hỏi: **đã ban hành rồi, khóa không sửa được, giờ muốn đổi nội dung thì làm sao.**
> Bốn tệp trước có nhắc tới phiên bản nhưng chưa nói rõ luồng. Đây là phần đó.

---

## 1. Trả lời ngắn

**Có hai cách, chọn theo loại văn bản. Không có cách dùng chung cho cả 32 loại.**

| | Cách 1 — Lên phiên bản | Cách 2 — Ban hành văn bản mới |
|---|---|---|
| Dùng cho | Nhóm A, B, C — tài liệu hệ thống | Nhóm D, E — văn bản hành chính |
| Ví dụ loại | Quy chế, Quy định, Quy trình, Hướng dẫn công việc, Biểu mẫu, Chính sách | Quyết định, Thông báo, Công văn, Tờ trình, Biên bản |
| Cột nhận biết | `tab_doc_type.id_scheme = 1` | `tab_doc_type.id_scheme = 2` |
| Định danh | `DEGO-QC-012` — bất biến, không có năm | `15/2026/QD-DEGO` — theo sổ, đếm lại mỗi năm |
| Sửa nội dung | Tạo **phiên bản 2.0**, mã giữ nguyên | **Không có phiên bản 2.** Ra một văn bản mới, số mới |
| Bản cũ trở thành | Phiên bản 1.0, trạng thái *bị thay thế* | Vẫn nguyên giá trị, gắn nhãn *đã bị sửa đổi bởi ...* |
| Người tra cứu thấy | Một văn bản, nhiều phiên bản, bản mới nhất là bản đang dùng | Hai văn bản riêng, nối với nhau bằng quan hệ *sửa đổi* |

**Vì sao phải tách hai cách:**

Một Quyết định đã ký, đã đóng dấu, có ngày tháng và chữ ký người có thẩm quyền. Sửa nội dung của nó là sửa giấy tờ đã phát hành — trên giấy tờ không phân biệt được với làm giả. Muốn đổi thì phải ra **Quyết định 47/2026/QD-DEGO** *"về việc sửa đổi Điều 5 Quyết định 15/2026/QD-DEGO"*.

Quy chế thì ngược lại. Nó là tài liệu sống, sửa vài lần một năm là bình thường. Nếu mỗi lần sửa lại cấp một mã mới thì sau ba năm có sáu mã khác nhau cùng nói về một việc, không ai biết mã nào đang có hiệu lực. Nên mã phải giữ nguyên, chỉ số phiên bản đổi.

---

## 2. Cách 1 — Lên phiên bản, chi tiết từng bước

Ví dụ: **Quy chế lương DEGO-QC-012**, phiên bản 1.0, đang có hiệu lực từ 01/01/2026. Nay muốn đổi mức phụ cấp.

### Bước 1 · Xin sửa

Người có nhu cầu tạo một **yêu cầu văn bản** với `kind = 2` (sửa văn bản đang có), `target_document_id` trỏ về DEGO-QC-012. Bắt buộc ghi lý do.

Bước này bỏ được hay không là tùy loại: `tab_doc_type.needs_request`. Với Quy chế thì nên giữ, vì sửa quy chế lương không phải việc ai muốn cũng làm.

### Bước 2 · Yêu cầu được duyệt

Đi qua luồng duyệt yêu cầu như văn bản soạn mới. Người duyệt yêu cầu **không nhất thiết là người duyệt văn bản** — cấu hình riêng.

### Bước 3 · Mở phiên bản nháp

Hệ thống tạo một dòng mới trong `tab_document_version`:
- `document_id` giữ nguyên — vẫn là DEGO-QC-012
- `version_no` = `2.0` hoặc `1.1`, xem mục 4
- `status` = 1 nháp
- Nội dung **chép từ phiên bản 1.0** làm điểm xuất phát, không bắt gõ lại từ đầu

**Quy tắc cứng: mỗi văn bản chỉ được có đúng một phiên bản đang mở.** Không cho hai người cùng mở bản nháp 2.0. Ai mở trước thì người sau thấy báo "đang có bản nháp 2.0 do anh A giữ".

### Bước 4 · Soạn và khai lý do

Người soạn sửa nội dung, bắt buộc điền hai ô:
- `change_summary` — sửa gì so với bản trước
- `change_reason` — vì sao sửa

Hai ô này bắt buộc từ phiên bản thứ hai trở đi. Chúng chính là **biên bản sửa đổi tài liệu** mà ISO đòi hỏi — không cần làm thêm bảng riêng.

### Bước 5 · Gửi duyệt

Đi qua luồng duyệt. Luồng dùng bản đầy đủ hay bản rút gọn thì tùy mức độ sửa, xem mục 4.

**Trong suốt bước 3, 4, 5 — phiên bản 1.0 vẫn đang có hiệu lực bình thường.** Người trong công ty vẫn mở ra đọc bản 1.0, vẫn làm theo bản 1.0. Không có khoảng trống, không có lúc nào công ty không có quy chế lương.

Đây là điểm quan trọng nhất của cả cơ chế phiên bản, và cũng là điểm hay bị làm sai nhất: nhiều hệ thống chuyển văn bản về trạng thái "đang sửa" ngay khi mở bản nháp, làm cả công ty mất chỗ tra cứu trong hai tuần.

### Bước 6 · Được duyệt

`tab_document_version` bản 2.0: `status` = 3 đã duyệt, `is_locked` = true. Từ đây không sửa được nữa, kể cả người tạo, kể cả quản trị.

**Nhưng chưa có hiệu lực.** Đã duyệt và có hiệu lực là hai việc khác nhau. Duyệt ngày 20/08 mà hiệu lực từ 01/09 là bình thường và rất hay gặp.

### Bước 7 · Ban hành

Đến `effective_from` của phiên bản 2.0, hệ thống làm **trong một giao dịch**:

| Việc | Chi tiết |
|---|---|
| Phiên bản 1.0 | `status` = 4 bị thay thế |
| Phiên bản 2.0 | `status` = 3, giữ `is_locked` |
| `tab_document` | `current_version_id` trỏ sang 2.0, `effective_date` cập nhật |
| `doc_code` | **Không đụng tới.** Vẫn là `DEGO-QC-012` |
| Trạng thái văn bản | Vẫn là 4 có hiệu lực — văn bản không hề chuyển sang "bị thay thế", chỉ phiên bản của nó thôi |
| Phân phối | Gửi thông báo cho người thuộc phạm vi |
| Xác nhận đã đọc | Sinh yêu cầu mới nếu là sửa lớn, xem mục 5 |

Việc chuyển tại `effective_from` chạy bằng tác vụ định kỳ. Hệ Thu mua **đã có Celery beat chạy thật** (đang chạy sao lưu R2 hai lần mỗi ngày), nên không phải dựng hạ tầng mới.

### Bước 8 · Sau khi ban hành

Bản 1.0 **không bị xóa, không bị ẩn**. Vẫn mở ra đọc được, vẫn tải tệp về được, nhưng:
- Đầu trang hiện băng cảnh báo: *"Đây là phiên bản 1.0, đã bị thay thế bởi phiên bản 2.0 từ ngày 01/09/2026"*, kèm nút sang bản mới
- Không nằm trong kết quả tìm kiếm mặc định, phải bật ô "xem cả bản cũ"

Lý do giữ lại: tranh chấp lao động tháng 03/2026 phải xử theo Quy chế lương bản 1.0, không phải bản 2.0. Xóa bản cũ là mất bằng chứng.

---

## 3. Cách 2 — Ban hành văn bản mới sửa đổi văn bản cũ

Ví dụ: **Quyết định 15/2026/QD-DEGO** về việc bổ nhiệm, đã ký. Nay muốn đổi một điều khoản.

### Các bước

1. Soạn một văn bản **mới hoàn toàn**, loại Quyết định, tiêu đề *"Về việc sửa đổi Điều 5 Quyết định số 15/2026/QD-DEGO"*.
2. Khai quan hệ trong `tab_document_link`: `source` = văn bản mới, `target` = Quyết định 15, `relation` = **2 sửa đổi**.
3. Duyệt, cấp số → thành **47/2026/QD-DEGO**. Số này lấy từ sổ Quyết định năm 2026, không liên quan gì tới số 15.
4. Quyết định 15 **giữ nguyên trạng thái có hiệu lực**, `version_no` mãi mãi là 1.0. Không ai đụng vào nó.
5. Trang chi tiết Quyết định 15 từ nay hiện thêm dòng: *"Đã bị sửa đổi bởi 47/2026/QD-DEGO ngày 15/08/2026"*, có đường dẫn sang.

### Ba biến thể của quan hệ

| Quan hệ | Tác động lên văn bản cũ | Ví dụ tiêu đề |
|---|---|---|
| **2 sửa đổi** | Không đổi trạng thái. Phần không bị sửa vẫn có hiệu lực | "Về việc sửa đổi Điều 5 Quyết định 15" |
| **1 thay thế** | Văn bản cũ chuyển `status` = 5 bị thay thế | "Về việc ban hành Quy chế X thay thế Quyết định 15" |
| **9 bãi bỏ** | Văn bản cũ chuyển `status` = 7 bãi bỏ | "Về việc bãi bỏ Quyết định 15" |

Ba tác động này hệ thống làm tự động khi văn bản mới được ban hành, dựa vào cột `relation`. Người dùng không phải nhớ đi đổi trạng thái văn bản cũ bằng tay — và cũng không được phép đổi bằng tay.

### Một điều bắt buộc, không phải tùy chọn

**Người mở Quyết định 15 phải thấy ngay là nó đã bị sửa đổi.** Nếu không thấy, họ đọc Điều 5 cũ và làm sai — mà lỗi này không ai phát hiện ra, vì trên màn hình văn bản vẫn hiện "có hiệu lực".

Đây là chỗ nguy hiểm nhất của cách 2, và nó khác hẳn cách 1: ở cách 1 hệ thống ép người ta nhìn bản mới nhất, ở cách 2 người ta hoàn toàn có thể đọc đúng một văn bản còn hiệu lực mà vẫn ra thông tin sai.

---

## 4. Số phiên bản: 1.1 hay 2.0

| Tăng số sau — 1.0 → 1.1 | Tăng số trước — 1.0 → 2.0 |
|---|---|
| Sửa lỗi chính tả, lỗi đánh máy | Thêm, bớt, đổi nội dung một điều khoản |
| Đổi định dạng, đổi bố cục trình bày | Đổi mức tiền, đổi tỷ lệ, đổi hạn mức |
| Đổi tên phòng ban do phòng đó đổi tên | Đổi thẩm quyền, đổi người chịu trách nhiệm |
| Sửa số hiệu văn bản dẫn chiếu bị ghi sai | Đổi phạm vi áp dụng |
| **Không điều khoản nào đổi nghĩa** | **Có ít nhất một điều khoản đổi nghĩa** |

Ghi vào cột mới `change_kind`: 1 sửa lớn · 2 sửa nhỏ.

**Ai chọn:** người soạn chọn, **người duyệt cuối xác nhận hoặc đổi lại**. Hệ thống không tự đoán — máy không đọc được là câu chữ có đổi nghĩa hay không.

**Cột này quyết định ba việc khác**, nên không phải khai cho vui:

| `change_kind` | Luồng duyệt | Xác nhận đã đọc | Đánh dấu văn bản con |
|---|---|---|---|
| 1 sửa lớn | Đầy đủ, như soạn mới | **Bắt buộc xác nhận lại** | Có |
| 2 sửa nhỏ | Rút gọn, một cấp | Chỉ thông báo, không bắt xác nhận | Không |

Nếu bắt xác nhận lại cho cả bản sửa chính tả thì 500 người phải bấm nút vì một dấu phẩy. Vài lần như vậy là người ta bấm cho xong mà không đọc, và cơ chế xác nhận đã đọc mất hết ý nghĩa.

---

## 5. Lên phiên bản kéo theo sáu thứ khác

Đây là phần dễ quên nhất. Ban hành 2.0 xong không phải là hết việc.

### 5.1 Các bản clone ở công ty con

Đã có sẵn cơ chế: `tab_document.source_version_id` ghi bản clone lấy từ phiên bản nào. Bản gốc lên 2.0 thì mọi bản clone có `source_version_id` = id của 1.0 tự chuyển `clone_status` sang **6 — cần rà lại vì bản gốc đã lên phiên bản mới**, và người phụ trách từng bản clone nhận thông báo.

Không tự sửa bản clone. Chỉ báo. Công ty con quyết định làm gì với nó.

### 5.2 Xác nhận đã đọc

Đã có sẵn: `tab_document_recipient` gắn với `version_id` chứ không gắn với `document_id`, và có `UNIQUE(version_id, recipient_kind, recipient_id)`. Nên bản 2.0 ra thì cột `confirmed_at` trống trơn, mọi người phải xác nhận lại từ đầu.

Điều bổ sung: chỉ bắt buộc khi `change_kind` = 1 sửa lớn.

### 5.3 Văn bản con

Quy trình QT-005 lên bản 2.0, mà có ba Hướng dẫn công việc *hướng dẫn* nó và năm Biểu mẫu *thuộc về* nó. Tám văn bản đó có còn đúng không?

Hệ thống **không biết** và không được đoán. Việc phải làm: hiện danh sách tám văn bản con cho người ban hành xem, hỏi "đánh dấu cần rà lại hay để nguyên", và ghi lựa chọn đó vào nhật ký.

Bảng quy tắc `tab_doc_type_link_rule` hiện chỉ có cột `on_parent_obsolete` — xử lý khi cha **bị bãi bỏ**. Thiếu trường hợp cha **lên phiên bản mới**. Phải thêm cột, xem mục 6.

### 5.4 Người đang giữ đường dẫn cũ

Ai đó đã gửi cho đồng nghiệp đường dẫn tới phiên bản 1.0 qua tin nhắn hồi tháng trước. Người kia bấm vào hôm nay.

Phải hiện băng cảnh báo và nút sang bản mới. Không được lặng lẽ chuyển hướng sang 2.0 — người ta có thể đang cố ý tìm bản cũ.

### 5.5 Quyết định kèm theo

Trong bảng quy tắc có dòng: **Quy chế — kèm theo — Quyết định — bắt buộc — đúng 1**. Nghĩa là Quy chế DEGO-QC-012 bản 1.0 được ban hành kèm Quyết định 15/2026.

Vậy bản 2.0 ban hành kèm cái gì? **Phải có một Quyết định mới.** Không dùng lại Quyết định 15 được — Quyết định 15 nói "ban hành Quy chế lương" tại thời điểm 01/01/2026, nó không nói gì về nội dung sửa tháng 09.

Nên: **`tab_doc_type.needs_decision` phải kiểm ở mức phiên bản, không phải mức văn bản.** Loại nào `needs_decision = true` thì mỗi phiên bản có `change_kind` = 1 sửa lớn đều phải kèm một Quyết định mới thì mới ban hành được.

Chỗ này bốn tệp trước chưa nói. Cột `needs_decision` có sẵn nhưng đọc qua thì ai cũng hiểu là chỉ kiểm một lần lúc tạo văn bản.

### 5.6 Phạm vi áp dụng

Phiên bản 2.0 có được đổi phạm vi áp dụng không?

**Được, nhưng phải khai rõ.** Quy chế bản 1.0 áp cho 3 công ty, bản 2.0 áp cho 5 công ty là chuyện có thật. Khi phạm vi đổi:
- Người **mới vào phạm vi** nhận thông báo như văn bản mới ban hành
- Người **bị loại khỏi phạm vi** nhận thông báo *"văn bản này không còn áp dụng cho bạn từ ngày ..."* — không được lặng lẽ biến mất khỏi danh sách của họ

---

## 6. Phải bổ sung vào [`04` Các bảng dữ liệu](./04-bang-du-lieu.md)

### 6.1 `tab_document_version` — thêm 5 cột

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `change_kind` | TINYINT | **1 sửa lớn · 2 sửa nhỏ.** Quyết định luồng duyệt, việc xác nhận lại, và việc đánh dấu văn bản con |
| `effective_from` | DATE, cho phép rỗng | Ngày phiên bản này bắt đầu có hiệu lực. **Khác với ngày được duyệt** |
| `requires_reconfirm` | BOOLEAN | Có bắt người trong phạm vi xác nhận đã đọc lại không. Mặc định lấy theo `change_kind`, sửa tay được |
| `prev_version_id` | BIGINT, cho phép rỗng | Phiên bản trước nó. Khai rõ chứ không suy từ thứ tự `version_no` |
| `created_from_request_id` | BIGINT, cho phép rỗng | Yêu cầu sửa nào sinh ra phiên bản này |

### 6.2 `tab_document_version` — thêm một ràng buộc

**Mỗi văn bản chỉ được có một phiên bản đang mở.** Ép ở tầng dữ liệu, không chỉ ở tầng dịch vụ:

```sql
ALTER TABLE tab_document_version
  ADD COLUMN open_slot BIGINT
    GENERATED ALWAYS AS (CASE WHEN status IN (1,2) THEN document_id END) STORED,
  ADD UNIQUE KEY uq_one_open_version (open_slot);
```

Cột sinh này bằng `document_id` khi phiên bản còn nháp hoặc đang duyệt, và bằng rỗng khi đã duyệt hoặc đã bị thay thế. Ràng buộc duy nhất bỏ qua giá trị rỗng, nên nhiều phiên bản cũ nằm chung một văn bản không sao, còn hai phiên bản đang mở thì cơ sở dữ liệu chặn.

Không làm bằng câu lệnh kiểm tra trong mã nguồn được: hai người bấm cùng lúc thì cả hai câu kiểm đều thấy trống.

### 6.3 `tab_doc_type_link_rule` — thêm 1 cột

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `on_parent_new_version` | TINYINT | **1 không làm gì · 2 đánh dấu con cần rà lại · 3 hỏi người ban hành rồi ghi nhật ký.** Đề nghị mặc định 3 |

Cột `on_parent_obsolete` đang có chỉ lo trường hợp cha bị bãi bỏ. Cha lên phiên bản mới là việc xảy ra thường xuyên hơn nhiều.

### 6.4 `tab_document` — làm rõ một cột đã có

`status` của **văn bản** và `status` của **phiên bản** là hai thứ khác nhau, dễ nhầm:

| | Giá trị 4 | Giá trị 5 |
|---|---|---|
| `tab_document.status` | Có hiệu lực | Bị thay thế — **bởi một văn bản khác**, dùng ở cách 2 |
| `tab_document_version.status` | (không có 4 nghĩa này) | — |
| `tab_document_version.status` = 4 | Bị thay thế — **bởi phiên bản sau của chính nó**, dùng ở cách 1 | |

Quy chế lên bản 2.0 thì **văn bản vẫn ở trạng thái 4 có hiệu lực**, chỉ có phiên bản 1.0 chuyển sang bị thay thế. Nhầm chỗ này là cả công ty thấy quy chế lương biến mất khỏi danh sách văn bản đang hiệu lực.

---

## 7. Phải bổ sung vào [`01` Danh sách tính năng](./01-danh-sach-tinh-nang.md)

Tám tính năng, tất cả thuộc bản đầu, tất cả nằm ở **phase 2** trong [`02`](./02-lo-trinh-phat-trien.md) trừ C18 nằm ở phase 4.

| Mã | Tính năng | Nội dung | Bản |
|---|---|---|---|
| C13 | Mở phiên bản mới từ văn bản đã ban hành | Chép nội dung bản hiện tại làm điểm xuất phát, bắt khai lý do sửa | 1 |
| C14 | Một văn bản chỉ một bản nháp | Ép bằng ràng buộc duy nhất ở tầng dữ liệu, không chỉ kiểm trong mã | 1 |
| C15 | Phân loại sửa lớn hay sửa nhỏ | Người soạn chọn, người duyệt xác nhận. Quyết định luồng duyệt, việc xác nhận lại, việc đánh dấu văn bản con | 1 |
| C16 | Bản cũ vẫn hiệu lực trong lúc soạn bản mới | Không có khoảng trống. Chỉ đổi tại giây ban hành | 1 |
| C17 | Ngày hiệu lực riêng của từng phiên bản | Duyệt trước, hiệu lực sau. Tác vụ định kỳ tự chuyển đúng ngày | 1 |
| C18 | Băng cảnh báo trên phiên bản cũ | "Đã bị thay thế bởi bản 2.0 ngày ...", kèm nút sang bản mới. Bản cũ **không xóa, không ẩn** | 1 |
| J10 | Nhãn "đã bị sửa đổi" trên văn bản hành chính | Mở Quyết định 15 phải thấy ngay nó đã bị sửa bởi Quyết định 47. **Bắt buộc, không phải tùy chọn** | 1 |
| J11 | Quyết định ban hành kiểm ở mức phiên bản | Loại có `needs_decision` thì mỗi lần sửa lớn phải kèm một Quyết định mới | 1 |

Cộng thêm tám mục: **160 tính năng, 119 thuộc bản đầu.**

---

## 8. Bốn chỗ dễ sai nhất

| Sai | Hậu quả | Cách chặn |
|---|---|---|
| Cho lên phiên bản với văn bản hành chính | Quyết định đã ký bị sửa nội dung, không phân biệt được với làm giả | Kiểm `id_scheme`: bằng 2 thì nút "Lên phiên bản" không tồn tại, và tầng dịch vụ từ chối |
| Đóng băng văn bản ngay khi mở bản nháp | Cả công ty mất chỗ tra cứu suốt thời gian soạn và duyệt | Bản nháp là một dòng riêng trong `tab_document_version`, không đụng gì tới `current_version_id` |
| Nhầm trạng thái văn bản với trạng thái phiên bản | Quy chế biến mất khỏi danh sách văn bản đang hiệu lực sau khi lên bản mới | Mục 6.4 |
| Bắt xác nhận đọc lại cho mọi phiên bản | Người ta bấm cho xong không đọc, cơ chế xác nhận mất ý nghĩa | `requires_reconfirm` mặc định theo `change_kind` |

---

## 9. Bốn câu cần trả lời

Bổ sung vào 17 câu ở [`00` mục 8](./00-danh-gia-va-cau-hoi.md). Cả bốn đều là câu nghiệp vụ, **đội phần mềm không tự quyết được**.

| Mã | Câu hỏi | Ai trả lời | Chặn gì |
|---|---|---|---|
| B9 | Sửa Quy chế thì có bắt buộc ra Quyết định mới để ban hành bản sửa không, hay Quyết định ban hành lần đầu là đủ | Pháp chế | Mục 5.5, phase 2 |
| B10 | Loại nào được phép sửa nhỏ không qua duyệt đầy đủ, và ai có quyền xác nhận là sửa nhỏ | Hành chính | Mục 4, phase 2 |
| B11 | Phiên bản cũ giữ bao lâu — giữ mãi hay theo thời hạn lưu trữ của loại | Pháp chế | Mục 2 bước 8, phase 5 |
| B12 | Có thêm **Trích lục** thành loại văn bản thứ 33 không, và ai được ký xác nhận "sao đúng với bản gốc" | Hành chính, Pháp chế | Tính năng C20, phase 1. **Không chặn C19** — bản trích nội bộ làm được ngay |

Ba câu đầu **không chặn việc bắt đầu**. Cứ làm theo phương án mặc định đề nghị trong tệp này, chỗ nào lệch thì sửa cấu hình chứ không sửa mã nguồn. Câu B12 chỉ chặn đúng một tính năng, phần còn lại của bản trích không phải chờ.
