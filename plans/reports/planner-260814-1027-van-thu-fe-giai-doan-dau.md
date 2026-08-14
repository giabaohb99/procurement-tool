# DS TÍNH NĂNG FRONTEND — VĂN THƯ GIAI ĐOẠN ĐẦU

> Nguồn: `van-thu/00`–`05` (bản đề xuất 13/08/2026, chưa duyệt) · hiện trạng `frontend-v2/src/modules/document`
> Phạm vi tệp này: **phần việc phía frontend-v2** cho bản 1 (132/174 tính năng của `01`).

---

## 1. Bộ van-thu nói gì — tóm 10 dòng

- Xây văn thư **thẳng trong mã nguồn Thu mua**, dùng lại tài khoản/nhân sự/pháp nhân/phân quyền/thông báo/kho tệp. 25 bảng mới + 4 bảng sửa (`04`).
- Bản 1 chạy đường: **yêu cầu văn bản → soạn → duyệt → ban hành → tra cứu**, kèm phiên bản, quan hệ cha–con, phạm vi áp dụng/clone xuống 13 pháp nhân, mức mật 4 cấp + chia sẻ/thu hồi.
- 10 phase (`02`): 0 vá nền · 1 danh mục+số hiệu · 2 soạn thảo+phiên bản · 3 bộ máy duyệt · 4 ban hành+clone · 5 quyền+tra cứu · 6 chạy thử · 7 prod · 8 chuyển Thu mua · 9 mở rộng.
- Phase 3 (bộ máy duyệt, 26 tính năng) và phase 5 (quyền, 24) là hai nhóm nặng nhất; **3 và 5 làm song song được**.
- Chặn cứng: 17 câu hỏi ở `00` mục 8 + 4 câu ở `05` mục 9 → chỉ chặn **từ phase 4 trở đi**; phase 0–3 làm được ngay.
- Nhóm **S (sổ văn bản đi/đến)** đang ở trạng thái `?` — **chờ câu A1**, và ở `02` xếp vào **phase 9**.
- Hai kiểu định danh: mã tài liệu bất biến `DEGO-QC-012` (quy chế/quy trình) và số hiệu theo sổ `08/2026/TB-NS-DEGO` (sự vụ).
- 4 mức mật chốt đề xuất: **Công khai · Nội bộ · Mật · Tuyệt mật** (`00` B3).
- Sửa văn bản đã ban hành có **hai cách không được dùng lẫn** (`05`): lên phiên bản 2.0 giữ mã (tài liệu hệ thống) · ra văn bản mới sửa đổi văn bản cũ (văn bản hành chính).
- Ràng buộc cứng cho FE: **khóa sửa/chặn gửi duyệt là ở tầng dịch vụ**, UI chỉ là tiện lợi; **không** có tùy chọn "không tìm thấy người duyệt thì tự duyệt qua".

---

## 2. Hiện trạng `frontend-v2`

Vite + React 19 + react-router 7 + TanStack Query + Tailwind v4 + shadcn (KHÔNG phải Next App Router như `.claude/rules/components.md` mô tả). Module `document` đã có:

| Đã có | Tệp |
|---|---|
| Tổng quan, danh sách, tạo mới, chi tiết văn bản | `pages/document-*-page.tsx` |
| Sổ văn bản đến/đi/nội bộ | `pages/document-book-page.tsx` |
| 4 danh mục nền chung một trang `?tab=`: loại văn bản · mức mật/khẩn · đối tác · trường động | `pages/document-settings-page.tsx` + 4 catalog |
| Form văn bản: thông tin chính/phụ, nơi nhận, xử lý, hiệu lực, ưu tiên, trường động, đính kèm, tự động lưu | `components/document-*` |
| Tự sinh số vào sổ + số hiệu theo (luồng × năm) | `helpers/document-number.ts` |
| Nhãn hiệu lực tính lúc hiển thị | `helpers/document-status.ts` |

Hạ tầng dùng lại được ngay: `shared/data-table` (resize/pin/drag/màu cột), `shared/conditional-filter`, `shared/ui/rich-text-editor` (tiptap + phân trang + bảng), `shared/audit`, `shared/notifications`, `shared/ui/mention-input`, `core/authorization` (`PermissionGate`, `usePermission`), `hr/components/role-permission-matrix`, `hr/components/user-scope-dialog`.

**Ba điểm phải chốt trước khi viết thêm dòng nào:**

