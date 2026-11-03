# YÊU CẦU CHỨC NĂNG — SẢN XUẤT

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Đọc trước:** phân hệ còn ở giai đoạn nghiên cứu, **chưa có tài liệu yêu cầu đã chốt, chưa có dòng mã**. Danh sách dưới
là các chức năng **đề xuất** rút từ tài liệu nghiên cứu và khảo sát Phòng Sản xuất, để làm khung cho bản yêu cầu sau này —
chưa phải phạm vi đã duyệt. Phạm vi chỉ chốt được sau khi trả lời 15 câu ở [`10`](10-tong-quan-nghiep-vu.md) §14 (việc SX1-1
của [kế hoạch theo module](../../../plans/00-ke-hoach-theo-module.md) §12). Mọi dòng trạng thái là **Chưa**.

## 1. Người dùng và vai trò

Chưa có mã vai trò trong hệ thống. Bộ máy hiện tại theo khảo sát ([`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §2):

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Trưởng phòng Sản xuất (chưa có mã) | Quyết cuối đơn thiếu điều kiện, duyệt chi phí phát sinh, ký phiếu duyệt giá, chủ trì tìm NCC GC mới |
| Điều phối thành phẩm (chưa có mã) | Nhận đơn từ Kinh doanh, gửi NCC, theo dõi tiến độ, nhận hàng |
| Điều phối vật tư bao bì (chưa có mã) | Kiểm tồn bao bì, duyệt mẫu, lập phiếu đề nghị mua khi thiếu |
| Điều phối nguyên liệu / bán thành phẩm (chưa có mã) | Lập phiếu điều chuyển hoặc phối trộn nguyên liệu |
| Nhóm Quản lý dữ liệu: giá vốn, pháp lý và sự cố, hồ sơ và dữ liệu NCC (chưa có mã) | Lập phiếu duyệt giá; kiểm giấy phép, hợp đồng; xử lý hàng lỗi; gom chứng từ, đối chiếu công nợ |
| Ngoài phòng: Kho, Lab, Kế toán sản xuất, Phòng Kinh doanh | Nhận hàng; kiểm mẫu; quyết toán; đặt hàng |

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-SX-01 | Đơn gia công tại NCC GC, theo dõi sáu bước từ nhận yêu cầu tới hoàn thiện chứng từ — [`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §3; [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §5.2, §7 dòng 1; [`10`](10-tong-quan-nghiep-vu.md) §10.1 | Điều phối thành phẩm, Trưởng phòng | chưa có | Chưa | — |
| CN-SX-02 | Kiểm điều kiện triển khai đơn (nguyên liệu, bao bì, pháp lý, giá vốn) và duyệt song song nhiều bộ phận trước khi gửi NCC — [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 7; [`05`](../nghien-cuu/05-san-xuat-van-ban-thong-nhat.md) mục B bước 2 | Các điều phối, Quản lý dữ liệu, Trưởng phòng | chưa có | Chưa | — |
| CN-SX-03 | Phiếu duyệt giá ba mức kèm định mức (giá thành dự toán theo đơn) — [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 6 | Giá vốn, Trưởng phòng | chưa có | Chưa | — |
| CN-SX-04 | Kho tại NCC GC, phiếu xuất vật tư gửi gia công, đối chiếu xuất nhập tồn VTBB với NCC — [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 1–2 | Điều phối, Kho, Hồ sơ | chưa có | Chưa | — |
| CN-SX-05 | Giấy đề nghị nhập kho thành phẩm có người xác nhận — [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 3 | Điều phối, Kho, Kế toán | chưa có | Chưa | — |
| CN-SX-06 | Mức tồn an toàn tối thiểu và lượng đặt tối thiểu cho VTBB — [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 4 | Điều phối VTBB | chưa có | Chưa | — |
| CN-SX-07 | Sản xuất lập Yêu cầu mua hàng thẳng trên ERP khi thiếu VTBB — [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 5 | Điều phối VTBB | YCMH của Thu mua | Chưa | — |
| CN-SX-08 | Bộ hồ sơ đơn gia công: danh mục 11 loại chứng từ, đánh dấu đủ / thiếu — [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 9 | Hồ sơ sản xuất | chưa có | Chưa | — |
| CN-SX-09 | Xử lý sự cố / hàng lỗi: năm bước, bốn cách kết thúc (chấp nhận, bắt NCC làm lại, hủy và cấn trừ, chờ ý kiến) — [`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §3; [`10`](10-tong-quan-nghiep-vu.md) §9 | Quản lý dữ liệu, Trưởng phòng | chưa có | Chưa | — |
| CN-SX-10 | Làm việc với NCC GC mới: bảy bước, Giám đốc công ty duyệt bằng văn bản — [`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §3; [`05`](../nghien-cuu/05-san-xuat-van-ban-thong-nhat.md) mục B | Trưởng phòng, Giám đốc | chưa có | Chưa | — |
| CN-SX-11 | Pháp nhân nhận hóa đơn trên mọi chứng từ sản xuất — [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 8 | Mọi vai trò | Mọi chứng từ | Chưa | — |
| CN-SX-12 | Định mức nguyên liệu (BOM) nhiều cấp, phiên bản, hiệu lực theo ngày; bảng sản phẩm cha làm nền — [`10`](10-tong-quan-nghiep-vu.md) §2.2, §10.4, §13; kế hoạch SX1-3, SX2-1 | Giá vốn, kế hoạch | chưa có | Chưa | — |
| CN-SX-13 | Lệnh sản xuất, công đoạn, báo cáo công đoạn; loại phiếu kho xuất sản xuất, nhập thành phẩm, trả vật tư, xuất hủy — [`10`](10-tong-quan-nghiep-vu.md) §4, §13.2; kế hoạch SX2-1 | Kế hoạch, Kho | chưa có | Chưa | — |
| CN-SX-14 | Danh mục kho thật, giữ chỗ tồn kho, lô và hạn dùng — [`10`](10-tong-quan-nghiep-vu.md) §13.2; kế hoạch SX2-2 | Kho | chưa có | Chưa | — |
| CN-SX-15 | Kiểm tra chất lượng ba chặng IQC, IPQC, FQC và phiếu NCR — [`10`](10-tong-quan-nghiep-vu.md) §4, §9 | Lab, QC | chưa có | Chưa | — |
| CN-SX-16 | Giá thành: đánh giá dở dang, phân bổ chi phí chung theo công suất bình thường, giá chuẩn / thực tế — [`10`](10-tong-quan-nghiep-vu.md) §5–§8; kế hoạch SX3-1 | Kế toán giá thành | chưa có | Chưa | — |
| CN-SX-17 | Hoạch định vật tư và năng lực (MRP, CRP), Routing — [`10`](10-tong-quan-nghiep-vu.md) §4; kế hoạch SX3-2 | Kế hoạch | chưa có | Chưa | — |
| CN-SX-18 | Bảng điều khiển Sản xuất có biểu đồ thật (số lệnh, sản lượng, hàng lỗi) — kế hoạch SX2-3 | Trưởng phòng | Tổng quan Sản xuất | Chưa | — |

## 3. Chi tiết từng chức năng

Chỉ ghi điều đã biết từ khảo sát; luật nghiệp vụ chưa chốt.

### CN-SX-01 — Đơn gia công tại NCC GC

- **Mục đích:** đưa việc theo dõi đơn gia công đang nằm trên Google Sheets, Drive và hơn 50 nhóm Zalo vào ERP.
- **Luồng chính (hiện trạng):** Kinh doanh gửi đơn → kiểm điều kiện → chuẩn bị nguồn lực, duyệt giá → gửi NCC, cập nhật
  tiến độ chậm nhất ba ngày một lần → nhận hàng (Kho đếm, Lab kiểm ngoại dạng) → gom 11 loại chứng từ, đối chiếu công nợ,
  bàn giao Kế toán. Chi tiết: [`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §3, [`05`](../nghien-cuu/05-san-xuat-van-ban-thong-nhat.md) mục B.
- **Chưa thống nhất:** quy trình chuẩn sáu hay bảy bước; một hay hai bộ trạng thái; số đơn mỗi ngày hay mỗi tuần
  ([`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §6).
- **Quyền:** chưa có entity; mỗi entity mới phải khai đủ phạm vi ([`10`](10-tong-quan-nghiep-vu.md) §13.3).

### CN-SX-02 — Kiểm điều kiện và duyệt song song

- **Mục đích:** đơn chỉ đi tiếp khi đủ nguyên liệu, bao bì, pháp lý (5 giấy), giá vốn.
- **Luật đã chốt một phần (24/10/2026, Trưởng phòng):** đơn thiếu điều kiện do Trưởng phòng Sản xuất quyết cuối; chi phí
  phát sinh duyệt tới Trưởng phòng; còn cần Kinh doanh và Giám đốc xác nhận ([`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §7).
- **Liên quan:** dùng bộ máy duyệt dùng chung, luồng song song nhiều nhánh ([Nền tảng](../../nen-tang/chuc-nang/01-yeu-cau-chuc-nang.md) CN-NT-08).

### CN-SX-04 — Kho tại NCC GC và đối chiếu VTBB

- **Mục đích:** biết nguyên liệu, VTBB của mình đang nằm ở NCC nào, đối chiếu định mức tiêu hao khi nhận thành phẩm.
- **Hiện trạng:** đối chiếu xuất nhập tồn VTBB với NCC đang làm trên bảng tính ([`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 2).
- **Phụ thuộc:** danh mục kho thật (CN-SX-14); hiện kho chỉ là chuỗi `warehouse_code` ([`10`](10-tong-quan-nghiep-vu.md) §13.2).

### CN-SX-09 — Xử lý sự cố, hàng lỗi

- **Mục đích:** có quy trình và dấu vết khi hàng nhận về sai lệch.
- **Chưa thống nhất:** ai quyết phương án cuối (hai trưởng nhóm cùng được nói là người quyết); Kho hay Lab quyết hàng được
  nhận ([`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §6). Cách hạch toán hàng lỗi ở [`10`](10-tong-quan-nghiep-vu.md) §9.2.

## 4. Luồng trạng thái chứng từ (nếu có)

Chưa có. Ràng buộc: trạng thái lệnh, công đoạn, NCR lưu `SMALLINT` có `IntEnum` ([`10`](10-tong-quan-nghiep-vu.md) §13.3).

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| B1 | Bản đầu chỉ quản lý số lượng hay làm cả giá thành | Đại ca | chưa có |
| C2 | Giá thành chuẩn hay thực tế, kỳ tháng hay quý | Kế toán, ban lãnh đạo | chưa có |
| A3 | Có theo dõi lô và hạn dùng không (C5 danh mục chờ) | Bộ phận sản xuất và kho | chưa có |
| H-A | Bảng RACI: ai quyết cuối theo từng loại vướng mắc | Trưởng phòng, Giám đốc | chưa có |
| H-D | Hạn mức duyệt chi phí 3 triệu và 5 triệu có áp cho phòng Sản xuất không | Trưởng phòng, Giám đốc, Kế toán | chưa có |
| H-K | Ai tính giá thành thực tế sau gia công, theo kỳ hay theo đơn | Kế toán sản xuất, Giá vốn | chưa có |

Đủ 15 câu ở [`10`](10-tong-quan-nghiep-vu.md) §14; câu hỏi lại H-A..H-K ở [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §8;
17 câu chưa thống nhất ở [`05`](../nghien-cuu/05-san-xuat-van-ban-thong-nhat.md) mục C.
