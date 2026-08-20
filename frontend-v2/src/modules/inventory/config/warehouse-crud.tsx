import { CircleCheck, CircleX, Hash } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import type { Warehouse } from '../types/warehouse'

export const WAREHOUSE_CRUD_CONFIG: CrudConfig<Warehouse> = {
  entity: 'warehouse',
  title: 'Danh mục Kho',
  unitLabel: 'kho',
  apiPath: '/api/warehouses',
  storageKey: 'inventory.warehouses',
  listRoute: appRoutes.inventory.warehouses,
  detailRoute: (id) => appRoutes.inventory.warehouseDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên kho…',
  getItemName: (w) => `${w.name} (${w.code})`,
  deleteWarning: 'Dữ liệu tồn kho và chứng từ liên quan đến kho này có thể bị ảnh hưởng.',
  chips: (w) => [
    ...(w.code ? [{ icon: Hash, text: w.code, tone: 'code' as const }] : []),
    {
      icon: w.is_active ? CircleCheck : CircleX,
      text: w.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
      tone: w.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'code',
      header: 'Mã kho',
      width: 140,
      hideable: false,
      cell: (w) => <span className="font-semibold text-primary">{w.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên kho',
      width: 280,
      hideable: false,
      cell: (w) => <span className="font-medium">{w.name}</span>,
    },
    {
      key: 'address',
      header: 'Địa chỉ',
      width: 400,
      cell: (w) => (
        <span className="truncate text-muted-foreground" title={w.address}>
          {w.address || '—'}
        </span>
      ),
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 140,
      cell: (w) => (
        <Badge variant={w.is_active ? 'default' : 'secondary'}>
          {w.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'code', label: 'Mã kho', type: 'text' },
      { name: 'name', label: 'Tên kho', type: 'text' },
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
      label: 'Mã kho',
      type: 'text',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: KHO-HN, KHO-HCM',
      hint: 'Mã dùng khi import/export và khi chọn kho nhập ở dòng hàng. Không thể sửa sau khi tạo.',
    },
    {
      name: 'name',
      label: 'Tên kho',
      type: 'text',
      required: true,
      placeholder: 'VD: Kho Tổng Hà Nội, Kho Nhà máy',
      hint: 'Tên đầy đủ, hiện trên đơn mua hàng và phiếu nhập kho.',
    },
    {
      name: 'address',
      label: 'Địa chỉ kho',
      type: 'textarea',
      fullWidth: true,
      placeholder: 'Địa chỉ thực tế nhận/giao hàng…',
      hint: 'Nơi giao hàng thực tế. Ghi thêm người nhận / số điện thoại nếu cần.',
    },
    {
      name: 'is_active',
      label: 'Trạng thái hoạt động',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn kho; dữ liệu cũ vẫn giữ nguyên.',
    },
  ],
}
