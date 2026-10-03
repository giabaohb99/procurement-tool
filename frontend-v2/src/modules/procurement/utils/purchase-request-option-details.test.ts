import { describe, expect, it } from 'vitest'

import type { PurchaseRequestOption } from '../types/purchase-request-options'
import { NO_SUPPLIER_CODE, buildOptionDetailsPayload, optionToDetailsForm } from './purchase-request-option-details'

// bao-CR-583 — thu mua sửa phương án 0: chỉ gửi ô ĐÃ ĐỔI, soát số trước khi gửi.

function zero(overrides: Partial<PurchaseRequestOption> = {}): PurchaseRequestOption {
  return {
    id: 9, pr_item_id: 5, source: 3, source_label: 'Yêu cầu gốc', product_survey_line_id: 0,
    public_id: 0, display_label: 'Phương án 0', is_chosen: true,
    snap_product_name: 'Nhãn decal', snap_spec: '', snap_origin: '', snap_quote_unit: 'cuộn',
    snap_moq: 0, snap_price_by_volume: 1000, snap_volume_range: '', snap_vat: 8,
    snap_delivery_time: '', snap_delivery_place: '', snap_shipping_cost: '0',
    snap_sample_ready: 'false', snap_lab_result: '', nstm_note: '', created_at: '',
    supplier_code: '', supplier_name: '', supplier_survey_id: 0, snap_internal_code: '',
    ...overrides,
  }
}

describe('optionToDetailsForm', () => {
  it('shows zeros as blank and keeps catalogue suppliers out of the free-text box', () => {
    const form = optionToDetailsForm(zero({ supplier_code: 'NCC01', supplier_name: 'Công ty A' }))
    expect(form.moq).toBe('')
    expect(form.price).toBe('1000')
    expect(form.supplierCode).toBe('NCC01')
    expect(form.supplierName).toBe('')
  })

  it('a free-text supplier lands in the text box with the picker on «none»', () => {
    const form = optionToDetailsForm(zero({ supplier_name: 'Cơ sở in B' }))
    expect(form.supplierCode).toBe(NO_SUPPLIER_CODE)
    expect(form.supplierName).toBe('Cơ sở in B')
  })

  it('reads the sample flag whether the API sends a boolean or a string', () => {
    expect(optionToDetailsForm(zero({ snap_sample_ready: 'false' })).sampleReady).toBe(false)
    expect(optionToDetailsForm(zero({ snap_sample_ready: true as unknown as string })).sampleReady).toBe(true)
  })
})

describe('buildOptionDetailsPayload', () => {
  it('sends nothing when nothing changed', () => {
    const option = zero()
    expect(buildOptionDetailsPayload(option, optionToDetailsForm(option))).toEqual({ payload: {} })
  })

  it('sends only the fields that changed, trimmed', () => {
    const option = zero()
    const form = { ...optionToDetailsForm(option), productCode: ' SP01 ', price: '1250', origin: ' Việt Nam ' }
    expect(buildOptionDetailsPayload(option, form).payload).toEqual({
      snap_internal_code: 'SP01',
      snap_price_by_volume: 1250,
      snap_origin: 'Việt Nam',
    })
  })

  it('picking a catalogue supplier sends its code with an empty free-text name', () => {
    const option = zero({ supplier_name: 'Tên gõ tay cũ' })
    const form = { ...optionToDetailsForm(option), supplierCode: 'NCC01', supplierName: 'bị bỏ qua' }
    expect(buildOptionDetailsPayload(option, form).payload).toEqual({ supplier_code: 'NCC01', supplier_name: '' })
  })

  it('clearing the supplier sends two blanks', () => {
    const option = zero({ supplier_code: 'NCC01', supplier_name: 'Công ty A' })
    const form = { ...optionToDetailsForm(option), supplierCode: NO_SUPPLIER_CODE, supplierName: '' }
    expect(buildOptionDetailsPayload(option, form).payload).toEqual({ supplier_code: '', supplier_name: '' })
  })

  it('clearing a number box means zero', () => {
    const option = zero({ snap_moq: 50 })
    const form = { ...optionToDetailsForm(option), moq: '' }
    expect(buildOptionDetailsPayload(option, form).payload).toEqual({ snap_moq: 0 })
  })

  it('rejects a blank product name, negative or non-numeric numbers and VAT of 100 or more', () => {
    const option = zero()
    const base = optionToDetailsForm(option)
    for (const form of [
      { ...base, productName: '   ' },
      { ...base, price: '-1' },
      { ...base, moq: 'abc' },
      { ...base, shippingCost: '-0.5' },
      { ...base, vat: '100' },
      { ...base, vat: '250' },
    ]) {
      expect(buildOptionDetailsPayload(option, form).error).toBeTruthy()
    }
  })

  it('toggling the sample flag is sent as a boolean', () => {
    const option = zero()
    const form = { ...optionToDetailsForm(option), sampleReady: true }
    expect(buildOptionDetailsPayload(option, form).payload).toEqual({ snap_sample_ready: true })
  })
})
