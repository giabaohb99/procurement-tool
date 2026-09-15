import { describe, expect, it } from 'vitest'

import type { PurchaseRequestDetail, PurchaseRequestItem } from '../types/purchase-request-detail'
import type { PurchaseRequestOption } from '../types/purchase-request-options'
import {
  PR_OPTION_SOURCE_MANUAL,
  PR_OPTION_SOURCE_ORIGINAL,
} from '../types/purchase-request-options'
import { buildPurchaseOrderLines, toDraftFromRequest } from './purchase-order-draft'

function makeOption(overrides: Partial<PurchaseRequestOption> = {}): PurchaseRequestOption {
  return {
    id: 1,
    pr_item_id: 1,
    source: PR_OPTION_SOURCE_MANUAL,
    source_label: 'Nhập tay',
    product_survey_line_id: null,
    public_id: 1,
    display_label: 'Phương án 1',
    is_chosen: true,
    snap_product_name: 'Vải mộc',
    snap_spec: '',
    snap_origin: '',
    snap_quote_unit: '',
    snap_moq: 0,
    snap_price_by_volume: 0,
    snap_volume_range: '',
    snap_vat: 0,
    snap_delivery_time: '',
    snap_delivery_place: '',
    snap_shipping_cost: '',
    snap_sample_ready: '',
    snap_lab_result: '',
    nstm_note: '',
    created_at: '2026-09-15T00:00:00',
    supplier_code: '',
    supplier_name: '',
    supplier_survey_id: 0,
    snap_internal_code: '',
    ...overrides,
  }
}

function makeItem(overrides: Partial<PurchaseRequestItem> = {}): PurchaseRequestItem {
  return {
    id: 1,
    product_code: 'SP-A',
    product_name: 'Vải mộc',
    item_group: 'Nguyên liệu',
    group_desc: '',
    qty: 100,
    unit: 'm',
    price: 4800,
    vat_pct: 8,
    amount: 0,
    warehouse: '',
    required_date: '2026-10-01',
    assignee: 'NV001',
    expected_date: '',
    line_status: 'no_po',
    progress_note: '',
    note: '',
    qty_ordered: 0,
    qty_received: 0,
    product_id: 0,
    product_thumbnail_url: '',
    ...overrides,
  }
}

function makeRequest(items: PurchaseRequestItem[]): PurchaseRequestDetail {
  return {
    id: 9,
    code: 'PR00009',
    company_id: 1,
    company_name: 'DEGO',
    requester: 'Nguyễn Văn A',
    requester_id: 5,
    requester_position: '',
    department: 'Sản xuất',
    head_of_dept: '',
    head_of_dept_id: 0,
    purpose: '',
    request_date: '2026-09-10',
    received_date: '2026-09-11',
    need_date: '2026-10-01',
    status: 'dispatched',
    is_urgent: false,
    vat_rate: 0.08,
    assignee_id: 0,
    note: '',
    show_code_on_print: false,
    supplier_req: { name: '', tax_code: '', contact: '' },
    supplier_pur: { name: 'NCC gợi ý cũ', tax_code: '', contact: '' },
    supplier_from_survey: false,
    can_edit_supplier_pur: false,
    suggested_supplier: 'NCC đề xuất',
    suggested_supplier_tax_code: '',
    suggested_supplier_contact: '',
    quote_filename: '',
    quote_file_url: '',
    dispatch_enabled: true,
    can_dispatch: false,
    can_approve: false,
    created_at: '2026-09-10T00:00:00',
    created_by_name: '',
    requester_signature: '',
    approver_name: '',
    approver_signature: '',
    dispatcher_name: '',
    dispatcher_signature: '',
    purchasing_head_name: '',
    purchasing_head_signature: '',
    items,
    subtotal: 0,
    vat: 0,
    total: 0,
  }
}

