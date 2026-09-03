import { Building2, Hash, Wrench } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { VEHICLE_STATUS_LABELS, type Vehicle } from '../types/vehicle'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'maintenance', label: 'Bảo trì' },
]

export const VEHICLE_CRUD_CONFIG: CrudConfig<Vehicle> = {
  entity: 'vehicle',
  title: 'Danh mục Xe',
  unitLabel: 'xe',
  apiPath: '/api/vehicles',
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
      key: 'license_plate',
      header: 'Biển số',
      width: 140,
      hideable: false,
      defaultPinned: true,
      cell: (v) => <span className="font-semibold text-primary">{v.license_plate || '—'}</span>,
    },
    {
      key: 'model',
      header: 'Mẫu xe',
      width: 200,
      cell: (v) => <span className="font-medium">{v.model || '—'}</span>,
    },
    { key: 'type', header: 'Loại xe', width: 150, cell: (v) => v.type || '—' },
    {
      key: 'capacity',
      header: 'Tải (người/tấn)',
      width: 130,
      align: 'right',
      cell: (v) => <span className="tabular-nums">{v.capacity}</span>,
    },
    {
      key: 'is_external',
      header: 'Nguồn',
      width: 120,
      cell: (v) => (
        <Badge variant={v.is_external ? 'outline' : 'secondary'}>
          {v.is_external ? 'Thuê ngoài' : 'Nội bộ'}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 130,
      cell: (v) => (
        <Badge variant={v.status === 'available' ? 'default' : 'outline'}>
          {VEHICLE_STATUS_LABELS[v.status] ?? v.status}
        </Badge>
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
  formFields: [
    {
      name: 'is_external',
      label: 'Xe thuê ngoài',
      type: 'switch',
      defaultValue: false,
      fullWidth: true,
      hint: 'Bật nếu là xe thuê ngoài (nhập thêm đơn vị cho thuê bên dưới).',
    },
    { name: 'license_plate', label: 'Biển số xe', type: 'text', required: true, placeholder: 'VD: 65C-172.76' },
    { name: 'model', label: 'Mẫu xe', type: 'text', required: true, placeholder: 'VD: Toyota Hilux' },
    { name: 'type', label: 'Loại xe', type: 'text', placeholder: 'VD: Sedan, SUV, Bán tải' },
    {
      name: 'capacity',
      label: 'Tải (người/tấn)',
      type: 'number',
      defaultValue: 4,
      hint: 'Số chỗ (chở người) hoặc tải trọng theo tấn (chở hàng).',
    },
    { name: 'status', label: 'Trạng thái', type: 'select', options: STATUS_OPTIONS, defaultValue: 'available' },
    {
      name: 'external_company',
      label: 'Đơn vị cho thuê',
      type: 'text',
      fullWidth: true,
      placeholder: 'Chỉ điền khi là xe thuê ngoài.',
    },
  ],
}
