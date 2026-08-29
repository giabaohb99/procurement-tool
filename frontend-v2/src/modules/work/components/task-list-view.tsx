import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { useMemo, useRef, useState } from 'react'

import { Skeleton } from '@/shared/ui/skeleton'
import { useCollapsedGroups } from '../hooks/use-collapsed-groups'
import { columnWidthVar, useListColumnWidths } from '../hooks/use-list-column-widths'
import type { CardFields } from '../types/view-options'
import type { WorkLabelField, WorkMember, WorkSection, WorkTask } from '../types/work'
import { groupTasksBySection } from '../utils/group-tasks'
import { buildListColumns } from '../utils/list-columns'
import {
  isSamePlace,
  parseDropTarget,
  resolveDropPlace,
  type KanbanDropPlace,
} from '../utils/kanban-drop'
import { HEADER_TITLE_PAD } from '../utils/list-metrics'
import { ListColumnResizer } from './list-column-resizer'
import type { NewTaskDraft } from './task-draft-row'
import { TaskListGroup } from './task-list-group'
import type { TaskRowActions } from './task-list-row'

/** Chỗ tối thiểu cho cột tên: mũi tên bung + ô tick + đủ chữ để đọc ra việc gì. */
const TITLE_MIN_WIDTH = 320
/** `gap-1.5` giữa các ô, tính bằng px — phải khớp với lớp Tailwind của dòng. */
const COLUMN_GAP = 6

interface TaskListViewProps extends TaskRowActions {
  listId: number
  tasks: WorkTask[]
  sections: WorkSection[]
  labelFields: WorkLabelField[]
  members: WorkMember[]
  fields: CardFields
  canEdit: boolean
  isLoading?: boolean
  /** Nhân sự đang đăng nhập — dòng nháp gán sẵn làm người phụ trách. */
  defaultPicId?: number
  /**
   * Cho kéo xếp lại không. Trang truyền `sort === 'manual'`: đang sắp theo hạn
   * chót hay độ ưu tiên mà vẫn cho kéo thì thả xong danh sách tự xếp lại chỗ cũ,
   * nhìn hệt như thao tác bị nuốt (§3.4, đúng luật của kanban).
   */
  dragEnabled: boolean
  onMoveTask: (taskId: number, place: KanbanDropPlace) => void
  onAddTask: (sectionId: number | null, draft: NewTaskDraft) => void
}

/**
 * Khung nhìn DANH SÁCH (D-02) — bảng gom nhóm theo cột, kiểu Lark.
 *
 * **Cố ý KHÔNG dùng `DataTable` dùng chung** dù luật chung của repo bảo phải
 * dùng: bảng ấy không có gom nhóm, mà thêm vào thì đụng ~35 màn đang chạy nhờ
 * nó; và dáng của nó (kẻ dọc, sọc chan hòa, phân trang, ghim cột) ngược hẳn với
 * dáng Lark mà màn này bám theo — một vạch ngang mảnh, ô sửa được tại chỗ. Đi
 * theo tiền lệ `LinesTable`: bảng thứ hai cho một hình dạng khác hẳn, không
 * phải một bảng tự ghép ở tầng trang.
 *
 * Cột hiện gì và theo thứ tự nào lấy từ chính bộ «Tùy chỉnh» của thẻ kanban
 * (`fields`), nên tắt một trường là nó biến mất ở cả hai khung nhìn. Bề rộng thì
 * kéo giãn được và nhớ riêng theo từng dự án.
 */
