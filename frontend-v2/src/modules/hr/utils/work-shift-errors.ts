import { extractErrorMessage } from '@/core/api/response-envelope'
import type { WorkShiftCopyWeekResult, WorkShiftRejection } from '../types/work-shift'

/**
 * Đọc lỗi của lượt ghi hàng loạt (duoc-CR-761). Backend từ chối CẢ lượt khi một ô sai, mã lỗi `shift_rejected`, kèm
 * `error.details.rejected = [{employee_id, work_date|null, code, message}]`. Câu gộp của backend chỉ nêu lý do đầu
 * tiên — người dùng cần biết ĐÍCH DANH ô nào để bỏ ra, nên dựng lại thành danh sách đọc được.
 */

export const SHIFT_REJECTED_CODE = 'shift_rejected'

function isRejection(value: unknown): value is WorkShiftRejection {
  if (!value || typeof value !== 'object') return false
  const row = value as Record<string, unknown>
  return typeof row.employee_id === 'number' && typeof row.code === 'string'
}

/** Danh sách ô bị từ chối; `null` khi lỗi không phải `shift_rejected` (lỗi mạng, 409, 422 khung sai…). */
export function readShiftRejections(error: unknown): WorkShiftRejection[] | null {
  if (!error || typeof error !== 'object') return null
  const body = (error as { response?: { data?: { error?: { code?: unknown; details?: unknown } } } }).response?.data
  const err = body?.error
  if (!err || err.code !== SHIFT_REJECTED_CODE) return null
  const rejected = (err.details as { rejected?: unknown } | null | undefined)?.rejected
  if (!Array.isArray(rejected)) return []
  return rejected.filter(isRejection).map((r) => ({
    employee_id: r.employee_id,
    work_date: typeof r.work_date === 'string' ? r.work_date : null,
    code: r.code,
    message: typeof r.message === 'string' && r.message ? r.message : 'Không xếp được ô này',
  }))
}

/** "2026-11-17" → "17/11/2026"; chuỗi hỏng giữ nguyên. */
export function formatVnDate(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  return match ? `${match[3]}/${match[2]}/${match[1]}` : iso
}

/** Trần số dòng bày ra; phần còn lại gộp thành "và N ô khác" để hộp thoại không dài vô tận (500 ô một lượt). */
export const MAX_REJECTION_LINES = 8

/**
 * Câu cho từng ô bị từ chối: "Nguyễn An · 17/11/2026: Chỉ xếp ca từ hôm nay trở đi". Ô cấp nhân sự (`work_date`
 * null) không có ngày. Tên không tra được → "Nhân sự #id" (người đó không có trên trang đang xem).
 */
export function describeShiftRejections(
  rejections: readonly WorkShiftRejection[],
  nameOf: (employeeId: number) => string | undefined,
): string[] {
  const lines = rejections.slice(0, MAX_REJECTION_LINES).map((r) => {
    const who = nameOf(r.employee_id) || `Nhân sự #${r.employee_id}`
    const when = r.work_date ? ` · ${formatVnDate(r.work_date)}` : ''
    return `${who}${when}: ${r.message}`
  })
  const rest = rejections.length - MAX_REJECTION_LINES
  if (rest > 0) lines.push(`và ${rest} ô khác`)
  return lines
}

/** Lỗi bày trong hộp thoại: câu chính + (nếu có) danh sách ô bị từ chối. */
export interface ShiftErrorView {
  message: string
  lines: string[]
}

export function toShiftErrorView(error: unknown, nameOf: (employeeId: number) => string | undefined): ShiftErrorView {
  const rejections = readShiftRejections(error)
  if (rejections && rejections.length > 0) {
    return {
      message: `Không ô nào được lưu — ${rejections.length} ô bị từ chối:`,
      lines: describeShiftRejections(rejections, nameOf),
    }
  }
  return { message: extractErrorMessage(error), lines: [] }
}

/** Số ngày có đơn nghỉ nêu đích danh trong câu báo; còn lại gộp "và N ngày khác". */
const MAX_LEAVE_ITEMS = 3

/**
 * Câu báo kết quả Chép tuần trước, nêu đủ số tạo / cập nhật / giữ nguyên / ngày đã qua / ngày có đơn nghỉ — ngày có
 * đơn nghỉ nêu đích danh người · ngày · mã đơn để người xếp biết phải xử lý đơn nào.
 */
export function formatCopyWeekResult(
  result: WorkShiftCopyWeekResult,
  nameOf: (employeeId: number) => string | undefined = () => undefined,
): string {
  const skippedLeave = result.skipped_leave ?? 0
  if (result.changed === 0 && result.skipped === 0 && result.skipped_past === 0 && skippedLeave === 0) {
    return 'Tuần trước không có ca xếp riêng nào để chép.'
  }
  const parts: string[] = []
  if (result.created > 0) parts.push(`thêm ${result.created} ngày`)
  if (result.updated > 0) parts.push(`ghi đè ${result.updated} ngày`)
  if (result.skipped > 0) parts.push(`giữ nguyên ${result.skipped} ngày đã có ca`)
  if (result.skipped_past > 0) parts.push(`bỏ qua ${result.skipped_past} ngày đã qua`)
  if (skippedLeave > 0) {
    const items = result.leave_conflicts ?? []
    const named = items
      .slice(0, MAX_LEAVE_ITEMS)
      .map(
        (it) =>
          `${nameOf(it.employee_id) || `Nhân sự #${it.employee_id}`} ${formatVnDate(it.work_date).slice(0, 5)} (${it.request_code || 'đơn nghỉ'})`,
      )
    const rest = items.length - named.length
    const detail = named.length > 0 ? `: ${named.join(', ')}${rest > 0 ? ` và ${rest} ngày khác` : ''}` : ''
    parts.push(`bỏ qua ${skippedLeave} ngày đã có đơn nghỉ${detail}`)
  }
  const head = result.changed > 0 ? 'Đã chép ca' : 'Không có ngày nào được chép'
  return `${head}: ${parts.join(', ')}.`
}
