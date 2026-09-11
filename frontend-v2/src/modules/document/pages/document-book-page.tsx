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
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsTrigger } from '@/shared/ui/tabs'
import { CatalogTable } from '../components/catalog-table'
import { DocumentBookCard } from '../components/document-book-card'
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
            {/*  ⚠️ Khổ hẹp nút chiếm TRỌN hàng — `w-full` chỉ ăn nhờ nhóm nút của
                 `PageHeader` cũng `max-md:w-full`. Không có vế đó thì nút là con
                 của một khối co theo nội dung, `width:100%` quy về đúng bề rộng
                 cũ và câu lệnh không làm gì cả. Đứng lửng bên phải trên một hàng
                 trống thì nó vừa khó với tới bằng ngón cái, vừa đọc ra như bị
                 bỏ quên ở đó. */}
            <Button
              className="w-full md:w-auto"
              onClick={() => navigate(appRoutes.document.bookNew)}
            >
              <Plus className="size-4" />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      {/*  Số đếm trên từng tab: người được chia MỘT quyển sổ đi mà tab mặc định
           là «Văn bản đến» thì mở lên chỉ thấy trống trơn và kết luận là chia sổ
           không có tác dụng. Có số trên tab là thấy ngay sổ của mình nằm ở đâu. */}
      {/*  ⚠️ **Dải này TỪNG là `TabsList` nền xám, và tab thứ ba KHÔNG BẤM ĐƯỢC.**
           `TabsList` khai `w-fit` nên nó rộng theo nội dung và không cuộn: đo ở
           393px, ba nhãn tiếng Việt cộng số đếm cần **486px**, mép phải tab «Sổ
           văn bản nội bộ» nằm ở `right = 499`. Cả trang lẫn thẻ đều không cuộn
           ngang (`documentElement.scrollWidth = 393`) nên tab đó bị cắt cụt và
           **không có đường nào chạm tới** — tức một phần ba màn hình biến mất
           trên điện thoại. `ScrollableTabsList` cho cuộn ngang kèm hai mũi tên ở
           mép, giống chi tiết Văn bản (duoc-CR-366) và Trang cá nhân (CR-367). */}
      <Tabs value={kind} onValueChange={setKind} className="mb-4">
        <ScrollableTabsList value={kind}>
          {BOOK_KIND_OPTIONS.map((option) => (
            <TabsTrigger
              key={option.value}
              value={String(option.value)}
              className={TAB_TRIGGER_UNDERLINE}
            >
              {BOOK_KIND_LABELS[option.value]}
              <span className="ml-1.5 tabular-nums text-muted-foreground">
                ({countByKind[option.value] ?? 0})
              </span>
            </TabsTrigger>
          ))}
        </ScrollableTabsList>
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
        searchPlaceholderShort="Tìm mã sổ, tên sổ…"
        detailPath={appRoutes.document.bookDetail}
        filterRows={filterRows}
        //  Khổ hẹp: THẺ thay bảng — xem `DocumentBookCard`.
        mobileCard={(row) => <DocumentBookCard book={row} year={year} />}
        emptyMessage={
          isLoading
            ? 'Đang tải danh sách sổ…'
            : `Chưa có ${BOOK_KIND_LABELS[Number(kind) as 1 | 2 | 3].toLowerCase()} nào khớp điều kiện đang lọc.`
        }
        //  ⚠️ Khai ở `filters` chứ KHÔNG ở `extraToolbar`: `filters` được
        //  `CatalogTable` dựng ở hai chỗ — thẳng hàng trên thanh công cụ từ `md`,
        //  và xếp dọc có nhãn trong tờ trượt ở khổ hẹp. Nhét vào `extraToolbar`
        //  thì ở điện thoại hai ô này chiếm thêm hai hàng của một thanh đã chật.
        //  `w-full md:w-*`: trong tờ trượt ô trải hết bề ngang, trên thanh công
        //  cụ về lại bề rộng cũ.
        filters={[
          {
            label: 'Pháp nhân',
            node: (
              <Select value={companyId} onValueChange={setCompanyId}>
                <SelectTrigger className="w-full md:w-56" aria-label="Lọc theo pháp nhân">
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
            ),
          },
          {
            label: 'Năm',
            node: (
              <Select value={year} onValueChange={setYear}>
                <SelectTrigger className="w-full md:w-32" aria-label="Lọc theo năm">
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
            ),
          },
        ]}
      />
    </PageContainer>
  )
}
