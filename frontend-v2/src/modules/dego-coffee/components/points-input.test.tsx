import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'

import { PointsInput } from './points-input'

function Harness({ initial = 0 }: { initial?: number }) {
  const [value, setValue] = useState(initial)
  return <PointsInput id="p" value={value} onChange={setValue} />
}

describe('PointsInput', () => {
  it('inserts thousand separators WHILE typing, not only on blur', () => {
    render(<Harness />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: '200000' } })
    //  Yêu cầu 08/09/2026: gõ 200000 phải thấy 200.000 ngay — khác NumberInput
    //  dùng chung (cố ý hiện số thô khi đang gõ).
    expect((input as HTMLInputElement).value).toBe('200.000')
  })

  it('strips every non-digit character (paste "1,5tr đ" does not corrupt the value)', () => {
    render(<Harness />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: '1,5tr đ' } })
    expect((input as HTMLInputElement).value).toBe('15')
  })

  it('shows empty for zero instead of a literal 0 blocking the caret', () => {
    render(<Harness initial={0} />)
    expect((screen.getByRole('textbox') as HTMLInputElement).value).toBe('')
  })

  it('caps at 1 tỷ — a held-down key cannot overflow the INT column', () => {
    render(<Harness />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: '99999999999999' } })
    expect((input as HTMLInputElement).value).toBe('1.000.000.000')
  })
})
