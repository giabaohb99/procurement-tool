import { useCallback, useMemo } from 'react'

import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { useSetUrlParams, useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { LeaveCalendarDayView } from '../components/leave-calendar-day-view'
import { LeaveCalendarMonthGrid } from '../components/leave-calendar-month-grid'
import { LeaveCalendarToolbar } from '../components/leave-calendar-toolbar'
import { LeaveCalendarWeekGrid } from '../components/leave-calendar-week-grid'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import { useHolidays, useLeaveRequests } from '../hooks/use-leave'
import { LEAVE_STATUS, type LeaveRequest } from '../types/leave'
import { rangeOf, shiftAnchor, toISODate, type CalendarMode } from '../utils/calendar-grid'

/**
 * LỊCH NGHỈ — trả lời câu *"ai nghỉ ngày nào"*, ba mức phóng to: ngày · tuần ·
 * tháng.
 *
 * Đây là câu QĐ-NP5 nêu ra để giải thích vì sao đơn nghỉ phải là BẢNG chứ không
 * phải ô JSON của giấy GNP: hỏi được nó trên cột `DATE` có chỉ mục, còn quét
 * `JSON_EXTRACT` thì vừa chậm vừa không đánh chỉ mục được.
 *
 * ⚠️ Lọc theo **GIAO NHAU của khoảng**, không theo `from_date` đơn lẻ — một đơn
 * nghỉ từ tuần trước kéo sang tuần này phải lọt vào. Backend nhận đúng hai tham
 * số `from_date` / `to_date` cho việc đó, và `rangeOf` dựng chúng theo chế độ
 * đang xem (chế độ tháng hỏi theo cả lưới 42 ô, không theo mốc đầu/cuối tháng).
 *
 * ⚠️ **Chỉ hiện đơn CÒN HIỆU LỰC** — chờ duyệt và đã duyệt. Đơn nháp chưa ai
 * duyệt, đơn bị từ chối / đã hủy thì người ta vẫn đi làm; vẽ chúng lên lịch là
 * xếp việc sai người.
 *
 * Chế độ và mốc đang xem nằm trên URL để dán được đường dẫn cho nhau.
 */

/** Trần số đơn nạp một lượt. Lưới tháng hỏi 42 ngày nên cần rộng tay. */
const PAGE_SIZE = 500

/**
 * Mảng rỗng DÙNG CHUNG cho ngày không ai nghỉ.
 *
 * ⚠️ Không viết `?? []` tại chỗ: mỗi lần gọi sẽ ra một mảng MỚI, nên `useMemo`
 * ở màn con thấy tham chiếu khác và tính lại toàn bộ mỗi lần vẽ — với lưới tháng
 * là 42 lần cho một lượt render.
 */
const NO_REQUESTS: LeaveRequest[] = []

export function LeaveCalendarPage() {
  const [mode, setMode] = useUrlParamState('mode', 'month')
  const [anchorISO, setAnchorISO] = useUrlParamState('date', toISODate(new Date()))
  const setUrlParams = useSetUrlParams()

  //  Dựng `Date` từ chuỗi `YYYY-MM-DD` bằng ba số rời, KHÔNG bằng
  //  `new Date('2026-09-01')`: dạng chuỗi đó được hiểu là UTC, và ở múi +7 nó
  //  ra 07:00 ngày 01/09 — đúng ngày, nhưng `new Date('2026-09-01')` ở múi âm
  //  thì lùi hẳn một ngày. Tách số là không phụ thuộc múi giờ.
  const anchor = useMemo(() => {
    const [y, m, d] = anchorISO.split('-').map(Number)
    if (!y || !m || !d) return new Date()
    return new Date(y, m - 1, d)
  }, [anchorISO])

  const calendarMode = (['day', 'week', 'month'] as const).includes(mode as CalendarMode)
    ? (mode as CalendarMode)
    : 'month'

  const range = useMemo(() => rangeOf(anchor, calendarMode), [anchor, calendarMode])

  const { data, isLoading } = useLeaveRequests({
    page: 1,
    page_size: PAGE_SIZE,
    from_date: range.from,
    to_date: range.to,
  })
  const { data: holidayData } = useHolidays()

  const shown = useMemo(
    () =>
      (data?.items ?? []).filter(
        (r) => r.status === LEAVE_STATUS.PENDING || r.status === LEAVE_STATUS.APPROVED,
      ),
    [data],
  )

  //  Gom theo NGÀY một lượt thay vì để mỗi ô tự quét cả danh sách: lưới tháng có
  //  42 ô × 500 đơn là 21.000 lượt so sánh cho mỗi lần vẽ lại.
  const byDay = useMemo(() => {
    const map = new Map<string, LeaveRequest[]>()
    for (const r of shown) {
      //  Rải đơn ra từng ngày nó phủ. Cắt theo khoảng đang xem để đơn nghỉ dài
      //  ba tháng không sinh ra chín chục khóa vô ích.
      const from = r.from_date > range.from ? r.from_date : range.from
      const to = r.to_date < range.to ? r.to_date : range.to
      const [fy, fm, fd] = from.split('-').map(Number)
      for (let d = new Date(fy, fm - 1, fd); toISODate(d) <= to; d.setDate(d.getDate() + 1)) {
        const iso = toISODate(d)
        const list = map.get(iso)
        if (list) list.push(r)
        else map.set(iso, [r])
      }
    }
    return map
  }, [shown, range])

  //  `useCallback` để hàm này ỔN ĐỊNH giữa các lần vẽ: màn con dùng nó bên
  //  trong `useMemo`, mà một hàm mới mỗi render thì mọi memo bên dưới thành vô
  //  nghĩa (React Compiler cũng báo lỗi `preserve-manual-memoization`).
  const requestsOn = useCallback((iso: string) => byDay.get(iso) ?? NO_REQUESTS, [byDay])

  //  Bấm vào một ngày ở lưới tháng / tuần → phóng to đúng ngày đó. Đây là lối
  //  thoát cho hai chế độ kia khi ô chật không chứa hết người nghỉ.
  //
  //  ⚠️ Đổi CẢ HAI param trong MỘT lượt. Gọi `setAnchorISO(...)` rồi
  //  `setMode(...)` liên tiếp thì lần sau ghi đè lần trước và ngày bị mất —
  //  xem `useSetUrlParams`.
  const pickDay = (d: Date) => setUrlParams({ mode: 'day', date: toISODate(d) })
  const todayISO = toISODate(new Date())
  const holidays = holidayData?.items ?? []

  return (
    <PageContainer fill>
      <PageHeader
        title="Lịch nghỉ"
        description="Ai nghỉ ngày nào — chỉ hiện đơn đang chờ duyệt và đã duyệt."
      />

      <LeaveSectionTabs />

      {/*  Thanh điều hướng đặt DƯỚI tiêu đề, không nhét vào `actions`: nó có
           năm cụm điều khiển và cần cả chiều ngang, còn khe `actions` thì chia
           chỗ với tiêu đề nên mọi thứ bị ép lại thành một dải chật. */}
      <div className="shrink-0 space-y-2.5 pb-3">
        <LeaveCalendarToolbar
          anchor={anchor}
          mode={calendarMode}
          onModeChange={setMode}
          onShift={(step) => setAnchorISO(toISODate(shiftAnchor(anchor, calendarMode, step)))}
          onJump={(d) => setAnchorISO(toISODate(d))}
        />

        {/*  Chú thích màu: hai màu ở đây là thứ duy nhất phân biệt "chắc chắn
             nghỉ" với "có thể nghỉ", mà ô lịch chật quá không ghi chữ được. */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          {/*  Ký hiệu ở đây phải TRÙNG với chip trong lịch (chấm tròn màu),
               không phải một hình khác cùng màu — chú thích mà vẽ khác thứ nó
               chú thích thì người đọc phải tự bắc cầu. */}
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-emerald-500" />
            Đã duyệt
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-amber-500" />
            Chờ duyệt
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-3 rounded-sm bg-rose-100 dark:bg-rose-950" />
            Ngày lễ
          </span>
          {isLoading && <span>Đang tải…</span>}
        </div>
      </div>

      {calendarMode === 'month' && (
        <LeaveCalendarMonthGrid
          anchor={anchor}
          requestsOn={requestsOn}
          holidays={holidays}
          todayISO={todayISO}
          onPickDay={pickDay}
        />
      )}
      {calendarMode === 'week' && (
        <LeaveCalendarWeekGrid
          anchor={anchor}
          requestsOn={requestsOn}
          holidays={holidays}
          todayISO={todayISO}
          onPickDay={pickDay}
        />
      )}
      {calendarMode === 'day' && (
        <LeaveCalendarDayView anchor={anchor} requestsOn={requestsOn} holidays={holidays} />
      )}
    </PageContainer>
  )
}
