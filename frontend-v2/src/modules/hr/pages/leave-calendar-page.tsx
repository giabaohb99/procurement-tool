import { useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { cn } from '@/shared/utils/cn'
import { Link } from 'react-router-dom'
import { LeaveStatusBadge } from '../components/leave-status-badge'
import { useLeaveRequests } from '../hooks/use-leave'
import { LEAVE_STATUS, type LeaveRequest } from '../types/leave'

/**
 * LỊCH NGHỈ — trả lời câu *"tuần tới ai nghỉ"*.
 *
 * Đây là câu QĐ-NP5 nêu ra để giải thích vì sao đơn nghỉ phải là BẢNG chứ không
 * phải ô JSON của giấy GNP: hỏi được nó trên cột `DATE` có chỉ mục, còn quét
 * `JSON_EXTRACT` thì vừa chậm vừa không đánh chỉ mục được.
 *
 * Lọc theo **GIAO NHAU của khoảng**, không theo `from_date` đơn lẻ — một đơn
 * nghỉ từ tuần trước kéo sang tuần này phải lọt vào. Backend nhận đúng hai tham
 * số `from_date` / `to_date` cho việc đó.
 *
 * Dựng theo TUẦN chứ không theo tháng: người quản lý hỏi câu này để xếp việc
 * cho tuần tới, và một ô lịch tháng không đủ chỗ ghi tên ai nghỉ.
 */
const DAY_LABELS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']

/** Thứ Hai của tuần chứa `date`. `getDay()` trả 0 cho Chủ nhật nên phải nắn. */
function startOfWeek(date: Date): Date {
  const d = new Date(date)
  const shift = (d.getDay() + 6) % 7
  d.setDate(d.getDate() - shift)
  d.setHours(0, 0, 0, 0)
  return d
}

function toISODate(d: Date): string {
  //  Cắt tay theo giờ ĐỊA PHƯƠNG. `toISOString()` quy về UTC, mà Việt Nam lệch
  //  +7 — ngày 01/09 lúc 00:00 giờ VN thành 31/08 trong chuỗi ISO, và cả lịch
  //  lệch đi một ngày.
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

export function LeaveCalendarPage() {
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()))

  const days = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(weekStart)
      d.setDate(d.getDate() + i)
      return d
    })
  }, [weekStart])

  const params = useMemo(
    () => ({
      page: 1,
      page_size: 200,
      from_date: toISODate(days[0]),
      to_date: toISODate(days[6]),
    }),
    [days],
  )
  const { data, isLoading } = useLeaveRequests(params)

  //  Chỉ hiện đơn CÒN HIỆU LỰC. Đơn nháp chưa ai duyệt, đơn bị từ chối / đã hủy
  //  thì người ta vẫn đi làm — vẽ chúng lên lịch là xếp việc sai.
  const shown = (data?.items ?? []).filter(
    (r) => r.status === LEAVE_STATUS.PENDING || r.status === LEAVE_STATUS.APPROVED,
  )

  const onDay = (day: Date): LeaveRequest[] => {
    const iso = toISODate(day)
    return shown.filter((r) => r.from_date <= iso && iso <= r.to_date)
  }

  const shiftWeek = (weeks: number) => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + weeks * 7)
    setWeekStart(d)
  }

  const todayISO = toISODate(new Date())

  return (
    <PageContainer>
      <PageHeader
        title="Lịch nghỉ"
        description="Ai nghỉ ngày nào trong tuần — chỉ hiện đơn đang chờ duyệt và đã duyệt."
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" aria-label="Tuần trước" onClick={() => shiftWeek(-1)}>
              <ChevronLeft className="size-4" />
            </Button>
            <Button variant="outline" onClick={() => setWeekStart(startOfWeek(new Date()))}>
              Tuần này
            </Button>
            <Button variant="outline" size="icon" aria-label="Tuần sau" onClick={() => shiftWeek(1)}>
              <ChevronRight className="size-4" />
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-7">
        {days.map((day, i) => {
          const iso = toISODate(day)
          const items = onDay(day)
          const isWeekend = i >= 5
          return (
            <Card
              key={iso}
              className={cn(
                'min-h-40',
                isWeekend && 'bg-muted/40',
                iso === todayISO && 'ring-2 ring-primary',
              )}
            >
              <CardContent className="space-y-2 p-3">
                <div className="flex items-baseline justify-between">
                  <span className="text-sm font-semibold">{DAY_LABELS[i]}</span>
                  <span className="text-xs tabular-nums text-muted-foreground">
                    {day.getDate()}/{day.getMonth() + 1}
                  </span>
                </div>

                {isLoading ? (
                  <p className="text-xs text-muted-foreground">Đang tải…</p>
                ) : items.length === 0 ? (
                  <p className="text-xs text-muted-foreground">Không ai nghỉ</p>
                ) : (
                  items.map((r) => (
                    <Link
                      key={r.id}
                      to={appRoutes.hr.leaveRequestDetail(r.id)}
                      className="block rounded-md border bg-background p-2 text-xs hover:bg-accent"
                    >
                      <div className="font-medium">{r.employee_name || `#${r.employee_id}`}</div>
                      <div className="text-muted-foreground">{r.leave_type_name}</div>
                      <div className="mt-1">
                        <LeaveStatusBadge status={r.status} label={r.status_label} />
                      </div>
                    </Link>
                  ))
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </PageContainer>
  )
}
