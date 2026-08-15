# THỨ TỰ THỰC HIỆN

> [← plan.md](./plan.md) · Chốt 14/08/2026, sửa lại cùng ngày khi chốt làm **hai nhánh song song**
> **Nhánh A viết lại toàn bộ 14/08/2026** — `phase-03` từ 18 task thành **36**, thêm nhóm nền tổ chức chặn đầu, bỏ văn thư khỏi phạm vi. Phần nhánh B bên dưới giữ nguyên.
> Thứ tự phía văn thư lấy theo mục **"Thứ tự làm phía FE"** của [`plans/reports/planner-260814-1027-van-thu-fe-giai-doan-dau.md`](../reports/planner-260814-1027-van-thu-fe-giai-doan-dau.md).
> Report đó là **FE-only** (64 mã `F-`); tệp này ghép mỗi mã `F-` với task backend tương ứng trong 4 tệp phase.

## Hai nhánh

Trước đây tệp này xếp bộ máy phê duyệt vào bước 4 và ghi **hoãn**. **Không còn hoãn** — có hai người nên chạy song song:

| | Nhánh | Người | Task | Nội dung |
|---|---|---|---|---|
| **A** | Nền tổ chức + bộ máy phê duyệt | chủ dự án | 36 | Toàn bộ [`phase-03`](./phase-03-bo-may-phe-duyet.md). **Không có task nào chờ nhánh B.** Nhưng **11 task nhóm A (nền tổ chức) chặn cứng 25 task còn lại**, và **4 quyết định của P3-T01 chặn nhóm A** — hỏi ngay hôm nay |
| **B** | Văn thư | người thứ hai | 35 | Bước 1 → 2 → 3 bên dưới: nắn nền module đang có → danh mục → soạn thảo và phiên bản |

Cộng **2 task nền chung** làm trước khi tách nhánh và **6 task P0 còn lại** chặn việc lên prod → **79 task**.

**Quan hệ hai nhánh đã đổi.** Trước đây nhánh A làm bộ máy *cho văn thư dùng*. Giờ (quyết định 8) bộ máy gom luôn phần duyệt viết tay của **Thu mua**, và **Thu mua là người dùng đầu tiên** — văn thư ra khỏi phạm vi phase 3. Hai nhánh vì thế **gần như không còn dính nhau**: nhánh B tự dựng luồng duyệt tạm của mình, đấu vào bộ máy sau, bằng một task chưa ai viết.

**Vì sao tách được:** bộ máy chạy phiên — chọn luồng, snapshot, chọn người duyệt, rẽ nhánh, ủy quyền — tự kiểm hoàn toàn bằng pytest. Còn hai màn hình trước đây tưởng phải chờ văn bản có thật thì **không phải chờ**: `<ApprovalPanel>` dựng và nghiệm thu trên **YCMH** (`frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx` đã có sẵn), màn "việc của tôi" chạy được ngay khi Thu mua lên bộ máy. Sơ đồ `P2 ──▶ P3` trong `plan.md` là phụ thuộc *của tính năng người dùng thấy*, không phải của mã.

Luật chống giẫm chân nhau (Alembic, `core/permissions.py`, …) nằm ở mục **"Luật khi hai người chạy song song"** trong [`plan.md`](./plan.md). Đọc trước khi gõ dòng đầu tiên.

---

## Nền chung — làm xong mới tách nhánh

Hai task này cả hai nhánh đều cần. Làm một lần, một người làm, đừng chia đôi.

| Report | Task | Việc | Ai cần |
|---|---|---|---|
| F-01 | **P0-T11** | Chuông lọc thông báo theo app. Nhỏ, không phụ thuộc gì | Cả hai — nhánh A cần cho nhắc hạn duyệt, nhánh B cần ngay khi bật menu văn thư |
| F-05 · F-02 | **P0-T10** | Gắn `entity: 'document'` vào `documentModule`, ẩn menu theo `can()`, gom nhóm đối tượng phân quyền theo phân hệ (28 → ~40 dòng). **Khai luôn** entity `approval_flow` · `approval_task` · `position` trong cùng lần sửa `core/permissions.py` | Cả hai — và đây là tệp dễ xung đột nhất, nên chỉ sửa một lần |

**P1-T01 không còn là nền chung.** Việc gắn phòng ban vào pháp nhân đã chuyển vào **P3-T04** (nhóm A của nhánh A) vì nhánh A cần nó gấp hơn nhiều. **P0-T01 cũng bỏ khỏi nền chung** — nó thành **P3-T11**, lưới an toàn của riêng nhánh A.

