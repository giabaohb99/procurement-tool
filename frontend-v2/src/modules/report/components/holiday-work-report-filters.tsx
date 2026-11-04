import { CalendarDays } from 'lucide-react'
import { useEffect } from 'react'

import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { ReportDepartmentFilter } from './report-department-filter'

/** Tên tham số backend (`holiday_work_report_controller`) — đổi tên là bộ lọc im lặng không ăn. */
const HOLIDAY_WORK_PARAM = { dayKind: 'day_kind', includePending: 'include_pending' } as const

/** `day_kind` vắng = 0 = mọi loại ngày ở backend — mặc định KHÔNG ghi URL. Ngoài 0-2 là 422. */
const DAY_KIND_ALL = '0'
const DAY_KIND_OPTIONS = [
  { value: DAY_KIND_ALL, label: 'Mọi loại ngày' },
  { value: '1', label: 'Ngày lễ' },
  { value: '2', label: 'Ngày nghỉ theo lịch' },
] as const

/** `include_pending` vắng = chỉ phiếu Đã duyệt (D8a). Bật = `1`. */
const PENDING_OFF = '0'
const PENDING_ON = '1'
/**
 * Bộ chữ backend coi là BẬT (`valid_flag`: 1/true/yes/on). Link gõ tay `?include_pending=yes` mà
 * công tắc chỉ nhận `1` thì màn hình nói "tắt" trong khi số liệu đã gồm phiếu chờ duyệt.
 */
const TRUTHY = new Set(['1', 'true', 'yes', 'on'])

/**
 * Ô lọc riêng của báo cáo "Làm việc vào ngày lễ, ngày nghỉ" (duoc-CR-717, khóa 30): phòng ban (ghi
 * trên phiếu nghỉ bù) · loại ngày · công tắc "Gồm phiếu chờ duyệt". Giá trị nằm thẳng trên URL —
 * `useReportFilters().queryParams` tự gom gửi backend.
 */
export function HolidayWorkReportFilters() {
  const [rawDayKind, setDayKind] = useUrlParamState(HOLIDAY_WORK_PARAM.dayKind, DAY_KIND_ALL)
  const [pending, setPending] = useUrlParamState(HOLIDAY_WORK_PARAM.includePending, PENDING_OFF)
  //  Link gõ tay `?day_kind=9`: hiện như mặc định thay vì một ô chọn trống, VÀ gỡ khỏi URL (review L2) —
  //  `useReportFilters().queryParams` gửi nguyên URL lên backend, để lại là mọi lượt gọi ăn 422.
  const isValidDayKind = DAY_KIND_OPTIONS.some((o) => o.value === rawDayKind)
  const dayKind = isValidDayKind ? rawDayKind : DAY_KIND_ALL
  useEffect(() => {
    if (!isValidDayKind) setDayKind(DAY_KIND_ALL)
  }, [isValidDayKind, setDayKind])
  return (
    <>
      <ReportDepartmentFilter />
      <Select value={dayKind} onValueChange={setDayKind}>
        <SelectTrigger className="w-auto min-w-40 max-md:min-w-0 max-md:flex-1" aria-label="Loại ngày">
          <CalendarDays className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {DAY_KIND_OPTIONS.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <div className="flex h-9 items-center gap-2">
        <Switch
          id="holiday-work-include-pending"
          checked={TRUTHY.has(pending.trim().toLowerCase())}
          onCheckedChange={(checked) => setPending(checked ? PENDING_ON : PENDING_OFF)}
        />
        <Label htmlFor="holiday-work-include-pending" className="whitespace-nowrap">
          Gồm phiếu chờ duyệt
        </Label>
      </div>
    </>
  )
}
