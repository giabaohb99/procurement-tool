import type { DataTableColumn } from './types'

/**
 * Cột «ID» mặc định của MỌI bảng danh sách (bao-CR-578, đại ca chốt 03/10/2026: «thêm mặc
 * định cột ID ở phía bìa trái, như vậy dễ nhìn hơn»).
 *
 * Bảng TỰ thêm, màn hình không phải khai. Khóa riêng `__row_id` để không đụng cột `id` mà vài
 * màn đã tự khai — màn nào đã có cột `id` thì bảng KHÔNG thêm nữa (tránh hai cột ID).
 */
export const ID_COLUMN_KEY = '__row_id'

/** Khóa các cột tick chọn — cột ID đứng NGAY SAU chúng, không chen lên trước ô tick. */
const LEADING_KEYS = new Set(['select'])

/** `id` số của một hàng; hàng không có `id` số (bảng gộp, báo cáo) thì `null`. */
export function readRowId(row: unknown): number | null {
  if (!row || typeof row !== 'object') return null
  const value = (row as { id?: unknown }).id
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

/**
 * Có thêm cột ID không.
 *
 * - Màn tắt (`enabled = false`) hoặc đã tự khai cột `id` → không.
 * - Đang tải (`rows` chưa có) hoặc danh sách rỗng → CÓ, kẻo cột hiện ra rồi biến mất làm bảng nhảy.
 * - Đã có dữ liệu mà không hàng nào mang `id` số (bảng gộp theo nhóm) → không, khỏi một cột toàn gạch.
 */
export function shouldShowIdColumn<T>(
  columns: DataTableColumn<T>[],
  rows: T[] | undefined,
  enabled: boolean,
): boolean {
  if (!enabled) return false
  if (columns.some((column) => column.key === 'id' || column.key === ID_COLUMN_KEY)) return false
  if (!rows || rows.length === 0) return true
  return rows.some((row) => readRowId(row) !== null)
}

/** Vị trí chèn: sau dãy cột tick chọn đứng đầu bảng. */
export function leadingColumnCount(keys: readonly string[]): number {
  let count = 0
  while (count < keys.length && LEADING_KEYS.has(keys[count])) count++
  return count
}

/** Danh sách cột có thêm cột ID ở bìa trái (sau cột tick chọn nếu có). */
export function withIdColumn<T>(columns: DataTableColumn<T>[], show: boolean): DataTableColumn<T>[] {
  if (!show) return columns
  const idColumn: DataTableColumn<T> = {
    key: ID_COLUMN_KEY,
    header: 'ID',
    width: 72,
    minWidth: 56,
    cell: (row) => readRowId(row) ?? '',
    placeAtStartWhenNew: true,
  }
  const at = leadingColumnCount(columns.map((column) => column.key))
  return [...columns.slice(0, at), idColumn, ...columns.slice(at)]
}
