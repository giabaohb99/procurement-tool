# TỪ ĐIỂN DỮ LIỆU — VĂN THƯ · BỘ MÁY DUYỆT · DUYỆT DẤU
Bản 1.0 — 28/08/2026. Nguồn sự thật là model.py; tệp này chép Ý NGHĨA, không thay mã.

---

## Phần 1: Văn bản (document)

Cụm này gồm 11 bảng. Trục trung tâm là `tab_document` (một bản ghi văn bản) và `tab_document_version` (nội dung thật của từng phiên bản). Các bảng còn lại bổ sung chữ ký, nơi nhận, phạm vi áp dụng, quyền đặc cách, quan hệ liên tài liệu, kế hoạch clone, mẫu soạn thảo, và sổ văn bản đến.

---

### `tab_document` — Văn bản

Bảng xương sống của phân hệ Văn thư. Mỗi dòng là một tài liệu; nội dung không nằm ở đây mà ở `tab_document_version`. Ba loại bản ghi dùng chung bảng, phân biệt qua `origin`: văn bản nội bộ (1), văn bản pháp luật ngoài (2), và văn bản đến (3). Mọi truy vấn danh sách phải lọc `origin = 1`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `origin` | int | Nguồn gốc: 1 nội bộ · 2 văn bản pháp luật ngoài · 3 văn bản đến |
| `doc_code` | str(50) | Mã tài liệu bất biến (ví dụ `DEGO-QC-012`), dùng với `id_scheme = 1`, UNIQUE |
| `issue_number` | str(100) | Số hiệu theo sổ (ví dụ `08/2026/TB-NS-DEGO`), dùng với `id_scheme = 2` |
| `seq_no` | int | Số thứ tự thô trong sổ, dùng cho UNIQUE và lọc |
| `issue_year` | int | Năm cấp số, dùng cho UNIQUE và lọc |
| `numbering_rule_id` | int | FK → `tab_document_numbering_rule.id`; 0 là cách cấp số mặc định cũ |
| `legacy_code` | str(100) | Số hiệu bản giấy trước khi lên hệ thống, phục vụ tra cứu |
| `storage_location` | str(200) | Địa chỉ lưu trữ bản giấy có chữ ký tươi, ô tự do |
| `doc_type_id` | int | FK → `tab_doc_type.id` — loại văn bản |
| `company_id` | int | FK → pháp nhân BAN HÀNH (không phải pháp nhân của người nhập) |
| `department_id` | int | FK → phòng chủ trì |
| `owner_employee_id` | int | FK → nhân sự chịu trách nhiệm nội dung (khác người soạn) |
| `drafter_employee_id` | int | FK → người soạn thảo |
| `signer_employee_id` | int | FK → người ký ban hành |
| `title` | str(500) | Trích yếu/tên văn bản |
| `summary` | text | Tóm tắt nội dung |
| `keywords` | str(500) | Từ khóa tra cứu, ngăn bằng dấu phẩy |
| `secrecy_level` | int | Mức mật: 1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật |
| `urgency` | int | Độ khẩn: 1 Thường · 2 Khẩn · 3 Hỏa tốc |
| `status` | int | Trạng thái vòng đời (xem bảng enum bên dưới) |
| `effective_date` | date | Ngày hiệu lực của phiên bản hiện hành, chép từ `current_version_id` để lọc nhanh |
| `expire_date` | date | Ngày văn bản hết hiệu lực |
| `issued_at` | datetime | Thời điểm ký ban hành (dùng sắp xếp sổ văn bản đi) |
| `next_review_date` | date | Hạn rà soát định kỳ |
| `attachment_view_until` | date | Hạn xem tệp đính kèm; quá ngày không mở/tải được, không liên quan `expire_date` |
| `needs_review` | bool | Cờ "cần rà lại" do văn bản cha thay đổi |
| `needs_review_note` | str(300) | Lý do cần rà lại, hiện thẳng trên băng cảnh báo |
| `current_version_id` | int | FK → `tab_document_version.id` — phiên bản đang có hiệu lực |
| `document_request_id` | int | FK → `tab_document_request.id`; LUÔN NULL ở bản 1 (bước xin phép đã cắt) |
| `source_document_id` | int | FK → `tab_document.id` — văn bản gốc nếu đây là bản clone |
| `clone_status` | int | 0 chưa đụng · 1 đã sinh nháp · 2 đã ban hành · 3 lệch bản so với gốc |
| `clone_source_version_id` | int | FK → phiên bản gốc mà bản clone đang bám theo |
| `apply_mode` | int | Cơ chế áp dụng cho pháp nhân con: 1 phạm vi · 2 clone riêng |
| `issue_mailbox_id` | int | FK → hộp thư đã dùng gửi thông báo ban hành |
| `cloned_at` | date | Ngày sinh bản clone |
| `cloned_by` | int | FK → tài khoản đã thực hiện clone |
| `clone_note` | str(500) | Ghi chú về lần clone |
| `clone_assignee_employee_id` | int | FK → nhân sự chịu trách nhiệm bản clone |
| `clone_due_date` | date | Hạn xử lý bản clone |
| `clone_handled_at` | datetime | Thời điểm bản clone được xử lý xong |
| `legal_issuer` | str(300) | Cơ quan ban hành (chỉ dùng với `origin = 2`) |
| `legal_url` | str(1000) | Đường dẫn văn bản pháp luật ngoài |
| `recipient_summary` | str(500) | Nơi nhận tóm tắt trên sổ văn bản đi |
| `copies` | int | Số bản phát hành |
| `register_note` | str(500) | Ghi chú trong sổ văn bản đi |
| `book_id` | int | FK → `tab_document_book.id`; luôn rỗng ở bản 1 |
| `book_seq_no` | int | Số thứ tự trong sổ; luôn rỗng ở bản 1 |
| `book_year` | int | Năm sổ; luôn rỗng ở bản 1 |
| `meta` | json | Dữ liệu riêng của từng loại văn bản (tên cột DB là `metadata`), hình dạng do `type_metadata.py` quy định |
| `is_active` | bool | Cờ xóa mềm |

**Trạng thái `status`:**

| Giá trị | Hằng số | Nhãn |
|---|---|---|
| 1 | `STATUS_DRAFT` | Nháp |
| 2 | `STATUS_SUBMITTED` | Đang duyệt |
| 3 | `STATUS_APPROVED` | Đã duyệt (đã ban hành, chờ tới ngày hiệu lực) |
| 4 | `STATUS_EFFECTIVE` | Có hiệu lực |
| 5 | `STATUS_REPLACED` | Đã thay thế |
| 6 | `STATUS_EXPIRED` | Hết hiệu lực |
| 7 | `STATUS_REVOKED` | Bãi bỏ |
| 8 | `STATUS_ARCHIVED` | Lưu trữ |
| 9 | `STATUS_RETURNED` | Trả về — sửa và gửi duyệt lại được |
| 10 | `STATUS_REJECTED` | Đã từ chối — KHÓA, phải sao chép để làm lại |
| 11 | `STATUS_PENDING_ISSUE` | Chờ ban hành — đã ký đủ, đang đợi người soạn bấm Ban hành |

