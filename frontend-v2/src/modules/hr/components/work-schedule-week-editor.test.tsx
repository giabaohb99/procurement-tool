import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useForm, useWatch, type Control } from 'react-hook-form'
import { describe, expect, it } from 'vitest'

import type { CrudRecord } from '@/shared/crud'
import type { WorkScheduleDay } from '../types/work-schedule'
import { WORK_DAY_KIND_CODE } from '../types/work-schedule'
import { buildDefaultWeek } from '../utils/work-schedule-week'
import { WorkScheduleWeekEditor } from './work-schedule-week-editor'

/** Hiện giá trị đang nằm trong form dạng JSON để khẳng định thứ SẼ GỬI LÊN backend. */
function ValueProbe({ control }: { control: Control<CrudRecord> }) {
  const days = useWatch({ control, name: 'days' })
  return <pre data-testid="payload">{JSON.stringify(days)}</pre>
}

function Harness({ initial, disabled = false }: { initial: unknown; disabled?: boolean }) {
  const { control } = useForm<CrudRecord>({ defaultValues: { days: initial } as CrudRecord })
  return (
    <form>
      <WorkScheduleWeekEditor control={control} name="days" disabled={disabled} />
      <ValueProbe control={control} />
    </form>
  )
}

function currentDays(): WorkScheduleDay[] {
  return JSON.parse(screen.getByTestId('payload').textContent ?? '[]') as WorkScheduleDay[]
}

async function pickKind(user: ReturnType<typeof userEvent.setup>, weekday: string, label: string) {
  await user.click(screen.getByRole('combobox', { name: `${weekday} — loại ngày` }))
  await user.click(await screen.findByRole('option', { name: label }))
}

