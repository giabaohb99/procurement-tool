import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { EMPLOYEE_CHANGE_REQUEST_STATUS } from '@/shared/constants/statuses'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Card } from '@/shared/ui/card'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'
import { EmployeeChangeRequestStatusBadge } from '../components/employee-change-request-status-badge'
import {
  useChangeRequestPendingCount,
  useChangeRequests,
} from '../hooks/use-employee-change-requests'
import type { EmployeeChangeRequest } from '../types/employee-change-request'
import { CHANGE_REQUEST_STATUS } from '../utils/employee-change-request-status'
import {
  countChangedFields,
  listChangedGroups,
} from '../utils/employee-change-request-review'

/** Mục «tất cả» — Radix cấm option value rỗng; mã trạng thái là 1..4 nên chữ này không đụng mã thật. */
const ALL = 'all'
/** Mặc định «Chờ duyệt»: người ta mở màn này để xử lý việc đang treo. */
const DEFAULT_STATUS = String(CHANGE_REQUEST_STATUS.PENDING)

/** Câu bảng rỗng phân biệt «rỗng vì bộ lọc» với «chưa có gì» (bẫy thứ ba của bảng có bộ lọc). */
function describeEmpty(keyword: string, status: string): string {
  if (keyword) return 'Không có đề nghị nào khớp từ khóa tìm.'
  if (status === DEFAULT_STATUS) return 'Không còn đề nghị nào chờ duyệt.'
  if (status !== ALL) return 'Không có đề nghị nào ở trạng thái này.'
  return 'Chưa có nhân viên nào gửi đề nghị sửa hồ sơ.'
}

/**
 * «Duyệt sửa hồ sơ» — danh sách đề nghị sửa hồ sơ nhân viên tự khai (duoc-CR-676, C6).
 *
 * Gác `employee.write` ở HAI lớp: mục menu (cũng là hàng rào route, vì gác điều hướng mặc định
 * MỞ) và kiểm lại ngay trong trang. Backend vẫn là chốt chặn thật.
 */
export function ProfileChangeRequestListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canReview = can('employee', 'write')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', DEFAULT_STATUS)
  const [pageSize, setPageSize] = useState(20)
  const [page, setPage] = usePageResetOnFilterChange([debouncedValue, status, pageSize])

  const params: ListParams = {
    page,
    page_size: pageSize,
    ...(debouncedValue ? { q: debouncedValue } : {}),
    ...(status !== ALL ? { status: Number(status) } : {}),
  }
  const { data, isLoading, isError } = useChangeRequests(params, canReview)
  const pendingCount = useChangeRequestPendingCount(canReview).data?.count ?? 0

  const columns = useMemo<DataTableColumn<EmployeeChangeRequest>[]>(
    () => [
      {
        key: 'employee_code',
        header: 'Mã NV',
        width: 120,
        hideable: false,
        cell: (row) => <span className="font-mono">{row.employee_code}</span>,
      },
      { key: 'employee_name', header: 'Họ tên', width: 220, hideable: false, cell: (row) => row.employee_name },
      {
        key: 'groups',
        header: 'Nhóm thay đổi',
        width: 240,
        wrap: true,
        cell: (row) => listChangedGroups(row).join(', '),
      },
      { key: 'count', header: 'Số trường', width: 100, align: 'right', cell: (row) => countChangedFields(row) },
      { key: 'created_at', header: 'Ngày gửi', width: 160, cell: (row) => formatDateTime(row.created_at) },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 130,
        cell: (row) => <EmployeeChangeRequestStatusBadge status={row.status} />,
      },
    ],
    [],
  )

  if (!canReview) {
    return (
      <ErrorState
        code="403"
        title="Không có quyền duyệt sửa hồ sơ"
        description="Màn này dành cho người được sửa hồ sơ nhân sự (quyền ghi Nhân sự)."
      />
    )
  }

  return (
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Duyệt sửa hồ sơ"
        description={
          pendingCount > 0
            ? `${pendingCount} đề nghị đang chờ duyệt. Duyệt xong thông tin mới được ghi vào hồ sơ.`
            : 'Đề nghị sửa thông tin cá nhân, ngân hàng, giấy tờ, hộ gia đình do nhân viên tự gửi.'
        }
      />
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(row) => row.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={describeEmpty(debouncedValue, status)}
          storageKey="hr.profile-change-requests"
          onRowClick={(row) => navigate(appRoutes.hr.profileChangeRequestDetail(row.id))}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'đề nghị',
          }}
          toolbar={
            <>
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm theo mã hoặc tên nhân viên…"
                placeholderShort="Mã, tên NV…"
                className="w-full max-w-xs"
              />
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44" aria-label="Trạng thái đề nghị">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {EMPLOYEE_CHANGE_REQUEST_STATUS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
