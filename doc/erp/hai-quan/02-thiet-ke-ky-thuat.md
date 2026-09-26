# PHÂN HỆ TRA CỨU GIÁ HẢI QUAN — THIẾT KẾ KỸ THUẬT

> **Mã tài liệu:** ERP-HQ-02 · **Bản:** 1.5 — 23/09/2026 · **Đã cài đặt HQ1…HQ6:** bao-CR-470, ở LOCAL (cây `erp-v2`), chưa commit, chưa deploy · **Loại:** THIẾT KẾ + ĐÃ DỰNG
> **Đi kèm:** [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md) — tài liệu này trả lời *làm thế nào* cho các tính năng nhóm N, T, B ở đó.
> **Yêu cầu của đại ca (23/09/2026):** hiển thị **đủ mọi cột như trong Excel**, nhưng **lưu dưới DB phải gọn nhất, tối ưu nhất**, vì dữ liệu thật có thể nhiều hơn rất nhiều và tăng theo thời gian.

Mọi con số trong tài liệu này **đo trên 5 tệp thật** trong thư mục `thongtinhaiquan/data/` (18.243 dòng, kết xuất GTT02 ngày 18/09/2026), không phải ước đoán.

## Lịch sử bản

| Bản | Ngày | Thay đổi | Vì sao |
|---|---|---|---|
| 1.0 | 23/09/2026 | Bản đầu | |
| 1.1 | 23/09/2026 | **(1)** Gộp *doanh nghiệp nhập khẩu* và *đối tác* thành **một bảng đối tượng** có cột phân loại. **(2)** **Bỏ bảng tổng hợp theo tháng**; kỳ gom (tháng / quý / năm) tính lúc đọc. **(3)** Bảng điều khiển cố định **dùng lại `tab_report_snapshot`** của phân hệ Báo cáo. **(4)** **Bỏ từ điển tên hàng**, tên hàng nằm thẳng trong dòng hàng. **(5)** Sửa lại con số dung lượng | (1)(2)(3) theo góp ý của đại ca. (2)(4)(5) do **đo lại** khi xét góp ý: bản 1.0 dựa trên giả định *tên hàng lặp lại nhiều* — sai, xem §2.1 |
| **1.2** | 23/09/2026 | **Bỏ `tab_customs_batch`**, dùng lại **`tab_import_batch` + `tab_import_log`** của mô-đun `import_tool` sẵn có (§3.1). Bước "xem trước khoảng ngày rồi mới chốt" dùng chế độ **`DRY_RUN`** có sẵn; tệp gốc giữ qua `file_id` có sẵn | Rà thêm theo tinh thần "tận dụng" của đại ca khi viết tài liệu giao diện |
| **1.3** | 23/09/2026 | Thêm §2.2 định nghĩa **tờ khai** và **dòng hàng**; đổi tên bảng lớn `tab_customs_declaration` → **`tab_customs_line`**; đổi "dòng tờ khai" thành "dòng hàng" trong mọi tài liệu | Đại ca hỏi *"định nghĩa một tờ khai là như thế nào"* — đo lại thì mỗi dòng Excel là **một dòng hàng**, không phải một tờ khai, và dữ liệu **không gom lại thành tờ khai được** |
| **1.4** | 23/09/2026 | **Bỏ lớp đệm `tab_report_snapshot`.** Không còn gì tính sẵn: mọi con số tính lúc mở | Đại ca chốt màn tra cứu **hai thẻ Danh sách / Biểu đồ, biểu đồ chỉ hiện khi đã lọc** — trang tổng quan (thứ duy nhất dùng snapshot) bỏ. Không có task định kỳ nào |
| **1.5** | 23/09/2026 | Thêm §10: bốn bảng danh mục của HQ4/HQ6 (`tab_customs_ingredient_alias` · `tab_customs_pesticide` · `tab_customs_regulation` · `tab_customs_tariff`), hai cột suy ra trên `tab_customs_line` (`active_ingredient` · `formulation`), script nạp danh mục, bộ nhận hoạt chất ba nguồn, khóa thứ hai `customs_regulation` | Đại ca bảo làm đủ mọi phase một lượt |
| **1.6** | 25/09/2026 | **bao-CR-496.** (1) Nhật ký **từng dòng** của lô: thêm cột `row_status` (SMALLINT, `ImportRowStatus`: 0 dòng nhật ký thường · 1 Thêm mới · 2 Lỗi · 3 Trùng trong lô) vào **`tab_import_log` có sẵn**, KHÔNG tạo bảng mới — xem §3.1b. (2) Bảng mới `tab_customs_saved_filter` (bộ lọc người dùng đặt tên, riêng từng tài khoản, `is_shared` chừa sẵn) | Chị Mi (F01 ghi chú 25/09, F07); đại ca chốt: không có kết cục «Cập nhật», dòng trùng chỉ đánh dấu không xóa, bộ lọc lưu riêng từng người |

---

## 1. Cách lưu — hai tầng dữ liệu và một lớp đệm

| Tầng | Lưu gì | Tối ưu cho |
|---|---|---|
| **1. Tệp gốc** | Tệp Excel người dùng nạp, giữ **nguyên văn** trong kho tệp (R2, theo `STORAGE_PREFIX`) | Truy vết và **nạp lại** khi luật đọc tệp thay đổi |
| **2. Dòng hàng + bảng đối tượng** | Mỗi dòng Excel thành một dòng có **kiểu đúng**; chữ **thật sự lặp lại** (tên doanh nghiệp, tên đối tác) tách ra bảng đối tượng; mã chuẩn quốc tế lưu thẳng mã | Dung lượng + mọi truy vấn tra cứu và biểu đồ |
| ~~Lớp đệm~~ | ~~Bảng điều khiển tính sẵn trong `tab_report_snapshot`~~ — **bỏ ở bản 1.4**, xem §3.6 | |

**Vì sao cần tầng 1.** Tầng 2 là dữ liệu *đã diễn giải* — đã vá ngày, đã bóc dấu `'`, đã đổi chữ thành mã. Diễn giải sai một luật (ví dụ luật vá ngày ở §4.2) thì tầng 2 sai theo, và không có tệp gốc thì **không sửa lại được**. Tốn khoảng 3 MB mỗi tệp, đổi lại nạp lại được mọi lúc.

**Vì sao không còn bảng tổng hợp riêng** — xem §2.1 và §3.5.

---

## 2. Số đo từng cột

