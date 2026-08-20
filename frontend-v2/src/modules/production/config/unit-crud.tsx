import { CircleCheck, CircleX, Hash } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import type { Unit } from '../types/unit'

export const UNIT_CRUD_CONFIG: CrudConfig<Unit> = {
  entity: 'unit',
  title: 'Đơn vị tính',
  unitLabel: 'đơn vị tính',
  apiPath: '/api/units',
  storageKey: 'production.units',
  listRoute: appRoutes.production.units,
  detailRoute: (id) => appRoutes.production.unitDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên hoặc mã ĐVT…',
  getItemName: (u) => `${u.name} (${u.code})`,
  deleteWarning: 'Dữ liệu sản phẩm và chứng từ sử dụng đơn vị tính này có thể bị ảnh hưởng.',
  chips: (u) => [
    ...(u.code && u.code !== u.name ? [{ icon: Hash, text: u.code, tone: 'code' as const }] : []),
    {
      icon: u.is_active ? CircleCheck : CircleX,
      text: u.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
      tone: u.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'code',
      header: 'Mã ĐVT',
      width: 140,
      hideable: false,
      cell: (u) => <span className="font-semibold text-primary">{u.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên ĐVT',
      width: 280,
      hideable: false,
      cell: (u) => <span className="font-medium">{u.name}</span>,
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 140,
      cell: (u) => (
        <Badge variant={u.is_active ? 'default' : 'secondary'}>
          {u.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'code', label: 'Mã ĐVT', type: 'text' },
      { name: 'name', label: 'Tên ĐVT', type: 'text' },
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
      label: 'Mã ĐVT',
      type: 'text',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: CAI, THUNG, KG, MET',
      hint: 'Mã dùng khi import/export và khi tham chiếu ĐVT ở dòng hàng. Không thể sửa sau khi tạo.',
    },
    {
      name: 'name',
      label: 'Tên ĐVT',
      type: 'text',
      required: true,
      placeholder: 'VD: Cái, Thùng, Kg, Mét',
      hint: 'Tên hiển thị trong ô chọn ĐVT trên đơn mua hàng và phiếu nhập kho.',
    },
    {
      name: 'is_active',
      label: 'Trạng thái hoạt động',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn ĐVT; dữ liệu cũ vẫn giữ nguyên.',
    },
  ],
}