**Logic chính:**

- `origin = 1` là văn bản nội bộ; mọi danh sách và thống kê chỉ lấy loại này qua hàm `query.documents_query()`.
- `status` của văn bản khác `status` của phiên bản: lên bản 2.0 thì `tab_document.status` vẫn là 4 (có hiệu lực), chỉ dòng phiên bản 1.0 chuyển sang trạng thái bị thay thế.
- Số hiệu cấp một lần, không thu hồi khi hủy văn bản.
- `STATUS_RETURNED` và `STATUS_REJECTED` được tách từ `STATUS_DRAFT` ngày 24/08/2026 để màn danh sách phân biệt được "bị trả — còn sửa" với "bị từ chối — đường đã chốt".
- `STATUS_PENDING_ISSUE` (11) chỉ áp dụng khi loại văn bản khai `auto_issue_after_approval = False`; khác `STATUS_APPROVED` vì văn bản chưa được cấp số, chưa khóa phiên bản.
- `apply_mode = 1` (phạm vi) là mặc định; `apply_mode = 2` (clone) cần bấm nút riêng sau khi ban hành.

---

### `tab_document_version` — Phiên bản văn bản

Nơi chứa nội dung thật của văn bản. Một văn bản có nhiều phiên bản, `tab_document.current_version_id` trỏ tới bản đang dùng. Sửa văn bản đã ban hành phải mở dòng mới, không sửa dòng cũ.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `document_id` | int | FK → `tab_document.id` |
| `major` | int | Số phiên bản lớn (ví dụ: 2 trong "2.0") |
| `minor` | int | Số phiên bản nhỏ (ví dụ: 0 trong "2.0") |
| `status` | int | Trạng thái phiên bản (xem bảng enum bên dưới) |
| `is_locked` | bool | Phiên bản bất biến sau khi duyệt; một chiều — bật rồi không tắt được |
| `open_slot` | int | Cột SINH: bằng `document_id` khi còn mở (status IN 1,2,5), NULL khi chốt; UNIQUE đảm bảo mỗi văn bản nhiều nhất một bản đang mở |
| `content_html` | MEDIUMTEXT | Thân văn bản do trình soạn thảo tiptap sinh, tối đa ~16MB |
| `content_sha256` | str(64) | Dấu vân tay nội dung, tính lúc khóa — dùng đối chiếu bản in |
| `margin_left_mm` | int | Lề trái tính bằng mm (mặc định 30) |
| `margin_right_mm` | int | Lề phải tính bằng mm (mặc định 20) |
| `header_left` | str(200) | Đầu trang trái, nhận thẻ `{{so_hieu}}` v.v. |
| `header_right` | str(200) | Đầu trang phải |
| `footer_left` | str(200) | Chân trang trái |
| `footer_right` | str(200) | Chân trang phải |
| `auto_heading_number` | bool | Đánh số mục tự động (I · 1 · a) cho phiên bản này |
| `change_kind` | int | 0 phiên bản đầu · 1 sửa lớn (lên x.0) · 2 sửa nhỏ (lên x.1) |
| `change_summary` | str(500) | Tóm tắt nội dung thay đổi, bắt buộc từ phiên bản thứ hai |
| `change_reason` | text | Lý do thay đổi |
| `requires_reconfirm` | bool | Sửa lớn: người đã đọc bản cũ phải xác nhận đọc lại |
| `effective_from` | date | Ngày hiệu lực riêng của phiên bản |
| `prev_version_id` | int | FK → `tab_document_version.id` — phiên bản liền trước |
| `created_from_request_id` | int | FK → `tab_document_request.id`; LUÔN NULL ở bản 1 |
| `file_id` | int | FK → tệp bản gốc đính kèm |
| `pdf_file_id` | int | FK → tệp PDF đã ký |
| `approved_at` | datetime | Thời điểm duyệt |
| `approved_by` | int | FK → tài khoản đã duyệt |

**Trạng thái `status`:**

| Giá trị | Hằng số | Nhãn |
|---|---|---|
| 1 | `VERSION_DRAFT` | Nháp — đang gõ, sửa được |
| 2 | `VERSION_SUBMITTED` | Đang duyệt — đóng băng, rút phiếu thì về nháp |
| 3 | `VERSION_APPROVED` | Đã duyệt — KHÓA, bất biến |
| 4 | `VERSION_SUPERSEDED` | Đã bị phiên bản sau thay thế |
| 5 | `VERSION_RETURNED` | Trả về — sửa được, gửi duyệt lại, vẫn giữ `open_slot` |
| 6 | `VERSION_REJECTED` | Đã từ chối — KHÓA, nhả `open_slot` để có thể mở bản mới |

**Logic chính:**

- `open_slot` là cột SINH (computed), đảm bảo mỗi văn bản nhiều nhất một phiên bản đang mở — chặn race condition khi hai người bấm cùng lúc.
- `is_locked` bật một chiều khi duyệt; muốn sửa phải mở phiên bản mới.
- `major.minor` lưu riêng hai số nguyên chứ không phải chuỗi "2.0" để sắp xếp đúng.
- Lề trang lưu theo phiên bản, không theo văn bản: sửa lề ở bản 2.0 không được đổi hình dạng bản 1.0 đã ký.
- `VERSION_REJECTED` cố ý không nằm trong `OPEN_STATUSES` để nhả `open_slot` cho phiên bản mới.

---

### `tab_signature` — Chữ ký trên văn bản

Ghi nhận mỗi lần ký vào một phiên bản cụ thể. Bảng chỉ ghi thêm, không sửa, không xóa. Ba loại chữ ký có giá trị pháp lý khác hẳn nhau.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `document_id` | int | FK → `tab_document.id` |
| `version_id` | int | FK → `tab_document_version.id` — ký vào phiên bản nào |
| `signer_employee_id` | int | FK → nhân sự đã ký |
| `sign_kind` | int | Loại chữ ký: 1 nội bộ · 2 có chứng thư số · 3 bản giấy đã quét |
| `signed_at` | datetime | Thời điểm ký |
| `content_sha256` | str(64) | Dấu vân tay nội dung lúc ký — để đối chiếu "ký cho bản nào" |
| `cert_serial` | str(100) | Số serial chứng thư (chỉ dùng với `sign_kind = 2`) |
| `cert_issuer` | str(200) | Nhà cung cấp chứng thư (chỉ dùng với `sign_kind = 2`) |
| `signature_blob` | binary | Dữ liệu chữ ký số (chỉ dùng với `sign_kind = 2`) |
| `ip` | str(45) | Địa chỉ IP lúc ký |
| `user_agent` | str(300) | Trình duyệt/ứng dụng lúc ký |

**Trạng thái `sign_kind`:**

