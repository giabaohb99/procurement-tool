# KHO (KHO)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 (dựng bộ tài liệu bắt buộc) · CR-001 (thiết kế lại danh mục kho, theo [tdd-redesign-kho.md](tai-lieu-ky-thuat/tdd-redesign-kho.md)) |

## Phân hệ này là gì

Phân hệ Kho giữ danh mục kho, tồn theo cặp *pháp nhân, kho, mã hàng*, sổ phát sinh và điều chỉnh tồn tay. Người dùng là
thu mua, thủ kho, kế toán kho. Trên giao diện v2 các màn nằm ở `/inventory` (Tổng quan), `/inventory/stock` (Tồn kho),
`/inventory/warehouses` (Danh mục kho). Hiện tồn **chỉ tăng** qua nhận hàng trên Đơn mua hàng và điều chỉnh tay; chưa có
phiếu xuất, chuyển kho, kiểm kê. Phần lớn chức năng kho chuẩn mới ở mức nghiên cứu.

## Tới đâu rồi

Tài liệu cũ không ghi trạng thái lên prod. Độ phủ lấy từ [nghiên cứu kho lõi](nghien-cuu/00-nghien-cuu-kho-erpnext.md)
(soát `erp-v2` commit `601ec718`, 02/11/2026): **19 %** (7 / 36 chức năng so với ERPNext v16).

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Danh mục kho, tồn, sổ phát sinh, điều chỉnh tay, tab Đơn hàng về kho | chưa ghi (có mã) | Đặc tả ở [thu mua 15](../thu-mua/chuc-nang/15-ton-kho-cong-no.md), [thu mua 16 mục Kho](../thu-mua/chuc-nang/16-danh-muc.md) |
| Danh mục kho có công ty sở hữu, loại kho | Chưa làm | [tdd-redesign-kho.md](tai-lieu-ky-thuat/tdd-redesign-kho.md) bản v0.1 chờ duyệt; việc KHO-1.4 |
| Sổ kho chỉ ghi thêm, phiếu kho, kiểm kê, khóa kỳ | Chưa làm | Nấc 2 của [nghiên cứu kho lõi mục 6](nghien-cuu/00-nghien-cuu-kho-erpnext.md) |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · nhóm `inventory`, `warehouse` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [tai-lieu-ky-thuat/tdd-redesign-kho.md](tai-lieu-ky-thuat/tdd-redesign-kho.md); [nghiên cứu kho lõi mục 3.2, 3.3, 5](nghien-cuu/00-nghien-cuu-kho-erpnext.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | [nghien-cuu/00-nghien-cuu-kho-erpnext.md](nghien-cuu/00-nghien-cuu-kho-erpnext.md) mục 4, 7; [nghien-cuu/10-nghiep-vu-kho.md](nghien-cuu/10-nghiep-vu-kho.md) |
| Kế hoạch đang làm / đã xong | Chưa có thư mục `plans/`; kế hoạch chung ở [doc/plans/12 Mức độ module kho, mặt hàng](../../plans/12-muc-do-module-kho-mat-hang-va-ke-hoach.md) và [doc/plans/01](../../plans/01-luong-chuan-mua-hang-kho-san-xuat.md) |
| Kịch bản kiểm thử tay | Chưa có |
| Hướng dẫn người dùng | Chưa có bài HDSD riêng cho kho |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng CN-KHO-01..17 (đã có và dự kiến) | Nháp |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-KHO-01..12 | Nháp |
| [nghien-cuu/00-nghien-cuu-kho-erpnext.md](nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Kho lõi ERPNext v16 so với ERP DEGO, đề xuất kiến trúc, kế hoạch ba nấc | Tài liệu nghiên cứu, chưa phải tài liệu yêu cầu |
| [nghien-cuu/10-nghiep-vu-kho.md](nghien-cuu/10-nghiep-vu-kho.md) | Giáo trình nghiệp vụ kho chuẩn | Tài liệu nghiên cứu, chưa phải tài liệu yêu cầu |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Bảng đường API dựng tự động từ mã | Nháp |
| [tai-lieu-ky-thuat/tdd-redesign-kho.md](tai-lieu-ky-thuat/tdd-redesign-kho.md) | Thiết kế lại danh mục kho: công ty sở hữu, phân loại kho | Bản nháp v0.1, chờ duyệt |

## Mã nguồn

- Backend: `backend/app/modules/inventory/` (tồn, sổ phát sinh, điều chỉnh); danh mục kho ở
  `backend/app/modules/catalog/model.py` (`Warehouse`, dựng bằng `make_crud_router`); phiếu nhập ngầm ở
  `backend/app/modules/goods_receipt/`.
- Giao diện v2: `frontend-v2/src/modules/inventory/`.
- Luật cho người viết mã: chưa có luật riêng; khi thêm entity quyền mới dùng skill `them-entity-moi`.