| Nhóm | Cột (số thứ tự trong Excel) | Số giá trị khác nhau / 18.243 | Cỡ trung bình | Quyết định |
|---|---|---|---|---|
| **Chữ dài, gần như duy nhất** | 7 Tên hàng | 12.436 — **10.323 tên chỉ xuất hiện đúng một lần** | **187 byte** | → **lưu thẳng trong dòng** (§2.1) |
| **Chữ lặp lại nhiều** | 3 Tên doanh nghiệp XNK | 1.447 mã số thuế (lặp ~12,6 lần) | 41 byte | → **bảng đối tượng** (§3.2) |
| | 4 Đơn vị đối tác | 2.056 (lặp ~8,9 lần) | 30 byte | → **bảng đối tượng** (§3.2) |
| **Chữ nhưng thực chất là loại** | 21 Phương tiện vận chuyển | **5** | 29 byte | → **số nguyên** theo luật R2 (§3.4) |
| **Mã chuẩn, ngắn** | 1 Nơi mở tờ khai · 5 Mã HS · 12 Nguyên tệ · 16 Đơn vị tính · 17 Xuất xứ · 20 Điều kiện giao hàng · 31 Nước nhập khẩu | 1–93 | 2–10 byte | → lưu **thẳng mã**, bộ ký tự ASCII (1 byte/ký tự thay vì tới 4) |
| **Gần như duy nhất** | 18 Số hợp đồng | 10.710 | 11 byte | → lưu thẳng |
| **Số** | 8–11 Đơn giá · 13–14 Tỷ giá · 15 Lượng · 22–30 Thuế | — | — | → **kiểu số cố định** (`DECIMAL`), không lưu dạng chữ |
| **Ngày** | 0 Ngày đăng ký · 19 Ngày hợp đồng | — | — | → kiểu `DATE` — **nhưng xem §4.2, hai cột này KHÁC nhau** |

Năm cột **chỉ có đúng một giá trị** trên toàn bộ dữ liệu mẫu (23 · 25 · 27 · 30 · 31). Vẫn **lưu đủ** — đại ca yêu cầu hiển thị đủ cột, và dữ liệu một chương HS không nói được gì về chương khác. Chúng là số hoặc mã 2 ký tự nên gần như không tốn chỗ.

### 2.1 Phát hiện quyết định bản 1.1: tên hàng KHÔNG lặp lại

Bản 1.0 cho rằng tên hàng lặp lại nhiều (cùng một mặt hàng nhập đi nhập lại mỗi tháng), nên tách thành từ điển và gom sẵn theo *mặt hàng × tháng*. Đo lại thì **sai**:

| Gom theo | Số dòng tổng hợp | Gọn hơn bảng gốc |
|---|---|---|
| **Tên hàng × tháng × đơn vị** (thiết kế bản 1.0) | **15.092** | **1,2 lần** — gần như không gọn gì |
| Tên hàng (cả thời kỳ) | 12.436 | 1,5 lần |
| Mã HS × tháng × đơn vị | 731 | 25 lần |
| Mã HS × quý × đơn vị | 367 | 50 lần |
| Mã HS × tháng × đơn vị × xuất xứ | 2.263 | 8 lần |

**83% tên hàng chỉ xuất hiện đúng một lần.** Tên hàng trên tờ khai là chữ tự do, nhét cả hàm lượng, quy cách đóng gói, số lô — hai lô cùng một hoạt chất gần như không bao giờ trùng tên từng chữ. Hệ quả:

- **"Mặt hàng" theo nghĩa của thu mua không có sẵn làm khóa trong dữ liệu.** Khóa gom thật sự thu mua cần là **hoạt chất** — chỉ có khi làm xong T-04 của `01`.
- **Từ điển tên hàng không tiết kiệm được gì**, thậm chí **tốn hơn**: lặp 1,5 lần mà mỗi mục từ điển phải mang thêm mã băm chống trùng và chỉ mục riêng. Bỏ.
- **Bảng tổng hợp theo mặt hàng không gọn hơn bảng gốc.** Bỏ — xem §3.5 thay bằng gì.

### 2.2 Một tờ khai là gì — và dữ liệu mình có chỉ là DÒNG HÀNG

**Tờ khai hải quan nhập khẩu** là chứng từ doanh nghiệp nộp cho hải quan (hệ VNACCS) cho **một lô hàng nhập**. Nó có hai phần:

| Phần | Gồm | Cột tương ứng trong Excel |
|---|---|---|
| **Đầu tờ khai** — một lần cho cả tờ | **Số tờ khai** (12 chữ số) · ngày đăng ký · chi cục mở tờ khai · doanh nghiệp nhập · đối tác nước ngoài · số và ngày hợp đồng · điều kiện giao hàng · phương tiện vận chuyển | 0 · 1 · 2–3 · 4 · 18–19 · 20 · 21 · 31 — **số tờ khai KHÔNG có** |
| **Các dòng hàng** — tối đa 50 dòng, mỗi dòng một mặt hàng | Số thứ tự hàng · mã HS · tên hàng · lượng · đơn vị · đơn giá · xuất xứ · thuế suất và tiền thuế | 5 · 6 · 7 · 8–17 · 22–30 |

Tệp GTT02 là **kết quả tra cứu đã lọc theo mã HS 3808**, trải phẳng thành bảng: **mỗi dòng Excel = một DÒNG HÀNG**, phần đầu tờ khai lặp lại ở mọi dòng. Đo trên 5 tệp mẫu:

- **Số thứ tự hàng chạy từ 1 đến 50** — đúng trần 50 dòng một tờ khai của VNACCS.
- **9.484 dòng mang số thứ tự 1** → bộ mẫu có **nhiều nhất khoảng 9.500 tờ khai**, không phải 18.243.
- **Không gom lại thành tờ khai được.** Không có số tờ khai; thử gom theo *ngày + chi cục + doanh nghiệp + số hợp đồng* thì chỉ **71% nhóm** có số thứ tự liền mạch 1, 2, 3…; phần còn lại là những nhóm kiểu **chỉ có đúng dòng số 7** — nghĩa là các dòng 1–6 của tờ khai đó là **hàng khác mã HS, đã bị bộ lọc 3808 loại ra** trước khi tới tay mình.

Hệ quả cho thiết kế:

1. **Gọi đúng tên.** Bảng lớn là **`tab_customs_line`** — mỗi dòng là một dòng hàng. Gọi nó là "tờ khai" thì sớm muộn có người đếm số dòng rồi báo cáo "18.243 tờ khai", sai gần gấp đôi.
2. **Đếm "số lần nhập" bằng số dòng là sai.** Màn hình ghi **"số dòng hàng"**. Muốn đếm số tờ khai thì chỉ **ước lượng** được (đếm dòng số thứ tự 1), không đếm chính xác được.
3. **Không dựng màn "xem cả một tờ khai".** Dữ liệu không đủ để dựng đúng, và dù dựng được cũng chỉ thấy phần hàng 3808 của tờ khai đó.
4. **Nếu GTT02 xuất được kèm số tờ khai** (câu Q6 ở [`01`](./01-danh-sach-tinh-nang.md) §9) thì mọi thứ đổi hẳn: *số tờ khai + số thứ tự hàng* là **khóa duy nhất tự nhiên** — giải luôn bẫy "không có khóa duy nhất" ở N-04 (nạp lại không cần xóa theo khoảng ngày nữa), và đếm được số tờ khai chính xác. Thêm một cột `VARCHAR(12)` là đủ.

