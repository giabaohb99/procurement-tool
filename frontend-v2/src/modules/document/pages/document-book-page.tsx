import { Plus } from 'lucide-react'
import { useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { useDepartments } from '@/modules/hr/hooks/use-departments'
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

const ALL_DEPARTMENTS = 'all'
/** Bốn năm gần nhất — đủ để tra sổ cũ mà không phải gõ tay. */
const YEARS = Array.from({ length: 4 }, (_, i) => new Date().getFullYear() - i)

/**
 * DANH SÁCH SỔ VĂN BẢN — ba tab theo loại sổ: đến · đi · nội bộ.
 *
 * Sổ là bản ghi riêng chứ không phải một bộ lọc trên bảng văn bản: mỗi sổ có
 * người quản lý, đơn vị được xem và **bộ đếm số của riêng nó**. Mở một sổ ra
 * mới thấy văn bản bên trong.
 *
 * Tab, đơn vị và năm đều ghi lên URL nên gửi link cho nhau vẫn ra đúng màn đang
 * xem. Riêng NĂM phải gửi lên backend chứ không lọc ở client: "số kế tiếp" và
 * "đã cấp trong năm" là do bộ đếm của năm đó quyết định.
 */
export function DocumentBookPage() {
  const navigate = useNavigate()
  const [kind, setKind] = useUrlParamState('kind', '1')
  const [departmentId, setDepartmentId] = useUrlParamState('dept', ALL_DEPARTMENTS)
  const [year, setYear] = useUrlParamState('year', String(YEARS[0]))

  const { items, isLoading } = useDocumentBooks(Number(year))
  const { data: departments } = useDepartments({ page_size: 200 })

  const filterRows = useCallback(
    (rows: DocumentBook[]) =>
      rows.filter((row) => {
        if (row.kind !== Number(kind)) return false
        if (departmentId === ALL_DEPARTMENTS) return true
        return row.department_id === Number(departmentId)
      }),
    [kind, departmentId],
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
      {
        key: 'company_name',
        header: 'Pháp nhân · đơn vị',
        width: 240,
        cell: (row) => (
          <span className="flex flex-col">
            <span>{row.company_name}</span>
            <span className="text-xs text-muted-foreground">
              {row.department_name || 'Cả pháp nhân'}
            </span>
          </span>
        ),
      },
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
            // Sổ không có người quản lý là sổ không ai chịu trách nhiệm — nói
            // thẳng thay vì để ô trống nhìn như dữ liệu chưa tải xong.
            <span className="text-muted-foreground">Chưa cử ai</span>
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
          <Button onClick={() => navigate(appRoutes.document.bookNew)}>
            <Plus className="size-4" />
            Thêm mới
          </Button>
        }
      />

      <Tabs value={kind} onValueChange={setKind} className="mb-4">
        <TabsList>
          {BOOK_KIND_OPTIONS.map((option) => (
            <TabsTrigger key={option.value} value={String(option.value)}>
              {BOOK_KIND_LABELS[option.value]}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <CatalogTable
        // Khóa nhớ layout tách theo tab: ba loại sổ có nhu cầu ẩn/hiện cột khác
        // nhau, dùng chung một khóa thì đổi cột ở tab này lại đổi luôn tab kia.
        storageKey={`document.books.${kind}`}
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
            <Select value={departmentId} onValueChange={setDepartmentId}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_DEPARTMENTS}>Tất cả đơn vị</SelectItem>
                {(departments?.items ?? []).map((department) => (
                  <SelectItem key={department.id} value={String(department.id)}>
                    {department.name}
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
