import { useMemo } from 'react'

import { SCROLL_TABS_TOOLBAR_STICKY } from '@/modules/hr/utils/list-sticky'
import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { formatDateTime } from '@/shared/utils/format-date'
import { useDocumentTemplates } from '../hooks/use-document-templates'
import type { DocumentTemplateListItem } from '../types/document-template'
import { CatalogCard } from './catalog-card'
import { CatalogTable } from './catalog-table'

/** Danh sách văn bản mẫu; bấm một dòng để mở đúng trình soạn thảo của văn bản. */
export function DocumentTemplateCatalog() {
  const { items, isLoading, isError } = useDocumentTemplates()

  const columns = useMemo<DataTableColumn<DocumentTemplateListItem>[]>(
    () => [
      {
        key: 'name',
        header: 'Tên văn bản mẫu',
        width: 260,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.name}</span>,
      },
      {
        key: 'doc_type_name',
        header: 'Loại văn bản',
        width: 220,
        cell: (row) => (
          <span>
            <span className="font-medium">{row.doc_type_code}</span>
            <span className="text-muted-foreground"> · {row.doc_type_name}</span>
          </span>
        ),
      },
      {
        key: 'description',
        header: 'Mô tả',
        cell: (row) => row.description || '—',
      },
      {
        key: 'updated_at',
        header: 'Cập nhật',
        width: 150,
        cell: (row) => formatDateTime(row.updated_at),
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
      storageKey="document.templates"
      //  Ghim thanh công cụ ở khổ hẹp — trang bỏ `fill` nên CẢ TRANG cuộn, không
      //  ghim thì ô tìm trôi mất ngay nhịp vuốt đầu. Mốc 37px = chiều cao dải tab
      //  cuộn ngang phía trên (xem `SCROLL_TABS_TOOLBAR_STICKY`).
      toolbarClassName={SCROLL_TABS_TOOLBAR_STICKY}
      items={items}
      columns={columns}
      searchFields={(row) => [row.name, row.doc_type_code, row.doc_type_name, row.description]}
      searchPlaceholder="Tìm theo tên mẫu hoặc loại văn bản…"
      searchPlaceholderShort="Tìm tên mẫu, loại…"
      detailPath={appRoutes.document.templateDetail}
      //  Mẫu không có mã riêng — dòng phụ là *mã loại · tên loại*, đúng thứ
      //  phân biệt hai mẫu cùng tên thuộc hai loại văn bản khác nhau.
      mobileCard={(row) => (
        <CatalogCard
          title={row.name}
          code={row.doc_type_code}
          meta={[row.doc_type_name, `Cập nhật ${formatDateTime(row.updated_at)}`]}
          isActive={row.is_active}
          note={row.description}
        />
      )}
      emptyMessage={
        isLoading
          ? 'Đang tải thư viện văn bản mẫu…'
          : isError
            ? 'Không tải được thư viện văn bản mẫu.'
            : 'Chưa có văn bản mẫu nào khớp điều kiện đang lọc.'
      }
    />
  )
}
