import { useMemo, useState } from 'react'

import { extractErrorMessage } from '@/core/api'
import { allModules } from '@/app/router/module-registry'
import { DataTable } from '@/shared/data-table'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { formatDate, toDateInputValue } from '@/shared/utils/format-date'

import { FeatureUsageBreakdownSheet } from '../components/feature-usage/feature-usage-breakdown-sheet'
import {
  buildActionColumns,
  buildErrorColumns,
  buildFormColumns,
  buildScreenColumns,
  buildSearchColumns,
} from '../components/feature-usage/feature-usage-columns'
import { ALL_DEPARTMENTS, ReportDepartmentFilter } from '../components/report-department-filter'
import { FeatureUsageOverviewCards } from '../components/feature-usage/feature-usage-overview-cards'
import { ReportExportButton } from '../components/report-export-button'
import { ReportFiltersBar } from '../components/report-filters-bar'
import { ReportPageHeader } from '../components/report-page-header'
import { UsageProfileNoticeBanner } from '../components/usage-profile/usage-profile-notice-banner'
import { useFeatureUsage } from '../hooks/use-feature-usage'
import { useReportFilters } from '../hooks/use-report-filters'
import type { FeatureRow } from '../types/feature-usage'
import { actionName, formName, screenName, unusedNames } from '../utils/feature-usage-format'
import { findUnusedScreens } from '../utils/feature-usage-unused-screens'

const DEFAULT_PRESET = 'last_30_days'
const rowId = (r: FeatureRow) => `${r.kind}:${r.code}:${r.route}`

type Target = { kind: number; code: number; route: string; title: string }

