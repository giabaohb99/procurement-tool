# Văn thư — Quản lý văn bản

Tài liệu mô tả phân hệ **Văn thư** (`/document`): soạn thảo, phê duyệt, ban hành, đánh số, phân phối và theo dõi vòng đời của văn bản nội bộ.

Khác mọi phân hệ còn lại trong tài liệu này ở một điểm: **phân hệ này chỉ có trên `frontend-v2`** (cổng 8083), không có bản trên `frontend/` đang đóng băng.

> **Phạm vi bản 1.** Chỉ làm **văn bản nội bộ do chính tập đoàn ban hành** (`origin = 1`). Hai nhánh còn lại — văn bản pháp luật ngoài (`origin = 2`) và văn bản đến (`origin = 3`) — đã khai sẵn cột nhưng **chưa có màn hình nào sinh ra chúng**.

---

## 1. Bản đồ màn hình

| Đường dẫn | Màn hình | Nội dung |
|---|---|---|
| `/document` | Tổng quan | 5 thẻ KPI, biểu đồ ban hành 12 tháng, cơ cấu theo loại, ma trận ưu tiên, việc cần xử lý |
| `/document/documents` | Danh sách văn bản | Bảng chính, tìm + lọc + phân trang **ở máy chủ**, bung nhánh bản riêng |
| `/document/documents/new` | Tạo văn bản | Form 3 bước |
| `/document/documents/:id` | Chi tiết văn bản | 5 tab: Soạn thảo · Thông tin · Phiên bản · Quan hệ · Phê duyệt |
| `/print/document/:id` | Bản in / Xuất PDF | Ngoài khung phân hệ, không menu |
| `/document/pending-approval` | Chờ tôi duyệt | Văn bản đang chờ **chính tôi** ký (có tìm + lọc) và khối **Đã duyệt gần đây**; bấm dòng là mở văn bản ra duyệt tại đó |
| `/document/applied-to-me` | Văn bản áp dụng cho tôi | Văn bản mà **chính tôi** phải làm theo |
| `/document/books` · `/books/:id` | Sổ văn bản | 3 tab theo chiều (đến · đi · nội bộ), bộ đếm theo năm |
| `/document/numbering-rules` · `/:id` | Quy tắc đánh số | 3 tab theo chiều |
| `/document/link-rules` · `/:id` | Quy tắc quan hệ | Loại nào được nối với loại nào |
| `/document/settings?tab=types` | Loại văn bản | Danh mục loại |
| `/document/settings?tab=templates` | Thư viện văn bản mẫu | Khung trắng để bắt đầu soạn |
| `/document/settings?tab=security-levels` | Mức mật / độ khẩn | **Chỉ đọc** — thang cố định trong mã |
| `/document/settings?tab=partners` | Đơn vị gửi nhận | Đối tác, cơ quan nhà nước, khách hàng… |
| `/system/mailboxes` | **Hộp thư gửi** | Ngoài phân hệ (Quản trị). Địa chỉ đứng tên gửi thông báo ban hành — xem §14.3 |

---

## 2. Vòng đời văn bản

### 2.1 Mười một trạng thái

| # | Trạng thái | Nghĩa |
|---|---|---|
| 1 | **Nháp** | Đang soạn, sửa thoải mái, xóa được |
| 2 | **Đang duyệt** | Đã gửi đi, **đóng băng toàn bộ** |
| 3 | **Đã duyệt** | **Đã ban hành xong**, có số hiệu, chỉ chưa tới ngày hiệu lực |
| 4 | **Có hiệu lực** | Đang áp dụng |
| 5 | **Đã thay thế** | Có văn bản mới thay |
| 6 | **Hết hiệu lực** | Quá ngày hết hạn, hoặc cha bị bãi bỏ kéo theo |
| 7 | **Bãi bỏ** | Thu hồi bằng quyết định |
| 8 | **Lưu trữ** | Đóng hồ sơ |
| 9 | **Trả về** | Người duyệt trả lại — **còn đường**: sửa rồi gửi duyệt lại |
| 10 | **Đã từ chối** | Hết đường, khóa sửa; làm lại thì *Sao chép* ra bản mới |
| 11 | **Chờ ban hành** | Đã ký đủ, **chưa cấp số**, đang chờ NGƯỜI SOẠN THẢO bấm *Ban hành* |

Trạng thái **3 và 4** gọi chung là *còn sống* — chỉ văn bản còn sống mới vào phạm vi áp dụng, mới clone được, mới tạo bản trích được.

⚠️ **Đừng nhầm 3 với 11.** Cả hai đều "đã ký xong" nhưng chờ hai thứ khác hẳn nhau:
*Đã duyệt* là **đã ban hành rồi**, có số hiệu, không ai phải làm gì nữa — chỉ chờ tới
ngày. *Chờ ban hành* là **chưa ban hành**: chưa số hiệu, chưa khóa phiên bản, và đang
chờ một con người bấm nút. Gộp hai cái là màn danh sách không tách được "việc của tôi"
khỏi "cứ để đó tới ngày".

Trạng thái 11 chỉ xuất hiện ở loại văn bản khai **«Chờ người soạn ban hành»** — xem §14.2.

### 2.2 Đường đi thường gặp

```
Tạo (Nháp)
  → Gửi duyệt (Đang duyệt)   ← khóa nội dung + khóa cả bộ trường chung
      ├─ Trả lại  → về Nháp, sửa tiếp
      ├─ Rút phiếu → về Nháp, sửa tiếp
      ├─ Từ chối  → Đã từ chối (khóa hẳn, làm lại thì Sao chép)
      └─ Duyệt → tùy cờ của LOẠI văn bản:
           ├─ loại tự ban hành (mặc định)  → cấp số hiệu → khóa phiên bản
           │        ├─ hiệu lực hôm nay → Có hiệu lực + chạy tác động dây chuyền
           │        └─ hiệu lực sau     → Đã duyệt, chờ tới ngày mới chạy tác động
           └─ loại «Chờ người soạn ban hành» → Chờ ban hành
                    └─ người soạn bấm Ban hành (+ chọn hộp thư) → như nhánh trên
```

