# Nhóm B — NCC gia công (GC) và Quản lý dữ liệu (QLDL)

Nguồn: 7 tệp Excel trong `D:\New folder\thuthapykien\tailieusanxuat\` (3 tệp gốc + 4 tệp trong `Drive QLDL (mới)`), tổng **84 sheet**, đọc ngày 26/11/2026 bằng openpyxl (giá trị + công thức + danh sách chọn). Không có chữ nằm trong hình (đã kiểm `xl/drawings`). Script tạm: `D:\tmp\sx-gom\scripts\b_*.py`.

Các tệp là bản xuất từ Google Sheets (còn dấu `__xludf.DUMMYFUNCTION`, `IMPORTRANGE` mất liên kết nên nhiều ô `#REF!` / `#N/A`). Phần lớn sheet là **khung biểu mẫu + 1–10 dòng dữ liệu mẫu**; dữ liệu thật đáng kể chỉ có ở 3 chỗ: *Tồn kho NCC* (59 dòng BTP), *Công nợ TP đóng gói* (khoảng 438 dòng), *NHẬP ĐIỂM* (690 dòng dựng sẵn, chưa chấm).

Viết tắt dùng chung: NL nguyên liệu, BTP bán thành phẩm (ruột), VTBB vật tư bao bì, NDT nhãn dán thùng, TP thành phẩm, ĐP điều phối, XLSC xử lý sự cố, P TCKT phòng tài chính kế toán, QLSX quản lý sản xuất, KD kinh doanh, LSX lệnh sản xuất, BĐM / BDM bảng định mức, HĐ hợp đồng / hoá đơn (theo ngữ cảnh).

---

## 1. Bảng kiểm kê

Loại: **QT** = quy trình bằng chữ · **BM** = biểu mẫu nhập liệu · **DM** = danh mục dữ liệu · **BC** = báo cáo / bảng tổng hợp tự tính · **In** = phiếu in · **Nháp** = trống / nháp / bỏ. Số dòng = dòng dữ liệu thật (không tính tiêu đề, dòng chỉ có STT).

### 1.1 CHECKLIST NCC GC MỚI.xlsx (7 sheet)

| Sheet | Loại | Dòng | Nội dung |
|---|---|---|---|
| DANH SÁCH TỔNG | Nháp | 0 | Trống hoàn toàn. |
| Mẫu 01 - Checklist DM hợp tác | BM | 0 | Danh mục sản phẩm dự kiến hợp tác với NCC GC mới. Cột (đều nhập tay): STT, Phân loại, Tên pháp lý, Thành phần, Mã BTP, Lý do chọn; theo từng thương hiệu (ABA, IDA GLOBAL, TỔNG): Ghi chú + Sản lượng dự kiến/năm (kg/lít); SL thùng tạm tính (15 L/kg mỗi thùng); Ghi chú AD; Định hướng. |
| Mẫu 02 - Checklist HĐ | BM + QT | 25 mục + 7 loại VB | Checklist 25 nội dung phải đàm phán với NCC (xem 2a). Cột: Nội dung thảo luận, Chi tiết, Công ty đề xuất, NCC phản hồi, Nội dung thống nhất, Loại văn bản chứa nội dung, **Giải thích riêng (bảo mật, không gửi NCC)**. Phần dưới: bảng *Thống nhất các loại văn bản phải có* (HĐ mua bán / gia công / phân phối / thuê kho / Phụ lục / Biên bản ngoài HĐ / Khác) với ô tích Thực hiện + Bên chuẩn bị. STT là công thức `row()-3`, còn lại nhập tay. |
| Mẫu 03-Nhóm làm việc NCC GC | BM | 5 | 5 nhóm làm việc cần lập khi ký hợp tác (Đặt hàng; Xuất nhập kho NL/BTP, VTBB; Kế toán; Thiết kế; Xử lý sự cố), bộ phận tham gia, ô tích Đã có, nhân sự NCC (kèm SĐT). Tiêu đề trong sheet ghi nhầm *MẪU 04*. |
| Mẫu 04-TỔNG HỢP GIÁ NCC GC | BM (nháp) | 0 | Ghi chú *Mẫu cũ chưa chốt lấy xây file*. Gồm 4 khung: Mẫu giá BTP NCC GC; Mẫu phí gia công (GCTP, màng co, tag, màng túi, dán decal, có/không hộp, dán tem); Mẫu phí phối chế (theo màu nước, dòng V); Mẫu bảng giá NCC GC cấu thành chi tiết (NL1–3, BTP ruột, chai/nắp, nhãn/túi, hộp, NDT, thùng, phí phối trộn, phí GC sang chai, vận chuyển + KCS, phí khác, tổng công nợ, quy đổi giá theo ml/gr). Dòng hướng dẫn: Auto / Click chọn / (nếu có) / Công thức. |
| Mẫu 05- BIÊN BẢN NỘI BỘ | BM | 0 | Biên bản bàn giao nội bộ Sản xuất → KD. Cột: Ngày, Đầu việc, Nội dung chi tiết, Thống nhất 2 bên, Phương thức lưu trữ / loại VB, Đại diện bên mua / bên bán. Gợi ý nội dung: phân bổ nhân sự, đàm phán được gì, còn vấn đề gì, nội dung trao đổi miệng. |
| Mẫu 06-CHECKLIST PHÁP LÝ NGƯNG | Nháp | 0 | Trống (tên gợi ý checklist pháp lý khi ngưng; nội dung thực tế nằm ở tệp ĐÁNH GIÁ NGƯNG HỢP TÁC › 1.1 PHÁP LÝ SX). |

### 1.2 ĐÁNH GIÁ ĐỊNH KÌ NCC GC.xlsx (6 sheet) — dựng 18/11/2026

| Sheet | Loại | Dòng | Nội dung |
|---|---|---|---|
| HƯỚNG DẪN | QT | 10 | Mục đích, căn cứ, 4 bước, cách tính điểm, quy ước lưu tệp (mỗi kỳ 1 tệp, vd `DANH_GIA_DINH_KY_NCC_GC_2026-H2`; ô trắng nhập, ô xanh công thức). |
| NHẬP ĐIỂM | BM | 690 (dựng sẵn, chưa có điểm) | Mỗi dòng = 1 NCC × 1 tiêu chí × 1 BP chấm (15 NCC × 46 dòng). Cột: NCC, Mã tiêu chí, Tiêu chí, Điểm tối đa, Các mức điểm, BP chấm (dựng sẵn); **Điểm chấm = Click chọn** (danh sách chỉ gồm các mức hợp lệ, vd 7/5/2/0); Căn cứ / số liệu, Vấn đề phát sinh, Người chấm, Ngày chấm = nhập tay. |
| VẤN ĐỀ & PHƯƠNG ÁN | BM | 0 | Sổ vấn đề: NCC, Mã tiêu chí, Vấn đề, BP ghi nhận, Ngày, Phương án cải thiện, Người phụ trách, Hạn, Trạng thái (Click chọn: Chưa xử lý / Đang xử lý / Đã xử lý), Kết quả. |
| TỔNG HỢP | BC | 15 NCC | Điểm 8 nhóm, Tổng /100, Mức đáp ứng (%), Số tiêu chí đã có điểm /21, Xếp loại, Số vấn đề (đều công thức); Đề xuất QLDL (nhập tay); Quyết định QLSX (Click chọn 4 mức). Đầu sheet: kỳ đánh giá, loại đánh giá (Click chọn: Định kỳ 6 tháng / Theo yêu cầu QLSX / Đột xuất khi có sự cố), người tổng hợp, người duyệt. |
| ĐIỂM TIÊU CHÍ | BC | 15 NCC | Điểm từng tiêu chí = `AVERAGEIFS` điểm các BP đã chấm; đếm số tiêu chí đã có điểm. |
| TIÊU CHÍ | DM | 21 tiêu chí | Chép nguyên từ *QUY TRÌNH SẢN XUẤT 09.07.2026 › 19. TIÊU CHÍ ĐÁNH GIÁ NCC GC*: tiêu chí, diễn giải, điểm, cách tính, BP đánh giá; thang xếp loại. |

### 1.3 ĐÁNH GIÁ NGƯNG HỢP TÁC NCC.xlsx (14 sheet) — bản v11/v12