---

## 3. Lược đồ

Quy ước chung: tiền tố bảng `tab_customs_`; khóa ngoài **không khai ràng buộc ở DB** trên bảng dòng hàng vì bảng đó chia phân vùng (MySQL không cho khóa ngoài trên bảng phân vùng — cùng lẽ với bốn bảng nhật ký của CR-454).

### 3.1 Lô nạp — dùng lại `tab_import_batch` + `tab_import_log`, KHÔNG tạo bảng mới

Mô-đun `import_tool` đã có sẵn bảng lô nạp **dùng chung cho mọi phân hệ**, và nó có đủ thứ lô hải quan cần:

| Nhu cầu | Có sẵn trong `import_tool` |
|---|---|
| Phân biệt lô hải quan với lô khác | Cột `module` (IntEnum `ImportModule`) — **thêm `CUSTOMS_DECLARATION = 3`**. Dải 3–9 được **chừa sẵn cho nghiệp vụ**, đúng chỗ |
| Giữ tệp gốc (tầng 1) | `file_id` → `StoredFile`, kèm `filename` · `file_size` |
| Xem trước rồi mới chốt (§4.4) | `mode = DRY_RUN` chạy thử không ghi; `APPLY` mới ghi thật |
| Trạng thái | `QUEUED · RUNNING · DONE · FAILED · REVERTED` |
| Hoàn tác một lô nạp nhầm | Trạng thái `REVERTED` — với hải quan là xóa mọi dòng mang `batch_id` đó |
| Số liệu lô | `total_rows` · `created_count` · `deleted_count` (= số dòng cũ bị thay trong khoảng ngày) · `warning_count` · `error_count` · `error_summary` · `started_at` · `finished_at` |
| Cảnh báo từng dòng | `tab_import_log` (`row_no` · `level` · `message`) |
| Màn danh sách + chi tiết lô | **`/system/imports`** của bản mới (CR-186) — lô hải quan tự hiện ra, lọc theo phân hệ. ⚠️ **Bản cũ không có màn này**, xem [`04`](./04-giao-dien.md) |

Ba thứ bản 1.1 định lưu riêng thì **suy ra được**, không cần cột mới:

- **Khoảng ngày của lô** = `MIN/MAX(reg_date)` của các dòng mang `batch_id` đó.
- **Số dòng đã vá ngày** = đếm `date_fixed = 1` theo `batch_id`. **Không** ghi 7.651 dòng cảnh báo vào `tab_import_log` cho mỗi lần nạp — vá ngày là việc bình thường của khuôn tệp này, không phải bất thường. Nhật ký dòng chỉ dành cho thứ **thật sự lạ** (mã phương tiện lạ, ô số không đọc được).
- **Lô bị thay** không cần trạng thái riêng: lô mới ghi `deleted_count` + một dòng nhật ký nói đã thay khoảng ngày nào.

### 3.1b Nhật ký TỪNG DÒNG — cột `row_status` trên `tab_import_log` (bản 1.6, bao-CR-496)

Ghi chú 25/09 của chị Mi (F01): sau khi nạp phải xem được **đủ mọi dòng** của tệp kèm kết cục, không chỉ dòng có cảnh báo. Hai cách: thêm cột vào bảng nhật ký chung, hoặc bảng riêng. **Chọn thêm cột `row_status`** (SMALLINT, `ImportRowStatus` — luật R2) vào `tab_import_log`, vì:

- bảng riêng chỉ chép lại `batch_id` · `row_no` · `message` và phải dựng lại phân trang, quyền, hoàn tác — thứ `import_tool` đã có;
- cột mặc định `0` = *dòng nhật ký thường*, các phân hệ khác dùng `import_tool` **không thấy gì đổi**; chỉ mục `(batch_id, row_status)` để đếm / lọc theo lô;
- mỗi dòng dữ liệu một dòng nhật ký, ghi bằng **chèn hàng loạt** (`customs/row_log.py`), ở **cả chạy thử lẫn ghi thật** để người nạp soi trước khi bấm ghi.

Ba kết cục, **cố ý không có «Cập nhật»** (đại ca chốt: nguồn không có số tờ khai, không biết dòng nào là dòng cũ): **1 Thêm mới** · **2 Lỗi** (bộ đọc bỏ dòng, hiện chỉ có «không đọc được Ngày đăng ký») · **3 Trùng trong lô** = giống hệt 32 cột *sau chuẩn hóa của bộ đọc* với một dòng đứng trước trong cùng tệp. Dòng trùng **chỉ đánh dấu, vẫn ghi** vào `tab_customs_line` — hai dòng giống hệt có thể là hai lô hàng thật (`01` N-04: tệp mẫu có 806 cặp); luật đếm `created_count` / `skipped_count` của lô giữ nguyên, số dòng trùng ghi thêm vào `sheet_info.duplicate_rows`. Đường đọc: `GET /api/customs/imports/{id}/rows?row_status=` + `/rows/summary` (`saved_filter_controller.py`). Lô nạp **trước** CR-496 không có nhật ký từng dòng — màn hình nói rõ thay vì hiện bảng trống.

**Một lô = một tệp** (`file_id` chỉ trỏ được một tệp). Chọn cả bộ 5 tệp một lần thì sinh 5 lô liền nhau — không sao, vì đo được 5 tệp phủ 5 khoảng ngày **không chồng nhau** (§4.4). Nguy cơ quên một tệp thì xử bằng **dải tháng đã phủ** trên màn hình ([`04`](./04-giao-dien.md)), tháng trống hiện rõ.

### 3.2 `tab_customs_party` — bảng đối tượng (doanh nghiệp trong nước + đối tác nước ngoài)

Bản 1.0 tách hai bảng. Đại ca góp ý gộp một bảng rồi phân loại — **đúng**: hai bảng có cùng hình dạng (một cái tên, một cách chống trùng), tách ra là hai đoạn mã tra-hoặc-tạo gần như chép nhau.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | INT UNSIGNED, khóa chính | |
| `party_type` | SMALLINT | IntEnum (luật R2): **`DOMESTIC=1`** (doanh nghiệp Việt Nam, có mã số thuế) · **`FOREIGN=2`** (đối tác nước ngoài, không có mã) |
| `dedupe_key` | VARCHAR(40) ASCII | Khóa chống trùng — **mã số thuế** với `DOMESTIC`, **MD5 của tên đã chuẩn hóa** với `FOREIGN` |
| `tax_code` | VARCHAR(14) NULL | Chỉ `DOMESTIC` có; bóc dấu `'` đầu |
| `name` | VARCHAR(255) | Tên của **lần nạp mới nhất** |
| | | **Duy nhất:** `(party_type, dedupe_key)` |

