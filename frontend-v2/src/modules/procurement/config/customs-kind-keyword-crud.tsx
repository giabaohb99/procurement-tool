// bao-CR-494 — cấu hình CRUD danh mục TỪ KHÓA nhận diện Thành phẩm / Nguyên liệu.
//
// Entity backend dùng chung `customs_price` (bảng này là cấu hình của chính màn tra cứu, không
// có màn nghiệp vụ riêng — luật «một khóa = một màn hình»), đường API
// `/api/customs-kind-keywords`. Luật gắn nhãn: tên hàng chứa từ khóa loại NGUYÊN LIỆU → Nguyên
// liệu; từ khóa loại THÀNH PHẨM là ngoại lệ thắng ngược; không khớp gì → Thành phẩm. Từ khóa
// ngắn (≤ 4 ký tự) khớp nguyên từ, từ dài khớp chuỗi con — xem `customs/ingredient.py`.
import { CircleCheck, CircleX, Tag } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'

import { CustomsRetagButton } from '../components/customs-retag-button'
import {
  formatProductKindLabel,
  PRODUCT_KIND,
  PRODUCT_KIND_OPTIONS,
  type CustomsKindKeyword,
} from '../types/customs-admin'

const KIND_FILTER_OPTIONS = PRODUCT_KIND_OPTIONS.map((item) => ({
  value: String(item.value),
  label: item.label,
}))

const ACTIVE_OPTIONS = [
  { value: 'true', label: 'Đang dùng' },
  { value: 'false', label: 'Ngừng dùng' },
]

export const CUSTOMS_KIND_KEYWORD_CRUD_CONFIG: CrudConfig<CustomsKindKeyword> = {
  entity: 'customs_price',
  title: 'Từ khóa Thành phẩm / Nguyên liệu',
  description:
    'Bộ từ khóa để màn Tra cứu thị trường tự gắn nhãn từng dòng hàng. Tên hàng chứa từ khóa loại «Nguyên liệu» thì là nguyên liệu kỹ thuật, còn lại là thành phẩm. Sửa xong bấm «Gắn lại nhãn».',
  unitLabel: 'từ khóa',
  apiPath: '/api/customs-kind-keywords',
  storageKey: 'procurement.customs-kind-keywords',
  listRoute: appRoutes.procurement.customsKindKeywords,
  searchParam: 'keyword',
  searchPlaceholder: 'Tìm từ khóa…',
  quickFilters: [
    { key: 'kind', label: 'Loại', type: 'select', options: KIND_FILTER_OPTIONS },
    { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
  ],
  getItemName: (row) => row.keyword,
  deleteWarning:
    'Xóa từ khóa thì các dòng đang mang nhãn nhờ nó KHÔNG tự đổi — bấm «Gắn lại nhãn» sau khi xóa. Muốn tạm tắt thì chuyển sang «Ngừng dùng».',
  renderToolbarExtra: () => <CustomsRetagButton />,
  openFormOnRowClick: true,
  columns: [
    {
      key: 'keyword',
      header: 'Từ khóa',
      width: 220,
      sortable: true,
      hideable: false,
      cell: (row) => <span className="font-medium">{row.keyword}</span>,
    },
    {
      key: 'kind',
      header: 'Gắn nhãn',
      width: 160,
      sortable: true,
      cell: (row) => (
        <Badge variant={row.kind === PRODUCT_KIND.TECHNICAL ? 'default' : 'secondary'}>
          <Tag className="size-3" />
          {formatProductKindLabel(row.kind)}
        </Badge>
      ),
    },
    { key: 'note', header: 'Ghi chú', width: 320, wrap: true, cell: (row) => row.note },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 120,
      sortable: true,
      cell: (row) => (
        <Badge variant={row.is_active ? 'default' : 'secondary'}>
          {row.is_active ? (
            <CircleCheck className="size-3" />
          ) : (
            <CircleX className="size-3" />
          )}
          {row.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'keyword', label: 'Từ khóa', type: 'text' },
      { name: 'kind', label: 'Loại', type: 'select', options: KIND_FILTER_OPTIONS },
      { name: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    preserveParams: ['kind', 'is_active'],
  },
  formFields: [
    {
      name: 'keyword',
      label: 'Từ khóa',
      type: 'text',
      required: true,
      fullWidth: true,
      hint: 'Không phân biệt hoa/thường. Từ ngắn (TC, TG…) chỉ khớp khi đứng thành một từ — «TC» không dính «ATC». Từ dài khớp cả khi nằm trong chuỗi («kỹ thuật» khớp «Thuốc kỹ thuật ATRAZINE»).',
    },
    {
      name: 'kind',
      label: 'Gắn nhãn',
      type: 'select',
      required: true,
      defaultValue: PRODUCT_KIND.TECHNICAL,
      options: PRODUCT_KIND_OPTIONS.map((item) => ({ value: item.value, label: item.label })),
      hint: 'Thường là «Nguyên liệu». Chọn «Thành phẩm» cho từ khóa NGOẠI LỆ muốn thắng ngược (vd tên chứa TECHNOLOGY nhưng vẫn là thành phẩm).',
    },
    { name: 'note', label: 'Ghi chú', type: 'textarea', fullWidth: true },
    {
      name: 'is_active',
      label: 'Đang sử dụng',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng thì lần gắn lại nhãn tới không còn xét từ khóa này.',
    },
  ],
}
