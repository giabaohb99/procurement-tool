# Kế hoạch nhân sự: định biên và chi phí nhân sự theo kỳ

> ⛔ **ĐÃ BỎ — 29/10/2026 (duoc-CR-692, anh Được).** Toàn bộ Kế hoạch nhân sự (màn, mẫu / nhóm khoản chi phí, API, bảng dữ liệu, báo cáo «Số người kế hoạch so với thực tế» khóa 25, cột kế hoạch của Quỹ lương) đã gỡ. Lý do: lương nhập ở tab Hợp đồng lao động của chi tiết nhân sự là đủ; báo cáo Quỹ lương cộng lương từng người ra quỹ lương phòng ban · pháp nhân · toàn công ty. Tài liệu này chỉ giữ làm lịch sử thiết kế — **không làm lại theo đây** nếu chưa có chốt mới.


| | |
|---|---|
| Bản | 1.1 — 28/10/2026 (thêm Văn bản liên kết sang phân hệ Văn bản) · 1.0 — 28/10/2026 (thiết kế lại sau khi anh Được soát bản đợt 4: form quá ít thông tin, quỹ lương tính theo tháng là sai, chi phí phải do người dùng tự định nghĩa) |
| Tình trạng | **Đã code ở local (duoc-CR-690, 28/10/2026), chưa lên dev.** Thay bản đợt 4 (duoc-CR-689: một dòng năm × pháp nhân × phòng với hai số «định biên», «quỹ lương / tháng» — hai cột này đã bỏ, dữ liệu cũ đã dời sang khuôn mới) |
| Màn | Nhân sự ▸ Danh mục ▸ **Kế hoạch nhân sự** (`/hr/headcount-plans`) |
| Báo cáo dùng số này | A4 «Định biên kế hoạch so với thực tế» và A5 «Quỹ lương theo pháp nhân» (`05-bao-cao-nhan-su.md`) |
| Mã nguồn hiện có | `backend/app/modules/headcount_plan/` · `frontend-v2/src/modules/hr/pages/headcount-plan-list-page.tsx` |

> ⚠️ **Đọc §10 trước (28/10/2026):** giao diện cuối cùng là **form 3 khối** (Người và lương · Chi phí khác · Tổng). Các màn «Mẫu khoản chi phí», «Nhóm chi phí», ô chọn mẫu và hộp thoại khoản tả ở §2.2, §4.1 **đã gỡ khỏi menu** — bảng dữ liệu, API và 5 cách tính ở backend vẫn giữ; kế hoạch mới tự lấy «Mẫu gợi ý».

Không trái chốt 16/10/2026 «không làm chấm công, không tính lương»: đây là **dự toán chi phí nhân sự** để duyệt và so sánh, không tính lương tháng, không làm phiếu lương.

---

## 1. Bài toán

Trưởng phòng Nhân sự cần trình Ban Giám đốc, rồi theo dõi:

- mỗi pháp nhân, mỗi phòng được bao nhiêu người, **ở vị trí nào**, tuyển dần theo lộ trình nào;
- chi phí nhân sự của từng kỳ (quý, bán niên, năm) là bao nhiêu, **gồm những khoản gì**;
- **căn cứ** của từng con số: quyết định nào duyệt, ai duyệt, lý do;
- tới kỳ thì so với thực tế: thiếu hay thừa người, còn dư hay vượt chi phí.

Bản đợt 4 sai ở bốn chỗ:

1. Chỉ có một số tổng cho cả phòng, không có vị trí;
2. Quỹ lương là một số «mỗi tháng» rồi nhân lên. Trong khi chi phí từng kỳ khác nhau: người vào giữa kỳ, tăng lương từ một tháng, thưởng rơi vào một tháng, trần BHXH đổi từ 01/7;
3. Chỉ có lương + phụ cấp, các khoản khác (bảo hiểm công ty đóng, kinh phí công đoàn, thưởng, phúc lợi) bị bỏ sót, nên kế hoạch thiếu khoảng 30%;
4. Không có căn cứ.

## 2. Bố cục form

Một kế hoạch = **một kỳ × một pháp nhân × một phòng ban** (hoặc «Toàn pháp nhân»). Form gồm bốn khối.

### 2.1. Khối Kỳ và Căn cứ

