import { Badge } from '@/shared/ui/badge'

import { metricLabel } from '../../config/usage-metric-labels'
import { USAGE_STYLE_HINTS, styleLabel } from '../../config/usage-style-hints'
import type { UsageSnapshot } from '../../types/usage-profile'
import { UsageSectionCard } from './usage-section-card'

/** Kiểu làm việc đã nhận được + bằng chứng (khóa chỉ số → nhãn) + gợi ý đọc. Chỉ để tham khảo. */
export function UsageStyleLabelsSection({ snapshot }: { snapshot: UsageSnapshot }) {
  const labels = [...(snapshot.labels ?? [])].sort((a, b) => b.score - a.score)
  return (
    <UsageSectionCard title="Kiểu làm việc" description="Nhãn gắn tự động theo tuần từ các chỉ số ở trên — gợi ý để hỏi, không phải kết luận về con người.">
      {labels.length === 0 ? (
        <p className="text-sm text-muted-foreground">Chưa nhận ra kiểu làm việc nào nổi bật (hoặc chưa đủ dữ liệu tối thiểu).</p>
      ) : (
        <ul className="space-y-3">
          {labels.map((l) => (
            <li key={l.code} className="space-y-1">
              <Badge variant="secondary">{styleLabel(l.code)}</Badge>
              {USAGE_STYLE_HINTS[l.code] && <p className="text-sm">{USAGE_STYLE_HINTS[l.code]}</p>}
              {l.evidence.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  Bằng chứng: {l.evidence.map((k) => metricLabel(k)).join(', ')}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </UsageSectionCard>
  )
}
