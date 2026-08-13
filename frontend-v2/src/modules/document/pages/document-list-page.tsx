import { Plus, Search } from 'lucide-react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
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
import { effectiveLabel } from '../helpers/document-status'
import {
  useDocumentPartners,
  useSecurityLevels,
} from '../hooks/use-document-catalogs'
import { useDocumentTypes } from '../hooks/use-document-types'
import { useDocuments } from '../hooks/use-documents'
import {
  DIRECTION_LABELS,
  PROCESSING_STATUS_LABELS,
  PROCESSING_STATUS_VARIANTS,
  STATUS_LABELS,
  type DocumentRecord,
} from '../types/document-record'

const ALL = 'all'

/**
 * Danh sách VĂN BẢN — tra cứu theo luồng (đến / đi / nội bộ), loại và hiệu lực.
 *
 * Tab luồng ghi lên URL nên gửi link "văn bản đến đang còn hiệu lực" cho người
 * khác vẫn ra đúng thứ đang xem.
 */
export function DocumentListPage() {
  const navigate = useNavigate()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [direction, setDirection] = useUrlParamState('direction', ALL)
  const [typeId, setTypeId] = useUrlParamState('type', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [processing, setProcessing] = useUrlParamState('processing', ALL)

  const records = useDocuments()
  const { items: documentTypes } = useDocumentTypes()
  const partners = useDocumentPartners()
  const securityLevels = useSecurityLevels()

  const rows = useMemo(() => {
    const needle = debouncedValue.trim().toLowerCase()
    return records
      .filter((record) => {
        if (direction !== ALL && record.direction !== direction) return false
        if (typeId !== ALL && record.document_type_id !== Number(typeId)) return false
        if (status !== ALL && record.status !== status) return false
        if (processing !== ALL && record.processing_status !== processing) return false
        if (!needle) return true
        return [record.code, record.title, record.signer, record.handler].some((field) =>
          (field ?? '').toLowerCase().includes(needle),
        )
      })
      // Mới nhất lên đầu: sổ văn bản luôn đọc từ số cuối trở lên.
      .sort((a, b) => b.book_year - a.book_year || b.book_no - a.book_no)
  }, [records, direction, typeId, status, processing, debouncedValue])

  const columns = useMemo<DataTableColumn<DocumentRecord>[]>(
    () => [
      {
        key: 'code',
        header: 'Số hiệu',
        width: 150,
        hideable: false,
        defaultPinned: true,
        cell: (row) => <span className="font-medium text-navy">{row.code}</span>,
      },
      {
        key: 'book_no',
        header: 'Số đến/đi',
        width: 110,
        align: 'right',
        cell: (row) => (
          <span className="tabular-nums">
            {row.book_no}/{row.book_year}
          </span>
        ),
      },
      { key: 'title', header: 'Trích yếu', width: 320, cell: (row) => row.title },
      {
        key: 'direction',
        header: 'Luồng',
        width: 140,
        cell: (row) => (
          <Badge variant="outline" className="font-normal">
            {DIRECTION_LABELS[row.direction]}
          </Badge>
        ),
      },
      {
        key: 'document_type_id',
        header: 'Loại',
        width: 150,
        cell: (row) =>
          documentTypes.find((type) => type.id === row.document_type_id)?.name ?? '',
      },
      {
        key: 'partner_id',
        header: 'Nơi gửi / nhận',
        width: 220,
        cell: (row) => partners.find((partner) => partner.id === row.partner_id)?.name ?? '',
      },
      {
        key: 'levels',
        header: 'Mật / khẩn',
        width: 170,
        cell: (row) => (
          <span className="flex flex-wrap gap-1">
            {[row.confidential_level_id, row.urgent_level_id]
              .map((levelId) => securityLevels.find((level) => level.id === levelId))
              .filter((level) => level && level.rank > 0)
              .map((level) => (
                <Badge key={level!.id} variant="outline" className="font-normal">
                  {level!.name}
                </Badge>
              ))}
          </span>
        ),
      },
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
        defaultHidden: true,
        cell: (row) => formatDate(row.received_date),
      },
      { key: 'signer', header: 'Người ký', width: 160, defaultHidden: true, cell: (row) => row.signer },
      {
        key: 'processing_status',
        header: 'Tình trạng xử lý',
        width: 160,
        // Văn bản lập trước khi có khối "Tình trạng xử lý" chưa mang trường
        // này — coi như còn chờ xử lý, đừng để ô trống không đọc được gì.
        cell: (row) => {
          const value = row.processing_status ?? 'pending'
          return (
            <Badge variant={PROCESSING_STATUS_VARIANTS[value]}>
              {PROCESSING_STATUS_LABELS[value]}
            </Badge>
          )
        },
      },
      {
        key: 'handler',
        header: 'Người xử lý',
        width: 160,
        defaultHidden: true,
        cell: (row) => row.handler,
      },
      {
        key: 'due_date',
        header: 'Hạn xử lý',
        width: 130,
        defaultHidden: true,
        cell: (row) => formatDate(row.due_date),
      },
      {
        key: 'status',
        header: 'Hiệu lực',
        width: 140,
        // Nhãn TÍNH RA lúc hiển thị (hết hạn theo ngày), không phải trạng thái thô.
        cell: (row) => {
          const label = effectiveLabel(row)
          return <Badge variant={label.variant}>{label.text}</Badge>
        },
      },
      {
        key: 'attachments',
        header: 'Tệp',
        width: 80,
        align: 'right',
        cell: (row) => (row.attachments.length ? `${row.attachments.length}` : ''),
      },
    ],
    [documentTypes, partners, securityLevels],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Văn bản"
        description="Văn bản đến, đi và nội bộ — số hiệu và số vào sổ do hệ cấp tự động."
        actions={
          <Button
            onClick={() =>
              navigate(
                // Mang luồng đang xem sang trang thêm mới cho khỏi phải chọn lại.
                direction === ALL
                  ? appRoutes.document.documentNew
                  : `${appRoutes.document.documentNew}?direction=${direction}`,
              )
            }
          >
            <Plus className="size-4" />
            Thêm mới
          </Button>
        }
      />

      <Tabs value={direction} onValueChange={setDirection} className="mb-4">
        <TabsList>
          <TabsTrigger value={ALL}>Tất cả</TabsTrigger>
          {Object.entries(DIRECTION_LABELS).map(([value, label]) => (
            <TabsTrigger key={value} value={value}>
              {label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Bọc `Card` như mọi màn danh sách khác — bảng đặt trần lên nền trang
          thì màu hàng tiêu đề và thân bảng lệch so với các phân hệ kia. */}
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={columns}
          rows={rows}
          getRowId={(row) => row.id}
          storageKey="document.records"
          fillHeight
          onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
          emptyMessage="Chưa có văn bản nào khớp điều kiện đang lọc."
          toolbar={
            <>
              <div className="relative w-full max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo số hiệu, trích yếu, người ký…"
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                />
              </div>

              <Select value={typeId} onValueChange={setTypeId}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả loại</SelectItem>
                  {documentTypes.map((type) => (
                    <SelectItem key={type.id} value={String(type.id)}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={processing} onValueChange={setProcessing}>
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả tình trạng</SelectItem>
                  {Object.entries(PROCESSING_STATUS_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả hiệu lực</SelectItem>
                  {Object.entries(STATUS_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
