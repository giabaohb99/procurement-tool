import { describe, expect, it } from 'vitest'

import { DEFAULT_PRINT_TERMS, padDays, resolvePrintTerms } from './purchase-order-print-terms'

describe('resolvePrintTerms', () => {
  it('falls back to the legacy hard-coded terms when the backend sends nothing', () => {
    expect(resolvePrintTerms({})).toEqual(DEFAULT_PRINT_TERMS)
    expect(resolvePrintTerms({ print_terms: null })).toEqual(DEFAULT_PRINT_TERMS)
  })

  it('keeps every value the backend already resolved', () => {
    const terms = resolvePrintTerms({
      print_terms: {
        inspection_days: 30,
        return_days: 3,
        inspection_days_label: '30',
        return_days_label: '03',
        invoice_deadline: 'Trong 3 ngày làm việc',
      },
    })
    expect(terms.inspection_days_label).toBe('30')
    expect(terms.return_days_label).toBe('03')
    expect(terms.invoice_deadline).toBe('Trong 3 ngày làm việc')
  })

  // Lỗi đã từng có ở bản in: ô ngày rỗng in ra "trong vòng  ngày" — hai dấu cách, không số.
  it('never prints an empty day count: 0, negative, NaN and blank labels fall back', () => {
    const terms = resolvePrintTerms({
      print_terms: {
        inspection_days: 0,
        return_days: -2,
        inspection_days_label: '',
        return_days_label: '   ',
        invoice_deadline: '  ',
      },
    })
    expect(terms.inspection_days).toBe(15)
    expect(terms.return_days).toBe(7)
    expect(terms.inspection_days_label).toBe('15')
    expect(terms.return_days_label).toBe('07')
    expect(terms.invoice_deadline).toBe(DEFAULT_PRINT_TERMS.invoice_deadline)
    expect(resolvePrintTerms({ print_terms: { inspection_days: Number.NaN } }).inspection_days).toBe(
      15,
    )
  })

  it('pads a missing label from the number so "7" reads "07" like the old form', () => {
    const terms = resolvePrintTerms({ print_terms: { inspection_days: 9, return_days: 7 } })
    expect(terms.inspection_days_label).toBe('09')
    expect(terms.return_days_label).toBe('07')
    expect(padDays(120)).toBe('120')
  })
})
