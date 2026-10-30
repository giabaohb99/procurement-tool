import { UserCheck } from 'lucide-react'

import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

/** Mặc định của backend (`employee_status` vắng = `working`) — KHÔNG ghi lên URL. */
export const EMPLOYEE_STATUS_WORKING = 'working'

/** Ba lựa chọn của tham số `employee_status` (Quỹ phép năm, duoc-CR-686) — khóa khớp backend. */
const OPTIONS = [
  { value: EMPLOYEE_STATUS_WORKING, label: 'Đang làm' },
  { value: 'resigned', label: 'Đã nghỉ' },
  { value: 'all', label: 'Tất cả nhân sự' },
] as const

/**
 * Ô lọc trạng thái nhân sự của người giữ quỹ. Giá trị trên URL (`employee_status`), mặc
 * định "Đang làm" thì xóa khỏi URL — link cũ không có tham số này vẫn mở đúng như trước.
 */
export function ReportEmployeeStatusFilter() {
  const [status, setStatus] = useUrlParamState('employee_status', EMPLOYEE_STATUS_WORKING)
  //  Link gõ tay `?employee_status=xyz`: hiện như mặc định thay vì một ô chọn trống.
  const value = OPTIONS.some((o) => o.value === status) ? status : EMPLOYEE_STATUS_WORKING
  return (
    <Select value={value} onValueChange={setStatus}>
      <SelectTrigger className="w-auto min-w-36 max-md:min-w-0 max-md:flex-1" aria-label="Trạng thái nhân sự">
        <UserCheck className="size-4 shrink-0 text-muted-foreground" aria-hidden />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {OPTIONS.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
