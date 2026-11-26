# YÊU CẦU CHỨC NĂNG — SẢN XUẤT GIA CÔNG (danh sách tính năng)

| | |
|---|---|
| Bản | 0.2 |
| Ngày | 26/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp, chờ phòng Sản xuất chốt câu hỏi |
| CR liên quan | — |

**Đọc trước.** Đây là tệp đọc đầu tiên của phân hệ: mỗi dòng là một tính năng, có mã để tra sang tệp chi tiết. Danh sách
rút từ bộ Google Sheets *quy trình làm việc* phòng Sản xuất gửi ngày 26/11/2026 (dữ liệu trong đó là **mô phỏng**, chỉ dùng
để hiểu quy trình và biểu mẫu). Chưa có dòng mã nào của phân hệ; cột *ERP đã có* so với phần Thu mua, Kho, Sản phẩm và cụm
Giá nguyên vật liệu sản xuất đang chạy. Bản 0.1 (danh sách CN-SX theo nghiên cứu chuẩn Thông tư 99) được thay bằng bản này;
nghiên cứu đó nằm ở [`nghien-cuu/20`](../nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md).

**Nguồn dữ liệu thật để nạp ban đầu:** sổ *Quản lý nhãn mác IDA GROUP* của Thiết kế (11.150 mã hàng hóa, quy tắc đặt mã,
định mức bao bì thật của 4.189 mã) — xem [`nghien-cuu/21`](../nghien-cuu/21-so-quan-ly-nhan-mac-ida-group.md).

## 1. Cách tổ chức

DEGO không tự sản xuất: toàn bộ là **gia công tại nhà cung cấp gia công (NCC GC)**. Tài liệu chia theo **chức năng**, không
theo tệp Excel:

| Thứ tự làm | Phần | Tệp chi tiết | Mã tính năng | Trạng thái tài liệu |
|---|---|---|---|---|
| 1 | **Sản phẩm**: mã hàng, quy tắc, công thức BTP, định mức / BOM, tiêu chí đánh giá | [`11-san-pham.md`](11-san-pham.md) | SX-SP-01 … SX-SP-54 | Đã viết |
| 2 | **Kho**: nhập, xuất, chuyển, kho tại NCC GC, tồn, đối chiếu NCC, báo cáo | [`12-kho.md`](12-kho.md) | SX-KHO-01 … SX-KHO-50 | Đã viết |
| 3 | Đơn hàng gia công (điều phối, duyệt 7 bộ phận, lệnh sản xuất) | chưa viết | SX-DH | Nguồn: [`nghien-cuu/16`](../nghien-cuu/16-khung-quy-trinh-va-phap-ly-san-xuat.md), [`19`](../nghien-cuu/19-dieu-phoi-thanh-pham-va-su-co.md) |
| 4 | Sự cố sản xuất | chưa viết | SX-SC | Nguồn: [`nghien-cuu/19`](../nghien-cuu/19-dieu-phoi-thanh-pham-va-su-co.md) |
| 5 | Các phần còn lại: NCC gia công, mua và khảo sát giá, giá vốn, công nợ, pháp lý, báo cáo | chưa viết | SX-NCC, SX-MH, SX-GV, SX-CN, SX-PL, SX-BC | Nguồn: [`nghien-cuu/15`](../nghien-cuu/15-tong-hop-13-quy-trinh-san-xuat.md) … [`19`](../nghien-cuu/19-dieu-phoi-thanh-pham-va-su-co.md) |

Lý do thứ tự: Kho cần mã hàng để ghi tồn; đơn gia công cần định mức (BOM) để biết xuất bao nhiêu và cần tồn kho để duyệt;
giá vốn cần BOM và giá mua; sự cố cần đơn hàng và kho lỗi.

**Cột Đợt** trong hai bảng dưới:

| Đợt | Nghĩa |
|---|---|
| 1a | Sản phẩm lõi: mã hàng, quy tắc mã, đồng bộ mã DEGO - NCC, định mức bao bì có số lượng — đủ để Kho chạy |
| 1b | BOM đầy đủ: công thức BTP, BĐM BTP, BĐM thành phẩm, bên cung ứng, phiên bản, duyệt |
| 2a | Kho lõi: danh mục kho, loại giao dịch, nhập, xuất ngoài sản xuất, chuyển kho, tồn, sổ giao dịch |
| 2b | Kho cho sản xuất: lô, xuất theo đơn và BĐM, giữ hàng, kho lỗi, tồn theo kỳ, đối chiếu NCC GC |
| 3 | Mở rộng, làm sau |

