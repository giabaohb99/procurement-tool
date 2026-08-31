import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  MeasuringStrategy,
  closestCenter,
  pointerWithin,
  defaultDropAnimationSideEffects,
  useSensor,
  useSensors,
  type CollisionDetection,
  type DropAnimation,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { Ban, Circle } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'

import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { useCollapsedGroups } from '../hooks/use-collapsed-groups'
import { columnWidthVar, useListColumnWidths } from '../hooks/use-list-column-widths'
import type { CardFields } from '../types/view-options'
import type { WorkLabelField, WorkMember, WorkSection, WorkTask } from '../types/work'
import { groupTasksBySection } from '../utils/group-tasks'
import { TITLE_COLUMN, buildListColumns } from '../utils/list-columns'
import {
  columnSortableId,
  isSamePlace,
  parseDropTarget,
  resolveColumnDrop,
  resolveDropPlace,
  taskDraggableId,
  type DropTarget,
  type KanbanDropPlace,
} from '../utils/kanban-drop'
import { isSubtaskDragData, resolveSubtaskDrop } from '../utils/subtask-drop'
import { LEAD_WIDTH, ROW_PAD_LEFT } from '../utils/list-metrics'
import { ListColumnResizer } from './list-column-resizer'
import type { NewTaskDraft } from './task-draft-row'
import { TaskListGroup } from './task-list-group'
import type { TaskRowActions } from './task-list-row'

/** `gap-1.5` giữa các ô, tính bằng px — phải khớp với lớp Tailwind của dòng. */
const COLUMN_GAP = 6

/**
 * Đo lại vùng thả LIÊN TỤC, không chỉ một lần lúc bắt đầu kéo (mặc định).
 *
 * Với mặc định `WhileDragging`, CÚ KÉO ĐẦU TIÊN sau khi mở màn hình không có
 * kích thước nào để đối chiếu: `over` rỗng suốt cú kéo, thả xuống là không có
 * gì xảy ra — thao tác bị nuốt không một lời báo. Lỗi này tái hiện được 100%
 * (tải lại trang → bung việc con → kéo phát đầu), và từ cú kéo thứ hai trở đi
 * thì bình thường, nên rất dễ tưởng là máy lag.
 *
 * Bảng còn thu/mở nhóm và bung việc con ngay giữa lúc kéo, mỗi lần như thế là
 * mọi dòng bên dưới đổi chỗ — số đo cũ sai ngay lập tức.
 *
 * PHẢI là hằng ngoài component. Viết thẳng object vào JSX là mỗi lần vẽ lại một
 * tham chiếu mới, `DndContext` thấy cấu hình "đổi" nên hẹn đo lại, đo xong đặt
 * state, state đổi lại vẽ lại — React ngắt bằng «Maximum update depth exceeded»
 * và cả bảng trắng trang. Cùng một cái bẫy đã vá ở `kanban-board.tsx`.
 */
const MEASURING = { droppable: { strategy: MeasuringStrategy.Always } }

/**
 * Hiệu ứng ĐẶT XUỐNG cho món KHÔNG dồn chỗ (việc cha): tấm thẻ trôi từ chỗ buông
 * tay về đúng chỗ dòng vừa nằm vào, rồi mới biến mất.
 *
 * ⚠️ KHÔNG dùng cho việc con / cột — xem {@link dropAnimationFor}.
 *
 * `dropAnimation={null}` như bản trước là thẻ tắt phụt tại chỗ buông, còn dòng
 * thì hiện ra ở chỗ khác — mắt không nối được hai sự kiện, cảm giác như món đồ
 * dịch chuyển tức thời và phải đi tìm xem nó rơi đâu.
 *
 * `styles.active.opacity = 0` là mảnh ghép bắt buộc: thả xong là dnd-kit xóa
 * `active` ngay nên dòng thật hết mờ và hiện đủ ở chỗ mới, trong khi lớp phủ vẫn
 * đang bay tới — thành ra thấy HAI bản cùng lúc. Giấu dòng thật đúng bằng thời
 * gian bay là xong.
 *
 * 180ms + đường cong giảm tốc: đủ để mắt bám theo, chưa đủ để thấy chậm.
 */
