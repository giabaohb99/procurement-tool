import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { LeaveRequestPeriodsEditor } from './leave-request-periods-editor'
import { LEAVE_SESSION, MAX_LEAVE_PERIODS } from '../types/leave'
import type { LeavePeriodValue } from '../utils/leave-form-values'

/**
 * "+ Thêm khoảng ngày" (duoc-CR-683). Hành vi người dùng thấy được: thêm / bỏ hàng, số ngày
 * từng hàng + tổng, khóa theo giờ, báo chồng ngày, trần 20 hàng. Ô ngày là `DatePicker` (nút
 * mở lịch), nên ngày của hàng mới kiểm qua giá trị form mà cha nhận được.
 */

const { FULL, AFTERNOON, HOURLY } = LEAVE_SESSION

const day = (from: string, to = from, from_session: number = FULL): LeavePeriodValue => ({
  from_date: from,
  from_session,
  to_date: to,
  to_session: FULL,
})

interface HarnessProps {
  initial: LeavePeriodValue[]
  rowDays?: (number | undefined)[]
  totalDays?: number
  estimateError?: string
  onPeriods?: (periods: LeavePeriodValue[]) => void
}

function Harness({ initial, rowDays, totalDays, estimateError, onPeriods }: HarnessProps) {
  const [state, setState] = useState({ periods: initial, from_time: '', to_time: '' })
  return (
    <form onSubmit={(e) => e.preventDefault()}>
      <LeaveRequestPeriodsEditor
        periods={state.periods}
        fromTime={state.from_time}
        toTime={state.to_time}
        rowDays={rowDays}
        totalDays={totalDays}
        estimateError={estimateError}
        onChange={(patch) => {
          const next = { ...state, ...patch }
          setState(next)
          onPeriods?.(next.periods)
        }}
      />
    </form>
  )
}

describe('LeaveRequestPeriodsEditor — one period looks like before', () => {
  it('shows the plain Từ ngày / Đến ngày pair with no row frame and no remove button', () => {
    render(<Harness initial={[day('2026-10-27')]} />)
    expect(screen.getByText('Từ ngày')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Buổi bắt đầu' })).toBeInTheDocument()
    expect(screen.queryByText(/Khoảng ngày 1/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Bỏ khoảng ngày/ })).not.toBeInTheDocument()
  })

  it('the add button is type="button" so it never submits the page form', () => {
    //  Bẫy biểu mẫu số 3: thiếu `type` là bấm "Thêm" thành LƯU đơn.
    render(<Harness initial={[day('2026-10-27')]} />)
    expect(screen.getByRole('button', { name: /Thêm khoảng ngày/ })).toHaveAttribute('type', 'button')
  })
})