Về sau: **Bãi bỏ** (giữ nguyên số hiệu trong sổ) hoặc **mở phiên bản mới** để sửa nội dung.

### 2.3 Luật cứng của vòng đời

- **Xóa được** chỉ khi còn *Nháp* **và** chưa cấp số. Đã có số thì chỉ còn đường **bãi bỏ** — số đã vào sổ không rút lại được.
- **Đang duyệt thì không sửa được gì**: nội dung, tiêu đề, mức mật, lề trang, đính kèm — tất cả trả lỗi 409. Người duyệt phải ký đúng bản họ đọc. Muốn sửa: rút phiếu hoặc chờ trả lại.
- **Gửi duyệt** đòi: có bản nháp đang mở · nội dung không rỗng · từ phiên bản thứ hai trở đi bắt buộc khai "sửa gì" · đủ quan hệ bắt buộc của loại.
- **Đã cấp số thì không đổi được loại văn bản và pháp nhân ban hành** — hai thứ đó nằm trong chính chuỗi số hiệu đã phát ra ngoài.
- Từ **phiên bản thứ hai trở đi**, gửi duyệt/trả lại **không đụng trạng thái văn bản**: quy chế lên bản 2.0 thì bản 1.0 **vẫn có hiệu lực** cho tới lúc bản mới được ban hành. Không có khoảng trống pháp lý.

---

## 3. Tạo văn bản

Ba bước, dữ liệu cả ba bước giữ nguyên khi chuyển qua lại.

**Bước 1 — Thông tin chính.** Bắt buộc: loại văn bản, pháp nhân ban hành, **phòng chủ trì**, trích yếu (tiêu đề), người chịu trách nhiệm. Trong bước này còn có:
- **Chọn văn bản mẫu** — lọc theo loại đang chọn; nội dung mẫu được **chép** vào phiên bản 1.0 (không giữ liên kết sống, sửa mẫu về sau không ảnh hưởng văn bản đã tạo).
- **Xem trước số hiệu** — cho biết số sẽ cấp; đây chỉ là xem trước, **không chiếm số**, và có thể lệch nếu có người được cấp số xen vào.
- **Gợi ý văn bản trùng** — liệt kê văn bản cùng loại, cùng phòng, còn hiệu lực. Chỉ nhắc với nhóm quản trị (quy chế, quy định, quy trình…), không làm phiền công văn/thông báo.
- **Chia quyền truy cập** ngay tại đây (không tách thành bước riêng).

**Bước 2 — Phạm vi áp dụng.** Khai ai phải làm theo (xem mục 7). Nếu phạm vi có pháp nhân khác nơi ban hành, thẻ **"Bản clone ở pháp nhân con"** tự hiện.

**Bước 3 — Thông tin bổ sung.** Mức mật, độ khẩn, người ký, số hiệu cũ của bản giấy, **nơi lưu trữ cứng**, ngày hiệu lực / hết hiệu lực, từ khóa, trích yếu.

**Nơi lưu trữ cứng** (CR-112) trả lời câu "bản giấy có chữ ký tươi đang nằm ở đâu" — ví dụ `Tủ A2 · Kệ 3 · Bìa 12`. Là **ô chữ tự do có gợi ý**, không phải danh mục: mỗi pháp nhân sắp kho một kiểu, ép vào một bảng danh mục là đẻ thêm màn khai báo không ai duy trì. Gõ vài chữ là hiện các chỗ người khác đã dùng, nhờ đó không có "Tủ A2" và "tu a2" nằm cạnh nhau. Ô tìm nhanh, bộ lọc nâng cao và bản xuất Excel đều có cột này — đó chính là lý do nó tồn tại (đi tìm lại hồ sơ giấy).

**Kiểm tra tiên quyết.** Loại nào khai "phải có văn bản cha" mà trong kho chưa có cái nào thì lúc bấm Tạo sẽ hiện hộp liệt kê thứ còn thiếu — **chỉ cảnh báo, không chặn** (chọn "Vẫn tạo văn bản" là đi tiếp). Cổng chặn thật nằm ở bước **gửi duyệt**.

Tạo xong, hệ ghi tuần tự quyền → phạm vi → kế hoạch clone. Phần nào hỏng thì báo rõ tab để khai lại, nhưng vẫn mở trang chi tiết chứ không vứt hết công nhập.

---

## 4. Soạn thảo

### 4.1 Trang giấy

Trình soạn thảo là **tờ A4 trắng trên nền xám**, tự chia trang khi nội dung tràn — soạn thẳng trên hệ thống thay vì làm ở Word rồi tải tệp lên.

Thể thức mặc định theo **Nghị định 30/2020 điều 8**: khổ A4, chữ **Times New Roman 14pt**, giãn dòng đơn kiểu Word, lề trên/dưới 20mm, **lề trái 30mm**, lề phải 20mm.

**Tự lưu** sau 1,5 giây ngừng gõ. Trạng thái hiện ngay cạnh tiêu đề: *Đang lưu… / Chưa lưu / Đã lưu lúc HH:mm*.

### 4.2 Thanh công cụ

| Nhóm | Có gì |
|---|---|
| Mục lục | Bật/tắt cột mục lục bên trái |
| Lịch sử | Hoàn tác (Ctrl+Z) · Làm lại (Ctrl+Y) |
| Bốn ô chọn | **Mức phóng** 50–200% · **Kiểu đoạn** (Đoạn văn, Tiêu đề 1–3) · **Phông** (Times New Roman, Arial, Cambria, Calibri, Tahoma, Verdana — có xem trước phông) · **Cỡ chữ** 10–32pt |
| Kiểu chữ | Đậm · Nghiêng · Gạch chân · Gạch ngang · Chỉ số trên · Chỉ số dưới |
| Màu | Màu chữ · Tô nền chữ (bảng 60 màu + chọn màu tùy ý + xóa màu) |
| Đoạn | Xóa định dạng · Canh trái/giữa/phải/đều · **Giãn dòng** · Giảm/Tăng thụt lề |
| Danh sách | Dấu chấm · Đánh số · Trích dẫn |
| Chèn | **Liên kết** · **Ảnh** (URL hoặc tệp ≤1MB) · **Bảng** (lưới 10×10 như Word) · Đường kẻ ngang |
| Bảng (khi con trỏ trong bảng) | **Viền bảng** (độ dày 0,5–2,25pt · nét liền/đứt/chấm · màu · preset Tất cả/Ngoài/Trong/**Không viền**/Trên/Dưới/Trái/Phải) · **Màu nền ô** |

