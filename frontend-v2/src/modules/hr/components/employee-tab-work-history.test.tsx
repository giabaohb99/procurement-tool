import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { AuthUser } from '@/core/auth/auth-types'
import type { EmployeeDetail } from '../types/employee'
import type { EmployeeWorkHistory, EmployeeWorkHistoryListResult } from '../types/employee-work-history'
import { EmployeeTabWorkHistory } from './employee-tab-work-history'

const state = vi.hoisted(() => ({
  result: undefined as EmployeeWorkHistoryListResult | undefined,
  isLoading: false,
  isError: false,
  filesDialogCalls: [] as { open: boolean; historyId: number }[],
  applyMutate: vi.fn(),
  authUser: undefined as Partial<AuthUser> | undefined,
}))

vi.mock('../hooks/use-employee-work-history', () => ({
  useEmployeeWorkHistory: () => ({ data: state.result, isLoading: state.isLoading, isError: state.isError }),
  useApplyEmployeeWorkHistory: () => ({ mutate: state.applyMutate }),
  useDeleteEmployeeWorkHistory: () => ({ mutate: vi.fn() }),
}))

vi.mock('../hooks/use-employees', () => ({
  useEmployeeDepartments: () => ({ data: { primary_department_id: 0, extra_department_ids: [] } }),
}))

vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: state.authUser }),
}))

const confirmMock = vi.fn()
vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: (...args: unknown[]) => confirmMock(...args),
}))

//  Hộp thêm/sửa đã có bài kiểm riêng (`employee-work-history-form-dialog.test.tsx`)
//  — ở đây chỉ cần biết tab có MỞ nó lên đúng lúc, không cần dựng lại cả hộp
//  (tránh gọi thật `useCompanies`/`useDepartments`/`useJobPositions`).
vi.mock('./employee-work-history-form-dialog', () => ({
  EmployeeWorkHistoryFormDialog: () => null,
}))

vi.mock('./employee-work-history-files-dialog', () => ({
  EmployeeWorkHistoryFilesDialog: (props: { open: boolean; historyId: number }) => {
    state.filesDialogCalls.push({ open: props.open, historyId: props.historyId })
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

function row(overrides: Partial<EmployeeWorkHistory> = {}): EmployeeWorkHistory {
  return {
    id: 1,
    employee_id: 1,
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
    ...overrides,
  }
}

function renderTab() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      {/*  Hai khu đọc/ghi lựa chọn Bảng|Dòng thời gian qua `useUrlParamState`
           (`useSearchParams`) — cần `<Router>` bọc ngoài, khác bản trước khi
           chưa có yêu cầu lưu vào URL. */}
      <MemoryRouter>
        <EmployeeTabWorkHistory employee={employee} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  state.result = { items: [], can_edit: true, can_open_files: true }
  state.isLoading = false
  state.isError = false
  state.filesDialogCalls = []
  state.applyMutate.mockReset()
  state.authUser = { employee_id: 999 } // mặc định KHÁC `employee.id` (1) — không phải hồ sơ của chính mình.
  confirmMock.mockReset()
})

describe('EmployeeTabWorkHistory', () => {
  it('can_edit=false → không nút Thêm/Sửa/Xóa/Áp', () => {
    state.result = { items: [row()], can_edit: false, can_open_files: true }

    renderTab()

    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()
  })

  it('nhãn loại lấy từ WORK_EVENT_TYPE (event_type=3 → "Bổ nhiệm")', () => {
    state.result = { items: [row({ event_type: 3 })], can_edit: true, can_open_files: true }

    renderTab()

    expect(screen.getByText('Bổ nhiệm')).toBeInTheDocument()
  })

  it('to_date rỗng → huy hiệu «Đang hiệu lực»', () => {
    state.result = { items: [row({ to_date: null })], can_edit: true, can_open_files: true }

    renderTab()

    expect(screen.getByText('Đang hiệu lực')).toBeInTheDocument()
  })

  //  Lỗi 05/10/2026: dòng chính nhập bù bị dòng mới hơn thay vẫn hiện «Đang hiệu lực».
  it('to_date rỗng nhưng is_current=false (đã bị dòng chính mới hơn thay) → chỉ MỘT «Đang hiệu lực»', () => {
    state.result = {
      items: [
        row({ id: 9, to_date: null, from_date: '2026-10-04', is_current: true }),
        row({ id: 10, to_date: null, from_date: '2026-10-03', is_current: false }),
      ],
      can_edit: true,
      can_open_files: true,
    }

    renderTab()

    expect(screen.getAllByText('Đang hiệu lực')).toHaveLength(1)
  })

  it('danh sách rỗng + can_edit → có nút «Tạo dòng đầu từ hồ sơ»', () => {
    state.result = { items: [], can_edit: true, can_open_files: true }

    renderTab()

    expect(screen.getByRole('button', { name: 'Tạo dòng đầu từ hồ sơ' })).toBeInTheDocument()
  })

  it('can_open_files=false + file_count=2 → "Có 2 tệp đính kèm", không nút xem/tải, không mở hộp tệp', () => {
    state.result = {
      items: [row({ file_count: 2 })],
      can_edit: true,
      can_open_files: false,
    }

    renderTab()

    expect(screen.getByText('Có 2 tệp đính kèm')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^2$/ })).not.toBeInTheDocument()
    //  Hộp tệp vẫn được dựng (prop `open`), nhưng CHƯA LẦN NÀO mở ra — vì không
    //  có nút nào để bấm vào. `EmployeeWorkHistoryFilesDialog` mock cho thấy nó
    //  luôn nhận `open:false`, nên hook `useWorkHistoryFiles` bên trong hộp thật
    //  (bị gác bởi chính cờ `open`) không bao giờ gọi `/api/attachments`.
    expect(state.filesDialogCalls.every((call) => call.open === false)).toBe(true)
  })
})

