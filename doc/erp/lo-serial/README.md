# LÔ, SERIAL VÀ HẠN DÙNG (LS)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 (dựng bộ tài liệu bắt buộc) · chưa có CR làm mã |

## Phân hệ này là gì

Phân hệ Lô, serial và hạn dùng lo việc theo dõi hàng theo **lô** (số lô, ngày sản xuất, hạn dùng), xuất theo FEFO, chặn
lô hết hạn, truy xuất ngược từ thành phẩm về nguyên liệu và xuôi tới khách. Người dùng dự kiến là thủ kho, QC, Lab, nhà
máy, kinh doanh (thu hồi). **Hiện ERP DEGO không có khái niệm lô, hạn dùng hay serial ở bất cứ bảng kho nào**; kho thành
phẩm đang ghi tay ngoài hệ thống. Phân hệ ở mức **nghiên cứu**, chưa có mã, chưa có màn. Kết luận nghiên cứu: DEGO cần lô
và hạn dùng, **không cần serial**.

## Tới đâu rồi

Độ phủ lấy từ [nghiên cứu lô, serial](nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) (soát `erp-v2` ngày 02/11/2026):
**3 %** (0,5 / 18 chức năng so với ERPNext v16), **4 %** trên 14 chức năng DEGO cần.

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Lô ở cửa nhập, tồn theo lô (L1) | Chưa làm | Phải vào cùng lúc với phiếu nhập kho thật (Nhận hàng N2.3) |
| Xuất theo FEFO, chặn lô hết hạn (L2) | Chưa làm | Chờ phiếu xuất (Xuất hàng XG1) |
| Lô trong sản xuất, truy xuất ngược, xuôi (L3, L4) | Chưa làm | Chờ phân hệ Sản xuất, bán hàng |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) (chưa có đường) |
| Thiết kế, bảng dữ liệu, bẫy | [nghiên cứu mục 2, 7.4](nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) (từ ngữ *lô* đang trùng nghĩa; phác thảo dữ liệu tối giản) |
| So sánh, khảo sát, câu hỏi chờ chốt | [nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md](nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) mục 6, 9 |
| Kế hoạch đang làm / đã xong | Chưa có thư mục `plans/`; kế hoạch chung ở [doc/plans/12](../../plans/12-muc-do-module-kho-mat-hang-va-ke-hoach.md) |
| Kịch bản kiểm thử tay | Chưa có |
| Hướng dẫn người dùng | Chưa có |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng dự kiến CN-LS-01..12 (nguồn nghiên cứu) | Nháp |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-LS-01..12 | Nháp |
| [nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md](nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) | Lô, serial, hạn dùng, truy xuất: ERPNext v16 so với ERP DEGO, luật ngành, kế hoạch L0..L4 | Tài liệu nghiên cứu, không sửa mã, không đổi dữ liệu |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Tài liệu API (chưa có đường) | Nháp |

## Mã nguồn

- Backend: chưa có. Thứ dùng lại được: luật tình trạng hiệu lực suy ra từ ngày ở `backend/app/modules/dossier/expiry.py`,
  khuôn thẻ cảnh báo ở `backend/app/modules/dashboard/controller.py`.
- Giao diện v2: chưa có.
- Luật cho người viết mã: chưa có. Lưu ý đặt tên: chữ *batch* đã bị `tab_import_batch` (lô nhập dữ liệu) chiếm; nghiên
  cứu đề xuất bảng `tab_stock_lot`.
