import { applyClientFilter, type FilterState } from '@/shared/conditional-filter'
import type { WorkTask } from '../types/work'
import { WORK_ASSIGNEE_KIND } from '../types/work'
import { plainText } from './description-html'

/**
 * Áp BỘ LỌC ĐIỀU KIỆN lên bảng công việc, ngay tại trình duyệt.
 *
 * `applyClientFilter` đọc thẳng `item[tên_trường]` và so bằng chuỗi/số/ngày, nên
 * một `WorkTask` thô không dùng được: người phụ trách và nhãn là MẢNG ĐỐI TƯỢNG.
 * Ở đây mỗi việc được dẹp thành một bản ghi phẳng, lọc xong thì trả lại đúng
 * tham chiếu `WorkTask` ban đầu.
 */

/**
 * Khóa của MỘT giá trị trong trường đa trị, có rào hai đầu: `|7|`.
 *
 * Rào `|` là phần bắt buộc chứ không phải cho đẹp. Không có nó thì chuỗi id
 * `1,12` chứa `1` — lọc "người phụ trách là NV 1" sẽ vớ luôn mọi việc của NV 12.
 */
export function multiKey(id: number): string {
  return `|${id}|`
}

/** Ghép nhiều id thành chuỗi tra được bằng phép «chứa»: `|3|7|` */
function multiKeys(ids: number[]): string {
  return ids.length === 0 ? '' : `|${ids.join('|')}|`
}

export interface FilterableTask {
  task: WorkTask
  title: string
  description: string
  status: number
  section_id: number | null
  start_date: string
  due_date: string
  created_at: string
  completed_at: string | null
  creator_employee_id: number
  pic_keys: string
  /**
   * Mỗi TRƯỜNG TÙY BIẾN một khóa `label_{fieldId}` (độ ưu tiên nay là một trong
   * số đó). Trường có bộ giá trị thì ghép id giá trị kiểu `|3|7|`, còn chữ · số ·
   * ngày · người thì lấy thẳng giá trị.
   */
  [labelKey: `label_${number}`]: string | number | null | undefined | WorkTask
}

export function toFilterableTask(task: WorkTask): FilterableTask {
  return {
    task,
    title: task.title,
    //  Mô tả lưu HTML — lọc trên chuỗi thô thì điều kiện «chứa "p"» khớp mọi
    //  việc có mô tả vì trúng tên thẻ.
    description: plainText(task.description),
    status: task.status,
    section_id: task.section_id,
    start_date: task.start_date,
    due_date: task.due_date,
    created_at: task.created_at,
    completed_at: task.completed_at,
    creator_employee_id: task.creator_employee_id,
    pic_keys: multiKeys(
      task.assignees.filter((a) => a.kind === WORK_ASSIGNEE_KIND.PIC).map((a) => a.employee_id),
    ),
    ...labelValues(task),
  }
}

/** Khóa `label_{fieldId}` → giá trị so được, cho MỌI trường tùy biến của việc. */
function labelValues(task: WorkTask): Record<string, string | number | null> {
  const ra: Record<string, string | number | null> = {}
  for (const value of task.labels) {
    const key = `label_${value.field_id}`
    if (value.option_id) {
      //  Kiểu chọn nhiều đẻ NHIỀU dòng cùng `field_id` — gom hết vào một chuỗi
      //  rào `|`, không thì dòng sau đè dòng trước và lọc chỉ thấy giá trị cuối.
      ra[key] = `${(ra[key] as string) || '|'}${value.option_id}|`
      continue
    }
    if (value.value_employee_id) {
      ra[key] = multiKey(value.value_employee_id)
      continue
    }
    ra[key] =
      value.value_text || value.value_date || (value.value_number ?? '') || ''
  }
  return ra
}

/** Không có điều kiện nào thì trả về CHÍNH mảng vào — đừng dựng mảng mới vô ích. */
export function applyTaskConditions(tasks: WorkTask[], state: FilterState): WorkTask[] {
  if (state.rows.length === 0) return tasks
  return applyClientFilter(tasks.map(toFilterableTask), state).map((r) => r.task)
}
