import { describe, expect, it } from 'vitest'

import {
  buildFormDefaults,
  percentInputToRatio,
  ratioToPercentInput,
  toApiPayload,
} from './field-values'
import type { CrudFormField } from './types'

const FIELDS: CrudFormField[] = [
  { name: 'code', label: 'Mã' },
  { name: 'vat', label: 'VAT (%)', type: 'percent', defaultValue: 0.08 },
  { name: 'debt_limit', label: 'Hạn mức nợ', type: 'number' },
  { name: 'is_active', label: 'Trạng thái', type: 'switch' },
]

describe('field-values', () => {
  /**
   * Lỗi đã gặp: `0.07 * 100` trong JS ra 7.000000000000001. Đổ thẳng vào ô số là
   * người dùng thấy nguyên cái đuôi thập phân đó trên form nhà cung cấp.
   */
  it('đổi tỉ lệ sang phần trăm không để lại đuôi thập phân rác', () => {
    expect(ratioToPercentInput(0.07)).toBe(7)
    expect(ratioToPercentInput(0.08)).toBe(8)
    expect(ratioToPercentInput(0.105)).toBe(10.5)
  })

  it('ô trống hay chữ vô nghĩa thì coi như 0, không ra NaN', () => {
    expect(ratioToPercentInput('')).toBe(0)
    expect(ratioToPercentInput(null)).toBe(0)
    expect(percentInputToRatio('abc')).toBe(0)
  })

  /** Nhập 8 rồi lưu rồi mở lại phải vẫn là 8 — không được trôi dần qua mỗi vòng. */
  it('gõ phần trăm rồi lưu rồi mở lại vẫn ra đúng con số cũ', () => {
    for (const percent of [0, 5, 8, 10, 33.33]) {
      expect(ratioToPercentInput(percentInputToRatio(percent))).toBe(percent)
    }
  })

  it('giá trị mặc định khai theo dạng lưu, ra form thì thành phần trăm', () => {
    const values = buildFormDefaults(FIELDS)

    expect(values.vat).toBe(8)
    expect(values.code).toBe('')
    expect(values.debt_limit).toBe(0)
    expect(values.is_active).toBe(true)
  })

  it('mở bản ghi có sẵn thì lấy giá trị của bản ghi, không lấy mặc định', () => {
    const values = buildFormDefaults(FIELDS, { code: 'HOAPHAT', vat: 0.1, is_active: false })

    expect(values.code).toBe('HOAPHAT')
    expect(values.vat).toBe(10)
    expect(values.is_active).toBe(false)
  })

  /**
   * Backend khai `vat` là `ge=0, lt=1` (CR-058) — gửi thẳng 8 lên là 422.
   * Ô số của trình duyệt trả về CHUỖI nên phải ép kiểu trước khi chia.
   */
  it('gửi lên backend thì phần trăm quy về tỉ lệ và số ép về kiểu số', () => {
    const payload = toApiPayload(FIELDS, {
      code: 'HOAPHAT',
      vat: '8',
      debt_limit: '5000000',
      is_active: true,
    })

    expect(payload.vat).toBe(0.08)
    expect(payload.debt_limit).toBe(5000000)
    expect(payload.code).toBe('HOAPHAT')
  })

  it('xóa trắng ô phần trăm thì gửi 0 chứ không gửi chuỗi rỗng', () => {
    expect(toApiPayload(FIELDS, { vat: '' }).vat).toBe(0)
  })
})
