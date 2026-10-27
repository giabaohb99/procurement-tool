# Kho mẫu báo cáo Nhân sự

| | |
|---|---|
| Bản | 2.8 — 27/10/2026 (đợt 3 duoc-CR-688: A3, A5, D1, H1 đã có — khóa 21–24; biểu đồ linh hoạt phần một) · 2.7 — 27/10/2026 (đợt 2 duoc-CR-687: B2, B3 đã có — khóa 19, 20; A2 đã có trong Biến động nhân sự) · 2.6 — 27/10/2026 (đính chính B3: mẫu 01/PLI là danh sách từng người 27 cột, nộp Sở Nội vụ; B2 liệt kê đủ thông tin bắt buộc của sổ) · 2.5 — 27/10/2026 (đợt 1 duoc-CR-686 lên mã: B1, E1 đã có; A1/C1/C2 bù các chỗ thiếu; lọc phòng ban + danh sách người cho 5 báo cáo) · 2.4 — 27/10/2026 (thêm §3.4 «Biểu đồ linh hoạt» dùng chung cho mọi mẫu, kèm biểu đồ gợi ý từng mẫu) · 2.3 — 27/10/2026 (thêm nhóm H «Phúc lợi & sự kiện», mẫu H1: lọc đối tượng theo dịp như 8/3 và dự trù kinh phí) · 2.2 — 27/10/2026 (thêm mẫu A5 «Quỹ lương theo pháp nhân» để chọn công ty tuyển người) · 2.1 — 27/10/2026 (thêm ý «Tuyển dụng» vào A1; thêm nhóm G «Tài sản cấp phát» với mẫu G1) · 2.0 — 27/10/2026 (viết lại thành kho mẫu: 6 nhóm, 16 mẫu, mỗi mẫu chia ý nhỏ; gộp các mục lẻ vào mẫu lớn; bỏ danh sách mẫu chưa có phân hệ; soát mã 3 báo cáo đang chạy, ghi «Còn thiếu so với bản đang chạy» ở A1, C1, C2) · 1.1 — 27/10/2026 (thêm góc nhìn trưởng phòng Nhân sự) · 1.0 — 27/10/2026 (3 báo cáo đã có + 6 đề xuất) |
| Tình trạng | 12 mẫu **đã có** trên ERP (A1, C1, C2 từ trước; B1, E1 từ duoc-CR-686; A2, B2, B3 từ duoc-CR-687; A3, A5, D1, H1 từ duoc-CR-688); các mẫu còn lại là **đề xuất**. Lộ trình các đợt: `plans/261027-1045-kho-mau-bao-cao-nhan-su/plan.md` |
| Giao diện | `frontend-v2/` (cổng 8083), menu *Báo cáo* ▸ nhóm «Nhân sự» |
| Mã nguồn backend | `modules/employee/report_*.py` · `modules/leave/report_*.py` · `modules/leave/balance_report_*.py` · khóa ở `core/report_keys.py` |
| Mã nguồn frontend | `modules/report/config/report-catalog-hr.ts` · `modules/report/pages/*-report-page.tsx` |
| Tài liệu khung báo cáo | `doc/tai-lieu-chuc-nang/08-he-thong-bao-cao.md` |

**Cách đọc:** mỗi **nhóm** (A–F) gom các mẫu báo cáo cùng đề tài. Mỗi **mẫu** có một câu «trả lời câu hỏi gì», sau đó chia thành **ý chính**, dưới mỗi ý chính là các **ý nhỏ** (chỉ số hoặc danh sách cụ thể).

**Ký hiệu tình trạng dữ liệu:**
✅ đủ dữ liệu, làm được ngay · 🟡 thiếu một chút (thêm một cột hoặc một danh mục là đủ) · 🔴 chưa có dữ liệu, phải làm phân hệ trước

Không làm chấm công và lương (đại ca chốt bỏ ngày 16/10/2026).

---

## 1. Bảng tổng

| Nhóm | Mẫu | Tình trạng | Ưu tiên |
|---|---|---|---|
| **A. Quy mô & cơ cấu** | A1. Biến động nhân sự (gồm cả tuyển dụng) | Đã có (khóa 6), mở rộng thêm; phần tuyển dụng 🔴 chờ phân hệ | 4 |
| | A2. Cơ cấu nhân sự | **Đã có trong A1 (duoc-CR-687)** | — |
| | A3. Cơ cấu quản lý | **Đã có (khóa 23, duoc-CR-688)** | — |
| | A4. Định biên kế hoạch so với thực tế | Đề xuất, 🟡 thiếu dữ liệu | Chờ chốt |
| | A5. Quỹ lương theo pháp nhân | **Đã có phần thực tế (khóa 21, duoc-CR-688)**; kế hoạch 🟡 | — |
| **B. Hợp đồng & tuân thủ pháp luật** | B1. Hợp đồng lao động | **Đã có (khóa 17, duoc-CR-686)** | — |
| | B2. Sổ quản lý lao động | **Đã có (khóa 19, duoc-CR-687)** | — |
| | B3. Báo cáo tình hình sử dụng lao động (mẫu 01/PLI) | **Đã có (khóa 20, duoc-CR-687)** | — |
| | B4. Đối tượng cần chú ý theo luật | Đề xuất | 7 |
| **C. Nghỉ phép & có mặt** | C1. Tình hình nghỉ phép | Đã có (khóa 7), mở rộng thêm | 6 |
| | C2. Quỹ phép năm | Đã có (khóa 8), mở rộng thêm | 6 |
| | C3. Có mặt theo ngày | Đề xuất | 8 |
| **D. Quá trình công tác** | D1. Điều chuyển & bổ nhiệm | **Đã có (khóa 24, duoc-CR-688)** | — |
| **E. Dữ liệu & vận hành phòng Nhân sự** | E1. Hồ sơ & tài khoản còn thiếu | **Đã có (khóa 18, duoc-CR-686)** | — |
| | E2. Yêu cầu sửa hồ sơ | Đề xuất | 8 |
| | E3. Lịch nhắc trong tháng | Đề xuất (ô ở Trang chủ, không phải báo cáo) | 9 |
| **F. Tiện ích văn phòng** | F1. Sử dụng phòng họp | Đề xuất | 9 |
| **G. Tài sản cấp phát** | G1. Quản lý tài sản cấp phát | Đề xuất, 🔴 chờ phân hệ Tài sản | Chờ phân hệ |
| **H. Phúc lợi & sự kiện** | H1. Đối tượng theo dịp và dự trù kinh phí | **Đã có (khóa 22, duoc-CR-688)** | — |

Mẫu nào làm thật mới được cấp số khóa trong `ReportKey`, nối tiếp số lớn nhất (17, 18 đã cấp cho B1, E1; mẫu kế tiếp nhận 19). Không giữ chỗ số trước. Mẫu mở rộng (A2, các phần mở rộng của A1/C1/C2) dùng lại khóa của báo cáo gốc.

---

## 2. Kho mẫu báo cáo

### Ba báo cáo đang chạy: chỗ thiếu chung

> **duoc-CR-686 (27/10/2026) đã bù** các mục đánh dấu ✔ dưới đây và trong A1, C1, C2. **Còn mở:** lọc trạng thái nhân sự ở A1, đọc lịch sử điều chuyển, định biên theo tháng, tách nghỉ tự nguyện, kiêm nhiệm, tỷ lệ vắng mặt, đơn đang nằm ở người duyệt nào, biểu đồ dùng phép theo tháng.

Đối chiếu mã ngày 27/10/2026: `employee/report_*.py`, `leave/report_*.py`, `leave/balance_report_service.py`, `report/pages/*-report-page.tsx`. Chỗ thiếu riêng của từng báo cáo ghi ở A1, C1, C2.

- **Lọc**
  - ✔ Thanh lọc chỉ có **kỳ** và **pháp nhân**, chưa lọc được theo **phòng ban**. Muốn xem một phòng thì phải chọn «Xem theo phòng ban» rồi dò dòng
  - Chưa lọc được theo trạng thái nhân sự (đang làm / thử việc / đã nghỉ)
- **Xem chi tiết**
  - ✔ Không bấm được vào con số để ra danh sách tên người (§3.3 việc 1)
- **Dữ liệu theo thời điểm**
  - Cả 3 báo cáo lấy phòng ban, chức vụ theo hồ sơ **hiện tại**. Ghi chú trên màn còn viết «hệ thống chưa lưu lịch sử điều chuyển», nhưng bảng Quá trình công tác **đã có** từ 03/10/2026 (duoc-CR-585). Có thể dùng bảng này để tính đúng phòng ban tại thời điểm, và sửa lại câu ghi chú cho khỏi sai

