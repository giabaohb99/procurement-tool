# MÔ TẢ: MÀN HÌNH QUẢN LÝ IMPORT + LOG LỖI + DB

Dùng chung cho cả Import Khảo sát và Import Đơn mua hàng.

## 1. Mục tiêu
- Theo dõi **mọi lần import**: ai làm · khi nào · file gì · kết quả · **danh sách lỗi/cảnh báo chi tiết từng dòng**.
- **Chuông thông báo** khi import xong → bấm vào dẫn **thẳng tới trang chi tiết** của lần import đó.
- **Lưu lại file đã import** để đối chiếu / chạy lại (nên có — đã chốt).

## 2. Màn hình

### 2.1 Danh sách Import (`/import-batches`)
Cột: `Thời gian · Người import · Chức năng (Khảo sát/ĐMH) · Tên file (chỉ hiện text) · Chế độ (Thử/Ghi) · Trạng thái · Tạo · Cập nhật · Bỏ qua · Cảnh báo · Lỗi`.
- **Không** cho tải file ở danh sách — chỉ hiển thị **tên file**. Việc tải/xem file để ở trang chi tiết.
Lọc: theo chức năng · trạng thái · người · khoảng ngày.

### 2.2 Chi tiết 1 lần Import (`/import-batches/:id`)  ← chuông dẫn tới đây
- **Header**: người import · thời điểm bắt đầu/kết thúc · file gốc (nút **Tải file**) · chế độ · tổng dòng · đếm (tạo/cập nhật/bỏ qua/cảnh báo/lỗi) · trạng thái.
- **Tab log**: `Lỗi` | `Cảnh báo` | `Cần rà soát` | `Tất cả`.
  - Bảng: `Dòng (sheet) · Loại · Thông báo · Khoá tham chiếu · Kết quả`.
  - Ví dụ: dòng 42 — *NCC text-only* — "MST 0316… khớp NCC khác tên viết tắt" — NCC=Đông Tây — (giữ text).
- **Thông báo đặc biệt**: khối riêng đầu trang (vd: "12 dòng tạo SP tự động", "5 dòng NSPT trống").
- Nút **Chạy lại** (re-run từ file đã lưu, chế độ apply) — tuỳ chọn.

## 3. Chuông (notification)
- Worker xong → `trigger_notification` cho **người import**: *"Import {Khảo sát/ĐMH} xong: X tạo · Y cập nhật · Z lỗi"*, `link=/import-batches/{id}`.
- Lỗi nặng (task fail) → chuông *"Import lỗi — xem chi tiết"*.

## 4. Lưu file đã import
- Lưu file `.xlsx` gốc qua cơ chế **StoredFile** sẵn có (như đính kèm) → `import_batch.file_id`.
- Cho phép **tải lại** ở màn chi tiết + **chạy lại** từ chính file đó.
- Giữ để audit ("data này import từ file nào, ngày nào, ai").

## 5. DB — 2 bảng

### 5.1 `tab_import_batch` — 1 dòng / 1 lần import
| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| id | BigInt PK | |
| module | SmallInt (enum) | `1 survey · 2 purchase_order` |
| mode | SmallInt (enum) | `0 dry_run · 1 apply` |
| filename | String(255) | tên file gốc |
| file_id | BigInt | FK → StoredFile (file .xlsx đã lưu) |
| file_size | Int | byte |
| sheet_info | Text(JSON) | sheet dùng + số dòng mỗi sheet |
| status | SmallInt (enum) | `0 queued · 1 running · 2 done · 3 failed` |
| total_rows | Int | tổng dòng đọc |
| created_count | Int | số bản ghi tạo |
| updated_count | Int | số bản ghi cập nhật |
| skipped_count | Int | bỏ qua |
| warning_count | Int | cảnh báo |
| error_count | Int | lỗi |
| review_count | Int | cần rà soát |
| error_summary | Text | tóm tắt khi `failed` |
| started_at / finished_at | DateTime | |
| created_by (=người import) | BigInt | + audit |

### 5.2 `tab_import_log` — nhiều dòng / 1 batch (chi tiết)
| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| id | BigInt PK | |
| batch_id | BigInt idx | FK → import_batch |
| sheet | String(40) | vd `3.KS-NCC` / `4.KS-SP` / `6.TIENDO` |
| row_no | Int | số dòng trong sheet |
| level | SmallInt (enum) | `0 info · 1 warning · 2 review · 3 error` (có thứ tự → lọc "≥ warning" dễ) |
| category | String(40) | mã loại (xem §6) — **giữ string** vì danh sách còn mở rộng |
| message | Text | mô tả cho người đọc |
| ref_key | String(120) | khoá tham chiếu (Mã yêu cầu / Misa / Số HĐ / NCC) |
| target_code | String(50) | bản ghi tạo/cập nhật (KS##### / PO#####) |
| raw | Text(JSON) | vài cột gốc của dòng (để soi) |

> Index: `import_log(batch_id, level)` để lọc nhanh theo tab.

### 5.3 Enum (định nghĩa 1 chỗ, backend `IntEnum` + FE map số→nhãn/màu)
```python
class ImportModule(IntEnum):  SURVEY = 1;  PURCHASE_ORDER = 2
class ImportMode(IntEnum):    DRY_RUN = 0; APPLY = 1
class ImportStatus(IntEnum):  QUEUED = 0;  RUNNING = 1; DONE = 2; FAILED = 3
class LogLevel(IntEnum):      INFO = 0;    WARNING = 1; REVIEW = 2; ERROR = 3
```
- **Cột cố định + có thứ tự** (`level`, `status`, `module`, `mode`) → lưu **SmallInt** theo enum: gọn, so sánh/lọc nhanh, 1 nguồn định nghĩa.
- **`category`** (loại lỗi) → **string code** vì hay thêm loại mới; dùng int sẽ phải đánh số lại + migrate mỗi lần thêm.
- FE có 1 map `{số: {nhãn, màu}}` để hiển thị (vd `3→"Lỗi"/đỏ`, `1→"Cảnh báo"/cam`).
- Lưu ý: đây là **module kỹ thuật** (import) nên dùng số; còn trạng thái nghiệp vụ (PYC/PO/khảo sát) vẫn giữ **string** theo quy ước hiện tại của repo — không đổi.

## 6. Phân loại `category` (log)
`bad_date` · `bad_number` · `missing_key` (thiếu phân loại/NCC/Misa) · `ncc_text_only` · `mst_conflict` · `ncc_created` · `product_created` (SP tạo tự động) · `nspt_missing` · `value_unmatched` (trạng thái/ĐVT/kho không khớp tập chuẩn) · `duplicate_in_file` · `skipped_exists`.

## 7. Quyền & lưu trữ
- Xem/chạy import: vai trò có quyền tạo trên module tương ứng (khảo sát/ĐMH) hoặc admin.
- Retention: giữ batch + log; file .xlsx có thể dọn định kỳ (tuỳ chọn) — mặc định giữ.
