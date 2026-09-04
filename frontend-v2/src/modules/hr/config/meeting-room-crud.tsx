import { CircleCheck, CircleX, Hash, MapPin, Users } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { RoomScheduleCard } from '../components/room-schedule-card'
import type { MeetingRoom } from '../types/room'

/**
 * DANH MỤC PHÒNG HỌP — khai bằng dữ liệu, không viết trang riêng (duoc-CR-279).
 *
 * ⚠️ Ô «Mã phòng» KHÔNG sửa được sau khi tạo (`readonlyOnEdit`): mã đó là cách
 * người ta gọi nhau ("họp ở P301") và nó nằm trong mọi phiếu đã đặt. Backend
 * chặn lớp thứ hai bằng cách bỏ `code` khỏi schema cập nhật.
 *
 * ⚠️ `company_id = 0` nghĩa là **phòng dùng chung mọi pháp nhân**, không phải
 * "chưa chọn" — đó là giá trị đúng cho toà nhà chung, và cũng là giá trị mặc
 * định. Hiện số 0 trần thì đọc ra như dữ liệu lỗi, nên cột và ô nhập đều nói
 * thành lời.
 */
export const MEETING_ROOM_CRUD_CONFIG: CrudConfig<MeetingRoom> = {
  entity: 'meeting_room',
  title: 'Phòng họp',
  description: 'Khai phòng, sức chứa và thiết bị — đây là nguồn của ô chọn phòng và của lịch đặt.',
  unitLabel: 'phòng họp',
  apiPath: '/api/meeting-rooms',
  storageKey: 'hr.meeting-rooms',
  listRoute: appRoutes.hr.meetingRooms,
  detailRoute: (id) => appRoutes.hr.meetingRoomDetail(id),
  //  Form 9 ô — dài quá cho một hộp thoại. Xem `CrudConfig.createRoute`.
  createRoute: appRoutes.hr.meetingRoomNew,
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên hoặc mã phòng…',
  quickFilters: [
    {
      key: 'is_active',
      label: 'Trạng thái',
      type: 'select',
      options: [
        { value: 'true', label: 'Đang dùng' },
        { value: 'false', label: 'Ngừng / Ẩn' },
      ],
    },
  ],
  getItemName: (r) => `${r.name} (${r.code})`,
  deleteWarning:
    'Phòng đang có phiếu đặt thì backend chặn xóa — xóa là để lại phiếu trỏ vào một phòng ' +
    'không còn tồn tại. Muốn dẹp phòng thì bỏ tick «Đang dùng».',
  chips: (r) => [
    { icon: Hash, text: r.code, tone: 'code' as const },
    ...(r.location ? [{ icon: MapPin, text: r.location, tone: 'muted' as const }] : []),
    ...(r.capacity
      ? [{ icon: Users, text: `${r.capacity} chỗ`, tone: 'ok' as const }]
      : []),
    {
      icon: r.is_active ? CircleCheck : CircleX,
      text: r.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
      tone: r.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'code',
      header: 'Mã phòng',
      width: 130,
      sortable: true,
      hideable: false,
      cell: (r) => <span className="font-semibold text-primary">{r.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên phòng',
      width: 240,
      sortable: true,
      hideable: false,
      cell: (r) => <span className="font-medium">{r.name}</span>,
    },
    { key: 'location', header: 'Vị trí', width: 180, cell: (r) => r.location || '—' },
    {
      key: 'capacity',
      header: 'Sức chứa',
      width: 110,
      align: 'right',
      sortable: true,
      //  `0` = CHƯA KHAI, không phải "không chứa được ai".
      cell: (r) =>
        r.capacity ? (
          <span className="tabular-nums">{r.capacity}</span>
        ) : (
          <span className="text-muted-foreground/50">—</span>
        ),
    },
    {
      key: 'equipment',
      header: 'Thiết bị',
      width: 260,
      wrap: true,
      minWidth: 180,
      cell: (r) => r.equipment || '—',
    },
    {
      key: 'company_id',
      header: 'Pháp nhân',
      width: 160,
      cell: (r) =>
        r.company_id ? `#${r.company_id}` : (
          <span className="text-muted-foreground">Dùng chung</span>
        ),
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (r) => (
        <Badge variant={r.is_active ? 'default' : 'secondary'}>
          {r.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  //  Mở một phòng ra phải thấy LỊCH của chính nó — xem `RoomScheduleCard`.
  //  Không có tab này thì đây mới là danh mục, chưa phải quản lý phòng.
  tabs: [
    {
      key: 'schedule',
      label: 'Lịch đặt của phòng',
      render: (room) => <RoomScheduleCard roomId={Number(room.id)} />,
    },
  ],
  formFields: [
    {
      name: 'code',
      label: 'Mã phòng',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: P301',
      hint: 'Mã ổn định, KHÔNG đổi được sau khi tạo — nó nằm trong mọi phiếu đã đặt.',
    },
    { name: 'name', label: 'Tên phòng', required: true, placeholder: 'VD: Phòng họp 301' },
    { name: 'location', label: 'Vị trí', placeholder: 'VD: Tầng 3, toà A' },
    {
      name: 'capacity',
      label: 'Sức chứa (người)',
      type: 'number',
      hint: 'Để 0 nếu chưa đo. Khai rồi thì phiếu ghi quá số này sẽ bị chặn.',
    },
    {
      name: 'equipment',
      label: 'Thiết bị sẵn có',
      fullWidth: true,
      placeholder: 'VD: máy chiếu, bảng trắng, micro',
      hint: 'Chỉ để người đặt chọn đúng phòng — không đặt riêng được từng thiết bị.',
    },
    {
      name: 'company_id',
      label: 'Pháp nhân riêng',
      type: 'select',
      source: { url: '/api/companies', valueKey: 'id', labelKey: 'name' },
      hint: 'Bỏ trống = phòng dùng chung cho MỌI pháp nhân. Chỉ chọn khi phòng thuộc riêng một pháp nhân.',
    },
    {
      name: 'sort_order',
      label: 'Thứ tự hiển thị',
      type: 'number',
      hint: 'Số nhỏ lên trước trên lịch và ô chọn. Phòng hay dùng để số nhỏ.',
    },
    { name: 'is_active', label: 'Đang dùng', type: 'switch', defaultValue: true },
    { name: 'note', label: 'Ghi chú', type: 'textarea', fullWidth: true },
  ],
}