| Sheet | Loại | Dòng | Nội dung |
|---|---|---|---|
| RÀ SOÁT QT DỪNG LÀM VIỆC | BC | 19 | Bảng rà soát 19 mâu thuẫn trong quy trình (định dạng STT, thứ tự bước, người duyệt, thời điểm xác nhận công nợ, thiếu biểu mẫu...) kèm kết quả xử lý v11. 18/19 đã sửa; còn thiếu lưu đồ, nhóm Zalo, số ký hiệu. |
| TỔNG HỢP | BC + BM | 10 BP, 40 hạng mục | Danh mục việc cần xử lý theo từng BP khi ngưng: phạm vi cần liệt kê (kèm *Nguồn* file › sheet), việc cần làm với NCC, chi phí nếu ngưng / nếu không ngưng kèm BP chịu, rủi ro, **Xác nhận có thể ngưng** (Có/Không), lý do. Dòng tổng mỗi BP là công thức kéo từ sheet BP. Đầu sheet: nguyên nhân, thời gian dự kiến, pháp nhân DEGO giao dịch, thương hiệu liên quan. |
| 1.1 PHÁP LÝ SX | BM | 0 (khung 8 dòng/bảng) | 4–5 bảng: Điều kiện SX/buôn bán của NCC và công ty nội bộ; Danh mục đang hợp tác (có thể đóng ở NCC nào, mã thay thế); Ủy quyền / thuê giấy đăng ký; Giấy đăng ký – lưu hành, hợp quy, nhãn; Kiểm tra thanh lý (Pháp lý chung). Mỗi bảng có Chi phí nếu ngưng / tiếp tục / BP chịu / Rủi ro; cuối sheet ô Có/Không. |
| 1.2 ĐP VTBB | BM | 0 | 7 bảng: XNT VTBB tại NCC (thương hiệu in trên bao bì, có in tên cơ sở GC, bên chuẩn bị, giá trị tồn, hướng xử lý chuyển/huỷ/giữ); VTBB chưa nhận (hàng / hoá đơn); Cọc nhãn (số cọc, sản lượng cam kết, đã đạt, còn phải thu); Đơn mua VTBB đang giao; Tồn vượt định mức hao hụt; Chứng từ NCC cung cấp; Phiếu đề nghị chuyển kho. |
| 1.3 ĐP NL-BTP | BM | 0 | 6 bảng tương tự cho NL/BTP (thêm số lô, NSX, HSD, đơn yêu cầu phối, kết quả lab). |
| 1.4 ĐP TP | BM | 0 | 3 bảng: Tiến độ đơn TP / đơn xử lý lại kèm LSX + chứng từ chưa gửi kế toán; XNT TP và hàng lỗi tại NCC; Thời gian giao hàng cập nhật cho KD. Loại dòng Click chọn (thành phẩm / hàng lỗi chờ xử lý). |
| 1.5 QLDL | BM | 0 | 14 bảng: Hợp đồng/phụ lục; Sản lượng thực hiện so cam kết; Chiết khấu, phí phạt; Phí lưu kho, hao hụt, chi phí khác, chi phí xử lý lại; Lãi chậm thanh toán; Công nợ chưa thống nhất Drive – Misa – NCC; Tổng hợp công nợ theo loại; Thanh toán, dự chi; Hoá đơn NCC GC; Tiến độ đối chiếu tồn; Dữ liệu NCC trên Drive, Misa; LSX đang mở; Hoa hồng; Phân bổ chi phí ngưng theo thương hiệu. |
| 1.6 GIÁ VỐN | BM | 0 | 2 bảng: Sản lượng và phương án với KD; So sánh giá / chính sách với NCC thay thế. |
| 1.7 XLSC | BM | 0 | 4 bảng: Sự cố chưa xong; Chi phí xử lý chưa thu/trả; Hàng lỗi tại NCC và tại kho Dr.Xanh (Click chọn nơi lưu); Kết quả yêu cầu xử lý lại, đơn lùi ngày giao. |
| 2 KINH DOANH | BM | 0 | 3 bảng: Đơn khách đang chờ thuộc NCC; Tồn kho / đơn chưa xử lý được (KD trả phương án); Mức phụ thuộc sản phẩm vào NCC. |
| 3 R&D | BM | 0 | 2 bảng: Theo dõi công thức (chuyển giao, bảo mật); Mẫu lưu và test lab. |
| 5 KHO | BM | 0 | 2 bảng: Hàng TP tại kho (Click chọn: thành phẩm / lỗi / chờ chưa có phương án); Nhận hàng thu hồi, trả hàng lỗi. |
| 6 GIÁM ĐỐC | BC + BM | 10 BP | Tổng chi phí ngưng / tiếp tục theo 10 BP (công thức), xác nhận từng BP, số BP không đồng ý; khung **Phê duyệt của QLSX** (Quyết định Click chọn: Ngưng / Tiếp tục / Họp lại; Ngày chấm dứt HĐ; Giới hạn nhượng bộ; Phân bổ chi phí); bảng *Vấn đề cần Giám đốc can thiệp*. |
| QT DỪNG LÀM VIỆC NCC GC | QT | 15 bước | Quy trình chính thức (v11): mục tiêu, thời điểm, các bước 1.0 → 7.0, biểu mẫu, danh sách file (xem 2c). Mục III lưu đồ và VII nhóm Zalo còn trống. |

Mỗi sheet BP đều theo một khuôn: đầu phiếu (NCC, ngày nhận thông báo, người lập, ngày lập) → các bảng có dòng *Nguồn: file › sheet* → bảng *Đánh giá của bộ phận* ở cuối (tổng chi phí 2 phương án tự tính, ô Có/Không, lý do).

### 1.4 Drive QLDL › 1. ĐẦU VÀO NCC GC.xlsx (10 sheet) — dữ liệu NCC gửi

| Sheet | Loại | Dòng | Nội dung |
|---|---|---|---|
| Mục Lục | DM | 8 | Liệt kê 8 sheet, loại nghiệp vụ (*Nhận thông tin từ NCC – Nhập liệu* / *từ nội bộ*), nguồn (Từ NCC GC). |
| CÔNG NỢ NCC GC GỬI | DM | 6 | Ảnh chụp sổ chi tiết công nợ do NCC (Hà Long) xuất từ phần mềm của họ: TK 131, khách IDA GLOBAL, từng dòng hoá đơn bán (mã TP của NCC + mã BTP + tên + quy cách + mã HH DEGO lồng trong diễn giải), SL, giá, tiền. |
| Bảng giá NCC GC | DM | 2 | Chính sách giá theo NCC × pháp nhân ký × mã hàng. Nhóm cột: Thời gian HĐ, Mã chính sách, NCC (Data NCC), Cty ký HĐ, ngày bắt đầu / kết thúc, số lần đổi giá, số HĐ/VB, **Tình trạng (Click chọn: Đang áp dụng / Ngưng – có giá mới / Ngưng – ngưng hợp tác)**, Dạng báo giá (Click chọn: BTP / Thành phẩm / Công nợ không xác định / VTBB), Tên pháp lý (Data pháp lý), mã hàng, mã ruột, phân loại VTBB, ĐVT, quy cách TP/thùng, thể tích, ĐVT BTP, đơn giá HĐ, **lượng tối thiểu/năm (SL thùng, SL TP)**, MOQ/đơn, đơn giá (công thức ×1.05), **% phí phạt + điều kiện phạt, % NCC chiết khấu + hình thức, % chiết khấu cho NCC + hình thức, số ngày công nợ**, nguyên tắc khác, chi tiết cấu thành giá; khối *có/không + giá* cho Thùng, Chai/túi, Nhãn, NDT, NL, ... (10 cặp). |
| Phí phối NCC GC | DM | 1 | Phí phối trộn theo NCC × tên pháp lý × dòng V × màu, ĐVT (ml), ngày áp dụng / hết hạn, trạng thái, số ngày công nợ. Ghi chú *Đề xuất tách drive riêng*. Vd Hà Long, Chitin 3.6EC dòng V2: 42 đ/ml. |
| Phí đóng gói NCC GC | DM | 7 | Phí sang chai đóng gói theo NCC + mã phí (PĐG...) + dải dung tích (vd chai tròn 5–25 ml: 500 đ chưa VAT), màng co, tấm lót thùng; giá chưa VAT / VAT / đã VAT, hiệu lực, trạng thái. |
| Pháp Lý NCC GC | DM | 2 | Ủy quyền (số, hiệu lực, hết hạn, bên cho thuê, bên nhận thuê, phạm vi, cảnh báo) + Giấy đăng ký / lưu hành + Thông báo hợp quy, mỗi khối có CẢNH BÁO PHÁP LÝ. Vd ABASBA 50EC thuê giấy của Đại Nam Á. |
| Hợp đồng NCC | DM | 4 hồ sơ + 4 HĐ | Ghi *Xây nhưng để QLDL quản lý chỉ lưu tạm ở đây*. Khối 1: danh sách hồ sơ/HĐ theo công ty nội bộ. Khối 2: trích yếu HĐ 35 cột — số/ký hiệu, tên VB, ngày ký, bên A/B, người ký, nội dung, điều kiện giá và đổi giá, sản lượng, cấu thành (bên nào chuẩn bị gì), KM/CK, công nợ, **hao hụt**, lãi phạt, hoá đơn, thanh toán, kho bảo quản, SL/thời gian tối thiểu SX, đóng date, đặt hàng, lưu mẫu, giao nhận, đối chiếu tồn, điều kiện phân phối, bảo mật, xử lý lỗi / đơn phương chấm dứt, quyền hạn hai bên, hiệu lực, trạng thái (Click chọn: Còn sử dụng / Ngưng sử dụng – đổi HĐ), link. Vd HĐ nguyên tắc Hà Long: hao hụt NL tối đa 0,3%, VTBB theo thực tế. |
| Đánh giá NCC GC định kì | Nháp | 0 | Chỉ ghi *xử lý sau* (đã chuyển thành tệp riêng ĐÁNH GIÁ ĐỊNH KÌ NCC GC). |
| Tồn kho NCC | DM | 59 | Tồn BTP tại NCC: mã vật tư (BTIDA...), tên (kèm dòng V, màu), ĐVT, số lượng; cột *Giá trị* thực tế chứa mã nhóm (BTPNC), không phải tiền. |
| Chi Phí hao hụt- lưu kho-CP khá | BM | 2 mẫu | Loại công nợ (Chi phí khác / Phí lưu kho / Hao hụt), số chứng từ Misa, mã/tên NCC, ngày ghi nhận, diễn giải, số tiền, số ngày công nợ, hình thức TT (UNC/TM), số hoá đơn, chính sách thanh toán. |

### 1.5 Drive QLDL › 2. Đầu vào nội bộ QLDL.xlsx (19 sheet) — dữ liệu các BP trong Sản xuất gửi sang

Toàn bộ là **bản chép / kéo về** từ drive của BP khác (Mục lục ghi *Nhận thông tin 100%* và nguồn).