| Ô | Bắt buộc | Ghi chú |
|---|---|---|
| **Loại kỳ** | Có | **Năm · Bán niên · Quý · Tháng**: người dùng chọn, form đổi theo (§3) |
| **Kỳ** | Có | Ví dụ 2026 · H2-2026 · Q3-2026 · 07/2026 |
| Pháp nhân · Phòng ban | Có | Phòng ban dùng chung cho mọi pháp nhân, như bản hiện tại |
| **Mẫu khoản chi phí** | Có | Chọn mẫu, hệ thống chép bộ khoản vào kế hoạch (§4) |
| **Số căn cứ** | Không | Ví dụ «12/QĐ-BGĐ» |
| **Ngày căn cứ** | Không | |
| **Người duyệt** | Không | Chọn nhân sự |
| **Văn bản liên kết** | Không | Chọn văn bản **có sẵn ở phân hệ Văn bản** (quyết định duyệt ngân sách, tờ trình, biên bản). Hiện số / ký hiệu, trích yếu, trạng thái; bấm mở sang trang văn bản. Liên kết được nhiều văn bản. Nút **«Tải tệp lên»**: chọn tệp (quyết định, tờ trình…) → hệ thống **tự tạo văn bản** loại «Căn cứ kế hoạch nhân sự» (`CCKHNS`) có tệp đó rồi thêm vào danh sách (dùng được cả lúc tạo mới) |
| **Tệp đính kèm** | Không | Bảng tính gốc, tệp lẻ chưa vào Văn bản. Dùng kho tệp chung |
| **Lý do / ghi chú** | Không | Ví dụ «Mở thêm mảng kế toán thuế» |

### 2.2. Khối Khoản chi phí của kế hoạch này

Bộ khoản đã chép từ mẫu. Ở đây được thêm, bớt khoản hoặc đổi tỷ lệ mà không ảnh hưởng mẫu hay kế hoạch khác (§4).

### 2.3. Khối Định biên theo vị trí

Mỗi dòng là một **vị trí** (danh mục Chức vụ), hoặc một dòng «Không theo vị trí» cho ai chỉ muốn nhập tổng phòng.

| Cột | Ghi chú |
|---|---|
| Vị trí | Danh mục Chức vụ (`tab_job_position`) |
| **Định biên theo kỳ con** | Số cột đổi theo loại kỳ (§3). Ví dụ Năm: Q1 · Q2 · Q3 · Q4 |
| **Đang có** | Hệ thống đếm: người đang làm có đúng pháp nhân × phòng × vị trí. Chỉ đọc |
| **Cần tuyển** | Định biên kỳ con cuối − Đang có. Chỉ đọc |
| **Một cột cho mỗi khoản «nhập theo vị trí»** | Mọc theo khối 2.2. Ví dụ Lương vị trí, PC chức vụ, Ăn trưa |
| Gợi ý | Bên cạnh ô lương hiện *bình quân hiện tại* của vị trí đó, lấy từ HĐLĐ, để nhập có căn cứ. Chỉ hiện với người được xem lương |

### 2.4. Khối Hệ thống tự tính (chỉ đọc)

Một bảng theo các kỳ con của kỳ đã chọn, cộng thêm cột Tổng kỳ. Mỗi **nhóm** khoản một dòng, bấm mở ra từng khoản. Dưới cùng là Tổng chi phí nhân sự, Định biên cuối kỳ con và Bình quân / người. Với kỳ đã qua hoặc đang chạy thì có thêm dòng **Thực tế** và **Còn dư / vượt** (§6).

## 3. Loại kỳ: form đổi theo lựa chọn

| Loại kỳ | Kỳ con (cột định biên + cột bảng tự tính) | «Rơi vào tháng» của khoản chi phí chọn trong |
|---|---|---|
| Năm | Q1 · Q2 · Q3 · Q4 | T1 – T12 |
| Bán niên | 2 quý của nửa năm đó | 6 tháng của nửa năm |
| Quý | 3 tháng của quý | 3 tháng của quý |
| Tháng | (một cột) | tháng đó |

