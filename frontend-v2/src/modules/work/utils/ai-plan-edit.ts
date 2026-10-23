import type {
  AiPlanDocument,
  AiPlanProblem,
  AiPlanSubtask,
  AiPlanTask,
} from '../types/ai-plan'

/**
 * Hàm thuần của màn *Duyệt kế hoạch AI* (kh-AI1-3): giữ bản đang sửa, thêm / bỏ /
 * sửa dòng, kiểm trước khi gửi, và ghim lỗi 422 của máy chủ vào đúng dòng.
 *
 * Mỗi dòng mang thêm `uid` CỤC BỘ làm khóa React và để ghim lỗi — `key` của máy chủ
 * không dùng được vì mọi dòng người thêm mới đều có `key` rỗng. `uid` bị gỡ trước khi
 * gửi (`toPlanPayload`), máy chủ không bao giờ thấy.
 */

/** Trần của máy chủ (`ai_plan/service.py`): vượt là máy chủ CẮT bớt hoặc báo lỗi. */
export const AI_PLAN_LIMITS = {
  phases: 12,
  tasksPerPhase: 30,
  subtasksPerTask: 7,
  criteria: 3,
  assignees: 10,
  maxHours: 999,
} as const

export interface EditableSubtask extends AiPlanSubtask {
  uid: string
}

export interface EditableTask extends Omit<AiPlanTask, 'subtasks'> {
  uid: string
  subtasks: EditableSubtask[]
}

export interface EditablePhase {
  uid: string
  name: string
  tasks: EditableTask[]
}

export interface EditablePlan extends Omit<AiPlanDocument, 'phases' | 'counts'> {
  phases: EditablePhase[]
}

/** Một lỗi đã ghim vào dòng: thiếu `phaseUid` = lỗi cấp kế hoạch. */
export interface PlanRowProblem {
  phaseUid?: string
  taskUid?: string
  subtaskUid?: string
  field: string
  message: string
  /**
   * `true` = chỉ nhắc, không chặn Lưu / Duyệt. Dùng cho giai đoạn rỗng: máy chủ cố ý coi
   * giai đoạn hết việc là XÓA giai đoạn đó (A4 chốt 22/10), nên gửi đi vẫn đúng ý.
   */
  warning?: boolean
}

let uidSeed = 0
function nextUid(): string {
  uidSeed += 1
  return `row-${uidSeed}`
}

type RawRow = Partial<AiPlanSubtask> & { subtasks?: unknown }

function toEditableSubtask(raw: RawRow): EditableSubtask {
  return {
    uid: nextUid(),
    key: raw.key ?? '',
    title: raw.title ?? '',
    description: raw.description ?? '',
    assignees: Array.isArray(raw.assignees) ? raw.assignees : [],
    start_date: raw.start_date ?? '',
    due_date: raw.due_date ?? '',
    priority: raw.priority ?? 'Thường',
    criteria: Array.isArray(raw.criteria) ? raw.criteria : [],
    estimate_hours: typeof raw.estimate_hours === 'number' ? raw.estimate_hours : null,
    task_type: raw.task_type ?? null,
    assignee_reason: raw.assignee_reason ?? '',
  }
}

function toEditableTask(raw: RawRow): EditableTask {
  const subtasks = Array.isArray(raw.subtasks) ? (raw.subtasks as RawRow[]) : []
  return { ...toEditableSubtask(raw), subtasks: subtasks.map(toEditableSubtask) }
}

/** Bản máy chủ → bản đang sửa. Chịu được bản cũ / thiếu ô: thiếu thì điền mặc định. */
export function toEditablePlan(plan: AiPlanDocument): EditablePlan {
  const phases = Array.isArray(plan.phases) ? plan.phases : []
  return {
    title: plan.title ?? '',
    description: plan.description ?? '',
    deadline: plan.deadline ?? '',
    assumptions: Array.isArray(plan.assumptions) ? plan.assumptions : [],
    phases: phases.map((phase) => ({
      uid: nextUid(),
      name: phase.name ?? '',
      tasks: (Array.isArray(phase.tasks) ? phase.tasks : []).map((task) => toEditableTask(task as RawRow)),
    })),
  }
}

function stripSubtask({ uid: _uid, ...rest }: EditableSubtask): AiPlanSubtask {
  return rest
}

/** Bản đang sửa → thân gửi máy chủ: gỡ `uid`, đếm lại `counts` theo đúng thứ đang có. */
export function toPlanPayload(plan: EditablePlan): AiPlanDocument {
  const phases = plan.phases.map((phase) => ({
    name: phase.name,
    tasks: phase.tasks.map(({ uid: _uid, subtasks, ...rest }) => ({
      ...rest,
      subtasks: subtasks.map(stripSubtask),
    })),
  }))
  const tasks = phases.reduce((sum, phase) => sum + phase.tasks.length, 0)
  const subtasks = phases.reduce(
    (sum, phase) => sum + phase.tasks.reduce((n, task) => n + task.subtasks.length, 0),
    0,
  )
  return {
    title: plan.title,
    description: plan.description,
    deadline: plan.deadline,
    phases,
    assumptions: plan.assumptions,
    counts: { phases: phases.length, tasks, subtasks },
  }
}

