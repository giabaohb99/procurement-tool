import { render, screen } from '@testing-library/react'
import { BarChart3 } from 'lucide-react'
import { describe, expect, it, vi } from 'vitest'

import type { ReportCatalogEntry } from '../config/report-catalog'
import type { ReportOverviewEntry } from '../hooks/use-report-overview'
import type { ReportAnalyticsResponse, ReportMetricMeta } from '../types/report-analytics'
import { ReportOverviewKpiStrip } from './report-overview-kpi-strip'

function metric(
  overrides: Partial<ReportMetricMeta> & Pick<ReportMetricMeta, 'key' | 'label' | 'kind'>,
): ReportMetricMeta {
  return { good: null, helper: false, snapshot: false, ...overrides }
}

function buildReport(overrides: Partial<ReportCatalogEntry> = {}): ReportCatalogEntry {
  return {
    label: 'Báo cáo thử',
    description: '',
    path: '/report/test',
    sourcePath: '/procurement/test',
    icon: BarChart3,
    entity: 'report',
    group: 'Thu mua',
    endpoint: '/api/reports/test/summary',
    overviewKpis: ['spend'],
    load: async () => () => null,
    ...overrides,
  }
}

function buildData(
  metrics: ReportMetricMeta[],
  current: Record<string, number>,
): ReportAnalyticsResponse {
  return {
    period: {
      date_from: '2026-09-01',
      date_to: '2026-09-28',
      compare_from: null,
      compare_to: null,
      compare: 'none',
      granularity: 'day',
      preset: 'this_month',
    },
    meta: { metrics, dimensions: [], group_by: 'none' },
    totals: { current, compare: null },
    trend: [],
    notes: [],
  }
}

describe('ReportOverviewKpiStrip — helper metrics never render a card (item 4/7)', () => {
  it('skips an overviewKpis entry whose metric is flagged helper, keeps the others', () => {
    const report = buildReport({ overviewKpis: ['spend', 'helper_metric'] })
    const data = buildData(
      [
        metric({ key: 'spend', label: 'Chi phí', kind: 'money' }),
        metric({ key: 'helper_metric', label: 'Mẫu số phụ', kind: 'int', helper: true }),
      ],
      { spend: 100, helper_metric: 5 },
    )
    const entries: ReportOverviewEntry[] = [{ report, data, isLoading: false, isError: false }]

    render(
      <ReportOverviewKpiStrip
        entries={entries}
        compareMode="none"
        selected={null}
        onSelect={vi.fn()}
      />,
    )

    expect(screen.getByText('Chi phí')).toBeInTheDocument()
    expect(screen.queryByText('Mẫu số phụ')).not.toBeInTheDocument()
  })
})

describe('ReportOverviewKpiStrip — snapshot metric card is not clickable', () => {
  it('renders as a static card (no button role) so it cannot drive the trend chart', () => {
    const report = buildReport({ overviewKpis: ['debt'] })
    const data = buildData(
      [metric({ key: 'debt', label: 'Công nợ', kind: 'money', snapshot: true })],
      {
        debt: 133_100_000,
      },
    )
    const entries: ReportOverviewEntry[] = [{ report, data, isLoading: false, isError: false }]

    render(
      <ReportOverviewKpiStrip
        entries={entries}
        compareMode="none"
        selected={null}
        onSelect={vi.fn()}
      />,
    )

    expect(screen.getByText('Công nợ')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})

describe('ReportOverviewKpiStrip — null derived metric renders — instead of 0', () => {
  it('shows a dash when totals.current is missing the key (zero-denominator derived)', () => {
    const report = buildReport({ overviewKpis: ['on_time_rate'] })
    const data = buildData(
      [metric({ key: 'on_time_rate', label: 'Giao đúng hạn', kind: 'percent', good: 'up' })],
      {},
    )
    const entries: ReportOverviewEntry[] = [{ report, data, isLoading: false, isError: false }]

    render(
      <ReportOverviewKpiStrip
        entries={entries}
        compareMode="none"
        selected={null}
        onSelect={vi.fn()}
      />,
    )

    expect(screen.getByText('—')).toBeInTheDocument()
  })
})
