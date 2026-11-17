# Đánh giá tệp quy trình bàn giao Phòng Sản xuất, đối chiếu với khảo sát MIC

| | |
|---|---|
| Ngày | 06/11/2026 |
| Đầu vào | Tệp quy trình Excel (20 sheet, xuất ra [`du-lieu/09-quy-trinh-ban-giao-sheets/`](../du-lieu/09-quy-trinh-ban-giao-sheets/); đọc thêm tệp gốc `qtsx.xlsx` để biết ô nào bỏ trống); bản tóm gọn MIC; 177 câu hỏi đáp MIC; bản phân tích cũ 24/10 |
| Cách trích nguồn | `S4 R32` = sheet *4. QT QL ĐƠN HÀNG SX GC*, dòng 32 của tệp xuất. `V3·C6` = vòng 3, câu 6 của MIC. `MIC-KQ` = trang kết quả MIC (không có số câu) |
| Trạng thái | Nháp để người chủ đọc. Chỗ nào chưa chắc ghi *chưa rõ* |

**Từ viết tắt dùng trong bài**

| Viết tắt | Nghĩa |
|---|---|
| NCC GC | Nhà cung cấp gia công: nhà máy ngoài làm hàng cho DEGO (khoảng 12 nhà) |
| NL, BTP, TP, HH | Nguyên liệu; Bán thành phẩm (phần ruột đã phối); Thành phẩm; Hàng hóa (mã thành phẩm trên MISA) |
| VTBB | Vật tư bao bì: chai, nắp, túi, nhãn, thùng... |
| BĐM | Bảng định mức: cần bao nhiêu NL / VTBB cho một đơn vị sản phẩm. Có 3 tầng BTP, VTBB, TP; mỗi tầng có bản *nội bộ* và bản *thuế* |
| LSX | Lệnh sản xuất |
| QLSX | Quản lý sản xuất = Trưởng phòng = chị Ngân |
| TNĐP | Trưởng nhóm Điều phối (đang trống, chị Ngân kiêm) |
| ĐP TP, ĐP NL/BTP, ĐP VTBB | Chuyên viên Điều phối thành phẩm; Điều phối nguyên liệu / bán thành phẩm; Điều phối vật tư bao bì |
| QLDL, TN QLDL | Nhóm Quản lý dữ liệu (hồ sơ, chứng từ, công nợ NCC GC); Trưởng nhóm QLDL (chị Huỳnh) |
| XLSC, NV XLSC | Xử lý sự cố; nhân viên xử lý sự cố (Bảo Thi, kiêm Pháp lý) |
| KD | Kinh doanh, tức các thương hiệu nội bộ (IDA, ABA, BamBoo, Dr Xanh, N2SBIO...) |
| P TCKT | Phòng Tài chính Kế toán |
| GVSX, GVKD | Giá vốn sản xuất; Giá vốn kinh doanh |
| MOQ | Số lượng đặt tối thiểu |

---

## 0. Đọc nhanh

1. **Tệp có khung tốt nhưng chưa phải bản bàn giao.** 12 quy trình đều theo một khuôn (mục tiêu, thời điểm, bảng bước, biểu mẫu, Drive, nhóm Zalo). Nhưng **cột Thời lượng bỏ trống ở mọi bước của cả 12 quy trình**; hai quy trình sự cố **không có cột Người duyệt**; quy trình Pháp lý **không bước nào có người duyệt**.
2. **Mục lục báo đẹp hơn thực tế.** Mục lục (cập nhật 14/8/2026) ghi *Hoàn thành* cho 9 quy trình, trong khi sheet 5, 8, 9 còn ghi chú *cần chốt trước khi ban hành*. Ba mục 13 (Ngưng hợp tác), 22 (Sơ đồ và mô tả công việc), 23 (Phân quyền ký) **không có sheet**. Hai sheet *Thông tin NCC GC* và *Thông tin sản phẩm* **gần như trống**.
3. **MIC không hỏi trúng chỗ tệp còn dở.** Tệp có khoảng 25 ghi chú dở (mục 5). Trong 177 câu lấy được, **không câu nào hỏi thẳng vào các ghi chú đó** (quy tắc mã đơn, hao hụt thuế, nhập kho dư sản xuất, phạm vi duyệt pháp lý...). Phần lớn câu MIC hỏi vai trò, kênh, công cụ theo khuôn của MIC; khoảng 13 câu hỏi lại thứ tệp đã ghi, và phòng đã phàn nàn.
4. **Có 6 chỗ tệp và câu trả lời lệch nhau thật sự**: ai ký giá vốn thực tế, đánh giá NCC theo quý hay 6 tháng, Lab trả kết quả 2 hay 14 ngày, ai xử lý sự cố trong sản xuất, cảnh báo biên lợi nhuận còn hay bỏ, ai duyệt hợp đồng NCC mới (mục 4).
5. **Hai thứ chặn việc dựng ERP**: chưa có quy tắc đặt mã đơn hàng (S2 R1) và chưa có danh sách trạng thái đơn chuẩn. Đề xuất **25 câu hỏi lại** (mục 5), câu nào cũng trích dòng tệp.

---

## 1. Tệp bàn giao gồm gì

Ghi chú khi đọc tệp:
- Số bước dạng `4.1`, `5.2`... trong tệp đã bị Excel đổi thành ngày (ví dụ `2026-01-04` là bước 4.1, `2026-02-05` là bước 5.2). Người kế nhiệm mở tệp sẽ thấy ngày thay vì số bước. Nên định dạng cột STT là *Text*.
- Cột *Thời lượng* trống ở **100% bước** của sheet 1 đến 12. Các hạn có trong tệp đều nằm lẫn trong chữ ở cột Chi tiết.
- *Trạng thái MỤC LỤC* lấy từ sheet MỤC LỤC R2–R24, ngày cập nhật 14/8/2026.

