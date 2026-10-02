import { ChartNoAxesColumn } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'

import type { ReportPeriod } from '../types/report-analytics'
import { formatReportRange } from '../utils/format-report-range'

interface ReportPeriodEmptyStateProps {
  /** Kỳ ĐÃ TÍNH LẠI từ backend — ghi đúng khoảng ngày vào câu giải thích. */
  period?: ReportPeriod
  /** "Xem cả năm nay" — `filters.applyPeriod({ preset: 'this_year', … })`. */
  onViewFullYear: () => void
}

/**
 * MỘT thông báo cho cả trang khi kỳ đang xem chưa phát sinh gì — thay cho biểu
 * đồ xu hướng, các khối Top và bảng "Xem theo". Trước đây mỗi khối tự báo rỗng
 * riêng (bốn năm câu "Chưa có dữ liệu" xếp chồng) và bảng thì vẽ nguyên một lưới
 * số 0 kèm "−100%" ở mọi ô — rối mà không nói thêm được gì. Hàng thẻ KPI phía
 * trên vẫn giữ, vì "0 so với kỳ trước" là thông tin thật.
 *
 * Đang xem "Năm nay" mà vẫn rỗng thì không mời "Xem cả năm nay" nữa (bấm vào
 * không đổi gì).
 */
export function ReportPeriodEmptyState({ period, onViewFullYear }: ReportPeriodEmptyStateProps) {
  const range = period ? formatReportRange(period.date_from, period.date_to) : ''
  const canWiden = period?.preset !== 'this_year'

  return (
    <Card className="flex flex-col items-center justify-center gap-2 px-4 py-14 text-center">
      <ChartNoAxesColumn className="size-10 text-muted-foreground/50" aria-hidden />
      <p className="text-sm font-medium text-foreground">Kỳ này chưa có dữ liệu</p>
      <p className="max-w-md text-sm text-muted-foreground">
        {range
          ? `Không có phát sinh nào trong ${range}.`
          : 'Không có phát sinh nào trong kỳ đang xem.'}
        {canWiden && ' Thử chọn một kỳ dài hơn.'}
      </p>
      {canWiden && (
        <Button variant="outline" size="sm" className="mt-1" onClick={onViewFullYear}>
          Xem cả năm nay
        </Button>
      )}
    </Card>
  )
}