const DROP_ANIMATION: DropAnimation = {
  duration: 180,
  easing: 'cubic-bezier(0.2, 0.9, 0.3, 1)',
  sideEffects: defaultDropAnimationSideEffects({ styles: { active: { opacity: '0' } } }),
}

/**
 * Hiệu ứng đặt xuống theo LOẠI món đang kéo.
 *
 * Món có dồn chỗ (việc con, cột) phải là `null`. Lý do: dnd-kit ngắm đích bay
 * bằng cách ĐO chính dòng gốc ngay lúc buông tay, mà đúng lúc ấy `transform` dồn
 * chỗ vừa bị gỡ còn thứ tự mới thì chưa kịp về (cập nhật lạc quan của TanStack
 * Query chạy ở một micro-task sau). Đo được là chỗ CŨ — nên tấm thẻ bay ngược
 * trở lại điểm xuất phát rồi tắt, trong khi dòng thật hiện ra ở chỗ mới: đo
 * được, thấy rõ, và là đúng cú "nhảy cóc" mà hiệu ứng này sinh ra để tránh.
 *
 * Bỏ hiệu ứng đi thì lớp phủ tắt ngay tại chỗ buông, còn dòng thật tự trượt về
 * chỗ mới bằng hiệu ứng dồn chỗ sẵn có của `@dnd-kit/sortable` — liền mạch hơn
 * hẳn, và không cần biết cập nhật lạc quan về lúc nào.
 */
function dropAnimationFor(kind: DragState['kind']): DropAnimation | null {
  return kind === 'task' ? DROP_ANIMATION : null
}

/**
 * Tự cuộn khi kéo tới gần mép — HIỀN hơn mặc định, và chỉ theo chiều DỌC.
 *
 * Mặc định (ngưỡng 25%, gia tốc 10) cuộn nhanh tới mức đo được: giữ con trỏ yên
 * ở mép dưới 150ms là trang trôi hơn 230px, cụm việc con trượt hẳn ra khỏi chỗ
 * con trỏ đang chỉ — `over` mất, người dùng thấy dấu cấm dù chưa hề rê ra ngoài.
 *
 * Chiều NGANG tắt hẳn: bảng cuộn ngang để xem cột, tự trượt ngang giữa lúc đang
 * nhắm một dòng thì mất luôn điểm tựa để ngắm.
 */
const AUTO_SCROLL = { threshold: { x: 0, y: 0.15 }, acceleration: 6 }

/** Món đang được kéo — đủ để vẽ lớp phủ và tắt mấy hiệu ứng gây nhiễu. */
interface DragState {
  kind: 'task' | 'subtask' | 'column'
  /** Tên việc, vẽ trong lớp phủ bám con trỏ. */
  label: string | null
  /** Con trỏ đang ở chỗ KHÔNG thả được — lớp phủ đổi dáng, con trỏ đổi biểu tượng. */
  blocked: boolean
}

/**
 * Thứ tự ƯU TIÊN khi con trỏ nằm trên nhiều vùng thả LỒNG NHAU cùng lúc.
 *
 * Một dòng luôn nằm trong thân nhóm (`section-`), thân nhóm lại nằm trong vỏ
 * nhóm (`column-`), nên `pointerWithin` trả về cả ba. Cụ thể nhất thắng — đó là
 * cái người dùng đang chỉ vào.
 */
const DROP_PRIORITY = ['task-', 'section-', 'column-']

function pickMostSpecific(collisions: ReturnType<CollisionDetection>) {
  for (const prefix of DROP_PRIORITY) {
    const hit = collisions.find((c) => String(c.id).startsWith(prefix))
    if (hit) return [hit]
  }
  return collisions
}

