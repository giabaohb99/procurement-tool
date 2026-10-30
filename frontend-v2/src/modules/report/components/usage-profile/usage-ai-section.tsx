import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'

import type { UsageSnapshot } from '../../types/usage-profile'
import { channelBars, clientBars, isAiNotCollected, toolGroupBars, type UsageAiBar } from '../../utils/usage-ai-helpers'
import { UsageMetricGrid } from './usage-metric-grid'
import { UsageSectionCard } from './usage-section-card'

const KEYS = [
  'ai_uses',
  'ai_active_days',
  'ai_mcp_share',
  'ai_tool_groups_used',
  'ai_docs_drafted',
  'ai_docs_share',
  'ai_drafts_confirmed',
  'ai_denied',
]

function BarCard({ title, bars }: { title: string; bars: UsageAiBar[] }) {
  if (bars.length === 0) return null
  return (
    <div className="rounded-md border p-3">
      <p className="mb-1 text-xs text-muted-foreground">{title}</p>
      <HorizontalBarChart data={bars} unit="lượt" />
    </div>
  )
}

/**
 * Dùng AI (nhóm 3.8): lượt dùng, kênh nào, ứng dụng nào, nhờ nhóm việc gì, bao nhiêu phiếu AI soạn.
 * Chỉ số đếm và mã — không có nội dung câu hỏi. Chưa thu số liệu thì nói rõ "chưa thu thập", không hiện 0.
 */
export function UsageAiSection({ snapshot }: { snapshot: UsageSnapshot }) {
  if (isAiNotCollected(snapshot)) {
    return (
      <UsageSectionCard title="Dùng AI">
        <p className="text-sm text-muted-foreground">
          Chưa thu thập — hệ thống chưa nhận số liệu dùng AI cho kỳ này.
        </p>
      </UsageSectionCard>
    )
  }
  return (
    <UsageSectionCard title="Dùng AI" description="Chỉ đếm lượt và nhóm việc, không lưu nội dung câu hỏi.">
      <UsageMetricGrid snapshot={snapshot} keys={KEYS} />
      <div className="grid gap-2 lg:grid-cols-3">
        <BarCard title="Kênh dùng" bars={channelBars(snapshot)} />
        <BarCard title="Ứng dụng AI ngoài" bars={clientBars(snapshot)} />
        <BarCard title="Nhóm việc nhờ AI" bars={toolGroupBars(snapshot)} />
      </div>
    </UsageSectionCard>
  )
}