export function TaskListView({
  listId,
  tasks,
  sections,
  labelFields,
  members,
  fields,
  canEdit,
  isLoading,
  defaultPicId,
  dragEnabled,
  onMoveTask,
  onAddTask,
  ...rowActions
}: TaskListViewProps) {
  const { isCollapsed, toggle } = useCollapsedGroups(listId)
  const gridRef = useRef<HTMLDivElement>(null)
  const [draggingId, setDraggingId] = useState<number | null>(null)

  const groups = useMemo(() => groupTasksBySection(tasks, sections), [tasks, sections])
  const columns = useMemo(() => buildListColumns(fields, labelFields), [fields, labelFields])
  const { resize, styleVars, totalWidth } = useListColumnWidths(listId, columns)

  /*  Bản đồ cột→việc cho `resolveDropPlace` — dùng lại nguyên bộ tính vị trí của
      kanban thay vì viết bản thứ hai. Nhóm "Chưa phân cột" (`sectionId` null) bị
      loại: nó không phải một cột có thật nên không thể là đích thả.  */
  const columnMap = useMemo(() => {
    const map = new Map<number, WorkTask[]>()
    for (const g of groups) if (g.sectionId !== null) map.set(g.sectionId, g.tasks)
    return map
  }, [groups])

  const draggingTask = useMemo(
    () => (draggingId === null ? null : tasks.find((t) => t.id === draggingId) ?? null),
    [draggingId, tasks],
  )

  const sensors = useSensors(
    //  Ngưỡng 6px: dưới mức đó vẫn tính là CÚ BẤM, nếu không thì bấm mở panel
    //  chi tiết mà tay hơi rung là thành một cú kéo hụt.
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  function handleDragStart(event: DragStartEvent) {
    const target = parseDropTarget(event.active.id)
    setDraggingId(target?.type === 'task' ? target.taskId : null)
  }

  function handleDragEnd(event: DragEndEvent) {
    const activeId = draggingId
    setDraggingId(null)
    if (activeId === null) return

    const place = resolveDropPlace(columnMap, activeId, parseDropTarget(event.over?.id))
    const task = tasks.find((t) => t.id === activeId)
    //  Thả về đúng chỗ cũ thì im lặng — đừng bắn một lượt PATCH không đổi gì,
    //  nó chỉ làm bẩn nhật ký thao tác.
    if (!place || !task || isSamePlace(columnMap, task, place)) return
    onMoveTask(activeId, place)
  }


  /*  Bề rộng tối thiểu TÍNH RA chứ không gõ cứng: cột tên là cột `flex-1` duy
      nhất, nên nếu khung hẹp hơn tổng các cột cố định thì nó bị ép về gần 0 và
      mọi tiêu đề việc cụt còn đúng một chữ cái. Số cột lẫn bề rộng đều đổi được
      lúc chạy, nên một hằng số không thể đúng mãi.  */
  const minWidth = TITLE_MIN_WIDTH + totalWidth + columns.length * COLUMN_GAP

  if (isLoading) {
    return (
      <div className="space-y-2 p-2">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-8 w-full" />
        ))}
      </div>
    )
  }

  if (!groups.length) {
    return (
      <p className="p-6 text-center text-sm text-muted-foreground">
        Chưa có cột nào. Thêm một cột ở khung nhìn Bảng để bắt đầu.
      </p>
    )
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setDraggingId(null)}
    >
      <div className="overflow-x-auto">
        <div ref={gridRef} style={{ ...styleVars, minWidth }}>
        <div
          role="row"
          className="group/head flex items-center gap-1.5 border-b bg-muted/30 px-2 py-1.5 text-xs font-medium text-muted-foreground"
        >
          <span className="min-w-0 flex-1" style={{ paddingLeft: HEADER_TITLE_PAD }}>
            Tên công việc
          </span>
          {columns.map((col) => (
            //  KHÔNG đặt `truncate` ở đây: nó kèm `overflow-hidden`, mà tay cầm
            //  kéo giãn nằm ở `-right-1` — tức NGOÀI hộp — nên bị cắt mất, nhìn
            //  như bảng không kéo giãn được. Cắt chữ để cho lớp con bên trong.
            <span
              key={col.key}
              className="relative shrink-0"
              style={{ width: `var(${columnWidthVar(col.key)})` }}
            >
              <span className="block truncate">{col.label}</span>
              <ListColumnResizer
                columnKey={col.key}
                gridRef={gridRef}
                onResize={(width) => resize(col.key, width)}
              />
            </span>
          ))}
        </div>

        {groups.map((group) => (
          <TaskListGroup
            key={group.key}
            group={group}
            columns={columns}
            fields={fields}
            labelFields={labelFields}
            members={members}
            canEdit={canEdit}
            collapsed={isCollapsed(group.key)}
            onToggleCollapse={() => toggle(group.key)}
            defaultPicId={defaultPicId}
            draggable={dragEnabled}
            onAddTask={onAddTask}
            {...rowActions}
          />
        ))}
        </div>
      </div>

      {/*  Lớp phủ bám con trỏ: chỉ mình nó vẽ lại trong lúc kéo, nên cả trăm
           dòng bên dưới đứng yên. Rút gọn còn mỗi tên việc — kéo theo nguyên
           dòng đủ ô nhập thì lớp phủ vừa nặng vừa che mất chỗ sắp thả. */}
      <DragOverlay dropAnimation={null}>
        {draggingTask && (
          <div className="rounded-md border bg-card px-3 py-1.5 text-sm shadow-lg">
            {draggingTask.title}
          </div>
        )}
      </DragOverlay>
    </DndContext>
  )
}
