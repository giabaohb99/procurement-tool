# 11 — ĐA PHÁP NHÂN VÀ CHUYỂN CHỨC NĂNG SANG ERP V2

**Bản 1.2 — 18/08/2026.** Ghi lại yêu cầu nghiệp vụ nhận ngày 18/08/2026, đối chiếu với mã nguồn
đang chạy thật, và đề xuất thứ tự làm. Bản 1.1 thêm **mục 4.1 và 4.2 — câu trả lời cho cả tám câu
Q1–Q8**, chốt trong cùng ngày. Chỗ nào mục 3 lệch với mục 4.2 thì **lấy mục 4.2**: đáng kể nhất là
Q4, khách chọn hướng khác đề xuất ở mục 3.4 và hướng đó rẻ hơn.

> **BẢN 1.2 — ĐỌC TRƯỚC TIÊN.** Cuối ngày 18/08/2026 khách **chốt đi HƯỚNG RÚT GỌN**: chưa làm
> tầng đa pháp nhân cho danh mục. Xem **mục 4.3**. Mục 3.1, 4.1 và 4.2 phần Q1/Q2/Q3 giữ lại làm
> hồ sơ thiết kế cho ngày bật lên, **nhưng chưa thi hành**. `GĐ 2` ở mục 5 **hoãn**.

Tài liệu này **không** thay `07-kien-truc-vo-erp.md`. `07` trả lời "bọc Thu mua thành một phân hệ
như thế nào"; tài liệu này trả lời "cho nhiều pháp nhân dùng chung một hệ như thế nào".

---

## 0. Kết luận trước, giải thích sau

Bốn cụm yêu cầu mới đụng vào nền ở mức rất khác nhau:

| Yêu cầu | Nền hiện có đỡ được | Phải làm mới | Mức đập đi xây lại |
|---|---|---|---|
| **1. Đa pháp nhân** | Chứng từ đã có cột pháp nhân; bảng pháp nhân đã có cây cha–con | Danh mục dùng chung chưa có pháp nhân; phạm vi quyền chưa nở xuống công ty con | **Cao** |
| **2. Gộp Yêu cầu báo giá + Yêu cầu mua hàng** | Cả hai luồng đã chạy đủ, có sẵn khối chọn nhà cung cấp | Phải chốt là **một chứng từ hai chế độ** hay **hai chứng từ** | **Cao** |
| **3. Công nợ, phiếu in theo công ty** | Công nợ và yêu cầu thanh toán **đã có** cột pháp nhân | Chặn trộn pháp nhân trong một phiếu; phiếu in lấy pháp nhân của chứng từ | **Thấp** |
| **4. Tiền treo, cấn trừ, hoàn tiền** | Yêu cầu thanh toán đã cho dòng không gắn công nợ | Chưa có sổ tiền treo, chưa có bút toán cấn trừ | **Trung bình** |

Ba việc phải làm **trước** mọi thứ khác, vì mọi thứ khác đứng lên trên nó:

1. **Chốt mô hình sản phẩm dùng chung** (mục 3.1). Đây là chỗ nghẽn lớn nhất — mã sản phẩm đang là
   khóa duy nhất của cả hệ, bảy bảng nối nhau bằng chuỗi mã đó.
2. **Phạm vi quyền nở theo cây pháp nhân** (mục 3.2). Không có cái này thì "công ty cha quản công ty
   con" phải cấp tay từng công ty một cho từng người.
3. **Khái niệm "pháp nhân đang làm việc"** trên phiên đăng nhập (mục 3.3). Không có cái này thì người
   dùng nhiều công ty không biết mình đang tạo phiếu cho ai.

Đánh giá của khách — *"nhiều lúc phải đập đi xây lại khá khá"* — là **đúng**, nhưng chỗ phải đập
không nằm ở giao diện mà nằm ở **danh mục dùng chung** và **quy trình yêu cầu**. Phần công nợ,
thanh toán, nhận hàng thì gia cố là đủ.

---

## 1. Yêu cầu nghiệp vụ nhận ngày 18/08/2026

Chép lại theo đúng ý người đặt hàng, đánh số để các mục sau dẫn chiếu.

### YC1 — Đa pháp nhân (tenant)

- **YC1.1** DEGO là công ty cha, dưới nó là các công ty con. Mỗi công ty con có bộ phận thu mua
  riêng, nhân sự riêng. Công ty cha có thể có sản phẩm dùng chung: **cha tạo sản phẩm thì sản phẩm
  được nhân xuống công ty con; con sửa lại được, nhưng KHÔNG được sửa mã.**
- **YC1.2** Công ty cha quản được công ty con: ai có quyền trên công ty cha và được cấp vai trò theo
  công ty nào thì quản được công ty đó. Có **báo cáo tổng**.
- **YC1.3** Các cụm danh mục — sản phẩm, hợp đồng, nhà cung cấp, phân loại, tồn kho, đơn vị tính… —
  công ty con tạo được, nhưng tài khoản có quyền ở công ty cha thao tác được. *(Người đặt hàng tự
  ghi chú: chỗ này có thể chỉ là "một vai trò đủ quyền trải trên nhiều công ty".)*

### YC2 — Gộp Yêu cầu báo giá và Yêu cầu mua hàng

- Quy trình chạy **như Yêu cầu báo giá**, trường thông tin lấy **như Yêu cầu mua hàng**, phần lớn
  **không bắt buộc**.
- **YC2.1** Lý do: giá thị trường lên xuống thất thường kéo theo giá thành sản phẩm, nên bên yêu cầu
  và bên kinh doanh cần so được nhiều phương án, tìm nhà cung cấp tối ưu, và **họ là người quyết
  cuối cùng có mua hay không**. Họ chọn phương án, bên thu mua tương ứng đi mua.
- **YC2.2** Ngay trên phiếu yêu cầu sẽ **cấu hình phiếu thuộc pháp nhân nào**. Kinh doanh ở công ty
  cha yêu cầu thì thuộc cha; công ty con yêu cầu thì mặc định của chính nó. Quy định chi tiết nằm ở
  văn bản vận hành riêng, không nằm trong phần mềm.
