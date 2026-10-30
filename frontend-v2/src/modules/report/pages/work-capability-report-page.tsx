import { Info } from 'lucide-react'
import { useMemo } from 'react'

import { extractErrorMessage } from '@/core/api'
import { DataTable } from '@/shared/data-table'
import { Card } from '@/shared/ui/card'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { toDateInputValue } from '@/shared/utils/format-date'

import { ALL_DEPARTMENTS } from '../components/report-department-filter'
import { buildPersonColumns, buildTypeColumns } from '../components/work-capability/work-capability-columns'
import { ALL, DEFAULT_ROLE, WorkCapabilityFilters } from '../components/work-capability/work-capability-filters'
import { WorkLoadPanel } from '../components/work-capability/work-load-panel'
import { ReportExportButton } from '../components/report-export-button'
import { ReportFiltersBar } from '../components/report-filters-bar'
import { ReportPageHeader } from '../components/report-page-header'
import { useReportFilters } from '../hooks/use-report-filters'
import { useWorkCapability } from '../hooks/use-work-capability'
import type { CapabilityPersonRow, CapabilityTypeRow } from '../types/work-capability'
import { formatDays, typeLabel } from '../utils/work-capability-format'

const DEFAULT_PRESET = 'last_30_days'
//  Cột không phụ thuộc dữ liệu nên dựng một lần ở mức module.
const typeColumns = buildTypeColumns()
const personColumns = buildPersonColumns()
const typeRowId = (r: CapabilityTypeRow) => `${r.kind}:${r.task_type_id}`
const personRowId = (r: CapabilityPersonRow) => `${r.kind}:${r.task_type_id}:${r.employee_id}`

/** Dải nhắc đầu trang: chốt của chủ sản phẩm 20/10/2026 — chỉ để tham khảo, không chấm điểm; "chậm" có thể là việc khó. */
function CapabilityNotice() {
  return (
    <div
      role="note"
      className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100"
    >
      <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span>
        Số liệu chỉ dùng tham khảo, không dùng để chấm điểm hay xếp hạng người. <strong>Chậm</strong> có thể chỉ vì việc khó hơn, nhiều bước hơn hoặc phải chờ bên
        khác. Ô <strong>chưa đủ mẫu</strong> nghĩa là dưới 5 phiếu cùng loại; phiếu có mốc xong là ước tính được đếm riêng, không nằm trong trung vị và P90.
      </span>
    </div>
  )
}

/**
 * "Năng lực theo loại việc" (duoc-CR-657, ReportKey 16): mỗi loại phiếu / loại việc mất bao lâu, làm lại bao nhiêu,
 * từng người trong loại đó (chỉ khi ≥ 5 mẫu) và tải đang ôm tức thì. Mặc định chỉ quản trị.
 */