- **Bên trong luôn tính theo từng tháng.** Định biên kỳ con áp cho mọi tháng trong kỳ con. Khoản tính theo tháng cộng từng tháng. Khoản «rơi vào tháng» chỉ cộng ở tháng đó. Rồi mới gộp lên kỳ con và tổng kỳ. Làm vậy thì chi phí Q2 là chi phí thật của Q2, không phải 1/4 của năm.
- **Kỳ hẹp thay kỳ rộng.** Đã có kế hoạch Năm 2026, sau đó lập thêm kế hoạch Q3-2026 cho cùng pháp nhân × phòng: báo cáo dùng số của Q3-2026 cho các tháng 7–9, các tháng khác vẫn theo kế hoạch năm. Đây là cách **điều chỉnh giữa năm** mà không đè mất kế hoạch gốc. Hai kế hoạch cùng loại, cùng kỳ, cùng pháp nhân × phòng thì bị chặn (trùng).
- Báo cáo A4 / A5 xem theo kỳ nào (tháng, quý, năm, tùy chọn) thì cộng đúng các tháng của kỳ đó từ kế hoạch có hiệu lực ở từng tháng.

## 4. Khoản chi phí: người dùng tự định nghĩa

Mã nguồn **không ghi cứng khoản nào**: không ghi cứng 17,5%, không ghi cứng «thưởng tháng 13».

### 4.1. Mẫu khoản chi phí

Màn riêng: Nhân sự ▸ Danh mục ▸ **Mẫu khoản chi phí**. Mỗi mẫu là một bộ khoản, ví dụ «Mẫu văn phòng», «Mẫu nhà máy», «Mẫu cửa hàng». Mỗi khoản khai:

| Ô | Giá trị |
|---|---|
| **Tên khoản** | Tự đặt |
| **Nhóm** | Danh mục **Nhóm chi phí** do người dùng tự đặt (gợi ý sẵn: Quỹ lương · Bắt buộc theo luật · Phúc lợi · Khác) |
| **Cách tính** | Một trong 5 cách ở §4.2 |
| **Áp cho** | Mọi vị trí · chỉ các vị trí đã chọn · cả phòng (không theo người) |
| **Rơi vào** | Mỗi tháng · các tháng đã chọn (vd T3, T12) |
| Thứ tự | Để sắp xếp trên form |

### 4.2. Năm cách tính

| Mã | Cách tính | Công thức một tháng | Ví dụ |
|---|---|---|---|
| 1 | **Số tiền / người / tháng, nhập theo vị trí** | số người của vị trí × số tiền nhập ở cột của khoản đó | Lương vị trí, PC chức vụ, ăn trưa |
| 2 | **% trên các khoản khác** (chọn khoản gốc, có trần / người nếu cần) | Σ người × min(tổng khoản gốc / người, trần) × % | BHXH 17,5% × (Lương + PC chức vụ), trần 50,6 tr; KPCĐ 2% |
| 3 | **Số tháng của một khoản** | số người × hệ số × khoản gốc / người | Thưởng tháng 13 = 1 × Lương, rơi vào T12 |
| 4 | **Số tiền / người / lần** | số người × số tiền, chỉ ở tháng «rơi vào» | Quà 8/3 500k, khám sức khỏe 1,5 tr |
| 5 | **Số tiền cả phòng** | số tiền, chia đều cho các tháng «rơi vào» | Du lịch 50 tr ở T6, chi phí tuyển dụng |

- Khoản % chỉ được trỏ tới khoản cách tính 1 hoặc 3, để không có vòng lặp tham chiếu. Lưu thì kiểm.
- Trần nhập tay ở từng khoản. Ví dụ 46,8 tr cho kế hoạch nửa đầu 2026, 50,6 tr từ 01/7/2026. Người dùng tự cập nhật khi luật đổi; mã không nhớ con số nào.
- Số người dùng cho tháng m = định biên kỳ con chứa tháng m.

### 4.3. Chép vào từng kế hoạch

- Tạo kế hoạch thì chọn mẫu: hệ thống **chép** toàn bộ khoản vào kế hoạch đó (bản chụp).
- Trong kế hoạch được sửa tự do; mẫu và kế hoạch khác không đổi.
- Sửa mẫu về sau: các kế hoạch đã lập **giữ nguyên**, nên con số đã duyệt không tự trôi.
- Hệ thống gieo sẵn **một mẫu gợi ý** cho người dùng sửa: Lương vị trí · PC đóng BH · PC không đóng BH · BHXH công ty 17,5% · BHYT 3% · BHTN 1% · KPCĐ 2% · Thưởng tháng 13. Mẫu này là **dữ liệu**, không phải mã; xóa hay sửa đều được.

