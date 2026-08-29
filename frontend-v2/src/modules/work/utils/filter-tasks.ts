import type { WorkTask } from '../types/work'
import { labelFieldId, type CardFieldKey, type WorkSort } from '../types/view-options'
import { plainText } from './description-html'

/** Bảng tra mà vài tiêu chí sắp xếp cần thêm ngoài chính danh sách việc. */
export interface SortContext {
  /** `option_id` → thứ tự trong bộ giá trị; tiêu chí "sắp theo trường tùy biến" cần. */
  optionRank?: Map<number, number>
}

/**
 * Tìm theo từ khóa + sắp xếp cho khung nhìn (§3.4 của `05-giao-dien.md`).
 *
 * Hàm THUẦN, chạy trên payload bảng đã tải: bảng một list vài trăm việc thì lọc
 * tại trình duyệt nhanh hơn một vòng gọi máy chủ, và giữ được kanban với danh
 * sách cùng đúng một thứ tự.
 *
 * Lọc theo điều kiện (trạng thái · người phụ trách · người tạo · ngày…) nằm ở
 * `task-conditions.ts` — nút «Bộ lọc». Ở đây KHÔNG còn lát cắt cố định nào.
 */

/** Tìm theo tiêu đề + mô tả, không phân biệt hoa thường (G-02). */
export function applyKeyword(tasks: WorkTask[], keyword: string): WorkTask[] {
  const tu = keyword.trim().toLowerCase()
  if (!tu) return tasks
  return tasks.filter((t) =>
    //  Mô tả lưu HTML — tìm trên chuỗi thô thì gõ "p" hay "li" là khớp mọi việc
    //  có mô tả, vì khớp trúng tên thẻ.
    `${t.title} ${plainText(t.description)}`.toLowerCase().includes(tu),
  )
}

/**
 * Sắp xếp. «Tay» giữ nguyên `sort_order` do kéo thả.
 *
 * Ba chỗ dễ sai và cố ý xử lý ở đây:
 * - **Ngày rỗng xuống cuối.** Chuỗi rỗng so từ vựng thì bé hơn mọi ngày, để
 *   nguyên là việc chưa đặt hạn leo lên đầu danh sách "gấp nhất".
 * - **Việc chưa chọn giá trị của trường tùy biến xuống cuối** (độ ưu tiên nay là
 *   một trường như thế) — xem `byLabel`.
 * - **Ngày MỚI lên trước** với ba mốc "đã xảy ra" (tạo · sửa · hoàn thành), khác
 *   hẳn hai mốc "sắp tới" (bắt đầu · hạn chót) xếp từ gần đến xa.
 */
export function sortTasks(
  tasks: WorkTask[],
  sort: WorkSort,
  context: SortContext = {},
): WorkTask[] {
  const { optionRank } = context
  const ra = [...tasks]
  const fieldId = labelFieldId(sort as CardFieldKey)
  if (fieldId !== null) return ra.sort(byLabel(fieldId, optionRank))
  if (sort === 'manual') return ra.sort((a, b) => a.sort_order - b.sort_order)
  if (sort === 'start') return ra.sort(byDateAsc((t) => t.start_date))
  if (sort === 'due') return ra.sort(byDateAsc((t) => t.due_date))
  if (sort === 'created') return ra.sort(byDateDesc((t) => t.created_at))
  if (sort === 'updated') return ra.sort(byDateDesc((t) => t.updated_at))
  if (sort === 'completed') return ra.sort(byDateDesc((t) => t.completed_at))
  return ra.sort((a, b) => a.title.localeCompare(b.title, 'vi'))
}

/**
 * Sắp theo MỘT TRƯỜNG TÙY BIẾN (độ ưu tiên là một trong số đó).
 *
 * Hạng lấy từ THỨ TỰ giá trị trong bộ giá trị của trường, không phải `option_id`
 * (id sinh theo lúc tạo) cũng không phải tên (P10 sẽ đứng trước P2). Việc chưa
 * chọn giá trị xuống cuối, y như việc chưa đặt hạn.
 */
function byLabel(fieldId: number, optionRank?: Map<number, number>) {
  const rank = (task: WorkTask) => {
    const value = task.labels.find((l) => l.field_id === fieldId)
    if (!value?.option_id) return Number.MAX_SAFE_INTEGER
    return optionRank?.get(value.option_id) ?? value.option_id
  }
  return (a: WorkTask, b: WorkTask) => rank(a) - rank(b)
}

/** Mốc SẮP TỚI: gần nhất lên đầu, chưa đặt xuống cuối. */
function byDateAsc(pick: (t: WorkTask) => string | null) {
  return (a: WorkTask, b: WorkTask) =>
    (pick(a) || '9999').localeCompare(pick(b) || '9999')
}

/** Mốc ĐÃ XẢY RA: mới nhất lên đầu, chưa có xuống cuối. */
function byDateDesc(pick: (t: WorkTask) => string | null) {
  return (a: WorkTask, b: WorkTask) => {
    const x = pick(a) ?? ''
    const y = pick(b) ?? ''
    //  Không đảo hai vế trước rồi mới so: chuỗi rỗng đảo lên thành LỚN NHẤT,
    //  việc chưa hoàn thành sẽ chen lên trên mọi việc đã hoàn thành.
    if (!x && !y) return 0
    if (!x) return 1
    if (!y) return -1
    return y.localeCompare(x)
  }
}

/** Cả hai bước theo đúng thứ tự dùng ở màn hình: lọc chữ trước, sắp xếp sau. */
export function prepareTasks(
  tasks: WorkTask[],
  options: { sort: WorkSort; keyword: string } & SortContext,
): WorkTask[] {
  const { sort, keyword, optionRank } = options
  return sortTasks(applyKeyword(tasks, keyword), sort, { optionRank })
}
