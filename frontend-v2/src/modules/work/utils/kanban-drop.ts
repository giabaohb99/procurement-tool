import type { WorkTask } from '../types/work'

/**
 * Luật KÉO THẢ của bảng kanban, tách hẳn khỏi component để kiểm được bằng test
 * thuần — chỗ này trước đây có hai công thức song song (một cái vẽ khe chờ lúc
 * `onDragOver`, một cái tính chỗ rơi lúc `onDragEnd`) nên khe chờ hiện một đằng
 * mà thẻ rơi một nẻo.
 */

/** Bước giãn `sort_order`. Phải khớp `SORT_STEP` ở `backend/app/modules/work/task_service.py`. */
export const SORT_STEP = 1000

/**
 * Chỗ thẻ sẽ rơi vào sau một cú kéo thả.
 *
 * Mốc là TƯƠNG ĐỐI (`beforeTaskId`) chứ không phải một `sort_order` tính sẵn ở
 * trình duyệt, vì hai lý do:
 *
 * 1. Bảng có thể đang LỌC (lát cắt / từ khóa), client chỉ thấy một phần của cột.
 *    Tự tính số thứ tự thì mọi thẻ đang bị ẩn văng lên đầu cột.
 * 2. Task tạo mới từng mang `sort_order = 0`, cả cột trùng số nên không còn khe
 *    để chèn vào giữa — kiểu "lấy số ở giữa hai thẻ" luôn hỏng.
 *
 * Máy chủ nhận mốc rồi đánh số lại cả cột thật (`task_service.move_task`).
 */
export interface KanbanDropPlace {
  sectionId: number
  /** Thẻ mà thẻ đang kéo sẽ đứng NGAY TRƯỚC; `null` = xuống cuối cột. */
  beforeTaskId: number | null
}

export type DropTarget =
  | { type: 'section'; sectionId: number }
  | { type: 'task'; taskId: number }
  | { type: 'column'; sectionId: number }

/** Id vùng thả THÂN cột (nơi hứng thẻ) trong dnd-kit. */
export const columnDroppableId = (sectionId: number) => `section-${sectionId}`

/**
 * Id của CẢ CỘT khi kéo đổi thứ tự cột. Khác `columnDroppableId` một cách cố ý:
 * cùng một cột có hai vai trò trong một `DndContext` — vùng hứng thẻ (`section-`)
 * và món đồ kéo được (`column-`) — mà dnd-kit thì cấm hai đăng ký trùng id.
 */
export const columnSortableId = (sectionId: number) => `column-${sectionId}`

/** Id thẻ kéo được trong dnd-kit. Khác họ tiền tố với cột để hai loại không đụng nhau. */
export const taskDraggableId = (taskId: number) => `task-${taskId}`

/**
 * Đọc ngược id dnd-kit. Id lạ trả `null` — thả ra ngoài bảng thì không làm gì.
 *
 * Khớp bằng BIỂU THỨC CHÍNH QUY chứ không `startsWith` + `Number`: `Number` nhận
 * cả `1e3`, ` 12 `, `0x0c`, `Infinity`… nên `task-1e3` sẽ lặng lẽ hóa thành thẻ
 * số 1000 của người khác.
 */
export function parseDropTarget(id: string | number | undefined | null): DropTarget | null {
  const raw = String(id ?? '')
  const section = /^section-([1-9]\d*)$/.exec(raw)
  if (section) return { type: 'section', sectionId: Number(section[1]) }
  const task = /^task-([1-9]\d*)$/.exec(raw)
  if (task) return { type: 'task', taskId: Number(task[1]) }
  const column = /^column-([1-9]\d*)$/.exec(raw)
  if (column) return { type: 'column', sectionId: Number(column[1]) }
  return null
}

/**
 * Cột sẽ đứng NGAY TRƯỚC cột nào sau khi kéo; `null` = đẩy xuống cuối hàng.
 *
 * Cùng phép `arrayMove` của dnd-kit như kéo thẻ trong một cột (kéo sang PHẢI thì
 * nằm SAU ô đích, sang TRÁI thì nằm TRƯỚC) — xem `resolveDropPlace`. Máy chủ
 * nhận mốc rồi đánh số lại cả hàng cột (`list_config_service.move_section`).
 */
export function resolveColumnDrop(
  sectionIds: number[],
  activeSectionId: number,
  overSectionId: number,
): { beforeSectionId: number | null } | null {
  const from = sectionIds.indexOf(activeSectionId)
  const to = sectionIds.indexOf(overSectionId)
  if (from === -1 || to === -1) return null
  const rest = sectionIds.filter((id) => id !== activeSectionId)
  return { beforeSectionId: rest[to] ?? null }
}

/** Cột đang chứa một thẻ; `null` nếu thẻ không có trên bảng. */
function findColumnOf(columns: Map<number, WorkTask[]>, taskId: number): number | null {
  for (const [sectionId, list] of columns) {
    if (list.some((t) => t.id === taskId)) return sectionId
  }
  return null
}

