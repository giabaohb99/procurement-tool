import { Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { useUrlSort } from '@/shared/hooks/use-url-sort'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { formatDate } from '@/shared/utils/format-date'
import { LeaveCompRequestCard } from '../components/leave-comp-request-card'
import { LeaveStatusBadge } from '../components/leave-status-badge'
import { approvalLifecycleRank } from '../utils/approval-lifecycle-rank'
import { formatCompDays } from '../utils/format-comp-days'
import { sortRowsByCell, type CellGetters } from '@/shared/utils/sort-rows-by-cell'
import { useLeaveCompRequests, useLeaveCompToApprove } from '../hooks/use-leave-comp'
import {
  LEAVE_COMP_STATUS,
  LEAVE_COMP_STATUS_LABELS,
  type LeaveCompRequest,
} from '../types/leave-comp'

const ALL = 'all'
const SCOPE = { MINE: 'mine', TO_APPROVE: 'to-approve', ALL: 'all' } as const
type Scope = (typeof SCOPE)[keyof typeof SCOPE]
const SCOPE_LABELS: Record<Scope, string> = {
  [SCOPE.MINE]: 'Của tôi',
  [SCOPE.TO_APPROVE]: 'Cần tôi duyệt',
  [SCOPE.ALL]: 'Tất cả trong phạm vi',
}

/**
 * Giá trị ô đang hiện của từng cột xếp được — dùng để xếp hàng đợi *Cần tôi duyệt* tại chỗ (endpoint
 * `/to-approve` trả hết, không nhận `sort_by`). Hai phạm vi còn lại xếp ở server theo cùng các khóa này
 * (`leave/comp_encashment_sort_expressions.py`, duoc-CR-744). `status` theo hạng dòng đời như máy chủ (duoc-CR-748).
 */
const COMP_SORT_GETTERS: CellGetters<LeaveCompRequest> = {
  id: (r) => r.id,
  code: (r) => r.code,
  employee_name: (r) => r.employee_name,
  work_date: (r) => r.work_date,
  days: (r) => r.days,
  status: (r) => approvalLifecycleRank(r.status),
  reason: (r) => r.reason,
  created_at: (r) => r.created_at,
}

/**
 * PHIẾU XIN NGHỈ BÙ — danh sách. Cùng cách chia phạm vi với màn Đơn nghỉ phép: ô "Phạm vi" chọn
 * *Của tôi* (GET list, lọc theo nhân sự đăng nhập) · *Cần tôi duyệt* (GET /to-approve, hàng đợi việc
 * của tôi, không phân trang) · *Tất cả trong phạm vi* (GET list theo phạm vi dữ liệu của vai trò).
 */
export function LeaveCompRequestListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { user } = useAuth()

  const [scopeParam, setScope] = useUrlParamState('scope', SCOPE.MINE)
  const scope: Scope = (Object.values(SCOPE) as string[]).includes(scopeParam)
    ? (scopeParam as Scope)
    : SCOPE.MINE
  const [status, setStatus] = useUrlParamState('status', ALL)
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const { sortBy, sortDir, handleSortChange } = useUrlSort()
  const [page, setPage] = usePageResetOnFilterChange([scope, status, debouncedValue, sortBy, sortDir])

  const employeeId = user?.employee_id
  const listParams = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue) p.q = debouncedValue
    if (status !== ALL) p.status = status
    if (scope === SCOPE.MINE && employeeId) p.employee_id = String(employeeId)
    if (sortBy) {
      p.sort_by = sortBy
      p.sort_dir = sortDir
    }
    return p
  }, [page, pageSize, debouncedValue, status, scope, employeeId, sortBy, sortDir])

  //  "Của tôi" mà tài khoản chưa gắn hồ sơ nhân sự thì không có gì để lọc — khỏi gọi (gọi không lọc là
  //  trả cả phạm vi, đánh lừa người xem).
  const listQuery = useLeaveCompRequests(listParams, {
    enabled: scope === SCOPE.ALL || (scope === SCOPE.MINE && Boolean(employeeId)),
  })
  const toApproveQuery = useLeaveCompToApprove()
  const waiting = useMemo(() => toApproveQuery.data?.items ?? [], [toApproveQuery.data])

  const needle = debouncedValue.trim().toLowerCase()
  const approveRows = useMemo(
    () =>
      sortRowsByCell(
        waiting.filter(
          (r) =>
            !needle ||
            [r.code, r.employee_name, r.reason].some((v) => v?.toLowerCase().includes(needle)),
        ),
        sortBy,
        sortDir,
        COMP_SORT_GETTERS,
      ),
    [waiting, needle, sortBy, sortDir],
  )

  const isApproveScope = scope === SCOPE.TO_APPROVE
  const rows: LeaveCompRequest[] | undefined = isApproveScope ? approveRows : listQuery.data?.items
  const total = isApproveScope ? approveRows.length : (listQuery.data?.total ?? 0)
  const isLoading = isApproveScope ? toApproveQuery.isLoading : listQuery.isLoading
  const isError = isApproveScope ? toApproveQuery.isError : listQuery.isError
  const waitingIds = useMemo(() => new Set(waiting.map((r) => r.id)), [waiting])

  const columns = useMemo<DataTableColumn<LeaveCompRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Số phiếu',
        width: 110,
        sortable: true,
        hideable: false,
        defaultPinned: true,
        cell: (r) => <span className="font-medium tabular-nums">{r.code}</span>,
      },
      {
        key: 'employee',
        //  Cột hiện tên kèm mã nhưng xếp theo họ tên — khóa gửi lên là `employee_name`.
        sortKey: 'employee_name',
        header: 'Người nghỉ',
        width: 220,
        sortable: true,
        cell: (r) => (
          <span className="truncate">
            {r.employee_name || `#${r.employee_id}`}
            {r.employee_code && <span className="text-muted-foreground"> · {r.employee_code}</span>}
          </span>
        ),
      },
      {
        key: 'work_date',
        header: 'Ngày đi làm',
        width: 130,
        sortable: true,
        sortDescFirst: true,
        cell: (r) => <span className="tabular-nums">{formatDate(r.work_date)}</span>,
      },
      {
        key: 'days',
        header: 'Số ngày',
        width: 90,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (r) => <span className="tabular-nums">{formatCompDays(r.days)}</span>,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 190,
        sortable: true,
        cell: (r) => (
          <div className="flex min-w-0 items-center gap-1.5">
            <LeaveStatusBadge status={r.status} label={r.status_label} />
            {waitingIds.has(r.id) && (
              <span className="shrink-0 text-xs font-medium text-sky-700 dark:text-sky-300">
                Cần bạn duyệt
              </span>
            )}
          </div>
        ),
      },
      {
        key: 'reason',
        header: 'Lý do',
        width: 280,
        defaultHidden: true,
        sortable: true,
        cell: (r) => <span className="truncate">{r.reason}</span>,
      },
      {
        key: 'created_at',
        header: 'Ngày tạo',
        width: 130,
        sortable: true,
        sortDescFirst: true,
        cell: (r) => <span className="tabular-nums">{formatDate(r.created_at)}</span>,
      },
    ],
    [waitingIds],
  )

  const isFiltered = Boolean(debouncedValue) || (!isApproveScope && status !== ALL)
  const emptyMessage = isFiltered
    ? 'Không có phiếu nào khớp bộ lọc.'
    : isApproveScope
      ? 'Không có phiếu nào đang chờ bạn duyệt.'
      : scope === SCOPE.MINE
        ? 'Bạn chưa có phiếu nghỉ bù nào.'
        : 'Chưa có phiếu nghỉ bù nào.'

  return (
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Phiếu nghỉ bù"
        description={
          <span className="max-md:hidden">
            Đi làm vào ngày nghỉ thì lập phiếu để được cộng ngày nghỉ bù vào quỹ phép.
          </span>
        }
        actions={
          can('leave_comp_request', 'create') ? (
            <Button
              type="button"
              className="w-full md:w-auto"
              onClick={() => navigate(appRoutes.hr.leaveCompRequestNew)}
            >
              <Plus className="size-4" />
              Lập phiếu nghỉ bù
            </Button>
          ) : undefined
        }
      />

      <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={rows}
          getRowId={(r) => r.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={emptyMessage}
          storageKey="hr.leave-comp-requests"
          sortBy={sortBy || undefined}
          sortDir={sortDir}
          onSortChange={handleSortChange}
          onRowClick={(r) => navigate(appRoutes.hr.leaveCompRequestDetail(r.id))}
          getRowHref={(r) => appRoutes.hr.leaveCompRequestDetail(r.id)}
          mobileCard={(r) => <LeaveCompRequestCard request={r} waitingForMe={waitingIds.has(r.id)} />}
          pagination={
            isApproveScope
              ? undefined
              : {
                  page,
                  pageSize,
                  total,
                  onPageChange: setPage,
                  onPageSizeChange: setPageSize,
                  unitLabel: 'phiếu',
                }
          }
          toolbar={
            <>
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm số phiếu, người nghỉ, lý do…"
                className="md:min-w-56 md:max-w-xs"
              />
              <Select value={scope} onValueChange={setScope}>
                <SelectTrigger className="w-full md:w-52" aria-label="Phạm vi">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.values(SCOPE) as Scope[]).map((s) => (
                    <SelectItem key={s} value={s}>
                      {SCOPE_LABELS[s]}
                      {s === SCOPE.TO_APPROVE && waiting.length > 0 ? ` (${waiting.length})` : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={status} onValueChange={setStatus} disabled={isApproveScope}>
                <SelectTrigger className="w-full md:w-44" aria-label="Trạng thái">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
                  {Object.values(LEAVE_COMP_STATUS).map((s) => (
                    <SelectItem key={s} value={String(s)}>
                      {LEAVE_COMP_STATUS_LABELS[s]}
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
