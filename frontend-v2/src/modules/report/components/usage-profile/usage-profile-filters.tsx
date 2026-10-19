import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useRoles } from '@/modules/hr/hooks/use-roles'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { USAGE_STYLE } from '@/shared/constants/statuses'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'


export const ALL = 'all'

interface UsageProfileFiltersProps {
  keyword: string
  onKeywordChange: (value: string) => void
}

/** Ô lọc riêng của danh sách hồ sơ: tìm tên/mã · phòng ban · vai trò · kiểu làm việc. Giá trị nằm trên URL. */
export function UsageProfileFilters({ keyword, onKeywordChange }: UsageProfileFiltersProps) {
  const { can } = usePermission()
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [roleId, setRoleId] = useUrlParamState('role_id', ALL)
  const [labelParam, setLabelParam] = useUrlParamState('label', '')

  //  Hai danh mục mượn của phân hệ khác — thiếu quyền đọc thì tắt hẳn, kẻo mở trang là ăn toast 403.
  const { data: departments } = useDepartments({ page_size: 500, is_active: true }, { enabled: can('department', 'read') })
  const { data: roles } = useRoles()

  const labelIds = useMemo(() => labelParam.split(',').filter(Boolean).map(Number), [labelParam])
  const labelOptions = useMemo(
    () => USAGE_STYLE.map((o) => ({ id: Number(o.value), label: o.label })),
    [],
  )

  return (
    <div className="flex flex-wrap items-start gap-2">
      <SearchField value={keyword} onChange={onKeywordChange} placeholder="Tìm tên, mã NV…" className="md:w-56 md:flex-none" />
      <Select value={departmentId} onValueChange={setDepartmentId}>
        <SelectTrigger className="w-auto min-w-40" aria-label="Phòng ban">
          <SelectValue placeholder="Phòng ban" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả phòng ban</SelectItem>
          {departments?.items.map((d) => (
            <SelectItem key={d.id} value={String(d.id)}>
              {d.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={roleId} onValueChange={setRoleId}>
        <SelectTrigger className="w-auto min-w-40" aria-label="Vai trò">
          <SelectValue placeholder="Vai trò" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả vai trò</SelectItem>
          {roles?.map((r) => (
            <SelectItem key={r.id} value={String(r.id)}>
              {r.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <div className="min-w-48">
        <MultiPicker
          value={labelIds}
          onChange={(ids) => setLabelParam(ids.join(','))}
          options={labelOptions}
          placeholder="Kiểu làm việc"
          searchPlaceholder="Tìm kiểu…"
          emptyMessage="Không có kiểu nào."
        />
      </div>
    </div>
  )
}