**Giãn dòng** theo nấc Word: 1,0 · 1,15 · 1,5 · 2,0 · 2,5 · 3,0, kèm **Tùy chỉnh…** (nhận dấu phẩy thập phân) và "Theo mặc định của trang". Word đo một dòng theo bộ phông chứ không theo cỡ chữ, nên nấc "1,5 dòng" của Word được quy đổi đúng sang CSS thay vì để 1.5 (đặt cạnh bản Word sẽ thấy thưa hơn hẳn).

Thanh công cụ **tự co theo bề ngang màn hình**: hụt chỗ thì các lệnh ít dùng rơi vào menu **"Thêm"** ở cuối thanh; bốn ô chọn thì không bao giờ bị giấu vì chúng vừa là nơi bấm vừa là nơi **đọc** định dạng của đoạn đang đứng.

**Menu chuột phải**: Cắt/Sao chép/Dán/Dán chữ thuần · Đậm/Nghiêng/Gạch chân/Xóa định dạng · Mở & gỡ liên kết · submenu **Bảng** đầy đủ (thêm/xóa hàng cột, gộp ô, tách ô, hàng tiêu đề, cột tiêu đề, chia đều bề ngang, xóa bảng) · bảng màu nền ô.

**Dán từ Excel / Google Sheets**: copy một vùng ô, bôi chọn vùng ô tương ứng trong bảng của trình soạn rồi nhấn Ctrl/Cmd+V — dữ liệu được rải theo đúng hàng/cột và vẫn sửa được, **không dán thành ảnh**. Nếu không đứng trong bảng, vùng Excel được chèn thành một bảng mới. Menu chuột phải **Dán** dùng cùng quy tắc này; ảnh copy thông thường vẫn dán thành ảnh.

### 4.3 Mục lục và thước

- **Mục lục** đọc thẳng các tiêu đề trong bài, thụt theo cấp, tô sáng mục đang đứng, bấm là cuộn tới. Cột kéo giãn được (160–420px).
- **Thước ngang** có hai con trượt chỉnh lề trái/phải: kéo (chỉ vẽ) → **buông tay mới ghi xuống bản ghi**; bấm đúp về lề mặc định; phím ←/→ nhích từng nấc. Lề lưu **theo phiên bản**, nên sửa lề ở bản 2.0 không đổi hình dạng bản 1.0 đã ký.
- **Thước dọc** chỉ để đọc — trả lời câu "đoạn này đã xuống tới đâu của tờ giấy".

### 4.4 Nhập tệp

Nút **Nhập tệp** có ở cả trang soạn văn bản thật lẫn trang dựng mẫu. Nhận **.doc · .docx · .pdf · .md · .html**, tối đa **10MB**. Nếu trình soạn thảo đã có nội dung, hệ thống hỏi một trong hai cách:

- **Chèn tại vị trí con trỏ** (mặc định an toàn): giữ nguyên phần đã soạn và gắn nội dung tệp vào đúng chỗ con trỏ.
- **Ghi đè toàn bộ**: xóa nội dung đang có rồi thay bằng toàn bộ nội dung tệp; lựa chọn mang màu cảnh báo. Editor đang rỗng thì nhập thẳng, không hiện hộp hỏi.

- **DOCX** đọc thẳng OpenXML, giữ định dạng đoạn/chữ/danh sách/bảng/ảnh.
- **PDF có lớp chữ** dựng lại được thành văn bản sửa được; PDF scan giữ nguyên dạng ảnh trang.
- Nhập PDF xong hiện **Báo cáo đối chiếu**: chất lượng, số trang sửa được / số trang ảnh, danh sách vấn đề theo mức thông tin/cảnh báo/lỗi, bấm một dòng là nhảy tới đúng trang nguồn.

### 4.5 Bản in / Xuất PDF

Nút **In / Xuất PDF** mở tab riêng, không menu.

- Nội dung được **gom vào từng tờ A4** rồi mới vẽ, không để trình duyệt tự ngắt trang — nhờ vậy mới đánh được **số trang** canh giữa lề trên, **bỏ trang đầu**, đúng Nghị định 30.
- Lề lấy đúng bộ số của phiên bản đang in.
- Bản **chưa ban hành in ra vẫn được** (soát bản thảo trên giấy là việc thật) nhưng đóng **chữ chìm "BẢN NHÁP"** — tờ giấy rời khỏi màn hình là không còn trạng thái nào đi kèm.
- Khối cao hơn một trang (bảng dài, ảnh lớn) **không bị cắt đôi**; nó tràn sang tờ sau và trang in **nói thẳng điều đó** bằng băng cảnh báo kèm số khối bị ảnh hưởng.

---

## 5. Phiên bản

Nội dung không nằm ở văn bản mà ở **phiên bản**. Một văn bản có nhiều phiên bản; `1.0`, `1.1` (sửa nhỏ), `2.0` (sửa lớn).

| Trạng thái phiên bản | Sửa nội dung | Ghi chú |
|---|---|---|
| Nháp | Được | |
| Đang duyệt | **Không** | Đóng băng chờ người duyệt |
| Đã duyệt | **Không, vĩnh viễn** | Khóa một chiều, không có hàm mở khóa |
| Đã thay thế | Không | Bản sau đã lên |

