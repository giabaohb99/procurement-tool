# Nhóm C — Giá vốn, mua NL/BTP/VTBB, công nợ, tồn kho (phòng Sản xuất DEGO Holding)

Nguồn: 9 tệp Excel trong `D:\New folder\thuthapykien\tailieusanxuat\` (4 tệp Drive QL Giá vốn, 4 tệp Drive QLDL (mới), BC VTBB.xlsx). Đọc bằng openpyxl (read_only, data_only; một số sheet đọc thêm công thức). Tổng **119 sheet** đã đọc. Ảnh / hình vẽ: đã mở zip kiểm `xl/drawings/*.xml` của các tệp lớn: không có hình chụp, không có hộp chữ (`<a:t>`), không có tệp `xl/media`; các sheet trống là trống thật. Phần lớn tệp là **xuất từ Google Sheets** (công thức `__xludf.DUMMYFUNCTION`, `FILTER`, `XLOOKUP`), nhiều sheet là **mẫu thiết kế có 2–10 dòng ví dụ**, chưa phải sổ vận hành thật (trừ BC VTBB và vài bảng danh mục).

Viết tắt dùng trong tài liệu nguồn: NL = nguyên liệu, BTP = bán thành phẩm (ruột), BTPCT = BTP cấu thành, TP = thành phẩm, VTBB = vật tư bao bì, NCC GC = nhà cung cấp gia công (nhà máy: Hà Long, Yamato, Đại Tâm, An Nông, Âu Việt, ADU, Agri Future, Basel...), KD = Kinh doanh, ĐP TP / ĐP NL-BTP / ĐP VTBB = điều phối thành phẩm / nguyên liệu-BTP / bao bì, GV = bộ phận Giá vốn (kế toán giá vốn), QLDL = Quản lý dữ liệu, QLSX = Quản lý sản xuất, BDM / BĐM = bảng định mức, LSX = lệnh sản xuất, NDT = nhãn dán thùng, ĐMH = đơn mua hàng Misa, UNC = ủy nhiệm chi, TM = tiền mặt, GVSX / GVKD = giá vốn sản xuất / giá vốn kinh doanh, Dòng V (V1..V5) = dòng công thức kỹ thuật của thuốc.

---

## 1. Bảng kiểm kê

Quy ước cột **Loại**: QT = quy trình / mục lục; HD = hướng dẫn; BM = biểu mẫu nhập liệu; DM = danh mục / master data; BC = báo cáo / tổng hợp tự tính; BT = bản sao (nhận thông tin 100% từ tệp khác); Nháp = trống hoặc bỏ. **Dòng** = số dòng dữ liệu thật (dòng có từ 4 ô trở lên dưới tiêu đề, ước lượng). Cột **Nguồn cột** tóm tắt ghi chú ngay trên tiêu đề của sheet (Nhập tay / Click chọn / Công thức / Lấy từ Misa).

### 1.1. `Drive QL Giá vốn\1. ĐẦU VÀO GIÁ VỐN.xlsx` (26 sheet, 5,4 MB — nặng do sheet DATA 1 kéo định dạng tới 50.500 dòng, dữ liệu thật ~25 dòng)

| Sheet | Loại | Dòng | Nội dung | Nguồn cột |
|---|---|---|---|---|
| Hướng dẫn sử dụng | HD | 23 | Hướng dẫn 23 phân hệ: nhóm chức năng, bộ phận phụ trách, mục đích, đầu vào, thao tác, lưu ý; nguyên tắc dữ liệu, luồng giá vốn 4 bước, quy ước màu tồn kho | — |
| Mục Lục | QT | 23 | Danh sách 23 sheet, loại nghiệp vụ (đều *Nhận thông tin 100%*), nguồn lấy từ tệp nào | — |
| Quản lý nhãn mác | BT | 6 | Danh mục mã HH: thương hiệu, công ty phân phối, pháp nhân xuất HĐ, tên đăng ký, NCC sản xuất, quy cách SP/thùng, chất liệu bao bì, nhãn, thùng, tồn đầu/cuối, tồn tối thiểu, thành phần VTBB (chai, nhãn, túi, thùng, NDT, nắp, hộp), hoạt chất | Lấy từ tệp QUẢN LÝ NHÃN MÁC IDA GROUP |
| Phí Lưu kho NCC GC (Hàng Tháng) | BM | 2 (khung 24 STT) | Sổ chi phí lưu kho / hao hụt / chi phí khác theo NCC: loại công nợ, số chứng từ Misa, mã NCC, ngày ghi nhận, diễn giải, số tiền, số ngày công nợ, hình thức TT, số HĐ, chính sách TT | Nhập tay; nguồn từ tệp 7 |
| ĐIỀU PHỐI | BT | 3 đơn mẫu | Sổ đơn đặt hàng TP (PO) của ĐP TP: NCC đề xuất, mã hàng, SL thùng/chai, ngày yêu cầu sẵn kho, tiến độ (ngày đủ NVL, ngày sản xuất, Lab), cảnh báo trễ, khối số lượng (KD đặt, gửi NCC, NCC sản xuất, xuất HĐ, đã nhận, còn lại), cấu thành nội bộ / thuế | Ghi rõ từng cột: Nhập (*) (mã PO, trạng thái, NCC, SL, ngày) / Công thức (tra tên hàng, phân loại, ĐVT) / Click chọn (mã BDM BTP KD) |
| DUYỆT ĐƠN HÀNG (ĐP TP) | BT | 3 | Duyệt đơn TP qua 7 bộ phận (Pháp lý, Sự cố, NL/BTP, VTBB, QLDL, Giá vốn, QLSX), mỗi bộ phận: ngày duyệt, trạng thái, ghi chú, link drive; cột tổng *ĐỦ ĐIỀU KIỆN NB (7 BP)* | Gần như toàn bộ Công thức (kéo từ drive từng bộ phận); QLSX Nhập |
| 1. DATA 1 (Admin) | DM | ~25 | Master data: phòng ban / thương hiệu viết tắt, pháp nhân (tên, MST, địa chỉ, giám đốc), danh mục kho (mã kho, người nhận, địa chỉ), định nghĩa loại Nhập / Xuất / Tồn, khoản mục chi phí, ĐVT, hình dạng VTBB và NL/BTP, màu, độ trong, phân loại thuốc, dòng V, trạng thái sự cố | Ghi từng cột: Nhập tay / Lấy từ Misa (tên công ty, MST, địa chỉ, mã kho, khoản mục chi phí) |
| Data TP | DM | 16 | Hồ sơ NCC GC thành phẩm: tên viết tắt, tên GCNĐKKD, nhóm SP được phép SX, MST, địa chỉ trụ sở / kho, giờ làm việc, thời gian báo trước khi nhận hàng, nhân sự ĐP TP phụ trách | Nhập tay |
| Data NCC GC | DM | 16 | Chính sách từng NCC GC: số ngày lưu kho miễn phí (TP; VTBB-NL), có / không phí lưu kho + chi tiết, số ngày SX TP, dự trù, % hao hụt (BTP, chai/túi/can, nhãn, thùng, khác), MOQ TP, thời gian xuất HĐ, thời gian SX khi đủ VTBB, SL phối BTP tối thiểu, cọc nhãn, giao nhận, liên hệ, lưu ý, đánh giá ưu / nhược; khối *Chính sách BTP* (NCC nhận dự trù BTP, MOQ, thời gian chuẩn bị, mua NL / BTP mang qua) | Nhập tay |
| Bảng giá NCC GC | BM | 2 (1 mã, 2 lần giá) | Hợp đồng giá gia công: thời gian HĐ, NCC, công ty ký, hiệu lực từ-đến, số lần đổi giá, số HĐ / văn bản (vd Zalo), tình trạng (Đang áp dụng / Ngưng áp dụng - có giá mới), tên pháp lý, quy cách, đơn giá HĐ, MOQ, phí phạt %, điều kiện phạt, NCC chiết khấu %, chiết khấu cho NCC, số ngày công nợ, *Chi tiết cấu thành giá* (Có/không + giá cho Thùng, Chai/túi, Nhãn, NDT, NL, Phí phối, BTP, Phí sang chai đóng gói, Thành phẩm) | Data NCC / Click chọn tình trạng / Data pháp lý / Data ĐVT / Nhập tay; cột Đơn giá = công thức |
| BDM TP | BT | 9 (1 mã HH, 6 vật tư) | Bảng định mức TP: mã đơn đầu tiên phát sinh BDM, mã hàng, tên pháp lý, thể tích quy đổi, quy cách thùng/hộp, cấu thành nội bộ, chi tiết định mức (Chai, Nắp, Nhãn, NDT, Thùng, Cốc...), mã vật tư, ĐVT, *chi tiết sử dụng / 1 TP*, mã BĐM VTBB, mã BTP ruột, mã BĐM TP, duyệt BĐM + ngày duyệt | Nhập (mã đơn) / còn lại Lấy từ sheet 1.1, 1.3, 1.4 (tệp 4. BDM thành phẩm) / Chọn (duyệt) |
| CP khác từ NCC GC | BC | 7 | Chiết khấu và phí phạt theo từng LSX (hiện áp cho An Nông): SL TP, đơn giá công nợ NCC, chính sách CK, thành tiền CK, phí phạt dự trù, thành tiền phạt, tổng chi phí | Lấy từ sheet 1.2.1 nhập kho DR.XANH; giá / CK / phạt lấy từ sheet *6. Chính sách NCC*; Công thức |
| LSX TP | BT | 9 | Lệnh sản xuất TP theo định mức: vật tư, SL xuất kho VTBB (nội bộ), SL xuất BTP ruột, số hóa đơn | Nhập (mã đơn) / Công thức |
| Phí phối NCC GC | BM | 1 (khung 52) | Phí phối trộn NL thành BTP: NCC, tên pháp lý, dòng V, màu, ĐVT, phí phối, ngày áp dụng / hết hạn, trạng thái, số ngày công nợ; ghi chú *Đề xuất tách drive riêng* | Nhập tay |
| Phí đóng gói NCC GC | BM | ~36 (7 có giá) | Biểu phí sang chai, đóng gói, màng co, tấm lót thùng theo khoảng thể tích (5–15 ml, 16–25 ml...), mã PĐG, giá chưa VAT, VAT, giá đã VAT, hiệu lực, trạng thái, công nợ | Nhập tay |
| Điều phối ĐH NLBTP | BT | 3 | Đơn mua / phối NL-BTP: phân loại (MUA NL / MUA BTP / PHỐI BTP), NCC, kho nhập, SL cần, ngày cần, mã yêu cầu khảo sát, giá yêu cầu, ngày dự kiến bán hết; phần ĐP NL/BTP trả lời (SL gửi mua, ngày NCC có hàng, nhập kho 3 lần, trạng thái, Lab, số lô, NSX, HSD, cấu thành nội bộ / thuế); khối duyệt 5 bộ phận | Khối 1 *YC KD*, khối 2–3 *ĐP NL/BTP* |
| Khảo sát NLBTPVTBB KD | BT | 4 | Phiếu yêu cầu khảo sát giá dùng chung NL/BTP/VTBB (mã YCKS) | KD nhập; nguồn tệp 3 |
| Thông tin trả kết quả NLBTP KD | BT | 0 (khung) | Phiếu GV trả kết quả khảo sát cho KD | Nguồn tệp 3 / 4 |
| Giá Nhập kho NLBTP | BM | 7 | Sổ nhập kho NL/BTP theo lô: số phiếu YC, ngày, phân loại nhập, kho, thương hiệu, mã NL/BTP nội bộ, tên pháp lý, dòng V SX / KD, màu, LAB TEST, hàm lượng thực tế, lượng nhập, **giá NL/BTP**, thành tiền, số lô, NSX, HSD, số CAS, đơn vị nhận HĐ, nhân sự, tài xế, số xe | Nhập / Click / Công thức; cột giá ghi *Giá vốn sản xuất* |
| Tồn kho chi tiết BTP SX | BC | 10 | Tồn BTP theo kho × mã × lô: nhập, xuất, tồn, đơn giá, giá trị tồn, trạng thái (Sử dụng được / Không), đơn hàng đang treo, SL treo, ngày xuất cuối, cảnh báo ngày không giao dịch, Min | Click (kho) / Công thức |
| Tồn kho tổng BTP SX | BC | 2 | Cân đối: nhập, xuất thực tế, xuất, tồn, xuất tạm, đơn chờ xuất, còn thiếu | Công thức |
| Trang tính24 | Nháp | 0 | Trống | — |
| Thông tin trả kết quả VTBB KD | Nháp | 0 | Trống (Mục Lục trỏ tới tệp 4. XUẤT NHẬP TỒN - VTBB) | — |
| Giá Nhập kho VTBB | BM | 9 | Sổ nhập kho VTBB: ngày, phân loại nhập, kho, thương hiệu, mã VTBB, lượng nhập, mã ĐMH Misa, đơn vị nhận HĐ, số / tên HĐ, ảnh phiếu nhập kho NCC GC, mã đơn KD, **giá đã gồm VAT và vận chuyển**, NCC, ngày thu mua, nhân sự yêu cầu | Nhập / Chọn / Công thức / Link; *phải có mã đơn Misa mới trích được giá* |
| Tồn kho chi tiết VTBB SX | BC | 10 | Cùng cấu trúc Tồn kho chi tiết BTP (tiêu đề cột vẫn ghi NL/BTP, dữ liệu mẫu cũng là BTP) | Công thức |
| Tồn kho tổng VTBB SX | BC | 2 | Cân đối VTBB như bản BTP | Công thức |

### 1.2. `Drive QL Giá vốn\2. DUYỆT ĐƠN HÀNG BTP VÀ TP (GV).xlsx` (16 sheet)

| Sheet | Loại | Dòng | Nội dung | Nguồn cột |
|---|---|---|---|---|
| Mục Lục | QT | 14 | 14 sheet; 4 sheet *Thực hiện* (Chi tiết giá TP, Tổng hợp giá TP, Mẫu duyệt giá TP, Mẫu duyệt giá NL/BTP), còn lại nhận từ tệp 1 | — |
| Quản lý nhãn mác, ĐIỀU PHỐI, DUYỆT ĐƠN HÀNG (ĐP TP), BDM TP, LSX TP, Giá Nhập kho VTBB, Giá Nhập kho NLBTP, Bảng giá NCC GC, Phí đóng gói NCC GC | BT | như tệp 1 | Bản sao từ tệp 1 (*Nhận thông tin 100%*); bình luận ô: *HÀNG CHIẾT KHẤU không cần in phí phạt với chiết khấu* | Như tệp 1 |
| Chi tiết giá TP SX-KD (dự kiến và thực tế) | BM | 8 (1 mã, 7 thành phần) | Bảng tính giá TP theo từng thành phần định mức: hai khối *Giá duyệt gửi đơn* (dự kiến) và *Giá duyệt theo đơn hàng* (thực tế), mỗi khối có mã BĐM QLDL, chi tiết định mức (Chai/Xô/Can/Bao → Nắp → Nhãn/Túi → Hộp → Thùng → NDT → BTPCT), phân loại NCC / CTY, mã vật tư, định mức / TP, dòng V áp cho KD, lần cập nhật giá, **đơn giá SX, giá SX theo 1 TP, thành tiền GVSX, đơn giá KD, giá KD theo 1 TP, thành tiền GVKD**; chênh lệch giá tạm - giá duyệt (SX, KD); người / ngày duyệt; chính sách công nợ; khuyến mãi | Công thức (tên thành phần tự xoay vòng); cột giá phần lớn còn trống |
| Tổng hợp giá TP SX-KD (dự kiến và thực tế) | BC | 3 | Mỗi đơn × mã một dòng: giá TP KD, giá TP SX, giá bán KH, biên vốn KD - SX, tổng thành tiền KD - SX, biên KH - KD, tổng thành tiền KH - KD; trạng thái duyệt (Duyệt / Chưa đủ TT duyệt); khối dự kiến và khối thực tế | CT (công thức) / Nhập tay (mã đơn, ngày cập nhật, ghi chú) / ngày + trạng thái duyệt nhập tay chạy qua Duyệt đơn hàng cột CB–CD |
| Mẫu duyệt giá TP | BM (phiếu in) | khung | PHIẾU DUYỆT ĐƠN HÀNG & GIÁ THÀNH PHẨM: thông tin chung, 12 đầu mục từ KD, bảng tổng hợp giá (GVSX, GVKD), thông tin phê duyệt, chữ ký 3 bên | Điền tay |
| Điều phối ĐH NLBTP | BT | 3 | Như tệp 1; ghi *Nhận thông tin từ cột A → BZ, Thực hiện từ cột CA → CD* (khối 4. GIÁ VỐN: ngày duyệt, trạng thái, **giá đã chốt với KD theo ĐVT**, ghi chú) | GV nhập khối CA–CD |
| Mẫu duyệt giá NLBTP | BM (phiếu in) | khung | PHIẾU ĐỀ XUẤT VÀ DUYỆT GIÁ BTP: thông tin chung (mã BTP nội bộ / thuế, Mua / Phối), yêu cầu KD, bảng chi phí BTP, so sánh giá, điều kiện giá, phê duyệt | Điền tay |
| Thông tin trả kết quả NLBTP KD | BT | 0 | Khung như tệp 1 | — |

### 1.3. `Drive QL Giá vốn\3. KD CHÍNH SÁCH NCC GC – KHẢO SÁT GIÁ – ĐẶT HÀNG NL_BTP_VTBB.xlsx` (17 sheet — sổ phía Kinh doanh)

| Sheet | Loại | Dòng | Nội dung | Nguồn cột |
|---|---|---|---|---|
| Mục Lục | QT | 12 | 7 sheet chính; 4 sheet *KD thực hiện*, 3 sheet nhận từ tệp 1 | — |
| BTP, VTBB, Pháp Lý, Trang tính26 | Nháp | 0 | Trống | — |
| Phân tích TP (Nhu cầu BTPVTBB) | BM | 3 | KD nhập đơn TP + định mức → tự tính SL BTP, chai/túi, nhãn, nhãn thùng, thùng (có hao hụt) | Dòng hướng dẫn từng cột: KD nhập / Click chọn / Mặc định 0% - 2% - 1 / Tự động tính |
| Khảo sát NLBTPVTBB KD | BM | 5 | Phiếu YC khảo sát giá (mã YCKS, thương hiệu, phân loại NL/BTP/VTBB, NCC nhập kho, mã, tên, dòng V / thông số, dạng màu, ĐVT, SL cần khảo sát, giá đề xuất, ngày cần báo giá, ngày cần hàng, thời gian dự kiến dùng, quy cách thùng/hộp/chai, hình ảnh VTBB, tiến độ chung) | KD nhập / Click chọn; tiến độ chạy từ sheet trả KQ; 3 cột *Có thể bỏ (hỏi lại QLDL)* |
| Thông tin trả kết quả NLBTPVTBB | BT | 0 | Khung trả KQ (nguồn tệp 1) | — |
| YC mua NLBTP | BM | 2 | KD lên yêu cầu mua NL/BTP (cùng cột Điều phối ĐH NLBTP); phần ĐP NL/BTP trả kết quả chạy qua | Dòng hướng dẫn từng cột (KD nhập / Click chọn) |
| YC mua VTBB | BM | 0 (khung) | KD lên yêu cầu mua VTBB: mã YC, kho nhận, mã / tên VTBB, SL, ngày cần, tháng sử dụng, mục đích, mã HH cần dùng, yêu cầu khác; phần ĐP VTBB trả (NCC, SL gửi mua, kho, ngày có hàng, 3 lần nhập, trạng thái) | KD nhập / Click chọn |
| Thông tin NCC GC | BT | 16 | Bản sao Data TP (tệp 1) | — |
| Chính sách BTP và TP NCC GC | BT | 16 | Bản sao Data NCC GC (tệp 1) | — |
| Tồn kho chi tiết / tổng BTP SX, VTBB SX (4 sheet) | BT | 10 / 2 | Bản sao từ tệp 1 | — |
| Phí Lưu kho NCC GC (Hàng Tháng) | BT | 2 | Bản sao từ tệp 1 | — |

### 1.4. `Drive QL Giá vốn\4. KHẢO SÁT GV - CÔNG VIỆC CẦN THỰC HIỆN.xlsx` (8 sheet — sổ phía Giá vốn)

| Sheet | Loại | Dòng | Nội dung | Nguồn cột |
|---|---|---|---|---|
| Mục Lục | QT | 3 | 3 dòng có nghĩa (Khảo sát KD nhận; 2 sheet phân tách *Thực hiện*), 15 dòng trỏ link trùng | — |
| Khảo sát NLBTPVTBB KD | BT | 8 | Bản sao phiếu khảo sát của KD (tệp 3) | — |
| Khảo sát NLBTP (Phân tách từ KD) | BC | 6 | Trích tự động phiếu khảo sát có phân loại NL/BTP; mỗi cột ưu tiên giá trị đã chuẩn hóa của QLDL, trống thì lấy của KD; trạng thái kiểm tra QLDL + ghi chú (vd *Điều chỉnh SL chốt lên 450 kg theo hao hụt mẻ*) | Ghi từng cột: Lấy từ cột X (KD) / Ưu tiên cột QLDL |
| Khảo sát VTBB (Phân tách từ KD) | BC | 3 | Như trên cho VTBB (thêm hình ảnh) | Như trên |
| Thông tin trả kết quả NLBTP KD | BM | 4 | GV trả KQ: mã, tên, SL mua, giá, ngày công nợ, NCC, MOQ, thời gian có hàng, thời gian giữ giá, VAT, phí vận chuyển, xuất xứ, nơi giao, kết quả lab, thông số, ảnh, đánh giá, nhân sự, **duyệt của BP yêu cầu** (Kết thúc khảo sát / Yêu cầu khảo sát thêm); khối 2 *kiểm tra lại và bổ sung* (được phép sửa): mã KD, tên, dòng V, dạng màu, ĐVT, SL khảo sát, **giá chốt báo KD**, trạng thái | Nhập tay |
| Thông tin trả kết quả VTBB KD | BM | 4 | Như trên cho VTBB | Nhập tay |
| Tổng hợp thông tin trả kết quả | BC | 8 | Gộp tự động 2 sheet trả KQ, gán nhãn nguồn NL/BTP hay VTBB | Công thức |
| Trang tính8 | Nháp | 0 | Trống | — |

### 1.5. `Drive QLDL (mới)\5. Theo dõi mua NL_BTP_VTBB (QLDL).xlsx` (4 sheet)

| Sheet | Loại | Dòng | Nội dung | Nguồn cột |
|---|---|---|---|---|
| Mục lục | QT | 3 | 3 sheet: tiến độ mua + lab + vận chuyển; phiếu chuyển kho; PO gửi NCC | — |
| Tiến độ mua, trả hàng | BM | 4 | Sổ mua VTBB/NL: ngày tiếp nhận, ngày yêu cầu có hàng, ngày dự kiến / thực nhận, người đặt, pháp lý lấy HĐ, NSPT, NCC, **mã đơn Misa (ĐMH)**, mã / tên, tên trên HĐ, trạng thái, kho nhận, SL đặt / đã nhận, đơn giá, VAT, thành tiền, số HĐ, số lần nhận, số ngày có hàng theo quy định, chênh lệch ngày, công nợ SP, vận chuyển (đơn vị, SL kiện, đơn giá, thành tiền, công nợ), Lab, khối đổi trả (phương án Trả / Đổi, lý do, tiến độ, ngày thực trả) | Nhập tay + Công thức; tra cứu tới sheet *1. DATA CHUNG*, *2. DATA NL, VTBB* (không có trong tệp — vỡ liên kết `#REF!`) |
| Phiếu chuyển kho | BM (phiếu in) | 3 | PHIẾU ĐỀ NGHỊ CHUYỂN KHO: người đề nghị, bộ phận, kho xuất, kho nhập, dòng hàng (SL yêu cầu / thực xuất, đơn giá, thành tiền) | Điền tay |
| PO | BM (phiếu in) | 2 | ĐƠN ĐẶT HÀNG gửi NCC (công ty DEGO HOLDING): mã đơn Misa, dòng hàng (mã, tên, thông số, ĐVT, SL, đơn giá chưa / đã VAT, thành tiền, kho nhận, tên trên HĐ), thỏa thuận (công nợ, hạn nhận HĐ *chậm nhất 24h kể từ khi nhận hàng*, giao nhận, thông tin nhận HĐ), file đính kèm; luật *mỗi 1 đơn mua hàng: 1 công ty nhận hóa đơn* | Điền tay + Công thức |

### 1.6. `Drive QLDL (mới)\6. Ghi nhận Công Nợ, Chi Phí và Hoá Đơn.xlsx` (13 sheet)

| Sheet | Loại | Dòng | Nội dung | Nguồn cột |
|---|---|---|---|---|
| Mục Lục | QT | 11 | 11 quy trình công nợ / hóa đơn, cột *Xử lý* hay *Nhận thông tin*, nguồn | — |
| NHẬP-XUẤT TP | BT | 7 | Nhập / xuất / chuyển / trả TP: ngày, số phiếu, PO, trạng thái đơn (Hàng mới / Hàng xử lý), kho xuất / nhận, trạng thái (1.NHẬP TP, 2.NHẬP MẪU...), mã HH, SL thùng / chai, mã lô, số HĐ, NSX, HSD, HSD còn lại, Lab, biển số, tài xế | Chạy từ tệp *2. Đầu vào nội bộ QLDL*; Nhập / Công thức |
| Công nợ TP đóng gói | BT + BM | 18 | Giá NCC GC gửi theo đơn (chuỗi gốc từ NCC: mã SP, SL × đơn giá = thành tiền) đối chiếu **giá bên mình tính** = đơn giá ruột + đóng gói + phí khác 1-3 + làm tròn; cột *Check đơn giá + mã HH* (Khớp); khối công nợ nhập tay (loại CN, chứng từ Misa, số ngày CN, hình thức TT, số HĐ, chính sách) | Cột A–Y chạy từ tệp *4. BDM thành phẩm*; AB–AF Nhập tay |
| CN (Thành phẩm - Phí đóng gói) | BM | 1 | Công nợ TP + phí đóng gói: ngày sẵn kho, loại CN, phiếu, NCC, mã HH, cấu thành nội bộ / thuế, loại HĐ cần lấy (Phí đóng gói / Thành phẩm / BTP + Phí gia công / Công nợ không xác định), công ty xuất / nhận HĐ, số HĐ, SL, đơn giá, VAT, ngày nhận HĐ, trạng thái lấy HĐ, dòng hóa đơn, xác nhận trưởng BP | Nhập tay |
| Trang tính21 | Nháp | 4 | GIẤY ĐỀ NGHỊ NHẬP KHO, toàn `#REF!` | — |
| CN Phí phối | BM | 0 (khung) | Công nợ phí phối trộn: chứng từ Misa, NCC, mã SP, màu, dòng công thức, số lô, SL, đơn giá chưa VAT, VAT %, có VAT, thành tiền, số ngày CN, hình thức TT, số HĐ, tên trên HĐ | Nhập tay |
| Theo dõi hiện trạng hoá đơn | BM | 5 | Theo dõi lấy HĐ theo SL: loại CN, mã đơn / mã YC phối / mã sự cố, NCC, mã, SL mua / phát sinh, SL đã lấy HĐ, SL còn lại, số HĐ, tiến độ, deadline | Nhập tay + Công thức |
| TỔNG HỢP CÔNG NỢ NCC | BC | 2 | Gộp các loại công nợ: loại, chứng từ Misa, NCC, ngày ghi nhận, số tiền (**dương = trả NCC, âm = thu NCC**), số ngày CN, hình thức TT, số HĐ, chính sách | Dự kiến công thức gộp (hiện mẫu) |
| CN XLSC | BM | 6 | Công nợ xử lý sự cố: mã sự cố, mã hàng, phương án kết luận, kết quả, tổng tiền phát sinh, BP chịu chi phí, phân bổ tiền theo BP, loại chi phí (vận chuyển, kiểm mẫu...), hình thức thu (cấn trừ công nợ / hạch toán chi phí / thu tiền), trạng thái, link xác nhận (biên bản có chữ ký NCC, phiếu thu / UNC) | Nhập tay |
| Chi Phí hao hụt- lưu kho-CP khác | BM | 2 | Như sheet Phí Lưu kho tệp 1 | Nhập tay |
| CN chiết khấu và phí phạt NCC | BT + BM | 6 | Như *CP khác từ NCC GC* tệp 1 + khối công nợ nhập tay | Công thức + Nhập tay |
| CN VTBB, NL, BTP | BT | 5 | Bản sao *Tiến độ mua, trả hàng* tệp 5 + 3 cột công nợ | Nguồn tệp 5 |
| Form in YC xuất HĐ NCC | BM (phiếu in) | 0 (toàn `#N/A`) | DANH SÁCH NHẬN HÓA ĐƠN theo chuỗi (vd Hà Long → DEGO): nội dung HĐ, ĐVT, SL, đơn giá chưa VAT, thành tiền, thuế suất 5%, tổng | Công thức (đang lỗi) |

### 1.7. `Drive QLDL (mới)\7. Đối chiếu tồn kho.xlsx` (14 sheet)

| Sheet | Loại | Dòng | Nội dung | Nguồn cột |
|---|---|---|---|---|
| Mục Lục | QT | 11 | 11 sheet, chức năng từng sheet | — |
| Tồn kho từ NCC GC | BT | 59 | Tồn do NCC GC báo (mã vật tư theo mã của NCC, tên, ĐVT, SL, nhóm); ghi chú *mỗi NCC GC có mẫu tồn kho khác nhau không chung form* | Chạy từ tệp *1. ĐẦU VÀO NCC GC* |
| Đối chiếu tồn kho VTBB / BTP / TP / hàng lỗi (4 sheet) | BC | 4 mỗi sheet | Cùng một khung: ngày GD, NCC GC, kho, mã, tên, ĐVT, giao dịch trong kỳ theo NCC (G) và theo hệ thống (H), lệch SL (H − G), tồn NCC báo (J), tồn hệ thống (K), lệch tồn (K − J), kết luận tự động (vd *Không tìm thấy Mã+Kho trong TỒN KHO*, *Thiếu Kho*) | Công thức; dữ liệu mẫu giống hệt nhau ở cả 4 sheet |
| Tổng hợp kết quả đối chiếu tồn kho | BC | 4 | Gộp 4 loại | Công thức |
| So sánh các lần đối chiếu (tồn) | BC | 0 (khung) | Lần gần nhất vs lần trước: tồn cuối, dư cuối, ngày kiểm tồn tại NCC, số lần gửi, chênh lệch | NCC / Nhập |
| Lịch sử đối chiếu (tồn kho) | BM | 4 | Lưu từng kỳ + hướng điều chỉnh NCC GC, nguyên nhân, trạng thái xử lý chênh lệch | Nhập tay |
| Phí lưu kho và hao hụt NCC GC / nội bộ (2 sheet) | BM | 2 mỗi sheet | Hai sổ giống khung Phí Lưu kho: bên NCC báo và bên mình ghi | Nhập tay |
| Đối chiếu phí lưu kho và hao hụt NCC | BC | 3 | 3 khối: dữ liệu nội bộ (có **ngày đến hạn TT tự động** = ngày ghi nhận + số ngày CN), dữ liệu NCC (ngày chứng từ, số HĐ, số tiền), kết quả (chênh lệch NB − NCC, khớp HĐ, tình trạng hạn TT *Quá hạn (n ngày)* / *Trong hạn*, trạng thái *Khớp hoàn toàn* / *Lệch số tiền* / *Thiếu bên NCC*, nguyên nhân và hướng xử lý) | Nhập + Công thức |
| So sánh các lần đối chiếu (LK - HH) | BC | 0 | Khung so sánh kỳ | — |
| Lịch sử đối chiếu (LK-HH) | BM | 4 | Khung chép từ lịch sử tồn kho (dữ liệu mẫu là VTBB, chưa đúng chủ đề) | Nhập tay |

### 1.8. `Drive QLDL (mới)\8. Đối chiếu công nợ NCC, thanh toán và dự chi (QLDL).xlsx` (11 sheet, 1 sheet ẩn)

| Sheet | Loại | Dòng | Nội dung | Nguồn cột |
|---|---|---|---|---|
| Mục Lục | QT | 11 | 12 quy trình, có 2 dòng *Xem lại Ms Huỳnh cần gì chưa rõ* (BC dự chi theo tháng, Tổng hợp thanh toán) | — |
| TỔNG HỢP CÔNG NỢ NCC (NỘI BỘ) | BT | 2 | Chạy từ tệp 6 sheet TỔNG HỢP CÔNG NỢ NCC | — |
| CÔNG NỢ MISA | BT | 2 | Xuất Misa *Chi tiết công nợ phải trả*, TK 331, theo kỳ: ngày hạch toán, số chứng từ, NCC, diễn giải, mã hàng, TK đối ứng, SL, đơn giá, phát sinh Nợ / Có, số dư Nợ / Có, số HĐ, ngày HĐ | Lấy từ Misa |
| ĐỐI CHIẾU CÔNG NỢ DRIVE/APP VÀ MISA | BC | 4 | Theo số chứng từ Misa: bên Drive/App (số HĐ, số tiền, ngày TT) vs bên Misa; khớp số HĐ, chênh lệch tiền, khớp ngày TT, tình trạng chung, nguyên nhân, hướng xử lý, người xử lý, deadline | Sheet công nợ NCC / sheet Misa / Công thức / Nhập tay (nguyên nhân, hướng xử lý, người, ghi chú) |
| CÔNG NỢ NCC GC GỬI | BT | 24 | Sổ chi tiết công nợ do NCC gửi (vd Hà Long: TK 131 phải thu, khách hàng IDA Global, theo tháng: chứng từ, diễn giải từng dòng hàng, SL, giá, tiền) | Từ tệp *1. ĐẦU VÀO NCC GC* |
| ĐỐI CHIẾU CÔNG NỢ NCC GC VÀ MISA | BC | 4 | Như trên nhưng NCC gửi vs Misa; ghi *Misa làm gốc* | Như trên |
| So sánh các lần đối chiếu | BC | 0 | Khung so sánh kỳ (tiêu đề vẫn là mã vật tư / tồn cuối — chép từ tệp 7) | — |
| Lịch sử đối chiếu | BM | 4 | Khung chép từ tệp 7 (dữ liệu mẫu tồn kho VTBB) | — |
| Dự chi NCC | BM | 1 | Kế hoạch chi theo tháng: người đề nghị, chứng từ Misa, loại CN, ngày ghi nhận (có thể *Dự kiến cuối tháng*), NCC, số HĐ, số tiền, chính sách, hình thức, số ngày CN, thương hiệu yêu cầu mua, công ty nhận HĐ, **ngày đến hạn**, đánh giá rủi ro nếu không trả đúng hạn (lãi, bị ngưng đơn), ngày chậm nhất phải trả (deal lại với NCC), đã trả, còn lại | C–L lấy từ đối chiếu NCC - Misa; Q–S nhập khi kế toán không trả đúng hạn; T chạy từ Chi tiết thanh toán |
| Chi tiết thanh toán | BM | 6 | Từng lần thanh toán: chứng từ Misa, NCC, số HĐ, số tiền CN, chính sách, công ty thanh toán, ngày lập / gửi hồ sơ TT, nội dung, tổng đã TT, số lần TT, còn lại, ngày TT, tình trạng, **số ngày quá hạn, lãi suất %/tháng, tiền lãi, lãi đã / chưa TT, tổng còn lại**, trạng thái HĐ, deadline, ảnh UNC | C–L lấy từ đối chiếu; O–AF Nhập tay |
| Tổng hợp thanh toán (ẩn) | BC | 1 | Theo mã hồ sơ: tổng CN ban đầu, đã TT gốc, còn gốc, số lần TT, tổng lãi, đã TT lãi, còn lãi, tổng còn phải TT, tình trạng (ĐANG THANH TOÁN...) | Công thức (dự kiến) |

### 1.9. `BC VTBB.xlsx` (10 sheet — báo cáo tự động VTBB, sổ có dữ liệu thật nhất)

| Sheet | Loại | Dòng | Nội dung | Nguồn cột |
|---|---|---|---|---|
| HƯỚNG DẪN | HD | 25 dòng chữ | Sơ đồ (người dùng chỉ cập nhật 4 sheet; hệ thống tự tính 5 sheet), quy trình hàng tháng 5 bước (~2 phút), mô tả báo cáo, **quy ước tính** (tồn thực tế / tạm / lỗi, nhập đầu kỳ, chuyển kho, giá trị, chi phí lưu kho, hao hụt, loại VTBB, NCC, dung lượng) | — |
| DASHBOARD | BC | ~61 | Ô cấu hình (năm báo cáo, kỳ từ - đến, % chi phí lưu kho, ngưỡng tồn lâu, ngưỡng vượt nhu cầu, ngưỡng luân chuyển nhanh / chậm, chế độ đơn giá); KIỂM TRA DỮ LIỆU (số dòng, phân loại chưa khai báo, mã ngoài danh mục, thiếu ngày, chênh lệch dashboard - báo cáo tháng); A. KPI; B. tồn theo loại; C. theo thương hiệu; D. theo kho; E. tuổi tồn; F. top 10 tồn lâu; 2 biểu đồ | Ô vàng nhập tay, còn lại công thức |
| BÁO CÁO THÁNG | BC | 200 | T1–T12 + cả năm: A1–A8 theo loại VTBB (nhập, xuất thực tế, tồn cuối tháng, chi phí lưu kho, tỷ lệ hao hụt, giá trị hao hụt, hàng lỗi nhập, tỷ lệ lỗi nhập), B theo thương hiệu, C theo kho, D theo NCC VTBB (gồm tỷ lệ lỗi nhập để đánh giá NCC), E so cùng kỳ năm trước, F toàn nhà máy | Công thức |
| BÁO CÁO QUÝ | BC | 200 | Như tháng, cộng theo quý | Công thức |
| TỔNG HỢP TÙY CHỌN | BC | 46 | Chọn từ ngày - đến ngày, lọc kho / thương hiệu / loại → bảng theo loại, theo thương hiệu (tồn đầu, nhập, xuất, hao hụt, nhập lỗi, tồn cuối, tỷ lệ, chi phí lưu kho / tháng) | Ô vàng chọn, còn lại công thức |
| XNT VTBB | BC | 2.173 | Xuất nhập tồn theo khóa kho × thương hiệu × mã: đơn giá, đầu kỳ, nhập, xuất, tồn TT, tồn tạm, tồn lỗi, tồn có thể SX, giá trị tồn, ngày nhập / xuất cuối, số ngày tồn, tồn lâu, nhóm luân chuyển, xuất 90 ngày, xuất TB / ngày, ngày đủ dùng, vượt nhu cầu, Min, MOQ, SL đang đặt, dưới Min, **SL đề xuất đặt**, tồn âm, chi phí lưu kho / tháng và lũy kế, thiếu đơn giá | Công thức (tự sinh, không nhập tay) |
| GIAO DỊCH VTBB | BM (dán dữ liệu) | 2.226 | Mọi giao dịch: ngày, sheet nguồn (NHẬP KHO VTBB / XUẤT KHO VTBB SX), loại GD, phân loại, kho, thương hiệu, mã, tên, ĐVT, SL (A–J dán giá trị); L trở đi cột xám tự tính (chiều, nhóm tồn, hao hụt, loại, đơn giá, giá trị, kỳ yyyymm, khóa) | A–J dán từ *file hệ thống quản lý kho → sheet LỊCH SỬ*; còn lại công thức |
| DANH MỤC VTBB | DM | ~6.158 mã | Mã, tên, ĐVT, giá Min, giá Max (từ DATA 1), đơn giá nhập tay (ưu tiên), loại ghi đè, NCC VTBB nhập tay, loại dùng, đơn giá dùng | A–E dán; F–H nhập tay; I–J công thức |
| MIN MOQ | BM | 12 | Theo mã + kho: Min (tồn an toàn), MOQ (đặt tối thiểu), NCC phụ trách, SL đang đặt chưa về, ghi chú (vd số hợp đồng) | Ô vàng nhập tay (ghi nguồn *sheet THÔNG TIN khối 1*) |
| CẤU HÌNH | DM | 32 | Loại VTBB + định mức hao hụt % + ngưỡng tồn lâu riêng; bảng tiền tố mã 3 ký tự → loại; bảng phân loại giao dịch (chiều ±1, nhóm tồn Thực tế / Tạm / Lỗi, nhóm báo cáo Nhập / Xuất / Đầu kỳ / Chuyển kho, cờ hao hụt); danh sách thương hiệu, kho (20 hiển thị), NCC VTBB (24 hiển thị), danh sách lọc | Ô vàng nhập tay |

---

## 2. Quy trình con

### (a) Đầu vào và cách tính giá vốn

**Mục đích.** Gom đủ tham số để tính giá vốn một đơn TP gia công: giá BTP / NL, giá VTBB, phí gia công (phối, sang chai, đóng gói), chi phí khác, chiết khấu / phạt, theo đúng định mức của mã hàng. Sổ chính: tệp 1 (đầu vào) và tệp 2 (tính + duyệt).

**Luồng chuẩn (theo Hướng dẫn tệp 1).**
1. Khởi tạo danh mục Admin, đối tác NCC GC, chính sách và biểu phí gia công (DATA 1, Data TP, Data NCC GC, Bảng giá NCC GC, Phí phối, Phí đóng gói).
2. Tiếp nhận đơn (ĐIỀU PHỐI) → kiểm soát và duyệt điều kiện sản xuất (DUYỆT ĐƠN HÀNG).
3. Khảo sát giá NL/BTP/VTBB → nhập kho, cập nhật **đơn giá vốn thực tế** (Giá Nhập kho NL/BTP, Giá Nhập kho VTBB).
4. Thiết lập định mức BDM → ban hành LSX TP → đối chiếu tồn kho và quyết toán lưu kho.

**Ai làm.** Admin / Kế toán trưởng (DATA 1); Kế toán GV (bảng giá, phí, BDM, CP khác, giá nhập kho); ĐP TP (Data TP, điều phối); Kỹ thuật (BDM, phí phối); Thu mua / ĐP VTBB (giá nhập VTBB); Thủ kho BTP.

**Nguồn giá (thứ tự tin cậy theo tài liệu).**
- Giá NL/BTP: sổ *Giá Nhập kho NL/BTP* (giá theo từng lô nhập, có Lab test) — *đơn giá nhập kho là đầu vào trực tiếp để tính giá vốn TP*.
- Giá VTBB: sổ *Giá Nhập kho VTBB*, cột **giá đã gồm VAT và vận chuyển**, trích từ **mã ĐMH Misa** (không có mã đơn Misa thì không trích được).
- Giá gia công: *Bảng giá NCC GC* (hợp đồng, có hiệu lực), *Phí phối NCC GC* (theo tên pháp lý + dòng V + màu, đơn vị ml/kg/lít), *Phí đóng gói NCC GC* (theo khoảng thể tích chai/gói, có VAT).
- Định mức: *BDM TP* (chi tiết sử dụng / 1 TP cho từng vật tư; vd chai 1, nắp 1, nhãn 1, nhãn dán thùng và thùng = 1 / quy cách thùng, ví dụ 1/30 = 0,0333).
- Giá đã chốt với KD: khối 4. GIÁ VỐN trong *Điều phối ĐH NL/BTP* (giá chốt theo ĐVT).

**Công thức (viết lại bằng lời).**
- Giá vốn TP (Mẫu duyệt giá TP, mỗi dòng có 2 cột GVSX và GVKD):
  `Tổng giá thành phẩm = Giá BTP + Giá VTBB + Phí gia công / đóng gói + Chi phí phụ gia + Chi phí khác`; `Giá TP cuối cùng = Tổng giá thành phẩm + Thuế VAT`.
- Chi tiết theo thành phần (Chi tiết giá TP SX-KD): với mỗi thành phần định mức *i* (chai/xô/can/bao, nắp, nhãn/túi, hộp, thùng, NDT, BTPCT): `Giá SX theo 1 TP_i = Đơn giá SX_i × Định mức_i / TP`; `Giá TP SX = Σ_i Giá SX theo 1 TP_i`; tương tự cho KD. `Thành tiền = Giá theo 1 TP × SL nhập`. Chỉ cộng các thành phần **bên mình cung cấp** (cột Phân loại NCC / CTY); thành phần NCC lo thì đã nằm trong giá NCC GC.
- Giá vốn BTP (Mẫu duyệt giá NL/BTP): `Tổng giá vốn BTP = Giá NL cấu thành + Phí phối BTP + Phụ gia + Chi phí vận chuyển + Chi phí khác`; `Giá BTP sau VAT = Tổng + VAT`; so sánh 4 cột: giá NCC báo / GVSX / giá KD / **giá chốt**.
- Bảng giá NCC GC: cột Đơn giá = **Đơn giá hợp đồng × 1,05** (hằng số 5% gõ cứng; ví dụ 81.120 → 85.176 / chai); năm HĐ = YEAR(thời gian HĐ). Cột *Chi tiết cấu thành giá* ghi giá NCC đã gồm những gì (ví dụ *Giá gồm BTP, phí đóng gói, thùng*: thùng có, giá 800; phí sang chai đóng gói có, giá 2.000).
- Phí đóng gói: `Giá đã VAT = Giá chưa VAT × 1,08` (ví dụ 250 → 270 đ / gói), dù cột VAT để trống.
- Chiết khấu / phạt theo LSX (CP khác từ NCC GC): `Thành tiền CK = SL TP × Đơn giá công nợ NCC × %CK`; `Thành tiền phạt = SL TP × Đơn giá công nợ × %phạt`; riêng 2 mã ngoại lệ tính `SL × mức cố định`; `Tổng chi phí = CK + phạt`. Giá công nợ, %CK, %phạt tra theo tên pháp lý + thể tích + kỳ hiệu lực ở sheet *6. Chính sách NCC*.
- Giá trị nhập kho NL/BTP: `Thành tiền = Lượng nhập × Giá NL/BTP` (ví dụ 3.265 kg × 112.000 đ).
- Phí lưu kho (Data NCC GC): miễn phí theo số ngày (ví dụ Hà Long: TP 15 ngày, VTBB-NL 60 ngày), vượt thì tính theo m² / pallet / tháng (ví dụ 86.400 đ / tháng / pallet 1,1 m² từ 14/9/25, 70.000 đ từ 14/9/26).
- Hao hụt: % hao hụt theo NCC (BTP, chai/túi/can, nhãn, thùng, khác) ở Data NCC GC — đa số ghi *theo thực tế* hoặc 0.

**Biên lợi nhuận (Tổng hợp giá TP).** `Biên vốn KD − SX = Giá TP KD − Giá TP SX`; `Tổng thành tiền KD − SX = Biên × SL`; `Biên KH − KD = Giá bán khách hàng − Giá TP KD`; `Tổng thành tiền KH − KD = Biên × SL`. Có hai bộ: **giá dự kiến** (lúc duyệt gửi đơn) và **giá thực tế** (theo đơn hàng), cột chênh lệch giá tạm - giá duyệt.

**Đầu ra.** Giá vốn TP / BTP đã duyệt → KD báo giá khách, lập đơn chính thức; → QLDL đối chiếu công nợ (tệp 6 *Công nợ TP đóng gói* kiểm giá NCC gửi với giá bên mình tính).

**Quy định.** Không xóa / gõ đè ô công thức; master data lấy từ Admin + Misa; có giá mới thì **không xóa dòng cũ**, cập nhật ngày kết thúc và chuyển *Ngưng áp dụng - có giá mới*; phí đóng gói phải chọn đúng VAT (8% hay 10%) và đúng khoảng thể tích; phí phối tính theo thể tích / khối lượng ruột BTP thực pha; chi phí phát sinh từ NCC phải có biên bản hoặc thỏa thuận trước.

### (b) Duyệt đơn hàng BTP và TP theo giá vốn

**Mục đích.** Không cho lập LSX khi chưa đủ điều kiện: kiểm 7 bộ phận cho đơn TP, 5 bộ phận cho đơn mua / phối NL-BTP; Giá vốn duyệt giá.

**Các bước (đơn TP).**
1. KD lên đơn PO (mã PO dạng ITP / ATP + ngày + số). ĐP TP nhập vào ĐIỀU PHỐI các trường bắt buộc (*): mã PO, trạng thái Mới / Xử lý, NCC đề xuất, SL TP, ngày yêu cầu sẵn kho NCC; công thức tự tra tên hàng, phân loại, tên pháp lý, ĐVT.
2. Sheet DUYỆT ĐƠN HÀNG kế thừa đơn; từng bộ phận cập nhật ở drive riêng của mình, công thức kéo về: **4. Pháp lý** (ĐKSX, ĐKKD, hợp đồng, pháp lý SP; đơn vị NCC bán hàng, công ty cấu thành, công ty nhận HĐ từ NCC, **dòng hóa đơn** dạng chuỗi pháp nhân, rủi ro phải chấp nhận), **5. Sự cố** (sự cố liên quan, SL mẫu), **1. NL/BTP** (ngày đủ NL/BTP nội bộ / thuế, mã BDM NL/BTP nội bộ / thuế, công thức, màu, cấu thành bên mình / khách / NCC), **2. VTBB** (ngày đủ VTBB, mã BDM VTBB nội bộ / thuế, cấu thành), **6. QLDL** (mã số chính sách giá, *Thuộc chính sách đã đàm phán với NCC GC*, hóa đơn lấy từ NCC), **3. Giá vốn** (ngày duyệt, trạng thái, ghi chú giá — ví dụ đơn giá BTP chốt và ngày), **7. QLSX** (nhập tay ngày duyệt, QLSX duyệt).
3. Cột tổng *ĐỦ ĐIỀU KIỆN NB (7 BP)* = Đủ khi cả 7 bộ phận Duyệt (mẫu đang ghi *Chưa duyệt đủ*), kèm *Ngày NB duyệt đủ điều kiện*.
4. Chỉ khi đủ điều kiện, kỹ thuật và gia công mới lập LSX; GV chuyển giá sang *Chi tiết / Tổng hợp giá TP* và in *Mẫu duyệt giá TP* (ký: người duyệt đơn, người duyệt giá TP, người lập).

**Đơn NL/BTP.** Trong *Điều phối ĐH NL/BTP* khối 4 có 5 bộ phận: Pháp lý, Sự cố, QLDL (phí phối đã chốt với NCC, HĐ lấy từ NCC), **Giá vốn** (ngày, trạng thái, giá đã chốt với KD theo ĐVT — ví dụ 110 đ / gr), QLSX. GV in *Mẫu duyệt giá NL/BTP*.

**Theo dõi tiến độ / cảnh báo (công thức ĐIỀU PHỐI).** `Số ngày gửi đơn NCC = (Ngày gửi đơn NCC, nếu chưa gửi thì hôm nay) − Ngày đơn hàng`; > 5 ngày → **TRỄ ĐƠN**, > 3 ngày → **LƯU Ý**. Khối số lượng: SL KD đặt → SL gửi NCC → NCC thực sản xuất → xuất HĐ NCC → đã nhận về → còn lại chưa SX → đã nhận HĐ chưa nhận hàng. Có tháng / năm / quý để báo cáo.

**Khái niệm cốt lõi cần giữ khi lên ERP.** *Cấu thành nội bộ* (thực tế ai cấp từng phần: bên mình / khách hàng / NCC, ví dụ *IDA: chai, nhãn, thùng; Hà Long: BTP, phí đóng gói*) khác *Cấu thành thuế* (trên hóa đơn ai xuất phần nào, ví dụ *mình mang VTBB qua nhưng NCC không nhận hóa đơn đầu vào*). Hai mã BDM tương ứng (nội bộ / thuế). *Dòng hóa đơn* là chuỗi pháp nhân hóa đơn chạy qua (ví dụ NCC → công ty trung gian → DEGO → thương hiệu).

### (c) Kinh doanh: chính sách NCC GC, khảo sát giá, đặt hàng NL/BTP/VTBB (tệp 3)

**Mục đích.** Sổ phía KD: tra chính sách NCC GC, tự tính nhu cầu BTP / VTBB cho đơn TP, gửi phiếu khảo sát giá, gửi yêu cầu mua.

**Các bước.**
1. KD tra *Thông tin NCC GC* và *Chính sách BTP và TP NCC GC* (bản sao Data TP / Data NCC GC): MOQ TP (ví dụ từ 10 thùng trở lên, trên 500 kg mới đóng đơn), thời gian SX khi đủ VTBB (3–12 ngày tùy NCC), SL phối tối thiểu, lưu kho miễn phí, hao hụt, NCC có nhận dự trù BTP không, mua NL / BTP mang qua.
2. *Phân tích TP*: KD nhập ngày, NCC GC, mã hàng, SL TP, quy cách SP (g/ml), quy cách thùng, chọn chai / nhãn / NDT / thùng, % hao hụt → tự tính nhu cầu.
3. *Khảo sát NL/BTP/VTBB KD*: KD lập phiếu YCKS (một phiếu dùng chung 3 loại; chưa có mã thì để trống; ghi thông tin bắt buộc để lấy hóa đơn riêng khi tên pháp lý thuộc NCC GC); cột tiến độ chạy về từ sheet trả KQ.
4. *YC mua NL/BTP* (phân loại Mua NL / Mua BTP / Phối BTP, giá yêu cầu, mã YCKS, ngày dự kiến bán hết) và *YC mua VTBB* (kho nhận, tháng sử dụng, mục đích, mã HH cần dùng); ĐP NL/BTP / ĐP VTBB trả kết quả vào cùng dòng (NCC, SL đã gửi mua, ngày NCC có hàng, nhập 3 lần, trạng thái, Lab).

**Công thức nhu cầu (Phân tích TP; ví dụ 4.000 chai × 240 ml).**
- `SL BTP (kg/lít) = SL TP × Quy cách SP / 1000 × (1 + %HH BTP)` → 960 lít.
- `SL chai / túi = SL TP × (1 + %HH VTBB)` → 4.080.
- `SL nhãn = SL TP × ĐM nhãn / SP × (1 + %HH VTBB)` (0 nếu in thẳng lên túi).
- `SL thùng = SL chai / Quy cách thùng`; `SL nhãn dán thùng = SL thùng × ĐM nhãn thùng`.
- Mặc định %HH BTP = 0%, %HH VTBB = 2%, ĐM nhãn = 1, ĐM nhãn thùng = 1 (KD được sửa).

**Đầu ra.** Phiếu YCKS → GV (tệp 4); YC mua → ĐP NL/BTP, ĐP VTBB (QLDL, tệp 5). **Quy định.** Phải phản hồi thời gian có hàng cho KD; thông tin hóa đơn bắt buộc khi pháp lý SX thuộc NCC GC.

### (d) Công việc khảo sát giá vốn (tệp 4)

**Mục đích.** Bộ phận GV nhận phiếu khảo sát của KD, tách NL/BTP và VTBB, chuẩn hóa qua QLDL, trả kết quả, KD duyệt.

**Các bước.**
1. Nhận 100% phiếu *Khảo sát NL/BTP/VTBB KD* (tệp 3).
2. Công thức tách 2 bảng: *Khảo sát NL/BTP* và *Khảo sát VTBB*. Mỗi cột mã / tên / dòng V / dạng màu / ĐVT / SL: **ưu tiên giá trị QLDL đã chuẩn hóa, trống thì lấy của KD**. QLDL ghi trạng thái kiểm tra (*Đã chốt thông tin* / *Chờ kiểm tra*) và ghi chú (ví dụ *Đã kiểm tra tên & SL khớp định mức*, *Điều chỉnh SL chốt lên 450 kg theo hao hụt mẻ*).
3. GV đi hỏi NCC, điền *Thông tin trả kết quả NL/BTP KD* và *VTBB KD*: giá, ngày công nợ, NCC, MOQ, thời gian có hàng, **thời gian giữ giá**, VAT, phí vận chuyển, xuất xứ, nơi giao, kết quả lab, thông số, ảnh, đánh giá, nhân sự phụ trách; khối 2 bổ sung (được sửa): **giá chốt báo KD**, trạng thái.
4. BP yêu cầu (KD) duyệt: *Kết thúc khảo sát* hoặc *Yêu cầu khảo sát thêm*.
5. *Tổng hợp thông tin trả kết quả*: gộp tự động 2 bảng, gán nhãn nguồn, cập nhật thời gian thực → KD dùng để tính giá thành báo giá khách và lập đơn.

**Trường chính.** Mã YCKS, phân loại, mã nội bộ / Misa, tên chuẩn, dòng V, ĐVT, SL khảo sát chốt, giá đề xuất, ngày cần báo giá, ngày cần hàng, thời gian dự kiến dùng (tháng), quy cách đóng gói, giá NCC, MOQ, VAT, phí vận chuyển, thời gian giữ giá.

### (e) Theo dõi mua NL/BTP/VTBB (tệp 5, QLDL)

**Mục đích.** QLDL theo dõi từng đơn mua VTBB / NL (có mã ĐMH Misa) từ lúc tiếp nhận tới khi nhận đủ, gồm vận chuyển, lab, đổi trả; lập PO gửi NCC và phiếu chuyển kho.

**Các bước.** Tiếp nhận yêu cầu (người / bộ phận đặt, pháp lý lấy HĐ) → đặt NCC (ngày đặt, mã ĐMH Misa) → in *PO* gửi NCC (mỗi đơn một công ty nhận HĐ; NCC gửi HĐ chậm nhất 24 giờ sau khi nhận hàng; ghi mail nhận HĐ) → theo dõi ngày dự kiến / thực nhận, số lần nhận, số HĐ → gửi mẫu Lab, ghi kết quả → nếu lỗi: khối đổi trả (phương án Trả / Đổi, lý do, phương án chi tiết về hàng, HĐ, công nợ, hồ sơ, tiến độ, ngày thực trả) → chuyển kho giữa các NCC GC bằng *Phiếu đề nghị chuyển kho*.

**Công thức.**
- `Ngày yêu cầu có hàng = Ngày tiếp nhận + 18`; `Ngày dự kiến nhận = Ngày tiếp nhận + 20` (hằng số gõ cứng).
- `Ngày quy định = Ngày tiếp nhận + Số ngày có hàng theo quy định` (tra theo phân loại và NCC ở DATA CHUNG).
- `Thành tiền = SL đặt × Đơn giá × (1 + VAT)` (ví dụ 100 thùng × 23.500 × 1,08).
- Vận chuyển: `SL gửi vận chuyển = SL đặt / 100` (kiện), `Thành tiền VC = SL kiện × Đơn giá VC`.
- Chỉ số trễ: `Ngày NCC dự kiến − Ngày nhận`, `Ngày quy định − Ngày nhận`, `Ngày quy định − Ngày KD yêu cầu`.
- Tên trên HĐ tự ghép theo tiền tố mã (NH = Nhãn, NT = Túi...).

**Đầu ra.** Sang tệp 6 (*CN VTBB, NL, BTP*) để ghi công nợ; số liệu nhập kho sang sổ giá nhập kho (tệp 1).

### (f) Ghi nhận công nợ, chi phí, hóa đơn (tệp 6, QLDL)

**Mục đích.** Ghi nhận mọi khoản phải trả / phải thu với NCC theo **loại công nợ**, theo dõi lấy đủ hóa đơn, kiểm giá NCC gửi.

**Loại công nợ (danh mục dùng chung).** Đơn hàng (TP / phí đóng gói), Phí phối, Phí lưu kho, Hao hụt, Chi phí khác, Mua VTBB, Mua NL (BTP), Xử lý sự cố (XLSC), Chiết khấu và phí phạt. Mỗi dòng: số chứng từ Misa, mã NCC, ngày ghi nhận, số tiền, **số ngày công nợ tính từ ngày ghi nhận** (ví dụ 7, 10), hình thức TT (UNC / TM), số HĐ, chính sách TT.

**Các bước.**
1. Nhận số nhập - xuất TP (từ tệp *2. Đầu vào nội bộ QLDL*) và giá NCC GC gửi theo từng đơn (từ tệp *4. BDM thành phẩm*).
2. *Công nợ TP đóng gói*: tách chuỗi NCC gửi (mã SP, SL × đơn giá = thành tiền), so với **giá bên mình tính** = `Đơn giá ruột NCC gửi + Đơn giá đóng gói + Phí khác 1 + 2 + 3 + Làm tròn`; cột kiểm *Khớp* đơn giá + mã HH; rồi nhập tay khối công nợ.
3. Ghi các sổ: CN (TP - phí đóng gói) — gồm loại HĐ cần lấy, công ty xuất / nhận HĐ, dòng hóa đơn, xác nhận trưởng BP; CN Phí phối; Chi phí hao hụt - lưu kho - khác (cả khoản **không có hóa đơn** từ NCC); CN XLSC; CN mua NL/BTP/VTBB; CN chiết khấu và phí phạt.
4. *Theo dõi hiện trạng hóa đơn*: `SL còn lại chưa lấy HĐ = SL mua / phát sinh − SL đã lấy HĐ` (âm = lấy dư), tiến độ, deadline.
5. *TỔNG HỢP CÔNG NỢ NCC*: gộp tất cả; quy ước **số tiền dương = trả NCC, âm = thu NCC**.
6. *Form in YC xuất HĐ NCC*: lập danh sách HĐ cần NCC xuất theo chuỗi pháp nhân (thuế suất ví dụ 5%), có ghi chú tách tờ riêng theo SP.

**CN XLSC.** Mỗi sự cố: phương án kết luận (làm gì với hàng, ai làm, tiến độ, kết quả, chi phí ai chịu, hồ sơ cần gì), tổng tiền phát sinh, **phân bổ theo bộ phận / bên chịu** (ABA, IDA, NCC...), loại chi phí (vận chuyển từ khách về kho, kiểm mẫu...), hình thức thu (cấn trừ công nợ / hạch toán chi phí / thu tiền), chứng từ xác nhận (biên bản có chữ ký NCC GC, giấy thanh toán, phiếu thu / UNC).

**Đầu ra.** Tổng hợp công nợ sang tệp 8 để đối chiếu Misa / NCC và lập dự chi.

### (g) Đối chiếu tồn kho (tệp 7, QLDL)

**Mục đích.** So tồn kho nội bộ (hệ thống) với tồn NCC GC báo, cho 4 nhóm: VTBB, BTP, TP, hàng lỗi; đối chiếu luôn phí lưu kho và hao hụt.

**Các bước.**
1. Nhận tồn NCC GC (mỗi NCC một mẫu khác nhau, mã vật tư theo mã NCC).
2. Nhận tồn nội bộ (từ ĐP VTBB, ĐP BTP, TP, hàng lỗi — tệp *2. Đầu vào nội bộ QLDL*).
3. Đối chiếu theo **Mã + Kho**: `Lệch SL giao dịch = GD hệ thống (H) − GD NCC (G)`; `Lệch tồn = Tồn hệ thống (K) − Tồn NCC báo (J)`; kết luận tự động (khớp / lệch / *Không tìm thấy Mã+Kho* / *Thiếu Kho — điền cột C*).
4. Tổng hợp 4 nhóm; lưu vào *Lịch sử đối chiếu* kèm hướng điều chỉnh với NCC GC, nguyên nhân, trạng thái xử lý; *So sánh các lần đối chiếu* lần gần nhất với lần trước (tồn cuối, dư cuối, ngày kiểm tồn tại NCC, số lần gửi).
5. Phí lưu kho và hao hụt: hai sổ (NCC báo / nội bộ ghi) → *Đối chiếu*: `Ngày đến hạn TT = Ngày ghi nhận + Số ngày CN`; `Chênh lệch tiền = Số tiền NB − Số tiền NCC`; khớp số HĐ; tình trạng hạn *Quá hạn (n ngày)* / *Trong hạn*; trạng thái *Khớp hoàn toàn* / *Lệch số tiền* / *Thiếu bên NCC*; hướng xử lý (ví dụ yêu cầu NCC gửi bảng kê ngày lưu bãi; gửi biên bản xác nhận hao hụt vượt định mức 2% để cấn trừ).

**Mốc.** Hướng dẫn tệp 1: đối chiếu tồn tổng định kỳ **hàng tuần / tháng** với biên bản kiểm kê của NCC; phí lưu kho đối chiếu **cuối tháng** theo biên bản tồn kho NCC. Ai làm: QLDL tổng hợp, ĐP VTBB / ĐP BTP cung cấp kết quả.

### (h) Đối chiếu công nợ NCC, thanh toán, dự chi (tệp 8, QLDL + Kế toán)

**Mục đích.** Đối chiếu ba phía (sổ nội bộ Drive/App, Misa, NCC gửi), lập kế hoạch chi, theo dõi từng lần trả và lãi quá hạn.

**Các bước.**
1. Nhận *Tổng hợp công nợ NCC (nội bộ)* từ tệp 6.
2. Xuất *Công nợ Misa* (chi tiết công nợ phải trả, TK 331, theo kỳ).
3. *Đối chiếu Drive/App với Misa* theo số chứng từ Misa: số HĐ, số tiền, ngày TT; `Chênh lệch = Tiền Drive − Tiền Misa`; tình trạng chung; nhập tay nguyên nhân (ví dụ *chưa ghi nhận đủ phí*), hướng xử lý, người xử lý, deadline.
4. Nhận *Công nợ NCC GC gửi* (sổ chi tiết công nợ của NCC, thường là TK 131 phía NCC) → *Đối chiếu NCC GC với Misa*, **Misa làm gốc**.
5. Lưu lịch sử, so sánh các kỳ.
6. *Dự chi NCC*: lấy các khoản từ đối chiếu, ghi tháng chi, **ngày đến hạn**, thương hiệu yêu cầu mua, công ty nhận HĐ; nếu kế toán không trả đúng hạn: đánh giá rủi ro (lãi suất, bị ngưng đơn), ngày chậm nhất phải trả (deal lại với NCC).
7. *Chi tiết thanh toán*: mỗi lần trả một dòng (ngày lập / gửi hồ sơ TT, nội dung, công ty thanh toán, số tiền đã trả, lần thứ mấy, còn lại, ảnh UNC); *Tổng hợp thanh toán* (ẩn) gộp theo mã hồ sơ.

**Công thức thanh toán.**
- `Còn lại chưa TT = Số tiền công nợ − Tổng đã TT`.
- `Tiền lãi quá hạn = Số tiền công nợ × Lãi suất %/tháng × Số ngày quá hạn / Số ngày thực tế của tháng` (ví dụ 50 triệu × 1% × 10/30 ≈ 166.667 đ).
- `Tổng còn lại = Còn lại chưa TT + Lãi chưa TT`.

**Đầu ra.** Kế toán chi; báo cáo dự chi theo tháng (sheet này còn *chưa rõ yêu cầu*).

### (i) Báo cáo VTBB (BC VTBB.xlsx)

**Mục đích.** Báo cáo tự động xuất - nhập - tồn VTBB theo tháng / quý / năm / khoảng tùy chọn; tồn lâu, tồn chết, chi phí lưu kho, hao hụt, lỗi nhập, đề xuất đặt hàng theo Min / MOQ.

**Các bước hàng tháng (khoảng 2 phút).** (1) Mở file hệ thống quản lý kho → sheet LỊCH SỬ → copy A:J; (2) dán *giá trị* vào GIAO DỊCH VTBB từ A2 (dán đè, xóa dòng thừa, không đụng cột L trở đi); (3) mã mới thì dán thêm vào DANH MỤC VTBB (mã, tên, ĐVT, giá Min, giá Max từ DATA 1), điền NCC nếu cần; (4) DASHBOARD đổi *Đến ngày* và *Năm báo cáo*; (5) xem KIỂM TRA DỮ LIỆU, các số phải = 0, phân loại lạ thì thêm vào CẤU HÌNH.

**Người dùng chỉ cập nhật 4 sheet**: GIAO DỊCH VTBB, DANH MỤC VTBB, MIN MOQ, CẤU HÌNH. Năm sheet còn lại tự tính.

**Cấu hình loại VTBB.** 10 loại (Thùng carton, Nhãn / Tem, Túi / Màng, Hộp giấy, Chai / Lọ, Nắp / Nút, Khay / Vách ngăn, Băng keo / Dây đai, Bao bì in khác, Khác), mỗi loại có **định mức hao hụt %** (1–3%: thùng 2%, nhãn 3%, túi 3%, hộp 2%, chai 1%, nắp 1%...) và ngưỡng tồn lâu riêng (để trống = mặc định 90 ngày). Loại **suy từ 3 ký tự đầu mã** (CPT / CHT / CET... → Chai / Lọ; NAP → Nắp; THC / THI / THA → Thùng; HOP → Hộp; NHG / NDT / NTN / TEM... → Nhãn; BAO / TUI / SEA → Túi; VT0 → Khác); ghi đè từng mã ở DANH MỤC cột G.

**Phân loại giao dịch (khớp danh sách ở DATA 1 Admin).** Nhập: mua, sau phối, chuyển kho, cho/tặng, đổ thu / dư sau SX, khác, tạm, lỗi / hư hỏng, đầu kỳ, đầu kỳ lỗi. Xuất: chuyển kho, cho/tặng, mẫu thử, tạm, SX tạm, xử lý hàng lỗi, **hao hụt / đổ bỏ** (cờ hao hụt = 1), khác, NL phối BTP, bán, hoàn thành. Mỗi loại có chiều (+1 / −1), nhóm tồn (Thực tế / Tạm / Lỗi), nhóm báo cáo (Nhập / Xuất / Đầu kỳ / Chuyển kho).

**Công thức chính.**
- `Đơn giá dùng` = đơn giá nhập tay nếu > 0; nếu không theo chế độ: Giá Min, Giá Max hoặc trung bình (Min + Max) / 2.
- `Giá trị = SL × Đơn giá dùng`; mã chưa có giá → giá trị 0 (đếm ở KPI).
- `Tồn = Đầu kỳ + Nhập − Xuất`; `Tồn có thể SX = Tồn thực tế + Tồn tạm` (tạm âm = đã xuất giữ cho đơn chưa SX).
- Nhập đầu kỳ và chuyển kho **không** tính vào giá trị nhập / xuất (chỉ đổi tồn).
- `Số ngày tồn = Đến ngày − Ngày nhập cuối` (khi tồn > 0); **tồn lâu** nếu số ngày tồn > ngưỡng của loại.
- Nhóm luân chuyển theo số ngày từ xuất cuối: ≤ 30 ngày *Nhanh*, ≤ 90 ngày *Chậm*, quá 90 hoặc chưa từng xuất → *Tồn chết*.
- `Xuất TB / ngày = Xuất thực tế 90 ngày gần nhất / 90`; `Ngày đủ dùng = Tồn có thể SX / Xuất TB ngày`; **vượt nhu cầu** nếu > 180 ngày.
- **Min / MOQ**: dưới Min khi `Tồn có thể SX < Min`; `SL đề xuất đặt = làm tròn lên( max(Min − Tồn có thể SX − SL đang đặt chưa về, 0) / MOQ ) × MOQ` (MOQ = 0 thì không làm tròn).
- **Chi phí lưu kho** (giả định): `CP / tháng = Giá trị tồn × 1,5%`; `CP lũy kế = Giá trị tồn × 1,5% × Số ngày tồn / 30`.
- **Hao hụt**: `Tỷ lệ hao hụt = Giá trị hao hụt / Giá trị xuất thực tế`, tô đỏ khi vượt định mức của loại; `Tỷ lệ lỗi nhập = Giá trị nhập lỗi / Giá trị tổng nhập` (theo NCC → đánh giá chất lượng NCC VTBB).
- DIO (số ngày tồn kho bình quân) theo loại; tuổi tồn theo 5 khoảng (0–30, 31–60, 61–90, 91–180, > 180 ngày).

**Số liệu hiện có (minh họa, chốt 30/06/2026).** 2.226 dòng giao dịch, 2.173 dòng XNT, khoảng 6.158 mã danh mục; 21 dòng giao dịch có mã ngoài danh mục; tổng giá trị tồn khoảng 3,6 tỷ đ; 8 mã dưới Min, 8 mã tồn âm (lỗi dữ liệu), 2.157 mã bị xếp *Tồn chết*.

**Đầu ra.** ĐP VTBB, QLDL, quản lý: biết mã cần đặt, mã tồn lâu cần xử lý, chi phí lưu kho ước tính, hao hụt vượt định mức, NCC hay giao lỗi.

---

## 3. Trùng lặp

1. **Bản sao nguyên sheet giữa các tệp** (đều ghi *Nhận thông tin 100%*): Quản lý nhãn mác, ĐIỀU PHỐI, DUYỆT ĐƠN HÀNG (ĐP TP), BDM TP, LSX TP, Giá Nhập kho VTBB / NLBTP, Bảng giá NCC GC, Phí đóng gói NCC GC, Điều phối ĐH NLBTP có ở cả tệp 1 và tệp 2; Data TP = *Thông tin NCC GC* (tệp 3); Data NCC GC = *Chính sách BTP và TP NCC GC* (tệp 3); 4 sheet Tồn kho chi tiết / tổng BTP, VTBB có ở tệp 1 và tệp 3; Phí Lưu kho NCC GC có ở tệp 1, tệp 3, tệp 6 (*Chi Phí hao hụt - lưu kho - CP khác*), tệp 7 (2 sheet *Phí lưu kho và hao hụt NCC GC / nội bộ*) — cùng một khung 12 cột.
2. **Phiếu khảo sát giá** xuất hiện 4 nơi: tệp 1, tệp 3 (gốc KD), tệp 4 (bản sao + 2 bảng phân tách); **phiếu trả kết quả** ở tệp 1, 2, 3, 4 (bản tệp 4 đầy đủ nhất, có khối bổ sung và giá chốt).
3. **YC mua NL/BTP (tệp 3)** và **Điều phối ĐH NLBTP (tệp 1, 2)** cùng cột A–AQ; tệp 1/2 thêm khối Lab, số lô, cấu thành và duyệt bộ phận.
4. **Tiến độ mua, trả hàng (tệp 5)** = **CN VTBB, NL, BTP (tệp 6)** (thêm 3 cột công nợ).
5. **CP khác từ NCC GC (tệp 1)** = **CN chiết khấu và phí phạt NCC (tệp 6)** (thêm khối công nợ).
6. **TỔNG HỢP CÔNG NỢ NCC (tệp 6)** = **TỔNG HỢP CÔNG NỢ NCC (NỘI BỘ) (tệp 8)**; hai sheet đối chiếu ở tệp 8 cùng một khung 24 cột; *So sánh các lần đối chiếu* và *Lịch sử đối chiếu* của tệp 8 chép nguyên từ tệp 7 (còn tiêu đề tồn kho, chưa sửa cho công nợ).
7. **Bốn sheet đối chiếu tồn kho (VTBB / BTP / TP / hàng lỗi) + tổng hợp + lịch sử** trong tệp 7 cùng khung 13 cột và cùng dữ liệu mẫu — có thể là một bảng có cột *nhóm hàng*.
8. **Danh sách phân loại giao dịch Nhập / Xuất / Tồn** ở DATA 1 Admin (tệp 1) và ở CẤU HÌNH (BC VTBB) — cùng từ vựng, BC VTBB có thêm chiều, nhóm tồn, cờ hao hụt.
9. **Tồn kho VTBB** được tính ít nhất 3 nơi: Tồn kho chi tiết / tổng VTBB SX (tệp 1, 3), XNT VTBB (BC VTBB), đối chiếu tồn VTBB (tệp 7); cùng khái niệm tồn thực tế / tạm / lỗi / có thể SX nhưng công thức và ngưỡng cảnh báo khác nhau.
10. **Hao hụt** có 4 nguồn tham số: % hao hụt theo NCC (Data NCC GC), mặc định 0% / 2% (Phân tích TP), định mức theo loại VTBB 1–3% (CẤU HÌNH BC VTBB), định mức 2% nêu trong đối chiếu phí hao hụt (tệp 7).
11. **MOQ** ở 5 nơi: MOQ TP (Data NCC GC), MOQ BTP (Chính sách BTP), MOQ trong Bảng giá NCC GC, MOQ trong trả kết quả khảo sát, MIN MOQ (BC VTBB).

---

## 4. Đối chiếu ERP (ước lượng)

Đã soát nhanh mã `procurement-tool` (nhánh `erp-v2`, cùng `origin/erp-v2` cho cụm duoc-CR-784). Mức khớp: **Khớp** / **Một phần** / **Chưa có**.

| Nghiệp vụ Excel | ERP DEGO hiện có | Mức | Ghi chú |
|---|---|---|---|
| Phiếu khảo sát NL/BTP/VTBB của KD (YCKS) + trả kết quả (giá, MOQ, VAT, phí vận chuyển, thời gian có hàng, giữ giá) + KD duyệt kết thúc / khảo sát thêm | YCBG / khảo sát giá (`survey_request`, `survey` có trường `moq`), phương án, chọn phương án | Một phần → khá khớp | Thiếu: thời gian giữ giá, kết quả lab, xuất xứ theo từng báo giá (cần soát lại); thiếu bước QLDL chuẩn hóa tên / mã / SL trước khi đi hỏi; thiếu *giá chốt báo KD* tách khỏi giá NCC |
| YC mua NL/BTP/VTBB của KD (phân loại Mua NL / Mua BTP / Phối BTP, kho nhận, ngày cần, mã HH cần dùng) | YCMH (`purchase_request`) | Một phần | ERP chưa có phân loại *Phối BTP* (gửi NL cho NCC GC phối), chưa gắn mã TP / đơn TP mà vật tư phục vụ |
| Theo dõi mua (tệp 5): ĐMH, PO in, ngày dự kiến / thực nhận, nhận nhiều lần, số HĐ | ĐMH (`purchase_order`), nhận hàng (`goods_receipt`), tiến độ mua (`purchase_progress`), in phiếu | Khớp phần lõi | Thiếu: chỉ số trễ theo **số ngày có hàng quy định** từng loại / NCC; khối **Lab** theo lô nhận; khối **đổi trả** (Trả / Đổi, phương án hàng - HĐ - công nợ); vận chuyển theo kiện tách thành tiền vận chuyển riêng (ERP có chi phí thu mua giá ba giai đoạn — xem dưới) |
| Giá nhập kho VTBB = giá gồm VAT + vận chuyển, trích theo mã ĐMH Misa | Chi phí thu mua giá ba giai đoạn (phân bổ chi phí về hàng vào giá); sổ giá cụm Giá NVL SX lấy từ lịch sử mua + dòng ĐMH + sổ Misa; giá mua gần nhất | Khớp khá | Excel lấy giá *gồm VAT*, ERP kho tính bình quân gia quyền (`avg_cost`) — cần chốt giá vốn dùng giá trước hay sau VAT |
| Định mức VTBB của TP (BDM TP: chai, nắp, nhãn, NDT, thùng, cốc; ĐM / 1 TP) | Định mức bao bì (`tab_packaging_bom` + `tab_packaging_bom_part`, duoc-CR-784) | Khớp | Excel còn có mã BĐM **nội bộ** và mã BĐM **thuế** riêng, cấu thành theo bên cung cấp (mình / khách / NCC), duyệt BĐM + ngày duyệt — ERP chưa thấy |
| Tính chi phí bao bì / TP (Chi tiết giá TP: Σ đơn giá × định mức) | Màn **Tác động giá bao bì**: chi phí bao bì trên chai và trên thùng từ sổ giá + định mức | Khớp phần VTBB | Đây là phần đã có gần nhất với giá vốn |
| **Giá vốn TP đầy đủ** = BTP/NL + VTBB + phí phối + phí sang chai / đóng gói + phụ gia + chi phí khác + VAT; GVSX vs GVKD; giá dự kiến vs giá thực tế; biên KD - SX, KH - KD; phiếu duyệt giá TP / BTP | — | **Chưa có** | ERP chỉ có phần bao bì; chưa có bảng giá BTP / NL theo dòng V - màu, chưa có phí gia công, chưa có hai lớp giá SX / KD, chưa có luồng duyệt giá |
| Bảng giá / hợp đồng NCC GC (hiệu lực, số lần đổi giá, tình trạng áp dụng, cấu thành giá, MOQ, % phạt, % chiết khấu hai chiều, số ngày công nợ); biểu phí phối; biểu phí đóng gói theo khoảng thể tích | Hợp đồng NCC (`contract`), báo giá trong cụm Giá NVL (`tab_product_price_quote`, nhập tay / Excel) | Một phần | Chưa có biểu phí dịch vụ gia công theo khoảng thể tích / dòng V; chưa có chiết khấu - phí phạt tự tính theo LSX |
| Chính sách NCC GC (lưu kho miễn phí, phí lưu kho m² / pallet, lead time, % hao hụt theo loại, MOQ TP, SL phối tối thiểu, cọc nhãn, đánh giá ưu / nhược) | Nhà cung cấp (`supplier`), thẻ điểm NCC | Một phần | Thiếu các trường chính sách gia công; đánh giá ưu / nhược đang là chữ tự do |
| Duyệt đơn TP / NL-BTP qua 7 (5) bộ phận, cột *đủ điều kiện* trước khi lập LSX | Luồng phê duyệt chung (`approval`) cho chứng từ thu mua | Chưa có (cho đơn sản xuất) | ERP chưa có chứng từ *đơn đặt hàng TP gia công* / LSX; khái niệm **cấu thành nội bộ / thuế** và **dòng hóa đơn** (chuỗi pháp nhân) chưa có |
| Kho và tồn kho: nhiều kho tại NCC GC, tồn thực tế / tạm / lỗi, xuất SX theo LSX, xuất tạm, hàng treo theo đơn, số lô, NSX, HSD, Lab, trạng thái sử dụng được | Kho (`inventory`: tồn + giá bình quân; phiếu kho chỉ `gr` nhận hàng và `adjust` điều chỉnh) | Một phần nhỏ | Thiếu: xuất kho (SX, mẫu, hao hụt, chuyển kho giữa NCC GC), tồn tạm / lỗi, theo lô - HSD, giữ hàng cho đơn |
| **Min / MOQ / SL đề xuất đặt** (BC VTBB) | — (chỉ có `moq` trên báo giá khảo sát) | **Chưa có** | Công thức sẵn ở BC VTBB, dễ đưa vào màn tồn kho |
| **Hao hụt** (định mức theo loại VTBB, theo NCC; tỷ lệ thực tế = hao hụt / xuất; vượt định mức → cấn trừ NCC) | — (kế hoạch `doc/plans/01-luong-chuan-mua-hang-kho-san-xuat.md` có nhắc hao hụt định mức) | **Chưa có** | |
| Chi phí lưu kho (thực tế NCC tính và ước tính 1,5% / tháng), tồn lâu, tồn chết, tuổi tồn, DIO | — | **Chưa có** | |
| Đối chiếu tồn kho nội bộ vs NCC GC theo mã + kho, lịch sử và so sánh kỳ | — | **Chưa có** | Cần bảng ánh xạ mã vật tư NCC ↔ mã nội bộ (mỗi NCC một mẫu) |
| Ghi nhận công nợ theo loại (đơn hàng, phí phối, lưu kho, hao hụt, mua NL/VTBB, XLSC, chiết khấu / phạt); dương trả / âm thu | Công nợ (`payable`: hạn trả `due_date`, cảnh báo đến hạn) gắn ĐMH | Một phần | ERP công nợ sinh từ ĐMH; chưa có công nợ **không qua ĐMH** (phí lưu kho, hao hụt, phạt, sự cố), chưa có loại công nợ, chưa có khoản âm (thu NCC / cấn trừ) |
| Theo dõi lấy hóa đơn theo số lượng (đã lấy / còn thiếu / deadline) | (cần soát; ĐMH có số HĐ) | Một phần / chưa rõ | |
| Đối chiếu công nợ 3 bên (nội bộ - Misa - NCC gửi), Misa làm gốc | Sổ Misa nạp vào cụm Giá NVL (chỉ giá), đồng bộ Misa một số chỗ | **Chưa có** (cho công nợ) | |
| Đề nghị thanh toán, nhiều lần trả, ảnh UNC | YCTT (`payment_request`) | Khớp phần lõi | Thiếu **lãi quá hạn** (lãi %/tháng × số ngày quá hạn) |
| **Dự chi** theo tháng (ngày đến hạn, rủi ro trễ, ngày chậm nhất đã deal lại) | Cảnh báo đến hạn công nợ (`payable/due_alerts.py`) | **Chưa có** (dạng kế hoạch chi) | |
| CN xử lý sự cố, phân bổ chi phí theo bên chịu | — (sự cố SX thuộc nhóm tài liệu khác) | Chưa có | |
| Lịch sử mua hàng, giá mua gần nhất, tra cứu thị trường (hải quan) | Có | Khớp | Hữu ích cho bước GV đi khảo sát (so giá NCC báo với giá đã mua / giá thị trường) — Excel không có bước này |

**Tóm lại.** Phần **mua hàng lõi** (khảo sát, YCMH, ĐMH, nhận hàng, YCTT) và **giá bao bì theo định mức** đã có. Phần **chưa có lớn nhất**: (1) giá vốn TP đầy đủ gồm BTP / NL + gia công + chi phí khác, hai lớp SX / KD, dự kiến / thực tế, phiếu duyệt giá; (2) đơn TP gia công + duyệt 7 bộ phận + cấu thành nội bộ / thuế; (3) kho nhiều trạng thái tại NCC GC, Min / MOQ / đề xuất đặt, hao hụt, chi phí lưu kho, đối chiếu tồn với NCC; (4) công nợ ngoài ĐMH, đối chiếu ba bên, dự chi, lãi quá hạn.

---

## 5. Câu hỏi / mâu thuẫn

1. **Hệ số 1,05 ở Bảng giá NCC GC** (Đơn giá = Đơn giá HĐ × 1,05) là VAT 5%, phụ phí hay chiết khấu? Cùng dòng có *NCC chiết khấu 5%* — dễ hiểu nhầm. Phí đóng gói lại nhân 1,08 trong khi cột VAT để trống.
2. **Giá vốn tính trước hay sau VAT?** Giá nhập kho VTBB ghi *đã gồm VAT và vận chuyển*; Mẫu duyệt giá TP cộng VAT ở cuối; kho ERP tính bình quân giá ĐMH. Cần một quy ước duy nhất.
3. **GVSX và GVKD khác nhau ở đâu?** Có hai cột đơn giá SX / KD và *dòng V áp dụng cho KD*, nhưng không có công thức hay quy tắc chênh (cộng phần trăm? giá thị trường?). Cột *Đơn giá KD* ở Chi tiết giá TP đang chứa công thức kiểu `ngày hạch toán + 15` — có vẻ đặt nhầm cột (giống ngày công nợ).
4. **Mẫu duyệt giá NL/BTP đánh số nhảy 3 → 5** (thiếu khoản mục 4) — có phải đã bỏ *hao hụt* khỏi giá BTP? Hao hụt có được cộng vào giá vốn không, cộng ở đâu?
5. **Định mức hao hụt mâu thuẫn**: Data NCC GC ghi *theo thực tế* / 0; Phân tích TP mặc định VTBB 2%; BC VTBB 1–3% theo loại; đối chiếu phí hao hụt nhắc *vượt định mức 2%*. Nguồn nào là chuẩn để cấn trừ NCC?
6. **Chế độ đơn giá ở BC VTBB**: Hướng dẫn nói mặc định lấy **trung bình** Min - Max, nhưng DASHBOARD đang đặt **Giá Max** — giá trị tồn 3,6 tỷ đang bị đẩy cao. Và giá Min / Max lấy từ DATA 1 thay vì giá nhập thực tế (sổ Giá Nhập kho VTBB) — vì sao không dùng giá ĐMH?
7. **2.157 / 2.159 mã bị xếp Tồn chết**, 8 mã tồn âm, 21 dòng mã ngoài danh mục: dữ liệu xuất kho có được ghi đầy đủ vào sheet LỊCH SỬ không, hay chỉ có nhập? Nhập đầu kỳ ngày 30/04/2026 làm tuổi tồn sai.
8. **Chi phí lưu kho 1,5% / tháng là giả định**; thực tế NCC tính theo m² / pallet (Hà Long) hoặc miễn phí. Báo cáo nào là số dùng để ra quyết định?
9. **Ngưỡng cảnh báo tồn 500 / 200** ở Tồn kho chi tiết BTP / VTBB dùng một mức cho mọi ĐVT (kg, lít, cái) — có cần ngưỡng theo mã (như Min ở BC VTBB)?
10. **Tồn kho chi tiết VTBB SX** đang mang tiêu đề và dữ liệu mẫu của BTP — chưa hoàn thiện.
11. **Liên kết vỡ**: tệp 5 tra *1. DATA CHUNG*, *2. DATA NL, VTBB* (không có trong tệp, ô `#REF!`); *Form in YC xuất HĐ NCC* và *Trang tính21* toàn `#N/A` / `#REF!`; *CP khác từ NCC GC* tra *6. Chính sách NCC* không có trong tệp 1. Các sổ này có đang chạy thật không, hay mới là thiết kế?
12. **Hằng số ngày trong tệp 5**: ngày yêu cầu có hàng = tiếp nhận + 18, dự kiến = + 20 cho mọi đơn — trùng hay lệch với *số ngày có hàng theo quy định* tra theo loại / NCC?
13. **Phân tích TP**: dòng mẫu 2 cho nhãn dán thùng 204 trong khi thùng 102 (dòng 1 và 3 thì bằng nhau) — ĐM nhãn thùng 2 hay lỗi gõ? SL nhãn dán thùng tính trên SL chai đã cộng hao hụt hay chưa?
14. **Ngày lưu kho VTBB, NL** ở tệp 3 hiển thị thành ngày 28/02/1900 (lỗi định dạng số 60) — bản sao làm sai dữ liệu.
15. **Trạng thái ĐỦ ĐIỀU KIỆN NB (7 BP)** chỉ là giá trị gõ tay ở mẫu; quy tắc chính xác (cả 7 *Duyệt*? bộ phận nào được *Duyệt có điều kiện*?) và ai là người chốt cuối (QLSX hay Ban Giám đốc như hướng dẫn ghi)?
16. **Lãi quá hạn** tính trên *số tiền công nợ ban đầu* hay *số còn lại*? Ví dụ mẫu tính trên 50 triệu dù đã trả 20 triệu. Lãi suất lấy từ đâu (hợp đồng NCC)?
17. **Tệp 8 còn 2 sheet ghi chưa rõ yêu cầu** (BC dự chi theo tháng, Tổng hợp thanh toán) — cần hỏi người dùng thực tế cần gì; *So sánh / Lịch sử đối chiếu* của tệp 8 vẫn là khung tồn kho.
18. **Tệp 1 và tệp 2 cùng chứa bản sao đầy đủ** ĐIỀU PHỐI / DUYỆT ĐƠN HÀNG / bảng giá: bản nào là gốc khi số liệu lệch? Hướng dẫn tệp 1 nói 22 phân hệ nhưng mục lục liệt kê 23.
19. **Mã sản phẩm hai hệ**: tồn NCC GC dùng mã của NCC (BTIDA..., TPIDA...), nội bộ dùng HH / BTPR / CPT...; đối chiếu tồn và công nợ cần bảng ánh xạ — ai giữ?
20. **Phạm vi chiết khấu / phạt** hiện chỉ áp cho An Nông và lấy từ nhập kho DR.XANH — các NCC khác xử lý thế nào? Bình luận *hàng chiết khấu không cần in phí phạt với chiết khấu* cần làm rõ quy tắc.