describe('EmployeeTabWorkHistory — nút ▶ «Áp vào hồ sơ» phải HỎI trước khi gọi API (H1)', () => {
  it('dòng Thôi việc: bấm ▶ → mở hộp xác nhận riêng, CHƯA gọi applyMutation', async () => {
    state.result = {
      items: [row({ event_type: 6, from_date: '2026-01-01' })],
      can_edit: true,
      can_open_files: true,
    }

    renderTab()
    await userEvent.click(screen.getByRole('button', { name: 'Áp vào hồ sơ' }))

    expect(await screen.findByText('Chuyển hồ sơ sang nghỉ việc?')).toBeInTheDocument()
    //  Hộp dùng lại cho nút ▶ phải đổi nhãn — KHÔNG phải nhãn của hộp LƯU dòng.
    expect(screen.getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chuyển sang nghỉ việc' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Chỉ lưu dòng' })).not.toBeInTheDocument()
    expect(state.applyMutate).not.toHaveBeenCalled()
  })

  it('dòng Thôi việc: bấm «Chuyển sang nghỉ việc» → gọi applyMutation với đúng id dòng', async () => {
    state.result = {
      items: [row({ id: 7, event_type: 6, from_date: '2026-01-01' })],
      can_edit: true,
      can_open_files: true,
    }

    renderTab()
    await userEvent.click(screen.getByRole('button', { name: 'Áp vào hồ sơ' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Chuyển sang nghỉ việc' }))

    expect(state.applyMutate).toHaveBeenCalledTimes(1)
    expect(state.applyMutate.mock.calls[0][0]).toBe(7)
  })

  it('dòng Thôi việc: bấm «Hủy» → KHÔNG gọi applyMutation, hộp đóng lại', async () => {
    state.result = {
      items: [row({ event_type: 6, from_date: '2026-01-01' })],
      can_edit: true,
      can_open_files: true,
    }

    renderTab()
    await userEvent.click(screen.getByRole('button', { name: 'Áp vào hồ sơ' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Hủy' }))

    expect(state.applyMutate).not.toHaveBeenCalled()
    await waitFor(() =>
      expect(screen.queryByText('Chuyển hồ sơ sang nghỉ việc?')).not.toBeInTheDocument(),
    )
  })

  it('loại KHÁC Thôi việc: bấm ▶ → mở confirm() chung (Hủy/Áp vào hồ sơ), đồng ý mới gọi applyMutation', async () => {
    confirmMock.mockResolvedValue(true)
    state.result = {
      items: [row({ id: 9, event_type: 3, from_date: '2026-01-01' })],
      can_edit: true,
      can_open_files: true,
    }

    renderTab()
    await userEvent.click(screen.getByRole('button', { name: 'Áp vào hồ sơ' }))

    await waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1))
    const options = confirmMock.mock.calls[0][0] as { cancelLabel?: string; confirmLabel?: string }
    expect(options.cancelLabel).toBe('Hủy')
    expect(options.confirmLabel).toBe('Áp vào hồ sơ')
    await waitFor(() => expect(state.applyMutate).toHaveBeenCalledTimes(1))
    expect(state.applyMutate.mock.calls[0][0]).toBe(9)
  })

  it('loại KHÁC Thôi việc: confirm() trả false (Hủy) → KHÔNG gọi applyMutation', async () => {
    confirmMock.mockResolvedValue(false)
    state.result = {
      items: [row({ event_type: 3, from_date: '2026-01-01' })],
      can_edit: true,
      can_open_files: true,
    }

    renderTab()
    await userEvent.click(screen.getByRole('button', { name: 'Áp vào hồ sơ' }))

    await waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1))
    expect(state.applyMutate).not.toHaveBeenCalled()
  })
})

describe('EmployeeTabWorkHistory — câu "của chính bạn do người khác cập nhật" (Low FE)', () => {
  it('canEdit=false + ĐÚNG hồ sơ của chính mình + đã tải xong → hiện câu', () => {
    state.result = { items: [], can_edit: false, can_open_files: true }
    state.authUser = { employee_id: employee.id }

    renderTab()

    expect(
      screen.getByText('Quá trình công tác của chính bạn do người khác cập nhật.'),
    ).toBeInTheDocument()
  })

  it('canEdit=false NHƯNG là hồ sơ của NGƯỜI KHÁC (chỉ thiếu quyền sửa) → KHÔNG hiện câu đó', () => {
    state.result = { items: [], can_edit: false, can_open_files: true }
    state.authUser = { employee_id: employee.id + 1 }

    renderTab()

    expect(
      screen.queryByText('Quá trình công tác của chính bạn do người khác cập nhật.'),
    ).not.toBeInTheDocument()
  })

  it('canEdit=false + là hồ sơ chính mình NHƯNG CHƯA tải xong → KHÔNG hiện câu đó', () => {
    state.result = undefined
    state.isLoading = true
    state.authUser = { employee_id: employee.id }

    renderTab()

    expect(
      screen.queryByText('Quá trình công tác của chính bạn do người khác cập nhật.'),
    ).not.toBeInTheDocument()
  })
})