- **Mỗi văn bản nhiều nhất một phiên bản đang mở.** Ràng buộc ép ở tầng dữ liệu, không phải kiểm bằng câu lệnh trong mã — hai người bấm "Mở phiên bản mới" cùng lúc thì một người thắng, người kia nhận câu **nói rõ ai đang giữ bản nháp**.
- Mở bản mới: bắt chọn **sửa lớn / sửa nhỏ**, bắt khai **"Sửa gì"**, tùy chọn "Vì sao sửa" và ngày hiệu lực. Bản mới **chép** nội dung, lề trang và liên kết tệp của bản gốc.
- Lúc duyệt, hệ tính **SHA-256 của nội dung** và ghi vào phiên bản — về sau còn cái để đối chiếu "bản in tôi cầm có đúng bản đã duyệt không".
- Sửa lớn mặc định bật cờ **bắt người đã đọc bản cũ xác nhận đã đọc lại**.

Tab **Phiên bản** liệt kê đủ các bản kèm trạng thái, ai duyệt, ngày hiệu lực; bấm một dòng là mở đúng bản đó ở tab Soạn thảo. Đang xem bản không phải bản đang dùng thì có băng cảnh báo + nút **"Sang bản đang dùng"**.

---

## 6. Số hiệu, sổ văn bản, quy tắc đánh số

### 6.1 Hai kiểu định danh

| Kiểu | Ví dụ | Dùng cho |
|---|---|---|
| **Mã tài liệu bất biến** | `DEGO-QC-012` | Quy chế, quy trình, biểu mẫu — đếm tiếp mãi, không reset theo năm |
| **Số hiệu theo sổ** | `08/2026/TB-NS-DEGO` | Công văn, thông báo, quyết định — đếm lại mỗi năm |

Thời điểm cấp số do **loại văn bản** quyết: cấp lúc tạo nháp, hoặc (mặc định) **cấp lúc được duyệt**.

### 6.2 Ba lớp chống trùng số

Số hiệu **do hệ cấp, không ai gõ tay**. Chống trùng bằng ba lớp cùng lúc: khóa dòng bộ đếm khi cấp · ràng buộc duy nhất trên khóa bộ đếm · cấp số **trong cùng giao dịch** ghi bản ghi. Không có endpoint "xin một số" đứng riêng — xin số rồi mới ghi là mở đường cho hai người cùng cầm một số.

**Cấp một lần, không cấp lại.** Bãi bỏ hay xóa cũng không trả số về sổ.

### 6.3 Quy tắc đánh số

Mẫu số hiệu ghép từ các thẻ: `{STT}` `{Ngay}` `{Thang}` `{Nam}` `{LoaiVB}` `{PhongBan}` `{PhapNhan}` `{SoVB}`. Thẻ nào không có dữ liệu thì bị dọn sạch cùng dấu phân cách thừa.

- Quy tắc chọn theo **chiều** (đến/đi/nội bộ) → **độ ưu tiên** → cùng ưu tiên thì **phạm vi cụ thể hơn thắng** (khai đích danh sổ > khai đích danh loại > áp chung).
- Không quy tắc nào khớp thì về mặc định của hệ.
- Quy tắc **đã cấp số ra ngoài** thì khóa chiều, mẫu, số bắt đầu, cách đếm — và **không xóa được**, chỉ ngừng dùng.
- Bật **"cho sửa số"** thì văn thư được sửa số hiệu thủ công, bắt buộc kèm lý do và không được trùng số trong cùng pháp nhân × năm.

### 6.4 Sổ văn bản

Sổ có **chiều** (đến/đi/nội bộ), bộ đếm riêng theo năm, và **thành viên**: người *quản lý sổ* (đọc + sửa) và người *xem sổ* (chỉ đọc) — đây cũng là một nguồn quyền, khỏi phải chia tay từng văn bản. Mỗi sổ phải có ít nhất một người quản lý. Sổ đã cấp số thì không đổi số bắt đầu và không xóa được.

---

## 7. Phạm vi áp dụng — "văn bản này ai phải làm theo"

Khai theo ba chiều: **pháp nhân · phòng ban · cá nhân**, mỗi dòng là *bao gồm* hoặc *loại trừ*.

**Luật đọc phạm vi:**
1. Các dòng *bao gồm* **cộng dồn**.
2. Phạm vi cụ thể hơn được ưu tiên: **cá nhân > phòng ban > pháp nhân**.
3. Nếu cùng một cấp thì dòng *loại trừ* thắng. Vì vậy có thể loại cả phòng rồi cho phép lại một cá nhân trong phòng đó.
4. **Không khai dòng nào = áp cho toàn bộ pháp nhân ban hành** — mọi phòng, mọi nhân sự của chính công ty đứng tên, và chỉ công ty đó.

Luật 4 là mặc định thực dụng: gần như mọi văn bản chỉ lưu hành trong đúng công ty làm ra nó, bắt người soạn khai tay một dòng "pháp nhân = công ty mình" thì ai cũng quên, và văn bản ban hành xong nằm im không tới ai mà không có gì báo. Khai **bất kỳ** dòng nào là tắt mặc định này.

Chọn chiều **phòng ban bắt buộc kèm pháp nhân** — "Phòng Kế toán" ở tập đoàn 13 công ty là câu hỏi thiếu vế.

**Chọn nhiều một lượt** (CR-117). Cả ba chiều đều khai được cả mẻ:

- *Pháp nhân* — tick nhiều nơi, mỗi nơi thành một dòng riêng (bỏ riêng một nơi về sau không phải khai lại cả cụm).
- *Phòng ban* — tick nhiều **pháp nhân** trước, ô phòng ban bên dưới gom phòng ban của **đúng những nơi đó**; tick nhiều phòng thì mỗi **cặp (phòng ban × pháp nhân)** thành một dòng. Bỏ tick một pháp nhân thì các cặp thuộc nơi đó tự rơi khỏi ô chọn. Cùng một tên phòng ở hai công ty là **hai dòng khác nhau** — ô chọn hiện tên pháp nhân bên phải để phân biệt.
- *Cá nhân* — vẫn từng người một.

Màn **Văn bản áp dụng cho tôi** (`/document/applied-to-me`) là mặt kia của cùng dữ liệu: mở ra thấy đúng những văn bản mình phải theo, lọc nhanh được nhóm "cần rà lại".

---

## 8. Quyền truy cập theo từng văn bản

