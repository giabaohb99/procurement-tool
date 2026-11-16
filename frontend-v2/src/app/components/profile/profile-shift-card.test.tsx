import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { MyShiftDay } from '@/modules/hr/types/work-shift'

/*  Thẻ "Ca làm việc tuần này" ở Trang cá nhân (duoc-CR-761): đọc `/api/work-shifts/me` theo tuần thứ Hai → Chủ nhật,
    bày ca xếp riêng như ngoại lệ, và đổi tuần bằng nút. Ngày "hôm nay" cố định để bài không phụ thuộc lịch thật. */

const apiGet = vi.fn()
vi.mock('@/core/api', () => ({ apiGet: (...a: unknown[]) => apiGet(...a) }))

const { ProfileShiftCard } = await import('./profile-shift-card')

function day(date: string, weekday: number, over: Partial<MyShiftDay> = {}): MyShiftDay {
  return {
    date,
    weekday,
    is_shift: false,
    work_kind: 2,
    work_kind_label: 'Cả ngày',
    start_time: '08:00',
    end_time: '17:00',
    segments: ['08:00–12:00', '13:00–17:00'],
    ranges: [],
    hours: 8,
    note: '',
    is_day_off: false,
    is_holiday: false,
    holiday_name: '',
    schedule_name: 'Hành chính',
    ...over,
  }
}

function params(): { from_date: string; to_date: string }[] {
  return apiGet.mock.calls
    .filter((c) => c[0] === '/api/work-shifts/me')
    .map((c) => (c[1] as { params: { from_date: string; to_date: string } }).params)
}

function renderCard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <ProfileShiftCard />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  //  Thứ Tư 18/11/2026, 10:00 giờ VN.
  vi.setSystemTime(new Date('2026-11-18T03:00:00Z'))
  apiGet.mockReset()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('ProfileShiftCard', () => {
  it('asks Monday to Sunday of the current week and shows shift days as exceptions', async () => {
    apiGet.mockResolvedValue({
      employee_id: 5,
      from_date: '2026-11-16',
      to_date: '2026-11-22',
      days: [
        day('2026-11-16', 0),
        day('2026-11-17', 1, { is_shift: true, segments: ['19:00–23:00'], hours: 4, note: 'Livestream', schedule_name: 'Xếp ca theo ngày' }),
        day('2026-11-22', 6, { segments: [], hours: 0, is_day_off: true }),
      ],
    })
    renderCard()
    expect(await screen.findByText('19:00–23:00')).toBeInTheDocument()
    expect(params()[0]).toEqual({ from_date: '2026-11-16', to_date: '2026-11-22' })
    expect(screen.getByText('Ca làm việc tuần này')).toBeInTheDocument()
    expect(screen.getByText('Ca xếp riêng')).toBeInTheDocument()
    expect(screen.getByText('Livestream')).toBeInTheDocument()
    expect(screen.getByText('Nghỉ')).toBeInTheDocument()
  })

  it('moves a week forward and back to this week', async () => {
    apiGet.mockResolvedValue({ employee_id: 5, from_date: '', to_date: '', days: [day('2026-11-16', 0)] })
    renderCard()
    await screen.findByText('13:00–17:00')
    fireEvent.click(screen.getByRole('button', { name: 'Tuần sau' }))
    await waitFor(() => expect(params()).toContainEqual({ from_date: '2026-11-23', to_date: '2026-11-29' }))
    expect(screen.getByText('Ca làm việc 23/11 – 29/11')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Tuần này' }))
    expect(await screen.findByText('Ca làm việc tuần này')).toBeInTheDocument()
  })

  it('an account without an employee profile gets an explanation, not an empty box', async () => {
    apiGet.mockResolvedValue({ employee_id: 0, from_date: '2026-11-16', to_date: '2026-11-22', days: [] })
    renderCard()
    expect(await screen.findByText(/chưa gắn hồ sơ nhân sự/)).toBeInTheDocument()
  })

  it('a load error says so instead of showing an empty week', async () => {
    apiGet.mockRejectedValue(new Error('boom'))
    renderCard()
    expect(await screen.findByText(/Không tải được ca làm việc/)).toBeInTheDocument()
  })
})
