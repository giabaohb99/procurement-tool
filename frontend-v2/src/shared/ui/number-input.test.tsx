import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import {
  DEFAULT_MAX_DECIMALS,
  formatNumberVn,
  NumberInput,
  parseNumberVn,
  PRICE_MAX_DECIMALS,
} from './number-input'

describe('formatNumberVn', () => {
  it('groups thousands with dots the way Vietnamese documents do', () => {
    expect(formatNumberVn(3500000)).toBe('3.500.000')
    expect(formatNumberVn(35000)).toBe('35.000')
    expect(formatNumberVn(1000)).toBe('1.000')
  })

  it('uses a comma for the decimal part', () => {
    expect(formatNumberVn(1250.5)).toBe('1.250,5')
    expect(formatNumberVn(1668.182, true, PRICE_MAX_DECIMALS)).toBe('1.668,182')
  })

  //  Ô trống dễ đọc hơn ô đầy số 0 — cả bảng 27 cột mà cột nào cũng "0" thì
  //  không phân biệt được "chưa nhập" với "bằng không".
  it('shows an empty box instead of a lone zero', () => {
    expect(formatNumberVn(0)).toBe('')
    expect(formatNumberVn(NaN)).toBe('')
  })

  it('rounds to whole numbers when decimals are turned off', () => {
    expect(formatNumberVn(1250.7, false)).toBe('1.251')
  })

  it('cuts the tail at maxDecimals instead of spilling every digit', () => {
    expect(formatNumberVn(1.23456)).toBe('1,235')
    expect(formatNumberVn(1.23456, true, PRICE_MAX_DECIMALS)).toBe('1,2346')
  })
})

describe('parseNumberVn', () => {
  it('reads back exactly what formatNumberVn wrote', () => {
    expect(parseNumberVn('3.500.000')).toBe(3500000)
    expect(parseNumberVn('1.250,5')).toBe(1250.5)
  })

  it('treats a bare typed number as thousands-free', () => {
    expect(parseNumberVn('35000')).toBe(35000)
  })

  it('gives 0 for anything that is not a number', () => {
    expect(parseNumberVn('')).toBe(0)
    expect(parseNumberVn('abc')).toBe(0)
    expect(parseNumberVn(',')).toBe(0)
    expect(parseNumberVn('.')).toBe(0)
  })

  //  Không có ô số nào của chứng từ mang nghĩa khi âm, và dấu trừ lọt lên server
  //  thì thành tiền âm trong sổ công nợ.
  it('refuses negative amounts', () => {
    expect(parseNumberVn('-500')).toBe(500)
  })

  it('keeps only one decimal separator when the user types two commas', () => {
    expect(parseNumberVn('1,2,3')).toBe(1.23)
  })

  it('drops the decimal part entirely when decimals are off', () => {
    expect(parseNumberVn('1.250,75', false)).toBe(125075)
    expect(parseNumberVn('18', false)).toBe(18)
  })

  it('cuts extra decimals rather than sending a longer number than the column holds', () => {
    expect(parseNumberVn('1,23456')).toBe(1.235)
    expect(parseNumberVn('1,23456', true, PRICE_MAX_DECIMALS)).toBe(1.2346)
  })

  it('survives a huge number without turning into scientific notation', () => {
    expect(parseNumberVn('999.999.999.999')).toBe(999999999999)
  })
})

describe('NumberInput', () => {
  it('shows the formatted number while the box is idle', () => {
    render(<NumberInput value={3500000} onChange={vi.fn()} />)
    expect(screen.getByRole('textbox')).toHaveValue('3.500.000')
  })

  it('reports the parsed number as the user types', async () => {
    const onChange = vi.fn()
    render(<NumberInput value={0} onChange={onChange} />)
    await userEvent.type(screen.getByRole('textbox'), '35000')
    expect(onChange).toHaveBeenLastCalledWith(35000)
  })

  it('reformats once the box loses focus', async () => {
    function Harness() {
      const [value, setValue] = useState(0)
      return <NumberInput value={value} onChange={setValue} />
    }
    render(<Harness />)
    const box = screen.getByRole('textbox')
    await userEvent.type(box, '35000')
    await userEvent.tab()
    expect(box).toHaveValue('35.000')
  })

  it('clamps to max while typing so the server never sees the overflow', async () => {
    const onChange = vi.fn()
    render(<NumberInput value={0} max={99.99} onChange={onChange} />)
    await userEvent.type(screen.getByRole('textbox'), '150')
    expect(onChange).toHaveBeenLastCalledWith(99.99)
  })

  it('is a text box, not a spinner — no wheel-scroll surprises', () => {
    render(<NumberInput value={5} onChange={vi.fn()} />)
    expect(screen.getByRole('textbox')).toHaveAttribute('type', 'text')
  })

  it('keeps the default decimal budget in step with the shared constant', () => {
    expect(DEFAULT_MAX_DECIMALS).toBe(3)
    expect(PRICE_MAX_DECIMALS).toBe(4)
  })
})