### A. Quy mô & cơ cấu nhân sự

#### A1. Biến động nhân sự — đã có (khóa 6), mở rộng thêm

> **Trả lời:** công ty đang có bao nhiêu người, kỳ này tuyển được bao nhiêu, nghỉ bao nhiêu, người mới có ở lại không.

- **Đang có trên màn**
  - Thẻ KPI: Định biên cuối kỳ · Vào mới · Nghỉ việc · Tỷ lệ nghỉ việc
  - Thêm trong bảng: Định biên đầu kỳ, Thay đổi ròng
  - Biểu đồ xu hướng chỉ vẽ Vào mới / Nghỉ việc; khối phụ «Theo trạng thái»
  - Xem theo: Công ty · Phòng ban (mặc định) · Cấp bậc · Loại hình · Giới tính · Chức vụ · Thâm niên (dưới 1 / 1–3 / 3–5 / trên 5 năm)
  - Ghi chú tự động: số hồ sơ đã nghỉ mà thiếu ngày nghỉ việc
- **Còn thiếu so với bản đang chạy**
  - Không có đường **định biên theo từng tháng**. Ban Giám đốc hay hỏi «12 tháng qua quân số lên xuống thế nào» nhưng biểu đồ chỉ có vào/nghỉ ✅
  - ✔ Không xem được **ai** vào, **ai** nghỉ: không có chiều «Nhân sự», cũng không bấm ra danh sách ✅
  - **Tỷ lệ nghỉ việc** chỉ tính trong kỳ đang chọn (nghỉ ÷ định biên bình quân). Chưa có tỷ lệ quy ra năm để so giữa các tháng, và chưa tách nghỉ tự nguyện / bị cho nghỉ 🟡
  - ✔ **Hồ sơ thiếu ngày vào làm** bị lấy ngày tạo hồ sơ thay vào, nhưng màn **không báo** có bao nhiêu hồ sơ như vậy (chỉ báo phần thiếu ngày nghỉ việc) ✅
  - **Kiêm nhiệm** không được tính: người kiêm nhiệm chỉ được đếm ở phòng chính ✅
  - **Không có chiều độ tuổi**, và mã cố ý không đọc ngày sinh vì ngày sinh là trường nhạy cảm (`employee_sensitive`). Muốn có A2 thì phải chốt: số đếm theo nhóm tuổi có cần quyền nhạy cảm không
- **Phân tích nghỉ việc** (mở rộng)
  - Nghỉ việc sớm: nghỉ trong thời gian thử việc hoặc 6 tháng đầu ✅
  - Thâm niên trung bình lúc nghỉ ✅
  - Nghỉ việc theo quản lý trực tiếp ✅ (tính theo quản lý hiện tại; số nhạy cảm, chỉ Ban Giám đốc xem)
  - Lý do nghỉ việc 🟡 (đang ghi chữ tự do, cần danh mục lý do lưu bằng số)
- **Tuyển dụng** (mở rộng; phần lớn 🔴 chờ phân hệ Tuyển dụng)
  - Phần có sẵn số liệu
    - Số người vào mới theo phòng, theo tháng (lấy từ «Vào mới» đang có) ✅
    - Tỷ lệ qua thử việc (lấy chung số với B1) ✅
  - Nhu cầu tuyển
    - Số vị trí đang cần tuyển theo phòng, theo đề xuất tuyển dụng đã duyệt 🔴
    - Vị trí mở quá lâu chưa tuyển được 🔴
  - Phễu ứng viên
    - Hồ sơ nhận → sơ loại → phỏng vấn → mời nhận việc → nhận việc; tỷ lệ rơi ở từng bước 🔴
    - Tỷ lệ ứng viên từ chối lời mời nhận việc 🔴
  - Tốc độ và hiệu quả tuyển
    - Thời gian tuyển: từ ngày duyệt đề xuất tới ngày người mới vào làm 🔴
    - Chi phí mỗi lần tuyển 🔴
  - Chọn công ty để tuyển
    - Pháp nhân nào còn dư quỹ lương và định biên để nhận thêm người: xem **A5** ✅
  - Nguồn ứng viên
    - Số ứng viên và số người được nhận theo từng nguồn (giới thiệu nội bộ, trang tuyển dụng, mạng xã hội…) 🔴
    - Chất lượng nguồn: tỷ lệ qua thử việc và tỷ lệ còn ở lại sau 6 tháng theo nguồn 🔴
- **Giữ chân người mới** (mở rộng)
  - Tỷ lệ còn ở lại sau 3 / 6 / 12 tháng, tính theo tháng vào làm ✅

*Nguồn:* `GET /api/employees/summary` (+ `/summary/export`), quyền `employee.read` / `export`; mã `employee/report_service.py`, `report_headcount_*.py`

#### A2. Cơ cấu nhân sự — đã có trong A1 (duoc-CR-687)

> **Trả lời:** đội ngũ đang trông như thế nào: tuổi, giới, trình độ, cấp bậc, làm ở đâu.

- **Nhân khẩu**
  - Theo nhóm tuổi; tuổi trung bình từng phòng ✅
  - Theo giới tính ✅
- **Trình độ**
  - Theo trình độ học vấn ✅
  - Theo chuyên ngành ✅
- **Vị trí**
  - Theo cấp bậc, chức vụ ✅
  - Tỷ lệ nữ ở từng cấp bậc, nhất là cấp quản lý ✅
- **Nơi làm và hình thức**
  - Theo địa điểm làm việc (văn phòng, kho, xưởng…) ✅
  - Theo loại hình lao động, theo pháp nhân ✅
  - Theo thâm niên ✅

*Đã làm (duoc-CR-687):* «Xem theo» của Biến động nhân sự có thêm Nhóm tuổi (dưới 25 · 25–34 · 35–44 · 45–54 · 55 trở lên), Trình độ, Địa điểm làm việc, Nhóm vị trí việc làm. Tuổi tính tại ngày của mốc. Người không có quyền xem dữ liệu nhạy cảm: nhóm tuổi có số nhỏ (1–2 người, ở kỳ này hoặc kỳ so sánh) bị che, kèm che thêm một nhóm để không lấy Tổng trừ ra được; không mở được danh sách theo nhóm tuổi. Tỷ lệ nữ theo cấp bậc, tuổi trung bình theo phòng ⏳ chưa làm (đi cùng biểu đồ linh hoạt).
*Nguồn:* `tab_employee` (`date_of_birth`, `gender`, `education_level`, `major`, `job_level`, `work_location`, `employment_type`)

#### A3. Cơ cấu quản lý — đã có (khóa 23, duoc-CR-688)

> **Trả lời:** bộ máy quản lý có hợp lý không.

- **Tầm quản lý**
  - Số người dưới quyền của từng quản lý ✅
  - Quản lý chỉ có 1 cấp dưới, hoặc có quá nhiều cấp dưới ✅
  - Tỷ lệ quản lý trên nhân viên, theo phòng ✅
- **Thiếu gán**
  - Nhân viên chưa gán quản lý trực tiếp ✅ (ảnh hưởng tới luồng duyệt theo quản lý)

*Nguồn:* `tab_employee.manager_id`, `job_level`

#### A4. Định biên kế hoạch so với thực tế — 🟡 chờ dữ liệu

> **Trả lời:** «Phòng Kinh doanh được duyệt 20 người, đang có 17.» Đây là câu Ban Giám đốc hay hỏi nhất.

- **Kế hoạch**
  - Định biên được duyệt theo phòng ban × năm 🟡 (chưa có bảng)
- **So sánh**
  - Thiếu / thừa so với kế hoạch, theo phòng ✅ khi đã có kế hoạch
  - Vị trí đang trống ✅ khi đã có kế hoạch

*Cần chốt:* có làm bảng định biên không, ai nhập, bao lâu nhập một lần.

#### A5. Quỹ lương theo pháp nhân — đã có phần thực tế (khóa 21, duoc-CR-688); kế hoạch và thử tính chưa làm

> **Trả lời:** mỗi pháp nhân đang gánh quỹ lương bao nhiêu, còn dư bao nhiêu so với kế hoạch, tuyển người mới vào công ty nào thì các công ty cân bằng nhất.

