# THỨ TỰ THỰC HIỆN

> [← plan.md](./plan.md) · Chốt 14/08/2026
> Thứ tự lấy theo mục **"Thứ tự làm phía FE"** của [`plans/reports/planner-260814-1027-van-thu-fe-giai-doan-dau.md`](../reports/planner-260814-1027-van-thu-fe-giai-doan-dau.md).
> Report đó là **FE-only** (64 mã `F-`); tệp này ghép mỗi mã `F-` với task backend tương ứng trong 4 tệp phase.

## Năm bước

| Bước | Report | Trong plan này | Trạng thái |
|---|---|---|---|
| **1** | F-05, F-11, F-12 + mục 4.1–4.4 · *nắn lại nền module đang có* | 5 task + 2 việc không mã | ☑ xong (trừ F-02 gom nhóm màn phân quyền) |
| **2** | F-06 → F-10 · *danh mục* | 6 task | ☑ xong (trừ F-09 phòng ban×pháp nhân) |
| **3** | F-13 → F-30 · *soạn thảo và phiên bản* | 27 task + 2 việc không mã | ◪ 3a, 3b, 3c xong · 3d (quan hệ cha–con, bản trích) và 3e (OCR) còn nguyên |
| **4** | F-31 → F-40 · *bộ máy phê duyệt* ‖ F-51 → F-64 · *quyền và tra cứu* | 18 task (P3) | ⏸ **Hoãn** — làm văn bản xong mới quay lại |
| **5** | F-41 → F-50 · *ban hành, phạm vi, clone* | — | Ngoài phạm vi plan này (P4) |

**38 task cho bước 1–3** (6 của `phase-00` + toàn bộ 14 của `phase-01` + toàn bộ 18 của `phase-02`), cộng 4 việc chưa đánh mã. 7 task `phase-00` còn lại xếp riêng ở cuối tệp. Bước 4 giữ nguyên [`phase-03`](./phase-03-bo-may-phe-duyet.md), 18 task. Bước 5 chờ trả lời B5/B6, sẽ lên plan riêng.

Hai chỗ tệp này **thêm vào so với report**, đều ghi rõ lý do tại chỗ: phần **cấp số backend** (report FE-only nên không có mã `F-`) và **F-01/F-03/F-04** (nằm trong bảng P0 của report nhưng mục "thứ tự làm" không xếp chúng vào bước nào).

---

## Bước 1 · Nắn lại nền module đang có — F-05, F-11, F-12 + mục 4.1–4.4

> Lý do report đặt bước này trước: *"nắn lại nền module hiện có trước khi đắp thêm — rẻ nhất lúc dữ liệu còn nằm ở localStorage."*

| Report | Task | Việc |
|---|---|---|
| F-05 | P0-T10 | Gắn `entity: 'document'` (+ entity con) vào `documentModule`, ẩn menu theo `can()`, thêm entity mới vào `core/permissions.py` |
| F-02 | P0-T10 | Gom nhóm đối tượng trên màn phân quyền theo phân hệ (28 → ~40 dòng). Cùng task với F-05 |
| F-11 | P1-T13 | Thang mức mật về 4 mức `Công khai · Nội bộ · Mật · Tuyệt mật`, tách hẳn khỏi thang độ khẩn 3 mức |
| F-12 | P1-T14 | Bỏ `nextBookNo` (`MAX+1`) ở client; `buildDocumentCode` chỉ còn để **xem trước**, kèm nhãn "số thật cấp lúc được duyệt" |
| mục 4.1 | — | Sổ văn bản đến/đi: **tạm ẩn khỏi menu**, giữ nguyên mã. Chờ câu A1 |
| mục 4.2 | — | Đổi trục `DocumentRecord`: `direction`/`book_no`/`partner_id` xuống thành thuộc tính phụ, trục chính là **loại văn bản + pháp nhân ban hành + phiên bản**. Đổi *kiểu dữ liệu* ở bước này, đổi *form* ở bước 3 (F-17) |
| mục 4.4 | P1-T14 | Trùng F-12 |
| — | P2-T14b | Gỡ bộ trường nhập động (quyết định 6) — làm ở đây vì cùng đụng `document-settings-page.tsx` với F-05 |
| **thêm** | P0-T11 | Chuông lọc theo app (`F-01` trong report). Xếp vào đây vì nhỏ, không phụ thuộc gì, và menu văn thư vừa bật ở F-05 thì chuông phải lọc đúng ngay |

**Xong là:** menu Văn bản chỉ hiện với người có quyền; thang mức mật đúng; không còn chỗ nào tự sinh số ở client; trang thiết lập còn 3 tab.
**Vẫn chạy trên localStorage** — chưa nối API nào. Đúng ý report: sửa lúc còn rẻ.

---

## Bước 2 · Danh mục — F-06 → F-10

