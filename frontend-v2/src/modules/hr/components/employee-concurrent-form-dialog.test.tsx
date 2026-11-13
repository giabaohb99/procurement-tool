import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Department, DepartmentOfCompany } from '../types/department'
import type { Employee } from '../types/employee'
import {
  CONCURRENT_KIND_COMPANY,
  CONCURRENT_KIND_DEPARTMENT,
  type EmployeeConcurrent,
} from '../types/employee-concurrent'
import { EmployeeConcurrentFormDialog } from './employee-concurrent-form-dialog'

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAny: () => true }),
}))
vi.mock('../hooks/use-companies', () => ({
  useCompanies: () => ({
    data: { items: [{ id: 10, name: 'DEGO A' }, { id: 11, name: 'DEGO B' }, { id: 12, name: 'DEGO C' }] },
  }),
}))

function dept(id: number, name: string, companyId: number): Department {
  return { id, code: '', name, issue_code: '', kind: 1, company_id: companyId, parent: 0, manager_id: 0, is_active: true }
}
const DEPARTMENTS = [dept(1, 'Kế toán chung', 0), dept(2, 'Kinh doanh A', 10), dept(3, 'Kho B', 11), dept(4, 'Nhà máy C', 12)]
//  Công ty A (10) — công ty HIỆN TẠI của hồ sơ — được "Nhà máy C" (nhà ở công ty C) phục vụ qua `tab_department_company`.
const PAIRS: Record<number, DepartmentOfCompany[]> = {
  10: [{ department_id: 4, department_name: 'Nhà máy C', department_code: '', company_id: 10, company_name: 'DEGO A' }],
}
const byCompaniesCalls: number[][] = []
vi.mock('../hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: DEPARTMENTS } }),
  useDepartmentsByCompanies: (ids: number[]) => {
    byCompaniesCalls.push(ids)
    return { data: ids.flatMap((id) => PAIRS[id] ?? []) }
  },
}))
vi.mock('../hooks/use-job-positions', () => ({
  useJobPositions: () => ({ data: { items: [{ id: 30, name: 'Phó phòng' }] } }),
}))

//  Lịch bật ra của DatePicker phụ thuộc tháng HIỆN TẠI — thay bằng ô chữ `yyyy-mm-dd` để bài kiểm không đổi theo ngày chạy.
vi.mock('@/shared/ui/date-picker', () => ({
  DatePicker: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <input aria-label="Ô ngày" value={value} onChange={(event) => onChange(event.target.value)} />
  ),
}))

const mutateAsync = vi.fn()
vi.mock('../hooks/use-employee-concurrents', () => ({
  useSaveEmployeeConcurrent: () => ({ mutateAsync, isPending: false }),
}))

//  Hồ sơ: công ty hiện tại DEGO A (10), phòng chính "Kinh doanh A" (2).
const employee = { id: 1, company_id: 10, company_name: 'DEGO A', department_id: 2 } as Employee
const employeeNoCompany = { id: 1, company_id: 0, company_name: '', department_id: 0 } as Employee

