# Kịch bản test phân hệ Văn bản

Bản 1.0 · 22/08/2026 · dùng cho bản chạy ở LOCAL (`frontend-v2`, cổng 8083).

Kịch bản này đi hết một vòng đời văn bản: **soạn → gửi duyệt → ký từng chặng →
ban hành → ai thấy → phiên bản mới**. Trọng tâm là ba thứ hay sai và khó tự phát
hiện: **ai được làm gì**, **ai thấy văn bản sau khi ban hành**, và **phiên bản**.

> ⚠️ Mỗi ca đều có cả **người PHẢI thấy** lẫn **người PHẢI KHÔNG thấy**. Chỉ kiểm
> một chiều thì một lỗi kiểu "chẳng ai thấy gì" vẫn qua được — đúng cái bẫy ghi ở
> §4.6.

---

## 0. Chuẩn bị (làm một lần)

```bash
docker compose up -d
docker compose exec api python -m app.seed                      # dữ liệu nền
docker compose exec api python -m app.seed_kich_ban_test_van_ban  # bộ diễn viên
```

Lệnh thứ hai là **bắt buộc**. Dữ liệu demo gốc không diễn nổi phần phạm vi: mỗi
pháp nhân chỉ có một phòng có người, 4/8 nhân sự DEGO không thuộc phòng nào, và
không phòng nào có từ 2 người trở lên — nên "loại trừ phòng ban" bấm xong không
phân biệt được luật chạy đúng hay vốn dĩ chẳng ai thấy.

**⚠️ Đổi phân quyền xong phải chờ ~60 giây** (hoặc `docker compose restart api`).
Hồ sơ quyền được nhớ trong tiến trình 60 giây (`_PERM_CACHE` ở `core/auth.py`);
seed chạy ở tiến trình khác nên không xóa được cache đó. Không biết điều này thì
sẽ tưởng phân quyền hỏng.

---

## 1. Danh sách tài khoản

Đăng nhập bằng **mã nhân viên**. Mở tab ẩn danh cho mỗi vai để không phải đăng
xuất liên tục — đây là cách chuyển vai nhanh nhất.

### 1.1 Người soạn và văn thư

| Mã đăng nhập | Mật khẩu | Là ai | Làm được gì |
|---|---|---|---|
| `admin` | trong `.env` (`ADMIN_PASSWORD`) | Quản trị viên, DEGO | Mọi thứ. Dùng khi cần dựng nhanh, **không dùng để kiểm phân quyền** |
| `VTIDA` | `VTIDA` | Văn thư pháp nhân IDA | Soạn/sửa/gửi duyệt/ban hành **văn bản của IDA**; chỉ thấy văn bản IDA |
| `VTSAM` | `VTSAM` | Văn thư SAM | như trên, phạm vi SAM |
| `VTABA` | `VTABA` | Văn thư ABA | như trên, phạm vi ABA |
| `VTAGRIPLANT` | `VTAGRIPLANT` | Văn thư AGRIPLANT | như trên, phạm vi AGRIPLANT |

Còn văn thư của 8 pháp nhân con khác, cùng quy ước `VT<mã pháp nhân>`, mật khẩu
bằng chính mã.

### 1.2 Ba luồng duyệt và ai đứng ở đâu

Luồng nào chạy là do **`priority` giảm dần** rồi mới tới điều kiện. Một loại văn
bản khớp nhiều luồng thì luồng `priority` cao thắng:

| Luồng | Ưu tiên | Áp cho loại | Số chặng |
|---|---|---|---|
| **Ban hành văn bản quản trị** | 20 | QC · QDI · QT · CS | 4 (có rẽ nhánh) |
| **Ban hành văn bản hành chính** | 10 | QDI · **TB** | 2 |
| **Ban hành văn bản (mặc định)** | 0 | mọi loại còn lại | 2 |

> QDI khớp **cả hai** luồng đầu — và luồng *quản trị* thắng vì ưu tiên 20 > 10.
> Đây là chỗ dễ tưởng nhầm.

**Luồng hành chính** (dùng cho loại TB ở §3.1–3.3):

| Chặng | Tên | Ai ký |
|---|---|---|
| 1 | Trưởng bộ phận duyệt nội dung | `DEGO0001` |
| 2 | Chánh Văn phòng ký ban hành | `DEMO_MANAGER` |

**Luồng quản trị** (dùng cho loại QDI ở §3.4):