---

# NHÁNH A · NỀN TỔ CHỨC + BỘ MÁY PHÊ DUYỆT

Chi tiết đầy đủ ở [`phase-03-bo-may-phe-duyet.md`](./phase-03-bo-may-phe-duyet.md) — **36 task, viết lại toàn bộ ngày 14/08/2026**. Người dùng đầu tiên của bộ máy là **Thu mua**, không phải văn thư. Sáu nhịp:

| Nhịp | Nhóm | Task | Ra được gì |
|---|---|---|---|
| **A1** | A · nền tổ chức | T01 → T11 | Chức vụ thành danh mục có cấp bậc · 244 nhân sự và 18 phòng ban gắn pháp nhân · trưởng phòng đã khai · cây tổ chức · **5 kiểm thử Thu mua xanh**. **Chặn cứng mọi nhịp sau** |
| **A2** | B · mô hình | T12 → T13 | 5 luồng thật khai được ra giấy · 6 bảng phê duyệt + chỉ mục |
| **A3** | C · bộ máy | T14 → T27 | Chạy phiên duyệt đầy đủ, tự kiểm bằng pytest. Người dùng đầu tiên là **bộ test** |
| **A4** | E · giao diện khai luồng | T32 | Khai luồng bằng giao diện, không sửa mã |
| **A5** | D + E · gom cổng | T28 → T31, T33, T34 | Một hàm trả lời "có quyền duyệt không" · chuyển **từng luồng Thu mua một** |
| **A6** | F · dọn | T35 → T36 | Sổ nợ ghi từ đầu, dọn sau khi prod chạy ổn |

### A1 · Nền tổ chức — làm trước, không được bỏ qua

Rà DB ngày 14/08/2026 ra kết quả này (số đo đầy đủ ở Phần 1 của `phase-03`):

- **Chức vụ là chữ tự do**, không có danh mục. 216/244 người ghi `"Nhân sự"` — đó là **tên phòng ban** lọt vào ô chức vụ.
- **18/18 phòng ban** không gắn pháp nhân · **235/244 nhân sự** không gắn pháp nhân.
- **16/18 phòng** không có trưởng phòng.
- Không có cây phòng ban, không có cây pháp nhân, `tab_employee` **không có cột cấp trên trực tiếp**.
- Phiếu nối phòng ban bằng **chuỗi tên**, và trong dữ liệu thật có `'Phòng Marketing'` — phòng này **không tồn tại** trong danh mục.

Hệ quả: trong 7 cách chọn người duyệt, hôm nay chỉ **2 cách chạy được**. Làm bộ máy trước nền này là làm xong không chạy.

**Bốn quyết định phải chốt trước (P3-T01):** một phòng ban thuộc một hay nhiều pháp nhân · danh mục chức vụ gồm gì và mấy cấp · "lên n cấp" leo theo cây phòng ban hay cấp bậc chức vụ · `'Phòng Marketing'` là phòng thật hay gõ nhầm.

**P3-T11 làm sớm nhất có thể** — phase này sẽ sửa thật vào 5 luồng duyệt của Thu mua, không có lưới thì không biết mình làm gãy cái gì.

### A2 · Mô hình luồng

**P3-T12 khai thử 5 luồng thật ra giấy** trước dòng mã đầu tiên, **có dùng chức vụ và cấp bậc** của A1. Chỗ nào khai không nổi là mô hình còn thiếu. Chú ý YCMH có **hai lần duyệt** (trưởng phòng, rồi thu mua điều phối) — khai không ra hai bước là mô hình sai.

**P3-T13** dựng 6 bảng. Chỉ mục `tab_approval_task(assignee_employee_id, status)` phải có **ngay từ migration**, không thêm sau.

### A3 · Bộ máy chạy phiên — T14 → T27

14 task backend, tự kiểm hoàn toàn bằng pytest. Hai task dễ bị bỏ sót nhưng **bắt buộc**:

- **T26 · việc chạy kèm cùng transaction.** Duyệt YCMH hiện kéo theo đổi trạng thái, điều phối, chuông, thư. Không có chỗ cắm này thì chuyển sang bộ máy là mất sạch tác dụng phụ.
- **T27 · quyền đọc phiếu cho người được giao duyệt.** `apply_scope` sẽ giấu việc của chính người phải duyệt, vì phạm vi `assigned` viết tay từng entity.

