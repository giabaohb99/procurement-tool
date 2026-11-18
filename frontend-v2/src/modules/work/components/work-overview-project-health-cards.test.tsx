import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { WorkOverviewProject } from '../hooks/use-work-overview'
import { WorkOverviewProjectHealthCards } from './work-overview-project-health-cards'

const LABEL: Record<number, string> = { 0: 'Chưa có việc', 1: 'Đúng tiến độ', 2: 'Có rủi ro', 3: 'Trễ' }

function project(id: number, name: string, health: number): WorkOverviewProject {
  return {
    list_id: id, name, color: '', total: health ? 4 : 0, done: 1, open: health ? 3 : 0, overdue: health >= 2 ? 1 : 0,
    done_in_period: 0, progress: health ? 25 : 0, last_due: '', health, health_label: LABEL[health], can_open: true,
  }
}

//  Tình huống anh Được hỏi: rất nhiều dự án. 25 có việc (5 trễ, 5 rủi ro, 15 đúng tiến độ) + 12 dự án trống.
const MANY: WorkOverviewProject[] = [
  ...Array.from({ length: 5 }, (_, i) => project(i + 1, `Dự án trễ ${i + 1}`, 3)),
  ...Array.from({ length: 5 }, (_, i) => project(i + 10, `Dự án rủi ro ${i + 1}`, 2)),
  ...Array.from({ length: 15 }, (_, i) => project(i + 20, `Kho chi nhánh ${i + 1}`, 1)),
  ...Array.from({ length: 12 }, (_, i) => project(i + 100, `Trống ${i + 1}`, 0)),
]

function renderCards(projects = MANY) {
  return render(
    <MemoryRouter>
      <WorkOverviewProjectHealthCards projects={projects} isLoading={false} isError={false} />
    </MemoryRouter>,
  )
}

const cardCount = () => screen.queryAllByText(/việc đã xong$/).length

describe('WorkOverviewProjectHealthCards with many projects (duoc-CR-782)', () => {
  it('shows only the first 9 cards and offers to show more, counting what is left', () => {
    renderCards()
    expect(cardCount()).toBe(9)
    fireEvent.click(screen.getByRole('button', { name: /Xem thêm 9 dự án \(còn 16\)/ }))
    expect(cardCount()).toBe(18)
    fireEvent.click(screen.getByRole('button', { name: /Xem thêm 7 dự án \(còn 7\)/ }))
    expect(cardCount()).toBe(25)
    expect(screen.queryByRole('button', { name: /Xem thêm/ })).not.toBeInTheDocument()
  })

  it('filters by health with counts and starts again from 9 after changing the filter', () => {
    renderCards()
    expect(screen.getByRole('button', { name: 'Trễ (5)' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Đúng tiến độ (15)' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Trễ (5)' }))
    expect(cardCount()).toBe(5)
    fireEvent.click(screen.getByRole('button', { name: 'Đúng tiến độ (15)' }))
    expect(cardCount()).toBe(9)
  })

  it('searches without diacritics and says so when nothing matches', () => {
    renderCards()
    fireEvent.change(screen.getByLabelText('Tìm dự án'), { target: { value: 'kho chi nhanh 1' } })
    //  "1", "10".."15" đều chứa "kho chi nhanh 1".
    expect(cardCount()).toBe(7)
    fireEvent.change(screen.getByLabelText('Tìm dự án'), { target: { value: 'khong co' } })
    expect(screen.getByText('Không có dự án nào khớp bộ lọc.')).toBeInTheDocument()
  })

  it('lists at most 10 empty project names and counts the rest', () => {
    renderCards()
    expect(screen.getByText('12 dự án chưa có việc:')).toBeInTheDocument()
    expect(screen.getByText(/và 2 dự án khác\./)).toBeInTheDocument()
  })
})
