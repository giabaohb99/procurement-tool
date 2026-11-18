import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { WorkOverview, WorkOverviewTask } from '../hooks/use-work-overview'
import { WorkProjectAttentionCard } from './work-project-attention-card'

function task(id: number, title: string, extra: Partial<WorkOverviewTask> = {}): WorkOverviewTask {
  return { id, title, list_id: 19, list_name: 'Kế hoạch hệ agent', due_date: '', ...extra } as WorkOverviewTask
}

function overview(parts: Partial<WorkOverview>): WorkOverview {
  return {
    overdue_tasks: [],
    unassigned_tasks: [],
    no_due_tasks: [],
    task_overdue: 0,
    task_unassigned: 0,
    task_no_due: 0,
    ...parts,
  } as WorkOverview
}

function renderCard(data: WorkOverview | undefined) {
  return render(
    <MemoryRouter>
      <WorkProjectAttentionCard data={data} isLoading={false} />
    </MemoryRouter>,
  )
}

const pressed = () => screen.getAllByRole('button').find((b) => b.getAttribute('aria-pressed') === 'true')

describe('WorkProjectAttentionCard (duoc-CR-782)', () => {
  it('opens the first group that has tasks instead of an empty "no overdue" message', () => {
    renderCard(overview({ no_due_tasks: [task(1, 'Viết kịch bản')], task_no_due: 1 }))
    expect(pressed()).toHaveTextContent('Chưa hạn')
    expect(screen.getByText('Viết kịch bản')).toBeInTheDocument()
  })

  it('falls back to the overdue group with its good-news message when nothing needs attention', () => {
    renderCard(overview({}))
    expect(pressed()).toHaveTextContent('Quá hạn')
    expect(screen.getByText('Không có việc nào quá hạn.')).toBeInTheDocument()
  })

  it('switches groups on click and shows each group count, including zero', () => {
    renderCard(
      overview({
        overdue_tasks: [task(1, 'Việc trễ', { due_date: '2026-11-01', overdue_days: 17 })],
        task_overdue: 1,
        unassigned_tasks: [task(2, 'Việc chưa nhận')],
        task_unassigned: 3,
      }),
    )
    expect(screen.getByText('Việc trễ')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Chưa nhận/ }))
    expect(screen.getByText('Việc chưa nhận')).toBeInTheDocument()
    //  Tổng 3 mà chỉ có 1 dòng: phải nói ra là còn nữa, cắt im lặng là người xem tưởng đã thấy hết.
    expect(screen.getByText(/Còn 2 việc nữa/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /0\s*Chưa hạn/ })).toBeInTheDocument()
  })

  it('drops the repeated project name and does not start the sub line with a separator', () => {
    renderCard(overview({ overdue_tasks: [task(1, 'Việc trễ', { due_date: '2026-11-01' })], task_overdue: 1 }))
    expect(screen.queryByText(/Kế hoạch hệ agent/)).not.toBeInTheDocument()
    expect(screen.getByText(/hạn 01\/11\/2026/).parentElement?.textContent?.startsWith(' · ')).toBe(false)
  })

  it('survives data not loaded yet', () => {
    renderCard(undefined)
    expect(screen.getByText('Không có việc nào quá hạn.')).toBeInTheDocument()
  })
})
