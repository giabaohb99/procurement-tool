import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import {
  VARIABLE_TYPE_DATE,
  VARIABLE_TYPE_MONEY,
  VARIABLE_TYPE_MULTILINE,
  VARIABLE_TYPE_NUMBER,
  VARIABLE_TYPE_TEXT,
} from '../types/labor-contract-variable'
import { LaborContractVariableValueInput } from './labor-contract-variable-value-input'

function Harness({ type, initial = '', spy }: { type: number; initial?: string; spy: (v: string) => void }) {
  const [value, setValue] = useState(initial)
  return (
    <LaborContractVariableValueInput
      valueType={type}
      value={value}
      aria-label="Ô thử"
      onChange={(v) => {
        setValue(v)
        spy(v)
      }}
    />
  )
}

describe('LaborContractVariableValueInput', () => {
  it('chữ: ô một dòng; chữ nhiều dòng: ô văn bản nhiều dòng', () => {
    const { unmount } = render(<Harness type={VARIABLE_TYPE_TEXT} spy={vi.fn()} />)
    expect(screen.getByRole('textbox', { name: 'Ô thử' }).tagName).toBe('INPUT')
    unmount()
    render(<Harness type={VARIABLE_TYPE_MULTILINE} spy={vi.fn()} />)
    expect(screen.getByRole('textbox', { name: 'Ô thử' }).tagName).toBe('TEXTAREA')
  })

  it('ngày: nút chọn ngày hiện dd/mm/yyyy', () => {
    render(<Harness type={VARIABLE_TYPE_DATE} initial="2026-10-01" spy={vi.fn()} />)
    expect(screen.getByRole('button', { name: /01\/10\/2026/ })).toBeInTheDocument()
  })

  it('số: gõ "1,5" ra giá trị chuẩn "1.5", chữ trong ô giữ nguyên "1,5"', async () => {
    const spy = vi.fn()
    render(<Harness type={VARIABLE_TYPE_NUMBER} spy={spy} />)
    await userEvent.type(screen.getByRole('textbox', { name: 'Ô thử' }), '1,5')
    expect(spy).toHaveBeenLastCalledWith('1.5')
    expect(screen.getByRole('textbox', { name: 'Ô thử' })).toHaveValue('1,5')
  })

  it('số: ký tự lạ và dấu trừ bị bỏ, tối đa 2 số lẻ', async () => {
    const spy = vi.fn()
    render(<Harness type={VARIABLE_TYPE_NUMBER} spy={spy} />)
    await userEvent.type(screen.getByRole('textbox', { name: 'Ô thử' }), '-a1.234')
    expect(spy).toHaveBeenLastCalledWith('1.23')
  })

  it('tiền: ra chuỗi chữ số; dán số vượt 10^12 bị kẹp về trần; không có dấu âm', async () => {
    const spy = vi.fn()
    render(<Harness type={VARIABLE_TYPE_MONEY} spy={spy} />)
    const box = screen.getByRole('textbox', { name: 'Ô thử' })
    await userEvent.type(box, '15000000')
    expect(spy).toHaveBeenLastCalledWith('15000000')
    await userEvent.clear(box)
    await userEvent.type(box, '-5')
    expect(spy).toHaveBeenLastCalledWith('5')
    await userEvent.clear(box)
    await userEvent.type(box, '99999999999999')
    expect(spy).toHaveBeenLastCalledWith(String(10 ** 12))
  })

  it('số 0 là một giá trị thật (tiền và số); xóa sạch ô mới là "không có giá trị"', async () => {
    const money = vi.fn()
    const { unmount } = render(<Harness type={VARIABLE_TYPE_MONEY} spy={money} />)
    const box = screen.getByRole('textbox', { name: 'Ô thử' })
    await userEvent.type(box, '0')
    expect(money).toHaveBeenLastCalledWith('0')
    expect(box).toHaveValue('0')
    await userEvent.type(box, '5')
    expect(money).toHaveBeenLastCalledWith('5')               // bỏ số 0 đứng đầu
    await userEvent.clear(box)
    expect(money).toHaveBeenLastCalledWith('')
    unmount()
    const num = vi.fn()
    render(<Harness type={VARIABLE_TYPE_NUMBER} spy={num} />)
    await userEvent.type(screen.getByRole('textbox', { name: 'Ô thử' }), '0')
    expect(num).toHaveBeenLastCalledWith('0')
  })

  it('Enter trong ô chữ không submit form cha', async () => {
    const submit = vi.fn((e: { preventDefault: () => void }) => e.preventDefault())
    render(
      <form onSubmit={submit}>
        <Harness type={VARIABLE_TYPE_TEXT} spy={vi.fn()} />
      </form>,
    )
    await userEvent.type(screen.getByRole('textbox', { name: 'Ô thử' }), 'abc{Enter}')
    expect(submit).not.toHaveBeenCalled()
  })
})
