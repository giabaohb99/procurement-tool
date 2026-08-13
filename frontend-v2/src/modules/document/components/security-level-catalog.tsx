import { useMemo } from 'react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { CatalogTable } from './catalog-table'
import { useSecurityLevels } from '../hooks/use-document-catalogs'
import {
  SECURITY_LEVEL_KIND_LABELS,
  type SecurityLevel,
} from '../types/security-level'

/** Danh mục MỨC MẬT / KHẨN — hai thang đo nằm chung một bảng, phân biệt cột "Thang". */
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
        header: 'Thứ bậc',
        width: 100,
        align: 'right',
        // Số càng lớn càng nghiêm/gấp — hiện thẳng con số để so sánh nhanh.
        cell: (row) => <span className="tabular-nums">{row.rank}</span>,
      },
      { key: 'description', header: 'Mô tả', cell: (row) => row.description },
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
      storageKey="document.security-levels"
      items={items}
      columns={columns}
      searchFields={(row) => [row.code, row.name]}
      searchPlaceholder="Tìm theo mã hoặc tên mức…"
      detailPath={appRoutes.document.securityLevelDetail}
    />
  )
}
