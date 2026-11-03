# Kịch bản demo — Phân hệ Văn thư

**Ngày:** 20/08/2026 · **Thời lượng:** 20–25 phút · **Trọng tâm:** ban hành một văn bản của Tập đoàn xuống 12 pháp nhân con

---

## 0. Chuẩn bị (làm trước 10 phút)

| Việc | Cách làm |
|---|---|
| Bật hệ thống | `docker compose up -d` |
| Mở giao diện | http://localhost:8083 (bản Docker) — nếu chạy Vite tay thì http://localhost:5174 |
| Kiểm nhanh | Đăng nhập `DEGO0001` / `admin`, vào **Văn bản** thấy 16 văn bản là ổn |

**Nút đổi tài khoản nhanh** nằm trên thanh trên, cạnh chuông thông báo — biểu tượng nhóm người, có chấm vàng và nhãn `DEV`. Cả buổi demo chỉ cần bấm vào đó để đổi vai, **không phải đăng xuất lần nào**.

> Nút này chỉ có ở bản chạy máy lập trình. Bản thật không có — đã kiểm bằng cách quét toàn bộ tệp build, không mật khẩu nào lọt ra.

**Ba vai sẽ dùng:**

| Vai | Tài khoản | Mật khẩu | Dùng để |
|---|---|---|---|
| Tập đoàn | `DEGO0001` | `admin` | Soạn và ban hành văn bản gốc |
| Người duyệt | `DEMO_MANAGER` | `demo123` | Ký duyệt |
| Pháp nhân con | `VTSAM` | `VTSAM` | Nhận và ban hành bản riêng của SAM |

Mười hai pháp nhân con đều có văn thư riêng, mật khẩu **chính là mã tài khoản**: `VTSAM` · `VTAGRIPLANT` · `VTICARE` · `VTIDA` · `VTABA` · `VTNNABA` · `VTNNDEGO` · `VTN2SBIO` · `VTBAMBOO` · `VTDRXANH` · `VTHKDDRXANH` · `VTDEGOHOLDING`.

---

## 1. Mở đầu — nêu vấn đề trước khi khoe tính năng (2 phút)

> "Tập đoàn có 13 pháp nhân. Ra một quy chế thì mỗi công ty con phải có bản của riêng mình — **số hiệu riêng, người ký riêng, ngày hiệu lực riêng** — vì đó là pháp nhân độc lập.
>
> Cách làm cũ: gửi file Word, mỗi nơi tự sửa. Sáu tháng sau có 12 bản khác nhau và **không ai biết bản nào đúng**."

Đó là câu hỏi cả buổi demo trả lời.

---

## 2. Kịch bản chính — ban hành xuống pháp nhân con (12 phút)

### 2.1 Xem văn bản gốc đã ban hành

Vai **`DEGO0001`** → **Văn bản** → mở **`01/2026/TB-DEGO` — Thông báo nghỉ lễ 02/09**.

Chỉ vào dải tiêu đề: số hiệu, loại, phiên bản, trạng thái **Có hiệu lực**.

> "Số hiệu do hệ thống cấp, không ai gõ tay. Cấp rồi là vĩnh viễn."

### 2.2 Thẻ theo dõi — điểm nhấn mạnh nhất

Mở tab **Quan hệ**, kéo xuống thẻ **«Bản clone ở pháp nhân con»**.

Ở đây có sẵn **12 dòng** — mỗi pháp nhân một dòng, kèm số hiệu, trạng thái, và cột theo dõi.

> "Đây là câu trả lời cho *'12 công ty con đang ở phiên bản nào của quy chế này'* — trước đây phải đi hỏi từng nơi."

Chỉ rõ ba cột:
- **Số hiệu** — nơi nào đã ban hành thì có số của chính nó, nơi chưa thì ghi *chưa cấp số*
- **Trạng thái** — Nháp / Đang duyệt / Có hiệu lực
- **Lệch bản** — bản gốc lên phiên bản mới mà nơi đó chưa rà thì hiện cảnh báo

### 2.3 Đổi vai sang pháp nhân con

