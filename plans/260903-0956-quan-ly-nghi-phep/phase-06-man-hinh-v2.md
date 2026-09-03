# P-06 — Màn hình `frontend-v2` ✅ XONG (CR-259)

## Đã làm — 5 màn, nằm TRONG phân hệ Nhân sự

| Màn | Đường dẫn | Tệp |
|---|---|---|
| Đơn nghỉ phép (danh sách) | `/hr/leave-requests` | `pages/leave-request-list-page.tsx` |
| Đơn nghỉ phép (chi tiết + nộp mới) | `/hr/leave-requests/{new,:id}` | `pages/leave-request-detail-page.tsx` |
| Lịch nghỉ (theo tuần) | `/hr/leave-calendar` | `pages/leave-calendar-page.tsx` |
| Quỹ phép năm | `/hr/leave-balances` | `pages/leave-balance-page.tsx` |
| Loại nghỉ · Lịch ngày lễ | `/hr/leave-types` · `/hr/holidays` | khung CRUD khai báo, `config/leave-type-crud.tsx` · `config/holiday-crud.tsx` |

Hạ tầng: `types/leave.ts` · `api/leave-api.ts` · `hooks/use-leave.ts` · sáu
component (`leave-request-form`, `leave-request-summary`, `leave-balance-hint-box`,
`my-leave-balance-card`, `adjust-balance-dialog`, `seniority-tier-card`,
`leave-status-badge`) · `utils/leave-form-values.ts`.

## Quyết định đáng ghi

- **Nằm trong phân hệ Nhân sự, không tách phân hệ riêng.** Người dùng đi tìm "xin
  nghỉ phép" ở chỗ họ tìm hồ sơ nhân sự, không ở một ô thứ hai trên màn chọn phân hệ.
- **Ô «số phép còn lại» đứng NGAY CẠNH ô loại nghỉ, cùng hàng** — đây là ràng buộc
  §6.1 và là lý do tồn tại của cả đợt. Bốn nhánh hiển thị: chưa chọn loại · loại
  không trừ quỹ · đủ phép · **vượt quỹ** (đỏ, kèm câu chỉ đường sang «Nghỉ không
  lương», đúng câu backend sẽ chặn).
- **Đơn đã gửi duyệt dựng `LeaveRequestSummary`, KHÔNG dựng form với `disabled`.**
  Luật của bộ ERP: ô chỉ xem cấm `<Input disabled>` — `disabled` gỡ luôn khả năng
  nhận con trỏ nên không bôi đen, không copy được, lại bị làm mờ nhìn như chữ gợi ý.
- **Nạp dữ liệu vào form bằng `useHasChanged(id)` trong lúc render**, không bằng
  `useEffect`: effect chạy sau khi commit nên người dùng thấy một khung hình form
  rỗng rồi mới thấy dữ liệu. Và so theo **`id`**, không theo tham chiếu `request` —
  theo tham chiếu thì mọi lượt nạp lại cache xóa những gì họ vừa gõ.
- **`SelectValue` truyền children tường minh** ở hai ô buổi — Radix sao chép
  children của mục đang chọn vào ô kích hoạt nếu không truyền (lỗi CR-258).
- **Thẻ «Quỹ phép của tôi» tự tắt khi thiếu `leave_balance.read`** — không có nhánh
  đó thì cứ mount là gọi và người dùng ăn toast 403 ngay lúc mở màn (bẫy CR-106).
- **Lịch nghỉ dựng theo TUẦN**, lọc theo **giao nhau của khoảng** (`from_date <= iso
  <= to_date`), và chỉ hiện đơn **Chờ duyệt / Đã duyệt** — vẽ đơn nháp hay đơn đã
  hủy lên lịch là xếp việc sai. Ngày ISO cắt tay theo giờ **địa phương**:
  `toISOString()` quy về UTC nên cả lịch lệch một ngày.
- **`LeaveType` và `Holiday` khai bằng `type` chứ không `interface`** — TypeScript
  chỉ cấp chỉ mục ngầm cho type alias, nên `CrudConfig<LeaveType>` không gán được
  vào `CrudConfig<CrudRecord>` nếu dùng `interface`.
- **Điều chỉnh quỹ ghi ĐÈ, không cộng dồn**, và hộp thoại **xem trước** số còn lại
  sau khi lưu — bắt người dùng tự cộng trừ là bắt họ tính sai.

## Nghiệm thu

`npm run check` xanh cả ba cổng: typecheck **0 lỗi** · lint **0 lỗi / 32 cảnh báo**
(đúng mức nền, không thêm cái nào) · **2049 test** qua (182 tệp), trong đó 24 bài
mới của đợt này. Đã kiểm bài kiểm có cắn: đổi `<=` thành `<` ở ngưỡng đủ phép làm
đúng 2 bài đỏ.
