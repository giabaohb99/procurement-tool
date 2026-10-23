import { describe, expect, it } from 'vitest'

import type { AiPlanDocument, AiPlanTask } from '../types/ai-plan'
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
  toEditablePlan,
  toPlanPayload,
  updateTask,
} from './ai-plan-edit'

function task(over: Partial<AiPlanTask> = {}): AiPlanTask {
  return {
    key: 'p1t1',
    title: 'Đặt phòng họp',
    description: '',
    assignees: [{ employee_id: 12, code: 'NSU012', name: 'Nguyễn A' }],
    start_date: '2026-10-23',
    due_date: '2026-10-24',
    priority: 'Ưu tiên',
    criteria: ['Có xác nhận'],
    estimate_hours: 2.5,
    task_type: { id: 3, name: 'Hậu cần' },
    assignee_reason: 'Ít việc nhất phòng',
    subtasks: [],
    ...over,
  }
}

function plan(over: Partial<AiPlanDocument> = {}): AiPlanDocument {
  return {
    title: 'Tiếp khách Trung Quốc',
    description: '',
    deadline: '2026-10-30',
    phases: [{ name: 'Chuẩn bị', tasks: [task()] }],
    assumptions: [],
    counts: { phases: 1, tasks: 1, subtasks: 0 },
    ...over,
  }
}

describe('toEditablePlan / toPlanPayload', () => {
  it('round-trips the plan unchanged apart from the recounted totals', () => {
    const original = plan()
    expect(toPlanPayload(toEditablePlan(original))).toEqual(original)
  })

  it('never sends the local row ids to the server', () => {
    const payload = toPlanPayload(toEditablePlan(plan()))
    expect(JSON.stringify(payload)).not.toContain('uid')
  })

  it('gives every row a distinct local id, even rows with the same key', () => {
    //  Hai dòng người thêm đều có `key` rỗng — lấy key làm khóa React là hai dòng trùng khóa.
    const editable = toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task({ key: '' }), task({ key: '' })] }] }))
    const [first, second] = editable.phases[0].tasks
    expect(first.uid).not.toBe(second.uid)
  })

  it('fills in missing arrays and fields from an old or partial plan instead of crashing', () => {
    const partial = { title: 'X', phases: [{ name: 'A', tasks: [{ title: 'Việc' }] }] } as unknown as AiPlanDocument
    const editable = toEditablePlan(partial)
    const row = editable.phases[0].tasks[0]
    expect(row.assignees).toEqual([])
    expect(row.subtasks).toEqual([])
    expect(row.criteria).toEqual([])
    expect(row.estimate_hours).toBeNull()
    expect(row.task_type).toBeNull()
    expect(editable.assumptions).toEqual([])
  })

  it('recounts phases, tasks and subtasks from what is actually there', () => {
    let editable = toEditablePlan(plan())
    editable = addTask(editable, editable.phases[0].uid)
    editable = addSubtask(editable, editable.phases[0].uid, editable.phases[0].tasks[0].uid)
    expect(toPlanPayload(editable).counts).toEqual({ phases: 1, tasks: 2, subtasks: 1 })
  })
})