| # | Sheet | Nội dung chính | Số bước | Trạng thái MỤC LỤC | Độ đầy đủ (nhận xét) |
|---|---|---|---|---|---|
| 0 | MỤC LỤC | Danh sách 23 mục, mô tả, link, trạng thái | 23 dòng | (không áp dụng) | Đánh số lệch với tên sheet (STT 16 là sheet *14. MẪU BIỂU*, STT 21 là sheet *20. LƯU TRỮ*); mục 13, 22, 23 không có sheet (R14, R23, R24) |
| 1 | TIẾN ĐỘ DRIVE | Bảng theo dõi việc dựng khoảng 196 sheet trên hơn 10 Drive: ai làm, trạng thái | 196 dòng | không có trong MỤC LỤC | 53 Hoàn thành, 138 Đang thực hiện, 5 Chưa bắt đầu. Toàn bộ 59 sheet Drive Giá vốn và Drive QLDL đều *Đang thực hiện* (R5–R128). Còn tên người đã nghỉ (Mr Toàn, R136–R140, R189) |
| 2 | 1. QT LÀM VIỆC VỚI NCC MỚI | Tìm NCC GC mới, kiểm pháp lý, chốt danh mục, lấy mẫu / phối mẫu (tối đa 2 lần), chốt bảng giá, soạn và ký hợp đồng, bàn giao nội bộ | 7 bước lớn, 30 dòng việc | Hoàn thành | Khá đủ vai trò. Thiếu thời hạn (R14 tự ghi *chưa có thời gian tiếp nhận và phản hồi*). Bước 3 không có người làm (R16). Ghi chú dở R18 (checklist BVTV có áp cho NCC phân bón không) |
| 3 | 2. QT KHAI BÁO SX | Khai báo mã NL, BTP (5 loại), VTBB, chi phí, HH, NCC, kho; luồng kiểm tra, trình QLSX, gửi Kế toán nhập MISA; quy tắc đặt mã từng loại | 3 phần: 12 loại khai báo, 5 bước duyệt, khoảng 25 quy tắc mã | Cần kiểm tra lại | **Thiếu quy tắc mã đơn hàng, mã sự cố, mã BĐM** (R1 tự ghi). Mục V, VI, VII trống (R71–R83). Biểu mẫu BTP R&D ghi *Drive ....* (R24). Tên nhóm Zalo không thống nhất (R19 *TM - KHAI BÁO NỘI BỘ*, R34 *SX&P TCKT...*, R65 *SX&KT - NB KHAI BÁO...*) |
| 4 | 3. QT KHẢO SÁT VÀ TÍNH GIÁ VỐN | Ba lúc tính giá: khảo sát cho KD, kiểm giá khi có đơn, xác nhận giá sau sản xuất và gửi Kế toán | 3 giai đoạn, 13 dòng việc | Hoàn thành | Có người làm, người duyệt. Biểu mẫu chỉ ghi *Form 1–5*, mục V trống (R40–R43). Đoạn cảnh báo biên (R32) đã lỗi thời theo V3·C2 |
| 5 | 4. QT QL ĐƠN HÀNG SX GC | **Xương sống.** A: tiếp nhận đơn, 7 bộ phận kiểm, duyệt giá, gửi đơn NCC, theo dõi, nhận hóa đơn, nhận hàng, gửi mẫu Lab, chứng từ. B: hủy đơn (chưa gửi / đã gửi NCC) | A: 7 bước (15 dòng); B: 3 bước (5 dòng) | Hoàn thành | Đủ người làm. Không có bước riêng *QLSX duyệt đơn* (chỉ là một trong 7 mục kiểm, R17). Không có danh sách trạng thái đơn. Hạn Lab tự mâu thuẫn trong cùng ô (R32) |
| 6 | 5. QT PHÁP LÝ SẢN XUẤT | I: kiểm pháp lý từng đơn (nguồn gốc, điều kiện SX, điều kiện mua bán, dòng hóa đơn). II: cập nhật và theo dõi hạn giấy tờ | I: 3 bước; II: 4 bước | Hoàn thành | **Không bước nào có người duyệt, không có thời lượng**; mục V, VII trống (R31–R39). Câu hỏi mở ngay đầu sheet (R2). TIẾN ĐỘ DRIVE R190 ghi *còn thiếu pháp lý SX*. Thực tế **chưa hoàn thành** |
| 7 | 6. QT QUẢN LÝ NCC GC | Việc của QLDL: BĐM TP, lấy hóa đơn, LSX và phiếu kho, bán nội bộ giữa công ty, đối chiếu tồn và công nợ (trước ngày 20), thanh toán, mua NL/VTBB tại NCC, hồ sơ pháp lý, hợp đồng, phí phạt, hoa hồng, dự chi | A: 8; B: 2; C: 6 | Hoàn thành (MỤC LỤC R7 tự ghi *chưa gồm đánh giá NCC*) | Khá đủ, có hạn (ngày 5, ngày 20, 7 ngày trước hạn, 25–28 hằng tháng). Bước 4, 5 **QLDL tự duyệt** (R23, R24). Ghi chú dở R21, R34 (*Drive ....*). Bước 8 hồ sơ thanh toán ghi *...* (R27) |
| 8 | 7. QT BĐM THUẾ | Lập BĐM BTP (ĐP NL/BTP), BĐM VTBB (ĐP VTBB), BĐM TP (QLDL) theo luồng pháp lý; QLSX ký; gửi Kế toán theo 3 công ty IDA, ABA, DEGO | 4 phần, 14 bước | Hoàn thành | Đủ người làm. Chỉ có một điểm duyệt chung ở cuối (R41). Mục V trống (R45–R47) |
| 9 | 8. QT QL NLBTP | Tiếp nhận đơn, BĐM, kiểm tồn, dự trù ngày 15, chuyển kho, nhập, xuất, hao hụt, hư hỏng, đối chiếu tồn, khảo sát công thức với NCC (10–14 ngày), mẫu cho tặng, tính giá BTP | 10 nhóm A–J, 38 dòng việc | Hoàn thành | Gần như bước nào cũng có người làm và người duyệt. Còn 5 ghi chú dở: R1, R24, R28, R29, R48. Bước E.4 *nhập kho đổ thu / dư sản xuất* **không có người làm, ghi chờ xây sau** (R48) |
| 10 | 9. QT QL VTBB | Như sheet 8 cho VTBB, thêm cọc nhãn (4 NCC), điều chuyển, bán giữa thương hiệu, khảo sát VTBB với NCC | 10 nhóm A–J, 36 dòng việc | Hoàn thành | Đủ người làm. Cuối sheet tự ghi **4 điểm cần thống nhất trước khi ban hành** (R112). Ghi chú dở R21, R26, R53. Mục V dòng 1 ghi nhầm (R71) |
| 11 | 10. QT QL DVVC | Đặt Grab gửi mẫu: tạm ứng, nhận yêu cầu, phiếu xuất, đặt xe, quyết toán 2 bộ (nội bộ, thuế) | 5 bước | Hoàn thành | **Không bước nào có thời điểm**. Thiếu hạn mức tạm ứng và hạn hoàn ứng (MIC có, tệp không). Ghi chú dở R23, R24 |
| 12 | 11. QT XL SỰ CỐ TRONG SX | Sự cố trước khi có thành phẩm: 5 nhóm (pháp lý, NL/BTP, VTBB, công thức, vận hành NCC); phương án, chứng từ thuế và nội bộ, chi phí, lưu trữ | 8 bước (32 dòng) | Cần kiểm tra lại | **Không có cột Người duyệt.** ĐP TP vừa làm vừa tự kiểm (R29–R50). Không có hạn |
| 13 | 12. QT XL SỰ CỐ SAU SX | Sự cố tại NCC, kho Dr Xanh, khách hàng, vận chuyển: 4 nhóm; phương án, thu hồi, đơn xử lý lại | 8 bước (30 dòng) | Cần kiểm tra lại | **Không có cột Người duyệt.** R1 ghi *đang gộp quy trình xử lý sự cố, cần xem lại*. Phần 5 chép gần nguyên sheet 11 |
| 14 | 14. MẪU BIỂU | Danh mục 33 chứng từ: ai lập, lúc nào, nơi duyệt, nơi nhận, nơi lưu, link | 37 dòng | Cần kiểm tra lại | 3 chứng từ quan trọng **chỉ có tên** (Đơn đặt hàng, Biên bản giao nhận, Biên bản hàng lỗi, R36–R38). Nơi duyệt ghi TNĐP cho hầu hết phiếu, lệch với các quy trình (mục 4) |
| 15 | 16. THUẬT NGỮ, VIẾT TẮT | 60 từ viết tắt | 60 dòng | Hoàn thành | Đủ dùng. Thiếu: TNĐP, CV, NLT, NLNK, BTPR, BTPM, BTPCT, PPT, PĐG, CPNK, KCS, PO, GĐ / CEO / ĐDPL |
| 16 | 17. TT NCC GC | Khung 22 cột cho từng NCC GC (MST, kho, MOQ, thời gian SX, hao hụt, hóa đơn, giao nhận, liên hệ, lưu ý, đánh giá) | 15 NCC | Đang thực hiện | **Chỉ điền tên và một phần MST; 17 cột vận hành trống hết.** MST của Thành Phát và PES trùng nhau (R17, R18). Không có Agama, Nhật Việt, Dego Đồng Tháp (MIC-KQ có) |
| 17 | 18. TT SP | Khung 19 cột cho từng sản phẩm tại từng NCC GC | 1 dòng | Đang thực hiện | **Chỉ 1 dòng** (Hà Long, Chitin 3.6EC, R3); các cột hao hụt, bên chuẩn bị NL / VTBB trống. Còn sót công thức Excel ở tiêu đề (R2) |
| 18 | 19. TIÊU CHÍ ĐÁNH GIÁ NCC GC | 8 nhóm, 18 tiêu chí, 100 điểm, thang xếp loại, chu kỳ 6 tháng | 18 tiêu chí | Cần kiểm tra lại | Khung điểm tốt. Chưa có biểu mẫu chấm, chưa có nguồn số liệu. Khoảng hở: hồ sơ còn hạn 3–6 tháng không có mức điểm (R5); mốc 1%, 3%, 5% chồng nhau (R14) |
| 19 | 20. LƯU TRỮ | Cây thư mục và quy tắc đặt tên tệp | 4 cấp | Đang thực hiện | Chép từ Thu mua (R1, ví dụ *ĐÔNG TÂY*, *DMH0001*), **chưa chỉnh cho Sản xuất** (không có thư mục theo đơn gia công, LSX, BĐM) |
| (thiếu) | 13. Ngưng hợp tác với NCC | Chỉ có tên ở MỤC LỤC R14 | 0 | không ghi | Không có nội dung |
| (thiếu) | 22. Sơ đồ SX và MTCV | MỤC LỤC R23 trỏ tới sheet *SƠ ĐỒ SX & MTCV* | 0 | Cần kiểm tra lại | Sheet không có trong tệp. Mô tả công việc nằm ở một link Drive riêng (V1·C4) |
| (thiếu) | 23. Phân bổ quyền ký | MỤC LỤC R24 ghi *Chưa có* | 0 | Cần kiểm tra lại | Không có nội dung |

