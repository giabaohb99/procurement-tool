import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { CYCLE_KIND, CYCLE_ROLE } from '@/shared/constants/statuses'
import { useActiveTaskTypes } from '@/modules/work/hooks/use-task-types'

import { ReportDepartmentFilter } from '../report-department-filter'

export const ALL = 'all'
/** `CycleKind.WORK_TASK` (backend) = 10 — chỉ task Dự án mới có loại việc. */
export const WORK_TASK_KIND = '10'
/** `CycleRole.HANDLER` = 2. */
export const DEFAULT_ROLE = '2'

function Pick({ label, value, onChange, options, all }: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
  all?: string
}) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-auto min-w-40 max-md:min-w-0 max-md:flex-1" aria-label={label}>
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        {all && <SelectItem value={ALL}>{all}</SelectItem>}
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

/** Lọc riêng của "Năng lực theo loại việc": phòng ban · loại phiếu · loại việc (khi là việc Dự án) · vai. Giá trị nằm trên URL. */
export function WorkCapabilityFilters() {
  const [kind, setKind] = useUrlParamState('kind', ALL)
  const [taskType, setTaskType] = useUrlParamState('task_type_id', ALL)
  const [role, setRole] = useUrlParamState('role', DEFAULT_ROLE)
  const { data: taskTypes } = useActiveTaskTypes()
  return (
    <>
      <ReportDepartmentFilter />
      <Pick label="Loại phiếu" value={kind} onChange={setKind} all="Tất cả loại phiếu" options={CYCLE_KIND.map((k) => ({ value: k.value, label: k.label }))} />
      {kind === WORK_TASK_KIND && (
        <Pick
          label="Loại việc"
          value={taskType}
          onChange={setTaskType}
          all="Tất cả loại việc"
          options={(taskTypes ?? []).map((t) => ({ value: String(t.id), label: t.name }))}
        />
      )}
      <Pick label="Vai" value={role} onChange={setRole} options={CYCLE_ROLE.map((r) => ({ value: r.value, label: r.label }))} />
    </>
  )
}
