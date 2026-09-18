import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { appConfig } from '@/core/config/app-config'
import {
  applyClientFilter,
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { LEAVE_REQUEST_FILTER_FIELDS } from '../config/leave-request-filter-fields'
import { useLeaveHandled, useLeaveRequests, useLeaveToApprove, useLeaveTypes } from '../hooks/use-leave'
import {
  LEAVE_SCOPE,
  LEAVE_STATUS,
  LEAVE_STATUS_LABELS,
  type LeaveInboxRow,
  type LeaveRequest,
  type LeaveScope,
} from '../types/leave'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'
import { LeaveRequestCard } from './leave-request-card'
import {
  codeColumn,
  dateColumns,
  employeeColumn,
  leaveTypeColumn,
  reasonColumn,
} from './leave-request-columns'
import { LeaveStatusCell } from './leave-status-cell'

const ALL = 'all'

/**
 * `preserveParams`: mọi tham số khác của màn phải kể tên ở đây, không thì bấm
 * «Áp dụng» là chúng bị xóa khỏi URL — mất `scope` thì nhảy về phạm vi mặc định,
 * mất `status`/`leave_type_id` thì hai ô chọn trên thanh công cụ tự nhảy về «Tất cả».
 */
const FILTER_CONFIG = {
  fields: LEAVE_REQUEST_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['scope', 'tab', 'status', 'leave_type_id'],
}

/**
 * BẢNG ĐƠN NGHỈ PHÉP DUY NHẤT — gom 3 tab (Cần tôi duyệt · Đơn của tôi · Tôi đã duyệt)
 * thành 1 bảng với bộ lọc phạm vi, loại nghỉ, trạng thái và đưa các đơn Chờ duyệt lên đầu.
 */
export function UnifiedLeaveRequestTable() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <UnifiedLeaveRequestContent />
    </FilterProvider>
  )
}