- **Quỹ lương hiện tại** (tính từ HĐ đang hiệu lực)
  - Tổng lương cơ bản + phụ cấp mỗi tháng, theo từng pháp nhân ✅
  - Số người hưởng lương, lương bình quân mỗi người ✅
  - Tổng lương đóng BHXH; ước phần BHXH công ty phải đóng 🟡 (cần khai tỷ lệ đóng trong cấu hình)
  - Người đang làm mà chưa có HĐ hiệu lực thì không có số lương: đếm riêng để biết quỹ lương đang bị thiếu bao nhiêu người (nối sang B1) ✅
- **So với kế hoạch**
  - Quỹ lương kế hoạch theo pháp nhân × năm 🟡 (chưa có bảng; nên làm chung một bảng với định biên kế hoạch ở A4)
  - Đã dùng, còn dư, % sử dụng; tô đỏ pháp nhân vượt kế hoạch ✅ khi đã có kế hoạch
- **Biến động quỹ lương**
  - Quỹ lương từng tháng trong 12 tháng gần nhất ✅ (tính theo ngày bắt đầu / kết thúc của HĐ)
  - Tăng do tuyển mới, giảm do nghỉ việc, đổi do ký lại HĐ với mức lương mới ✅
- **Hỗ trợ quyết định tuyển**
  - Bảng so các pháp nhân cạnh nhau: số người, quỹ lương, còn dư, lương bình quân ✅ (cột «còn dư» cần kế hoạch 🟡)
  - Lương của cùng một chức vụ ở các pháp nhân (thấp nhất / trung bình / cao nhất), để chào lương người mới không lệch giữa các công ty ✅
  - Thử tính: nhập chức vụ và mức lương dự kiến → quỹ lương từng pháp nhân sau khi tuyển, pháp nhân nào còn dư nhiều nhất 🟡 (cần kế hoạch)

*Xem theo:* Pháp nhân (mặc định) · Phòng ban · Chức vụ · Loại HĐ
*Nguồn:* `tab_labor_contract` (`base_salary`, `allowance`, `insurance_salary`, `start_date`, `end_date`, `status`, `company_id`). Đây là **lương thỏa thuận ghi trên HĐ**, không phải lương thực trả, vì ERP không có chấm công và bảng lương.
*Không trái quyết định bỏ lương ngày 16/10/2026:* mẫu này chỉ cộng số lương đã ghi trên HĐ; không tính lương, không làm phiếu lương.
*Bảo mật (phải chốt trước khi làm):*
- Lương là số nhạy cảm. Hiện màn HĐLĐ trả lương cho bất kỳ ai có `labor_contract.read`, không che
- Báo cáo này nên mặc định **chỉ admin và Ban Giám đốc**, giống khóa 14 và 16; ai khác muốn xem thì admin giao ở tab «Báo cáo»
- Chỉ hiện số tổng và số bình quân. Nhóm dưới 3 người thì ẩn bình quân, vì nhìn bình quân của nhóm 1–2 người là đoán ra lương từng người
- *Đã làm (duoc-CR-688):* che cả nhóm (mọi người xem, kể cả admin) + che phụ chống lấy Tổng trừ, xét riêng kỳ này và kỳ so sánh. Dòng Tổng và danh sách không che: người mở được báo cáo là người được xem lương (báo cáo mặc định chỉ admin; lọc hẹp còn 1–2 người thì Tổng = lương của họ — chấp nhận). Lớp chặn chính là quyền xem báo cáo 21, không phải việc che nhóm. Trợ lý AI không đọc báo cáo này.
- Danh sách lương từng người (khi bấm vào con số) chỉ mở cho người được giao riêng

---

### B. Hợp đồng & tuân thủ pháp luật

#### B1. Hợp đồng lao động — đã có (khóa 17, duoc-CR-686)

> **Trả lời:** tuần này phải xử lý những HĐ nào, có chỗ nào đang sai luật không.

- **Việc phải xử lý** (nhìn tới)
  - HĐ sắp hết hạn trong 30 / 60 / 90 ngày ✅
  - Thử việc sắp hết hạn ✅
  - HĐ đã quá hạn mà người vẫn đang đi làm ✅
  - Tô đỏ khi còn ≤ 15 ngày, vì Điều 45 Bộ luật Lao động 2019 buộc báo người lao động trước ít nhất 15 ngày ⏳ chưa làm (đi cùng việc «ngưỡng cảnh báo» ở §3.3)
- **Tuân thủ**
  - Người đang làm mà chưa có HĐ hiệu lực ✅
  - Người đã ký 2 HĐ có thời hạn: lần ký sau phải là HĐ không xác định thời hạn ✅
  - HĐ đã ký nhưng chưa tải bản scan ✅
- **Tổng hợp trong kỳ**
  - HĐ ký mới, chấm dứt ✔ · đếm riêng số HĐ **gia hạn** ⏳ chưa làm
  - Tỷ lệ qua thử việc (thử việc → ký HĐ chính thức) ⏳ chưa làm
  - Người đã nghỉ mà HĐ chưa bấm «Chấm dứt» ✔ (thêm khi làm, để Nhân sự dọn sổ)
  - Cơ cấu theo loại HĐ ✅

*Xem theo:* Pháp nhân · Phòng ban · Loại HĐ (Thử việc / Xác định thời hạn / Không xác định thời hạn / Khoán việc / Cộng tác viên / Khác)
*Nguồn:* `tab_labor_contract` (`status`, `contract_type`, `start_date`, `end_date`, `signed_file_id`, `terminated_date`); dùng lại luật tính hạn ở `labor_contract/expiry_service.py`
*Đã chốt 27/10/2026:* danh sách (bấm số) hiện Lương cơ bản, Lương đóng BHXH, Phụ cấp cho người có quyền xem HĐLĐ — giống màn HĐLĐ. Báo cáo mặc định chỉ admin; chỉ giao cho người được xem lương (trưởng phòng Nhân sự, Ban Giám đốc).
*Ký hiệu trong mẫu đã có:* ✔ đã làm · ⏳ chưa làm, để đợt sau.

#### B2. Sổ quản lý lao động — đã có (khóa 19, duoc-CR-687)

> **Trả lời:** khi thanh tra lao động hỏi thì đưa ngay được sổ. Bộ luật Lao động (Điều 12) bắt buộc lập sổ trong 30 ngày kể từ khi bắt đầu hoạt động, bằng giấy hoặc điện tử, ở nơi đặt trụ sở / chi nhánh / văn phòng đại diện (Điều 3 Nghị định 145/2020).

- **Thông tin từng người phải có trong sổ** (theo các trang tổng hợp Điều 3 khoản 2 Nghị định 145/2020 — đối chiếu văn bản gốc trước khi chốt mẫu)
  - Có sẵn trong ERP ✅: họ tên · giới tính · ngày sinh · nơi cư trú · số CCCD · trình độ chuyên môn · vị trí việc làm (chức vụ) · loại HĐLĐ · thời điểm bắt đầu làm việc · số BHXH · tiền lương (theo HĐ) · nâng lương (suy từ các HĐ nối tiếp) · số ngày nghỉ trong năm, có lương / không lương (từ Nghỉ phép) · thời điểm chấm dứt HĐ và lý do
  - Chưa có, để trống cho Nhân sự điền tay 🟡: quốc tịch · bậc trình độ kỹ năng nghề · học nghề / đào tạo · kỷ luật, trách nhiệm vật chất · tai nạn lao động, bệnh nghề nghiệp
  - Không có vì đã bỏ chấm công ⛔: số giờ làm thêm
- **Cách dùng**
  - Mỗi pháp nhân một sổ, xuất Excel, xem trên màn được
  - Đánh dấu người thiếu thông tin bắt buộc (nối sang E1) ✅

*Quyền:* sổ chứa ngày sinh, CCCD, địa chỉ, lương → chỉ người có `employee_sensitive.read` và `labor_contract.read`; xuất Excel theo phạm vi **xuất** và đòi thêm `labor_contract.export`. Danh sách trên màn không hiện các giá trị nhạy cảm, chỉ tệp Excel mới có.

#### B3. Báo cáo tình hình sử dụng lao động (mẫu 01/PLI) — đã có (khóa 20, duoc-CR-687)

> **Trả lời:** báo cáo phải nộp 2 lần mỗi năm. Mẫu số 01/PLI Phụ lục I Nghị định 145/2020 — bản sửa nghị định của Bộ Nội vụ (7/2026) mới là dự thảo, vẫn dùng mẫu này.

