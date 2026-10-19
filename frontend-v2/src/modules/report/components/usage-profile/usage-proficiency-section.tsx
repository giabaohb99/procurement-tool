import type { UsageSnapshot } from '../../types/usage-profile'
import { UsageMetricGrid } from './usage-metric-grid'
import { UsageSectionCard } from './usage-section-card'

const KEYS = [
  'saved_prefs',
  'http_422_per_100_writes',
  'search_empty_rate',
  'help_views',
  'tickets',
  'exports',
  'export_per_list_view',
  'imports',
  'import_error_rate',
  'distinct_screens_30d',
]

/** Mức thành thạo: bộ lọc đã lưu, lỗi nhập, tìm không ra, hướng dẫn/hỗ trợ, xuất Excel. */
export function UsageProficiencySection({ snapshot }: { snapshot: UsageSnapshot }) {
  return (
    <UsageSectionCard title="Mức thành thạo">
      <UsageMetricGrid snapshot={snapshot} keys={KEYS} />
    </UsageSectionCard>
  )
}