| Report | Task | Việc |
|---|---|---|
| F-08 | P1-T01 | M2: `issue_code`/`short_name`/`level` cho pháp nhân · `issue_code`/`kind` cho phòng ban · bảng `tab_department_company`. FE thêm ô `issue_code` vào form HR |
| F-06 | P1-T02 | M3: `tab_doc_type` · `tab_doc_type_link_rule` · `tab_external_party` |
| F-06 | P1-T07 | BE CRUD loại văn bản |
| F-06 | P1-T10 | FE form loại văn bản mở rộng (bỏ `has_template`, ẩn `needs_request` — quyết định 6 và 7) |
| F-07 | P1-T11 | FE danh mục 32 loại gom theo 6 nhóm A–F, nối react-query, bỏ `document-type-store.ts` |
| F-09 | P1-T09 | BE + FE phòng ban×pháp nhân, kèm trưởng phòng theo từng pháp nhân |
| F-10 | P1-T09 | Danh mục đối tác — đã có màn, chỉ nối API |

**Xong là:** khai được loại văn bản với đủ trường thật (`id_scheme`, `default_secrecy`, `number_when`, chu kỳ rà soát…), nhập được 32 loại.
**Bỏ qua ở bước này:** `P1-T08` + `P1-T12` (quy tắc cha–con) — report xếp nó ở **F-29 thuộc bước 3**, làm cùng chỗ dùng tới nó.
**Chặn:** câu **B6** — cấp số ở bước 3 xong là khóa mã, không đổi được nữa.

---

## Bước 3 · Soạn thảo và phiên bản — F-13 → F-30

Khối lớn nhất. Report ghi: *"cho người thật bấm thử sớm nhất."*

### 3a · Cấp số — **thêm vào, report không có mã `F-`**

Report là FE-only nên không liệt kê phần này, nhưng nó **chặn 3b**: không có bộ cấp số thì service văn bản không ghi được số hiệu.

| Task | Việc |
|---|---|
| P1-T03 | M4 `tab_number_sequence` + M5 `tab_incoming_register` (tạo sớm, không màn hình) |
| P1-T04 | `next_number()` — khóa dòng `with_for_update`, **cùng transaction** với việc ghi bản ghi |
| P1-T05 | Khóa `issue_code` / mã loại sau khi đã cấp số |
| P1-T06 | **Bài kiểm 100 kết nối** — 100 số liên tiếp, không trùng, không nhảy cóc |

**Không sang 3b khi P1-T06 chưa xanh.**

### 3b · Bản ghi văn bản và soạn tay

| Report | Task | Việc |
|---|---|---|
| — | P2-T01 | M6: `tab_document` · `tab_document_version` · `tab_document_request` (rỗng) |
| — | P2-T02 | M7: `tab_document_link` |
| — | P2-T03 | Chỉ mục theo `04` mục 10 |
| — | P2-T04 | Hàm dựng truy vấn dùng chung + **bài kiểm `origin = 1`** |
| — | P2-T10 | BE service văn bản, cấp số theo `number_when` |
| ~~F-13~~ ~~F-15~~ ~~F-16~~ | — | **Cắt** — bỏ bước xin phép (quyết định 7) |
| F-14 → P2-T05 | P2-T05 | Tạo văn bản trực tiếp; **giữ phần gợi ý** văn bản cùng loại cùng phòng đang hiệu lực, chuyển từ form yêu cầu sang form soạn |
| F-17 | P2-T14 | FE form văn bản theo bộ trường chung C01 |
| ~~F-18~~ | P2-T16 | **Cắt phần tệp mẫu** (quyết định 6); thay bằng trình soạn nội dung tiptap + tự động lưu nháp + đính kèm |
| F-24 | P2-T16 | Ô số hiệu cũ, tìm kiếm chấp nhận số cũ |
| **thêm** | P0-T02 · P0-T03 · P0-T04 · P0-T12 | **F-03 và F-04 của report** — kho tệp riêng tư + link tạm 60–120s + nhật ký truy cập. Xếp vào đây chứ không để cuối: văn bản cần đính tệp ngay từ bước này, đính bằng link công khai rồi dọn sau thì **không lấy lại được link đã phát tán** (`00` mục 4.6) |
| — | — | FE danh sách + chi tiết văn bản nối API, bỏ `document-record-store.ts` |
| — | — | **Luồng duyệt một bước viết tay tạm** — một nút gửi duyệt, một người duyệt cấu hình cứng. Bước 4 sẽ thay |

**Xong là:** tạo → chọn loại → gõ nội dung → đính tệp → lưu → tìm lại được. **Cho 3 người ngoài đội bấm thử ở đây**, đừng đợi hết bước 3.

### 3c · Phiên bản

| Report | Task | Việc |
|---|---|---|
| F-19 | P2-T11 | Tab phiên bản; bản đã duyệt chỉ đọc; `is_locked` một chiều; bắt `change_summary`/`change_reason` từ bản 2 |
| F-20 | P2-T12 | Dialog mở phiên bản mới: bắt lý do + phân loại sửa lớn/nhỏ |
| F-21 | P2-T12 | Ép `open_slot` — hai người cùng bấm thì chỉ một người mở được, người kia thấy ai đang giữ nháp |
| F-22 | P2-T15 | Băng cảnh báo trên bản cũ, có nút sang bản mới, **không xóa không ẩn bản cũ** |
| F-23 | P2-T13 | Ngày hiệu lực riêng từng phiên bản; bản cũ vẫn hiệu lực trong lúc bản mới đang duyệt |