1. **Chưa có backend** — cả module chạy trên `store/local-collection.ts` (localStorage). Mọi hook phải chuyển sang react-query khi API lên; kiểu dữ liệu đã đặt theo lối backend nên trang không phải sửa nhiều.
2. **`document` chưa có trong `ENTITIES`** của `core/permissions.py` → chưa gắn `entity` được, hiện ai đăng nhập cũng thấy phân hệ. Đây là việc phase 0 (N09).
3. **Mô hình đang lệch bộ van-thu.** Module hiện tại dựng theo **nhóm S — sổ đến/đi/nội bộ** (`direction`, `book_no`, `partner_id`, `processing_status`, `handler`), tức phần van-thu xếp **phase 9 / chờ A1**. Còn xương sống bản 1 (yêu cầu văn bản → phiên bản → quan hệ cha–con → phạm vi/clone → chia sẻ/thu hồi → luồng duyệt cấu hình được) thì **chưa có gì**. Thang mức mật hiện tại (Thường/Mật/Tối mật/Tuyệt mật + 4 mức khẩn) cũng khác đề xuất `00` B3 (Công khai/Nội bộ/Mật/Tuyệt mật).

---

## 3. Danh sách tính năng FE cho giai đoạn đầu

Cột **Tái dùng**: `[x]` có sẵn dùng ngay · `[~]` có nhưng phải sửa/mở rộng · `[ ]` làm mới.

### P0 · Vá nền (không sinh màn hình mới)

| # | Việc FE | Mã | Tái dùng |
|---|---|---|---|
| F-01 | Chuông lọc theo app đang mở (`app=vanthu`) | N08, M05 | `[~]` `shared/notifications` |
| F-02 | Màn phân quyền gom đối tượng theo phân hệ (28 → ~40 đối tượng) | N09 | `[~]` `hr/components/role-permission-matrix` |
| F-03 | Mọi chỗ xem/tải tệp gọi API sinh link tạm, bỏ dùng `file.url` | N02, N03 | `[~]` `document-attachment-list`, `procurement/document-attachments-card` |
| F-04 | Màn nhật ký thao tác đi qua kiểm quyền, không cho gọi trống mã bản ghi | N06, M03 | `[~]` `shared/audit` |
| F-05 | Gắn `entity: 'document'` (+ các entity con) vào `documentModule`, ẩn menu theo `can()` | N09 | `[~]` `modules/document/routes.tsx` |

### P1 · Danh mục và số hiệu

| # | Việc FE | Mã | Tái dùng |
|---|---|---|---|
| F-06 | Form loại văn bản mở rộng: kiểu định danh (mã bất biến / số theo sổ), mức mật mặc định, cần QĐ ban hành, chu kỳ rà soát, thời hạn lưu, luồng duyệt mặc định, tệp mẫu, bỏ qua bước yêu cầu | A01, A02, B06, D01, D06 | `[~]` `document-type-form` |
| F-07 | Nhập/hiển thị 32 loại theo 6 nhóm A–F (danh mục dài → cần nhóm + tìm) | A01 | `[~]` `document-type-catalog` |
| F-08 | Ô mã số hiệu cho pháp nhân và phòng ban; khóa không cho sửa sau khi đã cấp số | A04, A05, D07 | `[~]` `hr/company-form-dialog`, `hr/department-form-dialog` |
| F-09 | Màn "phòng ban tại từng pháp nhân" + trưởng phòng theo từng pháp nhân | A06 | `[ ]` |
| F-10 | Danh mục đối tác / cơ quan gửi nhận | A07 | `[x]` `document-partner-catalog` |
| F-11 | Sửa thang mức mật về 4 mức của `00` B3, tách khỏi thang độ khẩn | G03 | `[~]` `security-level-catalog` |
| F-12 | Hiển thị hai kiểu định danh trên bảng/chi tiết + xem trước số hiệu lúc soạn | D01, D08 | `[~]` `helpers/document-number.ts` (bỏ tự sinh phía client) |

### P2 · Yêu cầu, soạn thảo, phiên bản — khối nặng nhất của FE bản 1