- **YC2.3** Cần **một chỗ thiết lập điều kiện**: phân loại nào thì về công ty/đơn vị nào xử lý. Ví
  dụ nhà máy Dego Organic chỉ xử lý nguyên liệu, phòng Thu mua xử lý phần còn lại. *(Câu hỏi kèm
  theo: có tận dụng luồng phê duyệt được không?)* **Chỗ vướng:** trong hệ hiện tại Dego Organic và
  Thu mua đều là **phòng ban**, không phải pháp nhân; còn các nhà máy gia công bên ngoài lại thuộc
  công ty khác — hiện đang coi Dego Organic là một nhà máy ngoài gia công cho DEGO và DEGO quản
  được nó.

### YC3 — Công nợ và phiếu in theo công ty

Công ty nào thanh toán theo công ty đó. Phiếu in yêu cầu thanh toán cũng theo công ty đó.

### YC4 — Tiền treo

Có luồng thanh toán công nợ cho nhà cung cấp **không có mã hóa đơn**. Tiền đó coi là **tiền treo**.
Khi có đơn hàng từ nhà cung cấp đó thì **cấn trừ** lại, hoặc **hoàn tiền** (yêu cầu nhà cung cấp
trả lại).

---

## 2. Hiện trạng mã nguồn — đo ngày 18/08/2026

Đọc thẳng mã nguồn nhánh `erp-v2`, không phỏng đoán.

### 2.1 Bảng nào đã có pháp nhân, bảng nào chưa

**Đã có cột `company_id` (16 bảng):** hợp đồng, phòng ban, danh mục văn bản, văn bản, nhân sự,
nhận hàng, tồn kho, công nợ, yêu cầu thanh toán, lịch sử mua hàng, đơn mua hàng, yêu cầu mua hàng,
báo cáo, yêu cầu báo giá, phiếu hỗ trợ, tài khoản.

**Chưa có (danh mục dùng chung, đang là toàn cục):** `tab_product` (sản phẩm), `tab_supplier`
(nhà cung cấp), `tab_item_group` (phân loại), `tab_unit` (đơn vị tính), `tab_warehouse` (kho),
`tab_brand` (thương hiệu), `tab_category_assignee` (phân công phụ trách theo phân loại).

Nói cách khác: **chứng từ đã đa pháp nhân từ đầu, danh mục thì chưa.** YC1.3 đụng đúng vào nhóm sau.

### 2.2 Mã sản phẩm là khóa duy nhất toàn hệ

```
tab_product.code : String(50), unique=True     # duy nhất TOÀN HỆ, không kèm pháp nhân
```

Bảy bảng nối với sản phẩm bằng **chuỗi `product_code`**, không phải khóa ngoại: yêu cầu mua hàng,
đơn mua hàng, nhận hàng, tồn kho, luân chuyển kho, lịch sử mua hàng, phương án khảo sát. `CLAUDE.md`
và quyết định **D-025** ghi rõ: cấm đổi hoặc tái dùng `product_code`, cấm thêm bảng biến thể ở dưới.

Nhà cung cấp (`tab_supplier.code`), phân loại (`tab_item_group.code` và **cả `name`**), đơn vị tính,
kho, thương hiệu cũng đang `unique=True` toàn cục.

### 2.3 Phạm vi quyền chưa biết cây pháp nhân

`tab_company` **đã có** `parent` (0 là gốc) và `level` (1 tập đoàn · 2 công ty thành viên · 3 đơn vị
trực thuộc). Nhưng trong `app/core/scoping.py`, phạm vi `company` so sánh với **đúng một**
`profile["company_id"]` của người dùng, **không nở xuống công ty con**. Cây pháp nhân hiện chỉ để
hiển thị, chưa có nghĩa về quyền.

Hệ quả trực tiếp cho YC1.2: hôm nay muốn một người ở công ty cha nhìn được ba công ty con thì phải
cấp tay ba dòng "bao gồm công ty" cho người đó. Có 20 công ty con thì việc cấp quyền thành việc
nhập liệu.

### 2.4 Bộ máy duyệt đã có, nhưng không trả lời câu hỏi của YC2.3

Nhánh `erp-v2` đã có bộ bảng: `tab_approval_flow`, `tab_approval_node`, `tab_approval_switch`,
`tab_approval_instance`, `tab_approval_task`, `tab_approval_action`, `tab_delegation`. Trong đó
`tab_approval_switch` là nhánh rẽ theo điều kiện — nghe rất giống thứ YC2.3 cần.

**Nhưng luồng duyệt trả lời câu "ai duyệt", không trả lời câu "chứng từ này thuộc pháp nhân nào và
ai đi mua".** Hai câu đó phải tách: định tuyến quyết định **chủ sở hữu chứng từ**, xảy ra lúc tạo
phiếu; duyệt quyết định **người ký**, xảy ra sau đó. Trộn hai cái vào một bảng thì sau này sửa
người duyệt sẽ vô tình đổi cả pháp nhân của chứng từ.

Đã có sẵn `tab_category_assignee`: **mỗi phân loại một người phụ trách chính + một dự phòng**, dùng
lúc trưởng phòng duyệt yêu cầu để tự điền người phụ trách cho từng dòng. Đây chính là mầm của bảng
định tuyến YC2.3 — chỉ thiếu chiều pháp nhân và chiều phòng ban.

### 2.5 Công nợ và thanh toán

`tab_payable` đã có `company_id`, `supplier_code`, `invoice_no`, `amount/vat/total/paid_amount/
remaining`, trạng thái *Chờ TT · Trả một phần · Đã TT*.

`tab_payment_request` đã có `company_id`; dòng phiếu `tab_payment_request_line` có
**`payable_id = 0` nghĩa là dòng gõ tay, không gắn công nợ nào**. Nghĩa là hôm nay tiền đã đi ra
được mà không có khoản nợ đối ứng — **đó chính là "tiền treo" của YC4, chỉ khác là hệ chưa ghi sổ
nó ở đâu cả**, chi xong là mất dấu.

