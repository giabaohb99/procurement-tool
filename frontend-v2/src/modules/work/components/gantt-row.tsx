import { useDraggable } from '@dnd-kit/core'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { memo } from 'react'

import { cn } from '@/shared/utils/cn'
import type { WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { formatDueLabel } from '../utils/due-date'
import type { GanttDragKind } from '../utils/gantt-drag'
import {
  BAR_PAD,
  HANDLE_WIDTH,
  LINK_DOT,
  MILESTONE_SIZE,
  MIN_LABEL_WIDTH,
  ROW_HEIGHT,
} from '../utils/gantt-layout'
import type { OffscreenSide } from '../hooks/use-offscreen-bars'
import type { GanttGroupRow } from '../utils/gantt-rows'
import type { LinkSide } from '../utils/gantt-links'
import {
  barGeometry,
  daysBetween,
  isMilestone,
  milestoneCenter,
  rangeGeometry,
  type GanttTimeline,
} from '../utils/gantt-scale'
import { chipClass } from '../utils/work-colors'
import { GanttScheduleLayer } from './gantt-schedule-layer'

export interface GanttLinkHandlers {
  /** Bắt đầu kéo một mũi tên từ đầu `side` của việc này. */
  onStartLink: (taskId: number, side: LinkSide, event: React.PointerEvent) => void
  /** Việc đang được nhắm làm ĐÍCH của mũi tên đang kéo — tô sáng thanh của nó. */
  linkTargetId: number | null
  /** Có mũi tên nào đang được kéo không: lúc ấy mọi chấm nối đều hiện sẵn. */
  linking: boolean
}

interface GanttTaskRowProps extends GanttLinkHandlers {
  task: WorkTask
  /**
   * Hàng này là VIỆC CON: thanh vẽ mảnh hơn và KHÔNG có chấm nối phụ thuộc —
   * việc con không đặt phụ thuộc được (backend chặn thẳng theo luật C-05), bày
   * chấm ra chỉ mời người dùng ăn một toast 400.
   */
  isSubtask?: boolean
  timeline: GanttTimeline
  /** Màu thanh — tên màu trong `WORK_COLORS`, lấy từ bậc ưu tiên của việc. */
  barColor: string
  canEdit: boolean
  /**
   * Thanh của việc này đã trôi hẳn ra ngoài khung nhìn ở phía nào — `null` là
   * đang thấy được. Vẽ một chip mũi tên ở mép khung để cuộn về.
   */
  offscreen: OffscreenSide | null
  onJumpToTask: (taskId: number) => void
  /** Đặt lịch cho một việc CHƯA có ngày, bằng cách kéo trên hàng trống của nó. */
  onSchedule: (taskId: number, from: string, to: string) => void
  onOpenTask: (taskId: number) => void
}

/**
 * Một hàng VIỆC của trục thời gian: thanh (hoặc hình thoi cột mốc), hai mép kéo
 * đổi ngày, và hai chấm nối phụ thuộc.
 *
 * Hàng này **không vẽ lại trong lúc kéo ngày** — kết quả tạm hiện ở lớp phủ
 * (`GanttDragPreview`). Bản đầu cập nhật vị trí thanh theo từng nhịp chuột, kéo
 * theo cả trăm ô lưới ngày vẽ lại cùng lúc nên kéo giật.
 *
 * Việc chưa đặt ngày vẫn có hàng riêng, chỉ là không có thanh — giấu đi thì
 * người dùng đếm thiếu việc mà không biết vì sao (lưới trái vẫn liệt kê nó).
 */
export const GanttTaskRow = memo(function GanttTaskRow({
  task,
  isSubtask = false,
  timeline,
  barColor,
  canEdit,
  offscreen,
  onJumpToTask,
  onSchedule,
  onOpenTask,
  onStartLink,
  linkTargetId,
  linking,
}: GanttTaskRowProps) {
  //  `group/ganttrow` là móc để hai chấm nối chỉ hiện khi rê chuột vào HÀNG này.
  //  `flex items-center` chỉ để chip «cuộn về thanh» có chỗ đứng trong luồng —
  //  mọi thứ còn lại của hàng đều `absolute` nên không đụng gì tới bố cục.
  //  ⚠️ KHÔNG kẻ ngang trong vùng biểu đồ — chỉ có vạch DỌC của lưới ngày, đúng
  //  lối Lark (khách 31/08/2026: *"cho border dọc hà"*). Kẻ cả hai chiều thì
  //  vùng thanh thành một tấm bảng ô vuông, mà mắt đang cần lần theo thanh nằm
  //  ngang chứ không cần đếm ô. Hàng vẫn khớp với lưới trái nhờ cùng
  //  `ROW_HEIGHT`, và dải nền của hàng NHÓM đủ để tách các cụm.
  const nen = 'group/ganttrow relative flex items-center'
  //  Thanh việc con mảnh hơn và thụt vào theo chiều DỌC — nhìn là biết ngay nó
  //  thuộc về hàng ngay trên, khỏi phải dò sang lưới trái.
  const barPad = isSubtask ? BAR_PAD + 4 : BAR_PAD
  const barHeight = ROW_HEIGHT - barPad * 2
  const xong = task.status === WORK_TASK_STATUS.DONE
  const laDich = linkTargetId === task.id

  if (isMilestone(task)) {
    const center = milestoneCenter(task, timeline)
    //  Cột mốc chưa có ngày cũng xếp lịch được y như việc thường — nó chỉ nhận
    //  một đầu ngày, `GanttView` lo việc ghi xuống trường nào.
    if (center === null)
      return (
        <div style={{ height: ROW_HEIGHT }} className={nen}>
          {canEdit && (
            <GanttScheduleLayer
              timeline={timeline}
              onSchedule={(from, to) => onSchedule(task.id, from, to)}
            />
          )}
        </div>
      )
    return (
      <div style={{ height: ROW_HEIGHT }} className={nen}>
        <OffscreenJump side={offscreen} task={task} onJump={onJumpToTask} />
        <GanttMilestone
          task={task}
          center={center}
          xong={xong}
          canEdit={canEdit}
          laDich={laDich}
          linking={linking}
          onOpenTask={onOpenTask}
          onStartLink={onStartLink}
        />
      </div>
    )
  }

  const bar = barGeometry(task, timeline)
  //  Việc CHƯA CÓ NGÀY: hàng trống, nhưng cả hàng là chỗ XẾP LỊCH — rê vào hiện
  //  ô nét đứt kèm `+`, kéo ngang là chọn quãng. Không có chip «cuộn về thanh»
  //  vì chẳng có thanh nào để về.
  if (!bar)
    return (
      <div style={{ height: ROW_HEIGHT }} className={nen}>
        {canEdit && (
          <GanttScheduleLayer
            timeline={timeline}
            onSchedule={(from, to) => onSchedule(task.id, from, to)}
          />
        )}
      </div>
    )
  const nhanNgoai = bar.width < MIN_LABEL_WIDTH

  return (
    <div style={{ height: ROW_HEIGHT }} className={nen}>
      <OffscreenJump side={offscreen} task={task} onJump={onJumpToTask} />
      <GanttBar
        task={task}
        barColor={barColor}
        left={bar.left}
        width={bar.width}
        top={barPad}
        height={barHeight}
        xong={xong}
        canEdit={canEdit}
        laDich={laDich}
        hienNhan={!nhanNgoai}
        onOpenTask={onOpenTask}
      />

      {canEdit && (
        <>
          <GanttHandle task={task} kind="start" left={bar.left} top={barPad} height={barHeight} />
          <GanttHandle
            task={task}
            kind="end"
            left={bar.left + bar.width - HANDLE_WIDTH}
            top={barPad}
            height={barHeight}
          />
          {!isSubtask && (
            <>
              <LinkDot
                taskId={task.id}
                side="start"
                left={bar.left - LINK_DOT - 2}
                visible={linking}
                onStartLink={onStartLink}
              />
              <LinkDot
                taskId={task.id}
                side="end"
                left={bar.left + bar.width + 2}
                visible={linking}
                onStartLink={onStartLink}
              />
            </>
          )}
        </>
      )}

      {/*  Tên đặt ngoài thanh khi thanh quá ngắn. Không bắt sự kiện chuột để nó
          không che mất mép kéo của thanh bên cạnh. */}
      {nhanNgoai && (
        <span
          className={cn(
            'pointer-events-none absolute z-10 flex items-center gap-1.5 text-[11px] whitespace-nowrap',
            xong ? 'text-muted-foreground line-through' : 'text-foreground/80',
          )}
          style={{ left: bar.left + bar.width + LINK_DOT + 8, top: 10, maxWidth: 260 }}
        >
          <span className="truncate">{task.title}</span>
          <SoNgay task={task} />
        </span>
      )}
    </div>
  )
})

/**
 * Chip mũi tên ở MÉP KHUNG khi thanh của việc đã trôi ra ngoài tầm nhìn — bấm
 * để cuộn về nó. Lark có đúng thứ này và nó cần: trục dài hai năm, kéo vài nhịp
 * là biểu đồ chỉ còn một tấm lưới trống, không biết việc nằm bên trái hay phải.
 *
 * Đứng được ở mép là nhờ `sticky` — chip nằm TRONG luồng của hàng (hàng có
 * `flex items-center`), nên nó bám khung cuộn thay vì bám dải ngày. Chip phía
 * phải cần `ml-auto` để chỗ đứng tĩnh của nó ở cuối dải, rồi `sticky right-2`
 * mới kéo được nó vào trong tầm nhìn.
 *
 * Chỉ hiện MŨI TÊN, không kèm chữ: mỗi hàng một chip, dự án trăm việc mà chip
 * nào cũng có nhãn thì mép khung thành một cột chữ chạy dọc, che mất chính cái
 * lưới đang cần nhìn. Tên việc để trong `title`.
 */
function OffscreenJump({
  side,
  task,
  onJump,
}: {
  side: OffscreenSide | null
  task: WorkTask
  onJump: (taskId: number) => void
}) {
  if (!side) return null

  const Icon = side === 'left' ? ArrowLeft : ArrowRight
  return (
    <button
      type="button"
      title={`Cuộn về thanh của: ${task.title}`}
      aria-label={`Cuộn về thanh của việc ${task.title}`}
      onClick={(e) => {
        e.stopPropagation()
        onJump(task.id)
      }}
      className={cn(
        'sticky z-30 flex size-5 shrink-0 items-center justify-center rounded-full',
        'border bg-background text-muted-foreground shadow-sm',
        'transition-colors hover:border-primary hover:text-primary',
        side === 'left' ? 'left-2' : 'right-2 ml-auto',
      )}
    >
      <Icon className="size-3" />
    </button>
  )
}

/**
 * Hàng NHÓM: quãng của nhóm vẽ thành một **mảng nền mờ bo góc** trải từ ngày sớm
 * nhất tới hạn muộn nhất của các việc trong nhóm.
 *
 * ⚠️ Bản trước là một thanh dẹt xám đậm kèm hai chân tam giác quặp xuống (lối
 * thanh tóm tắt của Gantt cổ điển). Khách bỏ 31/08/2026 — *"UI đang bị xấu"*:
 * hai cái chân 6px lệch khỏi trục 1px, ở cỡ đó mắt không đọc ra "thanh tóm tắt"
 * mà đọc ra hai vệt thừa; còn thân thanh thì đậm ngang thanh việc nên hàng nhóm
 * tranh mất chú ý của chính những việc nó tóm tắt.
 *
 * Mảng nền thì lùi hẳn về sau: nó nói "quãng của nhóm nằm ở đây" mà không đòi
 * nhìn. Không viền — thêm viền là nó lại thành một cái hộp, tức lại tranh chú ý.
 *
 * Không kéo được: ngày của nó là ngày TÍNH RA từ các việc con, kéo thì không
 * biết phải dời việc nào.
 */
/** Bề dày dải nền của hàng NHÓM (px) — mảnh hơn hẳn thanh việc, cố ý. */
const GROUP_BAND_HEIGHT = 10

export function GanttGroupBar({
  row,
  timeline,
}: {
  row: GanttGroupRow
  timeline: GanttTimeline
}) {
  const bar = row.range ? rangeGeometry(row.range.start, row.range.due, timeline) : null
  return (
    <div style={{ height: ROW_HEIGHT }} className="relative bg-muted/30">
      {bar && (
        <div
          className="absolute overflow-hidden rounded-full bg-foreground/10"
          //  MỎNG và canh giữa hàng. Bản đầu cao `ROW_HEIGHT - 2·BAR_PAD` (22px)
          //  — khách chê dày: mảng ấy to gần bằng thanh việc nên hàng nhóm lại
          //  tranh chú ý, đúng cái bệnh của thanh xám cũ mà nó thay thế. Hàng
          //  nhóm chỉ cần nói "quãng nằm ở đây", một dải mảnh là đủ.
          style={{
            left: bar.left,
            width: bar.width,
            top: (ROW_HEIGHT - GROUP_BAND_HEIGHT) / 2,
            height: GROUP_BAND_HEIGHT,
          }}
          title={`${row.group.name} · ${formatDueLabel(row.range?.start ?? '')} → ${formatDueLabel(row.range?.due ?? '')}`}
        >
          {/*  Phần tô đậm = tỉ lệ việc đã hoàn thành trong nhóm. Vẫn giữ vì đây
               là thông tin duy nhất hàng nhóm mang ngoài cái quãng ngày. */}
          {row.progress > 0 && (
            <span
              aria-hidden
              className="absolute inset-y-0 left-0 bg-emerald-500/25"
              style={{ width: `${Math.min(100, row.progress * 100)}%` }}
            />
          )}
        </div>
      )}
    </div>
  )
}

interface GanttBarProps {
  task: WorkTask
  barColor: string
  left: number
  width: number
  top: number
  height: number
  xong: boolean
  canEdit: boolean
  laDich: boolean
  hienNhan: boolean
  onOpenTask: (taskId: number) => void
}

/** Thanh việc — kéo cả thanh để DỜI lịch. */
function GanttBar({
  task,
  barColor,
  left,
  width,
  top,
  height,
  xong,
  canEdit,
  laDich,
  hienNhan,
  onOpenTask,
}: GanttBarProps) {
  const { setNodeRef, listeners, attributes, isDragging } = useDraggable({
    id: `gantt-move-${task.id}`,
    disabled: !canEdit,
    data: { task, kind: 'move' satisfies GanttDragKind },
  })

  //  Phần tô đậm trong thanh = tiến độ. Việc đã xong là 100%; còn lại lấy tỉ lệ
  //  việc con đã tick (thẻ kanban cũng hiện đúng con số này).
  const tienDo = xong ? 1 : task.subtask_total ? task.subtask_done / task.subtask_total : 0
  const dau = task.start_date || task.due_date
  const cuoi = task.due_date || task.start_date

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      data-gantt-bar
      data-task-id={task.id}
      onClick={() => onOpenTask(task.id)}
      onKeyDown={(e) => e.key === 'Enter' && onOpenTask(task.id)}
      style={{ left, width, top, height }}
      className={cn(
        'absolute z-10 flex items-center overflow-hidden rounded px-2 text-[11px] font-medium',
        chipClass(barColor),
        'ring-1 ring-black/10 ring-inset',
        canEdit ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer',
        xong && 'opacity-60',
        isDragging && 'opacity-30',
        laDich && 'ring-2 ring-primary',
      )}
      title={`${task.title} · ${formatDueLabel(dau)} → ${formatDueLabel(cuoi)} · ${daysBetween(dau, cuoi) + 1} ngày`}
    >
      {/* Dải tiến độ nằm DƯỚI chữ, không che tiêu đề. */}
      {tienDo > 0 && (
        <span
          aria-hidden
          className="absolute inset-y-0 left-0 bg-current/20"
          style={{ width: `${Math.min(100, tienDo * 100)}%` }}
        />
      )}
      {hienNhan && (
        <span className="relative flex min-w-0 items-center gap-1.5">
          <span className="truncate">{task.title}</span>
          <SoNgay task={task} />
        </span>
      )}
    </div>
  )
}

