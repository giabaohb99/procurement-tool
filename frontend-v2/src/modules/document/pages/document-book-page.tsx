import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDate } from '@/shared/utils/format-date'
import { useDocumentPartners } from '../hooks/use-document-catalogs'
import { useDocuments } from '../hooks/use-documents'
import {
  BOOK_LABELS,
  DIRECTION_LABELS,
  type DocumentDirection,
  type DocumentRecord,
} from '../types/document-record'

/**
 * SỔ VĂN BẢN ĐẾN / ĐI / NỘI BỘ.
 *
 * Không phải bảng thứ hai: sổ chính là các văn bản đã lưu, xếp theo SỐ VÀO SỔ
 * tăng dần của từng (luồng × năm) — mở ra là đọc y như quyển sổ giấy. Số do hệ
 * cấp lúc tạo văn bản nên không có thao tác "vào sổ" thủ công nào.
 */
export function DocumentBookPage() {
  const navigate = useNavigate()
  const [direction, setDirection] = useUrlParamState('direction', 'incoming')
  const records = useDocuments()
  const partners = useDocumentPartners()

  /** Các năm đang có văn bản, mới nhất trước. */
  const years = useMemo(() => {
    const set = new Set(records.map((record) => record.book_year))
    if (set.size === 0) set.add(new Date().getFullYear())
    return [...set].sort((a, b) => b - a)
  }, [records])

  const [year, setYear] = useUrlParamState('year', String(years[0]))

  const rows = useMemo(
    () =>
      records
        .filter(
          (record) => record.direction === direction && record.book_year === Number(year),
        )
        .sort((a, b) => a.book_no - b.book_no),
    [records, direction, year],
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
        defaultHidden: direction !== 'incoming',
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
    [partners, direction],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title={BOOK_LABELS[direction as DocumentDirection]}
        description="Danh sách theo số vào sổ — số do hệ cấp tự động khi tạo văn bản."
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Tabs value={direction} onValueChange={setDirection}>
          <TabsList>
            {Object.entries(DIRECTION_LABELS).map(([value, label]) => (
              <TabsTrigger key={value} value={value}>
                {label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        <Select value={year} onValueChange={setYear}>
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {years.map((option) => (
              <SelectItem key={option} value={String(option)}>
                Năm {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Bọc `Card` như mọi màn danh sách khác — bảng đặt trần lên nền trang
          thì màu hàng tiêu đề và thân bảng lệch so với các phân hệ kia. */}
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={columns}
          rows={rows}
          getRowId={(row) => row.id}
          storageKey="document.books"
          fillHeight
          onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
          emptyMessage="Sổ năm này chưa có văn bản nào."
        />
      </Card>
    </PageContainer>
  )
}
