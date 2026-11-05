import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { PurchaseOrderImportCostAllocationShareCard } from './purchase-order-import-cost-allocation-share-card'

describe('PurchaseOrderImportCostAllocationShareCard', () => {
  it('shows type, description, supplier, method, ratio and amount', () => {
    render(
      <PurchaseOrderImportCostAllocationShareCard
        typeLabel="Cước biển"
        description="Thượng Hải – Cát Lái"
        supplier="MSK — Maersk"
        method="Theo giá trị"
        ratio="40.00%"
        amount="1.000.000 đ"
      />,
    )
    expect(screen.getByText('Cước biển')).toBeInTheDocument()
    expect(screen.getByText('· Thượng Hải – Cát Lái', { exact: false })).toBeInTheDocument()
    expect(screen.getByText('MSK — Maersk ·', { exact: false })).toBeInTheDocument()
    expect(screen.getByText('Tỷ lệ 40.00%')).toBeInTheDocument()
    expect(screen.getByText('1.000.000 đ')).toBeInTheDocument()
  })

  it('omits the supplier prefix entirely when the cost has no supplier', () => {
    render(
      <PurchaseOrderImportCostAllocationShareCard
        typeLabel="Thuế GTGT"
        description=""
        supplier=""
        method="Nhập tay"
        ratio="0.00%"
        amount={<input aria-label="Số tiền nhập tay dòng ABA36" />}
      />,
    )
    expect(screen.getByText('Nhập tay').textContent).toBe('Nhập tay')
    expect(screen.getByRole('textbox', { name: 'Số tiền nhập tay dòng ABA36' })).toBeInTheDocument()
  })
})
