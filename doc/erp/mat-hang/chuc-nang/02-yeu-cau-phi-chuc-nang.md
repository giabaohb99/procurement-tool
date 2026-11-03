# YÊU CẦU PHI CHỨC NĂNG — MẶT HÀNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · bao-CR-538, CR-060 |

Mỗi yêu cầu một mã `PCN-MH-NN`. Chỉ ghi điều có nguồn; chỗ không có ghi *Chưa có* / *Chưa đo*. Chưa chạy lại bài kiểm nào
khi viết bản này.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-MH-01 | Hiệu năng | Chưa có con số mục tiêu. Kế hoạch rà soát API có mục cho `product/service.py::list_products` | [Kế hoạch rà soát API hiệu năng](../../../tai-lieu-ky-thuat/van-hanh/ra-soat-api-hieu-nang.md) | Chưa đo |
| PCN-MH-02 | Phân quyền | Khóa quyền `product`, `unit`, `item_group`, `brand` (`read`, `create`, `write`, `delete`, `export`, `import` theo [api.md](../tai-lieu-ky-thuat/api.md)); cả bốn khai `PUBLIC` trong `SCOPE_FIELDS`, mọi công ty dùng chung một danh mục. Tài liệu [thu mua 16 mục Quyền](../../thu-mua/chuc-nang/16-danh-muc.md) ghi nhập CSV dùng `:create`, còn api.md dựng từ mã ghi `.import` — cần soát lại cho khớp | `test/backend/test_pham_vi_khai_du_b07.py` | Chưa đo; lệch tài liệu ghi ở cột yêu cầu |
| PCN-MH-03 | Dữ liệu nhạy cảm | Tab Lịch sử mua hàng trên sản phẩm chỉ đòi `product.read`; với người không có `supplier.read`, máy chủ xóa tên và mã NCC khỏi dữ liệu trả về và bỏ tên NCC khỏi vế tìm kiếm (CR-060) | [thu mua 18 mục 4](../../thu-mua/chuc-nang/18-lich-su-mua-hang.md); `test/backend/test_purchase_history.py` | Chưa đo |
| PCN-MH-04 | Giới hạn đầu vào | Trường chữ của schema ghi chặn độ dài theo `.claude/rules/backend-input-limits.md` (`specs` là `String(255)`); cỡ tệp CSV nhập, cỡ ảnh: Chưa có | `test/backend/test_canh_do_dai_o_chu_cr538.py` (có `product`, `catalog`) | Chưa đo |
| PCN-MH-05 | Nhật ký và truy vết | Chưa có yêu cầu riêng cho danh mục. Chứng từ là bản chụp, sửa danh mục không hồi tố chứng từ cũ | [mô hình mục 11](../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) | Chưa đo |
| PCN-MH-06 | Lưu trữ và dọn dữ liệu | Không xóa mã đã phát sinh chứng từ (`product/service.count_references` đếm bảy bảng); ngưng dùng bằng `is_active`. `Product` không có `SoftDeleteMixin` trong `model.py` | [nghiên cứu mục 3.2](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) | Chưa đo |
| PCN-MH-07 | Sao lưu và khôi phục | Nằm trong bản sao lưu CSDL chung (`backup.run`, `backend/app/core/celery_app.py`); ảnh lưu qua `attachment` (`FileLink`) | Chưa có | Chưa đo |
| PCN-MH-08 | Đồng thời | `code` duy nhất trên `tab_product`; nhập CSV gộp mã trùng trong tệp. Hai người sửa cùng một mã: Chưa có | [nghiên cứu mục 3.2](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) | Chưa đo |
| PCN-MH-09 | Tích hợp | `product_code` nối bảy bảng bằng chuỗi, không khóa ngoại (dòng YCMH, dòng ĐMH, nhận hàng, tồn, phát sinh kho, lịch sử mua, phương án khảo sát). Hợp đồng API `ProductOut` chỉ được **thêm** trường, không bỏ, không đổi nghĩa (phá `ProductPicker` và hai màn tự điền). Công cụ AI: `product_search`, `product_best_price`, `product_purchase_history` | [mô hình mục 2, 6.1, 7](../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) | Chưa đo |
| PCN-MH-10 | Khả dụng và thiết bị | Chưa có | Chưa có | Chưa đo |
| PCN-MH-11 | Pháp lý | Chưa có yêu cầu viết cho phân hệ. Nghiên cứu lô, hạn dùng nêu luật ghi nhãn phân bón, thuốc bảo vệ thực vật — áp ở phân hệ [Lô, serial](../../lo-serial/chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Chưa có | Chưa đo |
| PCN-MH-12 | Vận hành | Không có việc chạy ngầm của danh mục. Danh mục thuộc tính không được nhét vào `seed.py` / `seed_prod.py` (deploy sau sẽ đè bản người dùng sửa, trái D-018) | [mô hình mục 11](../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) | Chưa đo |
