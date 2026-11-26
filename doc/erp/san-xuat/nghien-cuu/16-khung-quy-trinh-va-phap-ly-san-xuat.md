# Nhóm A - Khung quy trình sản xuất và pháp lý (phòng Sản xuất DEGO Holding)

Nguồn đọc (không sửa tệp): thư mục *tailieusanxuat*
- **QUY TRÌNH SẢN XUẤT 09.07.2026.xlsx** (26 sheet) - viết tắt **[QT]**
- **DRIVE ĐẦU VÀO SX 11.09.2026 (chốt).xlsx** (12 sheet) - viết tắt **[DRV]**
- **Pháp Lý sản xuất.xlsx** (9 sheet) - viết tắt **[PL]**

Cách đọc: openpyxl đọc toàn bộ ô (kể cả ô gộp) + mở zip đọc chữ trong lưu đồ (xl/drawings, thẻ `a:t`); bản dump ở `D:\tmp\sx-gom\dump\`, script ở `D:\tmp\sx-gom\scripts\`. Lưu đồ (cột III. LƯU ĐỒ) chỉ là hộp chữ lặp lại tên bước, không thêm nội dung mới so với bảng chi tiết.
Không chép số điện thoại, CCCD, tài khoản ngân hàng, tên người ký; chỉ ghi tên trường.

Viết tắt dùng trong ghi chú (lấy từ sheet *16. THUẬT NGỮ, VIẾT TẮT*): QLSX quản lý sản xuất; QLDL quản lý dữ liệu (đầu mối NCC GC, chứng từ, công nợ); ĐP TP / ĐP NL/BTP / ĐP VTBB điều phối thành phẩm / nguyên liệu - bán thành phẩm / vật tư bao bì; GV giá vốn (GVSX, GVKD); NSPL nhân sự pháp lý; XLSC xử lý sự cố; P TCKT phòng tài chính kế toán; TM / QLTM thu mua / quản lý thu mua; KD kinh doanh; BPYC bộ phận yêu cầu; NTV Nhà máy Niềm Tin Việt; NB nội bộ (đối lập Thuế); BĐM bảng định mức; LSX lệnh sản xuất; MOQ lượng đặt tối thiểu; TN trưởng nhóm; TNĐP trưởng nhóm điều phối.

**Lưu ý chất lượng dữ liệu chung**: ở hầu hết sheet quy trình, số bước dạng `2.1`, `1.3`... đã bị Excel tự đổi thành ngày (ví dụ `2.1` thành 02/01/2026, `1.10` thành 01/10/2026). Khi đọc / nhập máy phải quy đổi ngược (ngày = bước con, tháng = bước cha). Ghi chú này đã quy đổi sẵn.

---

## 1. Bảng kiểm kê

Loại sheet: **QT** quy trình bằng chữ; **BM** biểu mẫu nhập liệu; **DM** danh mục dữ liệu; **BC** báo cáo / theo dõi; **TC** tra cứu tham chiếu; **NH** nháp / bỏ. *Dòng thật* = số dòng có dữ liệu (đã trừ dòng tiêu đề, ước lượng).

### 1.1 [QT] QUY TRÌNH SẢN XUẤT 09.07.2026.xlsx

| Sheet | Loại | Dòng thật | Nội dung |
|---|---|---|---|
| TIẾN ĐỘ DRIVE | BC | ~203 | Bảng đối chiếu tiến độ xây từng sheet của các Drive SX (Drive 1 chính sách giá vốn 23 sheet, Drive 2 QLDL NCC 32 sheet, XNT VTBB 30, công nợ 18, XNT NL/BTP 15...); trạng thái 108 Hoàn thành / 86 Đang thực hiện / 9 Chưa bắt đầu; team QLDL, GV, KSKH, ĐP. Ghi chú: *đổi Data 1 thì mọi Drive phải chạy lại* |
| ĐẦU VÀO ĐẦU RA | TC | 16 | 16 đầu việc của QLDL, mỗi việc ghi đầu vào và kết quả (BĐM TP, LSX TP, lấy hóa đơn BTP / phối / TP, phiếu bán nội bộ + phụ lục, công nợ, đối chiếu tồn, chiết khấu - hoa hồng - phí phạt, bảng giá chính sách NCC, pháp lý NCC, hợp đồng, hao hụt, mua NL/BTP/VTBB tại NCC, sự cố, duyệt đơn) |
| MỤC LỤC | TC | 27 | Danh mục 26 quy trình / tài liệu kèm trạng thái cập nhật 14/8/2026 (Hoàn thành / Cần kiểm tra lại / Đang thực hiện) và các ý cần bổ sung |
| QT DỪNG LÀM VIỆC NCC GC | QT | 7 bước (+6 bước con) | Quy trình ngưng hợp tác NCC GC |
| 6. QT QUẢN LÝ NCC GC | QT | 18 bước | QLDL: xử lý chứng từ đơn hàng, mua NL/BTP/VTBB tại NCC, quản lý dữ liệu NCC (pháp lý, hợp đồng, phí, hoa hồng, dự chi) |
| 1. QT LÀM VIỆC VỚI NCC MỚI | QT | 7 bước (~30 bước con) | Tìm, đánh giá, check pháp lý, test mẫu, bảng giá, hợp đồng NCC mới |
| 2. QT KHAI BÁO SX | QT | 3 khối (~45 dòng) | Ai khai báo mã gì, luồng duyệt - khai Misa, quy tắc đặt mã / tên |
| 2.1 QT KHAI BÁO MÃ YÊU CẦU ĐẶT | QT (nháp) | 14 loại mã | Quy tắc mã chứng từ yêu cầu (đơn đặt TP, sự cố, xử lý lại, phối BTP, khảo sát, BĐM, LSX); khung chép từ QT2 |
| 3. QT KHẢO SÁT VÀ TÍNH GIÁ VỐN | QT | 3 khối (~12 bước) | Khảo sát giá, check giá đơn SX, check giá TP sau SX |
| 4. QT QL ĐƠN HÀNG SX GC | QT | ~20 bước | Điều phối đơn hàng SX gia công + hủy đơn |
| 5. QT PHÁP LÝ SẢN XUẤT | QT | 2 khối (~10 bước) | Duyệt pháp lý đơn hàng + quản lý hồ sơ pháp lý |
| 7. QT BĐM THUẾ | QT | 4 khối (~16 bước) | Làm BĐM BTP / VTBB / TP (nội bộ và thuế) |
| 8. QT QL NLBTP | QT | 10 khối (~45 bước) | Toàn bộ nghiệp vụ NL/BTP |
| 9. QT QL VTBB | QT | 10 khối (~45 bước) | Toàn bộ nghiệp vụ VTBB, cọc nhãn |
| 10. QT QL DVVC | QT | 5 bước | Đặt Grab, tạm ứng, thanh toán theo thương hiệu |
| 11. QT XL SỰ CỐ TRONG SX | QT | 8 bước | Sự cố trước khi TP nhập kho |
| 12. QT XL SỰ CỐ SAU SX | QT | 8 bước | Sự cố sau SX (kho, khách, vận chuyển) |
| TH sự cố trong SX (chốt QT 11 ...) | TC | 10 + 5 | Ma trận 10 trường hợp sự cố: mức nghiêm trọng, phương án, luồng hóa đơn, ai chịu chi phí |
| 13. LINK DRIVE | TC | 35 | Danh sách Drive / file đang dùng, mục đích, BP phụ trách, cấp bảo mật, trạng thái (Sử dụng / Điều chỉnh / Bỏ / Tạo mới) |
| 14. MẪU BIỂU | TC | 37 | Danh mục 37 chứng từ: phân loại NB / Thuế, người lập, thời điểm, nơi duyệt, nơi nhận, nơi lưu (bản gốc P TCKT, scan trên Drive) |
| 15. NHÓM ZALO | TC | 51 | 51 nhóm Zalo: mục đích, BP phụ trách, thành viên, **cấp bảo mật 1-4** (1 không bảo mật, 2 giá vốn, 3 công thức SX, 4 NL mã hóa), trạng thái, đổi tên dự kiến |
| 16. THUẬT NGỮ, VIẾT TẮT | TC | 60 | Bảng thuật ngữ |
| 17. TT NCC GC | DM | 15 NCC | Hồ sơ vận hành từng NCC GC: tên GCNĐKKD, viết tắt, nhóm SP, MST, địa chỉ trụ sở / kho, giờ làm việc, chính sách lưu kho, báo trước nhận hàng, thời điểm xuất hóa đơn, MOQ TP, thời gian SX khi đủ VTBB, lượng phối BTP tối thiểu, hao hụt, ai chuẩn bị phụ gia, hình thức SX, hình thức giao nhận, hợp đồng, *nhân sự liên hệ (có SĐT - không chép)*, lưu ý, đánh giá ưu / nhược |
| 18. TT SP | DM | 170 | Sản phẩm theo NCC GC (Hà Long 127, An Nông 16, Yamato 9, Thu Loan 6, ATC 5, Basel 4...) và công ty phân phối (DEGO 77, IDA GLOBAL 60, ABA 33). 19 cột thiết kế (quy cách, MOQ BTP, hao hụt phối / chiết rót / VTBB, thời gian SX, công nợ, chiết khấu, bên chuẩn bị NL / VTBB) nhưng **chỉ 3 cột có dữ liệu đủ**, các cột chính sách gần như trống |
| 19. TIÊU CHÍ ĐÁNH GIÁ NCC GC | TC | 25 tiêu chí | Thang 100 điểm 8 nhóm, xếp loại, chu kỳ 6 tháng |
| 20. LƯU TRỮ | TC | 15 | Cấu trúc folder lưu trữ (tham khảo Thu mua): NCC > PO > mã ĐMH > file; báo giá; BB đối chiếu công nợ; hợp đồng; pháp lý khác; so sánh NCC |

### 1.2 [DRV] DRIVE ĐẦU VÀO SX 11.09.2026 (chốt).xlsx

| Sheet | Loại | Dòng thật | Nội dung |
|---|---|---|---|
| Nháp chung | NH / TC | ~55 | Bản thiết kế danh mục: loại data, ai khai báo, nhóm (click chọn / data quản lý), trường, quy định, có trên Misa không, BP cung cấp. Là đặc tả gốc của các sheet Data* |
| Mục lục | TC | 10 | 10 nhóm data click chọn, mục đích, nguồn gốc (Admin nhập tay, thu mua, pháp lý, ĐP NL/BTP, ĐP VTBB, QLDL, ĐP TP) |
| Admin | DM | ~35 | Danh mục dùng chung: công ty nội bộ (10), bộ phận / thương hiệu, kho (~35 kho), ĐVT, phân loại nhập / xuất / tồn, khoản mục chi phí, màu, độ trong, hình dạng, phân loại SP, dòng V, **trạng thái sự cố** |
| Data thu mua | DM | ~150 | NCC thu mua (147), đơn vị vận chuyển (6), thời gian mua theo loại VTBB (127), MOQ theo NCC VTBB (84), tiêu chuẩn NL (95 mã NL: xuất xứ, ngoại quan, màu, độ tan, độ ẩm, pH, hàm lượng, mã CAS, thuộc phụ lục nghị định). Cột danh mục VTBB / NL (A-D) **trống** |
| Data pháp lý (Tổng) | DM | 369 | Pháp lý sản phẩm (262 tên pháp lý): ủy quyền, GĐK / lưu hành, hợp quy, link, đơn vị thuê, NCC1-3, hình thức. **Bản chép của [PL] 2.1 TRINH ABA** |
| Data NLBTP | DM (khung) | 1 | Chỉ có tiêu đề + 1 dòng mẫu (quy tắc tên BTPR / BTPM) |
| Data TP | DM | 15 | Thông tin NCC GC phía ĐP TP (tách từ *17. TT NCC GC*), thêm cột *nhân sự ĐP TP phụ trách* |
| Data VTBB | DM | ~6.129 mã | Danh mục VTBB 4 khối: chai / nắp / xô / can / cốc (519), túi / nhãn (5.254), thùng / hộp (311), VTBB khác (45); cột gộp A-D 6.129 mã |
| Data đồng bộ NCC GC | DM | 1.679 | Bảng đối chiếu mã Dego - mã NCC; **chỉ có Hà Long** (VTBB 1.530, NL/BTP 70) |
| Data NCC GC | DM | 15 NCC + 147 dòng BTP | Chính sách TP từng NCC (lưu kho, phí, thời gian SX, % hao hụt theo nhóm vật tư, MOQ, cọc nhãn, cho dự trù VTBB...) + chính sách BTP theo NCC (mã BTP, dòng, màu, nhận dự trù, MOQ, thời gian phối) |
| Data QLDL | DM | 785 | Mã do QLDL khai báo: BTPR 213, PĐG 178, BTPCT 176, BTPM 124, PPT 46, Phí phạt 31, Chiết khấu 10, BTPNL 3; 578 đang dùng / 207 ngưng; 782 đã gửi khai báo |
| Data HH | DM (khung) | 0 | Chỉ tiêu đề (STT, mã HH, tên HH, tên pháp lý) |

### 1.3 [PL] Pháp Lý sản xuất.xlsx

| Sheet | Loại | Dòng thật | Nội dung |
|---|---|---|---|
| Mục Lục | TC | 6 | Mô tả 6 sheet; tiêu đề ghi nhầm *THỐNG KÊ HỢP ĐỒNG NCC GC* |
| DATA 1 | DM | ~35 | **Bản chép của [DRV] Admin** (thiếu 2 cột trạng thái sự cố) |
| 1. ĐỦ ĐK SX, BB | BM | 4 | Giấy đủ ĐK sản xuất / buôn bán từng NCC: loại, nhóm SP, dạng, hiệu lực, hết hạn, hiện trạng, số ngày sắp hết hạn. Mới có Thu Loan + DEGO |
| 2. SP | BM | 2 | Pháp lý SP tổng hợp từ 2.1 + 2.2 (mới 2 dòng mẫu ABASBA 50EC) |
| 2.1 TRINH ABA | DM | 369 | Pháp lý sản phẩm của công ty (do pháp lý ABA quản lý): 238 thuốc BVTV, 118 phân bón, 13 chế phẩm |
| 2.2 NCC GC SH | BM | 2 | Pháp lý SP do NCC GC sở hữu (QLDL cập nhật); mới 2 dòng mẫu |
| 3. SỰ CỐ | BM | 3 | Sự cố pháp lý (chưa có giấy / hết hạn / sai) gắn mã đơn, NCC, công ty, tên pháp lý; 3 dòng mẫu |
| 4. DUYỆT ĐƠN HÀNG | BM | 3 + 1 ví dụ | Bảng duyệt pháp lý từng đơn TP (62 cột): thông tin đơn + kiểm nguồn gốc, ĐK SX, ĐK mua bán, dòng hóa đơn, rủi ro chấp nhận |
| HỢP ĐỒNG (coppy QLDL) | DM | 4 + 5 hợp đồng | Theo dõi hợp đồng NCC GC (lưu tạm, QLDL quản lý): 2 khối tiêu đề khác nhau; 5 hợp đồng mẫu (An Nông x3, Hà Long x2) |

Tổng: **47 sheet đã đọc** (26 + 12 + 9).

---

## 2. Quy trình

Thứ tự theo Mục lục [QT]. QT13 là *QT DỪNG LÀM VIỆC NCC GC*. QT11, QT12 (sự cố) nằm trong tệp nhóm A nên ghi gọn để nối với pháp lý. Cột chung của mọi bảng quy trình gốc: STT, công việc, chi tiết, biểu mẫu, thời điểm, thời lượng (hầu hết để trống), hình thức (kênh Zalo / Drive), người thực hiện, phối hợp, kiểm tra, duyệt, ghi chú.

### QT1. Quy trình làm việc với NCC mới (sheet *1. QT LÀM VIỆC VỚI NCC MỚI*, trạng thái *Hoàn thành*)

**Mục đích**: đáp ứng nhu cầu KD khi phát sinh sản phẩm mới; mở rộng hệ thống đối tác khi NCC GC hiện tại không đáp ứng (năng lực, chất lượng, giá).
**Thời điểm**: NCC GC hiện tại không còn phù hợp cần thay thế; hoặc có sản phẩm mới NCC hiện tại không làm được.

| Bước | Ai làm (phối hợp / duyệt) | Làm gì | Biểu mẫu / kênh | Kết quả |
|---|---|---|---|---|
| 1 Tiếp nhận yêu cầu | QLSX (BPYC) | Nhận từ Ban lãnh đạo / bộ phận khác, xác định mục tiêu, nhận gợi ý NCC nếu có | Zalo *Nội bộ - Thảo luận sản xuất* | Ghi chú gốc: *chưa có thời gian tiếp nhận và phản hồi* |
| 2 Tìm NCC | QLSX (QLDL, Thu mua) | Dựa quan hệ sẵn có + nguồn công khai (web) theo danh mục sản phẩm cần sản xuất; chuyển QLDL tổng hợp | | Danh sách thô |
| 3 So sánh, đánh giá sơ bộ | QLDL (QLSX, Thu mua, Nhà máy, BGĐ) - duyệt QLSX | Lập danh sách NCC GC tiềm năng kèm lý do phù hợp, tham vấn bên liên quan | | Danh sách NCC tiềm năng |
| 4 Liên hệ, thu thập thông tin, thỏa thuận hình thức | QLSX (QLDL, NCC, TN ĐP, TN QLDL) | Làm việc với nhân sự phụ trách NCC; tạo nhóm Zalo riêng với NCC (TN ĐP + TN QLDL) | Zalo *Tên NCC - Dego hợp tác* | Hồ sơ thông tin NCC |
| 4.1 Check pháp lý | Pháp lý SX (NCC, QLDL) | Gửi checklist; kiểm Giấy CN đủ ĐK sản xuất thuốc BVTV (còn hiệu lực), Giấy CN đủ ĐK buôn bán thuốc BVTV, Giấy CN ĐKDN; hồ sơ hỗ trợ marketing (giấy ủy quyền quảng cáo); danh mục sản phẩm NCC được sản xuất / thương mại / sở hữu. **Không đạt thì ngưng hợp tác, tìm NCC khác** | CHECKLIST NCC GC MỚI.xlsx - Mẫu 01 | Kết luận đạt / không đạt |
| 4.2 Xác định danh mục dự kiến hợp tác | KD (QLSX, QLDL) - duyệt Giám đốc | KD lập danh mục sản phẩm hợp tác (sản phẩm / năm, nguyên nhân tìm NCC mới) gửi QLDL, QLDL gửi QLSX, QLSX trình Giám đốc. Không duyệt NCC: quay bước 2; không duyệt danh mục: điều chỉnh. QLDL báo ĐP NL/BTP làm tiếp test mẫu | Zalo QLDL nội bộ; Drive Checklist hợp tác | Danh mục được duyệt |
| 4.3 Kiểm pháp lý danh mục đã chốt | Pháp lý SX (NCC) | Lấy GĐK, bản công bố / thông báo hợp quy cho từng sản phẩm | | |
| 5 Lấy mẫu và kiểm tra mẫu | | Kiểm ruột phù hợp với VTBB và công nghệ sản xuất tại NCC | | |
| 5.1 Nhánh lấy mẫu theo danh mục của NCC | | 5.1.1 ĐP NL/BTP hỏi Lab lượng mẫu tối thiểu, lập đề nghị mua gửi QLDL, QLSX ký (*Phiếu yêu cầu đề nghị mua hàng hóa dịch vụ*) - 5.1.2 QLDL lấy / mua mẫu, thanh toán nếu mua (*Phiếu đề nghị thanh toán*), chuyển mẫu cho ĐP NL/BTP - 5.1.3 ĐP NL/BTP gửi Lab test, yêu cầu Lab lưu mẫu đối chứng - 5.1.4 Lab trả kết quả, ĐP NL/BTP lập báo cáo, QLDL trình QLSX, gửi NCC qua Zalo - 5.1.5 QLSX đàm phán lại: không đạt thì phối lại **tối đa 2 lần**, báo Giám đốc + BPYC; đạt thì ký hợp đồng - 5.1.6 Chốt công thức, ĐP NL/BTP xác định cấu thành, lập BĐM trình QLSX | Drive *Form_VTBB Khảo sát-Cọc nhãn-Mẫu.xlsx*; Zalo *Lab/SX - Tiếp nhận yêu cầu mẫu SP* | Công thức + BĐM BTP được duyệt |
| 5.2 Nhánh gửi công thức và mẫu cho NCC phối (danh mục của Dego) | ĐP NL/BTP | 5.2.1 Hỏi NCC số lượng mẫu tối thiểu - 5.2.2 Gửi Lab phối mẫu, Lab lưu mẫu đối chứng - 5.2.3 Gửi mẫu cho NCC, yêu cầu **NCC lưu mẫu đối chứng tối thiểu 2 năm** - 5.2.4 Theo dõi NCC phối; NCC thiếu nguyên liệu thì kiểm tồn kho (có: chuyển kho; không: lập đề nghị mua gửi Thu mua / QLDL) - 5.2.5 Nhận mẫu về, chuyển Lab - 5.2.6 Lab trả kết quả, báo cáo QLSX - 5.2.7 Đàm phán lại, tối đa 2 lần phối - 5.2.8 Chốt công thức, BĐM | như trên | |
| 6.1 Bảng giá NCC GC | QLDL (NCC, Giám đốc, Thu mua) - duyệt QLSX | 6.1.1 Nhận từ NCC: phí sang chai đóng gói, phí phối chế, giá BTP / VTBB / TP. 6.1.2 So sánh: phí sang chai - sản phẩm cũ so NCC đã hợp tác, mới so NCC có sản phẩm tương ứng; phí phối chế - sản phẩm mới trình Giám đốc; giá BTP / TP - sản phẩm mới so với giá NL + phí phối chế tham khảo + VTBB, trình QLSX. 6.1.3 Chốt, QLSX ký bảng giá; bảng giá đưa vào hợp đồng / phụ lục (tên pháp lý + quy cách + dòng sản phẩm + giá) | CHECKLIST NCC GC MỚI.xlsx - Mẫu 4 | Bảng giá đã ký |
| 6.2 Hợp đồng và phụ lục | QLDL - duyệt QLSX | 6.2.1 Lập checklist thông tin trong / ngoài hợp đồng (Mẫu 02) - 6.2.2 Thống nhất với NCC, QLSX duyệt - 6.2.3 Soạn Hợp đồng, Phụ lục, Bảng giá, Biên bản thỏa thuận khác - 6.2.4 Tham vấn lần lượt **Pháp lý, P TCKT, Giám đốc qua mail, tối đa 1 ngày mỗi bộ phận** - 6.2.5 QLSX ký nháy, Giám đốc ký, gửi NCC ký; trích thông tin gửi KD; **bản gốc bàn giao P TCKT, Sản xuất chỉ lưu bản scan** | CHECKLIST NCC GC MỚI.xlsx - Mẫu 02 | Hợp đồng hiệu lực |
| 7 Hoàn thiện quy trình NCC mới | QLDL (NCC, ĐP NL/BTP, ĐP TP) - duyệt QLSX | Tạo folder lưu trữ, nhóm làm việc; biên bản bàn giao nội bộ ký hai bên; triển khai cho Thu mua, KD, P TCKT, Pháp lý, nội bộ SX. **Phải xong trước đơn hàng đầu tiên** | CHECKLIST NCC GC MỚI.xlsx - Mẫu 05 | NCC sẵn sàng đặt đơn |

Biểu mẫu: Mẫu 01 danh mục sản phẩm hợp tác; Phiếu yêu cầu đề nghị mua hàng hóa dịch vụ; Phiếu đề nghị thanh toán; Mẫu 02 checklist hợp đồng / phụ lục; Mẫu 03 checklist quy trình làm việc. Nhóm Zalo: Nội bộ - Thảo luận sản xuất; *Tên NCC* - Dego hợp tác; QLDL - Thảo luận nội bộ; SX - Yêu cầu QLDL đặt NL, BTP; Lab/SX - Tiếp nhận yêu cầu mẫu SP.
Ghi chú gốc ở bước 4.1: checklist giấy phép ngành thuốc BVTV cần xác nhận áp cho mọi NCC hay chỉ nhóm BVTV.

### QT2. Quy trình khai báo dữ liệu sản xuất (sheet *2. QT KHAI BÁO SX*, trạng thái *Cần kiểm tra lại*)

**Mục tiêu**: đồng bộ hệ thống quản lý dữ liệu sản xuất; thống nhất cách đặt mã, tên; lưu trữ dễ tìm. **Thời điểm**: khi phát sinh dữ liệu / mã mới.

**Bước 1. Nhận / xác định thông tin khai báo** (ai khai báo loại mã nào):

| Loại mã | Ai khai báo (phối hợp) | Nguồn thông tin / khi nào |
|---|---|---|
| Nguyên liệu (nhập khẩu, kỹ thuật) | Thu mua, ĐP NL/BTP (Lab, QLDL) | Lab / ĐP NL/BTP báo khi có NL mới hoặc NL cũ đổi hàm lượng |
| BTP ruột (BTPR) | Thu mua (Lab, ĐP NL/BTP) | BTP mua từ NCC thu mua; BTPR = BTPNK + chi phí nhập khẩu, hoặc NLT + phí phối chế; khai khi mới / đổi dạng, dòng V, màu, hàm lượng |
| BTP mua (BTPM) | ĐP NL/BTP (QLDL) | BTP mua từ NCC GC (ruột); Giá vốn / QLDL báo; cần: tên pháp lý, thành phần, hàm lượng, ĐVT hàm lượng, dòng, dạng, màu. **Dự kiến bỏ năm 2027** |
| BTP nhập khẩu (BTPNK) | Thu mua (ĐP NL/BTP) | Ghi nhận công nợ NCC nước ngoài; chưa gồm VAT, phí dịch vụ, thuế khác |
| BTP cấu thành (BTPCT) | QLDL | Công nợ NCC GC trong nước gồm ruột + phần NCC không tách (thùng, chai, phí đóng gói); dùng cấu thành giá vốn TP; khai theo đơn hàng nếu chưa có mã |
| BTP từ R&D | Lab | BTP phân bón do Lab phối; dùng làm BĐM và LSX gửi NCC; mã theo quy tắc Lab |
| VTBB (chai, túi / gói, xô, can, lon, hộp, thùng, nhãn dán thùng, cốc, seal) | ĐP VTBB | Thu mua báo khi có VTBB mới hoặc đổi chất liệu, kích thước, màu, hình dạng; Drive *1. DATA DỮ LIỆU ĐẦU VÀO SX* |
| Chi phí nhập khẩu (CPNK) | Thu mua | Tổng chi phí một đơn nhập khẩu (VAT, phí dịch vụ, thuế khác), cấu thành giá vốn BTP / NL nhập khẩu |
| Phí gia công phối trộn (PPT) | QLDL (NCC GC) | NLT thành BTPR; khai theo mỗi lần NCC báo giá |
| Phí sang chai đóng gói (PĐG) | QLDL (NCC GC) | BTPR vào VTBB thành TP (HH); khai theo mỗi lần NCC báo giá |
| Hàng hóa (HH) | Thiết kế (Pháp lý chung, ĐP VTBB) | Khi có HH mới hoặc đổi BĐM, VTBB; cần: tên thương hiệu, khách hàng, nhãn hiệu, quy cách sản phẩm, quy cách thùng; Drive *QUẢN LÝ NHÃN MÁC IDA GROUP* |
| NCC GC | QLDL | Tên đơn vị, MST, địa chỉ, tên công ty trên Misa |
| NCC thu mua, đơn vị vận chuyển | Thu mua | như trên |
| Kho, công ty nội bộ | ĐP TP | như trên |

**Bước 2. Kiểm tra, trình duyệt, khai báo Misa, cập nhật Drive** (nhóm Zalo *SX&P TCKT - XUẤT NHẬP KHO NL & CÔNG NỢ NCC*):
- 2.1 Kiểm tra trùng: trùng thông tin mã cũ thì **không khai báo**, phản hồi. Phân vai: Thu mua kiểm + khai NCC thu mua, ĐVVC, NL, BTPR, BTPNK, CPNK; ĐP TP: kho, công ty nội bộ, khoản mục chi phí; QLDL: NCC GC, BTPCT, PPT, PĐG; ĐP NL/BTP: BTPM; ĐP VTBB: VTBB.
- 2.2 Trình duyệt: Thu mua trình QL thu mua (QLTM); QLDL, ĐP VTBB, ĐP TP, ĐP NL/BTP trình QLSX.
- 2.3 Gửi file *MẪU KHAI BÁO* vào nhóm Zalo sau khi duyệt (cho P TCKT).
- 2.4 P TCKT khai trên Misa, phản hồi; bộ phận cập nhật Drive Data sản xuất, báo nhóm nội bộ.
- 2.5 Lấy thông tin đã khai từ Misa về Drive *1. DATA DỮ LIỆU ĐẦU VÀO SX*, bổ sung chi tiết theo mẫu.

**Bước 3. Quy tắc mã / tên** (Mã | Tên nội bộ | Tên trên hóa đơn):
- NL nhập khẩu: `NLNK` + 4 số | "Nguyên liệu" + tên + hàm lượng + ĐVT | như tên nội bộ (bản gốc có lỗi gõ "7" ở đầu).
- NL kỹ thuật: `NLT` + 4 số | như trên.
- NL mã hóa: `NA` + 4 số | "Phụ gia" + mã NL (che tên thật, gắn với cấp bảo mật 4 *NL mã hóa*).
- BTPR: `BTPR` + 4 số | "BTPR" + loại + tên pháp lý + dòng V + dạng + màu + thành phần | tên pháp lý.
- BTPM: `BTPM` + 4 số | tương tự | tên pháp lý (dự kiến bỏ 2027).
- BTPNK: `BTPNK` + 4 số | tên pháp lý + hoạt chất + hàm lượng + ĐVT | như tên nội bộ.
- BTPCT: `BTPCT` + 4 số cuối mã HH | "BTPCT" + tên HH + NCC | tên pháp lý + quy cách SP + quy cách thùng + "(gia công)".
- BTP R&D: theo quy tắc Lab | mã BTP + tên pháp lý.
- VTBB: Túi / nhãn `N` + mã chất liệu (TG túi giấy, TN túi nhôm, HD nhãn decal, HG nhãn giấy) + 4 số cuối mã HH; Chai `C` + chất liệu + hình dạng + 4 số (tên nội bộ gồm cổ, size cổ, thể tích, trọng lượng g, màu, nhận diện riêng; tên hóa đơn "Chai" + chất liệu + thể tích); Nắp `NAP` + 4 số (chất liệu, cổ, size, trọng lượng, màu, logo, chữ logo, *Granty*); Cốc `COC`; Seal `SEAL` (không có tên hóa đơn); Hộp `HOP` + 4 số cuối mã HH / mã gợi ý (hộp riêng / hộp dùng chung); Xô `XO` + chữ đầu màu + 4 số; Can `CAN`; Lon `LON` (tên hóa đơn ghi "Hũ"); Thùng `TH` + viết tắt thương hiệu + 4 số (thùng dùng chung / thùng IDA, kích thước phủ bì D x R x C cm, độ dày giấy, màu; tên hóa đơn "Thùng carton" + số lớp); Nhãn dán thùng `NDT` + 4 số cuối mã HH.
- Chi phí: `CPNK` + 4 số; `PPT` + 4 số ("Phí gia công phối trộn" + NCC + thuốc / phân + tên pháp lý + dòng V + màu; nhóm *SX&KT - NB KHAI BÁO XNK NL, BTP, PHÍ GC MỚI*); `PĐG` + 4 số ("Phí sang chai đóng gói" + NCC + loại VTBB + quy cách theo bảng giá NCC).
- Hàng hóa: `HH` + 4 số | thương hiệu - mã đơn vị xuất hóa đơn - mã hàng - tên khách hàng - nhãn hiệu - quy cách SP - quy cách thùng. Thương hiệu: IDA GLOBAL / LOT IDA / GC (ABA) / AGC / BAMBOO / N2SBIOSBIO. **Mã đơn vị xuất hóa đơn**: I IDA Global; II Agricare; IV ABA; V Dego Holding; VI Bamboo; VII Nông nghiệp DEGO; VIII Dr Xanh; IX N2SBIOSbio (không có III). Tên hóa đơn: tên pháp lý - quy cách SP - quy cách thùng.
- NCC GC, NCC thu mua, ĐVVC: **mã = mã số thuế**, tên = tên trên Giấy CN ĐKKD.
- Kho: tên `KHO NCC_<viết tắt NCC>` và `KHO NCCXL_<viết tắt NCC>` (kho xử lý, không có địa điểm thực thì không khai địa chỉ); người liên hệ (tên, SĐT).
Mục V-VII (biểu mẫu, link, nhóm Zalo) để trống.

### QT2.1. Quy trình khai báo mã yêu cầu đặt hàng (sheet *2.1 QT KHAI BÁO MÃ YÊU CẦU ĐẶT*, chưa có trong Mục lục)

Khung bước 1-2 là **bản chép của QT2** (cột người thực hiện / phối hợp / nhóm Zalo còn nguyên của QT2, không khớp loại mã, ví dụ *LSX BTP* gán cho Thiết kế + Drive nhãn mác IDA). Mục 3 quy tắc ở thân bảng đều là một chuỗi giữ chỗ giống nhau; quy tắc thật nằm ở bảng phụ cuối sheet (ghi *check + QT*):

| Loại mã chứng từ | Quy tắc | Ví dụ |
|---|---|---|
| Đặt hàng TP | viết tắt thương hiệu + `TP` + ddmmyy + STT 2 số | ATP25112601 |
| Tiếp nhận sự cố | `SC.` + 6 số ngày + STT 2 số | SC.25112601 |
| Đặt hàng xử lý lại | thương hiệu + `YC` + ddmmyy + STT | AYC25112601 |
| Yêu cầu phối BTP | thương hiệu + `PBTP` + ddmmyy + STT | APBTP25112601 |
| Yêu cầu khảo sát VTBB, NL, BTP (KD gửi SX) | thương hiệu + `YCKS` + ... | AYCKS25112601 |
| Yêu cầu mua VTBB (KD gửi SX) | thương hiệu + `VTBB` + ... | AVTBB25112601 |
| Yêu cầu mua NL, BTP (KD gửi SX) | thương hiệu + `BTP` + ... | ABTP25112601 |
| Khảo sát VTBB phù hợp công nghệ NCC GC | thương hiệu + `YCKSCN` + ... | AYCKSCN25112601 |
| BĐM BTP | `BDMBTP_` + viết tắt tên pháp lý + `_` + mã màu 2 ký tự + `_` + dòng V + `_` + STT | BDMBTP_CT3.6_XL_V2_02 |
| BĐM VTBB | `BDMVT_` + mã HH + `_` + STT | BDMVT_HH4995_01 |
| BĐM TP | `BDMTP_` + mã HH + `_` + STT | BDMTP_HH4995_01 |
| LSX BTP | `LSX_` + mã yêu cầu phối BTP + `_` + STT | LSX_APBTP20052602_01 |
| LSX TP | `LSX_` + mã đơn đặt hàng + `_` + STT | LSX_ATP20052602_01 |
| Số chứng từ Misa | kế toán tạo, SX không tạo | |
Lưu ý: bảng ghi *dd/mm/yyyy* nhưng ví dụ dùng 6 số ddmmyy.

### QT3. Quy trình khảo sát và tính giá vốn sản xuất (sheet *3. QT KHẢO SÁT VÀ TÍNH GIÁ VỐN*, chủ trì Giá vốn)

**Mục tiêu**: kiểm soát giá vốn từ khảo sát, duyệt giá đến đối chiếu giá vốn thực tế; cảnh báo biên lợi nhuận kịp thời; tìm NCC GC có giá cạnh tranh.
**Thời điểm**: khi cần khảo sát / cập nhật giá; khi có đơn hàng; khi sản xuất xong, hàng về kho.
Lưu ý gốc: **Giá vốn tính cả GVSX (giá vốn sản xuất) và GVKD (giá vốn kinh doanh), giữ bảo mật giữa các bộ phận**.

**A. Tiếp nhận yêu cầu** (Giá vốn; phối hợp KD, Giám đốc; Form 1; Zalo / Drive): yêu cầu khảo sát / cập nhật giá thị trường từ KD / Giám đốc; yêu cầu duyệt giá từ đơn hàng; giá từ NCC GC (QLDL tiếp nhận) để check, đối chiếu.

**B. Xử lý và trả kết quả**
1. Khảo sát giá
   - 1.1 Kiểm tra pháp lý sản phẩm (Pháp lý SX; NCC, KD): danh mục, giấy chứng nhận, giấy phép KD. Drive *QLDL - THỐNG KÊ HỢP ĐỒNG*.
   - 1.2 Kiểm cấu thành để xác định đơn vị cung cấp NL / BTP / VTBB (Giá vốn, duyệt QLSX): NCC đã từng SX thì dựa lịch sử giao dịch + giá vốn đã lập; NCC có giao dịch nhưng chưa SX sản phẩm này thì lấy giá gia công toàn bộ hoặc giá khi Công ty tự cấp NL + VTBB; NCC mới thì theo QT1.
   - 1.3 Gửi bộ phận liên quan (Form 2): QLDL lấy giá NCC GC; ĐP VTBB lấy giá VTBB (qua Thu mua); ĐP NL/BTP lấy giá BTP (giá mua NL + phí phối NCC GC, qua Thu mua và QLDL); Thu mua lấy giá BTP từ NCC thu mua. Lưu ý: tên pháp lý trùng tên trên hóa đơn mua; ruột phù hợp VTBB; công nghệ NCC phù hợp VTBB.
   - 1.4 Lập bảng cấu thành giá, so sánh, trình QLSX (Form 3; Zalo *SX - GIÁ NL, BTP NCC GC*, *SX - KIỂM TRA GVKD*).
   - 1.5 Trả kết quả cho KD theo nhóm Zalo từng thương hiệu (Form 4), kèm lưu ý chiết khấu, công nợ, chi phí giao hàng, lưu kho; KD đồng ý hoặc đề xuất nguồn giá tốt hơn để thương lượng lại. Duyệt: KD / Giám đốc.
2. Check giá đơn hàng sản xuất
   - 2.1 Xác định cấu thành (Form 5; phối hợp ĐP TP): theo NCC, BTP, tên pháp lý, dòng V, màu; **chuyển mã BTP kinh doanh sang mã BTP sản xuất theo file quy đổi**; xác định chi phí đóng gói, bên chuẩn bị VTBB / NL / BTP; kiểm đơn đã có trong dự trù kế hoạch SX chưa.
   - 2.2 Tiếp nhận tồn kho: đủ tồn thì qua bước kế; **ngoài dự trù phải cộng thêm 3 ngày để khảo sát giá**. Đề xuất chuyển / mua / thay NCC có thể đổi giá; đề xuất thay thế thì đổi BĐM và có thể đổi giá. Duyệt: KD.
   - 2.3 Duyệt giá: **âm biên hoặc biên thấp hơn yêu cầu thì gửi KD xem lại giá bán; KD đồng ý thì đi đơn, không thì ngưng / hủy**. Chốt xong cập nhật Drive ĐP TP. Duyệt: KD / QLSX.
3. Check giá thành phẩm sau sản xuất
   - 3.1 Xác nhận giá trên đơn TP (QLDL / Thu mua; kiểm Giá vốn; duyệt QLSX): NCC báo tính tiền thì QLDL so giá ban đầu; lệch thì yêu cầu NCC điều chỉnh, NCC không chịu thì Giá vốn làm việc KD chốt giá rồi QLDL lấy hóa đơn. Phần cấu thành Dego mang qua: đổi BĐM / đổi giá cấu thành thì báo Giá vốn tính lại kèm nguyên nhân, trình QLSX rồi KD. Zalo *CÔNG NỢ/KẾ TOÁN + TÊN NCC GC*, *Giá Nhập Kho + NCC*.
   - 3.2 Lập hồ sơ giá vốn gửi P TCKT: nhận LSX từ QLDL, **tính giá vốn và gửi P TCKT trong ngày nhận LSX qua Signal *GROUP GIÁ VỐN KINH DOANH***; nhận hàng thực tế đổi BĐM thì tính lại, trình QLSX.

**C. Lưu trữ và báo cáo**: lưu GVSX, GVKD đã duyệt và giá thực tế vào Drive giá vốn làm căn cứ khảo sát sau; báo cáo KD định kỳ / theo yêu cầu về sản lượng, tiến độ, phí phạt, lãi quá hạn theo hợp đồng, yêu cầu KD giải trình nguyên nhân không đạt; QLSX thương lượng NCC nếu cần (Drive *5. GIÁ VỐN KINH DOANH NĂM 2024 - TRÌNH AD DUYỆT*).
Biểu mẫu Form 1-5 chỉ được gọi tên, mục V trống. Zalo: SX - CẬP NHẬT GIÁ VỐN ABA + AGC; SX - CẬP NHẬT GIÁ VỐN IDA GLOBAL; N2SBIOSBIO - GIÁ VỐN HÀNG HÓA; DR.XANH - GIÁ VỐN HÀNG HÓA; CÔNG NỢ/KẾ TOÁN + TÊN NCC GC; Giá Nhập Kho + NCC; SX - GIÁ NL, BTP NCC GIA CÔNG.

### QT4. Quy trình quản lý đơn hàng sản xuất gia công (sheet *4. QT QL ĐƠN HÀNG SX GC*, chủ trì ĐP TP)

**Mục tiêu**: đơn hàng đủ thông tin, đủ điều kiện trước khi gửi NCC GC; theo dõi tiến độ, báo kịp thời khi có sự cố; chứng từ đủ theo quy định.
**Phạm vi**: từ khi nhận đơn đặt hàng của KD đến khi có hàng tại NCC và đưa về kho thành phẩm.

**A. Điều phối đơn hàng sản xuất**

| Bước | Ai (phối hợp / duyệt) | Nội dung | Biểu mẫu / kênh | Mốc |
|---|---|---|---|---|
| 1 Tiếp nhận, xử lý dữ liệu | ĐP TP (KD) | KD nhập đơn vào Drive *Yêu cầu đặt hàng TP*, báo nhóm *Dự trù hàng hóa*; ĐP TP kiểm, xác nhận, thiếu thì yêu cầu KD bổ sung; chép vào Drive *SX-ĐIỀU PHỐI THÀNH PHẨM*: sheet *PYC* (tổng hợp đơn), *Pháp lý* (duyệt pháp lý), *Điều phối* (tiến độ). Đơn NCC Thu Loan cập nhật thêm Drive *Đơn đặt hàng Thu Loan* | Zalo *Tên thương hiệu - Dự trù hàng hóa* | **Chậm nhất 3 ngày sau khi nhận đơn phải cập nhật tiến độ; chậm phải nêu nguyên nhân + phương án** |
| 2.1 Pháp lý | NSPL (BP XLSC, Pháp lý chung) | Theo QT5 duyệt pháp lý; xác nhận trên sheet *Điều phối* | Drive Điều phối thành phẩm | Khi nhận đơn từ ĐP TP |
| 2.2 BĐM BTP và dòng công thức | ĐP NL/BTP (KD, NCC) | Kiểm dòng công thức KD đặt, đối chiếu nguyên tắc ở Drive *Xuất nhập tồn NL, BTP*; kiểm BĐM theo QT8; thiếu thì hỏi KD; sản phẩm mới KD làm trực tiếp với QLSX; xác nhận trên sheet Điều phối | | |
| 2.3 BĐM VTBB | ĐP VTBB (KD, NCC) | Cập nhật mockup gần nhất, cấu thành VTBB (nội bộ + gửi NCC); kiểm khả năng đóng nhãn / sản phẩm của các NCC, đề xuất đổi NCC nếu tối ưu giá; theo QT9 | Zalo *SX - Quản lý điều phối* | |
| 2.4 Duyệt giá TP tạm | Giá vốn (ĐP NL/BTP, ĐP VTBB, QLDL) - duyệt QLSX | Chép mã công thức vào sheet Điều phối; theo QT3 mục 2 | Zalo giá vốn theo thương hiệu | Khi có BĐM BTP, BĐM VTBB, phí NCC |
| 2.5 Kiểm tồn, chuyển / mua | ĐP VTBB, ĐP NL/BTP (Thu mua) | Theo cấu thành đã duyệt kiểm tồn, chuyển kho / mua bổ sung theo QT8, QT9; cập nhật Drive. **Lấy mẫu TP 2 đơn vị tính nhỏ nhất mỗi đơn** | | |
| 2.6 BĐM TP (nội bộ và thuế) | QLDL - duyệt QLSX | Theo QT6 và QT7 | | Trước khi gửi đơn NCC |
| 2.7 Duyệt giá đơn hàng | Giá vốn (ĐP TP, QLDL) - duyệt QLSX | Nhập mã đơn vào BĐM TP; lập **Phiếu duyệt giá 3 mức: giá vốn nội bộ, giá vốn tính thuế, giá KD bán**, QLSX ký; QLDL giữ bản gốc để đối chiếu công nợ; cập nhật *Đã duyệt giá* trên Drive | Phiếu duyệt giá (form mới có giá) | |
| 3.1 Gửi đơn NCC | ĐP TP (NCC) - duyệt QLSX | **Yamato, Thu Loan bắt buộc đủ VTBB, NL mới được gửi đơn**; dán mã đơn vào sheet *GỬI ĐƠN NCC*; gửi nhóm *TÊN NCC - ĐẶT HÀNG SẢN XUẤT* mockup + yêu cầu (Yamato gửi PDF theo mẫu NCC, NCC khác chụp màn hình). **Lần đầu giao dịch với NCC phải QLSX duyệt thông tin đặt hàng**. Đơn gồm mẫu TP 2 đơn vị nhỏ nhất | Đơn đặt hàng; *Mẫu gửi đơn NCC.jpg*; PDF đặt hàng Yamato | Khi QLSX duyệt đơn |
| 3.2 Cập nhật tiến độ | ĐP TP (NCC, KD, BP Kho) | **Sau 2 ngày làm việc từ ngày gửi đơn kiểm tiến độ**; chưa phản hồi / trễ thì tìm nguyên nhân, giải pháp; xác nhận phương án tối ưu với BPYC. **Báo cáo trước 16h30 hằng ngày**: hàng sẵn kho, hàng chờ nhận hóa đơn, hàng đã có lịch SX | Mẫu tiến độ ngày; Zalo *TÊN NCC - TIẾN ĐỘ SẢN XUẤT*, *SX&KHO - LỊCH GIAO NHẬN HÀNG TP* | Hằng ngày |
| 4.1 Nhận thông tin có hàng, đề nghị nhập kho | ĐP TP (NCC, QLDL, KD, BP XLSC) - duyệt QLSX | Nhập số lượng thực tế lên Drive (Yamato, Hà Long báo số cụ thể; NCC khác chỉ báo có hàng trên Zalo). Hà Long có tin nhắn tự động báo có hàng + công nợ, có app theo dõi tiến độ. Đúng số lượng: trạng thái *Chưa lấy hóa đơn*, lập đề nghị nhập kho TP gửi QLDL. Khác số lượng: hỏi KD; thiếu thì yêu cầu làm đủ hoặc hủy phần còn lại; dư thì nhận hoặc NCC xử lý (báo XLSC); XLSC lập phương án hướng dẫn QLDL lấy hóa đơn | Phiếu đề nghị nhập kho TP | Theo lịch SX NCC |
| 4.2 Nhận hóa đơn | QLDL - kiểm P TCKT | Theo QT6 | | |
| 5 Theo dõi nhận hàng | ĐP TP, BP Kho (NCC, QLDL) | Kho gửi danh sách hàng cần nhận + tài xế + biển số + giờ nhận lên nhóm *SX&KHO - LỊCH GIAO NHẬN HÀNG TP*; ĐP TP lập *Danh sách hàng hóa nhận* từng NCC; hàng về Kho kiểm số thùng + ngoại dạng, ký phiếu đề nghị xuất kho của NCC; chụp phiếu gửi nhóm *CHỨNG TỪ XUẤT NHẬP KHO NCC*; ĐP TP chuyển trạng thái *Đã nhận hàng* khi đủ số lượng; sai lệch thì Kho + ĐP TP đối chiếu | danh sách nhận hàng.jpg | Liên tục |
| 6 Kiểm tra mẫu (Lab) | ĐP TP, KD, BP Kho - duyệt QLSX | Lập đề nghị xuất kho mẫu, QLSX duyệt; KD xuất trên Misa (nhóm *Misa xuất mẫu + Tên TH*); gửi Kho; thuê vận chuyển gửi mẫu cho R&D; **R&D trả kết quả chậm nhất 2 ngày**; không đạt thì sang QT sự cố, trạng thái *TEST KHÔNG ĐẠT*; đạt thì hoàn thành đơn. Phân loại: BTP Dego mang sang thì chuyển kho + xuất kiểm mẫu (chi phí); BTP / TP NCC cho thì nhập Drive theo dõi, tự xuất; BTP / TP NCC bán thì mua + nhập kho + xuất (chi phí). **Thời gian test: ngoại dạng 1-2 ngày, hàm lượng 14 ngày** | Giấy đề nghị xuất vật tư.jpg | Khi hàng về kho |
| 7 Chứng từ cấu thành, đối chiếu, thanh toán | QLDL (P TCKT) - duyệt QLSX | Theo QT6 | | Sau khi NCC báo có hàng; định kỳ tháng |

**B. Hủy đơn đặt hàng NCC GC**
1. Tiếp nhận yêu cầu hủy (ĐP TP; KD, Lab) qua Zalo, trình duyệt. **Chuyển sang QT sự cố khi NCC báo VTBB / NL / BTP lỗi không dùng được, hoặc vướng pháp lý / không đủ điều kiện tiếp tục**.
2. Xác định trạng thái đơn:
   - 2.1 **Chưa gửi đơn NCC**: báo nội bộ dừng; VTBB xem ngưng mua / điều chuyển, xử lý hóa đơn, cập nhật tồn, ghi chi phí cho bộ phận yêu cầu hủy; NL/BTP kiểm đã phối BTP chưa để dừng kịp, xử lý hóa đơn, tồn, giá vốn, chi phí; kiểm hiện trạng BĐM + LSX; ĐP TP tổng hợp trình duyệt; sau duyệt đặt trạng thái hủy, chuyển dữ liệu sang sheet *Hoàn thành*, phản hồi bộ phận yêu cầu.
   - 2.2 **Đã gửi đơn NCC**: ĐP TP tổng hợp hiện trạng, trình duyệt, liên hệ NCC dừng đơn. 2.2.1 NCC chấp nhận: làm như 2.1. 2.2.2 NCC không chấp nhận: trình duyệt, báo KD, cập nhật số lượng thực SX, trạng thái *Chờ thông tin từ KD*; KD nhận hàng thì đi tiếp từ bước 4; KD không nhận thì sang QT sự cố.
3. Thanh toán, lưu trữ theo quy định (ĐP VTBB, ĐP NL, QLDL, ĐP TP; P TCKT; duyệt QLSX).

**Trạng thái đơn xuất hiện trong quy trình**: Đã duyệt giá, Chưa lấy hóa đơn, Đã nhận hàng, TEST KHÔNG ĐẠT, Hoàn thành, Hủy, Chờ thông tin từ KD.
Biểu mẫu: Đơn đặt hàng / Mẫu gửi đơn NCC; Phiếu đề nghị nhập kho; Phiếu đề nghị xuất kho (NCC); Phiếu duyệt giá; BĐM BTP (nội bộ và thuế); BĐM TP (nội bộ và thuế); Danh sách nhận hàng; Giấy đề nghị xuất vật tư (mẫu test); Mẫu báo cáo tiến độ ngày. Drive: SX-ĐIỀU PHỐI THÀNH PHẨM; *Tên thương hiệu* - YÊU CẦU ĐẶT HÀNG TP; ĐIỀU PHỐI THÀNH PHẨM; Đơn đặt hàng Thu Loan; Xuất nhập tồn NL, BTP; BDM TP (QLDL); Phiếu duyệt giá; Theo dõi sự cố. 20 nhóm Zalo (Dự trù hàng hóa, Quản lý điều phối, giá vốn theo thương hiệu, Đặt hàng SX / Tiến độ SX theo NCC, Lịch giao nhận TP, Chứng từ XNK NCC, Misa xuất mẫu, SX và Kho xuất hàng, Vận chuyển Grab, Lab trả kết quả mẫu, Xử lý sự cố hằng ngày...).

### QT5. Quy trình pháp lý sản xuất / duyệt pháp lý đơn hàng (sheet *5. QT PHÁP LÝ SẢN XUẤT*, chủ trì Pháp lý SX, thương hiệu Dego Holding)

**Mục tiêu**: đơn hàng đủ điều kiện pháp lý để sản xuất, mua bán. **Thời điểm**: khi ĐP TP cập nhật đơn đặt hàng.
Câu hỏi để ngỏ ngay đầu sheet: quy trình hiện chỉ duyệt pháp lý **đơn hàng TP**; còn đơn BTP, đơn xử lý lại, sự cố, mua / khảo sát NL / BTP thì sao?

**I. Pháp lý đơn hàng**
1. Tiếp nhận đơn (Pháp lý SX; ĐP TP): sau khi ĐP TP nhận đơn từ KD, cập nhật đủ Drive; kiểm hình mockup.
2. Kiểm pháp lý cho đơn:
   - 2.1 Đơn cần tạm ngưng do sự cố trước đó (phối hợp Sự cố): xác định VTBB / NL / BTP cấu thành mã hàng liên quan để cảnh báo sớm vật tư có nguy cơ lỗi.
   - 2.2 Nguồn gốc sản phẩm (phối hợp Pháp lý chung): (1) **đơn vị sở hữu** - tên trên Giấy đăng ký thuốc / Giấy CN đăng ký hoặc QĐ công nhận lưu hành phân bón còn hiệu lực; (2) **đơn vị cấu thành** - là đơn vị sở hữu hoặc được ủy quyền; khác đơn vị sở hữu thì phải có giấy ủy quyền / thỏa thuận hợp pháp; (3) GĐK thuốc / QĐ lưu hành còn hiệu lực; (4) Thông báo tiếp nhận hồ sơ công bố hợp quy còn hiệu lực; tên đơn vị trên hồ sơ phải là đơn vị sở hữu, cấu thành, hoặc sản xuất / gia công.
   - 2.3 Điều kiện sản xuất (phối hợp NCC GC): tên + địa chỉ cơ sở SX / gia công trên nhãn khớp hồ sơ; đơn vị cấu thành khác đơn vị SX thì phải có Hợp đồng gia công; Giấy CN đủ ĐK sản xuất phân bón / thuốc BVTV còn hiệu lực và **phạm vi được phép SX khớp sản phẩm**; nếu có mua bán thì Giấy CN đủ ĐK mua bán còn hiệu lực.
   - 2.4 Điều kiện mua bán: đơn vị mua bán mua từ đơn vị cấu thành / sản xuất / đơn vị bán; quan hệ phải có Hợp đồng / Phụ lục mua bán; tên + địa chỉ đơn vị chịu trách nhiệm trên nhãn khớp hồ sơ; Giấy CN đủ ĐK mua bán còn hiệu lực, đúng phạm vi.
   - 2.5 **Dòng hóa đơn**: từ đơn vị sở hữu / cấu thành, đơn vị SX / gia công, đơn vị mua / bán xác định dòng hóa đơn phù hợp (căn cứ cho QT6 bước A5 bán nội bộ).
3. Cập nhật kết quả vào Drive quản lý pháp lý đơn hàng, chia sẻ bộ phận liên quan (thực tế là sheet *Pháp lý* / *Điều phối* trong Drive SX-ĐIỀU PHỐI THÀNH PHẨM và sheet *4. DUYỆT ĐƠN HÀNG* của tệp Pháp lý sản xuất).

**II. Pháp lý sản xuất (hồ sơ nền)**
1. Nhận thông tin pháp lý sản phẩm / NCC GC từ QLDL khi có mới / bổ sung / gia hạn.
2. Rà trùng với dữ liệu cũ, nhập Drive pháp lý.
3. Định kỳ kiểm thời hạn: hợp quy, ủy quyền, thuê tên...; báo bộ phận liên quan bổ sung / gia hạn; có phản hồi thì quay lại bước II.1 (phối hợp QLDL, Pháp lý chung).
4. Lưu trữ, báo cáo theo quy định / yêu cầu.
Mục biểu mẫu, Zalo để trống; link: SX-ĐIỀU PHỐI THÀNH PHẨM.

### QT6. Quy trình quản lý NCC gia công (sheet *6. QT QUẢN LÝ NCC GC*, chủ trì QLDL)

**Mục đích**: chứng từ đơn hàng sản xuất đúng, đủ, kịp thời; quản lý hồ sơ, số liệu, chi phí với NCC GC đang giao dịch; phối hợp thông suốt.
**Thời điểm**: theo đơn đặt hàng từng NCC GC; định kỳ / phát sinh.

**A. Xử lý đơn hàng**

| Bước | Ai (phối hợp / duyệt) | Nội dung | Biểu mẫu / kênh | Mốc / quy định |
|---|---|---|---|---|
| A1 Tiếp nhận | QLDL (ĐP TP) | Nhận đơn đặt hàng từ Điều phối, dữ liệu tự cập nhật vào Drive; kiểm **mã số chính sách giá** của NCC cho đơn | Drive 01 | Khi đơn đã được *duyệt giá tạm* |
| A2 Lập BĐM TP | QLDL (P TCKT) - duyệt QLSX | Nhận BĐM VTBB + mã BTP, lập BĐM TP ra **mã BĐM TP**, trình QLSX, gửi P TCKT | Mẫu BĐM TP; Drive 01 | Trước khi gửi đơn NCC; ghi chú: P TCKT đồng bộ mã BĐM TP |
| A3 Nhận hóa đơn NCC | QLDL (ĐP TP, NCC) - kiểm P TCKT | ĐP TP gửi bản gốc đề nghị nhập kho TP, QLDL liên hệ NCC lấy hóa đơn | | **Ngày hóa đơn NCC phải trùng hoặc sau ngày lập LSX** |
| A4 LSX, phiếu nhập / xuất kho, hoa hồng | QLDL (P TCKT, ĐP VTBB, ĐP NL/BTP) | Nhận số lượng hàng sẵn kho tại NCC từ ĐP TP; nhận đề nghị xuất kho NL/BTP, VTBB có chữ ký; lập và ký LSX, đề nghị nhập kho công nợ NCC; lập phiếu tổng: LSX TP, Đề nghị nhập kho (mua mới từ NCC GC), Đề nghị xuất kho TP theo LSX, Đề nghị chuyển kho; gửi P TCKT. Cập nhật Drive hoa hồng, gửi danh sách giá trị cần chi từng đơn cho P TCKT hạch toán. Số lượng thực nhận lệch thông báo: Kho liên hệ các bộ phận xác nhận | Lệnh SX; Đề nghị nhập / xuất / chuyển kho; Zalo *CHỨNG TỪ XUẤT NHẬP KHO NCC*; Drive *BDM + Tên NCC* | **Phiếu đề nghị xuất kho NL/BTP, VTBB phải lập trước hoặc cùng ngày LSX** |
| A5 Bán TP giữa công ty nội bộ | QLDL (P TCKT, Pháp lý ABA) | Theo pháp lý duyệt xác định công ty bán / mua: trùng công ty bán cho khách thì không xử lý; khác thì lập phiếu đề nghị xuất bán + phụ lục bán hàng, trình duyệt; P TCKT lập hóa đơn nháp. Pháp lý (Ms Trinh) làm hợp đồng mua bán | Phiếu đề nghị xuất bán (Thuế) | **Chậm nhất ngày 5 hằng tháng gửi phụ lục tháng trước cho kế toán** |
| A6 Đối chiếu tồn kho, phí lưu kho | QLDL (P TCKT, NCC, ĐP VTBB, ĐP NL/BTP, ĐP TP, XLSC) - duyệt QLSX | Nhận danh sách tồn + phí lưu kho hằng tháng; phân bổ phí cho NL/BTP, VTBB, TP sau sản xuất, hàng lỗi tại NCC; gửi kết quả NCC; sai lệch thì giải trình | Biên bản đối chiếu tồn kho (nội bộ) | Hằng tháng |
| A7 Đối chiếu công nợ (nội bộ và thuế) | QLDL (P TCKT, NCC) - duyệt QLSX | So Drive theo dõi với Misa, điều chỉnh, đối chiếu NCC, lập biên bản | Biên bản đối chiếu công nợ | **Trước ngày 20 tháng kế tiếp** |
| A8 Thanh toán NCC GC | QLDL (P TCKT, NCC) - duyệt QLSX | UNC: đủ bộ Đề nghị thanh toán, Đề nghị thanh toán của NCC, Hóa đơn, Hợp đồng, Biên bản đối chiếu; nhận khoản cấn trừ từ XLSC; P TCKT chi, chụp UNC lên nhóm, QLDL chuyển NCC. Tiền mặt: thỏa thuận kế toán, gửi hồ sơ, xác nhận NCC. Cập nhật file tiến độ thanh toán cho KD | Giấy đề nghị tạm ứng; Giấy thanh toán | **Trước hạn thanh toán 7 ngày** |

**B. Mua NL/BTP, VTBB từ NCC GC**
- B1 Mua NL/BTP: nhận yêu cầu (kèm nơi mua, nơi nhận) từ ĐP NL/BTP; QLDL bổ sung hợp đồng, phiếu kiểm soát chất độc; nhập Drive QLDL; báo ngày có hàng + số lượng thực mua; ĐP NL/BTP lập đề nghị nhập kho; QLDL lấy hóa đơn; gửi test mẫu cho Lab (trừ khi mua BTP và đóng gói cùng một NCC không có phụ gia Dego mang qua thì chỉ test thành phẩm); chuyển kho nếu cần; đối chiếu + thanh toán như A7, A8. Chứng từ: Hợp đồng, Phiếu kiểm soát chất độc, Hóa đơn, COA (hàng nhập khẩu) / phiếu kiểm tra chất lượng (hàng trong nước). Kiểm: ĐP NL/BTP; duyệt QLSX.
- B2 Mua VTBB: tương tự, theo yêu cầu ĐP VTBB; chứng từ Hợp đồng / Phụ lục / Phụ kiện.

**C. Quản lý dữ liệu NCC GC**
- C1 Hồ sơ pháp lý NCC: scan bản gốc Giấy CN ĐKKD, Giấy đủ ĐKSX, Giấy đủ ĐKBB thuốc / phân bón; pháp lý sản phẩm (Giấy CN ĐKSP / QĐ công nhận lưu hành, hợp quy, ủy quyền / hợp đồng / chứng nhận sở hữu). Gửi Pháp lý chung lưu (chia sẻ Pháp lý SX). Pháp lý chung theo dõi sắp hết hạn, báo QLDL; **QLDL liên hệ NCC bổ sung trước 3 tháng hết hạn; sản phẩm do công ty sở hữu tên thì trước 6 tháng**. Thiếu hồ sơ phải trình QLSX. Biểu mẫu *Form Pháp lý - Chi phí*. Thời điểm: trước khi ký hợp đồng / khi có sản phẩm mới.
- C2 Hợp đồng / gia hạn / bổ sung: theo bước 6 QT1 (lược bước trùng). **QLDL báo QLSX hợp đồng sắp hết hạn trước 3 tháng; QLSX trả checklist cho QLDL trước ít nhất 1 tháng hết hạn**. Drive *QLDL - THỐNG KÊ HỢP ĐỒNG*.
- C3 Lãi quá hạn, sản lượng, phí phạt, chiết khấu: đối chiếu hằng tháng lãi quá hạn, phí lưu kho, sản lượng, chiết khấu; còn lại đối chiếu khi kết thúc hợp đồng, gửi Giá vốn. Phí phạt gửi Giá vốn tính giá; phí phối trộn gửi ĐP NL/BTP tính giá vốn SX BTP. Phân bổ phí lưu kho theo nhóm (NL/BTP, VTBB, TP, hàng lỗi). Lãi quá hạn phân bổ theo doanh số. Lập hồ sơ thanh toán trình QLSX gửi P TCKT.
- C4 Hoa hồng: tổng hợp hoa hồng cả năm để kế toán đối chiếu, **chi vào tháng đầu năm kế tiếp**; hồ sơ: hợp đồng chi hoa hồng + chứng từ chi cá nhân (kế toán lập); cá nhân được chỉ định giao tiền mặt cho NCC.
- C5 Dự chi: (5.1) hằng tháng thống kê công nợ cần chi lấy từ Misa, nhập Drive Dự chi **ngày 25-28 tháng trước**; khoản tháng trước chưa chi cộng dồn, giữ ngày cần chi thực tế. (5.2) Dự chi mua hàng trả ngay theo kế hoạch kinh doanh từ Giá vốn, QLSX duyệt, QLSX trao đổi Trưởng P TCKT. *Form Dự chi*.

Biểu mẫu: Phiếu BĐM; Phiếu nhập kho; Phiếu đề nghị xuất kho; Form Pháp lý - Chi phí; Checklist NCC GC mới; Form Dự chi. Drive: *DRIVE CẬP NHẬT THÔNG TIN GIÁ VỐN TỪ ĐIỀU PHỐI*; *BDM + TÊN NCC*. Zalo: IDA CÔNG NỢ HÀ LONG; YAMATO - Công ty ABA - CÔNG NỢ HÓA ĐƠN; GIÁ NHẬP KHO HÀ LONG/YAMATO; CHỨNG TỪ XUẤT NHẬP KHO NCC.

### QT7. Quy trình thực hiện bảng định mức thuế (sheet *7. QT BĐM THUẾ*)

**Mục tiêu**: cấu thành **trên 1.000 lít / gram cho BĐM BTP** và **trên 1 đơn vị sản phẩm cho BĐM VTBB, BĐM TP** (không gồm giá), định mức sử dụng trước khi lập LSX; kiểm soát tồn, thực tế sử dụng và hao phí.
**Thời điểm**: trước khi đưa vào SX; xác định trước để khảo sát, tính giá vốn.

| Khối | Ai | Bước |
|---|---|---|
| A. BĐM BTP | ĐP NL/BTP (Giá vốn, ĐP TP, Pháp lý SX, Lab / NCC GC) | 1 Nhận yêu cầu / đơn từ ĐP TP. 2 Xác định luồng pháp lý (đơn vị cấu thành, đơn vị chuẩn bị từng hạng mục) và cấu thành theo công thức: loại NL, ĐVT, lượng trên 1.000 ml / gram, **hàm lượng (thuốc), tỷ trọng (phân)**, phí phối trộn. 3 Kiểm tồn đủ cho đơn. 4.1 Tra BĐM cũ theo tên pháp lý, có rồi thì không làm; **chỉ làm mới khi khác dạng BTP (lỏng / rắn), đổi hàm lượng NL (thuốc), đổi tỷ trọng (phân)**. 4.2 Lập theo *Mẫu BĐM BTP* |
| B. BĐM VTBB | ĐP VTBB (Pháp lý SX, Lab / NCC GC) | 1 Nhận yêu cầu. 2 Luồng pháp lý + hạng mục: phí sang chai, đóng gói, chai / xô / can / túi / gói, nắp, nhãn, nhãn dán thùng, cốc đong, seal, tem, thùng (mã, tên, ĐVT, lượng trên 1 đơn vị SP), đơn vị SX / gia công. 3 Kiểm tồn. 4.1 Tra BĐM cũ; làm mới khi khác quy cách SP hoặc đổi chất liệu VTBB. 4.2 Lập theo mockup của Thiết kế, *Mẫu BĐM VTBB*; chú ý **tên VTBB trên hóa đơn** và **các VTBB không lấy được hóa đơn** |
| C. BĐM TP | QLDL (Pháp lý SX) | 1 Nhận yêu cầu. 2 Luồng pháp lý + hạng mục: mã BTP, loại, ĐVT, lượng VTBB, phí sang chai đóng gói. 3 Nhận mã BĐM BTP (ĐP NL/BTP) + BĐM VTBB (ĐP VTBB), đối chiếu luồng pháp lý. 4.1 Tra BĐM cũ theo tên pháp lý + quy cách. 4.2 Lập theo *Mẫu BĐM TP*, phân biệt chai / túi gói / xô can và *chuẩn bị toàn bộ* với *chuẩn bị một phần* |
| D. Trình duyệt, lưu | QLDL (P TCKT) - duyệt QLSX | In BĐM trình QLSX ký; BĐM BTP + VTBB gửi QLDL tổng hợp làm BĐM TP; **QLDL gửi bản gốc cho P TCKT**, gửi file BĐM BTP + TP qua Zalo cho P TCKT; QLDL lưu scan |

Drive: *1. BDM mua hàng THUẾ - Công ty IDA / ABA / DEGO* (mỗi công ty nội bộ một bộ BĐM thuế); *PHÁP LÝ SẢN PHẨM (CHUNG)* (kiểm hàm lượng NL thuốc BVTV); *PHÁP LÝ CẦN LÀM BĐM THUẾ PHÂN BÓN (sử dụng)*. Zalo: XỬ LÝ CV P TCKT THUẾ - IDA GLOBAL / DEGO (ĐẤT VIỆT) / ABA.

### QT8. Quy trình quản lý nguyên liệu / bán thành phẩm (sheet *8. QT QL NLBTP*, chủ trì ĐP NL/BTP)

**Mục tiêu**: quản lý toàn bộ điều phối NL, BTP từ tiếp nhận đơn đến nhập - xuất kho và đối chiếu tồn; đủ hàng đúng tiến độ; kiểm soát tồn, hao hụt, chi phí; đồng bộ chứng từ giữa SX, KD, Kho, P TCKT, NCC GC.
**Thời điểm**: khi có đơn mới, tồn thiếu, cần điều chuyển; **định kỳ hằng tháng (dự trù ngày 15)**; khi nhập / xuất, mua, xử lý hao hụt / hư hỏng, đối chiếu với NCC. Ghi chú nháp đầu sheet: *bổ sung test sản phẩm xem rớt hàm lượng*.

**A. Tiếp nhận và xác định BĐM**
1. Nhận đơn ngay khi ĐP TP cập nhật sheet *Điều phối*; nhận yêu cầu phối BTP.
2. Kiểm / làm BĐM (chỉ khi công ty nội bộ cấu thành hoặc chuẩn bị một phần; **mua TP trọn gói từ NCC GC thì bỏ bước này**). BĐM bắt buộc theo thực tế: thay NL/BTP trong SX thì lập BĐM mới gửi QLDL.
   - 2.1 BĐM nội bộ nhóm **Phân bón**: SX tại **Nhà máy NTV** thì theo dòng công thức KD + dữ liệu Lab, lập **Lệnh sản xuất** theo số lượng đơn; SX tại NCC GC khác thì đối chiếu mã HH với *DSQL BTP* (danh sách quản lý BTP) để ra dòng công thức + BĐM BTP; chưa có thì hỏi KD mã, Lab xác định công thức, khai mã BTP, làm BĐM; nhập mã BTP vào Drive Điều phối, cập nhật DSQL BTP. Biểu mẫu: DSQL BTP Phân bón; Phiếu đề nghị xuất kho NL. Duyệt QLSX.
   - 2.2 BĐM nội bộ nhóm **Thuốc BVTV**: đối chiếu DSQL BTP; chưa có / đổi dòng V, màu, hàm lượng NL thì làm BĐM mới: Lab thống nhất công thức; QLSX làm với NCC phối mẫu, test; mẫu đạt + NCC thống nhất BĐM thì chốt dòng công thức / tên pháp lý, lượng NL công ty mang qua; báo QLDL lấy giá; lưu DSQL BTP. Ghi chú gốc: **đang dùng tạm form khảo sát VTBB, nên có form khảo sát NL/BTP riêng**.
   - 2.3 BĐM cấu thành **thuế**: đối chiếu tên pháp lý + công ty cấu thành với Danh sách quản lý BĐM BTP thuế; chưa có thì làm theo QT7. **NCC cấu thành: không khai mã, BĐM do NCC lo**; công ty cấu thành / chuẩn bị một phần: làm BĐM BTP thuế. Biểu mẫu: Phiếu đề nghị xuất hóa đơn; Zalo *Cung ứng - Hóa đơn nội bộ*.

**B. Kiểm tồn và lên phương án** (ngay khi xác định BĐM; duyệt QLSX)
- Đủ tồn NL: đề xuất phối BTP. Đủ tồn BTP: duyệt đơn, chuyển trạng thái sản xuất trên Drive, báo ĐP TP.
- Tồn ở kho khác: báo KD chọn điều chuyển NL/BTP hoặc đổi NCC GC có sẵn hàng (**KD hủy đơn và tạo đơn mới**); báo ĐP TP.
- Không tồn: thiếu NL thì mua NL để phối; thiếu BTP thì mua hoặc phối.

**C. Dự trù NL/BTP** (định kỳ ngày 15; hoặc KD thấy tồn không đủ; hoặc kiểm tồn theo đơn thấy thiếu)
1. Cập nhật cho KD: tồn kho, **MOQ** theo dòng công thức / sản phẩm, chi phí lưu kho NCC; danh sách NCC được dự trù trước / mua BTP trước; nhắc KD **bắt buộc kiểm tồn trước khi dự trù**, mua BTP gắn mã HH dự kiến + sản lượng. Drive *Tên thương hiệu - Yêu cầu đặt hàng TP*.
2. KD xác nhận tài chính với P TCKT, gửi *Phiếu đề nghị mua hàng hóa dịch vụ (nội bộ)*; **ĐP NL/BTP phản hồi kết quả dự trù chậm nhất 5 ngày**. Ghi chú chưa chốt: Drive *Dự trù KD cập nhật giá* dùng riêng hay gộp với *Yêu cầu đặt hàng TP*.
3. Kiểm tên pháp lý, BĐM, đơn vị cấu thành, MOQ; phân loại đơn vị cung cấp (công ty hay một / nhiều NCC) theo pháp lý; lập danh sách sản phẩm theo công ty / NCC cấu thành và danh sách theo pháp lý + công ty nhận hóa đơn (Pháp lý phụ trách). **Cả công ty và NCC cùng sở hữu tên pháp lý thì lập ở cả hai mục (cần mua / cần đặt NCC GC) để so giá**. Ghi chú: chưa có phân công rõ ai chuẩn bị NL/BTP cho từng sản phẩm / NCC.
4. Lập *Phiếu đề nghị mua hàng hóa dịch vụ* / *Phiếu yêu cầu phối BTP* kèm phiếu xuất NL để phối, trình QLSX (kèm phiếu của KD); gửi nhóm Thu mua / QLDL lấy báo giá. Zalo *SX - Đề nghị phối-mua mới BTP (QLDL)*, *SX - Quản lý nguyên liệu trong nước/nhập khẩu (Thu mua)*.
5. Nhận báo giá (số lượng, đơn giá, ngày có hàng, **thời hạn áp dụng giá**); ĐP NL/BTP tính giá vốn SX BTP; báo GVKD; GVKD chốt với KD: hủy dự trù / hủy mua, tìm NCC khác, hoặc chấp nhận + chỉ định kho nhập.
6. Yêu cầu Thu mua / QLDL mua hoặc phối, theo dõi; **P TCKT từ chối duyệt thanh toán thì báo ngay để KD tìm phương án thay thế**; nhập Drive *3. XUẤT NHẬP TỒN NL, BTP*.
7. Công ty cấu thành mang NL sang: gửi yêu cầu phối, lấy hóa đơn phí phối trộn, lập BĐM thuế / nội bộ, ghi công nợ, đề nghị nhập + xuất kho.

**D. Điều chuyển kho** (duyệt QLSX, KD)
1. KD chốt loại, số lượng, đơn, kho chuyển / nhận; trình phương án vận chuyển: **xe công ty đặt riêng, xe công ty ghép chuyến (nhóm DR.XANH), thuê ngoài (qua Thu mua)**; KD chọn; chuyển BTP giữa NCC thì Lab bảo đảm tiêu chí chất lượng.
2. Thực hiện: nhận thông tin tài xế, ngày, địa chỉ; **báo NCC trước 1 ngày**; gửi đề nghị xuất kho tại NCC xuất, đề nghị nhập kho tại NCC nhập; **trong ngày nhận bản chụp có chữ ký hai bên**; gửi P TCKT trong ngày: cùng công ty lập phiếu đề nghị chuyển kho nội bộ; khác công ty lập phiếu xuất hóa đơn / xuất kho / nhập kho (Thuế) hoặc phiếu xuất bán nội bộ / xuất / nhập (Nội bộ).
3. Bán giữa các thương hiệu (chỉ điều chuyển số liệu, không luân chuyển thật): KD chốt số lượng chia lại; kiểm tồn trên **Misa Thuế và Misa Nội bộ**; Misa nội bộ lệch phiếu KD thì báo KD sửa; Misa Thuế không đủ thì lập phương án chứng từ; lập chứng từ nội bộ + thuế.

**E. Quản lý nhập kho**
1. Test trước khi nhập: **ngoại dạng 1-2 ngày; hàm lượng 14 ngày**. Tên của công ty: BTP mua thì test cả ngoại dạng + hàm lượng; BTP phối thì theo yêu cầu cấp trên + hàm lượng định kỳ. Tên NCC GC: test cả hai; TP quy cách lớn (từ 1L) hỏi QLDL số mẫu. **Mỗi lần lấy 2-4 mẫu, lưu mẫu đối chiếu**. *Phiếu yêu cầu test của LAB*.
2. Nhập NL/BTP mua qua Thu mua: Thu mua báo ngày hàng về (trong ngày / trước 1 ngày), ĐP TP báo kho; kho gửi chứng từ có chữ ký hai bên, ảnh lô hàng, nhãn, **biên bản cân tổng khối lượng**; nhận kết quả Lab do Thu mua yêu cầu; **ngày SX trên bao bì NL phải trước hoặc bằng ngày nhận hóa đơn NL**.
3. Nhập NL/BTP mua qua QLDL: 3.1 mua từ NCC GC này sang NCC khác / Lab / kho khác (QLDL chuyển kho, lập đề nghị chuyển kho cho ĐP NL/BTP ký nháy); 3.2 mua BTP đóng trực tiếp tại NCC GC. Chứng từ: Phiếu đề nghị mua, Phiếu nhập kho mua, COA / Phiếu kiểm tra chất lượng, Hợp đồng, Hóa đơn, Phiếu kiểm soát chất độc. Tiêu chí kiểm tra của Lab gồm **mã CAS**.
4. Nhập kho từ *đổ thu* / dư sản xuất: **chưa xây dựng** (ghi *sẽ xây dựng sau*).
5. Hàng cho / tặng tại NCC / kho: ký nháy đối chiếu trên Misa nội bộ, cập nhật Drive.

**F. Xuất kho và kiểm soát hao hụt** (duyệt QLSX)
1. Xuất kho SX khi đủ BTP: duyệt trạng thái BTP trên Drive *Dữ liệu BTP*; ngày NCC có hàng lập đề nghị xuất kho BTP + LSX (với Nhà máy NTV) gửi QLDL; QLDL gửi P TCKT bộ (phiếu xuất BTP / VTBB, hóa đơn NCC, phiếu nhập kho TP). **Phiếu xuất BTP lập trước hoặc cùng ngày LSX**.
2. Xuất NL, phụ gia phối BTP mới: kiểm pháp lý, số lượng; lập đề nghị phối + xuất kho NL; QLSX duyệt; QLDL gửi lệnh phối cho NCC; trạng thái *chưa đủ BTP*, phối xong xác nhận **trong sai số cho phép** thì *có BTP*; vượt sai số báo QLSX; lập đề nghị nhập kho BTP + nhập phí phối, QLDL đối chiếu công nợ, nhận hóa đơn phối trộn.
3. Xuất xử lý hao hụt: qua kiểm kê định kỳ / SX thực tế; NCC xác định nguyên nhân (tự nhiên hay theo lô); **đối chiếu tỷ lệ % hao hụt cho phép theo hợp đồng**; chuyển sang kho hàng lỗi / chờ xử lý. Vượt hạn mức: NCC đền hàng (chuyển từ kho lỗi về kho dùng sau khi QLDL ký với NCC) hoặc đền tiền (lập đề nghị xuất kho hao hụt, P TCKT theo dõi hoàn / cấn trừ). Trong hạn mức: *Phiếu đề nghị đưa vào chi phí* (ghi khoản mục + công ty chịu).
4. Xuất xử lý hư hỏng: nhận hình, chi tiết, số lô, khối lượng, biên bản; chuyển kho lỗi; Lab + Lab NCC giám định; phương án: tiếp tục dùng (bố trí đơn phù hợp), hủy (NCC thuê đơn vị tiêu hủy, phiếu xuất hủy), **tái chế (chỉ BTP, phải xác định lại công thức / pháp lý trước-sau, có xác nhận Pháp lý + P TCKT)**.
5. Xuất kho chi phí theo yêu cầu bộ phận khác: đối chiếu tồn Nội bộ + Thuế; cùng công ty xuất kho nội bộ; khác công ty xuất hóa đơn + xuất kho (Thuế) hoặc xuất bán nội bộ (Nội bộ).

**G. Đối chiếu định kỳ và báo cáo**
1-2. Đối chiếu tồn / công nợ khi NCC chủ động gửi biên bản hoặc không: đồng bộ **mã công ty - mã NCC GC**; kiểm Drive tồn + Misa Thuế + Misa Nội bộ; lập biên bản giải trình chênh lệch + biên bản xác nhận tồn; QLSX duyệt; NCC gửi biên bản chính thức, mỗi bên một bản. Drive *9. ĐỐI CHIẾU TỒN KHO TẤT CẢ NCC*; *Giấy ủy quyền QLSX ký BB*.
3. Phân bổ, thanh toán chi phí lưu kho: **áp dụng NCC Basel, Hà Long, Thuận Thành Phát**; chính sách lưu kho từ QLSX (loại, lượng, kỳ hạn, thời điểm); các nhóm đề xuất cắt giảm, phản hồi chi phí theo thương hiệu. (Người thực hiện ghi ĐP VTBB dù nằm trong QT NL/BTP.)
4. Báo cáo KD: tồn từng thương hiệu; số lượng nhà máy đóng được theo pháp lý; tỷ lệ hao hụt khi phối; MOQ BTP; NCC được / phải mua dự trù; chi phí lưu kho.

**H. Khảo sát NL/BTP phù hợp công nghệ NCC GC**: KD gửi đề nghị khảo sát (ruột, dòng công thức, NCC nào) hoặc đơn chưa khảo sát thì yêu cầu KD lập; xác định mã NL/BTP, nguồn, thời gian, phụ gia; gửi NCC kiểm tính phù hợp; **nhận mẫu thử 10-14 ngày**, gửi Lab; QLSX duyệt, phản hồi KD. *Phiếu yêu cầu thử nghiệm NCC GC*.

**I. Quản lý mẫu cho tặng** (không phục vụ SX, không xuất chi phí, **không quản lý tồn thực**): ghi mục đích, đơn vị cho / tặng (MST, tên, liên hệ), số lượng, thông số kỹ thuật, mã / tên VTBB của NCC, thời gian và cách nhận; QLSX duyệt việc cần làm; ghi nhận test, chụp, lưu, gửi.

**J. Tính giá vốn BTP**: nhận yêu cầu từ QLSX / Giá vốn: khảo sát thì **giá tạm**, quyết định mua thì **giá chính thức**; điều chỉnh khi phí phối NCC đổi. Cấu thành: NL / BTP (Thu mua cấp giá) + phí phối NCC + **hao hụt NL khi phối** + phí khác (QLDL / Giá vốn cấp). *Bảng giá BTP*, trình QLSX, gửi Giá vốn chốt với KD, lưu Drive.

Biểu mẫu: DSQL BTP Phân bón / Thuốc BVTV; Lệnh sản xuất; Phiếu đề nghị xuất kho NL / BTP; Phiếu đề nghị nhập kho BTP / TP; Phiếu đề nghị mua hàng hóa dịch vụ; Phiếu yêu cầu xuất hóa đơn (Thuế); Phiếu đề nghị xuất bán nội bộ; Phiếu đề nghị đưa vào chi phí; Biên bản xác nhận tồn kho cuối kỳ; Biên bản kiểm tra và giải trình chênh lệch. Drive: SX - Điều phối Thành phẩm; Dữ liệu BTP; 3. Xuất nhập tồn NL, BTP; *Tên thương hiệu* - Yêu cầu đặt hàng TP (có sheet Dự trù BTP); Dự trù KD cập nhật giá. Zalo: Đặt hàng + Tên NCC GC; SX - Cập nhật giá vốn + thương hiệu; 05. CUNG ỨNG - HÓA ĐƠN NỘI BỘ; SX - Yêu cầu TM đặt NL, BTP; SX - Yêu cầu QLDL đặt NL, BTP; DR.XANH - ĐK sử dụng xe tải; QLDL làm việc với NCC; QLDL làm việc với ĐP NL, ĐP VTBB.

### QT9. Quy trình quản lý vật tư bao bì (sheet *9. QT QL VTBB*, chủ trì ĐP VTBB)

**Mục tiêu**: kiểm soát VTBB (chai, túi, thùng, nhãn...) từ mockup, định mức, dự trù, luân chuyển, hao hụt thực tế tại NCC GC; kiểm soát **MOQ**, chi phí phát sinh, **cọc nhãn**, giảm phí lưu kho; dữ liệu **Nội bộ (NB) và Thuế** minh bạch, đồng bộ.
**Thời điểm**: khi có đơn mới / tồn thiếu / điều chuyển; định kỳ hằng tháng dự trù và cập nhật tồn; khi nhập - xuất, mua, hao hụt / hư hỏng, đối chiếu NCC.

**A. Tiếp nhận và xác định BĐM**
1. Khi thiết kế mockup và khai báo mã HH: **Thiết kế gắn mã VTBB vào hình mockup**; KD bảo đảm VTBB phù hợp (sức chứa, dạng chứa, tương thích ruột) theo tư vấn SX; ĐP VTBB nhập BĐM chi tiết (Drive *4. XUẤT NHẬP TỒN - VTBB*), khai mã VTBB mới nếu chưa có; lập BĐM VTBB, xác định nơi SX, in trình QLSX. Song song bộ phận Thuế xác định mã VTBB + công ty cấu thành; **sau khi đồng bộ mã Thuế - Nội bộ thì BĐM chỉ còn một bảng dùng chung**. Thay VTBB trong SX thì lập BĐM mới gửi QLDL. Biểu mẫu: *File danh mục mã VTBB theo loại (có hình)*, *Mẫu BĐM*. Zalo *KHAI BÁO SẢN PHẨM*.
2. Nhận đơn trên Drive Điều phối, lấy mockup từ Thiết kế; sau khi Pháp lý xác nhận đơn vị cấu thành, xác định BĐM + số lượng VTBB (NB và Thuế), kiểm tồn. **NCC Thu Loan (IDA, ABA): ĐP VTBB báo số lượng cần in cho Thiết kế, Thiết kế tự làm với NCC**. Biểu mẫu *8.1 BIỂU MẪU VTBB*; Drive *VTBB - THEO DÕI VẬT TƯ 2025* sheet *XUẤT HÀNG TP*. Duyệt KD.

**B. Kiểm tồn và phương án**
- Đủ tồn: trạng thái **Đủ VTBB** trên Drive Điều phối kèm số tồn thực (NB và Thuế).
- Tồn ở kho / công ty khác: NB báo KD đề xuất điều chuyển / mua; Thuế lập phiếu xuất bán nội bộ, yêu cầu xuất hóa đơn, P TCKT xác nhận đủ tồn thuế; đủ cả hai phía thì xử lý như đủ tồn.
- Hết tồn: báo KD đổi VTBB khác (KD làm với Thiết kế, ĐP VTBB lập lại BĐM) hoặc mua; đổi kho SX thì chuyển kho + chỉnh cấu thành. Ghi chú gốc: *xem lại nên bỏ việc kiểm tra thay thế ra khỏi quy trình*.

**C. Dự trù VTBB**
1. Định kỳ cập nhật cho KD: tồn (NB - Thuế), công nghệ SX VTBB, **MOQ theo NCC, phí lưu kho, thời gian quy định cọc nhãn, thời gian thu mua từng loại VTBB**, phương án tối ưu chi phí; nhắc KD kiểm tồn trước khi dự trù.
2. KD xác nhận tài chính với P TCKT, gửi phiếu đề nghị mua (mã hàng, số lượng, **mã pháp lý, kho nhận**); **ĐP VTBB phản hồi chậm nhất 4 ngày**.
3. Kiểm tồn thực tại NCC, MOQ; Pháp lý phân loại công ty cấu thành + công ty nhận hóa đơn; VTBB chưa khảo sát với NCC thì sang mục I; NCC cũng có VTBB tương ứng thì so giá mua ngoài vs đặt NCC.
4. Lập phiếu đề nghị mua kèm danh sách VTBB (chất liệu, công nghệ), trình QLSX, gửi nhóm Thu mua *SX - YÊU CẦU ĐẶT VTBB*.
5. Nhận báo giá Thu mua trên Drive (số lượng, đơn giá, ngày có hàng, **thời hạn áp dụng giá, tên trên hóa đơn**); kiểm phù hợp công nghệ NCC; chốt với KD: hủy / tìm NCC khác / mua.
6. Thu mua mua, thanh toán, nhập kho; **P TCKT từ chối thanh toán thì Thu mua báo ngay ĐP VTBB**; Drive *DEMO 5. THU MUA TRẢ KẾT QUẢ CHO KHỐI VP*.

**D. Kiểm soát cọc nhãn**
1. QLSX cấp danh sách NCC có chính sách cọc nhãn: **An Nông, Âu Việt, Đại Tâm, Thu Loan**; NCC duyệt nhãn trên nhóm *Duyệt nhãn - In ấn VTBB*, báo số tiền cọc cho QLDL; ĐP VTBB tổng hợp, KD chốt (sản phẩm, sản lượng, số tiền); QLDL làm hợp đồng, khai báo, thanh toán.
2. Theo dõi sản lượng + điều kiện hợp đồng cọc; theo sản lượng TP hoặc yêu cầu ngưng SX của KD báo QLDL thanh lý, hoàn cọc; QLDL xác nhận NCC hoàn cọc kèm biên bản thanh lý.

**E. Điều chuyển kho** (duyệt QLSX / QLTH)
1. Phương án: 1.1 theo đơn hàng (KD chốt, chọn xe công ty riêng / ghép / thuê ngoài, KD lập phiếu đề nghị chuyển kho); 1.2 **NCC yêu cầu rút vật tư** (xác định tồn + vật tư cho sản phẩm nào, có đơn thì đi đơn, không thì tìm kho chứa khác, **kiểm pháp lý điều kiện lưu trữ**); 1.3 theo yêu cầu XLSC / bộ phận khác.
2. Thực hiện: NB - cùng phần mềm Misa thì phiếu đề nghị chuyển kho, khác Misa thì phiếu xuất bán, kèm tài xế / số xe; Thuế - cùng công ty không xử lý, khác công ty thì phiếu đề nghị xuất bán + xuất hóa đơn; xác nhận nhận hàng, cập nhật số thực; gửi P TCKT phiếu xuất của kho giao.
3. Bán giữa các thương hiệu: như QT8 mục D3.

**F. Nhập kho**: 1 mua từ Thu mua (báo kho NCC nhận, chứng từ có chữ ký hai bên + ảnh); 2 **mua VTBB tại NCC GC đang SX khi thiếu** (trình KD loại + giá, khai mã, P TCKT khai Misa, lập phiếu mua + BĐM thay đổi gửi QLDL; QLDL cập nhật BĐM, công nợ, phiếu nhập kho); 3 nhập từ dư sản xuất (Thuế: QLDL yêu cầu NCC xuất bán lại, lập phiếu nhập kho kèm LSX).

**G. Xuất kho và hao hụt**
1. Xuất SX không bán VTBB cho NCC: duyệt trạng thái, xuất tạm; ngày NCC có hàng lập đề nghị xuất kho VTBB gửi QLDL. **Lập trước hoặc cùng ngày LSX**.
2. Xuất SX có bán VTBB cho NCC: Thuế xuất bán khi duyệt đơn; ngày có hàng QLDL so số đã xuất với thực SX (thiếu xuất bổ sung; dư theo dõi cho đơn sau hoặc NCC xuất trả); NB lập đề nghị xuất kho khi có TP. **Bảng phân loại tỷ lệ hao hụt: ngoài ngưỡng thì NCC xuất trả lại**. Ghi chú: quy trình thuế phần hao hụt chưa xong, cần Kế toán + SX thống nhất tỷ lệ theo hợp đồng.
3. Hư hỏng, thất thoát, hao hụt: chuyển kho tạm, xác định nguyên nhân; còn dùng thì lưu; hủy thì NCC thuê đơn vị tiêu hủy, *Biên bản tiêu hủy*, phiếu xuất hủy.
4. Xuất kho chi phí theo yêu cầu: VTBB không có thì trả phiếu; còn lại như QT8.

**H. Đối chiếu và báo cáo**: đối chiếu theo tháng hoặc theo đơn (đồng bộ mã công ty - mã NCC, Drive tồn + Misa Thuế + Misa NB, biên bản giải trình, biên bản xác nhận tồn, Giấy ủy quyền QLSX ký); phân bổ phí lưu kho (Basel, Hà Long, Thuận Thành Phát); **báo cáo KD: dữ liệu VTBB (mã, tên, hình, giá, sản phẩm áp dụng), lịch sử sử dụng theo BĐM, tồn theo thương hiệu và tổng, giá min / max 5 lần mua gần nhất**, pháp lý (nhà máy đóng được nhãn / túi), công nghệ theo NCC, tỷ lệ hao hụt theo loại VTBB / NCC, MOQ, đơn giá lưu kho, đề xuất tối ưu, tình trạng cọc nhãn.

**I. Khảo sát VTBB phù hợp công nghệ NCC GC**: **Nhóm 1 bắt buộc qua SX: chai, nhãn, túi, thùng, NDT, can, xô, túi PE; Nhóm 2 không cần qua SX: còn lại; nhà máy không cần qua SX**. Tiếp nhận như QT8 H; VTBB có sẵn thì điều chuyển để khảo sát, chưa có thì theo quy trình khảo sát của Thu mua; **gửi NCC 11 bộ với An Nông, 4-5 bộ với NCC khác; kết quả 10-14 ngày**; QLSX duyệt, phản hồi KD. Drive *ABA & VTBB - QUY TRÌNH TƯƠNG TÁC - TIẾP NHẬN YÊU CẦU VTBB*.

**J. Mẫu cho tặng**: như QT8 mục I (Drive *Form_VTBB Khảo sát-Cọc nhãn-Mẫu.xlsx*).

Biểu mẫu (13): Phiếu đề nghị mua hàng hóa dịch vụ; Phiếu đề nghị chuyển kho; Phiếu đề nghị xuất bán (NB + Thuế); Phiếu yêu cầu xuất hóa đơn; Phiếu đề nghị nhập kho vật tư; Phiếu đề nghị xuất kho VTBB; Phiếu đề nghị xuất hủy vật tư; Biên bản xác nhận tồn kho đối tác; Biên bản kiểm tra và giải trình nội bộ; File danh mục mã VTBB theo loại (kèm hình); **Bảng phân loại tỷ lệ hao hụt theo NCC**; Giấy ủy quyền QLSX ký biên bản đối chiếu. Drive: SX - Điều phối TP; 4. Xuất nhập tồn VTBB; VTBB - Theo dõi vật tư 2025; Tiếp nhận yêu cầu VTBB; Dự trù vật tư của thương hiệu; DEMO 5; Hệ thống báo cáo mới cho KD; Quản lý mẫu cho tặng mới. 13 nhóm Zalo.
Cuối sheet có ghi **điểm cần thống nhất trước khi ban hành**: (1) mâu thuẫn ở mục VIII về nghiệp vụ thuế; (2) ghi chú dở ở II.3 và VII.1.2; (3) vai trò QLDL có tách biệt QLSX không; (4) bổ sung thời lượng các bước còn trống. (Đánh số mục trong ghi chú không khớp với chữ A-J của thân bảng.)

### QT10. Quy trình đặt dịch vụ vận chuyển Grab (sheet *10. QT QL DVVC*, ĐP TP phụ trách Grab)

**Mục tiêu**: quản lý chi phí vận chuyển **theo thương hiệu**; kiểm soát giao nhận và hàng hóa trong quá trình giao. **Thời điểm**: khi gửi hàng cho khách / đối tác / nội bộ.

| Bước | Ai (phối hợp / duyệt) | Nội dung | Biểu mẫu / kênh |
|---|---|---|---|
| 1 Tạm ứng | ĐP TP (P TCKT) - duyệt QLSX | Tạm ứng cá nhân định kỳ theo quy trình tạm ứng kế toán | Đề nghị tạm ứng |
| 2 Tiếp nhận yêu cầu | ĐP TP (BPSX, TM) | Test mẫu TP thì sang bước 3; yêu cầu trong SX / TM cần: kho nhận + kho gửi (địa chỉ, người giao nhận), nội dung (gì, bao nhiêu, lưu ý), **phân bổ chi phí**, ngày yêu cầu, kho xuất ghi tên mẫu, khối lượng, công ty DEGO; rồi sang bước 4 | Zalo *VẬN CHUYỂN GRAB* |
| 3 Lập phiếu đề nghị xuất kho (khi lấy mẫu) | ĐP TP (P TCKT, KD, BP Kho) - duyệt QLSX | NCC do ĐP TP phụ trách: lập *Giấy đề nghị xuất vật tư*, QLSX ký, gửi nhóm, **trong ngày gửi bản cứng cho Kế toán**; KD xuất kho trên Misa, gửi hình đơn đặt hàng Misa; Kho Dr.Xanh phản hồi xuất được. NCC không do ĐP TP phụ trách: chỉ nhận phiếu | Zalo *MISA XUẤT MẪU + TÊN TH*, *SX & KHO XUẤT HÀNG* |
| 4 Đặt xe, xác nhận shipper | ĐP TP (BP Kho, Grab) | Book Grab trên app; shipper không cung cấp chứng từ bên giao / nhận, chỉ chụp gửi người đặt; Grab chụp mẫu; thanh toán từ tài khoản đã tạm ứng khi giao xong; báo giờ giao; **yêu cầu xuất hóa đơn trên app (tự gửi email kế toán)** | App Grab; ghi chú: bổ sung email BP nhận hóa đơn để bớt đối chiếu |
| 5 Đề nghị thanh toán | ĐP TP (P TCKT) - duyệt QLSX | Hồ sơ: Giấy đề nghị thanh toán (tài khoản app Dego đứng tên) - **một bộ nội bộ phân bổ chi phí theo thương hiệu, một bộ thuế lấy về Dego**; toàn bộ hóa đơn kỳ (từ kế toán); bảng kê vận đơn; đối chiếu hóa đơn với app; QLSX ký, nộp kế toán, kế toán hoàn tiền cá nhân | Drive *THEO DÕI CHI PHÍ*; ghi chú: chi phí thuế Grab chia đều cho các thương hiệu |
Mục lục mô tả QT10 là *thanh toán dịch vụ vận chuyển dựa trên bảng kê trên app mỗi tháng*.

### QT11. Quy trình xử lý sự cố trong sản xuất (sheet *11. QT XL SỰ CỐ TRONG SX*, chủ trì ĐP TP, trạng thái *Cần kiểm tra lại*)

Nằm trong tệp nhóm A nhưng là phần sự cố (nhóm khác sẽ đọc tệp BC SỰ CỐ / Sự cố sản xuất); ghi gọn ở đây để nối với pháp lý.
**Phạm vi**: sự cố trước khi TP hoàn thiện nhập kho: chuẩn bị / đặt NL, BTP, VTBB; phối chế / gia công tại NCC; điều kiện pháp lý và vận hành của NCC khi đang làm đơn.
**Bước**: 1 tiếp nhận qua Zalo (ảnh / video, mã hàng, số lượng, NSX, tình trạng, nơi phát hiện, số đã bán, tồn tại khách / kho khác, yêu cầu khác), cập nhật Drive, tra lịch sử lỗi - 2 phân loại: **điều kiện pháp lý** (hết hạn / chưa có Giấy đủ ĐK SX / mua bán, GĐK sản phẩm, hợp chuẩn hợp quy, giấy ủy quyền, hợp đồng NCC; hóa đơn trễ), **NL/BTP** (chậm, thiếu, lỗi, dùng nhầm so với BĐM), **VTBB** (chậm, thiếu, móp, bể, sai mockup, nhầm), **công thức phối chế** (mẫu / lô không đạt), **điều kiện vận hành NCC** (máy, công suất, không thống nhất giá / hóa đơn / giao hàng) - 3 kiểm tồn, tiến độ, hợp đồng (ĐP NL/BTP, ĐP VTBB, QLDL; kiểm ĐP TP) - 4 lập phương án theo nhóm: pháp lý thì **ngưng SX liên quan, chờ đủ pháp lý**, xem luân chuyển tồn cho đơn khác; NL/BTP / VTBB thì đẩy nhanh thay thế, dùng nhầm thì tư vấn Lab / Pháp lý, chốt KD, chỉnh BĐM; công thức thì ngưng đến khi mẫu đạt hoặc hủy đơn sau số lần phối lại quy định; vận hành thì đôn đốc, ngưng đơn khi chưa thống nhất, chuyển NCC khác phải kiểm pháp lý, năng lực, nhãn, giá - 5 chứng từ: thủ tục **thuế** (văn bản theo dòng pháp lý, hủy / điều chỉnh / xuất bổ sung hóa đơn qua P TCKT, phiếu đề nghị xuất kho SX, phiếu đề nghị xuất hóa đơn khi bán giữa công ty nội bộ, phiếu nhập / chuyển kho, phiếu đề nghị hủy, BĐM mới) và thủ tục **nội bộ** (xuất kho, chuyển kho cùng thương hiệu, nhập kho, **xuất bán nội bộ giữa thương hiệu**, hủy, BĐM) - 6 theo dõi tiến độ - 7 thống kê chi phí, xác định bộ phận chịu, Giấy đề nghị thanh toán (công ty) / **Biên bản cấn trừ công nợ (NCC GC)** - 8 cập nhật Drive *THEO DÕI SỰ CỐ*, báo các hạng mục cấu thành cần lưu ý cho đơn sau.

Sheet phụ *TH sự cố trong SX (chốt QT 11 ...)* liệt kê 10 trường hợp có **mức nghiêm trọng**, liên hệ làm rõ, phương án, luồng hóa đơn, lấy chi phí, người làm (ĐP TP), kiểm (QLSX):

| # | Trường hợp | Mức | Chi phí về đâu |
|---|---|---|---|
| 1 | NCC từ chối / ngừng hợp tác giữa chừng | Cao, ưu tiên 2 | Chi phí tìm NCC mới, khảo sát gấp về thương hiệu |
| 2 | Test / phối mẫu không đạt (kể cả sau 2 lần phối lại) | Cao, ưu tiên 2 | Chi phí mẫu vào phát triển SP; lỗi NCC thì NCC chịu |
| 3 | Thiếu NL/BTP khi đến hạn SX | Cao, **ưu tiên 1** | Chênh lệch giá mua khẩn cấp về thương hiệu / đơn |
| 4 | Thiếu / chậm VTBB trước đóng gói, đổi mockup giữa chừng | Trung bình (lên Cao nếu sát ngày giao) | VTBB tồn dư do đổi mockup về bộ phận ra quyết định đổi |
| 5 | Hao hụt NL vượt định mức khi phối | Trung bình | Trong hạn mức vào chi phí thương hiệu; vượt thì NCC chịu, cấn trừ công nợ |
| 6 | Đơn đã gửi NCC phát hiện thiếu pháp lý | **Rất cao, ưu tiên 1** | Chi phí dừng SX / đổi pháp nhân về thương hiệu; có thể hủy / điều chỉnh hóa đơn |
| 7 | Giá NCC chốt lệch giá đã duyệt | Trung bình | Chênh lệch (nếu chấp nhận) vào giá vốn thương hiệu / đơn |
| 8 | Thất lạc / hư hỏng khi điều chuyển kho nội bộ | Trung bình | Bên gây thiệt hại (kho giao, kho nhận, vận chuyển) |
| 9 | **Sai / trùng mã khai báo trên Misa hoặc dữ liệu quản lý (BĐM, mã BTP, VTBB)** | Trung bình | Không phát sinh, chỉ chỉnh dữ liệu; rà chứng từ đã dùng mã sai |
| 10 | NCC nhận cọc nhãn nhưng không hoàn cọc / không SX | Trung bình | Theo hợp đồng; ghi tổn thất nếu không thu hồi |

### QT12. Quy trình xử lý sự cố sau sản xuất (sheet *12. QT XL SỰ CỐ SAU SX*, chủ trì NV XLSC, ghi *đang gộp, cần xem lại*)

**Phạm vi**: TP tại NCC, tại kho Dr Xanh, hàng đã bán tại khách, hàng đang vận chuyển. Khung giống QT11 nhưng người làm là **NV XLSC**; bắt buộc **lập biên bản xác nhận số lượng giao nhận giữa các bên**. Phân loại: **pháp lý** (giấy đủ ĐK, GĐK / QĐ lưu hành, hợp chuẩn hợp quy, ủy quyền, hợp đồng, hóa đơn chưa có / hết hạn; hạn sử dụng hết / trôi thông tin; sai nhãn theo quy định), **hàm lượng / chất lượng** (màu, mùi, lắng cặn, vón cục, tách lớp, phình chai, cháy lá, đóng thiếu thể tích...), **VTBB** (móp, thấm, bể chai, sai quy cách, nắp, seal, cốc, nhãn lỏng / rách / nhầm / ngược / lỗi màu, thùng), **vận hành** (giao thiếu, hư do vận chuyển). Bước 3 Pháp lý SX + Pháp lý chung kiểm dòng pháp lý, hóa đơn đầu vào / ra. Phương án: pháp lý thì yêu cầu bổ sung và **cảnh báo tạm ngưng SX, gia công, mua bán đến khi đủ giấy**; hết HSD thì thay nhãn / xử lý lại BTP, thu hồi, lên **đơn xử lý lại** cho ĐP TP; chất lượng thì Lab kiểm, đạt thì hướng dẫn lại khách, không đạt thì thu hồi, xác định lỗi, đơn xử lý lại; VTBB thì xác định bên chịu (NCC hay Công ty); vận hành thì biên bản sự việc, bổ sung hàng. Chứng từ thuế / nội bộ như QT11. Biểu mẫu: Đề nghị thanh toán; **Biên bản thu hồi khoản tiền phát sinh**; Biên bản cấn trừ công nợ.

### QT13. Quy trình dừng làm việc với NCC GC (sheet *QT DỪNG LÀM VIỆC NCC GC*)

**Mục tiêu**: kiểm soát chấm dứt hợp tác; lập phương án thu hồi NL, BTP, VTBB, hàng lỗi, công nợ tồn tại NCC; hoàn tất pháp lý, chứng từ kế toán, cập nhật dữ liệu nội bộ.
**Thời điểm**: khi quyết định ngưng do NCC vi phạm hợp đồng, không đạt đánh giá định kỳ, hoặc hai bên không còn nhu cầu.

| Bước | Ai (phối hợp / kiểm / duyệt) | Nội dung | Biểu mẫu / kênh |
|---|---|---|---|
| 1 Tiếp nhận thông tin dự kiến ngưng | QLDL (QLSX / Giám đốc) | Nhận vấn đề từ NCC, dự kiến phương án. NCC ngừng giữa chừng: **ĐP TP xử lý gấp, tìm NCC thay thế, báo KD** | |
| 2 Thông báo và đánh giá từ Sản xuất | QLDL (Pháp lý SX, ĐP VTBB, ĐP NL/BTP, ĐP TP, Giá vốn, XLSC, P TCKT, KD, R&D, Pháp lý chung, BP Kho Dr Xanh, Giám đốc/QLTH) - duyệt QLSX | Các nhóm SX rà nghiệp vụ liên quan NCC, đánh giá phương án kèm chi phí; list việc + chi phí + điểm cần thương lượng theo checklist | Drive sheet *TỔNG HỢP* của *DANH_GIA_NGUNG_HOP_TAC_NCC_v12* |
| 2.1 Đánh giá từ P TCKT | P TCKT | Nhận số liệu đối chiếu công nợ, tồn kho, hóa đơn; đánh giá rủi ro; **xác nhận công nợ đã thanh toán hết (số dư = 0 đồng)**; xác nhận đã nhận đủ hợp đồng, phụ lục; xác nhận trực tiếp trên Drive | *8. Đối chiếu công nợ NCC, thanh toán và dự chi (QLDL)*; ĐÁNH GIÁ NGƯNG HỢP TÁC NCC |
| 2.2 Đánh giá từ Kho | BP Kho | Thống kê TP tại kho, phân loại (thành phẩm, lỗi, chờ / chưa có phương án) | ĐÁNH GIÁ NGƯNG HỢP TÁC NCC |
| 2.3 Đánh giá từ KD | KD | Nhận đối chiếu tồn VTBB / NL / BTP, đơn hàng (dự trù, xử lý lại, đang sản xuất, thành phẩm), tiến độ, danh mục NCC; lên phương án tồn kho; rà đơn chưa báo SX; dựa doanh số, lợi nhuận, khách hàng, chi phí ngưng để đề xuất danh mục thay thế hoặc hợp tác đến giai đoạn nhất định | như trên |
| 2.4 Đánh giá từ R&D | R&D | Thống kê mẫu lưu đến ngày hết hạn; danh sách công thức của Dego đang giao dịch tại NCC; gắn trách nhiệm chất lượng sau ngưng và bảo mật công thức. Đơn cũ chưa lưu mẫu: khi sự cố yêu cầu KH cung cấp mẫu | như trên |
| 2.5 Đánh giá từ Pháp lý chung | Pháp lý chung | Kiểm thanh lý hợp đồng và rủi ro khác | như trên |
| 2.6 Đánh giá từ Giám đốc | Giám đốc | Can thiệp khi các phòng không xác định được vấn đề | như trên |
| 2.7 QLSX phê duyệt phương án | QLDL tổng hợp 2.0-2.6 - duyệt QLSX | Quyết định ngưng chính thức; không xác định được thì chuyển Giám đốc | sheet TỔNG HỢP |
| 3 Thông báo, thương lượng với NCC | QLDL (QLSX, NCC) | Gửi văn bản thông báo theo mẫu; họp thống nhất ngày chấm dứt, đơn dở dang, công nợ, hàng tồn, cọc nhãn, hóa đơn; lập biên bản | BB cuộc họp NCC GC |
| 4 Phân bổ công việc | QLSX (các BP như bước 2) | Giao việc + deadline theo chuyên môn; QLDL tổng hợp | Bảng phân công / Checklist theo dõi |
| 5 Các BP thực hiện, báo tiến độ | các BP - kiểm QLSX | Làm theo form của từng BP; QLDL tổng hợp và đánh giá theo form đánh giá định kỳ NCC GC, QLSX duyệt | BB xác nhận tồn kho cuối kỳ; Phiếu chuyển kho / xuất bán; BB đối chiếu công nợ; BB đánh giá theo tiêu chí NCC GC; *ĐÁNH GIÁ ĐỊNH KÌ NCC GC*; *2026_QUY DINH QUAN TRI HOP DONG THUONG MAI_FINAL.docx* |
| 6 Ký biên bản thanh lý | QLDL (NCC, Pháp lý chung) - kiểm QLSX | QLDL lập biên bản, Pháp lý duyệt, gửi NCC theo quy trình duyệt pháp lý hợp đồng | BB thanh lý hợp đồng; BB thanh lý cọc nhãn; BB tiêu hủy (nếu có) |
| 7 Cập nhật trạng thái, lưu hồ sơ | QLDL | Đặt trạng thái NCC là **Ngưng hợp tác** kèm ngày + lý do; lưu đủ bộ hợp đồng, phụ lục, thông báo, biên bản họp, biên bản thanh lý + phụ lục đối chiếu, thống kê, biên bản nội bộ; **bản gốc biên bản thanh lý giao P TCKT, QLDL lưu scan** | |

Mục lục còn nhắc *CHECKLIST TRƯỚC KHI DỪNG LÀM VIỆC NCC GC* (mục 14) nhưng không có sheet tương ứng trong tệp; nội dung nằm ở tệp *ĐÁNH GIÁ NGƯNG HỢP TÁC NCC.xlsx* (ngoài phạm vi nhóm A).

### Phụ trợ quy trình: tiêu chí đánh giá NCC GC (sheet *19. TIÊU CHÍ ĐÁNH GIÁ NCC GC*, trạng thái *Cần kiểm tra lại*)

Dùng ở QT13 bước 5 và đánh giá định kỳ. **Định kỳ 6 tháng / lần hoặc đột xuất khi có sự cố**; QLDL, ĐP NL/BTP, ĐP VTBB, ĐP TP, XLSC, Pháp lý SX chấm độc lập phần mình; QLDL tổng hợp; **QLSX duyệt cuối**.

| Nhóm (điểm) | Tiêu chí (điểm tối đa) - BP chấm | Mốc chấm chính |
|---|---|---|
| 1 Pháp lý, hồ sơ năng lực (15) | Hồ sơ pháp lý (7) - Pháp lý SX, QLDL; Sẵn sàng ký hợp đồng (4); Minh bạch thông tin (4) | 7đ đủ giấy còn hạn từ 6 tháng; 5đ còn hạn dưới 3 tháng chờ bổ sung; 2đ thiếu 1 loại bổ sung được trong 3 tháng; 0đ hết hạn / không có |
| 2 Năng lực SX, công nghệ (20) | Công suất theo quy mô đơn (5) - QLDL, ĐP TP; Đa dạng hình thức (nhận NL/BTP, VTBB mang sang) (5); Máy móc, quy cách đóng gói (5); Khả năng test / phối (5) - có R&D | đạt lần 1-2 được 5đ |
| 3 Chất lượng (20) | Tỷ lệ lỗi TP/BTP (8) - XLSC, R&D, QLDL; Hao hụt so định mức (6); Thất lạc / hư hỏng, không FIFO lô (6) | lỗi dưới 1% = 8đ, 1-3% = 5đ, 3-5% = 2đ, trên 5% = 0đ |
| 4 Tiến độ (15) | Đúng thời gian SX cam kết (7) - ĐP TP; Tuân thủ báo trước giao nhận (4); Đáp ứng đơn gấp (4) | trễ nhẹ ≤ 10% có báo trước 1-2 ngày = 5đ |
| 5 Giá, chi phí (10) | Giá gia công cạnh tranh, ổn định (6) - Giá vốn, QLDL; Chính sách lưu kho, chiết khấu, phạt (4) | |
| 6 Hợp tác, xử lý sự cố (10) | Thái độ phối hợp (5); Xử lý sự cố (5) - XLSC, QLDL, ĐP TP | phản hồi ≤ 24h = 5đ, 2-3 ngày = 3đ, trên 3 ngày = 0đ |
| 7 Tài chính, công nợ (5) | Đối chiếu công nợ + hoàn cọc đúng hạn (3) - QLDL; Xuất hóa đơn đúng thời điểm (2) | |
| 8 Vị trí, logistic (5) | Vị trí kho / nhà máy (3) - ĐP TP; Hình thức giao nhận linh hoạt (2) | |

Xếp loại: **từ 90 Xuất sắc** (ưu tiên dài hạn); **75-89 Đạt**; **60-74 Cần cải thiện** (làm lại điều khoản); **dưới 60 Không đạt - ngưng hợp tác, tìm NCC thay thế** (nối sang QT13). Cột ghi chú có câu hỏi treo: *trùng hao hụt phía dưới*, *thất lạc = chất lượng?*.

---

## 3. Danh mục dữ liệu (các sheet Data* và Admin của [DRV])

Quy định chung ([DRV] Mục lục): **mỗi bộ phận tự cập nhật sheet mình quản lý** và phải ghi lịch sử sửa đổi ở Drive của bộ phận (chưa có form). Dòng 1 mỗi sheet ghi nguồn từng cột: *Lấy từ Misa*, *Lấy từ thu mua*, *Nhập tay*, *Click chọn từ data admin*, *Công thức*, *Chưa xác định*. Toàn bộ danh mục phải đồng bộ với Misa (mã do P TCKT tạo trên Misa theo QT2).

| Danh mục | Trường chính | Nguồn | Ai khai báo / quản lý | Quy định |
|---|---|---|---|---|
| **Admin - Công ty nội bộ** | Tên P/BP/TH viết tắt, công ty viết tắt, tên công ty, MST, địa chỉ, giám đốc / chủ cơ sở (tên người - không chép) | Tên, MST, địa chỉ lấy từ Misa; viết tắt nhập tay | Admin (BP cung cấp ghi một cá nhân) | Viết tắt `CTY.` + tối đa 5 chữ (VD CTY.NNABA); 10 pháp nhân: NN Dego, Icare, IDA, ABA, Dego (Holding), Agricare, Bamboo, N2SBio, Dr. Xanh (+ NPP Dr.Xanh 1, 2), Lona |
| **Admin - Bộ phận / thương hiệu** | Tên TH, viết tắt TH, tên BP, viết tắt BP | Nhập tay | Admin | `TH.` / `BP.` + tối đa 5 chữ (TH.ABA, BP.SX); ghi chú chưa nắm tên viết tắt trên Misa |
| **Admin - Kho** | Tên kho viết tắt, mã kho, thông tin nhận (tên, SĐT), địa chỉ, định nghĩa | Mã kho, liên hệ, địa chỉ từ Misa | Theo từng BP phát sinh (QT2: ĐP TP / ĐP VTBB / ĐP NL/BTP) | Dego chia kho TP, VTBB, BTP, NL, XL tại nhà máy Cần Thơ; kho Dr.Xanh (MEKONG, XL_MEKONG); **mỗi NCC GC chỉ 2 kho: `KHO NCC_<NCC>` và `KHO NCCXL_<NCC>` (hàng lỗi)**; ~35 kho, nhiều kho XL ghi *bổ sung kho sau* |
| **Admin - Phân loại nhập / xuất / tồn** | Nhập (10 loại: mua, sau phối, chuyển kho, cho / tặng, tạm, đổ thu / dư sau SX, lỗi / hư hỏng, khác, đầu kỳ, đầu kỳ lỗi); Xuất ngoài (chuyển kho, cho / tặng, mẫu thử, tạm, xử lý lỗi, hao hụt / đổ bỏ, khác, NL phối BTP, bán); Xuất theo đơn (chưa xuất, xuất tạm, xuất SX, hủy - không xuất); Tồn (tạm, có thể SX, lỗi) kèm diễn giải | Nhập tay | Admin | Dùng chung cho Drive XNT NL/BTP và VTBB |
| **Admin - Khoản mục chi phí** | Mã, tên, diễn giải (tiếp khách, đào tạo, phần mềm, VPP, in ấn vận chuyển, CCDC, bảo trì, chi phí SX phát sinh, chi phí SX - KD IDA / ABA / N2, test mẫu lab) | Từ Misa | Trưởng BP SX | |
| **Admin - thuộc tính** | ĐVT (Cái, Bộ, Kg, Lít, Ml, Gram, Cuộn, Bịch, Can, Thùng, Lon, Bao, Xô, Chai, Gói, Pallet, Lô, M2); hình dạng VTBB (tròn, vuông, tam giác); hình dạng NL/BTP (viên, cốm, bột, gel, lỏng); màu (10); độ trong (đục, trong); phân loại (trừ sâu, trừ bệnh, trừ cỏ, diệt ốc, phân bón, nguyên liệu); dòng V (V1-V6); **trạng thái sự cố** (nghi ngờ lỗi, chờ phương án, chờ chuyển hàng khác, chờ xử lý lại chính nó, chờ tiêu hủy, chờ đổ thu BTP, hoàn thành / dùng được) | Nhập tay | Admin | ĐVT viết hoa chữ đầu |
| **Data thu mua** | (a) DATA VTBB, NL: phân loại, mã, tên, ĐVT - *trống*; (b) NCC thu mua: tên, viết tắt, địa chỉ, MST (147); (c) đơn vị vận chuyển (6, chỉ tên viết tắt); (d) thời gian mua theo loại VTBB: số ngày quy định, ghi chú (vd *hàng thanh toán trước: hồ sơ 1 ngày, thanh toán 5 ngày, SX 0-7 ngày, nhận hàng 2 ngày*), ngày áp dụng, quy định theo hàng có sẵn NCC; (e) MOQ: NCC VTBB, nhóm VTBB, MOQ (84); (f) tiêu chuẩn NL (95): mã NL, tên, xuất xứ, ngoại quan, màu, độ tan, độ trong, độ ẩm, pH, hàm lượng, mã CAS, thuộc phụ lục nghị định | Lấy từ thu mua; tiêu chuẩn NL do Lab cấp cho Thu mua | Admin thu mua | Mục lục: Thu mua đang chuyển sang app nên chưa rõ cách trích dữ liệu (chính là ERP DEGO) |
| **Data pháp lý (Tổng)** | xem mục 4 | Chạy từ pháp lý (pháp lý ABA) | Pháp lý SX / pháp lý chung | |
| **Data NL/BTP** | Mã, tên, ĐVT, nhóm theo mã, phân loại, dòng V, tên thương phẩm (pháp lý), dạng ruột, màu, độ trong, thành phần, hàm lượng NL | Phân loại / dòng / màu / độ trong chọn từ Admin; còn lại nhập tay | ĐP NL/BTP | Khai mã BTPR / BTPM, NLT. Thiết kế ở Nháp chung còn có: mã SX + mã KD (quy đổi), tên pháp lý, thông số kỹ thuật, hình màu chuẩn, BĐM BTP, giá NL/BTP (mua / khảo sát, ngày, giá chưa / có VAT, phí vận chuyển về kho, kho nhận, **số ngày giữ giá, số ngày công nợ**, BP cung cấp giá, NCC), thời gian mua, MOQ. **Sheet hiện gần như trống** |
| **Data VTBB** | Khối chai / nắp / xô / can / cốc: phân loại, chất liệu, mã, tên, ĐVT, viết tắt, link hình, NCC tham khảo, hình dạng, kích thước (cao x đường kính), trọng lượng, cổ chai, màu, nhận diện riêng, kích thước nhãn phù hợp. Khối túi / nhãn: phân loại (nhãn / bao / NDT), chất liệu, mã, tên, ĐVT, **khách hàng / thương hiệu**, link hình, kích thước nhãn kể cả mép dán, **NCC GC nhận vật tư**, **mã HH thành phẩm**, tên pháp lý (chọn từ Data pháp lý), thể tích / trọng lượng, **tên trên hóa đơn**. Khối thùng / hộp: + quy cách SP, kích thước phủ bì / lọt lòng, trọng lượng, số lớp, cán màng, màu. Khối khác (bao, tem, seal, túi zip): thông số kỹ thuật | Mã, tên, ĐVT lấy từ Misa; thuộc tính chọn từ Admin; kích thước, hình nhập tay | ĐP VTBB | Theo quy tắc mã QT2 (tiền tố thực tế: NHG 2.511, NDT 1.139, NTN 857, NHD 626, THC 256, NAP 188, CHT 110, CPT 101, HOP 61, THI 54, CAN 34...). Ghi chú: cần làm lại với Thiết kế để lấy kích thước lọt lòng |
| **Data đồng bộ NCC GC** | Mã Dego, tên Dego (từ Misa), mã NCC, tên NCC (từ NCC), NCC GC, phân loại (VTBB / NL/BTP) | Misa + NCC GC | QLDL nhập tay (*chưa chốt*) | Cơ sở đối chiếu tồn / công nợ với NCC (QT8, QT9 bước đối chiếu: *đồng bộ mã công ty - mã NCC GC*). Mới có Hà Long |
| **Data NCC GC** | Chính sách TP từng NCC: viết tắt, tên, MST, địa chỉ, **số ngày được lưu kho (TP; VTBB, NL)**, phí lưu kho + chi tiết + ĐVT phí, số ngày SX TP, tình trạng dự trù tại NCC, chính sách nhận hàng tự mang đến, **% hao hụt BTP, chai / túi / can, nhãn, thùng, khác**, MOQ TP, thời điểm xuất hóa đơn, thời gian SX khi đủ VTBB, lượng phối BTP tối thiểu, **cọc nhãn**, cho dự trù VTBB, hình thức giao nhận, nhân sự liên hệ (có SĐT - không chép), lưu ý, đánh giá. Chính sách BTP: NCC, mã NL/BTP, tên, thành phần, dòng công thức, màu, ĐVT, nhận dự trù BTP (146 *Không nhận*, 2 *Nhận*), MOQ + thời gian chuẩn bị, mua NL mang qua (MOQ, thời gian phối), mua BTP mang qua, ghi chú | QLDL nhập tay | QLDL | Ví dụ: Hà Long lưu kho TP 15 ngày, VTBB / NL 60 ngày, có phí theo pallet / m2 / tháng; MOQ 10 thùng (trên 500 kg mới đóng). Yamato không phí lưu kho, dưới 500 L/kg phải chờ ghép đơn |
| **Data QLDL** | 3 khối khai báo mẫu: BTPCT (mã HH, tên HH, tên pháp lý, NCC), PĐG (tên NCC, loại VTBB, **quy cách theo bảng giá NCC**), PPT (NCC, phân / thuốc, tên pháp lý, dòng V, màu) + sổ khai báo: mã, tên, ĐVT, tên pháp lý, dòng, màu, hoạt chất, loại, NCC, **hiện trạng sử dụng**, **trạng thái khai báo**, ngày gửi khai báo, người khai báo | Drive + Misa; tên gộp bằng công thức | QLDL kiểm tra và nhập tay | 785 mã; loại gồm cả *Phí phạt*, *Chiết khấu*, *BTPNL* (chưa có trong quy tắc QT2) |
| **Data TP** | STT, viết tắt NCC, tên NCC, nhóm SP được phép SX, MST, địa chỉ trụ sở, địa chỉ kho, giờ làm việc, thời gian báo trước khi nhận hàng, nhân sự ĐP TP phụ trách | ĐP TP nhập tay | ĐP TP | 15 NCC; tách từ *17. TT NCC GC* |
| **Data HH** | STT, mã HH, tên HH, tên pháp lý | Nhập tay | Thiết kế (Nháp chung) / Admin, ĐP | Trống. Thiết kế khai HH lên Misa qua nhóm *KHAI BÁO SẢN PHẨM* (QT2) |
| *Giá vốn (chỉ có ở Nháp chung)* | Trạng thái giá BTP: **Đang áp dụng / Ngưng áp dụng - có giá mới / Ngưng áp dụng - ngưng SX / Giá mới chưa áp dụng**; phân loại ruột (BTP, TP, công nợ không xác nhận); cung cấp giá - tồn kho; báo cáo kế toán | | GV | Chưa có sheet |
| *Pháp lý NCC GC (Nháp chung)* | Hợp đồng, phụ lục, phụ kiện, hợp quy, MST (mã NCC), viết tắt, tên đầy đủ; các loại phí: **phí thuê tên, phí làm danh mục, phân bổ chi phí** | | Pháp lý SX | *Làm chi tiết sau*; điều kiện cần lưu: ĐK SX, ĐK KD, danh mục sở hữu / ủy quyền, pháp lý SP, hợp đồng / phụ lục / phụ kiện NCC GC, hợp đồng giữa công ty nội bộ |

Danh mục NCC GC đang giao dịch (15, theo 17. TT NCC GC / Data TP / Data NCC GC): Hà Long, Thái Nông, Âu Việt, ADU, Đại Tâm (3 pháp nhân), Agrifuture, Thu Loan, Yamato, Basel, Niềm Tin Việt (NTV), An Nông, Dubai, ATC, Thuận Thành Phát, Pest (Pesticidex). ATC và Pest **không có nhà máy, thuê lại** Dubai / Hà Long / Yamato; kho xuất nhập ghi theo tên NCC, nhập theo công ty xuất hóa đơn. Basel **hết giấy phép SX thuốc BVTV từ T1/2024**, ủy quyền tên cho Dego, Dego phải mua NL/BTP của Basel mang đi đóng.

---

## 4. Pháp lý

### 4.1 Các loại hồ sơ
- **Của NCC GC / công ty**: Giấy CN đăng ký doanh nghiệp (ĐKKD); **Giấy CN đủ điều kiện sản xuất** phân bón / thuốc BVTV (có phạm vi được phép SX, theo dạng: WP, lỏng, rắn...); **Giấy CN đủ điều kiện buôn bán** phân bón / thuốc. Quy định mới ghi ở [PL] Mục lục và sheet 1: **buôn bán phân: bỏ, không đăng ký mới từ 1/7/2026; buôn bán thuốc: sau 1/7/2026 nếu còn hạn thì tự gia hạn**.
- **Của sản phẩm**: Giấy ủy quyền (thuê tên) - số, hiệu lực, hết hạn (có loại *vô hạn*), bên cho thuê (sở hữu), bên nhận thuê, hình thức / phạm vi (độc quyền, theo tỉnh...); Giấy đăng ký thuốc / QĐ công nhận lưu hành phân bón - số, hiệu lực, hết hạn, đơn vị; Giấy CN phù hợp quy chuẩn / kết quả tự đánh giá (**từ 1/7/2026 không cần nữa**); Công bố hợp quy (số, ngày, đơn vị); Thông báo tiếp nhận hồ sơ công bố hợp quy (số, hiệu lực, hết hạn, đơn vị); hồ sơ hỗ trợ quảng cáo (giấy ủy quyền quảng cáo).
- **Hợp đồng**: hợp đồng gia công, mua bán, nguyên tắc, độc quyền, bao tiêu nhãn riêng, phụ kiện điều chỉnh; hợp đồng mua bán giữa các công ty nội bộ + phụ lục hằng tháng; hợp đồng cọc nhãn; biên bản thanh lý; phiếu kiểm soát chất độc; COA.

### 4.2 Trường theo dõi
- *2.1 TRINH ABA / Data pháp lý (Tổng)* (369 dòng, 262 tên pháp lý): STT, phân loại (thuốc BVTV 238, phân bón 118, chế phẩm diệt côn trùng / sinh học 13), tên pháp lý, công thức pháp lý (hoạt chất + hàm lượng), **hiện trạng KD** (Đang KD 242, Chưa KD 57, Ngưng KD 48, Ngưng sử dụng 17, Cập nhật khi có nhu cầu 5), khối ủy quyền (số, hiệu lực, hết hạn, bên cho / nhận, **hình thức sở hữu**: sở hữu 16, thuê tên độc quyền 21, thuê tên đại trà 158, độc quyền phân phối 6, mua hàng thành phẩm 75, nhận ủy quyền từ khách 25, hợp tác SX-GC), khối GĐK / lưu hành, khối GCN phù hợp quy chuẩn, khối công bố hợp quy, khối thông báo tiếp nhận hợp quy, link pháp lý, đơn vị liên hệ thuê, lý do thuê (vd *Basel hết hạn giấy phép SX*), **NCC1 / NCC2 / NCC3 gia công + phân loại sở hữu khi hợp tác với từng NCC** (thứ tự ưu tiên; NCC1 nhiều nhất Hà Long 112, Agama 38, NTV 27, Basel 14...), tình trạng hợp đồng, **hình thức** (tự cấu thành 143 / mua thành phẩm 69).
- **Cảnh báo pháp lý** (tự tính trên từng khối): **CÒN HẠN** còn trên 180 ngày; **SẮP HẾT HẠN** còn dưới 180 ngày; **HẾT HẠN** đến / quá ngày hết hạn. Hiện: ủy quyền hết hạn 38 / sắp hết 6; GĐK hết hạn 43 / sắp hết 28; hợp quy hết hạn 74 / sắp hết 20.
- *1. ĐỦ ĐK SX, BB*: NCC / công ty, loại (sản xuất / buôn bán), nhóm SP (phân / thuốc), dạng, hiệu lực, hết hạn, hiện trạng, số ngày sắp hết hạn, ghi chú.
- *2. SP* (tổng 2.1 + 2.2) và *2.2 NCC GC SH*: cùng cấu trúc rút gọn (ủy quyền, GĐK, thông báo hợp quy + cảnh báo); **nhiều đơn vị nhận ủy quyền thì tách nhiều dòng**; 2.2 do QLDL cập nhật, khi cần dùng thì yêu cầu NCC cung cấp.
- *HỢP ĐỒNG (coppy QLDL)*: số / ký hiệu, tên văn bản, ngày ký, bên A, bên B, (người ký - chức vụ: không chép), nội dung / SP giao dịch kèm đơn giá, **điều kiện giá và thay đổi giá**, **sản lượng cam kết**, khuyến mãi / chiết khấu, công nợ, **hao hụt**, lãi phạt, hóa đơn, thanh toán, kho / bảo quản, **SL tối thiểu SX**, **thời gian tối thiểu SX**, nguyên tắc đóng date, đặt hàng, lưu mẫu, giao nhận, đối chiếu tồn, điều kiện phân phối, bảo mật, xử lý hàng lỗi / phạt / đơn phương chấm dứt, quyền - trách nhiệm hai bên, hiệu lực, hết hạn, trạng thái (*Còn sử dụng / Ngưng sử dụng - đổi hợp đồng*), link file. Ví dụ điều khoản: Hà Long gia công - hao hụt NL tối đa 0,3%, VTBB theo thực tế, SX 7-10 ngày từ khi đủ NVL, NVL thừa / hỏng thu hồi trong 10-15 ngày nếu không bị tiêu hủy; An Nông bao tiêu nhãn riêng - nhận tối thiểu 50 thùng / lần, không đủ sản lượng 12 tháng thì truy thu về giá khung, cọc bao bì theo mẫu, tồn nhãn 2 năm phải thanh toán; An Nông độc quyền - sản lượng tối thiểu 5 năm tăng dần, không đạt phạt 15% giá trị hợp đồng năm.

### 4.3 Điều kiện ngưng
- **Ngưng sử dụng** (một dòng pháp lý): NCC hết pháp lý. **Ngưng KD**: **6 tháng không có đơn hàng / không đóng sản phẩm** (ghi ở dòng tiêu đề sheet 2.1 / Data pháp lý).
- Đơn hàng: thiếu / hết hạn giấy thì **tạm ngưng SX, gia công, mua bán đến khi bổ sung đủ** (QT11, QT12); không kịp thì đổi pháp nhân cấu thành hoặc hủy đơn (ma trận sự cố, trường hợp 6 - Rất cao, ưu tiên 1).
- NCC: QT1 check pháp lý không đạt thì ngưng, tìm NCC khác; đánh giá dưới 60 điểm thì ngưng hợp tác (QT13).
- Gia hạn: QLDL liên hệ NCC **trước 3 tháng** hết hạn; **sản phẩm công ty sở hữu tên: trước 6 tháng** (QT6 C1). Hợp đồng: báo QLSX trước 3 tháng, checklist trước 1 tháng (QT6 C2).

### 4.4 Liên hệ với duyệt đơn hàng
Sheet *4. DUYỆT ĐƠN HÀNG* hiện thực QT5: cột A-Z **chạy từ Drive Điều phối thành phẩm** (mã PO, trạng thái *Mới / Xử lý*, NCC đề xuất, ngày đơn, thương hiệu, mã HH, tên hàng, phân loại, tên pháp lý, đơn vị SX trên nhãn, ĐVT, mã BĐM BTP KD, quy cách thùng, SL thùng / chai, ngày yêu cầu sẵn kho NCC, yêu cầu khác, vật tư khác ngoài chai / túi / nhãn / thùng / NDT, NVL khách mang qua, số ngày SX, đã dự trù nhãn / BTP (mã yêu cầu), trạng thái NCC duyệt nhãn, **giá bán chai / gói thấp nhất theo chính sách bán hàng**, đã khảo sát VTBB). Khối kiểm (AL-AZ, nhập tay dựa sheet 1, 2, 3): **đơn vị sở hữu, đơn vị cấu thành, GĐK còn hạn + ngày hết hạn, hợp quy còn hạn + ngày hết hạn, hợp quy có thuộc đơn vị sở hữu / cấu thành / SX không** (chạy từ sheet 2. SP), đơn vị SX + **đủ ĐK SX**, công ty nhận hóa đơn từ NCC + **đủ ĐK mua / bán**, đơn vị bán cho khách + đủ ĐK, **dòng hóa đơn** (quy ước ghi: *NCC -> đơn vị cấu thành -> đơn vị nhận hóa đơn đầu tiên -> đơn vị xuất hóa đơn cho khách*, ví dụ `Hà Long -> DEGO -> ABA`), **rủi ro phải chấp nhận**. Kết quả (AB-AJ): ngày duyệt, trạng thái duyệt, NSX yêu cầu in, ghi chú, đơn vị NCC bán, công ty cấu thành, công ty nhận hóa đơn, dòng hóa đơn, rủi ro. Dòng hóa đơn quyết định QT6 A5 (bán TP giữa công ty nội bộ, phụ lục tháng) và QT7 (BĐM thuế theo công ty IDA / ABA / DEGO).

### 4.5 Liên hệ với sự cố
Sheet *3. SỰ CỐ* nhận dữ liệu **chạy từ Drive sự cố** và **trả kết quả lại** cho sự cố: ngày bắt đầu, mã đơn sự cố, NCC, công ty, tên pháp lý, sự cố (*Chưa có giấy / Hết hạn / Sai*), chi tiết, hiện trạng (*Hoàn thành / Đang phát sinh*), **mức ảnh hưởng SX** (vd *Duyệt tạm đơn*, *Ngưng đơn hiện tại và kiểm các đơn tiếp theo*), phương án (nhập tay: liên hệ ai, làm gì, kết quả, ngày dự kiến), ngày kết thúc. QT5 bước 2.1 dùng danh sách này để chặn / cảnh báo các đơn có VTBB / NL / BTP liên quan.

---

## 5. Trùng lặp (bỏ trùng khi gộp)

| Bản chép | Bản gốc / cùng nội dung | Mức trùng | Khi gộp |
|---|---|---|---|
| [PL] **DATA 1** | [DRV] **Admin** | 368/368 ô của DATA 1 trùng vị trí + giá trị; Admin thêm 2 cột *Trạng thái sự cố* + định nghĩa | Lấy **Admin** |
| [PL] **2.1 TRINH ABA** | [DRV] **Data pháp lý (Tổng)** | 8.959/8.960 ô trùng (lệch đúng 1 dòng do 2.1 có thêm dòng tiêu đề *Chạy từ pháp lý Trinh...*) | Lấy một bản; gốc thật là Drive *PHÁP LÝ SẢN PHẨM (CHUNG)* của pháp lý ABA |
| [PL] **2. SP** và **2.2 NCC GC SH** | 2 dòng mẫu chép từ 2.1 (ABASBA 50EC) | Dữ liệu mẫu | Bỏ dòng mẫu |
| [PL] **HỢP ĐỒNG (coppy QLDL)** | Drive QLDL *THỐNG KÊ HỢP ĐỒNG* (ngoài nhóm A, thư mục *Drive QLDL (mới)*) | Tự ghi *xây nhưng để QLDL quản lý, chỉ lưu tạm* | Lấy bản QLDL |
| [DRV] **Data TP** + phần *Chính sách TP* của **Data NCC GC** | [QT] **17. TT NCC GC** | Cùng 15 NCC, cùng nhóm cột (Data TP lấy cột nhận diện + giờ làm việc; Data NCC GC lấy chính sách, hao hụt, liên hệ, lưu ý, đánh giá); Mục lục DRV ghi *có điều chỉnh, giữ DATA TP / DATA NCC GC - xong* | Lấy Data NCC GC + Data TP (mới hơn), 17. TT NCC GC coi là bản cũ |
| [QT] **2.1 QT KHAI BÁO MÃ YÊU CẦU ĐẶT** | [QT] **2. QT KHAI BÁO SX** | Khung bước 1-2 chép nguyên, cột người làm không khớp | Chỉ giữ bảng quy tắc mã cuối sheet |
| [QT] **11** và **12** (bước 5 chứng từ thuế / nội bộ) | lẫn nhau | Chép gần nguyên, chỉ đổi người kiểm (ĐP TP / NV XLSC) | Gộp thành một khối chứng từ sự cố |
| [QT] QT8 mục H, I và QT9 mục I, J | lẫn nhau | Khảo sát công nghệ, mẫu cho tặng gần giống | Gộp thành một quy trình khảo sát / mẫu chung |
| [QT] **18. TT SP** | [DRV] Data NCC GC (khối BTP) và Data pháp lý (cột NCC1-3) | Không trùng ô, nhưng cùng trả lời *NCC nào làm SP nào* | Chọn một nguồn (đề xuất Data pháp lý NCC1-3 + Data NCC GC) |
| [DRV] **Nháp chung** | đặc tả của mọi sheet Data* | Không phải dữ liệu | Dùng làm đặc tả trường, không nạp |

---

## 6. Đối chiếu ERP (ƯỚC LƯỢNG)

Ước lượng dựa trên mô-đun có trong mã ERP DEGO (nhánh erp-v2: purchase_request, survey_request, purchase_order, goods_receipt, inventory, payable, payment_request, supplier, contract, product, catalog, purchase_history, customs, cụm *Giá nguyên vật liệu sản xuất* duoc-CR-784) và hiểu biết chung; **chưa kiểm từng màn, chưa đối chiếu trường**.

| Nghiệp vụ SX (nguồn) | ERP đã có tương ứng | Mức | Phần chưa có |
|---|---|---|---|
| Phiếu đề nghị mua hàng hóa dịch vụ của KD / ĐP NL/BTP / ĐP VTBB gửi Thu mua (QT8 C4, QT9 C4) | **YCMH** | Có | Mã yêu cầu theo quy tắc SX (AVTBB..., ABTP...), gắn mã HH dự kiến + kho nhận + mã pháp lý; phản hồi dự trù 4-5 ngày |
| Thu mua báo giá (số lượng, đơn giá, ngày có hàng, thời hạn giá, tên trên hóa đơn) | **YCBG** / báo giá NCC | Có phần lớn | Trường *tên trên hóa đơn*, *thời hạn áp dụng giá* cần kiểm |
| Mua NL / BTP / VTBB qua Thu mua, nhập kho | **ĐMH** + nhận hàng (goods_receipt) + tồn kho (inventory, BQ gia quyền) | Có | Kho theo NCC GC (KHO NCC_ / KHO NCCXL_), tồn tách **NB và Thuế**, trạng thái tồn tạm / lỗi / có thể SX, xuất tạm, chuyển kho giữa NCC, đổ thu, hao hụt, cho tặng |
| Công nợ NCC thu mua, đề nghị thanh toán | **Công nợ** (payable) + **YCTT** | Có | Công nợ NCC GC theo từng đơn TP (BTPCT), hoa hồng chi cuối năm, lãi quá hạn, cấn trừ sự cố, **dự chi ngày 25-28** |
| Danh mục NCC thu mua, đơn vị vận chuyển | **Nhà cung cấp** | Có | Hồ sơ NCC GC đặc thù: chính sách lưu kho, % hao hụt theo nhóm vật tư, MOQ, cọc nhãn, cho dự trù, thời gian SX, đánh giá 100 điểm 6 tháng, trạng thái *Ngưng hợp tác* kèm lý do |
| Hợp đồng NCC | **Hợp đồng** (tab_contract: mã, đối tượng, pháp nhân ký, loại, ngày, trạng thái active / expired / liquidated) | Có khung | ~30 điều khoản chi tiết (sản lượng cam kết, hao hụt, lãi phạt, MOQ SX, thời gian SX...), cảnh báo trước 3 tháng / 1 tháng, phụ lục bán nội bộ hằng tháng |
| Sản phẩm / mã hàng | **Sản phẩm** + catalog (kho, ĐVT, nhóm, thương hiệu) | Có | Bộ quy tắc mã SX (NLNK, NLT, NA, BTPR, BTPM, BTPNK, BTPCT, PPT, PĐG, HH + mã đơn vị xuất hóa đơn I-IX), **bảng đồng bộ mã Dego - mã NCC**, quy đổi mã BTP KD sang SX, luồng *khai báo - duyệt - P TCKT khai Misa* |
| Giá VTBB, định mức bao bì, sổ giá, lịch sử mua | **Giá NVL sản xuất** (sổ giá gộp lịch sử mua + dòng ĐMH, báo giá, ngưỡng giá, **định mức bao bì** tách thành phần part_type / bom_id, màn mô phỏng tác động giá bao bì) | Có, gần với BĐM VTBB + báo cáo *giá min / max 5 lần mua gần nhất* của QT9 | BĐM BTP (trên 1.000 L/kg, hàm lượng / tỷ trọng), BĐM TP (BTP + VTBB + phí đóng gói), bản **thuế** theo từng công ty, mã BĐM theo quy tắc, LSX |
| Tra cứu giá thị trường (hải quan) | **Tra cứu thị trường** | Có | Dùng được cho giá NL nhập khẩu khi khảo sát (QT3) |
| Khảo sát giá vốn, phiếu duyệt giá 3 mức, cảnh báo biên | - | Chưa có | Toàn bộ QT3: GVSX / GVKD, bảng cấu thành giá, trạng thái giá BTP, phiếu duyệt giá (nội bộ, thuế, giá bán), chặn âm biên |
| Đơn đặt hàng TP từ KD, điều phối, gửi đơn NCC GC, tiến độ 16h30, nhận hàng, test mẫu | - | Chưa có | QT4 trọn vẹn (sheet PYC / Pháp lý / Điều phối / Gửi đơn NCC), trạng thái đơn, hủy đơn hai nhánh |
| Duyệt pháp lý đơn, dòng hóa đơn, hồ sơ pháp lý SP, cảnh báo 180 ngày | - (ERP có theo dõi hạn hợp đồng lao động, không phải pháp lý SP) | Chưa có | Danh mục pháp lý SP (ủy quyền, GĐK, hợp quy) + NCC1-3, đủ ĐK SX / BB, sheet duyệt đơn |
| Phối BTP, LSX, phí phối, hao hụt theo hợp đồng | - | Chưa có | QT8 mục F, J |
| Cọc nhãn, khảo sát VTBB theo công nghệ NCC, mẫu cho tặng | - | Chưa có | QT9 D, I, J |
| Sự cố trong / sau SX | - (có ticket chung) | Chưa có chuyên biệt | Ma trận 10 trường hợp, chi phí theo thương hiệu, biên bản cấn trừ |
| Đặt xe Grab, chi phí vận chuyển theo thương hiệu | Đặt xe (vehicle_booking) cho xe công ty | Một phần | Grab app, tạm ứng, phân bổ phí theo thương hiệu |
| NCC mới, ngưng NCC, đánh giá NCC | Chấm điểm NCC thu mua (supplier_scorecard) | Một phần | Checklist NCC GC mới, test mẫu tối đa 2 lần, quy trình ngưng nhiều phòng xác nhận |

---

## 7. Câu hỏi / mâu thuẫn

1. **Số bước bị đổi thành ngày** ở gần như mọi sheet quy trình (2.1 thành 02/01/2026...). Bản gốc trên Google Sheets có thể đúng, bản xlsx tải về thì sai - cần định dạng cột STT là văn bản trước khi dùng làm nguồn.
2. **Thời gian trả kết quả test mâu thuẫn**: QT4 bước 6 ghi *R&D trả kết quả chậm nhất 2 ngày* nhưng cùng ô ghi *test hàm lượng 14 ngày*; QT8 E1 cũng 14 ngày. Cần tách hạn ngoại dạng (1-2 ngày) và hàm lượng (14 ngày).
3. **Quy định pháp lý mới (1/7/2026) chưa vào quy trình**: [PL] ghi buôn bán phân bỏ đăng ký mới, buôn bán thuốc tự gia hạn, GCN phù hợp quy chuẩn không cần nữa; nhưng QT1 (checklist), QT6 C1, QT5 2.3-2.4 và tiêu chí đánh giá (7 điểm hồ sơ) vẫn đòi Giấy đủ ĐK buôn bán thuốc / phân. QT1 cũng tự hỏi checklist BVTV có áp cho NCC ngành khác không.
4. **Ngưỡng hạn pháp lý không thống nhất**: cảnh báo *sắp hết hạn* = dưới 180 ngày; QT6 bổ sung trước 3 tháng (6 tháng nếu công ty sở hữu tên); tiêu chí đánh giá: 7 điểm khi còn từ 6 tháng, 5 điểm khi còn dưới 3 tháng - khoảng 3-6 tháng không có mức điểm.
5. **Hao hụt NCC lệch giữa các nguồn**: Hà Long - 17. TT NCC GC và hợp đồng ghi NL / BTP 0,3%, Data NCC GC ghi *theo thực tế*; Yamato - 17. TT ghi ±2% lỏng / ±3,5% bột, Data NCC GC ghi 0. Nhiều NCC *không thể hiện trong hợp đồng*, trong khi QT8 F3 và QT9 G2 xử lý hao hụt dựa trên *tỷ lệ cho phép theo hợp đồng*; QT9 tự ghi phần thuế cho hao hụt chưa xong.
6. **Thời gian SX Hà Long**: 17. TT ghi 5-7 / 7-10 / 14 ngày tùy ai cấp VTBB, BTP; Data NCC GC ghi 5-7 ngày; hợp đồng nguyên tắc ghi 7-10 ngày từ khi đủ NVL.
7. **MST trùng**: Pest (Pesticidex) và Thuận Thành Phát cùng ghi MST 1801685413 trong *17. TT NCC GC* - có thể chép nhầm; mã NCC = MST theo QT2 nên trùng là lỗi khóa.
8. **Mã đơn hàng không khớp quy tắc**: quy tắc QT2.1 = viết tắt thương hiệu + `TP` + ddmmyy + 2 số. Ở [PL] 4. DUYỆT ĐƠN HÀNG, đơn thương hiệu ABA lại mang mã `ITP...` (I thường là IDA), đơn thương hiệu BAMBOO mang `ITP...`; [PL] 3. SỰ CỐ có mã `ATP059864` không theo định dạng ngày. Bảng quy tắc ghi *dd/mm/yyyy* nhưng ví dụ dùng ddmmyy.
9. **Mã đơn vị xuất hóa đơn** đánh I, II, IV...IX, **thiếu III** - chưa rõ là pháp nhân đã bỏ hay sót.
10. **BTPM dự kiến bỏ năm 2027** nhưng Data QLDL đang có 124 mã BTPM; Data QLDL còn loại *Phí phạt, Chiết khấu, BTPNL* không có trong quy tắc QT2.
11. **QT2.1** chép khung QT2, cột người làm sai loại mã (vd LSX BTP gán Thiết kế); chưa có trong Mục lục; Mục lục ghi QT2 *Cần kiểm tra lại*.
12. **Sheet được Mục lục nhắc nhưng không có trong tệp**: CHECKLIST TRƯỚC KHI DỪNG LÀM VIỆC NCC GC, SƠ ĐỒ SX & MTCV, VẤN ĐỀ SẢN XUẤT, PHÂN BỔ QUYỀN KÝ HỒ SƠ. Tên Mục lục *QUY TRÌNH DUYỆT PHÁP LÝ ĐƠN HÀNG* khác tên sheet *QT PHÁP LÝ SẢN XUẤT*; [PL] Mục lục ghi tiêu đề *THỐNG KÊ HỢP ĐỒNG NCC GC*.
13. **QT5 chỉ duyệt đơn TP**; chưa rõ đơn BTP, đơn xử lý lại, sự cố, mua / khảo sát NL / BTP có qua duyệt pháp lý không (sheet tự đặt câu hỏi).
14. **Vai trò QLDL và QLSX**: QLSX duyệt gần như mọi bước; QT9 tự hỏi *QLDL có tách biệt QLSX không*; QT1 bước 1 ghi *chưa có thời gian tiếp nhận và phản hồi*; nhiều bước để trống thời lượng.
15. **Thu Loan** ở [PL] *1. ĐỦ ĐK SX, BB* ghi đủ ĐK **sản xuất phân bón** (một giấy hết hạn 2024, một giấy hết hạn 01/01/2026 vẫn ghi *Còn hạn*), trong khi 17. TT NCC GC ghi Thu Loan nhóm **thuốc BVTV**. Hiện trạng *Còn hạn* có vẻ không được tính lại theo ngày.
16. **Sheet HỢP ĐỒNG** có hai khối tiêu đề khác cột (khối 2 thêm *Sản phẩm chủ lực*, *Ghi chú*), dòng dữ liệu khối 2 lệch cột (ngày nằm ở cột số hợp đồng). Một hợp đồng ghi thanh toán vào **tài khoản cá nhân** của người bên NCC - rủi ro cần pháp lý xem.
17. **Nguồn dữ liệu chưa chốt**: Data thu mua ghi Thu mua chuyển sang app (ERP) nên chưa biết trích thế nào; Data đồng bộ NCC GC *chưa chốt*, chỉ có Hà Long; Data NLBTP, Data HH trống; 18. TT SP thiếu gần hết cột chính sách.
18. **Drive dự trù**: QT8 ghi chưa chốt Drive *Dự trù KD cập nhật giá* dùng riêng hay gộp *Yêu cầu đặt hàng TP*; 13. LINK DRIVE đã ghi trạng thái *Bỏ* cho Drive này.
19. **Cấp bảo mật**: 15. NHÓM ZALO có 4 cấp (giá vốn, công thức SX, NL mã hóa) và QT3 yêu cầu giữ bảo mật GVSX / GVKD giữa các bộ phận - khi lên ERP cần phân quyền tương ứng (đặc biệt mã `NA` phụ gia mã hóa che tên thật).
20. QT3 còn trỏ tới Drive *5. GIÁ VỐN KINH DOANH NĂM 2024* - có thể đã cũ.