| Giá trị | Nhãn | Giá trị pháp lý |
|---|---|---|
| 1 | Ký điện tử nội bộ | Có giá trị trong nội bộ tập đoàn, KHÔNG có giá trị với bên ngoài |
| 2 | Ký số có chứng thư | Có giá trị pháp lý với bên ngoài, dựa trên chứng thư số |
| 3 | Ký giấy đã quét | Bản ghi nhận chữ ký trên giấy, giá trị theo bản giấy gốc |

**Logic chính:**

- Chữ ký gắn với phiên bản, không với văn bản: văn bản lên bản 2.0 thì chữ ký của bản 1.0 vẫn nằm đúng chỗ.
- `content_sha256` chép từ `tab_document_version.content_sha256` lúc ký; nội dung đổi thì mã băm đổi, lộ ra là chữ ký cũ đang ký cho bản khác.
- `sign_kind = 2` (chứng thư số) thuộc dịch vụ J08 chưa làm; dòng loại 2 ở bảng này chỉ là ghi nhận.
- Bảng chỉ ghi thêm — không có đường xóa hay sửa.

---

### `tab_document_recipient` — Nơi nhận và xác nhận đã đọc

Ghi nhận ai được gửi văn bản và ai đã xác nhận đọc, gắn vào phiên bản cụ thể. Bảng khai sẵn ở bản 1, chưa có màn hình. Một người nhận = một dòng, dù gửi nhiều kênh.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `document_id` | int | FK → `tab_document.id` |
| `version_id` | int | FK → `tab_document_version.id` |
| `recipient_kind` | int | Loại người nhận: 1 nhân sự · 2 phòng ban · 3 pháp nhân · 4 bên ngoài |
| `recipient_id` | int | Id nhân sự/phòng/pháp nhân tùy `recipient_kind`; 0 khi gửi bên ngoài |
| `external_party_id` | int | FK → `tab_external_party.id`, dùng khi `recipient_kind = 4` |
| `channels` | int | Tập hợp kênh gửi (bitmask): 1 chuông · 2 email · 4 giấy · 8 bên ngoài |
| `send_status` | int | 1 chờ gửi · 2 đã gửi · 3 lỗi |
| `sent_at` | datetime | Thời điểm gửi thành công |
| `error` | str(500) | Thông báo lỗi nếu `send_status = 3` |
| `required` | bool | Bắt buộc bấm xác nhận, hay chỉ nhận thông báo |
| `due_date` | date | Hạn xác nhận |
| `read_at` | datetime | Lần mở đầu tiên — khác lúc bấm nút xác nhận |
| `confirmed_at` | datetime | Thời điểm bấm xác nhận đã đọc |
| `ip` | str(45) | Địa chỉ IP lúc xác nhận |

**Logic chính:**

- Gắn vào phiên bản, không vào văn bản: lên bản 2.0 thì người đã xác nhận bản 1.0 chưa được coi là đã đọc bản mới.
- `channels` là bitmask cộng dồn, không phải mỗi kênh một dòng, để tránh đếm trùng người nhận.
- `read_at` (lần mở) và `confirmed_at` (xác nhận) là hai sự thật khác nhau, lưu riêng.
- Quan hệ với `tab_email_log`: bảng này ghi "định gửi cho ai và đã đọc chưa"; `tab_email_log` ghi chi tiết từng lần gửi thư.

---

### `tab_document_scope` — Phạm vi áp dụng

Khai ai thuộc phạm vi của văn bản (bao gồm hoặc loại trừ). Ba chiều: pháp nhân, phòng ban, cá nhân. Không có chiều chức danh.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `document_id` | int | FK → `tab_document.id` |
| `dim` | int | Chiều: 1 pháp nhân · 2 phòng ban · 3 cá nhân |
| `company_id` | int | FK → pháp nhân; bắt buộc khi `dim = 2` |
| `department_id` | int | FK → phòng ban; dùng khi `dim = 2` |
| `employee_id` | int | FK → nhân sự; dùng khi `dim = 3` |
| `include_children` | bool | Khi áp cho Tập đoàn: tự động áp cho mọi công ty con hiện tại và tương lai |
| `mode` | int | 1 bao gồm · 2 loại trừ |

**Logic chính:**

- Bốn quy tắc: dòng bao gồm cộng dồn; chiều cụ thể hơn thắng (cá nhân > phòng > pháp nhân); cùng chiều thì loại trừ thắng bao gồm; không có dòng nào = chỉ pháp nhân ban hành.
- Phòng ban (`dim = 2`) bắt buộc kèm `company_id` ở tầng dữ liệu để tránh một phòng lan sang 13 pháp nhân.
- `include_children = True` tính lúc đọc, không bung sẵn thành nhiều dòng, để công ty con mở mới cũng được áp.

---

### `tab_document_access` — Quyền đặc cách trên từng văn bản

Lớp thứ ba của phân quyền, bổ sung hoặc thu hẹp quyền trên đúng một văn bản cụ thể. Đứng cạnh lớp vai trò (`require`) và lớp phạm vi (`apply_scope`), không thay thế lớp nào.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `document_id` | int | FK → `tab_document.id` |
| `subject_kind` | int | Loại đối tượng: 1 người · 2 phòng ban · 3 pháp nhân · 4 vai trò |
| `subject_id` | int | Id nhân sự/phòng/pháp nhân/vai trò tùy `subject_kind` |
| `effect` | int | 1 cho phép · 2 không cho phép (CẤM thắng mọi dòng cho phép) |
| `can_read` | bool | Quyền đọc |
| `can_write` | bool | Quyền sửa |
| `can_delete` | bool | Quyền xóa |
| `valid_from` | date | Ngày bắt đầu hiệu lực; rỗng = ngay lập tức |
| `valid_to` | date | Ngày hết hiệu lực; rỗng = không hạn |
| `reason` | str(500) | Lý do chia quyền, bắt buộc nhập khi chia đặc cách |
| `revoked_at` | datetime | Thời điểm thu hồi; ghi dấu mốc, KHÔNG xóa dòng |
| `revoked_by` | int | FK → tài khoản đã thu hồi |
| `revoke_reason` | str(500) | Lý do thu hồi |

**Logic chính:**

- `effect = 2` (cấm) ăn đứt mọi dòng cho phép và ăn đứt phạm vi vai trò.
- Thu hồi là đánh dấu `revoked_at`, không xóa dòng, để sau này tra được "hồi tháng 7 ai đọc được".
- `valid_to` tự hết hạn, không cần ai nhớ thu hồi.
- Không có UNIQUE cho "(văn bản × đối tượng × chiều tác động)"; chống trùng ở tầng service.

---

### `tab_document_link` — Quan hệ giữa các văn bản

