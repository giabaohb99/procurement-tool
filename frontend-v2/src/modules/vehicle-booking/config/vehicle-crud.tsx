import { Building2, Wrench } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { CrudRecordCard } from '@/shared/crud/crud-record-card'
import { CatalogExportButton } from '../components/catalog-export-button'
import { AvailabilityBadge, SourceBadge } from '../components/status-pill'
import { VehicleIdentityCell } from '../components/vehicle-identity-cell'
import { formatVehicleCapacity } from '../utils/format-vehicle-capacity'
import { VEHICLE_STATUS_LABELS, type Vehicle } from '../types/vehicle'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'maintenance', label: 'Bảo trì' },
  { value: 'inactive', label: 'Ngưng sử dụng' },
]

const SOURCE_OPTIONS = [
  { value: 'false', label: 'Nội bộ' },
  { value: 'true', label: 'Thuê ngoài' },
]

export const VEHICLE_CRUD_CONFIG: CrudConfig<Vehicle> = {
  entity: 'vehicle',
  title: 'Danh mục Xe',
  description: 'Đội xe dùng để điều phối phiếu đặt xe — gồm cả xe nội bộ lẫn xe thuê ngoài.',
  unitLabel: 'xe',
  apiPath: '/api/vehicles',
  // Thêm/Sửa mở TRANG riêng (không popup): nút "Thêm" đi `/new`, bấm dòng đi `/:id`.
  createRoute: appRoutes.vehicleBooking.vehicleNew,
  //  ⚠️ Đuôi `.v2` là CÓ CHỦ Ý (22/09/2026): bộ cột vừa đổi hẳn (gộp *Biển số* +
  //  *Mẫu xe*, thêm *Đơn vị cho thuê*). Ai đã từng đụng menu «Cột» thì
  //  `useTableLayout` đọc bản lưu trong `localStorage` và **bản lưu thắng** —
  //  cột mới nối vào cuối, cột cũ đã xóa nằm lại trong thứ tự. Đổi khóa là mọi
  //  người nhận đúng bố cục mặc định mới; khóa cũ nằm lại vô hại.
  storageKey: 'vehicle-booking.vehicles.v2',
  listRoute: appRoutes.vehicleBooking.vehicles,
  detailRoute: (id) => appRoutes.vehicleBooking.vehicleDetail(id),
  searchParam: 'license_plate',
  //  Ô tìm chỉ lọc theo biển số (`searchParam`) — câu gợi ý ngắn để còn đọc
  //  được ở khổ hẹp, nơi nó chia hàng với nút «Bộ lọc».
  searchPlaceholder: 'Tìm biển số…',
  //  Hai ô lọc nhanh đứng ngay trên bảng: đây là hai câu hỏi người điều phối
  //  hỏi mỗi ngày ("xe nào đang sẵn sàng", "xe nào là xe thuê"), bắt họ mở tờ
  //  «Bộ lọc» để hỏi là thêm hai lần bấm cho việc thường xuyên nhất.
  quickFilters: [
    { key: 'status', label: 'Trạng thái', type: 'select', options: STATUS_OPTIONS },
    { key: 'is_external', label: 'Nguồn', type: 'select', options: SOURCE_OPTIONS },
  ],
  getItemName: (v) => `${v.license_plate}${v.model ? ` — ${v.model}` : ''}`,
  deleteWarning: 'Xe này có thể đang được phân cho phiếu đặt xe.',
  renderToolbarExtra: () => (
    <CatalogExportButton apiPath="/api/vehicles" searchParam="license_plate" filename="quan-ly-xe.xlsx" />
  ),
  //  ⚠️ KHÔNG khai `chips`. Khóa đó chỉ có một chỗ đọc là `CrudDetailPage`, mà
  //  danh mục Xe **không dùng trang chi tiết generic** — nó có trang biểu mẫu
  //  riêng (`VehicleCatalogFormPage`). Khai vào là một bộ huy hiệu không màn
  //  nào vẽ, và người sau sửa nó xong đi tìm mãi không thấy đổi ở đâu.
  //
  //  ⚠️ Khổ hẹp: THẺ thay bảng. Bảng này sáu cột, trên máy 390px thì đọc biển
  //  số xong phải cuộn ngang mới biết xe đó còn chạy được hay không.
  //
  //  ⚠️ Thẻ chỉ nói cái BẤT THƯỜNG: huy hiệu trạng thái tắt đi khi xe *Sẵn sàng*
  //  (13/13 dòng hiện tại đều vậy — in ra là mười ba huy hiệu xanh giống hệt
  //  nhau, và thứ cần nhặt ra là chiếc đang *Bảo trì* thì chìm nghỉm). Cùng lối
  //  với thẻ Chức vụ. Sức chứa đẩy lên dòng phụ vì nó là con số người điều phối
  //  cần ngay khi chọn xe.
  mobileCard: (v) => (
    <CrudRecordCard
      title={v.license_plate || '—'}
      subtitle={
        <span className="block truncate">
          {[v.model || v.external_company, v.type, formatVehicleCapacity(v.type, v.capacity)]
            .filter((part) => part && part !== '—')
            .join(' · ') || '—'}
        </span>
      }
      chips={[
        ...(v.status === 'available'
          ? []
          : [
              {
                icon: Wrench,
                text: VEHICLE_STATUS_LABELS[v.status] ?? v.status,
                tone: 'muted' as const,
              },
            ]),
        ...(v.is_external ? [{ icon: Building2, text: 'Thuê ngoài', tone: 'muted' as const }] : []),
      ]}
    />
  ),
  columns: [
    {
      key: 'id',
      header: 'ID',
      width: 72,
      sortable: true,
      cell: (v) => <span className="tabular-nums text-muted-foreground">{v.id}</span>,
    },
    {
      //  ⚠️ MỘT cột nhận diện, không phải hai. Biển số + mẫu xe xếp chồng trong
      //  `VehicleIdentityCell` — lý do đầy đủ ghi ở đầu component đó.
      //
      //  Không khai `width`: bảng `table-fixed` + `w-full` chia phần dôi cho cột
      //  nào bỏ trống bề rộng, nên đây là cột nuốt chỗ thừa thay vì để bảng chừa
      //  một dải trắng bên phải.
      key: 'license_plate',
      header: 'Xe',
      minWidth: 220,
      hideable: false,
      sortable: true,
      cell: (v) => <VehicleIdentityCell vehicle={v} />,
    },
    {
      key: 'type',
      header: 'Loại xe',
      width: 140,
      sortable: true,
      //  Biểu tượng loại xe đã nằm ở ô nhận diện; ở đây chỉ cần chữ, và để
      //  chữ mờ vì nó là thuộc tính phụ, không phải thứ để nhận ra chiếc xe.
      cell: (v) => <span className="text-muted-foreground">{v.type || '—'}</span>,
    },
    {
      //  ⚠️ Đơn vị đi KÈM TỪNG Ô, không nhét vào tiêu đề: cùng một cột vừa chứa
      //  số chỗ ngồi vừa chứa số tấn. Xem `format-vehicle-capacity.ts`.
      key: 'capacity',
      header: 'Sức chứa',
      width: 120,
      align: 'right',
      sortable: true,
      cell: (v) => (
        <span className="tabular-nums">{formatVehicleCapacity(v.type, v.capacity)}</span>
      ),
    },
    {
      //  Mặc định ẩn: chỉ có nghĩa với xe thuê ngoài (3/13 dòng hiện tại), bày
      //  luôn thì cả cột là dấu gạch ngang. Ai theo dõi xe thuê thì bật lên ở
      //  menu «Cột», hoặc lọc *Nguồn = Thuê ngoài* rồi đọc ngay dòng phụ của ô
      //  nhận diện — xe thuê ngoài thường bỏ trống mẫu xe nên chỗ đó hiện tên
      //  đơn vị.
      key: 'external_company',
      header: 'Đơn vị cho thuê',
      width: 200,
      defaultHidden: true,
      cell: (v) => v.external_company || '—',
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
  //  ⚠️ Mọi `name` ở đây phải nằm trong danh sách lọc của
  //  `backend/app/modules/vehicle_booking/catalog_controller.py`
  //  (`["license_plate", "type", "status", "is_external"]`). Tên ngoài danh sách
  //  bị `apply_filters` **bỏ qua trong im lặng** — người dùng đặt điều kiện, bấm
  //  Áp dụng, và nhận lại nguyên danh sách cũ mà không có lỗi nào để lần. Vì thế
  //  KHÔNG khai *Mẫu xe* / *Đơn vị cho thuê* ở đây dù bảng có hai cột đó; muốn
  //  lọc được thì phải mở whitelist bên backend trước.
  filterConfig: {
    fields: [
      { name: 'license_plate', label: 'Biển số', type: 'text' },
      { name: 'type', label: 'Loại xe', type: 'text' },
      { name: 'status', label: 'Trạng thái', type: 'select', options: STATUS_OPTIONS },
      { name: 'is_external', label: 'Nguồn', type: 'select', options: SOURCE_OPTIONS },
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
