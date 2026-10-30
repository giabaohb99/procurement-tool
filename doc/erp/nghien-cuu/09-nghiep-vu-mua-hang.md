# NGHIỆP VỤ MUA HÀNG

| | |
|---|---|
| Phiên bản | **2.0** — 30/10/2026 (dựng lại theo dạng giáo trình: thêm kế toán căn bản, danh sách tài khoản, loại mặt hàng, luồng duyệt theo loại) |
| Người viết | A5 Nghiên cứu nghiệp vụ |
| Trạng thái | Tài liệu nghiên cứu nghiệp vụ chuẩn, chưa phải tài liệu yêu cầu |
| Căn cứ | Cách SAP, Oracle, Odoo, Microsoft Dynamics dựng phân hệ Mua hàng · Chuẩn mực kế toán số 02 · Thông tư 99/2025 (số hiệu tài khoản giữ như Thông tư 200) |
| Cùng cụm | [`10` Nghiệp vụ Kho](./10-nghiep-vu-kho.md) · [`san-xuat/00` Nghiệp vụ Sản xuất](../san-xuat/00-tong-quan-nghiep-vu.md) · [`01` Luồng nối Mua hàng, Kho, Sản xuất](./01-luong-chuan-mua-hang-kho-san-xuat.md) |

Số tiền trong ví dụ là giả định. Thuế suất GTGT lấy 10% cho dễ tính. Chỗ dính quy định thuế cần kế toán xác nhận.

---

## Cách đọc tài liệu này

Tài liệu viết như một giáo trình. **Đọc từ trên xuống**, phần sau chỉ dùng những gì phần trước đã giải thích:

| Phần | Học gì | Đọc xong thì hiểu |
|---|---|---|
| **I. Nền tảng** | Mua hàng là gì, kế toán căn bản, các tài khoản | Đọc được một bút toán, biết tiền nằm ở đâu |
| **II. Tổ chức** | Ai làm gì, các loại chứng từ, các loại mặt hàng, ai duyệt | Biết một yêu cầu mua sẽ đi qua những ai |
| **III. Luồng chuẩn** | Nhu cầu phát sinh từ đâu, bảy chặng từ yêu cầu tới trả tiền | Biết thao tác từng bước trên phần mềm |
| **IV. Tiền** | Hóa đơn, các khoản chi phí, ví dụ có số | Biết giá vốn tính ra sao, nợ phát sinh lúc nào |
| **V. Trường hợp thường gặp** | Sự cố, hình thức mua đặc biệt, trả trước, nhập khẩu | Xử lý được tình huống ngoài luồng chuẩn |
| **VI. Tổng kết** | Ranh giới với phân hệ khác, tóm tắt một trang | Nhìn lại toàn bộ |
| **Phụ lục** | Thuật ngữ, bảng tra nhanh | Tra khi quên |

Người đã biết kế toán có thể bỏ qua mục 2 và 3.

---

## Mục lục

