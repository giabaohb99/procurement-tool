import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { WorkOverview } from '../hooks/use-work-overview'
import {
  WorkOverviewPeopleChart,
  WorkOverviewProjectChart,
  WorkOverviewStatusChart,
} from './work-overview-charts'

function overview(patch: Partial<WorkOverview>): WorkOverview {
  return {
    scope: 'all',
    period_days: 30,
    project_total: 1,
    project_archived: 0,
    task_open: 0,
    task_done: 0,
    task_cancelled: 0,
    task_overdue: 0,
    task_due_soon: 0,
    task_mine: 0,
    task_created_in_period: 0,
    task_done_in_period: 0,
    on_time_rate: null,
    task_unassigned: 0,
    task_no_due: 0,
    by_project: [],
    by_priority: [],
    overdue_tasks: [],
    my_tasks: [],
    unassigned_tasks: [],
    no_due_tasks: [],
    people: [],
    projects: [],
    ...patch,
  }
}

/** Số của một dòng chú giải vòng tình trạng (dòng chú giải là HTML nên đọc được dù jsdom không vẽ SVG). */
function legendValue(label: string): string {
  const row = screen.getByText(label).closest('li')
  if (!row) throw new Error(`không thấy dòng chú giải ${label}`)
  return within(row).getAllByText(/^\d/)[0].textContent ?? ''
}

describe('WorkOverview charts (duoc-CR-782)', () => {
  it('splits open work into four parts that add up to the open count', () => {
    render(
      <WorkOverviewStatusChart data={overview({ task_open: 22, task_overdue: 4, task_due_soon: 3, task_no_due: 12 })} isLoading={false} />,
    )
    expect(legendValue('Quá hạn')).toBe('4')
    expect(legendValue('Đến hạn trong 7 ngày')).toBe('3')
    expect(legendValue('Còn hạn')).toBe('3')          // 22 − 4 − 3 − 12
    expect(legendValue('Chưa đặt hạn')).toBe('12')
  })

  it('never shows a negative "still on time" slice when the parts overshoot the open count', () => {
    //  Dữ liệu lệch (đếm ở hai lúc khác nhau) không được vẽ ra một lát âm.
    render(
      <WorkOverviewStatusChart data={overview({ task_open: 2, task_overdue: 2, task_due_soon: 1, task_no_due: 1 })} isLoading={false} />,
    )
    expect(legendValue('Còn hạn')).toBe('0')
  })

  it('says why each chart is empty instead of drawing nothing', () => {
    const empty = overview({})
    render(
      <>
        <WorkOverviewStatusChart data={empty} isLoading={false} />
        <WorkOverviewProjectChart data={empty} periodDays={7} isLoading={false} />
        <WorkOverviewPeopleChart data={empty} periodDays={7} isLoading={false} />
      </>,
    )
    expect(screen.getByText('Không có việc nào đang mở.')).toBeInTheDocument()
    expect(screen.getByText('Chưa dự án nào có việc.')).toBeInTheDocument()
    expect(screen.getByText('Chưa có việc nào được giao cho ai.')).toBeInTheDocument()
    //  Kỳ đang chọn phải hiện trong lời mô tả đường "xong trong kỳ".
    expect(screen.getAllByText(/Đường: việc xong trong 7 ngày\./)).toHaveLength(2)
  })
})