describe('LeaveRequestPeriodsEditor — add / remove', () => {
  it('adds a full-day row starting the day after the last row ends', async () => {
    const user = userEvent.setup()
    const onPeriods = vi.fn()
    render(<Harness initial={[day('2026-10-27')]} onPeriods={onPeriods} />)

    await user.click(screen.getByRole('button', { name: /Thêm khoảng ngày/ }))

    expect(onPeriods).toHaveBeenLastCalledWith([day('2026-10-27'), day('2026-10-28')])
    expect(screen.getByText('Khoảng ngày 1')).toBeInTheDocument()
    expect(screen.getByText('Khoảng ngày 2')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Buổi bắt đầu khoảng 2' })).toBeInTheDocument()
  })

  it('the new row crosses a month end correctly', async () => {
    const user = userEvent.setup()
    const onPeriods = vi.fn()
    render(<Harness initial={[day('2026-10-27', '2026-10-31')]} onPeriods={onPeriods} />)
    await user.click(screen.getByRole('button', { name: /Thêm khoảng ngày/ }))
    expect(onPeriods.mock.lastCall?.[0][1].from_date).toBe('2026-11-01')
  })

  it('removing a middle row keeps the other rows intact and in order', async () => {
    const user = userEvent.setup()
    const onPeriods = vi.fn()
    const rows = [day('2026-10-27'), day('2026-10-29'), day('2026-11-03', '2026-11-07')]
    render(<Harness initial={rows} onPeriods={onPeriods} />)

    await user.click(screen.getByRole('button', { name: 'Bỏ khoảng ngày 2' }))
    expect(onPeriods).toHaveBeenLastCalledWith([rows[0], rows[2]])
  })

  it('going back to one row drops the frame and the remove buttons', async () => {
    const user = userEvent.setup()
    render(<Harness initial={[day('2026-10-27'), day('2026-11-03')]} />)
    await user.click(screen.getByRole('button', { name: 'Bỏ khoảng ngày 1' }))
    expect(screen.queryByRole('button', { name: /Bỏ khoảng ngày/ })).not.toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Buổi bắt đầu' })).toBeInTheDocument()
  })

  it(`locks the add button at ${MAX_LEAVE_PERIODS} rows and says why`, () => {
    const rows = Array.from({ length: MAX_LEAVE_PERIODS }, (_, i) =>
      day(`2026-01-${String(i + 1).padStart(2, '0')}`),
    )
    render(<Harness initial={rows} />)
    expect(screen.getByRole('button', { name: /Thêm khoảng ngày/ })).toBeDisabled()
    expect(screen.getByText(`Tối đa ${MAX_LEAVE_PERIODS} khoảng ngày.`)).toBeInTheDocument()
  })
})

describe('LeaveRequestPeriodsEditor — days and rules', () => {
  it('shows each row day count and the total of the request', () => {
    render(
      <Harness
        initial={[day('2026-10-27'), day('2026-11-03', '2026-11-07', AFTERNOON)]}
        rowDays={[1, 4.5]}
        totalDays={5.5}
      />,
    )
    expect(screen.getByText('· 1 ngày')).toBeInTheDocument()
    expect(screen.getByText('· 4.5 ngày')).toBeInTheDocument()
    expect(screen.getByText('Cộng 2 khoảng: 5.5 ngày')).toBeInTheDocument()
  })

  it('hourly leave hides the add button — hourly is exactly one period', () => {
    render(<Harness initial={[{ ...day('2026-10-27'), from_session: HOURLY, to_session: HOURLY }]} />)
    expect(screen.queryByRole('button', { name: /Thêm khoảng ngày/ })).not.toBeInTheDocument()
    expect(screen.getByLabelText('Từ giờ')).toBeInTheDocument()
  })

  it('with two rows the "Theo giờ" option is disabled', async () => {
    const user = userEvent.setup()
    render(<Harness initial={[day('2026-10-27'), day('2026-11-03')]} />)
    await user.click(screen.getByRole('combobox', { name: 'Buổi bắt đầu khoảng 1' }))
    expect(screen.getByRole('option', { name: 'Theo giờ' })).toHaveAttribute('aria-disabled', 'true')
    expect(screen.getByText('Nghỉ theo giờ chỉ khai một khoảng ngày.')).toBeInTheDocument()
  })

  it('flags BOTH overlapping rows in red, right under them', () => {
    render(<Harness initial={[day('2026-11-03', '2026-11-07'), day('2026-11-05')]} />)
    expect(screen.getAllByText(/chồng ngày với một khoảng khác/)).toHaveLength(2)
  })

  it('flags a row whose end date is before its start date', () => {
    render(<Harness initial={[day('2026-11-07', '2026-11-03')]} />)
    expect(screen.getByText(/phải từ/)).toHaveTextContent('Đến ngày phải từ Từ ngày trở đi.')
  })

  it('shows the backend estimate error (e.g. cross-year) for a multi-period request', () => {
    const msg = 'Đơn nhiều khoảng ngày phải nằm trong cùng một năm.'
    render(<Harness initial={[day('2026-12-30'), day('2027-01-04')]} estimateError={msg} />)
    expect(screen.getByText(msg)).toBeInTheDocument()
  })

  it('each row header carries its own remove button', () => {
    render(<Harness initial={[day('2026-10-27'), day('2026-11-03')]} />)
    const header = screen.getByText('Khoảng ngày 2').closest('div')
    expect(header).not.toBeNull()
    expect(within(header as HTMLElement).getByRole('button', { name: 'Bỏ khoảng ngày 2' })).toBeInTheDocument()
  })
})

/**
 * Trình đọc màn hình (L9 của bản rà duoc-CR-683): đơn nhiều khoảng có năm cụm "Từ ngày" giống
 * hệt nhau — thiếu tên hàng thì người dùng không biết mình đang ở khoảng nào.
 */
describe('LeaveRequestPeriodsEditor — accessible names per row', () => {
  it('names each date group after its row in a multi-period request', () => {
    render(<Harness initial={[day('2026-10-27'), day('2026-11-03', '2026-11-07')]} />)
    const fromGroup = screen.getByRole('group', { name: /Khoảng ngày 2 – Từ ngày/ })
    //  Nút ngày vẫn mang ngày đang chọn làm tên — nhãn nhóm không nuốt mất giá trị.
    expect(within(fromGroup).getByRole('button', { name: /03\/11\/2026/ })).toBeInTheDocument()
    expect(within(fromGroup).getByRole('combobox', { name: 'Buổi bắt đầu khoảng 2' })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /Khoảng ngày 2 – Đến ngày/ })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /Khoảng ngày 1 – Từ ngày/ })).toBeInTheDocument()
  })

  it('a single-period request keeps the plain names, no row prefix', () => {
    render(<Harness initial={[day('2026-10-27')]} />)
    expect(screen.getByRole('group', { name: /^Từ ngày/ })).toBeInTheDocument()
    expect(screen.queryByRole('group', { name: /Khoảng ngày/ })).not.toBeInTheDocument()
  })
})
