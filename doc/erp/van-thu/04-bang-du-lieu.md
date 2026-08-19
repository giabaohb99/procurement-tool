# 04 · CÁC BẢNG DỮ LIỆU CẦN SINH RA

> Áp lên cơ sở dữ liệu `procurement` đang chạy (MySQL 8.4) · 57 bảng hiện có → khoảng 82 bảng
> Bản 1.1 · đã gom bớt bảng, xem [nhật ký thay đổi](./CHANGELOG.md)
> Danh sách tính năng ở [`01`](./01-danh-sach-tinh-nang.md) · lộ trình ở [`02`](./02-lo-trinh-phat-trien.md)

---

## 1. Tổng quan

| | Số lượng |
|---|---|
| Bảng đang có, phải **sửa** (thêm cột) | 4 |
| Bảng **tạo mới** | 25 |
| Bảng đang có, **dùng lại nguyên** | 12 |

Bảng dùng lại nguyên, không đụng gì: `tab_company`, `tab_employee`, `tab_user`, `tab_role`, `tab_user_role`, `tab_permission`, `tab_user_scope`, `tab_file`, `tab_file_link`, `tab_notification`, `tab_audit_log`, `tab_setting`. Đây chính là phần tiết kiệm được khi xây trong Thu mua thay vì làm hệ riêng — nếu làm riêng thì 12 bảng này phải dựng lại từ đầu, kèm toàn bộ màn hình quản lý của chúng.

### 1.1 Bốn bảng đã gom ở bản 1.1

Bản đầu của tài liệu này đề nghị 29 bảng mới. Rà lại thì bốn bảng trong đó **không mang thêm sự thật nào** so với bảng khác, chỉ mang thêm chỗ để dữ liệu lệch nhau. Đã gom:

| Bảng bỏ | Gom vào | Được thêm gì ngoài việc bớt một bảng |
|---|---|---|
| `tab_document_clone` | Cột trên `tab_document` (mục 5.6) | Bỏ được **ba chỗ cùng ghi một sự thật** "bản này clone từ đâu" |
| `tab_legal_reference` | `tab_document` với `origin = 2` (mục 5.2) | Vá lỗi: bản cũ bảo nối văn bản pháp luật qua `tab_document_link`, mà cột `target_document_id` lại trỏ `tab_document` — nối không nổi |
| `tab_outgoing_register` | Báo cáo đọc thẳng từ `tab_document` (mục 9.1) | Vá mâu thuẫn: ràng buộc duy nhất của sổ đi chống lại chính cách đánh số theo loại |
| `tab_read_receipt` | `tab_document_recipient` (mục 7.1) | Gộp với `tab_distribution` thành một bảng: gửi cho ai và ai đã đọc trả lời trong một truy vấn |

Hai bảng nữa **gom được nhưng cố ý không gom**, lý do ghi tại chỗ: `tab_doc_template` (mục 4.3) và `tab_incoming_register` (mục 9.2).

**Cái giá của việc gom vào `tab_document`:** bảng này giờ chứa ba loại bản ghi khác nhau, phân biệt bằng cột `origin`. Mọi truy vấn danh sách, tìm kiếm, báo cáo **phải lọc `origin = 1`**, và chỗ ép việc đó là **tầng dịch vụ**, không phải từng màn hình tự nhớ. Quên một chỗ là nghị định của Chính phủ hiện lẫn trong "văn bản của tôi". Xem mục 13 chỗ dễ sai số 12.

---

## 2. Quy ước bắt buộc

Bảy quy ước dưới đây áp cho **mọi bảng mới**, không có ngoại lệ. Đây là các ràng buộc đã chốt cho nền ERP, nêu lại ở đây để không phải mở tài liệu khác.

| # | Quy ước | Vì sao |
|---|---|---|
| 1 | Tên bảng bắt đầu bằng `tab_`, tên bảng và tên cột **bằng tiếng Anh, không dấu** | Bảng đang có đã theo quy ước này |
| 2 | Mọi bảng nghiệp vụ có cột `company_id` | Có 13 pháp nhân. Thiếu cột này là sau phải thêm vào bảng đã đầy dữ liệu |
| 3 | Trạng thái lưu bằng **số**, không lưu chuỗi tiếng Việt | Hiện có 30 cột trạng thái kiểu chuỗi, 11 cột chứa tiếng Việt có dấu — đó là nợ, không đẻ thêm |
| 4 | Mọi bảng có `created_at`, `created_by`, `updated_at`, `updated_by` | Dùng lại lớp `AuditMixin` đang có |
| 5 | Khóa ngoại khai đầy đủ ở tầng dữ liệu, không chỉ khai trong mã | Chống dữ liệu mồ côi |
| 6 | Bảng nào có phân quyền theo phạm vi thì **phải khai trong `SCOPE_FIELDS`** | Hiện chỉ 9 trên 28 đối tượng có khai, và chỗ thiếu khai thì **không lọc gì cả** — đó là lỗ hổng, không phải mặc định an toàn |
| 7 | Bảng mới phải được nhập vào `core/all_models.py` | Không nhập thì công cụ sinh migration **không nhìn thấy bảng**, chạy im lặng và không báo lỗi |

Thêm một quy ước riêng cho phân hệ này:

> **Bảng của phase sau vẫn tạo ngay ở bản đầu, chỉ là chưa có màn hình.** Thêm cột vào bảng trống mất một phút; thêm cột vào bảng đã có vài chục nghìn dòng thì phải canh giờ dừng hệ thống.

---

## 3. Nhóm 0 · Bốn bảng đang có phải sửa

### 3.1 `tab_company` — thêm 3 cột

| Cột thêm | Kiểu | Ý nghĩa |
|---|---|---|
| `issue_code` | VARCHAR(20), duy nhất | Mã dùng trong số hiệu văn bản. **Chỉ chữ và số, không dấu, không khoảng trắng.** Ví dụ `DEGO`, `DRGREEN` |
| `short_name` | VARCHAR(100) | Tên rút gọn để hiển thị |
| `level` | TINYINT | 1 Tập đoàn · 2 công ty thành viên · 3 đơn vị trực thuộc |

**Cẩn thận:** cột `code` đang có **không dùng làm mã số hiệu được** — nó là mã hiển thị, có thể chứa dấu và khoảng trắng. Dùng nhầm thì sinh ra số hiệu kiểu `Cty Dego-QC-012`. Phải thêm cột mới.

**Đã có sẵn:** `parent`, `legal_representative_id`, `legal_rep_title` — dùng luôn cho cây pháp nhân và cho việc xác định ai ký.

### 3.2 `tab_department` — thêm 2 cột

| Cột thêm | Kiểu | Ý nghĩa |
|---|---|---|
| `issue_code` | VARCHAR(20) | Mã dùng trong số hiệu. Ví dụ `NS`, `KT`, `HC` |
| `kind` | TINYINT | 1 phòng chức năng · 2 đơn vị kinh doanh · 3 ban dự án. **Chỉ loại 1 mới xuất hiện trong số hiệu văn bản** |

**Không đụng vào `company_id` và `manager_id` đang có.** Thiết kế văn thư gốc bỏ `company_id` khỏi phòng ban, nhưng bảng đang chạy thật có cột đó và mã nguồn Thu mua đang dùng. Cách xử lý: **giữ nguyên**, và thêm bảng nối `tab_department_company` ở mục 4.6 để mô tả phòng ban dùng chung nhiều pháp nhân. Cột cũ tiếp tục là "pháp nhân gốc của phòng ban", bảng mới trả lời "phòng này còn có mặt ở đâu, trưởng phòng ở mỗi nơi là ai".

### 3.3 `tab_file` — thêm 3 cột, bỏ dùng 1 cột

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `sha256` | CHAR(64) | Mã băm để chứng minh tệp không bị đổi, và để chống lưu trùng |
| `is_private` | BOOLEAN, mặc định `true` | Tệp mới **mặc định riêng tư**. Chỉ tệp thật sự công khai mới đặt `false` |
| `scan_status` | TINYINT | 0 chưa quét · 1 sạch · 2 nghi ngờ · 3 nhiễm. Chưa quét thì không cho tải |

Cột `url` đang lưu **đường dẫn công khai vĩnh viễn** tới tệp trên R2. Xử lý theo ba bước:

1. Ngừng ghi giá trị mới vào cột này ngay từ phase 0.
2. Xóa trắng giá trị cũ sau khi đã chuyển hết sang đường tải mới.
3. Bỏ hẳn cột ở một phase sau, khi chắc chắn không còn mã nào đọc tới.

Không xóa cột ngay ở bước 1 vì còn mã cũ đang đọc, xóa là hỏng ngay.

### 3.4 `tab_notification` — thêm 1 cột

| Cột thêm | Kiểu | Ý nghĩa |
|---|---|---|
| `app` | VARCHAR(30), mặc định `thumua` | Phân hệ sinh ra thông báo: `thumua`, `vanthu`, `hdsd`, ... |

Chuông lọc theo phân hệ đang mở. **Không tạo bảng thông báo thứ hai** — hai bảng thông báo nghĩa là hai chỗ đánh dấu đã đọc, hai chỗ đếm số chưa đọc, hai chỗ dọn dẹp.

---

## 4. Nhóm 1 · Danh mục và cấu hình — 6 bảng mới

### 4.1 `tab_doc_type` — loại văn bản

Bảng gốc của cả phân hệ. 32 dòng.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `code` | VARCHAR(10), duy nhất | `QC`, `QT`, `HDCV`, `TB`, `QD` ... |
| `name` | VARCHAR(200) | Tên đầy đủ |
| `group_code` | CHAR(1) | Nhóm A đến F |
| `description` | TEXT | Định nghĩa, dùng khi nào |
| `id_scheme` | TINYINT | **1 mã tài liệu bất biến** (`DEGO-QC-012`) · **2 số hiệu theo sổ** (`08/2026/TB-NS-DEGO`) |
| `needs_decision` | BOOLEAN | Ban hành có phải kèm một Quyết định không. **Kiểm ở mức phiên bản, không phải mức văn bản** — mỗi lần sửa lớn là phải có một Quyết định mới, xem [`05` mục 5.5](./05-vong-doi-phien-ban.md) |
| `default_secrecy` | TINYINT | Mức mật mặc định 1–4 |
| `is_confidential_type` | BOOLEAN | Cả loại là loại bảo mật |
| `needs_request` | BOOLEAN | Phải có yêu cầu được duyệt mới soạn được |
| `number_when` | TINYINT | 1 cấp số lúc tạo nháp · 2 cấp số lúc được duyệt. **Đề nghị mặc định 2** |
| `review_cycle_months` | SMALLINT | Chu kỳ rà soát, 0 là không rà |
| `retention_months` | SMALLINT | Thời hạn lưu trữ |
| `default_flow_id` | BIGINT | Luồng duyệt mặc định |
| `template_id` | BIGINT | Tệp mẫu mặc định |
| `sort_order` | INT | |
| `is_active` | BOOLEAN | |

