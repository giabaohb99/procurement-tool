import { Plus, Search } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import { ConditionalFilter, FilterProvider, useFilterQuery } from '@/shared/conditional-filter'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { CrudFormDialog } from './crud-form-dialog'
import type { CrudConfig, CrudRecord } from './types'
import { useCrudList } from './use-crud'

interface CrudListPageProps<T> {
  config: CrudConfig<T>
  /**
   * Chèn giữa TIÊU ĐỀ và bảng — chỗ cho thanh chuyển màn của những phân hệ gom
   * nhiều màn vào một mục menu (cụm Nghỉ phép, xem `LeaveSectionTabs`).
   *
   * Không nhét vào `renderToolbarExtra`: khe đó nằm trong nhóm NÚT bên phải
   * tiêu đề, còn thanh tab phải chạy hết bề ngang và đứng thành một dải riêng.
   */
  beforeContent?: ReactNode
}

export function CrudListPage<T extends CrudRecord>({
  config,
  beforeContent,
}: CrudListPageProps<T>) {
  /**
   * Bấm "Áp dụng" ở bộ lọc nâng cao là VIẾT LẠI toàn bộ query string, chỉ chừa lại
   * `searchParamName` + `preserveParams` (xem `use-filter-url-sync.ts`). Khai thiếu tên nào
   * thì tên đó bay khỏi URL — trước đây màn Hợp đồng mất sạch lọc nhanh và thứ tự sắp xếp
   * mỗi lần thêm một điều kiện nâng cao.
   *
   * Khóa lọc nhanh và `sort_by`/`sort_dir` do chính `CrudListContent` sinh ra nên gom sẵn ở
   * đây, khỏi bắt từng màn tự nhớ khai lại.
   */
  const filterConfig = useMemo(() => {
    if (!config.filterConfig) return undefined
    const auto = [...(config.quickFilters ?? []).map((qf) => qf.key), 'sort_by', 'sort_dir']
    return {
      ...config.filterConfig,
      preserveParams: [...new Set([...(config.filterConfig.preserveParams ?? []), ...auto])],
    }
  }, [config.filterConfig, config.quickFilters])

  if (filterConfig) {
    return (
      <FilterProvider config={filterConfig}>
        <CrudListContent config={config} beforeContent={beforeContent} />
      </FilterProvider>
    )
  }

  return <CrudListContent config={config} beforeContent={beforeContent} />
}

function CrudListContent<T extends CrudRecord>({
  config,
  beforeContent,
}: CrudListPageProps<T>) {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const idKey = (config.idKey as string) || 'id'
  const searchParamName = config.searchParam || 'name'

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [isCreateOpen, setCreateOpen] = useState(false)

  const { queryParams, queryKey } = useFilterQuery()
  const [page, setPage] = usePageResetOnFilterChange([queryKey, debouncedValue, searchParams.toString()])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) {
    params[searchParamName] = debouncedValue
  }
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  // Merge quick filters from URL params
  if (config.quickFilters) {
    for (const qf of config.quickFilters) {
      const val = searchParams.get(qf.key)
      if (val !== null && val !== '') {
        params[qf.key] = val
      }
    }
  }

  const { data, isLoading, isError } = useCrudList<T>(config.apiPath, params)

  const handleRowClick = (row: T) => {
    if (config.detailRoute) {
      navigate(config.detailRoute(row[idKey] as string | number))
    }
  }

  const handleSortChange = (newSortBy: string, newSortDir: 'asc' | 'desc') => {
    const nextParams = new URLSearchParams(searchParams)
    //  Khóa cột rỗng = nhịp thứ ba của tiêu đề cột: thôi sắp xếp. Phải XÓA tham
    //  số chứ đừng ghi chuỗi rỗng, kẻo đường dẫn gửi cho nhau còn dính
    //  `?sort_by=&sort_dir=asc`, đọc như đang sắp xếp theo một cột không tên.
    if (newSortBy) {
      nextParams.set('sort_by', newSortBy)
      nextParams.set('sort_dir', newSortDir)
    } else {
      nextParams.delete('sort_by')
      nextParams.delete('sort_dir')
    }
    setSearchParams(nextParams)
  }

  const handleQuickFilterChange = (key: string, value: string) => {
    const nextParams = new URLSearchParams(searchParams)
    if (value && value !== 'all') {
      nextParams.set(key, value)
    } else {
      nextParams.delete(key)
    }
    setSearchParams(nextParams)
  }

  return (
    <PageContainer fill>
      <PageHeader
        title={config.title}
        description={config.description}
        actions={
          <div className="flex items-center gap-2">
            {config.renderToolbarExtra?.()}

            <PermissionGate entity={config.entity} action="create">
              {/*  Khai `createRoute` = form thêm mới nằm ở TRANG RIÊNG, không
                   phải hộp thoại. Xem `CrudConfig.createRoute`. */}
              {config.createRoute ? (
                <Button asChild>
                  <Link to={config.createRoute}>
                    <Plus className="mr-1.5 size-4" /> Thêm {config.unitLabel}
                  </Link>
                </Button>
              ) : (
                <Button onClick={() => setCreateOpen(true)}>
                  <Plus className="mr-1.5 size-4" /> Thêm {config.unitLabel}
                </Button>
              )}
            </PermissionGate>
          </div>
        }
      />

      {beforeContent}

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={config.columns}
          rows={data?.items}
          getRowId={(row: T) => String(row[idKey])}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={`Không tìm thấy ${config.unitLabel} nào.`}
          storageKey={config.storageKey}
          onRowClick={handleRowClick}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={handleSortChange}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: config.unitLabel,
          }}
          toolbar={
            <>
              <div className="relative w-64 max-w-sm">
                <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder={config.searchPlaceholder || `Tìm ${config.unitLabel}…`}
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  className="pl-8 h-9 text-xs bg-background"
                />
              </div>

              {config.quickFilters?.map((qf) => {
                if (qf.type === 'select' && qf.options) {
                  const val = searchParams.get(qf.key) || 'all'
                  return (
                    <Select
                      key={qf.key}
                      value={val}
                      onValueChange={(v) => handleQuickFilterChange(qf.key, v)}
                    >
                      <SelectTrigger className="h-9 w-40 text-xs">
                        <SelectValue placeholder={qf.label} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Tất cả {qf.label.toLowerCase()}</SelectItem>
                        {qf.options.map((opt) => (
                          <SelectItem key={String(opt.value)} value={String(opt.value)}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )
                }
                return null
              })}

              {config.filterConfig && <ConditionalFilter />}
            </>
          }
        />
      </Card>

      {/*  Không dựng hộp thoại khi đã có trang thêm mới — dựng cả hai là hai
           nguồn dữ liệu cho cùng một việc, sớm muộn lệch nhau. */}
      {!config.createRoute && (
        <CrudFormDialog open={isCreateOpen} onOpenChange={setCreateOpen} config={config} />
      )}
    </PageContainer>
  )
}