/**
 * SỐ NGÀY của một việc, dán ngay sau tên trên thanh (hoặc sau cái nhãn ngoài
 * thanh, khi thanh quá ngắn để chứa chữ).
 *
 * Có nó thì đọc được độ dài mà không phải đếm ô lưới hay dò sang cột ngày — mà
 * đếm ô thì ở mức phóng Tuần / Tháng gần như không đếm nổi.
 *
 * `shrink-0` để nó KHÔNG bị cắt: thanh hẹp thì cắt cái tên (tên còn đọc được
 * phần đầu), chứ cắt con số thành «1 ng…» thì nó thành vô nghĩa. Không hiện với
 * việc chưa có ngày nào — chẳng có quãng nào để đếm.
 */
function SoNgay({ task }: { task: WorkTask }) {
  const dau = task.start_date || task.due_date
  const cuoi = task.due_date || task.start_date
  if (!dau || !cuoi) return null

  return (
    <span className="shrink-0 tabular-nums opacity-70">{daysBetween(dau, cuoi) + 1} ngày</span>
  )
}

/**
 * CỘT MỐC (B-14) — hình thoi tại đúng ngày, không phải một thanh.
 *
 * Kéo được như thanh (dời mốc sang ngày khác) nên vẫn là một `useDraggable` với
 * `kind: 'move'`; `datesToSave` chỉ ghi `due_date` vì mốc không có ngày bắt đầu.
 */
