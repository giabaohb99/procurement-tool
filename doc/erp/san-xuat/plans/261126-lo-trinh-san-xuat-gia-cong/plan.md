---
title: "Lộ trình phân hệ Sản xuất gia công: làm phần nào trước"
description: "Thứ tự các phase (không ước thời gian) và mô tả hai module viết chi tiết trước: Sản phẩm và Kho — chức năng, cách dùng, thay sheet nào, báo cáo nào"
status: pending
priority: P1
branch: erp-v2
tags: [san-xuat, san-pham, kho, bom, lo-trinh]
created: 2026-11-26
---

# Lộ trình phân hệ Sản xuất gia công

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 26/11/2026 | NSU209 (A1 Điều phối) | Nháp, chờ chủ dự án duyệt thứ tự | — |

Tệp này trả lời ba câu: **làm phần nào trước**, **hai module Sản phẩm và Kho gồm những chức năng gì, dùng ra sao**, và
**thay được sheet nào, báo cáo nào** của phòng Sản xuất. Không ước thời gian. Chi tiết từng tính năng (mã SX-SP, SX-KHO) ở
[`chuc-nang/11-san-pham.md`](../../chuc-nang/11-san-pham.md) và [`chuc-nang/12-kho.md`](../../chuc-nang/12-kho.md); bảng
tổng ở [`chuc-nang/01`](../../chuc-nang/01-yeu-cau-chuc-nang.md).

## 1. Nguyên tắc xếp thứ tự

1. **Dữ liệu gốc trước, nghiệp vụ sau.** Kho cần mã hàng; đơn gia công cần định mức và tồn; giá vốn cần định mức và giá mua;
   sự cố cần đơn hàng và kho lỗi.
2. **Mỗi phase là một lát cắt dùng được ngay**, thay được một nhóm sheet cụ thể, không chờ làm hết mới dùng.
3. **Mở rộng phần đang có, không làm lại**: danh mục sản phẩm, kho, định mức bao bì (cụm Giá nguyên vật liệu sản xuất),
   bộ máy duyệt, nhập Excel, in phiếu đã có trên ERP.
4. **Mỗi phase xong khi số liệu ERP khớp sheet của phòng Sản xuất** trên cùng dữ liệu đầu vào (mục 5).

## 2. Các phase

