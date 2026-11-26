# 12. KHO — PHÂN HỆ SẢN XUẤT GIA CÔNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 26/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | — |

## Phần này là gì

Tài liệu này mô tả **chức năng Kho** mà phòng Sản xuất DEGO Holding đang làm bằng Google Sheets, để làm căn cứ dựng phần Kho của phân hệ Sản xuất gia công trên ERP. DEGO không tự sản xuất: nguyên liệu (NL), bán thành phẩm (BTP) và vật tư bao bì (VTBB) được mua về rồi **gửi tại kho của nhà cung cấp gia công (NCC GC)**; NCC GC đóng thành phẩm (TP); DEGO nhận TP về kho và xuất bán. Vì vậy kho của phòng Sản xuất chủ yếu là **kho đặt tại bên thứ ba**, số liệu phải ghi theo chứng từ của mình và đối chiếu định kỳ với số NCC GC báo.

Nguồn rút tính năng: tệp *4. XUẤT NHẬP TỒN - VTBB* (37 sheet), tệp *3. XUẤT NHẬP TỒN NL, BTP* (36 sheet), thư mục *Drive QLDL (mới)* (tệp 1, 2, 5, 7), thư mục *Drive QL Giá vốn* (phần giá nhập kho và tồn có giá), tệp *BC VTBB* và hai quy trình QT8 (quản lý NL / BTP), QT9 (quản lý VTBB) trong tệp *QUY TRÌNH SẢN XUẤT*. **Dữ liệu trong các tệp là mô phỏng**; tài liệu chỉ rút quy tắc, cột, công thức và biểu mẫu, không coi số dòng là dữ liệu thật. Phần đối chiếu ERP lấy từ mã nhánh `erp-v2` (module `inventory`, `goods_receipt`, `catalog`, `purchase_order`) và bộ tài liệu `doc/erp/kho/`.

Viết tắt: NL = nguyên liệu; BTP = bán thành phẩm (ruột); VTBB = vật tư bao bì; TP = thành phẩm; NCC GC = nhà cung cấp gia công; ĐP = điều phối; QLDL = quản lý dữ liệu; QLSX = quản lý sản xuất; KD = kinh doanh; P TCKT = phòng Tài chính kế toán; BĐM = bảng định mức; LSX = lệnh sản xuất; ĐMH = đơn mua hàng; YCMH = yêu cầu mua hàng; NSX = ngày sản xuất; HSD = hạn sử dụng; NB = sổ nội bộ; XLSC = xử lý sự cố.

---

## 1. Mục đích và người dùng

### 1.1. Mục đích

1. Biết **tại từng kho, của từng thương hiệu, từng mã hàng đang có bao nhiêu**, trong đó bao nhiêu dùng được ngay, bao nhiêu đang giữ cho đơn chưa sản xuất, bao nhiêu là hàng lỗi.
2. Trả lời nhanh câu hỏi của điều phối thành phẩm khi có đơn: **đủ VTBB chưa, đủ NL / BTP chưa**, thiếu thì chuyển kho, mua hay phối.
3. Ghi đủ mọi lần hàng vào, hàng ra tại kho NCC GC, kèm chứng từ (phiếu có chữ ký hai bên, ảnh), để **đối chiếu tồn với NCC GC** hằng tháng hoặc theo đơn và quyết toán hao hụt.
4. Kiểm soát **hao hụt, hư hỏng, tồn lâu, phí lưu kho**; cảnh báo dưới mức tồn an toàn và đề xuất số lượng đặt theo MOQ.
5. Cung cấp **giá trị tồn** và số liệu nhập xuất cho giá vốn, công nợ và kế toán (hai sổ: nội bộ và thuế).

### 1.2. Người dùng và vai trò

| Vai trò | Làm gì ở phần Kho | Sổ / sheet đang dùng |
|---|---|---|
| Điều phối VTBB (ĐP VTBB) | Chủ sổ kho VTBB: nhập, xuất cho sản xuất theo đơn, xuất ngoài sản xuất, chuyển kho; khai Min / MOQ; duyệt *đủ VTBB* cho đơn; đối chiếu tồn VTBB với NCC GC; lập phiếu đề nghị nhập / xuất / chuyển / đưa vào chi phí | Tệp 4: NHẬP KHO VTBB, XUẤT KHO VTBB SX, XUẤT KHO VTBB NGOÀI SX, TỒN KHO, THÔNG TIN, DỮ LIỆU NCC, ĐỐI CHIẾU NCC, phiếu 1 đến 9; tệp BC VTBB |
| Điều phối NL / BTP (ĐP NL/BTP) | Chủ sổ kho NL, BTP: nhập (mua, sau phối), xuất NL đi phối, xuất BTP theo đơn TP, chuyển kho; theo dõi lô, NSX, HSD, kết quả Lab; duyệt *đủ NL / BTP* cho đơn; đối chiếu tồn BTP | Tệp 3: Nhập kho NLBTP, 6. Xuất kho ngoài sản xuất, 6.1 Xuất kho theo ĐH thành phẩm, 4. DS PHỐI BTP, 4.1 LSX BTP, 8 / 8.1, 9 / 9.1, 10.x |
| Điều phối thành phẩm (ĐP TP) | Lên đơn TP; ghi số TP có sẵn tại kho NCC GC theo từng lần; ghi nhập, chuyển, trả, xuất xử lý TP; lập phiếu nhập kho TP, phiếu xuất bán | Sổ ĐIỀU PHỐI, NHẬP-XUẤT TP, BC tồn kho tại NCC GC |
| Quản lý dữ liệu (QLDL) | Nhận số từ các điều phối và từ NCC GC; đối chiếu tồn bốn nhóm (VTBB, BTP, TP, hàng lỗi); ghi phí lưu kho, hao hụt; gửi bộ chứng từ cho P TCKT; làm việc với NCC GC | Drive QLDL: tệp 1, 2, 5, 7 |
| Quản lý sản xuất (QLSX) | Duyệt phiếu, duyệt phương án thiếu hàng, ký biên bản đối chiếu (theo giấy ủy quyền), duyệt chính sách lưu kho | Chữ ký trên phiếu, cột duyệt |
| Kho (thủ kho NCC GC, kho Dr.Xanh, kho DEGO Cần Thơ) | Thực nhận, thực xuất; ký phiếu, chụp ảnh lô hàng; KCS thành phẩm khi nhận về | Phiếu giấy, ảnh, sổ KCS |
| Thu mua | Mua NL, BTP, VTBB; báo ngày hàng về, kho nhận, số hóa đơn, giá | Sổ *Thu mua trả kết quả* (đã có trên ERP) |
| Kinh doanh (KD) | Xem tồn theo thương hiệu; chốt điều chuyển, mua dự trù, bán giữa thương hiệu; duyệt phiếu có liên quan chi phí của thương hiệu | 9 / 9.1 Tồn kho Kinh doanh; báo cáo tồn |
| Kế toán (P TCKT), kế toán giá vốn | Nhận phiếu trong ngày để hạch toán trên Misa nội bộ và Misa thuế; xác nhận đủ tồn thuế; dùng giá trị tồn và giá nhập kho | Phiếu in; sổ giá nhập kho; sổ tồn có giá |
| Lab | Test ngoại dạng, hàm lượng trước khi cho nhập thực tế; giám định hàng lỗi | Cột LAB TEST, phiếu yêu cầu test |
| Xử lý sự cố (XLSC) | Ghi chuyển hàng lỗi giữa các kho và trạng thái | LỊCH SỬ TỪ SỰ CỐ, YÊU CẦU XỬ LÝ LẠI |

---

## 2. Khái niệm và quy tắc kho của phòng Sản xuất

### 2.1. Các loại kho

Danh mục kho nằm ở sheet *DATA 1* (cột *Tên kho viết tắt*, *Mã kho*, *Thông tin nhận*, *Địa chỉ kho*, *Định nghĩa*; mã kho ghi chú *Lấy từ Misa*).

| Loại kho | Ví dụ trong danh mục | Ý nghĩa |
|---|---|---|
| Kho của DEGO tại Cần Thơ, chia theo loại hàng | `BTP_DEGO` (KHO BTP_DEGO CT), `TP_DEGO`, `VTBB_DEGO`, `NL_DEGO` | Kho BTP, TP, VTBB, NL của nhà máy DEGO Cần Thơ |
| Kho lỗi của DEGO | `XL_DEGO` (KHO NCCXL_DEGO CT) | Kho hàng lỗi của nhà máy DEGO Cần Thơ |
| Kho thành phẩm thương mại | `MEKONG` (KHO CHINH _ MK), `XL_MEKONG` | Kho chính Dr.Xanh (thành phẩm) và kho Dr.Xanh thu hàng lỗi, hỏng từ khách về |
| Kho tại NCC GC | `An Nông` (KHO NCC_ANNONG), `Hà Long`, `Yamato`, `Basel`, `Đại Tâm`, `Âu Việt`, `ATC`, `Dubai`, `Thái Nông`, `Niềm Tin Việt`, `Adu`, `Thu Loan`, `Agri Future` | Hàng của DEGO gửi tại kho NCC GC; mỗi NCC một kho |
| Kho lỗi tại NCC GC | `XL_An Nông` (KHO NCCXL_ ANNONG), `XL_Hà Long`, `XL_Basel`, `XL_Niềm Tin Việt`... | Kho chứa hàng lỗi tại từng NCC GC; một số kho mới khai tên, ghi *Bổ sung kho sau* |
| Kho sản xuất VTBB | `KHO SX_VTBB` | Kho sản xuất vật tư bao bì (chưa có định nghĩa) |
| Kho ảo trong luồng sự cố | `(Phát sinh)`, `(Tiêu hủy)`, `(Xuất chi phí)`, `<NCC>_lỗi`, `<NCC>_Sử dụng` | Dùng ở sổ chuyển hàng lỗi để thể hiện điểm đầu, điểm cuối |

Quy tắc đặt mã kho rút ra: `KHO NCC_<TÊN NCC>` cho kho thường tại NCC GC; `KHO NCCXL_<TÊN NCC>` cho kho lỗi cùng NCC; kho DEGO theo mẫu `KHO <LOẠI HÀNG>_DEGO CT`. Tên viết tắt thêm tiền tố `XL_` cho kho lỗi. Danh mục hiện có tên kho trùng nghĩa (ví dụ *Agri Future* và *kho nhà cung cấp AGRIFUTURE* cùng một mã kho), sổ tồn phải có cột *Kho đã chuẩn hóa* để gộp.

Chính sách kho theo NCC GC (cùng sheet *DATA 1*): có hay không **phí lưu kho**, chi tiết phí và đơn vị tính phí (ví dụ theo pallet / m² mỗi tháng, hoặc theo thùng mỗi ngày), **% hao hụt cho phép** (ví dụ *theo thực tế*, 0, ±3%, 3%), số ngày sản xuất.

### 2.2. Khóa của tồn kho

Mọi sổ tồn khớp dữ liệu theo **ba trường: Kho + Thương hiệu + Mã hàng**. Tên hàng và đơn vị tính chỉ để hiển thị, không dùng để khớp (hướng dẫn ghi rõ lý do: tránh lỗi gõ khác nhau giữa các sheet).

- **Thương hiệu** là chủ hàng nội bộ: IDA, ABA, DEGO, DR XANH, BAMBOO, N2SBIO, LAB, và giá trị **Dùng chung** (NL chưa gắn cho thương hiệu nào). Cùng một mã ở cùng một kho có thể thuộc nhiều thương hiệu, mỗi thương hiệu một dòng tồn.
- Với NL / BTP, sổ chi tiết còn theo **lô**: số lô, ngày sản xuất, hạn sử dụng, số CAS, kết quả Lab, trạng thái *Sử dụng được / Không sử dụng được*.
- Với BTP, tên hàng đi kèm **dòng V** (V1, V2... — dòng công thức; có dòng V sản xuất và dòng V kinh doanh) và **màu**.

### 2.3. Loại tồn

| Loại tồn | Định nghĩa theo nguồn | Dùng để |
|---|---|---|
| Tồn thực tế | Nhập thực tế trừ xuất thực tế; hàng đã phát sinh và đã trừ thật | Số chính để đối chiếu với NCC GC |
| Tồn tạm | Lượng nhập tạm, xuất tạm: đã phát sinh nhưng chưa nhập / xuất thật vì chưa kiểm duyệt hoặc chưa chốt số cho đơn | Biết phần đang treo |
| Tồn lỗi | Hàng nhập lỗi / hư hỏng trừ hàng đã xuất xử lý lỗi | Theo dõi kho lỗi |
| Tồn có thể sản xuất | Phần còn dùng được cho đơn mới, sau khi trừ lượng đã giữ cho đơn chưa sản xuất | Trả lời *đủ hay thiếu* cho đơn |
| Tồn trừ đơn chưa sản xuất | Tồn sau khi trừ *xuất tạm* và *đơn chờ xuất* (sheet *TỒN KHO MẪU 9.10*: Còn thiếu = Tồn − Xuất tạm − Đơn chờ xuất) | Cân đối hàng khi chưa đủ cho đơn |
| Tồn SX và tồn KD | Hai sổ tồn BTP cùng cấu trúc: một sổ trừ theo **quy cách thực tế sản xuất**, một sổ trừ theo **quy cách kinh doanh nắm** (ví dụ chai 450 ml đóng tối ưu 435 ml) | SX biết lượng ruột thật; KD biết lượng theo quy cách đã cam kết |
| Tồn nội bộ và tồn thuế | Sổ trên Drive là **dữ liệu nội bộ**, *chưa bao gồm dữ liệu thuế*. Tồn thuế nằm ở Misa Thuế theo từng pháp nhân | Kiểm đủ cả hai phía trước khi duyệt đơn, chuyển kho, xuất bán |

Lưu ý: ba nguồn định nghĩa **tồn có thể sản xuất** chưa trùng nhau (xem câu hỏi 3 ở mục 9).

### 2.4. Loại giao dịch

Danh mục phân loại giao dịch dùng chung cho VTBB và NL / BTP (sheet *DATA 1*, có cột diễn giải). Mỗi loại thuộc một **chiều** (nhập hay xuất) và một **nhóm tồn** (thực tế, tạm, lỗi).

**Nhập**

| Phân loại | Diễn giải của phòng Sản xuất | Nhóm tồn |
|---|---|---|
| Nhập mua | Mua NL / BTP, VTBB **đã kiểm duyệt** đúng chất lượng | Thực tế |
| Nhập sau phối | BTP có được sau khi đem NL đi phối (chỉ NL / BTP) | Thực tế |
| Nhập chuyển kho | Chuyển từ NCC GC này sang NCC GC khác | Thực tế (không tính vào giá trị nhập) |
| Nhập cho / tặng | Nhận hàng cho tặng từ NCC khác | Thực tế |
| Nhập đổ thu / dư sau sản xuất | Hàng lấy lại sau khi đã xuất sản xuất, hoặc đổ thu | Thực tế |
| Nhập khác | Phát sinh không thuộc các loại còn lại | Thực tế |
| Nhập tạm | Mua về **chưa kiểm duyệt**, nhập tạm đợi xử lý | Tạm |
| Nhập lỗi / hư hỏng | Hàng phát hiện lỗi, hư hỏng | Lỗi |
| Nhập đầu kỳ | Chuyển hàng dùng được từ cuối kỳ trước sang đầu kỳ mới | Thực tế (số dư đầu) |
| Nhập đầu kỳ lỗi | Chuyển hàng không dùng được sang đầu kỳ mới | Lỗi (số dư đầu) |

**Xuất ngoài sản xuất**

| Phân loại | Diễn giải | Nhóm tồn |
|---|---|---|
| Xuất chuyển kho | Chuyển từ NCC GC này sang NCC GC khác | Thực tế (không tính vào giá trị xuất) |
| Xuất cho / tặng | Xuất hàng cho tặng NCC khác | Thực tế |
| Xuất mẫu thử | Đem NL / BTP, VTBB đi test hoặc làm mẫu | Thực tế |
| Xuất tạm | Xuất hàng chưa kiểm duyệt, đợi xử lý | Tạm |
| Xuất xử lý hàng lỗi / hư hỏng | Xuất sau khi phát hiện hàng lỗi, hư hỏng | Lỗi |
| Xuất hao hụt / đổ bỏ | Hao hụt phát hiện khi đối chiếu cuối tháng, **trong mức hao hụt đã thỏa thuận**; đổ bỏ do sự cố đã tìm được nguyên nhân | Thực tế, đánh dấu là hao hụt |
| Xuất khác | Phát sinh không thuộc các loại còn lại | Thực tế |
| Xuất NL phối BTP | Đem NL đi phối BTP tại NCC GC (chỉ NL / BTP) | Thực tế |
| Xuất bán | Xuất bán giữa các thương hiệu, công ty thuế; xuất bán cho NCC GC khi NCC làm lỗi hoặc làm mất hàng | Thực tế |

**Xuất theo đơn hàng thành phẩm** (trạng thái của dòng xuất theo đơn)

| Phân loại | Diễn giải |
|---|---|
| Xuất SX tạm | Xuất cho sản xuất nhưng **chưa chốt số lượng chính xác** cho đơn |
| Xuất sản xuất | Đã xuất cho đơn hàng |
| Xuất hoàn thành | Đơn hoàn thành: chuyển trạng thái từ xuất sản xuất hoặc xuất tạm sang hoàn thành |
| Hủy đơn | KD báo hủy đơn; số lượng đơn đổi về 0 |
| Chưa đủ BTP | Chưa đủ BTP để đóng đơn (chỉ NL / BTP) |
| BTP NCC - không tồn kho | BTP của NCC GC, mua theo đơn, không qua tồn kho của DEGO |
| Đơn hàng đã trừ thực tế | BTP đã được trừ theo lượng thực tế |
| BTP NCC đã dự trù mua | BTP dự trù hoặc mua từ NCC GC |

