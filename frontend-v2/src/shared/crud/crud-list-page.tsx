import { Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

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
import { CrudFormDialog } from './crud-form-dialog'
import type { CrudConfig } from './types'
import { useCrudList } from './use-crud'

interface CrudListPageProps<T> {
  config: CrudConfig<T>
}

export function CrudListPage<T extends Record<string, any>>({ config }: CrudListPageProps<T>) {
  if (config.filterConfig) {
    return (
      <FilterProvider config={config.filterConfig}>
        <CrudListContent config={config} />
      </FilterProvider>
    )
  }

  return <CrudListContent config={config} />
}

function CrudListContent<T extends Record<string, any>>({ config }: CrudListPageProps<T>) {
  const navigate = useNavigate()
  const idKey = (config.idKey as string) || 'id'
  const searchParamName = config.searchParam || 'name'

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [isCreateOpen, setCreateOpen] = useState(false)

  const { queryParams, queryKey } = useFilterQuery()
  const [page, setPage] = usePageResetOnFilterChange([queryKey, debouncedValue])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) {
    params[searchParamName] = debouncedValue
  }

  const { data, isLoading, isError } = useCrudList<T>(config.apiPath, params)

  const handleRowClick = (row: T) => {
    if (config.detailRoute) {
      navigate(config.detailRoute(row[idKey]))
    }
  }

  return (
    <PageContainer fill>
      <PageHeader
        title={config.title}
        actions={
          <div className="flex items-center gap-2">
            {config.renderToolbarExtra?.()}

            <PermissionGate entity={config.entity} action="create">
              <Button onClick={() => setCreateOpen(true)}>
                <Plus className="mr-1.5 size-4" /> Thêm {config.unitLabel}
              </Button>
            </PermissionGate>
          </div>
        }
      />

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
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: config.unitLabel,
          }}
          toolbar={
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative w-64 max-w-sm">
                <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder={config.searchPlaceholder || `Tìm ${config.unitLabel}…`}
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  className="pl-8"
                />
              </div>

              {config.filterConfig && <ConditionalFilter />}
            </div>
          }
        />
      </Card>

      <CrudFormDialog
        open={isCreateOpen}
        onOpenChange={setCreateOpen}
        config={config}
      />
    </PageContainer>
  )
}
