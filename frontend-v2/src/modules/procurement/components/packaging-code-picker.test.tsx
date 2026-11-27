import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { FormEvent } from 'react'
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

const boxInput = () => screen.getByRole('combobox', { name: /Chọn mã chai/ })

async function openPicker(value: string[] = [], maxCodes?: number) {
  const user = userEvent.setup()
  const onChange = vi.fn()
  render(
    <PackagingCodePicker options={OPTIONS} value={value} onChange={onChange} maxCodes={maxCodes} />,
  )
  await user.click(boxInput())
  return { user, onChange }
}

describe('PackagingCodePicker', () => {
  it('"Chọn tất cả" after typing a group name picks only that group and keeps earlier picks', async () => {
    const { user, onChange } = await openPicker(['NHG0100'])
    await user.type(boxInput(), 'chai')
    await user.click(screen.getByRole('button', { name: 'Chọn tất cả (2)' }))
    expect(onChange).toHaveBeenCalledWith(['NHG0100', 'CPT0105', 'CPT0075'])
  })

  //  bao-CR-800 — ô chọn mã của Bảng giá nguyên liệu: nói "nguyên liệu", không ghi "n SP" (nguyên liệu không nằm trong định
  //  mức), và tên vai trò bao bì ("chai") KHÔNG được hiểu là nhóm — phải rơi về tìm chữ trong mã / tên / NCC.
  it('raw-material kind: own wording, no "SP" count, and "chai" is a text search, not the Chai group', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const rawOptions: PackagingCodeOption[] = [
      { code: 'NL0001', name: 'Dung môi rửa chai', group: 'Dung môi', usage: 0, new: 31000, suppliers: 'Hóa chất A' },
      { code: 'NL0002', name: 'Hoạt chất B', group: 'Hoạt chất', usage: 0, new: null },
    ]
    render(<PackagingCodePicker kind="rawMaterial" options={rawOptions} value={[]} onChange={onChange} />)
    const input = screen.getByRole('combobox', { name: 'Chọn mã nguyên liệu' })
    await user.click(input)
    expect(screen.getByText('2 mã nguyên liệu khớp')).toBeInTheDocument()
    const first = screen.getByRole('option', { name: /NL0001/ })
    expect(first).toHaveTextContent('Dung môi')
    expect(first).toHaveTextContent('31.000')
    expect(first).not.toHaveTextContent(/\d SP/)
    expect(screen.getByRole('option', { name: /NL0002/ })).not.toHaveTextContent(/SP|·/)

    await user.type(input, 'chai')
    expect(screen.getAllByRole('option')).toHaveLength(1)
    await user.click(screen.getByRole('button', { name: 'Chọn tất cả (1)' }))
    expect(onChange).toHaveBeenCalledWith(['NL0001'])
    //  Gõ tên nhóm có trong dữ liệu vẫn lọc theo nhóm; gõ tên NCC ra mã từng mua của NCC đó.
    await user.clear(input)
    await user.type(input, 'hoạt chất')
    expect(screen.getByRole('option', { name: /NL0002/ })).toBeInTheDocument()
    expect(screen.getAllByRole('option')).toHaveLength(1)
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
    await user.type(boxInput(), 'nắp')
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
    // chip buttons are not the input, so removing never opens the list
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('has no second search box: the list opens from the box input itself and typing filters it', async () => {
    const { user } = await openPicker()
    expect(screen.getByRole('listbox')).toBeInTheDocument()
    expect(boxInput()).toHaveAttribute('aria-expanded', 'true')
    expect(screen.queryByPlaceholderText(/^Vd:/)).not.toBeInTheDocument()
    expect(screen.getAllByRole('option')).toHaveLength(4)
    await user.type(boxInput(), 'nắp')
    expect(screen.getAllByRole('option')).toHaveLength(1)
    expect(boxInput()).toHaveFocus()
  })

  it('shows the long placeholder when empty and the short "Thêm mã…" hint once chips exist', () => {
    const { unmount } = render(<PackagingCodePicker options={OPTIONS} value={[]} onChange={vi.fn()} />)
    expect(boxInput()).toHaveAttribute('placeholder', expect.stringContaining('Chọn mã chai'))
    unmount()
    render(<PackagingCodePicker options={OPTIONS} value={['CPT0105']} onChange={vi.fn()} />)
    expect(boxInput()).toHaveAttribute('placeholder', expect.stringContaining('Thêm mã…'))
  })

  it('ArrowDown + Enter toggles the highlighted row, clears the typed text and never submits a wrapping form', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const onSubmit = vi.fn((event: FormEvent) => event.preventDefault())
    render(
      <form onSubmit={onSubmit}>
        <PackagingCodePicker options={OPTIONS} value={['NHG0100']} onChange={onChange} />
      </form>,
    )
    await user.type(boxInput(), 'chai')
    await user.keyboard('{ArrowDown}{ArrowDown}{Enter}')
    // options are sorted by the caller: CPT0105 then CPT0075, so the 2nd highlighted row is CPT0075
    expect(onChange).toHaveBeenCalledWith(['NHG0100', 'CPT0075'])
    expect(onSubmit).not.toHaveBeenCalled()
    expect(boxInput()).toHaveValue('')
    expect(screen.getAllByRole('option')).toHaveLength(4)
  })

  it('Enter with no highlight adds the exact typed code, or the single remaining match, and ignores the rest', async () => {
    const { user, onChange } = await openPicker(['NHG0100'])
    await user.type(boxInput(), 'nap0085{Enter}')
    expect(onChange).toHaveBeenLastCalledWith(['NHG0100', 'NAP0085'])
    expect(boxInput()).toHaveValue('')
    onChange.mockClear()
    // two matches and no exact code: nothing is added and the text stays
    await user.type(boxInput(), 'chai{Enter}')
    expect(onChange).not.toHaveBeenCalled()
    expect(boxInput()).toHaveValue('chai')
    await user.clear(boxInput())
    // a single remaining match ("nap" only hits NAP0085) is added without typing the full code
    await user.type(boxInput(), 'nap{Enter}')
    expect(onChange).toHaveBeenLastCalledWith(['NHG0100', 'NAP0085'])
  })

  it('Enter never clears chips and the cap still blocks it with a toast', async () => {
    toastError.mockClear()
    const { user, onChange } = await openPicker(['CPT0105', 'CPT0075'], 2)
    await user.type(boxInput(), 'nap0085{Enter}')
    expect(onChange).not.toHaveBeenCalled()
    expect(toastError).toHaveBeenCalledWith(expect.stringContaining('tối đa 2 mã'))
  })

  it('Backspace on an empty box removes the last chip, but not while text is typed', async () => {
    const { user, onChange } = await openPicker(['CPT0105', 'NAP0085'])
    await user.type(boxInput(), 'x')
    await user.keyboard('{Backspace}')
    expect(onChange).not.toHaveBeenCalled()
    await user.keyboard('{Backspace}')
    expect(onChange).toHaveBeenCalledWith(['CPT0105'])
  })

  it('Escape closes the list and blurs the box', async () => {
    const { user } = await openPicker()
    expect(screen.getByRole('listbox')).toBeInTheDocument()
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    expect(boxInput()).toHaveAttribute('aria-expanded', 'false')
  })

  it('keeps the list open and the typed text after a mouse pick so several matches can be chosen', async () => {
    const { user, onChange } = await openPicker()
    await user.type(boxInput(), 'chai')
    await user.click(screen.getByRole('option', { name: /CPT0105/ }))
    expect(onChange).toHaveBeenCalledWith(['CPT0105'])
    expect(screen.getByRole('listbox')).toBeInTheDocument()
    expect(boxInput()).toHaveValue('chai')
    expect(boxInput()).toHaveFocus()
  })

  it('has accessible combobox wiring: aria-controls points at the listbox, options carry aria-selected', async () => {
    await openPicker(['NAP0085'])
    const listbox = screen.getByRole('listbox')
    expect(boxInput()).toHaveAttribute('aria-controls', listbox.id)
    const selected = within(listbox).getByRole('option', { name: /NAP0085/ })
    expect(selected).toHaveAttribute('aria-selected', 'true')
    expect(within(listbox).getByRole('option', { name: /CPT0105/ })).toHaveAttribute('aria-selected', 'false')
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
    await user.click(screen.getByRole('combobox', { name: 'Chọn mã sản phẩm' }))
    return { user, onChange }
  }

  it('treats a typed word as plain text (a product named "Chai ..." is not mistaken for the Chai group)', async () => {
    const { user } = await openProducts()
    await user.type(screen.getByRole('combobox', { name: 'Chọn mã sản phẩm' }), 'chai')
    expect(screen.getAllByRole('option')).toHaveLength(2)
    await user.clear(screen.getByRole('combobox', { name: 'Chọn mã sản phẩm' }))
    await user.type(screen.getByRole('combobox', { name: 'Chọn mã sản phẩm' }), 'tương')
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
    expect(screen.getByPlaceholderText('Tất cả mã VTBB')).toBeInTheDocument()
  })
})

