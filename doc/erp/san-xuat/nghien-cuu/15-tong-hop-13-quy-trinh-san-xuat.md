# Tổng hợp 13 quy trình con của phòng Sản xuất và lộ trình đưa vào ERP

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 26/11/2026 | NSU209 (A1 Điều phối) | Nháp, chờ phòng Sản xuất chốt câu hỏi | — |

Nguồn: thư mục `tailieusanxuat` phòng Sản xuất gửi ngày 26/11/2026 (23 tệp Excel xuất từ Google Sheets, 318 sheet; tệp
zip kèm theo là bản trùng của chính 23 tệp đó). Bốn tệp chi tiết đi kèm tệp này:

| Tệp | Nội dung | Tệp nguồn |
|---|---|---|
| [16-khung-quy-trinh-va-phap-ly-san-xuat.md](16-khung-quy-trinh-va-phap-ly-san-xuat.md) | Từng bước QT1–QT13, danh mục dữ liệu đầu vào, pháp lý sản phẩm / NCC | QUY TRÌNH SẢN XUẤT 09.07.2026, DRIVE ĐẦU VÀO SX, Pháp Lý sản xuất (47 sheet) |
| [17-ncc-gia-cong-va-quan-ly-du-lieu.md](17-ncc-gia-cong-va-quan-ly-du-lieu.md) | Đưa NCC GC vào hợp tác, đánh giá định kỳ, ngưng hợp tác, đầu vào QLDL, duyệt đơn, BĐM thành phẩm | Checklist / đánh giá NCC GC, Drive QLDL 1–4 (84 sheet) |
| [18-gia-von-mua-hang-cong-no-ton-kho.md](18-gia-von-mua-hang-cong-no-ton-kho.md) | Tính giá vốn, khảo sát giá, mua NL / BTP / VTBB, công nợ, đối chiếu tồn, báo cáo VTBB | Drive QL Giá vốn 1–4, Drive QLDL 5–8, BC VTBB (119 sheet) |
| [19-dieu-phoi-thanh-pham-va-su-co.md](19-dieu-phoi-thanh-pham-va-su-co.md) | Điều phối đơn thành phẩm gửi NCC GC, nhận hàng, KCS; sự cố sản xuất và chỉ số | Điều phối thành phẩm, BC SỰ CỐ SX, Sự cố sản xuất (68 sheet) |

Mỗi tệp chi tiết có: bảng kiểm kê từng sheet, các bước từng quy trình, trường dữ liệu, chỗ trùng lặp giữa các tệp, đối
chiếu ERP (ước lượng) và danh sách câu hỏi / mâu thuẫn cần phòng Sản xuất trả lời. Đọc kèm bộ tài liệu cũ 09–14 (khảo sát
MIC và quy trình bàn giao).

## 1. Nhận xét chung về bộ tài liệu

- **Phần lớn là bản thiết kế biểu mẫu, chưa phải sổ đang chạy.** Đa số sheet chỉ có khung và 1–10 dòng ví dụ; nhiều liên
  kết vỡ (`#REF!`, `#N/A`) do chép từ Google Sheets. Dữ liệu thật chỉ có ở vài chỗ: báo cáo VTBB (2.226 giao dịch, khoảng
  6.158 mã), pháp lý sản phẩm (369 dòng, 262 tên pháp lý), tồn kho NCC (59 dòng BTP), công nợ TP đóng gói (khoảng 438 dòng).
- **Chép qua chép lại nhiều.** Cùng một danh mục (Admin / Data1 / DATA 1, thông tin NCC GC, hợp đồng, BĐM, LSX) có mặt ở
  3–6 tệp; một đơn hàng xuất hiện ở 5–6 sheet. Khi đưa vào ERP chỉ cần **một** nguồn cho mỗi danh mục.
- **Sự cố sản xuất có khung đầy đủ nhất nhưng toàn số liệu giả định**; quy trình ngưng hợp tác NCC (bản v11) là quy trình
  viết hoàn chỉnh nhất.
- **Lỗi kỹ thuật cần biết nếu nạp máy:** số bước bị Excel đổi thành ngày (bước 2.1 hiện 02/01/2026); tệp điều phối nháp có
  công thức sai tên trạng thái làm số NCC thực sản xuất cộng cả hàng chuyển kho; điều kiện *đủ điều kiện duyệt* chỉ kiểm 6/7
  nhóm.

## 2. Bảng 13 quy trình