## 5. Ví dụ: Kế toán · AGRIPLANT · Năm 2026

| Vị trí | Q1 | Q2 | Q3 | Q4 | Lương / người | PC chức vụ | Ăn trưa |
|---|---|---|---|---|---|---|---|
| Kế toán trưởng | 0 | 1 | 1 | 1 | 25 tr | 3 tr | 730k |
| Kế toán viên | 4 | 4 | 5 | 5 | 12 tr | 1 tr | 730k |

Khoản của kế hoạch: Lương (1) · PC chức vụ (1) · Ăn trưa (1) · BHXH 17,5% × (Lương + PC chức vụ), trần 46,8 tr (2) · BHYT 3% (2) · BHTN 1% (2) · KPCĐ 2% (2) · Thưởng tháng 13 = 1 × Lương, T12 (3) · Quà 8/3 500k / người, T3 (4).

Hệ thống tính từng tháng rồi gộp ra Q1 · Q2 · Q3 · Q4 · Năm, mỗi nhóm một dòng. Ví dụ Q1: 4 kế toán viên × 3 tháng × (12 + 1 + 0,73) tr + 23,5% × 13 tr × 4 × 3 + quà 8/3 (4 × 500k)…

## 6. So với thực tế

Thực tế chỉ lấy được từ **HĐLĐ đang hiệu lực** (`base_salary`, `allowance`, `insurance_salary`), vì ERP không có bảng lương. Mỗi khoản có thêm ô **«Lấy thực tế từ»**:

| Giá trị | Nghĩa |
|---|---|
| Không có | Khoản chỉ có số kế hoạch (thưởng, phúc lợi…) |
| Lương cơ bản trên HĐ | |
| Phụ cấp trên HĐ | |
| % × Lương đóng BHXH trên HĐ | Dùng đúng % và trần của khoản đó |

Dòng **Thực tế** chỉ cộng các khoản có nguồn, và ghi rõ «thực tế chưa gồm: …» để không ai so táo với cam. Số người thực tế đếm theo pháp nhân × phòng × vị trí, theo từng tháng.

## 7. Quyền

- Giữ khóa `headcount_plan`: đọc, tạo, sửa, xóa, xuất. Ghi chỉ trưởng phòng Nhân sự và admin (chốt 28/10).
- **Mọi số tiền** (cột khoản ở 2.3, bảng tự tính, gợi ý bình quân) chỉ hiện với người đọc được HĐLĐ của đúng pháp nhân đó ở phạm vi Tất cả hoặc Công ty, như luật đang chạy. Người khác chỉ thấy định biên và căn cứ.
- Mẫu khoản chi phí và Nhóm chi phí là danh mục không chứa lương ai. Đọc theo `headcount_plan.read`, sửa theo `headcount_plan.write`.

## 8. Dữ liệu (phác, chốt khi viết plan)

| Bảng | Nội dung |
|---|---|
| `tab_hr_cost_group` | Nhóm chi phí do người dùng đặt |
| `tab_hr_cost_template` · `tab_hr_cost_template_item` | Mẫu và khoản của mẫu |
| `tab_headcount_plan` (mở rộng) | + `period_type` SMALLINT (`IntEnum`: 1 Năm · 2 Bán niên · 3 Quý · 4 Tháng), `period_no`, các ô căn cứ, `template_id` (chỉ để biết đã chép từ đâu) |
| `tab_headcount_plan_cost_item` | Khoản đã chép vào kế hoạch: nhóm, `calc_method` SMALLINT (1–5), %, hệ số, trần, khoản gốc, áp cho, tháng rơi vào, nguồn thực tế |
| `tab_headcount_plan_line` | Vị trí × định biên từng kỳ con × số tiền các khoản nhập theo vị trí |

| `tab_headcount_plan_document` | Kế hoạch × văn bản liên kết (`plan_id`, `document_id`), duy nhất theo cặp |

**Văn bản liên kết và quyền:** chỉ chọn được văn bản mà người lập **đọc được** (luật đọc của phân hệ Văn bản: `document/access_service`). Người xem kế hoạch mà không đọc được văn bản đó thì chỉ thấy «Văn bản bạn chưa được xem», không lộ số, trích yếu hay tệp. Văn bản bị xóa thì liên kết hiện «Văn bản đã xóa». Kế hoạch không cấp thêm quyền đọc văn bản cho ai.

