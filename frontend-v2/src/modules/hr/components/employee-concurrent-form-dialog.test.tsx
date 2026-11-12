import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Department, DepartmentOfCompany } from '../types/department'
import type { Employee } from '../types/employee'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
import { EmployeeConcurrentFormDialog } from './employee-concurrent-form-dialog'

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAny: () => true }),
}))
vi.mock('../hooks/use-companies', () => ({
  useCompanies: () => ({
    data: { items: [{ id: 10, name: 'DEGO A' }, { id: 11, name: 'DEGO B' }] },
  }),
}))

function dept(id: number, name: string, companyId: number): Department {
  return { id, code: '', name, issue_code: '', kind: 1, company_id: companyId, parent: 0, manager_id: 0, is_active: true }
}
const DEPARTMENTS = [dept(1, 'Kế toán chung', 0), dept(2, 'Kinh doanh A', 10), dept(3, 'Kho B', 11), dept(4, 'Nhà máy C', 12)]
const PAIRS: Record<number, DepartmentOfCompany[]> = {
  11: [{ department_id: 4, department_name: 'Nhà máy C', department_code: '', company_id: 11, company_name: 'DEGO B' }],
}
vi.mock('../hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: DEPARTMENTS } }),
  useDepartmentsByCompanies: (ids: number[]) => ({ data: ids.flatMap((id) => PAIRS[id] ?? []) }),
}))
vi.mock('../hooks/use-job-positions', () => ({
  useJobPositions: () => ({ data: { items: [{ id: 30, name: 'Phó phòng' }] } }),
}))

const mutateAsync = vi.fn()
vi.mock('../hooks/use-employee-concurrents', () => ({
  useSaveEmployeeConcurrent: () => ({ mutateAsync, isPending: false }),
}))

const employee = { id: 1, company_id: 10, department_id: 2 } as Employee

function existing(overrides: Partial<EmployeeConcurrent> = {}): EmployeeConcurrent {
  return {
    id: 50,
    employee_id: 1,
    company_id: 11,
    company_name: 'DEGO B',
    department_id: 3,
    department_name: 'Kho B',
    position_id: 30,
    position_label: 'Phó phòng',
    from_date: '2026-11-01',
    to_date: null,
    decision_no: 'QĐ-7',
    decision_date: null,
    note: '',
    counts_scope: true,
    work_history_id: 0,
    status: 2,
    status_label: 'Đang hiệu lực',
    file_count: 0,
    ...overrides,
  }
}

function renderDialog(row: EmployeeConcurrent | null, outerSubmit = vi.fn()) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <form
        onSubmit={(event) => {
          event.preventDefault()
          outerSubmit()
        }}
      >
        <EmployeeConcurrentFormDialog open onOpenChange={vi.fn()} employee={employee} row={row} canOpenFiles={false} />
      </form>
    </QueryClientProvider>,
  )
  return { outerSubmit }
}

async function openCombobox(label: RegExp) {
  const trigger = screen.getAllByRole('combobox').find((el) => label.test(el.textContent ?? ''))
  if (!trigger) throw new Error(`combobox ${label} not found`)
  await userEvent.click(trigger)
}

beforeEach(() => {
  mutateAsync.mockReset()
})

describe('EmployeeConcurrentFormDialog', () => {
  it('department field is locked until a company is chosen', () => {
    renderDialog(null)
    const dept = screen.getAllByRole('combobox').find((el) => /Chọn công ty trước/.test(el.textContent ?? ''))
    expect(dept).toBeDisabled()
  })

  it('department list follows the chosen company: own + shared + mapped, never another company private one', async () => {
    renderDialog(existing())
    await openCombobox(/Kho B/)
    //  Công ty B (11): phòng riêng "Kho B", phòng dùng chung, và "Nhà máy C" (nhà ở công ty C, phục vụ B qua ánh xạ).
    expect(await screen.findByText('Kế toán chung')).toBeInTheDocument()
    expect(screen.getByText('Nhà máy C')).toBeInTheDocument()
    expect(screen.queryByText('Kinh doanh A')).not.toBeInTheDocument()
  })

  it('editing a row sends PATCH with the row id and the full payload, nulls for empty dates', async () => {
    mutateAsync.mockResolvedValue({ item: existing() })
    renderDialog(existing())
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(mutateAsync.mock.calls[0][0]).toEqual({
      id: 50,
      payload: {
        company_id: 11,
        department_id: 3,
        position_id: 30,
        from_date: '2026-11-01',
        to_date: null,
        decision_no: 'QĐ-7',
        decision_date: null,
        note: '',
        counts_scope: true,
      },
    })
  })

  it('saving never submits the outer profile form (trap: nested dialog inside the profile <form>)', async () => {
    mutateAsync.mockResolvedValue({ item: existing() })
    const { outerSubmit } = renderDialog(existing())
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled())
    expect(outerSubmit).not.toHaveBeenCalled()
  })

  it('pressing Enter in the decision number field does not submit the outer profile form', async () => {
    mutateAsync.mockResolvedValue({ item: existing() })
    const { outerSubmit } = renderDialog(existing())
    const input = screen.getByDisplayValue('QĐ-7')
    await userEvent.type(input, '{Enter}')
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(outerSubmit).not.toHaveBeenCalled()
  })

  it('double submit in the same tick sends ONE request (ref guard, not disabled state)', async () => {
    let resolve: (v: unknown) => void = () => {}
    mutateAsync.mockImplementation(() => new Promise((r) => (resolve = r)))
    renderDialog(existing())
    const save = screen.getByRole('button', { name: 'Lưu' })
    const formEl = save.closest('form') as HTMLFormElement
    fireEvent.submit(formEl)
    fireEvent.submit(formEl)
    fireEvent.submit(formEl)
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    resolve({ item: existing() })
    await new Promise((r) => setTimeout(r, 0))
    expect(mutateAsync).toHaveBeenCalledTimes(1)
  })

  it('missing company / department / start date blocks the request with field messages', async () => {
    renderDialog(null)
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText('Chọn phòng ban')).toBeInTheDocument()
    //  "Chọn công ty" vừa là chữ gợi ý của ô vừa là câu lỗi — có lỗi thì xuất hiện hai lần.
    expect(screen.getAllByText('Chọn công ty')).toHaveLength(2)
    expect(screen.getByText('Chọn từ ngày')).toBeInTheDocument()
    expect(mutateAsync).not.toHaveBeenCalled()
  })

  it('end date before start date is rejected client-side', async () => {
    renderDialog(existing({ to_date: '2026-10-01' }))
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText('Đến ngày phải sau hoặc bằng từ ngày')).toBeInTheDocument()
    expect(mutateAsync).not.toHaveBeenCalled()
  })

  it('scope switch is on by default for a new row and explains what it opens', () => {
    renderDialog(null)
    expect(screen.getByRole('switch')).toBeChecked()
    expect(screen.getByText(/thấy dữ liệu đúng phòng này ở công ty này/)).toBeInTheDocument()
  })
})
