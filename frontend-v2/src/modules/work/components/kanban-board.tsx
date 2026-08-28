import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  MeasuringStrategy,
  PointerSensor,
  closestCorners,
  pointerWithin,
  rectIntersection,
  useSensor,
  useSensors,
  type CollisionDetection,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  horizontalListSortingStrategy,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable'
import { Plus } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import type { WorkLabelField, WorkSection, WorkTag, WorkTask } from '../types/work'
import {
  applyMove,
  groupBySection,
  isSamePlace,
  columnSortableId,
  parseDropTarget,
  resolveColumnDrop,
  resolveDropPlace,
  type KanbanDropPlace,
} from '../utils/kanban-drop'
import { KanbanColumn } from './kanban-column'
import { TaskCardBody } from './task-card'
import type { CardFields } from '../types/view-options'

/**
 * Ảnh xem trước dời thẻ sang cột khác NGAY TRONG LÚC KÉO, nên chiều cao các cột
 * đổi liên tục. Để dnd-kit đo một lần lúc bắt đầu (mặc định) thì nó tính va chạm
 * trên hình dạng cũ — thẻ đã dời rồi mà con trỏ vẫn bắt vào chỗ trống.
 *
 * PHẢI là hằng ngoài component. Viết thẳng object vào JSX là mỗi lần vẽ lại một
 * tham chiếu mới, `DndContext` thấy cấu hình "đổi" nên hẹn đo lại, đo xong đặt
 * state, state đổi lại vẽ lại — React ngắt bằng «Maximum update depth exceeded»
 * và cả bảng trắng trang.
 */
const MEASURING = { droppable: { strategy: MeasuringStrategy.Always } }

interface KanbanBoardProps {
  sections: WorkSection[]
  tasks: WorkTask[]
  tags: WorkTag[]
  labelFields: WorkLabelField[]
  fields: CardFields
  canEdit: boolean
  canManage: boolean
  /** Đang sắp xếp khác «Tay» thì khóa việc đổi thứ tự trong cột (§3.4). */
  sortLocked: boolean
  onOpenTask: (taskId: number) => void
  onCreateTask: (sectionId: number, title: string) => void
  onMoveTask: (taskId: number, place: KanbanDropPlace) => void
  /** Kéo đổi thứ tự CỘT. `beforeSectionId = null` = đẩy xuống cuối hàng. */
  onMoveSection: (sectionId: number, beforeSectionId: number | null) => void
  onAddSection: () => void
  onRenameSection: (section: WorkSection) => void
  onDeleteSection: (section: WorkSection) => void
}

/**
 * Bảng kanban (D-01). Kéo thả bằng dnd-kit, cùng bộ cảm biến với màn Phân quyền
 * và Luồng duyệt: phải kéo đi 6px mới tính là kéo, không thì mỗi cú bấm mở thẻ
 * đều bị nuốt thành một thao tác kéo dài 0 pixel.
 *
 * Thẻ đang kéo được vẽ ở **`DragOverlay`** — một lớp nổi bám con trỏ, nằm ngoài
 * cột. Thẻ gốc chỉ mờ đi tại chỗ. Làm vậy vì lớp phủ không bị cột cắt khi kéo
 * sang cột đang cuộn, và nó không dính hiệu ứng dồn chỗ của danh sách nên chạy
 * đúng theo con trỏ.
 */
