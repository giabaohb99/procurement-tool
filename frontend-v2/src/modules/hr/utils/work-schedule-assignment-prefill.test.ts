import { describe, expect, it } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'
import { buildFormDefaults, resolveFormFields } from '@/shared/crud'
import { WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG as config } from '../config/work-schedule-assignment-crud'
import { WORK_SCHEDULE_LEVEL_CODE } from '../types/work-schedule'
import {
  PREFILL_PARAMS,
  buildAssignmentCreateUrl,
  buildAssignmentListUrl,
  parseAssignmentPrefill,
  withAssignmentPrefill,
} from './work-schedule-assignment-prefill'

const DEPT = WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT

function parse(query: string) {
  return parseAssignmentPrefill(new URLSearchParams(query))
}

/** Tách phần query của một đường dẫn tương đối. */
function queryOf(url: string): URLSearchParams {
  return new URLSearchParams(url.split('?')[1] ?? '')
}

describe('parseAssignmentPrefill', () => {
  it('reads level + target id + name from the URL', () => {
    expect(parse('target_level=3&prefill_target_id=12&prefill_target_name=K%E1%BA%BF%20to%C3%A1n')).toEqual({
      level: DEPT,
      targetId: 12,
      targetName: 'Kế toán',
    })
  })

  it('a plain level filter (no prefill id) is NOT a request to open the dialog', () => {
    expect(parse('target_level=3')).toBeNull()
    expect(parse('')).toBeNull()
  })

  it('rejects ids that are not plain positive integers', () => {
    for (const bad of ['0', '-3', '1.5', '1e3', '0x1f', ' 7', '7 ', 'abc', '', '99999999999999999999']) {
      expect(parse(`target_level=3&prefill_target_id=${encodeURIComponent(bad)}`), bad).toBeNull()
    }
  })

  it('rejects the SYSTEM level (it has no target) and unknown levels', () => {
    for (const level of [String(WORK_SCHEDULE_LEVEL_CODE.SYSTEM), '0', '5', '99', 'x', '']) {
      expect(parse(`target_level=${level}&prefill_target_id=12`), level).toBeNull()
    }
  })

  it('accepts company and employee levels too', () => {
    expect(parse('target_level=2&prefill_target_id=4')?.level).toBe(WORK_SCHEDULE_LEVEL_CODE.COMPANY)
    expect(parse('target_level=4&prefill_target_id=4')?.level).toBe(WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE)
  })

  it('trims the display name and caps an absurdly long one', () => {
    expect(parse('target_level=3&prefill_target_id=1&prefill_target_name=%20%20')?.targetName).toBe('')
    const long = 'a'.repeat(5000)
    expect(parse(`target_level=3&prefill_target_id=1&prefill_target_name=${long}`)?.targetName).toHaveLength(200)
  })
})

describe('buildAssignmentCreateUrl / buildAssignmentListUrl', () => {
  it('round-trips through the parser, including names with & and #', () => {
    const prefill = { level: DEPT, targetId: 42, targetName: 'R&D #2 — Hà Nội' }
    const url = buildAssignmentCreateUrl(prefill)
    expect(url.startsWith(`${appRoutes.hr.workScheduleAssignments}?`)).toBe(true)
    expect(parseAssignmentPrefill(queryOf(url))).toEqual(prefill)
  })

  it('omits the name param when there is no name', () => {
    const url = buildAssignmentCreateUrl({ level: DEPT, targetId: 5, targetName: '' })
    expect(queryOf(url).has('prefill_target_name')).toBe(false)
  })

  it('the list link filters by level only and never opens the dialog', () => {
    const url = buildAssignmentListUrl(DEPT)
    expect(queryOf(url).get('target_level')).toBe(String(DEPT))
    expect(parseAssignmentPrefill(queryOf(url))).toBeNull()
  })

  it('closing strips the prefill params but keeps the level filter', () => {
    const qs = queryOf(buildAssignmentCreateUrl({ level: DEPT, targetId: 5, targetName: 'X' }))
    for (const key of PREFILL_PARAMS) qs.delete(key)
    expect(qs.toString()).toBe(`target_level=${DEPT}`)
  })
})

describe('withAssignmentPrefill', () => {
  it('only the three target fields change their defaults; every other field stays as declared', () => {
    const prefilled = withAssignmentPrefill(config, { level: DEPT, targetId: 12, targetName: 'Kế toán' })
    const defaults = buildFormDefaults(resolveFormFields(prefilled.formFields, {}), undefined)
    const original = buildFormDefaults(resolveFormFields(config.formFields, {}), undefined)

    expect(defaults).toEqual({ ...original, target_level: DEPT, target_id: 12, target_name: 'Kế toán' })
  })

  it('does not mutate the shared config (the plain Thêm button must still open empty)', () => {
    const before = buildFormDefaults(resolveFormFields(config.formFields, {}), undefined)
    withAssignmentPrefill(config, { level: DEPT, targetId: 12, targetName: 'Kế toán' })
    expect(buildFormDefaults(resolveFormFields(config.formFields, {}), undefined)).toEqual(before)
    expect(before.target_level).toBe(0)
    expect(before.target_id).toBe(0)
  })

  it('also works when formFields is declared as a function', () => {
    const fnConfig = { ...config, formFields: () => resolveFormFields(config.formFields, {}) }
    const prefilled = withAssignmentPrefill(fnConfig, { level: DEPT, targetId: 3, targetName: '' })
    const defaults = buildFormDefaults(resolveFormFields(prefilled.formFields, {}), undefined)
    expect(defaults.target_level).toBe(DEPT)
    expect(defaults.target_id).toBe(3)
  })

  it('keeps the field validation/render untouched (same render function)', () => {
    const prefilled = withAssignmentPrefill(config, { level: DEPT, targetId: 12, targetName: '' })
    const pick = (fields: ReturnType<typeof resolveFormFields>) => fields.find((f) => f.name === 'target_id')
    expect(pick(resolveFormFields(prefilled.formFields, {}))?.render).toBe(
      pick(resolveFormFields(config.formFields, {}))?.render,
    )
  })
})