Đây là **lớp thứ ba**, đứng cạnh phân quyền theo vai trò và phạm vi dữ liệu — dùng cho hai ca mà phạm vi không diễn đạt nổi: "văn bản này chỉ ban giám đốc đọc" và "phòng này thấy hết trừ đúng một người".

Chia quyền cho **người · phòng ban · pháp nhân · vai trò**, mỗi dòng là *cho phép* hoặc **cấm**, kèm quyền (đọc/sửa/xóa), hạn hiệu lực và **lý do bắt buộc**.

**Thứ tự quyết định:** cấm đích danh → cho phép đích danh → thành viên sổ → phạm vi vai trò → không được. **Cấm thắng tất cả**, kể cả người tạo và quản trị viên.

Hai chi tiết cố ý:
- **Thu hồi là đánh dấu, không xóa dòng** — về sau còn tra được "ai từng có quyền gì, tới lúc nào".
- Không được đọc thì trả **404**, không phải 403 — 403 vẫn lộ ra là văn bản đó tồn tại.

Ngoại lệ: người đang (hoặc đã) có việc trong phiên duyệt của văn bản thì **luôn đọc được** — không ai ký một thứ họ không mở ra xem được.

---

## 9. Quan hệ giữa văn bản

Mười loại quan hệ, mỗi loại có chiều ngược của nó:

| Xuôi | Ngược | | Xuôi | Ngược |
|---|---|---|---|---|
| Thay thế | Bị thay thế bởi | | Kèm theo | Có kèm theo |
| Sửa đổi | Bị sửa đổi bởi | | Thuộc về | Bao gồm |
| Bổ sung | Được bổ sung bởi | | Căn cứ theo | Là căn cứ của |
| Hướng dẫn | Được hướng dẫn bởi | | Tham chiếu | Được tham chiếu bởi |
| Bãi bỏ | Bị bãi bỏ bởi | | Trích từ | Có bản trích |

**Quy tắc quan hệ** (màn `/document/link-rules`) khai loại nào được nối với loại nào, bắt buộc hay tùy chọn, số lượng tối thiểu/tối đa. Form khai quan hệ ở trang chi tiết **tự hiện ô theo quy tắc của loại**.

- **Thiếu quan hệ bắt buộc thì không gửi duyệt được.**
- **Cấm vòng lặp** — kiểm cả chuỗi chứ không chỉ hai bước (A thay thế B, B thay thế C, C thay thế A đều bị chặn).
- Quan hệ *trích từ* và *căn cứ theo* của bản clone do **hệ sinh**, không khai tay và không xóa được.
- Tab Quan hệ còn có **Cây tài liệu** (tối đa 3 cấp): mở Quy trình thấy ngay Hướng dẫn và Biểu mẫu treo dưới nó, tách riêng nhóm **bản riêng ở pháp nhân con**.

### 9.1 Tác động dây chuyền khi ban hành

Khi văn bản mới **thật sự có hiệu lực**:

| Quan hệ | Việc hệ tự làm với văn bản cũ |
|---|---|
| Thay thế | Chuyển sang **Đã thay thế** |
| Bãi bỏ | Chuyển sang **Bãi bỏ** |
| Sửa đổi / Bổ sung | **Không đổi trạng thái**, nhưng gắn nhãn cảnh báo "đã bị sửa đổi bởi…" |

Ca *sửa đổi/bổ sung* là ca nguy hiểm nhất vì văn bản cũ vẫn hiện "Có hiệu lực" trong khi một phần của nó đã bị thay — nên nhãn cảnh báo hiện ở **mọi tab** của trang chi tiết và **không đóng được**.

Khi văn bản cha lên phiên bản mới hoặc bị bãi bỏ, văn bản con được xử theo cấu hình của quy tắc: không làm gì · **đánh dấu cần rà soát lại** · hết hiệu lực theo cha. **Hệ chỉ đánh dấu, không bao giờ tự sửa nội dung văn bản con.**

Ban hành hôm nay mà hiệu lực tháng sau thì **chưa** chạy tác động — tới đúng ngày hệ mới chạy, tránh chuyện bản cũ chết sớm một tháng.

---

## 10. Bản trích

Tách một phần nội dung của văn bản đã ban hành thành văn bản riêng, mức mật thấp hơn, để gửi cho người không được đọc bản đầy đủ.

Ba ràng buộc **khóa cứng**, quy tắc quan hệ không tắt được:
1. Mức mật bản trích **luôn ≤ bản gốc** (kiểm cả lúc tạo lẫn lúc về sau nâng mức mật của bản trích).
2. Gốc lên phiên bản mới → bản trích **cần rà soát lại**.
3. Gốc bị bãi bỏ → bản trích **hết hiệu lực** theo.

Bản trích mang đúng loại của gốc, **không cấp số hiệu riêng**, không người ký, và luôn ghi rõ trích từ **phiên bản nào**.

---

## 11. Clone cho pháp nhân con

Dùng khi mỗi công ty con phải **tự đứng tên ban hành** văn bản của mình (số hiệu riêng, người ký riêng, hiệu lực riêng) thay vì dùng chung một văn bản của tập đoàn.

- Khai **kế hoạch clone** lúc tạo; bản nháp thật chỉ sinh **sau khi bản gốc đã ban hành**.
- Mỗi pháp nhân con **một bản clone duy nhất**; không clone về chính nơi ban hành.
- Bản clone tự có liên kết ngược **căn cứ theo** bản gốc — do hệ sinh, không xóa được.
- Gốc lên phiên bản mới → **mọi bản clone bị đánh dấu cần rà lại** và người phụ trách được báo (chuông trong ứng dụng, kèm email nếu môi trường bật email).
- Có màn theo dõi: 12 công ty con đang ở phiên bản nào, ai đã ban hành, ai còn nháp, ai chưa đụng tới.

Cơ chế áp dụng (**gắn phạm vi** hay **clone**) được suy ra từ chính phạm vi đã khai, chốt tại thời điểm ban hành — không hỏi lại người dùng lần thứ hai.

---

## 12. Chữ ký

