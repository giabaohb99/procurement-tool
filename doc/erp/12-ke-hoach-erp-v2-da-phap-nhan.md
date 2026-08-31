# 12 — KẾ HOẠCH CHUYỂN THU MUA SANG ERP V2 VÀ LÊN ĐA PHÁP NHÂN

**Bản 1.2 — 18/08/2026.** Bản 1.1 viết lại theo **tám câu Q1–Q8 đã chốt hết** trong ngày: P6 đổi
hướng (giữ luồng Yêu cầu báo giá, không chuyển đổi dữ liệu), P5 đổi từ "theo pháp nhân" sang "theo
đơn vị", bỏ P9-3, P8 nhẹ đi. Bản 1.2 thêm **mục 5 — phương án rút gọn**: đo thử kịch bản bỏ hẳn
tầng đa pháp nhân, chỉ phân quyền theo phòng ban và công ty. **Cuối ngày khách CHỐT đi hướng này** — P5 hoãn, xem `11` mục 4.3.

Đây là **bản thực thi** của `11-da-phap-nhan-va-erp-v2.md`. Tệp `11` trả
lời "vì sao" và "được hay không được"; tệp này trả lời "làm gì, theo thứ tự nào, xong thì đo bằng
gì". Không lặp lại phần đánh giá ở `11`.

Mười giai đoạn, mã **P0** đến **P9**. Ước lượng ghi theo **ngày công cho một người**, là ước lượng
thô, chưa tính thời gian chờ quyết định và chờ nghiệm thu.

---

## 1. Tám câu chặn — chốt hết ngày 18/08/2026

Chi tiết và lý do ở `11` mục 4.1 và 4.2. Tóm tắt để cầm đi làm:

| | Chốt | Ảnh hưởng |
|---|---|---|
| **Q1** | Sản phẩm **một dòng gốc + bản đè theo pháp nhân**. Mỗi công ty riêng tên, riêng giá, riêng tồn — **chung mã** | P5 |
| **Q2** | Con sửa được: tên hiển thị, quy cách, phân loại, NCC mặc định, dùng/ngưng; **khóa mã** | P5 |
| **Q3** | Danh mục tách theo **đơn vị**, có ô phân bổ xuống công ty con khi tạo. **Trừ phân loại và đơn vị tính — dùng chung** | P4, P5 |
| **Q4** | Giữ **luồng Yêu cầu báo giá**, thêm trường YCMH lên dòng hàng, gọi là **Yêu cầu mua hàng**; chọn phương án là **tạo thẳng đơn mua hàng** | P6 |
| **Q5** | Dego Organic là **phòng ban dùng chung nhiều công ty** | P2, P7 |
| **Q6** | Mã chứng từ **giữ nguyên, một dãy số chung** | Bỏ P9-3 |
| **Q7** | Tiền treo **không đối chiếu kế toán**; chỉ ghi sổ theo NCC rồi cho chọn để cấn trừ | P8 nhẹ đi |
| **Q8** | Dữ liệu cũ **về DEGO hết**; phiếu nguyên liệu đẩy đơn vị xử lý xuống nhà máy | P7-4 |

Hai chốt kéo theo việc mới, đã gộp vào kế hoạch:

- **Q5** → phiếu phải có **đơn vị xử lý** = cặp *(pháp nhân xử lý, phòng ban xử lý)*, và phạm vi
  phải có bậc **"đơn vị mình xử lý"** (P2-2b). Không có hai thứ này thì người của Dego Organic
  không thấy được phiếu của công ty khác định tuyến sang, bằng bất kỳ bậc nào đang có.
- **Q3** → dùng **đúng một khái niệm "đơn vị"** cho cả ba việc: đơn vị xử lý phiếu, đơn vị sở hữu
  danh mục, đơn vị được chia sẻ danh mục. Phòng ban để trống = cả pháp nhân. Nhờ vậy nhà máy tuy là
  phòng ban vẫn sở hữu được bộ nhà cung cấp riêng.

Còn đúng **một mẩu dữ liệu** đang thiếu, không chặn việc viết code nhưng chặn bước nạp dữ liệu ở
P7-4: **danh sách phân loại nào được coi là nguyên liệu**.

---

## 2. Danh sách tính năng sau khi update

Đây là **trạng thái đích**, không phải trạng thái hiện tại. Cột "Việc" đọc như sau:
**Đã xong** = v2 đã có, không phải làm gì · **Port** = bê từ bản cũ sang · **Nâng cấp** = đã có
nhưng phải sửa cho đa pháp nhân · **Gộp** = nhập vào màn khác · **Bỏ** = không dựng ở v2 ·
**Mới** = chưa từng có.

### 2.1 Phân hệ Thu mua

