import { describe, expect, it } from 'vitest'

import type { AuthUser } from '@/core/auth/auth-types'
import type { ListParams } from '@/shared/types/api'
import {
  addInCondition,
  buildClearParams,
  isSameRange,
  resolveMyEmployeeCode,
  resolveMyEmployeeId,
  resolveMyEmployeeName,
  toggleRange,
} from './list-quick-chips'

function user(patch: Partial<AuthUser>): AuthUser {
  return { id: 1, email: 'a@dego.vn', full_name: 'a@dego.vn', permissions: {}, ...patch }
}

describe('isSameRange / toggleRange', () => {
  const month: [string, string] = ['2026-10-01', '2026-10-31']

  it('is active only when BOTH ends match — a hand-picked half range is not the chip', () => {
    expect(isSameRange('2026-10-01', '2026-10-31', month)).toBe(true)
    expect(isSameRange('2026-10-01', '', month)).toBe(false)
    expect(isSameRange('', '2026-10-31', month)).toBe(false)
    expect(isSameRange('', '', month)).toBe(false)
  })

  it('switches the range on, then off again', () => {
    expect(toggleRange('', '', month)).toEqual(month)
    expect(toggleRange('2026-10-01', '2026-10-31', month)).toEqual(['', ''])
  })

  it('replaces a different range instead of clearing it', () => {
    //  Người dùng đang xem tháng 9 rồi bấm *Tháng này*: mong ra tháng 10, không phải bỏ lọc.
    expect(toggleRange('2026-09-01', '2026-09-30', month)).toEqual(month)
  })
})

describe('resolveMyEmployee*', () => {
  it('gives nothing for an account with no employee record', () => {
    //  `/api/auth/me` trả `full_name = email` và `emp_code = ""` khi tài khoản chưa
    //  gắn nhân sự — lọc theo email đó là ra bảng rỗng mà không ai hiểu vì sao.
    const bare = user({ emp_code: '', employee_id: undefined })
    expect(resolveMyEmployeeCode(bare)).toBeNull()
    expect(resolveMyEmployeeId(bare)).toBeNull()
    expect(resolveMyEmployeeName(bare)).toBeNull()
  })

  it('treats employee_id 0 as "no employee", not as a real id', () => {
    expect(resolveMyEmployeeId(user({ employee_id: 0 }))).toBeNull()
  })

  it('trims the code and the name', () => {
    const linked = user({ employee_id: 9, emp_code: ' NSU209 ', full_name: '  Huỳnh Gia Bảo ' })
    expect(resolveMyEmployeeCode(linked)).toBe('NSU209')
    expect(resolveMyEmployeeId(linked)).toBe('9')
    expect(resolveMyEmployeeName(linked)).toBe('Huỳnh Gia Bảo')
  })

  it('gives nothing when there is no user at all', () => {
    expect(resolveMyEmployeeCode(null)).toBeNull()
    expect(resolveMyEmployeeId(null)).toBeNull()
    expect(resolveMyEmployeeName(null)).toBeNull()
  })
})

describe('buildClearParams', () => {
  it('clears every quick key in one record — one URL write, not ten', () => {
    expect(buildClearParams(['status', 'assignee'], new URLSearchParams('status=a'))).toEqual({
      status: null,
      assignee: null,
    })
  })

  it('leaves advanced conditions, the keyword and the sort alone unless asked', () => {
    const current = new URLSearchParams('q=abc&sort_by=id&code__contains=A&conjunction=or')
    expect(buildClearParams(['status'], current)).toEqual({ status: null })
  })

  it('also clears advanced conditions and the conjunction when asked, but never the keyword or sort', () => {
    const current = new URLSearchParams('q=abc&sort_by=id&code__contains=A&purpose__contains=B&conjunction=or')
    expect(buildClearParams(['status'], current, true)).toEqual({
      status: null,
      code__contains: null,
      purpose__contains: null,
      conjunction: null,
    })
  })
})

describe('addInCondition', () => {
  it('adds an IN condition when the advanced filter has none on that field', () => {
    const params: ListParams = { page: 1 }
    expect(addInCondition(params, 'status', ['approved', 'processing'])).toBe(true)
    expect(params.status__in).toBe('approved,processing')
  })

  it('keeps only the overlap when the advanced filter already has an IN on that field', () => {
    //  Hai điều kiện cùng cột nối bằng AND: ghi đè là nuốt mất điều kiện người dùng tự dựng.
    const params: ListParams = { status__in: 'processing,done' }
    expect(addInCondition(params, 'status', ['approved', 'processing'])).toBe(true)
    expect(params.status__in).toBe('processing')
  })

  it('sends a value that matches nothing when the overlap is empty, rather than dropping the filter', () => {
    //  Gửi chuỗi rỗng thì máy chủ bỏ điều kiện và trả CẢ tập — ngược hẳn ý người dùng.
    const params: ListParams = { status__in: 'done' }
    expect(addInCondition(params, 'status', ['approved'])).toBe(true)
    expect(params.status__in).not.toBe('')
    expect(String(params.status__in).split(',')).not.toContain('done')
    expect(String(params.status__in).split(',')).not.toContain('approved')
  })

  it('refuses to join when the advanced filter combines its conditions with OR', () => {
    //  Máy chủ nối MỌI điều kiện có hậu tố bằng `conjunction`: thêm vào lúc đang OR là
    //  chip thành "hoặc đang chờ xử lý", bảng ra nhiều hơn chứ không ít đi.
    const params: ListParams = { conjunction: 'or', code__contains: 'A', purpose__contains: 'B' }
    expect(addInCondition(params, 'status', ['approved'])).toBe(false)
    expect(params.status__in).toBeUndefined()
  })
})
