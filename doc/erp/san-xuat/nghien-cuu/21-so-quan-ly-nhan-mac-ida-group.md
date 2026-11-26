# Sổ Quản lý nhãn mác IDA GROUP: danh mục hàng hóa, quy tắc mã và định mức bao bì thật

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 26/11/2026 | NSU209 (A1 Điều phối) | Nháp | — |

Nguồn: tệp `QUẢN LÝ NHÃN MÁC IDA GROUP.xlsx` (23 sheet, 9 MB), sổ của bộ phận **Thiết kế** và **Điều phối VTBB**, nhận ngày
26/11/2026. Tệp gốc để ở thư mục `tailieusanxuat` ngoài repo (không đưa vào repo vì chứa dữ liệu kinh doanh).

## 1. Vì sao tệp này quan trọng

Khác với các tệp quy trình của phòng Sản xuất (dữ liệu mô phỏng, xem [`15`](15-tong-hop-13-quy-trinh-san-xuat.md)), đây là
**sổ đang dùng thật, có dữ liệu thật nhiều năm** (nhập kho nhãn từ 2018–2021, tồn kho tới 2024, quy tắc mã cập nhật
31/03/2026). Nó là **nguồn gốc** của ba thứ mà phần Sản phẩm cần:

| Thứ cần | Sheet | Quy mô |
|---|---|---|
| Danh mục hàng hóa (mã HH) kèm thuộc tính | *DANH SÁCH TỔNG* | 11.150 mã HH |
| Quy tắc đặt mã nội bộ | *QUY TẮC ĐẶT MÃ* | 15 nhóm loại mã, bản 31/03/2026 |
| Định mức vật tư bao bì theo mã HH | *Bang chi tiet dinh muc* | 4.526 mã HH, trong đó 4.189 mã đã có ít nhất một mã VTBB |

Các sheet *Quản lý nhãn mác* trong tệp `3. XUẤT NHẬP TỒN NL, BTP`, `1. ĐẦU VÀO GIÁ VỐN`, `2. DUYỆT ĐƠN HÀNG BTP VÀ TP` đều
kéo dữ liệu từ sheet *DANH SÁCH TỔNG* của tệp này.

## 2. Kiểm kê sheet

