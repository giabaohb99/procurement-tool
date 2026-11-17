import { describe, expect, it } from 'vitest'

import {
  DEFAULT_PRINT_TEMPLATE,
  PRINT_LAYOUTS,
  PRINT_TEMPLATES,
  PURCHASING_PRINT_TEMPLATES,
  decodePrintChoice,
  encodePrintChoice,
  isPrintTemplateValue,
  isPurchasingPrintTemplate,
  defaultPrintTemplate,
  listPrintTemplates,
  readPrintTemplateParam,
  resolveAvailablePrintTemplate,
  resolvePrintTemplate,
} from './purchase-request-print-template'

// bao-CR-546 — ô chọn "Mẫu in" quy về đúng hai cờ cũ của tờ phiếu.
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

  //  duoc-CR-777: ba mẫu chung vẫn đúng ba — hai mẫu thu mua nằm ở danh sách riêng, vì
  //  `PRINT_TEMPLATES` còn nuôi nhóm "Tách theo NCC" và trang in theo NCC.
  it('default is the signed normal template, listed first, with exactly three common choices', () => {
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

// bao-CR-574 — ô "Mẫu in" gom luôn việc tách theo nhà cung cấp: một lựa chọn = (kiểu bản in, mẫu).
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

// duoc-CR-777 — hai mẫu thu mua chỉ có ở bản in YCMH mở từ đơn.
describe('purchasing templates (duoc-CR-777)', () => {
  it('declares exactly the two purchasing templates with the agreed labels', () => {
    expect(PURCHASING_PRINT_TEMPLATES.map((t) => t.value)).toEqual([
      'purchasing-signed',
      'purchasing-unsigned',
    ])
    expect(PURCHASING_PRINT_TEMPLATES.map((t) => t.label)).toEqual([
      'Mẫu thu mua – có chữ ký',
      'Mẫu thu mua – không chữ ký',
    ])
  })

  //  anh Được chốt 17/11/2026: Mẫu thu mua lên ĐẦU danh sách và được chọn sẵn khi dùng được.
  it('lists three templates outside purchasing mode and five inside, purchasing ones first', () => {
    expect(listPrintTemplates(false).map((t) => t.value)).toEqual(['normal-signed', 'normal-unsigned', 'tax'])
    expect(listPrintTemplates(true).map((t) => t.value)).toEqual([
      'purchasing-signed',
      'purchasing-unsigned',
      'normal-signed',
      'normal-unsigned',
      'tax',
    ])
  })

  it('preselects the signed purchasing template only when purchasing data is available', () => {
    expect(defaultPrintTemplate(true)).toBe('purchasing-signed')
    expect(defaultPrintTemplate(false)).toBe('normal-signed')
  })

  it('signed shows signatures, unsigned blanks them like the normal unsigned template', () => {
    expect(resolvePrintTemplate('purchasing-signed')).toEqual({ taxMode: false, showSignature: true })
    expect(resolvePrintTemplate('purchasing-unsigned')).toEqual(resolvePrintTemplate('normal-unsigned'))
  })

  it('recognises only the two purchasing values', () => {
    expect(isPurchasingPrintTemplate('purchasing-signed')).toBe(true)
    expect(isPurchasingPrintTemplate('purchasing-unsigned')).toBe(true)
    for (const raw of ['', 'purchasing', 'normal-signed', 'tax', 'PURCHASING-SIGNED', 'purchasing-signed ']) {
      expect(isPurchasingPrintTemplate(raw)).toBe(false)
    }
  })

  it('the picker round-trips purchasing choices on the common layout', () => {
    expect(decodePrintChoice('common:purchasing-unsigned')).toEqual({
      layout: 'common',
      template: 'purchasing-unsigned',
    })
  })

  it('falls back to the default when purchasing data is unavailable, keeps other templates', () => {
    expect(resolveAvailablePrintTemplate('purchasing-signed', false)).toBe(DEFAULT_PRINT_TEMPLATE)
    expect(resolveAvailablePrintTemplate('purchasing-unsigned', false)).toBe(DEFAULT_PRINT_TEMPLATE)
    expect(resolveAvailablePrintTemplate('purchasing-unsigned', true)).toBe('purchasing-unsigned')
    expect(resolveAvailablePrintTemplate('tax', false)).toBe('tax')
    expect(resolveAvailablePrintTemplate('normal-unsigned', true)).toBe('normal-unsigned')
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
      expect(readPrintTemplateParam(raw, { allowPurchasing: true })).toBe(DEFAULT_PRINT_TEMPLATE)
    }
  })

  //  duoc-CR-777: `?mau=purchasing-signed` gõ tay vào trang in YCMH thường / trang in theo NCC
  //  không được lọt mẫu thu mua sang đó.
  it('accepts purchasing templates only when the page allows them', () => {
    expect(readPrintTemplateParam('purchasing-signed')).toBe(DEFAULT_PRINT_TEMPLATE)
    expect(readPrintTemplateParam('purchasing-unsigned', { allowPurchasing: false })).toBe(
      DEFAULT_PRINT_TEMPLATE,
    )
    expect(readPrintTemplateParam('purchasing-signed', { allowPurchasing: true })).toBe('purchasing-signed')
    expect(readPrintTemplateParam('purchasing-unsigned', { allowPurchasing: true })).toBe(
      'purchasing-unsigned',
    )
    expect(readPrintTemplateParam('tax', { allowPurchasing: true })).toBe('tax')
  })
})
