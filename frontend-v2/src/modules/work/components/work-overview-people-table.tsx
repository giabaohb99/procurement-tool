import { Users } from 'lucide-react'
import { useMemo, useState } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import { formatRelativeTime } from '@/shared/utils/format-date'
import { nameInitials } from '@/shared/utils/name-initials'

import type { WorkOverviewPerson } from '../hooks/use-work-overview'
import { PersonAvatar } from './person-avatar'
import { WorkOverviewPersonTasksDialog } from './work-overview-person-tasks-dialog'

/** Lâu hơn chừng này ngày không động tới việc nào thì tô cam ô "Cập nhật gần nhất" — đáng hỏi một câu. */
const STALE_DAYS = 14

/** Máy chủ trả `updated_at` giờ UTC KHÔNG kèm múi giờ — gắn `Z` để trình duyệt khỏi đọc thành giờ địa phương (lệch 7 tiếng). */
function asUtc(value: string): string {
  return /([zZ]|[+-]\d\d:?\d\d)$/.test(value) ? value : `${value}Z`
}

function daysSince(value: string | null, now: Date): number | null {
  if (!value) return null
  return Math.floor((now.getTime() - new Date(asUtc(value)).getTime()) / 86_400_000)
}

/** Ô số: số 0 để mờ để mắt dừng ở chỗ có việc. */
function Count({ value, danger = false }: { value: number; danger?: boolean }) {
  return (
    <span className={cn('tabular-nums', value === 0 ? 'text-muted-foreground/60' : danger && 'font-semibold text-destructive')}>
      {value.toLocaleString('vi-VN')}
    </span>
  )
}

function OnTimeRate({ value }: { value: number | null }) {
  //  `null` = chưa có việc nào để đo — hiện gạch, không hiện 0% (0% là "trễ hết", nói sai sự thật).
  if (value === null) return <span className="text-muted-foreground/60">—</span>
  const tone = value >= 80 ? 'text-success' : value >= 50 ? 'text-warning' : 'text-destructive'
  return <span className={cn('font-medium tabular-nums', tone)}>{value}%</span>
}

function Hours({ value }: { value: number }) {
  if (!value) return <span className="text-muted-foreground/60">—</span>
  return <span className="tabular-nums">{value.toLocaleString('vi-VN', { maximumFractionDigits: 1 })} giờ</span>
}

interface WorkOverviewPeopleTableProps {
  people: WorkOverviewPerson[] | undefined
  periodDays: number
  isLoading: boolean
  isError: boolean
}

/**
 * Bảng ĐỐI CHIẾU THEO NGƯỜI của màn Tổng quan Dự án (duoc-CR-782) — trả lời câu hỏi của người quản lý: ai đang ôm
 * bao nhiêu việc, ai đang trễ, ai làm xong đúng hạn, ai lâu rồi không động tới việc. Bấm một dòng mở danh sách việc
 * đang mở của người đó.
 *
 * Thứ tự do MÁY CHỦ xếp (người nhiều việc quá hạn lên đầu); bảng nhận đủ mọi dòng nên không phân trang.
 */
export function WorkOverviewPeopleTable({ people, periodDays, isLoading, isError }: WorkOverviewPeopleTableProps) {
  const [selected, setSelected] = useState<WorkOverviewPerson | null>(null)

  const columns = useMemo<DataTableColumn<WorkOverviewPerson>[]>(() => {
    const now = new Date()
    return [
      {
        key: 'name',
        header: 'Người phụ trách',
        width: 220,
        hideable: false,
        defaultPinned: true,
        cell: (p) => (
          <span className="flex min-w-0 items-center gap-2">
            <PersonAvatar name={p.name} avatar={p.avatar} initials={nameInitials(p.name)} />
            <span className="min-w-0">
              <span className="block truncate font-medium">{p.name || `Nhân sự #${p.employee_id}`}</span>
              {p.code && <span className="block truncate text-xs text-muted-foreground">{p.code}</span>}
            </span>
          </span>
        ),
      },
      { key: 'open', header: 'Đang mở', width: 90, align: 'right', cell: (p) => <Count value={p.open} /> },
      {
        key: 'overdue',
        header: 'Quá hạn',
        width: 90,
        align: 'right',
        cell: (p) => <Count value={p.overdue} danger />,
      },
      {
        key: 'max_overdue_days',
        header: 'Trễ lâu nhất',
        width: 110,
        align: 'right',
        cell: (p) =>
          p.max_overdue_days ? (
            <span className="font-medium text-destructive tabular-nums">{p.max_overdue_days} ngày</span>
          ) : (
            <span className="text-muted-foreground/60">—</span>
          ),
      },
      {
        key: 'due_soon',
        header: 'Hạn 7 ngày tới',
        width: 120,
        align: 'right',
        cell: (p) => <Count value={p.due_soon} />,
      },
      {
        key: 'done_in_period',
        header: `Xong trong ${periodDays} ngày`,
        width: 130,
        align: 'right',
        cell: (p) => <Count value={p.done_in_period} />,
      },
      {
        key: 'on_time_rate',
        header: 'Đúng hạn',
        width: 100,
        align: 'right',
        cell: (p) => <OnTimeRate value={p.on_time_rate} />,
      },
      {
        key: 'estimate_hours_open',
        header: 'Giờ ước (việc mở)',
        width: 140,
        align: 'right',
        defaultHidden: true,
        cell: (p) => <Hours value={p.estimate_hours_open} />,
      },
      {
        key: 'actual_hours_done',
        header: 'Giờ thực tế (đã xong)',
        width: 160,
        align: 'right',
        defaultHidden: true,
        cell: (p) => <Hours value={p.actual_hours_done} />,
      },
      {
        key: 'last_update',
        header: 'Cập nhật gần nhất',
        width: 150,
        cell: (p) => {
          const days = daysSince(p.last_update, now)
          if (days === null || !p.last_update) return <span className="text-muted-foreground/60">—</span>
          return (
            <span className={cn(days >= STALE_DAYS && 'font-medium text-warning')}>
              {formatRelativeTime(asUtc(p.last_update), now)}
            </span>
          )
        },
      },
    ]
  }, [periodDays])

  return (
    <Card className="gap-3">
      <CardHeader className="max-md:px-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <Users className="size-4 text-muted-foreground" />
          Đối chiếu theo người
        </CardTitle>
        <CardDescription>
          Mỗi người phụ trách một dòng, người nhiều việc quá hạn lên đầu. Một việc hai người giữ thì tính cho cả hai.
          Bấm vào một người để xem việc đang mở của họ.
        </CardDescription>
      </CardHeader>
      <CardContent className="max-md:px-4">
        <DataTable
          columns={columns}
          rows={people}
          getRowId={(p) => p.employee_id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có việc nào được giao cho ai trong các dự án đang xem."
          storageKey="work.overview.people"
          onRowClick={setSelected}
        />
      </CardContent>
      <WorkOverviewPersonTasksDialog person={selected} onClose={() => setSelected(null)} />
    </Card>
  )
}