| Sheet | Loại | Dòng | Nội dung (nguồn) |
|---|---|---|---|
| Mục lục | DM | 18 | Danh mục sheet + chức năng + nguồn (4. XNT VTBB, 3. XNT NL/BTP, Sự cố sản xuất, Pháp Lý sản xuất, Điều phối thành phẩm). |
| Pháp lý sản phẩm | DM | 2 | Kéo từ Pháp Lý sản xuất › 2. SP (ủy quyền, giấy đăng ký, hợp quy, cảnh báo). |
| Tổng hợp đơn hàng | DM | 3 | Kéo từ Điều phối TP › ĐIỀU PHỐI: danh sách đơn GC (xem 2d). Dòng 1–3 ghi loại cột: Nhập (*) / Công thức / Click chọn / Bắt buộc / Tự động. |
| Pháp lý đơn hàng | BM | 3 | Kéo từ Pháp Lý sản xuất › 4. DUYỆT ĐƠN HÀNG: Pháp lý duyệt từng đơn (xem 2e). |
| Đơn hàng ĐP NLBTP | BM | 3 | Yêu cầu mua/phối NL, BTP theo đơn: 4 khối (1. YC KD; 2. ĐP NL/BTP trả thông tin; 3. thông tin theo dõi; 4. duyệt các BP: Pháp lý / Sự cố / QLDL). |
| Đơn hàng sự cố | BM | 5 | Yêu cầu BP hỗ trợ xử lý sự cố (= TIẾN ĐỘ XLY CÁC BP). |
| BĐM VTBB | DM | 8 | Định mức VTBB / 1 TP theo mã BĐM `VT_<mã HH>_01` (xem 2f). |
| NHẬP KHO VTBB | BM | 7 | Nhập kho VTBB tại kho NCC: ngày, phân loại (nhập mua / cho tặng / lỗi / khác / chuyển kho), kho, thương hiệu, mã VTBB, lượng, mã ĐMH Misa, đơn vị nhận HĐ, số/tên HĐ, ảnh phiếu nhập của NCC, mã đơn KD, **giá đã gồm VAT + vận chuyển**, NCC, ngày mua, người yêu cầu, tài xế, số xe. Mục tiêu ghi rõ: *lấy giá VTBB*. |
| BĐM BTP | DM | 7 | Định mức NL / 1.000 kg BTP (xem 2f). |
| Nhập kho NLBTP | BM | 6 | Nhập kho NL/BTP tại NCC: phân loại, kho, thương hiệu, mã NL/BTP nội bộ, tên pháp lý, dòng V SX / KD, màu, LAB TEST (Đạt / Không đạt), hàm lượng thực tế, ĐVT, lượng, **giá NL/BTP, thành tiền**, số lô, NSX, HSD, số CAS, đơn vị nhận HĐ, mã yêu cầu. |
| Đối chiếu tồn kho VTBB | BC | 4 mẫu | Giao dịch kỳ theo NCC (G) vs hệ thống (H), lệch; tồn NCC báo (J) vs hệ thống (K), lệch; kết luận tự động (cảnh báo thiếu kho / không tìm thấy mã). |
| Đối chiếu tồn kho BTP | BC | 4 mẫu | **Giống hệt sheet VTBB** (cả tiêu đề *Mã VTBB* và dữ liệu mẫu chai PET). |
| Tổng hợp sự cố | DM | 4 | Kéo từ Sự cố sản xuất › Tổng hợp sự cố (mã sự cố ISC..., nhóm lỗi, BP chịu, kết quả: Xử lý lại / Trừ công nợ / Đưa vào chi phí). |
| Chi Phí Xử Lý THỰC TẾ (sự cố) | DM | 0 (4 dòng loại chi phí) | Loại chi phí (chai / nhãn / thùng / NDT mới), BP chịu, hình thức thu (Cấn trừ công nợ / Hạch toán chi phí / Thu tiền), chứng từ. |
| TIẾN ĐỘ XLY CÁC BP | DM | 5 | Tiến độ BP hỗ trợ sự cố (Điều phối, LAB, Kế toán, NCC). |
| 1. ĐỦ ĐK SX, BB | DM | 4 | Điều kiện SX / buôn bán của NCC và DEGO: loại, nhóm SP, dạng (Click chọn), hiệu lực, hết hạn (= hiệu lực + 365), hiện trạng. Ghi chú: thuốc buôn bán tự động gia hạn sau 1/7/2026. |
| XUẤT NHẬP TP | BM | 5 | Nhập – xuất – chuyển – trả TP (Click chọn trạng thái: 1. NHẬP TP, 2. NHẬP MẪU, 3. NHẬP DƯ, 4. CHUYỂN KHO, 5. TRẢ HÀNG, 6...), mã lô, số HĐ, NSX, HSD còn lại, kết quả Lab, biển số, tài xế. |
| XK SX BTP | BM | 2 | Xuất kho BTP cho SX theo đơn: quy đổi SL TP → kg/lít BTP (quy cách × SL × tỷ trọng), trạng thái duyệt (Đủ tồn / Chuyển kho / Mua / Tồn NCC / Chờ phối BTP), mã BĐM nội bộ / thuế, cấu thành nội bộ / thuế (bên mình / khách / NCC), SL thực tế trừ theo SX và theo KD. |
| XK SX VTBB | BM | 4 (1013 dòng chỉ có STT) | Xuất kho VTBB theo đơn: SL KD đặt, SL đặt NCC, mã BĐM, nhóm, mã VTBB, định mức / 1 TP, **tổng VTBB cần xuất = SL đặt NCC × định mức**, ĐP VTBB chốt SL, cảnh báo xuất âm kho, SL TP có hàng 3 lần, SL xuất 3 lần, *SL VTBB đang xuất tạm*, cột *Xuất chưa có hao hụt*. |

### 1.6 Drive QLDL › 3. Duyệt đơn hàng QLDL.xlsx (7 sheet)

| Sheet | Loại | Dòng | Nội dung |
|---|---|---|---|
| Mục Lục | DM | 6 | 3 sheet *Nhận thông tin 100%*, 3 sheet *Xử lý*. |
| Tổng hợp đơn hàng | DM | 3 | Bản chép sheet cùng tên ở tệp 2. |
| Tổng duyệt đơn hàng | BC | 3 | Bảng duyệt đơn theo các BP (xem 2e). Toàn bộ cột là công thức (kéo từ drive các BP, dòng 2 ghi link nguồn), cột A *ĐỦ ĐIỀU KIỆN NB (7 BP)* + B *Ngày NB duyệt đủ điều kiện*. |
| Chi tiết đơn hàng theo từng NCC | BC | 2 | Cùng cột với Tổng duyệt; ghi chú *lọc theo từng NCC GC rồi giao từng bạn QLDL phụ trách NCC đó duyệt giá*. |
| Đơn hàng ĐP NLBTP | DM | 3 | Bản chép tệp 2. |
| Đơn hàng sự cố | DM | 5 | Bản chép tệp 2. |
| XỬ LÝ LẠI | BM | 1 | Đơn yêu cầu NCC xử lý lại sau sự cố: NCC chỉ định, mã yêu cầu (lấy từ mã sự cố), SP trước / sau xử lý, các khối duyệt như đơn thường + duyệt riêng (BX) + **QLSX duyệt**, tiến độ, kết quả Lab, trạng thái. |

### 1.7 Drive QLDL › 4. BDM thành phẩm.xlsx (21 sheet)

| Sheet | Loại | Dòng | Nội dung |
|---|---|---|---|
| Mục Lục | DM | 20 | 10 sheet *Nhận thông tin 100%* (từ tệp 1 và 2), 10 sheet *Xử lý*. |
| Bảng giá NCC GC | DM | 2 | Bản chép tệp 1. |
| ĐIỀU PHỐI | DM | 2 | Bản chép Điều phối TP (nhiều ô `#REF!` / `#N/A`). |
| XUẤT NHẬP TP | DM | 5 | Bản chép tệp 2. |
| BĐM BTP / Giá BTP / BĐM VTBB / Giá VTBB | Nháp | 0 | 4 sheet trống (dự kiến kéo từ tệp 2). |
| XK SX BTP | DM | 2 | Bản chép tệp 2. |
| XK SX VTBB | DM | 4 | Bản chép tệp 2. |
| Công nợ TP đóng gói | BM | ~438 | Dán chuỗi từ Zalo (thông báo tiếp nhận đơn hàng của Hà Long — *chỉ Hà Long có*), tách công thức ra mã SP NCC, tên, quy cách, mã HH, SL, đơn giá, thành tiền; nhập tay ngày nhận đơn, mã PO; kéo mã chính sách giá, đơn giá ruột, đơn giá đóng gói; phí khác 1–3; **cột kiểm *Check đơn giá + mã HH* (Khớp / lệch)**. |
| BDM TP | BM + BC | 7 | **Bảng định mức thành phẩm** (xem 2f). Cột thông tin TP lấy từ sheet 1.1, chi tiết định mức lấy từ 1.3/1.4; Duyệt BĐM = Chọn, Ngày duyệt = Nhập. |
| CP khác từ NCC GC | BC | 4 | Chi phí theo từng đơn / LSX, *áp dụng NCC An Nông*: SL nhập, cấu thành nội bộ / thuế, đơn giá công nợ NCC, **chính sách chiết khấu + thành tiền, phí phạt dự trù + thành tiền**, tổng. |
| Phiếu in Chiết khấu | In | 1 | Bảng kê chi phí chiết khấu (đơn vị ABA → Nhà phân phối Dr.Xanh): mã, HH, SL, đơn giá, % CK, thành tiền. |
| Phiếu in phí phạt | In | 2 | Bảng kê phí phạt dự trù với NCC (An Nông): % phạt 15%, lượng cần đạt / đã đạt, người lập / trưởng BP xác nhận. |
| Tổng hợp LSX TP | BC | 1 | Danh sách LSX: mã đơn đầu tiên phát sinh BĐM, TP, cấu thành, mã ruột nội bộ / thuế, giá ruột NCC/CTY, VTBB, mã + phí GC, pháp lý, SL xuất VTBB / BTP, số HĐ. |
| LSX TP | BC | 8 | Chi tiết LSX = bung BĐM TP từng dòng thành phần. |
| Phiếu in LSX | In | 1 | Lệnh sản xuất thành phẩm (DEGO HOLDING, BP QLDL): NCC, mã đơn, mã HH, cấu thành, dòng công thức, BĐM TP / BĐM VTBB, SL TP, SL thùng, quy cách; I. NVL và VTBB (mã, ĐVT, định mức / 1 SP, tổng, đơn vị cung ứng CTY/NCC); II. Chi phí (phí sang chai đóng gói). Người phê duyệt / người lập. |
| Phiếu xuất kho SX TP | In | 1 | Phiếu đề nghị xuất kho sản xuất, cùng khung LSX; số lượng lấy từ XK SX BTP / XK SX VTBB (*không nhân theo BĐM*). |
| Tổng hợp xuất bán TP | BC | 0 | Danh sách xuất bán nội bộ theo pháp lý (ngày gửi, mã, tên, SL, đơn giá, ngày yêu cầu xuất HĐ bán). |
| Phiếu in xuất bán TP | In | 0 | Phiếu đề nghị xuất kho bán hàng. |

---

## 2. Quy trình con

### (a) Đưa NCC GC mới vào hợp tác

