import { ReportDepartmentFilter } from './report-department-filter'
import { ReportEmployeeStatusFilter } from './report-employee-status-filter'

/** Ô lọc riêng của "Quỹ phép năm" (`ReportPageConfig.extraFilters` chỉ nhận MỘT component): phòng ban + trạng thái nhân sự. */
export function LeaveBalanceExtraFilters() {
  return (
    <>
      <ReportDepartmentFilter />
      <ReportEmployeeStatusFilter />
    </>
  )
}
