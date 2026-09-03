import { CalendarOff, CircleCheck, CircleX, Coins, Hash } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { SeniorityTierCard } from '../components/seniority-tier-card'
import { GENDER, GENDER_LABELS, type LeaveType } from '../types/leave'

/**
 * LOẠI NGHỈ (V1-6) — cấu hình luật nghỉ bằng DỮ LIỆU, không bằng mã nguồn.
 *
 * Trước CR-259, 7 loại nghỉ là hằng số chuỗi trong `core/leave_codes.py`, nên
 * đổi hạn mức phép năm từ 12 lên 14 ngày là sửa code + deploy. Màn này là chỗ
 * đổi bằng một ô nhập.
 *
 * ⚠️ Ô «Mã loại nghỉ» KHÔNG sửa được sau khi tạo (`readonlyOnEdit`): mã đó đi
 * vào metadata của mọi giấy GNP đã phát hành. Đổi nó là những giấy ấy trỏ vào
 * một loại không còn tồn tại. Backend chặn lớp thứ hai.
 */

const GENDER_OPTIONS = [
  { value: GENDER.UNKNOWN, label: GENDER_LABELS[GENDER.UNKNOWN] },
  { value: GENDER.MALE, label: GENDER_LABELS[GENDER.MALE] },
  { value: GENDER.FEMALE, label: GENDER_LABELS[GENDER.FEMALE] },
]