| # | Việc FE | Mã | Tái dùng |
|---|---|---|---|
| F-13 | Form **yêu cầu văn bản**: 3 loại (soạn mới / sửa / bãi bỏ), lý do bắt buộc | B01 | `[ ]` |
| F-14 | Gợi ý văn bản cùng loại cùng phòng ban đang hiệu lực ngay trong form yêu cầu | B05 | `[ ]` |
| F-15 | Danh sách "yêu cầu của tôi" — đang chờ ai, bao lâu rồi | B07 | `[~]` `data-table` + `conditional-filter` |
| F-16 | Vào soạn thảo từ yêu cầu đã duyệt (nút + điền sẵn + link ngược về yêu cầu gốc) | B03, B04 | `[ ]` |
| F-17 | Form văn bản dựng lại theo bộ trường chung `C01` (pháp nhân ban hành, phòng chủ trì, người chịu trách nhiệm nội dung, ngày hiệu lực, mức mật, độ khẩn, từ khóa) | C01 | `[~]` `document-record-form` |
| F-18 | Tải tệp mẫu theo loại / tải bản đã điền lên | C02, C03 | `[~]` `document-attachment-list` |
| F-19 | Tab **phiên bản**: danh sách bản, bản đã duyệt chỉ đọc, mở bản để xem | C04, C07 | `[ ]` |
| F-20 | Dialog "mở phiên bản mới": bắt khai lý do sửa + chọn **sửa lớn / sửa nhỏ** | C05, C13, C15 | `[ ]` |
| F-21 | Chặn hai người cùng mở nháp: báo rõ ai đang giữ bản nháp | C14 | `[ ]` |
| F-22 | Băng cảnh báo trên bản cũ "đã bị thay thế bởi bản 2.0 ngày …" + nút sang bản mới; bản cũ không ẩn | C18 | `[ ]` |
| F-23 | Ngày hiệu lực riêng của phiên bản; bản cũ vẫn hiện "có hiệu lực" trong lúc bản mới đang duyệt | C16, C17 | `[ ]` |
| F-24 | Ô số hiệu cũ của văn bản giấy, tìm kiếm chấp nhận số cũ | C12 | `[~]` |
| F-25 | Màn soạn **bản trích nội bộ**: chọn phần nội dung từ bản gốc → sinh văn bản mới mức mật thấp hơn, chặn đặt mức cao hơn gốc | C19, E11 | `[~]` `rich-text-editor` |
| F-26 | Khối quan hệ cha–con trên form: **ô tự hiện theo quy tắc**, danh sách chọn lọc đúng loại đích + chỉ văn bản đang hiệu lực | E03 | `[ ]` |
| F-27 | Báo lỗi chặn gửi duyệt khi thiếu quan hệ bắt buộc (nêu rõ thiếu gì) | E04, E05 | `[ ]` |
| F-28 | **Cây tài liệu** trên trang chi tiết: quy trình → hướng dẫn → biểu mẫu, kèm trạng thái + phiên bản | E06 | `[ ]` |
| F-29 | Màn khai **quy tắc quan hệ theo loại** (~15–25 dòng: loại nguồn, quan hệ, loại đích, bắt buộc, số lượng, xử lý khi cha lên bản/bãi bỏ) | E01, E02, A03 | `[ ]` |
| F-30 | Màn OCR: ảnh gốc đặt cạnh bản nháp để đối chiếu; kết quả AI chỉ ghi vào nháp; ẩn sạch khi tắt cờ AI | L01, L02, L07 | `[ ]` |

### P3 · Bộ máy phê duyệt dùng chung

| # | Việc FE | Mã | Tái dùng |
|---|---|---|---|
| F-31 | **Trình khai luồng duyệt bằng giao diện** — bước tuần tự, vai trò bước, 6 cách chọn người duyệt, rẽ nhánh theo điều kiện, 3 chế độ nhiều người, 3 mức bỏ qua khi trùng thao tác, người thay thế. Không có ô "tự động duyệt qua" | I01–I07 | `[ ]` màn nặng nhất |
| F-32 | Panel duyệt trên phiếu: duyệt / từ chối / trả lại (chọn bước) / rút lại — **bắt nhập lý do** | I08–I11 | `[~]` `procurement/document-comments` |
| F-33 | Ý kiến + tệp đính kèm khi duyệt, người nhận bản sao | I15, I16 | `[~]` `mention-input` |
| F-34 | **"Việc của tôi"** — gom việc chờ của cả văn thư và thu mua vào một chỗ | I17 | `[ ]` |
| F-35 | Hiện hạn duyệt / quá hạn / đã leo cấp trên phiếu và trong danh sách | I18 | `[~]` |
| F-36 | Màn ủy quyền có thời hạn; dấu vết ghi cả hai danh tính "B duyệt thay A" | I12, M04 | `[ ]` |
| F-37 | Bản in dấu vết duyệt | I20 | `[~]` mẫu `purchase-order-print-page` |
| F-38 | Hiện phiên bản luồng đang chạy trên phiếu (sửa luồng không đổi phiếu đang chạy) | I21 | `[ ]` |
| F-39 | Bàn giao hàng loạt khi nghỉ việc (chọn nhiều phiếu → chuyển người) | I23 | `[ ]` |
| F-40 | Màn bật/tắt cờ bộ máy duyệt theo từng loại chứng từ | I26 | `[ ]` |

