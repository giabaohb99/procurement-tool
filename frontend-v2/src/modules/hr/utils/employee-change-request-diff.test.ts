import { describe, expect, it } from 'vitest'

import { CHANGE_REQUEST_GROUP_FIELDS } from '../config/employee-profile-fields'
import { createEmptyFamilyRow } from '../config/employee-family-columns'
import type { Employee, EmployeeFamily } from '../types/employee'
import {
  buildChangeRequestPayload,
  normalizeFamilies,
  readChangeRequestValues,
} from './employee-change-request-diff'

function employee(overrides: Partial<Employee> = {}): Employee {
  return {
    id: 7,
    code: 'NSU007',
    full_name: 'Người Thử',
    gender: 1,
    date_of_birth: '1990-05-01',
    place_of_birth: 'Huế',
    ethnicity: 'Kinh',
    religion: '',
    marital_status: 1,
    children_count: 0,
    personal_email: 'thu@example.com',
    education_level: 4,
    major: 'Kế toán',
    bank_account_no: '0011',
    bank_account_name: 'NGUOI THU',
    bank_name: 'VCB',
    bank_branch: 'Huế',
    id_number: '046090000001',
    id_issue_date: '2021-01-02',
    id_issue_place: 'Cục CS',
    id_expiry_date: null,
    tax_code: '',
    social_insurance_no: '',
    health_care_place: 'BV Trung ương Huế',
    health_care_code: '46-001',
    ...overrides,
  } as Employee
}

function family(overrides: Partial<EmployeeFamily> = {}): EmployeeFamily {
  return { ...createEmptyFamilyRow(), id: 1, full_name: 'Mẹ Thử', relation: 3, gender: 2, ...overrides }
}

function build(
  draftValues: Record<string, unknown>,
  opts: { base?: Employee; families?: EmployeeFamily[]; draftFamilies?: EmployeeFamily[]; note?: string } = {},
) {
  const base = readChangeRequestValues(opts.base ?? employee())
  const baseFamilies = opts.families ?? [family()]
  return buildChangeRequestPayload(base, baseFamilies, {
    values: { ...base, ...draftValues } as typeof base,
    families: opts.draftFamilies ?? baseFamilies,
    note: opts.note ?? '',
  })
}

describe('buildChangeRequestPayload', () => {
  it('returns null when the draft equals the current profile (submit must be blocked)', () => {
    expect(build({})).toBeNull()
  })

  it('treats a note without any field change as no change', () => {
    expect(build({}, { note: 'Nhờ chị sửa giúp' })).toBeNull()
  })

  it('sends only the changed field, inside its own group, and omits untouched groups', () => {
    expect(build({ bank_name: 'ACB' })).toEqual({ bank: { bank_name: 'ACB' } })
  })

  it('ignores whitespace-only edits so a trailing space is not reported as a change', () => {
    expect(build({ place_of_birth: '  Huế  ' })).toBeNull()
  })

  it('sends null (not an empty string) for a cleared date — backend rejects "" on DATE NULL', () => {
    expect(build({ date_of_birth: '' })).toEqual({ personal: { date_of_birth: null } })
  })

  it('sends an empty string for a cleared text field — backend rejects null outside dates', () => {
    expect(build({ major: '' })).toEqual({ personal: { major: '' } })
  })

  it('compares codes numerically so "4" from a select equals the stored 4', () => {
    expect(build({ education_level: '4' })).toBeNull()
    expect(build({ education_level: 5 })).toEqual({ personal: { education_level: 5 } })
  })

  it('keeps several groups apart and attaches the trimmed note only when something changed', () => {
    expect(build({ gender: 2, id_number: ' 046090000009 ' }, { note: '  đổi CCCD mới  ' })).toEqual({
      personal: { gender: 2 },
      documents: { id_number: '046090000009' },
      note: 'đổi CCCD mới',
    })
  })

  it('treats null/undefined profile values as their empty form so an untouched legacy record is not a change', () => {
    //  Hồ sơ cũ thiếu hẳn các cột mở rộng (API trước duoc-CR-314) — không được thành "đổi".
    const legacy = { id: 9, code: 'X', full_name: 'Cũ' } as Employee
    expect(build({}, { base: legacy })).toBeNull()
  })

  it('does not count an added blank family row as a change (backend drops rows without a name)', () => {
    expect(build({}, { draftFamilies: [family(), createEmptyFamilyRow()] })).toBeNull()
  })

  it('sends the WHOLE family list when one member changes', () => {
    const payload = build(
      {},
      {
        families: [family(), family({ id: 2, full_name: 'Cha Thử', relation: 2, gender: 1 })],
        draftFamilies: [family({ id_number: '0123' }), family({ id: 2, full_name: 'Cha Thử', relation: 2, gender: 1 })],
      },
    )
    expect(payload?.families).toHaveLength(2)
    expect(payload?.families?.[0]).toMatchObject({ full_name: 'Mẹ Thử', id_number: '0123' })
    expect(payload).not.toHaveProperty('personal')
  })

  it('sends an empty family list when every member was removed', () => {
    expect(build({}, { draftFamilies: [] })).toEqual({ families: [] })
  })
})

describe('normalizeFamilies', () => {
  it('drops id/sort_order and maps an empty birth date to null', () => {
    expect(normalizeFamilies([family({ date_of_birth: '' as unknown as null, sort_order: 4 })])).toEqual([
      { full_name: 'Mẹ Thử', relation: 3, gender: 2, date_of_birth: null, phone: '', id_number: '' },
    ])
  })
})

describe('CHANGE_REQUEST_GROUP_FIELDS', () => {
  //  Phải khớp ĐÚNG PersonalChange / BankChange / DocumentsChange (extra="forbid" bên backend):
  //  lọt một ô liên hệ hay công việc vào đây là 422 cả lượt gửi.
  it('never lets contact or work fields into a self-service group', () => {
    const all = Object.values(CHANGE_REQUEST_GROUP_FIELDS).flat()
    for (const forbidden of ['phone', 'permanent_address', 'department_id', 'company_id', 'position', 'full_name']) {
      expect(all).not.toContain(forbidden)
    }
    expect(all).toHaveLength(22)
  })
})