**Phân loại theo BẢN CHẤT, không theo VAI TRÒ** — điểm tinh chỉnh so với cách gọi "nhập khẩu / đối tác":

- **Vai trò** (ai là người nhập, ai là người bán) đã nằm sẵn ở **cột nào của tờ khai trỏ tới**: `importer_id` hay `partner_id`. Ghi thêm vai trò vào bảng đối tượng là lặp một thông tin hai chỗ.
- Phân loại theo vai trò sẽ **vỡ khi có dữ liệu xuất khẩu**: một công ty Việt Nam lúc là người nhập, lúc là người xuất — thành hai dòng cho cùng một công ty. Phân loại theo bản chất (trong nước / nước ngoài) thì một công ty là một dòng dù đóng vai gì.

**Chống trùng doanh nghiệp trong nước theo mã số thuế, không theo tên.** Đo được 1.447 mã số thuế nhưng 1.504 cách viết tên — dữ liệu nguồn viết hoa lộn xộn (`CôNG TY TNHH BAYER VIệT NAM`). Chống trùng theo tên là một công ty tách thành nhiều dòng, và bảng xếp hạng nhà nhập khẩu (T-05) chia nhỏ lượng của cùng một công ty.

**Dừng ở đây, không gộp tiếp.** Đừng đẩy ý gộp này tới mức một "bảng từ điển mọi thứ" cho cả tên hàng, mã HS, đơn vị… Mỗi loại có thuộc tính riêng (tên hàng sau này nối hoạt chất, mã HS có biểu thuế), gộp chung là mất cột có kiểu và chỉ mục yếu đi.

### 3.3 `tab_customs_line` — dòng hàng (bảng lớn nhất)

**Chia phân vùng theo năm của `reg_date`** — đúng khuôn CR-454 (`PARTITION BY RANGE (YEAR(reg_date))` + phân vùng `pmax`), **tận dụng nguyên** `system_log/partition.py` để tự mở phân vùng năm mới. Khóa chính vì vậy là `(id, reg_date)`.

| # Excel | Tiêu đề Excel | Cột | Kiểu | Ghi chú |
|---|---|---|---|---|
| — | — | `id` | BIGINT UNSIGNED | Khóa chính cùng `reg_date` |
| — | — | `batch_id` | INT UNSIGNED | Lô nạp |
| — | — | `source_row` | MEDIUMINT UNSIGNED | Dòng thứ mấy trong tệp gốc — truy vết ngược về đúng ô Excel |
| — | — | `date_fixed` | TINYINT | 1 = dòng này đã được vá ngày đảo |
| 0 | Ngày đăng ký | `reg_date` | DATE | ⚠️ **Đã vá ngày đảo**, §4.2 |
| 1 | Tên nơi mở tờ khai | `office_code` | VARCHAR(10) ASCII | |
| 2–3 | Mã / Tên doanh nghiệp XNK | `importer_id` | INT UNSIGNED | → §3.2, loại `DOMESTIC` |
| 4 | Đơn vị đối tác | `partner_id` | INT UNSIGNED | → §3.2, loại `FOREIGN` |
| 5 | Mã hàng khai báo | `hs_code` | CHAR(8) ASCII | Bóc dấu `'` đầu. **Giữ dạng chữ**: mã HS có số 0 ở đầu (`01012100`) |
| 6 | Số thứ tự hàng | `line_no` | SMALLINT UNSIGNED | |
| 7 | Tên hàng | `product_name` | VARCHAR(255) | **Lưu thẳng** — §2.1. Tìm kiếm dựa vào collation `utf8mb4_unicode_ci` của DB (đã bỏ qua dấu và hoa thường), không cần cột chuẩn hóa riêng |
| 8 | Đơn giá khai báo(USD) | `price_usd` | DECIMAL(16,4) | |
| 9 | Đơn giá NT khai báo | `price_nt` | DECIMAL(16,4) | |
| 10 | Đơn giá điều chỉnh(USD) | `adj_price_usd` | DECIMAL(16,4) **NULL** | Rỗng 42% |
| 11 | Đơn giá NT điều chỉnh | `adj_price_nt` | DECIMAL(16,4) **NULL** | |
| 12 | Nguyên tệ | `currency` | CHAR(3) ASCII | ISO 4217 |
| 13 | Tỷ giá nguyên tệ | `fx_rate` | DECIMAL(14,4) **NULL** | Rỗng 8% |
| 14 | Tỷ giá USD | `usd_rate` | DECIMAL(14,4) | |
| 15 | Lượng | `quantity` | DECIMAL(18,4) | |
| 16 | Đơn vị tính | `unit_code` | VARCHAR(4) ASCII | Mã UN/ECE (`KGM`, `LTR`, `TNE`…) |
| 17 | Tên nuớc xuất xứ | `origin_country` | CHAR(2) ASCII | ISO 3166 |
| 18 | Số hợp đồng | `contract_no` | VARCHAR(40) | |
| 19 | Ngày hợp đồng | `contract_date` | DATE **NULL** | ⚠️ **KHÔNG vá**, §4.2 |
| 20 | Điều kiện giao hàng | `incoterm` | CHAR(3) ASCII | |
| 21 | Phương tiện vận chuyển | `transport_mode` | TINYINT | IntEnum, §3.4 |
| 22–25 | Thuế suất XNK / TTĐB / VAT / tự vệ | `rate_import` · `rate_excise` · `rate_vat` · `rate_safeguard` | DECIMAL(6,2) **NULL** | Rỗng giữ rỗng, **không đổi thành 0** — §5 |
| 26–30 | Thuế XNK / TTĐB / VAT / môi trường / tự vệ | `tax_import` · `tax_excise` · `tax_vat` · `tax_environment` · `tax_safeguard` | DECIMAL(18,3) **NULL** | Số tiền VND **có 3 chữ số lẻ** trong dữ liệu gốc (vd `19961918.592`) — `DECIMAL(18,2)` sẽ cắt mất |
| 31 | Nước nhập khẩu | `import_country` | CHAR(2) ASCII | |

**Chỉ mục phụ — cố ý giữ ít**, vì mỗi chỉ mục tốn thêm dung lượng:

| Chỉ mục | Phục vụ |
|---|---|
| `(hs_code, reg_date)` | Lọc theo mã HS + khoảng thời gian — đường vào chính của biểu đồ |
| `(importer_id, reg_date)` | Xếp hạng nhà nhập khẩu (T-05) |
| `(batch_id)` | Hủy / thay một lô |

Tìm theo tên hàng là `LIKE '%…%'` — không dùng được chỉ mục B-tree, **quét trong phạm vi phân vùng năm**. Với ~26.000 dòng/năm của phạm vi hiện tại là vài mili giây. Khi nào chậm thật thì mới thêm chỉ mục toàn văn, xem §3.6.