| # | Quy trình | Chủ trì | Mức hoàn thiện tài liệu | Dữ liệu thật | ERP hiện có | Phần ERP chưa có |
|---|---|---|---|---|---|---|
| QT1 | Làm việc với NCC mới | QLDL | Hoàn thành | Ít | Nhà cung cấp, hợp đồng (khung) | Checklist NCC GC mới, test mẫu, nhóm làm việc |
| QT2 | Khai báo dữ liệu sản xuất (mã hàng, NCC GC, quy tắc mã) | QLDL | Cần kiểm lại | Có một phần | Sản phẩm, NCC, kho | Quy tắc mã SX (NLNK, BTPR, HH...), đồng bộ mã Dego - NCC, thuộc tính SX của mã |
| QT3 | Khảo sát và tính giá vốn | Giá vốn | Có công thức, bảng chưa chạy | Gần như không | YCBG, sổ giá, Giá NVL sản xuất (chi phí bao bì) | Giá vốn đầy đủ BTP + VTBB + phí gia công, phiếu duyệt giá ba mức, cảnh báo biên |
| QT4 | Quản lý đơn hàng sản xuất gia công | ĐP thành phẩm | Có khung, 3 đơn ví dụ | Không | ĐMH (chỉ cho mua hàng) | Đơn gia công gửi NCC GC, duyệt 7 bộ phận, tiến độ NCC, nhận hàng có lô / HSD / KCS |
| QT5 | Pháp lý sản xuất, duyệt pháp lý đơn | Pháp lý SX | Có | **Có (369 dòng)** | Không | Hồ sơ pháp lý sản phẩm / NCC, cảnh báo 180 ngày, duyệt pháp lý đơn, chuỗi pháp nhân hóa đơn |
| QT6 | Quản lý NCC gia công, đánh giá định kỳ | QLDL | Khung 21 tiêu chí, chưa chạy kỳ nào | Không | Chấm điểm NCC thu mua (tự tính) | Phiếu chấm nhiều bộ phận, xếp loại 90 / 75 / 60, chu kỳ 6 tháng |
| QT7 | Bảng định mức thuế | QLDL / Giá vốn | Ngắn | Ít | Không | BĐM cấu thành thuế theo từng công ty |
| QT8 | Quản lý nguyên liệu / bán thành phẩm | ĐP NL/BTP | Có | Có một phần | YCMH, ĐMH, nhận hàng, tồn kho | Phối BTP, lệnh sản xuất, BĐM BTP (NL / 1.000 kg theo hàm lượng), kho tại NCC GC |
| QT9 | Quản lý vật tư bao bì | ĐP VTBB | Có, báo cáo có công thức đủ | **Có (2.226 giao dịch)** | YCMH, ĐMH, tồn kho, Giá NVL sản xuất (định mức bao bì, sổ giá) | Min / MOQ và số đề xuất đặt, hao hụt, tồn lâu, cọc nhãn, kho tại NCC |
| QT10 | Đặt dịch vụ vận chuyển (Grab) | ĐP thành phẩm | Ngắn | Ít | Đặt xe (xe công ty) | Grab, tạm ứng, phân bổ phí theo thương hiệu |
| QT11 | Xử lý sự cố trong sản xuất | ĐP thành phẩm | Cần kiểm lại | Giả định | Không | Phân hệ sự cố |
| QT12 | Xử lý sự cố sau sản xuất | NV xử lý sự cố | Đang gộp | Giả định | Không (có ticket chung) | Phân hệ sự cố, chi phí và trách nhiệm, kho lỗi, chỉ số NCC |
| QT13 | Dừng làm việc với NCC GC | QLDL + các bộ phận | **Hoàn chỉnh nhất (v11)** | Không | Hợp đồng có trạng thái *thanh lý* | Phiếu 10 bộ phận, so chi phí hai phương án, chuỗi biên bản, xác nhận công nợ bằng 0 |

## 3. Luồng dữ liệu giữa các quy trình

```
QT1 NCC mới ─► QT2 Khai báo dữ liệu (mã hàng, NCC GC, BĐM) ─┬─► QT3 Giá vốn ─────────┐
                                                             ├─► QT5 Pháp lý ────────┤
QT8 NL/BTP (mua qua Thu mua, phối, LSX) ─────────────────────┤                       ▼
QT9 VTBB (mua qua Thu mua, tồn, Min/MOQ) ────────────────────┴─► QT4 Đơn hàng gia công (duyệt 7 bộ phận:
                                                                  pháp lý, sự cố, NL/BTP, VTBB, QLDL, giá vốn, QLSX)
                                                                   │  gửi NCC GC ─► NCC sản xuất ─► KCS, nhận hàng
                                                                   ▼
                                                     Kho thành phẩm ─► xuất bán (Kinh doanh)
                                                                   │
                                     QT11 / QT12 Sự cố ◄───────────┘ ─► chi phí, trách nhiệm ─► QT6 đánh giá NCC ─► QT13 dừng NCC
Thu mua (ERP: YCMH, YCBG, ĐMH, nhận hàng, công nợ, YCTT) cung cấp NL / BTP / VTBB cho QT8, QT9.
```

## 4. Nên bắt đầu từ đâu (đề xuất)

