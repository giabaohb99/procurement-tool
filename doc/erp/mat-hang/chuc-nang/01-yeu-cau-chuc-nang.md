# YÊU CẦU CHỨC NĂNG — MẶT HÀNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · D-025 (mô hình dữ liệu sản phẩm) · CR-060 (che NCC trên lịch sử mua) |

Tệp này là **mục lục chức năng**. Chức năng đã có mã (CN-MH-01..08) đang được đặc tả ở
[thu mua 16 Danh mục](../../thu-mua/chuc-nang/16-danh-muc.md) và [thu mua 18 Lịch sử mua hàng](../../thu-mua/chuc-nang/18-lich-su-mua-hang.md);
hiện trạng soát mã ở [nghiên cứu mặt hàng mục 3.2](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md). Chức năng
CN-MH-09..18 là **dự kiến**, rút từ tài liệu **nghiên cứu** (mục 6, mã việc nấc *1.x / 2.x / 3.x*) và hai tài liệu thiết kế
[mô hình dữ liệu sản phẩm](../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md), [thuộc tính theo phân loại](../tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md);
chưa phải yêu cầu đã chốt.

**Cách đọc cột Trạng thái:** *có mã* nghĩa là nghiên cứu (soát `erp-v2` ngày 02/11/2026) xác nhận đã có mã, không nói đã
lên prod hay chưa.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Người phụ trách danh mục (mã vai trò: chưa ghi) | Thêm, sửa, ngưng dùng mã hàng; nhập, xuất CSV; dọn ĐVT, phân loại |
| Thu mua, người lập chứng từ (quyền `product.read`) | Tìm mã hàng, chọn mã để tự điền dòng YCMH, ĐMH, phiếu khảo sát; xem lịch sử mua |
| Quản trị (quyền `unit`, `item_group`, `brand`) | Quản ĐVT, phân loại kèm số ngày quy định, thương hiệu |