function NamesCard({ title, names, empty }: { title: string; names: string[]; empty: string }) {
  return (
    <Card className="p-4">
      <p className="mb-2 text-sm font-medium">{title}</p>
      {names.length === 0 ? (
        <p className="text-sm text-muted-foreground">{empty}</p>
      ) : (
        <ul className="grid gap-x-6 gap-y-1 text-sm text-muted-foreground sm:grid-cols-2 lg:grid-cols-3">
          {names.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      )}
    </Card>
  )
}

/**
 * "Mức dùng chức năng" (duoc-CR-655, ReportKey 15): chức năng nào nhiều người dùng, cái nào không ai dùng,
 * biểu mẫu nào hay bỏ dở, màn nào hay lỗi. Gom theo chức năng / phòng ban — KHÔNG có số liệu theo từng người.
 */
export function FeatureUsageReportPage() {
  const filters = useReportFilters({ defaultGroupBy: 'none', defaultPreset: DEFAULT_PRESET })
  const [departmentId] = useUrlParamState('department_id', ALL_DEPARTMENTS)
  const [target, setTarget] = useState<Target | null>(null)

  const filterParams = useMemo(() => {
    const p: Record<string, string> = { preset: filters.preset }
    if (filters.preset === 'custom') Object.assign(p, { date_from: filters.from, date_to: filters.to })
    if (filters.company) p.company_id = filters.company
    if (departmentId !== ALL_DEPARTMENTS) p.department_id = departmentId
    return p
  }, [filters.preset, filters.from, filters.to, filters.company, departmentId])

  const { data, isLoading, isError, error } = useFeatureUsage(filterParams)
  const active = data?.active_users ?? 0
  const columns = useMemo(
    () => ({
      actions: buildActionColumns(active),
      forms: buildFormColumns(active),
      screens: buildScreenColumns(active),
      errors: buildErrorColumns(),
      searches: buildSearchColumns(),
    }),
    [active],
  )
  //  "Chưa ai mở" chỉ có nghĩa khi đã có số liệu — kỳ rỗng thì mọi màn đều "chưa ai mở", nói vậy là sai.
  const unusedScreens = useMemo(
    () => (data?.has_data ? findUnusedScreens(allModules, data.screens.map((s) => s.route)) : []),
    [data],
  )

  const today = toDateInputValue(new Date())
  const exportName = `muc-dung-chuc-nang-${data?.period.date_from ?? today}-${data?.period.date_to ?? today}.xlsx`
  const open = (kind: number) => (r: FeatureRow, title: string) => setTarget({ kind, code: r.code, route: r.route, title })

  const table = (rows: FeatureRow[] | undefined, cols: typeof columns.actions, key: string, empty: string, titleOf: (r: FeatureRow) => string, kind: number) => (
    <Card className="p-4">
      <DataTable
        columns={cols}
        rows={rows}
        getRowId={rowId}
        isLoading={isLoading}
        isError={isError}
        errorMessage={isError ? extractErrorMessage(error) : undefined}
        emptyMessage={empty}
        storageKey={`report.feature-usage.${key}`}
        onRowClick={kind === 0 ? undefined : (r) => open(kind)(r, titleOf(r))}
      />
    </Card>
  )

  return (
    <PageContainer>
      <ReportPageHeader
        title="Mức dùng chức năng"
        description="Chức năng nào nhiều người dùng, chức năng nào không ai dùng, chỗ nào hay bỏ dở hay lỗi. Gom theo phòng ban, không theo từng người."
        sourcePath={appRoutes.system.logs}
        exportButton={
          <ReportExportButton
            endpoint="/api/feature-usage/summary/export"
            entity="setting"
            params={filterParams}
            filename={exportName}
          />
        }
      />
      <div className="mb-3 space-y-2">
        <UsageProfileNoticeBanner />
        {data && !data.has_data && (
          <div role="status" className="rounded-md border border-dashed px-3 py-2 text-sm text-muted-foreground">
            Chưa thu thập — kỳ này chưa có thao tác nào được ghi nhận
            {data.tracking_since ? ` (số liệu có từ ngày ${formatDate(data.tracking_since)}).` : '. Công tắc thu thập có thể đang tắt hoặc chưa đến kỳ gom đầu tiên.'}
          </div>
        )}
        {data?.has_data && data.tracking_since && data.tracking_since > data.period.date_from && (
          <p className="text-sm text-muted-foreground">Số liệu chỉ có từ ngày {formatDate(data.tracking_since)}.</p>
        )}
        <ReportFiltersBar filters={filters} ExtraFilters={ReportDepartmentFilter} />
      </div>

      {isLoading && <Skeleton className="h-64 w-full" />}
      {data?.has_data && <FeatureUsageOverviewCards data={data} />}

      <Tabs defaultValue="actions" className="mt-3">
        <TabsList className="h-auto flex-wrap">
          <TabsTrigger value="actions">Chức năng</TabsTrigger>
          <TabsTrigger value="forms">Biểu mẫu</TabsTrigger>
          <TabsTrigger value="screens">Màn hình</TabsTrigger>
          <TabsTrigger value="errors">Lỗi và tìm kiếm</TabsTrigger>
        </TabsList>
        <TabsContent value="actions" className="space-y-3">
          {table(data?.actions, columns.actions, 'actions', 'Chưa có lượt bấm nào trong kỳ này.', (r) => actionName(r.code), 1)}
          {data?.has_data && (
            <NamesCard
              title="Chức năng chưa ai dùng trong kỳ"
              names={unusedNames(data.unused_actions, actionName)}
              empty="Mọi chức năng có đo đều đã được dùng."
            />
          )}
        </TabsContent>
        <TabsContent value="forms" className="space-y-3">
          {table(data?.forms, columns.forms, 'forms', 'Chưa có biểu mẫu nào được mở trong kỳ này.', (r) => formName(r.code), 2)}
          {data?.has_data && (
            <NamesCard
              title="Biểu mẫu chưa ai mở trong kỳ"
              names={unusedNames(data.unused_forms, formName)}
              empty="Mọi biểu mẫu có đo đều đã được mở."
            />
          )}
        </TabsContent>
        <TabsContent value="screens" className="space-y-3">
          {table(data?.screens, columns.screens, 'screens', 'Chưa có lượt xem màn hình nào trong kỳ này.', (r) => screenName(r.route), 3)}
          {data?.has_data && (
            <NamesCard
              title="Màn hình trong menu chưa ai mở trong kỳ"
              names={unusedScreens.map((s) => `${s.module} › ${s.label}`)}
              empty="Mọi màn trong menu đều có người mở."
            />
          )}
        </TabsContent>
        <TabsContent value="errors" className="space-y-3">
          <p className="text-sm font-medium">Lỗi giao diện theo màn hình</p>
          {table(data?.errors, columns.errors, 'errors', 'Không có lỗi giao diện nào trong kỳ này.', (r) => screenName(r.route), 5)}
          <p className="text-sm font-medium">Tìm kiếm theo màn hình</p>
          {table(data?.searches, columns.searches, 'searches', 'Chưa có lượt tìm kiếm nào trong kỳ này.', (r) => screenName(r.route), 0)}
        </TabsContent>
      </Tabs>
      <FeatureUsageBreakdownSheet target={target} filterParams={filterParams} onClose={() => setTarget(null)} />
    </PageContainer>
  )
}
