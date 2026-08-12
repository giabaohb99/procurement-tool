import { Plus, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
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
import { CompanyFormDialog } from '../components/company-form-dialog'
import { COMPANY_FILTER_FIELDS } from '../config/hr-filter-fields'
import { useCompanies } from '../hooks/use-companies'
import { companyInitial, type Company } from '../types/company'

const ALL = 'all'

/** `preserveParams`: giữ select Trạng thái trên URL khi áp bộ lọc nâng cao. */
const FILTER_CONFIG = {
  fields: COMPANY_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['is_active'],
}

export function CompanyListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <CompanyListContent />
    </FilterProvider>
  )
}

/**
 * Danh mục pháp nhân.
 *
 * Thanh công cụ giữ ô tìm theo tên + select Trạng thái; Mã công ty và Mã số
 * thuế đưa vào "Bộ lọc" nâng cao.
 */
function CompanyListContent() {
  const navigate = useNavigate()

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [active, setActive] = useUrlParamState('is_active', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [isFormOpen, setFormOpen] = useState(false)

  const { queryParams, queryKey } = useFilterQuery()

  useEffect(() => setPage(1), [queryKey, debouncedValue, active])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.name = debouncedValue
  if (active !== ALL) params.is_active = active === 'true'

  const { data, isLoading, isError } = useCompanies(params)

  const columns = useMemo<DataTableColumn<Company>[]>(
    () => [
      {
        key: 'name',
        header: 'Tên pháp nhân',
        width: 340,
        hideable: false,
        cell: (company) => (
          <span className="flex min-w-0 items-center gap-2.5">
            {/* Logo đi kèm trong ô Tên, không tách cột riêng. */}
            <span className="grid size-7 shrink-0 place-items-center overflow-hidden rounded-md border bg-accent text-xs font-semibold text-primary">
              {company.logo ? (
                <img src={company.logo} alt="" className="size-full bg-white object-contain" />
              ) : (
                companyInitial(company)
              )}
            </span>
            <span className="truncate">{company.name}</span>
          </span>
        ),
      },
      { key: 'code', header: 'Mã', width: 140, cell: (c) => c.code },
      { key: 'tax_code', header: 'Mã số thuế', width: 170, cell: (c) => c.tax_code || '—' },
      {
        key: 'legal_rep_name',
        header: 'Người đại diện',
        width: 220,
        cell: (c) => c.legal_rep_name || '—',
      },
      {
        key: 'invoice_email',
        header: 'Email hóa đơn',
        width: 220,
        // Ít khi cần liếc trong danh sách — mặc định ẩn, ai cần thì bật ở menu Cột.
        defaultHidden: true,
        cell: (c) => c.invoice_email || '—',
      },
      {
        key: 'is_active',
        header: 'Trạng thái',
        width: 140,
        cell: (c) => (
          <Badge variant={c.is_active ? 'default' : 'secondary'}>
            {c.is_active ? 'Đang dùng' : 'Ngừng'}
          </Badge>
        ),
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Công ty"
        description="Danh mục pháp nhân: mã số thuế, người đại diện, thông tin hóa đơn."
        actions={
          <PermissionGate entity="company" action="create">
            <Button onClick={() => setFormOpen(true)}>
              <Plus />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(company) => company.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy công ty nào."
          storageKey="hr.companies"
          onRowClick={(company) => navigate(appRoutes.hr.companyDetail(company.id))}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'công ty',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-sm">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo tên pháp nhân…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={active} onValueChange={setActive}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  <SelectItem value="true">Đang dùng</SelectItem>
                  <SelectItem value="false">Ngừng</SelectItem>
                </SelectContent>
              </Select>

              <ConditionalFilter />
            </>
          }
        />
      </Card>

      <CompanyFormDialog open={isFormOpen} onOpenChange={setFormOpen} />
    </PageContainer>
  )
}