---

## 2. Đối chiếu với 9 quy trình của MIC

### 2.1. Bảng ghép

| Tệp | MIC | Phủ tới đâu |
|---|---|---|
| 4. Đơn hàng SX GC, phần A | MIC 1: Quản lý đơn hàng gia công | **Phủ, nhưng chia bước khác tệp.** MIC tách *QLSX duyệt* thành bước riêng (tệp không có bước này) và bỏ bước 4 *Nhập kho và nhận hóa đơn* của tệp (S4 R28–R30). Khi MIC hỏi lại trình tự, phòng đáp *xem quy trình đi* (V12·C2, V11·C2) |
| 4. Đơn hàng SX GC, phần B Hủy đơn | không có | **Bỏ sót.** MIC không có luồng hủy đơn, dù KD hủy đột xuất là nguồn tồn bao bì (MIC-KQ mục 9) |
| 11 và 12. Sự cố trong và sau SX | MIC 2: Xử lý sự cố | **Gộp làm một.** MIC không thấy hai sheet giao việc cho hai người khác nhau: sheet 11 do ĐP TP làm chính (S11 R22–R53), sheet 12 do NV XLSC làm chính (S12 R22–R51) |
| 6. Quản lý NCC GC | MIC 3: Hồ sơ, dữ liệu nhà gia công | Phủ phần chứng từ, công nợ, thanh toán. **Bỏ sót**: bán thành phẩm giữa các công ty nội bộ (S6 R24), mua NL / VTBB tại NCC GC (S6 R29–R30), phí phạt và lãi quá hạn (R34), hoa hồng (R35), dự chi (R37–R38) |
| 3. Khảo sát và tính giá vốn | MIC 4 | Phủ. MIC nắm được quy định mới bỏ cảnh báo biên (V3·C2) mà tệp chưa sửa |
| 2. Khai báo SX | MIC 5 | Phủ luồng duyệt. **Không đụng phần quy tắc mã** và ghi chú *thiếu quy tắc mã đơn* (S2 R1) |
| 9. VTBB | MIC 6 | Phủ. Thời gian cung ứng chuẩn từng loại VTBB, cọc 6 đối tác là số MIC lấy từ tài liệu khác, **không có trong tệp** |
| 8. NL/BTP | MIC 7 | Phủ trình tự (V11·C20). MIC đánh dấu *8/14 bước chưa rõ ai làm*, trong khi tệp đã ghi người làm cho gần hết bước (xem mục 3.2) |
| 1. Làm việc với NCC mới + 19. Tiêu chí | MIC 8: Đánh giá và làm việc với nhà gia công | Gộp hai thứ. Phủ luồng hợp đồng (V5·C2, V9·C17–C19) và thang điểm |
| 10. DVVC (Grab) | MIC 9 | Phủ, MIC còn chi tiết hơn tệp (hạn mức, hoàn ứng) |
| **5. Pháp lý sản xuất** | không có quy trình riêng | **Bỏ sót.** MIC chỉ coi pháp lý là một trong 7 điều kiện duyệt đơn và nhắc *dòng hóa đơn*. Phần II *theo dõi hạn giấy phép, hợp quy, ủy quyền, thuê tên* (S5 R25–R28) không có trong MIC |
| **7. BĐM thuế** | không có quy trình riêng | **Bỏ sót.** MIC có *BĐM 3 tầng* nhưng không có luồng thuế, không biết BĐM thuế lập riêng cho 3 công ty IDA, ABA, DEGO (S7 R51–R61) |
| **13. Ngưng hợp tác NCC** | không có | Cả tệp và MIC đều trống. MIC chỉ có ngưỡng *dưới 60 điểm thì ngưng* (S19 R39) |
| **22. Sơ đồ và mô tả công việc** | MIC dựng bộ máy | MIC tự dựng sơ đồ từ câu hỏi (V1·C3–C19, V6·C12). **Đây là phần MIC làm tốt hơn tệp**, nên chép vào tệp làm sheet 22 |
| **23. Phân quyền ký** | không có | Cả hai đều trống. MIC chỉ có ý *Đại diện pháp luật chỉ ký, không quyết* (V9·C3) |
| 14. Mẫu biểu, 17–18 Thông tin NCC / SP, 20 Lưu trữ | MIC đếm 97 tài liệu, 117 công cụ | MIC có bảng NCC đầy đủ hơn sheet 17 (MOQ, hao hụt, thời gian SX từng nhà, MIC-KQ mục 3). Nguồn là câu trả lời và tài liệu tải lên, **không phải tệp quy trình** |