Bấm nút đổi tài khoản → nhóm **«Pháp nhân con»** → **Văn thư SAM**.

Trang giữ nguyên, chỉ đổi người đăng nhập.

Vào **Văn bản** — danh sách **chỉ còn văn bản của SAM**.

> "Mỗi pháp nhân chỉ thấy văn bản của mình. Đây là phạm vi dữ liệu, không phải lọc giao diện — gọi thẳng API cũng không lấy được của nơi khác."

### 2.4 Nhận việc qua thông báo

Bấm **chuông** — có thư **«Bản nháp cần xử lý»**.

Bấm vào thư → mở thẳng bản nháp của SAM.

> "Pháp nhân con không phải đi tìm. Ban hành xong là bản nháp nằm sẵn ở đó và có thư báo."

### 2.5 Sửa cho đúng công ty mình

Trong trình soạn thảo, sửa vài chữ cho ra chất SAM — ví dụ thêm *"Áp dụng tại Công ty SAM"*.

Nhân tiện khoe trình soạn thảo (chọn 2–3 thứ, đừng tham):
- **Giãn dòng** — bôi đen, chọn nấc 1,5 → giãn ra thấy ngay
- **Đầu trang / chân trang** — menu **Tệp ▾**
- **Mục lục tài liệu** bên trái tự dựng theo tiêu đề

Bấm **Lưu nội dung**.

### 2.6 Gửi duyệt

Bấm **Gửi duyệt** → băng hiện: *"Đang chạy luồng «Ban hành văn bản» — bước 1 · Trưởng bộ phận duyệt"*, và *"Chờ … duyệt. Bạn không phải làm gì."*

> "Văn bản khóa lại ngay lúc này. Người duyệt phải ký đúng bản họ đọc — không ai sửa được dưới tay họ."

Thử bấm vào tab Soạn thảo cho khách thấy nội dung **đã khóa**.

### 2.7 Đổi vai sang người duyệt

Đổi tài khoản → **Trưởng bộ phận**.

Băng trên văn bản đổi câu: **«Đang chờ bạn duyệt. Mở «Việc của tôi» để xử lý.»**

> "Cùng một màn hình, hai người đọc ra hai câu khác nhau."

Bấm link → màn **Việc của tôi** → thấy dòng của SAM, cột **«Văn thư SAM trình»**.

Bấm mở → **Duyệt phiếu**.

### 2.8 Chốt hạ

Quay lại văn bản: SAM giờ có số riêng — dạng **`…/QĐ-SAM`**, trạng thái **Có hiệu lực**.

Đổi vai về **`DEGO0001`**, mở lại thẻ theo dõi ở văn bản gốc: dòng SAM chuyển sang **«Đã ban hành»** kèm số hiệu.

> "Một văn bản của Tập đoàn, 12 bản riêng ở 12 pháp nhân, mỗi bản có số hiệu và người ký của chính nơi đó — mà Tập đoàn vẫn nhìn thấy toàn cảnh trên một màn hình."

---

## 3. Nếu còn giờ (mỗi mục 2 phút, chọn theo khách)

| Mục | Đường đi | Câu chốt |
|---|---|---|
| **Nhập tệp Word/PDF** | Trong văn bản → **Nhập tệp** | "Tài liệu cũ đưa lên là dùng được ngay, giữ nguyên định dạng, bảng biểu, ảnh." |
| **In và xuất** | Menu **Tệp ▾** → In / Xuất Word | "Lề theo Nghị định 30, in ra đúng khổ A4 như bản giấy." |
| **Vòng đời phiên bản** | Mở `DEGO-QC-001` → tab **Phiên bản** | "Bản cũ không mất, tra lại được bất cứ lúc nào." |
| **Quan hệ văn bản** | `01/2024/QĐ-DEGO` (đã thay thế) | "Quyết định mới ban hành là quyết định cũ tự chuyển sang *bị thay thế*." |
| **Bộ lọc nâng cao** | Danh sách → **Bộ lọc** | 17 trường lọc, lọc ở máy chủ nên không tải hết dữ liệu về máy. |
| **Sổ văn bản** | Menu trái → **Sổ văn bản** | Số thứ tự trong sổ, tra theo quyển như sổ giấy. |