| Tính năng | Việc | Giai đoạn | Ghi chú |
|---|---|---|---|
| Tổng quan thu mua | Nâng cấp | P2 | Lọc theo pháp nhân đang làm việc |
| **Yêu cầu mua hàng (chứng từ hợp nhất)** | Nâng cấp lớn | P6 | Dựng trên `tab_survey_request` (luồng YCBG), thêm mã hàng và các trường YCMH lên dòng; phần lớn không bắt buộc |
| Chọn phương án nhà cung cấp trên phiếu | Mới | P6 | Chưa có mã thì phương án gợi ý mã; có mã rồi thì lọc phương án theo mã |
| **Chọn phương án là tạo thẳng đơn mua hàng** | Mới | P6 | Nhân sự thu mua tạo; bỏ hẳn bước sinh YCMH trung gian |
| ~~Yêu cầu mua hàng bản cũ (`tab_purchase_request`)~~ | **Đóng băng chỉ đọc** | P6 | Giữ để tra cứu, không tạo mới, không sửa — nhờ vậy **không phải chuyển đổi dữ liệu** |
| Đơn mua hàng (gồm nhận hàng) | Nâng cấp | P2 | Kiểm tra chéo pháp nhân khi lấy dòng từ yêu cầu |
| Tiến độ mua hàng | Nâng cấp | P6 | Nuốt luôn phần tiến độ báo giá thành một bộ lọc |
| Tiến độ báo giá | ~~Bỏ~~ **Đã dựng lại** *(29/08, CR-227)* | P6 | Xem đính chính ở mục 2.7 |
| Màn xử lý Yêu cầu báo giá | ~~Bỏ~~ **Đã dựng lại thành màn riêng** *(29/08, CR-222)* | P6 | Xem đính chính ở mục 2.7 |
| Phiếu khảo sát (danh sách) | Đã xong | — | |
| Phiếu khảo sát (chi tiết NCC / sản phẩm) | Port | P6 | Giữ lại: đây là **sổ giá** dùng chung nhiều phiếu, không phải phần bị gộp |
| Báo cáo khảo sát | Đã xong | — | |
| Báo cáo mua hàng | Port | P3 | Thêm chiều pháp nhân ở P9 |
| **Định tuyến phân loại về đơn vị xử lý** | Mới | P7 | Thay và mở rộng màn "Phân công phụ trách" |

### 2.2 Phân hệ Tài chính *(hiện `enabled: false`, bật ở P3)*

| Tính năng | Việc | Giai đoạn |
|---|---|---|
| Công nợ | Port | P3 |
| Yêu cầu thanh toán + phiếu in | Port | P3 |
| Chặn một phiếu thanh toán trộn nhiều pháp nhân | Mới | P8 |
| Phiếu in lấy pháp nhân **của chứng từ** (tên, MST, địa chỉ, chữ ký, tài khoản) | Nâng cấp | P8 |
| **Sổ tiền treo theo (pháp nhân × nhà cung cấp)** | Mới | P8 |
| **Cấn trừ tiền treo vào công nợ** — lập phiếu thanh toán thì chọn khoản treo của đúng NCC đó; mỗi lần một dòng bút toán | Mới | P8 |
| **Hoàn tiền — đòi nhà cung cấp trả lại** | Mới | P8 |

### 2.3 Phân hệ Kho *(hiện `enabled: false`, bật ở P3)*

| Tính năng | Việc | Giai đoạn |
|---|---|---|
| Tồn kho | Port | P3 |
| Danh mục Kho | Port | P4 |

### 2.4 Danh mục dùng chung

| Tính năng | Việc | Giai đoạn | Ghi chú |
|---|---|---|---|
| **Lớp CRUD khai báo dùng chung của v2** | Mới | P4 | Hạ tầng; bản cũ khai 10 danh mục trong 772 dòng config, v2 chưa có lớp này |
| Sản phẩm | Port | P4 | |
| **Bản đè sản phẩm theo pháp nhân** | Mới | P5 | Công ty con sửa được phần được phép, **mã khóa cứng** |
| Nhà cung cấp — chi tiết | Port | P4 | Danh sách đã có ở phân hệ Sản xuất |
| Hợp đồng | Port | P4 | Kèm khai phạm vi, hiện **chưa lọc theo pháp nhân** |
| Phân loại · Đơn vị tính | Port | P4 | **Dùng chung toàn tập đoàn** (Q3) — không gắn sở hữu, chỉ ẩn/hiện theo đơn vị |
| **Đơn vị sở hữu** + bảng phạm vi dùng chung cho danh mục | Mới | P5 | Sản phẩm, NCC, kho, hợp đồng. `tab_warehouse` phải thêm cột |
| **Bản đè nhà cung cấp** (điều khoản thanh toán, dùng/ngưng) | Mới | P5 | |
| Khối **"Đơn vị được dùng"** trên màn tạo NCC / sản phẩm | Mới | P5 | Chính là "chỗ phân bổ xuống công ty con" |

### 2.5 Quyền và pháp nhân

| Tính năng | Việc | Giai đoạn |
|---|---|---|
| Công ty · Phòng ban · Nhân sự | Đã xong | — |
| Phân quyền vai trò · Phân quyền theo người | Đã xong | — |
| Bậc phạm vi **"công ty và cấp dưới"** | Mới | P2 |
| Bậc phạm vi **"chỉ các công ty được cấp"** | Mới | P2 |
| **Đơn vị xử lý** trên phiếu *(pháp nhân xử lý, phòng ban xử lý)* | Mới | P2 |
| Bậc phạm vi **"đơn vị mình xử lý"** — thay `proc` | Mới | P2 |
| **Ô chọn "Pháp nhân đang làm việc"** trên thanh tiêu đề | Mới | P2 |
| Màn phân quyền hiểu bậc mới + cấp theo cây công ty | Nâng cấp | P9 |
| Báo cáo tổng hợp nhiều pháp nhân | Mới | P9 |

### 2.6 Chưa xếp lịch → **đã xếp lịch ngày 19/08/2026**

