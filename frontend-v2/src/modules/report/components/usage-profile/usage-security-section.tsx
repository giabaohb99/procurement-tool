import { ShieldCheck } from 'lucide-react'

import type { UsageSnapshot } from '../../types/usage-profile'
import { findSecurityFlags } from '../../utils/usage-profile-helpers'
import { UsageMetricWithCohort } from './usage-metric-with-cohort'
import { UsageSectionCard } from './usage-section-card'

/** An toàn tài khoản — rỗng thì nói rõ «Không có gì bất thường» thay vì để trống. */
export function UsageSecuritySection({ snapshot }: { snapshot: UsageSnapshot }) {
  const flags = findSecurityFlags(snapshot)
  return (
    <UsageSectionCard title="An toàn tài khoản">
      {flags.length === 0 ? (
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <ShieldCheck className="size-4" aria-hidden />
          Không có gì bất thường
        </p>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {flags.map((key) => (
            <UsageMetricWithCohort
              key={key}
              snapshot={snapshot}
              metricKey={key}
            />
          ))}
        </div>
      )}
    </UsageSectionCard>
  )
}
