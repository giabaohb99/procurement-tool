import { CalendarDays, CircleCheck, CircleX, Repeat } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { formatDate } from '@/shared/utils/format-date'
import { Badge } from '@/shared/ui/badge'
import type { Holiday } from '../types/leave'

/**
 * LỊCH NGÀY LỄ — dùng để KHÔNG tính ngày lễ vào số ngày phép đã dùng.
 *
 * Hai chi tiết dễ hiểu nhầm, nên chúng nằm ở `hint` của chính hai ô đó:
 *
 * 1. **Pháp nhân bỏ trống = áp cho MỌI pháp nhân.** Đây là lựa chọn đúng cho
 *    gần hết các dòng; chỉ khai riêng khi nhà máy nghỉ bù khác văn phòng.
 * 2. **«Lặp hằng năm» chỉ dùng được cho ngày CỐ ĐỊNH theo dương lịch** (01/01,
 *    30/4, 02/9). Tết Âm và Giỗ Tổ trôi theo lịch âm nên mỗi năm phải nhập lại
 *    — tick lặp cho chúng là năm sau nghỉ sai ngày.
 */
export const HOLIDAY_CRUD_CONFIG: CrudConfig<Holiday> = {
  entity: 'holiday',
  title: 'Lịch ngày lễ',
  unitLabel: 'ngày lễ',
  apiPath: '/api/holidays',
  storageKey: 'hr.holidays',
  listRoute: appRoutes.hr.holidays,
  detailRoute: (id) => appRoutes.hr.holidayDetail(id),
  //  Đi cùng cặp với Loại nghỉ: hai màn nằm chung tab «Thiết lập», một màn mở
  //  hộp thoại còn màn kia nhảy trang thì thao tác đọc ra như hai phần mềm.
  createRoute: appRoutes.hr.holidayNew,
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên ngày lễ…',
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
  getItemName: (h) => `${h.name} (${formatDate(h.date)})`,
  deleteWarning: 'Xóa ngày lễ sẽ làm các đơn nghỉ phép tính lại số ngày kể từ lần nhập sau.',
  chips: (h) => [
    { icon: CalendarDays, text: formatDate(h.date), tone: 'code' as const },
    ...(h.is_recurring ? [{ icon: Repeat, text: 'Lặp hằng năm', tone: 'ok' as const }] : []),
    {
      icon: h.is_active ? CircleCheck : CircleX,
      text: h.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
      tone: h.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'date',
      header: 'Ngày',
      width: 140,
      sortable: true,
      hideable: false,
      cell: (h) => <span className="font-semibold text-primary">{formatDate(h.date)}</span>,
    },
    {
      key: 'name',
      header: 'Tên ngày lễ',
      width: 300,
      sortable: true,
      hideable: false,
      cell: (h) => <span className="font-medium">{h.name}</span>,
    },
    {
      key: 'is_recurring',
      header: 'Lặp hằng năm',
      width: 150,
      cell: (h) =>
        h.is_recurring ? (
          <Badge variant="default">Lặp theo ngày/tháng</Badge>
        ) : (
          <span className="text-muted-foreground">Chỉ năm này</span>
        ),
    },
    {
      key: 'company_id',
      header: 'Pháp nhân',
      width: 160,
      //  `0` KHÔNG phải "chưa chọn" — nó là "áp cho mọi pháp nhân", và đó là
      //  giá trị của gần hết các dòng. Hiện số 0 thì đọc thành dữ liệu lỗi.
      cell: (h) =>
        h.company_id ? `#${h.company_id}` : (
          <span className="text-muted-foreground">Mọi pháp nhân</span>
        ),
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (h) => (
        <Badge variant={h.is_active ? 'default' : 'secondary'}>
          {h.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'name', label: 'Tên ngày lễ', type: 'text' },
      {
        name: 'is_recurring',
        label: 'Lặp hằng năm',
        type: 'select',
        options: [
          { value: 'true', label: 'Có lặp' },
          { value: 'false', label: 'Chỉ năm này' },
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
      name: 'date',
      label: 'Ngày',
      type: 'date',
      required: true,
    },
    {
      name: 'name',
      label: 'Tên ngày lễ',
      type: 'text',
      required: true,
      placeholder: 'VD: Tết Dương lịch, Quốc khánh',
    },
    {
      name: 'is_recurring',
      label: 'Lặp lại hằng năm',
      type: 'switch',
      defaultValue: false,
      hint:
        'Chỉ tick cho ngày CỐ ĐỊNH theo dương lịch (01/01, 30/4, 02/9). Tết Âm lịch và ' +
        'Giỗ Tổ trôi theo lịch âm — tick lặp là năm sau nghỉ sai ngày.',
    },
    {
      name: 'company_id',
      label: 'Pháp nhân riêng',
      type: 'select',
      source: { url: '/api/companies', valueKey: 'id', labelKey: 'name' },
      defaultValue: 0,
      hint: 'Bỏ trống = áp cho MỌI pháp nhân. Chỉ chọn khi một pháp nhân nghỉ khác lịch chung.',
    },
    {
      name: 'is_active',
      label: 'Đang dùng',
      type: 'switch',
      defaultValue: true,
    },
  ],
}
