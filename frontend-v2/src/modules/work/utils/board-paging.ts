import type { WorkBoard } from '../types/work'
import type { KanbanDropPlace } from './kanban-drop'

/**
 * Tải bảng công việc THEO TRANG — bao-CR-483.
 *
 * Đo trên dev 24/09/2026: mở dự án ERP v2 kéo 545 KB một lượt, trong đó 88% là
 * phần MÔ TẢ của 177 việc mà thẻ không vẽ tới, còn cột «Xong» chứa 160 thẻ. Nay
 * bảng có hai chế độ:
 *   · `light`: mỗi cột tối đa {@link BOARD_PAGE_SIZE} việc, không mô tả; phần dư
 *     tải thêm khi cuộn tới đáy cột;
 *   · `full`: trọn bộ như trước — cho những thao tác cần đủ dữ liệu ở trình
 *     duyệt: Gantt (vẽ hết thanh), tìm từ khóa, sắp xếp khác «Tay», bộ lọc.
 */
export type BoardMode = 'light' | 'full'

/** Trần mỗi cột ở chế độ nhẹ — khớp `BOARD_PAGE_SIZE` phía backend. */
export const BOARD_PAGE_SIZE = 40

export function boardModeFor(input: {
  view: string
  keyword: string
  sort: string
  hasConditions: boolean
}): BoardMode {
  if (input.view === 'gantt') return 'full'
  if (input.keyword.trim()) return 'full'
  if (input.sort !== 'manual') return 'full'
  if (input.hasConditions) return 'full'
  return 'light'
}

/** Số việc còn chưa tải của một cột (`null` cột = «Chưa phân cột» = khóa 0). */
export function remainingOf(board: WorkBoard | undefined, sectionId: number | null): number {
  return board?.remaining?.[sectionId ?? 0]?.count ?? 0
}

/**
 * Bảng «cột → số việc chưa tải» cho các khung nhìn; `undefined` khi bảng đã đủ
 * (chế độ đầy đủ, hoặc không cột nào bị cắt) — lúc đó không dựng đuôi «Tải thêm».
 */
export function remainingCounts(board: WorkBoard | undefined): Record<number, number> | undefined {
  const entries = Object.entries(board?.remaining ?? {})
  if (!entries.length) return undefined
  return Object.fromEntries(entries.map(([sid, r]) => [Number(sid), r.count]))
}

/**
 * Thả thẻ «xuống cuối cột» khi cột ĐANG TẢI DỞ: cuối cột thật nằm sau những thẻ
 * chưa tải, nên thẻ vừa thả sẽ biến khỏi màn hình ngay khi bảng nạp lại. Neo nó
 * NGAY TRƯỚC thẻ chưa tải đầu tiên (`next_task_id`) — vẫn là «cuối phần đang
 * thấy», và lần nạp lại vẫn còn nó trong 40 thẻ đầu.
 */
export function anchorInsideLoaded(place: KanbanDropPlace, board: WorkBoard | undefined): KanbanDropPlace {
  if (place.beforeTaskId !== null) return place
  const next = board?.remaining?.[place.sectionId]?.next_task_id ?? null
  return next ? { ...place, beforeTaskId: next } : place
}