describe('buildPurchaseOrderLines — điền sẵn theo phương án đã chọn (H.10.6)', () => {
  it('uses the chosen option price, quote unit and delivery commitment note', () => {
    const item = makeItem({
      note: 'Ghi chú dòng',
      chosen_option: makeOption({
        snap_price_by_volume: 4500,
        snap_quote_unit: 'cuộn',
        snap_delivery_time: '10 ngày',
        snap_delivery_place: 'Kho HCM',
      }),
    })
    const { remaining } = buildPurchaseOrderLines([item])
    expect(remaining).toHaveLength(1)
    expect(remaining[0].price).toBe(4500)
    expect(remaining[0].unit).toBe('cuộn')
    expect(remaining[0].note).toBe('Ghi chú dòng; Cam kết giao: 10 ngày; Nơi giao: Kho HCM')
  })

  it('falls back to the line vat when the option vat is blank (CR-058)', () => {
    const item = makeItem({
      chosen_option: makeOption({ snap_price_by_volume: 4500, snap_vat: 0 }),
    })
    const { remaining } = buildPurchaseOrderLines([item])
    expect(remaining[0].vat).toBe(8)
  })

  it('uses the option vat when it is set', () => {
    const item = makeItem({
      chosen_option: makeOption({ snap_price_by_volume: 4500, snap_vat: 10 }),
    })
    const { remaining } = buildPurchaseOrderLines([item])
    expect(remaining[0].vat).toBe(10)
  })

  it('keeps the old line values untouched when no option is chosen', () => {
    const { remaining } = buildPurchaseOrderLines([makeItem()])
    expect(remaining[0].price).toBe(4800)
    expect(remaining[0].vat).toBe(8)
    expect(remaining[0].unit).toBe('m')
    expect(remaining[0].note).toBe('')
  })

  // Phương án 0 chụp đúng giá trị dòng — nâng cấp này không được đổi kết quả
  // của phiếu chưa ai đụng phương án.
  it('option zero mirroring the line yields the same result as before', () => {
    const item = makeItem({
      chosen_option: makeOption({
        source: PR_OPTION_SOURCE_ORIGINAL,
        public_id: 0,
        snap_price_by_volume: 4800,
        snap_vat: 8,
        snap_quote_unit: 'm',
      }),
    })
    const { remaining } = buildPurchaseOrderLines([item])
    expect(remaining[0].price).toBe(4800)
    expect(remaining[0].vat).toBe(8)
    expect(remaining[0].unit).toBe('m')
  })
})

describe('toDraftFromRequest — NCC đầu đơn theo phương án thống nhất (H.10.6)', () => {
  const chosenNx = () =>
    makeOption({ supplier_code: 'NX', supplier_name: 'Nhà Xuất NX', snap_price_by_volume: 1 })

  it('fills the header supplier when every active line agrees on one supplier', () => {
    const request = makeRequest([
      makeItem({ id: 1, chosen_option: chosenNx() }),
      makeItem({ id: 2, product_code: 'SP-B', chosen_option: chosenNx() }),
    ])
    const draft = toDraftFromRequest(request, [])
    expect(draft.supplier_code).toBe('NX')
    expect(draft.supplier_name).toBe('Nhà Xuất NX')
  })

  it('leaves the header supplier empty when lines point at different suppliers', () => {
    const request = makeRequest([
      makeItem({ id: 1, chosen_option: chosenNx() }),
      makeItem({
        id: 2,
        product_code: 'SP-B',
        chosen_option: makeOption({ supplier_code: 'KH', supplier_name: 'Khác' }),
      }),
    ])
    const draft = toDraftFromRequest(request, [])
    expect(draft.supplier_code).toBe('')
    // Không thống nhất thì rơi về tên gợi ý cũ như trước nâng cấp.
    expect(draft.supplier_name).toBe('NCC gợi ý cũ')
  })

  it('leaves the header supplier empty when one line has no chosen option', () => {
    const request = makeRequest([
      makeItem({ id: 1, chosen_option: chosenNx() }),
      makeItem({ id: 2, product_code: 'SP-B' }),
    ])
    expect(toDraftFromRequest(request, []).supplier_code).toBe('')
  })

  it('ignores cancelled lines when checking supplier agreement', () => {
    const request = makeRequest([
      makeItem({ id: 1, chosen_option: chosenNx() }),
      makeItem({ id: 2, product_code: 'SP-B', line_status: 'cancelled' }),
    ])
    expect(toDraftFromRequest(request, []).supplier_code).toBe('NX')
  })

  // NCC bị backend che (thiếu supplier:read) trả chuỗi rỗng — coi như chưa có
  // NCC, đừng điền một cặp mã/tên rỗng lên đầu đơn.
  it('treats masked/blank suppliers as no agreement', () => {
    const request = makeRequest([
      makeItem({ id: 1, chosen_option: makeOption() }),
      makeItem({ id: 2, product_code: 'SP-B', chosen_option: makeOption() }),
    ])
    expect(toDraftFromRequest(request, []).supplier_code).toBe('')
  })

  it('handles a request with zero lines without inventing a supplier', () => {
    expect(toDraftFromRequest(makeRequest([]), []).supplier_code).toBe('')
  })
})
