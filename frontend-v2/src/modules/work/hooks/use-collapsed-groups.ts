import { useCallback, useState } from 'react'

import { logger } from '@/core/telemetry/logger'

function storageKey(listId: number): string {
  return `erp.work.collapsed.${listId}`
}

function read(listId: number): string[] {
  try {
    const raw = localStorage.getItem(storageKey(listId))
    if (!raw) return []
    const saved: unknown = JSON.parse(raw)
    return Array.isArray(saved) ? saved.filter((k): k is string => typeof k === 'string') : []
  } catch (error) {
    logger.warn('Trạng thái thu/mở nhóm Công việc trong localStorage hỏng, mở hết', error)
    return []
  }
}

/**
 * Nhóm nào đang THU trên khung nhìn Danh sách, nhớ theo từng dự án.
 *
 * Nhớ danh sách nhóm ĐANG THU chứ không phải nhóm đang mở: cột mới tạo phải
 * hiện sẵn, mà lưu chiều ngược lại thì nó vắng mặt cho tới khi người dùng bấm
 * vào — nhìn hệt như cột không được tạo.
 *
 * Đi `localStorage` chứ không lên máy chủ, cùng khuôn với `useWorkViewState`:
 * đây là tùy chọn nhìn của riêng người đang ngồi trước máy, không phải dữ liệu
 * dự án. Đổi lại nó theo trình duyệt chứ không theo tài khoản.
 */
export function useCollapsedGroups(listId: number) {
  const [collapsed, setCollapsed] = useState<string[]>(() => read(listId))

  const toggle = useCallback(
    (key: string) => {
      setCollapsed((prev) => {
        const next = prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
        try {
          localStorage.setItem(storageKey(listId), JSON.stringify(next))
        } catch (error) {
          logger.warn('Không ghi được trạng thái thu/mở nhóm Công việc', error)
        }
        return next
      })
    },
    [listId],
  )

  const isCollapsed = useCallback((key: string) => collapsed.includes(key), [collapsed])

  return { isCollapsed, toggle }
}
