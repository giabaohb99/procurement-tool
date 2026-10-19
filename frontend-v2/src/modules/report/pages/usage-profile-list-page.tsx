import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { extractErrorMessage } from '@/core/api'
import { appConfig } from '@/core/config/app-config'
import { DataTable } from '@/shared/data-table'
import { appRoutes } from '@/shared/constants/app-routes'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { formatDate, toDateInputValue } from '@/shared/utils/format-date'

import { ReportExportButton } from '../components/report-export-button'
import { ReportFiltersBar } from '../components/report-filters-bar'
import { ReportPageHeader } from '../components/report-page-header'
import { buildUsageProfileColumns } from '../components/usage-profile/usage-profile-columns'
import { ALL, UsageProfileFilters } from '../components/usage-profile/usage-profile-filters'
import { UsageProfileNoticeBanner } from '../components/usage-profile/usage-profile-notice-banner'
import { useReportFilters } from '../hooks/use-report-filters'
import { useUsageProfileList } from '../hooks/use-usage-profile-list'

/** Kỳ mặc định khi URL chưa có: 30 ngày qua (≈ 4 tuần). */
const DEFAULT_PRESET = 'last_30_days'

/** Danh sách «Hồ sơ cách làm việc» (duoc-CR-641): lọc kỳ/pháp nhân/phòng/vai trò/kiểu, bấm dòng mở hồ sơ. */
export function UsageProfileListPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const filters = useReportFilters({ defaultGroupBy: 'none', defaultPreset: DEFAULT_PRESET })
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const departmentId = searchParams.get('department_id') ?? ALL
  const roleId = searchParams.get('role_id') ?? ALL
  const labelParam = searchParams.get('label') ?? ''

  const filterParams = useMemo(() => {
    const p: Record<string, string | number | string[]> = { preset: filters.preset }
    if (filters.preset === 'custom') {
      Object.assign(p, { date_from: filters.from, date_to: filters.to })
    }
    if (filters.company) p.company_id = filters.company
    if (departmentId !== ALL) p.department_id = departmentId
    if (roleId !== ALL) p.role_id = roleId
    if (labelParam) p.label = labelParam.split(',').filter(Boolean)
    if (debouncedValue) p.q = debouncedValue
    return p
  }, [filters.preset, filters.from, filters.to, filters.company, departmentId, roleId, labelParam, debouncedValue])

  const [page, setPage] = usePageResetOnFilterChange([JSON.stringify(filterParams)])
  const { data, isLoading, isError, error } = useUsageProfileList({ ...filterParams, page, page_size: pageSize })
  const columns = useMemo(() => buildUsageProfileColumns(), [])

  const today = toDateInputValue(new Date())
  const exportName = `ho-so-cach-lam-viec-${data?.period?.date_from ?? today}-${data?.period?.date_to ?? today}.xlsx`

  return (
    <PageContainer fill>
      <ReportPageHeader
        title="Hồ sơ cách làm việc"
        description="Nhịp làm việc, màn hay vào, cách làm phiếu và kiểu làm việc của từng người."
        exportButton={
          <ReportExportButton
            endpoint="/api/usage-profiles/summary/export"
            entity="setting"
            params={Object.fromEntries(Object.entries(filterParams).map(([k, v]) => [k, Array.isArray(v) ? v : String(v)]))}
            filename={exportName}
          />
        }
      />
      <div className="mb-3 space-y-2">
        <UsageProfileNoticeBanner />
        <p className="text-sm text-muted-foreground">
          {data?.data_since
            ? `Số liệu có từ ngày ${formatDate(data.data_since)}; sự kiện giao diện từ khi bật thu thập.`
            : 'Sự kiện giao diện chỉ có từ khi bật thu thập.'}
        </p>
        <ReportFiltersBar filters={filters} />
      </div>
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.user_id}
          isLoading={isLoading}
          isError={isError}
          errorMessage={isError ? extractErrorMessage(error) : undefined}
          emptyMessage={
            Object.keys(filterParams).length > 1 || debouncedValue
              ? 'Không có ai khớp bộ lọc hiện tại.'
              : 'Chưa có số liệu hồ sơ nào trong kỳ này.'
          }
          storageKey="report.usage-profiles"
          onRowClick={(r) => navigate(appRoutes.report.usageProfileDetail(r.user_id))}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'người',
          }}
          toolbar={<UsageProfileFilters keyword={keyword} onKeywordChange={setKeyword} />}
        />
      </Card>
    </PageContainer>
  )
}
