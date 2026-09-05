import { Building2, Hash, Wrench } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { AvailabilityBadge, SourceBadge } from '../components/status-pill'
import { VehicleTypeIcon } from '../components/vehicle-type-icon'
import { VEHICLE_STATUS_LABELS, type Vehicle } from '../types/vehicle'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'maintenance', label: 'Bảo trì' },
  { value: 'inactive', label: 'Ngưng sử dụng' },
]

export const VEHICLE_CRUD_CONFIG: CrudConfig<Vehicle> = {
  entity: 'vehicle',
  title: 'Danh mục Xe',
  unitLabel: 'xe',
  apiPath: '/api/vehicles',
  // Thêm/Sửa mở TRANG riêng (không popup): nút "Thêm" đi `/new`, bấm dòng đi `/:id`.
  createRoute: appRoutes.vehicleBooking.vehicleNew,
  storageKey: 'vehicle-booking.vehicles',
  listRoute: appRoutes.vehicleBooking.vehicles,
  detailRoute: (id) => appRoutes.vehicleBooking.vehicleDetail(id),
  searchParam: 'license_plate',
  searchPlaceholder: 'Tìm theo biển số…',
  getItemName: (v) => `${v.license_plate}${v.model ? ` — ${v.model}` : ''}`,
  deleteWarning: 'Xe này có thể đang được phân cho phiếu đặt xe.',
  chips: (v) => [
    ...(v.license_plate ? [{ icon: Hash, text: v.license_plate, tone: 'code' as const }] : []),
    v.is_external
      ? { icon: Building2, text: 'Thuê ngoài', tone: 'muted' as const }
      : { icon: Wrench, text: VEHICLE_STATUS_LABELS[v.status] ?? v.status, tone: 'ok' as const },
  ],
  columns: [
    {
      key: 'type',
      header: 'Loại xe',
      width: 160,
      sortable: true,
      cell: (v) => (
        <span className="inline-flex items-center gap-2">
          <VehicleTypeIcon type={v.type} />
          {v.type || '—'}
        </span>
      ),
    },
    {
      key: 'license_plate',
      header: 'Biển số',
      width: 140,
      hideable: false,
      sortable: true,
      // Chữ đen theo token nền (var(--foreground)), không còn xanh primary.
      cell: (v) => <span className="font-semibold text-foreground">{v.license_plate || '—'}</span>,
    },
    {
      key: 'model',
      header: 'Mẫu xe',
      width: 200,
      sortable: true,
      // Không in đậm text mẫu xe (theo yêu cầu).
      cell: (v) => v.model || '—',
    },
    {
      key: 'capacity',
      header: 'Tải (người/tấn)',
      width: 130,
      align: 'right',
      sortable: true,
      cell: (v) => <span className="tabular-nums">{v.capacity}</span>,
    },
    {
      key: 'is_external',
      header: 'Nguồn',
      width: 120,
      sortable: true,
      cell: (v) => <SourceBadge isExternal={v.is_external} />,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (v) => (
        <AvailabilityBadge status={v.status} label={VEHICLE_STATUS_LABELS[v.status] ?? v.status} />
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'license_plate', label: 'Biển số', type: 'text' },
      { name: 'type', label: 'Loại xe', type: 'text' },
      { name: 'status', label: 'Trạng thái', type: 'select', options: STATUS_OPTIONS },
      {
        name: 'is_external',
        label: 'Nguồn',
        type: 'select',
        options: [
          { value: 'false', label: 'Nội bộ' },
          { value: 'true', label: 'Thuê ngoài' },
        ],
      },
    ],
  },
  // Thêm/Sửa xe nay ở TRANG riêng (`VehicleForm`, có nút nguồn + nhà cung cấp + lịch sử).
  // `formFields` chỉ còn để khung generic không lỗi — thực tế không dùng nữa.
  formFields: [
    { name: 'license_plate', label: 'Biển số / Tên xe', type: 'text', required: true, placeholder: 'VD: 65C-172.76' },
    { name: 'model', label: 'Mẫu xe', type: 'text', placeholder: 'VD: Toyota Hilux' },
    { name: 'type', label: 'Loại xe', type: 'text', placeholder: 'VD: Xe con, Xe tải, Xe bán tải' },
    {
      name: 'capacity',
      label: 'Tải (người/tấn)',
      type: 'number',
      defaultValue: 4,
      hint: 'Số chỗ (chở người) hoặc tải trọng theo tấn (chở hàng).',
    },
    { name: 'status', label: 'Trạng thái', type: 'select', options: STATUS_OPTIONS, defaultValue: 'available' },
  ],
}
