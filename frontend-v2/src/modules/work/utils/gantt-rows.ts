import type { WorkTask } from '../types/work'
import type { TaskGroup } from './group-tasks'

/**
 * Dựng danh sách HÀNG của biểu đồ Gantt.
 *
 * ⚠️ Đây là **bản sao đúng từng dòng** của thứ mà `TaskGroupsBoard` vẽ ra ở lưới
 * trái: mỗi nhóm một dòng tiêu đề, rồi các việc, việc con của việc đang bung, và
 * dòng «Việc mới» cuối nhóm. Lệch một dòng là mọi thanh bên dưới trượt khỏi tên
 * việc của nó — mà lệch đều nên nhìn vẫn "có vẻ đúng", chỉ khi đối chiếu tên với
 * thanh mới lòi ra.
 *
 * Kết quả là một mảng PHẲNG có thứ tự: chỉ số của một hàng chính là số thứ tự
 * dòng trên màn hình, nên trục thời gian và lớp mũi tên chỉ cần nhân chỉ số với
 * `ROW_HEIGHT` là ra đúng tọa độ.
 *
 * Sửa cấu trúc dòng ở `task-list-group.tsx` thì PHẢI sửa kèm ở đây.
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
  /** Việc con thì thanh vẽ mảnh hơn và thụt vào, cho khỏi lẫn với việc cha. */
  isSubtask: boolean
}

/** Dòng «Việc mới» cuối mỗi nhóm — bên trục thời gian là một hàng trống. */
export interface GanttDraftRow {
  kind: 'draft'
  key: string
}

export type GanttRowItem = GanttGroupRow | GanttTaskRow | GanttDraftRow

export interface BuildGanttRowsOptions {
  isCollapsed: (groupKey: string) => boolean
  isDone: (task: WorkTask) => boolean
  /** Việc đang bung việc con; `null` = không bung việc nào. */
  expandedTaskId: number | null
  /** Việc con của việc đang bung — nạp lười, có thể rỗng lúc còn đang tải. */
  subtasks: WorkTask[]
  /** Có dòng «Việc mới» cuối mỗi nhóm không (chỉ khi đủ quyền sửa). */
  showDraftRow: boolean
  /**
   * Cột đang bị KÉO — thu lại y như nhóm đang đóng.
   *
   * Lưới trái giấu thân nhóm trong lúc kéo cột (để cái trôi theo con trỏ chỉ là
   * một dải tiêu đề, không phải cả mảng xám nửa màn hình). Không thu theo ở đây
   * thì suốt cú kéo, bên phải thừa ra đúng bấy nhiêu hàng và mọi thanh bên dưới
   * trượt khỏi tên việc của nó.
   */
  draggingSectionId?: number | null
}

export function buildGanttRows(
  groups: TaskGroup[],
  options: BuildGanttRowsOptions,
): GanttRowItem[] {
  const { isCollapsed, isDone, expandedTaskId, subtasks, showDraftRow } = options
  const rows: GanttRowItem[] = []

  for (const group of groups) {
    const collapsed =
      isCollapsed(group.key) ||
      (group.sectionId !== null && group.sectionId === options.draggingSectionId)
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

    for (const task of group.tasks) {
      rows.push({ kind: 'task', key: `t:${task.id}`, task, isSubtask: false })
      if (task.id !== expandedTaskId) continue
      for (const sub of subtasks) {
        rows.push({ kind: 'task', key: `s:${sub.id}`, task: sub, isSubtask: true })
      }
    }

    if (showDraftRow) rows.push({ kind: 'draft', key: `d:${group.key}` })
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
