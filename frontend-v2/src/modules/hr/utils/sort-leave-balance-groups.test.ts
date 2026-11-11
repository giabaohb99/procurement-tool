import { describe, expect, it } from 'vitest'

import { balanceFixture } from '../components/leave-balance-fixture'
import { buildLeaveBalanceColumns } from '../components/leave-balance-columns'
import type { LeaveBalance } from '../types/leave'
import { flattenLeaveBalanceGroups, groupLeaveBalances } from './group-leave-balances'
import { LEAVE_BALANCE_SORTABLE_KEYS, sortLeaveBalanceGroups } from './sort-leave-balance-groups'

//  duoc-CR-748 — bảng Quỹ phép năm (thẻ Theo dòng quỹ) xếp NHÓM NGƯỜI ở trình duyệt, trước khi cắt trang.

let nextId = 1
function line(employeeId: number, name: string, overrides: Partial<LeaveBalance> = {}): LeaveBalance {
  return balanceFixture({
    id: nextId++,
    employee_id: employeeId,
    employee_name: name,
    allocated_days: 0,
    seniority_days: 0,
    carried_days: 0,
    adjusted_days: 0,
    used_days: 0,
    pending_days: 0,
    total_days: 0,
    remaining_days: 0,
    ...overrides,
  })
}

function names(groups: ReturnType<typeof groupLeaveBalances>): string[] {
  return groups.map((g) => g.employeeName)
}

