import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { ImportCostSummaryBySupplier } from '../types/purchase-order-detail'
import { PurchaseOrderImportCostSupplierPaymentCards } from './purchase-order-import-cost-supplier-payment-cards'

function group(overrides: Partial<ImportCostSummaryBySupplier> = {}): ImportCostSummaryBySupplier {
  return {
    supplier_code: 'MSK',
    supplier_name: 'Maersk Việt Nam',
    base_amount: 20_000_000,
    paid_amount: 5_000_000,
    remaining: 15_000_000,
    count: 2,
    unpaid_payable_ids: [31, 32],
    ...overrides,
  }
}

const TOTALS = { count: 3, base: 30_000_000, paid: 15_000_000, remaining: 15_000_000 }

describe('PurchaseOrderImportCostSupplierPaymentCards', () => {
  it('lists each supplier with the three money figures and keeps the grand total', () => {
    render(
      <PurchaseOrderImportCostSupplierPaymentCards
        groups={[group()]}
        totals={TOTALS}
        onCreatePaymentRequest={vi.fn()}
      />,
    )
    expect(screen.getByText('Maersk Việt Nam')).toBeInTheDocument()
    expect(screen.getByText('MSK')).toBeInTheDocument()
    expect(screen.getByText('20.000.000 đ')).toBeInTheDocument()
    expect(screen.getByText('Tổng cộng')).toBeInTheDocument()
    expect(screen.getByText('30.000.000 đ')).toBeInTheDocument()
  })

  it('sends exactly the unpaid payable ids of that supplier', async () => {
    const onCreatePaymentRequest = vi.fn()
    render(
      <PurchaseOrderImportCostSupplierPaymentCards
        groups={[group()]}
        totals={TOTALS}
        onCreatePaymentRequest={onCreatePaymentRequest}
      />,
    )
    await userEvent.click(screen.getByRole('button', { name: 'Tạo YCTT' }))
    expect(onCreatePaymentRequest).toHaveBeenCalledWith([31, 32])
  })

  it('shows "paid in full" once nothing is left, and "not yet a payable" text instead of a dead button', () => {
    //  duoc-CR-741: bản v1 ghi chữ Chưa thành công nợ khi còn phải chi mà chưa có khoản nợ
    //  nào; v2 từng vẽ nút Tạo YCTT bị khóa ở đó — người dùng bấm hoài không hiểu vì sao.
    render(
      <PurchaseOrderImportCostSupplierPaymentCards
        groups={[
          group({ supplier_code: 'A', remaining: 0, unpaid_payable_ids: [] }),
          group({ supplier_code: 'B', remaining: 100, unpaid_payable_ids: [] }),
        ]}
        totals={TOTALS}
        onCreatePaymentRequest={vi.fn()}
      />,
    )
    expect(screen.getByText('Đã chi đủ')).toBeInTheDocument()
    expect(screen.getByText('Chưa thành công nợ')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Tạo YCTT' })).not.toBeInTheDocument()
  })

  it('still offers the button when a payable id exists even if the remaining rounds to zero', () => {
    render(
      <PurchaseOrderImportCostSupplierPaymentCards
        groups={[group({ remaining: 0, unpaid_payable_ids: [7] })]}
        totals={TOTALS}
        onCreatePaymentRequest={vi.fn()}
      />,
    )
    expect(screen.getByRole('button', { name: 'Tạo YCTT' })).toBeEnabled()
  })

  it('labels costs without a supplier instead of printing an empty name', () => {
    render(
      <PurchaseOrderImportCostSupplierPaymentCards
        groups={[group({ supplier_code: '', supplier_name: '' })]}
        totals={TOTALS}
        onCreatePaymentRequest={vi.fn()}
      />,
    )
    expect(screen.getByText(/chưa chọn NCC/)).toBeInTheDocument()
  })
})
