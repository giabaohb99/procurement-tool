import { useCallback, useState } from 'react'

import { logger } from '@/core/telemetry/logger'

function storageKey(listId: number): string {
  return `erp.work.ganttgrid.${listId}`
}

function read(listId: number): boolean {
  try {
    return localStorage.getItem(storageKey(listId)) === '1'
  } catch (error) {
    logger.warn('Trạng thái ẩn/hiện lưới trái Gantt trong localStorage hỏng, mặc định hiện', error)
    return false
  }
}

/**
 * LƯỚI TRÁI của Gantt đang ẩn hay hiện — ẩn thì chỉ còn trục thời gian, chiếm
 * trọn bề ngang.
 *
 * Khác với kéo thanh chia về tối thiểu: `GRID_MIN_WIDTH` vẫn chừa lại một khúc
 * bảng đủ đọc tên việc, còn ở đây là bỏ hẳn — để soi một quý dài hay so nhiều
 * thanh với nhau thì mỗi pixel ngang đều đáng giá.
 *
 * Nhớ theo TỪNG DỰ ÁN, cùng khuôn `useGanttPaneWidth`: đây là cách bày biện của
 * riêng dự án ấy (dự án ít cột thì thích để lưới, dự án dài hai năm thì thích
 * tắt), không phải một thói quen chung của người dùng như cây danh sách bên
 * trái (`useWorkSidebarStore`).
 */
export function useGanttGridHidden(listId: number) {
  const [hidden, setHidden] = useState<boolean>(() => read(listId))

  const toggle = useCallback(() => {
    setHidden((prev) => {
      const next = !prev
      try {
        localStorage.setItem(storageKey(listId), next ? '1' : '0')
      } catch (error) {
        logger.warn('Không ghi được trạng thái ẩn/hiện lưới trái Gantt', error)
      }
      return next
    })
  }, [listId])

  return { hidden, toggle }
}