### P4 · Ban hành, phạm vi, clone

| # | Việc FE | Mã | Tái dùng |
|---|---|---|---|
| F-41 | Thanh vòng đời văn bản (nháp → đang duyệt → đã duyệt → hiệu lực → thay thế/hết hiệu lực/bãi bỏ → lưu trữ) | J01 | `[~]` `form-stepper`, `document-status-badge` |
| F-42 | Màn ban hành: cấp số, ký điện tử nội bộ, **ghi rõ loại chữ ký** (nội bộ ≠ ký số pháp lý) | J02, J03, J04 | `[ ]` |
| F-43 | **Trình dựng phạm vi áp dụng**: 3 kiểu (pháp nhân/phòng ban/cá nhân), bao gồm + loại trừ, bắt buộc kèm pháp nhân khi chọn phòng ban, cờ "gồm đơn vị con" | F01–F04 | `[~]` mẫu `hr/user-scope-dialog` |
| F-44 | Màn chọn cơ chế lúc ban hành: **một văn bản gắn phạm vi** (mặc định) hay **clone xuống từng pháp nhân**, có giải thích ngắn khác nhau chỗ nào | F13 | `[ ]` |
| F-45 | Dialog clone: chọn nhiều pháp nhân con → sinh nháp riêng; hiện liên kết ngược *căn cứ theo* **không có nút xóa** | F06, F07, F08 | `[ ]` |
| F-46 | **Bảng theo dõi clone**: 13 công ty con đang ở phiên bản nào, ai đã ban hành / còn nháp / chưa đụng / lệch bản | F10, F11 | `[ ]` |
| F-47 | Màn "văn bản áp dụng cho tôi" + thông báo theo phạm vi | F05, J05 | `[ ]` |
| F-48 | Nhãn **"đã bị sửa đổi bởi …"** trên văn bản hành chính — bắt buộc hiện, có link sang văn bản sửa đổi | J10 | `[ ]` |
| F-49 | Dialog cảnh báo tác động khi sửa/bãi bỏ văn bản cha: liệt kê con + hỏi xử lý (hệ thống không tự sửa) | E07, E08 | `[ ]` |
| F-50 | Kiểm "phải kèm Quyết định ban hành" ở mức từng phiên bản | J11 | `[ ]` |

### P5 · Quyền truy cập và tra cứu

| # | Việc FE | Mã | Tái dùng |
|---|---|---|---|
| F-51 | Cấp **mức mật cho từng người**, có hạn + nút gia hạn | G04 | `[~]` `hr/user-permission-detail-page` |
| F-52 | Dialog **chia sẻ đích danh** (người/phòng/pháp nhân/vai trò), cho phép + cấm, có hạn | G05, G06 | `[ ]` |
| F-53 | Màn quản lý **nhóm chia sẻ tự đặt** | G14 | `[ ]` |
| F-54 | **Màn 4 lựa chọn** khi người nhận không đủ mức mật (nâng mức người · chia đặc cách có hạn · hạ mức văn bản · tách bản trích), mỗi cách nêu rõ hệ quả — **không hiện "không đủ quyền" rồi hết** | G16 | `[ ]` |
| F-55 | Luồng chia đặc cách: lý do + hạn + người duyệt | G15 | `[ ]` |
| F-56 | Luồng hạ mức mật văn bản qua duyệt | G17 | `[ ]` |
| F-57 | Bảng chia sẻ trên trang chi tiết: đang chia cho ai, hết hạn khi nào; **thu hồi là đánh dấu, không xóa dòng** | G19, G20 | `[ ]` |
| F-58 | Bấm thu hồi → hiện ngay **ai đã kịp tải tệp về** | G21 | `[ ]` |
| F-59 | **Trình xem Tuyệt mật**: chỉ xem trên web, không nút tải, dấu chìm mang tên người xem + thời điểm | G09 | `[ ]` |
| F-60 | Nhật ký chia sẻ/thu hồi (chỉ thêm, không sửa xóa) | G24 | `[~]` `shared/audit` |
| F-61 | Danh sách + bộ lọc văn bản theo pháp nhân/loại/phòng/trạng thái/mức mật/khoảng ngày/người phụ trách | K01 | `[~]` `conditional-filter` + `data-table` |
| F-62 | Tìm theo tiêu đề, số hiệu, số hiệu cũ; **kết quả không lộ cả tiêu đề văn bản không được xem** | K02, K03 | `[~]` |
| F-63 | Trang chi tiết đủ tab: thông tin · phiên bản · quan hệ cha con · phạm vi · dấu vết duyệt · bản clone · chia sẻ | K04 | `[~]` `document-detail-page` |
| F-64 | Trang chủ theo vai: việc của tôi · văn bản áp dụng cho tôi · mới ban hành · sắp hết hiệu lực | K06 | `[~]` `document-dashboard-page` |