**Loại thứ 33 đang đề nghị thêm — TL Trích lục (C20).** Chưa thêm vào danh mục, chờ Hành chính trả lời câu B12. Nếu thêm thì khai như sau, không khai kiểu khác:

| Cột | Giá trị | Vì sao |
|---|---|---|
| `id_scheme` | 2 số hiệu theo sổ | Trích lục là văn bản sự vụ, cấp lần nào ghi sổ lần đó, đếm lại từ 1 mỗi năm. **Không được để 1** — trích lục không có phiên bản 2, cần bản mới thì cấp một trích lục mới |
| `needs_decision` | FALSE | Không ban hành chế độ gì, chỉ xác nhận nội dung |
| `number_when` | 2 cấp số lúc được duyệt | Trích lục nháp chưa ai ký thì chưa được chiếm số |
| `default_secrecy` | lấy theo bản gốc, không cố định | Trích lục của công thức sản xuất và trích lục của một Thông báo không cùng mức mật |
| `review_cycle_months` | 0 | Không rà định kỳ, vòng đời buộc theo gốc qua quan hệ *trích từ* |

**Bản trích nội bộ (C19) thì không thêm loại nào** — nó mang đúng loại của bản gốc, chỉ khác ở chỗ có quan hệ *trích từ* và mức mật thấp hơn.

### 4.2 `tab_doc_type_link_rule` — quy tắc cha con

Bảng được đề xuất riêng cho yêu cầu "loại đó có cha không, văn bản hướng dẫn thì hướng dẫn cái gì". Khoảng 15–25 dòng, sửa được bằng giao diện.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `source_type_id` | BIGINT | Loại văn bản nguồn |
| `relation` | TINYINT | 1 thay thế · 2 sửa đổi · 3 bổ sung · 4 hướng dẫn · 5 kèm theo · 6 thuộc về · 7 căn cứ theo · 8 tham chiếu · 9 bãi bỏ · **10 trích từ** |
| `target_type_id` | BIGINT, cho phép rỗng | Loại đích được phép. Rỗng nghĩa là loại nào cũng được |
| `is_required` | BOOLEAN | Thiếu quan hệ này thì **không cho gửi duyệt** |
| `min_count` | SMALLINT | |
| `max_count` | SMALLINT | 0 là không giới hạn |
| `on_parent_obsolete` | TINYINT | Cha **bị bãi bỏ** thì con ra sao: 1 không làm gì · 2 đánh dấu con cần rà lại · 3 con hết hiệu lực theo cha |
| `on_parent_new_version` | TINYINT | Cha **lên phiên bản mới** thì con ra sao: 1 không làm gì · 2 đánh dấu con cần rà lại · 3 hỏi người ban hành rồi ghi nhật ký. **Đề nghị mặc định 3** |
| `inherit_code` | BOOLEAN | Con lấy mã theo cha, `DEGO-QC-012-HD01` |
| `inherit_secrecy` | BOOLEAN | Con không được thấp hơn cha |

Bảy dòng mẫu:

| Loại nguồn | Quan hệ | Loại đích | Bắt buộc | Số lượng |
|---|---|---|---|---|
| HDCV Hướng dẫn công việc | hướng dẫn | QT Quy trình | Có | đúng 1 |
| BM Biểu mẫu | thuộc về | QT, QC | Có | từ 1 |
| QC Quy chế | kèm theo | QD Quyết định | Có | đúng 1 |
| QYD Quy định | căn cứ theo | CS Chính sách | Không | 0 trở lên |
| QD Quyết định | thay thế | QD Quyết định | Không | 0 trở lên |
| bất kỳ | tham chiếu | bất kỳ | Không | 0 trở lên |
| bản trích | trích từ | bất kỳ | Có | đúng 1 |

**Quan hệ 10 *trích từ* không cấu hình được như chín quan hệ kia.** Ba cột `on_parent_obsolete`, `on_parent_new_version`, `inherit_secrecy` với dòng *trích từ* bị **khóa cứng ở tầng dịch vụ**, giao diện không cho sửa:

| Cột | Giá trị bắt buộc | Vì sao |
|---|---|---|
| `on_parent_new_version` | 2 đánh dấu con cần rà lại | Gốc đổi nội dung thì bản trích có thể đang nói sai. Không được để "không làm gì" |
| `on_parent_obsolete` | 3 con hết hiệu lực theo cha | Gốc bị bãi bỏ mà bản trích còn sống là phát tán nội dung đã bỏ |
| `inherit_secrecy` | TRUE | Mức mật bản trích **luôn ≤ gốc**, và không thấp hơn mức thật của phần được trích. Muốn thấp hơn nữa thì phải hạ mức mật tường minh, đi qua duyệt như G17 |

Đây là chỗ khác *thuộc về*: Biểu mẫu **thuộc về** Quy trình là hai văn bản **khác nội dung** nên cha đổi con chưa chắc sai. Bản trích **cùng nội dung, chỉ ít hơn**, nên cha đổi là con sai theo. Dùng chung một quan hệ cho hai việc này thì mất luôn ba ràng buộc trên.

**Vì sao một bảng quy tắc chứ không phải một cột "loại cha" trên `tab_doc_type`:** một cột chỉ nói được "loại này có cha", không nói được **cha thuộc loại gì**, **quan hệ là gì**, **bắt buộc hay không**, **cha bị bãi bỏ thì con ra sao**. Mà một loại văn bản có thể có nhiều quan hệ cùng lúc: một Quy trình vừa căn cứ theo Chính sách, vừa được hướng dẫn bởi các Hướng dẫn công việc, vừa có các Biểu mẫu thuộc về nó.

### 4.3 `tab_doc_template` — tệp mẫu

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `doc_type_id` | BIGINT | |
| `company_id` | BIGINT, cho phép rỗng | Rỗng nghĩa là dùng chung cho mọi pháp nhân |
| `name` | VARCHAR(200) | |
| `file_id` | BIGINT | Trỏ tới `tab_file` |
| `version` | VARCHAR(20) | |
| `is_active` | BOOLEAN | |

**Đã cân nhắc gom vào `tab_file_link` đang có và quyết định không gom.** `tab_file_link` có sẵn `entity`, `entity_id`, `doc_type`, `sort_order` nên về hình thức chứa được tệp mẫu, nhưng nó thiếu `company_id`, `version`, `is_active`. Thêm ba cột đó vào bảng đính kèm dùng chung cho **cả Thu mua** — bảng bị ghi mỗi lần có ai đính kèm bất cứ thứ gì — chỉ để phục vụ khoảng 40 dòng tệp mẫu là đổi một chỗ nóng lấy một chỗ nguội. Giữ bảng riêng.

### 4.4 `tab_number_sequence` — bộ đếm cấp số

Bảng nhỏ nhất nhưng quan trọng nhất trong cả tài liệu.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `scope_key` | VARCHAR(150), **duy nhất** | Khóa xác định sổ nào |
| `year` | SMALLINT | Năm hiện tại của bộ đếm |
| `current_no` | INT | Số đã cấp gần nhất |

Ba dạng `scope_key`:

| Dạng | Dùng cho | Ví dụ |
|---|---|---|
| `doc:{mã pháp nhân}:{mã loại}` | Mã tài liệu bất biến, **không reset theo năm** | `doc:DEGO:QC` |
| `out:{mã pháp nhân}:{năm}:{mã loại}` | Số hiệu văn bản đi, reset mỗi năm | `out:DEGO:2026:TB` |
| `in:{mã pháp nhân}:{năm}` | Số văn bản đến, reset mỗi năm | `in:DEGO:2026` |

**Cách cấp số — bắt buộc làm đúng:**

```python
def next_number(db, scope_key: str, year: int) -> int:
    """Cấp số kế tiếp. PHẢI chạy trong cùng transaction với việc ghi bản ghi."""
    row = (db.query(NumberSequence)
           .filter(NumberSequence.scope_key == scope_key)
           .with_for_update()          # khóa dòng, người thứ hai phải xếp hàng
           .one_or_none())
    if row is None:
        row = NumberSequence(scope_key=scope_key, year=year, current_no=0)
        db.add(row); db.flush()
    if row.year != year:               # sang năm mới thì đếm lại từ đầu
        row.year, row.current_no = year, 0
    row.current_no += 1
    return row.current_no
```

**Ba điều cấm:**

| Cấm | Vì sao |
|---|---|
| Lấy số lớn nhất rồi cộng một | Hai người bấm cùng lúc đọc ra cùng một số lớn nhất, ra hai văn bản trùng số |
| Dùng bộ đếm ngoài cơ sở dữ liệu, ví dụ Redis | Cấp số xong mà ghi bản ghi thất bại thì mất số, không lấy lại được |
| Cấp số ở một giao dịch riêng rồi mới ghi bản ghi | Có khoảng thời gian ở giữa. Trong khoảng đó, hệ thống có một số đã cấp mà chưa có văn bản nào mang nó |

Ba lớp chặn, phải có đủ cả ba: khóa dòng khi cấp · ràng buộc duy nhất ở tầng dữ liệu · cùng một giao dịch.

Bài kiểm bắt buộc trước khi nghiệm thu: mở 100 kết nối cùng lúc xin cấp số cho cùng một sổ, phải nhận về **đúng 100 số liên tiếp, không trùng, không nhảy cóc**.