Ghi nhớ kèm theo: đã từng có lỗi phân bổ tiền dồn vào khoản nợ đã tất toán làm công nợ âm (sửa ở
`82ce6ad`). Bài học: **mọi lần cấn trừ phải là một dòng bút toán riêng**, không được cộng thẳng vào
`paid_amount` rồi thôi.

### 2.6 Giao diện v2 đang tới đâu

`frontend-v2` khai 13 phân hệ ở `src/app/router/module-registry.ts`; bật: nhân sự, thu mua, sản
xuất, văn bản, phê duyệt, hướng dẫn. Tắt: khách hàng, tài chính, kho, dự án, báo cáo, bán hàng,
hệ thống.

`frontend/` (bản đang chạy thật) còn **6 màn v2 chưa có**: Yêu cầu báo giá, Công nợ, Yêu cầu thanh
toán, Tiến độ mua hàng, Báo cáo, Phân quyền. Cộng thêm nợ **N-08**: các màn CR-074, CR-075, CR-077,
CR-081 mới làm ở bản cũ, chưa dựng lại ở v2.

---

## 3. Đánh giá từng yêu cầu

### 3.1 YC1.1 — "cha tạo sản phẩm, nhân xuống con, con sửa được nhưng không sửa mã"

Đọc theo nghĩa đen — nhân bản thật mỗi sản phẩm thành N dòng cho N công ty, giữ nguyên mã — thì
**không dựng được trên nền hiện tại**: `code` đang `unique=True` toàn hệ, và bảy bảng nối nhau bằng
chuỗi mã đó, nên hai dòng cùng mã sẽ làm mọi truy vấn nối bảng nhân đôi kết quả.

Ba đường đi:

| | Cách làm | Được | Mất |
|---|---|---|---|
| **PA1** *(khuyến nghị)* | Giữ **một dòng gốc duy nhất** trong `tab_product` + thêm bảng **bản đè theo pháp nhân** `tab_product_company` (pháp nhân, mã sản phẩm, các trường được phép sửa, cờ dùng/không dùng) | Mã vẫn duy nhất, bảy bảng cũ không phải đụng, không vi phạm D-025, dữ liệu cũ giữ nguyên hành vi | Đọc sản phẩm phải qua một lớp gộp gốc + bản đè; phải quy định rõ trường nào cho sửa |
| **PA2** | Nhân bản thật, đổi khóa duy nhất thành `(company_id, code)` | Đúng nghĩa đen yêu cầu | Phải sửa bảy bảng nối + mọi truy vấn + toàn bộ dữ liệu cũ trên prod; đây mới đúng là "đập đi xây lại"; rủi ro cao nhất trong cả tài liệu này |
| **PA3** | Giữ nguyên toàn cục, chỉ thêm bảng "sản phẩm này công ty nào được dùng" | Rẻ nhất, làm trong vài ngày | Công ty con **không sửa được gì**, trái YC1.1 |

**Đề xuất: PA1** — thực chất là PA3 cộng thêm lớp bản đè. Làm được từng bước: bước đầu chỉ có bảng
hiển thị/không hiển thị, bước sau mới mở dần các trường cho sửa.

Cần chốt với nghiệp vụ: **công ty con được sửa những trường nào?** Đề xuất mở: tên hiển thị, quy
cách, đơn vị tính, phân loại, nhà cung cấp mặc định, trạng thái dùng/ngưng. Đề xuất khóa: mã, nhóm
mã, các trường dùng để nối dữ liệu.

### 3.2 YC1.2 — công ty cha quản công ty con, báo cáo tổng

Việc phải làm: thêm phạm vi **"công ty và cấp dưới"** vào `scoping.py`, đọc `parent` của
`tab_company` để nở ra tập công ty con.

**Không được đổi nghĩa phạm vi `company` đang có** — trên prod đang có người được cấp phạm vi đó;
đổi nghĩa là âm thầm nới quyền cho họ. Thêm giá trị mới, ai cần thì cấp.

Báo cáo tổng đi kèm: báo cáo hiện lọc theo `company_id` đơn lẻ, phải cho nhóm theo pháp nhân và
cộng dồn theo cây.

### 3.3 YC2.2 — pháp nhân của phiếu, và "pháp nhân đang làm việc"

Chứng từ đã có `company_id` nên phần lưu trữ không phải làm gì. Phần thiếu là **phiên làm việc**:
một người thuộc nhiều công ty thì lúc tạo phiếu hệ phải biết đang tạo cho công ty nào.

Đề xuất: thêm **"pháp nhân đang làm việc"** — mặc định là công ty của nhân sự, ai có quyền nhiều
công ty thì đổi được bằng ô chọn trên thanh tiêu đề v2, gửi kèm theo mỗi lần gọi API. Đây là phần
**bắt buộc làm trước** cả YC1.1 lẫn YC2, vì nó là chỗ mọi màn hình lấy pháp nhân mặc định.

Kèm theo là luật kiểm tra chéo mà hiện chưa có: **không cho đơn mua hàng của pháp nhân A lấy dòng
từ yêu cầu của pháp nhân B**, không cho một phiếu thanh toán trộn công nợ của hai pháp nhân.

### 3.4 YC2 — gộp Yêu cầu báo giá và Yêu cầu mua hàng

Đây là luồng chứng từ lớn nhất của hệ, đang chạy thật hằng ngày, có tiến độ mua hàng và tiến độ
khảo sát bám theo. Không được gộp bằng cách xóa một cái.

Hai phương án:

- **A. Một chứng từ, hai chế độ.** Giữ `tab_purchase_request` làm gốc, thêm khối phương án nhà cung
  cấp (vốn đang nằm ở khảo sát) thành bảng con, thêm cờ chế độ *"cần so giá"* / *"mua thẳng"*.
  Yêu cầu báo giá cũ trở thành chế độ của cùng một chứng từ.
  *Được:* một mã phiếu, một chỗ theo dõi, đúng ý YC2.1. *Mất:* phải chuyển đổi dữ liệu cũ, và mọi
  màn hình bám vào hai bảng phải sửa.
