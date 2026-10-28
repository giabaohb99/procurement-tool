import { describe, expect, it } from 'vitest'

import {
  buildHeadcountPlanDepartmentOptions,
  buildHeadcountPlanYearOptions,
  normalizeHeadcountPlanPayload,
  splitImportErrorMessage,
} from './headcount-plan-options'

const DEPTS = [
  { id: 11, name: 'Kế toán', company_id: 1 },
  { id: 12, name: 'Kinh doanh', company_id: 1 },
  { id: 21, name: 'Kho', company_id: 2 },
]

describe('buildHeadcountPlanYearOptions', () => {
  it('offers next year first then three years back, newest on top', () => {
    expect(buildHeadcountPlanYearOptions(2026).map((o) => o.value)).toEqual(['2027', '2026', '2025', '2024', '2023'])
  })

  it('never offers a year the backend rejects (outside 2000–2100)', () => {
    expect(buildHeadcountPlanYearOptions(2001).map((o) => o.value)).toEqual(['2002', '2001', '2000'])
    expect(buildHeadcountPlanYearOptions(2100).map((o) => o.value)).toEqual(['2100', '2099', '2098', '2097'])
  })
})

describe('buildHeadcountPlanDepartmentOptions', () => {
  //  Phòng ban dùng chung cho mọi pháp nhân (chốt 28/10/2026) — lọc theo `company_id` từng làm mọi
  //  pháp nhân chỉ còn «Toàn pháp nhân» vì dữ liệu thật ghi 0 cho cả 18 phòng.
  it('lists every department regardless of company, after the whole-company row whose value is the real 0', () => {
    expect(buildHeadcountPlanDepartmentOptions(DEPTS)).toEqual([
      { value: '0', label: 'Toàn pháp nhân' },
      { value: '11', label: 'Kế toán' },
      { value: '21', label: 'Kho' },
      { value: '12', label: 'Kinh doanh' },
    ])
  })

  it('sorts by Vietnamese name and keeps a department only once', () => {
    const opts = buildHeadcountPlanDepartmentOptions([
      { id: 3, name: 'Đào tạo' },
      { id: 1, name: 'Ban giám đốc' },
      { id: 3, name: 'Đào tạo' },
      { id: 2, name: 'Dự án' },
    ])
    expect(opts.map((o) => o.label)).toEqual(['Toàn pháp nhân', 'Ban giám đốc', 'Dự án', 'Đào tạo'])
  })

  it('never lets a stray id 0 row shadow the whole-company option', () => {
    const opts = buildHeadcountPlanDepartmentOptions([{ id: 0, name: 'Rác' }, { id: 5, name: 'Kho' }])
    expect(opts).toEqual([
      { value: '0', label: 'Toàn pháp nhân' },
      { value: '5', label: 'Kho' },
    ])
  })

  it('still offers the whole-company row when the department list is empty or not loaded', () => {
    expect(buildHeadcountPlanDepartmentOptions([])).toEqual([{ value: '0', label: 'Toàn pháp nhân' }])
  })
})

describe('normalizeHeadcountPlanPayload', () => {
  it('turns select strings into the ints the backend schema forbids otherwise', () => {
    expect(
      normalizeHeadcountPlanPayload({ year: '2026', company_id: '3', department_id: '12', planned_headcount: 7, note: '' }),
    ).toEqual({ year: 2026, company_id: 3, department_id: 12, planned_headcount: 7, note: '' })
  })

  it('keeps department 0 (whole company) and maps an empty department to 0, not NaN', () => {
    expect(normalizeHeadcountPlanPayload({ year: '2026', company_id: '3', department_id: '0' }).department_id).toBe(0)
    expect(normalizeHeadcountPlanPayload({ year: '2026', company_id: '3', department_id: '' }).department_id).toBe(0)
  })

  it('does not add a payroll key when the form had no payroll field — backend would 403', () => {
    const out = normalizeHeadcountPlanPayload({ year: '2026', company_id: '3', planned_headcount: 2 })
    expect('planned_payroll_monthly' in out).toBe(false)
  })

  it('sends payroll as a number when present, null when cleared', () => {
    expect(normalizeHeadcountPlanPayload({ year: '2026', company_id: '1', planned_payroll_monthly: '150000000' }).planned_payroll_monthly).toBe(150000000)
    expect(normalizeHeadcountPlanPayload({ year: '2026', company_id: '1', planned_payroll_monthly: '' }).planned_payroll_monthly).toBeNull()
  })

  it('falls back to 0 for blank or garbage headcount instead of sending NaN', () => {
    expect(normalizeHeadcountPlanPayload({ year: '2026', company_id: '1', planned_headcount: '' }).planned_headcount).toBe(0)
    expect(normalizeHeadcountPlanPayload({ year: '2026', company_id: '1', planned_headcount: 'abc' }).planned_headcount).toBe(0)
  })
})

describe('splitImportErrorMessage', () => {
  it('drops the lead-in and gives one line per rejected CSV row', () => {
    expect(
      splitImportErrorMessage('Tệp CSV có lỗi, chưa ghi dòng nào: Dòng 2: mã pháp nhân không tồn tại | Dòng 3: year Input should be greater than or equal to 2000'),
    ).toEqual(['Dòng 2: mã pháp nhân không tồn tại', 'Dòng 3: year Input should be greater than or equal to 2000'])
  })

  it('keeps the "and N more" tail as its own line instead of gluing it to the last row', () => {
    expect(splitImportErrorMessage('Tệp CSV có lỗi, chưa ghi dòng nào: Dòng 2: a | Dòng 9: b (và 7 lỗi khác)')).toEqual([
      'Dòng 2: a',
      'Dòng 9: b',
      '…và 7 lỗi khác',
    ])
  })

  it('does not split inside a row whose own message holds several field errors', () => {
    expect(splitImportErrorMessage('Tệp CSV có lỗi, chưa ghi dòng nào: Dòng 4: year x; planned_headcount y')).toEqual([
      'Dòng 4: year x; planned_headcount y',
    ])
  })

  it('keeps a file-level sentence as a single line', () => {
    expect(splitImportErrorMessage('Tệp CSV thiếu cột: year, company_code')).toEqual(['Tệp CSV thiếu cột: year, company_code'])
    expect(splitImportErrorMessage('Tệp CSV tối đa 2000 dòng')).toEqual(['Tệp CSV tối đa 2000 dòng'])
  })

  it('returns nothing for an empty message', () => {
    expect(splitImportErrorMessage('   ')).toEqual([])
  })
})
