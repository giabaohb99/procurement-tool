import { Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
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
import { SURVEY_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { useSurveys } from '../hooks/use-purchase-documents'
import {
  SURVEY_STATUS_LABELS,
  SURVEY_TYPE_LABELS,
  statusOptions,
  type Survey,
} from '../types/purchase-document'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: SURVEY_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['status', 'product_code'],
}

export function SurveyListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <SurveyListContent />
    </FilterProvider>
  )
}

/**
 * Danh sách Phiếu khảo sát (khảo sát NCC hoặc khảo sát sản phẩm).
 *
 * "Mã SP (NCC)" để ở thanh công cụ: mã đó nằm ở DÒNG sản phẩm của phiếu, backend
 * lọc bằng subquery nên không dùng được trong bộ lọc nâng cao.
 */
function SurveyListContent() {
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { queryParams, queryKey } = useFilterQuery()

  useEffect(() => setPage(1), [queryKey, debouncedValue, status])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.code = debouncedValue
  if (status !== ALL) params.status = status

  const { data, isLoading, isError } = useSurveys(params)

  const columns = useMemo<DataTableColumn<Survey>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        width: 160,
        hideable: false,
        // 9 cột, có cột nội dung dài -> ghim mã phiếu.
        defaultPinned: true,
        cell: (survey) => <span className="truncate font-medium">{survey.code}</span>,
      },
      {
        key: 'survey_type',
        header: 'Loại',
        width: 130,
        cell: (survey) => (
          <Badge variant="outline">
            {SURVEY_TYPE_LABELS[survey.survey_type] ?? survey.survey_type}
          </Badge>
        ),
      },
      { key: 'sr_code', header: 'Mã YCBG', width: 140, cell: (survey) => survey.sr_code || '—' },
      {
        key: 'main_content',
        header: 'Nội dung chính',
        width: 280,
        cell: (survey) => (
          <span className="truncate" title={survey.main_content}>
            {survey.main_content || '—'}
          </span>
        ),
      },
      { key: 'item_code', header: 'Mã hàng', width: 140, cell: (survey) => survey.item_code || '—' },
      {
        key: 'item_group',
        header: 'Nhóm hàng',
        width: 160,
        cell: (survey) => survey.item_group || '—',
      },
      { key: 'nspt', header: 'NSPT', width: 170, cell: (survey) => survey.nspt || '—' },
      {
        key: 'created_at',
        header: 'Ngày tạo',
        width: 150,
        cell: (survey) => formatDateTime(survey.created_at) || '—',
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        cell: (survey) => <StatusBadge status={survey.status} labels={SURVEY_STATUS_LABELS} />,
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Phiếu khảo sát"
        description="Khảo sát nhà cung cấp và sản phẩm phục vụ so sánh giá."
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(survey) => survey.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy phiếu khảo sát nào."
          storageKey="procurement.surveys"
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

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {statusOptions(SURVEY_STATUS_LABELS).map((option) => (
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
