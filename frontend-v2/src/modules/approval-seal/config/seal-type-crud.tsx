import { CircleCheck, CircleX } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import type { SealType } from '../types/seal-type'

export const SEAL_TYPE_CRUD_CONFIG: CrudConfig<SealType> = {
  entity: 'seal_type',
  title: 'Loại con dấu',
  unitLabel: 'loại con dấu',
  apiPath: '/api/seal-types',
  storageKey: 'approval-seal.seal-types',
  listRoute: appRoutes.approvalSeal.sealTypes,
  detailRoute: (id) => appRoutes.approvalSeal.sealTypeDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên loại con dấu…',
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
  getItemName: (t) => t.name,
  deleteWarning: 'Các phiếu yêu cầu đóng dấu đang dùng loại con dấu này có thể bị ảnh hưởng.',
  chips: (t) => [
    {
      icon: t.is_active ? CircleCheck : CircleX,
      text: t.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
      tone: t.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'name',
      header: 'Tên loại con dấu',
      width: 280,
      sortable: true,
      hideable: false,
      cell: (t) => <span className="font-medium">{t.name}</span>,
    },
    {
      key: 'description',
      header: 'Mô tả',
      minWidth: 240,
      wrap: true,
      cell: (t) => t.description || '—',
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 140,
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
      { name: 'name', label: 'Tên loại con dấu', type: 'text' },
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
      name: 'name',
      label: 'Tên loại con dấu',
      type: 'text',
      required: true,
      placeholder: 'VD: Dấu tròn công ty, Dấu chức danh',
      hint: 'Tên hiển thị trong ô chọn loại con dấu khi tạo phiếu.',
    },
    {
      name: 'description',
      label: 'Mô tả',
      type: 'textarea',
      fullWidth: true,
      placeholder: 'Mô tả phạm vi sử dụng của loại con dấu này.',
    },
    {
      name: 'is_active',
      label: 'Đang dùng',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn loại con dấu; dữ liệu cũ vẫn giữ nguyên.',
    },
  ],
}
