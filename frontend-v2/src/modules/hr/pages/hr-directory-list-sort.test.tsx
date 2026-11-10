import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { CompanyListPage } from './company-list-page'
import { DepartmentListPage } from './department-list-page'
import { EmployeeListPage } from './employee-list-page'

/**
 * duoc-CR-744 — bấm tiêu đề cột ba danh sách Nhân sự / Pháp nhân / Phòng ban phải gửi `sort_by` lên server.
 * Trước đây chỉ vài cột có `sortable` (Mã, Tên, Ngày cập nhật); các cột còn lại bấm không có gì xảy ra.
 * Chặn ở tầng HOOK dữ liệu để bắt đúng BỘ THAM SỐ trang gửi đi.
 */
const employeeCalls: ListParams[] = []
const companyCalls: ListParams[] = []
const departmentCalls: ListParams[] = []

vi.mock('../hooks/use-employees', () => ({
  useEmployees: (params: ListParams) => {
    employeeCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false, isFetching: false }
  },
}))
vi.mock('../hooks/use-companies', () => ({
  useCompanies: (params: ListParams) => {
    companyCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
  },
}))
vi.mock('../hooks/use-departments', () => ({
  useDepartments: (params: ListParams) => {
    departmentCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
  },
}))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))
vi.mock('@/core/telemetry/use-search-telemetry', () => ({ useSearchTelemetry: () => undefined }))
//  Hộp thoại và nút nhập có hook riêng (mạng, form) — không liên quan tới sắp xếp.
vi.mock('../components/employee-form-dialog', () => ({ EmployeeFormDialog: () => null }))
vi.mock('../components/employee-import-button', () => ({ EmployeeImportButton: () => null }))
vi.mock('../components/company-form-dialog', () => ({ CompanyFormDialog: () => null }))
vi.mock('../components/department-form-dialog', () => ({ DepartmentFormDialog: () => null }))

function build(element: React.ReactElement, url: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>{element}</MemoryRouter>
    </QueryClientProvider>,
  )
}

function header(text: string) {
  return screen.getByText(text, { selector: 'thead span' })
}

function last(calls: ListParams[]) {
  return calls[calls.length - 1]
}

beforeEach(() => {
  employeeCalls.length = 0
  companyCalls.length = 0
  departmentCalls.length = 0
})

describe('EmployeeListPage — sắp xếp cột (duoc-CR-744)', () => {
  it('sends the column key as sort_by for every sortable data column', async () => {
    const user = userEvent.setup()
    build(<EmployeeListPage />, '/hr/employees')

    const cases: [string, string][] = [
      ['Mã NV', 'code'],
      ['Họ tên', 'full_name'],
      ['Email', 'email'],
      ['Công ty', 'company_name'],
      ['Phòng ban', 'department_name'],
      ['Chức vụ', 'position'],
      ['Hình thức', 'employment_type_label'],
      ['Cấp bậc', 'job_level_label'],
      ['Quản lý trực tiếp', 'direct_manager_name'],
      ['Tình trạng', 'status'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(last(employeeCalls).sort_by, text).toBe(key)
    }
  })

  it('cycles asc -> desc -> off, drops both params on the third click and resets to page 1', async () => {
    const user = userEvent.setup()
    build(<EmployeeListPage />, '/hr/employees')

    await user.click(header('Công ty'))
    expect(last(employeeCalls)).toMatchObject({ sort_by: 'company_name', sort_dir: 'asc', page: 1 })
    await user.click(header('Công ty'))
    expect(last(employeeCalls)).toMatchObject({ sort_by: 'company_name', sort_dir: 'desc' })
    await user.click(header('Công ty'))
    expect(last(employeeCalls).sort_by).toBeUndefined()
    expect(last(employeeCalls).sort_dir).toBeUndefined()
  })

  it('does not sort when the avatar column header is clicked (not a data column)', async () => {
    const user = userEvent.setup()
    build(<EmployeeListPage />, '/hr/employees')

    const before = employeeCalls.length
    await user.click(header('Ảnh'))
    expect(employeeCalls.length).toBe(before)
    expect(last(employeeCalls).sort_by).toBeUndefined()
  })

  it('restores the sort from the URL and keeps it in the request (shareable link)', () => {
    build(<EmployeeListPage />, '/hr/employees?sort_by=direct_manager_name&sort_dir=desc')
    expect(last(employeeCalls)).toMatchObject({ sort_by: 'direct_manager_name', sort_dir: 'desc' })
  })
})

describe('CompanyListPage — sắp xếp cột (duoc-CR-744)', () => {
  it('sends the column key as sort_by for every sortable data column', async () => {
    const user = userEvent.setup()
    build(<CompanyListPage />, '/hr/companies')

    const cases: [string, string][] = [
      ['Tên pháp nhân', 'name'],
      ['Mã', 'code'],
      ['Cấp', 'level'],
      ['Mã số hiệu', 'issue_code'],
      ['Mã số thuế', 'tax_code'],
      ['Người đại diện', 'legal_rep_name'],
      ['Trạng thái', 'is_active'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(last(companyCalls).sort_by, text).toBe(key)
    }
  })
})

describe('DepartmentListPage — sắp xếp cột (duoc-CR-744)', () => {
  it('sends the column key as sort_by for every sortable data column', async () => {
    const user = userEvent.setup()
    build(<DepartmentListPage />, '/hr/departments')

    const cases: [string, string][] = [
      ['Mã', 'code'],
      ['Mã số hiệu', 'issue_code'],
      ['Phòng ban', 'name'],
      ['Loại đơn vị', 'kind'],
      ['Trưởng bộ phận', 'manager_name'],
      ['Trạng thái', 'is_active'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(last(departmentCalls).sort_by, text).toBe(key)
    }
  })
})
