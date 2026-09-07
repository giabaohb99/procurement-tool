import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
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
import { LEAVE_REQUEST_FILTER_FIELDS } from '../config/leave-request-filter-fields'
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
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <LeaveMyRequestsContent />
    </FilterProvider>
  )
}

/**
 * `preserveParams`: mọi tham số khác của màn phải kể tên ở đây, không thì bấm
 * «Áp dụng» là chúng bị xóa khỏi URL — mất `tab` thì nhảy về tab mặc định, mất
 * `status`/`leave_type_id` thì hai ô chọn trên thanh công cụ tự nhảy về «Tất cả»
 * ngay lúc người dùng thêm một điều kiện. (`q` do `searchParamName` giữ sẵn.)
 */
const FILTER_CONFIG = {
  fields: LEAVE_REQUEST_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['tab', 'status', 'leave_type_id'],
}

function LeaveMyRequestsContent() {
  const navigate = useNavigate()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [leaveTypeId, setLeaveTypeId] = useUrlParamState('leave_type_id', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  //  Lọc ở BACKEND, không `applyClientFilter`: bảng này có phân trang, lọc trên
  //  trang đang mở là ra kết quả sai.
  const { queryParams, queryKey } = useFilterQuery()

  const { data: typeData } = useLeaveTypes()

  //  Đổi điều kiện thì về TRANG 1. Đang đứng trang 3 mà lọc còn 5 dòng thì trang
  //  3 rỗng — người dùng đọc ra "không có gì khớp".
  //
  //  Chỉnh NGAY TRONG LÚC VẼ chứ không qua `useEffect`: đây là state phái sinh
  //  từ `queryKey`, và làm bằng effect thì lượt vẽ đầu dùng trang cũ rồi mới vẽ
  //  lại — vừa nháy một nhịp, vừa bắn thừa một lượt gọi API cho trang không tồn
  //  tại. Khuôn chính thức của React cho "sửa state khi prop đổi".
  const [pageOfQuery, setPageOfQuery] = useState(queryKey)
  if (pageOfQuery !== queryKey) {
    setPageOfQuery(queryKey)
    setPage(1)
  }

  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize, ...queryParams }
    if (debouncedValue) p.search = debouncedValue
    if (status !== ALL) p.status = status
    if (leaveTypeId !== ALL) p.leave_type_id = leaveTypeId
    return p
  }, [page, pageSize, debouncedValue, status, leaveTypeId, queryParams])

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

          <ConditionalFilter />
        </>
      }
    />
  )
}