| Chặng | Tên | Ai ký |
|---|---|---|
| 1 | Trưởng bộ phận soạn thảo rà soát | **trưởng phòng của người nộp** — suy ra lúc chạy, không cố định |
| 2 | Pháp chế và Tài chính cùng rà soát | `DEGO0001` **và** `DEMO_STAFF` — hai người |
| 3 | Tổng Giám đốc ký ban hành | `admin` — **chỉ khi mức mật ≥ Mật** |
| 3 | Phó Tổng Giám đốc ký ban hành | `DEMO_MANAGER` — nhánh còn lại |
| 4 | Văn thư vào sổ và phát hành | `DEMO_MANAGER` |

Mật khẩu: `DEGO0001` / `DEMO_STAFF` / `DEMO_MANAGER` đều là **`demo123`**;
`admin` lấy trong `.env` (`ADMIN_PASSWORD`).

> ⚠️ **Chặng 1 của luồng quản trị cần người nộp CÓ PHÒNG BAN.** `admin` và
> `DEGO0001` không thuộc phòng nào, nộp bằng họ thì chặng này không suy ra được
> ai. Muốn chạy luồng quản trị thì nộp bằng một tài khoản có phòng —
> `DEMO_MANAGER_PURCHASE` (Phòng Thu mua) hoặc một tài khoản `TVB_*` sau khi cấp
> thêm quyền soạn.

### 1.3 Người đọc — dùng cho phần phạm vi (§4)

Chín tài khoản, **mật khẩu bằng chính mã**, đều thuộc pháp nhân **DEGO**:

| Phòng | Tài khoản |
|---|---|
| Phòng Nhân sự - Hành chính | `TVB_NS1` · `TVB_NS2` · `TVB_NS3` |
| Phòng Kế toán | `TVB_KT1` · `TVB_KT2` · `TVB_KT3` |
| Phòng Kinh doanh | `TVB_KD1` · `TVB_KD2` · `TVB_KD3` |

**Chín người này cố ý KHÔNG có quyền `document: read`.** Họ không vào được màn
*Văn bản*; họ chỉ thấy văn bản qua **«Áp dụng cho tôi»** và qua đường dẫn trực
tiếp. Cấp quyền đọc cho họ là kịch bản mất ý nghĩa — ai cũng thấy mọi thứ và
không còn phân biệt được phạm vi có chạy hay không.

---

## 2. Ai thấy gì — kiểm trước khi làm gì

Mục này chạy **trước**, vì nếu phân quyền đã sai thì mọi kết quả phía sau không
đọc được.

| # | Việc làm | Kết quả đúng |
|---|---|---|
| 2.1 | `VTIDA` mở **Văn bản** | Chỉ thấy văn bản của **IDA**. Không thấy của SAM, ABA, DEGO |
| 2.2 | `VTIDA` bấm **Tạo văn bản** | Ô *Pháp nhân ban hành* chọn được; các ô bắt buộc (loại, phòng, người chịu trách nhiệm) **có dữ liệu**, không rỗng |
| 2.3 | `VTIDA` mở ô **Vào sổ** | Có mục ngoài *"Không vào sổ"*. Nếu chỉ còn đúng một mục → thiếu quyền `document_book: read` |
| 2.4 | `TVB_NS1` xem thanh bên | Chỉ có *Tổng quan* và *Chờ tôi duyệt*. **Không có mục Văn bản** |
| 2.5 | `TVB_NS1` gõ thẳng `/document/documents` | Trang mở ra nhưng **bảng rỗng** (API trả 403). Chặn thật nằm ở backend, không phải ở việc giấu menu |
| 2.6 | `TVB_NS1` mở **Áp dụng cho tôi** | Vào được. Thấy **11 văn bản của DEGO** đã ban hành — chúng không khai dòng phạm vi nào nên áp cho cả pháp nhân (quy tắc F04) |
| 2.7 | `DEMO_MANAGER` mở **Chờ tôi duyệt** | Vào được; số trên chuông khớp số dòng trong danh sách |

---

## 3. Vòng đời: soạn → duyệt → ban hành

Làm bằng `VTIDA` trừ khi ghi khác.

### 3.1 Soạn — luồng ngắn (2 chặng)