function UnifiedLeaveRequestContent() {
  const navigate = useNavigate()
  const { user } = useAuth()

  // Đồng bộ `scope` trên URL; mặc định là ALL ('all')
  const [scopeParam, setScopeParam] = useUrlParamState('scope', LEAVE_SCOPE.ALL)
  const [tabParam] = useUrlParamState('tab', '')
  const currentScope: LeaveScope =
    (scopeParam !== LEAVE_SCOPE.ALL && Object.values(LEAVE_SCOPE).includes(scopeParam as LeaveScope))
      ? (scopeParam as LeaveScope)
      : (tabParam as LeaveScope) && Object.values(LEAVE_SCOPE).includes(tabParam as LeaveScope)
        ? (tabParam as LeaveScope)
        : LEAVE_SCOPE.ALL

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [leaveTypeId, setLeaveTypeId] = useUrlParamState('leave_type_id', ALL)

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { queryParams, queryKey } = useFilterQuery()
  const filter = useFilterContext()

  // Đổi điều kiện lọc hoặc phạm vi thì đưa về trang 1
  const querySignature = `${currentScope}-${queryKey}-${status}-${leaveTypeId}-${debouncedValue}`
  const [lastSignature, setLastSignature] = useState(querySignature)
  if (lastSignature !== querySignature) {
    setLastSignature(querySignature)
    setPage(1)
  }

  // 1. Dữ liệu danh mục loại nghỉ
  const { data: typeData } = useLeaveTypes()

  // 2. Hàng đợi việc cần chính tôi duyệt
  const toApproveQuery = useLeaveToApprove()
  const toApproveItems = useMemo(() => toApproveQuery.data?.items ?? [], [toApproveQuery.data])
  const waitingCount = toApproveItems.length
  const toApproveIds = useMemo(
    () => new Set(toApproveItems.map((r) => r.id)),
    [toApproveItems],
  )

  // 3. Danh sách tôi đã duyệt (30 ngày gần nhất)
  const handledQuery = useLeaveHandled({}, currentScope === LEAVE_SCOPE.HANDLED)
  const handledItems = useMemo(() => handledQuery.data?.items ?? [], [handledQuery.data])

  // 4. Danh sách đơn lấy từ backend theo phân trang (cho 'all' và 'mine')
  const employeeId = user?.employee_id
  const serverParams = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize, ...queryParams }
    if (debouncedValue) p.search = debouncedValue
    if (status !== ALL) p.status = status
    if (leaveTypeId !== ALL) p.leave_type_id = leaveTypeId
    if (currentScope === LEAVE_SCOPE.MINE && employeeId) {
      p.employee_id = String(employeeId)
    }
    return p
  }, [page, pageSize, debouncedValue, status, leaveTypeId, currentScope, employeeId, queryParams])

  const requestsQuery = useLeaveRequests(serverParams, {
    enabled: currentScope === LEAVE_SCOPE.ALL || currentScope === LEAVE_SCOPE.MINE,
  })

  // Tính toán dữ liệu hiển thị, tổng số lượng và trạng thái tải theo từng phạm vi
  const { displayRows, totalCount, isLoading, isError } = useMemo(() => {
    const needle = debouncedValue.trim().toLowerCase()

    if (currentScope === LEAVE_SCOPE.TO_APPROVE) {
      let list = toApproveItems
      if (needle) {
        list = list.filter(
          (r) =>
            r.code?.toLowerCase().includes(needle) ||
            r.employee_name?.toLowerCase().includes(needle) ||
            r.reason?.toLowerCase().includes(needle) ||
            r.leave_type_name?.toLowerCase().includes(needle),
        )
      }
      if (leaveTypeId !== ALL) {
        list = list.filter((r) => String(r.leave_type_id) === leaveTypeId)
      }
      list = applyClientFilter(list, filter.appliedState)
      const total = list.length
      const paged = list.slice((page - 1) * pageSize, page * pageSize)
      return {
        displayRows: paged,
        totalCount: total,
        isLoading: toApproveQuery.isLoading,
        isError: toApproveQuery.isError,
      }
    }

    if (currentScope === LEAVE_SCOPE.HANDLED) {
      let list = handledItems
      if (needle) {
        list = list.filter(
          (r) =>
            r.code?.toLowerCase().includes(needle) ||
            r.employee_name?.toLowerCase().includes(needle) ||
            r.reason?.toLowerCase().includes(needle) ||
            r.leave_type_name?.toLowerCase().includes(needle),
        )
      }
      if (status !== ALL) {
        list = list.filter((r) => String(r.status) === status)
      }
      if (leaveTypeId !== ALL) {
        list = list.filter((r) => String(r.leave_type_id) === leaveTypeId)
      }
      list = applyClientFilter(list, filter.appliedState)
      const total = list.length
      const paged = list.slice((page - 1) * pageSize, page * pageSize)
      return {
        displayRows: paged,
        totalCount: total,
        isLoading: handledQuery.isLoading,
        isError: handledQuery.isError,
      }
    }

    // currentScope === 'all' | 'mine'
    const rawItems = requestsQuery.data?.items ?? []
    // Khi xem 'all': backend đã sort Chờ duyệt lên trước (status == LR_PENDING).
    // Ở FE, ưu tiên đẩy thêm các đơn trong hàng đợi `toApprove` của chính người dùng lên hàng đầu tiên.
    const sorted =
      currentScope === LEAVE_SCOPE.ALL
        ? [...rawItems].sort((a, b) => {
            const aMine = toApproveIds.has(a.id) ? 0 : 1
            const bMine = toApproveIds.has(b.id) ? 0 : 1
            if (aMine !== bMine) return aMine - bMine
            const aPending = a.status === LEAVE_STATUS.PENDING ? 0 : 1
            const bPending = b.status === LEAVE_STATUS.PENDING ? 0 : 1
            if (aPending !== bPending) return aPending - bPending
            return b.id - a.id
          })
        : rawItems

    return {
      displayRows: sorted,
      totalCount: requestsQuery.data?.total ?? 0,
      isLoading: requestsQuery.isLoading,
      isError: requestsQuery.isError,
    }
  }, [
    currentScope,
    debouncedValue,
    toApproveItems,
    leaveTypeId,
    filter.appliedState,
    page,
    pageSize,
    toApproveQuery.isLoading,
    toApproveQuery.isError,
    handledItems,
    status,
    handledQuery.isLoading,
    handledQuery.isError,
    requestsQuery.data?.items,
    requestsQuery.data?.total,
    requestsQuery.isLoading,
    requestsQuery.isError,
    toApproveIds,
  ])

  const scopeSelect = (
    <Select
      value={currentScope}
      onValueChange={(val) => setScopeParam(val as LeaveScope)}
    >
      <SelectTrigger className="w-full md:w-44">
        <SelectValue placeholder="Phạm vi" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={LEAVE_SCOPE.ALL}>Tất cả</SelectItem>
        <SelectItem value={LEAVE_SCOPE.TO_APPROVE}>
          Cần tôi duyệt{waitingCount > 0 ? ` (${waitingCount})` : ''}
        </SelectItem>
        <SelectItem value={LEAVE_SCOPE.MINE}>Đơn của tôi</SelectItem>
        <SelectItem value={LEAVE_SCOPE.HANDLED}>Tôi đã duyệt</SelectItem>
      </SelectContent>
    </Select>
  )

  const typeSelect = (
    <Select value={leaveTypeId} onValueChange={setLeaveTypeId}>
      <SelectTrigger className="w-full md:w-44">
        <SelectValue placeholder="Loại nghỉ" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả loại nghỉ</SelectItem>
        {(typeData?.items ?? []).map((t) => (
          <SelectItem key={t.id} value={String(t.id)}>
            {t.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select
      value={status}
      onValueChange={setStatus}
      disabled={currentScope === LEAVE_SCOPE.TO_APPROVE}
    >
      <SelectTrigger className="w-full md:w-40">
        <SelectValue placeholder="Trạng thái" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
        {Object.values(LEAVE_STATUS).map((s) => (
          <SelectItem key={s} value={String(s)}>
            {LEAVE_STATUS_LABELS[s]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const isFiltered =
    Boolean(debouncedValue) ||
    (currentScope !== LEAVE_SCOPE.TO_APPROVE && status !== ALL) ||
    leaveTypeId !== ALL ||
    filter.activeCount > 0

  const emptyMessage = isFiltered
    ? 'Không có đơn nào khớp bộ lọc.'
    : currentScope === LEAVE_SCOPE.TO_APPROVE
      ? 'Không có đơn nào đang chờ bạn duyệt.'
      : currentScope === LEAVE_SCOPE.HANDLED
        ? 'Bạn chưa duyệt đơn nghỉ phép nào trong 30 ngày qua.'
        : currentScope === LEAVE_SCOPE.MINE
          ? 'Bạn chưa có đơn nghỉ phép nào.'
          : 'Chưa có đơn nghỉ phép nào.'

  const columns = useMemo<DataTableColumn<LeaveRequest>[]>(
    () => [
      codeColumn(),
      {
        key: 'status',
        header: 'Trạng thái',
        cell: (r) => {
          const isMyTask = toApproveIds.has(r.id)
          return (
            <div className="flex min-w-0 items-center gap-1.5">
              <LeaveStatusCell request={r} />
              {isMyTask && (
                <Badge
                  variant="outline"
                  className="shrink-0 border-sky-300 bg-sky-50 text-[11px] font-medium text-sky-800 dark:border-sky-700 dark:bg-sky-950 dark:text-sky-200"
                >
                  Cần bạn duyệt
                </Badge>
              )}
            </div>
          )
        },
        width: 240,
      },
      employeeColumn(),
      leaveTypeColumn(),
      ...dateColumns(),
      reasonColumn(),
    ],
    [toApproveIds],
  )

  return (
    <DataTable
      fillHeight
      columns={columns}
      rows={displayRows}
      getRowId={(r) => r.id}
      isLoading={isLoading}
      isError={isError}
      emptyMessage={emptyMessage}
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
      storageKey="hr.unified-leave-requests"
      onRowClick={(r) => navigate(appRoutes.hr.leaveRequestDetail(r.id))}
      mobileCard={(r) => {
        const dueAt = 'task' in r ? (r as LeaveInboxRow).task?.due_at : undefined
        return <LeaveRequestCard request={r} dueAt={dueAt} />
      }}
      pagination={{
        page,
        pageSize,
        total: totalCount,
        onPageChange: setPage,
        onPageSizeChange: setPageSize,
        unitLabel: 'đơn',
      }}
      toolbar={
        <>
          <SearchField
            value={keyword}
            onChange={setKeyword}
            placeholder="Tìm số đơn, lý do, người nghỉ…"
            className="md:min-w-56 md:max-w-xs"
          />

          <QuickFilterSheet
            activeCount={
              (currentScope !== LEAVE_SCOPE.ALL ? 1 : 0) +
              (leaveTypeId !== ALL ? 1 : 0) +
              (status !== ALL && currentScope !== LEAVE_SCOPE.TO_APPROVE ? 1 : 0) +
              filter.activeCount
            }
            onClearAll={() => {
              setScopeParam(LEAVE_SCOPE.ALL)
              setLeaveTypeId(ALL)
              setStatus(ALL)
              filter.reset()
            }}
            onApply={filter.apply}
          >
            <QuickFilterField label="Phạm vi">{scopeSelect}</QuickFilterField>
            <QuickFilterField label="Loại nghỉ">{typeSelect}</QuickFilterField>
            {currentScope !== LEAVE_SCOPE.TO_APPROVE && (
              <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
            )}
            <AdvancedFilterSection />
          </QuickFilterSheet>

          <div className="hidden items-center gap-3 md:flex md:flex-wrap">
            {scopeSelect}
            {typeSelect}
            {currentScope !== LEAVE_SCOPE.TO_APPROVE && statusSelect}
            <ConditionalFilter />
          </div>
        </>
      }
    />
  )
}
