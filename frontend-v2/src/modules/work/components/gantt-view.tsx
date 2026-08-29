import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { useMemo, useRef, useState } from 'react'

import { cn } from '@/shared/utils/cn'
import type { WorkLabelField, WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { formatDueLabel, today } from '../utils/due-date'
import { priorityColorOf } from '../utils/priority-field'
import {
  datesToSave,
  daysDragged,
  readDragData,
  snapToDayGrid,
  type GanttDragData,
} from '../utils/gantt-drag'
import { GRID_COLUMNS, GRID_WIDTH, HEADER_HEIGHT, ROW_HEIGHT } from '../utils/gantt-layout'
import {
  buildTimeline,
  dayLabel,
  groupHeader,
  isWeekend,
  type GanttTimeline,
  type GanttZoom,
} from '../utils/gantt-scale'
import { GanttDragPreview } from './gantt-drag-preview'
import { GanttRow } from './gantt-row'

interface GanttViewProps {
  tasks: WorkTask[]
  /**
   * Trường ĐỘ ƯU TIÊN của dự án — thanh việc tô theo màu bậc ưu tiên. Vắng =
   * dự án đã xóa trường đó, thanh về màu xám.
   */
  priorityField?: WorkLabelField
  zoom: GanttZoom
  canEdit: boolean
  onOpenTask: (taskId: number) => void
  /**
   * Kéo xong thanh — nhận ĐÚNG những trường đổi, không phải cả cặp ngày. Luật
   * quyết định trường nào nằm ở `utils/gantt-drag.ts` (`datesToSave`).
   */
  onMoveDates: (taskId: number, values: { start_date?: string; due_date?: string }) => void
}

/**
 * Khung nhìn GANTT (D-05) — khung nhìn thứ ba, cùng bộ với Bảng và Danh sách.
 *
 * Bố cục và thao tác bám **DHTMLX Gantt** (`05-giao-dien.md` §10 chỉ định làm
 * tham khảo): lưới cột bên trái · trục thời gian bên phải · hai hàng tiêu đề
 * (tháng + ngày) · vạch hôm nay · thanh kéo dời lịch, kéo hai mép đổi ngày ·
 * phần tô đậm trong thanh là tiến độ.
 *
 * **Tự dựng, KHÔNG cài thư viện của họ.** Ba lý do theo thứ tự cân nhắc:
 * 1. `dhtmlx-gantt` bản Standard là **GPLv2**. Dùng nội bộ không kích hoạt nghĩa
 *    vụ mở mã, nhưng rước một giấy phép lây lan vào repo để đổi lấy một biểu đồ
 *    thanh ngang là không đáng — bản Pro thì trả phí.
 * 2. Thư viện Gantt nào cũng mang CSS riêng, không biết gì về token màu và chế
 *    độ nền của hệ; chỉnh cho khớp còn tốn hơn tự vẽ.
 * 3. Phần khó nhất của họ là MŨI TÊN PHỤ THUỘC việc trước–sau, mà ta chưa có dữ
 *    liệu đó (chưa có bảng `tab_work_task_link`, cố ý chưa thêm — §10).
 *
 * Riêng phần KÉO thì dùng **dnd-kit**, cùng bộ với kanban. Bản đầu tự bắt
 * `pointerdown/move/up` và sai bốn chỗ: cuộn ngang giữa lúc kéo là thanh trôi
 * theo thanh cuộn (không trừ phần cuộn ra khỏi quãng đường chuột đi), thả ra
 * xong cú `click` vẫn nổ nên panel chi tiết bật lên sau mỗi lần kéo, hai mép
 * nằm lồng trong thanh nên `overflow-hidden` cắt mất vùng bắt chuột, và mỗi
 * nhịp chuột lại `setState` khiến cả biểu đồ vẽ lại nên kéo giật.
 *
 * Vị trí tạm lúc kéo nằm ở **`DragOverlay`** (`GanttDragPreview`) — chỉ mình nó
 * vẽ lại theo con trỏ, các hàng bên dưới đứng yên.
 */
export function GanttView({
  tasks,
  priorityField,
  zoom,
  canEdit,
  onOpenTask,
  onMoveDates,
}: GanttViewProps) {
  const homNay = today()
  const timeline = useMemo(() => buildTimeline(tasks, zoom, homNay), [tasks, zoom, homNay])
  const header = useMemo(() => groupHeader(timeline, zoom), [timeline, zoom])
  const [keo, setKeo] = useState<GanttDragData | null>(null)

  //  Sau một cú kéo thật, trình duyệt vẫn bắn `click` lên chính thanh vừa kéo —
  //  không chặn thì kéo xong là panel chi tiết bật ra. Cờ bật ở `onDragStart` và
  //  được xóa ở `pointerdown` của lần bấm SAU, nên không bao giờ kẹt lại (thả
  //  chuột ngoài vùng thanh thì không có `click` nào để tự xóa).
  const vuaKeo = useRef(false)

  //  Ngưỡng 4px chứ không 6px như kanban: ở mức phóng Tháng một ngày chỉ rộng
  //  5px, gác 6px là nuốt luôn nấc dịch chuyển đầu tiên.
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }))
  const snap = useMemo(() => snapToDayGrid(timeline.dayWidth), [timeline.dayWidth])

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
    onOpenTask(taskId)
  }

  if (tasks.length === 0) {
    return (
      <p className="py-16 text-center text-sm text-muted-foreground">
        Không có công việc nào khớp bộ lọc đang chọn.
      </p>
    )
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setKeo(null)}
    >
      <div
        className="flex min-h-0 flex-1 overflow-auto rounded-lg border bg-card"
        onPointerDownCapture={() => {
          vuaKeo.current = false
        }}
      >
        <GanttGrid tasks={tasks} onOpenTask={onOpenTask} />

        <div className="relative shrink-0" style={{ width: timeline.totalWidth }}>
          <GanttHeader timeline={timeline} header={header} zoom={zoom} homNay={homNay} />

          {/* Lưới nền + vạch hôm nay nằm dưới các thanh. */}
          <div className="absolute inset-x-0 bottom-0 flex" style={{ top: HEADER_HEIGHT }}>
            {timeline.days.map((ngay) => (
              <div
                key={ngay}
                style={{ width: timeline.dayWidth }}
                className={cn(
                  'h-full shrink-0 border-r border-border/60',
                  isWeekend(ngay) && 'bg-muted/40',
                  ngay === homNay && 'bg-primary/5',
                )}
              />
            ))}
          </div>

          <div className="relative">
            {tasks.map((t, i) => (
              <GanttRow
                key={t.id}
                task={t}
                timeline={timeline}
                barColor={priorityColorOf(t, priorityField)}
                canEdit={canEdit}
                zebra={i % 2 === 1}
                onOpenTask={openTask}
              />
            ))}
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