Cấu hình hệ thống · Quản lý Import · Sao lưu CSDL · Phiếu hỗ trợ · Thông báo · Trang cá nhân —
nay có kế hoạch riêng ở [`13`](./13-ke-hoach-man-con-lai-v2.md), mã **MC-1 … MC-7**, 13,5–18,5 ngày
công, **không phải viết backend**. Tệp `13` bổ sung một màn mục này bỏ sót: **Đặt lại mật khẩu** —
v2 có màn *Quên mật khẩu* nhưng đường dẫn trong thư rơi vào trang 404, tức luồng đang gãy chứ không
chỉ là thiếu màn.

### 2.7 Hai màn bị bỏ, và vì sao

- **Tiến độ báo giá.** Khi Yêu cầu báo giá và Yêu cầu mua hàng là **một chứng từ**, hai màn tiến độ
  trở thành hai lát cắt của cùng một tập dữ liệu. Giữ hai màn thì cùng một phiếu hiện ở hai chỗ với
  hai cách đếm, người dùng hỏi "số nào đúng". Gộp thành **Tiến độ mua hàng** có bộ lọc theo bước
  (đang so giá / đang mua / đang nhận hàng).
  > **ĐÍNH CHÍNH 29/08/2026 (CR-227):** khách trực tiếp dựng lại màn **Tiến độ báo giá** ở v2
  > (`survey-progress-page.tsx`, route `/procurement/survey-progress`) và xếp lại menu Thu mua
  > theo đúng bản v1 — quyết định gộp vào Tiến độ mua hàng coi như **ĐẢO**. Khi P6 hợp nhất
  > chứng từ thì xem lại: hoặc giữ hai màn với chú thích cách đếm, hoặc quay về phương án gộp.
- **Màn xử lý Yêu cầu báo giá** (798 dòng ở bản cũ). Nhiệm vụ của nó — nhặt phương án nhà cung cấp
  rồi đẩy sang Yêu cầu mua hàng — biến mất theo Q4: chọn phương án xảy ra **ngay trong chi tiết
  phiếu** và đi **thẳng ra đơn mua hàng**, không còn bước chuyển phiếu nào ở giữa.
  > **ĐÍNH CHÍNH 29/08/2026 (CR-222):** khách yêu cầu giữ thói quen bản cũ, nên phần việc của
  > NSTM (gắn phương án / chốt rỗng / chốt hoàn thành) **quay về MÀN RIÊNG**
  > `survey-request-process-page.tsx` (route `/procurement/survey-requests/:id/process`).
  > Nửa còn lại của quyết định vẫn đứng: người yêu cầu **chọn phương án ngay trong chi tiết
  > phiếu**, không có bước chuyển phiếu trung gian.

~~Cộng lại, bỏ được **1134 dòng** khỏi việc phải port.~~ *(Hết đúng từ 29/08 — cả hai màn đã sống
lại theo hai đính chính ở trên.)* Kèm thêm một khoản được nữa: màn **Yêu cầu mua
hàng bản cũ** không bị bỏ mà chuyển sang **chỉ đọc**, nên `tab_purchase_request` không phải chuyển
đổi dữ liệu — v2 đã có sẵn màn danh sách và chi tiết cho nó, chỉ khóa các nút sửa.

---

## 3. Mười giai đoạn

Quy tắc chung cho mọi giai đoạn: **cơ sở dữ liệu cũ chỉ thêm không sửa · Thu mua không được gián
đoạn · thay đổi hành vi thì bật ở v2 trước, `frontend/` giữ nguyên · mỗi thay đổi phạm vi phải có
bài test "người công ty A không thấy chứng từ công ty B".**

### P0 — Chốt quyết định *(0 ngày công, cần một buổi làm việc)*

Tám câu Q1–Q8 **đã chốt hết ngày 18/08/2026** (mục 1). Còn lại ba việc:

1. **Danh sách phân loại nào là nguyên liệu** — chặn bước nạp dữ liệu ở P7-4.
2. Quyết chỗ đặt màn hình, nhỏ nhưng khó đổi sau: **Công nợ và Yêu cầu thanh toán nằm ở phân hệ Tài
   chính hay Thu mua**, và **các danh mục nằm ở phân hệ nào**.
3. Đo hiện trạng prod: mỗi pháp nhân đang có bao nhiêu chứng từ, bao nhiêu người dùng, bao nhiêu
   sản phẩm thật sự dùng chung giữa các công ty.

*Điều kiện đủ:* có danh sách phân loại nguyên liệu và bảng số liệu đo.

### P1 — Vá lỗ hổng phạm vi *(4–6 ngày)*

Đây là **việc phải làm trước tiên trong phần code**, vì hai lỗ hổng dưới đây hôm nay vô hại (chỉ
một pháp nhân dùng thật) nhưng bật đa pháp nhân là thành lộ dữ liệu chéo công ty ngay ngày đầu.

- **P1-1. XONG (CR-164, 24/08).** Bậc `proc` nay AND thêm pháp nhân qua helper `_proc_status_cond`
  trong `scoping.py` — áp cho `purchase_request` (`approved|dispatched`) và `purchase_order`
  (`approved`). **CHỈ thu hẹp khi người xem đã gắn `company_id` (>0)**; nhân sự chưa gắn
  (`company_id=0` — trạng thái prod hiện tại) giữ nguyên hành vi cũ để Thu mua không gián đoạn.
  `survey_request` không đụng: nhánh nhặt-việc của nó đã lọc theo `emp_code` (duy nhất mỗi người)
  nên không lộ chéo công ty.
