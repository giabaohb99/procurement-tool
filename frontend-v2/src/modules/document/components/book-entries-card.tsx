import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { formatDate } from '@/shared/utils/format-date'
import { useDocuments } from '../hooks/use-documents'
import type { DocumentRecord } from '../types/document-record'

interface BookEntriesCardProps {
  bookId: number
  year: number
}

/**
 * VĂN BẢN TRONG SỔ — xếp theo số vào sổ tăng dần, đọc y như quyển sổ giấy.
 *
 * Lọc theo `book_id` chứ không theo loại sổ: một pháp nhân mở được nhiều sổ
 * cùng loại (sổ Quyết định của Hành chính, sổ Quyết định của Nhân sự), gộp theo
 * loại thì hai quyển lẫn vào nhau.
 *
 * Danh sách này đi qua đúng lớp quyền của `/api/documents` — mở trang sổ không
 * phải là đường vòng để xem văn bản mình không được xem.
 */
export function BookEntriesCard({ bookId, year }: BookEntriesCardProps) {
  const navigate = useNavigate()
  const { data, isLoading } = useDocuments({ book_id: bookId, page_size: 100 })

  const rows = useMemo(() => {
    const items = data?.items ?? []
    return items
      .filter((item) => !item.book_year || item.book_year === year)
      .sort((a, b) => (a.book_seq_no ?? 0) - (b.book_seq_no ?? 0))
  }, [data, year])

  const columns = useMemo<DataTableColumn<DocumentRecord>[]>(
    () => [
      {
        key: 'book_seq_no',
        header: 'Số vào sổ',
        width: 110,
        align: 'right',
        hideable: false,
        // Chưa duyệt thì chưa vào sổ — số vào sổ cấp cùng lúc với số hiệu.
        cell: (row) => (
          <span className="font-medium tabular-nums">
            {row.book_seq_no ?? <span className="text-muted-foreground">—</span>}
          </span>
        ),
      },
      {
        key: 'display_code',
        header: 'Số hiệu',
        width: 170,
        cell: (row) => row.display_code || '',
      },
      { key: 'title', header: 'Tên văn bản', cell: (row) => row.title },
      {
        key: 'doc_type_name',
        header: 'Loại',
        width: 150,
        cell: (row) => row.doc_type_name,
      },
      {
        key: 'effective_date',
        header: 'Ngày hiệu lực',
        width: 140,
        cell: (row) => formatDate(row.effective_date ?? ''),
      },
      {
        key: 'status_label',
        header: 'Trạng thái',
        width: 140,
        cell: (row) => (
          <Badge variant="outline" className="font-normal">
            {row.status_label}
          </Badge>
        ),
      },
      {
        key: 'signer_name',
        header: 'Người ký',
        width: 160,
        cell: (row) => row.signer_name,
      },
    ],
    [],
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Văn bản trong sổ · {year}</CardTitle>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          rows={rows}
          getRowId={(row) => row.id}
          storageKey="document.book-entries"
          isLoading={isLoading}
          onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
          emptyMessage="Sổ năm này chưa có văn bản nào."
        />
      </CardContent>
    </Card>
  )
}