- **Mục đích**: có NCC GC cho sản phẩm mới hoặc thay NCC không còn đáp ứng (năng lực, chất lượng, giá).
- **Nguồn quy trình**: các bước nằm ở *QUY TRÌNH SẢN XUẤT 09.07.2026 › 1. QT LÀM VIỆC VỚI NCC MỚI* (nhóm A); tệp CHECKLIST chỉ chứa biểu mẫu. Tóm tắt để nối với biểu mẫu:
  1. Tiếp nhận yêu cầu (QLSX, từ BLĐ / BP yêu cầu) → 2. Tìm NCC (QLSX, phối hợp QLDL, Thu mua) → 3. So sánh sơ bộ, danh sách NCC tiềm năng (QLDL, QLSX duyệt) → 4. Liên hệ NCC, lập nhóm Zalo *Tên NCC – Dego hợp tác*.
  2. 4.1 Pháp lý SX kiểm pháp lý NCC (ĐKSX thuốc BVTV, ĐK buôn bán, ĐKDN) — QT ghi biểu mẫu *Mẫu 01*.
  3. 4.2 **KD lập danh mục sản phẩm hợp tác (Mẫu 01)** → QLDL → QLSX → Giám đốc duyệt; không duyệt NCC thì quay lại bước 2, không duyệt danh mục thì điều chỉnh. 4.3 Pháp lý kiểm GĐK, hợp quy từng sản phẩm.
  4. 5.x Lấy mẫu / phối mẫu, Lab test (tối đa 2 lần phối), **ĐP NL/BTP chốt công thức, lập BĐM trình QLSX duyệt**.
  5. 6.1 QLDL nhận bảng giá (phí sang chai đóng gói, phí phối chế, giá BTP/VTBB/TP), so sánh với NCC cũ / NCC tương ứng, chốt và QLSX ký (**Mẫu 04**).
  6. 6.2 QLDL lập **checklist HĐ (Mẫu 02)**, thống nhất với NCC, QLSX duyệt → soạn HĐ / phụ lục / bảng giá / biên bản → tham vấn **Pháp lý → P TCKT → Giám đốc** (mỗi BP tối đa 1 ngày) → QLSX ký nháy, Giám đốc ký → bản gốc giao P TCKT, Sản xuất lưu scan, trích thông tin gửi KD.
  7. 7.0 Lập folder, **nhóm làm việc (Mẫu 03)**, **biên bản bàn giao nội bộ (Mẫu 05)**, triển khai cho Thu mua, KD, P TCKT, Pháp lý — trước đơn hàng đầu tiên.
- **Trường dữ liệu chính**:
  - Mẫu 01: phân loại, tên pháp lý, thành phần, mã BTP, lý do chọn, sản lượng dự kiến/năm theo từng thương hiệu (ABA, IDA GLOBAL), số thùng tạm tính.
  - Mẫu 02 (25 nội dung): loại HĐ (GC / mua bán; NCC đòi HĐ nguyên tắc thì vẫn phải có HĐ mua bán / GC); danh mục; **BĐM BTP/TP (NL / 1000 lít-kg; BTP, VTBB / 1 TP)**; bên chuẩn bị NL, VTBB cho từng SP; **phương thức xuất – nhận hoá đơn** (mang VTBB sang: NCC xuất HĐ TP gộp VTBB, hoặc công ty xuất HĐ bán VTBB sang NCC; không được cả hai thì cân nhắc không hợp tác; xuất HĐ sau ngày SX, trước ngày nhận hàng); bảng giá GC, hiệu lực, thời gian báo trước khi đổi giá; chiết khấu, hoa hồng, quà tặng; **cọc nhãn** (tiền/loại nhãn, lưu kho, hoàn cọc); công nợ, thanh toán; lưu kho, bảo quản, **tỷ lệ hao hụt NL, VTBB**; phương thức đặt hàng; thời gian SX (điều kiện, thời hạn báo trễ); SL tối thiểu SX (BTP và TP); địa điểm, giao nhận, chứng từ; KCS và trách nhiệm hàng lỗi; quy trình nhập xuất NL/VTBB và **đồng bộ mã NCC – mã DEGO**; **lưu mẫu (NCC tối thiểu 2 năm; DEGO lưu mẫu chốt, đối chiếu 6 tháng/lần)**; đóng date (NSX, ngày đóng gói, số lô); bảo mật (nhãn, hình ảnh, khách hàng); đối chiếu tồn, đối chiếu công nợ (ngày, hình thức, điều chỉnh lệch, xác nhận); xử lý hàng lỗi, cận date; cập nhật pháp lý; mẫu đính kèm.
  - Mẫu 03: 5 nhóm (Đặt hàng: ĐP TP + NCC; Xuất nhập kho NL/BTP/VTBB; Kế toán: báo giá, HĐ, đối chiếu, thanh toán, cọc nhãn; Thiết kế: duyệt nhãn, mockup; Xử lý sự cố).
- **Đầu ra**: HĐ / phụ lục / bảng giá (sang *1. ĐẦU VÀO NCC GC › Bảng giá, Hợp đồng NCC, Phí phối, Phí đóng gói, Pháp lý NCC GC*), BĐM (sang *2. Đầu vào nội bộ › BĐM BTP / BĐM VTBB*), thông tin NCC cho KD, Thu mua, P TCKT.

### (b) Đánh giá định kỳ NCC GC

- **Mục đích**: đánh giá lại toàn bộ NCC GC, ghi nhận vấn đề, đề xuất cải thiện hoặc điều chỉnh kế hoạch hợp tác; NCC không đạt chuyển sang quy trình ngưng.
- **Chu kỳ**: 6 tháng/lần; hoặc theo yêu cầu QLSX; hoặc đột xuất khi có sự cố. Mỗi kỳ 1 tệp.
- **Các bước**: (1) từng BP lọc sheet NHẬP ĐIỂM theo BP mình, chấm độc lập, ghi căn cứ → (2) ghi vấn đề vào VẤN ĐỀ & PHƯƠNG ÁN → (3) QLDL tổng hợp, ghi đề xuất → (4) QLSX chọn quyết định; NCC < 60 điểm chuyển *QT DỪNG LÀM VIỆC*.
- **Cách tính**: tiêu chí nhiều BP chấm thì lấy **trung bình** các BP đã chấm; nhóm = tổng tiêu chí; tổng /100; chỉ xếp loại khi đủ **21/21** tiêu chí có điểm.
- **Danh sách NCC dựng sẵn (15)**: Hà Long, Thái Nông, Âu Việt, ADU, Đại Tâm (3 pháp nhân), Agrifuture, Thu Loan, Yamato, Basel, Niềm Tin Việt, An Nông, DuBai, ATC, Thành Phát, Pest.

Tiêu chí, trọng số và BP chấm:

| Nhóm (điểm) | Tiêu chí | Tối đa | Các mức | BP chấm |
|---|---|---|---|---|
| 1. Pháp lý và hồ sơ năng lực (15) | 1.1 Hồ sơ pháp lý đầy đủ (ĐKKD, ĐKSX, ĐK buôn bán, ủy quyền, MST còn hiệu lực) | 7 | 7 (còn hạn ≥ 6 tháng) / 5 (còn < 3 tháng, chờ bổ sung) / 2 (thiếu 1 loại, bổ sung ≤ 3 tháng) / 0 | Pháp lý SX, QLDL |
| | 1.2 Sẵn sàng ký HĐ / phụ lục / cam kết sản lượng, hao hụt | 4 | 4 / 2 / 0 | Pháp lý SX, QLDL |
| | 1.3 Minh bạch thông tin doanh nghiệp | 4 | 4 / 2 / 0 | Pháp lý SX, QLDL |
| 2. Năng lực SX và công nghệ (20) | 2.1 Công suất đáp ứng quy mô đơn | 5 | 5 / 2 / 0 | QLDL, ĐP TP |
| | 2.2 Đa dạng hình thức SX/GC (nhận NL/BTP, VTBB mang sang) | 5 | 5 / 2 / 0 | ĐP VTBB, ĐP NL/BTP |
| | 2.3 Máy móc và quy cách đóng gói | 5 | 5 / 2 / 0 | ĐP VTBB, QLDL |
| | 2.4 Khả năng test / phối theo yêu cầu (đạt trong 2 lần) | 5 | 5 / 2 / 0 | ĐP VTBB, ĐP NL/BTP, R&D |
| 3. Chất lượng sản phẩm (20) | 3.1 Tỷ lệ lỗi TP/BTP trên số đơn | 8 | 8 (< 1%) / 5 (1–3%) / 2 (3–5%) / 0 (> 5% hoặc lặp lại) | XLSC, R&D, QLDL |
| | 3.2 Hao hụt NL/BTP, VTBB so với định mức | 6 | 6 / 4 / 2 / 0 | XLSC, ĐP NL/BTP, ĐP VTBB, QLDL |
| | 3.3 Thất lạc / hư hỏng, không xuất theo FIFO | 6 | 6 / 3 (1–2 lần, có đền bù) / 0 | XLSC, ĐP NL/BTP, ĐP VTBB, QLDL |
| 4. Tiến độ giao hàng (15) | 4.1 Đúng thời gian SX cam kết (từ khi đủ NL/VTBB) | 7 | 7 / 5 (trễ ≤ 10%, báo trước 1–2 ngày) / 2 / 0 | ĐP TP |
| | 4.2 Tuân thủ thời gian báo trước khi giao nhận | 4 | 4 / 2 / 0 | ĐP TP |
| | 4.3 Đáp ứng đơn gấp / phát sinh | 4 | 4 / 2 / 0 | ĐP TP |
| 5. Giá và chi phí GC (10) | 5.1 Giá GC cạnh tranh, ổn định, khớp giá duyệt | 6 | 6 / 4 / 0 | Giá vốn, QLDL |
| | 5.2 Chính sách phí lưu kho, chiết khấu, phạt | 4 | 4 / 2 / 0 | Giá vốn, QLDL |
| 6. Hợp tác, dịch vụ, xử lý sự cố (10) | 6.1 Thái độ phối hợp nhân sự NCC | 5 | 5 / 3 / 0 | QLDL, ĐP TP, ĐP VTBB, ĐP NL/BTP |
| | 6.2 Xử lý, khắc phục sự cố (≤ 24h = 5; 2–3 ngày = 3) | 5 | 5 / 3 / 0 | XLSC, QLDL, ĐP TP |
| 7. Tài chính, thanh toán, công nợ (5) | 7.1 Đối chiếu công nợ / tồn, hoàn cọc đúng hạn | 3 | 3 / 1 / 0 | QLDL, P TCKT |
| | 7.2 Xuất hoá đơn đúng thời điểm, đúng quy định | 2 | 2 / 1 / 0 | QLDL, P TCKT |
| 8. Vị trí và logistic (5) | 8.1 Vị trí kho / nhà máy thuận tiện | 3 | 3 / 2 / 0 | ĐP TP |
| | 8.2 Hình thức giao nhận linh hoạt | 2 | 2 / 1 / 0 | ĐP TP |

