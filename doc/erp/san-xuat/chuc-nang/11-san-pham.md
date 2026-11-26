# 11 — SẢN PHẨM: MÃ HÀNG, QUY TẮC, CÔNG THỨC, ĐỊNH MỨC (BOM), TIÊU CHÍ ĐÁNH GIÁ

| | |
|---|---|
| Bản | 0.2 |
| Ngày | 26/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | — |

## 1. Phần này là gì

Tài liệu này mô tả phần **Sản phẩm** của phân hệ Sản xuất gia công trên ERP DEGO Holding: danh mục mã hàng (nguyên liệu, bán thành phẩm, vật tư bao bì, thành phẩm), các quy tắc đặt mã và khai báo, công thức bán thành phẩm, ba tầng bảng định mức (BĐM BTP, BĐM VTBB, BĐM thành phẩm) cùng bản định mức thuế, và các tiêu chí đánh giá gắn với sản phẩm (test mẫu, sai số hàm lượng, sai số chiết rót, KCS). Kèm theo là ba sổ phụ gắn với mã hàng: khảo sát vật tư bao bì phù hợp công nghệ của nhà cung cấp gia công, cọc nhãn, mẫu cho tặng.

Nguồn là các tệp Google Sheets của phòng Sản xuất (bản tải về dạng Excel). Các tệp này là **quy trình làm việc và biểu mẫu**, số liệu bên trong là **mô phỏng**; tài liệu chỉ rút ra cấu trúc trường, cách tính và quy định, không coi số dòng là dữ liệu thật. Mỗi tính năng đều ghi rõ ERP **đã có** gì và **chưa có** gì (đối chiếu mã nhánh `erp-v2`).

Bối cảnh cần nhớ khi đọc: DEGO **không tự sản xuất**. DEGO mua nguyên liệu (NL), bán thành phẩm (BTP), vật tư bao bì (VTBB) rồi gửi sang nhà cung cấp gia công (NCC GC); NCC GC phối BTP, sang chai, đóng gói ra thành phẩm (TP, trên sổ gọi là hàng hóa HH). Có đơn NCC lo gần hết (DEGO chỉ mang nhãn), có đơn DEGO mang gần hết (NCC chỉ thu phí đóng gói). Vì vậy định mức ở đây không chỉ là *cần bao nhiêu vật tư* mà còn là *bên nào chuẩn bị vật tư đó* và *hóa đơn đi đường nào*.

---

## 2. Mục đích và người dùng

### 2.1 Mục đích

1. Có **một danh mục mã hàng duy nhất** cho sản xuất, đặt mã và đặt tên theo một quy tắc, không khai trùng, khớp với mã trên phần mềm kế toán (Misa).
2. Biết **mỗi thành phẩm làm từ gì**: ruột nào (BTP, công thức, dòng V, màu), bao bì nào (chai, nắp, nhãn, thùng...), phí gia công nào, bên nào cung ứng từng thứ.
3. Có định mức **được duyệt, có phiên bản** để lập lệnh sản xuất, xuất kho, quyết toán vật tư với NCC GC và tính giá vốn.
4. Giữ **chất lượng sản phẩm đúng pháp lý**: hàm lượng hoạt chất trong khung sai số, thể tích chiết rót trong khung, mẫu được test trước khi chốt công thức và trước khi nhập kho.
5. Giữ **bảo mật công thức**: dòng công thức Kinh doanh hiểu khác dòng công thức chốt với NCC; nguyên liệu mã hóa che tên thật.

### 2.2 Người dùng

| Vai trò | Viết tắt | Làm gì ở phần Sản phẩm |
|---|---|---|
| Quản lý sản xuất | QLSX | Duyệt khai báo mã, duyệt cả ba tầng BĐM, duyệt kết quả khảo sát công nghệ, duyệt công thức chốt với NCC. |
| Quản lý dữ liệu | QLDL | Khai báo mã BTP cấu thành (BTPCT), phí phối trộn (PPT), phí sang chai đóng gói (PĐG); giữ bảng đồng bộ mã DEGO - mã NCC; **gộp BĐM BTP và BĐM VTBB thành BĐM thành phẩm**; gửi BĐM cho kế toán; làm hợp đồng cọc nhãn. |
| Giá vốn | GV | Dùng BĐM và giá để tính giá vốn BTP, giá vốn TP; giữ trạng thái giá. Không sửa BĐM. |
| Điều phối NL / BTP | ĐP NL/BTP | Khai báo mã BTP mua (BTPM); giữ danh sách công thức và dòng công thức; lập BĐM BTP; theo dõi công thức mới và test mẫu; khảo sát NL / BTP phù hợp công nghệ NCC. |
| Điều phối VTBB | ĐP VTBB | Khai báo mã VTBB và thuộc tính; lập BĐM VTBB theo mockup; khảo sát VTBB phù hợp công nghệ; theo dõi cọc nhãn; ghi mẫu cho tặng. |
| Điều phối thành phẩm | ĐP TP | Khai báo kho, công ty nội bộ; gửi yêu cầu làm BĐM khi có đơn mới; dùng BĐM để lập lệnh sản xuất. |
| Lab / R&D | Lab | Cấp công thức, mã công thức Lab, tỷ trọng, tiêu chuẩn nguyên liệu; phối mẫu; test hàm lượng và ngoại dạng; lưu mẫu đối chứng. |
| Pháp lý sản xuất | PL | Cấp tên pháp lý, thành phần đăng ký, đơn vị cấu thành, luồng hóa đơn; kiểm hàm lượng theo giấy đăng ký; duyệt pháp lý trên phiếu BĐM. |
| Kinh doanh | KD | Yêu cầu sản phẩm mới, chọn dòng công thức theo cách KD hiểu, chọn bao bì cùng Thiết kế, gửi yêu cầu khảo sát; chốt cọc nhãn; xem dữ liệu VTBB và giá. |
| Thiết kế | TK | Làm mockup, **gắn mã VTBB vào mockup**, khai báo hàng hóa (HH) mới, giữ sổ Quản lý nhãn mác, duyệt nhãn với NCC. |
| Thu mua | TM | Khai báo mã NL, BTP ruột, BTP nhập khẩu, chi phí nhập khẩu, NCC thu mua; cấp giá NL và giá VTBB. |
| Phòng Tài chính kế toán | P TCKT | Tạo mã trên Misa sau khi khai báo được duyệt; nhận bản gốc BĐM; kế toán trưởng ký phiếu BĐM. |
| NCC gia công | NCC GC | Cấp mã và tên hàng phía NCC, báo phí phối, phí đóng gói, kết quả khảo sát công nghệ, duyệt nhãn, báo tiền cọc nhãn. Không đăng nhập ERP (giai đoạn đầu). |

---

## 3. Khái niệm

### 3.1 Các loại mã

| Loại | Tiền tố | Là gì | Ai khai báo |
|---|---|---|---|
| Nguyên liệu nhập khẩu | `NLNK` | Nguyên liệu mua từ nước ngoài. | Thu mua |
| Nguyên liệu kỹ thuật | `NLT` | Nguyên liệu kỹ thuật (tech) có hàm lượng hoạt chất, vd *Abamectin 95% TC*. Là đầu vào để phối BTP. | Thu mua, ĐP NL/BTP |
| Nguyên liệu mã hóa | `NA` | Phụ gia được **che tên thật**, tên hiển thị chỉ là *Phụ gia NA0001*. Gắn với cấp bảo mật công thức. | Thu mua, Lab |
| BTP ruột | `BTPR` | Ruột sản phẩm đã phối xong, sẵn sàng sang chai. BTPR = BTP nhập khẩu + chi phí nhập khẩu, hoặc = NL kỹ thuật + phí phối trộn. | Thu mua (Lab, ĐP NL/BTP) |
| BTP mua | `BTPM` | Ruột mua thẳng từ NCC GC. Sổ ghi *dự kiến bỏ năm 2027*. | ĐP NL/BTP |
| BTP nhập khẩu | `BTPNK` | BTP mua nước ngoài, dùng ghi công nợ NCC nước ngoài (chưa gồm VAT, phí dịch vụ, thuế khác). | Thu mua |
| BTP cấu thành | `BTPCT` | Mã ghi công nợ NCC GC khi NCC bán gộp ruột + phần NCC không tách được (thùng, chai, phí đóng gói). Dùng để cấu thành giá vốn TP. | QLDL |
| BTP từ R&D | theo Lab | BTP phân bón do Lab phối; mã theo quy tắc riêng của Lab. | Lab |
| Vật tư bao bì | `C..`, `NAP`, `N..`, `TH.`, `NDT`, `HOP`, `XO`, `CAN`, `LON`, `COC`, `SEAL` | Chai, nắp, túi / nhãn, thùng, nhãn dán thùng, hộp, xô, can, lon, cốc đong, seal... | ĐP VTBB |
| Chi phí nhập khẩu | `CPNK` | Tổng chi phí một đơn nhập khẩu (VAT, phí dịch vụ, thuế khác). | Thu mua |
| Phí gia công phối trộn | `PPT` | Phí NCC thu để phối NL thành BTP ruột. | QLDL |
| Phí sang chai đóng gói | `PĐG` | Phí NCC thu để đưa ruột vào bao bì thành TP, theo dải thể tích. | QLDL |
| Hàng hóa (thành phẩm) | `HH` | Một mã = một sản phẩm bán được: thương hiệu + khách hàng + nhãn hiệu + tên pháp lý + quy cách + quy cách thùng. | Thiết kế |

### 3.2 Tên pháp lý và tên thương mại

- **Tên pháp lý** (còn gọi *tên đăng ký*, *tên thương phẩm*): tên sản phẩm trên giấy đăng ký lưu hành, vd *HAIHAMEC 3.6EC*, *FORTIL 25SC*. Đi kèm **thành phần đăng ký** (hoạt chất + hàm lượng, vd *Fenobucarb 500 g/l*). Một tên pháp lý thuộc một đơn vị đăng ký, có thể cho đơn vị khác thuê tên, có giấy hợp quy với ngày hiệu lực và ngày hết hạn. Hai tên pháp lý có thể dùng chung một ruột (vd *Haihamec 3.6EC* và *Chitin 3.6EC*).
- **Tên thương mại** (*tên nhãn hiệu*, *tên sản phẩm*): tên in to trên nhãn cho từng khách hàng, vd *ĐẠI BÀNG SH*, *AGRIFORT*. Một tên pháp lý có rất nhiều tên thương mại, mỗi tên thương mại + quy cách là một mã HH.
- **Tên trên hóa đơn**: tên phải ghi khi xuất / nhận hóa đơn. Với HH là *tên pháp lý - quy cách sản phẩm - quy cách thùng*; với VTBB có mẫu tên riêng (vd *Thùng carton 5 lớp*, lon ghi là *Hũ*).

### 3.3 Công thức, dòng V, màu

- **Công thức**: tỷ lệ phối nguyên liệu để ra BTP. Lab giữ **mã công thức Lab**; công thức chốt với NCC ghi riêng.
- **Dòng V** (V1 đến V6): các bậc chất lượng / biến thể của cùng một tên pháp lý (khác phụ gia, khác định vị). Vd *Genol 1.2SL* có V1, V2, V3, V4, V6.
- **Màu**: màu gốc của công thức nguyên bản và màu thực tế sau khi pha thêm theo yêu cầu khách. Có màu **độc quyền theo khách hàng** (vd cùng một sản phẩm, mỗi nhóm khách một màu riêng).
- **Dòng công thức KD và dòng công thức NCC**: cùng một ruột nhưng Kinh doanh gọi là *V3 nước tím* trong khi NCC gọi là *V2 nước tím*. Sổ *1.1 DS và dòng công thức BTP* giữ bảng quy đổi này và ghi rõ là **bảo mật**.
- **Mã SP gốc**: cách gọi gọn dòng V + màu trên BĐM thành phẩm, vd *Dòng V1 - Nước trắng*.

### 3.4 Hàm lượng và tỷ trọng

- **Hàm lượng sản phẩm**: hàm lượng hoạt chất theo đăng ký (%, g/l, g/kg).
- **Hàm lượng yêu cầu sản xuất**: hàm lượng DEGO yêu cầu NCC phối, có thể thấp hơn hàm lượng đăng ký trong phạm vi sai số cho phép.
- **Hàm lượng trên nhãn NL** và **hàm lượng thực tế NL**: nguyên liệu ghi 95% nhưng lô thực tế test ra 97,8% thì lượng cần dùng ít hơn. Đây là lý do một sản phẩm có nhiều phiên bản BĐM BTP.
- **Tỷ trọng BTP sau phối**: dùng để đổi lít sang kg. Thuốc BVTV tính theo hàm lượng; phân bón tính theo tỷ trọng.
- **Sai số phối chế cho phép**: mức lệch hàm lượng DEGO chấp nhận khi phối, phải nằm trong khung sai số của Nhà nước.

### 3.5 Định mức

- **BĐM BTP**: cần những nguyên liệu nào, bao nhiêu kg, để ra **1.000 kg (hoặc 1.000 lít) BTP**.
- **BĐM VTBB**: cần những vật tư bao bì nào cho **1 đơn vị thành phẩm** (1 chai, 1 gói, 1 xô, 1 can).
- **BĐM thành phẩm (BĐM TP)**: gộp ruột + bao bì + phí gia công cho 1 đơn vị thành phẩm, kèm bên cung ứng từng dòng.
- **Cấu thành**: mô tả bên nào chuẩn bị gì, vd *IDA: chai, nhãn, thùng, lấy nhãn chính dán thùng, túi PE / Hà Long: BTP, phí đóng gói*.
- **Cấu thành nội bộ và cấu thành thuế**: cùng một thành phẩm có thể có hai bộ định mức. Bộ **nội bộ** phản ánh thực tế vận hành (ai mang gì sang NCC). Bộ **thuế** phản ánh hồ sơ kế toán thuế của từng công ty nội bộ (công ty nào là đơn vị cấu thành, hóa đơn đầu vào là gì, luồng hóa đơn NCC → đơn vị cấu thành → đơn vị nhận hóa đơn → đơn vị bán). Mỗi công ty nội bộ (IDA, ABA, DEGO...) có một bộ BĐM thuế riêng. Sổ ghi mục tiêu: sau khi đồng bộ mã Thuế - Nội bộ thì chỉ còn một bảng dùng chung.

---

## 4. Quy tắc

### 4.1 Quy tắc đặt mã và tên

Nguồn: *QUY TRÌNH SẢN XUẤT › 2. QT KHAI BÁO SX* (bước 3) và các sheet danh mục VTBB. Số chạy 4 chữ số.

| Loại | Mã | Tên nội bộ | Tên trên hóa đơn | Ví dụ |
|---|---|---|---|---|
| NL nhập khẩu | `NLNK` + 4 số | *Nguyên liệu* + tên + hàm lượng + ĐVT hàm lượng | như tên nội bộ | — |
| NL kỹ thuật | `NLT` + 4 số | như trên | như tên nội bộ | `NLT0192` Fenobucarb 98% TC |
| NL mã hóa | `NA` + 4 số | *Phụ gia* + mã | — | `NA0001` Phụ gia NA0001 |
| BTP ruột | `BTPR` + 4 số | *BTPR* + loại + tên pháp lý + dòng V + dạng + màu + thành phần | tên pháp lý | `BTPR0057` ABASBA 50EC V1 nước màu tím |
| BTP mua | `BTPM` + 4 số | tương tự BTPR | tên pháp lý | `BTPM0058` JAPAVIL 110SC V1 nước màu trắng sữa |
| BTP nhập khẩu | `BTPNK` + 4 số | tên pháp lý + hoạt chất + hàm lượng + ĐVT | như tên nội bộ | — |
| BTP cấu thành | `BTPCT` + **4 số cuối mã HH** | *BTPCT* + tên HH + NCC | tên pháp lý + quy cách SP + quy cách thùng + *(gia công)* | — |
| Chai | `C` + chữ chất liệu + chữ hình dạng + 4 số | *Chai* + chất liệu + hình dạng + cổ + thể tích + (trọng lượng g) + màu + nhận diện riêng | *Chai* + chất liệu + thể tích | `CPT0001` Chai PET tròn cổ 35 450ml-500ml (40g) trắng; `CPV` = PET vuông; `CHT` = HDPE tròn |
| Nắp | `NAP` + 4 số | *Nắp* + chất liệu + cổ + (trọng lượng) + màu + logo / garanti | — | `NAP0001` Nắp PET cổ 35 (4.3g) vàng |
| Túi / nhãn | `N` + 2 chữ chất liệu + **4 số cuối mã HH** | *[Nhãn]* + tên HH | — | `NTN` nhãn túi nhôm, `NTG` túi giấy, `NHD` nhãn decal, `NHG` nhãn giấy; vd `NHG4995` |
| Nhãn dán thùng | `NDT` + 4 số cuối mã HH | — | — | `NDT4995` |
| Thùng | `TH` + chữ thương hiệu + 4 số | *Thùng* + thương hiệu / dùng chung + loại chai + quy cách + kích thước phủ bì D x R x C + màu | *Thùng carton* + số lớp | `THI0001` thùng IDA; `THC0003` thùng dùng chung |
| Hộp | `HOP` + 4 số cuối mã HH (hộp riêng) hoặc mã gợi ý (hộp dùng chung) | — | — | — |
| Xô, can, lon, cốc, seal | `XO` + chữ đầu màu + 4 số; `CAN`; `LON`; `COC`; `SEAL` | theo mẫu từng loại | lon ghi *Hũ*; seal không có tên hóa đơn | `COC0004` Cốc đong cổ 49 50ml |
| Chi phí nhập khẩu | `CPNK` + 4 số | — | — | — |
| Phí phối trộn | `PPT` + 4 số | *Phí gia công phối trộn* + NCC + thuốc / phân + tên pháp lý + dòng V + màu | — | — |
| Phí sang chai đóng gói | `PĐG` + 4 số | *Phí sang chai đóng gói* + NCC + loại VTBB + quy cách theo bảng giá NCC | — | `PĐG0099` Phí sang chai đóng gói Hà Long chai tròn 801ml - 1000ml |
| Hàng hóa | `HH` + 4 số | thương hiệu - mã đơn vị xuất hóa đơn - số mã hàng - khách hàng - nhãn hiệu (màu / dạng ruột) - quy cách SP - quy cách thùng | tên pháp lý - quy cách SP - quy cách thùng | `HH4995` GC - V - 4995 - Sen Hồng - HAIHAMEC 3.6EC (Nước nâu đen) - 450ml - 40 |
| NCC GC, NCC thu mua, đơn vị vận chuyển | **mã = mã số thuế** | tên trên giấy đăng ký kinh doanh | — | — |
| Kho tại NCC | `KHO NCC_<viết tắt NCC>` và `KHO NCCXL_<viết tắt NCC>` (kho hàng lỗi) | — | — | mỗi NCC GC đúng hai kho |

