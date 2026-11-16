import type { ShiftRow } from '../utils/work-shift-rows'
import { shiftTotalStats } from '../utils/work-shift-rows'

/**
 * Tóm tắt gọn bên phải tiêu đề "Khung giờ làm việc" của hộp xếp ca (duoc-CR-761): "8 giờ · 1 ngày công", không khung
 * nào thì "Nghỉ cả ngày · không tính công". Đọc lại khi khung đổi (`aria-live`).
 *
 * Có dòng đang lỗi (trùng giờ, Đến ≤ Từ) thì ghi "— giờ": tổng lúc đó là số tạm, dễ đọc nhầm thành giờ sẽ lưu.
 */
export function WorkShiftTotalStats({ rows, hasRowErrors = false }: { rows: readonly ShiftRow[]; hasRowErrors?: boolean }) {
  const stats = shiftTotalStats(rows)
  const off = rows.length === 0
  return (
    <p aria-live="polite" className="text-sm whitespace-nowrap text-muted-foreground tabular-nums">
      <span className="font-medium text-foreground">{off ? 'Nghỉ cả ngày' : hasRowErrors ? '— giờ' : stats.hours}</span>
      <span aria-hidden> · </span>
      <span>{off ? 'không tính công' : `${stats.workday} công`}</span>
    </p>
  )
}
