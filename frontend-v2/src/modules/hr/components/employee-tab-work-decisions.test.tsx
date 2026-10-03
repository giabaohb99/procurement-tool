import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { EmployeeDetail } from '../types/employee'
import type { EmployeeWorkHistoryListResult } from '../types/employee-work-history'
import { EmployeeTabWorkDecisions } from './employee-tab-work-decisions'

const state = vi.hoisted(() => ({
  result: undefined as EmployeeWorkHistoryListResult | undefined,
  isLoading: false,
  isError: false,
  queriedEmployeeId: undefined as number | undefined,
  filesDialogCalls: [] as { open: boolean; historyId: number; editable: boolean }[],
}))

vi.mock('../hooks/use-employee-work-history', () => ({
  useEmployeeWorkHistory: (employeeId: number) => {
    state.queriedEmployeeId = employeeId
    return { data: state.result, isLoading: state.isLoading, isError: state.isError }
  },
}))

vi.mock('./employee-work-history-files-dialog', () => ({
  EmployeeWorkHistoryFilesDialog: (props: { open: boolean; historyId: number; editable: boolean }) => {
    state.filesDialogCalls.push({ open: props.open, historyId: props.historyId, editable: props.editable })
    return null
  },
}))

const employee: EmployeeDetail = {
  id: 1,
  code: 'NSU001',
  full_name: 'Trần Minh',
  email: '',
  phone: '',
  company_id: 10,
  department_id: 20,
  position: 'Nhân viên',
  position_id: 30,
  role_name: '',
  status: 'official',
  status_label: 'Đang làm',
  is_active: true,
  gender: 0,
  avatar: '',
  signature: '',
  user_id: 1,
}

function renderTab(onGoToWorkHistoryClick = vi.fn()) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const result = render(
    <QueryClientProvider client={queryClient}>
      {/*  `EmployeeWorkHistoryDecisionSection` đọc/ghi lựa chọn Bảng|Dòng thời
           gian qua `useUrlParamState` — cần `<Router>` bọc ngoài. */}
      <MemoryRouter>
        <EmployeeTabWorkDecisions employee={employee} onGoToWorkHistoryClick={onGoToWorkHistoryClick} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { ...result, onGoToWorkHistoryClick }
}

beforeEach(() => {
  state.result = { items: [], can_edit: true, can_open_files: true }
  state.isLoading = false
  state.isError = false
  state.queriedEmployeeId = undefined
  state.filesDialogCalls = []
})

describe('EmployeeTabWorkDecisions', () => {
  it('gọi useEmployeeWorkHistory với đúng id nhân sự — CHUNG khóa với tab Quá trình công tác', () => {
    renderTab()
    expect(state.queriedEmployeeId).toBe(employee.id)
  })

  it('rỗng + can_edit=true → nút «Thêm ở tab Quá trình công tác», bấm vào gọi onGoToWorkHistoryClick', async () => {
    state.result = { items: [], can_edit: true, can_open_files: true }
    const { onGoToWorkHistoryClick } = renderTab()

    const button = screen.getByRole('button', { name: 'Thêm ở tab Quá trình công tác' })
    await userEvent.click(button)

    expect(onGoToWorkHistoryClick).toHaveBeenCalledTimes(1)
  })

  it('rỗng + can_edit=false → KHÔNG có nút gợi ý (chỉ xem, không quyền sửa)', () => {
    state.result = { items: [], can_edit: false, can_open_files: true }
    renderTab()

    expect(
      screen.queryByRole('button', { name: 'Thêm ở tab Quá trình công tác' }),
    ).not.toBeInTheDocument()
  })

  it('không có nút Thêm/Sửa/Xóa/Áp — khu này chỉ đọc dù can_edit=true', () => {
    state.result = {
      items: [{ ...row(), decision_no: 'QD-30' }],
      can_edit: true,
      can_open_files: true,
    }
    renderTab()

    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()
  })

  it('hộp tệp theo `can_edit`: true → editable=true, false → editable=false', () => {
    state.result = { items: [], can_edit: true, can_open_files: true }
    renderTab()
    expect(state.filesDialogCalls.at(-1)?.editable).toBe(true)

    state.result = { items: [], can_edit: false, can_open_files: true }
    renderTab()
    expect(state.filesDialogCalls.at(-1)?.editable).toBe(false)
  })
})

function row(overrides: Partial<ReturnType<typeof baseRow>> = {}) {
  return { ...baseRow(), ...overrides }
}

function baseRow() {
  return {
    id: 1,
    employee_id: employee.id,
    event_type: 3,
    from_date: '2026-01-01',
    to_date: null,
    company_id: 10,
    company_name: 'DEGO',
    department_id: 20,
    department_name: 'Phòng KD',
    position_id: 30,
    position_label: 'Trưởng phòng',
    decision_no: '',
    decision_date: null,
    note: '',
    applied_at: null,
    file_count: 0,
    is_current: true,
    can_apply: true,
  }
}
