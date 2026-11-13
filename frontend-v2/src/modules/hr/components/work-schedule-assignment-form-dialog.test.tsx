import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { AuthUser } from '@/core/auth/auth-types'
import { WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG } from '../config/work-schedule-assignment-crud'
import { PERSONAL_ASSIGNMENT_HINT } from '../config/work-schedule-assignment-personal-config'
import { WORK_SCHEDULE_LEVEL_CODE, type WorkScheduleAssignment } from '../types/work-schedule'
import { withAssignmentPrefill } from '../utils/work-schedule-assignment-prefill'
import { WorkScheduleAssignmentFormDialog } from './work-schedule-assignment-form-dialog'

const apiGet = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

let permissions: Record<string, string[]> = {}
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => permissions[entity]?.includes(action) ?? false,
  }),
}))
//  `PermissionGate` của khung CRUD đọc quyền qua cùng hook — đã mock ở trên.

const SELF = 42
const SELF_USER = 1
const HEAD = { work_schedule: ['read'], work_schedule_personal: ['read', 'create', 'write', 'delete'] }
const HR = { work_schedule: ['read', 'create', 'write', 'delete'] }

function row(patch: Partial<WorkScheduleAssignment> = {}): WorkScheduleAssignment {
  return {
    id: 5,
    target_level: WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE,
    target_level_label: 'Nhân sự',
    target_id: 12,
    target_name: 'NV012 — Lê Văn A',
    schedule_id: 3,
    schedule_name: 'Hành chính T2–T6',
    //  Xa trong tương lai: bài kiểm không phụ thuộc hôm nay; dòng "đã bắt đầu" khai riêng ngày 2020.
    effective_from: '2099-01-01',
    effective_to: null,
    note: '',
    is_current: true,
    created_by: SELF_USER,
    ...patch,
  }
}

function renderDialog(item?: WorkScheduleAssignment, config = WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <WorkScheduleAssignmentFormDialog open onOpenChange={vi.fn()} config={config} item={item} />
    </QueryClientProvider>,
  )
}

