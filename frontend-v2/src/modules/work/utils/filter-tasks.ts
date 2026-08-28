import type { WorkTask } from '../types/work'
import { WORK_ASSIGNEE_KIND, WORK_TASK_STATUS } from '../types/work'
import type { WorkScope, WorkSort } from '../types/view-options'

/**
 * Lát cắt nhanh + tìm + sắp xếp cho khung nhìn (§3.2, §3.4 của `05-giao-dien.md`).
 *
 * Hàm THUẦN, chạy trên payload bảng đã tải: bảng một list vài trăm việc thì lọc
 * tại trình duyệt nhanh hơn một vòng gọi máy chủ, và giữ được kanban với danh
 * sách cùng đúng một lát cắt.
 */

/** Giữ lại việc khớp lát cắt. `myEmployeeId = 0` (tài khoản không có nhân sự) → lát cắt cá nhân rỗng. */
export function applyScope(
  tasks: WorkTask[],
  scope: WorkScope,
  myEmployeeId: number,
): WorkTask[] {
  if (scope === 'done') return tasks.filter((t) => t.status === WORK_TASK_STATUS.DONE)
  if (scope === 'cancelled')
    return tasks.filter((t) => t.status === WORK_TASK_STATUS.CANCELLED)
  if (scope === 'created')
    return tasks.filter(
      (t) => t.creator_employee_id === myEmployeeId && t.status === WORK_TASK_STATUS.OPEN,
    )
  if (scope === 'mine')
    return tasks.filter(
      (t) =>
        t.status === WORK_TASK_STATUS.OPEN &&
        t.assignees.some(
          (a) => a.employee_id === myEmployeeId && a.kind === WORK_ASSIGNEE_KIND.PIC,
        ),
    )
  //  Mặc định: việc CHƯA XONG. Việc đã hủy cũng ẩn — nó không còn là việc phải
  //  làm, để lẫn vào là đếm sai "còn bao nhiêu việc".
  return tasks.filter((t) => t.status === WORK_TASK_STATUS.OPEN)
}

/** Tìm theo tiêu đề + mô tả, không phân biệt hoa thường (G-02). */
export function applyKeyword(tasks: WorkTask[], keyword: string): WorkTask[] {
  const tu = keyword.trim().toLowerCase()
  if (!tu) return tasks
  return tasks.filter((t) =>
    `${t.title} ${t.description}`.toLowerCase().includes(tu),
  )
}

/**
 * Sắp xếp. «Tay» giữ nguyên `sort_order` do kéo thả.
 *
 * Hai chỗ dễ sai và cố ý xử lý ở đây:
 * - **Hạn rỗng xuống cuối.** Chuỗi rỗng so từ vựng thì bé hơn mọi ngày, để
 *   nguyên là việc chưa đặt hạn leo lên đầu danh sách "gấp nhất".
 * - **Ưu tiên 0 (chưa đặt) xuống cuối**, vì số 0 nhỏ hơn P1 nhưng nghĩa thì
 *   ngược lại.
 */
export function sortTasks(tasks: WorkTask[], sort: WorkSort): WorkTask[] {
  const ra = [...tasks]
  if (sort === 'manual') return ra.sort((a, b) => a.sort_order - b.sort_order)
  if (sort === 'due')
    return ra.sort((a, b) => (a.due_date || '9999').localeCompare(b.due_date || '9999'))
  if (sort === 'priority')
    return ra.sort((a, b) => (a.priority || 99) - (b.priority || 99))
  if (sort === 'created') return ra.sort((a, b) => b.created_at.localeCompare(a.created_at))
  return ra.sort((a, b) => a.title.localeCompare(b.title, 'vi'))
}

/** Cả ba bước theo đúng thứ tự dùng ở màn hình. */
export function prepareTasks(
  tasks: WorkTask[],
  options: { scope: WorkScope; sort: WorkSort; keyword: string; myEmployeeId: number },
): WorkTask[] {
  const { scope, sort, keyword, myEmployeeId } = options
  return sortTasks(applyKeyword(applyScope(tasks, scope, myEmployeeId), keyword), sort)
}
