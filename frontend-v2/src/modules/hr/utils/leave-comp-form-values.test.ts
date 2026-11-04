import { describe, expect, it } from 'vitest'

import {
  emptyLeaveCompForm,
  toLeaveCompPayload,
  validateLeaveCompForm,
} from './leave-comp-form-values'

const TODAY = '2026-11-02'
const ok = { ...emptyLeaveCompForm(), work_date: '2026-11-01', reason: 'Trực kho' }

describe('validateLeaveCompForm', () => {
  it('accepts a past Sunday with a reason', () => {
    expect(validateLeaveCompForm(ok, TODAY, true)).toEqual({})
  })

  it('accepts today but rejects tomorrow (string compare of ISO dates)', () => {
    expect(validateLeaveCompForm({ ...ok, work_date: TODAY }, TODAY, true)).toEqual({})
    expect(validateLeaveCompForm({ ...ok, work_date: '2026-11-03' }, TODAY, true).work_date).toBeTruthy()
  })

  it('requires a date, and treats an empty string as missing', () => {
    expect(validateLeaveCompForm({ ...ok, work_date: '' }, TODAY, false).work_date).toBeTruthy()
  })

  it.each([0, -1, 0.25, 1.5, 2, Number.NaN])('rejects days=%s', (days) => {
    expect(validateLeaveCompForm({ ...ok, days }, TODAY, false).days).toBeTruthy()
  })

  it.each([0.5, 1])('accepts days=%s', (days) => {
    expect(validateLeaveCompForm({ ...ok, days }, TODAY, false).days).toBeUndefined()
  })

  it('demands a reason only when submitting, and treats whitespace as empty', () => {
    const blank = { ...ok, reason: '   ' }
    expect(validateLeaveCompForm(blank, TODAY, false).reason).toBeUndefined()
    expect(validateLeaveCompForm(blank, TODAY, true).reason).toBeTruthy()
  })

  it('rejects a reason over 1000 characters even for a draft', () => {
    expect(validateLeaveCompForm({ ...ok, reason: 'a'.repeat(1001) }, TODAY, false).reason).toBeTruthy()
    expect(validateLeaveCompForm({ ...ok, reason: 'a'.repeat(1000) }, TODAY, false).reason).toBeUndefined()
  })
})

describe('toLeaveCompPayload', () => {
  it('trims the reason and sends employee_id 0 for "me"', () => {
    expect(toLeaveCompPayload({ ...ok, reason: '  x  ' })).toEqual({
      employee_id: 0,
      work_date: '2026-11-01',
      days: 1,
      reason: 'x',
    })
  })
})