Quy tắc phụ:

1. **Mã đơn vị xuất hóa đơn** trong tên HH: I = IDA Global, II = Agricare, IV = ABA, V = DEGO Holding, VI = Bamboo, VII = Nông nghiệp DEGO, VIII = Dr Xanh, IX = N2SBio. Không có III.
2. **Mã ăn theo mã HH**: nhãn, nhãn dán thùng, hộp riêng, BTPCT lấy 4 số cuối của mã HH. Một HH có thể có nhiều nhãn nên có hậu tố `.1`, `.2` (vd `NHD0013.1`).
3. **Mã màu 2 ký tự** dùng trong mã BĐM BTP: ĐỎ = `ĐO`, TRẮNG = `TR`, HỒNG = `HO`, CAM = `CA`, VÀNG = `VA`, TÍM = `TI`, XANH DƯƠNG = `XD`, XANH LÁ = `XL`, ĐEN = `ĐE`.
4. **Viết tắt tên pháp lý** dùng trong mã BĐM BTP: chữ cái đầu hoặc mã rút gọn có số, vd *CHITIN 3.6* = `CT3.6`, *CREEK 2.1* = `CR2.1`, *ABASBA* = `ABB`, *ASUPERGRAS* = `ASPG`.
5. **ĐVT** viết hoa chữ đầu, chọn từ danh mục: Cái, Bộ, Kg, Lít, Ml, Gram, Cuộn, Bịch, Can, Thùng, Lon, Bao, Xô, Chai, Gói, Pallet, Lô, M2.
6. **Không khai trùng**: thông tin trùng mã cũ thì không khai báo, phản hồi cho người yêu cầu.
7. **Đổi thuộc tính vật lý là mã mới**: VTBB đổi chất liệu, kích thước, màu, hình dạng thì khai mã mới; NL đổi hàm lượng thì khai mã mới; BTP đổi dạng, dòng V, màu, hàm lượng thì khai mã mới.

### 4.2 Quy tắc mã chứng từ định mức

| Chứng từ | Quy tắc theo quy trình (QT 2.1) | Thực tế trên sổ | Ví dụ |
|---|---|---|---|
| BĐM BTP | `BDMBTP_` + viết tắt tên pháp lý + `_` + mã màu + `_` + dòng V + `_` + số thứ tự 2 số | không có tiền tố `BDMBTP_` | `ABB_TI_V1_01`, `ASPG_DO_V2_02`, `CT3.6_XL_V2_01` |
| BĐM VTBB | `BDMVT_` + mã HH + `_` + số thứ tự | `VT_` + mã HH + `_` + số thứ tự | `VT_HH4995_01` |
| BĐM TP | `BDMTP_` + mã HH + `_` + số thứ tự | `BĐMTP_` + mã HH + `_` + số thứ tự | `BĐMTP_HH3309_01` |

Tiền tố lệch nhau giữa quy trình và sổ; cần chốt một kiểu (câu hỏi 3 ở mục 11).

### 4.3 Quy tắc phiên bản BĐM

1. Hai số cuối của mã BĐM là **số phiên bản**: `_01`, `_02`...
2. **BĐM BTP ra phiên bản mới** khi: khác dạng BTP (lỏng / rắn), đổi hàm lượng nguyên liệu (thuốc), đổi tỷ trọng (phân), hoặc dùng lô nguyên liệu có hàm lượng thực tế khác (vd cùng *ASUPERGRAS 200SL V2 đỏ*: `_01` dùng NL thực tế 95% cần 210,53 kg; `_02` dùng NL thực tế 97,8% cần 204,50 kg).
3. **BĐM VTBB ra phiên bản mới** khi: khác quy cách sản phẩm hoặc đổi chất liệu / mã VTBB (kể cả thay vật tư giữa chừng trong sản xuất). Ghi lý do ở cột *Ghi chú khác (lý do thay đổi)*.
4. **BĐM TP**: số phiên bản tăng theo từng tổ hợp (mã HH + mã BĐM VTBB) khác nhau. Ghi **mã đơn hàng đầu tiên phát sinh BĐM** để biết phiên bản bắt đầu dùng từ đơn nào.
5. Trước khi lập mới phải **tra BĐM cũ** theo tên pháp lý (BTP) hoặc tên pháp lý + quy cách (VTBB, TP); đã có thì dùng lại, không lập mới.
6. BĐM phải **theo thực tế**: thay NL / BTP / VTBB trong sản xuất thì lập BĐM mới và gửi QLDL.
7. Phiên bản cũ **không xóa, không sửa đè**; đơn hàng cũ vẫn trỏ về phiên bản lúc sản xuất.

### 4.4 Quy tắc đồng bộ mã DEGO - mã NCC

1. Mỗi NCC GC đặt mã và tên hàng riêng cho cùng một vật tư / BTP. Sổ *Data đồng bộ NCC GC* giữ cặp: mã DEGO, tên DEGO (lấy từ Misa), mã NCC, tên NCC (NCC cung cấp), NCC GC, phân loại (VTBB hay NL/BTP).
2. Bảng này là điều kiện để **đối chiếu tồn kho và công nợ** với NCC: số NCC gửi về mang mã NCC, phải đổi sang mã DEGO mới so được.
3. QLDL nhập và giữ bảng (sổ ghi *chưa chốt*, mới có một NCC).
4. Đồng bộ **dòng công thức** KD - NCC là bảng riêng (mục 3.3), bảo mật hơn bảng đồng bộ mã.
5. Checklist hợp đồng NCC mới có mục *quy trình nhập xuất NL / VTBB và đồng bộ mã NCC - mã DEGO*: phải thống nhất trước đơn hàng đầu tiên.

### 4.5 Quy tắc quy đổi mã Kinh doanh sang mã Sản xuất

1. Kinh doanh đặt hàng theo **mã HH + dòng công thức KD** (vd Thipro 550EC dòng V3 nước tím).
2. Sản xuất đổi sang **mã BTP ruột + dòng công thức NCC** (vd tại Hà Long là dòng V2 nước tím) qua *Danh sách quản lý BTP* (DSQL BTP).
3. Trên đơn điều phối có cột *mã BĐM BTP KD* tự chạy theo mã HH; ĐP NL/BTP điền mã BĐM NL/BTP thật (nội bộ và thuế).
4. Chưa có trong DSQL BTP thì: hỏi KD mã, Lab xác định công thức, khai mã BTP, làm BĐM, rồi cập nhật DSQL BTP.

### 4.6 Quy tắc khai báo và duyệt mã mới

1. **Ai khai báo loại nào**: xem cột cuối bảng 3.1.
2. **Kiểm trùng trước**: Thu mua kiểm NCC thu mua, đơn vị vận chuyển, NL, BTPR, BTPNK, CPNK; ĐP TP kiểm kho, công ty nội bộ, khoản mục chi phí; QLDL kiểm NCC GC, BTPCT, PPT, PĐG; ĐP NL/BTP kiểm BTPM; ĐP VTBB kiểm VTBB.
3. **Trình duyệt**: Thu mua trình quản lý thu mua; các bộ phận thuộc Sản xuất trình QLSX.
4. **Gửi mẫu khai báo** cho P TCKT sau khi duyệt; P TCKT tạo mã trên Misa và phản hồi.
5. **Cập nhật danh mục** sản xuất: lấy mã, tên, ĐVT từ Misa về, bổ sung thuộc tính chi tiết theo mẫu.
6. Sổ khai báo của QLDL có các cột trạng thái: *hiện trạng sử dụng*, *trạng thái khai báo*, *ngày gửi khai báo*, *người khai báo*.
7. PPT và PĐG khai **theo mỗi lần NCC báo giá**; BTPCT khai **theo đơn hàng** nếu chưa có mã.

### 4.7 Quy tắc quản lý nhãn mác

Nguồn: sheet *QUẢN LÝ NHÃN MÁC* (kéo từ sổ *QUẢN LÝ NHÃN MÁC IDA GROUP* của Thiết kế, mỗi dòng một mã HH). Sổ gốc đã nhận
ngày 26/11/2026 và là **dữ liệu thật**: 11.150 mã HH, bản quy tắc đặt mã 31/03/2026, định mức VTBB thật của 4.189 mã HH
(9 ô thành phần, có *Hộp* và *VTBB khác 1–3*) — xem [`nghien-cuu/21`](../nghien-cuu/21-so-quan-ly-nhan-mac-ida-group.md).

1. Mỗi mã HH có một hồ sơ nhãn mác gồm: tình trạng sản phẩm (*đã in*, *chưa in*, *tạm ngưng*, *bỏ nhãn*, *mua thành phẩm*...), khách hàng / thương hiệu, công ty phân phối, **đại diện pháp lý / hóa đơn** (công ty xuất hóa đơn đầu ra), dòng sản phẩm (phân bón, thuốc trừ sâu, trừ bệnh, trừ cỏ...), tên đăng ký, mô tả ruột (vd *Nước đỏ*), tên nhãn hiệu nội bộ, **công ty nhận hóa đơn đầu vào**, **NCC sản xuất**, quy cách sản phẩm, quy cách thùng, quy cách bao, ĐVT chính, chất liệu bao bì chứa, chất liệu nhãn, kích thước nhãn, loại thùng, kích thước thùng, nhãn dán thùng (có / dùng nhãn chính / kích thước), hộp giấy, lưu ý sản phẩm, tên sản phẩm (ghép tự động), link hình VTBB, hoạt chất, trọng lượng.
2. Hồ sơ có sáu cột mã bao bì gắn sẵn: **chai / xô / can / lon, nhãn chai / túi, túi, thùng, NDT, nắp, hộp**. Đây là điểm xuất phát của BĐM VTBB.
3. Thiết kế là chủ dữ liệu; các sổ khác chỉ kéo về để tra.
4. Thay bao bì hoặc đổi quy cách thì khai **mã HH mới** hoặc lập **BĐM VTBB phiên bản mới** (cần chốt ranh giới, câu hỏi 8).
5. Nhãn phải được **NCC duyệt** trước khi in (nhóm *Duyệt nhãn - In ấn VTBB*); trên đơn hàng có cột trạng thái NCC duyệt nhãn.
6. Lưu ý độc quyền ghi ngay trên hồ sơ (vd nhãn đang để dòng chữ độc quyền).

### 4.8 Quy tắc chất lượng gắn với sản phẩm

**(a) Khung sai số hàm lượng hoạt chất** (sheet *QUY TẮC*, dẫn quy định Nhà nước về hàm lượng hoạt chất trong thuốc BVTV thành phẩm):

| Hàm lượng đăng ký (% khối lượng) | Tương đương g/kg hoặc g/l ở 20 ± 2 °C | Mức sai lệch cho phép |
|---|---|---|
| Đến 2,5 | đến 25 | ±15% hàm lượng đăng ký với dạng đồng nhất (lỏng); ±25% với dạng không đồng nhất (rắn) |
| Trên 2,5 đến 10 | trên 25 đến 100 | ±10% hàm lượng đăng ký |
| Trên 10 đến 25 | trên 100 đến 250 | ±6% hàm lượng đăng ký |
| Trên 25 đến 50 | trên 250 đến 500 | ±5% hàm lượng đăng ký |
| Trên 50 | — | ±2,5% |
| — | trên 500 | ±25 g/kg hoặc g/l |

Quy định nội bộ ghi cạnh bảng định mức: hàm lượng yêu cầu sản xuất **chỉ được lệch tối đa 50% của ngưỡng sai số cho phép**.

**(b) Khung sai số chiết rót** (dẫn Thông tư về đo lường hàng đóng gói sẵn) và thể tích chốt đóng:

| Thể tích trên nhãn | Khung sai số cho phép | Thể tích dự kiến chốt đóng | % thiếu dự kiến |
|---|---|---|---|
| 100 ml | 4,5% | 97 ml | 3,0% |
| 200 ml | 4,5% | 195 ml | 2,5% |
| 220 ml | khoảng 4,1% (9 ml) | 215 ml | 2,3% |
| 240 ml | khoảng 4,1% (9 ml) | 234 ml | 2,5% |
| 400 ml | 3% | 390 ml | 2,5% |
| 450 ml | 3% | 440 ml | 2,2% |
| 900 ml | khoảng 1,7% (15 ml) | 891 ml | 1,0% |
| 20 lít | 1% | 19.840 ml | 0,8% |

Sổ còn có *Danh sách sản phẩm đang đóng tối ưu thể tích*: sản phẩm, NCC áp dụng, thông tin Sản xuất chốt với NCC (vd *97,5% theo thể tích chai*), thông tin Kinh doanh nắm, ghi chú (vd NCC đang đóng đủ 450 ml thì phần chênh đưa vào chi phí Kinh doanh).

**(c) Xác định ngày sản xuất của BTP**: NCC cung cấp NSX của BTP thì lấy theo NCC; NCC không cung cấp thì lấy NSX của BTP theo NSX của nguyên liệu và báo NCC đóng NSX theo yêu cầu của DEGO. Ngày sản xuất trên bao bì nguyên liệu phải trước hoặc bằng ngày nhận hóa đơn nguyên liệu.

---

## 5. Quy trình hiện tại

### 5.1 Khai báo mã mới

| Bước | Ai làm | Việc | Sheet / công cụ |
|---|---|---|---|
| 1 | Bộ phận phát sinh (theo bảng 3.1) | Xác định cần mã mới: NL mới hoặc đổi hàm lượng; BTP mới hoặc đổi dạng / dòng V / màu; VTBB mới hoặc đổi chất liệu / kích thước / màu; HH mới hoặc đổi BĐM, VTBB. | Zalo nhóm theo loại mã |
| 2 | Người khai báo | Kiểm trùng với danh mục. Trùng thì dừng và phản hồi. | Sổ *DATA DỮ LIỆU ĐẦU VÀO SX* |
| 3 | Người khai báo | Lập mã và tên theo quy tắc 4.1 vào *Mẫu khai báo*. | *Data QLDL* (BTPCT, PĐG, PPT), *KHAI BÁO VTBB*, *Data NL/BTP* |
| 4 | Quản lý thu mua hoặc QLSX | Duyệt. | — |
| 5 | Người khai báo | Gửi mẫu khai báo đã duyệt vào nhóm với P TCKT. | Zalo *SX & P TCKT* |
| 6 | P TCKT | Tạo mã trên Misa, phản hồi. | Misa |
| 7 | Người khai báo | Kéo mã, tên, ĐVT từ Misa về danh mục, bổ sung thuộc tính (hình, kích thước, NCC tham khảo...). Báo nhóm nội bộ. | Sổ danh mục |

- **Đầu vào**: thông tin kỹ thuật của mã (xem trường ở mục 9). Với HH: tên thương hiệu, khách hàng, nhãn hiệu, quy cách sản phẩm, quy cách thùng. Với BTPM: tên pháp lý, thành phần, hàm lượng, ĐVT hàm lượng, dòng, dạng, màu.
- **Đầu ra**: mã có trên Misa và trên danh mục sản xuất, dùng được trên đơn hàng, phiếu kho, BĐM.
- **Quy định**: mỗi bộ phận tự cập nhật sheet mình quản lý và phải ghi lịch sử sửa đổi; dòng đầu mỗi sheet ghi nguồn từng cột (*Lấy từ Misa*, *Lấy từ thu mua*, *Nhập tay*, *Click chọn*, *Công thức*).

### 5.2 Đưa công thức mới và test mẫu

| Bước | Ai làm | Việc | Sheet |
|---|---|---|---|
| 1 | ĐP NL/BTP | Ghi yêu cầu công thức mới: ngày, NCC, tên pháp lý, thành phần. | *2. Theo dõi công thức mới* |
| 2 | Lab | Chuẩn bị nguyên liệu, phối mẫu, lưu mẫu đối chứng. | — |
| 3 | QLSX | Duyệt hoặc không duyệt công thức; không duyệt thì Lab điều chỉnh và phối lại. Với NCC mới: phối lại **tối đa 2 lần**. | cột *Tiến độ xử lý* (nhật ký theo ngày) |
| 4 | ĐP NL/BTP | Gửi mẫu hoặc gửi nguyên liệu cho NCC phối thử; yêu cầu NCC **lưu mẫu đối chứng tối thiểu 2 năm**. | — |
| 5 | Lab | Test ngoại dạng (1-2 ngày) và hàm lượng (đến 14 ngày; có trường hợp chạy gia tốc 14 ngày rồi test lại). | *2.1 Theo dõi test mẫu* |
| 6 | ĐP NL/BTP | Ghi kết quả: hàm lượng test, chênh lệch so với giấy đăng ký, tỷ lệ chênh, sai số cho phép, Đạt / Không đạt; kết quả ngoại dạng. | *2.1 Theo dõi test mẫu* |
| 7 | QLSX, NCC | Mẫu đạt và NCC thống nhất thì **chốt công thức với NCC**: ngày chốt, mã công thức, mã BĐM. | *2. Theo dõi công thức mới* (khối *Công thức chốt với NCC*) |
| 8 | ĐP NL/BTP | Cập nhật *Danh sách và dòng công thức BTP*; khai mã BTP nếu chưa có; lập BĐM BTP; báo QLDL lấy giá phối. | *1.1 DS và dòng công thức BTP*, *3. BDM BTP* |

- **Đầu vào**: yêu cầu của KD hoặc QLSX, giấy đăng ký (hàm lượng), nguyên liệu mẫu.
- **Đầu ra**: công thức chốt, mã công thức Lab, mã BTP, dòng công thức KD - NCC, BĐM BTP.
- **Quy định**: test cả ngoại dạng và hàm lượng với BTP mua và hàng mang tên NCC GC; BTP tự phối test hàm lượng định kỳ; mỗi lần lấy 2-4 mẫu, lưu mẫu đối chiếu.

### 5.3 Lập BĐM BTP

| Bước | Ai làm | Việc |
|---|---|---|
| 1 | ĐP NL/BTP | Nhận yêu cầu / đơn từ ĐP TP (hoặc yêu cầu phối BTP). Mua thành phẩm trọn gói từ NCC thì **bỏ qua**, không lập BĐM. |
| 2 | ĐP NL/BTP + Pháp lý | Xác định luồng pháp lý: đơn vị cấu thành, đơn vị chuẩn bị nguyên liệu. |
| 3 | ĐP NL/BTP | Tra BĐM cũ theo tên pháp lý + dòng V + màu. Có rồi và không đổi gì thì dùng lại. |
| 4 | ĐP NL/BTP + Lab | Lập BĐM: mỗi hoạt chất một dòng, điền hàm lượng sản phẩm, hàm lượng yêu cầu sản xuất, sai số phối chế, mã NL, hàm lượng trên nhãn NL, hàm lượng thực tế NL, tỷ trọng (nếu có). Lượng NL trên 1.000 kg tự tính. |
| 5 | Hệ thống (công thức sheet) | Kiểm *Trong khung cho phép* hay *Sai số vượt quy định*. |
| 6 | QLSX | Duyệt: người duyệt, ngày duyệt. In trình ký. |
| 7 | ĐP NL/BTP | Gửi mã BĐM BTP cho QLDL để gộp BĐM TP; với công ty cấu thành thì lập thêm BĐM BTP thuế. |

