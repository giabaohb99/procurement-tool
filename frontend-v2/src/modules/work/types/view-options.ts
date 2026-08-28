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

/**
 * Trường vẽ trên thẻ kanban — bật/tắt và ĐỔI THỨ TỰ ở nút «Tùy chỉnh» (§3.6),
 * đúng khuôn *Customize* của Lark.
 *
 * Trường **nhãn tùy biến** (B-08) mang khóa `label:{fieldId}`: mỗi dự án tự khai
 * bộ nhãn riêng nên danh sách này KHÔNG cố định được, phải trộn với bộ nhãn
 * đang có của dự án lúc chạy (`mergeCardFields`).
 */
export const BUILTIN_CARD_FIELDS = [
  { key: 'priority', label: 'Độ ưu tiên' },
  { key: 'tags', label: 'Tag' },
  { key: 'assignees', label: 'Phụ trách' },
  { key: 'due', label: 'Hạn chót' },
  { key: 'subtasks', label: 'Việc con' },
  { key: 'comments', label: 'Số bình luận' },
] as const

export type BuiltinCardFieldKey = (typeof BUILTIN_CARD_FIELDS)[number]['key']
export type CardFieldKey = BuiltinCardFieldKey | `label:${number}`

/** Một dòng trong menu «Tùy chỉnh». THỨ TỰ trong mảng = thứ tự vẽ trên thẻ. */
export interface CardFieldSetting {
  key: CardFieldKey
  visible: boolean
}

export type CardFields = CardFieldSetting[]

export const DEFAULT_CARD_FIELDS: CardFields = BUILTIN_CARD_FIELDS.map((f) => ({
  key: f.key,
  visible: true,
}))

/** `label:12` → `12`; trường dựng sẵn → `null`. */
export function labelFieldId(key: CardFieldKey): number | null {
  const m = /^label:([1-9]\d*)$/.exec(key)
  return m ? Number(m[1]) : null
}

/**
 * Trộn thứ tự đã nhớ với bộ nhãn tùy biến ĐANG CÓ của dự án.
 *
 * Ba việc, thiếu cái nào cũng hỏng âm thầm:
 * - Nhãn vừa được thêm ở Thiết lập phải xuất hiện (nối vào CUỐI, bật sẵn) —
 *   không thì khai trường mới xong chẳng thấy đâu.
 * - Nhãn đã xóa phải biến mất, không để lại một dòng trống trong menu.
 * - Trường dựng sẵn mới thêm về sau cũng phải tự chen vào.
 */
export function mergeCardFields(saved: CardFields, labelIds: number[]): CardFields {
  const wanted = new Set<CardFieldKey>([
    ...BUILTIN_CARD_FIELDS.map((f) => f.key),
    ...labelIds.map((id): CardFieldKey => `label:${id}`),
  ])
  //  Bỏ khóa TRÙNG ngay tại đây: bản lưu là JSON người dùng sửa được, mà hai
  //  dòng cùng khóa là hai React `key` trùng — cảnh báo đỏ và dòng nhảy lung
  //  tung mỗi lần kéo đổi thứ tự.
  const seen = new Set<CardFieldKey>()
  const kept = saved.filter((f) => {
    if (!wanted.has(f.key) || seen.has(f.key)) return false
    seen.add(f.key)
    return true
  })
  const added = [...wanted].filter((k) => !seen.has(k)).map((key) => ({ key, visible: true }))
  return [...kept, ...added]
}
