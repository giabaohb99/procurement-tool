import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { EmployeeConcurrent } from '../types/employee-concurrent'
import { EmployeeCompanyChangeConcurrentDialog } from './employee-company-change-concurrent-dialog'

const TODAY = '2026-11-12'

function row(id: number, name: string, fromDate: string): EmployeeConcurrent {
  return {
    id,
    employee_id: 1,
    company_id: 10,
    company_name: 'DEGO A',
    department_id: id,
    department_name: name,
    position_id: 0,
    position_label: '',
    from_date: fromDate,
    to_date: null,
    decision_no: '',
    decision_date: null,
    note: '',
    counts_scope: true,
    work_history_id: 0,
    status: fromDate > TODAY ? 1 : 2,
    status_label: '',
    file_count: 0,
  }
}

const ROWS = [row(7, 'Kế toán', '2026-01-01'), row(8, 'Kho', '2026-12-01')]

function renderDialog(onConfirm = vi.fn()) {
  render(
    <EmployeeCompanyChangeConcurrentDialog
      open
      onOpenChange={vi.fn()}
      oldCompanyName="DEGO A"
      newCompanyName="DEGO B"
      rows={ROWS}
      today={TODAY}
      onConfirm={onConfirm}
    />,
  )
  return onConfirm
}

describe('EmployeeCompanyChangeConcurrentDialog', () => {
  it('names both companies and warns that the unstarted row will be deleted', () => {
    renderDialog()
    expect(screen.getAllByText('DEGO A').length).toBeGreaterThan(0)
    expect(screen.getByText('DEGO B')).toBeInTheDocument()
    expect(screen.getAllByText(/sẽ bị xóa nếu không giữ/)).toHaveLength(1)
  })

  it('default (nothing ticked) ends every row', async () => {
    const onConfirm = renderDialog()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu, kết thúc 2 dòng' }))
    expect(onConfirm).toHaveBeenCalledWith({ end_old_company_concurrent: true, keep_concurrent_ids: [] })
  })

  it('ticking one row keeps exactly that id and hides its deletion warning', async () => {
    const onConfirm = renderDialog()
    await userEvent.click(screen.getByLabelText(/Giữ: Kho/))
    expect(screen.queryByText(/sẽ bị xóa nếu không giữ/)).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu, kết thúc 1 dòng' }))
    expect(onConfirm).toHaveBeenCalledWith({ end_old_company_concurrent: true, keep_concurrent_ids: [8] })
  })

  it('ticking every row sends "keep all" (false), not a full id list', async () => {
    const onConfirm = renderDialog()
    await userEvent.click(screen.getByLabelText(/Giữ: Kế toán/))
    await userEvent.click(screen.getByLabelText(/Giữ: Kho/))
    await userEvent.click(screen.getByRole('button', { name: 'Lưu, giữ tất cả' }))
    expect(onConfirm).toHaveBeenCalledWith({ end_old_company_concurrent: false, keep_concurrent_ids: [] })
  })

  describe('default "today" (no prop) follows Vietnam time like backend vn_today()', () => {
    afterEach(() => vi.useRealTimers())

    it('at 01:30 on 13/11 in Vietnam (18:30 UTC on 12/11) a row starting 12/11 has already started', () => {
      vi.useFakeTimers({ toFake: ['Date'] })
      vi.setSystemTime(new Date('2026-11-12T18:30:00Z'))
      render(
        <EmployeeCompanyChangeConcurrentDialog
          open
          onOpenChange={vi.fn()}
          oldCompanyName="DEGO A"
          newCompanyName="DEGO B"
          rows={[row(9, 'Mua hàng', '2026-11-12')]}
          onConfirm={vi.fn()}
        />,
      )
      expect(screen.queryByText(/sẽ bị xóa nếu không giữ/)).not.toBeInTheDocument()
    })

    it('control: a row starting on the Vietnam "today" is still warned as unstarted', () => {
      vi.useFakeTimers({ toFake: ['Date'] })
      vi.setSystemTime(new Date('2026-11-12T18:30:00Z'))
      render(
        <EmployeeCompanyChangeConcurrentDialog
          open
          onOpenChange={vi.fn()}
          oldCompanyName="DEGO A"
          newCompanyName="DEGO B"
          rows={[row(9, 'Mua hàng', '2026-11-13')]}
          onConfirm={vi.fn()}
        />,
      )
      expect(screen.getAllByText(/sẽ bị xóa nếu không giữ/)).toHaveLength(1)
    })
  })
})
