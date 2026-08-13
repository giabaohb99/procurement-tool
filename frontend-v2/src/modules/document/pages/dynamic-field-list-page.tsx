import { useMemo } from 'react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { CatalogListPage } from '../components/catalog-list-page'
import { useDocumentTypes } from '../hooks/use-document-types'
import { useDynamicFields } from '../hooks/use-document-catalogs'
import {
  DYNAMIC_FIELD_TYPE_LABELS,
  type DynamicField,
} from '../types/dynamic-field'

/**
 * Danh mục TRƯỜNG THÔNG TIN ĐỘNG — ô nhập thêm cho văn bản, khai bằng cấu hình
 * chứ không phải sửa code.
 */
export function DynamicFieldListPage() {
  const items = useDynamicFields()
  const { items: documentTypes } = useDocumentTypes()

  const columns = useMemo<DataTableColumn<DynamicField>[]>(
    () => [
      {
        key: 'label',
        header: 'Nhãn hiển thị',
        width: 220,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.label}</span>,
      },
      {
        key: 'code',
        header: 'Khóa',
        width: 180,
        cell: (row) => <span className="font-mono text-xs">{row.code}</span>,
      },
      {
        key: 'field_type',
        header: 'Kiểu dữ liệu',
        width: 170,
        cell: (row) => (
          <Badge variant="outline" className="font-normal">
            {DYNAMIC_FIELD_TYPE_LABELS[row.field_type]}
          </Badge>
        ),
      },
      {
        key: 'document_type_ids',
        header: 'Áp dụng cho',
        width: 240,
        // Rỗng = mọi loại; nói thẳng ra chứ để trống thì người đọc tưởng thiếu
        // dữ liệu.
        cell: (row) =>
          row.document_type_ids.length === 0 ? (
            <span className="text-muted-foreground">Mọi loại văn bản</span>
          ) : (
            <span className="flex flex-wrap gap-1">
              {row.document_type_ids.map((typeId) => (
                <Badge key={typeId} variant="outline" className="font-normal">
                  {documentTypes.find((type) => type.id === typeId)?.name ?? `#${typeId}`}
                </Badge>
              ))}
            </span>
          ),
      },
      {
        key: 'is_required',
        header: 'Bắt buộc',
        width: 110,
        cell: (row) => (row.is_required ? 'Có' : '—'),
      },
      {
        key: 'sort_order',
        header: 'Thứ tự',
        width: 90,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{row.sort_order}</span>,
      },
      {
        key: 'is_active',
        header: 'Trạng thái',
        width: 120,
        cell: (row) => (
          <Badge variant={row.is_active ? 'default' : 'secondary'}>
            {row.is_active ? 'Đang dùng' : 'Ngừng'}
          </Badge>
        ),
      },
    ],
    [documentTypes],
  )

  return (
    <CatalogListPage
      title="Trường thông tin động"
      description="Khai thêm ô nhập cho văn bản mà không phải sửa code — vd giá trị hợp đồng, phạm vi áp dụng."
      storageKey="document.dynamic-fields"
      items={items}
      columns={columns}
      searchFields={(row) => [row.code, row.label]}
      searchPlaceholder="Tìm theo khóa hoặc nhãn…"
      newPath={appRoutes.document.fieldNew}
      detailPath={appRoutes.document.fieldDetail}
    />
  )
}
