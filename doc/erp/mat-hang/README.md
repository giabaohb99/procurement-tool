# MẶT HÀNG (MH)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 (dựng bộ tài liệu bắt buộc) · D-025 (mô hình dữ liệu sản phẩm, theo [mo-hinh-du-lieu-san-pham.md](tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md)) |

## Phân hệ này là gì

Phân hệ Mặt hàng giữ danh mục vật tư bao bì, nguyên liệu, hàng hóa (bảng `tab_product`, mỗi dòng là một SKU đặt mua và
nhập kho được), cùng các danh mục đi kèm: đơn vị tính, phân loại (nhóm hàng), thương hiệu. Người dùng là thu mua, người
phụ trách danh mục và mọi người lập chứng từ (chọn mã hàng thì tự điền dòng). Trên giao diện v2 các màn nằm trong phân
hệ Sản xuất: `/production/products`, `/production/units`, `/production/item-groups`. Luật bất biến: `product_code` là hạt
nối bảy bảng chứng từ, không đổi, không tái dùng.

## Tới đâu rồi

Độ phủ lấy từ [nghiên cứu mặt hàng](nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) (soát `erp-v2` commit `601ec718`,
02/11/2026): **37 %** (14 / 38 chức năng so với ERPNext v16). Tài liệu cũ không ghi trạng thái lên prod.

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Danh mục sản phẩm, ĐVT, phân loại, thương hiệu; nhập xuất CSV; ảnh; chặn xóa | chưa ghi (có mã) | Đặc tả ở [thu mua 16](../thu-mua/chuc-nang/16-danh-muc.md) |
| Thuộc tính theo phân loại, trường động | Chưa làm | [01-thuoc-tinh-theo-phan-loai.md](tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md) (phân tích, kiến trúc, chưa làm) |
| Quy đổi đơn vị, cờ loại hàng, mã hàng NCC, giá có hiệu lực, họ sản phẩm | Chưa làm | Kế hoạch ba nấc ở [nghiên cứu mục 6](nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · nhóm `product`, `unit`, `item_group`, `brand` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md](tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) (bắt buộc đọc trước khi sửa bảng sản phẩm), [tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md](tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | [nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md](nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) mục 4, 7 |
| Kế hoạch đang làm / đã xong | Chưa có thư mục `plans/`; kế hoạch chung ở [doc/plans/12 Mức độ module kho, mặt hàng](../../plans/12-muc-do-module-kho-mat-hang-va-ke-hoach.md) |
| Kịch bản kiểm thử tay | Chưa có |
| Hướng dẫn người dùng | Chưa có bài HDSD riêng |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng CN-MH-01..18 (đã có và dự kiến) | Nháp |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-MH-01..12 | Nháp |
| [nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md](nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) | Mặt hàng ERPNext v16 so với ERP DEGO, fit-gap 38 chức năng, kế hoạch ba nấc | chưa ghi (đầu tệp: bản 1.0, 02/11/2026) |
| [tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md](tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md) | Thuộc tính theo phân loại mặt hàng, phân tích từ danh mục VTBB đang dùng | chưa ghi (đầu tệp: bản 1.1, 02/11/2026, chưa làm) |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Bảng đường API dựng tự động từ mã | Nháp |
| [tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md](tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) | Mô hình dữ liệu sản phẩm: luật bất biến, thuộc tính động, họ sản phẩm, kế hoạch chuyển dữ liệu | chưa ghi |

## Mã nguồn

- Backend: `backend/app/modules/product/`; ĐVT, phân loại, thương hiệu, kho ở `backend/app/modules/catalog/`
  (dựng bằng `make_crud_router`); số ngày quy định ở `catalog/lead_time.py`.
- Giao diện v2: `frontend-v2/src/modules/production/` (`config/product-crud.tsx`, `item-group-crud.tsx`, `unit-crud.tsx`).
- Luật cho người viết mã: luật bất biến của bảng sản phẩm ở [mo-hinh-du-lieu-san-pham.md](tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) mục 1, 11.