Việc xếp đợt là **đề xuất**, chưa chốt.

## 2. Sản phẩm — 54 tính năng

ERP đã có trọn: 2 · có một phần: 18 · chưa có: 34. Chi tiết từng
tính năng (đầu vào, đầu ra, quy tắc, công thức, trường dữ liệu) ở [`11-san-pham.md`](11-san-pham.md) mục 7.

| Mã | Tính năng | Mô tả ngắn | ERP đã có | Ưu tiên | Đợt |
|---|---|---|---|---|---|
| | **Nhóm A — Danh mục mã hàng** | | | | |
| SX-SP-01 | Danh mục mã hàng theo loại mã | Một danh mục cho NL, BTP, VTBB, TP, phí; mỗi mã có **loại mã** (NLNK, NLT, NA, BTPR, BTPM, BTPNK, BTPCT, VTBB, HH, PPT, PĐG, CPNK) để lọc và áp quy tắc. | Một phần | Cao | 1a |
| SX-SP-02 | Thuộc tính nguyên liệu | Hàm lượng, ĐVT hàm lượng, dạng NL, màu chuẩn, hoạt chất, số CAS, xuất xứ, phân loại. | Chưa | Cao | 1a |
| SX-SP-03 | Thuộc tính BTP | Tên pháp lý, thành phần, dòng V, màu, dạng ruột, độ trong, tỷ trọng, mã công thức Lab, nhóm (thuốc / phân). | Chưa | Cao | 1a |
| SX-SP-04 | Thuộc tính VTBB theo phân loại | Ba khối: chai / nắp / xô / can (chất liệu, hình dạng, cao x đường kính, trọng lượng, cổ chai, màu, nhận diện riêng, kích thước nhãn phù hợp); túi / nhãn / bao (chất liệu, thương hiệu, kích thước nhãn gồm mép dán, NCC GC nhận vật tư, mã HH, tên pháp lý, thể tích); thùng / hộp (quy cách sản phẩm, thương hiệu, kích thước phủ bì, **kích thước lọt lòng**, trọng lượng, số lớp, cán màng, màu chính). | Chưa | Trung bình | 1a |
| SX-SP-05 | Hồ sơ thành phẩm (HH) | Mỗi mã HH: thương hiệu, khách hàng, công ty phân phối, công ty xuất hóa đơn đầu ra, công ty nhận hóa đơn đầu vào, NCC sản xuất, dòng sản phẩm, tên pháp lý, mô tả ruột, tên nhãn hiệu, quy cách SP, quy cách thùng, quy cách hộp / bao, ĐVT chính, đơn vị thể tích (g / ml), thể tích trên nhãn. | Một phần | Cao | 1a |
| SX-SP-06 | Danh mục dùng chung cho thuộc tính | ĐVT; màu (kèm mã 2 ký tự); hình dạng VTBB; dạng NL / BTP (viên, cốm, bột, gel, lỏng); dạng theo quy định (WP, WG, SL, EC, SC...) kèm tên đầy đủ; độ trong; phân loại sản phẩm; dòng V; danh mục hoạt chất + số CAS. | Một phần | Trung bình | 1a |
| SX-SP-07 | Mã chi phí gia công như mặt hàng phi kho | PPT, PĐG, CPNK là mã có tên, ĐVT, NCC, nhưng không nhập kho. | Chưa | Trung bình | 3 |
| SX-SP-08 | Hình ảnh và mockup của mã | Ảnh vật tư, ảnh nhãn, mockup có gắn mã VTBB. | Một phần | Thấp | 3 |
| SX-SP-09 | Ngưỡng tồn và MOQ theo mã + kho | Min tồn an toàn, MOQ, NCC phụ trách theo từng mã + kho; dùng cảnh báo cần đặt hàng. | Chưa | Thấp | 3 |
| | **Nhóm B — Quy tắc** | | | | |
| SX-SP-10 | Sinh mã tự động theo quy tắc | Chọn loại mã, hệ thống gợi ý mã kế tiếp theo tiền tố (và theo 4 số cuối mã HH với nhãn, NDT, hộp, BTPCT). | Chưa | Cao | 1a |
| SX-SP-11 | Sinh tên nội bộ và tên hóa đơn theo mẫu | Ghép tên từ thuộc tính theo mẫu từng loại. | Một phần | Trung bình | 3 |
| SX-SP-12 | Kiểm trùng khi khai báo | Cảnh báo khi thuộc tính trùng mã đã có (không chỉ trùng mã). | Một phần | Trung bình | 1a |
| SX-SP-13 | Phiếu khai báo mã mới và duyệt | Phiếu khai báo có trạng thái (nháp, chờ duyệt, đã duyệt, đã có trên Misa), người duyệt theo loại mã, ngày gửi kế toán. | Chưa | Trung bình | 3 |
| SX-SP-14 | Đồng bộ mã DEGO - mã NCC GC | Bảng cặp mã theo từng NCC; tự đổi mã khi nhập số liệu NCC gửi. | Chưa | Cao | 1a |
| SX-SP-15 | Bảng dòng công thức KD - NCC | Quy đổi dòng V + màu Kinh doanh gọi sang dòng V + màu NCC gọi, theo từng NCC. | Chưa | Cao | 1b |
| SX-SP-16 | Quản lý nhãn mác | Tình trạng in nhãn, trạng thái NCC duyệt nhãn, ghi chú độc quyền, sáu mã bao bì gắn với HH. | Chưa | Trung bình | 3 |
| SX-SP-17 | Bảo mật công thức và nguyên liệu mã hóa | Ai được xem công thức NCC, lượng NL trong BĐM BTP, tên thật của mã `NA`. | Một phần | Cao | 1b |
| SX-SP-18 | Trạng thái vòng đời mã | Đang kinh doanh, chưa kinh doanh, ngưng sử dụng; dự kiến bỏ (vd BTPM năm 2027). | Một phần | Thấp | 3 |
| | **Nhóm C — Công thức BTP** | | | | |
| SX-SP-19 | Danh sách công thức / dòng công thức BTP | Mỗi dòng: tên pháp lý 1, tên pháp lý 2, dòng V áp dụng với KD, màu gốc, màu thực tế, có phụ gia, có pha màu, mô tả phụ gia / pha thêm, mã Lab, mã BTP, công thức áp dụng với NCC, ghi chú, ngày cập nhật. | Chưa | Cao | 1b |
| SX-SP-20 | Theo dõi công thức mới | Sổ yêu cầu công thức mới: NCC, tên pháp lý, thành phần, nhật ký tiến độ, kết quả, công thức chốt (ngày, mã công thức, mã BĐM). | Chưa | Trung bình | 3 |
| SX-SP-21 | Theo dõi test mẫu | Phiếu test: mẫu, nguồn mẫu, từng hoạt chất, hàm lượng đăng ký, hàm lượng test, chênh lệch, sai số cho phép, kết quả; kết quả ngoại dạng. | Chưa | Cao | 3 |
| SX-SP-22 | Bảng khung sai số hàm lượng | Danh mục khung sai số theo dải hàm lượng và dạng (lỏng / rắn); tự tra sai số cho phép. | Chưa | Trung bình | 3 |
| SX-SP-23 | Khung sai số chiết rót và thể tích chốt đóng | Theo thể tích trên nhãn: khung sai số, thể tích chốt đóng; theo sản phẩm + NCC: tỷ lệ đóng tối ưu đã chốt, thông tin KD nắm. | Chưa | Trung bình | 3 |
| SX-SP-24 | Màu độc quyền theo khách hàng | Ghi màu dành riêng cho từng khách / nhóm khách của một sản phẩm; cảnh báo khi đơn chọn sai. | Chưa | Thấp | 3 |
| | **Nhóm D — Định mức / BOM** | | | | |
| SX-SP-25 | BĐM BTP (đầu phiếu + dòng) | Định mức nguyên liệu trên 1.000 kg / lít BTP, mỗi hoạt chất một dòng. | Chưa | Cao | 1b |
| SX-SP-26 | Tính lượng NL theo hàm lượng và tỷ trọng | Tự tính lượng NL, tỷ lệ hàm lượng yêu cầu / hàm lượng sản phẩm, kiểm khung sai số. | Chưa | Cao | 1b |
| SX-SP-27 | Tính lượng NL cần mua và giá BTP tạm | Từ BĐM BTP + lượng BTP cần phối + giá NL từng NCC + phí phối ra giá BTP; trạng thái *Giá tham khảo* / *Duyệt mua*. | Một phần | Trung bình | 3 |
| SX-SP-28 | BĐM VTBB | Định mức bao bì trên 1 thành phẩm theo mã HH. | Một phần | Cao | 1a |
| SX-SP-29 | Mở rộng loại thành phần và nhiều mã cùng loại | Thêm xô, can, lon, túi / gói, bao, hộp, cốc đong, seal, tem, màng co, túi PE, tag, tấm lót; cho phép hai nhãn, hai tem trên một sản phẩm. | Một phần | Cao | 1a |
| SX-SP-30 | Định mức số lượng trên từng dòng | Mỗi dòng có số lượng trên 1 thành phẩm (1; 1 / quy cách thùng; thể tích trên nhãn) và ĐVT. | Một phần | Cao | 1a |
| SX-SP-31 | Bên cung ứng từng thành phần và cấu thành | Mỗi dòng ghi CTY hay NCC; đầu phiếu ghi cấu thành theo từng bên (thương hiệu / công ty nào mang gì). | Chưa | Cao | 1b |
| SX-SP-32 | BĐM thành phẩm gộp | Một BĐM cho 1 thành phẩm gồm dòng BTP ruột + các dòng VTBB + dòng phí gia công; trỏ về BĐM BTP và BĐM VTBB nguồn. | Chưa | Cao | 1b |
| SX-SP-33 | Dòng phí gia công trong BĐM | Dòng *Phí sang chai đóng gói* (mã PĐG theo dải thể tích, số lượng 1 / TP), phí phối trộn theo ml / kg. | Chưa | Trung bình | 3 |
| SX-SP-34 | Phiên bản BĐM | Số phiên bản, lý do thay đổi, đơn đầu tiên áp dụng, phiên bản hiện hành, không sửa đè bản đã duyệt. | Chưa | Cao | 1b |
| SX-SP-35 | Duyệt BĐM | Trạng thái nháp / chờ duyệt / đã duyệt / ngưng; người duyệt, ngày duyệt; phiếu ký nhiều ô (bao bì, pháp lý, giá, kế toán trưởng). | Chưa | Cao | 1b |
| SX-SP-36 | BĐM thuế và cấu thành thuế | Bộ định mức thứ hai theo từng công ty nội bộ, kèm luồng hóa đơn; liên kết với bộ nội bộ. | Chưa | Trung bình | 3 |
| SX-SP-37 | In phiếu BĐM ký duyệt | Mẫu in *Bảng định mức VTBB thành phẩm* (và BĐM BTP, BĐM TP): đầu phiếu, bảng vật tư, luồng hóa đơn, ô ký. | Chưa | Trung bình | 3 |
| SX-SP-38 | Nhập và xuất Excel định mức | Nhập hàng loạt từ mẫu Excel, xem trước, xóa theo lô nhập. | Có | Trung bình | 1a |
| SX-SP-39 | Tra ngược mã vật tư dùng ở sản phẩm nào | Chọn một mã VTBB / NL, xem các thành phẩm và BĐM đang dùng. | Có | Trung bình | 1a |
| SX-SP-40 | Chi phí định mức của 1 thành phẩm | Cộng giá × định mức của mọi dòng do công ty cung ứng; tách phần NCC lo. | Một phần | Trung bình | 3 |
| SX-SP-41 | Cảnh báo dữ liệu định mức | HH chưa có BĐM duyệt; dòng thiếu mã; thiếu giá; thiếu quy cách thùng; lệch ĐVT; cùng một mã dùng cho hai loại (vd nhãn chính làm nhãn thùng); BĐM dùng mã đã ngưng. | Một phần | Trung bình | 3 |
| SX-SP-42 | Bung BĐM cho lệnh sản xuất và xuất kho | Từ mã BĐM TP + số lượng thành phẩm ra danh sách NVL, VTBB, phí theo bên cung ứng. | Chưa | Cao | 1b |
| | **Nhóm E — Tiêu chí đánh giá, khảo sát, sổ phụ** | | | | |
| SX-SP-43 | Tiêu chuẩn nguyên liệu | Theo mã NL: xuất xứ, ngoại quan, màu, độ tan, độ trong, độ ẩm, pH, hàm lượng, số CAS, thuộc phụ lục nghị định. | Chưa | Trung bình | 3 |
| SX-SP-44 | Phiếu yêu cầu test Lab và kết quả | Yêu cầu test cho mẫu công thức, lô nhập, hàng tồn; kết quả ngoại dạng và hàm lượng; hạn trả kết quả. | Chưa | Cao | 3 |
| SX-SP-45 | Sổ lưu mẫu đối chứng | Mẫu lưu tại Lab và tại NCC: sản phẩm, lô, ngày lưu, hạn lưu (NCC tối thiểu 2 năm), kỳ đối chiếu 6 tháng. | Chưa | Thấp | 3 |
| SX-SP-46 | Tiêu chí KCS thành phẩm theo sản phẩm | Bộ tiêu chí kiểm khi nhận hàng: ngoại dạng, màu, trọng lượng, thể tích, phụ kiện đi kèm, số lô, NSX, HSD, chứng từ. | Một phần | Trung bình | 3 |
| SX-SP-47 | Khảo sát VTBB / NL / BTP phù hợp công nghệ NCC | Sổ khảo sát theo mã VTBB + ruột + NCC: hiện trạng, số mẫu gửi, hạn 10-14 ngày, kết quả, đánh giá QLSX, phản hồi KD. | Chưa | Trung bình | 3 |
| SX-SP-48 | Ma trận phù hợp VTBB - ruột - NCC | Kết quả khảo sát đạt trở thành dữ liệu tra: NCC nào đóng được vật tư nào với ruột nào. | Chưa | Thấp | 3 |
| SX-SP-49 | Cọc nhãn | Sổ cọc theo NCC + mã HH + mã nhãn: số lượng, tiền cọc, hợp đồng, điều kiện hoàn, theo dõi, hoàn cọc. | Chưa | Trung bình | 3 |
| SX-SP-50 | Mẫu cho tặng | Sổ mẫu được cho / tặng: đơn vị cho, thông số, việc cần làm (test, chụp, lưu, gửi), kết quả, đánh giá. | Chưa | Thấp | 3 |
| SX-SP-51 | Chính sách theo sản phẩm tại NCC | % hao hụt cho phép theo NCC + nhóm vật tư; nhận dự trù BTP hay không; MOQ phối BTP; thể tích đóng tối ưu. | Chưa | Trung bình | 3 |
| SX-SP-52 | Báo cáo dữ liệu VTBB cho Kinh doanh | Mã, tên, hình, giá, sản phẩm áp dụng, giá thấp nhất / cao nhất 5 lần mua gần nhất, công nghệ theo NCC. | Một phần | Thấp | 3 |
| SX-SP-53 | Lịch sử thay đổi mã hàng và định mức | Ai sửa gì, khi nào, lý do. | Một phần | Thấp | 3 |
| SX-SP-54 | Chuyển dữ liệu ban đầu từ Google Sheets | Nhập danh mục VTBB, hồ sơ HH, công thức, BĐM hiện có vào ERP một lần, có đối soát. | Một phần | Cao | 1a |