**Tổng: 64 hạng mục FE** — `[x]` 1 · `[~]` 24 · `[ ]` 39.

---

## 4. Việc phải quyết với phần đã dựng trong `frontend-v2`

| # | Việc | Đề nghị |
|---|---|---|
| 1 | Màn **Sổ văn bản đến/đi** đã dựng nhưng van-thu xếp phase 9 / chờ A1 | Giữ mã, **tạm ẩn khỏi menu** cho tới khi có câu A1; không phát triển tiếp trong bản 1 |
| 2 | `DocumentRecord` hiện xoay quanh `direction` + `book_no` + `partner_id` | Đổi trục sang **loại văn bản + pháp nhân ban hành + phiên bản**; `direction` hạ xuống thành một thuộc tính, không phải khóa phân loại |
| 3 | Thang mức mật 4 mức hành chính VN + 4 mức khẩn | Đổi thang mật theo `00` B3 (Công khai/Nội bộ/Mật/Tuyệt mật), giữ nguyên thang khẩn |
| 4 | Tự sinh số hiệu ở client (`nextBookNo` lấy MAX+1) | **Bỏ hẳn** — `00` mục 4.2 cấm `MAX+1`; số do backend cấp trong giao dịch có khóa dòng. Client chỉ **xem trước** (D08) |
| 5 | `store/local-collection.ts` (localStorage) | Thay bằng react-query ngay khi API phase 1 lên; kiểu dữ liệu giữ nguyên |
| 6 | `document` chưa có entity phân quyền | Thêm entity + gắn `PermissionGate` trước khi mở cho người thật |
| 7 | `trường thông tin động` đang là danh mục riêng | Giữ — không xung đột với van-thu, nhưng **không dùng nó thay cho bộ trường chung C01** |

---

## 5. Thứ tự làm phía FE

1. **F-05, F-11, F-12, mục 4.1–4.4** — nắn lại nền module hiện có trước khi đắp thêm. Rẻ nhất lúc dữ liệu còn nằm ở localStorage.
2. **F-06 → F-10** (danh mục) — chạy được ngay khi API phase 1 lên.
3. **F-13 → F-30** (yêu cầu + soạn thảo + phiên bản) — khối lớn nhất, cho người thật bấm thử sớm nhất.
4. **F-31 → F-40** ‖ **F-51 → F-64** — hai nhánh song song, gần như không đụng file nhau (`02` mục 14).
5. **F-41 → F-50** — chờ xong F-31.

FE làm trước backend được: F-29 (màn quy tắc), F-31 (trình khai luồng), F-43 (trình dựng phạm vi), F-54 (màn 4 lựa chọn) — bốn màn này quyết định hình dạng API, nên dựng bản tương tác trước rồi mới chốt schema thì rẻ hơn.

---

## 6. Câu hỏi chưa giải quyết

1. **A1** — bản đầu có sổ văn bản đến không? Trả lời được thì mới biết giữ hay bỏ 2 màn đã dựng (`document-book-page`, phần `direction`/`partner`).
2. **B1** — "form chuẩn" là mẫu Word tải về (C02) hay form nhập trên web (C09)? Chênh nhau vài tháng công FE.
3. **B3** — chốt 4 mức mật nào? Đang lệch giữa `frontend-v2` và `00`.
4. Module `document` hiện tại do ai đặt hàng, có ràng buộc gì với người dùng đã xem demo chưa? Nếu đã hứa giao sổ đến/đi thì mục 4.1 phải xử lý khác.
5. `frontend-v2` đã được chốt là frontend chính thức thay `frontend/` chưa? Cả bộ van-thu không nhắc tới `frontend-v2` một chữ nào — `01` vẫn giả định dùng lại màn hình của Thu mua hiện tại.
