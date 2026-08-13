import { Plus, Search } from 'lucide-react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
} from '@/shared/conditional-filter'
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
import { DOCUMENT_TYPE_FILTER_FIELDS } from '../config/document-filter-fields'
import { filterDocumentTypes } from '../helpers/filter-document-types'
import { useDocumentTypes } from '../hooks/use-document-types'
import { DOCUMENT_TYPE_OPTIONS, type DocumentType } from '../types/document-type'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: DOCUMENT_TYPE_FILTER_FIELDS,
  allowConjunctionToggle: true,
  // Thiếu tên nào ở đây thì bấm "Áp dụng" bộ lọc nâng cao sẽ xóa mất select đó.
  preserveParams: ['status'],
}

/**
 * Danh mục LOẠI VĂN BẢN — mỗi văn bản khi tạo chọn một loại ở đây, số hiệu sinh
 * theo tiền tố của loại đó.
 *
 * ⚠️ Dữ liệu còn nằm ở kho tạm phía trình duyệt (`store/document-type-store.ts`),
 * chờ backend có `/api/document-types`.
 */
export function DocumentTypeListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <DocumentTypeListContent />
    </FilterProvider>
  )
}

function DocumentTypeListContent() {
  const navigate = useNavigate()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)

  // Lọc tại chỗ chứ không gửi query param: chưa có backend để lọc hộ.
  const { appliedState } = useFilterContext()
  const { items } = useDocumentTypes(debouncedValue)

  const rows = useMemo(() => {
    const byStatus =
      status === ALL
        ? items
        : items.filter((item) => item.is_active === (status === 'active'))
    return filterDocumentTypes(byStatus, appliedState)
  }, [items, status, appliedState])

  const columns = useMemo<DataTableColumn<DocumentType>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã loại',
        width: 110,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.code}</span>,
      },
      { key: 'name', header: 'Tên loại văn bản', width: 220, cell: (row) => row.name },
      {
        key: 'prefix',
        header: 'Tiền tố số hiệu',
        width: 160,
        // Mẫu số hiệu thật dễ hiểu hơn mỗi chuỗi tiền tố trơ trọi.
        cell: (row) => (
          <span className="font-mono text-xs text-muted-foreground">
            {row.prefix}-2026-001
          </span>
        ),
      },
      {
        key: 'options',
        header: 'Tùy chọn',
        width: 260,
        // Chỉ liệt kê cái ĐANG BẬT: kê cả cái tắt thì cột nào cũng như cột nào,
        // nhìn không ra loại nào khác loại nào.
        cell: (row) => (
          <span className="flex flex-wrap gap-1">
            {DOCUMENT_TYPE_OPTIONS.filter((option) => row[option.key]).map((option) => (
              <Badge key={option.key} variant="outline" className="font-normal">
                {option.label}
              </Badge>
            ))}
          </span>
        ),
      },
      { key: 'description', header: 'Mô tả', defaultHidden: true, cell: (row) => row.description },
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
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Loại văn bản"
        description="Danh mục các loại văn bản dùng trong hệ thống và tiền tố số hiệu tương ứng."
        actions={
          <Button onClick={() => navigate(appRoutes.document.typeNew)}>
            <Plus className="size-4" />
            Thêm mới
          </Button>
        }
      />

      {/* Bọc `Card` như mọi màn danh sách khác — bảng đặt trần lên nền trang
          thì màu hàng tiêu đề và thân bảng lệch so với các phân hệ kia. */}
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={columns}
          rows={rows}
          getRowId={(row) => row.id}
          storageKey="document.types"
          fillHeight
          onRowClick={(row) => navigate(appRoutes.document.typeDetail(row.id))}
          emptyMessage="Không có loại văn bản nào khớp điều kiện đang lọc."
          toolbar={
            <>
              <div className="relative w-full max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo mã, tên hoặc tiền tố…"
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

              <ConditionalFilter />
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