Một dòng = một câu "văn bản A có quan hệ loại X với văn bản B". Mười loại quan hệ định nghĩa ở `doc_catalog/link_rule_model.py`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `source_document_id` | int | FK → `tab_document.id` — văn bản nguồn |
| `target_document_id` | int | FK → `tab_document.id` — văn bản đích |
| `relation` | int | Loại quan hệ (xem bảng enum tại `tab_doc_type_link_rule`) |
| `rule_id` | int | FK → `tab_doc_type_link_rule.id`; rỗng với quan hệ khai tay |
| `source_version_id` | int | FK → phiên bản gốc, CHỈ dùng cho quan hệ "trích từ" (relation = 10) |
| `note` | str(500) | Ghi chú |
| `is_system` | bool | Hệ thống tự tạo — không thể xóa qua bất kỳ UI hay API nào |

**Logic chính:**

- Hai dòng `is_system = True` không xóa được: quan hệ "căn cứ theo" của bản clone về bản gốc, và quan hệ "trích từ".
- Quan hệ "trích từ" bắt buộc có `source_version_id` để phát hiện khi bản trích đã lạc hậu so với gốc.
- Cây tài liệu tra cả hai chiều nhờ hai chỉ mục trên `source_document_id` và `target_document_id`.

---

### `tab_document_clone_plan` — Kế hoạch clone

Khai lúc tạo văn bản, chạy lúc ban hành. Ghi dự định clone xuống pháp nhân nào, giúp tránh việc ban hành xong không ai bấm clone. Dòng bị xóa ngay khi bản clone tương ứng được tạo.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `document_id` | int | FK → `tab_document.id` |
| `company_id` | int | FK → pháp nhân sẽ nhận bản clone |
| `due_date` | date | Hạn xử lý bản clone |
| `note` | str(500) | Ghi chú |

**Logic chính:**

- Một pháp nhân chỉ đứng một lần trong kế hoạch của một văn bản (UNIQUE).
- Dòng kế hoạch bị tiêu thụ (`consume_plan`) ngay khi bản clone được tạo, để không nhầm lẫn "dự kiến" và "đã có".
- Clone chỉ được chạy sau khi văn bản đã ban hành — bản nháp chưa có `current_version_id` để chép nội dung.

---

### `tab_document_template` — Văn bản mẫu

Nội dung khởi tạo cho một loại văn bản. Mẫu được chép vào phiên bản 1.0 khi tạo văn bản, không giữ liên kết sống — sửa mẫu sau không ảnh hưởng văn bản đã tạo.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `doc_type_id` | int | FK → `tab_doc_type.id` |
| `name` | str(200) | Tên mẫu; UNIQUE trong cùng loại văn bản |
| `description` | text | Mô tả mục đích của mẫu |
| `content_html` | MEDIUMTEXT | Nội dung HTML của mẫu, cùng kiểu với `DocumentVersion.content_html` |
| `is_active` | bool | Cờ ẩn/hiện mẫu |

**Logic chính:**

- Trong cùng một loại văn bản, hai mẫu không được trùng tên (UNIQUE).
- Khác loại vẫn được phép trùng tên.
- Mẫu là điểm bắt đầu, không phải ràng buộc sống — người soạn sửa tự do sau khi chép.

---

### `tab_document_request` — Yêu cầu soạn văn bản

Bảng khai sẵn nhưng RỖNG ở bản 1. Bước xin phép đã cắt theo quyết định 7 (14/08/2026); không có service, không có router, không có màn hình nào ghi vào đây.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `kind` | int | 1 soạn mới · 2 xin sửa · 3 xin bãi bỏ |
| `target_document_id` | int | FK → văn bản muốn sửa/bãi bỏ; rỗng khi xin soạn mới |
| `doc_type_id` | int | FK → loại văn bản dự kiến |
| `company_id` | int | FK → pháp nhân ban hành dự kiến |
| `department_id` | int | FK → phòng chủ trì |
| `requester_employee_id` | int | FK → nhân sự đề nghị |
| `title` | str(500) | Tiêu đề dự kiến |
| `reason` | text | Lý do đề nghị, bắt buộc |
| `expected_date` | date | Hạn mong muốn có văn bản |
| `status` | int | 1 nháp · 2 đang duyệt · 3 đã duyệt · 4 từ chối · 5 đã soạn xong |
| `approved_by` | int | FK → tài khoản đã duyệt |
| `approved_at` | date | Ngày duyệt |
| `reject_reason` | text | Lý do từ chối |

**Logic chính:**

- `tab_document.document_request_id` và `tab_document_version.created_from_request_id` luôn NULL ở bản 1.
- `doc_type.needs_request` luôn FALSE và bị ẩn khỏi form loại văn bản.
- Bảng tạo sẵn để sau này bật lại không phải ALTER bảng đang chạy.

---

### `tab_incoming_register` — Sổ văn bản đến

Bảng khai sẵn nhưng RỖNG ở bản 1; màn hình thuộc phase 9. Văn bản đến có vòng đời khác hẳn (không phiên bản, không duyệt), nên tách thành bảng riêng thay vì dùng `origin = 3` trong `tab_document`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `company_id` | int | FK → pháp nhân nhận văn bản |
| `year` | int | Năm nhận |
| `seq_no` | int | Số thứ tự trong sổ, cấp qua `number_service.next_number()` |
| `received_date` | date | Ngày nhận |
| `sender_party_id` | int | FK → `tab_external_party.id` — bên gửi |
| `sender_doc_number` | str(100) | Số hiệu trên bản giấy của bên gửi |
| `sender_doc_date` | date | Ngày ký trên bản giấy của bên gửi |
| `title` | str(500) | Tóm tắt nội dung |
| `file_id` | int | FK → tệp scan bản gốc |
| `assigned_employee_id` | int | FK → nhân sự được giao xử lý |
| `due_date` | date | Hạn xử lý |
| `handled_at` | datetime | Thời điểm xử lý xong |
| `status` | int | Trạng thái xử lý (xem bên dưới) |
| `note` | text | Ghi chú |

**Trạng thái `status`:**

| Giá trị | Nhãn |
|---|---|
| 1 | Mới nhận |
| 2 | Đã giao |
| 3 | Đã xử lý |
| 4 | Đóng |

**Logic chính:**

- Bộ ba (pháp nhân × năm × số thứ tự) là UNIQUE vì sổ đến chỉ có một cho cả pháp nhân.
- Sổ văn bản đi là một TRUY VẤN trên `tab_document`, không phải bảng riêng.
- `seq_no` chỉ cấp qua `next_number()` với khóa `in:{mã pháp nhân}:{năm}`, cấm dùng `MAX() + 1`.
- `hằng số ORIGIN_INCOMING = 3` vẫn giữ ở `document/model.py` để văn bản đến có thể là đích của quan hệ "căn cứ theo".

---

## Phần 2: Danh mục văn thư (doc_catalog)

Cụm này gồm 10 bảng. Danh mục dùng chung cho mọi pháp nhân, cố ý không có `company_id`, trừ `tab_document_book` (mỗi pháp nhân có sổ riêng).

---

### `tab_doc_type` — Loại văn bản