- **Sheet**: *3. BDM BTP* (chi tiết trên 1.000 kg), *3.1 Tính lượng NL và giá BTP (tạm duyệt mua)*, *3.2 Khảo sát giá NL/BTP*.
- **Đầu ra**: mã BĐM BTP đã duyệt; từ đó tính lượng NL cần mua, giá BTP tạm, lệnh sản xuất BTP.
- **Quy định**: nhóm phân bón sản xuất tại nhà máy riêng thì theo dòng công thức KD + dữ liệu Lab và lập lệnh sản xuất theo số lượng đơn; nhóm thuốc BVTV thì Lab thống nhất công thức, QLSX làm với NCC phối mẫu, test đạt mới chốt.

### 5.4 Lập BĐM VTBB

| Bước | Ai làm | Việc |
|---|---|---|
| 1 | Thiết kế | Khi làm mockup và khai mã HH: gắn mã VTBB vào mockup. KD bảo đảm bao bì phù hợp ruột (sức chứa, dạng chứa, tương thích) theo tư vấn của Sản xuất. |
| 2 | ĐP VTBB | Khai mã VTBB mới nếu chưa có (theo 5.1). |
| 3 | ĐP VTBB + Pháp lý | Xác định bên chuẩn bị từng vật tư (DEGO / thương hiệu mang sang, hay NCC tự chuẩn bị), nơi sản xuất, công ty cấu thành. |
| 4 | ĐP VTBB | Tra BĐM cũ; lập mới khi khác quy cách hoặc đổi chất liệu. Mỗi vật tư một dòng: nhóm, mã, tên, ĐVT, định mức trên 1 thành phẩm. |
| 5 | QLSX | Duyệt (người duyệt, ngày duyệt); in *Phiếu BĐM VTBB thành phẩm* trình ký. |
| 6 | ĐP VTBB | Gửi mã BĐM VTBB cho QLDL. Thay vật tư trong sản xuất thì lập BĐM mới gửi QLDL. |

- **Sheet**: *BDM VTBB* (đầu vào: ngày cập nhật, mã đơn đặt hàng đại diện, mã BĐM, mã HH; tự chạy: tên HH, tên pháp lý, ĐVT thành phẩm), *9. Phiếu BDM VTBB TP* (mẫu in ký duyệt).
- **Quy định**: chú ý **tên VTBB trên hóa đơn** và các VTBB **không lấy được hóa đơn**; với một số NCC, ĐP VTBB chỉ báo số lượng cần in, Thiết kế tự làm với NCC.

### 5.5 Lập BĐM thành phẩm

| Bước | Ai làm | Việc |
|---|---|---|
| 1 | QLDL | Nhận yêu cầu khi có đơn mới hoặc đơn dùng tổ hợp vật tư chưa có BĐM. |
| 2 | QLDL + Pháp lý | Xác định luồng pháp lý và hạng mục: mã BTP ruột, loại và lượng VTBB, phí sang chai đóng gói. |
| 3 | QLDL | Nhận mã BĐM BTP (từ ĐP NL/BTP) và mã BĐM VTBB (từ ĐP VTBB); đối chiếu với luồng pháp lý. |
| 4 | QLDL | Tra BĐM TP cũ theo tên pháp lý + quy cách. Chưa có thì lập: đầu phiếu lấy từ hồ sơ HH, dòng chi tiết bung từ BĐM VTBB + thêm dòng BTP ruột + dòng phí gia công; mỗi dòng ghi bên cung ứng CTY hay NCC. |
| 5 | QLDL | Lập cả bộ **nội bộ** và bộ **thuế** (cột riêng cho mã BĐM VTBB, mã BTP ruột, mã BĐM TP của từng bộ). |
| 6 | QLSX | Duyệt BĐM (*Duyệt BĐM* = chọn, *Ngày duyệt* = nhập). |
| 7 | QLDL | Gửi bản gốc cho P TCKT, lưu bản scan. BĐM dùng cho lệnh sản xuất thành phẩm, phiếu xuất kho sản xuất, giá vốn. |

- **Sheet**: *4. BDM thành phẩm › BDM TP* (bản giống hệt nằm ở *1. ĐẦU VÀO GIÁ VỐN › BDM TP*), *LSX TP*, *Phiếu in LSX*, *Tổng hợp LSX TP*.
- **Quy định**: phân biệt sản phẩm dạng chai, dạng túi / gói, dạng xô / can; phân biệt *chuẩn bị toàn bộ* với *chuẩn bị một phần*.

### 5.6 Lập BĐM thuế

| Bước | Ai làm | Việc |
|---|---|---|
| 1 | ĐP NL/BTP, ĐP VTBB | Đối chiếu tên pháp lý + công ty cấu thành với *Danh sách quản lý BĐM thuế*. Có rồi thì dùng lại. |
| 2 | Pháp lý | Xác nhận đơn vị cấu thành và công ty nhận hóa đơn. **NCC cấu thành thì DEGO không khai mã, không làm BĐM thuế** (BĐM do NCC lo). Công ty nội bộ cấu thành hoặc chuẩn bị một phần thì phải làm. |
| 3 | ĐP NL/BTP, ĐP VTBB, QLDL | Lập BĐM BTP thuế, BĐM VTBB thuế, BĐM TP thuế theo mã và tên trên hóa đơn của công ty cấu thành. |
| 4 | QLSX, kế toán trưởng | Ký phiếu BĐM (các ô ký: kế toán trưởng, duyệt bao bì, duyệt pháp lý, duyệt giá). |
| 5 | QLDL | Gửi bản gốc cho P TCKT của đúng công ty (mỗi công ty nội bộ một bộ BĐM thuế). |

- **Thời điểm**: trước khi đưa vào sản xuất; xác định trước để khảo sát và tính giá vốn.
- **Quy định**: phiếu xuất BTP / VTBB phải lập **trước hoặc cùng ngày** lệnh sản xuất; phần thuế của hao hụt chưa thống nhất xong giữa Kế toán và Sản xuất.

### 5.7 Khảo sát VTBB (và NL / BTP) phù hợp công nghệ NCC GC

| Bước | Ai làm | Việc |
|---|---|---|
| 1 | KD | Gửi yêu cầu khảo sát (mã yêu cầu dạng thương hiệu + `YCKSCN` + ngày + số): VTBB nào, ruột nào, NCC nào, cần trả lời vấn đề gì. Đơn chưa khảo sát thì ĐP yêu cầu KD lập. |
| 2 | ĐP VTBB (ĐP NL/BTP) | Kiểm hiện trạng VTBB và BTP: sẵn kho, đang luân chuyển, phải mua; nguồn BTP (điều chuyển / mua mới / sẵn kho) kèm ngày có hàng. |
| 3 | ĐP VTBB | Gửi mẫu cho NCC: **11 bộ** với một NCC, **4-5 bộ** với các NCC khác; ghi người phụ trách hai bên, yêu cầu NCC trả kết quả gì, kênh liên hệ. |
| 4 | NCC GC | Chạy thử, trả kết quả trong **10-14 ngày**. |
| 5 | ĐP VTBB | Ghi tiến độ, kết quả (*Phù hợp - Đạt* / *Không phù hợp - Cần điều chỉnh*). |
| 6 | QLSX | Đánh giá, duyệt. |
| 7 | ĐP VTBB | Phản hồi KD (ngày, hình thức). |

- **Sheet**: *KHẢO SÁT CÔNG NGHỆ VTBB*; liên quan *PYC KHẢO SÁT VTBB* và *TRẢ KQ KHẢO SÁT VTBB* (khảo sát giá, dùng chung cho VTBB / NL / BTP).
- **Quy định**: **Nhóm 1 bắt buộc qua Sản xuất**: chai, nhãn, túi, thùng, nhãn dán thùng, can, xô, túi PE; **Nhóm 2** (còn lại) không cần; nhà máy riêng không cần.

### 5.8 Cọc nhãn

| Bước | Ai làm | Việc |
|---|---|---|
| 1 | QLSX | Cấp danh sách NCC có chính sách cọc nhãn (sổ ghi An Nông, Âu Việt, Đại Tâm; quy trình ghi thêm Thu Loan). |
| 2 | NCC GC | Duyệt nhãn, báo số tiền cọc cho QLDL. |
| 3 | ĐP VTBB, KD | Tổng hợp; KD chốt sản phẩm, sản lượng dự kiến, số tiền. |
| 4 | QLDL | Làm hợp đồng / phụ lục cọc nhãn, khai báo, chuyển cọc. |
| 5 | ĐP VTBB | Theo dõi sản lượng và điều kiện hoàn cọc theo hợp đồng; theo dõi tồn nhãn. |
| 6 | KD, ĐP VTBB | Đủ điều kiện hoặc KD ngưng sản xuất thì báo QLDL thanh lý. |
| 7 | QLDL | Hoàn cọc: số tiền hoàn, hình thức (vd cấn trừ công nợ), văn bản thanh lý, chứng từ. |

- **Sheet**: *CỌC NHÃN VTBB*. **Đầu ra**: sổ cọc theo mã HH + mã nhãn, tình trạng hoàn cọc.

### 5.9 Mẫu cho tặng

| Bước | Ai làm | Việc |
|---|---|---|
| 1 | ĐP VTBB (ĐP NL/BTP) | Tiếp nhận: ngày, bộ phận yêu cầu, mục đích, đơn vị cho tặng. |
| 2 | ĐP VTBB | Ghi thông số: mã và tên VTBB **phía NCC đặt**, chất liệu, hình dạng, thông số kỹ thuật, màu, ĐVT, số lượng, lưu ý. |
| 3 | ĐP VTBB | Nhận mẫu: thời gian, hình thức (tự lấy / gửi), người phụ trách. |
| 4 | QLSX | Giao việc cần làm với mẫu: **Test, Chụp, Lưu, Gửi** (mỗi việc: chưa làm / đã làm / không cần). |
| 5 | ĐP VTBB | Ghi tiến độ, kết quả trả cho bộ phận yêu cầu, trạng thái, đánh giá lợi ích (vd *có thể thay thế mã THC...*), link hình và kết quả test. |

- **Sheet**: *MẪU CHO TẶNG VTBB*. **Quy định**: mẫu **không dùng cho sản xuất, không xuất chi phí, không quản lý tồn thực**; chỉ lưu để tham khảo và đề xuất phương án.

---

## 6. Danh sách tính năng

Cột *ERP đã có*: **Có** = dùng được ngay; **Một phần** = có nền nhưng thiếu trường / thiếu luồng; **Chưa** = chưa có gì. Tên trong backtick là bảng, module hoặc đường dẫn màn trên nhánh `erp-v2`. Cụm *Giá nguyên vật liệu sản xuất* (module `packaging_cost`, `product_price`) hiện **mới có trên dev**, chưa lên prod.

### 6.1 Nhóm A — Danh mục mã hàng

| Mã | Tính năng | Mô tả ngắn | Quy trình / sheet nguồn | ERP đã có | Ưu tiên |
|---|---|---|---|---|---|
| SX-SP-01 | Danh mục mã hàng theo loại mã | Một danh mục cho NL, BTP, VTBB, TP, phí; mỗi mã có **loại mã** (NLNK, NLT, NA, BTPR, BTPM, BTPNK, BTPCT, VTBB, HH, PPT, PĐG, CPNK) để lọc và áp quy tắc. | QT2; Data NL/BTP, Data VTBB, Data HH, Data QLDL | **Một phần** — `tab_product` (mã, tên, tên hóa đơn, tên pháp lý, phân loại, ĐVT, mã HH, thông số, đang dùng), màn `/production/products`. Chưa có cột loại mã. | Cao — nền cho mọi tính năng sau |
| SX-SP-02 | Thuộc tính nguyên liệu | Hàm lượng, ĐVT hàm lượng, dạng NL, màu chuẩn, hoạt chất, số CAS, xuất xứ, phân loại. | Data 1 (khối Mã NL); Data thu mua (tiêu chuẩn NL) | **Chưa** — chỉ có ô `specs` dạng chữ. Thiết kế *thuộc tính theo phân loại* (CN-MH-09) đã duyệt, chưa làm. | Cao — BĐM BTP cần hàm lượng NL |
| SX-SP-03 | Thuộc tính BTP | Tên pháp lý, thành phần, dòng V, màu, dạng ruột, độ trong, tỷ trọng, mã công thức Lab, nhóm (thuốc / phân). | Data NL/BTP; 3. BDM BTP; 1.1 DS dòng công thức | **Chưa** — `legal_name` có, còn lại chưa. | Cao |
| SX-SP-04 | Thuộc tính VTBB theo phân loại | Ba khối: chai / nắp / xô / can (chất liệu, hình dạng, cao x đường kính, trọng lượng, cổ chai, màu, nhận diện riêng, kích thước nhãn phù hợp); túi / nhãn / bao (chất liệu, thương hiệu, kích thước nhãn gồm mép dán, NCC GC nhận vật tư, mã HH, tên pháp lý, thể tích); thùng / hộp (quy cách sản phẩm, thương hiệu, kích thước phủ bì, **kích thước lọt lòng**, trọng lượng, số lớp, cán màng, màu chính). | KHAI BÁO VTBB; DATA 2 | **Chưa** — đã có bản phân tích `doc/erp/mat-hang/tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md` (bốn bảng `tab_attribute...`), chưa làm. | Trung bình — tra cứu và ghép nắp - chai, chai - thùng |
| SX-SP-05 | Hồ sơ thành phẩm (HH) | Mỗi mã HH: thương hiệu, khách hàng, công ty phân phối, công ty xuất hóa đơn đầu ra, công ty nhận hóa đơn đầu vào, NCC sản xuất, dòng sản phẩm, tên pháp lý, mô tả ruột, tên nhãn hiệu, quy cách SP, quy cách thùng, quy cách hộp / bao, ĐVT chính, đơn vị thể tích (g / ml), thể tích trên nhãn. | QUẢN LÝ NHÃN MÁC; BDM TP (đầu phiếu) | **Một phần** — `tab_product.hh_code`, `hh_name`, `legal_name` (gắn trên dòng vật tư); `tab_packaging_bom` giữ `fg_code`, `fg_name`, `legal_name`, `carton_qty`. Chưa có hồ sơ HH riêng (họ sản phẩm CN-MH-17 dự kiến). | Cao — đầu phiếu của mọi BĐM |
| SX-SP-06 | Danh mục dùng chung cho thuộc tính | ĐVT; màu (kèm mã 2 ký tự); hình dạng VTBB; dạng NL / BTP (viên, cốm, bột, gel, lỏng); dạng theo quy định (WP, WG, SL, EC, SC...) kèm tên đầy đủ; độ trong; phân loại sản phẩm; dòng V; danh mục hoạt chất + số CAS. | Data 1 (Admin - thuộc tính) | **Một phần** — `tab_unit` (`/production/units`), `tab_item_group` (`/production/item-groups`), `tab_brand`. Các danh mục còn lại chưa có. | Trung bình |
| SX-SP-07 | Mã chi phí gia công như mặt hàng phi kho | PPT, PĐG, CPNK là mã có tên, ĐVT, NCC, nhưng không nhập kho. | QT2; Data QLDL; Phí phối NCC GC, Phí đóng gói NCC GC | **Chưa** — cờ loại hàng `item_type` (CN-MH-12) mới ở dự kiến. | Trung bình — cần cho dòng phí trong BĐM TP |
| SX-SP-08 | Hình ảnh và mockup của mã | Ảnh vật tư, ảnh nhãn, mockup có gắn mã VTBB. | KHAI BÁO VTBB (link hình); QUẢN LÝ NHÃN MÁC | **Một phần** — sản phẩm đã có nhiều ảnh và ảnh đại diện (CN-MH-03). Chưa có khái niệm mockup gắn mã. | Thấp |
| SX-SP-09 | Ngưỡng tồn và MOQ theo mã + kho | Min tồn an toàn, MOQ, NCC phụ trách theo từng mã + kho; dùng cảnh báo cần đặt hàng. | THÔNG TIN (khối 1) | **Chưa** | Thấp — thuộc Kho, ghi ở đây vì là thuộc tính mã |

### 6.2 Nhóm B — Quy tắc

| Mã | Tính năng | Mô tả ngắn | Quy trình / sheet nguồn | ERP đã có | Ưu tiên |
|---|---|---|---|---|---|
| SX-SP-10 | Sinh mã tự động theo quy tắc | Chọn loại mã, hệ thống gợi ý mã kế tiếp theo tiền tố (và theo 4 số cuối mã HH với nhãn, NDT, hộp, BTPCT). | QT2 bước 3 | **Chưa** — mã gõ tay, chỉ chặn trùng. | Cao — giảm sai mã |
| SX-SP-11 | Sinh tên nội bộ và tên hóa đơn theo mẫu | Ghép tên từ thuộc tính theo mẫu từng loại. | QT2 bước 3; KHAI BÁO VTBB (cột *Công thức*) | **Một phần** — có trường `invoice_name`, chưa có mẫu ghép. | Trung bình |
| SX-SP-12 | Kiểm trùng khi khai báo | Cảnh báo khi thuộc tính trùng mã đã có (không chỉ trùng mã). | QT2 bước 2.1 | **Một phần** — chặn trùng `code`. | Trung bình |
| SX-SP-13 | Phiếu khai báo mã mới và duyệt | Phiếu khai báo có trạng thái (nháp, chờ duyệt, đã duyệt, đã có trên Misa), người duyệt theo loại mã, ngày gửi kế toán. | QT2 bước 2; Data QLDL (trạng thái khai báo) | **Chưa** — tạo sản phẩm là dùng ngay, không có bước duyệt. | Trung bình — phụ thuộc quyết định có giữ Misa làm gốc không |
| SX-SP-14 | Đồng bộ mã DEGO - mã NCC GC | Bảng cặp mã theo từng NCC; tự đổi mã khi nhập số liệu NCC gửi. | Data đồng bộ NCC GC; QT8, QT9 bước đối chiếu | **Chưa** — *mã hàng của NCC* `tab_product_supplier` (CN-MH-14) ở dự kiến. | Cao — điều kiện của đối chiếu tồn |
| SX-SP-15 | Bảng dòng công thức KD - NCC | Quy đổi dòng V + màu Kinh doanh gọi sang dòng V + màu NCC gọi, theo từng NCC. | 1.1 DS và dòng công thức BTP; QUY TẮC (*Đồng bộ dòng công thức*) | **Chưa** | Cao — tránh đóng sai công thức |
| SX-SP-16 | Quản lý nhãn mác | Tình trạng in nhãn, trạng thái NCC duyệt nhãn, ghi chú độc quyền, sáu mã bao bì gắn với HH. | QUẢN LÝ NHÃN MÁC | **Chưa** | Trung bình |
| SX-SP-17 | Bảo mật công thức và nguyên liệu mã hóa | Ai được xem công thức NCC, lượng NL trong BĐM BTP, tên thật của mã `NA`. | 1.1 (ghi *BẢO MẬT*); QT2 (mã NA) | **Một phần** — có phân quyền theo entity (vd `packaging_cost.read`); chưa có quyền theo trường. | Cao — yêu cầu bắt buộc trước khi nhập công thức |
| SX-SP-18 | Trạng thái vòng đời mã | Đang kinh doanh, chưa kinh doanh, ngưng sử dụng; dự kiến bỏ (vd BTPM năm 2027). | Data 1 (cột *Trạng thái* của tên pháp lý); QT2 | **Một phần** — `is_active` hai trạng thái. | Thấp |