export function WorkCapabilityReportPage() {
  const filters = useReportFilters({ defaultGroupBy: 'none', defaultPreset: DEFAULT_PRESET })
  const [departmentId] = useUrlParamState('department_id', ALL_DEPARTMENTS)
  const [kind] = useUrlParamState('kind', ALL)
  const [taskType] = useUrlParamState('task_type_id', ALL)
  const [role] = useUrlParamState('role', DEFAULT_ROLE)

  const filterParams = useMemo(() => {
    const p: Record<string, string> = { preset: filters.preset, role }
    if (filters.preset === 'custom') Object.assign(p, { date_from: filters.from, date_to: filters.to })
    if (filters.company) p.company_id = filters.company
    if (departmentId !== ALL_DEPARTMENTS) p.department_id = departmentId
    if (kind !== ALL) p.kind = kind
    if (kind !== ALL && taskType !== ALL) p.task_type_id = taskType
    return p
  }, [filters.preset, filters.from, filters.to, filters.company, departmentId, kind, taskType, role])

  //  Tải đang ôm không phụ thuộc kỳ / loại phiếu — chỉ cần phạm vi người.
  const loadParams = useMemo(() => {
    const p: Record<string, string> = {}
    if (filters.company) p.company_id = filters.company
    if (departmentId !== ALL_DEPARTMENTS) p.department_id = departmentId
    return Object.keys(p).length > 0 ? p : null
  }, [filters.company, departmentId])

  const { data, isLoading, isError, error } = useWorkCapability(filterParams)
  const bars = useMemo(
    () =>
      (data?.types ?? [])
        .filter((t) => t.p50_days != null)
        .map((t) => ({ label: typeLabel(t), value: t.p50_days ?? 0 }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 8),
    [data],
  )

  const today = toDateInputValue(new Date())
  const exportName = `nang-luc-theo-loai-viec-${data?.period.date_from ?? today}-${data?.period.date_to ?? today}.xlsx`
  const errorMessage = isError ? extractErrorMessage(error) : undefined

  return (
    <PageContainer>
      <ReportPageHeader
        title="Năng lực theo loại việc"
        description="Mỗi loại phiếu / loại việc mất bao lâu, làm lại bao nhiêu lần, ai đang ôm bao nhiêu việc. Chỉ quản trị xem được số theo từng người."
        sourcePath={appRoutes.system.logs}
        exportButton={
          <ReportExportButton endpoint="/api/work-capability/summary/export" entity="setting" params={filterParams} filename={exportName} />
        }
      />
      <div className="mb-3 space-y-2">
        <CapabilityNotice />
        {data?.truncated && (
          <p role="status" className="text-sm text-muted-foreground">
            Kỳ quá lớn nên chỉ đọc được một phần số liệu — hãy thu hẹp kỳ hoặc lọc theo phòng ban.
          </p>
        )}
        <ReportFiltersBar filters={filters} ExtraFilters={WorkCapabilityFilters} />
      </div>

      {isLoading && <Skeleton className="h-64 w-full" />}
      {/* Khung biểu đồ LUÔN dựng khi đã có số: trước đây thiếu cột là ẩn cả khung, người xem tưởng biểu
          đồ bị mất. Loại dưới `min_samples` phiếu không có trung vị nên không lên cột — nói rõ điều đó. */}
      {data && (
        <Card className="mb-3 p-4">
          <p className="mb-1 text-sm font-medium">Thời gian trọn vòng — trung vị (ngày)</p>
          {bars.length > 0 ? (
            <HorizontalBarChart data={bars} unit="ngày" formatValue={(v) => formatDays(v)} />
          ) : (
            <p className="py-6 text-sm text-muted-foreground">
              {data.types.length === 0
                ? 'Chưa có phiếu nào xong trong kỳ này — chọn kỳ dài hơn để xem biểu đồ.'
                : `Chưa loại việc nào đủ ${data.min_samples} phiếu xong trong kỳ để tính trung vị — chọn kỳ dài hơn hoặc bỏ bớt bộ lọc.`}
            </p>
          )}
        </Card>
      )}

      <Tabs defaultValue="types">
        <TabsList className="h-auto flex-wrap">
          <TabsTrigger value="types">Theo loại việc</TabsTrigger>
          <TabsTrigger value="people">Theo người</TabsTrigger>
          <TabsTrigger value="load">Tải đang ôm</TabsTrigger>
        </TabsList>
        <TabsContent value="types">
          <Card className="p-4">
            <DataTable
              columns={typeColumns}
              rows={data?.types}
              getRowId={typeRowId}
              isLoading={isLoading}
              isError={isError}
              errorMessage={errorMessage}
              emptyMessage="Chưa có phiếu nào xong trong kỳ này."
              storageKey="report.work-capability.types"
            />
          </Card>
        </TabsContent>
        <TabsContent value="people">
          <Card className="p-4">
            <DataTable
              columns={personColumns}
              rows={data?.people}
              getRowId={personRowId}
              isLoading={isLoading}
              isError={isError}
              errorMessage={errorMessage}
              emptyMessage="Chưa có phiếu nào xong trong kỳ này."
              storageKey="report.work-capability.people"
            />
          </Card>
        </TabsContent>
        <TabsContent value="load">
          <WorkLoadPanel params={loadParams} />
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
