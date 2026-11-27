import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { PurchaseOrderRepriceBar } from './purchase-order-reprice-bar'

function renderBar(props: Partial<Parameters<typeof PurchaseOrderRepriceBar>[0]> = {}) {
  const handlers = { onCancel: vi.fn(), onSave: vi.fn() }
  render(
    <PurchaseOrderRepriceBar
      summary={{ changedCount: 2, oldTotal: 16_500_000, newTotal: 15_800_000 }}
      currencySuffix="đ"
      saving={false}
      {...handlers}
      {...props}
    />,
  )
  return handlers
}

describe('PurchaseOrderRepriceBar', () => {
  it('says nothing has been edited yet instead of showing an empty total', () => {
    renderBar({ summary: { changedCount: 0, oldTotal: 0, newTotal: 0 } })
    expect(screen.getByText('Chưa sửa dòng nào')).toBeInTheDocument()
  })

  it('blocks saving when nothing has been changed', () => {
    renderBar({ summary: { changedCount: 0, oldTotal: 0, newTotal: 0 } })
    expect(screen.getByRole('button', { name: /Lưu giá mới/ })).toBeDisabled()
  })

  //  Người chủ chốt 20/11/2026: sửa giá không hỏi lý do — có dòng đổi là lưu được ngay.
  it('saves right away without asking for a reason', async () => {
    const { onSave } = renderBar()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /Lưu giá mới/ }))
    expect(onSave).toHaveBeenCalledTimes(1)
  })

  it('blocks both buttons while saving', () => {
    renderBar({ saving: true })
    expect(screen.getByRole('button', { name: /Lưu giá mới/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Thôi' })).toBeDisabled()
  })

  it('shows the changed line count and the signed total difference', () => {
    renderBar()
    expect(screen.getByRole('region', { name: 'Sửa giá sau duyệt' })).toHaveTextContent('2 dòng')
    expect(screen.getByText(/-700\.000/)).toBeInTheDocument()
  })
})
