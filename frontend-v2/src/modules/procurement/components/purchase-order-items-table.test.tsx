import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import type { LineReportProgress } from '../utils/survey-report-helpers'
import { PurchaseOrderItemsTable } from './purchase-order-items-table'

// Bảng này nói về CÁCH HIỆN dòng hàng, không nói về mạng — cắt lượt gọi danh mục.
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestUnits: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestItemGroups: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestProducts: () => ({ data: { items: [] }, isLoading: false }),
  useProductPurchaseHistory: () => ({
    data: { total: 0, items: [] },
    isLoading: false,
    isError: false,
    isFetching: false,
  }),
}))

function item(overrides: Partial<PurchaseOrderItem>): PurchaseOrderItem {
  return {
    id: 501,
    product_code: 'ABA36',
    product_name: 'Abamectin 3.6EC',
    invoice_name: '',
    item_group: '',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: false,
    required_date: '',
    expected_date: '',
    unit: 'Lít',
    qty_request: 0,
    qty_order: 10,
    price: 1000,
    vat: 0,
    warehouse_code: '',
    note: '',
    currency: '',
    exchange_rate: 0,
    weight_kg: 0,
    dimension: '',
    deliveries: [],
    ...overrides,
  }
}

const ITEMS = [item({ id: 501 }), item({ id: 502, product_code: 'DK', product_name: 'Dầu khoáng' })]

function renderTable(props: Partial<Parameters<typeof PurchaseOrderItemsTable>[0]> = {}) {
  return render(
    <PurchaseOrderItemsTable
      items={ITEMS}
      editable={false}
      progressEditable={false}
      onChange={vi.fn()}
      {...props}
    />,
  )
}

/** bao-CR-602 — cột «Hồ sơ»: % báo cáo thực hiện theo dòng, bấm là cuộn tới khối báo cáo. */
describe('PurchaseOrderItemsTable — cột Hồ sơ (báo cáo thực hiện theo dòng)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it('hides the column entirely when no report map is passed (create screen)', () => {
    renderTable()
    expect(screen.queryByText('Hồ sơ')).toBeNull()
  })

  it('shows the per-line percent and calls back with the report item to focus', async () => {
    const onOpenLineReport = vi.fn()
    const lineReport = new Map<number, LineReportProgress>([
      [501, { itemId: 11, done: 3, total: 4, percent: 75 }],
    ])
    renderTable({ lineReport, onOpenLineReport })

    expect(screen.getByText('Hồ sơ')).toBeInTheDocument()
    const button = screen.getByRole('button', { name: 'Hồ sơ dòng 1: 75%' })
    expect(button).toHaveTextContent('75%')
    await userEvent.click(button)
    expect(onOpenLineReport).toHaveBeenCalledWith({ itemId: 11, done: 3, total: 4, percent: 75 })

    //  Dòng chưa có hồ sơ nào (không có trong map) hiện gạch ngang, không có nút để bấm hụt.
    expect(screen.queryByRole('button', { name: /Hồ sơ dòng 2/ })).toBeNull()
  })

  it('treats a line with zero docs as "no report" rather than 0%', () => {
    const lineReport = new Map<number, LineReportProgress>([
      [501, { itemId: 11, done: 0, total: 0, percent: 0 }],
    ])
    renderTable({ lineReport })
    expect(screen.queryByRole('button', { name: /Hồ sơ dòng 1/ })).toBeNull()
  })
})
