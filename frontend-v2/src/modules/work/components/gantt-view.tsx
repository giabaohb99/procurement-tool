import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { useCollapsedGroups } from '../hooks/use-collapsed-groups'
import { useGanttLinkDraft } from '../hooks/use-gantt-link-draft'
import { useGanttGridHidden } from '../hooks/use-gantt-grid-hidden'
import { useGanttPaneWidth } from '../hooks/use-gantt-pane-width'
import { useListColumnWidths } from '../hooks/use-list-column-widths'
import { useOffscreenBars } from '../hooks/use-offscreen-bars'
import { useWheelAxisLock } from '../hooks/use-wheel-axis-lock'
import { useWorkTask } from '../hooks/use-work-board'
import type { CardFields } from '../types/view-options'
import type {
  WorkLabelField,
  WorkMember,
  WorkSection,
  WorkTask,
  WorkTaskLink,
} from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import {
  datesToSave,
  daysDragged,
  readDragData,
  snapToDayGrid,
  type GanttDragData,
} from '../utils/gantt-drag'
import { HEADER_HEIGHT, ROW_HEIGHT } from '../utils/gantt-layout'
import { rowCenterY, taskEdges } from '../utils/gantt-links'
import { buildGanttRows, indexTaskRows } from '../utils/gantt-rows'
import {
  barGeometry,
  buildHeader,
  buildTimeline,
  isMilestone,
  milestoneCenter,
  todayLeft,
  type GanttZoom,
} from '../utils/gantt-scale'
import { groupTasksBySection } from '../utils/group-tasks'
import type { KanbanDropPlace } from '../utils/kanban-drop'
import { buildListColumns, TITLE_COLUMN, type TaskListColumn } from '../utils/list-columns'
import { COLUMN_GAP, ROW_PAD_LEFT } from '../utils/list-metrics'
import { today } from '../utils/due-date'
import { priorityColorOf } from '../utils/priority-field'
import { GanttDragPreview } from './gantt-drag-preview'
import { GanttGrid } from './gantt-grid'
import { GanttLinkLayer } from './gantt-link-layer'
import { GanttPaneSplitter } from './gantt-pane-splitter'
import { GanttGroupBar, GanttTaskRow } from './gantt-row'
import { GanttTimelineControls } from './gantt-timeline-controls'
import { GanttTimelineHeader } from './gantt-timeline-header'
import type { NewTaskDraft } from './task-draft-row'
import type { TaskRowActions } from './task-list-row'

/**
 * Cột TÊN của lưới trái hẹp hơn bên Danh sách: ở đây nó phải chia màn hình với
 * trục thời gian, mà trục ấy mới là thứ người ta mở Gantt để xem.
 */
const GANTT_TITLE_COLUMN: TaskListColumn = { ...TITLE_COLUMN, width: 240, minWidth: 160 }



interface GanttViewProps extends TaskRowActions {
  listId: number
  tasks: WorkTask[]
  sections: WorkSection[]
  links: WorkTaskLink[]
  labelFields: WorkLabelField[]
  members: WorkMember[]
  /** Bộ «Tùy chỉnh» — nguồn cột DUY NHẤT, dùng chung với Bảng và Danh sách. */
  fields: CardFields
  /**
   * Trường ĐỘ ƯU TIÊN của dự án — thanh việc tô theo màu bậc ưu tiên. Vắng =
   * dự án đã xóa trường đó, thanh về màu xám.
   */
  priorityField?: WorkLabelField
  zoom: GanttZoom
  onZoomChange: (zoom: GanttZoom) => void
  canEdit: boolean
  /** Quản trị dự án — chỉ họ mới xếp lại được CỘT. */
  canManage: boolean
  /** Cho kéo xếp lại việc/cột không — tắt khi đang sắp theo tiêu chí khác «Tay». */
  dragEnabled: boolean
  defaultPicId?: number
  /**
   * Kéo xong thanh — nhận ĐÚNG những trường đổi, không phải cả cặp ngày. Luật
   * quyết định trường nào nằm ở `utils/gantt-drag.ts` (`datesToSave`).
   */
  onMoveDates: (taskId: number, values: { start_date?: string; due_date?: string }) => void
  onMoveTask: (taskId: number, place: KanbanDropPlace) => void
  onMoveSubtask: (parentId: number, subtaskId: number, beforeTaskId: number | null) => void
  onMoveSection: (sectionId: number, beforeSectionId: number | null) => void
  onAddTask: (sectionId: number | null, draft: NewTaskDraft) => void
  onCreateLink: (values: {
    predecessor_id: number
    successor_id: number
    link_type: number
  }) => void
  onChangeLinkType: (linkId: number, linkType: number) => void
  onDeleteLink: (linkId: number) => void
}