**Thành phẩm** (sổ NHẬP-XUẤT TP): 1. Nhập TP, 2. Nhập mẫu, 3. Nhập dư, 4. Chuyển kho, 5. Trả hàng, 6. Xuất xử lý, 7. Nhập sau xử lý.

**Giao dịch chứng từ đi kèm** (không phải loại tồn riêng, nhưng phát sinh phiếu): xuất bán nội bộ, yêu cầu xuất hóa đơn, đưa vào chi phí, xuất hủy, chuyển kho nội bộ.

### 2.5. Quy tắc mã hàng, mã phiếu

| Đối tượng | Quy tắc rút từ nguồn | Ví dụ |
|---|---|---|
| Mã VTBB | Ba ký tự đầu cho biết loại: CPT / CHT / CET... chai, lọ; NAP nắp; THC / THI / THA thùng; HOP hộp; NHG / NTN / NDT / TEM nhãn, tem; BAO / TUI túi; VT0 khác | CPT0009, NAP0156, THC0072, NHG4995 |
| Mã NL | NLT + số (nguyên liệu), NA + số (phụ gia) | NLT0004, NA0001 |
| Mã BTP | BTPR = BTP ruột do DEGO chuẩn bị; BTPM = BTP mua của NCC GC | BTPR0124, BTPM0047 |
| Mã thành phẩm | HH + số | HH4995 |
| Mã BĐM VTBB | `VT_<Mã HH>_<số thứ tự 2 chữ số>` | VT_HH4995_01 |
| Mã BĐM BTP | `<tên rút gọn>_<mã màu>_<dòng V>_<số thứ tự>`; mã màu hai chữ (ĐO, TR, HO, CA, VA, TI, XD, XL, ĐE) | CT3.6_XL_V2_02 |
| Mã lệnh phối BTP | `BTP<số>/<năm>` hoặc `BTP<số>/<năm>/<thương hiệu>-<NCC>` | BTP09/2026; BTP132/2026/IDA-HL |
| Mã đơn TP | Tiền tố thương hiệu + TP + ngày ddmmyy + số thứ tự | ATP25062603, ITP02062602 |
| Số phiếu đề nghị | `<số thứ tự>/<ddmm>` | 01/0605 |
| Mã sự cố, mã yêu cầu xử lý lại | ISC. + ngày + số; IYC. + ngày + số | ISC.0201261, IYC.0801261 |
| Mã nối phiếu mua | Số nguyên do người nhập gán, dùng để gom các dòng nhập kho lên một phiếu in | 1 |

Mã vật tư của NCC GC khác mã DEGO (ví dụ NCC dùng TUIDA00159 cho nhãn mà DEGO gọi NTN3458; BTIDA00015 cho BTP DEGO gọi BTPR0030), nên có **bảng ánh xạ mã DEGO, mã NCC theo từng NCC GC** (hiện mới đủ cho Hà Long).

### 2.6. Thời điểm ghi nhận và các mốc bắt buộc

1. **Xuất nội bộ cho sản xuất được ghi nhận khi NCC GC có thành phẩm** (ghi chú đầu sheet *XUẤT KHO VTBB SX*). Trước thời điểm đó, lượng cần cho đơn nằm ở trạng thái *xuất SX tạm*.
2. Phiếu xuất BTP / VTBB phải **lập trước hoặc cùng ngày lệnh sản xuất**.
3. Phía thuế: nếu có bán VTBB cho NCC GC thì xuất bán **ngay khi duyệt đơn**; ngày có hàng QLDL so số đã xuất với số thực sản xuất (thiếu thì xuất bổ sung, dư thì để đơn sau hoặc NCC xuất trả).
4. Nhập mua chỉ ghi **nhập thực tế** khi hàng đã kiểm duyệt; chưa có kết quả thì ghi **nhập tạm**. Thời gian test: ngoại dạng 1 đến 2 ngày, hàm lượng 14 ngày; mỗi lần lấy 2 đến 4 mẫu và lưu mẫu đối chiếu.
5. Ngày sản xuất in trên bao bì NL phải **trước hoặc bằng ngày nhận hóa đơn NL**.
6. Chuyển kho: báo NCC **trước 1 ngày**; **trong ngày** phải nhận bản chụp phiếu có chữ ký hai bên và gửi P TCKT.
7. Đối chiếu tồn với NCC GC: **hằng tháng** hoặc theo đơn; cuối tháng có thể lưu ảnh sổ tồn để đối chiếu về sau. Dự trù NL / BTP định kỳ ngày 15.
8. HSD thành phẩm = NSX + 2 năm; HSD còn lại = HSD − ngày giao dịch.
9. NSX của BTP: nếu NCC cung cấp thì lấy theo NCC; nếu không thì lấy theo NSX của NL và yêu cầu NCC đóng theo ngày đó.

### 2.7. Dung sai kỹ thuật ảnh hưởng tới số kho

- **Sai số phối chế** (hàm lượng hoạt chất so với đăng ký): đến 2,5% khối lượng thì ±15% (dạng lỏng) hoặc ±25% (dạng rắn); trên 2,5 đến 10% thì ±10%; trên 10 đến 25% thì ±6%; trên 25 đến 50% thì ±5%; trên 50% thì ±2,5%. BTP phối xong nằm trong sai số thì chuyển *có BTP*; vượt thì báo QLSX.
- **Sai số chiết rót và đóng tối ưu thể tích**: mỗi mức thể tích có khung sai số cho phép và thể tích chốt đóng (ví dụ nhãn 450 ml chốt đóng 440 ml; một số sản phẩm chốt 97,5% thể tích chai). Phần chênh giữa quy cách thực đóng và quy cách KD nắm đang được đưa vào chi phí KD. Đây là lý do có hai sổ tồn SX và KD.
- **Số lượng gửi NCC lớn hơn số KD đặt** vì cộng mẫu Lab (ví dụ đặt 200 thì gửi 202; phía BTP cộng 1 đơn vị). Phần dư này là mẫu, không phải hao hụt.

---

## 3. Quy trình hiện tại

### 3.1. Nhập kho VTBB

| | |
|---|---|
| Ai làm | Thu mua báo ngày hàng về; kho NCC GC nhận và ký; ĐP VTBB ghi sổ; QLDL nhận dữ liệu giá |
| Sheet / phiếu | *NHẬP KHO VTBB*; *DATA THU MUA TRẢ KQ* (nguồn tra); *5. Phiếu đề nghị nhập*; *1. Phiếu đề nghị mua hàng hóa dịch vụ* |
| Đầu vào | Ngày nhập, phân loại nhập, kho, thương hiệu, mã VTBB, lượng nhập, mã ĐMH (mã đơn Misa), mã đơn KD nếu có |
| Đầu ra | Dòng nhập trong sổ giao dịch; tồn tăng theo nhóm tồn của phân loại; giá nhập cho giá vốn |

Các bước:

1. Thu mua mua hàng theo đề nghị, báo kho NCC GC nhận, ngày hàng về (trong ngày hoặc trước 1 ngày).
2. Kho nhận hàng, gửi chứng từ có chữ ký hai bên và ảnh lô hàng.
3. ĐP VTBB ghi một dòng nhập: chọn phân loại, kho, thương hiệu; gõ mã hoặc chọn tên VTBB (tên và ĐVT tự hiện); nhập lượng; **nhập mã ĐMH**.
4. Từ mã ĐMH, sổ tự tra từ kết quả mua của Thu mua: đơn vị nhận hóa đơn, số hóa đơn, tên trên hóa đơn, tên NCC, ngày thu mua. **Giá đã gồm VAT và vận chuyển** được tra theo bốn điều kiện cùng lúc: ngày nhận thực tế, mã VTBB, số lượng đã nhận, mã ĐMH; không khớp thì hiện *Không tìm thấy*.
5. Đính ảnh phiếu nhập kho của NCC GC.
6. Nếu là nhập chuyển kho: ghi tài xế, số xe, đơn vị làm việc với NCC, ghi chú trên phiếu gửi NCC.
7. Gán *mã nối* để gom các dòng lên một phiếu đề nghị in.

Trường hợp đặc biệt theo QT9: mua VTBB ngay tại NCC GC đang sản xuất khi thiếu (trình KD loại và giá, khai mã, lập phiếu mua và BĐM thay đổi gửi QLDL); nhập từ dư sản xuất phía thuế (QLDL yêu cầu NCC xuất bán lại, lập phiếu nhập kèm LSX).

### 3.2. Nhập kho NL / BTP

| | |
|---|---|
| Ai làm | Thu mua hoặc QLDL (bên mua); kho NCC GC; Lab; ĐP NL/BTP ghi sổ |
| Sheet / phiếu | *Nhập kho NLBTP*; *5.2 Điều phối ĐH NLBTP*; phiếu đề nghị nhập kho BTP; phiếu yêu cầu test của Lab |
| Đầu vào | Số phiếu yêu cầu, ngày nhập, phân loại, kho, thương hiệu, mã NL / BTP, lượng, giá, số lô, NSX, HSD, số CAS, kết quả Lab, hàm lượng thực tế, đơn vị nhận hóa đơn, mã số yêu cầu |
| Đầu ra | Dòng nhập theo lô; tồn thực tế hoặc tồn tạm; thành tiền = lượng × giá |

Các bước:

1. Thu mua báo ngày hàng về; kho gửi chứng từ ký hai bên, ảnh lô hàng, nhãn, **biên bản cân tổng khối lượng**.
2. Lấy mẫu gửi Lab (ngoại dạng, hàm lượng; tiêu chí gồm mã CAS). Chưa có kết quả thì ghi *Nhập tạm*; đạt thì chuyển *Nhập mua*; không đạt thì sang *Nhập lỗi / hư hỏng* và mở sự cố hoặc đổi trả.
3. Ghi dòng nhập: mã kho tự tra từ tên kho; tên hàng, dòng V, màu tự tra từ mã; nhập lượng, giá (cột giá ghi chú *Giá vốn sản xuất*), số lô, NSX, HSD, số CAS.
4. Đơn mua giao nhiều lần: sổ điều phối đơn NL / BTP ghi tới 3 lần nhập (ngày, số lượng), tổng đã nhập, HSD còn lại (ngày).
5. Mua qua QLDL có hai kiểu: mua từ NCC GC này chuyển sang NCC khác, Lab hoặc kho khác (QLDL lập đề nghị chuyển kho); mua BTP đóng trực tiếp tại NCC GC.
6. Chứng từ kèm: phiếu đề nghị mua, phiếu nhập kho mua, COA hoặc phiếu kiểm tra chất lượng, hợp đồng, hóa đơn, phiếu kiểm soát chất độc.

Nhập từ *đổ thu / dư sản xuất* có trong danh mục phân loại nhưng quy trình ghi **chưa xây dựng**. Hàng cho tặng tại NCC: ký nháy đối chiếu trên Misa nội bộ rồi cập nhật sổ.

### 3.3. Phối BTP (xuất NL, nhập BTP sau phối)

| | |
|---|---|
| Ai làm | ĐP NL/BTP lập; QLSX duyệt; QLDL gửi lệnh phối cho NCC và đối chiếu công nợ phí phối |
| Sheet / phiếu | *4. DS PHỐI BTP*; *4.1 LSX BTP* (lệnh sản xuất bán thành phẩm); *6. Xuất kho ngoài sản xuất* (phân loại *Xuất NL phối BTP*); *Nhập kho NLBTP* (phân loại *Nhập sau phối*) |
| Đầu vào | Mã lệnh phối, NCC, mã BĐM BTP, số lượng BTP cần phối |
| Đầu ra | Lượng NL thực xuất, lượng BTP thực phối, chênh lệch; BTP vào tồn |

Các bước:

1. Kiểm pháp lý và số lượng; lập yêu cầu phối: chọn mã BĐM thì BTP cần phối, dòng V, màu và danh sách NL tự hiện.
2. Lượng NL cần = định mức NL cho 1.000 lít (kg) BTP × số lượng BTP cần phối / 1.000.
3. Xuất NL đi phối: dòng xuất phân loại *Xuất NL phối BTP*, gắn mã lệnh phối (mã NL và lượng xuất tự lấy theo lệnh phối). Trạng thái dòng: *Chưa gửi lệnh phối*, *Đã gửi lệnh phối chờ nhập kho*, *Hoàn thành*; trạng thái chứng từ: *Chưa gửi*, *Đã gửi*.
4. NCC phối xong: ghi lượng BTP thực phối được; chênh lệch NL = lượng cần − lượng thực xuất; chênh lệch BTP = số cần phối − số thực phối. Trong sai số cho phép thì nhập kho BTP (*Nhập sau phối*) và trạng thái đơn chuyển *có BTP*; vượt thì báo QLSX.
5. Lập đề nghị nhập kho BTP và nhập phí phối; QLDL đối chiếu công nợ, nhận hóa đơn phối trộn (cột *Đơn vị nhận hóa đơn phối trộn*).
6. Tiến độ lệnh phối: *Chưa gửi lệnh*, *NCC đang phối*, *Hoàn thành*.

### 3.4. Xuất VTBB cho sản xuất theo đơn thành phẩm

| | |
|---|---|
| Ai làm | ĐP TP lên đơn và ghi số TP có hàng; ĐP VTBB duyệt và ghi xuất; QLDL gửi bộ chứng từ cho P TCKT |
| Sheet / phiếu | *ĐIỀU PHỐI* (bản chép từ sổ ĐP TP, có khối *Duyệt vật tư bao bì trả về ĐP*); *BDM VTBB*; *XUẤT KHO VTBB SX*; phiếu đề nghị xuất kho |
| Đầu vào | Mã đơn TP, mã BĐM VTBB, kho xuất, phân loại |
| Đầu ra | Trạng thái *đủ VTBB* trả về ĐP TP (ngày đủ nội bộ, ngày đủ thuế, ngày duyệt, mã BĐM nội bộ và thuế); các dòng xuất tạm, xuất thực tế |

Các bước:

1. Nhận đơn mới trên sổ điều phối; lấy mockup; xác định BĐM VTBB của mã hàng (lập mới nếu chưa có, trình QLSX ký *Phiếu BĐM VTBB TP*).
2. Trên sheet xuất: chọn phân loại và kho, **nhập mã đơn** thì thông tin đơn tự hiện (NCC, ngày yêu cầu, thương hiệu, mã hàng, tên pháp lý, ĐVT, SL KD đặt, SL đặt NCC); **nhập mã BĐM** thì bung ra từng VTBB với định mức trên một thành phẩm.
3. Tổng VTBB cần xuất = định mức × số lượng đặt NCC. ĐP VTBB chốt lại số cần sản xuất (nhập tay, làm tròn theo thực tế).
4. Kiểm tồn: đủ thì trả trạng thái *Đủ VTBB* kèm số tồn (nội bộ và thuế). Tồn ở kho hoặc công ty khác: đề xuất chuyển kho hoặc xuất bán nội bộ. Hết tồn: báo KD đổi VTBB hoặc mua.
5. Khi đơn được duyệt, dòng ở trạng thái **Xuất SX tạm**: lượng VTBB đang xuất tạm = số TP chưa sản xuất × định mức.
6. NCC GC có thành phẩm (tối đa 3 lần: ngày và số lượng TP mỗi lần): lượng VTBB xuất thực tế lần i = định mức × số TP lần i. Lượng tạm giảm tương ứng.
7. Ngày NCC có hàng: lập đề nghị xuất kho VTBB gửi QLDL (trước hoặc cùng ngày LSX); đính ảnh chứng từ xuất.
8. Đơn xong: chuyển *Xuất hoàn thành*. Đơn hủy: *Hủy đơn*, số lượng về 0.
9. Sổ có cột **Cảnh báo xuất âm kho** và cột kiểm tra dòng xuất có khớp dòng BĐM hay không (*Đã khớp / Không tồn tại*), kèm ngày duyệt BĐM.

### 3.5. Xuất BTP cho sản xuất theo đơn thành phẩm

| | |
|---|---|
| Ai làm | ĐP NL/BTP |
| Sheet / phiếu | *6.1 Xuất kho theo ĐH thành phẩm*; sổ điều phối; phiếu đề nghị xuất kho BTP; LSX |
| Đầu vào | Mã kho xuất, mã đơn; quy cách thực tế (nếu đóng khác quy cách nhãn); tỷ trọng; số lô |
| Đầu ra | Trạng thái duyệt NL / BTP trả về ĐP TP; lượng BTP trừ thực tế và lượng xuất tạm, theo hai cách tính SX và KD |

Các bước:

