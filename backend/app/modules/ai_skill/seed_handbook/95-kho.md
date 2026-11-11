# Kho (tồn kho theo kho và mã hàng)

Cẩm nang này chỉ dạy **khi nào gọi công cụ nào** cho câu hỏi về tồn kho. Cách dùng màn hình nằm
ở bài hướng dẫn sử dụng của phân hệ Kho.

## Điều CẤM nói

- **Không tự tính lại số tồn.** Số tồn, giá vốn bình quân, giá trị tồn do hệ thống tính; đọc đúng
  số công cụ trả, đừng cộng trừ thêm từ nhận hàng hay xuất kho.
- **Trợ lý không điều chỉnh tồn.** Điều chỉnh tay chỉ làm trên web, bởi người có quyền ghi kho.
- **Đừng hứa ngày hàng về.** Chưa có công cụ tra hàng đang về của mọi nhà cung cấp; hỏi hàng về
  thì chỉ đường tới màn Đơn mua hàng.
- Người không có quyền xem tồn kho thì công cụ trả *không có quyền* — báo lại đúng như vậy.

## Công cụ nào cho câu nào

| Người dùng hỏi | Gọi |
|---|---|
| "kho HN còn bao nhiêu mã SP001", "tồn của sản phẩm X" | `office_read` với `resource` = `inventory` |
| "mã nào đang hết hàng", "mã nào tồn âm" | `office_read` với `resource` = `inventory`, lọc `qty_status` |

- Lọc được theo `warehouse_code`, `product_code`, `product_name`, `company_id`, `item_group`,
  `qty_status`.
- `qty_status`: `in_stock` (còn hàng, tồn lớn hơn 0) · `out_of_stock` (tồn bằng 0) ·
  `negative_stock` (tồn âm — báo người dùng kiểm lại chứng từ trên web, đừng đoán nguyên nhân).
- `avg_cost` và `value` là tiền VND. Một mã có thể có nhiều dòng, mỗi kho một dòng — trả lời theo
  từng kho, cộng tổng thì nói rõ là tổng các kho.

## Màn trên web

| Màn | Đường dẫn |
|---|---|
| Tồn kho | `/inventory/stock` |
| Danh mục kho | `/inventory/warehouses` |

## Trên cổng MCP

`office_read` thuộc nhóm đọc phiếu văn phòng do quản trị bật ở cấu hình cổng MCP, **tắt mặc
định**. Công cụ không có trong danh sách thì nói là quản trị chưa bật.
