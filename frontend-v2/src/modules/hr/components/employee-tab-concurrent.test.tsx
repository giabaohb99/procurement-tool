import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Employee } from '../types/employee'
import type { EmployeeConcurrent, EmployeeConcurrentListResult } from '../types/employee-concurrent'
import { EmployeeTabConcurrent } from './employee-tab-concurrent'

const state: {
  result: EmployeeConcurrentListResult | undefined
  authEmployeeId: number
  deleteMutate: ReturnType<typeof vi.fn>
  formDialog: { open: boolean; row: EmployeeConcurrent | null } | null
  filesDialog: { open: boolean; concurrentId: number; editable: boolean } | null
} = { result: undefined, authEmployeeId: 0, deleteMutate: vi.fn(), formDialog: null, filesDialog: null }

vi.mock('../hooks/use-employee-concurrents', () => ({
  useEmployeeConcurrents: () => ({ data: state.result, isLoading: false, isError: false }),
  useDeleteEmployeeConcurrent: () => ({ mutate: state.deleteMutate }),
}))
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { employee_id: state.authEmployeeId } }),
}))
vi.mock('./employee-concurrent-form-dialog', () => ({
  EmployeeConcurrentFormDialog: (props: { open: boolean; row: EmployeeConcurrent | null }) => {
    state.formDialog = { open: props.open, row: props.row }
    return null
  },
}))
vi.mock('./employee-concurrent-files-dialog', () => ({
  EmployeeConcurrentFilesDialog: (props: { open: boolean; concurrentId: number; editable: boolean }) => {
    state.filesDialog = { open: props.open, concurrentId: props.concurrentId, editable: props.editable }
    return null
  },
}))

const employee = { id: 1, company_id: 10, department_id: 20 } as Employee

function row(overrides: Partial<EmployeeConcurrent>): EmployeeConcurrent {
  return {
    id: 1,
    employee_id: 1,
    kind: 1,
    kind_label: 'Phòng ban',
    company_id: 10,
    company_name: 'DEGO A',
    department_id: 5,
    department_name: 'Kế toán',
    position_id: 0,
    position_label: 'Phó phòng',
    from_date: '2026-01-01',
    to_date: null,
    decision_no: 'QĐ-01',
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

function renderTab(who: Employee = employee) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <form onSubmit={(e) => e.preventDefault()}>
          <EmployeeTabConcurrent employee={who} />
        </form>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  state.result = undefined
  state.authEmployeeId = 0
  state.deleteMutate = vi.fn()
  state.formDialog = null
  state.filesDialog = null
})

