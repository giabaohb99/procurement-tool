import { Building2, Wrench } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { CrudRecordCard } from '@/shared/crud/crud-record-card'
import { CatalogExportButton } from '../components/catalog-export-button'
import { DriverIdentityCell } from '../components/driver-identity-cell'
import { AvailabilityBadge, SourceBadge } from '../components/status-pill'
import { DRIVER_STATUS_LABELS, type Driver } from '../types/driver'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'on_leave', label: 'Nghỉ phép' },
  { value: 'inactive', label: 'Ngưng sử dụng' },
]

const SOURCE_OPTIONS = [
  { value: 'false', label: 'Nội bộ' },
  { value: 'true', label: 'Thuê ngoài' },
]

export const DRIVER_CRUD_CONFIG: CrudConfig<Driver> = {
  entity: 'driver',
  title: 'Danh mục Tài xế',
  description: 'Người cầm lái để điều phối phiếu đặt xe — gồm cả tài xế nội bộ lẫn thuê ngoài.',
  unitLabel: 'tài xế',
  apiPath: '/api/drivers',
  // Thêm/Sửa mở TRANG riêng (không popup): nút "Thêm" đi `/new`, bấm dòng đi `/:id`.
  createRoute: appRoutes.vehicleBooking.driverNew,
  //  ⚠️ Đuôi `.v2` là CÓ CHỦ Ý (22/09/2026): bộ cột vừa đổi hẳn (GPLX gộp vào ô
  //  nhận diện, thêm *Đơn vị cung cấp*). `useTableLayout` đọc bản lưu trong
  //  `localStorage` và **bản lưu thắng** — cột mới nối vào cuối, cột đã xóa nằm
  //  lại trong thứ tự. Đổi khóa là mọi người nhận đúng bố cục mặc định mới.
  storageKey: 'vehicle-booking.drivers.v2',
  listRoute: appRoutes.vehicleBooking.drivers,
  detailRoute: (id) => appRoutes.vehicleBooking.driverDetail(id),
  searchParam: 'name',
  //  Ô tìm chỉ lọc theo tên (`searchParam`) — câu gợi ý ngắn để còn đọc được ở
  //  khổ hẹp, nơi nó chia hàng với nút «Bộ lọc».
  searchPlaceholder: 'Tìm tên tài xế…',
  //  Hai câu hỏi thường ngày của người điều phối ("ai đang rảnh", "ai là tài xế
  //  thuê") đặt sẵn ngoài bảng, khỏi phải mở tờ «Bộ lọc».
  quickFilters: [
    { key: 'status', label: 'Trạng thái', type: 'select', options: STATUS_OPTIONS },
    { key: 'is_external', label: 'Nguồn', type: 'select', options: SOURCE_OPTIONS },
  ],
  getItemName: (d) => d.name,
  deleteWarning: 'Tài xế này có thể đang được phân cho phiếu đặt xe.',
  renderToolbarExtra: () => (
    <CatalogExportButton apiPath="/api/drivers" searchParam="name" filename="quan-ly-tai-xe.xlsx" />
  ),
  //  ⚠️ KHÔNG khai `chips` — xem lý do ở `vehicle-crud.tsx`: khóa đó chỉ
  //  `CrudDetailPage` đọc, mà danh mục Tài xế dùng trang biểu mẫu riêng.
  //
  //  ⚠️ Khổ hẹp: THẺ thay bảng — xem `CrudConfig.mobileCard`. Thẻ chỉ nói cái
  //  BẤT THƯỜNG: huy hiệu trạng thái tắt khi tài xế *Sẵn sàng* (15/15 dòng hiện
  //  tại đều vậy), giữ lại thì người đang tìm ai *Nghỉ phép* phải đọc từng thẻ.
  mobileCard: (d) => (
    <CrudRecordCard
      title={d.name || '—'}
      subtitle={
        <span className="block truncate">
          {(() => {
            //  Có chữ «GPLX» dẫn đường thì "B2" mới đọc ra là hạng bằng lái;
            //  đứng trơ sau số điện thoại, nó như một mẩu mã nào đó.
            const license = [d.license_class, d.license_number].filter(Boolean).join(' · ')
            return [d.phone, license && `GPLX ${license}`].filter(Boolean).join(' — ') || '—'
          })()}
        </span>
      }
      chips={[
        ...(d.status === 'available'
          ? []
          : [
              {
                icon: Wrench,
                text: DRIVER_STATUS_LABELS[d.status] ?? d.status,
                tone: 'muted' as const,
              },
            ]),
        ...(d.is_external ? [{ icon: Building2, text: 'Thuê ngoài', tone: 'muted' as const }] : []),
      ]}
    />
  ),
  columns: [
    {
      key: 'id',
      header: 'ID',
      width: 72,
      sortable: true,
      cell: (d) => <span className="tabular-nums text-muted-foreground">{d.id}</span>,
    },
    {
      //  ⚠️ MỘT cột nhận diện: tên + GPLX xếp chồng trong `DriverIdentityCell`
      //  (lý do đầy đủ ghi ở đầu component đó). Không khai `width` để nó nuốt
      //  phần dôi của bảng `table-fixed`, khỏi chừa dải trắng bên phải.
      key: 'name',
      header: 'Tài xế',
      minWidth: 220,
      hideable: false,
      sortable: true,
      cell: (d) => <DriverIdentityCell driver={d} />,
    },
    {
      key: 'phone',
      header: 'Điện thoại',
      width: 150,
      sortable: true,
      //  Số điện thoại đọc theo cụm — `tabular-nums` cho các chữ số thẳng cột
      //  giữa các hàng, mắt dò nhanh hơn hẳn.
      cell: (d) => <span className="tabular-nums">{d.phone || '—'}</span>,
    },
    {
      key: 'email',
      header: 'Email',
      width: 220,
      defaultHidden: true,
      sortable: true,
      cell: (d) => d.email || '—',
    },
    {
      //  Mặc định ẩn: chỉ có nghĩa với tài xế thuê ngoài (2/15 dòng hiện tại),
      //  bày luôn thì cả cột là dấu gạch ngang.
      key: 'external_company',
      header: 'Đơn vị cung cấp',
      width: 200,
      defaultHidden: true,
      cell: (d) => d.external_company || '—',
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
  //  ⚠️ Mọi `name` ở đây phải nằm trong danh sách lọc của
  //  `backend/app/modules/vehicle_booking/catalog_controller.py`
  //  (`["name", "phone", "status", "is_external"]`). Tên ngoài danh sách bị
  //  `apply_filters` **bỏ qua trong im lặng** — người dùng đặt điều kiện, bấm Áp
  //  dụng, và nhận lại nguyên danh sách cũ mà không có lỗi nào để lần. Vì thế
  //  KHÔNG khai *Số GPLX* / *Đơn vị cung cấp* dù bảng có bày chúng.
  filterConfig: {
    fields: [
      { name: 'name', label: 'Tên tài xế', type: 'text' },
      { name: 'phone', label: 'Điện thoại', type: 'text' },
      { name: 'status', label: 'Trạng thái', type: 'select', options: STATUS_OPTIONS },
      { name: 'is_external', label: 'Nguồn', type: 'select', options: SOURCE_OPTIONS },
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