Trong A3 người dùng đầu tiên là **bộ test**. Đừng bật cờ cho luồng Thu mua nào chỉ để "thấy nó chạy" — bật là việc có thủ tục riêng ở A5.

### A4 · Trình khai luồng — T32

Màn nặng nhất. Khối điều kiện rẽ nhánh phải khai được đủ: **số tiền · pháp nhân · phòng ban · chức vụ · cấp bậc chức vụ · loại phiếu · gấp**. Ép khai nhánh mặc định. Ô "không tìm ra người duyệt" **không có lựa chọn tự duyệt qua**. Không dùng thư viện flow-chart.

### A5 · Gom về một cổng và chuyển Thu mua — T28 → T31, T33, T34

Cách làm đã chốt (quyết định 8): **thay đúng đoạn kiểm tra phân quyền**, hoặc **thêm một nhánh `if` ngay trong hàm đó** để đổi đường. Không viết lại nghiệp vụ.

1. **T28** — dựng `gate.py`, **bê nguyên xi** mã duyệt của 5 module Thu mua vào, kể cả chỗ trông có vẻ sai. Giao diện không sửa. Nghiệm thu: 5 kiểm thử xanh y nguyên, `git diff` chỉ có mã **dời chỗ**. **Chống chỉ định: nhân tiện sửa luôn cái thấy sai** — để dành T31, lúc đó có kiểm thử hai chế độ làm chứng.
2. **T29** — nhánh `if` + cờ `approval_engine.{entity}`, nằm **đúng một chỗ** bên trong cổng.
3. **T30** — hợp đồng dữ liệu `approval` cho giao diện. Giữ song song 12 cờ `can_*` cũ, đừng xóa ngay kẻo vỡ `frontend/` đang chạy thật.
4. **T33/T34** — `<ApprovalPanel>` dựng trên trang YCMH; màn việc của tôi lấy từ `/approvals/my-tasks`, **không gọi cổng cho từng dòng**.
5. **T31** — chuyển từng luồng: yêu cầu thanh toán → khảo sát → yêu cầu khảo sát → **YCMH** → ĐMH. Mỗi luồng bốn nhịp: khai luồng → kiểm thử xanh ở **cả hai chế độ cờ** → bật ở dev, theo dõi → sang luồng kế. **Không bật hai luồng cùng lúc.**

### A6 · Sổ nợ và dọn — T35, T36

**T35 mở `no-can-don.md` cùng lúc với T28**, ghi **ngay lúc chèn** chứ không ghi sau. Bốn nhóm nợ đã biết trước: nhánh `if` đổi đường · mã duyệt cũ bê vào cổng (gồm `_in_approve_scope`) · 12 cờ `can_*` giữ song song · **vai trò và quyền thành thừa** (`MANAGER` id 2, `dept_head` id 11, `manager_purchase` id 8 demo, `pur_manager` id 14 cùng nghĩa "quản lý"; cộng `tab_user_scope` với `dim='department'` đang lưu tên phòng làm giá trị).

**T36 là task cuối, không được bỏ.** Không dọn là còn ba cơ chế cùng trả lời một câu hỏi — đúng cái mà việc gom này sinh ra để dẹp.

**Cổng nhánh A:** 5 luồng Thu mua chạy trên bộ máy ở prod ổn định · **5 kiểm thử vẫn xanh** · sổ nợ đã dọn hoặc mỗi dòng còn lại có lý do rõ.

---

# NHÁNH B · VĂN THƯ

## Bước 1 · Nắn lại nền module đang có — F-11, F-12 + mục 4.1–4.4

> Lý do report đặt bước này trước: *"nắn lại nền module hiện có trước khi đắp thêm — rẻ nhất lúc dữ liệu còn nằm ở localStorage."*
> F-01, F-02, F-05 đã chuyển lên **nền chung**.

| Report | Task | Việc |
|---|---|---|
| F-11 | P1-T13 | Thang mức mật về 4 mức `Công khai · Nội bộ · Mật · Tuyệt mật`, tách hẳn khỏi thang độ khẩn 3 mức |
| F-12 | P1-T14 | Bỏ `nextBookNo` (`MAX+1`) ở client; `buildDocumentCode` chỉ còn để **xem trước**, kèm nhãn "số thật cấp lúc được duyệt" |
| mục 4.1 | — | Sổ văn bản đến/đi: **tạm ẩn khỏi menu**, giữ nguyên mã. Chờ câu A1 |
| mục 4.2 | — | Đổi trục `DocumentRecord`: `direction`/`book_no`/`partner_id` xuống thành thuộc tính phụ, trục chính là **loại văn bản + pháp nhân ban hành + phiên bản**. Đổi *kiểu dữ liệu* ở bước này, đổi *form* ở bước 3 (F-17) |
| mục 4.4 | P1-T14 | Trùng F-12 |
| — | P2-T14b | Gỡ bộ trường nhập động (quyết định 6) — làm ở đây vì cùng đụng `document-settings-page.tsx` với F-05 |

