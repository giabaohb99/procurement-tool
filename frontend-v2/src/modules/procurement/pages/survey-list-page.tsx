import { Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
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
  preserveParams: ['status', 'survey_type', 'product_code', 'sort_by', 'sort_dir'],
}

export function SurveyListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <SurveyListContent />
    </FilterProvider>
  )
}

function SurveyListContent() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [surveyType, setSurveyType] = useUrlParamState('survey_type', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([queryKey, debouncedValue, status, surveyType, sortBy, sortDir])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.code = debouncedValue
  if (status !== ALL) params.status = status
  if (surveyType !== ALL) params.survey_type = surveyType
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = useSurveys(params)

  const activeCount = [status !== ALL, surveyType !== ALL].filter(Boolean).length

  const clearAllFilters = () => {
    setStatus(ALL)
    setSurveyType(ALL)
  }

  const handleSortChange = (newSortBy: string, newSortDir: 'asc' | 'desc') => {
    const next = new URLSearchParams(searchParams)
    next.set('sort_by', newSortBy)
    next.set('sort_dir', newSortDir)
    setSearchParams(next)
  }

  const columns = useMemo<DataTableColumn<Survey>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        width: 160,
        sortable: true,
        hideable: false,
        defaultPinned: true,
        cell: (survey) => <span className="truncate font-medium">{survey.code}</span>,
      },
      {
        key: 'survey_type',
        header: 'Loại',
        width: 130,
        sortable: true,
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
        sortable: true,
        cell: (survey) => formatDateTime(survey.created_at) || '—',
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        sortable: true,
        cell: (survey) => <StatusBadge status={survey.status} labels={SURVEY_STATUS_LABELS} />,
      },
    ],
    [],
  )

  const filterControls = (
    <>
      <Select value={surveyType} onValueChange={setSurveyType}>
        <SelectTrigger className="w-full md:w-44 text-xs h-9">
          <SelectValue placeholder="Loại khảo sát" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả loại</SelectItem>
          {Object.entries(SURVEY_TYPE_LABELS).map(([k, v]) => (
            <SelectItem key={k} value={k}>
              {v}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={status} onValueChange={setStatus}>
        <SelectTrigger className="w-full md:w-40 text-xs h-9">
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
    </>
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Phiếu khảo sát"
        description="Khảo sát nhà cung cấp và sản phẩm phục vụ so sánh giá."
        actions={
          <PermissionGate entity="survey" action="create">
            <Button onClick={() => navigate(appRoutes.procurement.surveyNew)}>
              <Plus />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(survey) => survey.id}
          onRowClick={(survey) => navigate(appRoutes.procurement.surveyDetail(survey.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy phiếu khảo sát nào."
          storageKey="procurement.surveys"
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={handleSortChange}
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
              {/* 1. Ô Tìm Kiếm Nhanh ở ngoài cùng bên trái */}
              <div className="relative min-w-56 flex-1 max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9 h-9 text-xs"
                  placeholder="Tìm mã phiếu, mã SP, tên SP, mã NCC…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <div className="hidden md:flex md:items-center md:gap-2">
                {filterControls}
                <ConditionalFilter />
              </div>

              <QuickFilterSheet activeCount={activeCount} onClearAll={clearAllFilters}>
                <div className="space-y-3">
                  {filterControls}
                </div>
              </QuickFilterSheet>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
