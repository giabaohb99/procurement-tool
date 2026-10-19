import { describe, expect, it } from 'vitest'

import { UI_EVENT_TYPE, UI_FORM } from '@/shared/constants/statuses'

import { UI_EVENT, UI_FORM_CODE, UI_FORM_NONE } from './ui-event-codes'

describe('ui event codes', () => {
  it('uses unique numbers per set so no code is reused', () => {
    expect(new Set(Object.values(UI_EVENT)).size).toBe(Object.keys(UI_EVENT).length)
    expect(new Set(Object.values(UI_FORM_CODE)).size).toBe(Object.keys(UI_FORM_CODE).length)
  })

  // Hằng gửi lên phải khớp đúng bộ mã backend đã đăng ký (cả hai cùng được sinh, test bắt sinh lệch / quên sinh lại).
  it('matches the backend registered sets exactly', () => {
    expect(UI_EVENT_TYPE.map((o) => Number(o.value)).sort()).toEqual(Object.values(UI_EVENT).sort())
    expect(UI_FORM.map((o) => Number(o.value)).sort()).toEqual(Object.values(UI_FORM_CODE).sort())
  })

  it('keeps 0 outside the form set (event not tied to a form)', () => {
    expect(Object.values(UI_FORM_CODE)).not.toContain(UI_FORM_NONE)
  })
})