Bảng gốc của cả phân hệ; dự kiến 32 dòng. Mỗi văn bản khi tạo chọn một loại ở đây; loại quyết định kiểu định danh, mức mật mặc định, thời điểm cấp số, và các ràng buộc quy trình.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `code` | str(10) | Mã loại, UNIQUE, đóng vai tiền tố số hiệu |
| `name` | str(200) | Tên loại văn bản |
| `group_code` | str(1) | Nhóm A–F theo danh mục 32 loại |
| `description` | text | Mô tả |
| `id_scheme` | int | 1 mã tài liệu bất biến (DEGO-QC-012) · 2 số hiệu theo sổ (đếm lại từ 1 mỗi năm) |
| `number_when` | int | 1 cấp số lúc tạo nháp · 2 cấp số lúc được duyệt (mặc định) |
| `default_secrecy` | int | Mức mật mặc định khi tạo văn bản: 1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật |
| `is_confidential_type` | bool | Toàn bộ loại mặc định mức mật cao; CHỈ đặt mức mặc định, không gác quyền đọc |
| `is_personal` | bool | Văn bản cá nhân (đơn nghỉ phép, phiếu lương…) — không đi theo phạm vi vai trò |
| `auto_issue_after_approval` | bool | Duyệt xong tự ban hành (True mặc định) hay dừng ở «Chờ ban hành» để người soạn bấm |
| `needs_approval` | bool | Loại này có phải duyệt không |
| `needs_signature` | bool | Loại này có phải ký không |
| `needs_decision` | bool | Ban hành phải kèm Quyết định riêng (kiểm theo phiên bản) |
| `needs_request` | bool | Phải có yêu cầu được duyệt mới soạn; LUÔN FALSE ở bản 1 |
| `review_cycle_months` | int | Chu kỳ rà soát định kỳ (tháng); 0 = không rà |
| `retention_months` | int | Thời hạn lưu trữ (tháng) |
| `default_flow_id` | int | FK → `tab_approval_flow.id` — luồng duyệt mặc định |
| `sort_order` | int | Thứ tự hiển thị trong danh mục |
| `is_active` | bool | Cờ ẩn/hiện |

**Logic chính:**

- `code` đồng thời là tiền tố số hiệu, không có cột `prefix` riêng.
- `is_personal = True` bật kiểm truy cập riêng: chỉ người trong tờ đơn mới thấy, bất kể phạm vi vai trò.
- `auto_issue_after_approval = False` tạo trạng thái `STATUS_PENDING_ISSUE` (11) — loại nào cần thì bật riêng, không bật đại trà.
- Mẫu soạn thảo khai ở `tab_document_template`, không đặt `template_id` trên bảng này.

---

### `tab_external_party` — Đơn vị gửi nhận bên ngoài

Danh mục đối tác bên ngoài, dùng làm nơi gửi của văn bản đến và nơi nhận của văn bản đi. Tách khỏi `tab_supplier` của Thu mua vì mục đích khác nhau.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `code` | str(30) | Mã đơn vị, UNIQUE |
| `name` | str(300) | Tên đầy đủ |
| `kind` | int | 1 cơ quan nhà nước · 2 đối tác · 3 khách hàng · 4 đơn vị nội bộ · 5 khác |
| `contact_person` | str(200) | Người liên hệ |
| `phone` | str(50) | Số điện thoại |
| `email` | str(150) | Email liên hệ |
| `address` | text | Địa chỉ |
| `is_active` | bool | Cờ ẩn/hiện |

**Logic chính:**

- Dùng làm `sender_party_id` trong `tab_incoming_register` và `external_party_id` trong `tab_document_recipient`.
- Cố ý tách khỏi `tab_supplier`: bên đó là pháp nhân mua bán (mã số thuế, VAT, hợp đồng), bên này phần lớn là cơ quan nhà nước.

---

### `tab_document_book` — Sổ văn bản

Mỗi sổ là một bản ghi; có bộ đếm số riêng. Sổ văn bản đến, văn bản đi, hoặc văn bản nội bộ.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `code` | str(30) | Mã sổ, UNIQUE; đi vào khóa bộ đếm `book:{code}:{năm}`, KHÔNG đổi sau khi cấp số |
| `name` | str(200) | Tên sổ |
| `kind` | int | 1 văn bản đến · 2 văn bản đi · 3 văn bản nội bộ |
| `description` | text | Mô tả |
| `company_id` | int | FK → pháp nhân sở hữu sổ |
| `number_prefix` | str(20) | Tiền tố in trước số thứ tự (ví dụ `CVĐ` → `CVĐ 08/2026`) |
| `reset_yearly` | bool | Đầu năm mới đếm lại từ 1 (mặc định bật) |
| `start_no` | int | Số đầu tiên, dùng khi chuyển từ sổ giấy dở |
| `is_active` | bool | Cờ ẩn/hiện |

**Logic chính:**

- `code` KHÔNG được đổi sau khi đã cấp số — đổi là mất dấu toàn bộ số đã cấp.
- Không có `department_id`: quyền xem sổ cấp cho người đích danh qua `tab_document_book_member`, không cấp theo phòng.

---

### `tab_document_book_member` — Thành viên sổ văn bản

Khai ai quản lý và ai được xem một quyển sổ.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `book_id` | int | FK → `tab_document_book.id` |
| `employee_id` | int | FK → `tab_employee.id` — id NHÂN SỰ, không phải id tài khoản |
| `role` | int | 1 người quản lý (xem, sửa, xóa sổ, cấp số) · 2 người xem |

**Logic chính:**

- UNIQUE trên `(book_id, employee_id, role)`.
- Chỉ mục trên `(employee_id, role)` để trả lời câu "người này quản lý/xem những sổ nào".

---

### `tab_number_sequence` — Bộ đếm cấp số

Bảng nhỏ nhất nhưng quan trọng nhất: mỗi dòng là bộ đếm cho một (sổ × năm). Là nguồn sự thật duy nhất về số đã cấp.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `scope_key` | str(150) | Khóa duy nhất: `book:{mã sổ}:{năm}` · `doc:{pháp nhân}:{loại}` · `out:{pháp nhân}:{năm}:{loại}` |
| `year` | int | Năm |
| `current_no` | int | Số đã cấp gần nhất; số kế = giá trị này + 1 |

**Logic chính:**

- Cách cấp số DUY NHẤT được phép: `number_service.next_number()` — khóa dòng bằng `SELECT ... FOR UPDATE` trong cùng transaction với việc ghi bản ghi.
- Cấm: lấy `MAX(số) + 1`; đếm bằng Redis hay bất kỳ thứ gì ngoài cơ sở dữ liệu; cấp số ở transaction riêng rồi mới ghi bản ghi.

---

### `tab_document_numbering_rule` — Quy tắc đánh số văn bản