describe('WorkScheduleAssignmentFormDialog (duoc-CR-757 lượt 2)', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiGet.mockImplementation(async (url: string) => {
      if (url === '/api/work-schedule-assignments/tools/assignable-employees') {
        //  Backend đã bỏ chính người gọi; vẫn gửi kèm để thử lớp chặn thứ hai ở giao diện.
        return {
          total: 2,
          items: [
            { id: 12, code: 'NV012', full_name: 'Lê Văn A', department_name: 'Kế toán' },
            { id: SELF, code: 'NV042', full_name: 'Trưởng Phòng B', department_name: 'Kế toán' },
          ],
        }
      }
      if (url === '/api/employees') {
        return {
          items: [
            { id: 12, code: 'NV012', full_name: 'Lê Văn A' },
            { id: SELF, code: 'NV042', full_name: 'Trưởng Phòng B' },
          ],
        }
      }
      if (url === '/api/work-schedules') return { items: [{ id: 3, name: 'Hành chính T2–T6' }], total: 1 }
      return { items: [] }
    })
    useAuthStore.setState({ user: { id: SELF_USER, email: '', full_name: 'TP', employee_id: SELF } as AuthUser })
    permissions = {}
  })

  it('HR keeps the full level picker and the plain hint', () => {
    permissions = HR
    renderDialog()
    expect(screen.getByRole('combobox', { name: /Cấp áp dụng/ })).toBeInTheDocument()
    expect(screen.queryByText(PERSONAL_ASSIGNMENT_HINT)).not.toBeInTheDocument()
  })

  it('personal mode locks the level to Nhân sự as read-only text and explains the limit', () => {
    permissions = HEAD
    renderDialog()
    expect(screen.queryByRole('combobox', { name: /Cấp áp dụng/ })).not.toBeInTheDocument()
    expect(screen.getByText('Nhân sự')).toBeInTheDocument()
    expect(screen.getByText(PERSONAL_ASSIGNMENT_HINT)).toBeInTheDocument()
  })

  it('personal mode never lists the user own employee record as a target', async () => {
    const user = userEvent.setup()
    permissions = HEAD
    renderDialog()
    await waitFor(() =>
      expect(apiGet).toHaveBeenCalledWith('/api/work-schedule-assignments/tools/assignable-employees', expect.anything()),
    )
    //  Không đi nguồn nhân sự theo quyền ĐỌC (rộng hơn phạm vi gán).
    expect(apiGet).not.toHaveBeenCalledWith('/api/employees', expect.anything())
    await user.click(screen.getByRole('combobox', { name: /Đối tượng áp dụng/ }))
    //  Mục của SearchSelect là nút trong khung thả xuống.
    expect(await screen.findByRole('button', { name: /Lê Văn A/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Trưởng Phòng B/ })).not.toBeInTheDocument()
  })

  it('a department prefill reaching personal mode drops the department id instead of reusing it as an employee id', () => {
    permissions = HEAD
    const prefilled = withAssignmentPrefill(WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG, {
      level: WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT,
      targetId: 12,
      targetName: 'Phòng Kế toán',
    })
    renderDialog(undefined, prefilled)
    expect(screen.getByText('Nhân sự')).toBeInTheDocument()
    expect(screen.queryByDisplayValue('Phòng Kế toán')).not.toBeInTheDocument()
    expect(screen.queryByDisplayValue('#12')).not.toBeInTheDocument()
  })

  it('a self prefill in personal mode is dropped too', () => {
    permissions = HEAD
    const prefilled = withAssignmentPrefill(WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG, {
      level: WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE,
      targetId: SELF,
      targetName: 'NV042 — Trưởng Phòng B',
    })
    renderDialog(undefined, prefilled)
    expect(screen.queryByDisplayValue('NV042 — Trưởng Phòng B')).not.toBeInTheDocument()
  })

  it('personal mode edits and deletes a colleague employee-level row', () => {
    permissions = HEAD
    renderDialog(row())
    expect(screen.getByRole('button', { name: 'Lưu thay đổi' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Xóa' })).toBeInTheDocument()
  })

  it('personal mode only views a department row: no save, no delete, says why', () => {
    permissions = HEAD
    renderDialog(
      row({
        target_level: WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT,
        target_level_label: 'Phòng ban',
        target_id: 3,
        target_name: 'Phòng Kế toán',
      }),
    )
    expect(screen.getByText('Phòng Kế toán')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu thay đổi' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
    expect(screen.getByText(/do Nhân sự cấu hình/)).toBeInTheDocument()
  })

  it('personal mode only views the user own row', () => {
    permissions = HEAD
    renderDialog(row({ target_id: SELF, target_name: 'NV042 — Trưởng Phòng B' }))
    expect(screen.queryByRole('button', { name: 'Lưu thay đổi' })).not.toBeInTheDocument()
  })

  it('personal create without write: existing rows open view-only', () => {
    permissions = { work_schedule_personal: ['create'] }
    renderDialog(row())
    expect(screen.queryByRole('button', { name: 'Lưu thay đổi' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Đóng' })).toBeInTheDocument()
  })

  it('personal write without delete: edit yes, delete button no', () => {
    permissions = { work_schedule_personal: ['write'] }
    renderDialog(row())
    expect(screen.getByRole('button', { name: 'Lưu thay đổi' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
  })

  it('HR still edits a department row and deletes it as before', () => {
    permissions = HR
    renderDialog(row({ target_level: WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT, target_id: 3 }))
    expect(screen.getByRole('button', { name: 'Lưu thay đổi' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Xóa' })).toBeInTheDocument()
  })

  it('a plain reader (no write key) gets the view-only dialog', () => {
    permissions = { work_schedule: ['read'] }
    renderDialog(row())
    expect(screen.queryByRole('button', { name: 'Lưu thay đổi' })).not.toBeInTheDocument()
    expect(screen.getByText('Bạn chỉ có quyền xem dòng gán lịch này.')).toBeInTheDocument()
  })

  it('personal mode only views a colleague row assigned by someone else', () => {
    permissions = HEAD
    renderDialog(row({ created_by: 77 }))
    expect(screen.queryByRole('button', { name: 'Lưu thay đổi' })).not.toBeInTheDocument()
    expect(screen.getByText(/do chính mình gán/)).toBeInTheDocument()
  })

  it('personal mode on its own STARTED row: only end date + note editable, no delete, says why', async () => {
    const user = userEvent.setup()
    permissions = HEAD
    renderDialog(row({ effective_from: '2020-01-01' }))
    expect(screen.getByText('Lịch đã bắt đầu: chỉ đặt được ngày kết thúc và ghi chú.')).toBeInTheDocument()
    expect(screen.getByText('Lịch đã bắt đầu, không xóa được — hãy đặt ngày kết thúc.')).toBeInTheDocument()
    //  Đối tượng, mẫu lịch, ngày bắt đầu: chữ chỉ xem, không còn ô chọn.
    expect(screen.queryByRole('combobox', { name: /Đối tượng áp dụng/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: /Mẫu lịch/ })).not.toBeInTheDocument()
    expect(screen.getByText('01/01/2020')).toBeInTheDocument()
    expect(screen.getByText(/Ngày kết thúc của lịch đã bắt đầu phải từ hôm qua trở đi/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
    //  Ngày bắt đầu đã qua nhưng bị khóa → không bị luật "từ hôm nay" chặn oan khi lưu ghi chú.
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('personal mode on a not-started row that replaced another: target + start locked, schedule still editable', () => {
    permissions = HEAD
    renderDialog(row({ replaces_previous: true }))
    expect(screen.getByText(/đã thay lịch trước đó/)).toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: /Đối tượng áp dụng/ })).not.toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /Mẫu lịch/ })).toBeInTheDocument()
    expect(screen.getByText('01/01/2099')).toBeInTheDocument()
    //  Chưa bắt đầu → vẫn xóa được (xóa rồi tạo lại là lối đổi người / ngày).
    expect(screen.getByRole('button', { name: 'Xóa' })).toBeInTheDocument()
  })

  it('HR on a started row keeps every field editable', () => {
    permissions = HR
    renderDialog(row({ effective_from: '2020-01-01', replaces_previous: true }))
    expect(screen.getByRole('combobox', { name: /Đối tượng áp dụng/ })).toBeInTheDocument()
    expect(screen.queryByText(/Lịch đã bắt đầu/)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Xóa' })).toBeInTheDocument()
  })

  it('personal create with a start date before today is blocked on the form with the backend sentence', async () => {
    const user = userEvent.setup()
    permissions = HEAD
    //  Ô chọn ngày không gõ tay được: đưa ngày lùi vào qua giá trị mặc định của cấu hình.
    const base = WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG
    const fields = Array.isArray(base.formFields) ? base.formFields : []
    const pastDefault = {
      ...base,
      formFields: fields.map((f) => (f.name === 'effective_from' ? { ...f, defaultValue: '2020-01-01' } : f)),
    }
    renderDialog(undefined, pastDefault)
    await user.click(screen.getByRole('button', { name: 'Tạo mới' }))
    expect(await screen.findByText('Ngày hiệu lực phải từ hôm nay trở đi', { selector: '[role="alert"]' })).toBeInTheDocument()
  })

  it('personal create defaults the start date to today', () => {
    permissions = HEAD
    renderDialog()
    const today = new Date()
    const shown = `${String(today.getDate()).padStart(2, '0')}/${String(today.getMonth() + 1).padStart(2, '0')}/${today.getFullYear()}`
    expect(screen.getByText(shown)).toBeInTheDocument()
  })
})
