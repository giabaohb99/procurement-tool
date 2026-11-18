import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as OverviewHooks from '../hooks/use-work-overview'
import type { WorkOverview, WorkOverviewTrendBucket } from '../hooks/use-work-overview'
import { WorkOverviewTracker } from './work-overview-tracker'

const trendCalls: { kind: string; id: number | null; periodDays: number }[] = []
let buckets: WorkOverviewTrendBucket[] = []

//  Chỉ thay hook gọi API; kiểu dữ liệu và hằng số giữ nguyên bản thật.
vi.mock('../hooks/use-work-overview', async (importOriginal) => ({
  ...(await importOriginal<typeof OverviewHooks>()),
  useWorkOverviewTrend: (kind: string, id: number | null, periodDays: number) => {
    trendCalls.push({ kind, id, periodDays })
    return { data: { granularity: 'day', buckets }, isLoading: false, isError: false }
  },
}))

const DATA = {
  projects: [
    {
      list_id: 7, name: 'Kho Quý 4', color: '', total: 10, done: 4, open: 6, overdue: 2, done_in_period: 3,
      progress: 40, last_due: '2026-12-01', health: 3, health_label: 'Trễ', can_open: true,
    },
    {
      list_id: 8, name: 'Thu mua', color: '', total: 2, done: 2, open: 0, overdue: 0, done_in_period: 0,
      progress: 100, last_due: '', health: 1, health_label: 'Đúng tiến độ', can_open: true,
    },
  ],
  people: [
    {
      employee_id: 21, name: 'Nguyễn An', code: 'NSU021', avatar: '', open: 4, overdue: 1, due_soon: 0,
      done_in_period: 5, on_time_rate: 40, max_overdue_days: 9, estimate_hours_open: 0, actual_hours_done: 0,
      last_update: null,
    },
  ],
} as unknown as WorkOverview

describe('WorkOverviewTracker (duoc-CR-782)', () => {
  beforeEach(() => {
    trendCalls.length = 0
    buckets = [{ start: '2026-11-17', label: '17/11', created: 2, done_on_time: 1, done_late: 1, done_no_due: 0 }]
  })

  it('starts on the first (most worrying) project and shows its own numbers', () => {
    render(<WorkOverviewTracker kind="project" data={DATA} periodDays={30} />)
    expect(trendCalls.at(-1)).toEqual({ kind: 'project', id: 7, periodDays: 30 })
    expect(screen.getByText('Trễ')).toBeInTheDocument()
    expect(screen.getByText('40%')).toBeInTheDocument()          // % hoàn thành của dự án
  })

  it('on the people tab asks for the first person’s trend and shows their own numbers', () => {
    render(<WorkOverviewTracker kind="person" data={DATA} periodDays={7} />)
    expect(trendCalls.at(-1)).toEqual({ kind: 'person', id: 21, periodDays: 7 })
    expect(screen.getByText('9 ngày')).toBeInTheDocument()       // trễ lâu nhất của người đó
    expect(screen.getByText('40%')).toBeInTheDocument()          // tỉ lệ xong đúng hạn
  })

  it('says plainly when nothing happened in the period instead of drawing a flat chart', () => {
    buckets = [{ start: '2026-11-17', label: '17/11', created: 0, done_on_time: 0, done_late: 0, done_no_due: 0 }]
    render(<WorkOverviewTracker kind="project" data={DATA} periodDays={30} />)
    expect(screen.getByText('Không có việc mới giao hay việc xong nào trong 30 ngày qua.')).toBeInTheDocument()
  })

  it('explains an empty scope instead of calling the API with nothing selected', () => {
    render(<WorkOverviewTracker kind="project" data={{ ...DATA, projects: [] }} periodDays={30} />)
    expect(screen.getByText('Chưa có dự án nào trong phạm vi đang xem.')).toBeInTheDocument()
    //  Không có đối tượng nào thì không dựng biểu đồ diễn biến — không gọi API lần nào.
    expect(trendCalls).toHaveLength(0)
  })
})
