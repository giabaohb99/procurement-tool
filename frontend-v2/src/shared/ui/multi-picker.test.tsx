import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { MultiPicker, type MultiPickerOption } from './multi-picker'

const OPTIONS: MultiPickerOption[] = [
  { id: 1, label: 'CÔNG TY TNHH DEGO HOLDING', hint: 'DEGO' },
  { id: 2, label: 'CÔNG TY TNHH N2SBIO VIỆT NAM', hint: 'N2SBIO' },
  { id: 3, label: 'NHÀ PHÂN PHỐI DR XANH', hint: 'NPP DR.XANH' },
]

async function openPicker(value: number[] = [], onChange = vi.fn()) {
  const user = userEvent.setup()
  render(
    <MultiPicker
      value={value}
      onChange={onChange}
      options={OPTIONS}
      placeholder="Chọn pháp nhân…"
    />,
  )
  await user.click(screen.getByRole('button', { name: 'Chọn pháp nhân…' }))
  return { user, onChange }
}

describe('MultiPicker', () => {
  it('chọn tất cả thì tick hết danh sách trong một lần bấm', async () => {
    const { user, onChange } = await openPicker()
    await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
    expect(onChange).toHaveBeenCalledWith([1, 2, 3])
  })

  it('đang tìm thì chỉ chọn phần khớp từ khóa, không đụng mục đã chọn trước đó', async () => {
    const { user, onChange } = await openPicker([3])
    await user.type(screen.getByPlaceholderText('Tìm…'), 'n2sbio')
    await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
    expect(onChange).toHaveBeenCalledWith([3, 2])
  })

  it('tick hết rồi thì nút đổi thành bỏ chọn tất cả', async () => {
    const { user, onChange } = await openPicker([1, 2, 3])
    await user.click(screen.getByRole('button', { name: /Bỏ chọn tất cả/ }))
    expect(onChange).toHaveBeenCalledWith([])
  })
})
