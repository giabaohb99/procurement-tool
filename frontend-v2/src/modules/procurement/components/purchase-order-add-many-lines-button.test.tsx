import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { PurchaseOrderAddManyLinesButton } from './purchase-order-add-many-lines-button'
import { ADD_MANY_LINES_MAX, parseAddManyLinesCount } from './purchase-order-add-many-lines-count'

/** duoc-CR-741 — nút Thêm nhiều của bản v1: hỏi số dòng, mặc định 3. */
describe('parseAddManyLinesCount', () => {
  it('reads a plain number', () => {
    expect(parseAddManyLinesCount('5')).toBe(5)
    expect(parseAddManyLinesCount(' 12 ')).toBe(12)
  })

  it('adds one line on anything unreadable, like v1 (blank, text, zero, negative)', () => {
    for (const raw of ['', 'abc', '0', '-4', '   ']) {
      expect(parseAddManyLinesCount(raw)).toBe(1)
    }
  })

  it('caps a mistyped huge number so the browser does not freeze', () => {
    expect(parseAddManyLinesCount('30000')).toBe(ADD_MANY_LINES_MAX)
    expect(parseAddManyLinesCount('1e9')).toBe(1)
  })
})

describe('PurchaseOrderAddManyLinesButton', () => {
  it('asks how many lines with v1 wording and adds the default 3', async () => {
    const onAdd = vi.fn()
    render(<PurchaseOrderAddManyLinesButton onAdd={onAdd} />)
    await userEvent.click(screen.getByRole('button', { name: 'Thêm nhiều' }))

    expect(screen.getByRole('heading', { name: 'Nhập thông tin' })).toBeInTheDocument()
    expect(screen.getByText('Thêm bao nhiêu dòng?')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Số dòng cần thêm' })).toHaveValue('3')
    await userEvent.click(screen.getByRole('button', { name: 'Xác nhận' }))
    expect(onAdd).toHaveBeenCalledWith(3)
  })

  it('confirms on Enter and adds nothing on Hủy', async () => {
    const onAdd = vi.fn()
    render(<PurchaseOrderAddManyLinesButton onAdd={onAdd} />)

    await userEvent.click(screen.getByRole('button', { name: 'Thêm nhiều' }))
    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(onAdd).not.toHaveBeenCalled()

    await userEvent.click(screen.getByRole('button', { name: 'Thêm nhiều' }))
    const input = screen.getByRole('textbox', { name: 'Số dòng cần thêm' })
    await userEvent.clear(input)
    await userEvent.type(input, '7{Enter}')
    expect(onAdd).toHaveBeenCalledWith(7)
  })

  it('never submits a surrounding form', async () => {
    const onSubmit = vi.fn((event: React.FormEvent) => event.preventDefault())
    render(
      <form onSubmit={onSubmit}>
        <PurchaseOrderAddManyLinesButton onAdd={vi.fn()} />
      </form>,
    )
    await userEvent.click(screen.getByRole('button', { name: 'Thêm nhiều' }))
    expect(onSubmit).not.toHaveBeenCalled()
  })
})