## 2. Danh sách chức năng

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-MH-01 | Danh mục sản phẩm: mã bất biến, tên, tên hóa đơn, tên pháp lý, phân loại, ĐVT, mã và tên hàng hóa thành phẩm, thông số, đang dùng — [thu mua 16 mục Sản phẩm](../../thu-mua/chuc-nang/16-danh-muc.md) | Người phụ trách danh mục | `/production/products` | chưa ghi · có mã | D-025 |
| CN-MH-02 | Nhập, xuất CSV sản phẩm: khớp tiêu đề linh hoạt, chỉ ghi đè cột có trong tệp, gộp mã trùng trong tệp — [nghiên cứu mục 3.2](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) | Người phụ trách danh mục | Nút Nhập, Xuất trên danh sách | chưa ghi · có mã | chưa ghi |
| CN-MH-03 | Nhiều ảnh cho một sản phẩm, ảnh đại diện — [nghiên cứu mục 3.2](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) | Người phụ trách danh mục | Chi tiết sản phẩm | chưa ghi · có mã | chưa ghi |
| CN-MH-04 | Chặn xóa sản phẩm còn chứng từ (đếm đủ bảy bảng), chặn xóa ĐVT, phân loại, kho đang dùng — [nghiên cứu mục 3.2](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) | Hệ thống | Xóa trên danh mục | chưa ghi · có mã | ai-CR-169 |
| CN-MH-05 | Danh mục đơn vị tính — [thu mua 16 mục Đơn vị tính](../../thu-mua/chuc-nang/16-danh-muc.md) | Quản trị | `/production/units` | chưa ghi · có mã | chưa ghi |
| CN-MH-06 | Danh mục phân loại (nhóm hàng) kèm số ngày quy định khi NCC có sẵn và không sẵn hàng — [thu mua 16 mục Phân loại](../../thu-mua/chuc-nang/16-danh-muc.md) | Quản trị | `/production/item-groups` | chưa ghi · có mã | chưa ghi |
| CN-MH-07 | Danh mục thương hiệu, thực chất là bộ phận đặt hàng kèm người quản lý; chưa có màn v2, không bảng nào trỏ tới — [thu mua 16 mục Thương hiệu](../../thu-mua/chuc-nang/16-danh-muc.md) | Quản trị | `/api/brands` | chưa ghi · có mã | chưa ghi |
| CN-MH-08 | Tab Lịch sử mua hàng trên chi tiết sản phẩm, giá mua gần nhất và cao nhất tự điền sang khảo sát — [thu mua 18](../../thu-mua/chuc-nang/18-lich-su-mua-hang.md) | Thu mua | Chi tiết sản phẩm | chưa ghi · có mã | CR-060 |
| CN-MH-09 | Thuộc tính theo phân loại: từ điển thuộc tính, giá trị chọn sẵn, gắn thuộc tính vào phân loại, trường động trên form sản phẩm, `specs` suy diễn (việc 2.1..2.3) — [thuộc tính theo phân loại](../tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md), [mô hình mục 5, 6](../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) | Người phụ trách danh mục | Form sản phẩm | Chưa | chưa có |
| CN-MH-10 | `item_group_id` thay chuỗi tên phân loại, bộ lọc *Chưa có ĐVT*, *Phân loại lệch danh mục* (việc 1.1, 1.2; M1 của mô hình) | Người phụ trách danh mục | `/production/products` | Chưa | chưa có |
| CN-MH-11 | Bắt buộc ĐVT với mã mới, đề xuất ĐVT cho mã cũ, khóa đổi ĐVT khi đã có phát sinh kho (việc 1.3, 1.5, 1.6) | Người phụ trách danh mục | Form sản phẩm | Chưa | chưa có |
| CN-MH-12 | Cờ loại hàng `item_type`: tồn kho, phi kho, dịch vụ, tài sản (việc 1.4) | Người phụ trách danh mục | Form sản phẩm | Chưa | chưa có |
| CN-MH-13 | Quy đổi đơn vị theo mặt hàng và bảng quy đổi chung; chứng từ mang hệ số quy đổi (việc 2.4, 2.5) | Thu mua, kho | Tab Quy đổi trên sản phẩm | Chưa | chưa có |
| CN-MH-14 | Mã hàng của NCC (`tab_product_supplier`), tự điền lên đơn (việc 2.6) | Thu mua | Chi tiết sản phẩm | Chưa | chưa có |
| CN-MH-15 | Cây nhóm hàng, nhóm con kế thừa số ngày quy định và NSTM (việc 2.7) | Quản trị | `/production/item-groups` | Chưa | chưa có |
| CN-MH-16 | Giá kế hoạch có hiệu lực (`tab_product_price`) từ hợp đồng khung hoặc báo giá đã duyệt (việc 2.8) | Thu mua | chưa có | Chưa | chưa có |
| CN-MH-17 | Họ sản phẩm (`tab_product_family`) ở trên `tab_product`, thương hiệu ở tầng họ (việc 3.1; mô hình mục 10) | Người phụ trách danh mục | chưa có | Chưa | chưa có |
| CN-MH-18 | Mở rộng nấc 3: mức đặt hàng lại, lô và hạn dùng, mẫu kiểm chất lượng, VAT gợi ý, mã vạch, kho nhận mặc định, hàng thay thế (việc 3.2..3.8) | Thu mua, kho | chưa có | Chưa | chưa có |

## 3. Chi tiết từng chức năng

### CN-MH-01 — Danh mục sản phẩm

- **Mục đích:** một danh mục mã hàng dùng chung cho mọi chứng từ mua, kho, khảo sát.
- **Luồng chính:** thêm hoặc nhập CSV mã hàng → người lập chứng từ chọn mã → hệ thống chép tên, ĐVT, phân loại, TSKT vào dòng chứng từ (bản chụp).
- **Luật nghiệp vụ:** `tab_product` là bảng SKU; `product_code` nối bảy bảng bằng chuỗi, không đổi, không tái dùng; cấm thêm bảng biến thể bên dưới, cấm đặt cột giá lên sản phẩm; sửa danh mục không hồi tố chứng từ — [mô hình mục 1, 11](../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md).
- **Dữ liệu:** danh sách trường ở [thu mua 16 mục Sản phẩm](../../thu-mua/chuc-nang/16-danh-muc.md).
- **Quyền:** entity `product` (`read`, `create`, `write`, `delete`, `export`, `import`); phạm vi `PUBLIC`.
- **Ngoại lệ / lỗi người dùng gặp:** xóa mã còn chứng từ bị chặn (CN-MH-04); câu báo cụ thể: chưa ghi.
- **Liên quan:** CN-MH-02..08; công cụ AI `product_search`, `product_best_price`, `product_purchase_history`.

