# Duyệt dấu (phiếu yêu cầu đóng dấu)

Cẩm nang này chỉ dạy **khi nào gọi công cụ nào** cho câu hỏi về xin đóng dấu. Quy trình chi tiết
nằm ở bài hướng dẫn sử dụng của phân hệ Duyệt dấu.

## Điều CẤM nói

- **Đừng báo là đã gửi duyệt** phiếu duyệt dấu. Trợ lý chỉ lưu được phiếu ở *Nháp*; gửi duyệt
  cần tệp chứng từ đính kèm nên người dùng phải tự làm trên web.
- **Đừng báo là đã đóng dấu** khi phiếu mới *Đã duyệt*. Dấu chỉ được đóng khi phiếu sang
  *Hoàn thành*.
- Phiếu ngoài phạm vi thì công cụ không trả — nói là **không truy cập được**, đừng nói phiếu không
  tồn tại.

## Công cụ nào cho câu nào

| Người dùng hỏi | Gọi |
|---|---|
| "phiếu xin dấu của tôi duyệt chưa", "tháng này xin dấu bao nhiêu lần" | `office_read` với `resource` = `seal_request` |
| "xem phiếu duyệt dấu số 45" | `office_read` với `resource` = `seal_request`, `id` = 45 |
| "xin đóng dấu hợp đồng đại lý cho công ty X, 2 bản" | `draft_seal_request` |

- `office_read` đọc **đúng như màn danh sách trên web**, đúng phạm vi quyền của người hỏi. Lọc
  được theo `search`, `status`, `seal_type_id`, `company_id`, `department_id`.
- Mỗi dòng có `url` mở màn chi tiết; đưa đường dẫn đó cho người dùng.

## Soạn phiếu bằng `draft_seal_request`

- Cần đủ: **mục đích** (giấy tờ gì, dùng vào việc gì) và **công ty cần đóng dấu** (một hoặc
  nhiều). Thiếu gì công cụ trả câu hỏi — hỏi người dùng **một câu**.
- `title` là tên chứng từ, `copies` là số bản (mặc định 1).
- **Người phê duyệt** bỏ trống thì lấy người duyệt mặc định của người hỏi. Tên mơ hồ thì công cụ
  trả danh sách để chọn.
- Có bản nháp rồi: đưa người dùng xem, họ đồng ý rõ thì xác nhận nháp với kind `seal_request`
  (trên cổng MCP là `confirm_draft`), **không** truyền `submit=true`. Sau đó nhắc họ mở phiếu trên
  web, tải tệp chứng từ cần đóng dấu rồi bấm *Gửi duyệt*.
- Người không có quyền lập phiếu duyệt dấu thì công cụ trả *không có quyền* — báo lại đúng như vậy.

## Trạng thái phiếu — đọc nhãn, đừng đoán

`Nháp → Chờ duyệt → Đã duyệt → Hoàn thành`, cộng ba ngã rẽ *Từ chối*, *Đã hủy*, *Yêu cầu chỉnh
sửa*.

- *Chờ duyệt*: đang chờ người phê duyệt. *Đã duyệt*: chờ Văn thư đóng dấu. *Hoàn thành*: Văn thư đã
  đóng dấu ngoài thực tế.
- *Từ chối* là khóa hẳn, muốn xin lại thì lập phiếu khác. *Yêu cầu chỉnh sửa* là sửa rồi gửi lại
  chính phiếu đó.
- Sửa, hủy, duyệt, đánh dấu đã đóng dấu làm trên web, trợ lý không làm.

## Màn trên web

| Màn | Đường dẫn |
|---|---|
| Tổng quan | `/approval-seal` |
| Danh sách phiếu | `/approval-seal/requests` |
| Lập phiếu mới | `/approval-seal/new` |
| Loại con dấu | `/approval-seal/seal-types` |
| Phân công văn thư | `/approval-seal/clerks` |

## Trên cổng MCP

Hai nhóm công cụ do quản trị bật ở cấu hình cổng MCP, **tắt mặc định**: nhóm đọc (`office_read`)
và nhóm lập phiếu (`draft_seal_request`). Công cụ không có trong danh sách thì nói là quản trị chưa
bật, đừng đoán số liệu.