Định nghĩa mẫu số hiệu và điều kiện áp dụng. Mỗi quy tắc có bộ đếm riêng theo pháp nhân.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `direction` | int | 1 văn bản đến · 2 văn bản đi · 3 văn bản nội bộ |
| `pattern` | str(200) | Mẫu số hiệu dùng token `{STT}`, `{Nam}`, `{LoaiVB}` v.v. |
| `start_no` | int | Số khởi đầu |
| `reset_yearly` | bool | Đầu năm đếm lại |
| `allow_manual` | bool | Cho phép nhập số tay |
| `doc_type_mode` | int | 1 tất cả loại · 2 chỉ các loại được chọn ở bảng con |
| `book_mode` | int | 1 tất cả sổ · 2 các sổ được chọn · 3 văn bản không vào sổ |
| `priority` | int | Số nhỏ xét trước; quy tắc cụ thể hơn thắng khi cùng ưu tiên |
| `is_active` | bool | Cờ ẩn/hiện |

**Logic chính:**

- Bộ đếm thật vẫn nằm ở `tab_number_sequence`, khóa dòng lúc cấp số.
- Bảng con `tab_document_numbering_rule_doc_type` và `tab_document_numbering_rule_book` khai loại và sổ áp dụng khi `doc_type_mode = 2` hoặc `book_mode = 2`.

---

### `tab_document_numbering_rule_doc_type` — Loại văn bản theo quy tắc số

Bảng con: quy tắc số áp cho những loại văn bản nào (khi `doc_type_mode = 2`).

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `rule_id` | int | FK → `tab_document_numbering_rule.id` (CASCADE xóa) |
| `doc_type_id` | int | FK → `tab_doc_type.id` (CASCADE xóa) |

**Logic chính:**

- UNIQUE trên `(rule_id, doc_type_id)`.

---

### `tab_document_numbering_rule_book` — Sổ theo quy tắc số

Bảng con: quy tắc số áp cho những sổ nào (khi `book_mode = 2`).

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `rule_id` | int | FK → `tab_document_numbering_rule.id` (CASCADE xóa) |
| `book_id` | int | FK → `tab_document_book.id` (CASCADE xóa) |

**Logic chính:**

- UNIQUE trên `(rule_id, book_id)`.

---

### `tab_doc_type_link_rule` — Quy tắc quan hệ cha–con giữa các loại văn bản

Khai các loại quan hệ được phép giữa hai loại văn bản, điều kiện bắt buộc, và hành vi khi văn bản cha thay đổi. Khoảng 15–25 dòng cho toàn hệ.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `source_type_id` | int | FK → `tab_doc_type.id` — loại văn bản nguồn |
| `relation` | int | Loại quan hệ: 1 thay thế · 2 sửa đổi · 3 bổ sung · 4 hướng dẫn · 5 kèm theo · 6 thuộc về · 7 căn cứ theo · 8 tham chiếu · 9 bãi bỏ · 10 trích từ |
| `target_type_id` | int | FK → loại văn bản đích; NULL = cho phép mọi loại |
| `is_required` | bool | Thiếu quan hệ này thì không cho gửi duyệt |
| `min_count` | int | Số tối thiểu văn bản liên kết |
| `max_count` | int | Số tối đa; 0 = không giới hạn |
| `sort_order` | int | Thứ tự hiển thị trong form soạn thảo |
| `on_parent_obsolete` | int | Cha bị bãi bỏ → con: 1 không làm gì · 2 đánh dấu cần rà · 3 hết hiệu lực theo cha |
| `on_parent_new_version` | int | Cha lên bản mới → con: 1 không làm gì · 2 đánh dấu cần rà · 3 hỏi người ban hành |
| `inherit_code` | bool | Con lấy mã theo cha (`DEGO-QC-012-HD01`) |
| `inherit_secrecy` | bool | Con không được đặt mức mật thấp hơn cha |
| `is_active` | bool | Tắt thay vì xóa để `tab_document_link.rule_id` không trỏ vào khoảng không |

**Logic chính:**

- UNIQUE trên `(source_type_id, relation, target_type_id)`.
- Quan hệ "trích từ" (10) bị khóa cứng ba cột: `on_parent_new_version = 2`, `on_parent_obsolete = 3`, `inherit_secrecy = True`.
- `sort_order` chỉ quyết định thứ tự hiện trên giao diện, không bắt buộc ban hành lần lượt.

---

### `tab_security_level` — Mức mật và độ khẩn

Danh mục hai thang: mức mật (1–4) và độ khẩn (1–3). Dùng chung cho mọi pháp nhân. Trước 22/08/2026 khai cứng trong mã; nay tách ra bảng để quản trị tự sửa.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `kind` | int | 1 mức mật · 2 độ khẩn |
| `value` | int | Con số lưu xuống `tab_document.secrecy_level` hoặc `.urgency`; càng lớn càng nghiêm/gấp |
| `code` | str(30) | Mã ngắn, UNIQUE toàn bảng |
| `name` | str(100) | Tên hiển thị |
| `description` | text | Giải thích |
| `is_active` | bool | Cờ ẩn/hiện |

**Logic chính:**

- `value` vừa là số lưu trên văn bản, vừa là thứ bậc — dùng trực tiếp trong điều kiện luồng duyệt dạng `{"field":"secrecy_level","op":"gte","value":3}`. KHÔNG đánh số lại sau khi đã có luồng.
- Khóa nghiệp vụ là cặp `(kind, value)` — UNIQUE trên cặp này.
- Không có khóa ngoại từ `tab_document`; chống mồ côi bằng chốt chặn lúc xóa trong `security_level_guard.py`.

---

## Phần 3: Bộ máy duyệt (approval)

Cụm này gồm 7 bảng. Bộ máy không dành riêng cho văn bản — `entity` nhận mọi loại chứng từ. Bật/tắt theo từng loại chứng từ bằng `tab_approval_switch`. Khi tắt, chứng từ quay về đường duyệt cũ ngay lập tức không cần deploy.

---

### `tab_approval_flow` — Luồng duyệt

Định nghĩa một luồng cho một loại chứng từ. Nhiều luồng cùng loại thì chọn theo `priority` và `condition`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `entity` | str(50) | Loại chứng từ: `document`, `purchase_request`, `purchase_order`, … |
| `code` | str(50) | Mã luồng |
| `name` | str(200) | Tên luồng |
| `description` | str(500) | Mô tả |
| `version_no` | int | Phiên bản luồng, tăng mỗi lần sửa |
| `is_active` | bool | Cờ ẩn/hiện |
| `company_id` | int | FK → pháp nhân áp dụng; NULL = mọi pháp nhân |
| `priority` | int | Số lớn xét trước khi chọn luồng |
| `condition` | text | Điều kiện chọn luồng dạng JSON; rỗng = luồng mặc định |

**Logic chính:**

- UNIQUE trên `(entity, code, version_no)`.
- Phiếu đang chạy giữ bản chụp `flow_snapshot` ở `tab_approval_instance`, không tham chiếu bảng này; sửa luồng không làm hỏng phiếu đang chạy.
- Luồng không có `condition` là luồng mặc định — chọn sau cùng khi không khớp điều kiện nào.

---

### `tab_approval_node` — Bước trong luồng

