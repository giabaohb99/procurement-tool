import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import type { WorkRosterDay, WorkRosterItem } from '../types/work-roster'
import { WEEKDAY_LABELS } from '../utils/calendar-grid'
import { describeRosterCell, type WorkRosterCellView } from '../utils/work-roster-cell'

interface WorkRosterDayListProps {
  days: WorkRosterDay[]
  items: WorkRosterItem[]
  selectedISO: string
  onSelect: (iso: string) => void
  todayISO: string
}

interface Row {
  item: WorkRosterItem
  view: WorkRosterCellView
}

function reasonOf(view: WorkRosterCellView): string {
  return view.isPending ? `${view.shortLabel} · chờ duyệt` : view.shortLabel
}

function RowLine({ row }: { row: Row }) {
  const { item, view } = row
  const content = (
    <>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{item.full_name}</span>
        <span className="block truncate text-xs text-muted-foreground">
          {item.code}
          {item.department_name ? ` · ${item.department_name}` : ''}
        </span>
      </span>
      <span
        title={view.description}
        className={cn(
          'max-w-[45%] shrink-0 truncate rounded-sm border border-transparent px-2 py-0.5 text-xs',
          'bg-muted/60 text-muted-foreground',
          (view.state === 'leave' || view.state === 'partial') && 'bg-leave-approved text-leave-approved-foreground',
          view.state === 'holiday' && 'bg-destructive/10 text-destructive',
          view.isPending && 'border-dashed border-info bg-info/10 text-info',
        )}
      >
        {reasonOf(view)}
      </span>
    </>
  )
  const base = 'flex items-center gap-3 rounded-md border bg-card px-3 py-2'
  return view.leaveRequestId !== null ? (
    <Link to={appRoutes.hr.leaveRequestDetail(view.leaveRequestId)} className={base}>
      {content}
    </Link>
  ) : (
    <div className={base}>{content}</div>
  )
}

function Section({ title, rows, emptyText }: { title: string; rows: Row[]; emptyText: string }) {
  return (
    <section aria-label={title} className="space-y-2">
      <h2 className="text-sm font-semibold">
        {title} <span className="font-normal text-muted-foreground">({rows.length})</span>
      </h2>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">{emptyText}</p>
      ) : (
        <ul className="space-y-1.5">
          {rows.map((row) => (
            <li key={row.item.employee_id}>
              <RowLine row={row} />
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

/**
 * Khổ điện thoại: lưới ngang không đọc nổi nên chọn MỘT ngày rồi chia nhân sự
 * thành hai nhóm «Đi làm» / «Nghỉ». Nửa buổi nghỉ vẫn nằm ở «Đi làm» (còn một buổi).
 * Ô thiếu dữ liệu (`unknown`) không vào nhóm nào — đừng đoán.
 */
export function WorkRosterDayList({ days, items, selectedISO, onSelect, todayISO }: WorkRosterDayListProps) {
  //  Biểu ngữ chỉ mang lễ CHUNG; lễ riêng của pháp nhân đi theo từng dòng (tooltip `view.description`).
  const holidayName = days.find((d) => d.date === selectedISO)?.holiday_name ?? ''
  const rows: Row[] = items.map((item) => ({
    item,
    view: describeRosterCell(item.cells.find((c) => c.date === selectedISO)),
  }))
  const working = rows.filter((r) => r.view.isWorking)
  const off = rows.filter((r) => !r.view.isWorking && r.view.state !== 'unknown')

  return (
    <div className="space-y-4">
      <div role="group" aria-label="Chọn ngày" className="-mx-4 flex gap-1 overflow-x-auto px-4 pb-1">
        {days.map((day) => (
          <button
            key={day.date}
            type="button"
            aria-pressed={day.date === selectedISO}
            aria-current={day.date === todayISO ? 'date' : undefined}
            onClick={() => onSelect(day.date)}
            className={cn(
              'flex min-w-11 shrink-0 flex-col items-center rounded-md border px-2 py-1 text-xs',
              day.date === selectedISO ? 'border-primary bg-primary text-primary-foreground' : 'bg-card',
              day.date !== selectedISO && day.date === todayISO && 'border-primary text-primary',
              day.date !== selectedISO && day.holiday_name && 'bg-destructive/10',
            )}
          >
            <span>{WEEKDAY_LABELS[day.weekday] ?? ''}</span>
            <span className="font-semibold tabular-nums">{Number(day.date.slice(8, 10))}</span>
          </button>
        ))}
      </div>
      {holidayName && <p className="text-sm text-muted-foreground">Ngày lễ: {holidayName}</p>}
      <Section title="Đi làm" rows={working} emptyText="Không ai đi làm." />
      <Section title="Nghỉ" rows={off} emptyText="Không ai nghỉ." />
    </div>
  )
}