/** Lưới trái: tên việc + hai cột ngày, dính lại khi cuộn ngang. */
function GanttGrid({
  tasks,
  onOpenTask,
}: {
  tasks: WorkTask[]
  onOpenTask: (taskId: number) => void
}) {
  return (
    <div className="sticky left-0 z-20 shrink-0 border-r bg-card" style={{ width: GRID_WIDTH }}>
      <div
        className="sticky top-0 z-10 flex items-end border-b bg-muted/50"
        style={{ height: HEADER_HEIGHT }}
      >
        {GRID_COLUMNS.map((c) => (
          <div
            key={c.key}
            style={{ width: c.width }}
            className="border-r px-3 pb-2 text-xs font-medium text-muted-foreground last:border-r-0"
          >
            {c.label}
          </div>
        ))}
      </div>

      {tasks.map((t, i) => (
        <button
          key={t.id}
          type="button"
          onClick={() => onOpenTask(t.id)}
          style={{ height: ROW_HEIGHT }}
          className={cn(
            'flex w-full items-center border-b text-left text-sm hover:bg-accent',
            i % 2 === 1 && 'bg-muted/20',
          )}
        >
          <span
            style={{ width: GRID_COLUMNS[0].width }}
            className={cn(
              'truncate px-3',
              t.status === WORK_TASK_STATUS.DONE && 'text-muted-foreground line-through',
            )}
          >
            {t.title}
          </span>
          <span
            style={{ width: GRID_COLUMNS[1].width }}
            className="px-3 text-xs text-muted-foreground"
          >
            {formatDueLabel(t.start_date) || '—'}
          </span>
          <span
            style={{ width: GRID_COLUMNS[2].width }}
            className="px-3 text-xs text-muted-foreground"
          >
            {formatDueLabel(t.due_date) || '—'}
          </span>
        </button>
      ))}
    </div>
  )
}

function GanttHeader({
  timeline,
  header,
  zoom,
  homNay,
}: {
  timeline: GanttTimeline
  header: { key: string; label: string; width: number }[]
  zoom: GanttZoom
  homNay: string
}) {
  return (
    <div className="sticky top-0 z-10 bg-muted/50">
      <div className="flex" style={{ height: ROW_HEIGHT }}>
        {header.map((o) => (
          <div
            key={o.key}
            style={{ width: o.width }}
            className="flex shrink-0 items-center justify-center border-r border-b text-xs font-medium text-muted-foreground"
          >
            {o.label}
          </div>
        ))}
      </div>
      <div className="flex" style={{ height: ROW_HEIGHT }}>
        {timeline.days.map((ngay) => {
          const { so, thu } = dayLabel(ngay)
          return (
            <div
              key={ngay}
              style={{ width: timeline.dayWidth }}
              className={cn(
                'flex shrink-0 flex-col items-center justify-center border-r border-b text-[10px] leading-none',
                isWeekend(ngay) ? 'text-muted-foreground/60' : 'text-muted-foreground',
                ngay === homNay && 'bg-primary/10 font-semibold text-primary',
              )}
            >
              {/* Mức Tuần/Tháng: ô hẹp quá để in chữ, chỉ giữ vạch lưới. */}
              {zoom === 'day' && (
                <>
                  <span>{so}</span>
                  <span className="mt-0.5">{thu}</span>
                </>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
