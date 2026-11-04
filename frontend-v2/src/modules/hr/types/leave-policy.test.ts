import { describe, expect, it } from 'vitest'

import { LEAVE_POLICY_ASSIGNMENT_STATE, LEAVE_POLICY_ASSIGNMENT_STATE_LABELS } from './leave-policy'

/**
 * Bản chép tay của `LeavePolicyAssignmentState` (backend `leave/constants.py`) — `gen_status_ts.py` chỉ sinh
 * bộ mã CHUỖI. Đổi số mục / số mã ở backend mà quên sửa bên này thì bài này đỏ.
 */
describe('LEAVE_POLICY_ASSIGNMENT_STATE', () => {
  it('mirrors the backend IntEnum: exactly 1 upcoming, 2 active, 3 ended, each with a label', () => {
    expect(LEAVE_POLICY_ASSIGNMENT_STATE).toEqual({ UPCOMING: 1, ACTIVE: 2, ENDED: 3 })
    expect(LEAVE_POLICY_ASSIGNMENT_STATE_LABELS).toEqual({
      1: 'Sắp tới',
      2: 'Đang hiệu lực',
      3: 'Đã kết thúc',
    })
  })
})
