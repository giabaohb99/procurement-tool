import { Copy, Download, Plus, Search } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import { downloadFile } from '@/core/api/download-file'
import { httpClient } from '@/core/api/http-client'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
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
  preserveParams: ['company_id', 'department_id', 'status', 'request_date_from', 'request_date_to', 'sort_by', 'sort_dir'],
}

export function SurveyRequestListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <SurveyRequestListContent />
    </FilterProvider>
  )
}

function SurveyRequestListContent() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { can } = usePermission()
  const canExport = can('survey_request', 'export')
  const canCreate = can('survey_request', 'create')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [reqDateFrom, setReqDateFrom] = useUrlParamState('request_date_from', '')
  const [reqDateTo, setReqDateTo] = useUrlParamState('request_date_to', '')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })
  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    companyId,
    departmentId,
    status,
    reqDateFrom,
    reqDateTo,
    sortBy,
    sortDir,
  ])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.code = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (departmentId !== ALL) params.department_id = Number(departmentId)
  if (status !== ALL) params.status = status
  if (reqDateFrom) params.request_date_from = reqDateFrom
  if (reqDateTo) params.request_date_to = reqDateTo
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = useSurveyRequests(params)

  const handleExportExcel = async () => {
    await downloadFile('/api/survey-requests/export/xlsx', 'yeu-cau-bao-gia.xlsx')
  }

  const handleClone = useCallback(
    async (sr: SurveyRequest, e: React.MouseEvent) => {
      e.stopPropagation()
      try {
        const res = await httpClient.post<{ data: { id: number } }>(`/api/survey-requests/${sr.id}/clone`)
        toast.success('Đã nhân bản phiếu yêu cầu báo giá')
        const newId = res.data?.data?.id
        if (newId) navigate(appRoutes.procurement.surveyRequestDetail(newId))
      } catch {
        toast.error('Nhân bản phiếu thất bại')
      }
    },
    [navigate],
  )

  const activeCount = [
    companyId !== ALL,
    departmentId !== ALL,
    status !== ALL,
    Boolean(reqDateFrom || reqDateTo),
  ].filter(Boolean).length

  const clearAllFilters = () => {
    setCompanyId(ALL)
    setDepartmentId(ALL)
    setStatus(ALL)
    setReqDateFrom('')
    setReqDateTo('')
  }

  const handleSortChange = (newSortBy: string, newSortDir: 'asc' | 'desc') => {
    const next = new URLSearchParams(searchParams)
    //  Khóa cột rỗng = nhịp thứ ba của tiêu đề cột: thôi sắp xếp. Phải XÓA tham
    //  số chứ đừng ghi chuỗi rỗng, kẻo đường dẫn gửi cho nhau còn dính
    //  `?sort_by=&sort_dir=asc`, đọc như đang sắp xếp theo một cột không tên.
    if (newSortBy) {
      next.set('sort_by', newSortBy)
      next.set('sort_dir', newSortDir)
    } else {
      next.delete('sort_by')
      next.delete('sort_dir')
    }
    setSearchParams(next)
  }

  const columns = useMemo<DataTableColumn<SurveyRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        width: 160,
        sortable: true,
        hideable: false,
        cell: (sr) => <span className="truncate font-medium">{sr.code}</span>,
      },
      { key: 'purpose', header: 'Mục đích', width: 280, cell: (sr) => sr.purpose || '' },
      { key: 'requester', header: 'Người yêu cầu', width: 200, cell: (sr) => sr.requester || '' },
      { key: 'department', header: 'Bộ phận', width: 180, cell: (sr) => sr.department || '' },
      {
        key: 'request_date',
        header: 'Ngày tạo',
        width: 150,
        sortable: true,
        cell: (sr) => formatDateTime(sr.created_at) || '',
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        sortable: true,
        cell: (sr) => <StatusBadge status={sr.status} labels={SR_STATUS_LABELS} />,
      },
      {
        key: 'actions',
        header: '',
        width: 60,
        hideable: false,
        cell: (sr) =>
          canCreate ? (
            <Button
              variant="ghost"
              size="icon-sm"
              title="Nhân bản phiếu yêu cầu báo giá"
              onClick={(e) => handleClone(sr, e)}
            >
              <Copy className="size-4 text-muted-foreground" />
            </Button>
          ) : null,
      },
    ],
    [canCreate, handleClone],
  )

  const filterControls = (
    <>
      <Select value={companyId} onValueChange={setCompanyId}>
        <SelectTrigger className="w-full md:w-44 text-xs h-9">
          <SelectValue placeholder="Công ty" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả công ty</SelectItem>
          {(companies?.items ?? []).map((company: { id: number; name: string }) => (
            <SelectItem key={company.id} value={String(company.id)}>
              {company.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={departmentId} onValueChange={setDepartmentId}>
        <SelectTrigger className="w-full md:w-44 text-xs h-9">
          <SelectValue placeholder="Bộ phận yêu cầu" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả bộ phận</SelectItem>
          {(departments?.items ?? []).map((dept: { id: number; name: string }) => (
            <SelectItem key={dept.id} value={String(dept.id)}>
              {dept.name}
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
          {statusOptions(SR_STATUS_LABELS).map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <DateRangePicker
        from={reqDateFrom}
        to={reqDateTo}
        placeholder="Ngày tạo..."
        className="w-full md:w-auto"
        onChange={(f, t) => {
          setReqDateFrom(f)
          setReqDateTo(t)
        }}
      />
    </>
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Yêu cầu mua hàng"
        description="Phiếu yêu cầu mua hàng theo luồng gộp (mã YCBG) — khảo sát giá, chốt phương án rồi lên thẳng đơn mua hàng."
        actions={
          <div className="flex items-center gap-2">
            {canExport && (
              <Button variant="outline" onClick={handleExportExcel}>
                <Download className="mr-1.5 size-4" />
                Xuất Excel
              </Button>
            )}
            <PermissionGate entity="survey_request" action="create">
              <Button onClick={() => navigate(appRoutes.procurement.surveyRequestNew)}>
                <Plus className="mr-1.5 size-4" />
                Thêm mới
              </Button>
            </PermissionGate>
          </div>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(sr) => sr.id}
          onRowClick={(sr) => navigate(appRoutes.procurement.surveyRequestDetail(sr.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy yêu cầu báo giá nào."
          storageKey="procurement.survey-requests"
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
              <div className="relative min-w-56 flex-1 max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9 h-9 text-xs"
                  placeholder="Tìm mã phiếu, người yêu cầu, mã/tên sản phẩm…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <div className="hidden md:flex md:flex-wrap md:items-center md:gap-2">
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