| Sheet | Loại | Dòng có dữ liệu | Nội dung |
|---|---|---|---|
| DANH SÁCH TỔNG | Danh mục gốc | 11.150 | Mỗi dòng một mã HH: tình trạng, khách hàng / thương hiệu, công ty phân phối, pháp nhân hóa đơn, dòng sản phẩm, tên đăng ký, nguyên liệu (màu, dạng), nhãn hiệu, NCC sản xuất, quy cách, bao bì, kích thước nhãn / thùng, link hình, tồn nhãn, hoạt chất |
| QUY TẮC ĐẶT MÃ | Quy tắc | 24 | *Quy tắc quản lý mã nội bộ*, cập nhật 31/03/2026 |
| Bang chi tiet dinh muc | Định mức | 4.526 | Định mức VTBB theo mã HH, bản đang dùng |
| Bang chi tiet dinh muc 2023 | Định mức (bản cũ) | khoảng 2.650 | Bản 2023, ít cột hơn |
| DM CHAI | Danh mục | 574 | Chai, nắp: mã, tên, thương hiệu, dung tích, trọng lượng, cổ chai, màu, chất liệu, kích thước nhãn, hình |
| DM TÚINHÃN | Danh mục | khoảng 5.990 | Túi, nhãn theo mã HH: phân loại, mã VTBB, bao bì chứa, chất liệu, nơi giao, công ty nhận hóa đơn |
| DM THÙNG | Danh mục | 329 | Thùng: mã, tên, tình trạng (có ghi *đổi thành mã khác*), thương hiệu, NCC, kích thước lọt lòng, chất liệu |
| DM VTBB | Danh mục phụ | 54 | Mẫu VTBB chuẩn theo nhà máy và kích thước nhãn tương ứng |
| DM NSX | Danh mục | 34 | Đơn vị sản xuất / gia công / đóng gói: tên, tên viết tắt, địa chỉ |
| DATA | Danh mục | 351 | Dữ liệu sản phẩm theo tên đăng ký: loại, mẫu VTBB, mockup, giấy phép, hợp quy, màu nguyên liệu, hạn sử dụng, hoạt chất, công dụng, HDSD, đơn vị đăng ký, đơn vị sản xuất |
| ĐỊNH MỨC TỒN | Định mức tồn | 49 | Tồn hàng tối thiểu, tồn nhãn tối thiểu, tồn tối đa, số đặt tối thiểu theo mã HH |
| NHẬP KHO NHÃN MÁC | Sổ nhập | 508 | Ngày đặt, ngày về dự kiến, ngày nhập, mã, số lượng, đơn giá, NCC VTBB, chất lượng, công nợ |
| NHẬP KHO NHÃN MÁC-2021 | Sổ nhập (cũ) | 30 | Bản 2021 |
| XUẤT KHO NHÃN MÁC | Sổ xuất | khoảng 2.630 | Dán từ chứng từ kế toán: ngày hạch toán, số chứng từ, NCC, mã hàng, số lượng |
| BÁO CÁO TỒN KHO NHÃN MÁC | Báo cáo | khoảng 1.060 | Tồn đầu, nhập, xuất, tồn cuối theo mã HH và theo thùng; nhiều ô lỗi công thức |
| Trang tính65 | Báo cáo | 46 | Tổng hợp tồn kho nhãn / túi tại một kho tới 18/05/2024, có đơn giá, thành tiền |
| Trang tính25 | Báo cáo | 130 | Tồn nhãn theo mã HH kèm hình nhãn 2D, mockup |
| Trang tính44 | Biểu mẫu | khung | Mẫu đơn đặt hàng VTBB gửi NCC |
| Trang tính62, QC | Phụ | vài dòng | Kích thước hộp / thùng mẫu; chuẩn hóa cách ghi quy cách |
| DM KHÁCH HÀNG, DM VTBB PB, Trang tính55 | Trống / vỡ liên kết | — | Bỏ qua |

## 3. Danh mục hàng hóa (sheet DANH SÁCH TỔNG)

Phân bố 11.150 mã HH theo dòng sản phẩm: Phân bón 4.293 · Thuốc trừ sâu 3.243 · Thuốc trừ bệnh 2.896 · Thuốc trừ cỏ 329 ·
Chế phẩm diệt côn trùng 133 · Thuốc trừ ốc 46 · Thuốc điều hòa sinh trưởng 15 · chưa ghi 193. Có 38 NCC sản xuất (viết tắt),
nhiều nhất là HL, BATS, AGA, DEGO.

Các trường của một mã HH:

| Nhóm | Trường |
|---|---|
| Định danh | Mã HH (có hậu tố `.1`, `.2` cho biến thể), tên sản phẩm ghép tự động, tình trạng (*đã in*, *chưa in*, *tạm ngưng*, *ngưng KD*, *mua thành phẩm*, ghi chú độc quyền) |
| Thương mại | Khách hàng / thương hiệu, công ty phân phối, đại diện pháp lý xuất hóa đơn đầu ra, công ty nhận hóa đơn đầu vào, NCC sản xuất |
| Sản phẩm | Dòng sản phẩm, tên đăng ký (tên pháp lý), nguyên liệu (dạng + màu, ví dụ *nước đỏ*, *bột trắng*), tên nhãn hiệu nội bộ, hoạt chất, trọng lượng |
| Quy cách | Quy cách sản phẩm (25ml, 500gr, 20L), quy cách thùng, quy cách bao, ĐVT chính (Chai, Túi/Gói, Lon, Can) |
| Bao bì | Chất liệu bao bì chứa, chất liệu nhãn, kích thước nhãn, loại thùng, kích thước thùng, có nhãn dán thùng, có hộp giấy |
| Mã VTBB gắn với HH | Chai / xô / can / lon, nhãn chai / túi, túi, thùng, nhãn dán thùng, nắp, hộp |
| Hình | Link hình VTBB, hình nhãn |
| Tồn nhãn | Ngày cập nhật tồn đầu kỳ, tồn đầu kỳ (chưa trừ hao hụt 5–10%), phát sinh nhập, phát sinh xuất, tồn cuối theo đơn vị lẻ và theo thùng, tồn tối thiểu |

