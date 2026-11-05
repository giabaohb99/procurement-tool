import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { createEmptyImportCost } from '../utils/purchase-order-draft'
import type { PurchaseOrderImportCost } from '../types/purchase-order-detail'
import { PurchaseOrderImportCostLineCard } from './purchase-order-import-cost-line-card'

function cost(overrides: Partial<PurchaseOrderImportCost> = {}): PurchaseOrderImportCost {
  return {
    ...createEmptyImportCost(),
    id: 9,
    cost_type_label: 'Cước biển',
    description: 'Cước biển Thượng Hải – Cát Lái',
    supplier_code: 'MSK',
    supplier_name: 'Maersk Việt Nam',
    invoice_no: 'HD-778',
    invoice_date: '2026-10-01',
    payment_due_date: '2026-10-31',
    ...overrides,
  }
}

const STAGES = [
  { label: 'Dự toán', amount: 12_000_000, labelClassName: 'text-blue-700' },
  { label: 'Tạm tính', amount: null, labelClassName: 'text-amber-700' },
  { label: 'Quyết toán', amount: 0, labelClassName: 'text-red-700' },
]

function renderCard(props: Partial<Parameters<typeof PurchaseOrderImportCostLineCard>[0]> = {}) {
  return render(
    <PurchaseOrderImportCostLineCard
      cost={cost()}
      index={0}
      stages={STAGES}
      baseAmount={1_234_567_890}
      paid={null}
      remaining={<span>1.234.567.890 đ</span>}
      finalized={false}
      actions={<button type="button">Xóa dòng chi phí 1</button>}
      onOpenDetail={vi.fn()}
      {...props}
    />,
  )
}

describe('PurchaseOrderImportCostLineCard', () => {
  it('leads with the description, then the cost type and the supplier code', () => {
    renderCard()
    expect(screen.getByText('Cước biển Thượng Hải – Cát Lái')).toBeInTheDocument()
    expect(screen.getByText('Cước biển')).toBeInTheDocument()
    expect(screen.getByText('MSK')).toBeInTheDocument()
    expect(screen.getByText('HĐ HD-778 · 01/10/2026 · hạn 31/10/2026')).toBeInTheDocument()
  })

  it('uses the cost type as the title when there is no description, and says the supplier is missing', () => {
    renderCard({ cost: cost({ description: '', supplier_code: '', supplier_name: '' }) })
    expect(screen.getByText('Cước biển')).toBeInTheDocument()
    expect(screen.getByText('chưa chọn NCC')).toBeInTheDocument()
  })

  it('tells "not entered" apart from "0 đ" and never shortens the money', () => {
    renderCard()
    expect(screen.getByText('12.000.000 đ')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()
    expect(screen.getByText('0 đ')).toBeInTheDocument()
    // Quy đổi hàng tỷ vẫn in đủ chữ số, không rút thành "1,2 tỷ".
    expect(screen.getAllByText('1.234.567.890 đ')).toHaveLength(2)
  })

  it('shows "paid" only for a cost that already became a payable', () => {
    const { unmount } = renderCard()
    expect(screen.queryByText(/Đã chi/)).toBeNull()
    unmount()
    renderCard({ paid: <span>500.000 đ</span> })
    expect(screen.getByText('500.000 đ')).toBeInTheDocument()
  })

  it('flags a finalized cost', () => {
    renderCard({ finalized: true })
    expect(screen.getByText('Đã quyết toán')).toBeInTheDocument()
  })

  it('opens the detail popup from the tap area; tick and actions stay outside it', async () => {
    const onOpenDetail = vi.fn()
    renderCard({ onOpenDetail, tick: <input type="checkbox" aria-label="Chọn khoản 1" /> })
    const tap = screen.getByRole('button', { name: /Chi tiết khoản chi phí 1/ })
    expect(within(tap).queryByRole('checkbox')).toBeNull()
    expect(within(tap).queryByRole('button')).toBeNull()
    await userEvent.click(tap)
    expect(onOpenDetail).toHaveBeenCalledTimes(1)
  })
})
