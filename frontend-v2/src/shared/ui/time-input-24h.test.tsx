import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'

import { TimeInput24h } from './time-input-24h'

function Harness({ initial, onSubmit }: { initial: string | null; onSubmit?: () => void }) {
  const [value, setValue] = useState<string | null>(initial)
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit?.()
      }}
    >
      <TimeInput24h value={value} onChange={setValue} aria-label="Giờ vào" />
      <output data-testid="value">{value === null ? 'null' : value}</output>
    </form>
  )
}

const stored = () => screen.getByTestId('value').textContent

describe('TimeInput24h', () => {
  it('shows the value as plain 24h text, never AM/PM', () => {
    render(<Harness initial="17:00" />)
    expect(screen.getByLabelText('Giờ vào')).toHaveValue('17:00')
  })

  it('typing four digits writes HH:MM immediately and auto-inserts the colon', async () => {
    const user = userEvent.setup()
    render(<Harness initial="08:00" />)
    const input = screen.getByLabelText('Giờ vào')
    await user.clear(input)
    await user.type(input, '1730')
    expect(input).toHaveValue('17:30')
    expect(stored()).toBe('17:30')
  })

  it('a short entry like "9" is normalised to 09:00 on blur', async () => {
    const user = userEvent.setup()
    render(<Harness initial="08:00" />)
    const input = screen.getByLabelText('Giờ vào')
    await user.clear(input)
    await user.type(input, '9')
    await user.tab()
    expect(stored()).toBe('09:00')
    expect(input).toHaveValue('09:00')
  })

  it('an impossible time (25:99) is never written to the form', async () => {
    const user = userEvent.setup()
    render(<Harness initial="08:00" />)
    const input = screen.getByLabelText('Giờ vào')
    await user.clear(input)
    await user.type(input, '2599')
    expect(stored()).not.toBe('25:99')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    await user.tab()
    expect(stored()).not.toBe('25:99')
    expect(input).not.toHaveAttribute('aria-invalid')
  })

  it('clearing the box sends null', async () => {
    const user = userEvent.setup()
    render(<Harness initial="08:00" />)
    await user.clear(screen.getByLabelText('Giờ vào'))
    expect(stored()).toBe('null')
  })

  it('arrow keys step 15 minutes and clamp at the day edge', async () => {
    const user = userEvent.setup()
    render(<Harness initial="23:50" />)
    const input = screen.getByLabelText('Giờ vào')
    input.focus()
    await user.keyboard('{ArrowUp}')
    expect(stored()).toBe('23:59')
    await user.keyboard('{ArrowDown}{ArrowDown}')
    expect(stored()).toBe('23:29')
  })

  it('Enter commits the box but does not submit the surrounding form', async () => {
    const user = userEvent.setup()
    let submitted = false
    render(<Harness initial="08:00" onSubmit={() => (submitted = true)} />)
    const input = screen.getByLabelText('Giờ vào')
    await user.clear(input)
    await user.type(input, '7{Enter}')
    expect(stored()).toBe('07:00')
    expect(submitted).toBe(false)
  })

  it('rejects letters and AM/PM text a hacker or an en-US paste would bring', async () => {
    const user = userEvent.setup()
    render(<Harness initial={null} />)
    const input = screen.getByLabelText('Giờ vào')
    await user.type(input, '8:30 PM')
    expect(input).toHaveValue('08:30')
  })
})
