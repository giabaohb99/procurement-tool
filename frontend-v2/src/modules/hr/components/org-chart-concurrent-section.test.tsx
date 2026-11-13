import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { ConcurrentMember } from '../types/concurrent-member'
import type { OrgChartConcurrentGroup } from '../utils/org-chart-forest'
import { OrgChartConcurrentSection } from './org-chart-concurrent-section'

function member(id: number, over: Partial<ConcurrentMember> = {}): ConcurrentMember {
  return {
    id,
    employee_id: 100 + id,
    kind: 1,
    kind_label: 'Phòng ban',
    code: `K${id}`,
    full_name: `Người kiêm ${id}`,
    position_label: 'Phó phòng',
    company_id: 2,
    company_name: 'Công ty B',
    department_id: 7,
    department_name: 'Phòng Kế toán',
    from_date: '2026-09-01',
    to_date: '2026-12-31',
    status: 2,
    status_label: 'Đang hiệu lực',
    counts_scope: true,
    primary_company_id: 1,
    primary_company_name: 'Công ty A',
    primary_department_id: 3,
    primary_department_name: 'Phòng Thu mua',
    can_open: true,
    ...over,
  }
}

function group(members: ConcurrentMember[]): OrgChartConcurrentGroup {
  return { key: 'd|7|2', kind: 1, departmentName: 'Phòng Kế toán', companyName: 'Công ty B', members }
}

function renderSection(groups: OrgChartConcurrentGroup[], truncated = false) {
  return render(
    <MemoryRouter>
      <OrgChartConcurrentSection groups={groups} truncated={truncated} />
    </MemoryRouter>,
  )
}

describe('OrgChartConcurrentSection', () => {
  it('renders nothing for an empty list so ordinary charts are unchanged', () => {
    const { container } = renderSection([])
    expect(container).toBeEmptyDOMElement()
  })

  it('shows each person under their concurrent place with the Kiêm nhiệm badge and position', () => {
    renderSection([group([member(1), member(2, { position_label: '' })])])
    expect(screen.getByText('Phòng Kế toán — Công ty B')).toBeInTheDocument()
    expect(screen.getByText('Người kiêm 1')).toBeInTheDocument()
    expect(screen.getByText('Người kiêm 2')).toBeInTheDocument()
    expect(screen.getAllByText('Kiêm nhiệm')).toHaveLength(2)
    expect(screen.getAllByText('Phó phòng')).toHaveLength(1)
  })

  it('reveals the primary department + company and a profile link on click, one card at a time', async () => {
    const user = userEvent.setup()
    renderSection([group([member(1), member(2)])])
    expect(screen.queryByText(/Phòng Thu mua — Công ty A/)).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Người kiêm 1/ }))
    expect(screen.getByText(/Phòng Thu mua — Công ty A/)).toBeInTheDocument()
    expect(screen.getByText('01/09/2026 – 31/12/2026')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Mở hồ sơ' })).toHaveAttribute('href', '/hr/employees/101')

    //  Mở thẻ thứ hai thì thẻ thứ nhất đóng — không chồng hai khung chi tiết lên nhau.
    await user.click(screen.getByRole('button', { name: /Người kiêm 2/ }))
    expect(screen.getAllByRole('link', { name: 'Mở hồ sơ' })).toHaveLength(1)
    expect(screen.getByRole('link', { name: 'Mở hồ sơ' })).toHaveAttribute('href', '/hr/employees/102')

    //  Bấm lại cùng thẻ thì đóng.
    await user.click(screen.getByRole('button', { name: /Người kiêm 2/ }))
    expect(screen.queryByRole('link', { name: 'Mở hồ sơ' })).not.toBeInTheDocument()
  })

  it('does not offer a profile link when the viewer cannot open the profile, and says why', async () => {
    const user = userEvent.setup()
    renderSection([group([member(1, { can_open: false })])])
    await user.click(screen.getByRole('button', { name: /Người kiêm 1/ }))
    expect(screen.queryByRole('link', { name: 'Mở hồ sơ' })).not.toBeInTheDocument()
    expect(screen.getByText(/không mở được hồ sơ/)).toBeInTheDocument()
  })

  it('still renders a person whose primary place and name parts are missing (blank strings from the backend)', async () => {
    const user = userEvent.setup()
    renderSection([
      { key: 'd|0|0', kind: 1, departmentName: '', companyName: '', members: [member(1, { primary_department_name: '', primary_company_name: '', position_label: '' })] },
    ])
    expect(screen.getByText('Phòng không rõ')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Người kiêm 1/ }))
    expect(screen.getByText('Chưa rõ phòng chính')).toBeInTheDocument()
  })

  it('shows a note only when the backend truncated the list', () => {
    renderSection([group([member(1)])], true)
    expect(screen.getByRole('note')).toHaveTextContent(/chỉ hiện phần đầu danh sách kiêm nhiệm/)
  })

  it('shows no note for a complete list', () => {
    renderSection([group([member(1)])])
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
  })

  it('a Công ty group is titled "Kiêm nhiệm tại ..." with no room (duoc-CR-756)', () => {
    renderSection([
      {
        key: 'c|2',
        kind: 2,
        departmentName: '',
        companyName: 'Công ty B',
        members: [member(5, { kind: 2, kind_label: 'Công ty', department_id: 0, department_name: '' })],
      },
    ])
    expect(screen.getByText('Kiêm nhiệm tại Công ty B')).toBeInTheDocument()
    expect(screen.getByText('Người kiêm 5')).toBeInTheDocument()
  })
})