| # | Việc làm | Kết quả đúng |
|---|---|---|
| 3.1.1 | Tạo văn bản, loại **Thông báo (TB)**, pháp nhân **IDA** | Bước 1 qua được. Ô *Số hiệu* ghi "chọn loại và pháp nhân để xem số" — **đây là số xem trước, không phải số thật** |
| 3.1.2 | Sang bước 2 *Phạm vi áp dụng*, **không khai dòng nào** | Cho qua. Không khai = áp cho **toàn bộ pháp nhân ban hành** (quy tắc F04, đổi 19/08/2026) |
| 3.1.3 | Bước 3, để **Mức mật = Nội bộ**, lưu nháp | Vào được màn soạn thảo. Trạng thái **Nháp** |
| 3.1.4 | Gõ nội dung, chờ ~2 giây | Tự lưu. Tab *Phiên bản* có **bản 1.0**, nhãn *Nháp* + *Sửa được* |
| 3.1.5 | Bấm **Gửi duyệt** | Trạng thái → *Đang duyệt*. Tab *Phiên bản*: bản 1.0 đổi sang **Chỉ đọc** |
| 3.1.6 | Thử sửa nội dung lúc này | **Không sửa được** (D-029: đang trình duyệt thì đóng băng, để người duyệt đọc bản nào thì ký đúng bản đó) |

### 3.2 Duyệt

Loại TB chạy **luồng hành chính**: chặng 1 `DEGO0001`, chặng 2 `DEMO_MANAGER`.

| # | Vai | Việc làm | Kết quả đúng |
|---|---|---|---|
| 3.2.1 | `DEGO0001` | Mở **Chờ tôi duyệt** | Thấy phiếu vừa gửi |
| 3.2.2 | `DEMO_MANAGER` | Mở **Chờ tôi duyệt** | **Chưa thấy** — phiếu còn ở chặng 1, chưa tới lượt |
| 3.2.3 | `DEGO0001` | Mở văn bản, tab **Phê duyệt** | Thấy đủ 2 chặng; chặng 1 có huy hiệu **"phiếu đang ở đây"**; có nút *Duyệt / Trả lại* |
| 3.2.4 | `VTIDA` | Mở đúng văn bản đó, tab **Phê duyệt** | Thấy luồng nhưng **không có nút duyệt** — nút chỉ hiện với đúng người đang cầm việc |
| 3.2.5 | `DEGO0001` | Bấm **Trả lại**, ghi lý do | Văn bản về **Nháp**. `VTIDA` sửa tiếp được. Lý do hiện ở dải *Hoạt động* |
| 3.2.6 | `VTIDA` | Gửi duyệt lại | Chạy lại **từ chặng 1** |
| 3.2.7 | `DEGO0001` | Duyệt | Chặng 1 tô xanh *Đã duyệt*; phiếu sang chặng 2 |
| 3.2.8 | `DEMO_MANAGER` | Mở **Chờ tôi duyệt** | **Bây giờ mới thấy** |
| 3.2.9 | — | Xem dải **Hoạt động** | Ghi **"mới nhất trước"**; ô *Bắt đầu* ở dải tóm tắt là mốc **cũ nhất** |

### 3.3 Ban hành và cấp số

| # | Việc làm | Kết quả đúng |
|---|---|---|
| 3.3.1 | Duyệt xong chặng cuối | Trạng thái → **Có hiệu lực**. **Số hiệu thật** được cấp lúc này (loại TB có `number_when = 2`) |
| 3.3.2 | So số hiệu với số xem trước ở 3.1.1 | Có thể khác — số thật cấp trong cùng giao dịch ghi bản ghi, không phải số client đoán |
| 3.3.3 | Tab **Phiên bản** | Bản 1.0: *Đã duyệt* + *Bản đang dùng* + *Chỉ đọc*, có ngày duyệt và tên người duyệt |

### 3.4 Luồng dài — rẽ nhánh theo mức mật

Ca này kiểm điều kiện `secrecy_level ≥ 3` ở chặng 3 của luồng *Ban hành văn bản
quản trị*.

Nộp bằng **`DEMO_MANAGER_PURCHASE`** (`demo123`, Phòng Thu mua) — chặng 1 cần
người nộp có phòng ban, xem cảnh báo ở §1.2.

