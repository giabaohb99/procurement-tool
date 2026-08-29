import { Copy, Download, Plus, Search } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { httpClient } from '@/core/api/http-client'
import { downloadFile } from '@/core/api/download-file'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
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
import { DateRangePicker } from '@/shared/ui/date-range-picker'
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
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { StatusBadge } from '../components/document-status-badge'
import { PURCHASE_REQUEST_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { usePurchaseRequests } from '../hooks/use-purchase-documents'
import {
  PR_STATUS_LABELS,
  statusOptions,
  type PurchaseRequest,
} from '../types/purchase-document'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: PURCHASE_REQUEST_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: [
    'company_id',
    'department_id',
    'status',
    'is_urgent',
    'need_date_from',
    'need_date_to',
    'request_date_from',
    'request_date_to',
    'sort_by',
    'sort_dir',
  ],
}

export function PurchaseRequestListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <PurchaseRequestListContent />
    </FilterProvider>
  )
}

function PurchaseRequestListContent() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { can } = usePermission()
  const canExport = can('purchase_request', 'export')
  const canCreate = can('purchase_request', 'create')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [isUrgent, setIsUrgent] = useUrlParamState('is_urgent', ALL)
  const [needDateFrom, setNeedDateFrom] = useUrlParamState('need_date_from', '')
  const [needDateTo, setNeedDateTo] = useUrlParamState('need_date_to', '')
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
    isUrgent,
    needDateFrom,
    needDateTo,
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
  if (isUrgent !== ALL) params.is_urgent = isUrgent === 'true'
  if (needDateFrom) params.need_date_from = needDateFrom
  if (needDateTo) params.need_date_to = needDateTo
  if (reqDateFrom) params.request_date_from = reqDateFrom
  if (reqDateTo) params.request_date_to = reqDateTo
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = usePurchaseRequests(params)

  const handleExportExcel = async () => {
    await downloadFile('/api/purchase-requests/export/xlsx', 'yeu-cau-mua-hang.xlsx')
  }

  const handleClone = useCallback(
    async (pr: PurchaseRequest, e: React.MouseEvent) => {
      e.stopPropagation()
      try {
        const res = await httpClient.post<{ data: { id: number } }>(`/api/purchase-requests/${pr.id}/clone`)
        toast.success('Đã nhân bản phiếu yêu cầu mua hàng')
        const newId = res.data?.data?.id
        if (newId) navigate(appRoutes.procurement.purchaseRequestDetail(newId))
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
    isUrgent === 'true',
    Boolean(needDateFrom || needDateTo),
    Boolean(reqDateFrom || reqDateTo),
  ].filter(Boolean).length

  const clearAllFilters = () => {
    setCompanyId(ALL)
    setDepartmentId(ALL)
    setStatus(ALL)
    setIsUrgent(ALL)
    setNeedDateFrom('')
    setNeedDateTo('')
    setReqDateFrom('')
    setReqDateTo('')
  }

  const handleSortChange = (newSortBy: string, newSortDir: 'asc' | 'desc') => {
    const next = new URLSearchParams(searchParams)
    next.set('sort_by', newSortBy)
    next.set('sort_dir', newSortDir)
    setSearchParams(next)
  }

  const columns = useMemo<DataTableColumn<PurchaseRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã PYC',
        width: 220,
        sortable: true,
        hideable: false,
        cell: (pr) => (
          <div className="flex items-center gap-1.5">
            <span className="truncate font-medium">{pr.code}</span>
            {pr.has_cancelled_line && (
              <Badge
                variant="secondary"
                className="shrink-0 border-0 bg-destructive/10 text-destructive"
                title="Phiếu có ít nhất một dòng đã hủy"
              >
                Có dòng hủy
              </Badge>
            )}
          </div>
        ),
      },
      {
        key: 'request_date',
        header: 'Ngày tạo',
        width: 150,
        sortable: true,
        cell: (pr) => formatDateTime(pr.created_at) || '',
      },
      { key: 'requester', header: 'Người yêu cầu', width: 200, cell: (pr) => pr.requester || '' },
      { key: 'department', header: 'Bộ phận', width: 180, cell: (pr) => pr.department || '' },
      {
        key: 'need_date',
        header: 'Cần hàng',
        width: 120,
        sortable: true,
        cell: (pr) => formatDate(pr.need_date) || '',
      },
      {
        key: 'total',
        header: 'Tổng tiền',
        width: 140,
        align: 'right',
        cell: (pr) => <span className="tabular-nums">{formatMoney(pr.total) || 0} đ</span>,
      },
      {
        key: 'is_urgent',
        header: 'Gấp',
        width: 80,
        sortable: true,
        cell: (pr) =>
          pr.is_urgent ? (
            <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
              Gấp
            </Badge>
          ) : null,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        sortable: true,
        cell: (pr) => <StatusBadge status={pr.status} labels={PR_STATUS_LABELS} />,
      },
      {
        key: 'actions',
        header: '',
        width: 60,
        hideable: false,
        cell: (pr) =>
          canCreate ? (
            <Button
              variant="ghost"
              size="icon-sm"
              title="Nhân bản phiếu"
              onClick={(e) => handleClone(pr, e)}
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
        <SelectTrigger className="w-full md:w-36 text-xs h-9">
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

      <Select value={departmentId} onValueChange={setDepartmentId}>
        <SelectTrigger className="w-full md:w-36 text-xs h-9">
          <SelectValue placeholder="Bộ phận yêu cầu" />
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

      <Select value={status} onValueChange={setStatus}>
        <SelectTrigger className="w-full md:w-36 text-xs h-9">
          <SelectValue placeholder="Trạng thái" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
          {statusOptions(PR_STATUS_LABELS).map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <DateRangePicker
        from={needDateFrom}
        to={needDateTo}
        placeholder="Ngày cần hàng..."
        className="w-full md:w-auto"
        onChange={(f, t) => {
          setNeedDateFrom(f)
          setNeedDateTo(t)
        }}
      />

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
        description="Phiếu yêu cầu mua hàng (PYC) của các bộ phận."
        actions={
          <div className="flex items-center gap-2">
            {canExport && (
              <Button variant="outline" onClick={handleExportExcel}>
                <Download className="mr-1.5 size-4" />
                Xuất Excel
              </Button>
            )}
            <PermissionGate entity="purchase_request" action="create">
              <Button onClick={() => navigate(appRoutes.procurement.purchaseRequestNew)}>
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
          getRowId={(pr) => pr.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy yêu cầu mua hàng nào."
          storageKey="procurement.purchase-requests"
          onRowClick={(pr) => navigate(appRoutes.procurement.purchaseRequestDetail(pr.id))}
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
              {/* 1. Ô Tìm Kiếm Nhanh luôn ở ngoài cùng bên trái */}
              <div className="relative min-w-56 flex-1 max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9 h-9 text-xs"
                  placeholder="Tìm mã PYC, người yêu cầu, mã/tên sản phẩm…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              {/* 2. Chip Gấp */}
              <Button
                variant={isUrgent === 'true' ? 'default' : 'outline'}
                size="sm"
                className="h-9 text-xs shrink-0"
                onClick={() => setIsUrgent(isUrgent === 'true' ? ALL : 'true')}
              >
                Gấp
              </Button>

              {/* Desktop Filter Controls */}
              <div className="hidden md:flex md:flex-wrap md:items-center md:gap-2">
                {filterControls}
                <ConditionalFilter />
              </div>

              {/* Mobile Filter Sheet (< 768px) */}
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
