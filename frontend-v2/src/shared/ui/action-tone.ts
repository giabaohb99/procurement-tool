/**
 * Tông màu cho NÚT VIỀN ở dải nút chứng từ, theo đúng nghĩa màu của bản v1
 * (duoc-CR-737) — người dời từ v1 sang nhận ra nút bằng màu trước khi đọc chữ.
 *
 * Bản v1 (`frontend/src/index.css`, các lớp `.btn.*` + màu gắn tay ở trang):
 *   · `.btn` nền xanh đặc        → v2 `variant="default"` (không cần tông);
 *   · `.btn.secondary` chữ xanh  → `accent`  — bước quy trình phụ: Lưu, Gửi duyệt,
 *                                  Hoàn thành, Tạo YCTT, Tạo phiếu khảo sát…;
 *   · `.btn.ghost` chữ xám       → `neutral` — tiện ích: In, Sửa,
 *                                  Chuyển phòng xử lý, Mở lại;
 *   · chữ + viền đỏ              → `danger`  — Từ chối, Hủy đơn, Xóa;
 *   · chữ + viền hổ phách        → `warning` — Trả về, Hủy duyệt, Mở lại chặng chi phí;
 *   · chữ xanh lá                → `success` — Đã tạo N phiếu YCMH, Quyết toán tất cả.
 *
 * Dùng token ngữ nghĩa (`primary` / `destructive` / `warning` / `success`) nên chạy
 * được cả chế độ tối, và mã màu trùng hex bản v1 (`src/index.css`).
 * Gắn bằng `className={ACTION_TONE_CLASS.danger}` lên `<Button variant="outline">`.
 *
 * Đối chiếu ảnh v1 (06/11/2026, PYC07082603): nút `ghost` của v1 KHÔNG có nền
 * (`background: none`) nên ăn màu nền trang, chỉ nút `secondary` mới nền trắng.
 * Vì vậy `neutral` / `danger` / `warning` / `success` đều `bg-transparent`, còn
 * `accent` giữ nền trắng của `outline`. Viền đỏ v1 đậm hẳn (`var(--red)`), viền
 * hổ phách v1 nhạt (`#fcd34d` = amber-300).
 */
export const ACTION_TONE_CLASS = {
  /** v1 `.btn.ghost`: chữ xám xanh, rê chuột thì đậm lại. */
  neutral: 'bg-transparent text-muted-foreground hover:bg-background hover:text-foreground',
  accent: 'text-primary hover:text-primary',
  danger: 'border-destructive bg-transparent text-destructive hover:bg-destructive/10 hover:text-destructive',
  warning:
    'border-amber-300 bg-transparent text-warning hover:bg-warning/10 hover:text-warning dark:border-amber-700',
  success: 'border-success/50 bg-transparent text-success hover:bg-success/10 hover:text-success',
} as const

export type ActionTone = keyof typeof ACTION_TONE_CLASS
