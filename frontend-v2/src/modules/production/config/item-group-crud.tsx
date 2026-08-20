import { Calendar, CircleCheck, CircleX, Clock, Hash } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import type { ItemGroup } from '../types/item-group'

export const ITEM_GROUP_CRUD_CONFIG: CrudConfig<ItemGroup> = {
  entity: 'item_group',
  title: 'Phân loại VTBB/NL',
  unitLabel: 'phân loại',
  apiPath: '/api/item-groups',
  storageKey: 'production.item-groups',
  listRoute: appRoutes.production.itemGroups,
  detailRoute: (id) => appRoutes.production.itemGroupDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên phân loại…',
  getItemName: (ig) => ig.name + (ig.code ? ` (${ig.code})` : ''),
  deleteWarning: 'Dữ liệu sản phẩm và đơn hàng thuộc phân loại này có thể bị ảnh hưởng.',
  chips: (ig) => [
    ...(ig.code ? [{ icon: Hash, text: ig.code, tone: 'code' as const }] : []),
    ...(ig.std_days || ig.std_days_unavail
      ? [
          {
            icon: Clock,
            text: `Ngày QĐ: ${ig.std_days || '—'} (sẵn hàng) · ${ig.std_days_unavail || '—'} (không sẵn)`,
          },
        ]
      : []),
    ...(ig.apply_date ? [{ icon: Calendar, text: `Áp dụng từ ${ig.apply_date}` }] : []),
    {
      icon: ig.is_active ? CircleCheck : CircleX,
      text: ig.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
      tone: ig.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'code',
      header: 'Mã',
      width: 120,
      cell: (ig) => <span className="font-semibold text-primary">{ig.code || '—'}</span>,
    },
    {
      key: 'name',
      header: 'Phân loại',
      width: 240,
      hideable: false,
      cell: (ig) => <span className="font-medium">{ig.name}</span>,
    },
    {
      key: 'std_days',
      header: 'Ngày QĐ (sẵn hàng)',
      width: 170,
      cell: (ig) => (ig.std_days ? `${ig.std_days} ngày` : '—'),
    },
    {
      key: 'std_days_unavail',
      header: 'Ngày QĐ (không sẵn)',
      width: 170,
      cell: (ig) => (ig.std_days_unavail ? `${ig.std_days_unavail} ngày` : '—'),
    },
    {
      key: 'apply_date',
      header: 'Ngày áp dụng',
      width: 140,
      cell: (ig) => ig.apply_date || '—',
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      cell: (ig) => (
        <Badge variant={ig.is_active ? 'default' : 'secondary'}>
          {ig.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'code', label: 'Mã', type: 'text' },
      { name: 'name', label: 'Phân loại', type: 'text' },
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
      label: 'Mã phân loại',
      type: 'text',
      placeholder: 'VD: NTL, BB, NHAN…',
      hint: 'Mã viết tắt của phân loại. Có thể để trống.',
    },
    {
      name: 'name',
      label: 'Tên phân loại',
      type: 'text',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: Nhãn, Chai, Thùng, Can, Túi…',
      hint: 'Tên phân loại vật tư / bao bì / nguyên liệu. Không sửa sau khi tạo để tránh vỡ tham chiếu.',
    },
    {
      name: 'std_days',
      label: 'Số ngày QĐ khi NCC CÓ sẵn hàng',
      type: 'text',
      placeholder: 'VD: 15',
      hint: 'Số ngày chuẩn từ lúc đặt tới lúc nhận, dùng để tính hạn giao và cảnh báo đơn gấp.',
    },
    {
      name: 'std_days_unavail',
      label: 'Số ngày QĐ khi KHÔNG sẵn hàng',
      type: 'text',
      placeholder: 'VD: 30',
      hint: 'Áp dụng khi NCC phải sản xuất hoặc nhập khẩu thêm mới có hàng.',
    },
    {
      name: 'apply_date',
      label: 'Ngày áp dụng',
      type: 'date',
      hint: 'Mốc bắt đầu áp dụng số ngày quy định ở trên.',
    },
    {
      name: 'note',
      label: 'Ghi chú',
      type: 'textarea',
      fullWidth: true,
      placeholder: 'Ghi chú thêm về phân loại này…',
    },
    {
      name: 'is_active',
      label: 'Trạng thái hoạt động',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn phân loại; dữ liệu cũ vẫn giữ nguyên.',
    },
  ],
}
