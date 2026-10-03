import { describe, expect, it } from 'vitest'

import {
  DEFAULT_PRINT_TEMPLATE,
  PRINT_LAYOUTS,
  PRINT_TEMPLATES,
  decodePrintChoice,
  encodePrintChoice,
  isPrintTemplateValue,
  readPrintTemplateParam,
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

// bao-CR-574 — ô «Mẫu in» gom luôn việc tách theo nhà cung cấp: một lựa chọn = (kiểu bản in, mẫu).
describe('print choice encoding', () => {
  it('round-trips every layout x template pair', () => {
    for (const layout of PRINT_LAYOUTS) {
      for (const template of PRINT_TEMPLATES) {
        expect(decodePrintChoice(encodePrintChoice(layout.value, template.value))).toEqual({
          layout: layout.value,
          template: template.value,
        })
      }
    }
  })

  it('rejects anything that is not exactly layout:template', () => {
    for (const raw of ['', 'common', 'tax', 'common:', ':tax', 'other:tax', 'common:other',
      'supplier:tax:x', 'COMMON:tax', 'common:TAX', ' common:tax']) {
      expect(decodePrintChoice(raw)).toBeNull()
    }
  })

  it('every choice value is unique so the picker never confuses two rows', () => {
    const values = PRINT_LAYOUTS.flatMap((layout) =>
      PRINT_TEMPLATES.map((template) => encodePrintChoice(layout.value, template.value)),
    )
    expect(new Set(values).size).toBe(values.length)
  })
})

describe('readPrintTemplateParam', () => {
  it('keeps a valid template carried over from the other print page', () => {
    expect(readPrintTemplateParam('tax')).toBe('tax')
    expect(readPrintTemplateParam('normal-unsigned')).toBe('normal-unsigned')
  })

  it('falls back to the default for missing or tampered values', () => {
    for (const raw of [null, '', 'thue', 'tax ', 'supplier:tax', '<script>']) {
      expect(readPrintTemplateParam(raw)).toBe(DEFAULT_PRINT_TEMPLATE)
    }
  })
})