### 2.2. Nhận xét

- Giả định *câu hỏi MIC chủ yếu để làm rõ tệp quy trình* **chỉ đúng một phần**. Khoảng 20 câu là *kiểm đếm* danh mục công cụ, vị trí của chính MIC (V6·C5–C15, V9·C4–C5, V10·C1–C4, C16–C20); khoảng 15 câu xác nhận hiện trạng (V6, V10). Câu bám vào một bước cụ thể của tệp thì có, nhưng chủ yếu hỏi *ai, kênh nào, công cụ gì*, mà tệp đã có ở các cột Người thực hiện, Hình thức.
- Ngược lại, MIC **thêm được** những thứ tệp không có: tên người cụ thể theo từng NCC GC, khung trách nhiệm 3 tầng (V6·C16), bộ 14 chứng từ thanh toán (V6·C4), phân biệt 3 nghĩa của chữ *Giám đốc* (V6·C8), các điểm nghẽn và khoản tiền ngoài sổ thuế (MIC-KQ mục 12).

---

## 3. Câu hỏi MIC đã làm rõ được gì trong tệp

### 3.1. Chỗ tệp mơ hồ mà câu trả lời đã chốt

| # | Chỗ tệp mơ hồ | Tệp | MIC đã chốt | Câu MIC |
|---|---|---|---|---|
| 1 | 7 mục kiểm đơn chỉ ghi tên bộ phận | S4 R17 | Tên người từng mục: NL/BTP Oanh, VTBB Ly, Giá vốn Hương, Pháp lý Huỳnh, Sự cố Thi, QLDL theo NCC (Thơ, Liên, Khang), QLSX Ngân | V6·C12 |
| 2 | Không có bước *QLSX duyệt đơn*, chỉ ghi *khi đơn được QLSX duyệt* | S4 R17, R26 | QLSX duyệt khi ĐP báo đủ các team, duyệt ở cột duyệt trên Drive Điều phối; ĐP báo qua điện thoại / Zalo | V3·C11, C12, C15; V4·C7 |
| 3 | Gửi đơn NCC có kèm giá không | S4 R26 | Đơn gửi NCC **không ghi giá**; gửi từng đơn, kèm mockup qua Zalo; NCC không ký thì đàm phán lại hoặc đổi NCC | V1·C11; V8·C2–C4 |
| 4 | Ai chịu trách nhiệm khi kiểm sót | S4 R17–R24 | Mỗi team chịu phần mình xác nhận; ĐP chịu việc đôn đốc; QLSX quyết cho đi | V3·C14 |
| 5 | Duyệt trước, cho nợ hồ sơ | không có trong tệp | Có, do QLSX quyết theo từng ca, **chưa có tiêu chuẩn văn bản** | V3·C4; V10·C11 |
| 6 | Kết luận đạt / không đạt và nhịp gửi mẫu | S4 R32 | Lab kết luận; **100% đơn** gửi mẫu; KCS khi kho nhận, Lab khi hàng về kho | V3·C16–C18 |
| 7 | Điều kiện chốt hoàn thành đơn | S4 R32 (*đạt thì chuyển hoàn thành*) | Đủ 3 thứ: kết quả Lab, QLDL báo đã có hóa đơn, Kho ký nhận đủ lượng; chốt xong khóa đơn trên sheet ĐIỀU PHỐI | V8·C6–C9 |
| 8 | Bộ hồ sơ thanh toán ghi *...* | S6 R27 | 14 chứng từ cụ thể | V6·C4 |
| 9 | Ai chịu trách nhiệm số công nợ | S6 R26 | CV QLDL phụ trách NCC chịu trách nhiệm; TN QLDL kiểm lại | V3·C19 |
| 10 | QLSX duyệt mã khai báo bằng gì | S2 R36 | Chỉ duyệt qua Zalo; người khai tự chịu trách nhiệm trùng, sai mã | V12·C3; V3·C8 |
| 11 | Chữ *Giám đốc* ở nhiều bước | S1 R19, R47, R48; S3 R21, R28 | Bước 4.2 và 6.2.4 của sheet 1, các bước sheet 3 là CEO; bước 6.2.5 sheet 1 là Đại diện pháp luật (chỉ ký) | V6·C8; V9·C3 |
| 12 | Ai tạo mã và duyệt đơn xử lý lại | S12 R30–R32 (*lên đơn xử lý lại cho ĐP TP*) | CV Pháp lý - Sự cố tạo mã; duyệt như đơn mới | V3·C5 |
| 13 | Biên bản bàn giao nội bộ (Mẫu 05) lập lúc nào | S1 R49 (*trước khi đặt đơn đầu tiên*) | Sau khi ký nếu có thỏa thuận ngoài hợp đồng; **trước khi ký** nếu người ngoài phòng đi đàm phán | V8·C5; V9·C1 |
| 14 | BĐM TP lập ở đâu, dựa trên gì | S6 R21; S7 R36 | QLDL lập trên Drive QLDL, ghép từ BĐM VTBB và BĐM NL/BTP | V2·C5; V6·C7; V7·C1 |
| 15 | Ai lập, ai ký BĐM BTP | S7 R41 (*QLSX ký*) | ĐP NL/BTP lập, QLSX ký, ĐP NL/BTP chịu trách nhiệm nội dung; công thức lấy từ Drive Lab | V11·C4, C5 |
| 16 | Grab: ai giữ tài khoản, lúc nào quyết toán | S10 R20–R24 (không có thời điểm) | Oanh giữ tài khoản; quyết toán cố định cuối tháng; QLSX ký thay TNĐP | V4·C5, C6, C20; V9·C10–C12 |
| 17 | Đối chiếu tồn lệch thì xử lý sao | S8 R57–R58; S9 R58–R59 | Chứng minh cho NCC, yêu cầu NCC kiểm lại, các ĐP theo đến khi khớp, QLDL in phiếu xác nhận | V1·C18 |
| 18 | Mấy loại đơn | dùng trong tệp, không định nghĩa | 3 loại: TP, BTP, xử lý lại; mỗi loại một mã | V1·C8 |
| 19 | Tên gọi người đứng đầu | S16 R3 chỉ ghi QLSX | QLSX = Trưởng phòng = Trợ lý SX, một người | V1·C3; V6·C1 |

### 3.2. Chỗ MIC đánh dấu *còn trống* nhưng tệp **đã có** (không nên hỏi lại)