Thang xếp loại: **≥ 90** Xuất sắc – ưu tiên hợp tác dài hạn · **75–89** Đạt – tiếp tục, theo dõi định kỳ · **60–74** Cần cải thiện – làm lại điều khoản, theo dõi kỹ · **< 60** Không đạt – ngưng hợp tác, tìm NCC thay thế.

- **Đầu vào**: số liệu từ Sự cố sản xuất (tỷ lệ lỗi, tốc độ xử lý), Đối chiếu tồn kho (hao hụt), Điều phối TP (tiến độ), Giá vốn, Pháp lý SX, P TCKT.
- **Đầu ra**: quyết định QLSX cho từng NCC; NCC không đạt vào quy trình (c); vấn đề và phương án có người phụ trách, hạn.

### (c) Ngưng hợp tác NCC GC

- **Mục đích**: kiểm soát chấm dứt; lập phương án thu hồi NL, BTP, VTBB, hàng lỗi, công nợ đang ở NCC; hoàn tất pháp lý, chứng từ kế toán, cập nhật dữ liệu nội bộ.
- **Điều kiện kích hoạt**: NCC vi phạm HĐ; **không đạt đánh giá định kỳ (< 60)**; hai bên không còn nhu cầu; hoặc NCC từ chối / ngừng giữa chừng (tình huống sự cố TH 1 — ĐP TP xử lý gấp, tìm NCC thay thế, báo KD; phần ngưng theo quy trình này). Quyết định chính thức do **QLSX duyệt ở bước 2.7**.
- **Các bước** (người thực hiện → phối hợp → kiểm tra → duyệt):
  1. **1.0** Tiếp nhận đề xuất / thông tin dự kiến ngưng — QLDL; phối hợp QLSX/Giám đốc.
  2. **2.0** QLDL thông báo 11 BP (Pháp lý SX, ĐP VTBB, ĐP NL/BTP, ĐP TP, Giá vốn, XLSC, P TCKT, KD, R&D, Pháp lý chung, Kho Dr.Xanh) rà soát nghiệp vụ, liệt kê việc + chi phí + điều cần thương lượng theo sheet TỔNG HỢP và sheet BP.
  3. **2.1–2.6** Đánh giá từng BP *trong phạm vi nghiệp vụ*: P TCKT (công nợ, tồn, hoá đơn — xác nhận ở 1.5 QLDL), Kho (hàng TP tại kho), KD (phương án tồn kho, đơn sót, danh mục thay thế / hợp tác đến giai đoạn nào dựa trên doanh số, lợi nhuận, khách, chi phí), R&D (mẫu lưu đến hạn, công thức đang ở NCC — trách nhiệm chất lượng và bảo mật), Pháp lý chung (thanh lý HĐ, rủi ro), Giám đốc (chỉ can thiệp khi BP không xác định được). Thời điểm: sau khi sản xuất báo số liệu.
  4. **2.7** QLDL tổng hợp, đề xuất → **QLSX phê duyệt phương án ngưng tổng thể** (sheet 6 GIÁM ĐỐC: quyết định, ngày chấm dứt HĐ, giới hạn nhượng bộ, phân bổ chi phí cho BP).
  5. **3.0** Gửi **Văn bản thông báo ngưng hợp tác** (Pháp lý chung kiểm, QLSX duyệt), họp thống nhất ngày chấm dứt, đơn dở dang, công nợ, hàng tồn, cọc nhãn, hoa hồng → biên bản họp. QLDL thực hiện.
  6. **4.0** QLSX phân công việc + deadline cho các BP (bảng phân công / checklist).
  7. **5.0** Các BP thực hiện; QLDL tổng hợp và đánh giá theo form đánh giá định kỳ → QLSX duyệt; thu hồi cọc nhãn, chốt hoa hồng; **QLDL phân bổ chi phí ngưng theo thương hiệu**, QLSX duyệt. Biểu mẫu: BB xác nhận tồn cuối kỳ, phiếu chuyển kho / xuất bán, BB đối chiếu công nợ, BB đánh giá theo tiêu chí.
  8. **5.1** **P TCKT xác nhận công nợ = 0 đồng và đủ HĐ, phụ lục, hồ sơ** (1.5 QLDL › Bảng 6), trước khi ký thanh lý.
  9. **6.0** QLDL lập BB thanh lý HĐ / BB thanh lý cọc nhãn / BB tiêu huỷ → duyệt **Pháp lý → P TCKT → Giám đốc** → QLSX ký nháy → **đại diện đúng pháp nhân đã ký HĐ** ký → gửi NCC.
  10. **7.0** Cập nhật trạng thái NCC *Ngưng hợp tác* kèm ngày, lý do; lưu đủ bộ hồ sơ; bản gốc BB thanh lý giao P TCKT, QLDL lưu scan.
- **Checklist pháp lý khi ngưng** (1.1 PHÁP LÝ SX + TỔNG HỢP): điều kiện SX/BB của NCC và công ty nội bộ còn hiệu lực đến ngày chấm dứt (lưu bản sao để truy xuất lô đã SX; kiểm hạn trước khi chốt lô cuối); danh mục đang hợp tác, mã ngưng / mã chuyển NCC; **ủy quyền, thuê giấy đăng ký** (mất ủy quyền là không được lưu hành sản phẩm); giấy đăng ký – lưu hành, hợp quy, nhãn khi đổi cơ sở SX (phí thủ tục, in lại nhãn); kiểm BB thanh lý ký đúng pháp nhân, đủ nội dung đối chiếu; đơn phương chấm dứt sai căn cứ có thể bồi thường (Điều 428 BLDS 2015).
- **Việc theo BP đáng chú ý**: VTBB in thương hiệu (IDA, ABA, Bamboo) phải huỷ có biên bản; thiếu hoá đơn đầu vào làm sai luồng pháp lý, không cấu thành được TP; NL hoá chất phải vận chuyển / lưu kho đúng điều kiện; quyết toán VTBB, NL/BTP = đã xuất – đã dùng theo định mức – tồn thực tế, đòi bồi thường phần vượt hao hụt; đối chiếu ba bên **Drive – Misa – NCC** tách theo pháp nhân; không ký thanh lý khi chưa chốt chiết khấu / phí phạt / công nợ; không thanh toán hết trước khi thu hồi xong hàng và hồ sơ.
- **Quy tắc ra quyết định**: mỗi BP so **tổng chi phí nếu ngưng** với **tổng chi phí nếu tiếp tục**, xác nhận Có/Không; QLSX ra quyết định hoặc họp lại BP vướng mắc.

### (d) Đầu vào NCC GC và đầu vào nội bộ QLDL

QLDL là **điểm gom dữ liệu**: không tự sinh dữ liệu gốc mà kéo / nhận từ NCC và từ các BP sản xuất, rồi dùng để duyệt đơn, lập BĐM TP, LSX, đối chiếu công nợ, giá vốn.

| Dữ liệu | Ai khai / nguồn | Sheet ở QLDL | Dùng cho |
|---|---|---|---|
| Bảng giá / chính sách giá theo NCC × pháp nhân × mã hàng (giá, MOQ, lượng tối thiểu/năm, phạt, chiết khấu hai chiều, ngày công nợ, cấu thành giá) | NCC gửi, QLDL nhập | 1 › Bảng giá NCC GC | Duyệt giá đơn, CP khác (CK, phạt), Công nợ TP đóng gói |
| Phí phối trộn theo SP × dòng V × màu | NCC gửi, QLDL nhập | 1 › Phí phối NCC GC | Giá BTP, duyệt đơn NL/BTP (*Phí phối đã chốt*) |
| Phí sang chai đóng gói theo dải dung tích, phụ phí màng co, tấm lót | NCC gửi | 1 › Phí đóng gói NCC GC | BĐM TP (dòng *Phí GC sang chai đóng gói*), LSX |
| Pháp lý NCC (ủy quyền, GĐK, hợp quy) | NCC + Pháp lý SX | 1 › Pháp Lý NCC GC; 2 › Pháp lý sản phẩm, 1. ĐỦ ĐK SX, BB | Duyệt pháp lý đơn |
| Hợp đồng, phụ lục (35 trường điều khoản) | NCC + QLDL | 1 › Hợp đồng NCC (tạm) | Đối chiếu, ngưng hợp tác |
| Sổ công nợ NCC gửi | NCC | 1 › CÔNG NỢ NCC GC GỬI | Đối chiếu công nợ (tệp 8) |
| Tồn kho NL/BTP tại NCC | NCC | 1 › Tồn kho NCC | Đối chiếu tồn (tệp 7) |
| Phí lưu kho, hao hụt, chi phí khác | NCC / Misa | 1 › Chi Phí hao hụt... | Công nợ (tệp 6, 8) |
| Đơn hàng GC (tổng hợp) | ĐP TP (drive Điều phối TP) | 2 › Tổng hợp đơn hàng | Duyệt đơn |
| Duyệt pháp lý đơn | Pháp lý SX | 2 › Pháp lý đơn hàng | Duyệt đơn |
| Đơn mua / phối NL, BTP | KD yêu cầu, ĐP NL/BTP trả lời | 2 › Đơn hàng ĐP NLBTP | Duyệt đơn, BĐM |
| BĐM VTBB, nhập kho VTBB (giá), đối chiếu tồn VTBB, xuất kho VTBB | ĐP VTBB (drive 4. XNT VTBB) | 2 › BĐM VTBB, NHẬP KHO VTBB, Đối chiếu..., XK SX VTBB | BĐM TP, giá, LSX |
| BĐM BTP, nhập kho NL/BTP (giá), đối chiếu tồn BTP, xuất kho BTP | ĐP NL/BTP (drive 3. XNT NL, BTP) | 2 › BĐM BTP, Nhập kho NLBTP, ... | BĐM TP, giá, LSX |
| Sự cố, chi phí xử lý, tiến độ BP hỗ trợ | XLSC (Sự cố sản xuất) | 2 › Tổng hợp sự cố, Chi Phí Xử Lý..., TIẾN ĐỘ XLY, Đơn hàng sự cố | Duyệt đơn (khối Sự cố), xử lý lại |
| Nhập – xuất – chuyển – trả TP | ĐP TP / Kho | 2 › XUẤT NHẬP TP | CP khác, công nợ TP |