### 6.3 Nhóm C — Công thức BTP

| Mã | Tính năng | Mô tả ngắn | Quy trình / sheet nguồn | ERP đã có | Ưu tiên |
|---|---|---|---|---|---|
| SX-SP-19 | Danh sách công thức / dòng công thức BTP | Mỗi dòng: tên pháp lý 1, tên pháp lý 2, dòng V áp dụng với KD, màu gốc, màu thực tế, có phụ gia, có pha màu, mô tả phụ gia / pha thêm, mã Lab, mã BTP, công thức áp dụng với NCC, ghi chú, ngày cập nhật. | 1.1 DS và dòng công thức BTP | **Chưa** | Cao |
| SX-SP-20 | Theo dõi công thức mới | Sổ yêu cầu công thức mới: NCC, tên pháp lý, thành phần, nhật ký tiến độ, kết quả, công thức chốt (ngày, mã công thức, mã BĐM). | 2. Theo dõi công thức mới | **Chưa** | Trung bình |
| SX-SP-21 | Theo dõi test mẫu | Phiếu test: mẫu, nguồn mẫu, từng hoạt chất, hàm lượng đăng ký, hàm lượng test, chênh lệch, sai số cho phép, kết quả; kết quả ngoại dạng. | 2.1 Theo dõi test mẫu | **Chưa** | Cao — căn cứ nhập kho và chốt công thức |
| SX-SP-22 | Bảng khung sai số hàm lượng | Danh mục khung sai số theo dải hàm lượng và dạng (lỏng / rắn); tự tra sai số cho phép. | QUY TẮC (*Sai số cho phép trong phối chế*) | **Chưa** | Trung bình |
| SX-SP-23 | Khung sai số chiết rót và thể tích chốt đóng | Theo thể tích trên nhãn: khung sai số, thể tích chốt đóng; theo sản phẩm + NCC: tỷ lệ đóng tối ưu đã chốt, thông tin KD nắm. | QUY TẮC (*Sai số cho phép trong chiết rót*, *Danh sách sản phẩm đang đóng tối ưu thể tích*) | **Chưa** | Trung bình — ảnh hưởng lượng BTP ruột trong BĐM TP |
| SX-SP-24 | Màu độc quyền theo khách hàng | Ghi màu dành riêng cho từng khách / nhóm khách của một sản phẩm; cảnh báo khi đơn chọn sai. | QUY TẮC (khối ghi chú màu); 1.1 (cột ghi chú) | **Chưa** | Thấp |

### 6.4 Nhóm D — Định mức / BOM

| Mã | Tính năng | Mô tả ngắn | Quy trình / sheet nguồn | ERP đã có | Ưu tiên |
|---|---|---|---|---|---|
| SX-SP-25 | BĐM BTP (đầu phiếu + dòng) | Định mức nguyên liệu trên 1.000 kg / lít BTP, mỗi hoạt chất một dòng. | 3. BDM BTP; QT7 khối A | **Chưa** | Cao |
| SX-SP-26 | Tính lượng NL theo hàm lượng và tỷ trọng | Tự tính lượng NL, tỷ lệ hàm lượng yêu cầu / hàm lượng sản phẩm, kiểm khung sai số. | 3. BDM BTP (cột Q, S, X) | **Chưa** | Cao |
| SX-SP-27 | Tính lượng NL cần mua và giá BTP tạm | Từ BĐM BTP + lượng BTP cần phối + giá NL từng NCC + phí phối ra giá BTP; trạng thái *Giá tham khảo* / *Duyệt mua*. | 3.1 Tính lượng NL và giá BTP; 3.2 Khảo sát giá NL/BTP | **Một phần** — sổ giá `tab_product_price_ledger`, báo giá `tab_product_price_quote` giữ giá theo mã + NCC; chưa có phép tính theo BĐM BTP. | Trung bình — phần giá thuộc Giá vốn |
| SX-SP-28 | BĐM VTBB | Định mức bao bì trên 1 thành phẩm theo mã HH. | BDM VTBB; QT7 khối B | **Một phần** — `tab_packaging_bom` + `tab_packaging_bom_part`, màn *Định mức bao bì* `/procurement/packaging-cost/boms`, nhập Excel. Mới 5 loại thành phần, mỗi loại 1 mã, định mức ngầm định. | Cao — mở rộng từ cái đã có |
| SX-SP-29 | Mở rộng loại thành phần và nhiều mã cùng loại | Thêm xô, can, lon, túi / gói, bao, hộp, cốc đong, seal, tem, màng co, túi PE, tag, tấm lót; cho phép hai nhãn, hai tem trên một sản phẩm. | BDM VTBB (cột *Nhóm*); BDM TP; QT7 khối B | **Một phần** — thêm loại = thêm thành viên `PackagingRole`; nhiều mã cùng loại bị chặn bởi ràng buộc duy nhất `(bom_id, part_type)`. | Cao |
| SX-SP-30 | Định mức số lượng trên từng dòng | Mỗi dòng có số lượng trên 1 thành phẩm (1; 1 / quy cách thùng; thể tích trên nhãn) và ĐVT. | BDM VTBB (cột *Định mức / thành phẩm*); BDM TP (cột *Chi tiết sử dụng / 1 TP*) | **Một phần** — không có cột số lượng; công thức cứng: chai, nắp, nhãn = 1; nhãn thùng, thùng = 1 / `carton_qty`. | Cao |
| SX-SP-31 | Bên cung ứng từng thành phần và cấu thành | Mỗi dòng ghi CTY hay NCC; đầu phiếu ghi cấu thành theo từng bên (thương hiệu / công ty nào mang gì). | BDM VTBB (cột *DEGO*, *NCC*); BDM TP (cột *Phân loại*, *Cấu thành*) | **Chưa** — ngầm định công ty mua hết. | Cao — quyết định xuất kho và giá vốn |
| SX-SP-32 | BĐM thành phẩm gộp | Một BĐM cho 1 thành phẩm gồm dòng BTP ruột + các dòng VTBB + dòng phí gia công; trỏ về BĐM BTP và BĐM VTBB nguồn. | BDM TP; QT7 khối C | **Chưa** | Cao |
| SX-SP-33 | Dòng phí gia công trong BĐM | Dòng *Phí sang chai đóng gói* (mã PĐG theo dải thể tích, số lượng 1 / TP), phí phối trộn theo ml / kg. | BDM TP; Phiếu in LSX (mục II. Chi phí) | **Chưa** | Trung bình |
| SX-SP-34 | Phiên bản BĐM | Số phiên bản, lý do thay đổi, đơn đầu tiên áp dụng, phiên bản hiện hành, không sửa đè bản đã duyệt. | BDM BTP (`_01`, `_02`); BDM VTBB (ghi chú thay đổi); BDM TP (mã đơn đầu tiên) | **Chưa** — `fg_code` duy nhất, một định mức mỗi mã HH; lịch sử chỉ xem qua nhật ký thao tác. | Cao |
| SX-SP-35 | Duyệt BĐM | Trạng thái nháp / chờ duyệt / đã duyệt / ngưng; người duyệt, ngày duyệt; phiếu ký nhiều ô (bao bì, pháp lý, giá, kế toán trưởng). | Cả ba sheet BĐM (cột *Người duyệt*, *Ngày duyệt*); 9. Phiếu BDM VTBB TP | **Chưa** — có vết người tạo / sửa (`AuditMixin`), không có bước duyệt. ERP có sẵn module `approval` dùng cho chứng từ khác. | Cao |
| SX-SP-36 | BĐM thuế và cấu thành thuế | Bộ định mức thứ hai theo từng công ty nội bộ, kèm luồng hóa đơn; liên kết với bộ nội bộ. | QT7; BDM TP (cột Z-AB); phiếu BĐM (*Số BĐM CCT BTP*, *Số BĐM CCT TP*, *Luồng hóa đơn*) | **Chưa** | Trung bình — cần phòng Sản xuất + Kế toán chốt định nghĩa trước |
| SX-SP-37 | In phiếu BĐM ký duyệt | Mẫu in *Bảng định mức VTBB thành phẩm* (và BĐM BTP, BĐM TP): đầu phiếu, bảng vật tư, luồng hóa đơn, ô ký. | 9. Phiếu BDM VTBB TP | **Chưa** — cụm giá NVL có trang in cho lịch sử giá và tác động giá, chưa có in định mức. | Trung bình |
| SX-SP-38 | Nhập và xuất Excel định mức | Nhập hàng loạt từ mẫu Excel, xem trước, xóa theo lô nhập. | Chuyển dữ liệu từ Sheets | **Có** (cho 5 loại bao bì) — `bom_import.py`, xóa theo lô `batch_purge_service.py`. Cần mở rộng cột khi BOM mở rộng. | Trung bình |
| SX-SP-39 | Tra ngược mã vật tư dùng ở sản phẩm nào | Chọn một mã VTBB / NL, xem các thành phẩm và BĐM đang dùng. | QT9 mục H (*sản phẩm áp dụng*, *lịch sử sử dụng theo BĐM*) | **Có** (bao bì) — màn *Tác động giá* `/procurement/packaging-cost`, chỉ mục `ix_pbom_part_code`. Chưa có cho NL → BTP → TP. | Trung bình |
| SX-SP-40 | Chi phí định mức của 1 thành phẩm | Cộng giá × định mức của mọi dòng do công ty cung ứng; tách phần NCC lo. | 1. ĐẦU VÀO GIÁ VỐN (BDM TP + giá nhập kho) | **Một phần** — `cost_service.py` tính chi phí bao bì / chai và / thùng theo 5 loại; màn *Giá theo sản phẩm* `/procurement/packaging-cost/products`. | Trung bình — phần mở rộng thuộc Giá vốn |
| SX-SP-41 | Cảnh báo dữ liệu định mức | HH chưa có BĐM duyệt; dòng thiếu mã; thiếu giá; thiếu quy cách thùng; lệch ĐVT; cùng một mã dùng cho hai loại (vd nhãn chính làm nhãn thùng); BĐM dùng mã đã ngưng. | Lỗi thấy trong dữ liệu mẫu | **Một phần** — `CostWarning`: thiếu giá chai, thiếu mã thành phần, thiếu giá thành phần, thiếu quy cách thùng; cảnh báo lệch ĐVT ở sổ giá. | Trung bình |
| SX-SP-42 | Bung BĐM cho lệnh sản xuất và xuất kho | Từ mã BĐM TP + số lượng thành phẩm ra danh sách NVL, VTBB, phí theo bên cung ứng. | LSX TP; Phiếu in LSX; XK SX BTP; XK SX VTBB | **Chưa** | Cao — nhưng thuộc phần Đơn hàng gia công và Kho; ở đây chỉ cấp hàm bung |

### 6.5 Nhóm E — Tiêu chí đánh giá, khảo sát, sổ phụ

| Mã | Tính năng | Mô tả ngắn | Quy trình / sheet nguồn | ERP đã có | Ưu tiên |
|---|---|---|---|---|---|
| SX-SP-43 | Tiêu chuẩn nguyên liệu | Theo mã NL: xuất xứ, ngoại quan, màu, độ tan, độ trong, độ ẩm, pH, hàm lượng, số CAS, thuộc phụ lục nghị định. | Data thu mua (tiêu chuẩn NL, Lab cấp) | **Chưa** | Trung bình |
| SX-SP-44 | Phiếu yêu cầu test Lab và kết quả | Yêu cầu test cho mẫu công thức, lô nhập, hàng tồn; kết quả ngoại dạng và hàm lượng; hạn trả kết quả. | QT8 mục E; 2.1 Theo dõi test mẫu | **Chưa** | Cao (gộp chung luồng với SX-SP-21) |
| SX-SP-45 | Sổ lưu mẫu đối chứng | Mẫu lưu tại Lab và tại NCC: sản phẩm, lô, ngày lưu, hạn lưu (NCC tối thiểu 2 năm), kỳ đối chiếu 6 tháng. | QT1 bước 5; checklist hợp đồng | **Chưa** | Thấp |
| SX-SP-46 | Tiêu chí KCS thành phẩm theo sản phẩm | Bộ tiêu chí kiểm khi nhận hàng: ngoại dạng, màu, trọng lượng, thể tích, phụ kiện đi kèm, số lô, NSX, HSD, chứng từ. | Điều phối TP (kết quả Lab, KCS kho) | **Một phần** — nhận hàng có `qc_result`; NCC có `inspection_days`, `return_days`. Chưa có bộ tiêu chí theo sản phẩm. | Trung bình — thực hiện ở phần Kho / Đơn hàng |
| SX-SP-47 | Khảo sát VTBB / NL / BTP phù hợp công nghệ NCC | Sổ khảo sát theo mã VTBB + ruột + NCC: hiện trạng, số mẫu gửi, hạn 10-14 ngày, kết quả, đánh giá QLSX, phản hồi KD. | KHẢO SÁT CÔNG NGHỆ VTBB; QT8 mục H; QT9 mục I | **Chưa** — ERP có *Yêu cầu khảo sát* (`survey_request`) cho khảo sát **giá**, không phải khảo sát công nghệ. | Trung bình |
| SX-SP-48 | Ma trận phù hợp VTBB - ruột - NCC | Kết quả khảo sát đạt trở thành dữ liệu tra: NCC nào đóng được vật tư nào với ruột nào. | KHẢO SÁT CÔNG NGHỆ VTBB (kết quả); QT9 mục H (*công nghệ theo NCC*) | **Chưa** | Thấp |
| SX-SP-49 | Cọc nhãn | Sổ cọc theo NCC + mã HH + mã nhãn: số lượng, tiền cọc, hợp đồng, điều kiện hoàn, theo dõi, hoàn cọc. | CỌC NHÃN VTBB; QT9 mục D | **Chưa** — `tab_contract` giữ được hợp đồng cọc, không có sổ cọc. | Trung bình |
| SX-SP-50 | Mẫu cho tặng | Sổ mẫu được cho / tặng: đơn vị cho, thông số, việc cần làm (test, chụp, lưu, gửi), kết quả, đánh giá. | MẪU CHO TẶNG VTBB; QT8 mục I; QT9 mục J | **Chưa** | Thấp |
| SX-SP-51 | Chính sách theo sản phẩm tại NCC | % hao hụt cho phép theo NCC + nhóm vật tư; nhận dự trù BTP hay không; MOQ phối BTP; thể tích đóng tối ưu. | THÔNG TIN (khối 2); Data NCC GC | **Chưa** | Trung bình — chủ yếu thuộc phần NCC GC, ở đây chỉ nêu phần gắn mã hàng |
| SX-SP-52 | Báo cáo dữ liệu VTBB cho Kinh doanh | Mã, tên, hình, giá, sản phẩm áp dụng, giá thấp nhất / cao nhất 5 lần mua gần nhất, công nghệ theo NCC. | QT9 mục H | **Một phần** — màn *Giá mua gần nhất* `/procurement/packaging-cost/last-prices`, *Lịch sử giá* `/history`, *Bảng giá VTBB* `/prices`. Thiếu hình, công nghệ. | Thấp |
| SX-SP-53 | Lịch sử thay đổi mã hàng và định mức | Ai sửa gì, khi nào, lý do. | Quy định *ghi lịch sử sửa đổi* ở Mục lục các Drive | **Một phần** — nhật ký thao tác chung (`audit`, `change_log`). | Thấp |
| SX-SP-54 | Chuyển dữ liệu ban đầu từ Google Sheets | Nhập danh mục VTBB, hồ sơ HH, công thức, BĐM hiện có vào ERP một lần, có đối soát. | Toàn bộ sheet nguồn | **Một phần** — nhập CSV sản phẩm (CN-MH-02), nhập Excel định mức bao bì. | Cao — không có thì không ai dùng |

Tổng cộng **54 tính năng**: 9 (A) + 9 (B) + 6 (C) + 18 (D) + 12 (E).

---

## 7. Chi tiết từng tính năng

Quy ước: *Đầu vào* là thứ người dùng nhập hoặc hệ thống lấy từ chỗ khác; *Đầu ra* là thứ tính năng tạo ra cho người hoặc cho tính năng khác.

### 7.1 Nhóm A — Danh mục mã hàng

**SX-SP-01 Danh mục mã hàng theo loại mã**
- Đầu vào: mã, tên, loại mã, phân loại (nhóm hàng), ĐVT, tên hóa đơn, tên pháp lý, đang dùng.
- Đầu ra: danh mục dùng chung cho đơn hàng, kho, BĐM, giá.
- Quy tắc: loại mã suy được từ tiền tố nhưng nên là một trường chọn để không phụ thuộc cách gõ; loại mã quyết định bộ thuộc tính hiện trên form và mẫu sinh mã, sinh tên.
- Trường chính: `code`, `name`, loại mã, `item_group`, `unit`, `invoice_name`, `legal_name`, `is_active`.
- Ràng buộc: mã là duy nhất, **không đổi, không tái dùng** (luật bất biến đã có của `tab_product`: mã nối bảy bảng chứng từ).
- Liên kết: mọi tính năng khác; Thu mua (YCMH, ĐMH chọn mã); Kho.

**SX-SP-02 Thuộc tính nguyên liệu**
- Đầu vào: hàm lượng (số + ĐVT: %, g/l, g/kg), dạng NL, màu chuẩn, hoạt chất (chọn từ danh mục), số CAS (tự hiện theo hoạt chất), xuất xứ, phân loại (thuốc / phân), cờ mã hóa.
- Đầu ra: hàm lượng trên nhãn NL để BĐM BTP tự lấy; số CAS cho phiếu nhập kho.
- Quy tắc: hàm lượng **thực tế** theo lô không nằm ở danh mục mà nằm ở lô nhập / kết quả test (SX-SP-21); danh mục chỉ giữ hàm lượng danh nghĩa.
- Ràng buộc: đổi hàm lượng danh nghĩa là mã mới.
- Liên kết: SX-SP-25, SX-SP-43, Kho (lô, NSX, HSD).

