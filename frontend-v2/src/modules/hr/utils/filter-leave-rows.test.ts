import { describe, expect, it } from 'vitest'

import {
  ALL_OPTION,
  filterLeaveRows,
  isFiltering,
  leaveTypesIn,
  matchesKeyword,
} from './filter-leave-rows'
import { LEAVE_SESSION, LEAVE_STATUS, LEAVE_UNIT, type LeaveRequest } from '../types/leave'

/**
 * Lọc đơn nghỉ ở phía màn hình — dùng chung cho hai tab hộp việc duyệt và chế
 * độ NGÀY của Lịch nghỉ.
 */
function request(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 1,
    code: 'NP001',
    company_id: 1,
    department_id: 2,
    employee_id: 3,
    employee_name: 'Lê Văn Nhân Sự Ba',
    leave_type_id: 4,
    leave_type_name: 'Phép năm',
    from_date: '2026-09-11',
    to_date: '2026-09-14',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    unit: LEAVE_UNIT.DAY,
    total_days: 3,
    reason: 'Về quê',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.PENDING,
    approval_instance_id: 0,
    document_id: 0,
    submitted_at: null,
    decided_at: null,
    decision_note: '',
    ...overrides,
  }
}

describe('matchesKeyword', () => {
  it('khớp TÊN người nghỉ', () => {
    expect(matchesKeyword(request(), 'nhân sự')).toBe(true)
  })

  it('khớp SỐ ĐƠN — thứ đọc được trong thư báo việc', () => {
    expect(matchesKeyword(request({ code: 'NP015' }), 'np015')).toBe(true)
  })

  it('khớp LÝ DO — khi chỉ nhớ mang máng "cái đơn về quê"', () => {
    expect(matchesKeyword(request(), 'quê')).toBe(true)
  })

  it('không phân biệt hoa thường', () => {
    //  Không ai gõ đúng hoa thường tên người khác.
    expect(matchesKeyword(request(), 'LÊ VĂN')).toBe(true)
    expect(matchesKeyword(request({ code: 'NP015' }), 'np015')).toBe(true)
  })

  it('khớp GIỮA chuỗi, không chỉ đầu chuỗi', () => {
    //  Người ta nhớ tên riêng chứ ít khi nhớ họ.
    expect(matchesKeyword(request(), 'Ba')).toBe(true)
  })

  it('từ khóa RỖNG hoặc toàn khoảng trắng thì khớp mọi dòng', () => {
    for (const k of ['', '   ', '\n\t ']) {
      expect(matchesKeyword(request(), k)).toBe(true)
    }
  })

  it('gõ sai thì KHÔNG khớp — đừng lặng lẽ bỏ qua bộ lọc', () => {
    expect(matchesKeyword(request(), 'zzzkhongcoai')).toBe(false)
  })

  it('thiếu tên hoặc thiếu lý do vẫn không nổ', () => {
    //  `employee_name` chỉ có ở vài đường API; `reason` để trống được.
    const thieu = request({ employee_name: undefined, reason: '' })
    expect(matchesKeyword(thieu, 'quê')).toBe(false)
    expect(matchesKeyword(thieu, 'NP001')).toBe(true)
  })
})

describe('leaveTypesIn', () => {
  it('loại nghỉ TRÙNG nhau chỉ ra MỘT lần', () => {
    //  Ba đơn cùng "Phép năm" mà ô chọn hiện ba dòng thì đọc như dữ liệu hỏng.
    const rows = [request({ id: 1 }), request({ id: 2 }), request({ id: 3 })]
    expect(leaveTypesIn(rows)).toEqual([{ id: 4, name: 'Phép năm' }])
  })

  it('sắp theo TÊN để thứ tự ô chọn không nhảy mỗi lần dữ liệu về', () => {
    const rows = [
      request({ id: 1, leave_type_id: 2, leave_type_name: 'Nghỉ không lương' }),
      request({ id: 2, leave_type_id: 1, leave_type_name: 'Phép năm' }),
      request({ id: 3, leave_type_id: 3, leave_type_name: 'Nghỉ bù' }),
    ]
    expect(leaveTypesIn(rows).map((t) => t.name)).toEqual([
      'Nghỉ bù',
      'Nghỉ không lương',
      'Phép năm',
    ])
  })

  it('thiếu tên loại thì rơi về mã, không để nhãn trống', () => {
    const rows = [request({ leave_type_id: 9, leave_type_name: undefined })]
    expect(leaveTypesIn(rows)).toEqual([{ id: 9, name: '#9' }])
  })

  it('danh sách rỗng thì trả rỗng', () => {
    expect(leaveTypesIn([])).toEqual([])
  })
})

describe('filterLeaveRows', () => {
  const rows = [
    request({ id: 1, code: 'NP001', employee_name: 'Phạm Thị Kế Toán', leave_type_id: 1 }),
    request({ id: 2, code: 'NP002', employee_name: 'Trần Trưởng Phòng', leave_type_id: 2 }),
    request({ id: 3, code: 'NP003', employee_name: 'Lý Phó Phòng', leave_type_id: 2 }),
  ]

  it('không lọc gì thì trả NGUYÊN danh sách', () => {
    expect(filterLeaveRows(rows, { keyword: '', typeId: ALL_OPTION })).toHaveLength(3)
  })

  it('lọc theo loại nghỉ', () => {
    const got = filterLeaveRows(rows, { keyword: '', typeId: '2' })
    expect(got.map((r) => r.code)).toEqual(['NP002', 'NP003'])
  })

  it('từ khóa và loại nghỉ CỘNG DỒN với nhau, không thay thế nhau', () => {
    //  Lọc loại 2 rồi gõ "Phó" phải còn đúng một dòng — nếu hai bộ lọc thay
    //  nhau thì người dùng thu hẹp mãi mà danh sách không hẹp lại.
    const got = filterLeaveRows(rows, { keyword: 'Phó', typeId: '2' })
    expect(got.map((r) => r.code)).toEqual(['NP003'])
  })

  it('không ai khớp thì trả RỖNG, không âm thầm bỏ qua bộ lọc', () => {
    expect(filterLeaveRows(rows, { keyword: 'zzz', typeId: ALL_OPTION })).toEqual([])
  })

  it('giữ nguyên kiểu của dòng — dùng được cho cả `LeaveInboxRow`', () => {
    const inbox = rows.map((r) => ({ ...r, task: { id: 1 } }))
    const got = filterLeaveRows(inbox, { keyword: 'Phó', typeId: ALL_OPTION })
    expect(got[0].task.id).toBe(1)
  })
})

describe('isFiltering', () => {
  it('nhận ra đang lọc để đổi câu lúc bảng rỗng', () => {
    //  "Không có đơn nào khớp bộ lọc" khác hẳn "chưa có đơn nào" — lẫn hai câu
    //  thì người dùng tưởng cả hàng đợi trống trong khi chỉ gõ sai một chữ.
    expect(isFiltering({ keyword: 'a', typeId: ALL_OPTION })).toBe(true)
    expect(isFiltering({ keyword: '', typeId: '2' })).toBe(true)
    expect(isFiltering({ keyword: '', typeId: ALL_OPTION })).toBe(false)
    //  Khoảng trắng KHÔNG tính là đang lọc.
    expect(isFiltering({ keyword: '   ', typeId: ALL_OPTION })).toBe(false)
  })
})
