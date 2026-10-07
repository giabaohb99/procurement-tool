import { describe, expect, it } from 'vitest'

import { makeLaborContract, laborContractEmployee } from '../components/labor-contract-fixture'
import {
  MAX_MONEY,
  buildContractFormDefaults,
  laborContractSchema,
  toLaborContractPayload,
  type LaborContractFormValues,
} from './labor-contract-schema'

const base: LaborContractFormValues = {
  contract_type: 2,
  contract_no: '',
  start_date: '2026-01-01',
  end_date: '2026-12-31',
  job_title: '',
  work_location: '',
  base_salary: 0,
  insurance_salary: 0,
  allowance: 0,
  allowance_note: '',
  note: '',
}

function firstError(values: Partial<LaborContractFormValues> | Record<string, unknown>) {
  const r = laborContractSchema.safeParse({ ...base, ...values })
  return r.success ? null : { path: r.error.issues[0].path.join('.'), message: r.error.issues[0].message }
}

describe('laborContractSchema', () => {
  it('giá trị hợp lệ qua được', () => {
    expect(firstError({})).toBeNull()
  })
  it('loại chưa chọn (0) -> lỗi ở ô loại, không chồng lỗi ngày', () => {
    const r = laborContractSchema.safeParse({ ...base, contract_type: 0, end_date: '' })
    expect(r.success).toBe(false)
    if (!r.success) expect(r.error.issues.map((i) => i.path[0])).toEqual(['contract_type'])
  })
  it('KHÔNG XĐ THỜI HẠN có ngày kết thúc -> lỗi', () => {
    expect(firstError({ contract_type: 3, end_date: '2026-12-31' })?.path).toBe('end_date')
    expect(firstError({ contract_type: 3, end_date: '' })).toBeNull()
  })
  it.each([1, 2, 4, 5])('loại %i thiếu ngày kết thúc -> lỗi', (t) => {
    expect(firstError({ contract_type: t, end_date: '' })?.path).toBe('end_date')
  })
  it('loại «Khác» (9) cho phép có hoặc không ngày kết thúc', () => {
    expect(firstError({ contract_type: 9, end_date: '' })).toBeNull()
    expect(firstError({ contract_type: 9, end_date: '2026-06-01' })).toBeNull()
  })
  it('kết thúc trước bắt đầu -> lỗi; cùng ngày thì qua', () => {
    expect(firstError({ end_date: '2025-12-31' })?.message).toMatch(/sau hoặc bằng/)
    expect(firstError({ end_date: '2026-01-01' })).toBeNull()
  })
  it('thiếu ngày bắt đầu, hoặc chỉ khoảng trắng -> lỗi', () => {
    expect(firstError({ start_date: '' })?.path).toBe('start_date')
    expect(firstError({ start_date: '   ' })?.path).toBe('start_date')
  })
  it.each([-1, 1.5, MAX_MONEY + 1, Number.NaN, Number.POSITIVE_INFINITY])('tiền %p bị từ chối', (v) => {
    expect(firstError({ base_salary: v })?.path).toBe('base_salary')
    expect(firstError({ allowance: v })?.path).toBe('allowance')
  })
  it('tiền = 0 và đúng trần 10^12 đều hợp lệ', () => {
    expect(firstError({ base_salary: 0 })).toBeNull()
    expect(firstError({ insurance_salary: MAX_MONEY })).toBeNull()
  })
  it('tiền dạng chuỗi (hack form) bị từ chối', () => {
    expect(firstError({ base_salary: '15000000' })?.path).toBe('base_salary')
  })
  it('giới hạn độ dài khớp backend (50/100/255/500)', () => {
    expect(firstError({ contract_no: 'a'.repeat(51) })?.path).toBe('contract_no')
    expect(firstError({ job_title: 'a'.repeat(101) })?.path).toBe('job_title')
    expect(firstError({ work_location: 'a'.repeat(256) })?.path).toBe('work_location')
    expect(firstError({ allowance_note: 'a'.repeat(501) })?.path).toBe('allowance_note')
    expect(firstError({ note: 'a'.repeat(501) })?.path).toBe('note')
    expect(firstError({ contract_no: 'a'.repeat(50), job_title: 'a'.repeat(100) })).toBeNull()
  })
})

describe('toLaborContractPayload', () => {
  it('lúc SỬA, chức danh / địa điểm xóa trắng gửi "" (không phải null) để backend ghi đè được', () => {
    const p = toLaborContractPayload({ ...base, job_title: '  ', work_location: '' }, 'edit')
    expect(p.job_title).toBe('')
    expect(p.work_location).toBe('')
    // Lập mới vẫn gửi null để backend lấy mặc định từ hồ sơ.
    expect(toLaborContractPayload({ ...base, job_title: '', work_location: '' }, 'create').job_title).toBeNull()
  })

  it('ngày kết thúc rỗng -> null (không gửi chuỗi rỗng); chức danh/địa điểm rỗng -> null', () => {
    const p = toLaborContractPayload({ ...base, contract_type: 3, end_date: '', job_title: '  ', work_location: '' })
    expect(p.end_date).toBeNull()
    expect(p.job_title).toBeNull()
    expect(p.work_location).toBeNull()
  })
  it('cắt khoảng trắng đầu/cuối và giữ nguyên số tiền', () => {
    const p = toLaborContractPayload({ ...base, contract_no: ' 01/HĐ ', job_title: ' NV ', base_salary: 123, note: ' ghi ' })
    expect(p).toMatchObject({ contract_no: '01/HĐ', job_title: 'NV', base_salary: 123, note: 'ghi' })
  })
  it('payload không chứa trường lạ (backend extra=forbid)', () => {
    expect(Object.keys(toLaborContractPayload(base)).sort()).toEqual(
      ['allowance', 'allowance_note', 'base_salary', 'contract_no', 'contract_type', 'end_date', 'insurance_salary', 'job_title', 'note', 'start_date', 'work_location'],
    )
  })
})

describe('buildContractFormDefaults', () => {
  it('lập mới: điền chức danh + địa điểm từ hồ sơ, loại chưa chọn', () => {
    const d = buildContractFormDefaults(laborContractEmployee)
    expect(d).toMatchObject({ contract_type: 0, job_title: 'Chuyên viên', work_location: 'Hà Nội', base_salary: 0 })
  })
  it('hồ sơ thiếu địa điểm (undefined) -> chuỗi rỗng, không "undefined"', () => {
    const d = buildContractFormDefaults({ position: '', work_location: undefined })
    expect(d.work_location).toBe('')
    expect(d.job_title).toBe('')
  })
  it('sửa: lấy theo dòng, end_date null -> chuỗi rỗng', () => {
    const d = buildContractFormDefaults(laborContractEmployee, makeLaborContract({ end_date: null, contract_type: 3, allowance: 7 }))
    expect(d).toMatchObject({ end_date: '', contract_type: 3, allowance: 7 })
  })
})
