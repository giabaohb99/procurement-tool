import { CalendarClock, CalendarRange, CircleCheck } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { WORK_SCHEDULE_LEVEL } from '@/shared/constants/statuses'
import { CrudRecordCard, type CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { formatDate } from '@/shared/utils/format-date'
import { WorkScheduleLevelField } from '../components/work-schedule-level-field'
import { WorkScheduleSelectField } from '../components/work-schedule-select-field'
import { WorkScheduleTargetField } from '../components/work-schedule-target-field'
import {
  SYSTEM_LEVEL_LABEL,
  WORK_SCHEDULE_LEVEL_CODE,
  type WorkScheduleAssignment,
} from '../types/work-schedule'

/** «Toàn hệ thống» cho cấp hệ thống (đối tượng `0` không có tên), còn lại lấy tên backend trả kèm. */
function targetLabel(row: WorkScheduleAssignment): string {
  if (row.target_level === WORK_SCHEDULE_LEVEL_CODE.SYSTEM) return SYSTEM_LEVEL_LABEL
  return row.target_name || `#${row.target_id}`
}

/**
 * GÁN LỊCH LÀM VIỆC — mẫu lịch nào áp cho ai, từ ngày nào.
 *
 * Hẹp thắng rộng (Nhân sự > Phòng ban > Pháp nhân > Toàn hệ thống). Cùng một đối
 * tượng không được có hai dòng chồng khoảng ngày — NGOẠI LỆ: tạo dòng mới khi đối
 * tượng đang có dòng «không thời hạn» bắt đầu trước đó thì backend tự đóng dòng cũ
 * vào ngày liền trước, và nếu dòng mới có «Đến ngày» thì lịch cũ tự nối lại không
 * thời hạn từ ngày sau đó (chốt 05/10/2026). Mọi chồng khác backend trả 400 kèm tên
 * dòng trùng, câu đó hiện ở toast chung của khung CRUD.
 *
 * Bốn ô đầu là ô TỰ VẼ vì cặp «cấp + đối tượng» phụ thuộc nhau: đổi cấp phải xóa
 * đối tượng cũ, và danh sách đối tượng đổi theo cấp.
 */
export const WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG: CrudConfig<WorkScheduleAssignment> = {
  entity: 'work_schedule',
  title: 'Gán lịch làm việc',
  description:
    'Chọn mẫu lịch áp cho toàn công ty, một pháp nhân, một phòng ban hoặc một nhân sự, kèm ngày hiệu lực.',
  unitLabel: 'dòng gán lịch',
  apiPath: '/api/work-schedule-assignments',
  storageKey: 'hr.work-schedule-assignments',
  listRoute: appRoutes.hr.workScheduleAssignments,
  openFormOnRowClick: true,
  //  Không có trang chi tiết → xóa ngay trong popup. Xóa dòng vừa gán thì backend tự mở lại
  //  lịch cũ mà dòng đó đã tự đóng (chốt 05/10/2026).
  deleteInForm: true,
  //  Gán/gỡ lịch đổi `assignment_count` của mẫu (cảnh báo «Mẫu đang gán n nơi»).
  alsoInvalidate: ['/api/work-schedules'],
  dialogMaxWidth: 'sm:max-w-xl',
  //  Lọc theo cấp ở backend (`target_level`); lọc theo mẫu cần danh sách động nên chưa có.
  quickFilters: [
    {
      key: 'target_level',
      label: 'Cấp áp dụng',
      type: 'select',
      options: WORK_SCHEDULE_LEVEL.map((o) => ({ value: o.value, label: o.label })),
    },
  ],
  getItemName: (row) => `${row.schedule_name} — ${targetLabel(row)}`,
  deleteWarning:
    'Nếu dòng này từng tự đóng lịch cũ của cùng đối tượng thì lịch cũ được mở lại; nếu không, đối tượng quay về lịch của cấp rộng hơn (hoặc mặc định T2–T7). Đơn nghỉ đã lưu không đổi.',
  //  Khổ hẹp: bảng 8 cột chỉ lộ 3 cột đầu, người xem không thấy mẫu lịch lẫn ngày hiệu lực.
  mobileCard: (row) => (
    <CrudRecordCard
      title={targetLabel(row)}
      subtitle={row.target_level_label}
      chips={[
        { icon: CalendarClock, text: row.schedule_name, tone: 'muted' },
        {
          icon: CalendarRange,
          text: `${formatDate(row.effective_from)} → ${row.effective_to ? formatDate(row.effective_to) : 'không thời hạn'}`,
          tone: 'muted',
        },
        ...(row.is_current ? [{ icon: CircleCheck, text: 'Đang hiệu lực', tone: 'ok' as const }] : []),
      ]}
    />
  ),
  columns: [
    {
      key: 'target_level',
      header: 'Cấp áp dụng',
      width: 140,
      hideable: false,
      cell: (row) => <Badge variant="outline">{row.target_level_label}</Badge>,
    },
    {
      key: 'target_name',
      header: 'Đối tượng',
      width: 240,
      hideable: false,
      cell: (row) => <span className="font-medium">{targetLabel(row)}</span>,
    },
    {
      key: 'schedule_name',
      header: 'Mẫu lịch',
      width: 240,
      cell: (row) => row.schedule_name,
    },
    {
      key: 'effective_from',
      header: 'Từ ngày',
      width: 120,
      cell: (row) => formatDate(row.effective_from),
    },
    {
      key: 'effective_to',
      header: 'Đến ngày',
      width: 130,
      cell: (row) =>
        row.effective_to ? (
          formatDate(row.effective_to)
        ) : (
          <span className="text-muted-foreground">Không thời hạn</span>
        ),
    },
    {
      key: 'is_current',
      header: 'Hiệu lực',
      width: 120,
      cell: (row) => (
        <Badge variant={row.is_current ? 'default' : 'secondary'}>
          {row.is_current ? 'Đang hiệu lực' : 'Không áp hôm nay'}
        </Badge>
      ),
    },
    {
      key: 'note',
      header: 'Ghi chú',
      width: 220,
      cell: (row) => row.note || <span className="text-muted-foreground">—</span>,
    },
  ],
  formFields: [
    {
      name: 'target_level',
      label: 'Cấp áp dụng',
      type: 'custom',
      defaultValue: 0,
      render: ({ control, name, disabled }) => (
        <WorkScheduleLevelField control={control} name={name} idName="target_id" disabled={disabled} />
      ),
    },
    //  Ô ẨN: chỉ để giữ tên đối tượng đã lưu cho ô «Đối tượng» hiện thay vì «#7».
    //  Không gửi lên backend (xem `buildPayload`).
    { name: 'target_name', label: 'Tên đối tượng', type: 'text', defaultValue: '', showWhen: () => false },
    {
      name: 'target_id',
      label: 'Đối tượng áp dụng',
      type: 'custom',
      defaultValue: 0,
      render: ({ control, name, disabled }) => (
        <WorkScheduleTargetField
          control={control}
          name={name}
          levelName="target_level"
          disabled={disabled}
        />
      ),
    },
    {
      name: 'schedule_id',
      label: 'Mẫu lịch',
      type: 'custom',
      defaultValue: 0,
      render: ({ control, name, disabled }) => (
        <WorkScheduleSelectField control={control} name={name} disabled={disabled} />
      ),
    },
    {
      name: 'effective_from',
      label: 'Hiệu lực từ ngày',
      type: 'date',
      required: true,
      hint:
        'Nếu đối tượng đang có lịch không thời hạn, lịch đó tự kết thúc trước ngày này; nếu lịch ' +
        'mới có «Đến ngày», lịch cũ tự nối lại sau ngày đó. Các trường hợp chồng ngày khác sẽ báo ' +
        'lỗi — khi đó đặt «Đến ngày» cho dòng cũ trước.',
    },
    {
      name: 'effective_to',
      label: 'Đến ngày',
      type: 'date',
      nullWhenEmpty: true,
      hint: 'Bỏ trống = không thời hạn.',
    },
    { name: 'note', label: 'Ghi chú', type: 'textarea', fullWidth: true },
  ],
  //  Ô chọn chung gửi SỐ dưới dạng chuỗi ("3"); ép về số cho chắc, backend khai int/IntEnum.
  buildPayload: ({ target_name: _savedName, ...payload }) => ({
    ...payload,
    target_level: Number(payload.target_level),
    target_id: Number(payload.target_id) || 0,
    schedule_id: Number(payload.schedule_id),
  }),
}