### 3.4 Phương tiện vận chuyển — theo luật R2

Chuỗi gốc đã mang sẵn mã số ở đầu, lấy đúng mã đó làm giá trị IntEnum:

| Giá trị | Chuỗi gốc | Số dòng |
|---|---|---|
| 1 | `1-Đường không` | 1.649 |
| 2 | `2-Đường biển (container)` | 12.509 |
| 3 | `3-Đường biển (hàng rời, lỏng...)` | 2.074 |
| 4 | `4-Đường bộ (xe tải)` | 650 |
| 9 | `9-Khác` | 1.361 |

Khai vào `status_catalog.py` + `code_sets.py` rồi chạy `gen_status_ts.py`. **Gặp mã lạ lúc nạp thì từ chối cả lô**, không lưu bừa thành `9` — mã lạ nghĩa là GTT02 đã đổi khuôn, cần người xem.

Nguyên tệ, đơn vị tính, xuất xứ, điều kiện giao hàng **không** áp R2: đó là **mã chuẩn quốc tế** (ISO 4217, UN/ECE, ISO 3166, Incoterms), không phải bộ trạng thái của mình.

### 3.5 Kỳ gom — tháng, quý, năm, tính lúc đọc

Đại ca góp ý bảng *theo tháng* là nghĩa hẹp — quý, năm thì sao. Trả lời: **kỳ gom là tham số của truy vấn, không phải một bảng.**

- API biểu đồ nhận `period = month | quarter | year` (thêm `week` nếu cần) và lọc bất kỳ: từ khóa tên hàng · mã HS · xuất xứ · đơn vị · doanh nghiệp · khoảng thời gian.
- Backend lọc dòng hàng theo điều kiện rồi **`GROUP BY` theo kỳ** ngay trong SQL. Kết quả mỗi kỳ: số dòng · tổng lượng · giá thấp nhất · cao nhất · **bình quân gia quyền theo lượng** (`Σ giá × lượng / Σ lượng` — không lấy bình quân cộng của các dòng, một lô 5 kg không được nặng bằng một lô 20 tấn).
- **Giá dùng để gom:** giá điều chỉnh USD nếu có, không có thì giá khai báo USD (N-06 của `01`). Cột giá USD **đã có sẵn** trong dữ liệu gốc — hải quan quy đổi hộ theo tỷ giá đúng ngày khai.
- **Tách theo đơn vị tính**, không cộng kg với lít.

Vì sao như vậy lại đúng:

1. **"Mặt hàng" thu mua cần không có sẵn làm khóa** (§2.1) — người dùng tìm theo từ khóa (thường là tên hoạt chất: *ATRAZINE*, *MANCOZEB*), và thứ cần gom chính là **tập kết quả của lần tìm đó**. Tập đó thay đổi theo từng lần gõ, không tính sẵn được.
2. **Quý và năm chỉ là cách chia khác** trên cùng tập dòng — đổi `period` là xong, không có bảng nào phải đồng bộ với bảng nào.
3. **Quy mô cho phép**: một lượt tìm điển hình chạm vài chục tới vài trăm dòng; kể cả gom cả năm của cả chương HS cũng chỉ ~26.000 dòng.

### 3.6 Không tính sẵn gì — bỏ `tab_report_snapshot` (bản 1.4)

Bản 1.1–1.3 định dùng lại `tab_report_snapshot` của phân hệ Báo cáo cho **trang tổng quan** (top mã HS, top doanh nghiệp…). Đại ca chốt bố cục **hai thẻ Danh sách / Biểu đồ, biểu đồ chỉ hiện khi đã lọc** ([`04`](./04-giao-dien.md) §2) — trang tổng quan bỏ, nên **không còn gì cần tính sẵn**:

| Con số | Tính lúc nào |
|---|---|
| Danh sách dòng hàng | Đọc thẳng bảng, phân trang |
| Biểu đồ + bảng theo kỳ | `GROUP BY` theo kỳ trên tập đã lọc (§3.5) |
| Dải tháng đã phủ | Đếm dòng theo tháng — ~26.000 dòng/năm, vài mili giây |

**Không có task định kỳ nào.** Dữ liệu hải quan chỉ đổi khi có người nạp tệp — đặt task chạy theo giờ là tính đi tính lại cùng một kết quả. Nếu sau này cần lưu sẵn (§3.7) thì **chính tác vụ nạp ghi vào**, vẫn không dùng task định kỳ.

### 3.7 Khi nào mới thêm bảng tổng hợp riêng

Không làm ở đợt 1. Chỉ thêm khi **cả hai** điều kiện đúng:

1. **Đo được chậm thật** — truy vấn biểu đồ vượt khoảng 1 giây trên dữ liệu thật, không phải lo trước.
2. **Có khóa gom lặp lại thật** — **hoạt chất** (sau T-04) hoặc **mã HS** (gọn 25 lần, §2.1). Không bao giờ gom theo tên hàng.

Lúc đó: khóa `(khóa gom, tháng, đơn vị)`, **lưu TỔNG** (`Σ lượng`, `Σ giá × lượng`, số dòng, thấp nhất, cao nhất) chứ **không lưu bình quân** — tổng thì cộng dồn lên quý, năm được; bình quân của các bình quân là số sai. Chỉ lưu **tháng**; quý và năm cộng từ tháng. Cùng lúc xét chỉ mục toàn văn cho cột tên hàng nếu tìm kiếm cũng chậm.

---

## 4. Đường nạp

### 4.1 Các bước

Chạy ở **tác vụ nền Celery**, không trong lượt gọi API.

1. Người dùng tải lên **một hoặc nhiều tệp** của cùng một lần kết xuất → mỗi tệp lưu nguyên văn vào kho tệp (tầng 1) và sinh **một lô `tab_import_batch`** (`module = CUSTOMS_DECLARATION`, `mode = DRY_RUN`).
   **Lượt chạy thử** đi hết bước 2–4 nhưng **không ghi dòng hàng**, rồi trả về: số dòng · khoảng ngày · số dòng sẽ vá ngày · **số dòng cũ sẽ bị thay** · cảnh báo. Người nạp xem xong bấm Áp dụng → chạy lại với `mode = APPLY` đi đủ bước 2–6.
