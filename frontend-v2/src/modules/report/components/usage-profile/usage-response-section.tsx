import type { UsageSnapshot } from '../../types/usage-profile'
import { UsageMetricGrid } from './usage-metric-grid'
import { UsageSectionCard } from './usage-section-card'

const KEYS = [
  'notif_read_rate',
  'notif_read_p50_min',
  'mention_reply_p50_h',
  'comments',
  'assistant_questions',
  'assistant_changes',
  'on_behalf_received',
  'on_behalf_done',
]

/** Phản hồi và phối hợp: đọc thông báo, nhắc tên → trả lời, bình luận, trợ lý AI, bấm hộ. */
export function UsageResponseSection({ snapshot }: { snapshot: UsageSnapshot }) {
  return (
    <UsageSectionCard title="Phản hồi và phối hợp">
      <UsageMetricGrid snapshot={snapshot} keys={KEYS} />
    </UsageSectionCard>
  )
}
