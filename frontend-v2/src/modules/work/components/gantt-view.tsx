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
import { COLUMN_GAP, GRID_PAD_LEFT, HEADER_HEIGHT, ROW_HEIGHT } from '../utils/gantt-layout'
import { rowCenterY, taskEdges } from '../utils/gantt-links'
import { buildGanttRows, indexTaskRows } from '../utils/gantt-rows'
import {
  buildHeader,
  buildTimeline,
  todayLeft,
  type GanttZoom,
} from '../utils/gantt-scale'
import { groupTasksBySection } from '../utils/group-tasks'
import { buildListColumns, TITLE_COLUMN } from '../utils/list-columns'
import { today } from '../utils/due-date'
import { priorityColorOf } from '../utils/priority-field'
import { GanttDragPreview } from './gantt-drag-preview'
import { GanttGrid } from './gantt-grid'
import { GanttLinkLayer } from './gantt-link-layer'
import { GanttPaneSplitter } from './gantt-pane-splitter'
import { GanttGroupBar, GanttTaskRow } from './gantt-row'
import { GanttTimelineHeader } from './gantt-timeline-header'
import type { TaskRowActions } from './task-list-row'

/**
 * Cột TÊN của lưới trái hẹp hơn bên Danh sách: ở đây nó phải chia màn hình với
 * trục thời gian, mà trục ấy mới là thứ người ta mở Gantt để xem.
 */
const GANTT_TITLE_COLUMN = { ...TITLE_COLUMN, width: 240, minWidth: 160 }

/** Những thao tác sửa tại chỗ mà lưới trái của Gantt dùng chung với Danh sách. */
export type GanttRowActions = Pick<
  TaskRowActions,
  'onOpenTask' | 'onSetAssignees' | 'onSetDue' | 'onSetStart' | 'onSetStatus' | 'onSetLabel'
>

interface GanttViewProps extends GanttRowActions {
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
  canEdit: boolean
  /**
   * Kéo xong thanh — nhận ĐÚNG những trường đổi, không phải cả cặp ngày. Luật
   * quyết định trường nào nằm ở `utils/gantt-drag.ts` (`datesToSave`).
   */
  onMoveDates: (taskId: number, values: { start_date?: string; due_date?: string }) => void
  onCreateLink: (values: {
    predecessor_id: number
    successor_id: number
    link_type: number
  }) => void
  onDeleteLink: (linkId: number) => void
}

