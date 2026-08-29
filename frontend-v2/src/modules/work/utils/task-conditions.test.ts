import { describe, expect, it } from 'vitest'

import type { FilterFieldDefinition, FilterState } from '@/shared/conditional-filter'
import type { WorkTask } from '../types/work'
import { WORK_ASSIGNEE_KIND, WORK_TASK_STATUS } from '../types/work'
import { applyTaskConditions, multiKey, toFilterableTask } from './task-conditions'

/**
 * Bộ lọc điều kiện của bảng công việc.
 *
 * Chỗ dễ hỏng nhất là các trường ĐA TRỊ (người phụ trách, và trường tùy biến
 * kiểu chọn nhiều — Tag chẳng hạn): chúng bị dẹp thành chuỗi rồi so bằng phép
 * «chứa», nên thiếu rào `|` là id 1 vớ luôn id 12.
 */

function task(patch: Partial<WorkTask> = {}): WorkTask {
  return {
    id: 1,
    list_id: 1,
    section_id: 1,
    parent_id: null,
    title: 'Việc',
    description: '',
    status: WORK_TASK_STATUS.OPEN,
    start_date: '',
    due_date: '',
    sort_order: 0,
    creator_employee_id: 0,
    completed_at: null,
    completed_by: null,
    created_at: '2026-08-01T00:00:00',
    updated_at: '2026-08-01T00:00:00',
    assignees: [],
    labels: [],
    subtask_done: 0,
    subtask_total: 0,
    comment_count: 0,
    ...patch,
  }
}

function label(fieldId: number, optionId: number) {
  return {
    field_id: fieldId,
    option_id: optionId,
    value_text: '',
    value_number: null,
    value_date: '',
    value_employee_id: null,
    value_employee_name: '',
  }
}

function field(name: string, type: FilterFieldDefinition['type']): FilterFieldDefinition {
  return { name, label: name, type }
}

function state(
  rows: { name: string; type: FilterFieldDefinition['type']; operator: string; value: unknown }[],
  conjunction: 'and' | 'or' = 'and',
): FilterState {
  return {
    conjunction,
    rows: rows.map((r, i) => ({
      id: String(i),
      field: field(r.name, r.type),
      operator: r.operator as FilterState['rows'][number]['operator'],
      value: r.value as FilterState['rows'][number]['value'],
    })),
  }
}

describe('toFilterableTask', () => {
  //  Độ ưu tiên nay là một TRƯỜNG TÙY BIẾN nên nó đi chung đường với mọi trường
  //  khác: khóa `label_{fieldId}`, giá trị rào `|`.
  it('gom NHIỀU giá trị của một trường chọn-nhiều vào một chuỗi, không đè lên nhau', () => {
    const ra = toFilterableTask(task({ labels: [label(5, 91), label(5, 94)] }))
    expect(ra.label_5).toBe('|91|94|')
    expect(String(ra.label_5).includes(multiKey(9))).toBe(false)
  })

  it('trường CHƯA có giá trị thì không sinh khóa — «đang trống» mới bắt được', () => {
    expect(toFilterableTask(task()).label_5).toBeUndefined()
  })

  it('rào hai đầu chuỗi đa trị để id 1 không khớp nhầm id 12', () => {
    const ra = toFilterableTask(
      task({
        labels: [label(6, 12)],
        assignees: [
          { employee_id: 12, kind: WORK_ASSIGNEE_KIND.PIC, employee_name: '', employee_code: '' },
        ],
      }),
    )
    expect(ra.label_6).toBe('|12|')
    expect(String(ra.label_6).includes(multiKey(1))).toBe(false)
    expect(ra.pic_keys.includes(multiKey(12))).toBe(true)
  })

  it('người THEO DÕI không tính là người phụ trách', () => {
    const ra = toFilterableTask(
      task({
        assignees: [
          { employee_id: 7, kind: WORK_ASSIGNEE_KIND.FOLLOWER, employee_name: '', employee_code: '' },
        ],
      }),
    )
    expect(ra.pic_keys).toBe('')
  })

  it('mô tả HTML được lột thẻ trước khi lọc, không thì điều kiện «chứa p» khớp tất', () => {
    expect(toFilterableTask(task({ description: '<p>In tem</p>' })).description).toBe('In tem')
  })

  it('việc không người phụ trách để chuỗi RỖNG, để «đang trống» hỏi được', () => {
    expect(toFilterableTask(task()).pic_keys).toBe('')
  })
})

