/**
 * Tùy chọn HIỂN THỊ của khung nhìn (D-07): lát cắt nhanh · sắp xếp · trường
 * hiện trên thẻ.
 *
 * Để riêng tệp này chứ không nằm cạnh component thanh công cụ: một tệp vừa xuất
 * component vừa xuất hằng số thì hot-reload của Vite mất tác dụng cho cả tệp
 * (`react-refresh/only-export-components`).
 */

/**
 * Khung nhìn của Lark: List · Kanban · Gantt · Activities (§2 của
 * `05-giao-dien.md`). Tab nào chưa làm thì KHÔNG khai ở đây — §2 cấm để tab
 * chết trên thanh; **Dashboard** (D-06) vì thế vẫn vắng mặt.
 *
 * «Hoạt động» đứng CUỐI, đúng thứ tự Lark: ba tab đầu là ba cách nhìn cùng một
 * mớ việc, còn nó là nhật ký — xếp xen vào giữa là gãy mạch.
 */
export const WORK_VIEWS = [
  { value: 'kanban', label: 'Bảng' },
  { value: 'list', label: 'Danh sách' },
  { value: 'gantt', label: 'Gantt' },
  { value: 'activities', label: 'Hoạt động' },
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
 *
 * `status` và `start` thêm vào cùng cụm Gantt mở rộng (B-14/B-15): lưới trái của
 * Gantt lấy cột từ CHÍNH bộ này, mà hai thứ người ta đọc nhiều nhất trên một
 * biểu đồ tiến độ là trạng thái và ngày bắt đầu. Thêm ở đây nên chúng cũng thành
 * cột của khung nhìn Danh sách — đúng ý "một nguồn cột cho cả ba khung nhìn".
 */
export const BUILTIN_CARD_FIELDS = [
  { key: 'assignees', label: 'Phụ trách' },
  { key: 'status', label: 'Trạng thái' },
  { key: 'start', label: 'Ngày bắt đầu' },
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
  const result = saved.filter((f) => {
    if (!wanted.has(f.key) || seen.has(f.key)) return false
    seen.add(f.key)
    return true
  })

  /*  Trường DỰNG SẴN mới thêm về sau chen vào NGAY TRƯỚC nhãn tùy biến đầu
      tiên, chứ không nối vào cuối như nhãn.

      Nối vào cuối thì với mọi người dùng cũ (ai cũng có sẵn một bản lưu trong
      `localStorage`), «Trạng thái» và «Ngày bắt đầu» rơi xuống sau tất cả nhãn
      tùy biến của dự án: ở khung nhìn Gantt, nơi lưới trái chỉ hiện được vài cột
      đầu, chúng bị cắt mất và người dùng kết luận là chưa làm.

      Chen theo MỐC "nhãn đầu tiên" chứ không theo vị trí trong
      `BUILTIN_CARD_FIELDS`: thứ tự đã nhớ là thứ tự người dùng tự kéo, bám theo
      bảng khai của ta là xáo lại đúng cái họ vừa xếp.  */
  const moc = result.findIndex((f) => labelFieldId(f.key) !== null)
  let chen = moc === -1 ? result.length : moc
  for (const f of BUILTIN_CARD_FIELDS) {
    const key = f.key as CardFieldKey
    if (seen.has(key)) continue
    seen.add(key)
    result.splice(chen, 0, { key, visible: true })
    chen += 1
  }

  for (const key of wanted) {
    if (!seen.has(key)) result.push({ key, visible: true })
  }
  return result
}
