// bao-CR-780 — ô "Phòng xử lý" của ĐMH: đơn tạo thẳng chọn được phòng, đơn từ YCMH chỉ xem.
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { Department } from '@/modules/hr/types/department'

import { createEmptyPurchaseOrder } from '../utils/purchase-order-draft'
import { PurchaseOrderInfoCard } from './purchase-order-info-card'

const DEPARTMENTS = [
  { id: 5, name: 'Dego Organic', is_active: true },
  { id: 20, name: 'Sản xuất -Thu mua', is_active: true },
] as Department[]

function renderCard(overrides: Partial<ReturnType<typeof createEmptyPurchaseOrder>> = {}, onChange = vi.fn()) {
  render(
    <MemoryRouter>
      <PurchaseOrderInfoCard
        data={{ ...createEmptyPurchaseOrder(), ...overrides }}
        editable
        departments={DEPARTMENTS}
        canPickNspt={false}
        onChange={onChange}
      />
    </MemoryRouter>,
  )
  return onChange
}

describe('PurchaseOrderInfoCard — Phòng xử lý', () => {
  it('lets a direct order (no source request) pick the handling department', async () => {
    const onChange = renderCard()
    const picker = document.getElementById('po-handler-dept') as HTMLElement
    expect(picker).not.toBeNull()
    await userEvent.click(picker)
    await userEvent.click(await screen.findByText('Dego Organic'))
    expect(onChange).toHaveBeenCalledWith({ handler_dept_id: 5, handler_dept_name: 'Dego Organic' })
  })

  it('keeps the handling department read-only when the order comes from a request', () => {
    renderCard({ pr_code: 'PYC13112604', handler_dept_id: 20, handler_dept_name: 'Sản xuất -Thu mua' })
    expect(document.getElementById('po-handler-dept')).toBeNull()
    expect(screen.getByText('Sản xuất -Thu mua')).toBeInTheDocument()
  })
})
