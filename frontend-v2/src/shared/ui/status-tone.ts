/**
 * Bảng màu trạng thái dùng chung cho MỌI phân hệ.
 *
 * Nhóm theo Ý NGHĨA chứ không theo từng mã: mỗi loại chứng từ có bộ mã riêng
 * nhưng người đọc chỉ cần phân biệt năm tình huống — trung tính, đang chờ, đang
 * chạy, đã xong, bị chặn.
 *
 * Trước đây khai riêng trong `procurement/components/document-status-badge.tsx`.
 * Tách ra khi phân hệ Tài chính cần đúng bảng này: chép sang là hai phân hệ lệch
 * màu nhau từ lần sửa đầu tiên, mà người dùng đọc "vàng = đang chờ" theo thói
 * quen chứ không đọc tên phân hệ.
 */
export const TONE_CLASS = {
  neutral: 'bg-muted text-muted-foreground',
  pending: 'bg-warning/10 text-warning',
  progress: 'bg-info/10 text-info',
  done: 'bg-success/10 text-success',
  danger: 'bg-destructive/10 text-destructive',
} as const

export type StatusTone = keyof typeof TONE_CLASS