function GanttMilestone({
  task,
  center,
  xong,
  canEdit,
  laDich,
  linking,
  onOpenTask,
  onStartLink,
}: {
  task: WorkTask
  center: number
  xong: boolean
  canEdit: boolean
  laDich: boolean
  linking: boolean
  onOpenTask: (taskId: number) => void
  onStartLink: GanttLinkHandlers['onStartLink']
}) {
  const { setNodeRef, listeners, attributes, isDragging } = useDraggable({
    id: `gantt-move-${task.id}`,
    disabled: !canEdit,
    data: { task, kind: 'move' satisfies GanttDragKind },
  })

  return (
    <>
      <div
        ref={setNodeRef}
        {...attributes}
        {...listeners}
        data-gantt-bar
        data-task-id={task.id}
        onClick={() => onOpenTask(task.id)}
        onKeyDown={(e) => e.key === 'Enter' && onOpenTask(task.id)}
        style={{
          left: center - MILESTONE_SIZE / 2,
          top: ROW_HEIGHT / 2 - MILESTONE_SIZE / 2,
          width: MILESTONE_SIZE,
          height: MILESTONE_SIZE,
        }}
        className={cn(
          'absolute z-10 rotate-45 rounded-[2px] bg-primary ring-1 ring-black/10',
          canEdit ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer',
          xong && 'opacity-60',
          isDragging && 'opacity-30',
          laDich && 'ring-2 ring-primary',
        )}
        title={`${task.title} · Cột mốc ${formatDueLabel(task.due_date || task.start_date)}`}
      />
      <span
        className={cn(
          'pointer-events-none absolute z-10 truncate text-[11px] font-medium whitespace-nowrap',
          xong ? 'text-muted-foreground line-through' : 'text-foreground/80',
        )}
        style={{ left: center + MILESTONE_SIZE, top: 10, maxWidth: 220 }}
      >
        {task.title}
      </span>
      {canEdit && (
        <LinkDot
          taskId={task.id}
          side="end"
          left={center + MILESTONE_SIZE / 2 + 2}
          visible={linking}
          onStartLink={onStartLink}
        />
      )}
    </>
  )
}

