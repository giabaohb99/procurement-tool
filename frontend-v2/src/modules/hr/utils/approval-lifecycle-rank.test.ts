import { describe, expect, it } from 'vitest'

import { sortRowsByCell } from '@/shared/utils/sort-rows-by-cell'
import { LEAVE_STATUS } from '../types/leave'
import { approvalLifecycleRank } from './approval-lifecycle-rank'
import { ENCASHMENT_SORT_GETTERS } from './leave-encashment-sort-getters'
import type { LeaveEncashment } from '../types/leave-encashment'

//  duoc-CR-748: máy chủ xếp cột Trạng thái của đơn nghỉ / nghỉ bù / thanh toán phép / đặt phòng theo DÒNG ĐỜI
//  (`APPROVAL_LIFECYCLE_ORDER`); hàng đợi xếp ở trình duyệt (Cần tôi duyệt, Tôi đã duyệt) phải ra cùng thứ tự.
describe('approvalLifecycleRank', () => {
  it('ranks Returned before Approved, matching the server lifecycle order', () => {
    const order = [
      LEAVE_STATUS.CANCELLED,
      LEAVE_STATUS.RETURNED,
      LEAVE_STATUS.REJECTED,
      LEAVE_STATUS.APPROVED,
      LEAVE_STATUS.PENDING,
      LEAVE_STATUS.DRAFT,
    ].sort((a, b) => (approvalLifecycleRank(a) ?? 99) - (approvalLifecycleRank(b) ?? 99))
    expect(order).toEqual([
      LEAVE_STATUS.DRAFT,
      LEAVE_STATUS.PENDING,
      LEAVE_STATUS.RETURNED,
      LEAVE_STATUS.APPROVED,
      LEAVE_STATUS.REJECTED,
      LEAVE_STATUS.CANCELLED,
    ])
  })

  it('treats a missing status as blank and puts unknown codes after every known one', () => {
    expect(approvalLifecycleRank(null)).toBeNull()
    expect(approvalLifecycleRank(undefined)).toBeNull()
    expect(approvalLifecycleRank(99)).toBeGreaterThan(approvalLifecycleRank(LEAVE_STATUS.CANCELLED) ?? 0)
  })

  it('sorts the encashment Status column by lifecycle rank, not by raw code', () => {
    const rows = [
      { id: 1, status: LEAVE_STATUS.APPROVED },
      { id: 2, status: LEAVE_STATUS.RETURNED },
      { id: 3, status: LEAVE_STATUS.REJECTED },
    ] as unknown as LeaveEncashment[]
    const sorted = sortRowsByCell(rows, 'status', 'asc', ENCASHMENT_SORT_GETTERS)
    expect(sorted.map((r) => r.id)).toEqual([2, 1, 3])
  })
})