/**
 * Va chạm — **`pointerWithin` trước, `closestCenter` chỉ để vét**.
 *
 * `closestCenter` một mình là sai ở bảng này, và sai âm thầm. Nó so khoảng cách
 * TỚI TÂM, mà thân nhóm cũng là một vùng thả: nhóm bốn dòng cao ~180px có tâm
 * nằm đâu đó giữa dòng 2 và 3, nên rê tới quãng ấy thì tâm nhóm gần hơn tâm mọi
 * dòng → `over` thành cả NHÓM → `resolveDropPlace` hiểu là "thả vào khoảng
 * trống" và đẩy việc xuống CUỐI nhóm. Người dùng nhắm dòng thứ hai, thả ra, việc
 * rơi xuống đáy. Đo được: kéo một việc xuống đúng một dòng, nó nhảy xuống cuối.
 *
 * `pointerWithin` chỉ nhận vùng THỰC SỰ chứa con trỏ nên không có chuyện đó;
 * `closestCenter` chỉ còn dùng khi con trỏ không nằm trên vùng nào (mép bảng,
 * dải «Việc mới»), lúc ấy "gần nhất" mới đúng là ý người dùng.
 *
 * **Việc con** thì thêm một lớp nữa: chỉ nhìn thấy anh em cùng cha, mọi thứ khác
 * vô hình. Không có nó thì rê ra khỏi cụm cả trăm pixel `closestCenter` vẫn bám
 * lấy anh em gần nhất và cú thả vẫn ăn ở chỗ người dùng không hề nhắm tới; ở đây
 * ra khỏi cụm là `over` rỗng — đúng lúc để báo "không thả được" và bỏ qua.
 */
const detectCollisions: CollisionDetection = (args) => {
  const active = args.active.data.current

  if (isSubtaskDragData(active)) {
    const siblings = new Set(active.siblingIds.map((id) => String(taskDraggableId(id))))
    return pointerWithin({
      ...args,
      droppableContainers: args.droppableContainers.filter((c) => siblings.has(String(c.id))),
    })
  }

  /*  Kéo CẢ CỘT thì chỉ nhìn thấy các cột khác. Không có nhánh này thì `over`
      gần như luôn là một DÒNG VIỆC — cột nào cũng cao hàng trăm pixel và con trỏ
      đa phần rơi vào giữa thân nó — nên `SortableContext` của hàng cột không bao
      giờ có `overIndex`, và hàng cột đứng im suốt cú kéo dù đã bật chiến lược
      dồn chỗ. `handleDragEnd` vẫn suy ngược được từ dòng ra cột, nhưng cái người
      dùng THẤY lúc rê thì không.  */
  if (active?.type === 'column') {
    const columnsOnly = {
      ...args,
      droppableContainers: args.droppableContainers.filter((c) =>
        String(c.id).startsWith('column-'),
      ),
    }
    const within = pointerWithin(columnsOnly)
    return within.length ? within : closestCenter(columnsOnly)
  }

  const within = pointerWithin(args)
  return within.length ? pickMostSpecific(within) : closestCenter(args)
}

