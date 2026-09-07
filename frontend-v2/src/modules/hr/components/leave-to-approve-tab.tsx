import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  applyClientFilter,
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { formatDateTime } from '@/shared/utils/format-date'
import { LEAVE_INBOX_FILTER_FIELDS } from '../config/leave-request-filter-fields'
import { useLeaveToApprove } from '../hooks/use-leave'
import type { LeaveInboxRow } from '../types/leave'
import {
  ALL_OPTION,
  filterLeaveRows,
  isFiltering,
  leaveTypesIn,
} from '../utils/filter-leave-rows'
import { LeaveRowsFilterBar } from './leave-rows-filter-bar'
import {
  codeColumn,
  dateColumns,
  employeeColumn,
  flowColumn,
  leaveTypeColumn,
  reasonColumn,
} from './leave-request-columns'

/**
 * Tab «CẦN TÔI DUYỆT» — hàng đợi việc đang chờ chính người đăng nhập ký.
 *
 * ⚠️ **Đơn chỉ hiện khi ĐÃ TỚI LƯỢT mình.** Người ở chặng 2 không thấy đơn đang
 * nằm ở chặng 1: thấy sớm thì họ bấm Duyệt rồi ăn câu "bạn không có việc nào
 * đang chờ ở phiếu này" — đúng luật nhưng vô nghĩa với thao tác vừa làm. Luật
 * lọc nằm ở backend (`task_service.my_tasks` chỉ lấy việc `TASK_PENDING`).
 *
 * ⚠️ **KHÔNG có cột thao tác** (bỏ 04/09/2026). Ba nút Duyệt / Trả về / Từ chối
 * lặp trên từng dòng ăn 280px và biến cả cột phải thành một mảng xanh-đỏ nhấp
 * nháy — mắt không còn đọc được dữ liệu nữa. Mà quyết định ở đây là **ký thay
 * mặt công ty cho người khác nghỉ**: bấm được ngay trên dòng nghĩa là ký mà chưa
 * đọc ai bàn giao, chưa xem còn bao nhiêu phép. Vào chi tiết rồi duyệt — ba nút
 * đó nằm sẵn ở đầu trang chi tiết (`LeaveDetailDecisionActions`).
 *
 * ⚠️ **Không có cột Trạng thái.** Mọi dòng ở đây đều là «Chờ duyệt» — một cột
 * lặp đúng một giá trị chỉ ăn chỗ của cột Luồng duyệt, thứ thật sự nói phiếu
 * đang ở đâu.
 *
 * Lọc ở PHÍA MÀN HÌNH: hàng đợi nạp trọn một lượt và không phân trang, nên hỏi
 * lại backend là thừa một vòng mạng — xem `utils/filter-leave-rows` (ô tìm nhanh)
 * và `config/leave-request-filter-fields` (bộ lọc nâng cao).
 */
export function LeaveToApproveTab() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <LeaveToApproveContent />
    </FilterProvider>
  )
}

/**
 * `preserveParams`: thiếu tên nào ở đây thì bấm «Áp dụng» của bộ lọc nâng cao sẽ
 * XÓA tham số đó khỏi URL — mà `tab` mất là màn nhảy về tab mặc định ngay sau
 * khi lọc, đúng lúc người dùng vừa nói rõ mình muốn xem gì.
 */
const FILTER_CONFIG = {
  fields: LEAVE_INBOX_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['tab'],
}

function LeaveToApproveContent() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useLeaveToApprove()
  const [keyword, setKeyword] = useState('')
  const [typeId, setTypeId] = useState(ALL_OPTION)
  const { appliedState, activeCount } = useFilterContext()

  const all = useMemo(() => data?.items ?? [], [data])
  const types = useMemo(() => leaveTypesIn(all), [all])
  const rows = useMemo(
    () => applyClientFilter(filterLeaveRows(all, { keyword, typeId }), appliedState),
    [all, keyword, typeId, appliedState],
  )
  //  Câu "bảng rỗng" phải kể cả bộ lọc nâng cao: rỗng vì mình vừa lọc khác hẳn
  //  rỗng vì không có việc nào — người đọc phải biết mình đang nhìn cái nào.
  const filtering = isFiltering({ keyword, typeId }) || activeCount > 0

  const columns = useMemo<DataTableColumn<LeaveInboxRow>[]>(
    () => [
      codeColumn(),
      employeeColumn(),
      leaveTypeColumn(),
      ...dateColumns(),
      flowColumn((row) => row.flow),
      {
        key: 'task_node',
        header: 'Việc của tôi',
        cell: (row) => (
          <div className="min-w-0">
            <span className="block truncate">
              {row.task.node_name || `Chặng ${row.task.node_seq}`}
            </span>
            {/*  Bấm THAY người khác phải nói ra TRƯỚC khi bấm, không phải sau:
                 chữ ký đi vào dấu vết mang cả hai tên. */}
            {row.task.on_behalf_of_name && (
              <span className="block truncate text-xs text-muted-foreground">
                Bấm thay {row.task.on_behalf_of_name}
              </span>
            )}
            {row.task.is_overdue && (
              <Badge variant="outline" className="mt-0.5 border-destructive/40 text-destructive">
                Quá hạn
              </Badge>
            )}
          </div>
        ),
        width: 170,
      },
      reasonColumn(),
      {
        key: 'due_at',
        header: 'Hạn xử lý',
        cell: (row) =>
          row.task.due_at ? (
            <span className="tabular-nums">{formatDateTime(row.task.due_at)}</span>
          ) : (
            '—'
          ),
        width: 150,
      },
    ],
    [],
  )

  return (
    <DataTable
      fillHeight
      columns={columns}
      rows={rows}
      getRowId={(r) => r.id}
      isLoading={isLoading}
      isError={isError}
      emptyMessage={
        filtering
          ? 'Không có đơn nào khớp bộ lọc.'
          : 'Không có đơn nào đang chờ bạn duyệt.'
      }
      storageKey="hr.leave-to-approve"
      onRowClick={(r) => navigate(appRoutes.hr.leaveRequestDetail(r.id))}
      toolbar={
        <LeaveRowsFilterBar
          keyword={keyword}
          onKeywordChange={setKeyword}
          typeId={typeId}
          onTypeChange={setTypeId}
          types={types}
        >
          {/*  Nói ra đường duyệt: bỏ cột nút rồi thì "bấm vào dòng" là thao tác
               duy nhất, mà một bảng không có nút nào thì không tự nói điều đó. */}
          <ConditionalFilter />

          {rows.length > 0 && (
            <span className="border-l pl-3 text-xs text-muted-foreground">
              <span className="font-medium text-foreground">{rows.length} đơn</span> · bấm
              vào một dòng để xem và duyệt
            </span>
          )}
        </LeaveRowsFilterBar>
      }
    />
  )
}
