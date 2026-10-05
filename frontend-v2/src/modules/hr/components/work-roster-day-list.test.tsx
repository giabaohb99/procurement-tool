import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { ROSTER_DAYS, rosterCell, rosterItem, rosterLeave } from './work-roster-fixture'
import { WorkRosterDayList } from './work-roster-day-list'

const IT = { id: 4, name: 'IT' }
const DAY = '2026-10-05'

function renderList(items: Parameters<typeof WorkRosterDayList>[0]['items'], selectedISO = DAY, onSelect = vi.fn()) {
  render(
    <MemoryRouter>
      <WorkRosterDayList days={ROSTER_DAYS} items={items} selectedISO={selectedISO} onSelect={onSelect} todayISO={DAY} />
    </MemoryRouter>,
  )
  return onSelect
}

describe('WorkRosterDayList', () => {
  it('splits people into working (including half days) and off (leave, scheduled off)', () => {
    renderList([
      rosterItem(1, 'An', IT, [rosterCell(DAY)]),
      rosterItem(2, 'Bình', IT, [rosterCell(DAY, { leave: rosterLeave({ afternoon: false }) })]),
      rosterItem(3, 'Chi', IT, [rosterCell(DAY, { leave: rosterLeave() })]),
      rosterItem(4, 'Dũng', IT, [rosterCell(DAY, { work_kind: 1 })]),
    ])
    const working = screen.getByRole('region', { name: 'Đi làm' })
    const off = screen.getByRole('region', { name: 'Nghỉ' })
    expect(within(working).getByText('An')).toBeInTheDocument()
    expect(within(working).getByText('Bình')).toBeInTheDocument()
    expect(within(off).getByText('Chi')).toBeInTheDocument()
    expect(within(off).getByText('Dũng')).toBeInTheDocument()
    expect(within(off).getByText('Phép năm')).toBeInTheDocument()
  })

  it('labels a pending request as pending and links to it', () => {
    renderList([rosterItem(3, 'Chi', IT, [rosterCell(DAY, { leave: rosterLeave({ is_approved: false, request_id: 9 }) })])])
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '/hr/leave-requests/9')
    expect(link).toHaveTextContent('Phép năm · chờ duyệt')
  })

  it('puts an employee without a cell for the selected day in neither group', () => {
    renderList([rosterItem(5, 'Em', IT, [])])
    expect(screen.queryByText('Em')).toBeNull()
    expect(screen.getByText('Không ai đi làm.')).toBeInTheDocument()
    expect(screen.getByText('Không ai nghỉ.')).toBeInTheDocument()
  })

  it('calls onSelect with the clicked date and marks the selected chip aria-pressed', () => {
    const onSelect = renderList([rosterItem(1, 'An', IT, [rosterCell(DAY)])])
    expect(screen.getByRole('button', { name: /T2\s*5/ })).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(screen.getByRole('button', { name: /CN\s*11/ }))
    expect(onSelect).toHaveBeenCalledWith('2026-10-11')
  })

  it('states the holiday and puts everyone in the off group', () => {
    renderList(
      [rosterItem(1, 'An', IT, [rosterCell('2026-10-06', { is_holiday: true, holiday_name: 'Nghỉ bù' })])],
      '2026-10-06',
    )
    expect(screen.getByText('Ngày lễ: Nghỉ bù')).toBeInTheDocument()
    expect(within(screen.getByRole('region', { name: 'Nghỉ' })).getByText('An')).toBeInTheDocument()
  })

  //  Lễ RIÊNG của một pháp nhân: biểu ngữ (chỉ lễ chung) không được nói «Ngày lễ», nhưng dòng của người đó phải nói.
  it('shows a company-only holiday on that employee row and not in the shared banner', () => {
    renderList(
      [
        rosterItem(1, 'An', IT, [rosterCell(DAY, { is_holiday: true, holiday_name: 'Lễ riêng' })]),
        rosterItem(2, 'Bình', IT, [rosterCell(DAY)]),
      ],
      DAY,
    )
    expect(screen.queryByText(/^Ngày lễ:/)).toBeNull()
    expect(within(screen.getByRole('region', { name: 'Nghỉ' })).getByTitle('Ngày lễ: Lễ riêng')).toBeInTheDocument()
    expect(within(screen.getByRole('region', { name: 'Đi làm' })).getByText('Bình')).toBeInTheDocument()
  })
})