| Phase | Làm gì | Module | Cần phase trước | Xong khi |
|---|---|---|---|---|
| **0. Chuẩn bị** | Phòng Sản xuất chốt câu hỏi chặn ([`01`](../../chuc-nang/01-yeu-cau-chuc-nang.md) mục 4); nạp thử dữ liệu thật từ sổ Quản lý nhãn mác lên dev (11.150 mã hàng hóa, 4.189 định mức bao bì) | Sản phẩm | — | Có câu trả lời về lô, tồn theo thương hiệu, tồn nội bộ / thuế, quy tắc mã; dữ liệu thật nạp được, đếm lỗi |
| **1. Sản phẩm lõi** | Danh mục mã hàng theo loại, thuộc tính, quy tắc sinh mã, ánh xạ mã DEGO - mã NCC, định mức bao bì có số lượng và đủ loại thành phần | Sản phẩm | 0 | Thiết kế và Điều phối VTBB khai mã, khai định mức trên ERP thay sổ nhãn mác |
| **2. Kho lõi (VTBB)** | Danh mục kho (kể cả kho tại NCC gia công), loại giao dịch, nhập, xuất ngoài sản xuất, chuyển kho, tồn ba nhóm, sổ giao dịch, giá trị tồn, Min / MOQ | Kho | 1 | Tồn VTBB trên ERP khớp sheet *TỒN KHO* của tệp Xuất nhập tồn VTBB |
| **3. Sản phẩm mở rộng (BOM đầy đủ)** | Công thức BTP, test mẫu, BĐM BTP, BĐM thành phẩm gộp (ruột + bao bì + phí gia công), bên cung ứng, phiên bản, duyệt định mức | Sản phẩm | 1 | Lượng nguyên liệu tính theo hàm lượng khớp sheet *BDM BTP*; định mức có phiên bản và người duyệt |
| **4. Kho cho sản xuất** | NL / BTP theo lô, nhập tạm chờ kiểm, phối BTP, xuất theo đơn thành phẩm và định mức, giữ hàng, kho lỗi, hao hụt, tồn theo kỳ, đối chiếu tồn với NCC gia công | Kho | 2, 3 | Tồn NL / BTP khớp sheet *Tồn kho chi tiết / tổng*; chạy được một kỳ đối chiếu với một NCC |
| **5. Đơn hàng gia công** | Kinh doanh lên đơn, duyệt 7 bộ phận, gửi NCC, tiến độ, lệnh sản xuất, KCS, nhận thành phẩm, xuất bán | Đơn hàng (mới) | 3, 4 | Một đơn đi trọn từ lên đơn tới nhập kho thành phẩm, kho tự trừ theo định mức |
| **6. Sự cố sản xuất** | Ghi nhận, phân nhóm lỗi, yêu cầu xử lý lại, chi phí, trách nhiệm, chỉ số NCC | Sự cố (mới) | 4, 5 | Sự cố gắn được với đơn và kho lỗi, ra báo cáo theo khung BC SỰ CỐ SX |
| **7. Giá vốn và công nợ NCC gia công** | Giá vốn thành phẩm từ định mức + giá mua + phí gia công; công nợ ngoài đơn mua (lưu kho, hao hụt, phạt), đối chiếu công nợ | Giá vốn, Công nợ | 3, 4, 5 | Giá vốn một thành phẩm khớp phiếu duyệt giá của phòng |
| **8. NCC gia công và báo cáo tổng** | Đưa NCC vào hợp tác, đánh giá định kỳ, ngưng hợp tác, bảng định mức thuế, vận chuyển, báo cáo điều hành | NCC gia công, Báo cáo | 5, 6 | — |
| **Chen được bất kỳ lúc nào** | **Pháp lý sản phẩm**: hồ sơ ủy quyền, giấy đăng ký, hợp quy, cảnh báo hết hạn 180 ngày | Pháp lý (mới, đứng riêng) | 1 | Nạp 369 dòng hồ sơ thật, có danh sách sắp hết hạn |

Phase 1–4 là hai module viết chi tiết trước (Sản phẩm, Kho), mô tả ở mục 3 và 4. Phase 5–8 mới có nguồn nghiên cứu
([`nghien-cuu/15`](../../nghien-cuu/15-tong-hop-13-quy-trinh-san-xuat.md) … [`19`](../../nghien-cuu/19-dieu-phoi-thanh-pham-va-su-co.md)),
chưa viết tài liệu chức năng.

## 3. Module Sản phẩm

### 3.1 Có những chức năng nào

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

### 3.2 Dùng ra sao

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

### 3.3 Thay được sheet nào

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

### 3.4 Báo cáo và tra cứu

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

## 4. Module Kho

### 4.1 Có những chức năng nào

