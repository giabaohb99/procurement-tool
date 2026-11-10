import { orderedValues, type StatusOption } from '@/shared/constants/statuses'

/**
 * Số thứ tự DÒNG ĐỜI của một mã trạng thái, để xếp cột trạng thái theo đúng tiến trình
 * thay vì theo chữ cái của mã tiếng Anh (duoc-CR-744) — cùng luật với
 * `backend/app/core/code_rank_sql.py`: chuỗi tiến trình trước, mã ngoại lệ (Tạm ngưng,
 * Hủy) sau theo thứ tự khai, mã lạ cuối cùng.
 *
 * Ô trống trả `null` để bảng xếp nó xuống cuối như mọi ô trống khác.
 */
export function getStatusRank(
  options: readonly StatusOption[],
  value: string | null | undefined,
): number | null {
  if (!value) return null
  const chain = orderedValues(options)
  const exceptions = options.filter((o) => !chain.includes(o.value)).map((o) => o.value)
  const rank = [...chain, ...exceptions].indexOf(value)
  return rank === -1 ? chain.length + exceptions.length : rank
}
