# YÊU CẦU PHI CHỨC NĂNG — SẢN XUẤT

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-SX-NN`, ghi **mức đo được** và **cách kiểm**. Phân hệ chưa có mã nên cột *Hiện trạng* đều là
*Chưa đo*; yêu cầu nào chưa có nguồn ghi *Chưa có*. Các ràng buộc dưới lấy từ [`10`](10-tong-quan-nghiep-vu.md) §13.3 và
luật chung của hệ.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-SX-01 | Hiệu năng | Chưa có. Quy mô tham khảo từ khảo sát: 10–15 đơn mỗi ngày hoặc 15 đơn mỗi tuần (chưa thống nhất, [`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §5) | Bộ tiêu chí ở [rà soát API hiệu năng](../../../tai-lieu-ky-thuat/van-hanh/ra-soat-api-hieu-nang.md) khi có mã | Chưa đo |
| PCN-SX-02 | Phân quyền | Mỗi entity quyền mới (dự kiến `production`) phải khai đủ phạm vi trong `SCOPE_FIELDS`, lấy một bản ghi qua `get_scoped`; phạm vi xem theo nhà máy / pháp nhân. Luật hai trục ở [`CLAUDE.md`](../../../../CLAUDE.md) | `test_pham_vi_khai_du_b07.py` | Chưa đo |
| PCN-SX-03 | Dữ liệu nhạy cảm | Chưa có. Khảo sát ghi ba điểm nhạy cảm về chứng từ, thuế với NCC, không ghi trong tài liệu ([`04`](../nghien-cuu/04-san-xuat-tom-tat-cho-ban-dieu-hanh.md) §8) | Chưa có | Chưa đo |
| PCN-SX-04 | Giới hạn đầu vào | Cột `String(n)` phải có `max_length` khớp ở schema; danh sách con (dòng BOM, dòng phiếu) phải có trần số dòng | [`backend-input-limits.md`](../../../../.claude/rules/backend-input-limits.md); kiểm ở tầng schema | Chưa đo |
| PCN-SX-05 | Nhật ký và truy vết | Chưa có | Chưa có | Chưa đo |
| PCN-SX-06 | Lưu trữ và dọn dữ liệu | Chưa có | Chưa có | Chưa đo |
| PCN-SX-07 | Sao lưu và khôi phục | Chưa có (dữ liệu sẽ nằm trong CSDL ERP, theo bản sao lưu chung của [Nền tảng](../../nen-tang/chuc-nang/02-yeu-cau-phi-chuc-nang.md) PCN-NT-07) | Chưa có | Chưa đo |
| PCN-SX-08 | Đồng thời | Chưa có. Lưu ý dữ liệu: đơn giá bình quân di động hiện tính lại mỗi lần nhận hàng; thêm nhập thành phẩm với giá tạm thì phải quyết có tính lại bình quân khi chốt giá thật không | [`10`](10-tong-quan-nghiep-vu.md) §8.2, §13.3 | Chưa đo |
| PCN-SX-09 | Tích hợp | Dùng lại `tab_product` (nối bằng `product_code`), `tab_inventory`, `tab_inventory_move`, YCMH / ĐMH, công nợ phải trả, bộ máy duyệt. Không thêm bảng biến thể dưới `tab_product`, không đổi / tái dùng `product_code`, không đặt cột giá lên sản phẩm. Kế toán dùng MISA: ranh giới ERP sinh bút toán hay chỉ xuất số chưa chốt (câu C1) | [`10`](10-tong-quan-nghiep-vu.md) §3, §13.1, §13.3, §14; [mô hình dữ liệu sản phẩm](../../mat-hang/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) | Chưa đo |
| PCN-SX-10 | Khả dụng và thiết bị | Chưa có | Chưa có | Chưa đo |
| PCN-SX-11 | Pháp lý | Hạch toán theo Thông tư 99/2025/TT-BTC (hiệu lực 01/01/2026) và Chuẩn mực kế toán số 02 *Hàng tồn kho*; phần vượt mức bình thường vào thẳng giá vốn, không vào tồn kho; pháp nhân theo chế độ doanh nghiệp nhỏ và vừa thì không dùng 621, 622, 627 (câu C3). Chứng từ phải mang đúng pháp nhân nhận hóa đơn | [`10`](10-tong-quan-nghiep-vu.md) §1, §5, §7; [`02`](../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md) §7 dòng 8 | Chưa đo |
| PCN-SX-12 | Vận hành | Chưa có | `/api/system/jobs` khi có việc chạy ngầm | Chưa đo |
