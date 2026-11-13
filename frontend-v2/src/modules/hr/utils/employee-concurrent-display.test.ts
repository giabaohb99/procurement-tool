import { describe, expect, it } from 'vitest'

import { CONCURRENT_KIND, CONCURRENT_STATUS } from '@/shared/constants/statuses'
import {
  CONCURRENT_ACTIVE,
  CONCURRENT_ENDED,
  CONCURRENT_KIND_COMPANY,
  CONCURRENT_KIND_DEPARTMENT,
  CONCURRENT_UPCOMING,
  type EmployeeConcurrent,
} from '../types/employee-concurrent'
import {
  concurrentKindLabel,
  concurrentPeriodLabel,
  concurrentPlaceLabel,
  concurrentRowsEndingOnCompanyChange,
  concurrentStatusLabel,
  hasOpenCompanyConcurrent,
  isConcurrentUnstarted,
  sortConcurrentRowsDefault,
} from './employee-concurrent-display'

function row(overrides: Partial<EmployeeConcurrent>): EmployeeConcurrent {
  return {
    id: 1,
    employee_id: 1,
    kind: CONCURRENT_KIND_DEPARTMENT,
    kind_label: 'Phòng ban',
    company_id: 10,
    company_name: 'DEGO A',
    department_id: 5,
    department_name: 'Kế toán',
    position_id: 0,
    position_label: '',
    from_date: '2026-01-01',
    to_date: null,
    decision_no: '',
    decision_date: null,
    note: '',
    counts_scope: true,
    work_history_id: 0,
    status: CONCURRENT_ACTIVE,
    status_label: '',
    file_count: 0,
    ...overrides,
  }
}

describe('concurrent status codes', () => {
  //  Ba hằng số mirror `ConcurrentStatus` của backend; lệch với bộ mã sinh là huy hiệu + xếp + hộp đổi pháp nhân sai cùng lúc.
  it('constants match the generated code set exactly (1 Sắp tới, 2 Đang hiệu lực, 3 Đã hết)', () => {
    expect(CONCURRENT_STATUS.map((o) => [o.value, o.label])).toEqual([
      [String(CONCURRENT_UPCOMING), 'Sắp tới'],
      [String(CONCURRENT_ACTIVE), 'Đang hiệu lực'],
      [String(CONCURRENT_ENDED), 'Đã hết'],
    ])
  })

  it('label falls back to the generated set when the backend label is empty', () => {
    expect(concurrentStatusLabel({ status: 3, status_label: '' })).toBe('Đã hết')
    expect(concurrentStatusLabel({ status: 1, status_label: 'Nhãn backend' })).toBe('Nhãn backend')
    expect(concurrentStatusLabel({ status: 99, status_label: '' })).toBe('')
  })
})

describe('sortConcurrentRowsDefault', () => {
  it('active first, then upcoming, then ended; newest start first inside a group; ties by id desc', () => {
    const rows = [
      row({ id: 1, status: CONCURRENT_ENDED, from_date: '2026-06-01' }),
      row({ id: 2, status: CONCURRENT_UPCOMING, from_date: '2027-01-01' }),
      row({ id: 3, status: CONCURRENT_ACTIVE, from_date: '2025-01-01' }),
      row({ id: 4, status: CONCURRENT_ACTIVE, from_date: '2026-01-01' }),
      row({ id: 5, status: CONCURRENT_ACTIVE, from_date: '2026-01-01' }),
      row({ id: 6, status: CONCURRENT_ACTIVE, from_date: null }),
    ]
    expect(sortConcurrentRowsDefault(rows).map((r) => r.id)).toEqual([5, 4, 3, 6, 2, 1])
  })

  it('does not mutate the input and handles an empty list', () => {
    const rows = [row({ id: 1 }), row({ id: 2 })]
    sortConcurrentRowsDefault(rows)
    expect(rows.map((r) => r.id)).toEqual([1, 2])
    expect(sortConcurrentRowsDefault([])).toEqual([])
  })
})

describe('concurrentRowsEndingOnCompanyChange (A=10 → C=20)', () => {
  const company = (over: Partial<EmployeeConcurrent>) =>
    row({ kind: CONCURRENT_KIND_COMPANY, department_id: 0, department_name: '', ...over })
  const rows = [
    row({ id: 1, company_id: 10, status: CONCURRENT_ACTIVE }),
    row({ id: 2, company_id: 10, status: CONCURRENT_UPCOMING }),
    row({ id: 3, company_id: 10, status: CONCURRENT_ENDED }),
    company({ id: 4, company_id: 20, status: CONCURRENT_ACTIVE }),
    company({ id: 5, company_id: 20, status: CONCURRENT_ENDED }),
    company({ id: 6, company_id: 30, status: CONCURRENT_ACTIVE }),
    //  Công ty CŨ ở loại Công ty: không đụng (đó chính là "giữ ở công ty cũ").
    company({ id: 7, company_id: 10, status: CONCURRENT_ACTIVE }),
    //  Loại Phòng ban mà mang công ty C (dữ liệu trôi) — backend chỉ lọc loại 1 theo công ty CŨ.
    row({ id: 8, company_id: 20, status: CONCURRENT_ACTIVE }),
  ]

  it('Phòng ban rows at the OLD company + Công ty rows equal to the NEW company, non-ended only', () => {
    expect(concurrentRowsEndingOnCompanyChange(rows, 10, 20).map((r) => r.id)).toEqual([1, 2, 4])
  })

  it('no real move (0 on either side, or same company) → nothing ends', () => {
    expect(concurrentRowsEndingOnCompanyChange(rows, 0, 20)).toEqual([])
    expect(concurrentRowsEndingOnCompanyChange(rows, 10, 0)).toEqual([])
    expect(concurrentRowsEndingOnCompanyChange(rows, 10, 10)).toEqual([])
    expect(concurrentRowsEndingOnCompanyChange([], 10, 20)).toEqual([])
  })
})

