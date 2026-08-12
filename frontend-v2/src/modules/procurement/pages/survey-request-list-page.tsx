import { Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'
import { StatusBadge } from '../components/document-status-badge'
import { SURVEY_REQUEST_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { useSurveyRequests } from '../hooks/use-purchase-documents'
import {
  SR_STATUS_LABELS,
  statusOptions,
  type SurveyRequest,
} from '../types/purchase-document'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: SURVEY_REQUEST_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['company_id', 'status'],
}

export function SurveyRequestListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <SurveyRequestListContent />
    </FilterProvider>
  )
}

/**
 * Danh sách Yêu cầu báo giá (YCBG) — bước đầu của luồng: bộ phận nêu nhu cầu,
 * thu mua đi khảo sát giá rồi mới lên yêu cầu mua hàng.
 */
function SurveyRequestListContent() {
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { queryParams, queryKey } = useFilterQuery()

  useEffect(() => setPage(1), [queryKey, debouncedValue, companyId, status])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.code = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (status !== ALL) params.status = status

  const { data, isLoading, isError } = useSurveyRequests(params)

  const columns = useMemo<DataTableColumn<SurveyRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        width: 160,
        hideable: false,
        cell: (sr) => <span className="truncate font-medium">{sr.code}</span>,
      },
      { key: 'purpose', header: 'Mục đích', width: 280, cell: (sr) => sr.purpose || '—' },
      { key: 'requester', header: 'Người yêu cầu', width: 200, cell: (sr) => sr.requester || '—' },
      { key: 'department', header: 'Bộ phận', width: 180, cell: (sr) => sr.department || '—' },
      {
        key: 'created_at',
        header: 'Ngày tạo',
        width: 150,
        cell: (sr) => formatDateTime(sr.created_at) || '—',
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        cell: (sr) => <StatusBadge status={sr.status} labels={SR_STATUS_LABELS} />,
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Yêu cầu báo giá"
        description="Phiếu yêu cầu khảo sát giá (YCBG) trước khi lên yêu cầu mua hàng."
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(sr) => sr.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy yêu cầu báo giá nào."
          storageKey="procurement.survey-requests"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'phiếu',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo mã phiếu…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={companyId} onValueChange={setCompanyId}>
                <SelectTrigger className="w-52">
                  <SelectValue placeholder="Công ty" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả công ty</SelectItem>
                  {(companies?.items ?? []).map((company) => (
                    <SelectItem key={company.id} value={String(company.id)}>
                      {company.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {statusOptions(SR_STATUS_LABELS).map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <ConditionalFilter />
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
