import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import type { ChartDatum } from '@/shared/ui/chart'
import type { DonutSlice } from '@/shared/ui/donut-chart'
import {
  buildStatusSlices,
  countProfileGaps,
  countRecentHires,
  groupCount,
  type ProfileGaps,
} from '../utils/hr-overview-metrics'
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

/** Cửa sổ tính "mới vào" của thẻ số liệu. */
export const NEW_HIRE_DAYS = 30

/** Số dòng tối đa của thẻ "Nhân sự theo pháp nhân" — xem chú thích ở `byCompany`. */
const COMPANY_BARS = 8

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

export interface HrOverview {
  stats: {
    active: number
    inactive: number
    departments: number
    companies: number
    newHires: number
  }
  /**
   * Dòng phụ của thẻ "Đang làm việc" — `undefined` khi hai danh mục còn đang
   * tải HOẶC người xem không có quyền đọc chúng. Ghép sẵn ở đây vì chỉ nơi này
   * biết khóa nào đọc được: dựng ở tầng thẻ thì thiếu quyền sẽ ra "0 phòng ban".
   */
  orgHint?: string
  byDepartment: ChartDatum[]
  byCompany: ChartDatum[]
  byStatus: DonutSlice[]
  gaps: ProfileGaps
  accounts: AccountCoverage
  isLoading: boolean
  isLoadingAccounts: boolean
  canReadEmployees: boolean
  canReadAccounts: boolean
}

/**
 * Dữ liệu người & tổ chức cho trang Tổng quan Nhân sự.
 *
 * Phần nghỉ phép nằm ở `use-hr-leave-glance.ts` — hai nguồn, hai bộ quyền, và
 * gộp một hook thì màn hình thiếu `leave_request.read` phải chờ luôn cả khối
 * hồ sơ.
 */
export function useHrOverview(): HrOverview {
  const { can } = usePermission()
  const canReadEmployees = can('employee', 'read')
  const canReadAccounts = can('user', 'read')
  const canReadDepartments = can('department', 'read')
  const canReadCompanies = can('company', 'read')

  const employeesQuery = useEmployees(
    { page_size: FULL_LIST_PAGE_SIZE },
    { enabled: canReadEmployees },
  )
  //  `page_size: 1` — chỉ lấy `total` để đếm danh mục. Tên pháp nhân của biểu đồ
  //  đọc thẳng `Employee.company_name` (backend gửi kèm), nên không cần kéo cả
  //  danh sách công ty về nữa. Bản cũ kéo về rồi tra bảng, và vì lọc
  //  `is_active: true` nên nhân sự thuộc pháp nhân đã ngừng dùng bị dồn hết vào
  //  cột "Chưa gán pháp nhân".
  const companiesQuery = useCompanies({ page_size: 1 }, { enabled: canReadCompanies })
  const departmentsQuery = useDepartments(
    { page_size: 1, is_active: true },
    { enabled: canReadDepartments },
  )
  const usersQuery = useUserAccounts(
    { page_size: FULL_LIST_PAGE_SIZE },
    { enabled: canReadAccounts },
  )

  const employees = useMemo(() => employeesQuery.data?.items ?? [], [employeesQuery.data])
  const activeEmployees = useMemo(
    () => employees.filter((employee) => employee.is_active),
    [employees],
  )

  const byDepartment = useMemo(
    () =>
      groupCount(activeEmployees, (employee) =>
        employee.department_name?.trim() ? employee.department_name.trim() : 'Chưa gán phòng ban',
      ),
    [activeEmployees],
  )

  //  Ít dòng hơn thẻ phòng ban: tập đoàn có hàng chục pháp nhân mà phần đuôi
  //  toàn 1 người, liệt kê hết thì thẻ cao gấp rưỡi hai thẻ nằm cùng hàng và
  //  chừa lại một mảng trắng bên cạnh. Phần bị gom vẫn hiện thành dòng
  //  "Khác (n mục)", không cắt lặng lẽ.
  const byCompany = useMemo(
    () =>
      groupCount(
        activeEmployees,
        (employee) =>
          employee.company_name?.trim() ? employee.company_name.trim() : 'Chưa gán pháp nhân',
        COMPANY_BARS,
      ),
    [activeEmployees],
  )

  const byStatus = useMemo(() => buildStatusSlices(employees), [employees])
  const gaps = useMemo(() => countProfileGaps(employees), [employees])
  //  Mốc "hôm nay" chốt MỘT LẦN cho cả lượt render: gọi `new Date()` trong hàm
  //  đếm thì hai thẻ cạnh nhau có thể rơi vào hai ngày khác nhau lúc nửa đêm.
  const newHires = useMemo(
    () => countRecentHires(employees, new Date(), NEW_HIRE_DAYS),
    [employees],
  )

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

  const departments = departmentsQuery.data?.total ?? 0
  const companies = companiesQuery.data?.total ?? 0
  const orgParts = [
    canReadDepartments && !departmentsQuery.isPending ? `${departments} phòng ban` : '',
    canReadCompanies && !companiesQuery.isPending ? `${companies} pháp nhân` : '',
  ].filter(Boolean)

  return {
    stats: {
      active: activeEmployees.length,
      inactive: employees.length - activeEmployees.length,
      departments,
      companies,
      newHires,
    },
    orgHint: orgParts.length > 0 ? orgParts.join(' · ') : undefined,
    byDepartment,
    byCompany,
    byStatus,
    gaps,
    accounts,
    /** Chỉ true ở lần tải đầu — refetch giữ nguyên khung, không nháy skeleton. */
    isLoading: canReadEmployees && employeesQuery.isPending,
    isLoadingAccounts: canReadAccounts && usersQuery.isPending,
    canReadEmployees,
    canReadAccounts,
  }
}