- **P1-2. XONG (CR-086).** Chiều phòng ban đã khớp theo **ID** (`_dept_match`), tên chuỗi chỉ còn là
  đường lùi cho phiếu cũ `department_id=0`. Trùng hạng mục **DB15** ở `08`.
- **P1-3.** Bộ test rò rỉ chéo pháp nhân. **Đã có** cho bậc `proc` (`test_proc_loc_cong_ty_p1.py` —
  5 ca: gắn pháp nhân thì không nhặt phiếu công ty khác + tương thích ngược `company_id=0` + phiếu
  do mình tạo vẫn thấy). Các bậc own/dept/company/all đã có ở `test_pham_vi_khai_du_b07.py`. Còn
  thiếu: ca chạy qua **API/URL trực tiếp** trên dev (khâu nghiệm thu tay).

*Điều kiện đủ:* test P1-3 xanh; chạy lại toàn bộ `test/backend` không hỏng bài nào *(đã chạy 143 ca
nhánh proc + 26 ca phạm vi, xanh hết)*; trên dev, tài khoản thu mua của công ty con **không** truy
được phiếu của công ty khác qua API lẫn qua URL trực tiếp *(chờ nghiệm thu tay khi bật đa pháp nhân
trên dev)*.

### P2 — Nền pháp nhân *(8–12 ngày)*

- **P2-1.** Bậc **"công ty và cấp dưới"** — nở theo `tab_company.parent`. **Thêm giá trị mới, không
  đổi nghĩa bậc `company` cũ.**
- **P2-2.** Bậc **"chỉ các công ty được cấp"** — bỏ được lối cấu hình vòng vèo hiện nay (phải mượn
  bậc `all` rồi thêm include công ty, mà xóa hết include thì người đó thấy cả tập đoàn).
- **P2-2b.** Cột **đơn vị xử lý** trên phiếu = cặp *(pháp nhân xử lý, phòng ban xử lý)*, cộng bậc
  phạm vi **"đơn vị mình xử lý"**. Đây là bậc thay thế đúng nghĩa cho `proc` — sinh ra vì Q5 chốt
  Dego Organic là **phòng ban dùng chung nhiều công ty** (xem mục 1). Cột này để trống với dữ liệu
  cũ; P7 mới là chỗ điền tự động.
- **P2-3.** **Pháp nhân đang làm việc** trên phiên đăng nhập: mặc định theo nhân sự, ai có quyền
  nhiều công ty thì đổi được; gửi kèm mỗi lần gọi API; mọi màn v2 lấy pháp nhân mặc định từ đây.
- **P2-4.** Luật kiểm tra chéo pháp nhân trên các mối nối chứng từ: yêu cầu → đơn hàng → nhận hàng
  → công nợ → thanh toán.
- **P2-5.** Tổng quan thu mua và các danh sách ở v2 lọc theo pháp nhân đang làm việc.

*Điều kiện cần:* xong P1. Ước lượng đã gồm P2-2b.
*Điều kiện đủ:* một tài khoản ở công ty cha, cấp bậc "công ty và cấp dưới", thấy đủ dữ liệu cây
con; tài khoản công ty con **không** thấy ngược lên; đổi pháp nhân đang làm việc thì mọi danh sách
đổi theo; tạo đơn mua hàng lấy dòng từ yêu cầu khác pháp nhân bị chặn có thông báo rõ; người thuộc
phòng ban dùng chung, cấp bậc "đơn vị mình xử lý", thấy đúng phiếu của **các công ty khác** có đơn
vị xử lý là phòng mình, và **không** thấy phiếu khác của những công ty đó.

### P3 — Port đợt 1 sang v2 *(10–14 ngày)*

Bốn màn **không bị đa pháp nhân và không bị việc gộp yêu cầu đụng tới**, port thẳng, dùng được ngay:

- **P3-1.** Công nợ *(bản cũ 277 dòng)*
- **P3-2.** Yêu cầu thanh toán + phiếu in *(464 dòng + trang in)*
- **P3-3.** Tồn kho *(436 dòng)*
- **P3-4.** Báo cáo mua hàng *(494 dòng)*
- **P3-5.** Bật phân hệ Tài chính và phân hệ Kho trong `module-registry.ts`

Quy tắc khi port: chỗ nào bản cũ **chép luật của backend xuống giao diện** (ví dụ
`frontend/src/utils/lead-time.ts`) thì **đừng chép lần thứ ba** sang v2 — để backend trả sẵn.

*Điều kiện cần:* không phụ thuộc P1/P2, **chạy song song được**.
*Điều kiện đủ:* `npm run check` ở `frontend-v2` sạch (typecheck 0 lỗi, lint 0 lỗi, test xanh); bốn
màn đối chiếu số liệu khớp bản cũ trên cùng bộ dữ liệu dev.

### P4 — Lớp CRUD khai báo và các danh mục *(12–16 ngày)*

- **P4-1.** **Lớp CRUD khai báo dùng chung của v2** — danh sách, chi tiết, bộ lọc, nhập/xuất, kiểm
  quyền, khai bằng cấu hình. Làm một lần, ba phân hệ dùng (Thu mua, Nhân sự, Văn thư).
