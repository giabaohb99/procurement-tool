import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import type { LeaveBalanceMatrixRow } from '../api/leave-balance-matrix-api'
import { accrualFixture } from './leave-accrual-fixture'
import { buildLeaveBalanceMatrixColumns } from './leave-balance-matrix-columns'

const COLUMNS = buildLeaveBalanceMatrixColumns([
  { leave_type_id: 3, name: 'Phép năm' },
  { leave_type_id: 7, name: 'Nghỉ bù' },
])

function cellOf(key: string) {
  const found = COLUMNS.find((c) => c.key === key)
  if (!found) throw new Error(`Không có cột "${key}"`)
  return found
}

function row(overrides: Partial<LeaveBalanceMatrixRow> = {}): LeaveBalanceMatrixRow {
  return {
    employee_id: 11,
    code: 'NSU001',
    name: 'Trần An',
    department_name: 'Kế toán',
    cells: { '3': 2, '7': 0 },
    total: 2,
    ...overrides,
  }
}

describe('matrix columns: accrual status (duoc-CR-762)', () => {
  it('puts an ICON next to the name (200px column) and moves the words into the accessible name + hover hint', async () => {
    const { rerender, container } = render(
      <>{cellOf('name').cell(row({ accrual: { '3': accrualFixture(3) } }))}</>,
    )
    const badge = screen.getByLabelText(/^Chưa có HĐLĐ trên hệ thống\. Đang tính từ ngày vào làm/)
    //  Không chữ nào chen vào ô tên — chỉ biểu tượng.
    expect(container.textContent).toBe('Trần An')
    await userEvent.hover(badge)
    expect((await screen.findAllByText(/nhập hợp đồng lao động để tính đúng/)).length).toBeGreaterThan(0)

    rerender(<>{cellOf('name').cell(row({ accrual: { '3': accrualFixture(2) } }))}</>)
    expect(screen.getByLabelText('Đang thử việc — chưa tích')).toBeTruthy()
  })

  it('hideNoContract (option B) drops the missing-contract icon but keeps the probation one', () => {
    const hidden = buildLeaveBalanceMatrixColumns([{ leave_type_id: 3, name: 'Phép năm' }], true)
    const name = hidden.find((c) => c.key === 'name')
    if (!name) throw new Error('Không có cột "name"')
    const { rerender } = render(<>{name.cell(row({ accrual: { '3': accrualFixture(3) } }))}</>)
    expect(screen.queryByLabelText(/Chưa có HĐLĐ/)).toBeNull()
    rerender(<>{name.cell(row({ accrual: { '3': accrualFixture(2) } }))}</>)
    expect(screen.getByLabelText('Đang thử việc — chưa tích')).toBeTruthy()
  })

  it('no accrual map (legacy backend), empty map or accruing person: name only', () => {
    const cases: LeaveBalanceMatrixRow['accrual'][] = [
      undefined,
      {},
      { '3': { accrual_status: 1, accrual_start_date: '2026-02-01' } },
    ]
    for (const accrual of cases) {
      const { container, unmount } = render(<>{cellOf('name').cell(row({ accrual }))}</>)
      expect(container.textContent).toBe('Trần An')
      unmount()
    }
  })

  it('accruing cell keeps its number and shows "Tích từ dd/mm/yyyy" only on hover', async () => {
    render(<>{cellOf('lt-3').cell(row({ accrual: { '3': { accrual_status: 1, accrual_start_date: '2026-02-01' } } }))}</>)
    expect(screen.getByText('2')).toBeTruthy()
    expect(screen.queryByText(/Tích từ/)).toBeNull()
    await userEvent.hover(screen.getByText('2'))
    expect((await screen.findAllByText('Tích từ 01/02/2026')).length).toBeGreaterThan(0)
  })

  it('reads the accrual map by STRING key: another type column gets no hint', async () => {
    render(<>{cellOf('lt-7').cell(row({ accrual: { '3': { accrual_status: 1, accrual_start_date: '2026-02-01' } } }))}</>)
    await userEvent.hover(screen.getByText('0'))
    expect(screen.queryByText(/Tích từ/)).toBeNull()
  })
})