/**
 * Khung nhìn GANTT (D-05 + cụm mở rộng B-14/B-15) — khung nhìn thứ ba, cùng bộ
 * với Bảng và Danh sách.
 *
 * Bố cục bám **Lark**: lưới trái **chính là khung nhìn Danh sách** (cùng bộ cột,
 * cùng ô sửa tại chỗ, cùng ba tầng kéo thả, có cả dòng «Việc mới» cuối nhóm) ·
 * trục thời gian bên phải với hai hàng tiêu đề · hàng NHÓM có thanh tổng gom con ·
 * cột mốc hình thoi · mũi tên phụ thuộc · vạch hôm nay · kéo thanh dời lịch, kéo
 * hai mép đổi ngày.
 *
 * **Tự dựng, KHÔNG cài thư viện Gantt nào.** Ba lý do theo thứ tự cân nhắc:
 * 1. `dhtmlx-gantt` bản Standard là **GPLv2**. Dùng nội bộ không kích hoạt nghĩa
 *    vụ mở mã, nhưng rước một giấy phép lây lan vào repo để đổi lấy một biểu đồ
 *    thanh ngang là không đáng — bản Pro thì trả phí.
 * 2. Thư viện Gantt nào cũng mang CSS riêng, không biết gì về token màu và chế
 *    độ nền của hệ; chỉnh cho khớp còn tốn hơn tự vẽ.
 * 3. Lưới trái phải là CHÍNH các dòng của khung nhìn Danh sách. Không thư viện
 *    nào nhận vào chỗ đó một cây React của mình mà không phải vá.
 *
 * ⚠️ **Hai bên phải sinh ra ĐÚNG cùng một dãy hàng**: `TaskGroupsBoard` vẽ bên
 * trái, `buildGanttRows` dựng lại y hệt cho bên phải. Vì vậy mọi thứ đổi số dòng
 * (thu/mở nhóm · bung việc con) đều là state của CHÍNH màn này, không giấu bên
 * trong cụm nhóm.
 *
 * **Bốn loại kéo, ba cơ chế khác nhau — cố ý:**
 * - Kéo NGÀY (cả thanh / hai mép) → dnd-kit, `DragOverlay`, chỉ lớp phủ vẽ lại.
 * - Kéo VIỆC / VIỆC CON / CỘT ở lưới trái → dnd-kit, nhưng là `DndContext` RIÊNG
 *   nằm trong `TaskGroupsBoard`. Hai context cạnh nhau không biết nhau, nên
 *   không có chuyện `onDragEnd` của bên này nhận nhầm món của bên kia.
 * - Kéo NỐI PHỤ THUỘC → `pointerdown` thô (`useGanttLinkDraft`): cho nó đi chung
 *   một `DndContext` thì `onDragEnd` phải đoán cú thả vừa rồi mang nghĩa gì,
 *   đoán nhầm là **ghi đè ngày của một việc thật**.
 * - Kéo GIÃN CỘT / THANH CHIA → ghi thẳng vào biến CSS, không qua state.
 */
