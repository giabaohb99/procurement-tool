import { ChevronRight, CornerDownRight, Plus, Search } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
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
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { effectiveLabel } from '../helpers/document-status'
import { useActiveDocumentTypes } from '../hooks/use-document-types'
import { useDocuments } from '../hooks/use-documents'
import { secrecyLabel, urgencyLabel } from '../types/security-level'
import { STATUS_LABELS, type DocumentRecord } from '../types/document-record'

const ALL = 'all'

/**
 * Danh sách VĂN BẢN.
 *
 * Tìm kiếm và phân trang chạy ở BACKEND, không nạp hết về rồi lọc tại trình
 * duyệt: ngoài chuyện bảng sẽ lên vài chục nghìn dòng, lọc ở client nghĩa là
 * máy người dùng phải nhận về cả những văn bản họ không được xem. Ô tìm chấp
 * nhận cả **số hiệu cũ của bản giấy** (C12).
 */
export function DocumentListPage() {
  const navigate = useNavigate()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [typeId, setTypeId] = useUrlParamState('type', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  //  Bung MỘT dòng tại một thời điểm: các bản riêng phải hỏi máy chủ, mà hook
  //  không gọi được trong vòng lặp. Mở dòng khác thì dòng đang mở tự đóng —
  //  cũng đúng thói quen dùng: người ta soi từng bản gốc một.
  const [dongDangBung, setDongDangBung] = useState<number | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const documentTypes = useActiveDocumentTypes()

  const { data, isLoading, isError } = useDocuments({
    page,
    page_size: pageSize,
    q: debouncedValue.trim() || undefined,
    doc_type_id: typeId === ALL ? undefined : Number(typeId),
    status: status === ALL ? undefined : Number(status),
  })

  //  Các BẢN RIÊNG của dòng đang bung. Backend giấu chúng khỏi danh sách chung
  //  (xem `an_ban_rieng_co_goc_xem_duoc`) nên phải hỏi đích danh theo bản gốc.
  const { data: banRieng } = useDocuments({
    source_document_id: dongDangBung ?? undefined,
    page_size: 100,
  })

  //  ⚠️ Phải chặn `dongDangBung === null`: `source_document_id` của văn bản
  //  thường cũng là `null`, mà `null === null` là TRUE — so thẳng thì lúc chưa
  //  bung dòng nào, CẢ BẢNG bị đánh dấu là bản riêng.
  const laConDangBung = useCallback(
    (row: DocumentRecord) =>
      dongDangBung !== null && row.source_document_id === dongDangBung,
    [dongDangBung],
  )

  const rows = useMemo(() => {
    const items = data?.items ?? []
    if (!dongDangBung) return items
    const con = (banRieng?.items ?? []).filter(
      (row) => row.source_document_id === dongDangBung,
    )

    return items.flatMap((row) => (row.id === dongDangBung ? [row, ...con] : [row]))
  }, [data?.items, banRieng?.items, dongDangBung])

  const columns = useMemo<DataTableColumn<DocumentRecord>[]>(
    () => [
      {
        key: 'display_code',
        header: 'Số hiệu',
        width: 210,
        hideable: false,
        defaultPinned: true,
        cell: (row) => {
          //  Chỉ thụt lề khi dòng CHA đang nằm ngay trên nó. Người ở pháp nhân
          //  con xem được bản riêng nhưng KHÔNG xem được bản gốc — với họ đây
          //  là văn bản đứng một mình, kẻ mũi tên rẽ nhánh là trỏ vào một dòng
          //  cha không tồn tại trên màn hình.
          const laBanRieng = laConDangBung(row)
          const soBanRieng = row.clone_count ?? 0

          return (
            <div className="flex items-center gap-1">
              {soBanRieng > 0 ? (
                //  Nút bung phải chặn click lan lên dòng, nếu không mỗi lần mở
                //  nhánh là mở luôn trang chi tiết của bản gốc.
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  className="-ml-1 shrink-0"
                  title={`${soBanRieng} bản riêng ở pháp nhân con`}
                  aria-label={`Xem ${soBanRieng} bản riêng`}
                  aria-expanded={dongDangBung === row.id}
                  onClick={(event) => {
                    event.stopPropagation()
                    setDongDangBung(dongDangBung === row.id ? null : row.id)
                  }}
                >
                  <ChevronRight
                    className={cn(
                      'transition-transform',
                      dongDangBung === row.id && 'rotate-90',
                    )}
                  />
                </Button>
              ) : (
                //  Chừa đúng chỗ của nút để cột số hiệu của mọi dòng thẳng hàng.
                <span className={cn('shrink-0', laBanRieng ? 'w-5' : 'w-7')} />
              )}

              {laBanRieng && (
                <CornerDownRight className="size-3.5 shrink-0 text-muted-foreground" />
              )}

              <span
                className={cn(
                  'truncate',
                  laBanRieng ? 'text-muted-foreground' : 'font-medium text-navy',
                )}
              >
                {/* Chưa duyệt thì chưa có số — nói rõ chứ đừng để ô trống. */}
                {row.display_code || (
                  <span className="text-muted-foreground">Chưa cấp số</span>
                )}
              </span>
            </div>
          )
        },
      },
      {
        key: 'book_number_display',
        header: 'Số vào sổ',
        width: 130,
        cell: (row) => (
          <span className="tabular-nums">{row.book_number_display}</span>
        ),
      },
      { key: 'title', header: 'Tên văn bản', width: 340, cell: (row) => row.title },
      {
        key: 'doc_type_name',
        header: 'Loại',
        width: 160,
        cell: (row) => row.doc_type_name,
      },
      {
        key: 'company_name',
        header: 'Pháp nhân ban hành',
        width: 220,
        cell: (row) => (
          //  Với BẢN RIÊNG đang bung, pháp nhân là thứ duy nhất phân biệt nó
          //  với bản gốc (tiêu đề chép nguyên) — tô đậm để mắt bám vào cột đó.
          <span className={cn('truncate', laConDangBung(row) && 'font-medium')}>
            {row.company_name}
          </span>
        ),
      },
      {
        key: 'department_name',
        header: 'Phòng chủ trì',
        width: 170,
        cell: (row) => row.department_name,
      },
      {
        key: 'book_name',
        header: 'Sổ',
        width: 170,
        defaultHidden: true,
        cell: (row) => row.book_name,
      },
      {
        key: 'version_no',
        header: 'Bản',
        width: 90,
        align: 'right',
        cell: (row) => (
          <span className="tabular-nums">
            {row.version_no}
            {row.version_count > 1 && (
              <span className="text-muted-foreground"> /{row.version_count}</span>
            )}
          </span>
        ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        // Nhãn TÍNH RA lúc hiển thị (hết hạn theo ngày), không phải trạng thái thô.
        cell: (row) => {
          const label = effectiveLabel(row)
          return <Badge variant={label.variant}>{label.text}</Badge>
        },
      },
      {
        key: 'effective_date',
        header: 'Ngày hiệu lực',
        width: 140,
        cell: (row) => formatDate(row.effective_date ?? ''),
      },
      {
        key: 'secrecy_level',
        header: 'Mức mật',
        width: 120,
        cell: (row) => (
          <Badge variant="outline" className="font-normal">
            {secrecyLabel(row.secrecy_level)}
          </Badge>
        ),
      },
      {
        key: 'urgency',
        header: 'Độ khẩn',
        width: 110,
        defaultHidden: true,
        cell: (row) => urgencyLabel(row.urgency),
      },
      {
        key: 'owner_name',
        header: 'Người chịu trách nhiệm',
        width: 180,
        defaultHidden: true,
        cell: (row) => row.owner_name,
      },
      {
        key: 'legacy_code',
        header: 'Số hiệu cũ',
        width: 150,
        defaultHidden: true,
        cell: (row) => row.legacy_code,
      },
      {
        key: 'attachment_count',
        header: 'Tệp',
        width: 80,
        align: 'right',
        cell: (row) => (row.attachment_count ? String(row.attachment_count) : ''),
      },
    ],
    [dongDangBung, laConDangBung],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Văn bản"
        description="Số hiệu do hệ cấp khi văn bản được duyệt — không ai gõ tay."
        actions={
          <PermissionGate entity="document" action="create">
            <Button onClick={() => navigate(appRoutes.document.documentNew)}>
              <Plus className="size-4" />
              Tạo văn bản
            </Button>
          </PermissionGate>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={columns}
          rows={rows}
          getRowId={(row) => row.id}
          storageKey="document.records"
          fillHeight
          isLoading={isLoading}
          isError={isError}
          onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
          emptyMessage="Chưa có văn bản nào khớp điều kiện đang lọc."
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'văn bản',
          }}
          toolbar={
            <>
              <div className="relative w-full max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo tên, số hiệu, số hiệu cũ, từ khóa…"
                  value={keyword}
                  onChange={(event) => {
                    setKeyword(event.target.value)
                    setPage(1)
                  }}
                />
              </div>

              <Select
                value={typeId}
                onValueChange={(value) => {
                  setTypeId(value)
                  setPage(1)
                }}
              >
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

              <Select
                value={status}
                onValueChange={(value) => {
                  setStatus(value)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
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
