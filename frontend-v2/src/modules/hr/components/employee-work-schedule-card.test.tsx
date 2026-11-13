import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { AuthUser } from '@/core/auth/auth-types'
import type { EffectiveWorkSchedule, WorkScheduleDay } from '../types/work-schedule'
import { WORK_DAY_KIND_CODE } from '../types/work-schedule'
import { buildDefaultWeek } from '../utils/work-schedule-week'
import { EmployeeWorkScheduleCard } from './employee-work-schedule-card'

const apiGet = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

let permissions: Record<string, string[]> = {}
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => permissions[entity]?.includes(action) ?? false,
  }),
}))

function effective(patch: Partial<EffectiveWorkSchedule> = {}): EffectiveWorkSchedule {
  return {
    schedule_id: 3,
    schedule_name: 'Hành chính T2–T7',
    days: buildDefaultWeek(),
    weekly_workdays: 6,
    is_fallback: false,
    level: 3,
    level_label: 'Phòng ban',
    target_name: 'Kế toán',
    assignment_id: 9,
    effective_from: '2026-11-01',
    effective_to: null,
    ...patch,
  }
}

function renderCard(employeeId = 7, employeeName?: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <EmployeeWorkScheduleCard employeeId={employeeId} employeeName={employeeName} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('EmployeeWorkScheduleCard', () => {
  beforeEach(() => {
    apiGet.mockReset()
    permissions = {}
    useAuthStore.setState({ user: null })
  })

  it('shows "Mặc định hệ thống" and NO validity dates for the built-in fallback', async () => {
    apiGet.mockResolvedValue(
      effective({
        is_fallback: true,
        schedule_id: 0,
        level: 0,
        schedule_name: 'Mặc định hệ thống (T2–T7, 08:00–17:00)',
        effective_from: '2026-01-01',
        target_name: undefined,
      }),
    )
    renderCard()
    expect(await screen.findByText('Mặc định hệ thống')).toBeInTheDocument()
    expect(screen.queryByText(/Từ \d/)).not.toBeInTheDocument()
  })

  it('shows the department source with an open-ended validity', async () => {
    apiGet.mockResolvedValue(effective())
    renderCard()
    expect(await screen.findByText('Theo phòng ban: Kế toán')).toBeInTheDocument()
    expect(screen.getByText(/Từ 01\/11\/2026 · Không thời hạn/)).toBeInTheDocument()
  })

  it('shows a closed validity range when effective_to is set', async () => {
    apiGet.mockResolvedValue(effective({ effective_to: '2026-12-31', level: 4 }))
    renderCard()
    expect(await screen.findByText('Gán riêng')).toBeInTheDocument()
    expect(screen.getByText(/đến 31\/12\/2026/)).toBeInTheDocument()
  })

  it('renders Saturday morning with its hours and the total as 5,5', async () => {
    const days: WorkScheduleDay[] = buildDefaultWeek()
    days[5] = { ...days[5], day_kind: WORK_DAY_KIND_CODE.MORNING, end_time: '12:00', lunch_start: null, lunch_end: null }
    apiGet.mockResolvedValue(effective({ days, weekly_workdays: 5.5 }))
    renderCard()
    expect(await screen.findByText('Sáng 08:00–12:00')).toBeInTheDocument()
    expect(screen.getByText('5,5 ngày công/tuần')).toBeInTheDocument()
  })

  it('shows the lunch break under each full day, and none under a half day', async () => {
    const days: WorkScheduleDay[] = buildDefaultWeek()
    days[5] = { ...days[5], day_kind: WORK_DAY_KIND_CODE.MORNING, end_time: '12:00', lunch_start: null, lunch_end: null }
    apiGet.mockResolvedValue(effective({ days }))
    renderCard()
    expect(await screen.findAllByText('nghỉ trưa 12:00–13:00')).toHaveLength(5)
  })

  it('labels the SYSTEM level "Toàn hệ thống"', async () => {
    apiGet.mockResolvedValue(effective({ level: 1, target_name: undefined }))
    renderCard()
    expect(await screen.findByText('Toàn hệ thống')).toBeInTheDocument()
    expect(screen.queryByText('Toàn công ty')).not.toBeInTheDocument()
  })

  it('does not crash on empty days: every weekday chip shows "—", never invented as "Nghỉ"', async () => {
    apiGet.mockResolvedValue(effective({ days: [], weekly_workdays: 0 }))
    renderCard()
    expect(await screen.findAllByText('—')).toHaveLength(7)
    expect(screen.queryByText('Nghỉ')).not.toBeInTheDocument()
  })

  it('shows "—" only for weekdays the backend left out', async () => {
    const days = buildDefaultWeek().filter((d) => d.weekday !== 3)
    apiGet.mockResolvedValue(effective({ days }))
    renderCard()
    expect(await screen.findAllByText('—')).toHaveLength(1)
  })

  it('a 404 (out of scope) shows one short sentence and no assign button', async () => {
    permissions = { work_schedule: ['write'] }
    apiGet.mockRejectedValue(Object.assign(new Error('Not found'), { response: { status: 404 } }))
    renderCard()
    expect(await screen.findByText(/Không xem được lịch làm việc/)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Gán lịch' })).not.toBeInTheDocument()
  })

  it('hides "Gán lịch" without work_schedule.write and shows it with', async () => {
    apiGet.mockResolvedValue(effective())
    const { unmount } = renderCard()
    await screen.findByText('Theo phòng ban: Kế toán')
    expect(screen.queryByRole('link', { name: 'Gán lịch' })).not.toBeInTheDocument()
    unmount()

    permissions = { work_schedule: ['write'] }
    renderCard()
    const link = await screen.findByRole('link', { name: 'Gán lịch' })
    expect(link).toHaveAttribute('href', '/hr/work-schedule-assignments')
  })

  it('does not call the API for employeeId 0 or a negative / fractional id', () => {
    for (const id of [0, -3, 1.5, Number.NaN]) {
      const { unmount } = renderCard(id)
      unmount()
    }
    expect(apiGet).not.toHaveBeenCalled()
  })

  describe('"Đổi lịch riêng" (duoc-CR-757 lượt 2)', () => {
    const signInAs = (employeeId: number) =>
      useAuthStore.setState({ user: { id: 1, email: '', full_name: 'TP', employee_id: employeeId } as AuthUser })

    it('a head of department with only the personal key gets a link that prefills employee level + this person', async () => {
      permissions = { work_schedule: ['read'], work_schedule_personal: ['create', 'write'] }
      signInAs(99)
      apiGet.mockResolvedValue(effective())
      renderCard(7, 'NSU007 — Lê Văn A')
      const link = await screen.findByRole('link', { name: 'Đổi lịch riêng' })
      const url = new URL(link.getAttribute('href') ?? '', 'http://x')
      expect(url.pathname).toBe('/hr/work-schedule-assignments')
      expect(url.searchParams.get('target_level')).toBe('4')
      expect(url.searchParams.get('prefill_target_id')).toBe('7')
      expect(url.searchParams.get('prefill_target_name')).toBe('NSU007 — Lê Văn A')
      //  Không có work_schedule.write thì không có lối tắt sang cả màn quản lý.
      expect(screen.queryByRole('link', { name: 'Gán lịch' })).not.toBeInTheDocument()
    })

    it('never offers it on the viewer own profile, even to HR (backend refuses self-assignment)', async () => {
      permissions = { work_schedule: ['create', 'write'], work_schedule_personal: ['create'] }
      signInAs(7)
      apiGet.mockResolvedValue(effective())
      renderCard(7)
      await screen.findByText('Theo phòng ban: Kế toán')
      expect(screen.queryByRole('link', { name: 'Đổi lịch riêng' })).not.toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'Gán lịch' })).toBeInTheDocument()
    })

    it('needs a create right: write-only or read-only keys show no button', async () => {
      apiGet.mockResolvedValue(effective())
      const grants: Record<string, string[]>[] = [
        { work_schedule_personal: ['write', 'delete'] },
        { work_schedule: ['read'], work_schedule_personal: ['read'] },
      ]
      for (const grant of grants) {
        permissions = grant
        const { unmount } = renderCard(7)
        await screen.findByText('Theo phòng ban: Kế toán')
        expect(screen.queryByRole('link', { name: 'Đổi lịch riêng' })).not.toBeInTheDocument()
        unmount()
      }
    })

    it('HR also gets it next to the plain "Gán lịch" link', async () => {
      permissions = { work_schedule: ['create', 'write'] }
      signInAs(99)
      apiGet.mockResolvedValue(effective())
      renderCard(7)
      expect(await screen.findByRole('link', { name: 'Đổi lịch riêng' })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'Gán lịch' })).toBeInTheDocument()
    })

    it('a user without a linked employee record still sees it for others', async () => {
      permissions = { work_schedule_personal: ['create'] }
      apiGet.mockResolvedValue(effective())
      renderCard(7)
      expect(await screen.findByRole('link', { name: 'Đổi lịch riêng' })).toBeInTheDocument()
    })
  })
})
