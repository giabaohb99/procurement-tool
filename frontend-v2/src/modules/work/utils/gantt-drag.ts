import type { Modifier } from '@dnd-kit/core'

import type { WorkTask } from '../types/work'
import { shiftDate } from './gantt-scale'

/**
 * Luật của thao tác KÉO trên biểu đồ Gantt — tách khỏi component để kiểm được.
 *
 * Đây là chỗ dễ làm hỏng dữ liệu nhất của cả phân hệ: một cú kéo trượt tay ghi
 * đè ngày của việc thật, và người dùng không có cách nào biết ngày cũ là gì.
 * Nên mọi quyết định "đổi trường nào" nằm hết ở đây, hàm thuần, có test.
 */

/** Kéo cả thanh (dời lịch) · kéo mép trái (đổi ngày bắt đầu) · kéo mép phải (đổi hạn). */
export type GanttDragKind = 'move' | 'start' | 'end'

/** Trạng thái đang kéo, dùng để vẽ trước kết quả — `days` đã làm tròn theo NGÀY. */
export interface GanttDragState {
  taskId: number
  kind: GanttDragKind
  days: number
}

/** Dữ liệu gắn kèm mỗi phần tử kéo được của dnd-kit. */
export interface GanttDragData {
  task: WorkTask
  kind: GanttDragKind
}

const KINDS: GanttDragKind[] = ['move', 'start', 'end']

/**
 * `active.data.current` của dnd-kit là `Record<string, any>` — thu hẹp lại ở
 * đúng một chỗ này để `any` không rò ra ngoài (luật `typescript.md`).
 */
export function readDragData(raw: unknown): GanttDragData | null {
  if (!raw || typeof raw !== 'object') return null
  const o = raw as { task?: WorkTask; kind?: GanttDragKind }
  if (!o.task || !o.kind || !KINDS.includes(o.kind)) return null
  return { task: o.task, kind: o.kind }
}

/**
 * Số ngày ứng với quãng đường con trỏ đã đi. Làm tròn ngay lúc kéo để thanh
 * nhảy từng nấc đúng bằng ô lưới — thấy trước kết quả, không phải thả ra mới
 * biết rơi vào đâu.
 */
export function daysDragged(deltaX: number, dayWidth: number): number {
  return Math.round(deltaX / dayWidth)
}

/**
 * Bộ chỉnh vị trí cho lớp phủ: khóa trục dọc (Gantt chỉ dời ngang) và bám nấc
 * NGÀY. Không khóa trục dọc thì lớp phủ trôi lên xuống giữa các hàng, trông như
 * sắp thả sang việc khác trong khi thao tác này không hề đổi hàng.
 */
export function snapToDayGrid(dayWidth: number): Modifier {
  return ({ transform }) => ({
    ...transform,
    x: daysDragged(transform.x, dayWidth) * dayWidth,
    y: 0,
  })
}

/** Mỗi mép xê dịch mấy ngày: kéo mép nào thì chỉ mép đó chạy. */
export function edgeShift(kind: GanttDragKind, days: number): { start: number; due: number } {
  return { start: kind === 'end' ? 0 : days, due: kind === 'start' ? 0 : days }
}

/**
 * Cặp ngày sau khi dời — dùng cho chú thích hiện lúc kéo. `null` = việc chưa có
 * ngày nào nên không có gì để dời.
 *
 * Việc chỉ có một trong hai ngày thì lấy chính ngày đó làm cả hai đầu, để thanh
 * một ngày vẫn dời được; còn ghi xuống trường nào là việc của `datesToSave`.
 */
export function shiftedRange(
  task: WorkTask,
  kind: GanttDragKind,
  days: number,
): { start: string; due: string } | null {
  const dau = task.start_date || task.due_date
  const cuoi = task.due_date || task.start_date
  if (!dau || !cuoi) return null

  const shift = edgeShift(kind, days)
  return { start: shiftDate(dau, shift.start), due: shiftDate(cuoi, shift.due) }
}

/**
 * Những trường THỰC SỰ đổi sau cú kéo. `null` = không lưu gì cả.
 *
 * Hai luật giữ dữ liệu sạch:
 * 1. **Không bịa ngày người dùng chưa từng nhập.** Dời cả thanh của việc chỉ có
 *    hạn thì chỉ đổi hạn; muốn đặt ngày bắt đầu thì phải kéo đúng mép trái. Bản
 *    đầu tự điền cả hai đầu, mở panel ra thấy một ngày lạ không biết ở đâu ra.
 * 2. **Không lưu ngày ngược.** Kéo mép quá đà làm ngày bắt đầu vượt hạn thì bỏ
 *    qua cả cú kéo, chứ không lưu rồi để đó cho báo cáo tính ra số âm.
 */
export function datesToSave(
  task: WorkTask,
  kind: GanttDragKind,
  days: number,
): { start_date?: string; due_date?: string } | null {
  if (days === 0) return null

  const range = shiftedRange(task, kind, days)
  if (!range || range.start > range.due) return null

  const values: { start_date?: string; due_date?: string } = {}
  if (kind === 'start' || (kind === 'move' && task.start_date)) values.start_date = range.start
  if (kind === 'end' || (kind === 'move' && task.due_date)) values.due_date = range.due

  return Object.keys(values).length > 0 ? values : null
}