**SX-SP-03 Thuộc tính BTP**
- Đầu vào: nhóm (thuốc BVTV / phân bón), tên pháp lý (chọn từ danh mục pháp lý), thành phần đăng ký, dòng V, màu, dạng ruột, dạng theo quy định (EC, SC, WP...), độ trong, tỷ trọng sau phối, mã công thức Lab.
- Đầu ra: tên BTP sinh tự động; dữ liệu cho BĐM BTP và BĐM TP (mã SP gốc = dòng V + màu).
- Quy tắc: một tên pháp lý có nhiều mã BTP (mỗi tổ hợp dòng V + màu + dạng một mã); hai tên pháp lý có thể chung một mã BTP.
- Ràng buộc: tổ hợp (tên pháp lý, dòng V, màu, dạng, loại mã) không trùng.
- Liên kết: Pháp lý (tên pháp lý, hạn giấy), SX-SP-19, SX-SP-25.

**SX-SP-04 Thuộc tính VTBB theo phân loại**
- Đầu vào theo khối: (1) chai, nắp, xô, can, cốc: chất liệu (PET, HDPE, PP...), hình dạng, kích thước cao x đường kính, trọng lượng (g), cổ chai, màu, nhận diện riêng (logo, garanti), kích thước nhãn phù hợp, NCC tham khảo; (2) túi, nhãn, bao, NDT: chất liệu, thương hiệu / khách hàng, kích thước nhãn gồm mép dán, NCC GC nhận vật tư, mã HH, tên pháp lý, thể tích / trọng lượng; (3) thùng, hộp: quy cách sản phẩm tham khảo, thương hiệu, kích thước phủ bì, kích thước lọt lòng, trọng lượng, số lớp, cán màng, màu chính.
- Đầu ra: tên viết tắt và tên hóa đơn sinh tự động; bộ lọc tìm vật tư thay thế (cùng cổ chai, cùng thể tích).
- Quy tắc: **cổ chai** là thuộc tính chung của chai, nắp, cốc đong để kiểm ghép; **kích thước lọt lòng** của thùng phải chứa vừa số chai theo quy cách thùng (sổ ghi cần làm lại với Thiết kế để lấy số này).
- Liên kết: thiết kế kỹ thuật đã có ở `doc/erp/mat-hang/tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md`; SX-SP-28, SX-SP-47.

**SX-SP-05 Hồ sơ thành phẩm (HH)**
- Đầu vào: mã HH, thương hiệu, khách hàng, công ty phân phối, công ty xuất hóa đơn đầu ra, công ty nhận hóa đơn đầu vào, NCC sản xuất mặc định, dòng sản phẩm, tên pháp lý, tên nhãn hiệu, mô tả ruột (màu / dạng), quy cách sản phẩm (số + đơn vị g / ml), ĐVT chính (chai, gói, xô, can, lon, bao), quy cách thùng, quy cách hộp, quy cách bao, lưu ý.
- Đầu ra: tên HH ghép tự động; tên hóa đơn; đầu phiếu cho BĐM VTBB và BĐM TP; mã đơn vị xuất hóa đơn (I..IX) suy từ công ty.
- Quy tắc: `Tên HH = thương hiệu - mã đơn vị - số mã hàng - khách hàng - nhãn hiệu (mô tả ruột) - quy cách SP - quy cách thùng`.
- Ràng buộc: quy cách thùng > 0 khi sản phẩm có thùng; đổi quy cách sản phẩm là mã HH mới.
- Liên kết: SX-SP-16, SX-SP-28, SX-SP-32; Đơn hàng gia công; Pháp lý. Trên ERP, `fg_code` / `fg_name` / `legal_name` / `carton_qty` của `tab_packaging_bom` nên chuyển về hồ sơ HH để BĐM chỉ trỏ tới.

**SX-SP-06 Danh mục dùng chung cho thuộc tính**
- Đầu vào: giá trị từng danh mục, mã viết tắt (màu 2 ký tự), đang dùng.
- Quy tắc: danh mục do quản trị giữ; ô chọn trên form lấy từ đây, không gõ tự do (sổ hiện bị lệch do gõ: *Có*, *có*, *x*, *X*).
- Liên kết: SX-SP-02..05, SX-SP-10 (mã màu trong mã BĐM BTP).

**SX-SP-07 Mã chi phí gia công**
- Đầu vào: loại (PPT, PĐG, CPNK), NCC GC, với PĐG: loại VTBB + dải thể tích theo bảng giá NCC; với PPT: thuốc / phân, tên pháp lý, dòng V, màu; ĐVT tính phí (chai, gói, ml, kg, lít).
- Đầu ra: mã dùng trên dòng phí của BĐM TP và trên công nợ NCC.
- Quy tắc: khai theo mỗi lần NCC báo giá; giá và hiệu lực nằm ở bảng giá NCC GC (phần NCC / Giá vốn), danh mục chỉ giữ mã.
- Ràng buộc: không nhập kho, không tồn.

**SX-SP-08 Hình ảnh và mockup**
- Đầu vào: ảnh vật tư, ảnh nhãn, tệp mockup; trên mockup đánh dấu mã VTBB từng vị trí.
- Đầu ra: hình trên danh mục, trên báo cáo cho KD, trên phiếu BĐM.

**SX-SP-09 Ngưỡng tồn và MOQ theo mã + kho**
- Đầu vào: mã, kho, Min, MOQ (của NCC có MOQ nhỏ nhất), NCC phụ trách, ghi chú.
- Đầu ra: trạng thái *Đủ* / *Dưới MOQ* / *Dưới Min - cần đặt hàng* trên báo cáo tồn. Thực hiện ở phần Kho.

### 7.2 Nhóm B — Quy tắc

**SX-SP-10 Sinh mã tự động**
- Đầu vào: loại mã; với chai: chất liệu + hình dạng; với thùng: thương hiệu; với xô: màu; với nhãn / NDT / hộp riêng / BTPCT: mã HH.
- Đầu ra: mã gợi ý = tiền tố + số kế tiếp 4 chữ số, hoặc tiền tố + 4 số cuối mã HH (+ hậu tố `.1`, `.2` nếu đã có).
- Ràng buộc: người dùng được sửa mã gợi ý nhưng phải đúng mẫu của loại; số chạy riêng theo tiền tố.

**SX-SP-11 Sinh tên theo mẫu**
- Quy tắc: mỗi loại mã một mẫu ghép (bảng 4.1). Ví dụ chai: `Chai {chất liệu} {hình dạng} cổ {cổ} {thể tích} ({trọng lượng}g) {màu}`; tên hóa đơn chai: `Chai {chất liệu} {thể tích}`.
- Ràng buộc: tên sinh ra sửa tay được, có cờ *đã sửa tay* để không bị ghi đè khi đổi thuộc tính.

**SX-SP-12 Kiểm trùng**
- Quy tắc: so bộ thuộc tính định danh của loại (vd chai: chất liệu + hình dạng + cổ + thể tích + trọng lượng + màu + nhận diện); trùng thì hiện mã đã có và chặn hoặc cảnh báo.

**SX-SP-13 Phiếu khai báo mã mới và duyệt**
- Đầu vào: thông tin mã, người khai báo, lý do (mới / đổi thuộc tính / theo báo giá NCC / theo đơn hàng).
- Luồng: Nháp → Chờ duyệt → Đã duyệt → (tùy chọn) Đã khai trên Misa. Người duyệt: quản lý thu mua với mã do Thu mua khai; QLSX với mã do Sản xuất khai.
- Đầu ra: mã chuyển sang *đang dùng* khi được duyệt; danh sách mã chờ kế toán tạo trên Misa (xuất tệp theo *Mẫu khai báo*).
- Ràng buộc: mã chưa duyệt không chọn được trên BĐM đã duyệt và đơn hàng.

**SX-SP-14 Đồng bộ mã DEGO - mã NCC GC**
- Đầu vào: NCC GC, mã DEGO, mã NCC, tên NCC, phân loại.
- Đầu ra: phép đổi mã hai chiều khi nhập tồn kho / công nợ NCC gửi và khi in đơn, lệnh sản xuất gửi NCC.
- Ràng buộc: (NCC, mã NCC) duy nhất; một mã DEGO có thể ứng nhiều mã NCC ở các NCC khác nhau.
- Liên kết: Kho (đối chiếu tồn), công nợ NCC GC.

**SX-SP-15 Bảng dòng công thức KD - NCC**
- Đầu vào: tên pháp lý, dòng V + màu phía KD, NCC GC, dòng V + màu phía NCC, mã BTP, hiệu lực, ghi chú (vd NCC chưa nắm thay đổi công thức).
- Đầu ra: khi đơn hàng chọn mã HH + NCC, hệ thống hiện đúng dòng công thức phải ghi trên đơn gửi NCC.
- Ràng buộc: chỉ nhóm được cấp quyền mới thấy cột phía NCC.

**SX-SP-16 Quản lý nhãn mác**
- Đầu vào: tình trạng in (chưa in, đã in, tạm ngưng, bỏ nhãn), trạng thái NCC duyệt nhãn, chất liệu nhãn, kích thước nhãn, loại thùng, nhãn dán thùng (có / dùng nhãn chính / không), hộp giấy, lưu ý độc quyền, sáu mã bao bì gợi ý.
- Đầu ra: BĐM VTBB nháp sinh từ sáu mã bao bì; cảnh báo đơn hàng khi nhãn chưa in hoặc chưa được NCC duyệt.
- Liên kết: SX-SP-05, SX-SP-28, SX-SP-49.

**SX-SP-17 Bảo mật công thức và NL mã hóa**
- Quy tắc: tách quyền xem (1) danh mục và BĐM VTBB; (2) BĐM BTP có lượng NL; (3) dòng công thức NCC; (4) tên thật của mã `NA`; (5) giá. Người không có quyền (2) vẫn thấy mã BĐM BTP nhưng không thấy dòng.
- Liên kết: phân quyền ERP (thêm entity mới cho công thức).

**SX-SP-18 Trạng thái vòng đời mã**
- Giá trị: nháp, đang dùng, ngưng dùng, (với tên pháp lý) đang kinh doanh / chưa kinh doanh / ngưng sử dụng.
- Ràng buộc: mã ngưng dùng không chọn được trên chứng từ mới nhưng vẫn hiện trên chứng từ cũ.

### 7.3 Nhóm C — Công thức BTP

**SX-SP-19 Danh sách công thức / dòng công thức BTP**
- Đầu vào: tên pháp lý 1, tên pháp lý 2 (ruột dùng chung), dòng V áp dụng với KD, màu gốc của công thức nguyên bản, màu thực tế theo dòng V, cờ có phụ gia, cờ có pha màu, mô tả (không phụ gia / có phụ gia / pha thêm màu gì), mã Lab, mã BTP, công thức áp dụng với NCC, ghi chú, ngày cập nhật.
- Đầu ra: *Danh sách quản lý BTP* để tra từ mã HH ra dòng công thức và BĐM BTP.
- Quy tắc: màu thực tế mặc định bằng màu gốc, chỉ khác khi có pha màu.
- Ràng buộc: (tên pháp lý, dòng V, màu thực tế) không trùng.

**SX-SP-20 Theo dõi công thức mới**
- Đầu vào: ngày, NCC, tên pháp lý, thành phần, các mốc tiến độ (ngày + nội dung), kết quả test, quyết định duyệt / không duyệt.
- Đầu ra: công thức chốt (ngày chốt, mã công thức, mã BĐM); dòng mới ở SX-SP-19.
- Quy tắc: tiến độ là nhật ký nhiều dòng, không gõ dồn một ô; số lần phối lại được đếm (NCC mới tối đa 2 lần).

**SX-SP-21 Theo dõi test mẫu**
- Đầu vào: ngày yêu cầu, tên mẫu (tên pháp lý), phiếu yêu cầu (nhập / xuất), thông tin mẫu (mẫu công thức mới / lô nhập kho / hàng tồn ở NCC), từng hoạt chất + ĐVT + hàm lượng theo giấy đăng ký, ngày có kết quả, hàm lượng test, kết quả ngoại dạng (ngày, mô tả), ghi chú.
- Công thức:
  - `Chênh lệch = Hàm lượng test − Hàm lượng đăng ký`.
  - `Tỷ lệ chênh lệch = Chênh lệch / Hàm lượng đăng ký`.
  - `Sai số cho phép` tra theo SX-SP-22.
  - `Kết quả = Đạt` khi trị tuyệt đối tỷ lệ chênh lệch ≤ sai số cho phép **và** ngoại dạng đạt; ngược lại *Không đạt*.
- Ví dụ từ sổ: đăng ký 50 g/kg, test 52,1 → chênh +2,1, tỷ lệ 4,2%, sai số cho phép 5% → Đạt. Đăng ký 19%, test 16,77% → tỷ lệ −11,7%, sai số 6% → Không đạt.
- Ràng buộc: sản phẩm nhiều hoạt chất thì đạt khi mọi hoạt chất đạt. (Sổ mẫu có dòng chia cho 1.000 hoặc 100 thay vì chia cho hàm lượng đăng ký — cần chốt, câu hỏi 12.)
- Liên kết: SX-SP-20, SX-SP-44, Kho (cột *LAB TEST* và *hàm lượng thực tế* trên phiếu nhập NL/BTP), SX-SP-25 (hàm lượng thực tế NL).

**SX-SP-22 Bảng khung sai số hàm lượng**
- Đầu vào: dải hàm lượng (từ, đến), dạng (lỏng / rắn), sai số; văn bản căn cứ, ngày hiệu lực.
- Đầu ra: hàm tra sai số cho phép theo hàm lượng đăng ký và dạng.
- Quy tắc: bảng ở mục 4.8 (a). Sai số phối chế nội bộ ≤ 50% khung Nhà nước.

**SX-SP-23 Khung sai số chiết rót và thể tích chốt đóng**
- Đầu vào: thể tích trên nhãn, khung sai số, thể tích chốt đóng; theo sản phẩm + NCC: tỷ lệ đóng đã chốt, thông tin KD nắm, ghi chú.
- Công thức: `% thiếu dự kiến = 1 − Thể tích chốt đóng / Thể tích trên nhãn`; phải ≤ khung sai số.
- Đầu ra: lượng BTP ruột thực dùng trên 1 thành phẩm (vd 440 ml thay vì 450 ml) cho BĐM TP và giá vốn.

**SX-SP-24 Màu độc quyền theo khách hàng**
- Đầu vào: tên pháp lý, khách / nhóm khách, màu dành riêng.
- Đầu ra: cảnh báo khi hồ sơ HH của khách khác chọn màu đã dành riêng.

### 7.4 Nhóm D — Định mức / BOM

**SX-SP-25 BĐM BTP**
- Đầu phiếu: ngày cập nhật, mã BĐM, mã công thức Lab, mã BTP, tên pháp lý, dòng V, màu, thành phần, tỷ trọng BTP sau phối, đơn vị chuẩn bị nguyên liệu (công ty / NCC), ghi chú cách tính, người duyệt, ngày duyệt.
- Dòng (mỗi hoạt chất / nguyên liệu một dòng): tên hoạt chất, hàm lượng sản phẩm, hàm lượng yêu cầu sản xuất, tỷ lệ yêu cầu / sản phẩm, sai số phối chế cho phép, kết quả so khung, mã NL nội bộ, tên NL, hàm lượng trên nhãn NL, hàm lượng thực tế NL, lượng NL trên 1.000 kg.
- Đơn vị gốc: 1.000 kg hoặc 1.000 lít BTP.
- Ràng buộc: mã BTP và mã NL phải tồn tại và đang dùng; BĐM đã duyệt không sửa, muốn đổi thì tạo phiên bản mới.
- Ghi chú nguồn: sổ hiện chỉ có dòng hoạt chất chính; dung môi, phụ gia, chất mang chưa có dòng (câu hỏi 10).

**SX-SP-26 Tính lượng NL theo hàm lượng và tỷ trọng**
- Công thức (đúng công thức ô trên sheet *3. BDM BTP*):
  - Chưa có tỷ trọng: `Lượng NL (kg) trên 1.000 kg = Hàm lượng yêu cầu SX × 1.000 / Hàm lượng thực tế NL`.
  - Có tỷ trọng: `Lượng NL = Tỷ trọng × Hàm lượng yêu cầu SX × 1.000 / Hàm lượng thực tế NL`.
  - `Tỷ lệ YCSX = Hàm lượng yêu cầu SX / Hàm lượng sản phẩm`.
  - Kết luận *Trong khung cho phép* khi `Tỷ lệ YCSX > 1 − Sai số phối chế cho phép`; ngược lại *Sai số vượt quy định*.
- Ví dụ: Fenobucarb 50% từ NL thực tế 98% → 0,5 × 1.000 / 0,98 = **510,20 kg**. Glufosinate 20% từ NL 95% → **210,53 kg**; từ NL thực tế 97,8% → **204,50 kg**.
- Ràng buộc: hàm lượng thực tế NL > 0; hàm lượng nhập dưới dạng phần trăm thống nhất (g/l phải quy đổi; sổ ghi chú *chưa tính tỷ trọng* ở nhiều dòng).

**SX-SP-27 Tính lượng NL cần mua và giá BTP tạm**
- Đầu vào: mã BĐM BTP, lượng BTP cần phối, với từng NL: giá (đồng / kg hoặc lít), NCC, lượng mua chẵn bao / phuy; phí phối tham khảo; NCC GC dự kiến.
- Công thức:
  - `Lượng NL cần phối = Lượng NL trên 1.000 × Lượng BTP cần phối / 1.000`.
  - `Giá NL trong 1 kg BTP = Giá NL × Lượng NL trên 1.000 / 1.000`.
  - `Giá BTP đã gồm phí phối = Σ Giá NL trong 1 kg BTP + Phí phối trên 1 kg (lít)`.
- Trạng thái dòng: *Giá tham khảo* / *Duyệt mua*; có ngày duyệt mua, người duyệt mua.
- Ghi chú: công thức trên sổ đang chia cho *lượng BTP cần phối* thay vì 1.000, cho kết quả sai khi lượng khác 1.000 (câu hỏi 11). Phần duyệt giá thuộc tài liệu Giá vốn; ở đây chỉ cấp số lượng từ BĐM.
- Liên kết: sổ giá `tab_product_price_ledger`, báo giá `tab_product_price_quote`; *3.2 Khảo sát giá NL/BTP* (giá trong nước, giá nhập khẩu, giá thấp nhất 3 tháng theo dữ liệu hải quan, thời gian áp dụng giá, thời gian có hàng, công nợ, lượng mua tối thiểu) — ERP đã có *Tra cứu thị trường* cho dữ liệu hải quan.