Tiêu chí xếp: (1) quy trình khác phụ thuộc vào nó, (2) có dữ liệu thật để dùng ngay, (3) nằm sát phần ERP đã có nên làm
nhanh, (4) giảm việc chép tay giữa các tệp.

| Đợt | Làm gì | Vì sao |
|---|---|---|
| **0. Chốt nghiệp vụ** | Phòng Sản xuất trả lời các câu hỏi chặn ở tệp 16–19: quy tắc mã (sự cố, PO, mã SX), đơn vị tính (thùng hay chai), hệ số 1,05 / 1,08 trong giá vốn, giá vốn trước hay sau VAT, nguồn chuẩn của hao hụt | Không chốt thì làm phần nào cũng phải sửa lại |
| **1. Nền dữ liệu (QT2, một phần QT1, QT6)** | Mở rộng Sản phẩm (thuộc tính sản xuất, quy tắc mã, đồng bộ mã Dego - NCC), hồ sơ NCC gia công (nhóm sản phẩm được phép, chính sách lưu kho, hao hụt, MOQ), **kho tại NCC GC**; mở rộng **định mức bao bì** đang có thành BĐM thành phẩm (thêm loại thành phần NL/BTP ruột, phí gia công, bên cung ứng) — bảng thành phần có cột loại vừa làm ở duoc-CR-784 dùng tiếp được | Mọi quy trình sau đều đọc từ đây; hiện danh mục bị chép ở 3–6 tệp |
| **2. Thắng nhanh, có dữ liệu thật (QT5, QT9)** | **Pháp lý sản phẩm**: danh mục hồ sơ + cảnh báo hết hạn 180 ngày (nạp ngay 369 dòng; hiện đã có 74 hợp quy và 43 GĐK quá hạn). **VTBB**: tồn thực tế / tạm / lỗi, Min / MOQ, số đề xuất đặt rồi **sinh YCMH sang Thu mua** | Dùng được ngay, rủi ro thấp, nối thẳng vào kho + YCMH + Giá NVL sản xuất đã có |
| **3. Lõi sản xuất (QT4, QT8)** | **Đơn hàng gia công**: Kinh doanh lên đơn, duyệt 7 bộ phận, gửi NCC GC, theo dõi tiến độ, KCS, nhận hàng có lô / ngày sản xuất / HSD, nhập kho thành phẩm; phối BTP, lệnh sản xuất, xuất kho cho NCC | Là trái tim của phòng Sản xuất, nhưng cần đợt 1–2 làm nền |
| **4. Mở rộng (QT3, QT11–QT12, QT13, QT7, QT10)** | Giá vốn đầy đủ (dựa BĐM + sổ giá), phân hệ sự cố (theo khung BC SỰ CỐ SX), đánh giá và dừng NCC, BĐM thuế, vận chuyển (dùng lại Đặt xe) | Cần dữ liệu đơn hàng và BĐM thật mới tính đúng |

**Điểm bắt đầu đề xuất:** đợt 0 song song với hai việc nhỏ của đợt 2 là **Pháp lý sản phẩm** và **đề xuất đặt VTBB**:
có dữ liệu thật, đứng riêng được, cho phòng Sản xuất thấy kết quả sớm; trong lúc đó dựng nền đợt 1.

## 5. Tên gọi cho cả chuỗi Thu mua - Sản xuất - Kho

Chuỗi *mua nguyên vật liệu → sản xuất (gia công) → nhập kho thành phẩm → giao bán* trong ERP gọi chung là **Chuỗi cung ứng**
(*Supply Chain Management*, SCM). Các hệ ERP lớn (SAP, Odoo, Oracle) đều gom Mua hàng, Sản xuất, Kho vào nhóm này; mô hình
chuẩn SCOR chia thành *Lập kế hoạch - Mua (Source) - Sản xuất (Make) - Giao hàng (Deliver)*.

Đề xuất cho DEGO:

| Cấp | Tên | Gồm |
|---|---|---|
| Nhóm phân hệ | **Chuỗi cung ứng** (SCM) | ba phân hệ dưới |
| Phân hệ | **Thu mua** (Procurement) | YCMH, YCBG, ĐMH, công nợ, YCTT, Giá NVL sản xuất (đang có) |
| Phân hệ | **Sản xuất gia công** (Subcontract Manufacturing) | BĐM, đơn gia công, điều phối thành phẩm, pháp lý sản xuất, sự cố, đánh giá NCC GC |
| Phân hệ | **Kho** (Inventory) | Nhập, xuất, chuyển kho, tồn theo kho kể cả kho tại NCC GC, lô / HSD, kiểm kê |

Gọi rõ *gia công* vì DEGO không tự sản xuất: mọi thành phẩm do NCC gia công làm, DEGO cấp nguyên liệu / bao bì và nhận
thành phẩm.