**Tải tệp lên (`POST /api/headcount-plans/documents/upload`, multipart `file` + `title` tùy chọn):** gác `headcount_plan.write` HOẶC `create` + `document.read`. Tạo văn bản loại `CCKHNS` (mã bất biến cấp ngay, ví dụ `DEGO-CCKHNS-001`; pháp nhân / phòng lấy từ hồ sơ người tải; thư mục mặc định của pháp nhân; không sổ, không duyệt, không ký), phiên bản 1.0 có đúng tệp tải lên, trích yếu mặc định «Căn cứ kế hoạch nhân sự – <tên tệp>». Loại bật `is_personal` nên văn bản **kín**: phạm vi vai trò (kể cả «công ty») không mở được; chỉ người tạo, người được chia đích danh, người duyệt và vai trò phạm vi «tất cả» đọc. Luật tệp (đuôi, 50 MB, byte đầu) là của đính kèm Văn bản. Người dùng tải rồi không lưu kế hoạch thì văn bản vẫn nằm ở phân hệ Văn bản của người đó (chấp nhận, xóa tay được). Người sửa kế hoạch **gỡ được** cả liên kết tới văn bản mình không đọc được (gỡ không làm lộ nội dung; kế hoạch thuộc quyền người lập).

Mọi cột loại / cách tính lưu **SMALLINT + IntEnum** (luật R2). Không lưu chữ tiếng Việt cho trạng thái.

**Dời dữ liệu đợt 4:** mỗi dòng cũ thành kế hoạch loại Năm, có một dòng «Không theo vị trí» với định biên 4 quý bằng nhau, và một khoản «Quỹ lương (nhập tổng)» cách tính 5 bằng 12 × số cũ. Hai báo cáo A4, A5 đọc bảng mới. CSV xuất/nhập làm lại theo khuôn mới.

## 9. Chưa làm trong bản này (ghi để khỏi quên)

- Trạng thái duyệt trên hệ thống (Nháp → Trình → Đã duyệt). Bản này chỉ ghi căn cứ duyệt ngoài hệ thống.
- Khoản «chỉ áp cho nữ» (quà 8/3 theo giới tính trong vị trí): kế hoạch chưa có giới tính của người sẽ tuyển.
- Sao chép kế hoạch từ kỳ trước, tăng x%.
- Cảnh báo khi tạo hồ sơ / ký HĐ làm vượt định biên hay vượt chi phí.

## 10. Đã làm (duoc-CR-690)