describe('EmployeeTabConcurrent', () => {
  it('Loại column + one "Nơi kiêm nhiệm" cell: room name for Phòng ban, company name for Công ty (never both)', () => {
    state.result = {
      items: [
        row({ id: 1, department_name: 'Kế toán', status: 2, status_label: 'Đang hiệu lực' }),
        row({
          id: 2,
          kind: 2,
          kind_label: 'Công ty',
          company_id: 11,
          company_name: 'DEGO B',
          department_id: 0,
          department_name: '',
          status: 1,
          status_label: 'Sắp tới',
        }),
        row({ id: 3, department_name: 'Mua hàng', status: 3, status_label: 'Đã hết', counts_scope: false }),
      ],
      can_edit: true,
      can_open_files: true,
    }
    renderTab()
    const table = screen.getByRole('table')
    expect(within(table).getByRole('columnheader', { name: /Loại/ })).toBeInTheDocument()
    expect(within(table).getByRole('columnheader', { name: /Nơi kiêm nhiệm/ })).toBeInTheDocument()
    expect(within(table).queryByRole('columnheader', { name: /^Công ty$/ })).not.toBeInTheDocument()
    expect(within(table).getAllByText('Phòng ban')).toHaveLength(2)
    expect(within(table).getByText('Công ty')).toBeInTheDocument()
    expect(within(table).getByText('Kế toán')).toBeInTheDocument()
    expect(within(table).getByText('DEGO B')).toBeInTheDocument()
    //  Dòng Phòng ban không lặp tên công ty hiện tại vào ô nơi kiêm nhiệm.
    expect(within(table).queryByText('DEGO A')).not.toBeInTheDocument()
    expect(within(table).getByText('Đang hiệu lực')).toBeInTheDocument()
    expect(within(table).getByText('Sắp tới')).toBeInTheDocument()
    expect(within(table).getByText('Đã hết')).toBeInTheDocument()
    expect(within(table).getByText('Không')).toBeInTheDocument()
  })

  it('default order puts active rows before upcoming and ended ones', () => {
    state.result = {
      items: [
        row({ id: 1, department_name: 'Phòng hết', status: 3 }),
        row({ id: 2, department_name: 'Phòng sắp', status: 1 }),
        row({ id: 3, department_name: 'Phòng đang', status: 2 }),
      ],
      can_edit: false,
      can_open_files: false,
    }
    renderTab()
    const names = screen.getAllByText(/^Phòng (hết|sắp|đang)$/).map((el) => el.textContent)
    expect(names).toEqual(['Phòng đang', 'Phòng sắp', 'Phòng hết'])
  })

  it('own profile (can_edit=false): no add / edit / delete buttons and a read-only notice', () => {
    state.authEmployeeId = 1
    state.result = { items: [row({})], can_edit: false, can_open_files: true }
    renderTab()
    expect(screen.queryByRole('button', { name: /Thêm kiêm nhiệm/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Sửa kiêm nhiệm/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
    expect(screen.getByText(/hồ sơ của chính bạn/)).toBeInTheDocument()
  })

  it('no write permission on someone else profile: read-only but no "your own profile" sentence', () => {
    state.authEmployeeId = 99
    state.result = { items: [row({})], can_edit: false, can_open_files: false }
    renderTab()
    expect(screen.queryByRole('button', { name: /Thêm kiêm nhiệm/ })).not.toBeInTheDocument()
    expect(screen.queryByText(/hồ sơ của chính bạn/)).not.toBeInTheDocument()
  })

  it('can_edit: add button opens the create dialog and is type=button (does not submit the profile form)', async () => {
    state.result = { items: [], can_edit: true, can_open_files: true }
    renderTab()
    const add = screen.getByRole('button', { name: /Thêm kiêm nhiệm/ })
    expect(add).toHaveAttribute('type', 'button')
    await userEvent.click(add)
    expect(state.formDialog).toEqual({ open: true, row: null })
  })

  it('edit button opens the dialog with that row', async () => {
    const target = row({ id: 42, department_name: 'Kế toán' })
    state.result = { items: [target], can_edit: true, can_open_files: true }
    renderTab()
    await userEvent.click(screen.getByRole('button', { name: 'Sửa kiêm nhiệm Kế toán' }))
    expect(state.formDialog?.row?.id).toBe(42)
  })

  it('can_open_files=false: shows the file count only, no button that would call the attachment API', () => {
    state.result = { items: [row({ file_count: 2 })], can_edit: true, can_open_files: false }
    renderTab()
    expect(screen.getByText('Có 2 tệp')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Mở 2 tệp/ })).not.toBeInTheDocument()
  })

  it('can_open_files=true: file button opens the files dialog for that row, editable follows can_edit', async () => {
    state.result = { items: [row({ id: 9, file_count: 1 })], can_edit: false, can_open_files: true }
    renderTab()
    await userEvent.click(screen.getByRole('button', { name: 'Mở 1 tệp quyết định' }))
    expect(state.filesDialog).toEqual({ open: true, concurrentId: 9, editable: false })
  })

  it('delete asks for confirmation first and only then calls the mutation once', async () => {
    state.result = { items: [row({ id: 5, department_name: 'Kế toán', company_name: 'DEGO B' })], can_edit: true, can_open_files: true }
    renderTab()
    await userEvent.click(screen.getByRole('button', { name: 'Xóa' }))
    expect(state.deleteMutate).not.toHaveBeenCalled()
    expect(screen.getByText(/Xóa kiêm nhiệm phòng "Kế toán"\?/)).toBeInTheDocument()
    expect(screen.getByText(/thôi thấy dữ liệu của phòng này/)).toBeInTheDocument()
    await userEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Xóa' }))
    expect(state.deleteMutate).toHaveBeenCalledTimes(1)
    expect(state.deleteMutate.mock.calls[0][0]).toBe(5)
  })

  it('delete of a Công ty row names the company and says the person stops counting as its staff', async () => {
    state.result = {
      items: [row({ id: 6, kind: 2, kind_label: 'Công ty', company_name: 'DEGO B', department_id: 0, department_name: '' })],
      can_edit: true,
      can_open_files: true,
    }
    renderTab()
    await userEvent.click(screen.getByRole('button', { name: 'Xóa' }))
    expect(screen.getByText(/Xóa kiêm nhiệm công ty "DEGO B"\?/)).toBeInTheDocument()
    expect(screen.getByText(/thôi được tính là người của công ty này/)).toBeInTheDocument()
  })

  it('profile without a primary company: add button disabled and a sentence says why (backend would 400 both kinds)', async () => {
    state.result = { items: [], can_edit: true, can_open_files: true }
    renderTab({ id: 1, company_id: 0, department_id: 0 } as Employee)
    const add = screen.getByRole('button', { name: /Thêm kiêm nhiệm/ })
    expect(add).toBeDisabled()
    expect(screen.getByText(/chưa gắn pháp nhân chính/)).toBeInTheDocument()
    await userEvent.click(add)
    expect(state.formDialog?.open).toBe(false)
  })

  it('profile with a primary company: no such sentence, add button enabled', () => {
    state.result = { items: [], can_edit: true, can_open_files: true }
    renderTab()
    expect(screen.getByRole('button', { name: /Thêm kiêm nhiệm/ })).toBeEnabled()
    expect(screen.queryByText(/chưa gắn pháp nhân chính/)).not.toBeInTheDocument()
  })
})