function existing(overrides: Partial<EmployeeConcurrent> = {}): EmployeeConcurrent {
  return {
    id: 50,
    employee_id: 1,
    kind: CONCURRENT_KIND_DEPARTMENT,
    kind_label: 'Phòng ban',
    company_id: 10,
    company_name: 'DEGO A',
    department_id: 1,
    department_name: 'Kế toán chung',
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

function existingCompanyRow(overrides: Partial<EmployeeConcurrent> = {}): EmployeeConcurrent {
  return existing({
    kind: CONCURRENT_KIND_COMPANY,
    kind_label: 'Công ty',
    company_id: 11,
    company_name: 'DEGO B',
    department_id: 0,
    department_name: '',
    ...overrides,
  })
}

function renderDialog(
  row: EmployeeConcurrent | null,
  outerSubmit = vi.fn(),
  who: Employee = employee,
  canOpenFiles = false,
) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <form
        onSubmit={(event) => {
          event.preventDefault()
          outerSubmit()
        }}
      >
        <EmployeeConcurrentFormDialog open onOpenChange={vi.fn()} employee={who} row={row} canOpenFiles={canOpenFiles} />
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

async function pickOption(name: string) {
  await userEvent.click(await screen.findByText(name))
}

async function fillStartDate() {
  //  Ô ngày đầu tiên của hộp là Từ ngày (bản giả của DatePicker ở trên).
  fireEvent.change(screen.getAllByLabelText('Ô ngày')[0], { target: { value: '2026-11-01' } })
}

beforeEach(() => {
  mutateAsync.mockReset()
  byCompaniesCalls.length = 0
})

describe('EmployeeConcurrentFormDialog — chọn Loại trước (duoc-CR-756)', () => {
  it('a new row starts as Phòng ban: no company picker, the department hint names the current company', () => {
    renderDialog(null)
    expect(screen.getByRole('radio', { name: 'Phòng ban' })).toBeChecked()
    expect(screen.getByRole('radio', { name: 'Công ty' })).not.toBeChecked()
    //  Ô chọn chỉ còn Phòng ban + Chức vụ.
    expect(screen.getAllByRole('combobox')).toHaveLength(2)
    expect(screen.getByText('Chọn phòng của DEGO A')).toBeInTheDocument()
    expect(screen.queryByText('Chọn công ty')).not.toBeInTheDocument()
  })

  it('department list = only rooms serving the CURRENT company: own + shared + mapped, never another company private one, never the primary one', async () => {
    renderDialog(null)
    //  Bảng ánh xạ chỉ được hỏi cho công ty hiện tại — không còn theo công ty người dùng chọn.
    expect(byCompaniesCalls.every((ids) => ids.length === 1 && ids[0] === 10)).toBe(true)
    await openCombobox(/Chọn phòng của DEGO A/)
    expect(await screen.findByText('Kế toán chung')).toBeInTheDocument()
    expect(screen.getByText('Nhà máy C')).toBeInTheDocument()
    //  Phòng riêng của công ty B — chọn vào là 400 "không phục vụ công ty hiện tại".
    expect(screen.queryByText('Kho B')).not.toBeInTheDocument()
    //  Phòng chính của hồ sơ — backend chặn "trùng phòng chính".
    expect(screen.queryByText('Kinh doanh A')).not.toBeInTheDocument()
  })

  it('switching to Công ty swaps the department picker for a company picker that excludes the current company', async () => {
    renderDialog(null)
    await userEvent.click(screen.getByRole('radio', { name: 'Công ty' }))
    expect(screen.queryByText('Chọn phòng ban')).not.toBeInTheDocument()
    await openCombobox(/Chọn công ty/)
    expect(await screen.findByText('DEGO B')).toBeInTheDocument()
    expect(screen.getByText('DEGO C')).toBeInTheDocument()
    //  Kiêm nhiệm chính công ty mình — backend 400 "trùng công ty chính".
    expect(screen.queryByText('DEGO A')).not.toBeInTheDocument()
  })

  it('POST for Phòng ban sends kind + department_id and NO company_id (server fills the primary company)', async () => {
    mutateAsync.mockResolvedValue({ item: existing() })
    renderDialog(null)
    await openCombobox(/Chọn phòng của DEGO A/)
    await pickOption('Kế toán chung')
    await fillStartDate()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    const variables = mutateAsync.mock.calls[0][0]
    expect(variables.id).toBeUndefined()
    expect(variables.payload).toEqual({
      kind: CONCURRENT_KIND_DEPARTMENT,
      department_id: 1,
      position_id: 0,
      from_date: '2026-11-01',
      to_date: null,
      decision_no: '',
      decision_date: null,
      note: '',
      counts_scope: true,
    })
    expect('company_id' in variables.payload).toBe(false)
  })

  it('POST for Công ty sends kind + company_id and NO department_id', async () => {
    mutateAsync.mockResolvedValue({ item: existingCompanyRow() })
    renderDialog(null)
    await userEvent.click(screen.getByRole('radio', { name: 'Công ty' }))
    await openCombobox(/Chọn công ty/)
    await pickOption('DEGO B')
    await fillStartDate()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    const { payload } = mutateAsync.mock.calls[0][0]
    expect(payload.kind).toBe(CONCURRENT_KIND_COMPANY)
    expect(payload.company_id).toBe(11)
    expect('department_id' in payload).toBe(false)
  })

  it('a department picked before switching to Công ty is cleared, so coming back does not resurrect it', async () => {
    renderDialog(null)
    await openCombobox(/Chọn phòng của DEGO A/)
    await pickOption('Kế toán chung')
    await userEvent.click(screen.getByRole('radio', { name: 'Công ty' }))
    await userEvent.click(screen.getByRole('radio', { name: 'Phòng ban' }))
    expect(screen.getByText('Chọn phòng của DEGO A')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText('Chọn phòng ban')).toBeInTheDocument()
    expect(mutateAsync).not.toHaveBeenCalled()
  })

  it('Công ty without a company picked is blocked client-side with the field message', async () => {
    renderDialog(null)
    await userEvent.click(screen.getByRole('radio', { name: 'Công ty' }))
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    //  "Chọn công ty" vừa là chữ gợi ý của ô vừa là câu lỗi — có lỗi thì xuất hiện hai lần.
    expect(await screen.findAllByText('Chọn công ty')).toHaveLength(2)
    expect(screen.getByText('Chọn từ ngày')).toBeInTheDocument()
    expect(mutateAsync).not.toHaveBeenCalled()
  })
})

describe('EmployeeConcurrentFormDialog — sửa dòng', () => {
  it('editing locks the kind (bar disabled, current kind still shown) and PATCH carries no kind', async () => {
    mutateAsync.mockResolvedValue({ item: existing() })
    renderDialog(existing())
    expect(screen.getByRole('radio', { name: 'Phòng ban' })).toBeChecked()
    expect(screen.getByRole('radio', { name: 'Phòng ban' })).toBeDisabled()
    expect(screen.getByRole('radio', { name: 'Công ty' })).toBeDisabled()
    await userEvent.click(screen.getByRole('radio', { name: 'Công ty' }))
    expect(screen.getByRole('radio', { name: 'Phòng ban' })).toBeChecked()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(mutateAsync.mock.calls[0][0]).toEqual({
      id: 50,
      payload: {
        department_id: 1,
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

  it('editing a Công ty row: PATCH sends company_id only, the current company still missing from the picker', async () => {
    mutateAsync.mockResolvedValue({ item: existingCompanyRow() })
    renderDialog(existingCompanyRow())
    expect(screen.getByRole('radio', { name: 'Công ty' })).toBeChecked()
    expect(screen.getByRole('radio', { name: 'Công ty' })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    const { id, payload } = mutateAsync.mock.calls[0][0]
    expect(id).toBe(50)
    expect(payload.company_id).toBe(11)
    expect('department_id' in payload).toBe(false)
    expect('kind' in payload).toBe(false)
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

  it('end date before start date is rejected client-side', async () => {
    renderDialog(existing({ to_date: '2026-10-01' }))
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText('Đến ngày phải sau hoặc bằng từ ngày')).toBeInTheDocument()
    expect(mutateAsync).not.toHaveBeenCalled()
  })

  it('scope switch is on by default; its explanation sits behind the (i) next to the label, not as body text', () => {
    renderDialog(null)
    expect(screen.getByRole('switch')).toBeChecked()
    expect(screen.getByRole('button', { name: 'Giải thích công tắc phạm vi quyền' })).toHaveAttribute('type', 'button')
    expect(screen.queryByText(/thấy thêm dữ liệu của phòng này/)).not.toBeInTheDocument()
  })

  it('a profile with no primary company: plain placeholder, never "Chọn phòng của " with a blank name', () => {
    renderDialog(null, vi.fn(), employeeNoCompany)
    expect(screen.getByText('Chọn phòng ban')).toBeInTheDocument()
    expect(screen.queryByText(/Chọn phòng của\s*$/)).not.toBeInTheDocument()
  })

  it('new row with file rights: picked files show as small removable rows, uploaded only after save', async () => {
    renderDialog(null, vi.fn(), employee, true)
    const input = screen.getByLabelText('Chọn tệp QĐ')
    await userEvent.upload(input, [new File(['a'], 'qd-1.pdf'), new File(['b'], 'qd-2.pdf')])
    expect(screen.getByText('qd-1.pdf')).toBeInTheDocument()
    expect(screen.getByText('qd-2.pdf')).toBeInTheDocument()
    expect(screen.getByText('Tải lên sau khi lưu')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Bỏ tệp qd-1.pdf' }))
    expect(screen.queryByText('qd-1.pdf')).not.toBeInTheDocument()
    expect(screen.getByText('qd-2.pdf')).toBeInTheDocument()
  })

  it('the file picker button is type=button (inside the profile <form> it must not submit anything)', () => {
    renderDialog(null, vi.fn(), employee, true)
    expect(screen.getByRole('button', { name: 'Chọn tệp' })).toHaveAttribute('type', 'button')
  })
})