- **P4-2.** Danh mục: Sản phẩm · Nhà cung cấp (chi tiết) · Hợp đồng · Kho · Đơn vị tính · Phân loại.
- **P4-3.** Khai phạm vi cho **hợp đồng**, **nhận hàng**, **lịch sử mua hàng** — ba entity này
  **không có trong `SCOPE_FIELDS`**, tức ai có quyền đọc là đọc hết mọi công ty.
  **Hợp đồng đã xong (CR-117, 21/08/2026)** — khai `company_id` + `created_by`, lọc ở cả 6 route,
  mặc định trong seed hạ xuống `company`. Còn **nhận hàng** và **lịch sử mua hàng**.

*Điều kiện cần:* P4-1 xong mới làm P4-2 (làm ngược lại là viết tay 6 màn rồi phải gỡ).
*Điều kiện đủ:* thêm một danh mục mới chỉ tốn một khối khai báo, không phải viết trang mới; test
P4-3 chứng minh hợp đồng của công ty khác không đọc được.

### P5 — Danh mục theo đơn vị *(9–13 ngày)*

- **P5-1.** **Đơn vị sở hữu** (`owner_unit` = cặp pháp nhân + phòng ban) cho sản phẩm, nhà cung cấp,
  kho, hợp đồng; cộng bảng phạm vi dùng chung `tab_master_scope` *(loại danh mục, mã, đơn vị được
  dùng)*. **Phân loại và đơn vị tính không gắn sở hữu** — dùng chung toàn tập đoàn theo Q3, chỉ
  ẩn/hiện. Dữ liệu cũ gán hết về DEGO (Q8) để hành vi không đổi.
- **P5-2.** Bảng **bản đè sản phẩm theo pháp nhân** + lớp đọc gộp gốc-và-bản-đè, có cờ tắt. Trường
  cho đè theo Q2; **giá và tồn kho không nằm ở đây** — tồn đã riêng sẵn theo `company_id`, giá thực
  mua đã nằm trên chứng từ; chỉ giá chuẩn/giá kế hoạch (nếu có) mới đặt ở bản đè.
- **P5-3.** Bản đè cho nhà cung cấp — tối thiểu `payment_terms` và dùng/ngưng dùng.
- **P5-4.** Màn danh mục ở v2 hiểu đơn vị: cha thấy hết, con thấy phần của mình cộng phần cha chia
  xuống; **ô mã khóa cứng ở bản đè**; màn tạo nhà cung cấp và sản phẩm có khối **"Đơn vị được
  dùng"** để phân bổ xuống công ty con ngay lúc tạo.

*Điều kiện cần:* P2 và P4 xong.
*Điều kiện đủ:* công ty con sửa tên hiển thị của một sản phẩm cha, mã không đổi, báo cáo và tồn kho
vẫn khớp số như trước khi sửa; nhà cung cấp tạo ở công ty con **không** hiện ở công ty khác cho tới
khi được tick chia sẻ; tắt cờ lớp đọc gộp thì hệ trở về hành vi cũ hoàn toàn.

### P6 — Gộp Yêu cầu báo giá và Yêu cầu mua hàng *(12–16 ngày — nặng nhất)*

Theo Q4: **chứng từ sống sót là `tab_survey_request`** (luồng của Yêu cầu báo giá), đổi tên chức
năng thành **Yêu cầu mua hàng**; `tab_purchase_request` đóng băng chỉ đọc. **Không chuyển đổi dữ
liệu cũ** — đó là chỗ rẻ hơn hẳn so với hướng cũ.

- **P6-1.** Thêm trường của YCMH lên `tab_survey_request_line`: **mã hàng**, kho nhận, ngày cần
  hàng, VAT dòng, `qty_ordered`, `qty_received`. Các trường nghiệp vụ khác (phân loại, số lượng,
  đơn vị, giá đề xuất, người phụ trách, trạng thái dòng) **đã có sẵn**.
- **P6-2.** Khối phương án: dòng **chưa có mã** thì phương án gợi ý mã (`system_product_code` đã có
  sẵn trên `tab_survey_request_option`), chọn xong điền mã lên dòng; dòng **đã có mã** thì lọc
  phương án theo đúng mã đó.
- **P6-3.** **Phân vai chốt phương án — CHỐT 24/08/2026.** Tách rõ hai hành động:
  *(a)* **Bộ phận yêu cầu CHỐT phương án** cho từng dòng (mỗi dòng chọn đúng một phương án NCC
  trong số phương án thu mua đã khảo sát). *(b)* **Nhân sự thu mua tạo thẳng đơn mua hàng** từ các
  dòng đã chốt, lấy giá/VAT/nhà cung cấp/thời gian giao từ bản chụp của phương án; bỏ hẳn bước sinh
  YCMH trung gian. Đúng lời khách: "bên yêu cầu chốt cái nào thì mình (thu mua) đi mua cái đó".
  *(Bản 1.2 trước ghi thu mua tự chọn phương án — nay đảo: quyền chốt phương án về bộ phận yêu
  cầu, thu mua chỉ khảo sát + thực thi đơn.)* Kéo theo: thêm quyền/hành động "chốt phương án" cho
  vai trò bộ phận yêu cầu, và một bước trạng thái dòng "đã chốt phương án" trước bước "đã lên đơn".
  Chỉnh máy trạng thái phiếu và trạng thái dòng cho khớp.
- **P6-4.** **Đồng bộ ngược** `qty_ordered` · `qty_received` · `line_status` từ đơn mua hàng về
  `tab_survey_request_line`. **Đây là chỗ dễ vỡ nhất của cả kế hoạch** — hôm nay nó đang đồng bộ về
  `tab_purchase_request_item`, và màn Tiến độ mua hàng đọc chính mấy cột đó. Viết test trước khi
  sửa.