| MIC đánh dấu trống | Tệp đã có ở đâu |
|---|---|
| NL/BTP: 8 trong 14 bước chưa rõ ai làm, ai chịu trách nhiệm (MIC-KQ mục 16) | S8 ghi Người thực hiện cho gần hết bước (R21–R70), Người duyệt QLSX cho phần lớn bước có chứng từ. Chỉ bước E.4 (R48) thiếu người làm |
| Thiếu tệp tính giá BTP | Sheet *3.1 Tính lượng NL và giá BTP* trong Drive Xuất nhập tồn NL/BTP, đã Hoàn thành (TIẾN ĐỘ DRIVE R176); biểu mẫu *Bảng giá BTP* (S8 R69) |
| Thiếu mẫu phiếu yêu cầu mua gửi Thu mua / QLDL | *Phiếu đề nghị mua hàng hóa dịch vụ*, Hoàn thành (TIẾN ĐỘ DRIVE R163); nêu ở S8 R34, S9 R31 |
| Chưa rõ tên tệp đối chiếu công nợ | *Drive 4. Công nợ, thanh toán* với 18 sheet (TIẾN ĐỘ DRIVE R110–R127); *Drive 9. Đối chiếu tồn kho tất cả NCC* (S8 R57) |
| Công cụ *Checklist NCC mới* chưa rõ dùng ở đâu | S1 R18, R42, R44, R49; TIẾN ĐỘ DRIVE R61–R65 (Mẫu 01–05) |

### 3.3. Câu MIC hỏi lại thứ tệp đã ghi (phòng đã phàn nàn)

V1·C6, V1·C20, V2·C2, V2·C8, V2·C10, V9·C6, V9·C7, V9·C18, V10·C7, V11·C2, V11·C16, V11·C17, V12·C2. Khoảng 13 câu. Phòng trả lời kiểu *xem quy trình* hoặc *đã có trong quy trình*.

---

## 4. Chỗ tệp và câu trả lời mâu thuẫn

| # | Việc | Tệp nói | Câu trả lời nói | Mức | Ghi chú |
|---|---|---|---|---|---|
| M1 | **Giá vốn thực tế: ai ký, bắt đầu lúc nào** | Bắt đầu *trong ngày nhận LSX từ QLDL*, người duyệt **QLSX** (S3 R35) | Bắt đầu khi **hàng về kho Dr Xanh** (V4·C15); **TN QLDL** ký (V3·C7, V4·C3) | Cao | LSX lập khi NCC báo xong hàng (S6 R23), có thể trước khi hàng về kho. Ảnh hưởng thời điểm Kế toán nhận giá |
| M2 | **Đánh giá NCC GC: chu kỳ và người làm** | **6 tháng/lần** hoặc đột xuất; các bộ phận chấm độc lập, QLSX phê duyệt (S19 R40) | **Theo quý** hoặc khi QLSX yêu cầu; CV QLDL tiến hành (V9·C13); QLDL lưu (V11·C1, V12·C1) | Trung bình | MIC-KQ ghi *thực tế chưa chạy* |
| M3 | **Lab trả kết quả bao lâu** | *BP R&D trả kết quả chậm nhất 2 ngày* và, cùng ô, *test hàm lượng 14 ngày* (S4 R32) | Ngoại dạng 1–2 ngày, hàm lượng 14 ngày (V3·C6); đơn chỉ hoàn thành khi có kết quả Lab (V8·C7) | Cao | Chưa rõ đơn chờ kết quả nào mới chốt. Quyết định độ dài vòng đơn trên ERP |
| M4 | **Ai xử lý sự cố trong sản xuất** | ĐP TP làm chính ở mọi bước và tự là người kiểm tra (S11 R22–R53) | File sự cố do CV Pháp lý - XLSC ghi; ĐP TP chỉ xử lý nhanh khi không ảnh hưởng giá, công nợ (V2·C14; V8·C15–C19; V9·C8, C9) | Cao | Sheet 12 (sau sản xuất) thì khớp: NV XLSC làm chính |
| M5 | **Ai duyệt phương án sự cố** | Sheet 11, 12 **không có cột Người duyệt** | TN QLDL có thẩm quyền, vướng thì QLSX (V2·C15); đơn xử lý lại thì CV XLSC chịu trách nhiệm, cần thì trình TN QLDL (V4·C1) | Cao | Bản phân tích cũ (24/10, H5) còn có ý thứ ba: TNĐP quyết |
| M6 | **Cảnh báo biên lợi nhuận** | Âm biên / biên thấp thì Giá vốn gửi KD xem lại (S3 R32); Drive có sheet *12. Biên giá SX-KD-KH* (TIẾN ĐỘ DRIVE R40) | Sản xuất bỏ cảnh báo biên, KD tự kiểm (V3·C2) | Trung bình | Tệp chưa cập nhật quy định mới |
| M7 | **Ai duyệt hợp đồng NCC mới** | QLDL soạn, tham vấn Pháp lý, P TCKT, Giám đốc rồi **QLSX duyệt, ký nháy** (S1 R47, R48) | CV QLDL lập, **TN QLDL kiểm duyệt**, Pháp lý chung, Kế toán, Giám đốc ký (V5·C2), không nhắc QLSX | Trung bình | Có thể cả hai cùng đúng (TN QLDL rồi QLSX). *Chưa rõ* |
| M8 | **Ai ký các phiếu kho, BĐM** | Sheet 14: *Nơi duyệt* là **TNĐP** cho hầu hết phiếu NL/BTP, VTBB, BĐM BTP, BĐM VTBB, nhập kho TP (S14 R3–R22) | Các quy trình ghi **QLSX** duyệt (S7 R41; S8 R23, R51–R54; S9 R43–R44); V11·C4 QLSX ký BĐM BTP; V4·C6 *có TNĐP thì TNĐP ký* (Grab) | Trung bình | Hôm nay cùng một người (chị Ngân kiêm). Sau bàn giao sẽ thành hai người. ERP phải chọn vai |
| M9 | **Ai khai mã BTP ruột** | Thu mua khai (S2 R20) | *BTP mua, ruột - Oanh khai báo* (TIẾN ĐỘ DRIVE R74); ĐP NL/BTP khai báo trình QLSX (V8·C12) | Thấp | Tự lệch trong tệp |
| M10 | **Khảo sát NL/BTP nhận yêu cầu từ ai** | KD gửi đề nghị khảo sát, trả kết quả cho KD qua Drive (S8 R62–R63) | Nhận từ **Giá vốn**, trả kết quả cho Giá vốn (V11·C3); *KD / cấp trên* (V12·C4) | Thấp | Có thể là hai loại khảo sát (giá và công thức). *Chưa rõ* |
| M11 | **Mẫu 05 bàn giao cho ai** | Triển khai cho Thu mua, KD, P TCKT, Pháp lý, nội bộ SX (S1 R49) | TN QLDL bàn giao cho **Giá vốn**, Giá vốn cập nhật giá cho KD (V4·C4) | Thấp | |
| M12 | **Theo dõi tiến độ NCC** | Kiểm sau **2 ngày làm việc** kể từ gửi đơn; báo cáo trước **16h30** hằng ngày (S4 R27) | *Tùy tình trạng đơn hàng và thời hạn giao* (V8·C1); MIC-KQ ghi *lần 2 trước ngày có hàng 2 ngày* và *báo cáo 16h* | Thấp | Mốc *lần 2* không có trong tệp |
| M13 | **Thời điểm lập hồ sơ thanh toán** | *Trước hạn thanh toán 7 ngày* (S6 R27; S14 R34–R35) | *Khi đến hạn sẽ lập hồ sơ* (V4·C10) | Thấp | |
| M14 | **NCC có cọc nhãn** | 4 NCC: An Nông, Âu Việt, Đại Tâm, Thu Loan (S9 R35) | Cọc trước 2026 với **6 đối tác** chưa có văn bản; thiếu dữ liệu cọc Âu Việt, Đại Tâm, **Basel**, An Nông (MIC-KQ mục 9) | Trung bình | Liên quan tiền |
| M15 | **Trạng thái MỤC LỤC và nội dung sheet** | MỤC LỤC: QT 5, 8, 9 *Hoàn thành* (R6, R9, R10) | S5 R2 còn câu hỏi mở; TIẾN ĐỘ DRIVE R190 *còn thiếu pháp lý SX*; S8 R48 *cần hoàn thiện trước khi ban hành*; S9 R112 *4 điểm cần thống nhất trước khi ban hành* | Cao (cho bàn giao) | Người kế nhiệm tin MỤC LỤC sẽ hiểu sai |