1. Nhập mã đơn, các thông tin đơn tự hiện từ sổ điều phối (NCC, ngày, thương hiệu, mã hàng, tên pháp lý, dòng V, màu, ĐVT, SL thành phẩm, SL mẫu Lab, tổng SL gửi NCC).
2. Quy đổi nhu cầu BTP: tách số và đơn vị từ quy cách (ví dụ 350ml thành 350 và ml); tổng theo đơn vị nhỏ = quy cách × SL gửi NCC; đổi sang kg hoặc lít (chia 1.000 nếu đơn vị là ml hoặc gam) rồi nhân tỷ trọng.
3. Chọn **trạng thái duyệt**: *Đủ tồn*, *Chuyển kho*, *Mua*, *Tồn NCC*, *Chờ phối BTP*; ghi ngày đủ NL / BTP nội bộ và thuế, mã BĐM nội bộ và thuế, ngày sản xuất BTP, cấu thành nội bộ và thuế (bên mình, khách, NCC).
4. Khi NCC có TP: lượng trừ thực tế = tổng TP sẵn kho tại NCC (3 lần) × quy cách (dùng quy cách thực tế nếu có nhập, không thì quy cách nhãn), đổi về kg / lít. Lượng xuất tạm = (SL gửi NCC − TP đã có) × quy cách.
5. Hai khối số song song: *Số lượng thực tế trừ đơn theo Sản xuất* và *theo Kinh doanh* (mỗi khối một cột quy cách thực tế riêng).
6. Cảnh báo tiến độ: còn lại chưa sản xuất âm thì *CHƯA SX HẾT*; bằng 0 thì *SX ĐỦ ĐH*; dương thì *SX VƯỢT ĐH*.
7. Phân loại dòng: *Xuất SX tạm*, *Xuất hoàn thành*, *Hủy đơn*, *Chưa đủ BTP*, *BTP NCC - không tồn kho* (không trừ tồn của DEGO), *Đơn hàng đã trừ thực tế*.
8. Ngày NCC có hàng: lập đề nghị xuất kho BTP và LSX gửi QLDL; QLDL gửi P TCKT bộ chứng từ (phiếu xuất BTP / VTBB, hóa đơn NCC, phiếu nhập kho TP).

### 3.6. Xuất ngoài sản xuất

| | |
|---|---|
| Ai làm | ĐP VTBB hoặc ĐP NL/BTP lập; QLSX duyệt; KD duyệt khi liên quan chi phí thương hiệu |
| Sheet / phiếu | *XUẤT KHO VTBB NGOÀI SX*; *6. Xuất kho ngoài sản xuất*; *4. Phiếu đề nghị xuất*; *7. Phiếu đề nghị đưa vào chi phí*; *2. Phiếu đề nghị xuất bán nội bộ*; *3. Phiếu yêu cầu xuất hóa đơn* |
| Đầu vào | Ngày xuất, phân loại, kho, thương hiệu, mã, lượng, số hóa đơn, ghi chú, ảnh phiếu xuất, mã số phiếu; với NL / BTP thêm lô, giá, thành tiền, nhân sự yêu cầu, lý do gửi NCC, tài xế, số xe |
| Đầu ra | Dòng xuất; phiếu in gửi NCC và P TCKT |

Các nhánh:

1. **Xuất mẫu thử, cho tặng, xuất khác**: ghi dòng xuất, in phiếu đề nghị xuất kho (người nhận, địa chỉ giao, lý do, kho xuất; dòng hàng có SL yêu cầu và SL thực xuất, đơn giá, thành tiền, tiền bằng chữ).
2. **Hao hụt**: phát hiện qua kiểm kê định kỳ hoặc sản xuất thực tế; NCC xác định nguyên nhân; so với % hao hụt cho phép theo hợp đồng; chuyển sang kho lỗi / chờ xử lý. *Trong hạn mức*: lập *Phiếu đề nghị đưa vào chi phí* (khoản mục chi phí, công ty chịu) rồi ghi *Xuất hao hụt / đổ bỏ*. *Vượt hạn mức*: NCC đền hàng (chuyển từ kho lỗi về kho dùng sau khi QLDL ký với NCC) hoặc đền tiền (lập đề nghị xuất kho hao hụt, P TCKT theo dõi hoàn hoặc cấn trừ).
3. **Hư hỏng**: nhận hình, số lô, khối lượng, biên bản; chuyển kho lỗi; Lab giám định; phương án: tiếp tục dùng, **hủy** (NCC thuê đơn vị tiêu hủy, biên bản tiêu hủy, phiếu xuất hủy), hoặc **tái chế** (chỉ BTP, phải xác định lại công thức và pháp lý, có xác nhận của Pháp lý và P TCKT).
4. **Xuất chi phí theo yêu cầu bộ phận khác**: đối chiếu tồn nội bộ và thuế; cùng công ty thì xuất kho nội bộ; khác công ty thì xuất hóa đơn và xuất kho (thuế) hoặc xuất bán nội bộ (nội bộ).
5. **Xuất bán**: bán giữa các thương hiệu, công ty; bán cho NCC GC khi NCC đóng lỗi hoặc làm mất hàng.

### 3.7. Chuyển kho

| | |
|---|---|
| Ai làm | KD chốt; ĐP VTBB / ĐP NL/BTP hoặc QLDL thực hiện; QLSX duyệt; kho hai đầu ký |
| Sheet / phiếu | *6. Phiếu đề nghị chuyển* (kho xuất, kho nhập, phân loại, dòng hàng với SL yêu cầu và SL thực xuất; ký Trưởng bộ phận, Người lập, Kế toán); một dòng *Xuất chuyển kho* và một dòng *Nhập chuyển kho* trong sổ |
| Đầu vào | Loại hàng, số lượng, đơn liên quan, kho chuyển, kho nhận, phương án vận chuyển |
| Đầu ra | Tồn giảm ở kho xuất, tăng ở kho nhập; chứng từ cho P TCKT |

Các bước:

1. Lý do chuyển: theo đơn hàng; NCC yêu cầu rút vật tư; theo yêu cầu xử lý sự cố hoặc bộ phận khác.
2. KD chốt loại, số lượng, kho; chọn vận chuyển: xe công ty đặt riêng, xe công ty ghép chuyến, hoặc thuê ngoài qua Thu mua. Chuyển BTP giữa NCC thì Lab bảo đảm tiêu chí chất lượng; VTBB phải kiểm điều kiện lưu trữ.
3. Nhận thông tin tài xế, ngày, địa chỉ; báo NCC trước 1 ngày; gửi đề nghị xuất kho cho NCC xuất và đề nghị nhập kho cho NCC nhập.
4. Trong ngày nhận bản chụp có chữ ký hai bên; cập nhật **số thực** xuất, thực nhận.
5. Chứng từ theo quan hệ pháp nhân: cùng công ty lập phiếu đề nghị chuyển kho nội bộ; khác công ty lập phiếu yêu cầu xuất hóa đơn + xuất kho + nhập kho (sổ thuế) hoặc phiếu xuất bán nội bộ + xuất + nhập (sổ nội bộ). Nội bộ khác phần mềm Misa cũng dùng phiếu xuất bán.
6. Trạng thái dòng chuyển (NL / BTP): *Chốt chuyển kho, chờ vận chuyển*, *Đang vận chuyển*, *Hoàn thành*.
7. **Bán giữa các thương hiệu** (chỉ chuyển số liệu, hàng không di chuyển): KD chốt số lượng chia lại; kiểm tồn trên Misa thuế và Misa nội bộ; lập chứng từ nội bộ và thuế.

### 3.8. Nhận thành phẩm

| | |
|---|---|
| Ai làm | ĐP TP; tài xế; kho Dr.Xanh (KCS); QLDL |
| Sheet / phiếu | Sổ NHẬP-XUẤT TP; danh sách nhận hàng; kết quả KCS kho; phiếu đề nghị nhập kho TP; phiếu đề nghị xuất kho bán hàng |
| Đầu vào | Mã đơn, kho xuất (NCC GC), kho nhận, trạng thái giao dịch (1 đến 7), mã hàng, SL thùng và SL lẻ, mã lô, số hóa đơn, NSX, HSD, kết quả Lab, biển số, tài xế |
| Đầu ra | Tồn TP tại NCC GC và tại kho DEGO; trạng thái đơn; căn cứ xuất VTBB / BTP thực tế |

Các bước:

1. NCC báo có hàng; ĐP TP ghi ngày và số TP sẵn kho tại NCC (tối đa 3 lần). Số này là **mốc để trừ thực tế VTBB và BTP** ở mục 3.4, 3.5.
2. Lấy mẫu gửi Lab; đạt thì lên danh sách nhận hàng cho tài xế.
3. Kho nhận, KCS: SL yêu cầu nhận, SL thực nhận, NSX, số lô, HSD, phụ kiện đi kèm, ngoại dạng, chứng từ NCC khớp hay không, SL đạt, SL không đạt, nguyên nhân.
4. Lập phiếu đề nghị nhập kho TP (SL mới, SL mẫu; ô ký *Duyệt đủ VTBB*, *Duyệt đủ NL*).
5. Hàng dư: KD nhận thì ghi *Nhập TP*; KD chưa nhận thì chuyển sự cố.
6. Xuất bán cho công ty nội bộ bằng phiếu đề nghị xuất kho bán hàng (có thể nhiều lần).
7. Tồn TP tại NCC GC = Nhập TP + Nhập mẫu + Nhập dư − Chuyển kho + Trả hàng − Xuất xử lý + Nhập sau xử lý; theo dõi số ngày tồn tại NCC và HSD còn lại.

### 3.9. Đối chiếu tồn với NCC GC định kỳ

| | |
|---|---|
| Ai làm | ĐP VTBB, ĐP NL/BTP đối chiếu phần mình; QLDL tổng hợp bốn nhóm; QLSX duyệt và ký biên bản |
| Sheet / phiếu | *DỮ LIỆU NCC*, *ĐỐI CHIẾU NCC*, *ĐỐI CHIẾU CÁC LẦN*, *LỊCH SỬ ĐỐI CHIẾU* (cả tệp 3 và tệp 4); tệp *7. Đối chiếu tồn kho* của QLDL; biên bản xác nhận tồn kho; biên bản kiểm tra và giải trình chênh lệch; giấy ủy quyền QLSX ký biên bản |
| Đầu vào | Báo cáo tồn NCC gửi (email, Excel, biên bản), mỗi NCC một mẫu, dùng mã của NCC |
| Đầu ra | Kết luận từng dòng; hướng điều chỉnh; biên bản hai bên |

Các bước:

1. Dán số liệu NCC vào bảng: ngày báo cáo, tên NCC, **kho (bắt buộc)**, mã NCC và tên NCC của vật tư; mã DEGO tự tra qua bảng ánh xạ; SL giao nhận theo NCC (không bắt buộc), tồn cuối kỳ theo NCC, ghi chú.
2. Bấm đối chiếu: với từng dòng, so số giao dịch trong kỳ và số tồn giữa NCC và sổ của mình **trên đúng kho đó**.
3. Kết luận tự động: *Khớp*; *Lệch*; *Không tìm thấy Mã + Kho trong sổ tồn*; *Thiếu Kho*. Dung sai khi so là **% hao hụt cho phép của NCC đó**.
4. So với lần NCC gửi trước (tồn cuối, dư cuối, ngày kiểm tồn tại NCC, số lần gửi); khác 0 thì tô đỏ.
5. Kiểm thêm Misa thuế và Misa nội bộ; lập biên bản giải trình chênh lệch và biên bản xác nhận tồn; QLSX duyệt; NCC gửi biên bản chính thức, mỗi bên một bản.
6. Lưu kết quả vào lịch sử kèm *hướng điều chỉnh với NCC GC*, *nguyên nhân*, *trạng thái xử lý chênh lệch*. Mục lục ghi rõ hai chỗ còn thiếu: chưa theo dõi xử lý sau đối chiếu, chưa xác định phiếu in.
7. Hao hụt phát hiện khi đối chiếu đi tiếp theo mục 3.6 nhánh 2.
8. Song song, QLDL đối chiếu **phí lưu kho và hao hụt** cuối tháng theo biên bản tồn của NCC.

### 3.10. Kiểm kê và cân đối khi phát sinh lỗi

Sheet *TỒN KHO MẪU 9.10* (có ở cả hai tệp) là mẫu mới nhất phòng Sản xuất phác ra, gộp ba tình huống trên một dòng mã + kho:

| Khối | Cột | Ý nghĩa |
|---|---|---|
| Khi phát sinh lỗi | Mã, Kho (kho thường và kho lỗi là hai dòng riêng) | Hàng lỗi tách sang kho lỗi, vẫn nhìn cùng một bảng |
| Đối chiếu NCC | Nhập, Xuất thực tế, Xuất, Tồn (= Nhập − Xuất) | Số dùng để so với NCC |
| Cân đối hàng | Xuất tạm (khi đủ cho đơn), Đơn chờ xuất (khi chưa đủ cho đơn), Còn thiếu (= Tồn − Xuất tạm − Đơn chờ xuất) | Biết thiếu bao nhiêu để mua, chuyển, phối |

Hàng lỗi được ghi ở sổ chuyển hàng lỗi (mỗi dòng một lần chuyển giữa hai kho và / hoặc hai trạng thái): phát sinh thì vào kho lỗi của NCC; chốt phương án (xử lý lại chính nó, chuyển thành hàng khác, tiêu hủy, đổ thu BTP); hoàn thành thì về kho sử dụng, hoặc ra *(Tiêu hủy)* / *(Xuất chi phí)*. Tồn lỗi = số phát sinh − số đã hoàn thành. Yêu cầu xử lý lại lấy *SL đạt* và *SL hao hụt / tiêu hủy* từ sổ kho theo mã yêu cầu, tính tỷ lệ thu hồi và đánh giá đúng hạn / trễ hạn.

Tài liệu nguồn **không có quy trình kiểm kê thực tế do DEGO tự đếm** tại kho NCC GC; việc kiểm tồn dựa trên biên bản của NCC.

### 3.11. Báo cáo tồn theo kỳ

1. **Tồn tức thời** (*TỒN KHO*): tự cập nhật từ ba sổ nhập, xuất SX, xuất ngoài SX.
2. **Tồn theo kỳ** (*TỒN KHO THEO KỲ*): chọn từ ngày, đến ngày; liệt kê từng giao dịch kèm tồn thực tế, tồn tạm, tồn lỗi **sau giao dịch** và cảnh báo tồn âm; giao dịch trước kỳ được gộp thành nhóm *Đầu kỳ*.
3. **Báo cáo VTBB hằng tháng** (tệp *BC VTBB*, khoảng 2 phút mỗi tháng): chép sổ giao dịch sang, thêm mã mới vào danh mục, đổi ngày báo cáo, xem ô kiểm tra dữ liệu (các số phải bằng 0). Ra báo cáo tháng, quý, khoảng tùy chọn, dashboard.
4. **Báo cáo KD**: tồn từng thương hiệu và tổng; lịch sử sử dụng theo BĐM; tỷ lệ hao hụt theo loại VTBB và theo NCC; MOQ; đơn giá lưu kho; giá min / max 5 lần mua gần nhất.
5. **Báo cáo NL / BTP** (mới có khung): tồn theo kỳ, lô sắp hết hạn, tồn vượt mức tối đa, tỷ lệ hao hụt, thiếu hóa đơn, kèm sổ theo dõi vấn đề và hành động.

---

## 4. Danh sách tính năng

Cột **ERP đã có**: *Có* = dùng được ngay; *Một phần* = có nền nhưng thiếu phần phòng Sản xuất cần; *Chưa* = chưa có mã. Hiện trạng ERP tóm tắt: danh mục kho `tab_warehouse` (mã, tên, địa chỉ, đang dùng) ở màn `/inventory/warehouses`; tồn `tab_inventory` theo khóa *công ty + kho + mã hàng* (số lượng, đơn giá bình quân, giá trị) ở màn `/inventory/stock`; sổ phát sinh `tab_inventory_move` chỉ có hai loại `gr` (nhận hàng từ ĐMH) và `adjust` (điều chỉnh tay); phiếu nhập ngầm `tab_goods_receipt` sinh khi ghi số nhận trên lần giao `tab_po_delivery`; tổng quan kho ở `/inventory`. **Chưa có** phiếu xuất, chuyển kho, kiểm kê, lô, hạn dùng, nhiều trạng thái tồn, chiều thương hiệu.

