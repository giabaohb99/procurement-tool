import { Building2, IdCard, Phone } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { DRIVER_STATUS_LABELS, type Driver } from '../types/driver'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'on_leave', label: 'Nghỉ phép' },
]

export const DRIVER_CRUD_CONFIG: CrudConfig<Driver> = {
  entity: 'driver',
  title: 'Danh mục Tài xế',
  unitLabel: 'tài xế',
  apiPath: '/api/drivers',
  storageKey: 'vehicle-booking.drivers',
  listRoute: appRoutes.vehicleBooking.drivers,
  detailRoute: (id) => appRoutes.vehicleBooking.driverDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên tài xế…',
  getItemName: (d) => d.name,
  deleteWarning: 'Tài xế này có thể đang được phân cho phiếu đặt xe.',
  chips: (d) => [
    ...(d.phone ? [{ icon: Phone, text: d.phone, tone: 'muted' as const }] : []),
    ...(d.license_number ? [{ icon: IdCard, text: d.license_number, tone: 'code' as const }] : []),
    ...(d.is_external
      ? [{ icon: Building2, text: 'Thuê ngoài', tone: 'muted' as const }]
      : []),
  ],
  columns: [
    {
      key: 'name',
      header: 'Tên tài xế',
      width: 220,
      hideable: false,
      defaultPinned: true,
      cell: (d) => <span className="font-medium">{d.name}</span>,
    },
    { key: 'phone', header: 'Điện thoại', width: 150, cell: (d) => d.phone || '—' },
    {
      key: 'email',
      header: 'Email',
      width: 220,
      defaultHidden: true,
      cell: (d) => d.email || '—',
    },
    {
      key: 'license_number',
      header: 'Số GPLX',
      width: 130,
      cell: (d) => d.license_number || '—',
    },
    {
      key: 'is_external',
      header: 'Nguồn',
      width: 120,
      cell: (d) => (
        <Badge variant={d.is_external ? 'outline' : 'secondary'}>
          {d.is_external ? 'Thuê ngoài' : 'Nội bộ'}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 130,
      cell: (d) => (
        <Badge variant={d.status === 'available' ? 'default' : 'outline'}>
          {DRIVER_STATUS_LABELS[d.status] ?? d.status}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'name', label: 'Tên tài xế', type: 'text' },
      { name: 'phone', label: 'Điện thoại', type: 'text' },
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
      label: 'Tài xế thuê ngoài',
      type: 'switch',
      defaultValue: false,
      fullWidth: true,
      hint: 'Bật nếu là tài xế thuê ngoài (nhập thêm đơn vị cung cấp bên dưới).',
    },
    { name: 'name', label: 'Tên tài xế', type: 'text', required: true, placeholder: 'VD: Lê Minh Thông' },
    { name: 'phone', label: 'Số điện thoại', type: 'text', required: true, placeholder: 'VD: 0907507103' },
    { name: 'email', label: 'Email', type: 'text', placeholder: 'VD: taixe@degoholding.com' },
    {
      name: 'license_number',
      label: 'Số giấy phép lái xe (hạng)',
      type: 'text',
      required: true,
      placeholder: 'VD: B2, C, D',
    },
    {
      name: 'user_id',
      label: 'Tài khoản đăng nhập (nội bộ)',
      type: 'select',
      source: { url: '/api/users', valueKey: 'id', labelKey: 'email' },
      fullWidth: true,
      hint: 'Liên kết tài xế nội bộ với một tài khoản để sau này tự xem chuyến của mình.',
    },
    { name: 'status', label: 'Trạng thái', type: 'select', options: STATUS_OPTIONS, defaultValue: 'available' },
    {
      name: 'external_company',
      label: 'Đơn vị cung cấp',
      type: 'text',
      fullWidth: true,
      placeholder: 'Chỉ điền khi là tài xế thuê ngoài.',
    },
  ],
}
