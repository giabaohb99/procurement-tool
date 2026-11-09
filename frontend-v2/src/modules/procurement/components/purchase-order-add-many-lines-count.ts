/** Trần số dòng một lần thêm — gõ nhầm 30000 thì trình duyệt không treo vì dựng 30000 ô nhập. */
export const ADD_MANY_LINES_MAX = 200

/**
 * Đổi chữ người gõ thành số dòng cần thêm, theo đúng bản v1: không đọc được (rỗng, chữ, số âm,
 * 0) thì vẫn thêm 1 dòng. Khác v1 duy nhất ở trần `ADD_MANY_LINES_MAX`.
 */
export function parseAddManyLinesCount(raw: string): number {
  const parsed = Number.parseInt(raw.trim(), 10)
  return Math.min(ADD_MANY_LINES_MAX, Math.max(1, Number.isFinite(parsed) ? parsed : 0))
}
