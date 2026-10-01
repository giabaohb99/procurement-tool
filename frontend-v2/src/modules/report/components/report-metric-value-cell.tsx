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
 * Dòng TỔNG (`row.isTotal`) hiện thêm mức thay đổi NGAY BÊN TRÁI con số, cùng
 * một dòng — con số vẫn sát mép phải để thẳng cột với các dòng nhóm. Chỉ hiện
 * khi có một con số thật (`kind: 'value'`): "Mới"/"Không đổi" lặp ở từng ô làm
 * dòng Tổng lổn nhổn mà không nói thêm được gì (đại ca chê 01/10/2026) — hai
 * trạng thái đó vẫn đọc được trong tooltip khi rê chuột.
 */
export function ReportMetricValueCell({ row, metric, compare }: ReportMetricValueCellProps) {
  const value = row.current[metric.key] ?? null
  const compareValue = row.compare?.[metric.key] ?? null
  const valueText = formatReportMetricValue(value, metric.kind, 'full')
  const mutedText = !row.isTotal && row.isEmpty ? 'text-muted-foreground' : undefined
  const canCompare = compare !== 'none' && value !== null && compareValue !== null

  if (row.isTotal) {
    const description = canCompare
      ? describeMetricChange(value, compareValue, metric.kind, metric.good)
      : undefined
    const valueNode = <span className="font-semibold tabular-nums">{valueText}</span>
    return (
      <div className="flex items-baseline justify-end gap-2">
        {description?.kind === 'value' && (
          <ReportChangePill description={description} variant="inline" />
        )}
        {description ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="cursor-help">{valueNode}</span>
            </TooltipTrigger>
            <TooltipContent side="top" className="flex flex-col gap-0.5">
              <span>Kỳ trước: {formatReportMetricValue(compareValue, metric.kind, 'full')}</span>
              {changeTooltipLine(description.kind, description.text) && (
                <span>{changeTooltipLine(description.kind, description.text)}</span>
              )}
            </TooltipContent>
          </Tooltip>
        ) : (
          valueNode
        )}
      </div>
    )
  }

  //  Không so sánh, hoặc dòng này thiếu MỘT trong hai vế (vd chỉ số `snapshot`
  //  vắng mặt ở `groups[]`, xem `ReportMetricMeta.snapshot`) — không có gì để
  //  nói thêm, khỏi bọc `Tooltip` (bọc suông vẫn tốn một lượt render Radix).
  if (!canCompare) {
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