- **P6-5.** Giai đoạn chuyển tiếp **hai nguồn cùng tồn tại**: đơn cũ vẫn bám YCMH cũ, đơn mới bám
  phiếu gộp. Tiến độ mua hàng phải đọc được cả hai; `pr_code` trên đơn mua hàng **giữ nguyên ý
  nghĩa**, thêm tham chiếu mới chứ không sửa tại chỗ.
- **P6-6.** Gộp hai màn tiến độ thành **Tiến độ mua hàng** có bộ lọc theo bước.
- **P6-7.** Phiếu khảo sát (chi tiết) port sang v2 — giữ nguyên vai trò **sổ giá**.
- **P6-8.** Bật bằng cờ tính năng; `frontend/` giữ nguyên hai màn cũ cho tới khi v2 chạy ổn.

*Điều kiện cần:* **P1 xong** *(đã xong 24/08)*. ~~P2 xong~~ — P2 hoãn, P6 làm độc lập với nền pháp
nhân (xem khối cập nhật §4). Bỏ **P6-7b** (map người xử lý theo cặp *pháp nhân, phòng ban*) khỏi
phạm vi P6, giữ cách phân bổ NSTM hiện tại.
*Điều kiện đủ:* một phiếu đi trọn vòng *yêu cầu → so phương án → chọn → đơn mua hàng → nhận hàng →
công nợ* trên dev, **không qua bước YCMH nào**; đơn cũ tạo trước ngày đổi vẫn chạy đúng tiến độ và
vẫn đồng bộ số lượng; phiếu YCMH cũ mở lên đọc được, không sửa được; tắt cờ là về đúng hành vi cũ.

### P7 — Định tuyến phân loại về đơn vị xử lý *(6–9 ngày)*

- **P7-1.** Bảng định tuyến *phân loại × pháp nhân yêu cầu → (pháp nhân, phòng ban) xử lý*, mở rộng
  từ `tab_category_assignee`. Đích đến là **cặp pháp nhân và phòng ban**, theo Q5: Dego Organic là
  **phòng ban dùng chung nhiều công ty**, đặt ở công ty mẹ; việc nó phục vụ công ty nào là do bảng
  này quyết, **không** phải do `company_id` của phòng ban quyết. `tab_department` giữ nguyên. Cấu
  trúc cặp cũng chịu được ngày mai Dego Organic tách thành pháp nhân riêng — chỉ sửa dữ liệu cấu
  hình, không sửa mã nguồn.
- **P7-2.** Màn cấu hình ở v2, thay màn "Phân công phụ trách".
- **P7-3.** Áp lúc tạo và lúc duyệt phiếu, **điền vào cột đơn vị xử lý** dựng ở P2-2b; không tìm
  được luật thì rơi về đơn vị mặc định và **ghi nhật ký**, không được im lặng.
- **P7-4.** Nạp ngược đơn vị xử lý cho phiếu cũ theo luật đang chạy tay hôm nay, để bậc phạm vi
  "đơn vị mình xử lý" không làm phiếu cũ biến mất khỏi danh sách của người đang xử lý chúng.

*Điều kiện cần:* P2-2b xong; P6-1 xong.
*Điều kiện đủ:* đổi một dòng cấu hình thì phiếu nguyên liệu mới chạy về nhà máy, phiếu cũ không bị
đổi ngược; người của phòng ban dùng chung thấy phiếu của nhiều công ty trong đúng một danh sách;
luồng phê duyệt **không** bị dùng để quyết pháp nhân (hai việc tách bạch).

### P8 — Công nợ theo pháp nhân và tiền treo *(7–11 ngày)*

- **P8-1.** Chặn phiếu thanh toán trộn nhiều pháp nhân.
- **P8-2.** Phiếu in lấy pháp nhân của chứng từ.
- **P8-3.** **Sổ tiền treo** theo (pháp nhân, nhà cung cấp): sinh khi duyệt chi dòng không có hóa
  đơn/công nợ — chính là các dòng `payable_id = 0` hôm nay đang đi ra mà không ghi sổ ở đâu. Theo
  Q7 **không đối chiếu với hệ kế toán**, chỉ ghi sổ trong hệ này.
- **P8-4.** **Cấn trừ**: lúc lập phiếu thanh toán cho nhà cung cấp, hiện số dư tiền treo của đúng
  nhà cung cấp đó và **cho chọn khoản để trừ vào**. Mỗi lần cấn trừ là một **dòng bút toán riêng**
  (tiền treo nào, công nợ nào, bao nhiêu, ai làm, khi nào). Không cộng thẳng vào `paid_amount`.
- **P8-5.** **Hoàn tiền**: đóng số dư bằng phiếu thu, ghi rõ đã đòi lại.
- **P8-6.** Ràng buộc: không cấn trừ quá số dư, không cấn trừ chéo pháp nhân, không sửa tay số đã
  trả mà không sinh dòng phân bổ.

*Điều kiện cần:* P2 xong.
*Điều kiện đủ:* chi 10 triệu không hóa đơn → sổ tiền treo tăng 10 triệu; cấn trừ 6 triệu vào công
nợ mới → công nợ giảm đúng 6, số dư treo còn 4, có 1 dòng bút toán; đảo dòng bút toán thì hai bên
về đúng trạng thái trước đó; **không ca nào tạo ra công nợ âm** (lỗi cũ `82ce6ad`).

### P9 — Báo cáo tổng và hoàn thiện quyền *(5–7 ngày)*