- **B. Hai chứng từ, một màn hình.** Giữ nguyên hai bảng, chỉ dựng ở v2 một màn nhập chung tự quyết
  tạo bảng nào.
  *Được:* không đụng dữ liệu cũ, làm nhanh. *Mất:* nghiệp vụ vẫn thấy hai loại phiếu, không đạt
  đúng ý "gộp".

**Đề xuất: A, nhưng chỉ mở ở v2 và bật theo cờ tính năng**, bản cũ giữ nguyên hai màn cho tới khi
v2 chạy ổn. Đây là phần tốn công nhất trong toàn bộ kế hoạch.

### 3.5 YC2.3 — định tuyến phân loại về đơn vị xử lý

Câu hỏi "có tận dụng luồng phê duyệt được không?" — **có phần, nhưng không nên gộp** (lý do ở mục
2.4). Đề xuất tách đôi:

- **Bảng định tuyến** (mới, mở rộng từ `tab_category_assignee`): *phân loại × pháp nhân yêu cầu →
  đơn vị xử lý*. Đơn vị xử lý phải là **cặp (pháp nhân, phòng ban)** chứ không chỉ pháp nhân — vì
  đúng như nhận xét của khách, Dego Organic và Thu Mua hôm nay đều là **phòng ban**. Cấu trúc cặp
  này chịu được cả hai trường hợp: hôm nay Dego Organic là phòng ban, mai tách thành pháp nhân
  riêng thì chỉ sửa dữ liệu cấu hình, không sửa mã nguồn.
- **Luồng duyệt** giữ nguyên vai trò của nó: sau khi phiếu đã có chủ, ai ký thì hỏi
  `tab_approval_flow`.

Còn nhà máy gia công bên ngoài thuộc công ty khác: đây là quan hệ **đối tác**, không phải pháp nhân
nội bộ. Đề xuất giữ họ ở danh mục nhà cung cấp, và nếu cần DEGO quản được thì cấp tài khoản có
phạm vi hẹp, **không** dựng thành pháp nhân con — dựng thành pháp nhân con sẽ kéo họ vào báo cáo
tổng của tập đoàn.

### 3.6 YC3 — công nợ và phiếu in theo công ty

Nhẹ nhất trong bốn cụm, vì hai bảng đã có `company_id`. Việc còn lại:

1. Chặn một phiếu thanh toán trộn nhiều pháp nhân (kiểm tra lúc thêm dòng).
2. Phiếu in lấy pháp nhân **của chứng từ**, không lấy pháp nhân của người bấm in — gồm tên, mã số
   thuế, địa chỉ, chữ ký, số tài khoản.
3. Đánh số phiếu theo pháp nhân (cần chốt: mỗi công ty một dãy số riêng hay dùng chung dãy số?).
4. Báo cáo công nợ nhóm theo pháp nhân, cộng dồn theo cây.

### 3.7 YC4 — tiền treo, cấn trừ, hoàn tiền

Cần ba thứ mới:

- **Sổ tiền treo** theo *(pháp nhân, nhà cung cấp)*: sinh ra khi duyệt chi một dòng không có hóa
  đơn/công nợ; ghi số tiền, ngày, phiếu chi nguồn, số dư còn lại.
- **Cấn trừ**: khi công nợ mới của đúng nhà cung cấp và đúng pháp nhân xuất hiện, cho phép lấy tiền
  treo trừ vào. **Mỗi lần cấn trừ là một dòng phân bổ riêng** (tiền treo nào, công nợ nào, bao
  nhiêu, ai làm, khi nào) — đúng bài học của lỗi `82ce6ad`.
- **Hoàn tiền**: đóng số dư tiền treo bằng một phiếu thu, ghi rõ đã đòi lại.

Ràng buộc phải có: không cho cấn trừ quá số dư, không cho cấn trừ chéo pháp nhân, không cho sửa tay
`paid_amount` mà không sinh dòng phân bổ.

---

## 4. Những câu phải chốt trước khi viết code

| # | Câu hỏi | Chặn việc gì |
|---|---|---|
| Q1 | Sản phẩm dùng chung theo **PA1 bản đè** hay **PA2 nhân bản thật**? | Toàn bộ YC1.1, và cả YC1.3 |
| Q2 | Công ty con được sửa **những trường nào** của sản phẩm cha? | Thiết kế bảng bản đè |
| Q3 | Nhà cung cấp, hợp đồng, phân loại, đơn vị tính, kho: **dùng chung toàn tập đoàn** hay **mỗi công ty một bộ**? | YC1.3 — mỗi cái một câu trả lời, đừng trả lời gộp |
| Q4 | Gộp yêu cầu theo **A (một chứng từ hai chế độ)** hay **B (hai chứng từ một màn hình)**? | YC2, phần tốn công nhất |
| Q5 | Dego Organic rốt cuộc là **phòng ban**, **pháp nhân con**, hay **nhà cung cấp gia công**? | YC2.3, và cả cách tính báo cáo tổng |
| Q6 | Mã chứng từ đánh số **riêng theo pháp nhân** hay **chung một dãy**? | YC3, và không sửa ngược được sau khi đã phát hành |
| Q7 | Tiền treo có phải **đối chiếu với kế toán** không (hệ kế toán riêng đang chạy trên VPS)? | YC4 |
| Q8 | Dữ liệu cũ trên prod quy về pháp nhân nào — tất cả về DEGO, hay chia lại theo phòng ban? | Mọi bước chuyển đổi dữ liệu |

Chưa có Q1, Q4, Q5 thì **không nên bắt đầu viết**; ba câu còn lại có thể vừa làm vừa chốt.

### 4.1 Trả lời nhận ngày 18/08/2026

**Q5 — ĐÃ CHỐT: Dego Organic là PHÒNG BAN**, và là *phòng ban dùng chung của nhiều công ty*.

Chốt như vậy kéo theo một thay đổi thiết kế phải ghi lại ngay, vì nó không hiển nhiên:

- `tab_department` đang có `company_id`, tức **một phòng ban thuộc đúng một công ty**. Phòng ban
  phục vụ nhiều công ty không khớp cấu trúc đó. **Không sửa `tab_department`** — để phòng ban dùng
  chung nằm ở công ty mẹ, việc phục vụ công ty nào là do **bảng định tuyến** quyết (YC2.3), không
  phải do cột `company_id` của phòng ban quyết.