| Mã | Tính năng | Mô tả ngắn | Quy trình / sheet nguồn | ERP đã có | Ưu tiên |
|---|---|---|---|---|---|
| SX-KHO-01 | Danh mục kho gia công | Kho có loại (DEGO, tại NCC GC, kho lỗi, thương mại), gắn NCC GC, kho lỗi đi cặp, loại hàng chứa, mã kho Misa | DATA 1 (kho) | Một phần — `tab_warehouse`, màn `/inventory/warehouses`; thiếu loại kho, NCC, cặp kho lỗi | Cao — nền của mọi phiếu |
| SX-KHO-02 | Danh mục loại giao dịch kho | Mỗi loại có chiều, nhóm tồn, nhóm báo cáo, cờ hao hụt, phạm vi (dùng chung / chỉ NL-BTP) | DATA 1; BC VTBB › CẤU HÌNH | Chưa — `ref_type` chỉ `gr`, `adjust` | Cao — quyết định cách tính tồn |
| SX-KHO-03 | Tồn theo thương hiệu | Thêm chiều thương hiệu (và *Dùng chung*) vào khóa tồn | Mọi sổ nhập, xuất, tồn | Chưa — khóa tồn chỉ có `company_id` (pháp nhân) | Cao — sổ hiện tại khớp theo ba trường |
| SX-KHO-04 | Ánh xạ mã vật tư NCC GC | Bảng mã DEGO, mã NCC, tên NCC đặt, theo từng NCC GC | DATA 1 (mã của DEGO, mã của NCC); DỮ LIỆU NCC | Chưa | Cao — không có thì không đối chiếu được |
| SX-KHO-05 | Khai báo Min, MOQ theo mã + kho | Tồn an toàn, số đặt tối thiểu, NCC phụ trách, số đang đặt chưa về, ghi chú | THÔNG TIN khối 1; BC VTBB › MIN MOQ | Chưa — chỉ có `moq` trên báo giá khảo sát | Trung bình — cần cho cảnh báo và đề xuất đặt |
| SX-KHO-06 | Chính sách kho theo NCC GC | % hao hụt cho phép (theo NCC, theo loại hàng), phí lưu kho, đơn vị tính phí, số ngày miễn phí | DATA 1; THÔNG TIN khối 2; Data NCC GC | Một phần — `tab_supplier` có hồ sơ NCC, thiếu các trường chính sách | Trung bình — dùng làm dung sai đối chiếu |
| SX-KHO-07 | Số dư đầu kỳ | Nhập tồn đầu (dùng được và lỗi) khi chuyển sổ, có đơn giá đầu kỳ | Nhập đầu kỳ, Nhập đầu kỳ lỗi | Một phần — làm bằng điều chỉnh tay `adjust` | Cao — phải có để chạy thật |
| SX-KHO-08 | Nhập kho từ mua hàng | Nhận hàng theo ĐMH vào kho NCC GC, theo thương hiệu, có ảnh phiếu, số hóa đơn | 3.1; NHẬP KHO VTBB | Một phần — `tab_po_delivery` → `tab_goods_receipt` + `tab_inventory_move`; thiếu thương hiệu, ảnh phiếu NCC | Cao |
| SX-KHO-09 | Nhập NL / BTP theo lô | Số lô, NSX, HSD, số CAS, hàm lượng thực tế, kết quả Lab trên dòng nhập | 3.2; Nhập kho NLBTP | Chưa — không có lô, hạn dùng; `qc_result` chỉ một chữ | Cao — bắt buộc với hóa chất |
| SX-KHO-10 | Nhập tạm chờ kiểm duyệt | Hàng về chưa có kết quả Lab ghi tồn tạm; đạt thì chuyển thực tế, không đạt chuyển lỗi | 2.4; QT8 mục E | Chưa | Cao — tách hàng chưa dùng được |
| SX-KHO-11 | Lệnh phối BTP | Xuất NL đi phối, nhập BTP sau phối, so định mức, chênh lệch, tiến độ | 3.3; 4. DS PHỐI BTP, 4.1 LSX BTP | Chưa | Cao — cách tạo BTP chính |
| SX-KHO-12 | Nhập khác: đổ thu, dư sau sản xuất, cho tặng | Các loại nhập không qua mua | 2.4; QT8 E4, E5 | Một phần — điều chỉnh tay, không có loại | Thấp — quy trình nguồn chưa xây |
| SX-KHO-13 | Nhập, chuyển, trả thành phẩm | Bảy trạng thái giao dịch TP; lô, NSX, HSD; KCS khi nhận | 3.8; sổ NHẬP-XUẤT TP | Chưa | Cao — khép vòng đơn gia công |
| SX-KHO-14 | Duyệt đủ vật tư cho đơn TP | ĐP VTBB, ĐP NL/BTP trả trạng thái, ngày đủ nội bộ, ngày đủ thuế, mã BĐM | 3.4, 3.5; khối *Duyệt VTBB trả về ĐP* | Chưa | Cao — điều kiện gửi đơn NCC |
| SX-KHO-15 | Xuất VTBB theo đơn TP và BĐM | Nhập mã đơn + mã BĐM, hệ thống bung dòng và tính số cần xuất | 3.4; XUẤT KHO VTBB SX | Chưa — có định mức bao bì `tab_packaging_bom`, chưa có phiếu xuất | Cao |
| SX-KHO-16 | Xuất BTP theo đơn TP | Quy đổi quy cách × số lượng × tỷ trọng ra kg / lít | 3.5; 6.1 Xuất kho theo ĐH TP | Chưa | Cao |
| SX-KHO-17 | Xuất tạm và giữ hàng cho đơn | Đơn duyệt thì giữ; có TP thì chuyển thực tế từng lần; đơn xong thì hoàn thành | 3.4, 3.5; cột *đang xuất tạm* | Chưa | Cao — lõi của *tồn có thể sản xuất* |
| SX-KHO-18 | Ghi nhận xuất theo lần NCC có thành phẩm | Tối đa 3 lần (nên không giới hạn): ngày, số TP, tự tính VTBB / BTP đã dùng | 2.6; 3.4 bước 6 | Chưa | Cao |
| SX-KHO-19 | Cảnh báo và chặn xuất âm kho | Báo khi số xuất vượt tồn; liệt kê dòng gây âm | Cột *Cảnh báo xuất âm kho*; TỒN KHO cột Cảnh báo | Chưa — điều chỉnh tay không kiểm tồn âm | Cao |
| SX-KHO-20 | Hủy đơn và hoàn giữ hàng | Đơn hủy thì số giữ về 0, tồn có thể sản xuất tăng lại | Phân loại *Hủy đơn* | Chưa | Trung bình |
| SX-KHO-21 | Xuất ngoài sản xuất | Mẫu thử, cho tặng, xuất khác, xuất bán; có lý do, người nhận, ảnh phiếu | 3.6; XUẤT KHO VTBB NGOÀI SX; 6. Xuất kho ngoài SX | Chưa | Cao |
| SX-KHO-22 | Chuyển kho | Một phiếu sinh xuất ở kho đi và nhập ở kho đến; SL yêu cầu, SL thực; tài xế, xe; trạng thái vận chuyển | 3.7; phiếu 6 | Chưa | Cao |
| SX-KHO-23 | Xuất bán nội bộ và yêu cầu xuất hóa đơn | Chuyển quyền sở hữu giữa thương hiệu / pháp nhân, có đơn giá, thành tiền | 3.7 bước 5, 7; phiếu 2, 3 | Chưa | Trung bình — phụ thuộc quyết định hai sổ |
| SX-KHO-24 | Đưa vào chi phí | Phiếu đề nghị đưa hàng vào chi phí: khoản mục, công ty chịu, giá trị | 3.6; phiếu 7 | Chưa | Trung bình |
| SX-KHO-25 | Hao hụt, đổ bỏ, xuất hủy | Ghi hao hụt, so định mức, rẽ nhánh trong / vượt hạn mức; biên bản tiêu hủy | 3.6 nhánh 2, 3 | Chưa | Cao — căn cứ cấn trừ NCC |
| SX-KHO-26 | Kho lỗi và chuyển trạng thái hàng lỗi | Nhập lỗi, chuyển giữa kho lỗi và kho dùng, gắn mã sự cố, mã yêu cầu xử lý lại | 3.10; LỊCH SỬ TỪ SỰ CỐ | Chưa | Cao |
| SX-KHO-27 | Mẫu cho tặng không quản tồn | Ghi nhận mẫu được cho tặng: mục đích, thông số, việc cần làm (test, chụp, lưu, gửi) | MẪU CHO TẶNG VTBB; QT8 mục I | Chưa | Thấp |
| SX-KHO-28 | Bộ phiếu in kho | Đề nghị nhập, xuất, chuyển, xuất bán nội bộ, đưa vào chi phí, nhập kho TP; số phiếu, chữ ký, tiền bằng chữ | Phiếu 2 đến 7 | Chưa — ERP có khung in chứng từ thu mua | Trung bình |
| SX-KHO-29 | Tồn tức thời ba nhóm | Theo kho × thương hiệu × mã: đầu kỳ, nhập, xuất, tồn thực tế, tồn tạm, tồn lỗi, tồn có thể sản xuất | TỒN KHO; 8.1 Tồn kho tổng | Một phần — `tab_inventory` chỉ một số `qty`, màn `/inventory/stock` | Cao |
| SX-KHO-30 | Tồn chi tiết theo lô | Từng lô: ngày nhập, NSX, HSD, tồn, đơn giá, trạng thái dùng được, đơn đang treo | 8. Tồn kho chi tiết SX | Chưa | Cao |
| SX-KHO-31 | Sổ giao dịch kho | Mọi giao dịch theo thời gian, lọc kho, thương hiệu, mã, loại; truy về phiếu gốc | LỊCH SỬ; TỒN KHO cột *Sheet GD cuối* | Một phần — `GET /api/inventory/moves` (chỉ nhập và điều chỉnh) | Cao |
| SX-KHO-32 | Tồn theo kỳ | Chọn khoảng ngày; tồn đầu, nhập, xuất, tồn cuối; tồn lũy kế sau từng giao dịch | TỒN KHO THEO KỲ | Chưa | Cao |
| SX-KHO-33 | Giá trị tồn và đơn giá bình quân | Đơn giá theo nhóm nhập; giá trị tồn; sổ tổng hợp có giá | 8.1 (cột Đơn giá BQGQ); 10. Sổ tổng hợp tồn kho có giá | Một phần — `avg_cost`, `value` bình quân gia quyền trên toàn sổ | Cao — đầu vào giá vốn |
| SX-KHO-34 | Hai góc nhìn tồn SX và KD | Trừ BTP theo quy cách thực đóng và theo quy cách KD | 8 / 8.1 và 9 / 9.1 | Chưa | Trung bình — cần chốt có giữ hai sổ không |
| SX-KHO-35 | Tồn nội bộ và tồn thuế | Hai sổ tồn; kiểm đủ cả hai khi duyệt đơn | TỒN KHO (ghi chú); QT8, QT9 | Chưa | Trung bình — cần quyết định lớn |
| SX-KHO-36 | Cảnh báo tồn | Tồn âm; không giao dịch quá n ngày; dưới Min; dưới MOQ; sắp hết hạn | TỒN KHO cột X, AA; 8.1 cột AM, AN | Một phần — tổng quan `/inventory` có tám mã tồn thấp nhất | Trung bình |
| SX-KHO-37 | Tồn thành phẩm tại NCC GC | Tồn TP theo NCC × mã × NSX; số ngày tồn; HSD còn lại | BC tồn kho tại NCC GC | Chưa | Trung bình |
| SX-KHO-38 | Nạp số liệu tồn NCC GC gửi | Dán / nhập tệp theo mẫu từng NCC; tự đổi mã NCC sang mã DEGO | DỮ LIỆU NCC; Tồn kho từ NCC GC | Chưa | Cao |
| SX-KHO-39 | Đối chiếu tự động với NCC GC | So giao dịch và tồn theo mã + kho; dung sai theo % hao hụt; kết luận | ĐỐI CHIẾU NCC; tệp 7 (4 nhóm) | Chưa | Cao — rủi ro tiền hàng lớn nhất |
| SX-KHO-40 | Lịch sử đối chiếu và xử lý chênh lệch | Lưu từng kỳ; hướng điều chỉnh, nguyên nhân, trạng thái xử lý | LỊCH SỬ ĐỐI CHIẾU | Chưa | Cao |
| SX-KHO-41 | So sánh các lần NCC gửi | Lần gần nhất so lần trước; khác thì cảnh báo | ĐỐI CHIẾU CÁC LẦN | Chưa | Thấp |
| SX-KHO-42 | Biên bản xác nhận tồn và giải trình chênh lệch | In biên bản hai bên ký; đính bản ký | QT8 mục G; QT9 mục H | Chưa | Trung bình |
| SX-KHO-43 | Phí lưu kho và hao hụt NCC tính | Ghi phía mình, ghi phía NCC, đối chiếu, hạn thanh toán | Tệp 7 (3 sheet) | Chưa — công nợ `payable` chỉ sinh từ ĐMH | Trung bình |
| SX-KHO-44 | Chốt kỳ kho | Lưu ảnh tồn cuối tháng, chặn sửa giao dịch kỳ đã chốt | TỒN KHO (ghi chú lưu tệp cuối tháng) | Chưa | Trung bình |
| SX-KHO-45 | Báo cáo xuất nhập tồn theo kỳ | Tháng, quý, tùy chọn; theo loại hàng, thương hiệu, kho, NCC; so cùng kỳ | BC VTBB › BÁO CÁO THÁNG, QUÝ, TỔNG HỢP TÙY CHỌN | Chưa | Trung bình |
| SX-KHO-46 | Tuổi tồn, tồn lâu, tồn chết | Số ngày tồn, nhóm tuổi, nhóm luân chuyển, top tồn lâu | BC VTBB › XNT VTBB, DASHBOARD | Chưa | Trung bình |
| SX-KHO-47 | Đề xuất đặt hàng theo Min, MOQ | Danh sách mã dưới Min kèm số đề xuất; tạo YCMH nháp | BC VTBB › XNT VTBB | Chưa — nút tạo YCMH từ mã tồn thấp có ở tổng quan kho | Trung bình |
| SX-KHO-48 | Báo cáo hao hụt và lỗi nhập | Tỷ lệ hao hụt so định mức theo loại, theo NCC GC; tỷ lệ lỗi nhập theo NCC bán | BC VTBB › BÁO CÁO THÁNG | Chưa | Trung bình |
| SX-KHO-49 | Dashboard kho và kiểm tra dữ liệu | Chỉ số chính, tồn theo loại / thương hiệu / kho, ô kiểm tra dữ liệu | BC VTBB › DASHBOARD | Một phần — `/inventory` (tổng giá trị, biểu đồ theo kho) | Thấp |
| SX-KHO-50 | Báo cáo NL / BTP và sổ theo dõi vấn đề | Lô sắp hết hạn, tồn vượt tối đa, thiếu hóa đơn; sổ vấn đề và hành động | Báo cáo, Chi tiết báo cáo, Báo cáo xử lý | Chưa | Thấp — nguồn mới có khung |

Tổng: 50 tính năng; 28 ưu tiên Cao, 17 Trung bình, 5 Thấp. Trên ERP: 0 *Có* trọn vẹn, 10 *Một phần*, 40 *Chưa*.

---

## 5. Chi tiết từng tính năng

### SX-KHO-01 — Danh mục kho gia công

- **Đầu vào:** tên viết tắt, mã kho (trùng mã Misa), tên đầy đủ, địa chỉ, người nhận hàng, định nghĩa; loại kho; NCC GC sở hữu địa điểm; kho lỗi đi cặp; loại hàng chứa (NL, BTP, VTBB, TP).
- **Đầu ra:** danh sách chọn kho trên mọi phiếu; cột *kho đã chuẩn hóa* trên báo cáo.
- **Quy tắc:** mỗi NCC GC có một kho thường và một kho lỗi; mã theo mẫu `KHO NCC_<TÊN>` và `KHO NCCXL_<TÊN>`. Tên kho trùng nghĩa phải gộp về một kho.
- **Ràng buộc:** không cho hai tên viết tắt trỏ cùng một mã kho; kho đã có giao dịch thì không xóa, chỉ ngưng dùng.
- **Liên kết:** SX-KHO-06 (chính sách theo NCC), SX-KHO-26 (kho lỗi), hồ sơ NCC GC.

### SX-KHO-02 — Danh mục loại giao dịch kho

- **Đầu vào:** tên loại, chiều (+1 nhập, −1 xuất), nhóm tồn (Thực tế, Tạm, Lỗi), nhóm báo cáo (Nhập, Xuất, Đầu kỳ, Chuyển kho), cờ hao hụt / hủy, phạm vi (dùng chung hay chỉ NL / BTP), diễn giải.
- **Đầu ra:** danh sách chọn *Phân loại* trên phiếu; luật cộng trừ tồn.
- **Quy tắc:** *Đầu kỳ* và *Chuyển kho* chỉ làm đổi tồn, **không** tính vào giá trị nhập, giá trị xuất của kỳ. Loại có cờ hao hụt vào chỉ tiêu hao hụt. Danh sách chuẩn ở mục 2.4.
- **Ràng buộc:** người dùng **chọn**, không gõ tay (sổ hiện tại bắt *gõ đúng chữ* nên hay lệch); loại lạ phải được quản trị thêm vào danh mục trước.
- **Liên kết:** SX-KHO-29, 45, 48.

### SX-KHO-03 — Tồn theo thương hiệu

- **Đầu vào:** thương hiệu trên mỗi dòng nhập, xuất; danh mục thương hiệu có giá trị *Dùng chung*.
- **Đầu ra:** tồn theo kho × thương hiệu × mã; tổng hợp tất cả thương hiệu.
- **Quy tắc:** hàng của thương hiệu nào chỉ xuất cho đơn của thương hiệu đó; muốn dùng của thương hiệu khác phải qua xuất bán nội bộ (SX-KHO-23). Sổ BTP quy ước gom một số thương hiệu về IDA khi tra đơn (DEGO AGROCHEM, DEGO, BAMBOO được tính là IDA) — cần chốt lại quy tắc này.
- **Ràng buộc:** thương hiệu bắt buộc trên mọi dòng.
- **Liên kết:** quan hệ thương hiệu với pháp nhân (`company_id` của ERP) phải chốt, xem câu hỏi 2.

### SX-KHO-04 — Ánh xạ mã vật tư NCC GC

- **Đầu vào:** NCC GC, mã vật tư của NCC, tên vật tư của NCC, mã DEGO, tên DEGO.
- **Đầu ra:** tự đổi mã khi nạp tồn NCC gửi; in mã NCC trên phiếu gửi NCC.
- **Quy tắc:** tra theo mã NCC; không có mã thì tra theo tên NCC. Một mã DEGO có thể ứng với mã khác nhau ở từng NCC. Có dòng đặc biệt *không có mã* (ví dụ BTP do NCC dự trù, không nhập kho DEGO).
- **Ràng buộc:** dòng NCC gửi không ánh xạ được phải hiện ở danh sách *chưa ánh xạ*, không bỏ qua im lặng.
- **Liên kết:** SX-KHO-38, 39.

### SX-KHO-05 — Khai báo Min, MOQ theo mã + kho

