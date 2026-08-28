import { useCallback, useState } from 'react'

import { logger } from '@/core/telemetry/logger'
import type { GanttZoom } from '../utils/gantt-scale'
import {
  DEFAULT_CARD_FIELDS,
  type CardFields,
  type WorkScope,
  type WorkSort,
  type WorkView,
} from '../types/view-options'

/**
 * Trạng thái khung nhìn của MỘT danh sách — khung nhìn đang mở, lát cắt, sắp
 * xếp, trường hiện trên thẻ.
 *
 * §1 của `05-giao-dien.md`: nhớ theo (người dùng × list × khung nhìn), lưu
 * `localStorage`, KHÔNG lưu máy chủ ở bản đầu — đúng khuôn `LinesTable` đang
 * nhớ cấu hình cột. Không nhớ thì mỗi lần F5 người dùng phải chọn lại "Việc của
 * tôi" và tắt lại mấy trường không cần.
 *
 * `localStorage` đi theo trình duyệt chứ không theo tài khoản; chấp nhận được
 * vì đây thuần là tùy chọn hiển thị, không có dữ liệu nghiệp vụ nào trong đó.
 */

export interface WorkViewState {
  view: WorkView
  scope: WorkScope
  sort: WorkSort
  fields: CardFields
  /** Mức phóng của khung nhìn Gantt — nhớ riêng, không dính tới hai khung kia. */
  ganttZoom: GanttZoom
}

const MAC_DINH: WorkViewState = {
  view: 'kanban',
  scope: 'open',
  sort: 'manual',
  fields: DEFAULT_CARD_FIELDS,
  ganttZoom: 'day',
}

function khoa(listId: number): string {
  return `erp.work.view.${listId}`
}

function doc(listId: number): WorkViewState {
  try {
    const raw = localStorage.getItem(khoa(listId))
    if (!raw) return MAC_DINH
    const luu = JSON.parse(raw) as Partial<WorkViewState>
    //  Trộn với mặc định chứ không tin bản lưu: thêm một trường mới vào
    //  `CardFields` thì bản lưu cũ thiếu khóa đó, đọc thẳng ra `undefined` và
    //  trường mới im lặng biến mất khỏi thẻ.
    return {
      ...MAC_DINH,
      ...luu,
      fields: { ...MAC_DINH.fields, ...(luu.fields ?? {}) },
    }
  } catch (error) {
    logger.warn('Tùy chọn khung nhìn Công việc trong localStorage hỏng, dùng mặc định', error)
    return MAC_DINH
  }
}

/**
 * Đọc/ghi trạng thái khung nhìn. Trả về `[state, patch]`; `patch` nhận một phần
 * và tự ghi xuống `localStorage`.
 */
export function useWorkViewState(listId: number) {
  const [state, setState] = useState<WorkViewState>(() => doc(listId))

  const patch = useCallback(
    (thayDoi: Partial<WorkViewState>) => {
      setState((truoc) => {
        const moi = { ...truoc, ...thayDoi }
        try {
          localStorage.setItem(khoa(listId), JSON.stringify(moi))
        } catch (error) {
          //  Chế độ riêng tư của Safari chặn ghi — mất phần nhớ thì thôi, không
          //  được để cả màn hình chết vì một tùy chọn hiển thị.
          logger.warn('Không ghi được tùy chọn khung nhìn Công việc', error)
        }
        return moi
      })
    },
    [listId],
  )

  return [state, patch] as const
}
