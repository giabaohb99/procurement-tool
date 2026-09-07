import { describe, expect, it } from 'vitest'

import { hasMultipleLeaveTypes, leaveLinesText, leaveTypeLabel } from './leave-type-label'
import { LEAVE_SESSION, LEAVE_STATUS, LEAVE_UNIT, type LeaveRequest } from '../types/leave'

function request(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 1,
    code: 'NP001',
    company_id: 1,
    department_id: 2,
    employee_id: 3,
    leave_type_id: 4,
    leave_type_name: 'Phép năm',
    from_date: '2026-01-05',
    to_date: '2026-01-08',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    unit: LEAVE_UNIT.DAY,
    total_days: 4,
    reason: 'Về quê',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.DRAFT,
    approval_instance_id: 0,
    document_id: 0,
    decision_note: '',
    ...overrides,
  }
}

const twoLines = [
  { id: 1, leave_type_id: 4, leave_type_name: 'Phép năm', days: 3, sort_order: 0 },
  { id: 2, leave_type_id: 5, leave_type_name: 'Nghỉ không lương', days: 1, sort_order: 1 },
]

describe('leaveTypeLabel', () => {
  it('đơn một loại hiện đúng tên loại đó', () => {
    expect(leaveTypeLabel(request({ lines: [twoLines[0]] }))).toBe('Phép năm')
  })

  it('đơn nhiều loại hiện «loại chính +n» — ô bảng cao 35px không chứa nổi hai tên', () => {
    expect(leaveTypeLabel(request({ lines: twoLines }))).toBe('Phép năm +1')
  })

  it('KHÔNG có bản kê thì vẫn hiện tên loại chính, không hiện «+0»', () => {
    //  Đường trả về nào không gom bản kê thì `lines` rỗng. Thiếu chữ «+1» còn hơn
    //  bịa ra một con số.
    expect(leaveTypeLabel(request({ lines: [] }))).toBe('Phép năm')
    expect(leaveTypeLabel(request({ lines: undefined }))).toBe('Phép năm')
  })

  it('đơn hỏng, không có cả tên loại chính, ra gạch ngang chứ không ra chuỗi rỗng', () => {
    expect(leaveTypeLabel(request({ leave_type_name: '', lines: [] }))).toBe('—')
    expect(leaveTypeLabel(request({ leave_type_name: undefined, lines: [] }))).toBe('—')
  })

  it('ba loại trở lên vẫn đếm đúng', () => {
    const three = [...twoLines, { id: 3, leave_type_id: 6, leave_type_name: 'Nghỉ ốm', days: 1, sort_order: 2 }]
    expect(leaveTypeLabel(request({ lines: three }))).toBe('Phép năm +2')
  })
})

describe('leaveLinesText', () => {
  it('liệt kê đủ từng loại mấy ngày — dùng cho tooltip và hộp xác nhận duyệt', () => {
    expect(leaveLinesText(request({ lines: twoLines }))).toBe(
      'Phép năm 3 ngày · Nghỉ không lương 1 ngày',
    )
  })

  it('dòng thiếu tên loại thì hiện id, không hiện chuỗi rỗng lửng lơ', () => {
    expect(
      leaveLinesText(
        request({ lines: [{ id: 1, leave_type_id: 9, days: 2, sort_order: 0 }] }),
      ),
    ).toBe('#9 2 ngày')
  })

  it('không có bản kê thì ra chuỗi RỖNG — nơi gọi tự quyết hiện gì thay thế', () => {
    expect(leaveLinesText(request({ lines: [] }))).toBe('')
    expect(leaveLinesText(request({ lines: undefined }))).toBe('')
  })

  it('số ngày lẻ giữ nguyên, không làm tròn', () => {
    expect(
      leaveLinesText(
        request({ lines: [{ id: 1, leave_type_id: 4, leave_type_name: 'Phép năm', days: 0.13, sort_order: 0 }] }),
      ),
    ).toBe('Phép năm 0.13 ngày')
  })
})

describe('hasMultipleLeaveTypes', () => {
  it('chỉ đúng khi có từ HAI dòng trở lên', () => {
    expect(hasMultipleLeaveTypes(request({ lines: twoLines }))).toBe(true)
    expect(hasMultipleLeaveTypes(request({ lines: [twoLines[0]] }))).toBe(false)
    expect(hasMultipleLeaveTypes(request({ lines: [] }))).toBe(false)
    expect(hasMultipleLeaveTypes(request({ lines: undefined }))).toBe(false)
  })
})
