# Phòng Sản xuất: tài liệu gộp khảo sát MIC và tệp quy trình bàn giao

| | |
|---|---|
| Ngày | 06/11/2026 |
| Nguồn 1 | Khảo sát MIC (Make It Clear), *Khảo sát hiện trạng Phòng Sản xuất, trả lời chung*, 13 vòng, 177 câu hỏi đáp đọc được, trang kết quả MIC. Chị Ngân duyệt câu trả lời |
| Nguồn 2 | Tệp quy trình bàn giao Excel `qtsx.xlsx`, 20 sheet, MỤC LỤC cập nhật 14/8/2026 |
| Luật gộp | **MIC là chuẩn** (người chủ chốt). Hai nguồn lệch thì nội dung chính viết theo MIC; bản của tệp ghi ở ô *Mâu thuẫn* và ở mục 9 |
| Đọc gì trước | Mục 1 (đọc nhanh) và mục 9 (sổ mâu thuẫn) |
| Trạng thái | Nháp. Chỗ chưa chắc ghi *chưa rõ* |
| Bản dễ đọc | Muốn hiểu logic từng quy trình bằng lời thường, không viết tắt: đọc [giai-thich-quy-trinh-san-xuat.md](giai-thich-quy-trinh-san-xuat.md) |

## Mục lục