- **Lịch và nơi nộp** (đã kiểm 27/10/2026)
  - Báo cáo 6 tháng nộp trước 05/6; báo cáo năm nộp trước 05/12. Hạn gần nhất: **05/12/2026**
  - Nộp **Sở Nội vụ** qua Cổng Dịch vụ công quốc gia, rồi báo cơ quan BHXH khu vực nơi đặt trụ sở / chi nhánh. Doanh nghiệp trong khu công nghiệp nộp Ban quản lý khu
  - Mỗi pháp nhân một bản
- **Nội dung mẫu — danh sách TỪNG NGƯỜI, 27 cột** (đính chính: không phải bảng số tổng như bản 2.x của tài liệu này ghi)
  - Phần đầu: tên, địa chỉ, mã số doanh nghiệp, ngành nghề chính của pháp nhân ✅
  - Cột 2–7: họ tên · mã số BHXH · ngày sinh · giới tính · số CCCD · cấp bậc, chức vụ, nơi làm việc ✅
  - Cột 8–11 «Vị trí việc làm»: Nhà quản lý / Chuyên môn kỹ thuật bậc cao (đại học trở lên) / bậc trung (cao đẳng, trung cấp) / Khác 🟡 (chưa có cột phân nhóm — xem câu hỏi mở)
  - Cột 12–17 «Tiền lương»: mức lương ✅ · phụ cấp chức vụ, thâm niên vượt khung, thâm niên nghề, phụ cấp lương, các khoản bổ sung 🟡 (ERP chỉ có MỘT ô phụ cấp tổng trên HĐ → ghi vào «Phụ cấp lương»)
  - Cột 18–19 «Ngành nghề nặng nhọc, độc hại» từ / đến 🟡 (không có dữ liệu → để trống)
  - Cột 20–24 «Loại và hiệu lực HĐLĐ»: không xác định thời hạn (ngày bắt đầu) · xác định thời hạn (bắt đầu / kết thúc) · khác — dưới 1 tháng, thử việc (bắt đầu / kết thúc) ✅
  - Cột 25–26 thời điểm bắt đầu / kết thúc đóng BHXH 🟡 (chưa có cột) · cột 27 ghi chú
- **Xuất tệp**
  - Một tệp Excel, **mỗi pháp nhân một sheet**: bố cục 27 cột, dòng Tổng, chỗ ký «Đại diện doanh nghiệp, cơ quan, tổ chức»
  - Danh sách gồm **mọi người làm việc ở bất kỳ lúc nào trong kỳ** (người nghỉ giữa kỳ có ghi chú «Nghỉ việc ngày …»). Báo cáo năm: chọn «Năm nay» lúc lập (đầu tháng 12); báo cáo 6 tháng: chọn khoảng 01/01–30/06

*Quyền:* như B2 — có CCCD, mã số BHXH, ngày sinh, lương.
*Đã chốt 27/10/2026:* nhóm vị trí việc làm tự suy (Phó phòng trở lên = Nhà quản lý; Đại học+ = bậc cao; Trung cấp / Cao đẳng = bậc trung; còn lại = Khác); cột ERP chưa có dữ liệu để trống; người ký hợp đồng khoán việc / cộng tác viên **không** đưa vào 01/PLI (không phải HĐLĐ), báo cáo ghi số người bị loại. Nhãn 27 cột đã đối chiếu bản PDF mẫu gốc.

#### B4. Đối tượng cần chú ý theo luật — đề xuất

> **Trả lời:** những ai đang được hưởng, hoặc sắp phải xử lý, chế độ riêng theo luật.

- **Nghỉ hưu**
  - Người sắp đến tuổi nghỉ hưu trong 6–12 tháng tới, theo lộ trình tăng tuổi (nam lên 62 vào năm 2028, nữ lên 60 vào năm 2035) ✅
- **Thai sản và con nhỏ**
  - Đang nghỉ thai sản, ngày dự kiến đi làm lại ✅ (nếu đã khai loại nghỉ thai sản)
  - Lao động nữ nuôi con dưới 12 tháng, được nghỉ 60 phút mỗi ngày ✅ (ngày sinh của con lấy từ bảng hộ gia đình `tab_employee_family`; chỉ đúng khi đã khai đủ người thân)
- **Lao động nước ngoài**
  - Danh sách lao động nước ngoài, giấy phép lao động sắp hết hạn 🟡 (chưa có cột quốc tịch, số giấy phép; chỉ cần nếu công ty có thuê)

---

### C. Nghỉ phép & có mặt

#### C1. Tình hình nghỉ phép — đã có (khóa 7), mở rộng thêm

> **Trả lời:** kỳ này nghỉ bao nhiêu, ai nghỉ, đơn có được xử lý nhanh không.

- **Đang có trên màn**
  - Thẻ KPI: Số đơn · Ngày nghỉ đã duyệt · Số người nghỉ · Tỷ lệ từ chối/trả về · Thời gian duyệt trung bình (giờ)
  - Thêm trong bảng: Ngày đang chờ duyệt
  - Biểu đồ xu hướng theo ngày / tuần / tháng; khối phụ «Top loại nghỉ» (theo ngày đã duyệt) và «Theo trạng thái»
  - Xem theo: Loại nghỉ (mặc định) · Phòng ban · Công ty · Nhân sự · Trạng thái
- **Còn thiếu so với bản đang chạy**
  - ✔ **Đơn vắt qua hai kỳ bị tính trọn vào kỳ có ngày bắt đầu.** Ví dụ đơn nghỉ 28/10–05/11 dồn cả vào tháng 10, nên «ngày nghỉ trong tháng» bị lệch. Cần chia số ngày theo từng ngày thật rơi vào kỳ ✅
  - ✔ **Đơn nhiều khoảng ngày** (mới có từ duoc-CR-683, 26/10/2026) cũng chỉ được xếp theo ngày bắt đầu của cả đơn, không theo từng khoảng ✅
  - ✔ Chưa tách **nghỉ có lương / không lương**, dù loại nghỉ đã có cờ `is_paid` ✅
  - Chưa có **tỷ lệ vắng mặt** (ngày nghỉ ÷ ngày công chuẩn theo lịch làm việc) và **ngày nghỉ bình quân mỗi người**, hai chỉ số nhân sự hay dùng nhất để so giữa các phòng ✅
  - Mới có thời gian duyệt **trung bình**. Chưa thấy **đơn đang chờ quá N ngày** và **đang nằm ở người duyệt nào** ✅
- **Người cần chú ý** (mở rộng)
  - Nghỉ dài ngày liên tục ✅
  - Nghỉ ốm nhiều, nghỉ không lương nhiều ✅
- **Thói quen nghỉ** (mở rộng)
  - Theo tháng: tháng nào nghỉ nhiều (ví dụ sát Tết), để xếp người trực ✅
  - Theo thứ trong tuần ✅ (chỉ hiện số tổng, không xếp hạng từng người)

*Nguồn:* `GET /api/leave-requests/summary` (+ export), quyền `leave_request.read` / `export`; mã `leave/report_service.py`, `report_rows.py`, `report_sql_*.py`

#### C2. Quỹ phép năm — đã có (khóa 8), mở rộng thêm

> **Trả lời:** mỗi người còn bao nhiêu phép, ai sắp mất phép, phải trả tiền phép cho ai.

- **Đang có trên màn**
  - Thẻ KPI: Được cấp · Đã dùng · Đang giữ chỗ · Còn lại · Tỷ lệ sử dụng
  - Kỳ là **năm**, mở lần đầu ở «Năm nay», so với năm trước. Không có biểu đồ xu hướng
  - Xem theo: Loại nghỉ (mặc định) · Công ty · Phòng ban · Nhân sự; khối phụ «Top loại nghỉ»
- **Còn thiếu so với bản đang chạy**
  - ✔ **Người đang làm mà chưa được cấp quỹ năm nay** không hiện ở đâu. Báo cáo chỉ đọc những dòng quỹ đã có, nên người bị sót cấp quỹ là im lặng ✅
  - ✔ **Vẫn tính cả người đã nghỉ việc**: không lọc trạng thái nhân sự, nên «Còn lại» bị thổi lên bởi phép của người đã đi ✅
  - ✔ «Được cấp» là một số gộp. Chưa tách **phép năm cơ bản · phép thâm niên · phép chuyển từ năm trước · điều chỉnh tay**, nên khó giải thích khi nhân viên thắc mắc ✅
  - ✔ Phép chuyển sang **đã hết hạn** (`carried_expired_days`) có lưu trong dữ liệu nhưng báo cáo không hiện ✅
  - ✔ Chưa nêu **người dùng vượt quỹ** (còn lại âm) và **người cả năm chưa nghỉ ngày nào** (để nhắc nghỉ trước khi mất phép) ✅
  - Không có biểu đồ: có thể vẽ **số ngày phép dùng theo từng tháng** từ đơn nghỉ đã duyệt ✅
