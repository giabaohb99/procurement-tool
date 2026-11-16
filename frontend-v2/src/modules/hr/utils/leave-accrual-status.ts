import { formatDate } from '@/shared/utils/format-date'
import { LEAVE_ACCRUAL_STATUS, type LeaveAccrualInfo } from '../types/leave'

/**
 * Luật HIỂN THỊ tình trạng tích phép của loại `MONTHLY_AFTER` (duoc-CR-762) — một chỗ cho bảng quỹ, ma trận,
 * trang chi tiết và hộp số dư trong đơn nghỉ.
 *
 * Chữ của nhãn LUÔN lấy từ `accrual_status_label` của API — ở đây chỉ chia mã thành ba TÔNG:
 *  · `none`  — 1 Đang tích: không thêm chữ nào, chỉ gợi ý rê chuột *Tích từ dd/mm/yyyy*;
 *  · `muted` — 2 Thử việc · 5 HĐ dịch vụ / CTV · 6 Chưa tới ngày chính thức: không tích, chuyện bình thường;
 *  · `warn`  — 3 Chưa có HĐLĐ · 4 Lịch sử HĐLĐ chưa đủ: số đang tính tạm, Nhân sự phải nhập hợp đồng. Gọi chung là
 *    *chưa đủ HĐLĐ*; dải đếm và luật ẩn nhãn quá nửa (phương án B) đều tính theo nhóm này.
 *
 * `null` / vắng (loại nghỉ chế độ khác, backend cũ) / mã lạ → không vẽ gì.
 */

export type AccrualTone = 'none' | 'muted' | 'warn'

const MUTED_STATUSES: readonly number[] = [
  LEAVE_ACCRUAL_STATUS.PROBATION,
  LEAVE_ACCRUAL_STATUS.SERVICE_CONTRACT,
  LEAVE_ACCRUAL_STATUS.NOT_YET_OFFICIAL,
]
const WARN_STATUSES: readonly number[] = [
  LEAVE_ACCRUAL_STATUS.MISSING_CONTRACT,
  LEAVE_ACCRUAL_STATUS.INCOMPLETE_HISTORY,
]

/** Tông hiển thị của một mã; `null` = không phải tình trạng tích (loại nghỉ chế độ khác hoặc mã lạ). */
export function getAccrualTone(status: number | null | undefined): AccrualTone | null {
  if (status === LEAVE_ACCRUAL_STATUS.ACCRUING) return 'none'
  if (status != null && MUTED_STATUSES.includes(status)) return 'muted'
  if (status != null && WARN_STATUSES.includes(status)) return 'warn'
  return null
}

/** Dòng / người này *chưa đủ HĐLĐ* (mã 3 hoặc 4). */
export function isContractWarning(status: number | null | undefined): boolean {
  return getAccrualTone(status) === 'warn'
}

/**
 * Câu VIỆC CẦN LÀM đi kèm nhãn hổ phách (không phải nhãn — nhãn là của API). Mã 3 giữ đúng câu người chủ chốt.
 */
export function getContractActionHint(status: number | null | undefined): string | null {
  if (status === LEAVE_ACCRUAL_STATUS.MISSING_CONTRACT) {
    return 'Đang tính từ ngày vào làm — nhập hợp đồng lao động để tính đúng'
  }
  if (status === LEAVE_ACCRUAL_STATUS.INCOMPLETE_HISTORY) return 'Nhập đủ hợp đồng lao động để tính đúng'
  return null
}

/** Câu gợi ý *Tích từ dd/mm/yyyy* cho người đang tích; mọi trường hợp khác `null`. */
export function getAccrualStartHint(info: LeaveAccrualInfo | null | undefined): string | null {
  if (info?.accrual_status !== LEAVE_ACCRUAL_STATUS.ACCRUING || !info.accrual_start_date) return null
  const date = formatDate(info.accrual_start_date)
  return date ? `Tích từ ${date}` : null
}

