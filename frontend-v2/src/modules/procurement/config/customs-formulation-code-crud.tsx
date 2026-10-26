// duoc-CR-684 — cấu hình CRUD danh mục MÃ DẠNG CHẾ PHẨM thuốc BVTV (EC, SC, WG… theo
// CropLife Technical Monograph n°2) để người dùng tra ý nghĩa mã trên tên hàng.
// Chỉ là danh mục tra cứu: không điều khiển gắn nhãn hay tìm kiếm. Entity dùng chung
// `customs_price`, đường API `/api/customs-formulation-codes`.
import { CircleCheck, CircleX } from 'lucide-react'

import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'

import type { CustomsFormulationCode } from '../types/customs-admin'

const ACTIVE_OPTIONS = [
  { value: 'true', label: 'Đang dùng' },
  { value: 'false', label: 'Ngừng dùng' },
]

export const CUSTOMS_FORMULATION_CODE_CRUD_CONFIG: CrudConfig<CustomsFormulationCode> = {
  entity: 'customs_price',
  title: 'Mã dạng chế phẩm',
  description:
    'Mã dạng chế phẩm thuốc BVTV trên tên hàng (EC, SC, WG…), theo CropLife Technical Monograph n°2. Số đứng trước mã: dạng rắn (WP, WG, SG, SP, GR) là % khối lượng, dạng lỏng (EC, SC, SL, EW…) thường là g/L. Danh mục chỉ để tra cứu.',
  unitLabel: 'mã dạng',
  apiPath: '/api/customs-formulation-codes',
  storageKey: 'procurement.customs-formulation-codes',
  searchParam: 'code',
  searchPlaceholder: 'Tìm mã…',
  quickFilters: [{ key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS }],
  getItemName: (row) => row.code,
  deleteWarning: 'Xóa mã thì chỉ mất dòng tra cứu này. Muốn tạm tắt thì chuyển sang «Ngừng dùng».',
  openFormOnRowClick: true,
  columns: [
    {
      key: 'code',
      header: 'Mã',
      width: 100,
      sortable: true,
      hideable: false,
      cell: (row) => <span className="font-medium">{row.code}</span>,
    },
    { key: 'name_en', header: 'Tên tiếng Anh', width: 240, wrap: true, cell: (row) => row.name_en },
    { key: 'name_vi', header: 'Tên tiếng Việt', width: 220, wrap: true, cell: (row) => row.name_vi },
    { key: 'description', header: 'Đặc điểm', width: 320, wrap: true, cell: (row) => row.description },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 120,
      sortable: true,
      cell: (row) => (
        <Badge variant={row.is_active ? 'default' : 'secondary'}>
          {row.is_active ? <CircleCheck className="size-3" /> : <CircleX className="size-3" />}
          {row.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'code', label: 'Mã', type: 'text' },
      { name: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    preserveParams: ['is_active'],
  },
  formFields: [
    { name: 'code', label: 'Mã', type: 'text', required: true, hint: 'Viết hoa, tối đa 20 ký tự, vd «EC».' },
    { name: 'name_en', label: 'Tên tiếng Anh', type: 'text', fullWidth: true },
    { name: 'name_vi', label: 'Tên tiếng Việt', type: 'text', fullWidth: true },
    { name: 'description', label: 'Đặc điểm', type: 'textarea', fullWidth: true },
    { name: 'is_active', label: 'Đang sử dụng', type: 'switch', defaultValue: true },
  ],
}