describe('WorkScheduleWeekEditor', () => {
  it('shows the default week total of 6 workdays', () => {
    render(<Harness initial={buildDefaultWeek()} />)
    expect(screen.getByText('Tổng: 6 ngày công/tuần')).toBeInTheDocument()
  })

  it('choosing Nghỉ removes the time inputs and sends null for all four time fields', async () => {
    const user = userEvent.setup()
    render(<Harness initial={buildDefaultWeek()} />)
    expect(screen.getByLabelText('T3 — giờ vào')).toBeInTheDocument()

    await pickKind(user, 'T3', 'Nghỉ')

    expect(screen.queryByLabelText('T3 — giờ vào')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('T3 — nghỉ trưa từ')).not.toBeInTheDocument()
    const tuesday = currentDays()[1]
    expect([tuesday.start_time, tuesday.end_time, tuesday.lunch_start, tuesday.lunch_end]).toEqual([
      null,
      null,
      null,
      null,
    ])
    expect(screen.getByText('Tổng: 5 ngày công/tuần')).toBeInTheDocument()
  })

  it('choosing Buổi sáng locks the lunch fields away and the total drops to 5,5', async () => {
    const user = userEvent.setup()
    render(<Harness initial={buildDefaultWeek()} />)

    await pickKind(user, 'T7', 'Buổi sáng')

    expect(screen.getByLabelText('T7 — giờ vào')).toBeInTheDocument()
    expect(screen.queryByLabelText('T7 — nghỉ trưa từ')).not.toBeInTheDocument()
    const saturday = currentDays()[5]
    expect(saturday.day_kind).toBe(WORK_DAY_KIND_CODE.MORNING)
    //  Regression: giờ ra từng giữ 17:00 của Cả ngày -> «sáng 08–17».
    expect([saturday.start_time, saturday.end_time, saturday.lunch_start, saturday.lunch_end]).toEqual([
      '08:00',
      '12:00',
      null,
      null,
    ])
    expect(screen.getByText('Tổng: 5,5 ngày công/tuần')).toBeInTheDocument()
  })

  it('turning Chủ nhật from Nghỉ into Cả ngày fills 08:00–17:00 so the payload is never half-empty', async () => {
    const user = userEvent.setup()
    render(<Harness initial={buildDefaultWeek()} />)

    await pickKind(user, 'CN', 'Cả ngày')

    const sunday = currentDays()[6]
    expect([sunday.start_time, sunday.end_time]).toEqual(['08:00', '17:00'])
    expect(screen.getByText('Tổng: 7 ngày công/tuần')).toBeInTheDocument()
  })

  it('editing a time input writes HH:MM into the form and clearing it sends null', async () => {
    const user = userEvent.setup()
    render(<Harness initial={buildDefaultWeek()} />)
    const input = screen.getByLabelText('T2 — giờ vào')

    await user.clear(input)
    expect(currentDays()[0].start_time).toBeNull()
    await user.type(input, '0730')
    expect(currentDays()[0].start_time).toBe('07:30')
  })

  it('renders every hour as 24h text (no AM/PM, no native time input) whatever the browser locale', () => {
    const week = buildDefaultWeek()
    week[0] = { ...week[0], end_time: '17:00' }
    render(<Harness initial={week} />)
    expect(screen.getByLabelText('T2 — giờ ra')).toHaveValue('17:00')
    expect(screen.getByLabelText('T2 — giờ vào')).toHaveValue('08:00')
    expect(screen.getByLabelText('T2 — nghỉ trưa từ')).toHaveValue('12:00')
    expect(document.querySelectorAll('input[type="time"]')).toHaveLength(0)
    expect(document.body.textContent).not.toMatch(/\b(AM|PM)\b/)
  })

  it('Nghỉ days show a muted note instead of empty space, half days show only the work range', async () => {
    const user = userEvent.setup()
    render(<Harness initial={buildDefaultWeek()} />)
    expect(screen.getByText('Nghỉ — không làm việc')).toBeInTheDocument()
    await pickKind(user, 'T7', 'Buổi chiều')
    expect(screen.getByLabelText('T7 — giờ vào')).toHaveValue('13:00')
    expect(screen.queryByLabelText('T7 — nghỉ trưa từ')).not.toBeInTheDocument()
    expect(screen.getAllByText('Không nghỉ trưa')).toHaveLength(1)
  })

  it('preset «T2–T6 hành chính» makes T7 off and the total 5; «T2–T7» restores 6', async () => {
    const user = userEvent.setup()
    render(<Harness initial={buildDefaultWeek()} />)
    await user.click(screen.getByRole('button', { name: 'T2–T6 hành chính' }))
    expect(screen.getByText('Tổng: 5 ngày công/tuần')).toBeInTheDocument()
    expect(currentDays()[5].day_kind).toBe(WORK_DAY_KIND_CODE.OFF)
    await user.click(screen.getByRole('button', { name: 'T2–T7' }))
    expect(screen.getByText('Tổng: 6 ngày công/tuần')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'T7 nửa buổi sáng' }))
    expect(screen.getByText('Tổng: 5,5 ngày công/tuần')).toBeInTheDocument()
  })

  it('shows the Vietnamese validation message when a working day has no hours', async () => {
    const user = userEvent.setup()
    function Wrapper() {
      const { control, handleSubmit } = useForm<CrudRecord>({ defaultValues: { days: buildDefaultWeek() } as CrudRecord })
      return (
        <form onSubmit={handleSubmit(() => undefined)}>
          <WorkScheduleWeekEditor control={control} name="days" />
          <button type="submit">Lưu</button>
        </form>
      )
    }
    render(<Wrapper />)
    await user.clear(screen.getByLabelText('T4 — giờ ra'))
    await user.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('T4: nhập đủ giờ vào và giờ ra.')
  })

  it('«Áp giờ T2 cho T3–T6» copies Monday into Tue–Fri but never overwrites T7 or CN', async () => {
    const user = userEvent.setup()
    const week = buildDefaultWeek()
    week[0] = { ...week[0], start_time: '07:30', end_time: '16:30' }
    week[5] = { ...week[5], day_kind: WORK_DAY_KIND_CODE.MORNING, end_time: '12:00', lunch_start: null, lunch_end: null }
    render(<Harness initial={week} />)

    await user.click(screen.getByRole('button', { name: /Áp giờ T2 cho T3–T6/ }))

    const days = currentDays()
    for (const index of [1, 2, 3, 4]) {
      expect(days[index].start_time).toBe('07:30')
      expect(days[index].weekday).toBe(index)
    }
    expect(days[5].day_kind).toBe(WORK_DAY_KIND_CODE.MORNING)
    expect(days[6].day_kind).toBe(WORK_DAY_KIND_CODE.OFF)
  })

  it('does not submit the surrounding form when its helper button is pressed', async () => {
    const user = userEvent.setup()
    let submitted = false
    function Wrapper() {
      const { control } = useForm<CrudRecord>({ defaultValues: { days: buildDefaultWeek() } as CrudRecord })
      return (
        <form onSubmit={(e) => { e.preventDefault(); submitted = true }}>
          <WorkScheduleWeekEditor control={control} name="days" />
        </form>
      )
    }
    render(<Wrapper />)
    await user.click(screen.getByRole('button', { name: /Áp giờ T2/ }))
    expect(submitted).toBe(false)
  })

  it('disabled mode renders read-only text: no inputs, no selects, no quick-action buttons', () => {
    render(<Harness initial={buildDefaultWeek()} disabled />)
    expect(screen.queryAllByRole('combobox')).toHaveLength(0)
    expect(document.querySelectorAll('input[type="time"]')).toHaveLength(0)
    expect(screen.queryByRole('button', { name: /Áp giờ T2/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'T2–T7' })).not.toBeInTheDocument()
    //  Ngày Cả ngày phải hiện cả giờ nghỉ trưa, ngày nghỉ hiện «Nghỉ».
    expect(screen.getAllByText('08:00–17:00 (nghỉ trưa 12:00–13:00)')).toHaveLength(6)
    expect(screen.getAllByText('Nghỉ')).toHaveLength(1)
  })

  it('disabled mode shows hours for a half day', () => {
    const week = buildDefaultWeek()
    week[5] = { ...week[5], day_kind: WORK_DAY_KIND_CODE.MORNING, end_time: '12:00', lunch_start: null, lunch_end: null }
    render(<Harness initial={week} disabled />)
    expect(screen.getByText('Sáng 08:00–12:00')).toBeInTheDocument()
  })

  it('survives an empty / missing / garbage value from the backend by showing 7 «Nghỉ» rows', () => {
    for (const bad of [[], undefined, null, 'oops']) {
      const { unmount } = render(<Harness initial={bad} disabled />)
      expect(screen.getAllByText('Nghỉ')).toHaveLength(7)
      expect(screen.getByText('Tổng: 0 ngày công/tuần')).toBeInTheDocument()
      unmount()
    }
  })
})