- **Đầu vào:** mã hàng, kho, Min (tồn an toàn), MOQ (số đặt tối thiểu, lấy của NCC có MOQ nhỏ nhất), NCC phụ trách, thương hiệu, số đang đặt chưa về, ghi chú (hợp đồng, chu kỳ đặt).
- **Đầu ra:** trạng thái Min / MOQ trên sổ tồn; số đề xuất đặt.
- **Quy tắc:** tồn nhỏ hơn Min thì báo cần đặt; mỗi lần đặt không nhỏ hơn MOQ. Mục lục ghi hướng mở rộng: khi KD xác nhận định mức tồn thì **tự cộng định mức của tất cả thương hiệu** cho cùng mã + kho.
- **Ràng buộc:** cặp mã + kho không có trong sổ tồn thì báo *Không khớp Mã / Kho*.
- **Liên kết:** SX-KHO-36, 47. Số đang đặt chưa về nên lấy tự động từ ĐMH còn mở trên ERP.

### SX-KHO-06 — Chính sách kho theo NCC GC

- **Đầu vào:** NCC GC; % hao hụt cho phép (chung, hoặc theo nhóm: BTP, chai / túi / can, nhãn, thùng, khác); có / không phí lưu kho; chi tiết và đơn vị tính phí; số ngày lưu kho miễn phí (TP; VTBB và NL); ghi chú điều khoản hợp đồng.
- **Đầu ra:** dung sai cho đối chiếu; ngưỡng cảnh báo hao hụt; căn cứ tính phí lưu kho.
- **Quy tắc:** hao hụt thực tế = số lượng hao hụt / số lượng nhập × 100%; lớn hơn % cho phép thì tô đỏ và nêu tên NCC. % này cũng là dung sai khi đối chiếu. Giá trị *theo thực tế* nghĩa là chưa có con số thỏa thuận.
- **Ràng buộc:** chỉ một nguồn chuẩn cho % hao hụt (hiện có bốn nơi ghi khác nhau, xem câu hỏi 8).
- **Liên kết:** SX-KHO-25, 39, 43, 48; hợp đồng NCC.

### SX-KHO-07 — Số dư đầu kỳ

- **Đầu vào:** ngày đầu kỳ, kho, thương hiệu, mã, số lượng dùng được, số lượng lỗi, đơn giá đầu kỳ; với NL / BTP thêm lô, NSX, HSD.
- **Đầu ra:** cột *Đầu kỳ* và *Đầu kỳ (lỗi)* trên sổ tồn.
- **Quy tắc:** số dư đầu không tính vào nhập của kỳ; ngày nhập đầu kỳ không dùng để tính tuổi tồn (dùng ngày nhập thật nếu biết), nếu không sẽ làm sai số ngày tồn.
- **Ràng buộc:** mỗi khóa tồn chỉ một dòng đầu kỳ cho một ngày chuyển sổ; cần người duyệt.
- **Liên kết:** SX-KHO-44 (chốt kỳ), SX-KHO-46.

### SX-KHO-08 — Nhập kho từ mua hàng

- **Đầu vào:** ĐMH và lần giao; kho nhận; thương hiệu; mã, lượng nhận; số hóa đơn, tên trên hóa đơn, đơn vị nhận hóa đơn; ảnh phiếu nhập của kho NCC GC; mã đơn KD (nếu mua theo đơn).
- **Đầu ra:** dòng *Nhập mua* (hoặc *Nhập tạm*); tồn tăng; giá nhập.
- **Quy tắc:** giá nhập kho VTBB hiện lấy **giá đã gồm VAT và vận chuyển**, tra theo ngày nhận + mã + số lượng + mã ĐMH. Trên ERP, lần giao đã có đủ số nhận, kho, ngày, số hóa đơn, tiền vận chuyển, nên phần tra tay này bỏ được.
- **Ràng buộc:** bắt buộc có mã ĐMH khi phân loại là *Nhập mua*; số nhận không vượt số đặt trừ khi có dung sai.
- **Liên kết:** Thu mua (ĐMH, nhận hàng), SX-KHO-09, 10, 33.

### SX-KHO-09 — Nhập NL / BTP theo lô

- **Đầu vào:** như SX-KHO-08, thêm số lô, NSX, HSD, số CAS, dòng V sản xuất, dòng V kinh doanh, màu, kết quả Lab (Đạt / Không đạt), ghi chú Lab, hàm lượng thực tế.
- **Đầu ra:** tồn theo lô; HSD còn lại.
- **Quy tắc:** thành tiền = lượng nhập × giá; HSD còn lại (ngày) = HSD − hôm nay; NSX trên bao bì NL không sau ngày nhận hóa đơn. Hàm lượng thực tế so với đăng ký theo bảng sai số ở mục 2.7.
- **Ràng buộc:** NL / BTP không có số lô thì không cho ghi nhập thực tế; cảnh báo lô đã hết hạn.
- **Liên kết:** SX-KHO-30, 50; phân hệ lô và hạn dùng của ERP (đang ở mức nghiên cứu).

### SX-KHO-10 — Nhập tạm chờ kiểm duyệt

- **Đầu vào:** dòng nhập ở trạng thái tạm; kết quả Lab.
- **Đầu ra:** chuyển *Nhập tạm* thành *Nhập mua* (đạt) hoặc *Nhập lỗi / hư hỏng* (không đạt).
- **Quy tắc:** tồn tạm không được tính là dùng được ngay; khi chuyển trạng thái phải giữ nguyên ngày nhận gốc và ghi thêm ngày duyệt.
- **Ràng buộc:** hàng nhập tạm quá số ngày test quy định (2 ngày ngoại dạng, 14 ngày hàm lượng) mà chưa có kết quả thì cảnh báo.
- **Liên kết:** Lab; SX-KHO-26; khối đổi trả của Thu mua.

### SX-KHO-11 — Lệnh phối BTP

- **Đầu vào:** mã lệnh phối (của NCC và nội bộ), ngày yêu cầu, người yêu cầu, NCC, mã BĐM BTP, số lượng BTP cần phối, đơn vị nhận hóa đơn phối trộn.
- **Đầu ra:** danh sách NL cần xuất; phiếu *Lệnh sản xuất bán thành phẩm*; dòng xuất NL và dòng nhập BTP; chênh lệch.
- **Quy tắc:** lượng NL cần = định mức cho 1.000 lít (kg) × số BTP cần phối / 1.000. Chênh lệch NL = lượng cần − lượng thực xuất. Chênh lệch BTP = số cần phối − số thực phối được. Giá BTP sau phối = giá NL + phí phối + hao hụt NL khi phối + phí khác (thuộc phần Giá vốn).
- **Ràng buộc:** không gửi lệnh khi NL chưa đủ tồn thực tế tại kho NCC phối; BTP thực phối lệch quá sai số thì chặn tự nhập, chờ QLSX quyết.
- **Liên kết:** BĐM BTP (SX-SP), Giá vốn (giá BTP), Công nợ (phí phối), SX-KHO-21.

### SX-KHO-12 — Nhập khác: đổ thu, dư sau sản xuất, cho tặng

- **Đầu vào:** phân loại, kho, thương hiệu, mã, lượng, đơn TP hoặc LSX liên quan, lý do.
- **Đầu ra:** tồn thực tế tăng.
- **Quy tắc:** dư sau sản xuất phía thuế cần NCC xuất bán lại và phiếu nhập kèm LSX. Hàng cho tặng nhập với giá 0 hay giá ước tính cần chốt.
- **Ràng buộc:** quy trình nguồn ghi *sẽ xây dựng sau*, nên trước mắt chỉ cần loại giao dịch và trường liên kết đơn.
- **Liên kết:** SX-KHO-18 (số dư = đã xuất − đã dùng theo định mức).

### SX-KHO-13 — Nhập, chuyển, trả thành phẩm

- **Đầu vào:** ngày, số phiếu, mã đơn, loại đơn (hàng mới / hàng xử lý), thương hiệu, kho xuất, kho nhận, trạng thái (1 đến 7), mã hàng, tên pháp lý, SL sản phẩm trên thùng, SL thùng, SL lẻ, mã lô, số hóa đơn, NSX, HSD, kết quả Lab, biển số, tài xế; kết quả KCS của kho nhận.
- **Đầu ra:** tồn TP theo kho; phiếu đề nghị nhập kho TP; số TP đã nhận của đơn.
- **Quy tắc:** tổng TP = SL thùng × SL trên thùng + SL lẻ; HSD = NSX + 2 năm; kho đã KCS đạt thì lỗi phát sinh do bảo quản về sau kho tự chịu.
- **Ràng buộc:** SL thực nhận khác SL yêu cầu phải có nguyên nhân; SL không đạt tự sang kho lỗi và mở sự cố.
- **Liên kết:** Đơn hàng gia công, Sự cố, SX-KHO-18, 37.

### SX-KHO-14 — Duyệt đủ vật tư cho đơn TP

- **Đầu vào:** đơn TP; BĐM; tồn có thể sản xuất tại kho NCC GC của đơn.
- **Đầu ra:** trả về đơn: trạng thái duyệt, ngày đủ nội bộ, ngày đủ thuế, ngày duyệt, mã BĐM nội bộ, mã BĐM thuế, cấu thành (bên mình, khách hàng, NCC), ghi chú.
- **Quy tắc:** VTBB: *Đủ VTBB* kèm số tồn thực. NL / BTP: một trong *Đủ tồn*, *Chuyển kho*, *Mua*, *Tồn NCC*, *Chờ phối BTP*. Đủ ở kho khác thì đề xuất chuyển kho; đủ ở thương hiệu khác thì đề xuất xuất bán nội bộ.
- **Ràng buộc:** đơn chỉ được coi là đủ điều kiện khi cả hai nhóm (VTBB và NL / BTP) đã duyệt.
- **Liên kết:** Đơn hàng gia công (luồng duyệt nhiều bộ phận), SX-KHO-17, 22, 23.

### SX-KHO-15 — Xuất VTBB theo đơn TP và BĐM

- **Đầu vào:** mã đơn TP, mã BĐM VTBB, kho xuất, phân loại; số ĐP VTBB chốt.
- **Đầu ra:** các dòng xuất theo từng VTBB của BĐM.
- **Quy tắc:**
  - Số lượng đặt NCC = số KD đặt + số mẫu Lab.
  - `Tổng VTBB cần xuất = Định mức trên 1 thành phẩm × Số lượng đặt NCC`.
  - Định mức thùng và nhãn thùng = 1 / số thành phẩm trong một thùng (ví dụ 1 / 40 = 0,025).
  - `VTBB xuất thực tế lần i = Định mức × Số TP có hàng lần i`.
  - `VTBB đang xuất tạm = (Số lượng đặt NCC − Tổng TP đã sản xuất) × Định mức`.
- **Trường chính:** phân loại, kho, mã đơn, NCC, ngày yêu cầu, thương hiệu, mã hàng, tên pháp lý, ĐVT, SL KD đặt, SL đặt NCC, mã BĐM, nhóm VTBB, mã VTBB, định mức, tổng cần xuất, số chốt, ngày và SL TP ba lần, SL VTBB xuất ba lần, SL đang xuất tạm, ngày duyệt BĐM, kết quả khớp BĐM, ảnh chứng từ.
- **Ràng buộc:** dòng xuất phải khớp một dòng của BĐM đã duyệt; BĐM chưa duyệt thì cảnh báo; không vượt tồn (SX-KHO-19).
- **Liên kết:** định mức bao bì của ERP (`tab_packaging_bom`, `tab_packaging_bom_part`) cần mở rộng cho đủ nhóm VTBB; SX-KHO-17, 18.

### SX-KHO-16 — Xuất BTP theo đơn TP

- **Đầu vào:** mã kho xuất, mã đơn; quy cách (tra từ danh mục nhãn mác theo mã hàng); tỷ trọng; quy cách thực tế (nếu có); số lô BTP.
- **Đầu ra:** nhu cầu BTP của đơn (kg / lít); lượng trừ thực tế; lượng xuất tạm.
- **Quy tắc:**
  - Số lượng gửi NCC = số thành phẩm (gồm khuyến mãi) + 1.
  - `Tổng theo đơn vị nhỏ = Quy cách × Số lượng gửi NCC`.
  - `Nhu cầu BTP (kg / lít) = (Tổng theo đơn vị nhỏ / 1.000 nếu đơn vị là ml hoặc gam; giữ nguyên nếu là lít hoặc kg) × Tỷ trọng`.
  - `Lượng trừ thực tế = Tổng TP sẵn kho tại NCC × Quy cách thực tế (hoặc quy cách nhãn)`, đổi về kg / lít.
  - `Lượng xuất tạm = (Số lượng gửi NCC − Tổng TP sẵn kho) × Quy cách`, đổi về kg / lít.
- **Ràng buộc:** dòng *BTP NCC - không tồn kho* không trừ tồn của DEGO; đơn hủy thì số lượng về 0.
- **Liên kết:** SX-KHO-30 (xuất theo lô, ưu tiên lô hết hạn trước), SX-KHO-34.

### SX-KHO-17 — Xuất tạm và giữ hàng cho đơn

- **Đầu vào:** đơn TP đã duyệt đủ vật tư.
- **Đầu ra:** lượng giữ theo đơn; tồn có thể sản xuất giảm; tồn thực tế chưa đổi.
- **Quy tắc:** vòng đời dòng xuất theo đơn: *Chưa xuất* (đang chờ, thiếu) → *Xuất SX tạm* (đã giữ, chưa chốt số) → *Xuất sản xuất* (đã trừ thực tế theo từng lần có TP) → *Xuất hoàn thành* (đơn xong) hoặc *Hủy đơn*. Cân đối: `Còn thiếu = Tồn − Xuất tạm − Đơn chờ xuất`; âm nghĩa là thiếu hàng.
- **Trường chính:** đơn, mã, kho, thương hiệu, số giữ, số đã trừ thực tế, số còn giữ, trạng thái.
- **Ràng buộc:** không giữ quá tồn có thể sản xuất, trừ khi người duyệt chấp nhận *đơn chờ xuất*.
- **Liên kết:** SX-KHO-14, 18, 20, 29.

### SX-KHO-18 — Ghi nhận xuất theo lần NCC có thành phẩm

- **Đầu vào:** đơn TP; từng lần: ngày TP sẵn kho tại NCC, số TP.
- **Đầu ra:** tự sinh dòng xuất thực tế VTBB và BTP của lần đó; giảm số giữ.
- **Quy tắc:** thời điểm ghi xuất nội bộ = ngày NCC có TP. Tổng TP đã sản xuất = tổng các lần. So với số đặt NCC: nhỏ hơn thì *chưa sản xuất hết*, bằng thì *đủ*, lớn hơn thì *vượt đơn*.
- **Ràng buộc:** sổ hiện giới hạn 3 lần; ERP nên cho số lần tùy ý. Phiếu xuất phải có ngày không sau ngày LSX.
- **Liên kết:** SX-KHO-13 (nhập TP), SX-KHO-25 (dùng thực tế vượt định mức là hao hụt).

### SX-KHO-19 — Cảnh báo và chặn xuất âm kho

- **Đầu vào:** mọi phiếu xuất, chuyển, giữ hàng.
- **Đầu ra:** thông báo ngay trên phiếu; danh sách khóa tồn đang âm kèm giao dịch cuối và phiếu gốc.
- **Quy tắc:** kiểm trên đúng khóa kho + thương hiệu + mã và đúng nhóm tồn. Sổ hiện tại chỉ **cảnh báo** (tô đỏ, ghi *Tồn âm* với số thực tế, tạm, lỗi) và chỉ cách dò: xem sheet giao dịch cuối, ngày giao dịch cuối rồi sửa.
- **Ràng buộc:** cần chốt chặn cứng hay chỉ cảnh báo (câu hỏi 6). Đề xuất: chặn cứng với xuất thực tế; cho phép âm có lý do với giữ hàng.
- **Liên kết:** SX-KHO-29, 36.

### SX-KHO-20 — Hủy đơn và hoàn giữ hàng

- **Đầu vào:** đơn TP bị KD hủy, hoặc giảm số lượng.
- **Đầu ra:** số giữ về 0 hoặc giảm theo; dòng chuyển trạng thái *Hủy đơn*.
- **Quy tắc:** phần đã trừ thực tế không hoàn tự động; phần BTP đã phối dư ở lại tồn (có ghi chú đơn gốc).
- **Ràng buộc:** hủy sau khi NCC đã sản xuất một phần phải ghi rõ số đã làm.
- **Liên kết:** Đơn hàng gia công.

### SX-KHO-21 — Xuất ngoài sản xuất

- **Đầu vào:** ngày xuất, phân loại, kho, thương hiệu, mã, lượng, số hóa đơn, ghi chú, ảnh phiếu xuất, mã số phiếu; NL / BTP thêm: số phiếu yêu cầu, mã lệnh phối, lô, NSX, HSD, số CAS, giá, thành tiền, mã yêu cầu dự trù KD, nhân sự yêu cầu, nhân sự làm việc với NCC, lý do gửi NCC, tài xế, số xe, trạng thái chứng từ, trạng thái xử lý.
- **Đầu ra:** dòng xuất; phiếu đề nghị xuất kho.
- **Quy tắc:** lượng xuất gam / ml = lượng kg / lít × 1.000; thành tiền = lượng × giá.
- **Ràng buộc:** bắt buộc lý do; xuất mẫu thử phải có nơi nhận (Lab, khách, NCC); không vượt tồn.
- **Liên kết:** SX-KHO-11, 22, 23, 24, 25, 28.

### SX-KHO-22 — Chuyển kho