Một bước duyệt trong luồng. Các bước cùng `seq` khác `branch_key` là các nhánh song song của một chặng; đúng một nhánh được chọn lúc chạy.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `flow_id` | int | FK → `tab_approval_flow.id` |
| `seq` | int | Thứ tự bước, đếm từ 1 |
| `branch_key` | str(50) | Định danh nhánh trong cùng `seq` |
| `name` | str(200) | Tên bước hiển thị cho người duyệt |
| `node_kind` | int | 1 bước duyệt (chặn luồng) · 2 nhận bản sao (không chặn) |
| `flow_role` | int | Vai trò: 1 đề xuất · 2 thực hiện · 3 kiểm tra · 4 phê duyệt |
| `approver_kind` | int | Cách chọn người duyệt (xem bảng enum bên dưới) |
| `approver_ref` | str(300) | Tham chiếu cho `approver_kind`; nhiều giá trị ngăn bằng dấu phẩy |
| `multi_mode` | int | Nhiều người: 1 một người đủ · 2 tất cả · 3 lần lượt · 4 đủ tỷ lệ |
| `quorum_percent` | int | Tỷ lệ phần trăm cần đạt khi `multi_mode = 4` |
| `condition` | text | Điều kiện rẽ nhánh dạng JSON |
| `is_default_branch` | bool | Nhánh mặc định khi không khớp điều kiện nào (chống mất phiếu) |
| `skip_duplicate` | int | 0 không bỏ · 1 bỏ khi trùng bước liền trước · 2 bỏ khi đã duyệt ở bước bất kỳ |
| `sla_hours` | int | Hạn duyệt tính từ lúc được giao (giờ); 0 = không đặt hạn |
| `fallback_employee_id` | int | FK → nhân sự dự phòng khi không tìm được người duyệt |
| `on_no_approver` | int | 1 chuyển cho người dự phòng · 3 dừng phiếu và báo quản trị |

**Giá trị `approver_kind`:**

| Giá trị | Ý nghĩa | `approver_ref` |
|---|---|---|
| 1 | Người cụ thể | employee_id |
| 2 | Theo vai trò | mã vai trò |
| 3 | Trưởng bộ phận người nộp | (không cần) |
| 4 | Lên N cấp quản lý | số cấp |
| 5 | Người đại diện pháp nhân | (không cần) |
| 6 | Lấy từ một ô trên phiếu | tên cột |
| 7 | Trưởng bộ phận của phòng ban chỉ định | danh sách department_id |

**Logic chính:**

- `is_default_branch = True` bắt buộc phải có ở mỗi chặng có nhánh; thiếu thì phiếu không khớp điều kiện nào bị mất.
- `on_no_approver = 2` ("đẩy lên cấp trên") đã bỏ từ 21/08/2026 (CR-114); hằng số giữ lại để đọc dữ liệu cũ, không còn là lựa chọn.
- Bộ máy cố ý không có giá trị "tự động duyệt qua" — văn bản không người duyệt phải dừng và kêu, không tự ban hành.

---

### `tab_approval_switch` — Bật/tắt bộ máy theo loại chứng từ

Đường lui của cả phase 3. Tắt là mọi chứng từ loại đó quay về đường duyệt cũ ngay lập tức. Mặc định TẮT.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `entity` | str(50) | Loại chứng từ; UNIQUE |
| `is_enabled` | bool | Đang bật bộ máy mới không |
| `note` | str(500) | Ghi chú |

**Logic chính:**

- Phiếu đã bắt đầu chạy bằng bộ máy mới thì vẫn chạy tiếp khi tắt cờ — cắt ngang là bỏ rơi phiếu.
- Thêm bảng mới không được tự bật cờ (`is_enabled = False` mặc định) để không đổi hành vi thứ đang chạy.

---

### `tab_approval_instance` — Phiên chạy

Một phiếu đang đi qua một luồng. Mỗi chứng từ nhiều nhất một phiếu đang mở, đảm bảo bằng cột `running_slot`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `entity` | str(50) | Loại chứng từ |
| `entity_id` | int | Id chứng từ |
| `running_slot` | int | Cột SINH: bằng `entity_id` khi còn mở (status IN 1,6), NULL khi kết thúc; UNIQUE `(entity, running_slot)` |
| `entity_code` | str(100) | Mã chứng từ lưu lại để hiện trên màn "Việc của tôi" mà không nối bảng |
| `entity_title` | str(500) | Tên chứng từ lưu lại tương tự |
| `flow_id` | int | FK → `tab_approval_flow.id` |
| `flow_version` | int | Phiên bản luồng lúc bắt đầu |
| `flow_snapshot` | text | Bản chụp toàn bộ luồng dạng JSON lúc bắt đầu chạy |
| `status` | int | Trạng thái phiên chạy (xem bên dưới) |
| `current_seq` | int | Bước hiện tại |
| `started_by_employee_id` | int | FK → nhân sự đã nộp phiếu |
| `started_at` | datetime | Thời điểm bắt đầu |
| `finished_at` | datetime | Thời điểm kết thúc |
| `finish_reason` | str(1000) | Lý do của hành động kết thúc |

**Trạng thái `status`:**

| Giá trị | Nhãn |
|---|---|
| 1 | Đang chạy |
| 2 | Đã duyệt |
| 3 | Từ chối |
| 4 | Trả lại |
| 5 | Đã rút |
| 6 | Kẹt — không có người duyệt |

**Logic chính:**

- `running_slot` là cột SINH, tương tự `open_slot` của phiên bản văn bản, bịt race condition khi nhấp đúp nút "Gửi duyệt".
- `flow_snapshot` lưu bản chụp luồng lúc bắt đầu; phiếu chạy theo bản chụp này, không theo `tab_approval_node` đang sống — sửa luồng không làm hỏng phiếu đang chạy.
- Trạng thái 1 và 6 được coi là "còn mở" (`INSTANCE_OPEN_STATUSES`).

---

### `tab_approval_task` — Việc cần xử lý

Một người cần xử lý một bước. Là nguồn dữ liệu của màn "Việc của tôi".

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `instance_id` | int | FK → `tab_approval_instance.id` |
| `node_seq` | int | Thứ tự bước |
| `node_name` | str(200) | Tên bước lưu lại để hiện mà không nối bảng |
| `order_no` | int | Thứ tự trong bước, dùng khi `multi_mode = lần lượt` |
| `assignee_employee_id` | int | FK → nhân sự cần xử lý |
| `status` | int | Trạng thái việc (xem bên dưới) |
| `due_at` | datetime | Hạn xử lý |
| `decided_at` | datetime | Thời điểm đã xử lý |
| `reminded_at` | datetime | Thời điểm nhắc quá hạn gần nhất |
| `escalated_at` | datetime | Thời điểm đẩy lên cấp trên |

**Trạng thái `status`:**

| Giá trị | Nhãn |
|---|---|
| 1 | Chưa tới lượt |
| 2 | Đang chờ |
| 3 | Đã duyệt |
| 4 | Từ chối |
| 5 | Tự qua vì trùng người duyệt |
| 6 | Đã hủy |

**Logic chính:**