| # | Việc làm | Kết quả đúng |
|---|---|---|
| 3.4.1 | Tạo văn bản loại **Quy định (QDI)** | Chạy **luồng quản trị** (ưu tiên 20), không phải luồng hành chính — dù QDI khớp cả hai |
| 3.4.2 | Mức mật **Nội bộ**, gửi duyệt, xem tab *Phê duyệt* | Chặng 3 là **Phó Tổng Giám đốc ký ban hành** (`DEMO_MANAGER`) |
| 3.4.3 | Tạo văn bản QDI khác, mức mật **Mật**, gửi duyệt | Chặng 3 đổi thành **Tổng Giám đốc ký ban hành** (`admin`) — đây là rẽ nhánh theo `secrecy_level ≥ 3` |
| 3.4.4 | Chặng 2 của cả hai ca | Có **hai người** (`DEGO0001` và `DEMO_STAFF`), mỗi người một dòng con với trạng thái riêng |
| 3.4.5 | Ca 3.4.3, tab *Thông tin*, ô Mức mật | Có dòng cảnh báo **"Lớp kiểm mức mật CHƯA bật"**. Đúng: mức mật hiện chỉ là nhãn, chưa chặn ai (P5 chưa làm) |
| 3.4.6 | QDI khai `needs_decision` | Không khai quan hệ *Kèm theo → Quyết định* thì **không ban hành được**; tab *Quan hệ* nói rõ còn thiếu gì |

---

## 4. Phạm vi áp dụng — phần dễ sai nhất

Bốn quy tắc (F01–F05, `scope_service.py`):

1. Các dòng **bao gồm** cộng dồn.
2. **Cụ thể hơn thắng**: cá nhân > phòng ban > pháp nhân.
3. **Cùng mức cụ thể thì loại trừ thắng.**
4. **Không khai dòng nào = áp cho toàn bộ pháp nhân ban hành.** Khai **một**
   dòng bất kỳ là tắt quy tắc 4.

Mỗi ca dưới đây: soạn bằng `admin` (pháp nhân **DEGO**), **loại Thông báo (TB)**
cho luồng duyệt ngắn 2 chặng, ban hành, rồi đăng nhập từng người đọc mở
**«Áp dụng cho tôi»**.

Cách nhanh: làm **một** văn bản rồi sửa lại thẻ *Phạm vi áp dụng* cho từng ca,
không phải tạo lại từ đầu mỗi lần.

> ⚠️ **«Áp dụng cho tôi» của mấy tài khoản `TVB_*` KHÔNG rỗng lúc bắt đầu** — có
> sẵn 11 văn bản DEGO từ dữ liệu nền (chúng không khai phạm vi nên áp cho cả
> pháp nhân). Nên mỗi ca phải **tìm đúng văn bản mình vừa tạo** theo số hiệu,
> đừng đọc theo kiểu "danh sách có/không có gì".

### 4.1 Không khai gì → cả pháp nhân thấy

| Kiểm | Kết quả đúng |
|---|---|
| `TVB_NS1`, `TVB_KT1`, `TVB_KD1` | **Đều thấy** |
| `VTIDA` (pháp nhân IDA) | **Không thấy** — mặc định dừng đúng ở pháp nhân ban hành |

### 4.2 Loại trừ vài cá nhân

Khai: *bao gồm* pháp nhân DEGO; *loại trừ* cá nhân `TVB_NS2`, `TVB_KT3`.

| Kiểm | Kết quả đúng |
|---|---|
| `TVB_NS1`, `TVB_NS3`, `TVB_KT1`, `TVB_KD1` | **Thấy** |
| `TVB_NS2`, `TVB_KT3` | **Không thấy** |

### 4.3 Loại trừ cả một phòng ban

Khai: *bao gồm* pháp nhân DEGO; *loại trừ* phòng **Kế toán**.

| Kiểm | Kết quả đúng |
|---|---|
| `TVB_NS1`, `TVB_NS2`, `TVB_KD1` | **Thấy** |
| `TVB_KT1`, `TVB_KT2`, `TVB_KT3` | **Không thấy** — cả ba, không sót ai |

### 4.4 Loại trừ phòng nhưng CHỪA một người trong phòng đó

Khai: *bao gồm* pháp nhân DEGO; *loại trừ* phòng **Kế toán**; *bao gồm* cá nhân
`TVB_KT2`.

| Kiểm | Kết quả đúng |
|---|---|
| `TVB_KT2` | **Thấy** — quy tắc 2: cá nhân cụ thể hơn phòng ban nên thắng |
| `TVB_KT1`, `TVB_KT3` | **Không thấy** |
| `TVB_NS1`, `TVB_KD1` | **Thấy** |

