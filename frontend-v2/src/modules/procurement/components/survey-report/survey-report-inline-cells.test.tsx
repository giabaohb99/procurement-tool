// duoc-CR-612 — ô chữ sửa tại chỗ của dạng «Bảng». Mỗi lần lưu là một PATCH ghi thẳng DB và
// một dòng Lịch sử thao tác, nên lỗi đáng sợ nhất là lưu THỪA (rời ô không đổi gì vẫn gửi,
// Enter rồi blur gửi hai lần) hoặc lưu NHẦM (Esc mà vẫn lưu, tên rỗng lọt xuống backend).
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { InlineTextCell } from './survey-report-inline-cells'

const toastError = vi.fn()
vi.mock('sonner', () => ({ toast: { error: (...args: unknown[]) => toastError(...args) } }))

function renderCell(props: Partial<React.ComponentProps<typeof InlineTextCell>> = {}) {
  const onCommit = vi.fn()
  render(
    <InlineTextCell value="Giấy phép" label="tên hồ sơ" maxLength={255} onCommit={onCommit} {...props} />,
  )
  return onCommit
}

function startEditing() {
  fireEvent.click(screen.getByRole('button', { name: /Sửa/ }))
  return screen.getByRole('textbox', { name: /tên hồ sơ|mô tả/ })
}

describe('InlineTextCell', () => {
  it('commits the trimmed value exactly once when Enter is followed by a stray blur', () => {
    const onCommit = renderCell()
    const input = startEditing()
    fireEvent.change(input, { target: { value: '  Giấy phép mới  ' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    //  Trình duyệt có thể bắn blur khi ô nhập bị gỡ — không được thành lần lưu thứ hai.
    fireEvent.blur(input)
    expect(onCommit).toHaveBeenCalledTimes(1)
    expect(onCommit).toHaveBeenCalledWith('Giấy phép mới')
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('saves on blur too, so clicking into the next cell does not lose the typing', () => {
    const onCommit = renderCell()
    const input = startEditing()
    fireEvent.change(input, { target: { value: 'Đã đổi' } })
    fireEvent.blur(input)
    expect(onCommit).toHaveBeenCalledWith('Đã đổi')
  })

  it('discards the draft on Escape and sends nothing', () => {
    const onCommit = renderCell()
    const input = startEditing()
    fireEvent.change(input, { target: { value: 'Gõ nhầm' } })
    fireEvent.keyDown(input, { key: 'Escape' })
    fireEvent.blur(input)
    expect(onCommit).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /Sửa/ })).toHaveTextContent('Giấy phép')
  })

  it('does not send a request when the value only gained surrounding spaces', () => {
    const onCommit = renderCell()
    const input = startEditing()
    fireEvent.change(input, { target: { value: '   Giấy phép ' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onCommit).not.toHaveBeenCalled()
  })

  it('refuses to blank a required cell and keeps the old value', () => {
    toastError.mockReset()
    const onCommit = renderCell({ required: true })
    const input = startEditing()
    fireEvent.change(input, { target: { value: '    ' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onCommit).not.toHaveBeenCalled()
    expect(toastError).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: /Sửa/ })).toHaveTextContent('Giấy phép')
  })

  it('lets an optional cell be cleared to an empty string', () => {
    const onCommit = renderCell({ label: 'mô tả', value: 'Cũ' })
    const input = startEditing()
    fireEvent.change(input, { target: { value: '' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onCommit).toHaveBeenCalledWith('')
  })

  it('keeps Shift+Enter as a newline in multi-line cells and saves on plain Enter', () => {
    const onCommit = renderCell({ label: 'mô tả', value: '', multiline: true })
    const input = startEditing()
    fireEvent.change(input, { target: { value: 'dòng 1' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true })
    expect(onCommit).not.toHaveBeenCalled()
    fireEvent.change(input, { target: { value: 'dòng 1\ndòng 2' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onCommit).toHaveBeenCalledWith('dòng 1\ndòng 2')
  })

  it('stops Enter from bubbling into a surrounding form', () => {
    const onSubmit = vi.fn((event: React.FormEvent) => event.preventDefault())
    render(
      <form onSubmit={onSubmit}>
        <InlineTextCell value="A" label="tên hồ sơ" maxLength={255} onCommit={vi.fn()} />
      </form>,
    )
    const input = startEditing()
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('renders plain text with no edit affordance when read-only', () => {
    renderCell({ readOnly: true })
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.getByText('Giấy phép')).toBeInTheDocument()
  })

  it('cannot enter edit mode while disabled', () => {
    renderCell({ disabled: true })
    fireEvent.click(screen.getByRole('button', { name: /Sửa/ }))
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  //  Lỗi rà soát H1: Enter chốt chữ của bộ gõ tiếng Việt mang `isComposing` — lưu lúc đó
  //  là mất dấu của chữ cuối.
  it('ignores the Enter that a Vietnamese IME uses to confirm a syllable', () => {
    const onCommit = renderCell()
    const input = startEditing()
    fireEvent.change(input, { target: { value: 'Giấy phép mơi' } })
    fireEvent.keyDown(input, { key: 'Enter', isComposing: true })
    expect(onCommit).not.toHaveBeenCalled()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('does not save when the old value merely had stray spaces and the user changed nothing', () => {
    const onCommit = renderCell({ value: '  Giấy phép\n' })
    const input = startEditing()
    fireEvent.blur(input)
    expect(onCommit).not.toHaveBeenCalled()
  })

  it('returns keyboard focus to the cell after Enter so the user does not lose their place', () => {
    renderCell()
    const input = startEditing()
    fireEvent.change(input, { target: { value: 'Mới' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(screen.getByRole('button', { name: /Sửa tên hồ sơ/ })).toHaveFocus()
  })

  it('reads the current value in the accessible name, not just the action', () => {
    renderCell()
    expect(screen.getByRole('button', { name: 'Sửa tên hồ sơ: Giấy phép' })).toBeInTheDocument()
  })
})
