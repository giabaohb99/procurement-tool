// bao-CR-495 — cấu hình CRUD danh mục TỪ ĐỒNG NGHĨA cho ô tìm tên hàng.
//
// Một dòng = một từ gốc + các cách viết tương đương (ngăn bằng «;»). Gõ từ nào trong nhóm cũng
// ra kết quả của cả nhóm. Nồng độ tương đương (3,6% ≡ 3.6EC ≡ 36 G/L) hệ tự quy đổi, không cần
// khai ở đây; bộ từ khóa → hoạt chất có sẵn (HQ4) cũng được dùng làm đồng nghĩa ngầm.
// Entity dùng chung `customs_price`, đường API `/api/customs-search-synonyms`.
import { CircleCheck, CircleX } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'

import type { CustomsSearchSynonym } from '../types/customs-admin'

const ACTIVE_OPTIONS = [
  { value: 'true', label: 'Đang dùng' },
  { value: 'false', label: 'Ngừng dùng' },
]

export const CUSTOMS_SEARCH_SYNONYM_CRUD_CONFIG: CrudConfig<CustomsSearchSynonym> = {
  entity: 'customs_price',
  title: 'Từ đồng nghĩa tìm kiếm',
  description:
    'Các cách viết tương đương của cùng một hoạt chất / tên hàng. Ô tìm trên màn Tra cứu giá hải quan gõ từ nào trong nhóm cũng ra kết quả của cả nhóm. Nồng độ (3,6% · 3.6EC · 36 G/L) hệ tự quy đổi, không cần khai.',
  unitLabel: 'nhóm từ',
  apiPath: '/api/customs-search-synonyms',
  storageKey: 'procurement.customs-search-synonyms',
  listRoute: appRoutes.procurement.customsSearchSynonyms,
  searchParam: 'term',
  searchPlaceholder: 'Tìm từ gốc…',
  quickFilters: [{ key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS }],
  getItemName: (row) => row.term,
  deleteWarning: 'Xóa nhóm thì gõ các từ trong nhóm không còn ra nhau nữa. Muốn tạm tắt thì chuyển sang «Ngừng dùng».',
  openFormOnRowClick: true,
  columns: [
    {
      key: 'term',
      header: 'Từ gốc',
      width: 200,
      sortable: true,
      hideable: false,
      cell: (row) => <span className="font-medium">{row.term}</span>,
    },
    {
      key: 'synonyms',
      header: 'Từ đồng nghĩa',
      width: 420,
      wrap: true,
      cell: (row) => (
        <span className="flex flex-wrap gap-1">
          {row.synonyms
            .split(';')
            .map((s) => s.trim())
            .filter(Boolean)
            .map((s) => (
              <Badge key={s} variant="outline">
                {s}
              </Badge>
            ))}
        </span>
      ),
    },
    { key: 'note', header: 'Ghi chú', width: 260, wrap: true, cell: (row) => row.note },
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
      { name: 'term', label: 'Từ gốc', type: 'text' },
      { name: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    preserveParams: ['is_active'],
  },
  formFields: [
    {
      name: 'term',
      label: 'Từ gốc',
      type: 'text',
      required: true,
      fullWidth: true,
      hint: 'Cách viết chính, vd «Abamectin».',
    },
    {
      name: 'synonyms',
      label: 'Từ đồng nghĩa',
      type: 'textarea',
      fullWidth: true,
      hint: 'Mỗi cách viết một dòng hoặc ngăn bằng «;», vd «Abamectine; Aba». Không phân biệt hoa/thường.',
    },
    { name: 'note', label: 'Ghi chú', type: 'textarea', fullWidth: true },
    { name: 'is_active', label: 'Đang sử dụng', type: 'switch', defaultValue: true },
  ],
}