Đây là ca quan trọng nhất của mục 4. Sai thứ tự ưu tiên là hoặc `TVB_KT2` không
thấy (loại trừ đè nhầm), hoặc cả phòng Kế toán thấy (bao gồm đè nhầm).

### 4.5 Chỉ khai dòng loại trừ — cái bẫy

Khai **duy nhất** một dòng: *loại trừ* phòng Kế toán. Không khai dòng bao gồm nào.

| Kiểm | Kết quả đúng |
|---|---|
| Màn khai phạm vi | Hiện **băng đỏ**: *"Đang chỉ có dòng loại trừ — ban hành xong văn bản sẽ không tới một ai."* |
| Mọi tài khoản `TVB_*` | **Không ai thấy** |

Đúng như vậy: khai một dòng là tắt quy tắc 4, mà dòng duy nhất lại là loại trừ
nên tập bao gồm rỗng. Backend **cố ý không chặn** — giao diện chỉ cảnh báo.

### 4.6 Kiểm chéo bốn nơi phải khớp nhau

Với **cùng một văn bản**, bốn chỗ sau phải cho **cùng một danh sách người**:

1. **«Áp dụng cho tôi»** của từng người;
2. mở **chi tiết văn bản** bằng đường dẫn trực tiếp (`/document/documents/<id>`);
3. thẻ **Phạm vi áp dụng** trên trang chi tiết (danh sách nó liệt kê);
4. ai **nhận chuông / email** lúc ban hành.

Lệch một trong bốn là lỗi thật. Hay gặp nhất: nhận được thông báo, bấm vào thì
**404** — nghĩa là (4) rộng hơn (2).

---

## 5. Bản riêng cho pháp nhân con (clone)

| # | Việc làm | Kết quả đúng |
|---|---|---|
| 5.1 | `admin` tạo văn bản của **DEGO**, bước 2 chọn cơ chế **tách bản riêng**, chọn IDA + SAM + ABA | Ban hành xong sinh **một bản nháp ở mỗi pháp nhân** đã chọn |
| 5.2 | `VTIDA` mở **Văn bản** | Thấy **bản riêng của IDA**, trạng thái *Nháp* |
| 5.3 | `VTSAM` mở danh sách | Thấy bản của SAM, **không thấy** bản của IDA |
| 5.4 | Trên bản gốc, tab **Quan hệ** → *Cây tài liệu* | Nhóm *Bản riêng ở pháp nhân con* liệt kê **3 dòng phân biệt được bằng TÊN PHÁP NHÂN** — chúng chép nguyên tiêu đề gốc và thường chưa cấp số |
| 5.5 | `VTIDA` sửa bản riêng, gửi duyệt, ban hành | Bản riêng có **số hiệu riêng của IDA**, người ký riêng, hiệu lực riêng |
| 5.6 | Bản gốc lên phiên bản mới (§6) | Bản riêng bị đánh dấu **"chưa theo bản mới"** trên cây |

---

## 6. Phiên bản

| # | Việc làm | Kết quả đúng |
|---|---|---|
| 6.1 | Văn bản *Có hiệu lực*, tab **Phiên bản** | Nút **Mở phiên bản mới** hiện ra |
| 6.2 | Chọn **Sửa lớn** | Dòng chữ ghi **"bản mới sẽ là 2.0"** — tính từ bản đang dùng, không ghi cứng |
| 6.3 | Đổi sang **Sửa nhỏ** | Đổi thành **"bản mới sẽ là 1.1"** |
| 6.4 | Bỏ trống ô *Sửa gì* | Nút **Mở phiên bản** không bấm được |
| 6.5 | Khai *Sửa gì* + *Vì sao sửa*, mở bản 2.0 | Danh sách có **2 dòng**. Bản 1.0 vẫn còn, không bị xóa |
| 6.6 | Đọc dòng 2.0 | Có huy hiệu **Sửa lớn**, câu *"Vì sao sửa: …"*, và chip **"Người đã đọc bản cũ phải xác nhận đọc lại"** |
| 6.7 | Trạng thái của **văn bản** lúc này | Vẫn **Có hiệu lực** — bản 2.0 còn nháp thì cả công ty vẫn đọc bản 1.0 |
| 6.8 | Mở lại bản **1.0** | **Chỉ đọc**. Sửa bản đã duyệt = mở phiên bản mới, không sửa đè |
| 6.9 | Người thứ hai (`admin`) bấm *Mở phiên bản mới* | **Bị chặn**, nêu đích danh **ai đang giữ** bản nháp và **mở từ lúc nào**, kèm nút sang xem bản đó |
| 6.10 | Ban hành bản 2.0 | Bản 1.0 chuyển **Đã thay thế**; bản 2.0 thành *Bản đang dùng* |
| 6.11 | Bấm dòng 1.0 | Vẫn mở ra đọc được — người còn cầm giấy tờ theo bản cũ phải tra ra được (C18) |

