import { Plus } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'

/**
 * Trường chung của một dòng "kết quả khảo sát đã duyệt" ở hai bàn xử lý
 * (`AvailablePrSurveyLine` của YCMH, `AvailableSurveyLine` của YCBG).
 */
export interface AvailableSurveyLineCardData {
  supplier_code: string
  supplier_name: string
  product_name: string
  spec: string
  price_by_volume: number
  moq: number
  quote_unit: string
  survey_item_group: string
  result_date: string
  survey_code: string
}

interface AvailableSurveyLineCardProps {
  row: AvailableSurveyLineCardData
  /** Phân loại của dòng đang xử lý — lệch thì gắn cờ cảnh báo, cùng luật với bảng. */
  lineItemGroup: string
  /** "YCMH" / "YCBG" — để câu gợi ý của cờ lệch phân loại nói đúng loại phiếu. */
  documentLabel: string
  attaching: boolean
  onAttach: () => void
}

/**
 * Một kết quả khảo sát chọn được làm phương án, ở khổ điện thoại.
 *
 * ⚠️ **Nút Gắn có CHỮ, không chỉ dấu cộng**: ở bảng dấu cộng nằm dưới tiêu đề cột
 * nên đủ hiểu; ở thẻ không còn tiêu đề cột nào, một ô vuông có dấu cộng đọc ra như
 * "thêm NCC mới". Nút là ANH EM của khối chữ — thẻ không phải vùng bấm.
 */
export function AvailableSurveyLineCard({
  row,
  lineItemGroup,
  documentLabel,
  attaching,
  onAttach,
}: AvailableSurveyLineCardProps) {
  const groupMismatch =
    !!row.survey_item_group && !!lineItemGroup && row.survey_item_group !== lineItemGroup
  const meta = [formatDate(row.result_date), row.survey_item_group].filter(Boolean)

  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-medium break-words text-foreground">
          {row.supplier_name || row.supplier_code || '—'}
        </p>

        <p className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
          <span className="font-medium text-sky-600 dark:text-sky-400">
            {row.survey_code || '—'}
          </span>
          {meta.map((text) => (
            <span key={text}>
              <span aria-hidden="true">· </span>
              {text}
            </span>
          ))}
          {groupMismatch && (
            <Badge
              variant="secondary"
              className="border-0 bg-warning/10 text-warning"
              title={`Khác phân loại của dòng ${documentLabel}`}
            >
              ≠ phân loại
            </Badge>
          )}
        </p>

        <p className="text-sm break-words">
          {row.product_name || '—'}
          {row.spec && <span className="block text-xs text-muted-foreground">{row.spec}</span>}
        </p>

        <p className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs text-muted-foreground">
          <span className="text-sm font-semibold tabular-nums text-foreground">
            {row.price_by_volume
              ? `${formatUnitPrice(row.price_by_volume)} đ${row.quote_unit ? `/${row.quote_unit}` : ''}`
              : 'Chưa có giá'}
          </span>
          {!!row.moq && <span className="tabular-nums">MOQ {formatQuantity(row.moq)}</span>}
        </p>
      </div>

      <Button
        type="button"
        variant="outline"
        size="sm"
        className="shrink-0"
        title="Gắn làm phương án"
        disabled={attaching}
        onClick={onAttach}
      >
        <Plus />
        Gắn
      </Button>
    </div>
  )
}
