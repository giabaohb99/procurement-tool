import type { UsageProfileDetail, UsageSnapshot } from '../../types/usage-profile'
import { UsageDayStrip } from './usage-day-strip'
import { UsageHourWeekdayHeatmap } from './usage-hour-weekday-heatmap'
import { UsageMetricGrid } from './usage-metric-grid'
import { UsageSectionCard } from './usage-section-card'

const KEYS = [
  'first_seen_p50_min',
  'last_action_p50_min',
  'active_ratio',
  'workdays_net',
  'bursts_per_day',
  'active_minutes_p50',
  'offhours_write_share',
  'mobile_write_share',
  'logins',
]

/** Nhịp làm việc: giờ vào/ra, ngày có vào, phiên, ngoài giờ, điện thoại + bản đồ nhiệt + dải ngày. */
export function UsageRhythmSection({ profile, snapshot }: { profile: UsageProfileDetail; snapshot: UsageSnapshot }) {
  return (
    <UsageSectionCard title="Nhịp làm việc" description="Giờ giấc và độ đều đặn, tính theo Lịch làm việc, đã trừ lễ và ngày nghỉ phép.">
      <UsageMetricGrid snapshot={snapshot} keys={KEYS} />
      <div className="space-y-1">
        <h3 className="text-sm font-medium">Thao tác theo giờ và thứ</h3>
        <UsageHourWeekdayHeatmap grid={profile.heatmap} />
      </div>
      <div className="space-y-1">
        <h3 className="text-sm font-medium">Từng ngày</h3>
        <UsageDayStrip days={profile.daily} />
      </div>
    </UsageSectionCard>
  )
}