---

## 7. Bản trích nội bộ

| # | Việc làm | Kết quả đúng |
|---|---|---|
| 7.1 | Văn bản **chưa ban hành** → menu **Tệp** | **Không có** mục *Tạo bản trích* — trích từ bản chưa duyệt là chia ra ngoài thứ chưa ai duyệt |
| 7.2 | Văn bản đã ban hành → *Tạo bản trích* | Ô *Phần nội dung được trích* là **ô soạn thảo có thanh công cụ**, không phải ô chữ trơn |
| 7.3 | Dán nội dung có **in đậm + bảng** từ bản gốc | Giữ nguyên định dạng và bảng |
| 7.4 | Xóa sạch nội dung | Nút *Tạo bản trích* **tắt lại** |
| 7.5 | Ô *Mức mật của bản trích* | Chỉ liệt kê mức **≤ mức của bản gốc** |
| 7.6 | Bản gốc lên phiên bản mới | Bản trích bị đánh dấu **cần rà lại** |

---

## 8. Danh mục Mức mật / Độ khẩn

| # | Việc làm | Kết quả đúng |
|---|---|---|
| 8.1 | *Thiết lập văn bản › Mức mật / khẩn* | 7 dòng: 4 Mức mật + 3 Độ khẩn |
| 8.2 | **Thêm mới**, bậc **7**, mã `TOIMAT` | Tạo được. Ô chọn Mức mật lúc tạo văn bản có thêm mục này ngay |
| 8.3 | Mở dòng vừa tạo để sửa | Ô **Thang** và **Bậc** ở dạng chỉ xem, kèm câu giải thích vì sao khóa |
| 8.4 | Đổi **tên** một bậc rồi xuất Excel danh sách văn bản | Cột *Mức mật* in **tên mới** |
| 8.5 | Xóa bậc **Mật** | **Bị chặn**, nêu đích danh: *"3 văn bản đang ở bậc này; 1 loại văn bản đang lấy làm mức mật mặc định; điều kiện phê duyệt đang trỏ tới «Tổng Giám đốc ký ban hành»"* |
| 8.6 | Xóa bậc vừa tạo ở 8.2 (chưa ai dùng) | Xóa được |
| 8.7 | Bỏ tick **Đang dùng** của một bậc | Không còn chọn được cho văn bản mới; văn bản cũ mang bậc đó **vẫn hiện đúng tên** |

---

## 9. Dọn dẹp sau khi test

```bash
docker compose exec api python -m app.seed_kich_ban_test_van_ban   # đặt lại 9 tài khoản
```

Văn bản tạo ra trong lúc thử thì xóa tay trên giao diện, hoặc dựng lại CSDL nếu
muốn sạch hẳn.

---

## Còn treo

1. **Lớp kiểm mức mật (P5) chưa có.** Mọi ca ở §3.4 chỉ kiểm được phần *rẽ nhánh
   luồng duyệt*, không kiểm được "người không đủ mức thì không đọc được" — vì
   chưa có gì chặn. Câu **B3** (*dùng mấy mức mật, ai được cấp mức 3–4*) vẫn treo
   `[CHẶN]` ở `00-danh-gia-va-cau-hoi.md`.
2. **`include_children` là phép xấp xỉ.** "Gồm đơn vị con" hiện hiểu là *mọi pháp
   nhân có `level` lớn hơn* vì `tab_company` không có cột cha. Đúng với cây một
   tầng đang có, sai ngay khi có tầng thứ ba thuộc hai nhánh khác nhau — nên
   §4 cố ý không có ca nào dùng tùy chọn này.
3. **Chưa có ca nào cho email thật.** §4.6 mục (4) hiện chỉ kiểm được chuông
   trong ứng dụng.
