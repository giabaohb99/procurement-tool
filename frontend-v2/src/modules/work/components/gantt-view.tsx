import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { cn } from '@/shared/utils/cn'
import { useCollapsedGroups } from '../hooks/use-collapsed-groups'
import { useGanttLinkDraft } from '../hooks/use-gantt-link-draft'
import { useGanttPaneWidth } from '../hooks/use-gantt-pane-width'
import { useListColumnWidths } from '../hooks/use-list-column-widths'
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
import {
  COLUMN_GAP,
  HEADER_HEIGHT,
  ROW_HEIGHT,
  SPLITTER_WIDTH,
} from '../utils/gantt-layout'
import { rowCenterY, taskEdges } from '../utils/gantt-links'
import { buildGanttRows, indexTaskRows } from '../utils/gantt-rows'
import { buildHeader, buildTimeline, todayLeft, type GanttZoom } from '../utils/gantt-scale'
import { groupTasksBySection } from '../utils/group-tasks'
import type { KanbanDropPlace } from '../utils/kanban-drop'
import { TITLE_COLUMN, type TaskListColumn } from '../utils/list-columns'
import { ROW_PAD_LEFT } from '../utils/list-metrics'
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

/**
 * Lưới trái Gantt chỉ có **ba cột**, gõ cứng: _Tên công việc · Phụ trách · Ngày
 * bắt đầu_ — đúng bộ của Lark (chốt với khách 31/08/2026).
 *
 * Cố ý KHÔNG lấy theo bộ «Tùy chỉnh» như khung nhìn Danh sách: ở đây mỗi cột
 * thêm vào là một khúc trục thời gian bị nuốt mất, mà người ta mở Gantt lên là
 * để nhìn cái trục ấy. Muốn xem đủ trường thì sang khung nhìn Danh sách — cùng
 * dữ liệu, cùng ô sửa tại chỗ.
 *
 * Bề rộng vẫn kéo giãn được và nhớ riêng cho Gantt (`useListColumnWidths` với
 * phạm vi `'gantt'`).
 */
const GANTT_COLUMNS: TaskListColumn[] = [
  { key: 'assignees', label: 'Phụ trách', width: 150 },
  { key: 'start', label: 'Ngày bắt đầu', width: 130 },
]

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

  const widthColumns = useMemo(() => [GANTT_TITLE_COLUMN, ...GANTT_COLUMNS], [])
  const { widths, resize, styleVars, totalWidth } = useListColumnWidths(
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

  /*  Chỉ vẽ những cột LỌT VÀO ô chứa. Cắt bằng `overflow-hidden` thì hàng tiêu
      đề `sticky` của lưới trái hỏng (xem ghi chú ở `gantt-grid.tsx`), mà bóp cột
      cho vừa thì mọi chữ trong đó cụt hết. Cột rơi ra ngoài không mất đi đâu:
      kéo rộng thanh chia là nó hiện lại.

      Cột TÊN luôn được vẽ dù ô có hẹp tới đâu — một lưới không có tên việc thì
      không còn là lưới. */
  const fitColumns = useMemo(() => {
    let x = ROW_PAD_LEFT + widths[GANTT_TITLE_COLUMN.key] + COLUMN_GAP
    const out: TaskListColumn[] = []
    for (const col of GANTT_COLUMNS) {
      const next = x + widths[col.key] + COLUMN_GAP
      if (next > paneWidth) break
      x = next
      out.push(col)
    }
    return out
  }, [widths, paneWidth])

  const gridRef = useRef<HTMLDivElement>(null)
  const areaRef = useRef<HTMLDivElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

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
      <div className="relative flex min-h-0 flex-1 flex-col">
      <div
        ref={scrollRef}
        style={styleVars}
        /*  KHÔNG bọc trong khung viền bo góc như các màn danh sách khác: Gantt
            là một mặt phẳng liền — lưới trái và trục thời gian phải đọc như MỘT
            bảng, thêm một cái hộp quanh chúng là mắt tự tách thành hai vùng rời.
            Đúng lối Lark. Chỉ còn một vạch trên để tách khỏi thanh công cụ.  */
        className={cn(
          'flex min-h-0 flex-1 overflow-auto border-t bg-card',
          //  Đang kéo một mũi tên: con trỏ hình chữ thập ở KHẮP NƠI, và không
          //  cho bôi đen chữ — rê qua tên việc mà quét xanh cả dòng thì nhìn
          //  như thao tác đã hỏng.
          draft && 'cursor-crosshair select-none',
        )}
        onPointerDownCapture={() => {
          vuaKeo.current = false
        }}
      >
        {/*  Lưới trái và thanh chia đi CHUNG một khối dính: dính riêng từng cái
             thì cả hai cùng bám `left: 0` và chồng lên nhau, mà kéo thanh chia
             thì ô lưới phình ra bên dưới nó. */}
        <div className="sticky left-0 z-30 flex border-r border-border/60 bg-card">
          <GanttGrid
            titleColumn={GANTT_TITLE_COLUMN}
            gridRef={gridRef}
            paneWidth={paneWidth}
            onResize={resize}
            groups={groups}
            sections={sections}
            columns={fitColumns}
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
          <GanttPaneSplitter width={paneWidth} maxWidth={maxPaneWidth} onResize={resizePane} />
        </div>

        <div className="relative shrink-0" style={{ width: timeline.totalWidth }}>
          <GanttTimelineHeader
            header={header}
            zoom={zoom}
            stickyLeft={paneWidth + SPLITTER_WIDTH}
          />

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
                    className="border-b border-border/60 bg-muted/20"
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

        {/*  Cụm điều khiển NẰM ĐÈ lên góc phải dải tiêu đề, đúng chỗ Lark đặt.

             Đặt đè bằng `absolute` chứ không nhét vào trong hàng tiêu đề: nhét
             vào thì nó là một ô của hàng, tức cộng thêm bề rộng vào trục và cuộn
             được quá cuối dải; mà để nguyên trong luồng cuộn thì nó trôi mất
             ngay khi người dùng kéo sang tháng khác. Đè ở ngoài khung cuộn thì
             luôn ở đúng một chỗ.  */}
        <div className="absolute top-1.5 right-3 z-40 rounded-md border bg-card/95 px-1 py-0.5 shadow-sm backdrop-blur-sm">
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
