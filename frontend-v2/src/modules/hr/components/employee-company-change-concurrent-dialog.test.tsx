import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { CONCURRENT_KIND_COMPANY, CONCURRENT_KIND_DEPARTMENT, type EmployeeConcurrent } from '../types/employee-concurrent'
import type { CompanyChangeConcurrentChoice } from '../utils/company-change-concurrent-choice'
import { EmployeeCompanyChangeConcurrentDialog } from './employee-company-change-concurrent-dialog'

const TODAY = '2026-11-12'

function departmentRow(id: number, name: string, fromDate: string): EmployeeConcurrent {
  return {
    id,
    employee_id: 1,
    kind: CONCURRENT_KIND_DEPARTMENT,
    kind_label: 'Phòng ban',
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

/** Dòng loại Công ty trùng công ty MỚI — cũng kết thúc khi đổi pháp nhân sang đó. */
function companyRow(id: number, companyName: string): EmployeeConcurrent {
  return {
    ...departmentRow(id, '', '2026-01-01'),
    kind: CONCURRENT_KIND_COMPANY,
    kind_label: 'Công ty',
    company_id: 11,
    company_name: companyName,
    department_id: 0,
  }
}

const ROWS = [departmentRow(7, 'Kế toán', '2026-01-01'), departmentRow(8, 'Kho', '2026-12-01'), companyRow(9, 'DEGO B')]

function renderDialog({
  rows = ROWS,
  oldCompanyKept = false,
  onConfirm = vi.fn<(choice: CompanyChangeConcurrentChoice) => void>(),
}: {
  rows?: EmployeeConcurrent[]
  oldCompanyKept?: boolean
  onConfirm?: ReturnType<typeof vi.fn<(choice: CompanyChangeConcurrentChoice) => void>>
} = {}) {
  render(
    <EmployeeCompanyChangeConcurrentDialog
      open
      onOpenChange={vi.fn()}
      oldCompanyName="DEGO A"
      newCompanyName="DEGO B"
      rows={rows}
      oldCompanyKept={oldCompanyKept}
      today={TODAY}
      onConfirm={onConfirm}
    />,
  )
  return onConfirm
}

describe('EmployeeCompanyChangeConcurrentDialog (duoc-CR-756)', () => {
  it('lists every ending row with its kind and place, warns once for the unstarted one, and has no per-row checkbox', () => {
    renderDialog()
    expect(screen.getByText('Phòng ban: Kế toán')).toBeInTheDocument()
    expect(screen.getByText('Phòng ban: Kho')).toBeInTheDocument()
    expect(screen.getByText('Công ty: DEGO B')).toBeInTheDocument()
    expect(screen.getAllByText(/Chưa bắt đầu — sẽ bị xóa/)).toHaveLength(1)
    //  CR-755 cho tick giữ TỪNG dòng; mô hình mới chỉ còn MỘT câu hỏi.
    expect(screen.getAllByRole('checkbox')).toHaveLength(1)
  })

  it('default (box unticked) sends keep_old_company_concurrent = false', async () => {
    const onConfirm = renderDialog()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu, kết thúc 3 dòng' }))
    expect(onConfirm).toHaveBeenCalledWith({ keep_old_company_concurrent: false })
  })

  it('ticking "Vẫn kiêm nhiệm ở công ty cũ" sends keep_old_company_concurrent = true and nothing else', async () => {
    const onConfirm = renderDialog()
    await userEvent.click(screen.getByLabelText(/Vẫn kiêm nhiệm ở công ty cũ/))
    await userEvent.click(screen.getByRole('button', { name: 'Lưu, kết thúc 3 dòng' }))
    expect(onConfirm).toHaveBeenCalledTimes(1)
    expect(onConfirm.mock.calls[0][0]).toEqual({ keep_old_company_concurrent: true })
  })

  it('no row ends: still asks the one question, button is a plain "Lưu"', async () => {
    const onConfirm = renderDialog({ rows: [] })
    expect(screen.getByText(/Không có dòng kiêm nhiệm nào phải kết thúc/)).toBeInTheDocument()
    await userEvent.click(screen.getByLabelText(/Vẫn kiêm nhiệm ở công ty cũ/))
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(onConfirm).toHaveBeenCalledWith({ keep_old_company_concurrent: true })
  })

  it('already has a Công ty row at the old company: no checkbox, says so, never asks backend to add a duplicate', async () => {
    const onConfirm = renderDialog({ oldCompanyKept: true })
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
    expect(screen.getByText(/đã có dòng kiêm nhiệm loại Công ty ở/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu, kết thúc 3 dòng' }))
    expect(onConfirm).toHaveBeenCalledWith({ keep_old_company_concurrent: false })
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
          rows={[departmentRow(9, 'Mua hàng', '2026-11-12')]}
          onConfirm={vi.fn()}
        />,
      )
      expect(screen.queryByText(/Chưa bắt đầu — sẽ bị xóa/)).not.toBeInTheDocument()
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
          rows={[departmentRow(9, 'Mua hàng', '2026-11-13')]}
          onConfirm={vi.fn()}
        />,
      )
      expect(screen.getAllByText(/Chưa bắt đầu — sẽ bị xóa/)).toHaveLength(1)
    })
  })
})
