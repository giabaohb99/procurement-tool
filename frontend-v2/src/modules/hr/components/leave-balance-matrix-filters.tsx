import { useClearUrlParams } from '@/shared/hooks/use-url-param-state'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import type { LeaveBalanceMatrixEmployeeStatus } from '../api/leave-balance-matrix-api'
import {
  MATRIX_ALL_DEPARTMENTS,
  MATRIX_STATUS_OPTIONS,
  MATRIX_STATUS_WORKING,
} from '../utils/leave-balance-matrix-filters'
import { LeaveBalanceYearSelect } from './leave-balance-year-select'

interface LeaveBalanceMatrixFiltersProps {
  /** `undefined` = không đọc được danh mục phòng ban → không dựng ô đó. */
  departments: readonly { id: number; name: string }[] | undefined
  departmentId: string
  onDepartmentChange: (value: string) => void
  status: LeaveBalanceMatrixEmployeeStatus
  onStatusChange: (value: string) => void
  year: string
  onYearChange: (year: string) => void
}

/**
 * Ba ô lọc của thẻ "Theo nhân sự" (phòng ban · trạng thái nhân sự · năm), tách khỏi
 * `leave-balance-matrix-table.tsx` (review L6 của duoc-CR-717). Dựng hai lần — hàng ngang ở màn rộng, tờ
 * trượt ở màn hẹp — state ở URL nên hai bản luôn nói cùng một giá trị.
 */
export function LeaveBalanceMatrixFilters({
  departments,
  departmentId,
  onDepartmentChange,
  status,
  onStatusChange,
  year,
  onYearChange,
}: LeaveBalanceMatrixFiltersProps) {
  const clearUrlParams = useClearUrlParams()
  const currentYear = String(new Date().getFullYear())

  const departmentSelect = departments && (
    <Select value={departmentId} onValueChange={onDepartmentChange}>
      <SelectTrigger className="w-full md:w-44" aria-label="Lọc theo phòng ban">
        <SelectValue placeholder="Phòng ban" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={MATRIX_ALL_DEPARTMENTS}>Tất cả phòng ban</SelectItem>
        {departments.map((d) => (
          <SelectItem key={d.id} value={String(d.id)}>
            {d.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
  const statusSelect = (
    <Select value={status} onValueChange={onStatusChange}>
      <SelectTrigger className="w-full md:w-36" aria-label="Trạng thái nhân sự">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {MATRIX_STATUS_OPTIONS.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
  const yearSelect = <LeaveBalanceYearSelect value={year} onChange={onYearChange} />

  return (
    <>
      <QuickFilterSheet
        activeCount={
          (departmentId !== MATRIX_ALL_DEPARTMENTS ? 1 : 0) +
          (status !== MATRIX_STATUS_WORKING ? 1 : 0) +
          (year !== currentYear ? 1 : 0)
        }
        //  Một lượt ghi URL — gọi từng setter liền nhau thì chỉ lần cuối ăn (`useClearUrlParams`).
        onClearAll={() => clearUrlParams(['department_id', 'employee_status', 'year'])}
      >
        {departmentSelect && <QuickFilterField label="Phòng ban">{departmentSelect}</QuickFilterField>}
        <QuickFilterField label="Trạng thái nhân sự">{statusSelect}</QuickFilterField>
        <QuickFilterField label="Năm">{yearSelect}</QuickFilterField>
      </QuickFilterSheet>
      <div className="hidden items-center gap-3 md:flex">
        {departmentSelect}
        {statusSelect}
        {yearSelect}
      </div>
    </>
  )
}