describe('hasOpenCompanyConcurrent', () => {
  it('true only for a non-ended Công ty row at exactly that company', () => {
    const live = row({ kind: CONCURRENT_KIND_COMPANY, company_id: 10, status: CONCURRENT_UPCOMING })
    expect(hasOpenCompanyConcurrent([live], 10)).toBe(true)
    expect(hasOpenCompanyConcurrent([{ ...live, status: CONCURRENT_ENDED }], 10)).toBe(false)
    expect(hasOpenCompanyConcurrent([{ ...live, company_id: 11 }], 10)).toBe(false)
    //  Dòng Phòng ban ở công ty đó KHÔNG phải ghế ở cả công ty.
    expect(hasOpenCompanyConcurrent([row({ company_id: 10, status: CONCURRENT_ACTIVE })], 10)).toBe(false)
    expect(hasOpenCompanyConcurrent([], 10)).toBe(false)
  })
})

describe('concurrentPlaceLabel / concurrentKindLabel', () => {
  it('room name for Phòng ban, company name for Công ty — never both', () => {
    expect(concurrentPlaceLabel(row({ department_name: 'Kế toán', company_name: 'DEGO A' }))).toBe('Kế toán')
    expect(
      concurrentPlaceLabel(
        row({ kind: CONCURRENT_KIND_COMPANY, company_name: 'DEGO B', department_id: 0, department_name: '' }),
      ),
    ).toBe('DEGO B')
  })

  it('missing names fall back to the id, never an empty cell', () => {
    expect(concurrentPlaceLabel(row({ department_id: 5, department_name: '' }))).toBe('Phòng #5')
    expect(concurrentPlaceLabel(row({ kind: CONCURRENT_KIND_COMPANY, company_id: 9, company_name: '' }))).toBe('Công ty #9')
  })

  it('kind label prefers backend text, falls back to the generated code set', () => {
    expect(concurrentKindLabel({ kind: CONCURRENT_KIND_COMPANY, kind_label: '' })).toBe('Công ty')
    expect(concurrentKindLabel({ kind: CONCURRENT_KIND_DEPARTMENT, kind_label: 'X' })).toBe('X')
  })

  it('kind constants follow the generated CONCURRENT_KIND set (backend renumbers → this goes red)', () => {
    expect(CONCURRENT_KIND.map((o) => [Number(o.value), o.label])).toEqual([
      [CONCURRENT_KIND_DEPARTMENT, 'Phòng ban'],
      [CONCURRENT_KIND_COMPANY, 'Công ty'],
    ])
  })
})

describe('isConcurrentUnstarted', () => {
  //  Backend xóa dòng `from_date >= hôm nay` (kể cả đúng hôm nay, đang hiện "Đang hiệu lực") — phải báo đúng dòng đó.
  it('a row starting TODAY counts as unstarted (it will be deleted, not ended)', () => {
    expect(isConcurrentUnstarted({ from_date: '2026-11-12' }, '2026-11-12')).toBe(true)
    expect(isConcurrentUnstarted({ from_date: '2026-11-13' }, '2026-11-12')).toBe(true)
    expect(isConcurrentUnstarted({ from_date: '2026-11-11' }, '2026-11-12')).toBe(false)
  })

  it('legacy row without a start date is never unstarted', () => {
    expect(isConcurrentUnstarted({ from_date: null }, '2026-11-12')).toBe(false)
  })
})

describe('concurrentPeriodLabel', () => {
  it('formats both ends, open end, missing start, and nothing', () => {
    expect(concurrentPeriodLabel({ from_date: '2026-11-01', to_date: '2026-11-30' })).toBe('01/11/2026 – 30/11/2026')
    expect(concurrentPeriodLabel({ from_date: '2026-11-01', to_date: null })).toBe('Từ 01/11/2026')
    expect(concurrentPeriodLabel({ from_date: null, to_date: '2026-11-30' })).toBe('Đến 30/11/2026')
    expect(concurrentPeriodLabel({ from_date: null, to_date: null })).toBe('')
  })
})
