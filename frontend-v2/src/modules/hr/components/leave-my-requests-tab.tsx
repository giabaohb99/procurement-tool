import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useLeaveFlowStrips, useLeaveRequests, useLeaveTypes } from '../hooks/use-leave'
import { LEAVE_STATUS, LEAVE_STATUS_LABELS, type LeaveRequest } from '../types/leave'
import {
  codeColumn,
  dateColumns,
  employeeColumn,
  flowColumn,
  leaveTypeColumn,
  reasonColumn,
  statusColumn,
} from './leave-request-columns'

const ALL = 'all'

/**
 * Tab «ĐƠN CỦA TÔI» — danh sách đơn trong phạm vi người xem.
 *
 * Người thường thấy đơn của chính mình (phạm vi `own`), trưởng phòng thấy cả
 * phòng, Nhân sự thấy toàn công ty. Cùng một bảng, backend lọc — màn hình không
 * cần biết mình đang đứng ở vai nào.
 *
 * ⚠️ Luồng duyệt lấy bằng MỘT lượt gọi cho cả trang, không phải mỗi dòng một
 * lượt: hai mươi dòng × một lượt là hai mươi lượt mạng cho một lần mở bảng.
 * Backend cũng gom sẵn — xem `approval/steps_service.py`.
 */
export function LeaveMyRequestsTab() {
  const navigate = useNavigate()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [leaveTypeId, setLeaveTypeId] = useUrlParamState('leave_type_id', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: typeData } = useLeaveTypes()

  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue) p.search = debouncedValue
    if (status !== ALL) p.status = status
    if (leaveTypeId !== ALL) p.leave_type_id = leaveTypeId
    return p
  }, [page, pageSize, debouncedValue, status, leaveTypeId])

  const { data, isLoading, isError } = useLeaveRequests(params)

  const pageIds = useMemo(() => (data?.items ?? []).map((r) => r.id), [data])
  const { data: flows } = useLeaveFlowStrips(pageIds)

  const columns = useMemo<DataTableColumn<LeaveRequest>[]>(
    () => [
      codeColumn(),
      statusColumn(),
      flowColumn((row) => flows?.[String(row.id)]),
      employeeColumn(),
      leaveTypeColumn(),
      ...dateColumns(),
      reasonColumn(),
    ],
    [flows],
  )

  return (
    <DataTable
      fillHeight
      columns={columns}
      rows={data?.items}
      getRowId={(r) => r.id}
      isLoading={isLoading}
      isError={isError}
      emptyMessage="Chưa có đơn nghỉ phép nào."
      storageKey="hr.leave-requests"
      onRowClick={(r) => navigate(appRoutes.hr.leaveRequestDetail(r.id))}
      pagination={{
        page,
        pageSize,
        total: data?.total ?? 0,
        onPageChange: setPage,
        onPageSizeChange: setPageSize,
        unitLabel: 'đơn',
      }}
      toolbar={
        <>
          <div className="relative min-w-56 flex-1 md:max-w-xs">
            <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Tìm theo số đơn hoặc lý do…"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </div>

          <Select value={leaveTypeId} onValueChange={setLeaveTypeId}>
            <SelectTrigger className="w-44">
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

          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-40">
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
        </>
      }
    />
  )
}