---

## 5. Chỗ vẫn còn khúc mắc sau 13 vòng: 25 câu hỏi lại

Nguyên tắc chọn: chỉ hỏi chỗ tệp **không có** hoặc **tự mâu thuẫn**; mỗi câu trỏ thẳng dòng tệp để phòng khỏi phải tìm lại. Xếp theo mức cần cho ERP và cho bàn giao.

**Nhóm A. Chặn việc dựng ERP**

| # | Chỗ tệp | Câu hỏi đề xuất |
|---|---|---|
| 1 | S2 R1 ghi *Xem lại quy tắc đặt mã đơn đặt hàng, mã đơn xử lý lại, mã đơn sự cố, mã các BĐM*; phần 3 (R40–R69) không có các mã này | Mã đơn TP, đơn BTP, đơn xử lý lại, mã sự cố và mã BĐM (BTP, VTBB, TP) hiện đặt theo quy tắc nào? Xin mỗi loại 2 mã thật đang dùng |
| 2 | S4 nhắc rải rác *Chưa lấy hóa đơn* (R29), *Đã nhận hàng* (R31), *TEST KHÔNG ĐẠT*, hoàn thành (R32), *Chờ thông tin từ KD* (R40), hủy (R37) | Cột trạng thái trên sheet ĐIỀU PHỐI đang có đúng những giá trị nào, theo thứ tự nào? Có trạng thái nào ngoài 6 trạng thái trên không? |
| 3 | S4 R32 ghi *R&D trả kết quả chậm nhất 2 ngày*, cùng ô ghi *test hàm lượng 14 ngày*; V8·C7 cần kết quả Lab để chốt đơn | Đơn TP được chốt hoàn thành khi có kết quả **ngoại dạng** hay phải chờ **hàm lượng**? Nếu chờ hàm lượng, trong 14 ngày đó hàng có được giao cho KD không? |
| 4 | S3 R35: giá vốn thực tế làm *trong ngày nhận LSX*, QLSX duyệt; V4·C15 và V3·C7 nói *hàng về kho Dr Xanh*, TN QLDL ký | Sửa dòng S3 R35 theo bên nào: mốc là *nhận LSX* hay *hàng về kho Dr Xanh*; người duyệt là QLSX hay TN QLDL? |
| 5 | Sheet 11 và 12 không có cột Người duyệt; V2·C15 nói TN QLDL có thẩm quyền | Điền **TN QLDL** vào ô duyệt của bước 4 (lập phương án) và bước 7 (chi phí) ở cả hai sheet có đúng không? Có mức tiền nào bắt buộc phải lên QLSX không? |
| 6 | S11 R22–R53: ĐP TP làm chính và tự kiểm mọi bước; V2·C14 nói CV XLSC ghi file sự cố, ĐP TP chỉ xử lý nhanh | Với sự cố **trong** sản xuất, việc nào ĐP TP tự làm trọn, từ lúc nào chuyển sang CV XLSC? Nếu chuyển, S11 có cần đổi người thực hiện sang NV XLSC như S12 không? |
| 7 | S14 R3–R22 ghi Nơi duyệt là TNĐP; S7 R41, S8 R23–R54, S9 R43 ghi QLSX | Sau khi có Trưởng nhóm Điều phối, những phiếu nào chuyển cho TNĐP ký, những phiếu nào QLSX vẫn ký? |
| 8 | TIẾN ĐỘ DRIVE R3 *đổi Data 1 thì mọi Drive chạy lại*; R192–R200 ghi *Xem lại và chốt Data 1*; R129–R133 thông số VTBB và NL *Chưa bắt đầu* | Data 1 (danh mục gốc) đã chốt chưa, ai chốt, dự kiến ngày nào? ERP sẽ lấy Data 1 làm danh mục gốc nên cần bản chốt |
| 9 | S8 R29 ghi *chưa có danh sách phân công ai chuẩn bị NL/BTP trên từng sản phẩm / NCC*; S18 hai cột *Được chuẩn bị NL*, *Được chuẩn bị VTBB* trống | Có bảng nào ghi theo từng sản phẩm và từng NCC GC: ai chuẩn bị NL, BTP, VTBB (công ty hay NCC) không? Nếu chưa, ai lập và xong trước ngày nào? |
| 10 | S9 R53 *quy trình thuế cho phần hao hụt chưa hoàn thiện, cần Kế toán và Sản xuất thống nhất tỷ lệ hao hụt*; S9 R82 có *Bảng phân loại tỷ lệ hao hụt theo NCC* | Bảng tỷ lệ hao hụt cho phép từng NCC nằm ở tệp nào? Kế toán đã đồng ý dùng bảng đó cho phần thuế chưa? |

**Nhóm B. Quy trình còn trống hoặc dở**

