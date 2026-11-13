import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { EMPTY_EMPLOYEE_PROFILE_FORM, type EmployeeProfileFormValues } from '../schemas/employee-schema'
import type { EmployeeDetail } from '../types/employee'
import { CONCURRENT_KIND_COMPANY, CONCURRENT_KIND_DEPARTMENT, type EmployeeConcurrent } from '../types/employee-concurrent'
import { useEmployeeProfileSaveFlow } from './use-employee-profile-save-flow'

const mutateAsync = vi.fn()
vi.mock('./use-employees', () => ({
  useSaveEmployee: () => ({ mutateAsync, isPending: false }),
}))

const listMock = vi.fn()
vi.mock('../api/employee-concurrent-api', () => ({
  employeeConcurrentApi: { list: (...args: unknown[]) => listMock(...args) },
}))

const employee = {
  id: 1,
  company_id: 10,
  department_id: 20,
  status: 'official',
  is_active: true,
  extra_phones: [],
} as unknown as EmployeeDetail

/** Dòng kiêm nhiệm tối thiểu. `kind` mặc định Phòng ban; loại Công ty thì phòng = 0. */
function concurrent(
  id: number,
  companyId: number,
  status: number,
  { kind = CONCURRENT_KIND_DEPARTMENT, fromDate = '2026-01-01' }: { kind?: number; fromDate?: string } = {},
): EmployeeConcurrent {
  const isCompany = kind === CONCURRENT_KIND_COMPANY
  return {
    id,
    employee_id: 1,
    kind,
    kind_label: isCompany ? 'Công ty' : 'Phòng ban',
    company_id: companyId,
    company_name: '',
    department_id: isCompany ? 0 : id,
    department_name: isCompany ? '' : `Phòng ${id}`,
    position_id: 0,
    position_label: '',
    from_date: fromDate,
    to_date: null,
    decision_no: '',
    decision_date: null,
    note: '',
    counts_scope: true,
    work_history_id: 0,
    status,
    status_label: '',
    file_count: 0,
  }
}

function values(overrides: Partial<EmployeeProfileFormValues>): EmployeeProfileFormValues {
  return {
    ...EMPTY_EMPLOYEE_PROFILE_FORM,
    full_name: 'Trần Minh',
    company_id: 10,
    department_id: 20,
    status: 'official',
    is_active: true,
    ...overrides,
  }
}

function setup() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  return renderHook(
    () => {
      const form = useForm<EmployeeProfileFormValues>({ defaultValues: EMPTY_EMPLOYEE_PROFILE_FORM })
      return useEmployeeProfileSaveFlow({ employeeId: 1, employee, form, canReadSensitive: true })
    },
    { wrapper },
  )
}

function sentBody(): Record<string, unknown> {
  return mutateAsync.mock.calls[0][0].values as Record<string, unknown>
}

beforeEach(() => {
  mutateAsync.mockReset().mockResolvedValue({})
  listMock.mockReset()
})

const COMPANY = { kind: CONCURRENT_KIND_COMPANY }

