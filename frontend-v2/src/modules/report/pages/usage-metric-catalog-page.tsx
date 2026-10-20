import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { extractErrorMessage } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDate } from '@/shared/utils/format-date'

import { buildUsageMetricCatalogColumns } from '../components/usage-profile/usage-metric-catalog-columns'
import { UsageProfileNoticeBanner } from '../components/usage-profile/usage-profile-notice-banner'
import { ReportPageHeader } from '../components/report-page-header'
import { USAGE_DEFERRED_METRICS, USAGE_METRIC_SECTIONS } from '../config/usage-metric-definitions'
import { useUsageMetricCatalog } from '../hooks/use-usage-metric-catalog'

/**
 * «Bộ chỉ số đánh giá» (duoc-CR-649): từ điển các chỉ số của Hồ sơ cách làm việc — ý nghĩa, cách tính, nguồn,
 * chiều tốt/xấu — kèm trạng thái đo THỰC của tuần snapshot mới nhất. Bấm dòng mở danh sách Hồ sơ cách làm việc xếp theo chỉ số đó (duoc-CR-650).
 */
export function UsageMetricCatalogPage() {
  const navigate = useNavigate()
  const { data, isLoading, isError, error } = useUsageMetricCatalog()
  const hasWeek = Boolean(data?.week)
  const columns = useMemo(() => buildUsageMetricCatalogColumns(hasWeek), [hasWeek])
  const deferred = (data?.deferred ?? []).filter((k) => USAGE_DEFERRED_METRICS[k])

  return (
    <PageContainer>
      <ReportPageHeader
        title="Bộ chỉ số đánh giá"
        description="Từng chỉ số của Hồ sơ cách làm việc: ý nghĩa, cách tính, nguồn dữ liệu và tình trạng đo hiện tại."
        sourcePath={appRoutes.report.usageProfiles}
      />
      <div className="mb-3 space-y-2">
        <UsageProfileNoticeBanner />
        <p className="text-sm text-muted-foreground">
          {data?.week
            ? `Trạng thái tính theo bản chụp tuần bắt đầu ngày ${formatDate(data.week)}. Bấm vào một chỉ số đã có người đo để xem danh sách Hồ sơ cách làm việc xếp theo chỉ số đó.`
            : 'Chưa có bản chụp tuần nào nên chưa có số liệu đo.'}
        </p>
      </div>
      <Tabs defaultValue={USAGE_METRIC_SECTIONS[0].section}>
        <TabsList className="h-auto flex-wrap">
          {USAGE_METRIC_SECTIONS.map((s) => (
            <TabsTrigger key={s.section} value={s.section}>
              {s.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {USAGE_METRIC_SECTIONS.map((s) => (
          <TabsContent key={s.section} value={s.section}>
            <Card className="p-4">
              <DataTable
                columns={columns}
                rows={data?.metrics.filter((m) => m.section === s.section)}
                getRowId={(r) => r.key}
                isLoading={isLoading}
                isError={isError}
                errorMessage={isError ? extractErrorMessage(error) : undefined}
                emptyMessage="Chưa có chỉ số nào trong nhóm này."
                storageKey="report.usage-metric-catalog"
                onRowClick={(r) => r.measured_users > 0 && navigate(appRoutes.report.usageProfilesByMetric(r.key))}
                rowClassName={(r) => (r.measured_users > 0 ? undefined : 'cursor-default')}
              />
            </Card>
          </TabsContent>
        ))}
      </Tabs>
      {deferred.length > 0 && (
        <Card className="mt-4 space-y-2 p-4">
          <h2 className="text-base font-semibold">Chỉ số hoãn hoặc bỏ</h2>
          <p className="text-sm text-muted-foreground">Chưa có số liệu và chưa hứa sẽ có; ghi lại để không bị hỏi lại.</p>
          <ul className="space-y-1.5 text-sm">
            {deferred.map((k) => (
              <li key={k}>
                <span className="font-medium">{USAGE_DEFERRED_METRICS[k].title}.</span>{' '}
                <span className="text-muted-foreground">{USAGE_DEFERRED_METRICS[k].reason}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </PageContainer>
  )
}