Ghi nhận chữ ký lên **phiên bản đã khóa**. Ba loại, **giá trị pháp lý khác hẳn nhau** nên câu giải thích in thẳng cạnh chữ ký chứ không giấu trong tài liệu hướng dẫn:

| Loại | Giá trị |
|---|---|
| Ký điện tử nội bộ | Có giá trị **trong nội bộ tập đoàn**, không có giá trị với bên ngoài |
| Ký số có chứng thư | Có giá trị pháp lý với bên ngoài (bắt khai số chứng thư + nhà cung cấp) |
| Ký giấy đã quét | Bản ghi nhận chữ ký trên giấy; giá trị theo bản giấy gốc |

Bảng chữ ký **chỉ ghi thêm** — không sửa, không xóa. Một chữ ký gỡ được thì nó không còn là chữ ký. Mỗi chữ ký chép lại SHA-256 nội dung lúc ký, nên nếu nội dung về sau lệch đi thì giao diện lộ ra ngay.

---

## 13. Phê duyệt

Hai đường tồn tại song song, chọn bằng công tắc của bộ máy duyệt dùng chung:

**Luồng một bước (mặc định).** Người có quyền `document.approve` bấm **Duyệt và ban hành** hoặc **Trả lại** ngay trên trang văn bản.

**Luồng nhiều bước.** Khi đã khai luồng duyệt cho `document`: gửi duyệt sinh một phiếu chạy qua từng chặng (trưởng bộ phận → ban chuyên môn → lãnh đạo…). Lúc này:
- Hai nút của luồng một bước **biến mất**.
- **Duyệt ngay trong văn bản** (CR-111): băng ở đầu trang chi tiết đổi màu và mọc nút **Duyệt / Trả lại** khi đang tới lượt người đang đọc; tab **Phê duyệt** cũng có nút đó. Cả hai mở đúng hộp thoại chung của bộ máy duyệt (Duyệt · Trả lại · Từ chối · Ghi ý kiến), nên dấu vết và luật bắt buộc nêu lý do không đổi. Nút **chỉ hiện với đúng người đang cầm việc**.
- Tab **Phê duyệt** hiển thị từng chặng: đã duyệt · đang chờ · từ chối · tự qua vì trùng người · chưa tới lượt · không chạy, kèm dấu vết ai làm gì lúc nào (in ra được).
- Băng ở đầu trang cho biết đang chờ ai, và **chuyển đỏ khi phiếu kẹt** (không tìm ra người duyệt) hoặc khi duyệt hết bước mà chưa ban hành.
- **Rút phiếu** đưa văn bản **về Nháp** để sửa tiếp.

**Đổi người duyệt giữa chừng** (CR-114). Sửa ô *ai duyệt bước này* trong màn **Luồng duyệt** thì mọi phiếu **đang chạy** theo luồng đó bám theo ngay:

- bước **đang chờ** → việc chuyển sang người mới, người cũ mất việc và **không ký được nữa**; người mới nhận thư báo;
- bước **chưa tới** → tới lượt thì tính theo người mới;
- bước **đã ký** → không đụng tới, chữ ký là chuyện đã rồi;
- phiếu đang **kẹt** ở bước đó → **hồi sinh** nếu nay tìm được người duyệt (đây là đường gỡ kẹt bằng cấu hình);
- sửa xong mà **không còn ai** duyệt được → phiếu KẸT, tuyệt đối không tự đi tiếp.

Người cũ đang mở trang chi tiết văn bản đó sẽ bị **báo lỗi và đá về danh sách** trong vòng 20 giây — khe đọc của họ vốn mở ra chính vì việc duyệt đó. Người còn quyền xem vì lý do khác (người soạn, được chia quyền, vai trò đủ rộng) thì vẫn ở lại, chỉ mất nút Duyệt.

⚠️ **Cấu trúc bước thì KHÔNG bám theo** — thêm/xóa/đổi thứ tự bước vẫn đóng băng theo bản chụp lúc phiếu bắt đầu, và đó là chủ ý: phiếu đang đứng ở một bước vừa bị xóa thì mất đích tới.

⚠️ **Không có ai thay ai.** Nhánh «Đẩy lên cấp trên» đã bỏ (CR-114) — đó là chỗ duy nhất bộ máy tự chọn một người không có tên trong luồng. Bước hụt người thì chỉ còn hai lối: *chuyển cho người dự phòng* (phải khai đích danh) hoặc *dừng phiếu và báo quản trị*.

**Ba đường tìm ra việc của mình** — cố ý nhiều đường, vì im lặng ở đây nghĩa là văn bản nằm chết giữa luồng:

1. **Thư báo** vào chuông thông báo và trang `/notifications` **ngay khi** việc chuyển sang chờ mình, kèm đường dẫn thẳng tới văn bản. Người được **ủy quyền bấm thay** cũng nhận thư, và thư nói rõ đang bấm thay ai. Dùng chung hệ thông báo sẵn có, không có hộp thư thứ hai.
2. **Menu «Chờ tôi duyệt»** trong chính phân hệ Văn bản, mang huy hiệu đếm việc (đỏ nếu có việc quá hạn). Mục này **không gác quyền** — người duyệt trong luồng thường không có vai trò nào ở phân hệ Văn bản. Màn này có ô tìm (số hiệu · tên · bước · người trình) và hai ô lọc (*Hạn duyệt*, *Người trình*), chạy ngay tại trình duyệt vì hộp việc của một người vốn ngắn.
3. **Nhãn *Chờ bạn duyệt*** trên đúng dòng của bảng danh sách văn bản.

**Nhìn lại việc mình đã ký.** Ngay dưới hộp việc là khối **«Đã duyệt gần đây»** — chọn 7 / 30 / 90 ngày, có ô tìm riêng, bấm dòng mở thẳng văn bản. Nó đọc từ **dấu vết** nên ghi rõ *tôi đã làm gì* (duyệt · trả lại · từ chối) kèm ý kiến, và người **bấm thay** theo ủy quyền vẫn thấy phiếu mình đã ký. Hai cột tách hẳn: *Tôi đã* và *Phiếu bây giờ* — ký xong bước của mình mà phiếu còn ba bước nữa là chuyện thường. Ghi ý kiến **không** tính là một quyết định nên không vào danh sách này. Muốn tra đủ lịch sử thì mở dấu vết của chính văn bản (tab *Phê duyệt*), nơi có cả những người khác đã làm gì.