function blankRow(): EditableSubtask {
  return toEditableSubtask({ priority: 'Thường' })
}

function mapPhase(
  plan: EditablePlan,
  phaseUid: string,
  change: (phase: EditablePhase) => EditablePhase,
): EditablePlan {
  if (!plan.phases.some((phase) => phase.uid === phaseUid)) return plan
  return { ...plan, phases: plan.phases.map((phase) => (phase.uid === phaseUid ? change(phase) : phase)) }
}

function mapTask(
  plan: EditablePlan,
  phaseUid: string,
  taskUid: string,
  change: (task: EditableTask) => EditableTask,
): EditablePlan {
  const phase = plan.phases.find((item) => item.uid === phaseUid)
  if (!phase?.tasks.some((task) => task.uid === taskUid)) return plan
  return mapPhase(plan, phaseUid, (current) => ({
    ...current,
    tasks: current.tasks.map((task) => (task.uid === taskUid ? change(task) : task)),
  }))
}

export function addPhase(plan: EditablePlan): EditablePlan {
  return {
    ...plan,
    phases: [...plan.phases, { uid: nextUid(), name: `Giai đoạn ${plan.phases.length + 1}`, tasks: [] }],
  }
}

export function renamePhase(plan: EditablePlan, phaseUid: string, name: string): EditablePlan {
  return mapPhase(plan, phaseUid, (phase) => ({ ...phase, name }))
}

export function removePhase(plan: EditablePlan, phaseUid: string): EditablePlan {
  return { ...plan, phases: plan.phases.filter((phase) => phase.uid !== phaseUid) }
}

/** Việc mới để `key` RỖNG — máy chủ đặt `n1`, `n2`… lúc lưu. */
export function addTask(plan: EditablePlan, phaseUid: string): EditablePlan {
  return mapPhase(plan, phaseUid, (phase) => ({
    ...phase,
    tasks: [...phase.tasks, { ...blankRow(), subtasks: [] }],
  }))
}

export function updateTask(
  plan: EditablePlan,
  phaseUid: string,
  taskUid: string,
  patch: Partial<Omit<EditableTask, 'uid' | 'subtasks'>>,
): EditablePlan {
  return mapTask(plan, phaseUid, taskUid, (task) => ({ ...task, ...patch }))
}

export function removeTask(plan: EditablePlan, phaseUid: string, taskUid: string): EditablePlan {
  return mapPhase(plan, phaseUid, (phase) => ({
    ...phase,
    tasks: phase.tasks.filter((task) => task.uid !== taskUid),
  }))
}

export function addSubtask(plan: EditablePlan, phaseUid: string, taskUid: string): EditablePlan {
  return mapTask(plan, phaseUid, taskUid, (task) => ({ ...task, subtasks: [...task.subtasks, blankRow()] }))
}

export function updateSubtask(
  plan: EditablePlan,
  phaseUid: string,
  taskUid: string,
  subtaskUid: string,
  patch: Partial<Omit<EditableSubtask, 'uid'>>,
): EditablePlan {
  return mapTask(plan, phaseUid, taskUid, (task) => ({
    ...task,
    subtasks: task.subtasks.map((sub) => (sub.uid === subtaskUid ? { ...sub, ...patch } : sub)),
  }))
}

export function removeSubtask(
  plan: EditablePlan,
  phaseUid: string,
  taskUid: string,
  subtaskUid: string,
): EditablePlan {
  return mapTask(plan, phaseUid, taskUid, (task) => ({
    ...task,
    subtasks: task.subtasks.filter((sub) => sub.uid !== subtaskUid),
  }))
}

function checkRow(
  row: EditableSubtask,
  where: Omit<PlanRowProblem, 'field' | 'message'>,
  problems: PlanRowProblem[],
) {
  //  Máy chủ BỎ LẶNG dòng không tên (`_normalize_task` trả None) — phải chặn ở đây,
  //  không thì người duyệt mất dòng mà không biết.
  if (!row.title.trim()) {
    problems.push({ ...where, field: 'title', message: 'Việc chưa có tên' })
  }
  if (row.start_date && row.due_date && row.due_date < row.start_date) {
    problems.push({ ...where, field: 'due_date', message: 'Hạn trước ngày bắt đầu' })
  }
  const hours = row.estimate_hours
  if (hours !== null && !(hours > 0 && hours <= AI_PLAN_LIMITS.maxHours)) {
    problems.push({
      ...where,
      field: 'estimate_hours',
      message: `Giờ ước lượng phải lớn hơn 0 và không quá ${AI_PLAN_LIMITS.maxHours}`,
    })
  }
  if (row.assignees.length > AI_PLAN_LIMITS.assignees) {
    problems.push({ ...where, field: 'assignees', message: `Tối đa ${AI_PLAN_LIMITS.assignees} người` })
  }
}