**Xong là:** menu Văn bản chỉ hiện với người có quyền; thang mức mật đúng; không còn chỗ nào tự sinh số ở client; trang thiết lập còn 3 tab.
**Vẫn chạy trên localStorage** — chưa nối API nào. Đúng ý report: sửa lúc còn rẻ.

---

## Bước 2 · Danh mục — F-06 → F-10

| Report | Task | Việc |
|---|---|---|
| F-06 | P1-T02 | M3: `tab_doc_type` · `tab_doc_type_link_rule` · `tab_external_party` |
| F-06 | P1-T07 | BE CRUD loại văn bản |
| F-06 | P1-T10 | FE form loại văn bản mở rộng (bỏ `has_template`, ẩn `needs_request` — quyết định 6 và 7) |
| F-07 | P1-T11 | FE danh mục 32 loại gom theo 6 nhóm A–F, nối react-query, bỏ `document-type-store.ts` |
| F-09 | P1-T09 | BE + FE phòng ban×pháp nhân (bảng đã tạo ở nền chung, đây là phần màn hình) |
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
| — | — | **Luồng duyệt một bước viết tay tạm** — một nút gửi duyệt, một người duyệt cấu hình cứng |

> ⚠️ **Vẫn phải dựng luồng tạm đó, đừng chờ nhánh A.** Quyết định 7 đã bỏ bước xin phép, nên nếu văn bản tạo xong là hiệu lực ngay thì không còn chốt chặn nào — đúng cái `00` mục 4.1 lo nhất.
>
> **Nhánh A viết lại ngày 14/08/2026 đã bỏ văn thư khỏi phạm vi.** Bộ máy phê duyệt giờ nhận **Thu mua** làm người dùng đầu tiên; trong 36 task của phase 3 **không còn task nào dành riêng cho văn thư**. Nghĩa là luồng tạm này sống lâu hơn dự tính ban đầu — cứ dựng cho tử tế, đừng dựng kiểu tạm bợ.
>
> Khi nào đấu văn thư vào bộ máy: **sau khi nhóm D (P3-T28 → P3-T31) chạy xong và bộ máy đã ổn ở prod với Thu mua.** Lúc đó văn thư đấu vào **theo đúng cách của P3-T31** (khai luồng → kiểm thử hai chế độ cờ → bật ở dev → bật prod). Đó là **task của nhánh B, chưa ai viết** — phải thêm vào phase 2 hoặc mở phase riêng, không mặc định có sẵn.

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

## Ngoài phạm vi plan này

| Report | Nội dung | Trạng thái |
|---|---|---|
| F-41 → F-50 | Ban hành, phạm vi áp dụng, clone xuống pháp nhân con (P4) | Chờ trả lời **B5** và **B6**, sẽ lên plan riêng |
| F-51 → F-64 | Quyền truy cập và tra cứu (P5) | Chạy song song được với nhánh A — hai mảng gần như không đụng nhau. Cần người thứ ba |

---

## Phần P0 chưa xếp vào nhánh nào — bắt buộc xong trước prod

Report liệt kê F-01…F-04 trong bảng P0. F-01/F-02/F-05 đã lên nền chung, F-03/F-04 vào 3b. **Sáu task còn lại của `phase-00`** chưa có chỗ:

| Task | Việc |
|---|---|
| P0-T05 | Cache quyền sang Redis + kênh xóa đệm tức thì |
| P0-T06 | Phạm vi phòng ban khớp bằng `department_id` |
| P0-T07 | Vá loại trừ phòng ban |
| P0-T08 | Vá nhật ký thao tác |
| P0-T09 | Grant MySQL append-only cho bảng nhật ký |
| P0-T13 | Guard `SCOPE_FIELDS` kèm danh sách miễn trừ 6 entity cũ |

Sáu task này **đụng thẳng vào lõi của hệ đang chạy**, không đụng gì tới việc dựng màn hình trên dev — nên chèn được vào bất cứ chỗ trống nào của nhánh nào, hoặc giao người thứ ba.

