import { Search } from 'lucide-react'
import { useMemo, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'

const ALL = 'all'

interface CatalogTableProps<T extends { id: number; is_active: boolean }> {
  /** Khóa nhớ layout bảng (ẩn/hiện, độ rộng, thứ tự cột). */
  storageKey: string
  items: T[]
  columns: DataTableColumn<T>[]
  /** Các trường được ô tìm kiếm quét qua. */
  searchFields: (row: T) => string[]
  searchPlaceholder: string
  detailPath: (id: number) => string
  emptyMessage?: string
  /** Lọc thêm sau ô tìm kiếm và select trạng thái (vd bộ lọc nâng cao). */
  filterRows?: (rows: T[]) => T[]
  /** Ô lọc riêng của từng danh mục, chèn sau select trạng thái. */
  extraToolbar?: ReactNode
}

/**
 * Bảng chung cho MỘT danh mục nền của phân hệ Văn bản.
 *
 * Bốn danh mục (loại văn bản, mức mật/khẩn, đối tác, trường động) đều cần đúng
 * một bộ: tìm theo từ khóa, lọc đang dùng / ngừng, bấm dòng vào chi tiết. Chỉ
 * cột và ô lọc riêng là khác nhau nên chúng đi vào props.
 *
 * KHÔNG tự vẽ tiêu đề trang: cả bốn nằm chung trang "Thiết lập văn bản", tiêu
 * đề và nút Thêm mới do trang đó lo (xem `pages/document-settings-page.tsx`).
 */
export function CatalogTable<T extends { id: number; is_active: boolean }>({
  storageKey,
  items,
  columns,
  searchFields,
  searchPlaceholder,
  detailPath,
  emptyMessage = 'Không có bản ghi nào khớp điều kiện đang lọc.',
  filterRows,
  extraToolbar,
}: CatalogTableProps<T>) {
  const navigate = useNavigate()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)

  const rows = useMemo(() => {
    const needle = debouncedValue.trim().toLowerCase()
    const found = items.filter((item) => {
      if (status !== ALL && item.is_active !== (status === 'active')) return false
      if (!needle) return true
      return searchFields(item).some((field) => (field ?? '').toLowerCase().includes(needle))
    })
    return filterRows ? filterRows(found) : found
  }, [items, status, debouncedValue, searchFields, filterRows])

  return (
    // Bọc `Card` giống mọi màn danh sách khác (Nhân sự, Thu mua) — bảng đặt
    // trần lên nền trang thì màu hàng tiêu đề và thân bảng lệch hẳn.
    <Card className="flex min-h-0 flex-1 flex-col p-4">
      <DataTable
        columns={columns}
        rows={rows}
        getRowId={(row) => row.id}
        storageKey={storageKey}
        fillHeight
        onRowClick={(row) => navigate(detailPath(row.id))}
        emptyMessage={emptyMessage}
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

            {extraToolbar}
          </>
        }
      />
    </Card>
  )
}
