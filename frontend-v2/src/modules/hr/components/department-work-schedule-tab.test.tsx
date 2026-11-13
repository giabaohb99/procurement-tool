import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { EffectiveDepartmentWorkSchedule, WorkScheduleAssignment } from '../types/work-schedule'
import { WORK_SCHEDULE_LEVEL_CODE } from '../types/work-schedule'
import { DEPARTMENT_FALLBACK_SOURCE } from '../utils/describe-department-schedule-source'
import { parseAssignmentPrefill } from '../utils/work-schedule-assignment-prefill'
import { buildDefaultWeek } from '../utils/work-schedule-week'
import { DepartmentWorkScheduleTab } from './department-work-schedule-tab'

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

function assignment(patch: Partial<WorkScheduleAssignment> = {}): WorkScheduleAssignment {
  return {
    id: 31,
    target_level: WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT,
    target_level_label: 'Phòng ban',
    target_id: 7,
    target_name: 'Kế toán',
    schedule_id: 3,
    schedule_name: 'Hành chính T2–T6',
    effective_from: '2026-11-01',
    effective_to: null,
    note: '',
    is_current: true,
    ...patch,
  }
}

function effective(patch: Partial<EffectiveDepartmentWorkSchedule> = {}): EffectiveDepartmentWorkSchedule {
  return {
    schedule_id: 3,
    schedule_name: 'Hành chính T2–T6',
    days: buildDefaultWeek(),
    weekly_workdays: 6,
    is_fallback: false,
    level: WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT,
    level_label: 'Phòng ban',
    target_name: 'Kế toán',
    assignment_id: 31,
    effective_from: '2026-11-01',
    effective_to: null,
    department_id: 7,
    department_name: 'Kế toán',
    company_id: 1,
    assignments: [assignment()],
    ...patch,
  }
}