**Trường dữ liệu của đơn hàng GC** (Tổng hợp đơn hàng, cột bắt buộc đánh dấu): mã PO (dạng ITP/ATP + ngày + số), trạng thái (Mới / Xử lý), NCC đề xuất, ngày đơn, thương hiệu, mã HH, tên hàng, phân loại, tên pháp lý, ĐVT, mã BĐM BTP KD (tự động), quy cách thùng, SL thùng / chai-gói, ngày yêu cầu sẵn kho NCC, yêu cầu khác, vật tư khác (ngoài chai, túi, nhãn, thùng, NDT), NVL khách mang qua, số ngày SX, đã dự trù nhãn / BTP (mã yêu cầu), trạng thái NCC duyệt nhãn, giá bán thấp nhất CSBH, khảo sát VTBB; khối tiến độ (NCC thực tế, ngày nội bộ duyệt đủ 7 BP, ngày đủ NVL, ngày NCC SX, số ngày gửi đơn, cảnh báo *TRỄ ĐƠN / LƯU Ý*, trạng thái đơn, ngày gửi đơn NCC, ngày NCC xác nhận đủ NVL, ngày dự kiến có hàng, ngày gửi / nhận mẫu Lab, kết quả Lab, diễn giải biến động, ghi chú NCC); khối số lượng (SL mẫu Lab, KD đặt, gửi NCC = KD đặt + mẫu, NCC thực SX, xuất HĐ, đã nhận, còn lại, đã nhận HĐ chưa nhận hàng, cảnh báo *SX VƯỢT ĐH / CHƯA SX HẾT*); khối **cấu thành nội bộ / cấu thành thuế** (bên mình / khách / NCC); tháng / năm / quý.

### (e) Duyệt đơn hàng QLDL

- **Mục đích**: trước khi gửi đơn GC cho NCC, đơn phải được **đủ điều kiện nội bộ (7 BP)**; QLDL duyệt cuối về chính sách giá và hoá đơn.
- **Các khối duyệt** (mỗi khối: Ngày duyệt + Trạng thái duyệt, Click chọn *Chờ duyệt / Duyệt / Huỷ / Chưa đủ TT duyệt*):

| Khối (đánh số theo sheet Tổng duyệt) | BP | Kiểm gì |
|---|---|---|
| 4. PHÁP LÝ — ĐKSX, ĐKKD, Hợp đồng, pháp lý SP | Pháp lý SX | NSX yêu cầu in trên bao bì; **đơn vị sản xuất trên nhãn**; công ty cấu thành; công ty nhận hoá đơn từ NCC; **dòng hoá đơn** (NCC → đơn vị cấu thành → đơn vị nhận HĐ đầu tiên → đơn vị xuất HĐ cho khách, vd *Hà Long → DEGO → ABA*); GĐK/lưu hành còn hạn + ngày hết hạn; hợp quy còn hạn và có thuộc đơn vị sở hữu / cấu thành / sản xuất không; đủ ĐK sản xuất (đơn vị SX), đủ ĐK của công ty nhận HĐ và công ty bán; rủi ro phải chấp nhận. |
| 5. Sự cố | XLSC | Sự cố có liên quan tới mã hàng / NCC; số lượng mẫu cần lấy. |
| 1. NGUYÊN LIỆU / BTP | ĐP NL/BTP | Ngày đủ NL/BTP (nội bộ và thuế); trạng thái (Đủ tồn / Chuyển kho / Mua / Tồn NCC / Chờ phối BTP); mã BĐM NL/BTP nội bộ và thuế; ngày SX BTP; công thức; màu; cấu thành nội bộ / thuế (bên mình / khách / NCC). |
| 2. VẬT TƯ BAO BÌ | ĐP VTBB | Ngày đủ VTBB (nội bộ / thuế); mã BĐM VTBB nội bộ / thuế; cấu thành (vd *Chai, nhãn, thùng; lấy nhãn chính dán thùng*); ghi chú rủi ro (vd *mình mang VTBB qua nhưng NCC không nhận hoá đơn đầu vào*). |
| 6. QLDL | QLDL | Thuộc chính sách đã đàm phán với NCC chưa (nếu chưa thì trao đổi trước khi gửi đơn); **hoá đơn lấy từ NCC** là gì (Thành phẩm / Phí sang chai đóng gói / Phí sang chai + thùng...); duyệt giá theo NCC phụ trách. |
| (Xử lý lại) + QLSX | Giá vốn (?) + QLSX | Sheet XỬ LÝ LẠI có thêm một khối duyệt (BX–BZ, ghi chú giá) và **QLSX duyệt** riêng. |

- Đơn NL/BTP (sheet Đơn hàng ĐP NLBTP) có 3 khối duyệt riêng: 1. Pháp lý, 2. Sự cố, 3. QLDL (phí phối đã chốt, hoá đơn lấy từ NCC).
- **Ai làm**: cột duyệt do từng BP điền ở drive của BP (Pháp Lý sản xuất › 4. DUYỆT ĐƠN HÀNG; Điều phối TP › DUYỆT ĐƠN HÀNG; drive Giá vốn › DUYỆT ĐƠN HÀNG (ĐP TP)); tệp QLDL chỉ kéo về bằng công thức; QLDL lọc theo NCC và giao người phụ trách từng NCC duyệt giá.
- **Mốc thời gian**: ngày yêu cầu sẵn kho NCC; số ngày SX theo NCC; cảnh báo *TRỄ ĐƠN* khi số ngày từ KD lên đơn đến gửi NCC quá lớn.
- **Đầu ra**: đơn gửi NCC (Điều phối TP › GỬI ĐƠN NCC), LSX TP và phiếu xuất kho SX (tệp 4).

### (f) BĐM thành phẩm

Định mức có **ba tầng**, mỗi tầng một mã, có người duyệt và ngày duyệt:

1. **BĐM BTP** (`<viết tắt SP>_<màu>_<dòng V>_<số>`, vd `ABB_TI_V1_01`, `ASPG_DO_V2_01`) — do ĐP NL/BTP / Lab lập, tính theo **1.000 kg BTP**:
   - Trường: ngày cập nhật, mã BĐM, mã công thức Lab, mã BTP, tên pháp lý, dòng V, màu, thành phần, tỷ trọng BTP sau phối, đơn vị chuẩn bị NL, ghi chú cách tính; mỗi hoạt chất một dòng: tên hoạt chất, **hàm lượng SP (%)**, **hàm lượng yêu cầu SX (%)**, tỷ lệ YCSX/SP, **sai số phối chế cho phép** (vd 5–6%), so với khung sai số nhà nước, mã NL nội bộ, tên NL, **hàm lượng trên nhãn NL**, **hàm lượng thực tế NL**, **lượng NL (kg) / 1.000 kg**; người duyệt, ngày duyệt.
   - Cách tính (suy từ số liệu): lượng NL = HL yêu cầu / HL thực tế NL × 1.000. Vd Fenobucarb 50% từ NL 98% TC → 510,2 kg; Glufosinate 20% từ NL 95% → 210,53 kg, từ NL thực tế 97,8% → 204,5 kg (cùng SP có hai BĐM theo lô NL khác hàm lượng: `_01`, `_02`). Ghi chú *Chưa tính tỷ trọng*.
2. **BĐM VTBB** (`VT_<mã HH>_01`) — do ĐP VTBB lập, tính theo **1 TP**:
   - Trường: ngày cập nhật, mã đơn đại diện, mã BĐM, mã HH, tên HH, tên pháp lý, ĐVT TP, trọng lượng TP, SL TP/hộp, SL TP/thùng, **cấu thành VTBB: bên DEGO chuẩn bị gì / bên NCC chuẩn bị gì**, ghi chú thay đổi; mỗi vật tư một dòng: nhóm (Click chọn: Chai Pet, Nắp Pet, Nhãn giấy, Nhãn thùng, Thùng carton 5 lớp...), mã VTBB, tên, ĐVT, **định mức / TP** (chai, nắp, nhãn = 1; nhãn thùng, thùng = 1 / SL TP mỗi thùng, vd 1/40 = 0,025); người duyệt, ngày duyệt.
3. **BĐM TP** (`BĐMTP_<mã HH>_01`, sheet *BDM TP*) — QLDL gộp, một dòng cho mỗi thành phần:
   - Đầu: mã đơn đầu tiên phát sinh BĐM, ngày lên đơn, mã HH, tên hàng, phân loại (P/T), tên pháp lý, thương hiệu, ĐVT, đơn vị thể tích (g/ml), thể tích trên nhãn, quy cách thùng, quy cách hộp, mã SP gốc (dòng V + màu), màu, **cấu thành nội bộ** (vd *IDA: chai, nhãn, thùng, lấy nhãn chính dán thùng, túi PE / Hà Long: BTP, phí đóng gói*).
   - Dòng chi tiết: loại thành phần (**Chai, Nắp, Nhãn, NDT, Thùng, Cốc đong, BTP ruột, Phí GC sang chai đóng gói**; LSX còn có túi PE, hộp, tem, màng co theo Mẫu 04), **phân loại bên cung ứng (CTY / NCC)**, mã vật tư, tên, ĐVT, **chi tiết sử dụng / 1 TP** (chai/nắp/nhãn/cốc 1; NDT, thùng 1/quy cách thùng; BTP ruột = thể tích trên nhãn, vd 450 ml; phí đóng gói 1), mã BĐM VTBB, mã BTP ruột, mã BĐM TP; có hai bộ cột cho **cấu thành nội bộ** và **cấu thành thuế**; Duyệt BĐM (Chọn) + ngày duyệt.