## 3. Kho — 50 tính năng

ERP đã có trọn: 0 · có một phần: 10 · chưa có: 40. Chi tiết ở
[`12-kho.md`](12-kho.md) mục 5.

| Mã | Tính năng | Mô tả ngắn | ERP đã có | Ưu tiên | Đợt |
|---|---|---|---|---|---|
| SX-KHO-01 | Danh mục kho gia công | Kho có loại (DEGO, tại NCC GC, kho lỗi, thương mại), gắn NCC GC, kho lỗi đi cặp, loại hàng chứa, mã kho Misa | Một phần | Cao | 2a |
| SX-KHO-02 | Danh mục loại giao dịch kho | Mỗi loại có chiều, nhóm tồn, nhóm báo cáo, cờ hao hụt, phạm vi (dùng chung / chỉ NL-BTP) | Chưa | Cao | 2a |
| SX-KHO-03 | Tồn theo thương hiệu | Thêm chiều thương hiệu (và *Dùng chung*) vào khóa tồn | Chưa | Cao | 2a |
| SX-KHO-04 | Ánh xạ mã vật tư NCC GC | Bảng mã DEGO, mã NCC, tên NCC đặt, theo từng NCC GC | Chưa | Cao | 2a |
| SX-KHO-05 | Khai báo Min, MOQ theo mã + kho | Tồn an toàn, số đặt tối thiểu, NCC phụ trách, số đang đặt chưa về, ghi chú | Chưa | Trung bình | 3 |
| SX-KHO-06 | Chính sách kho theo NCC GC | % hao hụt cho phép (theo NCC, theo loại hàng), phí lưu kho, đơn vị tính phí, số ngày miễn phí | Một phần | Trung bình | 3 |
| SX-KHO-07 | Số dư đầu kỳ | Nhập tồn đầu (dùng được và lỗi) khi chuyển sổ, có đơn giá đầu kỳ | Một phần | Cao | 2a |
| SX-KHO-08 | Nhập kho từ mua hàng | Nhận hàng theo ĐMH vào kho NCC GC, theo thương hiệu, có ảnh phiếu, số hóa đơn | Một phần | Cao | 2a |
| SX-KHO-09 | Nhập NL / BTP theo lô | Số lô, NSX, HSD, số CAS, hàm lượng thực tế, kết quả Lab trên dòng nhập | Chưa | Cao | 2b |
| SX-KHO-10 | Nhập tạm chờ kiểm duyệt | Hàng về chưa có kết quả Lab ghi tồn tạm; đạt thì chuyển thực tế, không đạt chuyển lỗi | Chưa | Cao | 2b |
| SX-KHO-11 | Lệnh phối BTP | Xuất NL đi phối, nhập BTP sau phối, so định mức, chênh lệch, tiến độ | Chưa | Cao | 2b |
| SX-KHO-12 | Nhập khác: đổ thu, dư sau sản xuất, cho tặng | Các loại nhập không qua mua | Một phần | Thấp | 3 |
| SX-KHO-13 | Nhập, chuyển, trả thành phẩm | Bảy trạng thái giao dịch TP; lô, NSX, HSD; KCS khi nhận | Chưa | Cao | 2b |
| SX-KHO-14 | Duyệt đủ vật tư cho đơn TP | ĐP VTBB, ĐP NL/BTP trả trạng thái, ngày đủ nội bộ, ngày đủ thuế, mã BĐM | Chưa | Cao | 2b |
| SX-KHO-15 | Xuất VTBB theo đơn TP và BĐM | Nhập mã đơn + mã BĐM, hệ thống bung dòng và tính số cần xuất | Chưa | Cao | 2b |
| SX-KHO-16 | Xuất BTP theo đơn TP | Quy đổi quy cách × số lượng × tỷ trọng ra kg / lít | Chưa | Cao | 2b |
| SX-KHO-17 | Xuất tạm và giữ hàng cho đơn | Đơn duyệt thì giữ; có TP thì chuyển thực tế từng lần; đơn xong thì hoàn thành | Chưa | Cao | 2b |
| SX-KHO-18 | Ghi nhận xuất theo lần NCC có thành phẩm | Tối đa 3 lần (nên không giới hạn): ngày, số TP, tự tính VTBB / BTP đã dùng | Chưa | Cao | 2b |
| SX-KHO-19 | Cảnh báo và chặn xuất âm kho | Báo khi số xuất vượt tồn; liệt kê dòng gây âm | Chưa | Cao | 2a |
| SX-KHO-20 | Hủy đơn và hoàn giữ hàng | Đơn hủy thì số giữ về 0, tồn có thể sản xuất tăng lại | Chưa | Trung bình | 3 |
| SX-KHO-21 | Xuất ngoài sản xuất | Mẫu thử, cho tặng, xuất khác, xuất bán; có lý do, người nhận, ảnh phiếu | Chưa | Cao | 2a |
| SX-KHO-22 | Chuyển kho | Một phiếu sinh xuất ở kho đi và nhập ở kho đến; SL yêu cầu, SL thực; tài xế, xe; trạng thái vận chuyển | Chưa | Cao | 2a |
| SX-KHO-23 | Xuất bán nội bộ và yêu cầu xuất hóa đơn | Chuyển quyền sở hữu giữa thương hiệu / pháp nhân, có đơn giá, thành tiền | Chưa | Trung bình | 3 |
| SX-KHO-24 | Đưa vào chi phí | Phiếu đề nghị đưa hàng vào chi phí: khoản mục, công ty chịu, giá trị | Chưa | Trung bình | 3 |
| SX-KHO-25 | Hao hụt, đổ bỏ, xuất hủy | Ghi hao hụt, so định mức, rẽ nhánh trong / vượt hạn mức; biên bản tiêu hủy | Chưa | Cao | 2b |
| SX-KHO-26 | Kho lỗi và chuyển trạng thái hàng lỗi | Nhập lỗi, chuyển giữa kho lỗi và kho dùng, gắn mã sự cố, mã yêu cầu xử lý lại | Chưa | Cao | 2b |
| SX-KHO-27 | Mẫu cho tặng không quản tồn | Ghi nhận mẫu được cho tặng: mục đích, thông số, việc cần làm (test, chụp, lưu, gửi) | Chưa | Thấp | 3 |
| SX-KHO-28 | Bộ phiếu in kho | Đề nghị nhập, xuất, chuyển, xuất bán nội bộ, đưa vào chi phí, nhập kho TP; số phiếu, chữ ký, tiền bằng chữ | Chưa | Trung bình | 3 |
| SX-KHO-29 | Tồn tức thời ba nhóm | Theo kho × thương hiệu × mã: đầu kỳ, nhập, xuất, tồn thực tế, tồn tạm, tồn lỗi, tồn có thể sản xuất | Một phần | Cao | 2a |
| SX-KHO-30 | Tồn chi tiết theo lô | Từng lô: ngày nhập, NSX, HSD, tồn, đơn giá, trạng thái dùng được, đơn đang treo | Chưa | Cao | 2b |
| SX-KHO-31 | Sổ giao dịch kho | Mọi giao dịch theo thời gian, lọc kho, thương hiệu, mã, loại; truy về phiếu gốc | Một phần | Cao | 2a |
| SX-KHO-32 | Tồn theo kỳ | Chọn khoảng ngày; tồn đầu, nhập, xuất, tồn cuối; tồn lũy kế sau từng giao dịch | Chưa | Cao | 2b |
| SX-KHO-33 | Giá trị tồn và đơn giá bình quân | Đơn giá theo nhóm nhập; giá trị tồn; sổ tổng hợp có giá | Một phần | Cao | 2a |
| SX-KHO-34 | Hai góc nhìn tồn SX và KD | Trừ BTP theo quy cách thực đóng và theo quy cách KD | Chưa | Trung bình | 3 |
| SX-KHO-35 | Tồn nội bộ và tồn thuế | Hai sổ tồn; kiểm đủ cả hai khi duyệt đơn | Chưa | Trung bình | 3 |
| SX-KHO-36 | Cảnh báo tồn | Tồn âm; không giao dịch quá n ngày; dưới Min; dưới MOQ; sắp hết hạn | Một phần | Trung bình | 3 |
| SX-KHO-37 | Tồn thành phẩm tại NCC GC | Tồn TP theo NCC × mã × NSX; số ngày tồn; HSD còn lại | Chưa | Trung bình | 3 |
| SX-KHO-38 | Nạp số liệu tồn NCC GC gửi | Dán / nhập tệp theo mẫu từng NCC; tự đổi mã NCC sang mã DEGO | Chưa | Cao | 2b |
| SX-KHO-39 | Đối chiếu tự động với NCC GC | So giao dịch và tồn theo mã + kho; dung sai theo % hao hụt; kết luận | Chưa | Cao | 2b |
| SX-KHO-40 | Lịch sử đối chiếu và xử lý chênh lệch | Lưu từng kỳ; hướng điều chỉnh, nguyên nhân, trạng thái xử lý | Chưa | Cao | 2b |
| SX-KHO-41 | So sánh các lần NCC gửi | Lần gần nhất so lần trước; khác thì cảnh báo | Chưa | Thấp | 3 |
| SX-KHO-42 | Biên bản xác nhận tồn và giải trình chênh lệch | In biên bản hai bên ký; đính bản ký | Chưa | Trung bình | 3 |
| SX-KHO-43 | Phí lưu kho và hao hụt NCC tính | Ghi phía mình, ghi phía NCC, đối chiếu, hạn thanh toán | Chưa | Trung bình | 3 |
| SX-KHO-44 | Chốt kỳ kho | Lưu ảnh tồn cuối tháng, chặn sửa giao dịch kỳ đã chốt | Chưa | Trung bình | 3 |
| SX-KHO-45 | Báo cáo xuất nhập tồn theo kỳ | Tháng, quý, tùy chọn; theo loại hàng, thương hiệu, kho, NCC; so cùng kỳ | Chưa | Trung bình | 3 |
| SX-KHO-46 | Tuổi tồn, tồn lâu, tồn chết | Số ngày tồn, nhóm tuổi, nhóm luân chuyển, top tồn lâu | Chưa | Trung bình | 3 |
| SX-KHO-47 | Đề xuất đặt hàng theo Min, MOQ | Danh sách mã dưới Min kèm số đề xuất; tạo YCMH nháp | Chưa | Trung bình | 3 |
| SX-KHO-48 | Báo cáo hao hụt và lỗi nhập | Tỷ lệ hao hụt so định mức theo loại, theo NCC GC; tỷ lệ lỗi nhập theo NCC bán | Chưa | Trung bình | 3 |
| SX-KHO-49 | Dashboard kho và kiểm tra dữ liệu | Chỉ số chính, tồn theo loại / thương hiệu / kho, ô kiểm tra dữ liệu | Một phần | Thấp | 3 |
| SX-KHO-50 | Báo cáo NL / BTP và sổ theo dõi vấn đề | Lô sắp hết hạn, tồn vượt tối đa, thiếu hóa đơn; sổ vấn đề và hành động | Chưa | Thấp | 3 |