**SX-SP-28 BĐM VTBB**
- Đầu phiếu: ngày cập nhật, mã đơn đặt hàng đại diện, mã BĐM, mã HH, tên HH, tên pháp lý, ĐVT thành phẩm, trọng lượng / thể tích thành phẩm, số thành phẩm trên hộp, số thành phẩm trên thùng, cấu thành (bên công ty mang gì, bên NCC tự chuẩn bị gì), ghi chú thay đổi, người duyệt, ngày duyệt.
- Dòng: nhóm vật tư, mã VTBB, tên, ĐVT, định mức trên 1 thành phẩm.
- Quy tắc định mức mặc định: chai / túi / xô / can, nắp, nhãn, cốc đong, seal = 1; hộp = 1 / số thành phẩm trên hộp; thùng, nhãn dán thùng = 1 / số thành phẩm trên thùng (vd 1 / 40 = 0,025).
- Ràng buộc: mỗi BĐM có ít nhất một vật tư chứa (chai / túi / xô / can / lon); số trên thùng > 0 khi có dòng thùng hoặc NDT.
- ERP đã có: đầu phiếu `tab_packaging_bom`, dòng `tab_packaging_bom_part`, màn danh sách + form + nhập Excel. Xem mục 9.4 về phần phải thêm.

**SX-SP-29 Mở rộng loại thành phần và nhiều mã cùng loại**
- Loại hiện có trên ERP (`PackagingRole`): 1 Chai, 2 Nắp, 3 Nhãn, 4 Nhãn thùng, 5 Thùng.
- Loại cần thêm theo sổ: vật tư chứa khác (túi / gói, xô, can, lon, bao), hộp, cốc đong, seal, tem, màng co, túi PE, tag treo, tấm lót, nhãn phụ; và các loại không phải bao bì: BTP ruột, nguyên liệu, phí sang chai đóng gói, phí phối trộn.
- Quy tắc: *Chai* nên đổi nghĩa thành *vật tư chứa chính* (hoặc thêm loại riêng cho từng dạng) vì sản phẩm dạng gói không có chai, nắp.
- Ràng buộc cần gỡ: duy nhất `(bom_id, part_type)`; thay bằng số thứ tự dòng.

**SX-SP-30 Định mức số lượng trên từng dòng**
- Đầu vào: số lượng trên 1 thành phẩm (số thập phân 6 chữ số), ĐVT dòng, **cách tính**: cố định / 1 chia quy cách thùng / 1 chia quy cách hộp / theo thể tích trên nhãn / theo thể tích chốt đóng.
- Quy tắc: lưu cả cách tính lẫn giá trị để khi đổi quy cách thùng thì các dòng tự tính lại (ở bản nháp), còn bản đã duyệt giữ nguyên số.
- Tương thích: công thức chi phí hiện tại của ERP (`Chai + Nắp + Nhãn + (Nhãn thùng + Thùng) / Quy cách thùng`) là trường hợp riêng của `Σ Giá × Định mức`.

**SX-SP-31 Bên cung ứng từng thành phần và cấu thành**
- Đầu vào trên dòng: bên cung ứng = CTY hoặc NCC; khi là CTY: công ty / thương hiệu nội bộ nào mang sang. Đầu phiếu: câu mô tả cấu thành (sinh tự động từ các dòng, sửa tay được).
- Đầu ra: lệnh sản xuất chia cột *đơn vị cung ứng*; phiếu xuất kho chỉ gồm dòng CTY; giá vốn chỉ cộng dòng CTY (dòng NCC đã nằm trong giá NCC).
- Ràng buộc: cùng mã HH nhưng làm ở NCC khác thì cấu thành có thể khác → BĐM TP cần gắn NCC GC áp dụng (câu hỏi 6).

**SX-SP-32 BĐM thành phẩm gộp**
- Đầu phiếu: mã BĐM TP, mã HH, tên hàng, phân loại (P phân bón / T thuốc), tên pháp lý, thương hiệu, ĐVT, đơn vị thể tích (g / ml), thể tích trên nhãn, quy cách thùng, quy cách hộp, mã SP gốc (dòng V + màu), màu, cấu thành nội bộ, mã đơn đầu tiên phát sinh, ngày lên đơn, mã BĐM VTBB nguồn, mã BTP ruột, mã BĐM BTP nguồn.
- Dòng: loại thành phần, bên cung ứng, mã vật tư, tên, ĐVT, số lượng trên 1 thành phẩm.
- Quy tắc lập: bung các dòng của BĐM VTBB; thêm một dòng *BTP ruột* với số lượng = thể tích (hoặc trọng lượng) trên nhãn theo ml / g; thêm dòng *Phí GC sang chai đóng gói* số lượng 1.
- Quy đổi: `Lượng BTP (lít hoặc kg) cho đơn = Số thành phẩm × Thể tích trên nhãn / 1.000` (nhân tỷ trọng nếu ruột quản lý theo kg mà nhãn ghi ml).
- Mã: số phiên bản tăng theo tổ hợp (mã HH, BĐM VTBB) mới.
- Ràng buộc: chỉ gộp từ BĐM BTP và BĐM VTBB **đã duyệt**; ĐVT dòng BTP ruột phải là ml / g (dữ liệu mẫu đang ghi *Cái*).

**SX-SP-33 Dòng phí gia công**
- Đầu vào: mã PĐG (chọn theo NCC + loại bao bì + dải thể tích chứa thể tích trên nhãn), số lượng 1 trên 1 thành phẩm, ĐVT (chai / gói); nếu có: mã PPT cho ruột tự phối.
- Quy tắc: hệ thống gợi ý mã PĐG theo thể tích trên nhãn (vd 1.000 ml rơi vào dải 801-1000 ml); bên cung ứng luôn là NCC.
- Liên kết: bảng giá phí đóng gói, phí phối của NCC GC (tài liệu NCC / Giá vốn).

**SX-SP-34 Phiên bản BĐM**
- Trường: số phiên bản, lý do thay đổi, đơn hàng đầu tiên áp dụng, ngày hiệu lực, cờ hiện hành, phiên bản trước.
- Quy tắc: *Tạo phiên bản mới* chép từ bản hiện hành sang bản nháp; duyệt xong thì bản mới thành hiện hành, bản cũ chuyển *ngưng*; đơn hàng và lệnh sản xuất lưu **đúng mã phiên bản** đã dùng.
- Ràng buộc: BĐM BTP có thể có **nhiều phiên bản cùng hiện hành** (mỗi lô NL một hàm lượng) — khi lập lệnh phối phải chọn phiên bản theo lô NL dùng.

**SX-SP-35 Duyệt BĐM**
- Luồng: Nháp → Chờ duyệt → Đã duyệt → Ngưng. Từ chối thì về Nháp kèm lý do.
- Người duyệt: QLSX cho cả ba tầng. Phiếu giấy có thêm ô ký *Duyệt bao bì*, *Duyệt pháp lý*, *Duyệt giá*, *Kế toán trưởng* — có đưa lên hệ thống thành các bước duyệt hay không cần chốt (câu hỏi 7).
- Ràng buộc: chỉ BĐM đã duyệt mới dùng được cho lệnh sản xuất, xuất kho, giá vốn chính thức; bản nháp chỉ dùng cho giá tham khảo.
- ERP: tái dùng module `approval` (luồng duyệt chứng từ hiện có) thay vì viết mới.

**SX-SP-36 BĐM thuế và cấu thành thuế**
- Đầu vào: mục đích (nội bộ / thuế), công ty cấu thành, công ty nhận hóa đơn, luồng hóa đơn (chuỗi công ty), mã và tên vật tư theo hóa đơn của công ty đó, BĐM nội bộ tương ứng.
- Quy tắc: NCC cấu thành → không lập BĐM thuế; công ty nội bộ cấu thành hoặc chuẩn bị một phần → lập. Cùng mã HH có thể có BĐM thuế của nhiều công ty.
- Đầu ra: *Số BĐM CCT BTP*, *Số BĐM CCT TP* in trên phiếu; bản gửi P TCKT của từng công ty.
- Ghi chú: sổ chưa có văn bản định nghĩa khi nào mã BĐM thuế khác mã nội bộ; ví dụ mẫu đều ghi giống nhau. Nên làm sau khi chốt câu hỏi 5.

**SX-SP-37 In phiếu BĐM ký duyệt**
- Nội dung phiếu *Bảng định mức VTBB thành phẩm*: ngày, người lập, bộ phận, chức vụ, kho xuất, hàng mới / xử lý lại, mã hàng, mã BĐM, tên hàng, tên pháp lý, quy cách thùng, cấu thành nội bộ, số BĐM CCT BTP, số BĐM CCT TP, lý do xuất, ghi chú; bảng: STT, mã vật tư, tên vật tư, ĐVT, số lượng trên 1 thành phẩm, luồng hóa đơn, ghi chú; dòng luồng hóa đơn; ô ký.
- Tái dùng: khung trang in đã có của cụm giá NVL (trang in lịch sử giá, tác động giá).

**SX-SP-38 Nhập và xuất Excel định mức**
- Đã có: mẫu nhập 5 loại bao bì theo mã HH, ghi lô nhập, xem trước và xóa theo lô.
- Cần thêm: mẫu dạng **dòng** (mỗi thành phần một dòng: mã HH, phiên bản, loại, mã, số lượng, bên cung ứng) vì dạng cột phẳng không chứa được nhiều mã cùng loại.

**SX-SP-39 Tra ngược mã vật tư**
- Đã có: lọc sản phẩm theo mã bao bì, đếm số sản phẩm dùng một mã, mô phỏng tác động khi giá mã đổi.
- Cần thêm: tra ngược hai tầng NL → BTP → TP; chỉ tính phiên bản hiện hành.

**SX-SP-40 Chi phí định mức 1 thành phẩm**
- Công thức: `Chi phí 1 TP = Σ (Đơn giá dòng × Số lượng trên 1 TP)` cho các dòng bên CTY cung ứng; dòng BTP ruột lấy giá BTP trên ml / g; dòng phí lấy bảng giá NCC. `Chi phí 1 thùng = Chi phí 1 TP × Quy cách thùng`.
- Đã có: phần bao bì (5 loại) với nguồn giá từ sổ giá và báo giá, có xu hướng tăng / giảm.
- Phần mở rộng (BTP, phí, giá sản xuất và giá kinh doanh) thuộc tài liệu Giá vốn.

**SX-SP-41 Cảnh báo dữ liệu định mức**
- Danh sách cảnh báo đề xuất: (1) mã HH đang có đơn nhưng chưa có BĐM TP duyệt; (2) dòng chưa khai mã; (3) mã trên dòng đã ngưng dùng; (4) có thùng / NDT mà quy cách thùng = 0; (5) ĐVT dòng lệch ĐVT danh mục; (6) cùng một mã xuất hiện ở hai loại (sổ mẫu dùng mã nhãn chính cho cả nhãn và nhãn thùng — hợp lệ khi *lấy nhãn chính dán thùng*, cần cờ xác nhận); (7) tên pháp lý trên BĐM lệch hồ sơ HH; (8) BĐM BTP có dòng *Sai số vượt quy định*; (9) cổ nắp khác cổ chai.
- Đã có trên ERP: (2), (4), thiếu giá, lệch ĐVT ở sổ giá.

**SX-SP-42 Bung BĐM cho lệnh sản xuất và xuất kho**
- Đầu vào: mã BĐM TP (đúng phiên bản), số thành phẩm (= số KD đặt + số mẫu Lab), NCC GC.
- Đầu ra: danh sách dòng `Tổng cần = Số thành phẩm × Số lượng trên 1 TP`, tách CTY / NCC; số thùng = số thành phẩm / quy cách thùng.
- Ghi chú: BĐM **không có cột hao hụt**; hao hụt cho phép nằm ở chính sách NCC (SX-SP-51). Lệnh sản xuất và phiếu xuất kho là của phần Đơn hàng gia công và Kho.

### 7.5 Nhóm E — Tiêu chí đánh giá, khảo sát, sổ phụ

**SX-SP-43 Tiêu chuẩn nguyên liệu**
- Đầu vào: mã NL, xuất xứ, ngoại quan, màu, độ tan, độ trong, độ ẩm, pH, hàm lượng, số CAS, thuộc phụ lục nghị định; người cấp (Lab), ngày.
- Đầu ra: bộ tiêu chí để Thu mua hỏi hàng và để kiểm khi nhập.

**SX-SP-44 Phiếu yêu cầu test Lab và kết quả**
- Đầu vào: đối tượng test (mẫu công thức / lô NL / lô BTP / thành phẩm của đơn), loại test (ngoại dạng, hàm lượng), số mẫu (mỗi lần 2-4 mẫu), ngày gửi, hạn trả (ngoại dạng 1-2 ngày, hàm lượng 14 ngày).
- Đầu ra: kết quả Đạt / Không đạt theo SX-SP-21; cờ quá hạn trả kết quả.
- Quy tắc: hàng mang tên của công ty: BTP mua thì test cả hai loại, BTP tự phối test hàm lượng định kỳ; hàng mang tên NCC GC: test cả hai; thành phẩm quy cách từ 1 lít hỏi QLDL số mẫu.

**SX-SP-45 Sổ lưu mẫu đối chứng**
- Đầu vào: sản phẩm, lô, nơi lưu (Lab / NCC), ngày lưu, hạn lưu, kỳ đối chiếu.
- Quy tắc: NCC lưu tối thiểu 2 năm; DEGO lưu mẫu chốt, đối chiếu 6 tháng một lần.

**SX-SP-46 Tiêu chí KCS thành phẩm theo sản phẩm**
- Bộ tiêu chí: xem mục 8.4. Phần Sản phẩm giữ **bộ tiêu chí và phụ kiện bắt buộc của từng mã HH** (cốc đong, tag, tem, màng co — suy từ BĐM); phần Kho / Đơn hàng thực hiện kiểm.

**SX-SP-47 Khảo sát phù hợp công nghệ NCC**
- Đầu vào: ngày tiếp nhận, bộ phận yêu cầu, mã yêu cầu, mã + tên VTBB, mã + tên ruột, NCC GC, nội dung cần khảo sát, hiện trạng VTBB (sẵn kho / chưa sẵn kho / luân chuyển / mua), hiện trạng BTP (điều chuyển / mua mới / sẵn kho + ngày có hàng), ghi chú mã thay thế, người phụ trách phía Sản xuất, người phụ trách phía NCC, số mẫu gửi, yêu cầu NCC trả gì, kênh liên hệ, ngày dự kiến nhận kết quả, tiến độ, kết quả, đánh giá của QLSX, ngày phản hồi KD, hình thức phản hồi.
- Quy tắc: hạn kết quả = ngày gửi + 10 đến 14 ngày; cảnh báo quá hạn; nhóm 1 (chai, nhãn, túi, thùng, NDT, can, xô, túi PE) bắt buộc khảo sát trước đơn đầu tiên với NCC đó.
- Đầu ra: kết quả *Phù hợp - Đạt* / *Không phù hợp - Cần điều chỉnh*; ghi vào ma trận SX-SP-48.

**SX-SP-48 Ma trận phù hợp VTBB - ruột - NCC**
- Đầu ra: khi lập đơn gia công, cảnh báo nếu tổ hợp (vật tư chứa, ruột, NCC) chưa có khảo sát đạt.

**SX-SP-49 Cọc nhãn**
- Đầu vào: NCC GC, mã HH, mã nhãn, tên nhãn, tên pháp lý trên nhãn, thương hiệu, công ty trên hợp đồng cọc, ĐVT, số lượng dự kiến, số tiền cọc, người phụ trách, số văn bản, loại văn bản (hợp đồng / phụ lục), ngày hiệu lực, ngày hết hạn, ngày chuyển cọc, điều kiện hoàn cọc.
- Theo dõi: xác nhận của ĐP VTBB về tiến độ sản lượng, hiện trạng tồn nhãn, nguyên nhân kết thúc.
- Hoàn cọc: số tiền hoàn, hình thức hoàn (chuyển khoản / cấn trừ công nợ), tên và số văn bản thanh lý, ngày xử lý, chứng từ.
- Công thức: `Số tiền hoàn = Tiền cọc − Phần bị trừ theo điều kiện hợp đồng` (sổ mẫu: 3.000.000 − 1.053.600 = 1.946.400).
- Trạng thái: đang cọc → đủ điều kiện hoàn → đã thanh lý. Liên kết: hợp đồng (`tab_contract`), công nợ NCC GC.

**SX-SP-50 Mẫu cho tặng**
- Đầu vào: ngày tiếp nhận, bộ phận yêu cầu, mục đích, đơn vị cho tặng (tên, mã số thuế, người đại diện, điện thoại), mã và tên VTBB phía NCC đặt, chất liệu, hình dạng, thông số kỹ thuật, màu, ĐVT, số lượng, lưu ý, thời gian và hình thức nhận, người phụ trách, việc cần làm, bốn ô việc (test, chụp, lưu, gửi), tiến độ, kết quả trả bộ phận yêu cầu, trạng thái, đánh giá lợi ích, link hình / thông số / kết quả test.
- Ràng buộc: không sinh phiếu kho, không tính chi phí. Mẫu đạt có thể chuyển thành đề xuất khai mã mới (SX-SP-13).

**SX-SP-51 Chính sách theo sản phẩm tại NCC**
- Đầu vào: NCC GC, nhóm vật tư (BTP, chai / túi / can, nhãn, thùng, khác), % hao hụt cho phép, căn cứ (điều khoản hợp đồng); theo mã BTP: có nhận dự trù không, MOQ phối, thời gian chuẩn bị.
- Công thức (sổ VTBB): `Hao hụt thực tế = Số lượng hao hụt / Số lượng nhập × 100%`; vượt % cho phép thì cảnh báo.
- Ghi chú: thuộc hồ sơ NCC GC; nêu ở đây vì BĐM không chứa hao hụt và phải tra chỗ này khi quyết toán.

**SX-SP-52 Báo cáo dữ liệu VTBB cho Kinh doanh**
- Nội dung: mã, tên, hình, giá hiện hành, sản phẩm áp dụng, lịch sử sử dụng theo BĐM, giá thấp nhất / cao nhất 5 lần mua gần nhất, công nghệ theo NCC, MOQ.
- Ràng buộc: giá là dữ liệu nhạy cảm; ERP hiện giấu cả cụm giá sau quyền `packaging_cost.read`.

**SX-SP-53 Lịch sử thay đổi** và **SX-SP-54 Chuyển dữ liệu ban đầu**
- Lịch sử: dùng nhật ký sẵn có; riêng BĐM đã có phiên bản nên lịch sử nghiệp vụ nằm ở chuỗi phiên bản.
- Chuyển dữ liệu: thứ tự nạp là danh mục dùng chung → mã NL, BTP, VTBB → hồ sơ HH → công thức → BĐM BTP → BĐM VTBB → BĐM TP; mỗi bước có báo cáo dòng lỗi (mã không tồn tại, trùng, thiếu ĐVT). Sổ nhãn mác có khoảng sáu nghìn dòng HH nên cần nhập theo lô và xóa được theo lô (đã có cơ chế lô nhập).

---

## 8. Tiêu chí đánh giá

