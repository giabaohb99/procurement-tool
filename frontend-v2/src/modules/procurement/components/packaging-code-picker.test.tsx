import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

const toastError = vi.fn()
vi.mock('sonner', () => ({ toast: { error: (m: string) => toastError(m), success: vi.fn() } }))

import type { PackagingCodeOption } from '../types/packaging-cost-types'
import { PackagingCodePicker } from './packaging-code-picker'

const option = (code: string, group: string): PackagingCodeOption => ({
  code,
  name: `Tên ${code}`,
  group,
  usage: 2,
  new: 1000,
})

const OPTIONS = [
  option('CPT0105', 'Chai'),
  option('CPT0075', 'Chai'),
  option('NAP0085', 'Nắp'),
  option('NHG0100', 'Nhãn'),
]

async function openPicker(value: string[] = [], maxCodes?: number) {
  const user = userEvent.setup()
  const onChange = vi.fn()
  render(
    <PackagingCodePicker options={OPTIONS} value={value} onChange={onChange} maxCodes={maxCodes} />,
  )
  await user.click(screen.getByRole('button', { name: /Chọn mã chai/ }))
  return { user, onChange }
}

describe('PackagingCodePicker', () => {
  it('"Chọn tất cả" after typing a group name picks only that group and keeps earlier picks', async () => {
    const { user, onChange } = await openPicker(['NHG0100'])
    await user.type(screen.getByLabelText('Tìm mã bao bì'), 'chai')
    await user.click(screen.getByRole('button', { name: 'Chọn tất cả (2)' }))
    expect(onChange).toHaveBeenCalledWith(['NHG0100', 'CPT0105', 'CPT0075'])
  })

  it('blocks the whole action when it would exceed the cap, instead of silently trimming', async () => {
    const { user, onChange } = await openPicker(['NHG0100'], 2)
    await user.click(screen.getByRole('button', { name: 'Chọn tất cả (4)' }))
    expect(onChange).not.toHaveBeenCalled()
    expect(toastError).toHaveBeenCalledWith(expect.stringContaining('tối đa 2 mã'))
  })

  it('blocks a single extra pick at the cap too', async () => {
    const { user, onChange } = await openPicker(['CPT0105', 'CPT0075'], 2)
    await user.click(screen.getByRole('option', { name: /NAP0085/ }))
    expect(onChange).not.toHaveBeenCalled()
  })

  it('"Bỏ chọn" only clears codes in the current filter', async () => {
    const { user, onChange } = await openPicker(['CPT0105', 'NAP0085'])
    await user.type(screen.getByLabelText('Tìm mã bao bì'), 'nắp')
    await user.click(screen.getByRole('button', { name: 'Bỏ chọn (1)' }))
    expect(onChange).toHaveBeenCalledWith(['CPT0105'])
  })

  it('shows selected codes as chips inside the box, at most 12, folding the rest into "+n mã"', () => {
    const many = Array.from({ length: 15 }, (_, i) => `CODE${i}`)
    render(<PackagingCodePicker options={OPTIONS} value={many} onChange={vi.fn()} />)
    expect(screen.getAllByRole('button', { name: /^Bỏ CODE/ })).toHaveLength(12)
    expect(screen.getByText('+3 mã')).toBeInTheDocument()
  })

  it('removes one code from its chip and all codes from the clear button, without opening the list', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<PackagingCodePicker options={OPTIONS} value={['CPT0105', 'NAP0085']} onChange={onChange} />)
    await user.click(screen.getByRole('button', { name: 'Bỏ CPT0105' }))
    expect(onChange).toHaveBeenLastCalledWith(['NAP0085'])
    await user.click(screen.getByRole('button', { name: 'Bỏ hết mã đã chọn' }))
    expect(onChange).toHaveBeenLastCalledWith([])
    // the chip buttons sit outside the trigger, so removing never opens the search list
    expect(screen.queryByLabelText('Tìm mã bao bì')).not.toBeInTheDocument()
  })
})

describe('PackagingCodePicker kind="product"', () => {
  const PRODUCTS: PackagingCodeOption[] = [
    { code: 'HH0713', name: 'Nước tương chai 500ml', group: '', usage: 0, new: null },
    { code: 'HH0714', name: 'Chai nhựa rỗng', group: '', usage: 0, new: null },
  ]

  async function openProducts() {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<PackagingCodePicker kind="product" options={PRODUCTS} value={[]} onChange={onChange} />)
    await user.click(screen.getByRole('button', { name: 'Chọn mã sản phẩm' }))
    return { user, onChange }
  }

  it('treats a typed word as plain text (a product named "Chai ..." is not mistaken for the Chai group)', async () => {
    const { user } = await openProducts()
    await user.type(screen.getByLabelText('Tìm mã sản phẩm'), 'chai')
    expect(screen.getAllByRole('option')).toHaveLength(2)
    await user.clear(screen.getByLabelText('Tìm mã sản phẩm'))
    await user.type(screen.getByLabelText('Tìm mã sản phẩm'), 'tương')
    expect(screen.getAllByRole('option')).toHaveLength(1)
  })

  it('does not show the "SP / price" meta of a material code, and picks by code', async () => {
    const { user, onChange } = await openProducts()
    expect(screen.queryByText(/SP/)).not.toBeInTheDocument()
    await user.click(screen.getByRole('option', { name: /HH0713/ }))
    expect(onChange).toHaveBeenCalledWith(['HH0713'])
  })

  it('shows a custom empty placeholder so the screen can say "empty = all"', () => {
    render(
      <PackagingCodePicker options={OPTIONS} value={[]} onChange={vi.fn()} emptyPlaceholder="Tất cả mã VTBB" />,
    )
    expect(screen.getByText('Tất cả mã VTBB')).toBeInTheDocument()
  })
})