### 3d · Quan hệ cha–con và bản trích

| Report | Task | Việc |
|---|---|---|
| F-29 | P1-T08 | BE CRUD quy tắc cha–con, **khóa cứng 3 cột của quan hệ *trích từ*** |
| F-29 | P1-T12 | FE màn quy tắc cha–con |
| F-26 | P2-T19 | Khối quan hệ trên form tự hiện theo quy tắc, danh sách lọc đúng loại đích |
| F-27 | P2-T17 | Chặn gửi duyệt khi thiếu quan hệ bắt buộc; **cấm vòng lặp cả chuỗi dài** |
| F-28 | P2-T19 | Cây tài liệu trên trang chi tiết |
| F-25 | P2-T18 · P2-T20 | Bản trích nội bộ + quan hệ *trích từ* + 3 ràng buộc kéo theo; màn soạn bản trích |

### 3e · AI đọc ảnh

| Report | Task | Việc |
|---|---|---|
| F-30 | P2-T21 | OCR ảnh → bản nháp, ảnh gốc đặt cạnh để đối chiếu, cờ tắt AI. **Tùy chọn** — bỏ không ảnh hưởng nghiệp vụ nào |

---

## Bước 4 · Bộ máy phê duyệt — F-31 → F-40 · ⏸ hoãn

18 task, giữ nguyên [`phase-03`](./phase-03-bo-may-phe-duyet.md). Khi quay lại:

- **P3-T01 (khai thử 7 luồng ra giấy) phải làm trước dòng mã đầu tiên.**
- Việc đầu tiên là thay luồng một bước viết tay tạm dựng ở 3b.
- Điều kiện: chạy lại 5 kiểm thử Thu mua (P0-T01) vẫn xanh.

Report xếp **F-51 → F-64 (quyền truy cập và tra cứu, P5)** chạy **song song** với nhánh này — hai mảng gần như không đụng nhau, chia đôi được nếu có người thứ hai. Phần đó chưa có trong plan này.

---

## Phần P0 chưa xếp vào bước nào — bắt buộc xong trước prod

Report liệt kê F-01…F-04 trong bảng P0 nhưng mục "thứ tự làm" không xếp chúng. F-01 đã đưa vào bước 1, F-03/F-04 vào 3b. **Bảy task còn lại của `phase-00`** chưa có chỗ:

| Task | Việc |
|---|---|
| P0-T01 | **Kiểm thử 5 luồng duyệt hiện tại của Thu mua** — không chờ gì, làm được ngay từ hôm nay |
| P0-T05 | Cache quyền sang Redis + kênh xóa đệm tức thì |
| P0-T06 | Phạm vi phòng ban khớp bằng `department_id` |
| P0-T07 | Vá loại trừ phòng ban |
| P0-T08 | Vá nhật ký thao tác |
| P0-T09 | Grant MySQL append-only cho bảng nhật ký |
| P0-T13 | Guard `SCOPE_FIELDS` kèm danh sách miễn trừ 6 entity cũ |

Bảy task này **đụng thẳng vào lõi của hệ đang chạy**, không đụng gì tới việc dựng màn hình văn thư trên dev — nên chèn được vào bất cứ chỗ trống nào, hoặc giao cho người thứ hai chạy song song từ đầu.

> ⚠️ **Ràng buộc không thương lượng:** cho tới khi bảy task này xong và đã chạy prod ổn định — **không mở tài khoản văn thư trên prod, không đưa văn bản thật (nhất là văn bản mật) vào hệ thống.** Bước 1–3 chỉ chạy trên dev với dữ liệu giả. Lý do đầy đủ ở `van-thu/00` mục 3.
>
> P0-T01 nên làm sớm nhất có thể: nó không chặn ai, không phụ thuộc gì, và là lưới an toàn duy nhất cho sáu task còn lại.

## Làm song song được

| Việc | Ai | Chờ gì |
|---|---|---|
| Nhập 32 loại văn bản, 13 mã pháp nhân, mã phòng ban | Hành chính | Xong bước 2 |
| Rà soát và số hóa văn bản giấy đang hiệu lực | Hành chính | **Không chờ gì** |
| 7 task P0 còn lại | Người thứ hai | Không chờ gì |
| Trả lời A1, B3, B6, B12 | Người quyết | — |

## Câu hỏi chặn theo bước

| Câu | Chặn |
|---|---|
| **B3** — tên chính xác 4 mức mật | Bước 1 (F-11). Nhẹ — sai thì sửa nhãn |
| **B6** — ai duyệt 32 mã loại + 13 mã pháp nhân | **Bước 3a** — cấp số xong là P1-T05 khóa mã, không đổi được nữa. Chặn thật |
| **A1** — bản đầu có sổ văn bản đến không | Không chặn. Bảng tạo sẵn ở 3a, màn hình tạm ẩn từ bước 1 |
| **B12** — có loại thứ 33 *Trích lục* không | Bước 3d, chỉ chặn trích lục chính thức (C20), không chặn bản trích nội bộ (C19) |