- **Phép sắp mất** (mở rộng)
  - Phép chuyển từ năm trước sắp hết hạn dùng ✅ (theo `carry_over_expire_month` của loại nghỉ, `leave/carryover_service.py`)
- **Phép tồn khi nghỉ việc** (mở rộng)
  - Số ngày phép chưa nghỉ của người sắp nghỉ hoặc vừa nghỉ việc. Theo Điều 113 Bộ luật Lao động, số ngày này phải được trả tiền; báo cáo chỉ ra số ngày, kế toán tự tính tiền ✅
- **Kết sổ cuối năm** (đã có)
  - Đối chiếu trước và sau kết sổ, nằm trong hộp «Đối chiếu kết sổ phép năm» (duoc-CR-664)

*Nguồn:* `GET /api/leave-balances/summary` (+ export), quyền `leave_balance.read` / `export`; mã `leave/balance_report_service.py`

#### C3. Có mặt theo ngày — đề xuất

> **Trả lời:** hôm nay, tuần này mỗi phòng có bao nhiêu người đi làm.

- **Có mặt**
  - Số người đi làm theo ngày, theo phòng: lịch làm việc trừ đi người nghỉ ✅
  - Ai đang nghỉ, nghỉ đến ngày nào ✅ (màn Lịch nghỉ đã có; đây là bản ra số)
- **Thiếu người**
  - Ngày có số người đi làm dưới mức tối thiểu của phòng 🟡 (cần khai mức tối thiểu cho từng phòng)

*Nguồn:* `work_schedule/resolver*.py`, `roster_leave.py` (đã dùng cho màn Xếp lịch), `tab_leave_request`

---

### D. Quá trình công tác

#### D1. Điều chuyển & bổ nhiệm — đã có (khóa 24, duoc-CR-688)

> **Trả lời:** người đi đâu, ai được lên, đề bạt nội bộ có nhiều không.

- **Sự kiện trong kỳ**
  - Số lượt: vào làm, điều chuyển, bổ nhiệm, kiêm nhiệm, miễn nhiệm, thôi việc ✅
  - Kèm số quyết định ✅
- **Luồng di chuyển**
  - Bảng chéo phòng đi → phòng đến ✅
- **Phát triển nghề nghiệp**
  - Thời gian trung bình để được bổ nhiệm lên một cấp ✅
  - Tỷ lệ vị trí quản lý được bổ nhiệm từ trong công ty ✅
- **Kiêm nhiệm**
  - Kiêm nhiệm đang hiệu lực, kiêm nhiệm sắp hết hạn ✅

*Xem theo:* Loại sự kiện · Phòng ban · Chức vụ · Pháp nhân
*Nguồn:* `tab_employee_work_history` (`event_type`, `from_date`, `to_date`, `department_id`, `position_id`, `decision_no`)

---

### E. Dữ liệu & vận hành phòng Nhân sự

#### E1. Hồ sơ & tài khoản còn thiếu — đã có (khóa 18, duoc-CR-686)

> **Trả lời:** hồ sơ của ai chưa đủ, phòng nào khai kém, tài khoản nào đang để hở.

- **Hồ sơ thiếu**
  - Tỷ lệ hồ sơ đầy đủ theo phòng ✅
  - Thiếu CCCD, mã số thuế, số BHXH, tài khoản ngân hàng, ngày vào làm, ngày sinh ✅
- **Giấy tờ sắp hết hạn**
  - CCCD sắp hết hạn (`id_expiry_date`) ✅
- **Gán thiếu**
  - Chưa có chức vụ, chưa có quản lý trực tiếp, chưa có phòng ban ✔
  - Chưa được gán lịch làm việc ⏳ chưa làm (hệ có lịch mặc định toàn công ty nên ai cũng «có lịch»; cần chốt «chưa gán» nghĩa là gì)
- **Tài khoản ERP**
  - Người đã nghỉ việc mà tài khoản vẫn còn mở ✅ (lỗ hổng bảo mật)
  - Nhân viên mới chưa có tài khoản, hoặc có tài khoản nhưng chưa có vai trò ✅

*Xem theo:* Phòng ban · Pháp nhân. «Loại thông tin còn thiếu» là khối biểu đồ phụ, chưa phải chiều xem của bảng.
*Nguồn:* `tab_employee`, `tab_user` / `tab_user_role`
*Quyền:* nhóm trường nhạy cảm chỉ hiện với người có quyền xem dữ liệu nhạy cảm; nhóm tài khoản chỉ hiện với người có quyền xem tài khoản.
*Bảo mật:* chỉ trả số đếm và tên người, không trả giá trị nhạy cảm (số CCCD, số tài khoản); dùng lại `export_mask.py`

#### E2. Yêu cầu sửa hồ sơ — đề xuất

> **Trả lời:** phòng Nhân sự duyệt yêu cầu sửa hồ sơ có kịp không.

- **Khối lượng**
  - Số yêu cầu, đang chờ, chờ quá 2 ngày ✅
- **Chất lượng xử lý**
  - Thời gian xử lý trung bình, tỷ lệ từ chối ✅
- **Nội dung**
  - Các trường hay bị xin sửa nhất ✅

*Nguồn:* `tab_employee_change_request` (`status`, `changes`, `created_at`, `decided_at`)

#### E3. Lịch nhắc trong tháng — ô ở Trang chủ Nhân sự

> **Trả lời:** tháng này có việc gì cần nhớ. Chỉ là danh sách, nên làm thành ô ở Trang chủ chứ không làm báo cáo.

- **Dịp của nhân viên**
  - Sinh nhật ✅
  - Kỷ niệm 1 / 3 / 5 / 10 năm làm việc ✅
- **Mốc công việc**
  - HĐ, thử việc hết hạn trong tháng (dẫn sang B1) ✅

*Muốn phát quà, dự trù tiền cho các dịp này thì dùng H1.*

---

### F. Tiện ích văn phòng

#### F1. Sử dụng phòng họp — đề xuất

> **Trả lời:** phòng nào quá tải, phòng nào bỏ không, giờ nào đông.

- **Mức dùng**
  - Tỷ lệ lấp đầy (giờ đã đặt / giờ làm việc), số lượt đặt ✅
  - Giờ cao điểm ✅
- **Hiệu quả**
  - Số người dự trung bình so với sức chứa của phòng ✅
  - Tỷ lệ đặt rồi hủy hoặc bị từ chối ✅
- **Ai dùng**
  - Theo phòng ban đặt ✅

*Xem theo:* Phòng · Pháp nhân · Phòng ban đặt · Khung giờ
*Nguồn:* `room_booking`, `room_booking_attendee`, `meeting_room.capacity`, lịch làm việc để tính giờ làm

---

### G. Tài sản cấp phát

#### G1. Quản lý tài sản cấp phát — đề xuất, 🔴 chờ phân hệ Tài sản

> **Trả lời:** công ty có những tài sản gì, ai đang giữ cái gì, người nghỉ việc đã trả đủ chưa.

- **Tổng quan tài sản**
  - Số tài sản theo loại (máy tính, điện thoại, màn hình, thẻ ra vào, đồng phục, xe…) 🔴
  - Theo tình trạng: đang cấp cho người dùng · trong kho · đang sửa · hỏng · đã thanh lý 🔴
  - Nguyên giá và giá trị còn lại theo loại, theo pháp nhân 🔴
- **Ai đang giữ gì**
  - Danh sách tài sản theo từng người, theo phòng ban 🔴
  - Tài sản dùng chung của phòng (máy in, máy chiếu…) và người chịu trách nhiệm 🔴
- **Cấp phát và thu hồi trong kỳ**
  - Số lượt cấp mới, thu hồi, chuyển từ người này sang người khác 🔴
  - Người mới vào chưa được cấp đủ theo định mức của chức vụ 🔴
  - Biên bản bàn giao đã ký / chưa ký 🔴
- **Rủi ro**
  - **Người đã nghỉ hoặc sắp nghỉ mà chưa trả tài sản.** Nối vào hộp «việc đang giữ» khi khóa tài khoản / cho nghỉ việc (duoc-CR-665) 🔴
  - Tài sản báo mất, hỏng; tài sản quá lâu không kiểm kê 🔴