/** Lỗi thật sự chặn Lưu / Duyệt (bỏ các dòng chỉ nhắc). */
export function findBlockingProblems(problems: PlanRowProblem[]): PlanRowProblem[] {
  return problems.filter((problem) => !problem.warning)
}

/**
 * Kiểm trước khi gửi những thứ máy chủ sẽ BỎ LẶNG hoặc cắt bớt (dòng không tên, giai
 * đoạn rỗng — chỉ nhắc, vượt trần) cùng những lỗi rẻ (hạn trước ngày bắt đầu, giờ ngoài dải).
 * Người còn làm hay không thì chỉ máy chủ biết — lỗi đó về qua `mapServerProblems`.
 */
export function findLocalProblems(plan: EditablePlan): PlanRowProblem[] {
  const problems: PlanRowProblem[] = []
  if (!plan.title.trim()) problems.push({ field: 'title', message: 'Kế hoạch chưa có tên' })
  if (plan.phases.length === 0) problems.push({ field: 'phases', message: 'Kế hoạch chưa có giai đoạn nào' })
  if (plan.phases.length > AI_PLAN_LIMITS.phases) {
    problems.push({ field: 'phases', message: `Tối đa ${AI_PLAN_LIMITS.phases} giai đoạn` })
  }
  for (const phase of plan.phases) {
    if (phase.tasks.length === 0) {
      problems.push({
        phaseUid: phase.uid,
        field: 'tasks',
        message: 'Giai đoạn chưa có việc nào — lưu hoặc duyệt thì giai đoạn này bị bỏ',
        warning: true,
      })
    }
    if (phase.tasks.length > AI_PLAN_LIMITS.tasksPerPhase) {
      problems.push({
        phaseUid: phase.uid,
        field: 'tasks',
        message: `Tối đa ${AI_PLAN_LIMITS.tasksPerPhase} việc mỗi giai đoạn`,
      })
    }
    for (const task of phase.tasks) {
      checkRow(task, { phaseUid: phase.uid, taskUid: task.uid }, problems)
      if (task.subtasks.length > AI_PLAN_LIMITS.subtasksPerTask) {
        problems.push({
          phaseUid: phase.uid,
          taskUid: task.uid,
          field: 'subtasks',
          message: `Tối đa ${AI_PLAN_LIMITS.subtasksPerTask} việc con`,
        })
      }
      for (const sub of task.subtasks) {
        checkRow(sub, { phaseUid: phase.uid, taskUid: task.uid, subtaskUid: sub.uid }, problems)
      }
    }
  }
  return problems
}

/**
 * Ghim lỗi 422 của máy chủ (vị trí đếm từ 0 trong mảng ĐÃ GỬI) vào dòng đang sửa. Vị trí
 * không còn (người vừa xóa dòng đó) thì giữ câu báo ở cấp kế hoạch, không đánh rơi.
 */
export function mapServerProblems(problems: AiPlanProblem[], plan: EditablePlan): PlanRowProblem[] {
  return problems.map(({ phase, task, subtask, field, message }) => {
    const planLevel = { field, message }
    if (phase === null) return planLevel
    const phaseRow = plan.phases[phase]
    if (!phaseRow) return planLevel
    if (task === null) return { phaseUid: phaseRow.uid, field, message }
    const taskRow = phaseRow.tasks[task]
    if (!taskRow) return planLevel
    if (subtask === null) return { phaseUid: phaseRow.uid, taskUid: taskRow.uid, field, message }
    const subRow = taskRow.subtasks[subtask]
    if (!subRow) return planLevel
    return { phaseUid: phaseRow.uid, taskUid: taskRow.uid, subtaskUid: subRow.uid, field, message }
  })
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

/** Rút `details.problems` khỏi lỗi 422 `PLAN_INVALID`; lỗi khác thì trả mảng rỗng. */
export function readPlanProblems(error: unknown): AiPlanProblem[] {
  if (!isRecord(error) || !isRecord(error.response) || !isRecord(error.response.data)) return []
  const body = error.response.data.error
  if (!isRecord(body) || body.code !== 'PLAN_INVALID' || !isRecord(body.details)) return []
  const problems = body.details.problems
  return Array.isArray(problems) ? problems.filter(isRecord).map((p) => p as unknown as AiPlanProblem) : []
}