- **Đầu vào:** người đề nghị, bộ phận, kho xuất, kho nhập, lý do, đơn liên quan; dòng hàng: mã, SL yêu cầu, SL thực xuất, SL thực nhận, đơn giá; phương án vận chuyển, tài xế, số xe; bản chụp phiếu ký hai bên.
- **Đầu ra:** một dòng *Xuất chuyển kho* và một dòng *Nhập chuyển kho*; phiếu in.
- **Quy tắc:** chuyển kho không tính vào giá trị nhập, xuất; giữ nguyên thương hiệu, lô, đơn giá. Trạng thái: *Chốt chuyển kho, chờ vận chuyển* → *Đang vận chuyển* → *Hoàn thành*. Trong lúc đang vận chuyển, hàng đã rời kho đi nhưng chưa vào kho đến.
- **Ràng buộc:** SL thực nhận khác SL thực xuất phải ghi chênh lệch và nguyên nhân; khác pháp nhân thì không dùng phiếu chuyển kho mà dùng xuất bán nội bộ.
- **Liên kết:** SX-KHO-23, Đặt xe (xe công ty), Thu mua (thuê ngoài).

### SX-KHO-23 — Xuất bán nội bộ và yêu cầu xuất hóa đơn

- **Đầu vào:** bên bán, bên mua (pháp nhân hoặc thương hiệu), kho xuất, kho nhận, dòng hàng (ngày yêu cầu, mã, SL, đơn giá, thành tiền); với hóa đơn: tên khách hàng, tên pháp lý sản phẩm, thuế suất, hình thức thanh toán, email nhận hóa đơn, công ty xuất hóa đơn, lý do, mã nội bộ.
- **Đầu ra:** tồn chuyển từ thương hiệu bán sang thương hiệu mua; phiếu in; yêu cầu gửi kế toán.
- **Quy tắc:** bán giữa thương hiệu có thể **chỉ chuyển số liệu**, hàng không rời kho. Trước khi lập phải kiểm tồn ở cả Misa nội bộ và Misa thuế.
- **Ràng buộc:** đơn giá bán nội bộ do kế toán cân đối; thiếu tồn thuế thì phải có phương án chứng từ trước.
- **Liên kết:** Công nợ nội bộ, Giá vốn, SX-KHO-35.

### SX-KHO-24 — Đưa vào chi phí

- **Đầu vào:** người đề xuất, bộ phận, nguyên nhân, thời gian; dòng hàng: tên, mã, ĐVT, số lượng, đơn giá, thành tiền; khoản mục chi phí; công ty / thương hiệu chịu.
- **Đầu ra:** phiếu *Đề nghị đưa vào chi phí*; dòng xuất tương ứng; khoản chi phí cho kế toán.
- **Quy tắc:** dùng cho hao hụt trong hạn mức, chênh lệch đóng tối ưu thể tích, hàng xuất cho bộ phận khác. Danh mục khoản mục chi phí lấy từ Misa.
- **Ràng buộc:** phải có người duyệt (QLSX; KD nếu thương hiệu chịu).
- **Liên kết:** SX-KHO-25, Giá vốn, kế toán.

### SX-KHO-25 — Hao hụt, đổ bỏ, xuất hủy

- **Đầu vào:** nguồn phát hiện (đối chiếu, sản xuất thực tế, sự cố); kho, mã, lô, số lượng; nguyên nhân; hình ảnh, biên bản.
- **Đầu ra:** dòng *Xuất hao hụt / đổ bỏ*; kết luận trong hay vượt hạn mức; phiếu đưa vào chi phí hoặc yêu cầu NCC bồi thường; biên bản tiêu hủy.
- **Quy tắc:** `Tỷ lệ hao hụt thực tế = Số lượng hao hụt / Số lượng nhập × 100%` (sổ VTBB) so với % cho phép của NCC. Trong hạn mức: DEGO chịu, đưa vào chi phí. Vượt: NCC đền hàng hoặc đền tiền (cấn trừ công nợ).
- **Ràng buộc:** xuất hủy bắt buộc có biên bản tiêu hủy; VTBB in thương hiệu phải hủy có biên bản.
- **Liên kết:** SX-KHO-06, 39, 43, 48; Công nợ (khoản thu NCC).

### SX-KHO-26 — Kho lỗi và chuyển trạng thái hàng lỗi

- **Đầu vào:** ngày, mã sự cố, mã hàng, NCC GC, kho xuất, kho nhập, số lượng, trạng thái từ, trạng thái đến, mã yêu cầu xử lý lại, diễn giải.
- **Đầu ra:** tồn lỗi theo kho lỗi và theo trạng thái; giá trị hàng lỗi = số lượng × giá vốn đơn vị.
- **Quy tắc:** dòng ghi nhận sự cố có kho xuất *(Phát sinh)*. Trạng thái: Phát sinh → Chờ phương án → Chờ xử lý lại chính nó / Chờ chuyển thành hàng khác / Chờ tiêu hủy / Chờ đổ thu BTP → Hoàn thành, sử dụng được / Tiêu hủy / Xuất chi phí. `Tồn lỗi = Số phát sinh − Số đã hoàn thành`. `Tỷ lệ thu hồi = SL đạt sau xử lý / SL yêu cầu xử lý`.
- **Ràng buộc:** hàng ở kho lỗi không được tính vào tồn có thể sản xuất; chuyển về kho dùng phải có duyệt.
- **Liên kết:** phần Sự cố; SX-KHO-10, 25.

### SX-KHO-27 — Mẫu cho tặng không quản tồn

- **Đầu vào:** ngày tiếp nhận, bộ phận yêu cầu, mục đích, đơn vị cho tặng và người liên hệ, mã và tên vật tư theo NCC, chất liệu, hình dạng, thông số, màu, ĐVT, số lượng, lưu ý, thời gian và cách nhận, người phụ trách, việc cần làm (test, chụp, lưu, gửi), tiến độ, kết quả, trạng thái, đánh giá, liên kết hình.
- **Đầu ra:** sổ tham khảo để đề xuất phương án vật tư thay thế.
- **Quy tắc:** mẫu cho tặng **không dùng cho sản xuất, không xuất chi phí, không quản tồn thực**.
- **Liên kết:** khảo sát VTBB phù hợp công nghệ NCC GC.

### SX-KHO-28 — Bộ phiếu in kho

- **Đầu vào:** dữ liệu từ phiếu kho tương ứng.
- **Đầu ra:** bản in: Phiếu đề nghị xuất kho; Phiếu đề nghị nhập kho; Phiếu đề nghị chuyển kho; Phiếu đề nghị xuất bán hàng nội bộ; Phiếu yêu cầu xuất hóa đơn; Phiếu đề nghị đưa vào chi phí; Giấy đề nghị nhập kho thành phẩm; Lệnh sản xuất BTP.
- **Quy tắc:** đầu phiếu ghi pháp nhân (chọn từ danh mục công ty), số phiếu, ngày; dòng hàng có SL yêu cầu và SL thực; tổng tiền bằng chữ; ô ký: Trưởng bộ phận, Người lập, Kế toán (phiếu nhập TP thêm *Duyệt đủ VTBB*, *Duyệt đủ NL*).
- **Ràng buộc:** phiếu phải gửi P TCKT trong ngày phát sinh.
- **Liên kết:** khung in chứng từ sẵn có của ERP.

### SX-KHO-29 — Tồn tức thời ba nhóm

- **Đầu vào:** sổ giao dịch.
- **Đầu ra:** mỗi khóa kho × thương hiệu × mã một dòng: đầu kỳ (dùng được, lỗi); tổng nhập (thực tế, tạm, lỗi); tổng xuất (thực tế, tạm, lỗi); tồn tạm, tồn thực tế / có thể sản xuất, tồn lỗi; ngày nhập cuối, ngày xuất cuối, ngày giao dịch cuối, nguồn giao dịch cuối; cảnh báo; Min, MOQ, trạng thái; số ngày tồn; giá trị tồn. Dòng tổng theo bộ lọc.
- **Quy tắc (sổ NL / BTP, có công thức rõ):**
  - `Tổng nhập = Nhập thực tế + Nhập tạm + Nhập lỗi`.
  - `Tổng xuất = Xuất thực tế + Xuất tạm + Xuất lỗi`.
  - `Tồn thực tế = Đầu kỳ + Nhập thực tế − Xuất thực tế`.
  - `Tồn lỗi = Đầu kỳ lỗi + Nhập lỗi − Xuất lỗi`.
  - Cột *Tồn (Tạm)* đang tính `Đầu kỳ + Tổng nhập − Tổng xuất`, tức tồn sau khi trừ hết cả phần tạm và lỗi.
  - Xuất tạm gồm *Xuất tạm* ở sổ ngoài sản xuất cộng lượng *Xuất SX tạm* ở sổ theo đơn.
- **Ràng buộc:** định nghĩa *tồn có thể sản xuất* phải chốt một công thức (câu hỏi 3).
- **Liên kết:** mọi tính năng khác.

### SX-KHO-30 — Tồn chi tiết theo lô

- **Đầu vào:** dòng nhập theo lô; dòng xuất có chọn lô.
- **Đầu ra:** theo kho × thương hiệu × mã × lô: ngày nhập, phân loại nhập, số lô, NSX, HSD, nhập, xuất, tồn, đơn giá, giá trị tồn, trạng thái (*Sử dụng được / Không sử dụng được*), đơn hàng đang treo, tổng lượng đang treo, ngày xuất cuối, mã đơn đóng gần nhất, cảnh báo số ngày không giao dịch, Min.
- **Quy tắc:** giá trị tồn = tồn × đơn giá; ưu tiên xuất lô hết hạn trước (nguồn chưa viết thành luật, là đề xuất).
- **Ràng buộc:** lô hết hạn hoặc *Không sử dụng được* không cho xuất sản xuất.
- **Liên kết:** SX-KHO-09, 16, 50.

### SX-KHO-31 — Sổ giao dịch kho

- **Đầu vào:** mọi phiếu kho đã ghi sổ.
- **Đầu ra:** bảng: ngày giao dịch, nguồn (loại phiếu), chiều, phân loại, kho, thương hiệu, mã, tên, ĐVT, số lượng; mở được phiếu gốc.
- **Quy tắc:** là sổ cái của kho, chỉ ghi thêm; sửa sai bằng dòng đảo, không sửa đè.
- **Ràng buộc:** không cho xóa dòng đã ghi sổ của kỳ đã chốt.
- **Liên kết:** SX-KHO-32, 44, 45.

### SX-KHO-32 — Tồn theo kỳ

- **Đầu vào:** từ ngày, đến ngày; bộ lọc kho, thương hiệu, mã, NCC.
- **Đầu ra:** tồn đầu kỳ, nhập, xuất, tồn cuối kỳ theo ba nhóm; bảng chi tiết từng giao dịch kèm tồn lũy kế sau giao dịch và cảnh báo âm; số giao dịch trong kỳ.
- **Quy tắc:** giao dịch trước *từ ngày* gộp thành đầu kỳ (thực tế và lỗi).
- **Liên kết:** SX-KHO-45; đối chiếu NCC theo kỳ.

### SX-KHO-33 — Giá trị tồn và đơn giá bình quân

- **Đầu vào:** đơn giá trên dòng nhập; đơn giá đầu kỳ.
- **Đầu ra:** đơn giá theo từng nhóm (đầu kỳ, nhập thực tế, nhập tạm, nhập lỗi, xuất, tồn); giá trị tồn; sổ tổng hợp tồn kho có giá để đối chiếu kế toán.
- **Quy tắc:** sổ NL / BTP: `Đơn giá bình quân gia quyền của nhóm = Tổng thành tiền các dòng của nhóm / Tổng số lượng của nhóm`; đơn giá xuất lấy bằng đơn giá nhập thực tế bình quân; đơn giá đầu kỳ chung = Σ(số lượng × đơn giá) / Σ số lượng. Sổ VTBB: mục lục ghi *trung bình cộng giá các lần nhập*; báo cáo VTBB lại dùng giá Min / Max của danh mục. ERP: `value = Σ(qty × unit_price)`, `avg_cost = value / qty` trên toàn bộ sổ của khóa.
- **Ràng buộc:** phải chốt một phương pháp và chốt giá trước hay sau VAT (câu hỏi 4, 5).
- **Liên kết:** Giá vốn, chi phí thu mua phân bổ vào giá của ERP.

### SX-KHO-34 — Hai góc nhìn tồn SX và KD

- **Đầu vào:** quy cách thực tế theo SX và theo KD trên dòng xuất theo đơn.
- **Đầu ra:** hai bộ số trừ thực tế và xuất tạm; hai sổ tồn (chi tiết và tổng) cho SX và cho KD.
- **Quy tắc:** cùng công thức SX-KHO-16, chỉ khác quy cách đem nhân. Chênh giữa hai sổ là phần đóng tối ưu thể tích.
- **Ràng buộc:** nếu giữ hai sổ thì chỉ một sổ là sổ gốc để đối chiếu với NCC (đề xuất: sổ SX).
- **Liên kết:** SX-KHO-24 (chênh lệch đưa vào chi phí KD).

### SX-KHO-35 — Tồn nội bộ và tồn thuế

- **Đầu vào:** giao dịch nội bộ (theo thương hiệu) và giao dịch thuế (theo pháp nhân, theo hóa đơn).
- **Đầu ra:** hai số tồn cho cùng mã + kho; cột *đủ nội bộ*, *đủ thuế* khi duyệt đơn.
- **Quy tắc:** phía thuế tồn chỉ đổi khi có hóa đơn (mua, bán nội bộ, NCC xuất trả); cùng công ty chuyển kho thì thuế không xử lý. Mục tiêu dài hạn nguồn ghi: sau khi đồng bộ mã thuế và mã nội bộ thì BĐM chỉ còn một bảng.
- **Ràng buộc:** quyết định phạm vi: ERP giữ cả hai sổ, hay chỉ sổ nội bộ và nhận số thuế từ Misa (câu hỏi 1).
- **Liên kết:** SX-KHO-23, kế toán, Misa.

### SX-KHO-36 — Cảnh báo tồn

- **Đầu vào:** sổ tồn; Min, MOQ; ngưỡng ngày.
- **Đầu ra:** nhãn trên dòng tồn và danh sách cảnh báo.
- **Quy tắc:**
  - *Tồn âm*: tồn thực tế nhỏ hơn 0 (tô đỏ).
  - *Dưới mức an toàn*: tồn nhỏ hơn Min (tô vàng). *Dưới MOQ*: tô cam.
  - *Không giao dịch quá 30 ngày*: sổ VTBB tính từ ngày giao dịch cuối; sổ NL / BTP ghi *Không giao dịch n ngày* tính từ ngày nhập cuối khi chưa từng xuất, hoặc *Giao dịch lần cuối n ngày* tính từ ngày xuất cuối.
  - Sổ NL / BTP dùng ngưỡng cứng: tồn trên 500 *An toàn*; từ 200 đến 500 *Theo dõi*; dưới 200 *Cần nhập hàng* (chung cho mọi đơn vị tính, cần thay bằng Min theo mã).
- **Liên kết:** SX-KHO-05, 46, 47; thông báo của ERP.

### SX-KHO-37 — Tồn thành phẩm tại NCC GC

- **Đầu vào:** sổ nhập, chuyển, trả TP.
- **Đầu ra:** theo NCC × mã hàng × NSX: tổng tồn, số ngày tồn tại NCC, HSD còn lại.
- **Quy tắc:** `Tổng tồn = Nhập TP + Nhập mẫu + Nhập dư − Chuyển kho + Trả hàng − Xuất xử lý + Nhập sau xử lý`; `Số ngày tồn = Hôm nay − Ngày nhập`.
- **Ràng buộc:** tồn quá số ngày lưu kho miễn phí của NCC thì cảnh báo phát sinh phí.
- **Liên kết:** SX-KHO-13, 43.

### SX-KHO-38 — Nạp số liệu tồn NCC GC gửi

- **Đầu vào:** ngày báo cáo, NCC, kho, mã và tên vật tư theo NCC, ĐVT, số giao nhận trong kỳ theo NCC (không bắt buộc), tồn cuối kỳ theo NCC, ghi chú (số biên bản, email); tệp đính kèm gốc.
- **Đầu ra:** bản ghi kỳ đối chiếu, sẵn sàng so.
- **Quy tắc:** mỗi NCC có mẫu báo cáo riêng, nên cần bước ghép cột khi nạp; mã NCC đổi sang mã DEGO qua SX-KHO-04.
- **Ràng buộc:** thiếu kho thì không so được (một mã có thể nằm ở nhiều kho).
- **Liên kết:** SX-KHO-39.

### SX-KHO-39 — Đối chiếu tự động với NCC GC

- **Đầu vào:** bản ghi kỳ của NCC; sổ tồn và sổ giao dịch của mình tại ngày báo cáo; dung sai.
- **Đầu ra:** từng dòng: giao dịch theo NCC (G), theo hệ thống (H), lệch số lượng, tồn theo NCC (J), tồn theo hệ thống (K), lệch tồn, kết luận; bảng tổng hợp bốn nhóm VTBB, BTP, TP, hàng lỗi.
- **Quy tắc:** `Lệch số lượng = H − G`; `Lệch tồn = K − J` (dương là sổ mình nhiều hơn NCC báo). Kết luận: *Khớp* (lệch trong dung sai); *Lệch*; *Không tìm thấy Mã + Kho*; *Thiếu Kho*. Dung sai = % hao hụt cho phép của NCC.
- **Ràng buộc:** so với **tồn thực tế** (không gồm phần giữ cho đơn); chỉ tính trên đúng kho của NCC đó; mã có ở sổ mình mà NCC không báo cũng phải hiện ra.
- **Liên kết:** SX-KHO-25, 40, 42.

### SX-KHO-40 — Lịch sử đối chiếu và xử lý chênh lệch

