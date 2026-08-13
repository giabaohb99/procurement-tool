import { useCallback, useMemo } from 'react'

import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { DOCUMENT_TYPE_FILTER_FIELDS } from '../config/document-filter-fields'
import { filterDocumentTypes } from '../helpers/filter-document-types'
import { useDocumentTypes } from '../hooks/use-document-types'
import { DOCUMENT_TYPE_OPTIONS, type DocumentType } from '../types/document-type'
import { CatalogTable } from './catalog-table'

const FILTER_CONFIG = {
  fields: DOCUMENT_TYPE_FILTER_FIELDS,
  allowConjunctionToggle: true,
  // Thiếu tên nào ở đây thì bấm "Áp dụng" bộ lọc nâng cao sẽ xóa mất tham số đó
  // — kể cả `tab`, tức là văng khỏi tab đang xem.
  preserveParams: ['status', 'tab'],
}

/**
 * Danh mục LOẠI VĂN BẢN — mỗi văn bản khi tạo chọn một loại ở đây, số hiệu sinh
 * theo tiền tố của loại đó.
 *
 * ⚠️ Dữ liệu còn nằm ở kho tạm phía trình duyệt (`store/document-type-store.ts`),
 * chờ backend có `/api/document-types`.
 */
export function DocumentTypeCatalog() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <DocumentTypeCatalogContent />
    </FilterProvider>
  )
}

function DocumentTypeCatalogContent() {
  const { items } = useDocumentTypes()

  // Lọc tại chỗ chứ không gửi query param: chưa có backend để lọc hộ.
  const { appliedState } = useFilterContext()
  const filterRows = useCallback(
    (rows: DocumentType[]) => filterDocumentTypes(rows, appliedState),
    [appliedState],
  )

  const columns = useMemo<DataTableColumn<DocumentType>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã loại',
        width: 110,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.code}</span>,
      },
      { key: 'name', header: 'Tên loại văn bản', width: 220, cell: (row) => row.name },
      {
        key: 'prefix',
        header: 'Tiền tố số hiệu',
        width: 160,
        // Mẫu số hiệu thật dễ hiểu hơn mỗi chuỗi tiền tố trơ trọi.
        cell: (row) => (
          <span className="font-mono text-xs text-muted-foreground">
            {row.prefix}-2026-001
          </span>
        ),
      },
      {
        key: 'options',
        header: 'Tùy chọn',
        width: 260,
        // Chỉ liệt kê cái ĐANG BẬT: kê cả cái tắt thì cột nào cũng như cột nào,
        // nhìn không ra loại nào khác loại nào.
        cell: (row) => (
          <span className="flex flex-wrap gap-1">
            {DOCUMENT_TYPE_OPTIONS.filter((option) => row[option.key]).map((option) => (
              <Badge key={option.key} variant="outline" className="font-normal">
                {option.label}
              </Badge>
            ))}
          </span>
        ),
      },
      {
        key: 'description',
        header: 'Mô tả',
        defaultHidden: true,
        cell: (row) => row.description,
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
    [],
  )

  return (
    <CatalogTable
      storageKey="document.types"
      items={items}
      columns={columns}
      searchFields={(row) => [row.code, row.name, row.prefix]}
      searchPlaceholder="Tìm theo mã, tên hoặc tiền tố…"
      detailPath={appRoutes.document.typeDetail}
      emptyMessage="Không có loại văn bản nào khớp điều kiện đang lọc."
      filterRows={filterRows}
      extraToolbar={<ConditionalFilter />}
    />
  )
}
