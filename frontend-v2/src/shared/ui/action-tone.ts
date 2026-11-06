/**
 * Tông màu cho NÚT VIỀN ở dải nút chứng từ, theo đúng nghĩa màu của bản v1
 * (duoc-CR-737) — người dời từ v1 sang nhận ra nút bằng màu trước khi đọc chữ.
 *
 * Bản v1 (`frontend/src/index.css`, các lớp `.btn.*` + màu gắn tay ở trang):
 *   · `.btn` nền xanh đặc        → v2 `variant="default"` (không cần tông);
 *   · `.btn.secondary` chữ xanh  → `accent`  — bước quy trình phụ: Lưu, Gửi duyệt,
 *                                  Hoàn thành, Tạo YCTT, Tạo phiếu khảo sát…;
 *   · `.btn.ghost` chữ xám       → để trơn `variant="outline"` — tiện ích: In,
 *                                  Chuyển phòng xử lý, Mở lại;
 *   · chữ + viền đỏ              → `danger`  — Từ chối, Hủy đơn, Xóa;
 *   · chữ + viền hổ phách        → `warning` — Trả về, Hủy duyệt, Mở lại chặng chi phí;
 *   · chữ xanh lá                → `success` — Đã tạo N phiếu YCMH, Quyết toán tất cả.
 *
 * Dùng token ngữ nghĩa (`primary` / `destructive` / `warning` / `success`) nên chạy
 * được cả chế độ tối, và mã màu trùng hex bản v1 (`src/index.css`).
 * Gắn bằng `className={ACTION_TONE_CLASS.danger}` lên `<Button variant="outline">`.
 */
export const ACTION_TONE_CLASS = {
  accent: 'text-primary hover:text-primary',
  danger: 'border-destructive/50 text-destructive hover:bg-destructive/10 hover:text-destructive',
  warning: 'border-warning/50 text-warning hover:bg-warning/10 hover:text-warning',
  success: 'border-success/50 text-success hover:bg-success/10 hover:text-success',
} as const

export type ActionTone = keyof typeof ACTION_TONE_CLASS
