# P-04 — API đơn nghỉ phép ✅ XONG (CR-259)

## Đã làm

| Tệp | Việc |
|---|---|
| `leave/schema.py` | Pydantic cho cả bốn nhóm bảng. |
| `leave/request_service.py` | Lập · sửa · xóa mềm · chốt gửi duyệt · hủy. |
| `leave/request_controller.py` | `/api/leave-requests` — CRUD + `submit` · `approve` · `reject` · `cancel` + hai endpoint trợ giúp form. |
| `leave/catalog_controller.py` | `/api/leave-types` · `/api/holidays` (khung `make_crud_router`) + `/api/leave-seniority-tiers` (viết tay). |
| `leave/balance_controller.py` | `/api/leave-balances` + `allocate` + `adjust` + `tools/summary`. |
| `app/main.py` | Đăng ký 5 router + nạp `approval_bridge` **không lười**. |

## Quyết định đáng ghi

- **Chốt "nhập đủ" đặt ở lúc GỬI DUYỆT**, không phải lúc lưu nháp — cùng luật với
  `required-fields.ts` của Thu mua và `type_metadata.require_on_submit`.
- **`prepare_submit` tách khỏi `mark_submitted`** để controller kiểm hết mọi chốt
  *trước khi* đụng vào bộ máy duyệt. Trình phiếu xong mới phát hiện hết phép thì
  phải đi rút phiếu, và người dùng đã kịp thấy một phiếu duyệt hiện ra rồi biến mất.
- **`/tools/my-balance` gác bằng `leave_request.read`**, không phải `leave_balance.read`.
  Đây là quỹ của chính người đang nộp; ai nộp được đơn thì phải thấy số còn lại.
  Bắt cấp thêm một khóa nữa là chắc chắn có người quên cấp rồi ô đó hiện 0 vĩnh viễn.
- **Hai endpoint trợ giúp đặt dưới `/tools/`** — đường một đoạn thì rơi vào `/{rid}`
  và ăn lỗi ép kiểu số.
- **`total_days` chỉ coi là "sửa đè" khi client GỬI LÊN nó.** Không gửi thì tính
  lại — sửa ngày mà giữ nguyên số ngày cũ là sai ngay lập tức.
- **`cancel` KHÔNG gọi `block_legacy_path`** — xem P-05.
- **Chặn xóa loại nghỉ đang có đơn hoặc có quỹ** (`before_delete`), và **cấm đổi
  `code`** (hai lớp: schema không có trường đó, cộng `before_update`).
- **Bậc thâm niên không phân trang** và **chặn khoảng chồng nhau** — chồng thì
  `seniority_days` vẫn ra một con số, chỉ là không phải con số người khai định.

## Nghiệm thu

`test_nghi_phep_don_va_duyet.py` (32 bài) + chạy thử thật qua `TestClient` trong
container: tạo → chi tiết → gửi duyệt → quỹ tụt 12 → 9 → hủy → quỹ về 12.