describe('sortLeaveBalanceGroups', () => {
  it('sorts people by Vietnamese name with diacritics, not by code point', () => {
    //  So theo mã ký tự thì "Đ" (U+0110) đứng sau "Z" và "Ánh" sau "Bình" — sai với mắt người Việt.
    const groups = groupLeaveBalances([
      line(1, 'Đặng Văn Đức'),
      line(2, 'Bùi Thị Ánh'),
      line(3, 'An Văn Bình'),
      line(4, 'Ánh Dương'),
    ])
    expect(names(sortLeaveBalanceGroups(groups, 'employee_name', 'asc'))).toEqual([
      'An Văn Bình',
      'Ánh Dương',
      'Bùi Thị Ánh',
      'Đặng Văn Đức',
    ])
    expect(names(sortLeaveBalanceGroups(groups, 'employee_name', 'desc'))).toEqual([
      'Đặng Văn Đức',
      'Bùi Thị Ánh',
      'Ánh Dương',
      'An Văn Bình',
    ])
  })

  it('sorts by the GROUP total, not by any single leave line', () => {
    //  A có hai dòng 1 + 4 = 5 ngày đã nghỉ, B một dòng 3 ngày: xếp theo dòng lẻ thì B (3) đứng giữa hai dòng
    //  của A và người A bị xé làm hai — tổng 5 mới là con số hàng người đang hiện.
    const groups = groupLeaveBalances([
      line(1, 'A', { used_days: 1 }),
      line(2, 'B', { used_days: 3 }),
      line(1, 'A', { used_days: 4, leave_type_id: 2, leave_type_name: 'Nghỉ ốm' }),
    ])
    expect(names(sortLeaveBalanceGroups(groups, 'used_days', 'asc'))).toEqual(['B', 'A'])
    expect(names(sortLeaveBalanceGroups(groups, 'used_days', 'desc'))).toEqual(['A', 'B'])
  })

  it('puts a zero total (shown as a dash) at the END in both directions', () => {
    const groups = groupLeaveBalances([
      line(1, 'Không nghỉ', { used_days: 0 }),
      line(2, 'Nghỉ nhiều', { used_days: 5 }),
      line(3, 'Nghỉ ít', { used_days: 0.5 }),
    ])
    expect(names(sortLeaveBalanceGroups(groups, 'used_days', 'asc'))).toEqual(['Nghỉ ít', 'Nghỉ nhiều', 'Không nghỉ'])
    expect(names(sortLeaveBalanceGroups(groups, 'used_days', 'desc'))).toEqual(['Nghỉ nhiều', 'Nghỉ ít', 'Không nghỉ'])
  })

  it('treats 0 as a REAL value in "Còn lại", since that cell always prints the number (0 = out of leave)', () => {
    const groups = groupLeaveBalances([
      line(1, 'Còn 3', { remaining_days: 3 }),
      line(2, 'Hết phép', { remaining_days: 0 }),
      line(3, 'Âm 1', { remaining_days: -1 }),
    ])
    expect(names(sortLeaveBalanceGroups(groups, 'remaining_days', 'asc'))).toEqual(['Âm 1', 'Hết phép', 'Còn 3'])
    expect(names(sortLeaveBalanceGroups(groups, 'remaining_days', 'desc'))).toEqual(['Còn 3', 'Hết phép', 'Âm 1'])
  })

  it('handles negative adjustments as numbers and keeps blanks last', () => {
    const groups = groupLeaveBalances([
      line(1, 'Trừ', { adjusted_days: -2 }),
      line(2, 'Không chỉnh'),
      line(3, 'Cộng', { adjusted_days: 1.5 }),
    ])
    expect(names(sortLeaveBalanceGroups(groups, 'adjusted_days', 'asc'))).toEqual(['Trừ', 'Cộng', 'Không chỉnh'])
    expect(names(sortLeaveBalanceGroups(groups, 'adjusted_days', 'desc'))).toEqual(['Cộng', 'Trừ', 'Không chỉnh'])
  })

  it('sorts by the joined policy names and leaves people without a policy at the end both ways', () => {
    const groups = groupLeaveBalances([
      line(1, 'Không gói'),
      line(2, 'Gói B', { policy_name: 'Văn phòng' }),
      line(3, 'Gói A', { policy_name: 'Ca kíp' }),
    ])
    expect(names(sortLeaveBalanceGroups(groups, 'policy_name', 'asc'))).toEqual(['Gói A', 'Gói B', 'Không gói'])
    expect(names(sortLeaveBalanceGroups(groups, 'policy_name', 'desc'))).toEqual(['Gói B', 'Gói A', 'Không gói'])
  })

  it('breaks ties by name then by employee id, so the order never flips between renders', () => {
    const groups = groupLeaveBalances([
      line(9, 'Cùng tên', { used_days: 2 }),
      line(3, 'Cùng tên', { used_days: 2 }),
      line(5, 'An', { used_days: 2 }),
    ])
    const sorted = sortLeaveBalanceGroups(groups, 'used_days', 'desc')
    expect(sorted.map((g) => g.employeeId)).toEqual([5, 3, 9])
  })

  it('keeps the child lines of a group in their original leave-type order after sorting', () => {
    const groups = groupLeaveBalances([
      line(1, 'Bình', { leave_type_id: 1, leave_type_name: 'Phép năm', used_days: 1 }),
      line(1, 'Bình', { leave_type_id: 7, leave_type_name: 'Nghỉ bù', used_days: 9 }),
      line(2, 'An', { leave_type_id: 1, leave_type_name: 'Phép năm', used_days: 2 }),
    ])
    const sorted = sortLeaveBalanceGroups(groups, 'used_days', 'desc')
    const rows = flattenLeaveBalanceGroups(sorted, new Set([1]))
    expect(rows.map((r) => (r.kind === 'group' || r.kind === 'single' ? r.group.employeeName : r.balance.leave_type_name)))
      .toEqual(['Bình', 'Phép năm', 'Nghỉ bù', 'An'])
  })

  it('returns the backend order for an empty key (third header click) or a key it does not know', () => {
    const groups = groupLeaveBalances([line(1, 'Cường'), line(2, 'An'), line(3, 'Bình')])
    expect(names(sortLeaveBalanceGroups(groups, '', 'desc'))).toEqual(['Cường', 'An', 'Bình'])
    expect(names(sortLeaveBalanceGroups(groups, 'year', 'asc'))).toEqual(['Cường', 'An', 'Bình'])
  })

  it('does not mutate the input array', () => {
    const groups = groupLeaveBalances([line(1, 'B'), line(2, 'A')])
    sortLeaveBalanceGroups(groups, 'employee_name', 'asc')
    expect(names(groups)).toEqual(['B', 'A'])
  })

  it('copes with an empty list', () => {
    expect(sortLeaveBalanceGroups([], 'employee_name', 'asc')).toEqual([])
  })

  it('marks as sortable exactly the columns the sorter understands', () => {
    //  Cột bật `sortable` mà hàm xếp không hiểu khóa là lỗi "bấm không ăn" (luật §8). Ngược lại cột xếp được
    //  mà không bật thì người dùng không biết là bấm được.
    const columns = buildLeaveBalanceColumns({ expanded: new Set(), onToggle: () => {} })
    for (const column of columns) {
      expect(Boolean(column.sortable), column.key).toBe(LEAVE_BALANCE_SORTABLE_KEYS.has(column.key))
    }
    expect(columns.every((c) => c.sortable)).toBe(true)
  })
})
