import { useDroppable } from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { ChevronRight, GripVertical, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'

import { cn } from '@/shared/utils/cn'
import { useWorkTask } from '../hooks/use-work-board'
import type { CardFields } from '../types/view-options'
import type { WorkLabelField, WorkMember, WorkTask } from '../types/work'
import type { TaskGroup } from '../utils/group-tasks'
import { columnDroppableId, columnSortableId, taskDraggableId } from '../utils/kanban-drop'
import type { TaskListColumn } from '../utils/list-columns'
import { ROW_PAD_LEFT } from '../utils/list-metrics'
import { noDisplacement } from '../utils/list-sorting-strategy'
import { dotClass } from '../utils/work-colors'
import { TaskDraftRow, type NewTaskDraft } from './task-draft-row'
import { TaskListRow, type TaskRowActions } from './task-list-row'

interface TaskListGroupProps extends TaskRowActions {
  group: TaskGroup
  columns: TaskListColumn[]
  fields: CardFields
  labelFields: WorkLabelField[]
  members: WorkMember[]
  canEdit: boolean
  collapsed: boolean
  onToggleCollapse: () => void
  /** Nhân sự đang đăng nhập — dòng nháp gán sẵn làm người phụ trách. */
  defaultPicId?: number
  /** Cho kéo xếp lại VIỆC — tắt khi đang sắp theo tiêu chí khác «Tay» (§3.4). */
  draggable: boolean
  /**
   * Cho kéo xếp lại CHÍNH NHÓM này.
   *
   * Cổng riêng, không đi chung với `draggable`: nhóm ở đây là một CỘT, tức cấu
   * hình của dự án — chỉ quản trị mới đổi được (giống hệt kanban) — và thứ tự
   * cột không dính dáng gì tới việc đang sắp việc theo tiêu chí nào.
   */
  sectionDraggable: boolean
  /**
   * Có món nào ĐANG được kéo trong bảng không — bất kể món gì.
   *
   * Dùng để TẮT hiệu ứng rê chuột của từng dòng: lớp phủ đang bám con trỏ nên
   * dòng nằm dưới nó cứ sáng lên theo, thành ra chạy suốt một vệt xám dọc bảng
   * trong lúc kéo, lấn át đúng cái khe chờ mà người dùng cần nhìn.
   */
  dragActive: boolean
  /** Con trỏ đang ở chỗ không thả được — dòng đang kéo viền đỏ. */
  dragBlocked: boolean
  /** Có tô sáng cột này khi con trỏ đi qua không — chỉ đúng khi đang kéo VIỆC. */
  showDropTarget: boolean
  /** Việc đang bung việc con — điều khiển từ ngoài, xem `TaskGroupsBoard`. */
  expandedTaskId: number | null
  onToggleExpand: (taskId: number) => void
  /** Chiều cao CỐ ĐỊNH mỗi dòng (px) — chỉ Gantt truyền. Xem `TaskGroupsBoard`. */
  rowHeight?: number
  /** Ghim ô tên khi cuộn ngang — chỉ Gantt. Xem `TaskListRow.stickyTitle`. */
  stickyTitle?: boolean
  /** Thêm việc vào ĐÚNG cột này — `sectionId` null với nhóm "Chưa phân cột". */
  onAddTask: (sectionId: number | null, draft: NewTaskDraft) => void
}

/**
 * Một NHÓM trên khung nhìn Danh sách: tiêu đề thu/mở + các dòng + «Việc mới».
 *
 * Số đếm trên tiêu đề là số việc SAU KHI LỌC, không phải tổng của cột — người
 * dùng đang nhìn bộ lọc nào thì con số phải nói về đúng bộ lọc ấy, chứ hiện
 * tổng thì nó mâu thuẫn ngay với số dòng đếm được bên dưới.
 */
export function TaskListGroup({
  group,
  columns,
  fields,
  labelFields,
  members,
  canEdit,
  collapsed,
  onToggleCollapse,
  defaultPicId,
  draggable,
  sectionDraggable,
  dragActive,
  dragBlocked,
  showDropTarget,
  expandedTaskId,
  onToggleExpand,
  rowHeight,
  stickyTitle,
  onAddTask,
  ...rowActions
}: TaskListGroupProps) {

  /*  Vùng hứng của CẢ nhóm, kể cả khi nhóm rỗng: không có nó thì cột chưa có
      việc nào không nhận được cú thả, mà đó lại đúng là lúc người ta hay kéo
      việc sang. `sectionId` null (nhóm "Chưa phân cột") không phải cột thật nên
      không đăng ký vùng thả — máy chủ cần một `section_id` có thật.  */
  const { setNodeRef, isOver } = useDroppable({
    id: group.sectionId === null ? `ungrouped-${group.key}` : columnDroppableId(group.sectionId),
    disabled: !draggable || group.sectionId === null,
  })

  /*  Cả nhóm là một món kéo được để ĐỔI THỨ TỰ CỘT — cùng id, cùng luật, cùng
      endpoint với kéo cột ở kanban, chỉ khác là ở đây hàng cột nằm DỌC.

      Vùng hứng thẻ và món đồ kéo được phải mang hai id khác họ (`section-` và
      `column-`) vì dnd-kit cấm hai đăng ký trùng id — xem `kanban-drop.ts`.
      Nhóm "Chưa phân cột" không phải cột thật nên không kéo được.  */
  /*  ⚠️ Phải PHÁ RA từng biến chứ không giữ nguyên đối tượng `sortable`:
      `react-hooks/refs` của ESLint 10 thấy `sortable.setNodeRef` là kết luận
      đang đọc một ref trong lúc dựng và bắn cảnh báo cho MỌI thuộc tính đọc
      qua nó. Cùng lối viết với `kanban-column.tsx` và `task-list-row.tsx`.  */
  const {
    attributes: sectionAttributes,
    listeners: sectionListeners,
    setNodeRef: setSectionRef,
    isDragging: sectionDragging,
    transform: sectionTransform,
    transition: sectionTransition,
  } = useSortable({
    id: columnSortableId(group.sectionId ?? 0),
    disabled: !sectionDraggable || group.sectionId === null,
    data: { type: 'column', sectionId: group.sectionId, label: group.name },
  })
  const showSectionGrip = sectionDraggable && group.sectionId !== null

  const sortableIds = useMemo(() => group.tasks.map((t) => taskDraggableId(t.id)), [group.tasks])

  return (
    //  Nhóm DẠT RA để chừa chỗ trong lúc kéo cột (`verticalListSortingStrategy`
    //  ở `TaskListView`) — bản đang đi theo con trỏ vẫn là tấm thẻ ở `DragOverlay`,
    //  còn nhóm gốc thì mờ đi và trượt tới chỗ nó sắp đậu.
    //  `bg-background` + `zIndex`: nhóm trượt đè lên nhóm khác, để nền trong
    //  suốt là hai bảng chồng chữ lên nhau giữa quãng trượt.
    <section
      ref={setSectionRef}
      style={{
        transform: CSS.Translate.toString(sectionTransform),
        transition: sectionTransition,
        zIndex: sectionDragging ? 1 : undefined,
      }}
      className={cn('relative', sectionDragging && 'bg-background opacity-40')}
    >
      {/*  Tay cầm kéo nhóm nằm TUYỆT ĐỐI trong khoảng lề trái, đúng chỗ và đúng
           lối hiện-khi-rê-chuột của tay cầm trên từng dòng việc. Tách khỏi nút
           thu/mở chứ không gắn `listeners` thẳng lên nó: gắn chung thì phím
           Space bị dnd-kit nuốt để bắt đầu kéo, người dùng bàn phím mất luôn
           cách bật/tắt nhóm.  */}
      <div className="group/section relative flex items-center">
        {showSectionGrip && (
          <button
            type="button"
            aria-label={`Kéo để xếp lại cột: ${group.name}`}
            {...sectionAttributes}
            {...sectionListeners}
            className={cn(
              'absolute top-1/2 left-0.5 -translate-y-1/2 cursor-grab touch-none rounded p-0.5',
              'text-muted-foreground transition-opacity focus-visible:opacity-100 active:cursor-grabbing',
              dragActive ? 'opacity-100' : 'opacity-0 group-hover/section:opacity-100',
            )}
          >
            <GripVertical className="size-3.5" />
          </button>
        )}

        <button
          type="button"
          onClick={onToggleCollapse}
          aria-expanded={!collapsed}
          style={{ height: rowHeight, width: stickyTitle ? 'max-content' : undefined }}
          /*  Không còn tô sáng dải tiêu đề khi con trỏ đi qua: hàng cột nay dạt
              ra chừa chỗ, khe hở đã nói rõ chỗ đậu — tô thêm một dải nữa là hai
              tín hiệu chỉ về hai chỗ khác nhau.  */
          className={cn(
            'flex w-full items-center gap-1.5 py-2 pr-2 pl-6 text-left',
            !dragActive && 'hover:bg-accent/30',
            //  Tiêu đề nhóm cũng ghim lại khi cuộn ngang, cùng lý do với ô tên:
            //  kéo sang phải mà mất tên nhóm thì không biết đang xem cột nào.
            stickyTitle && 'sticky left-0 z-10 bg-canvas',
          )}
        >
          <ChevronRight
            className={cn(
              'size-4 text-muted-foreground transition-transform',
              !collapsed && 'rotate-90',
            )}
          />
          <span className={cn('size-2 shrink-0 rounded-full', dotClass(group.color))} />
          <span className="text-sm font-medium">{group.name}</span>
          <span className="text-xs tabular-nums text-muted-foreground">{group.tasks.length}</span>
        </button>
      </div>

      {/*  Cột đang bị kéo thì THU LẠI còn mỗi dải tiêu đề, không mang theo đàn
           việc bên trong. Một cột đang bung có thể cao vài trăm pixel: để nguyên
           thì cái đang trôi theo con trỏ là một mảng xám gần bằng nửa màn hình,
           che mất chính hàng cột mà người dùng đang ngắm để thả, và khe chờ phải
           mở ra cũng to bằng chừng ấy nên hàng cột giật nảy mỗi lần đổi đích.
           Thu lại thì cú kéo gọn đúng bằng cái đang cầm — một dòng tiêu đề.  */}
      {!collapsed && !sectionDragging && (
        <div ref={setNodeRef} className={cn(isOver && showDropTarget && 'bg-accent/20')}>
          <SortableContext items={sortableIds} strategy={noDisplacement}>
            {group.tasks.map((task) => (
              <TaskRowWithSubtasks
                key={task.id}
                task={task}
                columns={columns}
                fields={fields}
                labelFields={labelFields}
                members={members}
                canEdit={canEdit}
                draggable={draggable && canEdit}
                dragActive={dragActive}
                dragBlocked={dragBlocked}
                expanded={expandedTaskId === task.id}
                onToggleExpand={() => onToggleExpand(task.id)}
                rowHeight={rowHeight}
                stickyTitle={stickyTitle}
                {...rowActions}
              />
            ))}
          </SortableContext>

          {canEdit && (
            <NewTaskRow
              columns={columns}
              members={members}
              defaultPicId={defaultPicId}
              rowHeight={rowHeight}
              stickyTitle={stickyTitle}
              onAdd={(draft) => onAddTask(group.sectionId, draft)}
            />
          )}
        </div>
      )}
    </section>
  )
}

interface TaskRowWithSubtasksProps extends TaskRowActions {
  task: WorkTask
  columns: TaskListColumn[]
  fields: CardFields
  labelFields: WorkLabelField[]
  members: WorkMember[]
  canEdit: boolean
  draggable: boolean
  dragActive: boolean
  dragBlocked: boolean
  expanded: boolean
  onToggleExpand: () => void
  rowHeight?: number
  stickyTitle?: boolean
}

/**
 * Một dòng cha kèm các dòng việc con khi được bung.
 *
 * Việc con nạp LƯỜI qua `GET /tasks/{id}` chứ không nằm sẵn trong payload bảng:
 * bảng đang trả 41 việc thì kèm luôn 82 việc con là gấp ba lượng dữ liệu cho
 * một thứ đa số người dùng không bung. Dùng lại đúng query của panel chi tiết
 * nên bung ở đây rồi mở panel là đã có sẵn trong cache, không gọi thêm lượt nào.
 *
 * Cụm việc con có `SortableContext` RIÊNG, lồng trong context của nhóm: chúng
 * chỉ được xếp lại với nhau, không lẫn vào hàng task cha. Gộp chung một context
 * thì dnd-kit dồn chỗ chéo giữa hai cấp, mà cú thả thì máy chủ từ chối.
 *
 * Và là cụm DUY NHẤT chạy `verticalListSortingStrategy` — các dòng anh em dạt ra
 * chừa khe ngay dưới con trỏ, đúng lối kéo thả quen thuộc. Ở đây làm được vì cụm
 * kín và ngắn (vài dòng, thứ tự đổi trong chính nó), khác hẳn hàng việc cha nơi
 * dồn chỗ phải chạy qua hàng chục dòng nặng nên mới bỏ (`list-sorting-strategy.ts`).
 */
function TaskRowWithSubtasks({ task, expanded, ...rest }: TaskRowWithSubtasksProps) {
  const { data: detail } = useWorkTask(expanded ? task.id : undefined)

  const subtasks = useMemo(() => detail?.subtasks ?? [], [detail?.subtasks])
  const siblingIds = useMemo(() => subtasks.map((s) => s.id), [subtasks])
  const sortableIds = useMemo(() => siblingIds.map(taskDraggableId), [siblingIds])

  return (
    <>
      <TaskListRow task={task} expanded={expanded} {...rest} />
      {expanded && subtasks.length > 0 && (
        <SortableContext items={sortableIds} strategy={verticalListSortingStrategy}>
          {subtasks.map((sub, index) => (
            <TaskListRow
              key={sub.id}
              task={sub}
              isSubtask
              isLastSubtask={index === subtasks.length - 1}
              subtaskGroup={{ parentId: task.id, siblingIds }}
              {...rest}
              //  Đè SAU `{...rest}`: việc con đi đường tick riêng, gắn sẵn id cha.
              onToggleDone={(subtaskId, done) => rest.onToggleSubtaskDone(task.id, subtaskId, done)}
            />
          ))}
        </SortableContext>
      )}
    </>
  )
}

function NewTaskRow({
  columns,
  members,
  defaultPicId,
  rowHeight,
  stickyTitle,
  onAdd,
}: {
  columns: TaskListColumn[]
  members: WorkMember[]
  defaultPicId?: number
  rowHeight?: number
  stickyTitle?: boolean
  onAdd: (draft: NewTaskDraft) => void
}) {
  const [typing, setTyping] = useState(false)

  if (typing) {
    return (
      <TaskDraftRow
        columns={columns}
        members={members}
        defaultPicId={defaultPicId}
        rowHeight={rowHeight}
        stickyTitle={stickyTitle}
        onCancel={() => setTyping(false)}
        onSave={onAdd}
      />
    )
  }

  /*  Cùng bố cục dẫn đầu với `TaskListRow`: chỗ trống bằng đúng nút bung việc
      con, rồi dấu «+» đứng đúng chỗ ô tick. Nhờ vậy chữ «Việc mới» thẳng hàng
      với tên việc ngay bên trên, thay vì thụt một khoảng lệch nhìn thấy rõ.  */
  return (
    <button
      type="button"
      onClick={() => setTyping(true)}
      style={{ paddingLeft: stickyTitle ? 0 : ROW_PAD_LEFT, height: rowHeight }}
      className="flex w-full items-center border-b border-border/60 bg-muted/30 py-1.5 pr-2 text-left text-sm text-muted-foreground hover:bg-accent/40 hover:text-foreground"
    >
      {/*  Ghim phần CHỮ chứ không ghim cả cái nút: nút rộng bằng cả bảng nên
           `sticky` trên nó không dịch được đi đâu, cuộn ngang một quãng là chữ
           «Việc mới» trôi khỏi màn hình và dòng nhìn như trống trơn. */}
      <span
        className={cn('flex items-center gap-1.5', stickyTitle && 'sticky left-0')}
        style={{ paddingLeft: stickyTitle ? ROW_PAD_LEFT : 0 }}
      >
        <span className="w-[18px] shrink-0" aria-hidden />
        <Plus className="size-4 shrink-0" />
        <span className="px-1">Việc mới</span>
      </span>
    </button>
  )
}
