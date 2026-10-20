import { Network } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

export const ALL_DEPARTMENTS = 'all'

/** Ô lọc phòng ban của «Mức dùng chức năng»; giá trị nằm trên URL (`department_id`). Thiếu quyền đọc phòng ban thì ẩn. */
export function FeatureUsageDepartmentFilter() {
  const { can } = usePermission()
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL_DEPARTMENTS)
  const { data } = useDepartments({ page_size: 500, is_active: true }, { enabled: can('department', 'read') })
  if (!can('department', 'read')) return null
  return (
    <Select value={departmentId} onValueChange={setDepartmentId}>
      <SelectTrigger className="w-auto min-w-40 max-md:min-w-0 max-md:flex-1" aria-label="Phòng ban">
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
