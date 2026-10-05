import { CalendarClock, CircleCheck, CircleX, Link2 } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { CrudRecordCard, type CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { WorkScheduleWeekEditor } from '../components/work-schedule-week-editor'
import type { WorkSchedule } from '../types/work-schedule'
import {
  buildDefaultWeek,
  fillWeek,
  formatWorkdays,
} from '../utils/work-schedule-week'
import { summarizeWeek } from '../utils/work-schedule-week-summary'

const scheduleChips = (row: WorkSchedule) => [
  {
    icon: CalendarClock,
    text: `${formatWorkdays(row.weekly_workdays ?? 0)} ngày công/tuần`,
    tone: 'muted' as const,
  },
  { icon: Link2, text: `Đang gán ${row.assignment_count ?? 0} nơi`, tone: 'muted' as const },
  {
    icon: row.is_active ? CircleCheck : CircleX,
    text: row.is_active ? 'Đang dùng' : 'Ngừng',
    tone: row.is_active ? ('ok' as const) : ('muted' as const),
  },
]

/**
 * MẪU LỊCH TUẦN — bảy ngày, mỗi ngày là Cả ngày / Buổi sáng / Buổi chiều / Nghỉ.
 *
 * Thêm mới mở TRANG RIÊNG (`createRoute`): bảng 7 ngày quá dài cho hộp thoại.
 * Sửa giờ của mẫu ĐANG GÁN đổi số ngày gợi ý của mọi đơn nhập sau (kể cả đơn lùi
 * ngày); đơn đã lưu không đổi vì `total_days` là cột — cảnh báo ở `renderExtra`.
 */
export const WORK_SCHEDULE_CRUD_CONFIG: CrudConfig<WorkSchedule> = {
  entity: 'work_schedule',
  title: 'Mẫu lịch tuần',
  description: 'Khai giờ làm từng ngày trong tuần, rồi gán cho công ty, phòng ban hoặc nhân sự.',
  unitLabel: 'mẫu lịch',
  apiPath: '/api/work-schedules',
  storageKey: 'hr.work-schedules',
  listRoute: appRoutes.hr.workSchedules,
  detailRoute: (id) => appRoutes.hr.workScheduleDetail(id),
  createRoute: appRoutes.hr.workScheduleNew,
  //  Đổi tên mẫu thì cột «Mẫu lịch» ở màn Gán lịch phải đổi theo.
  alsoInvalidate: ['/api/work-schedule-assignments'],
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên mẫu lịch…',
  detailMaxWidth: 'max-w-5xl',
  quickFilters: [
    {
      key: 'is_active',
      label: 'Trạng thái',
      type: 'select',
      options: [
        { value: 'true', label: 'Đang dùng' },
        { value: 'false', label: 'Ngừng' },
      ],
    },
  ],
  getItemName: (row) => row.name,
  deleteWarning: 'Mẫu đang được gán cho ai đó thì không xóa được — gỡ các dòng gán trước.',
  chips: scheduleChips,
  mobileCard: (row) => (
    <CrudRecordCard title={row.name} subtitle={summarizeWeek(row.days)} chips={scheduleChips(row)} />
  ),
  columns: [
    {
      key: 'name',
      header: 'Tên mẫu',
      width: 240,
      sortable: true,
      hideable: false,
      cell: (row) => <span className="font-medium">{row.name}</span>,
    },
    {
      key: 'days',
      header: 'Tóm tắt tuần',
      width: 340,
      cell: (row) => summarizeWeek(row.days),
    },
    {
      key: 'weekly_workdays',
      header: 'Công/tuần',
      width: 110,
      cell: (row) => formatWorkdays(row.weekly_workdays ?? 0),
    },
    {
      key: 'assignment_count',
      header: 'Đang gán',
      width: 110,
      cell: (row) =>
        row.assignment_count > 0 ? (
          `${row.assignment_count} nơi`
        ) : (
          <span className="text-muted-foreground">Chưa gán</span>
        ),
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 120,
      sortable: true,
      cell: (row) => (
        <Badge variant={row.is_active ? 'default' : 'secondary'}>
          {row.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  formFields: [
    {
      name: 'name',
      label: 'Tên mẫu lịch',
      type: 'text',
      required: true,
      placeholder: 'VD: Hành chính T2–T6 + sáng T7',
      section: 'Thông tin chung',
    },
    { name: 'note', label: 'Ghi chú', type: 'textarea', fullWidth: true, section: 'Thông tin chung' },
    {
      name: 'is_active',
      label: 'Đang dùng',
      type: 'switch',
      defaultValue: true,
      hint: 'Tắt = ẩn khỏi ô chọn khi gán mới; các dòng đã gán vẫn áp dụng.',
      section: 'Thông tin chung',
    },
    {
      name: 'days',
      label: 'Lịch 7 ngày',
      type: 'custom',
      section: 'Lịch 7 ngày trong tuần',
      defaultValue: buildDefaultWeek(),
      render: ({ control, name, disabled }) => (
        <WorkScheduleWeekEditor control={control} name={name} disabled={disabled} />
      ),
    },
  ],
  //  Luôn gửi đủ 7 ngày, giờ chuẩn "HH:MM" hoặc null — luật thật (giờ vào < giờ ra,
  //  trưa nằm trong khung…) ở backend, câu lỗi 422 hiện ở toast chung của khung CRUD.
  buildPayload: (payload) => ({ ...payload, days: fillWeek(payload.days) }),
  renderExtra: (row) =>
    row.assignment_count > 0 ? (
      <div
        role="note"
        className="rounded-md border border-dashed p-3 text-sm text-muted-foreground"
      >
        Mẫu đang gán <strong className="text-foreground">{row.assignment_count} nơi</strong> — sửa
        giờ sẽ đổi số ngày GỢI Ý của mọi đơn nhập sau, kể cả đơn lùi ngày. Đơn đã lưu không đổi.
        Muốn đổi lịch từ một ngày cụ thể thì tạo mẫu mới rồi gán kèm ngày hiệu lực.
      </div>
    ) : null,
}
