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

/*
 * ⚠️ ĐÃ BỎ nút «lát cắt nhanh» (Tất cả việc / Việc của tôi / Tôi tạo / Đã hoàn
 * thành / Đã hủy). Mọi lát cắt đó nay khai bằng BỘ LỌC ĐIỀU KIỆN — trạng thái,
 * người phụ trách, người tạo đều là trường lọc (`config/task-filter-fields.ts`).
 *
 * Không giữ lại "âm thầm ẩn việc đã xong": lát cắt cố định AND với bộ lọc thì
 * lọc «trạng thái = Hoàn thành» ra bảng trống, không ai hiểu vì sao.
 */

/**
 * Sắp xếp trong từng cột (§3.4) — đúng bộ tiêu chí của Lark, thêm «Tiêu đề».
 * «Tay» = theo `sort_order` do kéo thả.
 *
 * Mọi tiêu chí ở đây đọc được từ payload bảng đã tải, không cần gọi thêm máy chủ.
 * Sắp theo Tag thì nay đi đường `label:{fieldId}` như mọi trường tùy biến khác.
 */
export const WORK_SORTS = [
  { value: 'manual', label: 'Tay (kéo thả)' },
  { value: 'start', label: 'Ngày bắt đầu' },
  { value: 'due', label: 'Hạn chót' },
  { value: 'created', label: 'Ngày tạo' },
  { value: 'updated', label: 'Sửa gần nhất' },
  { value: 'completed', label: 'Ngày hoàn thành' },
  { value: 'title', label: 'Tiêu đề' },
] as const

/**
 * Ngoài bộ trên, sắp được theo **một trường tùy biến** — khóa `label:{fieldId}`,
 * cùng khuôn với `CardFieldKey`. Độ ưu tiên nay chính là một trường như thế, nên
 * "sắp theo độ ưu tiên" không còn là một giá trị cố định ở đây được.
 */
export type WorkSort = (typeof WORK_SORTS)[number]['value'] | `label:${number}`

/**
 * Trường vẽ trên thẻ kanban — bật/tắt và ĐỔI THỨ TỰ ở nút «Tùy chỉnh» (§3.6),
 * đúng khuôn *Customize* của Lark.
 *
 * Trường **nhãn tùy biến** (B-08) mang khóa `label:{fieldId}`: mỗi dự án tự khai
 * bộ nhãn riêng nên danh sách này KHÔNG cố định được, phải trộn với bộ nhãn
 * đang có của dự án lúc chạy (`mergeCardFields`).
 */
export const BUILTIN_CARD_FIELDS = [
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