---

## 4. Đừng bấm vào (chỗ còn dở)

| Chỗ | Vì sao |
|---|---|
| **Tổng quan Tài chính**, **Tổng quan Kho** | Còn là trang trắng |
| **Yêu cầu thanh toán** | Chưa dựng ở bản mới |
| Cột tick chọn ở màn **Công nợ** | Chưa có (chờ màn Yêu cầu thanh toán) |
| Tài khoản `TESTMEDEGO`, `TESTCONAGRI` | Chỉ xem được, không sửa — dùng nhóm `VT…` thay thế |
| Ô chọn pháp nhân có **hai dòng "CÔNG TY TNHH DEGO HOLDING"** | Hai pháp nhân trùng tên trong dữ liệu, dễ chọn nhầm — nếu khách hỏi thì nói thẳng là dữ liệu cần gộp |

---

## 5. Câu hỏi khó — trả lời sẵn

**"Ai duyệt văn bản của công ty con?"**
Hiện luồng giao cho trưởng bộ phận của người trình. Trong dữ liệu demo, các văn thư con đang gắn chung một phòng nên đều ra Trưởng bộ phận bên Tập đoàn. **Thực tế triển khai thì khai nhân sự và trưởng phòng riêng cho từng pháp nhân, luồng sẽ tự đi đúng người.** Nói thẳng, đừng vòng.

**"Lỡ ban hành nhầm thì sao?"**
Không xóa được văn bản đã cấp số — số đã vào sổ. Cách đúng là **Bãi bỏ**, có ghi lý do, và văn bản vẫn nằm trong sổ để tra.

**"Bản gốc sửa thì 12 bản con có tự cập nhật không?"**
**Không, cố ý.** Hệ thống chỉ **đánh dấu «cần rà lại»** và gửi thông báo cho từng nơi. Sửa nội dung của pháp nhân khác là làm thay việc của người chịu trách nhiệm ở đó. Rà xong họ bấm **«Đã rà xong»** kèm kết luận, ghi vào nhật ký.

**"Có chặn được người không phận sự xem không?"**
Có, hai tầng: quyền theo chức năng, và **phạm vi dữ liệu** theo pháp nhân/phòng ban/cá nhân. Demo được ngay bằng cách đổi sang `VTSAM` — danh sách chỉ còn văn bản của SAM.

**"Nhập file Word có giữ được định dạng không?"**
Giữ phông, cỡ chữ, màu, căn lề, thụt đầu dòng, bảng, ảnh, danh sách. Giãn dòng cũng giữ. Có báo cáo đối chiếu sau khi nhập để biết chỗ nào chuyển không trọn.

---

## 6. Mạch rút gọn (nếu chỉ có 5 phút)

1. Mở `01/2026/TB-DEGO` → tab **Quan hệ** → thẻ 12 bản clone
2. Đổi vai sang **Văn thư SAM** → danh sách chỉ còn của SAM
3. Bấm chuông → mở bản nháp → **Gửi duyệt**
4. Đổi vai **Trưởng bộ phận** → **Việc của tôi** → **Duyệt phiếu**
5. Quay về thẻ theo dõi: SAM đã có số riêng

---

## Còn chưa chốt

- **Người duyệt của pháp nhân con** vẫn là trưởng bộ phận bên Tập đoàn (mục 5). Muốn đúng thì cần khai nhân sự + trưởng phòng cho từng pháp nhân con — chưa làm.
- **Hai pháp nhân trùng tên** "CÔNG TY TNHH DEGO HOLDING" (mã `DEGO` và `DEGOHOLDING`) — cần gộp hoặc đổi tên một cái.
- **Văn bản nhập từ Word hiển thị chật hơn bản gốc chừng 15%** sau khi đổi quy tắc giãn dòng chiều nay. Nếu khách để ý và không chịu thì đổi lại được.
