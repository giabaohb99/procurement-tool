import { useMemo } from 'react'

import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { formatDate } from '@/shared/utils/format-date'
import { useDocumentsAppliedToMe } from '../hooks/use-document-scopes'
import type { DocumentRecord } from '../types/document-record'

/**
 * F05 — VĂN BẢN ÁP DỤNG CHO TÔI.
 *
 * Danh sách này KHÁC "tất cả văn bản tôi đọc được": ở đây chỉ những văn bản mà
 * người đang đăng nhập **nằm trong phạm vi áp dụng**, tức là phải làm theo. Đọc
 * được mà không thuộc phạm vi thì không hiện ở đây.
 */
export function DocumentsAppliedToMePage() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useDocumentsAppliedToMe()
  const items = useMemo(() => data?.items ?? [], [data?.items])

  const columns = useMemo<DataTableColumn<DocumentRecord>[]>(
    () => [
      {
        key: 'display_code',
        header: 'Số hiệu',
        width: 180,
        hideable: false,
        cell: (row) => (
          <span className="font-mono text-navy">{row.display_code || '—'}</span>
        ),
      },
      {
        key: 'title',
        header: 'Trích yếu',
        width: 380,
        cell: (row) => (
          <div>
            <div className="font-medium">{row.title}</div>
            {row.needs_review && (
              <div className="text-xs text-amber-800">Cần rà lại</div>
            )}
          </div>
        ),
      },
      { key: 'doc_type_name', header: 'Loại', width: 160, cell: (row) => row.doc_type_name },
      {
        key: 'status_label',
        header: 'Trạng thái',
        width: 140,
        cell: (row) => <Badge variant="outline">{row.status_label}</Badge>,
      },
      {
        key: 'effective_date',
        header: 'Hiệu lực từ',
        width: 140,
        cell: (row) => (row.effective_date ? formatDate(row.effective_date) : '—'),
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Văn bản áp dụng cho tôi"
        description="Những văn bản mà bạn nằm trong phạm vi áp dụng — không phải mọi văn bản bạn đọc được."
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={columns}
          rows={items}
          getRowId={(row) => row.id}
          storageKey="document.applies-to-me"
          fillHeight
          isLoading={isLoading}
          isError={isError}
          onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
          emptyMessage="Chưa có văn bản nào áp dụng cho bạn."
        />
      </Card>
    </PageContainer>
  )
}
