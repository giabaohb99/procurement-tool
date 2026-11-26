# Nhóm D — Điều phối thành phẩm và Sự cố sản xuất

Nguồn: `D:\New folder\thuthapykien\tailieusanxuat\` — 4 tệp, 68 sheet (7 + 19 + 25 + 17). Đọc bằng openpyxl (giá trị + công thức), kiểm thêm chú thích (comments) và hình vẽ trong zip. Không tệp nào có sheet ẩn, không có metadata ngày tạo / sửa (cả 4 tệp xuất từ Google Sheets: có hàm `__xludf.DUMMYFUNCTION`, `IMPORTRANGE`, `FILTER`).

Quy ước cột trong biểu mẫu: **NT** = Nhập tay, **CC** = Click chọn (dropdown), **CT** = Công thức, **Misa** = Lấy từ Misa. Các tệp tự ghi quy ước này ở dòng 2–3 của sheet.

Kết luận nhanh:

- **Bản sao của ĐIỀU PHỐI THÀNH PHẨM (NHÁP)** là sổ vận hành thật của ĐP TP (nhập liệu, duyệt đơn, gửi đơn, nhập xuất, phiếu in) nhưng còn ở dạng nháp, nhiều công thức hỏng (#REF!) và chỉ có 3 đơn ví dụ.
- **BC ĐP THÀNH PHẨM** là lớp báo cáo mới dựng *trên* sổ ĐIỀU PHỐI (KPI tháng/quý/năm, dung sai ±5%), dữ liệu chỉ là 3 dòng ví dụ chép từ tệp NHÁP.
- **Sự cố sản xuất** là sổ sự cố bản cũ (nháp, nhiều ghi chú *xem lại*, dữ liệu thử).
- **BC SỰ CỐ SX** là bản thiết kế lại hoàn chỉnh của sổ sự cố (25 sheet, 46 sự cố mẫu, đủ báo cáo + kiểm tra dữ liệu) nhưng toàn bộ là **số liệu giả định** (ghi rõ ở Mục lục, ngày báo cáo mẫu 12/10/2026).

---

## 1. Bảng kiểm kê

### 1.1. BC ĐP THÀNH PHẨM.xlsx (7 sheet)

| Sheet | Loại | Dòng dữ liệu thật | Nội dung |
|---|---|---|---|
| HƯỚNG DẪN | hướng dẫn | 21 dòng chữ | Quy ước màu (ô vàng chữ xanh = nhập, ô xám = cột phụ tự tính, ô trắng = báo cáo), 4 bước dùng, quy ước tính tháng, giới hạn dòng. |
| DASHBOARD | báo cáo | 9 KPI × 4 quý + 2 năm | Tham số Năm nay / Năm trước / Dung sai (0,05); KPI năm theo quý so năm trước. |
| BÁO CÁO | báo cáo | 13 bảng (215 dòng) | Bảng NCC / BP-thương hiệu / Kho × T1..T12 + Cả năm. |
| ĐIỀU PHỐI | biểu mẫu nhập liệu | 3 dòng VÍ DỤ | Mỗi dòng = 1 PO gia công. A–J nhập/dán (hoặc import từ sheet ĐIỀU PHỐI của tệp NHÁP), K–T công thức. |
| NHẬP-XUẤT TP | biểu mẫu nhập liệu | 2 dòng VÍ DỤ | Mỗi dòng = 1 lần nhập hoặc xuất thành phẩm (thùng). |
| SỰ CỐ TP | biểu mẫu nhập liệu | 1 dòng VÍ DỤ | Mỗi dòng = 1 sự cố thành phẩm (thùng), A–F nhập, G–I công thức. |
| DANH MỤC | danh mục | 15 NCC, 2 BP, 14 kho | Nguồn dropdown; ghi chú *Danh mục này thay bằng DATA 1 khi chốt form báo cáo*. |

Cột biểu mẫu ĐIỀU PHỐI: Mã PO, NCC, BP / Thương hiệu, Ngày đặt, Ngày y/c sẵn kho NCC, Ngày NCC SX xong, SL đặt (thùng), SL NCC thực SX (thùng), Loại đơn (Thường/Gấp), Nguyên nhân / ghi chú = NT/CC; Năm đặt, Tháng đặt, Năm SX xong, Tháng SX xong, Số ngày lệch, Cờ trễ, Cờ gấp, Cảnh báo SX (Dư/Thiếu/Đủ), Chưa hoàn thành, Kiểm tra dữ liệu = CT. Báo cáo dùng tên vùng (DP_NCC, DP_SLdat, DP_Lech, CFG_DungSai...), giới hạn 1.004 dòng (ĐIỀU PHỐI, SỰ CỐ TP) và 3.004 dòng (NHẬP-XUẤT TP).

### 1.2. Bản sao của ĐIỀU PHỐI THÀNH PHẨM (NHÁP).xlsx (19 sheet)

| Sheet | Loại | Dòng dữ liệu thật | Nội dung |
|---|---|---|---|
| MỤC LỤC | hướng dẫn | 18 dòng | Danh sách sheet + mô tả + phân loại (*Chạy KD*, *Phiếu*) + ghi chú việc còn treo. |
| Data1 | danh mục | ~35 dòng × 20 nhóm | Danh mục dùng chung (bản chép *Data 1*): công ty nội bộ, kho, loại nhập / xuất / tồn, khoản mục chi phí, ĐVT, hình dạng, màu, phân loại SP, dòng V. Dòng 1 ghi nguồn từng cột (NT / Misa). |
| Thông tin NCC(Data1) | danh mục | 15 NCC GC | Tên viết tắt, tên NCC GC (theo GCNĐKKD), nhóm SP được phép SX, MST, địa chỉ trụ sở, địa chỉ kho, thời gian làm việc, thời gian báo trước khi nhận hàng (trống cả 15), nhân sự ĐP TP phụ trách. MỤC LỤC gọi là *Thông tin NCC & MOQ đơn hàng (cung cấp KD)* nhưng không có cột MOQ. |
| Quà tặng NCC GC | biểu mẫu nhập liệu | 0 | STT, Ngày nhận/gửi, Người gửi, Người nhận, Chi tiết quà, Lý do, Giá trị (tất cả NT). |
| Data số ngày cập nhật cho KD | danh mục | 3 (Hà Long) | Số ngày SX theo NCC × cấu thành BTP / VTBB (bên mình / khách hàng / NCC). Nguồn QLDL, cung cấp cho KD. |
| Kết quả KCS Kho Dr.Xanh | biểu mẫu nhập liệu | 0 (chỉ 2 dòng giá trị dropdown) | Kết quả kiểm hàng khi kho Dr.Xanh nhận. |
| Lịch sử thông tin NCC GC | biểu mẫu nhập liệu | 3 (Hà Long) | Nhật ký thay đổi thông tin NCC: Tên NCC, Đầu mục, Thông tin, Chi phí, Hiện trạng (Còn / Hết hiệu lực), Ngày. |
| ĐIỀU PHỐI | biểu mẫu nhập liệu (sổ gốc) | 3 PO ví dụ + 15 trạng thái dropdown | Tiến độ từng PO gia công, 65 cột (xem mục 2). |
| họp07.10 | nháp / biên bản | 7 trạng thái chốt + 12 trạng thái *Bỏ* | Định nghĩa trạng thái điều phối đơn hàng chốt trong họp 07/10. |
| YÊU CẦU XỬ LÝ LẠI | biểu mẫu nhập liệu | 1 ví dụ | Đơn yêu cầu NCC GC xử lý lại hàng sự cố, cấu trúc giống DUYỆT ĐƠN HÀNG (7 nhóm duyệt). |
| DUYỆT ĐƠN HÀNG | biểu mẫu nhập liệu | 3 PO ví dụ | Duyệt đơn của 7 nhóm trong phòng SX trước khi gửi NCC; ~86 cột. |
| GỬI ĐƠN NCC | phiếu in | 1 dòng ví dụ (Hà Long) | Mẫu *Đơn đặt hàng sản xuất NCC*. |
| NHẬP-XUẤT TP | biểu mẫu nhập liệu | 5 ví dụ + 6 dòng dở | Nhập / xuất / chuyển / trả thành phẩm theo PO, kèm lô, NSX, HSD, kết quả Lab, biển số, tài xế. |
| BC TỒN KHO TẠI NCC GC | báo cáo | 1 dòng (lỗi) | Tồn TP tại NCC theo NCC × mã HH × NSX: 1+2+3−4+5−6+7. Cột khóa tham chiếu #REF!, toàn bộ ra 0. |
| BC GỬI KHO | báo cáo | 0 | Báo cáo hàng ngày cho kho (đủ / chưa đủ ĐK nhận hàng); ghi *ĐỂ TẠM, CÓ THỂ BỎ*. |
| DS NHẬN HÀNG | phiếu in | 0 (khung 15 dòng) | *Phiếu giao nhận hàng tại NCC* cho tài xế. |
| LỊCH NGHỈ LỄ NCC | danh mục | 9 NCC (năm 2026) | Tết Tây, Tết Nguyên đán, Giỗ Tổ, 30/4–1/5, Quốc khánh, Ngày Văn hóa 24/11 — chữ tự do. |
| P.NHẬP KHO TP | phiếu in | 1 PO (lỗi #REF!/#N/A) | *Giấy đề nghị nhập kho thành phẩm*, lọc theo mã PO bằng FILTER. |
| P.XUẤT BÁN HÀNG | phiếu in | 1 PO (lỗi #REF!) | *Phiếu đề nghị xuất kho bán hàng*, lấy dòng từ P.NHẬP KHO TP, ghi xuất bán lần 1/2/3. |

### 1.3. BC SỰ CỐ SX.xlsx (25 sheet) — số liệu giả định

| Sheet | Loại | Dòng dữ liệu | Nội dung |
|---|---|---|---|
| Trang tính1 | nháp / yêu cầu | 6 nhóm yêu cầu | Đề bài: danh sách số liệu cần thống kê (năm / chi tiết) và mục tiêu. |
| Mục lục | hướng dẫn | 24 sheet + luồng 6 bước + 9 định nghĩa chỉ số + quy ước | Hướng dẫn đầy đủ nhất trong nhóm D. |
| Danh mục | danh mục + tham số | 18 loại lỗi, 6 nhóm lỗi, 21 danh sách dropdown | Tham số kỳ báo cáo (Năm, Ngày BC, Tháng/Quý/Năm), quy tắc đặt mã, danh mục dropdown. |
| Mã hàng | danh mục | 20 mã | Mã hàng, Tên hàng, Tên pháp lý, Thương hiệu, NCC GC, ĐVT, QC thùng, Giá vốn / ĐVT (NT). |
| Sản lượng GC | biểu mẫu nhập liệu | 50 (5 NCC × T1–T10) | Năm, Tháng, NCC GC, Số đơn hàng GC, Sản lượng TP (ĐVT), Ghi chú — mẫu số tỷ lệ lỗi. Cột G (SL thùng mua) chưa có. |
| Tổng hợp sự cố | biểu mẫu nhập liệu (sổ gốc) | 46 sự cố | Mỗi dòng = 1 mã sự cố, 46 cột (xem mục 3). |
| Tiến độ XLY các BP | biểu mẫu nhập liệu | 111 yêu cầu | Mỗi dòng = 1 yêu cầu gửi 1 bộ phận hỗ trợ. |
| Yêu cầu ĐP XLY lại | biểu mẫu nhập liệu | 29 yêu cầu | Sự cố yêu cầu ĐP TP xử lý lại tại NCC GC. |
| BC Chi tiết SC | báo cáo | 46 | Chi tiết từng mã sự cố: chênh lệch SL, BP hỗ trợ, NCC xử lý, trễ hạn. |
| Chi Phí Xử Lý | biểu mẫu nhập liệu | 107 dòng chi phí | Phân bổ chi phí theo mã sự cố, đối tượng chịu, hình thức thu, trạng thái chứng từ. |
| Nhập xuất (NCC GC) | biểu mẫu nhập liệu (sổ gốc kho lỗi) | 174 giao dịch | Mỗi dòng = 1 lần chuyển hàng lỗi giữa kho và/hoặc trạng thái. |
| BC Tổng quan | báo cáo | KPI + 12 tháng + 4 quý + năm + top 5 | Bức tranh chung. |
| Tổng XNT (NCC GC) | báo cáo | 46 | Nhập xuất tồn hàng lỗi theo mã sự cố × trạng thái, có 2 cột kiểm tra. |
| BC NCC GC | báo cáo | 5 NCC | Bảng điểm NCC (trọng số), xu hướng tỷ lệ lỗi, NCC × nhóm lỗi. |
| BC Nhóm lỗi | báo cáo | 6 nhóm, 18 loại | Pareto, Trong SX / Sau SX, hướng cải tiến gợi ý. |
| BC Bộ phận | báo cáo | 9 BP | SLA phản hồi của BP hỗ trợ; trách nhiệm phát sinh theo BP. |
| BC Tồn kho lỗi | báo cáo | 7 kho | Tồn lỗi kho × trạng thái, tuổi tồn, nguyên nhân treo. |
| Kiểm tra dữ liệu | báo cáo (kiểm soát) | 16 phép kiểm | Toàn vẹn mã, lệch SL, thiếu dữ liệu — chạy trước khi chốt. |
| BC SC x Bộ phận | báo cáo | 46 | Ma trận mã sự cố × 9 BP: số lần yêu cầu, số ngày trả KQ TB. |
| BC Năm NCC | báo cáo | 5 NCC | % lỗi theo thùng, tỷ lệ chờ PA chuyển thẳng sang dùng được, kết cục chờ PA, tình trạng xử lý theo NCC. |
| BC Chi phí - Trách nhiệm | báo cáo | 17 đối tượng | Chi phí theo đối tượng / loại chi phí / đơn vị chịu / hình thức thu; loại lỗi × đối tượng. |
| BC Tồn kho chi tiết | báo cáo | 7 sự cố còn tồn | Hàng, nhóm lỗi, kho, trạng thái chờ, SL, giá trị, ngày, tuổi tồn. |
| BC Tần suất lỗi | báo cáo | top 15 | Tần suất theo tên pháp lý / mã hàng × nhóm lỗi. |
| BC Theo tuần | báo cáo | 53 tuần | Số sự cố, SL, thiệt hại, số yêu cầu BP, số trễ theo tuần (tuần bắt đầu thứ Hai). |
| Đối chiếu yêu cầu | báo cáo (kiểm soát) | 15 chỉ số | Từng yêu cầu ở Trang tính1 → sheet / vị trí / mức đáp ứng (2 chỉ số *Cần nhập liệu*). |

Cột biểu mẫu chính:

- **Tổng hợp sự cố**: Mã đơn sự cố, Ngày ghi nhận = NT; BP / nơi yêu cầu, Mã hàng = CC; Thương hiệu, Tên hàng, Tên pháp lý, QC thùng, ĐVT, NCC GC = CT (tra *Mã hàng*); Mã đơn đặt hàng, Ngày SX, SL bị sự cố = NT; Loại lỗi chi tiết = CC; Chi tiết lỗi = NT; Nhóm lỗi, Giai đoạn = CT (tra *Danh mục*); Nơi phát sinh, BP chịu TN (chốt sau GĐ1) = CC; Đối tượng chịu TN = CT; Group tiếp nhận = CC; Nguyên nhân = NT; Phương án xử lý chính = CC; từ *SL đã xử lý – dùng được* đến *Tháng* (22 cột) = CT; mô tả GĐ1, GĐ2 = NT.
- **Tiến độ XLY các BP**: Mã sự cố = NT; 9 cột thông tin sự cố = CT; Giai đoạn (GĐ1/GĐ2) = CC; Ngày yêu cầu = NT; BP phụ trách = CC; Yêu cầu, Hạn trả KQ, Ngày trả KQ = NT; Số ngày trả KQ, Số ngày trễ, Đánh giá = CT; Mức độ ảnh hưởng SX = CC; Kết quả, Ngày kết thúc, Ghi chú = NT.
- **Yêu cầu ĐP XLY lại**: NCC chỉ định, Mức ưu tiên, Phương án = CC; Mã yêu cầu, Ngày yêu cầu, Mã sự cố, SL thùng, Mã hàng sau xử lý, Ngày nhận hàng về kho, Hạn hoàn thành cam kết, Ngày hoàn thành, SL Dr Xanh giao thực tế = NT; còn lại CT.
- **Chi Phí Xử Lý**: Ngày cập nhật, Mã sự cố, Tổng số tiền (phiếu), Phân bổ số tiền, Đơn vị chịu cụ thể, Link chứng từ = NT; Phương án kết luận, Loại chi phí, Đối tượng chịu, Hình thức thu, Trạng thái = CC; Mã hàng, Tên hàng, NCC GC, Ngày ghi nhận, Năm, Tháng = CT.
- **Nhập xuất (NCC GC)**: Ngày, Mã sự cố, Số lượng, Mã đơn YC xử lý lại, Diễn giải = NT; Kho xuất, Kho nhập, Trạng thái từ, Trạng thái đến = CC; Mã hàng, Tên hàng, NCC, ĐVT, Nhóm lỗi, Giá vốn, Giá trị = CT.

### 1.4. Sự cố sản xuất.xlsx (17 sheet) — bản cũ, nháp

| Sheet | Loại | Dòng dữ liệu | Nội dung |
|---|---|---|---|
| Mục Lục | hướng dẫn | 9 dòng | *DRIVE THEO DÕI SỰ CỐ*, có *Link cũ*. |
| Nháp (xem lại) | nháp-bỏ | 4 dòng rác thử | Ý tưởng *sự cố mẹ / sự cố con*, so CP thực tế với CP dự trù; *Huỳnh chốt form*. |
| DATA | danh mục | ~35 dòng | Bản chép Data1 + thêm cột **Trạng thái sự cố / Định nghĩa** (12 trạng thái). |
| Tồng hợp sự cố | biểu mẫu nhập liệu | 4 dòng (ISC.2507262 và 3 mã con) + danh sách loại lỗi / nhóm lỗi viết tay | Sổ gốc bản cũ, 43 cột, nhiều cột NT mà bản mới đã chuyển thành CT. |
| TIẾN ĐỘ XLY CÁC BP | biểu mẫu nhập liệu | 3 dòng thử | Giai đoạn 1 / 2, BP trả kết quả. |
| YÊU CẦU ĐP XLY LẠI | biểu mẫu nhập liệu | 1 ví dụ (XYC.09012607) | Giống hệt *YÊU CẦU XỬ LÝ LẠI* của tệp NHÁP điều phối (7 nhóm duyệt). |
| Chi Phí Xử Lý (Hạo gửi KD) | biểu mẫu nhập liệu | 0 (chỉ dropdown) | Chi phí dự trù gửi KD. |
| BC Chi Phí Xử Lý (Hạo gửi KD) | báo cáo | 2 ví dụ | Phân bổ chi phí dự trù theo BP chịu. |
| FORM IN HẠO | phiếu in | 1 phiếu (HH5004, thay nhãn, tổng 1.727.000 đ) | *Chi phí dự trù xử lý hàng hóa* gửi KD; giá VTBB lấy bằng IMPORTRANGE từ tệp định mức. |
| BC CHI PHÍ XỬ LÝ THỰC TẾ | báo cáo | 2 ví dụ | Chi phí thực tế theo BP chịu + trạng thái thủ tục + link xác nhận. |
| Chi Phí Xử Lý THỰC TẾ | biểu mẫu nhập liệu | 0 | Chi phí thực tế + chứng từ + ngày xác nhận. |
| Chi tiết nhập xuất (NCC GC) | biểu mẫu nhập liệu | 16 dòng thử (HH0001...) | Tiền thân của *Nhập xuất (NCC GC)*. |
| Tổng XNT (NCC GC) | báo cáo | 4 dòng (giá trị dán, không công thức) | Trùng 4 dòng đầu của BC SỰ CỐ SX. |
| BC SỰ CỐ | báo cáo | 0 (chỉ tiêu đề) | Khung trống. |
| SỐ NGÀY LƯU KHO LỖI NCC GC | nháp / yêu cầu | 12 dòng | Danh sách chỉ số mong muốn (số mã sự cố/năm, chi phí lưu kho, đối chiếu NCC lưu kho...). |
| THEO DÕI ĐƠN HÀNG LÙI DATE | nháp-bỏ | 0 (*Huỳnh làm*) | Chưa làm. |
| Huỳnh - Nội dung cần trao đổi v | nháp | 1 dòng | *Hồ sơ thủ tục thực hiện đổ thu*. |

---

## 2. Quy trình điều phối thành phẩm

Vai trò: **KD** (lên đơn) → **ĐP TP** (điều phối thành phẩm, chủ sổ) → 7 nhóm duyệt trong phòng SX → **NCC GC** sản xuất → **Lab** test mẫu → **Kho Dr.Xanh** (MEKONG) nhận + KCS → **Kế toán** (hóa đơn, phiếu nhập / xuất).

### Bước 1. KD lên đơn → ĐP TP ghi sổ ĐIỀU PHỐI

- Sổ: NHÁP / ĐIỀU PHỐI (mỗi dòng = 1 PO). Bắt buộc: Mã đơn đặt hàng (PO), Trạng thái (*Mới* / *Xử lý*), NCC đề xuất / mong muốn, Ngày đơn hàng, Thương hiệu, Mã hàng, Tên hàng, Phân loại, Tên pháp lý, ĐVT, Quy cách thùng, SL TP (thùng), SL TP (chai/gói), Ngày yêu cầu sẵn kho NCC, Vật tư khác, NVL khách mang qua, Đã dự trù nhãn mã YC, Đã dự trù BTP mã YC, Trạng thái NCC duyệt nhãn, Giá bán chai/gói (giá thấp nhất CSBH), Khảo sát VTBB. Không bắt buộc: Yêu cầu khác.
- Mã PO mẫu: `ITP26082611`, `ATP03092611` (tiền tố ITP / ATP + ddmmyy + 2 số). Mã BDM BTP KD tự động.
- **Số ngày sản xuất** = Ngày yêu cầu sẵn kho − Ngày đơn hàng.
- Quy định thời hạn gửi đơn: **Số ngày gửi đơn NCC** = Ngày gửi đơn NCC (hoặc hôm nay nếu chưa gửi) − Ngày đơn hàng; **> 3 ngày → LƯU Ý, > 5 ngày → TRỄ ĐƠN**.
- Kiểm NCC: *NCC sản xuất thực tế* tra từ danh mục TP + NCC GC, so với NCC đề xuất → *ĐÚNG NCC / SAI NCC* (đang #REF! vì sheet danh mục đã bỏ).
- Số ngày SX tham chiếu cho KD (sheet *Data số ngày*, nguồn QLDL), ví dụ Hà Long: BTP + VTBB bên mình 15 ngày; BTP do NCC + VTBB bên mình 10 ngày; BTP + VTBB đều do NCC 7 ngày.

### Bước 2. Duyệt đơn hàng (7 nhóm)

- Sổ: NHÁP / DUYỆT ĐƠN HÀNG. Cột A–AB chạy từ ĐIỀU PHỐI; mỗi nhóm có *Ngày duyệt* + *Trạng thái duyệt* + cột riêng, kèm link drive nhóm:
  1. **NL/BTP** (ĐP NL-BTP): Ngày đủ NL/BTP nội bộ / thuế, Mã BDM NL/BTP nội bộ / thuế, Ngày SX BTP, Công thức, Màu BTP, cấu thành (bên mình / khách hàng / NCC); trạng thái *Đủ tồn* / *Tồn NCC*.
  2. **VTBB** (ĐP VTBB): Ngày đủ VTBB nội bộ / thuế, Mã BDM VTBB nội bộ / thuế, cấu thành VTBB.
  3. **Giá vốn**: duyệt giá (công thức đòi *Đã xử lí giá*).
  4. **Pháp lý** (ĐKSX, ĐKKD, hợp đồng, pháp lý SP): NSX in trên bao bì, Đơn vị NCC bán hàng, Công ty cấu thành, Công ty nhận hóa đơn từ NCC, **Dòng hóa đơn** (ví dụ *NAM BẮC → ADU → DEGO → ABA*), Rủi ro phải chấp nhận.
  5. **Sự cố**: Sự cố có liên quan, Số lượng mẫu (chai/gói).
  6. **QLDL**: Mã số chính sách giá, Hóa đơn lấy từ NCC (*Thành phẩm* / *Phí sang chai đóng gói* / *Phí sang chai đóng gói, thùng*) — phải thuộc chính sách đã đàm phán với NCC GC.
  7. **QLSX**: Ngày duyệt QLSX, QLSX duyệt.
- **Đủ điều kiện NB** = AND(NL/BTP *Đủ tồn*, VTBB *Duyệt*, Giá vốn *Đã xử lí giá*, Pháp lý *Duyệt*, QLDL *Duyệt*, QLSX *Duyệt*) → *Đủ điều kiện* / *Chưa duyệt đủ*. Ngày NB duyệt đủ điều kiện ghi về ĐIỀU PHỐI.
- Ngày đủ NVL của NCC = max(Ngày đủ NL/BTP nội bộ, Ngày đủ VTBB) — nếu thiếu một trong hai → *Chưa đủ*.

### Bước 3. Gửi đơn NCC GC

- Phiếu: NHÁP / GỬI ĐƠN NCC — *Đơn đặt hàng sản xuất NCC*: tên NCC, ngày; cột PO, Mã SP, Tên SP, Tên pháp lý, Công thức (*Dòng V1*... từ drive NL), Màu BTP, ĐVT, Quy cách / thùng, SL thùng, SL TP kể cả mẫu, Ngày yêu cầu sẵn kho, Ghi chú, Cấu thành nội bộ / thuế, VTBB (Chai/Xô/Can, Nắp, Nhãn/Túi, NDT, Thùng — từ drive VTBB). Dòng 1 đánh dấu cột gửi NCC và cột nội bộ (*NB*). Ghi chú *Gửi kèm mockup*.
- **SL gửi NCC** = SL KD đặt (chai/gói) + SL mẫu Lab (ví dụ 5.000 + 2 = 5.002).
- Ghi lại ở ĐIỀU PHỐI: Ngày gửi đơn NCC, Ngày NCC xác nhận đủ NVL (áp dụng Hà Long, các NCC khác nếu có), Ngày dự kiến NCC có hàng, Diễn giải biến động kế hoạch SX, Ghi chú NCC.
- Phải tra **Thông tin NCC** (giờ làm việc, thời gian báo trước khi nhận hàng, nhân sự ĐP phụ trách) và **LỊCH NGHỈ LỄ NCC** khi hẹn ngày; thay đổi thông tin NCC ghi vào **Lịch sử thông tin NCC GC** (Còn / Hết hiệu lực + ngày).

### Bước 4. Theo dõi NCC sản xuất

Trạng thái đơn (chốt họp 07/10): *Chưa gửi đơn* (đang kiểm duyệt chưa đủ ĐK) → *Chưa có lịch SX* (đã gửi, chưa có ngày dự kiến) → *Đang SX* (đã có ngày dự kiến, kể cả chưa SX đủ) → *Đủ điều kiện nhận hàng* → *Hoàn thành* (đã nhận toàn bộ) / *Hủy đơn* / *Tạm ngưng*. 12 trạng thái cũ ghi *Bỏ* (Hàng sẵn kho, Bổ sung pháp lý, Chờ phương án, Đang nhận hàng, Đã lấy hàng chờ KQ test ngoại dạng, Chờ nhập kho NL/BTP, Kiểm tra nhãn, Chờ ký BB nhãn, Thành phẩm dở dang, Chờ lấy hóa đơn, Đủ điều kiện giao hàng...) nhưng dropdown ở ĐIỀU PHỐI vẫn còn chúng.

Khối số lượng ở ĐIỀU PHỐI (đơn vị chai/gói):

- TC SL gửi NCC = SL mẫu Lab + SL KD đặt.
- TC SL NCC thực SX = Σ NHẬP-XUẤT TP theo PO (loại trừ chuyển kho).
- TC SL xuất HĐ NCC = Σ nhập kho NCC + nhập kho mẫu NCC; TC SL đã nhận về = Σ chuyển kho.
- SL còn lại chưa SX = thực SX − gửi NCC → **Cảnh báo**: < 0 *CHƯA SX HẾT*, = 0 *SX ĐỦ ĐH*, > 0 *SX VƯỢT ĐH*.
- SL đã nhận HĐ chưa nhận về = xuất HĐ − đã nhận.
- Ngày NCC sản xuất = ngày nhập cuối cùng loại *1.NHẬP* của PO.

Khối báo cáo ở **BC ĐP THÀNH PHẨM** (đơn vị thùng):

- **Số ngày lệch** = Ngày NCC SX xong − Ngày y/c sẵn kho NCC (dương = trễ, âm = sớm, 0 = đúng hạn); Cờ trễ = 1 nếu > 0.
- **Dung sai SX ±5%** (ô tham số): *Dư* nếu SL thực SX > SL đặt × 1,05; *Thiếu* nếu < SL đặt × 0,95; còn lại *Đủ*.
- Cờ gấp = Loại đơn *Gấp*; Chưa hoàn thành = chưa có ngày SX xong.
- KPI: Tổng số PO, Sản lượng đặt, Số ngày lệch TB, Tỷ lệ đơn trễ = Σ cờ trễ / số đơn đã có ngày SX xong, Tỷ lệ đặt gấp, Tỷ lệ NCC SX dư / thiếu (chỉ đơn đã có SL thực SX), Số đơn chưa hoàn thành; theo quý, cả năm, so năm trước (chênh lệch tỷ lệ = hiệu điểm %).
- Quy ước tháng: PO, sản lượng, % gấp, % dư/thiếu theo **tháng đặt**; số ngày lệch, % trễ theo **tháng SX xong**; sự cố theo **tháng phát sinh**; tồn kho cuối tháng = Σ nhập − Σ xuất đến ngày cuối tháng. Cột *Cả năm* tính lại từ dữ liệu, không cộng 12 tháng.
- 13 bảng: số PO / sản lượng theo NCC × tháng; ngày lệch TB và % trễ theo NCC; cơ cấu sớm / đúng / trễ / chưa xong; PO gấp, PO, sản lượng, % gấp theo BP-thương hiệu; % dư, % thiếu; PO so cùng kỳ; tồn kho TP cuối tháng theo kho; SL sự cố, số sự cố, số ngày khắc phục TB theo kho.

### Bước 5. Lấy mẫu Lab, nhận hàng, KCS

- ĐIỀU PHỐI / NHẬP-XUẤT TP: Ngày gửi mẫu Lab, Ngày Lab phản hồi, Kết quả Lab (ngoại dạng, màu sắc, trọng lượng, thể tích — *ĐẠT / KHÔNG ĐẠT*).
- **DS NHẬN HÀNG** (phiếu cho tài xế nhận tại kho NCC): Tên NCC, Địa chỉ, Giờ làm việc, Liên hệ nhận hàng, Điều phối phụ trách, Nhận hàng cho (công ty nội bộ, ví dụ IDA), Ngày nhận, Tài xế, Biển số; bảng Mã HH, Tên SP, Tên pháp lý, ĐVT, SL thùng, SL lẻ, Tổng TP, NSX, Ghi chú.
- **Kết quả KCS Kho Dr.Xanh** (kho nhập theo đơn hàng): Ngày nhận, Mã hàng, Tên hàng, SL yêu cầu nhận, SL thực tế nhận, NSX, Số lô, HSD, Phụ kiện đi kèm (*Đủ / Không đủ*: tag treo, cốc đong, nhãn phụ, tem, màng co), Ngoại dạng (*Đạt / Không đạt*: xì, rách, tróc), Chứng từ NCC (*Khớp / Không khớp*), SL đạt, SL không đạt, Nguyên nhân, Ngày hoàn thành, Trạng thái (*Đang KCS / Đã KCS xong*).
- Quy định: nếu kho đã KCS *đạt* thì **kho tự chịu** lỗi phát sinh do bảo quản tại kho. Còn treo: lỗi phát hiện sau bao nhiêu ngày kể từ nhận hàng thì ĐP TP còn làm việc với NCC GC.

### Bước 6. Nhập kho thành phẩm

- Sổ: NHÁP / NHẬP-XUẤT TP (*Nhập – Xuất – Chuyển – Trả thành phẩm*): Ngày, Số phiếu, Mã PO, Trạng thái đơn (*Hàng mới / Hàng xử lý*), Thương hiệu, Kho xuất, Kho nhận, **Trạng thái** (1.NHẬP TP, 2.NHẬP MẪU, 3.NHẬP DƯ, 4.CHUYỂN KHO, 5.TRẢ HÀNG, 6.XUẤT XỬ LÝ, 7.NHẬP SAU XỬ LÝ), Ghi chú, Mã HH, Tên, Pháp lý, ĐVT, SL SP/thùng, SL thùng, SL chai/gói, Mã lô, Số hóa đơn, NSX, HSD, HSD còn lại, Lab, Biển số, Tài xế.
- Quy định: **HSD = NSX + 2 năm** (công thức cố định 365×2); HSD còn lại = HSD − ngày giao dịch. Hàng **dư** nếu chấp nhận nhận thì chuyển trạng thái *1.NHẬP KHO TP*; hàng dư KD chưa nhận thì chuyển qua sự cố.
- Phiếu **P.NHẬP KHO TP** (*Giấy đề nghị nhập kho thành phẩm*, đơn vị IDA GLOBAL, người lập = nhân viên điều phối): Kho nhập, NCC, Ngày nhập kho, Mã PO, Mã hàng, Tên, Tên pháp lý, Màu BTP, ĐVT, SL mới, SL mẫu, Cấu thành TP nội bộ / thuế; ký Trưởng phòng, Kế toán, Duyệt đủ VTBB, Duyệt đủ NL, Người lập.
- **BC TỒN KHO TẠI NCC GC**: theo NCC × mã HH × NSX: Tổng tồn = 1.NHẬP TP + 2.NHẬP MẪU + 3.NHẬP DƯ − 4.CHUYỂN KHO + 5.TRẢ HÀNG − 6.XUẤT XỬ LÝ + 7.NHẬP SAU XỬ LÝ; Số ngày tồn tại NCC = hôm nay − ngày nhập; HSD còn lại.

### Bước 7. Xuất bán hàng

- Phiếu **P.XUẤT BÁN HÀNG** (*Phiếu đề nghị xuất kho bán hàng* cho công ty nội bộ): Người đề nghị, Bộ phận SX, Chức vụ Kế hoạch SX, Phân loại *Xuất kho bán hàng*, Đơn vị mua hàng, Kho xuất, Kho nhận, Khoản mục chi phí; bảng Mã hàng, Tên, ĐVT, SL (= SL mới + SL mẫu từ phiếu nhập); hỗ trợ xuất bán nhiều lần (lần 1/2/3: ngày nhận, SL); ký Trưởng BP, Người lập, Kế toán.
- Dòng hóa đơn đi theo *Công ty cấu thành* và *Công ty nhận hóa đơn từ NCC* đã duyệt ở bước 2.

### Bước 8. Phụ trợ

- **Quà tặng NCC GC**: ĐP TP theo dõi quà nhận / gửi (ngày, người gửi, người nhận, chi tiết, lý do, giá trị). Quy định: mỗi bộ phận có drive đánh giá NCC riêng tổng hợp cho QLDL; **QLSX ra quyết định cuối** về tặng quà.
- **LỊCH NGHỈ LỄ NCC**: ĐP TP cập nhật hằng năm cho từng NCC (6 dịp lễ).

---

## 3. Quy trình sự cố sản xuất (theo BC SỰ CỐ SX, bản mới)

Luồng 6 bước (Mục lục): Ghi nhận → GĐ1 định hiện trạng → GĐ2 chốt phương án → Hàng đi đâu → Ai chịu chi phí → Báo cáo.

### 3.1. Ghi nhận sự cố và quy tắc đặt mã

- Sổ: *Tổng hợp sự cố* (mỗi dòng = 1 mã sự cố; đến dòng 104). Người ghi: **BP yêu cầu** (NCC GC, KD, Kho, Khách hàng, Lab, ĐP TP, Pháp lý, QLDL, Kế toán) điền phần thông tin; **BP Sự cố (SC)** điền phần xử lý.
- **Mã sự cố**: `ISC.ddmmyy + số thứ tự trong ngày` (ví dụ `ISC.2507262` = sự cố thứ 2 ngày 25/07/26). Một mã sự cố = một mã hàng + một lô / đơn hàng, làm khóa chung giữa các sheet.
- **Mã yêu cầu xử lý lại**: `IYC.ddmmyy + số thứ tự trong ngày`.
- **Mã đơn đặt hàng**: `ATP + 6 số` (theo hệ thống).
- Bản cũ (Sự cố sản xuất) dùng thêm: sự cố con `ISC.2507262.1`, mã xử lý lại `ISC.2507262-1` hoặc `XYC.09012607` (mẫu *TH + YC + "." + ngày + stt*); nhiều mã xử lý lại cách nhau dấu phẩy; nhiều mã PO gộp trong một ô.
- Trường bắt buộc: Mã hàng, SL TP bị sự cố (*nhập đúng số lượng lỗi*), Ngày SX, Mã PO, Loại lỗi chi tiết, Chi tiết lỗi (*ghi chi tiết, không ghi chung chung*), Nơi phát sinh (Tại NCC GC / Kho Dr Xanh / Tại khách hàng). Bản cũ có thêm khối *tại khách hàng*: tên khách, SL đã bán theo lô, ngày giao, SL tồn tại khách, SL đã xuất HĐ, SL có thể thu hồi HĐ; và *tổng tồn tại kho Dr.Xanh*.

### 3.2. Phân nhóm lỗi

6 nhóm theo trình tự công đoạn, 18 loại lỗi chi tiết, mỗi loại có giai đoạn và BP chịu mặc định:

| TT | Nhóm lỗi | Loại lỗi chi tiết (giai đoạn, BP chịu mặc định) | Hướng cải tiến gợi ý |
|---|---|---|---|
| 1 | Pháp lý | Giấy tờ hết hạn / thiếu; Nội dung giấy tờ sai; Nội dung trên nhãn sai (Trong SX, Pháp lý) | Rà hạn giấy tờ + checklist nhãn trước khi lên đơn; khóa đơn nếu hồ sơ hết hiệu lực |
| 2 | NL/BTP | BTP rớt hàm lượng; BTP lắng cặn, tách lớp; Sử dụng sai NL/BTP (NCC GC); NL/BTP không đủ tồn; NL/BTP cận / hết HSD (ĐP NL-BTP) — Trong SX | Yêu cầu COA / test hàm lượng BTP trước khi đóng gói; kiểm tồn và hạn NL/BTP khi đặt đơn |
| 3 | VTBB | Sử dụng sai VTBB; VTBB không đạt (xì, móp chai, vỡ thùng) (NCC GC); VTBB không đủ tồn (ĐP VTBB) — Trong SX | Đối chiếu VTBB đặt – thực nhận; duyệt mẫu chuẩn; kiểm VTBB đầu vào tại NCC |
| 4 | Thành phẩm | Đóng thiếu / dư; Mờ / sai date (Trong SX, NCC GC); TP cận / hết HSD (Sau SX, ĐP TP) | Kiểm date, đếm thùng cuối chuyền (AQL); quản lý date lùi / chồng date |
| 5 | Vận hành ngoài SX | KCS tại kho phát hiện muộn; Giao hàng sai / thiếu / hư hỏng (Sau SX, Kho) | Chuẩn hóa KCS tại kho và checklist giao nhận; chụp ảnh khi giao |
| 6 | Lỗi khác | Không thống nhất chính sách / quy trình / chứng từ (QLDL); Không có hóa đơn (Kế toán) — Sau SX | Thống nhất chính sách, quy trình, hồ sơ giữa KD – Kế toán – QLDL |

BP chịu trách nhiệm → **nhóm đối tượng**: NCC GC → *NCC GC*; ĐP thành phẩm, ĐP VTBB, ĐP NL-BTP → *Nội bộ sản xuất*; QLDL, Pháp lý, Lab, Kinh doanh, Kho, Kế toán → *Bộ phận hỗ trợ*; Khách hàng → *Khách hàng*; chưa chốt → *Chưa xác định*. Group tiếp nhận: *1.SX SỰ CỐ, HÀNG LỖI, PHÁP LÝ* / *DR Xanh – Xử lý sự cố hàng hóa*.

### 3.3. GĐ1 — yêu cầu các bộ phận hỗ trợ (định hiện trạng)

- Sổ: *Tiến độ XLY các BP* — mỗi dòng = 1 yêu cầu gửi 1 BP (Lab, Kế toán, Pháp lý, Kho, QLDL, ĐP TP, ĐP VTBB, ĐP NL-BTP, Kinh doanh), có **Hạn trả kết quả**. Ví dụ yêu cầu: Lab test hàm lượng; QLDL làm việc với NCC về nguyên nhân và phương án; Kho kiểm đếm thực tế; Kế toán kiểm dòng hóa đơn; ĐP TP kiểm lịch sử SX, date lô.
- Mức độ ảnh hưởng SX: *Cao – ngưng đơn hàng* / *Trung bình – duyệt tạm đơn* / *Thấp – không ảnh hưởng*. Mức ưu tiên: *GẤP / THƯỜNG*.
- Công thức: Số ngày trả KQ = Ngày trả − Ngày yêu cầu; Số ngày trễ = max(0, Ngày trả (hoặc Ngày BC nếu chưa trả) − Hạn); Đánh giá = *Đúng hạn* / *Trễ hạn* / *Quá hạn chưa trả* / *Chưa đến hạn*.
- Đủ kết quả → chốt **BP chịu trách nhiệm** (NCC GC / nội bộ SX / BP hỗ trợ).

### 3.4. GĐ2 — phương án và yêu cầu xử lý lại tại NCC GC

- Phương án: *Sử dụng được / Xử lý lại chính nó / Chuyển thành hàng khác / Đổ thu BTP / Tiêu hủy / Xuất chi phí / Chưa có phương án*.
- Phương án xử lý lại → **Yêu cầu ĐP XLY lại** (Sự cố yêu cầu ĐP TP; ĐP TP trả kết quả về Sự cố): NCC chỉ định, Mã IYC, Ngày yêu cầu, Ưu tiên, Mã sự cố, Mã PO, SL thùng / SL TP yêu cầu xử lý, Phương án, Mã hàng sau xử lý (đổi nhãn / SP mới), Ngày nhận hàng về kho, **Hạn hoàn thành cam kết**, Ngày hoàn thành, SL Dr Xanh giao thực tế.
- Công thức: Tiến độ = *Hoàn thành* (có ngày xong) / *Chờ hàng về* (chưa nhận) / *Đang xử lý*; SL đạt / SL hao hụt lấy từ sổ kho theo mã IYC; **Tỷ lệ thu hồi = SL đạt / (SL đạt + SL hao hụt)**; Số ngày xử lý = Ngày xong (hoặc Ngày BC) − Ngày yêu cầu; Đánh giá thời hạn *Đúng hạn / Trễ hạn / Quá hạn / Trong hạn*; Chênh lệch = SL yêu cầu − SL Dr Xanh giao.
- Bản cũ / tệp NHÁP: đơn xử lý lại đi qua đủ **7 nhóm duyệt** như đơn mới (Pháp lý, Sự cố, NL/BTP, VTBB, QLDL, Giá vốn, QLSX), có *Ngày SX trên nhãn* (hàng trôi, mất, không có NSX → ghi *KHÔNG CÓ*), *NSX yêu cầu in trên bao bì* (nếu lùi date thì ghi ngày SX). MỤC LỤC tệp NHÁP: xem lại duyệt đơn xử lý lại có giống đơn điều phối không, gộp được thì gộp.

### 3.5. Kho lỗi / tồn kho lỗi

- Sổ gốc: *Nhập xuất (NCC GC)* — mỗi dòng = 1 lần chuyển hàng lỗi giữa kho (xuất → nhập) và/hoặc trạng thái (từ → đến). Dòng ghi nhận: kho xuất *(Phát sinh)*, trạng thái từ *Phát sinh*. Hoàn thành: kho nhập là kho sử dụng hoặc *(Tiêu hủy)* / *(Xuất chi phí)*.
- Kho: kho lỗi Dr Xanh, kho lỗi từng NCC GC (`<NCC>_lỗi`), *Kho KH lỗi* (tại khách), kho sử dụng (`<NCC>_Sử dụng`), và 3 kho ảo ngoài hệ thống. Danh mục Data1 có sẵn cặp kho `NCC_<tên>` / `NCCXL_<tên>` cho từng NCC.
- 12 trạng thái hàng lỗi: Phát sinh → Nghi ngờ lỗi → Chờ phương án → Chờ chuyển thành hàng khác / Chờ xử lý lại chính nó / Chờ tiêu hủy / Chờ đổ thu BTP → Hoàn thành / Sử dụng được, Tiêu hủy, Xuất chi phí (bản cũ thêm: Đã đổ thu BTP, Khách hàng tự xử lý, Trả trừ công nợ).
- **Tồn lỗi = SL phát sinh − SL hoàn thành (sử dụng được + tiêu hủy + xuất CP)** và phải bằng Σ các trạng thái chờ (cột kiểm tra = 0). Tuổi tồn = Ngày BC − Ngày ghi nhận; nhóm 0–30 / 31–60 / 61–90 / > 90 ngày; % giá trị tồn > 60 ngày.
- *Tiến độ chung* tự suy: *Chưa ghi nhận kho* (chưa có dòng phát sinh) / *Hoàn thành* (tồn = 0) / *Chưa có phương án* (còn SL chờ PA / nghi ngờ) / *Đang xử lý*.

### 3.6. Chi phí xử lý và đối tượng chịu trách nhiệm

- Sổ: *Chi Phí Xử Lý* — phân bổ theo mã sự cố; một phiếu có thể chia cho nhiều sự cố (kiểm: phân bổ không vượt tổng phiếu).
- Loại chi phí: Vận chuyển khách → kho, Vận chuyển kho – NCC GC, Kiểm mẫu / Test Lab, Nhân công xử lý lại, VTBB / bao bì thay thế, Phí tiêu hủy, Phí lưu kho. Bản cũ (phiếu dự trù gửi KD): chai mới, nhãn mới, thùng mới, nhãn dán thùng, đổ thu BTP, gia công đóng mới, KCS, vận chuyển; *chưa tính phối chế lại, hao hụt chiết rót*; *tái sử dụng thùng cũ thì không tốn CP thùng*.
- Đối tượng chịu chi phí: NCC GC / Nội bộ sản xuất / Bộ phận hỗ trợ / Khách hàng; Đơn vị chịu cụ thể (ví dụ Hà Long, ĐP NL-BTP, Công ty).
- Hình thức thu: **Cấn trừ công nợ / Thu tiền / Hạch toán chi phí**. Chứng từ: BB có chữ ký NCC GC, Giấy thanh toán, Phiếu thu / UNC từ NCC. Trạng thái: *Hoàn thành / Đang thực hiện / Chờ thực hiện chứng từ*.
- Quy định: chi phí nội bộ do **BP Sự cố** làm phiếu thanh toán; chi phí liên quan NCC GC do **QLDL** thực hiện dựa trên phiếu yêu cầu của Sự cố. Bản cũ tách 2 lớp: **chi phí dự trù** (gửi KD, có xác nhận chấp nhận / không chấp nhận, lý do, phương án đề xuất, ví dụ *Trình giám đốc*) và **chi phí thực tế** (chứng từ, link, ngày xác nhận). Bản mới chỉ còn một lớp.
- Chi phí và thiệt hại tính theo **kỳ phát sinh sự cố**.

### 3.7. Chỉ số báo cáo và công thức

Tham số kỳ: Năm báo cáo, Ngày báo cáo (thực tế = TODAY()), Loại kỳ Tháng / Quý / Năm, Giá trị kỳ → Từ tháng / Đến tháng.

| Chỉ số | Công thức |
|---|---|
| Tỷ lệ lỗi | SL sản phẩm sự cố / Sản lượng GC cùng kỳ (mọi nguyên nhân) |
| Tỷ lệ lỗi do NCC | SL sp sự cố có BP chịu = *NCC GC* / Sản lượng GC của NCC đó |
| Sự cố do NCC / 100 đơn | Số sự cố do NCC / Số đơn hàng GC × 100 |
| % lỗi theo thùng | SL thùng lỗi (= SL sự cố / QC thùng) / SL thùng mua (chưa có dữ liệu → *Chưa nhập*) |
| Sự cố lặp lại | Lần xuất hiện = số sự cố cùng mã hàng + cùng loại lỗi có ngày ≤ ngày hiện tại; > 1 → *Lặp lại* (cũng tính theo tên pháp lý + loại lỗi) |
| Giá trị hàng sự cố | SL sự cố × Giá vốn / ĐVT |
| Tổn thất hàng | (SL tiêu hủy + SL xuất CP) × Giá vốn |
| Tổng thiệt hại | Tổn thất hàng + Chi phí xử lý (Σ phân bổ ở Chi Phí Xử Lý) |
| Giá trị tồn lỗi | SL tồn lỗi × Giá vốn |
| Số ngày xử lý | Ngày hoàn thành − Ngày ghi nhận (chưa xong: Ngày BC − Ngày ghi nhận) |
| Tỷ lệ thu hồi | SL đạt sau xử lý lại / (SL đạt + SL hao hụt), theo mã IYC |
| Tỷ lệ đúng hạn BP | Số YC đúng hạn / (đúng hạn + trễ hạn + quá hạn chưa trả); chưa đến hạn không tính. Đánh giá: ≥ 85% *Đạt*, ≥ 70% *Cần theo dõi*, còn lại *Cần cải thiện* |
| % chuyển thẳng chờ PA → dùng được | SL chuyển thẳng từ *Chờ phương án* sang *Sử dụng được* / SL vào *Chờ phương án* |
| % thực tế không lỗi | Σ SL *Sử dụng được* (mọi đường) / Σ SL đã thống kê |

**Điểm NCC GC** (sheet BC NCC GC, tham số sửa được):

- Ngưỡng tỷ lệ lỗi do NCC bị 0 điểm = **2%**; mục tiêu số ngày xử lý = **30 ngày**.
- Trọng số: **Tỷ lệ lỗi 0,4 — Lặp lại 0,2 — Tốc độ xử lý 0,2 — Thu hồi chi phí 0,2** (kiểm tổng = 100%).
- Điểm tỷ lệ lỗi = max(0; 100 × (1 − tỷ lệ lỗi do NCC / 2%)).
- Điểm lặp lại = 100 × (1 − % sự cố do NCC bị lặp lại).
- Điểm tốc độ = min(100; max(0; 100 × (2 − ngày xử lý TB / 30))) — ≤ 30 ngày được 100, 60 ngày về 0.
- Điểm thu hồi CP = 100 × Đã thu hồi / Chi phí NCC chịu (không có chi phí → 100). Đã thu hồi = chi phí NCC chịu có trạng thái *Hoàn thành*.
- Tổng điểm = Σ trọng số × điểm thành phần; xếp loại **A ≥ 85, B ≥ 70, C ≥ 55, D < 55**; xếp hạng RANK. NCC có < 3 sự cố trong kỳ chỉ tham khảo; chưa có dữ liệu = điểm tối đa.
- Kèm: tỷ lệ thu hồi sau xử lý lại, % xử lý lại đúng hạn, xu hướng tỷ lệ lỗi do NCC theo T1..T12 / Q1..Q4 / năm, NCC × nhóm lỗi → *Công đoạn yếu nhất*.

Các báo cáo khác: Tổng quan (KPI kỳ, xu hướng tháng / quý / năm với Δ so kỳ trước, Trong SX vs Sau SX, phân bổ trách nhiệm, top 5 thiệt hại, top 5 tồn lỗi); Nhóm lỗi (Pareto); Bộ phận (SLA, trách nhiệm theo BP); Tồn kho lỗi (kho × trạng thái, tuổi tồn, nguyên nhân treo = trạng thái × nhóm lỗi); Chi phí – Trách nhiệm; Tần suất lỗi (top 15); **Theo tuần** (tuần bắt đầu thứ Hai, tuần 1 chứa 01/01, WEEKNUM kiểu 2); theo ngày xem cột Ngày ghi nhận.

16 phép **Kiểm tra dữ liệu** (mọi dòng phải = 0): mã sự cố ở các sổ con không có trong Tổng hợp; mã sự cố trùng; mã IYC trùng / không có; sự cố chưa ghi nhận kho; SL sổ kho ≠ SL sự cố; tồn ≠ Σ trạng thái chờ; mã hàng / loại lỗi ngoài danh mục; đã có phương án nhưng chưa chọn BP chịu; phân bổ chi phí vượt phiếu; dòng kho trống hoặc SL ≤ 0; sản lượng GC thiếu tháng.

Số liệu mẫu (giả định, chỉ để hình dung quy mô): năm 2026 có 46 sự cố, 139.946 ĐVT sự cố / 7.950.300 ĐVT sản lượng GC → tỷ lệ lỗi 1,76%; tổng thiệt hại khoảng 699 triệu đồng; tồn lỗi 16.520 ĐVT trị giá 387 triệu, 89% giá trị tồn > 60 ngày.

---

## 4. So sánh các cặp tệp

### 4.1. Sự cố: BC SỰ CỐ SX và Sự cố sản xuất

| Tiêu chí | Sự cố sản xuất (cũ) | BC SỰ CỐ SX (mới) |
|---|---|---|
| Vai trò | Sổ làm việc thật, đang dở (*Link cũ*, *Nháp (xem lại)*, *Huỳnh làm*) | Hệ thống thiết kế lại: sổ gốc + 15 báo cáo + kiểm tra dữ liệu |
| Dữ liệu | Vài dòng thử, mã giả HH0001 | 46 sự cố, 174 giao dịch kho, 107 dòng chi phí — **toàn bộ giả định** |
| Công thức | Hầu như không có (cột ghi *Công thức* nhưng nhập tay); Tổng XNT là giá trị dán | Tra cứu đầy đủ, tự tính tồn, tiến độ, thiệt hại, điểm NCC |
| Mã | ISC + sự cố con `.1` + mã xử lý lại `-1` hoặc `XYC` | ISC / IYC thống nhất, bỏ sự cố con |
| Chi phí | 2 lớp: dự trù (gửi KD, KD chấp nhận / không) + thực tế, phiếu in dự trù | 1 lớp, không còn phiếu dự trù, không còn bước KD xác nhận |
| Khách hàng | Có khối thông tin tại khách (đã bán theo lô, tồn tại khách, thu hồi HĐ) | Chỉ còn *Kho KH lỗi* và *Khách tự xử lý* |
| Duyệt xử lý lại | Đủ 7 nhóm duyệt như đơn hàng (chép từ tệp NHÁP điều phối) | Chỉ theo dõi tiến độ, SL đạt / hao hụt, hạn cam kết |
| Theo dõi lùi date | Có sheet (trống) | Không có (chỉ là hướng cải tiến) |

Trùng: DATA (danh mục), cấu trúc Tổng hợp / Tiến độ / Yêu cầu xử lý lại / Nhập xuất / Tổng XNT; 4 dòng Tổng XNT giống hệt. Danh sách yêu cầu ở *SỐ NGÀY LƯU KHO LỖI NCC GC* (cũ) tương ứng *Trang tính1* (mới).

Nên giữ: **BC SỰ CỐ SX làm khung chuẩn** (đầy đủ, có kiểm tra, đã đối chiếu đủ yêu cầu). Cần bù từ bản cũ: (a) lớp chi phí dự trù gửi KD và bước KD xác nhận; (b) khối thông tin tại khách hàng; (c) quy tắc sự cố con; (d) theo dõi đơn lùi date; (e) 3 trạng thái hoàn thành *Đã đổ thu BTP / Khách tự xử lý / Trả trừ công nợ*. Xóa dữ liệu giả định trước khi dùng. Bản cũ nên lưu trữ, không nhập tiếp.

### 4.2. Điều phối: BC ĐP THÀNH PHẨM và Bản sao ĐIỀU PHỐI (NHÁP)

| Tiêu chí | ĐIỀU PHỐI (NHÁP) | BC ĐP THÀNH PHẨM |
|---|---|---|
| Vai trò | Sổ vận hành: nhập đơn, duyệt 7 nhóm, gửi NCC, nhập xuất, phiếu in, danh mục NCC | Chỉ báo cáo KPI tháng / quý / năm |
| Phạm vi | 65 + 86 cột, đơn vị chai/gói | 10 cột nhập, đơn vị thùng |
| Tình trạng | Nhiều #REF! / #N/A (sheet danh mục đã bỏ, cột khóa mất), mã trạng thái không khớp | Công thức gọn, dùng tên vùng, có hướng dẫn rõ |
| Dữ liệu | 3 PO ví dụ | Cùng 3 PO ví dụ (chép lại, đổi sang thùng) |

Quan hệ: không thay thế nhau. BC ĐP được thiết kế để **import** cột A–J từ sheet ĐIỀU PHỐI của tệp NHÁP (*chạy imp từ SHEET ĐIỀU PHỐI*) và thay DANH MỤC bằng Data 1 khi chốt. Phần mới chỉ có ở BC ĐP: dung sai ±5%, số ngày lệch / tỷ lệ trễ, cơ cấu sớm-đúng-trễ, so cùng kỳ, tồn kho cuối tháng theo kho. Phần trùng: NHẬP-XUẤT TP và SỰ CỐ TP (bản rút gọn). Nên giữ cả hai nhưng: NHÁP là sổ gốc (cần sửa lỗi công thức), BC ĐP là báo cáo; **bỏ sheet SỰ CỐ TP của BC ĐP**, lấy sự cố từ BC SỰ CỐ SX để tránh hai nơi ghi sự cố.

---

## 5. Trùng lặp với các tệp khác

| Nội dung | Có ở | Trùng với |
|---|---|---|
| Danh mục dùng chung (công ty nội bộ, kho, loại nhập / xuất / tồn, khoản mục chi phí, ĐVT, hình dạng, màu, phân loại SP, dòng V) | NHÁP / Data1; Sự cố sản xuất / DATA | DRIVE ĐẦU VÀO SX / Admin; Pháp Lý sản xuất / DATA 1 (cùng dòng nguồn *Chưa xác định / Nhập tay / Lấy từ Misa*) |
| Thông tin NCC GC (15 NCC: tên, nhóm SP được SX, MST, địa chỉ, giờ làm việc, báo trước nhận hàng, ĐP phụ trách) | NHÁP / Thông tin NCC(Data1); DS NHẬN HÀNG | DRIVE ĐẦU VÀO SX / Data TP (cùng tiêu đề); QUY TRÌNH SẢN XUẤT / 17. TT NCC GC |
| Danh sách NCC + kho | BC ĐP / DANH MỤC; BC SỰ CỐ SX / Danh mục | Data1 (BC ĐP ghi rõ *thay bằng DATA 1*) |
| Danh mục mã hàng (mã, tên, tên pháp lý, thương hiệu, NCC, QC thùng, giá vốn) | BC SỰ CỐ SX / Mã hàng | DRIVE ĐẦU VÀO SX / Data HH; Drive QL Giá vốn |
| 7 nhóm duyệt đơn (Pháp lý, Sự cố, NL/BTP, VTBB, QLDL, Giá vốn, QLSX) | NHÁP / DUYỆT ĐƠN HÀNG, YÊU CẦU XỬ LÝ LẠI; Sự cố sản xuất / YÊU CẦU ĐP XLY LẠI | Pháp Lý sản xuất / 4. DUYỆT ĐƠN HÀNG (cột *Chạy công thức từ AX/AY*) |
| Sự cố liên quan pháp lý | Tổng hợp sự cố | Pháp Lý sản xuất / 3. SỰ CỐ (*Chạy từ sự cố*) |
| Trường hợp sự cố trong SX, quy trình xử lý | 2 tệp sự cố | QUY TRÌNH SẢN XUẤT / 11. QT XL SỰ CỐ TRONG SX, 12. QT XL SỰ CỐ SAU SX, TH sự cố trong SX |
| Tiêu chí đánh giá NCC GC | BC SỰ CỐ SX / BC NCC GC (điểm theo sự cố) | QUY TRÌNH SẢN XUẤT / 19. TIÊU CHÍ ĐÁNH GIÁ NCC GC; ĐÁNH GIÁ ĐỊNH KÌ NCC GC.xlsx |
| Kho lỗi / kho VTBB tại NCC | Nhập xuất (NCC GC) | BC VTBB (nhóm tồn Thực tế / Tạm / Lỗi) |
| Mẫu biểu, phiếu in | GỬI ĐƠN NCC, DS NHẬN HÀNG, P.NHẬP KHO TP, P.XUẤT BÁN HÀNG | QUY TRÌNH SẢN XUẤT / 14. MẪU BIỂU |
| Yêu cầu xử lý lại | NHÁP / YÊU CẦU XỬ LÝ LẠI | Sự cố sản xuất / YÊU CẦU ĐP XLY LẠI (giống hệt, cùng dòng ví dụ Yamato / HH3949 / NOFADA 822WP) |

---

## 6. Đối chiếu ERP (ước lượng)

Đã kiểm nhanh mã ERP: `inventory` (tồn theo công ty × kho × mã hàng, giá bình quân gia quyền, phát sinh chỉ có loại `gr` nhập từ nhận hàng và `adjust`); `goods_receipt` (nhận hàng theo đợt giao, có `qc_result` *Đạt / Thiếu / Lỗi*); `supplier` (có `inspection_days`, `return_days`, `invoice_deadline`).

| Nghiệp vụ Excel | ERP hiện có | Khớp / thiếu |
|---|---|---|
| KD lên đơn sản xuất (ĐIỀU PHỐI) | YCMH → ĐMH | Khớp phần *đơn mua*; thiếu khái niệm **đơn gia công**: NCC GC, ngày yêu cầu sẵn kho, SL mẫu Lab, cấu thành nội bộ / thuế, NVL khách mang qua, mã BDM |
| Duyệt 7 nhóm trong phòng SX | Luồng duyệt YCMH / ĐMH (người duyệt theo chặng) | Khớp cơ chế duyệt; thiếu duyệt **song song nhiều nhóm có dữ liệu riêng** (ngày đủ NL/BTP, mã BDM, dòng hóa đơn, chính sách giá) và điều kiện *đủ điều kiện NB* |
| Gửi đơn NCC GC, phiếu đơn SX | In / xuất ĐMH | Thiếu mẫu đơn SX có công thức, màu BTP, VTBB, cột ẩn với NCC |
| Theo dõi NCC SX (trạng thái, ngày dự kiến, SL thực SX, dung sai, cảnh báo trễ) | Tiến độ mua hàng (`purchase_progress`) | Một phần; thiếu trạng thái SX, ngày NCC SX xong, dung sai ±%, số ngày lệch, cờ gấp |
| Nhận hàng nhiều lần, KCS | Nhận hàng nhiều đợt + `qc_result` | Khớp khung; thiếu **số lô, NSX, HSD**, phụ kiện, ngoại dạng, khớp chứng từ, SL đạt / không đạt, kết quả Lab |
| Nhập kho TP, tồn kho | Kho: phiếu nhập từ nhận hàng, tồn theo kho × mã | Khớp nhập; thiếu **xuất kho, chuyển kho, trả hàng, xuất xử lý / nhập sau xử lý**, tồn theo lô / HSD, **tồn tại kho NCC GC**, kho lỗi theo trạng thái |
| Xuất bán cho công ty nội bộ | Chưa có | Thiếu hẳn phiếu đề nghị xuất bán / xuất kho |
| Danh mục NCC, lịch sử thay đổi | `supplier` (tên viết tắt, MST, địa chỉ, liên hệ, ngân hàng, ngày kiểm hàng, ngày đổi trả) | Khớp phần lớn; thiếu nhóm SP được phép SX, địa chỉ kho, giờ làm việc, thời gian báo trước, ĐP phụ trách, **lịch nghỉ lễ**, nhật ký thay đổi có hiệu lực |
| Hợp đồng / chính sách giá NCC GC | Hợp đồng | Khớp; mã số chính sách giá chưa liên kết vào đơn |
| Chi phí sự cố thu từ NCC (cấn trừ công nợ / thu tiền) | Công nợ, đề nghị thanh toán | Khớp đích đến; thiếu bút toán **cấn trừ công nợ do sự cố**, phân bổ chi phí theo đối tượng |
| Ghi nhận sự cố, GĐ1 yêu cầu BP, GĐ2 xử lý lại, kho lỗi, chi phí, điểm NCC | Chưa có phân hệ; có Ticket / Công việc dùng chung | Thiếu hẳn. Có thể tận dụng: `supplier_scorecard` (đã có công cụ MCP chấm NCC) để nhận điểm sự cố; Công việc / Ticket cho yêu cầu BP có hạn |
| Báo cáo KPI điều phối và sự cố | Báo cáo / dashboard mua hàng | Thiếu toàn bộ KPI SX |

Khuyến nghị thứ tự nếu đưa lên ERP: (1) mở rộng nhận hàng có lô / NSX / HSD / KCS; (2) kho có xuất, chuyển kho, kho NCC GC, kho lỗi; (3) phân hệ sự cố theo khung BC SỰ CỐ SX (mã ISC / IYC, sổ nhập xuất trạng thái là lõi); (4) đơn gia công + duyệt nhiều nhóm; (5) báo cáo KPI.

---

## 7. Câu hỏi / mâu thuẫn

**Mã và quy tắc**

1. Mã đơn đặt hàng: BC SỰ CỐ SX ghi *ATP + 6 số* (`ATP050706`), nhưng ĐIỀU PHỐI dùng `ITP26082611`, `ATP03092611` (tiền tố + ddmmyy + 2 số). Tiền tố I / A nghĩa là gì (IDA / ABA?) — ví dụ `ITP...` lại thuộc thương hiệu ABA và BAMBOO.
2. Mã xử lý lại có 3 kiểu: `IYC.ddmmyy+stt` (bản mới), `ISC.2507262-1` (NHÁP, Tổng hợp cũ), `XYC.09012607` (*TH + YC*). Chốt kiểu nào? Có giữ *sự cố con* `ISC.xxx.1` không?
3. Tiền tố `ISC` có phải cố định cho mọi thương hiệu không (quy tắc cũ *TH + YC* gợi ý đổi theo thương hiệu)?

**Công thức sai / hỏng (tệp NHÁP)**

4. Mã trạng thái nhập xuất không khớp: danh sách là *1.NHẬP TP / 2.NHẬP MẪU / 4.CHUYỂN KHO / 5.TRẢ HÀNG*, nhưng công thức ĐIỀU PHỐI tìm *1.NHẬP KHO NCC*, *2.NHẬP KHO MẪU NCC*, *5.CHUYỂN KHO*; P.NHẬP KHO TP tìm *1.NHẬP KHO*. Kết quả: *TC SL NCC thực SX* cộng cả chuyển kho (ví dụ 10.009 so với 5.002 gửi NCC → báo sai *SX VƯỢT ĐH*), *SL đã nhận về* luôn 0.
5. *Đủ điều kiện NB (7 BP)* chỉ kiểm 6 nhóm (thiếu Sự cố); nhóm Giá vốn đòi *Đã xử lí giá* trong khi dữ liệu ghi *Duyệt* → không đơn nào đủ điều kiện.
6. Tham chiếu sheet đã xóa: *Danh mục TP + NCC GC (chờ data 1 chỉnh lại form BỎ)*, *PHIẾU ĐỀ NGHỊ NHẬP KHO* → #REF! ở kiểm NCC đúng / sai, BC TỒN KHO TẠI NCC GC, P.NHẬP KHO TP, P.XUẤT BÁN HÀNG.
7. MỤC LỤC: dòng P.XUẤT BÁN HÀNG trỏ link về P.NHẬP KHO TP; *Thông tin NCC & MOQ* nhưng sheet không có cột MOQ; MỤC LỤC BC SỰ CỐ SX liệt kê sheet *Giá vốn* nhưng không có (giá vốn nằm ở *Mã hàng*).
8. HSD cố định NSX + 2 năm — có đúng cho mọi sản phẩm không, hay phải lấy theo đăng ký từng SP?

**Quy trình**

9. Trạng thái đơn: họp 07/10 chốt 7 trạng thái và *Bỏ* 12 trạng thái cũ, nhưng dropdown ĐIỀU PHỐI vẫn dùng trạng thái cũ (ví dụ *Hàng sẵn kho*). Cần dọn.
10. Đơn vị: ĐIỀU PHỐI theo chai/gói, BC ĐP theo thùng. Dung sai ±5% tính trên thùng hay chai? Hàng *dư* quá dung sai xử lý thế nào (MỤC NHẬP-XUẤT: chấp nhận thì nhập kho, KD chưa nhận thì chuyển sự cố)?
11. KCS: lỗi phát hiện sau bao nhiêu ngày kể từ nhận hàng thì còn quy trách nhiệm NCC GC? (ERP có sẵn `inspection_days` / `return_days` ở NCC.)
12. Chi phí dự trù gửi KD (*Hạo*): *Hạo* là tên người hay cách gọi chi phí dự trù? Bản mới bỏ bước KD xác nhận chấp nhận / không chấp nhận chi phí — có cố ý không?
13. Sự cố có hai nơi ghi: SỰ CỐ TP (BC ĐP, theo thùng, theo kho) và Tổng hợp sự cố (BC SỰ CỐ SX). Chốt một nơi.
14. *Số ngày lưu kho lỗi tại NCC GC* và *chi phí lưu kho sự cố* được yêu cầu (bản cũ) nhưng bản mới chưa có quy định số ngày được lưu kho miễn phí (DRIVE ĐẦU VÀO / Data NCC GC có cột *Số ngày được lưu kho* — nên nối vào).
15. BC SỰ CỐ SX dùng NCC *Việt Thắng*, *Đại Phát* không có trong danh sách 15 NCC GC thật; *An Nông* có trong yêu cầu đối tượng chịu nhưng chưa có trong danh mục NCC của báo cáo.
16. *SL thùng mua* (mẫu số % lỗi theo thùng) và *SL Dr Xanh giao thực tế* chưa có nguồn — ai nhập, lấy từ đâu (NHẬP-XUẤT TP của ĐP TP?).
17. Quà tặng NCC: cần ngưỡng giá trị / quy định khai báo không, và ai nhập (ĐP TP hay mỗi BP)?
18. Thời gian báo trước khi nhận hàng của 15 NCC đều trống — cần bổ sung vì dùng khi hẹn lấy hàng.

**Dữ liệu cá nhân**: các danh mục Data1 / DATA / DS NHẬN HÀNG chứa số điện thoại người liên hệ kho NCC và tên giám đốc / chủ cơ sở; ghi chú này chỉ nêu tên trường, không chép giá trị.
