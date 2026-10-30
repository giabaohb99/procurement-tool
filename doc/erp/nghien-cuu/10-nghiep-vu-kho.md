# NGHIỆP VỤ KHO

| | |
|---|---|
| Phiên bản | **2.0** — 30/10/2026 (dựng lại theo dạng giáo trình: thêm kế toán kho căn bản, tài khoản, luồng duyệt phiếu kho, trường hợp thường gặp, ví dụ một tháng) |
| Người viết | A5 Nghiên cứu nghiệp vụ |
| Trạng thái | Tài liệu nghiên cứu nghiệp vụ chuẩn, chưa phải tài liệu yêu cầu |
| Căn cứ | Cách SAP, Oracle, Odoo, Microsoft Dynamics dựng phân hệ Kho · Chuẩn mực kế toán số 02 *Hàng tồn kho* · Thông tư 99/2025 (số hiệu tài khoản giữ như Thông tư 200) |
| Cùng cụm | [`09` Nghiệp vụ Mua hàng](./09-nghiep-vu-mua-hang.md) · [`san-xuat/00` Nghiệp vụ Sản xuất](../san-xuat/00-tong-quan-nghiep-vu.md) · [`01` Luồng nối Mua hàng, Kho, Sản xuất](./01-luong-chuan-mua-hang-kho-san-xuat.md) |

Số tiền trong ví dụ là giả định. Chỗ dính quy định thuế, kế toán cần kế toán xác nhận.

---

## Cách đọc tài liệu này

Tài liệu viết như một giáo trình. **Đọc từ trên xuống**, phần sau chỉ dùng những gì phần trước đã giải thích:

| Phần | Học gì | Đọc xong thì hiểu |
|---|---|---|
| **I. Nền tảng** | Kho là gì, hàng trong kho được ghi sổ thế nào, các tài khoản | Biết hàng trong kho là tiền nằm ở đâu |
| **II. Tổ chức** | Ai làm gì, kho và mã hàng, trạng thái tồn, các loại phiếu và ai duyệt | Biết một phiếu kho đi qua những ai |
| **III. Luồng chuẩn** | Nhập, xuất, chuyển kho, kiểm kê | Biết thao tác từng bước trên phần mềm |
| **IV. Tiền** | Tính giá xuất kho, điều chỉnh giá trị tồn, ví dụ một tháng | Biết giá vốn tính ra sao, sổ kho khớp sổ cái thế nào |
| **V. Trường hợp thường gặp** | Sự cố khi nhập, xuất, chuyển, kiểm kê, hàng không phải của mình | Xử lý được tình huống ngoài luồng chuẩn |
| **VI. Tổng kết** | Việc cuối tháng, ranh giới với phân hệ khác, tóm tắt một trang | Nhìn lại toàn bộ |
| **Phụ lục** | Thuật ngữ, bảng tra phiếu kho và bút toán | Tra khi quên |

Chưa biết Nợ, Có là gì thì đọc trước **mục 2** của [`09` Nghiệp vụ Mua hàng](./09-nghiep-vu-mua-hang.md). Tài liệu này chỉ nhắc lại phần riêng của kho.

---

## Mục lục

**PHẦN I. NỀN TẢNG**

