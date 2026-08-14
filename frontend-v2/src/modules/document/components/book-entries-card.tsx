import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { formatDate } from '@/shared/utils/format-date'
import { useDocumentPartners } from '../hooks/use-document-catalogs'
import { useDocuments } from '../hooks/use-documents'
import type { BookKind } from '../types/document-book'
import type { DocumentDirection, DocumentRecord } from '../types/document-record'

/** Loại sổ ↔ luồng văn bản. Hai thang cùng nghĩa, đặt cạnh nhau cho khỏi lệch. */
const KIND_TO_DIRECTION: Record<BookKind, DocumentDirection> = {
  1: 'incoming',
  2: 'outgoing',
  3: 'internal',
}

interface BookEntriesCardProps {
  kind: BookKind
  year: number
}

/**
 * VĂN BẢN TRONG SỔ — xếp theo số vào sổ tăng dần, đọc y như quyển sổ giấy.
 *
 * ⚠️ Dữ liệu còn lấy từ kho tạm phía trình duyệt (`store/document-record-store.ts`)
 * và lọc theo `direction` chứ chưa theo `book_id` — bảng văn bản chưa có backend.
 * Khi bảng đó lên API thì lọc thẳng theo id sổ và bỏ `KIND_TO_DIRECTION` đi.
 */
export function BookEntriesCard({ kind, year }: BookEntriesCardProps) {
  const navigate = useNavigate()
  const records = useDocuments()
  const { items: partners } = useDocumentPartners()

  const rows = useMemo(
    () =>
      records
        .filter(
          (record) =>
            record.direction === KIND_TO_DIRECTION[kind] && record.book_year === year,
        )
        .sort((a, b) => a.book_no - b.book_no),
    [records, kind, year],
  )

  const columns = useMemo<DataTableColumn<DocumentRecord>[]>(
    () => [
      {
        key: 'book_no',
        header: 'Số vào sổ',
        width: 110,
        align: 'right',
        hideable: false,
        cell: (row) => <span className="font-medium tabular-nums">{row.book_no}</span>,
      },
      { key: 'code', header: 'Số hiệu', width: 150, cell: (row) => row.code },
      {
        key: 'issued_date',
        header: 'Ngày ban hành',
        width: 140,
        cell: (row) => formatDate(row.issued_date),
      },
      {
        key: 'received_date',
        header: 'Ngày đến',
        width: 130,
        // Chỉ sổ văn bản đến mới có cột này.
        defaultHidden: kind !== 1,
        cell: (row) => formatDate(row.received_date),
      },
      { key: 'title', header: 'Trích yếu', cell: (row) => row.title },
      {
        key: 'partner_id',
        header: 'Nơi gửi / nhận',
        width: 220,
        cell: (row) => partners.find((partner) => partner.id === row.partner_id)?.name ?? '',
      },
      { key: 'signer', header: 'Người ký', width: 160, cell: (row) => row.signer },
    ],
    [partners, kind],
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
          onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
          emptyMessage="Sổ năm này chưa có văn bản nào."
        />
      </CardContent>
    </Card>
  )
}
