import { Plus, Search } from 'lucide-react'
import { useMemo, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
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

const ALL = 'all'

interface CatalogListPageProps<T extends { id: number; is_active: boolean }> {
  title: string
  description: string
  /** Khóa nhớ layout bảng (ẩn/hiện, độ rộng, thứ tự cột). */
  storageKey: string
  items: T[]
  columns: DataTableColumn<T>[]
  /** Các trường được ô tìm kiếm quét qua. */
  searchFields: (row: T) => string[]
  searchPlaceholder: string
  newPath: string
  detailPath: (id: number) => string
  /** Ô lọc riêng của từng danh mục, chèn giữa ô tìm và select trạng thái. */
  extraToolbar?: ReactNode
}

/**
 * Khung chung cho danh sách DANH MỤC của phân hệ Văn bản.
 *
 * Bốn danh mục (loại văn bản, mức mật/khẩn, đối tác, trường động) đều cần đúng
 * một bộ: tìm theo từ khóa, lọc đang dùng / ngừng, bấm dòng vào chi tiết, nút
 * thêm mới. Chỉ cột và ô lọc riêng là khác nhau nên chúng đi vào props.
 */
export function CatalogListPage<T extends { id: number; is_active: boolean }>({
  title,
  description,
  storageKey,
  items,
  columns,
  searchFields,
  searchPlaceholder,
  newPath,
  detailPath,
  extraToolbar,
}: CatalogListPageProps<T>) {
  const navigate = useNavigate()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)

  const rows = useMemo(() => {
    const needle = debouncedValue.trim().toLowerCase()
    return items.filter((item) => {
      if (status !== ALL && item.is_active !== (status === 'active')) return false
      if (!needle) return true
      return searchFields(item).some((field) =>
        (field ?? '').toLowerCase().includes(needle),
      )
    })
  }, [items, status, debouncedValue, searchFields])

  return (
    <PageContainer fill>
      <PageHeader
        title={title}
        description={description}
        actions={
          <Button onClick={() => navigate(newPath)}>
            <Plus className="size-4" />
            Thêm mới
          </Button>
        }
      />

      {/* Bọc `Card` giống mọi màn danh sách khác (Nhân sự, Thu mua) — bảng đặt
          trần lên nền trang thì màu hàng tiêu đề và thân bảng lệch hẳn so với
          các phân hệ kia. */}
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={columns}
          rows={rows}
          getRowId={(row) => row.id}
          storageKey={storageKey}
          fillHeight
          onRowClick={(row) => navigate(detailPath(row.id))}
          emptyMessage="Không có bản ghi nào khớp điều kiện đang lọc."
          toolbar={
            <>
              <div className="relative w-full max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder={searchPlaceholder}
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                />
              </div>

              {extraToolbar}

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  <SelectItem value="active">Đang dùng</SelectItem>
                  <SelectItem value="inactive">Ngừng</SelectItem>
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