- Hệ quả nặng hơn: phiếu của **công ty B** được định tuyến về phòng ban thuộc **công ty mẹ**, nên
  người của Dego Organic **không thể thấy phiếu đó bằng bất kỳ bậc phạm vi nào đang có** — `company`
  so với công ty của chính họ, `dept` so với phòng ban của người tạo phiếu, còn `proc` thì thấy
  **mọi** phiếu đã duyệt của **mọi** công ty (chính là lỗ hổng P1-1).
- Vì vậy phiếu phải có thêm **đơn vị xử lý** = cặp *(pháp nhân xử lý, phòng ban xử lý)*, tách khỏi
  *pháp nhân yêu cầu* và *phòng ban người yêu cầu*; và phạm vi phải có thêm bậc **"đơn vị mình xử
  lý"**. Đây chính là bậc thay thế đúng nghĩa cho `proc`. Cột `assignee_id` / `assignee` hiện có là
  **người** phụ trách, không phải **đơn vị** — không dùng thay được.

**Q1 — khuyến nghị PA1, chờ xác nhận.** Câu hỏi của khách: *"có mô hình nào chung mã nhưng khác tên
cho từng pháp nhân không, hay chỉ clone khác `company_id` thôi?"* Có, và đó đúng là PA1 (mục 3.1):
**một dòng gốc + bảng bản đè theo pháp nhân**.

```
tab_product           (gốc — mỗi mã ĐÚNG MỘT dòng cho cả tập đoàn)
    code (unique)   name   unit   item_group   spec   owner_company_id ...

tab_product_company   (bản đè — mỗi cặp (pháp nhân, mã) nhiều nhất một dòng)
    company_id + product_code   (unique theo cặp)
    name_override, spec_override, unit_override, item_group_override,
    default_supplier_id, is_active, created_by, updated_at
```

Đọc một sản phẩm cho pháp nhân X = lấy dòng gốc rồi lấy bản đè của X phủ lên
(`name = override.name or goc.name`). Công ty con **không cần nhân bản gì cả**: cha tạo xong là con
thấy ngay; con sửa tên thì mới sinh một dòng bản đè; con ngưng dùng thì `is_active = false` chứ
không xóa dòng gốc.

Vì sao **không** chọn "clone khác `company_id` thôi":

| | Bản đè (PA1) | Clone theo `company_id` (PA2) |
|---|---|---|
| Khóa duy nhất | `code` giữ nguyên duy nhất toàn hệ | Phải đổi thành `(company_id, code)` |
| Bảy bảng nối bằng chuỗi `product_code` | **Không phải đụng** | Mọi phép nối phải thêm `company_id`, thiếu một chỗ là kết quả nhân đôi |
| Dữ liệu prod đang chạy | Giữ nguyên | Phải chuyển đổi toàn bộ, không có cửa sổ dừng hệ |
| Cha sửa quy cách sản phẩm | Con nào chưa đè thì **tự cập nhật theo** | Phải chạy tác vụ đẩy xuống N công ty, con nào lỡ sửa rồi thì phải xử lý xung đột |
| Báo cáo tổng tập đoàn | Gom theo mã là ra ngay | Phải gom N dòng khác `id` về một mã |
| D-025 (cấm đổi/tái dùng `product_code`) | Không vi phạm | Vi phạm tinh thần |
| Giá phải trả | Mọi chỗ đọc sản phẩm phải đi qua **một lớp gộp duy nhất**; truy vấn thẳng `tab_product` là sai | Rẻ về mặt khái niệm, đắt nhất về mặt thi công |

Một điểm yên tâm cho cả hai phương án: chứng từ **đã chụp sẵn** `product_name`, `item_group`, `unit`
xuống từng dòng (`tab_purchase_request_item`), nên đổi tên hiển thị ở bản đè **không làm sai lịch
sử** — phiếu cũ in ra vẫn đúng tên lúc lập.

**Q2 — diễn đạt lại cho dễ hiểu.** Câu này chỉ có nghĩa nếu Q1 chọn PA1, và nó hỏi đúng một việc:
*khi công ty con mở một sản phẩm của cha ra, ô nào cho gõ, ô nào để xám?* Đề xuất mặc định:

| Trường | Con sửa được? | Vì sao |
|---|---|---|
| Mã sản phẩm | **Khóa** | Là hạt nối của bảy bảng; đổi là hỏng lịch sử (D-025) |
| Tên hiển thị | Cho sửa | Chính là ý "chung mã khác tên" |
| Quy cách, mô tả | Cho sửa | Mỗi nơi diễn đạt một kiểu |
| Đơn vị tính | Cho sửa, **cảnh báo** | Đổi đơn vị làm lệch so sánh số lượng giữa các công ty |
| Phân loại | Cho sửa | Vì phân loại quyết định định tuyến (YC2.3), mỗi công ty phân khác nhau là bình thường |
| Nhà cung cấp mặc định | Cho sửa | Mỗi công ty mua một nguồn |
| Dùng / ngưng dùng | Cho sửa | Con không bán mặt hàng đó thì ẩn đi |
| Nhóm mã, các trường dùng để nối dữ liệu | **Khóa** | Cùng lý do với mã |

Chốt được bảng này thì bảng `tab_product_company` khai xong; chưa chốt thì làm bước đầu chỉ với
`is_active` (hiện/ẩn), các ô còn lại mở dần.

### 4.2 Trả lời đợt hai — Q1, Q2, Q3, Q4, Q6, Q7, Q8

**Q1 + Q2 — ĐÃ CHỐT: *"mỗi công ty có giá riêng, tồn kho riêng, tên gọi riêng, chỉ giống nhau về
mã"*.** Câu này chính là định nghĩa của mô hình bản đè, và ba phần của nó ở ba chỗ khác nhau —
quan trọng là **đừng nhét cả ba vào một bảng**:

| Yêu cầu | Chỗ giải quyết | Phải làm gì thêm |
|---|---|---|
| **Tồn kho riêng** | `tab_inventory` và `tab_inventory_move` **đã có `company_id`** | Không phải làm gì. Chỉ cần khai phạm vi cho đúng |
| **Giá riêng** | `tab_product` **không có cột giá nào** (cố ý — D-025). Giá nằm ở phương án khảo sát, đơn mua hàng, lịch sử mua — mà mọi chứng từ đó đều có `company_id` | Không phải làm gì cho giá *thực mua*. Nếu muốn thêm **giá chuẩn / giá kế hoạch theo công ty** thì đặt ở bảng bản đè, **tuyệt đối không** thêm cột giá vào `tab_product` |
| **Tên gọi riêng** | Bản đè | `name_override` và `invoice_name_override` (sản phẩm có tới bốn tên: `name`, `invoice_name`, `legal_name`, `hh_name` — chốt rõ tên nào cho đè) |
| **Chung mã** | `tab_product.code` giữ `unique` toàn hệ | Không phải làm gì |

Nói ngắn: **clone cho riêng hết cả `id`, rồi phải dán lại phần "chung mã" bằng tay; bản đè cho
chung mã sẵn, rồi mở riêng từng phần.** Yêu cầu của khách nghiêng hẳn về vế thứ hai.

**Q3 — ĐÃ CHỐT hướng: tách riêng theo pháp nhân, có chỗ phân bổ xuống công ty con khi tạo.** Kèm
câu hỏi ngược của khách: *"khổ cái nhà máy là phòng ban"*.

Đề xuất: dùng **đúng một khái niệm "đơn vị" = cặp (pháp nhân, phòng ban)** cho cả ba việc — đơn vị
xử lý phiếu (Q5), đơn vị sở hữu danh mục (Q3), và đơn vị được chia sẻ danh mục. Phòng ban để trống
nghĩa là "cả pháp nhân". Nhờ vậy nhà máy là phòng ban vẫn sở hữu được bộ nhà cung cấp riêng bên
trong DEGO, mà mai kia tách thành pháp nhân thì chỉ sửa dữ liệu cấu hình.

Cấu trúc dùng chung cho mọi danh mục: **một dòng gốc + `owner_unit` + bảng phạm vi
`tab_master_scope` (loại danh mục, mã, đơn vị được dùng) + bản đè nếu cần sửa trường.** Màn tạo nhà
cung cấp có thêm khối "Đơn vị được dùng" — mặc định chỉ đơn vị tạo, tick thêm công ty con nếu muốn
chia xuống. Đó đúng là "chỗ phân bổ xuống công ty con" mà khách hỏi.

Nhưng **không nên tách hết cả sáu danh mục**, vì hai cái sau là *từ vựng*, không phải *dữ liệu*:

| Danh mục | Đề xuất | Vì sao |
|---|---|---|
| Nhà cung cấp | Một dòng gốc theo **mã số thuế** + phạm vi theo đơn vị + bản đè (`payment_terms`, `is_active`) | Công nợ vốn đã riêng theo pháp nhân rồi; nhân bản NCC làm hỏng báo cáo tổng và tra cứu theo MST |
| Sản phẩm | Như Q1 | |
| Kho | **Riêng hẳn** theo đơn vị — `tab_warehouse` chưa có `company_id`, phải thêm | Kho là chỗ vật lý, không có nghĩa dùng chung |
| Hợp đồng | **Riêng hẳn** theo pháp nhân (đã có `company_id`, thiếu khai phạm vi) | Là quan hệ pháp lý của một pháp nhân |
| Phân loại | **Dùng chung**, chỉ ẩn/hiện theo đơn vị | `tab_item_group.name` đang `unique` toàn hệ, và phân loại là **khóa của bảng định tuyến** (YC2.3) lẫn khóa gom nhóm của báo cáo tổng. Mỗi công ty một bộ phân loại là vỡ cả hai |
| Đơn vị tính | **Dùng chung** | "kg" của công ty A phải là "kg" của công ty B, không thì không cộng được số liệu |

**Q4 — ĐÃ CHỐT, và chốt khác đề xuất ở mục 3.4 theo hướng rẻ hơn.** Khách chốt: giữ **luồng của
Yêu cầu báo giá**, thêm các trường của Yêu cầu mua hàng lên **dòng hàng** (mã hàng…), tên chức năng
gọi là **Yêu cầu mua hàng**; dòng chưa có mã thì phương án gợi ý mã, dòng có mã rồi thì lọc phương
án theo mã; **chọn phương án xong tạo thẳng đơn mua hàng** (nhân sự thu mua tạo), chỉnh lại trạng
thái cho khớp.

Đọc lại mã nguồn thì cách này **rẻ hơn phương án A cũ**, vì phần lớn đã có sẵn:

- `tab_survey_request_line` đã có `item_group`, `requirement_detail`, `request_qty`, `uom`,
  `proposed_price`, `assignee`, `line_status`, `no_option`.
- `tab_survey_request_option` đã có `system_product_code`, `is_chosen`, `chosen_by`, cùng bộ snapshot
  giá / VAT / thời gian giao / nhà cung cấp — đúng cái "phương án có mang mã" và "lọc phương án theo
  mã" mà khách mô tả.
- `tab_purchase_order` đã có **cả `pr_code` lẫn `survey_code`**.

Nên chứng từ sống sót là **`tab_survey_request`**, còn `tab_purchase_request` **đóng băng ở chế độ
chỉ đọc** để tra cứu — **không phải chuyển đổi dữ liệu cũ**, đây là điểm được lớn nhất. Bỏ luôn ý
"hai chế độ" ở mục 3.4: phân biệt bằng **dòng đã có mã hay chưa có mã**, không cần cờ chế độ.

Chỗ khó nhất, phải viết test trước khi sửa: hiện **đơn mua hàng đồng bộ ngược** `qty_ordered`,
`qty_received`, `line_status` về `tab_purchase_request_item`, và màn Tiến độ mua hàng đọc chính các
cột đó. Đổi nguồn phiếu thì phần đồng bộ ngược phải trỏ sang `tab_survey_request_line`, mà trong
giai đoạn chuyển tiếp **hai nguồn cùng tồn tại** (đơn cũ vẫn bám YCMH cũ) — nên Tiến độ mua hàng
phải đọc được cả hai, và `pr_code` phải giữ nguyên chứ không sửa tại chỗ.