## 4. Câu hỏi chặn cần phòng Sản xuất chốt trước khi thiết kế

Danh sách đầy đủ ở cuối mỗi tệp chi tiết ([`11`](11-san-pham.md) mục 11, [`12`](12-kho.md) mục 9). Các câu quyết định cấu
trúc dữ liệu, sửa sau rất tốn công:

1. **Lô và hạn sử dụng:** NL / BTP có bắt buộc theo dõi số lô, ngày sản xuất, hạn sử dụng, kết quả Lab không; VTBB và thành
   phẩm có theo lô không.
2. **Tồn nội bộ và tồn thuế:** ERP giữ một sổ (nội bộ) hay cả hai sổ; sổ thuế hiện chỉ ở Misa.
3. **Khóa tồn:** tồn theo Kho + Mã hàng, hay Kho + **Thương hiệu** + Mã hàng như sổ hiện tại.
4. **Hai góc nhìn tồn BTP** (theo Sản xuất và theo Kinh doanh, chênh do đóng tối ưu thể tích): giữ cả hai hay một.
5. **Cách tính tồn có thể sản xuất** và **giá tồn**: các sheet đang dùng ba cách khác nhau, cần chọn một.
6. **Định mức hao hụt:** lấy theo hợp đồng NCC, theo loại VTBB, hay theo thực tế; hiện có bốn nguồn.
7. **Phiên bản BĐM:** một thành phẩm có nhiều phiên bản định mức cùng hiệu lực không (theo lô NL khác hàm lượng).
8. **Bản thuế của BĐM:** khác bản nội bộ ở đâu; chưa có ví dụ nào trong tài liệu.
9. **Quy tắc mã:** tiền tố mã BĐM, mã sự cố, mã đơn đang lệch giữa quy trình và sổ; cần chốt một bộ.
10. **Bảo mật công thức:** ai được xem dòng công thức thật, mã NL mã hóa (`NA`), giá vốn.
