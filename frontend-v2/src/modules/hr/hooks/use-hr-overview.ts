import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { CHART_COLORS, CHART_NEUTRAL, type ChartDatum } from '@/shared/ui/chart'
import type { DonutSlice } from '@/shared/ui/donut-chart'
import type { Employee } from '../types/employee'
import { EMPLOYEE_STATUSES } from '../types/employee'
import { useCompanies } from './use-companies'
import { useDepartments } from './use-departments'
import { useEmployees } from './use-employees'
import { useUserAccounts } from './use-user-accounts'

/**
 * Hệ thống cỡ 20–100 người dùng nên kéo trọn danh sách về gom nhóm ở client rẻ
 * hơn nhiều so với việc thêm endpoint thống kê ở backend. Trần của backend là
 * 5000 dòng/trang.
 */
const FULL_LIST_PAGE_SIZE = 1000

/** Số hạng mục tối đa vẽ trên một biểu đồ cột; phần đuôi gom vào "Khác". */
const MAX_BARS = 12

export interface AccountCoverage {
  /** Nhân sự đang làm việc đã được cấp tài khoản đăng nhập. */
  withAccount: number
  /** Nhân sự đang làm việc chưa có tài khoản. */
  withoutAccount: number
  totalActive: number
  /** Tài khoản chưa được gán vai trò nào -> đăng nhập được nhưng không làm gì được. */
  noRole: number
  /** Tài khoản còn sống nhưng hồ sơ nhân sự đã bị xóa. */
  orphan: number
  totalAccounts: number
}

/**
 * Dữ liệu cho trang Tổng quan Nhân sự: 4 thẻ số liệu + 4 biểu đồ, gom từ đúng
 * bốn lời gọi danh sách (nhân viên, phòng ban, công ty, tài khoản).
 */
export function useHrOverview() {
  const { can } = usePermission()

  const employeesQuery = useEmployees({ page_size: FULL_LIST_PAGE_SIZE })
  const companiesQuery = useCompanies({ page_size: FULL_LIST_PAGE_SIZE, is_active: true })
  const departmentsQuery = useDepartments({ page_size: 1, is_active: true })
  const usersQuery = useUserAccounts(
    { page_size: FULL_LIST_PAGE_SIZE },
    { enabled: can('user', 'read') },
  )

  const employees = useMemo(() => employeesQuery.data?.items ?? [], [employeesQuery.data])
  const activeEmployees = useMemo(
    () => employees.filter((employee) => employee.is_active),
    [employees],
  )

  const companyNameById = useMemo(() => {
    const map = new Map<number, string>()
    for (const company of companiesQuery.data?.items ?? []) map.set(company.id, company.name)
    return map
  }, [companiesQuery.data])

  const byDepartment = useMemo(
    () =>
      groupCount(activeEmployees, (employee) =>
        employee.department_name?.trim() ? employee.department_name.trim() : 'Chưa gán phòng ban',
      ),
    [activeEmployees],
  )

  const byCompany = useMemo(
    () =>
      groupCount(
        activeEmployees,
        (employee) => companyNameById.get(employee.company_id) ?? 'Chưa gán pháp nhân',
      ),
    [activeEmployees, companyNameById],
  )

  const byStatus = useMemo(() => buildStatusSlices(employees), [employees])

  const accounts = useMemo<AccountCoverage>(() => {
    const users = usersQuery.data?.items ?? []
    const employeeIdsWithAccount = new Set(
      users.filter((user) => user.employee_id > 0).map((user) => user.employee_id),
    )
    const withAccount = activeEmployees.filter((employee) =>
      employeeIdsWithAccount.has(employee.id),
    ).length

    return {
      withAccount,
      withoutAccount: activeEmployees.length - withAccount,
      totalActive: activeEmployees.length,
      noRole: users.filter((user) => user.role_ids.length === 0).length,
      orphan: users.filter((user) => user.is_orphan).length,
      totalAccounts: users.length,
    }
  }, [usersQuery.data, activeEmployees])

  return {
    stats: {
      active: activeEmployees.length,
      inactive: employees.length - activeEmployees.length,
      departments: departmentsQuery.data?.total ?? 0,
      companies: companiesQuery.data?.total ?? 0,
    },
    byDepartment,
    byCompany,
    byStatus,
    accounts,
    /** Chỉ true ở lần tải đầu — refetch giữ nguyên khung, không nháy skeleton. */
    isLoading: employeesQuery.isPending,
    isLoadingCompanies: companiesQuery.isPending,
    isLoadingAccounts: usersQuery.isPending && can('user', 'read'),
    canReadAccounts: can('user', 'read'),
  }
}

/** Đếm theo khóa rồi xếp giảm dần; phần đuôi quá dài gom vào một cột "Khác". */
function groupCount(employees: Employee[], keyOf: (employee: Employee) => string): ChartDatum[] {
  const counter = new Map<string, number>()
  for (const employee of employees) {
    const key = keyOf(employee)
    counter.set(key, (counter.get(key) ?? 0) + 1)
  }

  const rows = [...counter.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value || a.label.localeCompare(b.label, 'vi'))

  if (rows.length <= MAX_BARS) return rows

  const head = rows.slice(0, MAX_BARS - 1)
  const tail = rows.slice(MAX_BARS - 1)
  return [...head, { label: `Khác (${tail.length} mục)`, value: sum(tail) }]
}

/**
 * Lát bánh theo trạng thái nhân sự. Màu bám THỨ TỰ CỐ ĐỊNH của
 * `EMPLOYEE_STATUSES`, không bám thứ hạng số lượng — có vậy "Chính thức" mới
 * luôn là một màu dù dữ liệu đổi. Trạng thái lạ (dữ liệu cũ, để trống) gom vào
 * "Khác" màu xám.
 */
function buildStatusSlices(employees: Employee[]): DonutSlice[] {
  const counter = new Map<string, number>()
  for (const employee of employees) {
    const status = employee.status?.trim() || 'Khác'
    const key = (EMPLOYEE_STATUSES as readonly string[]).includes(status) ? status : 'Khác'
    counter.set(key, (counter.get(key) ?? 0) + 1)
  }

  const slices: DonutSlice[] = EMPLOYEE_STATUSES.map((status, index) => ({
    label: status,
    value: counter.get(status) ?? 0,
    color: CHART_COLORS[index],
  }))

  const other = counter.get('Khác') ?? 0
  if (other > 0) slices.push({ label: 'Khác', value: other, color: CHART_NEUTRAL })

  // Bỏ lát rỗng để chú giải không liệt kê một loạt số 0.
  return slices.filter((slice) => slice.value > 0)
}

function sum(rows: ChartDatum[]): number {
  return rows.reduce((total, row) => total + row.value, 0)
}
