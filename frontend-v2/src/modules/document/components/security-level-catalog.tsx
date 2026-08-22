import { useMemo } from 'react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { CatalogTable } from './catalog-table'
import { useSecurityLevels } from '../hooks/use-document-catalogs'
import { SECURITY_LEVEL_KIND_LABELS, type SecurityLevel } from '../types/security-level'

/**
 * MỨC MẬT / ĐỘ KHẨN — danh mục CRUD từ 22/08/2026 (trước đó khai cứng trong mã).
 *
 * `id` (khóa chính, cột "ID" ẩn mặc định) khác `value` (cột "Bậc", con số thật
 * lưu trên văn bản) — xem cảnh báo đầu `types/security-level.ts`. Đừng lẫn hai
 * cột này khi đọc bảng.
 */
export function SecurityLevelCatalog() {
  const { items, isLoading } = useSecurityLevels()

  const columns = useMemo<DataTableColumn<SecurityLevel>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã',
        width: 130,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.code}</span>,
      },
      { key: 'name', header: 'Tên bậc', width: 180, cell: (row) => row.name },
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
        key: 'value',
        header: 'Bậc',
        width: 90,
        align: 'right',
        // Số càng lớn càng nghiêm/gấp — hiện thẳng con số để so sánh nhanh.
        // Đây là VALUE lưu trên văn bản, không phải id (cột ID ẩn mặc định).
        cell: (row) => <span className="tabular-nums">{row.value}</span>,
      },
      { key: 'description', header: 'Mô tả', cell: (row) => row.description },
      {
        key: 'id',
        header: 'ID',
        width: 80,
        align: 'right',
        defaultHidden: true,
        cell: (row) => <span className="tabular-nums text-muted-foreground">{row.id}</span>,
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
      storageKey="document.security-levels"
      items={items}
      columns={columns}
      searchFields={(row) => [row.code, row.name]}
      searchPlaceholder="Tìm theo mã hoặc tên bậc…"
      detailPath={appRoutes.document.securityLevelDetail}
      emptyMessage={
        isLoading ? 'Đang tải danh mục…' : 'Không có bậc nào khớp điều kiện đang lọc.'
      }
    />
  )
}