## 4. Quy tắc đặt mã (bản 31/03/2026)

Bảng quy tắc ở sheet *QUY TẮC ĐẶT MÃ* có đủ: mã, cách ghép tên nội bộ, tên trên hóa đơn, bộ phận khai báo, ví dụ, cách
thực hiện. Nội dung khớp với mục 4.1 của [`chuc-nang/11-san-pham.md`](../chuc-nang/11-san-pham.md); tệp này là **bản gốc
mới nhất**, bổ sung cột *bộ phận khai báo*:

| Loại | Mã | Bộ phận khai báo |
|---|---|---|
| Hàng hóa | `HH` + 4 số | Thiết kế |
| Túi / nhãn chai / nhãn túi | `N` + mã chất liệu + 4 số cuối mã HH | Điều phối VTBB |
| Chai | `C` + chất liệu + hình dạng + số chạy | Điều phối VTBB |
| Nắp, cốc, seal | `NAP`, `COC`, `SEAL` + 4 số | Điều phối VTBB |
| Hộp | `HOP` + 4 số cuối mã HH | Điều phối VTBB |
| Xô, can, lon | `XO` + chữ đầu màu + số; `CAN`; `LON` | Điều phối VTBB |
| Thùng | `TH` + chữ thương hiệu + 4 số | Điều phối VTBB |
| Nhãn dán thùng | `NDT` + 4 số cuối mã HH | Điều phối VTBB |
| Nguyên liệu | `NLNK`, `NLT`, `NA` + 4 số | Thu mua |
| Bán thành phẩm | `BTPNK`, `BTPR` (Thu mua), `BTPM` (QLDL), BTP từ R&D theo mã công thức Lab + ngày (Kế toán) | theo loại |
| Chi phí | `CPNK` (Thu mua); `BTPCT`, `PPT`, `PĐG` (Điều phối) | theo loại |

Cách khai chung: bộ phận tạo mã trên Drive của mình, gửi lên nhóm khai báo, kế toán khai vào Misa.

## 5. Định mức vật tư bao bì thật (sheet Bang chi tiet dinh muc)

Mỗi dòng một mã HH, gồm ba phần:

| Phần | Cột | Cách nhập |
|---|---|---|
| Thông tin sản phẩm | Mã HH, tên nội bộ, tên pháp lý, quy cách chai / gói, quy cách thùng, mô tả | Chép từ nhóm khai báo sản phẩm và công thức kéo từ *DANH SÁCH TỔNG* |
| Mô tả bao bì | Chai / túi / xô, nắp, nhãn, nhãn dán thùng, hộp, thùng, VTBB khác 1–3 | Chọn / nhập |
| **Mã vật tư bao bì** | Chai, Nắp, Nhãn chai / Túi, Hộp, NDT, Thùng, VTBB khác 1, 2, 3 | Công thức tra theo mô tả |
| Nơi đóng | Nhà máy đóng hàng | Nhập |

Số mã HH đã có mã cho từng loại: nhãn / túi 4.121 · thùng 3.765 · nhãn dán thùng 3.468 · chai 3.093 · nắp 2.598 · VTBB
khác (cốc, seal...) 548 · hộp 68. Ví dụ: `HH0223.1` dùng chai `CNT0033`, nắp `NAP0024`, nhãn `NHG0223.1`, nhãn dán thùng
`NDT0223.1`, thùng `THI0006`, quy cách 60 chai / thùng, đóng tại BATS.