**PHẦN I. NỀN TẢNG**
- [1. Mua hàng là gì](#1-mua-hàng-là-gì)
- [2. Kế toán căn bản cho người không chuyên](#2-kế-toán-căn-bản-cho-người-không-chuyên)
- [3. Các tài khoản kế toán dùng trong mua hàng](#3-các-tài-khoản-kế-toán-dùng-trong-mua-hàng)

**PHẦN II. TỔ CHỨC**

- [4. Ai làm gì](#4-ai-làm-gì)
- [5. Chứng từ và trạng thái](#5-chứng-từ-và-trạng-thái)
- [6. Loại mặt hàng](#6-loại-mặt-hàng)
- [7. Luồng duyệt theo loại mặt hàng](#7-luồng-duyệt-theo-loại-mặt-hàng)

**PHẦN III. LUỒNG MUA HÀNG CHUẨN**

- [8. Nhu cầu mua phát sinh từ đâu](#8-nhu-cầu-mua-phát-sinh-từ-đâu)
- [9. Bảy chặng từ yêu cầu mua tới thanh toán](#9-bảy-chặng-từ-yêu-cầu-mua-tới-thanh-toán)

**PHẦN IV. TIỀN: HÓA ĐƠN, CHI PHÍ, VÍ DỤ**

- [10. Hóa đơn và thời điểm ghi nợ](#10-hóa-đơn-và-thời-điểm-ghi-nợ)
- [11. Các khoản chi phí khi mua](#11-các-khoản-chi-phí-khi-mua)
- [12. Ví dụ có số](#12-ví-dụ-có-số)

**PHẦN V. CÁC TRƯỜNG HỢP THƯỜNG GẶP**

- [13. Sự cố và hình thức mua đặc biệt](#13-sự-cố-và-hình-thức-mua-đặc-biệt)
- [14. Trả trước và nhập khẩu: cách cân bằng](#14-trả-trước-và-nhập-khẩu-cách-cân-bằng)

**PHẦN VI. TỔNG KẾT**

- [15. Ranh giới với Kho và Kế toán](#15-ranh-giới-với-kho-và-kế-toán)
- [16. Tóm tắt một trang](#16-tóm-tắt-một-trang)

**PHỤ LỤC**

- [A. Thuật ngữ](#phụ-lục-a-thuật-ngữ)
- [B. Bảng tra nhanh: khoản này ghi vào đâu](#phụ-lục-b-bảng-tra-nhanh-khoản-này-ghi-vào-đâu)

---

# PHẦN I. NỀN TẢNG

## 1. Mua hàng là gì

Mua hàng lo **toàn bộ việc mua của công ty**, từ lúc có người cần hàng đến lúc trả xong tiền cho nhà cung cấp (NCC). Phân hệ này phục vụ mọi phòng, không riêng Sản xuất.

| Phân hệ | Quan hệ với Mua hàng |
|---|---|
| Sản xuất | Sinh nhu cầu vật tư, đẩy đề xuất mua sang |
| Kho | Nhận hàng theo đơn mua, báo số thực nhận |
| Bán hàng | Sinh nhu cầu mua hàng về bán, hoặc giao thẳng cho khách |
| Kế toán | Nhận hóa đơn, ghi công nợ, chi tiền |

**Ba nguyên tắc:**
1. **Ba người khác nhau:** người mua đặt hàng, thủ kho nhận hàng, kế toán nhập hóa đơn.
2. **Đơn đã duyệt thì khóa.** Muốn đổi thì làm bản sửa đổi có số phiên bản và duyệt lại.
3. **Trả tiền theo hóa đơn đã đối chiếu**, không trả theo đơn mua.

---

## 2. Kế toán căn bản cho người không chuyên

### 2.1. Tài khoản kế toán là gì
Hình dung công ty có **một dãy ngăn kéo, mỗi ngăn đựng một loại giá trị**: ngăn tiền mặt, ngăn tiền ngân hàng, ngăn hàng trong kho, ngăn nợ nhà cung cấp, ngăn chi phí văn phòng… Mỗi ngăn có một **số hiệu**. Ngăn đó gọi là **tài khoản**.

- **111** là ngăn tiền mặt, **152** là ngăn nguyên vật liệu, **331** là ngăn nợ nhà cung cấp.
- Số hiệu theo chế độ kế toán doanh nghiệp. Từ 01/01/2026 áp dụng Thông tư 99/2025 thay Thông tư 200, phần lớn số hiệu giữ nguyên.

### 2.2. Bút toán, Nợ và Có
Mỗi nghiệp vụ là **chuyển giá trị từ ngăn này sang ngăn khác**, gọi là một **bút toán**.
- Ngăn **nhận** giá trị ghi bên **Nợ**.
- Ngăn **đưa** giá trị ghi bên **Có**.
- Hai bên **luôn bằng nhau**.

*Nợ* và *Có* ở đây chỉ là tên hai cột, không mang nghĩa nợ nần hằng ngày.

**Ví dụ:** mua 10 triệu nguyên liệu, chưa trả tiền.
```
Nợ 152   10.000.000    ← ngăn kho nguyên liệu tăng
   Có 331   10.000.000    ← ngăn nợ NCC tăng (mình nợ thêm)
```
Trả tiền:
```
Nợ 331   10.000.000    ← nợ NCC giảm
   Có 112   10.000.000    ← tiền ngân hàng giảm
```

### 2.3. Chín nhóm tài khoản
Chữ số đầu của số hiệu cho biết ngăn thuộc nhóm nào.

| Chữ số đầu | Nhóm | Hiểu đơn giản | Tăng thì ghi |
|---|---|---|---|
| **1** | Tài sản ngắn hạn | Thứ công ty đang có, dùng hết trong 1 năm: tiền, hàng trong kho, khoản người khác nợ mình | Nợ |
| **2** | Tài sản dài hạn | Thứ công ty có và dùng nhiều năm: máy móc, nhà xưởng | Nợ |
| **3** | Nợ phải trả | Công ty đang nợ người khác: nợ NCC, nợ thuế, nợ lương, nợ ngân hàng | Có |
| **4** | Vốn chủ sở hữu | Tiền chủ bỏ vào và lãi tích lũy | Có |
| **5** | Doanh thu | Tiền kiếm được từ bán hàng | Có |
| **6** | Chi phí kinh doanh | Tiền tiêu để làm ra và bán hàng | Nợ |
| **7** | Thu nhập khác | Tiền kiếm ngoài việc chính: bán máy cũ, tiền phạt NCC | Có |
| **8** | Chi phí khác | Tiền mất ngoài việc chính: phạt, mất mát, thuế thu nhập doanh nghiệp | Nợ |
| **9** | Xác định kết quả | Cuối kỳ gom doanh thu trừ chi phí để ra lãi hay lỗ | |

**Mẹo nhớ:**
- Tài sản (1, 2) và chi phí (6, 8): **tăng ghi Nợ**, giảm ghi Có.
- Nợ phải trả, vốn (3, 4), doanh thu và thu nhập (5, 7): **tăng ghi Có**, giảm ghi Nợ.
- Luôn đúng: **Tài sản = Nợ phải trả + Vốn chủ sở hữu.**

### 2.4. Hai bản báo cáo lớn
- **Bảng cân đối kế toán:** chụp ảnh tại một ngày. Có những gì (nhóm 1, 2), nợ ai (3), vốn bao nhiêu (4).
- **Báo cáo kết quả kinh doanh:** trong cả kỳ kiếm bao nhiêu (5, 7), tiêu bao nhiêu (6, 8), lãi hay lỗ.

Vì vậy mua máy trộn ghi **211** (tài sản, nằm ở bảng cân đối), không ghi thẳng vào **627** (chi phí, làm giảm lãi ngay). Máy dùng 8 năm thì chi phí được chia ra 8 năm.

### 2.5. Một vòng đời đọc thử
Mua 100 kg nguyên liệu 1 triệu, đem sản xuất, bán được 3 triệu:

| # | Việc | Bút toán | Ý nghĩa |
|---|---|---|---|
| 1 | Nhận hàng, có hóa đơn | Nợ 152 1.000.000, Nợ 1331 100.000 / Có 331 1.100.000 | Kho có thêm hàng, mình nợ NCC |
| 2 | Trả tiền NCC | Nợ 331 / Có 112: 1.100.000 | Hết nợ, tiền ngân hàng giảm |
| 3 | Xuất cho sản xuất | Nợ 621 / Có 152: 1.000.000 | Hàng ra khỏi kho, thành chi phí sản xuất |
| 4 | Gom chi phí vào sản phẩm đang làm | Nợ 154 / Có 621: 1.000.000 | Sản phẩm dở dang |
| 5 | Sản phẩm xong, nhập kho | Nợ 155 / Có 154: 1.000.000 | Có thành phẩm |
| 6 | Bán, xuất kho | Nợ 632 / Có 155: 1.000.000 | Giá vốn hàng đã bán |
| 7 | Hóa đơn bán | Nợ 131 3.300.000 / Có 511 3.000.000, Có 3331 300.000 | Khách nợ mình, có doanh thu |
| 8 | Tính lãi | 511 − 632 = 2.000.000 | Lãi gộp |

Nguyên liệu đi qua **152 → 621 → 154 → 155 → 632** rồi mới thành chi phí trên báo cáo lãi lỗ. Vì vậy **mua vật tư chưa phải là chi phí ngay** lúc mua.

---

## 3. Các tài khoản kế toán dùng trong mua hàng

### 3.1. Nhóm 1. Tài sản ngắn hạn

| TK | Tên | Hiểu đơn giản | Ví dụ |
|---|---|---|---|
| **111** | Tiền mặt | Tiền trong két | Tạm ứng 1 triệu cho nhân viên |
| **112** | Tiền gửi ngân hàng | Tiền trong tài khoản ngân hàng. 1121 tiền đồng, 1122 ngoại tệ | Chuyển khoản trả NCC |
| **131** | Phải thu khách hàng | Khách đang nợ mình | Bán chịu cho khách |
| **1331** | Thuế GTGT được khấu trừ | Thuế GTGT đã trả khi mua, được trừ vào thuế phải nộp | 10% trên hóa đơn mua |
| **1381** | Tài sản thiếu chờ xử lý | Hàng hoặc tiền bị thiếu, chưa biết ai chịu | Kiểm kê thiếu 50 chai |
| **1388** | Phải thu khác | Người khác nợ mình ngoài tiền hàng | Nhà gia công bồi thường hàng hỏng |
| **141** | Tạm ứng | Tiền đưa trước cho nhân viên đi mua, chờ quyết toán | Ứng tiền mua văn phòng phẩm |
| **151** | Hàng mua đang đi đường | Hàng đã là của mình nhưng chưa về kho | Hàng nhập khẩu còn trên tàu |
| **152** | Nguyên vật liệu | Vật tư để sản xuất | Dung dịch, chai, nhãn, K₂SO₄ |
| **153** | Công cụ dụng cụ | Đồ dùng nhiều lần, giá trị dưới 30 triệu | Pallet, khuôn, dụng cụ cầm tay |
| **154** | Chi phí sản xuất dở dang | Hàng đang làm dở, chi phí đang gom vào | Vật tư đã gửi nhà gia công |
| **155** | Thành phẩm | Hàng mình sản xuất ra, đã nhập kho | 10.000 chai thuốc đóng xong |
| **156** | Hàng hóa | Hàng mua về để bán lại, không chế biến. 1561 giá mua, 1562 chi phí thu mua | Mua phân bón về bán nguyên bao |
| **157** | Hàng gửi đi bán | Hàng đã giao đi, khách chưa nhận hoặc chưa xác nhận | Giao thẳng mà khách chưa ký biên bản |

### 3.2. Nhóm 2. Tài sản dài hạn

| TK | Tên | Hiểu đơn giản | Ví dụ |
|---|---|---|---|
| **211** | Tài sản cố định hữu hình | Tài sản sờ được, từ 30 triệu, dùng trên 1 năm | Máy trộn, xe tải |
| **213** | Tài sản cố định vô hình | Tài sản không sờ được | Phần mềm, bản quyền |
| **214** | Hao mòn tài sản cố định | Phần giá trị tài sản đã dùng mất, cộng dồn qua các tháng khấu hao | Máy 320 triệu, sau 2 năm hao mòn 80 triệu |
| **241** | Xây dựng cơ bản dở dang | Tài sản đang lắp đặt hoặc đang xây, chưa dùng được | Máy đang lắp, chạy thử |
| **242** | Chi phí trả trước | Tiền đã trả cho nhiều tháng, chia dần vào chi phí | Bảo hiểm cả năm, pallet đem ra dùng |

### 3.3. Nhóm 3. Nợ phải trả

| TK | Tên | Hiểu đơn giản | Ví dụ |
|---|---|---|---|
| **331** | Phải trả người bán | Mình nợ NCC. Số dư nằm bên Nợ thì ngược lại: mình đã ứng trước, NCC đang giữ tiền của mình | Mua chịu 30 ngày |
| **3331** | Thuế GTGT đầu ra | Thuế GTGT thu của khách khi bán, phải nộp nhà nước | 10% trên hóa đơn bán |
| **33312** | Thuế GTGT hàng nhập khẩu | Thuế GTGT phải nộp khi nhập khẩu | Nộp ở hải quan |
| **3332** | Thuế tiêu thụ đặc biệt | Thuế riêng cho vài mặt hàng | Ít gặp |
| **3333** | Thuế xuất nhập khẩu | Thuế nhập khẩu phải nộp | 3% trên trị giá hàng |
| **33381** | Thuế bảo vệ môi trường | Thuế riêng cho xăng dầu, túi nilon | Ít gặp |
| **334** | Phải trả người lao động | Lương còn nợ nhân viên | Lương tháng trước |
| **3381** | Tài sản thừa chờ giải quyết | Hàng thừa, chưa rõ của ai | Kiểm kê thừa 20 bao |
| **341** | Vay | Nợ ngân hàng | Vay mua máy |

### 3.4. Nhóm 5, 7. Doanh thu và thu nhập

| TK | Tên | Hiểu đơn giản | Ví dụ |
|---|---|---|---|
| **511** | Doanh thu bán hàng | Tiền bán hàng, chưa tính thuế | Bán 5 tấn phân 100 triệu |
| **515** | Doanh thu tài chính | Tiền kiếm được từ tài chính | Chiết khấu trả sớm, lãi tỷ giá |
| **711** | Thu nhập khác | Thu ngoài việc chính | Bán thanh lý máy cũ, tiền phạt NCC |

### 3.5. Nhóm 6, 8, 9. Chi phí và kết quả

| TK | Tên | Hiểu đơn giản | Ví dụ |
|---|---|---|---|
| **621** | Chi phí nguyên vật liệu trực tiếp | Vật tư đem ra sản xuất một sản phẩm cụ thể | Xuất dung dịch, chai cho lệnh đóng hàng |
| **622** | Chi phí nhân công trực tiếp | Lương công nhân trực tiếp làm sản phẩm | Lương tổ đóng gói |
| **627** | Chi phí sản xuất chung | Chi phí của xưởng, không gắn riêng sản phẩm nào | Khấu hao máy, điện xưởng, sửa máy |
| **632** | Giá vốn hàng bán | Giá trị hàng đã bán, tính theo giá vốn | Bán 5 tấn, giá vốn 75 triệu |
| **635** | Chi phí tài chính | Mất tiền do tài chính | Lãi vay, lỗ tỷ giá, lãi trả chậm |
| **641** | Chi phí bán hàng | Chi phí để bán hàng | Lương kinh doanh, thuê kho chứa hàng chờ bán |
| **642** | Chi phí quản lý doanh nghiệp | Chi phí văn phòng, điều hành | Văn phòng phẩm, lương phòng Thu mua |
| **811** | Chi phí khác | Mất ngoài việc chính | Giá trị còn lại của máy thanh lý, phí hủy đơn |
| **911** | Xác định kết quả kinh doanh | Cuối kỳ gom doanh thu và chi phí, ra lãi hoặc lỗ | |

---

# PHẦN II. TỔ CHỨC

## 4. Ai làm gì

| Vai trò | Làm gì |
|---|---|
| Người cần hàng | Lập yêu cầu mua |
| Trưởng phòng của người cần hàng | Duyệt yêu cầu mua |
| Trưởng Thu mua | Chia việc cho người mua, duyệt phương án chọn NCC |
| Người mua | Hỏi giá, so sánh, lập đơn mua, theo dõi giao hàng, xử lý với NCC |
| Cấp duyệt đơn mua | Duyệt theo hạn mức giá trị |
| Thủ kho, QC | Nhận và kiểm hàng (xem tài liệu Kho 10) |
| Kế toán phải trả | Nhập hóa đơn, đối chiếu, ghi công nợ |
| Kế toán thanh toán, thủ quỹ | Lập lệnh chi, chi tiền |

---

## 5. Chứng từ và trạng thái

| Chứng từ | Trạng thái |
|---|---|
| **Yêu cầu mua (PR)** | Nháp → Chờ duyệt → Đã duyệt → Đã chuyển báo giá hoặc đơn mua → Đóng · Từ chối · Hủy |
| **Yêu cầu báo giá (RFQ)** | Nháp → Đã gửi → Đã nhận báo giá → Đã chọn → Đóng |
| **Đơn mua (PO)** | Nháp → Chờ duyệt → Đã duyệt → Đã gửi NCC → Nhận một phần → Nhận đủ → Đã có hóa đơn → Đóng · Hủy · Đóng sớm |
| **Hóa đơn NCC** | Nháp → Đang đối chiếu → Treo (lệch) hoặc Đã ghi sổ → Trả một phần → Đã trả |
| **Đề nghị thanh toán** | Nháp → Chờ duyệt → Đã duyệt → Đã chi |

Chứng từ sau luôn **trỏ về** chứng từ trước, để từ một khoản chi lần ngược được về yêu cầu mua ban đầu.

---

## 6. Loại mặt hàng

### 6.1. Vì sao mỗi dòng phải có loại mặt hàng
Trên **mỗi dòng** của yêu cầu mua và đơn mua phải chọn **loại mặt hàng**. Chỉ một ô này quyết định gần hết phần sau:
1. **Ai duyệt** và duyệt mấy cấp (mục 7).
2. **Có phải hỏi giá không.**
3. **Nhận hàng kiểu gì:** qua kho, nghiệm thu, hay chỉ xác nhận đã làm xong.
4. **Ghi vào tài khoản nào.** Người dùng không chọn tài khoản. Kế toán cài sẵn một bảng *loại mặt hàng → tài khoản*, hệ thống tự ghi.
5. **Lấy tiền từ ngân sách nào:** sản xuất, đầu tư, hay chi phí của phòng.

Một yêu cầu có nhiều loại (vừa mua máy vừa mua dầu máy) thì mỗi dòng mang loại riêng, hệ thống **tách thành nhiều đơn mua** theo loại.

### 6.2. Các loại mặt hàng

| Loại | Ví dụ | Ô bắt buộc trên phiếu | Nhận hàng |
|---|---|---|---|
| **Vật tư sản xuất** | Dung dịch, chai, nhãn, K₂SO₄ | Mã hàng, số lượng, ngày cần, kho nhận, lệnh sản xuất | Thủ kho nhập kho, QC kiểm, ghi lô và hạn dùng |
| **Hàng hóa** | Phân bón mua về bán nguyên bao | Mã hàng, kho nhận hoặc địa chỉ khách, đơn bán liên quan | Nhập kho, hoặc giao thẳng cho khách |
| **Công cụ dụng cụ** | Pallet, khuôn, dụng cụ | Mã hàng, bộ phận dùng | Nhập kho, khi đem ra dùng thì xuất |
| **Tài sản cố định** | Máy trộn, xe, máy tính đắt | Nhóm tài sản, bộ phận dùng, lý do đầu tư, công suất, ngân sách | Biên bản bàn giao, lắp đặt, biên bản nghiệm thu |
| **Dịch vụ** | Sửa máy, thuê xe, tư vấn, văn phòng phẩm | Mô tả công việc, bộ phận chịu chi phí, thời gian | Bộ phận yêu cầu xác nhận đã làm xong |
| **Trả trước nhiều tháng** | Bảo hiểm cả năm, thuê kho cả năm | Thời gian áp dụng, bộ phận chịu chi phí | Xác nhận hợp đồng có hiệu lực |
| **Dịch vụ gia công** | Phí gia công tại nhà máy ngoài | Thành phẩm nhận về, định mức vật tư cấp | Nhận thành phẩm, quyết toán vật tư |

**Tài sản hay công cụ:** từ 30 triệu đồng và dùng trên một năm là tài sản cố định. Dưới mức đó là công cụ dụng cụ (Thông tư 45/2013, kế toán xác nhận). Hệ thống gợi ý theo ngưỡng giá trị, kế toán là người chốt.

### 6.3. Loại mặt hàng → tài khoản

| Loại | Khi nhận hàng ghi vào | Khi dùng hoặc bán | Thành chi phí lúc nào |
|---|---|---|---|
| Vật tư sản xuất | **152** | 621 khi xuất cho sản xuất → 154 → 155 → **632** khi bán | Khi sản phẩm được bán |
| Hàng hóa | **156** | **632** khi bán | Khi bán |
| Công cụ dụng cụ | **153** | **242** khi đem ra dùng, chia dần vào 627 / 641 / 642 | Chia đều 1 đến 3 năm |
| Tài sản cố định | **241** khi lắp đặt lâu → **211** khi nghiệm thu | Khấu hao hằng tháng vào 627 / 641 / 642, đối ứng 214 | Chia đều nhiều năm |
| Dịch vụ cho xưởng | Thẳng **627** | | Ngay khi có hóa đơn |
| Dịch vụ, đồ dùng văn phòng | Thẳng **642** | | Ngay |
| Dịch vụ cho bán hàng | Thẳng **641** | | Ngay |
| Trả trước nhiều tháng | **242** | Chia mỗi tháng vào 627 / 641 / 642 | Theo tháng |
| Dịch vụ gia công | **154** | **155** khi nhận thành phẩm | Khi thành phẩm được bán |

Thuế GTGT trên hóa đơn mua luôn tách ra **1331** nếu được khấu trừ, với mọi loại.

### 6.4. So sánh ba loại chính

| Bước | Vật tư sản xuất | Tài sản cố định | Dịch vụ, chi phí |
|---|---|---|---|
| Nhu cầu từ đâu | Thường tự động: MRP, tồn dưới mức đặt hàng lại | Thủ công, theo kế hoạch đầu tư | Thủ công, phòng cần thì lập |
| Duyệt | Nhẹ | Nặng, lên tới CEO, kiểm ngân sách đầu tư | Theo hạn mức chi phí của phòng |
| Hỏi giá | Thường có hợp đồng khung, gọi hàng luôn | Bắt buộc so sánh hoặc đấu thầu | Khi vượt một mức tiền |
| Nhận hàng | Kho và QC | Bàn giao, nghiệm thu | Xác nhận đã làm xong |
| Đối chiếu hóa đơn | 3 chiều, có khi 4 chiều | 3 chiều cộng biên bản nghiệm thu | 2 chiều |
| Sau khi mua quản lý gì | Tồn kho, lô, hạn dùng | Thẻ tài sản, khấu hao, sửa chữa, thanh lý | Không gì thêm |

### 6.5. Tình huống phân loại hay gặp

| Tình huống | Cách xử lý |
|---|---|
| Không chắc là tài sản hay công cụ (máy tính 25 triệu) | Hệ thống gợi ý theo ngưỡng, kế toán chốt |
| Vật tư sản xuất mua gấp ngoài MRP | Lập thủ công, đánh dấu *gấp*. Vẫn là vật tư, vẫn qua kho và QC |
| Mua phụ tùng thay cho máy | Thay thường: vật tư hoặc chi phí sửa chữa 627. Tăng công suất hoặc kéo dài đời máy: nâng cấp, cộng vào nguyên giá |
| Thuê ngoài lắp đặt máy mới | Dịch vụ gắn vào tài sản đang lắp, cộng vào nguyên giá qua 241 |
| Mua vật tư để công ty tự xây, tự chế tạo tài sản | Loại vật tư nhưng gắn mã công trình, xuất thẳng vào 241 |

---

## 7. Luồng duyệt theo loại mặt hàng

### 7.1. Nguyên tắc chung
- Duyệt **hai lần**: duyệt **yêu cầu mua** (có cần mua không) và duyệt **đơn mua** (mua của ai, giá bao nhiêu).
- Đơn mua duyệt **theo hạn mức giá trị**, tính trên **tổng tiền cả đơn** sau quy đổi tiền, không tính từng dòng, để không ai chia nhỏ dòng mà lách.
- Mỗi loại mặt hàng lấy tiền từ **một ngân sách**. Hệ thống kiểm còn ngân sách trước khi cho duyệt.
- Mức tiền dưới đây là **ví dụ**. Mỗi công ty tự đặt và khai trong cấu hình.

**Hạn mức duyệt đơn mua (ví dụ):**

| Giá trị đơn | Ai duyệt |
|---|---|
| Dưới 50 triệu | Trưởng Thu mua |
| 50 đến 500 triệu | Thêm Giám đốc tài chính hoặc Kế toán trưởng |
| Trên 500 triệu | Thêm CEO |

### 7.2. Vật tư sản xuất
```
Yêu cầu mua ──► Duyệt yêu cầu ──► Chọn NCC ──► Duyệt đơn mua ──► Gửi NCC
(MRP hoặc       (tự duyệt nếu     (hợp đồng     (theo hạn mức)
 kế hoạch SX)    đi theo kế hoạch  khung: bỏ
                 đã duyệt; thủ     qua bước này)
                 công: Trưởng SX)
```
- **Ngân sách:** ngân sách sản xuất.
- **Có hợp đồng khung:** đơn con giá đã khóa, Trưởng Thu mua duyệt nhanh hoặc tự duyệt dưới một mức.
- **Mua gấp ngoài kế hoạch:** thêm Trưởng phòng Sản xuất duyệt lý do.

### 7.3. Hàng hóa mua để bán
```
Đơn bán của khách ──► Yêu cầu mua ──► Duyệt yêu cầu ──► Chọn NCC ──► Duyệt đơn mua
                       (tự sinh hoặc   (Quản lý thương    (Trưởng      (theo hạn mức)
                        Kinh doanh lập) hiệu: kiểm biên    Thu mua)
                                        lợi nhuận)
```
- **Ngân sách:** theo thương hiệu hoặc theo đơn bán.
- Giao thẳng cho khách thì đơn mua tự sinh từ đơn bán đã duyệt.

### 7.4. Công cụ dụng cụ
```
Yêu cầu mua ──► Trưởng phòng dùng ──► Chọn NCC ──► Duyệt đơn mua theo hạn mức
```
- **Ngân sách:** chi phí của phòng dùng.
- Duyệt nhẹ như vật tư. Kế toán kiểm lại phân loại khi giá gần ngưỡng 30 triệu.

### 7.5. Tài sản cố định
```
Đề xuất đầu tư ──► Trưởng bộ phận ──► Kế toán ──► Giám đốc tài chính ──► CEO
                                     (phân loại,
                                      ngân sách đầu tư)
   ──► Hỏi giá bắt buộc (ít nhất 3 báo giá hoặc đấu thầu) ──► Duyệt chọn NCC (CEO)
   ──► Duyệt đơn mua (CEO) ──► Nhận, lắp đặt ──► Hội đồng nghiệm thu
                                                 (bộ phận dùng, kỹ thuật, kế toán)
```
- **Ngân sách:** ngân sách đầu tư của năm.
- **Luôn lên CEO** dù giá trị nhỏ, vì là quyết định đầu tư.
- **Ngày nghiệm thu** là ngày bắt đầu khấu hao.

### 7.6. Dịch vụ
```
Yêu cầu mua ──► Trưởng phòng chịu chi phí ──► Hỏi giá (khi vượt mức, ví dụ 5 triệu)
   ──► Duyệt đơn mua theo hạn mức ──► Làm xong ──► Bộ phận yêu cầu xác nhận
```
- **Ngân sách:** chi phí của phòng.
- Dưới mức nhỏ (ví dụ 5 triệu) được mua thẳng, không cần hỏi giá.

### 7.7. Trả trước nhiều tháng và hợp đồng dài hạn
- Như dịch vụ, **thêm Kế toán trưởng** duyệt vì cam kết tiền nhiều kỳ.
- Hợp đồng khung: duyệt **một lần theo tổng giá trị hợp đồng**, các đơn con duyệt nhẹ.

### 7.8. Dịch vụ gia công
- Như vật tư sản xuất, **thêm Trưởng phòng Sản xuất duyệt định mức vật tư cấp và tỷ lệ hao hụt** trên đơn gia công.

### 7.9. Bảng tổng hợp

| Loại | Duyệt yêu cầu | Hỏi giá | Duyệt đơn mua | Nhận, nghiệm thu | Ngân sách |
|---|---|---|---|---|---|
| Vật tư sản xuất | Tự duyệt theo kế hoạch, hoặc Trưởng Sản xuất | Bỏ qua nếu có hợp đồng khung | Theo hạn mức | Thủ kho, QC | Sản xuất |
| Hàng hóa | Quản lý thương hiệu | Trưởng Thu mua | Theo hạn mức | Thủ kho, QC | Thương hiệu |
| Công cụ dụng cụ | Trưởng phòng dùng | Khi vượt mức | Theo hạn mức | Thủ kho | Chi phí phòng |
| Tài sản cố định | Trưởng bộ phận → Kế toán → Giám đốc tài chính → CEO | Bắt buộc, ít nhất 3 báo giá | CEO | Hội đồng nghiệm thu | Đầu tư |
| Dịch vụ | Trưởng phòng chịu chi phí | Khi vượt mức | Theo hạn mức | Bộ phận yêu cầu | Chi phí phòng |
| Trả trước, hợp đồng dài hạn | Trưởng phòng, Kế toán trưởng | Có | Theo hạn mức, cộng Kế toán trưởng | Hợp đồng có hiệu lực | Chi phí phòng |
| Dịch vụ gia công | Như vật tư, cộng duyệt định mức | Theo hợp đồng gia công | Theo hạn mức | Thủ kho, QC thành phẩm | Sản xuất |

---

# PHẦN III. LUỒNG MUA HÀNG CHUẨN

## 8. Nhu cầu mua phát sinh từ đâu

| Nguồn | Ví dụ | Loại hàng, tài khoản |
|---|---|---|
| Sản xuất (MRP) | Kế hoạch cần 30,6 tấn, tồn 8, đang về 10, tồn an toàn 5 → mua 17,6 tấn | Nguyên vật liệu, 152 |
| Tồn dưới mức đặt hàng lại | Dùng 2 tấn mỗi ngày × NCC giao 15 ngày + tồn an toàn 10 = đặt khi tồn dưới 40 tấn | 152 hoặc 156 |
| Đơn bán của khách | Mua về bán lại | Hàng hóa, 156 |
| Phòng ban dùng | Văn phòng phẩm, sửa máy, thuê xe | Chi phí 627, 641, 642 |
| Đầu tư | Máy trộn, xe nâng | Tài sản cố định, 211 |
| Hợp đồng khung | Mua lặp lại theo giá đã ký | Theo loại hàng |
| Sự cố, mua gấp | Máy hỏng, thiếu bao bì | Đi đường duyệt nhanh, lập phiếu bổ sung sau |

Loại hàng phải xác định **ngay từ yêu cầu mua**, vì nó quyết định luồng duyệt và tài khoản (mục 6, 7).

---

## 9. Bảy chặng từ yêu cầu mua tới thanh toán

### Chặng 1. Yêu cầu mua
- **Người dùng:** chọn mã hàng, số lượng, ngày cần, kho nhận, đối tượng chi phí (phòng ban, dự án, lệnh sản xuất). Gửi duyệt.
- **Hệ thống:** tự chọn luồng duyệt theo phòng ban và giá trị. Nếu có ngân sách thì kiểm còn tiền và tạm giữ.
- Đề xuất do MRP sinh ra ở dạng *Đề xuất*. Người mua xem lại, gộp, rồi mới chuyển thành yêu cầu mua.

### Chặng 2. Hỏi giá và chọn NCC
- **Người dùng:** từ yêu cầu mua, tạo yêu cầu báo giá gửi 2–3 NCC. Nhận về thì nhập giá, thời gian giao, điều kiện thanh toán, cước vận chuyển.
- **Hệ thống:** dựng bảng so sánh gồm tổng tiền thật (cộng cước), có kịp ngày cần không, điểm NCC từ các lần trước (giao trễ, tỷ lệ lỗi).
- **Chọn:** đánh dấu phương án, ghi lý do, trình duyệt. Giá chốt được lưu vào **bảng giá NCC** để lần sau tự điền.

### Chặng 3. Đơn mua
- **Người dùng:** tạo đơn mua từ phương án đã chọn. Bổ sung ngày giao, kho nhận, công ty đứng tên mua, dung sai nhận (ví dụ ±2%), mức đối chiếu (2, 3 hay 4 chiều).
- **Duyệt theo hạn mức** (ví dụ, chi tiết theo loại mặt hàng ở mục 7):

| Giá trị đơn | Duyệt |
|---|---|
| Dưới 50 triệu | Trưởng phòng |
| 50 đến 500 triệu | Thêm Giám đốc tài chính |
| Trên 500 triệu | Thêm CEO |

- **Duyệt xong, hệ thống tự làm:**
  1. Khóa giá, số lượng, NCC, điều kiện thanh toán.
  2. Sinh **lệnh chờ nhận hàng** bên Kho. Màn của thủ kho không thấy giá.
  3. Sinh **lịch thanh toán dự kiến** để dự báo dòng tiền.
  4. Gửi đơn cho NCC. NCC xác nhận.
- **Sửa đơn đã duyệt:** tạo phiên bản mới, giữ phiên bản cũ, ghi lý do. Giá trị tăng thì duyệt lại.

### Chặng 4. Theo dõi giao hàng
- Ghi ngày hẹn giao. Hệ thống nhắc đơn sắp đến hạn và đơn đã trễ.
- Nhận hàng, kiểm hàng, trả hàng lỗi: xem tài liệu Kho. Mua hàng nhận lại kết quả để xử lý với NCC.

### Chặng 5. Hóa đơn NCC
- **Hóa đơn sinh ra khi nào:** NCC lập vào **ngày giao hàng** (lúc chuyển quyền sở hữu). Với dịch vụ thì lập khi làm xong. Hóa đơn điện tử gửi về email.
- **Kế toán:** tạo hóa đơn NCC, chọn đơn mua. Hệ thống kéo các dòng đã nhận mà chưa có hóa đơn.
- **Kiểm khi nhận hóa đơn:**
  - Tên, mã số thuế bên mua đúng công ty đứng tên đơn. Thương hiệu khác pháp nhân thì phải xuất cho đúng pháp nhân.
  - Hàng, số lượng, đơn giá khớp đơn mua và số thực nhận.
  - Đúng thuế suất, có mã của cơ quan thuế.
- **Đối chiếu:**

| Mức | So | Dùng cho |
|---|---|---|
| 2 chiều | Đơn mua, hóa đơn | Dịch vụ |
| 3 chiều | Thêm phiếu nhập kho | Hàng hóa |
| 4 chiều | Thêm số đã qua kiểm | Nguyên liệu bắt buộc kiểm |

- Trong dung sai thì ghi sổ, **công nợ tự sinh**, hạn trả = ngày hóa đơn + số ngày công nợ. Vượt dung sai thì **treo** hóa đơn chờ xử lý.

### Chặng 6. Thanh toán
- **Kế toán:** chạy **đề xuất thanh toán**, lọc khoản nợ đến hạn, bỏ khoản đang tranh chấp. Gửi duyệt.
- **Duyệt xong:** xuất lệnh chi gửi ngân hàng. Công nợ giảm, đơn mua đóng.
- Hóa đơn **từ 5 triệu đồng trở lên** phải chuyển khoản mới được khấu trừ thuế GTGT (Luật Thuế GTGT 2024, từ 01/07/2025).

### Chặng 7. Cuối tháng
1. Soát **hàng về chưa có hóa đơn** và **hóa đơn về chưa có hàng**.
2. Đóng sớm các đơn treo lâu ở *Nhận một phần*.
3. Đối chiếu công nợ với từng NCC, ký biên bản.
4. Tính lại chênh lệch tỷ giá cho nợ ngoại tệ.

---

# PHẦN IV. TIỀN: HÓA ĐƠN, CHI PHÍ, VÍ DỤ

## 10. Hóa đơn và thời điểm ghi nợ

| Tình huống | Cách ghi |
|---|---|
| Hàng và hóa đơn về cùng lúc | Ghi nhập kho và nợ NCC theo hóa đơn |
| Hàng về trước, hóa đơn về sau | Trong tháng thì chờ. Hết tháng chưa có thì ghi theo **giá tạm tính**, có hóa đơn thì điều chỉnh |
| Hóa đơn về trước, hàng chưa về | Ghi **151 hàng mua đang đi đường**. Hàng về thì chuyển sang kho |
| Hóa đơn sai | Không tự sửa. Yêu cầu NCC lập hóa đơn điều chỉnh hoặc thay thế |
| NCC giảm giá sau khi bán | Hóa đơn điều chỉnh giảm, công nợ và giá vốn cùng giảm |

| Loại giấy tờ đầu vào | Khấu trừ thuế GTGT? |
|---|---|
| Hóa đơn GTGT | Có |
| Hóa đơn bán hàng (NCC nộp thuế trực tiếp, hộ kinh doanh) | Không, toàn bộ vào giá vốn hoặc chi phí |
| Tờ khai hải quan và chứng từ nộp thuế (nhập khẩu) | Có, phần thuế GTGT hàng nhập khẩu |

---

## 11. Các khoản chi phí khi mua

Nguyên tắc: **giá vốn gồm mọi chi phí để đưa hàng về tới kho, ở trạng thái dùng được.**

| Khoản | Vào giá vốn? | Tài khoản |
|---|---|---|
| Giá mua chưa thuế | Có | 152, 153, 156, 211 |
| Chiết khấu thương mại, giảm giá trên hóa đơn | Có, làm giảm | Giảm 152, 156 |
| Cước, bốc xếp, bảo hiểm hàng đi đường | Có | 152, 156 (hàng hóa có thể tách 1562) |
| Thuế nhập khẩu, tiêu thụ đặc biệt, bảo vệ môi trường | Có | Có 3333, 3332, 33381 |
| Phí hải quan, nâng hạ, lưu bãi ở cảng | Có | 152, 156 |
| Thuế GTGT được khấu trừ | Không | 1331 (nhập khẩu: Có 33312) |
| Thuế GTGT không được khấu trừ | Có | Cộng vào giá vốn hoặc chi phí |
| Hao hụt trên đường trong mức cho phép | Có | Không ghi riêng |
| Thiếu ngoài mức cho phép | Không | 1381 chờ xử lý |
| Chiết khấu trả sớm | Không | Có 515 |
| Lãi trả chậm | Không | Nợ 635 |
| Chênh lệch tỷ giá khi trả | Không | 515 (lãi), 635 (lỗ) |
| Tiền phạt NCC giao trễ | Không | Có 711 |
| Phí lưu kho sau khi đã nhập kho | Không | 641 hoặc 642 |
| Chi phí của phòng Thu mua | Không | 642 |

**Chi phí mua hàng chung cho nhiều mặt hàng** (ví dụ cước một container): lập phiếu chi phí mua hàng, chia cho từng mã theo một trong năm cách: chia đều, theo số lượng, theo giá trị, theo khối lượng, theo thể tích. Chi phí về muộn khi hàng đã xuất bớt: phần của hàng còn trong kho cộng vào giá tồn, phần đã xuất ghi vào giá vốn của kỳ đó.

---

## 12. Ví dụ có số

**Mua trong nước:** 17 tấn × 15.000.000 đ, VAT 10%.

| Bước | Bút toán | Số tiền |
|---|---|---|
| Ứng trước 30% | Nợ 331 / Có 112 | 84.150.000 |
| Hàng về 16,8 tấn, hóa đơn 17 tấn | Nợ 152: 252.000.000 · Nợ 1381: 3.000.000 · Nợ 1331: 25.500.000 / Có 331: 280.500.000 | |
| Cước xe | Nợ 152: 3.000.000 · Nợ 1331: 300.000 / Có 331 nhà xe: 3.300.000 | |
| NCC giao bù 0,2 tấn | Nợ 152 / Có 1381 | 3.000.000 |
| Trả 0,5 tấn lỗi | Nợ 331: 8.250.000 / Có 152: 7.500.000 · Có 1331: 750.000 | |
| Trả nốt sớm, chiết khấu 1% | Nợ 331: 188.100.000 / Có 515: 1.881.000 · Có 112: 186.219.000 | |

Kết quả: kho có 16,5 tấn, giá trị 250,5 triệu, khoảng **15.181.800 đ/tấn**.

**Nhập khẩu:** 12.000 USD, tỷ giá 25.000.

| Bước | Bút toán | Số tiền |
|---|---|---|
| Hàng về | Nợ 152 / Có 331 | 300.000.000 |
| Thuế nhập khẩu 3% | Nợ 152 / Có 3333 | 9.000.000 |
| Thuế GTGT nhập khẩu 10% × 309 triệu | Nợ 1331 / Có 33312 | 30.900.000 |
| Phí hải quan, nâng hạ, kéo về | Nợ 152: 6.000.000 · Nợ 1331: 600.000 / Có 331 | |
| Trả NCC khi tỷ giá 25.200 | Nợ 331: 300.000.000 · Nợ 635: 2.400.000 / Có 1122: 302.400.000 | |

Kết quả: giá vốn 315 triệu, **15.750.000 đ/tấn**. Lỗ tỷ giá là chi phí tài chính, không vào giá vốn.

---

# PHẦN V. CÁC TRƯỜNG HỢP THƯỜNG GẶP

## 13. Sự cố và hình thức mua đặc biệt

**Cách đọc:** mỗi trường hợp ghi *khi nào gặp*, rồi một bảng ba cột theo từng bước:
- **Người làm (ngoài đời):** ai làm gì, ký giấy gì, liên hệ ai.
- **Trên phần mềm:** người dùng bấm gì.
- **Hệ thống tự làm, bút toán:** phần mềm tự sinh gì, tiền đi vào tài khoản nào.

Nhóm A, B, C là **sự cố** trong luồng mua thường. Nhóm D là **hình thức mua đặc biệt**. Nhóm E là **thanh toán**.

---

### Nhóm A. Sự cố khi nhận hàng

#### A1. NCC giao thiếu hoặc giao nhiều đợt
*Khi nào:* đặt 1.000, chuyến đầu giao 600.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho đếm, ký biên bản giao nhận 600 | Chọn đơn mua, nhập 600, xác nhận | Phiếu nhập 600. Đơn chuyển *Nhận một phần*, mở đơn dở dang 400. Nợ 152 / Có TK tạm chờ hóa đơn |
| Người mua hỏi NCC lịch giao phần còn lại | Ghi ngày hẹn mới cho phần 400 | Nhắc khi tới hạn |
| NCC giao nốt 400 | Thủ kho nhập 400 | Phiếu nhập thứ hai. Đơn chuyển *Nhận đủ* |
| Nếu NCC báo không giao nữa | Người mua bấm *Đóng sớm*, ghi lý do | Hủy phần 400, giữ phần đã nhận, trả lại ngân sách tạm giữ |

#### A2. NCC giao thừa
*Khi nào:* đặt 1.000, giao 1.030.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho đếm được 1.030 | Nhập 1.030 | Trong dung sai (ví dụ ±2%) thì cho nhận 1.020, vượt thì chặn |
| Người mua quyết nhận phần dư hay trả | Nhận: sửa đơn tăng số lượng, trình duyệt lại. Trả: ghi biên bản trả lại phần dư cho tài xế | Nhận: phiếu nhập đủ 1.030. Trả: chỉ nhập 1.000 |

#### A3. Giao sai mã hàng hoặc sai quy cách
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho phát hiện, không nhận, lập biên bản, trả xe | Ghi *từ chối nhận* trên đơn, đính kèm biên bản và ảnh | Không sinh phiếu nhập, không bút toán. Đơn giữ trạng thái chờ giao |
| Người mua báo NCC giao lại đúng hàng | Cập nhật ngày hẹn | Ghi điểm trừ NCC (giao sai) vào đánh giá NCC |

#### A4. Hàng lỗi khi kiểm chất lượng
*Khi nào:* nhận 2.000 chai, QC thấy 40 chai móp.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| QC kiểm, lập biên bản hàng lỗi có ảnh | QC nhập kết quả: 1.960 đạt, 40 lỗi | 1.960 sang tồn dùng được, 40 sang kho cách ly |
| Người mua báo NCC, thống nhất cách xử lý | Chọn một trong bốn cách bên dưới | |
| **Trả NCC** | Từ phiếu nhập gốc bấm *Trả hàng NCC* | Phiếu xuất trả, phiếu ghi nợ NCC. Nợ 331 / Có 152 (và 1331 nếu đã có hóa đơn) |
| **NCC đổi hàng** | Trả rồi mở lại lệnh chờ nhận 40 chai | Đơn quay về *Nhận một phần* |
| **Nhận và giảm giá** | Ghi mức giảm, chờ hóa đơn điều chỉnh | Giá vốn và công nợ cùng giảm khi có hóa đơn điều chỉnh |
| **Tự hủy, chịu chi phí** | Lập phiếu xuất hủy, kèm biên bản | Nợ 632 hoặc 811 / Có 152 |

#### A5. Đã nhập kho rồi mới phát hiện nhập sai số
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho báo trưởng kho | Mở phiếu nhập sai, bấm *Đảo phiếu*, ghi lý do | Sinh phiếu đảo ngược dấu, trỏ về phiếu cũ. Không sửa, không xóa phiếu cũ |
| | Lập phiếu nhập mới với số đúng | Kỳ đã khóa thì không đảo được, phải điều chỉnh ở kỳ hiện tại |

---

### Nhóm B. Sự cố với đơn mua

#### B1. Phải sửa đơn đã duyệt
*Khi nào:* NCC báo tăng giá, cần thêm số lượng, đổi ngày giao.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Người mua thống nhất với NCC, xin văn bản báo giá mới | Bấm *Sửa đổi đơn*, nhập thay đổi, ghi lý do | Tạo phiên bản mới, giữ phiên bản cũ |
| Cấp duyệt xem lại | Duyệt phiên bản mới | Giá trị tăng thì bắt buộc duyệt lại. Chỉ đổi ngày giao thì có thể không cần |
| Gửi NCC bản sửa đổi | In hoặc gửi phiên bản mới | Hóa đơn về sau đối chiếu với phiên bản mới nhất |

#### B2. Hủy đơn
| Tình huống | Trên phần mềm | Hệ thống |
|---|---|---|
| Chưa nhận gì | *Hủy đơn*, ghi lý do | Trả lại ngân sách tạm giữ, báo NCC |
| Đã nhận một phần | Không hủy được, chỉ *Đóng sớm* | Giữ phần đã nhận |
| Đã trả trước | Hủy, xử lý tiền đã ứng | Xem mục 14.4 |

#### B3. NCC giao trễ
| Người làm | Trên phần mềm | Hệ thống |
|---|---|---|
| Người mua đôn đốc NCC | Theo dõi danh sách *đơn trễ hạn* | Tự nhắc khi quá ngày hẹn |
| Báo bộ phận cần hàng, tìm phương án khác nếu gấp | Ghi ngày hẹn mới và lý do trễ | Ghi điểm trừ NCC |
| Phạt theo hợp đồng nếu có | Ghi khoản phạt | Có 711 khi NCC chấp nhận trả hoặc trừ vào tiền hàng |

---

### Nhóm C. Sự cố với hóa đơn

#### C1. Hóa đơn lệch giá hoặc lệch số lượng
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Kế toán nhập hóa đơn | Chọn đơn mua, nhập số liệu theo hóa đơn | Đối chiếu ba chiều. Lệch quá dung sai thì **treo** hóa đơn |
| Người mua làm rõ với NCC | Xem phần lệch trên màn hóa đơn bị treo | |
| NCC sai thì lập hóa đơn điều chỉnh | Nhập hóa đơn điều chỉnh | Hóa đơn khớp, được ghi sổ |
| Chấp nhận phần lệch nhỏ | Kế toán trưởng bấm *Duyệt chênh lệch* | Phần chênh vào giá vốn (còn tồn) hoặc 632 (đã xuất) |

#### C2. Hàng và hóa đơn về lệch nhau
Xem mục 10. Tóm tắt: hàng về trước thì cuối tháng ghi giá tạm tính. Hóa đơn về trước thì ghi 151 hàng đi đường.

#### C3. Hóa đơn ghi sai công ty mua hoặc sai thông tin
| Người làm | Trên phần mềm | Hệ thống |
|---|---|---|
| Kế toán phát hiện | Nhập mã số thuế trên hóa đơn | So với công ty đứng tên đơn mua. Sai thì chặn |
| Báo NCC lập hóa đơn thay thế | Từ chối hóa đơn, ghi lý do | Hóa đơn bị từ chối không ghi sổ |

#### C4. NCC giảm giá sau khi đã bán
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| NCC gửi hóa đơn điều chỉnh giảm | Nhập hóa đơn điều chỉnh, trỏ về hóa đơn gốc | Nợ 331 / Có 152 (hàng còn) hoặc 632 (hàng đã xuất), Có 1331 |

---

### Nhóm D. Hình thức mua đặc biệt

#### D1. Mua dịch vụ
*Ví dụ:* sửa máy, thuê xe, tư vấn.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Bộ phận cần dịch vụ lập yêu cầu | Yêu cầu mua loại dịch vụ, chọn bộ phận chịu chi phí | |
| Người mua chọn đơn vị, lập đơn | Đơn mua loại dịch vụ | Không sinh lệnh chờ nhận ở kho |
| Bộ phận yêu cầu nghiệm thu khi làm xong | Bấm *Xác nhận đã làm xong* | Thay cho phiếu nhập kho |
| Kế toán nhập hóa đơn | Đối chiếu hai chiều | Nợ 627, 641 hoặc 642, Nợ 1331 / Có 331 |

#### D2. Mua lặt vặt bằng tạm ứng
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Nhân viên xin tạm ứng | Đề nghị tạm ứng, duyệt | Nợ 141 / Có 111 |
| Mua hàng, lấy hóa đơn | Đề nghị quyết toán tạm ứng, đính kèm hóa đơn | Nợ 642 hoặc 152, Nợ 1331 / Có 141 |
| Thừa thì nộp lại, thiếu thì được chi thêm | | Nợ 111 / Có 141, hoặc Nợ 141 / Có 111 |

#### D3. Hợp đồng khung
*Ví dụ:* 200.000 chai giá 2.450 đ trong năm.

| Người làm | Trên phần mềm | Hệ thống |
|---|---|---|
| Người mua đàm phán, ký hợp đồng khung một lần | Tạo hợp đồng khung: hàng, giá, tổng lượng, thời hạn. Duyệt theo tổng giá trị | Đưa giá vào bảng giá NCC |
| Mỗi lần cần hàng | Bấm *Gọi hàng* từ hợp đồng | Sinh đơn mua con, giá tự điền, không cho sửa, duyệt nhẹ |
| Nhận hàng, hóa đơn, thanh toán | Như luồng chuẩn, theo từng đơn con | |
| Theo dõi | Xem phần trăm đã dùng | Cảnh báo khi dùng 90% hoặc còn 30 ngày. Chặn khi vượt lượng hoặc hết hạn |

#### D4. Hàng ký gửi
*Ví dụ:* NCC gửi 10.000 chai ở kho mình, giá 2.450 đ, chốt hằng tháng.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Ký hợp đồng ký gửi: giá, mức tồn NCC phải giữ, chu kỳ chốt, ai chịu khi thiếu | Khai hợp đồng ký gửi và bảng giá | |
| NCC đưa hàng tới, thủ kho đếm | Phiếu nhận hàng ký gửi 10.000 | Tồn ký gửi tăng. **Không bút toán, không công nợ** |
| Xuất dùng 3.200 chai cho sản xuất | Xuất như thường, hệ thống lấy tồn ký gửi trước | Tự chuyển quyền sở hữu: Nợ 152 / Có 331 chờ hóa đơn 7.840.000, rồi Nợ 621 / Có 152 |
| Cuối tháng gửi NCC bảng kê số đã dùng | Bấm *Chốt hàng ký gửi đã dùng* | In bảng kê 3.200 × 2.450 + VAT = 8.624.000 |
| NCC xuất hóa đơn theo bảng kê | Nhập hóa đơn, đối chiếu với bảng kê | Nợ 331 chờ hóa đơn, Nợ 1331 / Có 331 NCC. Thanh toán như thường |
| Kiểm kê thấy thiếu 50 chai | *Ghi nhận thiếu hàng ký gửi* | Coi như đã dùng 50, cộng vào bảng kê. Phần thiếu ghi 1381 để truy trách nhiệm |
| Chấm dứt hợp đồng | Phiếu trả hàng ký gửi | Tồn ký gửi về 0, không phát sinh tiền |

Mình **trả tiền hàng đã dùng**, không trả phí lưu kho. Hàng ký gửi không tính vào tài sản công ty nhưng MRP vẫn coi là hàng dùng được.

#### D5. Gia công ngoài
*Ví dụ:* thuê nhà gia công đóng 10.000 chai thuốc 450 ml, phí 3.000 đ/chai, hao hụt cho phép 1%. Mình cấp dung dịch, chai, nhãn.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Ký hợp đồng gia công: phí, định mức, hao hụt cho phép, ai chịu khi hỏng vượt | Khai định mức gia công và **kho tại nhà gia công** | |
| Lập đơn gia công | Đơn mua loại gia công: nhận về 10.000 chai thành phẩm | Tự bung vật tư phải cấp, có cộng hao hụt: 4.545 lít, 10.100 chai, 10.100 nhãn |
| Thủ kho xuất vật tư, giao xe chở sang | *Cấp vật tư gia công* | Phiếu chuyển sang kho nhà gia công. Nợ 154 / Có 152: 302.495.000 |
| Theo dõi nhà gia công làm hàng | Theo dõi trên đơn gia công | |
| Nhận thành phẩm, kiểm chất lượng. Nhà gia công báo quyết toán vật tư (dùng 10.060 chai và nhãn, dư 40) | Nhận 10.000 chai, nhập số vật tư thực dùng | Trừ vật tư tại kho nhà gia công. Vượt định mức thì cảnh báo |
| Nhà gia công xuất hóa đơn phí gia công | Nhập hóa đơn, đối chiếu đơn gia công, phiếu nhập thành phẩm, hóa đơn | Nợ 154 30.000.000, Nợ 1331 3.000.000 / Có 331 |
| Thuê xe chở thành phẩm | Nhập hóa đơn vận chuyển gắn đơn gia công | Nợ 154 2.000.000 / Có 331 |
| | Đóng đơn gia công | Tính giá thành 334.377.000, khoảng 33.438 đ/chai. Nợ 155 / Có 154 |
| Lấy 40 chai và 40 nhãn dư về | Phiếu nhận lại vật tư | Nợ 152 / Có 154: 118.000. Tài khoản 154 của đơn về 0 |
| Hằng tháng đối chiếu tồn với nhà gia công | In báo cáo tồn tại kho nhà gia công | Tự kết luận Khớp hoặc Lệch |

| Trường hợp phụ | Cách xử lý |
|---|---|
| Nhà gia công tự cấp một phần vật tư | Phần đó không cấp từ kho. Hóa đơn gồm phí gia công và tiền vật tư, cả hai vào 154 |
| Hỏng vượt định mức do nhà gia công | Đòi bồi thường: trừ vào phí gia công, hoặc Nợ 1388 / Có 154 |
| Thành phẩm lỗi | Cách ly, nhà gia công làm lại không tính phí hoặc trả lại |
| Chuyển vật tư giữa hai nhà gia công | Phiếu chuyển giữa hai kho nhà gia công, không qua kho mình |

#### D6. Giao thẳng cho khách
*Ví dụ:* khách đặt 5 tấn, giá bán 20 triệu/tấn. Mua NCC 15 triệu/tấn. NCC chở thẳng tới khách.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Kinh doanh nhận đơn của khách | Đơn bán, dòng hàng chọn *Giao thẳng từ NCC* | Duyệt xong tự sinh đơn mua, địa chỉ giao là địa chỉ khách |
| Người mua kiểm giá, gửi NCC | Duyệt đơn mua | Hai đơn trỏ qua lại |
| NCC giao tới khách, khách ký biên bản, NCC gửi bản chụp | *Xác nhận đã giao thẳng*, đính kèm biên bản | Nhận và xuất cùng lúc qua kho ảo, tồn thật không đổi. Nợ 632 / Có 331 chờ hóa đơn: 75.000.000 (khách chưa xác nhận đủ thì Nợ 157 trước) |
| NCC xuất hóa đơn cho **mình** | Nhập hóa đơn mua | Nợ 331 chờ hóa đơn, Nợ 1331 / Có 331 NCC: 82.500.000 |
| Mình xuất hóa đơn cho khách | Lập hóa đơn bán từ đơn bán | Nợ 131 / Có 511 100.000.000, Có 3331 10.000.000 |
| Thu khách, trả NCC theo hạn từng bên | Thu tiền, đề nghị thanh toán | Lãi gộp 25 triệu thấy ngay trên đơn bán |

Không qua kho nhưng **vẫn phải có chứng từ nhận và xuất** qua kho ảo, nếu không thì không đối chiếu được với NCC.

#### D7. Mua tài sản cố định
*Ví dụ:* máy trộn 300 triệu, vận chuyển 5 triệu, lắp đặt chạy thử 15 triệu, dùng 8 năm. Từ 30 triệu đồng và dùng trên một năm là tài sản cố định. Dưới mức đó là công cụ dụng cụ (153, phân bổ qua 242).

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Bộ phận lập đề xuất đầu tư, nêu lý do, công suất | Yêu cầu mua loại tài sản | Duyệt cấp cao, kiểm ngân sách đầu tư |
| Người mua hỏi giá hoặc đấu thầu | Như mua thường, so cả bảo hành, phụ tùng | |
| Lập đơn | Đơn mua loại tài sản, chọn nhóm tài sản và bộ phận dùng | |
| Nhận máy, ký biên bản bàn giao. Lắp đặt, chạy thử | Ghi nhận hàng, gom chi phí lắp đặt | Nợ 241 / Có 331 cho máy, vận chuyển, lắp đặt (cộng 1331) |
| Ký biên bản nghiệm thu đưa vào dùng | Bấm *Nghiệm thu*, chọn ngày bắt đầu dùng | Nợ 211 / Có 241: 320.000.000. Tự tạo thẻ tài sản |
| Cuối tháng | Kế toán bấm *Chạy khấu hao* | 320.000.000 / 96 tháng = 3.333.333. Nợ 627 / Có 214 (văn phòng thì 642) |

| Nghiệp vụ sau này | Bút toán |
|---|---|
| Sửa chữa thường | Nợ 627 / Có 331, không đổi nguyên giá |
| Nâng cấp tăng công suất | Nợ 211 / Có 331, tính lại khấu hao |
| Điều chuyển bộ phận | Không bút toán, khấu hao tháng sau ghi cho bộ phận mới |
| Thanh lý | Nợ 214, Nợ 811 / Có 211. Thu tiền bán: Nợ 112 / Có 711, 3331 |

#### D8. Nhập khẩu và trả trước
Xem mục 14.

---

### Nhóm E. Thanh toán

| Trường hợp | Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|---|
| Trả một phần | Kế toán thống nhất với NCC số trả đợt này | Chọn khoản nợ, sửa số tiền nhỏ hơn | Khoản nợ *Trả một phần* |
| Gộp nhiều hóa đơn một lần chi | | Chọn nhiều khoản nợ của cùng NCC | Một lệnh chi, ghi giảm từng khoản |
| Chiết khấu trả sớm | Trả trong hạn được giảm | Chọn khoản nợ, hệ thống gợi ý số được giảm | Nợ 331 / Có 515 (phần giảm), Có 112 |
| Bù trừ (NCC cũng là khách) | Hai bên ký biên bản bù trừ | Lập phiếu bù trừ công nợ | Nợ 331 / Có 131, chỉ chi phần chênh |
| Nợ ngoại tệ | | Xem mục 14.5 | Chênh lệch tỷ giá vào 515 hoặc 635 |
| Hóa đơn từ 5 triệu đồng trở lên | | Chọn hình thức chuyển khoản | Cảnh báo nếu chọn tiền mặt, vì mất quyền khấu trừ thuế |

---

## 14. Trả trước và nhập khẩu: cách cân bằng

### 14.1. Trên app, cân bằng được làm thế nào
1. **Mỗi khoản trả trước là một dòng *Ứng trước*** gắn với đơn mua, có ba cột: đã ứng, đã đối trừ, còn lại.
2. **Khi ghi sổ hóa đơn**, hệ thống tự hiện các khoản ứng trước còn lại của NCC đó và gợi ý trừ.
3. **Màn công nợ NCC** luôn hiện: tổng hóa đơn, tổng ứng trước, tổng đã trả, số dư.
4. **Tài khoản trung gian** (151, tài khoản tạm chờ hóa đơn, 3333, 33312) chỉ là chỗ tiền đi ngang qua. Xong một vòng thì phải về 0. Còn dư là có chỗ sai.

### 14.2. Trả trước 100%, NCC giao thiếu
Đơn 5.000.000 + VAT 500.000 = 5.500.000 đ, trả trước toàn bộ.

| Bước | Trên app | Bút toán | Nợ NCC |
|---|---|---|---|
| Ứng trước | *Đề nghị ứng trước* từ đơn mua, duyệt, chi | Nợ 331 / Có 112: 5.500.000 | Dư Nợ 5.500.000 |
| NCC giao 90%, có hóa đơn | Nhập kho 90%, nhập hóa đơn, hệ thống trừ ứng trước | Nợ 152 4.500.000, Nợ 1331 450.000 / Có 331 4.950.000 | Dư Nợ 550.000 |
| NCC không giao tiếp | *Đóng sớm* đơn. Dòng ứng trước còn 550.000 hiện cảnh báo | | Dư Nợ 550.000 |
| NCC hoàn tiền | *Nhận hoàn tiền ứng trước* | Nợ 112 / Có 331: 550.000 | **0** |

Không hoàn mà muốn giữ lại thì bấm *Chuyển sang đơn* khác. NCC không hoàn, không giao thì chuyển sang phải thu khác để đòi, có quyết định xóa thì ghi 811.

### 14.3. Đặt cọc 30%, giao hai đợt
Đơn 110.000.000 đ có VAT, cọc 33.000.000 đ. Đợt 1 hóa đơn 66 triệu, đợt 2 hóa đơn 44 triệu. Trên đơn mua chọn **cách trừ cọc**:

| | Cách A: trừ hết vào hóa đơn đầu | Cách B: trừ 30% mỗi hóa đơn |
|---|---|---|
| Hóa đơn đợt 1 | Trừ 33 triệu, trả 33 triệu | Trừ 19,8 triệu, trả 46,2 triệu |
| Hóa đơn đợt 2 | Trả 44 triệu | Trừ 13,2 triệu, trả 30,8 triệu |
| Tổng chi | 110 triệu | 110 triệu |

Hai cách đều cân, chỉ khác dòng tiền từng đợt.

### 14.4. Hủy đơn sau khi đã trả trước

| Tình huống | Cách làm |
|---|---|
| Chưa nhận hàng, NCC hoàn đủ | Hủy đơn, nhận hoàn: Nợ 112 / Có 331 |
| Chuyển tiền sang đơn khác | *Chuyển sang đơn* trên dòng ứng trước |
| NCC giữ một phần làm phí hủy | Nợ 112 (phần hoàn), Nợ 811 (phí hủy) / Có 331 |
| Đã nhận một phần | Không hủy được, chỉ đóng sớm, xử lý như 14.2 |

### 14.5. Nhập khẩu trọn vòng
Đơn từ NCC nước ngoài, giá đã gồm cước tàu: K₂SO₄ 15 tấn × 600 USD = 9.000 USD, KNO₃ 5 tấn × 1.000 USD = 5.000 USD, **tổng 14.000 USD**. Trả trước 30% (4.200 USD), 70% (9.800 USD) trả sau khi nhận hàng 30 ngày.

**Quy tắc tỷ giá:** phần đã trả trước ghi giá hàng theo tỷ giá ngày trả trước, phần còn lại theo tỷ giá ngày nhận hàng. Kế toán xác nhận theo hướng dẫn hiện hành.

| # | Việc | Trên app | Bút toán |
|---|---|---|---|
| 1 | Trả trước 4.200 USD, tỷ giá 25.000 | *Đề nghị ứng trước*, chi từ tài khoản ngoại tệ | Nợ 331 / Có 1122: 105.000.000 |
| 2 | Tàu chạy, có bộ chứng từ, tỷ giá 25.100 | Mở **lô hàng nhập khẩu**, nhập vận đơn, *Ghi nhận hàng đi đường*. Giá hàng = 105.000.000 (phần đã ứng) + 9.800 × 25.100 = 245.980.000. Tổng 350.980.000, chia theo giá trị: K₂SO₄ 225.630.000, KNO₃ 125.350.000 | Nợ 151 / Có 331: 350.980.000. Nợ NCC còn dư Có 245.980.000 |
| 3 | Thông quan, tỷ giá hải quan 25.150 | Nhập tờ khai. Thuế nhập khẩu K₂SO₄ 3%: 9.000 × 25.150 × 3% = 6.790.500. Thuế GTGT nhập khẩu: (352.100.000 + 6.790.500) × 10% = 35.889.050 | Nợ 151 / Có 3333: 6.790.500 · Nợ 1331 / Có 33312: 35.889.050 |
| 4 | Nộp thuế | Lệnh chi nộp ngân sách | Nợ 3333, 33312 / Có 112: 42.679.550 |
| 5 | Phí hải quan, nâng hạ, kéo về | **Phiếu chi phí mua hàng** gắn lô hàng, 8.000.000 + VAT, chia theo khối lượng: K₂SO₄ 6.000.000, KNO₃ 2.000.000 | Nợ 151 8.000.000, Nợ 1331 800.000 / Có 331 đại lý 8.800.000 |
| 6 | Hàng về kho đủ | Thủ kho nhận theo lô hàng | Nợ 152 / Có 151: 365.770.500 |
| 7 | Phí lưu container về muộn 3.000.000 + VAT, đã xuất 10/15 tấn K₂SO₄ | Phiếu chi phí mua hàng gắn cùng lô. Hệ thống chia: K₂SO₄ 2.250.000 (1.500.000 phần đã xuất, 750.000 phần còn tồn), KNO₃ 750.000 | Nợ 152 1.500.000, Nợ 621 1.500.000, Nợ 1331 300.000 / Có 331 3.300.000 |
| 8 | Trả 9.800 USD, tỷ giá 25.300 | Đề xuất thanh toán, duyệt, chi | Nợ 331 245.980.000, Nợ 635 1.960.000 / Có 1122 247.940.000 |
| 9 | Trả đại lý và phí cảng | Đề xuất thanh toán | Nợ 331 / Có 112: 8.800.000 và 3.300.000 |

**Giá vốn khi về kho:**

| Mặt hàng | Giá hàng | Thuế nhập khẩu | Phí | Giá vốn | Mỗi tấn |
|---|---:|---:|---:|---:|---:|
| K₂SO₄ | 225.630.000 | 6.790.500 | 6.000.000 | 238.420.500 | 15.894.700 |
| KNO₃ | 125.350.000 | 0 | 2.000.000 | 127.350.000 | 25.470.000 |

**Kiểm cân bằng cuối vòng:**

| Tài khoản | Số dư | Nghĩa |
|---|---:|---|
| 331 NCC nước ngoài | 0 | Đã trả hết |
| 151 Hàng đi đường | 0 | Hàng đã về kho đủ |
| 3333, 33312 | 0 | Đã nộp thuế |
| 331 đại lý, phí cảng | 0 | Đã trả |
| 1331 | 36.989.050 | Đúng, chờ kê khai khấu trừ |
| 635 | 1.960.000 | Lỗ tỷ giá, chi phí tài chính, không vào giá vốn |
| 621 | 1.500.000 | Phần chi phí về muộn đã vào giá thành kỳ này |

### 14.6. Màn soát cân bằng cho kế toán
1. **Ứng trước chưa đối trừ:** khoản đã chi chưa có hóa đơn trừ vào, kèm số ngày treo.
2. **Hàng đi đường:** số dư 151 theo từng lô hàng, treo quá 60 ngày thì cảnh báo.
3. **Hàng về chưa có hóa đơn:** số dư tài khoản tạm theo từng phiếu nhập.
4. **Công nợ ngoại tệ:** số dư theo USD và VNĐ. Cuối kỳ tính lại chênh lệch tỷ giá theo tỷ giá cuối kỳ.

---

# PHẦN VI. TỔNG KẾT

## 15. Ranh giới với Kho và Kế toán

- **Mua hàng** sở hữu: yêu cầu mua, yêu cầu báo giá, đơn mua, bảng giá NCC, đánh giá NCC.
- **Kho** sở hữu: phiếu nhập, kết quả kiểm, phiếu trả hàng NCC, tồn kho, giá vốn tồn. Xem [`10`](./10-nghiep-vu-kho.md).
- **Kế toán** sở hữu: hóa đơn NCC, công nợ phải trả, thanh toán, sổ cái.
- Mỗi phân hệ chỉ **đọc** chứng từ của phân hệ khác, không sửa.

---

## 16. Tóm tắt một trang

**Một vòng mua hàng:**

**Yêu cầu mua** (chọn loại mặt hàng) → **Duyệt yêu cầu** → **Hỏi giá, chọn NCC** → **Đơn mua, duyệt theo hạn mức, khóa** → **NCC giao, thủ kho nhập, QC kiểm** → **NCC xuất hóa đơn ngày giao** → **Đối chiếu ba chiều, ghi công nợ** → **Đến hạn, đề nghị thanh toán, duyệt, chi tiền** → **Cuối tháng đối chiếu công nợ**

**Ba nguyên tắc:**
1. Ba người khác nhau: người mua đặt hàng, thủ kho nhận hàng, kế toán nhập hóa đơn.
2. Đơn đã duyệt thì khóa, muốn sửa thì làm phiên bản mới và duyệt lại.
3. Trả tiền theo hóa đơn đã đối chiếu, không theo đơn mua.

**Năm điều phải nhớ về tiền:**
1. Mọi chi phí đưa hàng về tới kho đều cộng vào giá vốn. Phát sinh sau khi nhập kho thì không.
2. Thuế GTGT được khấu trừ không vào giá vốn, nằm ở 1331.
3. Vật tư chưa là chi phí lúc mua, chỉ thành chi phí khi đem ra dùng hoặc khi bán.
4. Tài sản cố định thành chi phí dần qua khấu hao.
5. Các tài khoản trung gian (151, tài khoản tạm chờ hóa đơn, 3333, 33312, 331 dư Nợ) phải về 0 sau mỗi vòng.

**Loại mặt hàng quyết định luồng:**

| Loại | Duyệt | Nhận | Tài khoản |
|---|---|---|---|
| Vật tư sản xuất | Nhẹ | Kho, QC | 152 |
| Hàng hóa | Nhẹ, kiểm biên lợi nhuận | Kho hoặc giao thẳng | 156 |
| Công cụ dụng cụ | Nhẹ | Kho | 153 → 242 |
| Tài sản cố định | Nặng, lên CEO | Nghiệm thu | 241 → 211, khấu hao 214 |
| Dịch vụ | Theo hạn mức phòng | Xác nhận đã làm xong | 627 / 641 / 642 |

---

# PHỤ LỤC

## Phụ lục A. Thuật ngữ

| Từ | Nghĩa |
|---|---|
| **NCC** | Nhà cung cấp |
| **PR** (Purchase Requisition) | Yêu cầu mua hàng |
| **RFQ** (Request for Quotation) | Yêu cầu báo giá |
| **PO** (Purchase Order) | Đơn mua hàng |
| **GRN** (Goods Receipt Note) | Phiếu nhập kho |
| **QC** | Kiểm tra chất lượng |
| **MRP** | Hoạch định nhu cầu vật tư: tính từ kế hoạch sản xuất ra vật tư còn thiếu |
| **Đối chiếu 2, 3, 4 chiều** | So đơn mua với hóa đơn (2), thêm phiếu nhập (3), thêm kết quả kiểm (4) |
| **Dung sai** | Mức chênh lệch cho phép, ví dụ giá lệch ±2% vẫn chấp nhận |
| **Tài khoản tạm chờ hóa đơn** | Chỗ ghi nợ tạm khi hàng đã về mà chưa có hóa đơn. SAP gọi là GR/IR |
| **Landed cost** | Chi phí mua hàng: giá vốn hàng về tới kho, gồm giá mua và mọi chi phí đưa hàng về |
| **Hợp đồng khung** | Hợp đồng chốt giá và điều kiện một lần, mỗi lần cần thì gọi hàng. Còn gọi là hợp đồng nguyên tắc |
| **Đơn con** | Đơn mua sinh ra từ hợp đồng khung |
| **Đóng sớm** | Hủy phần chưa giao của đơn, giữ phần đã nhận |
| **Đơn dở dang** | Phần còn thiếu của một đơn đã nhận một phần |
| **Phiên bản đơn** | Mỗi lần sửa đơn đã duyệt tạo một phiên bản mới, phiên bản cũ vẫn giữ |
| **Hàng ký gửi** | Hàng NCC để ở kho mình, vẫn là của NCC, dùng tới đâu nợ tới đó |
| **Gia công ngoài** | Thuê nhà máy ngoài làm sản phẩm, mình cấp vật tư |
| **Giao thẳng** | NCC giao thẳng tới khách, hàng không qua kho mình |
| **Khấu hao** | Chia giá trị tài sản cố định thành chi phí từng tháng trong thời gian dùng |
| **Nguyên giá** | Giá trị ban đầu của tài sản: giá mua cộng vận chuyển, lắp đặt, chạy thử |
| **Nghiệm thu** | Xác nhận tài sản đã lắp xong, chạy được, đưa vào dùng |
| **Ứng trước, đặt cọc** | Trả tiền cho NCC trước khi có hóa đơn |
| **Đối trừ** | Trừ tiền ứng trước vào hóa đơn |
| **Bút toán** | Một lần ghi chuyển giá trị giữa các tài khoản, có bên Nợ và bên Có bằng nhau |

## Phụ lục B. Bảng tra nhanh: khoản này ghi vào đâu

| Khoản | Ghi vào |
|---|---|
| Mua nguyên vật liệu | Nợ 152, Nợ 1331 / Có 331 |
| Mua hàng về bán | Nợ 156, Nợ 1331 / Có 331 |
| Mua công cụ dụng cụ | Nợ 153 / Có 331, đem ra dùng: Nợ 242 / Có 153 |
| Mua máy móc, xe | Nợ 211 (hoặc 241 khi lắp đặt lâu), Nợ 1331 / Có 331 |
| Thuê sửa máy ở xưởng | Nợ 627, Nợ 1331 / Có 331 |
| Văn phòng phẩm | Nợ 642 / Có 111 hoặc 331 |
| Thuê xe giao hàng cho khách | Nợ 641 / Có 331 |
| Bảo hiểm cả năm | Nợ 242 / Có 331, mỗi tháng Nợ 642 / Có 242 |
| Cước chở hàng mua về kho | Nợ 152 hoặc 156 (cộng vào giá vốn) |
| Thuế nhập khẩu | Nợ 152 hoặc 156 / Có 3333 |
| Thuế GTGT hàng nhập khẩu | Nợ 1331 / Có 33312 |
| Phí lưu kho sau khi nhập kho | Nợ 641 hoặc 642 |
| Trả trước cho NCC | Nợ 331 / Có 112 |
| Trả tiền NCC | Nợ 331 / Có 112 |
| Được chiết khấu trả sớm | Có 515 |
| Lỗ tỷ giá khi trả nợ ngoại tệ | Nợ 635 |
| Lãi tỷ giá | Có 515 |
| Tiền phạt NCC giao trễ | Có 711 |
| Hàng thiếu chưa rõ lý do | Nợ 1381 |
| Hàng thừa chưa rõ lý do | Có 3381 |
| Phí gia công | Nợ 154, Nợ 1331 / Có 331 |
| Khấu hao máy ở xưởng | Nợ 627 / Có 214 |
| Tạm ứng nhân viên | Nợ 141 / Có 111 |
