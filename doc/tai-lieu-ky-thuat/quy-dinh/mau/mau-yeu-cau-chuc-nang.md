# YÊU CẦU CHỨC NĂNG — <TÊN PHÂN HỆ>

| | |
|---|---|
| Bản | 1.0 |
| Ngày | DD/MM/YYYY |
| Người phụ trách | <tên> |
| Trạng thái | Nháp / Hiệu lực |
| CR liên quan | <mã CR> |

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| | |

## 2. Danh sách chức năng

Mỗi chức năng một mã cố định `CN-<PHÂN HỆ>-NN` (không tái dùng số khi bỏ). Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-XX-01 | | | | | |

## 3. Chi tiết từng chức năng

### CN-XX-01 — <tên chức năng>

- **Mục đích:** một câu.
- **Luồng chính:** các bước người dùng làm, kết quả.
- **Luật nghiệp vụ:** điều kiện, ràng buộc, trạng thái chứng từ đổi thế nào.
- **Dữ liệu:** trường nhập chính, trường bắt buộc, giá trị mặc định.
- **Quyền:** khóa `entity.action` cần có; phạm vi dữ liệu áp dụng.
- **Ngoại lệ / lỗi người dùng gặp:** câu báo lỗi và lúc nào hiện.
- **Liên quan:** chức năng khác, phân hệ khác, công cụ AI / MCP dùng chức năng này.

## 4. Luồng trạng thái chứng từ (nếu có)

```
Nháp → Chờ duyệt → Đã duyệt → ...
```

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