describe('useEmployeeProfileSaveFlow — company change (duoc-CR-756)', () => {
  it('company A → C: asks first, sends nothing yet; ending rows = Phòng ban at A + Công ty at C, live only', async () => {
    listMock.mockResolvedValue({
      items: [
        concurrent(7, 10, 2), //  Phòng ban ở A, đang hiệu lực → kết thúc
        concurrent(8, 10, 3), //  Phòng ban ở A, đã hết → không đụng
        concurrent(9, 11, 2, COMPANY), //  Công ty trùng C → kết thúc
        concurrent(12, 12, 2, COMPANY), //  Công ty D khác → không đụng
      ],
    })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    expect(mutateAsync).not.toHaveBeenCalled()
    expect(result.current.pendingCompany?.rows.map((r) => r.id)).toEqual([7, 9])
    expect(result.current.pendingCompany?.oldCompanyKept).toBe(false)
  })

  it('answer is carried into the PATCH body as keep_old_company_concurrent — the CR-755 keys are never sent', async () => {
    listMock.mockResolvedValue({ items: [concurrent(7, 10, 2)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    act(() => result.current.answerCompanyChange({ keep_old_company_concurrent: true }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(sentBody()).toMatchObject({ company_id: 11, keep_old_company_concurrent: true })
    expect(sentBody()).not.toHaveProperty('keep_concurrent_ids')
    expect(sentBody()).not.toHaveProperty('end_old_company_concurrent')
    expect(result.current.pendingCompany).toBeNull()
  })

  it('nothing ends at all: still asks the "keep at old company" question (it is about the move, not about rows)', async () => {
    listMock.mockResolvedValue({ items: [concurrent(8, 10, 3), concurrent(12, 12, 2, COMPANY)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    expect(mutateAsync).not.toHaveBeenCalled()
    expect(result.current.pendingCompany?.rows).toEqual([])
  })

  it('already a live Công ty row at A and nothing ends → saves straight away, no flag (backend would skip anyway)', async () => {
    listMock.mockResolvedValue({ items: [concurrent(13, 10, 2, COMPANY)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    expect(result.current.pendingCompany).toBeNull()
    expect(mutateAsync).toHaveBeenCalledTimes(1)
    expect(sentBody()).not.toHaveProperty('keep_old_company_concurrent')
  })

  it('already a live Công ty row at A but rows end → asks, and tells the dialog A is already kept', async () => {
    listMock.mockResolvedValue({ items: [concurrent(13, 10, 1, COMPANY), concurrent(7, 10, 2)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    expect(result.current.pendingCompany?.rows.map((r) => r.id)).toEqual([7])
    expect(result.current.pendingCompany?.oldCompanyKept).toBe(true)
  })

  it('company unchanged → never fetches the concurrent list', async () => {
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ full_name: 'Tên mới' })))
    expect(listMock).not.toHaveBeenCalled()
    expect(mutateAsync).toHaveBeenCalledTimes(1)
  })

  it('removing the company (→ 0) does not ask', async () => {
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 0 })))
    expect(listMock).not.toHaveBeenCalled()
    expect(mutateAsync).toHaveBeenCalledTimes(1)
  })

  it('list fails to load → does NOT save silently (the question leads to deleting unstarted rows)', async () => {
    listMock.mockRejectedValue(new Error('network'))
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    expect(mutateAsync).not.toHaveBeenCalled()
    expect(result.current.pendingCompany).toBeNull()
  })

  it('company AND department change: the keep-old-department dialog is skipped, only the company question is asked', async () => {
    listMock.mockResolvedValue({ items: [concurrent(7, 10, 2)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11, department_id: 30 })))
    expect(result.current.pendingDepartment).toBeNull()
    expect(result.current.pendingCompany).not.toBeNull()
    act(() => result.current.answerCompanyChange({ keep_old_company_concurrent: true }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(sentBody()).toMatchObject({ company_id: 11, department_id: 30, keep_old_company_concurrent: true })
    //  Câu hỏi mở 5: gộp vào MỘT dòng loại Công ty — không gửi cờ giữ phòng cũ nữa.
    expect(sentBody()).not.toHaveProperty('keep_old_department')
  })

  it('department change inside the same company: keep-old-department dialog as before, no company question', async () => {
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ department_id: 30 })))
    expect(result.current.pendingDepartment).not.toBeNull()
    act(() => result.current.answerKeepOldDepartment(true))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(listMock).not.toHaveBeenCalled()
    expect(sentBody()).toMatchObject({ department_id: 30, keep_old_department: true })
    expect(sentBody()).not.toHaveProperty('keep_old_company_concurrent')
  })

  it('company change to a resigned status: company answer waits behind the leave confirmation, then is sent', async () => {
    listMock.mockResolvedValue({ items: [concurrent(7, 10, 2)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11, status: 'resigned' })))
    act(() => result.current.answerCompanyChange({ keep_old_company_concurrent: false }))
    await waitFor(() => expect(result.current.pendingLeave).not.toBeNull())
    expect(mutateAsync).not.toHaveBeenCalled()
    act(() => result.current.confirmLeave())
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(sentBody()).toMatchObject({ status: 'resigned', keep_old_company_concurrent: false })
  })
})
