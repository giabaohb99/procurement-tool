import { ArrowLeft, Check, ExternalLink, Plus, Save, Trash2, X } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { formatDateTime } from '@/shared/utils/format-date'
import { AiPlanRowEditor, type AiPlanPersonOption } from '../components/ai-plan-row-editor'
import { AiPlanStatusBadge } from '../components/ai-plan-status-badge'
import { WorkSidebarPeekButton } from '../components/work-sidebar-peek-button'
import { useAiPlan, useAiPlanActions } from '../hooks/use-ai-plans'
import { useActiveTaskTypes } from '../hooks/use-task-types'
import {
  AI_PLAN_STATUS_PENDING,
  AI_PLAN_STATUS_REJECTED,
  type AiPlanDetail,
} from '../types/ai-plan'
import {
  addPhase,
  addSubtask,
  addTask,
  findBlockingProblems,
  findLocalProblems,
  mapServerProblems,
  readPlanProblems,
  removePhase,
  removeSubtask,
  removeTask,
  renamePhase,
  toEditablePlan,
  toPlanPayload,
  updateSubtask,
  updateTask,
  type EditablePlan,
  type PlanRowProblem,
} from '../utils/ai-plan-edit'

/**
 * Màn *Duyệt kế hoạch AI* (kh-AI1-3, doc `erp/tai-lieu-ai/22` §5.2): chính người hỏi AI
 * xem bản kế hoạch, sửa người / giờ / dòng, rồi Duyệt — lúc đó máy chủ mới tạo việc.
 *
 * Đường `/project/ai-plans/:planId` phải KHỚP `REVIEW_PATH` của máy chủ (link trong tin
 * của bot). Đề xuất của người khác trả 404 như đề xuất không tồn tại.
 */
export function AiPlanDetailPage() {
  const { planId } = useParams()
  const id = Number(planId)
  const validId = Number.isInteger(id) && id > 0
  const { data, isLoading, isError, dataUpdatedAt } = useAiPlan(validId ? id : 0)

  if (!validId || isError) {
    return (
      <PageShell>
        <p className="text-sm text-muted-foreground">
          Không tìm thấy kế hoạch này, hoặc đây không phải đề xuất của bạn.
        </p>
      </PageShell>
    )
  }
  if (isLoading || !data) {
    return (
      <PageShell>
        <p className="text-sm text-muted-foreground">Đang tải kế hoạch…</p>
      </PageShell>
    )
  }
  //  Dựng lại bộ sửa mỗi khi máy chủ trả bản mới (lưu xong, từ chối) — bản đã chuẩn
  //  hóa có `key` mới cho dòng vừa thêm, giữ bản cũ là lần lưu sau gửi `key` rỗng lần nữa.
  return <AiPlanEditor key={`${data.id}:${dataUpdatedAt}`} detail={data} />
}

function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4 lg:p-6">
      <div className="flex items-center gap-2">
        <WorkSidebarPeekButton />
        <Button asChild variant="ghost" size="sm">
          <Link to={appRoutes.project.aiPlans}>
            <ArrowLeft className="size-4" />
            Danh sách kế hoạch AI
          </Link>
        </Button>
      </div>
      {children}
    </div>
  )
}

function messagesFor(problems: PlanRowProblem[], where: { phaseUid?: string; taskUid?: string; subtaskUid?: string }) {
  return problems
    .filter(
      (p) => p.phaseUid === where.phaseUid && p.taskUid === where.taskUid && p.subtaskUid === where.subtaskUid,
    )
    .map((p) => p.message)
}

