import { ExternalLink, Lock } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate } from '@/shared/utils/format-date'
import { docCodeText, effectiveStatusBadge } from './outgoing-document-columns'
import { recentBookYears } from '../helpers/recent-book-years'
import { useDocuments } from '../hooks/use-documents'
import type { DocumentRecord } from '../types/document-record'

interface BookDocumentsTabProps {
  bookId: number
  /** Cùng state với `BookCounterCard` — một sổ chỉ có MỘT năm đang xem, dù đứng ở tab nào. */
  year: number
  onYearChange: (year: number) => void
}

/**
 * Mặc định sắp theo SỐ VÀO SỔ giảm dần — đọc y như quyển sổ giấy, số mới nhất
 * lên đầu. `apply_sort` ở backend đẩy NULL (chưa vào sổ) xuống cuối bất kể
 * chiều sắp (duoc-CR-474).
 */
const DEFAULT_SORT = '-book_seq_no'

/**
 * TAB «VĂN BẢN TRONG SỔ» của trang chi tiết Sổ văn bản (duoc-CR-474, 23/09/2026).
 *
 * Đè lại quyết định 25/08/2026 (CR-175, commit `89d04519`): khi đó bảng này bị
 * gỡ với lý do "tra theo sổ thì lọc ở màn Văn bản, không cần bảng thứ hai
 * trong trang khai báo sổ". Khách đổi ý 23/09/2026 — muốn bấm sổ ra thẳng danh
 * sách văn bản trong sổ mà không phải vòng qua bộ lọc nâng cao của màn Văn bản.
 * Cả hai đường vẫn cùng tồn tại: nút «Mở ở màn Văn bản» bên dưới dẫn sang đó
 * cho ai cần bộ lọc đầy đủ.
 *
 * Đi qua ĐÚNG `/api/documents` — không có API riêng, không đường vòng quyền:
 * văn bản mật trong sổ vẫn ẩn với người không đủ quyền xem, giống mọi bảng
 * văn bản khác (`documents_query` + `access_service.visible_condition`).
 */
export function BookDocumentsTab(props: BookDocumentsTabProps) {
  const { can } = usePermission()

  //  Không có `document.read` → KHÔNG mount `BookDocumentsContent`, tức
  //  `useDocuments` bên trong nó không bao giờ được gọi. Đây là cách duy nhất
  //  để "không gọi API mà vẫn ăn 403" — chốt của đại ca 23/09/2026: thành viên
  //  sổ (quản lý/xem theo sổ) không tự động có quyền đọc phân hệ Văn bản.
  if (!can('document', 'read')) {
    return (
      <Card className="flex items-start gap-2 border-dashed p-4 text-sm text-muted-foreground">
        <Lock className="mt-0.5 size-4 shrink-0" />
        <span>
          Bạn chưa có quyền đọc phân hệ Văn bản (<code>document.read</code>), nên không xem
          được danh sách văn bản trong sổ này. Là thành viên sổ (quản lý hoặc người xem sổ)
          không tự mở quyền này — liên hệ quản trị viên nếu cần.
        </span>
      </Card>
    )
  }

  return <BookDocumentsContent {...props} />
}

function BookDocumentsContent({ bookId, year, onYearChange }: BookDocumentsTabProps) {
  const navigate = useNavigate()

  const [keyword, setKeyword] = useState('')
  const debouncedKeyword = useDebouncedValue(keyword)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  //  Đổi năm hay đổi từ khóa tìm đều phải về trang 1 — bộ lọc lên URL của TRANG
  //  CHA (`?tab=documents`) nên state này ở lại cục bộ, không đẩy lên URL.
  const [page, setPage] = usePageResetOnFilterChange([bookId, year, debouncedKeyword])

  const { data, isLoading, isError } = useDocuments({
    book_id: bookId,
    book_year: year,
    q: debouncedKeyword.trim() || undefined,
    sort: DEFAULT_SORT,
    page,
    page_size: pageSize,
  })

  const columns = useMemo<DataTableColumn<DocumentRecord>[]>(
    () => [
      {
        key: 'book_seq_no',
        header: 'Số trong sổ',
        width: 110,
        align: 'right',
        hideable: false,
        //  Chưa duyệt thì chưa vào sổ — số này cấp CÙNG LÚC với số hiệu.
        cell: (row) => (
          <span className="font-medium tabular-nums">
            {row.book_seq_no ?? <span className="text-muted-foreground">—</span>}
          </span>
        ),
      },
      {
        key: 'display_code',
        header: 'Số/ký hiệu',
        width: 170,
        cell: (row) => docCodeText(row),
      },
      { key: 'title', header: 'Trích yếu', width: 320, wrap: true, cell: (row) => row.title },
      { key: 'doc_type_name', header: 'Loại', width: 160, cell: (row) => row.doc_type_name },
      {
        key: 'effective_date',
        header: 'Ngày hiệu lực',
        width: 140,
        cell: (row) => formatDate(row.effective_date ?? ''),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 160,
        cell: (row) => effectiveStatusBadge(row),
      },
      {
        key: 'drafter_name',
        header: 'Người soạn',
        width: 170,
        cell: (row) => row.drafter_name,
      },
    ],
    [],
  )

  //  Đang lọc THẬT — riêng năm thì luôn có giá trị (không có mốc "tất cả năm"
  //  cho tab này, giống bộ đếm cạnh nó), nên chỉ từ khóa mới tính là "đang lọc".
  const filtersActive = debouncedKeyword.trim() !== ''

  return (
    <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
      <DataTable
        columns={columns}
        rows={data?.items}
        getRowId={(row: DocumentRecord) => row.id}
        storageKey="document.book-documents"
        isLoading={isLoading}
        isError={isError}
        onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
        //  Rỗng vì TỪ KHÓA không tìm thấy khác hẳn rỗng vì sổ chưa có văn bản
        //  nào trong năm đó — gộp một câu thì người gõ nhầm một chữ đọc ra
        //  "sổ chưa dùng bao giờ" trong khi sự thật là đang gõ sai từ khóa.
        emptyMessage={
          debouncedKeyword.trim()
            ? 'Không tìm thấy văn bản nào khớp từ khóa đang tìm.'
            : `Sổ chưa có văn bản nào trong năm ${year}.`
        }
        filtersActive={filtersActive}
        onResetFilters={() => setKeyword('')}
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
            <SearchField
              value={keyword}
              onChange={(value) => setKeyword(value)}
              placeholder="Tìm tên, số hiệu, từ khóa…"
              placeholderShort="Tìm tên, số hiệu…"
              className="md:min-w-56 md:max-w-xs"
            />

            <Select value={String(year)} onValueChange={(value) => onYearChange(Number(value))}>
              <SelectTrigger className="w-full md:w-32" aria-label="Lọc theo năm vào sổ">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {recentBookYears().map((option) => (
                  <SelectItem key={option} value={String(option)}>
                    Năm {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/*  Đường vòng cho ai cần bộ lọc nâng cao đầy đủ (loại, trạng thái,
                 mức mật…) — bảng ở đây cố ý chỉ có đúng hai ô lọc để đọc như
                 một quyển sổ, không phải một bản sao của màn Văn bản. */}
            <Button
              type="button"
              variant="outline"
              className="md:ml-auto"
              onClick={() =>
                navigate(`${appRoutes.document.documents}?book_id__eq=${bookId}`)
              }
            >
              <ExternalLink className="size-4" />
              Mở ở màn Văn bản
            </Button>
          </>
        }
      />
    </Card>
  )
}
