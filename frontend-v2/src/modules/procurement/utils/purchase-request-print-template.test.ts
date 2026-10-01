import { describe, expect, it } from 'vitest'

import {
  DEFAULT_PRINT_TEMPLATE,
  PRINT_TEMPLATES,
  isPrintTemplateValue,
  resolvePrintTemplate,
} from './purchase-request-print-template'

// bao-CR-546 — ô chọn «Mẫu in» quy về đúng hai cờ cũ của tờ phiếu.
describe('resolvePrintTemplate', () => {
  it('maps the three fixed templates to the old signature / tax flags', () => {
    expect(resolvePrintTemplate('normal-signed')).toEqual({ taxMode: false, showSignature: true })
    expect(resolvePrintTemplate('normal-unsigned')).toEqual({ taxMode: false, showSignature: false })
    expect(resolvePrintTemplate('tax')).toEqual({ taxMode: true, showSignature: false })
  })

  it('falls back to the default template for unknown or empty values', () => {
    const fallback = resolvePrintTemplate(DEFAULT_PRINT_TEMPLATE)
    expect(resolvePrintTemplate('')).toEqual(fallback)
    expect(resolvePrintTemplate('TAX')).toEqual(fallback)
    expect(resolvePrintTemplate('__proto__')).toEqual(fallback)
  })

  it('default is the signed normal template, listed first, with exactly three choices', () => {
    expect(DEFAULT_PRINT_TEMPLATE).toBe('normal-signed')
    expect(PRINT_TEMPLATES.map((t) => t.value)).toEqual(['normal-signed', 'normal-unsigned', 'tax'])
    expect(PRINT_TEMPLATES.map((t) => t.label)).toEqual([
      'Mẫu thường – có chữ ký',
      'Mẫu thường – không chữ ký',
      'Mẫu thuế',
    ])
  })

  it('accepts only the declared values from the picker', () => {
    expect(isPrintTemplateValue('tax')).toBe(true)
    expect(isPrintTemplateValue('normal')).toBe(false)
    expect(isPrintTemplateValue('')).toBe(false)
  })
})