2. **Kiểm tiêu đề** — khớp đủ 32 cột theo **chữ đã chuẩn hóa** (thường, bỏ dấu, gộp khoảng trắng) chứ không theo vị trí. Tiêu đề gốc có lỗi chính tả (`Tên nuớc xuất xứ` — "nuớc" chứ không phải "nước"); khớp nguyên văn thì một lần GTT02 sửa chính tả là hỏng hết. **Thiếu cột nào là từ chối cả lô**, báo đúng tên cột thiếu.
3. Đọc từng dòng, chuẩn hóa (§4.2, §4.3).
4. Tra hoặc tạo bảng đối tượng (§3.2) theo `(party_type, dedupe_key)` — **một lượt truy vấn cho cả khối**, không truy vấn từng dòng.
5. Ghi dòng hàng bằng **lệnh chèn hàng loạt** theo khối 2.000 dòng — không `db.add` từng dòng (nhanh hơn nhiều, và không kích hoạt nhật ký trước/sau; hai bảng hải quan cũng đã vào `NO_LOG_TABLES`).
6. Xóa dòng của **lô khác** nằm trong khoảng ngày của lô mới → ghi số đã xóa vào `deleted_count` của lô mới → lô chuyển `DONE`.

**Bản cài đặt (bao-CR-470):** xóa dòng cũ trong khoảng ngày + chèn dòng mới nằm trong **MỘT giao dịch** — không có khoảnh khắc nào dữ liệu cũ và mới cùng tồn tại. Với cỡ một lần kết xuất (vài nghìn tới vài chục nghìn dòng) một giao dịch là vừa; khi tệp lên cỡ trăm nghìn dòng mới cần xét chia nhỏ.

### 4.2 ⚠️ Hai cột ngày — một cột phải vá, một cột TUYỆT ĐỐI KHÔNG

**Ngày đăng ký (cột 0) — PHẢI vá.** Cột này lẫn hai kiểu ô:

- **Ô chữ** `DD-MM-YYYY` → đọc thẳng. Đo được: ô chữ **chỉ chứa ngày 13–31**.
- **Ô kiểu ngày của Excel** → **ngày và tháng đã bị hoán đổi**, phải đảo lại. Đo được: ô kiểu ngày suy ra "ngày" **chỉ từ 1–9**.

Nguồn gốc: dữ liệu gốc là chữ `DD-MM-YYYY`; hễ ngày ≤ 12 thì Excel hiểu nhầm thành `MM-DD` rồi tự đổi thành ô ngày, ngày > 12 thì không hiểu được nên để nguyên chữ. 7.651 / 18.243 dòng (42%) dính.

**Bằng chứng luật vá đúng:** sau khi vá, 5 tệp mẫu xếp khít thành 5 khối hai tháng liền nhau, không chồng một ngày nào (§4.4). Vá sai thì các khối xáo lộn vào nhau.

**Ngày hợp đồng (cột 19) — KHÔNG ĐƯỢC vá.** Cột này là ô ngày **thật**, không lẫn kiểu: 10.855 ô có ngày > 12, tức Excel đọc đúng. Ai viết kiểu *"vá mọi cột ngày cho chắc"* sẽ **làm hỏng 39% số ngày hợp đồng đang đúng**. Luật vá phải gắn vào **đúng cột 0**, và phải có bài kiểm chốt điều này.

### 4.3 Các chuẩn hóa khác

- **Mã có dấu `'` đầu** (`'0500590269`, `'38089990`): bóc bỏ — đó là mẹo của Excel để giữ số 0 đầu.
- **Ô số trống** → `NULL`, **không đổi thành 0** (§5).
- **Phương tiện vận chuyển** → tách mã số trước dấu `-` (§3.4).

### 4.4 Khoảng ngày của lô

Mặc định **suy từ dữ liệu** (ngày nhỏ nhất → lớn nhất sau khi vá), **hiện cho người nạp xác nhận** trước khi chốt. Đo trên bộ mẫu:

| Tệp | Từ | Đến | Số dòng |
|---|---|---|---|
| `1.xls` | 02/01/2026 | 28/02/2026 | 3.370 |
| `2.xls` | 01/03/2026 | 30/04/2026 | 4.772 |
| `3.xls` | 01/05/2026 | 30/06/2026 | 4.466 |
| `4.xls` | 01/07/2026 | 31/08/2026 | 4.350 |
| `5.xls` | 03/09/2026 | 17/09/2026 | 1.285 |

GTT02 cắt một lần kết xuất thành từng khối hai tháng. **Một lô nên gồm cả bộ tệp của một lần kết xuất** — nạp lẻ thì dễ quên một tệp, và khoảng trống đó không ai thấy.

---

## 5. Những thứ CỐ Ý không làm

| Không làm | Vì sao |
|---|---|
| **Lưu mỗi dòng Excel thành một khối JSON** | Nghe dễ nhất để "giữ đủ cột", nhưng **tốn chỗ nhất**: tên 32 khóa lặp lại ở mọi dòng, số thành chữ, không lọc hay gom được bằng chỉ mục |
| **Từ điển tên hàng** (có ở bản 1.0) | 83% tên chỉ xuất hiện một lần — không gọn hơn mà còn thêm mã băm và chỉ mục (§2.1) |
| **Bảng tổng hợp theo mặt hàng × tháng** (có ở bản 1.0) | Gọn có 1,2 lần; kỳ gom tính lúc đọc linh hoạt hơn (§3.5) |
| **Lưu riêng bảng quý, bảng năm** | Dữ liệu trùng phải đồng bộ; lệch nhau là hai màn ra hai con số |
| **Đổi ô trống thành 0 cho gọn** | Trống ≠ 0. *Thuế suất XNK* rỗng 15% — rỗng là tờ khai không khai, 0 là thuế suất bằng không |
| **Tự quy đổi sang USD** | Dữ liệu gốc đã có cột giá USD do hải quan quy đổi đúng ngày khai |
| **Quy đổi giữa các đơn vị** | Chỉ `TNE → KGM` là chắc chắn; cái / bộ / đơn vị không quy sang kg được |
| **Tách cơ sở dữ liệu riêng / kho phân tích chuyên dụng** | Quy mô hiện tại không cần (§6) |

---

## 6. Dung lượng — số đã sửa ở bản 1.1

⚠️ **Bản 1.0 ghi "gọn hơn 2,2 lần" là SAI** — con số đó quên cộng phần từ điển tên hàng, mà từ điển lại không tiết kiệm được gì (§2.1). Số đúng:

| Cách lưu | Byte / dòng | So với lưu thẳng chữ |
|---|---|---|
| Lưu thẳng chữ như Excel | ≈ 470 | — |
| **Thiết kế bản 1.1** (kiểu đúng + bảng đối tượng, tên hàng lưu thẳng) | **≈ 395** | gọn hơn **~1,2 lần** |
| Bản 1.1 **+ nén trang InnoDB** | ≈ 200 | gọn hơn **~2,3 lần** |

**Nói thẳng:** cột tên hàng chiếm 187 / ~395 byte mỗi dòng và là **chữ gần như duy nhất** — không mẹo sắp xếp bảng nào làm nó nhỏ đi được. Thứ duy nhất thu nhỏ được chữ duy nhất là **nén**.

