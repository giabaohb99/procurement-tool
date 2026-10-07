import { describe, expect, it } from 'vitest'

import { LABOR_CONTRACT_STATUS, LABOR_CONTRACT_TYPE } from '@/shared/constants/statuses'
import {
  CONTRACT_STATUS,
  contractStatusLabel,
  endDateRule,
  transitionSpecOf,
  validateSignedFile,
  validateTransitionInput,
} from './labor-contract-rules'

const file = (name: string, size = 10) => new File([new Uint8Array(size)], name)

describe('endDateRule', () => {
  // Hằng số FE phải khớp bộ mã backend: thêm/đổi loại mà quên sửa ở đây thì test này đỏ.
  it('mỗi loại hợp đồng sinh từ backend đều có luật ngày xác định', () => {
    const rules = Object.fromEntries(
      LABOR_CONTRACT_TYPE.map((o) => [o.value, endDateRule(Number(o.value))]),
    )
    expect(rules).toEqual({ '1': 'required', '2': 'required', '3': 'forbidden', '4': 'required', '5': 'required', '9': 'optional' })
  })
  it.each([0, -1, 99, Number.NaN])('mã lạ %p -> tùy chọn, không ném lỗi', (t) => {
    expect(endDateRule(t)).toBe('optional')
  })
})

describe('trạng thái', () => {
  it('năm mã CONTRACT_STATUS đều có nhãn trong bộ mã sinh từ backend', () => {
    for (const code of Object.values(CONTRACT_STATUS)) {
      expect(LABOR_CONTRACT_STATUS.some((o) => o.value === String(code))).toBe(true)
    }
  })
  it('EXPIRED hiện «Hết hạn»; mã lạ hiện gạch ngang', () => {
    expect(contractStatusLabel(CONTRACT_STATUS.EXPIRED)).toBe('Hết hạn')
    expect(contractStatusLabel(77)).toBe('—')
  })
})

describe('transitionSpecOf', () => {
  it('Ký chỉ cần ngày, không đòi lý do hay tệp', () => {
    const spec = transitionSpecOf(CONTRACT_STATUS.SIGNED)
    expect(spec).toMatchObject({ needsReason: false })
    expect(spec?.dateLabel).toBeTruthy()
  })
  it('Hủy chỉ cần lý do; Chấm dứt cần cả ngày lẫn lý do', () => {
    expect(transitionSpecOf(CONTRACT_STATUS.CANCELLED)).toMatchObject({ dateLabel: null, needsReason: true })
    expect(transitionSpecOf(CONTRACT_STATUS.TERMINATED)).toMatchObject({ needsReason: true })
    expect(transitionSpecOf(CONTRACT_STATUS.TERMINATED)?.dateLabel).toBeTruthy()
  })
  it('mã đích lạ -> undefined (bỏ qua nút)', () => {
    expect(transitionSpecOf(999)).toBeUndefined()
  })
})

describe('validateTransitionInput', () => {
  const sign = transitionSpecOf(CONTRACT_STATUS.SIGNED)!
  const terminate = transitionSpecOf(CONTRACT_STATUS.TERMINATED)!
  const cancel = transitionSpecOf(CONTRACT_STATUS.CANCELLED)!

  it('Ký thiếu ngày -> lỗi; đủ ngày -> ổn', () => {
    expect(validateTransitionInput(sign, { date: '', reason: '' }, '2026-01-01')).toMatch(/ngày ký/i)
    expect(validateTransitionInput(sign, { date: '2026-01-05', reason: '' }, '2026-01-01')).toBeNull()
  })
  it('Hủy: lý do chỉ toàn khoảng trắng bị coi là rỗng', () => {
    expect(validateTransitionInput(cancel, { date: '', reason: '   ' }, '2026-01-01')).toMatch(/lý do/i)
  })
  it('Chấm dứt: ngày trước ngày bắt đầu bị chặn, bằng ngày bắt đầu thì qua', () => {
    expect(validateTransitionInput(terminate, { date: '2025-12-31', reason: 'x' }, '2026-01-01')).toMatch(/trước ngày bắt đầu/)
    expect(validateTransitionInput(terminate, { date: '2026-01-01', reason: 'x' }, '2026-01-01')).toBeNull()
  })
  it('lý do quá 500 ký tự bị chặn trước khi gửi (backend 422)', () => {
    expect(validateTransitionInput(cancel, { date: '', reason: 'a'.repeat(501) }, '2026-01-01')).toMatch(/500/)
    expect(validateTransitionInput(cancel, { date: '', reason: 'a'.repeat(500) }, '2026-01-01')).toBeNull()
  })
})

describe('validateSignedFile', () => {
  it.each(['scan.pdf', 'scan.JPG', 'scan.jpeg', 'scan.png'])('nhận %s', (name) => {
    expect(validateSignedFile(file(name))).toBeNull()
  })
  // Đuôi kép / giả đuôi: chỉ đuôi CUỐI cùng được tính.
  it.each(['scan.pdf.exe', 'scan.svg', 'scan', 'scan.docx', '.pdf.'])('từ chối %s', (name) => {
    expect(validateSignedFile(file(name))).not.toBeNull()
  })
  it('từ chối tệp rỗng và tệp > 50MB', () => {
    expect(validateSignedFile(file('a.pdf', 0))).toBe('Tệp rỗng')
    const big = file('a.pdf', 1)
    Object.defineProperty(big, 'size', { value: 50 * 1024 * 1024 + 1 })
    expect(validateSignedFile(big)).toMatch(/50 MB/)
  })
})
