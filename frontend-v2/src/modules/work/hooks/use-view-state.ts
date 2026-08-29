import { useCallback, useState } from 'react'

import { logger } from '@/core/telemetry/logger'
import type { GanttZoom } from '../utils/gantt-scale'
import {
  DEFAULT_CARD_FIELDS,
  WORK_SORTS,
  type CardFields,
  type CardFieldSetting,
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
  sort: WorkSort
  fields: CardFields
  /** Mức phóng của khung nhìn Gantt — nhớ riêng, không dính tới hai khung kia. */
  ganttZoom: GanttZoom
}

const DEFAULTS: WorkViewState = {
  view: 'kanban',
  sort: 'manual',
  fields: DEFAULT_CARD_FIELDS,
  ganttZoom: 'day',
}

function storageKey(listId: number): string {
  return `erp.work.view.${listId}`
}

/**
 * Đọc phần «trường hiện trên thẻ», CHỊU ĐƯỢC bản lưu theo khuôn cũ.
 *
 * Khuôn cũ là một object bảy công tắc (`{priority: true, labels: false, …}`),
 * khuôn mới là MẢNG có thứ tự. Ai đang mở dở màn hình mà không đổi được thì mở
 * ra thấy thẻ trắng trơn — nên bản cũ được dịch sang bản mới, giữ nguyên thứ tự
 * mặc định và giữ đúng những trường họ đã tắt. Khóa `labels` cũ (một công tắc
 * cho MỌI nhãn tùy biến) không còn tương ứng 1-1 nên bỏ; nhãn sẽ do
 * `mergeCardFields` nối vào, bật sẵn.
 */
function readFields(saved: unknown): CardFields {
  if (Array.isArray(saved)) {
    return saved.filter(
      (f): f is CardFieldSetting =>
        !!f && typeof f === 'object' && typeof (f as CardFieldSetting).key === 'string',
    )
  }
  if (saved && typeof saved === 'object') {
    const old = saved as Record<string, unknown>
    return DEFAULT_CARD_FIELDS.map((f) => ({
      key: f.key,
      visible: old[f.key] === undefined ? true : old[f.key] === true,
    }))
  }
  return DEFAULT_CARD_FIELDS
}

/**
 * Tiêu chí sắp xếp đã lưu có còn tồn tại không.
 *
 * Bản lưu là JSON cũ trong máy người dùng: `"priority"` từng là một tiêu chí
 * cứng, nay độ ưu tiên thành trường tùy biến nên khóa ấy không còn. Để nguyên
 * thì nút «Sắp xếp:» hiện một nhãn RỖNG và bảng xếp theo tiêu đề một cách khó
 * hiểu — rơi về «Tay» là hành vi đúng.
 */
function readSort(saved: unknown): WorkSort {
  if (typeof saved !== 'string') return DEFAULTS.sort
  if (/^label:[1-9]\d*$/.test(saved)) return saved as WorkSort
  return WORK_SORTS.some((s) => s.value === saved) ? (saved as WorkSort) : DEFAULTS.sort
}

function readState(listId: number): WorkViewState {
  try {
    const raw = localStorage.getItem(storageKey(listId))
    if (!raw) return DEFAULTS
    const saved = JSON.parse(raw) as Partial<WorkViewState>
    return {
      ...DEFAULTS,
      ...saved,
      sort: readSort(saved.sort),
      fields: readFields(saved.fields),
    }
  } catch (error) {
    logger.warn('Tùy chọn khung nhìn Công việc trong localStorage hỏng, dùng mặc định', error)
    return DEFAULTS
  }
}

/**
 * Đọc/ghi trạng thái khung nhìn. Trả về `[state, patch]`; `patch` nhận một phần
 * và tự ghi xuống `localStorage`.
 */
export function useWorkViewState(listId: number) {
  const [state, setState] = useState<WorkViewState>(() => readState(listId))

  const patch = useCallback(
    (changes: Partial<WorkViewState>) => {
      setState((prev) => {
        const next = { ...prev, ...changes }
        try {
          localStorage.setItem(storageKey(listId), JSON.stringify(next))
        } catch (error) {
          //  Chế độ riêng tư của Safari chặn ghi — mất phần nhớ thì thôi, không
          //  được để cả màn hình chết vì một tùy chọn hiển thị.
          logger.warn('Không ghi được tùy chọn khung nhìn Công việc', error)
        }
        return next
      })
    },
    [listId],
  )

  return [state, patch] as const
}
