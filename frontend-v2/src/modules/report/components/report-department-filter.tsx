import { Network } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

/** Mốc «Tất cả phòng ban» — chuỗi, KHÔNG `0`: `department_id=0` là nhóm «chưa gắn phòng» thật. */
export const ALL_DEPARTMENTS = 'all'

/**
 * Ô lọc phòng ban dùng chung của phân hệ Báo cáo (duoc-CR-655 → dùng chung từ duoc-CR-686).
 * Giá trị nằm thẳng trên URL (`department_id`), mặc định «Tất cả» thì KHÔNG ghi URL —
 * `useReportFilters().queryParams` tự gom tham số này gửi backend, trang không cần biết.
 * Thiếu `department.read` thì ẩn hẳn (danh mục phòng ban mượn của Nhân sự, gọi là ăn 403).
 */
export function ReportDepartmentFilter() {
  const { can } = usePermission()
  const canRead = can('department', 'read')
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL_DEPARTMENTS)
  const { data } = useDepartments({ page_size: 500, is_active: true }, { enabled: canRead })
  if (!canRead) return null
  return (
    <Select value={departmentId} onValueChange={setDepartmentId}>
      <SelectTrigger className="w-auto min-w-40 max-md:min-w-36 max-md:flex-1" aria-label="Phòng ban">
        <Network className="size-4 shrink-0 text-muted-foreground" aria-hidden />
        <SelectValue placeholder="Phòng ban" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL_DEPARTMENTS}>Tất cả phòng ban</SelectItem>
        {data?.items.map((d) => (
          <SelectItem key={d.id} value={String(d.id)}>
            {d.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