- **Đầu vào:** kết quả kỳ; hướng điều chỉnh với NCC GC; nguyên nhân, ghi chú; trạng thái xử lý chênh lệch; người xử lý, hạn.
- **Đầu ra:** hồ sơ theo kỳ; danh sách chênh lệch còn mở.
- **Quy tắc:** mỗi dòng lệch phải đóng bằng một trong: sửa sổ mình (phiếu điều chỉnh), NCC sửa sổ, ghi hao hụt, NCC bồi thường.
- **Ràng buộc:** nguồn ghi rõ phần này *chưa theo dõi xử lý sau đối chiếu* — là khoảng trống cần ERP lấp.
- **Liên kết:** SX-KHO-25, đánh giá định kỳ NCC GC (tiêu chí đối chiếu tồn).

### SX-KHO-41 — So sánh các lần NCC gửi

- **Đầu vào:** hai kỳ báo cáo liên tiếp của cùng NCC.
- **Đầu ra:** theo mã: tồn cuối và dư cuối lần gần nhất, lần trước, chênh lệch; ngày kiểm tồn tại NCC; số lần gửi.
- **Quy tắc:** `Chênh lệch tồn cuối = Lần gần nhất − Lần trước`; khác 0 thì tô đỏ để xem có giao dịch giải thích không.
- **Liên kết:** SX-KHO-38.

### SX-KHO-42 — Biên bản xác nhận tồn và giải trình chênh lệch

- **Đầu vào:** kết quả đối chiếu đã duyệt.
- **Đầu ra:** *Biên bản xác nhận tồn kho cuối kỳ* (hai bên ký, mỗi bên một bản); *Biên bản kiểm tra và giải trình chênh lệch* (nội bộ); lưu bản ký.
- **Quy tắc:** QLSX ký theo giấy ủy quyền; biên bản tách theo pháp nhân.
- **Ràng buộc:** mục lục ghi *chưa xác định phiếu in* — cần phòng Sản xuất đưa mẫu.
- **Liên kết:** SX-KHO-44, Công nợ.

### SX-KHO-43 — Phí lưu kho và hao hụt NCC tính

- **Đầu vào:** phía mình: loại (phí lưu kho, hao hụt, chi phí khác), số chứng từ Misa, NCC, ngày ghi nhận, diễn giải, số tiền, số ngày công nợ, hình thức thanh toán, số hóa đơn; phía NCC: ngày chứng từ, số hóa đơn, số tiền.
- **Đầu ra:** bảng đối chiếu: chênh lệch tiền, khớp hóa đơn, tình trạng hạn, trạng thái, nguyên nhân và hướng xử lý.
- **Quy tắc:** `Ngày đến hạn thanh toán = Ngày ghi nhận + Số ngày công nợ`; `Chênh lệch = Số tiền nội bộ − Số tiền NCC`; trạng thái *Khớp hoàn toàn / Lệch số tiền / Thiếu bên NCC*; hạn *Trong hạn / Quá hạn n ngày*. Phí lưu kho thực tế theo chính sách từng NCC (theo pallet mỗi tháng, theo thùng mỗi ngày, hoặc miễn phí), phân bổ về thương hiệu.
- **Ràng buộc:** phí lưu kho không sinh từ ĐMH, cần loại công nợ riêng.
- **Liên kết:** Công nợ, Giá vốn, SX-KHO-06, 37.

### SX-KHO-44 — Chốt kỳ kho

- **Đầu vào:** ngày chốt (cuối tháng).
- **Đầu ra:** ảnh chụp tồn cuối kỳ theo khóa; kỳ bị khóa.
- **Quy tắc:** nguồn chỉ ghi *cuối tháng có thể lưu tệp tồn kho để đối chiếu về sau*; trên ERP nên thành thao tác chốt kỳ: lưu số, chặn thêm / sửa giao dịch có ngày trong kỳ đã chốt, mở lại phải có quyền.
- **Liên kết:** SX-KHO-07, 31, 42.

### SX-KHO-45 — Báo cáo xuất nhập tồn theo kỳ

- **Đầu vào:** kỳ (tháng, quý, năm, khoảng tùy chọn); lọc kho, thương hiệu, loại hàng.
- **Đầu ra:** theo loại hàng, theo thương hiệu, theo kho, theo NCC bán: tồn đầu, nhập, xuất thực tế, hao hụt, nhập lỗi, tồn cuối, tỷ lệ, chi phí lưu kho; so cùng kỳ năm trước; tổng toàn bộ.
- **Quy tắc:** công thức ở mục 6.
- **Liên kết:** SX-KHO-02 (nhóm báo cáo), xuất Excel.

### SX-KHO-46 — Tuổi tồn, tồn lâu, tồn chết

- **Đầu vào:** sổ tồn, ngày nhập cuối, ngày xuất cuối; ngưỡng.
- **Đầu ra:** số ngày tồn; nhóm tuổi; cờ tồn lâu; nhóm luân chuyển; 10 mã tồn lâu giá trị lớn nhất.
- **Quy tắc:** công thức ở mục 6.
- **Ràng buộc:** ngày nhập đầu kỳ làm sai tuổi tồn nếu không có ngày nhập thật.
- **Liên kết:** SX-KHO-07, 49.

### SX-KHO-47 — Đề xuất đặt hàng theo Min, MOQ

- **Đầu vào:** tồn có thể sản xuất; Min, MOQ; số đang đặt chưa về.
- **Đầu ra:** danh sách mã dưới Min kèm số đề xuất đặt; tạo YCMH nháp.
- **Quy tắc:** `Số đề xuất đặt = Làm tròn lên( max(Min − Tồn có thể sản xuất − Số đang đặt chưa về, 0) / MOQ ) × MOQ`; MOQ bằng 0 thì không làm tròn.
- **Liên kết:** Thu mua (YCMH), SX-KHO-05.

### SX-KHO-48 — Báo cáo hao hụt và lỗi nhập

- **Đầu vào:** giao dịch có cờ hao hụt; giao dịch nhập lỗi; định mức hao hụt theo loại hàng và theo NCC GC.
- **Đầu ra:** tỷ lệ và giá trị hao hụt theo loại, theo NCC GC, tô đỏ khi vượt; tỷ lệ lỗi nhập theo NCC bán hàng.
- **Quy tắc:** công thức ở mục 6.
- **Liên kết:** đánh giá NCC, SX-KHO-25.

### SX-KHO-49 — Dashboard kho và kiểm tra dữ liệu

- **Đầu vào:** cấu hình: năm báo cáo, kỳ, % chi phí lưu kho giả định, ngưỡng tồn lâu, ngưỡng vượt nhu cầu, ngưỡng luân chuyển, chế độ đơn giá.
- **Đầu ra:** chỉ số chính; tồn theo loại, thương hiệu, kho; tuổi tồn; top tồn lâu; khối kiểm tra dữ liệu (phân loại chưa khai báo, mã ngoài danh mục, thiếu ngày, chênh giữa dashboard và báo cáo tháng).
- **Quy tắc:** các số kiểm tra phải bằng 0 mới tin báo cáo. Khi dữ liệu đã ở ERP, phần *mã ngoài danh mục* và *phân loại lạ* tự hết nhờ chọn từ danh mục.
- **Liên kết:** tổng quan kho `/inventory` của ERP.

### SX-KHO-50 — Báo cáo NL / BTP và sổ theo dõi vấn đề

- **Đầu vào:** kỳ báo cáo; dữ liệu lô, đơn, QC, hóa đơn, dự trù KD.
- **Đầu ra:** chỉ tiêu: tổng tồn, tổng phí lưu kho, số dòng tồn vượt mức tối đa, số lô sắp hết hạn trong 90 ngày, tỷ lệ đơn đúng tiến độ, tỷ lệ QC đạt, tỷ lệ hao hụt, số dòng thiếu hóa đơn, tỷ lệ đáp ứng dự trù KD, tỷ lệ đơn gấp; sổ vấn đề (mã, ngày phát hiện, nhóm, mã hàng, lô / đơn, mô tả, nguyên nhân, ưu tiên, phương án, người phụ trách, hạn, trạng thái, kết quả).
- **Quy tắc:** nguồn mới có khung và tên chỉ tiêu, chưa có công thức; danh sách báo cáo mong muốn còn gồm công suất phối BTP theo NCC, tồn hóa đơn theo số CAS.
- **Liên kết:** SX-KHO-30, 36; phần Công việc của ERP có thể thay sổ vấn đề.

---

## 6. Báo cáo và chỉ số kho

Nguồn công thức chủ yếu là tệp *BC VTBB* (báo cáo tự tính, người dùng chỉ cập nhật bốn sheet: giao dịch, danh mục, Min MOQ, cấu hình) và các cột công thức ở sổ tồn NL / BTP. Các ngưỡng dưới đây là ô cấu hình, không phải hằng số cứng.

### 6.1. Tồn theo kỳ

| Chỉ số | Công thức | Ghi chú |
|---|---|---|
| Tồn cuối kỳ | `Tồn đầu kỳ + Nhập trong kỳ − Xuất trong kỳ` | Tính riêng cho ba nhóm thực tế, tạm, lỗi |
| Tồn có thể sản xuất (báo cáo VTBB) | `Tồn thực tế + Tồn tạm` | Tồn tạm âm nghĩa là đã xuất giữ cho đơn chưa sản xuất |
| Giá trị nhập, giá trị xuất của kỳ | `Σ Số lượng × Đơn giá dùng` của các giao dịch thuộc nhóm báo cáo *Nhập*, *Xuất* | *Đầu kỳ* và *Chuyển kho* không tính |
| Giá trị tồn | `Tồn × Đơn giá dùng` | Mã chưa có giá thì giá trị 0 và được đếm riêng (chỉ số *thiếu đơn giá*) |
| Đơn giá dùng (báo cáo VTBB) | Đơn giá nhập tay nếu lớn hơn 0; nếu không thì theo chế độ: giá Min, giá Max, hoặc `(Min + Max) / 2` | Trên ERP nên thay bằng đơn giá bình quân của sổ kho |

Các chiều xem: loại hàng (10 loại VTBB suy từ ba ký tự đầu của mã, ghi đè được theo từng mã), thương hiệu, kho, NCC bán hàng, tháng, quý, năm, khoảng ngày tùy chọn, so cùng kỳ năm trước.

### 6.2. Tồn lâu, tồn chết, luân chuyển

| Chỉ số | Công thức | Ngưỡng mặc định |
|---|---|---|
| Số ngày tồn | `Ngày báo cáo − Ngày nhập cuối` (khi tồn lớn hơn 0) | — |
| Tồn lâu | Số ngày tồn lớn hơn ngưỡng của loại hàng | 90 ngày; mỗi loại có thể đặt ngưỡng riêng |
| Nhóm luân chuyển | Theo số ngày kể từ lần xuất cuối: *Nhanh*, *Chậm*, *Tồn chết* | Đến 30 ngày; đến 90 ngày; quá 90 ngày hoặc chưa từng xuất |
| Tuổi tồn | Chia giá trị tồn theo 5 khoảng | 0–30, 31–60, 61–90, 91–180, trên 180 ngày |
| Xuất bình quân ngày | `Xuất thực tế 90 ngày gần nhất / 90` | — |
| Số ngày đủ dùng | `Tồn có thể sản xuất / Xuất bình quân ngày` | — |
| Vượt nhu cầu | Số ngày đủ dùng lớn hơn ngưỡng | 180 ngày |
| Số ngày tồn kho bình quân (DIO) | Theo loại hàng | — |
| Không giao dịch | `Hôm nay − Ngày giao dịch cuối` lớn hơn ngưỡng | 30 ngày (sổ tồn VTBB) |
| Tồn thành phẩm tại NCC | `Hôm nay − Ngày nhập` | So với số ngày lưu kho miễn phí của NCC |
| Tuổi tồn hàng lỗi | `Ngày báo cáo − Ngày ghi nhận sự cố`; nhóm 0–30, 31–60, 61–90, trên 90 ngày | Theo dõi % giá trị tồn lỗi trên 60 ngày |

### 6.3. Min, MOQ và số đề xuất đặt

- Dưới Min: `Tồn có thể sản xuất < Min`.
- `Số đề xuất đặt = Làm tròn lên( max(Min − Tồn có thể sản xuất − Số đang đặt chưa về, 0) / MOQ ) × MOQ`. MOQ bằng 0 thì lấy đúng phần thiếu.
- Ví dụ: Min 500, tồn có thể sản xuất 120, đang đặt 0, MOQ 1.000 thì đề xuất 1.000. Min 5.000, tồn 1.200, đang đặt 1.000, MOQ 1.500 thì thiếu 2.800, đề xuất 3.000.
- Sổ NL / BTP hiện dùng ba mức cứng 500 / 200 cho mọi mã; cần chuyển sang Min theo mã + kho.

### 6.4. Hao hụt so với định mức

| Chỉ số | Công thức | Nguồn |
|---|---|---|
| Tỷ lệ hao hụt theo số lượng | `Số lượng hao hụt / Số lượng nhập × 100%` | Sổ tồn VTBB (khối % hao hụt theo NCC GC) |
| Tỷ lệ hao hụt theo giá trị | `Giá trị hao hụt / Giá trị xuất thực tế` | Báo cáo VTBB theo loại hàng |
| Định mức hao hụt theo loại VTBB | Thùng 2%, nhãn 3%, túi 3%, hộp 2%, chai 1%, nắp 1%, khay 2%, băng keo 2%, bao bì in khác 3%, khác 2% | Báo cáo VTBB › cấu hình |
| Định mức hao hụt theo NCC GC | Theo hợp đồng từng NCC (có NCC ghi *theo thực tế*) | Danh mục NCC GC |
| Vượt định mức | Tỷ lệ thực tế lớn hơn định mức thì tô đỏ, nêu tên NCC | Căn cứ yêu cầu NCC bồi thường |
| Chênh lệch khi phối BTP | `Lượng NL cần theo định mức − Lượng NL thực xuất`; `BTP cần phối − BTP thực phối` | Danh sách phối BTP |
| Quyết toán vật tư với NCC GC | `Đã xuất − Đã dùng theo định mức − Tồn thực tế` | Quy trình ngưng hợp tác NCC |
| Tỷ lệ lỗi nhập | `Giá trị nhập lỗi / Giá trị tổng nhập`, theo NCC bán hàng | Báo cáo VTBB |
| Tỷ lệ thu hồi sau xử lý lại | `Số lượng đạt sau xử lý / Số lượng yêu cầu xử lý` | Yêu cầu xử lý lại |

Hai công thức tỷ lệ hao hụt dùng **mẫu số khác nhau** (số lượng nhập và giá trị xuất); phải chốt một cách (câu hỏi 8).

### 6.5. Đối chiếu NCC GC

- `Lệch số lượng giao dịch = Giao dịch theo hệ thống − Giao dịch theo NCC`.
- `Lệch tồn = Tồn theo hệ thống − Tồn NCC báo`.
- Chỉ số theo dõi đề xuất: số dòng khớp / tổng số dòng theo NCC và theo kỳ; giá trị chênh lệch còn mở; số ngày từ khi phát hiện đến khi đóng chênh lệch; số lần NCC gửi báo cáo trong kỳ. Kết quả này là đầu vào tiêu chí *đối chiếu công nợ / tồn* trong đánh giá định kỳ NCC GC.

### 6.6. Giá trị tồn có giá và chi phí lưu kho

- Sổ tổng hợp tồn kho có giá: số lượng và giá trị theo đầu kỳ, nhập, xuất, tồn, *tương tự báo cáo tồn kho trên phần mềm kế toán*, phục vụ giá vốn và đối chiếu kế toán.
- Đơn giá bình quân gia quyền: `Σ Thành tiền nhập / Σ Số lượng nhập` theo khóa kho × thương hiệu × mã.
- Chi phí lưu kho **ước tính** (báo cáo VTBB): `Chi phí một tháng = Giá trị tồn × % chi phí lưu kho` (mặc định 1,5%); `Lũy kế = Giá trị tồn × % × Số ngày tồn / 30`.
- Chi phí lưu kho **thực tế**: theo bảng kê của NCC (đơn giá × số pallet, m² hoặc thùng × thời gian), đối chiếu cuối tháng theo biên bản tồn, phân bổ về thương hiệu.

### 6.7. Chỉ số theo đơn

- `Số TP chưa sản xuất = Số đặt NCC − Tổng TP đã có hàng`.
- `Vật tư đang giữ cho đơn = Số TP chưa sản xuất × Định mức`.
- `Còn thiếu = Tồn − Xuất tạm − Đơn chờ xuất`.
- Số ngày từ lúc đơn duyệt đến *ngày đủ VTBB*, *ngày đủ NL / BTP* (nội bộ và thuế).

---

## 7. Dữ liệu chính

Cột **ERP** ghi bảng hiện có nếu dùng lại được.

### 7.1. Kho

| Trường | Ghi chú | ERP |
|---|---|---|
| Mã kho, tên viết tắt, tên đầy đủ, địa chỉ, đang dùng | Mã trùng mã kho Misa | `tab_warehouse` (`code`, `name`, `address`, `is_active`) |
| Loại kho | DEGO; tại NCC GC; kho lỗi; thương mại; ảo | Chưa |
| NCC GC | Kho đặt tại NCC nào | Chưa |
| Kho lỗi đi cặp | Trỏ tới kho lỗi của cùng địa điểm | Chưa |
| Loại hàng chứa | NL, BTP, VTBB, TP | Chưa |
| Thông tin nhận hàng | Người nhận, giờ làm việc, thời gian báo trước | Chưa |

### 7.2. Loại giao dịch kho

