import { Card } from '@/shared/ui/card'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'

import { UI_ACTION, UI_FORM } from '@/shared/constants/statuses'

import type { FeatureSummary } from '../../types/feature-usage'
import { abandonRate, actionName, formName } from '../../utils/feature-usage-format'
import { formatCount, formatRatio } from '../../utils/usage-format'

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card className="p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </Card>
  )
}

/** Dải số tổng + hai biểu đồ cột (chức năng nhiều người dùng nhất · biểu mẫu hay bỏ dở nhất), cùng kiểu thẻ "Bộ chỉ số đánh giá". */
export function FeatureUsageOverviewCards({ data }: { data: FeatureSummary }) {
  const topActions = data.actions
    .reduce<Map<number, { users: number }>>((m, r) => m.set(r.code, { users: Math.max(m.get(r.code)?.users ?? 0, r.users) }), new Map())
  const actionBars = [...topActions.entries()]
    .map(([code, v]) => ({ label: actionName(code), value: v.users }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8)
  const formBars = data.forms
    .filter((f) => f.uses >= 3 && abandonRate(f) != null)
    .map((f) => ({ label: formName(f.code), value: Math.round((abandonRate(f) ?? 0) * 100) }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8)
  const totalCodes = UI_ACTION.length + UI_FORM.length
  const usedCodes = new Set(data.actions.map((a) => a.code)).size + data.forms.length

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Người có hoạt động trong kỳ" value={formatCount(data.active_users)} />
        <Stat label="Chức năng đã được dùng" value={`${usedCodes}/${totalCodes}`} hint="nút bấm và biểu mẫu có đo" />
        <Stat label="Chức năng chưa ai dùng" value={formatCount(data.unused_actions.length + data.unused_forms.length)} />
      </div>
      <div className="grid gap-3 lg:grid-cols-2">
        <Card className="p-4">
          <p className="mb-1 text-sm font-medium">Chức năng nhiều người dùng nhất</p>
          {actionBars.length > 0 ? <HorizontalBarChart data={actionBars} unit="người" /> : <p className="text-sm text-muted-foreground">Chưa có lượt bấm nào.</p>}
        </Card>
        <Card className="p-4">
          <p className="mb-1 text-sm font-medium">Biểu mẫu hay bị bỏ dở (% lượt mở)</p>
          {formBars.length > 0 ? (
            <HorizontalBarChart data={formBars} unit="%" formatValue={(v) => formatRatio(v / 100)} />
          ) : (
            <p className="text-sm text-muted-foreground">Chưa đủ lượt mở biểu mẫu để tính tỷ lệ bỏ dở (cần từ 3 lượt).</p>
          )}
        </Card>
      </div>
    </div>
  )
}
