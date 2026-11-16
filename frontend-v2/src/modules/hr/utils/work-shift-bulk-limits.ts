/** Trần một lượt ghi hàng loạt của `/api/work-shifts/bulk` và `/copy-week` — khớp `shift_schema.py` (duoc-CR-761). */
export const BULK_MAX_EMPLOYEES = 50
export const BULK_MAX_DATES = 42
export const BULK_MAX_CELLS = 500

/** Câu chặn lượt áp vượt trần của backend (chặn trước cho khỏi ăn 422); `null` = trong trần. */
export function bulkLimitMessage(employeeCount: number, dateCount: number): string | null {
  if (employeeCount > BULK_MAX_EMPLOYEES) return `Mỗi lượt tối đa ${BULK_MAX_EMPLOYEES} người.`
  if (dateCount > BULK_MAX_DATES) return `Mỗi lượt tối đa ${BULK_MAX_DATES} ngày.`
  if (employeeCount * dateCount > BULK_MAX_CELLS) return `Mỗi lượt tối đa ${BULK_MAX_CELLS} ô (người × ngày).`
  return null
}