**So với định mức bao bì của ERP** (`tab_packaging_bom` + `tab_packaging_bom_part`, cụm Giá nguyên vật liệu sản xuất):

| Điểm | Sổ nhãn mác | ERP hiện có |
|---|---|---|
| Loại thành phần | 9 ô: chai, nắp, nhãn / túi, **hộp**, nhãn dán thùng, thùng, **VTBB khác 1–3** | 5 loại: chai, nắp, nhãn, nhãn thùng, thùng |
| Quy cách thùng | Có (QC thùng) | Có (`carton_qty`) |
| Nhà máy đóng hàng | Có | Chưa |
| Số mã HH | 4.189 mã có định mức thật | 1.000 dòng mẫu trên dev |
| Biến thể mã | `HH0223.1` | Mã là chuỗi nên nhận được |

Hệ quả: đây là **nguồn định mức thật** để nạp vào ERP thay 1.000 dòng mẫu; muốn nạp đủ thì cần thêm loại thành phần *Hộp*
và *VTBB khác* (cốc đong, seal...), đúng hướng tính năng SX-SP-29 (*mở rộng loại thành phần và nhiều mã cùng loại*).

## 6. Kho nhãn mác

Sổ này quản riêng tồn **nhãn / túi** (vật tư do Thiết kế đặt in):

- Nhập: ngày đặt NCC, ngày về dự kiến, ngày nhập, số lượng nhãn, số thùng tương ứng, đơn giá, NCC VTBB, chất lượng, công nợ.
- Xuất: lấy từ chứng từ kế toán (ngày hạch toán, số chứng từ, mã hàng, số lượng).
- Tồn: tồn đầu kỳ (ghi chú *chưa trừ hao hụt 5–10%*) + nhập − xuất, hiển thị theo đơn vị lẻ và quy ra số thùng thành phẩm
  đóng được; có tồn tối thiểu theo thùng.
- Định mức tồn: tồn hàng tối thiểu, tồn nhãn tối thiểu, tồn tối đa, số đặt tối thiểu theo mã HH (49 mã).

Các sổ nhập / xuất dừng ở 2021–2023 nên là dữ liệu lịch sử; việc theo dõi tồn VTBB hiện hành nằm ở tệp
`4. XUẤT NHẬP TỒN - VTBB` (xem [`chuc-nang/12-kho.md`](../chuc-nang/12-kho.md)).

## 7. Dùng tệp này vào đâu

| Tính năng | Dùng sheet | Ghi chú |
|---|---|---|
| SX-SP-01, 05 Danh mục mã hàng, hồ sơ thành phẩm | DANH SÁCH TỔNG | Nguồn nạp ban đầu 11.150 mã HH và thuộc tính |
| SX-SP-04, 06 Thuộc tính VTBB, danh mục dùng chung | DM CHAI, DM TÚINHÃN, DM THÙNG, DM NSX | Nguồn nạp danh mục VTBB và đơn vị sản xuất |
| SX-SP-10, 11 Sinh mã và tên theo quy tắc | QUY TẮC ĐẶT MÃ | Bản quy tắc gốc mới nhất |
| SX-SP-16 Quản lý nhãn mác | DANH SÁCH TỔNG (tình trạng, độc quyền, hình) | |
| SX-SP-28, 29, 30 BĐM VTBB, mở rộng loại thành phần | Bang chi tiet dinh muc | Nguồn định mức thật thay dữ liệu mẫu |
| SX-SP-54 Chuyển dữ liệu ban đầu | Cả tệp | |
| SX-KHO-05, 47 Min / MOQ, đề xuất đặt | ĐỊNH MỨC TỒN | Mẫu cách tính tồn nhãn tối thiểu theo thùng |

## 8. Câu hỏi

Đã gom về [`chuc-nang/90`](../chuc-nang/90-phu-luc-cau-hoi-phong-san-xuat.md) mục D.