interface TaskListViewProps extends TaskRowActions {
  listId: number
  tasks: WorkTask[]
  sections: WorkSection[]
  labelFields: WorkLabelField[]
  members: WorkMember[]
  fields: CardFields
  canEdit: boolean
  /** Quản trị dự án — chỉ họ mới xếp lại được CỘT (cột là cấu hình của dự án). */
  canManage: boolean
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
  onMoveSubtask: (parentId: number, subtaskId: number, beforeTaskId: number | null) => void
  onMoveSection: (sectionId: number, beforeSectionId: number | null) => void
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
 *
 * **Ba tầng kéo thả** cùng sống trong một `DndContext`, phân biệt bằng `type`
 * trong `data` của món đang kéo: NHÓM (đổi thứ tự cột), VIỆC (đổi cột + đổi thứ
 * tự), VIỆC CON (xếp lại trong cụm của cha). Mỗi tầng một luật và một endpoint,
 * nên `onDragEnd` rẽ nhánh ngay từ đầu thay vì cố nhét chung một công thức.
 */
export function TaskListView({
  listId,
  tasks,
  sections,
  labelFields,
  members,
  fields,
  canEdit,
  canManage,
  isLoading,
  defaultPicId,
  dragEnabled,
  onMoveTask,
  onMoveSubtask,
  onMoveSection,
  onAddTask,
  ...rowActions
}: TaskListViewProps) {
  const { isCollapsed, toggle } = useCollapsedGroups(listId)
  const gridRef = useRef<HTMLDivElement>(null)
  const [drag, setDrag] = useState<DragState | null>(null)
  /*  Loại món của cú kéo VỪA XONG. Không đọc được từ `drag`: hiệu ứng đặt xuống
      chỉ chạy SAU khi `drag` đã về `null`, lúc ấy hỏi nó thì không còn gì.  */
  const [dropKind, setDropKind] = useState<DragState['kind']>('task')

  const groups = useMemo(() => groupTasksBySection(tasks, sections), [tasks, sections])
  const columns = useMemo(() => buildListColumns(fields, labelFields), [fields, labelFields])
  //  Cột TÊN đi cùng các cột dữ liệu trong bộ bề rộng — nó cũng kéo giãn và nhớ
  //  được — nhưng KHÔNG nằm trong `columns`: nó có bố cục riêng (mũi tên bung, ô
  //  tick, huy hiệu) chứ không phải một ô dữ liệu vẽ bằng `TaskListCell`.
  const widthColumns = useMemo(() => [TITLE_COLUMN, ...columns], [columns])
  const { resize, styleVars, totalWidth } = useListColumnWidths(listId, widthColumns)

  /*  Bản đồ cột→việc cho `resolveDropPlace` — dùng lại nguyên bộ tính vị trí của
      kanban thay vì viết bản thứ hai. Nhóm "Chưa phân cột" (`sectionId` null) bị
      loại: nó không phải một cột có thật nên không thể là đích thả.  */
  const columnMap = useMemo(() => {
    const map = new Map<number, WorkTask[]>()
    for (const g of groups) if (g.sectionId !== null) map.set(g.sectionId, g.tasks)
    return map
  }, [groups])

  //  Id phải giữ nguyên tham chiếu giữa các lần vẽ, không thì mỗi nhịp kéo là
  //  `SortableContext` tưởng hàng cột vừa đổi và đo lại toàn bộ.
  const sectionIds = useMemo(() => sections.map((s) => s.id), [sections])
  const sectionSortableIds = useMemo(() => sectionIds.map(columnSortableId), [sectionIds])

  const sensors = useSensors(
    //  Ngưỡng 6px: dưới mức đó vẫn tính là CÚ BẤM, nếu không thì bấm mở panel
    //  chi tiết mà tay hơi rung là thành một cú kéo hụt.
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  function handleDragStart(event: DragStartEvent) {
    const data = event.active.data.current
    const kind = data?.type
    if (kind !== 'task' && kind !== 'subtask' && kind !== 'column') return
    setDropKind(kind)
    setDrag({ kind, label: typeof data?.label === 'string' ? data.label : null, blocked: false })
  }

  /*  Chỉ theo dõi việc con: `detectCollisions` đã bịt mắt nó với mọi thứ ngoài
      cụm, nên `over` rỗng nghĩa là con trỏ đã ra khỏi cụm — chính là lúc phải
      báo "không thả được ở đây".

      So trước khi `setDrag` để không dựng lại cây ở MỖI nhịp rê chuột; giá trị
      chỉ đổi đúng hai lần: lúc ra khỏi cụm và lúc quay vào.  */
  function handleDragOver(event: DragOverEvent) {
    setDrag((prev) => {
      if (!prev || prev.kind !== 'subtask') return prev
      const blocked = event.over === null
      return blocked === prev.blocked ? prev : { ...prev, blocked }
    })
  }

  function handleDragEnd(event: DragEndEvent) {
    setDrag(null)

    const active = event.active.data.current
    const overData = event.over?.data.current

    if (isSubtaskDragData(active)) {
      const drop = resolveSubtaskDrop(active, overData)
      if (drop) onMoveSubtask(drop.parentId, active.taskId, drop.beforeTaskId)
      return
    }

    /*  Rê trúng một dòng VIỆC CON thì quy về dòng CHA của nó. Việc con không có
        trong bản đồ cột, để nguyên thì mọi cú thả rơi trúng nó đều rơi vào hư
        không — mà cụm việc con đang bung lại chiếm đúng khoảng giữa cột, tức
        chỗ người ta hay thả nhất.  */
    const target: DropTarget | null = isSubtaskDragData(overData)
      ? { type: 'task', taskId: overData.parentId }
      : parseDropTarget(event.over?.id)

    if (active?.type === 'column' && typeof active.sectionId === 'number') {
      const to = sectionOfTarget(columnMap, target)
      if (to === null || to === active.sectionId) return
      const place = resolveColumnDrop(sectionIds, active.sectionId, to)
      if (place) onMoveSection(active.sectionId, place.beforeSectionId)
      return
    }

    if (typeof active?.taskId !== 'number') return
    const activeId = active.taskId
    const place = resolveDropPlace(columnMap, activeId, target)
    const task = tasks.find((t) => t.id === activeId)
    //  Thả về đúng chỗ cũ thì im lặng — đừng bắn một lượt PATCH không đổi gì,
    //  nó chỉ làm bẩn nhật ký thao tác.
    if (!place || !task || isSamePlace(columnMap, task, place)) return
    onMoveTask(activeId, place)
  }

  /*  Bề rộng tối thiểu TÍNH RA chứ không gõ cứng: hẹp hơn tổng các cột là cột
      nào đó bị bóp lại và chữ trong nó cụt còn dăm ba chữ cái — thà cho cuộn
      ngang. Số cột lẫn bề rộng đều đổi được lúc chạy nên một hằng số không thể
      đúng mãi. Cộng cả lề trái của dòng: nó nằm ngoài mọi cột.  */
  const minWidth = ROW_PAD_LEFT + totalWidth + widthColumns.length * COLUMN_GAP

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
      collisionDetection={detectCollisions}
      measuring={MEASURING}
      autoScroll={AUTO_SCROLL}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setDrag(null)}
    >
      {/*  Con trỏ "cấm" phải đặt lên CON của khung chứ không phải chính khung:
           mỗi dòng tự khai `cursor-pointer`, mà khai ở con thì nó thắng thừa kế
           từ cha — không có `[&_*]` thì cả vùng vẫn hiện bàn tay như thường. */}
      <div className={cn('overflow-x-auto', drag?.blocked && '[&_*]:cursor-not-allowed')}>
        <div ref={gridRef} style={{ ...styleVars, minWidth }}>
          <div
            role="row"
            /*  Cùng `paddingLeft` với dòng việc (không phải `px-2` như trước):
                có thế mép TRÁI của ô tiêu đề mới trùng mép trái ô tên bên dưới,
                mà hai ô nay rộng bằng nhau nên mép PHẢI — chỗ đặt tay cầm kéo —
                cũng trùng nốt. `py-2.5` cho hàng tiêu đề thở hơn phần thân.  */
            style={{ paddingLeft: ROW_PAD_LEFT }}
            className="group/head flex items-center gap-1.5 border-b bg-muted/30 py-2.5 pr-2 text-xs font-medium text-muted-foreground"
          >
            <span
              className="relative shrink-0"
              style={{
                width: `var(${columnWidthVar(TITLE_COLUMN.key)})`,
                paddingLeft: LEAD_WIDTH,
              }}
            >
              <span className="block truncate">{TITLE_COLUMN.label}</span>
              <ListColumnResizer
                columnKey={TITLE_COLUMN.key}
                gridRef={gridRef}
                minWidth={TITLE_COLUMN.minWidth}
                onResize={(width) => resize(TITLE_COLUMN.key, width)}
              />
            </span>

            {/*  Khoảng đệm nuốt phần dư của khung: các cột dữ liệu vẫn dính mép
                 phải như trước, còn cột tên thì có bề rộng thật để mà kéo. */}
            <span className="min-w-0 flex-1" aria-hidden />

            {columns.map((col) => (
              //  KHÔNG đặt `truncate` ở đây: nó kèm `overflow-hidden`, mà tay cầm
              //  kéo giãn nằm ở `-right-1.5` — tức NGOÀI hộp — nên bị cắt mất,
              //  nhìn như bảng không kéo giãn được. Cắt chữ để cho lớp con.
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

          {/*  Hàng CỘT dồn chỗ thật: kéo một cột đi thì các cột khác dạt lên/xuống
               để chừa chỗ, nhìn ra ngay nó sẽ nằm giữa hai cột nào. Cột cao thấp
               khác nhau vẫn đúng — `verticalListSortingStrategy` dịch mỗi cột bị
               ảnh hưởng đúng bằng chiều cao của cột đang kéo, và tính chỗ đậu của
               chính nó từ hình chữ nhật thật của cột đích. */}
          <SortableContext items={sectionSortableIds} strategy={verticalListSortingStrategy}>
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
                sectionDraggable={canManage}
                dragActive={drag !== null}
                dragBlocked={drag?.blocked ?? false}
                //  Vệt sáng "thả được vào cột này" chỉ có nghĩa khi đang kéo một
                //  VIỆC. Kéo việc con hay kéo cả nhóm mà cột vẫn sáng lên thì nó
                //  hứa một chỗ thả không có thật.
                showDropTarget={drag?.kind === 'task'}
                onAddTask={onAddTask}
                {...rowActions}
              />
            ))}
          </SortableContext>
        </div>
      </div>

      {/*  Tấm thẻ bám con trỏ — CHỈ ô tick + tên việc, đúng như Lark. Chép cả
           dòng vào đây thì lớp phủ rộng bằng màn hình và che mất chính khu vực
           người dùng đang nhắm thả; `w-fit` là bắt buộc vì dnd-kit ép khung phủ
           rộng đúng bằng dòng gốc. */}
      <DragOverlay dropAnimation={dropAnimationFor(dropKind)}>
        {drag && (
          <div
            className={cn(
              'flex w-fit max-w-sm items-center gap-2 rounded-md border bg-card py-1.5 pr-4 pl-3 text-sm shadow-lg',
              drag.blocked && 'border-destructive/60 text-destructive',
            )}
          >
            {drag.blocked ? (
              <Ban className="size-4 shrink-0" />
            ) : (
              <Circle className="size-4 shrink-0 text-muted-foreground" />
            )}
            <span className="truncate">{drag.label}</span>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  )
}

/**
 * Cột mà một đích thả thuộc về — dùng khi đang kéo CẢ NHÓM.
 *
 * Rê một nhóm đi thì con trỏ đa phần nằm trên các dòng việc của nhóm khác chứ
 * không trúng đúng dải tiêu đề của nó, nên phải suy ngược từ dòng ra cột. Thiếu
 * bước này thì kéo nhóm gần như không bao giờ ăn.
 */
function sectionOfTarget(
  columnMap: Map<number, WorkTask[]>,
  target: DropTarget | null,
): number | null {
  if (!target) return null
  if (target.type === 'section' || target.type === 'column') return target.sectionId
  for (const [sectionId, list] of columnMap) {
    if (list.some((t) => t.id === target.taskId)) return sectionId
  }
  return null
}