/**
 * Khung nhìn GANTT (D-05 + cụm mở rộng B-14/B-15) — khung nhìn thứ ba, cùng bộ
 * với Bảng và Danh sách.
 *
 * Bố cục bám **Lark**: lưới cột bên trái dùng CHUNG bộ cột với khung nhìn Danh
 * sách · trục thời gian bên phải với hai hàng tiêu đề · hàng NHÓM có thanh tổng
 * gom con · cột mốc vẽ hình thoi · mũi tên phụ thuộc nối việc trước–sau · vạch
 * hôm nay · kéo thanh dời lịch, kéo hai mép đổi ngày.
 *
 * **Tự dựng, KHÔNG cài thư viện Gantt nào.** Ba lý do theo thứ tự cân nhắc:
 * 1. `dhtmlx-gantt` bản Standard là **GPLv2**. Dùng nội bộ không kích hoạt nghĩa
 *    vụ mở mã, nhưng rước một giấy phép lây lan vào repo để đổi lấy một biểu đồ
 *    thanh ngang là không đáng — bản Pro thì trả phí.
 * 2. Thư viện Gantt nào cũng mang CSS riêng, không biết gì về token màu và chế
 *    độ nền của hệ; chỉnh cho khớp còn tốn hơn tự vẽ.
 * 3. Lưới trái phải là CHÍNH các ô sửa được của khung nhìn Danh sách. Không thư
 *    viện nào nhận vào chỗ đó một cây React của mình mà không phải vá.
 *
 * **Ba loại kéo, ba cơ chế khác nhau — cố ý:**
 * - Kéo NGÀY (cả thanh / hai mép) → dnd-kit, cùng bộ với kanban; vị trí tạm nằm
 *   ở `DragOverlay` nên chỉ mình lớp phủ vẽ lại theo con trỏ.
 * - Kéo NỐI PHỤ THUỘC → `pointerdown` thô (`useGanttLinkDraft`): cho nó đi chung
 *   `DndContext` thì `onDragEnd` phải đoán cú thả vừa rồi mang nghĩa gì, đoán
 *   nhầm là ghi đè ngày của một việc thật.
 * - Kéo GIÃN CỘT → `ListColumnResizer`, ghi thẳng vào biến CSS, không qua state.
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
  canEdit,
  onMoveDates,
  onCreateLink,
  onDeleteLink,
  ...rowActions
}: GanttViewProps) {
  const homNay = today()
  const timeline = useMemo(() => buildTimeline(tasks, zoom, homNay), [tasks, zoom, homNay])
  const header = useMemo(() => buildHeader(timeline, zoom, homNay), [timeline, zoom, homNay])

  const { isCollapsed, toggle } = useCollapsedGroups(listId)
  const groups = useMemo(() => groupTasksBySection(tasks, sections), [tasks, sections])
  const rows = useMemo(
    () => buildGanttRows(groups, isCollapsed, (t) => t.status === WORK_TASK_STATUS.DONE),
    [groups, isCollapsed],
  )
  const taskRows = useMemo(() => indexTaskRows(rows), [rows])
  const taskById = useMemo(() => new Map(tasks.map((t) => [t.id, t])), [tasks])

  const columns = useMemo(() => buildListColumns(fields, labelFields), [fields, labelFields])
  const widthColumns = useMemo(() => [GANTT_TITLE_COLUMN, ...columns], [columns])
  const { widths, resize, styleVars, totalWidth } = useListColumnWidths(listId, widthColumns, 'gantt')
  //  Bề rộng NỘI DUNG của lưới (mọi cột + lề + khe giữa các ô) — chặn trên của
  //  thanh chia: kéo rộng hơn thế chỉ chừa thêm khoảng trắng.
  const gridContentWidth = GRID_PAD_LEFT + totalWidth + widthColumns.length * COLUMN_GAP + 8
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
    let x = GRID_PAD_LEFT + widths[GANTT_TITLE_COLUMN.key] + COLUMN_GAP
    const out: typeof columns = []
    for (const col of columns) {
      const next = x + widths[col.key] + COLUMN_GAP
      if (next > paneWidth) break
      x = next
      out.push(col)
    }
    return out
  }, [columns, widths, paneWidth])

  const gridRef = useRef<HTMLDivElement>(null)
  const areaRef = useRef<HTMLDivElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  /*  Mở ra là nhìn thấy HÔM NAY luôn, đặt ở khoảng một phần ba bên trái để còn
      thấy cả việc vừa qua lẫn việc sắp tới.

      Dự án hai năm ở mức Ngày rộng cả chục nghìn pixel, mà khung luôn mở ở mép
      TRÁI — tức đầu dải, thường là quá khứ xa. Người dùng phải kéo ngang một
      quãng dài mới thấy phần đang chạy, và chẳng có gì mách họ kéo về đâu.

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
        ref={scrollRef}
        style={styleVars}
        className={cn(
          'flex min-h-0 flex-1 overflow-auto rounded-lg border bg-card',
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
        <div className="sticky left-0 z-30 flex border-r bg-card">
          <GanttGrid
            rows={rows}
            columns={fitColumns}
            titleColumn={GANTT_TITLE_COLUMN}
            labelFields={labelFields}
            members={members}
            canEdit={canEdit}
            gridRef={gridRef}
            paneWidth={paneWidth}
            onResize={resize}
            onToggleGroup={toggle}
            {...rowActions}
            onOpenTask={openTask}
          />
          <GanttPaneSplitter width={paneWidth} maxWidth={maxPaneWidth} onResize={resizePane} />
        </div>

        <div className="relative shrink-0" style={{ width: timeline.totalWidth }}>
          <GanttTimelineHeader header={header} zoom={zoom} />

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

            {rows.map((row) =>
              row.kind === 'group' ? (
                <GanttGroupBar key={row.key} row={row} timeline={timeline} />
              ) : (
                <GanttTaskRow
                  key={row.key}
                  task={row.task}
                  timeline={timeline}
                  barColor={priorityColorOf(row.task, priorityField)}
                  canEdit={canEdit}
                  onOpenTask={openTask}
                  onStartLink={startLink}
                  linkTargetId={draft?.targetTaskId ?? null}
                  linking={draft !== null}
                />
              ),
            )}

            <GanttLinkLayer
              links={links}
              rows={rows}
              taskRows={taskRows}
              tasks={taskById}
              timeline={timeline}
              canEdit={canEdit}
              onDelete={onDeleteLink}
            />

            {draft && <LinkDraftLine draft={draft} timeline={timeline} taskRows={taskRows} tasks={taskById} />}
          </div>
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
