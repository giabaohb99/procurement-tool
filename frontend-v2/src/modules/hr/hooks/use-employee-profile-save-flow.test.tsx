import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { EMPTY_EMPLOYEE_PROFILE_FORM, type EmployeeProfileFormValues } from '../schemas/employee-schema'
import type { EmployeeDetail } from '../types/employee'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
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

function concurrent(id: number, companyId: number, status: number, fromDate = '2026-01-01'): EmployeeConcurrent {
  return {
    id,
    employee_id: 1,
    company_id: companyId,
    company_name: '',
    department_id: id,
    department_name: `Phòng ${id}`,
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

describe('useEmployeeProfileSaveFlow — company change (duoc-CR-755)', () => {
  it('company changes and old company still has live rows → asks first, sends nothing yet', async () => {
    listMock.mockResolvedValue({ items: [concurrent(7, 10, 2), concurrent(8, 10, 3), concurrent(9, 11, 2)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    expect(mutateAsync).not.toHaveBeenCalled()
    //  Chỉ dòng chưa hết hạn ở công ty CŨ: dòng 8 đã hết, dòng 9 ở công ty khác.
    expect(result.current.pendingCompany?.rows.map((r) => r.id)).toEqual([7])
  })

  it('answer is carried into the PATCH body: end_old_company_concurrent + keep_concurrent_ids', async () => {
    listMock.mockResolvedValue({ items: [concurrent(7, 10, 2), concurrent(8, 10, 1, '2027-01-01')] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    act(() => result.current.answerCompanyChange({ end_old_company_concurrent: true, keep_concurrent_ids: [8] }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(sentBody()).toMatchObject({ company_id: 11, end_old_company_concurrent: true, keep_concurrent_ids: [8] })
    expect(result.current.pendingCompany).toBeNull()
  })

  it('no live rows at the old company → saves straight away without control flags', async () => {
    listMock.mockResolvedValue({ items: [concurrent(8, 10, 3), concurrent(9, 11, 2)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    expect(result.current.pendingCompany).toBeNull()
    expect(mutateAsync).toHaveBeenCalledTimes(1)
    expect(sentBody()).not.toHaveProperty('end_old_company_concurrent')
    expect(sentBody()).not.toHaveProperty('keep_concurrent_ids')
  })

  it('company unchanged → never fetches the concurrent list', async () => {
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ full_name: 'Tên mới' })))
    expect(listMock).not.toHaveBeenCalled()
    expect(mutateAsync).toHaveBeenCalledTimes(1)
  })

  it('removing the company (→ 0) does not ask: backend keeps every row in that case', async () => {
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 0 })))
    expect(listMock).not.toHaveBeenCalled()
    expect(mutateAsync).toHaveBeenCalledTimes(1)
  })

  it('list fails to load → does NOT save silently (the backend default would end every row)', async () => {
    listMock.mockRejectedValue(new Error('network'))
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11 })))
    expect(mutateAsync).not.toHaveBeenCalled()
    expect(result.current.pendingCompany).toBeNull()
  })

  it('department + company change: keep-old-department answer survives into the company step and the PATCH', async () => {
    listMock.mockResolvedValue({ items: [concurrent(7, 10, 2)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11, department_id: 30 })))
    expect(result.current.pendingDepartment).not.toBeNull()
    act(() => result.current.answerKeepOldDepartment(true))
    await waitFor(() => expect(result.current.pendingCompany).not.toBeNull())
    act(() => result.current.answerCompanyChange({ end_old_company_concurrent: false, keep_concurrent_ids: [] }))
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(sentBody()).toMatchObject({ keep_old_department: true, end_old_company_concurrent: false, keep_concurrent_ids: [] })
  })

  it('company change to a resigned status: company answer waits behind the leave confirmation, then is sent', async () => {
    listMock.mockResolvedValue({ items: [concurrent(7, 10, 2)] })
    const { result } = setup()
    await act(() => result.current.onSubmit(values({ company_id: 11, status: 'resigned' })))
    act(() => result.current.answerCompanyChange({ end_old_company_concurrent: true, keep_concurrent_ids: [] }))
    await waitFor(() => expect(result.current.pendingLeave).not.toBeNull())
    expect(mutateAsync).not.toHaveBeenCalled()
    act(() => result.current.confirmLeave())
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
    expect(sentBody()).toMatchObject({ status: 'resigned', end_old_company_concurrent: true, keep_concurrent_ids: [] })
  })
})