### 4.5 `tab_external_party` — đơn vị gửi nhận bên ngoài

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `code` | VARCHAR(30) | |
| `name` | VARCHAR(300) | |
| `kind` | TINYINT | 1 cơ quan nhà nước · 2 đối tác · 3 khách hàng · 4 khác |
| `address`, `email`, `phone` | VARCHAR | |
| `is_active` | BOOLEAN | |

### 4.6 `tab_department_company` — phòng ban tại từng pháp nhân

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `department_id` | BIGINT | |
| `company_id` | BIGINT | |
| `manager_employee_id` | BIGINT | **Trưởng phòng của phòng đó tại pháp nhân đó** |
| `issue_code_override` | VARCHAR(20), cho phép rỗng | Khi mã phòng ở pháp nhân này khác mặc định |
| `is_active` | BOOLEAN | |

Ràng buộc: `UNIQUE(department_id, company_id)`.

Bảng này nhỏ nhưng gỡ đúng cái bẫy nêu ở [`03` mục 5](./03-lark-approver.md#5-nhóm-c--cách-chọn-người-duyệt): phòng Kế toán có mặt ở nhiều pháp nhân, trưởng phòng mỗi nơi là người khác. Không có bảng này thì luồng duyệt "gửi cho trưởng phòng của người nộp" sẽ gửi nhầm người ở nhầm công ty.

---

## 5. Nhóm 2 · Văn bản — 6 bảng mới

### 5.1 `tab_document_request` — yêu cầu văn bản

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `code` | VARCHAR(30), duy nhất | Mã yêu cầu |
| `company_id` | BIGINT | Pháp nhân |
| `department_id` | BIGINT | Phòng ban xin |
| `requester_id` | BIGINT | **ID nhân sự**, không phải ID tài khoản |
| `kind` | TINYINT | 1 soạn mới · 2 sửa văn bản đang có · 3 bãi bỏ |
| `doc_type_id` | BIGINT | Loại văn bản định soạn |
| `target_document_id` | BIGINT, cho phép rỗng | Với loại 2 và 3 thì trỏ tới văn bản cần sửa hoặc bãi bỏ |
| `title` | VARCHAR(500) | Tên văn bản dự kiến |
| `reason` | TEXT, **bắt buộc** | Vì sao cần |
| `expected_date` | DATE | Mong có trước ngày nào |
| `status` | TINYINT | 1 nháp · 2 đang duyệt · 3 đã duyệt · 4 từ chối · 5 đã hủy |
| `approved_at`, `approved_by` | | |

**Cố ý không có cột `created_document_id`.** Quan hệ "yêu cầu nào sinh ra văn bản nào" đã nằm ở `tab_document.document_request_id`. Khai thêm con trỏ ngược là **hai chỗ ghi cùng một quan hệ**, và con trỏ hai chiều thì luôn có ngày lệch nhau — lệch im lặng, không ai báo lỗi. Cần danh sách văn bản sinh từ một yêu cầu thì truy ngược, đã có chỉ mục.

Ràng buộc nghiệp vụ, đặt ở **tầng dịch vụ**: loại văn bản có `needs_request = true` thì không tạo được `tab_document` nếu không kèm một `document_request_id` có `status = 3`.

### 5.2 `tab_document` — văn bản

Bảng chính. Sau khi gom ở bản 1.1, bảng này chứa **ba loại bản ghi**, phân biệt bằng cột `origin`:

| `origin` | Là gì | Ai tạo |
|---|---|---|
| **1 nội bộ** | Văn bản do tập đoàn soạn và ban hành. Đây là loại duy nhất có phiên bản, có duyệt, có phạm vi | Người soạn |
| **2 pháp luật ngoài** | Nghị định, thông tư, luật — thứ mình *căn cứ theo* chứ không ban hành | Quản trị văn thư khai tay |
| **3 văn bản đến** | Công văn nhận từ bên ngoài. **Chưa dùng ở bản đầu**, xem mục 9.2 | Văn thư nhận |

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `origin` | TINYINT, mặc định 1 | **1 nội bộ · 2 pháp luật ngoài · 3 văn bản đến.** Xem bảng trên |
| `doc_code` | VARCHAR(50), cho phép rỗng, **duy nhất** | Mã tài liệu bất biến. `DEGO-QC-012` |
| `issue_number` | VARCHAR(80), cho phép rỗng | Số hiệu theo sổ. `08/2026/TB-NS-DEGO` |
| `seq_no` | INT, cho phép rỗng | Phần số thứ tự, tách riêng để sắp xếp và kiểm tra |
| `issue_year` | SMALLINT, cho phép rỗng | |
| `doc_type_id` | BIGINT | |
| `company_id` | BIGINT | Pháp nhân **ban hành** |
| `department_id` | BIGINT | Phòng ban chủ trì |
| `title` | VARCHAR(500) | |
| `summary` | TEXT | |
| `keywords` | VARCHAR(500) | |
| `owner_employee_id` | BIGINT | **Người chịu trách nhiệm nội dung**, không phải người gõ |
| `drafter_employee_id` | BIGINT | Người soạn |
| `signer_employee_id` | BIGINT, cho phép rỗng | Người ký ban hành |
| `secrecy_level` | TINYINT | 1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật |
| `urgency` | TINYINT | 1 thường · 2 khẩn · 3 hỏa tốc. **Độc lập với mức mật** |
| `status` | TINYINT | 1 nháp · 2 đang duyệt · 3 đã duyệt · 4 có hiệu lực · 5 bị thay thế · 6 hết hiệu lực · 7 bãi bỏ · 8 lưu trữ · 9 đã hủy |
| `effective_date` | DATE | |
| `expiry_date` | DATE, cho phép rỗng | |
| `issued_at` | DATETIME, cho phép rỗng | |
| `current_version_id` | BIGINT | Phiên bản đang hiệu lực |
| `document_request_id` | BIGINT, cho phép rỗng | Yêu cầu sinh ra nó |
| `legacy_code` | VARCHAR(80), cho phép rỗng | Số hiệu cũ thời còn dùng giấy, để tìm kiếm ra |
| `next_review_date` | DATE, cho phép rỗng | |
| `is_active` | BOOLEAN | |
| | | **Bảy cột dưới đây gom từ `tab_document_clone`, mục 5.6** |
| `source_document_id` | BIGINT, cho phép rỗng | Bản gốc, nếu bản này là clone |
| `source_version_id` | BIGINT, cho phép rỗng | **Clone từ phiên bản nào của gốc.** Cột làm nên toàn bộ giá trị của việc theo dõi clone |
| `clone_status` | TINYINT, cho phép rỗng | 1 đã gửi · 2 đang soạn · 3 đang duyệt · 4 đã ban hành · 5 từ chối áp dụng · **6 cần rà lại vì bản gốc đã lên phiên bản mới** |
| `clone_due_date` | DATE, cho phép rỗng | Hạn xử lý bản clone |
| `clone_handled_at` | DATETIME, cho phép rỗng | |
| `clone_assignee_employee_id` | BIGINT, cho phép rỗng | Ai ở pháp nhân nhận chịu trách nhiệm |
| `clone_note` | TEXT, cho phép rỗng | |
| | | **Hai cột dưới đây chỉ dùng khi `origin = 2`, gom từ `tab_legal_reference`** |
| `issuer` | VARCHAR(200), cho phép rỗng | Cơ quan ban hành: Chính phủ, Bộ Tài chính, Quốc hội |
| `external_url` | VARCHAR(500), cho phép rỗng | Đường dẫn tới bản gốc trên cổng thông tin pháp luật |
| | | **Ba cột dưới đây phục vụ báo cáo sổ văn bản đi, gom từ `tab_outgoing_register`, mục 9.1** |
| `recipient_summary` | VARCHAR(500), cho phép rỗng | Nơi nhận, ghi gọn như trên bản giấy |
| `copies` | SMALLINT, cho phép rỗng | Số bản phát hành |
| `register_note` | VARCHAR(500), cho phép rỗng | Ghi chú của văn thư khi vào sổ |

**Hai cột `urgency` và `secrecy_level` phải tách riêng.** Một thông báo hỏa tốc có thể là văn bản công khai; một quy chế lương là văn bản mật nhưng không khẩn. Gộp vào một cột là sau này không tách ra được.

**Cột `origin` kéo theo bốn hệ quả, phải làm đủ cả bốn:**

| # | Hệ quả | Xử lý |
|---|---|---|
| 1 | Bản ghi `origin = 2` không có loại văn bản nội bộ, không có pháp nhân ban hành, không có người chịu trách nhiệm | Bốn cột `doc_type_id`, `company_id`, `owner_employee_id`, `drafter_employee_id` chuyển sang **cho phép rỗng**, và ép lại bằng `CHECK` bên dưới |
| 2 | Danh sách, tìm kiếm, thống kê nếu quên lọc thì lòi nghị định ra | Bộ lọc `origin = 1` đặt ở **hàm dựng truy vấn dùng chung**, không để từng màn hình tự thêm. Muốn lấy văn bản pháp luật thì phải gọi tường minh |
| 3 | `origin = 2` không có phiên bản, không đi qua bộ máy duyệt, không có phạm vi | Chặn ở tầng dịch vụ. Nghị định chỉ có đúng một dòng `tab_document`, `current_version_id` để rỗng |
| 4 | Cấp số không áp cho `origin = 2` | `doc_code` và `issue_number` của nghị định là **số hiệu do cơ quan nhà nước đặt**, gõ tay vào, không đi qua `tab_number_sequence` |

```sql
CHECK (origin <> 1 OR (doc_type_id IS NOT NULL
                       AND company_id IS NOT NULL
                       AND owner_employee_id IS NOT NULL))
```

**Vì sao gộp văn bản pháp luật vào đây thay vì để bảng riêng:** mục 9.3 của bản cũ nói nối nghị định với quy chế nội bộ qua `tab_document_link` quan hệ *căn cứ theo*. Nhưng `tab_document_link.target_document_id` là khóa ngoại trỏ `tab_document`, nên một dòng ở bảng `tab_legal_reference` **không bao giờ làm đích của quan hệ được**. Bản cũ có hai lối thoát: hoặc thêm cột thứ hai cho `tab_document_link` và mỗi lần đọc quan hệ phải xét cả hai, hoặc dựng một bảng quan hệ thứ hai chỉ dành cho pháp luật. Cả hai đều đắt hơn một cột `origin`.

**Clone: vì sao không cần bảng riêng.** Tính năng F06 quy định clone là **sinh ngay một bản nháp** ở pháp nhân nhận, nên cột `cloned_document_id` của bảng cũ không bao giờ rỗng — bản ghi theo dõi và bản nháp luôn là một. Giữ bảng riêng nghĩa là ba chỗ cùng ghi một sự thật: `tab_document.source_document_id`, `tab_document_clone`, và dòng `tab_document_link` *căn cứ theo* `is_system`. Ba nguồn thì sớm muộn lệch, và lúc lệch thì không biết tin cái nào. Nay còn hai: cột trên bảng chính là sự thật, dòng `tab_document_link` là bản sao chỉ đọc phục vụ cây tài liệu.

Bảng theo dõi clone — "12 công ty con đang ở phiên bản nào, ai chưa đụng tới" — nay là một truy vấn trên chính `tab_document`, lọc theo `source_document_id`, so `source_version_id` với `current_version_id` của bản gốc.

### 5.3 `tab_document_version` — phiên bản

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `document_id` | BIGINT | |
| `version_no` | VARCHAR(20) | `1.0`, `1.1`, `2.0`. **Không bao giờ nằm trong số hiệu văn bản** |
| `content_html` | LONGTEXT, cho phép rỗng | Nội dung soạn trên web, nếu có |
| `file_id` | BIGINT, cho phép rỗng | Tệp Word hoặc PDF |
| `pdf_file_id` | BIGINT, cho phép rỗng | Bản PDF để xem trên trình duyệt |
| `sha256` | CHAR(64) | Mã băm nội dung |
| `change_summary` | TEXT, **bắt buộc từ phiên bản thứ hai** | Sửa gì so với bản trước |
| `change_reason` | TEXT, **bắt buộc từ phiên bản thứ hai** | Vì sao sửa |
| `change_kind` | TINYINT | **1 sửa lớn · 2 sửa nhỏ.** Quyết định luồng duyệt, việc bắt xác nhận đã đọc lại, và việc đánh dấu văn bản con |
| `status` | TINYINT | 1 nháp · 2 đang duyệt · 3 đã duyệt · 4 bị thay thế |
| `effective_from` | DATE, cho phép rỗng | Ngày phiên bản này bắt đầu có hiệu lực. **Khác với ngày được duyệt** — duyệt 20/08 mà hiệu lực 01/09 là bình thường |
| `requires_reconfirm` | BOOLEAN | Có bắt người trong phạm vi xác nhận đã đọc lại không. Mặc định lấy theo `change_kind`, sửa tay được |
| `prev_version_id` | BIGINT, cho phép rỗng | Phiên bản trước nó. Khai rõ chứ không suy từ thứ tự `version_no` |
| `created_from_request_id` | BIGINT, cho phép rỗng | Yêu cầu sửa nào sinh ra phiên bản này |
| `approved_at`, `approved_by` | | |
| `is_locked` | BOOLEAN | Đã duyệt thì bật, và **không có đường nào tắt** |

**Quy tắc cứng:** phiên bản đã duyệt là bất biến. Sửa nghĩa là tạo dòng mới, không phải cập nhật dòng cũ. Chặn ở tầng dịch vụ chứ không phải ẩn nút trên giao diện.

**Mỗi văn bản chỉ được có đúng một phiên bản đang mở.** Ép ở tầng dữ liệu, vì hai người bấm cùng lúc thì hai câu kiểm trong mã nguồn đều thấy trống:

```sql
ALTER TABLE tab_document_version
  ADD COLUMN open_slot BIGINT
    GENERATED ALWAYS AS (CASE WHEN status IN (1,2) THEN document_id END) STORED,
  ADD UNIQUE KEY uq_one_open_version (open_slot);
```

Cột sinh này bằng `document_id` khi phiên bản còn nháp hoặc đang duyệt, bằng rỗng khi đã duyệt hoặc đã bị thay thế. Ràng buộc duy nhất bỏ qua giá trị rỗng nên nhiều phiên bản cũ chung một văn bản không sao.

**Đừng nhầm `status` của phiên bản với `status` của văn bản.** Quy chế lên bản 2.0 thì `tab_document.status` **vẫn là 4 có hiệu lực**, chỉ dòng phiên bản 1.0 chuyển sang 4 bị thay thế. Nhầm chỗ này là cả công ty thấy quy chế lương biến mất khỏi danh sách đang hiệu lực. Giá trị 5 bị thay thế trên `tab_document` chỉ dùng khi bị **một văn bản khác** thay thế.

Luồng đầy đủ của việc lên phiên bản nằm ở [`05` Vòng đời phiên bản](./05-vong-doi-phien-ban.md).

Hai cột `change_summary` và `change_reason` chính là biên bản sửa đổi tài liệu mà ISO đòi hỏi — không phải làm thêm một bảng riêng cho nó.

**Tệp đính kèm dùng lại `tab_file_link` đang có**, với `entity = 'document_version'` và `entity_id` là id phiên bản. Không tạo bảng nối riêng.

### 5.4 `tab_document_scope` — phạm vi áp dụng

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `document_id` | BIGINT | |
| `dim` | TINYINT | 1 pháp nhân · 2 phòng ban · 3 cá nhân |
| `company_id` | BIGINT, cho phép rỗng | |
| `department_id` | BIGINT, cho phép rỗng | |
| `employee_id` | BIGINT, cho phép rỗng | |
| `include_children` | BOOLEAN | Áp cho cả đơn vị con |
| `mode` | TINYINT | **1 bao gồm · 2 loại trừ** |

**Ràng buộc bắt buộc ở tầng dữ liệu:**

```sql
CHECK (dim <> 2 OR company_id IS NOT NULL)
```

Tức là: chọn phòng ban thì **bắt buộc phải kèm pháp nhân**. Vì một phòng ban có mặt ở 13 pháp nhân, chọn trơ trọi "phòng Kế toán" là văn bản lan sang cả 13 công ty. Đây là lỗi rất dễ mắc và rất khó phát hiện sau khi đã ban hành, nên phải chặn ở tầng dữ liệu chứ không chỉ ở giao diện.

**Ba quy tắc khi tính ai thuộc phạm vi:**
1. Các dòng bao gồm cộng dồn với nhau.
2. **Loại trừ luôn thắng bao gồm.**
3. Không có dòng nào thì **không ai** thuộc phạm vi — không phải "mọi người".

Quy tắc 3 ngược với trực giác nhưng an toàn hơn: quên khai phạm vi thì văn bản không tới ai, người ta sẽ hỏi. Còn nếu mặc định là mọi người thì quên khai nghĩa là văn bản mật gửi cho cả tập đoàn.

### 5.5 `tab_document_link` — quan hệ giữa các văn bản

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `source_document_id` | BIGINT | |
| `target_document_id` | BIGINT | |
| `relation` | TINYINT | Mười giá trị, giống `tab_doc_type_link_rule.relation` |
| `rule_id` | BIGINT, cho phép rỗng | Quy tắc nào sinh ra quan hệ này |
| `source_version_id` | BIGINT, cho phép rỗng | Chỉ dùng cho quan hệ *trích từ*: bản trích được tách ra từ **phiên bản nào** của gốc. So với `current_version_id` của gốc để biết bản trích đã lạc hậu chưa |
| `note` | VARCHAR(500) | |
| `is_system` | BOOLEAN | Hệ thống tự tạo, **người dùng không xóa được** |

Ràng buộc: `UNIQUE(source_document_id, target_document_id, relation)`.

Quan hệ *căn cứ theo* của bản clone về bản gốc luôn có `is_system = true`. Không có màn hình nào, không có nút nào, không có gọi hàm nào xóa được dòng đó. Nếu xóa được thì sau vài tháng sẽ có bản clone mồ côi, không truy được về gốc.

Quan hệ *trích từ* cũng `is_system = true`, và **bắt buộc có `source_version_id`**. Không ghi phiên bản gốc thì sáu tháng sau không ai biết bản trích đang nói theo bản nào — đó chính là cách nội dung cũ rò rỉ ra ngoài dưới danh nghĩa văn bản còn hiệu lực.

**Cấm vòng lặp:** kiểm ngay lúc lưu. A hướng dẫn B mà B lại hướng dẫn A thì báo lỗi. Kiểm cả chuỗi dài, không chỉ kiểm hai bước.

### 5.6 Theo dõi các bản clone — **đã gom vào `tab_document`**

Bản 1.0 của tài liệu này có một bảng `tab_document_clone` riêng. Bản 1.1 bỏ bảng đó, chuyển thành **bảy cột trên `tab_document`** (mục 5.2), vì bản ghi theo dõi và bản nháp được clone luôn luôn là cùng một thứ.

Đối chiếu cột cũ sang cột mới, để ai đọc bản 1.0 rồi thì tra được:

| Cột cũ ở `tab_document_clone` | Nay nằm ở đâu |
|---|---|
| `source_document_id` | `tab_document.source_document_id` |
| `source_version_id` | `tab_document.source_version_id` |
| `target_company_id` | `tab_document.company_id` — pháp nhân của chính bản clone |
| `cloned_document_id` | Chính là `tab_document.id` |
| `status` | `tab_document.clone_status` |
| `due_date`, `handled_at`, `assignee_employee_id`, `note` | `clone_due_date`, `clone_handled_at`, `clone_assignee_employee_id`, `clone_note` |
| `sent_at` | `tab_document.created_at` — bản nháp sinh ra đúng lúc gửi |

Ràng buộc `UNIQUE(source_document_id, target_company_id)` chuyển thành chỉ mục duy nhất trên `tab_document(source_document_id, company_id)` khi `source_document_id` khác rỗng. Vẫn chặn đúng cái cần chặn: **một bản gốc không được clone hai lần xuống cùng một pháp nhân**.

Cơ chế "bản gốc lên phiên bản thì con phải rà lại" giữ nguyên, chỉ đổi chỗ chạy: khi bản gốc lên 2.0, hệ thống quét các dòng `tab_document` có `source_document_id` trỏ về nó, dòng nào có `source_version_id` lệch với `current_version_id` hiện tại thì chuyển `clone_status = 6` và báo cho `clone_assignee_employee_id`.

Việc bỏ bảng **không làm mất** thứ mà quyết định "tuyệt đối không nhân bản" trước đây lo: mọi bản clone vẫn dẫn ngược về gốc, vẫn biết theo phiên bản nào, vẫn có bảng theo dõi tập trung. Chỉ khác là bảng theo dõi nay là một truy vấn chứ không phải một bảng.

---

## 6. Nhóm 3 · Bộ máy phê duyệt dùng chung — 6 bảng mới

Sáu bảng này **không dành riêng cho văn bản**. Chúng nhận mọi loại chứng từ, và sau này thay 5 luồng duyệt viết tay của Thu mua.

### 6.1 `tab_approval_flow` — luồng duyệt

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `code` | VARCHAR(50) | |
| `name` | VARCHAR(200) | |
| `entity` | VARCHAR(50) | Áp cho loại chứng từ nào: `document`, `document_request`, `purchase_order`, ... |
| `doc_type_id` | BIGINT, cho phép rỗng | Với văn bản thì thêm điều kiện theo loại văn bản |
| `company_id` | BIGINT, cho phép rỗng | Rỗng nghĩa là áp cho mọi pháp nhân |
| `department_id` | BIGINT, cho phép rỗng | |
| `condition_json` | JSON | Điều kiện chọn luồng, ví dụ số tiền từ bao nhiêu tới bao nhiêu |
| `version_no` | INT | Tăng mỗi lần sửa |
| `duplicate_mode` | TINYINT | **1 bỏ qua khi trùng liền kề · 2 bỏ qua khi trùng bất kỳ chỗ nào trước · 3 không bỏ qua** |
| `on_no_approver` | TINYINT | **1 đẩy cho quản trị · 2 dùng người thay thế · 3 lên trưởng phòng.** Không có giá trị "tự động duyệt qua" |
| `priority` | INT | Nhiều luồng cùng khớp thì lấy luồng có số nhỏ hơn |
| `is_active` | BOOLEAN | |

Cột `on_no_approver` **cố ý không có giá trị "tự động duyệt qua"**. Lark có tùy chọn đó; với văn bản nó tạo ra văn bản có hiệu lực mà không ai chịu trách nhiệm. Không khai giá trị thì sau này không ai bật nhầm được.

### 6.2 `tab_approval_node` — các bước trong luồng

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `flow_id` | BIGINT | |
| `seq` | INT | Thứ tự |
| `name` | VARCHAR(200) | Tên bước hiện cho người dùng |
| `node_kind` | TINYINT | 1 phê duyệt · 2 nhận bản sao · 3 điều kiện rẽ nhánh · 4 xử lý việc |
| `flow_role` | TINYINT | 1 đề xuất · 2 thực hiện · 3 kiểm tra · 4 phê duyệt |
| `approver_kind` | TINYINT | 1 người cụ thể · 2 vai trò · 3 trưởng phòng người nộp · 4 lên n cấp · 5 người đại diện pháp nhân · 6 lấy từ ô trên phiếu · 7 cả phòng ban |
| `approver_ref` | VARCHAR(200) | Giá trị đi kèm: id nhân sự, mã vai trò, số cấp, tên ô |
| `multi_mode` | TINYINT | 1 một người là đủ · 2 tất cả phải duyệt · 3 lần lượt · 4 đủ tỷ lệ |
| `quorum` | SMALLINT | Dùng với chế độ 4 |
| `fallback_employee_id` | BIGINT, cho phép rỗng | **Người thay thế khi người duyệt đã nghỉ việc** |
| `condition_json` | JSON | Điều kiện để đi vào nhánh này |
| `is_default_branch` | BOOLEAN | **Nhánh nhận phiếu khi không điều kiện nào đúng.** Mỗi chỗ rẽ phải có đúng một nhánh mặc định |
| `sla_hours` | INT | Hạn xử lý |
| `min_secrecy_required` | TINYINT | Mức mật tối thiểu người duyệt bước này phải có |
| `next_node_id` | BIGINT, cho phép rỗng | |

`is_default_branch` là cột chống mất phiếu. Không có nó thì phiếu rơi vào trạng thái không nhánh nào nhận, biến mất khỏi mọi danh sách, tới lúc có người đi hỏi mới phát hiện.

### 6.3 `tab_approval_instance` — một lần chạy luồng

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `flow_id` | BIGINT | |
| `flow_version_no` | INT | Chạy theo bản luồng nào |
| `flow_snapshot` | JSON | **Bản chụp toàn bộ định nghĩa luồng lúc khởi tạo** |
| `entity` | VARCHAR(50) | |
| `entity_id` | BIGINT | Chứng từ đang được duyệt |
| `company_id` | BIGINT | |
| `submitter_employee_id` | BIGINT | |
| `status` | TINYINT | 1 đang chạy · 2 đã duyệt xong · 3 bị từ chối · 4 bị rút · 5 đã trả lại |
| `current_node_id` | BIGINT, cho phép rỗng | |
| `started_at`, `finished_at` | DATETIME | |

Cột `flow_snapshot` là cột giải quyết vấn đề "sửa luồng trong lúc có phiếu đang chạy". Phiếu chạy theo bản chụp của chính nó, không tham chiếu tới bản luồng đang sống. Sửa luồng bao nhiêu lần cũng không ảnh hưởng phiếu đang chạy.

Chỉ mục: `INDEX(entity, entity_id)` và `INDEX(status, company_id)`.

### 6.4 `tab_approval_task` — việc giao cho từng người

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `instance_id` | BIGINT | |
| `node_id` | BIGINT | |
| `assignee_employee_id` | BIGINT | **ID nhân sự** |
| `original_assignee_id` | BIGINT, cho phép rỗng | Ai là người đáng lẽ xử lý, khi việc được chuyển đi |
| `assign_reason` | TINYINT | 1 giao thường · 2 theo ủy quyền · 3 người thay thế vì đã nghỉ · 4 đẩy cho quản trị · 5 được chuyển tiếp |
| `status` | TINYINT | 1 đang chờ · 2 đã duyệt · 3 từ chối · 4 trả lại · 5 **tự động qua vì trùng người** · 6 bị hủy |
| `due_at` | DATETIME | |
| `completed_at` | DATETIME, cho phép rỗng | |
| `reminded_count` | SMALLINT | Đã nhắc mấy lần |

Trạng thái 5 là chỗ ghi lại việc "trùng thao tác thì bỏ qua". Phải là một trạng thái riêng, không được để trống và cũng không được ghi thành "đã duyệt" — bản in dấu vết duyệt cần phân biệt được **người này ký** với **bước này tự qua vì người này đã ký ở bước trước**.

Chỉ mục quan trọng nhất của cả hệ thống: `INDEX(assignee_employee_id, status)` — đây là truy vấn của màn hình "việc của tôi", chạy mỗi lần ai đó mở trang chủ.

### 6.5 `tab_approval_action` — nhật ký hành động duyệt

Bảng **chỉ ghi thêm**, không sửa, không xóa.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `instance_id` | BIGINT | |
| `task_id` | BIGINT, cho phép rỗng | |
| `node_id` | BIGINT, cho phép rỗng | |
| `action` | TINYINT | 1 nộp · 2 duyệt · 3 từ chối · 4 trả lại · 5 rút · 6 nộp lại · 7 chuyển tiếp · 8 thêm người duyệt · 9 **tự động qua vì trùng** · 10 giao cho người thay thế · 11 nhắc |
| `actor_employee_id` | BIGINT | Người thật sự bấm |
| `on_behalf_of_id` | BIGINT, cho phép rỗng | **Duyệt thay cho ai** |
| `delegation_id` | BIGINT, cho phép rỗng | Theo ủy quyền nào |
| `comment` | TEXT | |
| `return_to_node_id` | BIGINT, cho phép rỗng | Trả lại về bước nào |
| `ip`, `user_agent` | VARCHAR | |
| `created_at` | DATETIME | |

Ba cột `actor_employee_id`, `on_behalf_of_id`, `delegation_id` là để bản in dấu vết duyệt ghi được đúng câu **"ông B duyệt thay ông A theo ủy quyền số 12"**. Chỉ ghi một người là sau này không phân biệt được ai chịu trách nhiệm.

### 6.6 `tab_delegation` — ủy quyền

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `from_employee_id` | BIGINT | |
| `to_employee_id` | BIGINT | |
| `entity` | VARCHAR(50), cho phép rỗng | Rỗng nghĩa là mọi loại chứng từ |
| `company_id` | BIGINT, cho phép rỗng | |
| `from_date`, `to_date` | DATE | **Bắt buộc có hạn** |
| `reason` | VARCHAR(500) | |
| `created_by_admin` | BOOLEAN | Quản trị đặt hộ |
| `is_active` | BOOLEAN | |

Ràng buộc ở tầng dịch vụ: **cấm ủy quyền dây chuyền.** A ủy cho B thì B không được ủy tiếp cho C phần việc nhận từ A. Kiểm lúc lưu, báo lỗi rõ ràng.

---

## 7. Nhóm 4 · Ban hành và phân phối — 2 bảng mới

### 7.1 `tab_document_recipient` — nơi nhận, và ai đã đọc

Bản 1.0 tách làm hai bảng `tab_distribution` (gửi cho ai) và `tab_read_receipt` (ai đã đọc). Bản 1.1 gộp một, vì **hai bảng cùng một hạt dữ liệu**: một người nhận, một phiên bản. Tách ra thì câu hỏi thường gặp nhất của văn thư — *"gửi 240 người, bao nhiêu người đã đọc, ai chưa"* — phải nối hai bảng, mà nối bằng cặp khóa không hoàn toàn khớp nhau.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `document_id` | BIGINT | |
| `version_id` | BIGINT | **Gắn với phiên bản, không gắn với văn bản** |
| `recipient_kind` | TINYINT | 1 nhân sự · 2 phòng ban · 3 pháp nhân · 4 đơn vị bên ngoài |
| `recipient_id` | BIGINT | Id nhân sự, phòng ban hoặc pháp nhân |
| `external_party_id` | BIGINT, cho phép rỗng | Dùng khi `recipient_kind = 4` |
| `channels` | TINYINT | **Tập hợp kênh, cộng dồn:** 1 chuông · 2 thư · 4 bản giấy · 8 gửi ra ngoài. Gửi cả chuông lẫn thư thì ghi 3 |
| `send_status` | TINYINT | 1 chờ gửi · 2 đã gửi · 3 gửi lỗi |
| `sent_at` | DATETIME, cho phép rỗng | |
| `error` | VARCHAR(500), cho phép rỗng | |
| `required` | BOOLEAN | Bắt buộc xác nhận đã đọc, hay chỉ cần nhận thông báo |
| `due_date` | DATE, cho phép rỗng | Hạn xác nhận |
| `read_at` | DATETIME, cho phép rỗng | Lần mở đầu tiên |
| `confirmed_at` | DATETIME, cho phép rỗng | Lúc bấm nút xác nhận |
| `ip` | VARCHAR(45), cho phép rỗng | |

Ràng buộc: `UNIQUE(version_id, recipient_kind, recipient_id)`.

**Cột `channels` là tập hợp chứ không phải một dòng mỗi kênh.** Đây là điều kiện để việc gộp bảng đứng vững: nếu mỗi kênh một dòng thì một người nhận qua hai kênh sẽ có hai dòng, và ràng buộc duy nhất ở trên vỡ ngay — kéo theo việc đếm "bao nhiêu người đã đọc" đếm trùng. Một người nhận, một dòng, gửi qua mấy kênh thì cộng vào `channels`.

**Gắn vào phiên bản chứ không vào văn bản** là điểm mấu chốt, giữ nguyên từ bản 1.0: quy chế lên bản 2.0 thì mọi người **phải xác nhận lại**. Nếu gắn vào văn bản thì người đã xác nhận bản 1.0 vẫn hiện là đã đọc, trong khi họ chưa từng đọc nội dung mới.

**Quan hệ với `tab_email_log` đang có.** Thu mua đã có bảng `tab_email_log` ghi từng lần gửi thư thật kèm lỗi SMTP. Bảng này **không thay thế nó và không được làm lại nó**. Phân vai rõ: `tab_document_recipient` ghi *đã định gửi cho ai và người đó đọc chưa*; `tab_email_log` ghi *lần gửi thư đó ra sao*. Cột `send_status` ở đây là kết quả gần nhất, chi tiết vì sao lỗi thì tra sang `tab_email_log`.

### 7.2 `tab_signature` — chữ ký

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `document_id` | BIGINT | |
| `version_id` | BIGINT | |
| `signer_employee_id` | BIGINT | |
| `sign_kind` | TINYINT | **1 ký điện tử nội bộ · 2 ký số có chứng thư · 3 ký giấy đã quét lên** |
| `signed_at` | DATETIME | |
| `content_sha256` | CHAR(64) | Ký vào nội dung nào |
| `cert_serial` | VARCHAR(100), cho phép rỗng | |
| `cert_issuer` | VARCHAR(200), cho phép rỗng | |
| `signature_blob` | BLOB, cho phép rỗng | |
| `ip`, `user_agent` | VARCHAR | |

Cột `sign_kind` phải hiện rõ trên giao diện. Ký điện tử nội bộ có giá trị trong nội bộ tập đoàn; ký số có chứng thư mới có giá trị với bên ngoài. Người dùng không được phép nhầm hai thứ này, và cách chắc chắn nhất để họ không nhầm là **ghi rõ ngay cạnh chữ ký** chứ không giấu trong tài liệu hướng dẫn.

Phần xác nhận đã đọc **không còn là bảng riêng** — đã gộp vào mục 7.1. Bảng tạo đủ cột ngay ở bản đầu, màn hình xác nhận làm sau, chờ trả lời câu hỏi ở [`00`](./00-danh-gia-va-cau-hoi.md).

---

## 8. Nhóm 5 · Quyền truy cập — 5 bảng mới

### 8.1 `tab_user_clearance` — mức mật được phép của từng người

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `user_id` | BIGINT | |
| `company_id` | BIGINT, cho phép rỗng | Mức mật có thể khác nhau ở từng pháp nhân |
| `level` | TINYINT | 1 đến 4 |
| `granted_by` | BIGINT | Ai cấp |
| `granted_at` | DATETIME | |
| `valid_to` | DATE, cho phép rỗng | **Nên có hạn và phải gia hạn** |
| `reason` | VARCHAR(500) | |
| `is_active` | BOOLEAN | |

Không có dòng nào thì mặc định là mức 2 Nội bộ. Mức 3 và mức 4 **luôn phải cấp tường minh**, không suy ra từ chức danh.

Lý do bắt hạn: quyền xem tài liệu mật là thứ chỉ tăng chứ không bao giờ tự giảm nếu không có cơ chế hết hạn. Sau ba năm sẽ có vài chục người giữ mức 4 mà không ai nhớ vì sao.

### 8.2 `tab_document_acl` — chia sẻ đích danh trên từng văn bản

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `document_id` | BIGINT | |
| `subject_kind` | TINYINT | 1 nhân sự · 2 phòng ban · 3 pháp nhân · 4 vai trò · **5 nhóm chia sẻ tự đặt** |
| `subject_id` | BIGINT | |
| `perm` | TINYINT | 1 xem · 2 tải về · 3 sửa · 4 duyệt |
| `effect` | TINYINT | **1 cho phép · 2 cấm** |
| `valid_from`, `valid_to` | DATE, cho phép rỗng | |
| `granted_by` | BIGINT | |
| `reason` | VARCHAR(500) | |
| `can_reshare` | BOOLEAN | **Mặc định tắt.** Người được chia không được chia tiếp |
| `override_clearance` | BOOLEAN | Chia đặc cách cho người chưa đủ mức mật. Xem bên dưới |
| `override_approved_by` | BIGINT, cho phép rỗng | Ai duyệt việc đặc cách |
| `override_approved_at` | DATETIME, cho phép rỗng | |
| `revoked_at` | DATETIME, cho phép rỗng | Thu hồi là **đánh dấu**, không xóa dòng |
| `revoked_by` | BIGINT, cho phép rỗng | |
| `revoke_reason` | VARCHAR(500), cho phép rỗng | |

**Hai quy tắc vàng, không có ngoại lệ:**

| Quy tắc | Nghĩa |
|---|---|
| **Cấm luôn thắng cho phép** | Một dòng `effect = 2` ở bất kỳ lớp nào là chặn, kể cả khi có mười dòng cho phép |
| **Chia sẻ không tự vượt được mức mật** | Chia văn bản mức 4 cho người có mức 2 thì người đó **vẫn không xem được**, trừ khi có dòng đặc cách đã được duyệt |

Cột `perm` tách **xem** và **tải về** thành hai quyền riêng. Đây là ý lấy từ HrOnline và nó đúng: có tài liệu cho người ta đọc trên màn hình nhưng không cho lưu về máy.

**Chia sẻ đặc cách — cửa duy nhất vượt được mức mật**

Không có cửa này thì thiết kế bế tắc: văn bản Tuyệt mật chỉ giám đốc thấy, giám đốc cần đưa xuống nhà máy, bấm chia sẻ, nhà máy vẫn không thấy gì. Có cửa này nhưng không khóa thì mức mật thành hình vẽ. Nên cửa này có **bốn điều kiện bắt buộc**, ép ở tầng dữ liệu:

```sql
CHECK (override_clearance = 0 OR (valid_to IS NOT NULL
                                  AND override_approved_by IS NOT NULL
                                  AND subject_kind = 1))
```

1. **Bắt buộc có hạn.** Đặc cách vô thời hạn thì bằng nâng mức mật, mà nâng mức mật thì phải nâng đàng hoàng.
2. **Bắt buộc có người duyệt.** Người duyệt phải có mức mật **bằng hoặc cao hơn** mức của văn bản.
3. **Chỉ chia cho đích danh nhân sự** (`subject_kind = 1`). Đặc cách cho cả một phòng ban 40 người thì đó không còn là ngoại lệ.
4. **Chỉ được `perm = 1 xem`.** Đặc cách không kèm quyền tải về.

**Chia cho phòng ban khác chia cho đích danh — phải ghi rõ trên màn hình:**

| Chia cho | Người mới vào phòng | Người chuyển đi |
|---|---|---|
| Phòng ban (`subject_kind = 2`) | **Tự có quyền**, không ai bấm gì | **Tự mất quyền** |
| Đích danh (`subject_kind = 1`) | Không có gì | **Vẫn giữ quyền** cho tới khi bị thu hồi tay hoặc hết hạn |

Hai hành vi này ngược nhau và hậu quả khác hẳn. Người chia phải biết mình đang chọn cái nào chứ không phải đoán.

**Chia sẻ không lan xuống văn bản con.** Chia một Quy trình không tự chia các Hướng dẫn công việc thuộc nó — con hoàn toàn có thể mật hơn cha.

**Thu hồi: ba mức, phải phân biệt**

| Mức | Làm được gì | Ghi chú |
|---|---|---|
| 1 · Thu hồi quyền xem | Có hiệu lực **ngay** | Đặt `revoked_at`, **không xóa dòng**. Phải gọi `perm_cache_clear` ngay, không thì tới 60 giây sau mới có tác dụng |
| 2 · Thu hồi link tệp | Link tạm sống 60–120 giây nên tự chết | **Chỉ đúng nếu N02 đã làm.** Còn cơ chế link công khai R2 thì link đã phát ra là không thu hồi được — đây là lý do N02 nằm ở phase 0 |
| 3 · Tệp đã tải về máy, ảnh chụp màn hình, bản in | **Không thu hồi được, không có cách nào** | Cái duy nhất làm được là **biết ai đã tải**, tra từ `tab_file_access_log` |

Nên màn hình thu hồi phải hiện ngay dòng: *"3 người đã tải tệp về trước khi bị thu hồi: ..."*. Đây là thông tin quan trọng nhất trong cả thao tác thu hồi — nó trả lời câu "giờ phải đi nói chuyện với ai".

Và đó cũng là lý do tính năng G09 (mức Tuyệt mật thì chặn tải, chỉ xem trên web kèm dấu chìm mang tên người xem) **phải nằm ở bản 1**, không để lại bản 2. Đã cho tải thì mọi cơ chế thu hồi phía trên chỉ còn ý nghĩa hình thức.

### 8.2b `tab_share_group` và `tab_share_group_member` — nhóm chia sẻ tự đặt

Trường hợp thật: "tổ dự án sản phẩm X" gồm 6 người ở 3 phòng khác nhau. Không phải phòng ban, không phải vai trò phân quyền. Thiếu bảng này thì người ta chia tay 6 lần rồi quên thu hồi 6 lần.

| `tab_share_group` | Kiểu | Ý nghĩa |
|---|---|---|
| `id`, `company_id`, `name`, `description` | | |
| `owner_employee_id` | BIGINT | Người chịu trách nhiệm danh sách thành viên |
| `is_active` | BOOLEAN | |

| `tab_share_group_member` | Kiểu | Ý nghĩa |
|---|---|---|
| `id`, `group_id`, `employee_id` | | |
| `added_by`, `added_at` | | |
| `removed_at`, `removed_by` | cho phép rỗng | Ra khỏi nhóm cũng là đánh dấu, không xóa dòng |

Ràng buộc: `UNIQUE(group_id, employee_id, removed_at)`.

Thêm người vào nhóm là **cấp quyền cho mọi văn bản đang chia cho nhóm đó**. Nên thao tác này phải vào nhật ký, và màn hình phải hiện trước: "nhóm này đang được chia 7 văn bản, trong đó 2 văn bản mức Mật".

### 8.3 `tab_file_access_log` — nhật ký truy cập tệp

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT | |
| `file_id` | BIGINT | |
| `document_id` | BIGINT, cho phép rỗng | |
| `user_id` | BIGINT | |
| `action` | TINYINT | 1 xem · 2 tải về · 3 in · 4 sinh link tạm |
| `ip`, `user_agent` | VARCHAR | |
| `created_at` | DATETIME | |

Bảng này sinh nhiều dòng, phải có kế hoạch dọn từ đầu: giữ chi tiết 24 tháng, cũ hơn thì gộp thành số liệu tổng.

**Vì sao tách khỏi `tab_audit_log` đang có:** khối lượng khác hẳn nhau. Nhật ký thao tác ghi khi người ta sửa dữ liệu; nhật ký truy cập tệp ghi cả khi người ta chỉ mở ra xem. Gộp chung thì bảng nhật ký chính phình lên và các truy vấn hiện có chậm theo.

---

## 9. Nhóm 6 · Một bảng tạo sớm, dùng sau

Bản 1.0 có ba bảng ở nhóm này. Bản 1.1 còn một: hai bảng kia đã gom về `tab_document`.

### 9.1 Sổ văn bản đi — **là báo cáo, không phải bảng**

Bản 1.0 đề nghị bảng `tab_outgoing_register`. Bỏ, vì mười một cột của nó thì tám cột đã nằm nguyên trên `tab_document`: `company_id`, `issue_year`, `seq_no`, `document_id`, `issue_number`, `issued_at`, `signer_employee_id`, và bản thân dòng văn bản. Ba cột còn lại — `recipient_summary`, `copies`, `note` — đã thêm vào `tab_document` ở mục 5.2. Sổ văn bản đi nay là **một truy vấn**: lọc `origin = 1`, đã ban hành, theo pháp nhân và năm, sắp theo `seq_no`.

**Việc bỏ bảng còn gỡ một mâu thuẫn.** Bản 1.0 đặt cho sổ đi ràng buộc `UNIQUE(company_id, year, seq_no)`. Nhưng cách cấp số ở mục 4.4 dùng khóa `out:{mã pháp nhân}:{năm}:{mã loại}`, nghĩa là **số thứ tự đếm lại từ 1 theo từng loại văn bản**. Trong cùng một pháp nhân, cùng một năm, Thông báo số 8 và Quyết định số 8 cùng tồn tại là chuyện bình thường — và ràng buộc kia chặn đúng chuyện bình thường đó. Hai lối ra: bỏ bảng sổ (đang chọn), hoặc giữ bảng và mở thêm một bộ đếm thứ hai không kèm mã loại, tức là mỗi văn bản mang hai số. Cách thứ hai đắt và khó giải thích với người dùng.

Ràng buộc thật sự cần thì đã có ở mục 11: `UNIQUE(company_id, issue_year, doc_type_id, seq_no)` trên `tab_document` — đúng bốn chiều mà bộ đếm đang dùng.

### 9.2 `tab_incoming_register` — sổ văn bản đến

| Cột | Kiểu |
|---|---|
| `id`, `company_id`, `year`, `seq_no`, `received_date`, `sender_party_id`, `sender_doc_number`, `sender_doc_date`, `title`, `file_id`, `assigned_employee_id`, `due_date`, `handled_at`, `status`, `note` | |

Ràng buộc: `UNIQUE(company_id, year, seq_no)`. Ở đây ràng buộc này **đúng**, vì số đến dùng khóa `in:{mã pháp nhân}:{năm}` không kèm loại — một sổ duy nhất cho cả pháp nhân.

**Đã cân nhắc gom vào `tab_document` với `origin = 3` và quyết định không gom.** Văn bản đến có vòng đời khác hẳn: không phiên bản, không duyệt, không phạm vi, không ban hành — đổi lại có giao người xử lý và hạn xử lý. Gom vào nghĩa là nhét bốn cột chết vào bảng nóng nhất của cả phân hệ, đổi lấy việc bớt một bảng thuộc phase 9. Cột `origin = 3` vẫn khai sẵn ở mục 5.2, để sau này nếu văn bản đến cần làm đích của quan hệ *căn cứ theo* thì đã có đường, không phải sửa lại thiết kế.

### 9.3 Văn bản pháp luật tham chiếu — **đã gom vào `tab_document`**

Bản 1.0 đề nghị bảng `tab_legal_reference`. Bỏ, thay bằng `tab_document` với `origin = 2`. Lý do đầy đủ ở mục 5.2. Đối chiếu cột:

| Cột cũ | Nay là |
|---|---|
| `number` | `issue_number` — số hiệu do cơ quan nhà nước đặt, gõ tay |
| `name` | `title` |
| `issuer` | `issuer` — cột mới trên `tab_document` |
| `issued_date` | `issued_at` |
| `effective_date`, `expiry_date` | Trùng tên, đã có sẵn |
| `url` | `external_url` — cột mới |
| `status` | `status`, dùng 4 có hiệu lực và 6 hết hiệu lực |
| `note` | `summary` |

Việc quan trọng nhất vẫn làm được y nguyên, mà lại làm bằng cơ chế có sẵn: một nghị định hết hiệu lực thì đổi `status`, rồi đọc `tab_document_link` chiều ngược để liệt kê mọi quy chế nội bộ đang *căn cứ theo* nó. Ở bản 1.0 câu truy vấn này không chạy được, vì nghị định không nằm trong bảng mà `target_document_id` trỏ tới.

---

## 10. Chỉ mục bắt buộc

Không có mấy chỉ mục này thì hệ thống chạy được ở giai đoạn chạy thử với 200 văn bản, rồi chậm dần và không ai biết vì sao.

| Bảng | Chỉ mục | Phục vụ |
|---|---|---|
| `tab_document` | `(origin, company_id, doc_type_id, status)` | Màn hình danh sách và bộ lọc. **`origin` đứng đầu** vì mọi truy vấn đều lọc nó |
| `tab_document` | `(origin, status, effective_date)` | Văn bản đang hiệu lực, sắp hết hiệu lực |
| `tab_document` | `(doc_code)` duy nhất, `(issue_number)`, `(legacy_code)` | Tìm theo số hiệu |
| `tab_document` | `(company_id, issue_year, doc_type_id, seq_no)` | Sổ văn bản đi, mục 9.1 |
| `tab_document` | `(source_document_id, clone_status)` | Bảng theo dõi clone, mục 5.6 |
| `tab_document_version` | `(document_id, version_no)` | Danh sách phiên bản |
| `tab_document_scope` | `(document_id)`, `(company_id, department_id)` | Tính ai thuộc phạm vi |
| `tab_document_link` | `(source_document_id)`, `(target_document_id)` | Cây tài liệu, **cả hai chiều** |
| `tab_document_acl` | `(document_id, subject_kind, subject_id)`, `(subject_kind, subject_id, revoked_at)` | Kiểm quyền mỗi lần mở văn bản; chỉ mục thứ hai cho màn hình "văn bản đang chia cho tôi" và cho việc rà soát định kỳ |
| `tab_share_group_member` | `(group_id, removed_at)`, `(employee_id, removed_at)` | Tính thành viên hiện tại của nhóm |
| `tab_approval_task` | **`(assignee_employee_id, status)`** | Màn hình việc của tôi — truy vấn chạy nhiều nhất |
| `tab_approval_task` | `(instance_id, node_id)` | |
| `tab_approval_instance` | `(entity, entity_id)`, `(status, company_id)` | |
| `tab_approval_action` | `(instance_id, created_at)` | Bản in dấu vết duyệt |
| `tab_number_sequence` | `(scope_key)` duy nhất | Cấp số |
| `tab_file_access_log` | `(file_id, created_at)`, `(user_id, created_at)` | Tra cứu khi có sự cố |
| `tab_document_recipient` | `(version_id, recipient_kind, recipient_id)` duy nhất, `(recipient_id, confirmed_at)`, `(version_id, confirmed_at)` | Ai đã đọc, ai chưa — chỉ mục thứ ba cho báo cáo đếm theo phiên bản |

---

## 11. Ràng buộc phải đặt ở tầng dữ liệu

Đây là các ràng buộc **không được chỉ kiểm trong mã**. Mã có bug, có đường vòng, có script chạy tay; tầng dữ liệu thì không.

| Bảng | Ràng buộc |
|---|---|
| `tab_document` | `UNIQUE(doc_code)` khi khác rỗng |
| `tab_document` | `UNIQUE(company_id, issue_year, doc_type_id, seq_no)` khi khác rỗng |
| `tab_document` | `UNIQUE(source_document_id, company_id)` khi `source_document_id` khác rỗng — một bản gốc không clone hai lần xuống cùng một pháp nhân |
| `tab_document` | `CHECK (origin <> 1 OR (doc_type_id IS NOT NULL AND company_id IS NOT NULL AND owner_employee_id IS NOT NULL))` |
| `tab_number_sequence` | `UNIQUE(scope_key)` |
| `tab_document_scope` | `CHECK (dim <> 2 OR company_id IS NOT NULL)` |
| `tab_document_link` | `UNIQUE(source_document_id, target_document_id, relation)` |
| `tab_document_link` | `CHECK (source_document_id <> target_document_id)` |
| `tab_department_company` | `UNIQUE(department_id, company_id)` |
| `tab_document_recipient` | `UNIQUE(version_id, recipient_kind, recipient_id)` |
| `tab_doc_type_link_rule` | `UNIQUE(source_type_id, relation, target_type_id)` |
| `tab_approval_action` | Tài khoản ứng dụng **chỉ được cấp quyền thêm và đọc**, không có quyền sửa và xóa |
| `tab_audit_log` | Như trên |

Hai dòng cuối làm ở tầng phân quyền của MySQL, không làm trong mã ứng dụng. Nhật ký mà sửa được thì không còn là nhật ký.

---

## 12. Thứ tự chạy migration

Chạy theo phase, mỗi phase một hoặc vài migration, không dồn một lần.

| Migration | Nội dung | Phase |
|---|---|---|
| M1 | `tab_file` thêm 3 cột; `tab_notification` thêm `app` | 0 |
| M2 | `tab_company` thêm 3 cột; `tab_department` thêm 2 cột; tạo `tab_department_company` | 1 |
| M3 | `tab_doc_type`, `tab_doc_type_link_rule`, `tab_doc_template`, `tab_external_party` | 1 |
| M4 | `tab_number_sequence` | 1 |
| M5 | `tab_incoming_register` (tạo sớm) | 1 |
| M6 | `tab_document_request`, `tab_document`, `tab_document_version` | 2 |
| M7 | `tab_document_link` | 2 |
| M8 | `tab_approval_flow`, `tab_approval_node`, `tab_approval_instance`, `tab_approval_task`, `tab_approval_action`, `tab_delegation` | 3 |
| M9 | `tab_document_scope`, `tab_document_recipient`, `tab_signature` | 4 |
| M10 | `tab_user_clearance`, `tab_share_group`, `tab_share_group_member`, `tab_document_acl`, `tab_file_access_log` | 5 |
| M11 | Xóa trắng rồi bỏ cột `tab_file.url` | sau khi chạy thật ổn |

Bản 1.1 bớt một migration so với bản 1.0, và **M6 nặng thêm** vì `tab_document` nay gánh thêm 12 cột gom về. Không tách M6 làm hai: các cột đó phải có mặt ngay từ lúc tạo bảng, thêm sau là đúng cái việc mà quy ước ở mục 2 muốn tránh.

**Ba điều phải nhớ khi viết migration:**

1. **Bảng mới phải nhập vào `core/all_models.py`.** Không nhập thì công cụ sinh migration không thấy bảng, chạy xong không báo lỗi gì, và phải mất một buổi để tìm ra vì sao bảng không được tạo.
2. **Không chạy câu lệnh có chữ tiếng Việt thẳng qua dòng lệnh mysql.** Chữ bị mã hóa hai lần thành ký tự lạ, và sau đó không sửa được nữa. Dữ liệu tiếng Việt phải nạp bằng migration hoặc bằng script Python.
3. **Cột `is_active` mặc định là gì thì ghi rõ trong migration**, đừng để mã ứng dụng tự đoán.

---

## 13. Mười hai chỗ dễ sai nhất

| # | Chỗ dễ sai | Hậu quả | Cách tránh |
|---|---|---|---|
| 1 | Dùng `tab_company.code` làm mã số hiệu | Số hiệu chứa dấu và khoảng trắng, không sửa được sau khi đã ban hành | Thêm cột `issue_code` riêng, chỉ chữ và số |
| 2 | Cấp số bằng cách lấy số lớn nhất cộng một | Hai văn bản trùng số | Khóa dòng bộ đếm, ràng buộc duy nhất, cùng một giao dịch |
| 3 | Cho phép chọn phòng ban mà không kèm pháp nhân | Văn bản của một công ty lan sang cả 13 công ty | `CHECK` ở tầng dữ liệu |
| 4 | Gắn xác nhận đã đọc vào văn bản thay vì vào phiên bản | Người đã xác nhận bản 1.0 hiện là đã đọc bản 2.0 mà chưa từng đọc | `UNIQUE(version_id, employee_id)` |
| 5 | Phiên bản chạy theo bản luồng đang sống | Sửa luồng làm phiếu đang chạy nhảy bước | Chép định nghĩa luồng vào `flow_snapshot` lúc khởi tạo |
| 6 | Quên khai bảng mới trong `SCOPE_FIELDS` | **Không lọc dữ liệu gì cả** — ai cũng thấy mọi thứ | Bổ sung kiểm tra khi khởi động: bảng nào có `company_id` mà chưa khai phạm vi thì báo lỗi ngay lúc chạy |
| 7 | Nhầm `status` của văn bản với `status` của phiên bản | Quy chế lên bản 2.0 xong thì biến mất khỏi danh sách văn bản đang hiệu lực | Lên phiên bản **không đụng tới** `tab_document.status`. Xem [`05` mục 6.4](./05-vong-doi-phien-ban.md) |
| 8 | Chỉ kiểm "một bản nháp mỗi văn bản" trong mã nguồn | Hai người bấm cùng lúc, hai bản nháp 2.0 cùng tồn tại, một bản mất công vô ích | Cột sinh `open_slot` kèm ràng buộc duy nhất, mục 5.3 |
| 9 | Thu hồi chia sẻ bằng cách **xóa dòng** ACL | Mất luôn thông tin ai từng được xem — đúng thứ cần nhất khi điều tra rò rỉ | `revoked_at` chứ không `DELETE`. Cũng đừng quên `perm_cache_clear`, không thì tới 60 giây sau mới có hiệu lực |
| 10 | Cho phép chia sẻ đặc cách mà không bắt hạn | Đặc cách vô thời hạn bằng nâng mức mật, nhưng không ai rà lại được vì nó nằm rải trên từng văn bản | `CHECK` bắt `valid_to` và `override_approved_by` khác rỗng, mục 8.2 |
| 11 | Dùng quan hệ *thuộc về* cho bản trích thay vì *trích từ* | Mất cả ba ràng buộc: gốc lên phiên bản mà bản trích không bị đánh dấu, gốc bãi bỏ mà bản trích còn hiệu lực, mức mật bản trích vượt gốc. Nội dung mật cũ tiếp tục lưu hành dưới danh nghĩa văn bản còn hiệu lực | Quan hệ riêng số 10, ba cột cấu hình khóa cứng, bắt buộc có `source_version_id`. Mục 4.2 và 5.5 |
| 12 | **Quên lọc `origin = 1`** ở một màn hình nào đó | Nghị định của Chính phủ và công văn nhận từ bên ngoài hiện lẫn trong danh sách "văn bản của tôi", đếm sai mọi báo cáo, và người dùng bấm vào thì gặp trang chi tiết trống trơn vì bản ghi đó không có phiên bản | Bộ lọc nằm ở **hàm dựng truy vấn dùng chung**, không để từng màn hình tự thêm. Kèm một bài kiểm tự động: tạo một bản ghi `origin = 2`, gọi hết các trang danh sách và tìm kiếm, không trang nào được trả về nó. Đây là cái giá của việc gom bảng ở mục 1.1, và là chỗ duy nhất việc gom làm tăng rủi ro |

Hai điều đáng làm thành bài kiểm tự động là số 6 và số 12, vì cùng một kiểu lỗi im lặng: không ai báo lỗi, màn hình vẫn chạy, chỉ là hiện ra thứ đáng lẽ không được hiện.

---

## 14. Bảng tổng hợp

| Nhóm | Bảng mới, bản 1.0 | Bảng mới, bản 1.1 | Bảng sửa |
|---|---|---|---|
| 0 · Sửa bảng đang có | 0 | 0 | 4 |
| 1 · Danh mục và cấu hình | 6 | 6 | |
| 2 · Văn bản | 6 | **5** | |
| 3 · Bộ máy duyệt dùng chung | 6 | 6 | |
| 4 · Ban hành và phân phối | 3 | **2** | |
| 5 · Quyền truy cập | 5 | 5 | |
| 6 · Tạo sớm dùng sau | 3 | **1** | |
| **Tổng** | **29** | **25** | **4** |

Thiết kế hệ văn thư độc lập trước đây cần **42 bảng**. Xây trong Thu mua còn **25**, vì 12 bảng nền dùng lại được nguyên, 4 bảng nữa chỉ cần thêm cột, và 4 bảng đã gom ở bản 1.1. Phần tiết kiệm được đổi lại bằng hai thứ: phải sửa nền trên một hệ đang chạy thật (phase 0 trong [`02`](./02-lo-trinh-phat-trien.md)), và phải kỷ luật với bộ lọc `origin` (chỗ dễ sai số 12).

**Gom bảng không làm giảm khối lượng công việc.** Cột vẫn từng ấy cột, màn hình vẫn từng ấy màn hình. Cái được là bớt bốn chỗ dữ liệu có thể lệch nhau, và vá được hai lỗi thiết kế mà việc gom làm lộ ra. Đừng đọc con số 29 xuống 25 thành "nhẹ đi 14%".

---

Quay lại: [`00` Đánh giá và câu hỏi](./00-danh-gia-va-cau-hoi.md) · [`01` Danh sách tính năng](./01-danh-sach-tinh-nang.md) · [`02` Lộ trình](./02-lo-trinh-phat-trien.md) · [`03` Lark Approver](./03-lark-approver.md) · [`05` Vòng đời phiên bản](./05-vong-doi-phien-ban.md) · [Nhật ký thay đổi](./CHANGELOG.md)
