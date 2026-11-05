import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { ImportCostAllocationLine } from '../types/purchase-order-detail'
import { PurchaseOrderImportCostAllocationLineCard } from './purchase-order-import-cost-allocation-line-card'

const LINE: ImportCostAllocationLine = {
  item_id: 5,
  product_code: 'ABA36',
  product_name: 'Abamectin 3.6EC',
  unit: 'Lít',
  qty_order: 1_000,
  weight_kg: 0,
  goods_base: 50_000_000,
  cost_base: 2_500_000,
  landed_base: 52_500_000,
  costs: [],
}

describe('PurchaseOrderImportCostAllocationLineCard', () => {
  it('summarises the line money and the cost ratio', () => {
    render(<PurchaseOrderImportCostAllocationLineCard line={LINE} open={false} onToggle={vi.fn()} />)
    expect(screen.getByText('Abamectin 3.6EC')).toBeInTheDocument()
    expect(screen.getByText('ABA36')).toBeInTheDocument()
    expect(screen.getByText('2.500.000 đ')).toBeInTheDocument()
    expect(screen.getByText('52.500.000 đ')).toBeInTheDocument()
    expect(screen.getByText('5.0%')).toBeInTheDocument()
    // Không có khối lượng thì không in "0 kg".
    expect(screen.queryByText(/kg/)).toBeNull()
  })

  it('prints "-" instead of dividing by zero goods value', () => {
    render(
      <PurchaseOrderImportCostAllocationLineCard
        line={{ ...LINE, goods_base: 0 }}
        open={false}
        onToggle={vi.fn()}
      />,
    )
    expect(screen.getByText('-')).toBeInTheDocument()
  })

  it('toggles from the summary and renders the detail outside the toggle button', async () => {
    const onToggle = vi.fn()
    const { rerender } = render(
      <PurchaseOrderImportCostAllocationLineCard line={LINE} open={false} onToggle={onToggle}>
        <input aria-label="Số tiền nhập tay dòng ABA36" />
      </PurchaseOrderImportCostAllocationLineCard>,
    )
    expect(screen.queryByRole('textbox')).toBeNull()
    await userEvent.click(screen.getByRole('button', { expanded: false }))
    expect(onToggle).toHaveBeenCalledTimes(1)

    rerender(
      <PurchaseOrderImportCostAllocationLineCard line={LINE} open onToggle={onToggle}>
        <input aria-label="Số tiền nhập tay dòng ABA36" />
      </PurchaseOrderImportCostAllocationLineCard>,
    )
    const input = screen.getByRole('textbox', { name: 'Số tiền nhập tay dòng ABA36' })
    // Ô nhập trong nút bung thì chạm vào ô là gập mất dòng.
    expect(screen.getByRole('button', { expanded: true })).not.toContainElement(input)
  })
})