| # | Chỗ tệp | Câu hỏi đề xuất |
|---|---|---|
| 11 | MỤC LỤC R14 *13. Ngưng hợp tác với NCC*, không có sheet | Khi ngưng một NCC GC thì phải làm những việc gì, theo thứ tự nào (thu hồi VTBB và NL tồn, cọc nhãn, đối chiếu tồn và công nợ, thanh lý hợp đồng, nhãn cũ tồn)? Ai quyết ngưng? Lần ngưng gần nhất làm thế nào? |
| 12 | MỤC LỤC R24 *23. Phân bổ quyền ký: Chưa có*; S14 R36–R38 *Đơn đặt hàng, Biên bản giao nhận, Biên bản hàng lỗi* không có người lập, người ký | Ba chứng từ này ai lập, ai ký, ký nhân danh công ty nào trong các công ty nội bộ? |
| 13 | S5 R2 hỏi *duyệt pháp lý đơn hàng TP, còn đơn BTP, đơn xử lý lại, sự cố, mua / khảo sát NL/BTP?*; không bước nào có người duyệt | Pháp lý SX có duyệt cho đơn BTP, đơn xử lý lại, mua NL/BTP không? Nếu có thì kiểm mục nào trong 5 mục R18–R22? Kết quả kiểm pháp lý có cần ai duyệt lại không? |
| 14 | S5 R27: Pháp lý SX *định kỳ* kiểm hạn giấy tờ; S6 R32: **Pháp lý chung** theo dõi hạn, QLDL bổ sung trước 3 tháng (6 tháng nếu công ty sở hữu tên) | Ai là người phát cảnh báo sắp hết hạn: Pháp lý SX hay Pháp lý chung? Bao lâu rà một lần? |
| 15 | S8 R48 *Nhập kho từ đổ thu / dư sản xuất*: không có người làm, *sẽ xây dựng sau* | Hàng dư, đổ thu sau sản xuất hiện ai ghi nhận, dùng phiếu gì, nhập vào kho nào? |
| 16 | S9 R112: *(1) mâu thuẫn ở Mục VIII về nghiệp vụ thuế; (2) ghi chú dở Mục II.3 và VII.1.2; (3) vai trò QLDL có tách biệt với QLSX; (4) bổ sung thời lượng*. Sheet 9 hiện không có Mục VIII | Bốn điểm ở S9 R112 đã chốt chưa? *Mục VIII nghiệp vụ thuế* ứng với mục nào trong bản hiện tại (mục G, H)? |
| 17 | S12 R1 *Đang gộp QT xử lý sự cố, các trường hợp và câu hỏi XLSC, cần xem lại* | Hai quy trình sự cố trong và sau sản xuất sẽ gộp thành một hay giữ hai? Ai chốt, khi nào? |

**Nhóm C. Mâu thuẫn cần chọn một bên**

| # | Chỗ tệp | Câu hỏi đề xuất |
|---|---|---|
| 18 | S19 R40 *6 tháng/lần*, các bộ phận chấm độc lập; V9·C13 *theo quý*, CV QLDL làm | Đánh giá NCC GC chạy theo quý hay 6 tháng? Đã chấm lần nào chưa, bảng điểm để ở đâu? |
| 19 | S1 R47–R48: QLSX duyệt, ký nháy hợp đồng NCC mới; V5·C2: TN QLDL kiểm duyệt | Hợp đồng NCC mới đi qua TN QLDL **rồi** QLSX, hay TN QLDL **thay** QLSX? |
| 20 | S3 R32 vẫn còn bước *âm biên thì gửi KD kiểm lại*; V3·C2 nói bỏ cảnh báo biên | Từ ngày nào KD tự kiểm biên? Có xóa đoạn đó khỏi S3 R32 và bỏ sheet *12. Biên giá* (TIẾN ĐỘ DRIVE R40) không? |
| 21 | S2 R20 ghi Thu mua khai BTP ruột; TIẾN ĐỘ DRIVE R74 ghi *BTP mua, ruột - Oanh khai báo* | Mã BTPR do Thu mua hay ĐP NL/BTP khai? |
| 22 | S9 R35 ghi 4 NCC có cọc nhãn; MIC-KQ ghi 6 đối tác, có Basel | Hiện đang để cọc nhãn ở những NCC nào, số tiền bao nhiêu? Sheet *Quản lý cọc nhãn* (TIẾN ĐỘ DRIVE R162) đã đủ các nhà chưa? |

**Nhóm D. Dữ liệu nền cho bàn giao**

| # | Chỗ tệp | Câu hỏi đề xuất |
|---|---|---|
| 23 | S17 R4–R18: 17 cột vận hành trống; MST Thành Phát và PES cùng là 1801685413 (R17, R18); không có Agama, Nhật Việt, Dego Đồng Tháp | Ai điền sheet Thông tin NCC GC, xong trước ngày nào? Số MOQ, hao hụt, thời gian sản xuất từng nhà đang nằm ở tệp nào để chép sang? MST đúng của PES là gì? |
| 24 | Cột Thời lượng trống ở mọi bước; V4·C9 *chưa có quy định thời gian cho từng team* | Để ERP nhắc việc, mỗi bộ phận xác nhận một đơn mới trong bao lâu thì coi là trễ? Xin một con số mặc định (ví dụ 1 ngày làm việc) |
| 25 | V3·C4, V10·C11: duyệt trước, cho nợ hồ sơ dựa vào kinh nghiệm QLSX; tệp không có bước này | Trong 7 điều kiện, điều kiện nào từng được cho nợ, nợ tối đa bao lâu, ai theo dõi đến khi đủ? (để người kế nhiệm có luật thay cho kinh nghiệm) |

---

## 6. Rủi ro bàn giao

### 6.1. Thứ chỉ có trong đầu người

| Rủi ro | Nguồn | Người kế nhiệm vướng ở đâu |
|---|---|---|
| Quyết *duyệt trước, cho nợ hồ sơ* hoàn toàn theo kinh nghiệm QLSX | V3·C4; V10·C11 | Không biết đơn nào được cho đi khi thiếu giấy tờ. Hoặc chặn hết (chậm đơn), hoặc cho hết (rủi ro pháp lý) |
| Chính sách riêng từng NCC GC: điều kiện bắt buộc, điều kiện thỏa thuận, nhà dự phòng | V6·C17, C19; S17 cột *Lưu ý khi làm việc* trống | Không biết nhà nào nhận VTBB mang sang, nhà nào từ chối ký đơn, ký đề nghị thanh toán |
| Thỏa thuận ngoài hợp đồng: chiết khấu ngoài, hoa hồng trả tiền mặt qua cá nhân được chỉ định | S6 R35; V6·C19; MIC-KQ mục 12 | Không biết khoản nào phải chi, chi cho ai, vào tháng nào. Đây là chỗ nhạy cảm, nên người chủ xem riêng với Kế toán trưởng |
| Thẩm quyền xử lý sự cố, mức tiền | S11, S12 không có cột duyệt; V2·C15; V6·C3 | Không biết phương án nào tự quyết, phương án nào phải trình |
| Kiêm nhiệm nhiều ghế | V1·C12 (QLSX kiêm TNĐP); V1·C16 (Oanh kiêm ĐP TP và ĐP NL/BTP); bộ máy MIC-KQ (Huỳnh kiêm TN QLDL và Pháp lý); V2·C20 (Hương vắng thì QLSX làm) | Người kế nhiệm nhận cùng lúc ghế QLSX, TNĐP và người làm thay Giá vốn |
| Tên người lạ hoặc đã nghỉ còn đứng ở chỗ phụ trách | TIẾN ĐỘ DRIVE R136–R140, R189 (Mr Toàn, đã nghỉ theo V1·C13); Ms Trang, Ms Quyên (R61–R65, R135–R171), Ms Trinh (S6 R24), Mr Phú (R150) không có trong bộ máy MIC | *Chưa rõ* những người này thuộc bộ phận nào; không biết hỏi ai khi Drive lỗi |

### 6.2. Thứ chỉ có ở Drive, Zalo, Signal, app

