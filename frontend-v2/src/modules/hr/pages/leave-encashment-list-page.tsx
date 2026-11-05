import { Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { buildLeaveEncashmentColumns } from '../components/leave-encashment-columns'
import { useLeaveEncashments, useLeaveEncashmentToApprove } from '../hooks/use-leave-encashment'
import {
  LEAVE_ENCASHMENT_REASON_LABELS,
  LEAVE_ENCASHMENT_STATUS,
  LEAVE_ENCASHMENT_STATUS_LABELS,
  type LeaveEncashment,
} from '../types/leave-encashment'

const ALL = 'all'
const SCOPE = { MINE: 'mine', TO_APPROVE: 'to-approve', ALL: 'all' } as const
type Scope = (typeof SCOPE)[keyof typeof SCOPE]
const SCOPE_LABELS: Record<Scope, string> = {
  [SCOPE.MINE]: 'Của tôi',
  [SCOPE.TO_APPROVE]: 'Cần tôi duyệt',
  [SCOPE.ALL]: 'Tất cả trong phạm vi',
}

/**
 * PHIẾU THANH TOÁN NGHỈ PHÉP — danh sách (duoc-CR-719). Cùng cách chia phạm vi với màn Nghỉ bù: *Của tôi* (lọc theo
 * nhân sự đăng nhập) · *Cần tôi duyệt* (GET /to-approve, không phân trang) · *Tất cả trong phạm vi* (theo phạm vi dữ
 * liệu của vai trò). Cột "Trạng thái chi" đọc từ YCTT (backend gửi kèm), không có số tiền.
 */
export function LeaveEncashmentListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { user } = useAuth()

  const [scopeParam, setScope] = useUrlParamState('scope', SCOPE.MINE)
  const scope: Scope = (Object.values(SCOPE) as string[]).includes(scopeParam)
    ? (scopeParam as Scope)
    : SCOPE.MINE
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [reason, setReason] = useUrlParamState('reason_kind', ALL)
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([scope, status, reason, debouncedValue])

  const employeeId = user?.employee_id
  const listParams = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue) p.q = debouncedValue
    if (status !== ALL) p.status = status
    if (reason !== ALL) p.reason_kind = reason
    if (scope === SCOPE.MINE && employeeId) p.employee_id = String(employeeId)
    return p
  }, [page, pageSize, debouncedValue, status, reason, scope, employeeId])

  //  "Của tôi" mà tài khoản chưa gắn hồ sơ nhân sự thì không có gì để lọc — khỏi gọi (gọi không lọc là trả cả
  //  phạm vi, đánh lừa người xem).
  const listQuery = useLeaveEncashments(listParams, {
    enabled: scope === SCOPE.ALL || (scope === SCOPE.MINE && Boolean(employeeId)),
  })
  const toApproveQuery = useLeaveEncashmentToApprove()
  const waiting = useMemo(() => toApproveQuery.data?.items ?? [], [toApproveQuery.data])

  const needle = debouncedValue.trim().toLowerCase()
  const approveRows = useMemo(
    () =>
      waiting.filter(
        (r) =>
          !needle || [r.code, r.employee_name, r.note].some((v) => v?.toLowerCase().includes(needle)),
      ),
    [waiting, needle],
  )

  const isApproveScope = scope === SCOPE.TO_APPROVE
  const rows: LeaveEncashment[] | undefined = isApproveScope ? approveRows : listQuery.data?.items
  const total = isApproveScope ? approveRows.length : (listQuery.data?.total ?? 0)
  const isLoading = isApproveScope ? toApproveQuery.isLoading : listQuery.isLoading
  const isError = isApproveScope ? toApproveQuery.isError : listQuery.isError
  const waitingIds = useMemo(() => new Set(waiting.map((r) => r.id)), [waiting])
  const columns = useMemo(() => buildLeaveEncashmentColumns(waitingIds), [waitingIds])

  const isFiltered = Boolean(debouncedValue) || (!isApproveScope && (status !== ALL || reason !== ALL))
  const emptyMessage = isFiltered
    ? 'Không có phiếu nào khớp bộ lọc.'
    : isApproveScope
      ? 'Không có phiếu nào đang chờ bạn duyệt.'
      : scope === SCOPE.MINE
        ? 'Bạn chưa có phiếu thanh toán nghỉ phép nào.'
        : 'Chưa có phiếu thanh toán nghỉ phép nào.'

  return (
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Thanh toán nghỉ phép"
        description={
          <span className="max-md:hidden">
            Đổi ngày phép chưa nghỉ ra tiền khi cuối năm còn dư hoặc khi nghỉ việc. Duyệt xong, kế toán nhận yêu cầu
            thanh toán để chi.
          </span>
        }
        actions={
          can('leave_encashment', 'create') ? (
            <Button
              type="button"
              className="w-full md:w-auto"
              onClick={() => navigate(appRoutes.hr.leaveEncashmentNew)}
            >
              <Plus className="size-4" />
              Lập phiếu thanh toán
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
          storageKey="hr.leave-encashments"
          onRowClick={(r) => navigate(appRoutes.hr.leaveEncashmentDetail(r.id))}
          getRowHref={(r) => appRoutes.hr.leaveEncashmentDetail(r.id)}
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
                placeholder="Tìm số phiếu, người được thanh toán, ghi chú…"
                className="md:max-w-xs md:min-w-56"
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
                  {Object.values(LEAVE_ENCASHMENT_STATUS).map((s) => (
                    <SelectItem key={s} value={String(s)}>
                      {LEAVE_ENCASHMENT_STATUS_LABELS[s]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={reason} onValueChange={setReason} disabled={isApproveScope}>
                <SelectTrigger className="w-full md:w-44" aria-label="Lý do">
                  <SelectValue placeholder="Lý do" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi lý do</SelectItem>
                  {Object.entries(LEAVE_ENCASHMENT_REASON_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
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