- **Bảo hành và bảo trì**
  - Tài sản sắp hết bảo hành, đến hạn bảo dưỡng 🔴
  - Tài sản đã hết khấu hao mà vẫn đang dùng 🔴

*Xem theo:* Loại tài sản · Tình trạng · Phòng ban · Pháp nhân · Người giữ
*Dữ liệu:* chưa có. `modules/inventory` là kho hàng mua về, không theo dõi tài sản đang trong tay ai. Phân hệ Tài sản cấp phát là việc V2-3 trong `../tham-khao-hrm/10-de-xuat-ap-dung.md`, chưa bắt đầu. Khi làm thì nên nối với Thu mua: tài sản sinh ra từ phiếu nhận hàng của đơn mua hàng, khỏi nhập tay lần hai.

---

### H. Phúc lợi & sự kiện

#### H1. Đối tượng theo dịp và dự trù kinh phí — đã có (khóa 22, duoc-CR-688)

> **Trả lời:** một dịp (8/3, 20/10, 1/6, Trung thu, Tết, du lịch…) thì phát cho ai, bao nhiêu người, ở pháp nhân và phòng nào, chức vụ gì, tổng tiền bao nhiêu, mỗi pháp nhân chịu bao nhiêu.
>
> **Ví dụ 8/3:** lọc nữ đang làm vào ngày 08/3 → ra số người theo từng pháp nhân, phòng ban, chức vụ → nhập mức quà (quản lý 500.000đ, nhân viên 300.000đ) → ra tổng tiền mỗi pháp nhân → xuất danh sách ký nhận.

- **Chọn đối tượng** (bộ lọc ghép được với nhau)
  - Giới tính, nhóm tuổi ✅
  - Pháp nhân, phòng ban, chức vụ, cấp bậc ✅
  - Thâm niên; loại hình, loại HĐ (để chọn có tính người thử việc, cộng tác viên hay không) ✅
  - **Đang làm vào đúng ngày diễn ra dịp**: bỏ người đã nghỉ trước ngày đó và người vào sau ngày đó ✅
  - Người đang nghỉ dài ngày hoặc nghỉ thai sản vào ngày đó: vẫn tặng hay bỏ, tùy chọn ✅
  - Người thân: con theo độ tuổi, ví dụ con dưới 15 tuổi cho dịp 1/6 ✅ (từ bảng hộ gia đình; chỉ đúng khi đã khai đủ)
- **Đếm và gom nhóm**
  - Số người theo pháp nhân × phòng ban ✅
  - Số người theo chức vụ, cấp bậc ✅
  - So với cùng dịp năm trước (đếm lại tại ngày đó của năm trước) ⏳ chưa làm
- **Dự trù kinh phí**
  - Mức chi mỗi người, được khác nhau theo nhóm (quản lý / nhân viên, theo thâm niên…) ✅ (nhập ngay trên màn)
  - **Tổng tiền theo pháp nhân**, để mỗi công ty hạch toán đúng phần của mình ✅
  - Tổng tiền theo phòng ban ✅
  - Từ tổng dự trù lập luôn **Yêu cầu thanh toán** (phân hệ đã có), khỏi gõ lại số ✅
- **Xuất danh sách**
  - Danh sách ký nhận: mã NV, họ tên, pháp nhân, phòng, chức vụ, mức quà, cột ký tên ✅
  - Danh sách tách theo phòng để phát quà tận nơi ✅
- **Lưu đợt phát**
  - Lưu lại đợt (dịp, ngày, danh sách, mức chi) và đánh dấu ai đã nhận 🟡 (cần bảng mới). Không lưu thì vẫn dùng được, chỉ là năm sau phải lọc lại từ đầu
- **Dịp có sẵn** (bấm một nút là ra bộ lọc mặc định, sửa thêm được)
  - 8/3, 20/10: nữ đang làm ✅
  - 1/6, Trung thu: con của nhân viên theo độ tuổi ✅
  - Tết: toàn bộ người đang làm, mức chi theo thâm niên ✅
  - Sinh nhật trong tháng; kỷ niệm 5 / 10 năm làm việc ✅
  - Hiếu hỉ: nhân viên cưới, sinh con, có người thân mất, lấy theo đơn nghỉ đã duyệt của loại nghỉ tương ứng ✅
  - Du lịch, tiệc cuối năm: người đang làm + số người thân đi cùng 🟡 (số người thân đi cùng phải cho đăng ký)

*Xem theo:* Pháp nhân · Phòng ban · Chức vụ · Cấp bậc · Nhóm tuổi · Thâm niên
*Nguồn:* `tab_employee` (`gender`, `date_of_birth`, `company_id`, `department_id`, `position_id`, `job_level`, `hire_date`, `resign_date`, `status`) · `tab_employee_family` (`relation`, `date_of_birth`) · `tab_leave_request` (loại nghỉ, cho hiếu hỉ và thai sản) · `tab_labor_contract` (loại HĐ)
*Bảo mật:*
- Ngày sinh và người thân là dữ liệu nhạy cảm (`employee_sensitive`). Chỉ dùng để **lọc**; danh sách xuất ra không in ngày sinh, không in thông tin người thân ngoài số con được tính
- Người xem chỉ thấy nhân sự trong phạm vi của mình, như mọi báo cáo khác


*Đã chốt mặc định 27/10/2026 (duoc-CR-688):* mức quà nhập tay trên màn mỗi lần, **không lưu** đợt phát; người ký hợp đồng khoán việc / cộng tác viên mặc định không tính; «Kỷ niệm năm làm việc» = cùng tháng vào làm và tròn 1 / 3 / 5 / 10 năm; ngày dịp 8/3, 20/10, 1/6 tự nhảy tới lần gần nhất sắp tới; Trung thu / Tết chọn ngày tay. Lập Yêu cầu thanh toán từ tổng dự trù, hiếu hỉ theo đơn nghỉ, du lịch kèm người thân ⏳ chưa làm.

---

## 3. Góc nhìn trưởng phòng Nhân sự: mẫu báo cáo cần khai những gì

Mục này viết từ vai **trưởng phòng Nhân sự**, là người dùng chính của nhóm báo cáo này. Câu hỏi đặt ra: muốn **sinh ra** một mẫu báo cáo dùng được thì mẫu phải khai đủ những gì, và khung báo cáo hiện tại còn thiếu gì.

### 3.1. Trưởng phòng dùng báo cáo để làm gì, theo nhịp nào

| Nhịp | Việc phải làm | Mẫu cần |
|---|---|---|
| **Hằng tuần** (sáng thứ Hai) | Quyết định ký tiếp hay không ký tiếp HĐ, kết thúc thử việc, đốc yêu cầu sửa hồ sơ và đơn nghỉ đang chờ | B1 · E2 · C1 |
| **Hằng tháng** (trước ngày 5) | Gửi Ban Giám đốc báo cáo nhân sự tháng, **gộp thành một tệp** | A1 · C1 · E1 |
| **Hằng quý** | Xem cơ cấu, tìm phòng có vấn đề | A2 · A3 · A1 (nghỉ việc sớm, giữ chân) · D1 |
| **6 tháng và cả năm** | Nộp mẫu 01/PLI; chốt phép cuối năm; lên kế hoạch HĐ năm sau | B3 · B2 · C2 · B1 (nhìn tới 12 tháng) |
| **Theo dịp** (8/3, 20/10, 1/6, Trung thu, Tết…) | Lên danh sách người được tặng, dự trù tiền theo từng pháp nhân, xin duyệt chi | H1 |
| **Khi được hỏi** | Trả lời ngay câu kiểu «phòng X bao nhiêu người, ai sắp hết HĐ» | Mọi mẫu phải **bấm được vào con số để ra danh sách tên người** |

### 3.2. Phiếu khai một mẫu báo cáo

Để sinh một mẫu báo cáo (dù người viết mã tay hay nhờ trợ lý AI dựng), trưởng phòng chỉ cần điền đủ phiếu dưới đây. Cột cuối cho biết mỗi ô ứng với chỗ khai nào trong khung báo cáo hiện tại.