| Nhóm chức năng | Làm được gì | Tính năng | Phase |
|---|---|---|---|
| Danh mục kho và loại giao dịch | Kho DEGO, kho tại từng NCC gia công (mỗi NCC một kho thường và một kho lỗi), kho thương mại; danh mục loại nhập / xuất để mọi phiếu ghi cùng một cách | SX-KHO-01, 02, 06 | 2 |
| Tồn theo thương hiệu | Tồn ghi theo Kho + Thương hiệu + Mã hàng (nếu phòng Sản xuất chốt giữ cách này) | SX-KHO-03 | 2 |
| Số dư đầu kỳ | Nhập tồn đầu kỳ từ sheet hiện có bằng Excel | SX-KHO-07 | 2 |
| Nhập kho | Nhập từ đơn mua hàng của Thu mua (đã có), nhập khác (đổ thu, dư sau sản xuất, cho tặng) | SX-KHO-08, 12 | 2 |
| Xuất ngoài sản xuất, chuyển kho | Phiếu đề nghị xuất, chuyển giữa kho DEGO và kho NCC, giữa các NCC; chặn xuất âm kho | SX-KHO-19, 21, 22 | 2 |
| Tồn và sổ giao dịch | Tồn tức thời ba nhóm (thực tế, tạm, lỗi), tồn có thể sản xuất, sổ giao dịch từng mã (thẻ kho), giá trị tồn theo đơn giá bình quân | SX-KHO-29, 31, 33 | 2 |
| Min, MOQ và đề xuất đặt | Khai tồn an toàn và số đặt tối thiểu theo mã + kho; hệ đề xuất số cần đặt và chuyển thành yêu cầu mua hàng sang Thu mua | SX-KHO-05, 36, 47 | 2 |
| NL / BTP theo lô | Nhập theo số lô, ngày sản xuất, hạn sử dụng, kết quả Lab; nhập tạm chờ kiểm duyệt; tồn chi tiết theo lô | SX-KHO-09, 10, 30 | 4 |
| Phối BTP | Lệnh phối: xuất nguyên liệu theo BĐM BTP, nhập BTP sau phối | SX-KHO-11 | 4 |
| Xuất cho sản xuất theo đơn | Đơn duyệt thì giữ hàng (xuất tạm); mỗi lần NCC có thành phẩm thì trừ tồn thực tế = định mức x số thành phẩm; kiểm đủ vật tư cho đơn; hủy đơn thì hoàn giữ hàng | SX-KHO-14 … 20 | 4 |
| Thành phẩm | Nhập thành phẩm từ NCC, chuyển về kho, trả hàng, tồn thành phẩm tại NCC | SX-KHO-13, 37 | 4 (cùng phase 5) |
| Hàng lỗi và hao hụt | Chuyển sang kho lỗi theo trạng thái (nghi lỗi, chờ phương án, chờ xử lý lại), xuất hủy, ghi hao hụt, đưa vào chi phí | SX-KHO-24, 25, 26 | 4 |
| Đối chiếu tồn với NCC gia công | Nạp tệp tồn NCC gửi, hệ tự so theo mã + kho với dung sai hao hụt, lưu lịch sử chênh lệch và cách xử lý, in biên bản | SX-KHO-04, 38 … 42 | 4 |
| Kỳ kho | Chốt kỳ, tồn theo kỳ, phí lưu kho và hao hụt NCC tính | SX-KHO-32, 43, 44 | 4 |
| Phiếu in | Phiếu đề nghị nhập, xuất, chuyển, xuất bán nội bộ, đưa vào chi phí | SX-KHO-23, 28 | 2 (mẫu cơ bản), 4 |
| Hai góc nhìn tồn, tồn thuế | Tồn BTP theo Sản xuất và theo Kinh doanh; tồn nội bộ và tồn thuế | SX-KHO-34, 35 | sau (chờ chốt) |

### 4.2 Dùng ra sao

| Ai | Việc hằng ngày trên ERP |
|---|---|
| Điều phối VTBB | Nhận hàng mua về kho NCC (từ đơn mua hàng), lập phiếu chuyển kho, xuất ngoài sản xuất; xem tồn và cảnh báo dưới Min; bấm tạo yêu cầu mua hàng từ số đề xuất |
| Điều phối NL / BTP | Nhập nguyên liệu, BTP theo lô; lập lệnh phối; kiểm đủ BTP cho đơn |
| Điều phối thành phẩm | Ghi lần NCC có thành phẩm (hệ tự trừ VTBB, BTP theo định mức); nhập thành phẩm; chuyển hàng lỗi |
| QLDL | Nạp tệp tồn NCC gửi cuối kỳ, xem bảng chênh lệch, ghi cách xử lý, in biên bản; chốt kỳ |
| Kế toán | Xem giá trị tồn, phiếu xuất bán nội bộ, phiếu đưa vào chi phí |
| Kinh doanh | Tra tồn thành phẩm và tồn BTP có thể đóng hàng |
| Thu mua | Nhận yêu cầu mua hàng sinh từ đề xuất đặt; nhận hàng như hiện nay |

### 4.3 Thay được sheet nào

