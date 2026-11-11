import { Plus } from 'lucide-react'
import { useMemo } from 'react'

import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { DataTable } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { toDateInputValue } from '@/shared/utils/format-date'
import { sortRowsByCell } from '@/shared/utils/sort-rows-by-cell'
import {
  buildEmployeeWorkHistoryColumns,
  EMPLOYEE_WORK_HISTORY_SORT_GETTERS,
  type EmployeeWorkHistoryRowActions,
} from '../config/employee-work-history-columns'
import { useLocalTableSort } from '../hooks/use-local-table-sort'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { EmployeeWorkHistoryTimeline } from './employee-work-history-timeline'
import { EmployeeWorkHistoryTimelineToolbar, EmployeeWorkHistoryToolbarTitle } from './employee-work-history-toolbar'
import type { WorkHistoryViewMode } from './employee-work-history-view-toggle'
import { WorkHistoryCard } from './work-history-card'

const TITLE = 'Quá trình công tác'

interface EmployeeWorkHistoryMainSectionProps {
  /** TOÀN BỘ dòng — khác khu Quyết định, khu này KHÔNG lọc theo decision_no. */
  items: EmployeeWorkHistory[]
  isLoading?: boolean
  isError?: boolean
  errorMessage?: string
  emptyMessage: string
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeWorkHistory) => void
  /** Bỏ trống = chỉ đọc (Trang cá nhân `/me`) — không cột/nút Thao tác. */
  actions?: EmployeeWorkHistoryRowActions
  storageKey: string
  /** Bỏ trống = ẨN nút "Thêm dòng" (chỉ đọc). */
  onAddClick?: () => void
  /** Bỏ trống = ẨN nút "Tạo dòng đầu từ hồ sơ" ở trạng thái rỗng. */
  onCreateFromProfileClick?: () => void
  /** Việc chạy khi bấm Tải lại. Bỏ trống = tự làm mới mọi query đang hoạt động. */
  onRefresh?: () => void | Promise<unknown>
}

/**
 * Khu "Quá trình công tác" (đại ca chốt 03/10/2026) — MỌI dòng (khác khu
 * "Quyết định bổ nhiệm" chỉ lọc dòng có số QĐ), giữ nguyên nút Thêm dòng / Áp /
 * Sửa / Xóa đã có từ trước, nay thêm nút chuyển Bảng | Dòng thời gian.
 *
 * Dùng lại Ở CẢ HAI NƠI: tab hồ sơ (`actions`/`onAddClick` có giá trị — ghi
 * được) và thẻ Trang cá nhân `/me` (bỏ trống cả hai — chỉ đọc, đúng ở cả dạng
 * Bảng LẪN Dòng thời gian vì `EmployeeWorkHistoryTimeline` cũng đọc `actions`).
 */
export function EmployeeWorkHistoryMainSection({
  items,
  isLoading,
  isError,
  errorMessage = 'Không tải được quá trình công tác.',
  emptyMessage,
  canOpenFiles,
  onOpenFiles,
  actions,
  storageKey,
  onAddClick,
  onCreateFromProfileClick,
  onRefresh,
}: EmployeeWorkHistoryMainSectionProps) {
  const [rawView, setView] = useUrlParamState('whView', 'table')
  const view: WorkHistoryViewMode = rawView === 'timeline' ? 'timeline' : 'table'

  const columns = useMemo(
    () => buildEmployeeWorkHistoryColumns({ canOpenFiles, onOpenFiles, actions }),
    [canOpenFiles, onOpenFiles, actions],
  )

  //  duoc-CR-748: dạng Bảng bấm tiêu đề cột để xếp, ngay ở trình duyệt (`items` là đủ mọi dòng của người này).
  //  Dạng Dòng thời gian giữ thứ tự riêng của nó (mới nhất ở trên).
  const sort = useLocalTableSort()
  const sortedItems = useMemo(
    () => sortRowsByCell(items, sort.sortBy, sort.sortDir, EMPLOYEE_WORK_HISTORY_SORT_GETTERS),
    [items, sort.sortBy, sort.sortDir],
  )

  const showCreateFromProfile = items.length === 0 && !isLoading && !isError && Boolean(onCreateFromProfileClick)

  //  Size mặc định (h-9) — khớp chiều cao Tải lại/Cột/ToggleGroup đứng cùng
  //  hàng (đại ca chê lệch cỡ nút, 03/10/2026); từng là `size="sm"` lúc nút
  //  này còn đứng ở hàng riêng của chính nó.
  const addButton = onAddClick && (
    <Button type="button" onClick={onAddClick}>
      <Plus className="size-4" />
      Thêm dòng
    </Button>
  )

  return (
    <Card className="gap-4 p-3 sm:p-5">
      {view === 'timeline' ? (
        <>
          <EmployeeWorkHistoryTimelineToolbar
            title={TITLE}
            view={view}
            onChange={setView}
            onRefresh={onRefresh}
            addButton={addButton}
          />
          {isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : isError ? (
            <p className="text-sm text-destructive">{errorMessage}</p>
          ) : (
            <EmployeeWorkHistoryTimeline
              items={items}
              variant="history"
              canOpenFiles={canOpenFiles}
              onOpenFiles={onOpenFiles}
              actions={actions}
              emptyMessage={emptyMessage}
            />
          )}
        </>
      ) : (
        <DataTable
          columns={columns}
          rows={sortedItems}
          getRowId={(row) => row.id}
          sortBy={sort.sortBy}
          sortDir={sort.sortDir}
          onSortChange={sort.onSortChange}
          isLoading={isLoading}
          isError={isError}
          errorMessage={errorMessage}
          emptyMessage={emptyMessage}
          storageKey={storageKey}
          onRefresh={onRefresh}
          //  Toggle Bảng|Dòng thời gian ghi `whView` lên URL (xem `useUrlParamState`
          //  trên) — tự suy "đang lọc" từ query string sẽ đọc nhầm nó thành bộ lọc
          //  và hiện lố nút "Xóa lọc" (bấm vào xóa luôn cả tham số đó). Khu này
          //  không có bộ lọc thật nào, nên khóa cứng về false.
          filtersActive={false}
          //  Khổ điện thoại (duoc-CR-721): mỗi dòng một thẻ. "Hôm nay" tính trong hàm vẽ thẻ như ô
          //  Đến ngày của bảng, không tính ở thân component.
          mobileCard={(row) => (
            <WorkHistoryCard
              row={row}
              variant="history"
              canOpenFiles={canOpenFiles}
              onOpenFiles={onOpenFiles}
              actions={actions}
              today={toDateInputValue(new Date())}
            />
          )}
          toolbar={<EmployeeWorkHistoryToolbarTitle title={TITLE} view={view} onChange={setView} />}
          toolbarEnd={addButton}
        />
      )}

      {showCreateFromProfile && (
        <div className="flex justify-center">
          <Button type="button" variant="outline" size="sm" onClick={onCreateFromProfileClick}>
            Tạo dòng đầu từ hồ sơ
          </Button>
        </div>
      )}
    </Card>
  )
}