**Nén trang là đòn bẩy thật.** Đo bằng cách nén từng khối 16 KB (đúng cỡ trang InnoDB) trên dữ liệu thật: riêng tên hàng gọn **3,1 lần**, cả dòng gọn **3,5 lần**. Trên đĩa thật hệ số thấp hơn vì trang nén phải làm tròn lên theo khối 4 KB của hệ thống tệp — tính thận trọng **khoảng 2 lần**. Cái giá: một ít CPU lúc đọc và ghi.

| Kịch bản | Dòng / năm | Không nén | Có nén trang |
|---|---|---|---|
| **Phạm vi hiện tại** (một chương HS 3808) | ~26.000 | ~10 MB | ~5 MB |
| Mở rộng vài chương hóa chất | ~1 triệu | ~400 MB | ~200 MB |
| Mở rộng rất rộng | ~10 triệu | ~4 GB | ~2 GB |

*(Đã gồm chỉ mục. Bảng đối tượng dưới 1 MB, không đáng kể.)*

**Khi nào bật nén:** ở phạm vi hiện tại **không cần** — 10 MB một năm. Bật khi dữ liệu vượt khoảng 1 triệu dòng. Bật ngay từ đầu cũng được và đỡ một lần dựng lại bảng về sau, **nhưng phải thử trên VPS trước**: nén trang của InnoDB phụ thuộc hệ thống tệp hỗ trợ đục lỗ (*hole punching*); không hỗ trợ thì MySQL chỉ cảnh báo rồi **lặng lẽ không nén**.

---

## 7. Hiển thị đủ 32 cột như Excel

- **Một danh sách cột duy nhất ở backend**: mỗi mục gồm *khóa · tiêu đề Excel · thứ tự*. Danh sách này **vừa là chỗ khớp tiêu đề lúc nạp (§4.1 bước 2), vừa là nguồn dựng cột trên màn hình** — một chỗ khai, hai chỗ dùng, không lệch được.
- Đường API trả dòng đã **nối lại bảng đối tượng**, đủ 32 trường theo đúng thứ tự Excel.
- Cột nào đã chuẩn hóa thì **hiện giá trị đã chuẩn hóa** (ngày đã vá, mã đã bóc `'`, phương tiện hiện nhãn tiếng Việt). Cần xem nguyên văn thì mở tệp gốc ở tầng 1.
- Bảng dùng `DataTable` với **bố cục cột nhớ theo người dùng**; mặc định bật khoảng 10 cột quan trọng (ngày · tên hàng · mã HS · doanh nghiệp · đối tác · đơn giá USD · lượng · đơn vị · xuất xứ · điều kiện giao hàng), 22 cột còn lại bật trong menu *Cột*.

---

## 8. Bài kiểm bắt buộc

| Bài kiểm | Canh cái gì |
|---|---|
| Vá ngày đảo đúng ở cột 0 | Ô kiểu ngày với ngày ≤ 12 bị đảo lại; ô chữ đọc thẳng |
| **Không vá cột 19** | Ngày hợp đồng giữ nguyên — canh đúng cái bẫy §4.2 |
| Bóc dấu `'` | Mã số thuế và mã HS giữ nguyên số 0 đầu |
| Ô trống ra `NULL` | Không thành 0 |
| Bảng đối tượng — trong nước theo mã số thuế | Hai cách viết tên cùng một mã → một dòng |
| Bảng đối tượng — **cùng tên, khác loại** | Một đối tác nước ngoài trùng tên một doanh nghiệp trong nước → **hai dòng**, không gộp nhầm |
| Kỳ gom tháng / quý / năm | Cùng một tập dòng, tổng lượng ba kỳ khớp nhau; giá bình quân là **gia quyền theo lượng**, khớp tính tay |
| Tách theo đơn vị | kg và lít không cộng lẫn |
| Thay lô cùng khoảng ngày | Không nhân đôi dòng; `deleted_count` của lô mới đúng bằng số dòng cũ bị thay |
| Chạy thử `DRY_RUN` | Không ghi dòng hàng nào, nhưng trả đúng số dòng · khoảng ngày · số dòng sẽ bị thay |
| Hoàn tác lô | `REVERTED` xóa hết dòng mang `batch_id` đó, không đụng lô khác |
| Tiêu đề thiếu cột | Từ chối cả lô, báo đúng tên cột |
| Mã phương tiện lạ | Từ chối cả lô, không lưu thành `9` |
| Phạm vi quyền | Khóa `customs_price` khai trong `SCOPE_FIELDS` (canh bởi `test_pham_vi_khai_du_b07.py`) |

Lưu ý: bộ test chạy **SQLite** — không có phân vùng, không ép độ dài `VARCHAR`, và `LIKE` **không** bỏ qua dấu tiếng Việt như collation MySQL. Nên: migration phân vùng có nhánh `if dialect != "mysql": return` như CR-454; **giới hạn độ dài kiểm ở tầng schema** (bài học duoc-CR-316); bài kiểm tìm kiếm dùng từ khóa **không dấu** (tên hoạt chất Latin như *ATRAZINE*), còn việc bỏ qua dấu là tính chất của collation MySQL, không phải mã của mình.

**Hạn chế đã biết của tìm kiếm:** `utf8mb4_unicode_ci` coi **đ** và **d** là hai chữ khác nhau — gõ "dong" không ra "đồng". Ảnh hưởng nhỏ vì thu mua chủ yếu tìm theo tên hoạt chất (chữ Latin).

---

## 9. Phụ thuộc cần thêm

- **`xlrd`** vào `backend/requirements.txt` — tệp GTT02 là `.xls` đời cũ (OLE2/BIFF), `openpyxl` đang có **không đọc được**. Đổi `requirements.txt` nghĩa là **phải dựng lại** `api` + `celery-worker` lúc deploy, không restart suông được.

---

## 10. Phần thêm ở HQ4 – HQ6 (bản 1.5)

Tất cả nằm trong **cùng một migration** `c4d8e2a6f470_cr470_hai_quan_nen_du_lieu.py` với HQ1 (chưa lên môi trường nào ngoài local, nên gộp chứ không đẻ migration thứ hai).

### 10.1 Hai cột suy ra trên `tab_customs_line`

| Cột | Kiểu | Nghĩa |
|---|---|---|
| `active_ingredient` | `VARCHAR(255)`, có chỉ mục | Hoạt chất suy ra từ tên hàng; hỗn hợp nối bằng ` + `, tối đa 3. Rỗng = không nhận ra |
| `formulation` | `VARCHAR(40)` | Hàm lượng / dạng bào chế đầu tiên tách được: `97%`, `80WP`, `250G/L` |

Gắn **lúc nạp** (một lần cho cả lô, có bộ nhớ đệm theo tên hàng) và gắn lại toàn bộ bằng `ingredient.retag_all()` mỗi khi danh mục đổi — script nạp danh mục tự gọi. Ô tìm kiếm khớp **tên hàng HOẶC hoạt chất**.

