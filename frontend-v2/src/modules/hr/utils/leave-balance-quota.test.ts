import { describe, expect, it } from 'vitest'

import type { LeaveBalance } from '../types/leave'
import { hasQuota } from './leave-balance-quota'

function balance(overrides: Partial<LeaveBalance> = {}): LeaveBalance {
  return {
    id: 1,
    company_id: 1,
    employee_id: 3,
    employee_name: 'Lê Thị C',
    leave_type_id: 4,
    leave_type_name: 'Phép năm',
    year: 2026,
    allocated_days: 0,
    seniority_days: 0,
    carried_days: 0,
    carried_out_days: 0,
    carried_expired_days: 0,
    adjusted_days: 0,
    used_days: 0,
    pending_days: 0,
    total_days: 0,
    remaining_days: 0,
    note: '',
    ...overrides,
  }
}

describe('hasQuota', () => {
  it('không cấp gì thì KHÔNG có quỹ — số 0 ở đó nghĩa là "loại này không cấp", không phải "hết phép"', () => {
    //  Nghỉ tang chế · Nghỉ bù · Nghỉ cưới hỏi đều hạn mức 0 và chiếm phần lớn
    //  số dòng; tô đỏ hết thì màu đỏ mất nghĩa đúng chỗ nó cần có nghĩa.
    expect(hasQuota(balance())).toBe(false)
  })

  it('có hạn mức thì có quỹ', () => {
    expect(hasQuota(balance({ allocated_days: 12 }))).toBe(true)
  })

  it('phép mang sang hoặc điều chỉnh tay CŨNG là quỹ tiêu được', () => {
    //  Người hạn mức 0 nhưng được chuyển sang 3 ngày rồi tiêu hết thì đúng là
    //  *hết phép* — hỏi mỗi `allocated_days` sẽ bỏ sót ca này.
    expect(hasQuota(balance({ carried_days: 3 }))).toBe(true)
    expect(hasQuota(balance({ seniority_days: 2 }))).toBe(true)
    expect(hasQuota(balance({ adjusted_days: 1 }))).toBe(true)
  })

  it('điều chỉnh tay ÂM cũng tính là có quỹ — nó là dấu vết ai đó đã đụng vào dòng này', () => {
    expect(hasQuota(balance({ adjusted_days: -2 }))).toBe(true)
  })

  it('đã nghỉ / chờ duyệt KHÔNG phải quỹ', () => {
    //  Hai cột đó là phần TIÊU RA. Lấy chúng làm dấu hiệu "có quỹ" thì một dòng
    //  hạn mức 0 mà lỡ có đơn treo sẽ tự nhiên hóa đỏ.
    expect(hasQuota(balance({ used_days: 2, pending_days: 1 }))).toBe(false)
  })
})
