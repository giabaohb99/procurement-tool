import { useMemo } from 'react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { CatalogListPage } from '../components/catalog-list-page'
import { useDocumentPartners } from '../hooks/use-document-catalogs'
import { PARTNER_KIND_LABELS, type DocumentPartner } from '../types/document-partner'

/** Danh mục ĐỐI TÁC — nơi gửi của văn bản đến, nơi nhận của văn bản đi. */
export function DocumentPartnerListPage() {
  const items = useDocumentPartners()

  const columns = useMemo<DataTableColumn<DocumentPartner>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã',
        width: 130,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.code}</span>,
      },
      { key: 'name', header: 'Tên đối tác', width: 280, cell: (row) => row.name },
      {
        key: 'kind',
        header: 'Nhóm',
        width: 160,
        cell: (row) => (
          <Badge variant="outline" className="font-normal">
            {PARTNER_KIND_LABELS[row.kind]}
          </Badge>
        ),
      },
      { key: 'contact_person', header: 'Người liên hệ', width: 160, cell: (row) => row.contact_person },
      { key: 'phone', header: 'Điện thoại', width: 130, cell: (row) => row.phone },
      { key: 'email', header: 'Email', width: 200, defaultHidden: true, cell: (row) => row.email },
      { key: 'address', header: 'Địa chỉ', defaultHidden: true, cell: (row) => row.address },
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
    <CatalogListPage
      title="Đối tác"
      description="Cơ quan, doanh nghiệp, cá nhân và đơn vị nội bộ trao đổi văn bản với công ty."
      storageKey="document.partners"
      items={items}
      columns={columns}
      searchFields={(row) => [row.code, row.name, row.contact_person, row.phone]}
      searchPlaceholder="Tìm theo mã, tên hoặc người liên hệ…"
      newPath={appRoutes.document.partnerNew}
      detailPath={appRoutes.document.partnerDetail}
    />
  )
}
