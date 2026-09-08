import { describe, expect, it } from 'vitest'

import type { WorkSection, WorkTask } from '../types/work'
import { WORK_TASK_KIND, WORK_TASK_STATUS } from '../types/work'
import { groupTasksBySection, UNGROUPED_KEY } from './group-tasks'

function section(id: number, name: string, sortOrder = id): WorkSection {
  return { id, list_id: 1, name, color: 'blue', sort_order: sortOrder } as WorkSection
}

function task(id: number, sectionId: number | null): WorkTask {
  return {
    id,
    list_id: 1,
    section_id: sectionId,
    parent_id: null,
    title: `Việc ${id}`,
    description: '',
    status: WORK_TASK_STATUS.OPEN,
    kind: WORK_TASK_KIND.TASK,
    start_date: '',
    due_date: '',
    sort_order: id,
    creator_employee_id: 1,
    completed_at: null,
    completed_by: null,
    created_at: '2026-08-29T00:00:00',
    updated_at: '2026-08-29T00:00:00',
    assignees: [],
    labels: [],
    subtask_done: 0,
    subtask_total: 0,
    comment_count: 0,
  }
}

describe('groupTasksBySection', () => {
  it('keeps one group per column, in the column order given', () => {
    const groups = groupTasksBySection(
      [task(1, 20), task(2, 10)],
      [section(10, 'To do'), section(20, 'Doing')],
    )

    expect(groups.map((g) => g.name)).toEqual(['To do', 'Doing'])
    expect(groups[0].tasks.map((t) => t.id)).toEqual([2])
    expect(groups[1].tasks.map((t) => t.id)).toEqual([1])
  })

  it('shows an EMPTY column — that is the only place its «Việc mới» row can live', () => {
    const groups = groupTasksBySection([], [section(10, 'To do'), section(20, 'Doing')])

    expect(groups).toHaveLength(2)
    expect(groups.every((g) => g.tasks.length === 0)).toBe(true)
  })

  it('preserves the incoming task order instead of re-sorting', () => {
    //  Mảng vào đã qua prepareTasks (lọc + tiêu chí sắp xếp người dùng chọn).
    const groups = groupTasksBySection([task(9, 10), task(3, 10), task(7, 10)], [section(10, 'A')])

    expect(groups[0].tasks.map((t) => t.id)).toEqual([9, 3, 7])
  })

  it('drops tasks with no column into «Chưa phân cột», placed last', () => {
    const groups = groupTasksBySection([task(1, null), task(2, 10)], [section(10, 'To do')])

    expect(groups.map((g) => g.key)).toEqual(['section:10', UNGROUPED_KEY])
    expect(groups[1].tasks.map((t) => t.id)).toEqual([1])
  })

  it('rescues a task pointing at a DELETED column instead of hiding it', () => {
    //  `section_id` không có ON DELETE SET NULL, nên số cũ còn nằm lại sau khi
    //  xóa cột. Lọc theo cột đang có thì task biến mất, người dùng tưởng mất việc.
    const groups = groupTasksBySection([task(1, 999)], [section(10, 'To do')])

    expect(groups.find((g) => g.key === UNGROUPED_KEY)?.tasks.map((t) => t.id)).toEqual([1])
  })

  it('omits «Chưa phân cột» entirely when every task has a column', () => {
    const groups = groupTasksBySection([task(1, 10)], [section(10, 'To do')])

    expect(groups.map((g) => g.key)).toEqual(['section:10'])
  })

  it('returns nothing at all when the list has no columns and no tasks', () => {
    expect(groupTasksBySection([], [])).toEqual([])
  })

  it('puts everything under «Chưa phân cột» when the list has no columns yet', () => {
    const groups = groupTasksBySection([task(1, null), task(2, null)], [])

    expect(groups).toHaveLength(1)
    expect(groups[0].sectionId).toBeNull()
    expect(groups[0].tasks).toHaveLength(2)
  })
})
