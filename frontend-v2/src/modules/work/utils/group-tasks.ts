import type { WorkSection, WorkTask } from '../types/work'

/** Một nhóm trên khung nhìn Danh sách — tương ứng MỘT cột kanban. */
export interface TaskGroup {
  /** `section:{id}` hoặc `none`. Dùng làm React key và khóa nhớ trạng thái thu/mở. */
  key: string
  name: string
  color: string
  /** `null` với nhóm "Chưa phân cột" — thêm việc ở đây thì không gán cột nào. */
  sectionId: number | null
  tasks: WorkTask[]
}

export const UNGROUPED_KEY = 'none'

/**
 * Gom task theo CỘT (section) cho khung nhìn Danh sách (D-02, §2 của `05-giao-dien.md`).
 *
 * Ba luật, mỗi cái vá một chỗ hỏng âm thầm:
 *
 * 1. **Cột rỗng VẪN hiện.** Bỏ đi thì cột vừa tạo không có chỗ nào bấm được để
 *    thêm việc đầu tiên — dòng «Việc mới» nằm trong nhóm chứ không ở đâu khác.
 * 2. **Thứ tự task giữ NGUYÊN** như mảng đưa vào. Mảng đó đã qua lọc + sắp xếp
 *    (`prepareTasks`); xếp lại ở đây là nuốt mất tiêu chí người dùng đang chọn.
 * 3. **Task trỏ vào cột đã bị xóa** rơi về nhóm "Chưa phân cột" thay vì biến mất.
 *    `section_id` là cột thường, không phải khóa ngoại có `ON DELETE SET NULL`,
 *    nên số cũ còn nằm lại sau khi xóa cột — lọc theo section đang có thì task
 *    lặng lẽ không hiện ở đâu cả và người dùng tưởng mất dữ liệu.
 */
export function groupTasksBySection(tasks: WorkTask[], sections: WorkSection[]): TaskGroup[] {
  const groups = new Map<number, TaskGroup>()
  for (const s of sections) {
    groups.set(s.id, {
      key: `section:${s.id}`,
      name: s.name,
      color: s.color,
      sectionId: s.id,
      tasks: [],
    })
  }

  const ungrouped: WorkTask[] = []
  for (const t of tasks) {
    const group = t.section_id === null ? undefined : groups.get(t.section_id)
    if (group) group.tasks.push(t)
    else ungrouped.push(t)
  }

  const result = [...groups.values()]
  if (ungrouped.length) {
    result.push({
      key: UNGROUPED_KEY,
      name: 'Chưa phân cột',
      color: 'gray',
      sectionId: null,
      tasks: ungrouped,
    })
  }
  return result
}
