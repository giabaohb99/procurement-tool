import { AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { ENTITY_LABELS, entityLink } from '@/modules/approval/helpers/entity-link'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { SearchSelect } from '@/shared/ui/search-select'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import {
  useEmployeePendingWork,
  useHandoverAllPendingTasks,
  useReassignPendingTask,
} from '../hooks/use-employee-pending-work'
import { useEmployees } from '../hooks/use-employees'

interface EmployeePendingWorkPanelProps {
  employeeId: number
}

/**
 * Khung "Việc đang giữ" trước khi khóa tài khoản / cho nghỉ việc (duoc-CR-665, V0-4).
 *
 * Hai loại: việc DUYỆT còn treo (chuyển được từng việc hoặc chuyển hết, cần `approval_flow.write`)
 * và bước LUỒNG duyệt chỉ đích danh người này (chỉ nêu + dẫn tới luồng, không sửa tại đây).
 * Không xem được danh sách (thiếu quyền / lỗi) thì nói ra chứ không giả vờ "không có việc".
 */
export function EmployeePendingWorkPanel({ employeeId }: EmployeePendingWorkPanelProps) {
  const { can } = usePermission()
  const canTransfer = can('approval_flow', 'write')
  const { data, isLoading, isError } = useEmployeePendingWork(employeeId)
  const { data: colleagues } = useEmployees({ page_size: 500, is_active: true }, { enabled: canTransfer })
  const reassign = useReassignPendingTask(employeeId)
  const handoverAll = useHandoverAllPendingTasks(employeeId)
  const [target, setTarget] = useState('')

  const options = useMemo(
    () =>
      (colleagues?.items ?? [])
        .filter((emp) => emp.id !== employeeId)
        .map((emp) => ({ value: String(emp.id), label: `${emp.full_name} (${emp.code})` })),
    [colleagues, employeeId],
  )

  if (isLoading) return <Skeleton className="h-16 w-full" />
  if (isError || !data) {
    return (
      <p className="text-sm text-muted-foreground">
        Không xem được danh sách việc đang giữ (thiếu quyền hoặc lỗi). Hãy tự kiểm tra ở màn Báo
        cáo duyệt trước khi khóa.
      </p>
    )
  }
  if (data.total_tasks === 0 && data.total_flow_steps === 0) {
    return (
      <p className="flex items-center gap-2 text-sm text-muted-foreground">
        <CheckCircle2 className="size-4 text-emerald-600" />
        Người này không còn việc duyệt nào đang treo.
      </p>
    )
  }

  const toEmployeeId = Number(target) || 0
  const busy = reassign.isPending || handoverAll.isPending

  return (
    <div className="space-y-3 text-sm" data-testid="pending-work-panel">
      {data.total_tasks > 0 && (
        <div className="space-y-2">
          <p className="flex items-start gap-2 font-medium">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />
            {data.total_tasks} việc duyệt đang chờ người này — khóa mà không chuyển thì phiếu KẸT.
          </p>
          {canTransfer ? (
            <div className="flex flex-wrap items-center gap-2">
              <div className="w-64">
                <SearchSelect
                  value={target}
                  onChange={setTarget}
                  options={options}
                  placeholder="Chuyển cho…"
                  searchPlaceholder="Tìm theo tên hoặc mã…"
                />
              </div>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={!toEmployeeId || busy}
                onClick={() => handoverAll.mutate({ toEmployeeId })}
              >
                {handoverAll.isPending && <Loader2 className="size-4 animate-spin" />}
                Chuyển hết ({data.total_tasks})
              </Button>
            </div>
          ) : (
            <p className="text-muted-foreground">
              Bạn không có quyền chuyển việc duyệt (cần quyền ghi <em>Luồng duyệt</em>) — nhờ quản trị
              luồng chuyển giúp trước khi khóa.
            </p>
          )}
          <ul className="divide-y rounded-md border">
            {data.tasks.map((task) => {
              const link = task.hidden ? null : entityLink(task.entity, task.entity_id)
              const label = task.hidden
                ? `${ENTITY_LABELS[task.entity] ?? task.entity} · (bạn không có quyền xem phiếu này)`
                : `${ENTITY_LABELS[task.entity] ?? task.entity} · ${task.entity_code || `#${task.entity_id}`}`
              return (
                <li key={task.task_id} className="flex items-center gap-2 p-2">
                  <div className="min-w-0 flex-1">
                    <p className="truncate">
                      {link ? (
                        <Link to={link} target="_blank" className="text-primary hover:underline">
                          {label}
                        </Link>
                      ) : (
                        label
                      )}
                      {task.entity_title ? ` — ${task.entity_title}` : ''}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {task.node_name} · {task.status_label}
                      {task.started_by_name ? ` · người trình: ${task.started_by_name}` : ''}
                      {task.due_at ? ` · hạn ${formatDate(task.due_at)}` : ''}
                      {task.is_overdue ? ' (quá hạn)' : ''}
                    </p>
                  </div>
                  {canTransfer && (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={!toEmployeeId || busy}
                      onClick={() => reassign.mutate({ taskId: task.task_id, toEmployeeId })}
                    >
                      Chuyển
                    </Button>
                  )}
                </li>
              )
            })}
          </ul>
          {data.total_tasks > data.tasks.length && (
            <p className="text-xs text-muted-foreground">
              Chỉ hiện {data.tasks.length}/{data.total_tasks} việc đầu — chuyển hết sẽ lấy đủ.
            </p>
          )}
        </div>
      )}

      {data.total_flow_steps > 0 && (
        <div className="space-y-1">
          <p className="flex items-start gap-2 font-medium">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />
            {data.total_flow_steps} bước luồng duyệt chỉ đích danh người này — phiếu MỚI sẽ lùi
            sang người dự phòng hoặc kẹt; nên đổi người duyệt ở luồng.
          </p>
          <ul className="space-y-0.5 pl-6">
            {data.flow_steps.map((step) => (
              <li key={step.node_id}>
                <Link
                  to={appRoutes.approval.flowDetail(step.flow_id)}
                  target="_blank"
                  className="text-primary hover:underline"
                >
                  {step.flow_name || step.flow_code}
                </Link>{' '}
                · {ENTITY_LABELS[step.entity] ?? step.entity} · bước {step.node_seq}{' '}
                {step.node_name} ({step.role === 'fallback' ? 'người dự phòng' : 'người duyệt'})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