| Tệp | Sheet thay được | Phase |
|---|---|---|
| 4. XUẤT NHẬP TỒN - VTBB | NHẬP KHO VTBB, XUẤT KHO VTBB NGOÀI SX, TỒN KHO, THÔNG TIN (Min / MOQ), các phiếu đề nghị xuất / nhập / chuyển / xuất bán nội bộ / đưa vào chi phí | 2 |
| 4. XUẤT NHẬP TỒN - VTBB | XUẤT KHO VTBB SX, TỒN KHO THEO KỲ, DỮ LIỆU NCC, ĐỐI CHIẾU NCC, ĐỐI CHIẾU CÁC LẦN, LỊCH SỬ ĐỐI CHIẾU, LỊCH SỬ TỪ SỰ CỐ | 4 |
| BC VTBB (cả tệp) | DASHBOARD, BÁO CÁO THÁNG, BÁO CÁO QUÝ, TỔNG HỢP TÙY CHỌN, XNT VTBB, GIAO DỊCH VTBB, MIN MOQ, CẤU HÌNH | 2 (tồn, Min / MOQ), 4 (hao hụt, tồn lâu) |
| QUẢN LÝ NHÃN MÁC IDA GROUP | NHẬP KHO NHÃN MÁC, XUẤT KHO NHÃN MÁC, BÁO CÁO TỒN KHO NHÃN MÁC, ĐỊNH MỨC TỒN | 2 |
| 3. XUẤT NHẬP TỒN NL, BTP | Nhập kho NLBTP, 6. Xuất kho ngoài sản xuất, 6.1 Xuất kho theo ĐH thành phẩm, 4. DS PHỐI BTP, 4.1 LSX BTP, 8 và 8.1 Tồn kho SX, 9 và 9.1 Tồn kho Kinh doanh, 10 đến 10.3 đối chiếu NCC, Sổ tổng hợp tồn kho có giá, Báo cáo, Chi tiết báo cáo | 4 |
| Drive QLDL 7. Đối chiếu tồn kho (cả tệp) | Toàn bộ | 4 |
| Drive QLDL 1, 2, 4 | Tồn kho NCC (1); NHẬP KHO VTBB, Nhập kho NLBTP, Đối chiếu tồn kho VTBB / BTP, XK SX BTP, XK SX VTBB, XUẤT NHẬP TP (2 và 4) | 2 (nhập), 4 (còn lại) |
| Drive QL Giá vốn 1 và 3 | Tồn kho chi tiết / tổng BTP SX và VTBB SX, Giá nhập kho VTBB, Giá nhập kho NLBTP | 4 |
| ĐIỀU PHỐI THÀNH PHẨM, BC ĐP THÀNH PHẨM | NHẬP-XUẤT TP, BC TỒN KHO TẠI NCC GC, phiếu nhập kho thành phẩm | 4 (cùng phase 5) |

Sheet tồn kho đang bị chép ở ít nhất 6 tệp (hai tệp Xuất nhập tồn, QLDL 2, QLDL 7, Giá vốn 1, Giá vốn 3); sau phase 4
chỉ còn một nơi.

### 4.4 Báo cáo