> **P0-T06 phải đi cùng P3-T09.** Cả hai cùng chuyển việc khớp phòng ban từ **chuỗi tên** sang **`department_id`**: P3-T09 thêm cột `department_id` vào phiếu Thu mua và điền ngược dữ liệu cũ, P0-T06 sửa `apply_scope` khớp theo cột đó. Làm lệch nhau thì nửa hệ khớp theo tên, nửa khớp theo id, và **không ai thấy sai** cho tới khi có người mất quyền xem phiếu của chính phòng mình. Một người làm cả hai, một lần.

> ⚠️ **Ràng buộc không thương lượng:** cho tới khi sáu task này xong và đã chạy prod ổn định — **không mở tài khoản văn thư trên prod, không đưa văn bản thật (nhất là văn bản mật) vào hệ thống.** Cả hai nhánh chỉ chạy trên dev với dữ liệu giả. Lý do đầy đủ ở `van-thu/00` mục 3.
>
> Ràng buộc thứ hai: **không mở prod khi luồng duyệt văn bản vẫn là luồng tạm một bước cấu hình cứng.** Nhánh A không còn nhận việc này (xem cảnh báo ở 3b), nên hoặc nhánh B tự làm luồng tạm đủ chắc để chạy thật, hoặc chờ đấu vào bộ máy sau P3-T31. Chọn đường nào cũng phải chốt trước khi bàn mở prod.

## Làm song song được

| Việc | Ai | Chờ gì |
|---|---|---|
| Nhập 32 loại văn bản, 13 mã pháp nhân, mã phòng ban | Hành chính | Xong bước 2 của nhánh B |
| Rà soát và số hóa văn bản giấy đang hiệu lực | Hành chính | **Không chờ gì** |
| 6 task P0 còn lại | Người thứ ba | Không chờ gì |
| F-51 → F-64 quyền và tra cứu (P5) | Người thứ ba | Chưa có plan, cần viết trước |
| Trả lời A1, B3, B6, B12 | Người quyết | — |
| **Trả lời 4 quyết định của P3-T01** | Hành chính / nhân sự | — · **chặn toàn bộ nhánh A**, hỏi trước tiên |
| Chuẩn bị **danh mục chức vụ** và **bảng phòng ban ↔ pháp nhân** ra giấy | Hành chính / nhân sự | Chờ quyết định a và b · nạp vào ở P3-T02 → P3-T05 |

## Câu hỏi chặn theo bước

| Câu | Chặn |
|---|---|
| **B3** — tên chính xác 4 mức mật | Nhánh B bước 1 (F-11). Nhẹ — sai thì sửa nhãn. **Nhánh A không còn dùng mức mật** sau khi viết lại: điều kiện rẽ nhánh giờ là số tiền · pháp nhân · phòng ban · chức vụ · cấp bậc · loại phiếu · gấp |
| **B6** — ai duyệt 32 mã loại + 13 mã pháp nhân | **Nhánh B bước 3a** — cấp số xong là P1-T05 khóa mã, không đổi được nữa. Chặn thật |
| **A1** — bản đầu có sổ văn bản đến không | Không chặn. Bảng tạo sẵn ở 3a, màn hình tạm ẩn từ bước 1 |
| **B12** — có loại thứ 33 *Trích lục* không | Nhánh B bước 3d, chỉ chặn trích lục chính thức (C20), không chặn bản trích nội bộ (C19) |

**Nhánh A giờ CÓ câu hỏi chặn** — khác với bản trước. Bốn quyết định của **P3-T01** chặn cứng toàn bộ nhóm A, mà nhóm A chặn cả 25 task còn lại:

| Câu | Chặn |
|---|---|
| **a** — một phòng ban thuộc **một** pháp nhân hay **nhiều** | P3-T04. Một thì thêm cột, nhiều thì phải có bảng nối — chọn sai là làm lại migration |
| **b** — danh mục chức vụ gồm những gì, **mấy cấp bậc** | P3-T02 · P3-T03. Không có danh sách thì không nạp được cho 244 người |
| **c** — "lên n cấp" leo theo **cây phòng ban** hay **cấp bậc chức vụ** | P3-T07 · P3-T18. Hai cách cho ra hai người duyệt khác nhau |
| **d** — `'Phòng Marketing'` là phòng **thật chưa khai** hay **gõ nhầm** | P3-T09. Thật thì khai thêm, nhầm thì sửa dữ liệu cũ |

Câu **a** và **b** phải hỏi **hành chính/nhân sự**, không tự quyết được. Hỏi sớm — đây là đường găng của cả nhánh A.
