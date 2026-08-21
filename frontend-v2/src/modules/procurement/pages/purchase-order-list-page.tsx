import { Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
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
import { DateRangePresetPicker } from '@/shared/ui/date-range-preset-picker'
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
import { formatMoney } from '@/shared/utils/format-money'
import { DocumentStatusBadge, StatusBadge } from '../components/document-status-badge'
import { PURCHASE_ORDER_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { usePurchaseOrders } from '../hooks/use-purchase-documents'
import {
  DOCUMENT_STATUSES,
  PO_STATUS_LABELS,
  statusOptions,
  type PurchaseOrder,
} from '../types/purchase-document'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: PURCHASE_ORDER_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: [
    'company_id',
    'supplier_code',
    'nspt_id',
    'document_status',
    'status',
    'invoice_no',
    'is_urgent',
    'order_date_from',
    'order_date_to',
    'sort_by',
    'sort_dir',
  ],
}

export function PurchaseOrderListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <PurchaseOrderListContent />
    </FilterProvider>
  )
}

function PurchaseOrderListContent() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [supplierCode, setSupplierCode] = useUrlParamState('supplier_code', ALL)
  const [nsptId, setNsptId] = useUrlParamState('nspt_id', ALL)
  const [docStatus, setDocStatus] = useUrlParamState('document_status', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [isUrgent, setIsUrgent] = useUrlParamState('is_urgent', ALL)
  const [orderDateFrom, setOrderDateFrom] = useUrlParamState('order_date_from', '')
  const [orderDateTo, setOrderDateTo] = useUrlParamState('order_date_to', '')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const navigate = useNavigate()

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: suppliers } = useSuppliers({ page_size: 500, is_active: true })
  const { data: employees } = useEmployees({ page_size: 500, is_active: true })
  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    companyId,
    supplierCode,
    nsptId,
    docStatus,
    status,
    isUrgent,
    orderDateFrom,
    orderDateTo,
    sortBy,
    sortDir,
  ])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.code = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (supplierCode !== ALL) params.supplier_code = supplierCode
  if (nsptId !== ALL) params.nspt_id = Number(nsptId)
  if (docStatus !== ALL) params.document_status = docStatus
  if (status !== ALL) params.status = status
  if (isUrgent === 'true') params.is_urgent = true
  if (orderDateFrom) params.order_date_from = orderDateFrom
  if (orderDateTo) params.order_date_to = orderDateTo
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = usePurchaseOrders(params)

  const activeCount = [
    companyId !== ALL,
    supplierCode !== ALL,
    nsptId !== ALL,
    docStatus !== ALL,
    status !== ALL,
    isUrgent === 'true',
    Boolean(orderDateFrom || orderDateTo),
  ].filter(Boolean).length

  const clearAllFilters = () => {
    setCompanyId(ALL)
    setSupplierCode(ALL)
    setNsptId(ALL)
    setDocStatus(ALL)
    setStatus(ALL)
    setIsUrgent(ALL)
    setOrderDateFrom('')
    setOrderDateTo('')
  }

  const handleSortChange = (newSortBy: string, newSortDir: 'asc' | 'desc') => {
    const next = new URLSearchParams(searchParams)
    next.set('sort_by', newSortBy)
    next.set('sort_dir', newSortDir)
    setSearchParams(next)
  }

  const columns = useMemo<DataTableColumn<PurchaseOrder>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã ĐMH',
        width: 160,
        sortable: true,
        hideable: false,
        defaultPinned: true,
        cell: (po) => <span className="truncate font-medium">{po.code}</span>,
      },
      {
        key: 'misa_code',
        header: 'Mã MISA',
        width: 130,
        sortable: true,
        defaultHidden: true,
        cell: (po) => po.misa_code || '—',
      },
      {
        key: 'order_date',
        header: 'Ngày đặt',
        width: 150,
        sortable: true,
        cell: (po) => formatDateTime(po.created_at) || '—',
      },
      {
        key: 'supplier',
        header: 'Nhà cung cấp',
        width: 240,
        cell: (po) => (
          <span className="truncate" title={po.supplier_name}>
            {po.supplier_name || po.supplier_code || '—'}
          </span>
        ),
      },
      { key: 'pr_code', header: 'Mã PYC', width: 140, cell: (po) => po.pr_code || '—' },
      { key: 'nspt', header: 'NSPT', width: 170, defaultHidden: true, cell: (po) => po.nspt || '—' },
      {
        key: 'amount',
        header: 'Tiền hàng',
        width: 150,
        align: 'right',
        cell: (po) => <span className="tabular-nums">{formatMoney(po.amount) || 0} đ</span>,
      },
      {
        key: 'is_urgent',
        header: 'Gấp',
        width: 80,
        sortable: true,
        cell: (po) =>
          po.is_urgent ? (
            <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
              Gấp
            </Badge>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        key: 'document_status',
        header: 'Hồ sơ',
        width: 130,
        cell: (po) => <DocumentStatusBadge status={po.document_status} />,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        sortable: true,
        cell: (po) => <StatusBadge status={po.status} labels={PO_STATUS_LABELS} />,
      },
    ],
    [],
  )

  const filterControls = (
    <>
      <Select value={companyId} onValueChange={setCompanyId}>
        <SelectTrigger className="w-full md:w-44 text-xs h-9">
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

      <Select value={supplierCode} onValueChange={setSupplierCode}>
        <SelectTrigger className="w-full md:w-48 text-xs h-9">
          <SelectValue placeholder="Nhà cung cấp" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả nhà cung cấp</SelectItem>
          {(suppliers?.items ?? []).map((sup) => (
            <SelectItem key={sup.code} value={sup.code}>
              {sup.name} ({sup.code})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={nsptId} onValueChange={setNsptId}>
        <SelectTrigger className="w-full md:w-40 text-xs h-9">
          <SelectValue placeholder="NSPT" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả NSPT</SelectItem>
          {(employees?.items ?? []).map((emp) => (
            <SelectItem key={emp.id} value={String(emp.id)}>
              {emp.full_name} ({emp.code})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={docStatus} onValueChange={setDocStatus}>
        <SelectTrigger className="w-full md:w-40 text-xs h-9">
          <SelectValue placeholder="Hồ sơ" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả hồ sơ</SelectItem>
          {DOCUMENT_STATUSES.map((val) => (
            <SelectItem key={val} value={val}>
              {val}
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
          {statusOptions(PO_STATUS_LABELS).map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <DateRangePresetPicker
        from={orderDateFrom}
        to={orderDateTo}
        placeholder="Ngày đặt..."
        className="w-full md:w-auto"
        onChange={(f, t) => {
          setOrderDateFrom(f)
          setOrderDateTo(t)
        }}
      />
    </>
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Đơn mua hàng"
        description="Đơn mua hàng (PO) gửi nhà cung cấp."
        actions={
          <PermissionGate entity="purchase_order" action="create">
            <Button onClick={() => navigate(appRoutes.procurement.purchaseOrderNew)}>
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
          getRowId={(po) => po.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy đơn mua hàng nào."
          storageKey="procurement.purchase-orders"
          onRowClick={(po) => navigate(appRoutes.procurement.purchaseOrderDetail(po.id))}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={handleSortChange}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'đơn',
          }}
          toolbar={
            <>
              {/* 1. Ô Tìm Kiếm Nhanh luôn ở ngoài cùng bên trái */}
              <div className="relative min-w-56 flex-1 max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9 h-9 text-xs"
                  placeholder="Tìm mã ĐMH, MISA, PYC, NCC, mã/tên sản phẩm…"
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
              <div className="hidden md:flex md:items-center md:gap-2">
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
