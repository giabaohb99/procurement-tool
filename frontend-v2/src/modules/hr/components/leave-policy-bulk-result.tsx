import { CircleCheck, X } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import type { PolicyBulkResult } from '../types/leave-policy'
import { describeBalanceChanges } from '../utils/leave-policy-display'

interface LeavePolicyBulkResultProps {
  result: PolicyBulkResult
  onDismiss: () => void
}

/**
 * Khung KẾT QUẢ sau khi phân bổ hàng loạt (duoc-CR-717). Số ở đây là số THẬT lúc lưu (không phải số xem
 * trước) — dữ liệu đổi giữa lúc xem và lúc bấm thì người vướng rơi vào "Bỏ qua" kèm lý do.
 */
export function LeavePolicyBulkResult({ result, onDismiss }: LeavePolicyBulkResultProps) {
  const people = new Set(result.balances.recalculated.map((r) => r.employee_id)).size
  return (
    <Card role="status" className="gap-3 border-success/40">
      <CardHeader className="flex flex-row items-start justify-between gap-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <CircleCheck className="size-5 text-success" />
          Đã phân bổ {result.created} · Bỏ qua {result.skipped.length}
        </CardTitle>
        <Button type="button" variant="ghost" size="icon" aria-label="Đóng kết quả" onClick={onDismiss}>
          <X className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p>
          {describeBalanceChanges(result.balances)}
          {people > 0 && ` (${people} người được tính lại.)`}
        </p>
        {result.skipped.length > 0 && (
          <div className="space-y-1">
            <p className="font-medium">Người bị bỏ qua</p>
            <ul className="divide-y rounded-md border">
              {result.skipped.map((s) => (
                <li key={s.employee_id} className="flex flex-wrap gap-x-3 px-3 py-1.5">
                  <span className="font-medium">{s.name || `Nhân sự #${s.employee_id}`}</span>
                  <span className="text-muted-foreground">{s.reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
