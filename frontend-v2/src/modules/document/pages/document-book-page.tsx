import { Plus } from 'lucide-react'
import { useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
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
import { CatalogTable } from '../components/catalog-table'
import { useDocumentBooks } from '../hooks/use-document-books'
import { BOOK_KIND_LABELS, BOOK_KIND_OPTIONS, type DocumentBook } from '../types/document-book'

const ALL_COMPANIES = 'all'
/** Bốn năm gần nhất — đủ để tra sổ cũ mà không phải gõ tay. */
const YEARS = Array.from({ length: 4 }, (_, i) => new Date().getFullYear() - i)

/**
 * DANH SÁCH SỔ VĂN BẢN — ba tab theo loại sổ: đến · đi · nội bộ.
 *
 * Sổ là bản ghi riêng chứ không phải một bộ lọc trên bảng văn bản: mỗi sổ có
 * người quản lý, người xem đích danh và **bộ đếm số của riêng nó**. Mở một sổ ra
 * mới thấy văn bản bên trong.
 *
 * Tab, pháp nhân và năm đều ghi lên URL nên gửi link cho nhau vẫn ra đúng màn
 * đang xem. Riêng NĂM phải gửi lên backend chứ không lọc ở client: "số kế tiếp"
 * và "đã cấp trong năm" là do bộ đếm của năm đó quyết định.
 */
export function DocumentBookPage() {
  const navigate = useNavigate()
  const [kind, setKind] = useUrlParamState('kind', '1')
  const [companyId, setCompanyId] = useUrlParamState('company', ALL_COMPANIES)
  const [year, setYear] = useUrlParamState('year', String(YEARS[0]))

  const { can } = usePermission()
  //  Ô chọn pháp nhân mượn danh mục của phân hệ Nhân sự (`company.read`). Người
  //  được CHIA SỔ thường không có quyền đó, mà không tắt query thì cứ mở trang
  //  là ăn một toast 403 chẳng liên quan gì tới việc họ đang làm.
  const canReadCompany = can('company', 'read')

  const { items, isLoading } = useDocumentBooks(Number(year))
  const { data: companies } = useCompanies({ page_size: 200 }, { enabled: canReadCompany })

  /** Số sổ mỗi loại, đã trừ đi ô lọc pháp nhân nhưng KHÔNG trừ ô tìm kiếm. */
  const countByKind = useMemo(() => {
    const total: Record<number, number> = { 1: 0, 2: 0, 3: 0 }
    for (const row of items) {
      if (companyId !== ALL_COMPANIES && row.company_id !== Number(companyId)) continue
      total[row.kind] = (total[row.kind] ?? 0) + 1
    }
    return total
  }, [items, companyId])

  const filterRows = useCallback(
    (rows: DocumentBook[]) =>
      rows.filter((row) => {
        if (row.kind !== Number(kind)) return false
        if (companyId === ALL_COMPANIES) return true
        return row.company_id === Number(companyId)
      }),
    [kind, companyId],
  )

  const columns = useMemo<DataTableColumn<DocumentBook>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã sổ',
        width: 110,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.code}</span>,
      },
      { key: 'name', header: 'Tên sổ', width: 240, cell: (row) => row.name },
      { key: 'company_name', header: 'Pháp nhân', width: 240, cell: (row) => row.company_name },
      {
        key: 'next_number_display',
        header: 'Số kế tiếp',
        width: 150,
        // Con số cần nhất khi mở màn này: sổ đang tới đâu rồi.
        cell: (row) => <span className="font-mono text-xs">{row.next_number_display}</span>,
      },
      {
        key: 'issued_count',
        header: `Đã cấp ${year}`,
        width: 120,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{row.issued_count}</span>,
      },
      {
        key: 'manager_names',
        header: 'Người quản lý',
        width: 200,
        cell: (row) =>
          row.manager_names.length ? (
            row.manager_names.join(', ')
          ) : (
            // Sổ mở từ trước lúc bắt buộc cử người quản lý — nói thẳng thay vì
            // để ô trống nhìn như dữ liệu chưa tải xong.
            <span className="text-muted-foreground">Chưa cử ai</span>
          ),
      },
      {
        key: 'viewer_names',
        header: 'Người xem sổ',
        width: 200,
        defaultHidden: true,
        cell: (row) =>
          row.viewer_names.length ? (
            row.viewer_names.join(', ')
          ) : (
            <span className="text-muted-foreground">Chỉ người quản lý</span>
          ),
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
    [year],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Sổ văn bản"
        description="Mỗi sổ có bộ đếm số riêng, đếm lại từ 1 mỗi năm."
        actions={
          //  Người được chia sổ vào đây để TRA CỨU, họ không có `document_book.create`
          //  — bày nút ra là mời họ bấm rồi ăn 403 ở màn khai sổ.
          <PermissionGate entity="document_book" action="create">
            <Button onClick={() => navigate(appRoutes.document.bookNew)}>
              <Plus className="size-4" />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      {/*  Số đếm trên từng tab: người được chia MỘT quyển sổ đi mà tab mặc định
           là «Văn bản đến» thì mở lên chỉ thấy trống trơn và kết luận là chia sổ
           không có tác dụng. Có số trên tab là thấy ngay sổ của mình nằm ở đâu. */}
      <Tabs value={kind} onValueChange={setKind} className="mb-4">
        <TabsList>
          {BOOK_KIND_OPTIONS.map((option) => (
            <TabsTrigger key={option.value} value={String(option.value)}>
              {BOOK_KIND_LABELS[option.value]}
              <span className="ml-1.5 tabular-nums text-muted-foreground">
                ({countByKind[option.value] ?? 0})
              </span>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <CatalogTable
        // Khóa nhớ layout tách theo tab: ba loại sổ có nhu cầu ẩn/hiện cột khác
        // nhau, dùng chung một khóa thì đổi cột ở tab này lại đổi luôn tab kia.
        storageKey={`document.books.${kind}`}
        //  `kind` ở màn này là TAB, không phải bộ lọc — xóa lọc mà nhảy về tab
        //  «Văn bản đến» là mất chỗ đang đứng.
        keepFilterParams={['kind']}
        items={items}
        columns={columns}
        searchFields={(row) => [row.code, row.name, row.company_name]}
        searchPlaceholder="Tìm theo mã sổ, tên sổ hoặc pháp nhân…"
        detailPath={appRoutes.document.bookDetail}
        filterRows={filterRows}
        emptyMessage={
          isLoading
            ? 'Đang tải danh sách sổ…'
            : `Chưa có ${BOOK_KIND_LABELS[Number(kind) as 1 | 2 | 3].toLowerCase()} nào khớp điều kiện đang lọc.`
        }
        extraToolbar={
          <>
            <Select value={companyId} onValueChange={setCompanyId}>
              <SelectTrigger className="w-56">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_COMPANIES}>Tất cả pháp nhân</SelectItem>
                {(companies?.items ?? []).map((company) => (
                  <SelectItem key={company.id} value={String(company.id)}>
                    {company.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={year} onValueChange={setYear}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {YEARS.map((option) => (
                  <SelectItem key={option} value={String(option)}>
                    Năm {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </>
        }
      />
    </PageContainer>
  )
}