- **Đơn vị**: BTP theo ml / g (quy đổi lít / kg bằng `/1000` × tỷ trọng); VTBB theo Cái; phí theo Chai.
- **Hao hụt**: **không có cột hao hụt** trong cả ba tầng BĐM. Hao hụt chỉ xuất hiện ở: điều khoản HĐ (Hà Long: NL tối đa 0,3%, VTBB theo thực tế), tiêu chí đánh giá 3.2, quyết toán khi ngưng, *Chi phí hao hụt – lưu kho* (công nợ), cột *Xuất chưa có hao hụt* ở XK SX VTBB. Phần dư khi xuất là **mẫu Lab** (SL gửi NCC = SL KD đặt + SL mẫu, vd 200 + 2; BTP thêm 1 chai), không phải hao hụt.
- **Cách dùng**: đơn hàng → mã BĐM TP → **LSX TP** (bung từng thành phần × SL TP, ghi đơn vị cung ứng CTY/NCC) → **Phiếu in LSX** (I. NVL và VTBB; II. Chi phí) → **Phiếu xuất kho SX TP** (SL lấy từ XK SX BTP / VTBB thực tế, không nhân BĐM) → **CP khác** (chiết khấu, phí phạt dự trù theo chính sách) → **Công nợ TP đóng gói** (so đơn giá NCC báo với giá mình tính = ruột + đóng gói + phí khác).

---

## 3. Trùng lặp (bản chép giữa các tệp)

So bằng tập tiêu đề 12 dòng đầu (Jaccard ≥ 0,6), cả bộ `tailieusanxuat`. **1,00** = cùng tiêu đề.

| Sheet trong nhóm B | Là bản chép của / trùng với |
|---|---|
| 2 › Tổng hợp đơn hàng; 3 › Tổng hợp đơn hàng; 4 › ĐIỀU PHỐI | Bản sao ĐIỀU PHỐI THÀNH PHẨM (NHÁP) › ĐIỀU PHỐI; Drive QL Giá vốn › 1. ĐẦU VÀO GIÁ VỐN / 2. DUYỆT ĐƠN HÀNG BTP VÀ TP › ĐIỀU PHỐI (0,92–1,00) |
| 3 › Tổng duyệt đơn hàng; 3 › Chi tiết đơn hàng theo từng NCC | Bản sao ĐIỀU PHỐI TP › DUYỆT ĐƠN HÀNG; Drive QL Giá vốn › DUYỆT ĐƠN HÀNG (ĐP TP) (0,74–0,91) |
| 2 › Đơn hàng ĐP NLBTP = 3 › Đơn hàng ĐP NLBTP | Drive QL Giá vốn › Điều phối ĐH NLBTP (0,93) |
| 2 › Đơn hàng sự cố = 3 › Đơn hàng sự cố = 2 › TIẾN ĐỘ XLY CÁC BP | Sự cố sản xuất › TIẾN ĐỘ XLY CÁC BP (0,98–1,00) |
| 2 › Tổng hợp sự cố; 2 › Chi Phí Xử Lý THỰC TẾ | Sự cố sản xuất › Tồng hợp sự cố (0,88), Chi Phí Xử Lý THỰC TẾ (1,00) |
| 3 › XỬ LÝ LẠI | Bản sao ĐIỀU PHỐI TP › YÊU CẦU XỬ LÝ LẠI (1,00); Sự cố sản xuất › YÊU CẦU ĐP XLY LẠI (0,77) |
| 2 › Pháp lý sản phẩm; 1 › Pháp Lý NCC GC | Pháp Lý sản xuất › 2. SP (1,00) và 2.2 NCC GC SH (0,90–0,96) |
| 2 › 1. ĐỦ ĐK SX, BB | Pháp Lý sản xuất › 1. ĐỦ ĐK SX, BB (1,00) |
| 2 › Pháp lý đơn hàng | Pháp Lý sản xuất › 4. DUYỆT ĐƠN HÀNG (0,99) |
| 1 › Hợp đồng NCC | Pháp Lý sản xuất › HỢP ĐỒNG (coppy QLDL) (0,97) |
| 2 › XUẤT NHẬP TP = 4 › XUẤT NHẬP TP | Bản sao ĐIỀU PHỐI TP › NHẬP-XUẤT TP (1,00); QLDL 6 › NHẬP-XUẤT TP (0,98) |
| 2 › XK SX BTP = 4 › XK SX BTP; 2 › XK SX VTBB = 4 › XK SX VTBB | (1,00) |
| 2 › Đối chiếu tồn kho VTBB = 2 › Đối chiếu tồn kho BTP | QLDL 7 › Đối chiếu tồn kho VTBB / BTP / TP / hàng lỗi / Tổng hợp (1,00 — cùng một khuôn chưa tách); QLDL 8 › Lịch sử đối chiếu (0,88) |
| 2 › NHẬP KHO VTBB; 2 › Nhập kho NLBTP | Drive QL Giá vốn › Giá Nhập kho VTBB / Giá Nhập kho NLBTP (0,93–0,95) |
| 1 › Bảng giá NCC GC = 4 › Bảng giá NCC GC | Drive QL Giá vốn › 1. ĐẦU VÀO GIÁ VỐN, 2. DUYỆT ĐƠN HÀNG › Bảng giá NCC GC (0,98–1,00) |
| 1 › Phí phối NCC GC; 1 › Phí đóng gói NCC GC | Drive QL Giá vốn › 1. ĐẦU VÀO GIÁ VỐN (và 2.) (1,00) |
| 1 › CÔNG NỢ NCC GC GỬI | QLDL 8 › CÔNG NỢ NCC GC GỬI (1,00) |
| 1 › Chi Phí hao hụt- lưu kho-CP khác | QLDL 6 › cùng tên; QLDL 7 › Phí lưu kho và hao hụt (nội bộ / NCC GC); Drive QL Giá vốn › Phí Lưu kho NCC GC (Hàng Tháng) (0,94–1,00) |
| 1 › Tồn kho NCC | QLDL 7 › Tồn kho từ NCC GC (0,90) |
| 4 › BDM TP; 4 › LSX TP; 4 › CP khác từ NCC GC | Drive QL Giá vốn › 1. ĐẦU VÀO GIÁ VỐN và 2. DUYỆT ĐƠN HÀNG › cùng tên (1,00) — BĐM TP đang được **dựng song song ở QLDL và Giá vốn** |
| 4 › Công nợ TP đóng gói | QLDL 6 › Công nợ TP đóng gói (0,64, đã khác cột) |
| 4 › CP khác từ NCC GC | QLDL 6 › CN chiết khấu và phí phạt NCC (0,69) |
| 4 › Phiếu in xuất bán TP | Bản sao ĐIỀU PHỐI TP › P.XUẤT BÁN HÀNG (0,68) |
| Ngưng hợp tác › QT DỪNG LÀM VIỆC NCC GC | QUY TRÌNH SẢN XUẤT 09.07.2026 › cùng tên (0,78 — bản trong tệp ngưng là v11 đã sửa) |
| Định kỳ › TIÊU CHÍ | QUY TRÌNH SẢN XUẤT › 19. TIÊU CHÍ ĐÁNH GIÁ NCC GC (ghi *chép nguyên*) |

Kết luận: tệp 2 và tệp 3 gần như **chỉ là gương** của drive các BP; tệp 4 chép tiếp từ tệp 1 + 2; cụm Giá vốn chép lại gần hết tệp 4. Một bản ghi đơn hàng xuất hiện ở ít nhất 5–6 sheet.

---

## 4. Đối chiếu ERP (ước lượng)

Căn cứ: mô tả ERP DEGO + đọc nhanh nhánh `origin/erp-v2` (module `supplier`, `contract`, `packaging_cost` duoc-CR-784). Chưa kiểm hết màn hình.

### 4.1 Đã có hoặc gần có

| Nhu cầu sản xuất | ERP hiện có | Mức khớp |
|---|---|---|
| Danh sách NCC GC (tên viết tắt, tên pháp lý, MST, địa chỉ, ngày công nợ) | `Supplier` (code = tên viết tắt, name, tax_code, address, payment_terms, is_active, inspection_days, return_days, invoice_deadline) | Khớp phần lõi. Thiếu: nhóm SP được phép SX, địa chỉ kho, giờ làm việc, thời gian báo trước nhận hàng, nhân sự ĐP phụ trách, **trạng thái Ngưng hợp tác kèm ngày + lý do** (chỉ có is_active), lịch nghỉ lễ NCC. |
| Hợp đồng NCC | `Contract` (party, company_id = pháp nhân ký, loại, ngày, đã ký, status active / expired / **liquidated** / cancelled, tệp) | Khớp phần đầu phiếu. Thiếu 30 trường điều khoản (hao hụt, MOQ, thời gian SX, lưu mẫu, đóng date, cọc nhãn, chiết khấu hai chiều, phạt, đối chiếu...), loại VB phụ lục / biên bản ngoài HĐ, lượng cam kết theo năm. |
| Sản phẩm, mã HH, mã VTBB, mã NL/BTP | Danh mục sản phẩm | Có mã; thiếu thuộc tính SX: tên pháp lý ↔ mã, dòng V, màu, mã BTP ruột, tỷ trọng, hàm lượng. |
| YCMH / YCBG / ĐMH | Có đủ luồng mua | Dùng được cho **mua NL, BTP, VTBB** (sheet Đơn hàng ĐP NLBTP, NHẬP KHO VTBB ghi cả *mã ĐMH Misa*). Chưa có **đơn đặt gia công TP gửi NCC GC** (PO ITP/ATP...) với số ngày SX, mẫu Lab, tiến độ 3 lần nhập. |
| Công nợ | `payable`, phiếu đề nghị thanh toán | Có công nợ mua. Chưa có: đối chiếu ba bên Drive – Misa – NCC, chiết khấu / phí phạt dự trù theo chính sách, phí lưu kho / hao hụt NCC, lãi chậm trả, hoa hồng, cọc nhãn. |
| Kho | `inventory`, `goods_receipt` | Có nhập kho. Chưa có **kho tại NCC GC** (VTBB, BTP gửi ở NCC), xuất kho SX theo đơn, xuất tạm, đối chiếu tồn với NCC. |
| Định mức bao bì theo mã TP + sổ giá + lịch sử mua | `packaging_cost`: `PackagingBom` (fg_code, fg_name, legal_name, **carton_qty**), `PackagingBomPart` (5 vai trò cố định **Chai, Nắp, Nhãn, Nhãn thùng, Thùng**, một mã mỗi vai trò), sổ giá (lịch sử mua, dòng ĐMH, sổ Misa), báo giá VTBB, mô phỏng tác động giá, cảnh báo thiếu giá / thiếu quy cách thùng / lệch ĐVT | Khớp đúng phần **BĐM VTBB cơ bản** của sản xuất (chai, nắp, nhãn = 1/TP; nhãn thùng, thùng = 1/quy cách thùng). |
| Đánh giá NCC | Công cụ AI `supplier_scorecard` (tính từ dữ liệu mua) | Không phải phiếu chấm 21 tiêu chí nhiều BP. |

