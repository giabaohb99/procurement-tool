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
| Nghiên cứu nghiệp vụ chuẩn (Thông tư 99/2025) | Đã có tài liệu | [`10`](chuc-nang/10-tong-quan-nghiep-vu.md), bản 1.0 21/10/2026 |
| Khảo sát hiện trạng Phòng Sản xuất | Đã có tài liệu | [`02`](nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) … [`08`](nghien-cuu/08-san-xuat-cau-tra-loi-trich-duoc-2610.md); còn câu chưa thống nhất |
| Tài liệu yêu cầu | Chưa làm | Chờ trả lời 15 câu ở [`10`](chuc-nang/10-tong-quan-nghiep-vu.md) §14 (việc SX1-1) |
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
| Làm được gì (đề xuất, chưa chốt) | [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) (chưa có đường nào) |
| Thiết kế, bảng dữ liệu, bẫy | chưa có; ràng buộc thiết kế ở [`10`](chuc-nang/10-tong-quan-nghiep-vu.md) §13.3 |
| So sánh, khảo sát, câu hỏi chờ chốt | [`nghien-cuu/`](nghien-cuu/) — đọc nhanh [`04`](nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md); câu cần chốt ở [`10`](chuc-nang/10-tong-quan-nghiep-vu.md) §14 |
| Kế hoạch đang làm / đã xong | chưa có thư mục `plans/`; việc ở [kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §12 (SX1-x, SX2-x, SX3-x) |
| Kịch bản kiểm thử tay | chưa có |
| Hướng dẫn người dùng | chưa có |

Đọc theo vai:

- **Người quyết:** đọc [`10`](chuc-nang/10-tong-quan-nghiep-vu.md) mục 14; câu B1 quan trọng nhất (bản đầu chỉ quản lý số
  lượng hay làm cả giá thành). Đọc nhanh hiện trạng ở [`04`](nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md).
- **Kế toán:** đọc [`10`](chuc-nang/10-tong-quan-nghiep-vu.md) mục 5 đến 9, rồi trả lời nhóm C ở mục 14.
- **Đội phần mềm:** đọc [`10`](chuc-nang/10-tong-quan-nghiep-vu.md) mục 13 (đã có gì, phải làm mới gì, ràng buộc không được
  phá) và [`02`](nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) mục 7 (ý nghĩa của khảo sát cho ERP).

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng đề xuất CN-SX-NN rút từ nghiên cứu, chưa chốt phạm vi | Nháp |
| [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-SX-01..12 (phần lớn chưa có) | Nháp |
| [`chuc-nang/10-tong-quan-nghiep-vu.md`](chuc-nang/10-tong-quan-nghiep-vu.md) | Thuật ngữ, quan hệ với Tồn kho / Mua hàng / Bán hàng / Kế toán, quy trình chuẩn, hạch toán giá thành theo Thông tư 99/2025, dở dang, phân bổ chi phí chung, giá chuẩn / thực tế, hàng lỗi, gia công ngoài, đối chiếu mã ERP, 15 câu phải chốt | Tài liệu nghiên cứu (bản 1.0, 21/10/2026) |
| [`du-lieu/03-mau-thuan-san-xuat-gui-phong-sx.docx`](du-lieu/03-mau-thuan-san-xuat-gui-phong-sx.docx) | Bản Word các mâu thuẫn gửi Phòng Sản xuất | chưa ghi |
| [`du-lieu/03-mau-thuan-san-xuat.xlsx`](du-lieu/03-mau-thuan-san-xuat.xlsx) | Bảng Excel mâu thuẫn và câu hỏi (đi kèm `03`) | chưa ghi |
| [`du-lieu/06-ban-do-quy-trinh-san-xuat.html`](du-lieu/06-ban-do-quy-trinh-san-xuat.html) | Bản đồ quy trình sản xuất, mở bằng trình duyệt | chưa ghi |
| [`nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md`](nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) | Phân tích khảo sát hiện trạng 19/10/2026: mâu thuẫn, hiện trạng, lỗ hổng, ý nghĩa cho ERP, câu hỏi lại | chưa ghi (bản 1.0, 24/10/2026) |
| [`nghien-cuu/03-phong-van-san-xuat-cau-hoi-va-mau-thuan.md`](nghien-cuu/03-phong-van-san-xuat-cau-hoi-va-mau-thuan.md) | Câu hỏi, câu trả lời từng người và mâu thuẫn cần chốt | chưa ghi (bản 1.0, 24/10/2026) |
| [`nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md`](nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) | Tóm tắt đọc nhanh cho ban điều hành | chưa ghi |
| [`nghien-cuu/05-san-xuat-van-ban-thong-nhat.md`](nghien-cuu/05-san-xuat-van-ban-thong-nhat.md) | Văn bản thống nhất: thuật ngữ, 108 câu hỏi và trả lời, 17 câu chưa thống nhất | chưa ghi (cập nhật 26/10/2026) |
| [`nghien-cuu/07-san-xuat-khao-sat-tra-loi-chung-2610.md`](nghien-cuu/07-san-xuat-khao-sat-tra-loi-chung-2610.md) | Tổng hợp khảo sát cả phòng trả lời chung 26/10/2026 | chưa ghi |
| [`nghien-cuu/08-san-xuat-cau-tra-loi-trich-duoc-2610.md`](nghien-cuu/08-san-xuat-cau-tra-loi-trich-duoc-2610.md) | Các câu trả lời lấy được từ khảo sát trả lời chung | chưa ghi |
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