function AiPlanEditor({ detail }: { detail: AiPlanDetail }) {
  const navigate = useNavigate()
  const { can } = usePermission()
  const pending = detail.status === AI_PLAN_STATUS_PENDING
  const canWrite = can('work_task', 'create')
  const readOnly = !pending || !canWrite

  const [plan, setPlan] = useState<EditablePlan>(() => toEditablePlan(detail.plan))
  const [dirty, setDirty] = useState(false)
  const [serverProblems, setServerProblems] = useState<PlanRowProblem[]>([])
  const [rejectOpen, setRejectOpen] = useState(false)
  //  `disabled={isPending}` không chặn được bấm đúp (bẫy biểu mẫu duoc-CR-317): duyệt hai
  //  lần là hai lượt dựng bảng. Chốt bằng ref đổi ngay trong tick.
  const busy = useRef(false)

  const { save, approve, reject } = useAiPlanActions(detail.id)
  const { data: taskTypes = [] } = useActiveTaskTypes()
  //  Danh bạ là dữ liệu của phân hệ Nhân sự: thiếu `employee.read` thì không gọi (khỏi
  //  toast 403), ô chọn chỉ còn những người đã có trong kế hoạch.
  const { data: directory } = useEmployees(
    { page_size: 500, is_active: true },
    { enabled: can('employee', 'read') },
  )

  const people = useMemo<AiPlanPersonOption[]>(() => {
    const options = new Map<number, AiPlanPersonOption>()
    for (const employee of directory?.items ?? []) {
      options.set(employee.id, {
        employee_id: employee.id,
        code: employee.code,
        name: employee.full_name,
        active: true,
      })
    }
    for (const phase of plan.phases) {
      for (const task of phase.tasks) {
        for (const person of [...task.assignees, ...task.subtasks.flatMap((sub) => sub.assignees)]) {
          if (!options.has(person.employee_id)) {
            options.set(person.employee_id, { ...person, active: !directory })
          }
        }
      }
    }
    return [...options.values()]
  }, [directory, plan.phases])

  const localProblems = useMemo(() => findLocalProblems(plan), [plan])
  const problems = [...localProblems, ...serverProblems]
  const planLevel = messagesFor(problems, {})
  const taskCount = plan.phases.reduce((sum, phase) => sum + phase.tasks.length, 0)

  const edit = (next: EditablePlan) => {
    setPlan(next)
    setDirty(true)
    //  Lỗi máy chủ trỏ VỊ TRÍ của lần gửi trước — sửa xong là vị trí có thể đã lệch.
    setServerProblems([])
  }

  const run = async (action: () => Promise<void>) => {
    if (busy.current) return
    busy.current = true
    try {
      await action()
    } catch (error) {
      setServerProblems(mapServerProblems(readPlanProblems(error), plan))
    } finally {
      busy.current = false
    }
  }

  const handleSave = () =>
    run(async () => {
      await save.mutateAsync(toPlanPayload(plan))
    })

  const handleApprove = () =>
    run(async () => {
      const ok = await confirm({
        title: 'Duyệt kế hoạch này?',
        message: `Hệ thống sẽ tạo một dự án mới với ${taskCount} việc theo đúng bản đang hiện. Sau khi duyệt không sửa kế hoạch ở đây được nữa — sửa trực tiếp trong dự án.`,
        confirmLabel: 'Duyệt và tạo việc',
        tone: 'default',
      })
      if (!ok) return
      const result = await approve.mutateAsync(toPlanPayload(plan))
      navigate(result.list_url || appRoutes.project.detail(result.list_id))
    })

  const handleReject = (reason: string) =>
    run(async () => {
      await reject.mutateAsync(reason)
      setRejectOpen(false)
    })

  const blockingCount = findBlockingProblems(localProblems).length
  const blocked = blockingCount > 0
  const working = save.isPending || approve.isPending || reject.isPending

  return (
    <PageShell>
      <Card className="space-y-3 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1 space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <AiPlanStatusBadge status={detail.status} label={detail.status_label} />
              {detail.channel_label && (
                <span className="text-xs text-muted-foreground">Hỏi qua {detail.channel_label}</span>
              )}
              {detail.created_at && (
                <span className="text-xs text-muted-foreground">· Lập {formatDateTime(detail.created_at)}</span>
              )}
            </div>
            <Input
              value={plan.title}
              readOnly={readOnly}
              aria-label="Tên kế hoạch"
              maxLength={200}
              className="h-10 text-lg font-semibold"
              onChange={(event) => edit({ ...plan, title: event.target.value })}
            />
          </div>
          <div className="w-44 space-y-1">
            <span className="text-xs text-muted-foreground">Hạn chót cả kế hoạch</span>
            <DatePicker
              value={plan.deadline}
              onChange={(value) => edit({ ...plan, deadline: value })}
              placeholder="Chưa đặt hạn"
              size="sm"
              clearable
              disabled={readOnly}
            />
          </div>
        </div>

        {detail.goal && (
          <p className="text-sm">
            <span className="font-medium">Mục tiêu bạn nói với AI:</span> {detail.goal}
          </p>
        )}
        {plan.assumptions.length > 0 && (
          <div className="text-sm">
            <p className="font-medium">AI đã giả định:</p>
            <ul className="list-disc pl-5 text-muted-foreground">
              {plan.assumptions.map((assumption, index) => (
                <li key={index}>{assumption}</li>
              ))}
            </ul>
          </div>
        )}

        {detail.status === AI_PLAN_STATUS_REJECTED && detail.reject_reason && (
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">Lý do từ chối:</span> {detail.reject_reason}
          </p>
        )}
        {detail.list_url && (
          <Button asChild variant="outline" size="sm">
            <Link to={detail.list_url}>
              <ExternalLink className="size-4" />
              Mở dự án đã tạo
            </Link>
          </Button>
        )}
        {pending && !canWrite && (
          <p className="text-sm text-muted-foreground">
            Bạn chỉ có quyền xem việc nên không sửa hay duyệt được kế hoạch này.
          </p>
        )}

        {planLevel.length > 0 && (
          <ul className="space-y-0.5 text-sm text-destructive" role="alert">
            {planLevel.map((message, index) => (
              <li key={index}>{message}</li>
            ))}
          </ul>
        )}
      </Card>

      {plan.phases.map((phase, phaseIndex) => {
        //  Lỗi cấp giai đoạn giữ cả cờ `warning`: giai đoạn rỗng chỉ là lời nhắc (vàng).
        const phaseProblems = problems.filter((p) => p.phaseUid === phase.uid && !p.taskUid)
        return (
          <Card key={phase.uid} className="space-y-3 p-4" aria-label={`Giai đoạn ${phaseIndex + 1}`}>
            <div className="flex items-center gap-2">
              <span className="shrink-0 text-sm text-muted-foreground">Giai đoạn {phaseIndex + 1}</span>
              <Input
                value={phase.name}
                readOnly={readOnly}
                aria-label={`Tên giai đoạn ${phaseIndex + 1}`}
                maxLength={100}
                className="h-9 flex-1 font-medium"
                onChange={(event) => edit(renamePhase(plan, phase.uid, event.target.value))}
              />
              {!readOnly && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  title="Bỏ cả giai đoạn"
                  aria-label={`Bỏ giai đoạn ${phase.name}`}
                  onClick={() => edit(removePhase(plan, phase.uid))}
                >
                  <Trash2 className="size-4 text-muted-foreground" />
                </Button>
              )}
            </div>
            {phaseProblems.length > 0 && (
              <ul className="space-y-0.5 text-xs" role="alert">
                {phaseProblems.map((problem, index) => (
                  <li key={index} className={problem.warning ? 'text-warning' : 'text-destructive'}>
                    {problem.message}
                  </li>
                ))}
              </ul>
            )}

            {phase.tasks.map((task) => (
              <AiPlanRowEditor
                key={task.uid}
                row={task}
                readOnly={readOnly}
                people={people}
                taskTypes={taskTypes}
                problems={messagesFor(problems, { phaseUid: phase.uid, taskUid: task.uid })}
                onChange={(patch) => edit(updateTask(plan, phase.uid, task.uid, patch))}
                onRemove={() => edit(removeTask(plan, phase.uid, task.uid))}
              >
                {task.subtasks.length > 0 && (
                  <div className="space-y-2 border-l-2 pl-3">
                    {task.subtasks.map((sub) => (
                      <AiPlanRowEditor
                        key={sub.uid}
                        compact
                        row={sub}
                        readOnly={readOnly}
                        people={people}
                        taskTypes={taskTypes}
                        problems={messagesFor(problems, {
                          phaseUid: phase.uid,
                          taskUid: task.uid,
                          subtaskUid: sub.uid,
                        })}
                        onChange={(patch) => edit(updateSubtask(plan, phase.uid, task.uid, sub.uid, patch))}
                        onRemove={() => edit(removeSubtask(plan, phase.uid, task.uid, sub.uid))}
                      />
                    ))}
                  </div>
                )}
                {!readOnly && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-xs"
                    onClick={() => edit(addSubtask(plan, phase.uid, task.uid))}
                  >
                    <Plus className="size-3.5" />
                    Thêm việc con
                  </Button>
                )}
              </AiPlanRowEditor>
            ))}

            {!readOnly && (
              <Button type="button" variant="outline" size="sm" onClick={() => edit(addTask(plan, phase.uid))}>
                <Plus className="size-4" />
                Thêm việc
              </Button>
            )}
          </Card>
        )
      })}

      {!readOnly && (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => edit(addPhase(plan))}>
            <Plus className="size-4" />
            Thêm giai đoạn
          </Button>
          <div className="flex flex-wrap items-center gap-2">
            {blocked && (
              <span className="text-xs text-destructive">
                Còn {blockingCount} chỗ cần sửa trước khi lưu hoặc duyệt
              </span>
            )}
            <Button
              type="button"
              variant="outline"
              disabled={working}
              onClick={() => setRejectOpen(true)}
            >
              <X className="size-4" />
              Từ chối
            </Button>
            <Button type="button" variant="outline" disabled={!dirty || blocked || working} onClick={handleSave}>
              <Save className="size-4" />
              Lưu bản sửa
            </Button>
            <Button type="button" disabled={blocked || working} onClick={handleApprove}>
              <Check className="size-4" />
              Duyệt và tạo việc
            </Button>
          </div>
        </div>
      )}

      {!pending && detail.decided_at && (
        <p className="text-xs text-muted-foreground">Đã xử lý lúc {formatDateTime(detail.decided_at)}.</p>
      )}

      <ReasonConfirmDialog
        open={rejectOpen}
        onOpenChange={setRejectOpen}
        title="Từ chối kế hoạch này?"
        description="Không việc nào được tạo. Lý do giúp AI soạn kế hoạch sau sát hơn."
        label="Lý do từ chối"
        confirmText="Từ chối"
        destructive
        pending={reject.isPending}
        onConfirm={handleReject}
      />
    </PageShell>
  )
}
