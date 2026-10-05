import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { EmployeeDetail } from '../types/employee'
import type { EmployeeWorkHistory, EmployeeWorkHistoryListResult } from '../types/employee-work-history'
import { EmployeeTabWorkDecisions } from './employee-tab-work-decisions'

const state = vi.hoisted(() => ({
  result: undefined as EmployeeWorkHistoryListResult | undefined,
  isLoading: false,
  isError: false,
  queriedEmployeeId: undefined as number | undefined,
  filesDialogCalls: [] as { open: boolean; historyId: number; editable: boolean }[],
  formDialogCalls: [] as {
    open: boolean
    row: EmployeeWorkHistory | null
    seed: unknown
    requireDecisionNo: boolean | undefined
    createTitle: string | undefined
  }[],
}))

vi.mock('../hooks/use-employee-work-history', () => ({
  useEmployeeWorkHistory: (employeeId: number) => {
    state.queriedEmployeeId = employeeId
    return { data: state.result, isLoading: state.isLoading, isError: state.isError }
  },
}))

vi.mock('../hooks/use-employees', () => ({
  useEmployeeDepartments: () => ({ data: { primary_department_id: 0, extra_department_ids: [] } }),
}))

vi.mock('./employee-work-history-files-dialog', () => ({
  EmployeeWorkHistoryFilesDialog: (props: { open: boolean; historyId: number; editable: boolean }) => {
    state.filesDialogCalls.push({ open: props.open, historyId: props.historyId, editable: props.editable })
    return null
  },
}))

//  Hộp thêm/sửa đã có bài kiểm riêng (`employee-work-history-form-dialog.test.tsx`)
//  — ở đây chỉ cần biết tab mở nó lên ĐÚNG lúc, ĐÚNG seed/tiêu đề/ép Số QĐ
//  (mục 3), không cần dựng lại cả hộp (tránh gọi thật useCompanies/useDepartments/useJobPositions).
vi.mock('./employee-work-history-form-dialog', () => ({
  EmployeeWorkHistoryFormDialog: (props: {
    open: boolean
    row: EmployeeWorkHistory | null
    seed: unknown
    requireDecisionNo?: boolean
    createTitle?: string
  }) => {
    state.formDialogCalls.push({
      open: props.open,
      row: props.row,
      seed: props.seed,
      requireDecisionNo: props.requireDecisionNo,
      createTitle: props.createTitle,
    })
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

function renderTab() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      {/*  `EmployeeWorkHistoryDecisionSection` đọc/ghi lựa chọn Bảng|Dòng thời
           gian qua `useUrlParamState` — cần `<Router>` bọc ngoài. */}
      <MemoryRouter>
        <EmployeeTabWorkDecisions employee={employee} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  state.result = { items: [], can_edit: true, can_open_files: true }
  state.isLoading = false
  state.isError = false
  state.queriedEmployeeId = undefined
  state.filesDialogCalls = []
  state.formDialogCalls = []
})

describe('EmployeeTabWorkDecisions', () => {
  it('gọi useEmployeeWorkHistory với đúng id nhân sự — CHUNG khóa với tab Quá trình công tác', () => {
    renderTab()
    expect(state.queriedEmployeeId).toBe(employee.id)
  })

  it('không có nút Thêm/Sửa/Xóa/Áp — khu này chỉ đọc dù can_edit=true (chỉ có «+ Thêm quyết định»)', () => {
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

/**
 * Mục 3 (03/10/2026) — nút «+ Thêm quyết định» mở ĐÚNG hộp thêm/sửa quá trình
 * công tác dùng chung, nhưng với tiêu đề/loại mặc định/ràng buộc riêng cho
 * ngữ cảnh "thêm quyết định": loại Bổ nhiệm, Số QĐ bắt buộc. Lưu xong dùng
 * chung khóa truy vấn với tab «Quá trình công tác» nên dòng mới hiện ở cả hai.
 */
describe('EmployeeTabWorkDecisions — nút «+ Thêm quyết định» (mục 3)', () => {
  it('can_edit=true → có nút, bấm vào mở hộp với tiêu đề/loại/ràng buộc đúng ngữ cảnh', async () => {
    state.result = { items: [], can_edit: true, can_open_files: true }
    renderTab()

    //  Rỗng → 2 nút cùng tên (toolbarEnd + gợi ý giữa khu), bấm nút nào cũng như nhau.
    const buttons = screen.getAllByRole('button', { name: /Thêm quyết định/ })
    await userEvent.click(buttons[0])

    const call = state.formDialogCalls.at(-1)
    expect(call?.open).toBe(true)
    expect(call?.row).toBeNull()
    expect(call?.seed).toEqual({ event_type: 3 }) // APPOINT_TYPE — Bổ nhiệm
    expect(call?.requireDecisionNo).toBe(true)
    expect(call?.createTitle).toBe('Thêm quyết định bổ nhiệm')
  })

  it('can_edit=false → KHÔNG có nút «+ Thêm quyết định» ở đâu cả', () => {
    state.result = { items: [], can_edit: false, can_open_files: true }
    renderTab()

    expect(screen.queryByRole('button', { name: /Thêm quyết định/ })).not.toBeInTheDocument()
  })

  it('hộp luôn mount với `open=false` lúc chưa bấm gì — không tự bật', () => {
    state.result = { items: [], can_edit: true, can_open_files: true }
    renderTab()

    expect(state.formDialogCalls.at(-1)?.open).toBe(false)
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
