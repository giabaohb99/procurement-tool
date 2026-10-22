# SẢN XUẤT (MFG) — BỘ TÀI LIỆU

Bộ tài liệu chuẩn bị cho phân hệ **Quản lý sản xuất** của ERP DEGO. Hiện mới ở **giai đoạn nghiên cứu nghiệp vụ**: chưa có tài liệu yêu cầu, chưa có dòng mã, chưa có bảng nào.

---

## Các tệp

| Tệp | Nội dung | Đọc khi nào |
|---|---|---|
| [`00` Tổng quan nghiệp vụ](./00-tong-quan-nghiep-vu.md) | Thuật ngữ, quan hệ với Tồn kho, Mua hàng, Bán hàng, Kế toán. Quy trình sản xuất chuẩn. **Hạch toán giá thành theo Thông tư 99/2025** kèm bảng bút toán. **Đánh giá dở dang**, **phân bổ chi phí chung theo công suất bình thường**, **giá chuẩn và giá thực tế**, hàng lỗi, gia công ngoài, đồng sản phẩm. **Đối chiếu với mã nguồn ERP đang chạy** và **15 câu hỏi phải chốt** | Đọc đầu tiên |

---

## Đọc theo vai

- **Người quyết:** đọc `00` mục 14. Đó là các câu cần trả lời trước khi viết tài liệu yêu cầu. Câu B1 quan trọng nhất: bản đầu chỉ quản lý số lượng hay làm cả giá thành.
- **Kế toán:** đọc `00` mục 5 đến mục 9, rồi trả lời nhóm C ở mục 14.
- **Đội phần mềm:** đọc `00` mục 13 để biết phần nào đã có, phần nào phải làm mới, và bốn ràng buộc thiết kế không được phá.

---

## Ba điều quan trọng nhất

1. **Căn cứ là Thông tư 99/2025, không phải Thông tư 200.** Thông tư 200 hết hiệu lực từ 01/01/2026. Số hiệu các tài khoản sản xuất không đổi, nhưng kế toán phải soát lại tên tài khoản trước khi đưa vào hệ thống.
2. **Chọn giá chuẩn hay giá thực tế trước khi thiết kế bảng.** Hai cách cần hai cấu trúc dữ liệu khác nhau. Đổi sau là làm lại.
3. **Phần vượt mức bình thường không bao giờ nằm trong tồn kho.** Hỏng ngoài định mức và chi phí chung cố định khi chạy dưới công suất đều vào thẳng giá vốn trong kỳ. Hệ thống phải tách được hai phần này, nếu không giá trị tồn kho bị thổi phồng.

---

## Liên quan tới đâu

| Nơi khác | Quan hệ |
|---|---|
| [`erp/README.md`](../README.md) | Bộ tài liệu nền ERP |
| `doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md` | Luật của bảng sản phẩm. BOM phải tuân theo |
| [`nhap-khau/`](../nhap-khau/01-danh-sach-tinh-nang.md) | Nguyên liệu nhập khẩu cho nhà máy |

---

## Lịch sử

| Phiên bản | Ngày | Thay đổi |
|---|---|---|
| 1.0 | 21/10/2026 | Tạo bộ tài liệu. `00` viết lại từ bản tổng quan đại ca gửi: sửa tám chỗ, đổi căn cứ sang Thông tư 99, bổ sung các mục 6, 7, 8, 10, 13, 14 |