| Báo cáo | Nội dung | Thay sheet | Tính năng | Phase |
|---|---|---|---|---|
| Tồn tức thời | Tồn thực tế, tạm, lỗi, có thể sản xuất theo kho, thương hiệu, mã | TỒN KHO; 8.1, 9.1 Tồn kho tổng | SX-KHO-29 | 2 |
| Sổ giao dịch (thẻ kho) | Mọi lần nhập, xuất, chuyển của một mã | GIAO DỊCH VTBB, LỊCH SỬ | SX-KHO-31 | 2 |
| Giá trị tồn | Số lượng x đơn giá bình quân theo kho, loại hàng | Sổ tổng hợp tồn kho có giá | SX-KHO-33 | 2 |
| Cần đặt hàng | Mã dưới tồn an toàn, số đề xuất đặt làm tròn theo MOQ, trừ số đang đặt chưa về | MIN MOQ, THÔNG TIN, ĐỊNH MỨC TỒN | SX-KHO-36, 47 | 2 |
| Xuất nhập tồn theo kỳ | Tồn đầu, nhập, xuất, tồn cuối theo tháng, quý, khoảng ngày | BÁO CÁO THÁNG, BÁO CÁO QUÝ, TỔNG HỢP TÙY CHỌN, TỒN KHO THEO KỲ | SX-KHO-32, 45 | 4 |
| Tồn theo lô và hạn sử dụng | Lô nào còn bao nhiêu, sắp hết hạn | 8. Tồn kho chi tiết | SX-KHO-30 | 4 |
| Tuổi tồn, tồn lâu, tồn chết | Mã không phát sinh lâu ngày, chi phí lưu kho ước tính | DASHBOARD của BC VTBB | SX-KHO-46 | 4 |
| Hao hụt và lỗi nhập | Hao hụt thực tế so định mức theo loại vật tư, tỷ lệ lỗi nhập theo NCC | BC VTBB | SX-KHO-48 | 4 |
| Đối chiếu tồn với NCC | Chênh lệch từng mã từng kỳ, trạng thái xử lý, so các lần NCC gửi | ĐỐI CHIẾU NCC, LỊCH SỬ ĐỐI CHIẾU, QLDL 7 | SX-KHO-39 … 42 | 4 |
| Tồn tại NCC gia công | VTBB, BTP, thành phẩm đang nằm ở từng NCC | BC TỒN KHO TẠI NCC GC, Tồn kho NCC | SX-KHO-37 | 4 |
| Đủ vật tư cho đơn | Đơn nào đủ VTBB, đủ BTP để sản xuất | Cột trạng thái ở sheet ĐIỀU PHỐI | SX-KHO-14 | 4 |
| Bảng điều khiển kho và kiểm tra dữ liệu | Số tổng, cảnh báo, dòng dữ liệu sai | DASHBOARD, Kiểm tra dữ liệu | SX-KHO-49 | sau |

## 5. Cách kiểm chứng mỗi phase

1. **Chốt nghiệp vụ:** mỗi tính năng có tiêu chí chấp nhận, người phụ trách bên Sản xuất xác nhận trước khi viết mã.
2. **Đối chứng với sheet:** lấy dòng ví dụ và công thức trong sheet làm bộ ca đối chứng; cùng đầu vào thì ERP phải ra đúng
   con số của sheet. Dữ liệu thật từ sổ Quản lý nhãn mác dùng để thử ở quy mô thật.
3. **Bài kiểm tự động** cho mỗi công thức và mỗi luật chặn (xuất âm kho, dựng lại tồn từ sổ giao dịch phải khớp).
4. **Người dùng chạy thử trên dev**, rồi chạy song song với Google Sheets; số tồn hai bên khớp ổn định thì mới bỏ sheet.

## 6. Việc cần chủ dự án quyết

| # | Câu hỏi | Đề xuất |
|---|---|---|
| 1 | Thứ tự phase ở mục 2 | Duyệt như bảng; Pháp lý sản phẩm chen sau phase 1 |
| 2 | Lát cắt đầu tiên | Phase 0 + 1 + 2 cho VTBB: mã hàng, định mức bao bì thật, nhập / xuất / chuyển kho, tồn |
| 3 | Gửi câu hỏi chặn cho phòng Sản xuất | Gửi 10 câu ở [`01`](../../chuc-nang/01-yeu-cau-chuc-nang.md) mục 4 trước khi thiết kế bảng Kho |
| 4 | Mở rộng định mức bao bì (thêm *Hộp*, *Vật tư khác*, số lượng trên dòng) | Làm chung đợt tối ưu duoc-CR-784 đang chạy |

## 7. Liên kết

- Danh sách tính năng: [`chuc-nang/01`](../../chuc-nang/01-yeu-cau-chuc-nang.md), [`11`](../../chuc-nang/11-san-pham.md), [`12`](../../chuc-nang/12-kho.md)
- Nguồn dữ liệu thật: [`nghien-cuu/21`](../../nghien-cuu/21-so-quan-ly-nhan-mac-ida-group.md)
- 13 quy trình con và tên gọi chuỗi cung ứng: [`nghien-cuu/15`](../../nghien-cuu/15-tong-hop-13-quy-trinh-san-xuat.md)
- Đợt tối ưu bảng Giá nguyên vật liệu sản xuất: [`thu-mua/plans/261125`](../../../thu-mua/plans/261125-toi-uu-bang-gia-nvl-duoc-cr-784/plan.md)