Phần này gom mọi tiêu chí chấm / kiểm gắn với **sản phẩm, mẫu, công thức**. Tiêu chí đánh giá NCC GC đầy đủ (100 điểm, 21 tiêu chí) thuộc tài liệu NCC gia công; ở đây chỉ trích phần dính tới sản phẩm (mục 8.6).

### 8.1 Tiêu chí công thức (trước khi chốt)

| Tiêu chí | Cách đo | Ngưỡng đạt | Ai đánh giá |
|---|---|---|---|
| Hàm lượng yêu cầu sản xuất so với hàm lượng đăng ký | Tỷ lệ YCSX = hàm lượng yêu cầu / hàm lượng sản phẩm | Lớn hơn 1 − sai số phối chế cho phép | ĐP NL/BTP (tự tính trên BĐM BTP) |
| Sai số phối chế nội bộ | So với khung Nhà nước (bảng 4.8 a) | Không quá 50% khung Nhà nước | QLSX chốt với NCC |
| Ngoại dạng mẫu phối | So với mẫu chuẩn / mẫu nhập khẩu: dạng, màu, độ mịn, độ thấm ướt | Tương đồng mẫu chuẩn | Lab |
| Hàm lượng mẫu phối | Test hàm lượng từng hoạt chất | Trong sai số cho phép | Lab |
| Số lần phối | Đếm số lần phối lại | NCC mới: đạt trong tối đa 2 lần | QLSX |
| Phù hợp công nghệ NCC | Khảo sát ruột + bao bì tại NCC | *Phù hợp - Đạt* | NCC GC, QLSX |

### 8.2 Tiêu chí mẫu (test mẫu)

| Tiêu chí | Cách tính | Kết quả |
|---|---|---|
| Hàm lượng | Chênh lệch = test − đăng ký; tỷ lệ = chênh lệch / đăng ký; so với sai số cho phép theo dải hàm lượng và dạng | Đạt khi trị tuyệt đối tỷ lệ ≤ sai số cho phép, với **mọi** hoạt chất |
| Ngoại dạng | Mô tả: dạng (huyền phù, cốm, bột...), màu, độ mịn, độ thấm ướt | Đạt / Không đạt kèm mô tả |
| Ổn định | Chạy gia tốc 14 ngày rồi test lại hàm lượng (khi kết quả sát ngưỡng) | Đạt / Không đạt |

Thời hạn: ngoại dạng 1-2 ngày; hàm lượng 14 ngày. Số mẫu: mỗi lần 2-4 mẫu, có mẫu lưu đối chiếu. Không có thang điểm, chỉ có Đạt / Không đạt.

### 8.3 Tiêu chí nguyên liệu

Theo từng mã NL (Lab cấp cho Thu mua): xuất xứ, ngoại quan, màu, độ tan, độ trong, độ ẩm, pH, hàm lượng, số CAS, thuộc phụ lục nghị định hay không. Khi nhập kho: Lab test Đạt / Không đạt, ghi **hàm lượng thực tế**, số lô, NSX, HSD, số CAS; ngày sản xuất trên bao bì phải trước hoặc bằng ngày nhận hóa đơn; chứng từ kèm: COA / phiếu kiểm tra chất lượng, biên bản cân tổng khối lượng.

### 8.4 Tiêu chí thành phẩm (Lab và KCS)

| Nhóm | Tiêu chí | Giá trị |
|---|---|---|
| Lab test thành phẩm của đơn | Ngoại dạng, màu sắc, trọng lượng, thể tích | ĐẠT / KHÔNG ĐẠT |
| Thể tích chiết rót | Thể tích thực so với thể tích trên nhãn | Trong khung sai số chiết rót (bảng 4.8 b); mức chốt đóng theo sản phẩm + NCC |
| KCS khi kho nhận | Số lượng thực nhận so với yêu cầu | Số đạt, số không đạt |
| | Ngày sản xuất, số lô, hạn sử dụng | Có, đúng |
| | Phụ kiện đi kèm (tag treo, cốc đong, nhãn phụ, tem, màng co) | Đủ / Không đủ |
| | Ngoại dạng bao bì (xì, rách, tróc) | Đạt / Không đạt |
| | Chứng từ NCC | Khớp / Không khớp |

Quy định: kho đã KCS *đạt* thì lỗi phát sinh do bảo quản tại kho do kho chịu. Thời hạn còn quy trách nhiệm NCC sau khi nhận hàng chưa chốt (ERP có sẵn `inspection_days`, `return_days` trên hồ sơ NCC).

### 8.5 Tiêu chí vật tư bao bì

- Phù hợp ruột: sức chứa, dạng chứa, tương thích ruột (KD bảo đảm theo tư vấn của Sản xuất).
- Phù hợp công nghệ NCC: kết quả khảo sát (mục 5.7).
- Ghép bộ: cổ nắp = cổ chai; cốc đong đúng cổ; thùng lọt lòng chứa vừa số chai theo quy cách; nhãn đúng kích thước phù hợp của chai.
- Mẫu cho tặng: đánh giá lợi ích (có thay thế được mã nào không) sau khi test, chụp, lưu.

### 8.6 Phần tiêu chí NCC GC liên quan tới sản phẩm

Trích từ bảng đánh giá định kỳ NCC GC (6 tháng một lần hoặc đột xuất khi có sự cố; tổng 100 điểm; từ 90 *Xuất sắc*, 75-89 *Đạt*, 60-74 *Cần cải thiện*, dưới 60 *Không đạt*):

| Tiêu chí | Điểm tối đa | Mức chấm | Dữ liệu từ phần Sản phẩm |
|---|---|---|---|
| 2.2 Đa dạng hình thức sản xuất (nhận NL / BTP, VTBB mang sang) | 5 | 5 / 2 / 0 | Cấu thành trên BĐM TP theo NCC |
| 2.3 Máy móc và quy cách đóng gói | 5 | 5 / 2 / 0 | Ma trận phù hợp VTBB - ruột - NCC |
| 2.4 Khả năng test / phối theo yêu cầu | 5 | 5 khi đạt trong 1-2 lần / 2 / 0 | Sổ theo dõi công thức mới (số lần phối) |
| 3.1 Tỷ lệ lỗi thành phẩm / BTP trên số đơn | 8 | 8 (dưới 1%) / 5 (1-3%) / 2 (3-5%) / 0 (trên 5% hoặc lặp lại) | Kết quả test mẫu, KCS |
| 3.2 Hao hụt NL / BTP, VTBB so với định mức | 6 | 6 / 4 / 2 / 0 | **BĐM là mẫu số**: lượng theo định mức × sản lượng so với lượng thực xuất |
| 3.3 Thất lạc, hư hỏng, không xuất theo lô nhập trước xuất trước | 6 | 6 / 3 / 0 | — (Kho) |

---

## 9. Dữ liệu chính

Tên bảng dưới đây là **đề xuất** để dễ hình dung, trừ những tên ghi *đã có*. Trạng thái dùng số nguyên nhỏ kèm bảng mã (luật chung của ERP).

### 9.1 Mã hàng và danh mục

| Thực thể | Trường chính | Ghi chú |
|---|---|---|
| Mã hàng — `tab_product` (**đã có**) | `code`, `name`, `invoice_name`, `legal_name`, `item_group`, `unit`, `hh_code`, `hh_name`, `specs`, `is_active` | Thêm: loại mã, trạng thái vòng đời, cờ mã hóa, cờ tên sửa tay. |
| Thuộc tính theo phân loại (**đã thiết kế, chưa làm**) | `tab_attribute`, `tab_attribute_option`, `tab_item_group_attribute`, `tab_product_attribute` | Dùng cho SX-SP-02, 03, 04; không thêm cột cứng vào `tab_product`. |
| Hồ sơ thành phẩm (HH) | mã HH, tên HH, thương hiệu, khách hàng, công ty phân phối, công ty xuất hóa đơn, công ty nhận hóa đơn, NCC sản xuất mặc định, dòng sản phẩm, tên pháp lý, tên nhãn hiệu, mô tả ruột, quy cách (số + đơn vị), ĐVT chính, quy cách thùng, quy cách hộp, quy cách bao, tình trạng in nhãn, trạng thái duyệt nhãn, lưu ý | Hiện rải ở `tab_product.hh_*` và `tab_packaging_bom.fg_*`. |
| Danh mục dùng chung | ĐVT (`tab_unit`, **đã có**), phân loại (`tab_item_group`, **đã có**), thương hiệu (`tab_brand`, **đã có**), màu (tên, mã 2 ký tự), hình dạng, dạng ruột, dạng theo quy định, độ trong, dòng V, hoạt chất (tên, số CAS) | |
| Tên pháp lý | tên, phân loại, thành phần đăng ký, trạng thái, đơn vị đăng ký, bên nhận thuê tên, đơn vị có hợp quy, ngày hiệu lực, ngày hết hạn | Chủ dữ liệu là phần Pháp lý; ở đây chỉ tham chiếu. |
| Mã hàng phía NCC | NCC GC, mã DEGO, mã NCC, tên NCC, phân loại | `tab_product_supplier` (dự kiến CN-MH-14). |
| Phiếu khai báo mã | mã phiếu, loại mã, nội dung, lý do, người khai, trạng thái, người duyệt, ngày duyệt, ngày gửi kế toán, ngày có trên Misa | |

### 9.2 Công thức

| Thực thể | Trường chính |
|---|---|
| Dòng công thức BTP | tên pháp lý 1, tên pháp lý 2, dòng V (KD), màu gốc, màu thực tế, có phụ gia, có pha màu, mô tả pha thêm, mã Lab, mã BTP, ghi chú, ngày cập nhật |
| Quy đổi dòng công thức theo NCC | dòng công thức, NCC GC, dòng V phía NCC, màu phía NCC, hiệu lực, ghi chú |
| Yêu cầu công thức mới | ngày, NCC, tên pháp lý, thành phần, trạng thái, số lần phối, ngày chốt, mã công thức chốt, mã BĐM; bảng con nhật ký tiến độ (ngày, nội dung, người ghi) |
| Phiếu test mẫu | ngày yêu cầu, tên mẫu, loại đối tượng (công thức / lô nhập / tồn / đơn hàng), tham chiếu, thông tin mẫu, ngày và kết quả ngoại dạng, kết luận; bảng con hoạt chất (tên, ĐVT, hàm lượng đăng ký, hàm lượng test, chênh lệch, tỷ lệ, sai số cho phép, kết quả) |
| Khung sai số hàm lượng | từ, đến, dạng, sai số, căn cứ, hiệu lực |
| Khung chiết rót | thể tích trên nhãn, khung sai số, thể tích chốt đóng; theo sản phẩm + NCC: tỷ lệ đóng, ghi chú |

### 9.3 Định mức theo sổ hiện tại

| Thực thể | Đầu phiếu | Dòng |
|---|---|---|
| BĐM BTP | mã BĐM, phiên bản, ngày cập nhật, mã công thức Lab, mã BTP, tên pháp lý, dòng V, màu, thành phần, tỷ trọng, đơn vị chuẩn bị NL, ghi chú cách tính, trạng thái, người duyệt, ngày duyệt | hoạt chất, hàm lượng SP, hàm lượng YCSX, sai số phối chế, mã NL, hàm lượng nhãn NL, hàm lượng thực tế NL, lượng trên 1.000 |
| BĐM VTBB | mã BĐM, phiên bản, ngày cập nhật, mã đơn đại diện, mã HH, ĐVT thành phẩm, trọng lượng / thể tích, số trên hộp, số trên thùng, cấu thành (công ty / NCC), lý do thay đổi, trạng thái, người duyệt, ngày duyệt | nhóm vật tư, mã VTBB, ĐVT, định mức trên 1 thành phẩm |
| BĐM TP | mã BĐM, phiên bản, mã đơn đầu tiên, mã HH, phân loại P/T, thương hiệu, thể tích trên nhãn + đơn vị, quy cách thùng, quy cách hộp, mã SP gốc, màu, cấu thành, mã BĐM VTBB, mã BTP ruột, mã BĐM BTP; bộ thuế: mã BĐM VTBB thuế, mã BTP ruột thuế, mã BĐM TP thuế; duyệt, ngày duyệt | loại thành phần, bên cung ứng, mã vật tư, ĐVT, số lượng trên 1 thành phẩm |

### 9.4 Đề xuất mở rộng định mức bao bì của ERP thành BOM đầy đủ

**Hiện trạng trên `erp-v2`** (cụm duoc-CR-784, mới trên dev):

- `tab_packaging_bom` — đầu phiếu, **một dòng mỗi mã HH**: `fg_code` (duy nhất), `fg_name`, `legal_name`, `carton_qty`, `import_batch_id`, cùng các cột người tạo / sửa.
- `tab_packaging_bom_part` — thành phần: `bom_id`, `part_type` (bảng mã `PackagingRole`: 1 chai, 2 nắp, 3 nhãn, 4 nhãn thùng, 5 thùng), `part_code` (chuỗi mã `tab_product`, không khóa ngoại). Ràng buộc duy nhất `(bom_id, part_type)`: mỗi loại một mã. Không có cột số lượng.
- Công thức chi phí cứng trong `cost_service.py`: chai + nắp + nhãn + (nhãn thùng + thùng) / quy cách thùng.
- Màn: *Tác động giá*, *Giá theo sản phẩm*, *Bảng giá VTBB*, *Giá mua gần nhất*, *Lịch sử giá*, *Báo giá VTBB*, *Định mức bao bì* (đường dẫn `/procurement/packaging-cost/...`), quyền `packaging_cost.read`.
- Ghi chú trong mã đã dự liệu: thêm loại thành phần chỉ cần thêm thành viên bảng mã; cho nhiều mã cùng loại chỉ cần bỏ ràng buộc duy nhất; chưa cần nhiều phiên bản (câu hỏi Q7 của kế hoạch cũ).

**Đề xuất** — giữ hai bảng, mở rộng dần, không đập đi làm lại:

| Nhu cầu | Thay đổi đề xuất | Ảnh hưởng tới cái đang chạy |
|---|---|---|
| Loại thành phần mới | Thêm vào bảng mã: vật tư chứa khác (túi / gói, xô, can, lon, bao), hộp, cốc đong, seal, tem, màng co, túi PE, tag, tấm lót, nhãn phụ; **BTP ruột**; **nguyên liệu**; **phí sang chai đóng gói**; **phí phối trộn**. Thêm thuộc tính *nhóm* cho loại: bao bì / ruột / nguyên liệu / phí. | Không đổi cấu trúc bảng. Các màn giá bao bì lọc theo nhóm *bao bì* nên không bị ảnh hưởng. |
| Nhiều mã cùng loại | Bỏ ràng buộc duy nhất `(bom_id, part_type)`; thêm `line_no`. | Năm thuộc tính phẳng (`bottle_code`...) phải đổi sang trả mã **đầu tiên** của loại hoặc danh sách; API danh mục và mẫu nhập Excel cần cột dạng dòng. |
| Số lượng định mức | Thêm `qty_per_unit` (số thập phân 6 chữ số), `unit`, `qty_rule` (cố định / chia quy cách thùng / chia quy cách hộp / theo thể tích nhãn). Dữ liệu cũ nạp mặc định: chai, nắp, nhãn = 1 cố định; nhãn thùng, thùng = chia quy cách thùng. | `cost_service` đổi sang `Σ giá × qty_per_unit`; kết quả cũ giữ nguyên. |
| Bên cung ứng | Thêm trên dòng `supplied_by` (1 công ty, 2 NCC) và `supplier_company_id` (công ty nội bộ mang sang, 0 = chưa rõ); thêm trên đầu phiếu `composition_note` (câu cấu thành). | Mặc định dữ liệu cũ = công ty. Chi phí chỉ cộng dòng *công ty*. |
| NL / BTP | Dòng *BTP ruột* trong BĐM TP: `part_code` = mã BTP, `qty_per_unit` = thể tích trên nhãn, `unit` = ml / g, kèm `source_bom_id` trỏ BĐM BTP. **BĐM BTP** nên là bảng dòng riêng (vd `tab_formula_bom_line`: hoạt chất, hàm lượng SP, hàm lượng YCSX, sai số, mã NL, hàm lượng nhãn, hàm lượng thực tế, lượng trên 1.000) vì trường khác hẳn dòng bao bì; đầu phiếu dùng chung. | Thêm mới, không đụng cái cũ. |
| Phí gia công | Dòng loại *phí*: `part_code` = mã PĐG / PPT (mặt hàng phi kho), `qty_per_unit` = 1, `supplied_by` = NCC. | Cần SX-SP-07 trước. |
| Ba tầng BĐM | Thêm trên đầu phiếu `bom_kind` (1 BĐM VTBB, 2 BĐM BTP, 3 BĐM TP), `bom_code` (mã theo quy tắc), `base_qty` + `base_unit` (1 thành phẩm, hoặc 1.000 kg / lít). Hồ sơ HH tách khỏi đầu phiếu (đầu phiếu chỉ giữ `fg_code`). | Dữ liệu cũ nạp `bom_kind` = BĐM VTBB. |
| Phiên bản | Bỏ duy nhất trên `fg_code`; thay bằng duy nhất `(bom_kind, fg_code hoặc mã BTP, purpose, company_id, supplier_code, version_no)`. Thêm `version_no`, `is_current`, `prev_bom_id`, `change_reason`, `first_order_code`, `effective_from`. | Mọi truy vấn hiện tại phải thêm điều kiện `is_current`. Đây là thay đổi lớn nhất, cần kế hoạch chuyển dữ liệu. |
| Duyệt | Thêm `status` (1 nháp, 2 chờ duyệt, 3 đã duyệt, 4 ngưng), `approved_by`, `approved_at`; nối module `approval`. Bản đã duyệt khóa sửa. | Dữ liệu cũ nạp *đã duyệt* (đang dùng để tính giá) hoặc *nháp* (câu hỏi 16). |
| Nội bộ và thuế | Thêm `purpose` (1 nội bộ, 2 thuế), `company_id` (công ty cấu thành, 0 với bản nội bộ), `invoice_flow` (chuỗi luồng hóa đơn), `internal_bom_id` (bản thuế trỏ bản nội bộ). | Làm sau cùng. |
| NCC áp dụng | Thêm `supplier_code` trên đầu phiếu BĐM TP (rỗng = dùng chung mọi NCC). | Tùy câu hỏi 6. |

**Thứ tự làm gợi ý**: (1) số lượng + cách tính trên dòng, bỏ công thức cứng; (2) thêm loại bao bì và nhiều mã cùng loại; (3) bên cung ứng; (4) phiên bản + duyệt; (5) BĐM BTP; (6) BĐM TP gộp + dòng phí; (7) bản thuế. Bước 1-3 không đổi cách người dùng Thu mua đang dùng cụm giá.

**Tên gọi**: bảng đang mang tên *packaging* (bao bì) trong khi nội dung sẽ rộng hơn; đổi tên bảng là việc kỹ thuật, quyết sau. Trên màn hình nên đổi nhãn *Định mức bao bì* thành *Định mức sản phẩm* khi có tầng BTP và TP.