- [1. Kho là gì](#1-kho-là-gì)
- [2. Kế toán kho căn bản](#2-kế-toán-kho-căn-bản)
- [3. Các tài khoản dùng trong kho](#3-các-tài-khoản-dùng-trong-kho)

**PHẦN II. TỔ CHỨC**

- [4. Ai làm gì](#4-ai-làm-gì)
- [5. Kho, vị trí và mã hàng](#5-kho-vị-trí-và-mã-hàng)
- [6. Trạng thái tồn và các con số tồn](#6-trạng-thái-tồn-và-các-con-số-tồn)
- [7. Phiếu kho và luồng duyệt](#7-phiếu-kho-và-luồng-duyệt)

**PHẦN III. LUỒNG KHO CHUẨN**

- [8. Nhập kho](#8-nhập-kho)
- [9. Xuất kho](#9-xuất-kho)
- [10. Chuyển kho](#10-chuyển-kho)
- [11. Kiểm kê](#11-kiểm-kê)

**PHẦN IV. TIỀN: GIÁ TRỊ HÀNG TRONG KHO**

- [12. Tính giá xuất kho](#12-tính-giá-xuất-kho)
- [13. Điều chỉnh giá trị tồn](#13-điều-chỉnh-giá-trị-tồn)
- [14. Ví dụ một tháng của một kho](#14-ví-dụ-một-tháng-của-một-kho)

**PHẦN V. CÁC TRƯỜNG HỢP THƯỜNG GẶP**

- [15. Sự cố và tình huống đặc biệt](#15-sự-cố-và-tình-huống-đặc-biệt)
- [16. Bổ sung hàng](#16-bổ-sung-hàng)

**PHẦN VI. TỔNG KẾT**

- [17. Việc cuối tháng](#17-việc-cuối-tháng)
- [18. Ranh giới với các phân hệ khác](#18-ranh-giới-với-các-phân-hệ-khác)
- [19. Tóm tắt một trang](#19-tóm-tắt-một-trang)

**PHỤ LỤC**

- [A. Thuật ngữ](#phụ-lục-a-thuật-ngữ)
- [B. Bảng tra phiếu kho và bút toán](#phụ-lục-b-bảng-tra-phiếu-kho-và-bút-toán)

---

# PHẦN I. NỀN TẢNG

## 1. Kho là gì

Kho trả lời ba câu: **có bao nhiêu, ở đâu, trị giá bao nhiêu**. Mọi hàng ra vào đều phải qua một **phiếu kho**. Không có phiếu thì coi như hàng chưa vào hoặc chưa ra.

Kho đứng giữa các phân hệ khác:

| Phân hệ | Quan hệ với Kho |
|---|---|
| Mua hàng | Đơn mua duyệt xong thì kho có lệnh chờ nhận. Kho nhận, QC kiểm, trả hàng lỗi |
| Sản xuất | Kho cấp vật tư theo lệnh sản xuất, nhận thành phẩm và vật tư thừa trả lại |
| Bán hàng | Kho xuất hàng giao khách, nhận hàng khách trả |
| Kế toán | Mỗi phiếu kho tự sinh bút toán. Kế toán tính giá, khóa kỳ |

**Ba nguyên tắc:**
1. **Sổ kho chỉ ghi thêm.** Không sửa, không xóa phiếu đã ghi sổ. Sai thì lập phiếu đảo rồi lập phiếu đúng.
2. **Thủ kho xác nhận số thực đếm được**, không chép số trên đơn mua hay đơn bán.
3. **Hàng chưa kiểm hoặc hàng lỗi không được dùng**, dù đang nằm trong kho.

---

## 2. Kế toán kho căn bản

### 2.1. Hàng trong kho là tài sản, chưa phải chi phí
Hàng nằm trong kho là **tiền của công ty đổi sang dạng hàng**. Nó nằm ở nhóm 1 (tài sản ngắn hạn), trên bảng cân đối kế toán.

Hàng chỉ thành **chi phí** khi rời kho để dùng hoặc để bán:
- Xuất cho sản xuất: thành chi phí sản xuất (621), rồi gom vào thành phẩm.
- Xuất bán: thành **giá vốn hàng bán** (632).
- Xuất dùng cho phòng ban: thành chi phí của phòng (627, 641, 642).
- Mất, hỏng, hủy: thành giá vốn hoặc chi phí khác.

Vì vậy **mỗi phiếu xuất kho là một lần biến tài sản thành chi phí**. Giá xuất sai thì lãi lỗ sai.

### 2.2. Ghi sổ liên tục
Có hai cách theo dõi hàng tồn kho:

| Cách | Làm thế nào | Ai dùng |
|---|---|---|
| **Kê khai thường xuyên** | Mỗi lần nhập, xuất đều ghi ngay. Lúc nào cũng biết tồn bao nhiêu | Mọi phần mềm ERP. Tài liệu này dùng cách này |
| **Kiểm kê định kỳ** | Trong kỳ chỉ ghi nhập. Cuối kỳ đếm tồn, suy ra đã xuất bao nhiêu | Cửa hàng nhỏ, hàng lặt vặt |

Với cách kê khai thường xuyên, **sổ kho và sổ cái phải luôn khớp**: tổng giá trị tồn trên sổ kho của vật tư bằng số dư tài khoản 152 trên sổ cái, và tương tự với 153, 155, 156.

### 2.3. Giá trị tồn = số lượng × giá
Kho giữ hai thứ cho mỗi mã hàng: **số lượng** và **giá trị**.
- Thủ kho lo số lượng.
- Kế toán lo giá trị.
- Phần mềm nhân hai thứ lại khi xuất kho, theo cách tính giá đã chọn (mục 12).

### 2.4. Một vòng đọc thử
Kho nguyên liệu nhận 100 kg giá 10.000 đ, xuất 60 kg cho sản xuất, kiểm kê thấy thiếu 2 kg:

| # | Việc | Bút toán | Ý nghĩa |
|---|---|---|---|
| 1 | Nhập mua | Nợ 152 / Có 331: 1.000.000 | Kho có thêm hàng, mình nợ NCC |
| 2 | Xuất cho sản xuất | Nợ 621 / Có 152: 600.000 | 60 kg rời kho, thành chi phí sản xuất |
| 3 | Kiểm kê thiếu 2 kg | Nợ 1381 / Có 152: 20.000 | Hàng mất, chưa biết ai chịu, treo chờ xử lý |
| 4 | Giám đốc quyết: hao hụt cho phép | Nợ 632 / Có 1381: 20.000 | Thành giá vốn |

Tồn cuối: 38 kg, giá trị 380.000. Số dư 152 cũng đúng bằng 380.000.

---

## 3. Các tài khoản dùng trong kho

Chỉ liệt kê tài khoản kho hay đụng. Danh sách đầy đủ hơn ở mục 3 tài liệu 09.

### 3.1. Tài khoản chứa hàng (nhóm 1)

| TK | Tên | Chứa gì | Kho tương ứng |
|---|---|---|---|
| **151** | Hàng mua đang đi đường | Hàng đã là của mình nhưng chưa về kho | Không có kho thật. Thường là hàng nhập khẩu |
| **152** | Nguyên vật liệu | Vật tư để sản xuất | Kho vật tư |
| **153** | Công cụ dụng cụ | Đồ dùng nhiều lần, giá trị dưới 30 triệu | Kho công cụ |
| **154** | Chi phí sản xuất dở dang | Hàng đang làm dở, kể cả vật tư đã gửi nhà gia công | Kho tại nhà gia công |
| **155** | Thành phẩm | Hàng mình sản xuất xong, đã nhập kho | Kho thành phẩm |
| **156** | Hàng hóa | Hàng mua về bán lại, không chế biến | Kho hàng hóa |
| **157** | Hàng gửi đi bán | Hàng đã xuất giao nhưng khách chưa nhận, chưa xác nhận | Kho hàng gửi đi |

### 3.2. Tài khoản treo chờ xử lý

| TK | Tên | Khi nào dùng |
|---|---|---|
| **1381** | Tài sản thiếu chờ xử lý | Kiểm kê thiếu, chuyển kho bị hụt, chưa biết ai chịu |
| **3381** | Tài sản thừa chờ giải quyết | Kiểm kê thừa, chưa rõ hàng của ai |
| **1388** | Phải thu khác | Đã biết người phải bồi thường: nhân viên, nhà xe, nhà gia công |
| **2294** | Dự phòng giảm giá hàng tồn kho | Hàng tồn có giá bán thấp hơn giá vốn: hết mốt, gần hết hạn |

Tài khoản treo **phải về 0** sau khi có quyết định xử lý. Treo lâu là dấu hiệu kho có vấn đề.

### 3.3. Tài khoản nhận hàng xuất ra

| TK | Tên | Hàng xuất đi đâu thì ghi vào đây |
|---|---|---|
| **621** | Chi phí nguyên vật liệu trực tiếp | Xuất vật tư cho lệnh sản xuất |
| **627** | Chi phí sản xuất chung | Xuất vật tư, phụ tùng dùng chung ở xưởng |
| **641** | Chi phí bán hàng | Xuất hàng làm mẫu, khuyến mãi, dùng cho bộ phận bán hàng |
| **642** | Chi phí quản lý doanh nghiệp | Xuất dùng cho văn phòng |
| **242** | Chi phí trả trước | Xuất công cụ dụng cụ đem ra dùng, chia dần nhiều tháng |
| **632** | Giá vốn hàng bán | Xuất bán, hao hụt trong định mức, hàng hủy thông thường |
| **811** | Chi phí khác | Mất mát bất thường không ai bồi thường |
| **711** | Thu nhập khác | Hàng thừa đã xác định là của mình (cách xử lý khác: giảm 632) |

---

# PHẦN II. TỔ CHỨC

## 4. Ai làm gì

| Vai trò | Làm gì | Không được làm |
|---|---|---|
| **Thủ kho** | Nhận, xuất, chuyển, đếm hàng, lập phiếu kho | Không thấy giá, không tự duyệt điều chỉnh của mình |
| **QC** | Kiểm hàng nhập và thành phẩm, chuyển trạng thái tồn | Không nhập, xuất hàng |
| **Trưởng kho** | Duyệt xuất ngoài định mức, chuyển kho, trả NCC, điều chỉnh kiểm kê trong hạn mức | |
| **Người có nhu cầu** | Lập đề nghị xuất: sản xuất, phòng ban | Không tự lấy hàng |
| **Kế toán kho** | Theo dõi giá trị, đối chiếu sổ kho với sổ cái, xử lý tài khoản treo, khóa kỳ | Không nhập, xuất số lượng |
| **Hội đồng kiểm kê, hủy hàng** | Trưởng kho, QC, kế toán, đại diện giám đốc. Đếm, lập biên bản, quyết hủy | |

**Tách người:** người giữ hàng (thủ kho), người ghi giá trị (kế toán) và người duyệt điều chỉnh (trưởng kho hoặc cao hơn) là ba người khác nhau. Thủ kho **không thấy giá** trên màn nhận và xuất hàng.

---

## 5. Kho, vị trí và mã hàng

### 5.1. Kho
Mỗi kho thuộc **một công ty**. Ngoài kho thật còn có các **kho đặc biệt** để theo dõi hàng đang ở trạng thái khác:

| Kho đặc biệt | Chứa gì | Có thật không |
|---|---|---|
| Kho chờ kiểm | Hàng đã nhận, chưa có kết quả QC | Có thể là một khu trong kho thật |
| Kho cách ly | Hàng lỗi chờ trả, chờ hủy | Khu riêng, có biển |
| Kho đang chuyển | Hàng đã rời kho đi, chưa tới kho đến | Không, là hàng trên xe |
| Kho tại nhà gia công | Vật tư mình gửi nhà máy ngoài | Nằm ở nhà gia công |
| Kho hàng ký gửi | Hàng NCC để ở kho mình, vẫn là của NCC | Khu riêng trong kho mình |
| Kho hàng giữ hộ | Hàng của khách gửi lại | Khu riêng trong kho mình |

### 5.2. Vị trí
Kho → Khu → Dãy → Kệ → Ô. Doanh nghiệp vừa thường chỉ cần tới **Khu**. Có vị trí thì thủ kho biết lấy hàng ở đâu, kiểm kê chia được theo khu.

### 5.3. Mã hàng
Mỗi mã hàng khai một lần, dùng cho mọi phiếu:

| Thông tin | Vì sao cần |
|---|---|
| **Loại mặt hàng** | Quyết định vào kho nào, tài khoản nào (mục 6 tài liệu 09) |
| **Đơn vị tính và quy đổi** | Mua theo bao 50 kg, dùng theo kg. Kho luôn giữ theo đơn vị nhỏ nhất |
| **Theo dõi lô** | Bắt buộc với hàng cần truy xuất: thuốc, hóa chất, thực phẩm |
| **Hạn dùng** | Để xuất hàng gần hết hạn trước, cảnh báo hàng sắp hết hạn |
| **Phải kiểm khi nhập** | Có thì nhập vào chờ kiểm. Không thì vào thẳng dùng được |
| **Tồn tối thiểu, tối đa** | Mức đặt hàng lại cho từng mã, từng kho (mục 16) |
| **Cách tính giá** | Bình quân, nhập trước xuất trước, hoặc đích danh. Chọn một lần, giữ ổn định |

### 5.4. Loại mặt hàng đi vào kho nào

| Loại mặt hàng | Kho | Tài khoản |
|---|---|---|
| Vật tư sản xuất | Kho vật tư | 152 |
| Hàng hóa mua để bán | Kho hàng hóa | 156 |
| Thành phẩm tự làm | Kho thành phẩm | 155 |
| Công cụ dụng cụ | Kho công cụ | 153 |
| Tài sản cố định | **Không qua kho.** Theo dõi ở sổ tài sản | 211 |
| Dịch vụ | **Không qua kho** | 627, 641, 642 |

---

## 6. Trạng thái tồn và các con số tồn

### 6.1. Trạng thái tồn

| Trạng thái | Nghĩa | Được dùng? |
|---|---|---|
| **Chờ kiểm** | Đã nhận, chưa có kết quả kiểm | Không |
| **Dùng được** | Đã đạt | Có |
| **Cách ly** | Không đạt, chờ xử lý | Không |
| **Đã giữ chỗ** | Đã dành cho một lệnh sản xuất hoặc đơn bán | Chỉ cho lệnh hoặc đơn đó |
| **Đang chuyển** | Đã xuất khỏi kho đi, chưa tới kho đến | Không |

Đổi trạng thái **không đổi tổng tồn**, không sinh bút toán. Hàng vẫn ở 152, chỉ đổi nhãn.

### 6.2. Ba con số tồn

- **Tồn thực tế** = mọi hàng đang có, kể cả chờ kiểm và cách ly.
- **Tồn khả dụng** = dùng được − đã giữ chỗ. Đây là số được phép cấp ra.
- **Tồn dự báo** = khả dụng + hàng đang về (đơn mua đã duyệt chưa nhận) − nhu cầu đã biết (lệnh sản xuất, đơn bán chưa xuất).

**Ví dụ:** chai 450 ml.

| Thành phần | Số lượng |
|---|---:|
| Dùng được | 12.000 |
| Chờ kiểm | 3.000 |
| Cách ly | 200 |
| **Tồn thực tế** | **15.200** |
| Đã giữ cho lệnh sản xuất LSX-15 | 8.000 |
| **Tồn khả dụng** = 12.000 − 8.000 | **4.000** |
| Đơn mua đang về | 10.000 |
| Lệnh sản xuất tuần sau chưa giữ chỗ | 9.000 |
| **Tồn dự báo** = 4.000 + 10.000 − 9.000 | **5.000** |

Sản xuất hỏi *còn cấp được bao nhiêu* thì nhìn tồn khả dụng. Mua hàng hỏi *có cần đặt thêm không* thì nhìn tồn dự báo.

---

## 7. Phiếu kho và luồng duyệt

### 7.1. Các loại phiếu

| Phiếu | Tăng / giảm | Sinh ra từ | Bút toán (đơn giản) |
|---|---|---|---|
| Nhập mua | + | Đơn mua | Nợ 152, 153, 156 / Có 331 hoặc tài khoản tạm chờ hóa đơn |
| Nhập thành phẩm | + | Lệnh sản xuất | Nợ 155 / Có 154 |
| Nhập vật tư thừa từ sản xuất | + | Lệnh sản xuất | Nợ 152 / Có 621 |
| Nhập hàng khách trả | + | Đơn bán | Nợ 155, 156 / Có 632 |
| Xuất cho sản xuất | − | Lệnh sản xuất | Nợ 621 / Có 152 |
| Xuất bán | − | Đơn bán | Nợ 632 / Có 155, 156 |
| Xuất dùng nội bộ | − | Đề nghị xuất | Nợ 627, 641, 642 / Có 152. Công cụ: Nợ 242 / Có 153 |
| Xuất trả NCC | − | Phiếu nhập gốc | Nợ 331 / Có 152, 1331 |
| Xuất hủy | − | Biên bản hủy | Nợ 632 hoặc 811 / Có 152, 155, 156 |
| Chuyển kho | − kho đi, + kho đến | Phiếu chuyển | Không bút toán nếu cùng công ty |
| Chuyển trạng thái | Không đổi tổng | Kết quả QC | Không bút toán |
| Điều chỉnh kiểm kê | + / − | Biên bản kiểm kê | Thừa: Nợ 152 / Có 3381. Thiếu: Nợ 1381 / Có 152 |
| Phiếu đảo | Ngược dấu phiếu gốc | Phiếu sai | Ngược bút toán phiếu gốc |

Mỗi phiếu có **ngày ghi sổ**. Kỳ đã khóa thì không ghi lùi ngày vào được.

### 7.2. Ai duyệt phiếu nào

Phiếu sinh ra từ một chứng từ **đã duyệt ở phân hệ khác** thì kho không duyệt lại, chỉ xác nhận số thực. Phiếu kho tự phát sinh (không có chứng từ gốc) thì phải duyệt.

| Phiếu | Ai lập | Ai duyệt | Ghi chú |
|---|---|---|---|
| Nhập mua | Thủ kho | Không cần. Đơn mua đã duyệt | Đơn chưa duyệt thì chặn nhập |
| Nhập thành phẩm | Thủ kho | Không cần. QC đạt là đủ | |
| Xuất cho sản xuất trong định mức | Thủ kho theo lệnh | Không cần. Lệnh đã phát hành | |
| Xuất vượt định mức | Sản xuất đề nghị | Quản đốc, rồi trưởng kho | Bắt buộc ghi lý do |
| Xuất bán | Thủ kho theo đơn | Không cần. Đơn bán đã duyệt | |
| Xuất dùng nội bộ | Phòng có nhu cầu | Trưởng phòng | Bắt buộc chọn mục đích chi phí |
| Xuất trả NCC | Mua hàng hoặc QC | Trưởng kho | Trỏ về phiếu nhập gốc |
| Chuyển kho cùng công ty | Thủ kho đi | Trưởng kho | |
| Xuất hủy, điều chỉnh kiểm kê | Thủ kho, hội đồng | Theo hạn mức bên dưới | Kèm biên bản |
| Đảo phiếu | Thủ kho | Trưởng kho. Kỳ đã khóa: kế toán | |

**Hạn mức duyệt hủy và điều chỉnh** (ví dụ, mỗi công ty tự đặt):

| Giá trị chênh lệch | Người duyệt |
|---|---|
| Dưới 5 triệu | Trưởng kho |
| 5 đến 50 triệu | Trưởng kho → Kế toán trưởng |
| Trên 50 triệu | Trưởng kho → Kế toán trưởng → Giám đốc |

Giá trị tính theo giá vốn, nên trưởng kho thấy giá ở màn duyệt dù thủ kho không thấy.

---

# PHẦN III. LUỒNG KHO CHUẨN

**Cách đọc các bảng từ đây:** mỗi bước có ba cột:
- **Người làm (ngoài đời):** ai làm gì, ký giấy gì.
- **Trên phần mềm:** người dùng bấm gì.
- **Hệ thống, bút toán:** phần mềm tự làm gì, tiền đi vào tài khoản nào.

## 8. Nhập kho

### 8.1. Nhập mua

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Mua hàng gửi đơn cho NCC | Đơn mua duyệt xong | Kho có **lệnh chờ nhận**, thấy ngày dự kiến giao |
| Xe tới. Thủ kho đối chiếu phiếu giao hàng với đơn, đếm hàng, ký biên bản giao nhận | Chọn đơn mua, gõ **số thực đếm được**, số lô, hạn dùng, vị trí | Chặn nếu sai mã, vượt dung sai, đơn chưa duyệt |
| | Bấm xác nhận | Sinh **phiếu nhập**. Hàng vào *chờ kiểm* (hoặc *dùng được* nếu miễn kiểm). Nợ 152 / Có tài khoản tạm chờ hóa đơn, theo giá đơn mua |
| QC lấy mẫu, kiểm | Nhập kết quả: số đạt, số lỗi | Phần đạt sang *dùng được*, phần lỗi sang *cách ly*. Không bút toán |
| Kế toán nhận hóa đơn | Nhập hóa đơn, đối chiếu ba chiều (xem tài liệu 09) | Tài khoản tạm về 0, ghi nợ NCC 331. Lệch giá thì điều chỉnh giá trị tồn |

Giao nhiều lần thì **mỗi chuyến một phiếu nhập**. Phần còn thiếu thành đơn dở dang.

### 8.2. Nhập thành phẩm

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Tổ sản xuất báo xong, đưa hàng sang khu chờ kiểm | Sản xuất báo hoàn thành trên lệnh | Kho có lệnh chờ nhập thành phẩm |
| QC kiểm thành phẩm | Nhập kết quả | Đạt sang *dùng được* ở kho thành phẩm, mang số lô thành phẩm |
| Thủ kho xếp hàng vào kệ | Xác nhận phiếu nhập thành phẩm | Nợ 155 / Có 154 theo **giá tạm** (giá chuẩn hoặc ước tính) |
| Cuối tháng kế toán tính giá thành | Chạy tính giá thành | Điều chỉnh chênh lệch giữa giá tạm và giá thật vào 155 và 632 |

### 8.3. Nhập vật tư thừa từ sản xuất

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Xưởng gom vật tư dùng không hết, mang trả kho | Lập phiếu trả vật tư, trỏ về lệnh sản xuất | |
| Thủ kho đếm, kiểm còn dùng được không | Xác nhận số nhận lại | Nợ 152 / Có 621 theo giá lúc xuất. Hỏng thì vào cách ly |

### 8.4. Nhập hàng khách trả

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Bán hàng chấp nhận cho khách trả | Lập phiếu nhận hàng trả, trỏ về đơn bán | |
| Thủ kho nhận, QC kiểm | Nhận vào *cách ly* trước | Nợ 155 hoặc 156 / Có 632 theo giá vốn lúc bán. Bán hàng ghi giảm doanh thu riêng |
| QC kết luận | Còn bán được: chuyển *dùng được*. Không: hủy | |

---

## 9. Xuất kho

### 9.1. Xuất cho sản xuất

Có hai cách cấp vật tư:

| Cách | Làm thế nào | Được gì, mất gì |
|---|---|---|
| **Xuất theo lệnh trước khi làm** | Thủ kho xuất theo danh sách vật tư của lệnh | Thấy ngay xuất vượt định mức. Tốn công lập phiếu |
| **Trừ tự động sau khi báo hoàn thành** | Báo xong 1.000 sản phẩm thì hệ thống tự trừ vật tư theo định mức | Nhanh. Nhưng che mất tiêu hao thật: hao hụt cao hơn định mức phải tới kiểm kê mới lộ |

Hàng giá trị cao hoặc hay hao hụt nên xuất theo lệnh. Hàng rẻ, ổn định (keo, băng dính) có thể trừ tự động.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Kế hoạch phát hành lệnh sản xuất | Lệnh chuyển *đã phát hành* | Giữ chỗ vật tư. Kho có lệnh chờ xuất |
| Thủ kho soạn hàng theo phiếu soạn, giao tổ sản xuất ký nhận | Mở lệnh, xác nhận số thực xuất, chọn lô | Gợi ý lô **gần hết hạn trước**. Nợ 621 / Có 152 |
| Thiếu hàng giữa ca, xưởng xin thêm | Lập đề nghị xuất vượt định mức, ghi lý do | Chờ quản đốc và trưởng kho duyệt rồi mới xuất |

### 9.2. Xuất bán

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Bán hàng chốt đơn | Đơn bán duyệt | Giữ chỗ hàng. Kho có lệnh chờ xuất |
| Thủ kho soạn hàng, đóng gói | Xác nhận số thực xuất, chọn lô | Gợi ý lô gần hết hạn trước |
| Giao cho xe, tài xế ký | Xác nhận đã giao | Nợ 632 / Có 155 hoặc 156 |
| Nếu khách chưa nhận ngay (gửi qua nhà xe, đại lý) | Xác nhận *đã gửi đi* | Nợ 157 / Có 155. Khi khách xác nhận nhận: Nợ 632 / Có 157 |

### 9.3. Xuất dùng nội bộ

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Phòng cần đồ lập đề nghị | Lập đề nghị xuất, chọn **mục đích chi phí** (xưởng, bán hàng, văn phòng) | |
| Trưởng phòng duyệt | Duyệt | |
| Thủ kho phát, người nhận ký | Xác nhận phiếu xuất | Vật tư: Nợ 627, 641 hoặc 642 / Có 152. Công cụ: Nợ 242 / Có 153, rồi chia dần mỗi tháng |

### 9.4. Xuất trả NCC và xuất hủy
- **Trả NCC:** lập từ phiếu nhập gốc để lấy đúng giá. Chi tiết xem trường hợp A4 mục 13 tài liệu 09.
- **Hủy:** hội đồng lập biên bản (lý do, số lượng, cách hủy, ảnh), duyệt theo hạn mức mục 7.2, rồi thủ kho xuất hủy. Xem trường hợp D3 mục 15.

---

## 10. Chuyển kho

| Cách | Khi nào dùng | Hệ thống làm gì |
|---|---|---|
| **Một bước** | Hai kho gần nhau, giao nhận ngay | Trừ kho đi, cộng kho đến cùng lúc |
| **Hai bước** | Chuyển xa, xe chạy nhiều ngày | Kho đi xuất, hàng nằm ở **kho đang chuyển**. Kho đến xác nhận số thực nhận mới cộng. Lệch số thì lộ ngay |
| **Gửi nhà gia công** | Gửi vật tư cho nhà máy khác làm | Chuyển sang **kho tại nhà gia công**. Hàng vẫn của mình. Chi tiết xem D5 mục 13 tài liệu 09 |

Chuyển hai bước:

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho đi soạn hàng, giao xe, ký biên bản | Lập phiếu chuyển, trưởng kho duyệt, xác nhận xuất | Trừ kho đi, cộng kho đang chuyển. Cùng công ty: không bút toán |
| Xe tới, thủ kho đến đếm | Mở phiếu chuyển, gõ số thực nhận | Trừ kho đang chuyển, cộng kho đến |
| Nếu nhận thiếu | Ghi số thiếu và lý do | Phần thiếu nằm lại kho đang chuyển, phải xử lý (C1 mục 15) |

Chuyển giữa **hai công ty khác nhau** không phải chuyển kho. Đó là **mua bán nội bộ**, phải có hóa đơn (C2 mục 15).

---

## 11. Kiểm kê

### 11.1. Các bước

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Trưởng kho lên kế hoạch: kho nào, khu nào, ngày nào, ai đếm | Lập phiếu kiểm kê, chọn kho, khu, nhóm hàng | **Chụp số sổ sách** tại lúc bắt đầu |
| Thông báo dừng nhập xuất khu đang đếm | Khóa khu, hoặc để mở và ghi lại phát sinh trong lúc đếm | Chặn phiếu vào khu đã khóa |
| Hai người một tổ, đếm và ghi | Nhập số đếm, có thể quét mã trên điện thoại | **Đếm mù:** người đếm không thấy số sổ sách |
| | | Tính chênh lệch từng mã. Lệch quá ngưỡng thì yêu cầu đếm lại |
| Đếm lại các mã lệch, tìm nguyên nhân (nhập nhầm mã, xuất chưa lập phiếu) | Nhập số đếm lại, ghi nguyên nhân | |
| Hội đồng ký biên bản | Trình duyệt theo hạn mức mục 7.2 | Duyệt xong sinh phiếu điều chỉnh. Thiếu: Nợ 1381 / Có 152. Thừa: Nợ 152 / Có 3381 |
| Giám đốc quyết xử lý chênh lệch | Kế toán ghi quyết định | 1381 và 3381 về 0 (xem D1, D2 mục 15) |

### 11.2. Kiểm kê toàn bộ và xoay vòng
- **Toàn bộ:** cuối năm, bắt buộc. Thường đóng kho một đến hai ngày.
- **Xoay vòng:** chia hàng theo giá trị. Hàng giá trị cao đếm hằng tháng, hàng vừa hằng quý, hàng thấp nửa năm. Không phải đóng cả kho, sai lệch lộ sớm.

Nguyên tắc: thiếu chưa rõ nguyên nhân thì ghi **1381 chờ xử lý**, không ghi thẳng vào chi phí.

---

# PHẦN IV. TIỀN: GIÁ TRỊ HÀNG TRONG KHO

## 12. Tính giá xuất kho

### 12.1. Bốn cách

| Cách | Làm thế nào | Hợp khi |
|---|---|---|
| **Bình quân di động** | Mỗi lần nhập tính lại giá bình quân. Xuất theo giá bình quân lúc xuất | Hàng đồng nhất, nhập nhiều lần. Phổ biến nhất |
| **Bình quân cuối kỳ** | Cuối kỳ mới tính một giá cho cả kỳ | Ít nghiệp vụ, chấp nhận chờ khóa kỳ mới biết giá vốn |
| **Nhập trước xuất trước** | Xuất theo giá lô nhập sớm nhất còn lại | Hàng có hạn dùng, giá biến động mạnh |
| **Đích danh** | Xuất đúng giá của lô cụ thể | Hàng giá trị lớn, theo dõi từng chiếc, từng lô |

Chọn một cách cho mỗi nhóm hàng và **giữ ổn định cả năm**. Đổi cách phải có lý do và thuyết minh trên báo cáo tài chính.

### 12.2. So hai cách trên cùng số liệu

Cùng một mã hàng, cùng nhập và xuất như nhau:

| Ngày | Việc | Số lượng | Đơn giá nhập |
|---|---|---:|---:|
| 01/10 | Nhập | 1.000 | 50.000 |
| 05/10 | Xuất | 400 | |
| 10/10 | Nhập | 1.000 | 54.000 |
| 15/10 | Xuất | 800 | |

**Bình quân di động:**

| Ngày | Việc | Giá xuất | Tồn | Giá trị tồn | Bình quân |
|---|---|---:|---:|---:|---:|
| 01/10 | Nhập 1.000 | | 1.000 | 50.000.000 | 50.000 |
| 05/10 | Xuất 400 | 20.000.000 | 600 | 30.000.000 | 50.000 |
| 10/10 | Nhập 1.000 | | 1.600 | 84.000.000 | 52.500 |
| 15/10 | Xuất 800 | 42.000.000 | 800 | 42.000.000 | 52.500 |

**Nhập trước xuất trước:**

| Ngày | Việc | Giá xuất | Tồn còn lại |
|---|---|---:|---|
| 05/10 | Xuất 400 | 400 × 50.000 = 20.000.000 | 600 lô 01/10 |
| 15/10 | Xuất 800 | 600 × 50.000 + 200 × 54.000 = 40.800.000 | 800 lô 10/10, 43.200.000 |

**So sánh:**

| | Bình quân di động | Nhập trước xuất trước |
|---|---:|---:|
| Tổng giá xuất trong tháng | 62.000.000 | 60.800.000 |
| Giá trị tồn cuối | 42.000.000 | 43.200.000 |
| Cộng | 104.000.000 | 104.000.000 |

Tổng luôn bằng tổng tiền nhập. Cách tính giá chỉ chia **phần nào thành chi phí tháng này, phần nào còn nằm trong kho**. Giá đang tăng thì nhập trước xuất trước cho giá vốn thấp hơn, lãi tháng này cao hơn.

---

## 13. Điều chỉnh giá trị tồn

Giá trị tồn có khi phải sửa sau khi đã nhập kho. Ba trường hợp hay gặp:

### 13.1. Chi phí mua về muộn
*Ví dụ:* lô 1.000 kg nhập ngày 10, hóa đơn cước vận chuyển 2.000.000 về ngày 25. Tới ngày 25 lô đó đã xuất 600 kg, còn 400 kg.

| Phần | Số tiền | Ghi vào |
|---|---:|---|
| Phần của hàng còn tồn (40%) | 800.000 | Nợ 152: cộng vào giá trị tồn, bình quân tăng |
| Phần của hàng đã xuất (60%) | 1.200.000 | Nợ 621 nếu đã xuất cho sản xuất, Nợ 632 nếu đã bán |

Lần xuất đã chốt giá thì **không đổi lại**. Phần chênh dồn vào chi phí của kỳ hiện tại.

### 13.2. Giá thành phẩm tạm và giá thật
Thành phẩm nhập kho theo giá tạm (mục 8.2). Cuối tháng tính xong giá thành thật:
- Phần thành phẩm **còn tồn**: điều chỉnh 155.
- Phần **đã bán**: điều chỉnh 632.

### 13.3. Hàng giảm giá trị: dự phòng
Hàng hết mốt, gần hết hạn, bị lỗi nhẹ thì giá bán được có thể **thấp hơn giá vốn**. Cuối năm (hoặc cuối quý) kế toán lập **dự phòng giảm giá hàng tồn kho**:

*Ví dụ:* 500 chai giá vốn 30.000, chỉ bán được 22.000. Dự phòng 500 × 8.000 = 4.000.000.
```
Nợ 632    4.000.000
   Có 2294   4.000.000
```
Kho vẫn giữ 500 chai giá vốn 30.000. Dự phòng nằm riêng ở 2294, làm giảm giá trị trên báo cáo. Bán hoặc hủy xong thì hoàn nhập dự phòng.

---

## 14. Ví dụ một tháng của một kho

*Kho vật tư, mã dung dịch A, tính giá bình quân di động.* Tồn đầu tháng 11: **2.000 kg, giá 30.000, trị giá 60.000.000.**

| Ngày | Việc | Số lượng | Giá | Bút toán | Tồn | Giá trị tồn |
|---|---|---:|---:|---|---:|---:|
| 01/11 | Tồn đầu | | 30.000 | | 2.000 | 60.000.000 |
| 03/11 | Nhập mua, QC đạt | +3.000 | 32.000 | Nợ 152 / Có 331: 96.000.000 | 5.000 | 156.000.000 |
| | *Bình quân mới = 156.000.000 / 5.000 = 31.200* | | | | | |
| 08/11 | Xuất cho lệnh LSX-01 | −2.500 | 31.200 | Nợ 621 / Có 152: 78.000.000 | 2.500 | 78.000.000 |
| 15/11 | Chuyển 500 kg sang kho xưởng 2 | | | Không bút toán | 2.500 | 78.000.000 |
| 20/11 | Xưởng trả vật tư thừa | +100 | 31.200 | Nợ 152 / Có 621: 3.120.000 | 2.600 | 81.120.000 |
| 30/11 | Kiểm kê đếm được 2.580 | −20 | 31.200 | Nợ 1381 / Có 152: 624.000 | 2.580 | 80.496.000 |

Ngày 15/11 chuyển kho: tồn của kho chính giảm 500, kho xưởng 2 tăng 500, **tổng công ty không đổi**. Bảng trên là tổng hai kho.

**Xử lý chênh lệch kiểm kê** theo quyết định giám đốc:

| Phần | Số lượng | Bút toán |
|---|---:|---|
| Hao hụt trong định mức (bay hơi) | 15 kg | Nợ 632 / Có 1381: 468.000 |
| Thủ kho làm đổ, bồi thường | 5 kg | Nợ 1388 / Có 1381: 156.000 (trừ lương thì Nợ 334) |

**Đối chiếu cuối tháng:**

| | Số tiền |
|---|---:|
| Tồn đầu | 60.000.000 |
| + Nhập mua | 96.000.000 |
| − Xuất sản xuất | 78.000.000 |
| + Vật tư trả lại | 3.120.000 |
| − Thiếu kiểm kê | 624.000 |
| **= Tồn cuối trên sổ kho** | **80.496.000** |
| Số dư 152 trên sổ cái (phần dung dịch A) | 80.496.000 |
| Tài khoản 1381 | 0 |

Hai số khớp, tài khoản treo về 0: kho tháng 11 sạch.

---

# PHẦN V. CÁC TRƯỜNG HỢP THƯỜNG GẶP

## 15. Sự cố và tình huống đặc biệt

Mỗi trường hợp ghi *khi nào gặp*, rồi bảng ba cột như phần III. Các sự cố phía NCC (giao thiếu, giao thừa, sai mã, hàng lỗi khi QC) đã có ở **nhóm A mục 13 tài liệu 09**, ở đây không chép lại.

---

### Nhóm A. Khi nhập

#### A1. Hàng về mà chưa có đơn mua
*Khi nào:* NCC giao theo lời hẹn qua điện thoại, hoặc đơn còn đang chờ duyệt.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho không nhập vào kho chính. Nhận giữ tạm ở khu riêng, ký biên bản *nhận giữ hộ chờ đơn* | Không lập được phiếu nhập: hệ thống chặn | Không bút toán |
| Báo người mua hoàn tất đơn mua và duyệt | Người mua lập hoặc đẩy duyệt đơn | |
| Đơn duyệt xong | Thủ kho nhập theo đơn như thường | Phiếu nhập, bút toán như mục 8.1 |

Không cho *nhập trước, lập đơn sau*: đó là kẽ hở để mua ngoài quy trình.

#### A2. Hàng về trước, hóa đơn về sau
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho nhập như thường | Phiếu nhập | Nợ 152 / Có tài khoản tạm chờ hóa đơn, theo giá đơn mua |
| Cuối tháng vẫn chưa có hóa đơn | Kế toán xem báo cáo *hàng đã nhận chưa có hóa đơn* | Số dư treo được trình bày như nợ phải trả ước tính |
| Hóa đơn về, lệch giá | Nhập hóa đơn | Tài khoản tạm về 0. Phần lệch điều chỉnh giá trị tồn như mục 13.1 |

#### A3. Nhập nhầm mã hoặc nhầm số
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho phát hiện, báo trưởng kho | Mở phiếu sai, bấm *Đảo phiếu*, ghi lý do. Trưởng kho duyệt | Sinh phiếu ngược dấu, trỏ về phiếu cũ. Bút toán ngược |
| | Lập phiếu đúng | Phiếu cũ vẫn còn, có dấu *đã đảo* |
| Nếu hàng nhập nhầm đã bị xuất đi | Phải đảo phiếu xuất trước, rồi mới đảo phiếu nhập | Hệ thống chặn đảo khi tồn không đủ |

#### A4. Nhập lô không có hạn dùng hoặc thiếu số lô
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho thấy bao bì không ghi lô, hạn | Mã hàng bắt buộc lô thì không xác nhận được phiếu | Chặn |
| Hỏi NCC, hoặc tự gán lô nội bộ theo ngày nhập | Chọn *tạo lô nội bộ*, ghi chú nguồn | Lô nội bộ vẫn truy được về phiếu nhập và NCC |

---

### Nhóm B. Khi xuất

#### B1. Xuất vượt định mức
*Khi nào:* lệnh cần 1.000 nhãn, xưởng xin thêm 80 vì in lỗi.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Tổ trưởng ghi lý do, mang nhãn hỏng về làm bằng | Lập đề nghị xuất vượt, chọn lý do (hỏng máy, lỗi vật tư, lỗi người) | |
| Quản đốc, trưởng kho duyệt | Duyệt | Xuất 80 nhãn, Nợ 621 / Có 152 |
| | | Báo cáo **tiêu hao thực tế so với định mức** theo lệnh. Lỗi do vật tư NCC thì chuyển Mua hàng đòi bồi thường |

#### B2. Không đủ hàng để xuất
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho thấy trên kệ có hàng nhưng phần mềm báo hết | Không xuất được: **chặn tồn âm** | |
| Thường do: hàng chưa nhập phiếu, hàng đang chờ kiểm, nhập nhầm mã | Trưởng kho tìm nguyên nhân, nhập bổ sung hoặc giục QC | Xuất sau khi tồn khả dụng đủ |
| Thật sự hết | Báo sản xuất, bán hàng. Lập yêu cầu mua gấp | |

Không cho tồn âm. Tồn âm làm giá bình quân sai và che mất hàng xuất chưa có phiếu nhập.

#### B3. Xuất nhầm lô
*Khi nào:* phải xuất lô hết hạn tháng 12, lại xuất lô hết hạn tháng 6 năm sau.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Hàng chưa rời kho | Đảo phiếu xuất, xuất lại đúng lô | Không đổi tổng giá trị nếu tính giá bình quân |
| Hàng đã giao khách | Ghi đổi lô trên phiếu xuất (đảo và lập lại) để truy xuất đúng | Lô hết hạn tháng 12 vẫn còn trong kho, theo dõi để xử lý sớm |

#### B4. Cho mượn hàng, xuất mẫu
| Tình huống | Cách làm | Bút toán |
|---|---|---|
| Đem hàng đi hội chợ, sẽ mang về | Chuyển sang kho *hàng đem đi* | Không bút toán. Mang về thì chuyển lại, hao hụt xử lý như kiểm kê thiếu |
| Tặng mẫu cho khách, không lấy lại | Xuất dùng nội bộ, mục đích *bán hàng* | Nợ 641 / Có 155 |
| Cho công ty khác trong tập đoàn mượn | Không phải chuyển kho. Lập giấy mượn, theo dõi trả | Theo hướng dẫn kế toán, thường ghi phải thu khác 1388 |

---

### Nhóm C. Khi chuyển kho và gia công

#### C1. Chuyển hai bước bị hụt
*Khi nào:* chuyển 500 bao, kho đến nhận 497.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Thủ kho đến đếm 497, lập biên bản với tài xế | Nhận 497, ghi thiếu 3 | 3 bao còn treo ở kho đang chuyển |
| Trưởng kho hai bên tìm nguyên nhân | Đính kèm biên bản | |
| Nhà xe bồi thường | Xử lý phần thiếu: *người chịu* | Nợ 1388 (nhà xe) / Có 152 |
| Không rõ ai chịu | Xử lý phần thiếu: *chờ quyết định* | Nợ 1381 / Có 152, xử lý như kiểm kê thiếu |

#### C2. Chuyển hàng giữa hai công ty trong tập đoàn
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Hai công ty thống nhất giá chuyển | Công ty nhận lập đơn mua. Công ty giao lập đơn bán | |
| Kho bên giao xuất bán | Xuất bán theo đơn | Bên giao: Nợ 632 / Có 155, xuất hóa đơn: Nợ 131 / Có 511, 3331 |
| Kho bên nhận nhập mua | Nhập theo đơn mua | Bên nhận: Nợ 152 hoặc 156, 1331 / Có 331 |

Mỗi công ty là một đơn vị kế toán riêng. Hàng đổi chủ thì phải có hóa đơn.

#### C3. Đối chiếu tồn với nhà gia công bị lệch
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Hằng tháng nhà gia công gửi bảng kê tồn | In báo cáo tồn kho tại nhà gia công, nhập số nhà gia công báo | Tự so, kết luận Khớp hoặc Lệch |
| Lệch do hỏng vượt định mức phía nhà gia công | Ghi bồi thường theo hợp đồng | Nợ 1388 / Có 154, hoặc trừ vào phí gia công |
| Lệch do mình ghi thiếu phiếu | Lập bổ sung phiếu | |

---

### Nhóm D. Kiểm kê, hư hỏng, hết hạn

#### D1. Kiểm kê thiếu
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Hội đồng ký biên bản thiếu | Duyệt điều chỉnh | Nợ 1381 / Có 152 |
| Giám đốc quyết xử lý | Kế toán chọn cách xử lý từng phần | |
| Hao hụt trong định mức | | Nợ 632 / Có 1381 |
| Người làm mất phải bồi thường | | Nợ 1388 hoặc 334 / Có 1381 |
| Mất bất thường, không ai bồi thường | | Nợ 632 hoặc 811 / Có 1381 |

#### D2. Kiểm kê thừa
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Hội đồng ký biên bản thừa | Duyệt điều chỉnh | Nợ 152 / Có 3381, theo giá bình quân hiện tại |
| Tìm ra là NCC giao thừa | Báo Mua hàng: trả lại hoặc mua thêm | Trả lại: Nợ 3381 / Có 152 khi xuất trả |
| Tìm ra là đã xuất thiếu phiếu nhầm từ trước | Ghi giảm giá vốn | Nợ 3381 / Có 632 |
| Không rõ nguồn | Giám đốc quyết ghi thu nhập | Nợ 3381 / Có 711 |

#### D3. Hàng hết hạn, hư hỏng phải hủy
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Báo cáo hàng sắp hết hạn cảnh báo trước 30, 60, 90 ngày | Kho, kinh doanh tìm cách bán gấp, dùng trước | |
| Hết hạn thật: QC chuyển cách ly | Chuyển trạng thái *cách ly* | Không bút toán |
| Hội đồng lập biên bản hủy: lý do, số lượng, cách hủy | Lập đề nghị hủy, duyệt theo hạn mức | |
| Hủy có chứng kiến, chụp ảnh. Hóa chất thì thuê đơn vị xử lý chất thải | Xác nhận phiếu xuất hủy, đính kèm biên bản và ảnh | Nợ 632 (hoặc 811 nếu bất thường) / Có 152, 155. Có dự phòng thì hoàn nhập dự phòng |

#### D4. Hàng chậm luân chuyển
| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Kho xem báo cáo hàng không xuất trong 90, 180 ngày | In báo cáo, gửi kinh doanh và kế hoạch | |
| Còn dùng được, giá bán thấp hơn giá vốn | Kế toán lập dự phòng | Nợ 632 / Có 2294 (mục 13.3) |
| Không dùng được nữa | Hủy như D3 | |

---

### Nhóm E. Hàng nằm trong kho mình nhưng không phải của mình

#### E1. Hàng ký gửi của NCC
Hàng NCC để ở kho mình, vẫn là của NCC, dùng tới đâu nợ tới đó. Nằm ở **kho hàng ký gửi**, không vào 152 cho tới khi dùng. Cách làm đủ bước xem **D4 mục 13 tài liệu 09**.

#### E2. Hàng giữ hộ khách
*Khi nào:* khách mua và trả tiền rồi nhưng nhờ để lại kho, lấy dần.

| Người làm | Trên phần mềm | Hệ thống, bút toán |
|---|---|---|
| Bán hàng xuất hóa đơn, khách đồng ý gửi lại | Xuất bán như thường, rồi nhập vào **kho hàng giữ hộ** | Doanh thu và giá vốn ghi khi bán. Kho giữ hộ chỉ theo dõi số lượng, **không vào 155, 156** |
| Khách tới lấy từng đợt | Xuất từ kho giữ hộ | Không bút toán |
| Kiểm kê | Đếm cả kho giữ hộ, đối chiếu với khách | Thiếu thì mình phải bồi thường cho khách |

Phải tách khu riêng: lẫn với hàng của mình thì dễ bán trùng một lô hai lần.

---

## 16. Bổ sung hàng

```
Mức đặt hàng lại = Dùng mỗi ngày × Số ngày NCC giao + Tồn an toàn
```

- **Ví dụ:** dùng 2 tấn mỗi ngày, NCC giao sau 15 ngày, tồn an toàn 10 tấn. Đặt khi **tồn dự báo** xuống dưới 2 × 15 + 10 = 40 tấn.
- Hệ thống tự sinh **đề xuất mua** (hoặc đề xuất sản xuất) để kéo tồn lên mức tối đa. Đề xuất chuyển sang Mua hàng thành yêu cầu mua.
- Luôn so với **tồn dự báo**, không so với tồn thực tế, để không đặt trùng hàng đang về.
- Hàng có kế hoạch sản xuất thì MRP tính nhu cầu, mức đặt hàng lại chỉ là lớp an toàn.

---

# PHẦN VI. TỔNG KẾT

## 17. Việc cuối tháng

| # | Việc | Ai làm | Xong khi |
|---|---|---|---|
| 1 | Lập đủ phiếu cho mọi hàng đã ra vào trong tháng | Thủ kho | Không còn lệnh chờ nhận, chờ xuất đã làm ngoài đời |
| 2 | Soát hàng *chờ kiểm*, *cách ly* treo lâu | Trưởng kho, QC | Có kết luận hoặc hạn xử lý |
| 3 | Soát *kho đang chuyển* và *kho tại nhà gia công* | Trưởng kho | Khớp với biên bản và bảng kê nhà gia công |
| 4 | Kiểm kê xoay vòng theo lịch | Hội đồng | Biên bản đã duyệt |
| 5 | Xử lý 1381, 3381 | Kế toán | Hai tài khoản về 0 hoặc có quyết định |
| 6 | Tính giá thành, điều chỉnh giá thành phẩm | Kế toán | Giá tạm đã thay bằng giá thật |
| 7 | Đối chiếu giá trị tồn sổ kho với số dư 152, 153, 155, 156 | Kế toán | Hai số khớp |
| 8 | Báo cáo hàng sắp hết hạn, chậm luân chuyển | Kho | Gửi kinh doanh, kế hoạch |
| 9 | Khóa kỳ kho | Kế toán | Trước khi kế toán khóa sổ |

---

## 18. Ranh giới với các phân hệ khác

- **Kho** sở hữu: phiếu kho, kết quả kiểm, tồn, giá vốn tồn, kiểm kê.
- **Mua hàng** sở hữu đơn mua. Kho chỉ đọc đơn mua để nhận hàng. Xem [`09`](./09-nghiep-vu-mua-hang.md).
- **Sản xuất** sở hữu lệnh sản xuất, định mức. Kho cấp và nhận theo lệnh. Xem [`san-xuat/00`](../san-xuat/00-tong-quan-nghiep-vu.md).
- **Bán hàng** sở hữu đơn bán, doanh thu. Kho xuất theo đơn.
- **Kế toán** sở hữu sổ cái. Phiếu kho tự sinh bút toán, kế toán không gõ tay lại.

---

## 19. Tóm tắt một trang

**Một vòng của hàng qua kho:**

**Nhận theo đơn** (đếm số thực) → **Chờ kiểm** → **QC: đạt sang dùng được, lỗi sang cách ly** → **Giữ chỗ cho lệnh hoặc đơn** → **Xuất theo lệnh hoặc đơn** (tài sản thành chi phí) → **Kiểm kê** → **Cuối tháng: sổ kho khớp sổ cái**

**Ba nguyên tắc:**
1. Sổ kho chỉ ghi thêm. Sai thì đảo phiếu, không sửa, không xóa.
2. Thủ kho xác nhận số thực, không thấy giá. Kế toán lo giá trị.
3. Hàng chưa kiểm, hàng lỗi không được dùng.

**Năm điều phải nhớ về tiền:**
1. Hàng trong kho là tài sản. Chỉ thành chi phí khi xuất ra.
2. Phiếu nhập, xuất nào cũng sinh bút toán. Chuyển kho cùng công ty và đổi trạng thái thì không.
3. Cách tính giá chỉ chia chi phí giữa tháng này và hàng còn tồn. Tổng không đổi.
4. Thiếu, thừa chưa rõ lý do thì treo 1381, 3381, không ghi thẳng chi phí. Treo phải về 0.
5. Hàng không phải của mình (ký gửi, giữ hộ) nằm khu riêng, không vào tài khoản hàng tồn kho.

**Ai duyệt:** phiếu có chứng từ gốc đã duyệt (đơn mua, lệnh sản xuất, đơn bán) thì không duyệt lại. Phiếu kho tự phát sinh (xuất nội bộ, vượt định mức, trả NCC, hủy, điều chỉnh) thì duyệt theo hạn mức.

---

# PHỤ LỤC

## Phụ lục A. Thuật ngữ

| Từ | Nghĩa |
|---|---|
| **Phiếu kho** | Chứng từ ghi một lần hàng ra, vào hoặc đổi chỗ |
| **Phiếu đảo** | Phiếu ngược dấu để hủy tác dụng của phiếu sai |
| **Lệnh chờ nhận** | Phần đơn mua đã duyệt mà kho chưa nhận |
| **Tồn thực tế** | Mọi hàng đang có, kể cả chờ kiểm, cách ly |
| **Tồn khả dụng** | Hàng dùng được trừ phần đã giữ chỗ |
| **Tồn dự báo** | Khả dụng cộng hàng đang về trừ nhu cầu đã biết |
| **Giữ chỗ** | Dành sẵn hàng cho một lệnh hoặc một đơn |
| **Cách ly** | Trạng thái hàng lỗi, không được dùng |
| **Lô** | Nhóm hàng cùng một lần sản xuất hoặc nhập, cùng hạn dùng |
| **Định mức** | Lượng vật tư được phép dùng cho một đơn vị sản phẩm |
| **Trừ tự động sau hoàn thành** | Hệ thống tự trừ vật tư theo định mức khi báo xong sản phẩm. Tiếng Anh: backflush |
| **Đếm mù** | Người đếm không thấy số sổ sách |
| **Kiểm kê xoay vòng** | Đếm từng phần kho theo lịch, không đóng cả kho |
| **Bình quân di động** | Tính lại giá bình quân sau mỗi lần nhập |
| **Nhập trước xuất trước** | Xuất theo giá của lô nhập sớm nhất còn lại. Tiếng Anh: FIFO |
| **Giá tạm** | Giá thành phẩm dùng khi nhập kho, điều chỉnh khi tính xong giá thành |
| **Dự phòng giảm giá** | Phần giá trị hàng tồn ước mất vì bán được thấp hơn giá vốn |
| **Mức đặt hàng lại** | Mức tồn mà xuống dưới thì phải đặt thêm |
| **Tồn an toàn** | Lượng giữ thêm phòng NCC giao trễ hoặc dùng tăng đột ngột |
| **Hàng ký gửi** | Hàng NCC để ở kho mình, vẫn là của NCC |
| **Hàng giữ hộ** | Hàng của khách gửi lại kho mình |
| **Khóa kỳ** | Không cho ghi thêm phiếu vào tháng đã chốt |

## Phụ lục B. Bảng tra phiếu kho và bút toán

| Việc | Bút toán |
|---|---|
| Nhập mua vật tư | Nợ 152 / Có 331 hoặc tài khoản tạm chờ hóa đơn |
| Nhập mua hàng hóa | Nợ 156 / Có 331 |
| Nhập mua công cụ | Nợ 153 / Có 331 |
| Nhập thành phẩm | Nợ 155 / Có 154 |
| Xưởng trả vật tư thừa | Nợ 152 / Có 621 |
| Khách trả hàng | Nợ 155, 156 / Có 632 |
| Xuất cho sản xuất | Nợ 621 / Có 152 |
| Xuất dùng chung ở xưởng | Nợ 627 / Có 152 |
| Xuất dùng văn phòng | Nợ 642 / Có 152 |
| Xuất mẫu, khuyến mãi | Nợ 641 / Có 155, 156 |
| Xuất công cụ đem ra dùng | Nợ 242 / Có 153, mỗi tháng Nợ 627, 641, 642 / Có 242 |
| Xuất bán, khách nhận ngay | Nợ 632 / Có 155, 156 |
| Xuất gửi đi, khách chưa nhận | Nợ 157 / Có 155, khi khách nhận Nợ 632 / Có 157 |
| Gửi vật tư cho nhà gia công | Nợ 154 / Có 152 |
| Xuất trả NCC | Nợ 331 / Có 152, 1331 |
| Xuất hủy | Nợ 632 hoặc 811 / Có 152, 155, 156 |
| Chuyển kho cùng công ty | Không bút toán |
| Chuyển trạng thái | Không bút toán |
| Kiểm kê thiếu | Nợ 1381 / Có 152 |
| Xử lý thiếu: hao hụt cho phép | Nợ 632 / Có 1381 |
| Xử lý thiếu: người bồi thường | Nợ 1388 hoặc 334 / Có 1381 |
| Kiểm kê thừa | Nợ 152 / Có 3381 |
| Xử lý thừa | Nợ 3381 / Có 632 hoặc 711 |
| Chi phí mua về muộn, hàng còn tồn | Nợ 152 / Có 331 |
| Chi phí mua về muộn, hàng đã xuất | Nợ 621 hoặc 632 / Có 331 |
| Lập dự phòng giảm giá | Nợ 632 / Có 2294 |
