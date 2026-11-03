import { CalendarOff, CircleCheck, CircleX } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { CrudRecordCard, type CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import type { LeaveBlockPeriod } from '../types/leave'
import { formatBlockRange } from '../utils/leave-block-conflicts'

/**
 * NGÀY CẤM NGHỈ (duoc-CR-715) — khoảng ngày công ty không muốn ai nghỉ (chốt sổ, kiểm kê, mùa cao điểm).
 *
 * Chỉ CẢNH BÁO lúc lập đơn; đơn đụng khoảng cấm bị chặn ở lượt duyệt cuối, trừ vai trò được miễn khai ở
 * "Cài đặt nhân sự › Nghỉ phép". Pháp nhân / phòng ban bỏ trống = áp cho tất cả.
 * Khóa quyền dùng chung `leave_type` — cùng "Thiết lập" nghỉ phép.
 */
const blockChips = (b: LeaveBlockPeriod) => [
  { icon: CalendarOff, text: formatBlockRange(b), tone: 'code' as const },
  {
    icon: b.is_active ? CircleCheck : CircleX,
    text: b.is_active ? 'Đang áp dụng' : 'Ngừng',
    tone: b.is_active ? ('ok' as const) : ('muted' as const),
  },
]

export const LEAVE_BLOCK_CRUD_CONFIG: CrudConfig<LeaveBlockPeriod> = {
  entity: 'leave_type',
  auditEntity: 'leave_block_period',
  title: 'Ngày cấm nghỉ',
  unitLabel: 'khoảng cấm nghỉ',
  apiPath: '/api/leave-block-periods',
  storageKey: 'hr.leave-blocks',
  listRoute: appRoutes.hr.leaveBlocks,
  detailRoute: (id) => appRoutes.hr.leaveBlockDetail(id),
  createRoute: appRoutes.hr.leaveBlockNew,
  quickFilters: [
    {
      key: 'is_active',
      label: 'Trạng thái',
      type: 'select',
      options: [
        { value: 'true', label: 'Đang áp dụng' },
        { value: 'false', label: 'Ngừng' },
      ],
    },
  ],
  getItemName: (b) => `ngày cấm nghỉ ${formatBlockRange(b)}`,
  deleteWarning: 'Xóa khoảng cấm thì đơn nghỉ rơi vào các ngày đó không còn bị cảnh báo hay chặn duyệt.',
  chips: blockChips,
  mobileCard: (b) => (
    <CrudRecordCard
      title={formatBlockRange(b)}
      subtitle={b.reason || 'Không ghi lý do'}
      chips={blockChips(b)}
    />
  ),
  columns: [
    {
      key: 'from_date',
      header: 'Khoảng ngày cấm',
      width: 220,
      sortable: true,
      hideable: false,
      cell: (b) => <span className="font-semibold text-primary">{formatBlockRange(b)}</span>,
    },
    {
      key: 'reason',
      header: 'Lý do',
      width: 300,
      cell: (b) =>
        b.reason ? b.reason : <span className="text-muted-foreground">Không ghi lý do</span>,
    },
    {
      key: 'company_id',
      header: 'Pháp nhân',
      width: 140,
      //  `0` = áp cho mọi pháp nhân, không phải dữ liệu lỗi — xem `holiday-crud`.
      cell: (b) =>
        b.company_id ? `#${b.company_id}` : <span className="text-muted-foreground">Mọi pháp nhân</span>,
    },
    {
      key: 'department_id',
      header: 'Phòng ban',
      width: 140,
      cell: (b) =>
        b.department_id ? `#${b.department_id}` : <span className="text-muted-foreground">Mọi phòng ban</span>,
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (b) => (
        <Badge variant={b.is_active ? 'default' : 'secondary'}>{b.is_active ? 'Đang áp dụng' : 'Ngừng'}</Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      {
        name: 'is_active',
        label: 'Trạng thái',
        type: 'select',
        options: [
          { value: 'true', label: 'Đang áp dụng' },
          { value: 'false', label: 'Ngừng' },
        ],
      },
    ],
  },
  formFields: [
    { name: 'from_date', label: 'Từ ngày', type: 'date', required: true },
    {
      name: 'to_date',
      label: 'Đến ngày',
      type: 'date',
      required: true,
      hint: 'Một khoảng dài tối đa 366 ngày. Cấm một ngày thì chọn cùng ngày với "Từ ngày".',
    },
    {
      name: 'reason',
      label: 'Lý do',
      type: 'text',
      placeholder: 'VD: Chốt sổ cuối năm, kiểm kê kho',
      hint: 'Tối đa 255 ký tự. Hiện trong khung cảnh báo trên đơn nghỉ và trong thông báo chặn duyệt.',
    },
    {
      name: 'company_id',
      label: 'Pháp nhân',
      type: 'select',
      source: { url: '/api/companies', valueKey: 'id', labelKey: 'name' },
      defaultValue: 0,
      placeholder: 'Mọi pháp nhân',
      hint: 'Bỏ trống = áp cho MỌI pháp nhân. Khớp theo pháp nhân của người nghỉ.',
    },
    {
      name: 'department_id',
      label: 'Phòng ban',
      type: 'select',
      source: { url: '/api/departments', valueKey: 'id', labelKey: 'name' },
      defaultValue: 0,
      placeholder: 'Mọi phòng ban',
      hint: 'Bỏ trống = áp cho MỌI phòng ban. Khớp theo phòng ban của người nghỉ.',
    },
    { name: 'is_active', label: 'Đang áp dụng', type: 'switch', defaultValue: true },
  ],
}