/** Mức "cần chú ý": Chưa có HĐLĐ > Lịch sử chưa đủ > (thử việc, HĐ dịch vụ, chưa chính thức) > Đang tích > không có. */
function rankAccrualStatus(status: number | null | undefined): number {
  if (status === LEAVE_ACCRUAL_STATUS.MISSING_CONTRACT) return 5
  if (status === LEAVE_ACCRUAL_STATUS.INCOMPLETE_HISTORY) return 4
  const tone = getAccrualTone(status)
  if (tone === 'muted') return 3
  if (tone === 'none') return 1
  return 0
}

/**
 * Tình trạng đại diện cho cả NHÓM dòng quỹ của một người (hàng cha của bảng gom). Lấy cái cần chú ý nhất — người
 * có hai loại `MONTHLY_AFTER` mà một loại báo thiếu HĐLĐ thì hàng cha phải nói ra điều đó.
 */
export function pickAccrualInfo(
  items: readonly LeaveAccrualInfo[],
  /** Bỏ qua dòng *chưa đủ HĐLĐ* — khi bảng đang ẩn nhãn đó, nhãn tông mờ của dòng khác vẫn phải hiện. */
  excludeContractWarning = false,
): LeaveAccrualInfo | null {
  let best: LeaveAccrualInfo | null = null
  for (const item of items) {
    if (excludeContractWarning && isContractWarning(item.accrual_status)) continue
    if (rankAccrualStatus(item.accrual_status) > rankAccrualStatus(best?.accrual_status)) best = item
  }
  return best
}

/** Một dòng "người × tình trạng tích" — dòng quỹ đã có sẵn dạng này; ô ma trận thì trải ra bằng `matrixAccrualEntries`. */
export type EmployeeAccrualEntry = LeaveAccrualInfo & { employee_id: number }

/**
 * Tóm tắt người *chưa đủ HĐLĐ* (mã 3 + 4) trong phần đang hiển thị (duoc-CR-762, phương án B của người chủ):
 *  · `missing` — số NGƯỜI có ít nhất một dòng chưa đủ HĐLĐ;
 *  · `total`   — số NGƯỜI có ít nhất một dòng thuộc loại cộng dần sau mỗi tháng làm đủ (mã hợp lệ);
 *  · `showRowBadges` — nhãn hổ phách trên TỪNG DÒNG chỉ bày khi `missing` ≤ một nửa `total`. Quá nửa thì nhãn phủ kín
 *    bảng và mất nghĩa, chỉ còn dải đếm ở đầu bảng nói thay.
 * Đếm theo người, không theo dòng.
 */
export interface MissingContractSummary {
  missing: number
  total: number
  showRowBadges: boolean
}

export function summarizeMissingContract(entries: readonly EmployeeAccrualEntry[] | undefined): MissingContractSummary {
  const tracked = new Set<number>()
  const missing = new Set<number>()
  for (const entry of entries ?? []) {
    if (getAccrualTone(entry.accrual_status) === null) continue
    tracked.add(entry.employee_id)
    if (isContractWarning(entry.accrual_status)) missing.add(entry.employee_id)
  }
  return { missing: missing.size, total: tracked.size, showRowBadges: missing.size * 2 <= tracked.size }
}

/** Trải ô `accrual` của các dòng ma trận thành danh sách người × tình trạng để dùng chung `summarizeMissingContract`. */
export function matrixAccrualEntries(
  rows: readonly { employee_id: number; accrual?: Record<string, LeaveAccrualInfo> }[] | undefined,
): EmployeeAccrualEntry[] {
  return (rows ?? []).flatMap((row) =>
    Object.values(row.accrual ?? {}).map((info) => ({ ...info, employee_id: row.employee_id })),
  )
}

/** Người (nhóm dòng quỹ) này có dòng nào *chưa đủ HĐLĐ* không — dùng cho nút lọc ở dải đếm. */
export function hasMissingContract(balances: readonly LeaveAccrualInfo[]): boolean {
  return balances.some((b) => isContractWarning(b.accrual_status))
}
