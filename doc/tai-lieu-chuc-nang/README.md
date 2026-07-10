# Tài liệu chức năng — Mini Tool Quản lý Thu Mua

Mỗi chức năng một file riêng. Khi có thay đổi (thêm/bớt trường, đổi quyền, đổi luồng),
cập nhật trực tiếp vào file tương ứng.

Mục lục toàn bộ tính năng: [00-muc-luc.md](00-muc-luc.md)

## Tài liệu đã có

| File | Chức năng |
|------|-----------|
| [01-phieu-khao-sat.md](01-phieu-khao-sat.md) | Phiếu khảo sát (NCC + Sản phẩm) |

## Quy ước cột trong bảng trường

- **Trường**: tên hiển thị (kèm mã kỹ thuật trong ngoặc).
- **Kiểu nhập**: Nhập tay / Nhập số / Nhập nhiều dòng / Chọn (danh sách) / Chọn ngày / Checkbox / Tự tính / Tự động.
- **Mặc định**: giá trị khi mới tạo dòng (trường số mặc định 0 nhưng hiển thị trống).
- **Bắt buộc**: `Không` / `Khi gửi duyệt` (không bắt buộc lúc Nháp, bắt buộc khi bấm Gửi duyệt) / `Có`.
- **Nguồn / Giá trị**: bảng nguồn (nếu Chọn) hoặc danh sách giá trị cố định.
- **Người sửa**: vai trò được phép chỉnh + điều kiện trạng thái.

## Vai trò quy ước

- **NSPT / Người tạo phiếu**: quyền `survey:write` (hoặc `create` khi tạo mới). Sửa các trường nội dung.
- **TP/QL / Người duyệt**: quyền `survey:approve`. Chỉ sửa các trường duyệt.