- **Màn:** Nhân sự ▸ Danh mục ▸ **Kế hoạch nhân sự** (danh sách + trang riêng bốn khối), **Mẫu khoản chi phí**, **Nhóm chi phí**. Có sẵn «Mẫu gợi ý» 8 khoản và 4 nhóm, đều là dữ liệu (sửa / xóa được).
- **Bộ tính** `modules/headcount_plan/costing.py`: tính từng tháng, gộp kỳ con. Xem trước khi đang nhập qua `POST /api/headcount-plans/compute`.
- **Tạo từ mẫu cho kỳ không phải Năm:** khoản mà mọi tháng «rơi vào» đều ngoài kỳ thì bị bỏ khi chép (kèm khoản trỏ vào nó), và form báo rõ đã bỏ khoản nào.
- **Trang kế hoạch đã lưu:** có dòng Thực tế / Còn dư theo kỳ con. Kỳ con đang chạy chỉ so các tháng đã bắt đầu (so cùng số tháng ở cả kế hoạch lẫn thực tế). Kỳ con tương lai để trống.
- **«Đang có» của kế hoạch Toàn pháp nhân** đếm cả pháp nhân.
- **A4:** định biên kế hoạch = định biên của tháng cuối kỳ báo cáo, theo kế hoạch có hiệu lực ở tháng đó (kỳ hẹp thay kỳ rộng). Có thêm «Xem theo» Vị trí. Người ở vị trí kế hoạch không khai rơi vào «(Chưa gắn)».
- **A5:** năm chỉ số: Chi phí nhân sự kế hoạch (mọi tháng của kỳ báo cáo), Kế hoạch phần so được, Thực tế phần so được (các tháng đã bắt đầu, theo «Lấy thực tế từ» của từng khoản), Còn dư, % dùng. Không khoản nào có nguồn thực tế thì ba chỉ số sau để trống, không phải 0.
- **Tệp đính kèm** của kế hoạch chỉ liệt kê / tải được với người xem được tiền của pháp nhân đó, vì tệp có thể chứa bảng tính chi phí.
- **Văn bản liên kết** theo luật đọc của phân hệ Văn bản.
- **Người xem thấy thiếu một phần HĐ** (vd quyền HĐLĐ loại trừ một phòng mà xem kế hoạch toàn pháp nhân): không so Thực tế, ghi «Không so thực tế: bạn chỉ được xem hợp đồng của một phần nơi này». Phòng bị loại trừ thì kế hoạch của phòng đó ẩn hết tiền.
- **Người không xem được tiền** chỉ sửa được định biên, vị trí, căn cứ, văn bản; đổi cấu trúc khoản chi phí bị chặn.
- Nhóm trên bảng tự tính xếp theo ô «Thứ tự» của Nhóm chi phí. Mẫu và nhóm: thêm / nhân bản cần quyền thêm, sửa cần quyền sửa, xóa cần quyền xóa.
- **Giao diện khoản chi phí tối giản (28/10/2026, anh Được «nhiều quá loạn»):** mỗi khoản một dòng (tên + câu mô tả). Hộp thoại chỉ có Tên và «Tính thế nào»: **Hằng tháng theo người** (ô «Số tiền mỗi người mỗi tháng» = MỨC CHUNG lưu ở `amount`; ô tiền của vị trí trống / 0 thì dùng mức chung, > 0 thì số riêng thắng), **Phần trăm trên lương** (Tỷ lệ %, Tối đa đ/người; luôn tính trên MỌI khoản hằng tháng), **Theo đợt** (Chi vào tháng + Mức: mỗi người · cả phòng · số tháng lương). Không còn mục «Nâng cao»: mã, nhóm (theo cách tính), nguồn thực tế, áp cho, thứ tự hệ thống tự đặt. Khoản cũ có cấu hình riêng được giữ nguyên, có nhãn riêng. Màn **Nhóm chi phí đã gỡ** khỏi menu (bảng dữ liệu còn, hệ thống tự gán). «Mẫu gợi ý» gọn còn 4 khoản (Lương, Phụ cấp, Bảo hiểm + công đoàn 23,5% trần 50,6 tr, Thưởng tháng 13) — `hcplan04` thay bộ 8 khoản cũ nếu mẫu chưa bị sửa. Chữ «Định biên» đổi thành **«Số người kế hoạch»** ở màn kế hoạch và báo cáo A4. **Văn bản liên kết** có nút «Tải tệp lên»: tự tạo văn bản loại «Căn cứ kế hoạch nhân sự» (`CCKHNS`, cá nhân + mật) ở phân hệ Văn bản rồi gắn vào kế hoạch; khối «Tệp đính kèm» riêng đã bỏ khỏi trang. Mô hình dữ liệu và 5 cách tính ở §4 không đổi.
- **Form 3 khối (28/10/2026, anh Được chốt sau khi thấy «khoản chi phí / cách tính» khó hiểu) — thay §2.2, §2.3 ở phía giao diện:** ① **Người và lương**: Vị trí · Hiện có · Cần có theo kỳ con · Cần tuyển · Lương/người (khoản `LUONG`) · Phụ cấp/người (`PHU_CAP`); «+ Thêm vị trí» (tìm chức vụ), «+ Nhập tổng cả phòng», «Giống nhau cả năm». ② **Chi phí khác**: mỗi khoản một câu có ô số + bật/tắt — «% trên lương» (cách 2, tính trên mọi khoản lương/phụ cấp), «Số tháng lương» (cách 3), «Theo đợt mỗi người» (cách 4), «Cả phòng» (cách 5). ③ **Tổng (tự tính)**: Số người · Lương + phụ cấp · Bảo hiểm · Thưởng, quà, chi khác · TỔNG (gom theo cách tính, không theo nhóm) + Thực tế / Còn dư. Không còn ô chọn mẫu: kế hoạch mới tự lấy «Mẫu gợi ý». Màn «Mẫu khoản chi phí» và «Nhóm chi phí» gỡ khỏi menu (bảng dữ liệu, API và 5 cách tính ở backend giữ nguyên). Cột «Ghi chú» của dòng vị trí không còn trên bảng (dữ liệu cũ giữ khi lưu).