export function KanbanBoard({
  sections,
  tasks,
  tags,
  labelFields,
  fields,
  canEdit,
  canManage,
  sortLocked,
  onOpenTask,
  onCreateTask,
  onMoveTask,
  onMoveSection,
  onAddSection,
  onRenameSection,
  onDeleteSection,
}: KanbanBoardProps) {
  const [dragged, setDragged] = useState<WorkTask | null>(null)
  //  Cột đang được kéo đổi thứ tự — tách hẳn khỏi `dragged` (thẻ) vì hai loại
  //  đi hai đường khác nhau, gộp vào một biến là mỗi nhánh phải tự đoán kiểu.
  const [draggedColumn, setDraggedColumn] = useState<number | null>(null)
  //  Chỗ thẻ ĐANG được xem trước khi kéo sang cột khác — xem `displayed` bên dưới.
  const [preview, setPreview] = useState<KanbanDropPlace | null>(null)
  //  Bật đúng MỘT khung hình ngay sau khi thẻ được dời sang cột khác. Xem
  //  `collision` bên dưới — không có nó thì bảng tự treo.
  const justChangedColumn = useRef(false)

  /**
   * Ảnh xem trước phải SỐNG THÊM một nhịp sau khi buông tay.
   *
   * Cập nhật lạc quan của TanStack Query chạy ở microtask KẾ TIẾP chứ không
   * đồng bộ trong hàm xử lý sự kiện. Xoá ảnh xem trước ngay lúc thả thì có đúng
   * một khung hình bảng vẽ lại theo dữ liệu CŨ — thẻ nháy về cột nguồn rồi mới
   * sang cột đích. Giữ nó tới khi `tasks` đổi, tức là lúc dữ liệu mới đã về.
   */
  const [justDropped, setJustDropped] = useState<{ taskId: number; place: KanbanDropPlace } | null>(null)
  const tasksAtDrop = useRef<WorkTask[] | null>(null)

  useEffect(() => {
    if (!justDropped || tasksAtDrop.current === tasks) return
    tasksAtDrop.current = null
    setJustDropped(null)
  }, [tasks, justDropped])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  //  Gom thẻ theo cột MỘT LẦN cho mỗi lần dữ liệu đổi. Lọc/sắp ngay trong JSX
  //  thì mỗi lần bảng vẽ lại là mỗi cột nhận một mảng mới, kéo theo `items` của
  //  `SortableContext` cũng mới — dnd-kit đo lại toàn bộ ô.
  const columnIds = useMemo(() => sections.map((s) => columnSortableId(s.id)), [sections])

  const byColumn = useMemo(
    () => groupBySection(sections.map((s) => s.id), tasks),
    [sections, tasks],
  )

  /**
   * Bảng ĐANG VẼ. Khi thẻ được kéo sang cột khác, nó được dời sang cột đó ngay
   * trong lúc kéo — chưa gọi API, chỉ là ảnh xem trước.
   *
   * Trước đây chỗ này vẽ một "khe chờ" gạch đứt: khe đó nằm ngoài
   * `SortableContext` nên không có hiệu ứng dồn chỗ, hiện ra và biến mất giật
   * cục, khác hẳn cảm giác kéo trong CÙNG một cột. Dời hẳn thẻ sang cột đích thì
   * cột đó nhận nó như thẻ của mình và dùng đúng hiệu ứng sortable sẵn có — hai
   * kiểu kéo nhìn như một.
   */
  const displayed = useMemo(() => {
    //  Đang kéo thì theo ảnh xem trước; vừa buông tay thì giữ nguyên chỗ vừa thả
    //  cho tới khi dữ liệu thật về (xem `justDropped`).
    const applied =
      dragged && preview ? { taskId: dragged.id, place: preview } : justDropped
    if (!applied) return byColumn
    return groupBySection(
      sections.map((s) => s.id),
      applyMove(tasks, applied.taskId, applied.place),
    )
  }, [byColumn, sections, tasks, dragged, preview, justDropped])

  /**
   * Thẻ mờ nằm lại chỉ có nghĩa khi nó CÒN Ở CỘT CŨ — lúc đó nó là chỗ trống
   * của chính nó và dnd-kit dồn chỗ quanh nó như thường.
   *
   * Đã dời sang cột khác thì giấu đi: nó với lớp phủ đang bám con trỏ là cùng
   * một việc, để cả hai thì nhìn như bảng có hai thẻ trùng tên. Vẫn chừa nguyên
   * khe (`invisible`, xem `task-card.tsx`) nên cột đích vẫn mở chỗ ra.
   */
  const hiddenGhostTaskId =
    dragged && preview && preview.sectionId !== dragged.section_id ? dragged.id : null

  //  Hạ cờ ở khung hình KẾ TIẾP, sau khi trình duyệt đã dựng lại bố cục mới.
  useEffect(() => {
    if (!justChangedColumn.current) return
    const id = requestAnimationFrame(() => {
      justChangedColumn.current = false
    })
    return () => cancelAnimationFrame(id)
  }, [preview])

  /**
   * Va chạm dùng thật. Bọc thêm một lớp quanh `kanbanCollision`: ngay sau khi
   * thẻ vừa được dời sang cột khác, GHIM đích vào chính thẻ đang kéo một khung
   * hình.
   *
   * Không ghim thì thành vòng lặp vô tận: dời thẻ sang cột B → cả hai cột dựng
   * lại → dnd-kit đo lại và tính ra một đích khác → dời tiếp → đo lại… React đếm
   * đủ số lần thì ném «Maximum update depth exceeded» và cả bảng trắng trang.
   * Một khung hình đứng yên là đủ để bố cục mới kịp ổn định.
   */
  const collision = useCallback<CollisionDetection>(
    //  Chỉ đọc hằng ở tầng module và một `ref` nên KHÔNG có phụ thuộc: giữ
    //  nguyên tham chiếu để dnd-kit khỏi tính lại va chạm ở mỗi lần vẽ.
    (args) => (justChangedColumn.current ? [{ id: args.active.id }] : kanbanCollision(args)),
    [],
  )

  function handleDragStart(event: DragStartEvent) {
    const target = parseDropTarget(event.active.id)
    if (target?.type === 'column') {
      setDraggedColumn(target.sectionId)
      return
    }
    const taskId = Number(event.active.data.current?.taskId)
    setDragged(tasks.find((t) => t.id === taskId) ?? null)
    setPreview(null)
    justChangedColumn.current = false
    //  Cú thả trước chưa kịp nhả chốt (lỗi mạng chẳng hạn) thì bỏ ở đây, đừng
    //  để một ảnh xem trước cũ đè lên cú kéo mới.
    tasksAtDrop.current = null
    setJustDropped(null)
  }

  /**
   * dnd-kit chỉ gọi lại khi Ô ĐÍCH đổi, không phải mỗi nhịp chuột — nên đặt
   * state ở đây là rẻ.
   *
   * CHỈ đổi ảnh xem trước khi thẻ sang một CỘT KHÁC với cột nó đang đứng. Trong
   * cùng một cột, dnd-kit đã tự dồn chỗ bằng `transform`; can thiệp thêm là thẻ
   * nhảy hai lần cho một cú kéo.
   */
  function handleDragOver(event: DragOverEvent) {
    //  Kéo cột thì để `SortableContext` ngang tự dồn chỗ, không cần ảnh xem trước.
    if (draggedColumn !== null || !dragged) return
    const place = resolveDropPlace(displayed, dragged.id, parseDropTarget(event.over?.id))
    if (!place) return

    const currentSection = preview?.sectionId ?? dragged.section_id
    if (place.sectionId === currentSection) return
    //  Sắp xếp khác «Tay» vẫn cho đổi cột, nhưng về đúng cột cũ thì thứ tự do
    //  trường sắp xếp quyết — không xem trước một thứ tự sẽ không được lưu (§3.4).
    if (sortLocked && place.sectionId === dragged.section_id) {
      setPreview(null)
      return
    }
    justChangedColumn.current = true
    setPreview(place)
  }

  function resetDragState() {
    setDragged(null)
    setDraggedColumn(null)
    setPreview(null)
    justChangedColumn.current = false
  }

  function handleDragEnd(event: DragEndEvent) {
    const target = parseDropTarget(event.over?.id)

    if (draggedColumn !== null) {
      const from = draggedColumn
      resetDragState()
      if (target?.type !== 'column' || target.sectionId === from) return
      const place = resolveColumnDrop(
        sections.map((s) => s.id),
        from,
        target.sectionId,
      )
      if (place) onMoveSection(from, place.beforeSectionId)
      return
    }

    const card = dragged
    const place = card ? resolveDropPlace(displayed, card.id, target) : null
    resetDragState()
    if (!card || !place) return

    //  Sắp xếp khác «Tay»: cho đổi CỘT nhưng không cho đổi thứ tự trong cột —
    //  thứ tự lúc đó do trường sắp xếp quyết, thả xong nó nhảy về chỗ cũ ngay
    //  và người dùng tưởng hỏng (§3.4).
    if (sortLocked && place.sectionId === card.section_id) return
    if (isSamePlace(byColumn, card, place)) return

    //  Ghim chỗ vừa thả lại cho tới khi dữ liệu mới về, không thì nháy một
    //  khung hình về chỗ cũ (xem `justDropped`).
    tasksAtDrop.current = tasks
    setJustDropped({ taskId: card.id, place })
    onMoveTask(card.id, place)
  }

  if (sections.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 py-16 text-center">
        <p className="text-sm text-muted-foreground">Danh sách này chưa có cột nào.</p>
        {canManage && (
          <Button variant="outline" onClick={onAddSection}>
            <Plus className="size-4" />
            Thêm cột
          </Button>
        )}
      </div>
    )
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={collision}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={resetDragState}
      measuring={MEASURING}
    >
      <div className="flex flex-1 gap-3 overflow-x-auto pb-4">
        <SortableContext items={columnIds} strategy={horizontalListSortingStrategy}>
          {sections.map((section) => (
          <KanbanColumn
            key={section.id}
            section={section}
            tasks={displayed.get(section.id) ?? []}
            tags={tags}
            labelFields={labelFields}
            fields={fields}
            canEdit={canEdit}
            canManage={canManage}
            dragDisabled={!canEdit}
            hideGhostTaskId={hiddenGhostTaskId}
            onOpenTask={onOpenTask}
            onCreateTask={onCreateTask}
            onRenameSection={onRenameSection}
            onDeleteSection={onDeleteSection}
          />
          ))}
        </SortableContext>
        {canManage && (
          <Button
            variant="ghost"
            className="h-10 w-40 shrink-0 justify-start text-muted-foreground"
            onClick={onAddSection}
          >
            <Plus className="size-4" />
            Thêm cột
          </Button>
        )}
      </div>

      {/*  `dropAnimation={null}` — TẮT hiệu ứng thả của dnd-kit.
          Mặc định lớp phủ bay từ chỗ con trỏ về đúng ô mà dnd-kit ĐO LÚC BẮT
          ĐẦU KÉO, tức là chỗ cũ ở cột cũ. Kéo trong một cột thì không thấy gì
          vì hai chỗ trùng nhau, nhưng kéo sang cột khác là thẻ bay ngược về cột
          nguồn rồi mới biến mất — đúng cái "nháy rồi quay về" người dùng thấy.
          Thẻ thật đã nằm sẵn đúng chỗ thả rồi nên không cần bay đi đâu cả. */}
      <DragOverlay dropAnimation={null}>
        {dragged && (
          <TaskCardBody
            task={dragged}
            tags={tags}
            labelFields={labelFields}
            fields={fields}
            className="cursor-grabbing shadow-xl ring-2 ring-primary/40"
          />
        )}
      </DragOverlay>
    </DndContext>
  )
}