Màn **«Việc của tôi»** ở phân hệ Phê duyệt **đã xóa** (21/08/2026). Phân hệ đó nay chỉ còn phần cấu hình (Luồng duyệt · Bật bộ máy duyệt). Nút hộp việc trên thanh trên và nút *Việc cần làm* ở Trang cá nhân đều dẫn về **«Chờ tôi duyệt»**. Hiện chỉ Văn bản chạy bộ máy duyệt; ngày bật cho Thu mua thì dựng hộp việc trong chính phân hệ đó — **không** dựng lại một danh sách gom chung có nút duyệt trên từng dòng.

---

## 14. Ban hành

### 14.1 Hộp thoại ban hành

Bấm **Duyệt và ban hành** mở bản **xem trước trước khi ban hành**, cho biết:

- Số hiệu **sẽ** được cấp; phiên bản nào sẽ bị khóa; hiệu lực từ ngày nào.
- Văn bản nào sẽ **đổi trạng thái** theo (bị thay thế / bị bãi bỏ).
- Phạm vi áp dụng đang khai bao nhiêu dòng; pháp nhân nào sẽ nhận bản riêng.
- **Khối chặn (đỏ)** và **khối cảnh báo (vàng)** tách bạch: chặn thì nút Ban hành mờ đi, cảnh báo thì vẫn ban hành được.
- Ô **«Gửi thông báo danh nghĩa»** — xem §14.3. Ô này chỉ hiện khi người đang đăng nhập
  thật sự được cấp hộp thư nào đó.

Ban hành xong: cấp số → khóa phiên bản (tính SHA-256) → vào sổ → chạy tác động dây chuyền (nếu hiệu lực hôm nay).

### 14.2 Duyệt xong KHÔNG phải lúc nào cũng ban hành

Cột **«Chờ người soạn ban hành»** trên *Loại văn bản* quyết định nhịp cuối:

| Cờ | Ký đủ chữ ký xong thì |
|---|---|
| **Tắt** (mặc định — mọi loại đang chạy) | Ban hành luôn: cấp số, khóa phiên bản, chuyển hiệu lực |
| **Bật** | Dừng ở **Chờ ban hành**; **người soạn thảo** mở ra, chọn hộp thư rồi bấm *Ban hành* |

Vì sao tách: với thông báo gửi toàn công ty, người ký duyệt **nội dung**, còn người chịu
trách nhiệm phát hành mới là người quyết định **gửi đi lúc nào** và **danh nghĩa địa chỉ nào**.

Luật của trạng thái *Chờ ban hành*:

- **Chỉ người soạn thảo bấm được.** Quyền `document.approve` không thay được — người ký
  đã ký xong phần của họ rồi; phát hành là một trách nhiệm khác và phải chỉ đúng một người.
  So theo hồ sơ nhân sự (`drafter_employee_id` / `owner_employee_id`), không theo người tạo bản ghi.
- **Khóa sửa y như lúc đang duyệt** (409). Chữ ký đã đặt lên nội dung này; mở ra sửa tiêu đề
  hay nâng mức mật rồi mới bấm Ban hành là phát hành ra thứ khác với thứ người ký đã đọc.
- **Không gửi duyệt chồng lên được** — bản đang mở vẫn ở tư thế "chờ duyệt" nên `submit` chặn.
- Muốn sửa thì phải nhờ người duyệt **trả lại**.
- Băng thông báo trên trang nói **hai câu khác nhau**: với người soạn là *"đang chờ bạn"*,
  với người khác là *"chờ ai"*. Không nói ra thì người soạn ngồi chờ người khác, người khác
  tưởng xong rồi, và văn bản nằm im vô thời hạn.

### 14.3 Chọn hộp thư gửi thông báo

Ca nghiệp vụ: nhân sự hành chính đăng nhập bằng tài khoản của chính mình
(`nhanvien@gmail.com`) nhưng ban hành *Thông báo nghỉ lễ* cho toàn công ty **danh nghĩa
`hr@gmail.com`** — người nhận phải thấy thư đến từ phòng Hành chính, không phải từ một cá nhân.

- Khai hộp thư ở **Quản trị › Hộp thư gửi** (`/system/mailboxes`, entity quyền `mailbox`).
- **Mỗi hộp thư giữ bộ SMTP RIÊNG**, không chỉ đổi dòng «Từ». Gmail **ghi đè** `From` về
  đúng tài khoản đã đăng nhập trừ khi địa chỉ kia đã khai *Send mail as* trong chính hộp
  thư đó — chỉ đổi tiêu đề là người nhận vẫn thấy địa chỉ cũ, hỏng mà không có lỗi nào báo.
  Gmail đòi **Mật khẩu ứng dụng** (bật xác minh 2 bước rồi tạo), mật khẩu đăng nhập thường
  không gửi được.
- **Ai dùng được thì khai đích danh từng người.** Quyền gửi thư danh nghĩa cả một phòng ban
  phải chỉ mặt đặt tên, và phải kiểm toán được về sau *"ai đã từng gửi thay ai"*. Cột
  `company_id` của hộp thư chỉ là **bộ lọc hiển thị** theo pháp nhân, không phải chốt quyền.
- Mật khẩu **mã hóa Fernet**, API không bao giờ trả ngược — chỉ trả cờ "đã có hay chưa".
  ⚠️ Lúc sửa, ô mật khẩu **để trống nghĩa là GIỮ NGUYÊN**, không phải xóa: màn sửa không
  nhận lại được giá trị cũ nên nó gửi rỗng ở mọi lần sửa tên hay ghi chú. Muốn xóa thật thì
  có nút riêng.
- Chốt quyền dùng hộp thư nằm ở **tầng dịch vụ**, không ở ô chọn: `mailbox_id` là một con
  số trong thân request, giao diện chỉ bày hộp thư của mình nhưng ai cũng gõ số khác vào được.