- **P9-1.** Màn phân quyền ở v2 hiểu bậc mới, cấp phạm vi theo cây công ty.
- **P9-2.** Báo cáo nhóm theo pháp nhân, cộng dồn theo cây (mua hàng, công nợ, tồn kho). Vì Q6 giữ
  **một dãy số chung**, nhìn mã phiếu không đoán ra công ty — nên **mọi danh sách và báo cáo phải
  có cột pháp nhân**, và không chỗ nào được suy pháp nhân từ mã.
- ~~**P9-3.** Đánh số chứng từ theo pháp nhân.~~ **Bỏ** — Q6 chốt giữ nguyên cách đánh số cũ.

*Điều kiện cần:* P2, P3, P8 xong.
*Điều kiện đủ:* tài khoản ở công ty cha xem được báo cáo hợp nhất và bóc tách được xuống từng công
ty con, số cộng dồn khớp tổng các phần.

---

## 4. Thứ tự và hai luồng chạy song song

> **CẬP NHẬT 24/08/2026 — P2 HOÃN, LÀM P6 TRƯỚC.** Khách chốt: tận dụng nền phạm vi hiện có
> (đã xong B-07 + P1) thay cho nền pháp nhân đầy đủ. Nhân sự **bắt buộc thuộc một công ty**
> (ràng buộc lưu trữ); "các công ty liên quan" cấu hình tay bằng `scope=all` + danh sách công ty
> được cấp — phòng Thu mua và Sản xuất tự đưa bảng phạm vi; vẫn có vai trò giám đốc thu mua /
> tổng giám đốc `scope=all` nắm hết. **P6 (gộp phiếu) làm ngay sau P1**, không chờ P2. **P2 thành
> nợ kỹ thuật**, quay lại **khi HRM chuẩn hết** (đã ghi ở [`02` mục 6](./02-dai-han.md)). Đường
> găng mới: **P1 (xong) → P6**. P6-7b (map người xử lý theo cặp *pháp nhân, phòng ban*) bỏ khỏi
> P6, giữ cách phân bổ NSTM hiện tại. Ba đánh đổi của việc hoãn P2: cấu hình phạm vi bằng tay dày
> lên khi nhiều pháp nhân · phải gắn `company_id` cho nhân sự trước khi bật · bậc `proc` nhặt-việc
> chỉ khóa đúng công ty của người đó *(muốn nhặt đa công ty thì dùng `scope=all` + include)*.

```
Luồng NỀN (backend)   P0 → P1 →[P6]→ P7 → P9     (P2 HOÃN — nợ kỹ thuật, trả khi HRM chuẩn)
                                                  P5, P8 kéo theo P2 nên hoãn cùng
Luồng GIAO DIỆN (v2)  P3 ────────→ P4             (P3 và P4 không chờ P1)
```

- **P0 → P1 là dây chuyền cứng còn lại.** P1 bịt lỗ hổng phạm vi (đã xong 24/08), là điều kiện đủ
  để bật cho nhiều công ty dùng chung mà không lộ dữ liệu chéo.
- ~~**P0 → P1 → P2 là dây chuyền cứng.** Không được nhảy cóc: P2 nới quyền xuyên công ty, mà P1 là
  chỗ bịt lỗ hổng, làm ngược thứ tự là mở rộng một hệ đang hở.~~ *(P2 đã hoãn — xem khối cập nhật
  trên. P6 không nới quyền xuyên công ty nên không dính lý do "làm ngược thứ tự".)*
- **P3 và P4 chạy song song ngay từ đầu**, không chờ nền, vì bốn màn ở P3 không đụng pháp nhân.
- **P5, P6, P8 chạy song song được** sau khi P2 xong, nếu có nhiều người.
- **P7 phải sau P6-1**; **P9 phải sau cùng.**

**Tổng ước lượng: 73–104 ngày công cho một người.** Hai người làm song song hai luồng thì đường
găng là P1 → P2 → P6 → P7 → P9, tức **35–50 ngày công**; luồng giao diện P3 → P4 → P5 chạy kèm
mất 31–43 ngày, không dài hơn.

Bản 1.1 giảm so với bản 1.0 (78–110) nhờ ba chốt: **Q4** cho phép giữ nguyên `tab_purchase_request`
nên bỏ được cả phần chuyển đổi dữ liệu, **Q6** bỏ hạng mục đánh số theo pháp nhân, **Q7** bỏ phần
đối chiếu tiền treo với kế toán.

---

## 5. Phương án rút gọn — hoãn tầng đa pháp nhân

Ngày 18/08/2026 khách hỏi thêm: *bỏ hẳn phần đa pháp nhân, phân quyền chỉ dựa trên phòng ban hoặc
công ty trong phạm vi vai trò, mọi tài nguyên khác dùng chung.* Đo lại từng giai đoạn thì đây là
phương án hợp lệ, nhưng nó rẻ ít hơn cảm giác ban đầu.

**Bỏ được đúng một giai đoạn.** Chỉ P5 biến mất trọn vẹn (9–13 ngày công), cộng vài mục nhỏ của P2
và P4. Tổng còn khoảng **62–89 ngày công**. **Đường găng không đổi, vẫn 35–50 ngày**, vì P5 nằm ở
luồng giao diện chạy song song chứ không nằm trên đường găng — bỏ nó tiết kiệm tiền công, không
tiết kiệm ngày giao. Khối lượng của kế hoạch này nằm ở P6 (gộp yêu cầu) và P3+P4 (port giao diện),
cả hai đều không dính đa pháp nhân.

