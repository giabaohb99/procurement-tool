import { describe, expect, it } from 'vitest'

import { autoPrintText } from './print-texts'

describe('autoPrintText (CR-149)', () => {
  it('mặc định ghi "Thanh toán công nợ <NCC> <kỳ mm/yyyy>"', () => {
    expect(
      autoPrintText({ prepay: 0, supplier_name: 'Công ty A', request_date: '2026-08-20' }),
    ).toBe('Thanh toán công nợ Công ty A 08/2026')
  })

  it('phiếu cũ có cờ prepay thì vẫn ra câu "Thanh toán trước..." như CR-146', () => {
    expect(
      autoPrintText({ prepay: 1, supplier_name: 'Công ty A', request_date: '2026-08-20' }),
    ).toBe('Thanh toán trước cho nhà cung cấp Công ty A 08/2026')
  })

  it('thiếu tên NCC thì rơi về mã; thiếu ngày thì không thừa khoảng trắng đuôi', () => {
    expect(autoPrintText({ supplier_code: 'NCC01' })).toBe('Thanh toán công nợ NCC01')
  })
})