### CN-MH-06 — Danh mục phân loại

- **Mục đích:** gom mã hàng theo nhóm và làm khóa cho số ngày quy định có hàng, phân công NSTM.
- **Luồng chính:** khai phân loại, số ngày khi NCC có sẵn và không sẵn hàng, ngày áp dụng → YCMH, ĐMH dùng để tính ngày dự kiến; phân công phụ trách gán NSTM theo phân loại.
- **Luật nghiệp vụ:** `tab_product.item_group` hiện là chuỗi tên, không phải khóa; nghiên cứu ghi 685 mã lệch tên danh mục — [nghiên cứu mục 3.2](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md).
- **Dữ liệu:** [thu mua 16 mục Phân loại](../../thu-mua/chuc-nang/16-danh-muc.md).
- **Quyền:** entity `item_group`; phạm vi `PUBLIC`.
- **Ngoại lệ / lỗi người dùng gặp:** xóa phân loại đang dùng bị chặn (`catalog/references.py`).
- **Liên quan:** [thu mua CN-TM-18](../../thu-mua/chuc-nang/01-yeu-cau-chuc-nang.md) phân công phụ trách; CN-MH-10, CN-MH-15.

### CN-MH-09 — Thuộc tính theo phân loại (dự kiến, nguồn thiết kế)

- **Mục đích:** mỗi phân loại có bộ thuộc tính riêng (chai có dung tích, cổ chai; thùng có kích thước, số lớp) thay cho quy cách viết trong tên.
- **Luồng chính (đề xuất):** khai thuộc tính và giá trị → gắn vào phân loại → form sản phẩm hiện trường động → nạp giá trị từ tên hàng cũ (đề xuất, duyệt, nạp).
- **Luật nghiệp vụ (đã chốt 02/11/2026):** phân loại chỉ là bộ **gợi ý**; mã hàng hóa và tên trên hóa đơn không làm thuộc tính — [thuộc tính theo phân loại mục 4, 4b, 4c](../tai-lieu-ky-thuat/01-thuoc-tinh-theo-phan-loai.md).
- **Dữ liệu (thiết kế):** `tab_attribute`, `tab_attribute_option`, `tab_item_group_attribute`, `tab_product_attribute` — [mô hình mục 5](../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md).
- **Quyền:** chưa có.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** `ProductOut` chỉ được thêm trường ([mô hình mục 6.1](../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md)).

## 4. Luồng trạng thái chứng từ

Không áp dụng: danh mục không có chứng từ; mã hàng chỉ có cờ *đang dùng* (`is_active`).

## 5. Câu hỏi còn mở

Chín câu Q1..Q9 ở [nghiên cứu mặt hàng mục 7](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md): từ ngày nào bắt buộc ĐVT và ai
duyệt ĐVT cho 6.424 mã cũ, có tách cờ loại hàng, nhóm nào cần quy đổi đơn vị, có thêm hệ số quy đổi vào chứng từ, có cây
nhóm hàng, giá kế hoạch lấy từ đâu, điều kiện bật họ sản phẩm, VAT gợi ý theo đâu, có đổi nhãn `tab_brand` thành *Bộ phận
đặt hàng*. Câu C5 (lô, hạn dùng, vị trí kho) nằm ở [doc/plans/00](../../../plans/00-ke-hoach-theo-module.md).

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Q1..Q9 của nghiên cứu mặt hàng | Đại ca, người phụ trách danh mục, kho | chưa có |