1. [Đọc nhanh](#1-đọc-nhanh)
2. [Bảng tra nguồn](#2-bảng-tra-nguồn) (nhãn nguồn, ký hiệu sheet, từ viết tắt)
3. [Bộ máy và người phụ trách](#3-bộ-máy-và-người-phụ-trách)
4. [Các bên ngoài phòng và các nhà gia công](#4-các-bên-ngoài-phòng-và-các-nhà-gia-công)
5. [Từng quy trình](#5-từng-quy-trình)
   - 5.1 Làm việc với nhà gia công mới
   - 5.2 Khai báo mã
   - 5.3 Khảo sát và tính giá vốn
   - 5.4 Quản lý đơn hàng gia công (xương sống)
   - 5.5 Pháp lý sản xuất
   - 5.6 Quản lý nhà gia công (hồ sơ, công nợ, thanh toán)
   - 5.7 Bảng định mức thuế
   - 5.8 Nguyên liệu và bán thành phẩm
   - 5.9 Vật tư bao bì
   - 5.10 Vận chuyển (Grab)
   - 5.11 Sự cố trong sản xuất
   - 5.12 Sự cố sau sản xuất
   - 5.13 Ngưng hợp tác với nhà gia công
   - 5.14 Sơ đồ và mô tả công việc
   - 5.15 Phân quyền ký hồ sơ
6. [Danh mục](#6-danh-mục) (từ ngữ, mã khai báo, biểu mẫu, công cụ)
7. [Tiền, thuế, chứng từ](#7-tiền-thuế-chứng-từ)
8. [Đánh giá](#8-đánh-giá) (độ sẵn sàng bàn giao, rủi ro, gợi ý ERP)
9. [Sổ mâu thuẫn và câu đã trả lời](#9-sổ-mâu-thuẫn-và-câu-đã-trả-lời)
10. [Câu cần hỏi lại](#10-câu-cần-hỏi-lại)

---

## 1. Đọc nhanh

- **DEGO không tự sản xuất.** Toàn bộ hàng gia công tại khoảng 12 nhà máy ngoài, gọi là NCC GC (nhà cung cấp gia công). Phòng lo đặt hàng, cấp nguyên liệu và bao bì, theo dõi, kiểm chất lượng, tính giá vốn, làm hồ sơ thanh toán. Quy mô khoảng 42 đơn thành phẩm mỗi tháng [MIC].
- **Một đơn chỉ đi khi đủ 7 bộ phận xác nhận và Quản lý sản xuất duyệt** [MIC V6·C12, V3·C11]. Đơn gửi nhà gia công không ghi giá [MIC V1·C11].
- **Tệp bàn giao có 12 quy trình, MIC dựng 9.** MIC gộp hai quy trình sự cố làm một. MIC bỏ sót 4 phần: hủy đơn, pháp lý sản xuất, bảng định mức thuế, và phần mua hàng, hoa hồng, dự chi của QLDL. Ba mục 13 Ngưng hợp tác, 22 Sơ đồ, 23 Phân quyền ký thì cả hai nguồn đều trống.
- **17 mâu thuẫn giữa MIC và tệp, đã viết theo MIC.** Lớn nhất: ai ký giá vốn thực tế; đánh giá nhà gia công theo quý (MIC) hay 6 tháng (tệp); Lab trả kết quả; ai xử lý sự cố trong sản xuất; bỏ cảnh báo biên lợi nhuận; ai duyệt hợp đồng nhà gia công mới. Thêm 3 chỗ tệp tự mâu thuẫn mà chưa ai trả lời.
- **Có 8 chỗ chỉ cần sửa tệp cho khớp MIC, không phải hỏi lại phòng** (mục 10).
- **Còn 16 câu thật sự phải hỏi.** Hai câu chặn việc dựng ERP: quy tắc đặt mã đơn hàng và danh sách trạng thái đơn. Cả hai nguồn đều không có.
- **Tệp chưa đủ để bàn giao.** Cột *Thời lượng* trống ở mọi bước. Hai sheet sự cố không có cột người duyệt. Sheet thông tin nhà gia công và thông tin sản phẩm gần như trống. MỤC LỤC ghi *Hoàn thành* cho cả những quy trình còn ghi chú *chưa ban hành*.
- **Rủi ro bàn giao lớn nhất nằm ngoài tệp**: chị Ngân là chủ mọi Drive; lịch sử duyệt nằm trong hơn 40 nhóm Zalo và Signal; việc *duyệt trước, cho nợ hồ sơ* chỉ dựa vào kinh nghiệm của chị Ngân [MIC V1·C20, V10·C11].
- **Người chủ cần quyết 4 việc**: có chuẩn bị phương án bàn giao *không kịp app* không; đặt hạn mặc định cho các bộ phận; tuyển Trưởng nhóm Điều phối; xem riêng với Kế toán trưởng các khoản ngoài hợp đồng (mục 10.3).
- **Gợi ý ERP**: số hóa trước danh mục mã và hồ sơ nhà gia công, rồi đến đơn gia công có 7 nhánh xác nhận song song (mục 8.3).

---

## 2. Bảng tra nguồn

### 2.1. Nhãn nguồn

| Nhãn | Nghĩa |
|---|---|
| `[MIC]` | Trang kết quả MIC (bản tóm), không có số câu |
| `[MIC V3·C14]` | Khảo sát MIC, vòng 3, câu 14 |
| `[Tệp S4 R32]` | Tệp bàn giao, sheet *4. QT QL ĐƠN HÀNG SX GC*, dòng 32 |
| *(chỉ có ở tệp)* | Ý chỉ có ở tệp bàn giao; MIC không nói tới, chưa được phòng xác nhận lại qua MIC |
| **Theo MIC** | Hai nguồn lệch nhau; nội dung chính đã viết theo MIC |
| **Tệp bổ sung** | Tệp có chi tiết MIC không có, không mâu thuẫn |
| **Chưa ai trả lời** | Cả hai nguồn đều không có, hoặc tệp tự mâu thuẫn mà MIC không đụng tới |

### 2.2. Ký hiệu sheet của tệp

| Ký hiệu | Sheet | Ký hiệu | Sheet |
|---|---|---|---|
| ML | MỤC LỤC | S8 | 8. QT QL NL/BTP |
| TĐ | TIẾN ĐỘ DRIVE | S9 | 9. QT QL VTBB |
| S1 | 1. QT LÀM VIỆC VỚI NCC MỚI | S10 | 10. QT QL DVVC (Grab) |
| S2 | 2. QT KHAI BÁO SX | S11 | 11. QT XL SỰ CỐ TRONG SX |
| S3 | 3. QT KHẢO SÁT VÀ TÍNH GIÁ VỐN | S12 | 12. QT XL SỰ CỐ SAU SX |
| S4 | 4. QT QL ĐƠN HÀNG SX GC | S14 | 14. MẪU BIỂU |
| S5 | 5. QT PHÁP LÝ SẢN XUẤT | S16 | 16. THUẬT NGỮ, VIẾT TẮT |
| S6 | 6. QT QUẢN LÝ NCC GC | S17 | 17. TT NCC GC |
| S7 | 7. QT BĐM THUẾ | S18 | 18. TT SP |
| | | S19 | 19. TIÊU CHÍ ĐÁNH GIÁ NCC GC |
| | | S20 | 20. LƯU TRỮ |

Lưu ý khi mở tệp: số bước như `4.1` đã bị Excel đổi thành ngày (`2026-01-04` là bước 4.1, `2026-02-05` là bước 5.2). Bài này ghi lại đúng số bước.

### 2.3. Từ viết tắt dùng nhiều

| Viết tắt | Nghĩa |
|---|---|
| NCC GC / NCC | Nhà máy gia công / đơn vị bán NL, BTP, VTBB (không gia công) [MIC V1·C9] |
| NL, BTP, TP, HH | Nguyên liệu; Bán thành phẩm (phần ruột đã phối); Thành phẩm; Hàng hóa (mã thành phẩm trên MISA) |
| VTBB | Vật tư bao bì |
| BĐM | Bảng định mức. Có 3 tầng BTP, VTBB, TP; mỗi tầng có bản nội bộ và bản thuế |
| LSX | Lệnh sản xuất |
| PO | Đơn đặt hàng gửi nhà gia công |
| QLSX | Quản lý sản xuất = Trưởng phòng = Trợ lý SX, cùng một người (chị Ngân) [MIC V1·C3] |
| TNĐP | Trưởng nhóm Điều phối (đang trống) |
| ĐP TP, ĐP NL/BTP, ĐP VTBB | Chuyên viên Điều phối thành phẩm (tên chính thức: CV Điều phối SX [MIC V1·C7]); Điều phối NL/BTP; Điều phối VTBB |
| QLDL, CV QLDL, TN QLDL | Nhóm Quản lý dữ liệu; Chuyên viên Quản lý hồ sơ SX và dữ liệu NCC GC; Trưởng nhóm QLDL [MIC V1·C4] |
| XLSC, CV XLSC | Xử lý sự cố; Chuyên viên Pháp lý - Xử lý sự cố |
| KD | Kinh doanh = các thương hiệu nội bộ [MIC V1·C2] |
| P TCKT | Phòng Tài chính Kế toán |
| GVSX, GVKD | Giá vốn sản xuất; Giá vốn kinh doanh |
| KCS | Kiểm tra chất lượng khi nhận hàng (Kho làm) |
| MOQ | Số lượng đặt tối thiểu |
| ĐDPL | Đại diện pháp luật |

---

## 3. Bộ máy và người phụ trách

### 3.1. Sơ đồ (theo MIC)

```
Giám đốc (CEO quyết định; Đại diện pháp luật chỉ ký chứng từ)
└── QLSX = Trưởng phòng: Phạm Khánh Ngân (bàn giao trước 31/12/2026)
    ├── Giá vốn và Xử lý dữ liệu: Hương
    ├── Nhóm Điều phối: Trưởng nhóm TRỐNG, chị Ngân kiêm
    │   ├── ĐP TP: Nguyễn Thị Phương Thảo · Lê Mỹ Ngọc · Đào Thị Thúy Oanh
    │   ├── ĐP NL/BTP: Đào Thị Thúy Oanh (kiêm ĐP TP)
    │   └── ĐP VTBB: Ly (việc chung) · Tiên (Hà Long) · An (các nhà còn lại)
    └── Nhóm QLDL: Trưởng nhóm Trần Ngọc Huỳnh (kiêm Pháp lý)
        ├── CV QLDL: Lê Thị Trúc Thơ · Hồ Thị Diệu Liên · Trần Phước Hoàng Khang
        └── CV Pháp lý - Xử lý sự cố: Nguyễn Ngọc Bảo Thi
```
Nguồn: [MIC V1·C3, C12–C16, C19; V2·C20; V6·C12, C14]. Mr Toàn đã nghỉ [MIC V1·C13]. Phòng không có Kế toán sản xuất; hồ sơ quyết toán do nhóm QLDL làm [MIC V1·C5].

**Khung trách nhiệm 3 tầng do phòng tự đưa ra** [MIC V6·C16]: chuyên viên chịu trách nhiệm trực tiếp phần mình; Trưởng nhóm kiểm tra cuối và gỡ chỗ chuyên viên không làm được; QLSX duyệt đơn và gỡ chỗ Trưởng nhóm vướng. Khi hỏi *ai chịu trách nhiệm cuối*, dùng khung này.

### 3.2. Vị trí, người, việc chính

| Vị trí | Người | Việc chính | Làm thay khi vắng | Nguồn |
|---|---|---|---|---|
| QLSX | Ngân | Duyệt đơn; duyệt mã khai báo qua Zalo; ký BĐM BTP, phiếu duyệt giá, biên bản đối chiếu; chủ sở hữu mọi Drive và cấp quyền; quyết *duyệt trước, cho nợ hồ sơ*; kiêm TNĐP | Không có người thay | [MIC V1·C20, V3·C4, V12·C3, V11·C4, V6·C2] |
| Giá vốn và Xử lý dữ liệu | Hương | Nhận và phân loại yêu cầu của KD; khảo sát giá vốn; kiểm giá trước khi duyệt đơn; giá vốn thực tế sau sản xuất; chuẩn hóa dữ liệu gốc. Việc tính biên lợi nhuận sẽ giao cho KD | QLSX (vắng trên 3 ngày) | [MIC V3·C2, V2·C20] |
| TNĐP | Trống, chị Ngân kiêm | Báo cáo Trưởng phòng, phối hợp KD; sẽ ký thay QLSX một số hồ sơ, ví dụ Grab | (không áp dụng) | [MIC V1·C12, V4·C6, V6·C14] |
| ĐP TP | Thảo, Ngọc, Oanh, chia theo nhà gia công (mục 4.2) | Tiếp nhận đơn, kiểm đủ thông tin, tổng hợp 7 xác nhận, lập và gửi PO, theo dõi tiến độ, nhận hàng, gửi mẫu Lab, chốt hoàn thành, xử lý nhanh sự cố. Oanh giữ tài khoản Grab. Khai báo mã kho, công ty nội bộ, khoản mục chi phí *(chỉ có ở tệp)* [Tệp S2 R35] | Người trong nhóm hỗ trợ | [MIC V1·C14, V2·C1–C3, C7, V4·C20] |
| ĐP NL/BTP | Oanh | Khảo sát NL/BTP, BĐM BTP, dự trù, mua hoặc điều chuyển, đề xuất phối, theo dõi phối, hao hụt, xuất nhập tồn, tính giá BTP | Giá vốn | [MIC V1·C16, V3·C3, V9·C2] |
| ĐP VTBB | Ly, Tiên, An | Kế hoạch cung ứng VTBB, kiểm BĐM VTBB trên đơn, tồn kho và tài sản ở nhà gia công (khuôn, trục in), khai báo mã VTBB, cọc nhãn | (chưa rõ) | [MIC V1·C15, V3·C1, V1·C17] |
| TN QLDL | Huỳnh | Kiểm cuối số công nợ; ký giá vốn thực tế; duyệt hợp đồng nhà gia công mới; thẩm quyền xử lý sự cố; bàn giao nội bộ sau khi ký với nhà gia công mới; kiêm Pháp lý (1 trong 7 bộ phận duyệt đơn) | Không có người thay | [MIC V3·C19, V3·C7, V5·C2, V2·C15, V4·C4, V6·C12] |
| CV QLDL | Thơ, Liên, Khang, chia theo nhà gia công | BĐM TP, LSX, phiếu kho, lấy hóa đơn, đối chiếu tồn và công nợ, hồ sơ thanh toán, hợp đồng, lấy chữ ký và dấu của nhà gia công | (chưa rõ) | [MIC V1·C19, V2·C13, V4·C10, V6·C7] |
| CV Pháp lý - Xử lý sự cố | Bảo Thi | Tiếp nhận, phân loại, ghi file sự cố; tạo mã đơn xử lý lại; theo dõi đến khi xong | (chưa rõ) | [MIC V1·C13, V2·C14, V3·C5, V8·C15–C19] |

**Mô tả công việc chi tiết** nằm ở một link Drive riêng mà phòng đã gửi [MIC V1·C4]. Link này không có trong tệp bàn giao: sheet 22 mà MỤC LỤC trỏ tới không có trong tệp [Tệp ML R23].

**Tên người trong tệp nhưng không có trong bộ máy MIC** *(chỉ có ở tệp)*: Ms Trang, Ms Quyên (dựng Drive VTBB, Checklist NCC mới) [Tệp TĐ R61–R65, R135–R171]; Ms Trinh, Pháp lý làm hợp đồng mua bán [Tệp S6 R24]; Mr Phú [Tệp TĐ R150]. *Chưa rõ* những người này thuộc bộ phận nào.

---

## 4. Các bên ngoài phòng và các nhà gia công

### 4.1. Các bên làm việc cùng phòng

| Bên | Đưa cho Sản xuất | Nhận từ Sản xuất | Nguồn |
|---|---|---|---|
| KD (IDA, ABA, BamBoo, Dr Xanh, N2SBIO, Dego Agrochem) | Yêu cầu đặt hàng; dự trù hằng tháng (riêng ABA chỉ gửi đơn); quyết định phía KD mặc định đã được duyệt | Tiến độ, giá vốn khảo sát, tồn kho, kế hoạch sản xuất | [MIC V1·C2, V6·C11] |
| Thiết kế | Mockup bao bì; khai báo mã HH | | [MIC V3·C1]; [Tệp S2 R30] |
| R&D / Lab (ngoài phòng) | Công thức kỹ thuật (qua Drive Lab); kết quả kiểm; **kết luận đạt / không đạt**; là đầu mối duy nhất với trung tâm kiểm nghiệm ngoài | Mẫu kiểm (bộ phận nào cần thì tự gửi) | [MIC V3·C9, C10, C16; V6·C6, C10; V11·C5] |
| Kho Dr Xanh, Logistics | Lịch nhận hàng, biên bản giao nhận, kết quả KCS | Báo cáo hằng ngày các đơn chưa xong | [MIC V1·C6, V10·C1]; [Tệp S4 R27, R31] |
| Thu mua | Kết quả mua NL, VTBB | Yêu cầu mua, làm theo quy trình Thu mua | [MIC V2·C19] |
| P TCKT | Quyền xem MISA; hóa đơn nháp; xác nhận khai báo mã | Chứng từ giao nhận bản cứng trong ngày; hồ sơ thanh toán; giá vốn | [MIC]; [Tệp S6 R24] |
| Pháp lý công ty (Pháp lý chung) | Hồ sơ đăng ký sản phẩm, hợp đồng thuê tên, hợp đồng nội bộ; theo dõi giấy tờ sắp hết hạn | Hồ sơ pháp lý nhà gia công do QLDL thu | [MIC]; [Tệp S6 R32] |
| Nhà máy Dego / Khối kỹ thuật | BOM, BĐM, tiêu chuẩn kỹ thuật, cấp số lô | | [MIC] |
| Ban Giám đốc | Chủ trương, kế hoạch kinh doanh | Báo cáo, cảnh báo rủi ro | [MIC] |

### 4.2. Hồ sơ từng nhà gia công (hợp nhất)

Người phụ trách theo nhà [MIC V1·C14, C15, C19]. Tên pháp lý và mã số thuế (MST) lấy từ tệp [Tệp S17 R4–R18] *(chỉ có ở tệp)*.

| Nhà gia công | Tên pháp lý, MST | Mặt hàng, nơi | ĐP TP / VTBB / QLDL | Vận hành | Vướng chứng từ | Ghi chú thêm từ tệp |
|---|---|---|---|---|---|---|
| **Hà Long** | CTCP Hóa chất Nông nghiệp Hà Long, 1100839224 | Thuốc BVTV, KCN Thái Hòa, Long An | Ngọc / Tiên / Liên | Tối thiểu 10 thùng; phối BTP tối thiểu 500L / 1.000L; hao hụt 0,3%; sản xuất 5–14 ngày; có app xem tiến độ. Hay lỗi BTP, mất VTBB, đóng sai thùng; túi cuộn hao hụt tới 23% [MIC] | Chỉ ký hợp đồng nguyên tắc; PO làm lùi, NV KD ký dấu treo; từ chối đề nghị thanh toán [MIC] | Báo số lượng cụ thể; tin nhắn tự động báo có hàng kèm công nợ [Tệp S4 R29]. Có phí lưu kho [Tệp S8 R59]. Đối chiếu giá riêng cho hàng Hà Long sở hữu pháp lý [Tệp TĐ R95, R100] |
| **Yamato** | TNHH SX TM Yamato VN, 1101865347 | Thuốc BVTV, Long An | Ngọc / An / Thơ | Sản xuất 3–5 ngày; hao hụt ±2% lỏng, ±3,5% bột; không đóng túi 10–15g; đơn dưới 500kg phải ghép [MIC] | Từ chối PO có giá; xác nhận công nợ qua Zalo [MIC] | Bắt buộc đủ VTBB, NL mới gửi đơn; gửi PO dạng PDF theo mẫu Yamato [Tệp S4 R26] |
| **Thái Nông** | TNHH Thái Nông, MST chưa có | Thuốc BVTV, 1 sản phẩm (Acodyl) | Oanh / An / Thơ | Tối thiểu 25 thùng; nhận VTBB mang sang [MIC] | Hợp đồng phân phối không tên hàng, giá, số lượng; từ chối PO và đề nghị thanh toán; một phần trả tiền mặt; không tách đối chiếu tồn theo công ty [MIC] | |
| **Âu Việt** | CTCP Phân bón Quốc tế Âu Việt, 6300230407 | Phân bón, Hậu Giang | Oanh / An / Thơ | Sản xuất 7–10 ngày; nhà gia công giao tận nơi [MIC] | Hợp đồng không giá; công ty phải tự soạn đề nghị thanh toán, đối chiếu [MIC] | Có cọc nhãn [Tệp S9 R35] |
| **An Nông** | TNHH Tập đoàn An Nông, 1101724106 | Thuốc BVTV, Long An | Thảo / An / Khang | Tối thiểu 30 thùng; sản xuất 7–10 ngày; VTBB gửi mẫu duyệt trước [MIC] | Không làm PO, đề nghị thanh toán, xác nhận công nợ; khuyến mãi hàng 0đ rồi xuất hóa đơn giá trung bình [MIC] | Có cọc nhãn [Tệp S9 R35]; khảo sát VTBB gửi 11 bộ (nhà khác 4–5 bộ) [Tệp S9 R64] |
| **Đại Tâm** | 3 pháp nhân: Real Chemical; Sustainable Development S.U.D; Prima - Pháp - Châu Âu | Phân và thuốc, Long An | **chưa có ĐP TP** / An / Liên | Sản xuất 10–12 ngày [MIC] | Chỉ ký khi công ty tự soạn sẵn [MIC] | Có cọc nhãn [Tệp S9 R35] |
| **Basel** | TNHH Basel Thụy Sĩ, 1101742391 | Phân và thuốc, Đức Hòa, Long An | Thảo / An / Khang | 5–7 ngày; 200–250 thùng lỏng hoặc 100–130 thùng bột mỗi ngày. Từ 01/2024 hết giấy phép SX thuốc BVTV, phải mua NL/BTP của Basel đi đóng (trừ Chitin 3.6EC) [MIC] | Chỉ ký khi tự soạn sẵn; nhãn cũ tồn chưa có phương án [MIC] | Có phí lưu kho [Tệp S8 R59] |
| **Niềm Tin Việt** (NTV) | TNHH SX TM PT Niềm Tin Việt, MST chưa có | Phân bón, Tháp Mười, Đồng Tháp | Thảo / An / Thơ | Có đơn thì báo Oanh kiểm NL, phụ gia; nhà máy Dego cấp số lô [MIC] | Chỉ ký khi tự soạn sẵn [MIC] | ĐP NL/BTP lập LSX riêng cho NTV [Tệp S8 R23, R51] |
| **Thu Loan** | TNHH SX TM DV Thu Loan, MST chưa có | Thuốc BVTV, Vĩnh Long | Thảo / An / Thơ | Làm xong đơn này mới tới đơn kế; thỏa thuận đóng 435ml nhưng đóng đủ 450ml, phần chênh tính vào chi phí KD [MIC] | | Có cọc nhãn [Tệp S9 R35]; bắt buộc đủ VTBB, NL mới gửi đơn; có Drive *Đơn đặt hàng Thu Loan* riêng [Tệp S4 R16, R26]; Thiết kế tự làm việc in nhãn với Thu Loan cho IDA, ABA [Tệp S9 R22] |
| **ADU** | TNHH ADU Việt Nam, 108502573 (*có thể mất số 0 đầu*) | Thuốc BVTV, Long An | Oanh / An / Khang | Công ty sắp xếp nhận hàng; ADU lo nhập khẩu BTP [MIC] | | |
| **ATC** | TNHH XNK Hóa chất ATC, 1602181299 | Thuốc BVTV; không có nhà máy, thuê lại nhà khác | Thảo / An / **chưa có QLDL** | Nhận hàng ở kho Hà Long [MIC] | | |
| **PES (Pesticidex)** | Sàn Giao dịch Thuốc BVTV Việt Nam, 1801685413 (**trùng MST với Thành Phát**) | Thuốc BVTV; không có nhà máy | Ngọc / An / Thơ | Thuê lại Hà Long / Yamato / Dubai [MIC] | Hóa đơn đi vòng qua Hà Long, phải đối chiếu chênh lệch thuế định kỳ [MIC] | |
| **Agrifuture** | TNHH Agrifuture, MST chưa có | Thuốc BVTV | Thảo / An / Khang | | | |
| **Dubai** | TNHH Hóa chất Phân bón, Thuốc BVTV Dubai, 1101798524 | Thuốc BVTV | Thảo / An / **chưa có QLDL** | | | |
| **Thành Phát** (Thuận Thành Phát) | CTCP ĐT & CN Thuận Thành Phát, 1801685413 | Thuốc BVTV | **chưa có** / An / **chưa có** | | | Có phí lưu kho [Tệp S8 R59] *(chỉ có ở tệp; MIC không nhắc nhà này)* |
| Agama, Nhật Việt, Dego Đồng Tháp | (không có trong tệp) | | Nhật Việt: QLDL Liên; còn lại chưa có | MIC nhắc tên [MIC] | | Sự cố BOOMGOLD tại AGA [MIC] |

**Bảng Thông tin NCC GC của tệp chỉ là khung.** Sheet có 22 cột (kho, thời gian làm việc, chính sách lưu kho, báo trước khi nhận hàng, thời điểm hóa đơn, MOQ, thời gian SX, hao hụt, bên chuẩn bị phụ gia, hình thức giao nhận, hợp đồng, liên hệ, lưu ý, đánh giá), nhưng chỉ điền tên và một phần MST [Tệp S17 R2–R18]. Số liệu vận hành ở bảng trên lấy từ MIC. MIC trả lời *phí lưu kho từng NCC xem TT NCC GC* [MIC V1·C18], nhưng sheet đó trống: **chưa ai trả lời** về mức phí lưu kho.

Năm 2026 có khoảng 4 nhà gia công mới [MIC].

---

## 5. Từng quy trình

Cách đọc bảng: *Ai duyệt / chịu cuối* ghi theo khung 3 tầng ở mục 3.1. Cột *Thời hạn* trống ở mọi bước của tệp; thời hạn trong bài lấy từ câu chữ trong tệp hoặc từ MIC.

### 5.1. Quy trình 1: Làm việc với NCC GC mới

**Khi nào**: có sản phẩm mới mà nhà hiện tại không làm được, nhà hiện tại không đáp ứng (năng lực, chất lượng, giá), hoặc muốn so giá [MIC]; [Tệp S1 R6–R8].

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ / biểu mẫu | Thời hạn |
|---|---|---|---|---|---|---|
| 1. Tiếp nhận yêu cầu | QLSX | | Yêu cầu từ lãnh đạo hoặc bộ phận khác, gợi ý NCC nếu có | Mục tiêu tìm NCC | Zalo *Nội bộ - Thảo luận sản xuất* [MIC]; [Tệp S1 R14] | Chưa có (tệp tự ghi) [Tệp S1 R14] |
| 2. Tìm NCC | QLSX; phối hợp QLDL, Thu mua | | Quan hệ sẵn có, web | Danh sách NCC | [Tệp S1 R15] *(chỉ có ở tệp)* | |
| 3. So sánh, đánh giá sơ bộ | **chưa có người làm** [Tệp S1 R16] | | | Danh sách NCC tiềm năng kèm lý do | Tham vấn QLDL, Thu mua, Nhà máy, Ban Giám đốc *(chỉ có ở tệp)* | |
| 4. Liên hệ, thu thập thông tin | QLSX | | | Nhóm Zalo riêng với NCC | Zalo *Tên NCC - Dego hợp tác* [Tệp S1 R17] | |
| 4.1 Kiểm pháp lý NCC | CV QLDL | | Giấy phép SX, buôn bán, đăng ký doanh nghiệp | Đạt thì đi tiếp; không đạt thì ngưng, tìm nhà khác | Checklist NCC GC mới, Mẫu 01 [Tệp S1 R18] | |
| 4.2 Chốt danh mục hợp tác | KD lập; QLDL, QLSX | CEO duyệt [MIC V6·C8] | | Danh mục được duyệt; QLDL báo ĐP NL/BTP test mẫu | [Tệp S1 R19] | |
| 4.3 Kiểm pháp lý danh mục | CV QLDL | | Giấy đăng ký, công bố hợp quy từng sản phẩm | | [Tệp S1 R20] | |
| 5.1 Lấy mẫu của NCC, kiểm, chốt công thức | ĐP NL/BTP; QLDL mua mẫu | QLSX duyệt báo cáo và BĐM | Danh mục đã duyệt | Kết quả Lab; BĐM BTP | Phiếu đề nghị mua; Form khảo sát VTBB - cọc nhãn - mẫu [Tệp S1 R23–R28] | Thử mẫu 10–14 ngày; phối không đạt tối đa 2 lần [MIC]; [Tệp S1 R27] |
| 5.2 Gửi công thức, mẫu cho NCC phối | ĐP NL/BTP; Lab | QLSX | Công thức Dego | Mẫu đạt; NCC lưu mẫu tối thiểu 2 năm | [Tệp S1 R30–R37] | Như trên |
| 6.1 Bảng giá | CV QLDL | QLSX duyệt và ký bảng giá | Báo giá phí đóng gói, phí phối, giá BTP / TP | Bảng giá đưa vào hợp đồng | Checklist Mẫu 04 [Tệp S1 R40–R42] | |
| 6.2 Hợp đồng, phụ lục | CV QLDL soạn | **TN QLDL kiểm duyệt** → Pháp lý chung → Kế toán → Giám đốc (ĐDPL) ký [MIC V5·C2] | Khoảng 25 mục phải chốt (giá gia công, chiết khấu, cọc nhãn, công nợ, lưu kho, MOQ, KCS, lưu mẫu, đóng date, hàng lỗi...) [MIC V9·C17] | Hợp đồng ký; bản scan lưu Drive, bản gốc gửi P TCKT [MIC V9·C18] | Word; Checklist Mẫu 02 [MIC V9·C19]; [Tệp S1 R44] | Mỗi bộ phận tham vấn tối đa 1 ngày [Tệp S1 R47] *(chỉ có ở tệp)* |
| 7. Bàn giao nội bộ | CV QLDL | TN QLDL chịu trách nhiệm [MIC V4·C4] | Thỏa thuận ngoài hợp đồng | Mẫu 05 Biên bản nội bộ; QLDL chuyển Giá vốn, Giá vốn báo KD [MIC V4·C4, V9·C1] | Checklist Mẫu 05 | Sau khi ký nếu có thỏa thuận ngoài hợp đồng; **trước khi ký** nếu người ngoài phòng đi đàm phán [MIC V8·C5] |

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Chữ *Giám đốc* ở bước 4.2 và 6.2.4 là CEO, ở 6.2.5 là ĐDPL chỉ ký [MIC V6·C8, V9·C3]. Luồng hợp đồng [MIC V5·C2]. 25 mục cần chốt [MIC V9·C17]. Lưu trữ hợp đồng [MIC V9·C18, C19]. Mẫu 05 lập lúc nào [MIC V8·C5] | (1) Người duyệt hợp đồng: MIC là TN QLDL kiểm duyệt [MIC V5·C2]; tệp ghi QLSX duyệt và ký nháy [Tệp S1 R47, R48]. **Theo MIC**; *chưa rõ* QLSX có còn ký nháy sau TN QLDL không. (2) Mẫu 05 giao cho ai: MIC là Giá vốn rồi KD [MIC V4·C4]; tệp ghi triển khai cho Thu mua, KD, P TCKT, Pháp lý [Tệp S1 R49]. **Theo MIC** | Bước 3 không có người làm [Tệp S1 R16]. Không có hạn tiếp nhận, phản hồi [Tệp S1 R14]. Checklist giấy phép BVTV có áp cho NCC phân bón không [Tệp S1 R18] |

### 5.2. Quy trình 2: Khai báo dữ liệu sản xuất (mã)

**Khi nào**: phát sinh dữ liệu mới, mã mới [MIC V11·C11, C16]; [Tệp S2 R11].

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ / biểu mẫu | Thời hạn |
|---|---|---|---|---|---|---|
| 1. Nhận thông tin, khai trên Drive | Người khai theo loại mã (bảng dưới) | Người khai tự chịu trách nhiệm trùng, sai mã [MIC V3·C8] | Hình ảnh, thông số | Dòng khai báo | Drive *1. DATA DỮ LIỆU ĐẦU VÀO SX*; Mẫu khai báo [MIC V11·C14]; [Tệp S2 R19–R33] | Khi phát sinh |
| 2. Kiểm trùng | Người khai | | Mã đã có | Trùng thì không khai, báo lại | [Tệp S2 R35] | |
| 3. Trình duyệt | QLDL, ĐP VTBB, ĐP TP, ĐP NL/BTP trình QLSX; Thu mua trình Quản lý Thu mua | **QLSX duyệt qua Zalo** [MIC V12·C3] | | | Zalo *SX&P TCKT - XUẤT NHẬP KHO NL & CÔNG NỢ NCC* [MIC V8·C12]; [Tệp S2 R36] | |
| 4. Gửi Kế toán | Người khai | | File đã duyệt | Kế toán nhập MISA | Cùng nhóm Zalo [MIC V8·C13] | |
| 5. Cập nhật kết quả | Người khai | | Phản hồi của Kế toán | Drive dữ liệu cập nhật; báo nhóm nội bộ | [MIC V11·C18]; [Tệp S2 R38–R39] | |

**Ai khai mã nào** [Tệp S2 R35] *(chỉ có ở tệp)*: Thu mua khai NCC thu mua, đơn vị vận chuyển, NL, BTP ruột, BTP nhập khẩu, chi phí nhập khẩu. ĐP TP khai kho, công ty nội bộ, khoản mục chi phí. QLDL khai NCC GC, BTP cấu thành, phí phối trộn, phí đóng gói. ĐP NL/BTP khai BTP mua. ĐP VTBB khai VTBB. Thiết kế khai HH. Lab khai BTP R&D. Quy tắc đặt mã: mục 6.2.

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Thời điểm: khi phát sinh [MIC V8·C11, V11·C11, C16]. QLSX duyệt qua Zalo, không ký chính thức [MIC V12·C3]. Kênh, file [MIC V8·C12–C14, V11·C14]. Hai nơi khai: MISA (Kế toán) và Drive SX [MIC V11·C18] | Không có mâu thuẫn MIC và tệp. Tệp tự lệch: BTP ruột do Thu mua khai [Tệp S2 R20] hay Oanh khai [Tệp TĐ R74]. **Chưa ai trả lời** | **Quy tắc mã đơn TP, BTP, xử lý lại, mã sự cố, mã BĐM chưa có** [Tệp S2 R1]. Biểu mẫu BTP R&D ghi *Drive ....* [Tệp S2 R24]. Mục V, VI, VII trống [Tệp S2 R71–R83]. Tên nhóm Zalo khai báo không thống nhất [Tệp S2 R19, R34, R65]. Mã BTP mua dự kiến bỏ năm 2027 [Tệp S2 R47] |

### 5.3. Quy trình 3: Khảo sát và tính giá vốn

**Ba lúc làm**: khảo sát khi chưa có đơn; kiểm giá khi KD lên đơn; xác nhận giá sau sản xuất và gửi Kế toán [MIC]; [Tệp S3 R11–R13]. **Có 3 loại giá vốn** khác nhau: kinh doanh, sản xuất, kế toán [MIC].

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ / biểu mẫu | Thời hạn |
|---|---|---|---|---|---|---|
| A. Tiếp nhận yêu cầu | Giá vốn | | Yêu cầu của KD (link dự trù) hoặc CEO nhắn Zalo [MIC V11·C7] | | Form 1 [Tệp S3 R21] | |
| B1. Khảo sát giá cho KD: kiểm pháp lý sản phẩm → kiểm cấu thành → hỏi giá QLDL, ĐP VTBB, ĐP NL/BTP, Thu mua → lập bảng cấu thành giá → trả KD | Giá vốn; Pháp lý SX kiểm pháp lý | **Giá vốn chịu trách nhiệm**; bước này chỉ khảo sát, so sánh, không tính lại giá [MIC V4·C2]. QLSX duyệt bảng cấu thành [Tệp S3 R25, R27] *(chỉ có ở tệp)* | | Kết quả vào Drive *3. DỰ TRÙ KINH DOANH*, KD vào xem [MIC V11·C8, C9] | Form 2–4; Zalo theo thương hiệu [Tệp S3 R24–R28] | **Không có hạn** [MIC V6·C20] |
| B2. Kiểm giá đơn sản xuất: xác định cấu thành → nhận tồn kho → duyệt giá | Giá vốn | QLSX ký *Phiếu duyệt giá*, lưu nội bộ, không cần Giám đốc [MIC V2·C6]. Biên lợi nhuận: **KD tự kiểm** [MIC V3·C2] | Thông tin đơn, BĐM, phí NCC | Giá đã duyệt ghi vào Drive ĐP TP | Form 5; file quy đổi mã BTP KD sang SX [Tệp S3 R30] | Đơn ngoài dự trù thêm 3 ngày khảo sát [Tệp S3 R31] *(chỉ có ở tệp)* |
| B3.1 Xác nhận giá NCC khi tính tiền | QLDL / Thu mua | Giá vốn kiểm; QLSX duyệt [Tệp S3 R34] | Giá NCC báo | Lệch thì yêu cầu NCC sửa; không sửa thì Giá vốn làm việc KD | Zalo *CÔNG NỢ/KẾ TOÁN + Tên NCC* | |
| B3.2 Giá vốn thực tế gửi Kế toán | Giá vốn | **TN QLDL ký** [MIC V3·C7, V4·C3] | Giá BTP, VTBB, BĐM TP, phí gia công, phí phát sinh từ QLDL [MIC V8·C20] | Ảnh chụp sheet gửi Kế toán | Sheet *4. Quản lý giá vốn 2026* + Signal [MIC V4·C17, V5·C1, V10·C16] | Bắt đầu khi **hàng về kho Dr Xanh**, làm theo từng đơn hoàn thành [MIC V4·C15, C16] |
| C1. Lưu giá vào Drive | Giá vốn | QLSX | | GVSX, GVKD đã duyệt và giá thực tế | [Tệp S3 R37] *(chỉ có ở tệp)* | Sau khi chốt đơn |
| C2. Báo cáo KD (sản lượng, tiến độ, phí phạt, lãi quá hạn) | Giá vốn | QLSX | | | Drive *5. GIÁ VỐN KINH DOANH NĂM 2024* [Tệp S3 R38] *(chỉ có ở tệp)* | Định kỳ / theo yêu cầu |

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Ai chịu trách nhiệm khảo sát [MIC V4·C2]; tần suất theo yêu cầu [MIC V11·C6, C13]; kết thúc khi bên yêu cầu xác nhận [MIC V11·C15]; Hương vắng thì QLSX làm [MIC V2·C20]; đầu vào và công cụ giá vốn thực tế [MIC V4·C15–C17, V8·C20] | (1) Giá vốn thực tế: MIC bắt đầu khi hàng về kho Dr Xanh, TN QLDL ký [MIC V4·C15, V3·C7, V4·C3]; tệp ghi *trong ngày nhận LSX*, QLSX duyệt [Tệp S3 R35]. **Theo MIC**. (2) Biên lợi nhuận: MIC nói chuyển cho KD tự kiểm [MIC V3·C2]; tệp còn bước *âm biên thì gửi KD kiểm lại* [Tệp S3 R32] và sheet *12. Biên giá* [Tệp TĐ R40]. **Theo MIC**; ngày áp dụng *chưa rõ* (V3·C2 ghi *trong thời gian tới*) | Biểu mẫu chỉ ghi Form 1–5, mục V trống [Tệp S3 R40–R43]. Phí thuê tên, phí danh mục chờ Pháp lý [MIC]; [Tệp TĐ R26–R27] |

### 5.4. Quy trình 4: Quản lý đơn hàng sản xuất gia công (xương sống)

**Khung 7 bước theo MIC**. Tệp có 7 bước đánh số khác (tiếp nhận, kiểm tra, gửi đơn, nhập kho và hóa đơn, nhận hàng, gửi Lab, chứng từ) [Tệp S4 R16–R33]; các phần tệp có mà MIC không có được chèn vào đúng chỗ. Đơn có 3 loại: TP, BTP, xử lý lại. ĐP TP quản đơn TP và đơn xử lý lại; ĐP NL/BTP quản đơn BTP [MIC V1·C8]. Một đơn mất 10–20 ngày [MIC].

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ / biểu mẫu | Thời hạn |
|---|---|---|---|---|---|---|
| 1. Nhận yêu cầu, kiểm 7 điều kiện | ĐP TP phụ trách nhà đó + 7 bộ phận | Mỗi bộ phận chịu phần mình xác nhận; ĐP TP chịu việc đôn đốc [MIC V3·C14] | KD nhập Drive *Yêu cầu đặt hàng TP* và báo Zalo *Dự trù hàng hóa*; đủ giấy tờ và mockup, **thiếu mockup thì dừng đơn** [MIC V2·C1, C2] | 7 xác nhận trên sheet DUYỆT ĐƠN HÀNG | Drive *SX-ĐIỀU PHỐI THÀNH PHẨM*, sheet PYC, Pháp lý, Điều phối [Tệp S4 R16] | Kiểm liên tục; suôn sẻ khoảng 1 buổi [MIC V2·C4, V4·C8]; **chưa có hạn cho từng bộ phận** [MIC V4·C9]. Chậm nhất 3 ngày phải cập nhật tiến độ [Tệp S4 R16] *(chỉ có ở tệp)* |
| 2. QLSX duyệt | QLSX | QLSX quyết cho đi [MIC V3·C14] | ĐP TP báo đủ 7 bên qua điện thoại, Zalo [MIC V3·C15] | Cột duyệt QLSX trên Drive Điều phối [MIC V3·C12] | Drive các team [MIC V3·C13, V4·C7] | Khi đủ xác nhận [MIC V3·C11]. Được duyệt trước, cho nợ hồ sơ, **không có tiêu chuẩn văn bản** [MIC V3·C4, V10·C11] |
| 3. Lập và gửi PO | ĐP TP | Lần đầu giao dịch với NCC thì QLSX duyệt thông tin đặt hàng [Tệp S4 R26] *(chỉ có ở tệp)* | 7 bên đã duyệt, phần thiếu lấy từ yêu cầu KD [MIC V4·C18] | PO **không ghi giá**, kèm mockup; NCC không ký thì đàm phán lại hoặc đổi NCC [MIC V1·C11] | Drive ĐP TP; Zalo *TÊN NCC - ĐẶT HÀNG SẢN XUẤT* [MIC V8·C3]; Yamato gửi PDF, nhà khác chụp màn hình [Tệp S4 R26] | Từng đơn, sau khi duyệt [MIC V8·C2] |
| 4. Theo dõi sản xuất | ĐP TP | QLSX chịu cuối [MIC] | Phản hồi của NCC | Ngày dự kiến có hàng trên Drive; báo cáo hằng ngày [MIC V4·C19] | Sheet Điều phối; Zalo *TÊN NCC - TIẾN ĐỘ SẢN XUẤT* [MIC V2·C9] | Lần 1 sau 2 ngày gửi đơn, lần 2 trước ngày có hàng 2 ngày [MIC]; nhịp tùy đơn [MIC V8·C1]. Báo cáo hằng ngày: hàng sẵn kho, chờ hóa đơn, đã có lịch [Tệp S4 R27] |
| 4a. Có hàng, đề nghị nhập kho, lấy hóa đơn | ĐP TP; QLDL lấy hóa đơn | QLSX duyệt đề nghị nhập kho [Tệp S4 R29] | Yamato, Hà Long báo số lượng; nhà khác chỉ báo có hàng [Tệp S4 R29] | Trạng thái *Chưa lấy hóa đơn*; đề nghị nhập kho TP gửi QLDL | Phiếu đề nghị nhập kho TP [Tệp S4 R29–R30] *(chỉ có ở tệp)* | Theo lịch NCC |
| 4b. Nhận hàng về kho | Kho Dr Xanh; ĐP TP | | Lịch nhận hàng, tài xế, biển số | Kho kiểm số thùng, ngoại dạng, ký phiếu xuất kho NCC; trạng thái *Đã nhận hàng* | Zalo *SX&KHO - LỊCH GIAO NHẬN HÀNG TP*, *CHỨNG TỪ XUẤT NHẬP KHO NCC* [Tệp S4 R31] | Chứng từ giao nhận bản cứng nộp Kế toán **trong ngày** [MIC] |
| 5. Kiểm chất lượng | Kho làm KCS; ĐP TP gửi mẫu | **Lab kết luận đạt / không đạt** [MIC V3·C16] | KCS khi kho nhận hàng; Lab khi hàng về kho [MIC V3·C17] | Kết quả về nhóm Zalo; không đạt thì sang quy trình sự cố | Sheet *Kết quả KCS* [MIC V10·C1]; đề nghị xuất kho mẫu, QLSX duyệt, KD xuất MISA [Tệp S4 R32] | **100% đơn** [MIC V3·C18]. Ngoại dạng 1–2 ngày, hàm lượng 14 ngày [MIC V3·C6] |
| 6. Chốt hoàn thành | ĐP TP | | Đủ 3 điều kiện: Lab đạt, QLDL báo có hóa đơn, Kho ký nhận đủ lượng [MIC V8·C7] | Cập nhật sheet ĐIỀU PHỐI, **khóa đơn**; tin chạy về bộ phận yêu cầu và Kho [MIC V8·C8, C9] | Sheet ĐIỀU PHỐI | Ngay khi đủ điều kiện [MIC V8·C6]. Hóa đơn phải cùng ngày hoặc sau ngày LSX [MIC]; [Tệp S6 R22] |
| 6a. Lệch số lượng | ĐP TP hỏi KD | KD quyết | | Thiếu: làm thêm hoặc hủy; dư: nhận hoặc báo sự cố [MIC]; [Tệp S4 R29] | | |
| 7. Hồ sơ thanh toán, đối chiếu công nợ | CV QLDL | CV phụ trách chịu trách nhiệm, TN QLDL kiểm [MIC V3·C19] | Chứng từ từ NCC [MIC V3·C20] | Biên bản đối chiếu công nợ trình QLSX ký | Xem quy trình 6 | Đầu tháng làm cho đơn tháng trước; trước ngày 20 tháng kế [MIC]; [Tệp S6 R26] |

**Bảy mục kiểm ở bước 1** (tên người theo MIC [MIC V6·C12]; việc theo tệp [Tệp S4 R18–R24]):

| Mục | Người | Việc | Duyệt |
|---|---|---|---|
| Pháp lý | Huỳnh | Theo quy trình 5; xác nhận trên sheet Điều phối | |
| NL/BTP | Oanh | Kiểm dòng công thức, BĐM BTP, tồn, giá; thiếu thì chuyển hoặc mua | |
| VTBB | Ly | Mockup gần nhất, cấu thành VTBB nội bộ và gửi NCC; khả năng đóng của NCC | |
| Giá vốn | Hương | Duyệt giá tạm; rồi lập *Phiếu duyệt giá* 3 mức (giá vốn nội bộ, giá vốn thuế, giá KD bán); QLDL lưu bản gốc | QLSX |
| Sự cố | Thi | Cảnh báo đơn đang vướng sự cố cũ | |
| QLDL | Thơ / Liên / Khang | BĐM TP nội bộ và thuế | QLSX |
| QLSX | Ngân | Duyệt cuối | |

Mỗi đơn kèm mẫu thành phẩm 2 đơn vị tính nhỏ nhất [Tệp S4 R22, R26] *(chỉ có ở tệp)*.

**Phần B. Hủy đơn đặt hàng NCC GC** *(chỉ có ở tệp; MIC không có)* [Tệp S4 R34–R41]

| Bước | Ai làm | Ai duyệt | Nội dung |
|---|---|---|---|
| 1. Nhận yêu cầu hủy | ĐP TP | | Từ bộ phận đặt hàng qua Zalo. Lỗi NL, VTBB hoặc vướng pháp lý thì chuyển quy trình sự cố |
| 2.1 Chưa gửi NCC | ĐP VTBB, ĐP NL/BTP, QLDL, ĐP TP | QLSX | Dừng mua, dừng phối, cập nhật tồn, ghi chi phí cho bên yêu cầu hủy; chuyển đơn sang sheet Hoàn thành |
| 2.2 Đã gửi NCC | ĐP TP | QLSX | NCC chấp nhận: làm như 2.1. NCC không chấp nhận: trạng thái *Chờ thông tin từ KD*; KD nhận hàng thì đi tiếp từ bước 4a; không nhận thì sang sự cố |
| 3. Thanh toán, lưu trữ | Các ĐP, QLDL | QLSX | Theo quy định công ty |

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Người tiếp nhận, tổng hợp, tạo PO [MIC V2·C1, C3, C7]. Điều kiện gửi PO [MIC V2·C8]. QLSX duyệt ở đâu, lúc nào [MIC V3·C11–C13, C15, V4·C7]. Ai chịu trách nhiệm khi kiểm sót [MIC V3·C14]. Lab, KCS [MIC V3·C6, C16–C18]. Điều kiện hoàn thành, khóa đơn [MIC V8·C6–C9] | (1) Lab: MIC ngoại dạng 1–2 ngày, hàm lượng 14 ngày [MIC V3·C6]; tệp ghi *R&D trả kết quả chậm nhất 2 ngày* [Tệp S4 R32]. **Theo MIC**. (2) Báo cáo hằng ngày: MIC ghi 16h [MIC]; tệp ghi trước 16h30 [Tệp S4 R27]. **Theo MIC** (mức thấp). (3) Khung bước: MIC tách *QLSX duyệt* thành bước riêng; tệp không có bước này. **Theo MIC**, tệp bổ sung bước 4a, 4b, phần B | **Danh sách trạng thái đơn chưa có** (tệp nhắc rải rác *Chưa lấy hóa đơn, Đã nhận hàng, TEST KHÔNG ĐẠT, Chờ thông tin từ KD*, hủy, hoàn thành) [Tệp S4 R29–R40]. Đơn chốt sau kết quả ngoại dạng hay hàm lượng: *chưa rõ*. Tiêu chuẩn duyệt trước, nợ hồ sơ [MIC V10·C11] |

### 5.5. Quy trình 5: Pháp lý sản xuất *(MIC không có quy trình riêng)*

Pháp lý là 1 trong 7 bộ phận duyệt đơn, do Huỳnh phụ trách [MIC V6·C12]; dùng Drive *Pháp lý sản xuất* cho pháp lý sản phẩm, pháp lý NCC, duyệt đơn, xử lý sự cố [MIC V10·C20]. Chi tiết các bước *(chỉ có ở tệp)*:

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ | Thời hạn |
|---|---|---|---|---|---|---|
| I.1 Nhận thông tin đơn | Pháp lý SX | **trống** | ĐP TP cập nhật đơn; mockup | | Drive [Tệp S5 R16] | Khi nhận đơn |
| I.2.1 Đơn đang tạm ngưng do sự cố | Pháp lý SX; phối hợp Sự cố | **trống** | | Cảnh báo VTBB, NL, BTP có nguy cơ lỗi | [Tệp S5 R18] | |
| I.2.2 Nguồn gốc sản phẩm | Pháp lý SX; Pháp lý chung | **trống** | Giấy đăng ký thuốc / quyết định lưu hành phân bón, công bố hợp quy, ủy quyền | Xác định đơn vị sở hữu, đơn vị cấu thành | [Tệp S5 R19] | |
| I.2.3 Điều kiện sản xuất | Pháp lý SX; NCC GC | **trống** | Giấy phép đủ điều kiện SX; nhãn | | [Tệp S5 R20] | |
| I.2.4 Điều kiện mua bán | Pháp lý SX; Pháp lý chung | **trống** | Hợp đồng mua bán; giấy đủ điều kiện mua bán | | [Tệp S5 R21] | |
| I.2.5 Dòng hóa đơn | Pháp lý SX | **trống** | Ba bước trên | Dòng hóa đơn: xuất theo **công ty sở hữu pháp lý sản phẩm**, không theo thương hiệu đặt (ví dụ IDA đặt, sản phẩm của BamBoo thì hóa đơn cho BamBoo) [MIC]; [Tệp S5 R22] | | |
| I.3 Cập nhật | Pháp lý SX | | | Drive pháp lý đơn hàng; chia sẻ các bộ phận | [Tệp S5 R23] | |
| II.1–II.4 Pháp lý sản xuất: nhận, rà trùng, theo dõi hạn (hợp quy, ủy quyền, thuê tên), báo cáo | Pháp lý SX; QLDL, Pháp lý chung | **trống** | Hồ sơ mới, gia hạn từ QLDL | Thông báo bộ phận gia hạn | [Tệp S5 R25–R28] | *Định kỳ*, không ghi tần suất |

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Người phụ trách pháp lý đơn [MIC V6·C12]; Drive Pháp lý [MIC V10·C20]; dòng hóa đơn theo công ty sở hữu [MIC]; đơn xử lý lại cũng qua pháp lý như đơn mới [MIC V3·C5] | Không có mâu thuẫn MIC và tệp. Tệp tự lệch: theo dõi hạn giấy tờ do Pháp lý SX làm [Tệp S5 R27] hay Pháp lý chung làm, QLDL bổ sung trước 3 tháng (6 tháng nếu công ty sở hữu tên) [Tệp S6 R32]. **Chưa ai trả lời** | Không bước nào có người duyệt, thời hạn. Câu mở đầu sheet: *còn duyệt pháp lý đơn BTP, đơn xử lý lại, sự cố, mua / khảo sát NL/BTP?* [Tệp S5 R2]. TĐ ghi *còn thiếu pháp lý SX* [Tệp TĐ R190], dù MỤC LỤC ghi Hoàn thành [Tệp ML R6]. Mục V, VII trống |

### 5.6. Quy trình 6: Quản lý NCC GC (việc của QLDL)

MIC gọi là *Quản lý hồ sơ, dữ liệu nhà gia công*, làm theo từng đơn hoặc hằng tháng, CV QLDL phụ trách [MIC]. Kết thúc khi đối chiếu và thanh toán xong, bàn giao hồ sơ cho Kế toán [MIC V13·C2].

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ / biểu mẫu | Thời hạn |
|---|---|---|---|---|---|---|
| A1. Nhận thông tin đơn | CV QLDL | | Đơn đã duyệt giá tạm, dữ liệu tự chạy từ Drive ĐP | | Drive 01 [Tệp S6 R20] | |
| A2. Lập BĐM TP | CV QLDL | QLSX | BĐM VTBB + mã BTP | Mã BĐM TP; gửi P TCKT | Drive QLDL [MIC V6·C7]; Mẫu BĐM TP | Trước khi gửi đơn NCC |
| A3. Nhận hóa đơn NCC | CV QLDL | | Bản gốc đề nghị nhập kho TP từ ĐP TP | Hóa đơn | [Tệp S6 R22] | Hóa đơn cùng ngày hoặc sau ngày LSX |
| A4. LSX, phiếu nhập / xuất / chuyển kho | CV QLDL | QLDL tự duyệt [Tệp S6 R23] | Số lượng sẵn kho từ ĐP TP; phiếu xuất NL/BTP, VTBB có chữ ký | Phiếu tổng: LSX, đề nghị nhập kho, xuất kho, chuyển kho gửi P TCKT | Zalo *CHỨNG TỪ XUẤT NHẬP KHO NCC* | Phiếu xuất NL/BTP, VTBB lập trước hoặc cùng ngày LSX |
| A5. Bán thành phẩm giữa các công ty nội bộ *(chỉ có ở tệp)* | CV QLDL | QLDL | Pháp lý đã duyệt (công ty bán, công ty mua) | Phiếu đề nghị xuất bán, phụ lục bán hàng; P TCKT làm hóa đơn nháp | [Tệp S6 R24] | Phụ lục tháng trước gửi Kế toán chậm nhất ngày 5 |
| A6. Đối chiếu tồn kho, phí lưu kho | CV QLDL; các ĐP, XLSC | QLSX ký biên bản | Danh sách tồn NCC gửi | Biên bản đối chiếu tồn kho; lệch thì chứng minh cho NCC, theo đến khi khớp [MIC V1·C18] | Drive *4. Công nợ, thanh toán* [Tệp TĐ R110–R127] | Hằng tháng |
| A7. Đối chiếu công nợ nội bộ và thuế | CV QLDL | CV chịu trách nhiệm, TN QLDL kiểm [MIC V3·C19]; QLSX ký biên bản | Công nợ ghi trên từng đơn khi nhận hóa đơn [MIC V4·C10]; MISA | Biên bản đối chiếu công nợ | Drive, MISA | **Trước ngày 20 tháng kế** [MIC]; [Tệp S6 R26] |
| A8. Thanh toán | CV QLDL | QLSX | **14 chứng từ** [MIC V6·C4]; khoản cấn trừ từ XLSC | Hồ sơ gửi Kế toán; ảnh ủy nhiệm chi gửi NCC | | Khi đến hạn [MIC V4·C10] |
| B1–B2. Mua NL/BTP, VTBB tại NCC GC *(chỉ có ở tệp)* | CV QLDL | ĐP NL/BTP hoặc ĐP VTBB kiểm; QLSX duyệt | Yêu cầu mua từ ĐP | Hợp đồng bổ sung, hóa đơn, phiếu kiểm soát chất độc, COA; test mẫu | [Tệp S6 R29–R30] | |
| C1. Hồ sơ pháp lý NCC | CV QLDL | Thiếu hồ sơ thì trình QLSX | Bản scan giấy phép, giấy đăng ký sản phẩm | Gửi Pháp lý chung lưu | Form Pháp lý - Chi phí [Tệp S6 R32] | Gia hạn trước 3 tháng (6 tháng nếu công ty sở hữu tên) |
| C2. Hợp đồng mới, gia hạn | CV QLDL | QLSX | | Hợp đồng; báo QLSX trước 3 tháng hết hạn | Drive *QLDL - THỐNG KÊ HỢP ĐỒNG* [Tệp S6 R33] | Checklist trả trước ít nhất 1 tháng |
| C3. Lãi quá hạn, sản lượng, phí phạt, chiết khấu, phí lưu kho *(chỉ có ở tệp)* | CV QLDL | QLSX | | Phí phạt gửi Giá vốn; phí phối gửi ĐP NL/BTP; phân bổ phí lưu kho theo thương hiệu | *Drive ....* (chưa có) [Tệp S6 R34] | Hằng tháng |
| C4. Hoa hồng | (xem mục 7) | | | | [Tệp S6 R35] | |
| C5. Dự chi *(chỉ có ở tệp)* | CV QLDL | QLSX (dự chi mua trả ngay) | Công nợ trên MISA; kế hoạch KD | Drive Dự chi | Form Dự chi [Tệp S6 R37–R38] | Ngày 25–28 tháng trước |

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Bộ 14 chứng từ [MIC V6·C4]. Ai lấy chữ ký, dấu của NCC: QLDL [MIC V2·C13]. Trách nhiệm số công nợ [MIC V3·C19]. Lúc lập hồ sơ [MIC V4·C10]. Kết thúc quy trình [MIC V13·C2] | Thời điểm lập hồ sơ thanh toán: MIC *khi đến hạn* [MIC V4·C10]; tệp *trước hạn 7 ngày* [Tệp S6 R27; S14 R34–R35]. **Theo MIC** (mức thấp) | Drive theo dõi phí phạt ghi *Drive ....* [Tệp S6 R34]. P TCKT đồng bộ mã BĐM TP: *check lại* [Tệp S6 R21]. Drive 5 hồ sơ thanh toán *chưa có* [Tệp TĐ R128] |

### 5.7. Quy trình 7: Bảng định mức thuế *(MIC không có quy trình riêng)*

MIC có **BĐM 3 tầng**: BĐM VTBB do ĐP VTBB; BĐM NL/BTP do ĐP NL/BTP (công thức từ Drive Lab, QLSX ký); BĐM TP do CV QLDL ghép lại [MIC V2·C5, V11·C4, C5, V7·C1]. Phần thuế *(chỉ có ở tệp)*: BĐM BTP tính trên 1.000 L hoặc kg; BĐM VTBB và BĐM TP tính trên 1 đơn vị sản phẩm; làm trước khi sản xuất và trước khi tính giá vốn [Tệp S7 R6–R11].

| Bước | Ai làm | Ai duyệt | Nội dung | Thời hạn |
|---|---|---|---|---|
| A. BĐM BTP: nhận tin → xác định luồng pháp lý và cấu thành → kiểm tồn → kiểm BĐM cũ → lập mới | ĐP NL/BTP; Pháp lý SX, Lab, NCC GC phối hợp | QLSX (ở bước D) | Chỉ lập mới khi khác dạng lỏng / rắn, đổi hàm lượng (thuốc), đổi tỷ trọng (phân) [Tệp S7 R24]; [MIC] | Khi phát sinh |
| B. BĐM VTBB: tương tự | ĐP VTBB | QLSX | Dựa mockup của Thiết kế; ghi tên VTBB trên hóa đơn và loại VTBB không lấy được hóa đơn [Tệp S7 R32] | |
| C. BĐM TP: nhận mã BĐM BTP và BĐM VTBB, đối chiếu luồng pháp lý | CV QLDL | QLSX | Phân biệt chuẩn bị toàn bộ và chuẩn bị một phần [Tệp S7 R39] | |
| D1. Trình duyệt | CV QLDL | QLSX ký bản in | Bản gốc gửi P TCKT; file gửi qua Zalo thuế theo 3 công ty IDA Global, Dego Holding, ABA [Tệp S7 R41, R59–R61] | Khi xong BĐM |
| D2. Lưu trữ | CV QLDL | | Lưu bản scan [Tệp S7 R42] | |

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Ai lập từng tầng [MIC V2·C5]; ai ký BĐM BTP, nguồn công thức [MIC V11·C4, C5]; BĐM TP lập ở đâu [MIC V6·C7, V7·C1] | Nơi duyệt BĐM BTP, BĐM VTBB: MIC ghi QLSX ký [MIC V11·C4]; sheet Mẫu biểu ghi TNĐP [Tệp S14 R3, R15]. **Theo MIC** (hiện tại QLSX ký; TNĐP đang trống) | Mục V biểu mẫu trống [Tệp S7 R45–R47]. Thuế quản chai và nắp là một bộ, nội bộ quản riêng [MIC] |

### 5.8. Quy trình 8: Quản lý NL/BTP

**Trình tự theo MIC** [MIC V11·C20]: khảo sát nhu cầu → kiểm tồn và điều kiện → lập BĐM BTP → điều phối mua hoặc điều chuyển → đề xuất phối BTP → theo dõi phối và gia công → kiểm hao hụt, thiếu, dư → xuất nhập tồn và báo cáo. Người làm chính: ĐP NL/BTP (Oanh) [MIC V3·C3].

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ / biểu mẫu | Thời hạn |
|---|---|---|---|---|---|---|
| 1. Khảo sát nhu cầu, công thức với NCC | ĐP NL/BTP | QLSX duyệt kết quả [MIC V11·C3] | Yêu cầu từ **Giá vốn** [MIC V11·C3], hoặc KD / cấp trên [MIC V12·C4] | Kết quả trả Giá vốn | Form khảo sát VTBB - cọc nhãn - mẫu, **dùng tạm**, chưa có form NL/BTP riêng [Tệp S8 R24, R62] | Thử mẫu 10–14 ngày rồi gửi Lab [MIC]; [Tệp S8 R63] |
| 2. Kiểm tồn, lên phương án | ĐP NL/BTP | QLSX | Đơn trên sheet Điều phối | Đủ NL thì đề xuất phối; đủ BTP thì cho sản xuất; tồn ở kho khác thì báo KD chọn; không có thì mua hoặc phối | Drive Điều phối [Tệp S8 R27–R29] | Ngay khi xác định BĐM |
| 3. Lập BĐM BTP | ĐP NL/BTP | QLSX ký; ĐP NL/BTP chịu trách nhiệm [MIC V11·C4] | Công thức từ Drive Lab [MIC V11·C5] | BĐM BTP gửi QLDL làm BĐM TP | Danh sách quản lý BTP phân bón / thuốc [Tệp S8 R23–R25] | Chỉ khi có BTP mới, đổi dạng, đổi hàm lượng / tỷ trọng [MIC]. Sai lệch cho phép theo hàm lượng hoạt chất (đến 2,5% thì ±15% lỏng / ±25% rắn; ... trên 50% thì ±2,5%) [MIC] |
| 4. Dự trù, mua | KD lập ngày 15; ĐP NL/BTP | QLSX duyệt phiếu | KD báo tồn, MOQ, phí lưu kho; KD cân đối tiền với P TCKT [MIC V1·C17] | Phiếu đề nghị mua / phối gửi Thu mua hoặc QLDL lấy báo giá; GVKD chốt phương án với KD | Sheet *7. YC MUA NL, BTP*; Zalo *SX - Đề nghị phối-mua mới BTP* [MIC]; [Tệp S8 R31–R36] | Phản hồi KD chậm nhất **5 ngày làm việc** [MIC] |
| 5. Đề xuất phối BTP | ĐP NL/BTP; QLDL gửi lệnh phối cho NCC | QLSX duyệt phối | Phiếu yêu cầu mua của KD [MIC V13·C1] | Phiếu đề nghị phối + phiếu xuất NL | Zalo *SX - Đề nghị phối-mua mới BTP* | |
| 6. Theo dõi phối, gia công | ĐP NL/BTP | Vượt sai số cho phép thì báo QLSX | | Trạng thái *chưa đủ BTP* → *có BTP*; đề nghị nhập kho BTP và phí phối gửi QLDL | Drive Dữ liệu BTP [Tệp S8 R52] | Phối không đạt sau 2 lần thì có thể đổi nhà hoặc dừng sản phẩm [MIC] |
| 7. Điều chuyển kho | ĐP NL/BTP | QLSX và KD | KD chốt lượng | Chọn xe (xe công ty, ghép chuyến Zalo DR.XANH, thuê qua Thu mua); chứng từ chuyển kho | Phiếu đề nghị chuyển kho, xuất bán nội bộ, yêu cầu xuất hóa đơn [Tệp S8 R39–R41] | Báo NCC trước 1 ngày; chứng từ gửi P TCKT trong ngày [MIC] |
| 8. Nhập kho (mua từ Thu mua, từ QLDL, cho tặng) | ĐP NL/BTP, ĐP TP, Thu mua, QLDL | QLSX (test trước nhập) | Chứng từ có chữ ký hai bên, ảnh lô hàng, cân tổng | Tồn cập nhật; test ngoại dạng 1–2 ngày, hàm lượng 14 ngày | Phiếu yêu cầu test của Lab [Tệp S8 R43–R49] | Ngày sản xuất trên bao bì NL trước hoặc bằng ngày hóa đơn [Tệp S8 R44] |
| 8a. Nhập kho đổ thu / dư sản xuất | **chưa có người làm** | | | | *Sẽ xây dựng sau* [Tệp S8 R48] | |
| 9. Xuất kho, hao hụt, hư hỏng, xuất chi phí | ĐP NL/BTP; QLDL | QLSX | Kiểm kê; tin sự cố tại kho NCC | Hao hụt vượt mức: NCC đền bằng hàng hoặc tiền; trong mức: đưa vào chi phí; hư hỏng: dùng tiếp, hủy, tái chế | Phiếu đề nghị đưa vào chi phí; phiếu xuất hủy [Tệp S8 R51–R55] | Phiếu xuất BTP lập trước hoặc cùng ngày LSX |
| 10. Đối chiếu tồn định kỳ | ĐP NL/BTP, QLDL | QLSX ký biên bản | Đồng bộ mã công ty và mã NCC; Drive, **MISA Thuế, MISA Nội bộ** [MIC] | Biên bản giải trình chênh lệch; biên bản xác nhận tồn; phân bổ phí lưu kho theo thương hiệu | Drive *9. ĐỐI CHIẾU TỒN KHO TẤT CẢ NCC* [Tệp S8 R57–R59] | Hằng tháng |
| 11. Báo cáo KD | ĐP NL/BTP | | | Tồn từng thương hiệu, nhà đóng được theo pháp lý, hao hụt khi phối, MOQ, phí lưu kho | Drive *Yêu cầu đặt hàng TP* [Tệp S8 R60] | Định kỳ |
| 12. Mẫu cho tặng *(chỉ có ở tệp)* | ĐP NL/BTP | QLSX | | Chỉ lưu tham khảo, không quản tồn | [Tệp S8 R64–R66] | |
| 13. Tính giá BTP | ĐP NL/BTP | QLSX | Giá NL từ Thu mua; phí phối từ QLDL / Giá vốn | Giá tạm (khảo sát) hoặc chính thức (quyết mua); gửi Giá vốn | Bảng giá BTP; sheet *3.1 Tính lượng NL & giá BTP* [Tệp S8 R68–R70; TĐ R176] | Phí phối cơ bản: SL 12k; SC 20k / 25k; EC 40k / 55k; WG 50k; WP 20k [MIC] |

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Sáu nhóm việc [MIC V9·C2]; trình tự [MIC V11·C20]; khảo sát nhận từ ai, trả ai [MIC V11·C3]; ai lập, ai ký BĐM BTP [MIC V11·C4, C5]; phiếu đề xuất phối [MIC V13·C1]; khi nào bắt đầu khảo sát [MIC V12·C4]. **MIC ghi *8/14 bước chưa rõ ai làm*, nhưng tệp đã ghi người làm cho gần hết bước** [Tệp S8 R21–R70] | (1) Nguồn yêu cầu khảo sát: MIC là Giá vốn [MIC V11·C3]; tệp ghi KD gửi đề nghị, trả KD qua Drive [Tệp S8 R62–R63]. **Theo MIC**. (2) Hạn phản hồi dự trù: MIC 5 ngày làm việc [MIC]; tệp 5 ngày [Tệp S8 R32]. **Theo MIC** | Bước 8a không có người làm [Tệp S8 R48]. **Chưa có danh sách ai chuẩn bị NL/BTP theo từng sản phẩm, NCC** [Tệp S8 R29]. Drive *Dự trù KD cập nhật giá* dùng riêng hay gộp [Tệp S8 R28]. Ghi chú *BS test sp xem rớt hàm lượng* [Tệp S8 R1]. Form khảo sát NL/BTP riêng [Tệp S8 R24] |

### 5.9. Quy trình 9: Quản lý VTBB

MIC gọi là *Tồn kho và cung ứng VTBB*, làm khi có đơn mới, hằng tháng, khi có nhập xuất; ĐP VTBB phụ trách [MIC].

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ / biểu mẫu | Thời hạn |
|---|---|---|---|---|---|---|
| 1. Xác định BĐM VTBB khi khai mã HH | ĐP VTBB; Thiết kế gắn mã VTBB vào mockup | QLSX | Mockup, mã VTBB | BĐM VTBB; sau đồng bộ mã thuế và nội bộ chỉ còn 1 bảng | Drive *4. XUẤT NHẬP TỒN - VTBB* [MIC V10·C2]; [Tệp S9 R21] | |
| 2. Nhận đơn, kiểm BĐM và tồn (nội bộ và thuế) | ĐP VTBB | KD | Đơn trên Drive Điều phối; Pháp lý xác nhận đơn vị cấu thành | *Đủ VTBB*, hoặc phương án chuyển, mua, thay thế | Drive Điều phối [Tệp S9 R22–R26] | |
| 3. Dự trù, mua | ĐP VTBB | QLSX, KD | Phiếu đề nghị mua của KD (mã, số lượng, mã pháp lý, kho nhận); KD cân đối tiền [MIC V1·C17] | Phiếu mua gửi Thu mua; chốt phương án với KD | Zalo *SX - YÊU CẦU ĐẶT VTBB* [Tệp S9 R28–R33] | Phản hồi KD chậm nhất 4 ngày [Tệp S9 R29] *(chỉ có ở tệp)*. Thời gian cung ứng chuẩn: nhãn thường 7 ngày; metalize 12; túi flexo 12–15; túi in trục 21; hộp carton 10–15; thùng 15–18; chai, can, xô 7–8 (15 nếu NCC phải sản xuất) [MIC] |
| 4. Cọc nhãn | ĐP VTBB theo dõi từng NCC [MIC V1·C17]; QLDL thanh toán và thanh lý | QLSX (hoàn cọc) | NCC duyệt nhãn, báo số tiền cọc | KD chốt phương án cọc; hoàn cọc theo sản lượng | Zalo *TH - Duyệt nhãn - In ấn VTBB* [Tệp S9 R35–R36] | Cọc trước 2026 với **6 đối tác** chưa có văn bản xác nhận hai bên [MIC] |
| 5. Điều chuyển kho, bán giữa thương hiệu | ĐP VTBB | QLSX; QLTH (quản lý thương hiệu) | KD chốt, hoặc NCC yêu cầu rút vật tư | Phiếu chuyển kho, xuất bán, xuất hóa đơn | [Tệp S9 R39–R46] | |
| 6. Nhập kho (Thu mua, tại NCC, dư sản xuất) | ĐP VTBB; QLDL | QLSX | Chứng từ có chữ ký hai bên | Tồn cập nhật | [Tệp S9 R48–R50] | |
| 7. Xuất kho sản xuất, hao hụt, hư hỏng | ĐP VTBB; QLDL | QLSX | | Phiếu xuất; hao hụt ngoài ngưỡng thì NCC trả lại | Bảng tỷ lệ hao hụt theo NCC [Tệp S9 R52–R55] | Phiếu xuất VTBB lập trước hoặc cùng ngày LSX |
| 8. Đối chiếu tồn theo tháng hoặc theo đơn; phân bổ phí lưu kho | ĐP VTBB | QLSX ký biên bản | Số NCC gửi | Biên bản xác nhận tồn, biên bản giải trình | Giấy ủy quyền QLSX ký biên bản [Tệp S9 R58–R60] | Hằng tháng |
| 9. Báo cáo KD | ĐP VTBB | QLSX | | Giá min / max 5 lần mua gần nhất, hao hụt, MOQ, cọc nhãn | [Tệp S9 R61] | Định kỳ |
| 10. Khảo sát VTBB với NCC | ĐP VTBB | QLSX | Đề nghị khảo sát của KD | Nhóm 1 bắt buộc qua Sản xuất (chai, nhãn, túi, thùng, nhãn dán thùng, can, xô, túi PE) | Phiếu yêu cầu thử nghiệm NCC [Tệp S9 R62–R64] | Kết quả 10–14 ngày |
| 11. Mẫu cho tặng *(chỉ có ở tệp)* | ĐP VTBB | QLSX | | Lưu tham khảo | [Tệp S9 R65–R67] | |

**Vướng theo MIC**: mã VTBB lệch mã nhà gia công, dễ đóng nhầm (đang gắn ảnh, video, thông số) [MIC V1·C17]; mockup chưa gắn mã; thuế quản chai và nắp là một bộ; vật tư mua theo kg không quy ra cái; sheet tồn hay lỗi vì gõ không khớp bộ 3 *Kho + Thương hiệu + Mã VTBB*; KD hủy đơn, đổi mockup làm tồn bao bì [MIC].

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Việc của ĐP VTBB, mockup do Thiết kế khai [MIC V3·C1]; cọc nhãn do ĐP VTBB quản [MIC V1·C17]; Drive VTBB dùng làm gì [MIC V10·C2, C18]; phân việc Ly, Tiên, An [MIC V1·C15] | Nhà có cọc nhãn: MIC nói 6 đối tác, thiếu dữ liệu cọc Âu Việt, Đại Tâm, Basel, An Nông [MIC]; tệp ghi 4 nhà An Nông, Âu Việt, Đại Tâm, Thu Loan [Tệp S9 R35]. **Theo MIC**; danh sách đủ 6 nhà *chưa rõ* | Thuế phần hao hụt chưa xong, cần Kế toán và SX thống nhất tỷ lệ [Tệp S9 R53]. 4 điểm *cần thống nhất trước khi ban hành* [Tệp S9 R112]. Điểm (3) *QLDL có tách biệt với QLSX*: MIC đã trả lời, QLDL là nhóm dưới QLSX [MIC V1·C4] |

### 5.10. Quy trình 10: Dịch vụ vận chuyển (Grab)

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ | Thời hạn |
|---|---|---|---|---|---|---|
| 1. Tạm ứng | Oanh (ĐP TP, giữ tài khoản) [MIC V4·C20] | QLSX duyệt | | Khoảng 1 triệu mỗi tháng [MIC] | Đề nghị tạm ứng [Tệp S10 R20] | Hoàn ứng trong 7 ngày làm việc; quá hạn thì dừng tạm ứng mới [MIC] |
| 2. Tiếp nhận yêu cầu | Oanh | | Kho nhận, kho gửi, nội dung, phân bổ chi phí theo thương hiệu, ngày | | Zalo *VẬN CHUYỂN GRAB* [Tệp S10 R21] | |
| 3. Phiếu xuất kho mẫu (nếu lấy mẫu) | Oanh | QLSX ký | | KD xuất trên MISA; bản cứng gửi Kế toán trong ngày | Giấy đề nghị xuất vật tư [Tệp S10 R22] | |
| 4. Đặt xe | Oanh | | | Yêu cầu xuất hóa đơn trên app (tự về email Kế toán) | App Grab trên điện thoại [MIC V11·C19] | |
| 5. Quyết toán | Oanh chịu trách nhiệm hồ sơ [MIC V4·C5] | QLSX ký (thay TNĐP) [MIC V4·C5, C6] | Hóa đơn điện tử, lịch sử chuyến, phiếu đề nghị thanh toán [MIC V9·C11] | **2 bộ** đề nghị thanh toán: nội bộ phân bổ theo thương hiệu; thuế về Dego [MIC]; [Tệp S10 R24] | App Grab, mail, Drive *THEO DÕI CHI PHÍ* [MIC V9·C12] | Cuối tháng [MIC V9·C10] |

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Người giữ tài khoản [MIC V4·C20]; chi phí coi như đã duyệt từ báo giá đầu, không duyệt từng lần [MIC V4·C5]; ai ký [MIC V4·C6]; lúc nào và cần gì [MIC V9·C10–C12] | Không có mâu thuẫn | Tệp không ghi thời điểm bước nào [Tệp S10 R20–R24]. Đề xuất thêm email bộ phận nhận hóa đơn; chia thuế Grab đều cho thương hiệu [Tệp S10 R23, R24] |

### 5.11. Quy trình 11: Xử lý sự cố trong sản xuất

**Theo MIC, sự cố là một quy trình, chia hai nhánh** trong sản xuất và sau sản xuất [MIC V9·C7]. Phạm vi nhánh *trong sản xuất*: từ chuẩn bị NL, BTP, VTBB tới phối, gia công tại NCC, trước khi có thành phẩm [Tệp S11 R12]. **Khung chung** (dùng cho cả 5.11 và 5.12):

| Bước | Ai làm | Ai duyệt / chịu cuối | Đầu vào | Đầu ra | Công cụ | Thời hạn |
|---|---|---|---|---|---|---|
| 1. Nhận tin | Kho, KD, các ĐP báo qua Zalo [MIC V8·C15] | | Ảnh, video, mã, tên, số lượng, date, nguyên nhân, hiện trạng [MIC V8·C17]; thêm số đã bán, tồn tại khách [Tệp S11 R22] | | Zalo *Tên thương hiệu - Xử lý sự cố hằng ngày*, *1. SX - XỬ LÝ SỰ CỐ, HÀNG LỖI, PHÁP LÝ* | Khi phát sinh [MIC V11·C10]. **Chưa thống kê số vụ** [MIC V8·C16] |
| 2. Phân loại, phân luồng | ĐP TP xử lý nhanh **khi không ảnh hưởng giá và công nợ nhà gia công**, ghi vào tiến độ đơn; còn lại chuyển **CV XLSC** [MIC V2·C14, V9·C8, C9] | | Tiêu chí 5 nhóm (bảng dưới) [MIC V9·C7] | Phân loại tạm | Drive ĐP TP (xử lý nhanh) [MIC V9·C9]; file *1. SỰ CỐ CHI TIẾT SAU SẢN XUẤT* (CV XLSC) [MIC V8·C18, C19, V10·C3] | |
| 3. Kiểm tồn, tiến độ, hợp đồng | ĐP NL/BTP, ĐP VTBB, QLDL | | | Khả năng luân chuyển tồn, hạn cam kết với KD | [Tệp S11 R29] | |
| 4. Lập phương án | CV XLSC (ĐP TP nếu xử lý nhanh) | **TN QLDL**; vướng thì QLSX [MIC V2·C15] | Trao đổi KD, Lab, NCC, Kho, Pháp lý | Phương án; thông báo QLSX và bộ phận liên quan [MIC V8·C18] | | **Không có hạn cố định**, phòng cho là đúng vì mỗi vụ một khác [MIC V6·C3] |
| 5. Chứng từ thuế và nội bộ | Pháp lý / QLDL (hóa đơn); các ĐP (phiếu kho) | | | Hủy, điều chỉnh, xuất bổ sung hóa đơn; phiếu xuất, nhập, chuyển, hủy; BĐM mới nếu đổi | [Tệp S11 R36–R50] | |
| 6. Theo dõi tiến độ | CV XLSC | | | Cập nhật các bộ phận | [Tệp S11 R51] | |
| 7. Chi phí | CV XLSC | **Bên nào gây lỗi thì bên đó chịu** (nội bộ, KD hay NCC); vẫn phải thỏa thuận được với NCC [MIC V2·C15] | | Đề nghị thanh toán; biên bản cấn trừ công nợ; biên bản thu hồi tiền; biên bản làm việc / đánh giá NCC [MIC V9·C6] | Mẫu thống kê chi phí [Tệp S11 R52] | |
| 8. Lưu trữ, kết thúc | CV XLSC | | | Kết thúc khi làm xong phương án [MIC V11·C12]; lưu ý cho đơn sau | Drive *THEO DÕI SỰ CỐ* | |
| Nhánh: đơn xử lý lại | CV XLSC tạo mã | Duyệt **như đơn mới** (pháp lý, VTBB, NL/BTP, QLDL, Giá vốn, QLSX) [MIC V3·C5]; CV XLSC chịu trách nhiệm cuối, cần thì trình TN QLDL [MIC V4·C1] | QLSX hoặc KD yêu cầu xử lý lại [MIC V4·C11]; xác nhận tồn, pháp lý, vật tư từ các bộ phận [MIC V4·C14] | Yêu cầu ĐP TP xử lý lại | Drive sự cố, sheet *TIẾN ĐỘ XLY CÁC BP* [MIC V4·C13, C14] | Không thường xuyên, không ước được [MIC V4·C12] |

**Năm nhóm sự cố trong sản xuất** [MIC V9·C7]; nội dung [Tệp S11 R24–R35]: pháp lý (giấy tờ hết hạn, hóa đơn chậm) → ngưng sản xuất đến khi đủ; NL/BTP (chậm, thiếu, lỗi, dùng nhầm) → đẩy thay thế, tư vấn Lab và Pháp lý, chốt KD, sửa BĐM; VTBB (chậm, thiếu, móp bể, sai mockup) → tương tự; công thức phối (mẫu không đạt) → ngưng đến khi đạt hoặc hủy sau số lần phối cho phép; vận hành NCC (máy, công suất, không thống nhất giá, hóa đơn) → đôn đốc, ngưng đơn, hoặc chuyển NCC khác sau khi kiểm pháp lý, năng lực, nhãn, giá.

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Ai ghi file sự cố, xử lý nhanh [MIC V2·C14, V9·C8, C9]; thẩm quyền chi phí [MIC V2·C15]; kênh nhận tin, đầu vào [MIC V8·C15–C19]; tiêu chí phân loại [MIC V9·C7]; bắt đầu, kết thúc [MIC V11·C10, C12]; đơn xử lý lại [MIC V3·C5, V4·C1, C11–C14] | (1) Người làm chính: MIC là CV XLSC, ĐP TP chỉ xử lý nhanh [MIC V2·C14]; tệp ghi ĐP TP làm chính và tự kiểm mọi bước [Tệp S11 R22–R53]. **Theo MIC**. (2) Người duyệt: MIC là TN QLDL [MIC V2·C15]; tệp không có cột Người duyệt. **Theo MIC**. (3) Một hay hai quy trình: MIC gộp [MIC V9·C7]; tệp tách hai sheet. **Theo MIC** | Mức tiền nào bắt buộc trình QLSX: *chưa rõ*. Thống kê số vụ mỗi tháng chưa có [MIC V8·C16] |

### 5.12. Quy trình 12: Xử lý sự cố sau sản xuất

Dùng khung chung ở 5.11. Phạm vi: hàng tại NCC, tại kho Dr Xanh, tại khách hàng, khi vận chuyển [MIC V9·C7]; [Tệp S12 R12]. Người làm chính: **NV XLSC**, khớp với MIC [Tệp S12 R22–R51].

**Bốn nhóm sự cố** [Tệp S12 R24–R33]: pháp lý (giấy tờ thiếu, hết hạn sử dụng, sai nhãn) → bổ sung giấy tờ, thu hồi, thay nhãn, lên đơn xử lý lại; hàm lượng, chất lượng (đổi màu, lắng cặn, tách lớp, cháy lá, đóng thiếu thể tích) → gửi Lab; đạt thì hướng dẫn lại khách, không đạt thì thu hồi, tìm lỗi với Lab, NCC, lên đơn xử lý lại; VTBB (móp, thấm, nhầm chai, nhãn lỗi, thùng rách) → xác định bên phụ trách VTBB, thu hồi, xử lý lại; vận hành (giao thiếu, hỏng khi vận chuyển) → biên bản sự việc, bổ sung hàng.

**Sự cố hay gặp** [MIC]: lệch tỷ trọng Lab với máy chiết (BOOMGOLD tại AGA); hàng cận date, lắng đáy phải trả (Vatino Super); Basel không biết đổi công thức và màu dòng V1–V4 GENOL; lệch dòng công thức giữa KD và Hà Long (Thipro 550EC); NCC ngừng giữa chừng; thiếu NL, VTBB tới hạn; hao hụt vượt định mức; đơn đã gửi mới phát hiện thiếu giấy phép; giá chốt lệch giá duyệt; thất lạc khi chuyển kho; sai, trùng mã MISA; NCC giữ cọc nhãn không hoàn.

| Đã chốt qua hỏi đáp | Mâu thuẫn | Còn trống |
|---|---|---|
| Như 5.11 | Không có mâu thuẫn về người làm. Tệp không có cột Người duyệt; **theo MIC** là TN QLDL [MIC V2·C15] | Tệp ghi *đang gộp quy trình xử lý sự cố, cần xem lại* [Tệp S12 R1]. Chưa có hạn để ĐP TP khiếu nại NCC sau khi Kho nhận KCS đạt [MIC] |

### 5.13. Mục 13: Ngưng hợp tác với NCC GC

Tệp chỉ có tên mục, không có nội dung [Tệp ML R14]. MIC không có quy trình. Những gì hai nguồn có:

| Ý | Nguồn |
|---|---|
| Đánh giá dưới 60 điểm thì không hợp tác / ngưng, tìm NCC thay | [MIC]; [Tệp S19 R39] |
| NCC không ký PO thì đàm phán lại hoặc đổi NCC | [MIC V1·C11] |
| Phối không đạt sau 2 lần thì có thể đổi NCC hoặc dừng sản phẩm | [MIC] |
| KD đề xuất đổi NCC thì Sản xuất đổi | [MIC] |
| Trước khi chuyển đơn sang NCC khác: kiểm pháp lý, năng lực, nhãn hiệu, giá của nhà thay thế | [Tệp S11 R35] *(chỉ có ở tệp)* |
| Cần chính sách riêng từng NCC: điều kiện bắt buộc, điều kiện thỏa thuận được, **nhà dự phòng** | [MIC V6·C17, C19] |
| Ví dụ thật: Basel hết giấy phép SX thuốc từ 01/2024; nhãn cũ còn tồn chưa có phương án | [MIC] |

**Còn trống**: các bước ngưng (thu hồi NL, VTBB, khuôn, trục in; hoàn cọc nhãn; đối chiếu tồn và công nợ cuối; thanh lý hợp đồng; xử lý nhãn tồn), ai quyết ngưng. **Chưa ai trả lời.**

### 5.14. Mục 22: Sơ đồ sản xuất và mô tả công việc

Sheet *SƠ ĐỒ SX & MTCV* mà MỤC LỤC trỏ tới **không có trong tệp** [Tệp ML R23]. Mô tả công việc nằm ở một link Drive riêng [MIC V1·C4]. Sơ đồ và việc chính từng vị trí: xem **mục 3** (dựng theo MIC, phần này MIC đầy đủ hơn tệp).

Đã chốt qua hỏi đáp: tên gọi người đứng đầu [MIC V1·C3, V6·C1]; Kế toán sản xuất không có [MIC V1·C5]; tên chính thức ĐP TP [MIC V1·C7]; người theo từng NCC [MIC V1·C14, C15, C19]; việc của ĐP VTBB, Giá vốn, ĐP NL/BTP [MIC V3·C1–C3]; 7 bộ phận duyệt [MIC V6·C12]; TNĐP trống [MIC V6·C14]. **Còn trống**: người làm thay cho Giá vốn, ĐP NL/BTP, các Trưởng nhóm, QLSX [MIC V6·C2, V10·C5]; vị trí của Ms Trang, Ms Quyên, Ms Trinh, Mr Phú *(chưa rõ)*.

### 5.15. Mục 23: Phân quyền ký hồ sơ

Tệp ghi *Chưa có* [Tệp ML R24]. Bảng dưới gom từ hai nguồn; đây là bản nháp đầu tiên của mục này.

| Hồ sơ | Ai lập | Ai ký / duyệt | Nguồn |
|---|---|---|---|
| Hợp đồng, phụ lục với NCC GC | CV QLDL | TN QLDL kiểm duyệt → Pháp lý chung → Kế toán → **ĐDPL ký** (chỉ ký, không quyết) | [MIC V5·C2, V9·C3] |
| Danh mục sản phẩm hợp tác NCC mới | KD | CEO | [MIC V6·C8]; [Tệp S1 R19] |
| Bảng giá NCC GC | CV QLDL | QLSX | [Tệp S1 R42] *(chỉ có ở tệp)* |
| Phiếu duyệt giá đơn hàng | Giá vốn | QLSX, không cần Giám đốc | [MIC V2·C6] |
| Giá vốn thực tế gửi Kế toán | Giá vốn | TN QLDL | [MIC V3·C7, V4·C3] |
| BĐM BTP | ĐP NL/BTP | QLSX | [MIC V11·C4] |
| BĐM VTBB, BĐM TP, BĐM thuế | ĐP VTBB / QLDL | QLSX | [Tệp S7 R41] *(chỉ có ở tệp)* |
| Mã khai báo | Người khai | QLSX duyệt qua Zalo | [MIC V12·C3] |
| PO gửi NCC | ĐP TP | NCC ký xác nhận (ĐP TP theo dõi) | [MIC V2·C7, V1·C11] |
| Đề nghị nhập kho TP; phiếu kho NL/BTP, VTBB | ĐP TP / ĐP NL/BTP / ĐP VTBB | QLSX hiện tại; sheet Mẫu biểu ghi TNĐP | [Tệp S4 R29; S8; S9; S14 R3–R22] |
| LSX, đề nghị nhập kho công nợ NCC, phiếu xuất bán TP nội bộ | CV QLDL | QLDL tự ký | [Tệp S6 R23–R24; S14 R23, R26, R28] *(chỉ có ở tệp)* |
| Biên bản đối chiếu tồn kho, công nợ | CV QLDL | QLSX ký (có giấy ủy quyền QLSX ký biên bản đối chiếu tồn) | [MIC]; [Tệp S6 R25–R26; S9 R58] |
| Đề nghị tạm ứng, thanh toán NCC | CV QLDL | TN QLDL (theo Mẫu biểu) / QLSX (theo quy trình) | [Tệp S14 R34–R35; S6 R27] *(chỉ có ở tệp, tự lệch)* |
| Hồ sơ quyết toán Grab | Oanh | QLSX, sau này TNĐP | [MIC V4·C5, C6] |
| Phương án, chi phí sự cố | CV XLSC | TN QLDL, vướng thì QLSX | [MIC V2·C15] |
| Phiếu xuất kho mẫu test | ĐP TP | QLSX | [Tệp S4 R32; S10 R22] |
| Biên bản giao nhận (đúng pháp nhân nhận hóa đơn), biên bản hàng lỗi | **chưa rõ** | **chưa rõ** | [Tệp S14 R37–R38]; [MIC V6·C17] |

---

## 6. Danh mục

### 6.1. Từ ngữ cần hiểu đúng

| Từ | Nghĩa | Nguồn |
|---|---|---|
| Đơn hàng | 3 loại TP, BTP, xử lý lại; mỗi loại một mã; báo số đơn phải cộng đủ 3 loại | [MIC V1·C8] |
| NCC GC / NCC / Đối tác | Nhà máy gia công / bên bán NL, BTP, VTBB / gọi chung | [MIC V1·C9] |
| KD | Các thương hiệu nội bộ; ý KD gửi sang mặc định đã được duyệt | [MIC V1·C2, V6·C11] |
| Giám đốc | CEO (quyết), ĐDPL (chỉ ký); Quản lý thương hiệu thì gọi là KD | [MIC V6·C8, V9·C3] |
| Giá vốn | 3 loại: kinh doanh, sản xuất, kế toán | [MIC] |
| Dòng V | Dòng công thức (V1–V4...) của một sản phẩm; KD và SX đang theo dõi lệch nhau | [MIC] |
| Nội bộ / Thuế | Hai hệ số liệu chạy song song: nội bộ theo màu, dòng V, thương hiệu, nơi chứa; thuế theo tên pháp lý và công ty sở hữu | [MIC] |
| Kho NCC / Kho NCCXL | Kho tại NCC GC / kho xử lý (không có địa điểm thật) | [Tệp S2 R69] *(chỉ có ở tệp)* |
| BTP cấu thành | Công nợ NCC GC gồm ruột và phần NCC không tách được (thùng, chai, phí đóng gói) | [Tệp S2 R23] *(chỉ có ở tệp)* |
| Mã đơn vị xuất hóa đơn | I IDA Global; II Agricare; IV ABA; V Dego Holding; VI Bamboo; VII Nông nghiệp DEGO; VIII Dr Xanh; IX N2SBIO | [Tệp S2 R67] *(chỉ có ở tệp)* |

Sheet thuật ngữ của tệp có 60 từ viết tắt [Tệp S16]; thiếu TNĐP, CV, KCS, PO, ĐDPL và các tiền tố mã ở mục 6.2.

### 6.2. Mã khai báo (quy tắc đặt mã)

Tiền tố khớp giữa hai nguồn [MIC]; [Tệp S2 R40–R69]. Cột *Cách đặt* lấy từ tệp *(chỉ có ở tệp)*.

| Tiền tố | Loại | Cách đặt | Ai khai |
|---|---|---|---|
| NLNK / NLT / NA | NL nhập khẩu / NL kỹ thuật / phụ gia (NL mã hóa) | Tiền tố + 4 số tăng dần | Thu mua, ĐP NL/BTP |
| BTPR / BTPM / BTPNK | BTP ruột / BTP mua (dự kiến bỏ 2027) / BTP nhập khẩu | Tiền tố + 4 số | Thu mua; ĐP NL/BTP (BTPM) |
| BTPCT | BTP cấu thành | BTPCT + 4 số cuối mã HH | QLDL |
| BTP R&D | BTP phân bón do Lab phối | Theo quy tắc Lab | Lab |
| N + TG / TN / HD / HG | Túi giấy / túi nhôm / nhãn decal / nhãn giấy | N + mã chất liệu + 4 số cuối mã HH | ĐP VTBB |
| C, NAP, COC, SEAL, HOP, XO, CAN, LON, TH, NDT | Chai, nắp, cốc, seal, hộp, xô, can, lon, thùng (kèm viết tắt thương hiệu), nhãn dán thùng | Tiền tố + chất liệu / hình dạng + 4 số; tên nội bộ đủ thông số | ĐP VTBB |
| CPNK / PPT / PĐG | Chi phí nhập khẩu / phí gia công phối trộn / phí sang chai đóng gói | Tiền tố + 4 số | Thu mua (CPNK); QLDL |
| HH | Hàng hóa (thành phẩm) | HH + 4 số; tên gồm thương hiệu, mã đơn vị xuất hóa đơn, quy cách | Thiết kế |
| (MST) | NCC GC, NCC thu mua, đơn vị vận chuyển | Mã = mã số thuế | QLDL, ĐP TP, Thu mua |
| KHO NCC_, KHO NCCXL_ | Kho | Tên viết tắt NCC | ĐP TP, ĐP VTBB, ĐP NL/BTP |
| **(chưa có)** | **Mã đơn TP, đơn BTP, đơn xử lý lại, mã sự cố, mã BĐM** | **chưa có** [Tệp S2 R1] | |

### 6.3. Biểu mẫu chính

Gộp từ danh sách biểu mẫu của từng quy trình và sheet Mẫu biểu [Tệp S14 R2–R39], MIC [MIC V6·C4, V9·C1, V9·C17]. Bản gốc chứng từ để ở P TCKT, Sản xuất giữ bản scan [MIC V10·C7]; [Tệp S14].

| Nhóm | Biểu mẫu |
|---|---|
| NCC mới | Checklist NCC GC mới: Mẫu 01 danh mục hợp tác, Mẫu 02 checklist hợp đồng, Mẫu 03 nhóm làm việc, Mẫu 04 tổng hợp giá (mẫu cũ, chưa chốt), **Mẫu 05 Biên bản nội bộ** [Tệp TĐ R61–R65]; [MIC V9·C1] |
| Đơn hàng | Yêu cầu đặt hàng TP; Đơn đặt hàng / mẫu gửi đơn NCC; Phiếu duyệt giá 3 mức (form mới có giá); Mẫu báo cáo tiến độ ngày; Danh sách nhận hàng; Checklist kiểm hàng TP nhận từ NCC [Tệp S4 R45–R53; S14 R39] |
| Định mức | BĐM BTP, BĐM VTBB, BĐM TP (nội bộ và thuế); Phiếu ký duyệt BĐM; Danh sách quản lý BTP phân bón / thuốc [Tệp S14 R3, R15, R21; S8 R76] |
| Kho | Phiếu đề nghị nhập / xuất / chuyển kho (NL, BTP, VTBB, TP); Phiếu đề nghị xuất bán nội bộ; Phiếu yêu cầu xuất hóa đơn; Phiếu đề nghị đưa vào chi phí; Phiếu đề nghị xuất hủy; Giấy đề nghị xuất vật tư (mẫu test); Phiếu đề nghị phối BTP; LSX [Tệp S14 R4–R26] |
| Mua, khảo sát | Phiếu đề nghị mua hàng hóa dịch vụ (nội bộ + thuế); Phiếu yêu cầu test của Lab; Phiếu yêu cầu thử nghiệm NCC GC; Form khảo sát VTBB - cọc nhãn - mẫu (NL/BTP dùng tạm) [Tệp S8 R80; S9 R72; S1 R64] |
| Đối chiếu | Đồng bộ mã công ty - NCC GC; Biên bản xác nhận tồn kho; Biên bản kiểm tra và giải trình; Giấy ủy quyền QLSX ký biên bản; Biên bản đối chiếu công nợ (nội bộ và thuế) [Tệp S9 R79–R83; S14 R29–R30] |
| Thanh toán | **14 chứng từ**: đề nghị thanh toán (của mình và của NCC), hóa đơn GTGT, hợp đồng, phụ lục, đơn đặt hàng, phiếu mua hàng MISA, phiếu nhập kho, phiếu xuất kho, phiếu giao hàng, bảng xác nhận công nợ, biên bản đối chiếu công nợ, ủy nhiệm chi, giấy báo nợ [MIC V6·C4]. Thêm: giấy đề nghị tạm ứng; Form Dự chi; Form Pháp lý - Chi phí [Tệp S6 R42–R47] |
| Sự cố | Biên bản thu hồi khoản tiền phát sinh; Biên bản cấn trừ công nợ; Biên bản làm việc / đánh giá NCC; Mẫu thống kê chi phí [MIC V9·C6]; [Tệp S11 R57–R63; S12 R55–R57] |
| Chỉ có tên, chưa có nội dung | Đơn đặt hàng, Biên bản giao nhận, Biên bản hàng lỗi [Tệp S14 R36–R38]; biểu mẫu chấm điểm NCC [MIC] |

### 6.4. Công cụ

QLSX là chủ sở hữu mọi Drive và cấp quyền [MIC V1·C20]. Google Sheets hay lỗi mạng; chưa có hướng dẫn thao tác cho người mới [MIC V10·C15].

| Công cụ | Ai dùng | Dùng làm gì | Tình trạng dựng (tệp) |
|---|---|---|---|
| Drive *1. DATA DỮ LIỆU ĐẦU VÀO SX* (Data 1) | Người khai mã | Danh mục gốc; **đổi cấu trúc là mọi Drive phải chạy lại** [MIC]; [Tệp TĐ R3] | *Xem lại và chốt Data 1* [Tệp TĐ R192–R200]; thông số VTBB, NL *Chưa bắt đầu* [Tệp TĐ R129–R133] |
| Drive *SX-ĐIỀU PHỐI THÀNH PHẨM* (sheet ĐIỀU PHỐI, DUYỆT ĐƠN HÀNG, GỬI ĐƠN NCC, Kết quả KCS, Báo cáo kho, Nhập kho) | ĐP TP | Đơn hàng, 7 xác nhận, PO, tiến độ, KCS, kho TP tại NCC [MIC V6·C9, V10·C1, C17] | Đang thực hiện [Tệp TĐ R135–R141] |
| Drive *4. XUẤT NHẬP TỒN - VTBB* | ĐP VTBB | Tồn, mua mới, đối chiếu, cọc nhãn, phiếu [MIC V10·C2] | Hoàn thành [Tệp TĐ R142–R171] |
| Drive *3. XUẤT NHẬP TỒN NL, BTP* | ĐP NL/BTP | Tồn, mua, phối, LSX BTP, tính giá BTP [MIC V10·C19] | Hoàn thành [Tệp TĐ R172–R186] |
| Drive *4. Quản lý giá vốn 2026* và *Tổng thông tin chính sách giá vốn* | Giá vốn | Tính giá vốn, lưu giá mọi NCC [MIC V10·C16] | 59 sheet, tất cả *Đang thực hiện* [Tệp TĐ R5–R59] |
| Drive *3. DỰ TRÙ KINH DOANH*, sheet *7. YC MUA NL, BTP* | KD, Giá vốn, ĐP NL/BTP | KD gửi yêu cầu, SX trả kết quả [MIC V11·C8] | Đang thực hiện |
| Drive *2. QLDL NCC*, *3. Hóa đơn*, *4. Công nợ, thanh toán*, *5. HSTT*; *Thống kê hợp đồng* | QLDL | BĐM TP, LSX, hóa đơn, công nợ, dự chi, phí lưu kho, hao hụt | Đang thực hiện; Drive 5 *chưa có* [Tệp TĐ R60–R128] |
| Drive *Sự cố* (file *1. SỰ CỐ CHI TIẾT SAU SẢN XUẤT*), Drive *Pháp lý sản xuất* | CV XLSC, Pháp lý | Sự cố; pháp lý [MIC V10·C3, C20] | Quy trình sự cố *cần check lại* [Tệp TĐ R188] |
| Drive Lab | Lab, ĐP NL/BTP | Công thức kỹ thuật [MIC V11·C5] | |
| Zalo | Mọi vị trí | Trao đổi, duyệt mã, báo duyệt đơn, gửi PO | Khoảng 40–50 nhóm (ước, đếm từ danh sách nhóm của 10 sheet) |
| Signal *GROUP GIÁ VỐN KINH DOANH* | Giá vốn | Gửi giá vốn cho Kế toán | [MIC V4·C17]; [Tệp S3 R35] |
| MISA (Thuế, Nội bộ) | Kế toán; SX được xem | Hạch toán; đối chiếu tồn | [MIC] |
| App Grab, Word, Email | Oanh; QLDL | Đặt xe; hợp đồng; hóa đơn Grab | [MIC V9·C12, V9·C19] |

MIC đếm được 117 công cụ và 97 tài liệu, biểu mẫu; danh mục công cụ đã hỏi 10 lần, coi như đủ [MIC V10·C7].

---

## 7. Tiền, thuế, chứng từ

Tóm theo MIC [MIC mục 12].

**Chứng từ với nhà gia công là vướng lớn nhất** [MIC]:
- Mỗi nhà một kiểu. Nhiều nhà từ chối ký PO, đề nghị thanh toán, xác nhận công nợ (mục 4.2).
- Biên bản giao nhận nhiều lần không đúng pháp nhân nhận hóa đơn. Nhà gia công chỉ làm việc với một công ty, trong khi DEGO có nhiều công ty nội bộ [MIC V6·C17].
- Nhà gia công sở hữu tên sản phẩm thì chỉ xuất một dòng hóa đơn (BTP và phí gia công gộp). Sản xuất phải tự tách, không dùng MISA đối chiếu tồn BTP được [MIC].
- Phần lớn nhà gia công chỉ gửi tồn tổng tháng, không tách theo công ty, không theo số lô. Hao hụt phải chấp nhận số của họ [MIC].
- Chứng từ giao nhận bản cứng nộp Kế toán trong ngày; Kế toán hạch toán từ giấy, không có hạn, không gửi đối soát ngược cho Sản xuất [MIC V10·C9].

**Hai hệ số liệu và tiền nằm ngoài sổ thuế** [MIC]:

| Khoản | Số tiền | Nguồn |
|---|---|---|
| VTBB công ty mang sang nhà gia công, không vào cấu thành thuế (Thái Nông, Hà Long không chịu ghi vào hợp đồng) | Trên 5 tỷ | [MIC V6·C19] |
| Phí thuê tên đăng ký sản phẩm không lấy được hóa đơn; KD muốn phân bổ vào giá vốn từng thương hiệu | Hơn 650 triệu | [MIC] |
| Thái Nông xuất hóa đơn thiếu | Khoảng 28% chi phí (trả ngoài 141,7 triệu; túi VTBB 57,5 triệu) | [MIC] |
| An Nông khuyến mãi hàng 0đ rồi xuất hóa đơn giá trung bình | (không có số) | [MIC] |
| Phối đổi màu BTP lần 2 không có hóa đơn | Khoảng 22,8 triệu mỗi năm bị loại thuế; phối lại từ đầu thì tồn hơn 262 triệu | [MIC] |
| Chi phí ngoài dự toán chưa có định mức; tạm ứng quá 30 ngày không quyết toán thành công nợ cá nhân, bị treo lương | | [MIC] |
| **Chiết khấu, hoa hồng ngoài hợp đồng** | *Xem riêng với Kế toán trưởng* | [MIC V6·C19]; [Tệp S6 R35] |

---

## 8. Đánh giá

### 8.1. Độ sẵn sàng để bàn giao

Mức: **Dùng được** = người mới đọc làm theo được; **Sửa tệp** = nội dung có, nhưng phải sửa cho khớp MIC hoặc điền chỗ trống; **Thiếu** = chưa có nội dung.

| Quy trình | MỤC LỤC ghi | Mức | Việc phải làm trước 31/12 |
|---|---|---|---|
| 1. NCC mới | Hoàn thành | Sửa tệp | Sửa người duyệt hợp đồng, Mẫu 05 theo MIC; điền người làm bước 3 |
| 2. Khai báo SX | Cần kiểm tra lại | **Thiếu** phần mã đơn | Thêm quy tắc mã đơn, mã sự cố, mã BĐM; điền mục V–VII |
| 3. Giá vốn | Hoàn thành | Sửa tệp | Sửa bước giá vốn thực tế và bước biên lợi nhuận theo MIC |
| 4. Đơn hàng SX GC | Hoàn thành | Dùng được, cần bổ sung | Thêm bước QLSX duyệt, danh sách trạng thái, sửa câu Lab 2 ngày |
| 5. Pháp lý SX | Hoàn thành | **Thiếu** | Điền người duyệt, tần suất theo dõi hạn; trả lời phạm vi duyệt |
| 6. Quản lý NCC GC | Hoàn thành | Dùng được | Điền *Drive ....*, bộ 14 chứng từ |
| 7. BĐM thuế | Hoàn thành | Dùng được | Điền mục biểu mẫu |
| 8. NL/BTP | Hoàn thành | Sửa tệp | Bước nhập kho dư sản xuất; nguồn yêu cầu khảo sát; danh sách bên chuẩn bị NL |
| 9. VTBB | Hoàn thành | Sửa tệp | Chốt 4 điểm cuối sheet; phần thuế của hao hụt; cọc nhãn đủ 6 nhà |
| 10. Grab | Hoàn thành | Dùng được | Thêm hạn mức, hạn hoàn ứng theo MIC |
| 11–12. Sự cố | Cần kiểm tra lại | Sửa tệp | Gộp theo MIC; đổi người làm nhánh trong SX; thêm cột Người duyệt (TN QLDL) |
| 13. Ngưng hợp tác | (không ghi) | **Thiếu** | Viết mới |
| 14. Mẫu biểu | Cần kiểm tra lại | Sửa tệp | Điền 3 chứng từ trống; sửa Nơi duyệt cho khớp quy trình |
| 17. TT NCC GC, 18. TT SP | Đang thực hiện | **Thiếu** | Chép số liệu từ MIC (mục 4.2); điền bên chuẩn bị NL, VTBB, hao hụt |
| 19. Tiêu chí đánh giá | Cần kiểm tra lại | Sửa tệp | Đổi chu kỳ thành theo quý; làm biểu mẫu chấm |
| 20. Lưu trữ | Đang thực hiện | Sửa tệp | Đang chép của Thu mua; chỉnh cho đơn gia công, LSX, BĐM |
| 22. Sơ đồ, MTCV | Cần kiểm tra lại | **Thiếu** sheet | Chép mục 3 vào tệp; đính link mô tả công việc |
| 23. Phân quyền ký | Cần kiểm tra lại | **Thiếu** | Dùng bảng 5.15 làm bản nháp |

Tóm lại: 4 quy trình dùng được, 9 phải sửa tệp, 6 mục còn thiếu. MỤC LỤC cập nhật 14/8 nên **không dùng làm thước đo** (mâu thuẫn S-03 ở mục 9).

### 8.2. Rủi ro bàn giao

| Rủi ro | Nguồn | Người kế nhiệm vướng ở đâu |
|---|---|---|
| Chị Ngân là chủ sở hữu mọi Drive | [MIC V1·C20] | Phải chuyển quyền sở hữu trước 31/12; tài khoản bị khóa là mất quyền quản trị |
| *Duyệt trước, cho nợ hồ sơ* chỉ dựa vào kinh nghiệm QLSX | [MIC V3·C4, V10·C11] | Không biết đơn nào được đi khi thiếu giấy tờ |
| Chị Ngân giữ cùng lúc QLSX, TNĐP, người làm thay Giá vốn | [MIC V1·C12, V2·C20, V6·C2] | Người kế nhiệm nhận 3 ghế một lúc |
| Lịch sử duyệt nằm trong Zalo, giá vốn gửi qua Signal | [MIC V12·C3, V3·C15, V4·C17] | Không chuyển quyền trưởng nhóm chat thì mất dấu vết |
| Data 1 chưa chốt; 138/196 sheet Drive còn đang dựng | [Tệp TĐ R3, R192–R200] | Nhận một hệ bảng tính dở dang, không có hướng dẫn [MIC V10·C15] |
| Tài khoản Grab và tạm ứng nằm ở Oanh | [MIC V4·C20] | Oanh nghỉ thì mất đường đặt xe, khoản tạm ứng treo |
| Chính sách riêng từng NCC chưa viết ra | [MIC V6·C17, C19]; [Tệp S17] | Không biết nhà nào chịu ký gì, nhận gì |
| Thỏa thuận ngoài hợp đồng | [MIC V6·C19] | Xem riêng với Kế toán trưởng |
| Không có người làm thay ở các vị trí một người | [MIC V6·C2, V10·C5] | Một người nghỉ là đứng việc |
| Phạm vi bàn giao phụ thuộc app có kịp không | [MIC V1·C10] | Còn 8 tuần. Nên chuẩn bị phương án *không kịp app*: tệp quy trình phải tự đứng được |

### 8.3. Gợi ý cho ERP

- **Đơn gia công** là thực thể gốc: 3 loại; gắn NCC GC, thương hiệu đặt, **công ty sở hữu pháp lý** và công ty nhận hóa đơn [MIC V1·C8]; [Tệp S5 R22]. Đơn xử lý lại trỏ về sự cố gốc [MIC V3·C5].
- **7 nhánh xác nhận chạy song song** trên cùng đơn, rồi QLSX duyệt; cho *duyệt có điều kiện*, ghi rõ điều kiện đang nợ và hạn [MIC V6·C12, V3·C4].
- **Bộ trạng thái đơn** phải chốt trước khi làm (câu 2 mục 10). Bản nháp: tiếp nhận, chờ xác nhận, chờ QLSX duyệt, đã gửi NCC, đang sản xuất, có hàng chưa lấy hóa đơn, đã nhận hàng, chờ Lab, hoàn thành (khóa), test không đạt, chờ thông tin KD, hủy.
- **BĐM 3 tầng × 2 bản** (nội bộ, thuế), có phiên bản, vì BĐM phải đổi theo thực tế [MIC V2·C5]; [Tệp S7 R6; S8 R22].
- **Kho tại NCC GC** là kho thật, tách theo công ty nội bộ. Phiếu kho mang cặp *công ty bán, công ty mua* để sinh đúng phiếu nội bộ hay phiếu thuế [MIC]; [Tệp S8 R40–R41; S9 R43].
- **Danh mục mã** theo mục 6.2, có luồng khai, QLSX duyệt, Kế toán xác nhận, thay cho nhóm Zalo [MIC V8·C10–C14]. **Làm đầu tiên**, vì mọi Drive đang phụ thuộc Data 1.
- **Hồ sơ NCC GC**: hợp đồng, bảng giá, giấy phép, hồ sơ pháp lý sản phẩm, có ngày hết hạn và nhắc trước 3 tháng (6 tháng nếu công ty sở hữu tên) [Tệp S6 R32–R33]. Làm sớm, vì *đơn đã gửi mới phát hiện thiếu giấy phép* là sự cố có thật [MIC].
- **Giá theo vai trò**: phiếu duyệt giá 3 mức; PO không có giá; giá bảo mật giữa các thương hiệu [MIC V1·C11]; [Tệp S4 R24; TĐ R142].
- **Sự cố**: một luồng, hai nhánh, 5 + 4 nhóm phân loại, có người duyệt (TN QLDL), chi phí, bên chịu; sinh biên bản cấn trừ [MIC V9·C7, V2·C15].
- **Đối chiếu tháng** tồn và công nợ, hạn ngày 20 [MIC]. Làm sau, vì còn phụ thuộc MISA.
- **Đánh giá NCC** theo quý, khung 100 điểm của tệp, lấy điểm từ dữ liệu ERP (lỗi, trễ, hao hụt) thay vì chấm tay [MIC V9·C13]; [Tệp S19].
- **Thứ tự**: (1) danh mục mã và NCC GC; (2) đơn gia công, 7 xác nhận, trạng thái; (3) BĐM và kho tại NCC; (4) hồ sơ, hạn pháp lý; (5) sự cố; (6) đối chiếu, thanh toán, đánh giá NCC.

---

## 9. Sổ mâu thuẫn và câu đã trả lời

### 9.1. Mâu thuẫn MIC và tệp (17 dòng, đã viết theo MIC)

| # | Chủ đề | MIC nói | Tệp nói | Kết luận | Nguồn |
|---|---|---|---|---|---|
| M-01 | Giá vốn thực tế: bắt đầu lúc nào | Khi hàng về kho Dr Xanh | Trong ngày nhận LSX từ QLDL | **Theo MIC** | [MIC V4·C15]; [Tệp S3 R35] |
| M-02 | Giá vốn thực tế: ai ký | TN QLDL | QLSX | **Theo MIC** | [MIC V3·C7, V4·C3]; [Tệp S3 R35] |
| M-03 | Đánh giá NCC: chu kỳ | Theo quý hoặc khi QLSX yêu cầu | 6 tháng một lần hoặc đột xuất | **Theo MIC** | [MIC V9·C13]; [Tệp S19 R40] |
| M-04 | Đánh giá NCC: ai làm | CV QLDL tiến hành, QLDL lưu | Các bộ phận chấm độc lập, QLSX phê duyệt | **Theo MIC**; có thể là QLDL tổng hợp điểm các bộ phận (*chưa rõ*) | [MIC V9·C13, V11·C1, V12·C1]; [Tệp S19 R40] |
| M-05 | Lab trả kết quả | Ngoại dạng 1–2 ngày, hàm lượng 14 ngày | *R&D trả kết quả chậm nhất 2 ngày* (cùng ô có 14 ngày) | **Theo MIC** | [MIC V3·C6]; [Tệp S4 R32] |
| M-06 | Sự cố trong SX: ai làm chính | CV XLSC; ĐP TP chỉ xử lý nhanh khi không ảnh hưởng giá, công nợ | ĐP TP làm và tự kiểm mọi bước | **Theo MIC** | [MIC V2·C14, V9·C8, C9]; [Tệp S11 R22–R53] |
| M-07 | Sự cố: một hay hai quy trình | Một quy trình, hai nhánh | Hai sheet riêng | **Theo MIC** | [MIC V9·C7]; [Tệp S11, S12] |
| M-08 | Cảnh báo biên lợi nhuận | SX bỏ cảnh báo, KD tự kiểm | Âm biên thì Giá vốn gửi KD xem lại; có sheet Biên giá | **Theo MIC**; ngày áp dụng *chưa rõ* | [MIC V3·C2]; [Tệp S3 R32; TĐ R40] |
| M-09 | Duyệt hợp đồng NCC mới | TN QLDL kiểm duyệt rồi Pháp lý, Kế toán, ĐDPL ký | QLSX duyệt, ký nháy | **Theo MIC** | [MIC V5·C2]; [Tệp S1 R47–R48] |
| M-10 | Mẫu 05 bàn giao cho ai | Giá vốn, Giá vốn báo KD | Thu mua, KD, P TCKT, Pháp lý, nội bộ SX | **Theo MIC** | [MIC V4·C4]; [Tệp S1 R49] |
| M-11 | Ai ký BĐM BTP, BĐM VTBB, phiếu kho | QLSX ký | Sheet Mẫu biểu ghi TNĐP | **Theo MIC** (hiện tại); sau khi có TNĐP phải chốt lại | [MIC V11·C4, V4·C6]; [Tệp S14 R3–R22] |
| M-12 | Khảo sát NL/BTP: yêu cầu từ ai, trả ai | Từ Giá vốn, trả Giá vốn | KD gửi đề nghị, trả KD qua Drive | **Theo MIC** | [MIC V11·C3]; [Tệp S8 R62–R63] |
| M-13 | Hạn phản hồi dự trù NL/BTP | 5 ngày làm việc | 5 ngày | **Theo MIC** | [MIC]; [Tệp S8 R32] |
| M-14 | Báo cáo hằng ngày | 16h | Trước 16h30 | **Theo MIC** (mức thấp) | [MIC]; [Tệp S4 R27] |
| M-15 | Thời điểm lập hồ sơ thanh toán | Khi đến hạn | Trước hạn 7 ngày | **Theo MIC** (mức thấp) | [MIC V4·C10]; [Tệp S6 R27; S14 R34–R35] |
| M-16 | NCC có cọc nhãn | 6 đối tác; thiếu dữ liệu Âu Việt, Đại Tâm, Basel, An Nông | 4 nhà: An Nông, Âu Việt, Đại Tâm, Thu Loan | **Theo MIC**; danh sách đủ 6 nhà *chưa rõ* | [MIC]; [Tệp S9 R35] |
| M-17 | Khung bước quy trình đơn hàng | 7 bước, có bước *QLSX duyệt* | 7 bước khác, không có bước duyệt, có nhập kho, hóa đơn, hủy đơn | **Theo MIC** làm khung; tệp bổ sung bước 4a, 4b, phần B | [MIC V12·C2]; [Tệp S4 R16–R41] |

### 9.2. Chỗ tệp tự mâu thuẫn hoặc tệp trống mà chưa ai trả lời

| # | Chủ đề | MIC nói | Tệp nói | Kết luận | Nguồn |
|---|---|---|---|---|---|
| S-01 | Ai khai mã BTP ruột | ĐP NL/BTP là một trong những người khai trình QLSX (không nói riêng BTPR) | Thu mua (S2) / Oanh (TĐ) | Chưa ai trả lời | [MIC V8·C12]; [Tệp S2 R20; TĐ R74] |
| S-02 | Ai phát cảnh báo hạn giấy tờ pháp lý | (không có) | Pháp lý SX định kỳ (S5) / Pháp lý chung, QLDL bổ sung trước 3–6 tháng (S6) | Chưa ai trả lời | [Tệp S5 R27; S6 R32] |
| S-03 | MỤC LỤC và nội dung sheet | (không có) | ML ghi Hoàn thành cho QT 5, 8, 9; nội dung còn ghi *chưa ban hành, còn thiếu* | Chưa ai trả lời; tạm coi nội dung sheet là đúng | [Tệp ML R6, R9, R10; S5 R2; S8 R48; S9 R112; TĐ R190] |
| S-04 | Quy tắc mã đơn, mã sự cố, mã BĐM | Mỗi loại đơn có mã riêng | *Xem lại quy tắc...*, chưa có | Chưa ai trả lời | [MIC V1·C8]; [Tệp S2 R1] |
| S-05 | Danh sách trạng thái đơn | Có khóa đơn khi hoàn thành | Nhắc rải rác 6 trạng thái | Chưa ai trả lời | [MIC V8·C8]; [Tệp S4 R29–R40] |
| S-06 | Đơn chốt sau kết quả nào của Lab | Cần kết quả Lab | (không rõ) | Chưa ai trả lời | [MIC V8·C7]; [Tệp S4 R32] |
| S-07 | Pháp lý duyệt cho đơn BTP, mua NL/BTP | Đơn xử lý lại thì có | Câu hỏi mở đầu sheet | Chưa ai trả lời (phần đơn BTP, mua NL/BTP) | [MIC V3·C5]; [Tệp S5 R2] |
| S-08 | Ngưng hợp tác NCC | Chỉ có ngưỡng điểm, đổi NCC khi cần | Chỉ có tên mục | Chưa ai trả lời | [MIC]; [Tệp ML R14] |
| S-09 | Phân quyền ký biên bản giao nhận, biên bản hàng lỗi | Biên bản giao nhận hay sai pháp nhân | Chỉ có tên chứng từ | Chưa ai trả lời | [MIC V6·C17]; [Tệp S14 R37–R38] |
| S-10 | Nhập kho đổ thu / dư sản xuất | (không có) | *Sẽ xây dựng sau* | Chưa ai trả lời | [Tệp S8 R48] |
| S-11 | Thuế phần hao hụt, tỷ lệ cho phép | Hao hụt phải chấp nhận số của NCC | Chưa thống nhất với Kế toán | Chưa ai trả lời | [MIC]; [Tệp S9 R53, R82] |
| S-12 | Ai chuẩn bị NL, BTP, VTBB theo từng sản phẩm, NCC | (không có bảng) | Chưa có danh sách; cột trống | Chưa ai trả lời | [Tệp S8 R29; S18 R2] |
| S-13 | Data 1 chốt lúc nào | Đổi Data 1 là mọi Drive chạy lại | *Xem lại và chốt* | Chưa ai trả lời | [MIC]; [Tệp TĐ R192–R200] |
| S-14 | Phí lưu kho từng NCC | *Xem TT NCC GC* | Sheet TT NCC GC trống | Chưa ai trả lời | [MIC V1·C18]; [Tệp S17] |
| S-15 | MST trùng giữa Thành Phát và PES | (không có) | Cả hai 1801685413 | Chưa ai trả lời | [Tệp S17 R17–R18] |
| S-16 | NCC chưa có người phụ trách | Đại Tâm, Thành Phát chưa có ĐP TP; ATC, Dubai chưa có QLDL | (không có) | Chưa ai trả lời (MIC tự thiếu) | [MIC V1·C14, C19] |
| S-17 | 4 điểm *cần thống nhất trước khi ban hành* của sheet VTBB | Điểm (3) đã có: QLDL là nhóm dưới QLSX | Mục VIII thuế, ghi chú dở II.3 và VII.1.2, thời lượng | Điểm (3) **theo MIC**; 3 điểm còn lại chưa ai trả lời | [MIC V1·C4]; [Tệp S9 R112] |
| S-18 | Tiêu chuẩn duyệt trước, cho nợ hồ sơ | Có, nhưng không có văn bản | (không có) | Chưa ai trả lời | [MIC V3·C4, V10·C11] |
| S-19 | Hạn cho 7 bộ phận, Thiết kế, Kế toán | Chưa có; phòng xác nhận đúng hiện trạng | Cột Thời lượng trống | Người chủ quyết | [MIC V4·C9, V10·C8, C9] |

### 9.3. Chỗ đã trả lời: MIC lấp chỗ tệp thiếu, hoặc tệp bổ sung cho MIC

| # | Chủ đề | MIC nói | Tệp nói | Kết luận | Nguồn |
|---|---|---|---|---|---|
| A-01 | Tên người 7 bộ phận duyệt | Oanh, Ly, Hương, Huỳnh, Thi, QLDL theo NCC, Ngân | Chỉ tên bộ phận | Theo MIC (tệp thiếu) | [MIC V6·C12]; [Tệp S4 R17] |
| A-02 | QLSX duyệt ở đâu, lúc nào | Cột duyệt trên Drive Điều phối, khi đủ xác nhận | (không có bước) | Theo MIC (tệp thiếu) | [MIC V3·C11–C13, V4·C7] |
| A-03 | PO có giá không | Không có giá | (không nói) | Theo MIC (tệp thiếu) | [MIC V1·C11] |
| A-04 | Điều kiện hoàn thành đơn | Lab, hóa đơn, Kho ký nhận đủ; khóa đơn | *Đạt thì chuyển hoàn thành* | Theo MIC (tệp thiếu) | [MIC V8·C6–C9]; [Tệp S4 R32] |
| A-05 | Ai kết luận đạt / không đạt | Lab | (không nói) | Theo MIC (tệp thiếu) | [MIC V3·C16] |
| A-06 | Gửi mẫu Lab bao nhiêu đơn | 100% | (không nói) | Theo MIC (tệp thiếu) | [MIC V3·C18] |
| A-07 | Bộ hồ sơ thanh toán | 14 chứng từ | Liệt kê dở, ghi *...* | Theo MIC (tệp thiếu) | [MIC V6·C4]; [Tệp S6 R27] |
| A-08 | Người duyệt phương án sự cố | TN QLDL, vướng thì QLSX | Không có cột | Theo MIC (tệp thiếu) | [MIC V2·C15] |
| A-09 | Bên chịu chi phí sự cố | Bên gây lỗi chịu | *Xác định bộ phận chịu* | Tệp bổ sung, không mâu thuẫn | [MIC V2·C15]; [Tệp S11 R52] |
| A-10 | Đơn xử lý lại | CV XLSC tạo mã, duyệt như đơn mới | *Lên đơn xử lý lại cho ĐP TP* | Theo MIC (chi tiết hơn) | [MIC V3·C5, V4·C1]; [Tệp S12 R30–R32] |
| A-11 | Chữ Giám đốc ở từng bước | CEO hay ĐDPL theo bước | Chỉ ghi *Giám đốc* | Theo MIC (tệp thiếu) | [MIC V6·C8, V9·C3] |
| A-12 | QLSX duyệt mã khai báo bằng gì | Chỉ qua Zalo; người khai chịu trách nhiệm | *Trình duyệt QLSX* | Tệp bổ sung, không mâu thuẫn | [MIC V12·C3, V3·C8]; [Tệp S2 R36] |
| A-13 | Mẫu 05 lập lúc nào | Sau ký, hoặc trước ký nếu người ngoài phòng đàm phán | Trước khi đặt đơn đầu tiên | Theo MIC (chi tiết hơn) | [MIC V8·C5]; [Tệp S1 R49] |
| A-14 | Grab: người giữ, lúc quyết toán, hạn mức, hoàn ứng | Oanh; cuối tháng; khoảng 1 triệu; hoàn ứng 7 ngày làm việc | Không có thời điểm, hạn mức | Theo MIC (tệp thiếu) | [MIC V4·C20, V9·C10]; [Tệp S10] |
| A-15 | Đối chiếu tồn lệch thì làm gì | Chứng minh cho NCC, theo đến khi khớp | Lập biên bản giải trình | Tệp bổ sung, không mâu thuẫn | [MIC V1·C18]; [Tệp S8 R57–R58] |
| A-16 | BĐM 3 tầng: ai lập, ai ký | ĐP VTBB, ĐP NL/BTP (QLSX ký), QLDL ghép BĐM TP | Như MIC, thêm bản thuế | Tệp bổ sung, không mâu thuẫn | [MIC V2·C5, V11·C4, V7·C1]; [Tệp S7] |
| A-17 | Đối chiếu công nợ hạn ngày 20; hóa đơn sau ngày LSX | Như tệp | Như MIC | Khớp | [MIC]; [Tệp S6 R22, R26] |
| A-18 | Thử mẫu 10–14 ngày; phối tối đa 2 lần | Như tệp | Như MIC | Khớp | [MIC]; [Tệp S1 R27; S8 R63] |
| A-19 | Dòng hóa đơn theo công ty sở hữu pháp lý | Có, kèm ví dụ IDA / BamBoo | Có, theo 3 luồng sở hữu, sản xuất, mua bán | Khớp, tệp chi tiết hơn | [MIC]; [Tệp S5 R19–R22] |
| A-20 | Ai chịu trách nhiệm số công nợ | CV phụ trách, TN QLDL kiểm | QLDL làm, QLSX ký | Tệp bổ sung, không mâu thuẫn | [MIC V3·C19]; [Tệp S6 R26] |
| A-21 | Khảo sát giá vốn cho KD | Giá vốn chịu trách nhiệm; chỉ so sánh; không có hạn | Có các bước, QLSX duyệt bảng cấu thành | Tệp bổ sung, không mâu thuẫn | [MIC V4·C2, V6·C20]; [Tệp S3 R24–R28] |
| A-22 | Hủy đơn | (không có) | Có quy trình B | Tệp bổ sung | [Tệp S4 R34–R41] |
| A-23 | Pháp lý SX, BĐM thuế, mua tại NCC, dự chi, bán nội bộ | (không có) | Có quy trình | Tệp bổ sung | [Tệp S5; S7; S6 R24, R29–R30, R37–R38] |
| A-24 | Số liệu từng NCC (MOQ, hao hụt, thời gian SX, vướng chứng từ) | Có cho 13 nhà | Sheet trống | Theo MIC (tệp thiếu) | [MIC]; [Tệp S17] |
| A-25 | Bộ máy, người phụ trách từng NCC | Đầy đủ | Không có sheet | Theo MIC (tệp thiếu) | [MIC V1·C14–C19]; [Tệp ML R23] |
| A-26 | Khung trách nhiệm 3 tầng | Có | (không có) | Theo MIC | [MIC V6·C16] |
| A-27 | Hương vắng trên 3 ngày | QLSX làm thay | (không có) | Theo MIC | [MIC V2·C20] |
| A-28 | Theo dõi tiến độ | Lần 1 sau 2 ngày, lần 2 trước ngày có hàng 2 ngày; nhịp tùy đơn | Sau 2 ngày làm việc; báo cáo hằng ngày | Tệp bổ sung, không mâu thuẫn | [MIC, V8·C1]; [Tệp S4 R27] |

---

## 10. Câu cần hỏi lại

### 10.1. Không cần hỏi nữa: chỉ cần sửa tệp cho khớp MIC (8 câu cũ)

Phòng đã trả lời qua MIC. Việc còn lại là người giữ tệp sửa dòng tương ứng.

| Câu cũ | Sửa dòng nào | Sửa thành | Nguồn |
|---|---|---|---|
| 4 | S3 R35 | Bắt đầu khi hàng về kho Dr Xanh; TN QLDL ký | [MIC V4·C15, V3·C7, V4·C3] |
| 5 | S11, S12: thêm cột Người duyệt ở bước 4, 7 | TN QLDL; vướng thì QLSX | [MIC V2·C15, V4·C1] |
| 6 | S11 R22–R53 | ĐP TP chỉ xử lý nhanh khi không ảnh hưởng giá, công nợ; còn lại CV XLSC làm | [MIC V2·C14, V9·C8, C9] |
| 7 | S14 cột Nơi duyệt | QLSX (hiện tại); ghi chú *chuyển TNĐP khi có người* | [MIC V11·C4, V4·C6] |
| 17 | S11, S12 | Gộp một quy trình, hai nhánh | [MIC V9·C7] |
| 18 | S19 R40 | Theo quý hoặc khi QLSX yêu cầu; QLDL tổng hợp và lưu | [MIC V9·C13, V11·C1, V12·C1] |
| 19 | S1 R47–R48 | CV QLDL lập → TN QLDL kiểm duyệt → Pháp lý chung → Kế toán → ĐDPL ký | [MIC V5·C2] |
| 20 | S3 R32, TĐ R40 | Bỏ bước cảnh báo biên; KD tự kiểm biên | [MIC V3·C2] |

Kèm theo: sửa S4 R32 (*2 ngày* thành ngoại dạng 1–2 ngày, hàm lượng 14 ngày) [MIC V3·C6]; S1 R49 (Mẫu 05 giao Giá vốn) [MIC V4·C4]; S8 R62 (khảo sát nhận từ Giá vốn) [MIC V11·C3]; S9 R35 (cọc nhãn 6 đối tác) [MIC]; S10 (hạn mức, hoàn ứng Grab) [MIC]; S17 (chép số liệu NCC từ mục 4.2).

### 10.2. Còn phải hỏi phòng (16 câu)

Mỗi câu trỏ thẳng dòng tệp để phòng khỏi phải tìm lại. Xếp theo mức cần cho ERP và bàn giao.

| # | Câu cũ | Chỗ tệp | Câu hỏi |
|---|---|---|---|
| H-01 | 1 | S2 R1 *Xem lại quy tắc đặt mã đơn đặt hàng, mã đơn xử lý lại, mã đơn sự cố, mã các BĐM* | Mã đơn TP, đơn BTP, đơn xử lý lại, mã sự cố và mã BĐM (BTP, VTBB, TP) hiện đặt theo quy tắc nào? Xin mỗi loại 2 mã thật |
| H-02 | 2 | S4 nhắc *Chưa lấy hóa đơn* (R29), *Đã nhận hàng* (R31), *TEST KHÔNG ĐẠT* (R32), *Chờ thông tin từ KD* (R40), hủy, hoàn thành | Cột trạng thái trên sheet ĐIỀU PHỐI có đúng những giá trị nào, theo thứ tự nào? |
| H-03 | 3 | S4 R32; MIC: hoàn thành cần kết quả Lab [V8·C7]; ngoại dạng 1–2 ngày, hàm lượng 14 ngày [V3·C6] | Đơn TP chốt hoàn thành sau kết quả **ngoại dạng** hay phải chờ **hàm lượng**? Nếu chờ, trong 14 ngày hàng có được giao KD không? |
| H-04 | 25 | Không có trong tệp; MIC: có cho nợ hồ sơ, không có văn bản [V3·C4, V10·C11] | Trong 7 điều kiện, điều kiện nào từng được cho nợ, nợ tối đa bao lâu, ai theo dõi đến khi đủ? |
| H-05 | 8 | TĐ R192–R200 *Xem lại và chốt Data 1*; R129–R133 *Chưa bắt đầu* | Data 1 đã chốt chưa, ai chốt, dự kiến ngày nào? |
| H-06 | 9 | S8 R29 *chưa có danh sách ai chuẩn bị NL/BTP*; S18 cột bên chuẩn bị trống | Có bảng nào ghi theo từng sản phẩm và NCC GC: ai chuẩn bị NL, BTP, VTBB không? Nếu chưa, ai lập, xong trước ngày nào? |
| H-07 | 10 | S9 R53 *thuế cho phần hao hụt chưa hoàn thiện*; S9 R82 *Bảng tỷ lệ hao hụt theo NCC* | Bảng tỷ lệ hao hụt cho phép từng NCC nằm ở tệp nào? Kế toán đã đồng ý dùng cho phần thuế chưa? |
| H-08 | 11 | ML R14 *13. Ngưng hợp tác với NCC*, không có sheet | Khi ngưng một NCC GC phải làm những việc gì, theo thứ tự nào (thu hồi VTBB, NL, khuôn; hoàn cọc; đối chiếu cuối; thanh lý hợp đồng; nhãn tồn)? Ai quyết ngưng? Lần gần nhất (ví dụ Basel) làm thế nào? |
| H-09 | 13 | S5 R2 *còn duyệt pháp lý đơn BTP, ..., mua / khảo sát NL/BTP?* (đơn xử lý lại đã có trả lời [V3·C5]) | Pháp lý SX có duyệt cho đơn BTP và cho việc mua NL/BTP không? Nếu có, kiểm mục nào trong 5 mục S5 R18–R22? |
| H-10 | 14 | S5 R27 Pháp lý SX *định kỳ* kiểm hạn; S6 R32 Pháp lý chung theo dõi, QLDL bổ sung trước 3 tháng | Ai phát cảnh báo giấy tờ sắp hết hạn: Pháp lý SX hay Pháp lý chung? Bao lâu rà một lần? |
| H-11 | 12 | ML R24 *Chưa có*; S14 R37–R38 Biên bản giao nhận, Biên bản hàng lỗi chỉ có tên | Biên bản giao nhận và biên bản hàng lỗi do ai lập, ai ký, ký nhân danh công ty nào? (Bảng nháp ở mục 5.15 nhờ phòng soát luôn) |
| H-12 | 22 | S9 R35 ghi 4 NCC; MIC: 6 đối tác, có Basel | Hiện đang để cọc nhãn ở 6 nhà nào, số tiền từng nhà, nhà nào đã có văn bản xác nhận? |
| H-13 | 23 | S17 R4–R18 trống 17 cột; MST Thành Phát và PES trùng (R17, R18); Đại Tâm, Thành Phát chưa có ĐP TP, ATC, Dubai chưa có QLDL | MST đúng của PES là gì? Thành Phát còn hợp tác không? Ai phụ trách Đại Tâm (ĐP TP), ATC và Dubai (QLDL)? Phí lưu kho từng nhà ghi ở đâu? |
| H-14 | 15 | S8 R48 *Nhập kho từ đổ thu / dư sản xuất*: chưa có người làm | Hàng dư, đổ thu sau sản xuất hiện ai ghi nhận, dùng phiếu gì, nhập kho nào? |
| H-15 | 16 | S9 R112: *(1) mâu thuẫn ở Mục VIII về nghiệp vụ thuế; (2) ghi chú dở II.3 và VII.1.2; (4) thời lượng* (điểm 3 đã có trả lời [V1·C4]) | Ba điểm còn lại ở S9 R112 đã chốt chưa? *Mục VIII* là mục nào trong bản hiện tại? |
| H-16 | 21 | S2 R20 Thu mua khai BTPR; TĐ R74 Oanh khai | Mã BTP ruột do Thu mua hay ĐP NL/BTP khai? |

### 10.3. Không hỏi phòng: người chủ cần quyết

| # | Việc | Vì sao | Nguồn |
|---|---|---|---|
| Q-01 (câu cũ 24) | Đặt hạn mặc định cho 7 bộ phận xác nhận đơn, cho Thiết kế làm mockup, cho Kế toán hạch toán | Phòng xác nhận *chưa có hạn là đúng hiện trạng*; ERP cần một con số để nhắc việc | [MIC V4·C9, V10·C8, C9] |
| Q-02 | Có chuẩn bị phương án bàn giao *không kịp app* không | Phạm vi bàn giao phụ thuộc app; còn 8 tuần | [MIC V1·C10] |
| Q-03 | Tuyển Trưởng nhóm Điều phối, và giao ai sửa 8 chỗ ở mục 10.1, trước ngày nào | Ghế TNĐP trống làm dồn việc lên QLSX; vai ký phiếu phụ thuộc ghế này | [MIC V6·C14] |
| Q-04 | Xem riêng với Kế toán trưởng các khoản ngoài hợp đồng (chiết khấu, hoa hồng, VTBB ngoài cấu thành thuế, phí thuê tên) | Rủi ro pháp lý, thuế; quyết có đưa lên ERP không, ai được xem | [MIC V6·C19]; mục 7 |