/**
 * Mép kéo đổi một đầu ngày. Cố ý là ANH EM của thanh chứ không nằm TRONG thanh:
 * dnd-kit lồng hai vùng kéo vào nhau thì cú bấm vào mép đánh thức luôn thanh
 * cha, và `overflow-hidden` của thanh cũng cắt mất vùng bắt chuột.
 *
 * Không nhận tiêu điểm bàn phím: bàn phím chưa đổi được ngày ở đây (dùng panel
 * chi tiết), thêm hai chặng Tab mỗi hàng chỉ làm rối.
 */
function GanttHandle({
  task,
  kind,
  left,
  top,
  height,
}: {
  task: WorkTask
  kind: GanttDragKind
  left: number
  top: number
  height: number
}) {
  const { setNodeRef, listeners } = useDraggable({
    id: `gantt-${kind}-${task.id}`,
    data: { task, kind },
  })

  return (
    <span
      ref={setNodeRef}
      {...listeners}
      aria-hidden
      //  Mang theo id việc để phép dò đích của cú kéo NỐI PHỤ THUỘC nhận ra nó
      //  thuộc về ai — mép này đè lên thanh, thiếu nó thì thả vào những việc chỉ
      //  rộng một ngày luôn trượt (xem `use-gantt-link-draft.hitTest`).
      data-task-id={task.id}
      style={{ left, width: HANDLE_WIDTH, top, height }}
      className="absolute z-20 cursor-ew-resize rounded-sm hover:bg-foreground/20"
    />
  )
}

