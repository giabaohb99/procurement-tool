import { Boxes, CircleCheck, CircleX, Hash, ImageIcon, Tag } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { PurchaseHistoryTable } from '../components/purchase-history-table'
import type { Product } from '../types/product'

export const PRODUCT_CRUD_CONFIG: CrudConfig<Product> = {
  entity: 'product',
  title: 'Sản phẩm & Vật tư',
  unitLabel: 'sản phẩm',
  apiPath: '/api/products',
  storageKey: 'production.products',
  listRoute: appRoutes.production.products,
  detailRoute: (id) => appRoutes.production.productDetail(id),
  searchParam: 'search',
  searchPlaceholder: 'Tìm theo mã, tên, mã HH…',
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
  getItemName: (p) => `${p.name} (${p.code})`,
  deleteWarning:
    'Mã sản phẩm này có thể đã được liên kết với đơn mua hàng và khảo sát. Xóa sẽ làm mất liên kết tham chiếu.',
  chips: (p) => [
    ...(p.code ? [{ icon: Hash, text: p.code, tone: 'code' as const }] : []),
    ...(p.item_group ? [{ icon: Tag, text: `Phân loại: ${p.item_group}` }] : []),
    ...(p.unit ? [{ text: `ĐVT: ${p.unit}` }] : []),
    ...(p.hh_code ? [{ icon: Boxes, text: `Thành phẩm: ${p.hh_code}` }] : []),
    {
      icon: p.is_active ? CircleCheck : CircleX,
      text: p.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
      tone: p.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'thumbnail_url',
      header: 'Ảnh',
      width: 60,
      cell: (p) =>
        p.thumbnail_url ? (
          <img
            src={p.thumbnail_url}
            alt=""
            className="size-8 rounded object-cover shadow-xs"
          />
        ) : (
          <div className="flex size-8 items-center justify-center rounded bg-muted/60 text-muted-foreground/60">
            <ImageIcon className="size-4" />
          </div>
        ),
    },
    {
      key: 'code',
      header: 'Mã VTBB/NL',
      width: 140,
      sortable: true,
      hideable: false,
      cell: (p) => <span className="font-semibold text-primary">{p.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên VTBB/NL',
      width: 280,
      sortable: true,
      wrap: true,
      hideable: false,
      cell: (p) => <span className="font-medium">{p.name}</span>,
    },
    {
      key: 'item_group',
      header: 'Phân loại',
      width: 150,
      sortable: true,
      cell: (p) => p.item_group || '—',
    },
    {
      key: 'unit',
      header: 'ĐVT',
      width: 90,
      sortable: true,
      cell: (p) => p.unit || '—',
    },
    {
      key: 'hh_code',
      header: 'Mã HH',
      width: 120,
      sortable: true,
      cell: (p) => p.hh_code || '—',
    },
    {
      key: 'hh_name',
      header: 'Tên SP (HH)',
      width: 220,
      wrap: true,
      cell: (p) => (
        <span className="text-muted-foreground">
          {p.hh_name || '—'}
        </span>
      ),
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (p) => (
        <Badge variant={p.is_active ? 'default' : 'secondary'}>
          {p.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'code', label: 'Mã VTBB/NL', type: 'text' },
      { name: 'name', label: 'Tên VTBB/NL', type: 'text' },
      { name: 'item_group', label: 'Phân loại', type: 'text' },
      { name: 'unit', label: 'ĐVT', type: 'text' },
      { name: 'hh_code', label: 'Mã HH (sản phẩm)', type: 'text' },
      { name: 'hh_name', label: 'Tên SP (HH)', type: 'text' },
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
      label: 'Mã VTBB/NL',
      type: 'text',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: SP001, VT002…',
      hint: 'Mã VTBB/NL là định danh duy nhất (SKU). Không thể sửa sau khi tạo để tránh vỡ liên kết chứng từ.',
    },
    {
      name: 'name',
      label: 'Tên VTBB/NL',
      type: 'text',
      required: true,
      placeholder: 'VD: Nhãn chai 500ml…',
      hint: 'Tên hiển thị nội bộ của vật tư / bao bì / nguyên liệu.',
    },
    {
      name: 'invoice_name',
      label: 'Tên trên hóa đơn',
      type: 'text',
      placeholder: 'Tên xuất trên hóa đơn GTGT…',
      hint: 'Tên hàng hóa đầy đủ in trên hóa đơn tài chính.',
    },
    {
      name: 'legal_name',
      label: 'Tên pháp lý',
      type: 'text',
      placeholder: 'Tên pháp lý theo hồ sơ công bố…',
    },
    {
      name: 'item_group',
      label: 'Phân loại',
      type: 'select',
      source: { url: '/api/item-groups', valueKey: 'name', labelKey: 'name' },
      placeholder: 'Chọn phân loại',
    },
    {
      name: 'unit',
      label: 'Đơn vị tính',
      type: 'select',
      source: { url: '/api/units', valueKey: 'name', labelKey: 'name' },
      placeholder: 'Chọn ĐVT',
    },
    {
      name: 'hh_code',
      label: 'Mã HH (thành phẩm)',
      type: 'text',
      placeholder: 'VD: TP-01…',
      hint: 'Mã sản phẩm / hàng hóa thành phẩm tương ứng.',
    },
    {
      name: 'hh_name',
      label: 'Tên Sản phẩm (HH)',
      type: 'text',
      placeholder: 'Tên thành phẩm / hàng hóa tương ứng…',
    },
    {
      name: 'specs',
      label: 'Thông số kỹ thuật',
      type: 'textarea',
      fullWidth: true,
      placeholder: 'Kích thước, độ dày, chất liệu, xuất xứ…',
      hint: 'Tự động điền vào ô "Xuất xứ / TSKT / chất liệu" của dòng hàng khi chọn sản phẩm này trong Đơn mua hàng.',
    },
    {
      name: 'is_active',
      label: 'Trạng thái hoạt động',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn sản phẩm khi tạo đơn; dữ liệu cũ vẫn giữ nguyên.',
    },
  ],
  tabs: [
    {
      key: 'purchase-history',
      label: 'Lịch sử mua hàng',
      render: (product) => <PurchaseHistoryTable productCode={product.code} />,
    },
  ],
}
