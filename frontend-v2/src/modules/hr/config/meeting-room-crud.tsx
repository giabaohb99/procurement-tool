import { CircleCheck, CircleX, Hash, MapPin, Users } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { CrudRecordCard } from '@/shared/crud/crud-record-card'
import { Badge } from '@/shared/ui/badge'
import type { IdentityChip } from '@/shared/ui/record-identity-card'
import { RoomScheduleCard } from '../components/room-schedule-card'
import type { MeetingRoom } from '../types/room'

/**
 * Huy hiệu mô tả nhanh một phòng — dùng CHUNG cho thẻ danh tính ở trang chi tiết
 * và thẻ ở khổ điện thoại. Cùng một bản ghi thì hai màn phải nói cùng một câu.
 *
 * `quietWhenNormal` bỏ huy hiệu trạng thái khi phòng vẫn *Đang dùng* — xem ghi
 * chú ở `mobileCard`.
 */
function meetingRoomChips(r: MeetingRoom, quietWhenNormal = false): IdentityChip[] {
  const normal = r.is_active && quietWhenNormal
  return [
    { icon: Hash, text: r.code, tone: 'code' },
    ...(r.location ? [{ icon: MapPin, text: r.location, tone: 'muted' as const }] : []),
    //  `0` = CHƯA ĐO, không phải "không chứa được ai" — không có số thì không
    //  dựng huy hiệu, đừng in «0 chỗ».
    ...(r.capacity ? [{ icon: Users, text: `${r.capacity} chỗ`, tone: 'ok' as const }] : []),
    ...(normal
      ? []
      : [
          {
            icon: r.is_active ? CircleCheck : CircleX,
            text: r.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
            tone: r.is_active ? ('ok' as const) : ('muted' as const),
          },
        ]),
  ]
}

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
  //  ⚠️ **KHÔNG khai `detailMaxWidth`** — dùng `max-w-5xl` mặc định như mọi màn
  //  chi tiết CRUD khác. Bản cũ khai `max-w-none` với lý do "tab Lịch đặt cần cả
  //  bề ngang để xếp khung giờ", nhưng tab đó là một **`DataTable`** chứ không
  //  phải lưới khung giờ (có lẽ đúng ở bản đầu, rồi đổi mà ghi chú ở lại). Sáu
  //  cột của nó cộng lại **960px**, vừa trong 976px lòng trang.
  //
  //  Cái giá của `max-w-none` thì trả ở tab Thông tin — tab mở ra đầu tiên: trên
  //  màn 1440px ô «Tên phòng» dài 545px và ô «Thiết bị» dài 1090px để chứa hai
  //  chữ, mắt phải quét ngang gần cả màn hình mới đi hết một dòng. Bề ngang của ô
  //  nhập là lời hứa về lượng chữ phải gõ.
  listRoute: appRoutes.hr.meetingRooms,
  detailRoute: (id) => appRoutes.hr.meetingRoomDetail(id),
  //  Form 9 ô — dài quá cho một hộp thoại. Xem `CrudConfig.createRoute`.
  createRoute: appRoutes.hr.meetingRoomNew,
  searchParam: 'name',
  //  Ngắn để ĐỌC HẾT được ở khổ hẹp: ô tìm còn ~180px sau khi chia chỗ cho nút
  //  «Bộ lọc» và nút «Tải lại», bản cũ *«Tìm theo tên hoặc mã phòng…»* cần 226px
  //  nên cụt thành «Tìm theo». Một ô tìm không nói nổi mình tìm được những gì
  //  thì người dùng đoán, và thường đoán là chỉ tìm được mã.
  searchPlaceholder: 'Tìm tên, mã phòng…',
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
  //  Câu này người dùng đọc, không phải lập trình viên: đừng nhắc «backend»,
  //  «tham chiếu» hay tên bảng. Nói ĐIỀU GÌ XẢY RA và LÀM GÌ THAY THẾ.
  deleteWarning:
    'Phòng đang có phiếu đặt thì không xóa được. Xóa rồi thì các phiếu cũ mất tên phòng. ' +
    'Muốn dẹp phòng mà vẫn giữ lịch sử đặt thì bỏ tick «Đang dùng».',
  chips: meetingRoomChips,
  //  Khổ hẹp: thẻ thay bảng. Bảng khai 7 cột, bề rộng tự nhiên ~1210px — trên
  //  máy 390px chỉ thấy *Mã phòng* + *Tên phòng*, tức đúng hai cột KHÔNG dùng để
  //  chọn phòng; sức chứa, vị trí và thiết bị đều nằm sau một lượt cuộn ngang.
  //
  //  ⚠️ **Thẻ chỉ nói cái BẤT THƯỜNG, không nói lại cái mặc định.** Bản thử đầu
  //  in đủ *«Dùng chung mọi pháp nhân»* và huy hiệu *«Đang dùng»* trên mọi thẻ,
  //  và vì 21/21 phòng đều như vậy nên hai dòng đó chỉ là **21 dòng giống hệt
  //  nhau**, mỗi dòng ăn một hàng của thẻ (thẻ cao 4 hàng thay vì 2). Đúng lỗi
  //  đã phải vá ở `RoomDayList`.
  //
  //  Nay: pháp nhân chỉ hiện khi phòng bị GIỚI HẠN cho một pháp nhân — đó là ca
  //  đổi hành vi (phòng biến mất khỏi ô chọn của mọi người còn lại) và cũng là
  //  thứ hay bị khai nhầm. Trạng thái chỉ hiện khi *Ngừng / Ẩn*. Vắng mặt vì
  //  thế mang nghĩa nhất quán "bình thường", và thứ cần nhặt ra thì nổi lên.
  //
  //  ⚠️ Trang CHI TIẾT thì ngược lại, vẫn bày đủ (`chips`): ở đó chỉ có MỘT bản
  //  ghi nên không có gì để lặp, và người đang sửa phòng cần đọc được cả những
  //  giá trị mặc định.
  mobileCard: (r) => (
    <CrudRecordCard
      title={r.name}
      subtitle={
        <>
          {r.company_id > 0 && (
            <span className="block">Riêng pháp nhân #{r.company_id}</span>
          )}
          {/*  Thiết bị là chữ tự do, không giới hạn độ dài ở tầng nhập — cắt
               ĐÚNG MỘT dòng bằng «…» (luật chung của thẻ danh mục, khách chốt
               10/09/2026). Đầy đủ thì đọc ở trang chi tiết. */}
          {r.equipment && <span className="block truncate">{r.equipment}</span>}
        </>
      }
      chips={meetingRoomChips(r, true)}
    />
  ),
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