describe('adding and removing rows', () => {
  it('adds a new task with an EMPTY key so the server assigns one', () => {
    const editable = toEditablePlan(plan())
    const next = addTask(editable, editable.phases[0].uid)
    const added = next.phases[0].tasks[1]
    expect(added.key).toBe('')
    expect(added.priority).toBe('Thường')
    expect(added.subtasks).toEqual([])
  })

  it('does not mutate the plan it was given', () => {
    const editable = toEditablePlan(plan())
    const before = JSON.stringify(editable)
    addTask(editable, editable.phases[0].uid)
    addPhase(editable)
    updateTask(editable, editable.phases[0].uid, editable.phases[0].tasks[0].uid, { title: 'Khác' })
    expect(JSON.stringify(editable)).toBe(before)
  })

  it('removes only the targeted task, phase or subtask', () => {
    let editable = toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task({ key: 'a' }), task({ key: 'b' })] }] }))
    const phaseUid = editable.phases[0].uid
    const [first, second] = editable.phases[0].tasks
    editable = removeTask(editable, phaseUid, first.uid)
    expect(editable.phases[0].tasks.map((t) => t.key)).toEqual(['b'])

    editable = addSubtask(editable, phaseUid, second.uid)
    editable = addSubtask(editable, phaseUid, second.uid)
    const [s1] = editable.phases[0].tasks[0].subtasks
    editable = removeSubtask(editable, phaseUid, second.uid, s1.uid)
    expect(editable.phases[0].tasks[0].subtasks).toHaveLength(1)

    editable = addPhase(editable)
    editable = removePhase(editable, phaseUid)
    expect(editable.phases).toHaveLength(1)
    expect(editable.phases[0].name).toBe('Giai đoạn 2')
  })

  it('ignores an unknown row id instead of throwing', () => {
    const editable = toEditablePlan(plan())
    expect(removeTask(editable, 'nope', 'nope')).toEqual(editable)
    expect(updateTask(editable, editable.phases[0].uid, 'nope', { title: 'X' })).toEqual(editable)
  })
})

describe('findLocalProblems', () => {
  it('finds nothing wrong with a well-formed plan', () => {
    expect(findLocalProblems(toEditablePlan(plan()))).toEqual([])
  })

  it('flags a task with no title — the server would DROP it silently', () => {
    //  `_normalize_task` trả None cho việc không tên và máy chủ lặng lẽ bỏ dòng đó.
    const editable = toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task({ title: '   ' })] }] }))
    const problems = findLocalProblems(editable)
    expect(problems.some((p) => p.field === 'title' && p.taskUid === editable.phases[0].tasks[0].uid)).toBe(true)
  })

  it('only WARNS about a phase with no task — the server treats it as deleting that phase', () => {
    //  A4 chốt 22/10: giai đoạn hết việc là xóa giai đoạn, giao diện cứ gửi. Nhắc để người
    //  duyệt biết, không chặn.
    const editable = toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task()] }, { name: 'B', tasks: [] }] }))
    const problems = findLocalProblems(editable)
    const empty = problems.find((p) => p.phaseUid === editable.phases[1].uid)
    expect(empty?.warning).toBe(true)
    expect(findBlockingProblems(problems)).toEqual([])
  })

  it('still blocks a nameless task even when a warning sits next to it', () => {
    const editable = toEditablePlan(
      plan({ phases: [{ name: 'A', tasks: [task({ title: '' })] }, { name: 'B', tasks: [] }] }),
    )
    expect(findBlockingProblems(findLocalProblems(editable)).map((p) => p.field)).toEqual(['title'])
  })

  it('flags a plan with no title or no phase at all', () => {
    expect(findLocalProblems(toEditablePlan(plan({ title: '' }))).some((p) => p.field === 'title' && !p.phaseUid)).toBe(true)
    expect(findLocalProblems(toEditablePlan(plan({ phases: [] }))).some((p) => p.field === 'phases')).toBe(true)
  })

  it('flags a due date before the start date, but accepts the same day', () => {
    const bad = toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task({ start_date: '2026-10-24', due_date: '2026-10-23' })] }] }))
    expect(findLocalProblems(bad).some((p) => p.field === 'due_date')).toBe(true)
    const same = toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task({ start_date: '2026-10-24', due_date: '2026-10-24' })] }] }))
    expect(findLocalProblems(same)).toEqual([])
  })

  it('flags estimate hours of 0, negative, or above 999, and accepts empty', () => {
    for (const hours of [0, -1, 1000, Number.NaN]) {
      const editable = toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task({ estimate_hours: hours })] }] }))
      expect(findLocalProblems(editable).some((p) => p.field === 'estimate_hours')).toBe(true)
    }
    for (const hours of [null, 0.5, 999]) {
      const editable = toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task({ estimate_hours: hours })] }] }))
      expect(findLocalProblems(editable)).toEqual([])
    }
  })

  it('flags going over the server limits instead of letting the server cut rows off', () => {
    const manyTasks = Array.from({ length: 31 }, (_, i) => task({ key: `k${i}` }))
    expect(
      findLocalProblems(toEditablePlan(plan({ phases: [{ name: 'A', tasks: manyTasks }] }))).some(
        (p) => p.field === 'tasks',
      ),
    ).toBe(true)

    const manyPhases = Array.from({ length: 13 }, (_, i) => ({ name: `G${i}`, tasks: [task()] }))
    expect(findLocalProblems(toEditablePlan(plan({ phases: manyPhases }))).some((p) => p.field === 'phases')).toBe(true)

    const manySubs = Array.from({ length: 8 }, () => task())
    expect(
      findLocalProblems(toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task({ subtasks: manySubs })] }] }))).some(
        (p) => p.field === 'subtasks',
      ),
    ).toBe(true)
  })

  it('checks subtasks too', () => {
    const editable = toEditablePlan(plan({ phases: [{ name: 'A', tasks: [task({ subtasks: [task({ title: '' })] })] }] }))
    const sub = editable.phases[0].tasks[0].subtasks[0]
    expect(findLocalProblems(editable).some((p) => p.subtaskUid === sub.uid && p.field === 'title')).toBe(true)
  })
})