- Hộp thư thiếu SMTP **vẫn bày ra** trong hộp thoại nhưng không chọn được, kèm một dòng nói
  rõ. Lặng lẽ bỏ khỏi danh sách thì người được cấp không thấy hộp thư của mình và không hiểu vì sao.
- Không chọn gì → gửi bằng địa chỉ hệ thống, y như trước. Tính năng này là **thêm lựa chọn**,
  không bắt buộc.
- Hộp thư ngừng dùng thì **không xóa hẳn**: nhật ký thư cũ còn trỏ vào đây, và câu *"thư đó
  gửi danh nghĩa ai"* phải trả lời được mãi về sau. `tab_email_log` giữ cả `mailbox_id` lẫn
  `from_email` đã gửi thật.

---

## 15. Danh sách, tìm kiếm, tổng quan

**Danh sách văn bản** lọc và phân trang **ở máy chủ** — bảng sẽ lên hàng chục nghìn dòng, và nạp hết về máy người dùng còn nghĩa là gửi cho họ cả văn bản họ không được xem.

- Ô tìm nhanh chấp nhận **tên, số hiệu, số hiệu cũ của bản giấy, từ khóa, nơi lưu trữ cứng**.
- Hai ô chọn nhanh: loại văn bản, trạng thái.
- **Bộ lọc nâng cao** (nhiều điều kiện, nối AND/OR): trích yếu · mã tài liệu · số hiệu theo sổ · số hiệu cũ · nơi lưu trữ cứng · từ khóa · loại · pháp nhân · phòng chủ trì · người chịu trách nhiệm · sổ · trạng thái · mức mật · độ khẩn · ngày hiệu lực · ngày hết hiệu lực · năm ban hành · cờ cần rà soát. Ô tham chiếu tra theo **ID** chứ không theo tên — đổi tên phòng thì bộ lọc cũ không trượt.
- **Bản riêng nằm dưới bản gốc**, không đứng ngang hàng: một văn bản clone cho 12 pháp nhân sẽ thành 13 dòng gần như giống hệt nhau. Bung dòng gốc ra mới thấy các bản riêng.

**Tổng quan** (`/document`): 5 thẻ KPI (đang hiệu lực · chờ duyệt · cần rà lại · sắp hết hiệu lực trong 30 ngày · bản nháp), biểu đồ ban hành 12 tháng, cơ cấu theo loại, **ma trận ưu tiên** (quan trọng × khẩn), việc cần xử lý (cần rà lại · chờ duyệt · nháp treo quá 30 ngày), 8 văn bản gần đây. Mọi con số đều đã lọc theo đúng quyền của người đang xem.

---

## 16. Danh mục và thiết lập

| Danh mục | Nội dung |
|---|---|
| **Loại văn bản** | Mã, tên, nhóm, kiểu định danh, thời điểm cấp số, mức mật mặc định, chu kỳ rà soát, các cờ quy tắc áp dụng (kể cả **«Chờ người soạn ban hành»**, §14.2), và **quy tắc quan hệ** của loại |
| **Thư viện văn bản mẫu** | Khung trắng theo từng loại; mọi chỗ phải điền để dấu chấm lửng, **không gán sẵn tên người hay số hiệu** |
| **Mức mật / độ khẩn** | Chỉ đọc — thang cố định: Công khai · Nội bộ · Mật · Tuyệt mật; thường · khẩn · hỏa tốc |
| **Đơn vị gửi nhận** | Cơ quan nhà nước · đối tác · khách hàng · đơn vị nội bộ · khác |

Mã loại văn bản và mã dùng cho số hiệu của pháp nhân/phòng ban bị **khóa sau khi đã cấp số** — đổi chúng là đổi luôn tiền tố của số đã phát ra ngoài.

---

## 17. Chưa làm — biết trước để khỏi tìm

| Hạng mục | Tình trạng |
|---|---|
| **Nơi nhận + xác nhận đã đọc** | Bảng đã khai, chưa có màn hình |
| **Sổ văn bản đến** (văn bản từ ngoài gửi vào) | Chưa làm |
| **Trích lục chính thức** (khác bản trích nội bộ) | Chưa làm, chờ chốt nghiệp vụ |
| **Ký số có chứng thư** | Hệ chỉ **ghi nhận**; việc ký thật làm ở dịch vụ ngoài |
| **Lớp kiểm quyền theo mức mật** | Cột có, ràng buộc bản trích có, **lớp chặn chưa làm** → chưa đưa văn bản mật thật vào hệ thống |
| **Yêu cầu/xin phép soạn văn bản** | Đã cắt khỏi phạm vi |
| Tab stop / dấu chấm dẫn tự căn cột trong trình soạn thảo | Chưa có — dùng bảng không viền để thay |
| Đầu trang – chân trang tùy biến, đánh số mục tự động, chú thích chân trang | Chưa có |
| "Gồm cả đơn vị con" của phạm vi | Đang là **phép xấp xỉ** theo cấp công ty; sẽ sai khi có tầng thứ ba |

---

## 18. Quyết định đã chốt liên quan

Chi tiết đầy đủ ở `doc/tai-lieu-ky-thuat/change-log.md`.

| Mã | Nội dung |
|---|---|
| **D-028** | Không khai phạm vi = áp cho toàn bộ pháp nhân ban hành; bỏ hỏi cơ chế áp dụng lúc ban hành |
| **D-029** | Rút phiếu duyệt thì văn bản **về Nháp**; phòng chủ trì bắt buộc; cảnh báo hai luồng duyệt mặc định cùng bật |
| **D-030** | Thể thức trang theo Nghị định 30: lề lưu theo phiên bản, có trang in, có nhập tệp ở trang soạn thảo |
| **D-031** | Văn bản **đang trình duyệt thì đóng băng** nội dung, bộ trường chung và đính kèm |
| **D-032** | Thước lề ghi xuống bản ghi khi **buông tay**, không hẹn giờ |
| **D-033** | Bộ lọc nâng cao cho danh sách văn bản |