| Giai đoạn | Không làm đa pháp nhân |
|---|---|
| P1 vá lỗ hổng phạm vi | Còn nguyên, và bắt buộc hơn |
| P2 nền pháp nhân | Còn khoảng hai phần ba — vẫn cần cây công ty, đơn vị xử lý, pháp nhân trên chứng từ |
| P3 · P4 · P6 · P7 · P8 · P9 | Còn nguyên |
| **P5 danh mục theo đơn vị** | **Bỏ hết** |

**Được và mất.** Trong ba thứ chốt ở Q1/Q2, chỉ mất một:

| Yêu cầu | Dùng chung hết thì sao |
|---|---|
| Giá riêng theo công ty | **Còn** — giá nằm ở chứng từ, `tab_product` vốn không có cột giá (D-025) |
| Tồn kho riêng | **Còn** — `tab_inventory` và `tab_inventory_move` đã có `company_id` |
| **Tên gọi riêng theo pháp nhân** | **Mất** — muốn tên khác phải đẻ mã khác, mà D-025 cấm tái dùng mã nên sẽ thành hai mã cho một thứ, hỏng báo cáo gom |
| YC1.2 cây cha–con + báo cáo tổng | **Còn** |
| YC3 công nợ và phiếu in theo công ty | **Còn** |
| YC4 tiền treo | **Còn** |

Mất thêm một thứ chưa ai nêu: danh mục dùng chung nghĩa là **ai đọc được nhà cung cấp thì thấy
toàn bộ danh sách NCC, điều khoản thanh toán và lịch sử giá của cả tập đoàn.** Đây là quyết định
thương mại, không phải kỹ thuật.

**Ba nợ kỹ thuật nhảy hạng thành lỗ hổng cấp một** nếu phòng ban thành trục phân quyền chính:

1. `department` là **chuỗi tên** chứ không phải id (N-006) — hai công ty cùng có "Phòng Thu Mua"
   là thấy chéo phiếu của nhau. Phải sửa **trước**, không phải sau.
2. Bậc `proc` **không lọc công ty** (P1-1) — thu mua công ty A thấy phiếu công ty B.
3. **Không có cây phòng ban** (bỏ ở bản 2.1) — trưởng phòng lớn phải khai tay từng phòng con vào
   phạm vi. Chịu được ở quy mô mười phòng, không chịu được ở bốn mươi.

**ĐÃ CHỐT ngày 18/08/2026: hoãn P5 chứ không xóa P5.** P5 chỉ **thêm bảng mới** (`tab_product_company`, bảng sở
hữu danh mục), không sửa bảng cũ, nên hoãn không phát sinh phí — sang năm làm vẫn đúng giá đó.
Ngược lại P1 và P2 hoãn thì càng lâu càng đắt vì dữ liệu tích lũy rồi mới vá quyền phải rà lại
lịch sử. Điều kiện để hoãn an toàn: **P4 bắt buộc làm bằng lớp CRUD khai báo**, không viết tay
từng màn, để sau này thêm cột pháp nhân là sửa một chỗ.

---

## 6. Rủi ro

Bảng rủi ro đầy đủ ở `11` mục 6. Ba điều riêng của kế hoạch này:

| Rủi ro | Dấu hiệu sớm | Đường lui |
|---|---|---|
| **Đồng bộ ngược số lượng vỡ ở P6-4** — đơn mua hàng không cập nhật được về dòng yêu cầu | Tiến độ mua hàng lệch số, dòng kẹt trạng thái | Viết test trước khi sửa; giữ `pr_code` nguyên nghĩa; tắt cờ tính năng là quay về nguồn cũ |
| Viết tay từng màn danh mục vì "làm cho nhanh" | P4-2 chạy trước P4-1 | Mỗi màn viết tay là một chỗ phải sửa lại khi P5 thêm pháp nhân |
| P2 làm trước P1 | Cấp bậc "công ty và cấp dưới" khi bậc `proc` chưa lọc công ty | Thu hồi bậc mới, không phải sửa mã |

---

## 7. Không nằm trong kế hoạch này

- **Tắt `frontend/`.** Chỉ bàn khi P3, P4, P6 xong; còn Cấu hình hệ thống, Quản lý Import, Sao lưu
  CSDL, Phiếu hỗ trợ, Thông báo, Trang cá nhân chưa có ở v2.
- **Triển khai v2 lên prod.** Hiện `docker-compose.production.yml` chưa có service `erp`; dev đã có.
- **HRM, Văn thư, các phân hệ còn lại** — xem `02`, `06`, `10` và `van-thu/`.
- **685 sản phẩm dùng tên phân loại thô** (CR-083) — việc dữ liệu, độc lập với kế hoạch này.

---

## 8. Liên quan

- [`11` Đa pháp nhân và chuyển chức năng sang ERP v2](./11-da-phap-nhan-va-erp-v2.md) — đánh giá, số
  đo hiện trạng, tám câu phải chốt.
- [`08` Danh sách task củng cố](./08-danh-sach-task-cung-co.md) — **DB15** trùng với P1-2;
  **PQ11/PQ13/PQ14** nên gộp vào P1.
- [`07` Kiến trúc vỏ ERP](./07-kien-truc-vo-erp.md) — bảng chia entity vào phân hệ, dùng khi quyết
  chỗ đặt Công nợ và các danh mục ở P0.
