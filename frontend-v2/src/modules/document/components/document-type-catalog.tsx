import { useCallback, useMemo } from 'react'

import {
  applyClientFilter,
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { DOCUMENT_TYPE_FILTER_FIELDS } from '../config/document-filter-fields'
import { useDocumentTypes } from '../hooks/use-document-types'
import {
  DOCUMENT_TYPE_FLAGS,
  DOC_GROUP_LABELS,
  ID_SCHEME_LABELS,
  documentCodeSample,
  type DocumentType,
} from '../types/document-type'
import { secrecyLabel } from '../types/security-level'
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
 * theo mã của loại đó.
 */
export function DocumentTypeCatalog() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <DocumentTypeCatalogContent />
    </FilterProvider>
  )
}

function DocumentTypeCatalogContent() {
  const { items, isLoading } = useDocumentTypes()

  // Lọc tại chỗ chứ không gửi query param: danh mục dưới 100 dòng, đã nạp cả
  // danh sách rồi thì lọc ở client nhanh hơn và đỡ một vòng gọi mỗi lần gõ.
  const { appliedState } = useFilterContext()
  const filterRows = useCallback(
    (rows: DocumentType[]) => applyClientFilter(rows, appliedState),
    [appliedState],
  )

  const columns = useMemo<DataTableColumn<DocumentType>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã loại',
        width: 100,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.code}</span>,
      },
      { key: 'name', header: 'Tên loại văn bản', width: 220, cell: (row) => row.name },
      {
        key: 'id_scheme',
        header: 'Số hiệu',
        width: 210,
        // Mẫu số hiệu thật dễ hiểu hơn chữ "mã bất biến / theo sổ" trơ trọi.
        cell: (row) => (
          <span className="flex flex-col">
            <span className="font-mono text-xs text-muted-foreground">
              {documentCodeSample(row.code, row.id_scheme)}
            </span>
            <span className="text-xs text-muted-foreground">
              {ID_SCHEME_LABELS[row.id_scheme]}
            </span>
          </span>
        ),
      },
      {
        key: 'flags',
        header: 'Quy tắc',
        width: 240,
        // Chỉ liệt kê cái ĐANG BẬT: kê cả cái tắt thì cột nào cũng như cột nào,
        // nhìn không ra loại nào khác loại nào.
        cell: (row) => (
          <span className="flex flex-wrap gap-1">
            {DOCUMENT_TYPE_FLAGS.filter((flag) => row[flag.key]).map((flag) => (
              <Badge key={flag.key} variant="outline" className="font-normal">
                {flag.label}
              </Badge>
            ))}
          </span>
        ),
      },
      {
        key: 'default_secrecy',
        header: 'Mức mật mặc định',
        width: 150,
        defaultHidden: true,
        cell: (row) => secrecyLabel(row.default_secrecy),
      },
      {
        key: 'group_code',
        header: 'Nhóm',
        width: 180,
        defaultHidden: true,
        cell: (row) => DOC_GROUP_LABELS[row.group_code] ?? '—',
      },
      {
        key: 'review_cycle_months',
        header: 'Chu kỳ rà soát',
        width: 130,
        defaultHidden: true,
        cell: (row) => (row.review_cycle_months ? `${row.review_cycle_months} tháng` : '—'),
      },
      {
        key: 'description',
        header: 'Mô tả',
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
      searchFields={(row) => [row.code, row.name]}
      searchPlaceholder="Tìm theo mã hoặc tên loại…"
      detailPath={appRoutes.document.typeDetail}
      emptyMessage={
        isLoading
          ? 'Đang tải danh mục…'
          : 'Không có loại văn bản nào khớp điều kiện đang lọc.'
      }
      filterRows={filterRows}
      extraToolbar={<ConditionalFilter />}
    />
  )
}
