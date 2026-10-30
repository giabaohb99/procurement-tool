import { ImageDown } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'

import {
  FLEXIBLE_CHART_TOPS,
  FLEXIBLE_CHART_TYPE_LABELS,
  GROUP_CHART_TYPES,
  TIME_CHART_TYPES,
  type FlexibleChartBy,
  type FlexibleChartOptions,
  type FlexibleChartTop,
  type FlexibleChartType,
} from '../utils/report-flexible-chart-options'
import { DONUT_MAX_GROUPS } from '../utils/report-flexible-chart-series'

const TOP_LABELS: Record<FlexibleChartTop, string> = {
  '5': 'Top 5',
  '10': 'Top 10',
  '20': 'Top 20',
  all: 'Tất cả',
}

interface ReportFlexibleChartToolbarProps {
  options: FlexibleChartOptions
  hasTime: boolean
  /** Nhãn chiều "Xem theo" đang chọn; `null` = không vẽ theo nhóm được. */
  groupLabel: string | null
  donutAllowed: boolean
  onChange: (patch: Partial<FlexibleChartOptions>) => void
  onDownload: () => void
  downloadDisabled: boolean
}

/**
 * Hàng điều khiển của biểu đồ linh hoạt: "Vẽ theo" · Kiểu · Top N · Tải ảnh PNG. Xuống dòng ở
 * màn hẹp (390px) thay vì tràn ngang; nút PNG chỉ còn biểu tượng (kèm `aria-label`).
 */
export function ReportFlexibleChartToolbar({
  options,
  hasTime,
  groupLabel,
  donutAllowed,
  onChange,
  onDownload,
  downloadDisabled,
}: ReportFlexibleChartToolbarProps) {
  const types = options.by === 'time' ? TIME_CHART_TYPES : GROUP_CHART_TYPES
  const showBy = hasTime && groupLabel !== null

  return (
    <div className="flex flex-wrap items-center gap-2">
      {showBy && (
        <div className="flex items-center gap-1.5">
          <span className="text-sm text-muted-foreground">Vẽ theo</span>
          <Select value={options.by} onValueChange={(v) => onChange({ by: v as FlexibleChartBy })}>
            <SelectTrigger className="h-8 w-auto min-w-28 gap-1.5" aria-label="Vẽ theo">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="time">Thời gian</SelectItem>
              <SelectItem value="group">{groupLabel}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        aria-label="Kiểu biểu đồ"
        value={options.type}
        //  Radix trả `''` khi bấm lại nút đang bật — giữ nguyên kiểu, không có "không kiểu nào".
        onValueChange={(v) => v && onChange({ type: v as FlexibleChartType })}
      >
        {types.map((type) => {
          const disabled = type === 'donut' && !donutAllowed
          return (
            <ToggleGroupItem
              key={type}
              value={type}
              disabled={disabled}
              title={
                disabled
                  ? `Vành khuyên chỉ dùng khi có tối đa ${DONUT_MAX_GROUPS} nhóm có số, không âm và cộng gộp được (không phải tỷ lệ, bình quân)`
                  : undefined
              }
              className="text-xs"
            >
              {FLEXIBLE_CHART_TYPE_LABELS[type]}
            </ToggleGroupItem>
          )
        })}
      </ToggleGroup>

      {options.by === 'group' && (
        <Select value={options.top} onValueChange={(v) => onChange({ top: v as FlexibleChartTop })}>
          <SelectTrigger className="h-8 w-auto min-w-24 gap-1.5" aria-label="Số nhóm hiện">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {FLEXIBLE_CHART_TOPS.map((top) => (
              <SelectItem key={top} value={top}>
                {TOP_LABELS[top]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      <Button
        type="button"
        variant="outline"
        size="sm"
        className="ml-auto h-8"
        aria-label="Tải ảnh PNG"
        disabled={downloadDisabled}
        onClick={onDownload}
      >
        <ImageDown className="size-4" />
        <span className="hidden sm:inline">Tải ảnh PNG</span>
      </Button>
    </div>
  )
}