**Q6 — ĐÃ CHỐT: mã chứng từ giữ nguyên như cũ, một dãy số chung, không tách theo pháp nhân.** Bỏ
được một hạng mục khỏi kế hoạch. Đổi lại phải nhớ hai điều: **không được suy ra pháp nhân từ mã
phiếu**, và mọi danh sách/báo cáo phải có **cột pháp nhân** vì nhìn mã không đoán ra.

**Q7 — ĐÃ CHỐT: tiền treo không đối chiếu với kế toán.** Chỉ cần: khi chi cho một nhà cung cấp mà
không có hóa đơn thì **ghi nhận số tiền treo của nhà cung cấp đó**; lần sau thanh toán hóa đơn của
đúng nhà cung cấp đó thì **cho chọn khoản tiền treo** để cấn trừ. Bỏ phần đối chiếu hai chiều với
hệ kế toán. Giữ nguyên ràng buộc: mỗi lần cấn trừ là **một dòng phân bổ riêng**, không cấn trừ quá
số dư, không cấn trừ chéo pháp nhân.

**Q8 — ĐÃ CHỐT: dữ liệu cũ về DEGO hết; phiếu nào thuộc nguyên liệu thì đơn vị xử lý đẩy xuống nhà
máy.** Vì nhà máy là phòng ban (Q5), "đẩy xuống nhà máy" nghĩa là đặt **đơn vị xử lý = (DEGO, nhà
máy)**, không đổi `company_id` của phiếu. Còn thiếu đúng một mẩu dữ liệu để chạy được bước này:
**danh sách phân loại nào được coi là nguyên liệu** — xem `04-danh-muc-cho.md`.

---

### 4.3 Chốt cuối ngày 18/08/2026 — đi hướng rút gọn

Sau khi đo lại khối lượng, khách chốt: **chưa làm tầng đa pháp nhân cho danh mục.** Phân quyền dựa
trên **phòng ban và công ty trong phạm vi vai trò**; sản phẩm, nhà cung cấp, kho, đơn vị tính, phân
loại **dùng chung toàn tập đoàn**.

**Vì sao chốt được nhanh:** đo ra chỉ bỏ được đúng một giai đoạn (`12` P5, 9–13 ngày công), tổng
còn 62–89 ngày công, và **đường găng không đổi** vì P5 vốn chạy song song. Khối lượng thật nằm ở
gộp yêu cầu và port giao diện, không nằm ở đa pháp nhân. Chi tiết đo đạc ở `12` mục 5.

**Cái vẫn còn, không mất gì:** giá riêng theo công ty (giá nằm ở chứng từ), tồn kho riêng
(`tab_inventory` đã có `company_id`), cây công ty cha–con, báo cáo tổng, công nợ và phiếu in theo
công ty, tiền treo.

**Cái chấp nhận mất:**
1. **Tên gọi riêng theo pháp nhân** — cả tập đoàn dùng một tên cho một mã. Không được đẻ mã thứ hai
   để lách, vì D-025 cấm và sẽ vỡ báo cáo gom.
2. **Che danh mục giữa các công ty** — ai đọc được nhà cung cấp thì thấy toàn bộ danh sách, điều
   khoản thanh toán và lịch sử giá của cả tập đoàn. Đây là quyết định thương mại, đã cân nhắc.

**Hồ sơ giữ lại, chưa thi hành:** bản đè sản phẩm ở mục 4.1/4.2 (Q1, Q2), danh mục theo đơn vị
(Q3), và `GĐ 2` ở mục 5. Chỉ **thêm bảng mới**, không sửa bảng cũ, nên hoãn không phát sinh phí —
bật lên lúc nào cũng đúng giá đó.

**Đổi lại, ba việc sau lên hàng bắt buộc và phải làm TRƯỚC** vì phạm vi giờ là hàng rào duy nhất:

| # | Việc | Vì sao gấp |
|---|---|---|
| 1 | `department` đổi từ **chuỗi tên** sang id (N-006, DB15 ở `08`) | Hai công ty cùng có "Phòng Thu Mua" là thấy chéo phiếu của nhau |
| 2 | Bậc `proc` phải **lọc công ty** (`12` P1-1) | Thu mua công ty A đang thấy phiếu công ty B |
| 3 | Quyết có cần **cây phòng ban** không | Bản 2.1 cố ý bỏ; giờ phòng ban là trục phân quyền chính, trưởng phòng lớn phải khai tay từng phòng con |

Việc kế tiếp: **`12` P1 — vá lỗ hổng phạm vi.** Chưa khởi công, khách hẹn làm sau.

---

## 5. Kế hoạch theo giai đoạn

Ba quy tắc xuyên suốt của bộ tài liệu này vẫn giữ: **cơ sở dữ liệu cũ chỉ thêm không sửa · Thu mua
không được gián đoạn · khai một chỗ dùng nhiều chỗ.** Thêm quy tắc thứ tư cho đợt này: **mọi thứ đa
pháp nhân bật ở v2 trước, bản cũ giữ nguyên hành vi.**

### GĐ 0 — Chốt (không viết code)

Trả lời Q1, Q4, Q5. Đo lại dữ liệu prod: mỗi pháp nhân đang có bao nhiêu chứng từ, bao nhiêu người
dùng, bao nhiêu sản phẩm thực sự dùng chung giữa các công ty.

*Điều kiện đủ:* có văn bản chốt ba câu, có bảng số liệu đo.

### GĐ 1 — Nền pháp nhân

1. Phạm vi **"công ty và cấp dưới"** trong `scoping.py`, đọc cây `tab_company`. Không đổi nghĩa
   phạm vi cũ.