/**
 * Chấm NỐI PHỤ THUỘC ở một đầu thanh — kéo từ đây sang một việc khác là tạo mũi
 * tên (B-15).
 *
 * Nằm HẲN NGOÀI thanh: đặt lồng bên trong thì nó ăn mất chỗ của mép kéo đổi
 * ngày, và ở mức phóng Tháng (thanh rộng vài pixel) thì chồng lên nhau hết.
 *
 * Ẩn cho tới khi rê chuột vào hàng — hiện sẵn thì mỗi hàng có thêm hai chấm,
 * biểu đồ trăm việc thành một bãi chấm. Đang kéo một mũi tên thì hiện HẾT, vì
 * lúc ấy chúng chính là các đích để ngắm.
 *
 * Dùng `pointerdown` thô chứ không qua dnd-kit: dnd-kit trong khung này đang lo
 * việc kéo NGÀY, cho hai loại kéo khác nghĩa đi chung một `DndContext` thì
 * `onDragEnd` phải đoán xem cú thả vừa rồi là loại nào — đúng chỗ dễ nhầm nhất.
 */
function LinkDot({
  taskId,
  side,
  left,
  visible,
  onStartLink,
}: {
  taskId: number
  side: LinkSide
  left: number
  visible: boolean
  onStartLink: GanttLinkHandlers['onStartLink']
}) {
  return (
    <span
      role="presentation"
      aria-hidden
      data-task-id={taskId}
      title={side === 'end' ? 'Kéo để nối việc sau' : 'Kéo để nối việc trước'}
      onPointerDown={(e) => {
        e.stopPropagation()
        e.preventDefault()
        onStartLink(taskId, side, e)
      }}
      onClick={(e) => e.stopPropagation()}
      style={{
        left,
        top: ROW_HEIGHT / 2 - LINK_DOT / 2,
        width: LINK_DOT,
        height: LINK_DOT,
      }}
      className={cn(
        'absolute z-30 cursor-crosshair rounded-full border-2 border-primary bg-background transition-opacity',
        visible ? 'opacity-100' : 'opacity-0 group-hover/ganttrow:opacity-100',
      )}
    />
  )
}
