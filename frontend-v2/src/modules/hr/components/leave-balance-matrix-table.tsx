import { Download } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import type { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Button } from '@/shared/ui/button'
import { SearchField } from '@/shared/ui/search-field'
import { leaveBalanceMatrixApi, type LeaveBalanceMatrixParams } from '../api/leave-balance-matrix-api'
import { useDepartments } from '../hooks/use-departments'
import { useLeaveBalanceMatrix } from '../hooks/use-leave-balance-matrix'
import { useSingleFlight } from '../hooks/use-single-flight'
import {
  MATRIX_ALL_DEPARTMENTS as ALL_DEPARTMENTS,
  MATRIX_STATUS_OPTIONS as STATUS_OPTIONS,
  MATRIX_STATUS_WORKING as STATUS_WORKING,
} from '../utils/leave-balance-matrix-filters'
import { LIST_TOOLBAR_STICKY } from '../utils/list-sticky'
import { LeaveBalanceMatrixCard } from './leave-balance-matrix-card'
import { buildLeaveBalanceMatrixColumns } from './leave-balance-matrix-columns'
import { LeaveBalanceMatrixFilters } from './leave-balance-matrix-filters'

interface LeaveBalanceMatrixTableProps {
  year: string
  onYearChange: (year: string) => void
  /** Ô tìm `?q=` — MỘT chủ ở màn cha, dùng chung hai thẻ (review L9). */
  search: ReturnType<typeof useUrlSearchParam>
}

/**
 * Thẻ "Theo nhân sự" của màn Quỹ phép năm (duoc-CR-717, D9a): mỗi người một dòng, mỗi loại nghỉ
 * một cột, ô = số ngày còn dùng được, cột Tổng. Trả lời câu *"anh A còn mấy ngày mỗi loại"* trong
 * một hàng — bảng "Theo dòng quỹ" phải bung từng người mới đọc được.
 *
 * Phân trang ở BACKEND theo người (không như thẻ dòng quỹ kéo trọn về rồi cắt ở client). Cột không
 * đổi theo trang — backend tính cột trên cả kết quả. Mọi bộ lọc nằm trên URL; `view` được giữ khi
 * bấm "Xóa lọc" để không bị đá về thẻ kia.
 */
export function LeaveBalanceMatrixTable({ year, onYearChange, search }: LeaveBalanceMatrixTableProps) {
  const { can } = usePermission()
  const canReadDepartment = can('department', 'read')
  const canExport = can('leave_balance', 'export')
  const { value: keyword, setValue: setKeyword, debouncedValue } = search
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL_DEPARTMENTS)
  const [rawStatus, setStatus] = useUrlParamState('employee_status', STATUS_WORKING)
  //  Link gõ tay `?employee_status=xyz`: coi như mặc định, không gửi giá trị lạ cho backend ăn 422.
  const status = STATUS_OPTIONS.find((o) => o.value === rawStatus)?.value ?? STATUS_WORKING
  const [page, setPage] = usePageResetOnFilterChange([debouncedValue, year, departmentId, status])
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [exporting, setExporting] = useState(false)
  const runOnce = useSingleFlight()

  const { data: departments } = useDepartments(
    { page_size: 500, is_active: true },
    { enabled: canReadDepartment },
  )

  const filters = useMemo<LeaveBalanceMatrixParams>(() => {
    const p: LeaveBalanceMatrixParams = { year: Number(year) }
    if (debouncedValue) p.search = debouncedValue
    const dept = Number(departmentId)
    if (departmentId !== ALL_DEPARTMENTS && Number.isInteger(dept) && dept > 0) p.department_id = dept
    if (status !== STATUS_WORKING) p.employee_status = status
    return p
  }, [year, debouncedValue, departmentId, status])

  const { data, isLoading, isError } = useLeaveBalanceMatrix({ ...filters, page, page_size: pageSize })
  const typeColumns = useMemo(() => data?.columns ?? [], [data])
  const columns = useMemo(() => buildLeaveBalanceMatrixColumns(typeColumns), [typeColumns])

  //  Chặn bấm đúp bằng cờ ref (`exporting` là state, đổi ở lượt render sau) — tệp 5000 người
  //  dựng mất vài giây, bấm hai lần là hai lượt dựng trên máy chủ và hai tệp tải về.
  const exportExcel = () =>
    runOnce((release) => {
      setExporting(true)
      leaveBalanceMatrixApi
        .exportExcel(filters)
        .catch(() => toast.error('Không xuất được tệp Excel.'))
        .finally(() => {
          setExporting(false)
          release()
        })
    })

  const filtering =
    Boolean(debouncedValue) || departmentId !== ALL_DEPARTMENTS || status !== STATUS_WORKING

  return (
    <DataTable
      fillHeight
      columns={columns}
      rows={data?.items}
      getRowId={(r) => r.employee_id}
      isLoading={isLoading}
      isError={isError}
      emptyMessage={
        filtering ? 'Không có nhân sự nào khớp bộ lọc.' : `Chưa có ai được cấp quỹ phép năm ${year}.`
      }
      storageKey="hr.leave-balances.matrix"
      toolbarClassName={LIST_TOOLBAR_STICKY}
      keepFilterParams={['view']}
      //  Hàng khóa theo `employee_id`, không có `id` — lúc bảng rỗng bảng không suy ra được điều
      //  đó và tự chèn cột "ID" trống (thấy tận mắt ở năm chưa cấp quỹ).
      idColumn={false}
      mobileCard={(row) => <LeaveBalanceMatrixCard row={row} columns={typeColumns} />}
      pagination={{
        page,
        pageSize,
        total: data?.total ?? 0,
        onPageChange: setPage,
        onPageSizeChange: setPageSize,
        unitLabel: 'nhân sự',
      }}
      toolbar={
        <>
          <SearchField
            value={keyword}
            onChange={setKeyword}
            placeholder="Tìm tên, mã nhân sự"
            className="md:max-w-xs md:min-w-56"
          />
          <LeaveBalanceMatrixFilters
            departments={canReadDepartment ? (departments?.items ?? []) : undefined}
            departmentId={departmentId}
            onDepartmentChange={setDepartmentId}
            status={status}
            onStatusChange={setStatus}
            year={year}
            onYearChange={onYearChange}
          />
        </>
      }
      toolbarEnd={
        canExport && (
          <Button
            variant="outline"
            size="sm"
            onClick={exportExcel}
            disabled={exporting || !data?.items.length}
            //  Khổ hẹp chỉ còn biểu tượng: nhãn đầy đủ ép ô tìm còn 3 chữ "Tìm" (thấy ở 390px).
            aria-label="Xuất Excel"
          >
            <Download className="size-4" />
            <span className="max-md:hidden">Xuất Excel</span>
          </Button>
        )
      }
    />
  )
}
