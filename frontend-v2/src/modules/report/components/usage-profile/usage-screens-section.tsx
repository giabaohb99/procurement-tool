import { useMemo } from 'react'

import { DonutChart } from '@/shared/ui/donut-chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { CHART_COLORS, CHART_NEUTRAL } from '@/shared/ui/chart'

import type { UsageProfileDetail, UsageSnapshot } from '../../types/usage-profile'
import { formatDurationMs } from '../../utils/usage-format'
import { sumDwellByModule } from '../../utils/usage-profile-helpers'
import { labelRouteInApp } from '../../utils/usage-route-label'
import { UsageSectionCard } from './usage-section-card'

const screenName = (route: string) => {
  const l = labelRouteInApp(route)
  return l.module ? `${l.module} › ${l.screen}` : l.screen
}

/** Bảng màu có 4 bậc: giữ 3 phân hệ đầu, phần còn lại gom «Khác» (xám trung tính). */
function groupSlices(slices: { label: string; value: number }[]) {
  const head = slices.length > CHART_COLORS.length ? slices.slice(0, CHART_COLORS.length - 1) : slices
  const rest = slices.slice(head.length)
  const out = head.map((d, i) => ({ ...d, color: CHART_COLORS[i] as string }))
  if (rest.length > 0) out.push({ label: 'Khác', value: rest.reduce((a, d) => a + d.value, 0), color: CHART_NEUTRAL })
  return out
}

/** Màn hay vào: top 10 màn · % thời gian theo phân hệ · ở lâu nhất · màn mở đầu ngày · đường đi hay gặp. */
export function UsageScreensSection({ profile, snapshot }: { profile: UsageProfileDetail; snapshot: UsageSnapshot }) {
  const { top, donut, longest } = useMemo(() => {
    const byViews = [...profile.screens].sort((a, b) => b.views - a.views || b.api_calls - a.api_calls)
    return {
      top: byViews.slice(0, 10).map((s) => ({ label: screenName(s.route), value: s.views || s.api_calls })),
      donut: groupSlices(sumDwellByModule(profile.screens, (r) => labelRouteInApp(r).module)),
      longest: [...profile.screens].sort((a, b) => b.dwell_ms - a.dwell_ms)[0],
    }
  }, [profile.screens])

  const estimated = profile.screens.length > 0 && profile.screens_source === 2
  const first = snapshot.lists?.first_screen?.length ? snapshot.lists.first_screen : null
  const paths = snapshot.lists?.top_paths ?? []

  if (profile.screens.length === 0) {
    return (
      <UsageSectionCard title="Màn hay vào">
        <p className="text-sm text-muted-foreground">Chưa đo được — chưa có dữ liệu màn hình trong kỳ.</p>
      </UsageSectionCard>
    )
  }

  return (
    <UsageSectionCard title="Màn hay vào" description={estimated ? 'Ước lượng từ lời gọi API (chưa có sự kiện giao diện).' : undefined}>
      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="mb-1 text-sm font-medium">Top 10 màn</h3>
          <HorizontalBarChart data={top} unit="lượt" />
        </div>
        <div>
          <h3 className="mb-1 text-sm font-medium">Thời gian theo phân hệ</h3>
          {donut.length > 0 ? (
            <DonutChart data={donut} centerLabel="thời gian" formatTotal={formatDurationMs} formatValue={formatDurationMs} />
          ) : (
            <p className="text-sm text-muted-foreground">Chưa đo được — cần sự kiện giao diện.</p>
          )}
        </div>
      </div>
      <dl className="grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-muted-foreground">Ở lâu nhất</dt>
          <dd>{longest && longest.dwell_ms > 0 ? `${screenName(longest.route)} (${formatDurationMs(longest.dwell_ms)})` : 'Chưa đo được'}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Màn mở đầu ngày</dt>
          <dd>{first ? `${screenName(first[0])} (${first[1]} ngày)` : 'Chưa đo được'}</dd>
        </div>
      </dl>
      {paths.length > 0 && (
        <div>
          <h3 className="mb-1 text-sm font-medium">Đường đi hay gặp</h3>
          <ul className="space-y-1 text-sm">
            {paths.slice(0, 5).map(([a, b, c, n]) => (
              <li key={`${a}|${b}|${c}`}>
                {[a, b, c].map((r) => labelRouteInApp(r).screen).join(' → ')}{' '}
                <span className="text-muted-foreground">({n} lần)</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </UsageSectionCard>
  )
}
