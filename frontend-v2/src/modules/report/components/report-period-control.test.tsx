import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ReportPeriodControl, type ReportPeriodInput } from './report-period-control'

const onApply = vi.fn()

function build(overrides: Partial<Parameters<typeof ReportPeriodControl>[0]> = {}) {
  return render(
    <ReportPeriodControl
      preset="this_month"
      from=""
      to=""
      compare="previous"
      onApply={onApply}
      {...overrides}
    />,
  )
}

/** Nút mở popover kỳ — nhãn của nó gộp cả preset lẫn khoảng ngày, bám icon cho chắc. */
function trigger(): HTMLElement {
  const el = document.querySelector('[aria-haspopup="dialog"]')
  if (!el) throw new Error('Không thấy nút mở popover kỳ')
  return el as HTMLElement
}

async function openPopover(overrides: Partial<Parameters<typeof ReportPeriodControl>[0]> = {}) {
  const user = userEvent.setup()
  build(overrides)
  await user.click(trigger())
  return user
}

beforeEach(() => onApply.mockClear())

describe('ReportPeriodControl — trigger reflects the APPLIED period, not the draft', () => {
  it('shows the preset label and a locally computed range before any API response arrives', () => {
    build()
    expect(trigger()).toHaveTextContent('Tháng này')
  })

  it('prefers the backend-resolved range once a response is available', () => {
    build({
      period: {
        date_from: '2026-09-01',
        date_to: '2026-09-28',
        compare_from: '2026-08-01',
        compare_to: '2026-08-28',
        compare: 'previous',
        granularity: 'day',
        preset: 'this_month',
      },
    })
    expect(trigger()).toHaveTextContent('01/09/2026 – 28/09/2026')
    expect(screen.getByText(/So với 01\/08\/2026 – 28\/08\/2026/)).toBeInTheDocument()
  })

  it('shows "Không so sánh" under the trigger when compare is off', () => {
    build({ compare: 'none' })
    expect(screen.getByText('Không so sánh')).toBeInTheDocument()
  })
})

describe('ReportPeriodControl — popover stages changes locally, applies in ONE call', () => {
  it('picks a different preset and calls onApply exactly once on "Áp dụng"', async () => {
    const user = await openPopover()
    const dialog = within(screen.getByRole('dialog'))

    await user.click(dialog.getByRole('button', { name: 'Năm nay' }))
    await user.click(dialog.getByRole('button', { name: 'Áp dụng' }))

    expect(onApply).toHaveBeenCalledTimes(1)
    const applied = onApply.mock.calls[0][0] as ReportPeriodInput
    expect(applied.preset).toBe('this_year')
    expect(applied.compare).toBe('previous')
  })

  it('discards the staged change when "Hủy" is clicked', async () => {
    const user = await openPopover()
    const dialog = within(screen.getByRole('dialog'))

    await user.click(dialog.getByRole('button', { name: 'Năm nay' }))
    await user.click(dialog.getByRole('button', { name: 'Hủy' }))

    expect(onApply).not.toHaveBeenCalled()
  })

  it('reopening after Hủy shows the still-applied preset, not the discarded draft', async () => {
    const user = await openPopover()
    let dialog = within(screen.getByRole('dialog'))
    await user.click(dialog.getByRole('button', { name: 'Năm nay' }))
    await user.click(dialog.getByRole('button', { name: 'Hủy' }))

    await user.click(trigger())
    dialog = within(screen.getByRole('dialog'))
    //  "Tháng này" vẫn phải là mục đang tô đậm (aria-pressed) — không phải "Năm nay".
    expect(dialog.getByRole('button', { name: 'Tháng này' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('lets a compare change ride along with the preset change in the SAME Áp dụng call', async () => {
    const user = await openPopover()
    const dialog = within(screen.getByRole('dialog'))

    await user.click(dialog.getByRole('button', { name: 'Năm nay' }))
    //  `ToggleGroup type="single"` của Radix vẽ mỗi lựa chọn bằng `role="radio"`
    //  trong một `role="radiogroup"`, không phải `role="button"`.
    await user.click(dialog.getByRole('radio', { name: 'Không so sánh' }))
    await user.click(dialog.getByRole('button', { name: 'Áp dụng' }))

    expect(onApply).toHaveBeenCalledTimes(1)
    expect(onApply).toHaveBeenCalledWith(
      expect.objectContaining({ preset: 'this_year', compare: 'none' }),
    )
  })

  it('picking one day disables "Áp dụng" until an end day is picked, then applies the exact picked range', async () => {
    //  Cố định `preset: 'custom'` với khoảng ngày biết trước — KHÔNG dựa vào
    //  "tháng này" của đồng hồ hệ thống (`resolveLocalPresetRange` đọc
    //  `new Date()` thật), tránh test đỏ tùy ngày chạy CI (`testing.md`).
    const user = await openPopover({ preset: 'custom', from: '2026-03-01', to: '2026-03-10' })
    const dialog = within(screen.getByRole('dialog'))
    const day = (value: string) => {
      const cell = document.querySelector(`[data-day="${value}"]`)
      if (!cell) throw new Error(`Lịch không có ngày ${value}`)
      return within(cell as HTMLElement).getByRole('button')
    }

    //  Bấm MỘT đầu — "Tùy chọn" vẫn đang chọn nhưng chưa đủ hai đầu.
    await user.click(day('2026-03-15'))
    expect(dialog.getByRole('button', { name: 'Áp dụng' })).toBeDisabled()

    //  Bấm đầu THỨ HAI — đủ khoảng, "Áp dụng" mở khóa và gửi ĐÚNG khoảng vừa chọn.
    await user.click(day('2026-03-20'))
    expect(dialog.getByRole('button', { name: 'Áp dụng' })).toBeEnabled()

    await user.click(dialog.getByRole('button', { name: 'Áp dụng' }))
    expect(onApply).toHaveBeenCalledWith(
      expect.objectContaining({ preset: 'custom', from: '2026-03-15', to: '2026-03-20' }),
    )
  })
})
