import { describe, expect, it } from 'vitest'

import type { CategoryAssignee } from '../types/category-assignee'
import {
  CATEGORY_ASSIGNEE_SORT_KEYS,
  sortCategoryAssignees,
} from './category-assignee-sort'

function row(over: Partial<CategoryAssignee> & { id: number }): CategoryAssignee {
  return {
    item_group_id: over.id,
    primary_employee_id: 0,
    backup_employee_id: 0,
    department_id: 1,
    department_name: 'Phòng Thu mua',
    ...over,
  }
}

const label = (r: CategoryAssignee) => r.department_name || 'Thu mua chung'
const ids = (rows: CategoryAssignee[]) => rows.map((r) => r.id)

const rows = [
  row({ id: 1, item_group_name: 'Đồ điện', primary_name: 'Trần Bình', backup_name: 'Lê Cường', department_name: 'Sản xuất' }),
  row({ id: 2, item_group_name: 'Bao bì', primary_name: 'Ân Nguyễn', backup_name: null, department_name: 'Kinh doanh' }),
  row({ id: 3, item_group_name: 'Hóa chất', primary_name: null, backup_name: 'An Phạm', department_name: 'Sản xuất' }),
  row({ id: 4, item_group_name: 'Công cụ', primary_name: 'Đức Hồ', backup_name: 'Bảo Vũ', department_name: '' }),
]

describe('sortCategoryAssignees', () => {
  it('sorts Phân loại by Vietnamese collation (Đ sits right after D)', () => {
    expect(ids(sortCategoryAssignees(rows, 'item_group_name', 'asc', label))).toEqual([2, 4, 1, 3])
    expect(ids(sortCategoryAssignees(rows, 'item_group_name', 'desc', label))).toEqual([3, 1, 4, 2])
  })

  it('sorts Phòng by the label the cell shows, including the fallback label', () => {
    //  Dòng 4 không có tên phòng -> ô hiện "Thu mua chung"; hai dòng cùng phòng xếp theo phân loại.
    expect(ids(sortCategoryAssignees(rows, 'department_name', 'asc', label))).toEqual([2, 1, 3, 4])
    expect(ids(sortCategoryAssignees(rows, 'department_name', 'desc', label))).toEqual([4, 1, 3, 2])
  })

  it('sorts the people columns by name and keeps blank cells LAST in both directions', () => {
    expect(ids(sortCategoryAssignees(rows, 'primary_name', 'asc', label))).toEqual([2, 4, 1, 3])
    expect(ids(sortCategoryAssignees(rows, 'primary_name', 'desc', label))).toEqual([1, 4, 2, 3])
    expect(ids(sortCategoryAssignees(rows, 'backup_name', 'asc', label))).toEqual([3, 4, 1, 2])
    expect(ids(sortCategoryAssignees(rows, 'backup_name', 'desc', label))).toEqual([1, 4, 3, 2])
  })

  it('ignores an unknown key, returns a copy and never mutates the input', () => {
    const input = [...rows]
    const out = sortCategoryAssignees(input, 'actions', 'desc', label)
    expect(ids(out)).toEqual(ids(rows))
    expect(out).not.toBe(input)
    sortCategoryAssignees(input, 'primary_name', 'desc', label)
    expect(ids(input)).toEqual(ids(rows))
  })

  it('covers every sortable column key of the table', () => {
    expect([...CATEGORY_ASSIGNEE_SORT_KEYS]).toEqual([
      'item_group_name',
      'department_name',
      'primary_name',
      'backup_name',
    ])
  })
})