### 9.5 Khảo sát, cọc nhãn, mẫu

| Thực thể | Trường chính |
|---|---|
| Khảo sát công nghệ | mã yêu cầu, ngày tiếp nhận, bộ phận yêu cầu, mã VTBB, mã ruột, NCC GC, nội dung, hiện trạng VTBB, hiện trạng BTP, số mẫu gửi, yêu cầu trả, ngày dự kiến có kết quả, tiến độ, kết quả, đánh giá QLSX, ngày phản hồi KD, trạng thái |
| Cọc nhãn | NCC GC, mã HH, mã nhãn, tên pháp lý, thương hiệu, công ty ký, số lượng dự kiến, tiền cọc, hợp đồng (trỏ `tab_contract`), ngày hiệu lực, ngày hết hạn, ngày chuyển cọc, điều kiện hoàn, hiện trạng tồn nhãn, tiền hoàn, hình thức hoàn, văn bản thanh lý, ngày xử lý, trạng thái |
| Mẫu cho tặng | ngày, bộ phận yêu cầu, mục đích, đơn vị cho (tên, mã số thuế, người đại diện, điện thoại), mã / tên phía NCC, chất liệu, hình dạng, thông số, màu, ĐVT, số lượng, thời gian và hình thức nhận, người phụ trách, bốn việc (test, chụp, lưu, gửi), kết quả, đánh giá, tệp đính kèm, trạng thái |
| Chính sách theo NCC + nhóm vật tư | NCC GC, nhóm vật tư, % hao hụt cho phép, căn cứ, hiệu lực |

---

## 10. Liên kết với phần khác

| Phần | Sản phẩm cấp gì | Sản phẩm nhận gì |
|---|---|---|
| **Kho (SX-KHO)** | Mã hàng và ĐVT; ngưỡng Min / MOQ theo mã + kho; hàm bung BĐM để tính lượng xuất sản xuất (BTP theo lít / kg, VTBB theo cái); bảng đồng bộ mã DEGO - mã NCC để đối chiếu tồn; % hao hụt cho phép để so hao hụt thực tế. | Hàm lượng thực tế, số lô, NSX, HSD của lô NL / BTP (quyết định phiên bản BĐM BTP); tồn nhãn (theo dõi cọc nhãn); tồn theo kho NCC. |
| **Thu mua / Giá NVL sản xuất** | Mã hàng dùng trên YCMH, YCBG, ĐMH; tiêu chuẩn NL để hỏi hàng; định mức để biết đổi giá một mã thì sản phẩm nào đổi chi phí; lượng NL cần mua theo BĐM BTP. | Giá mua từng mã (sổ giá `tab_product_price_ledger`, báo giá `tab_product_price_quote`); tên trên hóa đơn; MOQ; thời gian mua theo phân loại (`tab_item_group`). Hai bên **dùng chung một bộ định mức** — không dựng định mức riêng cho Sản xuất. |
| **Giá vốn** | BĐM đã duyệt (số lượng, bên cung ứng) cho công thức giá vốn TP và BTP; mã PĐG, PPT; thể tích chốt đóng. | Trạng thái giá BTP (đang áp dụng / ngưng / giá mới chưa áp dụng); ô *Duyệt giá* trên phiếu BĐM. |
| **Đơn hàng gia công** | Hồ sơ HH; mã BĐM TP đúng phiên bản; dòng công thức phía NCC để ghi trên đơn; cấu thành; bộ tiêu chí KCS và phụ kiện theo mã HH; cảnh báo chưa khảo sát công nghệ, nhãn chưa duyệt. | Mã đơn đầu tiên phát sinh BĐM; yêu cầu lập BĐM khi đơn dùng tổ hợp mới; kết quả Lab của đơn. |
| **NCC gia công** | Danh mục sản phẩm hợp tác; kết quả khảo sát công nghệ; sổ cọc nhãn; dữ liệu cho tiêu chí 2.2-2.4, 3.1-3.2. | Phí phối, phí đóng gói theo dải thể tích; % hao hụt; chính sách cọc nhãn; mã và tên hàng phía NCC. |
| **Pháp lý** | Danh sách mã BTP, mã HH theo tên pháp lý; hàm lượng yêu cầu sản xuất. | Tên pháp lý, thành phần đăng ký, đơn vị đăng ký / thuê tên, hạn giấy; đơn vị cấu thành và luồng hóa đơn (cho BĐM thuế); ô *Duyệt pháp lý* trên phiếu BĐM. |
| **Sự cố sản xuất** | Công thức, BĐM, kết quả test của lô liên quan. | Phương án *chuyển thành hàng khác* (đổi mã HH) hoặc *tái chế BTP* (phải xác định lại công thức và pháp lý). |
| **Kế toán (Misa)** | Phiếu khai báo mã đã duyệt; bản BĐM thuế. | Mã đã tạo trên Misa. |

---

## 11. Câu hỏi cần phòng Sản xuất chốt

Danh sách câu hỏi của phần Sản phẩm đã gom về [`90-phu-luc-cau-hoi-phong-san-xuat.md`](90-phu-luc-cau-hoi-phong-san-xuat.md) mục B.

## 12. Phase, cách dùng, sheet thay thế, báo cáo

Thứ tự phase đã được chủ dự án duyệt ngày 26/11/2026 ([lộ trình](../plans/261126-lo-trinh-san-xuat-gia-cong/plan.md)): phần Sản phẩm làm ở **phase 1** (lõi) và **phase 3** (BOM đầy đủ).

### 12.1 Có những chức năng nào

| Nhóm chức năng | Làm được gì | Tính năng | Phase |
|---|---|---|---|
| Danh mục mã hàng | Một danh mục cho nguyên liệu, bán thành phẩm, vật tư bao bì, thành phẩm, mã phí; lọc theo loại mã; mỗi loại có thuộc tính riêng (hàm lượng, tỷ trọng, chất liệu, cổ chai, kích thước, thương hiệu, pháp nhân hóa đơn, NCC sản xuất) | SX-SP-01 … 09 | 1 |
| Sinh mã và tên theo quy tắc | Chọn loại mã, hệ tự sinh mã (`NAP0123`, `NHG4995`, `THI0164`...) và ghép tên nội bộ, tên hóa đơn theo mẫu; chặn khai trùng | SX-SP-10, 11, 12 | 1 |
| Khai báo mã mới có duyệt | Người đề nghị lập phiếu khai báo, bộ phận phụ trách duyệt, kế toán nhận để khai Misa | SX-SP-13, 18 | 1 (duyệt ở 3) |
| Đồng bộ mã DEGO - mã NCC | Một mã DEGO ứng với mã nào của từng NCC gia công; dùng khi đối chiếu tồn và công nợ | SX-SP-14 | 1 |
| Hồ sơ nhãn mác | Tình trạng in nhãn, NCC duyệt nhãn, ghi chú độc quyền, hình nhãn và mockup gắn mã | SX-SP-08, 16 | 1 |
| Định mức bao bì | Mỗi thành phẩm dùng chai, nắp, nhãn, hộp, nhãn thùng, thùng, vật tư khác nào, số lượng bao nhiêu, quy cách thùng, nhà máy đóng hàng; tra ngược *mã vật tư này dùng ở sản phẩm nào*; nhập / xuất Excel | SX-SP-28, 29, 30, 38, 39, 41 | 1 |
| Công thức BTP và test mẫu | Danh sách công thức (dòng công thức cho Kinh doanh khác dòng gửi NCC), theo dõi công thức mới, phiếu test mẫu và kết quả Lab, khung sai số hàm lượng và chiết rót | SX-SP-15, 17, 19 … 24, 43, 44 | 3 |
| BĐM BTP | Nguyên liệu cho 1.000 kg / lít BTP, tự tính theo hàm lượng yêu cầu, hàm lượng thực của lô nguyên liệu và tỷ trọng | SX-SP-25, 26, 27 | 3 |
| BĐM thành phẩm | Gộp BTP ruột + bao bì + phí gia công; mỗi dòng ghi công ty hay NCC cung ứng; bung ra nhu cầu vật tư cho một đơn | SX-SP-31, 32, 33, 42 | 3 |
| Phiên bản và duyệt định mức | Định mức có mã phiên bản (`_01`, `_02`), người duyệt, ngày duyệt, in phiếu ký; định mức chưa duyệt không dùng để xuất kho | SX-SP-34, 35, 37 | 3 |
| Bản thuế của định mức | Bộ cấu thành thuế song song bộ nội bộ | SX-SP-36 | sau (chờ nguồn) |
| Sổ phụ theo sản phẩm | Cọc nhãn, khảo sát công nghệ VTBB tại NCC, mẫu cho tặng, tiêu chí KCS, chính sách theo sản phẩm tại NCC | SX-SP-45 … 52 | sau |
| Chuyển dữ liệu ban đầu | Nhập Excel mã hàng, định mức, ánh xạ mã từ các sheet hiện có | SX-SP-54 | 0, 1 |

### 12.2 Dùng ra sao

| Ai | Việc hằng ngày trên ERP |
|---|---|
| Thiết kế | Khai mã hàng hóa mới (hệ sinh mã và tên), gắn hình nhãn / mockup, cập nhật tình trạng in nhãn |
| Điều phối VTBB | Khai chai, nắp, nhãn, thùng mới; lập định mức bao bì cho thành phẩm; tra *đổi chai này thì ảnh hưởng sản phẩm nào* |
| Điều phối NL / BTP | Khai nguyên liệu, BTP; lập BĐM BTP, hệ tự tính lượng nguyên liệu theo hàm lượng lô |
| QLDL | Duyệt mã mới, duyệt định mức, gộp BĐM thành phẩm, giữ bảng ánh xạ mã với NCC |
| Lab / R&D | Nhập kết quả test mẫu, chốt công thức |
| Giá vốn, Thu mua | Đọc định mức và giá để tính chi phí (màn Tác động giá bao bì đã có dùng chính định mức này) |
| Kinh doanh | Tra mã, quy cách, tình trạng sản phẩm; chỉ thấy dòng công thức dành cho Kinh doanh |
| Kế toán | Nhận danh sách mã mới đã duyệt để khai Misa |

### 12.3 Thay được sheet nào

| Tệp | Sheet thay được | Phase |
|---|---|---|
| QUẢN LÝ NHÃN MÁC IDA GROUP | DANH SÁCH TỔNG, QUY TẮC ĐẶT MÃ, Bang chi tiet dinh muc (và bản 2023), DM CHAI, DM TÚINHÃN, DM THÙNG, DM VTBB, DM NSX, DATA | 1 |
| DRIVE ĐẦU VÀO SX | Admin, Data HH, Data NLBTP, Data VTBB, Data đồng bộ NCC GC, Nháp chung | 1 |
| 5 tệp khác | Các bản chép danh mục: *DATA 1*, *Data1*, *Data 1 (mới)*, *DATA MỚI*, *Quản lý nhãn mác* (ở Pháp lý, Điều phối, Giá vốn 1 và 2, hai tệp Xuất nhập tồn) | 1 |
| 4. XUẤT NHẬP TỒN - VTBB | DATA 2, KHAI BÁO VTBB, BDM VTBB, 9. Phiếu BDM VTBB TP | 1 |
| 3. XUẤT NHẬP TỒN NL, BTP | QUY TẮC, 1.1 DS và dòng công thức BTP, 2. Theo dõi công thức mới, 2.1 Theo dõi test mẫu, 3. BDM BTP, 3.1 Tính lượng NL và giá BTP | 3 |
| Drive QLDL 2 và 4 | BĐM VTBB, BĐM BTP (2); BĐM BTP, BĐM VTBB, BDM TP (4) | 1 (VTBB), 3 (BTP, TP) |
| Drive QL Giá vốn 1 và 2 | BDM TP | 3 |
| 4. XUẤT NHẬP TỒN - VTBB | KHẢO SÁT CÔNG NGHỆ VTBB, CỌC NHÃN VTBB, MẪU CHO TẶNG VTBB | sau |

Lợi trực tiếp: danh mục mã và định mức chỉ còn **một nơi**, các bộ phận không phải chép qua 5–6 tệp.

### 12.4 Báo cáo và tra cứu

| Báo cáo / tra cứu | Dùng để | Tính năng |
|---|---|---|
| Danh sách mã theo loại, thương hiệu, NCC sản xuất, tình trạng | Thay việc lọc sheet DANH SÁCH TỔNG | SX-SP-01, 05 |
| Mã thiếu thông tin, định mức thiếu thành phần hoặc thiếu quy cách thùng | Dọn dữ liệu trước khi dùng cho kho và đơn hàng | SX-SP-41 |
| Tra ngược vật tư dùng ở sản phẩm nào | Đổi mẫu chai, đổi NCC bao bì, ngưng mã | SX-SP-39 |
| Chi phí định mức của một thành phẩm (theo chai và theo thùng) | Đã có ở màn *Tác động giá bao bì*; mở rộng khi có BTP và phí gia công | SX-SP-40 |
| Định mức chờ duyệt, định mức theo phiên bản | Kiểm soát thay đổi định mức | SX-SP-34, 35 |
| Phiếu in BĐM có chữ ký | Thay phiếu BĐM in từ sheet | SX-SP-37 |
| Tình trạng nhãn (đã in, chưa in, tạm ngưng, độc quyền) | Thiết kế và Kinh doanh | SX-SP-16 |
| Lịch sử thay đổi mã và định mức | Ai sửa gì, khi nào | SX-SP-53 |
| Dữ liệu VTBB cho Kinh doanh | Kinh doanh tra bao bì, kích thước nhãn | SX-SP-52 |

### 12.5 Bổ sung từ sổ Quản lý nhãn mác (dữ liệu thật)

Sổ *QUẢN LÝ NHÃN MÁC IDA GROUP* của Thiết kế nhận ngày 26/11/2026 là dữ liệu đang dùng thật (chi tiết ở
[`nghien-cuu/21`](../nghien-cuu/21-so-quan-ly-nhan-mac-ida-group.md)). Ba điểm bổ sung cho phần này:

1. **Danh mục hàng hóa có 11.150 mã HH** (không phải khoảng sáu nghìn dòng như các bản chép): phân bón 4.293, thuốc trừ sâu
   3.243, thuốc trừ bệnh 2.896, còn lại là thuốc trừ cỏ, chế phẩm diệt côn trùng, thuốc trừ ốc, điều hòa sinh trưởng; 38 NCC
   sản xuất. Đây là nguồn nạp ban đầu cho SX-SP-01, SX-SP-05, SX-SP-16.
2. **Bảng quy tắc đặt mã bản 31/03/2026** là bản gốc mới nhất của mục 4.1, có thêm cột bộ phận khai báo: Thiết kế khai mã
   HH; Điều phối VTBB khai chai, nắp, nhãn, hộp, thùng, nhãn dán thùng; Thu mua khai nguyên liệu, BTP nhập khẩu, BTPR, chi phí
   nhập khẩu; QLDL khai BTPM; Điều phối khai BTPCT, PPT, PĐG. Dùng cho SX-SP-10, SX-SP-13.
3. **Định mức bao bì thật của 4.189 mã HH có 9 ô thành phần**: chai, nắp, nhãn / túi, **hộp**, nhãn dán thùng, thùng,
   **VTBB khác 1–3** (cốc đong, seal...), kèm quy cách thùng và nhà máy đóng hàng. Số mã đã có mã vật tư theo loại: nhãn
   4.121, thùng 3.765, nhãn dán thùng 3.468, chai 3.093, nắp 2.598, VTBB khác 548, hộp 68. Vì vậy SX-SP-29 (*mở rộng loại
   thành phần và nhiều mã cùng loại*) phải có tối thiểu hai loại mới *Hộp* và *Vật tư khác*; đây cũng là nguồn nạp thay
   1.000 dòng định mức mẫu (SX-SP-28, SX-SP-54).

## Phụ lục — Nguồn đã đọc

| Tệp | Sheet đã dùng |
|---|---|
| `Bản sao của 3. XUẤT NHẬP TỒN NL, BTP.xlsx` | QUY TẮC; QUẢN LÝ NHÃN MÁC; 0. Mục lục; Data 1 (cũ và mới); 1.1 DS và dòng công thức BTP; 2. Theo dõi công thức mới; 2.1 Theo dõi test mẫu; 3. BDM BTP; 3.1 Tính lượng NL và giá BTP; 3.2 Khảo sát giá NL/BTP |
| `4. XUẤT NHẬP TỒN - VTBB.xlsx` | HƯỚNG DẪN; DATA 2; KHAI BÁO VTBB; PYC KHẢO SÁT VTBB; TRẢ KQ KHẢO SÁT VTBB; KHẢO SÁT CÔNG NGHỆ VTBB; CỌC NHÃN VTBB; MẪU CHO TẶNG VTBB; THÔNG TIN; BDM VTBB; 9. Phiếu BDM VTBB TP |
| `Drive QLDL (mới)\4. BDM thành phẩm.xlsx` | BDM TP; Phiếu in LSX; LSX TP (qua ghi chú nhóm B) |
| `Drive QLDL (mới)\2. Đầu vào nội bộ QLDL.xlsx`, `1. ĐẦU VÀO NCC GC.xlsx`, `3. Duyệt đơn hàng QLDL.xlsx` | BĐM VTBB, BĐM BTP, XK SX BTP, XK SX VTBB; Phí phối, Phí đóng gói; khối duyệt đơn (qua ghi chú nhóm B) |
| `Drive QL Giá vốn\1. ĐẦU VÀO GIÁ VỐN.xlsx` | BDM TP, Quản lý nhãn mác, công thức giá (qua ghi chú nhóm C) |
| `QUY TRÌNH SẢN XUẤT 09.07.2026.xlsx` | 1. QT làm việc với NCC mới; 2. QT khai báo SX; 2.1 QT khai báo mã yêu cầu đặt; 7. QT BĐM thuế; 8. QT QL NLBTP; 9. QT QL VTBB; 19. Tiêu chí đánh giá NCC GC (qua ghi chú nhóm A) |
| `DRIVE ĐẦU VÀO SX 11.09.2026 (chốt).xlsx` | Admin, Data NL/BTP, Data VTBB, Data đồng bộ NCC GC, Data QLDL, Data HH (qua ghi chú nhóm A) |
| `CHECKLIST NCC GC MỚI.xlsx`, `ĐÁNH GIÁ ĐỊNH KÌ NCC GC.xlsx` | Mẫu 01, Mẫu 02; bảng tiêu chí và thang điểm (qua ghi chú nhóm B) |
| Mã ERP nhánh `erp-v2` | `backend/app/modules/product`, `catalog`, `packaging_cost`, `product_price`; `backend/app/core/packaging_price_codes.py`; `doc/erp/mat-hang/`; `doc/erp/thu-mua/chuc-nang/21-tac-dong-gia-bao-bi.md` |
