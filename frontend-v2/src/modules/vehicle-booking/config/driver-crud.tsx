import { Building2, IdCard, Phone } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { AvailabilityBadge, SourceBadge } from '../components/status-pill'
import { DRIVER_STATUS_LABELS, type Driver } from '../types/driver'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'on_leave', label: 'Nghỉ phép' },
  { value: 'inactive', label: 'Ngưng sử dụng' },
]

export const DRIVER_CRUD_CONFIG: CrudConfig<Driver> = {
  entity: 'driver',
  title: 'Danh mục Tài xế',
  unitLabel: 'tài xế',
  apiPath: '/api/drivers',
  // Thêm/Sửa mở TRANG riêng (không popup): nút "Thêm" đi `/new`, bấm dòng đi `/:id`.
  createRoute: appRoutes.vehicleBooking.driverNew,
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
      sortable: true,
      cell: (d) => <span className="font-medium">{d.name}</span>,
    },
    { key: 'phone', header: 'Điện thoại', width: 150, sortable: true, cell: (d) => d.phone || '—' },
    {
      key: 'email',
      header: 'Email',
      width: 220,
      defaultHidden: true,
      sortable: true,
      cell: (d) => d.email || '—',
    },
    {
      key: 'license_number',
      header: 'Số GPLX',
      width: 150,
      sortable: true,
      cell: (d) => d.license_number || '—',
    },
    {
      key: 'license_class',
      header: 'Hạng',
      width: 90,
      sortable: true,
      cell: (d) => d.license_class || '—',
    },
    {
      key: 'is_external',
      header: 'Nguồn',
      width: 120,
      sortable: true,
      cell: (d) => <SourceBadge isExternal={d.is_external} />,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (d) => (
        <AvailabilityBadge status={d.status} label={DRIVER_STATUS_LABELS[d.status] ?? d.status} />
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
    { name: 'license_number', label: 'Số giấy phép lái xe', type: 'text', required: true, placeholder: 'VD: 790112345678' },
    { name: 'license_class', label: 'Hạng GPLX', type: 'text', placeholder: 'VD: B2, C, D' },
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
