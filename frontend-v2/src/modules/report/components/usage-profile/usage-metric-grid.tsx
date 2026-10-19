import type { UsageSnapshot } from '../../types/usage-profile'
import { UsageMetricWithCohort } from './usage-metric-with-cohort'

interface UsageMetricGridProps {
  snapshot: UsageSnapshot
  keys: string[]
}

/** Lưới các thẻ chỉ số (`UsageMetricWithCohort`) theo danh sách khóa. */
export function UsageMetricGrid({ snapshot, keys }: UsageMetricGridProps) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {keys.map((key) => (
        <UsageMetricWithCohort key={key} snapshot={snapshot} metricKey={key} />
      ))}
    </div>
  )
}
