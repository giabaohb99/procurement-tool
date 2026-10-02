import { renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { SUBJECT_KIND } from '@/shared/access-subject/subject-kind'
import { useAccessSubjectOptions } from './use-access-subject-options'
import { useCompanies } from './use-companies'
import { useDepartments } from './use-departments'
import { useEmployees } from './use-employees'
import { useRoles } from './use-roles'

vi.mock('./use-employees', () => ({ useEmployees: vi.fn() }))
vi.mock('./use-departments', () => ({ useDepartments: vi.fn() }))
vi.mock('./use-companies', () => ({ useCompanies: vi.fn() }))
vi.mock('./use-roles', () => ({ useRoles: vi.fn() }))

/** Trả về giống `useQuery` thật — chỉ cần `data` + `isLoading` cho hook này. */
function queryResult<T>(data: T, isLoading = false) {
  return { data, isLoading }
}

function mockHrHooks({
  employees = [] as { id: number; full_name: string }[],
  departments = [] as { id: number; name: string; company_id: number; is_active: boolean }[],
  companies = [] as { id: number; name: string; short_name: string }[],
  roles = [] as { id: number; name: string }[],
  loading = { employees: false, departments: false, companies: false, roles: false },
} = {}) {
  vi.mocked(useEmployees).mockReturnValue(
    queryResult({ items: employees }, loading.employees) as unknown as ReturnType<typeof useEmployees>,
  )
  vi.mocked(useDepartments).mockReturnValue(
    queryResult({ items: departments }, loading.departments) as unknown as ReturnType<
      typeof useDepartments
    >,
  )
  vi.mocked(useCompanies).mockReturnValue(
    queryResult({ items: companies }, loading.companies) as unknown as ReturnType<typeof useCompanies>,
  )
  vi.mocked(useRoles).mockReturnValue(
    queryResult(roles, loading.roles) as unknown as ReturnType<typeof useRoles>,
  )
}

//  Phản hồi 24/09/2026: 272 dòng người đứng đầu vùi mất 18 phòng ban + 14 pháp
//  nhân, người dùng tưởng chỉ chia sẻ được cho từng người. Logic xếp thứ tự +
//  gắn tên pháp nhân vào phòng ban trùng tên từng nằm trong
//  `FolderShareSubjectPicker`, nay chuyển hẳn vào hook này cùng với dữ liệu.
describe('useAccessSubjectOptions', () => {
  it('xếp pháp nhân · phòng ban · vai trò LÊN TRƯỚC, người xuống cuối', () => {
    mockHrHooks({
      employees: [{ id: 1, full_name: 'Nhân viên Một' }],
      departments: [{ id: 7, name: 'Kế toán', company_id: 1, is_active: true }],
      companies: [{ id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', short_name: 'DEGO Holding' }],
      roles: [{ id: 3, name: 'Văn thư' }],
    })

    const { result } = renderHook(() => useAccessSubjectOptions())

    expect(result.current.options.map((o) => o.subject_kind)).toEqual([
      SUBJECT_KIND.company,
      SUBJECT_KIND.department,
      SUBJECT_KIND.role,
      SUBJECT_KIND.employee,
    ])
  })

  it('phòng ban trùng tên ở hai pháp nhân khác nhau được phân biệt bằng tên pháp nhân', () => {
    mockHrHooks({
      departments: [
        { id: 7, name: 'Kế toán', company_id: 1, is_active: true },
        { id: 8, name: 'Kế toán', company_id: 2, is_active: true },
      ],
      companies: [
        { id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', short_name: 'DEGO Holding' },
        { id: 2, name: 'CÔNG TY TNHH ABA', short_name: '' },
      ],
    })

    const { result } = renderHook(() => useAccessSubjectOptions())
    const labels = result.current.options
      .filter((o) => o.subject_kind === SUBJECT_KIND.department)
      .map((o) => o.label)

    expect(labels).toEqual(['Kế toán · DEGO Holding', 'Kế toán · CÔNG TY TNHH ABA'])
  })

  it('phòng ban đã giải thể (is_active=false) không được đưa vào danh mục', () => {
    mockHrHooks({
      departments: [
        { id: 7, name: 'Kế toán', company_id: 1, is_active: true },
        { id: 9, name: 'Phòng đã giải thể', company_id: 1, is_active: false },
      ],
    })

    const { result } = renderHook(() => useAccessSubjectOptions())

    expect(result.current.options.map((o) => o.label)).not.toContain('Phòng đã giải thể')
  })

  it('công ty không có tên viết tắt (short_name rỗng) thì dùng tên đầy đủ làm nhãn', () => {
    mockHrHooks({
      companies: [{ id: 2, name: 'CÔNG TY TNHH ABA', short_name: '' }],
    })

    const { result } = renderHook(() => useAccessSubjectOptions())

    expect(result.current.options[0]).toEqual({
      subject_kind: SUBJECT_KIND.company,
      subject_id: 2,
      label: 'CÔNG TY TNHH ABA',
    })
  })

  it('loading=true khi còn BẤT KỲ danh mục nào chưa tải xong', () => {
    mockHrHooks({ loading: { employees: false, departments: true, companies: false, roles: false } })

    const { result } = renderHook(() => useAccessSubjectOptions())

    expect(result.current.loading).toBe(true)
  })

  it('loading=false khi cả bốn danh mục đã về (kể cả khi RỖNG)', () => {
    mockHrHooks()

    const { result } = renderHook(() => useAccessSubjectOptions())

    expect(result.current.loading).toBe(false)
    expect(result.current.options).toEqual([])
  })
})