export const LEAVE_TYPE_CRUD_CONFIG: CrudConfig<LeaveType> = {
  entity: 'leave_type',
  title: 'Loại nghỉ',
  unitLabel: 'loại nghỉ',
  apiPath: '/api/leave-types',
  storageKey: 'hr.leave-types',
  listRoute: appRoutes.hr.leaveTypes,
  detailRoute: (id) => appRoutes.hr.leaveTypeDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên hoặc mã loại nghỉ…',
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
  getItemName: (t) => `${t.name} (${t.code})`,
  deleteWarning:
    'Loại nghỉ đang có đơn hoặc đã cấp quỹ thì backend chặn xóa. Muốn ẩn khỏi ô chọn ' +
    'mà giữ dữ liệu cũ thì bỏ tick «Đang dùng».',
  chips: (t) => [
    { icon: Hash, text: t.code, tone: 'code' as const },
    ...(t.counts_balance
      ? [{ icon: Coins, text: `Quỹ ${t.annual_quota_days} ngày/năm`, tone: 'ok' as const }]
      : [{ icon: CalendarOff, text: 'Không trừ quỹ phép', tone: 'muted' as const }]),
    {
      icon: t.is_active ? CircleCheck : CircleX,
      text: t.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
      tone: t.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'code',
      header: 'Mã',
      width: 130,
      sortable: true,
      hideable: false,
      cell: (t) => <span className="font-semibold text-primary">{t.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên loại nghỉ',
      width: 240,
      sortable: true,
      hideable: false,
      cell: (t) => <span className="font-medium">{t.name}</span>,
    },
    {
      key: 'counts_balance',
      header: 'Trừ quỹ phép',
      width: 150,
      cell: (t) =>
        t.counts_balance ? (
          <Badge variant="default">{t.annual_quota_days} ngày/năm</Badge>
        ) : (
          <span className="text-muted-foreground">Không</span>
        ),
    },
    {
      key: 'is_paid',
      header: 'Hưởng lương',
      width: 130,
      cell: (t) => (t.is_paid ? 'Có' : 'Không'),
    },
    {
      key: 'max_days_per_request',
      header: 'Tối đa / lần',
      width: 130,
      //  `0` nghĩa là KHÔNG giới hạn, hiện số 0 thì đọc thành "không cho nghỉ".
      cell: (t) =>
        t.max_days_per_request ? `${t.max_days_per_request} ngày` : (
          <span className="text-muted-foreground">Không giới hạn</span>
        ),
    },
    {
      key: 'min_notice_days',
      header: 'Báo trước',
      width: 120,
      cell: (t) =>
        t.min_notice_days ? `${t.min_notice_days} ngày` : (
          <span className="text-muted-foreground">Không cần</span>
        ),
    },
    {
      key: 'gender',
      header: 'Áp dụng cho',
      width: 130,
      cell: (t) => GENDER_LABELS[t.gender] ?? GENDER_LABELS[GENDER.UNKNOWN],
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (t) => (
        <Badge variant={t.is_active ? 'default' : 'secondary'}>
          {t.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'code', label: 'Mã loại nghỉ', type: 'text' },
      { name: 'name', label: 'Tên loại nghỉ', type: 'text' },
      {
        name: 'counts_balance',
        label: 'Trừ quỹ phép',
        type: 'select',
        options: [
          { value: 'true', label: 'Có trừ quỹ' },
          { value: 'false', label: 'Không trừ quỹ' },
        ],
      },
      {
        name: 'is_active',
        label: 'Trạng thái',
        type: 'select',
        options: [
          { value: 'true', label: 'Đang dùng' },
          { value: 'false', label: 'Ngừng / Ẩn' },
        ],
      },
    ],
  },
  formFields: [
    {
      name: 'code',
      label: 'Mã loại nghỉ',
      type: 'text',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: annual, sick, unpaid',
      hint:
        'Mã ổn định, KHÔNG đổi được sau khi tạo — nó đi vào giấy nghỉ phép (GNP) ' +
        'đã phát hành. Dùng chữ thường không dấu.',
    },
    {
      name: 'name',
      label: 'Tên loại nghỉ',
      type: 'text',
      required: true,
      placeholder: 'VD: Phép năm, Nghỉ ốm đau',
    },
    {
      name: 'is_paid',
      label: 'Có hưởng lương',
      type: 'switch',
      defaultValue: true,
      hint: 'Khác với «Trừ quỹ phép» bên dưới: nghỉ cưới hỏi vẫn hưởng lương nhưng không ăn vào phép năm.',
    },
    {
      name: 'counts_balance',
      label: 'Trừ vào quỹ phép năm',
      type: 'switch',
      defaultValue: false,
      hint: 'Bật thì nộp đơn sẽ kiểm số ngày còn lại và chặn nếu vượt (không cho ứng phép).',
    },
    {
      name: 'annual_quota_days',
      label: 'Hạn mức mỗi năm (ngày)',
      type: 'number',
      defaultValue: 0,
      hint: 'Chỉ có nghĩa khi bật «Trừ vào quỹ phép năm». Bậc thâm niên cộng thêm ở tab bên dưới.',
    },
    {
      name: 'max_days_per_request',
      label: 'Tối đa mỗi lần nghỉ (ngày)',
      type: 'number',
      defaultValue: 0,
      hint: '0 = không giới hạn. Dùng cho loại có luật cứng như cưới hỏi 3 ngày.',
    },
    {
      name: 'min_notice_days',
      label: 'Phải nộp trước (ngày)',
      type: 'number',
      defaultValue: 0,
      hint: '0 = nộp lúc nào cũng được. Nghỉ ốm để 0 — không ai biết trước mai mình ốm.',
    },
    {
      name: 'gender',
      label: 'Áp dụng cho giới tính',
      type: 'select',
      options: GENDER_OPTIONS,
      defaultValue: GENDER.UNKNOWN,
      hint: 'Hồ sơ CHƯA khai giới tính vẫn nộp được — không chặn để khỏi khóa cả công ty.',
    },
    {
      name: 'exclude_holiday',
      label: 'Trừ thứ Bảy, Chủ nhật và ngày lễ',
      type: 'switch',
      defaultValue: true,
      hint: 'Tắt cho loại nghỉ dài liên tục (thai sản 6 tháng thì không bù cuối tuần).',
    },
    {
      name: 'require_attachment',
      label: 'Bắt buộc đính kèm',
      type: 'switch',
      defaultValue: false,
      hint: 'Giấy khám bệnh, giấy đăng ký kết hôn…',
    },
    {
      name: 'carry_over',
      label: 'Cho chuyển phép sang năm sau',
      type: 'switch',
      defaultValue: false,
      hint: 'Mặc định TẮT. Bật rồi tắt lại thì phải đi gỡ số đã chuyển, tắt rồi bật thì không mất gì.',
    },
    {
      name: 'carry_over_max_days',
      label: 'Chuyển tối đa (ngày)',
      type: 'number',
      defaultValue: 0,
    },
    {
      name: 'carry_over_expire_month',
      label: 'Phép chuyển hết hạn cuối tháng',
      type: 'number',
      defaultValue: 3,
      hint: 'Thông lệ: hết tháng 3 của năm sau.',
    },
    {
      name: 'sort_order',
      label: 'Thứ tự hiển thị',
      type: 'number',
      defaultValue: 0,
    },
    {
      name: 'is_active',
      label: 'Đang dùng',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn loại nghỉ; đơn cũ vẫn giữ nguyên.',
    },
    {
      name: 'note',
      label: 'Ghi chú',
      type: 'textarea',
      fullWidth: true,
    },
  ],
  tabs: [
    {
      key: 'seniority',
      label: 'Bậc thâm niên',
      render: (t) => <SeniorityTierCard leaveTypeId={t.id} />,
    },
  ],
}
