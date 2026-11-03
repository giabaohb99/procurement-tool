import { describe, expect, it } from 'vitest'

import type { HrSettingField, SettingsPayloadForHr } from '../types/hr-setting'
import { parseRoleCodes, pickHrSettingFields, toHrSettingPayload, toHrSettingValues } from './hr-setting-values'

//  `tab: null` = ô không khai tab (truyền `undefined` thì tham số mặc định 'leave' nuốt mất).
const raw = (key: string, value: unknown, type = 'bool', tab: string | null = 'leave', group = 'hr') => ({
  key, value, type, tab: tab ?? undefined, group, label: key,
})
const field = (key: string, value: unknown, type: HrSettingField['type'] = 'bool', tab: HrSettingField['tab'] = 'leave') =>
  raw(key, value, type, tab) as HrSettingField

describe('pickHrSettingFields', () => {
  it('keeps only hr fields with a known type AND tab; drops other groups, unknown types/tabs and a missing payload', () => {
    const payload: SettingsPayloadForHr = {
      fields: [
        raw('leave_restrict_backdated', true),
        raw('smtp_host', 'x', 'str', null, 'email'),
        raw('hr_kieu_la', 'x', 'condition'),
        raw('hr_tab_la', 'x', 'str', 'payroll'),
        raw('hr_khong_tab', 'x', 'str', null),
        raw('employee_code_prefix', 'NSU', 'code_prefix', 'employee'),
      ],
    }
    expect(pickHrSettingFields(payload).map((f) => f.key)).toEqual(['leave_restrict_backdated', 'employee_code_prefix'])
    expect(pickHrSettingFields(undefined)).toEqual([])
  })
})

describe('parseRoleCodes', () => {
  it('trims, drops empties and duplicates — same rule the backend stores', () => {
    expect(parseRoleCodes(' hr , ,admin,hr ')).toEqual(['hr', 'admin'])
    expect(parseRoleCodes(['hr', ' hr', ''])).toEqual(['hr'])
    expect(parseRoleCodes('')).toEqual([])
    expect(parseRoleCodes(null)).toEqual([])
    expect(parseRoleCodes(undefined)).toEqual([])
  })
})

describe('toHrSettingValues / toHrSettingPayload', () => {
  it('treats anything but literal true as OFF and shows numbers / null as strings', () => {
    const fields = [
      field('leave_restrict_backdated', 'true'),
      field('org_chart_visible_to_all', 1, 'bool', 'employee'),
      field('labor_contract_warn_days', 30, 'int', 'contract'),
      field('employee_code_prefix', null, 'code_prefix', 'employee'),
    ]
    expect(toHrSettingValues(fields)).toEqual({
      leave_restrict_backdated: false,
      org_chart_visible_to_all: false,
      labor_contract_warn_days: '30',
      employee_code_prefix: '',
    })
  })

  it('builds the PUT body: roles as "a,b", text trimmed, every field present', () => {
    const fields = [
      field('leave_restrict_backdated', true),
      field('leave_backdated_roles', 'hr_profile,admin', 'roles'),
      field('employee_anniversary_years', '1,3', 'int_list', 'employee'),
      field('labor_contract_warn_days', 30, 'int', 'contract'),
    ]
    const values = { ...toHrSettingValues(fields), employee_anniversary_years: ' 2, 4 ', labor_contract_warn_days: '' }
    expect(toHrSettingPayload(fields, values)).toEqual({
      leave_restrict_backdated: true,
      leave_backdated_roles: 'hr_profile,admin',
      employee_anniversary_years: '2, 4',
      labor_contract_warn_days: '',
    })
  })
})