### 4.2 BĐM thành phẩm sản xuất rộng hơn định mức bao bì ERP ở đâu

| Điểm | Sản xuất (Excel) | ERP `packaging_cost` |
|---|---|---|
| Thành phần | Chai, nắp, nhãn, NDT, thùng **+ cốc đong, túi PE, hộp, tem, màng co, tag** | 5 vai trò cố định (thêm vai trò được nhưng phải thêm mã enum) |
| Nhiều mã cùng loại | Có thể (vd hai nhãn) | Ràng buộc duy nhất (bom_id, part_type) — một mã mỗi vai trò |
| **NL / BTP ruột** | BĐM TP có dòng *BTP ruột* (ml/TP); BĐM BTP tính NL / 1.000 kg theo hàm lượng, sai số phối chế, tỷ trọng | Không có |
| **Phí gia công** | Dòng *Phí GC sang chai đóng gói* (mã PĐG theo dải dung tích), phí phối trộn theo ml | Không có |
| **Bên cung ứng** | Mỗi thành phần ghi CTY hay NCC chuẩn bị; cấu thành theo thương hiệu (IDA mang chai, nhãn; Hà Long lo BTP, phí) | Không có (ngầm định công ty mua hết) |
| **Hai bộ cấu thành** | Cấu thành **nội bộ** và cấu thành **thuế** (mã BĐM nội bộ / thuế, luồng hoá đơn NCC → cấu thành → nhận HĐ → bán) | Không có |
| Phiên bản / lô | Mã `_01`, `_02` theo lô NL khác hàm lượng; mã đơn đầu tiên phát sinh BĐM | Một BĐM mỗi mã TP (fg_code unique) |
| Duyệt | Người duyệt + ngày duyệt mỗi tầng; QLSX duyệt BĐM | Có vết sửa (AuditMixin), không có bước duyệt |
| Hao hụt | Không nằm trong BĐM (ở HĐ, đánh giá, quyết toán) | Không có |
| Dùng để | LSX, phiếu xuất kho SX, quyết toán VTBB / NL với NCC, giá vốn TP | Tính chi phí bao bì / TP và / thùng, tác động giá |

### 4.3 ERP chưa có

1. **Hồ sơ NCC GC mở rộng** và **checklist đưa NCC vào hợp tác** (danh mục hợp tác theo thương hiệu, checklist 25 điều khoản có cột bảo mật, nhóm làm việc, biên bản bàn giao).
2. **Chính sách giá NCC GC** theo NCC × pháp nhân × mã hàng: MOQ, lượng tối thiểu/năm, % phạt + điều kiện, chiết khấu hai chiều, ngày công nợ, cấu thành giá; phí phối trộn; phí sang chai đóng gói theo dải dung tích.
3. **Pháp lý sản phẩm / NCC**: ủy quyền, thuê giấy đăng ký, GĐK lưu hành, hợp quy, điều kiện SX/buôn bán kèm cảnh báo hết hạn.
4. **Đơn đặt gia công và duyệt 7 BP** (pháp lý, sự cố, NL/BTP, VTBB, QLDL, giá vốn, QLSX) với luồng hoá đơn nhiều pháp nhân.
5. **BĐM BTP và BĐM TP đầy đủ**, LSX, phiếu xuất kho SX.
6. **Kho tại NCC GC** + xuất tạm + đối chiếu tồn định kỳ với NCC + quyết toán hao hụt.
7. **Đánh giá định kỳ NCC GC** (21 tiêu chí, nhiều BP chấm, trung bình, xếp loại, sổ vấn đề, QLSX quyết định).
8. **Quy trình ngưng hợp tác** (phiếu 10 BP, so chi phí hai phương án, QLSX phê duyệt, chuỗi biên bản, xác nhận công nợ = 0).
9. Sự cố sản xuất và yêu cầu xử lý lại (thuộc nhóm khác nhưng nối vào duyệt đơn).
10. Công nợ phía NCC GC: đối chiếu sổ NCC gửi, kiểm đơn giá tiếp nhận đơn (Công nợ TP đóng gói), chiết khấu / phí phạt dự trù, cọc nhãn, hoa hồng, phí lưu kho.

---

## 5. Câu hỏi / mâu thuẫn

1. **Số và tên biểu mẫu lệch nhau**: QT làm việc NCC mới ghi *Check pháp lý → Mẫu 01*, nhưng Mẫu 01 là danh mục hợp tác; QT ghi *Mẫu 03 – Checklist quy trình làm việc*, tệp có Mẫu 03 = Nhóm làm việc (tiêu đề bên trong lại ghi *MẪU 04*); Mẫu 04 ghi *mẫu cũ chưa chốt*; Mẫu 06 và DANH SÁCH TỔNG trống. Bộ mẫu chính thức là bộ nào?
2. **STT bị Excel đổi thành ngày** ở QT làm việc NCC mới (4.1, 4.2, 4.3 hiện 2026-01-04, 02-04, 03-04) — lỗi giống mục 1 của bảng rà soát quy trình ngưng, chưa sửa ở tệp QUY TRÌNH.
3. **Đánh số khối duyệt đơn không thống nhất**: Tổng duyệt đơn hàng đánh 4. Pháp lý, 5. Sự cố, 1. NL/BTP, 2. VTBB, 6. QLDL (thiếu số 3); sheet Đơn hàng ĐP NLBTP đánh 1. Pháp lý, 2. Sự cố, 3. QLDL. *7 BP* gồm những BP nào (Giá vốn, QLSX, Lab có tính không)?
4. **Thang điểm 1.1**: 7 điểm khi còn hạn ≥ 6 tháng, 5 điểm khi < 3 tháng — khoảng 3–6 tháng chấm mấy?
5. Hướng dẫn đánh giá định kỳ liệt kê BP chấm *QLDL, ĐP NL/BTP, ĐP VTBB, ĐP TP, XLSC, P TCKT, Pháp lý SX*, nhưng sheet NHẬP ĐIỂM còn có **R&D** và **Giá vốn** chấm; ngược lại P TCKT không có dòng chấm nào ở NHẬP ĐIỂM dù tiêu chí 7.1/7.2 ghi P TCKT.
6. Đại Tâm là **3 pháp nhân** nhưng chấm chung một dòng; NCC nhiều pháp nhân thì đánh giá và ngưng theo NCC hay theo pháp nhân? (Quy trình ngưng nhấn mạnh ký thanh lý theo đúng pháp nhân.)
7. **Hao hụt** không có trong BĐM: định mức hao hụt cho phép (NL 0,3% theo HĐ Hà Long) để ở đâu khi tính xuất kho và quyết toán? Cột *Xuất chưa có hao hụt* ở XK SX VTBB chưa có công thức.
8. **Lỗi dữ liệu mẫu trong BĐM / LSX**: Phiếu in LSX ghi định mức chai, nắp, nhãn = **1000 / 1 SP** (đúng là 1); BDM TP dòng BTP ruột ĐVT *Cái* nhưng giá trị 450 (thực là ml); LSX TP hiển thị NDT, thùng = 0 (làm tròn 1/30); XK SX VTBB mã HH4995 (HAIHAMEC) nhưng tên pháp lý ghi JAPA VIL 110SC; BĐM VTBB dùng cùng mã NHG4995 cho cả nhãn giấy và nhãn thùng.
9. **Đối chiếu tồn kho BTP** dùng nguyên tiêu đề và dữ liệu của VTBB (QLDL 7 cũng vậy cho TP, hàng lỗi) — khuôn đối chiếu BTP / TP / hàng lỗi chưa được dựng riêng.
10. **Phiếu xuất kho SX** lấy SL từ sheet xuất thực tế *không nhân theo BĐM* (vd 2.000 cho đơn 192 chai), còn LSX nhân theo BĐM — hai phiếu cho cùng đơn ra hai số khác nhau; số nào là chuẩn để quyết toán?
11. **Tồn kho NCC › cột Giá trị** chứa mã nhóm (BTPNC) chứ không phải tiền — thiếu giá trị tồn mà quy trình ngưng yêu cầu.
12. **BĐM TP dựng ở hai nơi** (QLDL tệp 4 và Drive QL Giá vốn) với tiêu đề giống hệt — ai là chủ dữ liệu BĐM TP: ĐP NL/BTP + ĐP VTBB lập, QLDL gộp, hay Giá vốn?
13. **Công nợ TP đóng gói** chỉ áp cho Hà Long (NCC duy nhất gửi thông báo tiếp nhận đơn); NCC khác kiểm đơn giá bằng gì? Cột *Ngày gửi đơn NCC* đang ra ngày năm 1967 / 2109 (công thức sai kiểu số).
14. Quy trình ngưng: **lưu đồ, nhóm Zalo, số ký hiệu** còn trống; sheet *Trang tính21* của tệp 6 lỗi `#REF!` (ghi trong 1.5 QLDL › Bảng 7); sheet *Đối chiếu phí lưu kho và hao hụt* trống.
15. Tình huống sự cố TH 1 (NCC ngừng giữa chừng) ở QUY TRÌNH SẢN XUẤT giao ĐP TP, còn quy trình ngưng giao QLDL — đã ghi chú nhưng TH 1 chưa sửa.
16. **Cấu thành thuế vs nội bộ**: định nghĩa chính xác và quy tắc chọn mã BĐM thuế khác mã nội bộ chưa có văn bản; ví dụ mẫu đều ghi giống nhau (BTP / BTP) hoặc *Ví dụ cụ thể*.
17. Thuốc buôn bán *tự động gia hạn sau 1/7/2026* (1. ĐỦ ĐK SX, BB) trong khi ngày hết hạn tính bằng hiệu lực + 365 — cảnh báo hết hạn có còn đúng cho loại này?