function renderTab(departmentId = 7) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <DepartmentWorkScheduleTab departmentId={departmentId} departmentName="Kế toán" />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DepartmentWorkScheduleTab', () => {
  beforeEach(() => {
    apiGet.mockReset()
    permissions = {}
  })

  it('asks the department endpoint with the department id', async () => {
    apiGet.mockResolvedValue(effective())
    renderTab(7)
    await screen.findByText('Gán riêng cho phòng này từ 01/11/2026')
    expect(apiGet).toHaveBeenCalledWith('/api/work-schedules/tools/effective-department', {
      params: { department_id: 7, on_date: undefined },
    })
  })

  it('level DEPARTMENT: says it is assigned to this department from the start date', async () => {
    apiGet.mockResolvedValue(effective())
    renderTab()
    expect(await screen.findByText('Gán riêng cho phòng này từ 01/11/2026')).toBeInTheDocument()
  })

  it('level DEPARTMENT with an end date: says both dates', async () => {
    apiGet.mockResolvedValue(effective({ effective_to: '2026-12-31' }))
    renderTab()
    expect(
      await screen.findByText('Gán riêng cho phòng này từ 01/11/2026 đến 31/12/2026'),
    ).toBeInTheDocument()
  })

  it('level COMPANY: names the company it inherits from', async () => {
    apiGet.mockResolvedValue(
      effective({ level: WORK_SCHEDULE_LEVEL_CODE.COMPANY, level_label: 'Pháp nhân', target_name: 'DEGO Holding', assignments: [] }),
    )
    renderTab()
    expect(await screen.findByText('Theo lịch của pháp nhân DEGO Holding')).toBeInTheDocument()
    expect(screen.getByText('Phòng này chưa có dòng gán lịch riêng.')).toBeInTheDocument()
  })

  it('level SYSTEM: says it follows the company-wide (toàn hệ thống) schedule', async () => {
    apiGet.mockResolvedValue(
      effective({ level: WORK_SCHEDULE_LEVEL_CODE.SYSTEM, level_label: 'Toàn hệ thống', target_name: '', assignments: [] }),
    )
    renderTab()
    expect(await screen.findByText('Theo lịch toàn hệ thống')).toBeInTheDocument()
  })

  // Backend gửi level = 0 khi chưa ai gán gì. Số 0 không khớp cấp nào: phải đọc `is_fallback`,
  // không được rơi xuống nhánh "Không rõ nguồn".
  it('fallback: says nothing is assigned and the built-in default applies', async () => {
    apiGet.mockResolvedValue(
      effective({
        is_fallback: true,
        schedule_id: 0,
        schedule_name: 'Mặc định T2–T7',
        level: 0,
        level_label: '',
        target_name: '',
        assignment_id: 0,
        effective_from: null,
        assignments: [],
      }),
    )
    renderTab()
    expect(await screen.findByText(DEPARTMENT_FALLBACK_SOURCE)).toBeInTheDocument()
    expect(screen.queryByText(/Gán riêng cho phòng này/)).not.toBeInTheDocument()
  })

  // Hợp đồng đính chính (duoc-CR-757): backend gửi số trần 3 Phòng ban · 2 Pháp nhân · 1 Toàn hệ
  // thống · 0 chỉ khi is_fallback. Bản đề bài đầu ghi lệch một bậc (2 phòng ban, 1 pháp nhân,
  // 0 hệ thống) — bài này đọc đúng SỐ backend gửi để lệch kiểu đó không lọt lại.
  it.each([
    [3, 'Gán riêng cho phòng này từ 01/11/2026'],
    [2, 'Theo lịch của pháp nhân DEGO Holding'],
    [1, 'Theo lịch toàn hệ thống'],
  ])('raw backend level %i maps to the right source sentence', async (level, text) => {
    apiGet.mockResolvedValue(effective({ level, target_name: 'DEGO Holding' }))
    renderTab()
    expect(await screen.findByText(text)).toBeInTheDocument()
  })

  it('an unknown level shows the backend label instead of inventing a source', async () => {
    apiGet.mockResolvedValue(effective({ level: 99, level_label: 'Cấp mới' }))
    renderTab()
    expect(await screen.findByText('Cấp mới')).toBeInTheDocument()
  })

  it('lists department assignments: open-ended says Không thời hạn, current one is badged', async () => {
    apiGet.mockResolvedValue(
      effective({
        assignments: [
          assignment(),
          assignment({ id: 30, schedule_name: 'Ca cũ', effective_from: '2026-01-01', effective_to: '2026-10-31', is_current: false }),
        ],
      }),
    )
    renderTab()
    expect(await screen.findByText('Ca cũ')).toBeInTheDocument()
    expect(screen.getByText(/Không thời hạn/)).toBeInTheDocument()
    expect(screen.getByText(/đến 31\/10\/2026/)).toBeInTheDocument()
    expect(screen.getAllByText('Đang áp')).toHaveLength(1)
  })

  it('survives a payload without the assignments array (old backend)', async () => {
    const { assignments: _drop, ...rest } = effective()
    apiGet.mockResolvedValue(rest)
    renderTab()
    expect(await screen.findByText('Phòng này chưa có dòng gán lịch riêng.')).toBeInTheDocument()
  })

  it('tells the user the personal schedule overrides the department one', async () => {
    apiGet.mockResolvedValue(effective())
    renderTab()
    expect(await screen.findByText(/theo lịch riêng đó, không theo lịch của phòng/)).toBeInTheDocument()
  })

  it('hides both assignment buttons without work_schedule permissions', async () => {
    apiGet.mockResolvedValue(effective())
    renderTab()
    await screen.findByText('Gán riêng cho phòng này từ 01/11/2026')
    expect(screen.queryByRole('link', { name: /Gán lịch cho phòng/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Xem gán lịch/ })).not.toBeInTheDocument()
  })

  it('read-only users get the list link but not the create button', async () => {
    permissions = { work_schedule: ['read'] }
    apiGet.mockResolvedValue(effective())
    renderTab()
    expect(await screen.findByRole('link', { name: /Xem gán lịch/ })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Gán lịch cho phòng/ })).not.toBeInTheDocument()
  })

  it('the create button links to the assignment screen with level + this department prefilled', async () => {
    permissions = { work_schedule: ['read', 'create'] }
    apiGet.mockResolvedValue(effective())
    renderTab(7)
    const link = await screen.findByRole('link', { name: /Gán lịch cho phòng/ })
    const href = link.getAttribute('href') ?? ''
    expect(parseAssignmentPrefill(new URLSearchParams(href.split('?')[1]))).toEqual({
      level: WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT,
      targetId: 7,
      targetName: 'Kế toán',
    })
  })

  it('on error (403/404) shows one sentence, and the create button still works', async () => {
    permissions = { work_schedule: ['create'] }
    apiGet.mockRejectedValue(new Error('403'))
    renderTab()
    expect(await screen.findByText('Không xem được lịch làm việc của phòng ban này.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Gán lịch cho phòng/ })).toBeInTheDocument()
  })

  it('does not call the API for a broken department id', () => {
    renderTab(0)
    renderTab(Number.NaN)
    expect(apiGet).not.toHaveBeenCalled()
  })
})
