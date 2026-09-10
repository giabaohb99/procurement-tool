import { Copy, Download, Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { downloadFile } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { ConditionalFilter, FilterProvider, useFilterQuery } from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { CarBookingIcon, DeliveryBookingIcon } from '../components/booking-type-icons'
import { BookingStatusBadge } from '../components/status-pill'
import { VEHICLE_BOOKING_FILTER_FIELDS } from '../config/vehicle-booking-filter-fields'
import { useVehicleBookings } from '../hooks/use-vehicle-bookings'
import { BOOKING_STATUS_LABELS, REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: VEHICLE_BOOKING_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: [
    'company_id',
    'department_id',
    'status',
    'request_type',
    'created_at_from',
    'created_at_to',
    'sort_by',
    'sort_dir',
  ],
}

function formatDateTime(value: string): string {
  if (!value) return ''
  const [date, time] = value.split('T')
  if (!date) return value
  const [y, m, d] = date.split('-')
  const hm = (time ?? '').slice(0, 5)
  return `${d}/${m}/${y}${hm ? ` ${hm}` : ''}`
}

export function VehicleBookingListPage() {
  //  Bỏ các trường lọc THAM CHIẾU khi thiếu quyền đọc danh mục — backend gác
  //  `company/department/employee.read`, mở popup chọn mà không quyền là ăn 403.
  const { can } = usePermission()
  const config = useMemo(
    () => ({
      ...FILTER_CONFIG,
      fields: VEHICLE_BOOKING_FILTER_FIELDS.filter((f) => {
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
      <VehicleBookingListContent />
    </FilterProvider>
  )
}

function VehicleBookingListContent() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { can } = usePermission()
  const canCreate = can('vehicle_booking', 'create')
  const canReadCompany = can('company', 'read')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [requestType, setRequestType] = useUrlParamState('request_type', ALL)
  const [createdFrom, setCreatedFrom] = useUrlParamState('created_at_from', '')
  const [createdTo, setCreatedTo] = useUrlParamState('created_at_to', '')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { data: companies } = useCompanies({ page_size: 500, is_active: true }, { enabled: canReadCompany })
  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    companyId,
    departmentId,
    status,
    requestType,
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
  if (requestType !== ALL) params.request_type = requestType
  if (createdFrom) params.created_at_from = createdFrom
  if (createdTo) params.created_at_to = createdTo
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = useVehicleBookings(params)

  const activeCount = [
    companyId !== ALL,
    departmentId !== ALL,
    status !== ALL,
    requestType !== ALL,
    Boolean(createdFrom || createdTo),
  ].filter(Boolean).length

  const clearAllFilters = () => {
    setCompanyId(ALL)
    setDepartmentId(ALL)
    setStatus(ALL)
    setRequestType(ALL)
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

  const columns = useMemo<DataTableColumn<VehicleBooking>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        cell: (r) => <span className="font-medium tabular-nums">{r.code}</span>,
        width: 110,
        hideable: false,
        defaultPinned: true,
        sortable: true,
      },
      {
        key: 'request_type',
        header: 'Loại',
        sortable: true,
        cell: (r) => (
          <span className="inline-flex items-center gap-1.5">
            {r.request_type === REQUEST_TYPE.delivery ? (
              <DeliveryBookingIcon className="size-4 text-orange-600 dark:text-orange-400" />
            ) : (
              <CarBookingIcon className="size-4 text-sky-600 dark:text-sky-400" />
            )}
            {r.request_type_label}
          </span>
        ),
        width: 170,
      },
      {
        key: 'purpose',
        header: 'Mục đích',
        cell: (r) => r.purpose,
        wrap: true,
        minWidth: 180,
        sortable: true,
      },
      {
        key: 'route',
        header: 'Lộ trình',
        cell: (r) => {
          const stopNames = (r.stops ?? []).map((s) => s.location).filter(Boolean)
          const parts = [r.start_location, ...stopNames, r.end_location].filter(Boolean)
          return parts.length ? parts.join(' → ') : ''
        },
        wrap: true,
        minWidth: 200,
      },
      {
        key: 'start_time',
        header: 'Thời gian đi',
        cell: (r) => <span className="tabular-nums">{formatDateTime(r.start_time)}</span>,
        width: 140,
        sortable: true,
      },
      {
        key: 'requester',
        header: 'Người tạo',
        cell: (r) => r.requester,
        width: 150,
        sortable: true,
      },
      {
        key: 'assigned',
        header: 'Xe / Tài xế',
        cell: (r) => {
          const parts = [r.assigned_vehicle_label, r.assigned_driver_label].filter(Boolean)
          return parts.length ? parts.join(' · ') : '—'
        },
        wrap: true,
        minWidth: 160,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        cell: (r) => <BookingStatusBadge status={r.status} driverStatus={r.driver_status} />,
        width: 130,
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
                navigate(`${appRoutes.vehicleBooking.new}?from=${r.id}`)
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


      <Select value={requestType} onValueChange={setRequestType}>
        <SelectTrigger className="w-full md:w-40 text-xs h-9">
          <SelectValue placeholder="Loại yêu cầu" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả loại</SelectItem>
          <SelectItem value={String(REQUEST_TYPE.car)}>Đặt xe công tác</SelectItem>
          <SelectItem value={String(REQUEST_TYPE.delivery)}>Đặt xe giao hàng</SelectItem>
        </SelectContent>
      </Select>

      <Select value={status} onValueChange={setStatus}>
        <SelectTrigger className="w-full md:w-40 text-xs h-9">
          <SelectValue placeholder="Trạng thái" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
          {Object.entries(BOOKING_STATUS_LABELS).map(([value, label]) => (
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

  //  Xuất Excel theo ĐÚNG bộ lọc đang hiển thị (khớp tập backend trả về).
  const handleExport = async () => {
    const q = new URLSearchParams()
    if (debouncedValue) q.set('search', debouncedValue)
    if (companyId !== ALL) q.set('company_id', companyId)
    if (status !== ALL) q.set('status', status)
    if (requestType !== ALL) q.set('request_type', requestType)
    if (createdFrom) q.set('created_at_from', createdFrom)
    if (createdTo) q.set('created_at_to', createdTo)
    const qs = q.toString() ? `?${q.toString()}` : ''
    await downloadFile(`/api/vehicle-bookings/export/xlsx${qs}`, 'yeu-cau-dat-xe.xlsx')
  }

  return (
    <PageContainer fill>
      <PageHeader
        title="Đặt xe nội bộ"
        description="Tạo và theo dõi yêu cầu đặt xe công tác / giao hàng của bạn."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => void handleExport()}>
              <Download className="mr-1.5 size-4" />
              Xuất Excel
            </Button>
            {canCreate && (
              <Button onClick={() => navigate(appRoutes.vehicleBooking.new)}>
                <Plus className="size-4" />
                Tạo yêu cầu
              </Button>
            )}
          </div>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          onRowClick={(r) => navigate(appRoutes.vehicleBooking.detail(r.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có yêu cầu đặt xe nào."
          storageKey="vehicle-booking.list"
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
                  placeholder="Tìm theo mã, mục đích, điểm đi/đến…"
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
