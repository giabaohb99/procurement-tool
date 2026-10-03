import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { queryKeys } from '@/shared/constants/query-keys'
import { toDateInputValue } from '@/shared/utils/format-date'
import type * as EmployeeWorkHistoryApiModule from '../api/employee-work-history-api'
import type { Employee } from '../types/employee'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { EmployeeWorkHistoryFormDialog } from './employee-work-history-form-dialog'

const TODAY = toDateInputValue(new Date())

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAny: () => true }),
}))

vi.mock('../hooks/use-companies', () => ({
  useCompanies: () => ({ data: { items: [] } }),
}))
vi.mock('../hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: [] } }),
}))
vi.mock('../hooks/use-job-positions', () => ({
  useJobPositions: () => ({ data: { items: [] } }),
}))

const mutateAsync = vi.fn()
vi.mock('../hooks/use-employee-work-history', () => ({
  useSaveEmployeeWorkHistory: () => ({ mutateAsync, isPending: false }),
}))

const confirmMock = vi.fn()
vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: (...args: unknown[]) => confirmMock(...args),
}))

const uploadWorkHistoryFilesMock = vi.fn()
vi.mock('../api/employee-work-history-api', async (importOriginal) => {
  const actual = await importOriginal<typeof EmployeeWorkHistoryApiModule>()
  return { ...actual, uploadWorkHistoryFiles: (...args: unknown[]) => uploadWorkHistoryFilesMock(...args) }
})

const employee: Employee = {
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
}

function renderDialog(
  seed: Record<string, unknown>,
  options: {
    outerSubmit?: () => void
    canOpenFiles?: boolean
    row?: EmployeeWorkHistory | null
    allRows?: EmployeeWorkHistory[]
    queryClient?: QueryClient
  } = {},
) {
  const queryClient = options.queryClient ?? new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const node = (
    <QueryClientProvider client={queryClient}>
      <EmployeeWorkHistoryFormDialog
        open
        onOpenChange={vi.fn()}
        employeeId={1}
        employee={employee}
        row={options.row ?? null}
        allRows={options.allRows ?? []}
        extraDeptIds={[]}
        canOpenFiles={options.canOpenFiles ?? true}
        seed={seed as never}
      />
    </QueryClientProvider>
  )
  if (options.outerSubmit) {
    return render(
      <form
        onSubmit={(event) => {
          event.preventDefault()
          options.outerSubmit?.()
        }}
      >
        {node}
      </form>,
    )
  }
  return render(node)
}

function workHistoryRow(overrides: Partial<EmployeeWorkHistory> = {}): EmployeeWorkHistory {
  return {
    id: 5,
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
    file_count: 2,
    is_current: true,
    can_apply: true,
    ...overrides,
  }
}

beforeEach(() => {
  mutateAsync.mockReset()
  mutateAsync.mockResolvedValue({ item: { id: 123, file_count: 0 }, warnings: [], applied_changes: [] })
  confirmMock.mockReset()
  uploadWorkHistoryFilesMock.mockReset()
  uploadWorkHistoryFilesMock.mockResolvedValue([])
})

describe('EmployeeWorkHistoryFormDialog', () => {
  it('to_date < from_date hiện lỗi, không gọi API', async () => {
    renderDialog({ event_type: 9, from_date: TODAY, to_date: '2020-01-01' })

    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    expect(await screen.findByText('Đến ngày phải sau hoặc bằng từ ngày')).toBeInTheDocument()
    expect(mutateAsync).not.toHaveBeenCalled()
  })

  it('bấm Lưu 2 lần liền → 1 request', async () => {
    //  `disabled={isPending}` chỉ đúng ở lần render SAU — hai lần submit liền
    //  tay (cùng tick) phải bị chốt `useRef` chặn, không thì ra hai lần lưu.
    let release: (value: unknown) => void = () => {}
    mutateAsync.mockImplementation(() => new Promise((resolve) => (release = resolve)))
    renderDialog({ event_type: 9, from_date: TODAY, to_date: '' })
    //  `Dialog` dựng qua Portal nên form KHÔNG nằm trong `container` của RTL.
    const form = screen.getByRole('button', { name: 'Lưu' }).closest('form')
    if (!form) throw new Error('Không thấy form trong hộp thoại')

    fireEvent.submit(form)
    fireEvent.submit(form)

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    release({ item: { id: 123, file_count: 0 }, warnings: [], applied_changes: [] })
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
  })

  it('submit hộp KHÔNG kích onSubmit của form CHA bọc ngoài (bẫy 1)', async () => {
    const outerSubmit = vi.fn()
    renderDialog({ event_type: 9, from_date: TODAY, to_date: '' }, { outerSubmit })

    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(outerSubmit).not.toHaveBeenCalled()
  })

  it('từ chối câu hỏi áp hồ sơ → gửi apply_to_profile:false', async () => {
    confirmMock.mockResolvedValue(false)
    //  Loại 3 (Bổ nhiệm) + phòng KHÁC hồ sơ hiện tại (20) → có câu hỏi.
    renderDialog({ event_type: 3, from_date: TODAY, to_date: '', department_id: 999 })

    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(confirmMock).toHaveBeenCalledTimes(1)
    const call = mutateAsync.mock.calls[0][0] as { payload: { apply_to_profile: boolean } }
    expect(call.payload.apply_to_profile).toBe(false)
  })

  it('loại Thôi việc mở hộp xác nhận RIÊNG, không mở confirm() chung', async () => {
    renderDialog({ event_type: 6, from_date: TODAY, to_date: '' })

    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    expect(await screen.findByText('Chuyển hồ sơ sang nghỉ việc?')).toBeInTheDocument()
    expect(confirmMock).not.toHaveBeenCalled()
    //  Chưa bấm nút nào trong hộp riêng → chưa gửi gì.
    expect(mutateAsync).not.toHaveBeenCalled()
  })

  it('M6 — confirmLabel/cancelLabel đúng, nêu giá trị cũ → mới và câu Esc', async () => {
    confirmMock.mockResolvedValue(false)
    //  Loại 3 (Bổ nhiệm) + phòng KHÁC hồ sơ hiện tại (20).
    renderDialog({ event_type: 3, from_date: TODAY, to_date: '', department_id: 999 })

    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    await waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1))
    const options = confirmMock.mock.calls[0][0] as {
      confirmLabel?: string
      cancelLabel?: string
      message?: string
    }
    expect(options.confirmLabel).toBe('Lưu và cập nhật hồ sơ')
    expect(options.cancelLabel).toBe('Chỉ lưu dòng')
    expect(options.message).toContain('Phòng ban:')
    expect(options.message).toContain('→')
    //  Esc/đóng hộp phải nói rõ hệ quả — chọn phương án "nói rõ trong câu" (M6).
    expect(options.message?.toLowerCase()).toContain('chỉ lưu dòng')
  })

  it('M6 — có dòng CHÍNH khác hiệu lực muộn hơn (nhập bù lịch sử cũ) → KHÔNG hỏi, lưu thẳng không áp hồ sơ', async () => {
    const laterMainRow: EmployeeWorkHistory = {
      id: 99,
      employee_id: 1,
      event_type: 3,
      from_date: '2026-12-01',
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
    renderDialog(
      { event_type: 3, from_date: TODAY, to_date: '', department_id: 999 },
      { allRows: [laterMainRow] },
    )

    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(confirmMock).not.toHaveBeenCalled()
    const call = mutateAsync.mock.calls[0][0] as { payload: { apply_to_profile: boolean } }
    expect(call.payload.apply_to_profile).toBe(false)
  })
})