export function GanttView({
  listId,
  tasks,
  sections,
  links,
  labelFields,
  members,
  fields,
  priorityField,
  zoom,
  onZoomChange,
  canEdit,
  canManage,
  dragEnabled,
  defaultPicId,
  onMoveDates,
  onMoveTask,
  onMoveSubtask,
  onMoveSection,
  onAddTask,
  onCreateLink,
  onChangeLinkType,
  onDeleteLink,
  ...rowActions
}: GanttViewProps) {
  const homNay = today()
  const timeline = useMemo(() => buildTimeline(tasks, zoom, homNay), [tasks, zoom, homNay])
  const header = useMemo(() => buildHeader(timeline, zoom, homNay), [timeline, zoom, homNay])

  const { isCollapsed, toggle } = useCollapsedGroups(listId)
  const groups = useMemo(() => groupTasksBySection(tasks, sections), [tasks, sections])

  /*  Việc đang bung việc con. State nằm ở ĐÂY chứ không trong cụm nhóm: trục
      thời gian phải biết chính xác đang có bao nhiêu dòng để vẽ bấy nhiêu hàng.

      Việc con nạp lười qua đúng query của panel chi tiết (`useWorkTask`), nên
      lưới trái bung ra và bên này vẽ thanh đều đọc CÙNG một bản trong cache —
      không tốn thêm lượt gọi nào.  */
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null)
  //  Cột đang bị kéo — lưới trái thu nó lại còn mỗi dải tiêu đề, bên này phải
  //  thu theo, xem `BuildGanttRowsOptions.draggingSectionId`.
  const [draggingSectionId, setDraggingSectionId] = useState<number | null>(null)
  const { data: expandedDetail } = useWorkTask(expandedTaskId ?? undefined)
  const subtasks = useMemo(() => expandedDetail?.subtasks ?? [], [expandedDetail?.subtasks])

  const rows = useMemo(
    () =>
      buildGanttRows(groups, {
        isCollapsed,
        isDone: (t) => t.status === WORK_TASK_STATUS.DONE,
        expandedTaskId,
        subtasks,
        showDraftRow: canEdit,
        draggingSectionId,
      }),
    [groups, isCollapsed, expandedTaskId, subtasks, canEdit, draggingSectionId],
  )
  const taskRows = useMemo(() => indexTaskRows(rows), [rows])
  const taskById = useMemo(() => new Map(tasks.map((t) => [t.id, t])), [tasks])

  /*  Cột lấy ĐỦ từ bộ «Tùy chỉnh» y như khung nhìn Danh sách — nhưng ô chứa
      lưới thì hẹp (mặc định vừa khoảng ba cột), nên lưới TỰ CUỘN NGANG và ô tên
      ghim lại ở mép trái. Trước đây bản này gõ cứng ba cột và cắt phần thừa;
      khách chốt 31/08/2026 là phải hiện đủ, chỉ mặc định thấy ba.  */
  const columns = useMemo(() => buildListColumns(fields, labelFields), [fields, labelFields])
  const widthColumns = useMemo(() => [GANTT_TITLE_COLUMN, ...columns], [columns])
  const { resize, styleVars, totalWidth } = useListColumnWidths(
    listId,
    widthColumns,
    'gantt',
  )
  //  Bề rộng NỘI DUNG của lưới (mọi cột + lề + khe giữa các ô) — chặn trên của
  //  thanh chia: kéo rộng hơn thế chỉ chừa thêm khoảng trắng.
  const gridContentWidth = ROW_PAD_LEFT + totalWidth + widthColumns.length * COLUMN_GAP + 8
  const {
    width: paneWidth,
    maxWidth: maxPaneWidth,
    resize: resizePane,
  } = useGanttPaneWidth(listId, gridContentWidth)
  const { hidden: gridHidden, toggle: toggleGrid } = useGanttGridHidden(listId)

  const gridRef = useRef<HTMLDivElement>(null)
  const areaRef = useRef<HTMLDivElement>(null)
  /** Khung cuộn của TRỤC THỜI GIAN — cuộn cả hai chiều, và là bên chủ động. */
  const scrollRef = useRef<HTMLDivElement>(null)
  /** Khung cuộn của LƯỚI TRÁI — chỉ cuộn ngang; chiều dọc do bên kia lái. */
  const gridPaneRef = useRef<HTMLDivElement>(null)

  /*  Hai bên là HAI khung cuộn riêng (Lark cũng vậy) chứ không còn một khung
      chung. Đổi vì lưới trái phải tự cuộn ngang để xem hết cột, mà một khung
      chung thì cuộn ngang là kéo luôn cả trục thời gian đi.

      Cái giá phải trả: chiều DỌC phải tự đồng bộ. Trục thời gian là bên chủ
      động (nó có thanh cuộn dọc thật); lưới trái để `overflow-y-hidden` và được
      lái bằng `scrollTop` — `scrollTop` vẫn gán được trên phần tử ẩn tràn, nên
      không cần thanh cuộn thứ hai chạy song song trông rất rối.

      Lăn chuột khi con trỏ đang ở TRÊN lưới trái thì chuyển thẳng sang bên kia,
      nếu không thì rê chuột vào vùng tên việc là lăn không ăn gì.  */
  function syncGridScroll() {
    const grid = gridPaneRef.current
    const box = scrollRef.current
    if (grid && box) grid.scrollTop = box.scrollTop
  }

  /*  Đánh dấu "lưới trái đã cuộn ngang" để cột TÊN ghim hiện bóng đổ ở mép phải
      (xem `utils/pinned-title-class.ts`). Chưa cuộn thì không đổ bóng — sau ô
      tên chẳng có gì, đổ bóng lên nền trơn là bịa ra một tầng lớp không có thật.

      Gán thẳng thuộc tính DOM chứ KHÔNG nuôi một `useState`: cờ này chỉ để vẽ,
      mà `onScroll` bắn hàng chục nhịp mỗi cú lăn — cho nó chạy qua state là mỗi
      nhịp vẽ lại toàn bộ Gantt (hàng trăm ô lưới ngày) chỉ để bật một cái bóng.  */
  function markGridScrolledX(e: React.UIEvent<HTMLDivElement>) {
    e.currentTarget.toggleAttribute('data-scrolled-x', e.currentTarget.scrollLeft > 0)
  }

  /*  KHÓA TRỤC khi lăn (xem `useWheelAxisLock`). Trục thời gian cuộn được cả hai
      chiều, mà trackpad thì không có cử chỉ "thuần ngang" — vuốt sang tháng sau
      là biểu đồ trôi dọc theo, mất luôn hàng đang nhìn.  */
  const applyTimelineWheel = useCallback((axis: 'x' | 'y', delta: number) => {
    const box = scrollRef.current
    if (!box) return
    if (axis === 'x') box.scrollLeft += delta
    else box.scrollTop += delta
  }, [])

  /*  Lăn khi con trỏ ở trên LƯỚI TRÁI: chiều ngang là của chính lưới, còn chiều
      dọc chuyển thẳng sang trục thời gian — lưới `overflow-y-hidden` nên tự nó
      không cuộn dọc được, không chuyển thì rê vào vùng tên việc là lăn không ăn
      gì. `syncGridScroll` sẽ kéo `scrollTop` của lưới theo sau.  */
  const applyGridWheel = useCallback((axis: 'x' | 'y', delta: number) => {
    const grid = gridPaneRef.current
    const box = scrollRef.current
    if (axis === 'x') {
      if (grid) grid.scrollLeft += delta
      return
    }
    if (box) box.scrollTop += delta
  }, [])

  useWheelAxisLock(scrollRef, applyTimelineWheel)
  useWheelAxisLock(gridPaneRef, applyGridWheel)

  /*  Việc nào có thanh đã trôi khỏi tầm nhìn thì hàng của nó mọc một chip mũi
      tên ở mép khung (`OffscreenJump`) — trục dài hai năm nên kéo vài nhịp là
      biểu đồ chỉ còn lưới trống, không biết việc nằm bên nào.  */
  const offscreenBars = useOffscreenBars(scrollRef, rows)

  /*  Bề rộng thanh cuộn dọc của trục — cụm điều khiển nằm NGOÀI khung cuộn nên
      phải tự chừa chỗ, không thì nó đè lên thanh cuộn. macOS đo ra 0 (thanh cuộn
      phủ lên nội dung), Windows/Linux ra ~15. Đo lại khi số dòng đổi vì đó là
      lúc trục chuyển giữa có và không có thanh cuộn dọc.  */
  const [scrollbarWidth, setScrollbarWidth] = useState(0)
  useLayoutEffect(() => {
    const box = scrollRef.current
    if (box) setScrollbarWidth(box.offsetWidth - box.clientWidth)
  }, [rows.length, paneWidth])

  /*  Đặt lịch cho một việc CHƯA có ngày, bằng cách kéo ngay trên hàng trống của
      nó (xem `GanttScheduleLayer`). CỘT MỐC chỉ nhận MỘT đầu ngày — nó là một
      thời điểm chứ không phải một quãng, ghi cả `start_date` cho nó là bịa ra
      một dữ liệu mà panel chi tiết còn chẳng có ô để hiện.  */
  const scheduleTask = useCallback(
    (taskId: number, from: string, to: string) => {
      const task = taskById.get(taskId)
      if (!task) return
      onMoveDates(taskId, isMilestone(task) ? { due_date: to } : { start_date: from, due_date: to })
    },
    [taskById, onMoveDates],
  )

  const jumpToTask = useCallback(
    (taskId: number) => {
      const box = scrollRef.current
      const task = taskById.get(taskId)
      if (!box || !task) return

      //  Cột mốc là hình thoi tại MỘT ngày, không có `barGeometry`.
      const left = isMilestone(task)
        ? (milestoneCenter(task, timeline) ?? null)
        : (barGeometry(task, timeline)?.left ?? null)
      if (left === null) return

      //  Đặt thanh ở khoảng một phần ba bên trái, cùng chỗ nút «Hôm nay» đưa
      //  vạch hôm nay về: còn thấy được cả quãng trước lẫn quãng sau của nó.
      box.scrollTo({ left: Math.max(0, left - box.clientWidth / 3), behavior: 'smooth' })
    },
    [taskById, timeline],
  )

  /*  Mở ra là nhìn thấy HÔM NAY luôn, đặt ở khoảng một phần ba bên trái để còn
      thấy cả việc vừa qua lẫn việc sắp tới.

      Chỉ canh lại MỘT LẦN cho mỗi mức phóng, canh bằng cờ chứ không bằng mảng
      phụ thuộc. Hai lý do, mỗi cái là một lỗi thật:
      - Phụ thuộc `timeline` thì mỗi lần sửa một việc là dải dựng lại và thanh
        cuộn giật về chỗ hôm nay, cuốn phăng chỗ người dùng đang xem.
      - Phụ thuộc `[zoom]` thì lúc mới mở, dữ liệu chưa về nên khung cuộn chưa
        tồn tại; tới lúc nó hiện ra thì `zoom` không đổi nên hiệu ứng không chạy
        lại lần nào nữa, và biểu đồ nằm mãi ở đầu dải.  */
  const daCuonCho = useRef('')
  useEffect(() => {
    const box = scrollRef.current
    if (!box || daCuonCho.current === zoom) return
    const x = todayLeft(timeline, homNay)
    if (x === null) return
    daCuonCho.current = zoom
    box.scrollLeft = Math.max(0, x - box.clientWidth / 3)
  })

  /** Đưa vạch hôm nay về khoảng một phần ba bên trái — cùng chỗ với lúc mở màn. */
  function scrollToToday() {
    const box = scrollRef.current
    const x = todayLeft(timeline, homNay)
    if (!box || x === null) return
    box.scrollTo({ left: Math.max(0, x - box.clientWidth / 3), behavior: 'smooth' })
  }

  /*  Lùi/tiến MỘT TRANG = 80% bề rộng đang nhìn, không phải trọn màn: chừa lại
      một khúc quen mắt ở mép để người dùng biết mình vừa nhảy tới đâu.  */
  function stepTimeline(direction: -1 | 1) {
    const box = scrollRef.current
    if (!box) return
    box.scrollBy({ left: direction * box.clientWidth * 0.8, behavior: 'smooth' })
  }

  const [keo, setKeo] = useState<GanttDragData | null>(null)

  //  Sau một cú kéo thật, trình duyệt vẫn bắn `click` lên chính thanh vừa kéo —
  //  không chặn thì kéo xong là panel chi tiết bật ra. Cờ bật ở `onDragStart` và
  //  được xóa ở `pointerdown` của lần bấm SAU, nên không bao giờ kẹt lại (thả
  //  chuột ngoài vùng thanh thì không có `click` nào để tự xóa).
  const vuaKeo = useRef(false)

  //  Ngưỡng 4px chứ không 6px như kanban: ở mức phóng Tháng một ngày chỉ rộng
  //  4px, gác 6px là nuốt luôn nấc dịch chuyển đầu tiên.
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }))
  const snap = useMemo(() => snapToDayGrid(timeline.dayWidth), [timeline.dayWidth])

  const handleCreateLink = useCallback(
    (values: { predecessor_id: number; successor_id: number; link_type: number }) =>
      onCreateLink(values),
    [onCreateLink],
  )
  const { draft, start: startLink } = useGanttLinkDraft({ areaRef, onCreate: handleCreateLink })

  function handleDragStart(e: DragStartEvent) {
    const data = readDragData(e.active.data.current)
    if (!data) return
    vuaKeo.current = true
    setKeo(data)
  }

  function handleDragEnd(e: DragEndEvent) {
    setKeo(null)
    const data = readDragData(e.active.data.current)
    if (!data) return
    const values = datesToSave(data.task, data.kind, daysDragged(e.delta.x, timeline.dayWidth))
    if (values) onMoveDates(data.task.id, values)
  }

  function openTask(taskId: number) {
    if (vuaKeo.current) return
    rowActions.onOpenTask(taskId)
  }

  if (tasks.length === 0) {
    return (
      <p className="py-16 text-center text-sm text-muted-foreground">
        Không có công việc nào khớp bộ lọc đang chọn.
      </p>
    )
  }

  const vachHomNay = todayLeft(timeline, homNay)
  const bodyHeight = rows.length * ROW_HEIGHT

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setKeo(null)}
    >
      <div
        style={styleVars}
        /*  KHÔNG viền, không bo góc, không vạch trên, và nền TRÙNG nền trang
            (`bg-canvas`) chứ không phải một tấm thẻ trắng: Gantt là một mặt
            phẳng liền — thêm bất kỳ nét kẻ hay mảng trắng nào quanh nó là mắt tự
            tách thành hai vùng rời. Đúng lối Lark.  */
        className={cn(
          'relative flex min-h-0 flex-1 bg-canvas',
          //  Đang kéo một mũi tên: con trỏ hình chữ thập ở KHẮP NƠI, và không
          //  cho bôi đen chữ — rê qua tên việc mà quét xanh cả dòng thì nhìn
          //  như thao tác đã hỏng.
          draft && 'cursor-crosshair select-none',
        )}
        onPointerDownCapture={() => {
          vuaKeo.current = false
        }}
      >
        {/*  LƯỚI TRÁI — khung cuộn RIÊNG, chỉ cuộn ngang; chiều dọc do trục thời
             gian lái (xem `syncGridScroll`). Lăn chuột khi con trỏ đang ở trên
             lưới thì chuyển thẳng sang bên kia, không thì rê vào vùng tên việc
             là lăn không ăn gì.

             Ẩn lưới thì GỠ HẲN khỏi cây, không phải `w-0` hay `hidden`: giữ lại
             thì `syncGridScroll` vẫn gán `scrollTop` mỗi nhịp cuộn cho một thứ
             không ai thấy, và `IntersectionObserver` của chip «cuộn về thanh»
             vẫn phải theo dõi từng thanh trong đó.  */}
        {!gridHidden && (
        <div
          ref={gridPaneRef}
          /*  ⚠️ ĐỪNG thêm `scroll-snap` vào đây. Đã thử cho cuộn ngang bám mép
              cột để không bao giờ thấy nửa viên chip ở sát ô tên ghim; khách bác
              ngay 31/08/2026 — *"dừng làm snap ngang làm dị khó chịu á"*. Cuộn
              phải trôi tự do.  */
          //  KHÔNG `border-r` ở đây: thanh chia ngay bên phải đã là nét 1px rồi,
          //  để cả hai là hai vạch dọc sát nhau.
          className="shrink-0 overflow-x-auto overflow-y-hidden"
          style={{ width: paneWidth }}
          onScroll={markGridScrolledX}
        >
          <GanttGrid
            titleColumn={GANTT_TITLE_COLUMN}
            gridRef={gridRef}
            contentWidth={gridContentWidth}
            onResize={resize}
            groups={groups}
            sections={sections}
            columns={columns}
            stickyTitle
            fields={fields}
            labelFields={labelFields}
            members={members}
            canEdit={canEdit}
            canManage={canManage}
            defaultPicId={defaultPicId}
            dragEnabled={dragEnabled}
            isCollapsed={isCollapsed}
            onToggleCollapse={toggle}
            expandedTaskId={expandedTaskId}
            onToggleExpand={(taskId) =>
              setExpandedTaskId((prev) => (prev === taskId ? null : taskId))
            }
            rowHeight={ROW_HEIGHT}
            onDraggingSectionChange={setDraggingSectionId}
            onMoveTask={onMoveTask}
            onMoveSubtask={onMoveSubtask}
            onMoveSection={onMoveSection}
            onAddTask={onAddTask}
            {...rowActions}
            onOpenTask={openTask}
          />
        </div>
        )}

        {!gridHidden && (
          <GanttPaneSplitter width={paneWidth} maxWidth={maxPaneWidth} onResize={resizePane} />
        )}

        {/*  TRỤC THỜI GIAN — khung cuộn CHÍNH: cuộn cả hai chiều và lái chiều
             dọc của lưới trái. */}
        <div ref={scrollRef} onScroll={syncGridScroll} className="min-w-0 flex-1 overflow-auto">
        <div className="relative" style={{ width: timeline.totalWidth }}>
          <GanttTimelineHeader header={header} zoom={zoom} leadInset={gridHidden ? 28 : 0} />

          {/* Lưới nền — vẽ theo Ô của hàng tiêu đề dưới, không phải theo từng
              ngày: ở mức Tháng một dải hai năm là hơn 700 ngày, tức 700 nút DOM
              cho một tấm lưới mà mắt chỉ thấy mỗi vạch tháng. */}
          <div className="absolute inset-x-0 bottom-0 flex" style={{ top: HEADER_HEIGHT }}>
            {header.bottom.map((cell) => (
              <div
                key={cell.key}
                style={{ width: cell.width }}
                className={cn(
                  'h-full shrink-0 border-r border-border/60',
                  //  Cuối tuần tô nhạt hơn hẳn ngày làm việc — nhìn phát ra ngay
                  //  quãng nào là ngày nghỉ, khỏi dò dòng «T7 · CN» ở tiêu đề.
                  //  Đặt TRƯỚC `isNow` để cột hôm nay vẫn thắng khi hôm nay rơi
                  //  vào thứ Bảy hay Chủ nhật.
                  cell.isWeekend && 'bg-muted-foreground/[0.07]',
                  cell.isNow && 'bg-primary/5',
                )}
              />
            ))}
          </div>

          <div ref={areaRef} className="relative" style={{ minHeight: bodyHeight }}>
            {/* Vạch HÔM NAY chạy suốt mọi hàng — mốc đọc chính của cả biểu đồ. */}
            {vachHomNay !== null && (
              <span
                aria-hidden
                className="pointer-events-none absolute top-0 z-20 w-px bg-primary/70"
                style={{ left: vachHomNay, height: bodyHeight }}
              />
            )}

            {rows.map((row) => {
              if (row.kind === 'group') {
                return <GanttGroupBar key={row.key} row={row} timeline={timeline} />
              }
              if (row.kind === 'draft') {
                //  Hàng đối diện dòng «Việc mới» — trống, chỉ giữ chỗ cho hai
                //  bên khỏi lệch nhau.
                return (
                  <div
                    key={row.key}
                    style={{ height: ROW_HEIGHT }}
                    className="bg-muted/20"
                  />
                )
              }
              return (
                <GanttTaskRow
                  key={row.key}
                  task={row.task}
                  isSubtask={row.isSubtask}
                  timeline={timeline}
                  barColor={priorityColorOf(row.task, priorityField)}
                  canEdit={canEdit}
                  offscreen={offscreenBars.get(row.task.id) ?? null}
                  onJumpToTask={jumpToTask}
                  onSchedule={scheduleTask}
                  onOpenTask={openTask}
                  onStartLink={startLink}
                  linkTargetId={draft?.targetTaskId ?? null}
                  linking={draft !== null}
                />
              )
            })}

            <GanttLinkLayer
              links={links}
              rows={rows}
              taskRows={taskRows}
              tasks={taskById}
              timeline={timeline}
              canEdit={canEdit}
              onChangeType={onChangeLinkType}
              onDelete={onDeleteLink}
            />

            {draft && (
              <LinkDraftLine
                draft={draft}
                timeline={timeline}
                taskRows={taskRows}
                tasks={taskById}
              />
            )}
          </div>
        </div>
        </div>

        {/*  Nút ẨN / HIỆN lưới trái — luôn đứng ngay CẠNH NHÃN THÁNG, đúng chỗ
             Lark đặt: lưới đang hiện thì nó ở góc trên bên phải dải tiêu đề lưới
             (sát thanh chia, tức sát nhãn tháng bên kia); lưới ẩn rồi thì nó lùi
             về góc trái của chính dải tiêu đề trục.

             Đặt ở TẦNG NÀY chứ không nhét vào `GanttGrid`: bên trong lưới, một
             `absolute right-2` sẽ bám mép NỘI DUNG (rộng `gridContentWidth`) chứ
             không bám mép nhìn thấy, nên cuộn ngang một cái là nút trôi mất. Ở
             đây thì `paneWidth` là con số thật của ô chứa, tính thẳng ra được.  */}
        <Button
          variant="ghost"
          size="icon-sm"
          title={gridHidden ? 'Hiện danh sách công việc' : 'Ẩn danh sách công việc'}
          aria-label={gridHidden ? 'Hiện danh sách công việc' : 'Ẩn danh sách công việc'}
          className="absolute top-1.5 z-40 text-muted-foreground hover:text-foreground"
          style={{ left: gridHidden ? 6 : paneWidth - 34 }}
          onClick={toggleGrid}
        >
          {gridHidden ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
        </Button>

        {/*  Cụm điều khiển NẰM ĐÈ lên góc phải dải tiêu đề, đúng chỗ Lark đặt.

             Đặt đè bằng `absolute` chứ không nhét vào trong hàng tiêu đề: nhét
             vào thì nó là một ô của hàng, tức cộng thêm bề rộng vào trục và cuộn
             được quá cuối dải; mà để nguyên trong luồng cuộn thì nó trôi mất
             ngay khi người dùng kéo sang tháng khác. Đè ở ngoài khung cuộn thì
             luôn ở đúng một chỗ.  */}
        {/*  Không hộp trắng, không viền, không đổ bóng — cụm này thuộc về chính
             dải tiêu đề chứ không phải một tấm thẻ nổi lên trên nó (Lark cũng
             vậy).

             ⚠️ Nhưng PHẢI có nền `bg-muted` (đúng màu dải tiêu đề, nên nhìn như
             không có nền): để trong suốt thì nhãn tháng cuộn ngang chui xuống
             dưới và chồng chữ lên nhau — đo được «Tháng 9/2026» đè lên «Hôm nay»
             thành một mớ không đọc nổi.  */}
        {/*  ⚠️ Nền phải phủ KÍN cả ô tiêu đề tháng, không chừa khe nào. Bản trước
             đặt `top-1.5 right-3` cho thoáng, thành ra hở 6px trên và 12px phải —
             đúng hai khe ấy nhãn tháng cuộn ngang lòi ra một mẩu («/2» của "Tháng
             9/2027") nhìn như rác. Nay hộp bám `top-0`, cao đúng một hàng tiêu
             đề, còn khoảng thở chuyển vào `pr-3` (đệm TRONG hộp) nên nút vẫn
             không dính mép mà nền thì liền một mảnh.

             `right` chừa đúng bề rộng thanh cuộn dọc: cụm này nằm NGOÀI khung
             cuộn nên `right-0` sẽ đè lên thanh cuộn ở những nền tảng có thanh
             cuộn chiếm chỗ thật (Windows/Linux). macOS đo ra 0 nên không thấy
             gì, đúng kiểu lỗi chỉ nổ ở máy người dùng.  */}
        <div
          className="absolute top-0 z-40 flex items-center bg-muted pr-3 pl-2"
          style={{ right: scrollbarWidth, height: ROW_HEIGHT }}
        >
          <GanttTimelineControls
            zoom={zoom}
            onZoomChange={onZoomChange}
            onStep={stepTimeline}
            onToday={scrollToToday}
          />
        </div>
      </div>

      {/*  Không dùng hiệu ứng thả về chỗ cũ: ngày nhảy theo nấc rời rạc nên lớp
          phủ bay về sẽ trượt qua chỗ thanh vừa được đặt, nhìn như thả hụt. */}
      <DragOverlay modifiers={[snap]} dropAnimation={null}>
        {keo && (
          <GanttDragPreview
            data={keo}
            timeline={timeline}
            barColor={priorityColorOf(keo.task, priorityField)}
          />
        )}
      </DragOverlay>
    </DndContext>
  )
}

/**
 * Nét đứt bám con trỏ trong lúc kéo tạo phụ thuộc — không có nó thì người dùng
 * đang kéo một thứ vô hình và chỉ biết mình vừa làm gì sau khi thả tay.
 */
function LinkDraftLine({
  draft,
  timeline,
  taskRows,
  tasks,
}: {
  draft: NonNullable<ReturnType<typeof useGanttLinkDraft>['draft']>
  timeline: ReturnType<typeof buildTimeline>
  taskRows: Map<number, number>
  tasks: Map<number, WorkTask>
}) {
  const task = tasks.get(draft.fromTaskId)
  const row = taskRows.get(draft.fromTaskId)
  if (!task || row === undefined) return null

  const edges = taskEdges(task, timeline)
  if (!edges) return null
  const x = draft.fromSide === 'end' ? edges.right : edges.left

  return (
    <svg className="pointer-events-none absolute inset-0 z-30 overflow-visible" aria-hidden>
      <line
        x1={x}
        y1={rowCenterY(row)}
        x2={draft.x}
        y2={draft.y}
        strokeDasharray="4 3"
        className="stroke-primary"
        strokeWidth={1.5}
      />
    </svg>
  )
}
