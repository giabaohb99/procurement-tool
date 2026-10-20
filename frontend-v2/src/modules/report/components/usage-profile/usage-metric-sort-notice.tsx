import { X } from 'lucide-react'

import { Button } from '@/shared/ui/button'

import { metricLabel } from '../../config/usage-metric-labels'

/** Dải «Đang sắp theo: <chỉ số>» (duoc-CR-650) kèm nút (X) bỏ chỉ số về danh sách thường. */
export function UsageMetricSortNotice({ metricKey, desc, onClear }: { metricKey: string; desc: boolean; onClear: () => void }) {
  return (
    <div className="flex items-center gap-2 rounded-md border bg-muted/40 px-3 py-1.5 text-sm">
      <span>
        Đang sắp theo: <span className="font-medium">{metricLabel(metricKey)}</span>{' '}
        <span className="text-muted-foreground">({desc ? 'cao nhất trước' : 'thấp nhất trước'}; người chưa đo xếp cuối)</span>
      </span>
      <Button type="button" variant="ghost" size="icon" className="ml-auto size-6" aria-label="Bỏ sắp theo chỉ số" onClick={onClear}>
        <X className="size-4" />
      </Button>
    </div>
  )
}
