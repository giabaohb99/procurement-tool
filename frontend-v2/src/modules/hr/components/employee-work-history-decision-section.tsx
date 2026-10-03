import { useMemo } from 'react'

import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { DataTable } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { buildEmployeeWorkHistoryDecisionColumns } from '../config/employee-work-history-decision-columns'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { filterDecisionRows } from '../utils/employee-work-history-display'
import { EmployeeWorkHistoryTimeline } from './employee-work-history-timeline'
import { EmployeeWorkHistoryViewToggle, type WorkHistoryViewMode } from './employee-work-history-view-toggle'

const EMPTY_MESSAGE = 'Chưa có quyết định nào — ghi số QĐ khi thêm dòng quá trình công tác.'

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
   * Bỏ trống = ẨN nút gợi ý (thẻ Trang cá nhân `/me`, hoặc người xem không có
   * quyền sửa). Có giá trị = RỖNG thì hiện nút «Thêm ở tab Quá trình công
   * tác», bấm vào nhảy sang tab đó (tách tab, đại ca chốt 03/10/2026) — khu
   * này tự nó không ghi được.
   */
  onAddInWorkHistoryClick?: () => void
}

/**
 * Tab/khu «Quyết định bổ nhiệm» (đại ca chốt 03/10/2026) — CHỈ các dòng có
 * `decision_no`, dùng CHUNG nguồn dữ liệu với tab/khu «Quá trình công tác»
 * (không gọi API thêm). Dùng lại ở tab hồ sơ (`employee-tab-work-decisions.tsx`)
 * VÀ thẻ Trang cá nhân `/me` — khu này CHỈ ĐỌC ở cả hai nơi (không nhận
 * `actions`), ghi vẫn làm ở tab «Quá trình công tác».
 */
export function EmployeeWorkHistoryDecisionSection({
  items,
  isLoading,
  isError,
  errorMessage = 'Không tải được quyết định bổ nhiệm.',
  canOpenFiles,
  onOpenFiles,
  storageKey,
  onAddInWorkHistoryClick,
}: EmployeeWorkHistoryDecisionSectionProps) {
  const [rawView, setView] = useUrlParamState('decView', 'table')
  const view: WorkHistoryViewMode = rawView === 'timeline' ? 'timeline' : 'table'

  const decisions = useMemo(() => filterDecisionRows(items), [items])
  const columns = useMemo(
    () => buildEmployeeWorkHistoryDecisionColumns({ canOpenFiles, onOpenFiles }),
    [canOpenFiles, onOpenFiles],
  )

  //  Giống `showCreateFromProfile` của khu Quá trình công tác — chỉ hiện khi
  //  đã tải xong, không lỗi, và RỖNG (không phải "chưa tải" hiện nhầm nút).
  const showAddInWorkHistory =
    decisions.length === 0 && !isLoading && !isError && Boolean(onAddInWorkHistoryClick)

  return (
    <Card className="gap-4 p-3 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <SectionHeading>Quyết định bổ nhiệm</SectionHeading>
        <EmployeeWorkHistoryViewToggle value={view} onChange={setView} />
      </div>

      {view === 'timeline' ? (
        isLoading ? (
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
        )
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
        />
      )}

      {showAddInWorkHistory && (
        <div className="flex justify-center">
          <Button type="button" variant="outline" size="sm" onClick={onAddInWorkHistoryClick}>
            Thêm ở tab Quá trình công tác
          </Button>
        </div>
      )}
    </Card>
  )
}