**Bộ nhận hoạt chất — ba nguồn, dùng lần lượt** (`customs/ingredient.py`):
1. `tab_customs_ingredient_alias` — 99 từ khóa tay (`EMAMECTIN` → `EMAMECTIN BENZOATE`), khớp chuỗi con.
2. **Tên hoạt chất bóc từ danh mục thuốc BVTV** (`derive_aliases`): tách theo `+`, bỏ ngoặc, bỏ hàm lượng, bỏ tên tiếng Việt và tên công ty chép nhầm vào cột hoạt chất; khớp **nguyên từ** trên chuỗi đã chuẩn hóa (gạch nối thành khoảng trắng). Thêm từ đầu của tên nhiều chữ (`KANAMYCIN` → `KANAMYCIN SULFATE`) trừ các từ chung chung (`POTASSIUM`, `ALUMINIUM`, `ACRYLIC`…) — danh sách chặn ở `_GENERIC_HEADS`, mỗi mục trong đó là một lỗi gắn nhầm đã gặp trên dữ liệu thật.
3. Tên thương mại của thuốc BVTV — chỉ khi hai nguồn trên không ra gì, vì tên thương mại hay xuất hiện trong câu *"dùng để sản xuất thuốc X"* của một hoạt chất KHÁC.

Đo trên 18.243 dòng: **51%** nhận ra hoạt chất (trước nguồn 2 là 41%), **93%** tách được hàm lượng.

### 10.1b Chỉ mục thêm sau khi đo trên dev

Migration riêng `d7a3f9c2b481` (sau `c4d8e2a6f470`, vì bản kia đã chạy trên dev): chỉ mục
`ix_customs_line_partner_date (partner_id, reg_date)`. Nút *Các lần nhập khác của đối tác
này* lọc theo `partner_id`; thiếu chỉ mục thì MySQL quét cả bảng qua mọi phân vùng rồi mới
sắp xếp — đo **1,8 giây** trên dev ngày 23/09/2026, có chỉ mục còn **4 ms**. Cùng lúc, đếm
tổng của danh sách đổi sang `COUNT(id)` thẳng thay vì `Query.count()` (hàm này bọc cả câu
SELECT mọi cột thành bảng con).

### 10.2 Bốn bảng danh mục

| Bảng | Số dòng nạp | Khóa / chỉ mục | Ghi chú |
|---|---|---|---|
| `tab_customs_ingredient_alias` | 99 | `keyword` duy nhất | `keyword` → `canonical` |
| `tab_customs_pesticide` | 6.919 | `trade_key` | Danh mục thuốc BVTV được phép: tên thương mại, hoạt chất, nhóm, đơn vị đăng ký |
| `tab_customs_regulation` | 1.060 | `list_code`, `cas_no` | Có `AuditMixin` + màn sửa (khóa `customs_regulation`). `list_code` là SMALLINT theo `RegulationList`: 1–4 = NĐ 24/2026 Phụ lục I–IV, 10 = hoạt chất cấm TT 75/2025, 11 = phải công bố TT 01/2026. `threshold_kg` chỉ Phụ lục IV có |
| `tab_customs_tariff` | 15.115 | `hs_code` | Biểu thuế 2026: `rate_normal` (thông thường), `rate_mfn` (ưu đãi), `rate_vat` (chuỗi, có mã nhiều mức `5/8/10`), `fta_json`, `policy`. Tra mã lá kèm các mã cha 4 · 6 · 8 số |

**Nguồn dữ liệu:** các tệp `.js` của phần mềm ngoài trong `thongtinhaiquan/` — **không chép dữ liệu vào repo**, repo chỉ giữ bộ nạp. Chạy:

```bash
docker compose cp "<thư mục phần mềm ngoài>" api:/tmp/hqapp
docker compose exec -T api python -m scripts.load_customs_catalogs --src /tmp/hqapp
```

Script thay sạch ba bảng alias / thuốc BVTV / biểu thuế, còn danh mục pháp lý thì **chỉ THÊM** dòng chưa có (khóa `list_code + cas_no + name`) để không đè chỗ người dùng đã sửa tay; xong tự gắn lại hoạt chất cho mọi dòng hàng. Bộ đọc `.js` quét từng ký tự (biết nháy, bỏ chú thích `//`, dấu phẩy thừa) — đọc bằng biểu thức chính quy từng vỡ ở tên có ngoặc vuông như `Benzo[b]fluoranthene`.

### 10.3 Thống kê và cảnh báo — tính lúc đọc

Vẫn không có gì tính sẵn (§3.6). `service.compute_stats` / `compare_terms` / `rank_importers` đọc bốn–sáu cột của tập dòng đã lọc rồi gom bằng Python — với vài trăm dòng mỗi lần tra là tức thì. Cảnh báo pháp lý (`match_alerts`) so **từ khóa đang tra** với ba danh sách *cấm · có ngưỡng · phải công bố*; không so tồn kho (P-02 để sau).

### 10.4 Trợ lý AI

`assistant/tools/customs_tool.py`: `customs_price_stats` và `customs_buy_timing`, gọi **đúng** `customs/service.py` của màn hình nên hai bên không bao giờ ra hai con số khác nhau. Độ tin cậy chấm theo số năm + số dòng (`thấp` khi dưới 2 năm), kèm câu `caveat` bắt buộc nhắc lại. Bot Telegram dùng chung bộ tool nên có luôn.

**bao-CR-481** thêm hai tool và mở rộng hai tool cũ (tổng tool trợ lý 39 → 41):

- `customs_price_stats` + `compare_keywords` → `service.compare_terms` (bắt buộc có `keyword`; mã HS chỉ là bộ lọc chung).
- `customs_market` → `service.market_overview`: `rank_importers` + gom đối tác (`partner_id`) và nước xuất xứ trong ĐÚNG một đơn vị, cộng 5 dòng mới nhất từ `list_lines`. Tool bỏ `importer_id` nội bộ khỏi kết quả.
- `customs_legal_check` → `lookup_regulations` (xếp cấm · PL III · PL IV · TT 01 · PL I · PL II) + `lookup_tariff`; luôn kèm câu nhắc «không có mức phạt».
- `customs_buy_timing` + `now` = `service.assess_current_price(stats, today)`: tứ phân vị + xu hướng chỉ trên tháng có ≥ `MIN_LINES_FOR_BEST` dòng (không tháng nào đủ thì dùng tất cả nhưng `reliable=False`); tháng gần nhất ít dòng → `reference_month`; `STALE_DATA_DAYS = 45`. Lý do chỉ dùng tháng đủ dữ liệu: dữ liệu thật 24/09 ATRAZINE 09/2026 chỉ có 1 dòng, tính cả vào thì ra «đang giảm» từ đúng một lô.
