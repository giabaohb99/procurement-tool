import { describe, expect, it } from 'vitest'

import { resolveShiftSubmit, type ShiftSubmitInput } from './work-shift-submit-state'

const base: ShiftSubmitInput = {
  pending: false,
  templateLoading: false,
  rowsValid: true,
  cells: 1,
  bulkWarning: null,
  hasShift: false,
  dirty: true,
}

describe('resolveShiftSubmit', () => {
  it('labels the button by what it will do: one cell "Lưu", several cells "Lưu cho N ô"', () => {
    expect(resolveShiftSubmit(base)).toEqual({ label: 'Lưu', bulk: false, enabled: true, reason: null })
    expect(resolveShiftSubmit({ ...base, cells: 8 })).toMatchObject({ label: 'Lưu cho 8 ô', bulk: true, enabled: true })
  })

  it('never disables without a reason', () => {
    const cases: Partial<ShiftSubmitInput>[] = [
      { pending: true },
      { templateLoading: true },
      { rowsValid: false },
      { cells: 3, bulkWarning: 'Vượt trần' },
      { dirty: false },
    ]
    for (const over of cases) {
      const state = resolveShiftSubmit({ ...base, ...over })
      expect(state.enabled).toBe(false)
      expect(state.reason).toBeTruthy()
    }
  })

  it('an untouched template cell cannot be saved alone, but can be copied to other cells', () => {
    expect(resolveShiftSubmit({ ...base, dirty: false }).reason).toBe('Chưa thay đổi gì')
    expect(resolveShiftSubmit({ ...base, dirty: false, cells: 2 }).enabled).toBe(true)
    //  Ô đã có ca riêng: lưu lại nguyên trạng vẫn được (như bản trước).
    expect(resolveShiftSubmit({ ...base, dirty: false, hasShift: true }).enabled).toBe(true)
  })

  it('a bulk warning only blocks a bulk save, and row errors win over it', () => {
    expect(resolveShiftSubmit({ ...base, bulkWarning: 'Vượt trần' }).enabled).toBe(true)
    expect(resolveShiftSubmit({ ...base, cells: 4, bulkWarning: 'x', rowsValid: false }).reason).toBe('Còn khung giờ bị lỗi')
    expect(resolveShiftSubmit({ ...base, templateLoading: true, rowsValid: false }).reason).toBe('Đang tải lịch tuần…')
  })
})
