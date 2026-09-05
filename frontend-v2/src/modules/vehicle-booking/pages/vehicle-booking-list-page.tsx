import { Copy, Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
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
import { CarBookingIcon, DeliveryBookingIcon } from '../components/booking-type-icons'
import { BookingStatusBadge } from '../components/status-pill'
import { useVehicleBookings } from '../hooks/use-vehicle-bookings'
import { BOOKING_STATUS_LABELS, REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'

const ALL = 'all'

function formatDateTime(value: string): string {
  if (!value) return ''
  // Chuỗi ISO không kèm múi giờ (vd "2026-09-01T08:00") — cắt hiển thị gọn.
  const [date, time] = value.split('T')
  if (!date) return value
  const [y, m, d] = date.split('-')
  const hm = (time ?? '').slice(0, 5)
  return `${d}/${m}/${y}${hm ? ` ${hm}` : ''}`
}

export function VehicleBookingListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canCreate = can('vehicle_booking', 'create')
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [requestType, setRequestType] = useUrlParamState('request_type', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  // Sắp xếp phía server theo cột (backend whitelist cột thật, xem apply_sort_from_request).
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue) p.search = debouncedValue
    if (status !== ALL) p.status = status
    if (requestType !== ALL) p.request_type = requestType
    if (sortBy) {
      p.sort_by = sortBy
      p.sort_dir = sortDir
    }
    return p
  }, [page, pageSize, debouncedValue, status, requestType, sortBy, sortDir])

  const { data, isLoading, isError } = useVehicleBookings(params)

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
        cell: (r) => <BookingStatusBadge status={r.status} label={r.status_label} />,
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
              // Ô hành động phải chặn nổi bọt, không thì bấm là mở luôn trang chi tiết.
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

  return (
    <PageContainer fill>
      <PageHeader
        title="Đặt xe nội bộ"
        description="Tạo và theo dõi yêu cầu đặt xe công tác / giao hàng của bạn."
        actions={
          can('vehicle_booking', 'create') ? (
            <Button onClick={() => navigate(appRoutes.vehicleBooking.new)}>
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
          onRowClick={(r) => navigate(appRoutes.vehicleBooking.detail(r.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có yêu cầu đặt xe nào."
          storageKey="vehicle-booking.list"
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={(by, dir) => {
            setSortBy(by)
            setSortDir(dir)
            setPage(1)
          }}
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
                  className="pl-9"
                  placeholder="Tìm theo mã, mục đích, điểm đi/đến…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>
              <Select value={requestType} onValueChange={setRequestType}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Loại yêu cầu" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả loại</SelectItem>
                  <SelectItem value={String(REQUEST_TYPE.car)}>Đặt xe công tác</SelectItem>
                  <SelectItem value={String(REQUEST_TYPE.delivery)}>Đặt xe giao hàng</SelectItem>
                </SelectContent>
              </Select>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-40">
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
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
