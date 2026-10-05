import { Plus } from 'lucide-react'
import { useMemo } from 'react'

import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { DataTable } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { buildEmployeeWorkHistoryDecisionColumns } from '../config/employee-work-history-decision-columns'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { filterDecisionRows } from '../utils/employee-work-history-display'
import { EmployeeWorkHistoryTimeline } from './employee-work-history-timeline'
import { EmployeeWorkHistoryTimelineToolbar, EmployeeWorkHistoryToolbarTitle } from './employee-work-history-toolbar'
import type { WorkHistoryViewMode } from './employee-work-history-view-toggle'

const TITLE = 'Quyết định bổ nhiệm'
const EMPTY_MESSAGE = 'Chưa có quyết định nào.'

interface EmployeeWorkHistoryDecisionSectionProps {
  /** TOÀN BỘ dòng quá trình công tác — khu này tự lọc, KHÔNG gọi API riêng. */
  items: EmployeeWorkHistory[]
  isLoading?: boolean
  isError?: boolean
  errorMessage?: string
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeWorkHistory) => void
  /** Khóa nhớ bố cột ở `localStorage` — khác bảng chính vì bộ cột khác hẳn. */
  storageKey: string
  /**
   * Bỏ trống = ẨN nút «+ Thêm quyết định» (thẻ Trang cá nhân `/me`, hoặc
   * người xem không có quyền sửa — cùng điều kiện với «Thêm dòng» của khu
   * Quá trình công tác). Có giá trị → hiện ở CUỐI thanh công cụ (cùng chỗ
   * «Thêm dòng» của khu kia) VÀ thay cho nút gợi ý lúc rỗng — bấm MỞ THẲNG hộp
   * thêm (mục 3, 03/10/2026; trước đó nhảy sang tab «Quá trình công tác»).
   */
  onAddClick?: () => void
  /** Việc chạy khi bấm Tải lại. Bỏ trống = tự làm mới mọi query đang hoạt động. */
  onRefresh?: () => void | Promise<unknown>
}

/**
 * Tab/khu «Quyết định bổ nhiệm» (đại ca chốt 03/10/2026) — CHỈ các dòng có
 * `decision_no`, dùng CHUNG nguồn dữ liệu với tab/khu «Quá trình công tác»
 * (không gọi API thêm). Dùng lại ở tab hồ sơ (`employee-tab-work-decisions.tsx`)
 * VÀ thẻ Trang cá nhân `/me` — khu này không nhận `actions` (không Sửa/Xóa/Áp,
 * việc đó vẫn làm ở tab «Quá trình công tác») nhưng CÓ thể nhận `onAddClick`
 * (mục 3) vì tạo MỘT quyết định mới không cần sửa dòng cũ nào.
 */
export function EmployeeWorkHistoryDecisionSection({
  items,
  isLoading,
  isError,
  errorMessage = 'Không tải được quyết định bổ nhiệm.',
  canOpenFiles,
  onOpenFiles,
  storageKey,
  onAddClick,
  onRefresh,
}: EmployeeWorkHistoryDecisionSectionProps) {
  const [rawView, setView] = useUrlParamState('decView', 'table')
  const view: WorkHistoryViewMode = rawView === 'timeline' ? 'timeline' : 'table'

  const decisions = useMemo(() => filterDecisionRows(items), [items])
  const columns = useMemo(
    () => buildEmployeeWorkHistoryDecisionColumns({ canOpenFiles, onOpenFiles }),
    [canOpenFiles, onOpenFiles],
  )

  //  Cùng cỡ nút (h-9) với Tải lại/Cột đứng cùng hàng — khuôn của khu Quá
  //  trình công tác (`employee-work-history-main-section.tsx::addButton`).
  const addButton = onAddClick && (
    <Button type="button" onClick={onAddClick}>
      <Plus className="size-4" />
      Thêm quyết định
    </Button>
  )

  //  Giống `showCreateFromProfile` của khu Quá trình công tác — chỉ hiện khi
  //  đã tải xong, không lỗi, và RỖNG (không phải "chưa tải" hiện nhầm nút).
  const showEmptyAdd = decisions.length === 0 && !isLoading && !isError && Boolean(onAddClick)

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
              items={decisions}
              variant="decision"
              canOpenFiles={canOpenFiles}
              onOpenFiles={onOpenFiles}
              emptyMessage={EMPTY_MESSAGE}
            />
          )}
        </>
      ) : (
        <DataTable
          columns={columns}
          rows={decisions}
          getRowId={(row) => row.id}
          isLoading={isLoading}
          isError={isError}
          errorMessage={errorMessage}
          emptyMessage={EMPTY_MESSAGE}
          storageKey={storageKey}
          onRefresh={onRefresh}
          //  Cùng lý do đã ghi ở khu Quá trình công tác: `decView` trên URL
          //  không phải bộ lọc, đừng để `FilterResetButton` tự suy nhầm.
          filtersActive={false}
          toolbar={<EmployeeWorkHistoryToolbarTitle title={TITLE} view={view} onChange={setView} />}
          toolbarEnd={addButton}
        />
      )}

      {showEmptyAdd && (
        <div className="flex justify-center">
          <Button type="button" variant="outline" size="sm" onClick={onAddClick}>
            <Plus className="size-4" />
            Thêm quyết định
          </Button>
        </div>
      )}
    </Card>
  )
}