| # | Ô cần khai | Ví dụ (B1. Hợp đồng lao động) | Khai ở đâu trong mã |
|---|---|---|---|
| 1 | **Câu hỏi chính** mà báo cáo trả lời (một câu) | «Tuần này tôi phải xử lý những HĐ nào?» | `description` ở `report-catalog-hr.ts` |
| 2 | **Ai xem, ai nhận** | Trưởng phòng Nhân sự, chuyên viên Nhân sự; trưởng phòng ban chỉ thấy phòng mình | `tab_report_access` + `require(entity)` + `apply_scope` |
| 3 | **Nhịp xem** | Hằng tuần | Quyết định `defaultPreset` |
| 4 | **Kiểu thời gian**: *theo kỳ* (sự kiện xảy ra trong kỳ) · *tại thời điểm* (số chốt tới một ngày) · *nhìn tới* (sẽ xảy ra trong N ngày tới) | Nhìn tới 30 / 60 / 90 ngày, kèm HĐ đã quá hạn | Theo kỳ và tại thời điểm: `MetricSpec(snapshot=…)` · nhìn tới: **chưa có** (§3.3) |
| 5 | **Chỉ số**: tên · cách tính · đơn vị · tăng là tốt hay xấu | «Sắp hết hạn = HĐ đã ký, `end_date` ≤ hôm nay + 30, chưa có HĐ nối tiếp»; đơn vị: HĐ; tăng là xấu | `MetricSpec(key, label, kind, good=…)` |
| 6 | **Thẻ KPI ở đầu trang** (tối đa 4, đúng thứ tự) | Đang hiệu lực · Sắp hết hạn 30 ngày · Đã quá hạn · Chưa có HĐ | `kpis` |
| 7 | **Xem theo** (chiều gom) và chiều mặc định | Phòng ban (mặc định) · Pháp nhân · Loại HĐ · Trạng thái | `DimensionSpec` · `defaultGroupBy` |
| 8 | **Bộ lọc** | Pháp nhân · phòng ban · loại HĐ · số ngày nhìn tới | Ô lọc chung + `extraFilters` |
| 9 | **So sánh với** | Không cần (đây là danh sách việc phải làm) | `compare = previous / year / none` |
| 10 | **Ngưỡng cảnh báo** (tô đỏ khi nào) | Còn ≤ 15 ngày hoặc đã quá hạn | Dùng lại `DANGER_DAYS` ở `labor_contract/expiry_service.py` · tô màu: **chưa có** |
| 11 | **Danh sách chi tiết** khi bấm vào con số: những cột nào, cột nào phải che | Mã NV · Họ tên · Phòng · Loại HĐ · Ngày hết hạn · Số lần đã ký HĐ có thời hạn; **không** hiện lương | **Chưa có** (§3.3) |
| 11b | **Biểu đồ mặc định**: vẽ chỉ số nào, theo chiều nào, kiểu gì (người xem đổi được, §3.4) | Cột chồng: số HĐ sắp hết hạn theo tuần, tách màu theo loại HĐ | `chartMetric` · kiểu và chiều: **chưa có** (§3.4) |
| 12 | **Xuất ra**: Excel thường hay theo mẫu cố định; có dòng người lập / ký không | Excel thường | `exportEndpoint` · mẫu cố định: **chưa có** |
| 13 | **Gửi tự động** cho ai, lúc nào | 7 giờ sáng thứ Hai, gửi trưởng phòng Nhân sự | **Chưa có** (§3.3) |
| 14 | **Dữ liệu phải đủ trước khi tin số** | Mọi nhân viên đang làm phải có `hire_date` và ít nhất một HĐ đã ký | Ghi vào `notes` của phản hồi `/summary` |

Thiếu ô 4, 5 hoặc 11 thì chưa sinh được mẫu; các ô còn lại để trống thì lấy mặc định.

### 3.3. Khung báo cáo hiện tại đáp ứng gì, thiếu gì

**Đã có** (`ReportAnalyticsPage`, `ReportPageConfig`, `MetricSpec`, `DimensionSpec`): chọn kỳ có sẵn · so với kỳ trước hoặc cùng kỳ năm trước · xem theo ngày/tuần/tháng · thẻ KPI · biểu đồ xu hướng · gom theo một chiều · khối «Top» · lọc pháp nhân và lọc riêng từng trang · xuất Excel · nút mở bảng gốc · gác quyền từng báo cáo.

**Trưởng phòng còn cần**, xếp theo mức cần:

| # | Thiếu | Vì sao cần | Mẫu cần tới | Gợi ý cách làm |
|---|---|---|---|---|
| 1 | **Bấm vào con số ra danh sách tên người** | «12 HĐ sắp hết hạn» mà không thấy là ai thì phải mở bảng gốc lọc lại tay | Hầu hết | Đường `/summary/rows` dùng chung bộ lọc, trả danh sách đã che dữ liệu nhạy cảm; hiện trong ngăn kéo bên phải |
| 1b | **Lọc theo phòng ban** | Trưởng phòng ban chỉ muốn xem phòng mình mà không phải chọn «Xem theo» rồi dò dòng | Mọi báo cáo | Thêm ô Phòng ban vào `report-filters-bar.tsx`, lọc sau `apply_scope` giống ô pháp nhân |
| 2 | **Kiểu «nhìn tới»** (trong N ngày tới) | Khung hiện chỉ tính theo kỳ đã qua | B1 · B4 · C2 · E1 | Thêm preset «30 / 60 / 90 ngày tới» vào `report-period-presets.ts` |
| 3 | **Chốt số theo tháng** | Báo cáo gửi Ban Giám đốc tháng 9 không được tự đổi khi tháng 10 có người sửa hồ sơ. Hiện mọi số đều tính lại lúc xem | A1 · A2 · B3 | Bảng chụp số cuối tháng, chạy bằng Celery; xem tháng cũ thì đọc bảng chụp |
| 4 | **Bảng chéo hai chiều** | Phòng ban × loại HĐ; phòng đi × phòng đến; độ tuổi × giới tính | B1 · D1 · B3 | Tham số `group_by_2`, hiện dạng ma trận |
| 5 | **Xuất theo mẫu cố định** | Có tên pháp nhân, kỳ, người lập, chỗ ký | B2 · B3 | Khuôn Excel/Word riêng; dùng lại cách sinh tệp của HĐLĐ (`docx_engine.py`) |
| 6 | **Gộp nhiều báo cáo thành một tệp tháng** | Mỗi tháng gửi một tệp, không phải 4 tệp rời | A1 · C1 · E1 | Nút «Xuất gói báo cáo tháng», mỗi báo cáo một sheet |
| 7 | **Ngưỡng cảnh báo và tô màu** | Tỷ lệ nghỉ việc > 5%/tháng, HĐ còn ≤ 15 ngày… phải nổi lên ngay | A1 · B1 | Khai `threshold` trong `MetricSpec`, giao diện tô đỏ/vàng |
| 7b | **Biểu đồ linh hoạt** | Mỗi người hỏi một kiểu: Ban Giám đốc muốn so pháp nhân, trưởng phòng muốn xem phòng mình theo tháng. Biểu đồ cố định thì phải xuất Excel tự vẽ lại | Mọi mẫu | Xem §3.4 |
| 8 | **Gửi tự động định kỳ** | Sáng thứ Hai có ngay danh sách việc tuần | B1 · E2 | Celery gửi qua thông báo ERP hoặc email; người nhận lấy từ `tab_report_access` |

Việc 1 và 2 nhỏ, nên làm cùng B1. Việc 3, 4, 5 nên làm cùng B3 vì đều cần số đã chốt và tệp đúng mẫu. Việc 6, 7, 8 làm sau.

### 3.4. Biểu đồ linh hoạt

> **duoc-CR-688 đã làm phần một** (mọi báo cáo): vẽ theo thời gian hoặc theo chiều «Xem theo» đang chọn; kiểu đường / cột / cột ngang / vành khuyên (≤ 6 nhóm); Top 5 / 10 / 20 / tất cả, phần dư gộp «Khác» chỉ khi chỉ số cộng được (cờ `additive` của `meta`); bỏ nhóm bị che, nhóm 0; bấm cột / lát mở danh sách người; tải ảnh PNG; lựa chọn nằm trên đường dẫn. **Chưa làm** (cần máy chủ xem theo hai chiều): tách màu theo chiều thứ hai, bảng nhiệt, tháp tuổi, lưu và ghim góc nhìn, Excel kèm biểu đồ.

Áp cho **mọi mẫu** trong tài liệu này. Một khung biểu đồ dùng chung; mẫu nào cũng chỉ khai biểu đồ mặc định, còn người xem tự đổi.

