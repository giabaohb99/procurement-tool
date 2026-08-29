import { useCallback, useMemo, useState } from 'react'

import { logger } from '@/core/telemetry/logger'
import type { TaskListColumn } from '../utils/list-columns'

/** Chặn dưới khi kéo — hẹp hơn nữa thì chip trong ô mất chữ, coi như mất cột. */
export const MIN_COLUMN_WIDTH = 90

function storageKey(listId: number): string {
  return `erp.work.listcols.${listId}`
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

function read(listId: number): Record<string, number> {
  try {
    const raw = localStorage.getItem(storageKey(listId))
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
export function useListColumnWidths(listId: number, columns: TaskListColumn[]) {
  const [saved, setSaved] = useState<Record<string, number>>(() => read(listId))

  const widths = useMemo(() => {
    const result: Record<string, number> = {}
    for (const c of columns) {
      const value = saved[c.key]
      result[c.key] = value === undefined ? c.width : Math.max(MIN_COLUMN_WIDTH, value)
    }
    return result
  }, [columns, saved])

  const resize = useCallback(
    (key: string, width: number) => {
      setSaved((prev) => {
        const next = { ...prev, [key]: Math.round(Math.max(MIN_COLUMN_WIDTH, width)) }
        try {
          localStorage.setItem(storageKey(listId), JSON.stringify(next))
        } catch (error) {
          logger.warn('Không ghi được bề rộng cột Công việc', error)
        }
        return next
      })
    },
    [listId],
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
