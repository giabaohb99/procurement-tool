import { Copy, Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { ConditionalFilter, FilterProvider, useFilterQuery } from '@/shared/conditional-filter'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { appRoutes } from '@/shared/constants/app-routes'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'
import { SealStatusBadge } from '../components/status-pill'
import { SEAL_REQUEST_FILTER_FIELDS } from '../config/seal-request-filter-fields'
import { useSealRequests } from '../hooks/use-seal-requests'
import { SEAL_STATUS_LABELS, type SealRequest } from '../types/seal-request'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: SEAL_REQUEST_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: [
    'company_id',
    'department_id',
    'status',
    'created_at_from',
    'created_at_to',
    'sort_by',
    'sort_dir',
  ],
}

export function SealRequestListPage() {
  //  Bỏ trường lọc tham chiếu khi thiếu quyền đọc danh mục (tránh 403 khi mở popup).
  const { can } = usePermission()
  const config = useMemo(
    () => ({
      ...FILTER_CONFIG,
      fields: SEAL_REQUEST_FILTER_FIELDS.filter((f) => {
        if (f.name === 'company_id') return can('company', 'read')
        if (f.name === 'department_id') return can('department', 'read')
        if (f.name === 'requester_id') return can('employee', 'read')
        return true
      }),
    }),
    [can],
  )
  return (
    <FilterProvider config={config}>
      <SealRequestListContent />
    </FilterProvider>
  )
}

function SealRequestListContent() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { can } = usePermission()
  const canCreate = can('seal_request', 'create')
  const canReadCompany = can('company', 'read')
  const canReadDept = can('department', 'read')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [createdFrom, setCreatedFrom] = useUrlParamState('created_at_from', '')
  const [createdTo, setCreatedTo] = useUrlParamState('created_at_to', '')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { data: companies } = useCompanies({ page_size: 500, is_active: true }, { enabled: canReadCompany })
  const { data: departments } = useDepartments({ page_size: 500, is_active: true }, { enabled: canReadDept })
  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    companyId,
    departmentId,
    status,
    createdFrom,
    createdTo,
    sortBy,
    sortDir,
  ])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.search = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (departmentId !== ALL) params.department_id = Number(departmentId)
  if (status !== ALL) params.status = status
  if (createdFrom) params.created_at_from = createdFrom
  if (createdTo) params.created_at_to = createdTo
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = useSealRequests(params)

  const activeCount = [
    companyId !== ALL,
    departmentId !== ALL,
    status !== ALL,
    Boolean(createdFrom || createdTo),
  ].filter(Boolean).length

  const clearAllFilters = () => {
    setCompanyId(ALL)
    setDepartmentId(ALL)
    setStatus(ALL)
    setCreatedFrom('')
    setCreatedTo('')
  }

  const handleSortChange = (newSortBy: string, newSortDir: 'asc' | 'desc') => {
    const next = new URLSearchParams(searchParams)
    if (newSortBy) {
      next.set('sort_by', newSortBy)
      next.set('sort_dir', newSortDir)
    } else {
      next.delete('sort_by')
      next.delete('sort_dir')
    }
    setSearchParams(next)
  }

  const columns = useMemo<DataTableColumn<SealRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        cell: (r) => <span className="font-medium tabular-nums">{r.code || '—'}</span>,
        width: 120,
        hideable: false,
        defaultPinned: true,
        sortable: true,
      },
      {
        key: 'purpose',
        header: 'Mục đích',
        cell: (r) => r.purpose,
        wrap: true,
        minWidth: 200,
        sortable: true,
      },
      {
        key: 'companies',
        header: 'Công ty',
        cell: (r) => (r.companies.length > 0 ? r.companies.map((c) => c.name).join(', ') : '—'),
        wrap: true,
        minWidth: 200,
      },
      {
        key: 'requester',
        header: 'Người tạo',
        cell: (r) => r.requester,
        width: 150,
        sortable: true,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        cell: (r) => <SealStatusBadge status={r.status} label={r.status_label} />,
        width: 130,
        sortable: true,
      },
      {
        key: 'created_at',
        header: 'Ngày tạo',
        cell: (r) => <span className="tabular-nums">{formatDateTime(r.created_at) || '—'}</span>,
        width: 150,
        sortable: true,
      },
      {
        key: 'actions',
        header: 'Thao tác',
        align: 'center',
        width: 90,
        hideable: false,
        cell: (r) =>
          canCreate ? (
            <Button
              variant="ghost"
              size="icon"
              aria-label={`Nhân bản ${r.code}`}
              title="Nhân bản"
              onClick={(e) => {
                e.stopPropagation()
                navigate(`${appRoutes.approvalSeal.new}?from=${r.id}`)
              }}
            >
              <Copy className="size-4" />
            </Button>
          ) : null,
      },
    ],
    [canCreate, navigate],
  )

  const filterControls = (
    <>
      {canReadCompany && (
        <Select value={companyId} onValueChange={setCompanyId}>
          <SelectTrigger className="w-full md:w-40 text-xs h-9">
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
      )}

      {canReadDept && (
        <Select value={departmentId} onValueChange={setDepartmentId}>
          <SelectTrigger className="w-full md:w-40 text-xs h-9">
            <SelectValue placeholder="Bộ phận" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Tất cả bộ phận</SelectItem>
            {(departments?.items ?? []).map((dept) => (
              <SelectItem key={dept.id} value={String(dept.id)}>
                {dept.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      <Select value={status} onValueChange={setStatus}>
        <SelectTrigger className="w-full md:w-40 text-xs h-9">
          <SelectValue placeholder="Trạng thái" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
          {Object.entries(SEAL_STATUS_LABELS).map(([value, label]) => (
            <SelectItem key={value} value={value}>
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <DateRangePicker
        from={createdFrom}
        to={createdTo}
        placeholder="Ngày tạo..."
        className="w-full md:w-auto"
        onChange={(f, t) => {
          setCreatedFrom(f)
          setCreatedTo(t)
        }}
      />
    </>
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Yêu cầu đóng dấu"
        description="Tạo và theo dõi yêu cầu trình ký, duyệt và đóng dấu chứng từ."
        actions={
          canCreate ? (
            <Button onClick={() => navigate(appRoutes.approvalSeal.new)}>
              <Plus className="size-4" />
              Tạo yêu cầu
            </Button>
          ) : undefined
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          onRowClick={(r) => navigate(appRoutes.approvalSeal.detail(r.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có yêu cầu đóng dấu nào."
          storageKey="approval-seal.list"
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={handleSortChange}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'yêu cầu',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9 h-9 text-xs"
                  placeholder="Tìm theo mã, mục đích…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <div className="hidden md:flex md:flex-wrap md:items-center md:gap-2">
                {filterControls}
                <ConditionalFilter />
              </div>

              <QuickFilterSheet activeCount={activeCount} onClearAll={clearAllFilters}>
                <div className="space-y-3">{filterControls}</div>
              </QuickFilterSheet>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
