import type { WorkTask } from '../types/work'
import type { TaskGroup } from './group-tasks'

/**
 * Dựng danh sách HÀNG của biểu đồ Gantt: mỗi nhóm (cột kanban) một dòng tiêu đề,
 * bên dưới là các việc của nhóm đó — cùng cách gom với khung nhìn Danh sách, nên
 * thu/mở nhóm ở bên nào cũng nhớ chung một chỗ (`useCollapsedGroups`).
 *
 * Kết quả là một mảng PHẲNG có thứ tự: chỉ số của một hàng chính là số thứ tự
 * dòng trên màn hình, nên lưới trái, trục thời gian và lớp mũi tên phụ thuộc chỉ
 * cần nhân chỉ số với `ROW_HEIGHT` là ra đúng một tọa độ — không component nào
 * phải tự đếm lại, và không có cách nào để chúng đếm lệch nhau.
 */

export interface GanttGroupRow {
  kind: 'group'
  key: string
  group: TaskGroup
  /** Quãng ngày gom từ mọi việc trong nhóm; `null` = cả nhóm chưa việc nào có ngày. */
  range: { start: string; due: string } | null
  /** Tiến độ 0…1 = số việc đã xong / tổng số việc có trong nhóm. */
  progress: number
  collapsed: boolean
}

export interface GanttTaskRow {
  kind: 'task'
  key: string
  task: WorkTask
}

export type GanttRowItem = GanttGroupRow | GanttTaskRow

export function buildGanttRows(
  groups: TaskGroup[],
  isCollapsed: (key: string) => boolean,
  isDone: (task: WorkTask) => boolean,
): GanttRowItem[] {
  const rows: GanttRowItem[] = []
  for (const group of groups) {
    const collapsed = isCollapsed(group.key)
    rows.push({
      kind: 'group',
      key: `g:${group.key}`,
      group,
      range: rollUpRange(group.tasks),
      progress: group.tasks.length
        ? group.tasks.filter(isDone).length / group.tasks.length
        : 0,
      collapsed,
    })
    if (collapsed) continue
    for (const task of group.tasks) rows.push({ kind: 'task', key: `t:${task.id}`, task })
  }
  return rows
}

/**
 * Quãng ngày của cả một nhóm: sớm nhất → muộn nhất trong số việc CÓ NGÀY.
 *
 * Việc chưa đặt ngày bị bỏ qua chứ không kéo quãng về hôm nay — nhóm mười việc
 * mà chín việc chưa có ngày thì thanh nhóm phải nói đúng về một việc kia, chứ
 * không phải bịa ra một quãng dài suốt để "trông có vẻ đầy đủ".
 */
export function rollUpRange(tasks: WorkTask[]): { start: string; due: string } | null {
  let start = ''
  let due = ''
  for (const t of tasks) {
    //  Việc chỉ có MỘT trong hai ngày vẫn tính, lấy chính ngày đó cho cả hai đầu
    //  — giống hệt cách `barGeometry` vẽ thanh một ngày cho nó.
    const dau = t.start_date || t.due_date
    const cuoi = t.due_date || t.start_date
    if (!dau || !cuoi) continue
    const tu = dau <= cuoi ? dau : cuoi
    const den = dau <= cuoi ? cuoi : dau
    if (!start || tu < start) start = tu
    if (!due || den > due) due = den
  }
  return start && due ? { start, due } : null
}

/** Số thứ tự dòng của từng việc — lớp mũi tên tra chỗ đặt hai đầu bằng bản đồ này. */
export function indexTaskRows(rows: GanttRowItem[]): Map<number, number> {
  const map = new Map<number, number>()
  rows.forEach((row, i) => {
    if (row.kind === 'task') map.set(row.task.id, i)
  })
  return map
}
