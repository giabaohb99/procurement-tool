// bao-CR-583 — biểu mẫu sửa thông tin PHƯƠNG ÁN 0 / NHẬP TAY của YCMH (màn xử lý và màn chọn).

import type { PrOptionDetailsPayload, PurchaseRequestOption } from '../types/purchase-request-options'
import { PR_OPTION_SOURCE_MANUAL } from '../types/purchase-request-options'

/** Giá trị «không chọn NCC trong danh mục» của ô chọn. */
export const NO_SUPPLIER_CODE = '__none__'

export interface OptionDetailsForm {
  productName: string
  productCode: string
  supplierCode: string
  supplierName: string
  price: string
  quoteUnit: string
  moq: string
  volumeRange: string
  vat: string
  origin: string
  deliveryTime: string
  deliveryPlace: string
  shippingCost: string
  sampleReady: boolean
  note: string
}

const numberText = (value: unknown) => {
  const number = Number(value ?? 0)
  return Number.isFinite(number) && number !== 0 ? String(number) : ''
}

/** Phương án hiện tại → ô của biểu mẫu. Số 0 hiện thành ô trống cho dễ gõ. */
export function optionToDetailsForm(option: PurchaseRequestOption): OptionDetailsForm {
  return {
    productName: option.snap_product_name ?? '',
    productCode: option.snap_internal_code ?? '',
    supplierCode: option.supplier_code || NO_SUPPLIER_CODE,
    //  NCC trong danh mục đã nằm ở ô chọn; chỉ NCC ngoài danh mục mới đổ vào ô gõ tay.
    supplierName: option.supplier_code ? '' : (option.supplier_name ?? ''),
    price: numberText(option.snap_price_by_volume),
    quoteUnit: option.snap_quote_unit ?? '',
    moq: numberText(option.snap_moq),
    volumeRange: option.snap_volume_range ?? '',
    vat: numberText(option.snap_vat),
    origin: option.snap_origin ?? '',
    deliveryTime: option.snap_delivery_time ?? '',
    deliveryPlace: option.snap_delivery_place ?? '',
    shippingCost: numberText(option.snap_shipping_cost),
    sampleReady: Boolean(option.snap_sample_ready) && String(option.snap_sample_ready) !== 'false',
    note: option.nstm_note ?? '',
  }
}

/** Ô số: trống = 0; chữ, số âm → `null` (báo lỗi). */
function parseNumber(raw: string): number | null {
  const trimmed = raw.trim()
  if (!trimmed) return 0
  const value = Number(trimmed)
  return Number.isFinite(value) && value >= 0 ? value : null
}

/**
 * Chỉ gửi ô ĐÃ ĐỔI so với phương án hiện tại — gửi cả gói thì ghi đè cả những ô người khác
 * vừa sửa trên phiếu khác, và nhật ký ghi một loạt «đổi» không có thật.
 */
export function buildOptionDetailsPayload(
  option: PurchaseRequestOption,
  form: OptionDetailsForm,
): { payload: PrOptionDetailsPayload; error?: string } {
  const payload: PrOptionDetailsPayload = {}

  const productName = form.productName.trim()
  if (!productName) return { payload, error: 'Tên hàng không được để trống' }
  if (productName !== (option.snap_product_name ?? '')) payload.snap_product_name = productName

  const productCode = form.productCode.trim()
  if (productCode !== (option.snap_internal_code ?? '')) payload.snap_internal_code = productCode

  const supplierCode = form.supplierCode === NO_SUPPLIER_CODE ? '' : form.supplierCode
  const supplierName = supplierCode ? '' : form.supplierName.trim()
  const currentName = option.supplier_code ? '' : (option.supplier_name ?? '')
  if (!supplierCode && !supplierName && option.source === PR_OPTION_SOURCE_MANUAL) {
    return { payload, error: 'Phương án nhập tay phải có nhà cung cấp' }
  }
  if (supplierCode !== (option.supplier_code ?? '') || supplierName !== currentName) {
    payload.supplier_code = supplierCode
    payload.supplier_name = supplierName
  }

  const numbers: [keyof OptionDetailsForm, keyof PrOptionDetailsPayload, string, number | undefined][] = [
    ['price', 'snap_price_by_volume', 'Đơn giá', undefined],
    ['moq', 'snap_moq', 'MOQ', undefined],
    ['vat', 'snap_vat', 'VAT', 100],
    ['shippingCost', 'snap_shipping_cost', 'Phí vận chuyển', undefined],
  ]
  for (const [formKey, payloadKey, label, below] of numbers) {
    const value = parseNumber(String(form[formKey]))
    if (value === null || (below !== undefined && value >= below)) {
      return {
        payload,
        error: below ? `${label} phải là số từ 0 tới dưới ${below}` : `${label} phải là số không âm`,
      }
    }
    if (value !== Number(option[payloadKey as keyof PurchaseRequestOption] ?? 0)) {
      ;(payload as Record<string, unknown>)[payloadKey] = value
    }
  }

  const texts: [keyof OptionDetailsForm, keyof PrOptionDetailsPayload][] = [
    ['quoteUnit', 'snap_quote_unit'],
    ['volumeRange', 'snap_volume_range'],
    ['origin', 'snap_origin'],
    ['deliveryTime', 'snap_delivery_time'],
    ['deliveryPlace', 'snap_delivery_place'],
    ['note', 'nstm_note'],
  ]
  for (const [formKey, payloadKey] of texts) {
    const value = String(form[formKey]).trim()
    if (value !== String(option[payloadKey as keyof PurchaseRequestOption] ?? '')) {
      ;(payload as Record<string, unknown>)[payloadKey] = value
    }
  }

  if (form.sampleReady !== optionToDetailsForm(option).sampleReady) {
    payload.snap_sample_ready = form.sampleReady
  }
  return { payload }
}
