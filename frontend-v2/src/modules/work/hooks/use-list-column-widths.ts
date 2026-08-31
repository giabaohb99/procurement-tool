import { useCallback, useMemo, useState } from 'react'

import { logger } from '@/core/telemetry/logger'
import type { TaskListColumn } from '../utils/list-columns'

/** Chặn dưới khi kéo — hẹp hơn nữa thì chip trong ô mất chữ, coi như mất cột. */
export const MIN_COLUMN_WIDTH = 90

/** Chặn dưới của một cột cụ thể; cột tên khai riêng vì nó cần rộng hơn nhiều. */
export function minWidthOf(column: TaskListColumn): number {
  return column.minWidth ?? MIN_COLUMN_WIDTH
}

/**
 * Khung nhìn nào đang giữ bộ bề rộng này.
 *
 * Danh sách và Gantt dùng CHUNG bộ cột (`buildListColumns`) nhưng KHÔNG dùng
 * chung bề rộng: lưới trái của Gantt chỉ được chiếm chừng một phần ba màn hình,
 * còn lại phải chừa cho trục thời gian. Nhớ chung một khóa thì kéo rộng cột tên
 * bên Danh sách xong sang Gantt là mất gần hết biểu đồ.
 */
export type ColumnWidthScope = 'list' | 'gantt'

function storageKey(listId: number, scope: ColumnWidthScope): string {
  return scope === 'list'
    ? //  Giữ nguyên khóa cũ cho khung nhìn Danh sách — đổi tên là mọi người mất
      //  bề rộng đã kéo, mà chẳng đổi lấy gì.
      `erp.work.listcols.${listId}`
    : `erp.work.${scope}cols.${listId}`
}

/**
 * Tên biến CSS giữ bề rộng của một cột.
 *
 * Phải rửa khóa: cột nhãn tùy biến mang khóa `label:12`, mà dấu hai chấm không
 * hợp lệ trong tên custom property — để nguyên thì trình duyệt bỏ qua cả dòng
 * khai báo và cột co về 0 mà không báo lỗi gì.
 */
export function columnWidthVar(key: string): string {
  return `--wcol-${key.replace(/[^a-z0-9]/gi, '-')}`
}

function read(listId: number, scope: ColumnWidthScope): Record<string, number> {
  try {
    const raw = localStorage.getItem(storageKey(listId, scope))
    if (!raw) return {}
    const saved: unknown = JSON.parse(raw)
    if (!saved || typeof saved !== 'object') return {}
    return Object.fromEntries(
      Object.entries(saved as Record<string, unknown>).filter(
        (entry): entry is [string, number] =>
          typeof entry[1] === 'number' && Number.isFinite(entry[1]),
      ),
    )
  } catch (error) {
    logger.warn('Bề rộng cột Công việc trong localStorage hỏng, dùng mặc định', error)
    return {}
  }
}

/**
 * Bề rộng từng cột của khung nhìn Danh sách, nhớ theo từng dự án.
 *
 * Khác `useColumnWidths` dùng chung ở chỗ tập cột KHÔNG cố định: mỗi dự án tự
 * khai trường tùy biến của mình, và khai thêm một trường giữa chừng là có thêm
 * một cột. Nên bản đã lưu được TRỘN với tập cột đang có ở mỗi lần dựng — cột
 * mới lấy bề rộng mặc định, cột đã xóa lặng lẽ rơi ra.
 */
export function useListColumnWidths(
  listId: number,
  columns: TaskListColumn[],
  scope: ColumnWidthScope = 'list',
) {
  const [saved, setSaved] = useState<Record<string, number>>(() => read(listId, scope))

  const widths = useMemo(() => {
    const result: Record<string, number> = {}
    for (const c of columns) {
      const value = saved[c.key]
      result[c.key] = value === undefined ? c.width : Math.max(minWidthOf(c), value)
    }
    return result
  }, [columns, saved])

  const resize = useCallback(
    (key: string, width: number) => {
      setSaved((prev) => {
        const next = { ...prev, [key]: Math.round(width) }
        try {
          localStorage.setItem(storageKey(listId, scope), JSON.stringify(next))
        } catch (error) {
          logger.warn('Không ghi được bề rộng cột Công việc', error)
        }
        return next
      })
    },
    [listId, scope],
  )

  /** Biến CSS đặt trên khung bao — ô của mọi dòng đọc theo, khỏi truyền số xuống. */
  const styleVars = useMemo(() => {
    const vars: Record<string, string> = {}
    for (const c of columns) vars[columnWidthVar(c.key)] = `${widths[c.key]}px`
    return vars as React.CSSProperties
  }, [columns, widths])

  const totalWidth = useMemo(
    () => columns.reduce((sum, c) => sum + widths[c.key], 0),
    [columns, widths],
  )

  return { widths, resize, styleVars, totalWidth }
}
