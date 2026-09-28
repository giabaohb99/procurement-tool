import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip'
import { cn } from '@/shared/utils/cn'

import type { ReportTableRow } from '../utils/build-report-table-rows'
import { formatReportMetricValue } from '../utils/format-report-metric'
import { describeMetricChange, type MetricChangeKind } from '../utils/report-period-comparison'
import type { ReportCompareMode, ReportMetricMeta } from '../types/report-analytics'
import { ReportChangePill } from './report-change-pill'

interface ReportMetricValueCellProps {
  row: ReportTableRow
  metric: ReportMetricMeta
  compare: ReportCompareMode
}

/** Câu mô tả thay đổi trong tooltip — cùng phân loại với "pill", chỉ khác chỗ hiện: chữ thường, không icon. */
function changeTooltipLine(kind: MetricChangeKind, text: string): string | null {
  if (kind === 'unavailable') return null
  if (kind === 'new') return 'Mới so với kỳ trước'
  if (kind === 'flat') return 'Không đổi so với kỳ trước'
  return `Thay đổi: ${text}`
}

/**
 * MỘT ô giá trị của bảng "Xem theo".
 *
 * Dòng NHÓM chỉ hiện con số kỳ NÀY — giá trị kỳ trước + mức thay đổi lùi vào
 * tooltip (rê chuột), thay vì nhồi cả hai vào ô như bản cũ: bảy, tám cột mỗi ô
 * hai dòng ép cuộn ngang liên tục, còn "0 / ↘ −100%" ở kỳ rỗng đọc như lỗi.
 *
 * Dòng TỔNG (`row.isTotal`) là nơi DUY NHẤT hiện "pill" thay đổi ngay dưới con
 * số — đây là chỉ số tổng người xem cần thấy xu hướng ngay, không cần rê chuột.
 */
export function ReportMetricValueCell({ row, metric, compare }: ReportMetricValueCellProps) {
  const value = row.current[metric.key] ?? null
  const compareValue = row.compare?.[metric.key] ?? null
  const valueText = formatReportMetricValue(value, metric.kind, 'full')
  const mutedText = !row.isTotal && row.isEmpty ? 'text-muted-foreground' : undefined

  if (row.isTotal) {
    const description =
      compare === 'none'
        ? undefined
        : describeMetricChange(value, compareValue, metric.kind, metric.good)
    return (
      <div className="flex flex-col items-end gap-0.5">
        <span className="font-semibold tabular-nums">{valueText}</span>
        {description && <ReportChangePill description={description} />}
      </div>
    )
  }

  //  Không so sánh, hoặc dòng này thiếu MỘT trong hai vế (vd chỉ số `snapshot`
  //  vắng mặt ở `groups[]`, xem `ReportMetricMeta.snapshot`) — không có gì để
  //  nói thêm, khỏi bọc `Tooltip` (bọc suông vẫn tốn một lượt render Radix).
  if (compare === 'none' || value === null || compareValue === null) {
    return <span className={cn('tabular-nums', mutedText)}>{valueText}</span>
  }

  const description = describeMetricChange(value, compareValue, metric.kind, metric.good)
  const changeLine = changeTooltipLine(description.kind, description.text)

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={cn('cursor-help tabular-nums', mutedText)}>{valueText}</span>
      </TooltipTrigger>
      <TooltipContent side="top" className="flex flex-col gap-0.5">
        <span>Kỳ trước: {formatReportMetricValue(compareValue, metric.kind, 'full')}</span>
        {changeLine && <span>{changeLine}</span>}
      </TooltipContent>
    </Tooltip>
  )
}
