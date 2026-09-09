import type { LeaveBalance } from '../types/leave'

/**
 * Dòng quỹ này có QUỸ THẬT không — tức có gì để mà tiêu hết hay không.
 *
 * ⚠️ Đây là thứ phân biệt hai nghĩa của con số **0 còn lại**, mà chúng ngược
 * hẳn nhau: *«đã tiêu hết phép»* (đáng báo động, tô đỏ) và *«loại nghỉ này công
 * ty không cấp hạn mức»* (bình thường, để mờ). Bảng quỹ của một người có tám
 * dòng thì sáu dòng thuộc vế sau — Nghỉ tang chế, Nghỉ bù, Nghỉ cưới hỏi… đều
 * hạn mức 0. Tô đỏ hết thì màu đỏ mất nghĩa đúng ở chỗ nó cần có nghĩa nhất.
 *
 * Không chỉ hỏi `allocated_days`: phép mang sang từ năm trước và điều chỉnh tay
 * cũng là quỹ tiêu được, nên người có `allocated_days = 0` nhưng được chuyển
 * sang 3 ngày mà tiêu hết thì vẫn là *hết phép*.
 */
export function hasQuota(balance: LeaveBalance): boolean {
  return (
    balance.allocated_days > 0 ||
    balance.seniority_days > 0 ||
    balance.carried_days > 0 ||
    balance.adjusted_days !== 0
  )
}
