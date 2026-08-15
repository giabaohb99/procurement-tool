import { useMemo } from 'react'

import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { CatalogTable } from './catalog-table'
import { useSecurityLevels } from '../hooks/use-document-catalogs'
import {
  SECURITY_LEVEL_KIND_LABELS,
  type SecurityLevel,
} from '../types/security-level'

/**
 * MỨC MẬT / ĐỘ KHẨN — bảng **chỉ đọc**, không thêm sửa xóa được.
 *
 * Đây là thang cố định khai trong mã, không phải danh mục: mức mật lưu xuống DB
 * bằng số và mọi lớp kiểm quyền so sánh bằng chính con số đó. Cho sửa ở đây thì
 * phần kiểm quyền hiểu một đằng, danh mục nói một nẻo — mà sai chỗ này nghĩa là
 * lộ văn bản mật. Chi tiết ở `types/security-level.ts`.
 */
export function SecurityLevelCatalog() {
  const items = useSecurityLevels()

  const columns = useMemo<DataTableColumn<SecurityLevel>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã',
        width: 130,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.code}</span>,
      },
      { key: 'name', header: 'Tên mức', width: 180, cell: (row) => row.name },
      {
        key: 'kind',
        header: 'Thang',
        width: 130,
        cell: (row) => (
          <Badge variant="outline" className="font-normal">
            {SECURITY_LEVEL_KIND_LABELS[row.kind]}
          </Badge>
        ),
      },
      {
        key: 'rank',
        header: 'Bậc',
        width: 100,
        align: 'right',
        // Số càng lớn càng nghiêm/gấp — hiện thẳng con số để so sánh nhanh.
        cell: (row) => <span className="tabular-nums">{row.rank}</span>,
      },
      { key: 'description', header: 'Mô tả', cell: (row) => row.description },
    ],
    [],
  )

  return (
    <CatalogTable
      storageKey="document.security-levels"
      items={items}
      columns={columns}
      searchFields={(row) => [row.code, row.name]}
      searchPlaceholder="Tìm theo mã hoặc tên mức…"
    />
  )
}
