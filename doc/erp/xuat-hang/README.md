# XUẤT KHO VÀ GIAO HÀNG (XH)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 (dựng bộ tài liệu bắt buộc) · chưa có CR làm mã |

## Phân hệ này là gì

Phân hệ Xuất kho và Giao hàng lo chiều ra của kho: đề nghị lĩnh vật tư, phiếu xuất dùng nội bộ, xuất hủy, chuyển kho,
xuất cho sản xuất ở mức chứng từ kho, và về sau là giao hàng bán (đơn bán, phiếu giao, trả hàng bán), nối với Đặt xe giao
hàng. Người dùng dự kiến là thủ kho, người có nhu cầu lĩnh vật tư, sản xuất, hành chính điều xe. **Hiện ERP DEGO chưa có
chiều ra của kho**: mọi lần lấy hàng ra phải đi bằng điều chỉnh tồn âm; phân hệ Bán hàng, Khách hàng trên v2 mới là vỏ
(`enabled: false`). Phân hệ đang ở mức **nghiên cứu**, chưa có mã backend.

## Tới đâu rồi

Độ phủ lấy từ [nghiên cứu xuất kho, giao hàng](nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) (soát `erp-v2`
ngày 02/11/2026): **21 %** (6,5 / 31 chức năng so với ERPNext v16); điểm có được nằm ở nền dùng chung và Đặt xe.

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Phiếu xuất dùng nội bộ, xuất hủy, chuyển kho, đề nghị lĩnh vật tư | Chưa làm | Nấc XG1, XG2 |
| Nối Đặt xe giao hàng với chứng từ kho | Chưa làm | Đặt xe giao hàng đã có, thuộc phân hệ Đặt xe |
| Giao hàng bán | Chưa làm | Chờ câu X1 (công ty có bán hàng qua ERP không) |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) (chưa có đường) |
| Thiết kế, bảng dữ liệu, bẫy | [nghiên cứu mục 6](nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | [nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md](nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) mục 5, 8 |
| Kế hoạch đang làm / đã xong | Chưa có thư mục `plans/`; kế hoạch chung ở [doc/plans/12](../../plans/12-muc-do-module-kho-mat-hang-va-ke-hoach.md) |
| Kịch bản kiểm thử tay | Chưa có |
| Hướng dẫn người dùng | Chưa có |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng dự kiến CN-XH-01..10 (nguồn nghiên cứu) | Nháp |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-XH-01..12 | Nháp |
| [nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md](nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md) | Xuất kho, giao hàng, kết nối bán hàng: ERPNext v16 so với ERP DEGO, kế hoạch XG0..XG9 | Chỉ nghiên cứu, không sửa mã, không ghi dữ liệu |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Tài liệu API (chưa có đường) | Nháp |

## Mã nguồn

- Backend: chưa có. Phần liên quan đang có: `backend/app/modules/inventory/` (điều chỉnh tồn), `vehicle_booking/` (đặt
  xe giao hàng), `approval/` (bộ máy duyệt chung).
- Giao diện v2: vỏ `frontend-v2/src/modules/sales/`, `frontend-v2/src/modules/customer/`.
- Luật cho người viết mã: chưa có.