- Chỉ mục `(assignee_employee_id, status)` là quan trọng nhất của cả bộ máy — màn "Việc của tôi" chạy trên chỉ mục này.
- `TASK_SKIPPED_DUPLICATE` (5) là trạng thái riêng, không ghi thành "đã duyệt", để bản in dấu vết phân biệt được ai thật sự đã xem xét.

---

### `tab_approval_action` — Dấu vết duyệt

Nhật ký hành động của phiên chạy. Chỉ ghi thêm, không sửa, không xóa.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `instance_id` | int | FK → `tab_approval_instance.id` |
| `task_id` | int | FK → `tab_approval_task.id`; NULL cho hành động cấp phiên |
| `node_seq` | int | Thứ tự bước |
| `node_name` | str(200) | Tên bước |
| `action` | int | Hành động: 1 bắt đầu · 2 duyệt · 3 từ chối · 4 trả lại · 5 rút · 6 tự qua · 7 chuyển người · 8 ý kiến · 9 quá hạn · 10 kết thúc |
| `actor_employee_id` | int | FK → người thật sự bấm nút |
| `on_behalf_of_id` | int | FK → người mà việc đó vốn là của họ (khi duyệt thay ủy quyền) |
| `delegation_id` | int | FK → `tab_delegation.id` — quyết định ủy quyền căn cứ theo |
| `comment` | text | Ý kiến/lý do |

**Logic chính:**

- Ba cột danh tính (`actor_employee_id`, `on_behalf_of_id`, `delegation_id`) để bản in ghi đúng "ông B duyệt thay ông A theo ủy quyền số 12".
- Ba hành động bắt buộc có `comment`: từ chối, trả lại, rút.

---

### `tab_delegation` — Ủy quyền có thời hạn

Cho phép một nhân sự xử lý việc của nhân sự khác trong khoảng thời gian xác định. Cấm ủy quyền dây chuyền.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `from_employee_id` | int | FK → nhân sự ủy quyền |
| `to_employee_id` | int | FK → nhân sự nhận ủy quyền |
| `entity` | str(50) | Loại chứng từ được ủy quyền; rỗng = mọi loại |
| `from_date` | date | Ngày bắt đầu, bắt buộc |
| `to_date` | date | Ngày kết thúc, bắt buộc |
| `is_active` | bool | Cờ hủy nhanh mà không cần sửa ngày |
| `reason` | str(500) | Lý do ủy quyền |

**Logic chính:**

- Cả hai ngày bắt buộc — ủy quyền vô thời hạn là nguồn gốc của "người đã nghỉ vẫn còn ký thay".
- Cấm ủy quyền dây chuyền: A ủy B thì B không ủy tiếp phần việc nhận từ A — chặn ở `delegation_service.resolve`, không phải ràng buộc dữ liệu.
- `entity` rỗng = ủy quyền tất cả; có giá trị = chỉ loại đó (ủy quyền ký văn bản không kéo theo ủy quyền duyệt chi tiền).

---

## Phần 4: Duyệt dấu (seal_request)

Cụm này gồm 2 bảng. Quản lý yêu cầu đóng con dấu cho văn bản.

---

### `tab_seal_type` — Loại con dấu

Danh mục các loại con dấu.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `name` | str(100) | Tên loại con dấu, UNIQUE |
| `description` | str(255) | Mô tả |
| `is_active` | bool | Cờ ẩn/hiện |

**Logic chính:**

- Dữ liệu master; `tab_seal_request.seal_type_id` trỏ vào bảng này.

---

### `tab_seal_request` — Yêu cầu đóng dấu

Mỗi dòng là một phiếu xin đóng dấu cho một văn bản hoặc tài liệu.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | Khóa chính tự tăng |
| `code` | str(50) | Mã phiếu, UNIQUE |
| `title` | str(255) | Tiêu đề phiếu |
| `purpose` | text | Mục đích đóng dấu |
| `seal_type_id` | int | FK → `tab_seal_type.id` — loại con dấu |
| `department_id` | int | FK → phòng ban của người yêu cầu |
| `company_id` | int | FK → pháp nhân |
| `requester` | str(255) | Tên người yêu cầu (lưu log) |
| `requester_id` | int | FK → id nhân sự người yêu cầu |
| `first_approver_id` | int | FK → id nhân sự người duyệt đầu tiên, do người yêu cầu chọn |
| `status` | str(30) | Trạng thái văn bản dạng chuỗi: `draft`, v.v. |
| `note` | text | Ghi chú |
| `is_deleted` | bool | Cờ xóa mềm |

**Logic chính:**

- `status` là chuỗi (ngoại lệ so với quy tắc SMALLINT+IntEnum của module mới — bảng này thuộc cụm cũ hơn).
- `first_approver_id` do người yêu cầu chọn lúc gửi — người duyệt đầu tiên trong luồng dấu.
- `requester` lưu tên tường minh để log bền vững ngay cả khi bản ghi nhân sự bị sửa.

---

## Quan hệ trong cụm

**Document ↔ Approval (qua `approval_bridge.py`)**

- Cầu nối là module `document/approval_bridge.py`; không có khóa ngoại vật lý giữa hai cụm.
- `tab_approval_instance.entity = 'document'` và `tab_approval_instance.entity_id = tab_document.id`.
- Khi phiên chạy kết thúc, `entity_hooks` gọi lại các hàm trong `approval_bridge`: `_on_approved` → gọi `service.approve()` hoặc `service.mark_pending_issue()`; `_on_rejected` → `service.reject()`; `_on_returned` → `service.send_back()`; `_on_withdrawn` → `service.withdraw_document()`.
- Bối cảnh cho điều kiện rẽ nhánh và cách chọn người duyệt được dựng bởi `entity_context(doc)`: các ô `doc_type_id`, `company_id`, `department_id`, `secrecy_level`, `urgency`, `owner_employee_id`, `drafter_employee_id`, `signer_employee_id`.
- Bản clone phải có luồng khớp đúng pháp nhân (`company_flow_only = True`); không có luồng riêng thì bị chặn trước khi đổi trạng thái.

**Document ↔ Doc\_catalog**

- `tab_document.doc_type_id` → `tab_doc_type.id`: loại quyết định kiểu định danh, mức mật mặc định, luồng duyệt mặc định, và cờ `auto_issue_after_approval`.
- `tab_document.numbering_rule_id` → `tab_document_numbering_rule.id`: quy tắc đánh số áp dụng; bộ đếm thật ở `tab_number_sequence`.
- `tab_document.book_id` → `tab_document_book.id`: khai sẵn, luôn rỗng ở bản 1.
- `tab_document_link.relation` dùng chung hằng số loại quan hệ với `tab_doc_type_link_rule.relation`.
- `tab_security_level.value` là con số lưu thẳng vào `tab_document.secrecy_level` và `tab_document.urgency`; không có khóa ngoại, chống mồ côi qua `security_level_guard.py`.
- `tab_document_template.doc_type_id` → `tab_doc_type.id`: mẫu thuộc loại văn bản, không phải loại mẫu riêng.
