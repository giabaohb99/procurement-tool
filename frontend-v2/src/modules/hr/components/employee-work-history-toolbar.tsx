import { useQueryClient } from '@tanstack/react-query'
import { RotateCw } from 'lucide-react'
import { useCallback, useState, type ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { SectionHeading } from '@/shared/ui/section-heading'
import { cn } from '@/shared/utils/cn'
import { EmployeeWorkHistoryViewToggle, type WorkHistoryViewMode } from './employee-work-history-view-toggle'

interface EmployeeWorkHistoryToolbarTitleProps {
  title: string
  view: WorkHistoryViewMode
  onChange: (next: WorkHistoryViewMode) => void
}

/**
 * Tiêu đề khu + nút chuyển Bảng | Dòng thời gian GỘP THÀNH MỘT Ô co giãn
 * (đại ca chê hàng điều khiển cũ rời rạc, 03/10/2026).
 *
 * Dùng làm `toolbar` của `DataTable` ở CHẾ ĐỘ BẢNG: ô `flex-1` này nuốt hết
 * khoảng trống còn lại của dải công cụ — cùng kỹ thuật ô tìm kiếm `flex-1` ở
 * các màn danh sách khác (xem `docs/ui/table.md` §3) — nên `justify-between`
 * đẩy nút chuyển đứng SÁT cụm Tải lại/Cột/Thêm dòng bên phải, không dính liền
 * tiêu đề bên trái. Dùng lại Y NGUYÊN ở `EmployeeWorkHistoryTimelineToolbar`
 * cho CHẾ ĐỘ DÒNG THỜI GIAN, vì lúc đó `DataTable` không mount nên không có
 * dải công cụ nào để gắn vào.
 */
export function EmployeeWorkHistoryToolbarTitle({ title, view, onChange }: EmployeeWorkHistoryToolbarTitleProps) {
  return (
    <div className="flex min-w-0 flex-1 items-center justify-between gap-3">
      <SectionHeading className="shrink-0">{title}</SectionHeading>
      <EmployeeWorkHistoryViewToggle value={view} onChange={onChange} />
    </div>
  )
}

interface EmployeeWorkHistoryTimelineToolbarProps extends EmployeeWorkHistoryToolbarTitleProps {
  /** Bỏ trống = tự làm mới MỌI query đang hoạt động — khớp mặc định của `DataTable`. */
  onRefresh?: () => void | Promise<unknown>
  /** Nút «Thêm dòng» — bỏ trống ở khu Quyết định (chỉ đọc) và ở thẻ Trang cá nhân `/me`. */
  addButton?: ReactNode
}

/**
 * Hàng công cụ Ở CHẾ ĐỘ DÒNG THỜI GIAN. `DataTable` không mount lúc này (xem
 * nhánh `view === 'timeline'` của `EmployeeWorkHistoryMainSection`/
 * `EmployeeWorkHistoryDecisionSection`), nên hàng tiêu đề + toggle + nút Tải
 * lại phải TỰ DỰNG ở đây — lặp lại đúng class của dải công cụ trong
 * `data-table.tsx` (`mb-4 flex shrink-0 flex-wrap items-center gap-3` +
 * `ml-auto flex items-center gap-2`) để đổi Bảng ↔ Dòng thời gian không nhảy
 * hình. KHÔNG có menu «Cột» ở đây — hết bảng thì hết cột để ẩn/hiện.
 */
export function EmployeeWorkHistoryTimelineToolbar({
  title,
  view,
  onChange,
  onRefresh,
  addButton,
}: EmployeeWorkHistoryTimelineToolbarProps) {
  const queryClient = useQueryClient()
  const [refreshing, setRefreshing] = useState(false)

  //  Cờ quay do CHÍNH nút giữ (không đọc `isFetching` của trang) — cùng lý do
  //  đã ghi ở `data-table.tsx`: dữ liệu về gần như tức thì vẫn phải thấy một
  //  nhịp phản hồi, không thì bấm xong chẳng thấy gì đổi.
  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    try {
      await (onRefresh ? onRefresh() : queryClient.invalidateQueries({ type: 'active' }))
    } finally {
      setRefreshing(false)
    }
  }, [onRefresh, queryClient])

  return (
    <div className="mb-4 flex shrink-0 flex-wrap items-center gap-3">
      <EmployeeWorkHistoryToolbarTitle title={title} view={view} onChange={onChange} />
      <div className="ml-auto flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon"
          title="Tải lại dữ liệu"
          aria-label="Tải lại dữ liệu"
          disabled={refreshing}
          onClick={handleRefresh}
        >
          <RotateCw className={cn('size-4', refreshing && 'animate-spin')} />
        </Button>
        {addButton}
      </div>
    </div>
  )
}