describe('EmployeeWorkHistoryFormDialog — M4 (ẩn vùng tệp khi can_open_files=false)', () => {
  it('canOpenFiles=false + TẠO MỚI → không vùng thả tệp, không cả nhãn «Tệp QĐ» trống hoác', () => {
    renderDialog({ event_type: 9, from_date: TODAY, to_date: '' }, { canOpenFiles: false })

    expect(screen.queryByText(/Kéo tệp QĐ vào đây/)).not.toBeInTheDocument()
    expect(screen.queryByText('Tệp QĐ')).not.toBeInTheDocument()
  })

  it('canOpenFiles=true + TẠO MỚI → CÓ vùng thả tệp (không hồi quy)', () => {
    renderDialog({ event_type: 9, from_date: TODAY, to_date: '' }, { canOpenFiles: true })

    expect(screen.getByText(/Kéo tệp QĐ vào đây/)).toBeInTheDocument()
  })

  it('canOpenFiles=false + SỬA dòng có sẵn (có tệp) → không nút «Quản lý tệp», chỉ báo số lượng', () => {
    renderDialog(
      { event_type: 9, from_date: TODAY, to_date: '' },
      { canOpenFiles: false, row: workHistoryRow({ file_count: 2 }) },
    )

    expect(screen.queryByRole('button', { name: /Quản lý tệp/ })).not.toBeInTheDocument()
    expect(screen.getByText(/Có 2 tệp đính kèm/)).toBeInTheDocument()
  })

  it('canOpenFiles=false + SỬA dòng KHÔNG có tệp → không hiện gì (không cả nhãn trống)', () => {
    renderDialog(
      { event_type: 9, from_date: TODAY, to_date: '' },
      { canOpenFiles: false, row: workHistoryRow({ file_count: 0 }) },
    )

    expect(screen.queryByText('Tệp QĐ')).not.toBeInTheDocument()
  })

  it('canOpenFiles=true + SỬA dòng có sẵn → CÓ nút «Quản lý tệp» (không hồi quy)', () => {
    renderDialog(
      { event_type: 9, from_date: TODAY, to_date: '' },
      { canOpenFiles: true, row: workHistoryRow() },
    )

    expect(screen.getByRole('button', { name: /Quản lý tệp/ })).toBeInTheDocument()
  })
})

describe('EmployeeWorkHistoryFormDialog — M5 (nạp lại danh sách sau khi tải tệp)', () => {
  it('tạo dòng rồi tải tệp xong → invalidate khóa danh sách quá trình công tác của nhân sự đó', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')
    renderDialog({ event_type: 9, from_date: TODAY, to_date: '' }, { queryClient })

    const fileInput = document.querySelector('input[type="file"]')
    if (!fileInput) throw new Error('Không thấy input chọn tệp')
    const file = new File(['noi dung'], 'quyet-dinh.pdf', { type: 'application/pdf' })
    fireEvent.change(fileInput, { target: { files: [file] } })

    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    await waitFor(() => expect(uploadWorkHistoryFilesMock).toHaveBeenCalledTimes(1))
    expect(uploadWorkHistoryFilesMock.mock.calls[0]).toEqual([123, [file]])

    await waitFor(() =>
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: queryKeys.hr.employeeWorkHistory(1) }),
    )
  })

  it('canOpenFiles=false → không hàng đợi tệp, không gọi uploadWorkHistoryFiles dù đã lưu xong', async () => {
    renderDialog({ event_type: 9, from_date: TODAY, to_date: '' }, { canOpenFiles: false })

    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(uploadWorkHistoryFilesMock).not.toHaveBeenCalled()
  })
})