| Rủi ro | Nguồn | Người kế nhiệm vướng ở đâu |
|---|---|---|
| **QLSX là chủ sở hữu mọi Drive** | V1·C20; V10·C7 | Phải chuyển quyền sở hữu trước 31/12, nếu không tài khoản chị Ngân bị khóa là mất quyền quản trị |
| Mọi Drive phụ thuộc *Data 1*, Data 1 chưa chốt | TIẾN ĐỘ DRIVE R3, R192–R200 | Sửa một cột danh mục là làm hỏng liên kết ở các Drive khác |
| 138 trên 196 sheet Drive còn *Đang thực hiện*; Drive Giá vốn và Drive QLDL chưa xong sheet nào; *Drive 5. HSTT chưa có* (R128); *Drive 5 báo cáo: chưa có quyền truy cập* (R59) | TIẾN ĐỘ DRIVE | Nhận một hệ bảng tính đang dựng dở, không có hướng dẫn thao tác (V10·C15) |
| Khoảng 40–50 nhóm Zalo (ước, từ mục VII của 10 sheet, 67 dòng có trùng); *nhóm Zalo QLDL chưa cập nhật* (R187); nhiều thương hiệu *chưa có nhóm* (S9 R22, R25) | các mục VII; TIẾN ĐỘ DRIVE R187 | Lịch sử duyệt mã, duyệt đơn nằm trong tin nhắn Zalo (V12·C3, V3·C15). Không chuyển quyền trưởng nhóm thì mất dấu vết |
| Giá vốn gửi Kế toán bằng ảnh chụp qua **Signal** | S3 R35; V4·C17 | Lịch sử giá vốn thực tế đã gửi nằm trong một nhóm chat |
| Tài khoản Grab đứng tên công ty, Oanh giữ, tạm ứng cá nhân | S10 R20, R24; V4·C20 | Oanh nghỉ thì mất đường đặt xe và khoản tạm ứng đang treo |
| Mô tả công việc chỉ ở một link Drive, không có trong tệp | V1·C4; MỤC LỤC R23 | Tệp bàn giao thiếu sheet 22 |
| Bản gốc chứng từ ở P TCKT, Sản xuất chỉ giữ bản scan | S1 R48; V10·C7 | Cần biết bản scan nằm ở thư mục nào; sheet 20 Lưu trữ chưa chỉnh cho Sản xuất |
| Số liệu NCC (MOQ, hao hụt, thời gian SX, lưu kho) nằm ở MIC và tài liệu rời, **không ở sheet 17, 18** | S17, S18 trống; MIC-KQ mục 3 | Không có một bảng tra cứu nhà gia công |

### 6.3. Phạm vi bàn giao chưa chốt

V1·C10: nếu kịp app thì bàn giao quy trình mới kèm dữ liệu; nếu không kịp thì bàn giao quy trình, nhân sự, công việc đang áp dụng và hiện trạng. Còn 8 tuần tới 31/12/2026. Thực tế nên chuẩn bị **phương án không kịp app**: tức là tệp quy trình này phải tự đứng được, sửa xong các chỗ ở mục 4 và 5.

---

## 7. Gợi ý cho ERP

- **Đơn gia công** là thực thể gốc: 3 loại (TP, BTP, xử lý lại, V1·C8), gắn NCC GC, thương hiệu đặt, **công ty sở hữu pháp lý** và công ty nhận hóa đơn (S5 R22; MIC-KQ mục 6). Đơn xử lý lại trỏ về sự cố gốc (V3·C5).
- **Xác nhận 7 bộ phận chạy song song** trên cùng một đơn (S4 R17–R24; V6·C12), mỗi nhánh có người, giờ xác nhận, ghi chú; QLSX duyệt sau cùng; cho phép *duyệt có điều kiện* ghi rõ điều kiện đang nợ và hạn (V3·C4).
- **Bộ trạng thái đơn** tối thiểu, dựng từ S4: tiếp nhận, chờ xác nhận, chờ QLSX duyệt, đã gửi NCC, đang sản xuất, có hàng chưa lấy hóa đơn, đã nhận hàng, chờ kết quả Lab, hoàn thành (khóa), test không đạt, chờ thông tin KD, hủy. Phải chốt bằng câu hỏi 2 và 3 trước.
- **BĐM 3 tầng × 2 bản**: BĐM BTP (theo 1.000 L / kg), BĐM VTBB và BĐM TP (theo 1 đơn vị), mỗi tầng có bản nội bộ và bản thuế (S7 R6, R41); có trạng thái duyệt và phiên bản, vì *BĐM bắt buộc đổi theo thực tế* (S8 R22; S9 R21).
- **Kho tại NCC GC** là kho thật trên ERP (S2 R69 *KHO NCC*, *KHO NCCXL*), theo dõi NL, BTP, VTBB của từng công ty nội bộ. Phiếu kho cần cặp *công ty bán, công ty mua* để sinh đúng phiếu nội bộ hay phiếu thuế (S8 R40–R41; S9 R43, R46).
- **Danh mục mã** theo đúng quy tắc S2 R40–R69 (NLNK, NLT, NA, BTPR, BTPNK, BTPCT, N, C, NAP, TH, PPT, PĐG, CPNK, HH...), có luồng khai, QLSX duyệt, Kế toán xác nhận, thay cho nhóm Zalo (V8·C10–C14). Đây là Data 1, nên **số hóa trước** để gỡ phụ thuộc *đổi Data 1 là Drive chạy lại*.
- **Phiếu duyệt giá 3 mức** (giá vốn nội bộ, giá vốn tính thuế, giá KD bán) gắn với đơn (S4 R24); giá vốn thực tế sau sản xuất gắn LSX (S3 R35). Ẩn giá theo vai trò, vì đơn gửi NCC không có giá (V1·C11) và *giá bảo mật giữa các thương hiệu* (TIẾN ĐỘ DRIVE R142, R172).
- **Hồ sơ NCC GC**: hợp đồng, phụ lục, bảng giá, giấy phép, hồ sơ pháp lý sản phẩm, mỗi thứ có ngày hết hạn; nhắc trước 3 tháng, 6 tháng nếu công ty sở hữu tên (S6 R32, R33). Làm sớm, vì đơn đã gửi mới phát hiện thiếu giấy phép là sự cố có thật (MIC-KQ mục 10).
- **Sự cố**: phân loại theo 5 nhóm trong sản xuất và 4 nhóm sau sản xuất (S11 R24–R28; S12 R24–R27), có người làm, người duyệt, chi phí, bên chịu; sinh biên bản cấn trừ công nợ (S11 R52).
- **Đối chiếu tháng với NCC**: tồn kho và công nợ, hạn trước ngày 20 tháng sau (S6 R26; S14 R30), so Drive / MISA / số NCC. Đặt sau cùng vì còn phụ thuộc MISA.
- **Đánh giá NCC** dùng sẵn khung 100 điểm của S19; lấy điểm từ dữ liệu ERP (tỷ lệ lỗi từ sự cố, trễ hạn từ đơn, hao hụt từ đối chiếu) thay vì chấm tay.
- **Thứ tự đề xuất**: (1) danh mục mã và NCC GC; (2) đơn gia công + 7 xác nhận + trạng thái; (3) BĐM và phiếu kho tại NCC; (4) hồ sơ, hạn pháp lý; (5) sự cố; (6) đối chiếu, thanh toán, đánh giá NCC.