/**
 * Va chạm cho bảng kanban.
 *
 * `closestCorners` một mình KHÔNG dùng được ở đây: cột là một vùng thả cao bằng
 * cả bảng, nên tổng khoảng cách bốn góc của nó gần như luôn thua một thẻ nhỏ ở
 * cột bên cạnh. Cột RỖNG là chỗ lộ rõ nhất — kéo thẻ vào giữa cột rỗng thì đích
 * vẫn rơi sang thẻ của cột khác, buông tay ra không có gì xảy ra.
 *
 * Cách chạy: lấy thứ nằm NGAY DƯỚI con trỏ. Con trỏ ở khoảng trống dưới thẻ cuối
 * thì `pointerWithin` vẫn trả về cột nên vẫn có đích để thả. Kéo bằng BÀN PHÍM
 * không có tọa độ con trỏ, lúc đó mới lùi về hình học.
 */
const kanbanCollision: CollisionDetection = (args) => {
  const byPointer = pointerWithin(args)
  const hits = byPointer.length > 0 ? byPointer : rectIntersection(args)
  if (hits.length === 0) return closestCorners(args)

  //  Đang kéo CẢ CỘT thì chỉ nhìn các cột khác; thân cột và thẻ bên trong đều
  //  nằm dưới con trỏ nhưng không phải đích hợp lệ.
  if (String(args.active.id).startsWith('column-')) {
    return hits.filter((c) => String(c.id).startsWith('column-'))
  }

  //  Đang kéo THẺ: bỏ vỏ cột đi, chỉ còn thẻ hoặc thân cột.
  const forCard = hits.filter((c) => !String(c.id).startsWith('column-'))
  //  Con trỏ trên một thẻ thì cả thẻ lẫn cột chứa nó cùng trúng — ưu tiên thẻ,
  //  không thì mọi cú thả đều thành "xuống cuối cột".
  const onCard = forCard.find((c) => String(c.id).startsWith('task-'))
  return onCard ? [onCard] : forCard
}