describe('applyTaskConditions', () => {
  it('không có điều kiện nào thì trả về ĐÚNG mảng vào, không dựng mảng mới', () => {
    const rows = [task({ id: 1 })]
    expect(applyTaskConditions(rows, { rows: [], conjunction: 'and' })).toBe(rows)
  })

  it('lọc trường chọn-nhiều khớp đúng việc mang giá trị đó, kể cả khi việc mang nhiều', () => {
    const rows = [
      task({ id: 1, labels: [label(6, 3), label(6, 7)] }),
      task({ id: 2, labels: [label(6, 7)] }),
      task({ id: 3, labels: [] }),
    ]
    const ra = applyTaskConditions(
      rows,
      state([{ name: 'label_6', type: 'select', operator: 'contains', value: multiKey(3) }]),
    )
    expect(ra.map((t) => t.id)).toEqual([1])
  })

  it('trả về CHÍNH tham chiếu WorkTask, không phải bản dẹp phẳng', () => {
    const rows = [task({ id: 1, labels: [label(6, 3)] })]
    const ra = applyTaskConditions(
      rows,
      state([{ name: 'label_6', type: 'select', operator: 'contains', value: multiKey(3) }]),
    )
    expect(ra[0]).toBe(rows[0])
  })

  it('«đang trống» bắt đúng việc chưa gán ai, không bắt việc đã gán', () => {
    const rows = [
      task({ id: 1 }),
      task({
        id: 2,
        assignees: [
          { employee_id: 7, kind: WORK_ASSIGNEE_KIND.PIC, employee_name: '', employee_code: '' },
        ],
      }),
    ]
    const ra = applyTaskConditions(
      rows,
      state([{ name: 'pic_keys', type: 'combobox', operator: 'is_empty', value: null }]),
    )
    expect(ra.map((t) => t.id)).toEqual([1])
  })

  it('lọc theo ngày so được với mốc có kèm GIỜ (created_at là datetime)', () => {
    const rows = [
      task({ id: 1, created_at: '2026-08-01T23:59:00' }),
      task({ id: 2, created_at: '2026-08-20T00:00:01' }),
    ]
    const ra = applyTaskConditions(
      rows,
      state([{ name: 'created_at', type: 'date', operator: 'gte', value: '2026-08-20' }]),
    )
    expect(ra.map((t) => t.id)).toEqual([2])
  })

  it('hai điều kiện AND phải cùng đúng; đổi sang OR thì nới ra', () => {
    const rows = [
      task({ id: 1, labels: [label(5, 91), label(6, 3)] }),
      task({ id: 2, labels: [label(5, 91)] }),
      task({ id: 3, labels: [label(5, 94), label(6, 3)] }),
    ]
    const dieuKien = [
      { name: 'label_5', type: 'select' as const, operator: 'contains', value: multiKey(91) },
      { name: 'label_6', type: 'select' as const, operator: 'contains', value: multiKey(3) },
    ]
    expect(applyTaskConditions(rows, state(dieuKien)).map((t) => t.id)).toEqual([1])
    expect(applyTaskConditions(rows, state(dieuKien, 'or')).map((t) => t.id)).toEqual([1, 2, 3])
  })

  it('điều kiện chưa nhập giá trị bị BỎ QUA, không lọc sạch bảng', () => {
    //  Dòng dở dang (chọn trường xong chưa nhập gì) không được coi là điều kiện
    //  hợp lệ — nếu không, vừa bấm «Thêm điều kiện» là bảng trắng.
    const rows = [task({ id: 1 }), task({ id: 2 })]
    const ra = applyTaskConditions(
      rows,
      state([{ name: 'title', type: 'text', operator: 'contains', value: '' }]),
    )
    expect(ra).toHaveLength(2)
  })
})