Mã, tên, chiều (+1 / −1), nhóm tồn (thực tế, tạm, lỗi), nhóm báo cáo (nhập, xuất, đầu kỳ, chuyển kho), cờ hao hụt, phạm vi áp dụng, diễn giải, đang dùng. ERP: chưa có (cột `ref_type` của `tab_inventory_move` chỉ nhận `gr`, `adjust`).

### 7.3. Phiếu kho (đầu phiếu)

| Trường | Ghi chú |
|---|---|
| Số phiếu, ngày chứng từ, ngày ghi sổ | Số phiếu theo mẫu `<số thứ tự>/<ddmm>` hoặc theo quy tắc mã chứng từ của ERP |
| Loại phiếu | Nhập; xuất theo đơn; xuất ngoài sản xuất; chuyển kho; xuất bán nội bộ; đưa vào chi phí; nhập / chuyển / trả TP; số dư đầu kỳ; điều chỉnh sau đối chiếu |
| Phân loại giao dịch | Từ danh mục 7.2 |
| Pháp nhân, thương hiệu | Pháp nhân đứng tên phiếu; thương hiệu chủ hàng |
| Kho xuất, kho nhập | Một hoặc cả hai tùy loại phiếu |
| Chứng từ gốc | ĐMH và lần giao; đơn TP; lệnh phối; mã sự cố; mã yêu cầu xử lý lại; kỳ đối chiếu |
| NCC GC, đơn vị làm việc với NCC | — |
| Lý do, ghi chú, ghi chú trên phiếu gửi NCC | — |
| Người đề nghị, người lập, người duyệt, ngày duyệt | — |
| Vận chuyển | Phương án, tài xế, số xe |
| Hóa đơn | Số hóa đơn, đơn vị nhận hóa đơn, tên trên hóa đơn |
| Trạng thái phiếu | Nháp; chờ duyệt; đã ghi sổ; đã hủy |
| Trạng thái thực hiện | Chưa gửi; đã gửi NCC; chờ vận chuyển; đang vận chuyển; hoàn thành |
| Tệp đính kèm | Ảnh phiếu của kho NCC GC, bản chụp có chữ ký hai bên, biên bản |

ERP: chưa có bảng phiếu kho chung; phiếu nhập ngầm `tab_goods_receipt` (mã, ĐMH, lần giao, công ty, kho, mã hàng, số nhận, ngày nhận, kết quả kiểm, ghi chú) không có trạng thái.

### 7.4. Dòng phiếu kho

Mã hàng, tên, ĐVT; số lượng yêu cầu, số lượng thực; đơn giá, thành tiền; nhóm tồn; số lô, NSX, HSD, số CAS; dòng V sản xuất, dòng V kinh doanh, màu; kết quả Lab, hàm lượng thực tế; mã BĐM, định mức; mã đơn TP; ghi chú dòng. ERP: `tab_inventory_move` (`company_id`, `warehouse_code`, `product_code`, `qty`, `unit_price`, `ref_type`, `ref_id`, `note`) — thiếu thương hiệu, nhóm tồn, lô, ngày ghi sổ.

### 7.5. Xuất theo đơn (giữ hàng và trừ thực tế)

Đơn TP; mã hàng TP; NCC GC; kho; thương hiệu; mã BĐM; mã vật tư; định mức; số lượng đặt NCC; tổng cần xuất; số chốt; các lần có thành phẩm (ngày, số TP, lượng vật tư trừ); lượng đang giữ; quy cách nhãn, quy cách thực tế SX, quy cách KD, tỷ trọng (BTP); trạng thái dòng; trạng thái duyệt; ngày đủ nội bộ, ngày đủ thuế. ERP: chưa có.

### 7.6. Tồn kho

| Trường | Ghi chú | ERP |
|---|---|---|
| Pháp nhân, kho, mã hàng | Khóa hiện có | `tab_inventory` (`company_id`, `warehouse_code`, `product_code`) |
| Thương hiệu | Thêm vào khóa | Chưa |
| Lô | Khóa của tồn chi tiết NL / BTP, TP | Chưa |
| Tồn thực tế, tồn tạm, tồn lỗi, đang giữ cho đơn, có thể sản xuất | — | Chỉ có `qty` |
| Đơn giá bình quân, giá trị tồn | — | `avg_cost`, `value` |
| Ngày nhập cuối, ngày xuất cuối, ngày giao dịch cuối | — | Chưa |
| Trạng thái sử dụng | Sử dụng được / không | Chưa |

### 7.7. Min, MOQ

Mã hàng, kho, thương hiệu, Min, MOQ, NCC phụ trách, số đang đặt chưa về, ghi chú. ERP: chưa có.

### 7.8. Lệnh phối BTP

Mã lệnh phối (NCC, nội bộ), ngày yêu cầu, người yêu cầu, NCC GC, mã BĐM BTP, BTP cần phối, dòng V, màu, số lượng cần phối, số lượng thực phối, chênh lệch, tiến độ, đơn vị nhận hóa đơn phối trộn; dòng NL: mã, định mức cho 1.000 lít (kg), lượng cần, lượng thực xuất, chênh lệch. ERP: chưa có.

### 7.9. Ánh xạ mã vật tư NCC GC

NCC GC, mã vật tư NCC, tên vật tư NCC, mã DEGO, ghi chú. ERP: chưa có.

### 7.10. Kỳ đối chiếu tồn NCC GC

- **Đầu kỳ đối chiếu:** NCC GC, kho, ngày báo cáo, ngày kiểm tồn tại NCC, lần gửi thứ mấy, nhóm hàng (VTBB, BTP, TP, hàng lỗi), tệp NCC gửi, trạng thái (nháp, đã đối chiếu, đã ký biên bản), người duyệt, bản biên bản đã ký.
- **Dòng đối chiếu:** mã NCC, mã DEGO, ĐVT, giao dịch theo NCC, giao dịch theo hệ thống, lệch số lượng, tồn theo NCC, tồn theo hệ thống, lệch tồn, dung sai, kết luận, hướng điều chỉnh, nguyên nhân, trạng thái xử lý, phiếu điều chỉnh liên quan.

ERP: chưa có.

### 7.11. Phí lưu kho và hao hụt

Loại (phí lưu kho, hao hụt, chi phí khác), NCC GC, kỳ, ngày ghi nhận, diễn giải, số tiền phía mình, số tiền phía NCC, số chứng từ kế toán, số hóa đơn, số ngày công nợ, ngày đến hạn, hình thức thanh toán, thương hiệu chịu, trạng thái đối chiếu. ERP: chưa có (công nợ `payable` chỉ sinh từ ĐMH).

### 7.12. Chuyển trạng thái hàng lỗi

Ngày, mã sự cố, mã hàng, NCC GC, kho xuất, kho nhập, số lượng, trạng thái từ, trạng thái đến, mã yêu cầu xử lý lại, nhóm lỗi, giá vốn đơn vị, giá trị, diễn giải. ERP: chưa có.

---

## 8. Liên kết với phần khác

| Phần | Kho nhận gì | Kho trả gì |
|---|---|---|
| Sản phẩm và định mức (SX-SP) | Danh mục mã NL, BTP, VTBB, TP (ERP: `tab_product`, có sẵn mã hàng, tên pháp lý, phân loại, ĐVT, mã HH liên kết); BĐM VTBB của TP (ERP: `tab_packaging_bom`, `tab_packaging_bom_part`); BĐM BTP; quy cách, tỷ trọng, dòng V, màu; nhóm hàng và số ngày quy định (`tab_item_group`) | Lịch sử sử dụng vật tư theo BĐM; tồn theo mã; cảnh báo BĐM chưa duyệt khi xuất |
| Thu mua (YCMH, ĐMH, nhận hàng) | Lần giao của ĐMH (`tab_po_delivery`: kho, số nhận, ngày nhận, số hóa đơn, tiền vận chuyển, kết quả kiểm) sinh nhập kho; số đang đặt chưa về; giá nhập | Đề xuất đặt theo Min / MOQ thành YCMH nháp; kho nhận trên YCMH (`warehouse_code`); số tồn để KD kiểm trước khi dự trù; yêu cầu đổi trả khi nhập lỗi |
| Đơn hàng gia công | Đơn TP (mã đơn, NCC, mã hàng, số KD đặt, số gửi NCC, ngày yêu cầu sẵn kho); số TP có hàng theo từng lần; hủy đơn | Trạng thái duyệt đủ VTBB, đủ NL / BTP (ngày đủ nội bộ, thuế; mã BĐM; cấu thành); số vật tư đã dùng cho đơn; phiếu xuất kho kèm LSX |
| Sự cố | Mã sự cố, phương án, yêu cầu xử lý lại | Tồn lỗi theo kho và trạng thái; số lượng đạt, số hao hụt / tiêu hủy sau xử lý; giá trị hàng lỗi |
| Giá vốn | Phí phối, phí đóng gói, chính sách NCC | Giá nhập kho VTBB, NL / BTP; đơn giá bình quân; giá trị tồn; lượng hao hụt; chênh lệch đóng tối ưu thể tích; phí lưu kho phân bổ theo thương hiệu |
| Công nợ | Số ngày công nợ theo NCC | Khoản phải trả không qua ĐMH: phí lưu kho, phí phối; khoản phải thu NCC: bồi thường hao hụt vượt mức, hàng NCC làm mất; công nợ nội bộ khi xuất bán giữa thương hiệu |
| NCC GC (hồ sơ, đánh giá) | Chính sách hao hụt, lưu kho, MOQ; danh sách kho | Kết quả đối chiếu tồn, tỷ lệ hao hụt, tiến độ xử lý chênh lệch cho đánh giá định kỳ; quyết toán tồn khi ngưng hợp tác |
| Lab | Kết quả test, hàm lượng thực tế | Yêu cầu test khi nhập tạm; mẫu xuất thử |
| Kế toán và Misa | Mã kho, khoản mục chi phí, tồn thuế | Phiếu in gửi trong ngày; sổ tổng hợp tồn có giá |
| Đặt xe | — | Yêu cầu xe khi chuyển kho bằng xe công ty |

---

## 9. Câu hỏi cần phòng Sản xuất chốt

1. **Hai sổ nội bộ và thuế:** ERP giữ cả tồn nội bộ lẫn tồn thuế, hay chỉ giữ tồn nội bộ còn tồn thuế vẫn ở Misa Thuế? Gợi ý: giai đoạn đầu chỉ làm sổ nội bộ, thêm ô xác nhận *đủ tồn thuế* do kế toán tích.
2. **Thương hiệu và pháp nhân:** thương hiệu trên sổ kho (IDA, ABA, DEGO, DR XANH, BAMBOO, N2SBIO, LAB, Dùng chung) có ứng một-một với pháp nhân không? Việc gom DEGO AGROCHEM, DEGO, BAMBOO về IDA ở sổ BTP là quy tắc cố định hay tạm thời?
3. **Tồn có thể sản xuất tính thế nào?** Ba nguồn ghi ba cách: (a) sổ tồn: tồn thực tế = đầu kỳ + nhập thực tế − xuất thực tế, tồn tạm tính riêng; (b) báo cáo VTBB: tồn thực tế + tồn tạm; (c) mẫu 9.10: tồn − xuất tạm − đơn chờ xuất. Gợi ý: lấy (c) làm chuẩn, hiển thị đủ ba thành phần.
4. **Phương pháp tính giá tồn:** bình quân gia quyền cả kỳ, bình quân sau mỗi lần nhập, hay trung bình cộng các lần nhập như mục lục sổ VTBB ghi? Tính theo từng kho hay gộp các kho? Theo từng thương hiệu hay gộp?
5. **Giá nhập kho trước hay sau VAT?** Sổ VTBB lấy giá đã gồm VAT và vận chuyển; ERP đang tính theo đơn giá ĐMH cộng chi phí thu mua phân bổ. Cần một quy ước cho giá vốn.
6. **Xuất âm kho:** chặn cứng hay chỉ cảnh báo? Gợi ý: chặn với xuất thực tế, cho phép giữ hàng vượt tồn khi có người duyệt (thành *đơn chờ xuất*).
7. **Thời điểm ghi xuất:** xác nhận quy tắc *xuất nội bộ khi NCC có thành phẩm*. Khi nhận TP về kho DEGO khác số NCC báo có hàng thì trừ vật tư theo số nào?
8. **Định mức hao hụt chuẩn:** đang có bốn nguồn khác nhau (theo NCC GC trong danh mục, theo loại VTBB ở báo cáo, mặc định 2% ở phân tích TP, điều khoản hợp đồng). Nguồn nào dùng để cấn trừ NCC? Tỷ lệ hao hụt tính trên số lượng nhập hay giá trị xuất?
9. **Hao hụt có vào BĐM không?** BĐM hiện không có cột hao hụt; phần dư khi gửi NCC là mẫu Lab. Vật tư NCC dùng vượt định mức được ghi nhận lúc nào: theo từng đơn hay chỉ khi đối chiếu cuối tháng?
10. **Số lần NCC có thành phẩm:** sổ giới hạn 3 lần cho một đơn. Thực tế có đơn giao hơn 3 lần không?
11. **Cột xuất VTBB:** hướng dẫn ghi số xuất thực tế đọc từ cột AF, AG, AH và xuất tạm từ cột AI, nhưng sheet hiện đặt ở AG, AH, AI và AJ. Bản nào đúng với sổ đang chạy?
12. **Mẫu Lab cộng thêm:** phía VTBB cộng theo số mẫu (ví dụ 200 thành 202), phía BTP cộng cố định 1. Quy tắc chung là gì, có theo quy cách sản phẩm không?
13. **Nhập đổ thu, dư sau sản xuất:** quy trình ghi *sẽ xây dựng sau*. Hiện dư vật tư sau đơn được xử lý thế nào: để lại kho NCC cho đơn sau hay NCC xuất trả?
14. **Hàng cho tặng nhập kho:** ghi giá 0 hay giá ước tính? Có tính vào giá trị tồn không?
15. **Kho lỗi:** mỗi NCC GC một kho lỗi riêng như danh mục, hay dùng nhóm tồn *lỗi* trong cùng kho? Các kho lỗi ghi *Bổ sung kho sau* đã có mã Misa chưa?
16. **Kiểm kê thực tế:** DEGO có cử người đếm tại kho NCC GC không, hay chỉ dựa biên bản của NCC? Nếu có: chu kỳ, ai đếm, ai duyệt chênh lệch.
17. **Chu kỳ đối chiếu:** hằng tuần, hằng tháng hay theo đơn? Ngày chốt số? NCC nào bắt buộc gửi báo cáo, NCC nào không gửi thì làm thế nào?
18. **Bảng ánh xạ mã NCC GC:** hiện mới đủ cho Hà Long. Ai giữ và cập nhật cho các NCC còn lại? NCC nào dùng luôn mã DEGO?
19. **Mẫu biên bản:** cần mẫu *Biên bản xác nhận tồn kho cuối kỳ* và *Biên bản kiểm tra và giải trình chênh lệch* (mục lục ghi chưa xác định phiếu in).
20. **Min và MOQ:** đặt theo mã + kho hay theo mã + kho + thương hiệu? Khi KD xác nhận định mức tồn thì cộng định mức các thương hiệu như mục lục ghi? Ngưỡng 500 / 200 ở sổ NL / BTP có bỏ không?
21. **Hai sổ tồn SX và KD:** có giữ cả hai trên ERP không? Nếu giữ, sổ nào là sổ gốc đối chiếu với NCC? Chênh lệch đóng tối ưu thể tích hạch toán ra sao?
22. **Lô và hạn dùng:** bắt buộc số lô cho NL, BTP, TP; VTBB có cần lô không (nhãn in theo đợt)? Có áp dụng xuất lô hết hạn trước không? Cảnh báo trước hạn bao nhiêu ngày (báo cáo ghi 90 ngày)?
23. **Thành phẩm:** kho TP do phòng Sản xuất hay kho Dr.Xanh quản trên ERP? TP nằm tại kho NCC GC sau khi sản xuất có tính là tồn của DEGO từ ngày nào (ngày NCC báo có hàng hay ngày nhận hóa đơn)?
24. **Xuất bán nội bộ giữa thương hiệu:** đơn giá do ai quyết, có luồng duyệt không? Trường hợp chỉ chuyển số liệu (hàng không di chuyển) có cần phiếu in không?
25. **Phí lưu kho:** danh sách NCC đang tính phí và cách tính từng NCC; phân bổ về thương hiệu theo tiêu chí nào (giá trị tồn, số pallet)? Con số ước tính 1,5% mỗi tháng có còn dùng khi đã có số thực tế?
26. **Quyền duyệt phiếu kho:** loại phiếu nào QLSX duyệt, loại nào cần thêm KD hoặc kế toán? Có hạn mức giá trị không?
27. **Chốt kỳ:** có cần khóa sổ kho theo tháng không, ai được mở lại?
28. **Số dư đầu kỳ khi lên ERP:** lấy số tại ngày nào, nguồn nào là chuẩn (sổ Drive, Misa nội bộ hay biên bản NCC), có đơn giá đầu kỳ cho VTBB không?
29. **Loại VTBB suy từ ba ký tự đầu của mã** có còn dùng khi ERP đã có phân loại trên danh mục sản phẩm không? Mã `VT0` và các mã lạ xếp vào đâu?
30. **Danh mục kho:** `KHO SX_VTBB` là kho gì? Hai tên *Agri Future* và *kho nhà cung cấp AGRIFUTURE* có gộp không? NCC có trong danh sách chính sách nhưng chưa có kho (ví dụ Việt Thắng xuất hiện ở sổ sự cố) thì bổ sung thế nào?