**Đang có** (`period-comparison-chart.tsx`, `report-breakdown-charts.tsx`, `kpi-trend-card.tsx`): một đường xu hướng so với kỳ trước (bấm thẻ KPI để đổi chỉ số) · các khối cột ngang «Top» cố định theo cấu hình trang · đường nhỏ trong thẻ KPI. Không đổi được kiểu biểu đồ, không chọn được chiều để vẽ.

- **Người xem tự chọn**
  - **Chỉ số** để vẽ: đã có một phần (bấm thẻ KPI)
  - **Vẽ theo**: thời gian (ngày / tuần / tháng) hoặc một chiều bất kỳ trong «Xem theo» (pháp nhân, phòng ban, chức vụ, nhóm tuổi…)
  - **Tách màu theo** một chiều thứ hai. Ví dụ: số người theo phòng ban, tách màu nam / nữ; quỹ lương theo pháp nhân, tách màu theo loại HĐ
  - **Kiểu biểu đồ**: đường · cột · cột chồng · cột chồng 100% · cột ngang · tròn / vành khuyên · bảng nhiệt · tháp tuổi
  - **Top N**: chỉ hiện N nhóm lớn nhất, phần còn lại gộp thành «Khác»
- **Hệ thống tự gợi ý kiểu hợp lý** (người xem vẫn đổi được)
  - Theo thời gian → đường hoặc cột
  - So các nhóm với nhau → cột ngang, xếp từ lớn tới nhỏ
  - Cơ cấu, tỷ trọng → cột chồng 100%; biểu đồ tròn chỉ cho phép khi có tối đa 6 nhóm
  - Hai chiều cùng lúc (phòng ban × tháng) → bảng nhiệt
  - Tuổi × giới tính → tháp tuổi
- **Tương tác**
  - Rê chuột hiện số chính xác và % so với kỳ trước
  - Bấm vào một cột hoặc một ô → lọc cả trang theo nhóm đó, hoặc mở danh sách người (§3.3 việc 1)
  - Bấm vào chú thích để ẩn / hiện một dòng màu
- **Lưu và chia sẻ**
  - Lưu «góc nhìn» (bộ lọc + chỉ số + chiều + kiểu biểu đồ) đặt tên riêng để mở lại, ví dụ «Nữ theo phòng ban – 8/3»
  - Ghim một biểu đồ lên Trang chủ Nhân sự
  - Gửi đường dẫn mở đúng góc nhìn đó; bộ lọc đã nằm trên URL nên phần này gần như có sẵn
- **Xuất**
  - Tải ảnh PNG của biểu đồ để dán vào báo cáo gửi Ban Giám đốc
  - Tệp Excel xuất ra có kèm sheet số liệu đúng như biểu đồ đang xem
- **Bảo mật**
  - Với mẫu nhạy cảm (A5 quỹ lương, nhóm tuổi), nhóm dưới 3 người thì không hiện bình quân, cả trên biểu đồ lẫn trong chú thích

**Biểu đồ gợi ý cho từng mẫu**

| Mẫu | Biểu đồ mặc định | Đổi sang khi cần |
|---|---|---|
| A1 Biến động nhân sự | Đường định biên theo tháng + cột vào / nghỉ | Cột ngang tỷ lệ nghỉ việc theo phòng; phễu tuyển dụng (khi có phân hệ) |
| A2 Cơ cấu nhân sự | Tháp tuổi × giới tính | Cột chồng 100% trình độ theo phòng; vành khuyên theo địa điểm |
| A3 Cơ cấu quản lý | Cột ngang số người dưới quyền mỗi quản lý | — |
| A4 / A5 Định biên, quỹ lương | Cột nhóm theo pháp nhân: thực tế cạnh kế hoạch | Đường quỹ lương 12 tháng; cột chồng theo loại HĐ |
| B1 Hợp đồng lao động | Cột chồng số HĐ hết hạn theo tuần, tách màu theo loại HĐ | Cột ngang theo phòng ban |
| B3 Mẫu 01/PLI | Bảng số đúng mẫu (không cần biểu đồ) | Cột chồng theo trình độ, theo loại HĐ |
| C1 Tình hình nghỉ phép | Đường ngày nghỉ theo tháng | Bảng nhiệt phòng ban × tháng; cột theo thứ trong tuần; vành khuyên có lương / không lương |
| C2 Quỹ phép năm | Cột chồng cấu thành quỹ (cơ bản · thâm niên · chuyển sang · điều chỉnh) theo phòng | Cột ngang người còn nhiều phép nhất |
| C3 Có mặt theo ngày | Cột số người đi làm theo ngày, tách màu theo phòng | Bảng nhiệt phòng × ngày |
| D1 Điều chuyển & bổ nhiệm | Bảng nhiệt phòng đi × phòng đến | Cột theo loại sự kiện |
| E1, E2 | Cột ngang theo phòng (số thiếu, số chờ) | Vành khuyên theo loại thông tin thiếu |
| F1 Phòng họp | Bảng nhiệt giờ × thứ trong tuần | Cột ngang tỷ lệ lấp đầy theo phòng |
| G1 Tài sản cấp phát | Cột chồng theo loại tài sản, tách màu theo tình trạng | Cột ngang theo phòng ban |
| H1 Phúc lợi & sự kiện | Cột chồng số người theo pháp nhân, tách màu theo phòng ban | Cột tổng tiền theo pháp nhân; vành khuyên theo chức vụ |

*Cách làm:* dựng một khung biểu đồ chung trong `modules/report/components/` (đã dùng Recharts); backend chỉ cần cho phép `group_by` thứ hai (cùng việc «bảng chéo hai chiều» ở §3.3). Không viết biểu đồ riêng cho từng mẫu.

---

## 4. Việc phải làm cho mỗi báo cáo mới

1. Cấp số mới ở `core/report_keys.py`, nối tiếp số lớn nhất và không tái dùng số cũ, rồi chạy `scripts/gen_status_ts.py`.
2. Gắn `require_report(ReportKey.X)` lên cả `/summary` lẫn `/summary/export`, kèm `require(entity, action)` và `apply_scope` của phân hệ gốc.
3. Khai mục mới trong `report-catalog-hr.ts`, nhãn khớp `REPORT_META`.
4. Viết API theo hướng tốc độ trước: gom SQL, số truy vấn cố định, có bài kiểm đếm số truy vấn, chỉ mục gom vào một migration.
5. Cập nhật bài hướng dẫn sử dụng và chỉ mục RAG khi xong.

---

## Câu hỏi còn mở

1. Đại ca chọn những mẫu nào, theo thứ tự nào? Thứ tự ưu tiên ở §1 là đề nghị của em.
2. B3 (01/PLI) cần xuất Excel đúng bố cục mẫu để nộp luôn, hay chỉ cần xem số trên màn hình? Phòng Nhân sự có tệp đã nộp kỳ trước không?
3. B1 có hiện lương cơ bản / lương đóng bảo hiểm không, hay bỏ hẳn cho thống nhất với việc đã bỏ phần lương?
4. E1 cho ai xem: chỉ phòng Nhân sự, hay cả trưởng phòng ban (chỉ thấy phòng mình)?
5. A4: có làm bảng định biên kế hoạch theo phòng × năm không? Nếu có thì ai nhập, bao lâu nhập một lần?
6. Báo cáo tháng gửi Ban Giám đốc có cần chốt số (không tự đổi khi hồ sơ được sửa sau đó) không? Nếu có thì chốt vào ngày nào hằng tháng?
7. Số đếm theo **nhóm tuổi** (A1, A2, B3) có cần quyền xem dữ liệu nhạy cảm (`employee_sensitive`) không? Ngày sinh đang là trường nhạy cảm, nhưng báo cáo chỉ ra số đếm theo nhóm chứ không ra ngày sinh của ai.
8. Tuyển dụng (A1) và Tài sản cấp phát (G1) đều cần làm phân hệ trước. Làm phân hệ nào trước? Tài sản cấp phát quản lý ở phân hệ Nhân sự hay Hành chính?
9. A5 Quỹ lương: ai được xem (đề nghị: chỉ admin và Ban Giám đốc)? Quỹ lương kế hoạch theo pháp nhân do ai nhập, nhập theo năm hay theo tháng? Quỹ lương tính lương cơ bản + phụ cấp, hay tính thêm phần BHXH công ty đóng?
10. H1 Phúc lợi: mức chi mỗi dịp nhập tay mỗi lần, hay lưu sẵn thành định mức theo dịp? Có cần lưu đợt phát và đánh dấu ai đã nhận không? Người thử việc, cộng tác viên có được tính vào các dịp không?