describe('mapServerProblems', () => {
  it('pins each server problem to the row at that position in what was sent', () => {
    const editable = toEditablePlan(
      plan({ phases: [{ name: 'A', tasks: [task(), task({ subtasks: [task()] })] }] }),
    )
    const mapped = mapServerProblems(
      [
        { phase: 0, task: 1, subtask: 0, key: '', field: 'assignees', message: 'người #9 đã nghỉ' },
        { phase: 0, task: 0, subtask: null, key: 'p1t1', field: 'due_date', message: 'hạn sai' },
        { phase: null, task: null, subtask: null, key: '', field: 'deadline', message: 'hạn chót sai' },
      ],
      editable,
    )
    const [taskA, taskB] = editable.phases[0].tasks
    expect(mapped[0]).toMatchObject({ taskUid: taskB.uid, subtaskUid: taskB.subtasks[0].uid, field: 'assignees' })
    expect(mapped[1]).toMatchObject({ taskUid: taskA.uid, field: 'due_date' })
    expect(mapped[1].subtaskUid).toBeUndefined()
    expect(mapped[2]).toEqual({ field: 'deadline', message: 'hạn chót sai' })
  })

  it('keeps a problem whose position no longer exists as a plan-level message', () => {
    //  Người sửa xóa dòng sau lúc gửi: vị trí cũ không còn, nhưng câu báo vẫn phải hiện.
    const editable = toEditablePlan(plan())
    const mapped = mapServerProblems(
      [{ phase: 5, task: 9, subtask: null, key: '', field: 'title', message: 'mất dòng' }],
      editable,
    )
    expect(mapped).toEqual([{ field: 'title', message: 'mất dòng' }])
  })
})

describe('readPlanProblems', () => {
  it('reads the problems out of a 422 PLAN_INVALID error', () => {
    const error = {
      response: {
        status: 422,
        data: {
          success: false,
          error: {
            code: 'PLAN_INVALID',
            message: 'Kế hoạch chưa hợp lệ',
            details: { problems: [{ phase: 0, task: 0, subtask: null, key: 'p1t1', field: 'title', message: 'x' }] },
          },
        },
      },
    }
    expect(readPlanProblems(error)).toHaveLength(1)
  })

  it('gives an empty list for any other error shape', () => {
    expect(readPlanProblems(new Error('mạng'))).toEqual([])
    expect(readPlanProblems(null)).toEqual([])
    expect(readPlanProblems({ response: { data: { error: { code: 'OTHER', details: { problems: [1] } } } } })).toEqual([])
    expect(
      readPlanProblems({ response: { data: { error: { code: 'PLAN_INVALID', details: { problems: 'oops' } } } } }),
    ).toEqual([])
  })
})
