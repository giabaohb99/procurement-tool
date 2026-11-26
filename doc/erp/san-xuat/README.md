# SẢN XUẤT (SX)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

## Phân hệ này là gì

Phân hệ **Quản lý sản xuất** của ERP DEGO: lập kế hoạch, điều phối, theo dõi và kiểm soát việc biến nguyên vật liệu thành
thành phẩm, dùng chung dữ liệu với Mua hàng, Tồn kho, Bán hàng và Kế toán. Theo khảo sát Phòng Sản xuất (19/10–26/10/2026),
DEGO **không tự sản xuất**: toàn bộ là **gia công tại nhà cung cấp (NCC GC)** — DEGO giao nguyên liệu, bán thành phẩm, bao
bì; NCC đóng gói; DEGO nhận thành phẩm về kho. Hiện mới ở **giai đoạn nghiên cứu nghiệp vụ**: chưa có tài liệu yêu cầu
đã chốt, chưa có bảng, chưa có entity quyền. Trên giao diện v2, menu **Sản xuất** hiện chỉ chứa danh mục dùng chung (Nhà
cung cấp, Sản phẩm và Vật tư, Đơn vị tính, Phân loại, Hợp đồng — `frontend-v2/src/modules/production/routes.tsx`); các
danh mục đó thuộc tài liệu của Thu mua và Mặt hàng, không thuộc phân hệ này.

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Nghiên cứu nghiệp vụ chuẩn (Thông tư 99/2025) | Đã có tài liệu | [`10`](nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md), bản 1.0 21/10/2026 |
| Khảo sát hiện trạng Phòng Sản xuất | Đã có tài liệu | [`02`](nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) … [`08`](nghien-cuu/08-san-xuat-cau-tra-loi-trich-duoc-2610.md); còn câu chưa thống nhất |
| Tài liệu yêu cầu (danh sách tính năng) | Đang làm: Sản phẩm (54 tính năng) và Kho (50 tính năng) đã viết 26/11/2026; đơn hàng, sự cố, phần còn lại chưa | [`01`](chuc-nang/01-yeu-cau-chuc-nang.md), [`11`](chuc-nang/11-san-pham.md), [`12`](chuc-nang/12-kho.md); còn chờ trả lời 15 câu ở [`10`](nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md) §14 (việc SX1-1) |
| Mã nguồn (BOM, đơn gia công, lệnh sản xuất, phiếu kho sản xuất) | Chưa làm | [Kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §12 |

## Ba điều quan trọng nhất

1. **Căn cứ là Thông tư 99/2025, không phải Thông tư 200.** Thông tư 200 hết hiệu lực từ 01/01/2026. Số hiệu tài khoản sản
   xuất không đổi, nhưng kế toán phải soát lại tên tài khoản trước khi đưa vào hệ thống.
2. **Chọn giá chuẩn hay giá thực tế trước khi thiết kế bảng.** Hai cách cần hai cấu trúc dữ liệu khác nhau; đổi sau là làm lại.
3. **Phần vượt mức bình thường không bao giờ nằm trong tồn kho.** Hỏng ngoài định mức và chi phí chung cố định khi chạy dưới
   công suất vào thẳng giá vốn trong kỳ; hệ thống phải tách được, nếu không giá trị tồn kho bị thổi phồng.

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Danh sách tính năng (đọc đầu tiên) | [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Sản phẩm: mã hàng, quy tắc, công thức, định mức / BOM | [`chuc-nang/11-san-pham.md`](chuc-nang/11-san-pham.md) |
| Kho: nhập, xuất, tồn, kho tại NCC gia công, đối chiếu | [`chuc-nang/12-kho.md`](chuc-nang/12-kho.md) |
| Chạy tốt cỡ nào, ai được xem gì | [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) (chưa có đường nào) |
| Thiết kế, bảng dữ liệu, bẫy | chưa có; ràng buộc thiết kế ở [`10`](nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md) §13.3 |
| So sánh, khảo sát, câu hỏi chờ chốt | [`nghien-cuu/`](nghien-cuu/) — đọc nhanh [`04`](nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md); câu cần chốt ở [`10`](nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md) §14 |
| Làm phần nào trước (lộ trình phase) | [`plans/261126-lo-trinh-san-xuat-gia-cong/plan.md`](plans/261126-lo-trinh-san-xuat-gia-cong/plan.md) |
| Kế hoạch đang làm / đã xong | [`plans/`](plans/); việc cũ ở [kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §12 (SX1-x, SX2-x, SX3-x) |
| Kịch bản kiểm thử tay | chưa có |
| Hướng dẫn người dùng | chưa có |

Đọc theo vai:

- **Người quyết:** đọc [`10`](nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md) mục 14; câu B1 quan trọng nhất (bản đầu chỉ quản lý số
  lượng hay làm cả giá thành). Đọc nhanh hiện trạng ở [`04`](nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md).
- **Kế toán:** đọc [`10`](nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md) mục 5 đến 9, rồi trả lời nhóm C ở mục 14.
- **Đội phần mềm:** đọc [`10`](nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md) mục 13 (đã có gì, phải làm mới gì, ràng buộc không được
  phá) và [`02`](nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) mục 7 (ý nghĩa của khảo sát cho ERP).

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) | **Danh sách tính năng tổng** (SX-SP, SX-KHO), thứ tự làm, câu hỏi chặn | Nháp 0.2 (26/11/2026) |
| [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-SX-01..16 (phần lớn chưa có) | Nháp 0.2 |
| [`chuc-nang/11-san-pham.md`](chuc-nang/11-san-pham.md) | Sản phẩm: mã hàng, quy tắc mã, công thức BTP, định mức / BOM ba tầng, tiêu chí đánh giá; 54 tính năng SX-SP | Nháp 0.1 (26/11/2026) |
| [`chuc-nang/12-kho.md`](chuc-nang/12-kho.md) | Kho: loại kho, loại tồn, nhập / xuất / chuyển, xuất theo đơn và BĐM, đối chiếu NCC GC, báo cáo; 50 tính năng SX-KHO | Nháp 0.1 (26/11/2026) |
| [`nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md`](nghien-cuu/20-tong-quan-nghiep-vu-chuan-tt99.md) | Thuật ngữ, quan hệ với Tồn kho / Mua hàng / Bán hàng / Kế toán, quy trình chuẩn, hạch toán giá thành theo Thông tư 99/2025, dở dang, phân bổ chi phí chung, giá chuẩn / thực tế, hàng lỗi, gia công ngoài, đối chiếu mã ERP, 15 câu phải chốt | Tài liệu nghiên cứu (bản 1.0, 21/10/2026) |
| [`du-lieu/03-mau-thuan-san-xuat-gui-phong-sx.docx`](du-lieu/03-mau-thuan-san-xuat-gui-phong-sx.docx) | Bản Word các mâu thuẫn gửi Phòng Sản xuất | chưa ghi |
| [`du-lieu/03-mau-thuan-san-xuat.xlsx`](du-lieu/03-mau-thuan-san-xuat.xlsx) | Bảng Excel mâu thuẫn và câu hỏi (đi kèm `03`) | chưa ghi |
| [`du-lieu/06-ban-do-quy-trinh-san-xuat.html`](du-lieu/06-ban-do-quy-trinh-san-xuat.html) | Bản đồ quy trình sản xuất, mở bằng trình duyệt | chưa ghi |
| [`nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md`](nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) | Phân tích khảo sát hiện trạng 19/10/2026: mâu thuẫn, hiện trạng, lỗ hổng, ý nghĩa cho ERP, câu hỏi lại | chưa ghi (bản 1.0, 24/10/2026) |
| [`nghien-cuu/03-phong-van-san-xuat-cau-hoi-va-mau-thuan.md`](nghien-cuu/03-phong-van-san-xuat-cau-hoi-va-mau-thuan.md) | Câu hỏi, câu trả lời từng người và mâu thuẫn cần chốt | chưa ghi (bản 1.0, 24/10/2026) |
| [`nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md`](nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) | Tóm tắt đọc nhanh cho ban điều hành | chưa ghi |
| [`nghien-cuu/05-san-xuat-van-ban-thong-nhat.md`](nghien-cuu/05-san-xuat-van-ban-thong-nhat.md) | Văn bản thống nhất: thuật ngữ, 108 câu hỏi và trả lời, 17 câu chưa thống nhất | chưa ghi (cập nhật 26/10/2026) |
| [`nghien-cuu/07-san-xuat-khao-sat-tra-loi-chung-2610.md`](nghien-cuu/07-san-xuat-khao-sat-tra-loi-chung-2610.md) | Tổng hợp khảo sát cả phòng trả lời chung 26/10/2026 | chưa ghi |
| [`nghien-cuu/08-san-xuat-cau-tra-loi-trich-duoc-2610.md`](nghien-cuu/08-san-xuat-cau-tra-loi-trich-duoc-2610.md) | Các câu trả lời lấy được từ khảo sát trả lời chung | chưa ghi |
| [`nghien-cuu/09-tai-lieu-gop-phong-san-xuat.md`](nghien-cuu/09-tai-lieu-gop-phong-san-xuat.md) | **Bản gộp chi tiết**: khảo sát MIC cùng tệp quy trình bàn giao Phòng Sản xuất | chưa ghi (06/11/2026) |
| [`nghien-cuu/10-giai-thich-quy-trinh-san-xuat.md`](nghien-cuu/10-giai-thich-quy-trinh-san-xuat.md) | Giải thích từng quy trình của Phòng Sản xuất | chưa ghi (06/11/2026) |
| [`nghien-cuu/11-tom-tat-khao-sat-san-xuat.md`](nghien-cuu/11-tom-tat-khao-sat-san-xuat.md) | Hiện trạng qua khảo sát MIC, bản tóm gọn đủ ý | chưa ghi (06/11/2026) |
| [`nghien-cuu/12-cau-hoi-tra-loi-khao-sat-san-xuat.md`](nghien-cuu/12-cau-hoi-tra-loi-khao-sat-san-xuat.md) | Toàn bộ câu hỏi và câu trả lời khảo sát MIC (trả lời chung 24/10) | chưa ghi (06/11/2026) |
| [`nghien-cuu/13-hieu-nhanh-phong-san-xuat.md`](nghien-cuu/13-hieu-nhanh-phong-san-xuat.md) | Hiểu nhanh Phòng Sản xuất | chưa ghi (06/11/2026) |
| [`nghien-cuu/14-danh-gia-quy-trinh-ban-giao.md`](nghien-cuu/14-danh-gia-quy-trinh-ban-giao.md) | Đánh giá tệp quy trình bàn giao, đối chiếu với khảo sát MIC | chưa ghi (06/11/2026) |
| [`nghien-cuu/15-tong-hop-13-quy-trinh-san-xuat.md`](nghien-cuu/15-tong-hop-13-quy-trinh-san-xuat.md) | Tổng hợp 13 quy trình con, luồng dữ liệu, lộ trình đưa vào ERP, tên gọi chuỗi cung ứng | 26/11/2026 |
| [`nghien-cuu/16-khung-quy-trinh-va-phap-ly-san-xuat.md`](nghien-cuu/16-khung-quy-trinh-va-phap-ly-san-xuat.md) | Chi tiết QT1–QT13, danh mục đầu vào sản xuất, pháp lý sản phẩm / NCC | 26/11/2026 |
| [`nghien-cuu/17-ncc-gia-cong-va-quan-ly-du-lieu.md`](nghien-cuu/17-ncc-gia-cong-va-quan-ly-du-lieu.md) | NCC gia công (đưa vào, đánh giá, ngưng), đầu vào QLDL, duyệt đơn, BĐM thành phẩm | 26/11/2026 |
| [`nghien-cuu/18-gia-von-mua-hang-cong-no-ton-kho.md`](nghien-cuu/18-gia-von-mua-hang-cong-no-ton-kho.md) | Giá vốn, mua NL / BTP / VTBB, công nợ, đối chiếu tồn, báo cáo VTBB | 26/11/2026 |
| [`nghien-cuu/19-dieu-phoi-thanh-pham-va-su-co.md`](nghien-cuu/19-dieu-phoi-thanh-pham-va-su-co.md) | Điều phối thành phẩm gửi NCC GC, sự cố sản xuất và chỉ số | 26/11/2026 |
| [`nghien-cuu/21-so-quan-ly-nhan-mac-ida-group.md`](nghien-cuu/21-so-quan-ly-nhan-mac-ida-group.md) | Sổ Quản lý nhãn mác (dữ liệu thật): 11.150 mã hàng hóa, quy tắc đặt mã 31/03/2026, định mức bao bì thật 4.189 mã, kho nhãn | 26/11/2026 |
| [`du-lieu/09-quy-trinh-ban-giao-sheets/`](du-lieu/09-quy-trinh-ban-giao-sheets/) | 20 sheet của tệp quy trình bàn giao (mục lục, tiến độ, QT 1–20) xuất ra văn bản | dữ liệu gốc |
| [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) | Bảng đường API (dựng tự động; chưa có mã backend) | Nháp |

## Liên quan tới đâu

| Nơi khác | Quan hệ |
|---|---|
| [`erp/README.md`](../README.md) | Bộ tài liệu nền ERP |
| [`mat-hang/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md`](../mat-hang/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) | Luật của bảng sản phẩm; BOM phải tuân theo |
| [`nhap-khau/`](../nhap-khau/chuc-nang/10-danh-sach-tinh-nang.md) | Nguyên liệu nhập khẩu cho nhà máy |
| [`01-luong-chuan-mua-hang-kho-san-xuat.md`](../../plans/01-luong-chuan-mua-hang-kho-san-xuat.md) | Luồng chuẩn mua hàng, kho, sản xuất |

## Mã nguồn

- Backend: chưa có.
- Giao diện v2: `frontend-v2/src/modules/production/` hiện chỉ là khung menu Sản xuất chứa danh mục dùng chung.

## Lịch sử

| Phiên bản | Ngày | Thay đổi |
|---|---|---|
| 1.0 | 21/10/2026 | Tạo bộ tài liệu. Tài liệu tổng quan viết lại từ bản đại ca gửi: sửa tám chỗ, đổi căn cứ sang Thông tư 99, bổ sung các mục 6, 7, 8, 10, 13, 14 |
| 0.1 (khuôn mới) | 03/11/2026 | Sắp lại README theo khuôn `mau-readme-phan-he.md`, thêm hai tệp bắt buộc 01, 02 (bao-CR-712) |