/**
 * Chỗ thẻ sẽ rơi vào, tính từ ô đích dnd-kit báo về. MỘT hàm dùng cho cả lúc vẽ
 * khe chờ lẫn lúc thả thật.
 *
 * **Cùng cột** bám đúng phép `arrayMove` của dnd-kit sortable: kéo XUỐNG thì thẻ
 * nằm SAU ô đích, kéo LÊN thì nằm TRƯỚC. Tính kiểu "luôn chèn trước ô đích" thì
 * mọi cú kéo xuống đều lệch một chỗ so với cái người dùng vừa nhìn thấy.
 *
 * **Sang cột khác** thì chèn TRƯỚC ô đích — đúng chỗ khe chờ đang vẽ. Thả vào
 * khoảng trống của cột (kể cả cột RỖNG) thì xuống cuối.
 *
 * @param columns  thẻ của từng cột, ĐÃ sắp theo thứ tự hiển thị
 */
export function resolveDropPlace(
  columns: Map<number, WorkTask[]>,
  activeTaskId: number,
  target: DropTarget | null,
): KanbanDropPlace | null {
  //  Vỏ cột (`column-`) là món đồ để KÉO ĐỔI THỨ TỰ CỘT, không phải chỗ thả
  //  thẻ. Thả thẻ vào nó thì không có nghĩa gì — thân cột (`section-`) mới là
  //  vùng hứng.
  if (!target || target.type === 'column') return null

  const sourceSection = findColumnOf(columns, activeTaskId)
  if (sourceSection === null) return null

  const targetSection =
    target.type === 'section' ? target.sectionId : findColumnOf(columns, target.taskId)
  if (targetSection === null || !columns.has(targetSection)) return null

  //  Thả vào khoảng trống của cột = xuống cuối cột.
  if (target.type === 'section') return { sectionId: targetSection, beforeTaskId: null }

  const list = columns.get(targetSection) ?? []
  const rest = list.filter((t) => t.id !== activeTaskId)

  //  Rê ngang qua CHÍNH NÓ: đứng yên. Thiếu nhánh này thì mỗi lần con trỏ đi qua
  //  thẻ gốc lại thành một lệnh "xuống cuối cột".
  if (target.taskId === activeTaskId) {
    const at = list.findIndex((t) => t.id === activeTaskId)
    return { sectionId: targetSection, beforeTaskId: rest[at]?.id ?? null }
  }

  if (targetSection !== sourceSection) {
    return { sectionId: targetSection, beforeTaskId: target.taskId }
  }

  //  Cùng cột. `arrayMove(list, from, to)` đặt thẻ vào đúng vị trí `to` của danh
  //  sách ĐÃ BỎ nó ra — nên mốc chính là thẻ đang đứng ở chỗ đó.
  const to = list.findIndex((t) => t.id === target.taskId)
  return { sectionId: targetSection, beforeTaskId: rest[to]?.id ?? null }
}

/** Thả về ĐÚNG chỗ cũ — đừng gọi API cho một cú kéo không đổi gì. */
export function isSamePlace(
  columns: Map<number, WorkTask[]>,
  task: WorkTask,
  place: KanbanDropPlace,
): boolean {
  if (task.section_id !== place.sectionId) return false
  const list = columns.get(place.sectionId) ?? []
  const at = list.findIndex((t) => t.id === task.id)
  if (at === -1) return false
  return (list[at + 1]?.id ?? null) === place.beforeTaskId
}

/**
 * Gom thẻ theo cột, sắp đúng như máy chủ trả về (`ORDER BY sort_order, id`).
 *
 * Sắp thiếu vế `id` là hỏng âm thầm: cột nào còn thẻ trùng `sort_order` (dữ liệu
 * cũ để `0` hết) thì thứ tự lạc quan sau khi thả sẽ khác thứ tự refetch, thẻ tự
 * nhảy chỗ một nhịp sau khi người dùng buông tay.
 */
export function groupBySection(
  sectionIds: number[],
  tasks: WorkTask[],
): Map<number, WorkTask[]> {
  const map = new Map<number, WorkTask[]>(sectionIds.map((id) => [id, []]))
  //  Việc con không thuộc cột nào (`section_id` rỗng) nên không lên bảng.
  for (const t of tasks) if (t.section_id !== null) map.get(t.section_id)?.push(t)
  for (const list of map.values()) list.sort(compareByOrder)
  return map
}

function compareByOrder(a: WorkTask, b: WorkTask): number {
  return a.sort_order - b.sort_order || a.id - b.id
}

/**
 * Bảng SAU cú thả — dùng cho cập nhật lạc quan.
 *
 * Đánh số lại cả cột đích y hệt máy chủ để cái người dùng thấy ngay và cái
 * refetch trả về là một; lệch nhau thì thẻ nhấp nháy nhảy chỗ sau mỗi cú kéo.
 */
export function applyMove(
  tasks: WorkTask[],
  taskId: number,
  place: KanbanDropPlace,
): WorkTask[] {
  const moved = tasks.find((t) => t.id === taskId)
  if (!moved) return tasks

  const column = tasks
    .filter(
      (t) => t.parent_id === null && t.section_id === place.sectionId && t.id !== taskId,
    )
    .sort(compareByOrder)

  const found =
    place.beforeTaskId === null ? -1 : column.findIndex((t) => t.id === place.beforeTaskId)
  const at = found === -1 ? column.length : found
  const reordered = [...column.slice(0, at), moved, ...column.slice(at)]

  const orders = new Map(reordered.map((t, i) => [t.id, (i + 1) * SORT_STEP]))
  return tasks.map((t) => {
    const order = orders.get(t.id)
    if (order === undefined) return t
    return t.id === taskId
      ? { ...t, sort_order: order, section_id: place.sectionId }
      : { ...t, sort_order: order }
  })
}
