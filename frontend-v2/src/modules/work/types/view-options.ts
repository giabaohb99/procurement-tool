/**
 * Tùy chọn HIỂN THỊ của khung nhìn (D-07): lát cắt nhanh · sắp xếp · trường
 * hiện trên thẻ.
 *
 * Để riêng tệp này chứ không nằm cạnh component thanh công cụ: một tệp vừa xuất
 * component vừa xuất hằng số thì hot-reload của Vite mất tác dụng cho cả tệp
 * (`react-refresh/only-export-components`).
 */

/**
 * Ba khung nhìn của Lark: List · Kanban · Gantt (§2 của `05-giao-dien.md`).
 * Tab nào chưa làm thì KHÔNG khai ở đây — §2 cấm để tab chết trên thanh.
 */
export const WORK_VIEWS = [
  { value: 'kanban', label: 'Bảng' },
  { value: 'list', label: 'Danh sách' },
  { value: 'gantt', label: 'Gantt' },
] as const

export type WorkView = (typeof WORK_VIEWS)[number]['value']

/** Nút «Tất cả» của Lark (§3.2) — đổi nhanh lát cắt, không đụng bộ lọc điều kiện. */
export const WORK_SCOPES = [
  { value: 'open', label: 'Tất cả việc (chưa xong)' },
  { value: 'mine', label: 'Việc của tôi' },
  { value: 'created', label: 'Tôi tạo' },
  { value: 'done', label: 'Đã hoàn thành' },
  { value: 'cancelled', label: 'Đã hủy' },
] as const

export type WorkScope = (typeof WORK_SCOPES)[number]['value']

/** Sắp xếp trong từng cột (§3.4). «Tay» = theo `sort_order` do kéo thả. */
export const WORK_SORTS = [
  { value: 'manual', label: 'Tay (kéo thả)' },
  { value: 'due', label: 'Hạn chót' },
  { value: 'priority', label: 'Độ ưu tiên' },
  { value: 'created', label: 'Ngày tạo' },
  { value: 'title', label: 'Tiêu đề' },
] as const

export type WorkSort = (typeof WORK_SORTS)[number]['value']

/** Trường nào được vẽ trên thẻ kanban — bật/tắt ở nút «Tùy chỉnh» (§3.6). */
export interface CardFields {
  priority: boolean
  tags: boolean
  labels: boolean
  assignees: boolean
  due: boolean
  subtasks: boolean
  comments: boolean
}

export const DEFAULT_CARD_FIELDS: CardFields = {
  priority: true,
  tags: true,
  labels: true,
  assignees: true,
  due: true,
  subtasks: true,
  comments: true,
}

export const CARD_FIELD_LABELS: { key: keyof CardFields; label: string }[] = [
  { key: 'priority', label: 'Độ ưu tiên' },
  { key: 'tags', label: 'Tag' },
  { key: 'labels', label: 'Nhãn tùy biến' },
  { key: 'assignees', label: 'Người phụ trách' },
  { key: 'due', label: 'Hạn chót' },
  { key: 'subtasks', label: 'Tiến độ việc con' },
  { key: 'comments', label: 'Số bình luận' },
]