2. **Pháp nhân đang làm việc** trên phiên đăng nhập + ô chọn ở thanh tiêu đề v2.
3. Luật kiểm tra chéo pháp nhân trên các chỗ nối chứng từ (yêu cầu → đơn hàng → nhận hàng → công
   nợ → thanh toán).
4. Kiểm thử: một người ở công ty cha thấy đủ dữ liệu cây con; người công ty con **không** thấy
   ngược lên.

*Điều kiện cần:* xong các hạng mục vá lỗ hổng phạm vi ở `08` (PQ11, PQ13, PQ14) — vì sắp cấp quyền
xuyên công ty, lỗ hổng cũ sẽ thành lỗ hổng xuyên pháp nhân.

### GĐ 2 — Danh mục theo pháp nhân *(HOÃN — xem mục 4.3)*

1. Thêm cột chủ sở hữu vào sáu bảng danh mục, dữ liệu cũ gán hết về pháp nhân gốc.
2. Bảng **bản đè sản phẩm theo pháp nhân** (theo phương án chốt ở Q1) + lớp đọc gộp.
3. Màn danh mục ở v2 hiểu pháp nhân: cha thấy hết, con thấy phần của mình cộng phần cha chia xuống.

### GĐ 3 — Chứng từ theo pháp nhân

Đánh số theo pháp nhân (nếu Q6 chọn vậy), phiếu in lấy pháp nhân của chứng từ, báo cáo nhóm theo
pháp nhân và cộng dồn theo cây.

### GĐ 4 — Gộp yêu cầu báo giá và yêu cầu mua hàng (ở v2)

Theo phương án chốt ở Q4. Bật bằng cờ tính năng, bản cũ giữ nguyên. Có kịch bản chuyển đổi dữ liệu
và đường lui.

### GĐ 5 — Định tuyến phân loại về đơn vị xử lý

Bảng *phân loại × pháp nhân yêu cầu → (pháp nhân, phòng ban) xử lý*, mở rộng từ
`tab_category_assignee`. Màn cấu hình ở v2. Luồng duyệt giữ nguyên vai trò riêng.

### GĐ 6 — Công nợ, thanh toán, tiền treo

Chặn trộn pháp nhân · sổ tiền treo · bút toán cấn trừ · hoàn tiền · báo cáo công nợ theo pháp nhân.

### GĐ 7 — Trả nợ giao diện v2

Sáu màn còn thiếu (Yêu cầu báo giá, Công nợ, Yêu cầu thanh toán, Tiến độ mua hàng, Báo cáo, Phân
quyền) + nợ N-08 (CR-074, CR-075, CR-077, CR-081). Xong bước này mới tính tới chuyện tắt `frontend/`.

**Thứ tự bắt buộc:** GĐ 0 → GĐ 1 → GĐ 2. Từ GĐ 3 trở đi chạy song song được. GĐ 7 chen vào lúc nào
cũng được vì không đụng backend.

---

## 6. Rủi ro và đường lui

| Rủi ro | Dấu hiệu sớm | Đường lui |
|---|---|---|
| Nới phạm vi quyền làm lộ dữ liệu chéo công ty | Người công ty con thấy chứng từ công ty khác | Phạm vi mới là **giá trị mới**, gỡ bằng cách thu hồi cấp phát, không phải sửa mã |
| Bản đè sản phẩm làm sai số liệu báo cáo cũ | Số tồn, số mua lệch so với bản cũ | Lớp đọc gộp có cờ tắt, tắt là về hành vi cũ |
| Gộp yêu cầu làm gián đoạn phòng ban đang dùng | Người dùng phàn nàn ngay ngày đầu | Chạy ở v2 sau cờ tính năng; bản cũ vẫn nguyên hai màn |
| Tiền treo ghi sai làm công nợ âm lần nữa | Công nợ âm, dòng đơn hàng kẹt không Hoàn thành | Mỗi lần cấn trừ là một dòng riêng, đảo được từng dòng |
| Chốt muộn Q1/Q4/Q5 rồi làm bù | Code đi trước quyết định | Không bắt đầu GĐ 2 và GĐ 4 khi chưa có câu trả lời |

---

## 7. Phần hạ tầng đã làm ngày 18/08/2026

Để v2 chạy được như một ứng dụng triển khai thật (không phải chỉ dev server):

- Thêm `docker/Dockerfile.erp.prod` — build tĩnh bằng Vite rồi phục vụ bằng nginx, `/api` proxy sang
  backend chung. Ảnh 96,4 MB.
- Thêm `docker/nginx.erp.prod.conf` — như bản của `frontend/` nhưng bỏ phần PWA (v2 chưa có service
  worker).
- Thêm service `erp` vào `docker-compose.dev.yml`, container `procurement-erp-dev`, chạy **song
  song** bản cũ chứ không thay thế. Prod **chưa** đụng tới.
- Thêm `.dockerignore` ở gốc kho mã. **Đây là một lỗi thật đã được vá:** trước đó không có tệp này
  nên bước `COPY frontend-v2/ /app/` kéo cả `node_modules` của máy Windows vào ảnh Linux, đè lên bản
  vừa cài; `vite build` chết với *"Unable to resolve @typescript/typescript-linux-x64"*.
- `Dockerfile.erp.prod` dùng `npm ci` kèm `package-lock.json` thay vì `npm install`, để chốt đúng
  TypeScript 5.9.3 theo D-027.

Còn lại (chưa làm, cần quyết): tên miền cho v2 (đề xuất `deverp.degoholding.vn`) và khai đường
tunnel Cloudflare trỏ về `procurement-erp-dev:80`.

---

## 8. Liên quan

- `07-kien-truc-vo-erp.md` — bọc Thu mua thành phân hệ, hợp đồng dữ liệu `/api/me/modules`.
- `08-danh-sach-task-cung-co.md` — các task PQ11, PQ13, PQ14 là **điều kiện cần** của GĐ 1.
- `van-thu/05-vong-doi-phien-ban.md` — đã bàn chuyện "clone văn bản xuống pháp nhân con có kiểm
  soát"; mô hình bản đè ở mục 3.1 nên thống nhất cách làm với chỗ đó.
- `doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md` — D-025, đọc trước khi đụng `tab_product`.
